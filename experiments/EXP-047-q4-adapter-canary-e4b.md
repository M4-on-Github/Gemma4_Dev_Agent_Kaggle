# EXP-047 — Q4 adapter canary on the E4B: does the harness's own vLLM start path apply an `adapters/` LoRA, and what KV cache does an adapter-bearing submission get?

**Date:** 2026-11-05
**Type:** zero-task GPU probe, one kernel, two vLLM boots of the E4B, no agent run, no grading. About **0.20-0.35 L4x4-h expected (point 0.26)**, worst case about 0.5 h, notebook hard cap ~~0.75 h~~ 0.5 h (section 2.5; caps tightened at build, section 8). ~~**Built, not pushed**: no GPU approval is open, and the push guard does not admit this notebook as it stands (section 8).~~ 2026-11-05: GPU approved by the user (`knowledge/user-decisions.md`, D-006 item 1, 0.2 to 0.3 GPU-h); push status in section 8.
**Cohort:** none (no task runs; the notebook has no `TASK_IDS` and no `RUN_AGENT` parameter)
**Ladder:** stage 1 of D-006 (`knowledge/directions/D-006-e4b-role-team-and-tool-adapter.md`), the gate in front of any adapter work for C-024. Not a screen of a lever: it answers an infrastructure question that n = 8 or 48 task runs cannot read (an adapter that is silently dropped and an adapter that does nothing useful give the same resolves).
**Pre-registered:** this file, then the notebook and the analysis script, are committed before any push. Sections 3 and 4 are written blind and are not revised; results are appended as a new section.
**Serves:** Q4 (`experiments/README.md` §1, "LoRA zeroing in patched vLLM", OPEN), C-024 (narrow exact-copy adapter, gated on this canary), C-013 (the earlier whole-trajectory LoRA result, -10.8 points; was that adapter even applied?).
**Relates:** EXP-006 (the E4B boot and KV figures without LoRA), EXP-048 (the desk costing of the narrow adapter that this canary gates), `research/kaggle/digests/2026-11-05-adapters.md`, `research/kaggle/threads/kg-743508-lora-wipe-host-replies.md`, `research/kaggle/threads/kg-744331-lora-kv-cache-and-loading.md`.
**Tags:** [V] verified in source or by a check run here, [M] community or mirror, [I] inference.

## 1. Why this, now

D-006 puts a narrow LoRA on the E4B behind one question: does the served vLLM apply an `adapter:` at all? Three things are known.

