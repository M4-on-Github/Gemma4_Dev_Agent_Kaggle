# EXP-036 — Re-grade of EXP-028 Arms R and RH with the two test-only packages present at grading

**Date:** 2026-11-05
**Type:** zero-GPU re-grade of patches already collected. It runs on a CPU-only Kaggle kernel: no model, no agent, no accelerator, 0.0 L4x4-h. No upload.
**Cohort:** dev-48
**Ladder:** L1 (re-grade of existing patches, the EXP-004 pattern).
  - L0 has been read: EXP-034 §7 item 5 and §9.4, and EXP-035 §9.3. They show that the gap exists and how large it is. They cannot say whether R's patches on the gated tasks are right, because the hidden tests never ran on them.
  - The grade can only be run where the grading environment exists, that is, inside the pinned Kaggle image.
**Pre-registered:** this file is committed before the kernel is built or pushed. Sections 2 to 6 are written blind and are not revised. Results are appended as section 9, which applies section 4 as written.
**Serves:** C-021; C-015 and the D-005 F3 pool, since the critic's Required fix 3 in `experiments/EXP-034/critic.md` asks for this before either moves; the next step named by EXP-035 row 1.
**Relates:**
- EXP-004: tool and pattern. Its E0 re-grade gave 0 flips.
- EXP-028: Arms R and RH, the patches.
- EXP-034: the gated set (`posthoc_gated.py`) and the RFWF definition (`mine.py`).
- EXP-035: the V / H / U classifier (`grader_tests.py`), reused by import.

## 1. Why this, now

- **The two arms were graded without the packages.**
  - The eval notebook has no shim code (EXP-034 §7 item 5).
  - Arms R and RH were graded as run without `inline_snapshot` and `dirty_equals`.
  - Over the six dev-48 arms on disk, 15 tasks have an as-run grader tail with `No module named` for one of the two packages (`experiments/EXP-034/posthoc_gated.json`). R's own tail shows it on 13 tasks, RH's on 14.
  - R and RH resolve 0 of the 15. None of their 96 patches vendors a copy.
  - The older-lineage arms resolve 1 to 2 of the 15, and only through vendored copies. X003 gains 3 under EXP-004's grader-supplied shims.
- **The RFWF readings hang on this.**
  - EXP-035 row 1 fired on R's RFWF group: 16 of 30 unreadable, 11 of them from the missing package.
  - EXP-034 §9.4: 11 of R's 30 RFWF tasks are grader-blocked.
  - Until these patches are graded with the packages present, nobody knows whether the shipped prompt's failures on these tasks are wrong fixes or sandbox artifacts. The same holds for whether a verify stage built on existing tests has anything to catch on them.
- **The tool exists and has been checked once.**
  - `tools/regrade_patches.py` replays stored patches through the harness `Evaluator` with the subprocess sandbox.
  - It drops `tools/compat_shims/{inline_snapshot,dirty_equals}` into `/workspace` only for a task whose workspace imports the package, and not where the patch itself creates the package.
  - EXP-004 v2 re-graded E0 with 0 flips, 11 to 11.
- **The patches on disk are the scored ones.** `runs/EXP-028-armR/patches/*.patch` and `runs/EXP-028-armRH/patches/*.patch` are byte-equal to the `patch` field of `task_results.jsonl` for all 48 tasks in each arm (checked 2026-11-05). R has 42 non-empty patches and 9 resolves; RH has 43 and 10. Each arm's ids equal `experiments/cohorts/dev-48.txt`.
- **Grading timeouts as run.**
  - The eval notebook builds `EvalConfig` with `timeout_seconds` taken from the tree (240 s for R and RH) and no `verification_timeout_seconds`.
  - The harness default for the pytest phase is 300 s (`swegemma/budget.py`, `HarnessLimits.verification_timeout_seconds = 300`; `config.py` lines 180-198).
  - So R and RH were graded with a 240 s command timeout and a 300 s pytest timeout. `regrade_patches.py` sets both to `--timeout` (default 300). §2 adds a separate flag so the re-grade uses 240 and 300.
- **Why a Kaggle kernel and not this machine.** The local Python has no `swegemma` installed, and the per-task test dependencies of the scored grade are the ones in the pinned Kaggle image plus the competition wheelhouse. A local re-grade would change the environment as well as the packages, so it would be a second variable.

