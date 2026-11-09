# Agent routing in multi-agent trees: nudges, transfers, caps

Source-read 2026-11-09 for EXP-062 (desk check), confirmed by the EXP-061 smoke-8 traces. Paths are under
`data/src/` (gitignored). Line numbers are for the pinned wheels.

## Where a nudge re-run starts [V]

- The harness re-runs `run_async` on the same session with no `invocation_id` (`swegemma/harness/agent_runner.py:806-811`).
- ADK picks the agent with `_find_agent_to_run` (`google_adk/google/adk/runners.py:1082-1134`), called from
  `_setup_context_for_new_invocation` at 1299.
  - If the last event is a function response, it returns that call's agent (1107-1109).
  - Otherwise it walks the non-user events backwards, skipping agent_state and end_of_agent events (1111-1119). An event the root wrote returns the root (1120-1122).
  - Any other author is returned only if `_is_transferable_across_agent_tree` holds (1131-1132). That check walks up the parents and needs each one to have `disallow_transfer_to_parent` set to false (1136-1156). Sequential and Parallel agents do not have the attribute.
  - The fallback is the root (1133-1134).
- Consequence: in a tree whose working agents sit under a Sequential or Parallel parent, **every nudge re-run lands on the root**. EXP-061 `fastapi_14301` showed this in a trace: the nudge went to the transfer-only root.
- A re-run lands back on a working agent only in three cases:
  - an LlmAgent whose whole parent chain is transfer-capable LlmAgents;
  - a root that transfers again (EXP-062);
  - a Sequential root, which is the EXP-052 compaction crash.
- swegemma sets no resumability, so a SequentialAgent that is entered again restarts at sub-agent 0 (`google_adk/google/adk/agents/sequential_agent.py:61-67, 94-108`).

## Transfer tools [V]

- An LlmAgent with sub-agents gets `transfer_to_agent` (`flows/llm_flows/agent_transfer.py:47-63, 156-158`).
- Children of Sequential or Parallel agents get no route up (`agent_transfer.py:44, 160-163`).
- A transfer runs the target agent whatever its class (`flows/llm_flows/base_llm_flow.py:636-640`).
- `tools: []` on such a root leaves `transfer_to_agent` as its only tool. Any other call returns the ADK fixed error `Tool '<name>' not found. Available tools: transfer_to_agent` (EXP-061).
  - `analyze_traces.py` does not count a refused `submit_patch` as a submit since d1286b5 (EXP-062 §7 item 1).
  - `summary.jsonl` files made before that commit count it (EXP-061 `fastapi_14301`).
- `tools/validate_submission.py` checks a delegating root over the union of the tool names of every LlmAgent in the tree, since 3a05e08 (EXP-061).

## Nudge loop and caps [V]

- `max_nudges = 3` (`agent_runner.py:784`). The loop stops after 3 nudges in a row (965-971).
- The count resets after any turn that has a function call (962-963, with `has_function_call` at 832-839). A transfer counts as a function call, so a root that transfers on every nudge never reaches 3. Its passes are then bounded only by the time, call and turn caps [I].
- The cap checks:
  - time: 924-930, plus `asyncio.timeout` at 724-728;
  - tool calls: 932-946;
  - turns: 947-958.
- The nudge texts are at 983-1000.
- A cap hit does not throw the work away. `except (TimeoutError, LlmCallsLimitExceededError)` (1026-1038) only sets `agent_error`. If nothing was submitted, the code then falls through to the on-disk fallback (1054-1078): it diffs against `_swegemma_baseline`, strips protected files, and the result becomes the patch.
  - So a cap hit keeps a partial on-disk edit as the patch.
  - Only an empty diff gives the fixed message `Agent completed execution without calling submit_patch.`, and only when no cap error was already set (1080-1083).
