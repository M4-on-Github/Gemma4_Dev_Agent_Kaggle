# R-045: E4B three-solver race with no submit tool (pre-registration)

Written 2026-11-27, before any job of this round is submitted. Counts only. Follows R-044 (dropped: E4B runners
submitted without APPLIED in 6 of 20 tasks).

## Change against R-044

`trees/e4b-race3n` is `trees/e4b-race3` with `submit_patch` removed from the three runners (no agent holds it) and
the runner prompt cut to: call the solver, run the fixed finish command, reply. The first runner to take the lock
applies its solver's diff to `/workspace`. The task ends when all three branches end, and the scorer grades the
working tree as left (its fallback for a run without a submit; source read 2026-11-26).

Stated costs: the task lasts as long as its slowest branch; a task where no runner applies is graded on the emptied
tree, a miss.

## Arm and control

`R-045-e4b-race3n-d1..d8`, `--concurrency 1`, other settings and control (`R-041-e4b-rcheck-d1..d8`) as R-044.
d1 first; d2-d8 after the early check.

## Readings (written before any job runs)

0. **Smoke** (`runs/_cohorts/smoke-te.txt`, concurrency 1): both tasks served, no crash, three solvers active.
1. **Early mechanism check on d1 at 20 rows** (no resolved count looked at). Cancel unread and drop if any holds:
   - more than 0.15 of solvers land an edit outside their worktree;
   - a runner's finish command prints APPLIED in fewer than 10 of 20 tasks;
   - the graded patch deletes files (emptied tree handed in) in more than 8 of 20 tasks;
   - mean task wall above 300 s.
2. **Served check** per draw: 79 rows, all served; one re-run with an `r` suffix.
3. **Decision** (`tools/paired_boot.py`, arm x8 against rcheck x8): **promote** at +1.5 or more with CI lower bound
   above -0.5 and mean task wall 300 s or less; **harm** at -1.5 or less; **not kept** otherwise.
4. **Mechanism, per draw:** tasks with APPLIED; emptied-tree patches; solvers ending EMPTY; landed outside edits;
   time-cap tasks; mean wall; SD of solves over draws.

**Blind guess.** Early check pass 50%. Promote 15%.

## Smoke (job 68054, 2026-11-27): PASS

Both tasks served, no crash, three solvers active in both; neither graded patch deletes files; task walls 94 s and
80 s. After the branches end the scorer prompts for continuation and the runners reply with text (about 10-30 s per
task). d1 submitted.

## Early mechanism check on d1 at 20 rows (job 68055, 2026-11-27): PASS as written

No resolved count was looked at.
- Landed outside edits: 4 of 57 solvers (0.07; bar 0.15).
- APPLIED printed in 15 of 20 tasks (bar 10).
- Graded patch deletes files in 6 of 20 (bar 8): 4 tasks where no runner applied, and 2 where a runner applied and a
  solver started again by the scorer's continuation prompt then re-ran its first command, which emptied the root.
- Mean task wall 105.3 s (bar 300 s).

**Deviation (logged before any resolved count is read):** the solver's first command now skips the delete once the
lock exists (`[ -d /workspace/.git/race.lock ] || ...`), which removes the 2-in-20 case. d1 (68055) was cancelled
unread and is re-run with d2-d8 on the fixed tree; run names are unchanged except d1, which becomes `d1r`.

## Results (2026-11-27, readings applied as written)

2. **Served check: pass.** All 8 draws (d1r, d2-d8) have 79 rows and 79 served tasks.
3. **Decision: harm.** Race 7, 5, 7, 3, 7, 5, 6, 6 (5.75) against rcheck 9, 9, 10, 7, 8, 7, 8, 7 (8.12): **−2.38 per
   draw, 90% CI −4.50..−0.50**. Mean task wall 151.7 s (rcheck 149.2 s; bar 300 s).
4. **Mechanism, means per draw:** no runner applied (empty or emptied-tree patch) 19.75; time-cap tasks 3.9; SD of
   solves 1.39. Solvers ending EMPTY and which solver won were not counted.

**Where it loses (not a reading).** On the 59.25 tasks per draw where a runner applied, the race solves 5.75 and
rcheck expects 6.00. On the 19.75 where none applied it solves 0 and rcheck expects 2.12. A race patch resolves at
0.097, an rcheck patch at 0.108.

**Lesson.** For the E4B the first finisher is no better than one attempt, so the race has no gain to set against the
tasks where no runner applies. R-047 (restart on EMPTY) is cancelled unread by its own rule (job 68074). The race
line closes for the E4B.
