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

## Hazard: a root that is not an `LlmAgent` can crash post-invocation compaction (EXP-052, source read 2026-11-08)

Read from `data/src/` (ADK 1.36.1, swegemma 0.2.11). EXP-052 recorded it as [I] in its section 7 item 12; this section settles it. The error is the ADK's fixed `ValueError` text "No LlmAgent model available for event compaction summarizer." The harness catches it as a sandbox execution error and harvests the on-disk diff (`agent_runner.py:1039-1043`) [V].

**(a) It is not raised whenever the root is not an `LlmAgent` and the prompt passes 14,336.** [V] It is raised by `_ensure_compaction_summarizer` (`apps/compaction.py:223-236`), and only the post-invocation path hands that function `app.root_agent`: the token path at `:589-590` and `:475-490`, the sliding-window path at `:683`. All of these must hold:
1. the `run_async` invocation runs to its end (`runners.py:598-610`);
2. no in-flow token compaction fired during that invocation. A successful in-flow compaction sets `token_compaction_checked` (`flows/llm_flows/compaction.py:52-53`), which the runner passes as the skip flag (`runners.py:609`);
3. the latest `prompt_token_count` in the session is at least `token_threshold`. That count is read from any branch or author (`apps/compaction.py:156-173`, `:448`);
4. there are events to compact (`:451-456`);
5. no summarizer is cached on the compaction config yet (`:227-228`);
6. the root is not an `LlmAgent` (`:231-234`).

The sliding-window path reaches the same check only after 15 new invocations (`:632-633`), which a task does not reach [I].

**The summarizer is cached across tasks.** [V for the code; the same-object point rests on pydantic's default handling of a model instance passed as a field, not run.]
- `:236` stores the summarizer on the config object, and the harness hands the same `EvalConfig.events_compaction_config` object to every task's `App` (`agent_runner.py:694-695`).
- Our eval notebook builds one `EvalConfig` per run (`notebooks/kaggle_eval_l4x4.py:331-345`, `:399`). So in our notebook the hazard can fire only before the first token compaction of the whole run. After that, the cached summarizer (the first compacting agent's model) serves the root.
- EXP-052 fits this: its one compaction, `rich_3468`, came after `httpx_3672` in kernel order.
- Whether the scorer shares one config across tasks or shards is not on disk [I]. So on the hidden set the hazard is order-dependent, and a clean dev run does not rule it out.

**(b) Two triggers, neither of them per event.** [V]
- **In-flow:** a request processor in `SingleFlow` (`flows/llm_flows/single_flow.py:49`, `flows/llm_flows/compaction.py:32-54`) runs before each model call of each `LlmAgent`. It passes that `LlmAgent`, so it cannot raise this error.
- **Post-invocation:** this runs once per `runner.run_async` invocation, after the last event is yielded (`runners.py:598-610`; the source comment says it never compacts mid-invocation). Each task is one invocation, plus one per nudge (`agent_runner.py:788-806`).
- **What only the post-invocation path sees:** the in-flow check reads the count left by the previous model call. So a prompt over the threshold on the invocation's last model call is seen only by the post-invocation path.

**(c) A `submit_patch` call does not itself end the loop.** [V] It only sets the flag (`tools/execution.py:111-112`).
- **The breaks that leave the loop early:** the harness breaks out of the event loop at the first final text event after the flag is set (`agent_runner.py:854-864`), and on the session timeout (`:866-874`). Such a break leaves `run_async` suspended before `runners.py:598`, and the compaction there is not in a `finally`, so it is never reached [V source; generator semantics].
- **Why `:920-922` does not protect:** that check comes after the loop has ended, so the post-invocation path has already run by then.
- **Consequence:** a stage that calls `submit_patch` and then answers in text is safe. An invocation that ends naturally is exposed. That covers a text ending before any submit, which is EXP-052's applier on `httpx_3672`, and every nudge re-run of the tree. An invocation that ends after a submit with no final text event would also be exposed [I, not seen].

**(d) Shapes that avoid it.**
- **An `LlmAgent` root** [V]: the post-invocation path then builds the summarizer from that agent's model (`apps/compaction.py:229-236`).
- **`agent_tool`** [V]: it runs its inner tree in its own `Runner` with no `App` (`tools/agent_tool.py:241-249`). Neither compaction path runs inside it (`runners.py:601`, `:1429`), so a Sequential or Parallel tree there is never compacted. Its prompts are then bounded only by the 32k window.
- **A ParallelAgent in `sub_agents` of an `LlmAgent` root** runs only if the root's model transfers to it [I]. The root stays an `LlmAgent`, so this error cannot occur.
- **No `agent.yaml` key can set a summarizer** [V]: `EventsCompactionConfig` is an `App` argument the harness takes from `EvalConfig` (`agent_runner.py:687-697`), and no `agent.yaml` key reaches it (section "What a submission controls").
- **Mitigation on a non-`LlmAgent` root** [I]: keep the last model call of every invocation below 14,336 prompt tokens, and make the final stage submit and then end in text, so the break at `:854-864` applies. Nudge re-runs stay exposed.
