# EXP-055 — E4B edit loop, round 2: the last call before `submit_patch` must be a one-command check, and a broken edited file is repaired, on smoke-8

**Date:** 2026-11-08
**Type:** smoke-8 screen, one arm (`v`), about 0.28-0.35 L4x4-h expected (point 0.30, conditional worst case about 1.24 h, section 2.4). **Built, then pushed under the standing approval** of `knowledge/user-decisions.md` (2026-11-08 entry, df193f3): a smoke-8 round inside the 4.0 GPU-h day ceiling.
**Cohort:** smoke-8
**Ladder:** L2, after L1 (the base-set diagnosis of EXP-053 section 1 plus the EXP-053 traces, zero GPU). Round 2 of the E4B edit loop (`knowledge/lessons-e4b-loop.md`); EXP-053 (round 1) was dropped at row 3, so the tree starts from EXP-033's, not from EXP-053's.
**Pre-registered:** this file, the tree, the zip's recorded sha and the notebook are committed before the push. Sections 3 to 5 are written blind and are not revised; results are appended as a new section.
**Serves:** the E4B small-model line (S-014 scored 3/58); class D and G of the EXP-053 diagnosis.
**Relates:** EXP-045 (the reproduce-before-submit bullet, row 5, whose `/tmp` finding this arm follows), EXP-053 (round 1, row 3), EXP-033 and EXP-038 and EXP-052 (base set).
**Tags:** [V] verified in a trace or a check run here, [I] inference, [H] hand judgement (a hand count from tool order and step ids).
**Numbering:** EXP-054 is the experimenter's (copy-LoRA run); this file takes EXP-055.

## 1. Why this, now

**Two process facts from the base set (EXP-053 section 1, extended by the EXP-053 traces), counts and step ids only.**

- **D, no command run after the last applied edit.** In the 24 non-resolving base runs 12 were flagged D (EXP-033 2, EXP-038 4, EXP-052 4, EXP-045 2); EXP-053 adds 2 of its 6 non-resolving tasks: fastapi_14448 (calls in order: run_command, read_file, read_file, edit_file, submit_patch; the edit is call 4 and the submit is call 5) and httpx_3672 (the last applied edit is at step 13, then `submit_patch` with no command between). Further D moments: fastapi_14605 in EXP-038 (steps 9 to 13 failed edits, then the submit) and in EXP-045, requests_7205 in EXP-052 (applied at step 12, no run). The prompt already says "run at most one focused check", and 14 of the 30 non-resolving runs listed above still skipped it.
- **G, a check showed the edited module failing and the run submitted anyway.** EXP-045 httpx_3672: the check at step 7 reported a SyntaxError in the edited module and `submit_patch` followed at step 8. The prompt licenses it: section 4's fourth bullet says "if it fails because of ... import errors ... ignore it", and a SyntaxError or an import error caused by the edit is not pre-existing breakage. 1 of 32 base task-runs.
- **The `/tmp` finding (EXP-045 section 9.2).** `write_file` to `/tmp/...` is refused as a path outside the workspace (requests_7309 step 6, rich_3468 step 11, rich_3006 step 8); so the check must be a command (`python -c`, one test file) with no scratch file. EXP-045's own check shape (write a script, run it) is why row 5 fired and says nothing against a one-command check.

**Cue, this candidate (V).** The run ends on an edit with no command after it (D), or on a failing check that points into the edited file (G). The tasks: fastapi_14448 (EXP-053), httpx_3672 (EXP-053 and EXP-045), fastapi_14605 (EXP-038, EXP-045), requests_7205 (EXP-052): 4 tasks, at least 2 required. D is a risk for tasks that resolve by luck too: it is a process fact about 14 of 30 non-resolving runs, with no claim that a check turns a wrong fix into a right one (class C, 12 of 24, is not touched).

**Candidate L (edit the definition site) is named and not built.** Its cue is fastapi_14448 (edit in the caller file at EXP-033 step 5, EXP-038 step 7, EXP-052 step 13) and rich_3468 (EXP-033 step 6, a different file from the fix). But the last two runs on fastapi_14448 (EXP-045 step 10, EXP-053) landed in the gold-patch file with no bullet at all, so the per-run chance of the target tasks landing right with no edit is already 2 of 5 for fastapi_14448 and 4 of 5 for rich_3468; the best reading n = 8 can give would be "dropped" on a wrong-file landing that has a 3 in 5 chance anyway, and no "kept" row beyond chance. A screen whose answer is mostly the base rate is not bought here; it is available if the lead wants it, with those numbers as its limit.

## 2. Design

### 2.1 The tree

`experiments/EXP-055/candidate-v/` is `experiments/EXP-033/candidate-e4b/` (the S-014 / EXP-038 tree: 8 minutes, 28 calls, `timeout_seconds` 240, `model: gemma-4-e4b-it-qat-w4a16-ct`) with three small changes to `prompts/system.md` section 4, the same variable (the post-edit check is required and a broken edited file is repaired). The text is in `experiments/EXP-055/v_insert.md`:

