---
id: kg-744331-lora-kv-cache-and-loading
topic_id: 744331, 744070, 745364
title: With LoRA enabled, the 4xL4 KV cache shrinks to ~7.6k tokens (744331); Can the scoring server load LoRA (744070); Has anyone confirmed a LoRA adapter taking effect in a scored run (745364)
author: Adithya Giridharan (744331); clustifier (744070); Manoj Gowda BG (745364)
author_role: participants; host = Ryan Holbrook
credibility: host statements [V] as to text, fix status unconfirmed; participant measurements [M], one (whoami 09-30) is a measured KV count, not a score
topics: [adapters, lora, kv-cache, vllm, scoring]
first_seen: 2026-11-05
last_checked: 2026-11-05
---

## Summary
Three threads on whether an adapter-bearing submission runs at all, and at what context length. Measured at the notebook's default LoRA settings, a submission that ships any adapter gets a KV cache of about 7,600 tokens on 4xL4 (vs 46,048 without). Prompts above that hang. The host said on 2026-09-30 that it will size the LoRA slots from the submission. One participant reports (2026-10-04) that the hang is gone on wheelhouse v28, and a later participant (2026-10-08, in 743508) measured 27,696 tokens with the submission-sized values. The host has not confirmed the scorer uses either setting. Whether the scorer runs these values is still open.

## 744331: KV cache shrinks with LoRA (Adithya Giridharan, 2026-09-29, 5 votes)
- Setup: Kaggle L4x4, getting-started install cell and its `VllmConfig` (TP=4, `max_model_len` 32768, `gpu_memory_utilization` 0.90, `enable_lora=True`, `max_loras=8`, `max_lora_rank=128`), launched via `VllmServer.build_cmd()`.
- Measured: no adapter, GPU KV cache 46,048 tokens. Sample main_lora (rank 4) only: 7,600 tokens (1.74 GiB free per GPU). The author says `build_cmd()` passes `--max-loras max(8, n)` and `--max-lora-rank 128`, so a submission cannot lower them.
- With that server, a ~6.9k-token prompt completes; a ~20.7k-token prompt never starts ("Running: 0 reqs, Waiting: 1 reqs" for 600 s), for both base and adapter model names.
- Host, 2026-09-30 16:30:40, Ryan Holbrook: "I will patch to set the `loras` parameters based on the submission. It looks like a bug in our vLLM version is causing the hang, but I think I have a workaround." [V as text]
- Pierre Baume, 2026-10-04 11:22 [M]: quotes an AI assistant's output (says so in the post). On wheelhouse v28, 4xL4, util 0.80, TP 4, vllm 0.19.1, a rank-16 adapter loads and serves; 28k-token prompts complete; KV 36,432 -> 27,712 tokens (0.76x). Most of the loss is CUDA-graph specialisation (graphs captured twice). Proposes `compilation_config={"cudagraph_specialize_lora": False}`; with it, KV 34,288 (0.94x). Offers logs; no host reply.
- whoami, 2026-09-30 14:13:17 [M, measured]: rank-64 trained adapter, wheelhouse v25, same `VllmConfig`. Log: KV 1.74 GiB, 7,600 tokens. ~4,000-token prompt served by base (7.9 s) and adapter (5.4 s); ~14,000-token prompt never returns (900 s read timeout each). Author says 99% of their episodes exceed 7,600 prompt tokens. Asks Ryan which `VllmConfig` the private scorer uses when an adapter is present. No host reply.

## 744070: can the scorer load LoRA? (clustifier, 2026-09-28, 1 vote)
- Author: the vLLM 0.19.1 in the published wheelhouse gives `ValueError: Gemma4ForConditionalGeneration does not support LoRA yet` with the sample main_lora; author says the tagged upstream 0.19.1 does not implement `SupportsLoRA` for this class. Asks whether the scorer uses a different build.
- Host, 2026-09-28 14:48:48, Ryan Holbrook: "We're using a patched version of vLLM 0.19, updated in the wheelhouse recently." And the getting-started notebook "appears to show it working." [V as text]
- Cross-ref: 743213 (2026-09-26, Carson Rodrigues) says only the patched 0.19.1 in the wheelhouse adds `SupportsLoRA`; the unpatched PyPI wheel fails at startup.

## 745364: has anyone confirmed an adapter taking effect in a scored run? (Manoj Gowda BG, 2026-10-03, 0 votes)
- Opening asks about silent drop of adapters and the 7.6k KV figure; also asks about QLoRA on 2xT4.
- Manojhmshetty, 2026-10-08 03:21 [M]: submitted v5 plus "a zero lora adapter (rank 16, one q_proj module, peft format)"; it failed with "Kaggle Error"; the same bundle without the adapter scored 0.13. Asks whether LoRA loading on the scorer hits a vLLM sampler warmup OOM (256 dummy requests) on 4xL4. No host reply in the topic.

## Related submissions reported in other threads (participant text, not checked)
- whoami, 2026-09-30 23:12 in 744331 [M]: submission 56719837 with a 980 MB rank-64 adapter "completed after about 30 minutes with no score", error "Your notebook hit an unhandled error while rerunning your code." Asks whether the scorer side raised it. No host reply.

## Status
- Host-side statements on the hang: 2026-09-30 only, "I will patch", "I think I have a workaround". No later host statement in these three topics as of 2026-11-05.
- Participant evidence that a sized setup works: Fawad07 (743508, 2026-10-08, 27,696 tokens with `max_loras=2`, `max_lora_rank=8`); Pierre Baume (744331, 2026-10-04, v28, 27,712 tokens). Neither is the scorer.
- Still open: which `VllmConfig` the scorer uses with an adapter present (asked by whoami on 09-30, not answered).

## Files
- None downloaded from these threads.
