# Serving settings and in-task concurrency (read from source, 2026-11-06, EXP-049)

Tags: [V] read in source or our own log; [I] inference. Paths: `server.py` = `data/src/adk_submission/adk_submission/server.py`; `arg_utils.py` = the vLLM 0.19.1 wheel's `vllm/engine/arg_utils.py`; README = `data/raw/HARNESS_README.md`.

## vLLM server

- The scorer (README 160-170, `setup_vllm_server` in `scripts/inference.py`, which is not on disk) sets tp 4, gpu_memory_utilization 0.90, max_model_len 32768, scheduler_reserve_full_isl False, the gemma4 tool and reasoning parsers, and LoRA right-sizing from `adapters/` [V].
- `server.py` `build_cmd` (lines 686-801) emits no `--max-num-seqs`, `--max-num-batched-tokens` or prefix-caching flag. `--speculative-config` is emitted only when set (746-750); the default is None [V].
- So vLLM defaults apply. Below 70 GiB device memory (the L4 is 24 GB), the API-server defaults are max_num_seqs 256 and max_num_batched_tokens 2048 (`arg_utils.py:2053-2072`) [V for our server; I for the scorer, which lists no override].
- Our 31B log (EXP-006) shows:
  - prefix caching and chunked prefill on;
  - speculative off;
  - the TRITON_ATTN backend forced;
  - 8.74 concurrent 32k sequences.

  The printed KV size of 46,352 tokens is not a per-sequence budget for this hybrid-attention model [V log, I reading]. The figures for the other variants are E4B 45.63x, 12B 19.97x and E2B 67.18x.
- Our notebook (`notebooks/kaggle_eval_l4x4.py:280-287`) matches the scorer on every memory and batching setting. It differs in two places: `max_loras` 8, which is moot with no adapters, and `default_chat_template_kwargs` with thinking on, which the README does not list [I].
- A submission can set none of these except through `adapters/` (`generate_content_config` has no `candidate_count` or `n`: `adk_submission/schema.py:179-202`, `extra="forbid"`) [V].

## Concurrency inside one task

- Only `ParallelAgent` issues concurrent model calls (`parallel_agent.py:51-85`, one asyncio TaskGroup) [V].
- Every branch's model call counts as a turn (`agent_runner.py:880-914`, `context.py:277-299`) [V].
- All branches share the one tool counter (`context.py:139-140,468-551`), `/workspace`, the task clock and compaction [V].
- A sync tool in any branch stalls all of them (EXP-007 H3, stall fraction 0.78) [V].
- `agent_tool` runs a new Runner with a fresh session service and no App (`agent_tool.py:241-249`), so the inner agent has no events compaction [V for the code]. The parent's plugins propagate (236-240), so its model events likely count as turns [I].
- Concurrent `agent_tool` calls happen only if one turn emits several function calls (`flows/llm_flows/functions.py:387-405`, asyncio.gather). 0 of 3,278 E0 tool-call steps did (`plan.md:997`) [V].
- Measured costs: EXP-006 (synthetic bursts), EXP-032 §9 and EXP-040 §9; the shapes are ranked in EXP-049 §9.2.
