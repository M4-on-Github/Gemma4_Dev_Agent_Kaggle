# L-008: E4B solver self-distillation adapter (pre-registration)

Written 2026-11-22, before the training job is submitted. Counts and losses only; samples and adapters stay under
`/data/mmyatmau/gemma4-lora/` (plan.md:52). No ids, trace text or code here.

## Question

Does a LoRA on the E4B **solver**, trained only on the solver's own resolved attempts under the shipping solver
prompt, raise resolves on the 40 unseen `lfold-b` tasks in the shipping retry layout (`trees/e4b-r020-retry`)?

## Why this adapter and not a1/a2 again

- a1 and a2 (L-003, L-007, R-026) were trained on synthetic edits and on 31B trajectories under the single-agent
  prompt. Served as the retry solver, they used about 3.5 times the control's tool calls (R-026 reading 4), and the
  a1 single-agent arm ran 3.51 times the wall (L-003). R-026 put this down to training off-distribution: wrong
  prompt, wrong tools, wrong model.
- This adapter is trained on-distribution: the same model (E4B), the same system prompt as ADK serves it, the same
  five solver tools, and the solver's own sampled turns. Only the selection is new: rows come from resolved task-draws
  only (rejection-sampling fine-tuning). The expected effect is a shift toward the behaviour of the draws that
  resolved, without the call bloat.
- The E4B has spare wall on Kaggle (about 4.4-4.9 h projected on L4 against the 11 h gate; LoRA-on decode about 0.75×
  on L4, EXP-047), so an adapter's serving cost fits.

## Data (fixed; built 2026-11-22 by `tools/lora/solver_to_sft.py`, new)

- **Source runs.** Every run dir under `runs/` whose copied tree (`agent/`) has `prompts/solver.md`,
  `sub_agents/solver.yaml` and `configs/sampling.yaml` byte-identical to `trees/e4b-r020-retry`, excluding held-out
  runs: 152 runs (R-020 to R-036 retry and control layouts, and their smokes). Only `lfold-a` task-draws are read.
