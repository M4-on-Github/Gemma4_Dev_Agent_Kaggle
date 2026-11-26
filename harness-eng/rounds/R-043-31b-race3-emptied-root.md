# R-043: 31B three-solver race with the root working tree emptied (pre-registration)

Written 2026-11-27, before any job of this round is submitted. Counts only. Follows R-042 (dropped at its early
mechanism check: 0.37 of solvers misplaced edits by relative paths; the race mechanism itself worked).

## Change against R-042's last tree

`trees/31b-kf-race3d` is `trees/31b-kf-race3` with two edits:
- each solver's fixed first command, after making its worktree, deletes the tracked working files directly under
  `/workspace` (`git ls-files -z | xargs -0 rm -f`). A read or edit by a relative or `/workspace/...` path then
  fails with a file error, and the prompt says to repeat it with the full worktree path;
- the runner's finish command restores `/workspace` (`git checkout -- .`, `git clean -fdq`) before it applies.

Stated costs: a task where no runner submits is graded on a tree with its files deleted, which is a miss (as an
empty patch is). A solver's own check may fail to import a package that is installed from `/workspace`.

## Arm, control, flags

As R-042 after its deviations: `R-043-31b-kfrace3d-d1..d8`, `--concurrency 1`, `max_tool_calls` 200,
`max_time_minutes` 9.9, cohort `cohorts/cdev2-79.txt`; control `R-037-31b-kfctl-d1..d8` (existing, not concurrent,
4 streams per GPU against 3 here; the wall reading carries that caveat). d1-d4 first, d5-d8 after the early check.

## Readings (written before any job runs)

0. **Smoke** (`runs/_cohorts/smoke-te.txt`, concurrency 1): pass needs both tasks served, no crash, and at least one
   task where a runner applies and submits. One fix and re-smoke allowed, logged first.
1. **Early mechanism check on d1 at 20 rows** (no resolved count looked at). Cancel all draws unread and drop the
   round if any holds:
   - more than 0.15 of solvers land an edit outside their worktree;
   - a runner applies and submits in fewer than 14 of 20 tasks;
   - mean task wall above 443 s.
2. **Served check** per draw: 79 rows, all served; one re-run with an `r` suffix.
3. **Draw-1 kill gate:** 25 or more empty-or-deleted-tree patches, or mean task wall above 443 s.
4. **Decision** (`tools/paired_boot.py`, arm x8 against kfctl x8):
   - **Promote:** +1.5 or more, CI lower bound above -0.5, wall ratio 1.00 or less. A promote means "worth a Kaggle
     notebook timing run", not "ship".
   - **Harm:** -1.5 or less. **Not kept:** anything else.
5. **Mechanism, per draw:** runner applied and submitted; which solver won; misplaced edits; failed file calls per
   solver before its first edit; empty patches; time-cap tasks; mean wall; SD of solves over draws against 2.64.

**Blind guess.** Smoke pass 75%. Early check pass 60%. Promote 25%, not kept 55%, harm 20%.
