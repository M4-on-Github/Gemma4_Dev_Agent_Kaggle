# EXP-044 — E4B, one prompt line "read the lines, then copy them" for edit_file, on the 8 ids where every edit failed (failed-edit-8), with an unchanged-tree control

**Date:** 2026-11-05
**Type:** smoke-8 screen, 8 ids, conversion measure (the cohort is selected on outcome, section 2.3). Arm X about 0.25-0.56 L4x4-h (point 0.42); the control arm X0 about 0.25-0.56 h (point 0.38), pushed only if row 4 fires (section 4); both 0.50-1.1 h. **Built, not pushed**: the user has not approved this screen's GPU.
**Cohort:** failed-edit-8
**Ladder:** L2. L0 and L1 are EXP-043 (the failed-call classes on these 8 ids; its row 1 fires on the copy half and licenses this screen, 9.9). The desk check of this file (section 2.3) found that the same line cannot be screened on smoke-8: the endpoint has no room there.
**Pre-registered:** this file, the cohort file, the tree, the zip's recorded sha and the notebooks are committed before any push. Sections 3 to 5 are written blind and are not revised; results are appended as a new section.
**Serves:** no claim directly. It touches C-004 (edit calls that never reach the file) and C-006 (retry after a failed edit), neither of which covers a copy error.
**Relates:** EXP-043 (the license, 9.4 row 1 and 9.9; its 9.7 items 1 to 3 are in view here), EXP-038 (the baseline run of these 8 ids; same tree as the arm X0 control), EXP-033 (the other E4B reference, smoke-8 only), EXP-042 (the check-before-submit mining, not this variable), EXP-045 (the second screen of this job, a different variable on a different cohort).
**Tags:** [V] verified in trace or by a check run here, [M] community or mirror, [I] inference, [H] hand judgement.

## 1. Why this, now

EXP-043 mined the 39 failed `edit_file` calls on the 8 ids where every edit of the EXP-038 E4B run failed. Its row 1 fired on the copy half: 5 of the 8 tasks have a majority of calls in the "paraphrase" class (the old string differs from the file in non-whitespace characters, T(b) = 5), 1 task is "from memory" (T(c) = 1), the other classes are 1 each (lost arguments, other). All 8 tasks ended far inside the budget (59.6 to 190.1 s of 480 s, at most 17 of 28 calls): the agent gave up after 3 to 8 failures. EXP-043 9.9 licenses "at most a smoke-8 screen of a prompt line about exact copying, with the endpoint being the share of tasks with an applied edit, not the resolve rate". This file is that screen.

It is a **conversion measure on a cohort chosen because it failed**, so it reads a bound and carries its confound in every row (2.3, 4). EXP-043 9.7 items 1 to 3 are the reasons for caution: the existing prompt already says `old_string` must match the file exactly, including indentation, so the new line repeats an instruction and changes only its form; 8 of 8 tasks had read the file (the region itself 5 of 7, correction in 9.7 item 10); and the non-unique-match failures (3 tasks) and the lost-argument failures (3 tasks) are outside this line.

## 2. Design

### 2.1 The tree

`experiments/EXP-044/candidate-x/` is `experiments/EXP-033/candidate-e4b/` (the v24 prompt at 8 minutes and 28 calls, `model: gemma-4-e4b-it-qat-w4a16-ct`; EXP-038 ran it unchanged, same zip) with **one inserted bullet** in `prompts/system.md`, section 3, directly after the "Prefer `edit_file`" bullet. `agent.yaml`, `configs/sampling.yaml` and `eval_config.yaml` are byte for byte EXP-033's (no value changes, so no dated comment is added to the YAML). The inserted text alone is `experiments/EXP-044/x_insert.md`:

```
- Immediately before each `edit_file` call, `read_file` the exact lines you are about to replace, then copy `old_string` from that output character for character: the same indentation, the same comments, no `...`, no abbreviated names and no line you did not see. If `edit_file` says `old_string` was not found, read the same lines again and copy them again; do not retype them from memory.
```

Scope, fixed now: this is the row 1 line of EXP-043 ("read the exact lines immediately before editing and copy them"), plus the one retry clause that is the same instruction applied to a failed call. It says nothing about non-unique matches (the error text already asks for more context; advice there is a second variable, EXP-043 9.7 item 2) and nothing about the read range (EXP-043 9.7 item 7, 6 calls on 2 tasks). The `diff -ru` of the two trees is recorded in section 8 once built.

