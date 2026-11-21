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

### P1, job 59897 (pleiades-0-17, 1 RTX 6000 Ada, 5 min 36 s in total, load included)

| Reading | Value |
|---|---|
| Packed vs library dequantization, first and last layer | 13 of 13 modules bit-exact (max abs diff 0.0) |
| wrapped / served targets / missing | 410 / 410 / 0 (q 60, k 60, v 50, o 60, gate 60, up 60, down 60) |
| LoRA parameters | 122.4M |
| GPU memory after load | 18.43 GiB of 48 |
| Longest row: tokens / loss / grad norm | 16359 / 0.1918 / 0.4871 (finite) |
| Peak GPU memory, longest row | 40.41 GiB |
| Step time, longest row (first step, forward + backward) | 109.9 s (6.7 ms per token) |
| Chunked-vs-stock attention check | **did not run** (see below) |

- The D2 data under the 31B tokenizer: 103 train rows and 13 validation rows, 1.55M tokens (0.62M trained). Median
  length is 14253 tokens, p90 15775. Nine rows are over 16384.
- The job's whole wall time, CPU load included, was 336 s. Loading is not a cost that matters.
- **The chunked-vs-stock check did not run.** It needs a 2k-4k-token training row, and the D2 rows have none at the
  31B's lengths. Reading 1 asks for this check, so it is not yet met. L-002 passed the chunked attention on the
  E4B, but the 31B has 512-wide global heads and a 1024-token sliding window, so the check is not carried over.
- **Deviation, recorded before the next job.** P1c is P1 with D1 data (`synth-s1.jsonl:64`, which has 2k-4k rows)
  in place of D2, still with `--packed --load-check`. It gives the chunk check, plus a second packed load. P3b runs
  only if P1c's abs diff is at most 1e-3. The readings and decisions are unchanged.

### P1c (`L-004-p1c`, job 59898, pleiades-0-23, 2026-11-21T04:38-04:42Z)

- **Chunk check passes:** a 2,905-token D1 row gives loss 0.3568 chunked against 0.35715 stock, abs diff 0.000344
  (bar 1e-3). Reading 1 is now met in full.
- Second packed load: 13/13 probe modules exact (max abs diff 0.0); 410 wrapped of 410 served targets, 0 missing;
  18.43 GiB after load.
- Longest D1 row (3,315 tokens): loss 0.2469, grad norm 40.23 (finite), 17.2 s for the step, 24.45 GiB peak.
- Data: 64 D1 rows, all encoded; 160,522 tokens, 8,849 trained; median length 2,458.
- Job wall 221 s, CPU load included.
- P3b is submitted next, as written.

### P3b (`L-004-p3b`, job 59931, pleiades-0-23, 2026-11-21T04:48-05:22Z)

- **Reading 2, learns: passes.** Mean loss of the first 16 steps 0.159, last 16 steps 0.0117, ratio 0.074 (bar 0.25).
  No non-finite loss or grad norm in 128 steps (largest grad norm 155.5, early; last step 0.16).
- **Reading 3, speed.** 128 steps in 1,838 s of training: 14.4 s per step, 5.67 ms per token over 324,304 tokens
  (about 2.5k tokens per row). P1's longest row ran at 6.7 ms per token. Job wall 2,034 s, CPU load included.
- All three readings pass, so the packed 31B trainer is cleared for L-005. The P3b adapter is never served.
