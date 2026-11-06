# EXP-049 — A pipeline that uses the full inference VRAM of the L4x4: desk check

**Date:** 2026-11-06
**Type:** desk check (L0, zero GPU). Nothing is built or pushed.
**Cohort:** none
**Ladder:** L0. Every answer comes from the harness and vLLM wheel source on disk, the harness README, our own kernel logs, or an earlier EXP section. No trace is mined here.
**Pre-registered:** the readings in section 4 were written after the facts in section 2 were gathered (an L0 has no outcome to be blind to), and before the shapes in section 9 were ranked against them. They are not revised.
**Serves:** the user's direction of 2026-11-06, quoted by the lead: explore a pipeline that uses the full inference VRAM of the L4 GPUs, and submit it. Also C-015 (best-of-N needs a selector) and C-023 (voting on the E4B).
**Relates:** EXP-006 (KV room and burst speed-up), EXP-007 (ParallelAgent overlap and the sync-tool stall), EXP-009 (idle capacity buys throughput, not latency), EXP-028 (31B v24 at 8 min, the 10.04 h projection), EXP-030 (no data), EXP-032 (parallel localizers on the 31B), EXP-034 (the best-of-N ceiling and proxies), EXP-038 (E4B single loop, dev-48), EXP-040 (16 tool-less voters on the E4B), EXP-046 (stage bounds).
**Tags:** [V] read in source on disk, in the harness README, or in our own log, with file:line; [M] mirror or community source; [I] inference or arithmetic from [V] numbers.

Path roots used below: `server.py` = `data/src/adk_submission/adk_submission/server.py`; `README` = `data/raw/HARNESS_README.md`; `arg_utils.py` = the vLLM 0.19.1 wheel's `vllm/engine/arg_utils.py`; `agent_runner.py`, `context.py` = `swegemma/harness/agent_runner.py`, `swegemma/context.py`; ADK files are under the `google/adk/` package of the wheelhouse; the EXP-006 31B log is `runs/EXP-006-vllm-concurrency-probe/.../logs/gemma-4-31b-it-qat-w4a16-ct_faithful_a1.log` (gitignored, our own run).

## 0. Verdict, first

- **On the 31B, no shape fits.** The 10.5 h rule leaves 13.8 s per task (EXP-028 9.1, EXP-032 line 106). A single extra burst of tool-less 256-token samples costs at least 8.6 s of decode at N = 1 and about 13.9 s at N = 16, before prefill and before any thinking tokens [I]. Cutting the cap to buy that room cuts the loop that already ends 37.5% of tasks at the call cap.
- **On the E4B, the time and the memory exist** (225.6 s per task, at least 45.6 concurrent 32k sequences), **but no selector does.** The one shape that ran (16 identical voters, EXP-040) never changed a pick. Whole-attempt best-of-N is blocked by the shared `/workspace` and by the lack of a selector without hidden tests (EXP-034: the best free proxy is +3.0 of 48 over a random arm, below the board MDE of 4). Parallel tool-bearing readers starve the editor on the shared counter (EXP-032).
- **What survives is one unmeasured shape:** k tool-less samples with different prompts at a single decision point, on the E4B. Its selector is a majority vote, which the literature cited in C-015 finds adds nothing. Its cheapest kill is a zero-GPU read of the EXP-040 vote spread, then a smoke-8 at about 0.3 GPU-h.
- **The submission can set none of the server's memory or batching settings.** "Using the full VRAM" can only mean issuing more concurrent requests inside one task.

## 1. Why this, now

The user asked for a pipeline that uses the full inference VRAM and for it to be submitted. Whether anything can be built depends on four harness facts the record holds in pieces:
- what the scorer's server does with its memory;
- which config routes give concurrent requests inside one task;
- what those requests cost in wall time;
- whether anything can pick among their outputs without the hidden tests.

This desk check puts those facts in one place, cited, so the lead can rank a screen or close the direction.

## 2. The desk check

### 2.1 Q1. The scorer's server, our server, and what a submission controls

