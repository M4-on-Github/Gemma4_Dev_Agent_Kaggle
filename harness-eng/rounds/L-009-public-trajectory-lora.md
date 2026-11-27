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

## Training results

- **Deviation (31B).** The first 31B job (68279) ran out of GPU memory after 18 minutes: a cancelled evaluation job
  had not yet released the same GPU. Resubmitted unchanged as 68281.
- **`L-009-se4` (E4B, job 68280, 1 h 40 min).** 676 train rows, 22 validation rows, 169 steps. Training reading 1:
  `final/` written, no error. Reading 2: validation loss 0.3185 at step 0, 0.1457 at the end. Both pass.

## E4B evaluation (pre-registered 2026-11-27, before any evaluation job)

- **Arm.** `trees/e4b-sw-s9` = `trees/e4b-r041-retry-check` (the R-041 tree, the current E4B candidate layout) with
  `adapter: s9` on the solver; the root and the check agent stay on the base weights. The adapter files are copied
  to `trees/e4b-sw-s9/adapters/s9/` (gitignored).
- **Control.** `R-041-e4b-rcheck-d1..d8` (8.12 per draw, mean task wall 149.2 s), reused. They ran two days earlier
  without LoRA serving, so wall is compared with that in mind.
- **Runs.** Smoke on `runs/_cohorts/smoke-te.txt`; then `L-009-e4b-s9-d1..d4` on `cohorts/cdev2-79.txt`,
  concurrency 4, flags as R-041. No cdev2 task or repository is in the training data.
- **Readings.**
  1. Smoke: both tasks served, no engine error, the solver's steps name the adapter.
  2. Served check per draw: 79 rows, all served; one re-run with an `r` suffix.
  3. Draw-1 kill gate: 25 or more empty patches, or mean task wall above 300 s. A kill cancels the rest unread.
  4. Extension: d5-d8 only if d1-d4 read +0.5 or more against rcheck x8.
  5. Decision at 8 draws (`tools/paired_boot.py` against rcheck x8): **promote** at +1.5 or more with CI lower bound
     above -0.5 and mean task wall 300 s or less; **harm** at -1.5 or less; **not kept** otherwise.
  6. Reported: empty patches, time-cap tasks, mean wall, tool calls per task, patch resolve rate.
