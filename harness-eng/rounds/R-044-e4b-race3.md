# R-044: E4B three-solver race (pre-registration)

Written 2026-11-27, before any job of this round is submitted. Counts only. The E4B form of R-043's tree, built
after R-043's early mechanism check passed on the 31B (0 landed outside edits, 19 of 20 tasks submitted by a runner).

## Why

- The only E4B change ever kept is a re-draw: retry on an empty patch (R-021, +1.08 per 79). R-041 reproduced it
  without a skill script (8.12 per 79 over 8 draws).
- The sequential retry shares one call and time budget and a leftover working tree. Best of 3 independent attempts
  has an oracle ceiling of 13.5 per 79 against 7.6 (final-week plan).
- The race runs the attempts side by side in separate worktrees, and a solver that changes nothing simply drops out.

## Arm and control

| Run | Tree | Draws | Concurrency |
|---|---|---|---|
| `R-044-e4b-race3-d1..d8` | `trees/e4b-race3` | 8 | 1 task (3 model streams per GPU) |
| control: `R-041-e4b-rcheck-d1..d8` (existing) | `trees/e4b-r041-retry-check` | 8 | 4 tasks |

- **Tree.** Root `ParallelAgent`, three runners, each with one `agent_tool` solver (the `e4b-r020-retry` solver
  prompt plus the working-copy section and full-path search of R-043). Runner finish command, lock and emptied root
  as R-043. `max_tool_calls` 200, `max_turns` 240, `max_time_minutes` 8 (the E4B shipping cap; no time scaling,
  as in R-021 and R-041).
- The control is not concurrent with the arm and runs 4 streams per GPU against 3. The E4B has spare time on Kaggle
  (R-025), so the wall reading is reported, not a promote condition, up to the bar below.
- Cohort `cohorts/cdev2-79.txt`. d1-d4 first; d5-d8 after the early check.

## Readings (written before any job runs)

0. **Smoke** (`runs/_cohorts/smoke-te.txt`, concurrency 1): pass needs both tasks served, no crash, three solvers
   active in both. One fix and re-smoke allowed, logged first.
1. **Early mechanism check on d1 at 20 rows** (no resolved count looked at). Cancel all draws unread and drop the
   round if any holds:
   - more than 0.15 of solvers land an edit outside their worktree;
   - fewer than 50 of 60 solvers make their worktree;
   - a runner applies and submits in fewer than 10 of 20 tasks;
   - a runner calls `submit_patch` without APPLIED in more than 3 of 20 tasks;
   - mean task wall above 300 s.
2. **Served check** per draw: 79 rows, all served; one re-run with an `r` suffix.
3. **Decision** (`tools/paired_boot.py`, arm x8 against rcheck x8):
   - **Promote:** +1.5 or more, CI lower bound above -0.5, mean task wall 300 s or less.
   - **Harm:** -1.5 or less. **Not kept:** anything else.
4. **Mechanism, per draw:** runner applied and submitted; solvers ending EMPTY; misplaced edits; empty patches;
   time-cap tasks; mean wall; SD of solves over draws.

**Blind guess.** Smoke pass 60%. Early check pass 45% (the E4B follows fixed commands less reliably). Promote 20%.
