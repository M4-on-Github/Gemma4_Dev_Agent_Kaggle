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

### 8.1 Push

Committed as `2111524` (hygiene OK, 5 files) before any push; the pre-registration is `a6df3fb`. On 2026-11-08 `rainm4/gemma4-exp057-r1`: "Kernel version 1 successfully pushed", first status `RUNNING`. Then `rainm4/gemma4-exp057-r2`: "Kernel version 1 successfully pushed", first status `RUNNING`; at that push the only other kernel known to be running was r1 (EXP-056 r2 `COMPLETE`, no EXP-058 notebook directory yet), so at most 2 GPU kernels. Each pushed once, not re-run, not waited on. Analysis is a separate job once each status is COMPLETE; rows 0 and 1 read from r1 alone, the rest pooled.

### 8.2 Reference counts read after the push (dated 2026-11-08, no row changed)

EXP-056 r2 (same defective picker, 8 task-runs; EXP-056 section 9.2) was analysed after both EXP-057 kernels were pushed, so none of it entered the prompt or the readings. As references for the later analysis: Ad 4 of 8; 3 well-formed script calls, all returning the notice line; 1 model-side `SKILL_NOT_FOUND` from literal quote characters inside the string values; 2 of 8 task-runs typed the skill call as a shell command text (not counted in Ad); 0 `load_skill` calls; tool-free endings 2 of 8; the slimmer `traces/` copy omits `run_skill_script` calls, so count them in `official/traces/`. The blind prediction of section 4 (M_x 0 to 2 calls) stands as written.

## 9. Results

### 9.1 r1 alone (2026-11-08, screener; r2 not opened when this was written and committed)

Kernel `rainm4/gemma4-exp057-r1`, COMPLETE. Read as section 4 is written: rows 0 and 1 only, per-run thresholds. T and the pooled rows are not read here. Skill calls were counted in `official/traces/`. Per-task summary: `experiments/EXP-057/r1/summary.jsonl` (from `analyze_traces.py`).

**Cost.** Kernel-log span 981.7 s (vLLM up in 322.8 s) = **0.273 GPU-h** (section 2.4 predicted 0.28 to 0.30; EXP-056 r1 0.281).

| Task | wall s | calls | skill calls | edit_file calls (failed) | ending |
|---|---|---|---|---|---|
| requests_7309 | 18.1 | 0 | 0 | 0 | tool-free, 3 nudges, no submit |
| requests_7205 | 70.4 | 10 | 1 | 2 (1) | submit |
| fastapi_14448 | 47.8 | 5 | 1 | 1 (0) | submit |
| fastapi_14301 | 46.7 | 4 | 1 | 1 (0) | submit |
| httpx_3672 | 142.2 | 12 | 1 | 6 (4, 3 with lost arguments) | submit |
| fastapi_14605 | 109.5 | 11 | 1 | 6 (2) | submit |
| rich_3468 | 68.5 | 10 | 1 | 1 (0) | submit |
| rich_3006 | 38.4 | 5 | 1 | 1 (0) | submit |

**Row 0 (infrastructure): not fired.** S_s = 0 over 7 script calls: every result had status success, empty stderr, and one line of stdout. `error` is non-null in 0 of the 7 task-runs that made a tool call (the one non-null `error` is the tool-free ending, which does not count). The tree ran. **First-trace check passed:** S_p = 7 of 7, every script call returned a pick that is a pytest command naming one test file, none the notice line. This is the change from EXP-056, where every well-formed call returned the notice line.

**Row 1 (harm): not fired.** A_e = 7 of 8 (threshold below 6); mean wall 67.7 s (threshold above 140); capped 0 (threshold 3); longest 142.2 s, httpx_3672 (threshold 495 s); stray file in a patch 0 (threshold 2); malformed turns 0 (threshold 2). Patches non-empty 7 of 8; the one empty patch is the tool-free task-run.

**Recorded, not read.**

