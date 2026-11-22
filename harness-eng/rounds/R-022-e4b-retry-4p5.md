# R-022: E4B retry on an empty attempt at the Kaggle time cap, 4.5 min (pre-registration)

Written 2026-11-22, before any job of this round is submitted. Counts only; no trace content. Tweak id
**T-e4b-022**. Part of the goal set by the user on 2026-11-21: find an orchestration framework for both models that
can win.

## Why

- R-021 measured the retry layout at **+1.08 solves per draw, CI +0.08..+2.08**, with a task cap of **8.0 min**.
- The Kaggle candidate must run at **4.5 min**: the pack gate is `120 x (cap + 1.0) <= 11.0 h`.
- A retry spends time. At 8 min, 11.5% of retry rows ran past 270 s, against 7.4% of control rows. Counting those
  rows as lost gives 7.42 against 6.42, but that is an estimate from rows that ran at 8 min. A solver that is cut
  off, or a retry that never starts, behaves differently from a row that is only relabeled.
- On Ada the E4B runs at about 105-115 s per task at time scale 1.0, and the EXP-048 Kaggle projection
  (3.56-3.96 h for 120 tasks) works out to about 107-119 s per task. So the Ada clock is a fair stand-in for the
  Kaggle L4 clock. That is a stated assumption, not a measurement.
- This round answers one question before H-003 runs on Kaggle: **does the gain hold at the cap the candidate ships
  with?**

## Change

| ID | Arm | Tree | Change |
|---|---|---|---|
| T-e4b-022 | control | `trees/e4b-r022-ctl-4p5` | `trees/e4b-r020-ctl` with `max_time_minutes` 8 → 4.5 |
| T-e4b-022 | retry | `trees/e4b-r022-retry-4p5` | `trees/e4b-r020-retry` with `max_time_minutes` 8 → 4.5 |

- `diff -r` against the R-021 trees (cccd61b) shows only the `max_time_minutes` line and its comment in
  `eval_config.yaml`.
- The solver prompt still says "28 tool calls and 8 minutes". That is the Kaggle candidate as H-003 describes it
  (one variable, as EXP-050).
- Validator (`--official`, `env/harness.sif`) on the retry tree:
  - `adk_submission.validate_directory` OK;
  - the two expected warnings, VERIFY(Q1) skill scripts and `timeout_seconds` 240;
  - the H-002 false error, and the cluster-only `compile_submission` TypeError;
  - **the pack-gate error is gone** at 4.5 min.

## Runs

| Arm | Cohort | Draws | Run ids |
|---|---|---|---|
| control | `cohorts/cdev2-79.txt` | 12 | `R-022-e4b-ctl-4p5-d1..d12` |
| retry | `cohorts/cdev2-79.txt` | 12 | `R-022-e4b-retry-4p5-d1..d12` |

- Flags: as R-021 (`slurm/eval.sbatch`, `--concurrency 4 --py313 env/py313-scorer/bin/python3.13 --task-envs
  env/taskenvs`, time scale 1.0). 1 Ada GPU, 4 CPUs, 64G per job.
- **All jobs pinned to pleiades-0-23 (`-w`).** In R-021, 14 jobs on pleiades-0-17 ran out of memory, and one lost its
  model server mid-run. None of the jobs on 0-23 did.
- **No smoke.** Both trees passed R-021's smokes and ran 24 draws. The only change is one number in
  `eval_config.yaml`. The draw-1 gates cover a broken cap.
- Draws are submitted interleaved (ctl d1, retry d1, ...), with no dependency. About 24 × 0.7 = 17 Ada GPU-h.
- Queueing follows the weekend rule. A draw-1 kill cancels every pending or running draw of both arms, unread.

## Readings (written before any job runs)

1. **Draw-1 kill gates** (`tools/d1_gate.py`).
   - Retry d1, kill on any of:
     - resolved ≤ 3;
     - empty ≥ 23;
     - time caps ≥ 20;
     - `retry_miss` ≥ 3;
     - `solve_calls_gt3` ≥ 1.
   - Control d1, kill on resolved ≤ 3 or empty ≥ 23.
   - The time-cap bar is raised from R-021's 7 to 20. At 8 min, about 9 retry rows per draw ran past 270 s. The bar
     catches a cap that cuts most tasks, not the expected cut.
   - Read by hand, and also a kill: any row whose error reports a session timeout other than 4.5 min. That would
     show the cap was not read from the tree.