## 2. Design

### 2.1 The kernel

- **Kernel and image.** One CPU-only Kaggle kernel, `rainm4/gemma4-exp036-regrade`. This is a new id: it is not EXP-004's kernel, and not the screener's `rainm4/gemma4-exp032-p1`. It uses the same pinned `docker_image` as R's kernel (`notebooks/exp028_armR/kernel-metadata.json`).
- **Inputs:** competition `gemma-4-developer-agent` (`tasks.jsonl`, snapshots, wheels) and dataset `metric/gemma-4-developer-agent-wheelhouse`. No model source.
- **How CPU-only is confirmed:**
  - `kernel-metadata.json` has `enable_gpu: false`, `enable_tpu: false`, no `machine_shape`, no `model_sources` and `enable_internet: false`;
  - the notebook installs only the wheels it needs (`swegemma`, `adk_submission`, `adk_eval_core`), as EXP-004 did, and imports none of `vllm`, `torch`, `litellm` or `google.adk`;
  - after the run, the kernel log's accelerator line is read and quoted in §8.
- **Embedded payloads.**
  - The notebook carries base64 copies of `tools/regrade_patches.py`, the two shims, and zips of R's and RH's 48 stored patches.
  - The gold patches are not embedded. The kernel writes them from the competition's own `tasks.jsonl`.
  - **The built `.ipynb` is not committed**, because it carries agent patches, which are diffs of competition repository code (plan.md:52). The template, the builder and `kernel-metadata.json` are committed.

### 2.2 Four grading passes

Every pass grades all 48 dev-48 ids with the same tool, shims and timeouts. The order is fixed.

| pass | patches graded | purpose |
|---|---|---|
| `R` | R's 48 stored patches | primary |
| `RH` | RH's 48 stored patches | replicate |
| `GOLD` | the 48 gold patches from `tasks.jsonl` | ceiling and validity: can a correct fix pass the gated tests once the packages are there? |
| `BASE` | 48 empty patches | which tests fail before any fix. This is base plus the test patch, because grading always applies the test patch. It is not the repository the agent saw |

**Shims and timeouts.** In every pass, a shim is dropped by the EXP-004 rule: per task, and only when a grep over `/workspace` after the snapshot is extracted finds an import of the package; never when the patch itself creates `<pkg>/__init__.py`. Command timeout 240 s, pytest timeout 300 s, as run (§1).

**Tool changes, before the build.** Committed and recorded in §8:
- a `--verification-timeout` flag, defaulting to `--timeout`;
- a `shims_dropped` field per row: the packages copied in for that task, so the gating can be audited;
- a `--tail-chars` flag (default 6000, as now). This run uses 20000, so the FAILED lists are less often cut.

**Outputs.** Rows go to `runs/EXP-036-regrade/<pass>/regrade.jsonl`, gitignored. The analysis uses the `resolved`, `exit`, `tail` and `shims_dropped` fields.

### 2.3 Definitions

- **Gated task.** One of the 15 tasks in the union over the six arms on disk of an as-run `test_tail` matching `No module named '?(inline_snapshot|dirty_equals)`. That is the regex and set of `experiments/EXP-034/posthoc_gated.py`, and it governs here. **Own-blocked** means the arm's own as-run tail matches (R 13, RH 14); it is secondary. EXP-035's u1 is not used, because it is narrower: unresolved tasks with a non-empty patch only, and any missing third-party module.
- **Flip.** A task whose `resolved` differs between the as-run grade (`task_results.jsonl`) and the re-grade.
  - On a **non-gated task** the grader is unchanged, because no shim is needed there. Any flip there is environment drift, CPU box against GPU box, by construction.
  - On a gated task a False-to-True flip is the shim effect.
  - A **True-to-False flip in either set is a defect to explain**, not a result. §9 lists each one with its exit code and kind (timeout 124, kill -9, apply failure -1, other).
