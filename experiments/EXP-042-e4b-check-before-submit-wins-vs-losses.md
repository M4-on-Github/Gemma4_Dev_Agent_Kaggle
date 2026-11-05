# EXP-042 — Does an executed check before submit separate the E4B's wins from its losses on dev-48? Zero-GPU trace mining over EXP-038 and EXP-028 Arm R

**Date:** 2026-11-05
**Type:** zero-GPU trace mining (L1) over existing run directories. No kernel, no upload, no zip, no notebook, 0.0 L4x4-h.
**Cohort:** none run. Reads all 48 dev-48 ids of `runs/EXP-038-e4b-dev48/` (E4B) and of `runs/EXP-028-armR/` (31B Arm R) read-only.
**Ladder:** L1. Follows EXP-041 and feeds the lead's ranking of two candidate levers in `knowledge/plan.md` (a check-before-submit rule; the failed-edit-then-submit path). No claim status moves.
**Pre-registered:** commit of this file, before any E4B win trace was opened for this purpose (see "What was seen before writing").
**Serves:** the lead's ranking of the E4B levers; C-020 context only.
**Relates:** EXP-041 (the four targets and the 19-id control; its section 9.4 observation 1 is the question here), EXP-038 (E4B dev-48, not touched), EXP-028 (Arm R, not touched), EXP-036 (gated and constant ids).
**Tags:** [V] verified in the traces or tool output, [H] read by hand from a trace, [I] inference.

## 1. Why this, now

EXP-041 found that the E4B submits with no informative check on 4 of 4 target tasks and on 16 of 19 control ids, and Arm R ran its own reproduction on all four targets. It did not look at the E4B's five resolved tasks. If the wins ran a check and the losses did not, a check-before-submit rule has trace support as a lever. If the wins also ran nothing, it has none. EXP-041 also found that 5 of the 6 empty patches in its control were tasks where every `edit_file` call failed and the agent still submitted; section 9 sizes that path on all 48 as recorded quantities.

## 2. Design

**Population.** The 48 ids of the EXP-038 E4B run. Wins: the 5 resolved ids (fastapi_14301, fastapi_14463, rich_3006, rich_3905, requests_6644). requests_6644 resolves with an empty patch (EXP-036, the free task), so every table is also given without it. Losses: the other 43. Marked so a reader can drop them: the 5 impossible ids (httpx_3672, requests_7205, requests_7309, requests_7315, requests_7427, never resolve on this grader) and the 15 gated fastapi ids (the dev-48 fastapi ids not in `informative27` of `experiments/EXP-038/cost_estimate.json`: fastapi_11355, 13207, 13786, 14262, 14297, 14360, 14459, 14512, 14583, 14605, 14609, 14953, 14962, 14964, 15030). Dropping both leaves the informative 27 (4 wins plus 23 losses, the 4 EXP-041 targets and the 19 control ids).

**The check, definition fixed now.** EXP-041 section 2 defined it as: "a `run_command` whose command string contains `pytest`, `unittest`, `tests/`, or starts a `python` run, issued before the `submit_patch` call", counted as `tests` (pytest, unittest or `tests/`) and `code` (any other python run). That wording is reused. One clarification, which is how EXP-041 applied it and is stated here so it can be checked: a command counts only if it **runs** pytest, unittest, a file under `tests/`, or a python interpreter (including `python3 -c` and a heredoc that is then run). Listing, grepping or `cat`-ing a path under `tests/` or a command that merely contains the word python (for example `grep python_version`) is not a run. Applied again to all 48 ids, so the 23 ids EXP-041 classified must come out the same; a difference is reported as a defect.

**Sharpened measure ("informative").** EXP-041 section 9.4 used "informative" without a rule. The sharpened rule, fixed now and applied to all 48 E4B ids and all 48 Arm R ids: a task has an **informative check** if at least one counted run has an output that is not an environment or launcher failure. A failure is one of: a collection error from `ModuleNotFoundError` or `ImportError` (for example the missing `inline_snapshot`, `dirty_equals`), `command not found`, `No such file or directory` for the target, or `no tests ran`. A script that runs and raises the bug's own error or prints a result is informative. The as-written definition is the primary measure; the sharpened one is a second 2x2 of the same tasks.