2. **Server deaths.** A draw with any `litellm.InternalServerError` row is invalid. It is re-run once, under the
   same id with a `b` suffix, and the deviation is logged here before the decision is read. The gates are not
   changed.
3. **Decision**: retry d1-d12 against control d1-d12, with `tools/paired_boot.py` (79 tasks, 90% CI, 10,000
   resamples, seed 0). The wall ratio is reported. The rules are R-020's, word for word:
   - **Helps:** the CI lower bound is above 0.
   - **Kept on mechanism:** the CI lower bound is at or below 0, and all of these hold: rescued ≥ 0.5 per draw;
     the point estimate is at least +0.5; the wall ratio is at most 1.4.
   - **Dropped:** anything else.
4. **Mechanism (reported)**, per draw for both arms:
   - the `solve`-call histogram;
   - first empty / non-empty / unknown;
   - retried, rescued, over-retry, `solve_after_submit`;
   - empty, time caps, mean wall;
   - task wall p50/p90/p99, and the share of rows over 270 s.
   - **The Kaggle projection:** `120 × (mean task wall + 60 s)` for each arm, against the 11.0 h gate.
   - **Against R-021 (8 min):** each arm's resolved per draw, and the 270-s cut estimate (7.42 / 6.42) against what
     4.5 min gives. This is a check on the estimate, not a reading.

## What each outcome means

- **Helps or kept.** H-003 ships as written: the retry layout at 4.5 min, pending H-002 and the Kaggle dev-48 run.
  The R-022 numbers replace the 270-s estimate in H-003.
- **Dropped.** At the Kaggle cap the retry layout does not pay for its time. The E4B candidate on Kaggle stays the
  EXP-050 single loop, and H-003 is withdrawn with a note on the consolidated branch. A retry with a shorter first
  attempt would be the next variant; it is not queued.

**Blind guess (not a reading).** Passes the d1 gates: 85%. Helps: 35%. Kept on mechanism: 30%. Dropped: 35%.

## Queued (2026-11-22)

- Draws, all `-w pleiades-0-23`, no dependency, as (control, retry): d1 60280/60281, d2 60282/60283, d3 60284/60285,
  d4 60286/60287, d5 60288/60289, d6 60290/60291, d7 60292/60293, d8 60294/60295, d9 60296/60297, d10 60298/60299,
  d11 60300/60301, d12 60302/60303. Five ran at once at submission; the rest wait for a GPU on 0-23.
- Gate actors (`tools/gate_actor.sh`): retry d1 on 60281 and control d1 on 60280, with the reading-1 bars. Each
  cancels every other R-022 job on a kill.

## Draw-1 gate (reading 1), 2026-11-22: KILLED by the control gate

- Control d1 (60280) COMPLETED in 44 min: 79 rows, resolved 4, **empty 23**, time caps 1 (the error text reports
  4.5 min, so the cap was read from the tree), no server error.
- **`empty>=23` fired at exactly 23.** As pre-registered, `tools/gate_actor.sh` cancelled every other R-022 job. That
  includes retry d1 (60281), cancelled at 69 of 79 rows, and draws d2-d5, which were running. None of them is read.
- **The kill is a bar error, not a broken tree.** The bar was copied from R-020, where it was meant to catch the
  no-submit solver breaking. It was not checked against R-021's control, which ran the same solver at 8 min:
  - R-021 control empties per draw: 15, 16, 13, 19, 15, **24**, **23**, 20, 15, 19, 19, 10. The bar would have
    fired on 2 of its 12 draws.
  - Control d1's other counts sit inside R-021's control range: resolved 4 (range 4-9), time caps 1 (range 0-2).
- The decision is not read. The same comparison is re-registered as R-023, with every kill bar set outside the arm's
  own per-draw range in R-021. This section was written before R-023 was submitted.
