# EXP-037 — The v24 single loop plus a proactive vendoring section (search, then write two test-only stand-ins), on the gated 8

**Date:** 2026-11-05
**Type:** smoke screen, one arm, 8 tasks, 31B. Estimate 0.90-0.93 L4x4-h at the point, **1.24 h worst case** (all eight at the 8-minute cap); section 2 gives the arithmetic. No upload.
**Cohort:** gated-8 (`experiments/cohorts/gated-8.txt`, 8 ids: fastapi_11355, fastapi_13207, fastapi_14297, fastapi_14360, fastapi_14459, fastapi_14512, fastapi_14583, fastapi_14605). **Selected on outcome** (section 1).
**Ladder:** L2. L0 and L1 are done: EXP-034 (the gated set), EXP-036 (re-grade with the packages present: R 3, RH 5 of the 15 gated flip), and the trigger mining of section 1 (zero GPU). smoke-8 cannot read this claim: it holds one gated task and three of the six patch-insensitive tasks (C-022).
**Pre-registered:** this file, the candidate tree, the cohort file, the build scripts and the notebook are committed before any push. Sections 2 to 6 are written blind and are not revised; results are appended as section 9, which applies section 4 as written. **The user has not approved the GPU spend. This job pushes nothing; the push is a later job.** The worst case is above 1 GPU-h, so whether a critic `prereg` review comes first is the lead's call (section 2, Cost).
**Serves:** C-021 (the grading gap hides real fixes), C-022 (the six patch-insensitive tasks, only as a cohort exclusion), D-005.
**Relates:**
- EXP-027: the base tree, `experiments/EXP-027/candidate-v24-at-8/`, zip c22069db...7600.
- EXP-028: Arm R (that tree as run) and Arm RH. Both are references on the same 8 ids.
- EXP-034: the gated set (`posthoc_gated.py`) and the trace miner (`mine.py`), imported by `experiments/EXP-037/mine_trigger.py`.
- EXP-036: the re-grade that fired row 1, and the placement of the shims.
- EXP-004 and `tools/compat_shims/`: the stand-in code this section reproduces.

## 1. Why this, now

**The gap and its size.**
- EXP-036 row 1 fired. With `inline_snapshot` and `dirty_equals` present at grading, R's patches resolve 3 more of the 15 gated tasks (fastapi_13207, 14297, 14360) and RH's 5 more (those three plus 14459, 14605).
- As run, R and RH resolve 0 of the 15, and none of their 96 patches carries a stand-in.
- The as-run grader on Kaggle has no shim code (EXP-034 §7 item 5). A task's own test file that imports a missing package fails as a whole.

**Which trigger: counted from the traces, zero GPU** (`experiments/EXP-037/mine_trigger.py` -> `trigger_mining.json`, gate regex `No module named '?(inline_snapshot|dirty_equals)` on tool results).

| Arm (dev-48) | Saw the error, of 15 gated | Vendored | First vendor at counted call | In final patch | Under tests | Vendored, then dropped | Gated resolved as run |
|---|---|---|---|---|---|---|---|
| R | **0** | 0 | - | 0 | 0 | 0 | 0 |
| RH | **0** | 0 | - | 0 | 0 | 0 | 0 |
| E0 | 3 (13207, 14297, 14583) | 3 | 24, 24, 28 | 3 | 0 | 0 | 2 (13207, 14297) |
| A25 | 3 (14297, 14360, 14953) | 3 | 17, 17, 21 | 3 | 0 | 0 | 2 (14297, 14360) |
| B25 | 1 (14297) | 1 | 18 | 1 | 0 | 0 | 1 |
| X003 | 0 | 0 | - | 0 | 0 | 0 | 0 |

- **R and RH never see the error.** R ran pytest on 1 of the 15 and never after its last edit; RH ran pytest on none. The old "Known sandbox gaps" section (`submission/prompts/swe_coder.md`) fires only when the error is seen, so on the v24 tree it would fire on 0 of 15. **Choice: a proactive trigger.** The first tool call is one bounded search of test paths for the two import names. The stand-ins are written only if that search prints a path.
- **The older lineage vendored exactly when it saw the error, and kept what it wrote.** In all four arms: 0 vendored without seeing it, 0 saw it without vendoring, 0 vendored then dropped. Every older-lineage gated resolve came through a vendored stand-in: 5 of the 7 gated vendorings resolved. The cost was the timing: the first vendoring came at counted call 17 to 28, late in a 28-to-45-call budget.
- **Placement.** Every stand-in in an older-lineage final patch is top-level `inline_snapshot/__init__.py` or `dirty_equals/__init__.py`: 15 task patches, gated and not, all top-level (`experiments/EXP-037/vendor_paths.py`). EXP-036 dropped `tools/compat_shims` into `/workspace` the same way. `tools/regrade_patches.py` records why that works: the subprocess sandbox sets `PYTHONPATH=<workspace>` for the grading pytest.
- **Older-lineage stand-ins on non-gated tasks** (final patch): E0 1 (13537, resolved), X003 3 (13537, 14301, 15589; 2 resolved), A25 1 (13537, resolved), B25 3 (13537, 15800, 5624; 2 resolved). R and RH: 0.

**Reach of the search, measured on the base-commit snapshots** (`trigger_mining.json`, `snapshot_reach`): a base-commit `.py` file under a test path names either package on **26 of 48** dev-48 tasks. That is all 15 gated tasks plus 11 non-gated (fastapi_13537, 14301, 14448, 14463, 14873, 15280, 15589, 15661, 15800, 5624, 9753). These are the same 11 non-gated tasks where EXP-036 dropped shims, and none flipped there. The rules "any `.py`", "top-level `tests/`" and the `'*test*'` pathspec all give 26 of 48; "outside test paths" gives 0.