| Question | Answer | Source |
|---|---|---|
| Hidden tasks one at a time? | **Yes, sequentially**: about 120 hidden tasks inside 12 h | `.claude/skills/competition-brief/SKILL.md:16` [V per the brief; its source page was not re-read in this job] |
| Corroboration | The README gives a `--concurrency N` flag for the local `swegemma eval` CLI only. The scorer's `scripts/inference.py` is described but not on disk, and its listed settings name no task concurrency. 120 tasks at our measured 297 s mean plus setup projects about 10 h, which only fits a 12 h limit if tasks run one at a time | `README:647,656`; `README:160-170`; EXP-028 9.1 [I] |
| Tensor parallel size | 4 | `README:164` [V]; our server: log line 7 [V] |
| gpu_memory_utilization | 0.90 | `README:165` [V]; `server.py` VllmConfig default (lines 103-164) [V]; our notebook `notebooks/kaggle_eval_l4x4.py:280-287` [V] |
| max_model_len | 32,768 | `README:166` [V]; `server.py` default [V]; notebook [V] |
| max_num_seqs | 256 | No flag in `server.py` `build_cmd` (lines 686-801), so vLLM's default applies: below 70 GiB of device memory the API-server default is 256 | `arg_utils.py:2053-2072` [V for our server; I for the scorer, since the README lists no override] |
| max_num_batched_tokens | 2,048 (same default rule) | `arg_utils.py:2053-2072` [V ours; I scorer] |
| Prefix caching | **On** | our 31B log line 12 (V1 engine default) [V ours]; the README's section 7.2 heading names prefix caching and the ADK context cache (`README:568,577`) [V that the harness relies on it; I that the scorer's vLLM has it on] |
| Chunked prefill | On | log line 12 [V ours; I scorer] |
| Speculative decoding | **Off** | `server.py` emits `--speculative-config` only when set (lines 746-750), default None; log line 12 shows none [V ours]; the README lists none [I scorer] |
| KV cache, 31B | 8.74 concurrent sequences of 32,768 tokens (the log prints a KV size of 46,352 tokens; for this hybrid local/global attention model that figure is not a per-sequence budget) | log lines 100-101 [V]; EXP-006 line 77 [V]; the hybrid-attention reading [I] |
| KV cache, other variants | 12B 19.97x, E4B 45.63x, E2B 67.18x at 32k | EXP-006 lines 75-80 [V] |
| Idle KV under one agent | 88.6% on the 31B (1 - 1/8.74) | EXP-006 line 85 [V] |
| Can a submission influence any of these? | **No**, except LoRA right-sizing when `adapters/` exists (`enable_lora`, `max_loras`, `max_lora_rank`). `agent.yaml` has no server key; `generate_content_config` has no `candidate_count` or `n`; `eval_config` has four budget keys | `README:169`; `server.py:781-798`; `tools/submission_rules.py:42-55`; `adk_submission/schema.py:179-202` (`extra="forbid"`); `README:72,98` [V] |
| Does our notebook match the scorer? | **Yes, on every memory and batching setting.** Two differences: `max_loras` 8, which is moot without adapters (no LoRA flags in our argv, EXP-006 log lines 68-70 [V]); and `default_chat_template_kwargs` with thinking on, which the README list does not mention. The second is open [I] and bears on thinking, not on memory or concurrency | notebook lines 280-287 [V]; `README:160-170` [V] |

### 2.2 Q2. Every route to concurrent requests inside one task

Shared by all routes, whatever the shape:
- **One tool-call counter and one turn counter per task.** They are `tool_calls_used` and `llm_calls_used` (`context.py:139-140`). `check_budget` refuses calls at either cap (`context.py:468-551`) [V].
- **Every model call of every agent counts as a turn**, sub-agents and parallel branches included. After each run, `llm_calls_used` is set to the larger of itself and the count of model events in the session (`agent_runner.py:880-914`). `handle_adk_event` counts every non-partial model event from the root or any sub-agent (`context.py:277-299`) [V]. This holds whether or not ADK's own per-invocation cost manager is shared between branches. That sharing is [I]: the shallow `model_copy` in `parallel_agent.py:35-48` and the PrivateAttr at `invocation_context.py:221` suggest it is, and EXP-007 H4 was inconclusive.
- **One session and one `/workspace`.** One `InMemorySessionService` session per task (`agent_runner.py:675-698`) [V]. `submit_patch` diffs the whole workspace, so parallel coding branches write one tree (`plan.md:1037-1039`; C-015) [V].
- **One task clock.** The whole loop runs inside `asyncio.timeout(max_time_minutes x 60)` (`agent_runner.py:783-786`) [V].
- **Compaction runs for everyone.** It runs before every model call of every LlmAgent and reads the latest prompt token count from any branch. Any branch's prompt at or above 14,336 tokens therefore compacts the shared history, and the summary event has no branch (`.claude/skills/harness-stack/reference/compaction.md`; `README:570-574`) [V]. The summarizer call counts on the clock, not as a turn [V, same file]. ADK issue 7324 (compaction under ParallelAgent) is a risk [M].
- **A pass that ends in text re-runs the whole tree**, up to 3 nudges (`agent_runner.py:783-786`; EXP-040 line 82) [V].

