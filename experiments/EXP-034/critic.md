---
id: EXP-034-critic
exp: EXP-034
tier: light
verdict: needs-work
verified: regenerated
date: 2026-11-05
---

## Verdict
The readings were applied as written and every Q1 number regenerates. One pre-registration fact is wrong, though, and it changes how D-005 may use both endpoints. §2.1 says "every later arm was graded with the shims present". It was not: A25, B25, R and RH were graded as run, without the two test-only packages. Claim the lead can copy once the fixes land: *over six dev-48 arms, union minus best is 5 (Q1-stays, as registered), but 2 of the 5 sit on 15 tasks whose Kaggle grade depends on two test-only packages the sandbox lacks. On the other 33 tasks it is 3 across configs and 1 between R and RH. On Arm R's 30 right-file-wrong-fix (RFWF) tasks the agent rarely runs a counted test after its last edit (21 of 30), and the grader never ran the hidden tests on 11 of the 30.*

## Audit (light: 1, 2, 3, 8)
1. **Order: pass.** f5f387a (08:52:53) precedes d2a8041 (08:57:53). Every file under `runs/EXP-034/` is stamped 08:53:03 to 08:56:02. Above §9, the diff touches only §7. Minor: there is no `---` separator and no §8; `mine.py` was committed only with the results; `obs.txt` and `key.txt` of the hand check were written in the same second, so its blindness is inspected only.
2. **Cohort: pass; grading as §2.1 states: fail.** There are 48 ids, all in dev-48. The notebook source has no shim code, and EXP-004 re-graded only E0 and X003. Grader tails show the missing package in 15 tasks (per arm: E0 5, X003 14, A25 8, B25 8, R 13, RH 14). On those 15 tasks:
   - E0 (2), A25 (2) and B25 (1) resolve only with patches that vendor the shim.
   - X003's 3 resolves exist only under EXP-004's grader-supplied shims.
   - R and RH resolve 0 of 15 and never vendor.

   Why R and RH never vendor (inspected): `submission/prompts/swe_coder.md` has carried a "Known sandbox gaps" vendoring section since f16b801 (2026-10-16). The v24 prompts R and RH ran (`experiments/EXP-027/candidate-v24-at-8/`, `experiments/EXP-028/candidate-RH/`) contain no shim or vendoring text. Adopting v24 dropped that section.

   So the union of 17 mixes two grading environments, and 1 of the 4 gated "some" tasks is in it only through the re-grade. The uniform as-scored line still gives 5, so the reading stands. On the 33 non-gated tasks, per arm 9, 9, 9, 8, 9, 10; union 13; **union minus best 3** (V 1, O 3). Post hoc, mine.
3. **Regenerated from the committed `summary.jsonl`.** Exact: per-arm counts, unions, curves, 6/11/31 and the histogram, the 202 pairs, all four proxy 2x2s and scores, random arm 10.333 and random non-empty 12.217. The Q2 booleans agree with `aggregates.json` (R: 15 tested after the last edit, 13 last-pass of which 7 unresolved, 1 fail). I recomputed RFWF membership in memory with `mine.py`'s own functions:
   - Endings (R, 30): submit 15, calls cap 10, turn cap 2, clock 3. This matches §9.3 as reconciled.
   - Ending against last-visible result: pass 7 (all submit); none 21 (calls cap 10, submit 8, clock 2, turn cap 1); fail 1 (clock); error 1 (turn cap).
   - Grader-blocked: 11 of the 30, 2 of them among the 7 last-pass. Graded RFWF: 19 (pass 5, fail 1, none 13).
   - The X003 as-scored line was read from aggregates, not regenerated.

   **Q2 defects cannot move the reading.** Q2-pass or Q2-fail needs 16 of 30.
   - Item 3 only lowers fail, which is 1.
   - Item 2 can at most turn the 7 passes into fail (text), which makes fail at most 8.
   - Item 4: 4 RFWF "none" tasks have a `python -c` after the last edit, which gives at most pass 11 or fail 5.
   - The 8 of 10 hand check misses only item-3 cases.
   - The graded-only split (5, 1, 13 of 19) gives the same reading.
8. **Scope and hygiene: pass.** §9 stays inside §5, and the committed files hold ids, booleans and counts only.

## Required fixes (zero GPU)
1. §7 defect item: §2.1's grading statement is wrong. State per-arm environments as in audit 2.
2. Add post-hoc lines to §9:
   - Q1 on the 33 non-gated tasks: union minus best 3, V 1, O 3.
   - R's RFWF group split into grader-blocked (11) and graded (19), each with the last-visible counts.
   - Readings unchanged.
3. For the lead, not the experimenter alone: before C-015 or any F3 pool moves, re-grade R and RH with the shims (`regrade_patches.py`, EXP-004 pattern, CPU kernel, 0 GPU-h). It sizes how much of the RFWF pool depends on the sandbox. Ship decisions stay on the as-run grade until we know whether the hidden grader has these packages.

## D-005 direction review
**The P column is undefined.** Read as one observed draw, the null alone gives +4 or more about 13% of the time (plan.md:297 gives 26% two-sided at a per-task rate of 0.095, and more at 0.18). That puts F1 and F2 below chance. Relabel it "P(true gain >= 4 of 58)".

