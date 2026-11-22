# R-034: line-only edits on both models (pre-registration)

Written 2026-11-22, before any job of this round is submitted. Counts only; no trace content, no ids. Tweak ids
**T-e4b-034** and **T-31b-034**. Goal set by the user: raise the solve rate and the models' abilities, with small
representative sweeps before bigger runs.

## Why

- **E4B.** About 54% of `edit_file` results fail on cdev2-79 (R-033: 0.540 for the concurrent controls, 0.552 for
  R-021). R-028 classed the `Failed to replace` results against the base file:
  - 92% quote text that is mostly present, invented, or present but not contiguous;
  - 402 of 404 come after a `read_file` of the same file.

  So the E4B writes the old text from memory after reading it. Prompt rules on the anchor did not move this
  (T-e4b-003), and an edit applier in a fresh context was killed (T-e4b-016). A line-range replace needs no copy of
  the old text, so this failure class cannot happen.
- **31B.** About half of its `edit_file` calls lose their arguments: 128.8 per draw against 122.0 `ok` (R-028). Each
  loss is a resend, so it costs wall, about 7 calls in an affected task, and the 31B's limit is the 8-minute cap.
  - In the six base draws the time cap ends 23.8 task-draws per draw: 14.0 with a patch and 9.8 empty.
  - The empty ones are solved in 14.9% of the other draws of the same task.
- **What is new against R-026.** R-026 offered the same `line-edit` skill as an optional prompt bullet. It was called
  in 0 of 32 E4B tasks and 0 of 24 31B tasks. Here `edit_file` is taken out of the tool list, so the skill becomes the
  edit tool. `write_file` and `run_command` stay, and their use is measured.

## Arms

| ID | Arm | Tree | Change against the parent |
|---|---|---|---|
| T-e4b-034 | e4b-lineonly | `trees/e4b-lineonly` | parent `trees/e4b-r020-retry` (the shipping E4B layout). The solver loses `edit_file` and gains `skills/line-edit`. The prompt's edit bullet ("Prefer `edit_file` ...") is replaced by four lines on `show.py` and `replace.py`, and section 4's repair names `replace.py`. |
| T-31b-034 | 31b-lineonly | `trees/31b-lineonly` | parent `trees/31b-base` (the shipping 31B agent). The same three changes on the single agent. |

- `skills/line-edit` is `skills_lib/line-edit`, unchanged from R-026:
  - `show.py` prints numbered lines, at most 120;
  - `replace.py` replaces an inclusive line range, keeps the line ending, refuses test files and paths outside the
    repository, and prints `ERROR ...` without writing on a bad request.
- The new prompt lines contain no braces and none of the lint words. `diff -r` against each parent shows only the
  changes listed above and the `agent.yaml` header comment.
- **Validator (`--official`).**
  - e4b-lineonly: 3 errors and 4 warnings. These are the parent's 3 errors and 2 warnings, plus the Q1 note on
    `show.py` and `replace.py`.
  - 31b-lineonly: 2 errors and 3 warnings. These are the parent's 2 and 1, plus the same two notes.
  - `run_skill_script` already runs in the shipping E4B layout (change-count).

## Runs

| Stage | Run | Tree | Cohort | Draws | Dependency |
|---|---|---|---|---|---|
| smoke (not read for effect) | `S-034-e4b-lineonly-smoke`, `S-034-31b-lineonly-smoke` | each arm tree | `runs/_cohorts/smoke-te.txt`, concurrency 2 | 1 each | none |
| E4B arm | `R-034-e4b-lineonly-ada-d1..d4` | `trees/e4b-lineonly` | `runs/_cohorts/sw-e4b-32.txt` | 4 | `afterok` its smoke |
| E4B concurrent control | `R-034-e4b-ctl-ada-d1..d4` | `trees/e4b-r020-retry` | `sw-e4b-32` | 4 | none |
| 31B arm | `R-034-31b-lineonly-ada-d1..d4` | `trees/31b-lineonly` | `runs/_cohorts/sw-31b-24.txt` | 4 | `afterok` its smoke |
| 31B concurrent control | `R-034-31b-ctl-ada-d1..d4` | `trees/31b-base` | `sw-31b-24` | 4 | none |