| Route | Concurrent? | What it shares beyond the above | How the next agent reads the outputs | Cost and risk on record |
|---|---|---|---|---|
| **Tool-less `ParallelAgent` branches** | Yes: each branch is an asyncio task in one TaskGroup, merged through a queue (`parallel_agent.py:51-85`) [V] | Each branch's model call is a turn [V] | `output_key` writes the branch's final text (no thought parts) to session state, and a later agent reads `{key?}` (EXP-046 2.1; `schema.py:283`) [V]. Siblings do not see each other's events. A later agent with no branch, at the root, sees every branch's events (`contents.py:748-763`) [V]. `include_contents: none` plus placeholders is the hand-off that ran (EXP-032 2, EXP-040 9.3) [V] | No tool stall. 16 voters took 0.83-1.44 s on 7 of 8 E4B tasks at 385-809-token prompts (EXP-040 lines 325-329) [V]. Each voter is a turn: `max_turns` had to go from 80 to 200 (EXP-040 line 40) [V] |
| **Branches with tools** | Model calls overlap. But a synchronous tool runs on the event loop and stalls every branch: `function_tool.py:223-238`, `run_command` is a plain function (`plan.md:991-994`); EXP-007 stall fraction 0.78 [V] | The tool counter: a prompt-only per-branch limit is not enforced. 21 of 24 EXP-032 localizer branches broke a 5-call limit, and the editor was left with 0 guaranteed calls on 7 of 8 [V]. There is no per-agent cap and no exit tool (EXP-046 0, 2.2) [V] | As above | EXP-032: +72.9 s mean wall paired against Arm R on the 31B, 17 compactions, 0 of 8 resolved (EXP-032 9) [V] |
| **`LoopAgent` around a `ParallelAgent`** | Yes, per iteration | Each iteration costs N turns plus whatever follows. `max_iterations` is a workflow key, at most 500 (`submission_rules.py:48`; `swegemma/config.py:35`) [V]. In practice it is bounded by turns, calls and the clock [I] | `output_key` is overwritten each iteration; history is visible as above [V for output_key semantics in EXP-046 2.1; I for overwrite across iterations] | Multiplies the voter cost by the iteration count. No run on record |
| **`agent_tool`** | **No, in practice.** It runs only when the model emits a call to it. Several calls in one turn would be gathered concurrently (`flows/llm_flows/functions.py:387-405`) [V], but 0 of 3,278 E0 tool-call steps carried more than one call (`plan.md:997`) [V] | It runs a new Runner with a fresh session service and no App (`agent_tool.py:241-249`), so the inner agent has **no compaction** [V for the code; I for the effect]. The parent's plugins propagate (`agent_tool.py:236-240`), so its model events likely count as turns, and its tool calls go through the same `check_budget` [I] | It returns the inner agent's last text. State is copied in and the state delta copied back (`agent_tool.py:251-272`) [V] | No run on record |
| **Anything else in the compile path** | **None found.** `GenerateContentConfig` allows temperature, top_p, top_k, max_output_tokens, stop_sequences, presence/frequency penalty, response_mime_type, seed and thinking_config, and forbids extras: no `candidate_count`, no `n` (`schema.py:179-202`) [V]. Agent classes are LlmAgent, Sequential, Parallel and Loop only; workflow keys are name, description, sub_agents and max_iterations (`submission_rules.py:42-49`) [V]. Limits: 500 agents, depth 50, 500 loop iterations (`swegemma/config.py:35,52-64`; `adk_submission/limits.py:191,193`) [V]. `eval_config` has 4 keys, none for concurrency (`README:72,98`) [V] | | | |

