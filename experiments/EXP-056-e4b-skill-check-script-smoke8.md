# EXP-056 — E4B edit loop, round 3: a skill script chooses the last check, on smoke-8, two runs over one zip

**Date:** 2026-11-08
**Type:** smoke-8 screen, one arm (`s`), two runs (`r1`, `r2`) of the same zip, about 0.30 L4x4-h each (point; conditional worst case about 1.24 h each, section 2.5). **Built and, for r1 only, pushed under the standing approval** of `knowledge/user-decisions.md` (2026-11-08 ~19:15 UTC entry: one more loop round, "sure let's rerun one more time for the loop"). r2 is committed unpushed; the lead dispatches its push when a kernel slot is free (EXP-054 v2 holds the other slot).
**Cohort:** smoke-8
**Ladder:** L2, after L1 (the EXP-055 traces, zero GPU). Round 3 of the E4B edit loop (`knowledge/lessons-e4b-loop.md`); rounds 1 and 2 (EXP-053, EXP-055) both ended keep-base, so the tree starts from EXP-033's.
**Pre-registered:** this file, the tree, the zip's recorded sha and both notebooks are committed before the push. Sections 3 and 4 are written blind and are not revised; results are appended as a new section.
**Serves:** the E4B small-model line (S-014 scored 3/58); class D and G of the EXP-053 diagnosis, and the new "the check tests nothing" finding of EXP-055 section 9.1.
**Relates:** EXP-055 (round 2, row 3: the bullet is obeyed 7 of 7, 4 of 7 checks tested nothing), EXP-053, EXP-045, EXP-033 and EXP-038 (base set).
**Tags:** [V] verified in a trace, in source on disk, or by a check run here; [I] inference; [H] hand judgement (a hand count from tool order and step ids).
**Numbering:** EXP-054 is the experimenter's (copy-LoRA run), EXP-055 the last round; this file takes EXP-056.

## 1. Why this, now

**Round 2's lesson (EXP-055 section 9.1, V).** The sentence "your last tool call before `submit_patch` must be that check" was obeyed by 7 of 7 task-runs that made calls (V1 = 7 of 8), and G was 0. But of the 7 checks, 4 tested nothing: httpx_3672 (exit 4), fastapi_14605 (exit 5), rich_3468 (exit 5), each a wrong path or working directory in the model's own command, and fastapi_14301 (exit 2, a collection error there before the edit; the model ran bare `pytest tests/`). Three checks gave a usable signal (requests_7309, requests_7205, rich_3006, all `pytest tests/...` exit 1) [H]. More wording on whether to run a check is not the next gain; the model chooses the command badly.

**Cue, this candidate (V).** The 4 tasks above: 4 of the 7 compliant checks were not tests. At least 2 required; 4 found.

**The lever.** Move the choice of command out of the model: a script, called by the model, reads the workspace and prints exactly one command line; the model runs it as its last call. The script runs nothing itself (it is pure file reading), so it cannot import the edited module with side effects, start a test run, or hang.

**Source facts (V, read in `data/src/` on disk this session).**

- Declaring `skills:` in `agent.yaml` makes the harness build an ADK `SkillToolset` appended to the plain tools. It adds four tools, `list_skills`, `load_skill`, `load_skill_resource`, `run_skill_script`, and a fixed paragraph (about 700 characters) is injected into every request telling the model to call `load_skill` first.
- `run_skill_script` writes the skill's files into a `TemporaryDirectory` and does `os.chdir` into it, then `runpy.run_path` with `sys.argv = ['scripts/pick_check.py', ...]`. The current directory is therefore not the workspace; the script hard-codes `/workspace`.
- The sandbox executor writes `.adk_exec_<id>.py` into `/workspace`, runs `python3`, and removes it in a `finally`. Stderr with empty stdout, or a nonzero exit, is returned as `status: "error"`. The script always exits 0 and always prints one stdout line, so any `error` is a crash and is row 0.
- A `run_skill_script` call counts as one of the 28 tool calls (the executor calls the budget check with `count_tool_call=True`).
- `args` as a list gives plain tokens, as a dict gives `--key value`, `positional_args` inserts a `--` token; the script collects every `.py` piece out of whatever tokens arrive.
- The pytest paths of the EXP-055 checks that ran tests (requests_7309, requests_7205, rich_3006) were workspace-relative `tests/...` and gave exit 1 [H], so `run_command`'s working directory is `/workspace` and the script's relative output is runnable.

