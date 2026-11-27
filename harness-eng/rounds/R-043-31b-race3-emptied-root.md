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

## Smoke (job 68021, 2026-11-27): PASS

Both tasks served, no crash, a runner submitted in both, both resolved; 0 of 6 solvers edited outside their worktree;
task walls 105 s and 349 s. Draws d1-d4 submitted next; early check at 20 rows of d1 as written.

## Early mechanism check on d1 at 20 rows (2026-11-27): PASS

Draw ids: d1-d4 = 68022-68025. No resolved count was looked at.
- **Edits landed outside a solver's worktree: 0 of 60 solvers** (bar 0.15). 12 solvers made a `write_file` call with a
  path outside their worktree; all 12 calls failed with a file error and none landed. (A first count of 12 of 60
  counted these attempts; the reading is about landed edits.) After the failed call, 6 solvers made their next edit
  inside the worktree and 6 made no further edit call.
- **A runner applied and submitted: 19 of 20** (bar 14). One submit of 0 files; no failed apply.
- **Mean task wall 276.0 s** (bar 443 s; kfctl 385.6 s at 4 streams per GPU against 3 here).
- Also: three solvers active and all worktrees made in 20 of 20; 1 empty patch; 1 time cap.

d5-d8 submitted.

## Results (2026-11-27, readings applied as written)

Draw ids: d5-d8 = 68048-68051.

2. **Served check: pass.** All 8 draws have 79 rows and 79 served tasks.
3. **Draw-1 kill gate: pass.** d1 has 13 empty-or-deleted-tree patches (bar 25) and a mean task wall of 320.1 s (bar
   443 s).
4. **Decision: not kept.** Race 32, 26, 29, 32, 32, 30, 26, 34 (30.12) against kfctl 35, 32, 27, 30, 29, 30, 33, 27
   (30.38): **−0.25 per draw, 90% CI −2.62..+2.00**. Wall ratio 330.3 / 385.6 = 0.857 (3 streams on one GPU against
   the control's 4, so the ratio does not carry to Kaggle).
5. **Mechanism, means per draw:**

   | | race |
   |---|---|
   | a runner applied a patch | 62.75 |
   | tasks with a submit | 69.1 |
   | empty patches | 0.75 |
   | deleted-tree patches (no runner applied; the fallback graded the emptied tree) | 10.4 |
   | time-cap tasks | 10.4 (kfctl 15.5) |
   | solvers with an edit call outside their worktree (attempts, not landed edits) | 0.27 of solvers |
   | SD of solves over draws | 2.95 (kfctl 2.64) |

   Which solver won was not counted.

**Where the race gains and loses (not a reading; computed after the decision).**

| Tasks | per draw | race solves | kfctl expects on the same tasks |
|---|---|---|---|
| a runner applied a patch | 67.9 | 30.12 | 27.78 |
| no runner applied (81% at the time cap) | 11.1 | 0 | 2.59 |

- By control class: the 17 tasks kfctl solves 8 of 8: race 16.00; the 26 swing tasks: 13.50 against 13.38; the 36
  tasks kfctl never solves: 0.62. Three tasks are solved only by the race and three only by kfctl.
- A submitted race patch resolves at 0.444, a kfctl patch at 0.452.
- In the no-apply tasks one runner's solver had usually come back with no edit (its finish command printed EMPTY in
  about three quarters of them) and that runner then stayed idle; in about half of them another solver had a landed
  edit in its worktree when the task ended.

**Agreement picker, simulated on kfctl (no GPU, not a reading).** Over all triples of the 8 kfctl draws: a random
non-empty patch of three 33.14, the patch with the highest line overlap with the other two 34.12, an oracle 37.39. All
three need every attempt to run to its end, which does not fit the time budget.

**Lesson.** The first finisher is as good as a single attempt and no better per patch; the race's gain on finished
tasks is cancelled by the tasks where no runner applies and the emptied tree is graded. The fix to test is an idle
runner that restarts its solver and, if still empty, applies another solver's edits (R-048).
