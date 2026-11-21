# L-006 / L-007: adapters that learn to stop after submit_patch (pre-registration)

Written 2026-11-21, before either training job is submitted. L-006 is the 31B arm, L-007 the E4B arm. Counts only; the
data and adapters live under `/data/mmyatmau/gemma4-lora/` and never enter git (plan.md:52). L-003 Part 2 (a1 d1-d8)
is still running and is read as written; nothing here changes it.

## Why: both adapters so far keep calling submit_patch

Every trained row from `trace_to_sft.py` ends at the first `submit_patch` response, so no row shows the model
stopping (L-001 data design). In the base runs the model stops by itself right after submitting: in
`L-003-e4b-full0-tu127-d1` and `R-015-31b-base-te-d6`, 83 of the 101 traces that submit have a text turn with no tool
call as the next agent step.

The served adapters, from their d1 traces (tool-call counts only):

| Run | Tasks that submit | submit_patch calls | Calls per submitting task | Median identical repeats per task |
|---|---|---|---|---|
| `L-003-e4b-full0-tu127-d1` (zero adapter) | 39 / 40 | 44 | 1.1 | 0 |
| `L-003-e4b-a1e1-tu127-d1` (a1, epoch 1) | 37 / 40 | 833 | 22.5 | 33 |
| `R-015-31b-base-te-d6` (31B base) | 62 / 79 | 127 | 2.0 | 1 |
| `L-005-31b-l5-d1` (31B l5) | 29 / 40 | 197 | 6.8 | 1 |

- a1e1 over all 8 fold-B draws: the 28-call cap in 294 of 320 task-draws (full0 2 of 320); 147 runs end at the
  80-turn budget; empty patches 23.1 per draw (full0 5.8); mean task wall 1478 s (full0 720 s).
- L-005 d1 was killed for wall (ratio 1.155, time caps 14 against base 3-11).

## The change (one change per arm)

- `tools/lora/add_stop_turn.py` appends one assistant message with no tool call to each `complete` row: the text of
  the trace's first `final`/`text` agent step after the first `submit_patch` response, when no tool call comes
  between them. Rows without such a step are left unchanged. All other messages are byte-identical.
- `tools/lora/train_lora.py` accepts that message. It trains what the chat template renders after the turn's last
  `<tool_response|>` through the `<turn|>` that ends the turn (eos 106, a vLLM stop id). It trains the template's
  rendering, because the template rewrites a few stored texts. Rows without a closing message encode exactly as
  before. Checks, on the 31B L-005 data:
  - The old file still encodes 75 rows (67 train, 8 validation), as in L-005.
  - The stop file encodes 74. Rendering with the closing message leaves every earlier turn unchanged (66 of 66).
  - 64 stop spans end at `<turn|>` with no tool markup, and 62 of them equal the stored text.
- Data:
  - `31b-fast-stop-lfold-a.jsonl` (sha256 prefix `1842fd2976611869`): L-005's 76 rows, 66 with a stop turn, 10
    unchanged (tools after submit).
  - `31b-all-stop-lfold-a.jsonl` (sha256 prefix `889aeb52e74f1b19`): D2's 254 rows, 117 with a stop turn, 23
    unchanged (tools after submit), 114 unchanged (not complete). The closing text has a median of about 800 chars.

## L-006: 31B l6

- **Training.** Exactly L-005's command and readings, with `--data .../31b-fast-stop-lfold-a.jsonl` and
  `--out /data/mmyatmau/gemma4-lora/adapters/L-006-f1`. Rank 16, alpha 32, lr 1e-4, 2 epochs, accumulation 2,
  warmup 5, seed 1, `--packed --val-tasks 1 --max-len 16384`, one Ada, 4 CPUs, 128G, `--time 6:00:00`.
  - Dry run: 74 encoded (2 span mismatches), 66 train, 8 validation.
  - Training readings 1-2 of L-005 apply unchanged.
