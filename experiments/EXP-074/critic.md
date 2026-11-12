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
needs-work. No harness-side arm in reach clears the base-draw gap on resolves. The draws span 3 to 6, and EXP-074's largest class ceiling (E, 4) needs full conversion. The roughly 20 GPU-h left this week [I] buy process answers, with two draws per arm where the endpoint is unstable.

## Weakest assumption: the endpoint rule
"Keep beyond the gap" treats one two-draw gap as the spread. Where the draws agree by chance, it is near 0:
- Empties 10 and 9 sit on E churn: 7 of 10 left and 6 entered, against a reference SD of about 4 for a difference.
- Repeats 25 and 22 sit inside a bootstrap SD of 7.

The fix costs no GPU: keep beyond the larger of the gap and two reference SDs.

What one draw can carry:
- Stable on one draw: mean wall, cap hits, projection.
- Large moves only: Eo and repeats.
- Two draws per arm: M, A, F, C, same-class, resolves.

## The 0.2 replicate
Read it alone. The first draw picked the endpoint, and replicate ≤ 4 is the same event as pooled ≤ 9 of 96.

| Eo | Reading |
|---|---|
| ≤ 4 | Keep. One-sided P 0.027 with base 19/96 as known, 0.059 by Fisher with the base estimated |
| 5 to 8 | No decision, recorded as untested at this power |
| ≥ 9 | Not replicated; the first 5 is filed as draw noise |

Either of the last two rows ends the empties line, and a second 5 is no decision. Power is 0.43 at a true rate of 5/48, and the middle band is the likeliest outcome (0.51). The shared ids are treated as independent, which the E churn makes roughly tenable [I].

M did not fall, so a real drop came through some other channel [I]. Tasks with an arg-loss edit went 6 and 4 to 1, but these were empty on only 2 and 2. A blind secondary: arg-loss tasks ≤ 1 (P 0.034 at 10/96).

## Ranked arms (none clears on resolves)
1. The replicate.
2. EXP-076's file-list search recipe, on the single loop.
   - It is offered there and not built. Simulated, it names gold on 3 of the 6 F misses where the output never named gold.
   - It differs from EXP-064 and EXP-066, which put the reader on the pipeline's shared call counter.
   - Endpoint: a gold path in a tool output before the first edit (base: F 3 of 12), over two draws. Ceiling F3.
3. A visible-budget change. It can act through pacing only, since no cap was hit (at most 22 of 28 calls).

Not levers:
- Thinking: 1.1% of steps reach 4096.
- Compaction and context: not settable. EXP-038 empties were 3 of 18 compacted and 7 of 30 uncompacted [I].

## Misstatements
- "Only figure outside both base draws": A, the failed share and resolves are outside both too. On temperature, cite `experiments/EXP-075/critic.md`.
- Stale figures:
  - an arm costs about 2 GPU-h; measured 1.27 to 1.34;
  - ledger 6.8; now 9.8;
  - "4.5-min cap"; the tree runs at 8;
  - the week starts on 11-07 and on 11-08.
- Omitted: 5 of the 48 are gold-blocked, so rule 1 needs 16 of 43.
- Process: EXP-075 and EXP-077 ran above 1 GPU-h before this review.

## Other side
- The 31B pools 28/174 on the LB, against 0.05 for the E4B. A top-5 team would spend on the 31B [I].
- Not considered: top_p at temperature 1.0, which would tell tail-token argument loss apart from homogenized behaviour.
