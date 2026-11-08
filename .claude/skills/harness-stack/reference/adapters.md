# Adapters (LoRA) on the harness's vLLM path

Read from the wheelhouse source on 2026-11-05 (`adk_submission` 0.2.13, vLLM 0.19.1); described in our own words. EXP-047 carries the same facts. Q4 is settled for the E4B [V]: EXP-047 v2 (2026-11-08) showed the served model applies `adapters/` canaries with no fall-through, and EXP-054 v2 (2026-11-08) served a trained rank-8 `q_proj`/`o_proj` adapter in this layout (keys `base_model.model.<module>.lora_{A,B}.weight`, module names from the served checkpoint's index) through `VllmServer`: listed in `/v1/models`, 228 of 228 requests HTTP 200 and answered under the adapter name, and the compiled agent model ended in the adapter name.

- **Discovery** [V] `adk_submission/discovery.py:384-500` (`discover_adapters`).
  - A PEFT directory under `adapters/<name>/` (an `adapter_config.json` beside `adapter_model.safetensors`) becomes one adapter, named after the directory.
  - Its rank is `r` from the config, else read from the safetensors header (`discovery.py:288-330`).
  - Nothing reads `base_model_name_or_path`.
- **Server flags** [V] `adk_submission/server.py:759-797` (`VllmServer.build_cmd`).
  - `--enable-lora` is passed only when at least one adapter mounts.
  - `--max-loras` is the number mounted. The notebook's `max_loras=8` is overridden.
  - `--max-lora-rank` is the largest detected rank rounded up to a vLLM bucket, from 1, 8, 16, 32, 64, 128, 256, 320, 512 (`server.py:58`, round-up at `:62-67`).
  - Each adapter is passed as `--lora-modules name=path`.
  - A submission without adapters boots with LoRA off.
  - The scorer's own `scripts/inference.py` is not in the wheelhouse. Its README describes `max_loras = max(1, n)` and a rank of the maximum detected, without the bucket [M as to the scorer].
- **Routing** [V] `server.py:398-445` (`create_model_registry`) and `swegemma/harness/agent_runner.py:64-92` (`resolve_swegemma_adapter`, wired at `:616-627`).
  - An adapter name and `adapter:<name>` resolve to the adapter as the request's model.
  - That holds only when the server is a `VllmServer` with `enable_lora` on (`server.py:432-439`). Otherwise the name resolves to the base model path, with no error: a **silent fall-through**.
  - A direct HTTP request naming an unknown model gets an error from vLLM. Only the registry path can fall through.
- **Model side** [V] vLLM 0.19.1.
  - `Gemma4ForCausalLM` (`gemma4.py:1439-1441`) and `Gemma4ForConditionalGeneration` (`gemma4_mm.py:883-889`) declare LoRA support.
  - `q/k/v` pack into `qkv_proj` and `gate/up` into `gate_up_proj`.
  - The PEFT prefix `model.language_model.` maps onto the module paths, so the organisers' sample key layout loads.
  - `vllm/lora/lora_model.py:161-191` raises on an unexpected target module.
- **The organisers' sample adapter is a no-op** [V, counted 2026-11-05].
  - Both `lora_B` tensors are all zero.
  - It is rank 4, `q_proj`/`o_proj`, layer 0 only, with 31B shapes. Use it as a format example only.
