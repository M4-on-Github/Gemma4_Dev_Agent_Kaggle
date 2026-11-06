# EXP-046 — Sequential role team on the E4B, `SequentialAgent[locate, edit, check]`: desk check (D-006 stage 0)

**Date:** 2026-11-05
**Type:** desk check (L0, zero GPU). A smoke-8 screen is specified in sections 3 and 4 and **is not built**: the desk check does not pass (section 2.2, row Q2).
**Cohort:** smoke-8 (for the specified, unbuilt screen)
**Ladder:** L0. No trace mining was needed: the stage-ending question is answered by the harness source, and the one real Sequential run on the E4B (EXP-040, same cohort) gives the measured stage times.
**Serves:** C-023, C-024, D-006 (new idea 1, "bound each agent by what it is given, not by what it is told", and its Stage 3).
**Relates:** EXP-039 (the voting desk check, whose F-table this one reuses), EXP-040 (the only Sequential tree that has run), EXP-032 (P1: a prompt-only call limit held on 3 of 24), EXP-033 and EXP-038 (the single-loop references), EXP-043, EXP-044, EXP-045.
**Tags:** [V] verified in the harness source or the validator, with file:line; [M] mirror; [I] inference; [H] hand judgement.

## 0. Verdict, first

**The desk check does not pass, and nothing is built.** The lead's question has a yes-half and a no-half.

- **Yes:** each stage can be given its own tool list, and a stage hands its result on by `output_key` and `{key?}`. A tree `Sequential[locate, edit, check]` is valid and has run on the E4B in the same shape (EXP-040).
- **No, and it is the kill criterion the lead named:** **only the model can end a stage that holds a tool.** There is no exit tool, no per-stage call cap, no per-stage iteration setting, and no callback hook. A tool bounds *what kind of thing* a stage can do (a reader cannot edit), never *how many times* it does it. The premise "a stage ends because its agent has nothing else it can do" holds only for a tool-less stage, which ends after one reply, and neither locate nor check can be tool-less. So the premise of D-006 new idea 1 is killed for this tree as specified. What survives is a capability split (read / edit / run) whose call counts are prompt-bounded, which is the form EXP-032 (3 of 24) and EXP-040 (5 of 8) already measured.

## 1. Why this, now

