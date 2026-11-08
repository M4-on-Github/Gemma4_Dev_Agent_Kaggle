# EXP-057 — E4B edit loop, round 4: the check-picker fixed (run-time workspace root, both argument shapes, newest-file fallback, exact call shape in the prompt), smoke-8, two runs over one zip

**Date:** 2026-11-08
**Type:** smoke-8 screen, one arm (`f`), two runs (`r1`, `r2`) of the same zip, about 0.28 to 0.30 L4x4-h each (point; conditional worst case about 1.24 h each, section 2.6). Pushed under the user's word of `knowledge/user-decisions.md` (2026-11-08 ~21:25 UTC entry: round 4 approved, raw-model loop continues, inside the day's 4.0 GPU-h ceiling).
**Cohort:** smoke-8
**Ladder:** L2, after L1 (the EXP-056 r1 traces, zero GPU, and the harness source on disk). Round 4 of the E4B edit loop (`knowledge/lessons-e4b-loop.md`). EXP-056 row 0 was an infrastructure result (the picker never saw the workspace), so round 3's question is still unanswered; this round re-asks it.
**Pre-registered:** this file, the tree, the tests and the README row are committed before the zip is built and before any push. Sections 3 and 4 are written blind and are not revised; results are appended as a new section.
**Serves:** the E4B small-model line (S-014 scored 3/58); class D and G of the EXP-053 diagnosis; the "the check tests nothing" finding of EXP-055 section 9.1.
**Relates:** EXP-056 (round 3, same package, row 0), EXP-055 (round 2, T_ref 3 of 8), EXP-053, EXP-045, EXP-033 and EXP-038 (base set).
**Tags:** [V] verified in source on disk or by a test run here; [I] inference; [H] hand judgement from tool order and exit codes.
**Numbering:** EXP-058 is the experimenter's (adapter bug test); this file takes EXP-057.

## 1. Why this, now

**EXP-056 r1 (V, section 9.1 of that file).** 6 script calls in 8 task-runs. Two were model-side tool errors (`SKILL_NOT_FOUND` for a skill name other than the declared one; `INVALID_ARGUMENTS` for `args` given as a list together with `positional_args`). Four returned the picker's notice line, among them two well-formed calls with workspace paths. T was 0 of 8, V1 2 of 8. The picker's root was the constant `/workspace`; the Kaggle subprocess sandbox has a temp workspace instead, so the script saw an empty tree.

**Where the workspace is, from the harness source (V, all in `data/src/` on disk).**

- `adk_eval_core/adk_eval_core/sandbox/base.py:201-210`: `AdkSandboxCodeExecutor` writes the wrapper as `.adk_exec_<id>.py` into `sandbox.work_dir`, runs `python3 <that path>` through `sandbox.run_command`, then deletes it. The wrapper's directory, which python puts first on `sys.path`, is the workspace.
- `swegemma/swegemma/sandbox/subprocess.py:485-498` (`exec`): the command runs with `cwd=workspace_dir` and an environment whose `PYTHONPATH` is `str(workspace_dir)`; `adk_eval_core/.../subprocess_sandbox.py:38-54` (`build_sanitized_env`) applies that `extra_env` over a short allowlist. Lines 441-448 rewrite the literal `/workspace` only inside the command string, never inside a Python file, which is the EXP-056 defect.
- `google_adk/google/adk/tools/skill_toolset.py:626-634,658`: the wrapper records `_orig_cwd` in a local variable, then `os.chdir` into a `TemporaryDirectory` that holds only the skill's files, and runs the script with `runpy.run_path`; line 706 restores the directory afterwards. So the script's current directory is that temp directory, but `PYTHONPATH` and `sys.path[0]` still name the workspace.
- `subprocess.py:56-57`: the default sandbox's work dir is the temp workspace path, else `/workspace` (the Docker form was not read; the scorer's sandbox may differ, so the literal `/workspace` and the current directory stay in the candidate list as late fallbacks).

