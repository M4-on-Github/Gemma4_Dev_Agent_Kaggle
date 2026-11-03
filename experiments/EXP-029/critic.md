---
id: EXP-029-critic
exp: EXP-029
tier: prereg
verdict: ready
verified: regenerated
date: 2026-11-03
---

## Verdict
Ready for the proposed R upload (sha c22069db, equal to `out/submission.zip`, `experiments/EXP-027/v24_at8.zip` and #11). Not ready for an RH upload until the row 3 pooling clause is fixed (Required fixes 1). That defect does not affect the default tree.

## Audit
- P1 pass. Rows 1-4 cover blank and every k from 0 to 58, applied in order, and each names the next slot. Committed at f56b226. No upload yet (`approvals/` holds only the README). Wording defects to log in §7, none blocking: (a) row 2, case R, compares a two-draw mean (<= 7.5) with the retired lineage's best-of-9 maximum (8), when the right comparator is its mean, about 6.6; (b) row 2 calls one R draw "the discriminating draw for RH", but one draw per tree cannot resolve a gap below the MDE.
- P2 pass. k ~ 10, band 6-14. P(k <= 5) = P(k >= 15) ~ 0.06 at Bin(58, 0.172) checks out.
- P3 pass. k of 58 plus blank.
- P4 pass, with one caveat for the lead. Pooling halves the variance of the baseline mean, but a single future draw compared with a two-draw baseline has a difference sd of sqrt(1.5)σ instead of sqrt(2)σ. The one-draw MDE drops only to about 3.5 tasks (my calculation), so treat it as about 4, not 2.
- P5 pass on my regeneration. §2 makes the override against EXP-028 §9's T1-T3, which is not written yet. From `runs/EXP-028-armR`, Arm R has a mean task wall of 297.5 s, which gives 9.92 h for 120 tasks. The kernel log spans 14,832 s against 14,280 s of summed task walls, so about 550 s of measured overhead. Projection: 10.07 h if that overhead is fixed, about 10.3 h if it scales per task. That is T2 (9.5-10.5 h), so 8 min stands with no margin. 6 of 48 tasks were at the cap; p90 is 483 s. Tail risk for RH: its mean equals R's (296.8 s), but rich_3480 ran 752 s, which is 272 s past the cap, and 10 of 48 tasks were at the cap against 6 for R.
- P6 pass. R differs from #11 in nothing. RH differs only by the section (EXP-028 §2 `diff -r`). Both shas regenerated.

## Required fixes
1. **Only if RH ships:** row 3 pools a different tree into the baseline that the Serves line and S-012 say "every later arm is read against". The "R + RH" label does not cure it: any LB effect of the section below the MDE shifts the comparator by half that effect, and EXP-028's compliance endpoint says nothing about resolves. Fix: pool only byte-identical zips. An RH draw opens the RH count at n=1, and the R baseline stays at #11 alone. A combined lineage figure may be reported but is never the comparator. Make the same edit in the Serves line and in S-012.
2. Recommended, not blocking: §2 says the tree is "whatever EXP-028 §9 names", but §9 may land after the approval is written. Add: "the governing §9 is the one committed before `approvals/S-012.txt` exists; otherwise R." The sha-bound approval already enforces this in practice. Also add a line saying what the next slot does while #12 is pending, since grading has taken up to 5 days and every row's action is a next-slot action.