1. **Added bullet** after the first bullet: "Your last tool call before `submit_patch` must be that check, run after your last edit. Run it as one command with no scratch file: the named test file, or `python -c "import <module>"` for the module you changed. If the output shows a `SyntaxError`, `IndentationError`, `NameError` or `ImportError` that points into a file you edited, fix that file with one `edit_file`, run the same command once more, then submit."
2. **Deleted** "import errors," from the fourth bullet (it contradicts the new bullet).
3. **Deleted** "or you skipped it" from the fifth bullet (it contradicts "must").

Everything else, `agent.yaml`, `configs/sampling.yaml`, `eval_config.yaml`, is byte for byte EXP-033's. Repo-agnostic (no repo, library or package word; no network, subprocess, `pip` or URL word). The fallback "If `get_status` shows less than 90 seconds remaining, call `submit_patch` immediately" is kept, so the check yields to the clock. Lever (a), prompt only; no skill, no script.

### 2.2 Measures, defined now

- **V1** (target): tasks of 8 in which a `run_command` whose command text contains `python` or `pytest` follows the last successful `edit_file` and precedes `submit_patch` [H, from tool order in the trace]. Reference upper bounds (a task counts as having its check if it resolved, which is generous): 6, 4, 4, 6, 6 of 8 for EXP-033, EXP-038, EXP-052, EXP-045, EXP-053 (8 minus D in the non-resolving tasks). So no reference exceeds 6.
- **G**: tasks in which a check's output names a `SyntaxError`, `IndentationError`, `NameError`, `ImportError` or `ModuleNotFoundError` in a file that the patch changes and no `edit_file` follows before the submit. Reference: 1 of 32 task-runs.
- **Rp** (repair, recorded): checks that showed such an error in an edited file and were followed by an `edit_file`.
- **A_e / P**: tasks with an applied edit, non-empty patches (references 6, 8, 7, 8, 8).
- **W**: mean and longest wall (references 56.9, 78.3, 82.5, 54.4, 66.8 s mean; longest 84 to 150.5 s); calls per task; cap hits.
- Also recorded, not read: nudges, malformed turns, stray file in patch, scratch writes refused, resolves.

### 2.3 Cohort

smoke-8 (`experiments/cohorts/smoke-8.txt`), strict subset of dev-48; pairing against the five references above is free.

### 2.4 Cost

Kernel overhead 430 to 500 s plus about 55 to 85 s per task (EXP-045 0.248 h, EXP-053 0.281 h by kernel log span), plus up to two more calls per task for the check: **0.28 to 0.35 h, point 0.30 h**. **Conditional worst case about 1.24 h** (every task at the 495 s cap), not expected: no reference task ran past 150.5 s. Day ledger: 4.0 GPU-h ceiling, loop share about 2.8 h, EXP-045 0.248 and EXP-053 0.281 spent, so about 2.27 h before this kernel and about 1.97 h after it.

`pack_submission.py --skip-budget-gate --allow-warnings` is used: 8 minutes is above the 4.5-minute packing gate (the EXP-033 situation); a screen is never uploaded.

## 3. Endpoints, fixed in advance

| # | endpoint | definition |
|---|---|---|
| E1 | V1 | 2.2, the target; read against the maximum of the references (6 of 8) |
| E2 | G | 2.2, must be 0 |
| E3 | A_e and P | applied-edit tasks and non-empty patches |
| E4 | W | mean and longest wall, cap hits |
| E5 | Rp, calls per task | recorded |
| E6 | nudges, malformed, stray file, resolves | recorded, resolves not read |

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

First match, in order.

