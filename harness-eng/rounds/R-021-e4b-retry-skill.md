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

## Queued (2026-11-22)

- Smoke `S-021-e4b-retry-smoke`: job 60195.
- Draws, all `afterok:60195`, as (control, retry): d1 60196/60197, d2 60198/60199, d3 60200/60201, d4 60202/60203,
  d5 60204/60205, d6 60206/60207, d7 60208/60209, d8 60210/60211, d9 60212/60213, d10 60214/60215, d11 60216/60217,
  d12 60218/60219.
- Gate actors: the smoke on 60195, retry d1 on 60197, control d1 on 60196. Each cancels every other R-021 job on a
  kill.

## Smoke (reading 1), 2026-11-21 23:20Z: PASS as written; one mechanism defect recorded before any draw lands

- 60195: 8 rows SUCCESS; resolved 1; empty 3. `solve` calls {1: 5, 2: 3}; root model calls at most 6. Every skill
  count printed an integer: 7 of 8 tasks ran the count, and none printed anything else. `retry_miss` 0. So the
  pre-registered gates pass, and the draws were released by `afterok`.
- **Defect the `retry_miss` definition does not see.** Event order, tool names only:
  - 3 first attempts were empty.
  - In 1, the retry ran as designed: count 0, `solve`, count 1, `submit_patch`.
  - In 2, the root called `submit_patch` before its second `solve`. In one of them the root never ran the count;
    in the other the count printed 0 and the root submitted anyway.
  - A `solve` after a submit cannot change the outcome. The solver's final text then ends the task with the empty
    patch already submitted. So the effective retry rate in the smoke is 1 of 3.
- **Also seen:** 1 task where the count printed 1 but the patch was empty. The changed file was most likely one
  `submit_patch` strips, or an ignored scratch file. That error leads only to not retrying.
- **Handling.**
  - The gates are not re-read, and the draws run as queued. The arm is the layout as the E4B follows it, so the
    decision reading measures it as it is.
  - `tools/retry_counts.py` gains `solve_after_submit`, reported per draw under reading 4 and not a gate. It
    reads 2 in this smoke and 0 in both R-020 smokes.
  - **Expectation, written now:** with 1 of 3 retries effective, the simulated +1.0 per draw on Ada shrinks to
    about +0.3. "Helps" is unlikely. "Kept on mechanism" needs a point estimate of at least +0.5 and rescued of at
    least 0.5 per draw, which is also unlikely.
  - If the round is dropped for this reason, the next variant puts the decision in the script: it prints SOLVE
    AGAIN or SUBMIT NOW instead of a number. Not queued: Ada is near full (asingal2 holds 15 of the 16 GPUs) and
    R-021 already holds the queue.

## Draw-1 gates (reading 2), 2026-11-22: both pass

- Control d1 (60196): 79 rows SUCCESS; resolved 9; empty 15; time caps 0; mean task wall 104.7 s; one
  `submit_patch` per task. PASS.
- Retry d1 (60197): 79 rows SUCCESS; resolved 7; empty 4; time caps 1; mean task wall 132.5 s; root calls at most 9;
  `solve` calls {1: 59, 2: 16, 3: 4}, none more than 3; first attempt empty 12, retried 12, **`retry_miss` 0**,
  rescued 0; `solve_after_submit` 0. PASS. The draws ran on.

## Deviation, out-of-memory jobs (2026-11-22 01:30Z, recorded before reading 3 is computed)

- 13 of the 24 draw jobs ended `OUT_OF_MEMORY` (64G cgroup), all on pleiades-0-17: control d2-d8, d10 and retry
  d4, d6, d7, d9, d11. None of the 7 draws on pleiades-0-23 did.
- 12 of the 13 are complete: 79 SUCCESS rows, no model-server error in any row or log, and error counts
  (session timeout 0-2, tool budget 0-2) within the range of the clean jobs. Their OOM event is logged after the run's
  `done` line. **They are kept.**
- **Control d4 (60202) is not valid.** The vLLM server stopped serving at task 21. Tasks 1-20 are normal,
  tasks 21-41 end at the session timeout, and tasks 42-79 end in a model-server error (`litellm.InternalServerError`,
  347 log lines). It reads resolved 2, which is a server failure, not an agent outcome.
