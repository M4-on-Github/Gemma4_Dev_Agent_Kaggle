---
id: EXP-037-critic
exp: EXP-037
tier: prereg
verdict: needs-work
verified: inspected
date: 2026-11-05
---

## Verdict
needs-work. The arm is one variable and the build reproduces. Two rules change what a row means and must be fixed before the push: Δ_8min is a median read against a mean-derived headroom, and rows 2 and 3 order re-runs the ledger cannot pay for. Fixes 3 and 4 complete the readings table (a rule for M_any = 5, pooled-15 thresholds, a grading-fault class) and §5. No rebuild of tree or notebook is needed; the prediction must be restated under fix 1 before the push.

## Checks
- **P1** Rows 0-7 cover blank/crash and both directions, each with a next step. Gaps: M_any = 5 falls to row 7 and discards K and the cost reads; row 2's "pooled 15 against rows 3 to 7" has no thresholds (rows 3-6 are written "of 8"); row 0 misses a grading fault, which would read as row 3.
- **P2** Stated (M_any 7, K 3 [1-5], Δ_8min ~11 s, row odds). Must be restated after fix 1.
- **P3** Mismatch. 13.8 s = (10.5 - 10.04 h)/120 and 10.04 h is a mean projection (EXP-028 §9); endpoint (c) uses median turn times. The file's own means give ~24 s, not ~11 s. Δ also omits the extra prompt tokens on every later call and extra compactions, so it is a lower bound. The full-cost instrument (paired mean wall) has SE ~30 s at n = 8 (EXP-032 E8: 29.4 s) and cannot clear 13.8 s.
- **P4** Counts only, no test, K not read as a rate. Correct.
- **P5** Point 0.90-0.93 h is built right (measured 517 s overhead + R's measured 2,493 s + 30-40 s/task). 1.24 h is not a bound: 1 of 96 R/RH tasks ran 751.9 s at the 8-min cap (rich_3480, RH), +0.07 h each. Rows 2/3 each order a second run of ~0.85-1.24 h; after this run the ledger has ~0.1-0.44 h of 3.2 left.
- **P6** Holds. `diff -r` against `EXP-027/candidate-v24-at-8`: one hunk (7a8,51), 44 lines added, 0 removed; agent.yaml, eval_config.yaml, sampling.yaml sha-identical; all LF. Embedded zip decodes to a4379856...1a71. Kernel metadata equals exp028_armR's but for id/title. Notebook code cells equal Arm R's except cell 0 (parameters, new empty MODEL_NAME) and cell 5 (model dir from the zip, D-004), which resolves the same 31B dir. Not a second variable; say so in §2.

## Answers
1. **Discrimination.** Row 2 vs 7: fix 3. Row 6 can fire on selection: 13207, 14297, 14360 flipped in both R and RH, so K >= 2 is near-certain if those three carry a stand-in [I]; within rows 5/6 only X0 and Δ decide. K = 2-3 shows that a carried stand-in plus an already-known fix survives two extra calls and the as-run grader. It shows no dev-48 or LB rate, no gain beyond EXP-036's +3 (R) / +5 (RH) of 48, nothing on the 11 non-gated hit tasks or the hidden set.
2. **Fair.** Yes (P6). The write path works in this harness: R's forensics show 48 heredoc-write turns through run_command (re-run here), and 15 older-lineage final patches carried top-level stand-ins.
3. **Coverage.** The 128 probes show equivalence to compat_shims, not coverage. In all 15 gated snapshots the tests tree imports `Is`, `IsInt`, `IsStr`, which neither provides (8 of 15: up to 7 such names). Sufficiency rests on a chain: same code as compat_shims; GOLD 15/15 gated under compat_shims (EXP-036); the grader runs only the test-patch files (harness-stack). Yes for all 15, on this grader only.
4. **Risks.** Shadowing is stated but not its mechanism. `__pycache__` is absent from §5: all 15 gated snapshots' .gitignore cover it and 0 of 15 older-lineage stand-in patches carry a pyc or binary hunk; check_standins.py excludes `__pycache__` in `files_of`, so it does not test this. Non-gated harm and miss-task cost are correctly listed as unreadable; here a stand-in cannot change a non-gated grade by import (that task would be gated), so cost is the only channel [I]. The package names pass lint; log as a §7 defect.
5. **Cost.** 1.24 h + ~0.07 h per overrun. Nothing cheaper answers the same question: 5 flip ids alone save ~0.3 h but cut M_any to n = 5; a 3-call run reads G/W/F for ~0.2 h but changes the cap and loses K, X, H3. Same cost, more information (lead's call, cohort change): swap the 3 seeded ids for non-gated hit ids R resolves as run (e.g. 13537) to read harm.

## Synthesis [I]
On means, Δ_8min is ~24 s. Emitting the 1,712-byte command is ~500-670 output tokens, or 17-22 s at 29.8 tok/s. So row 6 is near-unreachable and the 8-min question goes to a dev-48 time profile either way. The screen buys M_any, F, and fix survival. An LB gain also needs at least 4 of 58 hidden tasks to import these packages; nothing we hold tests that, and EXP-036 already bounds dev-48 at 0 GPU. Competing causes of a weak result, separable on the existing endpoints: an unfaithful copy (F); first-edit displacement (e); the agent adding names to a stand-in after an ImportError on `IsStr` (H3, which row 1 counts as harm even when additive).

## Required fixes
1. §3(c): define Δ_hit and Δ_miss as **means**, labelled a lower bound (it omits prompt growth and compactions). Restate the §4 prediction and row odds before the push.
2. §2 Cost: state the conditional re-run spend of rows 2 and 3 (~0.85-1.24 h each) and that it exceeds the remaining ceiling, so each re-run needs its own approval. Make the worst case conditional: "1.24 h if no task overruns; 1 of 96 R/RH tasks ran 751.9 s".
3. §4:
   - Add a rule for M_any = 5: either rows 3-6 apply at M_any >= 5, or row 7 reads K, X0 and Δ against the rows 3-6 thresholds with the mechanism marked weak.
   - Give row 2's pooled-15 re-read its own thresholds, e.g. kill at <= 7 of 15 and rows 3-6 at >= 11 of 15.
   - In row 0, add a grading fault: no grade, or test_exit_code -1 on a patch touching no test path.
   - In H3, record what the touch did (added names, or changed or removed code).
4. §2 line 82 and §5:
   - Replace "the subset ... a test file can reach" with the answer 3 chain.
   - Name the regression on a grader that has the real packages: a graded file importing `Is`/`IsInt`/`IsStr` (or similar) fails at collection where it would otherwise pass.
   - Add the `__pycache__` evidence from answer 4.
   - State that K >= 2 has a high base rate on this cohort.