### 2.3 Q3. Wall cost of N concurrent samples

**Measured at real prompt sizes (the anchors):**
- **31B, 3 tool-bearing branches** (EXP-032 9): +72.9 s mean wall per task against Arm R, paired (SD 83.3, SE 29.4). The first editor step came at 180-308 s. The figure is confounded by extra calls and 17 compactions; every task's peak prompt was 14,925-18,556 tokens [V].
- **E4B, 16 tool-less voters** (EXP-040 9): the burst took 0.83-1.44 s on 7 of 8 tasks and 11.49 s on one, at 385-809-token prompts. Mean task wall was 86.5 s, with 0 capped [V].

**Synthetic burst ratios.** EXP-006 lines 75-94 measured a decode-bound burst of about 256-token outputs on short prompts against an idle server (EXP-040 line 208 describes the setup):

| Model | speed-up at N = 4 | speed-up at N = 16 | per-request latency factor N / speed-up |
|---|---|---|---|
| 31B | 3.60x | 9.85x | 1.11x at 4, 1.62x at 16 [I] |
| E4B | 3.47x | 9.45x | 1.15x at 4, 1.69x at 16 [I] |

**Not measured on either model:** N concurrent prompts of about 15k tokens under 2,048-token chunked prefill, with or without a shared cached prefix. Any shape has to fill that gap before it can be costed. Nothing above N = 16 is measured (EXP-040 line 208) [V].

**Room against the 10.5 h rule at 120 tasks:**
- **31B, v24 at 8 min (EXP-028 9.1):** mean wall 297.4 s, projected 10.04 h, row T2 fired. The room is 13.8 s per task (EXP-032 line 106) [V]. Decode-only lower bounds for one added burst of 256-token outputs at the 29.8 tok/s probe (EXP-032 9) [I]:
  - 8.6 s at N = 1;
  - about 9.5 s at N = 4;
  - about 13.9 s at N = 16.

  So **there is no break-even N: one burst per task at any N uses 62% to all of the room** before prefill and thinking tokens. A whole extra loop per branch (a best-of-N attempt) would add about 11% at N = 4, about 30 s [I], twice the room.
