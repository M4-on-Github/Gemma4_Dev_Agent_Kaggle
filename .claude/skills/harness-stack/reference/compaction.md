# Context compaction in the scorer (Q7), 2026-11-05

These facts come from reading `data/src/` (ADK 1.36.1, `swegemma`) and `data/raw/HARNESS_README.md` §7.2. Tags:
**[V]** official doc or source on disk, **[M]** community or GitHub, **[I]** inference.

## Settings

| What | Scorer | Our eval notebook | Tag |
|---|---|---|---|
| `EventsCompactionConfig` | interval 15, overlap 2, token_threshold 14,336, event_retention_size 5 | same values (`COMPACTION_INTERVAL`, `COMPACTION_TOKEN_THRESHOLD`, `make_config`) | [V] README §7.2; the scorer's `scripts/inference.py` is not on disk |
| `ContextCacheConfig` | min_tokens 2,048, ttl 1,800 s, cache_intervals 10 | same | [V] README §7.2 |
| Plain `swegemma` CLI / `EvalConfig` default | `events_compaction_config = None`, so compaction is off unless the runner passes it | n/a | [V] `swegemma/config.py:118` |

The constants are mirrored in `tools/submission_rules.py` (`COMPACTION_*`).

## What triggers it

- **Token threshold.** `flows/llm_flows/compaction.py` is a request processor in `SingleFlow`, so it runs before **every** model call of **every** `LlmAgent`, sub-agents included [V].
  - It reads the most recent session event that carries `usage_metadata.prompt_token_count`. The scan does not filter by branch or author (`apps/compaction.py` `_latest_prompt_token_count`) [V].
  - If that count is ≥ 14,336, it summarizes every raw event except the last 5 [V]. Before the cut, the split moves earlier so that a retained function response keeps its call, and the cut also stops before any pending (unanswered) function call [V].
- **Sliding window** (interval 15 user-initiated invocations, overlap 2). This runs only after an invocation ends (`runners.py:598`), and it is skipped when a token compaction already ran in that invocation [V].
  - Each task is a single `run_async` invocation, plus one more per nudge, and nudges stop after 3 consecutive. So it practically never fires [I].
- **Measured.** EXP-028 Arm R had 49 compactions in 36 of 48 tasks, and RH had 49 in 35 of 48 (EXP-028 §7 D5). Every one fired right after a turn at ≥ 14,336 prompt tokens.

## The summarizer call

- One extra model call through `LlmEventSummarizer(llm=agent.canonical_model)`, which is the model of the first agent that triggers it. The summarizer is then cached on the shared config object [V].
- The request carries no `generate_content_config`, so the agent's sampling and `max_output_tokens` do not apply [V].
- The summary contains only the **text parts** of the compacted events. Function calls and tool outputs older than the retained 5 events leave the model's view [V] (`_format_events_for_prompt`).
- **It counts against the task clock.** It runs inside `runner.run_async` within `agent_runner`'s `async with timeout_context` [V].
- **It is not a turn.** `llm_calls_used` counts only events yielded to the plugin, and the summary event is appended directly to the session, never yielded [V]. It bypasses `ModelRetryPlugin` and `max_llm_calls` [I].
- **It is not in the trace.** The same appended-not-yielded path means no trace step records it. `analyze_traces.py` therefore detects it as a prompt-token drop, using `count_token_compactions` [V; 0 compaction steps in 96 EXP-028 traces].

## Sub-agents and ParallelAgent (ADK issue 7324 [M])

- Sub-agents compact [V]. All agents of a task share one session, and `ParallelAgent` gives each child a branch `parent.child` [V].
- The summary event has `branch=None`, so it is visible in **every** branch [V] (`_is_event_belongs_to_branch`). `_process_compaction_events` then hides every raw event whose timestamp falls inside the compacted range, whichever branch wrote it [V].
- Issue 7324 [M] is `ValueError: No function call event found for function responses ids`. It is raised in `contents.py` when the latest function response has no matching call left in the context.
- **What in the scorer's settings makes it more likely** [I, from the source above]:
  - The threshold is low: 14,336 is 44% of the 32k window, and it fired in 75% of our single-loop tasks.
  - Any branch's large prompt triggers compaction for all branches, so the first localizer to cross the threshold compacts its siblings' history too.
  - Retention is small (5 events) across interleaved branches.
  - The summarizer takes seconds of model time while sibling branches keep appending call and response events.
- **What makes it less likely:**
  - Every agent's prompt staying under 14,336: ranged reads, short instructions, a stated call allowance per localizer.
  - Fewer function-call events in flight during the parallel stage.
  - No `ParallelAgent` at all. The sequential case shares the session but has no concurrent appends.
- Blast radius is one task. `agent_runner` catches the exception and harvests the on-disk diff (EXP-030 critic.md item 4) [I].

## What a submission controls

- **No direct control over the settings.** `EventsCompactionConfig` is an `App` argument set by the scorer, and no `agent.yaml` key reaches it (`R.LLM_AGENT_KEYS`) [V].
- **Indirect control, through anything that keeps the latest prompt below 14,336 tokens** [I]:
  - prompt length;
  - `read_file` ranges;
  - per-agent `generate_content_config.max_output_tokens`;
  - `include_contents: none` on a sub-agent, so it is not sent the earlier session history (an allowed `LlmAgent` key, `adk_submission/schema.py:284`; its exact scope is unverified);
  - topology: whether a `ParallelAgent` exists.
