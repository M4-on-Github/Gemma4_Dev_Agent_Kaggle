# R-033: E4B solver temperature 0.6 on cdev2-79, with concurrent controls (pre-registration)

Written 2026-11-22, after R-032's results and before any job of this round is submitted. Counts only; no trace
content, no ids. Tweak id **T-e4b-033** (the tree of T-e4b-032a). Same goal as R-029 (set by the user on
2026-11-22): raise the solve rate and the models' abilities, with small sweeps before bigger runs. This is the
bigger run that R-032's reading 4 buys.

## Why

- R-032 promoted `trees/e4b-retry-t06` (solver temperature 0.6) by its written bar: +1.25 solves per draw on
  `sw-e4b-32` against R-021 retry ×12 (CI −0.33..+3.00), wall 1.04.
- **The same round showed drift.** Its fresh controls (unchanged `trees/e4b-r020-retry`) gained +1.50 over the same
  comparator, and against the 4 fresh control draws t06 was 0.00. So the promotion is most likely the comparator
  drifting, not the temperature.
- R-032 reading 4 names the comparator: 12 draws on cdev2-79 against the 12 R-021 retry draws. That comparator is a
  day old, and R-032 shows it can drift by as much as the effect being tested. So **12 concurrent control draws** run
  in this round, and the decision needs both comparisons.
- Prior, stated now: low. At 0.6 the failed-edit share fell only to 0.438 (bar 0.428), and every E4B sampling change
  before it was noise (R-003, R-007, R-032 t03).

## Runs

| Run | Tree | Cohort | Draws |
|---|---|---|---|
| `R-033-e4b-t06-c79-d1..d12` | `trees/e4b-retry-t06` (unchanged since R-032) | `cohorts/cdev2-79.txt` | 12 |
| `R-033-e4b-ctl-c79-d1..d12` | `trees/e4b-r020-retry` (unchanged) | `cohorts/cdev2-79.txt` | 12 |

- Submitted interleaved (t06 d1, ctl d1, t06 d2, ...), so both arms share the nodes and the hours.
- Flags as R-032 (`-J heng_e4b`, concurrency 4, py313, task envs, 1 Ada GPU, 4 CPUs, 64G). No smoke: both trees ran
  in R-032 unchanged.
- Cost: 24 draws × about 0.75 h ≈ 18 Ada GPU-h.

## Readings (written before any job runs)

1. **Draw-1 kill gates** on t06 d1 and on ctl d1 (`tools/gate_actor.sh`; a kill on either cancels every other
   R-033 job, since a broken control leaves nothing to compare against):
   `resolved<=3 empty>=23 timecap>=7 retry_miss>=4 solve_calls_gt3>=6 mean_wall>250 callcap>=30`.
   - Checked with `tools/d1_gate.py` on the 12 R-021 retry draws and the 2 R-029 cdev2-79 controls: 14 of 14 PASS.
     The maxima there are `solve_calls_gt3` 4, `retry_miss` 2, empty 11, callcap 16, mean wall 170.4 s.
   - A first set had `solve_calls_gt3>=3`, which 3 of the 12 comparator draws reach. It was raised to ≥ 6 before
     this file was written.