**Cohort rule** (also in the file header). The cohort is the five ids that flip under the EXP-036 re-grade in R or RH (fastapi_13207, 14297, 14360, 14459, 14605), plus 3 of the other 10 gated ids. The 3 are the ones whose sha256 of the text `20261105037:<id>` plus a line feed (LF, no BOM) has the smallest hex digest; seed 20261105037. That draw gives fastapi_14512, fastapi_11355 and fastapi_14583.
- **This cohort is selected on outcome.** A resolve count on it measures conversion on these ids. It is not a dev-48 rate, it does not project to the leaderboard, and it cannot be compared with any dev-48 resolve count.
- The six patch-insensitive tasks of C-022 are not in it (all fastapi gated ids are patch-sensitive).
- The other 7 gated ids form the second set used by the re-run rules of section 4: fastapi_13786, 14262, 14609, 14953, 14962, 14964, 15030.

**Reference runs on the same 8 ids**, already measured; no new GPU. From `experiments/EXP-028/{armR,armRH}/summary.jsonl`:

| id | R wall s / calls / cap | RH wall s / calls / cap | R re-graded (EXP-036) | RH re-graded |
|---|---|---|---|---|
| fastapi_11355 | 248 / 25 / - | 270 / 22 / - | F | F |
| fastapi_13207 | 312 / 27 / - | 370 / 29 / calls | **T** | **T** |
| fastapi_14297 | 433 / 26 / - | 136 / 10 / - | **T** | **T** |
| fastapi_14360 | 343 / 16 / - | 488 / 27 / time | **T** | **T** |
| fastapi_14459 | 382 / 24 / - | 265 / 25 / - | F | **T** |
| fastapi_14512 | 198 / 29 / calls | 419 / 29 / calls | F | F |
| fastapi_14583 | 422 / 28 / calls | 488 / 19 / time | F | F |
| fastapi_14605 | 156 / 29 / calls | 188 / 36 / calls | F | **T** |
| sum / count | 2,493 s (mean 311.7) / 204 / 3 capped | 2,623 s / 197 / 5 capped | 3 of 8 | 5 of 8 |

- As run: 0 of 8 in both arms.
- Compactions (analyzer field): R 12, RH 10.
- R's five uncapped tasks: 11355, 13207, 14297, 14360, 14459. Two of them are close to the call cap in R: 13207 at 27 calls, 14297 at 26.

## 2. Design

**One variable.** The candidate is `experiments/EXP-037/candidate-vendor/`, built by `experiments/EXP-037/make_candidate.py` from `experiments/EXP-027/candidate-v24-at-8/`.
- The script checks the base file set and the recorded sha256 of all four base files.
- It inserts `experiments/EXP-037/insert_vendoring.md` into `prompts/system.md` immediately before the line `## 1. Contract, before any tool call`; that line must match exactly once.
- Every other file is byte-copied: `agent.yaml` 6ad913b0...5227, `eval_config.yaml` 916cf6cb...c531 (240 s / 28 calls / 8 min / 80 turns), `configs/sampling.yaml` 63005688...c3f6 (T 1.0, thinking 4096, max output 8192).
- `prompts/system.md` goes from 3,162 to 5,595 bytes (+2,433, 44 lines added, 0 removed), sha256 `43fcdf77535b8fb9559c5529b2bb127245ca132a3199a5e90dd122d866416cb9`.

**The inserted section, in its parts.**
1. **Why.** Two sentences: some tests import the two packages, the sandbox may lack them, and a test file that cannot import one fails as a whole.
2. **First tool call:** `cd /workspace && git grep -l -e inline_snapshot -e dirty_equals -- '*test*' | head -3` (85 bytes). If it prints nothing, the agent goes to step 1.
3. **Second tool call, only if a path was printed:** one fenced `run_command` (1,712 bytes, 38 lines, sha256 `f32c0467...ef54`). For each package, `if ! python -c 'import <pkg>'`, it writes `<pkg>/__init__.py` at the top of `/workspace` with a heredoc, then prints `git status --short | head -5`.
4. **The exception.** One sentence: the new directories are part of the fix and the one exception to the v24 rules on new files and files left in the repository; never edit or delete them, and keep them in the diff at `submit_patch`.

**Why two calls, not one.** A single combined command would make the model emit the 1.7 KB heredoc on every task, hit or not. R's forensics put a heredoc-write turn at a median 12.66 s (mean 22.6 s, 48 calls) and a grep turn at a median 4.14 s (mean 11.7 s, 286 calls) (`tools/run_forensics.py forensics runs/EXP-028-armR`). The 8-minute headroom on the projected hidden-set total is 13.8 s per task (EXP-032 row d: 10.5 - 10.04 h). So a task with no hit pays one grep turn, and only a hit task pays for the write.

**Why both packages.** The command writes both stand-ins whenever either name is found, guarded only by the import check. On a repository that needs one package, the other is a stand-in that is not needed, by design. Splitting it would mean a longer command or a third call.

**Stand-in code.** ~~It is the subset of `tools/compat_shims/{inline_snapshot,dirty_equals}` that a test file can reach,~~ rewritten without literal braces: the validator warns on braces (ADK templating), so there are no f-strings and no `{ }` groups.

*Corrected 2026-11-05, after the critic prereg review (`experiments/EXP-037/critic.md`, b60bb81), fix 4.* The struck words claimed coverage that the probes do not show. What the build shows is that the code behaves the same as `tools/compat_shims` (128 probes, 0 differ). It does not cover every name in the tests tree: in all 15 gated snapshots the tests tree imports `Is`, `IsInt` and `IsStr`, which neither shim provides. Why it is still enough on this grader is a chain of three links, and the conclusion holds only on this grader:
1. The code is the same as `tools/compat_shims` (the 128 probes).
2. GOLD resolves 15 of 15 gated tasks with `tools/compat_shims` supplied (EXP-036).
3. The grader runs only the files the test patch touches (`Task.test_files`, harness-stack). The tests-tree files that import the missing names are not collected.

