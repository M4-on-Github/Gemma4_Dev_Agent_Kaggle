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

### 4.4 Amendment 2026-11-05, after the guard refused the push and before any number exists: two misreads closed

Found on review after 483d448. A1, A3 to A6 and reading B stay as written; these two clauses change which row two specific outcomes land in.

1. **A failure of the loud dose alone.** The loud dose can break the numerics (condition (iii) makes it large on purpose); vLLM loads an adapter on its first request, so a failure on that request can also be a load failure. As written, any adapter non-200 is A1. Now:
   - E5's non-200 test reads the **logprob** requests only, the measure. A greedy or decode failure is recorded and not read, so an engine that dies after the loud request does not turn earlier passes into A1. Logprob requests run first for every name (the notebook's order).
   - Suppose the logprob failures are confined to `canary_loud`, while `canary_zero` and `canary_big` return 200 and all three names are listed. Then the failure is classed by its error text:
     - text naming the adapter or LoRA, a target module, or a missing model stays **A1** as written;
     - text naming NaN, inf, overflow or a numerical error sets **E2 = infinity** (applied at the loud dose), and reading A proceeds on E1 to E3 as written;
     - any other text leaves E2 unread, so A3 and A4 cannot fire and the row is A6 unless E1 and E3 decide A2 or A1f.
2. **Every adapter logprob request skipped.** Boot 1 starts, but the 30-minute cap stops every adapter logprob request. That is "the kernel ends before boot 1's logprob probes": **A0**, not A1.

`experiments/EXP-047/analyze_canary.py` applies both. It was run on seven synthetic outputs:

| synthetic output | row |
|---|---|
| applied | A3 |
| wiped | A5 |
| fall-through | A1f |
| loud non-finite | A3 |
| loud overflow error | A3 |
| loud LoRA load error | A1 |
| all skipped | A0 |

These test the code path, not a result.

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

- **Pushed 2026-11-07 (section 8 addendum, written at the push; nothing above is revised).** Authority: the user's decision of 2026-11-07 (`knowledge/user-decisions.md`, correction entry); GPU under D-006 item 1. The guard rule for zero-task GPU probes was applied by the user and committed as fad234a; it admits a notebook with no `RUN_AGENT` and no `TASK_IDS` parameter, a `**Cohort:** none` line and no competition source, so section 7 item 7 no longer blocks. Pre-push checks: this file committed with its section 4 readings and `**Cohort:** none`; `kernel-metadata.json` has `competition_sources: []`; the docker image, dataset source (`metric/gemma-4-developer-agent-wheelhouse`, unversioned, as in EXP-038) and model source (`google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2`) equal those of `notebooks/exp038_e4b_dev48/kernel-metadata.json` (the E4B source of EXP-038 and S-014), and the notebook's model path layout and wheelhouse path candidates equal those of `notebooks/kaggle_eval_l4x4.py`. **Nothing was rebuilt**; the 2026-11-05 notebook was pushed as committed (764ae43). Push at 2026-11-07T23:41:34Z to 23:41:48Z UTC from commit fad234a: kernel `rainm4/gemma4-exp047-q4-canary` **version 1**, status RUNNING right after the push. Expected 0.20-0.35 L4x4-h (point 0.26), capped at 0.5 h in the notebook. One malformed attempt came first, at about 23:40 UTC: the push command was chained with other commands in one shell line, the hook read the directory argument with a trailing `;`, and it refused with "Blocked kernel push: expected exactly one .ipynb in notebooks/exp047_q4canary;, found 0." That refusal came from the command text, not from the guard's rules; nothing reached Kaggle and no GPU was spent by it. The push above was the bare command, run once.

### v2 re-run, 2026-11-08

Written before the v2 push. Nothing above is revised.