- **Ad = 7 of 8, S_c = 7.** Every call well formed: skill name `check-picker`, the script path `scripts/pick_check.py`, `args` an empty list (7 of 7 used the newest-modified-file fallback, so the pick is a recency pick, not a pick chosen from the model's own file names). **A_p = 7 of 8.**
- **M_x = 0** of every kind (wrong name, quote-wrapped values, rejected shape, empty args). `load_skill`, `list_skills`, `load_skill_resource` calls 0. Skill calls typed as text in a shell command 0.
- **Printed line then run** (exact program and test file, with `run_command`): 5 of 7 (fastapi_14448, fastapi_14605, requests_7205, rich_3006, rich_3468); fastapi_14301 and httpx_3672 submitted without running it (S_m 2 of 8 by that reading). Exit codes of the 5: 0 in four (all passed), 2 in fastapi_14605 (a collection error, an ImportError, raised inside a file the model had edited). In fastapi_14605 one `edit_file` and then `submit_patch` followed, so G = 0 by definition. Observation, recorded and not read: the statement that the check's ImportError traced to is still present in the final patch (grep count 1), so a failing module may have shipped despite G = 0 by the rule as written; row 6 reads G as defined, so this is for the pooled reading to note.
- **V1** (literal rule, a python or pytest command after the last successful edit) about 5 of 8 (corrected in 9.2 to 4 of 8: in fastapi_14605 the edit after the failing check succeeded, so no check follows the last successful edit); **G = 0**; T not read here.
- **Tool-free endings 1 of 8** (requests_7309), against 2, 2 and 1 in EXP-056 r1, EXP-056 r2 and EXP-055.
- **Mean wall 67.7 s, longest 142.2 s.** Nudges 3, all on the tool-free task-run. Resolves 1 of 8 (rich_3006), recorded and not read.

**Blind prediction against outcome (r1).** Ad 5 to 7 of 8: actual 7, top of the range. S_s 0: actual 0. M_x 0 to 2: actual 0. A_p 4 to 6: actual 7, above. V1 5 to 7: actual about 5. G 0: actual 0. Mean wall 60 to 100 s: actual 67.7. Tool-free 1 to 2: actual 1. T 3 to 5: not read.

**What r1 licenses.** Rows 0 and 1 did not fire; r1 is recorded and rows 2 to 6 wait for r2. The mechanism works as built: the fixed picker runs in the harness and returns real picks, and the model calls it correctly (the EXP-056 `SKILL_NOT_FOUND` quote-wrapping did not recur in 7 of 7). Whether the picks are the right check (T) is not read. Caveat for the pooled reading: r2 is the same zip over the same 8 tasks, so the 16 task-runs are two draws over 8 clusters, not 16 independent tasks.

### 9.2 r2 and the pooled reading over 16 task-runs (2026-11-08, screener; opened only after 9.1 was committed at `f6bea23`)

Kernel `rainm4/gemma4-exp057-r2`, COMPLETE, same zip and same 8 tasks. Per-task summary: `experiments/EXP-057/r2/summary.jsonl`. Skill calls counted in `official/traces/`. Run settings in the downloaded `eval_config.yaml`: 28 tool calls, 8 minutes, 240 s per command.

**Cost.** Kernel-log span 1101.0 s (vLLM up in 330.9 s) = **0.306 GPU-h** (r1 0.273; both runs 0.579 GPU-h; section 2.4 predicted about 0.6).

| Task | wall s | calls | skill calls | edit_file calls (failed) | pick run? exit codes of the pytest runs | ending |
|---|---|---|---|---|---|---|
| requests_7309 | 23.2 | 0 | 0 | 0 | none | tool-free, 3 nudges, no submit |
| requests_7205 | 53.1 | 9 | 1 | 1 (0) | not run | submit |
| fastapi_14448 | 45.1 | 6 | 1 | 1 (0) | run, 0 | submit |
| fastapi_14301 | 45.8 | 5 | 1 | 1 (0) | run, 0 | submit |
| httpx_3672 | 146.5 | 14 | 1 | 8 (4) | run three times, 2, 2, 2 | submit |
| fastapi_14605 | 186.6 | 29 | 4 | 11 (3) | run five times, all 2 | submit, 29 calls against a cap of 28 |
| rich_3468 | 108.6 | 10 | 1 | 2 (0) | run, 0 | submit |
| rich_3006 | 30.4 | 5 | 1 | 2 (1, arg loss) | run, 0 | submit |

**r2 process counts.**

- **Ad 7 of 8, S_c 10, S_s 0, M_x 0 of every kind, S_p 10 of 10, A_p 7 of 8.** All 10 calls well formed (name `check-picker`, path `scripts/pick_check.py`, `args` an empty list); all 10 results status success with empty stderr and one pytest pick on stdout, no notice line. fastapi_14605 called the script 4 times, each time returning the same pick; the other six called once. `load_skill` and `list_skills` calls 0; skill calls typed as text in a shell command 0.
- **Pick then run:** 6 of 7 ran the printed line with `run_command` (all but requests_7205). In requests_7205 the model's own text said the check command had been executed and that it was assuming the result, then submitted: the print of the pick was taken for a run (a mechanism observation, 1 case; the same phrase was searched for in the two r1 task-runs that did not run the pick and is absent there).
- **Last-check exit codes after the last edit:** 0 in four (fastapi_14448, fastapi_14301, rich_3468, rich_3006); 2 in httpx_3672 (a collection error, AttributeError class) and in fastapi_14605 (a collection error, NameError class, raised at a line of a file the patch changes); none in requests_7205 and requests_7309.
- **V1** 6 of 8 (the six that ran a pytest after the last successful edit). **G = 1**: fastapi_14605 ends on a check whose output names a NameError at a patched file, then a file read, then the submit, with no edit between. httpx_3672 ends on exit 2 with an AttributeError, which is not in the G list as written (SyntaxError, IndentationError, NameError, ImportError, ModuleNotFoundError). Earlier in fastapi_14605 the same picker line was run after edits and returned ImportError and NameError collection errors in turn; the model edited, re-called the script, and ran the same line again; it spent 29 calls, one above the call cap, and shipped.
- **Wall mean 79.9 s, longest 186.6 s** (fastapi_14605). A_e 7 of 8 (non-empty patches 7 of 8). Capped on time 0; on calls 1 (fastapi_14605). Past 495 s 0. Stray file in a patch 0. Malformed turns 0. Identical-repeat calls 5 (httpx_3672 2, fastapi_14605 3). Nudges 3, all on requests_7309.
- **Tool-free endings 1 of 8** (requests_7309, the same task as in r1), against 2, 2 and 1 in the last three runs. **Resolves 1 of 8** (rich_3006, the same task as r1), recorded and not read.
- **Correction to 9.1:** V1 in r1 on the literal rule is 4 of 8 (not about 5): in fastapi_14605 the edit after the failing check was successful, so no check follows the last successful edit.

**Pooled counts (16 task-runs).**

| count | r1 | r2 | pooled |
|---|---|---|---|
| Ad (task-runs with a well-formed skill call) | 7 | 7 | **14 of 16** |
| S_c (script calls) | 7 | 10 | 17 |
| S_s (script-side errors) | 0 | 0 | **0** |
| M_x (model-side tool errors) | 0 | 0 | 0 |
| S_p (picks that are not the notice line) | 7 of 7 | 10 of 10 | 17 of 17 |
| A_p (task-runs with at least one pick) | 7 | 7 | 14 of 16 |
| calls with empty `args` | 7 | 10 | 17 of 17 |
| printed line then run with `run_command` | 5 of 7 | 6 of 7 | 11 of 14 |
| **T** (last check after the last applied edit is a pytest, exit 0 or 1) | **4** | **4** | **8 of 16** |
| V1 | 4 | 6 | 10 of 16 |
| G | 0 | 1 | 1 |
| A_e | 7 | 7 | 14 of 16 |
| mean wall (s) | 67.7 | 79.9 | 73.8 |
| longest wall (s) | 142.2 | 186.6 | 186.6 |
| capped (time / calls) | 0 / 0 | 0 / 1 | 0 / 1 |
| tool-free endings | 1 | 1 | 2 |
| resolved (not read) | 1 | 1 | 2 |
| GPU-h | 0.273 | 0.306 | 0.579 |

T by task-run, the 8 that are T: fastapi_14448, rich_3468 and rich_3006 in both runs (6), requests_7205 in r1 only, fastapi_14301 in r2 only. The 8 that are not T: requests_7309 twice (tool-free); the pick printed but not run, 3 (fastapi_14301 and httpx_3672 in r1, requests_7205 in r2); the pick run with exit 2 as the last check, 3 (fastapi_14605 in r1 and in r2, httpx_3672 in r2). Exit 2 here is a collection error. In the two fastapi_14605 cases the error was raised in a file the patch changes; in httpx_3672 r2 it is an AttributeError raised at the test file's own import line, with a cause I did not trace. Those three are not T as defined whatever the cause.

**Row reading, section 4, pooled over 16, first match.**

- **Row 0 (infrastructure): no.** S_s 0 over 17 calls; `error` non-null in 0 of the 14 task-runs with tool calls (limit more than 4); the tree ran; the first-trace check passed over both runs (S_p 17 of 17).
- **Row 1 (harm): no.** A_e 14 of 16 (limit below 12); mean wall 73.8 s (limit above 140); capped 1 task-run on calls and 0 on time (limit 6); none past 495 s; stray file in 0 patches (limit 4); malformed turns 0 (limit 4).
- **Row 2 (not adopted): no.** Ad 14 of 16 (the row needs 8 or fewer).
- **Row 3 (adopted but not a better check): fires. T = 8 of 16, the row's bound is 9 or fewer.** Under the registered readings the package is **dropped**. The reference is 6 of 16 (EXP-055 3 of 8, doubled); the pooled draw sits two above it, inside what 8 clusters over two draws can move, and the row does not ask whether it is above the reference.
- Rows 4 to 6 are not reached.

**Blind prediction against outcome (pooled).** Ad 10 to 14 of 16: actual 14, the top of the range. T 7 to 10 of 16: actual 8, inside it, row 3 as the most likely row said ("row 3 or 4"). r2's own counts sit inside the r1 prediction ranges except A_p (actual 7, above 4 to 6) and mean wall (79.9, inside 60 to 100).

**Why T stayed at 8, in own words, recorded not read.** The mechanism works (S_s 0, S_p 17 of 17, 14 of 16 task-runs called it correctly, M_x 0): the EXP-056 failure is gone. The ceiling on T is behaviour after the pick: 3 of 14 did not run the printed line (one believed it had), and 3 ran it, got a collection error as the last check, and shipped (two of the three in a file the patch changes). The picker cannot help in the second group because it names a test file only; it says nothing about whether the model's edit broke an import. No resolve difference is read (2 of 16, both rich_3006).

**What this licenses.** Dropped as written (row 3): `check-picker` is not kept for the loop and is not promoted to a dev-48 arm or an LB draw. It can be decided only as far as the readings go: n = 8 twice with clustered tasks, resolves not read. A fix or a re-run needs the user's word and is not proposed here.

## Status

**r1 and r2 COMPLETE and ANALYSED 2026-11-08** (sections 9.1 and 9.2). r1: rows 0 and 1 not fired, 0.273 GPU-h. Pooled over 16: row 0 no (S_s 0, first-trace check passed), row 1 no, row 2 no (Ad 14 of 16), **row 3 fires, T 8 of 16, dropped as written**; M_x 0, G 1, V1 10, 0.579 GPU-h both runs, resolves 2 of 16 (not read). Pre-registered at `a6df3fb`, built at `2111524`. Zip `e402d6dd...6362e6`.