- **G (primary).** For an arm, the number of gated tasks that flip False to True.
- **RFWF after the re-grade.** EXP-034's definition (unresolved, and the final patch touches a gold file), applied to the **re-graded** `resolved` flag.
- **Recomputed EXP-035 table.** EXP-035's per-test classifier (`experiments/EXP-035/grader_tests.py`: snapshot `ast` spans against the test patch's hunks; existing = (b), added or changed = (c)), run on the **re-graded** tails for the RFWF group after the re-grade, with these changes:
  1. **Exit code 2 (collection interrupted) is its own row, C.** It is no longer folded into U.
  2. **Existing is decided from the test-patch hunks** by the snapshot `ast` map, as in EXP-035. It is never decided by a test's name.
  3. **A (b) test that fails at base is excluded as evidence for V.** It fails at base if the `BASE` pass's tail for that task lists it as FAILED or ERROR. If the `BASE` tail for that task is not a complete list (EXP-035 §7.1 corrected count) or ends in a collection error, the base status of its (b) tests is **unknown**. A test of unknown status cannot make a task V on its own.
  4. **No task is V on the strength of an as-run tail.** Only re-graded tails are read. A gated task whose re-graded tail still shows the missing package is unreadable (u1).
  5. **Task categories, first match:**
     - **C:** exit 2.
     - **V:** at least one failing (b) test that is not base-failing and not of unknown status.
     - **H:** the list is complete and every failing test is (c), or (b) and base-failing.
     - **U:** everything else. That covers exit -1, 124 and -9, a partial list, an unlocated test, a missing package, and a (b) failure whose base status is unknown.
  6. **Sensitivity lines:**
     - **S1:** (b) tests whose base status is unknown count as visible;
     - **S2:** base-failing (b) tests that pass under `GOLD` count as visible. They are tests the fix should repair, and the agent could have seen them fail before and after its patch;
     - **S3:** EXP-035's rule as corrected, applied to the re-graded tails, with no base exclusion and with C folded into U.

### 2.4 Cost

- **GPU:** 0.0 L4x4-h.
- **CPU:** EXP-004's two passes took 588 s and 594 s of grading. Four passes at a 20000-character tail are estimated at under 1 h of CPU kernel time, including the wheel install.
- No upload slot is spent.

## 3. Endpoints, fixed in advance

1. **Primary:** G for Arm R: gated tasks that flip False to True, out of 15.
2. **Secondary, resolves:**
   - R and RH resolves as run and as re-graded, on all 48, on the 15 gated tasks and on the 33 non-gated tasks;
   - the same restricted to own-blocked tasks.
3. **Secondary, flips:** False to True and True to False, gated and non-gated, per arm. Non-gated flips are the drift measure.
4. **Secondary, ceiling:**
   - `GOLD` resolves on the 15 gated and the 33 non-gated tasks;
   - on gated tasks, how many R and RH resolves are on tasks that `GOLD` also resolves.
5. **Secondary, best-of-N:** union minus best for {R, RH} after the re-grade, on all 48 and on the gated tasks, against EXP-034 §9.1 (all 48: union 11, best 10, union minus best 1).
6. **Secondary, the recomputed EXP-035 table** for R's and RH's RFWF group after the re-grade:
   - n′, C, V, H and U, with Wilson 95% intervals for the shares;
   - S1, S2 and S3;
   - the number of (b) tests that are base-failing and that have unknown base status.
7. **Audit:**
   - rows per pass (48 expected);
   - `shims_dropped` counts per pass, gated against non-gated;
   - gated tasks whose re-graded tail still shows the missing package.

**Statistics.** Counts are exact, and shares carry Wilson 95% intervals. There is no significance test for G: the re-grade is deterministic given the patch, so the uncertainty lies in what the 15 tasks represent, not in the measurement.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

**Resolves.** These rows are applied to Arm R. The first matching row governs.

