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

Built 2026-11-05 after the pre-registration commit aa40b83, with the section 6 commands. Sections 1 to 7 are unchanged.

- **Diff, tree against baseline** (`diff -ru experiments/EXP-033/candidate-e4b experiments/EXP-044/candidate-x`): one hunk, `@@ -17,6 +17,7 @@` of `prompts/system.md`, one line added (the `x_insert.md` bullet, after the "Prefer `edit_file`" bullet), nothing removed. No other file differs: `agent.yaml`, `configs/sampling.yaml` and `eval_config.yaml` are byte for byte EXP-033's.
- **Validate:** `python tools/validate_submission.py experiments/EXP-044/candidate-x --strict` gave 4 files, 1 agent, `RESULT: INVALID (1 errors, 1 warnings)`: the one error is the packing gate (`120 x (8 + 1.0) min = 18.00 h`), the warning is the 240 s timeout (VERIFY(Q2)); both are the EXP-033 situation. The inserted text has no forbidden lint word and no URL (the packer's lint passed).
- **Pack, arm X:** `python tools/pack_submission.py --src experiments/EXP-044/candidate-x --out dist/EXP-044-x.zip --skip-budget-gate --allow-warnings` (the override stated in 2.4): 4 reachable files, `RESULT: VALID (0 errors, 2 warnings)`, 2.6 KiB. **Zip sha256 `ddcc377ada15ce67b798aae099b9ff84804084a704b92f86266a99117cd5310a`** (confirmed with `sha256sum`). Packed from LF worktree files that equal the committed blobs. Screen build, never uploaded.
- **Control zip, arm X0:** `dist/EXP-038-e4b.zip`, **sha256 `9de869bd2cd8853b72d653d06b9acef3e03794c8b588c26494435774dda11ac0`** (confirmed with `sha256sum`; the same bytes as `dist/EXP-033-e4b.zip`), the tree EXP-038 ran.
- **Notebooks**, parameter cells read back: `notebooks/exp044_x/kaggle_eval_l4x4.ipynb` (`EXP_ID = "EXP-044-x"`, 3,524 base64 characters) and `notebooks/exp044_x0/kaggle_eval_l4x4.ipynb` (`EXP_ID = "EXP-044-x0"`, 3,324 characters); both `RUN_GOLD_CONTROL = False`, `RUN_AGENT = True`, `N_TASKS = 8`, `MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"`, `TASK_IDS` = fastapi_13786, fastapi_14360, fastapi_14459, fastapi_14873, fastapi_15661, rich_3063, rich_3676, rich_3935 (the 8 ids of `experiments/cohorts/failed-edit-8.txt`).
- `kernel-metadata.json` in each directory: copied from `notebooks/exp033_e4b/` after the build, only `id` and `title` changed (`rainm4/gemma4-exp044-x`, `rainm4/gemma4-exp044-x0`; `diff` shows those two lines only).
- **Kernel ids: `rainm4/gemma4-exp044-x` (arm X), `rainm4/gemma4-exp044-x0` (control, only if row 4 fires).** **Not pushed.** The push is a separate job after the user approves the GPU. Push commands: `kaggle kernels push -p notebooks/exp044_x`, then if row 4 fires `kaggle kernels push -p notebooks/exp044_x0`.

### Push record, 2026-11-06

- **Arm X pushed** with `kaggle kernels push -p notebooks/exp044_x` at about 00:24 UTC on 2026-11-06 (19:24 local, read from the file clock to the minute; this shell has no clock command). Output: `Kernel version 1 successfully pushed`. Repo HEAD at the push: `73d369d90c96fa1b66bebf6a4467582c63ebb554`; the pre-registration is `aa40b83`, the notebook and zip are the section 8 build (zip sha256 `ddcc377a...310a`, unchanged).
- **Kernel id `rainm4/gemma4-exp044-x`**, version 1. `kaggle kernels status` right after the push: `KernelWorkerStatus.RUNNING`. `notebooks/exp044_x/kernel-metadata.json` has `is_private: true`, `enable_gpu: true`, `machine_shape: NvidiaL4`, `enable_internet: false`, `model_sources` the E4B.
- **Arm X0 not pushed.** The user's approval (2026-11-06, `knowledge/user-decisions.md`) covers X0 only if X's analysis applies an edit on 5 or more of 8, as row 4 reads. Stop rules from the approval: no re-run of a failed kernel without asking; a kernel set to pass its stated worst case (1.24 h) is reported to the lead.
- **Next, a separate job:** when `kaggle kernels status rainm4/gemma4-exp044-x` says COMPLETE, `kaggle kernels output rainm4/gemma4-exp044-x -p runs/EXP-044-x/`, then the section 6 analysis.

## 9. Results, arm X, 2026-11-06. Section 4's readings applied as written (design, endpoints and readings above are unchanged)

**Run.** `rainm4/gemma4-exp044-x` v1, COMPLETE. 8 of 8 tasks ran, ids exactly `experiments/cohorts/failed-edit-8.txt`, no kernel error. One task (fastapi_15661) ended with the harness's "Agent completed execution without calling submit_patch" after 24 calls, which is a normal agent exit, not a crash. Downloaded with `kaggle kernels output rainm4/gemma4-exp044-x -p runs/EXP-044-X/`; the bundle nests at `runs/EXP-044-X/runs/EXP-044-x/`, analysed there with `python tools/analyze_traces.py runs/EXP-044-X/runs/EXP-044-x --cap-minutes 8 --max-calls 28`; `summary.jsonl` is copied to `experiments/EXP-044/x/summary.jsonl`. **Measured GPU-h: kernel wall 1,291 s = 0.36 h** (last entry of `runs/EXP-044-X/gemma4-exp044-x.log`, which includes the notebook export tail; the 8 agent walls sum to 844 s). That is inside the 0.25 to 0.56 h range of section 2.4.

**Endpoints (counts over the 8 tasks).**

| # | Endpoint | Result |
|---|---|---|
| E1 | A, applied (at least one `edit_file` call with status ok; `n_edit_fail` below the `edit_file` count) | **6 of 8**: fastapi_14459, fastapi_14360, rich_3935, fastapi_13786, rich_3676, rich_3063. Not applied: fastapi_15661 (17 of 17 edit calls failed), fastapi_14873 (4 of 4) |
| E2 | N_e, at least one `edit_file` call | **8 of 8** |
| E3 | failed `edit_file` calls by class | 24 failed of 35 edit calls (11 ok). **All 24 are the harness's "old_string not found" error** (fastapi_15661 17, fastapi_14873 4, rich_3063 3); lost-argument (the "mandatory input parameters are not present" message) 0; non-unique or other 0. Reference, EXP-043 on the same 8 ids from the EXP-038 draw: 22, 5, 12. Check: per trace the count of "old_string not found" tool results equals `n_edit_fail`; the only extra text hit is in the model's own message, not a tool result |
| E4 | non-empty patches | **6 of 8** (empty: fastapi_15661, fastapi_14873) |
| E5 | calls and wall, recorded not read | `n_calls` 24, 9, 14, 6, 4, 15, 4, 16 (sum 92, max 24 of 28); wall 200.2, 91.8, 106.1, 54.3, 77.7, 180.0, 60.9, 73.3 s (mean 105.5 s); no task at the 28-call or 480 s cap; 3 compactions (fastapi_14459 once, fastapi_13786 twice); 0 nudge events |
| E6 | resolves, recorded not read | 0 of 8 (3 of the 8 are gated) |

**Row that fired, first match in order: row 4.** Row 0 no (no crash, tree ran); row 1 no (N_e 8 is above 5); rows 2 and 3 no (A is 6, not 4 or fewer); **row 4: A is 5 or more of 8, the bound is met, and it is not an effect (regression to the mean is not excluded): buy X0** (the unchanged tree, same 8 ids). X0 was pushed on this reading (section 8, "X0 push record" below). The share of failed calls typed "old_string not found" is 24 of 24, reported beside it as row 4 asks.

**Prediction check (blind, section 4), recorded not argued.** N_e 6 or more of 8: held (8). A 4 of 8, range 2 to 6: 6, the top of the range. Row probabilities: row 4 was 30%. Non-empty patches 5 of 8: 6. Resolves 0 to 1: 0. Failed calls by type (not-found about 12, lost-argument about 5, other about 10): not held, 24, 0, 0; the failures that remain are the not-found class only, 21 of them on two tasks. The EXP-043 non-unique and lost-argument failures on rich_3063, rich_3935 and others did not recur in this draw, which fits regression to the mean on a cohort chosen because one draw failed, so the class counts are not read against the line either.

**What this does and does not say.** A is 6 of 8 against 0 of 8 by construction in the reference draw; the section 2.3 confound stands in full. Two tasks (fastapi_15661, fastapi_14873) carry all 21 of the not-found failures that did not recover, and these were not-found tasks in the reference too. Whether the unchanged tree also applies 6 of 8 is exactly what X0 measures. No row licenses an upload or a claim move.

### X0 push record, 2026-11-06

Control arm X0 pushed with `kaggle kernels push -p notebooks/exp044_x0` at about 00:51 UTC on 2026-11-06 (19:51 local, UTC-5; read from the mtime of a file written just after the push), repo HEAD `522c561`, output `Kernel version 1 successfully pushed`. Kernel **`rainm4/gemma4-exp044-x0` v1**, status right after: RUNNING. Zip is `dist/EXP-038-e4b.zip`, sha256 `9de869bd2cd8853b72d653d06b9acef3e03794c8b588c26494435774dda11ac0`, the tree EXP-038 ran. This push is inside the user's approval of 2026-11-06 item 2 (X0 only if X applies an edit on 5 or more of 8). Stop rule: no re-run of a failed kernel without asking. Not waited on.

### 9.1 Results, arm X0 (the control), 2026-11-06. Section 4 rows 5 to 7 applied as written

**Run.** `rainm4/gemma4-exp044-x0` v1, COMPLETE. 8 of 8 tasks ran, ids exactly `experiments/cohorts/failed-edit-8.txt`, no kernel error, every task called `submit_patch`. Downloaded with `kaggle kernels output rainm4/gemma4-exp044-x0 -p runs/EXP-044-X0/`, analysed at `runs/EXP-044-X0/runs/EXP-044-x0/` with `python tools/analyze_traces.py ... --cap-minutes 8 --max-calls 28`; `summary.jsonl` is copied to `experiments/EXP-044/x0/summary.jsonl`. **Measured GPU-h: kernel wall 1,253.1 s = 0.348 h** (last entry of the kernel log, includes the notebook export tail; the 8 agent walls sum to 760.1 s). Inside the 0.25 to 0.56 h range of section 2.4 (point 0.38 h).

**Endpoints for X0 (counts over the 8 tasks).**

| # | Endpoint | X0 result |
|---|---|---|
| E1 | A, applied | **7 of 8**: fastapi_15661, fastapi_14873, fastapi_14459, fastapi_14360, fastapi_13786, rich_3676, rich_3063. Not applied: rich_3935 (4 of 4 edit calls failed) |
| E2 | N_e | **8 of 8** |
| E3 | failed `edit_file` calls by class | Counted from the tool results in the traces: 13 failed of 24 edit calls (11 ok). **11 are the harness's "old_string not found" error** (fastapi_15661 3, fastapi_14873 1, rich_3935 4, fastapi_13786 3), **2 are the lost-argument message** (fastapi_14873 2), non-unique or other 0. `summary.jsonl` shows `n_edit_fail` 12, one lower, because it counts 2 on fastapi_13786 where the trace holds 3 error results; this does not move A (that task has 3 ok edits either way) |
| E4 | non-empty patches | **7 of 8** (empty: rich_3935) |
| E5 | calls and wall, recorded not read | `n_calls` 7, 15, 8, 8, 7, 11, 5, 9 (sum 70, max 15 of 28); wall 63.4, 170.2, 61.0, 63.4, 86.8, 160.6, 39.8, 114.9 s (mean 95.0 s); no task at the 28-call or 480 s cap; 5 compactions (fastapi_14873 twice, fastapi_13786 once, rich_3063 twice); 0 nudge events |
| E6 | resolves, recorded not read | 0 of 8 |

**Paired per task, arm X against arm X0** (edit calls, with failed in brackets; trace counts for X0, `summary.jsonl` counts for X).

| Task | X edit calls (failed) | X applied | X0 edit calls (failed) | X0 applied |
|---|---|---|---|---|
| fastapi_13786 | 6 (0) | yes | 6 (3) | yes |
| fastapi_14360 | 1 (0) | yes | 2 (0) | yes |
| fastapi_14459 | 1 (0) | yes | 1 (0) | yes |
| fastapi_14873 | 4 (4) | **no** | 4 (3) | **yes** |
| fastapi_15661 | 17 (17) | **no** | 5 (3) | **yes** |
| rich_3063 | 4 (3) | yes | 1 (0) | yes |
| rich_3676 | 1 (0) | yes | 1 (0) | yes |
| rich_3935 | 1 (0) | **yes** | 4 (4) | **no** |

Applied in both arms: 5 (fastapi_13786, 14360, 14459, rich_3063, rich_3676). X only: 1 (rich_3935). X0 only: 2 (fastapi_14873, fastapi_15661). Resolves: 0 of 8 in both arms, recorded, not read.

**Row that fired, in order: row 6.** Rows 1 to 4 were settled by arm X (row 4 fired). Row 5 needs A_X of 5 or more with A_X minus A_0 of 3 or more and A_0 of 3 or fewer: A_X is 6, A_0 is 7, so A_X minus A_0 is minus 1 and A_0 is above 3; **not met**. **Row 6: A_0 (7) is at least A_X minus 1 (5): met.** Reading as written: the unchanged tree applies as many, regression to the mean explains row 4, **kill the line as specified.** Row 7 is not reached.

**What this licenses (section 5).** The screen's outcome is a kill. **No dev-48 arm is proposed**: row 5 did not fire, so the cost recomputation that section 5 reserves for a promotion is not made. The cohort was chosen because the unchanged tree failed every edit in one draw; a second draw of the same tree applied an edit on 7 of 8, so the reference of 0 of 8 was a draw, as defect 1 of section 7 warned.

**Prediction check (blind, section 4), recorded not argued.** A_0 about 3 of 8, range 1 to 5: **7, outside the range** (the blind estimate of regression to the mean was too low). Row 6 had no stated probability. Failed calls by type for X0 were not predicted separately. The classes that section 4 expected to persist (lost-argument, non-unique) appeared as lost-argument on one task (fastapi_14873, 2 calls) and non-unique on none. The not-found class fell from 22 in the EXP-038 draw to 11 here with no change to the prompt. Cost: X0 0.348 h against the 0.38 h point.

**Both kernels together.** 0.359 h (X) plus 0.348 h (X0) = 0.707 GPU-h, against the 0.5 to 1.1 h range (point 0.8 h) of section 2.4.

## Status

2026-11-06: **X0 analysed (section 9.1): ROW 6 FIRED, A_0 7 of 8 against A_X 6 of 8, the line is killed as specified, no dev-48 arm proposed, X0 kernel 0.348 h, X and X0 together 0.707 h.** Earlier, 2026-11-06: arm X analysed (section 9): **row 4 fired**, A 6 of 8, N_e 8 of 8, 24 of 24 failed calls typed not-found, kernel 0.36 h. **X0 pushed at about 00:51 UTC as `rainm4/gemma4-exp044-x0` v1, RUNNING.** Next, a separate job once `kaggle kernels status rainm4/gemma4-exp044-x0` says COMPLETE: `kaggle kernels output rainm4/gemma4-exp044-x0 -p runs/EXP-044-X0/`, then `python tools/analyze_traces.py` on the nested bundle with `--cap-minutes 8 --max-calls 28`, and apply rows 5 to 7 (A_X is 6, so row 5 needs A_0 at 3 or fewer and row 6 fires at A_0 of 5 or more).
