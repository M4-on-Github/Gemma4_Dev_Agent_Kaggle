# L-004: 31B LoRA training probe on one Ada (pre-registration)

Written 2026-11-20, before any job of this round is submitted. Counts and losses only; samples stay under
`/data/mmyatmau/gemma4-lora/` (plan.md:52). The user asked for this probe ("do both on the adas", 2026-11-20);
the other Ada slot goes to the next 31B orchestration round, R-015.

## Question

Can `tools/lora/train_lora.py` train a 31B LoRA on one RTX 6000 Ada (48 GB, sm89, the L4's generation)? How
many ms per token does it take?

The L-002 path does not fit. It loads the checkpoint dequantized to bf16 on the GPU, which is about 62 GB for the
31B. compressed-tensors 0.15 has no packed forward any more: `CompressedLinear.from_linear` raises "no longer
supported".

## Trainer change: `--packed` (this commit)

- The model loads dequantized on the **CPU**. The job asks for 128G of host memory for that, against the usual
  64G.
- Each served LoRA target (q/k/v/o/gate/up/down of the text layers) is replaced by a `Packed` module.
  - It holds the checkpoint's own `weight_packed` (int32, 8 values per word) and `weight_scale` (bf16, one per 32
    inputs) on the GPU.
  - It rebuilds the bf16 weight inside its forward, with the library's unpack order and offset 8.
  - Under gradient checkpointing, the bf16 weight exists for one decoder layer at a time.
- **Exactness check, in every `--packed` run.** In the first and last layer, every `Packed` weight must equal the
  library's CPU dequantization bit for bit, or the run exits. No bf16 reference of the whole 31B fits on one GPU,
  so this per-module check replaces L-002's whole-model reference.
- The rest of the text path goes to the GPU: embeddings (tied to `lm_head`), norms, and the 192 unquantized
  modules the text path uses. The vision tower stays on the CPU.
- LoRA, the chunked attention, the chunked head loss and the adapter layout are unchanged from L-002/L-003. The
  E4B path without `--packed` is unchanged, apart from a guard: the 31B has no per-layer embedding table.

## Setup

- `slurm/lora_train.sbatch` with `--constraint=RTX6000ADA --gpus=1 --cpus-per-task=4 --mem=128G`.
- Model: `models/gemma-4-31b-it-qat-w4a16-ct`. LoRA rank 16, alpha 32 on every served q/k/v/o/gate/up/down target.
- System prompt: the `system_instruction` of an R-014 31B base trace (`runs/R-014-31b-base-te-d5`). Tools: the six
  served declarations.
- Data:
  - P1 uses D2 `31b-all-lfold-a.jsonl` (the 31B's own resolved trajectories on fold A, at most 8 per task) at
    `--max-len 16384`, so that its longest row is the longest D2 row.
  - P3b uses D1 `synth-s1.jsonl`.

## Jobs, in order (each runs only if the one before it gives a reading)

1. **P1, load check** (`--packed --load-check`): load, pack, check, then one forward and backward on the longest
   row. `--time 2:00:00`.
2. **P1b**: the same at `--max-len 8192`. Runs only if P1 runs out of GPU memory on the longest row.
3. **P3b, memorization**: the first 8 D1 rows after the seeded shuffle, 16 epochs, accumulation 1 (128 steps), lr
   2e-4, warmup 10, `--val-tasks 0`, as in L-002's P3b. Output goes to
   `/data/mmyatmau/gemma4-lora/adapters/L-004-p3b/` and is never served. `--time 6:00:00`.

**Budget.** Under 6 Ada GPU-h for the round. CPU loading takes an unknown share of each job's wall time, and it is
recorded.

## Readings (written before any job runs)

1. **Load.**
   - Passes if `pack_exact` equals `pack_probe_modules`, `wrapped` equals `served_targets` with `missing_in_model`
     at 0, and the longest row's loss and grad norm are finite.
   - The chunked-vs-stock check on one 2k-4k row must have an abs diff of at most 1e-3. Both sides use the packed
     weights, so this checks the attention path only.
   - Record: GPU memory after load, peak on the longest row, step seconds, and the job's load time.
   - Fails if P1 and P1b both run out of memory.
2. **Learns** (P3b). Passes if the mean loss of the last 16 steps is at most 0.25x the mean of the first 16, with
   no non-finite value.
3. **Speed.** Seconds per step and ms per token in P3b (about 2.5k tokens per row), and on P1's longest row.

## Decisions

- **Readings 1 and 2 pass.** The first 31B adapter gets its own pre-registration. It states:
  - the data, sized so that one epoch fits one Ada job at reading 3's ms per token;
  - the evaluation cohort and arms;
  - the serving cost below.
- **Reading 1 fails for memory.** Record the peak. The next option is two Adas with `--device-map auto` and no
  `--packed`, which takes both Ada slots, so it is the user's call.
- **Reading 1 fails on exactness.** It is a trainer bug: fix it and re-run P1. Nothing trains on an inexact path.
- **Reading 2 fails while reading 1 passes.** Look for a packed-path bug (dequantization under checkpoint
  recompute, or the gradient through `Packed`) before anything else.

## Serving cost, stated now (not a reading of this round)

- The 31B base projects to 10.04 h on the Kaggle run.
- LoRA on costs 0.916x decode on Ada (R-013). The L4 ratio for the 31B is not measured; EXP-047 measured 0.75x for
  the E4B on L4.
- If the 31B task wall time is decode-bound, 10.04 / 0.916 is about 10.96 h, and 10.04 / 0.75 is about 13.4 h. The
  shipped `max_time_minutes` caps each task, so the risk is fewer resolves inside the cap, not a timeout. A 31B
  adapter therefore has to buy more resolves than it loses to slower decode.
- Only an L4 measurement (S6, with the user's OK) settles this. The first 31B adapter round says how it is
  measured.

## Results

(appended after the jobs finish)
