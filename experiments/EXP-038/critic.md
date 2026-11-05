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

## Re-review 2026-11-05 (after 4024082)

**Verdict: needs-work. Fixes 1 to 4 hold. The new section 8 clause needs two dated notes, and two one-line notes follow from the fixes. Nothing is rebuilt.** If fixes 5 to 8 are committed with the text below verbatim, the push needs no further critic read [mine].

What I checked: `git diff 143fba1 4024082` on the EXP file, on `cost_estimate.{py,json}` and on the README row. The script, re-run into scratch, gives byte-identical JSON.

**Fixes 1 to 4**
- **Fix 1 holds.**
  - The amended Row 0 counts 0 errors on Arm R, where 10 of 10 error rows are cap strings, and 0 on RH (8 of 8).
  - It still catches a failure before the loop, fewer than 44 rows, and non-cap errors.
  - It leaves one gap, closed by fix 7.
- **Fix 2 holds.**
  - E7 for R: 297.44 s x 120 + 555.5 s = 10.07 h.
  - Row 2 threshold: (37,800 - 444.8) / 120 = 311.3 s.
- **Fix 3 holds, and the split is sound.**
  - One count picks the branch: calls or time cap, 23 on R. The room is measured on U under either branch, so no row fires two ways.
  - R's one turns-only task is in neither set, as the file states (24 excluded).
  - Every field exists in `summary.jsonl`. `n_calls` over U is at most 27.
  - On R the per-task room has mean 237 s and p10 101 s. The total-clock room is 13 s, so the total clock binds.
- **Fix 4 holds.**
  - The §2.2 figures match my review.
  - E8 = 75 s x 48 + 444.8 s = 1.12 h.
  - Row 0b and row F are as asked, and the patch path matches R's layout.
  - Keeping 75 s is right. The prediction is the experimenter's blind call; both figures carry their source and both get scored.
- **Item 6.** Every changed first-written line is either struck and kept, or extended by a dated note. Nothing is deleted.

**New defects**
- **A. A truncated run has no reading of its own.**
  - It inherits Row 0's "infrastructure, not the model", and a cancel counts as a "Kaggle stop" there.
  - A truncated run always has fewer than 44 rows, and nothing orders the truncation clause against the crash clauses.
  - Line 210 would also apply Row T to its partial rows.
  - The reading matters for cost. Read as infrastructure, a re-run is priced at 1.25 to 1.3 h. Read as a truncation, the run shows that estimate is wrong.
- **B. The stop rule cannot fire as written [I].**
  - No agent is woken at a set time.
  - The lead's commands are git and `kaggle kernels status`, and the screener has no clock command (EXP-032 push record).
  - If no one acts, the run continues.

**Required fixes (dated notes, text only)**
5. Under Row 0's reading, add: "*Added 2026-11-05 (critic re-check):* a run cancelled under the section 8 stop rule is read as **truncated**, neither infrastructure nor a model reading. It is read as a crash instead only if the surviving output shows a failure before the task loop, or 5 or more errors counted under the clauses above among the surviving rows. Report the elapsed time at the cancel, the number of surviving rows, and their mean `wall_s` and capped count. No endpoint is read and row T is not applied. A re-run is priced from these figures, not from section 2.2."
6. In section 8, add: "*Amended 2026-11-05 (critic re-check):* the push record states the push time in UTC, and the lead's push report gives the user two clock times, push + 1.75 h and push + 2.0 h. The decision at push + 1.75 h is the user's, made from the Kaggle UI. If no one acts, the run continues to its end, 2.0 h is not enforced, and the exposure is section 2.2's tail (scenario C 2.41 h, conditional worst case 6.66 h)."
7. Under Row 0's fix-1 clause, add: "*Added 2026-11-05 (critic re-check):* a cap-string row whose `n_turns` is 0 counts as an error."
   - Without it, a model server that stalls into session timeouts reads under row 1.
   - Every cap-string row in R and RH has at least 12 turns, so the rule cannot fire on a real cap.
8. In the README row, strike "kernel about 1.05 h" and add "1.12 h (restated)".

**Not required.** Lines 210 and 258 disagree on whether Row T follows rows 0b to 2. The disagreement predates the fixes.

**For the user's decision at 1.75 h [I].**
- My bootstrap p90s, 1.61 h and 1.76 h, put about 5 to 10% on the run not being COMPLETE at 1.75 h of GPU time. Queueing adds to the elapsed time.
- Whether a cancelled kernel keeps any output is unverified: EXP-032's cancelled version was never downloaded.
- So cancelling at 1.75 h buys protection against the tail, at the risk of losing the whole spend.
