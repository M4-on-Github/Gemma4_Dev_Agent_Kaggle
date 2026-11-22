# R-026: small sweep of model-ability levers on both models (pre-registration)

Written 2026-11-22, before any job of this round is submitted. Counts only; no trace content, no task ids. Part of
the goal the user set on 2026-11-22: a robust system for any project of the competition, raising the solve rate
and the model's ability through prompt, context, skills, orchestration or LoRA, starting with small representative
sweeps before larger tests. This round is the small sweep. Its winners go to full paired rounds.

## Why these levers

- **E4B** (layout fixed as the R-021 retry tree, `trees/e4b-r020-retry`, at 8 min; every arm changes one lever inside
  it):
  - LoRA a1 and a2 were killed in the single-agent layout (L-003, L-007). The a2 failure was a submit loop: the call
    cap was hit in 38 of 40 tasks. In the retry layout the solver has no `submit_patch`, so that loop cannot happen.
    This is the first test of either adapter where the layout removes their known failure.
  - Skill: a file outline (`skills_lib/outline`), so the solver reads only the region it needs.
  - Context: the retry request says what went wrong ("changed no source file").
  - Budget: up to 5 attempts, calls 56 → 80, time 8 → 10 min. The E4B has Kaggle time to spend (6.66 h projected
    at Ada speed for the retry layout).
- **31B** (single agent, `trees/31b-base`; no arm may add wall, `framework.md`):
  - Skill: the same outline script.
  - Skill: line-range editing (`skills_lib/line-edit`), aimed at the failed edits. In the base draws, 516 of 1,065
    malformed edits had no `old_string`.
- An earlier sizing (`rounds/skill-script-sizing.md`) argued against a 31B locate script and an E4B fuzzy edit applier. The
  outline and line-edit scripts are different tools, but that argument (time goes to deciding, not finding) is why
  the guess below is low.

## Arms

| Arm | Tree | Built from | Change |
|---|---|---|---|
| e4b-a1 | `trees/e4b-sw-a1` | `e4b-r020-retry` | `sub_agents/solver.yaml` adds `adapter: a1` (L-003 a1, epoch 1) |
| e4b-a2 | `trees/e4b-sw-a2` | `e4b-r020-retry` | the same with `adapter: a2` (L-007 a2) |
| e4b-outline | `trees/e4b-sw-outline` | `e4b-r020-retry` | solver gets `skills: [skills/outline]` and one section-2 bullet in `prompts/solver.md` |
| e4b-hint | `trees/e4b-sw-hint` | `e4b-r020-retry` | root step 3: on 0, the next `solve` request says the last attempt changed no source file and asks for an edit of the file the issue is about |
| e4b-budget | `trees/e4b-sw-budget` | `e4b-r020-retry` | root: fewer than five `solve` calls (was 3); `max_tool_calls` 56 → 80; `max_time_minutes` 8 → 10 |
| 31b-outline | `trees/31b-sw-outline` | `31b-base` | `skills: [skills/outline]` and the same bullet in `prompts/system.md` section 2 |
| 31b-lineedit | `trees/31b-sw-lineedit` | `31b-base` | `skills: [skills/line-edit]` and one section-3 bullet: use it if an `edit_file` fails or the change spans more than a few lines |

- `diff -r` against the parent shows only the listed files plus the `agent.yaml` comment.
- The adapter dirs (`adapters/a1`, `adapters/a2`, 67M each) are copied from the L-003 and L-007 outputs and are
  gitignored. Every other file is committed with this round.
- The two skills are pure Python, run in-process by `run_skill_script`, and run no program. `outline.py` prints
  `L<start>-<end> class|def name(args)` from `ast` (a regex fallback for other files, at most 150 entries).
  `line-edit` has `show.py` (numbered lines, at most 120) and `replace.py` (replaces a line range, keeps CRLF and the
  final newline, refuses test files and paths outside the repo, prints the new region). Both were checked by hand on
  synthetic files.
- Validator (`--official`, `env/harness.sif`): every tree shows its parent's known profile
  (`adk_submission.validate_directory` OK; the cluster-only gate and compile errors; the H-002 false error on the
  retry trees; the VERIFY warnings).

## Cohorts (ids only in gitignored `runs/_cohorts/`)

