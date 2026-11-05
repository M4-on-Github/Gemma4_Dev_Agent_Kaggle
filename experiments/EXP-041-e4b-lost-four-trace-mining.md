# EXP-041 — Why does the E4B single loop lose the four tasks the 31B Arm R resolves? Zero-GPU trace mining over EXP-038 and EXP-028

**Date:** 2026-11-05
**Type:** zero-GPU trace mining (L1) over existing run directories. No kernel, no upload, no zip, no notebook, 0.0 L4x4-h.
**Cohort:** none run. Reads the dev-48 ids of `runs/EXP-038-e4b-dev48/` (E4B) and `runs/EXP-028-armR/` (31B Arm R) read-only. Four target ids plus a control of 19 ids.
**Ladder:** L1. Feeds the lead's ranking of prompt or config changes for the E4B; no claim status moves here.
**Pre-registered:** commit of this file, before the four E4B target traces were opened (see "What was seen before writing" below for what was not blind).
**Serves:** C-020 (supported, E4B 5 of 48 against R 9 of 48), the critic's suggested next step in `experiments/EXP-038/critic.md`, C-023 (voting) as a consumer of the answer.
**Relates:** EXP-038 (the E4B run and the informative-27 definition, not touched), EXP-028 (Arm R, not touched), EXP-033 (E4B smoke-8), EXP-040 (V1 voting screen, not touched).
**Tags:** [V] verified in the traces or tool output, [H] read by hand from a trace, [I] inference.

## 1. Why this, now

