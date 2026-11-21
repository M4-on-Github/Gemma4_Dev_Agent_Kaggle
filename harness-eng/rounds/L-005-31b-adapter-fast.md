# L-005: first 31B adapter, trained on the 31B's own fastest solves (pre-registration)

Written 2026-11-21 (about 05:30Z), before any job of this round is submitted. Counts only; no trace content. The
training data and the adapter live under `/data/mmyatmau/gemma4-lora/` and never enter git (plan.md:52).

## Question

Does a LoRA adapter trained on the 31B's own shortest resolved trajectories on fold A raise the 31B's resolves on
fold B, and does it do so without pushing the Kaggle projection over 11.0 h?

## Why this data

- The 31B is wall-bound: 10.04 h projected against the 11.0 h gate. Serving with LoRA on costs 0.916x decode on Ada
  (R-013), and the L4 ratio is being measured now (EXP-085, S6). So an adapter that solves more by taking longer cannot
  ship. It has to solve more, or as many, in fewer calls.
- The 31B finds the right file early and then spends a median of 9 calls deciding what to change: 7 in resolved draws,
  12 in unresolved ones (`rounds/skill-script-sizing.md` part A). Its own fast solves show the behaviour we want: read
  the cause, then edit.
- So the data is the 31B's complete resolved fold-A trajectories, shortest first: rejection-sampled self-distillation
  that selects for speed. No E4B rows, no synthetic D1 rows (D1 targets the E4B's edit-copy failures, which the 31B
  does not have).

## Data (built 2026-11-21, before this file was committed)

- Source: D2 `31b-all-lfold-a.jsonl` (254 rows from 16 31B arms over fold A, `rounds/L-001-lora-data-desk.md`).
- `tools/lora/select_fast.py --per-task 8 --max-calls 20` keeps only `complete` rows (ending at the first
  `submit_patch` response), drops the 6 no-thinking rows, drops rows with more than 20 LLM calls, then per task keeps
  the 8 with the fewest calls (ties by run name).
- Output: `/data/mmyatmau/gemma4-lora/data/d2/31b-fast-lfold-a.jsonl`, sha256 prefix `0ae82f5ef8b624dc`.
  - 76 rows over 15 tasks; per task 1, 1, 2, 2, 2, 3, 3, 6, then 8 for seven tasks.
  - LLM calls per row: min 5, median 11, max 20.
  - Dropped: 114 not complete (94 compaction cuts, 16 nudge cuts, 4 other), 16 over 20 calls, 6 no-thinking, 42 over
    the per-task cap.
- Trainer dry run (`--packed --max-len 16384 --val-tasks 1`, 31B tokenizer): 75 encoded (1 span mismatch), 67 train
  rows, 8 validation rows from 1 held-out fold-A task; 0.89M tokens, 0.35M trained; length median 12,069, p90 14,571,
  max 15,406.

## Training

- `slurm/lora_train.sbatch` on one RTX 6000 Ada (`--constraint=RTX6000ADA --gpus=1 --cpus-per-task=4 --mem=128G
  --time 6:00:00`), `tools/lora/train_lora.py` with `--packed` (L-004).
- `--model models/gemma-4-31b-it-qat-w4a16-ct --tools /data/mmyatmau/gemma4-lora/schema/tools.json
  --system-from-trace runs/R-014-31b-base-te-d5/traces/trace_fastapi_11355.json` (the 31B base system instruction, as
  in L-004) `--data .../31b-fast-lfold-a.jsonl --val-tasks 1 --max-len 16384 --rank 16 --alpha 32 --lr 1e-4
  --epochs 2 --accum 2 --warmup 5 --seed 1 --out /data/mmyatmau/gemma4-lora/adapters/L-005-f1`.
- Accumulation 2, not L-003's 8: 67 rows at 8 would give 8 optimizer steps per epoch, nearly all warmup. At 2 it is 34
  steps per epoch, 67 in all.
- **Starts only after** L-004 P1c (chunk check) and P3b reading 2 (learns) pass. If either fails, nothing here runs.
- Expected cost about 3.2 Ada GPU-h (0.8M tokens per epoch at P1's 6.7 ms per token, plus the CPU load).

### Training readings

1. **Health.** No non-finite loss or grad norm; the job completes; `epoch1/` and `final/` are written; the packed
   exactness check passes on the first and last layer. Record steps, wall and ms per token.
2. **Fit.** Validation loss on the 8 held-out rows at step 0 and at the end, as in L-003 training reading 2: the end
   value must be below step 0. If it rose by more than 10% from its minimum, the lower of `epoch1`/`final` is the one
   evaluated. If both are above step 0, nothing is evaluated.

## Evaluation on fold B

**Arm.** `adapters/trees/31b-l5` (gitignored) = `trees/31b-base` with `adapter: l5` and the chosen adapter dir.

| Arm | Tree | Cohort | Draws | Run ids |
|---|---|---|---|---|
| smoke (not read) | `adapters/trees/31b-l5` | `runs/_cohorts/smoke-te.txt`, concurrency 2 | 1 | `S-005-31b-l5-smoke` |
| adapter | `adapters/trees/31b-l5` | `cohorts/lfold-b.txt` (40) | 8 | `L-005-31b-l5-d1..d8` |

- Ada, 1 GPU, 4 CPUs, 64G; `--concurrency 4 --py313 env/py313-scorer/bin/python3.13 --task-envs env/taskenvs`, the
  R-008/R-011/R-014 flags.
- **Control: the existing 31B base draws restricted to fold B, not new full0 draws.** R-013 measured `full_zero`
  against base at a mean absolute logprob delta of 0.0, so a zero adapter changes speed, not outputs. The control set
  is R-008 d1, d2, R-011 d3, d4, R-014 d5 on the 40 fold-B ids, plus R-015 base d6-d8 if they exist when the adapter's
  8th draw finishes (if R-015 is killed at its draw-1 gate, d7 and d8 never run).
  - Fold-B values already on disk (read 2026-11-21, base only): resolved 14, 16, 16, 14, 16 (mean 15.2, SD 1.1);
    mean task wall 339.7 s.
  - The adapter arm carries the LoRA-on decode cost and the base arm does not. This is the conservative direction for
    the adapter, and it is the cost a shipped adapter pays.
- **Order.** Smoke, then d1. After the draw-1 gate, d2-d8 are submitted at once. They queue with R-015's jobs as Ada
  GPUs free.
- **Cost.** About 1.1 Ada GPU-h per 40-task draw, so about 9.5 GPU-h for 8 draws and the smoke, plus training.

### Kaggle projection

For an adapter arm with mean fold-B task wall W_a, against the base's W_b on the same draws' fold-B rows:

projected = 10.04 h × (W_a / W_b) × (f / r_L4 + 1 − f) / (f / 0.916 + 1 − f)

- f = 0.89 is the model-time share of 31B task wall (R-015 "Why"). 0.916 is the Ada LoRA decode ratio (R-013).
- r_L4 is EXP-085's `full_zero`/base decode ratio at 4 streams on L4. Until EXP-085 reports, r_L4 = 0.75 (the
  E4B-on-L4 value, EXP-047) is the planning value [I].