D-006 stage 0 asks, before any GPU, whether a team of single-job agents can be bounded by tools. Prompt limits are ignored (EXP-032: 21 of 24 branches; EXP-040: the proposer's 4-read limit held on 5 of 8, with 7, 7 and 13 reads on the others; EXP-043: the E4B paraphrases an exact-copy rule). The harness has one call counter shared by all agents. If a tool list could end a stage, a team would be a way to enforce what a prompt cannot.

## 2. The desk check

### 2.1 Q1. What each stage may be given, and how a stage hands on

| Question | Answer | Source |
|---|---|---|
| Is a sub-agent's `tools` list its own? | **Yes.** Each `LlmAgent` resolves its own `config.tools` and passes exactly that list to the ADK agent; no tool is inherited from the parent or the siblings | `adk_submission/builders/llm.py:62-65` (resolve), `:82` (`tools=tools`) [V] |
| Names accepted | Strings looked up in the harness registry: `run_command, read_file, edit_file, write_file, get_status, submit_patch` (plus three code-graph tools) | `resolvers/tools.py:64-65`; `tools/submission_rules.py:15-18` [V] |
| Empty or absent list | Legal (`tools: list[...] \| None`) | `adk_submission/schema.py:287` [V] |
| Agent classes | `LlmAgent, SequentialAgent, ParallelAgent, LoopAgent`; workflow agents take only `name, description, sub_agents, max_iterations` | `tools/submission_rules.py:42,48` [V] |
| Hand-off | `output_key` stores the stage's final text (thought parts excluded) in session state; a later stage reads it with `{key?}` (the `?` makes a missing key an empty string, not a `KeyError`). Ran in EXP-040 (`cands`, `vote_NN`) | `schema.py:283`; EXP-040 section 9.3 E4 and E6 [V]; templating `instructions_utils.py:81-124` (EXP-039 Q3) [V] |
| Hand-off by the conversation | With `include_contents: default` a later stage also sees the earlier stages' tool calls and results. With `none` its window starts at the latest user event or another agent's reply, so the task message is invisible (F11) | `contents.py:569-580` (EXP-039 F11) [V] |
| What a restricted tool list does not do | `run_command` is a shell: a stage that holds it can edit files (`sed -i`, `python -c`). So **only locate (read_file) and edit (no run_command) are capability-bounded; check is not read-only** | `execution.py:21`; [I] |

**Tool lists chosen.** locate: `read_file`. edit: `read_file, edit_file`. check: `run_command, get_status, submit_patch`. Locate has no search tool: `read_file` takes a path and a line range, and the shell is the only way to grep. It therefore works from the workspace tree printed in the task message, as EXP-040's proposer did (reads 0 to 13 per task).

### 2.2 Q2. What ends each stage

| Stage | Tools | What ends it | Not the model's choice? |
|---|---|---|---|
| Any LlmAgent, with or without tools | | `run_async` loops one model call at a time and breaks **only** when the last event `is_final_response()` (a text-only reply) or is partial | `base_llm_flow.py:866-875` [V] |
| locate | `read_file` | the model emits text | **no** |
| edit | `read_file, edit_file` | the model emits text | **no** |
| check | `run_command, get_status, submit_patch` | the model emits text, or `submit_patch` is called (below) | **no**, except by `submit_patch` |
| a tool-less stage | none | one model reply, always | yes (but has nothing to do) |

What was searched for and not found, each with its source:

- **No exit tool.** The registry holds six tools and three code-graph tools; none ends a stage (`submission_rules.py:15-18`) [V].
- **No per-stage cap.** `max_tool_calls`, `max_turns`, `max_time_minutes` and `timeout_seconds` are the only budget keys, and they are global (`submission_rules.py:64`; the counters are in the one `context`, `agent_runner.py:932-957`) [V].
- **`LoopAgent.max_iterations` does not help.** It bounds how many times the loop runs its sub-agents (1 to 500, `validate_submission.py:446-447`), not calls inside one run of a stage. A `LoopAgent[locate]` with `max_iterations: 1` is a plain stage [V].
- **No callback.** The submission schema has `before_*`/`after_*` callbacks, but the harness compiles the submission without a `callback_registry` (`swegemma/harness/agent_runner.py:616-628`), so `resolve_callbacks` returns nothing (`adk_submission/resolvers/callbacks.py:84-85`), and the validator's key set omits them (`submission_rules.py:43-47`) [V].
- **The shared exits** are the 28-call budget (`agent_runner.py:932-945`), the 480 s clock (`:924-930`), and the turn budget (`:947-957`), each ending the whole task, not a stage. Every model event of every agent counts as a turn (`context.py:277-299`, EXP-039) [V].

**Plainly: only the model can end a stage that holds a tool. This is the kill criterion; it fires.**

What a runaway stage costs is therefore shared, not local. In a Sequential tree the next stage runs only after the current one ends, so a locate stage that never stops reading takes the 28 calls or the clock from edit and check. The measured size of that risk is small and is not a bound: EXP-040's proposer overran its prompt limit on 3 of 8 tasks (up to 13 reads) and the next stage was still reached on 8 of 8 (EXP-040 section 9.2, 9.8) [V].

### 2.3 Q3. `submit_patch`, who calls it, and what happens without it

| Case | What happens | Source |
|---|---|---|
| The last stage (check) holds `submit_patch` and calls it | `submit_patch` strips protected files from the diff and sets `submitted_patch` and `patch_submitted`; the harness loop breaks on that flag at the end of the pass | `execution.py:103-112`; `agent_runner.py:920-922` [V] |
| An earlier stage holds it and calls it | The harness breaks on `patch_submitted`, and the stage that follows may never run: the session ends "from inside a sub-call". This is the validator's warning, which fires on check.yaml in the probe (a sub-agent holding it); it is expected here because check is a sub-agent of a Sequential root and the last stage | `validate_submission.py:515-516` [V]; probe output in 2.5 |
| So where must it sit | In the last stage only. The root of a Sequential tree has no tools, so the "root lacks `submit_patch`" check (`validate_submission.py:510-512`) does not apply to a workflow root in the probe [V] | probe output in 2.5 |
| The tree ends a pass with no `submit_patch` | The harness records a `continuation_nudge` and **runs the whole root tree again from locate**, up to 3 nudges in a row without a tool call in the pass; a pass with a tool call resets the count | `agent_runner.py:962-973`, `:1008-1024`; EXP-040 section 9.8 (httpx_3672: the actor ended in text, the tree re-ran) [V] |
| The run ends (caps, errors, 3 nudges) with edits on disk and no `submit_patch` | The harness scores the working-tree diff (`git diff` against `_swegemma_baseline`), protected files stripped. **An applied edit therefore counts without `submit_patch`** | `agent_runner.py:1048-1078` [V] |

Two consequences for a screen. A restart re-runs locate and edit on a tree that already holds the first edit, which can double-apply or conflict (an edit's `old_string` no longer matches). And a restart on `include_contents: none` stages lost the task message (EXP-040, httpx_3672: the proposer's second prompt was 583 tokens against 1,409), so all three stages use default contents; locate and edit then each see the task message on a restart.

### 2.4 Failure modes of this shape (the EXP-039 table, adapted)

| # | Mode | Where | Effect on a screen |
|---|---|---|---|
| T1 | A stage ends only when the model stops (Q2) | every tool-holding stage | the kill criterion; no bound on locate's reads, edit's retries, check's commands |
| T2 | Shared counter and clock (28 calls, 480 s) | locate starving edit | reach is a bound on locate's call use (EXP-040: not seen) |
| T3 | `run_command` can edit | check | check is not read-only; a check that "repairs" through the shell bypasses edit's exact-match rule |
| T4 | Default contents carry every earlier stage's tool results | edit, check | the first prompt of the last stage was 5,170 to 14,005 tokens in EXP-040 (331 under the 14,336 compaction threshold on requests_7205); a locate stage that reads 13 times adds to it |
| T5 | `output_key` carries only text, and a thought-only reply leaves the key empty | locate to edit | `{plan?}` renders empty; EXP-040: the proposer's `ISSUE:` line was missing on 3 of 8 |
| T6 | Restart re-runs the whole tree (Q3) | all | one extra pass is about one locate + edit + check |
| T7 | Edit applies, then check ends in text without `submit_patch` | check to harness | nudge, restart; the working-tree fallback still scores the edit |
| T8 | `edit_file` needs an exact `old_string`; locate cannot give it, only a span | edit | EXP-043's failure (16 altered or extended, 11 non-unique of 39 failed calls) is the editor's, not the locator's; a team does not touch it unless the editor re-reads the span (the prompt says so; prompt-only) |

### 2.5 Q4. The role prompts, written, not packed

Three files, `experiments/EXP-046/probe/prompts/{locate,edit,check}.md`, **802, 807 and 718 bytes** (2,327 characters together, against the v24 prompt's 3,162 bytes; each is about a quarter of it). They contain no repository name, no network or install word and no URL. Each names only tools its agent declares (`validate_submission.py:505-506`). The tree is a validator-only probe, `experiments/EXP-046/probe/` (nine files, never packed, never built into a notebook), the EXP-039 pattern.

`python tools/validate_submission.py experiments/EXP-046/probe --strict` result: structure valid, no prompt lint, **two warnings and one error, all expected**: (a) `check.yaml` holds `submit_patch` as a sub-agent (the Q3 warning), (b) `timeout_seconds=240 < 300` (EXP-033's own value), (c) the packing gate, `120 x (8 + 1.0) min = 18.00 h > 11.0 h`, the same error every 8-minute arm gets; a screen is packed with `--skip-budget-gate`, as EXP-033 and EXP-040 were, and is never uploaded. `max_turns` is 200 (the probe's `eval_config.yaml`): every model event of every agent is a turn, and one pass is about 3 stage-end replies + 6 to 12 tool turns, well under 200, but 80 would end a task in its third pass (EXP-040 section 2.3 c).

### 2.6 Q5. Cost and time, against the E4B's spare time

Measured on the E4B, on smoke-8:

| Quantity | Value | Source |
|---|---|---|
| Single loop, per task | mean 56.9 s (EXP-033), 78.3 s (EXP-038 on the same 8), 85.7 s (EXP-038, dev-48) | EXP-033 section 9, EXP-038 [V] |
| A read-only first stage | 10.0 to 55.0 s per task (EXP-040's proposer, 0 to 13 reads) | EXP-040 section 9.3 E8 [V] |
| A Sequential tree end to end | mean 86.5 s (67.0 to 116.8 s), no task at any cap | EXP-040 section 9.3 E8 [V] |
| A model turn | about 6.0 s | EXP-039 [V] |
| Kernel overhead (vLLM up, setup) | 432 to 504 s (0.12 to 0.14 h) | EXP-033, EXP-040 [V] |
| Spare time per task | about 225 s under the 10.5 h rule | D-006 |

Estimate for three stages [I]: locate 15 to 55 s (as the proposer, with one fewer text-only reply to write), edit about the single loop's edit share (20 to 50 s), check 12 to 30 s (a diff, one command, `submit_patch`), plus about 3 stage-end replies of 3 to 6 s. **Per task 80 to 130 s, point 100 s**, which is **+20 to +45 s over EXP-033's 56.9 s and about the same as EXP-040's 86.5 s plus 14 s**. That is at most a fifth of the 225 s spare. A restart pass adds about 60 to 100 s to a task.

Smoke-8 kernel: 8 x 100 s + 432 to 504 s overhead = 1,232 to 1,304 s, **point 0.35 h, range 0.30 to 0.43 h** (D-006's 0.3 to 0.45). **Conditional worst case** (every task to the 495 s cap): 8 x 495 + 445 = 4,405 s = **1.22 h**, reached only if every pass restarts until the clock. 120 hidden tasks at 100 s plus the E4B's setup is about 3.5 h, inside the 10.5 h rule; the cap-only gate still reads 18 h at an 8-minute cap, as for every 8-minute arm.

## 3. Endpoints (for the specified screen, not run)

All are computed from `traces/trace_*.json` and `task_results.jsonl`, pass 1 unless stated, by `tools/analyze_traces.py` and hand counts.

| # | Endpoint | Definition |
|---|---|---|
| E1 | Editor reached | the `edit` agent emits at least one model step on pass 1 (in a Sequential tree it can fail only if locate uses the 28 calls or the 480 s clock, so this row is a bound on locate's call use) |
| E2 | Applied edit | at least one `edit_file` call whose result has status ok, on the final tree, per task |
| E3 | Stage call counts | per stage, `read_file` calls of locate, calls of edit, calls of check, from agent-author steps; recorded, not read |
| E4 | Wall and caps | per task and mean; tasks at the 28-call, 480 s or 200-turn cap |
| E5 | Restarts | tasks with a `continuation_nudge` event (the `nudges` counter in `analyze_traces.py` misses these, EXP-040 section 9.8, so count the events) |
| E6 | Resolves | recorded, never an endpoint (n = 8) |

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

These apply only if the lead decides to run the screen despite section 2.2. First match, in order.

| # | Condition | Reading |
|---|---|---|
| 0 | not exactly the 8 ids, `err` non-empty on any task, a model other than the E4B, or a stage missing from a trace | infrastructure; fix and re-run, no reading |
| 1 | E1 fewer than 6 of 8 | **kill** (D-006 team-line row): locate takes the room; no fix beyond the one re-run D-006 allows |
| 2 | E2 fewer than 6 of 8 | **kill** (D-006 team-line row, read against EXP-033's 6 of 8; see below) |
| 3 | mean wall above 282 s (EXP-033's 56.9 s plus the 225 s spare), or 3 or more tasks at a cap | no dev-48 arm; the tree cannot ship on 120 tasks |
| 4 | E1 and E2 each 6 or more of 8, row 3 not met | **promote** to one dev-48 E4B arm, paired against EXP-038, same 48 ids |

**The reference for row 2, fixed here.** The single loop's applied-edit share on the same 8 ids is 6 of 8 in EXP-033 (requests_7205 every edit failed, httpx_3672 never edited) and 8 of 8 in EXP-038's subset; both are the same tree. Row 2 is read against **EXP-033's 6 of 8**, because EXP-033 is the paired smoke-8 reference throughout this family (EXP-040, 044, 045), and because against 8 of 8 one missed task kills, which is not a near-deterministic reading at n = 8. The price is a weak kill: row 2 detects a team that is worse than the single loop's *lower* draw. The 8 of 8 is recorded beside it and not read.

**Prediction, blind.** E1 8 of 8 [I]: EXP-040 reached its last stage on 8 of 8 with a prompt-bounded reader that overran on 3. E2 6 or 7 of 8: the editor's `old_string` rule is prompt-only (EXP-043); the new thing the team gives it is a fresh `read_file` in the same stage, which the single loop also had. Mean wall 90 to 120 s.

## 5. What this licenses

- **The desk check kills the premise "each stage bounded by its tools, not by its prompt"** for every stage that holds a tool: only the model ends it (2.2). It does not kill the team as a capability split.
- **It does not buy the smoke-8 screen.** The two kill rows of D-006 are rows 1 and 2. Row 1 is "locate did not eat the 28 calls", which EXP-040 already showed on 8 of 8 for a similar reader; row 2's best case is a promotion to a dev-48 arm whose mechanism is not the one D-006 proposed. The screen can only **kill**; it cannot promote the *bounded-by-tools* claim, because the claim is false by construction. If the lead wants the team as a prompt-bounded capability split anyway, the endpoint a dev-48 arm should carry is **the share of tasks with an applied edit, paired against EXP-038 (the 8 of 48 with no applied edit are the interesting cell), not resolves (5 of 48 gives no power)**, and the arm costs about 1.3 GPU-h (D-006 stage 5).
- **What would reopen it:** a per-agent call cap, an exit tool or a working callback in the harness. None can be added from a submission; the organisers would have to.
- **No claim status moves** (only a critic `accepted` moves one). A note for C-023: the stage-ending finding applies to any tree with tool-holding stages, voting trees included.

## 6. Exact commands

```
python tools/validate_submission.py experiments/EXP-046/probe --strict
wc -c experiments/EXP-046/probe/prompts/locate.md experiments/EXP-046/probe/prompts/edit.md experiments/EXP-046/probe/prompts/check.md experiments/EXP-033/candidate-e4b/prompts/system.md
# if the lead runs the screen anyway (a separate job; none of this was run):
#   cp the probe to experiments/EXP-046/candidate-team/, pack with --skip-budget-gate, build_notebook with --cohort experiments/cohorts/smoke-8.txt, then kernel push after the user's GPU word
```

## 7. Defects and limits of this desk check

1. **The tool-bound claim was read from the source and one prior run, not tested.** No kernel ran this tree; locate's and edit's real call counts are unknown. The EXP-040 reads (0 to 13) are for a reader with `read_file` and `get_status` and a different prompt.
2. **`base_llm_flow.py:872` is ADK 1.36.x as vendored in `data/src`.** If the scorer's ADK differs the line moves; the harness README pins the version (EXP-039 cites it) [I].
3. **I did not read `adk_submission/builders/workflows.py`.** That `SequentialAgent` runs its children in order is from ADK's own contract, EXP-040's trace (proposer, voters, actor in order) and the probe validating [V by EXP-040].
4. **Cost is an estimate** built from EXP-033, EXP-038 and EXP-040 stage times (section 2.6); no E4B edit-stage time on its own was measured.
5. **The probe's prompts are not lint-tested by the packer,** only by the validator; `pack_submission.py` also scans for rejected prompt markers (`_REJECTED_PROMPT_MARKERS`), which was not run because nothing is packed.
6. **Row 2's reference is a choice** (section 4); a lead who prefers 8 of 8 can say so before any push.

## 8. Built

Not built, by section 0. The validator-only probe is `experiments/EXP-046/probe/`. No zip, no notebook, no kernel.

## Status

Desk check complete 2026-11-05. Premise killed as specified (Q2). Nothing pushed, no GPU used. The screen of sections 3 and 4 is specified and not built; it needs the lead's decision and the user's GPU word.