EXP-038 (critic-accepted, `experiments/EXP-038/critic.md`): E4B resolves 5 of 48, Arm R 9 of 48. On the 27 informative ids (dev-48 minus 15 gated fastapi tasks minus 6 constant tasks) the pair table is both 4, R only 4, E4B only 0, neither 19. The four R-only ids are **fastapi_13537, fastapi_15589, fastapi_9753, rich_3067**. The E4B stops early (median first edit at turn 6 against R's 14, 47 of 48 end by `submit_patch`, no task uses more than 21 of 28 calls, mean wall 85.7 s) but that is an aggregate over all 48. The question here is narrower: for each of the four tasks R wins and the E4B loses, what did the E4B trace do that R's did not? Any prompt or config change aimed at the E4B should target a failure the traces show, not one guessed from the aggregate.

## 2. Design

Four candidate explanations, each with the trace evidence that recognises it. All are decided from the E4B trace and patch, with the Arm R trace beside it.

| Letter | Explanation | Recognised in the E4B trace by |
|---|---|---|
| (a) | submits too early | `submit_patch` called with `n_calls` <= 8 of the 28-call cap, and no test or code run (`run_command` whose command names pytest, unittest, a `tests/` path, or a `python` invocation) after the first edit; call budget mostly unused |
| (b) | edits the wrong file | non-empty patch whose files have no overlap with the gold patch's source files (gold files from `experiments/recall_check/gold.jsonl` `files_touched`; `docs_src/`, `docs/` and `tests/` paths do not count as source) |
| (c) | finds the right file, cannot write the fix | patch files overlap the gold source files, patch non-empty, graded tests still fail |
| (d) | format failure | at least one agent step with no `tool_calls` whose text carries a tool call written as text (a fenced block or `name(...)`), plus a harness `continuation_nudge` event in the trace, and no `edit_file` executed |
| (none) | none of these | the outcome when no letter holds, including an empty patch without a format failure. Reported as its own outcome with a one-line description of what the trace did |

Class assignment rules, fixed now:

- A letter is a flag. A task's class is the set of flags that hold. Where more than one holds (for example a and c together) the set is reported as such and is not collapsed; if a single label is wanted the convention is the precedence d, b, a, c, and the report says it is a convention.
- The threshold for (a) is `n_calls` <= 8. It is chosen before reading; the report prints the `n_calls` of every task so a reader can see how a different threshold would move a task.
- "Test run before submit" means a `run_command` whose command string contains `pytest`, `unittest`, `tests/`, or starts a `python` run, issued before the `submit_patch` call. Counted by grep over the trace's `run_command` arguments, and listed as `tests` (pytest or unittest or `tests/`) and `code` (any other python run) separately.
- "Edited files" come from the patch's `diff --git` header lines (`runs/EXP-038-e4b-dev48/patches/<id>.patch`), cross-checked against the `edit_file` / `write_file` path arguments in the trace. "Files read" are the distinct `read_file` paths.

Fields for each of the four ids, E4B and Arm R side by side: `n_calls`, `n_turns`, `wall_s`, first-edit turn, distinct files read, files edited, gold patch files, a test run before submit (count), `submit_patch` called, patch empty or not, `continuation_nudge` count, and the class. Sources: `summary.jsonl` of each run (written by `tools/analyze_traces.py`), `tools/run_forensics.py forensics` and `compare` for the first-edit turn, `grep` over the trace JSON for tool arguments and the nudge event, and `Read` of the trace for the format check in (d) and for anything the tools do not give. Every number that came from a hand reading is marked [H] in section 9.

**Control.** The same fields, counts only, over the 19 ids that neither arm resolved on the informative 27: the 27 ids of `experiments/EXP-038/cost_estimate.json` key `informative27`, minus the 4 both-resolved (fastapi_14301, fastapi_14463, rich_3006, rich_3905) and minus the 4 R-only. Reported as class counts, with `n_calls`, `submit`, empty-patch and nudge counts. The control tells whether a class is specific to the four lost tasks or is the E4B's general failure mode. If the control takes more than about an hour, only class counts are reported and the report says so.

**Nudges.** The `nudges` counter of `analyze_traces.py` reads 0 on every task (it counts a different marker). The report counts the harness's `continuation_nudge` events directly per task on the four ids (E4B and R) and, if cheap, over the control.

**Cap and scope.** No GPU, no kernel. No change to EXP-038, EXP-028, EXP-034, EXP-035, EXP-040 or to any other agent's README row. Per plan.md:52 nothing from `runs/` goes into git except counts, turn numbers, file paths and short labels.

### What was seen before writing this file

Not blind, disclosed so the readings are weighed accordingly:

- The EXP-038 critic review: `fastapi_13537` is a format failure (3 replies put a tool name in a fenced block after harness continuation nudges; 0 tool calls), and the `nudges` counter misses system `continuation_nudge` events (9 on 7 E4B tasks, 2 in R).
- The E4B `summary.jsonl` row of `fastapi_15589`: 4 calls, 7 turns, 50.7 s, submitted, non-empty patch.
- The aggregate E4B statistics quoted in section 1.
- The gold source files of `fastapi_13537`, `fastapi_15589` (`fastapi/dependencies/utils.py`) and `rich_3067` (`rich/highlighter.py`).

So (d) for fastapi_13537 and (a) for fastapi_15589 are confirmations of what was seen, not blind outcomes. `fastapi_9753`, `rich_3067` and the whole control are blind.

## 3. Endpoints

1. The class (set of flags) per target id, E4B, with the Arm R fields beside it.
2. Class counts over the 19 control ids.
3. `continuation_nudge` events per target id, E4B and R.
4. No rate is estimated and no p-value is computed.

## 4. Readings (blind)

n = 4 targets. This study can classify four traces and cannot estimate a rate. Four tasks is far too few for any frequency claim, and chance is not ruled out: that three of four share a class is what one would also see if the E4B's failures all share that class regardless of why these four were lost. The control is there for exactly this, and a reading is only as strong as its contrast with it.

| # | Observed | Reading |
|---|---|---|
| 1 | One letter holds for at least 3 of the 4 targets, and its share in the control is clearly lower (fewer than half of the control share, by count) | That class is specific to the lost four. Named as the primary target of a prompt or config change [I]; a screen of that change is a separate pre-registration |
| 2 | One letter holds for at least 3 of the 4 targets and holds for most of the control too | A property of the E4B loop in general, not of these four tasks. It is a candidate for a change but does not explain why R wins these four; the 4-0 may still be capability |
| 3 | The targets split across letters, no letter on more than 2 | No single mechanism. A prompt change aimed at one letter can recover at most the tasks of that letter; report each letter's targets by id |
| 4 | (c) holds for 3 or more targets (right file, patch non-empty, still fails) | Prompt-side targeting of localisation or of stopping would not help; the gap is in writing the fix. Points at capacity, best-of-N or voting (EXP-040) rather than a prompt change [I] |
| 5 | (a) holds for 3 or more targets and the control has `n_calls` > 8 with a test run in most tasks | Premature submit is specific to the lost four. A gate before `submit_patch` (test run required, call floor) is the target [I] |
| 6 | (b) holds for 2 or more targets | Localisation is the lever; the aid is read-first or grep-first guidance, not a stop rule [I] |
| 7 | (d) holds for 2 or more targets | A format-recovery target; fastapi_13537 alone does not make it a pattern. One target only is reported as an isolated failure |
| 8 | "none" holds for any target | Reported with the one-line description. No change is proposed from a "none" alone |
| 9 | The `continuation_nudge` count is 0 for all four R and for all four E4B targets | Nudges play no part. Any nonzero count is listed per task |

Rows 1 to 8 are not exclusive; a task can carry two flags and the report says which. Rows decide what the lead may rank, not what is true: with n = 4 a reading is a lead, and the ranking should say so.

## 5. Licenses

What this study can decide: which of the four named mechanisms the four E4B traces show, task by task, and which target a prompt or config change could have for the E4B (inference, tagged [I]). What it cannot decide: how often any mechanism occurs (n = 4 and a 19-id control, no rate), that a change would recover the task (the 4-0 against Arm R may be capability, not a lever; a recovered task needs a screen), or any claim status. A class found here is a candidate for a screen, not a result.

## 6. Commands

```
python -I -X utf8 tools/analyze_traces.py runs/EXP-038-e4b-dev48 --cap-minutes 8 --max-calls 28    # only if a field is missing; summary.jsonl already exists
python -I -X utf8 tools/run_forensics.py forensics runs/EXP-038-e4b-dev48
python -I -X utf8 tools/run_forensics.py forensics runs/EXP-028-armR
python -I -X utf8 tools/run_forensics.py compare runs/EXP-028-armR runs/EXP-038-e4b-dev48
grep -o -H -E '"function_name": "[a-z_]+"' runs/<run>/traces/trace_<id>.json
grep -o -H -E 'continuation_nudge' runs/<run>/traces/trace_<id>.json
grep -o -H -E '^diff --git a/[^ ]+' runs/<run>/patches/<id>.patch
```

The shell of the screener allows no pipes, chaining or ad-hoc scripts, so per-trace counts are `grep -o -H` output counted by eye and by `wc`, and anything else is `Read`. Both are named in section 9.

## 7. Defects

Written before the run; section 9 appends any found.

1. **`nudges` reads 0 and is not used.** `analyze_traces.py` counts a different marker; the direct `continuation_nudge` grep replaces it.
2. **Hand reading.** The (d) test needs the text of agent replies. It is read by hand, marked [H], and a different reader could classify a borderline reply differently.
3. **Gold files.** `files_touched` is the gold patch's file list; a fix in a different file that is functionally equivalent would read as (b). The report says when an edited file is plausibly equivalent.
4. **One run per arm.** Both runs are single draws of a stochastic loop; a different draw could classify a task differently. This is a description of these runs, not of the model.
5. **Seen-before disclosure** in section 2.

## 8. Built

Nothing. No tree, zip, notebook or kernel. 0.0 L4x4-h.

## 9. Results

Pending.

## Status

2026-11-05: pre-registered, committed before the four E4B target traces were opened. Results pending.