- The formula assumes model time scales with decode speed and tool time does not [I]. At r_L4 = 0.75 the last factor
  is 1.199, so the adapter must run at W_a / W_b ≤ 0.914 to project ≤ 11.0 h.

### Readings (written before any job runs)

1. **Smoke and health.** Both smoke rows SUCCESS, no engine error, every model-named step in both traces names `l5`.
   Per draw: non-SUCCESS rows at most 2%; a draw with fewer rows than its cohort is reported and not used.
2. **Draw-1 kill gates** (from d1 alone; any one kills the arm):
   - resolved ≤ 12 (the base fold-B mean minus 3; the base range is 14-16);
   - projected Kaggle time above 12.0 h by the formula above;
   - empty patches in 12 or more of 40 tasks.
3. **Decision, 8 adapter draws against the control set.** Paired over the 40 fold-B tasks, using each task's
   resolve rate over its draws per arm. The statistic is the mean of (adapter rate − base rate) × 40, in solves per
   draw, with a 90% bootstrap CI over tasks (10,000 resamples, seed 0).
   - **Helps:** CI lower bound above 0 and projected ≤ 11.0 h at the r_L4 then known. The 31B LoRA direction is kept;
     the shipped adapter is retrained on the frozen config's prompt (about Nov 26) and checked once more on fold B.
   - **Helps but too slow:** CI lower bound above 0 and projected above 11.0 h. Not shippable at the current caps;
     the trade (a lower time cap, or a recorded override) is the user's decision.
   - **Extend:** point estimate +1.0 or more without the CI above 0: 8 more adapter draws (d9-d16) once, the same rule
     on all 16, no further extension.
   - **Harm:** point estimate −1.0 or less. Not kept.
   - **Otherwise:** not kept.
4. **Mechanism (reported for every outcome; it does not override reading 3).** With `tools/r015_gates.py` over the
   adapter draws and the control draws (fold-B rows): median calls from first naming of the edited file to the edit
   (base pooled 9 on cdev2-79); first-edit call and clock; no-attempt draws; time-cap and call-cap task-draws; mean
   task wall W_a / W_b.

**Blind guess (not a reading).** Helps 20%, helps but too slow 10%, extend 20%, not kept or harm 50%. W_a / W_b about
0.95.

## Results

(appended after the jobs finish)

- 2026-11-21: L-004 P1c (chunk check, abs diff 0.000344) and P3b (learns, ratio 0.074) both pass. Training
  `L-005-f1` submitted as written.

### Training (`L-005-f1`, job 59938, pleiades-0-23, 2026-11-21T05:29-08:39Z)

- **Training reading 1, health: passes.** 67 steps, no non-finite loss or grad norm; packed check 13/13 exact (max
  abs diff 0.0); `epoch1/` (step 34) and `final/` written. Training 11,067 s (6.91 ms per token); job wall 11,397 s,
  CPU load included (3.2 Ada GPU-h, as budgeted).
- **Training reading 2, fit: passes.** Validation loss (8 held-out rows) 0.1809 at step 0, 0.1643 at the end; the
  minimum is 0.1637 at step 32, so the end is 0.4% above it (bar 10%). `final` is the adapter evaluated.
  - Training loss, mean of the first 8 steps 0.197, last 8 steps 0.163.
- `adapters/trees/31b-l5` (gitignored) is `trees/31b-base` plus `adapter: l5` and `final/` copied as
  `adapters/l5` (820 tensors, BF16, names and shapes equal to the served `full_zero`). The validator gives the same
  two errors and two warnings as `adapters/trees/31b-full0`, which R-013 served (the 8-minute cluster cap fails the
  11 h pack gate; the harness's `compile_submission` signature).
- Smoke `S-005-31b-l5-smoke` submitted.

### Smoke (`S-005-31b-l5-smoke`, job 59971, pleiades-0-23, 12 min 46 s)

- **Reading 1 passes.** 2 of 2 rows SUCCESS; no engine error or traceback in the job log; every model-named step in
  both traces names `l5` (11 of 11 and 32 of 32), none names `full_zero`. Resolves and wall not read.
- `L-005-31b-l5-d1` submitted on fold B.