- **The one change.** `notebooks/exp047_q4canary/kernel-metadata.json` now sets `competition_sources` to `gemma-4-developer-agent`. Every other key is as before. Reason: v1 read A0, and section 9.1 traced the cause to the kernel seeing 2 GPUs, the likeliest reason being that no competition source was attached (section 9.4). The notebook is not touched and not rebuilt. `q4_canary.ipynb` is the file committed in 764ae43, sha256 `35bd32c8c127e75a31fc477c2ca218ea3d0ce16c3feb87d2d323e1a08067bb67`, checked again before this commit.
- **Authority.** The user decision of 2026-11-08 in `knowledge/user-decisions.md` ("the guard admits the main competition source on a zero-task probe; the EXP-047 canary re-run is approved"). The user's guard patch is committed with it as dd8d3fc: a zero-task GPU probe may now attach the main competition source and nothing else.
- **A section 8 property no longer holds for v2.** The 2026-11-05 build note says that no competition source is attached, so no competition file is mounted in the kernel. For v2, the competition mount is present. The notebook reads nothing under it (no path in `q4_canary.py` names it), it has no `TASK_IDS` and no `RUN_AGENT`, it runs no agent and no task, and its outputs are its own files: the canary records, the env record and the boot logs.
- **Unchanged.** Sections 3 and 4 (with the 4.3 and 4.4 amendments) are unchanged, and so are the analysis script and the caps (27-minute stop, 0.5 h cap). The expected cost is still 0.20-0.35 L4x4-h (point 0.26). This is the one re-run A0 allows. If v2 also fails, there is no further re-run without the user's word.
- **v2 pushed.** 2026-11-08, between 14:42:34Z and 14:42:51Z UTC, from commit 0e4b9d3 (addendum and metadata change), with the bare command from the repo root, once. The push printed "Kernel version 2 successfully pushed." Kernel `rainm4/gemma4-exp047-q4-canary` **version 2**; one `kaggle kernels status` call right after returned `KernelWorkerStatus.RUNNING`. Expected 0.20-0.35 L4x4-h (point 0.26), cap 0.5 h. The download and analysis is a separate job (section 6 commands; results appended as a v2 part of section 9).

## Status

~~2026-11-05: pre-registered. Not built, not pushed. Zero GPU spent.~~

2026-11-05: renumbered EXP-046 to EXP-047, critic conditions added (4.3), built (764ae43). **Push refused by `guard_push.py`** on the one attempt (the section 6 push of `notebooks/exp047_q4canary`): the hook's message is that `RUN_AGENT` is not True and that gold controls run only from an exp000 directory. The guard admits a notebook without `RUN_AGENT` only when its metadata is CPU-only (section 8). Nothing reached Kaggle; zero GPU spent. A push needs a guard rule for zero-task GPU probes (a user or lead decision; `.claude/hooks/` is outside the experimenter's paths); the notebook is not altered to get past the guard.

2026-11-07: **pushed**, kernel `rainm4/gemma4-exp047-q4-canary` version 1, at 23:41 UTC from commit fad234a, after the user's guard rule for zero-task GPU probes (fad234a). No rebuild (section 8 addendum). Expected 0.20-0.35 L4x4-h (point 0.26), cap 0.5 h. Not analyzed; download and analysis are a separate job (section 6).

2026-11-08: **ERROR, read as A0 / B0** (section 9). v1 stopped at its own GPU-count gate at 120.5 s with 2 GPUs visible, before boot 0. GPU 0.040 h (kernel-log span). Proposed fix: attach the competition source in the metadata. That needs the user to change the guard rule; nothing was rebuilt or re-pushed. Next command, only after the user approves the re-run and changes the guard: re-push `notebooks/exp047_q4canary` with the one metadata change recorded in section 8.

2026-11-08: **v2 pushed** (14:42 UTC, version 2, RUNNING, from 0e4b9d3). The one A0 re-run, with the main competition source attached (section 8, v2 addendum; user decision 2026-11-08, dd8d3fc). Next, when COMPLETE: download `rainm4/gemma4-exp047-q4-canary` into `runs/EXP-047-q4-canary-v2/` and run `python -I -X utf8 experiments/EXP-047/analyze_canary.py runs/EXP-047-q4-canary-v2`. If v2 fails, there is no further re-run without the user.

---

## 9. Results, 2026-11-08. Section 4's readings applied as written.

Kernel `rainm4/gemma4-exp047-q4-canary` version 1 ended with status `KernelWorkerStatus.ERROR` (`kaggle kernels status`, rechecked at the download). Downloaded with the section 6 command to `runs/EXP-047-q4-canary/`; the bundle nested one level, as usual, and was moved up. It holds `canary.json`, `env.json` and the kernel log only. No `probes.jsonl`, `boot0.log`, `boot1.log` or `adapters.json` was written. Everything was read as data with `python -I -X utf8`; nothing from the bundle was run. `python -I -X utf8 experiments/EXP-047/analyze_canary.py runs/EXP-047-q4-canary` ran (exit 0) and returned `reading_A` A0 and `reading_B` B0.

### 9.1 Where and why it stopped

