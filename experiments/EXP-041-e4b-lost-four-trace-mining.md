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

Pre-registration committed as 618d3b1 before any of the four E4B traces was opened (apart from the disclosed items). The rules of section 2 and the readings of section 4 are applied as written. Sources: `summary.jsonl` of EXP-038 and EXP-028 (`analyze_traces.py`), `run_forensics.py compare` (re-derives the 4-0), `grep -o` over the trace JSON for tool names, arguments and `continuation_nudge`, patch `diff --git` headers, `gold.jsonl` `files_touched`, and Read of the traces named below. `run_forensics.py forensics` prints only cohort medians (first edit 5.0 resolved, 6.0 patch-but-failed, 6.0 empty-patch), not a per-task turn, so the per-task first-edit turn below is read by hand [H]: turn = `step_id` of the first call minus 2 (system and user steps), minus any `continuation_nudge` steps before it.

### 9.1 The four targets, E4B (E) against Arm R (R)

| Field | fastapi_13537 | fastapi_15589 | fastapi_9753 | rich_3067 |
|---|---|---|---|---|
| gold source files | `fastapi/dependencies/utils.py` | `fastapi/dependencies/utils.py` | `fastapi/dependencies/models.py` | `rich/highlighter.py` |
| calls (`n_calls`) E / R | 0 / 11 | 4 / 14 | 9 / 22 | 7 / 24 |
| turns E / R | 8 / 15 | 7 / 16 | 13 / 25 | 10 / 27 |
| wall s E / R | 19.6 / 211.6 | 50.7 / 371.9 | 85.3 / 203.0 | 64.7 / 164.7 |
| first source edit, turn E / R [H] | none / 10 | 3 / 13 | 4 / 15 | 5 / 12 (scratch file written at 9) |
| distinct files read E / R | 0 / 1 | 1 / 1 | 1 / 2 | 2 / 2 |
| files in patch E | none (empty) | `fastapi/dependencies/utils.py` | `fastapi/dependencies/models.py` | `rich/style.py` |
| files in patch R | `fastapi/dependencies/utils.py` | `fastapi/dependencies/utils.py` | `fastapi/dependencies/models.py` | `rich/highlighter.py` |
| tests or code run before submit E | 0 | 1 test (bare `pytest`) | 1 test (`pytest tests/`) | 0 |
| tests run / code runs R | 0 / 5 | 0 / 6 | 0 / 8 | 0 / 5 |
| `submit_patch` called E / R | no / yes | yes / yes | yes (twice) / yes (twice) | yes / yes |
| patch empty E | yes | no | no | no |
| `continuation_nudge` events E / R | **3** / 0 | 0 / 1 | 0 / 0 | 0 / 0 |
| edit_file calls failed of made, E | 0 of 0 | 0 of 1 | 3 of 5 | 0 of 3 |
| **E4B class (flags)** | **d** | **c** | **c** | **a and b** |

How each flag was decided:

- **fastapi_13537, d.** Zero tool calls in 8 turns. Four agent replies (steps 4, 7, 10, 13) are a fenced `json` block naming a command (for example a `git grep` and `read_file ./fastapi/requests.py 100-200`) written as text, after three harness `continuation_nudge` events [H, read steps 4 and 13]. No `edit_file` executed, patch empty, `submit_patch` never called, "Agent completed execution without calling submit_patch." Confirms what the critic reported; not blind.
- **fastapi_15589, c.** The patch edits the gold file (overlap), non-empty, and the task fails. (a) does **not** hold by the rule as written: `n_calls` is 4, but a test run (`pytest`, no arguments) was issued after the edit. That run collected 1108 items with 304 errors, all `ModuleNotFoundError: inline_snapshot`; the model quoted a prompt instruction to ignore import errors and submitted [H, read steps 5 to 9]. The edit flips the fallback in `getattr(..., "convert_underscores", True)` to `False`; Arm R changed the same file and resolved.
- **fastapi_9753, c.** The patch edits the gold file, non-empty, fails. `n_calls` 9 exceeds the (a) threshold of 8. Three of five `edit_file` calls failed with "old_string not found" before two applied. One test run, `pytest tests/`, collected 709 items with 148 errors (`dirty_equals`, `inline_snapshot` missing); `submit_patch` was then called twice.
- **rich_3067, a and b.** `n_calls` 7, both `run_command` calls are `git grep`, no test or code run: (a) holds. The patch edits `rich/style.py`; the gold file is `rich/highlighter.py`: (b) holds. Convention precedence gives b. Arm R read `rich/highlighter.py`, wrote a scratch reproduction, and ran it five times.

