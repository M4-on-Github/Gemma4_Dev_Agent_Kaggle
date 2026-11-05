---
id: EXP-038-critic
exp: EXP-038
tier: prereg
verdict: needs-work
verified: regenerated
date: 2026-11-05
---

## Verdict
**needs-work. The estimate does not honestly meet "only 1 hr": hold the push for the user.**
- My central estimate is about 1.25 to 1.3 GPU-h. I put about 25% on the run going above 1.5 h, and about 45% on it going above 1.34 h, the room left under the 3.2 h ceiling.
- Those figures weight the ratio-of-means bootstrap above the mean-of-ratios one, because a mean of ratios is biased upward on 8 noisy denominators.
- 0.88 h is not a credible point.

Four text fixes are needed and nothing has to be rebuilt.

## Cost (item 1)
- **The script is built right.** `cost_estimate.py`, re-run into scratch, gives byte-identical output. Time outside `wall_s` is 0.02 s per task in the E4B log and 0.07 s in R's, so the 444.8 s overhead is fixed. The McNemar thresholds check by hand.
- **Point A should not be offered as a point.** Arm R capped on 22 of the 40 ids outside smoke-8, against 1 of 8 inside it, so dev-48 is harder than smoke-8.
- **1.466 is defensible, but it is one of several scalings.** The 8 pairs couple only weakly (per-task wall correlation 0.23, turns 0.62). Other scalings give 0.94 to 1.46 h, with most between 1.23 and 1.30 h. Bootstrapping the 8 pairs gives these probabilities [mine]:

  | Estimator | P(> 1.34 h) | P(> 1.5 h) |
  |---|---|---|
  | Ratio of means | 0.35 | 0.17 |
  | Mean of ratios | 0.67 | 0.41 |

  Arm R's walls are censored at the caps, so scaling by them understates the difficulty [I].
- **Scenario C (2.41 h) gets under 5% from me [I].** All 8 E4B tasks ended by submit after 1 to 15 counted calls.
- **The ledger sum uses a point estimate as if it were a bound.** "1.86 + 1.24 = 3.10" treats B as an upper end, the same error as EXP-037 fix 2.

## Pre-registration checks
- **P1: fail, Row 0.** The clause "5 or more rows carry a non-empty `error`" fires on Arm R itself: 10 of R's 48 rows carry the harness cap strings (6 "Agent exceeded session timeout", 4 "turns budget"). A cap-bound E4B would therefore read as a crash, and Row T's cap-bound branch could never be reached.
- **P2: pass, with one inconsistency.** E8 at 1.05 h does not follow from E3's 75 s mean, which gives 1.12 h. Both sit below §2.2's point B.
- **P3: fail, E7.** `estimate_budget.py --results` takes the larger of the wall and a decode estimate. On EXP-033 it gives a mean task of 2.91 min (5.82 h projected) against a measured 56.9 s. Even at `--tok-s 56.4` it gives 2.69 h. Row 2 also uses 11.0 h where the plan's rule is about 10.5 h.
- **P4: pass.** R's 9 resolves include the free `requests_6644`, so there can be at most 8 R-only tasks; §4 states the power limit.
- **P5: pass on the hidden-set clock.**
- **P6: pass.**
  - Only the model line differs.
  - R's as-run agent directory is identical to EXP-027's tree.
  - 1cd52f8 is the only execution change to the notebook.
  - The zip sha, `TASK_IDS` and the metadata match.

## Items 2 to 5
- **Readings.** They cover both directions, the test is paired, and "admissible" means a proposal only. One wording issue: Row 0b treats any as-run resolve of a gated task as a grader change. A resolve whose patch creates the missing module is not one.
- **Pairing.** It is fair, and the 28-of-48 and 43-of-48 ceilings match C-022. The re-grade in §3.3 has no fault row.
- **Row T.** "Room" as 480 minus wall includes grading and ignores the total clock. Under the 10.5 h rule, 120 tasks allow about 311 s per task on average, so at an 85 s mean the room is about 225 s, not 395 [I]. A voting design priced against EXP-033's 423 s would overrun the 12 h clock.
- **Unreadable at 48.** Only the Row 0 and E7 defects.

## Required fixes (text only, no rebuild)
1. **Row 0:** count only errors other than the harness cap strings.
2. **E7 and Row 2:** read the mean `wall_s` x 120 / 3600, plus the measured overhead, against about 10.5 h. Record `estimate_budget.py` without reading it.
3. **Row T:** define the room in full:
   - the per-task room is 480 minus `wall_s`, a lower bound;
   - the total-clock room is (10.5 h minus E7) x 3600 / 120;
   - the smaller of the two binds;
   - report the mean and the p10, headroom on calls and on turns, seconds per turn as wall sum / turn sum, and the number of capped tasks excluded.
4. **§2.2 and §4.2:**
   - state the central estimate and the probabilities above;
   - make E8 consistent with E3;
   - narrow Row 0b's gated clause;
   - add a fault row to the re-grade: fewer than 48 graded, or GOLD or BASE grading differently from EXP-036.

**Option for the user [mine].** Run only the 27 informative ids. E2 stays intact, because the other 21 are expected to be concordant, and the run takes about 0.75 h. It loses 21 tasks of the time profile and the gated re-grade.
