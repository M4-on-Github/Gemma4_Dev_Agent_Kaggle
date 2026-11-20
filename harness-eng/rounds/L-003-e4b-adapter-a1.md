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

## Part 2: evaluation on fold B

Pre-registered in this file, in its own commit, **before any evaluation job** and before any adapter is served.
Nothing about fold-B outcomes is known when it is written. What it must fix:

- the arms:
  - `e4b-full0`: base tree plus the zero adapter, so both arms serve with LoRA on at the same speed;
  - `e4b-a1`: the same tree with the trained adapter;
- the draw count and the paired test;
- the `--time-scale`. R-013 says it is set from a base-with-`full_zero` draw, not from R-011's 5.0;
- the mechanism endpoints (failed-edit draws, not-found draws, empty patches);
- the decision readings.

## Results

(appended after the jobs finish)