### 9.2 Readings of section 4 applied

- Row 3 fires (split): d on 1 target, c on 2, a on 1, b on 1; no letter on more than 2. No single mechanism explains the four. Rows 1, 2, 4, 5 and 6 do not fire (no letter on 3 or more; (b) on 1, not 2). Row 7: (d) on 1 target only, an isolated failure. Row 8: "none" holds for no target. Row 9: not all zero; the nonzero counts are E4B fastapi_13537 (3) and Arm R fastapi_15589 (1, a resolved task), listed above.
- A single label by the pre-registered precedence (d, b, a, c): fastapi_13537 d, rich_3067 b, fastapi_15589 c, fastapi_9753 c. It is a convention, not a finding.
- At most one task would be recovered by a change aimed at any one letter other than c, and the two c tasks are the ones where the E4B had the right file and wrote a different fix. n = 4 classifies four traces and estimates no rate; chance is not ruled out.

### 9.3 Control: the 19 ids neither arm resolved on the informative 27

The ids: fastapi_14448, 14873, 15280, 15661, 15800, 5624; rich_3061, 3063, 3105, 3180, 3468, 3480, 3521, 3676, 3934, 3935, 3953, 4070, 4075. Same rules, applied from `summary.jsonl`, patch headers, `gold.jsonl` and the first word of each `run_command` command. Only counts, ids, file paths and short labels are recorded here (plan.md:52).

| Class | Count of 19 | Ids |
|---|---|---|
| d (text calls plus nudge, no edit executed) | 0 | none; no control task has 0 calls |
| b (patch files disjoint from gold) | 5 | fastapi_14448, fastapi_5624, rich_3105, rich_3480, rich_3953 |
| c (patch overlaps gold, fails) | 8 | fastapi_15280, fastapi_15800, rich_3061, rich_3180, rich_3468, rich_3521, rich_3934, rich_4070 |
| a (`n_calls` <= 8, submitted, no test or code run) | 9 | fastapi_15280, fastapi_15661, rich_3180, rich_3468, rich_3521, rich_3676, rich_3934, rich_3953, rich_4075 |
| patch empty | 6 | fastapi_14873, fastapi_15661, rich_3063, rich_3676, rich_3935, rich_4075 |
| single label by precedence d, b, a, c; remainder "none" | b 5, a 8, c 3, none 3 (sum 19) | none = fastapi_14873, rich_3063, rich_3935 (empty patch, not a format failure) |

Further control counts. A test or code run before submit: 3 of 19 (fastapi_14448 two `pytest`, rich_3935 one `pytest`, rich_3105 two `python3 tools/...`); 16 of 19 ran neither. `continuation_nudge` events: 3, on fastapi_15280, fastapi_15800 and rich_3934, each with an edit executed (so not class d). `n_calls`: 4 to 21, none above 21; all 19 called `submit_patch`. Raising the (a) threshold from 8 to 10 adds fastapi_14873 (10 calls, empty patch) to (a) and moves no target. The control took well under the hour; nothing was cut.

### 9.4 Observations not in the pre-registered classes (post-hoc, [H], labelled as such)

