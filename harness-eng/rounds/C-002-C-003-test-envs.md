# C-002 / C-003: test environments for grading (2026-11-18)

Question: which test environment makes the most tasks gradeable here, and how close is it to the public scorer?
A task is gradeable when the reference patch resolves and the empty patch does not. All 129 tasks, concurrency 6,
CPU jobs 59103-59106. Grading code is swegemma's; only the Python and packages the tests import change.

| Run pair | Test env | Gold resolves | Empty resolves | Gradeable |
|---|---|---|---|---|
| C-001 (earlier) | vLLM image Python 3.12 + its packages + two shims | 106/129 | 5/129 | 101 |
| C-002 | copy of the public scorer: Python 3.13, Dockerfile.public pip set, newest-version wheel overlay (`env/py313-scorer`) | 55/129 | 1/129 | 54 |
| C-003 | C-002 plus each task's own declared test deps at the task's date, ahead of site-packages (`env/taskenvs/<id>`, `tools/build_task_envs.py`) | 121/129 | 2/129 | 119 |

Run with: `sbatch --export=ALL,HENG_EVAL_ARGS="--py313 env/py313-scorer/bin/python3.13 --task-envs env/taskenvs" slurm/control.sbatch <run> gold|empty cohorts/all-129.txt 6`.

## Readings

- C-003 vs C-001: 19 tasks gained (all 11 requests tasks that failed before, httpx_3672, rich_3064/3130/3296/3469,
  fastapi_14371/14962/14964), 1 lost (rich_3472). Use the C-003 set (119) as the gradeable set from now on.
- C-002 (the scorer copy without task deps) loses 54 of the old 101, mostly fastapi: the newest starlette and
  pygments in the wheel overlay break older snapshots (`Router.__init__() got an unexpected keyword argument
  'on_startup'`). If the real scorer installs the wheels the way our copy does, those tasks cannot resolve for
  anyone there; that is an inference from the harness code, not a measured scorer fact.
- C-003 is not scorer-faithful: it adds packages and older versions the public scorer does not ship. Results under
  it say whether the agent's patch is right, not whether the public scorer would accept it.
- Builder: 129/129 task envs built (sources: poetry 48, requirements-tests.txt 43, uv.lock 24,
  requirements-dev.txt 13, requirements.txt 1). 14 compiled packages had no cp313 wheel at the task date and were
  taken newest (cffi 5 tasks, greenlet 5, rpds-py 4). pytest, pluggy, iniconfig, py and the project itself are
  stripped from each env so the scorer's pytest runs the workspace code.

## Still failing gold under C-003 (8)

| Task | First failing line | Likely cause |
|---|---|---|
| requests_6592 | `ImportError: cannot import name 'parse_authorization_header' from 'werkzeug.http'` | werkzeug at the task date is 3.x; the httpbin pin needs werkzeug < 3. Fixable with a pin |
| requests_6757 | `test_different_connection_pool_for_mtls_settings` fails | not checked |
| fastapi_15745, 15763, 15785 | the same two `test_router_include_context.py` tests fail | not checked; same tests in three tasks suggests one env cause |
| fastapi_14186 | required node `test_model_description_escaped_with_formfeed` did not pass | not checked |
| rich_3472 | pretty-repr assertion differs | passed under Python 3.12; likely a 3.13 behaviour change, so it would fail in the scorer too |
| rich_3486 | required node `test_traceback_finely_grained_missing` did not pass | traceback layout; likely Python-version dependent |

## C-004 (2026-11-19): the eight gold failures checked

| Task | Cause found | Fixable here? |
|---|---|---|
| requests_6592 | httpbin 0.10.0 needs werkzeug < 3; the date cap picked 3.0.1 | **Fixed.** `EXTRA_REQS` in `tools/build_task_envs.py` adds `werkzeug<3` (built 2.3.8, flask 2.3.3). C-004 gold 1/1, empty 0/1 (jobs 59429, 59430). |
| fastapi_15745, 15763, 15785 | the failing tests are `@pytest.mark.anyio` async tests; swegemma's own verification runs pytest with `-p no:anyio` (`harness/verification.py:631`, `container_setup.py:892`) | No. They pass when run by hand without that flag (34 passed under pytest 9.2.0 and 9.1.1), so this is the harness's own rule and the public scorer fails them too. |
| requests_6757 | `SSLV3_ALERT_CERTIFICATE_EXPIRED`: the repo's bundled test certificates have expired | No; it depends on the date, not on packages. It fails on the scorer too unless the scorer fakes the clock. |
| fastapi_14186 | the required test `test_model_description_escaped_with_formfeed` is skipped (it needs pydantic v1; the env has 2.12.3) and a skipped test counts as not passed | Not without a pydantic-v1 env, which would break the task's other tests. |
| rich_3472, rich_3486 | Python 3.13 output differences (see above) | No; the scorer runs 3.13 too. |

Gradeable under C-003 + C-004: **120/129**. The remaining 8 are ungradeable by the scorer's own rules or
Python version, as far as can be told from the harness code; that last point is an inference.