**F3.** 4.5 points × 48 = 2.2 follows. The transfer does not: lit-2504.07164's +4.5 comes from regression tests filtering 26 trajectories, not from a check-then-fix loop on one patch. "At most 23" is not a bound:
- 5 of the 7 passes it subtracts were the agent's own scripts, not existing tests.
- 11 of the 23 are grader-blocked; gradable non-pass is 14, and 10 of those ended on a cap.
- At 4.5 min, 10 of R's 15 RFWF submits would never happen, because they came after 270 s.

P 0.2 is too high; ≤0.1 until the re-grade and EXP-035 report. [I]

**(c), the "half" reading, is not supported.** Of the 15 submits, 7 did check (and passed). 8 had no counted test after the last edit, or 4 if a `python -c` counts. 4 of those 8 are grader-blocked, and 2 submitted under 270 s, of which 1 is gradable. Supported sentence: "8 of 30 submitted with no counted test after the last edit; at 4.5 min about 1 had time left."

**F0.** The 11 call-cap tasks are T4's pool (EXP-032, 8 min / 43 calls), not the common setting's. At 4.5 min the clock binds at about 21 calls (B8: 270 / 12.83 s), so cap 40 is inert and F0 is the shipped loop with 44% less clock: ≤0 against R at 8 min (B14). P 0.15 is too high.

**F1.** The arithmetic follows (3.87 × 0.39-0.55 = 1.5-2.1; V 0.6-0.8). The inputs do not:
- The sources draw full tool-using runs, and the 39% is measured from a vote baseline. D-005's proposals are tool-free texts sharing one locate stage.
- On the non-gated 33, the k = 3 gap is 2.4, giving 0.9-1.3, against a mean arm rather than the shipped one.

P about 0.05. [I]

**F2 and the ranking.** "Pool: none" ignores our traces:
- R compacted in 36 of 48 tasks (3 resolved) against 12 uncompacted (6 resolved).
- 15 of 30 RFWF tasks made their first edit after the first compaction.

This is confounded by length, but context isolation is the mechanism an orchestrator acts on, and the user named it. The cheapest check is zero GPU: within each of the 11 "some" tasks, compare compaction before the first edit between the arms that resolved and those that failed. Stratifying by task holds difficulty fixed; n is tiny, so read it as a gate. If it separates, run the 0.7 GPU-h screen with the endpoint "writer's first edit before any compaction". Unconsidered option: an orchestrator whose worker *executes* the check (a tester called through `agent_tool`). It targets the measured failure and keeps test output out of the writer's context.

**Staging.**
- 4.5 min is right for ship safety and wrong as the only reference. Keep R at 8 min (on disk, 0 GPU) as a second reference.
- The smoke-8 gates are readable as gross checks. Smoke-8 holds 6 R RFWF tasks and 1 gated task. "Verifier reached <4 of 8" falsely kills a true 60% reach rate 17% of the time. "Repro fails ≥4 of 8" against R's base rate of 6 of 48 happens by chance about 1% of the time.
- Pre-register a prediction now that F3's verify turn is rarely reached before 270 s.
- Stage 1 belongs after the screens, beside the first Stage 3 arm. The kill branch should keep the measured 8-min tree, not an unmeasured 4.5-min one.
- Stage 1b serves the prize, and sub-10B results invert (lit-2506.03524), so it does not belong in D-005.

**EXP-035.** It answers the narrower question: does the wrong patch break an unchanged existing test? It is computable from `test_tail` for 14 of R's 30:
- 15 are exit 2: 11 blocked, 2 "cannot import name".
- 1 FAILED list is cut by the 1,500-char cap.

It misleads if:
- exit-2 tasks are not their own row;
- "existing" is decided by name (there are no FAIL_TO_PASS lists, so map `test_patch` hunks to functions);
- tests that fail at base in the sandbox are kept;
- gated tasks are counted as visible.

**Dissent (for D-005 Options, verbatim).** The benchmark's instrument partly measures the sandbox: 15 of the 48 dev-48 tasks are graded without two test-only packages the Kaggle sandbox lacks, and the shipped v24 prompt, which dropped our vendoring section, resolves none of them while the older-lineage arms resolve 1-2 through vendored code; 11 of Arm R's 30 right-file-wrong-fix tasks never had their hidden tests run, and on the other 33 tasks the six-arm best-of-N ceiling is 3, not 5. Re-grade R and RH with the shims on a CPU kernel, finish EXP-035 on the graded tasks, and test porting the vendoring section as its own one-variable arm, keeping ship decisions on the as-run grade until we know whether the hidden grader has these packages. Then screen one change at a time against Arm R at its shipped 8 minutes, starting with a required executed check, rather than four structures at 4.5 minutes, where 10 of R's 15 wrong-fix submits would never happen because they came after 270 s.

## Not verified
- Whether the hidden grader has these packages, and whether hidden repos use them.
- Every literature figure (read from notes, not PDFs).
- EXP-033 (§9 read, not regenerated).
- Hand-check blindness.
