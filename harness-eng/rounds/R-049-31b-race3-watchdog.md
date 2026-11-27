# R-049: 31B race of three with a background timer that hands in a copy before the time cap (pre-registration)

Written 2026-11-27, before any job of this round is submitted. Counts only; no trace content, no ids.

## Why

In R-043 the race is 2.34 solves per draw ahead of kfctl where a runner applies a patch and loses 2.59 on the 11.1
tasks per draw where none does; 81% of those end at the time cap with the emptied tree graded, and in about half of
them a solver had a landed edit in its copy. R-048 (restart and late hand-in by a runner) did not shrink that group:
a runner can only act when its solver returns. The harness runs tool calls one at a time behind a lock, so a runner
cannot wait and poll either. A process left running in the sandbox can.

## Arm

`trees/31b-kf-race3w` = `trees/31b-kf-race3d` with two changes:
1. **Timer.** Each runner's first call starts, once per task, a background shell that sleeps 540 s (cluster cap
   594 s). If the race lock is still free it takes it, restores the root's files and applies the first copy (a, b, c)
   that has a change; with no changed copy it only restores the files. The time-cap fallback then grades that tree.
2. **Solver first command** no longer deletes the root's files once the lock exists.

Scratch-repository test with a 3 s sleep: started once on two calls, applied the changed copy, lock taken.
Validator: the two known errors only. Flags as R-043 (`--concurrency 1`, `cohorts/cdev2-79.txt`). 4 draws, about
30 GPU-h; 4 more by the extension rule.

## Readings (written before any job runs)

0. **Smoke** (`runs/_cohorts/smoke-te.txt`): both tasks served, no crash, a runner applies and submits in at least
   one. One fix and re-smoke allowed, logged first.
1. **Early mechanism check on d1 at 20 rows** (no resolved count looked at). Cancel all draws unread and drop the
   round if any holds: a runner applies in fewer than 14 of 20; mean task wall above 443 s; any time-capped task among
   the 20 is graded on a deleted-tree patch (the timer did not run or did not survive). If none of the 20 is
   time-capped, the check is repeated at 40 rows.
2. **Served check** per draw: 79 rows, all served; one re-run with an `r` suffix.
3. **Mechanism bar (d1-d4):** deleted-tree patches per draw 3.0 or fewer (R-043 10.4).
4. **Decision** (`tools/paired_boot.py`, arm against kfctl x8; also reported against R-043 x8):
   - **Extension:** d5-d8 only if d1-d4 read +1.0 or more against kfctl and the mechanism bar is met; otherwise the
     round ends as not kept.
   - **Promote (8 draws):** +1.5 or more, CI lower bound above -0.5. A promote means "worth a Kaggle notebook timing
     run", not "ship".
   - **Harm:** -1.5 or less. **Not kept:** anything else.
5. **Reported:** time-cap tasks; tasks graded on a timer-applied patch and how many resolve; empty patches; mean wall.

**Blind guess.** Timer survives in the sandbox 65%. Mechanism bar met 55%. Extension 20%. Promote 10%.

## Smoke (job 68271, 2026-11-27): PASS

Both tasks served, no crash, a runner applied and submitted in both; the timer command was called by the runners in
both tasks; mean task wall 191.9 s. Neither task reached the time cap, so the timer's effect is not seen yet. Draws
d1-d4 submitted: 68272 68273 68274 68275. Early check at 20 rows of d1 as written.