1. **The source routes adapters by model name, and sizes LoRA from the submission** [V, read 2026-11-05]:
   - `adk_submission/discovery.py:384-500` (`discover_adapters`) catalogues `.safetensors` under `adapters/`; a PEFT directory (`adapter_config.json` beside `adapter_model.safetensors`) becomes one adapter named after the directory. The rank comes from `adapter_config.json` `r`, else from the safetensors header (`infer_adapter_rank`, `discovery.py:288-330`). Nothing in `adk_submission` or `swegemma` reads `base_model_name_or_path` (grep of every `.py` under the two packages, no hit).
   - `adk_submission/server.py:759-797` (`VllmServer.build_cmd`): `--enable-lora` is added only when at least one adapter mounts; `--max-loras` is the number mounted (the notebook's `max_loras=8` is overridden); `--max-lora-rank` is the detected maximum rank rounded up to a vLLM bucket when every rank is known, else the bucket of the maximum of the config value and the detected ranks. Buckets 1, 8, 16, 32, 64, 128, 256, 320, 512 at `server.py:58`, round-up at `server.py:62-67`. Each adapter is passed as `--lora-modules name=path`. **So a rank-4 adapter is served at max rank 8, and a boot with no adapters runs with LoRA off.** The thread report (744331, 2026-09-29) that `build_cmd` passes `max(8, n)` and rank 128 is not what `adk_submission` 0.2.13 does [V].
   - `server.py:398-445` (`create_model_registry`) binds each adapter name and `adapter:<name>` to a LiteLlm whose model is the adapter name; `swegemma/harness/agent_runner.py:64-92` (`resolve_swegemma_adapter`, wired at `agent_runner.py:616-627`) returns that entry, or else copies the base LiteLlm with only the model changed to `<prefix><adapter_name>`. Either way the HTTP request names the adapter as the model.
   - The vLLM 0.19.1 wheel in the wheelhouse declares LoRA support on both Gemma 4 classes: `vllm/model_executor/models/gemma4.py:1439-1441` (`Gemma4ForCausalLM`, `SupportsLoRA`) and `gemma4_mm.py:883-889` (`Gemma4ForConditionalGeneration`, `SupportsLoRA`). Both pack `q_proj`/`k_proj`/`v_proj` into `qkv_proj` and `gate_proj`/`up_proj` into `gate_up_proj` (`gemma4.py:1463-1473`, `gemma4_mm.py:892-902`), and both map the PEFT prefix `model.language_model.` onto their own module paths (`gemma4.py:1444-1459`, `gemma4_mm.py:905-919`), so an adapter keyed like the organisers' sample loads on either class. `gemma4.py:1460-1462` notes that `k_eq_v` layers keep `q_proj` and `k_proj` unpacked; this canary targets `q_proj` and `o_proj` only. `vllm/lora/lora_model.py:161-191` raises on a module the model does not expect, so a mis-keyed adapter fails loudly rather than being dropped.
   - The scorer's own `setup_vllm_server` (`scripts/inference.py`) is not in the wheelhouse. `HARNESS_README.md:169` describes its sizing as `max_loras = max(1, len(adapter_map))` and `max_lora_rank = max(detected_ranks)` without the bucket round-up [M as to the scorer]. This canary tests `VllmServer.build_cmd`, the path our dev runs use, and not the scorer.
2. **The organisers' sample adapter is a no-op by construction** [V, counted here]. In our staged copy (`runs/EXP-028-armR/phase0/sample_submission/adapters/main_lora/`), both `lora_B` tensors are all zero (0 of 21,504 and 0 of 32,768 entries non-zero); both `lora_A` tensors are dense with standard deviation about 0.01. So "it works in the Getting Started notebook" (host, 2026-09-25) can mean that it loads, not that it changes output. Its shapes are the 31B's; it is a format example only.
3. **The only post-fix test says loaded but no effect** [M]. The host said the zeroing fix is in wheelhouse v23 (2026-09-30). A participant (743508, 2026-10-08) reports that, under `VllmServer` with `discover_adapters`, the adapters are listed in `/v1/models` and requests route to them, but at temperature 0 the base model, a near-zero adapter and a `lora_B ~ N(0, 1)` adapter (the sample's format: rank 4, `q_proj` and `o_proj`, layer 0) give the same text with per-token logprobs within 1e-6. The same thread family reports an adapter-bearing 31B submission getting a 7,600-token KV cache at the notebook's then-default LoRA settings, against 46,048 without, and 27,696 with the submission-sized settings [M].

What none of these settles: whether, on the wheelhouse we run today, a LoRA with non-zero `lora_B` changes the E4B's output, and how much KV cache the E4B keeps with one. Both are needed before a training run is costed for real (EXP-048). The E4B is used because D-006 is E4B-only and its boot is the cheapest; nothing in the harness source restricts adapters to the 31B.

## 2. Design

### 2.1 The adapters, made inside the kernel from the model's own shapes

No competition data and no third-party weights. The kernel reads `config.json` (top level and `text_config`) and the checkpoint's tensor index, takes each layer's `q_proj` and `o_proj` module names and `[out, in]` shapes from the checkpoint (`weight_shape` where the weights are compressed, else the weight's own shape), asserts them against the config, and writes three PEFT directories under `/kaggle/working/canary_sub/adapters/` with the sample's key pattern (`base_model.model.` + the checkpoint module name + `.lora_A.weight` / `.lora_B.weight`) and the sample's `adapter_config.json` fields (only `r`, `lora_alpha`, `target_modules`, `layers_to_transform` and `base_model_name_or_path` set per adapter). BF16, fixed seeds.

| Adapter | rank, alpha | modules, layers | `lora_A` | `lora_B` | role |
|---|---|---|---|---|---|
| `canary_zero` | 4, 8 | `q_proj`, `o_proj`; layer 0 | N(0, 0.01) | 0 | the sample's own construction: the control that must equal base |
| `canary_big` | 4, 8 | `q_proj`, `o_proj`; layer 0 | N(0, 0.01) | N(0, 1) | **the participant's test (743508), reproduced** on the E4B's shapes |
| `canary_loud` | 8, 16 | `q_proj`, `o_proj`; every layer | N(0, 1) | N(0, 1) | the positive-control dose: if applied it cannot fail to move the output, so "no change" cannot be read as "too small" |

Each file is re-read from disk after writing and its non-zero counts, bytes and sha256 recorded. Expected sizes are a few MB in total (section 7 item 5); max rank 8 is far under `MAX_LORA_RANK` 128 and the 3 GiB limit.

A minimal submission directory is written beside them (`agent.yaml` with `model: gemma-4-e4b-it-qat-w4a16-ct`, `adapter: canary_big`, a one-line instruction, no tools), so that adapters are discovered by `discover_adapters(<submission root>)` exactly as the eval notebook does.

### 2.2 Two boots, in this order

1. **Boot 0, no adapters.** The same submission directory with `adapters/` absent; `discover_adapters` returns nothing, so `build_cmd` adds no LoRA flag. The eval notebook's `VllmConfig` (TP 4, `max_model_len` 32768, `gpu_memory_utilization` 0.90, `gemma4` parsers, `enable_thinking` true by default, `startup_timeout` 900 s). This boot is the infrastructure check and the KV baseline.
2. **Boot 1, three adapters.** Same config, `adapter_manifest=discover_adapters(<root>)`. Expected flags: `--enable-lora --max-loras 3 --max-lora-rank 8 --lora-modules canary_zero=... canary_big=... canary_loud=...`, recorded from `build_cmd()` before start.

The vLLM log is copied continuously (`VllmServer.stop()` deletes it; the EXP-006 `LogTee`), and `GPU KV cache size: N tokens` and `Maximum concurrency` are parsed from the copy.

### 2.3 What is sent

All requests are sequential, `temperature` 0, with a client timeout of 120 s; after one timeout on a model name, the rest of that name's requests are skipped and the timeout recorded. Two fixed prompts, written for this file in our own words (about 150 to 250 tokens each, neutral prose, no code), defined in the notebook's parameter cell.

- **Prompt logprobs** (the measure): `POST /v1/completions` with `echo: true`, `logprobs: 0`, `max_tokens: 1`, on each prompt; the per-token logprob of every prompt token after the first. If the server rejects `echo`, the same with `prompt_logprobs: 0`. The token sequence must be identical across model names (one tokenizer); a mismatch is recorded and that prompt dropped.
- **Greedy text** (corroboration, not a measure): `POST /v1/chat/completions`, two fixed questions, `max_tokens` 48, `chat_template_kwargs: {enable_thinking: false}`.
- **Decode speed** (recorded): one 256-token greedy chat completion per model name on boot 1, tokens per second from `usage` and wall.
- `GET /v1/models` on both boots.

Boot 0: base, twice. Boot 1: base, base again, `canary_zero`, `canary_big`, `canary_loud`.

**Routing through the official compile path** (recorded, boot 1): `registry = server.create_model_registry(aliases=[declared model, TARGET], model_prefix="openai/")`, then `compile_submission(<root>, tool_registry={}, model_registry=registry, adapter_manifest=..., adapter_resolver_fn=lambda b, i: resolve_swegemma_adapter(b, i, registry))`; record the root agent's model string, then one `litellm.completion` through that model string and `api_base` on the first greedy question and compare its text with the direct `canary_big` request.

### 2.4 Quantities, defined now

- d(x, y) = the maximum, over both prompts and every prompt position, of |logprob_x - logprob_y|.
- **F, the repeat floor** = max(d(base, base repeat) on boot 1, d(base, base repeat) on boot 0).
- **tau** = max(10 F, 1e-3), the "no change" band; **H** = max(100 F, 0.05), the "changed" bar.
- **K0, K1** = `GPU KV cache size` tokens on boot 0 and boot 1 (the minimum if the log has several lines).
- Recorded, not read: d(base boot 0, base boot 1) (does turning LoRA on move the base path?), greedy text equal or not per name, decode tok/s per name, the routing result, boot seconds, `build_cmd` LoRA flags, `/v1/models` names, the model's architecture, text dims and per-layer `q_proj`/`o_proj` shapes (EXP-048 needs them), wheelhouse versions (`vllm`, `adk_submission`, `swegemma`) and the vLLM wheel's sha256.

### 2.5 Cost

| item | seconds | basis |
|---|---|---|
| wheelhouse install and imports | 100 to 150 | EXP-033: 445 s overhead of which 323 s was vLLM up |
| boot 0 (E4B, LoRA off) | 290 to 330 | EXP-006 289.4 s, EXP-033 322.9 s, EXP-040 319.8 s |
| boot 1 (E4B, 3 adapters, rank 8) | 300 to 450 | boot 0 plus LoRA warm-up and a second set of CUDA graphs [I; 744331 reports graphs captured twice with LoRA] |
| probes, both boots | 40 to 100 | 7 names x (2 logprob + 2 greedy) short requests, 5 decode runs of 256 tokens at about 56 tok/s (EXP-033) |
| adapter build, teardowns, compile check | 30 to 80 | shapes from the index, three small files, two stops |
| **total** | **760 to 1,110 s = 0.21 to 0.31 h; range 0.20 to 0.35 h, point 0.26 h** | |

**Worst case about 0.5 h**: boot 1 hangs to its 900 s startup timeout, plus at most 3 request timeouts of 120 s. The notebook stops starting new work at 40 minutes and has a hard cap of 45 minutes (0.75 h).

## 3. Endpoints, fixed in advance

From `runs/EXP-047-q4-canary/` (the kernel output: `canary.json`, `probes.jsonl`, `boot0.log`, `boot1.log`, `adapters.json`), read by `experiments/EXP-047/analyze_canary.py`.

| # | Endpoint | Definition |
|---|---|---|
| E1 | d(canary_big, base) | 2.4, boot 1 |
| E2 | d(canary_loud, base) | 2.4, boot 1 |
| E3 | d(canary_zero, base) | 2.4, boot 1 |
| E4 | F, tau, H | 2.4 |
| E5 | Loadable | boot 1 started; all three names in `/v1/models`; every adapter request returned HTTP 200 |
| E6 | K0, K1, K1/K0 | 2.4 |
| E7 | Recorded, not read | the 2.4 list |

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Two questions, each with its own reading. First matching row wins within each table.

### 4.1 Reading A: is the adapter applied?

| Row | Condition | Reading |
|---|---|---|
| A0 | infrastructure: the wheelhouse install or imports fail, no 4 GPUs, the E4B input is missing, boot 0 fails, or the kernel ends before boot 1's logprob probes | no reading; fix the one cause and re-run once |
| A1 | **not loadable**: boot 1 fails while boot 0 started (a failure naming the KV cache or the maximum model length is reported as A1k, the rest as A1), or a canary name is absent from `/v1/models`, or any adapter request returns non-200 | adapters do not load on this path. The adapter line (C-024 stage 2 onwards) stops until the failure is understood; the failure text class and `build_cmd` flags are reported |
| A2 | E3 > tau | the zero-B control moves the output: the LoRA path is not a clean add, so neither "applied" nor "wiped" can be read; reported as an infrastructure finding for the lead |
| A3 | **applied**: E1 > H and E2 > H | the adapter is applied at the thread's own dose; the 2026-10-08 null does not reproduce on this wheelhouse. Stage 2 of D-006 (EXP-048's costing, then a training kernel) may be asked for |
| A4 | **applied at the loud dose only**: E2 > H and E1 <= tau | LoRA is applied, but a layer-0 rank-4 `lora_B ~ N(0, 1)` adapter on the E4B does not move the output; the thread's null is a weak-adapter result, not a wipe. Stage 2 may be asked for, with the trained adapter's own effect measured before any agent run |
| A5 | **wiped**: E1 <= tau and E2 <= tau, with E5 true | adapters load, are listed and route, and do nothing: the 2026-10-08 report reproduces under our path. **The adapter line stops** (C-024's training is not bought); the evidence goes to the lead for a host report |
| A6 | anything else (for example tau < E2 <= H) | no reading; numbers reported |

### 4.2 Reading B: is there enough context with an adapter?

| Row | Condition | Reading |
|---|---|---|
| B0 | K1 is not in boot 1's log (or boot 1 did not start) | no reading |
| B1 | K1 < 14,336 | **kills the adapter line on context, whatever reading A says**: the single loop compacts at 14,336 prompt tokens, so one request at its threshold does not fit |
| B2 | 14,336 <= K1 < 32,768 | the single loop fits; one request at `max_model_len` does not, so any design with concurrent requests (voting, a parallel team) is constrained; reported with K1/K0 |
| B3 | K1 >= 32,768 | context is not a constraint for the E4B with an adapter of this size |

These figures are the E4B's. They do not transfer to the 31B's 7,600 and 46,048, and the 31B's do not transfer here.

**Blind prediction.** Reading A: A3 40%, A4 10%, A5 30%, A1 12%, A2 3%, A0 or A6 5%. The host's fix claim and adk_submission 0.2.13 (newer than the 0.2.12 the 2026-10-08 participant cites) pull towards A3; the one post-fix test pulls towards A5. If A3, E1 of order 0.5 to 5 nats and the loud adapter's greedy text visibly degraded; if A5, E1 and E2 exactly 0 with F = 0. Reading B: B3 92% (EXP-006 measured K0 = 298,464 for the E4B, and rank 8 with 3 slots is small), B2 5%, B1 3%; K1/K0 between 0.6 and 0.95. Decode tok/s with an adapter 10 to 30% below base [I, from the 29% per-task slowdown reported in 755677 on the 31B].

### 4.3 Amendment 2026-11-05, before any push and before any number exists: the critic's three conditions

Added on the lead's instruction, from the critic's D-006 direction review (`experiments/EXP-043/critic.md`, 19a8b20 and 5ab7020). Sections 4.1 and 4.2 above stay as written; this section adds one row to reading A and states how the other two conditions are met. Reading B is unchanged.

**(i) The server lists the adapter and answers under its name; a silent fall-through is a fail.** [V, wheel `adk_submission/server.py:432-439`, read 2026-11-05] `create_model_registry` binds an adapter name (and `adapter:<name>`) to that name only when the server is a `VllmServer` whose config has `enable_lora` on; otherwise it binds the name to the base model path and raises nothing. A direct HTTP request that names an unknown model gets an error from vLLM, so the direct probes cannot fall through; the registry and compile path can. The notebook therefore also records the `model` field of every response, what each registry name resolves to, and the compiled root agent's model string. New row, checked after A1 and before A2:

| Row | Condition | Reading |
|---|---|---|
| A1f | **fall-through**: any HTTP 200 adapter response whose `model` field names something other than the requested adapter; or the registry binds `canary_big` or `adapter:canary_big` to a model string that does not end in `canary_big`; or the compiled root agent's model string does not end in `canary_big`; or the compile-path text equals boot 1's base text while the direct `canary_big` text differs | **fail**, read like A1: the adapter line stops until the routing is understood. A3 to A5 cannot be read through a fall-through |

A response with no `model` field is counted and reported, not read as a mismatch. A routing check that raises an exception is not a silent fall-through: it is reported, and reading A then rests on the direct probes alone, with the compile-path half stated as not read.

**(ii) At temperature 0, with and without the adapter must differ by more than two runs without it.** Already the design: every canary request sets `temperature: 0` itself (the submission's sampling file, temperature 1.0 for the E4B, is not used by these probes), F is the larger of the two base-against-base-repeat differences (2.4), and A3 and A4 need E1, E2 above H = max(100 F, 0.05), A5 needs them at or below tau = max(10 F, 1e-3). One addition, for the loud dose: a logprob that is not finite on one side only counts as an infinite difference (changed); a non-finite value in a base or base-repeat run makes F infinite and reading A is A6.

**(iii) The adapter is built to have a large effect.** `canary_loud` (2.1) is that adapter: rank 8, alpha 16, `q_proj` and `o_proj` on every layer, both factors N(0, 1). Its update is (alpha / r) B A = 2 B A, whose entries have standard deviation 2 x sqrt(8), about 5.7, against base weights of order 0.01 to 0.1 [I], on every layer. If applied it cannot plausibly leave every prompt logprob within 0.05 nats of base [I]. `canary_big` is the thread's dose, kept to test the 743508 null, not to carry condition (iii).

**Scope, restated.** A pass in a Kaggle notebook tests that notebook's server (`VllmServer.build_cmd` from the attached wheelhouse), not the scorer's `setup_vllm_server` in `scripts/inference.py` [I]. Section 5's last bullet and section 7 item 1 already say this.

**Renumbered 2026-11-05.** This file was committed as EXP-046 in 73d369d; the screener's `experiments/EXP-046-e4b-sequential-role-team-desk-check.md` (0553ba1) was filed first, so the canary is EXP-047 (file renamed in the lead's 162c1aa, ids in the text, notebook directory, kernel slug and analysis path renumbered here). The desk costing that this file called EXP-047 is EXP-048. No reading changed in the renumber.

## 5. What this licenses

- A3 or A4 with B2 or B3: the lead may ask for EXP-048's stage 2 (data generation and a training kernel). Nothing here licenses an upload, and no claim moves on this result alone beyond Q4.
- A5 or A1, or B1: the adapter line stops at this gate; C-024 is reported as blocked by infrastructure, not refuted.
- Any reading: the C-013 result (-10.8 points from a 31B adapter) is not re-read here; whether that adapter was applied is a 31B question this canary does not answer.
- Scope: the wheelhouse attached at run time, `VllmServer.build_cmd`, the E4B. Not the scorer's `setup_vllm_server`.

## 6. Exact commands

```
python tools/build_notebook.py --src notebooks/exp047_q4canary/q4_canary.py --out notebooks/exp047_q4canary/q4_canary.ipynb
# push: a later job, only after the user approves the GPU, the lead dispatches it, and the push guard admits the notebook (section 8)
# after COMPLETE, a separate job:
kaggle kernels output rainm4/gemma4-exp047-q4-canary -p runs/EXP-047-q4-canary/
python -I -X utf8 experiments/EXP-047/analyze_canary.py runs/EXP-047-q4-canary
```

## 7. Defects

Written before the run.

1. **Not the scorer.** The canary exercises `VllmServer` from the wheelhouse; the scorer's `scripts/inference.py` is not available to read, and HARNESS_README describes its rank sizing without the bucket round-up. A different result on the scorer would not show here.
2. **The wheelhouse version is whatever Kaggle attaches at run time.** Versions and the vLLM wheel sha are recorded so that a later re-run can say whether it ran the same build.
3. **Temperature-0 numerics.** Sequential requests on one server are expected to repeat exactly (F = 0); if F is large, tau and H scale with it and a small real effect could hide under it. F is reported.
4. **Prompt logprobs, not generated-token logprobs.** Generated sequences diverge after the first differing token, so only prompt positions are compared; the greedy text is corroboration only.
5. **Sizes are [I] until the kernel reports shapes.** For an E4B with hidden size about 2,560, `q_proj` output about 2,048 and 42 layers, `canary_loud` is about 8 x (2,560 + 2,048) x 2 modules x 42 layers x 2 bytes = about 6 MB, and each layer-0 adapter about 75 KB.
6. **`q_proj` sits in the packed `qkv_proj`.** An adapter that sets only `q_proj` leaves the `k` and `v` slices empty, as the sample does. A failure that only the packed slot shows would read as A1 or A5 here; `o_proj` (unpacked) is in every adapter so that a packed-only failure is not the only route to a change.
7. **The push guard** blocks a GPU notebook that has no `RUN_AGENT` parameter (section 8).

## 8. Built

2026-11-05, built (no GPU spent).

- **Files.** Source `notebooks/exp047_q4canary/q4_canary.py` (py:percent), built with the section 6 command into `notebooks/exp047_q4canary/q4_canary.ipynb` (10 cells, no embedded zip, sha256 `35bd32c8c127e75a31fc477c2ca218ea3d0ce16c3feb87d2d323e1a08067bb67` of the CRLF worktree file); `notebooks/exp047_q4canary/kernel-metadata.json`; analysis `experiments/EXP-047/analyze_canary.py`.
- **Kernel id** `rainm4/gemma4-exp047-q4-canary`. Private, GPU on (`NvidiaL4`, the eval notebooks' docker image), internet off. Inputs: dataset `metric/gemma-4-developer-agent-wheelhouse` and model `google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2` only. **No competition source is attached**, so no task, snapshot or competition file is mounted in the kernel and none can leave it; the adapters are random tensors made in the kernel from the model's shapes, and the prompts are our own words.
- **Amendment to 2.5, dated 2026-11-05 at build, before the push (the 2.5 table stands as the estimate):** the notebook's caps are tighter than 2.5 states: no new boot or probe group after 27 minutes, every wait bounded so the kernel ends near 30 minutes (0.5 h), boot 0 startup timeout 600 s and boot 1 720 s (not 900 s), request timeout 120 s. Boot 1 is not started unless 720 s remain before the 27-minute stop; that case is recorded as infrastructure (A0). So the worst case is the 0.5 h cap, and the expected 0.20 to 0.35 h (point 0.26) is unchanged. A boot that would need more than 720 s on the E4B (boot 0 measured 289 to 323 s three times) is itself a finding, recorded as A1 with its failure class.
- **Amendment (i) wiring.** Every probe records the response's `model` field; the routing check records what each registry name resolves to (`registry_models`), the compiled root agent's model string and the compile-path response. The analysis applies row A1f and the non-finite rule of 4.3.
- **Checks run locally (no GPU).** The adapter and shape cells ran on a synthetic checkpoint with the sample's key layout: keys matched the sample pattern, `canary_zero` has 0 non-zero `lora_B` entries, `canary_big` and `canary_loud` are dense, and the discovered ranks were 4, 4 and 8. The analysis script was run on four synthetic outputs and returned A3 (applied), A5 (wiped), A1f (registry and agent bound to the base path) and A3 (loud logprobs non-finite), each with B3 at the synthetic KV figures. These check the code paths, not the result.
- **Push guard, read before the push.** `.claude/hooks/guard_push.py` admits a notebook with no `RUN_AGENT` parameter only when its metadata is CPU-only; this notebook has GPU metadata and no `RUN_AGENT`, so the guard is expected to refuse it (section 7 item 7). The notebook is not given a `RUN_AGENT` or `TASK_IDS` to pass the guard: it runs no agent and no task, and a fake parameter would misstate what it does.

## Status

~~2026-11-05: pre-registered. Not built, not pushed. Zero GPU spent.~~

2026-11-05: renumbered EXP-046 to EXP-047, critic conditions added (4.3), built (764ae43). **Push refused by `guard_push.py`** on the one attempt (the section 6 push of `notebooks/exp047_q4canary`): the hook's message is that `RUN_AGENT` is not True and that gold controls run only from an exp000 directory. The guard admits a notebook without `RUN_AGENT` only when its metadata is CPU-only (section 8). Nothing reached Kaggle; zero GPU spent. A push needs a guard rule for zero-task GPU probes (a user or lead decision; `.claude/hooks/` is outside the experimenter's paths); the notebook is not altered to get past the guard.
