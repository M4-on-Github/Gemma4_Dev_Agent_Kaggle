# R-037: 31B call cap under Kaggle's binding limit (pre-registration)

Written 2026-11-25, before any job of this round is submitted. Counts only; no trace content, no ids. User goal
(2026-11-25): the highest hidden-test score, from the 31B and the E4B, in the days left. Background:
`final-week-plan.md` (Kaggle against cluster; what ends a Kaggle 31B task).

## Why

- **Kaggle is call-bound and the cluster is time-bound.** On Kaggle (EXP-028 R and RH, EXP-003; 144 task-draws,
  shipping budget), 37.5% of 31B tasks end at the 28-call cap and 19.4% at the time cap. On the cluster (562
  task-draws) those shares are 18.5% and 30.6%. The cluster serves 4 tasks per GPU, so its effective decode per stream
  is 23.2 tok/s, against 28.7 on Kaggle.
- **Kaggle tasks that hit the call cap resolve 2 of 54 times.** Finished tasks resolve 24 of 67.
- **T-31b-001 (calls 28 → 40, not kept) was screened under the cluster's binding limit.** Its extra calls ran into
  the time cap, which binds less on Kaggle.
- **Calls 40 does not fit the budget on Kaggle** (about 11.6 h projected). Calls 34 with `max_time` 8 → 7 projects to
  about 10.45 h by the desk estimate in `final-week-plan.md`.

## Arms

| Run | Tree | Draws | Stands in for |
|---|---|---|---|
| `R-037-31b-kfctl-d1..d8` | `trees/31b-kf-ctl` | 8 | Kaggle `31b-base` (28 calls, 8 min) |
| `R-037-31b-kfc34-d1..d8` | `trees/31b-kf-c34` | 8 | Kaggle `trees/31b-c34t7` (34 calls, 7 min) |

- **Shippable tree `trees/31b-c34t7`.** It is `31b-base` with three changes: `max_tool_calls` 34, `max_time_minutes`
  7, and the prompt line "You have 34 tool calls and 7 minutes".
- **Cluster stand-ins.** Each is its Kaggle tree with `max_time_minutes` scaled by ×1.2375 (28.7 / 23.2): 9.9 for 8,
  8.66 for 7. The prompt keeps the Kaggle wording, so the model is told exactly what it is told on Kaggle.
  - `diff -r` against `31b-base` shows only `eval_config.yaml` lines and, for the c34 trees, that one prompt line.
- **Validator.** All three trees validate with the same two errors as `31b-base`, and nothing else. The errors are
  the cap-only packing gate (the 31B ships on its measured projection) and the known `compile_submission` signature
  mismatch.
- **Cohort and flags.** Cohort `cohorts/cdev2-79.txt`. Flags as R-036: `sbatch --parsable --hold -J heng_31b
  slurm/eval.sbatch <run> <tree> cohorts/cdev2-79.txt --concurrency 4 --py313 env/py313-scorer/bin/python3.13
  --task-envs env/taskenvs`, 1 Ada GPU, 4 CPUs.
- **Queue.** Arm and control draws are submitted interleaved (ctl d1, c34 d1, ctl d2, ...) and held. They are
  released by `tools/throttle_release.sh 2` (at most 2 running, user rule 2026-11-22).
- **Cost.** About 16 × 2.3 = 37 Ada GPU-h, about 19 h of wall clock at 2 running.

## Readings (written before any job runs)

1. **Served check, every draw, before any reading.** A draw is read only if it has 79 rows and every task is served
   (some agent step has prompt tokens). A draw that fails is re-run once with an `r` suffix, logged here first.
2. **Fidelity (reported; it limits what reading 3 can claim).** kfctl ×8: the share of task-draws ending at the call
   cap (`tool_calls >= max_tool_calls`) and at the time cap (`task_wall_s >= 0.98 × max_time`).
   - **Faithful:** the call-cap share is 0.28 or more and the time-cap share is 0.25 or less, closer to Kaggle (0.375,
     0.194) than to the cluster base (0.185, 0.306).
   - **Not faithful:** anything else. A promote under "not faithful" is downgraded to "not kept: screen not
     faithful".
3. **Decision.** Run `tools/paired_boot.py --arm` kfc34 ×8 `--base` kfctl ×8 on 79 tasks: solves per draw, 90% CI
   over tasks. The wall ratio is kfc34 mean task wall over kfctl mean task wall. The Kaggle projection is 10.04 h ×
   the wall ratio.
   - **Promote:** a point estimate of +1.5 or more, a CI lower bound above −0.5, and a wall ratio of 1.06 or less
     (projection 10.64 h or less). Next step: propose to the user a Kaggle dev-48 run of `trees/31b-c34t7` or a
     direct upload. Nothing ships without the user.
   - **Harm:** a point estimate of −1.5 or less.
   - **Not kept:** anything else, including any wall ratio above 1.06.
   - No extension: there is no time for one.
4. **Mechanism (reported for every outcome).** Per arm, means per draw:
   - call-cap, time-cap and empty-patch tasks; mean task wall; tool calls per task;
   - resolved on the tasks where the control draw hit the call cap.
5. **Draw-1 kill gate** (applied by hand when kfc34 d1 and kfctl d1 end; a kill cancels every held draw unread). Kill
   if kfc34 d1 has fewer than 79 served tasks after one re-run, or 25 or more empty patches, or a mean task wall above
   1.15 × kfctl d1. For scale, the 6 cluster base draws on cdev2-79 at 8 min had 13-17 empty patches each.

**Comparator, for scale (not a reading).** The cluster base on cdev2-79 at 8 min solves 28.67 per draw (6 draws).

**Blind guess (not a reading).** Faithful 60%. Promote 15%, not kept 75%, harm 10%. Wall ratio 0.95-1.05.

## Queued
- **R-037 queued 2026-11-25** (held, interleaved ctl/c34 d1..d8): 66317-66332. d1 pair 66317 (kfctl) and 66318 (kfc34) released at once; d2-d8 held until the reading-5 gate is applied by hand, then released by `tools/throttle_release.sh 2`.
