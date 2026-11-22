# R-023: E4B retry on an empty attempt at the Kaggle cap, 4.5 min, re-registered with calibrated bars (pre-registration)

Written 2026-11-22, after R-022 was killed by its control gate and before any job of this round is submitted. Counts
only; no trace content. Tweak id **T-e4b-022**, unchanged.

## What carries over from R-022

- Why, the two trees (`trees/e4b-r022-ctl-4p5`, `trees/e4b-r022-retry-4p5`, committed at 5176b41), flags, the pin to
  pleiades-0-23, no smoke, cost (about 17 Ada GPU-h), the server-death rule (reading 2), the decision rule
  (reading 3), the mechanism readings (reading 4) and what each outcome means: **as R-022, word for word.**
- **What R-022 showed, and is not read for effect:** control d1 resolved 4, empty 23, time caps 1, with the session
  timeout reported as 4.5 min. Its retry d1 was cancelled at 69 of 79 rows and never read. No R-022 row enters this
  round's decision.

## The only change: draw-1 kill bars

The rule: each bar lies outside that arm's own per-draw range over R-021's 12 draws of the same tree at 8 min, with a
margin. At 4.5 min the time-cap counts are expected to rise, so that bar keeps R-022's reasoning.

| Arm | Field | R-021 range | R-022 bar | **R-023 bar (kill on)** |
|---|---|---|---|---|
| retry d1 | resolved | 5-12 | ≤ 3 | **≤ 3** |
| retry d1 | empty | 2-11 | ≥ 23 | **≥ 23** |
| retry d1 | time caps | 0-2 | ≥ 20 | **≥ 20** |
| retry d1 | `retry_miss` | - | ≥ 3 | **≥ 3** |
| retry d1 | `solve_calls_gt3` | 0 | ≥ 1 | **≥ 1** |
| control d1 | resolved | 4-9 | ≤ 3 | **≤ 2** |
| control d1 | empty | 10-24 | ≥ 23 | **≥ 32** |

- Read by hand, and also a kill on either d1: any row whose session timeout is not 4.5 min.

## Runs

| Arm | Cohort | Draws | Run ids |
|---|---|---|---|
| control | `cohorts/cdev2-79.txt` | 12 | `R-023-e4b-ctl-4p5-d1..d12` |
| retry | `cohorts/cdev2-79.txt` | 12 | `R-023-e4b-retry-4p5-d1..d12` |

**Blind guess (not a reading), as R-022.** Passes the d1 gates: 90%. Helps: 35%. Kept on mechanism: 30%. Dropped: 35%.