- Flags as R-026: `sbatch --parsable -J heng_<e4b|31b> slurm/eval.sbatch <run> <tree> <cohort> --concurrency 4
  --py313 env/py313-scorer/bin/python3.13 --task-envs env/taskenvs`, 1 Ada GPU, 4 CPUs, 64G. Smokes use
  `--concurrency 2`.
- Arm and control draws are submitted interleaved, so they share the queue period (the R-033 lesson). 18 jobs, about
  2 × 0.2 + 8 × 0.4 + 8 × 0.85 ≈ 10.4 Ada GPU-h.

## Readings (written before any job runs)

1. **Smoke gate, per arm.** A kill cancels that arm's draws, unread. A failed smoke is fixed once, the fix is logged
   here, and the smoke is re-run.
   - Gate fields: `status_SUCCESS<2`; E4B also `solve_calls_gt3>=1 root_calls_max>9` (R-026's).
   - Read by hand, also a kill: a `replace.py` or `show.py` result `ERROR replace failed` / `ERROR show failed` (the
     script raised). An `ERROR` on a bad request is the script working.
   - Skill use is not gated at the smoke.
2. **Draw-1 kill gates, per arm and per control.** `tools/gate_actor.sh` cancels that arm's d2-d4 on a kill.
   - E4B (32 rows): `resolved<=2 empty>=9 timecap>=6 mean_wall>250 retry_miss>=4 solve_calls_gt3>=3 callcap>=14`.
     Checked with `tools/d1_gate.py` on the 4 same-tree draws on `sw-e4b-32` (R-026 ctl d1-d2, R-032 ctl d1-d2):
     4 of 4 PASS.
   - 31B (24 rows): `resolved<=7 empty>=13 timecap>=11 mean_wall>440 callcap>=11`. Checked on R-026 31B ctl d1-d4:
     4 of 4 PASS.
   - Arms only: also `lever_skill_tasks<=0`. An arm whose skill nobody calls is not tested.
   - 31B control d1: the 31B bars. A kill there cancels every 31B job of the round, because the environment drifted.
   - E4B control d1: the E4B bars, reported only.
3. **Promotion, per arm, after all its draws.** Uses `tools/paired_boot.py`. The statistic is solves per draw on the
   cohort, with a 90% CI over tasks. The wall ratio is the arm's mean task wall over the concurrent controls' mean.
   - **E4B: promote** if all three hold:
     - against the 4 concurrent controls, the point estimate is at least +1.0;
     - against the 12 R-021 retry draws restricted to `sw-e4b-32` (7.0 per draw), the point estimate is at least
       +1.0;
     - the wall ratio is at most 1.25.
   - **31B: promote** if, against the 4 concurrent controls, the point estimate is at least +1.5 and the wall ratio
     is at most 1.05 (R-026's 31B bars).
   - **Drop** anything else, and any arm stopped by a gate.
   - Reported: the 31B arm against the 8 pooled controls (R-026 ctl and these); each control against its older
     comparator (drift).
4. **Mechanism (reported, not gates).** Per arm, against its controls:
   - edit attempts per draw and their failure share:
     - controls: `tools/edit_status_counts.py`, `edit_file` ok against failed;
     - arms: `replace.py` results starting `OK` against `ERROR`;
   - `write_file` calls to an existing source file, and `run_command` edits are not counted;
   - empty final patches, time caps, calls per task, mean task wall;
   - 31B: results holding only `error` (argument loss), `edit_file` in the controls against `run_skill_script` in
     the arm;
   - E4B: `tools/retry_counts.py` (first-attempt empty, retried, rescued).
5. **What promotion buys.**
   - A promoted E4B arm runs 12 draws on `cohorts/cdev2-79.txt` with 12 concurrent controls, under R-033's decision
     rule.
   - A promoted 31B arm runs 6 draws on cdev2-79 with 6 concurrent controls.
   - Each is its own pre-registered round.

## What each outcome means

- **E4B helps:** the edit, not the search, was the limit (R-028), and copying old text was the part of the edit that
  failed.
- **E4B mechanism works, no solves:** edits land, but their content is wrong. The limit then sits in deciding the
  change. Edit-tool levers on the E4B are closed.
- **31B helps or stays at par with a lower wall:** argument loss was specific to `edit_file`'s schema. At par with
  lower wall is not a promotion here, but it is reported. It would free 31B time for a later lever.
- **31B arg loss moves to `run_skill_script`:** the loss is a generation slip on long string arguments, as EXP-025
  said. The 31B edit-tool line is closed.

**Blind guess (not a reading).**

| Arm | Smoke and d1 pass | Promoted |
|---|---|---|
| E4B | 65% | 15% |
| 31B | 70% | 10% |

E4B replace failure share below 0.25: 60%.

## Queued (2026-11-22)

- Smokes: e4b 60798, 31b 60799.
- E4B arm d1-d4: 60800, 60804, 60808, 60812 (`afterok:60798`). E4B ctl d1-d4: 60801, 60805, 60809, 60813.
- 31B arm d1-d4: 60802, 60806, 60810, 60814 (`afterok:60799`). 31B ctl d1-d4: 60803, 60807, 60811, 60815.
- Gate actors (readings 1 and 2, bars as written):
  - 60798, which cancels the E4B arm;
  - 60799, which cancels the 31B arm;
  - 60800, which cancels E4B arm d2-d4;
  - 60802, which cancels 31B arm d2-d4;
  - 60803 (31B ctl d1), which cancels every other 31B job.
- E4B ctl d1 (60801) is read by hand with the E4B bars, reported only. The hand-read smoke check (script raised) is
  done when the smokes end.

## Smoke gates (reading 1), 2026-11-22: both PASS

- **E4B, 60798:** COMPLETED in 12 min 11 s.
  - Gate fields: 2 rows SUCCESS; `solve_calls_gt3` 0; root calls at most 4.
  - Solver skill calls, 13 in total:
    - 7 returned ok: `replace.py` printed `OK` 5 times, and `show.py` ran.
    - 6 got a harness error code, so the script never ran: 5 `SKILL_NOT_FOUND` (a wrong `skill_name`) and 1
      `INVALID_ARGUMENTS`.
  - `replace failed` (the script raised): 0.
- **31B, 60799:** COMPLETED in 11 min 51 s.
  - 2 rows SUCCESS.
  - `replace.py` printed `OK` 6 times and `ERROR` 0 times. 0 harness errors, 0 argument loss, 0 `show.py` calls,
    0 `write_file` calls.
- **Hand check (script raised): 0 in both.** Smoke use is not read for effect.
- **Reported, not a gate:** the E4B sometimes puts something other than `line-edit` in `skill_name`. This is a
  mechanism count under reading 4.
- **Tool change, made before any draw was read.** `tools/lineedit_counts.py` now counts results with a harness
  `error_code` as `skill_harness_error`, not as `replace_error`. A `replace_error` is now only an `ERROR` line printed
  by the script.

## Deviation (2026-11-22, recorded before any draw is read)

- **Out-of-memory after all rows were written.** Slurm ended three jobs as OUT_OF_MEMORY:
  - 60800 (E4B arm d1): 32 of 32 rows SUCCESS, 32 unique tasks;
  - 60803 (31B ctl d1): 24 of 24 rows SUCCESS;
  - 60815 (31B ctl d4): 24 of 24 rows SUCCESS.

  They are kept under R-021's rule, as R-033 did.
- **60804 (E4B arm d2)** also ended out of memory. Like 60808 and 60812, it is a draw the d1 gate meant to cancel. It
  is not read.