| # | outcome | reading |
|---|---|---|
| 0 | Fewer than 48 rows in any pass; or `GOLD` resolves fewer than 12 of the 15 gated tasks; or more than 1 non-gated task flips (either direction) in R or in RH; or any True-to-False flip not explained by a timeout or a kill (exit 124 or -9) | **Infrastructure, no reading.** The re-grade environment does not reproduce the scored grade, or the shims do not make the gated tests runnable. Fix the tool or the shims and re-run. If `GOLD` is the cause, the shims' API coverage is the gap |
| 1 | G >= 3 | **The grading gap hides real fixes.** With the packages present, the shipped prompt's patches resolve 3 or more of the gated tasks, so its as-run score understates its fixes on them. Porting the vendoring section ("Known sandbox gaps" in `submission/prompts/swe_coder.md`) into the shipped v24 tree is worth its own one-variable screen. smoke-8 holds 1 gated task and cannot read this, so the rung is the lead's choice, and §5 states what it can decide |
| 2 | G <= 2 | **The gap costs little with this prompt.** R's patches on the gated tasks are mostly wrong even with the packages present. A vendoring port is worth at most about 2 tasks on dev-48, which is below the paired MDE. It is not a priority on this evidence. The gated RFWF tasks join the readable F3 pool for the table below |

- **Replicate.** RH is read with the same rows at the same thresholds. If RH fires a different row from R, the R reading is reported as **not replicated**.
- **Defects.** Each True-to-False flip explained by exit 124 or -9 is reported, with the task counted as re-graded unresolved and a second count that keeps the as-run True. If that second count alone would move R across G = 3, this is stated.
- **Best-of-N.** If the re-grade raises union minus best for {R, RH} on all 48 to 3 or more, this is stated next to EXP-034's V reading (1). It does not change EXP-034's reading, which was applied as written.

**The recomputed EXP-035 table.** It is applied to R's RFWF group after the re-grade, with n′ its size. U here counts C + U. The thresholds are EXP-035's, scaled to n′ (EXP-035 used 15, 10 and 2/3 at n = 30). The first matching row governs.