**What the tool carries (V).** `skill_toolset.py:724-774` (declaration): `skill_name`, `file_path` required; `args` is an object or a list of strings; `short_options` an object; `positional_args` a list of strings. `776-820`: any of `short_options` or `positional_args` together with a list `args` is `INVALID_ARGUMENTS` (810-820, a dict `args` is fine with both). `638-661`: argv is the list as given, or `--key value` per dict item, `-k value` per short option, then `--` and the positional items. `swegemma/harness/agent_runner.py:97-129`: a one-item list for `skill_name` or `file_path` is coerced to a string, any other non-string is `INVALID_ARGUMENTS`; `158-181`: an exception inside a skill tool comes back as `{status: error, error_type, error}`; `skill_toolset.py:525-526,537-569`: stderr with no stdout is `status: error`, a script exit is `EXECUTION_ERROR`.

## 2. Design

### 2.1 The tree

`experiments/EXP-057/candidate-f/` is `experiments/EXP-056/candidate-s/` with these changes only, as **one package, "the same check-picker, fixed"** (all of (a) to (d) are about the script or the way the model is told to call it):

- (a) **Workspace root.** `scripts/pick_check.py` builds a candidate list: the `PYTHONPATH` entries, then the `sys.path` entries (library directories, the script's own directory and the skill's temp directory are skipped), then the literal `/workspace`, then the current directory. The root is the first candidate that holds one of the named edited files, else the first with any `.py` file. No constant is used as the only root.
- (b) **Argument shapes.** Every `.py` piece of every token is read as an edited path, so the list form, `--key value` (also a repr of a list), `-k value`, and the `--` form all work; braces and parentheses are now stripped too. A `/workspace/` prefix, the real root prefix and `./` are stripped.
- (c) **Empty or unusable arguments.** With no usable edited path the script takes the newest-modified non-test, non-dot `.py` files of the workspace: at most 3, all within 300 s of the newest. No subprocess, no git. Extension beyond the lead's text, same lever: the fallback also applies when the paths given do not exist or are test files (EXP-056's notice-on-bad-path case), because the same defect class (a path the script cannot use) should end in a pick.
- (d) **Prompt.** Section 4, first bullet only: "Send exactly three fields: `skill_name` set to `check-picker` (the full name, both words), `file_path` set to `scripts/pick_check.py`, and `args` set to one list of strings holding the source paths you edited, for example `["pkg/module.py"]`. Never send `positional_args` or `short_options`. If you do not remember the paths, send `[]` and the script uses the files changed most recently." The rest of section 4 is byte for byte EXP-056's. The prompt was written from EXP-056 r1's call shapes; EXP-056 r2's were not read first.
- `SKILL.md` body updated to the same call shape (it is read only if the model loads the skill, which the prompt forbids). `agent.yaml`: one dated comment line. `configs/sampling.yaml` and `eval_config.yaml` are byte for byte EXP-056's (diff empty).

`diff -ru experiments/EXP-056/candidate-s experiments/EXP-057/candidate-f` (2026-11-08): `agent.yaml` +1 comment line; `prompts/system.md` one hunk, the first bullet of section 4; `SKILL.md` one line; `pick_check.py` the changes above (a new `candidate_roots`, `pick_root`, `strip_root`, `newest_sources`, `choose`, and a `main` that sets the root at run time); no other file differs.

### 2.2 Local tests (e)

`experiments/EXP-057/test_pick_check.py`, 20 tests, synthetic trees only (no repo content), the workspace always a temp directory that is not at `/workspace`; all 20 pass (`python -m pytest experiments/EXP-057/test_pick_check.py`). They run the script (1) in process with the current directory elsewhere and `PYTHONPATH` naming the workspace; (2) as a child process that reproduces the harness wrapper (a file in the workspace, started with the workspace as cwd and `PYTHONPATH` set, then `chdir` to a temp dir and `runpy.run_path`), with and without `PYTHONPATH`; (3) directly with the workspace as cwd and no `PYTHONPATH`. They cover the list, dict, short-option and `--` shapes, absolute and `/workspace/`-prefixed paths, empty and unusable arguments, the recency window, dot and test files not chosen, the notice line on a tree with no `.py`, the EXP-056 selection cases (name match, import match, missing third-party import skipped, indented import ignored, flat and namespace layouts), and a text check that the script has no process, network or write calls. They show the script runs and selects where the harness puts it; they say nothing about whether the model calls it.

### 2.3 Measures, defined now

Task-run = one task in one run; 8 per run, 16 pooled. T, V1, G, A_e, P, W are EXP-056's definitions (its section 2.5), reproduced here:

- **T (target):** the last `run_command` whose text contains `python` or `pytest`, after the last applied `edit_file` and before `submit_patch`, is a `pytest` invocation (`pytest` or `python -m pytest`) with exit 0 or 1, or a `python -c "import ..."` of an edited module with exit 0, or exit 1 with a traceback naming an edited file. Not T: exit 2, 4 or 5, the notice line, a `grep` or `git diff`, an import error naming only a package. [H] **T_ref (EXP-055): 3 of 8; EXP-056 r1: 0 of 8.**
- **V1:** a `python` or `pytest` command after the last successful edit, before `submit_patch` (reference 7 of 8, EXP-055; 2 of 8, EXP-056 r1). **G:** a check output names a SyntaxError, IndentationError, NameError, ImportError or ModuleNotFoundError in a patched file and no `edit_file` follows before the submit (EXP-055: 0 of 8). **A_e, P, W:** applied-edit task-runs, non-empty patches, wall mean and longest, cap hits.
- **Ad:** task-runs with at least one `run_skill_script` call whose arguments name `check-picker` and `scripts/pick_check.py`. **S_c:** script calls. **S_m:** task-runs whose last check is not the printed line.
- **S_x, now split.** **S_s, script-side error (row 0):** a `run_skill_script` result carrying a traceback or any text on stderr, `error_type`, no stdout, an exit of the script itself (`EXECUTION_ERROR`), or any error code other than the model-side three below (`REGISTRY_ERROR`, `NO_CODE_EXECUTOR`, `UNSUPPORTED_SCRIPT_TYPE`), or a ToolNotFoundError. **M_x, model-side tool error (counted process endpoint, not row 0):** `SKILL_NOT_FOUND`, `INVALID_ARGUMENTS`, `SCRIPT_NOT_FOUND`.
- **S_p:** script calls that returned a pick that is not the notice line (the line does not start with `python -c "print(`); **A_p:** task-runs with at least one.
- **First-trace check:** over the run (r1 alone: r1; pooled: r1 and r2), at least one script call that did not error must have returned a pick (S_p of 1 or more). If there is at least one non-error call and S_p is 0, that is row 0. With no script call at all the check cannot be applied and is recorded.
- Recorded, not read: tool-free endings (a task-run with 0 tool calls; EXP-056 r1 had 2 of 8, EXP-055 1 of 8); empty-argument calls and call shapes; `load_skill`, `list_skills`, `load_skill_resource` calls; last-check exit codes; nudges; malformed turns (skill-tool calls are not malformed); stray file in the patch; resolves.

### 2.4 Cost

Overhead 430 to 500 s plus about 55 to 85 s per task plus the script call: **about 0.28 to 0.30 h per run (EXP-056 r1 measured 0.281), 0.6 h for both**; conditional worst case about 1.24 h per run (every task at the 495 s cap), not expected. Day ledger on 2026-11-08: about 2.18 of 4.0 h spent (with EXP-056 r2), so both runs bring it to about 2.8, before EXP-058's about 0.35. `pack_submission.py --skip-budget-gate --allow-warnings` is used: 8 minutes is above the 4.5-minute packing gate (the EXP-033 and EXP-056 situation) and the validator warns on skill scripts (VERIFY(Q1), now answered: the skill path runs in the harness); a screen is never uploaded. The validator rejects `__pycache__` in the source tree, so the zip is packed from a clean copy of the committed files under `out/`.

### 2.5 Cohort and two runs

smoke-8 (`experiments/cohorts/smoke-8.txt`), strict subset of dev-48. `r1` and `r2` are two kernels over one zip (`notebooks/exp057_r1`, `notebooks/exp057_r2`, `EXP_ID` `EXP-057-r1`, `-r2`). At most 2 GPU kernels run at once, counting the experimenter's EXP-058 kernel; r2 is pushed when a slot is free.

## 3. Endpoints, fixed in advance

| # | endpoint | definition |
|---|---|---|
| E1 | T | 2.3, pooled over 16; reference 6 of 16 (EXP-055 3 of 8, doubled) |
| E2 | Ad, S_c, S_s, M_x, S_p, A_p, S_m | 2.3; the mechanism |
| E3 | G | 2.3 |
| E4 | V1 | 2.3 |
| E5 | A_e, P, W | edits, patches, mean and longest wall, cap hits |
| E6 | skill-tool calls, last-check exit, call shapes, tool-free endings | recorded |
| E7 | nudges, malformed, stray file, resolves | recorded, resolves not read |

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

