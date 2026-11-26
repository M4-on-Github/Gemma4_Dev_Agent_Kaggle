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
