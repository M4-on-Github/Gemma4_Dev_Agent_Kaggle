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

## Deviation (logged 2026-11-25, before any resolved count of this round is looked at)

- The run argument was given as `runs/<run>`, and `slurm/eval.sbatch` adds `runs/` itself, so d1 wrote to
  `runs/runs/<run>`. The two d1 directories were moved to `runs/<run>` unchanged. The 14 held d2-d8 jobs
  (66319-66332) had never started; they were cancelled and resubmitted with the bare run id, still interleaved and
  held: 66363, 66364, 66365, 66366, 66367, 66368, 66369, 66370, 66371, 66372, 66373, 66374, 66375, 66376.

## Reading 5 (d1 gate, applied by hand 2026-11-25): PASS

kfc34 d1: 79 rows, 79 served; 14 empty (bar 25); mean task wall 381.7 s against kfctl d1 393.0 s (bar 1.15 ×, 452 s).
kfctl d1: 79 rows, 79 served. d2-d8 released by `tools/throttle_release.sh 2`.
- **Deviation, 2026-11-25 about 22:45 UTC (before any resolved count is looked at):** the user lifted the 2-running cap for the final-week rounds. The release script was stopped and the remaining held draws were released at once; draws now start as GPUs free up.

## Results (2026-11-25, readings applied as written)

Job 66373 (kfctl d7) ended with SLURM state OUT_OF_MEMORY (98 GB against a 96 GB request). Its run has 79 rows, all
served and all graded, so it is read; the kill came after the results were written.

1. **Served check: pass.** All 16 draws have 79 rows and 79 served tasks.
2. **Fidelity: not faithful.** kfctl ×8: call-cap share 0.237 (bar 0.28 or more; Kaggle 0.375), time-cap share 0.196
   (bar 0.25 or less; Kaggle 0.194). The longer time limit moved the time cap to Kaggle's level but only part of the
   freed tasks ran into the call cap.
3. **Decision: not kept.** kfc34 30, 28, 27, 31, 33, 31, 31, 28 (29.88) against kfctl 35, 32, 27, 30, 29, 30, 33, 27
   (30.38): **−0.50 per draw, 90% CI −2.62..+1.62**. Wall ratio 376.3 / 385.6 = 0.976 (projection 9.80 h).
4. **Mechanism, means per draw:**

   | | kfctl | kfc34 |
   |---|---|---|
   | call-cap tasks | 18.75 | 13.38 |
   | time-cap tasks | 15.50 | 21.88 |
   | empty patches | 11.75 | 12.38 |
   | mean task wall (s) | 385.6 | 376.3 |
   | tool calls per task | 19.72 | 21.09 |
   | resolved on tasks where the control hit the call cap (18.75 per draw) | 2.25 | 1.88 |

   Six more calls took 5.4 tasks per draw off the call cap and put 6.4 onto the (shorter) time cap. The tasks the
   control lost at the call cap did not resolve more often with 34 calls.

**Lesson.** A task that has not converged by call 28 does not converge by call 34. The call cap is where
non-converging tasks stop, not what stops them. Calls 34 / time 7 is safe on time (0.976) but buys nothing.