- **Row 0, infrastructure.** Any `error` string in more than 2 of 8 rows, or the tree does not run, or a stage the harness cannot start: a mechanism result, no reading, no re-run without the user's word.
- **Row 1, harm: dropped.** A_e below 6 of 8 (EXP-033's floor), or mean wall above 140 s, or 3 or more tasks capped, or any task past 495 s, or a stray file in 2 or more patches, or malformed turns in 2 or more tasks.
- **Row 2, not enforced: dropped.** V1 of 6 or fewer of 8 (no reference exceeded 6; the bullet changed nothing the base rate does not already give).
- **Row 3, partly enforced: no decision, keep-base.** V1 = 7.
- **Row 4, enforced everywhere with no failing module shipped: kept for the loop.** V1 = 8 and G = 0 and row 1 not fired. The next round starts from this tree. It is not a dev-48 result and a kept edit counts only after an LB draw or a dev-48 arm (user's word); the endpoint a dev-48 arm would carry: tasks with a check after the last edit and G on all 48 ids, paired against EXP-038, plus the mean wall.
- **Row 5, check ran but a failing module still went out: no decision, keep-base.** V1 = 8 and G of 1 or more (the repair half is not enforced).

Rp, resolves and the rest: recorded, not read. **Blind prediction:** V1 = 7 (range 6 to 8), G = 0, mean wall 65 to 85 s; the most likely rows are 3 and 4. This is a bound on compliance (EXP-020 section 4), not a mean: 8 of 8 against a reference maximum of 6 is the only outcome n = 8 can read as more than the base rate.

## 5. What this licenses

**It can kill the bullet** (rows 1 and 2) or **keep it for the loop** (row 4); rows 3 and 5 decide nothing. It cannot show that a check raises the resolve rate (n = 8, resolves not read; the check does not address the 12 of 24 non-resolving runs that are class C or the 8 that are class A). A kept edit counts only after an LB draw or a dev-48 arm.

## 6. Exact commands

```
cp -r experiments/EXP-033/candidate-e4b experiments/EXP-055/candidate-v      # then the three edits of section 2.1
diff -ru experiments/EXP-033/candidate-e4b experiments/EXP-055/candidate-v
python tools/validate_submission.py experiments/EXP-055/candidate-v --strict
python tools/pack_submission.py --src experiments/EXP-055/candidate-v --out dist/EXP-055-v.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed dist/EXP-055-v.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-055-v"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp055_v/kaggle_eval_l4x4.ipynb
kaggle kernels push -p notebooks/exp055_v
```

Analysis (a separate job): `kaggle kernels output rainm4/gemma4-exp055-v -p runs/EXP-055-v`, `python -I -X utf8 tools/analyze_traces.py` on the nested directory with `--cap-minutes 8 --max-calls 28`, then sections 3 and 4 as written, row 0 first.

## 7. Defects and limits of this pre-registration

1. **V1 and G are hand counts from tool order and a command-text rule** (`python` or `pytest` in the command); a `git diff` or `grep` after the edit does not count, a `python -c` that does not touch the edited module does. Same rule for every reference, but the references are upper bounds, since a resolving task is counted as checked without reading its order.
2. **Three hunks in one prompt, one variable.** A change in V1 cannot be split between the "must" wording and the deleted "or you skipped it".
3. **A check can cost calls and seconds.** The tasks that end at 4 or 5 calls (EXP-053) gain one more. Row 1 bounds the wall at 140 s.
4. **Prior from EXP-045:** a different check shape (write a script, run it) fired row 5; this one is a single command and its compliance is the question, not the value of reproducing.
5. **G is rare** (1 of 32); a G = 0 in 8 is near the base rate. It is only an exclusion in row 4 and 5.
6. **Seen before:** the base counts and the EXP-053 traces were read before the bullet was written; the bullet is written from them, sections 3 and 4 after it and before any arm output.
7. **Stray directory:** `experiments/EXP-053-candidate-tmp/` exists untracked from a mistaken copy (round 1); it is not part of this experiment and is not committed.

## 8. Built

Built 2026-11-08 with the section 6 commands. Sections 1 to 7 are unchanged.

- **Diff, tree against baseline:** `diff -ru experiments/EXP-033/candidate-e4b experiments/EXP-055/candidate-v`: one file, `prompts/system.md`, one hunk `@@ -23,10 +23,11 @@`: one bullet added after the first bullet of section 4, "import errors," deleted from the fourth, "or you skipped it" deleted from the fifth.
- **Validate:** `--strict` gave 4 files, `RESULT: INVALID (1 errors, 1 warnings)`: the packing gate (`120 x (8 + 1.0) min = 18.00 h`) and the 240 s timeout warning, both the EXP-033 situation.
- **Pack:** `--skip-budget-gate --allow-warnings`: 4 reachable files, `RESULT: VALID (0 errors, 2 warnings)`, 2.6 KiB. **Zip sha256 `9d9b19143701361c9424c27540959746fc1c3323b5276b2e5123cd45dd8b124f`.** Screen build, never uploaded.
- **Notebook:** `notebooks/exp055_v/kaggle_eval_l4x4.ipynb`: `EXP_ID = "EXP-055-v"`, `RUN_GOLD_CONTROL = False`, `N_TASKS = 8`, `MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"`, `TASK_IDS` = the 8 smoke ids; 3,524 base64 characters.
- `notebooks/exp055_v/kernel-metadata.json`: copied from `notebooks/exp053_r/`, only `id` (`rainm4/gemma4-exp055-v`) and `title` (`gemma4-exp055-v`) changed.
- **Kernel id: `rainm4/gemma4-exp055-v`.**

### 8.1 Push

Committed as `9601dd0` (hygiene OK, 9 files) before the push. Before it, no other kernel of the team was known to be running (EXP-053 COMPLETE; `notebooks/exp054_copylora/` held no `kernel-metadata.json`, so no EXP-054 kernel had been pushed; `kaggle kernels list` is not an allowed command for this agent). `kaggle kernels push -p notebooks/exp055_v` on 2026-11-08 after that commit: "Kernel version 1 successfully pushed", kernel `rainm4/gemma4-exp055-v`, first status `RUNNING`. Pushed once, not re-run. Analysis is a separate job once the status is COMPLETE.

## Status

2026-11-08: **PUSHED** (kernel `rainm4/gemma4-exp055-v`, version 1, RUNNING at first check; standing approval of `knowledge/user-decisions.md` 2026-11-08), analysis pending. Zip `9d9b1914...8b124f`.
