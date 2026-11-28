# R-052: 31B, three parallel attempts with a checkpoint submit and an agreement stop (pre-registration)

Written 2026-11-28, before any job of this round is submitted. Counts only.

## Why

- Race rounds R-043 to R-048 took the first finisher. They gained about 2.3 solves where a runner applied a patch and
  lost about 2.6 on the roughly 11 tasks per draw that ended with nothing applied.
- Offline, over independent control draws: first non-empty patch of three 33.14, the patch with the highest line
  overlap 34.12, oracle 37.39, against the control's 30.38.
- Harness source (read 2026-11-28): `submit_patch` stores the diff at the moment of the call, and a task that ends
  at the time cap is graded on the stored diff. So an early submit is a safe checkpoint, and a later submit replaces
  it. A text-only reply from a runner after any submit ends the task.

## Arm

`trees/31b-kf-agree` = `trees/31b-kf-race3h` with new runner prompts and one finish command per runner:

- Every finished, non-empty attempt is saved and the runner's working copy is reset for a fresh attempt.
- **First** finished attempt: applied and submitted at once; the runner starts a fresh attempt.
- **Later** attempt whose normalized changed lines have Jaccard 0.5 or more with a saved one: applied, submitted,
  task ends. Without agreement the runner starts a fresh attempt.
- **Third** finished attempt ends the task: applied if it shares any changed line with a saved one, otherwise the
  checkpoint stands.
- At most four solver calls per runner. Solver prompts, sampling and caps as in R-048.

Scratch test of the command (throwaway repository, sh and bash): empty, first, second disagreeing, second agreeing,
third with partial overlap, third without overlap print AGAIN, FIRST, AGAIN, FINAL, FINAL, KEEP; the working copy is
clean after the reset.

## Readings (written before any job runs)

1. Smoke (2 tasks): both served; a FIRST followed by `submit_patch`; no engine error. Draws are chained behind it.
2. Draw-1 kill gate: 25 or more empty patches, or 3 or more tasks graded on a tree with deleted files.
3. Decision, `R-052-31b-agree-d1..d4` against kfctl x8 (30.38): extend to 8 draws at +1.5 or more; promote at 8
   draws with +2.0 and CI lower bound above 0; harm at -1.5.
4. Time is reported, not gated here: mean task wall, share of tasks ending FINAL, KEEP, at the cap with a
   checkpoint, at the cap without one. The Kaggle fit is decided from these and the L4 stream-speed measurement
   (handoff H-note); a promotion needs both.
5. Mechanism: tasks with a checkpoint; tasks where the final patch differs from the checkpoint and the solve rate
   of each group; runner text replies that ended a task early; solver calls per runner.

**Blind guess.** Tasks with nothing applied fall from about 11 to 4 or fewer: 60%. Mean solves 32 or more over four
draws: 35%. Extension: 25%. Mean wall above 452 s: 65%.

## Smoke and a deviation, logged 2026-11-28 07:50 UTC before any draw is read

- **R-052 smoke (job 68464, after two server-start failures on GPUs occupied by another user's processes):** both
  tasks served. Task 1: two finish commands, both copied exactly, two `submit_patch` calls, resolved in 194 s.
  Task 2: no solver finished before the cap (605 s), no finish command ran, and the task was graded on the
  emptied tree, as in the race rounds' no-apply tasks. Reading 1 passes.
- **Deviation.** Kill-gate clause "3 or more tasks graded on a tree with deleted files" was written for tasks that
  had a submitted patch and were still graded on an emptied tree. As written it would also count every task where
  no attempt finished, which the race rounds show at about 11 per draw and which this layout cannot remove. The
  clause is read as: 3 or more tasks **with a submit** graded on an emptied tree. Tasks with no finished attempt
  are counted and reported under reading 4/5. Changed before any draw result exists.

## Draws d1-d4 void: submitted at the wrong task concurrency (logged 2026-11-28 10:55 UTC)

- **What happened.** Draws `R-052-31b-agree-d1..d4` were submitted with `--concurrency 4`, the setting of the
  single-stream rounds. The race rounds this layout comes from (R-042..R-049) ran at `--concurrency 1`, because one
  task already holds three solver streams. Four tasks at once put twelve streams on one GPU.
- **Evidence it is the setup, not the layout.** Draw 1 (the only complete one): 14.9 s of task wall per solver call
  against 4.4 s in `R-048-31b-kfrace3h-d1/d2`; 40.8 solver calls per task against 81-84; a finish command ran in
  12 of 79 tasks; 74 of 79 tasks ended at the cap with nothing applied; job wall 12,485 s for 79 tasks of 608 s
  mean, so 3.8 tasks ran at once. The two-task smoke, which ran at concurrency 1, had 5.6 s per solver call.
- **Deviation.** d1 is void and is not a reading of the design; its solve count (4) is recorded here and not
  compared with the bar. d2-d4 were cancelled at 60-64 of 79 tasks; their partial counts (2-4 solves, same pace)
  were seen in the diagnosis and are void too. The kill gate is read again on the first rerun draw.
- **Rerun.** Same tree, same cohort, `--concurrency 1`, run ids `R-052-31b-agree-r1..r4`, job time limit 15 h
  (79 tasks at up to 610 s is 13.4 h). Readings 2-5 apply to r1..r4 as written. Nothing else changes.
