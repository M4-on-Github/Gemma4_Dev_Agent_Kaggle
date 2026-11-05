# EXP-034 — Which architecture families can pay at all: the best-of-N ceiling from patches we already have, and whether the agent's own test runs carry a signal

**Date:** 2026-11-05
**Type:** zero-GPU trace mining over runs already on disk. No kernel, no upload, 0.0 L4x4-h.
**Cohort:** dev-48 (the six dev-48 arms on disk, intersected on task id; no new run)
**Ladder:** L1 (trace mining). L0 is the dispatch itself: three families (best-of-N with selection, orchestrator with workers, role pipeline with a verifier) are to be chosen between by benchmark, and these two questions decide, before any GPU hour, which of them can pay at all.
**Pre-registered:** this file is committed before anything in sections 3 to 5 is computed. Sections 2 to 6 are written blind and are not revised; results are appended as section 9, which applies the readings as written.
**Serves:** the architecture-family choice (lead's dispatch, 2026-11-05); D-004.
**Relates:** EXP-030 L1b (`experiments/EXP-030/l1b_trace_mining.py`; its "patch touches a gold file" measure defines the right-file-wrong-fix group here), EXP-028 (Arms R and RH, the Q2 traces), EXP-004 (the shim re-grade of EXP-003).

## 1. Why this, now

A best-of-N family pays only if different draws resolve different tasks and something we can compute without the gold tests picks the right draw. Both facts are partly on disk already: six dev-48 arms with patches and traces exist, so the ceiling (the union) and a set of free selector proxies can be read at zero GPU. A verifier stage pays only if a check the agent can run tells right patches from wrong ones. The EXP-028 traces record every test or script run and its output, so whether the last visible test result before the patch was final was a pass or a fail can also be read at zero GPU.

What is already known before this file is committed: the per-arm resolve counts (README §3) and the EXP-030 L1b aggregates (Arm R: 30 of 39 unresolved patches touch a gold file). Not computed: any union, curve, always/some/none split, proxy table, or any Q2 count.

## 2. Design

### 2.1 Arms (every dev-48 arm with patches and traces on disk)

Six arms are on disk with `task_results.jsonl` (patches) and 48 traces each. All six use the same 48 task ids, which are exactly `experiments/cohorts/dev-48.txt` (checked during orientation: intersection 48, all in the cohort file; the gold-control exclusion is already applied to every one). EXP-024 and EXP-027 have no dev-48 run on disk (EXP-024 was superseded by EXP-025; EXP-027 was LB-only). The smoke-8 runs (EXP-002, EXP-020) are not dev-48 arms and are not used.

| key | run | config in one line |
|---|---|---|
| E0 | `runs/E0-dev48-baseline/...` | own prompt (E0 version), 4.5 min / 45 calls / 70 turns / 300 s, T 0.2, top_k 64, max_output 4096, thinking_budget 256 |
| X003 | `runs/exp003_public_budget_dev48/...` | own prompt + edit-by-call-12 rule, 8 min / 28 / 80 / 240 s, T 0.2, top_k removed, 8192 / 4096 (8 changes vs E0) |
| A25 | `runs/exp025_armA/...` | own prompt as in `submission/` on 2026-10-26 (the tree before #9), 4.5 min / 64 / 96 / 300 s, T 1.0, top_k 64, 8192 / 4096 |
| B25 | `runs/exp025_armB/...` | A25 + the two EXP-024 prompt edits (recovery ladder), nothing else; the tree of submission #9 |
| R | `runs/EXP-028-armR` | rank-3 v24 bundle (the shipped tree, = submissions #11/#12), 8 min / 28 / 80 / 240 s, T 1.0, top_k 64, 8192 / 4096 |
| RH | `runs/EXP-028-armRH` | R + the 942-char lost-edit recovery section, nothing else |

**Resolved flags.** Each arm's own `resolved` field, except X003, which uses the EXP-004 v2 shim re-grade (`runs_download/exp004_regrade_v2/.../regrade.jsonl`; 3 flips False to True, 9 to 12) because every later arm was graded with the shims present. E0 had 0 flips. The as-scored X003 flags are reported as a sensitivity line.

**Prompt families.** No two arms on disk differ only in sampling or caps, so a strict "N draws of one config" subset does not exist. The nearest are two families whose members differ by one prompt addition each:
- **V (the shipped v24 family):** {R, RH}.
- **O (our own prompt lineage):** {E0, X003, A25, B25}; A25/B25 are a one-edit pair, E0 and X003 differ from them in caps and sampling as well.

### 2.2 Q1 measurements

**Q1a.** Per arm resolves; union of resolves over all six arms; union minus the best single arm. The same for V and for O. The curve: for k = 1..6, the expected union size averaged over all C(6, k) subsets of size k (and for V, k = 1..2; for O, k = 1..4).

**Q1b.** Over all six arms: tasks resolved in every arm, in some but not all, in none.

**Q1c. Free selector proxies.** The unit is a (task, arm) pair with a non-empty patch. Each proxy is a 2x2 against resolved, with counts.
1. **diff match:** the arm's normalised patch equals another arm's normalised patch for the same task. Normalisation: per file, keep only `+`/`-` body lines (not `+++`/`---` headers), strip each line of whitespace, drop empty lines and lines that start with `#` after stripping, keep the sign; each hunk becomes a tuple of its kept lines with its file path; hunks with no kept lines are dropped; the patch is the sorted tuple of hunks.
2. **majority file set:** the arm's set of touched files equals a file set that at least 4 of the 6 arms produce for the task (strict majority of six; arms with empty patches count as not matching).
3. **smaller patch:** lines changed (count of `+`/`-` body lines) strictly below the task's median over the arms with non-empty patches.
4. **submit before cap:** the trace's last tool call is `submit_patch`, and `calls_cap_hit`, `time_cap_hit` and `timeout_hit` are all false in the arm's `summary.jsonl` regenerated with the current `tools/analyze_traces.py` under the arm's own caps. The turn cap has no separate flag; a turn-cap ending that is not also flagged would be counted as "before cap" and is disclosed if seen.

**Selector score.** For a proxy, per task: the candidate set is the arms whose patch is non-empty and proxy-true; if that set is empty, all arms with a non-empty patch; if none, the task scores 0. The task scores the mean of `resolved` over the candidate set (uniform random tie-break, so the score is an expectation). The selector's score is the sum over the 48 tasks. Baselines: **random arm** = sum over tasks of the mean of `resolved` over all six arms (= the mean per-arm resolve count); **random non-empty** = the same over non-empty patches only; **union** = the oracle from Q1a. Gain over random = selector score minus random arm.

### 2.3 Q2 measurements (Arm R primary, RH replicate)

**Edit call.** `edit_file` or `write_file` whose path (leading `./` and `/workspace/` style prefixes removed) is a file in the task's final patch; or `run_command` whose command contains a final-patch path and either `sed -i`, `perl -i`, `.write(`, or a redirection `>`/`>>` directly onto that path. First edit and last edit are the first and last such calls. A task with no recognised edit call is its own category ("no edit found").

**Test run.** A `run_command` whose command matches `pytest`, `py.test` or `unittest` (**suite run**), or runs `python`/`python3` on a `.py` file (**script run**). `python -c` one-liners are not test runs; their count is reported.

**Reproduction script.** A `.py` path the agent created (by `write_file`, or a heredoc or redirection `cat ... > X.py` in `run_command`) that is not in the final patch and is later run as a script run.

**Result of a test run**, from the observation JSON (`status`, `exit_code`, `stdout`, `stderr`, `error_message`, `details`):
- **error:** the run did not execute the check: a timeout; `can't open file` / `No such file or directory` for the script; a `SyntaxError`, `ModuleNotFoundError` or `ImportError` traceback; pytest `ERROR collecting`, `no tests ran`, `collected 0 items`, `file or directory not found`, or `usage:` errors.
- **fail:** otherwise, a pytest summary line with `failed` or `error(s)` counts, or `FAILED` lines; or a non-zero exit code; or exit 0 with failure text on stdout/stderr (`FAIL`, `FAILED`, `AssertionError`, `Traceback`, `Error:`, `BUG`, `not fixed`, `mismatch`, case-sensitive word match) — the last is counted as **fail (text)** and reported separately.
- **pass:** otherwise (exit 0, a pytest summary with `passed` and no failed or error).

**Last visible result** of a task: the result of the last test run strictly after the last edit call; **none** if no test run follows the last edit.

**Counts reported, over all 48, resolved, unresolved, and the right-file-wrong-fix group (RFWF = unresolved and the final patch touches a gold file, the EXP-030 L1b definition, 30 in R):**
- last visible = pass, unresolved (tests cannot see the bug);
- last visible = fail, unresolved, split by the ending (calls cap, time cap or session timeout, ended by `submit_patch`, other);
- last visible = error; none after the last edit; no test run anywhere in the trace; no edit found;
- reproduction scripts: tasks with one; of those, run before the first edit with result fail (a usable oracle), run before the first edit with result pass or error, or only run after the first edit.

**Hand check.** Ten test-run observations from Arm R, drawn with `random.Random(34)` from the set of last-visible test runs (stratified: up to 4 classified pass, 4 fail, 2 error), are read by hand and classified before seeing the tool's label; the agreement k/10 is reported, and every disagreement is described by kind (not by text).

## 3. Endpoints, fixed in advance

1. Q1 primary: **union minus best single arm** over all six arms on the 48-id intersection, resolved flags as in §2.1.
2. Q1 secondary: the same for V and O; the curve; the always/some/none split; the proxy 2x2s and selector scores; the best proxy's gain over random arm.
3. Q2 primary: in Arm R's RFWF group, the number whose last visible result is pass, and the number whose last visible result is fail (fail includes fail (text)).
4. Q2 secondary: the same in RH; the full category table; the reproduction-script counts; hand-check agreement.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

**Q1.**
- **Q1-low:** union minus best below 4 tasks on the intersection: best-of-N cannot be read on dev-48 or on the board (MDE 4 tasks) and is **ranked last** among the three families.
- **Q1-stays:** 4 or more: best-of-N **stays**, and the best proxy's gain over random arm is the number a selector has to beat.
- The reading is applied to endpoint 1 (all six arms). V and O are reported with the same threshold; if the V or O reading differs from the all-arm reading, both are stated and the family number is named as the closer picture of N draws of one config. The X003 sensitivity line does not change which reading fires unless it alone moves endpoint 1 across 4, in which case that is stated.

**Q2** (on Arm R's RFWF group; "most" = more than half of the group):
- **Q2-pass:** most RFWF tasks end on a visible pass: a same-model verifier has **no signal from existing tests**, and a verify stage must rest on a model-written reproduction that fails before the fix.
- **Q2-fail:** most RFWF tasks end on a visible fail: the constraint is **budget**, and a verify loop or a raised call cap is the direct lever.
- **Q2-neither:** neither pass nor fail is a majority (for instance, most end with no test after the last edit): neither reading fires; the finding is stated as the largest category, and what it implies for a verify stage is left to the lead.
- RH is a replicate: if RH's RFWF group gives a different reading, the R reading is reported as **not replicated**.

## 5. What this does and does not license

**Can decide:** whether best-of-N has room on our own draws to be measurable at all, the size of the ceiling, how far free proxies get towards it, and whether the agent's own visible test results separate right from wrong patches on the RFWF group. **Cannot decide:** the effect of any architecture; whether N draws of the shipped config would reach the all-arm union (the arms are not draws of one config); anything about the hidden set. Proxies are fitted on these 48 tasks with nothing held out; a selector built from them needs its own arm. No upload and no tree change is licensed by any reading.

## 6. Exact commands

```bash
# summaries under each arm's own caps, written outside the arm dirs (runs/ is gitignored)
python tools/analyze_traces.py runs/E0-dev48-baseline/runs/E0-dev48-baseline --out runs/EXP-034/E0 --cap-minutes 4.5 --max-calls 45
python tools/analyze_traces.py runs/exp003_public_budget_dev48/runs/EXP-003-public-budget-dev48 --out runs/EXP-034/X003 --cap-minutes 8 --max-calls 28
python tools/analyze_traces.py runs/exp025_armA/runs/EXP-025-editfix-dev48-armA-baseline --out runs/EXP-034/A25 --cap-minutes 4.5 --max-calls 64
python tools/analyze_traces.py runs/exp025_armB/runs/EXP-025-editfix-dev48-armB-editfix --out runs/EXP-034/B25 --cap-minutes 4.5 --max-calls 64
python tools/analyze_traces.py runs/EXP-028-armR --out runs/EXP-034/R --cap-minutes 8 --max-calls 28
python tools/analyze_traces.py runs/EXP-028-armRH --out runs/EXP-034/RH --cap-minutes 8 --max-calls 28
# the mining script (committed with the results); aggregates only, plus ids-and-booleans summary.jsonl
python -I -X utf8 experiments/EXP-034/mine.py --tasks data/raw/tasks.jsonl --out experiments/EXP-034/aggregates.json --summary experiments/EXP-034/summary.jsonl
```

Committed output: `aggregates.json` (counts only) and `summary.jsonl` (task id and booleans per arm: resolved, non-empty patch, the four proxies, and for R and RH whether a test ran after the last edit and whether it passed or failed). No task text, paths, snippets, or per-task gold-derived field (the RFWF membership stays aggregate-only), per plan.md:52.

## 7. Defects in this pre-registration, logged after the fact

1. **(2026-11-05, after the run) The hand-check pool was too small for the stratified draw.** Arm R has only 15 last-visible test runs (13 pass, 1 fail, 1 error), so the §2.3 draw gave 6 items, not 10. Deviation: 4 more were drawn with `random.Random(34)` from every other R test run labelled fail, fail (text) or error (3 fail, 1 error, from tasks not already drawn), to reach the 10 the dispatch asks for. The extra four test the classifier, not the last-visible endpoint.
2. **(2026-11-05) `SUITE_RE` matches `unittest` inside a script's own text** (for example `from unittest.mock import ...` in a heredoc), so some script runs are typed as suite runs. Seen once in the hand check, where the result label was still right.
3. **(2026-11-05) A script that crashes on its own mistake is labelled fail, not error.** §2.3 calls a run "error" only for a missing file, a timeout, or a syntax or import error. A script that raises `TypeError` or `AttributeError` because it misuses the API is "fail" by the rule, though the check did not run. Two of the ten hand-checked items are of this kind. This inflates the fail counts and the "before_fail" (usable oracle) count. It cannot move any last-visible fail count by more than the 1 that exists.
4. **(2026-11-05) The "none after the last edit" category does not see `python -c` one-liners or `python - <<EOF` stdin scripts**, by the §2.3 definition. Their size is reported in §9 as a post-hoc line. It does not change the definitions.
5. **(2026-11-05, found by the critic, `experiments/EXP-034/critic.md` audit 2; verified by me) The grading statement in §2.1 is false.** §2.1 says X003 needs the re-grade "because every later arm was graded with the shims present". That is wrong: no arm on disk was graded with the shims present except in the EXP-004 re-grade.
   - **The eval notebook.** `notebooks/kaggle_eval_l4x4.py` has no shim code: a grep for `compat_shims`, `inline_snapshot` and `dirty_equals` finds nothing.
   - **Grading environment of each arm:**

     | arm | resolved flags used | graded |
     |---|---|---|
     | E0 | as run | without the shims. EXP-004 re-graded it with the shims and found 0 flips, so the flags are the same under either grader |
     | X003 | the EXP-004 v2 re-grade | with the shims, gated per task (3 flips False to True) |
     | A25, B25, R, RH | as run | without the shims |

   - **Tasks hit.** The as-run grader tail shows `No module named` for one of the two packages on the following number of tasks in each arm: E0 5, X003 14, A25 8, B25 8, R 13, RH 14. Over the six arms that is 15 distinct tasks (the "gated" tasks).
   - **Resolves on the gated tasks.**
     - E0 (2), A25 (2) and B25 (1) resolve them only with patches that vendor a copy of the package (`+++ b/inline_snapshot/...` or `+++ b/dirty_equals/...`).
     - X003 resolves 3 under the re-grade, none as run.
     - R and RH resolve 0 of the 15, and none of their 96 patches vendors.
   - **Effect on Q1.** The union of 17 therefore mixes two grading environments.
   - **Effect on the readings: none.** They are applied as written. The uniform as-scored line (X003 as scored) also gives union minus best 5. §9.4 gives the non-gated numbers post hoc.
   - Command: `python -I -X utf8 experiments/EXP-034/posthoc_gated.py --out experiments/EXP-034/posthoc_gated.json` (counts only).

## 9. Results (2026-11-05). Applies section 4 as written.

Commands as §6, run 2026-11-05 after the pre-registration commit f5f387a. GPU: **0.0 L4x4-h** (no kernel). Output: `experiments/EXP-034/aggregates.json` (counts), `experiments/EXP-034/summary.jsonl` (48 rows, task id and booleans), script `experiments/EXP-034/mine.py`. Intersection: **48 ids**, all six arms, all in `cohorts/dev-48.txt`.

### 9.1 Q1, the best-of-N ceiling

| set | per arm | union | best single | union minus best | expected union for k = 1, 2, 3, 4, 5, 6 |
|---|---|---:|---:|---:|---|
| all six | E0 11, X003 12 (shim re-grade), A25 11, B25 9, R 9, RH 10 | **17** | 12 | **5** | 10.33, 12.73, 14.20, 15.27, 16.17, 17 |
| V {R, RH} | 9, 10 | 11 | 10 | 1 | 9.5, 11 |
| O {E0, X003, A25, B25} | 11, 12, 11, 9 | 16 | 12 | 4 | 10.75, 13.33, 15.0, 16 |
| all six, X003 as scored (9) | as above, X003 9 | 16 | 11 | 5 | 9.83, 12.0, 13.35, 14.33, 15.17, 16 |

Always / some / none over the six arms: **6 / 11 / 31**. Histogram of arms resolving a task: 0: 31, 1: 5, 2: 1, 3: 2, 4: 2, 5: 1, 6: 6. The pool a selector could act on is the **11** "some but not all" tasks.

**Selector proxies** over the 202 (task, arm) pairs with a non-empty patch. Each 2x2 is given as proxy-true resolved / unresolved and proxy-false resolved / unresolved. Scores are expected tasks out of 48.

| proxy | true: res / unres | false: res / unres | selector score | vs random arm (10.33) | vs random non-empty (12.22) | union |
|---|---|---|---:|---:|---:|---:|
| diff match | 36 / 25 | 26 / 115 | 12.38 | +2.05 | +0.17 | 17 |
| majority file set (>= 4 of 6) | 37 / 46 | 25 / 94 | 12.50 | +2.17 | +0.28 | 17 |
| smaller patch | 14 / 51 | 48 / 89 | 12.00 | +1.67 | -0.22 | 17 |
| **submit before cap** | 35 / 50 | 27 / 90 | **13.33** | **+3.00** | **+1.12** | 17 |

Of the +3.00, +1.88 comes from preferring any non-empty patch (random non-empty minus random arm). One proxy-true pair had `n_turns` >= 79, a possible turn-cap ending counted as "before cap" (§2.2 item 4).

**Reading: Q1-stays fires** on endpoint 1 (union minus best = 5, which is at least 4). Best-of-N stays, and **the number a selector has to beat is +3.0 tasks over a random arm** (the submit-before-cap proxy alone scores 13.33 of 48). The X003 sensitivity line also gives 5, so it does not move the reading.

**The family readings differ, which §4 requires stating.**
- V (R and RH, the closest thing on disk to two draws of the shipped config) gives union minus best = **1**. By the same threshold that is Q1-low.
- O gives 4.

The V number is the closer picture of N draws of one config. The all-arm 5 comes from arms that differ in prompt, caps and sampling, so most of the measured ceiling is diversity across configs, not across draws.

### 9.2 Q2, the visible test signal (Arm R; RH replicate)

Arm R, last visible result after the last edit. Fail includes fail (text), but no fail (text) occurred as a last-visible result.

| group | n | pass | fail | error | none after last edit | no edit found | no test run anywhere |
|---|---:|---:|---:|---:|---:|---:|---:|
| all | 48 | 13 | 1 | 1 | 27 | 6 | 22 |
| resolved | 9 | 6 | 0 | 0 | 3 | 0 | 3 |
| unresolved | 39 | 7 | 1 | 1 | 24 | 6 | 19 |
| **RFWF** | **30** | **7** | **1** | **1** | **21** | 0 | 16 |

- **Last visible pass and unresolved (tests cannot see the bug): 7.** All 7 ended by `submit_patch`, and all 7 are RFWF.
- **Last visible fail and unresolved: 1.** It ended by the time cap or session timeout.
- **RFWF endings:** calls cap 11, `submit_patch` 16, time cap or timeout 3.
- **Reproduction scripts (R, all 48).** 21 tasks wrote and ran one:
  - run before the first edit and failed (a usable oracle): **6**;
  - run before the first edit without failing: 6;
  - run only after the first edit: 9.

  27 tasks had none. In RFWF the same split is 3 / 3 / 6, with 18 none. The oracle counts of 6 and 3 include scripts that crashed on their own mistakes (§7 item 3), so they are upper bounds.
- **A last visible pass separates weakly:** 6 of the 13 last-pass tasks resolved, against 9 of 48 overall.

**RH replicate.**
- RFWF (n = 27): pass 4, fail 1 (ended by submit), error 0, none 22. No test run anywhere: 21.
- All 48: pass 7, fail 1, none 35, no edit found 5, no test run anywhere 36.
- Reproduction scripts: 7 tasks only, oracle 2.

**Hand check (§2.3, with the §7 item 1 top-up).** 10 R observations were classified by hand before the tool's label was read: **8 of 10 agree**. Both disagreements are the §7 item 3 kind: a script that crashed on its own API misuse, labelled fail by the tool and error by hand. One further item was typed suite instead of script (§7 item 2), with the right label.

**Reading: Q2-neither fires.** In Arm R's RFWF group neither pass (7 of 30) nor fail (1 of 30) is a majority. **Replicated in RH:** pass 4, fail 1, none 22 of 27, the same reading.

The largest category is **none after the last edit: 21 of 30**. 16 of the 30 ran no test or script anywhere in the trace. The finding, stated as §4 asks:
- On the right-file-wrong-fix tasks the agent almost never checks its final patch, so the traces cannot say whether existing tests would have seen the bug.
- The record shows neither "tests cannot see it" (Q2-pass) nor "the agent knew and ran out of budget" (Q2-fail).
- What that implies for a verify stage is left to the lead.

**Post hoc, not pre-registered (§7 item 4).**
- Of R's 27 "none" tasks, 17 have nothing but `submit_patch` or `get_status` after the last edit, and 7 have a `python -c` after it. Among the 21 RFWF "none" tasks, 4 have one.
- R makes 76 `python -c` calls in all and no stdin heredocs.
- RH makes 18 `python -c` calls and 120 stdin heredocs; its recovery section routes edits through stdin heredocs. 13 of RH's 22 RFWF "none" tasks have a heredoc after the last edit. It may be an edit or a check; this analysis does not separate the two.

### 9.3 Not verified

- **Comment stripping:** the diff normalisation drops a comment line only when it starts with `#`. Patches that differ only in a docstring still count as different.
- **Turn cap:** it has no flag in `summary.jsonl`. Endings are taken from `calls_cap_hit`, `time_cap_hit`, `timeout_hit` and the trace's last call.
  - *Reconciled after the run against the harness `error` field in `task_results.jsonl`.* R has 4 "turns budget (80 turns)" endings, which matches EXP-028. Three are counted here as calls cap, because the calls flag is set too. One is counted as `submit_patch`; it is the single proxy-true pair with `n_turns` >= 79. That task is unresolved and RFWF, and its last visible result is error.
  - So R's RFWF "submit 16" is really 15 submits and 1 turn-cap ending. The submit-before-cap proxy holds one unresolved pair that should be false. The 7 last-pass unresolved tasks are not affected.
  - R's 6 session timeouts are 5 counted here as time cap and 1 counted as calls cap. RH has 1 turn-budget ending, counted as calls cap. None of this moves either reading.
- **Grading:** resolved flags come from each run's own grading (X003 re-graded), and grader timeouts differ between arms (300 s vs 240 s).
- **Edit detection:** it found an edit in every non-empty patch in R and RH. A check for later edits written through `write_text(` or `open(..., "w")` found 0 such tasks in R and 1 in RH.

### 9.4 Post hoc, not pre-registered: the gated tasks (critic Required fix 2, 2026-11-05)

These lines come from `experiments/EXP-034/posthoc_gated.json`, written by `posthoc_gated.py`, which reuses `mine.py`'s own loaders and Q2 functions. A gated task is one where at least one arm's as-run grader tail shows the missing package (§7 item 5): 15 tasks, leaving 33 non-gated. The readings in §4 are not touched, and nothing below is a reading.

**Q1 on the 33 non-gated tasks** (resolved flags as in §2.1):

| set | per arm | union | best single | union minus best |
|---|---|---:|---:|---:|
| all six | E0 9, X003 9, A25 9, B25 8, R 9, RH 10 | 13 | 10 | **3** |
| V {R, RH} | 9, 10 | 11 | 10 | 1 |
| O {E0, X003, A25, B25} | 9, 9, 9, 8 | 12 | 9 | 3 |

On the full 48, the same script reproduces §9.1: 17, 12, 5; V 1; O 4. Removing the gated tasks brings the all-arm union minus best down from 5 to 3, and O from 4 to 3. V stays at 1.

**Arm R's RFWF group (30), split by its own grader tail**:

| R RFWF | n | pass | fail | error | none after last edit |
|---|---:|---:|---:|---:|---:|
| grader-blocked (R's tail shows the missing package) | 11 | 2 | 0 | 1 | 8 |
| graded | 19 | 5 | 1 | 0 | 13 |

- **Grader-blocked tasks.** The hidden tests never ran on these 11, so "unresolved" says nothing about the fix.
- **Graded tasks.** The 19 graded tasks give the same Q2-neither picture as the full group: neither pass (5) nor fail (1) is a majority.
- **RH (27).** 12 are blocked (pass 1, none 11) and 15 are graded (pass 3, fail 1, none 11).

## Status

COMPLETE 2026-11-05 (zero GPU). The critic's Required fixes 1 and 2 (`experiments/EXP-034/critic.md`) are applied as §7 item 5 and §9.4. The readings are unchanged.
- Q1-stays: all-arm union minus best is 5 (V family 1, O family 4); the selector bar is +3.0 tasks over a random arm.
- Q2-neither: R RFWF pass 7, fail 1, none 21 of 30; replicated in RH.