## 2. Design

### 2.1 The tree

`experiments/EXP-056/candidate-s/` is `experiments/EXP-033/candidate-e4b/` (8 minutes, 28 calls, `timeout_seconds` 240, `model: gemma-4-e4b-it-qat-w4a16-ct`) with, as **one package, "the last check, chosen by a script"**:

1. `agent.yaml`: a `skills:` list with one entry, `skills/check-picker` (with a dated comment). First time any tree declares a skill.
2. `skills/check-picker/SKILL.md` (frontmatter `name: check-picker`, a description, a four-line body) and `skills/check-picker/scripts/pick_check.py`.
3. `prompts/system.md` section 4: EXP-055's check bullet in revised form (carried, not a separate lever): the first bullet now says to call `run_skill_script` once after the last edit with the edited paths, and not to call `load_skill` first; a new second bullet says the last call before `submit_patch` must be the printed command run with `run_command` exactly as printed, and keeps EXP-055's repair clause (SyntaxError, IndentationError, NameError or ImportError pointing into an edited file: one `edit_file`, the same command once more, then submit). "import errors," is deleted from the fixture bullet and "or you skipped it" from the `submit_patch` bullet, as in EXP-055.

`diff -ru experiments/EXP-033/candidate-e4b experiments/EXP-056/candidate-s` (recorded 2026-11-08):

```
agent.yaml:      +3 lines after the tools list (comment, "skills:", "  - skills/check-picker")
prompts/system.md, one hunk @@ -22,11 +22,12 @@:
- - After the edit, run at most one focused check: `pytest tests/test_file.py -k test_name -q` or `python -c "..."`.
+ - After your last edit, call `run_skill_script` once with `skill_name` set to `check-picker`, `file_path` set to `scripts/pick_check.py` and `args` set to a list of the source paths you edited, for example `["pkg/module.py"]`. Do not call `load_skill` first. The script reads the workspace and prints one command line.
+ - Your last tool call before `submit_patch` must be that printed command, run with `run_command` exactly as printed, after your last edit. Do not write a scratch file or choose another check. If the output shows a `SyntaxError`, `IndentationError`, `NameError` or `ImportError` that points into a file you edited, fix that file with one `edit_file`, run the same command once more, then submit.
  (unchanged: Never run bare pytest ...; the assertion bullet)
- - If it fails because of missing fixtures, import errors, or pre-existing breakage, ignore it. ...
+ - If it fails because of missing fixtures or pre-existing breakage, ignore it. ...
- - Call `submit_patch` after that, even when the local check is red or you skipped it. ...
+ - Call `submit_patch` after that, even when the local check is red. ...
Only in candidate-s: skills/
```

`configs/sampling.yaml` and `eval_config.yaml` are byte for byte EXP-033's.

### 2.2 What the script does

`pick_check.py`, stdlib only, no subprocess, no os.system, no network, no writes, repo-agnostic (no repo, library or package word). It always ends normally and prints exactly one line.

