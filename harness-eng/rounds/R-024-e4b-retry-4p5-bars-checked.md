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