- **Row.** For each resolved fold-A task-draw, the last `solve` attempt: the solver system prompt as ADK builds it
  (`prompts/solver.md` with `{problem_description}` and `{hints?}` filled from the task data, as
  `swegemma/harness/agent_runner.py` sets the session state, plus ADK's identity line), the root's request as the
  user turn, each solver LLM call with its tool responses, and the solver's closing text turn.
  - A probe without the state fill found a task-dependent 16-475 token gap at the first call. With it, the median
    first-call gap against the recorded prompt tokens is 1 token, and the median worst gap per row is 15.
  - Rows are cut before the first call whose re-rendered prefix differs from the recorded prompt tokens by more than
    64 (`cut`, no closing turn).
- **Counts.** 3,790 fold-A task-draws, 305 resolved. Kept 299 rows (272 complete with a closing turn, 23 cut, 4
  without a final text), dropped 2 too short and 4 without metrics. 20 tasks; rows per task are heavily skewed
  (104, 60, 42, 22, 15, 13, 9, 6, 5, 5, 4, 3, 2, 2, 2, 1, 1, 1, 1, 1).
- **Trainer selection** (`train_lora.py`, dry run): `--cap-per-task 16` keeps 135 rows; `--val-tasks 1` holds out one
  task (16 rows) for validation; at `--max-len 32768` none is dropped. 119 train rows, 1.75M tokens, 0.54M trained.
  Median row 12.2k tokens, p90 19.7k, max 25.5k.

## Part 1: training

- **Trainer.** `tools/lora/train_lora.py` at the commit that adds this file. New flag `--system-from-row` keeps each
  row's own system message (the problem statement differs per task); nothing else changes.
- **Job.** `sbatch -J heng_lora slurm/lora_train.sbatch L-008-l8 ...`, 1 RTX 6000 Ada, 4 CPUs, 64G,
  `--time 10:00:00`.
- **Model and adapter.** `models/gemma-4-e4b-it-qat-w4a16-ct`; LoRA rank 16, alpha 32 on the q/k/v/o/gate/up/down
  targets, as a1.
- **Prompt and tools.** `--system-from-row`; `--tool-names run_command,read_file,edit_file,write_file,get_status`.
- **Loss.** `--default-train all`: the thought channel and the call of every solver turn, and the closing turn.
- **Optimization.** lr 2e-4, warmup 5, cosine; 3 epochs; accumulation 4 (30 steps per epoch, about 90 steps); clip
  1.0; seed 1. a1's settings (lr 1e-4, accumulation 8, 2 epochs) would give 30 steps on this data; the higher lr and
  the third epoch are the usual rejection-sampling settings for a small on-policy set. `epoch1/` and `epoch2/` are
  saved.
- **Output.** `/data/mmyatmau/gemma4-lora/adapters/L-008-l8/`. Never committed.
- **Budget.** About 2-4 Ada GPU-h.

### Training readings

1. **Health.** No non-finite loss or grad norm, the job completes, `final/` is written. Recorded: steps, wall,
   ms per token. If the job runs out of memory, it is re-run once at `--max-len 24576` (one row dropped), logged
   here first.
2. **Choice** (`tools/lora/pick_adapter.py`, new, run as a job `afterok` on training):
   - `final` when its validation loss is below step 0's and at most 10% above the lowest logged value;
   - otherwise the latest `epochK` whose last logged validation loss at or before its step is below step 0's;
   - otherwise nothing is evaluated: the chain stops, and the result is recorded.
   - The chosen dir is copied to `trees/e4b-sw-l8/adapters/l8/` (gitignored).

## Part 2: evaluation on fold B

### Arms

| Arm | Tree | Cohort | Draws | Run ids |
|---|---|---|---|---|
| smoke (not read) | `trees/e4b-sw-l8` | `runs/_cohorts/smoke-te.txt` (2), concurrency 2 | 1 | `S-008-e4b-l8-smoke` |
| l8 | `trees/e4b-sw-l8` | `cohorts/lfold-b.txt` (40) | 8 | `L-008-e4b-l8-ada-d1..d8` |
| ctl | `trees/e4b-r020-retry` (shipping, no adapter) | `cohorts/lfold-b.txt` (40) | 8 | `L-008-e4b-ctl-ada-d1..d8` |
| l8 on fold A (reported, not read) | `trees/e4b-sw-l8` | `cohorts/lfold-a.txt` (39) | 2 | `L-008-e4b-l8a-ada-d1..d2` |

- `trees/e4b-sw-l8` is `trees/e4b-r020-retry` with `adapter: l8` in `sub_agents/solver.yaml` and an `agent.yaml`
  comment. `diff -r` shows only those two lines. The root serves the base model.
- The control is the shipping tree without LoRA, because that is what the adapter would replace. LoRA serving
  costs some decode speed, so the wall ratio is read with that in mind. Fresh control draws run in the same queue
  period instead of R-021's old draws (the R-033 lesson).
- Flags, every eval job: `sbatch --parsable -J heng_e4b slurm/eval.sbatch <run> <tree> <cohort> --concurrency 4
  --py313 env/py313-scorer/bin/python3.13 --task-envs env/taskenvs`, 1 Ada GPU, 4 CPUs, 64G, time scale 1.0.
- **Order and chain.** All jobs are queued at once:
  - pick `afterok` training; smoke `afterok` pick;
  - l8 d1 and ctl d1-d8 `afterok` smoke;
  - l8 d2-d8 and l8a d1-d2 held, released by the d1 gate.
- Cost: 18 draws × about 0.2 Ada GPU-h plus the smoke, about 4 GPU-h; with training, about 6-8.

### Readings (written before any job of this round runs)

1. **Smoke gate** (`tools/gate_actor.sh` on the smoke, `tools/d1_gate.py` gates `status_SUCCESS<2
   solve_calls_gt3>=1 root_calls_max>9 adapter_steps<=0`). A kill cancels every eval job of the round unread; a
   failed smoke is fixed once, logged here, and re-run.
2. **Served check, every draw, before any reading.** A draw is read only if it has 40 rows (39 for l8a) and every
   task is served (some agent step has prompt tokens). A draw that fails is re-run once under the same name with an
   `r` suffix, logged here first.
3. **Draw-1 kill gate on l8 d1** (`tools/gate_actor.sh`; a kill cancels l8 d2-d8, l8a and the unfinished ctl
   draws, unread): `resolved<=2 empty>=11 timecap>=6 mean_wall>250 callcap>=18 retry_miss>=4 solve_calls_gt3>=5`.
   All 12 R-021 retry draws restricted to fold B pass every bar (resolved 4-7, empty 0-7, timecap 0-2, mean wall
   128-161 s, callcap 5-10). `retry_miss` (0-2) and `solve_calls_gt3` (0-4) were checked on the full 79-task draws,
   which bound the fold-B counts; a first `solve_calls_gt3>=3` was raised to 5 before this file was committed.
4. **Decision.** `tools/paired_boot.py --arm` l8 ×8 `--base` ctl ×8 on the 40 fold-B tasks; solves per draw, 90% CI
   over tasks. Wall ratio = l8 mean task wall / ctl mean task wall.
   - **Promote:** the point estimate is +1.0 or more, the CI lower bound is above 0, and the wall ratio is 1.5 or
     less. Next: the user decides on an L4 Kaggle run (L4/L5); the adapter would ship inside the E4B zip.
   - **Extend:** a point estimate of +0.5 or more without promote extends once, by 8 more draws per arm (d9-d16,
     interleaved). The same rule is then applied to 16 and 16; no further extension.
   - **Harm:** a point estimate of −1.0 or less. The self-distillation line closes.
   - **Not kept:** anything else.
5. **Mechanism (reported for every outcome).** Per arm, per draw: tool calls per task, `callcap`, empty patches,
   time caps, mean task wall; `tools/retry_counts.py` (first-attempt empty, rescued, retry_miss, `solve_calls_gt3`);
   `tools/argloss_counts.py` (edit_file lost / ok / failed); `adapter_steps`.
6. **Fold A (reported, not read).** l8a ×2 resolved per draw on the 39 training-fold tasks, beside the R-021 retry
   draws restricted to fold A. Higher there and flat on fold B means the adapter learned the training tasks and did
   not transfer.

**Comparator, for scale (not a reading).** R-021 retry restricted to fold B: 5.17 per draw (12 draws, sd 1.19),
mean task wall 145.1 s. R-021 ctl (one solve): 4.62.

**Blind guess (not a reading).** Smoke and d1 pass: 75%. Promote 10%, extend 20%, not kept 55%, harm 15%. Wall
ratio 1.1-1.4.

## Queued

Submitted 2026-11-22, all at once, after the commit that adds this file:
- training 60874 (`heng_lora`, 10 h limit); pick 60875 (`afterok` 60874); smoke 60876 (`afterok` 60875).
- l8 d1 60877 and ctl d1-d8 60878-60885, `afterok` 60876.
- held: l8 d2-d8 60886-60892, l8a d1-d2 60893-60894.
- Gate actors: smoke (kill cancels 60877-60894); d1 on 60877 (kill cancels 60886-60894 and the ctl draws; pass
  releases 60886-60894).

## Results, part 1 (2026-11-22; training readings and smoke applied as written)

- **Training reading 1 (health): pass.** Job 60874 COMPLETED in 1:33 (5,532 s of training), 90 steps; loss and grad
  norm finite throughout; `epoch1`, `epoch2` and `final` written. 119 train rows, 16 val rows, as the dry run.
- **Training reading 2 (choice): `final`.** Validation loss 0.4573 at step 0, lowest 0.4296 (step 22), final 0.4432
  (10 values). The final is below step 0 and within 10% of the lowest. The loss fell over the first epoch and rose
  slowly over epochs 2-3, so the last two epochs overfit the 20 training tasks somewhat. The pick job (60875) copied
  `final` to `trees/e4b-sw-l8/adapters/l8/`.
- **Smoke gate: pass** (job 60876): 2 rows, 2 SUCCESS, root calls max 4, no task with more than 3 solve calls,
  adapter steps 12. Not read for solves.
- The l8 d1 draw and the control draws are running; the d1 gate actor waits on 60877.
