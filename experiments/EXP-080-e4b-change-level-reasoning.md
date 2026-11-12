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

Logged after the pre-registration commit (4a5968a). The rules in sections 2 to 4 are not revised. Each item below says how section 6 handles it.

1. **The opportunity rule did not say whether E4B runs that already resolved count.** Section 2.7 counts "the E4B runs of that draw with the item in its failing state on a task arm R resolves under the re-grade". For a judged item this cannot matter, because the sample holds only unresolved runs. For a scripted item over 48 it does matter: a resolved E4B run can sit in the failing state, and flipping the item there adds no resolve. Section 6 reports the rule as written (conditioned) and beside it the conditioned ceiling with resolved E4B runs left out (conditioned-unresolved). The call as written uses the first figure.
2. **Model-level 2 SD.** It is applied as written: 2 x sqrt(2 p (1 - p) / 48) at the four-draw pooled rate. Items d, e2, e3 and e4 have denominators below 48, so a sensitivity is printed with the item's own mean denominator. It changes no call.
3. **"Failing state"** is read as the E4B side of the separating direction: the label the E4B mostly shows where arm R mostly shows the other one. For d this is E4B = y. The E4B reads the lines it edits verbatim more often than arm R does, so a lever that flips d is not a sensible direction. d is reported with its counts and gets no lever.
4. **`refs.exit_code` returns "?"** on 2 checks in EXP-078. For e2 and e4 these count as non-zero, as `items.py` codes them, because "?" is not exit 0.
5. **Not pre-registered: the check-form and exit table.** The table of check form (pytest, `python -c`, other python) by exit code, and the reading of the shared prompt's check line (section 6.4), were not pre-registered. They were added after the scripted items had printed. They are labelled post hoc and enter no call.
6. **Blinding broke in practice.** The arm R windows were recognisable from step style and from the patch reference, and so were the E4B windows. For most tasks the step index of the first change gives the model away. The judged codes are therefore not blind to the model, only to the draw and the class.
7. **Thin arm R windows.** The 31B's first edit comes late and its runs are long, so arm R's windows hold a smaller share of the run's thought text: median 0.180 against the E4B's 0.291. One arm R run (fastapi_14873, no change call) holds 0.005 and was coded w on a and b.
8. **Item c is coarse** when all the gold regions share one enclosing function. Naming that function then counts as "all".
9. **Item f is hard to apply to a feature-request issue.** On such an issue the issue wording and the gold point largely coincide. rich_3676 was coded n on f in every run.
10. **Output file renamed.** Section 2.5 names `experiments/EXP-080/codes.jsonl`, but `.jsonl` outside `summary.jsonl` is gitignored and fails `check_repo_hygiene.py`. The same rows, ids and labels only, are written to `experiments/EXP-080/codes.csv`.
11. **Item x1 was added after reading** (section 2.4 rule). It was defined after the five runs of fastapi_14297, the fifth task in reading order, and before any further run was coded. The four earlier tasks' runs were then back-coded for x1. Definition: the change is the gold's idea at a gold site, but it carries a code-level defect that makes it not do what the window says it does (a wrong attribute, call or value type, a name used but not imported, a check that can never be true). Codes are y or n. It is na when a is not y or when the run touched no gold region. It enters no separation call.
12. **Class E split, added after the first results commit (8f7875d).** Class E is an empty patch, not a wrong file. The headline "leaves at the file" in 8f7875d therefore overread E. `experiments/EXP-080/e_split.py` now splits each E4B run that leaves at E by what it attempted: an `edit_file` or `write_file` call on a gold source file (any outcome), calls on other files only, or no change call. Section 6.1 is reworded to match. This is a description and enters no pre-registered call.
13. **Recoded after the first results commit: arm R's rich_3180 on item c.** The run issued no change call (6 `read_file`, 6 `run_command`), so section 2.4 makes c na. It had been coded "part". It is now na. Re-joined, c reads arm R 8/9, 9 tasks, +0.519, and still separates. The opportunity counts do not change.
14. **The grading gap reaches the Part 2 sample.** Seven of the 26 sample runs are un-regraded gated cells: EXP-077, EXP-075 and EXP-078 on fastapi_13207, 14297 and 14360, the gated tasks of the sample. Any of them may resolve under a re-grade, and then it would leave the sample. `items.py join` now also prints every item and opportunity figure with those 7 runs dropped. Section 6.2 and 6.5 report this as a sensitivity. The calls as written use all 26.

