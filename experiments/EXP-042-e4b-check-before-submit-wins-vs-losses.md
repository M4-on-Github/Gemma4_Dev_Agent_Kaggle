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

Pending.

## Status

2026-11-05: pre-registered, committed before any E4B win trace was opened for this purpose. Results pending.
