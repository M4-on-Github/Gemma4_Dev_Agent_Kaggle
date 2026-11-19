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

## Log

- **2026-11-19T01:14Z, smoke `S-008-e4b-te-smoke` (job 59431, 2 tasks), passed.**
  - 0 of 2 task-draws had import errors, and the one pytest header said Python 3.13.
  - `orjson`, `flask`, `inline_snapshot` and `dirty_equals.IsInt`/`IsStr`/`IsUUID`/`IsList`/`AnyThing` import
    from `env/taskenvs/fastapi_14301` and `_14459`.
  - It is thin evidence for check 1 (one pytest call), so check 1 is read again on every draw.
  - Counter: `envcheck.py` matches `No module named` / `cannot import name` in tool output. For calibration,
    on old draws it reads 10/79 (`R-007-e4b-pagedread-d1`) and 5/20 (`S-000-e4b-base-s1`), with every pytest
    header saying 3.12.
- **2026-11-19T01:16Z, E4B launched without `HENG_SHIMS`.**
  - `S-008-e4b-base-te-s1..s3`: jobs 59432, 59434, 59436.
  - `R-008-e4b-base-te-d1..d3`: jobs 59433, 59435, 59437.
- **31B queued `afterany:59096`, concurrency 4 (same as the old base).**
  - `S-008-31b-base-te-s1, s2`: jobs 59438, 59440.
  - `R-008-31b-base-te-d1, d2`: jobs 59439, 59441.

### Check 1 failed on the first E4B draws; round stopped and restarted (2026-11-19T01:30-01:55Z)

- **Read at 01:25Z** (`envcheck.py`):
  - `S-008-e4b-base-te-s1`: 2 of 14 task-draws had import errors.
  - `-s2`: 2 of 20.
  - `R-008-e4b-base-te-d1`: 0 of 16.
  - All 4 are `No module named 'pkg_resources'`, in `rich_3006` and `rich_3105`, from the agent's
    `pytest tests/`. 4 of 50 is 8%, over the 2% line.
  - Pytest headers were all Python 3.13, so check 2 held.
- **Action, per check 1.** Cancelled jobs 59432-59437. None of their rows is used.
- **Cause.** `tests/test_syntax.py` does `import pkg_resources` in 10 rich snapshots (rich_3006, _3043, _3052,
  _3061, _3063, _3064, _3067, _3105, _3130, _3180). The scorer copy's setuptools 84.2.1 no longer has
  `pkg_resources`; the old 3.12 image's did.
- **Fix.** `tools/build_task_envs.py` `EXTRA_REQS` adds `setuptools` to those 10 envs. The date cap gives
  68.0.0, which has `pkg_resources`; it imports on 3.13.
- **Grading unchanged (C-005).** Jobs 59442/59443 ran gold 10/10 and empty 0/10 on the 10 tasks, the same as
  C-003.
- **Audit of all 129 snapshots.** Every top-level import in test files was checked against the task's env plus
  the scorer interpreter. The only unresolved names left are guarded:
  - Python 2 and Windows fallbacks in requests (`StringIO`, `BaseHTTPServer`, `winreg`, ...);
  - `orjson` in 7 fastapi tasks, behind `pytest.importorskip` / `find_spec` skips;
  - `importlib_metadata` in 3 rich tasks, behind a Python < 3.8 branch.
- **Restart (jobs 59444-59449).** The same design and readings, under new run ids:
  - `S-008-e4b-base-te2-s1..s3` and `R-008-e4b-base-te2-d1..d3`.
  - The 31B jobs 59438-59441 have not started, so they keep their ids and pick up the fixed envs (envs are
    read at run time).

## Results: E4B (2026-11-19T02:40Z)

| Run | Resolved | cdev-56 | cdevx-23 | Empty patches | Import errors (task-draws) | Pytest headers |
|---|---|---|---|---|---|---|
| S-008-e4b-base-te2-s1 (job 59444) | 4/20 | - | - | 1 | 0/20 | 3.13 x 25 |
| S-008-e4b-base-te2-s2 (59446) | 5/20 | - | - | 4 | 0/20 | 3.13 x 13 |
| S-008-e4b-base-te2-s3 (59448) | 2/20 | - | - | 3 | 0/20 | 3.13 x 27 |
| R-008-e4b-base-te2-d1 (59445) | 7/79 | 6 | 1 | 13 | 1/79 (`coverage`, called by the agent) | 3.13 x 115 |
| R-008-e4b-base-te2-d2 (59447) | 8/79 | 6 | 2 | 9 | 0/79 | 3.13 x 67 |
| R-008-e4b-base-te2-d3 (59449) | 5/79 | 5 | 0 | 10 | 0/79 | 3.13 x 74 |

