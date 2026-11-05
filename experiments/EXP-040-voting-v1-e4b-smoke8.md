# EXP-040 — Voting agents V1 on the E4B, smoke-8 screen (C-023): sixteen tool-less voters at one vote point, paired against EXP-033

**Date:** 2026-11-05
**Type:** smoke-8 screen, one arm, about 0.31-0.37 L4x4-h expected (conditional worst case about 1.2 h, section 2 gives the arithmetic). **Built, not pushed**: the user has not approved this screen's GPU.
**Cohort:** smoke-8
**Ladder:** L2. L0 is EXP-039 (expressibility, termination, vote format, bound on N, failure modes F1 to F11). L1 cannot read it: no E4B trace holds a candidate list, a vote or a multi-agent run.
**Pre-registered:** this file, the tree, the zip's recorded sha and the notebook are committed before any push. Sections 3 to 5 are written blind and are not revised; results are appended as a new section.
**Serves:** C-023 (hypothesis, D-005), the user's decision of 2026-11-05 about 17:30 UTC: voting agents "with varying temps", a deterministic tie rule, and "maximum allowed agents" on the E4B.
**Relates:** EXP-039 (the desk check this builds and whose section 4 readings it copies), EXP-033 (the reference arm on the same 8 ids and the source tree), EXP-038 (E4B dev-48, not touched), EXP-032 (P1: a prompt-only call limit did not hold; ParallelAgent in the real harness), EXP-006 (concurrency X(N)), D-004.
**Tags:** [V] verified in source, trace or by a check run here, [M] community or mirror, [I] inference.

## 1. Why this, now

The user asked for agents that vote on the best next move. EXP-039 found that the one design that is both expressible and enforceable is a single vote point: `Sequential[proposer, Parallel[N voters], actor]`, and that the E4B has the clock for it (EXP-033: mean 423 s and minimum 389 s left under the 480 s cap, 6.0 s per model turn, 0 of 8 capped). This file builds that design at N = 16 (the largest N with a measured concurrency X, 9.45 in EXP-006) and fixes the readings before any trace exists. The lead is putting the cost to the user; the kernel is not pushed in this job.

Reference arm: EXP-033 on the same 8 ids (`experiments/EXP-033-e4b-single-loop-smoke8.md` section 9). Per task: requests_7309 27.9 s, requests_7205 89.6 s, fastapi_14448 56.8 s, fastapi_14301 31.3 s, httpx_3672 60.4 s, fastapi_14605 90.7 s, rich_3468 56.2 s, rich_3006 42.6 s; mean 56.9 s, 9.5 turns, 5.4 counted calls, 0 of 8 capped, 6 of 8 non-empty patches, resolved 2 of 8 (fastapi_14301, rich_3006; recorded, not read).

## 2. Design

### 2.1 The tree

