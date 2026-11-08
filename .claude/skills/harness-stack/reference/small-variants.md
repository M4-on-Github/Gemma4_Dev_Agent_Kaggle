# Running a small variant (E2B, E4B)

Recorded 2026-11-05 by the experimenter. Tags: [V] official file or our own measured run, [M] mirror, [I] inference.

## Names and how a submission declares one

- The scorer admits exactly four base models, all quantized: `gemma-4-31b-it-qat-w4a16-ct`, `gemma-4-12b-it-qat-w4a16-ct`, `gemma-4-e4b-it-qat-w4a16-ct`, `gemma-4-e2b-it-qat-w4a16-ct` [V] (`data/raw/HARNESS_README.md` §2 `model` field, §3.1 table, §3.2).
- A submission declares its model only through the `model:` key of each LlmAgent in `agent.yaml` and every sub-agent / agent_tool YAML. One unique base model per submission, sub-agents included; provider prefixes `openai/ google/ hosted_vllm/ custom/` are stripped first; a second model or an unlisted name raises `ParticipantVisibleError` [V] (HARNESS_README §3.2; host, kg-743063: "Every agent and subagent in your submission must use the same variant").
- The bf16 aliases `gemma-4-e2b-it`, `gemma-4-e4b-it`, `gemma-4-e2b`, `gemma-4-e4b` exist only in `adk_eval_core/budget/models.yaml` for local CLI runs; they are not allowed in a competition upload [V] (HARNESS_README §3.1 last row).
- `tools/submission_rules.py` admits 31B, E4B and E2B (`ALLOWED_MODEL_NAMES`; `SMALL_MODEL_NAMES` = the two prize-eligible ones). 12B is left out on purpose because it needs a vLLM flag the eval notebook does not pass (below).

## What differs for a small variant

- vLLM serving recipe: identical for E2B / E4B / 31B: TP 4, `max_model_len` 32768, `gpu_memory_utilization` 0.90, `tool_call_parser` and `reasoning_parser` `gemma4` [V] (HARNESS_README §3.1). The only model-specific flag in the scorer is `--hf-overrides '{"architectures": ["Gemma4ForCausalLM"], "model_type": "gemma4"}'` for **12B only** [V] (§3.1 `MODEL_VLLM_EXTRA_ARGS`; EXP-006 cmd argv: empty `extra_args` for e2b/e4b).
- Budgets, hardware, the 12 h limit and per-task caps: the same [V] (host 2026-10-11, kg-743063: "Yes, everything is the same"). Generation limits (`max_output_tokens` and `thinking_budget` up to 32,768) are not model-specific [V] (`swegemma/config.py build_submission_limits`).
- Model configs read by EXP-006 from `config.json` [V]: E4B 42 layers, 8 heads, 2 KV heads, sliding window 512, `max_position_embeddings` 131072; E2B 35 layers, 8 heads, 1 KV head, sliding window 512, 131072; both `Gemma4ForConditionalGeneration`, `compressed-tensors`. 31B: 60 layers, 16 KV heads, window 1024, 262144. The 32k serving window is inside every model's native context.
- Boot and KV room on L4x4 [V] (EXP-006): e2b booted in 245 s, max concurrency at 32k 67.2x; e4b 289 s, 45.6x; 31B 377 s, 8.7x.
- Public BF16 E4B weights for training [V] (`kaggle models get google/gemma-4`, 2026-11-08; Apache 2.0): `transformers` instances `gemma-4-e4b-it-qat-q4_0-unquantized` v2 (15,914,702,139 bytes) and `gemma-4-e4b-it` v1 (16,024,808,340 bytes). In `model_sources` they are `google/gemma-4/transformers/<instance>/<version>`. The served `w4a16` checkpoint can also be decompressed to BF16 in transformers 5.13.1 with `run_compressed=False` (`quantizer_compressed_tensors.py:74-78`). `peft` is not in the wheelhouse; torch 2.10.0+cu128 and transformers 5.13.1 are (EXP-048 gate, G3). Even so, the L4x4 GPU kernel has a `peft` distribution, 0.19.1 (`importlib.metadata` after the wheelhouse install, EXP-054 v1 `env.json`, 2026-11-08) [V]. Whether it comes from the docker image or from elsewhere was not checked.
- Mounted in the kernel [V] (EXP-054 v1, 2026-11-08): with `model_sources` entry `google/gemma-4/transformers/gemma-4-e4b-it-qat-q4_0-unquantized/2`, the BF16 parent sits at `/kaggle/input/models/google/gemma-4/transformers/gemma-4-e4b-it-qat-q4_0-unquantized/2/config.json`, the same layout as the served `other/` instance.
- That kernel also reported: Python 3.12.13, standard library at `/usr/lib/python3.12`, 48 CPUs, 188.7 GiB RAM (184.4 GiB available), and 4 x 22,563 MiB GPUs. Boot 0 of the E4B with no adapter came up with a KV pool of 298,464 tokens, the same as in EXP-047 v2.
- Training a LoRA on the E4B in an L4x4 kernel [V] (EXP-054 v2, 2026-11-08):
  - Load the BF16 parent above with `Gemma4ForConditionalGeneration` in bf16, move the per-layer embedding table and the vision and audio parts to the CPU, freeze the base, and run one child under `torchrun` with 4 ranks.
  - Memory: 8.65 GiB per rank after the offload. With gradient checkpointing (non-reentrant), micro-batch 1 and rank 8 on `q_proj`/`o_proj` (84 modules, 3,325,952 parameters), one sequence of 6,695 tokens peaked at 11.98 GiB per rank of the 22,563 MiB GPUs.
  - Speed: 67 optimiser steps (accumulation 2, so 536 sequences of median 3,025 tokens) took 660 s. The model load and the child start add about 140 s.
  - The rank-8 adapter in the PEFT layout is 6,676,712 bytes of `.safetensors` plus a 645-byte `adapter_config.json`.
