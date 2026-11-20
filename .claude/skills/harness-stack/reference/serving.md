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
- `agent_tool` runs a new Runner with a fresh session service and no App (`agent_tool.py:241-249`), so the inner agent has no events compaction [V for the code]. The parent's plugins propagate (236-240).
- **`agent_tool` measured on Kaggle** [V] (2026-11-20, EXP-085 31B and EXP-086 E4B, smoke-8 each; `experiments/EXP-085/counter_check.py`).
  - **Tool counter.** The call to the `agent_tool` itself is not counted against `max_tool_calls`. The inner agent's counted tool calls are.
    - Over the 11 reader-using tasks, harness `tool_calls` equals the root's counted calls plus the inner calls in 9. It equals that sum plus the `agent_tool` calls in 0.
    - The 2 exceptions are E4B tasks that came out 1 below the sum.
    - So a reader costs the shared budget exactly its own reads.
  - **Trace.** The trace carries the inner agent's steps and calls inline, with `extra.author` set to the inner agent's name (the root's are `swe_agent`). The root's tool response is a separate step whose `observation.extra.tool_name` is the agent_tool name.
    - Split by `extra.author`. `analyze_traces.py` `n_calls` counts the inner calls as calls.
  - **Turns: still [I].** On 31B reader tasks the harness `llm_calls` exceeds the root's model steps. Step counts do not reproduce `llm_calls` even on reader-free E4B tasks, so how inner model events count as turns is unsettled.
  - **Failures seen.** One E4B `agent_tool` call without its `request` argument returned `{"status": "error", "error_type": "KeyError", ...}` as the tool response; the task went on.
  - **Prompt limit.** "One reader call per file, at most 3 files" was broken on 3 of 8 E4B tasks (5 to 6 calls), and on none of the 31B tasks (at most 2).
- Concurrent `agent_tool` calls happen only if one turn emits several function calls (`flows/llm_flows/functions.py:387-405`, asyncio.gather). 0 of 3,278 E0 tool-call steps did (`plan.md:997`) [V].
- Measured costs: EXP-006 (synthetic bursts), EXP-032 §9 and EXP-040 §9; the shapes are ranked in EXP-049 §9.2.