| # | outcome | reading |
|---|---|---|
| T0 | n′ < 12, or `BASE` has fewer than 48 rows | **Too few, or no base, to read.** Report counts only |
| T1 | C + U >= n′ / 2 | **No reading.** Even with the packages present, the grader's output cannot say whether existing tests would have exposed the wrong fix. The causes are reported |
| T2 | V >= n′ / 3 | **Existing tests would have exposed the wrong fix in a substantial share.** A verify stage can rest partly on running the existing test file of the edited module after the last edit. Candidate next rung (the lead's call): a smoke-8 screen of that rule |
| T3 | H >= 2/3 of (V + H) | **Mostly hidden only.** A verify stage needs a model-written reproduction that fails before the fix (D-005 F3) |
| T4 | none of the above | **Mixed.** Report V, H, C and U |

- **Replicate.** RH is read the same way at its own n′. A different row means **not replicated**.
- **Sensitivity.** If S1, S2 or S3 alone would move R to a different row, this is stated next to the governing row.

**Prediction (written before anything runs).**
- R: **G = 2** (80% interval 0 to 4), so R re-graded resolves 11 of 48. P(row 1) is about 0.35.
  - The basis: X003 gained 3 of 14 under the same shims, and R's resolve rate on non-gated tasks is 9 of 33.
  - Against that, 11 of R's 13 own-blocked tasks are RFWF, and the agent tested after its last edit on only 3 of those 11 (EXP-034 §9.4).
- RH: G = 2.
- `GOLD`: at least 14 of 15 gated tasks and at least 31 of 33 non-gated tasks. Non-gated drift: 0 flips.
- Table: R n′ about 28, with C about 5, U about 4, V about 4 and H about 15. T3 is the likeliest (about 0.5), then T1 (0.25), T4 (0.15) and T2 (0.1).

## 5. What this does and does not license

**Can decide:**
- how many of the shipped prompt's patches on the 15 gated tasks are correct fixes once the two packages are present at grading;
- whether the dev-48 as-run score of the v24 lineage understates its fixes there;
- whether the RFWF pool's visible / hidden-only split survives once those tasks become readable.

**Cannot decide:**
- **Whether the hidden grader lacks these packages**, and whether the hidden private repositories use them at all. The re-grade puts the packages into our grader, and nothing here observes the hidden one. Ship decisions stay on the as-run grade.
- **Any effect of adding vendoring text to the prompt.** The re-grade supplies the packages at grading. It does not make the agent vendor them, and a prompt that vendors spends turns and characters, which this re-grade does not price. A positive row 1 licenses screening the port, not shipping it.
- Anything about the fixes on non-gated tasks: those are unchanged by construction.
- The visible / hidden split on resolved tasks, or the effect of any verify stage.

No upload, tree change or GPU arm is licensed by any row.

## 6. Exact commands

```bash
# 1. tool change (committed before the build): --verification-timeout, --tail-chars, shims_dropped
python -m pytest -q
# 2. build (writes notebooks/exp036_regrade/kaggle_regrade.ipynb, untracked; it embeds agent patches)
python -I -X utf8 experiments/EXP-036/build_regrade_notebook.py \
    --template experiments/EXP-036/kaggle_regrade_template.py \
    --cohort experiments/cohorts/dev-48.txt \
    --arm R=runs/EXP-028-armR/patches --arm RH=runs/EXP-028-armRH/patches \
    --out notebooks/exp036_regrade/kaggle_regrade.ipynb
# 3. push (kernel id rainm4/gemma4-exp036-regrade, CPU-only metadata); then status, then output into runs/EXP-036-regrade/
# 4. analysis (separate job; script written after this file is committed, committed with the results)
python -I -X utf8 experiments/EXP-036/analyze_regrade.py --regrade runs/EXP-036-regrade \
    --tasks data/raw/tasks.jsonl --snapshots data/local/snapshots --out experiments/EXP-036/aggregates.json
```

**Committed output:** `experiments/EXP-036/aggregates.json`, with counts only. If a `summary.jsonl` is written, it holds the task id plus the booleans resolved-as-run, resolved-re-graded and gated, per arm. The visible / hidden labels are derived from the gold test patch and stay in `runs/` (plan.md:52).

## 7. Defects in this pre-registration, logged after the fact

1. **Where the runtime accelerator check lives.** §2.1 says the accelerator line from the kernel log is quoted in §8. The notebook as built writes that check to `environment.json`, so §9 reads it from there. The check is the same; only its place changed.

---

## 8. Built; first push refused by the guard; pushed after the user's exemption

- **Pre-registration:** d86d09c.
- **Commit 3d9d12c, tool change.** `tools/regrade_patches.py`:
  - `--verification-timeout` (0 means the same as `--timeout`);
  - `--tail-chars` (default 6000, unchanged);
  - a per-row `shims_dropped` list.

  The full test suite passes.
- **Same commit, the kernel files:**
  - template `experiments/EXP-036/kaggle_regrade_template.py`;
  - builder `experiments/EXP-036/build_regrade_notebook.py`;
  - `notebooks/exp036_regrade/kernel-metadata.json`;
  - `notebooks/exp036_regrade/.gitignore`, which keeps the built `.ipynb` out of git.
- **Built 2026-11-05:**
  - `notebooks/exp036_regrade/kaggle_regrade.ipynb`, 279,290 bytes, ignored and not committed.
  - Its `TASK_IDS` equal the 48 dev-48 ids.
  - The embedded zips hold all 48 patches per arm, byte-equal to `runs/EXP-028-arm{R,RH}/patches/`.
  - There is no `RUN_AGENT` parameter, because no agent runs.
- **CPU-only, as built:**
  - the metadata has `enable_gpu: false`, `enable_tpu: false`, `enable_internet: false`, no `machine_shape` and `model_sources: []`, and the builder refuses to build otherwise;
  - the notebook imports none of `vllm`, `torch`, `litellm` or `google.adk`;
  - its first code cell records the Python version, any `/dev/nvidia*` device nodes and `CUDA_VISIBLE_DEVICES` into `environment.json`. That file is the runtime confirmation and is read in §9.
- **Push 2026-11-05: refused by `.claude/hooks/guard_push.py`.**
  - The command was the kernels push with `-p notebooks/exp036_regrade`.
  - The guard's message: `Blocked kernel push: RUN_AGENT is not True. Gold controls (RUN_AGENT = False; cell 5 then sets a 60-minute cap) run only from an exp000 directory.`
  - The guard accepts only notebooks that run the agent, or gold controls from an exp000 directory.
  - It was not worked around: no dummy `RUN_AGENT`, no exp000 directory name. No kernel exists, and 0 GPU-h and 0 CPU-h were spent.
- **After the refusal, the template gained one assert.** It stops the kernel if any gold patch is empty, because GOLD would then silently equal BASE. Locally, all 48 cohort tasks in `data/raw/tasks.jsonl` have a non-empty `patch`. The next build picks the assert up.
- **What the push needs.** A guard exemption recorded in `guard_push.py`. One form: allow a notebook with no `RUN_AGENT` parameter when its `kernel-metadata.json` has `enable_gpu` and `enable_tpu` false, no `machine_shape` and empty `model_sources`. The cohort check stays: `TASK_IDS` against `**Cohort:** dev-48` already passes. Changing the guard is outside the experimenter's paths and is the lead's or the user's decision.

- **The notebook that was pushed.** It was rebuilt in the same command as commit 1c8e9c8 (2026-11-05 14:43:07 UTC), after the assert was added. Nothing the build reads has changed since then: the template, `tools/regrade_patches.py`, the shims and the metadata. Checked before the push:
  - the assert is in the built notebook;
  - the embedded tool and both shims are byte-equal to the committed files;
  - `TASK_IDS` equal dev-48.

  The notebook is 279,415 bytes, sha256 `73df67c8453bd2ac31abf77aa6f6d6dc59590666b92a59d76e90020310e9686e`, and is not committed.
- **sha256 of the embedded patch zips:**
  - R: `59d3c61b2831a715f1936041b941eb835b4bda5a9d9672e05bc7bfb6cbe08613`
  - RH: `edd7b004075926eec595692eff59598a5eebf81ab6476d12d8c06f4d2e0708c8`
- **Guard exemption.** Commit 45996cd records the user's decision of 2026-11-05 in `knowledge/user-decisions.md`. `guard_push.py` now passes a notebook that has no `RUN_AGENT` parameter when its metadata requests no GPU, no TPU, no machine shape and no model source. The committed pre-registration with a readings section is still required. The cohort check is skipped for such notebooks. `TASK_IDS` equal dev-48 anyway.
- **Push 2026-11-05 15:13:59 UTC:** `Kernel version 1 successfully pushed.` The kernel is `rainm4/gemma4-exp036-regrade`, version 1. Its status right after the push was `KernelWorkerStatus.RUNNING`. The kernel metadata is unchanged and CPU-only.

- **Downloaded 2026-11-05, after the lead reported COMPLETE (16:10 UTC).** The download went to `runs/EXP-036-regrade/`, and the nested `runs/EXP-036-regrade/` was moved up a level. Nothing from the bundle was executed. Its `tools/` copy is left unread.
- **Kernel wall-clock:** the last log entry is at 2608.6 s, so **0.72 h of CPU and 0.0 GPU-h**.
  - Wheel install took 75 s.
  - Grading took 697.7 s for R, 713.4 s for RH, 475.4 s for GOLD and 547.3 s for BASE.

## Status

**COMPLETE.** Kernel `rainm4/gemma4-exp036-regrade` v1 has been downloaded and analysed (§9). Nothing is running.

---

## 9. Results, 2026-11-05. Section 4's readings applied as written.

**Command:**

```
python -I -X utf8 experiments/EXP-036/analyze_regrade.py --regrade runs/EXP-036-regrade --tasks data/raw/tasks.jsonl --snapshots data/local/snapshots --out experiments/EXP-036/aggregates.json --summary experiments/EXP-036/summary.jsonl --rows runs/EXP-036-regrade/rows.jsonl
```

- Every number below is from `experiments/EXP-036/aggregates.json`, apart from the kernel times in §8.
- `experiments/EXP-036/summary.jsonl` holds, per task, the id plus booleans: gated, and resolved as run and re-graded for R and RH.
- The per-task V / H labels stay in `runs/EXP-036-regrade/rows.jsonl`.

### 9.1 Environment and row 0

- **No accelerator was attached.** `environment.json` shows Python 3.12.13, no `/dev/nvidia*` nodes, no `nvidia-smi` on the path, `CUDA_VISIBLE_DEVICES` unset and 4 CPUs. The log line reads `accelerator: none (CPU only)`.
- **All four passes ran in full:**
  - all 41 wheels installed;
  - every pass had 48 patch files, so the gold-patch assert passed;
  - every pass exited 0;
  - each pass wrote 48 rows, and each pass's ids equal dev-48.
- **The shims went where expected.** They were copied into the workspace on 26 tasks in every pass: all 15 gated tasks and 11 non-gated ones. No gated tail still shows the missing package in any pass.
- **Exit codes:**

  | pass | 0 | 1 | 2 | -9 |
  |---|---|---|---|---|
  | R | 12 | 29 | 6 | 1 |
  | RH | 15 | 26 | 6 | 1 |
  | GOLD | 43 | 4 | 1 | — |
  | BASE | 1 | 40 | 6 | 1 |

  The one -9 is `rich_3480` in R, RH and BASE, killed after about 253-267 s. As run it was -1 in R and 124 in RH, and it was unresolved in both.
- **Tails at the 20,000-character cap:** 6 in each of R, RH and BASE.

**Row 0 does not fire:**
- every pass has 48 rows;
- GOLD resolves **15 of the 15** gated tasks;
- non-gated flips: **0** in R and **0** in RH, in either direction;
- resolved-to-unresolved flips: **0** in both arms. Every as-run resolve (R 9, RH 10) is still resolved.

### 9.2 Resolves, applying rows 1 and 2

| | as run, 48 | re-graded, 48 | as run, 15 gated | re-graded, 15 gated | as run, 33 non-gated | re-graded, 33 non-gated | own-blocked as run → re-graded | G (gated, unresolved → resolved) |
|---|---|---|---|---|---|---|---|---|
| R | 9 | **12** | 0 | 3 | 9 | 9 | 0 → 3 of 13 | **3**: `fastapi_13207`, `fastapi_14297`, `fastapi_14360` |
| RH | 10 | **15** | 0 | 5 | 10 | 10 | 0 → 5 of 14 | **5**: the same three plus `fastapi_14459`, `fastapi_14605` |
| GOLD | — | 43 | — | 15 | — | 28 | — | — |
| BASE (empty patch) | — | 1 (`requests_6644`) | — | 0 | — | 1 | — | — |

- **R, the primary: G = 3, so row 1 fires. The grading gap hides real fixes.** With the two packages present, the shipped v24 prompt's patches resolve 3 of the 15 gated tasks, and GOLD resolves all 3 of them. Porting the vendoring section ("Known sandbox gaps") into the v24 tree is worth its own one-variable screen. smoke-8 holds 1 gated task and cannot read this, so the rung is the lead's choice.
- **RH, the replicate: G = 5, row 1. Replicated.** All 5 of its gated flips are on tasks GOLD resolves.
- **No defects** under §4: there are no resolved-to-unresolved flips.
- **Best of N for {R, RH} after the re-grade:**
  - all 48: union 16, best 15, union minus best **1**, the same as EXP-034's as-scored 1 (union 11, best 10);
  - gated: union 5, best 5, union minus best 0.

  Union minus best is not 3 or more, so there is nothing to state against EXP-034's reading.

**Against the prediction:**
- R: predicted G = 2 (80% interval 0 to 4) and 11 of 48 re-graded. Observed G = 3 and **12**, inside the interval, one task above the point.
- P(row 1) had been put at 0.35, and row 1 fired.
- RH: predicted G = 2, observed **5**.
- GOLD: predicted at least 14 of 15 gated and at least 31 of 33 non-gated. Observed 15 of 15 gated, **28 of 33** non-gated, so the non-gated part of the prediction **missed**. The cause is in §9.4.
- Non-gated drift: predicted 0, observed 0.

### 9.3 The recomputed EXP-035 table, applying rows T0 to T4

RFWF after the re-grade: R n′ = 27 (EXP-034 found 30 as run, and 3 of those are now resolved); RH n′ = 22 (27 as run, 5 now resolved).

**Base status.** It is known on 40 of 48 tasks: the BASE tail is complete, has no collection error, and exits 0 or 1.

**Existing (b) tests among the failures:**

| arm | base-pass | base-fail (excluded from V) | unknown |
|---|---|---|---|
| R | 7 | 4 | 0 |
| RH | 4 | 4 | 0 |

**Main table (Wilson 95% intervals for shares of n′):**

| arm | n′ | C (exit 2) | V | H | U | C + U | row |
|---|---|---|---|---|---|---|---|
| R | 27 | 6 [0.11, 0.41] | 2 [0.02, 0.23] | 19 [0.52, 0.84] | 0 [0, 0.13] | 6 | **T3** |
| RH | 22 | 5 [0.10, 0.43] | 1 [0.01, 0.22] | 14 [0.43, 0.80] | 2 (`u5`, one at exit -9) | 7 | **T3** |

**Row checks, R:**
- T0: n′ = 27, at least 12, and BASE has 48 rows, so T0 does not fire.
- T1: C + U = 6, below 13.5.
- T2: V = 2, below 9.
- T3: H = 19, at least 2/3 × 21 = 14. **T3 fires.**

**Row checks, RH:**
- C + U = 7, below 11.
- V = 1, below 7.3.
- H = 14, at least 2/3 × 15 = 10. **T3, replicated.**

**Reading T3: mostly hidden only.** On the right-file-wrong-fix tasks the grader can now read, the failing tests are almost all tests the test patch adds or changes. The fixes that would catch them need a model-written reproduction that fails before the fix (D-005 F3). Running the existing test file of the edited module would have exposed the wrong fix on 2 of 27 (R) and 1 of 22 (RH).

**By gated status:**
- R gated: C 4, H 6. R non-gated: C 2, V 2, H 13.
- RH gated: C 3, H 5. RH non-gated: C 2, V 1, H 9, U 2.

**Sensitivity: no line moves either arm off T3.**
- S1: no (b) test has unknown base status, so S1 equals the main table.
- S2: no base-failing (b) test passes under GOLD, so S2 equals the main table.
- S3, the EXP-035 rule with C folded into U:
  - R: V 4, H 17, U 6, row T3;
  - RH: V 3, H 12, U 7, row T3.

**Against the prediction:** R n′ about 28 with C 5, U 4, V 4 and H 15, and T3 likeliest at about 0.5. **T3 held.** Observed n′ 27, C 6, U 0, V 2, H 19.

### 9.4 Things that do not fit, post hoc

These lines are not pre-registered.

**1. Six tasks where the grade does not depend on the patch.**
- On `httpx_3672`, `requests_6644`, `requests_7205`, `requests_7309`, `requests_7315` and `requests_7427`, GOLD and BASE end with the same exit code, the same count line and the same failing test ids.
  - `requests_6644` passes with an empty patch.
  - The other five fail even with the gold patch.
- So on the Kaggle subprocess grader, these six dev-48 tasks do not measure the patch.
- All six EXP-034 arms show the same pattern on these tasks as run: `requests_6644` resolved, the other five unresolved. So this is not drift from the CPU kernel.
- This is the requests (pytest-httpbin) and httpx package-shadowing classes already recorded for the Kaggle gold control in `experiments/README.md` §1 (EXP-000 push6 cause table). dev-48 removed only the Docker gold-control failures.
- The mechanism on these six tasks was not checked here. Two of the five gold failures show the installed package's path in the tail.
- **Consequences:**
  - The 5-of-33 non-gated GOLD miss in §9.2 is entirely these five tasks.
  - Excluding the six, R goes from 8 to 11 of 42 and RH from 9 to 14 of 42.
  - Paired comparisons on dev-48 are unaffected: every arm gets the same constant on these six.
  - Absolute dev-48 rates carry one free resolve and five that are impossible.
- `httpx_3672` is one of R's and RH's C tasks (exit 2).

**2. The C tasks are mostly the patch's own collection errors.**
- The gated C tasks fail to collect with errors other than the missing package:
  - R: `TypeError`, `SyntaxError` and two `ImportError`s, on `fastapi_14262`, `fastapi_14605`, `fastapi_14609` and `fastapi_15030`;
  - RH: a `ModuleNotFoundError` for a repository submodule (`fastapi._compat.v1`, not one of the two packages) and the same `TypeError` and `ImportError` tasks.
- They are C by §2.3 rule 1 and were not classified further.

**3. The kills on `rich_3480`.** The -9 there occurs in BASE as well, so this task's test file does not finish on the 4-CPU box with these packages.

### 9.5 What this licenses (from §5, unchanged)

- Row 1 licenses screening a vendoring port, not shipping it.
- The re-grade cannot say whether the hidden grader lacks these packages, and it does not price what the vendoring text costs in turns.
- Ship decisions stay on the as-run grade.
- No upload, tree change or GPU arm is licensed.