- **`sw-e4b-32`** (32 tasks, 2 repos). Selected on draws that are **not** the comparator: R-021 control d1-d13,
  R-011-e4b-base-tu5 d1-d8, R-008-e4b-base-te2 d1-d3. 22 tasks solved at least once there, plus 10 never solved,
  filled by repo with seed 0.
  - Comparator: R-021-e4b-retry-ada d1-d12 restricted to the cohort (not used in selection). Per draw 7, 11, 6, 8,
    8, 7, 8, 5, 7, 5, 6, 6 (mean 7.0); mean task wall 109-170 s.
  - `sw-e4b-32-foldb` (17 tasks): the cohort's tasks in `lfold-b`. **Both adapters were trained on fold-A tasks** (D2
    is 31B trajectories on the 39 `lfold-a` tasks), and 15 of the 32 tasks are fold A. The adapter arms are read on
    the 17 fold-B tasks only. Their fold-A counts are reported and not read.
- **`sw-31b-24`** (24 tasks). 21 tasks resolved in some but not all of the six base cdev2-79 draws (R-008 d1-d2,
  R-011 d3-d4, R-014 d5, R-015 d6), plus 3 always resolved. Base on the cohort: 12, 11, 14, 12, 16, 11 (mean 12.67).
  Those draws chose the cohort, so the 31B comparator is **4 fresh control draws** of `trees/31b-base`. The six old
  draws are reported as a drift check only.
- The cohorts favour tasks the model sometimes solves. An effect measured here is larger than on cdev2-79, which is
  why winners are re-measured there.

## Noise, measured before this file was written

- Same arm against itself (R-021 retry restricted to `sw-e4b-32`, all 495 splits of 4 draws against the other 8):
  the difference in solves per draw has quantiles 50% 0, 75% +0.75, 80% +1.12, 90% +1.5, 95% +1.88. Per-draw sd 1.65.
- 31B (the six old draws, all 20 splits of 3 against 3): 50% 0, 75% +0.67, 80% +1.33, 90% +2.0. Per-draw sd 1.97.
- So 4 draws per arm can screen only for large effects. The promotion bars below sit near the 90th percentile of
  those null splits.

## Runs

| Job | Tree | Cohort | Draws |
|---|---|---|---|
| smoke, one per new tree (not read for effect) | each of the 7 arm trees | `runs/_cohorts/smoke-te.txt` (2 tasks), concurrency 2 | 1 each, `S-026-<arm>-smoke` |
| E4B arms | 5 E4B trees | `runs/_cohorts/sw-e4b-32.txt` | 4 each, `R-026-<arm>-ada-d1..d4`, `afterok` on that arm's smoke |
| E4B fresh control | `trees/e4b-r020-retry` | `sw-e4b-32` | 2, `R-026-e4b-ctl-ada-d1..d2` |
| 31B arms | 2 31B trees | `runs/_cohorts/sw-31b-24.txt` | 4 each, `R-026-<arm>-ada-d1..d4`, `afterok` on that arm's smoke |
| 31B control | `trees/31b-base` | `sw-31b-24` | 4, `R-026-31b-ctl-ada-d1..d4` |

- Flags, every job: `sbatch --parsable -J heng_<e4b|31b> slurm/eval.sbatch <run> <tree> <cohort> --concurrency 4
  --py313 env/py313-scorer/bin/python3.13 --task-envs env/taskenvs` (time scale 1.0; the tree sets the cap), 1 Ada
  GPU (`RTX6000ADA`, the sbatch default), 4 CPUs, 64G. Smokes use `--concurrency 2`.
- 41 jobs. Cost: about 22 E4B draws × 0.4 h + 12 31B draws × 0.85 h + 7 smokes × 0.2 h, so about 20 Ada GPU-h.
- Queued up front (weekend rule). Free when written: 8 Ada GPUs on pleiades-0-23, 4 on pleiades-0-17.

## Readings (written before any job runs)

1. **Smoke gate, per arm** (kill = cancel that arm's draws, unread; a failed smoke is fixed once, logged here, and
   re-run):
   - `status_SUCCESS` < 2;
   - retry trees: `solve_calls_gt3` ≥ 1 (e4b-budget: a task with more than 5 `solve` calls, read by hand),
     `root_calls_max` > 9 (e4b-budget > 13);
   - adapter trees: `adapter_steps` = 0, that is, no solver model call was served by the adapter;
   - read by hand, also a kill: any skill script that raised (an `ERROR` line from `replace.py` on a bad request is
     the script working, not a failure).
   - Skill use is not gated at the smoke: 2 tasks cannot show adoption.
