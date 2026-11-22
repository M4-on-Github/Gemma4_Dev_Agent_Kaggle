# R-024: E4B retry on an empty attempt at the Kaggle cap, 4.5 min, bars checked against R-021 (pre-registration)

Written 2026-11-22, after R-023 was killed by its retry gate and before any job of this round is submitted. Counts
only; no trace content. Tweak id **T-e4b-022**, unchanged.

## What carries over from R-022 and R-023

- Why, the two trees (`trees/e4b-r022-ctl-4p5`, `trees/e4b-r022-retry-4p5`, at 5176b41), flags, the pin to
  pleiades-0-23, no smoke, cost (about 17 Ada GPU-h), the server-death rule (R-022 reading 2), the decision rule
  (R-022 reading 3, which is R-020's word for word), the mechanism readings (R-022 reading 4) and what each outcome
  means: **as R-022, word for word.**
- **Not read for effect:** the d1 gate values of R-022 control, and of R-023 control and retry, as written in those
  files. No R-022 or R-023 row enters this round's decision.

## The only change: draw-1 kill bars, each checked on all 24 R-021 draws

| Arm | Field | R-021 per-draw range (12 draws) | **R-024 bar (kill on)** |
|---|---|---|---|
| retry d1 | resolved | 5-12 | **≤ 3** |
| retry d1 | empty | 2-11 | **≥ 23** |
| retry d1 | time caps | 0-2 (at 8 min) | **≥ 20** |
| retry d1 | `retry_miss` | 0-2 | **≥ 5** |
| retry d1 | `solve_calls_gt3` | 0-4 | **≥ 8** |
| control d1 | resolved | 4-9 | **≤ 2** |
| control d1 | empty | 10-24 | **≥ 32** |

- Check, run before this file was written: `tools/d1_gate.py runs/R-021-e4b-retry-ada-dN 79 <retry bars>` gives PASS
  on all 12 retry draws. The control bars give PASS on all 12 control draws (d1-d3, d4b, d5-d12).
- Read by hand, and also a kill on either d1: any row whose session timeout is not 4.5 min.
- The bars catch a broken arm (a cap that cuts most tasks, a root that retries without limit, a solver that stops
  editing), not the arm's normal spread.

## Runs

| Arm | Cohort | Draws | Run ids |
|---|---|---|---|
| control | `cohorts/cdev2-79.txt` | 12 | `R-024-e4b-ctl-4p5-d1..d12` |
| retry | `cohorts/cdev2-79.txt` | 12 | `R-024-e4b-retry-4p5-d1..d12` |

**Blind guess (not a reading), as R-022.** Passes the d1 gates: 95%. Helps: 35%. Kept on mechanism: 30%. Dropped: 35%.

## Queued (2026-11-22)

- Draws, all `-w pleiades-0-23`, no dependency, as (control, retry): d1 60364/60365, d2 60366/60367, d3 60368/60369,
  d4 60370/60371, d5 60372/60373, d6 60374/60375, d7 60376/60377, d8 60378/60379, d9 60380/60381, d10 60382/60383,
  d11 60384/60385, d12 60386/60387.
- Gate actors (`tools/gate_actor.sh`): retry d1 on 60365 and control d1 on 60364, with the bars above. Each cancels
  every other R-024 job on a kill.

## Draw-1 gates (reading 1), 2026-11-22: both PASS

- Control d1 (60364, 49 min): resolved 5, empty 11, time caps 3 (all report 4.5 min), no server error. PASS.
- Retry d1 (60365): resolved 5, empty 9, time caps 5 (all report 4.5 min), `retry_miss` 1, `solve_calls_gt3` 1, no
  server error. PASS.
- The other draws keep running. The decision waits for all 24.

## Decision (reading 3), 2026-11-22: **Dropped**

- All 24 draws COMPLETED on pleiades-0-23: 79 rows each, 0 model-server errors, 0 out-of-memory kills. No re-runs.
- Resolved per draw (`tools/paired_boot.py`, 79 tasks, 10,000 resamples, seed 0):
  - retry: 5, 7, 8, 6, 7, 8, 7, 6, 9, 6, 10, 7 (mean 7.17);
  - control: 5, 4, 8, 5, 10, 8, 5, 6, 7, 10, 5, 9 (mean 6.83).
- **Paired difference +0.33 solves per draw, 90% CI −1.08..+1.83.** Wall ratio 133.0 / 117.9 s = **1.13**.
- Applying R-022 reading 3 as written:
  - Helps: the CI lower bound is not above 0. No.
  - Kept on mechanism: rescued is 10 / 12 = 0.83 per draw (≥ 0.5, yes) and the wall ratio is 1.13 (≤ 1.4, yes), but
    the point estimate +0.33 is below +0.5. No.
  - **Dropped.**

## Mechanism (reading 4)

| Count, 12 draws | Control | Retry |
|---|---|---|
| first attempt empty / non-empty / unknown | 167 / 646 / 131 | 168 / 674 / 105 |
| retried | 0 | 162 |
| `retry_miss` | 167 | 6 |
| rescued | 0 | 10 |
| over-retry | 0 | 5 |
| `solve_after_submit` | - | 7 |
| tasks with more than 3 `solve` calls | 6 | 14 |
| empty patches | 195 (16.3 per draw) | 78 (6.5 per draw) |
| time caps (4.5 min) | 47 (3.9 per draw) | 84 (7.0 per draw) |
| tasks solved at least once | 19 | 21 |
| task wall mean / p50 / p90 / p99 | 117.9 / 94 / 250 / 380 s | 133.0 / 108 / 275 / 373 s |
| rows over 270 s | 7.5% | 11.7% |
| Kaggle projection `120 × (mean wall + 60 s)` | 5.93 h | 6.43 h |

- Both arms project well inside the 11.0 h gate.
- **Against R-021 (8 min), a check on the estimate, not a reading.** The 270-s cut of R-021 predicted 7.42 against 6.42.
  At 4.5 min the retry arm gave 7.17 (R-021: 7.58), and the control 6.83 (R-021: 6.50). Rescued fell from 13 to 10
  over 12 draws. Retry time caps rose from about 0.7 to 7.0 per draw. The control's rise is inside its draw-to-draw
  spread.
- **Stated, not a reading.** Rescued counts tasks whose first attempt was empty and that ended resolved. The control's
  layout cannot produce those. That argues for a real gain near the rescued rate (0.83 per draw). The pre-registered
  rule asked for the paired point estimate as well, and that is +0.33. The rule stands. The two rounds' CIs
  (R-021 +0.08..+2.08, R-024 −1.08..+1.83) overlap, and no pooled reading was registered, so none is made.

## What this means (as pre-registered)

- At the Kaggle cap the retry layout does not show a gain that pays for its time. **The E4B Kaggle candidate stays
  the EXP-050 single loop.** H-003 is withdrawn on the consolidated branch.
- The retry trees and tools are kept. Any further retry round needs a new pre-registration and a change of design,
  not more draws of this one.

## Correction, 2026-11-22 (after the decision; the readings above are not changed)

- **The premise of R-022 to R-024 was wrong.** R-022 said the Kaggle candidate must run at 4.5 min because of the pack
  gate `120 × (cap + 1.0) ≤ 11.0 h`. The shipped configs do not:
  - the E4B EXP-050 upload (`submissions.md` row 14) is "variant A", 8 min / 28 calls. Variant B at 4.5 min was not
    uploaded;
  - the 31B v24 uploads (rows 11-13 and 17) run at 8 min under a recorded gate override (`--skip-budget-gate`,
    formula 18.00 h, measured projection 10.04 h).
- So the 4.5-min round measured a cap that nothing ships with. Its result stands as a fact about 4.5 min. **The
  ship decision is governed by R-021 at 8 min, the shipping cap**, whose pre-registered reading was "helps" (+1.08,
  CI +0.08..+2.08).
- Kaggle time at 8 min, from the R-021 retry rows: mean task wall 139.7 s, p50/p90/p99 104/295/485 s, so
  `120 × (mean + 60 s)` = 6.66 h at Ada speed. EXP-048 projected the E4B single loop at 3.56-3.96 h on L4x4; at 1.23x
  that is about 4.4-4.9 h. Either is far inside 11.0 h. Shipping at 8 min needs the same recorded override as
  rows 11-17.
- H-003 is reinstated on the consolidated branch, with its cap item corrected to 8 min. The mistake was mine.
