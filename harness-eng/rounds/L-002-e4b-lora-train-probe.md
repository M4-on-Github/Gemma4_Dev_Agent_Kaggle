# L-002: E4B LoRA training probe on the Turing lane (pre-registration)

Written 2026-11-20, before any job of this round is submitted. Counts and losses only.

## Question

Can `tools/lora/train_lora.py` train an E4B LoRA on the served int4 checkpoint dequantized to bf16, on
pleiades-1-10's Quadro RTX 6000 (Turing, 24 GB, no native bf16 matrix units)? How long does a step take at the
lengths the L-001 data has (median 2378 tokens, p90 3282, max 16359 over the 1616 encoded rows)?

The two Ada slots stay with the R-014 31B draws. If Turing cannot train, the first adapter round has to wait for
an Ada slot, and that is the user's call.

## Setup

- Trainer: `tools/lora/train_lora.py` at the commit that adds this file. Job script: `slurm/lora_train.sbatch`,
  4 CPUs and 64G, on pleiades-1-10 after `squeue -w pleiades-1-10`.
- Model: `models/gemma-4-e4b-it-qat-w4a16-ct`. LoRA rank 16, alpha 32 on every q/k/v/o/gate/up/down projection
  of the text layers that the served checkpoint has (R-013's `full_zero` set).
- System prompt: the `system_instruction` of an R-011 E4B base trace (the base config; the frozen config is not
  chosen yet). Tools: the six served declarations.
- Data: D1 `synth-s1.jsonl` (first 1500 after the seeded shuffle) and D2 `31b-all-lfold-a.jsonl` with at most 8
  rows per task. The probe does not use its losses for any decision about the data.

## Jobs, in order (each runs only if the one before it gives a reading)

1. **P1, load check, 1 GPU** (`--load-check --device-map single`): load, wrap, then one forward and backward on
   the longest training row.
2. **P2, load check, 2 GPUs** (`--device-map auto`). Runs only if P1 fails for memory.
3. **P3, overfit sanity**: 64 D1 rows, 2 epochs, accumulation 1 (128 steps), lr 2e-4, on P1's or P2's GPU count.
   Output goes under `/data/mmyatmau/gemma4-lora/adapters/L-002-p3/` and is never served.

Budget: under 1.5 GPU-h in total on Turing, none on Ada.

## Readings (written before any job runs)

1. **Load.** P1 or P2 passes if the model loads with every served target wrapped as a dequantized `nn.Linear`
   (`missing_in_model` = 0, `wrapped` = `served_targets`), and the loss on the longest row is finite. Record
   `bf16_supported`, the GPU memory after loading, the peak, and the step seconds.
2. **Learns.** P3 passes if the mean loss of its last 16 steps is at most half the mean of its first 16 steps,
   with no non-finite loss or gradient norm.
3. **Speed.** Record seconds per step at accumulation 1 for P3 (D1 rows, median about 1.5k tokens) and for P1's
   longest row. Projection for a training round: the steps of the planned data mix times the per-token time.

## Decisions

- Readings 1 and 2 pass and the projected epoch over the L-001 mix (about 5.3M tokens) fits in 12 h on one or
  two Turing GPUs: the first E4B adapter round trains on pleiades-1-10. It gets its own pre-registration (data
  mix, epochs, and the fold-B evaluation).
- Reading 1 fails on Turing (no bf16 path, or out of memory on two GPUs): record why. The first adapter round
  waits for an Ada slot, after asking the user.
- Reading 2 fails while reading 1 passes: the trainer has a bug (mask, scaling or optimizer). Fix it and re-run
  P3 only.

## Results

### P1, job 59861 (pleiades-1-10, 1 Quadro RTX 6000, 41 s): failed, out of memory in the trainer's loss

- Load passes: `wrapped` 258 = `served_targets` 258, `missing_in_model` 0 (q 42, k 24, v 24, o 42, gate 42,
  up 42, down 42), 34.9M LoRA parameters. `bf16_supported` is true on Turing. GPU memory after loading:
  15.15 GiB of 23.46.
- The forward on the longest row (16359 tokens) ran out of memory allocating 7.98 GiB.
  - *Corrected 2026-11-20 after the second run:* the allocation was the attention scores in
    `scaled_dot_product_attention` (traceback at `modeling_gemma4.py:1282`), not the logits. The first reading
    named the full-vocabulary logits because their size is also 7.98 GiB (16359 x 262144 x 2 bytes, against
    8 heads x 16359^2 x 4 bytes). The logit change below is still needed: the logits would have run out of
    memory next.
- **Deviation, recorded before the re-run.** This is the trainer's memory use, not the model's, so P2 (two
  GPUs) is not the right next job. The fix is in `train_lora.py`:
  - run the decoder alone (`model.model`);
  - apply `lm_head`, the final logit softcap and the cross-entropy only at the trained positions, in checkpointed
    chunks of 1024;
  - load with `attn_implementation="sdpa"`.
  P1 is re-run once at the commit that records this. Readings and decisions are unchanged.

### P1 re-run, job 59862 (41 s): failed again, out of memory in attention

- Same load readings as 59861. Same 7.98 GiB allocation, inside `scaled_dot_product_attention` in a
  checkpointed decoder layer. `attn_implementation="sdpa"` falls back to the math kernel here: the fused kernels
  need sm80 for bf16 (Turing is sm75), and the global layers' head_dim of 512 is over their limit of 256. The
  math kernel builds the whole 8 x 16359 x 16359 score matrix.
- **Second deviation, recorded before the next run.** `train_lora.py` registers a query-chunked attention under
  the name `sdpa`:
  - chunks of 1024 queries, each checkpointed, with the same SDPA masks;
  - rows of at most 1024 tokens still go through stock SDPA.
  `--load-check` now first compares the chunked and stock losses on one 2k-4k row, without gradients. P1 runs
  once more at the commit that records this. Readings and decisions are unchanged.

### P1 third run, job 59863 (1 min 29 s): attention fixed, out of memory in the head

- The chunked attention matches stock SDPA on a 2905-token row: loss 0.18217 both, abs diff 0.0.
- On the 16359-token row it ran out of memory allocating 1.00 GiB: the fp32 logits of one 1024-position head
  chunk (1024 x 262144 x 4 bytes), with 22.05 GiB already allocated.
- Of the 15.15 GiB resident after loading:
  - 5.25 GiB is the per-layer embedding table, which training only looks rows up in;
  - 0.90 GiB is the audio and vision towers, which text input never calls.
- **Third deviation, recorded before the next run.** `train_lora.py` moves the per-layer table and the towers to
  the CPU after wrapping. It computes `per_layer_inputs` there and passes them to `Gemma4Model`, which is what
  the model computes itself for text-only input.
  - `--load-check` now takes its reference loss before the move, with everything on the GPU and stock SDPA.
    It compares that against the new path.
  - P1 runs once more. Readings and decisions are unchanged.

### P1 fourth run, job 59864 (47 s): offload works, wrong call

- GPU memory after the move: 9.02 GiB (from 15.15).
- `Gemma4Model.forward` rejects `per_layer_inputs` together with `input_ids`. The trainer now passes
  `inputs_embeds = get_input_embeddings()(ids)` with them. That is the same embedding the model computes from
  `input_ids` when the input is text-only. The reference check stands. P1 runs once more.

### P1 fifth run, job 59866 (3 min 20 s): passes reading 1

| Reading | Value |
|---|---|
| wrapped / served targets / missing | 258 / 258 / 0 |
| `bf16_supported` | true |
| GPU memory after load / after moving the per-layer table and towers to CPU | 15.15 / 9.02 GiB |
| New path vs all-GPU stock-SDPA reference, 2905-token row | 0.18217 vs 0.18217 (abs diff 0.0) |
| Longest row: tokens / loss / grad norm | 16359 / 0.5731 / 0.4868 (finite) |
| Peak GPU memory, longest row | 17.95 of 23.46 GiB |
| Step time, longest row (first step, forward + backward) | 149.0 s |

P2 does not run, since one GPU suffices. P3 runs next on one GPU, as pre-registered.

### P3, job 59867 (23 min 53 s): **fails reading 2 as written**

| Reading | Value |
|---|---|
| Steps / non-finite loss or grad norm | 128 / 0 |
| Mean loss, first 16 steps / last 16 steps | 0.1366 / 0.0831 (ratio 0.61; the bar was <= 0.5) |
| Speed (reading 3) | 10.94 s per step at 2508 tokens per step: 4.36 ms per token |

Bug search, done before any re-run. None found:

- **Same rows, epoch 1 against epoch 2.** All 64 rows have distinct token counts, so each epoch-1 step pairs
  with its epoch-2 step. Mean loss is 0.1096 against 0.0830 (ratio 0.757), lower on 61 of 64 rows.
- **Optimizer and schedule.**
  - lr follows the warmup and cosine as set: 4e-5 at step 1, 1.9e-4 at step 17, 7e-6 at step 113.
  - grad norm falls from 1.47 to 0.07-0.32.
- **Mask and loss.** The mask was checked by hand in L-001's dry run. The new loss path equals the stock one
  exactly (P1).

Reading: the trainer learns. The bar was set without knowing the starting loss: D1's trained tokens are tool calls
that copy from a file the model has just read, and the base model already scores them at 0.137 nats per token.
Two passes per row at a decaying lr do not halve that. This is recorded as a failure of reading 2. The bar is not
re-read after the fact.

### P3b addendum (pre-registered here, before the job is submitted)

The decision for a failed reading 2 is "fix the trainer, re-run P3", but no bug was found, so re-running P3
unchanged would tell nothing. P3b is a stricter test for a trainer bug: memorization.

- **Setup.** The first 8 D1 rows after the seeded shuffle, 16 epochs, accumulation 1 (128 steps), lr 2e-4,
  warmup 10. Otherwise the same as P3. Output goes to `/data/mmyatmau/gemma4-lora/adapters/L-002-p3b/` and is
  never served.
- **Reading 2b.**
  - Passes if the mean of the last 16 steps is at most 0.25x the mean of the first 16, with no non-finite value.
  - If it passes, the trainer has no learning bug. P3's miss is attributed to too few passes per row, and the
    first adapter round sets its lr and epochs in its own pre-registration.
  - If it fails, there is a trainer bug: stop and look again.
- **Budget.** About 0.4 GPU-h. The round total stays under the 1.5 GPU-h budget (P1 runs 0.1, P3 0.4).