**r1 alone (8 task-runs), rows 0 and 1 only, per-run thresholds.**

- **Row 0, infrastructure.** Any S_s, or `error` non-null in more than 2 of the 8 task-runs that made at least one tool call (a tool-free ending is recorded and does not count here), or the tree does not run, or the first-trace check fails (2.3). A mechanism result: no T reading, no re-run without the user's word. M_x does not fire it.
- **Row 1, harm.** A_e below 6, or mean wall above 140 s, or 3 or more capped, or any task past 495 s, or a stray file in 2 or more patches, or malformed turns in 2 or more.
- Neither fires: r1 is recorded (counts, M_x, S_p) and rows 2 to 6 wait for r2. If r2 is never run, no T reading is made and the result is "r1 only, mechanism read".

**Pooled over `r1` and `r2` (16 task-runs). First match, in order.**

- **Row 0, infrastructure.** Any S_s, or `error` non-null in more than 4 of the 16 task-runs that made at least one tool call, or the tree does not run, or the first-trace check fails over both runs. No reading, no re-run without the user's word.
- **Row 1, harm: dropped.** A_e below 12 of 16, or mean wall above 140 s, or 6 or more task-runs capped, or any task past 495 s, or a stray file in 4 or more patches, or malformed turns in 4 or more task-runs.
- **Row 2, not adopted: dropped.** Ad of 8 or fewer of 16. (M_x is counted; a package the model cannot call correctly is dropped as the model calls it, and the M_x counts say whether the shape or the idea failed.)
- **Row 3, adopted but not a better check: dropped.** T of 9 or fewer of 16.
- **Row 4, partly better: no decision, keep-base.** T of 10 to 12 of 16.
- **Row 5, the check tests the edit nearly everywhere with no failing module shipped: kept for the loop.** T of 13 or more of 16, G of 0 or 1, row 1 not fired. Not a dev-48 result: a kept edit counts only after an LB draw or a dev-48 arm (user's word). **The dev-48 endpoint if promoted:** the share of the 48 ids whose last check tests the edit (T, same definition) and G, paired against EXP-038, plus mean wall and calls per task (the script costs one call).
- **Row 6, tests the edit, but a failing module still went out: no decision, keep-base.** T of 13 or more and G of 2 or more.

**Blind prediction (written before any EXP-057 trace).** r1: Ad 5 to 7 of 8; S_s 0; M_x 0 to 2 calls; A_p 4 to 6 of 8; T 3 to 5 of 8; V1 5 to 7; G 0; mean wall 60 to 100 s; tool-free endings 1 to 2 of 8. Pooled: Ad 10 to 14 of 16; T 7 to 10 of 16 (most likely row 3 or 4). This is a bound on compliance and on check quality (EXP-020 section 4), not a mean; the round 2 and round 3 predictions both overshot compliance.

## 5. What this does and does not license

**It can kill the package** (rows 1, 2 and 3), **or keep it for the loop** (row 5), and a keep promotes it only to an LB draw or a dev-48 arm with the endpoint in row 5. Rows 0, 4 and 6 decide nothing. It cannot show a higher resolve rate (n = 8 twice, resolves not read; a better last check does not address the class C and A failures).

## 6. Exact commands

```
cp -r (files only) experiments/EXP-056/candidate-s -> experiments/EXP-057/candidate-f      # then the edits of section 2.1
diff -ru experiments/EXP-056/candidate-s experiments/EXP-057/candidate-f
python -m pytest experiments/EXP-057/test_pick_check.py -q
cp (candidate-f files) out/exp057_pack/                                                    # no __pycache__
python tools/validate_submission.py out/exp057_pack --strict
python tools/pack_submission.py --src out/exp057_pack --out dist/EXP-057-f.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed dist/EXP-057-f.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-057-r1"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp057_r1/kaggle_eval_l4x4.ipynb
(the same with EXP-057-r2 and notebooks/exp057_r2; kernel-metadata.json copied from notebooks/exp056_r1, only id and title changed, written after each build)
```

Analysis (separate jobs): `kaggle kernels output rainm4/gemma4-exp057-r1 -p runs/EXP-057-r1`, `python -I -X utf8 tools/analyze_traces.py` on the nested directory with `--cap-minutes 8 --max-calls 28`, then sections 3 and 4 as written, row 0 first. `n_undeclared_tool` of 1 or more is expected on every task-run that calls the script and is not read as malformed.

## 7. Defects and limits of this pre-registration

1. **T is a hand count** from tool order, exit codes and a command-text rule; the model may run the printed line with a change (S_m counts that).
2. **The package is the fixed script plus the changed first bullet**; a change in Ad cannot be split between the call-shape wording and the script. The fix to the script cannot change Ad, only A_p and T.
3. **The newest-file fallback has two weak spots:** a scratch file the model writes into the workspace is the newest source, and when no edit was made the workspace files tie on modification time, so up to 3 arbitrary files are used. Neither is read; the output is still one valid line.
4. **The scorer's sandbox may not be the subprocess one** (the Docker form was not read); the candidate list ends with the literal `/workspace` and the current directory for that reason, and the first-trace check is the guard.
5. **The importability filter is still unverified in the sandbox interpreter** (EXP-056 section 7 item 4): the sandbox's own environment may not see the packages the local one does.
6. **Clustering:** the 16 task-runs are 8 tasks twice; a task-specific effect counts twice.
7. **The tool-free endings are not controlled.** EXP-056 r1 had 2 of 8 (two tasks that made no call at all); they cap A_e at 6 and T at 6 per run, so the blind prediction of T allows for them.
8. **Seen before:** EXP-056 r1's traces were read before this prompt and script were written; EXP-056 r2's traces were not, and the lead allowed its call-shape counts as reference if they came first. None was used.
9. **Stray untracked directories** (`experiments/EXP-053-candidate-tmp/`, `experiments/EXP-032-t4-tmp/`, the `.keep` files, `out/exp056_dry/`) are not part of this experiment and are not committed.
10. **A cached `__pycache__`** appeared in the candidate directory when the tests ran (git-ignored); the zip is built from a clean copy.

## 8. Built

Built 2026-11-08 after the pre-registration commit `a6df3fb` (tree, tests, readings, README row). Sections 1 to 7 are unchanged except one line-range citation in section 1 (`810-814` to `810-820`, a numbering correction made before the commit).

- **Clean pack source:** `out/exp057_pack/` (6 files copied from `experiments/EXP-057/candidate-f/` with `cp`, no `__pycache__`; the files are byte for byte the committed ones). `validate_submission.py --strict` on it: one error, the 18.00 h packing gate, plus 2 warnings.
- **Validate / pack:** `pack_submission.py --src out/exp057_pack --out dist/EXP-057-f.zip --skip-budget-gate --allow-warnings`: 6 reachable files, `RESULT: VALID (0 errors, 3 warnings)`, 7.2 KiB. The 3 warnings: skill scripts rely on `run_skill_script` (VERIFY(Q1)), the packing gate (`120 x (8 + 1.0) min = 18.00 h`), the 240 s timeout. Members: `agent.yaml`, `configs/sampling.yaml`, `eval_config.yaml`, `prompts/system.md`, `skills/check-picker/SKILL.md`, `skills/check-picker/scripts/pick_check.py`. **Zip sha256 `e402d6dd68338b098858d5baf6d9270f32cd2722bb4bb9ec89860b72346362e6`** (`sha256sum` agrees). Screen build, never uploaded.
- **Notebooks:** `notebooks/exp057_r1/kaggle_eval_l4x4.ipynb` (`EXP_ID = "EXP-057-r1"`) and `notebooks/exp057_r2/kaggle_eval_l4x4.ipynb` (`EXP_ID = "EXP-057-r2"`); both `RUN_GOLD_CONTROL = False`, `N_TASKS = 8`, `MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"`, `TASK_IDS` = the 8 smoke ids, 9,804 base64 characters each, same zip.
- **`kernel-metadata.json`** in each directory: the EXP-056 r1 file with only `id` (`rainm4/gemma4-exp057-r1`, `rainm4/gemma4-exp057-r2`) and `title` changed (`diff` confirms), written after each build (the builder does not create it).
- **Kernel ids:** `rainm4/gemma4-exp057-r1`, `rainm4/gemma4-exp057-r2`.

## Status

**BUILT 2026-11-08, not yet pushed.** Pre-registered at `a6df3fb`. Zip `e402d6dd...6362e6`. r1 push and r2 push are recorded in section 8.1 when done; analysis is a separate job.