## 6. Results (2026-11-12)

Commands, all zero GPU:

```bash
python -I -X utf8 experiments/EXP-080/part1.py
python -I -X utf8 experiments/EXP-080/items.py scripted
python -I -X utf8 experiments/EXP-080/items.py dump <scratchpad dir>      # windows, scratchpad only
python -I -X utf8 experiments/EXP-080/items.py join <scratchpad codes> <scratchpad keymap>   # -> experiments/EXP-080/codes.csv
python -I -X utf8 experiments/EXP-080/e_split.py                               # defect 12, the E-leave split
```

### 6.1 Part 1: classes and the first check

`part1.py` finds 48 shared ids. Arm R as run reads E6 F3 R6 C14 S10 with 9 resolved, which matches the critic's figure, so the first check passes and **P1 holds**. `experiments/EXP-036/summary.jsonl` agrees with arm R's summary on all 48 ids: 9 resolved as run, 12 re-graded, 15 gated.

| Run | E | F | R | C | S | resolved | short | same | further | leaves at E F R C S |
|---|---|---|---|---|---|---|---|---|---|---|
| EXP-028-armR (31B) | 6 | 3 | 6 | 14 | 10 | 9 | | | | |
| EXP-038-e4b-dev48 | 10 | 12 | 6 | 9 | 6 | 5 | 19 | 24 | 5 | 8 8 2 1 0 |
| EXP-077-base | 9 | 8 | 8 | 13 | 7 | 3 | 20 | 24 | 4 | 6 6 5 2 1 |
| EXP-075-t02 | 5 | 12 | 7 | 10 | 8 | 6 | 14 | 30 | 4 | 3 8 3 0 0 |
| EXP-078-t02r | 3 | 9 | 12 | 10 | 9 | 5 | 12 | 30 | 6 | 2 4 5 1 0 |
| four draws, per task-draw (192) | | | | | | | 65 | 108 | 19 | 19 26 15 4 1 |

The table below sums the four draws, with arm R's stage as rows and the E4B's as columns (as run; v = resolved):

| arm R \ E4B | E | F | R | C | S | v | row |
|---|---|---|---|---|---|---|---|
| E | 8 | 7 | 4 | 4 | 0 | 1 | 24 |
| F | 4 | 8 | 0 | 0 | 0 | 0 | 12 |
| R | 0 | 8 | 14 | 2 | 0 | 0 | 24 |
| C | 6 | 9 | 8 | 32 | 1 | 0 | 56 |
| S | 4 | 6 | 0 | 2 | 28 | 0 | 40 |
| v | 5 | 3 | 7 | 2 | 1 | 18 | 36 |

- **Where the E4B leaves the 31B's path: before a change lands on a gold file.** Of the 65 short task-draws, the E4B stops at E (empty patch) in 19 and at F (wrong file) in 26, an E+F share of 0.692. It stops at R in 15, at C in 4 and at S in 1. **P2 holds**: E+F is at least 0.50 and F is the single most frequent letter.
- **The 19 E leaves, split by `e_split.py` (defect 12, a description only):**

  | E leaves split | count |
  |---|---|
  | edited a gold source file, every edit failed | 8 |
  | change calls on other files only | 9 |
  | no change call | 2 |

  On the F leaves (26) and on the E leaves with other files only (9), the E4B never brings a change to a gold file. On 8 it is at the gold file but no edit lands there. The per-draw split, in that order, is EXP-038 3/4/1, EXP-077 2/3/1, EXP-075 2/1/0 and EXP-078 1/1/0.