2. **Draw-1 kill gates, per arm, on d1** (`tools/gate_actor.sh`, which cancels that arm's d2-d4 on a kill). Every bar
   was checked with `tools/d1_gate.py` on every comparator draw restricted to the cohort, and all passed (12 of 12
   E4B, 6 of 6 31B). A first set had `solve_calls_gt3>=1`, which 4 of the 12 comparator draws reach; it was raised
   to ≥ 3 before this file was written.
   - E4B (32 rows): `resolved<=2 empty>=9 timecap>=6 mean_wall>250 retry_miss>=4 solve_calls_gt3>=3 callcap>=14`.
   - e4b-budget: `resolved<=2 empty>=9 timecap>=6 mean_wall>300 retry_miss>=4 callcap>=20`.
   - Skill arms (both models): also `lever_skill_tasks<=0`. A skill nobody calls is not tested, and the arm stops.
     This gate is about the arm, so it is not checked on the comparator (which has no lever skill).
   - 31B (24 rows): `resolved<=7 empty>=13 timecap>=11 mean_wall>440 callcap>=11`.
   - 31B control d1: the 31B bars. A kill there cancels every 31B job of the round: the environment drifted.
   - E4B control d1: the E4B bars, reported only (the comparator is the R-021 draws).
3. **Promotion, per arm, after all its draws** (`tools/paired_boot.py`, statistic = solves per draw on the cohort,
   90% CI over tasks; wall ratio = arm mean task wall / comparator mean task wall):
   - E4B skill, hint and budget arms, against the 12 comparator draws on `sw-e4b-32`: **promote** if the point
     estimate is ≥ +1.25 and the wall ratio is ≤ 1.25 (e4b-budget ≤ 1.4).
   - E4B adapter arms, the same on `sw-e4b-32-foldb` (`--subset`): **promote** if the point estimate is ≥ +0.75 and the
     wall ratio ≤ 1.25.
   - 31B arms, against the 4 fresh control draws: **promote** if the point estimate is ≥ +1.5 and the wall ratio is
     ≤ 1.05.
   - **Drop** anything else, and any arm stopped by a gate.
   - **Drift check (reported).** If the E4B fresh control's mean is outside 5-11, or the 31B fresh control's mean is
     outside 11-16, that is stated next to every reading of that model, and the E4B arms are also compared with the
     fresh control.
4. **Mechanism (reported, not gates).** Per arm: `lever_skill_calls`, `lever_skill_tasks`, `lever_skill_errors`,
   `adapter_steps`; `retry_counts.py` (first-attempt empty, retried, rescued); empty patches; time caps; calls per
   task; malformed edits (`tools/analyze_traces.py`).
5. **What promotion buys.** A promoted E4B arm runs 12 draws on `cohorts/cdev2-79.txt` against the 12 R-021 retry
   draws (paired, R-021 readings). A promoted 31B arm runs 6 draws on cdev2-79 against the six base draws. Both are
   pre-registered as their own rounds. Two promoted arms of one model may be combined in one tree for that round.

**Blind guess (not a reading).** Each arm passes its smoke and d1: 70%. Promoted: e4b-a1 15%, e4b-a2 15%,
e4b-outline 10%, e4b-hint 15%, e4b-budget 20%, 31b-outline 10%, 31b-lineedit 15%. At least one promoted: 55%.

## Queued (2026-11-22)

- Smokes: e4b-a1 60511, e4b-a2 60512, e4b-outline 60513, e4b-hint 60514, e4b-budget 60515, 31b-outline 60516, 31b-lineedit 60517.
- e4b-a1 d1-d4, all `afterok` on 60511: 60524, 60531, 60538, 60545.
- e4b-a2 d1-d4, all `afterok` on 60512: 60525, 60532, 60539, 60546.
- e4b-outline d1-d4, all `afterok` on 60513: 60526, 60533, 60540, 60547.
- e4b-hint d1-d4, all `afterok` on 60514: 60527, 60534, 60541, 60548.
- e4b-budget d1-d4, all `afterok` on 60515: 60528, 60535, 60542, 60549.
- 31b-outline d1-d4, all `afterok` on 60516: 60529, 60536, 60543, 60550.
- 31b-lineedit d1-d4, all `afterok` on 60517: 60530, 60537, 60544, 60551.
- Controls, no dependency: 31b-ctl d1-d4 60518, 60519, 60520, 60521; e4b-ctl d1-d2 60522, 60523.
- Gate actors (`tools/gate_actor.sh`, logs `logs/gate_R-026_<job>.log`): each smoke (cancels that arm's d1-d4 on a kill),
  each arm's d1 (cancels its d2-d4), and 31b-ctl d1 (cancels every other 31B job of the round), with the bars of
  readings 1 and 2. E4B control d1 is read by hand.
