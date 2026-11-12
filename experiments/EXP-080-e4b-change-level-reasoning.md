# EXP-080: where the E4B's change goes wrong once it is on the right file (zero-GPU study, the 31B as reference)

**Date:** 2026-11-12
**Type:** zero-GPU analysis (L1 trace mining and hand coding against the gold patches), 0 L4x4-h. No kernel, no build, no upload.
**Cohort:** none (existing runs only: `EXP-028-armR` and the four E4B dev-48 draws `EXP-038-e4b-dev48`, `EXP-077-base`, `EXP-075-t02`, `EXP-078-t02r`)
**Ladder:** L1. It ranks levers for D-011; it decides no tree by itself.
**Pre-registered:** yes. Sections 2 to 4 (sample, item definitions, the Part 1 tally, the separation rule, the D-011 opportunity rule, blind predictions) are committed before any item is coded or any arm R class is computed. Only the format checks in section 2.8 were run before this commit. Results are appended as section 6 and apply the rules as written; defects go in section 5.
**Serves:** D-011 (the open-ended E4B loop). The critic's ranking in `experiments/EXP-078/critic.md` (af8cfc0) funds no E4B harness arm on GPU and lists this study as zero-GPU items 1 and 2.
**Relates:** EXP-074 (divergence classes, `diag.py`; Q3 covered F and R runs at the file level), EXP-075 `noise.py` (`classes`), EXP-077 `pair.py`, EXP-078 `pair4.py`, EXP-028 (arm R, the 31B on the E4B tree's exact files), EXP-035 section 9.3 and EXP-036 (the fastapi collection gap and its re-grade), EXP-063 `refs.py` (`args_of`, `exit_code`, `failed`).

## 1. Questions

- **Part 1, the model swap with the harness fixed.** Arm R of EXP-028 ran the 31B on the same files the E4B draws ran (the v24 tree at 8 min; the EXP-033 E4B tree differs only in its model line). For each dev-48 task: its EXP-074 stage under the 31B and under each of the four E4B draws. At which stage does the E4B leave the 31B's path?
- **Part 2, the change itself.** On the tasks that some run has resolved, when an E4B run reaches a gold file (stage R, C or S) and still fails, what does its reasoning and its tool use show? Coded on fixed items (section 2.4), with arm R's run of the same task coded the same way. Which items separate the two models, and could anything we ship act on a separating item by enough to clear the D-011 endpoint rule?

## 2. Rules, fixed before computing

### 2.1 Runs

- **The 31B reference:** `runs/EXP-028-armR` (model `gemma-4-31b-it-qat-w4a16-ct`; `max_time_minutes` 8, `max_tool_calls` 28). One draw only; it has no spread of its own, and every 31B count below carries that limit.
- **The E4B draws:** `runs/EXP-038-e4b-dev48` and `runs/EXP-077-base` (temperature 1.0, the base pair under D-011), `runs/EXP-075-t02` and `runs/EXP-078-t02r` (temperature 0.2). Same caps. Each is read alone; nothing is pooled into a fake larger draw, and a "per task-draw" count is labelled as such.
- Resolved, empty, wall and call fields come from each run's `summary.jsonl`; patches from `task_results.jsonl` `patch`; gold from `data/raw/tasks.jsonl` field `patch` (never `test_patch`).

### 2.2 Part 1: stages and the tally

- **Classes:** `noise.classes(run, tasks)` (EXP-074 `diag.classify`, margin 5, gold source files), lowercase when resolved, as-run grading. **First check:** arm R must read E6 F3 R6 C14 S10 over its 39 unresolved and 9 resolved, the critic's figure. A mismatch is a defect logged before anything else is read.
- **Stage order (rank, low to high):** E 0, F 1, R 2, C 3, S 4, resolved 5. A resolved run ranks 5 whatever its letter.
- **Tally per task-draw (48 tasks x 4 draws = 192):** **short** when the E4B rank is below arm R's; **same** when equal; **further** when above. For a short task-draw, the E4B **leaves at** its own class (the stage it stopped at), and the cell is also indexed by arm R's stage (where the 31B got to). The answer to Part 1 is the 6 x 6 matrix (arm R stage rows, E4B stage columns) summed over the four draws, reported with each draw's own matrix, and the share of short task-draws by "leaves at" letter.
- **Tally per task:** a task is **short** when the E4B is short in at least 3 of the 4 draws; its leave stage is the most frequent "leaves at" letter over its short draws (ties listed both).
- **The table:** one row per dev-48 task: arm R class as run, arm R re-graded resolve flag and gated flag from `experiments/EXP-036/summary.jsonl`, and the four E4B classes. Printed by `experiments/EXP-080/part1.py`; `pair.py` is not called because its tail lines treat `RUNS[0]` and `RUNS[1]` as the base pair and label the union "three runs".
- **The grading gap.** Arm R's grading lacked the two test-only packages on 15 fastapi tasks (the EXP-036 `gated` flag). Re-graded with stand-ins it resolves 12 of 48, not 9 (zero flips the other way). The primary tally uses as-run grading; a sensitivity tally re-ranks arm R as resolved where `R_resolved_regraded` is true. Of the E4B draws only EXP-038 has a re-grade (5 of 48, unchanged); gated cells of the other three draws are flagged un-regraded and counted apart in the sensitivity line.

### 2.3 Part 2: the sample

- **Tasks ever resolved:** `diag.ever_resolved()` (EXP-074 section 2.5: any run's `task_results.jsonl` under `runs/`, EXP-000 excluded). 16 tasks by the format check, all in dev-48.
- **The E4B sample:** every run of the four draws on those 16 tasks whose class is upper-case R, C or S (reached a gold file, unresolved). By the format check: 26 runs on 11 tasks (R 9, C 9, S 8). Resolved runs (lower case) are outside the judged sample; they enter the scripted items over all 48 tasks (section 2.6).
- **The 31B side:** arm R's run on each of those 11 tasks, whatever its class or outcome (11 runs). Every 31B count is reported split by arm R's own stage and its re-graded resolve flag, because the E4B runs were selected as failures and arm R's were not.
- **The unit of comparison is the task (11).** Two tasks hold 8 of the 26 E4B runs; per-run counts are given beside the per-task figures and never used alone to call a separation.

### 2.4 Items

Judged items are coded by hand by the agent, reading the window of section 2.5 against the issue text and the gold source diff. Scripted items come from tool calls and `summary.jsonl` by `experiments/EXP-080/items.py`. Codes are fixed labels only (no free text, no cause or failure wording; plan.md:52).

| Item | Kind | Codes | Definition |
|---|---|---|---|
| a | judged | y, n, w | The window states the root cause that the gold change addresses (the same faulty behaviour at the same point in the code, in any words). w: no cause can be read in the window. |
| b | judged | y, n, w | The window states a cause other than the gold's, and the run's last window step still acts on it (does not abandon it). a = y implies b = n. |
| c | judged | all, part, none, w | Of the gold regions (EXP-074 regions at margin 5 over gold source files), the window names every one, some, or none, by function, class or name of the changed construct. With one gold region, all or none. |
| c' | scripted | count of k | Gold regions whose enclosing `def` or `class` name (the nearest such line at or above the region's first line in the snapshot) appears in any thinking text before submit, of k regions. A proxy for c, reported beside it. |
| d | scripted | y, n, na | Every successful `edit_file` call's `old_string` was shown to the run before the call: each of its non-blank lines, stripped, occurs in the JSON-unescaped content of an earlier observation of the same run. na: no successful `edit_file`. Also the per-edit share. |
| e1 | scripted | y, n | After the first successful change call (`edit_file` not failed by `refs.failed`, or `write_file`), the run executed a `run_command` whose program is `python`, `python3` or `pytest` (any form). |
| e2 | scripted | y, n, na | One of those checks exited non-zero (`refs.exit_code`). na when e1 = n. |
| e3 | scripted | fix, ign, na | After the last non-zero check: a further successful change call (fix) or none before the end (ign). na when e2 is not y. |
| e4 | scripted | pass, fail, na | The last check's exit is 0 (pass) or not (fail). na when e1 = n. |
| f | judged | y, n, w | The run's change follows the issue's literal wording (adds or alters what the issue text names) where the gold change alters the code's behaviour at another point or in another way. n when the change and the gold act on the same behaviour, or the issue wording and the gold point coincide. |
| g | scripted | y, n | Submitted with room: `submit_patch_called` true and none of `calls_cap_hit`, `time_cap_hit`, `timeout_hit`. Reported with time left = 480 - `wall_s` and calls left = 28 - `n_calls` (floor 0). The harness let some arm R runs past 28 counted calls (one has `n_calls` 32), so calls left is a relative figure, and g leans on the cap flags. |

- An item added because the first read shows a recurring pattern is labelled **added after reading**, defined before it is coded on any further run, and never enters the separation call as a pre-registered item.
- Arm R runs with no change call: c, d, f are na; a and b are coded from the window.

### 2.5 Reading window and blinding

- **Window, by steps.** W1 = the thinking messages of the agent step that issues the first successful change call and of the agent step before it; when no change call succeeds, the last two thinking steps of the run. W2 = the thinking message of the step that issues `submit_patch`, or of the last thinking step when there is none (dropped when it is already in W1). Each step is cut to its last 2500 characters. The share of the run's thought characters that the window holds is recorded per run.
- **References shown with each window:** the issue text (`problem_statement`, first 2000 characters), the gold source diff's changed lines, and the run's own submitted patch's changed lines (first 60 lines). Read with `python -I -X utf8` into the scratchpad only.
- **Blinding (partial).** Windows are written to scratchpad files under shuffled opaque keys (`random.Random(80)`), with no run id, model name or class in the file. The key map stays in the scratchpad until every run is coded. The 31B's step style can still be recognised, so the blinding is partial. Codes are appended to a scratchpad file run by run, then joined to run ids by script into `experiments/EXP-080/codes.jsonl` (ids and labels only).

### 2.6 Scripted items over all 48 tasks

- d, e1 to e4 and g are also computed for every task-run of each of the five runs over all 48 tasks, so each has a per-draw value with a proper denominator, and over the sample.

### 2.7 Separation, levers, and the D-011 opportunity rule

- **Per task:** e(t) = the share of coded E4B sample runs on task t with the item at its "yes" label (y; all for c; fix for e3; pass for e4); w and na runs are dropped from the denominator. r(t) = arm R's value on t (1, 0, or dropped when w or na).
- **An item separates the models** when both hold, over the tasks where e(t) and r(t) both exist: (i) the mean of r(t) minus the mean of e(t) is at least 0.30 in absolute value; (ii) at least 4 tasks are untied (r(t) differs from e(t)) and at least 75% of them go the direction of (i). One condition alone: **leans**, reported but not called. Neither: does not separate. The like-for-like line (tasks where arm R is itself unresolved R, C or S) is reported and not required.
- **Scripted items over 48 (model level):** arm R's rate separates from the E4B when it lies outside the range of the four draws by more than two binomial SDs of one draw against one at the four-draw pooled rate, 2 x sqrt(2 x p(1 - p) / 48).
- **Levers.** For each separating item: whether anything in the submission's tree (sub-agents, the loop), prompt structure, sampling (`configs/sampling.yaml`) or `eval_config.yaml` could act on it; "none" when that is the answer.
- **The D-011 rule (endpoint: resolves per dev-48 draw).** Keep is set beyond the larger of the base-draw gap and two reference SDs, the SDs binomial at the pooled base rate with the draws independent (EXP-079 section 4). Base pair: EXP-038 (5) and EXP-077 (3) by `summary.jsonl`. Thresholds are computed by `items.py`: two pooled draws against two, more than max(gap, 2 x sqrt(48 p (1 - p))); one draw against one, more than max(gap, 2 x sqrt(2 x 48 p (1 - p))).
- **Opportunity count per draw for a separating item:** the E4B runs of that draw with the item in its failing state on a task arm R resolves under the re-grade (the conditioned ceiling: a lever flipping the item, with flipping sufficient). Beside it the loose ceiling, failing-state runs regardless of arm R. Judged items count over the sample (about 6.5 runs per draw); scripted items count over all 48 tasks. The mean over the base pair is set against the two-against-two threshold. An item whose conditioned ceiling does not exceed it **cannot clear the rule at full conversion**, and no lever on it is proposed for GPU.

### 2.8 Format checks run before this commit

- `diag.ever_resolved()` gives 16 tasks, all in dev-48; the E4B union over the four draws is 7.
- The four E4B draws' class letters on those 16 tasks (already committed through EXP-078 `pair4.py`), from which the sample counts in section 2.3 were taken. Arm R's classes were not computed.
- Thought-text length on seven traces (four EXP-038, three arm R): 11k to 34k characters per run, with arm R's first edit later (step 11 to 23 against 4 to 5). This is why section 2.5 reads a step window and not whole runs.
- Trace schema (step keys, tool names and argument keys) and the `summary.jsonl` call counter (`n_calls` excludes free calls; an arm R run has 32 against the cap of 28).
- `experiments/EXP-036/summary.jsonl` fields (`gated`, `R_resolved_as_run`, `R_resolved_regraded`).

## 3. Blind predictions

Probabilities are the agent's, written before any coding.

- **P1.** Arm R reproduces E6 F3 R6 C14 S10 with 9 resolved. 95%.
- **P2.** Of the short task-draws (section 2.2), E and F together are at least 50% of "leaves at" letters, and F is the single most frequent. 60%.
- **P3.** Of the task-draws where arm R reaches C, S or resolves, the E4B also reaches C, S or resolves in at most half. 60%.
- **Part 2, per item (E4B sample rate against arm R):**
  - a: E4B at most 0.40, arm R at least 0.60; a separates. 55%.
  - b: E4B at least 0.40, arm R at most 0.20; b separates. 45%.
  - c: E4B "all" less often than arm R by 0.30 or more; c separates. 40%.
  - d: both at least 0.70; d does not separate. 55%.
  - e1: E4B below arm R by 0.30 or more; e1 separates on the sample and over 48. 65%.
  - f: E4B at least 0.25, arm R at most 0.10; f separates. 35%.
  - g: the E4B submits with room more often, its median time left at least 300 s and arm R's at most 200 s; g separates in that direction. 80%.
- **Levers.** No separating item has a conditioned ceiling above the two-against-two threshold on the base pair. 60%.

## 4. What this licenses

- Nothing on GPU by itself. A separating item whose conditioned ceiling clears the threshold goes to the lead as a candidate for the ladder (desk check first). One that cannot clear it is recorded as such.
- A null (no item separates) says that on these tasks the two models' failures look alike on these items, within one 31B draw and a step window; it does not say the models reason alike.

## 5. Defects

(none yet)

## Status

PRE-REGISTERED 2026-11-12. Next: `part1.py`, `items.py`, the coding pass, results in section 6.
