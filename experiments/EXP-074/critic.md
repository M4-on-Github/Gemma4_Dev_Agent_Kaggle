---
id: D-011-critic
exp: D-011
tier: direction
verdict: needs-work
verified: regenerated
date: 2026-11-12
---

# D-011 direction review (not a review of EXP-074)
Filed here only because the dispatch named this path. A later EXP-074 review must not treat it as a prior review.

## Verdict
needs-work. No harness-side arm in reach clears the base-draw gap on resolves: the draws span 3 to 6, and the largest EXP-074 class ceiling (E, 4) needs full conversion. The roughly 20 GPU-h left this week [I] buy process answers, with two draws per arm where an endpoint is unstable.

## Weakest assumption: the endpoint rule
"Keep beyond the gap" treats one two-draw gap as the spread, and where the draws agree by chance that gap is near 0.

Empties 10 and 9 sit on E churn: 7 of 10 left and 6 entered, a reference SD of about 4 for a difference. A third exchangeable draw would fall below both one time in three. Repeats 25 and 22 are inside a bootstrap SD of 7.

The fix costs no GPU: keep beyond the larger of the gap and two reference SDs.

What one draw can read:
- Mean wall, cap hits and projection: yes.
- Eo and repeats: only large moves.
- M, A, F, C, same-class and resolves: two draws per arm.

## The 0.2 replicate
Read the replicate alone, since the first draw picked the endpoint. Pooled figures are estimates only.

The null is 19/96 = 0.198 per task-run. That counts the shared ids as independent, roughly tenable given the E churn [I].

| Eo | Reading |
|---|---|
| ≤ 4 | Keep. P 0.027 under the null, 0.015 at 0.214 |
| 5 to 8 | No decision; the empties line ends |
| ≥ 9 | Kill |

Power is 0.43 at a true 5/48, and the middle band is the likeliest outcome (0.51).

A blind secondary at no extra GPU: tasks with an arg-loss edit, 6 and 4 in the base draws and 1 in the first 0.2 draw. Read ≤ 1 (P 0.034 at 10/96).

## Ranked arms (none clears on resolves)
1. The replicate.
2. A locate step before the first edit. On 9 of 12 EXP-038 F runs no gold file was shown before it. Endpoint: gold file read first, over two draws. Ceiling: F3 + R1.
3. A visible-budget change, which can act only through pacing, since no cap was hit (at most 22 of 28 calls). The 31B's #7 was null.

Not levers:
- Thinking: 1.1% of steps reach 4096, and the 31B's #6 was null.
- Compaction and context: not settable. Empties were 3 of 18 on compacted EXP-038 tasks and 7 of 30 on the rest [I].

## Misstatements
- "Only figure outside both base draws": A, the failed share and resolves are outside both as well.
- "Not closed" and the README's "dead" should both carry the `experiments/EXP-075/critic.md` wording.
- The cap is 8 min, not 4.5.
- A dev-48 arm costs 1.27 to 1.34 GPU-h, not about 2.
- The ledger shows 9.8 GPU-h, not 6.8.
- The week start is given as 11-07 and as 11-08.
- 5 of the 48 tasks are gold-blocked, so rule 1 needs 16 of 43.
- EXP-075 and EXP-077 ran above 1 GPU-h before this review, although the status line promised the review first.

## Other side
- The 31B pools 28/174 on the LB, against 0.05 for the E4B.
- A top-5 team would spend the GPU on the 31B [I].
- Not considered: top_p at temperature 1.0. It would separate tail-token argument loss from homogenized behaviour as the cause of the empties signal.