- **Last stage reached: GPU count**, the check after install and imports. The wheelhouse installed 41 of 41 wheels with none skipped (install 119.0 s by the notebook's clock; the log line says 65 s for the copy-and-install step), and the version imports ran. The notebook's own gate then failed and recorded stage `no_gpu_or_model` at 120.5 s, with `gpu_count` **2**.
- **Failure class.** `SystemExit` raised by the notebook's own gate, with the notebook's own message about needing 4 GPUs and the E4B input. Papermill reported it as `PapermillExecutionError` at cell In [2], which is why Kaggle shows ERROR. This is a real stop before any boot, not an exception thrown after the outputs were written. `canary.json` carries `status: infrastructure` because the gate writes it before raising.
- **The cause.** `torch.cuda.device_count()` returned 2. The gate needs exactly 4. The gate tests the GPU count and the model's `config.json` together, and the stage record does not say whether the E4B input was mounted. So the model half is not read here; the GPU half fails on its own.
- **Why 2 GPUs [I].** Every earlier GPU kernel of ours with the same `machine_shape` (`NvidiaL4`), docker image and model source logged 4 GPUs: 15 kernel logs under `runs/` show `tp=4, gpus=4` and none shows fewer, including EXP-038 (the same E4B, wheelhouse and image). This kernel's metadata differs from EXP-038's only in `id`, `title`, `code_file`, and **`competition_sources` empty** (EXP-038: `gemma-4-developer-agent`). `plan.md:114` records [M] that L4x4 is available to competition-attached notebooks only. The likeliest cause is therefore that a kernel with no competition source attached is given the 2-GPU L4 machine. This is an inference from one kernel; the notebook exited before its `nvidia-smi` call, so the device type was not recorded.
- **Versions, as recorded** (`env.json`): Python 3.12.13, vllm 0.19.1, torch 2.10.0+cu128, adk_submission 0.2.13, swegemma 0.2.11, google-adk 1.36.1, litellm 1.82.4, safetensors 0.8.0. Wheel sha256: vllm `73c69bafca24fbdad44690c44d6c6446514351e6f3cc9a6057cba05e66051310`, adk_submission `f156f0bd84580ccb9334726d114d7a5481f16d3a6e2887cc4d276ced0ef8d99d`, swegemma `9ad876581f3acde8ec3c369858f0834e2b9f41a3cffce3ca42f09cb090aea9d3`. `build_cmd` flags: not recorded, because no boot started.

### 9.2 Readings

| Reading | Row | Why |
|---|---|---|
| A | **A0** (infrastructure) | first matching row: "no 4 GPUs"; the kernel ended before boot 0, so it also ended before boot 1's logprob probes. A1, A1k, A1f and the 4.4 clauses are not reached: no boot 1 started and no adapter request was sent |
| B | **B0** (no reading) | boot 1 did not start, so K1 is not in any boot-1 log |

E1 to E6: none exists. E1, E2, E3, F, tau and H are null; E5 is false only because nothing loaded (no names listed, no adapter non-200s, because no requests were sent); K0 and K1 are null. The routing check did not run. Reading A0 says nothing about whether adapters are applied. Q4 stays OPEN, and C-024's gate is unread. The blind prediction gave A0 or A6 5%.

### 9.3 GPU spent

Kernel-log span (last kernel-log entry, as EXP-038 E8 was measured): **144.5 s = 0.040 h**. Kaggle showed no figure. Whether the hours of a 2-GPU L4 kernel are charged against the 30 L4x4-h per week is unknown.

### 9.4 A0: the one cause and the one fix (proposed, not applied)

- **Cause:** the kernel saw 2 GPUs, not 4. The likeliest reason [I, 9.1] is that no competition source was attached.
- **Fix (proposed):** add `gemma-4-developer-agent` to `competition_sources` in `notebooks/exp047_q4canary/kernel-metadata.json`, as every 4-GPU arm has it, and change nothing else. The notebook reads nothing under that mount, so no task runs and no competition file is written to the outputs. But it ends the "no competition source is attached" property of section 8. And the user's zero-task-probe rule in `guard_push.py` (fad234a) admits only a notebook with **no** competition source, so the push needs the user to change that rule first.
- **Fallback, not proposed:** let the gate accept 2 GPUs with tp = 2. That changes the design (K0 and K1 would then be tp = 2 figures, not the 4-GPU server's), so it would need its own amendment.
- **Not done here:** the notebook was not edited, rebuilt or pushed. A0's "re-run once" goes to the user through the lead.
