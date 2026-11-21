# R-015: 31B worked-example prompt (pre-registration)

Written 2026-11-21 (about 02:15Z), before any job of this round is submitted. Counts only; no trace content.
Tweak id **T-31b-013**. The `tweaks.md` row is added with the results, as for T-31b-012.

## Why

`rounds/skill-script-sizing.md` part A (5 base draws, 395 task-draws) found that the 31B finds the right file early
and then spends its calls deciding what to change:

- The reference file is named by call 3 in 293 of 395 draws, at a median of call 2.
- From the first naming of the file it eventually edits to the edit itself takes a median of **9 calls**: 7 in
  resolved draws, 12 in noisy-fail draws and 21 in draws that never land an edit.
- The first edit attempt comes at a median of call 12 (197 s). Losing draws reach call 12 at 292 s, against 135 s
  for winning ones. Model time is 89% of task wall time.
- Every locate-style change so far failed on effect (R-005, R-007, R-014's scout, EXP-032). Raising the call cap
  (T-31b-001) only moved tasks onto the time cap.

The user's direction (2026-11-20) is to let the model reason inside the caps and to support it where it fails,
without making it reason about time or call counts. The base prompt already *tells* the model to edit early (section
3, "Edit by tool call 12"). It has never *shown* a solve. One short worked example shows the shape of a solve: once a
read shows the cause, the next call is the edit. This is the only change in this round.

## Change

| ID | Arm | Tree | Change |
|---|---|---|---|
| T-31b-013 | example | `trees/31b-r015-example` | `trees/31b-base` plus one prompt section, "## 5. A worked example" (instruction 3162 → 4315 characters) |

- The section is placed after section 4 and before "Never". The rest of the tree (agent.yaml, sampling.yaml,
  eval_config.yaml, sections 1-4 and "Never") is byte-identical to `trees/31b-base`.
- The example is made up: a function `format_amount` in `ledgerkit/money.py` that drops the sign of negative
  amounts. Steps: one `git grep`, one `read_file` of a 40-line range, the cause named, `edit_file` on the two lines,
  one `python -c` check, `submit_patch`. The section says the names do not exist in the real repository and must not
  be searched for.
- It says nothing about time, call counts or limits, and it adds no new rule. The example's code has no braces,
  because ADK reads `{name}` in an instruction as a session-state placeholder; the first draft had f-strings and the
  validator rejected it (KeyError at runtime).

## Facts relied on

- The base comparison set: R-008 d1, d2, R-011 d3, d4, R-014 d5, resolved 28, 27, 30, 28, 32 (mean 29.0). Their
  per-draw counts from `tools/r015_gates.py`:

  | Draw | Resolved | Mean wall (s) | Empty | Time cap | Call cap | No edit attempt | First edit call (median) | Named → edit (median; resolved / unresolved) |
  |---|---|---|---|---|---|---|---|---|
  | R-008 d1 | 28 | 352.6 | 13 | 19 | 12 | 9 | 13 | 9 (6 / 12) |
  | R-008 d2 | 27 | 367.7 | 17 | 19 | 18 | 9 | 12 | 9.5 (8 / 13) |
  | R-011 d3 | 30 | 368.5 | 17 | 21 | 17 | 17 | 11 | 9 (7 / 9) |
  | R-011 d4 | 28 | 355.1 | 17 | 17 | 16 | 10 | 14 | 11.5 (7 / 15) |
  | R-014 d5 | 32 | 348.6 | 13 | 15 | 16 | 8 | 12 | 10 (8.5 / 12) |
  | pooled | 29.0 per draw | 358.5 | 77 (19.5%) | 91 | 79 | 53 | 12 | 9 (7 / 12) |

- The projection rule of R-014 is kept unchanged: projected Kaggle time = 10.04 h × (arm mean task wall / 361 s),
  so the 11.0 h gate means a mean task wall of at most 395 s.
- The `edit_file` matcher already tolerates whitespace (skill-script-sizing part B), so the example does not need
  to teach exact quoting beyond "exactly as read".

## Validation (done before this file was committed)

- `tools/validate_submission.py --official` (run in `env/harness.sif`) gives `trees/31b-r015-example` exactly the
  `trees/31b-base` profile: official `validate_directory` OK; the 8-minute packing-gate error, the
  `compile_submission` signature error and the `timeout_seconds` warning, all expected on the cluster trees. No
  placeholder or lint finding.
- `tools/compile_check.py trees/31b-r015-example`: one `LlmAgent swe_agent` with the six tools.

## Design

**31B, Ada** (`--constraint=RTX6000ADA`, 1 GPU, 4 CPUs, 64G). Flags: `--concurrency 4 --py313
env/py313-scorer/bin/python3.13 --task-envs env/taskenvs`, `HENG_SHIMS` off, the R-008/R-011/R-014 flags.

| Arm | Tree | Cohort | Draws | Run ids |
|---|---|---|---|---|
| smoke (not read) | `trees/31b-r015-example` | `runs/_cohorts/smoke-te.txt` (2 tasks), concurrency 2 | 1 | `S-015-31b-example-smoke` |
| example | `trees/31b-r015-example` | `cohorts/cdev2-79.txt` | 8 | `R-015-31b-example-d1..d8` |
| base | `trees/31b-base` | `cohorts/cdev2-79.txt` | 3 new | `R-015-31b-base-te-d6..d8` |

- **Comparison set.** Example d1-d8 against base d1-d5 above plus the 3 new base draws, so 8 and 8.
- **Order.** After the smoke, example d1 runs with base d6 beside it. The other 9 jobs are submitted only after the
  draw-1 gate (reading 3), all at once, in this order: example d2, base d7, example d3, example d4, base d8,
  example d5, d6, d7, d8. They start as Ada GPUs free.
- **Queue (2026-11-21T02:10Z).** Both Ada nodes are full with other users' jobs. asingal2 has 21 one-GPU jobs
  pending for the Adas. Our jobs have higher priority, and the user approved queueing ahead of them (2026-11-21).
  L-004 P1c (job 59898) is already first in line.
- **Cost.** About 2.05 Ada GPU-h per draw, so 11 draws plus the smoke is about 23 Ada GPU-h. A kill at the draw-1
  gate costs about 4.3 GPU-h (smoke, example d1, base d6).

## Checks and readings (written before any job runs)

1. **Smoke gate (not a resolve reading).** Passes if both rows are SUCCESS, there is no engine error, both traces
   carry the R-015 system instruction (it contains "A worked example"), and no tool call or patch names
   `ledgerkit` or `format_amount`. A failed smoke is fixed, the fix logged below, and the smoke re-run before any
   draw.
2. **Health, per draw.** No engine crash. A draw with fewer rows than its cohort is reported and not used. Non-SUCCESS
   rows stay at or below 2% of task-draws.
3. **Draw-1 kill gates.** Each is computed from example d1 alone with `tools/r015_gates.py`; any one kills the arm.
   - the projected Kaggle time exceeds 11.0 h (mean task wall above 395 s);
   - resolved ≤ 25, the base mean minus 4;
   - empty patches above 29.5% of task-draws (base 19.5% + 10 points), so 24 or more of 79;
   - the example leaks: a tool call or a patch names `ledgerkit` or `format_amount` in more than 4 of 79 tasks.
4. **Decision, 8v8, the R-012 rule.**
   - **Kept:** mean(example) − mean(base) ≥ +1.9, and the projected Kaggle time from all 8 example draws is
     ≤ 11.0 h. A kept arm replaces `trees/31b-base` as the 31B config that the next orchestration rounds build on
     and that the 31B LoRA adapter is trained on. It still needs a held-out check, which is its own round.
   - **Not kept:** anything else. There are no extension draws.
5. **Mechanism (reported for every outcome; it does not override reading 4).** From `tools/r015_gates.py`, pooled
   over the 8 example draws:
   - **Primary:** the median number of calls from the first naming of the file that is first edited to that edit,
     against the base's pooled 9. **Met** at 7 or fewer, the base's resolved-draw median. The base per-draw medians
     range from 9 to 11.5.
   - Also reported, against the base pooled values: the same median in resolved and unresolved draws (7 / 12); the
     median first-edit call (12) and its clock (197 s); draws with no edit attempt (53 of 395); time-cap and call-cap
     task-draws per draw (18.2, 15.8); empty patches (19.5%); and the paired per-task difference over the 79 tasks
     (resolve rate per task over 8 draws) with a 90% bootstrap CI (10,000 resamples, seed 0).
   - The example-leak count over all 8 draws.

**Blind guess (not a reading).** Kept 20%, not kept 65%, killed at draw 1 15%. Pooled named → edit median: 8.

Results are appended below as new sections and apply these readings as written.

## Smoke log

- `S-015-31b-example-smoke`, job 59920, pleiades-0-23, 2026-11-21, 10 min 9 s. **Smoke gate passes.**
  - Both rows SUCCESS, no engine error in the job log.
  - Both traces carry the R-015 system instruction ("A worked example" in 2 of 2).
  - No tool call or patch names `ledgerkit` or `format_amount` (`r015_gates.py` example-leak tasks 0).
  - Not read, as written: resolves, wall, calls.
- Example d1 and base d6 submitted next, side by side.

## Results: draw 1 (2026-11-21)

- `R-015-31b-example-d1` (job 59932, pleiades-0-23, 2 h 13 min) and `R-015-31b-base-te-d6` (job 59933, 1 h 56 min).
- **Health passes for both.** 79 of 79 rows, all SUCCESS, no engine error. Job 59932 ends with the known cgroup
  oom-kill flag (MaxRSS 58.4 GB; R-007, R-008 and R-011 record the same flag with every row written). No test exit
  code or test tail shows a killed test (exit codes: 0 x25, 1 x32, -1 x17, 2 x4, 124 x1). The draw is used.

| Draw-1 gate (example d1) | Bar | Value | Fires |
|---|---|---|---|
| Projected Kaggle time | > 11.0 h (wall > 395 s) | 10.71 h (385.0 s) | no |
| Resolved | ≤ 25 | **25** | **yes** |
| Empty patches | ≥ 24 of 79 | 21 | no |
| Example leak | > 4 tasks | 0 | no |

- **Reading 3: the arm is killed at draw 1** (resolved 25, at the bar). Example d2-d8 and base d7-d8 are not
  submitted. Reading 4 is not reached.
- **Mechanism (reported; d1 only, against base d6 from the same hours):**
  - calls from first naming of the edited file to the edit: median 10 (resolved 7, unresolved 11.5; n 63) against
    base d6 9.5 (7 / 11; n 70) and the base pooled 9. **Not met** (bar 7).
  - first-edit call median 13 against 12; first-edit clock 209.7 s against 208.5 s.
  - no edit attempt 15 against 8; time-cap task-draws 29 against 15; call-cap 13 against 14; empty patches 21
    against 16.
  - So the worked example did not shorten the step from file to edit. It made more draws run out the clock without
    an edit (wall 385.0 s against 335.1 s).
- **Base d6** (27 of 79, wall 335.1 s, projected 9.32 h) joins the 31B base record. The base cdev2-79 draws are now
  R-011 d1-d4 plus R-014 d5 and R-015 d6. Its fold-B rows join the L-005 control set, as L-005 says.
- **Blind guess check:** killed at draw 1 was 15%.
- Cost: smoke 0.17 + two draws 4.15 = about 4.3 Ada GPU-h, as budgeted for a draw-1 kill.
