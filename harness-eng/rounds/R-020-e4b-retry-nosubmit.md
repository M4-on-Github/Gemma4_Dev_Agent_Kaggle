# R-020: E4B retry on an empty attempt, with a solver that cannot submit (pre-registration)

Written 2026-11-21, before any job of this round is submitted. Counts only; no trace content. Tweak id
**T-e4b-020**. It follows from the R-018 kill (see that file's reading 2).

## Why

- Offline sizing from R-018 still applies (`tools/retry_sim.py`):
  - Ada base draws, cap 56, 3 attempts: 6.67 → 7.67 resolved per draw, 106 → 122 s per task.
  - `tools/bestof_sim.py` under the shared clock, Ada: retry-on-empty 7.67. On Turing (time ÷ 5) it is 8.20 against
    a base of 7.00.
- R-019's desk check found that a file-set selector over 3 attempts does no better than retry-on-empty, at twice
  the wall. So retry-on-empty is the E4B layout to test.
- R-018 could not test it. Any `submit_patch` sets `patch_submitted`, and the next final text from any agent ends the
  task. The solver submitted its own empty attempt, and the task ended before the root could retry.
- **The fix.** No agent submits before the last attempt.
  - The solver loses `submit_patch`, and its prompt says the caller submits.
  - The root checks the attempt with one fixed `run_command`. It counts the changed source files against
    `_swegemma_baseline`, leaving out test paths and `conftest.py`, the same paths the grader drops.
  - The root calls `solve` again while the count is 0, at most 3 `solve` calls, then calls `submit_patch`.

## Change and arms

| Arm | Tree | Root | Solver |
|---|---|---|---|
| control | `trees/e4b-r020-ctl` | R-017's root, byte for byte: one `solve`, then `submit_patch` | no `submit_patch`; 6 prompt lines reworded from "call submit_patch" to "stop" |
| retry (T-e4b-020) | `trees/e4b-r020-retry` | `solve`, the fixed count command, `solve` again while 0 (at most 3), then `submit_patch`; root gains `run_command` | the control's solver, byte for byte |

- Both arms use `max_tool_calls` 56. Everything else is R-017's tree: solver sampling, root sampling, time cap 8 min
  and turn cap 80.
- `diff -r` between the arms shows only the `agent.yaml` comment, the root's `run_command` tool and `prompts/root.md`.
  The retry is therefore the only difference. The solver change is in both arms.
- The control against R-017 and R-011 is a drift check of the solver change and the call cap, read only as a
  drift check.
- The count command was checked by hand on a synthetic git repo. Test-only changes give 0, a new source file gives 1,
  and two source files give 2.
- Validator (`--official`, `env/harness.sif`):
  - Both arms: `adk_submission.validate_directory` OK, plus the two cluster-only errors (the 18 h gate;
    compile_submission TypeError).
  - The control also shows the lint false error "root agent has no way to modify files" (H-002). It does not
    show the sub-agent `submit_patch` warning, since the solver no longer has the tool.
  - One warning in both arms: timeout_seconds below 300.

## Runs

| Arm | Cohort | Draws | Run ids |
|---|---|---|---|
| smoke, retry tree (not read for effect) | `runs/_cohorts/smoke-empty4.txt`, concurrency 2 | 1 | `S-020-e4b-retry-smoke` |
| smoke, control tree | `runs/_cohorts/smoke-te.txt`, concurrency 2 | 1 | `S-020-e4b-ctl-smoke` |
| control | `cohorts/cdev2-79.txt` | 12 | `R-020-e4b-ctl-ada-d1..d12` |
| retry | `cohorts/cdev2-79.txt` | 12 | `R-020-e4b-retry-ada-d1..d12` |

- `smoke-empty4` holds the 4 tasks, in sorted order, whose solver submitted an empty first attempt in R-018 retry
  d1. The retry branch is therefore exercised. The ids live only in gitignored `runs/_cohorts/`.
- Flags: as R-018 (Ada, `slurm/eval.sbatch`, `--concurrency 4 --py313 env/py313-scorer/bin/python3.13 --task-envs
  env/taskenvs`, time scale 1.0). Draws are interleaved (ctl d1, retry d1, ...), all `afterok` on both smokes.
  About 17 Ada GPU-h.
- Queueing follows the weekend rule. A smoke-gate fail cancels all draws. A retry-d1 kill cancels every pending or
  running draw of both arms, unread.

## Readings (written before any job runs)

1. **Smoke gates.**
   - Both smokes: every row SUCCESS, no engine error, and no task with more than 3 `solve` calls.
   - Retry smoke: root model calls at most 9 per task, and **at least 1 task retried** (`retry_counts.py`
     `retried` ≥ 1). The count is read from the root's count command.
   - Control smoke: every task ends with a root `submit_patch`. `submit_calls` must be at least the row count.

   A failed smoke is fixed once, logged here, and re-run.
2. **Draw-1 kill gates**, on retry d1 (`tools/d1_gate.py`):
   - resolved ≤ 3;
   - empty ≥ 23;
   - time caps ≥ 7;
   - `retry_miss` ≥ 3;
   - `solve_calls_gt3` ≥ 1.

   Also a kill: control d1 resolved ≤ 3 or empty ≥ 23. That would show the no-submit solver breaking. It is read
   when control d1 ends, by its own gate actor.
3. **Decision**: retry d1-d12 against control d1-d12, with `tools/paired_boot.py` (79 tasks, 90% CI, 10,000
   resamples, seed 0). The wall ratio is reported.
   - **Helps:** the CI lower bound is above 0.
   - **Kept on mechanism:** the CI lower bound is at or below 0, and all of these hold: rescued ≥ 0.5 per draw;
     the point estimate is at least +0.5; the wall ratio is at most 1.4.
   - **Dropped:** anything else.
4. **Mechanism (reported)**, per draw for both arms:
   - the `solve`-call histogram;
   - first empty / non-empty / unknown;
   - retried, rescued, over-retry;
   - empty, time caps, mean wall, root calls;
   - tasks with no root `submit_patch`.
   - Drift check: R-020 control against R-017 Turing, R-011 base and R-008 Ada.

**Blind guess (not a reading).** Passes the smoke and d1 gates: 70%. Helps: 15%. Kept on mechanism: 30%. The
no-submit solver changes the base: 35% that control resolved differs from R-008 Ada by more than 1.5 per draw.

## Queued (2026-11-21)

- Smokes: retry 60112, control 60113. Draws, all `afterok:60112:60113`, as (control, retry): d1 60114/60115,
  d2 60116/60117, d3 60118/60119, d4 60120/60121, d5 60122/60123, d6 60124/60125, d7 60126/60127, d8 60128/60129,
  d9 60130/60131, d10 60132/60133, d11 60134/60135, d12 60136/60137.
- Gate actors (`tools/gate_actor.sh`), each cancelling every other R-020 job on a kill:
  - retry smoke: `status_SUCCESS<4`, `solve_calls_gt3>=1`, `root_calls_max>9`, `retried<1`;
  - control smoke: `status_SUCCESS<2`, `solve_calls_gt3>=1`, `submit_calls<2`;
  - retry d1: the five reading-2 gates;
  - control d1: `resolved<=3`, `empty>=23`.

## Smoke gates (reading 1), 2026-11-21/22

- **Control smoke (60113): PASS.** 2 rows SUCCESS; resolved 1; empty 0; one root `submit_patch` per task;
  `solve` calls at most 1; root model calls at most 3.
- **Retry smoke (60112): FAIL** on `root_calls_max>9` (value 10). `tools/gate_actor.sh` cancelled every R-020 draw
  before any started. No draw is read.
  - 4 rows SUCCESS; resolved 0; empty 2. `retry_counts.py`: first attempt empty 2, retried 2, rescued 0,
    `retry_miss` 0, `solve` calls {0: 1, 2: 1, 3: 2}.
  - **Cause, from event order, tool names and counts only:**
    - The root used `run_command` for work other than the count command. In 1 task it never called `solve` and
      ran its own shell commands, which was the 10-call task. In 1 other task it ran 4 non-count commands
      before the count.
    - In 2 tasks the root called `solve` twice in a row without the count between them.
    - The count itself printed an integer in 3 of the 4 tasks, and the branch went the right way each time:
      0 led to another `solve`, and 1 led to `submit_patch`.
- **Fix 1 (the one fix the reading allows).** The root loses `run_command`. The count moves into a skill,
  `skills/change-count/scripts/count.py`, called with `run_skill_script`, the call shape EXP-057 showed works
  with the E4B.
  - The script uses pure file reads. It parses the git index and the baseline commit object, starts no program
    and writes nothing.
  - A tracked file counts when its content hash differs from the index blob, or when it is gone. A new file counts
    when its mtime is after the baseline commit time.
  - Test paths, dot paths, caches and compiled files are skipped, and so are intent-to-add index entries.
  - On any error it prints 1, so an unreadable state never starts another attempt.
  - Checked by hand on a synthetic repo in the harness python: no change, a touched file, test-only changes and
    junk files all print 0. One modified file plus one new file prints 2, both before and after `git add -N`.
    A further deletion prints 3. No `.git` prints 1.
  - The root now has no tool with which to work on the issue itself.
  - `prompts/root.md` step 2 now names the skill call. Steps 1, 3 and 4 are unchanged.
- The control tree is unchanged, and its smoke stands. The arms now differ in the root prompt and the root's
  `change-count` skill. The pre-registered gates and readings are unchanged.
- `tools/retry_counts.py` also reads `run_skill_script` stdout as the count.
- Validator: `validate_directory` OK. It shows the three known errors and two warnings, the new one being
  VERIFY(Q1), skill scripts rely on `run_skill_script`.
- Re-run: retry smoke `S-020b-e4b-retry-smoke` on `smoke-empty4`, then the 24 draws `afterok` on it alone.
  Gates as before. Also checked by hand: at least 1 skill count printed an integer.
- Re-queued 2026-11-22 under new run ids, so no run directory of the cancelled jobs is reused. Those directories
  hold 13 rows in all and are not read.
  - Smoke `S-020b-e4b-retry-smoke`: job 60138.
  - Draws `R-020b-e4b-{ctl,retry}-ada-dN`, all `afterok:60138`, as (control, retry): d1 60139/60140,
    d2 60141/60142, d3 60143/60144, d4 60145/60146, d5 60147/60148, d6 60149/60150, d7 60151/60152, d8 60153/60154,
    d9 60155/60156, d10 60157/60158, d11 60159/60160, d12 60161/60162.
  - Gate actors: the smoke on 60138; retry d1 on 60140; control d1 on 60139. Gates as above.
