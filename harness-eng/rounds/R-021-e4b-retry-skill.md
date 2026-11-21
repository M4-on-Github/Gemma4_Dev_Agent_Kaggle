# R-021: E4B retry on an empty attempt, skill count (pre-registration)

Written 2026-11-22, before any job of this round is submitted. Counts only; no trace content. Tweak id **T-e4b-020**,
unchanged. This is R-020's design, re-registered with a smoke gate that does not depend on chance.

## What carries over from R-020

- **Trees.** `trees/e4b-r020-ctl` and `trees/e4b-r020-retry` as committed in cccd61b (retry tree after fix 1: the root
  has `solve`, `submit_patch` and the `change-count` skill, and no shell).
- Why, arms, flags, cost (about 17 Ada GPU-h), draw-1 kill gates, decision rule, mechanism readings and the blind
  guess: as R-020 §Why, §Change and arms, §Runs and readings 2-4, word for word.
- **What R-020 showed, and is not read for effect:**
  - control smoke 60113 passed;
  - in retry smoke 60138, every skill count printed an integer and the root branched and submitted as written,
    but no first attempt was empty.

## Smoke (the only change)

- `S-021-e4b-retry-smoke`, retry tree, `runs/_cohorts/smoke-empty8.txt`, concurrency 4.
- The 8 tasks of `cdev2-79` with the highest empty-patch rate over the 11 base draws (R-011 tu5 d1-d8, R-008 te2
  d1-d3), leaving out the 4 tasks of `smoke-empty4`. Their per-task empty rates are 1.00, 0.45 (4 tasks) and
  0.36 (3 tasks). The ids live only in gitignored `runs/_cohorts/`.
- **Gates (kill on any).** `status_SUCCESS<8`, `solve_calls_gt3>=1`, `root_calls_max>9`, and `retry_miss>=1`.
  The last is a task whose first attempt was counted 0 that did not call `solve` again.
- Read by hand, and also a kill: any skill count that is not an integer.
- If no first attempt is empty, the smoke passes on the other gates and the retry branch is covered by the d1
  `retry_miss` gate. That is stated here, before the run.

## Runs

- Draws `R-021-e4b-{ctl,retry}-ada-d1..d12`, cohort `cohorts/cdev2-79.txt`, interleaved, all `afterok` on the smoke.
  Gate actors on the smoke, retry d1 and control d1, as in R-020.