2. **Decision** (`tools/paired_boot.py`, 79 tasks, 90% CI, 10,000 resamples, seed 0):
   - (a) t06 ×12 against R-021 retry ×12 (R-032 reading 4's comparator; 7.58 per draw);
   - (b) t06 ×12 against the 12 concurrent controls;
   - wall ratio = t06 mean task wall / concurrent-control mean task wall.
   - **Helps (adopt):** the CI lower bound of (a) is above 0, **and** the point estimate of (b) is at least +0.5,
     **and** the wall ratio is at most 1.15.
   - **Dropped:** anything else. The shipping E4B layout stays `trees/e4b-r020-retry` at temperature 1.0.
   - Reported, not read: (b)'s CI; t06 against the pool of the 12 R-021 draws plus the 12 concurrent controls; the
     concurrent controls against R-021 (the drift).
3. **Mechanism (reported):** failed-edit share (`tools/edit_status_counts.py`); empty final patches; first-attempt
   empty, retried, rescued (`tools/retry_counts.py`); time caps; calls per task.

## What each outcome means

- **Helps:** the E4B shipping layout becomes `trees/e4b-retry-t06`, and a Kaggle handoff carries the one-line
  sampling change (the dev-48 wall check of H-003 covers it, since the wall ratio is bounded at 1.15).
- **Dropped with (b) near 0:** R-032's +1.25 was comparator drift. E4B sampling is closed as a lever.

**Blind guess (not a reading).** Both d1 gates pass: 90%. Helps: 7%. (b) point estimate ≥ +0.5: 25%.

## Queued (2026-11-22)

- t06 d1-d12: 60771, 60773, ..., 60793 (odd ids). ctl d1-d12: 60772, 60774, ..., 60794 (even ids).
- Gate actors on 60771 (t06 d1) and 60772 (ctl d1), each cancelling every other R-033 job on a kill, with the bars
  of reading 1.

## Deviation, out-of-memory jobs (recorded 2026-11-22 before reading 2 is computed)

- Both d1 gates PASS (`logs/gate_R-033_60771.log`, `_60772.log`). Nothing was cancelled.
- 7 of the 24 jobs ended `OUT_OF_MEMORY` (64G cgroup), all on pleiades-0-17: t06 d1, d2, d3, d10 and ctl d1, d3, d8.
  This is the R-021 pattern.
- Checked blind to the resolved field, with R-021's rule: every one of the 24 runs has 79 SUCCESS rows. No row or log
  has a model-server error. In every log the OOM event comes after the run's `done` line. Error counts per run (time
  caps 0-3, tool budget 0-4, other 0-1) are in the range of the clean jobs. **All 24 are kept**, and the readings
  are unchanged.

## Results (2026-11-22): **dropped**

**Decision (reading 2)**, `tools/paired_boot.py`, 79 tasks:

| Comparison | Arm per draw | Base per draw | Point | 90% CI |
|---|---|---|---|---|
| (a) t06 ×12 vs R-021 retry ×12 | 6, 8, 11, 9, 7, 8, 9, 8, 11, 9, 7, 5 (8.17) | 7, 12, 6, 9, 9, 7, 8, 6, 8, 5, 7, 7 (7.58) | +0.58 | −0.58..+1.83 |
| (b) t06 ×12 vs concurrent ctl ×12 | (as above) | 10, 6, 8, 7, 8, 8, 8, 10, 8, 8, 10, 6 (8.08) | **+0.08** | −1.08..+1.25 |
| pool: t06 vs R-021 + ctl (24) | | | +0.33 | −0.58..+1.33 |
| drift: ctl vs R-021 | | | +0.50 | −0.83..+1.92 |

- Wall ratio: 147.5 / 139.6 s = 1.06.
- (a)'s CI lower bound is not above 0, and (b) is below +0.5, so the reading is **dropped**. The shipping E4B layout
  stays `trees/e4b-r020-retry` at temperature 1.0.
- R-032's +1.25 on `sw-e4b-32` did not hold. Against concurrent controls it was 0.00 there and +0.08 here.

**Mechanism (reading 3), 12 draws each:**

| Arm | Failed-edit share | Empty final patches per draw | First-attempt empty | Retried | Rescued | Time caps | Calls per task |
|---|---|---|---|---|---|---|---|
| t06 | 0.558 (1610 ok, 2035 failed) | 4.08 | 103 | 101 | 10 | 18 | 16.6 |
| ctl | 0.540 (1568, 1841) | 4.50 | 161 | 157 | 14 | 15 | 16.1 |
| R-021 retry | 0.552 (1557, 1921) | 5.25 | | | | | 16.2 |

- On cdev2-79, temperature 0.6 does not lower the failed-edit share. The sw-e4b-32 drop (R-032) was cohort-specific.
- It does cut empty first attempts by a third (161 → 103). The retry was already catching those, so final empties
  move only 4.50 → 4.08, and rescues fall (14 → 10).
- **E4B sampling is closed as a lever** (R-003, R-007, R-032, R-033).
- Process lesson, kept: a 4-draw screen against an old comparator can pass on drift alone. R-032's fresh controls
  showed it, and the concurrent controls here settled it. Promotion rounds from now on carry concurrent controls.