**The 2x2.** Rows resolved (W) and not resolved (L); columns check run, no check run. Filled for: E4B all 48, E4B without requests_6644, E4B informative 27 (gated and impossible dropped), E4B informative 27 without requests_6644 (3 wins); and the same all-48 and informative-27 versions for the sharpened measure. Arm R: all 48, and its informative-27 version, as-written and sharpened, with 9 wins.

**Order assumption.** Commands that precede the `submit_patch` call are those that precede it in step order; a task ends at its (last) `submit_patch`, so a check after it does not occur and is not looked for.

**Recorded quantities on all 48 E4B ids, no reading attached.** (i) tasks with at least one `edit_file` call that failed (`n_edit_fail` >= 1 in `summary.jsonl`); (ii) tasks where every `edit_file` call failed (`n_edit_fail` equals the `edit_file` count in `tool_histogram`, count >= 1); (iii) tasks that called `submit_patch` and ended with an empty patch (`patch_empty` true and `submit_patch_called` true). For each: how many resolved, and the overlap with the gated, impossible and free ids. Reported with and without the marked ids.

**Instruments.** `summary.jsonl` of each run (written by `tools/analyze_traces.py`) for the recorded quantities; `grep -o -H -c -l` over the trace JSON for command strings and observation heads; `Read` for anything ambiguous, marked [H]. The shell of this agent allows no ad-hoc scripts or pipes, so counts are `grep` output tallied by hand, each reproducible with the commands in section 6.

**Cap and scope.** No GPU, no kernel. Nothing in `submission/`, `tools/`, `tests/`, EXP-038, EXP-028, EXP-041 or another agent's README row is touched. Per plan.md:52 nothing from `runs/` goes into git except counts, task ids, file paths and short labels.

### What was seen before writing this file

Not blind, disclosed so the readings are weighed accordingly:

- EXP-041 section 9: the classification of the 4 targets and 19 control ids, which gives for the 23 informative losses the as-written check count (fastapi_14448 pytest, rich_3935 pytest, rich_3105 python3 tool run, fastapi_15589 bare pytest, fastapi_9753 pytest tests/: 5 of 23) and the sharpened count for those (the two bare full-suite pytest runs of fastapi_15589 and fastapi_9753 are collection failures: at most 3 of 23 informative).
- The `summary.jsonl` rows of all 48 E4B ids (calls, `n_edit_fail`, `tool_histogram`, `patch_empty`), so the three recorded quantities of section 2 are tallied from rows already seen and **no prediction is made for them**. For the 5 wins I saw the `run_command` counts (fastapi_14463 3, fastapi_14301 2, rich_3905 2, requests_6644 4, rich_3006 2) but **not** the command strings or outputs.
- For Arm R I saw the summary rows and the check commands of the four EXP-041 targets only (a python3 reproduction in all four).
- The 20 other losses (the 15 gated and the 5 impossible ids): nothing seen beyond the summary rows.

## 3. Endpoints

1. The 2x2 counts (check run or not, by resolved or not), as-written and sharpened, for each population in section 2, E4B and Arm R.
2. The recorded quantities (i) to (iii) with resolved counts.
3. No test statistic is an endpoint; 5 wins support none. Percentages are descriptive.

## 4. Readings (blind)

Notation: W is the number of E4B wins with a check (of 5), L the number of E4B losses with a check (of 43), by the as-written measure over all 48. Applied the same way to the sharpened measure.

| # | Observed | Reading |
|---|---|---|
| 1 | W <= 1 | The wins mostly ran nothing. A check-before-submit rule has no trace support as a lever, whatever L is |
| 2 | W is 2 or 3 | No reading. Five wins cannot separate the groups; the rule is neither supported nor rejected by this table |
| 3 | W >= 4 and L <= 10 (at most 25 percent of losses) | The wins ran checks and most losses did not. The rule has observational trace support as a lever: a candidate for a smoke-8 screen whose endpoint is enforcement and share of tasks with an informative check, not resolve rate |
| 4 | W >= 4 and L >= 22 (at least 50 percent of losses) | The habit is common to wins and losses. The losses did not lack it; a rule that requires it has no trace support as a lever |
| 5 | W >= 4 and 11 <= L <= 21 | A weak, unread separation: the rates are reported, no lever is ranked on them |