- **Once on the 31B's regions it mostly stays there.** Arm R is at C, S or resolved on 132 task-draws. On 84 of them (0.636) the E4B also reaches C, S or resolved. **P3 fails**: it predicted at most half.
- **Per task:** 12 tasks are short in at least 3 of the 4 draws. Their most frequent leave stage is F on 7, R on 3, C on 1 and E on 1. By arm R stage these tasks are R 2, C 4, S 2 and resolved 4.
- **The EXP-028 fastapi grading gap.** Re-ranking arm R as resolved on its 3 re-graded flips gives short 72, same 101, further 19, leaves at E19 F26 R15 C4 S8, E+F 0.625, and 84 of 132 (0.636). 14 tasks are then short in at least 3 draws, with leave stages F 7, R 3, S 2, C 1, E 1. The gap moves cells from arm R's S row to its v row: re-graded, the E4B leaves at S 8 times where it did once. The E-and-F answer stands. The three later E4B draws have 45 gated cells that were never re-graded, all of them unresolved. Dropping them leaves 147 task-draws: short 52, E+F 0.692, and 59 of 99 (0.596) at C, S or resolved. 8 tasks are then short in at least 3 draws.

Per task, as run (ever = in the 16 ever-resolved; g = EXP-036 gated; Rv = arm R re-graded resolved; lowercase = resolved):

| task | ever | g | arm R | Rv | 038 | 077 | 075 | 078 |
|---|---|---|---|---|---|---|---|---|
| fastapi_11355 | - | g | C | - | F | C | F | F |
| fastapi_13207 | y | g | S | v | F | C | F | E |
| fastapi_13537 | y | - | s | v | E | R | R | R |
| fastapi_13786 | - | g | C | - | E | C | C | C |
| fastapi_14262 | - | g | C | - | C | C | C | C |
| fastapi_14297 | y | g | S | v | S | S | S | S |
| fastapi_14301 | y | - | s | v | s | s | s | s |
| fastapi_14360 | y | g | S | v | E | S | S | S |
| fastapi_14448 | - | - | C | - | F | F | R | F |
| fastapi_14459 | - | g | C | - | E | R | C | R |
| fastapi_14463 | y | - | s | v | s | s | s | s |
| fastapi_14512 | - | g | F | - | F | E | E | F |
| fastapi_14583 | - | g | F | - | F | F | F | F |
| fastapi_14605 | - | g | C | - | R | C | C | R |
| fastapi_14609 | - | g | C | - | C | C | E | C |
| fastapi_14873 | y | - | E | - | E | E | c | R |
| fastapi_14953 | - | g | C | - | C | C | C | C |
| fastapi_14962 | - | g | R | - | F | F | F | R |
| fastapi_14964 | - | g | S | - | S | C | S | S |
| fastapi_15030 | - | g | R | - | R | R | R | R |
| fastapi_15280 | - | - | E | - | R | R | E | R |
| fastapi_15589 | y | - | s | v | R | E | R | R |
| fastapi_15661 | - | - | S | - | E | F | F | F |
| fastapi_15800 | - | - | R | - | C | C | R | R |
| fastapi_5624 | y | - | R | - | F | F | F | F |
| fastapi_9753 | y | - | s | v | C | E | F | C |
| httpx_3672 | - | - | C | - | C | C | C | C |
| requests_6644 | y | - | f | v | f | f | f | f |
| requests_7205 | - | - | S | - | S | S | S | S |
| requests_7309 | - | - | S | - | S | S | S | S |
| requests_7315 | - | - | S | - | F | S | S | S |
| requests_7427 | - | - | S | - | S | S | S | S |
| rich_3006 | y | - | s | v | s | R | F | s |
| rich_3061 | - | - | C | - | C | R | C | R |
| rich_3063 | - | - | C | - | E | C | E | S |
| rich_3067 | y | - | s | v | F | E | s | E |
| rich_3105 | - | - | E | - | F | F | F | F |
| rich_3180 | y | - | E | - | C | C | C | C |
| rich_3468 | - | - | R | - | R | F | R | R |
| rich_3480 | - | - | E | - | F | E | F | F |
| rich_3521 | - | - | S | - | S | E | S | S |
| rich_3676 | y | - | C | - | E | R | C | C |
| rich_3905 | y | - | s | v | s | S | s | s |
| rich_3934 | - | - | R | - | R | R | R | R |
| rich_3935 | - | - | F | - | E | E | F | F |
| rich_3953 | - | - | C | - | F | F | F | C |
| rich_4070 | - | - | C | - | C | C | C | C |
| rich_4075 | - | - | E | - | E | E | E | E |

