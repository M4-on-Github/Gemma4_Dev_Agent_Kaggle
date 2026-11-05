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

(none yet)

## Status

Pre-registered 2026-11-05; nothing in sections 3 to 5 computed yet.