Robustness, applied to rows 1 to 5: the table is also read without requests_6644 (4 wins, thresholds: W' <= 1 row 1, W' = 2 row 2, W' >= 3 with the same L rules rows 3 to 5) and on the informative 27 (23 losses; L' <= 5 low, L' >= 12 high, between those row 5). If any variant gives a different row from the all-48 reading, the report says "not robust to the marked ids" and the weaker of the readings governs (rows ordered 3 strongest, then 5, then 2, then 4 and 1 as non-supportive).

Arm R (9 wins, 39 losses), same measures; W_R and L_R are the counts with a check.

| # | Observed | Reading |
|---|---|---|
| R-A | the check rate over all 48 is at least 80 percent and the win rate (W_R of 9) and loss rate (L_R of 39) differ by less than 15 points | R's check habit is near-universal and does not track resolves inside R. The E4B-to-R difference is then a difference in the level of the habit, not shown to track outcome within a model |
| R-B | the win rate exceeds the loss rate by 25 points or more | The check habit tracks resolves in the 31B as well |
| R-C | anything else | Rates reported, no reading |

The readings decide what the lead may rank, not what is true.

**Predictions, written blind.** E4B as-written: W = 4 of 5 (all but one win ran pytest or a python snippet), L = 8 of 43 (of which 5 are the already-seen informative losses, plus about 3 among the 20 gated and impossible ids): reading row 3 if L <= 10. E4B sharpened: W = 3 of 5, L = 5 of 43 (the gated fastapi tasks fail collection in the sandbox, so some of their runs will not be informative). Arm R: W_R = 9 of 9, L_R = 33 of 39, reading R-A if the rates come out within 15 points. The uncertainty is large; the wins' commands were not seen.

## 5. Licenses

What the table can decide: whether the trace record shows the habit of an executed check on the E4B's wins, so that the rule is or is not an observationally supported candidate for a screen. What it cannot show: **it is observational. There are 5 wins (4 without the free task, 3 informative ones with a patch that came from a repair). Task difficulty confounds both columns**: an easy task can both invite a quick check and resolve, and a hard one can fail with or without a check. A win with a check does not show the check caused the win. R's habit may be capacity (a different model and budget), not a lever. No claim status moves; a positive reading licenses a smoke-8 screen of the rule, not a conclusion about resolves.

## 6. Commands

```
grep -c -e '"command": ".*python' -e '"command": ".*pytest' -e '"command": ".*unittest' -e '"command": ".*tests/' runs/<run>/traces/trace_<id>.json    # candidate traces
grep -o -H -e '"command": "[^"]\{0,110\}' runs/<run>/traces/trace_<id>.json                                                                                 # command heads of candidates
grep -c -e 'ModuleNotFoundError' -e 'ImportError' -e 'no tests ran' -e 'command not found' runs/<run>/traces/trace_<id>.json                                  # failure markers
grep -c -e '"patch_empty": true' runs/EXP-038-e4b-dev48/summary.jsonl
```

Counts that need a reading beyond the head of a command use `Read` on the trace, marked [H] in section 9.

## 7. Defects

Written before the run; section 9 appends any found.

1. **Clarification of the EXP-041 wording.** "Contains `tests/`" in EXP-041 was applied as a run, not a path; stated in section 2 and re-applied to all 48.
2. **Two measures, not one.** The as-written measure is primary; the sharpened measure is defined after EXP-041's post-hoc use of "informative" and is applied to all 48 ids and to Arm R.
3. **Hand classification.** The command heads are cut at 110 characters and the failure markers are string counts; a borderline run is read by hand and marked [H].
4. **Seen-before disclosure** in section 2: the 23 informative losses and the summary rows are not blind; the five wins' commands and the 20 other losses are.
5. **One run per arm.** Both runs are single draws of a stochastic loop.

## 8. Built

Nothing. No tree, zip, notebook or kernel. 0.0 L4x4-h.

## 9. Results

Mined 2026-11-05 after the pre-registration commit 510e2a2. Zero GPU. The readings of section 4 are applied as written. No trace text is reproduced; labels are one or two words.

### 9.1 E4B: which ids ran a check (as-written definition) [V]

17 of 48 ids ran a counted check before their `submit_patch`; 31 did not. 16 are `tests` runs (pytest) and 1 is a `code` run (rich_3105). Every check precedes the task's `submit_patch` by line order (fastapi_9753 submitted twice; its check precedes both). The 23 ids EXP-041 classified come out the same (5 of 23: fastapi_14448, fastapi_15589, fastapi_9753, rich_3105, rich_3935), so there is no defect against EXP-041.

| Group | Checked (as-written) | Informative (sharpened) |
|---|---|---|
| Wins, informative 27 (4) | fastapi_14301, fastapi_14463, rich_3006 | rich_3006 only |
| Wins, free (1) | none (requests_6644) | none |
| Wins not checking | rich_3905, requests_6644 | |
| Losses, informative 27 (23) | fastapi_14448, fastapi_15589, fastapi_9753, rich_3105, rich_3935 | rich_3935 only |
| Losses, gated 15 | fastapi_11355, 13207, 14262, 14297, 14583, 14962, 15030 (7) | none |
| Losses, impossible 5 | requests_7205, requests_7427 (2) | both (see 9.2) |

Non-checking ids (31): fastapi_13537, 13786, 14360, 14459, 14512, 14605, 14609, 14873, 14953, 14964, 15280, 15661, 15800, 5624; httpx_3672; requests_6644, 7309, 7315; rich_3061, 3063, 3067, 3180, 3468, 3480, 3521, 3676, 3905, 3934, 3953, 4070, 4075.

### 9.2 E4B sharpened measure: what the 17 runs returned [V] unless [H]

- 11 fastapi ids (fastapi_11355, 13207, 14262, 14297, 14301, 14448, 14463, 14583, 15030, 15589, 9753) ran a `pytest tests/` or bare `pytest` whose output is `collected N items / M errors`, exit 2, with `ModuleNotFoundError` for the missing test dependencies (the marker is in the output of each of these 11 traces). None of those runs ran a test.
- fastapi_14262, fastapi_14448 and fastapi_14962 each also ran a `pytest <file>` on a path that does not exist: exit 4, `no tests ran`.
- rich_3006 (win): 813 items collected, the suite ran with failures in other modules, exit 1. Informative by the rule.
- rich_3935: `pytest` on one test file, 5 passed. Informative by the rule. All four of its `edit_file` calls failed and its patch is empty, so the run exercised an unmodified tree.
- requests_7205 and requests_7427 (both impossible ids): 611 and 623 items collected, tests ran, exit 1, many setup errors (`E`) in the first. Informative by the rule [H]; both are dropped in the informative-27 version.
- rich_3105: a repo script run twice, both failing on a missing path. Uninformative by the rule [H]; the script is a repo utility, not a check of the edit.

### 9.3 E4B 2x2 (counts; no test)

As-written (check = any counted run):

| Population | Resolved: check / no check | Not resolved: check / no check |
|---|---|---|
| All 48 (5 wins, 43 losses) | 3 / 2 | 14 / 29 |
| Without requests_6644 (4 / 43) | 3 / 1 | 14 / 29 |
| Informative 27 (4 / 23) | 3 / 1 | 5 / 18 |

Sharpened (check = a run whose output is not an environment or launcher failure):

| Population | Resolved: check / no check | Not resolved: check / no check |
|---|---|---|
| All 48 | 1 / 4 | 3 / 40 |
| Without requests_6644 | 1 / 3 | 3 / 40 |
| Informative 27 | 1 / 3 | 1 / 22 |

Rates: as-written W = 3 of 5 (60 percent), L = 14 of 43 (33 percent); in the informative 27, 3 of 4 against 5 of 23 (22 percent). Sharpened W = 1 of 5, L = 3 of 43 (7 percent); informative 27: 1 of 4 against 1 of 23.

### 9.4 E4B readings applied (section 4)

- As-written, all 48: W = 3, row 2: **no reading**. Variants: without requests_6644, W' = 3 of 4 and L = 14, row 5 (weak, unread); informative 27, W' = 3 of 4 and L' = 5 (at most 5), row 3. The variants give different rows, so the result is **not robust to the marked ids**, and the weaker reading governs: row 2, no reading.
- Sharpened, all 48: W = 1, **row 1 fires**: the wins mostly ran nothing informative, and a check-before-submit rule has no trace support as a lever, whatever L is. The variants agree: without requests_6644 W' = 1 of 4 (row 1), informative 27 W' = 1 of 4 (row 1). Robust to the marked ids.
- What the two together show: of the two wins that ran pytest on fastapi (fastapi_14301, fastapi_14463), the run died in collection on the missing `dirty_equals` and `inline_snapshot` packages (the same output as all the fastapi losses that ran pytest), and they submitted and resolved anyway. The only win with an informative check is rich_3006.

### 9.5 Predictions against observed

| | Predicted (blind) | Observed |
|---|---|---|
| E4B as-written W, L | 4 of 5, 8 of 43 | 3 of 5, 14 of 43 |
| E4B sharpened W, L | 3 of 5, 5 of 43 | 1 of 5, 3 of 43 |
| Arm R as-written W_R, L_R | 9 of 9, 33 of 39 | 9 of 9, 28 of 39 |

The E4B wins ran fewer informative checks than predicted, and the L count was higher than predicted because 9 gated and impossible ids ran pytest (I guessed about 3). The R loss rate was lower than predicted.

### 9.6 Arm R (EXP-028, 31B, same 48 ids) [V] for the counts, [H] where marked

37 of 48 ids ran a counted check, 11 did not. Wins 9 (fastapi_13537, 14301, 14463, 15589, 9753; requests_6644; rich_3006, 3067, 3905), all 9 with a check, in order before `submit_patch` (by line number for each win). Non-checking ids (all losses): fastapi_11355, 13207, 13786, 14605, 15280, 15661, 15800; httpx_3672; rich_3061, 3676, 4070. R commonly runs a python3 reproduction (`-c`, a heredoc or a written script) rather than the suite; the single run of the suite is rich_3105 (pytest per file) and requests_7315 (pytest on one file). 6 R ids never called `submit_patch` (requests_7427, fastapi_13786, rich_3180, rich_3521, rich_3480, rich_3105); their checks, where they ran, are counted, so "before submit" is read as "before the task ended" for them (5 of the 6 checked). The pre-registration did not state this.

| Population (R) | Resolved: check / no check | Not resolved: check / no check |
|---|---|---|
| All 48 (9 / 39), as-written | 9 / 0 | 28 / 11 |
| Without requests_6644 (8 / 39) | 8 / 0 | 28 / 11 |
| Informative 27 (8 / 19) | 8 / 0 | 13 / 6 |
| All 48, sharpened | 9 / 0 | 27 / 12 |

Sharpened for R is a marker count plus hand checks, not a read of every run. Of the 37 R checker traces, 27 have none of the failure marker words anywhere, and 10 contain them: 8 only as source code read from the repo, and 2 as a real import error in a script run (fastapi_15030 in one of several runs, so it stays informative; fastapi_14360, whose single run dies on an import of a name the script guessed wrongly, read as uninformative [H], a borderline call that moves L_R by one). The 9 wins carry no marker. So the sharpened counts are 9 of 9 wins and 27 of 39 losses (28 minus 14360), as an upper bound because the 27 marker-free traces were not each read.

Readings (R, section 4): overall check rate over all 48 is 37 of 48 (77 percent), below the 80 percent R-A needs, so R-A does not fire. Win rate 9 of 9 (100 percent) against loss rate 28 of 39 (72 percent): a difference of 28 points, **R-B fires** (at least 25 points). The same holds without requests_6644 (100 against 72), on the informative 27 (100 against 68, 32 points) and on the sharpened measure (100 against 69, 31 points): robust to the marked ids. Restricted to the 33 R losses that submitted, 23 checked (70 percent); the reading is unchanged.

### 9.7 Recorded quantities on all 48 E4B ids (no reading attached)

From `summary.jsonl`, each cross-checked by `grep -c` (23 ids with `n_edit_fail` 0, hence 25 with at least one; 10 rows with `patch_empty` true; 5 resolved).

| Quantity | Tasks | Resolved | Gated | Impossible | Free | Informative 27 | Resolved in informative 27 |
|---|---|---|---|---|---|---|---|
| (i) at least one `edit_file` call failed | 25 | 3 (fastapi_14463, fastapi_14301, requests_6644) | 8 | 2 | 1 | 14 | 2 |
| (ii) every `edit_file` call failed (at least one call) | 8 | 0 | 3 | 0 | 0 | 5 | 0 |
| (iii) called `submit_patch` and the patch is empty | 9 | 0 | 3 | 0 | 0 | 6 | 0 |

- (i) ids: fastapi_15661, 15280, 14964, 14873, 14463, 14512, 14459, 9753, 13207, 14360, 14301, 14262, 15800, 14605, 13786; requests_7315, 6644; httpx_3672; rich_4070, 3935, 3180, 3676, 3480, 3105, 3063.
- (ii) ids: fastapi_15661, 14873, 14459, 14360, 13786; rich_3935, 3676, 3063. Of these 8, 7 ran no check at all; rich_3935 ran a passing test file on the unmodified tree.
- (iii) ids: the 8 of (ii) plus rich_4075, whose two `edit_file` calls did not fail and whose patch is nonetheless empty (cause not examined).
- Outside (iii): fastapi_13537 has an empty patch and never called `submit_patch` (text-format calls, EXP-041); it is not counted.
- Zero of the 9 empty-patch submitters resolved, as expected; none of the 5 wins has an empty patch (requests_6644 patch is non-empty, 939 bytes).

### 9.8 What the table cannot show

It is observational. There are 5 E4B wins (4 without the free task); 3 ran a counted check and 1 an informative one. Task difficulty confounds both columns: the 11 fastapi checkers that ran pytest got the same collection failure whether they won or lost, so on those tasks the check cannot have separated anything. Even for the sharpened measure, a run on a tree whose edits all failed (rich_3935) counts as informative because the rule counts runs, not whether they exercised the edit. R's higher rate (77 percent against 35 percent, as-written) is a different model and a different budget (4.5 min against the E4B's cap), not shown to be transferable. R-B is a descriptive association (11 of 39 R losses never ran anything) and the 11 non-checkers include tasks that are both hard and short. No claim status moves, and no p-value is read.