- **Evaluation.** Tree `adapters/trees/31b-l6` = `trees/31b-base` plus `adapter: l6`.
  - Smoke `S-006-31b-l6-smoke`: reading 1 of L-005, with `l6`.
  - Then `L-006-31b-l6-d1..d8` on fold B with L-005's flags.
  - The control set, projection formula, draw-1 kill gates, decision (reading 3) and mechanism (reading 4) are
    L-005's, word for word, with the base control draws R-008 d1/d2, R-011 d3/d4, R-014 d5 and R-015 d6. The r_L4
    used is the one known when d1 finishes: 0.75 unless EXP-087 (H-001) has reported.
- **Added mechanism reading (reported, not a gate): stop.** submit_patch calls per submitting task on d1, against
  l5's 6.8 and base's 2.0. The fix **works** for the 31B if it is 3.0 or less.
- **Stated limit.** At r_L4 = 0.75 the draw-1 time gate needs W_a/W_b ≤ 0.997, and shipping needs ≤ 0.914. The Ada
  LoRA decode cost alone is about 1.08×, so l6 passes only if stopping cleanly makes it faster than the base per task.
  L-005 already showed named-to-edit 7 against 9.
- **Cost.** About 3.2 Ada GPU-h of training plus 1.1 per draw.

## L-007: E4B a2

- **Training.** Exactly L-003 Part 1's command and readings (D1 `synth-s1.jsonl:1500` + D2 with `--cap-per-task 8`,
  `--val-tasks 3`, lr 1e-4, warmup 10, 2 epochs, accumulation 8, rank 16, alpha 32, seed 1, `--device-map single`,
  system prompt from `runs/R-011-e4b-base-tu5-d1/traces/trace_fastapi_11355.json`), with D2 =
  `31b-all-stop-lfold-a.jsonl` and `--out /data/mmyatmau/gemma4-lora/adapters/L-007-a2`.
  - Dry run: 1500 D1 + 114 D2 encoded (a1: 1500 + 116), 1601 train, 13 validation, 0.841M trained tokens (a1
    0.842M).
  - L-003 training readings 1-2 apply unchanged.
- **Hardware: one RTX 6000 Ada, not Turing** (`--constraint=RTX6000ADA --gpus=1 --cpus-per-task=4 --mem=64G
  --time 12:00:00`). The Turing node is serving a1 d1-d8. This is a second difference from a1, besides the data:
  bf16 kernels differ between GPUs. Recorded as a limit; it is not expected to matter beside the data change.
- **Evaluation.** `adapters/trees/e4b-a2` = `e4b-full0` with `adapter: a2`.
  - Smoke `S-007-e4b-a2-smoke` on Turing with L-003 Part 2 reading 1.
  - Then `L-007-e4b-a2-tu127-d1..d8` on fold B, with L-003 Part 2's flags, as Turing GPUs free.
  - Control: full0 d1-d8 of L-003 Part 2. Readings 2-5 of L-003 Part 2 apply word for word, with a2 in place of a1.
- **Draw-1 kill gate (new):** a2 d1 hits the 28-call cap in 20 or more of 40 tasks (a1e1: 294 of 320; full0: 2 of
  320). Then the fix did not work for the E4B, and d2-d8 do not run.
- **Added mechanism reading (reported): stop.** submit_patch calls per submitting task (a1e1 22.5, full0 1.1) and
  call-cap task-draws per draw.
- **Cost.** Training on Ada is unmeasured for the E4B. a1 took 16.3 h on Turing; Ada is expected to take a few
  hours. Then about 17 Turing GPU-h for 8 draws.

## What each outcome means

- Stop fixed, and resolves at least match the control: the stop turn becomes part of every later adapter's data,
  including the frozen-config retrains.
- Stop fixed but no gain: the earlier adapters' results were confounded by the loop, and the next lever is the data
  mix (D1 share, rank).
- Stop not fixed: the loop comes from elsewhere (for the E4B, possibly D1's 1500 read-then-edit rows, none of which
  submit). Diagnose before training anything else.

**Blind guess (not a reading).**
- l6 submit calls per submitting task: at most 3.0, 75%.
- l6 passes its draw-1 gates: 35%.
- a2 passes its call-cap gate: 70%.
- a2 helps on reading 2: 20%.
