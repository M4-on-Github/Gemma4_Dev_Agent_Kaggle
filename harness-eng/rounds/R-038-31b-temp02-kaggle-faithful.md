# R-038: 31B temperature 0.2 under Kaggle's binding limit (pre-registration)

Written 2026-11-25, before any job of this round is submitted and before any resolved count of R-037 is looked at.
Counts only. User goal (2026-11-25): the highest hidden-test score in the days left.

## Why

- The four public notebooks that claim a public score of 0.20 to 0.22 (scouting note of 2026-11-17) all run the 31B
  at temperature 0.2. Our shipping tree, the rank-3 v24 bundle, runs at 1.0. Their scores are single draws, so this
  is a hint, not evidence.
- Our only temperature test is T-31b-010 (1.0 → 0.6): 2 draws on 20 tasks at the cluster's time-bound budget, 8.5
  against 8.5. It could not see an effect of 1 or 2 tasks, and it ran under the wrong binding limit (R-037, Why).
- It is one config line with no cost in tool calls. Its time cost is unknown and is measured here.

## Arm

| Run | Tree | Draws | Stands in for |
|---|---|---|---|
| `R-038-31b-kft02-d1..d8` | `trees/31b-kf-t02` | 8 | Kaggle `trees/31b-t02` (`31b-base` at temperature 0.2) |
| control: `R-037-31b-kfctl-d1..d8` | `trees/31b-kf-ctl` | 8 (reused) | Kaggle `31b-base` |

- `trees/31b-kf-t02` is `trees/31b-kf-ctl` with `temperature: 0.2` (`diff -r`: that line and its comment).
  `trees/31b-t02` is `31b-base` with the same change; it is the tree that would ship. Validator: the same two errors
  as `31b-base`, nothing else.
- **The control is reused, not concurrent.** R-037's kfctl draws ran on 2026-11-25 on the same GPU type; the R-038
  draws follow within a day. A fresh control would double the round to about 18 h, which the calendar does not have.
  The R-033 lesson (arms should share the queue period) is knowingly not met; reading 3 carries a wider bar for it.
- Cohort, flags and throttle as R-037 (`cohorts/cdev2-79.txt`, `--concurrency 4`, at most 2 running).
- Cost: about 8 × 2.3 = 18 Ada GPU-h, about 9.5 h of wall clock.

## Readings (written before any job runs)

1. **Served check** as R-037 reading 1 (79 rows, 79 served; one re-run with an `r` suffix, logged first).
2. **Fidelity.** R-037 reading 2 on kfctl ×8 applies unchanged. "Not faithful" there downgrades a promote here to
   "not kept: screen not faithful".
3. **Decision.** `tools/paired_boot.py --arm` kft02 ×8 `--base` kfctl ×8, 79 tasks, 90% CI over tasks; wall ratio =
   kft02 mean task wall / kfctl mean task wall; Kaggle projection = 10.04 h × wall ratio.
   - **Promote:** point estimate +2.0 or more (R-037 asks +1.5; the extra 0.5 is for the control not being
     concurrent), CI lower bound above 0, wall ratio 1.06 or less. Next: propose an upload of `trees/31b-t02` to the
     user. Nothing ships without the user.
   - **Harm:** −1.5 or less. **Not kept:** anything else, including any wall ratio above 1.06. No extension.
   - If R-037 also promotes, the two changes are not stacked untested. The one with the higher point estimate is
     proposed, and the other is reported.
4. **Mechanism (reported).** Per draw: call-cap, time-cap and empty-patch tasks, mean task wall, tool calls per task,
   completion tokens per task; the spread of solves across draws (sd) for each arm.
5. **Draw-1 kill gate** (by hand; a kill cancels d2-d8 unread): fewer than 79 served after one re-run, or 25 or more
   empty patches, or a mean task wall above 452 s (1.15 × kfctl d1's 393.0 s).

**Blind guess (not a reading).** Promote 10%, not kept 75%, harm 15%. Wall ratio 0.95-1.10. Lower spread across
draws: 65%.

## Queued
- **R-038 queued 2026-11-25** (held): d1..d8 = 67698,67699,67700,67701,67702,67703,67704,67705. d1 is released by `tools/throttle_release.sh 2` once R-037's release script has ended; d2-d8 stay held until the reading-5 gate.
- **Deviation, 2026-11-25 about 22:45 UTC (before any resolved count is looked at):** the user lifted the 2-running cap for the final-week rounds. The release script was stopped and the remaining held draws were released at once; draws now start as GPUs free up. R-038 d1 was held again for a few minutes so the R-039 smokes queue ahead of it.

## Draw-1 gate (applied by hand 2026-11-25): PASS

kft02 d1: 79 rows, 79 served; 18 empty (bar 25); mean task wall 392.7 s (bar 452 s). d2-d8 (67699-67705) released at
once (the 2-running cap is lifted for the final-week rounds).

## Results (2026-11-26, readings applied as written)

Job 67704 (d7) ended with SLURM state OUT_OF_MEMORY after its results were written; the run has 79 rows, all served
and graded, and is read (as R-037 job 66373).

- **Served check: pass.** All 8 draws have 79 rows and 79 served tasks.
- **Decision: harm.** kft02 29, 32, 27, 31, 26, 26, 30, 28 (28.62) against kfctl 35, 32, 27, 30, 29, 30, 33, 27
  (30.38): **−1.75 per draw, 90% CI −3.88..+0.25**. The point estimate is at or below the −1.5 harm bar.
- **Mechanism, means per draw (kft02 against kfctl):** empty 14.0 against 11.75; time-cap tasks 18.4 against 15.5;
  call-cap tasks 18.4 against 18.75; mean task wall 394.8 s against 385.6 s (ratio 1.024); calls 19.4 against 19.7.
- **Lesson.** Lower temperature does not steady the 31B; it leaves more tasks without a patch. Temperature stays 1.0.
  With T-e4b-004, 032b and 033 this closes temperature for both models.