### 6.2 Part 2: sample and coding

The sample is 26 E4B runs on 11 tasks, as in section 2.3: EXP-038 4, EXP-077 8, EXP-075 6, EXP-078 8; R 9, C 9, S 8. Arm R's 11 runs on those tasks are 8 resolved under the re-grade (Sv or sv) and 3 unresolved under it (fastapi_14873 E, rich_3180 E, rich_3676 C). All 37 runs were coded. The per-run labels are in `experiments/EXP-080/codes.csv`. The window held a median 0.291 of an E4B run's thought text and 0.180 of an arm R run's (defect 7).

**Judged items** (section 2.7 per-task rule; "tasks" = tasks where both sides exist):

| item | E4B runs yes/n | arm R runs yes/n | tasks | mean r - mean e | untied | with sign | call |
|---|---|---|---|---|---|---|---|
| a root cause | 8/24 | 10/10 | 9 | +0.676 | 7 | 7 | **separates** |
| b other cause, kept | 16/24 | 0/10 | 9 | -0.676 | 7 | 7 | **separates** |
| c all regions named | 10/26 | 8/9 | 9 | +0.519 | 5 | 5 | **separates** (after the defect 13 recode; it was 8/10, 10 tasks, +0.467 in 8f7875d) |
| f literal wording | 11/26 | 0/9 | 9 | -0.370 | 4 | 4 | **separates** |
| x1 (added after reading) | 7/8 | 1/9 | 3 | -1.000 | 3 | 3 | leans (fewer than 4 tasks); not a pre-registered item |

**Scripted items on the sample:**

| item | E4B runs yes/n | arm R runs yes/n | tasks | mean r - mean e | untied | with sign | call |
|---|---|---|---|---|---|---|---|
| d read before edit | 25/26 | 9/9 | 9 | +0.000 | 0 | 0 | does not separate |
| e1 check after change | 20/26 | 5/11 | 11 | -0.265 | 5 | 4 | leans |
| e2 a check failed | 19/20 | 2/5 | 5 | -0.500 | 4 | 3 | **separates** |
| e3 fixed after failure | 0/19 | 0/2 | 2 | +0.000 | 0 | 0 | does not separate |
| e4 last check passed | 1/20 | 5/5 | 5 | +0.900 | 5 | 5 | **separates** |
| g submitted with room | 26/26 | 8/11 | 11 | -0.273 | 3 | 3 | does not separate |

- **Arm R by its own stage.** a is y on all 8 re-graded-resolved runs, on the C- run and on one E- run; the other E- run is coded w. c is "all" on all 8 resolved runs, "part" on the C- run, and na on both E- runs, which made no successful change. Each like-for-like line (tasks where arm R is itself unresolved R, C or S) has at most 1 task, so it can say nothing.
- **Sensitivity: the grading gap (defect 14).** Seven sample runs are un-regraded gated cells. With them dropped:

  | item | E4B | arm R | tasks | difference | call |
  |---|---|---|---|---|---|
  | a | 3/17 | 10/10 | 7 | +0.679 | separates |
  | b | 14/17 | 0/10 | 7 | -0.679 | separates |
  | c | 4/19 | 8/9 | 7 | +0.524 | separates |
  | f | 7/19 | 0/9 | 7 | -0.429 | leans (3 untied tasks) |
  | e2 | 15/16 | | | | separates |
  | e4 | 1/16 | | | | separates |
  | g | 19/19 | | | | leans |
  | x1 | 2/3 | | | | leans |

  Five of the seven x1 = y runs are on these gated tasks, so x1 rests mostly on runs whose grade is not settled.
- **x1.** It is y on 7 of the 8 E4B runs where a = y and the change touched a gold region. Those are the 4 runs on fastapi_14297, 2 on fastapi_14360 and 1 on rich_3905. It is y on 1 of 9 arm R runs (rich_3676, unresolved). In other words, where the E4B has the gold's idea at the gold site, its change is almost always broken at the code level.
- **Pattern seen in the reading.** This is a hand observation, not an item, and enters no call. On fastapi_9753, 2 E4B windows are filled by failed `edit_file` retries; both are coded w on a and b.