1. **Executed evidence before submit.** Arm R wrote and ran its own reproduction (heredoc or `python3 -c`, 5 to 8 runs, no `pytest`) on all four tasks before and after the edit. The E4B ran no code on two targets, and on the two (c) targets ran one bare full-suite `pytest` that could not collect (missing `inline_snapshot`, `dirty_equals`) and then submitted. In the control, 16 of 19 E4B tasks have no test or code run. So "submits without informative execution evidence" is the E4B's general behaviour (4 of 4 targets, 16 of 19 control), not something specific to the four. It also fits the pattern in R's wins. R is a different model on a different budget; a repro habit may be capacity, not a lever.
2. **Empty patch from failed edits.** In the control, 5 of the 6 empty patches are tasks where every `edit_file` call failed ("old_string not found", 3 to 6 failures each) and the agent still submitted: fastapi_14873, fastapi_15661, rich_3063, rich_3676, rich_3935. The sixth, rich_4075, edited `pyproject.toml` and the harness patch was 0 bytes. That is 5 of 19 control tasks (26 percent) with no patch because an edit tool failure was not recovered. Among the targets the nearest case is fastapi_9753 (3 of 5 edits failed, then recovered).
3. **Prompt line cited by the model.** In fastapi_15589 the model cites the task prompt's "ignore" instruction for import errors as the reason it submitted after a collection failure [H]. The prompt text was not re-read here.

### 9.5 What a prompt or config change could target [I]

Inference, not a result. Four traces and a 19-id control cannot support a rate or a recovery estimate.

- The four losses have no single cause (row 3), so no single change is licensed to recover "the four". At most: d (one task) is a format-recovery target; (c) (two tasks) is a fix-quality gap in the right file, which a prompt change does not obviously address and which is the place where sampling more candidates (EXP-040 voting) is the nearest lever; (b) (one task) is a localisation miss.
- The most common and most addressable E4B behaviour in these runs is not one of the four letters but obs 1 and 2: no informative check before `submit_patch` (4 of 4 targets, 16 of 19 control), and 5 of 19 control tasks submit an empty patch after failed edits. A change that requires a targeted check (a small `python3 -c` repro or a named test file, not the full suite) and a non-empty `git diff` before `submit_patch` is the target the traces point at. It is a candidate for a smoke-8 screen whose decidable endpoint is enforcement (the share of tasks with an executed check and a non-empty diff at submit), not resolve rate; a dev-48 arm would carry the resolve endpoint on the 27 informative ids.
- Neither observation is specific to the lost four (they occur at least as often in the control), so this study does not show that such a change would win these four; Arm R's behaviour is a pointer, not a proven cause.

### 9.6 Defects found and what was not done

1. `run_forensics.py forensics` gives cohort medians only, so the first-edit turn per task was read by hand from `step_id`.
2. `n_calls` in `summary.jsonl` excludes the free calls (`submit_patch`, `get_status`); `n_calls_incl_free` is larger by 1 to 3. Class (a) uses `n_calls`, as written.
3. Control class (a) uses the first word of each `run_command` command, cut at 70 characters; rich_4075's single command began with an escaped quote and was read by hand (`grep`, failed). The "after the first edit" ordering of the test run was assumed from the first word, not checked, for the control; the effect is only at the (a) boundary (fastapi_14448 and rich_3935 have a `pytest` and are not counted as (a)).
4. The shell of this agent allows no pipes, chaining or ad-hoc scripts, so everything above is `grep -o` output counted by hand plus Read; a transcription slip is possible and every number is reproducible with the commands of section 6.
5. The E4B 2-of-4 and 4-of-4 shares in 9.4 compare four traces with 19, and no resolved E4B task (fastapi_14301, fastapi_14463, rich_3006, rich_3905) was examined, so whether "executed check" separates E4B wins from E4B losses is open. That is the cheapest next L1 step (zero GPU, four traces).
6. Nothing in `submission/`, `tools/` or `tests/` was touched; no kernel, no GPU.

## Status

2026-11-05: pre-registered (618d3b1), mined. Class per target (E4B): fastapi_13537 d, fastapi_15589 c, fastapi_9753 c, rich_3067 a and b. Row 3 fires: no single mechanism. Control of 19: b 5, c 8, a 9, d 0 as flags. No claim status moves. 0.0 L4x4-h.
