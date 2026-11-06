---
id: kg-743508-lora-wipe-host-replies
topic_id: 743508
title: LoRA adapters are silently wiped in the patched vLLM 0.19.1 (Gemma4 decoder layers registered twice); cross-ref 743213
author: Whisper Last (opener); Ryan Holbrook (host replies)
author_role: opener participant; host = organiser
credibility: host statements [V] as to what the host said; the fix claims are the host's and untested by us; participant tests [M]
topics: [adapters, lora, vllm, harness]
first_seen: 2026-11-05
last_checked: 2026-11-05
---

## Summary
The host has said twice that the adapter-zeroing bug is fixed in the wheelhouse (v23, now v25). The last host statement on it is dated 2026-09-30. The latest participant test in the topic is dated 2026-10-08 and says the adapter now loads and routes but still does not change the output at temperature 0. No host reply after 2026-09-30 is in the topic as of 2026-11-05. For D-006 Q4 this is open: the host's word says fixed, the one post-fix test says the adapter is registered but its weights have no effect.

## Host statements (Ryan Holbrook, all [V] as to text)
- 2026-09-25 19:31, topic 743213: "I'll check again. ... It's working in the Getting Started notebook, at least." (cross-ref: 743213 opened 2026-09-25 by Violet Notes on the official sample failing; host 10:55 "I have a fix incoming.")
- 2026-09-26 11:19, 743508: "Thanks for the report. I will address."
- 2026-09-30 14:34:38, 743508, two numbered answers to Abdul Muiz:
  1. "The zeroing fix landed in v23 of the wheelhouse dataset (now on v25)." (asked to check the notebook has the latest version)
  2. "Yes, it should." (asked whether `discover_adapters` gets the submission root, "not the adapter directory")
- 2026-09-30 14:34:58, 743508, to Ayush Thakur: "It should be fixed in the most recent wheelhouse version, but please let me know if it seems otherwise."
- No host reply in 743508 after 2026-09-30 (checked 2026-11-05, 6 comments total).

## Participant tests (not reproduced by us)
- Abdul Muiz, 2026-09-29 10:55 (before the host's 09-30 fix statement). Wheelhouse "version [N]", vLLM 0.19.1, sample main_lora with lora_B replaced by N(0,1). Through `VllmServer`, `/v1/models` lists only the base model; `POST /v1/load_lora_adapter` returns 404 with the runtime-updating flag set. Direct `LLM(...)`, `enable_lora=True, max_loras=1, max_lora_rank=128`: base and LoRA text and logprobs identical. Author's caveat: lora_A may be all zero, which alone would explain it; promised a re-run with A and B randomised (no re-run in the topic). Asked whether the zeroing fix is in the wheelhouse or only on the scorer, and whether `/v1/models` should list the adapter.
- Fawad07, 2026-10-08 18:10 (after the host's v23/v25 statement). Setup: Kaggle 4xL4, Getting Started image, `VllmServer` plus `discover_adapters(<submission root>)`, scorer values (`gpu_memory_utilization=0.80`, `max_model_len=32768`), two adapters from the sample main_lora (rank 4, q_proj/o_proj, layer 0): `test_lora` with lora_B N(0, 1e-3) and `loud_lora` with lora_B N(0, 1). Author reports:
  - Memory problem solved: LoRA sized from the submission (`max_loras=2`, `max_lora_rank=8`), 6.06 GiB/GPU model load, KV cache 27,696 tokens, server starts.
  - `/v1/models` lists both adapters; harness requests route to the adapter.
  - DEBUG log shows `Successfully loaded LoRA weights` for `layers.0.self_attn.qkv_proj` and `o_proj`; no `self_decoder` lines, so the reset-after-set is gone (author's reading).
  - Still broken: at temperature 0, thinking off, base, `test_lora` and `loud_lora` return the identical first-ten-primes answer, per-token logprobs agree within 1e-6; same with `--enforce-eager` (within 7e-7).
  - Author's conclusion: "the weights seem to be set but not used in the forward pass". Asked the host to reproduce and whether the scorer runs the same build.
  - Version note: the author cites `adk_submission` 0.2.12 and "the patched vLLM 0.19.1 wheel from 2026-09-30". Our wheelhouse inventory (2026-10-12) lists `adk_submission` 0.2.13. Not reconciled.
- Whisper Last (opener), 2026-09-26 06:00 in 743213: "once the server starts with the patched vLLM, LoRA adapters are silently wiped (no effect on outputs)". Same claim as the topic title.

## Status for D-006 Q4
- Q4 as written ("does the harness apply adapters at all") is not answered by the host. The host's last word (2026-09-30) is a fix claim; the only post-fix test (2026-10-08) says the adapter is loaded and routed but has no effect on output.
- The D-006 canary's kill criterion ("no output change with an adapter loaded") is the same test as Fawad07's. Not reproduced by us; the canary is still needed.

## Files
- None. Nothing from this topic was downloaded.