So the stand-ins are sufficient for all 15 gated tasks on this grader only. Section 7a (desk check B1) lists the names the graded files and their conftest and helper closure actually reach.
- `inline_snapshot`: `Snapshot`, `snapshot`.
- `dirty_equals`: `IsDict`, `IsPartialDict`, `IsOneOf`, `HasRepr`, and `|` alternation.
- **Build check** (`python experiments/EXP-037/check_standins.py`, passes):
  - Repo (a), with a test file importing `inline_snapshot`: the search prints `tests/test_a.py`. The second call writes exactly `inline_snapshot/__init__.py` and `dirty_equals/__init__.py` at the top level and nothing under `tests/`, and its output is `?? dirty_equals/` and `?? inline_snapshot/`. A repeat changes nothing.
  - Repo (b), with no such import: the search prints nothing.
  - 128 behavioural probes against `tools/compat_shims` (equality both ways, inequality, repr, hashability, alternation, class subscription): 0 differ.
  - The commands were run with Git Bash on Windows, not in the Kaggle sandbox.

**Validator.** `python tools/validate_submission.py experiments/EXP-037/candidate-vendor --strict` gives 1 ERROR and 1 WARN, the same two findings the base tree has. No lint finding was added; the instruction is 5,595 characters.
- ERROR: `worst case 120 x (8 + 1.0 setup) min = 18.00 h` exceeds the packing gate. This is the same value as EXP-027, EXP-028 and EXP-032 (8 minutes), overridden with `--skip-budget-gate`: this is a screen of 8 tasks, and the zip is for the notebook only and is never uploaded.
- WARN: `timeout_seconds=240 < 300`, as in the base tree, unchanged on purpose.

**Cost of the text in tokens** (`experiments/EXP-037/prompt_cost.py` -> `prompt_cost.json`).
- **Measured rate.** R to RH's 942-byte prose section adds 0.2866 tokens per byte, constant over 48 tasks; R to A25 gives 0.2508.
- **System prompt.** The insert adds about 700 tokens at the prose rate. Code may tokenize denser; the rate is not measured, and at 0.39 tokens per byte the insert is about 950.
- **Growth by task type.**
  - Hit task: the second call's arguments (1,712 bytes) and the two short tool results stay in the history, so about 1,250 to 1,700 tokens are added to every prompt after call 2.
  - Miss task: about 750 to 1,000 tokens.
- **Compaction threshold (14,336).** Arm R's dev-48 peaks: 38 of 48 tasks already reach it. Adding 700, 1,400 or 1,800 tokens newly reaches it on 1, 2 and 2 tasks. On gated-8, all 8 already peak at or above it (14,340 to 16,112), so 0 are newly reached; more compactions per task are possible.
- **First prompt.** R's median first prompt is 2,925 tokens on dev-48 and 2,835 on gated-8, so about 3,650 to 3,900 with the insert.

**Build.**
- `python tools/pack_submission.py --src experiments/EXP-037/candidate-vendor --out dist/EXP-037-vendor.zip --skip-budget-gate --allow-warnings` gives 4 members (agent.yaml, configs/sampling.yaml, eval_config.yaml, prompts/system.md), sha256 **`a43798560ae9bc1b5e5b8e82805c6a5d43282f14ffffbe6e02a3ee9b08f31a71`**.
- The zip is gitignored (`dist/`). The candidate files were written LF by `make_candidate.py`.
- Notebook: `notebooks/exp037_vendor/kaggle_eval_l4x4.ipynb`, built with the gated-8 cohort, `EXP_ID = "EXP-037-vendor"` and `RUN_GOLD_CONTROL = False`.
  - The parameter cell was read back: `TASK_IDS` holds the 8 ids in file order, `N_TASKS = 8`, `RUN_AGENT = True`; `RUN_PHASE0_CHECKS` and `MEASURE_DECODE_SPEED` are left `True`, as in EXP-028 and EXP-032.
  - The embedded base64 zip was decoded and hashed: it equals the sha above.
  - `kernel-metadata.json` was copied from `notebooks/exp032_p1` with only `id` (`rainm4/gemma4-exp037-vendor`) and `title` changed.

**Cost in GPU-hours.**
- Overhead: EXP-032 P1's kernel ran 3,280.1 s for a task-duration sum of 2,763.4 s, so 516.7 s of overhead (vLLM up in 379.5 s, decode probe 29.8 tok/s). EXP-033 measured 444.8 s.
- Point estimate: 517 s + R's 2,493 s on these ids + 30 to 40 s added per task x 8 = 3,250 to 3,330 s, **0.90-0.93 h**.
- Worst case: all 8 at the 480 s cap plus about 15 s setup each, 8 x 495 + 517 = 4,477 s, **1.24 h**.
- Both figures are reported, and the over-1.0 decision is left to the lead.

*Corrected 2026-11-05, after the critic prereg review (b60bb81), fix 2. The two bullets above are kept as first written.*
- **The worst case is conditional.** It is 1.24 h only if no task overruns the 8-minute cap. Overruns happen: 1 of 96 R and RH tasks ran 751.9 s at the 8-minute cap (rich_3480 in RH). Each such overrun adds about 0.07 h.
- **Re-runs ordered by rows 2 and 3.** Each re-run is a second smoke screen of 7 or 8 tasks and costs about 0.85 to 1.24 h. The approved ceiling has 1.34 of 3.2 h left before this run, and about 0.1 to 0.44 h after it. A re-run therefore exceeds what is left. **Each re-run needs its own approval from the user** before it is built or pushed. Until it is approved, a row 2 or row 3 result is reported as a kill pending a re-run that has not been funded.
- **Notebook cells (critic P6).** The notebook's code cells equal Arm R's except two:
  - cell 0, the parameters, which adds a new empty `MODEL_NAME`;
  - cell 5, which takes the model directory from the zip (D-004) and resolves the same 31B directory.

  Neither is a second variable.