- **Check 1 holds.** 1 of 357 task-draws (0.3%) had an import error, against 2% allowed. The one hit is
  `coverage`, a tool the agent called, not a test dependency.
- **Check 2 holds.** Every pytest header is Python 3.13.
- **New E4B bases (reading 3):**
  - screen-e4b-20: **3.67** (4, 5, 2);
  - cdev2-79: **6.67** (7, 8, 5), of which cdev-56 5.67 and cdevx-23 1.0.
  - The next E4B screens and L2 runs are read against these, with the same flags.
  - The L2 bar (base + 3) becomes 9.67.
- **Environment effect (reading 4).** Screen +0.67 (against 3.0), cdev2-79 -0.67 (against 7.33). Both are
  under the no-change lines (1.5 and 3).
  - Per task on cdev2-79, 7 tasks went up and 9 went down, all by a third or two thirds of a draw.
  - Removing the import errors did not change the E4B's resolve rate.
- **Harness errors.** "Agent completed execution without calling ..." came up 1, 0 and 3 times on d1-d3 and
  once on the screen. This is a harness message, not an env error.
- **Teardown flag.** Jobs 59445 and 59449 ended with the usual OUT_OF_MEMORY flag after writing all rows.

## Results: 31B (2026-11-19T05:20Z)

| Run | Resolved | cdev-56 | cdevx-23 | Empty patches (cdev-56) | Time-cap stops (cdev-56) | Import errors (task-draws) | Pytest headers |
|---|---|---|---|---|---|---|---|
| S-008-31b-base-te-s1 (job 59438) | 8/20 | - | - | - | - | 0/20 | 3.13 x 4 |
| S-008-31b-base-te-s2 (59440) | 9/20 | - | - | - | - | 1/20 | none |
| R-008-31b-base-te-d1 (59439) | 28/79 | 20 | 8 | 10 | 14 | 1/79 | none |
| R-008-31b-base-te-d2 (59441) | 27/79 | 19 | 8 | 12 | 13 | 3/79 | 3.13 x 4 |
| old base R-000-31b-base-d1, d2 | - | 22, 22 | - | 11, 12 | 13, 11 | - | 3.12 |

- **Check 1 holds, with one note.**
  - The counter reads 5 of 198 task-draws (2.5%), over the 2% line.
  - All 5 are `cannot import name` from the agent's own scratch scripts, importing names that do not exist in
    that library: `types.TypeAliasType`, `rich.highlighter.AutoHighlighter`, `fastapi.FastAPIError`,
    `starlette.datastructures.Cookies`, and `fastapi.dependencies.analyze_param`.
  - `No module named` hits: 0 of 198. The check asks whether the env reaches the agent, and it does. Same ruling
    as the E4B `coverage` hit.
- **Check 2 holds, thinly.** The 31B ran pytest with a visible header only 8 times, and all 8 say Python 3.13.
- **New 31B bases (reading 3):**
  - screen-31b-20: **8.5** (8, 9);
  - cdev2-79: **27.5** (28, 27), of which cdev-56 19.5 and cdevx-23 8.0.
  - The L2 bar (base + 3) on cdev2-79 is 30.5.
- **Environment effect (reading 4).**
  - Screen -0.5 against 9.0, cdev-56 -2.5 against 22.0. Both are under the no-change lines (1.5 and 3), so
    no hand check is triggered.
  - Per task on cdev-56: 2 up (`rich_3676` 0 -> 2, `rich_3782` 0 -> 1) and 6 down. `fastapi_15589` and
    `fastapi_9753` went 2 -> 0, and `fastapi_14419`, `fastapi_9425`, `rich_3063`, `rich_4079` dropped 1 each.
  - The two 2 -> 0 tasks were looked at even though the line was not crossed. The four new draws are one
    time-cap stop with an empty patch, and three wrong patches (an assertion failure, and a
    response-validation error in both 9753 draws). None shows an import or env error.
  - The -2.5 is the largest env shift on either model, so if the 31B's next L2 arms all land low, the 20
    lowest tasks get the hand check reading 4 describes.
- **OUT_OF_MEMORY flags (jobs 59439-59441).**
  - Each job had one cgroup OOM kill, and every job wrote all its rows.
  - The killed process is the grading run of `rich_3480` (exit -9). Its bug is an infinite loop (R-004), so a
    patch that leaves it unfixed grows memory until the 64G cgroup limit.
  - Across all 63 `rich_3480` draws in `runs/`, 41 grading runs were killed this way, and all 9 resolves
    exited 0. So -9 is how that task fails. It does not cost a resolve, and earlier "teardown" flags are the
    same event.