### 6.3 Scripted items over all 48 tasks (model level, section 2.7)

| run | d | e1 | e2 | e3 (fix) | e4 (pass) | g | median time left s | median calls left |
|---|---|---|---|---|---|---|---|---|
| EXP-028-armR | 35/40 | 21/48 | 12/21 | 3/12 | 18/21 | 25/48 | 179.7 | 4 |
| EXP-038-e4b-dev48 | 38/39 | 16/48 | 16/16 | 1/16 | 1/16 | 47/48 | 398.7 | 21 |
| EXP-077-base | 39/40 | 21/48 | 21/21 | 1/21 | 0/21 | 48/48 | 410.0 | 21 |
| EXP-075-t02 | 43/43 | 32/48 | 30/32 | 2/30 | 3/32 | 48/48 | 408.6 | 19 |
| EXP-078-t02r | 44/45 | 27/48 | 26/27 | 0/26 | 1/27 | 46/48 | 404.4 | 21 |

| item | draw range | arm R | outside by | 2 SD | call |
|---|---|---|---|---|---|
| d | 0.974-1.000 | 0.875 | 0.099 | 0.054 | **separates** (arm R lower) |
| e1 | 0.333-0.667 | 0.438 | 0.000 | 0.204 | does not separate |
| e2 | 0.938-1.000 | 0.571 | 0.366 | 0.071 | **separates** (arm R lower) |
| e3 | 0.000-0.067 | 0.250 | 0.183 | 0.083 | **separates** (arm R higher) |
| e4 | 0.000-0.094 | 0.857 | 0.763 | 0.091 | **separates** (arm R higher) |
| g | 0.958-1.000 | 0.521 | 0.438 | 0.051 | **separates** (arm R lower) |

The own-denominator 2 SD (defect 2) gives the same calls.

### 6.4 Post hoc: what the checks are (defect 5, not pre-registered, enters no call)

Check form and exit code of the e1 checks, over all 48 tasks:

| run | pytest exit 0 / non-zero | `python -c` exit 0 / non-zero | other python exit 0 / non-zero |
|---|---|---|---|
| EXP-028-armR | 0 / 0 | 24 / 8 | 10 / 8 |
| EXP-038-e4b-dev48 | 0 / 17 | 0 / 0 | 1 / 1 |
| EXP-077-base | 0 / 24 | 0 / 0 | 0 / 0 |
| EXP-075-t02 | 2 / 35 | 0 / 0 | 2 / 0 |
| EXP-078-t02r | 1 / 30 | 0 / 0 | 0 / 0 |

- **What the E4B checks with.** It checks with pytest. Over the four draws pooled, 106 of its 109 pytest checks exit non-zero, and 6 of its 113 checks of any form exit 0.
- **The E4B's exit codes, per draw (all forms):**

  | draw | exit 0 | exit 1 | exit 2 | exit 4 | ? |
  |---|---|---|---|---|---|
  | EXP-038 | 1 | 4 | 11 | 3 | |
  | EXP-077 | | 7 | 11 | 6 | |
  | EXP-075 | 4 | 16 | 13 | 6 | |
  | EXP-078 | 1 | 16 | 12 | | 2 |

  Exit 2 and 4 are pytest usage or collection errors. Exit 1 is test failures (or an error in a python script), and it is the largest single code in EXP-078 and EXP-075.
- **What arm R checks with.** It never runs pytest after its first change. Its checks are `python -c` or a small python script, and 34 of 50 exit 0.
- **Both trees carry the same check line.** The E4B tree and arm R share one prompt (`experiments/EXP-033/candidate-e4b/prompts/system.md` line 25), which offers both a pytest node and a `python -c` check after the edit. The E4B takes the first option, and that check almost always exits non-zero. The 31B takes the second.
- **This is a reading, not a measured cause.** The table does not show that the failing pytest checks are why the E4B submits broken changes.

### 6.5 Separating items, levers, and the D-011 opportunity count

The D-011 thresholds come from `items.py`. The base pair resolves 5 and 3, pooled p 0.0833, gap 2. Two draws against two need **more than 3.83** per draw; one against one needs more than 5.42.

