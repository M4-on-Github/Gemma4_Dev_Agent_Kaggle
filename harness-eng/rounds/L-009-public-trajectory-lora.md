# L-009: adapters trained on public solved trajectories, 31B and E4B (pre-registration)

Written 2026-11-27, before any training job of this round is submitted. Counts only.
User instruction (2026-11-27): train both models on public solved trajectories.

## Why

Every harness-side change since `31b-base` and the E4B retry tree read as a null or harm (R-037 to R-049 so far).
36 of 79 cdev2 tasks are never solved by the 31B in any design. The adapters so far (L-003 to L-008) were trained on
our own models' solves, which cannot teach what the model does not already do. This round trains on a stronger
teacher's solves (D3 in `rounds/L-001-lora-data-desk.md`).

## Data

- **Source.** Hugging Face `SWE-bench/SWE-smith-trajectories`, split `tool` (MIT licence; 24,100 trajectories of an
  agent driven by two Claude Sonnet versions on synthetic bugs in public Python repositories; 9,427 resolved).
  Downloaded 2026-11-27 to `/data/mmyatmau/gemma4-lora/data/d3/` (1.08 GB), on the user's instruction.
- **Conversion.** `tools/lora/smith_to_sft.py` (this commit): resolved trajectories with 4 to 24 mapped tool calls
  and at least one edit; the source agent's shell, view, replace, create and submit actions are mapped onto
  `run_command`, `read_file`, `edit_file`, `write_file` and `submit_patch`, with tool responses rebuilt in the
  harness's JSON shapes and the harness's own task prompt. Trajectories with an unmapped action or an abbreviated
  long-file view are dropped. The two repositories of cdev2-79 are excluded. At most 40 rows per repository.
  - 31B layout: 1,948 rows over 107 repositories, median 14 calls.
  - E4B solver layout (the `solve` sub-agent's prompt, five tools, closing text turn): 1,893 rows, median 12 calls.
- **Loss.** `--default-train call`: only the tool calls and the closing turn are trained. The teacher's text before
  each call stays in the context, cut to 400 characters, and is not trained.
- **Known gaps.** No workspace tree in the task prompt; edit diffs are rebuilt from the two strings without file
  line numbers; a command's exit code is always 0; the source bugs are synthetic.

## Training

| Adapter | Model | Rows | Tokens (trained) | Settings | Est. cost |
|---|---|---|---|---|---|
| `L-009-s31` | 31B (`--packed`) | 400 (dry run on 600: 567 train, 22 val, 5.26M tokens, median 8,786) | about 3.5M (0.6M) | rank 16, alpha 32, lr 1e-4, 1 epoch, accumulation 4, warmup 10, max-len 14000 | about 7 Ada GPU-h |
| `L-009-se4` | E4B | 700 (dry run on 900: 871 train, 25 val, 7.68M tokens) | about 6.0M (1.0M) | same, `--system-from-row`, five tools | about 6-8 Ada GPU-h |

**Training readings.** (1) The job ends with `final/` written and no error. (2) Validation loss at the end is below
its value at step 0. An adapter that fails either is not evaluated.

## Evaluation

Pre-registered in this file before any evaluation job is submitted, once the adapters exist: full cdev2-79 (no
task of it is in the training data), against kfctl x8 for the 31B and rcheck x8 for the E4B, with the L-005 serving
projection for the 31B's time.

**Blind guess.** Either adapter beats its control by 1.5 or more: 15% each. The 31B adapter fits the time budget
without a lower time cap: 25%.
