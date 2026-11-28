# R-057 (E4B): stand-ins for two missing test-helper modules, added by a `prepare` step

Date: 2026-11-28. Pre-registration, written before any GPU run of this tree. Companion of R-056 (31B).

## Why

R-056's desk checks (D-011, D-012) showed that in a test environment without `inline_snapshot` and `dirty_equals`
the 31B control loses about 8 of 79 solves per draw, and that adding stand-ins for the two modules to the patch
returns all of them. An outside review of our failure report (pasted by the user on 2026-11-28) names the same
gap for E4B: its own test runs fail on the missing modules. The E4B has never been run with the stand-ins.

## Change

`trees/e4b-r057-vend` = `trees/e4b-r041-retry-check` plus:

- `sub_agents/prepare.yaml` and `prompts/prepare.md`: a shell-only agent_tool that runs the R-056 command once
  (the same 1,194 characters as `trees/31b-kf-vend`).
- `prompts/root.md`: step 0, call `prepare` once before the first `solve`.
- `prompts/solver.md`: one sentence, leave a new `inline_snapshot/` or `dirty_equals/` folder as it is.

The change count of `count_changes` is unaffected by design: git lists a new folder as one line ending in `/`,
which the count's file-extension filter does not match. The smoke run checks this.

The step sits in its own agent so that a miscopied command costs one call and nothing else. The E4B copies a
250-character command reliably in `count_changes`; 1,194 characters is untested, hence reading 1.

## Desk check D-013 (CPU only, before the GPU run)

Control draws `R-041-e4b-rcheck-d1..d4` regraded in the environment without the two modules
(`--task-envs env/taskenvs-nosnap`), as they are (v0) and with the stand-ins appended to the patch (v1). Results
are appended below when the eight jobs finish. They size the grading effect only; the GPU run adds any effect of
the solver's own test runs working.

## Runs

- Smoke: `R-057-e4b-vend-smoke`, cohort `runs/_cohorts/smoke-vend.txt` (2 tasks whose tests import the modules).
- Draws: `R-057-e4b-vend-d1..d4`, `cohorts/cdev2-79.txt`, `--concurrency 4`, `--task-envs env/taskenvs-nosnap`.
- Comparator: the regraded control draws of D-013 (v0), extended to all eight control draws for the decision.

## Readings, fixed now

1. Smoke. Pass when in both tasks the first tool call of the run is `prepare`, its `run_command` carries the
   exact command, the graded patch holds both stand-in folders where the task's tests import them, and no
   `count_changes` answer counts a stand-in folder. A fail stops the round; the draws are cancelled unread.
2. Draw 1 kill gate (may be read alone). Kill when d1 solves fewer than the regraded control mean minus 3, or
   its mean task wall is above 1.15 times the control's mean task wall.
3. Mechanism bars over d1..d4: exact command in at least 90% of tasks; at least 85% of the tasks whose tests
   import a module carry its stand-in in the graded patch.
4. Decision over d1..d4, paired by task against the regraded control (`tools/paired_boot.py`, 90% interval):
   kept as the E4B upload candidate at +2.0 or more with the interval's low end above 0. Between +1.0 and +2.0
   four more draws are run and the same bar is applied to eight.
5. Harm flag: against the cluster-standard control (8.12 of 79, both modules installed) a difference below −1.5.

## Limits known in advance

- Which environment the official scorer resembles is not known. The stand-ins help only where the modules are
  absent at grading; where they are present the command adds nothing and the arm should equal the control.
- Hidden repositories may miss other packages; the command covers these two only.

## Desk check D-013: result (2026-11-28, CPU jobs 68726-68733)

Solves of 79, control draws `R-041-e4b-rcheck-d1..d4`.

| Draw | Cluster standard (both modules installed) | Without the modules, patch as is | Without the modules, stand-ins appended |
|---|---|---|---|
| d1 | 9 | 6 | 9 |
| d2 | 9 | 8 | 9 |
| d3 | 10 | 8 | 10 |
| d4 | 7 | 6 | 7 |
| mean | 8.75 | 7.00 | 8.75 |

- The stand-ins gain 3, 1, 2, 1 solves and lose none: +1.75 per draw, the whole loss from the missing modules.
- This is the grading effect alone. It is below the +2.0 bar of reading 4, which was fixed before this result and
  stays as written; the arm reaches it only if the solver's own working test runs add solves.
- Regraded control mean for reading 2 on these four draws: 7.00.

## Deviation logged before any result: smoke job 68734 did not start the model server (2026-11-28)

Job 68734 ended after 70 s with no task run: 22 GiB of the assigned card were held by another process (25.3 of
47.4 GiB free against the 42.7 GiB the server reserves). The 31B smoke job 68699 failed the same way one minute
earlier on the same node. No result file was written. Resubmitted unchanged as job 68744; readings as written.

## Deviation logged before any result: smoke run on a shared card at a lower memory share (2026-11-28)

The resubmitted smoke job 68744 failed like 68734 (25.3 of 47.4 GiB free), as did the 31B smoke jobs 68699 and
68743: one card of pleiades-0-17 is persistently part-held by a process outside the scheduler. `tools/cluster_eval.py`
and `slurm/eval.sbatch` now read an optional `HENG_GPU_MEM` (default 0.90, unchanged for every other run). The
smoke run is resubmitted as job 68746 with `HENG_GPU_MEM=0.45` on that card. Reading 1 has no time component, so
a slower shared card does not affect it. The four draws are pinned to pleiades-0-23 and run at the default 0.90.

## Reading 1 (smoke, job 68746): pass

| Check | Task 1 | Task 2 |
|---|---|---|
| First tool call of the run is `prepare` | yes | yes |
| `prepare` ran the exact command | yes | yes |
| Both stand-in folders in the graded patch | yes | yes |
| `count_changes` answer with the stand-ins present | 1 (one source file changed) | 0, then 1 after a second solve |

- The 0 in task 2 shows the count ignores the stand-in folders and the retry still fires.
- In task 2 the root made one call to a tool it does not hold, between `prepare` and `solve`; it had no effect.
- Neither task was solved; the smoke reading does not use that.
- The four draws are released.

## Deviation logged before any draw result: draws on shared cards at memory share 0.70 (2026-11-28)

- Draw jobs 68735 (d1) and 68736 (d2) failed at model start on pleiades-0-23 like the smoke jobs, with no task
  run and no trace written. Jobs 68737 and 68738 were cancelled before starting.
- A guard added to `slurm/eval.sbatch` logs the holder: the cards the scheduler has free are the ones on which
  another user's processes run outside the scheduler (about 11 GiB each, one card per node seen so far). These
  processes are not ours to stop.
- The four draws are resubmitted under the same run ids with `HENG_GPU_MEM=0.70`. The E4B server needs far less
  than that, so only the shared compute can differ from the control's conditions.
- Added check, fixed now: seconds per solver call in each draw against the control's (`pace.py`). A draw more
  than 15% slower is marked slowed; the decision is then read both with and without slowed draws, and reading 2's
  wall clause is not applied to a slowed draw 1.