## 3. Endpoints, fixed in advance

All are read per task over the 8 ids from `traces/trace_<id>.json`, `task_results.jsonl` (`patch`) and `summary.jsonl`. The R and RH figures come from their existing runs on the same ids (section 1).

| # | Endpoint | Definition |
|---|---|---|
| a | **Mechanism** | Counts over the 8 tasks:<br>- G: the first counted tool call is a `run_command` containing `git grep -l -e inline_snapshot -e dirty_equals`.<br>- W: a `run_command` containing `cat > inline_snapshot/__init__.py` or `cat > dirty_equals/__init__.py` was issued; record the counted-call index of the first such call.<br>- **M_any**: the final patch creates at least one of top-level `inline_snapshot/__init__.py` or `dirty_equals/__init__.py`.<br>- M_both: it creates both.<br>- F: the created file text is byte-identical to the heredoc body in `insert_vendoring.md`. |
| b | **As-run resolves (K)** | Of 8, as graded by the notebook (no shims at grading). Reference: R and RH as run 0 of 8; re-graded R 3 and RH 5, all on the five flip ids. Reported by id, split into the flip five and the other three. n = 8: K is a conversion count on outcome-selected ids, with no test and no dev-48 rate. |
| c | **Cost** | Per task, paired against R by id:<br>- counted calls (`n_calls`), wall (`wall_s`), compactions (analyzer field), `calls_cap_hit`, `time_cap_hit`.<br>- **X**: of R's five uncapped tasks, how many now end at a cap.<br>- **X0**: of those, how many have no source-file edit in the final patch (any file other than the two stand-ins).<br>- Direct turn cost: ~~Δ_miss = median elapsed of the grep turn; Δ_hit = median elapsed of the grep turn plus the write turn~~, both from step timestamps.<br>- *Corrected 2026-11-05 after the critic prereg (b60bb81), fix 1:* Δ_miss = **mean** elapsed of the grep turn over the 8 tasks; Δ_hit = **mean** elapsed of the grep turn plus the write turn over the tasks that write. The 13.8 s headroom is derived from a mean projection (EXP-028 section 9), so a median does not compare with it. **Δ is a lower bound** on the added time: it omits the larger prompt on every later call and any extra compactions.<br>- **Δ_8min = (26/48) x Δ_hit + (22/48) x Δ_miss**, compared with the 13.8 s per-task headroom at 8 minutes. 26 of 48 is the dev-48 reach of the search (section 1); the hidden set's reach is unknown.<br>- Paired mean wall difference against R and its SE are also reported. |
| d | **Harm** | **H1**: a stand-in path in the final patch that is not top-level, or that sits under a path component named `test` or `tests`.<br>**H2**: the write call's `git status --short` output shows any line not starting with `??` (a tracked file changed), or the final patch modifies a tracked file named like a package.<br>**H3**: a stand-in written (W) and absent from the final patch, or touched after the write by `edit_file`, `write_file` or a later `run_command` that names its path.<br>*Added 2026-11-05 after the critic prereg (b60bb81), fix 3:* for each H3 event, record what the touch did: names added, code changed, or code removed (or the file deleted). Row 1 counts every H3 event, including an additive one.<br>Also reported: tasks where only one package's import fails on the grader but both stand-ins were written (by design, section 2). "Written where not needed" cannot be read on this cohort, because every id needs a stand-in. |
| e | Recorded, not read | The first source-file edit as a counted-call index (the `run_forensics.py` first-edit rule, with the stand-in write excluded), paired by id against R. It is recorded because v24's "Search once" and "Edit by tool call 12" now run after one or two calls are spent (section 7 item 2). Also recorded: `edit_file` arg-loss and malformed calls. |

Statistics: none. n = 8 reads counts and all-or-none events only.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Rows are applied in order; the first match governs. The critic's rule applies: **a kill at n = 8 gets one re-run on a second set before it stands** (rows 2 and 3).