- **E4B single loop (EXP-038 9):** mean wall 85.7 s, E7 2.98 h, room 225.6 s per task (line 571) [V]. At the 56.2 tok/s probe, one 256-token burst costs about 4.6 s at N = 1 and about 7.7 s at N = 16, decode only [I]. That is about 29 such bursts per task before the room is gone. The KV ceiling is at least 45.6 concurrent 32k sequences [V]. C-023's history puts the dev-48 mean a voting tree must stay under at about 311 s [V].
- **Memory is not the binding limit on either model:** at N up to 16 both stay under their measured 32k concurrency (8.74x is the 31B's ceiling; above that, sequences queue) [I].

### 2.4 Q5 inputs. The 31B against the E4B

- 31B Arm R resolved 9 of 48; the E4B single loop resolved 5 of 48. The pair is discordant 4-0, McNemar p 0.125: the direction is against the E4B, not significant on dev-48 (EXP-038 9) [V].
- The board MDE is about 4 tasks (`plan.md` 5.5) [V].
- Spare time per task: E4B about 225 s, 31B about 14 s (above) [V].

## 3. Endpoints

This is a desk check, so the endpoints are the answers, not counts:
1. Q1: scorer task concurrency, the six server settings, submission control, notebook match.
2. Q2: for each route, whether it is concurrent; whether it shares the tool counter, turns, `/workspace` and compaction; and the hand-off.
3. Q3: the per-burst wall cost against the per-task room on each model, and whether a break-even N exists.
4. Q4: the ranked shapes, each with consumer, selector (and whether it exists without hidden tests), runs on record, the failure it would hit, and the cheapest kill screen.
5. Q5: whether any surviving shape changes the model choice.

## 4. Pre-registered readings (applied in section 9 as written)

- **R1, 31B excluded.** If the 31B's per-task room is below the decode-only cost of one added 256-token burst at N = 1, no 31B shape is screened. This holds unless a re-balanced cap can create room without cutting the calls of a loop the record shows to be call-bound (EXP-028: 37.5% end at 28 calls).
- **R2, a shape survives the desk check** only if all three hold:
  - (a) its concurrent requests carry no tool that shares the counter with the editor without a hard bound;
  - (b) it has a selector computable without hidden tests that the record does not already show to be inert;
  - (c) its decode-only cost fits the model's room.
- **R3, no shape fits.** If no shape meets R2, nothing is built or screened for this direction. The lead reports to the user that the record gives no buildable full-VRAM pipeline, and why.
- **R4, unmeasured.** A shape that meets (a) and (c), but whose selector is unmeasured rather than shown inert, goes forward only to the cheapest named screen, priced. It is never sent straight to dev-48 or to an upload.
- **R5, model choice.** A shape changes the model choice only if it runs only on the E4B and its plausible gain exceeds the 31B-E4B gap (4 tasks on dev-48) plus the board MDE (about 4 tasks). Otherwise the record's choice stands.

## 5. What this licenses

At most one screen. Under R4 that is a zero-GPU read of an existing run, then a smoke-8 at about 0.3 GPU-h on the E4B. It licenses no dev-48 arm and no upload. `plan.md` 5.8 still requires a dev-48 run with projected worst case at or under 11 h before any submission.

## 6. Exact commands

None were run beyond reading files. The reads were:
- `grep` and `sed` over `data/raw/HARNESS_README.md`, the wheel sources under `data/src/` and the wheelhouse, and our own kernel log under `runs/EXP-006-vllm-concurrency-probe/`;
- reads of the EXP files cited.

No trace text is reproduced.

## 7. Defects and limits of this desk check

1. The scorer's `scripts/inference.py` is not on disk. Every scorer setting beyond the README's list is the vLLM default by inference [I]. This covers max_num_seqs, batched tokens, prefix caching and chunked prefill.
2. "Sequential" rests on the competition brief [V per brief]. Its source page was not re-read in this job.
3. The latency factors come from a synthetic burst on short prompts. No concurrent measurement at 15k-token prompts exists on either model.
4. The decode-only costs in 2.3 are lower bounds: they leave out prefill, thinking tokens and the voter-to-actor hand-off.
5. Whether `agent_tool` inner calls count as turns is [I], from plugin propagation. No run on record tests it.

---

## 8. Built

Nothing. Zero GPU-h.

## 9. Results (2026-11-06; section 4 applied as written)

### 9.1 Answers

1. **Scorer.** The scorer runs tasks sequentially [V per brief]. It serves with:
   - tp 4, gpu util 0.90 and max_model_len 32,768 [V];
   - max_num_seqs 256, 2,048 batched tokens, prefix caching and chunked prefill on [V ours, I scorer];
   - speculative decoding off.

   The 31B gets 8.74 concurrent 32k sequences, 88.6% idle under one agent. A submission controls none of these except LoRA sizing. Our notebook matches on every memory and batching setting. One difference is open: the thinking template kwarg.
2. **Concurrent requests.** Only `ParallelAgent` gives real concurrency, with or without a Loop around it. Every route shares:
   - the one tool counter;
   - the one turn counter (each branch's call is a turn [V]);
   - `/workspace`;
   - the clock;
   - compaction, which any branch's 14,336-token prompt triggers for all.

   Tool-bearing branches add the event-loop stall (0.78) and counter starvation (EXP-032). `agent_tool` is sequential in practice: 0 of 3,278 steps carried more than one call. It also runs without compaction. Nothing else in the compile path issues parallel samples: there is no `candidate_count` or `n`. Outputs pass by `output_key` and `{key?}`, or by root-level visibility of branch events.
3. **Wall cost.** The anchors at real prompt sizes:
   - 31B, 3 tool branches: +72.9 s per task (confounded);
   - E4B, 16 tool-less voters at short prompts: about 1 s per burst.

   The synthetic latency factors are 1.1x at N = 4 and 1.6-1.7x at N = 16 [I]. The 31B has no break-even N: its 13.8 s room is used up by one 256-token burst at N = 1 (8.6 s) to N = 16 (13.9 s) [I]. The E4B has room for about 29 bursts of N = 16 (decode only) in its 225.6 s [I]. Concurrent ~15k-token prompts are unmeasured on both models.
4. **Shapes:** see 9.2.
5. **Model choice.** Only the E4B has room for any shape. Under R5 the surviving shape would have to beat the 4-task dev-48 gap plus the board MDE, about 8 tasks over the E4B single loop. EXP-034's best free selector reaches +3.0 over a random arm. So no shape changes the choice on the record [I].

### 9.2 Ranked shapes

| Rank | Shape | Consumes the samples | Selector, and does it exist without hidden tests | Runs on record, failure it would hit | Cheapest kill | R2 / R4 verdict |
|---|---|---|---|---|---|---|
| 1 | **No shape fits on the 31B** | | | EXP-028 T2 (10.04 h, 13.8 s room). EXP-032 (+72.9 s). Re-balancing the cap: 37.5% already end at 28 calls with 0 resolved, so taking calls or minutes away to buy parallel room removes the room the loop needs | Already killed by on-disk numbers (L0) | **R1 fires**: no 31B shape is screened |
| 2 | **E4B: k tool-less samples with different prompts at one decision point** (for example, which file to edit, or which candidate edit to apply), then one actor | A vote or a pick by the actor | Majority vote exists without hidden tests. Whether it carries signal is unmeasured for prompt-diverse voters. The identical-prompt form had none, and the C-015 literature finds majority vote adds nothing | EXP-040: 16 identical voters, winner = voter 1 on 8 of 8 (D = 0), row 2 fired. It would hit the same inert vote if diversity does not split the votes. Turns: about 16 per burst (`max_turns` raised to 200) | L1: read the EXP-040 per-task vote spread at zero GPU. If voters already disagreed and the vote still matched voter 1, diversity has nothing to add. Then smoke-8 on the E4B, about 0.3 GPU-h (EXP-040 cost 0.30-0.36) | (a) yes, (c) yes, (b) unmeasured: **R4, the only survivor** |
| 3 | E4B: k tool-less reviewers of the final diff, gating submit or continue | A gate on submit | The model's own judgment of its patch. EXP-034 Q2-neither: visible tests do not separate right from wrong patches on the RFWF group. C-015: no signal without hidden tests | None run | No on-disk read can test it. A smoke-8 at about 0.3 GPU-h | (b) has no evidence for it. Ranked below 2. **R4 only if the lead wants a second screen**; it does not meet R2 as written |
| 4 | E4B: a `LoopAgent` around shape 2 or 3 | Repeated votes | The same as 2 or 3 | None run. It multiplies turns and restarts (a pass that ends in text re-runs the tree) | Only after 2 passes its screen | Inherits 2's status; not screened first |
| 5 | Parallel read-only localizers feeding one editor (either model) | The editor reads their plans | No selection: the editor merges | EXP-032: 21 of 24 broke the limit; the editor had 0 guaranteed calls on 7 of 8; 17 compactions; 0 of 8 resolved. EXP-046: no per-agent cap exists | Already killed by on-disk data (EXP-032 9) | Fails (a): excluded |
| 6 | N whole-loop attempts with best-of-N selection | N patches | None without hidden tests: EXP-034's best proxy is +3.0 of 48, below the MDE of 4 | Structurally blocked: one `/workspace`, one diff (`plan.md:1037-1039`). A sync tool in any attempt stalls all of them (EXP-007 H3 0.78). The counter is shared. On the 31B it is also about twice the room | L0 (here) | Fails (a) and (b): excluded |
| 7 | `agent_tool` fan-out | | | 0 of 3,278 multi-call steps: no concurrency in practice | L0 (here) | Not a full-VRAM shape |

**Readings applied.**
- **R1 fires** for the 31B.
- **R2 is met by no shape.**
- **R4 fires for shape 2 only.** The cheapest next step is the zero-GPU read of the EXP-040 vote spread. A smoke-8 at about 0.3 GPU-h follows only if that read leaves room.
- **R3 does not fire as a whole,** because shape 2 is unmeasured rather than shown inert. It does fire for the 31B and for every shape with tools.
- **R5:** no change of model on the record.

The user's "submit it" is not reachable from this desk check. Any shape needs a screen, then a dev-48 run, before `plan.md` 5.8 allows an upload.

## Status

DESK CHECK DONE 2026-11-06, zero GPU-h. R1 fires (31B). R4 fires for one E4B shape (prompt-diverse tool-less voters at one decision point). Next, if the lead takes it: a zero-GPU read of the EXP-040 vote spread. Nothing built.
