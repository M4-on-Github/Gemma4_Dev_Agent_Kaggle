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