1. Reads the `.py` tokens of its arguments (list, dict or `--` shapes), maps each to a workspace-relative path (a `/workspace/` prefix or `./` is stripped; absolute, `..` and non-file paths and test files are dropped).
2. Derives, for each edited source file, its stem and its dotted import name (climbing `__init__.py` directories; a bare `src` or `lib` prefix is dropped).
3. Walks `/workspace` for `test_*.py` and `*_test.py` (dot directories and build directories skipped; capped at 8,000 py files) and ranks them by name match (equal name 100, stem inside the test name 60, test name inside the stem 40, stem equal to a directory name 30) and then by how the test file imports the module (dotted import 50, `from <parent> import <stem>` 45, dotted text anywhere 30, flat name 40), ties to the shortest path.
4. **Importability filter:** a candidate test whose top-level imports (or its `conftest.py` chain's) name a package this interpreter cannot find is skipped, so a test that cannot even be collected is not chosen.
5. Prints `python -m pytest -q -x <best test>`; with no usable test, `python -c "import <dotted>"` for the first edited module; with no usable path, a `python -c "print('check-picker: ...')"` notice line, which is still runnable.

### 2.3 Confound, accepted and counted

The harness's fixed skill paragraph (about 700 characters) is added to every request, and four tools, three of which this prompt never uses, are added to the tool list. A small model may call `load_skill` (the paragraph says it must) or `list_skills`. That is part of the package and cannot be separated at n = 8; `load_skill`, `list_skills` and `load_skill_resource` calls are counted (section 3) and a prompt-length effect on the F-form failure rate is named in section 7.

### 2.4 Local desk check of the picker (not a result about the model)

The picker was run offline on the 8 smoke-8 snapshots with the files the EXP-055 patches edited (a local interpreter, not the sandbox). It returned a test file for 7 of 7 edit sets (requests_7309 and requests_7205 `tests/test_utils.py`; fastapi_14301 `tests/test_multipart_installation.py`; httpx_3672 `tests/test_parsers.py`; fastapi_14605 `tests/test_empty_router.py`; rich_3468 `tests/test_live.py`; rich_3006 `tests/test_repr.py`) and the notice line for fastapi_14448 (no edit in its patch). The importability filter changed none of the 8 picks on this machine, so it is **unverified until the kernel runs**: nothing here says it avoids a collection error like fastapi_14301's. Eleven synthetic-tree tests of the script (`experiments/EXP-056/test_pick_check.py`, no repo content) pass. These show the script runs and selects; they say nothing about whether the model calls it.

### 2.5 Measures, defined now

Task-run = one task in one run; 8 per run, 16 pooled.

- **T (target)**, the "last check really tests the edit": the last `run_command` whose command text contains `python` or `pytest`, after the last applied `edit_file` and before `submit_patch`, counts when (a) it is a `pytest` invocation (`pytest` or `python -m pytest`) with exit 0 or 1 (tests were collected and ran), or (b) it is a `python -c "import ..."` of an edited module with exit 0, or exit 1 with a traceback naming an edited file. It does not count when the exit is 2, 4 or 5 (collection error, usage error, no tests ran), when it is the notice line, a `grep` or `git diff`, or when an import error names only a package and not an edited file. [H, from tool order and exit codes.] **Reference T_ref, EXP-055: 3 of 8** (requests_7309, requests_7205, rich_3006); 6 of 16 as a pooled equivalent.
- **Ad (adoption):** task-runs with at least one `run_skill_script` call whose arguments name `check-picker` and `scripts/pick_check.py`. Of 16.
- **S_c:** script calls, total. **S_x:** script calls that returned `status: error`, a ToolNotFoundError, or that crashed. **S_m:** task-runs whose last check is not the printed line (mismatch).
- **V1:** as in EXP-055 (a `python` or `pytest` command after the last successful edit, before `submit_patch`). Reference 7 of 8.
- **G:** a check output names a SyntaxError, IndentationError, NameError, ImportError or ModuleNotFoundError in a patched file and no `edit_file` follows before the submit. Reference 1 of 32, 0 of 8 in EXP-055.
- **A_e, P, W:** applied-edit tasks, non-empty patches, wall (mean and longest) and cap hits; EXP-055 gave 7, 7, mean 75.4 s, longest 166.5 s.
- Also recorded, not read: `load_skill`, `list_skills` and `load_skill_resource` calls; the last check's exit code; nudges; malformed turns (skill-tool calls are not malformed); stray file in the patch; resolves.

### 2.6 Cost

Overhead 430 to 500 s plus about 55 to 85 s per task, plus the script call and the printed command (one more call than EXP-055): **about 0.30 h per run, 0.60 h for both**; conditional worst case about 1.24 h per run (every task at the 495 s cap), not expected. Day ledger on 2026-11-08: 0.971 of 4.0 h spent before this file, plus EXP-054 v2's 0.98 h worst case, plus r1 0.30 h: about 2.25 h; r2 later brings it to about 2.55 h.

`pack_submission.py --skip-budget-gate --allow-warnings` is used: 8 minutes is above the 4.5-minute packing gate (the EXP-033 situation), and the validator warns on skill script files (VERIFY(Q1)); a screen is never uploaded.

### 2.7 Cohort and two runs

smoke-8 (`experiments/cohorts/smoke-8.txt`), strict subset of dev-48, so pairing against EXP-033, EXP-038, EXP-052, EXP-045, EXP-053 and EXP-055 is free. `r1` and `r2` are two kernels over the same zip (`notebooks/exp056_r1`, `notebooks/exp056_r2`, `EXP_ID` `EXP-056-r1`, `-r2`). Pooling is by one rule over 16 task-runs; the runs share 8 tasks, so the 16 are clustered (section 7).

## 3. Endpoints, fixed in advance

| # | endpoint | definition |
|---|---|---|
| E1 | T | 2.5, the target, pooled over 16; reference 6 of 16 |
| E2 | Ad, S_c, S_x, S_m | 2.5; the mechanism |
| E3 | G | 2.5 |
| E4 | V1 | 2.5; reference 7 of 8 |
| E5 | A_e, P, W | edits, patches, mean and longest wall, cap hits |
| E6 | skill-tool calls, last-check exit | recorded |
| E7 | nudges, malformed, stray file, resolves | recorded, resolves not read |

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Pooled over `r1` and `r2` (16 task-runs). First match, in order.

- **Row 0, infrastructure.** Any S_x (a `run_skill_script` that errored, a ToolNotFoundError, or a script crash), or `error` non-null in more than 4 of 16 task-runs, or the tree does not run: a mechanism result, no reading, no re-run without the user's word. (`error` on a task that never called a tool, the fastapi_14448 form of EXP-055, counts toward the 4.)
- **Row 1, harm: dropped.** Pooled A_e below 12 of 16, or mean wall above 140 s, or 6 or more task-runs capped, or any task past 495 s, or a stray file in 4 or more patches, or malformed turns in 4 or more task-runs.
- **Row 2, not adopted: dropped.** Ad of 8 or fewer of 16 (the model does not call the script half the time; the package changes nothing).
- **Row 3, adopted but not a better check: dropped.** T of 9 or fewer of 16 (the pooled reference is 6; +3 is inside the clustering noise).
- **Row 4, partly better: no decision, keep-base.** T of 10 to 12 of 16.
- **Row 5, the check tests the edit nearly everywhere with no failing module shipped: kept for the loop.** T of 13 or more of 16 and G of 0 or 1 and row 1 not fired. T has a practical ceiling near 14 (a tool-free F-form run and a collection error cap two task-runs), so 13 is nearly all. Not a dev-48 result: a kept edit counts only after an LB draw or a dev-48 arm (user's word). **The dev-48 endpoint if promoted:** the share of the 48 ids whose last check tests the edit (T, same definition) and G, paired against EXP-038, plus mean wall and calls per task (the script costs one call).
- **Row 6, tests the edit, but a failing module still went out: no decision, keep-base.** T of 13 or more and G of 2 or more.

**If only r1 has landed:** a per-run reading, the EXP-055 thresholds on 8 task-runs, for rows 0 and 1 only (any S_x or `error` in more than 2 of 8; A_e below 6, mean wall above 140 s, 3 or more capped, any past 495 s, a stray file in 2 or more, malformed in 2 or more). Rows 2 to 6 wait for r2. If r2 is never run, no T reading is made and the result is recorded as "r1 only, mechanism read".

Ad, S_c, S_m, skill-tool calls, resolves and the rest: recorded, not read except as stated. **Blind prediction:** Ad about 12 to 14 of 16, T about 8 to 11 (most likely row 3 or 4), G = 0, mean wall 70 to 100 s, S_x = 0. This is a bound on compliance and on check quality (EXP-020 section 4), not a mean.

## 5. What this licenses

**It can kill the package** (rows 1, 2 and 3 do; row 0 is a mechanism result and decides nothing) **or keep it for the loop** (row 5), and a keep promotes it only to an LB draw or a dev-48 arm with the endpoint in row 5 (T and G on the 48 ids, paired against EXP-038, plus wall). Rows 4 and 6 decide nothing. It cannot show a higher resolve rate (n = 8 twice, resolves not read; the check does not address the class C and class A failures).

## 6. Exact commands

```
cp -r experiments/EXP-033/candidate-e4b experiments/EXP-056/candidate-s      # then the edits of section 2.1
diff -ru experiments/EXP-033/candidate-e4b experiments/EXP-056/candidate-s
python tools/validate_submission.py experiments/EXP-056/candidate-s --strict
python tools/pack_submission.py --src experiments/EXP-056/candidate-s --out dist/EXP-056-s.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed dist/EXP-056-s.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-056-r1"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp056_r1/kaggle_eval_l4x4.ipynb
python tools/build_notebook.py ... --set EXP_ID='"EXP-056-r2"' ... --out notebooks/exp056_r2/kaggle_eval_l4x4.ipynb
kaggle kernels push -p notebooks/exp056_r1
kaggle kernels push -p notebooks/exp056_r2      # later, by the lead, when a slot is free
```

Analysis (separate jobs): `kaggle kernels output rainm4/gemma4-exp056-r1 -p runs/EXP-056-r1` (and `-r2`), `python -I -X utf8 tools/analyze_traces.py` on the nested directory with `--cap-minutes 8 --max-calls 28`, then sections 3 and 4 as written, row 0 first. `n_undeclared_tool` of 1 or more is expected on every task-run that calls the script (the skill tool is not in `FREE_TOOLS`) and is not read as malformed.

## 7. Defects and limits of this pre-registration

1. **T is a hand count** from tool order, exit codes and a command-text rule. The model may run the printed line with a change; S_m counts that.
2. **One package, several things at once:** the script, the carried EXP-055 bullet, the added skill tools and the fixed skill paragraph. A change in T cannot be split between them (section 2.3).
3. **The injected paragraph says the model MUST call `load_skill` first;** the prompt says not to. A model that follows the paragraph spends one more call per task; `load_skill` calls are counted and Row 1 bounds the wall.
4. **The importability filter is unverified** (section 2.4: a no-op locally). The kernel interpreter and the harness's per-task sandbox are not the local one; fastapi_14301's pre-existing collection error may be chosen again.
5. **The picker's tie-break is the shortest path among equal import scores.** For a widely imported module (fastapi_14605, `fastapi/exceptions.py` to `tests/test_empty_router.py`) the pick is a file that imports the module, not necessarily the most relevant one. T counts it as a test that ran; the limit is recorded, the script is not changed for it.
6. **Clustering:** the 16 task-runs are 8 tasks twice. A task-specific effect (for example fastapi_14448's tool-free F-form failure, or fastapi_14301's collection error) counts twice. A pooled count is not a sample of 16 independent tasks.
7. **Call counting:** the script call is one of the 28; a task near the cap spends a call on it. EXP-055's calls per task were 4, 4, 0, 7, 10, 10, 5, 3.
8. **F-form base rate:** EXP-055 had one tool-free run (fastapi_14448, 0 calls) in 8 and none in about 46 earlier E4B traces; the longer request (the skill paragraph and four tools) may change it. It is read only through Row 0 (`error` in more than 4 of 16).
9. **Seen before:** the EXP-055 traces were read before this prompt was written; the prompt and the script are written from them, sections 3 and 4 after both and before any arm output.
10. **Stray untracked directories** from earlier rounds (`experiments/EXP-053-candidate-tmp/`, `experiments/EXP-053/r/.keep`, `experiments/EXP-055/v/.keep`) are not part of this experiment and are not committed.
11. **Desk check scope:** the 7 of 7 picks of section 2.4 were run on a local interpreter and the EXP-055 edit sets; they test the picker, not the model's use of it.

## 8. Built

Built 2026-11-08 after the pre-registration commit `8e40ffc` (tree, readings and README row). Sections 1 to 7 are unchanged.

- **Validate / pack:** `pack_submission.py --skip-budget-gate --allow-warnings`: 6 reachable files, `RESULT: VALID (0 errors, 3 warnings)`, 5.7 KiB. The 3 warnings: skill scripts rely on `run_skill_script` (VERIFY(Q1), the ToolNotFoundError report), the packing gate (`120 x (8 + 1.0) min = 18.00 h`), and the 240 s timeout (the EXP-033 situation). Members: `agent.yaml`, `configs/sampling.yaml`, `eval_config.yaml`, `prompts/system.md`, `skills/check-picker/SKILL.md`, `skills/check-picker/scripts/pick_check.py` (both skill files are in the zip). **Zip sha256 `1a591945dc582d00d86bd64e91f2a545155b2617612180da230fa01c96a33126`.** Screen build, never uploaded.
- **Notebooks:** `notebooks/exp056_r1/kaggle_eval_l4x4.ipynb` (`EXP_ID = "EXP-056-r1"`) and `notebooks/exp056_r2/kaggle_eval_l4x4.ipynb` (`EXP_ID = "EXP-056-r2"`); both `RUN_GOLD_CONTROL = False`, `N_TASKS = 8`, `MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"`, `TASK_IDS` = the 8 smoke ids, 7,844 base64 characters each, same zip.
- **`kernel-metadata.json`** in each directory: copied from `notebooks/exp055_v/`, only `id` (`rainm4/gemma4-exp056-r1`, `rainm4/gemma4-exp056-r2`) and `title` changed, written after each build (the builder overwrites it).
- **Kernel ids:** `rainm4/gemma4-exp056-r1`, `rainm4/gemma4-exp056-r2`.

### 8.1 Push

Committed as `9a51a11` (hygiene OK, 5 files) before the push; the pre-registration is `8e40ffc`. `kaggle kernels push -p notebooks/exp056_r1` on 2026-11-08: "Kernel version 1 successfully pushed", kernel `rainm4/gemma4-exp056-r1`, first status `RUNNING`. Pushed once, not re-run, not waited on. r2 (`rainm4/gemma4-exp056-r2`) is built and committed, not pushed: EXP-054 v2 holds the other kernel slot. Analysis is a separate job once each status is COMPLETE; the T reading needs both runs.

**r2 push (lead's job, 2026-11-08 after 20:31 UTC, r1 and EXP-054 v2 both COMPLETE):** `kaggle kernels push -p notebooks/exp056_r2`: "Kernel version 1 successfully pushed", kernel `rainm4/gemma4-exp056-r2`, first status `RUNNING`. Pushed once under the standing approval for round 3's two runs, not re-run, not waited on.

---

## 9. Results

### 9.1 r1 alone (2026-11-08, screener; r2 not read)

Sections 1 to 8 are unchanged. Applied: the "if only r1 has landed" paragraph of section 4, rows 0 and 1 only, at the per-run thresholds as written. Source: `rainm4/gemma4-exp056-r1` version 1, output downloaded to `runs/EXP-056-r1/` (nested one level), `tools/analyze_traces.py --cap-minutes 8 --max-calls 28`; per-task rows committed at `experiments/EXP-056/r1/summary.jsonl`.

**Cost.** Kernel log span 1010 s (last entry 1010.97 s; vLLM up at 465.9 s after a 348.5 s start) = **0.281 GPU-h**. Agent phase about 528 s.

**Per-task (8 ids).**

| Task | calls | wall s | edit applied | patch | script calls | resolved |
|---|---|---|---|---|---|---|
| requests_7309 | 0 | 16.0 | no | empty | 0 | no |
| requests_7205 | 11 | 67.4 | yes | yes | 2 | no |
| fastapi_14448 | 6 | 84.3 | yes | yes | 0 | no |
| fastapi_14301 | 6 | 32.7 | yes | yes | 1 | yes |
| httpx_3672 | 11 | 113.6 | yes | yes | 1 | no |
| fastapi_14605 | 0 | 15.5 | no | empty | 0 | no |
| rich_3468 | 16 | 152.8 | yes | yes | 1 | no |
| rich_3006 | 6 | 38.3 | yes | yes | 1 | yes |

Resolved 2 of 8 (recorded, not read). Mean wall 65.1 s, longest 152.8 s, no task capped, none past 495 s, `error` in 2 of 8 (both the tool-free endings below), stray file in 0 patches, malformed turns 0.

**Row 0 (infrastructure, r1 alone): FIRED as written, through the S_x clause.** S_x = 2 of 6 script calls returned `status: error` (an error object with an error code): one `SKILL_NOT_FOUND` (fastapi_14301) and one `INVALID_ARGUMENTS` (requests_7205). `error` was 2 of 8, which is not more than 2, so that clause did not fire; the tree ran. A mechanism result: it decides nothing about the package, and the T reading is not made from r1.

**Row 1 (harm, r1 alone): did not fire.** A_e = 6 (threshold: below 6), mean wall 65.1 s (above 140), capped 0 (3 or more), longest 152.8 s (past 495), stray file 0 (2 or more), malformed 0 (2 or more). A_e is 6 not 7 because both tool-free endings made no edit.

**Process counts (recorded, not read).**

- Ad = 5 of 8 task-runs called the script (blind prediction: 12 to 14 of 16, i.e. 6 to 7 of 8). S_c = 6 calls (requests_7205 made two). S_x = 2.
- Of the 4 script calls that did not error: 2 were made with no arguments (httpx_3672 and rich_3006) and 2 with an argument list that carried workspace paths (rich_3468, and the second call in requests_7205); all 4 returned the notice line, the picker's "no pick" output.
- S_m: not countable as designed (no check line was ever printed).
- `load_skill`, `list_skills`, `load_skill_resource` calls: 0 across the 8 traces (the injected paragraph's "MUST `load_skill` first" was not followed, as the prompt asked).
- Tool-free endings: 2 (requests_7309 and fastapi_14605, 0 calls, 3 nudges, no `submit_patch`, error "completed without calling submit_patch"). No fenced-text endings otherwise. EXP-055 had 1 (fastapi_14448, which this time made calls).
- T = 0 of 8 (reference 3). The last `python` or `pytest` after the last edit: rich_3006 ran a pytest on a path that does not exist (exit 4, does not count); requests_7205 ran a `python` print of the notice line (not a test, not an import of an edited module); httpx_3672 ran the script name as a shell command (exit 127); fastapi_14448 ran the repo's `scripts/test.sh` (exit 2, collection errors from test-only packages, not a `python` or `pytest` command by the text rule); rich_3468 and fastapi_14301 ran no check after the edit.
- V1 = 2 of 8 by the literal rule (reference 7): requests_7205 (the print) and rich_3006 (the exit-4 pytest). Neither tested the edit. G = 0 (no run ended with exit 0 or 1).

**Why the script gave nothing (found by reading the traces and the harness sandbox source, not by a kernel experiment).**

1. The picker's root is the fixed string `/workspace`. In the Kaggle subprocess sandbox the commands' working directory is a per-task temp workspace and the literal `/workspace` is rewritten only inside command strings, so the script saw no files and printed the notice line every time, including on well-formed calls (rich_3468, requests_7205 second call). The pytest rootdir in the traces is a temp workspace path, consistent with this. Neither the local dry run (section 2.4) nor the importability filter exercised this; the dry run used a workspace laid out at `/workspace`. This is an inference from the source; the kernel did not print the script's root.
2. The model called the skill by a name other than the declared `check-picker` (fastapi_14301, `SKILL_NOT_FOUND`) and passed `args` in a shape the tool rejects (requests_7205, `INVALID_ARGUMENTS`: a list together with another argument field), and twice called with no arguments. The harness side is fine: the skill is found when named right, the script runs, and error responses are well formed. No ToolNotFoundError and no "script not found" in any trace (VERIFY(Q1) for the skill path is answered: it runs, through `run_skill_script`).

**Blind prediction against outcome.** Ad 5 of 8 against 6 to 7; T 0 against 4 to 5.5 per run; G 0 as predicted; mean wall 65.1 s against 70 to 100 s (inside the harm bound, below); S_x 2 against 0 (the miss). The compliance prediction missed because the arguments the model had to supply were often wrong or absent, and the outcome the package exists to change did not occur because the picker returns the notice. This is a defect of the build, not a result about the idea.

**What r1 licenses.** Nothing on T. The package as built cannot test the hypothesis: every pick is the notice line. **r2 runs the identical zip (`1a591945...a33126`) and carries the same defect;** its T would be read against the same cause, so it is a second mechanism sample (script-call shapes, skill-name errors, tool-free rate), not a T test. Rows 2 to 6 are applied only if r2's analysis is run, and then with the caveat that the picker returned the notice. A fixed script (derive the root from the process working directory or `PYTHONPATH` rather than a constant; accept both argument shapes; name the skill exactly in the prompt) is a new tree and a new round, which needs the user's word (`knowledge/lessons-e4b-loop.md`). Not committed or built here.

## Status

2026-11-08: **r1 PUSHED, COMPLETE and ANALYSED (`rainm4/gemma4-exp056-r1`, 0.281 GPU-h): section 4 row 0 fired as written (S_x = 2: `SKILL_NOT_FOUND`, `INVALID_ARGUMENTS`), row 1 did not; Ad 5 of 8, T 0 of 8, G 0, resolved 2 of 8 not read; mechanism result, the picker returned the notice line every time (fixed root `/workspace` against the sandbox temp workspace).** r2 PUSHED (`rainm4/gemma4-exp056-r2`, version 1, RUNNING), same zip and same defect, analysis pending and not a T test. Zip `1a591945...a33126`. See section 9.1.