- **Change.**
  - Control d4 is re-run as `R-021-e4b-ctl-ada-d4b` with the same tree, cohort and flags (4 CPUs, 64G, 1 Ada GPU).
    It is pinned to pleiades-0-23 (`-w`), since no job there ran out of memory.
  - Reading 3 then uses control d1-d3, d4b, d5-d12 against retry d1-d12. If d4b also fails the same way, reading 3
    uses control d1-d3 and d5-d12 (11 draws). The paired statistic is per-task resolve rates, so the arms need not
    have equal draw counts. 60202's rows are not read for any reading.
  - The bars of readings 3 and 4 are unchanged.
- Cause not established. Most likely candidate: memory charged to the cgroup on 0-17 that is not used on 0-23. The
  clean 0-23 jobs peak at 46-56 GB RSS.

## Decision (reading 3), 2026-11-22: **Helps**

- All 24 valid draws are complete: retry d1-d12, and control d1-d3, d4b (job 60258, pleiades-0-23, 42 min,
  no OOM), d5-d12. Each has 79 SUCCESS rows and 0 model-server errors. The d12 pair (60218/60219) also ended
  `OUT_OF_MEMORY` after the run, in the same way as the 12 kept jobs, so the pair is kept under the deviation above.
- `tools/paired_boot.py`, retry d1-d12 against control (d1-d3, d4b, d5-d12), 79 tasks, 10,000 resamples, seed 0:
  - resolved per draw: retry 7, 12, 6, 9, 9, 7, 8, 6, 8, 5, 7, 7 (mean 7.58); control 9, 4, 6, 5, 6, 6, 9, 8, 5, 7,
    4, 9 (mean 6.50);
  - **difference +1.08 solves per draw, 90% CI [+0.08, +2.08]. The lower bound is above 0, so the arm helps.**
  - wall ratio 139.7 / 113.3 s = **1.23**.
  - **By the reading, the E4B frozen config uses the retry layout.**
- Sensitivity (reported, not a reading): using only the jobs with no OOM event (retry d1, d2, d3, d5, d8, d10;
  control d1, d4b, d9, d11), the difference is +1.75, CI [+0.25, +3.33]. The sign does not depend on the kept OOM
  jobs.
- Mechanism (reading 4), summed over 12 draws per arm:

  | | Control | Retry |
  |---|---|---|
  | First attempt empty | 192 | 169 |
  | Retried | 1 | 163 |
  | `retry_miss` | 191 | **6** |
  | **Rescued** (resolved after an empty first attempt) | 0 | **13 (1.08 per draw)** |
  | Over-retry (second `solve` after a non-empty first) | 0 | 5 |
  | `solve_after_submit` | 2 | 12 |
  | Tasks with more than 3 `solve` calls | 8 | 18 |
  | Empty patches (per draw) | 208 (17.3) | 63 (5.3) |
  | Time caps | 5 | 9 |
  | Tasks solved in at least one draw | 16 | 24 |

  - The rescue count, 13, matches the paired gain, +1.08 per draw. The added solves come from retried empty attempts
    and not from a change to first attempts.
  - So the R-018 limit (a retry starts in the leftover workspace) does not stop a retry from working. The smoke's
    `solve_after_submit` defect (2 of 3) did not recur at that rate: 12 of 169 empty first attempts.
  - Tasks with more than 3 `solve` calls also occur in the control (8), where the root prompt allows one. This is a
    root habit of both arms. It is not a gate past d1, and no such task ran past the caps.
- **Kaggle time.** This round ran with an 8.0-minute task cap. The E4B Kaggle candidate (EXP-050) uses 4.5 minutes.
  - Counting a resolved row as lost when its task wall is over 270 s gives retry 7.42 against control 6.42 per
    draw, so the gain survives the shorter cap on this estimate.
  - 11.5% of retry rows run past 270 s (control 7.4%). Task wall p50/p90/p99: retry 104/295/485 s, control
    88/228/454 s.
  - The Kaggle check goes to handoff H-002.
- Drift check: control mean 6.50 against R-017 Turing 6.88, R-011 base 7.00, R-008 Ada base 6.67. Control
  empties 17.3 per draw, close to R-017's 16.8: it is the R-017 solver without `submit_patch`.
