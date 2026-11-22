# Lessons, E4B

- R-000 (2026-11-18): base resolves 4 and 7 of 56 on cdev-56. 14-18% of tasks end with an empty patch
  although `submit_patch` is called on 95%+; 17-28% of edit calls fail.
- R-001/R-002: one tree's two draws differ by up to 6 resolves (11 vs 5; 6 vs 2). Two draws of 56
  tasks cannot rank E4B trees; use three and pool the base.
- R-002: adding rules to the 3.1 kB prompt did not change edit behaviour. Next: fewer rules, not more.
- R-003/R-004: temperature 0.3, a short prompt and thoughts-out-of-history all score at the base
  (5.7, 6.0, 5.0 vs 6.0). The E4B is insensitive to prompt length and sampling at this level.
- R-001 at three draws: calls40 and sweep both 8.0 vs 6.0, exactly at the keep threshold. Treated as
  unproven until the compose run (R-006).

- 2026-11-18 R-006: sweep + calls40 composed scores 8, 4, 8 (6.7) against base 6.0. The two +2.0
  three-draw results were noise. On cdev-56 a three-draw mean must beat the base by 3 to be kept.

- 2026-11-22 R-017..R-021: the E4B's first significant gain is **retry on an empty attempt**, +1.08 solves per
  draw (CI +0.08..+2.08, 12 paired draws), at 1.23x wall. It needs three things together:
  - the solver cannot call `submit_patch`, since any submit ends the task;
  - the root has no shell, only `solve`, a pure-Python count skill and `submit_patch`, or it does the work itself;
  - the count is a number printed by `run_skill_script` (three fields, no `load_skill`).
  Prompt-level control of the root (R-018) and a file-set selector (R-019) did not get there.

- **2026-11-22 (R-022). Check every kill bar against the arm's own past draws before queueing.** A bar copied from an
  earlier round (control `empty>=23`, from R-020) sat inside the control's observed range at 8 min (10-24 per draw).
  It killed a 17 GPU-h round at draw 1 for no fault in the trees. Bars now sit outside each arm's range in the
  nearest round with the same trees.
  The same day R-023 repeated the error on a different field (`solve_calls_gt3>=1`, R-021 range 0-4), because the
  range was taken from one draw. The check is now mechanical: run `tools/d1_gate.py` with the new bars on every draw
  of the reference round, and queue only if all PASS.