Opportunity per draw is given as loose / conditioned (rule as written). For the scripted items, a third figure leaves out the resolved E4B runs (conditioned-unresolved, defect 1). Draws are listed in the order 038, 077, 075, 078.

| item | direction | per draw | base-pair mean conditioned | as written | resolved E4B runs left out | lever in the tree, prompt, sampling or eval_config |
|---|---|---|---|---|---|---|
| a | E4B states the root cause less | 2/1, 5/3, 5/3, 4/2 | 2.0 | cannot clear | n/a | none. The model is fixed. Comprehension of the cause is not a setting in any shipped file. |
| b | E4B keeps another cause | 2/1, 5/3, 5/3, 4/2 | 2.0 | cannot clear | n/a | none (as a) |
| c | E4B names all regions less | 3/2, 5/3, 3/1, 5/3 | 2.5 | cannot clear | n/a | none (as a) |
| f | E4B follows literal wording | 2/2, 2/2, 3/3, 4/4 | 2.0 | cannot clear | n/a | none. A prompt line against literal readings would also act on the tasks where the wording and the gold coincide. |
| e2 (sample) | E4B checks fail | 3/3, 4/3, 6/4, 6/3 | 3.0 | cannot clear | n/a | prompt structure: the check line (6.4) |
| e4 (sample) | E4B last check fails | 3/3, 4/3, 6/4, 6/3 | 3.0 | cannot clear | n/a | prompt structure: the check line (6.4) |
| d (48) | E4B reads verbatim more | 38/10/5, 39/9/6, 43/12/7, 44/10/5 | 9.5 | exceeds | 5.5, exceeds | none. The direction is not a lever (defect 3). |
| e2 (48) | E4B checks fail | 16/7/4, 21/6/3, 30/11/7, 26/7/3 | 6.5 | exceeds | 3.5, cannot clear | prompt structure: offer only the `python -c` form in the check line. Two near variants have already been screened on smoke-8: EXP-045 (a repro bullet; row 5 fired, no decision) and EXP-055 (the last call must be a one-command check; row 3 fired, no decision, keep-base). |
| e3 (48) | E4B ignores a failed check | 15/7/4, 20/6/3, 28/11/7, 26/7/3 | 6.5 | exceeds | 3.5, cannot clear | prompt structure, as e2. Many of the E4B's failed checks are pytest usage or collection exits (2, 4), which a fix to the library does not change. |
| e4 (48) | E4B last check fails | 15/7/4, 21/6/3, 29/11/7, 26/7/3 | 6.5 | exceeds | 3.5, cannot clear | prompt structure, as e2 |
| g (48) | E4B submits early with room | 47/11/6, 48/12/9, 48/12/7, 46/11/6 | 11.5 | exceeds | 7.5, exceeds | `eval_config.yaml` cannot make a run use its budget, and the caps already allow 480 s and 28 calls. A prompt line to keep working before submitting would be speculative: EXP-055 tested a last-check rule. There is no measured mechanism by which more time converts. |

- **Reading 2.7 and section 4 as written.**
  - Every judged separating item (a, b, c, f, and e2 and e4 on the sample) **cannot clear the rule at full conversion**, so no lever on them is proposed for GPU. With the 7 un-regraded gated runs dropped (defect 14), the means fall to between 1.5 and 2.5.
  - **e2, e3, e4 and g over 48 clear the rule.** Their conditioned ceiling as written is above 3.83: 6.5 for e2, e3 and e4, and 11.5 for g. Under section 4 they **go to the lead as candidates for the ladder, desk check first**. Their levers are the check line in the prompt (e2, e3, e4) and a use-the-budget line (g).
  - d also exceeds (9.5), but its direction is not a lever (defect 3).
  - **Sensitivity, defect 1.** Leaving out the E4B runs that already resolved, e2, e3 and e4 fall to 3.5, which cannot clear. g stays above, at 7.5.
