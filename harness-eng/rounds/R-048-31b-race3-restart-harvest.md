# R-048: 31B race of three, idle runner restarts its solver and hands in another copy late (pre-registration)

Written 2026-11-27, before any job of this round is submitted. Counts only; no trace content, no ids.

## Why

R-043 (race of three, emptied root) read not kept: 30.12 against kfctl 30.38. Its breakdown:
- on the 67.9 tasks per draw where a runner applied a patch the race solves 30.12 and kfctl expects 27.78 (+2.34);
- on the 11.1 tasks per draw where no runner applied, the race solves 0 and kfctl expects 2.59. 81% of them end at the
  time cap. In about three quarters of them one runner's solver came back with no edit and the runner stayed idle; in
  about half, another solver had a landed edit in its copy when the task ended.

This round changes only what a runner does when its solver comes back empty.

## Arm

`trees/31b-kf-race3h` = `trees/31b-kf-race3d` with two changes:
1. **Runner.** One finish command, run after each solver call. It hands in the runner's own copy if that has a
   change. If it has none and 400 s or more have passed since the copy was made (cluster cap 594 s), it hands in the
   first other copy that has a change. If the command prints EMPTY, the runner calls its solver one more time and
   runs the command again. Submit only on APPLIED, as before.
2. **Solver first command.** It no longer deletes the root's files once the race lock exists (the R-045 fix), so a
   restarted solver cannot empty an applied patch.

The command was tested in a scratch repository (own change; no change and young; another copy's change and old; lock
held): APPLIED, EMPTY, APPLIED, TAKEN as intended. Validator: the two known errors only.

Flags as R-043: `--concurrency 1`, cohort `cohorts/cdev2-79.txt`, 1 GPU and 4 CPUs per draw. Cost: about 7.5 GPU-h
per draw; 4 draws first (30 GPU-h), 4 more by the extension rule.

## Readings (written before any job runs)

0. **Smoke** (`runs/_cohorts/smoke-te.txt`): both tasks served, no crash, a runner applies and submits in at least
   one. One fix and re-smoke allowed, logged first.
1. **Early mechanism check on d1 at 20 rows** (no resolved count looked at). Cancel all draws unread and drop the
   round if any holds: a runner applies in fewer than 14 of 20 tasks; a failed apply in 3 or more; a solver edit
   landed outside its copy in more than 0.15 of solvers; mean task wall above 443 s.
2. **Served check** per draw: 79 rows, all served; one re-run with an `r` suffix.
3. **Mechanism bar (d1-d4):** tasks per draw where no runner applied (empty or deleted-tree patch). R-043 has 11.1.
   The change works as a mechanism at 7.5 or fewer.
4. **Decision** (`tools/paired_boot.py`, arm against kfctl x8; also reported against R-043 x8):
   - **Extension:** d5-d8 are submitted only if d1-d4 read +1.0 or more against kfctl and the mechanism bar is met.
     Otherwise the round ends at 4 draws as not kept.
   - **Promote (8 draws):** +1.5 or more, CI lower bound above -0.5. A promote means "worth a Kaggle notebook timing
     run", not "ship": three streams on Kaggle's hardware are unmeasured.
   - **Harm:** -1.5 or less. **Not kept:** anything else.
5. **Reported:** restarts per draw and how many end with a change; late hand-ins of another copy per draw and how
   many resolve; time-cap tasks; mean wall; submits without APPLIED.

**Blind guess.** Smoke pass 80%. Early check pass 75%. Mechanism bar met 55%. Promote 20%, not kept 65%, harm 15%.
