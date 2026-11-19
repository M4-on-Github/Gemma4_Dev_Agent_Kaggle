# R-008 (both models): re-baseline with each task's own test packages in the agent's sandbox

Written 2026-11-19, before any R-008 draw except the 2-task smoke `S-008-e4b-te-smoke`, which checks only
that the packages reach the agent (it is not read for resolves). This is a change of environment, not a tweak:
nothing in `trees/` changes, and no promotion rule applies. Approved by the user on 2026-11-19 ("go ahead").

## Why

- **The agent sees import errors that the real scorer would not.** Since shims were switched on
  (2026-11-18T17:10Z), 111 of 584 E4B task-draws and 7 of 216 31B task-draws hit `No module named ...` or
  `cannot import name ...` while running tests:
  - `orjson` (43 task-draws) and `flask` (21) have no stand-in;
  - `dirty_equals` names the shim lacks (`IsInt`, `IsStr`, `IsUUID`, `IsList`, `AnyThing`: about 40);
  - `inline_snapshot` and `dirty_equals` themselves (81, 66), from screen and R-006 jobs launched without
    `HENG_SHIMS=1`.
- **The harness tells the agent the opposite.** Its task text says every dependency is installed and that a
  failed import means the bug is in `/workspace`.
- **The scorer installs task deps.** The public scorer's Docker path installs each task's dependencies
  (`setup.py --fast-path`); our subprocess sandbox does not.
- **The env already exists.** `--py313 env/py313-scorer/bin/python3.13 --task-envs env/taskenvs`
  (`tools/scorer_env.py`, built in C-002/C-003) gives every sandbox venv the task's declared test deps at the
  task date. Until now it was used only for gold and empty controls.

## Change

- **Flags:** every eval job appends `--py313 env/py313-scorer/bin/python3.13 --task-envs env/taskenvs`.
  `HENG_SHIMS` is left off, since the real packages replace the stand-ins.
- **Python:** the agent's `python` and `pytest` become Python 3.13, with pytest 9.2.0. The image's 3.12
  site-packages leave the sandbox.
- **Grading:** grading uses the same venv, so it matches C-003.
- **Rebuilt env:** `requests_6592`'s env was rebuilt with `werkzeug<3` (`tools/build_task_envs.py`
  `EXTRA_REQS`) before any draw; C-004 grades its gold and empty patches.

## Runs

| Run ids | Model | Cohort | Draws |
|---|---|---|---|
| `S-008-e4b-base-te-s1..s3` | E4B, `trees/e4b-base` | `screen-e4b-20` | 3 |
| `R-008-e4b-base-te-d1..d3` | E4B | `cdev2-79` | 3 |
| `S-008-31b-base-te-s1..s2` | 31B, `trees/31b-base` | `screen-31b-20` | 2 |
| `R-008-31b-base-te-d1..d2` | 31B | `cdev2-79` | 2 |

- **E4B** runs as its own lane after the 2-task smoke passes.
- **31B** runs after the last queued R-003/R-004 job (59096).
- **Estimate:** about 2.1 GPU-h for the E4B and 5.3 GPU-h for the 31B.

## Checks and readings (written before the draws)

1. **The env reaches the agent (from the smoke and then every draw).** Missing-module errors fall to at
   most 2% of task-draws, from 19% (E4B).
   - If they don't, the env is not reaching the agent. Stop the round, find out why, and do not use these
     draws as a base.
2. **Pytest header:** the agent's pytest headers show `Python 3.13`.
3. **New bases.** If checks 1 and 2 hold, these draws become the base for every later screen and L2 run:
   - the S-008 means are the screen bases;
   - the R-008 means are the cdev2-79 bases.
   - Earlier bars (screen 3.0 / 9.0, pooled cdev2-79 7.33 E4B) are retired, and every later tweak run uses the
     same flags.
4. **Size of the environment effect (reported, not a promotion).** New base minus old base:
   - E4B: on screen-e4b-20 against 3.0 and on cdev2-79 against 7.33;
   - 31B: on screen-31b-20 against 9.0 and on cdev-56 against 22.0.
   - With 2-3 draws, a move under 3 tasks on cdev2-79 (1.5 on the screens) is read as no change.
   - A fall of 3 or more is read as a cost of Python 3.13 or the newer packages, and the 20 lowest tasks are
     checked by hand before the base is used.
5. **Later, not in this round.** The cohorts stay as they are so the comparison with the old base is paired.
   Rebuilding cohorts over the 119 C-003-gradeable tasks is a separate decision.