- **What the conditioned ceiling measures over 48.** It is bounded by the model gap itself: the 12 tasks arm R resolves under the re-grade, minus the E4B's resolves there. Every E4B run on those tasks that fails is in nearly every item's failing state. So the ceiling exceeding the threshold says the model gap is large. It does not say that flipping the item would convert, and sufficiency is untested. g is the clearest case: its loose count is 46 to 48 of 48 runs per draw.
- **Candidates for the lead, as written.** There are two: the check line (e2, e3, e4) and the budget line (g). Annotations on each:
  - The check line clears only if resolved runs count.
  - Two smoke screens on near variants of the check line, EXP-045 and EXP-055, fired rows with no decision.
  - g has no measured mechanism by which more time converts.
  - Section 4 licenses nothing on GPU by itself, and this study proposes no GPU arm.

### 6.6 Predictions scored

| prediction | outcome |
|---|---|
| P1 arm R E6 F3 R6 C14 S10, 9 resolved (95%) | **hit** |
| P2 E+F at least 0.50 of leaves-at, F most frequent (60%) | **hit**: 0.692, F 26 |
| P3 E4B at C, S or resolved in at most half where arm R is (60%) | **miss**: 84 of 132 (0.636) |
| a: E4B at most 0.40, arm R at least 0.60, separates (55%) | **hit**: 8/24, 10/10, separates |
| b: E4B at least 0.40, arm R at most 0.20, separates (45%) | **hit**: 16/24, 0/10, separates |
| c: E4B "all" less by at least 0.30, separates (40%) | **hit**: +0.467, separates |
| d: both at least 0.70, does not separate (55%) | **hit on the sample** (25/26, 9/9, does not separate). Over 48 d separates with arm R lower (35/40). |
| e1: E4B lower by at least 0.30, separates on the sample and over 48 (65%) | **miss**: the E4B checks more on the sample (20/26 against 5/11, leans the other way), and over 48 arm R lies inside the draw range |
| f: E4B at least 0.25, arm R at most 0.10, separates (35%) | **hit**: 11/26, 0/9, separates |
| g: E4B submits with room more, median at least 300 s against at most 200 s, separates (80%) | **hit over 48** (about 400 s against 179.7 s, separates). It does not separate on the sample (3 untied tasks). |
| Levers: no separating item has a conditioned ceiling above the threshold (60%) | **miss as written**: d, e2, e3, e4 and g exceed over 48. All judged items fall below it. |

### 6.7 What this says, within section 4

- **Part 1.** With the harness and files fixed, the E4B leaves the 31B's path mostly before a change lands on a gold file. On the short task-draws it stops at E or F in 0.692 of cases: F 26, E on other files 9, E with every gold-file edit failed 8, E with no change 2. Where the 31B reaches the gold regions, the E4B also reaches them in about two thirds of task-draws.
- **Part 2.** On the ever-resolved tasks where an E4B run reaches a gold file and fails, it states the gold's cause in 8 of 24 codable runs, against 10 of 10 for arm R. In 16 of 24 it acts on a different cause and keeps it. Where it does state the gold's cause, its change carries a code-level defect in 7 of 8 runs (x1, added after reading).
- **Its checks.** The E4B's checks are pytest runs, and 106 of 109 of them exit non-zero, by usage or collection errors or test failures; it submits after them. Arm R's checks are `python -c` runs or scripts, and 34 of 50 of them exit 0.
- **Opportunity.** None of the judged differences has enough opportunity on the sample to clear the D-011 rule. The over-48 check items and g do clear it as written, but their ceilings are bounded by the model gap and sufficiency is untested.
- **Limits.** All of this rests on one 31B draw and on step windows that hold a fifth to a third of each run's thought text.

## Status

ANALYZED 2026-11-12, 0 GPU-h (pre-registration 4a5968a; results 8f7875d, corrected in the next commit, defects 12 to 14).

- **Part 1.** The E4B leaves before a change lands on a gold file (E+F 0.692 of short task-draws). Of the 19 E leaves, 8 had every gold-file edit fail.
- **Part 2, sample.** a, b, c and f separate on the sample, and none can clear the D-011 rule there.
- **Part 2, over 48.** d, e2, e3, e4 and g separate. As written, e2, e3, e4 (6.5) and g (11.5) clear the rule and go to the lead as desk-check candidates (the check line in the prompt; a use-the-budget line). Without the resolved E4B runs, e2 to e4 fall to 3.5 and g holds at 7.5.
- **No GPU arm proposed.**
