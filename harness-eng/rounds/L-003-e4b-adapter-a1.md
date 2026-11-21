# L-003: first E4B adapter (a1), D1 + D2 fold A (pre-registration)

Written 2026-11-20, before the training job is submitted. Counts and losses only; samples stay under
`/data/mmyatmau/gemma4-lora/` (plan.md:52).

## Question

Does an E4B LoRA trained on D1 (synthetic exact-copy edits from the CPython stdlib, PSF-2.0) plus D2 fold A
(31B -> E4B distillation from our resolved 31B trajectories on the 39 `lfold-a` tasks) raise E4B resolves on the
40 unseen `lfold-b` tasks? Does it lower the failed-edit and not-found rates that D1 targets?

This is a probe of whether LoRA helps the E4B at all. It trains on the **base** E4B config's system prompt. The
frozen config (about Nov 26, possibly with R-014's applier) is not chosen yet. A shipped adapter is trained again
on the frozen config.

## Part 1: training (this section is fixed now)

- **Trainer.** `tools/lora/train_lora.py` at the commit that adds this file; L-002 passed it on one Turing GPU.
  - Job: `slurm/lora_train.sbatch`, 1 Quadro RTX 6000 on pleiades-1-10 after `squeue -w pleiades-1-10`,
    4 CPUs, 64G, `--time 20:00:00`.
- **Model and adapter.** `models/gemma-4-e4b-it-qat-w4a16-ct`. LoRA rank 16, alpha 32 on all 258 served
  q/k/v/o/gate/up/down targets (R-013's `full_zero` set).
- **Prompt and tools.** The system prompt is the `system_instruction` of the first R-011 E4B base trace, as in
  L-002. Tools are the six served declarations.
- **Data, exactly the L-001 mix that L-002 encoded.**
  - D1 `synth-s1.jsonl`: the first 1500 rows after the seeded shuffle.
  - D2 `31b-all-lfold-a.jsonl`: at most 8 rows per task.
  - 1603 train rows and 13 validation rows. The validation rows are 3 fold-A tasks held out of training.
  - 5.27M tokens, 0.84M of them trained.
- **Optimization.** lr 1e-4, warmup 10, cosine; 2 epochs; accumulation 8 (about 401 steps); clip 1.0; seed 1.
  - P3/P3b showed the trainer learns slowly at a decaying lr over a low starting loss. A second epoch is the
    standard remedy, and the run also saves `epoch1/`, so one job gives a 1-epoch and a 2-epoch adapter.
- **Output.** `/data/mmyatmau/gemma4-lora/adapters/L-003-a1/{epoch1,final}/`, in PEFT layout. It is never
  committed.
- **Budget.** About 13-17 Turing GPU-h at L-002's 4.36 ms per token (long D2 rows run up to 9 ms per token).
  None on Ada.

### Training readings

1. **Health.**
   - Pass: no non-finite loss or grad norm, the job completes, and both adapter dirs are written.
   - Record: steps, wall time, ms per token.
2. **Fit.** Validation loss (13 held-out rows) at step 0 and at the end.
   - The end value must be below step 0.
   - If it is above step 0, or rises by more than 10% from its minimum by the end, the adapter whose
     validation loss is lower (`epoch1` or `final`) is the one evaluated. If both are above step 0, nothing is
     evaluated: record it and redesign.

## Part 2: evaluation on fold B (pre-registered 2026-11-20, before any evaluation job)

Written while a1 is at step 98 of 401. No fold-B draw with any adapter has run, and a1 has never been served.

### Arms

| Arm | Tree | Cohort | Draws | Run ids |
|---|---|---|---|---|
| full0 | `adapters/trees/e4b-full0` (R-013: base tree + rank-16 zero adapter `full_zero`) | `cohorts/lfold-b.txt` (40) | 8 | `L-003-e4b-full0-tu127-d1..d8` |
| smoke (not read) | `adapters/trees/e4b-a1` | `runs/_cohorts/smoke-te.txt` (2), concurrency 2 | 1 | `S-003-e4b-a1-smoke` |
| a1 | `adapters/trees/e4b-a1` | `cohorts/lfold-b.txt` | 8 | `L-003-e4b-a1-tu127-d1..d8` |

- **`e4b-a1`** is `e4b-full0` with `adapter: a1` and `adapters/a1/` holding the adapter that training reading 2
  selects (`final`, or `epoch1` under reading 2's rule). Nothing else in the tree changes. It is built after
  training ends and before the smoke.
- **Both arms serve with LoRA on.** R-013 measured the Turing LoRA cost as fixed and independent of adapter size,
  so the arms run at the same speed and differ only in the weights.
- **Flags**, every job: `sbatch -J heng_e4b_tu --constraint=QUADRORTX6000 -w pleiades-1-10 slurm/eval.sbatch <run>
  <tree> cohorts/lfold-b.txt --concurrency 4 --py313 env/py313-scorer/bin/python3.13 --task-envs env/taskenvs
  --time-scale 12.7`, at 4 CPUs and 64G, `HENG_SHIMS` off, with `squeue -w pleiades-1-10` checked first.
- **Order.** full0 d1-d7 start now on the 7 free GPUs and d8 starts when one frees. The a1 smoke, then a1 d1-d8,
  start after training readings 1-2. The arms are therefore not interleaved in time. This is a stated limit; the
  node is otherwise ours.

### Time scale: 12.7, a deviation from R-013's wording

R-013 says a later E4B adapter round sets its scale "from a base-with-`full_zero` draw". Here the `full_zero` draws
are themselves the comparison arm, so the scale has to be fixed before them. It is fixed from measured decode
rates:
- E4B base on this lane is scaled 5.0 (R-011).
- LoRA on costs 0.296× decode on Turing (R-013) and 0.75× on Kaggle L4 (EXP-047: 116.6 → 86.9 tok/s).
- 5.0 × 0.75 / 0.296 = **12.7**. This is the decode-bound upper value. Prefill and tool time slow less, so the
  real ratio lies between 5.0 and 12.7, and the caps here are, if anything, looser than Kaggle's.

The arms share the scale, so the comparison does not depend on it. The scale only changes how many task-draws reach
the 101.6-minute session cap. Recorded, not read: the full0 mean task wall against the R-011 base mean on the same
40 tasks, which is the measured Turing ratio. A shipped adapter's Kaggle time is measured on L4 (S6), not here.

### Readings

1. **Health.**
   - At most 2% of task-draws per arm have a status other than SUCCESS.
   - The a1 smoke passes when vLLM loads `a1` (`/v1/models` lists it), every model-named step in both traces names
     `a1`, and there is no engine error. If it fails, no a1 draw runs; the cause is recorded first.
2. **Decision.** Paired over the 40 fold-B tasks, using each task's resolve rate over 8 draws per arm. The
   statistic is the mean of a1 rate − full0 rate, times 40, so it is in solves per draw. The CI is a 90% bootstrap
   over the 40 tasks (10,000 resamples, seed 0).
   - **Helps:** the CI lower bound is above 0. The E4B LoRA direction is kept. Next is S6: the L4 speed measurement
     on Kaggle, run only with the user's OK. After that, the adapter is retrained on the frozen config.
   - **Extend:** a point estimate of +1.0 or more without the CI above 0 extends once, by 8 more draws per arm
     (d9-d16). The same rule is then applied to all 16 and 16, and there is no further extension.
   - **Harm:** a point estimate of −1.0 or less. Not kept; the data mix is redesigned before any new adapter.
   - **Not kept:** anything else.
3. **Mechanism** (reported for every outcome; it does not override reading 2).
   - Failed-edit task-draws and not-found task-draws per arm, counted by `tools/r014_gates.py applier` exactly as
     in R-014 reading 3: not-found, not-unique, no-op or malformed `edit_file`.
   - **Met** if the a1 failed-edit share is at least 10 points below full0's.
   - Also reported: empty patches, time-cap and call-cap task-draws per draw, and tool calls per task.
4. **Harm check** (reported): the a1 resolve rate on tasks that full0 resolves in at least 4 of 8 draws.
5. **Speed** (reported): a1/full0 mean task wall, expected near 1.0.

**Cost.** About 5-8 h per draw at 40 tasks and concurrency 4, so 16 draws are about 80-130 Turing GPU-h. That is
outside the Ada ledger. An extension doubles it.

**Blind guess (not a reading).** Helps 25%, extend 20%, not kept 40%, harm 15%. Failed-edit share: full0 about
55%, a1 about 45%.

## Part 3: the 1-epoch adapter as its own arm (pre-registered 2026-11-21T01:55Z)

Written while a1 is at step 198 of 401, before `epoch1/` is saved and before any adapter has been served. Parts 1
and 2 are unchanged. full0 d1-d7 are finished. Their counts have been looked at, so this part does not touch the
full0 arm or any rule that reads it. The user freed every GPU for the weekend (2026-11-20, Friday night), and 6
Turing GPUs are idle until a1 finishes (about 10:30Z).

**Why.** The shipped adapter is retrained on the frozen config at about Nov 26, and an epoch on Turing takes
about 8 h. Whether 1 epoch does as well as 2 decides how much of the last week that retrain uses. Training
reading 2 picks one adapter by validation loss only; this arm measures the other one too.

### Arm

| Arm | Tree | Cohort | Draws | Run ids |
|---|---|---|---|---|
| smoke (not read) | `adapters/trees/e4b-a1e1` | `runs/_cohorts/smoke-te.txt` (2), concurrency 2 | 1 | `S-003-e4b-a1e1-smoke` |
| a1e1 | `adapters/trees/e4b-a1e1` | `cohorts/lfold-b.txt` (40) | 8 | `L-003-e4b-a1e1-tu127-d1..d8` |

- **`e4b-a1e1`** is `e4b-full0` with `adapter: a1e1`, and `adapters/a1e1/` holds a copy of
  `/data/mmyatmau/gemma4-lora/adapters/L-003-a1/epoch1/`. Nothing else in the tree changes. `adapters/` is
  gitignored, so the weights never enter git.
- **Flags.** The same as Part 2: `--concurrency 4 --time-scale 12.7`, 4 CPUs, 64G, `HENG_SHIMS` off,
  `squeue -w pleiades-1-10` checked before each submit.
- **Order.** The smoke runs as soon as `epoch1/` exists, then d1-d8 on the free Turing GPUs. The a1 (final) arm
  of Part 2 still starts after training readings 1-2, so a1e1 is not interleaved with full0 or a1.
- **Blind until training reading 2.** Only health is checked on a1e1 runs before training reading 2 is applied
  and written here: status, the adapter name in the traces, engine errors. No a1e1 resolve count is opened before
  that.

### Readings

1. **Smoke and health.** The same as Part 2 reading 1, with `a1e1` in place of `a1`. If the smoke fails, no a1e1
   draw runs; the cause is recorded first.
2. **If training reading 2 selects `epoch1`.** The a1e1 draws are Part 2's a1 arm, and readings 2-5 of Part 2
   apply to them unchanged. The final adapter is then served only as a reported arm, if at all.
3. **If training reading 2 selects `final`** (its default). Part 2 is read on the a1 (final) draws exactly as
   written. a1e1 is reported, not read for keeping the E4B LoRA direction:
   - The paired statistic of Part 2 reading 2 (solves per draw, 90% bootstrap over the 40 tasks, seed 0), for
     a1e1 against full0 and for a1e1 against a1.
   - Part 2 readings 3-5 for a1e1.
4. **Epoch-count rule, for planning only.** It applies only if Part 2 keeps the direction (helps, or helps after
   the extension). The shipped retrain then uses **1 epoch** if the a1e1 point estimate against full0 is at least
   the kept arm's minus 0.5 solves per draw. Otherwise it uses **2**. It moves no claim. It picks a training length
   that the frozen-config retrain then has to earn again on its own evaluation.

**Cost.** 8 draws at about 2.1 h each (the full0 draws took 2.0-2.3 h), about 17 Turing GPU-h, plus the smoke.

**Blind guess (not a reading).** a1e1 against a1 (final): within 0.5 solves per draw, 60%; a1 better, 30%;
a1e1 better, 10%.

## Results

(appended after the jobs finish)

### Part 3 smoke (`S-003-e4b-a1e1-smoke`, job 59919, pleiades-1-10, 2026-11-21T02:07-02:25Z)

Reading 1 (Part 2 reading 1 with `a1e1`): **pass.** The resolve count was not read.

- 2 of 2 rows SUCCESS; no Traceback, EngineDead or CUDA error in the job log.
- Every model-named step in both traces names `a1e1` (80 of 80 in each).
- `/v1/models` was not printed by the runner, so the adapter check is indirect, and that is recorded here. The
  server is a `VllmServer` with `enable_lora=True` and the tree's adapter manifest (`tools/cluster_eval.py:210-217`).
  Per `harness-stack/reference/adapters.md`, only a server without LoRA falls through silently. With LoRA on, a
  request naming an unloaded model gets an error from vLLM, so 160 accepted `a1e1` requests mean the adapter was
  served.
- vLLM came up in 266.3 s. Decode probe: 50.3 tok/s on one stream, 95.7 tok/s on two.

a1e1 d1-d8 submitted to pleiades-1-10 after this entry.