`experiments/EXP-040/candidate-v1/` is built from `experiments/EXP-033/candidate-e4b/` (EXP-027's v24-at-8 prompt, `model: gemma-4-e4b-it-qat-w4a16-ct`). 20 agents, 26 files.

```
swe_agent (SequentialAgent)
  proposer   LlmAgent, read_file + get_status, include_contents none, output_key cands
  vote       ParallelAgent
    voter_01 .. voter_16   LlmAgent, tools [], include_contents none, output_key vote_01 .. vote_16
  actor      LlmAgent, the six EXP-033 tools, include_contents default, instruction = v24 + one inserted section
```

**Every difference from the EXP-033 tree** (the screen's variables; `diff -rq experiments/EXP-033/candidate-e4b experiments/EXP-040/candidate-v1` lists the files, the two modified ones are diffed below):

| # | Difference | File | Why |
|---|---|---|---|
| 1 | Root changes from one `LlmAgent` to a `SequentialAgent` with three sub-agents | `agent.yaml`, `sub_agents/{proposer,vote,actor}.yaml` | the design under test |
| 2 | New proposer: E4B, `read_file` and `get_status` only, at most 4 reads of at most 120 lines, ends with an `ISSUE:` line (at most 120 words) and at most four lettered candidates, `output_key: cands`; sampling temperature 1.0, `max_output_tokens` 4096 (EXP-033: 8192), `thinking_budget` 1024 (EXP-033: 4096) | `sub_agents/proposer.yaml`, `prompts/proposer.md`, `configs/sampling_proposer.yaml` | a short plan, so the voters have options and the proposer cannot spend the actor's clock |
| 3 | 16 voters: E4B, `tools: []`, `include_contents: none`, one shared instruction file, `output_key: vote_NN`; temperatures 0.20, 0.28, 0.36, 0.44, 0.52, 0.60, 0.68, 0.76, 0.84, 0.92, 1.00, 1.08, 1.16, 1.24, 1.32, 1.40 (voter 1 lowest); `top_p` 0.95, `top_k` 64, `max_output_tokens` 256, `thinking_budget` 0, `include_thoughts` false; reply `PICK: X` | `sub_agents/vote.yaml`, `sub_agents/voter_01.yaml` .. `voter_16.yaml`, `prompts/voter.md` | the vote; the voters differ in temperature and nothing else |
| 4 | Actor prompt is the v24 text byte for byte plus one inserted section ("Team plan and votes", 26 lines, before "## 1. Contract") that carries `{cands?}`, `{vote_01?}` .. `{vote_16?}` and the tally and tie rule as sentences; the actor runs on default contents. The inserted text alone is in `experiments/EXP-040/actor_insert.md` | `prompts/actor.md` (EXP-033's `system.md`) | the actor must see the plan and the votes and apply the rule |
| 5 | `max_turns` 80 to 200 (the other three values, 240 / 28 / 8 min, are EXP-033's) | `eval_config.yaml` | every model event of every agent counts as a turn (`context.py:277-299`); one pass is about 34 turns (check c) |
| 6 | The actor's sampling file is EXP-033's `configs/sampling.yaml` unchanged (temperature 1.0, 8192 output, thinking 4096) | `configs/sampling.yaml` | the actor is the EXP-033 agent |

```
$ diff -u experiments/EXP-033/candidate-e4b/eval_config.yaml experiments/EXP-040/candidate-v1/eval_config.yaml
+# EXP-040 2026-11-05: max_turns 80 -> 200. (comment, 2 lines)
 evaluation:
   timeout_seconds: 240
   max_tool_calls: 28
   max_time_minutes: 8
-  max_turns: 80
+  max_turns: 200
```

`prompts/actor.md` against `prompts/system.md`: one hunk, `@@ -5,6 +5,32 @@`, 26 added lines after "## Budget", nothing removed. The actor is told to state the counts and the winner in one sentence that ends "The winner is X." so that the stated winner can be compared with the recomputed one by code.

Every changed value in YAML carries a dated `EXP-040 2026-11-05` comment in the file. Prompts carry no braces other than the 17 placeholders (checked, 17 lines in `actor.md`, 1 in `voter.md`), no forbidden lint word and no URL.

### 2.2 The F11 fix, and why this one

EXP-039 section 7 item 7 (F11): with `include_contents: none` the context window starts at the latest user event or at another agent's reply (`contents.py:569-580`), so a voter or an actor on `none` never sees the task message. Three ways out:

1. **The proposer's `ISSUE:` line reaches the voters through `{cands?}`, and the actor runs on default contents (chosen).** The voter prompt is the same few hundred tokens for all 16 voters, so the vote differs by temperature only. The actor keeps the whole history (the task message, the proposer's reads, the votes as "For context" lines) and the v24 prompt works as it did.
2. Voters on default contents. They would see the task message and the proposer's whole read trace (up to 4 x 120 lines), so a prompt of 4k to 9k tokens times 16, near the compaction threshold, and the voters would no longer be a cheap burst. Rejected on cost and compaction risk.
3. Pass the task text through session state. There is no state key for the task message in the harness path. Rejected as unavailable.

The price of (1): the voters judge the candidates on the proposer's 120-word restatement, not on the issue text. So this screen tests the vote on the proposer's summary, not on the issue. If that summary is wrong the vote cannot be right; C and A (section 3) read it.

### 2.3 Zero-GPU checks, with commands and results

**(a) Validator on the real tree, strict.** `python tools/validate_submission.py experiments/EXP-040/candidate-v1 --strict` gives 26 files, 20 agents, `RESULT: INVALID (1 errors, 2 warnings)`. The one error is the packing gate, `120 x (8 + 1.0 setup) min = 18.00 h (gate 11.0 h)`, expected: a screen at 8 minutes needs `--skip-budget-gate`, as EXP-032 and EXP-033 used (stated here, and recorded in section 6). The two warnings are expected and carried from the EXP-032 P1 tree: "sub-agent with submit_patch can end the session from inside a sub-call" (the actor) and "timeout_seconds=240 < 300 may also cap the grading pytest run (VERIFY(Q2))". There is no "no tools declared" warning on the voters (`tools: []`). The two info lines on thinking being ON for the proposer and the actor are the EXP-033 situation (VERIFY(Q3)). The official validator (`--official`) is not importable here and was not run [V].

**(b) The template path.** Source: `data/src/google_adk/google/adk/utils/instructions_utils.py:81-124`, regex `{+[^{}]*}+` (line 124). [V] from the source lines:
- a trailing `?` makes the key optional (84-86); a key that is absent from `session.state` renders as the empty string when optional (115-120) and raises `KeyError` otherwise (122), so every placeholder carries `?`;
- a value that is `None` renders as the empty string (111-112); any other value is `str(value)` (113);
- a name that is not an identifier is returned unchanged (107-108), so prose with braces is left alone, and the substitution is a single pass over the template, so braces inside an injected `cands` are not templated again (73-79).

The test file `experiments/EXP-040/test_template_relay.py` runs the real prompt files through (i) the real `inject_session_state` if `google.adk` imports and (ii) a line-for-line port of lines 70-149 that runs anywhere. Command: `python -m pytest experiments/EXP-040/test_template_relay.py -q -rs`. Result: the port tests (empty state, filled state with a `None` vote and braces inside `cands`, every placeholder optional and a valid name, 17 placeholders in `actor.md`, a required key raises) pass; the two real-ADK tests are SKIPPED: `google.adk does not import here: ModuleNotFoundError("No module named 'opentelemetry'")`. So the relay has been proved against the source's logic, not against the installed package; the first kernel is the first run of the real one [V for the port, I for the package].

**(c) Prompt size and turn counts.** Source numbers: prompt tokens at the first call of the 8 EXP-033 traces, 2.3k to 3.0k (2,342 to 3,030) [V]; the compaction threshold is 14,336 on the latest prompt-token count (`.claude/skills/harness-stack/reference/compaction.md`).
- Voter prompt = the 100-token template + `cands`. A realistic `cands` (ISSUE 120 words about 170 tokens, four one-sentence candidates about 160) gives **about 0.5 to 0.7k tokens**. Worst case: the proposer ends at its 4096-token cap and all of it is text, **about 4.3k**. 30% of the threshold at worst, 5% at realistic. [I for the realistic length: no E4B candidate list exists on disk]
- Actor's first call: v24 and the task message (2.3k to 3.0k as in EXP-033) + the inserted section (0.5k to 4.3k with `cands`, 0.15k for the votes) + the proposer's reads that default contents carry (the proxy assumes all four reads, each about 0.9k to 1.5k tokens for at most 120 lines [I]). **Proxy range about 6.7k (2.3 + 0.65 + 4 x 0.94) to 13.5k (3.0 + 4.3 + 0.15 + 4 x 1.5), under 14,336 at the top by 0.8k.** A proposer that reads less gives less. Its later calls may compact, as in EXP-033 (1 of 8). A compaction summarizer call counts on the clock, not as a turn. The parallel stage holds only text events, so ADK issue 7324 does not apply there [I].
- Turns per task against `max_turns` 200 (the F7 correction: the 3-nudge limit applies only to passes without a tool call; a pass that ends in text re-runs the whole tree, bounded by the 28-call cap shared with the proposer's reads, the 8-minute clock and the turn cap):

| passes | turns (about 8 proposer + 16 voter + 10 actor = 34 per pass) | against 200 |
|---|---|---|
| 1 | 34 | 17% |
| 2 | 68 | 34% |
| 4 | 136, stress 140 | 68% to 70% |
| 5 | 170 | 85% |
| 6 | 204 | exceeds; the turn cap or the clock ends the task here |

`max_turns: 80` would end a task in its third pass, which is why it is raised. A restart costs one pass of about 34 turns, of which 16 are the parallel voters; in time about 35 to 60 s [I] (proposer and actor turns are serial at 6.0 s, the 16 voters are one concurrent burst of about 5 to 15 s).

**(d) Tally and tie rule by code.** `experiments/EXP-040/tally.py` is a pure function of the proposer's text and the voters' texts as the trace records them (`extra.author` of each agent step: `proposer`, `voter_01` .. `voter_16`, `actor`): `candidate_letters`, `parse_vote` (a line that is exactly `PICK: X`, X a candidate letter), `tally` (most votes; a tie goes to the tied letter picked by the lowest-numbered voter; no valid vote gives A), `d_flag` (D for one task: winner differs from voter 1's pick; undefined when voter 1's vote is invalid), `stated_winner` (the actor's "The winner is X"), and `extract_rounds` for a trace with restarts. `experiments/EXP-040/test_tally.py` has 11 cases: clear majority, tie to the lowest voter, a lower voter whose letter is not in the tie, no valid vote, malformed lines, a letter outside the set, candidate extraction, the D definition, the stated winner, a two-pass extraction fixture, and a trace with no votes. Command and result: `python -m pytest experiments/EXP-040 -q -rs`: 15 passed, 2 skipped (the two real-ADK tests of (b)).

How **A** (the actor followed the winner) is judged: by hand on the 8 traces, blind to the resolved flag. A task counts as followed when the first `edit_file` or `write_file` call touches the file the winning candidate names and the edited span lies in the function or change that candidate names; if the candidate names only a file, a file match is enough; an ambiguous case counts as not followed. The file-level match is also recorded (A_file) and is a supporting number. Separately the code checks whether the actor's stated winner equals the recomputed W (counting fidelity, not following fidelity).

How to run the recompute after the run: `tally.py` takes a traces directory (`main(argv)`), but this agent's shell can run only `python tools/` and `python -m pytest`, so the post-run call needs the experimenter or a thin wrapper under `tools/` (not written here, `tools/` is not mine).

### 2.4 Cost

| item | seconds | basis |
|---|---|---|
| kernel overhead (boot 322.9 s, decode probe, teardown) | about 445 | EXP-033: kernel span 900 s minus 455.5 s of tasks |
| per task, single loop | 57 | EXP-033 mean |
| proposer (about 8 serial turns) | +30 to 48 | 6.0 s per turn |
| 16 voters, one concurrent burst | +5 to 15 | X(16) = 9.45 on short prompts [I above 4 on real prefills] |
| actor, longer prompt and the tally sentence | +5 to 15 | |
| per task, point | 79 to 105 | |
| 8 tasks + overhead | 1,077 to 1,285 s | = **0.30 to 0.36 GPU-h**, the 0.31 to 0.37 of EXP-039 |

**Conditional worst case about 1.2 GPU-h**: every task at the 495 s cap plus overhead, 8 x 495 + 445 = 4,405 s = 1.22 h. EXP-033's tasks ran at 57 s, so this needs every pass to restart until the clock. **What a restart costs:** about 34 turns, 35 to 60 s per extra pass per task, so two tasks with one extra pass add about 0.03 h. **What a failed screen costs to re-run:** if row 0 fires and the one cause is fixed, one more kernel of 0.30 to 0.36 h; the lead owns the ledger and the user's ceiling.

`pack_submission.py --skip-budget-gate --allow-warnings` is used: the screen's 8-minute setting is above the 4.5-minute packing gate (as EXP-032 and EXP-033), the gate is for the real submission, and a screen is never uploaded.

## 3. Endpoints, fixed in advance

Counts over the 8 tasks, read from `runs/EXP-040-v1/.../traces/trace_<id>.json`, `summary.jsonl` and the kernel log, and from `tally.py`. Reference for each is EXP-033's table.

| # | Endpoint | Definition |
|---|---|---|
| E1 | C | per task, distinct lettered candidates in the proposer's final text (`tally.candidate_letters`) |
| E2 | Parseable votes | per task, valid `PICK: X` lines of 16; a task is "voted" at 12 or more |
| E3 | D | tasks of 8 where the recomputed winner W differs from voter 1's pick P1 (undefined when P1 is invalid, reported apart) |
| E4 | Tie rule | tasks where W was decided by the tie rule; the actor's stated winner against W |
| E5 | A | tasks where the actor's first edit follows W (hand check, section 2.3 d) |
| E6 | F11 check | the voter prompt in the trace contains the `ISSUE:` line; the actor's first message mentions the issue |
| E7 | Passes and turns | per task, rounds from `extract_rounds`; model turns from the trace against 200 |
| E8 | Wall | per task and mean (EXP-033 mean 56.9 s); capped (calls 28, turns 200, time 480 s, as E6 of EXP-033); vote-stage wall from the first to the last voter step timestamp |
| E9 | Malformed calls, compactions, non-empty patches | as EXP-033 (0 of 43, 1, 6 of 8) |
| E10 | Resolves | recorded only, no rate claimed, not read |

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Copied from EXP-039 section 4, unchanged in substance. The order is first match. Quantities: C, the vote texts, W, P1, D and A as defined above and in section 3.

| Row | Condition | Reading |
|---|---|---|
| 0 | infrastructure: a crash in more than 2 of 8, or fewer than 6 of 8 tasks with at least 12 of 16 parseable votes, or the tree does not run | fix the one cause (for example F5) and re-run once; no reading |
| 1 | C >= 2 in fewer than 6 of 8 tasks | the proposer yields no real alternatives; kill V1 as specified and send the gap (EXP-039 Q6, 2) to the lit-scout; the claim is not killed, its candidate source is |
| 2 | D = 0 of 8 | the vote never changed a pick: kill V1 as specified (at N = 16 the voters and voter 1 always agree); C-023 stays a hypothesis pending a prompt-diverse variant |
| 3 | A <= 4 of 8 | the actor does not follow the tally; the vote is decorative; fix the actor prompt, not N |
| 4 | mean wall > 140 s, or 3 or more of 8 capped, or any task past 480 s | the vote costs more than the room (EXP-033 mean 56.9 s); report seconds per vote point; no dev-48 arm at this N |
| 5 | D >= 1, A >= 6 of 8, wall within row 4's bounds | the mechanism works: promote to one dev-48 E4B arm paired against EXP-038, same 48 ids |
| 6 | otherwise | no decision |

Recorded in every row, not read: resolves (E10) and the counts E4, E6, E7, E9.

**Blind prediction.** Loop functions: 75%. C >= 2 in at least 6 of 8: 65%. D >= 1: 60%, because the proposer's candidates are near-duplicates and a spread of temperatures sometimes flips a close call. Voted (at least 12 of 16 parseable) in 6 or more of 8: 70%. A >= 6 of 8: 55%. At least one task with more than one pass: 50%. Mean wall 90 to 130 s, kernel 0.30 to 0.40 h. Row 5 about 25%, row 2 about 20%, row 1 about 20%, row 4 about 10%, row 0 about 15%, rows 3 and 6 the rest. Resolves 1 to 3 of 8, recorded not read.

## 5. What this licenses

**The screen can decide one of two things.** It can **kill V1 as specified** (row 1: no real alternatives, row 2: the vote is inert at N = 16, row 3: the actor ignores the tally), or it can **promote V1 to one dev-48 E4B arm** (row 5). It cannot decide that voting does not help the E4B, and it cannot decide that it does: n = 8, resolves are recorded and never an endpoint.

**The dev-48 endpoint if row 5 fires.** Paired resolves against EXP-038 (the E4B single loop on the same 48 ids; McNemar, discordant pairs reported), plus D and A on 48, mean wall, cap incidence and the projected 120-task hours (must stay at or under 11 h at the setting the arm uses). A vote-stage wall at N = 16 and the one-pass share are reported so that a scale-up (section 7) can be costed. Estimated cost of that arm: 48 x 79 to 105 s + overhead = 1.2 to 1.6 GPU-h [I], to be recomputed from this screen's wall before the ask.

Rows 1 to 3 keep C-023 a hypothesis; row 5 asks for a dev-48 arm and for no upload. No row licenses an upload.

## 6. Exact commands

```
python tools/validate_submission.py experiments/EXP-040/candidate-v1 --strict
python -m pytest experiments/EXP-040 -q -rs
python tools/pack_submission.py --src experiments/EXP-040/candidate-v1 --out dist/EXP-040-v1.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed dist/EXP-040-v1.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-040-v1"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp040_v1/kaggle_eval_l4x4.ipynb
# push, a later job, only after the user approves the GPU and the lead dispatches it:   kaggle kernels push -p notebooks/exp040_v1
# after COMPLETE, a separate job:
kaggle kernels output rainm4/gemma4-exp040-v1 -p runs/EXP-040-v1/
python tools/analyze_traces.py <inner bundle dir> --cap-minutes 8 --max-calls 28
python tools/run_forensics.py forensics <inner bundle dir>
python tools/run_forensics.py compare runs/EXP-033-e4b/runs/EXP-033-e4b <inner bundle dir>
# D, A-support and tie-rule fidelity: tally.main(["tally.py", "<inner bundle dir>/traces"])  (a wrapper is needed, see 2.3 d)
```

## 7. Defects, and two paragraphs that are not run

**Defects known at writing.** (1) The real ADK substitution has not run: `google.adk` does not import here (no `opentelemetry`), so (b) is a source read plus a port. (2) The realistic `cands` length is an estimate: no E4B candidate list exists on disk. (3) The voters decide on the proposer's restatement (2.2), so a bad `ISSUE:` line makes a bad vote, and C and A cannot tell the two apart. (4) `thinking_budget: 0` and `include_thoughts: false` are validated but whether the E4B template honours them is unverified (F5); the first trace shows it. (5) The actor on default contents inherits the proposer's reads, so its first call may sit close to 14,336. (6) `tally.py` cannot be run by this agent's shell outside pytest; a wrapper under `tools/` or the experimenter's hand is needed after the run. (7) A is a hand judgement by one reader.

**Not run, second arm A: the per-step version** (the user's "vote for the best next move"). It is `LoopAgent[proposer, Parallel[voters], actor]`, and it can be screened honestly only if the executor stops after one counted call per round. The harness has no exit tool and the prompt-only rule failed in EXP-032 P1 (21 of 24 localizers ignored a 5-call limit), so the first thing needed is a zero-GPU read of that rate on traces that exist: the share of actor invocations that end after exactly one counted call (EXP-032 P1 traces and, from this screen, the actor's text-only turns), and, if that is inconclusive, a 3-task two-round stub loop whose executor is told to make one call and reply DONE, about 0.13 to 0.2 GPU-h, boot-dominated [I]. What from this screen would justify trying it: row 5, D >= 2 of 8 (the vote changes the pick more than once at a single point), A >= 7 of 8, mean wall under 90 s (per-step costs about 4.7 times the single loop, EXP-039 Q5), and a one-call rate of at least 80% in the zero-GPU read. Otherwise per-step voting is not screened.

**Not run, scale-up to "maximum": about 100 voters at one vote point.** Nothing above X(16) = 9.45 is measured, and EXP-006 measured decode-bound 256-token bursts on short prompts, which overstates X under real prefills. The first thing needed is a concurrency probe at real prompt sizes: a bursts-only kernel (no agent, the E4B boot plus bursts of 16, 32, 64 and 100 identical requests at 0.5k and 4.3k prompt tokens, `max_output_tokens` 256), about 0.1 to 0.15 GPU-h with the 0.125 h boot dominating [I]. It is not pre-registered here and it needs its own approval. The vote stage itself would add about 5 to 30 s per task (EXP-039 Q5) and 100 turns per pass against `max_turns` 200, so N = 100 leaves room for one pass and a restart only if `max_turns` goes to 500, the schema limit.

## 8. Built

(filled in after the pack and the notebook build)

## Status

2026-11-05: written, tree built, checks (a) to (d) run, **not pushed**. Awaiting the user's GPU approval, then the lead's dispatch of the push.