| # | Outcome | Reading and what happens next |
|---|---|---|
| 0 | Fewer than 8 task rows; vLLM fails; the run's agent tree differs from `candidate-vendor`; or G = 0 (the section was not delivered) | **Infrastructure, no reading.** Read the log for the class and say which endpoints are lost. A re-push needs the lead. |
| 1 | H1 or H2 in 1 or more tasks, or H3 in 2 or more | **Harm: fix the text.** The exception sentence does not hold against v24's rules on new files, or the command misplaces files. One rewritten-text screen of the same size; no promotion. Report which v24 rule the agent cited, if it did. |
| 2 | M_any is 4 or fewer of 8 | **Mechanism kill, pending a re-run.** Classify each failure: no grep first, grep printed nothing, no write call, write call mangled (non-zero exit or wrong path), or stand-in removed (H3). The kill stands only if one re-run on the second set (the other 7 gated ids, section 1) also gives M_any of 3 or fewer of 7. Otherwise read the pooled 15 against rows 3 to 7. |
| 3 | M_any 6 or more, K = 0 | **Conversion kill, pending a re-run.** The stand-ins are carried, but the fixes do not resolve.<br>- Zero-GPU diagnostic first: re-grade this run's patches with the stand-ins stripped and `tools/compat_shims` supplied (the EXP-036 tool). That splits stand-in code from fix quality.<br>- Then one re-run on the same gated-8 (the flip ids are only in this set). The kill stands only if the re-run is also K = 0. |
| 4 | M_any 6 or more, K = 1 | **Weak.** Lead's call. The same zero-GPU diagnostic as row 3 is available; no promotion on this alone. |
| 5 | M_any 6 or more, K 2 or more, and (X0 2 or more, or Δ_8min above 13.8 s) | **Converts, but costs budget.** The next rung is one dev-48 arm (lead's call; its own prereg and critic). It must run at a time setting the arithmetic admits: a 4.5-minute build, or a dev-48 time-profile arm with projected hours as the primary endpoint. The paired non-gated resolve count against R is the safety endpoint. **No 8-minute upload.** |
| 6 | M_any 6 or more, K 2 or more, X0 1 or fewer, Δ_8min 13.8 s or less | **Promote to one dev-48 arm** (lead's call, 4 to 7 GPU-h, its own prereg and critic). Primary: paired dev-48 resolves against R, the gated and non-gated split, and projected hours with the non-hit grep cost. **No upload is licensed by this screen.** |
| 7 | None of the above (for example M_any = 5) | Report the numbers; no decision. Lead's call. |

**Amendments to the table, 2026-11-05, after the critic prereg review (`experiments/EXP-037/critic.md`, b60bb81), fix 3.** The table above is kept as first written. No result exists yet, so these are corrections before the fact. Where they differ from the table, these govern.
- **Row 0, a grading fault, added.** A task has a grading fault if it has no grade, or if it has `test_exit_code` -1 (the test patch did not apply) on a patch that touches no test path. If any of the 8 tasks has one, K is not read and rows 3 to 6 do not apply. Endpoints (a), (c) and (d) are still reported, and the class is read from the log as row 0 says.
- **M_any = 5, a rule added.** Rows 3 to 6 apply at M_any 5 or more, not 6 or more, with their K, X0 and Δ_8min thresholds unchanged. A reading at exactly M_any = 5 is labelled **mechanism weak (5 of 8)**, and its next step is the one its row gives. Row 7 keeps only outcomes that no row covers.
- **Row 2's pooled-15 re-read, thresholds added.** The re-run on the second set (7 ids) needs its own user approval (section 2, Cost). If it runs, M_any is pooled over the 15 gated ids:
  - 7 or fewer of 15: the mechanism kill stands.
  - 11 or more of 15: rows 3 to 6 are applied to the pooled 15. K counts stay absolute (K = 0, K = 1, K 2 or more), because all five flip ids are in gated-8. X and X0 are counted over R's uncapped tasks among the 15. Δ_8min uses the pooled means.
  - 8 to 10 of 15: report the numbers, with no decision; lead's call.
- **Base rate of K 2 or more (critic, answer 1).** fastapi_13207, 14297 and 14360 flipped under the EXP-036 re-grade in both R and RH. If those three carry a stand-in, K of 2 or more is close to certain [I]. A row 5 or row 6 reading therefore shows mainly that a carried stand-in plus a fix already known to be right survives two extra calls and the as-run grader. It is not evidence of a resolve gain beyond EXP-036's +3 (R) and +5 (RH) of 48.

A gated task resolves on this grader only if a stand-in is in the patch. Evidence: R and RH resolve 0 of the 15 as run without one, and every older-lineage gated resolve came with one (section 1). A K above 0 is therefore the stand-in's effect together with the fix. Whether the fix alone is right is what the row 3 diagnostic separates.

**Prediction, written blind:**
- Mechanism: M_any = 7 of 8 and M_both = 7; F (byte-identical) in 5 of the 7; the write at counted call 2 in every task that writes.
- Resolves: K = 3 of 8 (80% interval 1 to 5), all from the five flip ids.
- Calls: +2 per task at the median.
- Turn cost: Δ_hit about 17 s at the median (the forensics medians, 4.1 + 12.7 s) and Δ_miss about 4 s, so Δ_8min about 11 s. On the forensics means (34 s and 12 s) it is about 24 s, so even odds that the 13.8 s rule flags.
- Caps: X = 1 or 2 (13207 and 14297 are 1 and 2 calls from the cap in R) and X0 = 0.
- Compactions: about 14 against R's 12.
- Harm: 0 events.
- Rows: row 5 at 35%, row 6 at 20%, rows 3 and 4 together at 25%, row 2 at 10%, row 1 at 10%.

**Prediction restated 2026-11-05, after the critic prereg (b60bb81), fix 1.** The prediction above is kept as first written. It read Δ on medians, which fix 1 retracts. Under the corrected definition (means, a lower bound) and the amended table:
- Mechanism, resolves, calls, caps, compactions and harm: unchanged (M_any 7, M_both 7, F in 5 of 7, write at call 2; K = 3 of 8, 80% interval 1 to 5; +2 calls; X 1 or 2, X0 0; compactions about 14; H 0).
- Turn cost, on means:
  - Δ_miss is about 12 s; on gated-8 it is read from the grep turn of all 8 tasks.
  - Δ_hit is about 34 s on the forensics means (11.7 + 22.6 s), or 39 to 45 s on the section 7a write-turn model [I].
  - So Δ_8min is about 24 s (range 22 to 30 s).
  - Section 7a also shows that no two-call design clears 13.8 s on means: the floor is 18.0 s with zero extra bytes.
  - So the 13.8 s rule flags with probability about 0.95, not at even odds.
- Rows: row 5 at 50%, row 6 at 5% or less, rows 3 and 4 together at 25%, row 2 at 10%, row 1 at 10%. Row 7 is about 0, because M_any = 5 now falls under rows 3 to 6.

## 5. What this does and does not license

**Can decide:** whether the v24 agent carries the two stand-ins when told to proactively (rows 1 and 2). Whether, on the ids where R's or RH's fixes are known to be right under the re-grade, carrying them converts into as-run resolves (rows 3 to 6). Whether the next rung is a dev-48 arm at 8 minutes or only at a setting the time arithmetic admits (rows 5 and 6).

**Cannot decide:**
- Any dev-48 or leaderboard rate. The cohort is selected on outcome.
- The net effect on non-gated tasks: the +2 calls on the 11 non-gated hit tasks, and the +1 call on the 22 miss tasks.
- Whether the hidden set needs these packages at all. It is private repositories, so its reach is unknown and may be 0, in which case the section is pure cost: about 4 to 12 s per task for the grep turn.

**Risks that this screen cannot read, stated now:**
- **Shadowing on a grader that has the real packages.** The import guard skips the write only when the package imports in the agent's sandbox. If the agent's sandbox lacks it but the grader has it, the stand-in sits first on `PYTHONPATH=<workspace>` and replaces the real package with a subset.
- **Placement on another grader.** Top-level placement works on the subprocess sandbox because it puts the workspace on `PYTHONPATH` (`tools/regrade_patches.py`). It is verified on the fastapi layout only, which is all of gated-8. A grader with a different path setup is unverified.
- **The hidden-set time projection.** Δ_8min uses dev-48's reach of 26 of 48; the hidden set's reach could be anywhere from 0 to that.

*Added 2026-11-05, after the critic prereg (b60bb81), fix 4.*
- **The shadowing regression, by its mechanism.** Take a grader that has the real packages, run on a patch whose agent sandbox lacked them, so the stand-ins were written. The top-level stand-in comes first on `PYTHONPATH=<workspace>` and replaces the real package. A graded file that imports a name the stand-in lacks then fails at collection, where it would otherwise pass. For example, the tests trees of all 15 gated snapshots import `Is`, `IsInt` and `IsStr` (section 7a). On this grader no graded file reaches those names, which is why the chain in section 2 holds. A grader with the real packages and different graded files is not covered.
- **`__pycache__`.** The `.gitignore` of all 15 gated snapshots covers `__pycache__`, and 0 of the 15 older-lineage final patches that carry a stand-in have a `.pyc` or binary hunk (critic, answer 4). So on this layout the import check and pytest do not put bytecode into the patch [I]. `check_standins.py` excludes `__pycache__` in `files_of`, so it does not test this.
- **The base rate of K.** K of 2 or more has a high base rate on this cohort (section 4 amendments). So "carries and converts" can be read; "gains" cannot.
- **Non-gated tasks.** A stand-in cannot change a non-gated task's grade through an import, because such a task would be gated. On those tasks, cost and misplacement (H1, H2) are the only channels [I]. This screen reads neither on non-gated tasks; section 7a, B3, sizes a cohort that could.

**No row licenses an upload.**

## 6. Exact commands

```
python -I -X utf8 experiments/EXP-037/mine_trigger.py --tasks data/raw/tasks.jsonl --snapshots data/local/snapshots --cohort experiments/cohorts/dev-48.txt --out experiments/EXP-037/trigger_mining.json
python -I -X utf8 experiments/EXP-037/vendor_paths.py
python -I -X utf8 experiments/EXP-037/prompt_cost.py --ids experiments/cohorts/gated-8.txt --delta 700 1400 1800 --out experiments/EXP-037/prompt_cost.json
python experiments/EXP-037/make_candidate.py
python experiments/EXP-037/check_standins.py
python -I -X utf8 experiments/EXP-037/desk_checks.py --tasks data/raw/tasks.jsonl --snapshots data/local/snapshots --out experiments/EXP-037/desk_checks.json   # added 2026-11-05, section 7a
python tools/validate_submission.py experiments/EXP-037/candidate-vendor --strict
python tools/pack_submission.py --src experiments/EXP-037/candidate-vendor --out dist/EXP-037-vendor.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed dist/EXP-037-vendor.zip --username rainm4 --cohort experiments/cohorts/gated-8.txt --set EXP_ID='"EXP-037-vendor"' --set RUN_GOLD_CONTROL=False --out notebooks/exp037_vendor/kaggle_eval_l4x4.ipynb
# later, a separate job, only after the user approves the GPU spend (and the critic, if the lead asks):
#   kernel push of notebooks/exp037_vendor
# later still, after the status says COMPLETE:
kaggle kernels output rainm4/gemma4-exp037-vendor -p runs/EXP-037-vendor/
python tools/analyze_traces.py runs/EXP-037-vendor --cap-minutes 8 --max-calls 28
python tools/run_forensics.py forensics runs/EXP-037-vendor
python tools/run_forensics.py compare runs/EXP-028-armR runs/EXP-037-vendor
# endpoints a, c (turn cost, X0), d and e need a small analysis script under experiments/EXP-037/, written at analysis time against the definitions of section 3
```

## 7. Defects in this pre-registration, logged at writing time

1. The v24 heading `## 1. Contract, before any tool call` now follows text that orders two tool calls first. The contract is a text list, so the two do not strictly conflict, but the wording is stale. It is not changed (one variable).
2. v24's "Search once", "Edit by tool call 12" and "You have 28 tool calls" are unchanged. On a hit task, two of the 28 calls and two of the first 12 are now spent before step 2. Endpoint (e) records the displacement; it is not read.
3. The command writes both packages whenever either name is found (section 2), so on a repository that needs one there is a stand-in that is not needed, by design.
4. The `'*test*'` pathspec matches any path containing "test", not only test directories. On dev-48 it equals the tests-directory rule (26 = 26); on other layouts it may match more.
5. The tokenization rate of code is not measured. The token growth in section 2 is a range.
6. The analysis script for endpoints (a), (c), (d) and (e) is not written yet. If a trace field these definitions need is missing, the analysis will say which endpoint is lost.
7. The screen artifact is packed with `--skip-budget-gate` (18.00 h at 8 minutes, the same as the base tree). The zip is never an upload candidate.

8. *Logged 2026-11-05, from the critic prereg (b60bb81).* The instruction names two specific third-party packages, `inline_snapshot` and `dirty_equals`, in a prompt meant to be repo-agnostic. Neither name is in the lint word list, so validation passes. The names are chosen from what dev-48's tests import, which is a fastapi-family fact. Whether the hidden set's private repositories use either package is unknown (section 5).

## 7a. Desk checks B1 to B3, 2026-11-05, after the critic prereg (zero GPU)

These were run after the critic's review (b60bb81), at the lead's request. They change no endpoint, reading or build: the candidate tree, cohort file and notebook are unchanged. Every number below is from `python -I -X utf8 experiments/EXP-037/desk_checks.py --tasks data/raw/tasks.jsonl --snapshots data/local/snapshots --out experiments/EXP-037/desk_checks.json`. The output holds names, counts and ids only. Inputs from earlier work, cited as they are used:
- turn means from `tools/run_forensics.py forensics runs/EXP-028-armR`: grep 11.7 s, heredoc-write 22.6 s, agent wall 230.4 min;
- decode 29.8 tok/s and overhead 516.7 s (EXP-032 P1); overhead 444.8 s (EXP-033);
- token rates 0.2866 to 0.39 per byte (section 2).

**B1. The smallest stand-in that the graded files need.**

*Method.* The graded files are the `.py` files the test patch touches, in their post-patch text. The patch applied cleanly to the base snapshot on all 15 gated tasks. To them are added every `conftest.py` on their directory chain and every local module they import, transitively. All imports are resolved inside the base-commit snapshot, and the names come from a static AST walk. Not modelled: `pytest_plugins`, dynamic imports, and `importorskip`.

*Names the graded closure reaches,* by task count of 15:

| Name | Tasks | How it is used |
|---|---|---|
| `inline_snapshot.snapshot` | 9 (all in the test-patch files themselves) | 73 calls, each with one positional argument, each an operand of `==`. No empty `snapshot()`, no keywords. |
| `inline_snapshot.Snapshot` | 5 (11355, 13207, 14262, 14297, 14512), only through a closure file, never in a test-patch file | 10 uses, all as a parameter annotation. No subscription and no calls. |
| `dirty_equals.IsDict` | 2 (13786, 14605) | 42 calls, positional arguments only. Every one is an operand of a two-operand `IsDict(...) \| IsDict(...)`: 21 expressions, 5 of them directly an `==` operand and the rest nested inside a larger compared value. No `.settings`, no keywords. |
| `dirty_equals.IsPartialDict` | 1 (14360) | 1 call, positional, an operand of `==`. |

On 4 tasks (11355, 13207, 14262, 14297) the test-patch files import nothing from either package. The gate there comes from a helper or conftest in the closure.

*Not reached by any graded closure,* though present in the tests tree:
- `Is`, `IsInt`, `IsStr`, `HasRepr` and `IsOneOf`: all 15 tasks;
- `AnyThing` and `IsUUID`: 8;
- `IsAnyStr` and `IsList`: 6.

This is the critic's coverage chain seen from the graded side (section 2). It is consistent with GOLD resolving 15 of 15 under `tools/compat_shims`, which lacks `Is`, `IsInt` and `IsStr`.

*The smallest stand-in.* It is the built command's form, keeping both import guards and the `git status` line, with the module bodies cut to the uses above. It has no literal braces.

```
cd /workspace
if ! python -c 'import inline_snapshot' 2>/dev/null; then mkdir -p inline_snapshot; cat > inline_snapshot/__init__.py <<'EOF'
class Snapshot: pass
def snapshot(v=None): return v
EOF
fi
if ! python -c 'import dirty_equals' 2>/dev/null; then mkdir -p dirty_equals; cat > dirty_equals/__init__.py <<'EOF'
class _Or:
    def __init__(self, a, b): self.a, self.b = a, b
    def __eq__(self, o): return self.a == o or self.b == o
    def __or__(self, o): return _Or(self, o)
class IsDict(dict):
    def __eq__(self, o): return isinstance(o, dict) and dict(o) == dict(self)
    def __or__(self, o): return _Or(self, o)
class IsPartialDict(dict):
    def __eq__(self, o): return isinstance(o, dict) and all(k in o and o[k] == v for k, v in self.items())
EOF
fi
git status --short | head -5
```

*Size and cost of the small command, against the built one:*

| | Built command | Small command |
|---|---|---|
| Bytes | 1,712 (38 lines) | **796** (19 lines; module files 52 and 444 bytes; sha256 `a9c0abdc...783e`) |
| Output tokens | 491 to 668 | **228 to 310** |
| Generation at 29.8 tok/s | 16.5 to 22.4 s | **7.7 to 10.4 s** |

The small modules were checked against `tools/compat_shims` with 979 equality probes, in both directions, on the observed forms: `snapshot(v)`, two- and three-operand `IsDict` chains, and `IsPartialDict`. 0 differ.

*Projected mean added time per task at 8 minutes,* Δ_8min = (26/48) x Δ_hit + (22/48) x Δ_miss, with Δ_miss = 11.7 s. The write-turn model is [I]: one grep-turn mean (11.7 s) plus generation of the bytes beyond the 85-byte grep.

| Design | Δ_8min |
|---|---|
| Built command, forensics means (write turn 22.6 s) | 23.9 s |
| Built command, write-turn model (27.3 to 33.0 s) | 26.5 to 29.6 s |
| **Small command, write-turn model (18.5 to 21.0 s)** | **21.7 to 23.1 s** |
| Any second turn at all, zero extra bytes (floor) | 18.0 s |
| Grep and small write in one command on every task [I] | 19.4 to 22.1 s |
| Grep turn only, on every task | 11.7 s |
| Headroom at 8 minutes | 13.8 s |

**Answer.** The small stand-in saves about 1 to 8 s per task, but it does not make the section shippable at 8 minutes on means:
- any design that spends a dedicated second turn on hit tasks has a floor of 18.0 s;
- the dedicated grep turn alone spends 11.7 s of the 13.8 s.

Only a design that spends no dedicated turn on miss tasks could fit [I]; none is designed here. All of these figures are lower bounds (section 3, endpoint c).

*Verifying it would need* a CPU re-grade on Kaggle, no GPU, with the EXP-036 tool (`experiments/EXP-036/build_regrade_notebook.py` and `kaggle_regrade_template.py`), supplying the two small modules instead of `tools/compat_shims`:
- GOLD on the 15 gated tasks must resolve 15 of 15;
- R's and RH's patches on the five flip ids must give the same 3 and 5 flips as EXP-036.

The static closure does not model dynamic imports, so this re-grade is the check. It is not built or pushed here.

**B2. A 3-call mechanism run, costed (not built).**
- *Tree.* The built candidate with `eval_config.yaml` `max_tool_calls: 3` and `max_time_minutes: 2`. This is a different `eval_config.yaml` from Arm R's, and the prompt's "You have 28 tool calls" is then false, a known mismatch for a run that reads only the mechanism.
- *Cohort.* gated-8: every id is a hit. Adding 3 dev-48 ids outside the search's reach makes 11 tasks. Without them the run cannot read whether the grep prints nothing on a miss and no write follows.
- *Reads:* G; whether the grep printed a path; W and its call index; F, from the write call's arguments in the trace and from the patch; H1, the placement; H2, from the `git status` line. It also reads the grep turn and write turn times directly, which are Δ_miss and Δ_hit as section 3 now defines them.
- *Does not read:* K (no fix fits in 3 calls); X and X0; H3 (nothing follows the write); compactions; the prompt-growth cost on later calls; the first-edit displacement (endpoint e); any non-gated harm.
- *Per-task inputs:*
  - hit-task agent time 63.9 to 74.3 s: the grep mean, a write turn of 22.6 to 33.0 s, one more call, and 2 non-call turns at R's mean of 9.86 s per turn. R ran 1,402 turns, with a median of 2 turns beyond its calls per task.
  - miss-task agent time 51.1 s;
  - task wall outside turns 9.4 s, from R's 14,276.9 s of task wall less 13,824 s of agent wall, over 48 tasks;
  - an allowance of 15 to 20 s per task for setup and grading, which is an assumption.
- *Estimate,* with an overhead of 444.8 to 516.7 s:
  - gated-8: **0.32 to 0.37 h**, with a ceiling of 0.45 h if every task runs the 2-minute cap;
  - gated-8 plus 3 miss ids: **0.38 to 0.44 h**, with a ceiling of 0.57 h.

  This is above the critic's ~0.2 h because the kernel overhead alone is 0.12 to 0.14 h. It fits inside the 1.34 h left on the ceiling.
- *How it relates to the full screen.* It costs about a third to a half of the full screen's 0.90 to 0.93 h point estimate. If it kills the mechanism (M_any of 4 or fewer), the full screen is not needed. If the mechanism holds, the full screen is still needed for K, X0 and H3, so the two together cost more than the full screen alone.

**B3. The harm cohort: non-gated tasks the search reaches.** There are 11 ids:
- 13537, 14301, 14448, 14463, 14873, 15280, 15589, 15661, 15800, 5624, 9753, all fastapi.

Resolves as run (EXP-036 `summary.jsonl`; the re-graded sets are identical):
- **R: 5**, namely 13537, 14301, 14463, 15589 and 9753;
- **RH: 5**, namely 13537, 14301, 14463, 15589 and 5624;
- **both: 4**, namely 13537, 14301, 14463 and 15589.

**So at least 3 exist that R resolves: there are 5.** A cohort of the 5 flip ids plus 3 of these could read harm on those 3, as unresolves against R, at n = 3.

None of R's 5 hit a cap there (`experiments/EXP-028/armR/summary.jsonl`): 11 to 22 calls and 78.9 to 371.9 s. The two closest to a cap, where two extra calls and a longer prompt are most likely to matter, are:
- 15589, at 371.9 s against the 480 s cap;
- 9753, at 22 of 28 calls.

Older lineages already carried top-level stand-ins on some of these ids and still resolved them (`vendor_paths.py`):
- 13537: resolved in E0, A25 and B25, unresolved in X003;
- 14301 and 15589: resolved in X003;
- 5624: resolved in B25;
- 15800: unresolved in B25.

No cohort file is changed here.

## 8. Built, not pushed

Built 2026-11-05 with the section 6 commands; the shas are in section 2. Committed by pathspec. **No kernel has been pushed.** The next step is a separate job, only after the user approves the GPU spend: push `notebooks/exp037_vendor` (kernel id `rainm4/gemma4-exp037-vendor`), then record the push and a new `## Status` line here.

## Status

Built, not pushed; awaiting the user's GPU approval (estimate 0.90-0.93 h, worst case 1.24 h). Zip `dist/EXP-037-vendor.zip` sha256 `a43798560ae9bc1b5e5b8e82805c6a5d43282f14ffffbe6e02a3ee9b08f31a71`.

2026-11-05: the critic's prereg review was needs-work (b60bb81). Its four text fixes are applied in sections 2 to 5 and 7, and the desk checks B1 to B3 are in section 7a. Tree, cohort and notebook are unchanged. Still not pushed: the design may change, and the push waits for the user. The worst case is 1.24 h if no task overruns (+0.07 h per overrun), and each row 2 or row 3 re-run needs its own approval.
