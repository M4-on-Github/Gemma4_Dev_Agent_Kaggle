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