### 9.9 Outside the readings

1. A check-before-submit rule would, on the E4B, mostly produce a fastapi collection failure: 11 of the 17 E4B checkers ran pytest on a tree that cannot import its own test dependencies, so a rule that only requires "run the tests" is satisfied without information. What the E4B would need is a different kind of check (a short reproduction script, which is what Arm R writes), not a stricter pytest requirement. That is [I], not a measured effect.
2. The failed-edit-then-submit path is large and does not resolve: 25 of 48 E4B tasks had a failed edit, 8 had every edit fail, 9 submitted an empty patch, and none of those 9 resolved. This is a recorded count; the reading about which lever to rank is the lead's.
3. The pre-registration text called requests_6644 "resolves with an empty patch". The E4B's own patch for it is non-empty (939 bytes); the task is free in the EXP-036 sense (resolves under any patch). The population and tables are unaffected.
4. The pre-registered variant "informative 27 without requests_6644 (3 wins)" is ill-specified: the informative 27 never contained requests_6644 and has 4 wins; this file reports the 27 with 4 wins.
5. fastapi_14301 and fastapi_14463 (E4B wins) resolved after a pytest run that produced no test result. EXP-041 observed the same output for fastapi_15589 and fastapi_9753 (losses).

### 9.10 Defects found

1. The wording of EXP-041 "contains tests/" is clarified to a run (done as pre-registered); it matched EXP-041's counts.
2. Arm R's 6 no-submit ids were not provided for in the pre-registered order assumption; they are counted by "before the task ended" and the submitter-only rate is also reported.
3. rich_3105 and fastapi_14360 are [H] calls (uninformative); requests_7205 and requests_7427 are [H] calls (informative though with many setup errors). Flipping any of the four changes no row of section 4 for the E4B (W stays 1) and no reading for R.
4. R's sharpened counts are a marker count with 10 hand checks, not a read of all runs.
5. There are 12 fastapi checkers; 11 got the collection failure and fastapi_14962 only ran a pytest on a missing file.
6. 2026-11-05: a command string with a repo script path, an error text, and a test file name were removed from 9.2 for hygiene (lead job, after the critic light on EXP-041); no number or reading changed.
7. *Corrected 2026-11-05 (critic light):* rich_3105's second counted run exited 0 and its output contains none of the failure markers of the rule (its stderr does carry a path error from a sub-tool, and its stdout prints a result); by the rule as written it is informative, so the sharpened loss count is 4 of 43 (2 of 23 on the informative 27). W and every reading are unchanged. This supersedes "both failing" and "uninformative by the rule" for rich_3105 in 9.2; the first run exited 1 on a missing path.

## Status

2026-11-05: **MINED, zero GPU** (pre-registration 510e2a2). E4B as-written W 3 of 5, L 14 of 43: row 2, no reading, not robust (variants rows 5 and 3). E4B sharpened W 1 of 5, L 3 of 43: row 1 fires, robust. Arm R W 9 of 9, L 28 of 39: R-B fires, robust. Recorded: failed edit 25 of 48 (3 resolved), every edit failed 8 (0 resolved), empty-patch submit 9 (0 resolved). Observational, 5 wins; no claim status moves.