- Serving with one rank-8 adapter [V] (EXP-054 v2): the boot with the LoRA flags took 283.4 s and had a KV pool of 263,280 tokens (298,464 without, 0.88). Idle single-stream decode at 256 tokens: base 104.5 tok/s, adapter 86.9 tok/s (0.168 slower).
- Not verified by us: whether E2B / E4B emit thinking and gemma4 tool calls well under the harness (EXP-006 sent plain chat completions only); whether the chat template in the model directory differs from 31B's; per-call decode speed under an agent loop; whether `enable_lora=True` (our notebook's setting; the scorer sets it False when no adapters ship) changes anything for the small models. The first E2B smoke-8 answers the first and third.

## Steps for an E2B smoke-8

1. Build the candidate tree with a tool from a committed source (e.g. `experiments/EXP-027/candidate-v24-at-8/` with `model: gemma-4-e2b-it-qat-w4a16-ct` in `agent.yaml` as one anchored edit). `python tools/validate_submission.py <tree> --strict`: the model is accepted; the 8-min cap still trips the 18.00 h gate, so packing needs `--skip-budget-gate` and the EXP §2 must state the override.
2. Pack with `tools/pack_submission.py --src <tree> --out <zip> [--allow-warnings] [--skip-budget-gate]`; record the sha.
3. `python tools/build_notebook.py --embed <zip> --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set MODEL_NAME='"gemma-4-e2b-it-qat-w4a16-ct"' --out notebooks/expNNN_<arm>/kaggle_eval_l4x4.ipynb`. The vLLM cell takes the model from the zip's `agent.yaml`; `MODEL_NAME` is only a cross-check and may be left empty.
4. Copy `kernel-metadata.json` from `notebooks/exp028_armR/`, change `id` and `title`, and set `model_sources` to `["google/gemma-4/other/gemma-4-e2b-it-qat-w4a16-ct/2"]` (`build_notebook.py` never touches `model_sources`). The notebook asserts `/kaggle/input/models/google/gemma-4/other/<name>/2/config.json` exists before booting vLLM, so a wrong input fails in seconds, not after the boot.
5. Push as any other screen. Analysis is unchanged (`analyze_traces.py` is model-agnostic).