Known design risks, written before the run: (a) one more `read_file` per edit costs a call and about 6 s per turn; the existing "by your 12th tool call a source file must already be edited" rule is not changed and the extra reads may push an edit later; (b) the line repeats an existing instruction, so a null result is likely if the cause is not the instruction's form; (c) the E4B may copy a line-number prefix if the read tool shows one, and the line does not mention it (not verified from the prompt; the first trace shows it).

### 2.2 The arms and the order

| Arm | Tree | Zip | Cohort | Pushed |
|---|---|---|---|---|
| X | candidate-x | `dist/EXP-044-x.zip` | failed-edit-8 | first, if the user approves the GPU |
| X0 (control) | EXP-038's tree unchanged | `dist/EXP-038-e4b.zip` (sha `9de869bd...`, the zip EXP-038 ran) | failed-edit-8 | only if row 4 fires |

Two notebook directories, `notebooks/exp044_x/` and `notebooks/exp044_x0/`, both named for this EXP number so `guard_push` finds this file. One file holds both arms because both are on one cohort (`guard_push` compares one `**Cohort:**` line to the notebook's `TASK_IDS`). EXP-045 is a separate file because its cohort is smoke-8.

### 2.3 The cohort, and the desk check that chose it

**Smoke-8 cannot move this endpoint [V].** The share of tasks with an applied edit (an `edit_file` call with status ok) on the smoke-8 ids in the two references:

| Reference | Tasks with an applied edit | `edit_file` calls | Failed calls | Tasks with a failed call |
|---|---|---|---|---|
| EXP-038 (the smoke-8 subset of dev-48) | 8 of 8 | 20 | 10 | 3 (fastapi_14301 1, httpx_3672 4, fastapi_14605 5) |
| EXP-033 | 6 of 8 (requests_7205 every edit failed, httpx_3672 never edited) | 17 | 7 | 2 (requests_7205 3, fastapi_14605 4) |

A baseline of 6 to 8 of 8 leaves no room for a 6-of-8 flip. By error class, EXP-043 9.6 typed the EXP-038 failures: fastapi_14605 five non-unique matches, httpx_3672 three non-unique and one not-found, fastapi_14301 one lost argument, so 8 of the 10 reference failures are the class the line does not target. The 7 EXP-033 failures are all "old_string not found" (requests_7205 3, fastapi_14605 4; `grep` of the harness's fixed message over the two traces, no lost-argument message in either) [V], which is the class the line targets, but they sit in two tasks, one of which (fastapi_14605) applied an edit afterwards. So at most 1 or 2 smoke-8 tasks could convert. **Arm X is not worth a kernel on smoke-8, and is not built on it.**

**The cohort the endpoint needs: failed-edit-8** (`experiments/cohorts/failed-edit-8.txt`, committed with this file): the 8 ids on which every `edit_file` call of the EXP-038 E4B run failed (`n_edit_fail` equals the `edit_file` count in `tool_histogram`, count at least 1; EXP-042 section 2 quantity (ii)). The rule is fully specified and needs no seed: fastapi_13786, fastapi_14360, fastapi_14459, fastapi_14873, fastapi_15661, rich_3063, rich_3676, rich_3935. The same 8 ids as EXP-043, so its classes apply.

**Selected on outcome. Two consequences, stated here because the lead is asked to buy GPU on this file.**

1. **The baseline is 0 of 8 applied by construction, from one stochastic draw.** A re-run of the unchanged tree would apply edits on some of these ids by regression to the mean alone (every id was chosen because one draw failed; temperature 1.0). So a single kernel of arm X can give only a bound, and the pre-registered bound (row 4) is not an effect. The clean read is arm X paired with the unchanged-tree re-run X0 on the same 8 ids (rows 5 to 7), two kernels.
2. **Three of the 8 are gated** (fastapi_13786, fastapi_14360, fastapi_14459: EXP-037 and `experiments/cohorts/gated-8.txt`; the grader lacks two test-only packages and a gated task resolves 0 on this grader as run). Their resolves carry nothing about the line. The endpoint is applied edits, which the gating does not touch.

**Drift between references.** For these 8 ids there is one reference draw (EXP-038), not two (EXP-033 ran smoke-8 only). The EXP-033 and EXP-038 smoke-8 draws differ on the same tree (mean wall 56.9 s against 78.3 s), which is the drift this design must not read as an effect: so wall is never an endpoint here (recorded only), no row compares a mean against a mean, and the count rows are read only against the control X0 or as a bound.

### 2.4 Cost

| item | seconds | basis |
|---|---|---|
| kernel overhead | 432 to 504 (0.12 to 0.14 h) | EXP-040 about 443 s, EXP-033 about 445 s |
| per task, the 8 ids' own EXP-038 walls | 59.6, 110.7, 121.0, 190.1, 91.5, 79.6, 84.2, 121.3 (sum 858, mean 107) | EXP-038 `summary.jsonl`, the same 8 ids |
| per task, arm X | 60 to 190 plus 0 to 8 extra `read_file` turns at about 6 s: about 107 + 25 at the point | EXP-033 per-turn 6.0 s [I for the number of extra reads] |
| arm X kernel | 912 to 2,024 s = **0.25 to 0.56 h, point about 0.42 h** | 8 x 60 + 432 to 8 x 190 + 504 |
| arm X0 kernel | **0.25 to 0.56 h, point about 0.38 h** | the same arithmetic with the 858 s sum, no extra reads |
| both | **0.50 to 1.1 h, point about 0.8 h** | |

**Conditional worst case per kernel about 1.24 h**: every task at the 495 s cap plus 504 s overhead. The tasks ran far inside the cap in EXP-038, so this needs every task to keep trying edits to the clock. A task that applies an edit usually runs a check afterwards and so takes longer than these 8 did: the high end is the realistic ceiling. The lead owns the ledger and the user's ceiling.

`pack_submission.py --skip-budget-gate --allow-warnings` is used for arm X: the 8-minute setting is above the 4.5-minute packing gate (as EXP-032, EXP-033 and EXP-040), the gate is for the real submission, and a screen is never uploaded. Arm X0 reuses the EXP-038 zip, which was packed the same way.

## 3. Endpoints, fixed in advance

Counts over the 8 tasks, from `runs/EXP-044-x/.../traces/trace_<id>.json`, `summary.jsonl` and the kernel log. Reference for each is EXP-038's row for the same id (all 8 failed by construction), and X0 when it exists.

| # | Endpoint | Definition |
|---|---|---|
| E1 | A, applied | tasks of 8 with at least one `edit_file` call whose observation status is not error (EXP-042 quantity: `n_edit_fail` less than the `edit_file` count) |
| E2 | N_e, edited | tasks of 8 with at least one `edit_file` call at all |
| E3 | Failed calls by class | per task and in total, failed `edit_file` calls typed E1 (old_string not found), E2 (mandatory parameters not present), E3 (other, non-unique counted apart), with EXP-043's 39 calls (22, 5, 12; 11 of the 12 non-unique) as the reference; recorded, not read |
| E4 | Non-empty patches | tasks of 8 with a non-empty patch |
| E5 | Calls and wall | per task `n_calls` and `wall_s`; capped (28 calls or 480 s); recorded, not read |
| E6 | Resolves | recorded only, never read (3 of the 8 are gated) |

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Order is first match. A and N_e are counts over the 8 tasks. Rows 1 to 4 read arm X alone; rows 5 to 7 are appended only if X0 is run. **A bound, not an effect, with the regression-to-the-mean confound named in every row.**

| Row | Condition | Reading |
|---|---|---|
| 0 | infrastructure: a crash in more than 2 of 8, or the tree does not run | fix the one cause and re-run once; no reading |
| 1 | N_e is 5 or fewer of 8 | the agent does not reach an `edit_file` call on most tasks, so the endpoint has no denominator; no reading on the line; look at why (reading budget, the extra reads) before another arm |
| 2 | A is 3 or fewer of 8 | the line does not convert the failed-edit tasks beyond what a re-run of the unchanged tree plausibly gives (about 3 of 8 under the blind estimate below): **kill the line as specified**; X0 is not bought |
| 3 | A is 4 of 8 | no decision; equal to the unchanged-tree estimate; X0 is not bought on this |
| 4 | A is 5 or more of 8 | the bound is met, and it is not an effect (regression to the mean is not excluded): **buy X0** (the unchanged tree, same 8 ids) and read rows 5 to 7. The share of failed calls typed E1 is reported beside it |
| 5 | (after X0) A_X >= 5 and A_X - A_0 >= 3, and A_0 is 3 or fewer | the line converts failed-edit tasks over the unchanged tree: **promote** to one dev-48 E4B arm (section 5). Six of eight tasks must flip the same way for p < 0.05, so this is a promote gate for a cost-priced arm, not evidence of an effect |
| 6 | (after X0) A_0 >= A_X - 1 | the unchanged tree applies as many: regression to the mean explains row 4; **kill the line as specified** |
| 7 | (after X0) otherwise | no decision; the lead may buy a dev-48 arm on cost grounds alone |

Recorded in every row, not read: E3 (the error classes), E4, E5, E6. The classes E2 (lost arguments, rich_3935's shape) and non-unique matches are expected to persist because the line does not address them.

**Blind prediction.** N_e at least 6 of 8: 85%. A: 4 of 8 (range 2 to 6); the tasks the line can reach are the not-found tasks (fastapi_15661, 14873, 14459, 14360, 13786, rich_3676, so at most 6 of 8), and rich_3935 (lost arguments every call) and rich_3063 (non-unique) are not addressed. P(row 2) 40%, P(row 3) 25%, P(row 4) 30%, P(row 1) 5%, row 0 about 5%. If X0 is run: A_0 about 3 of 8 (range 1 to 5), because the 17 other tasks with a failed edit recovered in the same draw (EXP-043 9.6). Failed calls by type over the 8 tasks: not-found about 12 (from 22), lost-argument about 5 (unchanged), other about 10 (unchanged). Non-empty patches 5 of 8. Resolves 0 to 1 of 8, recorded and not read.

## 5. What this licenses

**The screen can decide one of two things.** It can **kill the line as specified** (row 2, or row 6 after the control), or **promote it to one dev-48 E4B arm** (row 5). Row 4 alone only buys the control; rows 1, 3 and 7 decide nothing. It cannot decide that the line raises the resolve rate (an applied edit is not a resolved task: EXP-043 9.8), and it cannot show a dev-48 effect (the cohort is selected on outcome).

**The dev-48 endpoint if row 5 fires.** A paired comparison against EXP-038 on all 48 ids, which removes the selection by running every id: the share of tasks with an applied edit and the share of `edit_file` calls typed not-found (the E1 rate per call), paired per task; paired resolves (McNemar, discordant pairs reported) as a second, recorded endpoint; calls and wall as cost, with the projected 120-task hours at the setting used. Not an upload. Cost of that arm: 48 x 78 to 110 s + about 450 s overhead = about 1.2 to 1.7 L4x4-h [I], to be recomputed from this screen's wall before the ask.

No row licenses an upload and no row moves a claim.

## 6. Exact commands

```
python tools/validate_submission.py experiments/EXP-044/candidate-x --strict
python tools/pack_submission.py --src experiments/EXP-044/candidate-x --out dist/EXP-044-x.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed dist/EXP-044-x.zip --username rainm4 --cohort experiments/cohorts/failed-edit-8.txt --set EXP_ID='"EXP-044-x"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp044_x/kaggle_eval_l4x4.ipynb
python tools/build_notebook.py --embed dist/EXP-038-e4b.zip --username rainm4 --cohort experiments/cohorts/failed-edit-8.txt --set EXP_ID='"EXP-044-x0"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp044_x0/kaggle_eval_l4x4.ipynb
# push, a later job, only after the user approves the GPU and the lead dispatches it:   kaggle kernels push -p notebooks/exp044_x
# the control is pushed only if row 4 fires:                                              kaggle kernels push -p notebooks/exp044_x0
# after COMPLETE, a separate job:
kaggle kernels output rainm4/gemma4-exp044-x -p runs/EXP-044-x/
python tools/analyze_traces.py <inner bundle dir> --cap-minutes 8 --max-calls 28
python tools/run_forensics.py compare runs/EXP-038-e4b-dev48 <inner bundle dir>
```

## 7. Defects

Written before the run.

1. **Selected on outcome.** Row 4 is a bound that a re-run of the unchanged tree can pass (at a rate of about 0.4 per task, 5 or more of 8 happens about 17% of the time, and 6 or more about 5%; [I], the 0.4 is not measured). That is why row 4 buys the control and does not promote.
2. **One reference draw per id.** No second E4B run covers these 8 ids; the control X0 is the only reference that shares the draw-to-draw noise.
3. **The line repeats an existing instruction** (EXP-043 9.7 item 3), so a null result is the likely outcome and is a result.
4. **The mechanism is not isolated.** If A rises, the screen cannot say whether the read-before-edit step or the copy wording did it; both are in one bullet by EXP-043's row 1 wording.
5. **Applied is not correct.** An applied edit with the wrong fix is an applied edit (EXP-043 9.8); resolves are not read.
6. **The 12th-call rule** is unchanged and the extra reads cost calls; a task could reach its first edit later.
7. **Seen-before:** the references' failed calls and their classes (EXP-043 9.1 to 9.6); the prediction above uses them. The new line was written after seeing them.

## 8. Built

Not built yet. Sections 1 to 7 are the pre-registration; the build record follows below the Status line when the tree, zips and notebooks exist.

## Status

2026-11-05: pre-registered, not built, not pushed. Zero GPU. Arm X is not built on smoke-8 (the endpoint is at ceiling there, section 2.3); built on failed-edit-8 only, with the unchanged-tree control X0 priced alongside it.
