id: EXP-007-adk-parallel-probe        date: pending        owner: M4
hypothesis: EXP-006 established that a single-agent submission leaves most of an already-booted 31B
        vLLM server's KV-cache capacity idle (max_concurrency_32k=8.74, 88.6% idle under one request at
        a time). This experiment asks whether ADK's own `ParallelAgent` can actually exploit that
        capacity for real agent work, or whether something in ADK's own machinery serializes it anyway.
        H1: `ParallelAgent[analyzer_A, analyzer_B]` issues genuinely concurrent LLM requests to the vLLM
        server -- pass bar: the relay observes >=2 requests in flight simultaneously, and wall time for
        the parallel arm is <=0.75x the wall time of a sequential control doing the same two branches'
        worth of work. H2 (secondary, non-gating): whether multiple tool calls inside one LLM turn run
        serially (sync `FunctionTool`) vs concurrently (`AgentTool`) -- low real-world relevance since
        E0 traces show every one of 3,278 tool-call steps carries exactly one function call. H3: a long
        sync tool call in one branch (`slow_sync_tool`, a plain Python function that
        `FunctionTool._invoke_callable` calls directly on the event loop, confirmed at
        `data/src/google_adk/google/adk/tools/function_tool.py:223-238`) measurably stalls the sibling
        branch's progress, via both relay arrival timestamps and an explicit event-loop-lag monitor. H4:
        `RunConfig.max_llm_calls` is a single budget shared across all `ParallelAgent` branches, not a
        per-branch allowance (`google_adk/agents/run_config.py` declares it as a flat `int`, not a
        per-agent mapping).
single variable changed: n/a -- no real submission, no `eval_config.yaml`, no task cohort, no
        `evaluate_task`/`Evaluator` call anywhere. This is a read-only measurement of ADK's own
        concurrency behavior using synthetic agents (`analyzer_a`, `analyzer_b`, each a one-tool-call
        `LlmAgent`) built fresh for this probe and compiled via the real `compile_submission()` path, run
        against (a) a fake, scripted `/v1/chat/completions` relay (Stage 0, no GPU) and then (b) a real,
        harness-faithful 31B vLLM server reached through a thin proxying relay (Stage 1).
cohort: n/a -- no tasks. The "cohort" is 4 synthetic arms run twice (Stage 0 fake relay, Stage 1 real
        31B): `control-seq` (`SequentialAgent[analyzer_a, analyzer_b]`, both call `lookup_fact`),
        `parallel` (`ParallelAgent[analyzer_a, analyzer_b]`, both call `lookup_fact` -- H1), `parallel-
        sync-block` (`ParallelAgent[analyzer_a, analyzer_b]`, `analyzer_b` calls `slow_sync_tool`
        instead -- H3), and (Stage 0 only) `shared-budget` (`parallel` arm with
        `RunConfig(max_llm_calls=1)` -- H4).
        GPU-h used: Stage 0 is CPU-only (no GPU time). Stage 1 budget: 25 min soft / 40 min hard wall-clock
        cap (`GLOBAL_SOFT_BUDGET_S`/`GLOBAL_HARD_CAP_S`), ~0.2-0.3 L4x4 kernel-hours expected (31B boot
        ~6-7 min per EXP-006's `boot_s=376.5`, plus 3 short arms).
config: `notebooks/exp012_adk_parallel_probe/adk_parallel_probe.py` (source) ->
        `adk_parallel_probe.ipynb` (built via `tools/build_notebook.py`, not hand-edited).
        kernel: `rainm4/gemma4-exp012-adk-parallel-probe`
        (`notebooks/exp012_adk_parallel_probe/kernel-metadata.json`), same pinned docker image as
        EXP-006, `machine_shape: NvidiaL4`, `enable_internet: false`, wheelhouse + competition source
        attached, **only the 31B model** attached as `model_sources` (not all 4 -- this probe targets
        the worst-case/lowest-headroom model from EXP-006's results).

        **Why only `ParallelAgent[analyzer_A, analyzer_B]`, N=2, read-only sub-agents:** parallel
        *coding* agents were ruled out as unsafe before this experiment was designed -- every sub-agent
        in an ADK agent tree shares the same `/workspace`, and `submit_patch` diffs the whole workspace,
        so there is no sandbox isolation per branch that would make N>2 concurrent coding branches safe
        or meaningful to probe. This experiment only tests whether ADK's concurrency primitives work at
        all, using read-only synthetic agents, not whether parallel coding is viable.

        **Synthetic agents** (hand-built YAML submission trees under `runs/.../arms/<arm_id>/`, compiled
        via the real `adk_submission.compiler.compile_submission()`, not written by hand as Python
        objects): `analyzer_a.yaml`/`analyzer_b.yaml` (`SandboxedLlmAgentConfig`: `agent_class: LlmAgent`,
        `model: probe_model`, one-sentence instruction to call exactly one tool and echo its result,
        `tools: [lookup_fact]` or `[slow_sync_tool]`), `agent.yaml` (root, `SandboxedSequentialAgentConfig`
        or `SandboxedParallelAgentConfig` per arm, `sub_agents: [{config_path: analyzer_a.yaml}, ...]`).
        Tools are plain Python functions (`lookup_fact(key) -> str` returns instantly;
        `slow_sync_tool(seconds) -> str` does `time.sleep(seconds)`) registered into a `ToolRegistry`.
        `ModelRegistry` registers a single alias (`probe_model`) to a `LiteLlm(model=f'openai/{id}',
        api_base=<relay base_url>, api_key='EMPTY')`, pointed at a relay rather than vLLM directly.

        **Relay process** (`subprocess.Popen`, stdlib `http.server.ThreadingMixIn` so it has its own
        process/GIL and stays responsive independent of whatever the main process's asyncio loop is
        doing): serves `/v1/chat/completions` and `/v1/models`. In `fake` mode (Stage 0) it scripts a
        canned tool-call-then-stop response with an artificial `FAKE_LATENCY_S=2.0` sleep per request
        (long enough to show real overlap vs serialization without burning wall time) and needs no GPU.
        In `proxy` mode (Stage 1) it forwards each request to the real vLLM server's own `base_url +
        '/chat/completions'` (confirmed exact path shape via
        `data/src/adk_submission/adk_submission/server.py` -- `VllmServer.base_url` returns
        `f"http://{host}:{port}/v1"`) and returns the real response unmodified. Every request, in both
        modes, is logged as one JSON line (`t_arrive`, `t_depart`, `in_flight_at_arrive`) -- this is the
        ground truth for "how many requests were simultaneously in flight," independent of what ADK
        itself reports. vLLM's own `/metrics` is not proxied or faked; Stage 1 could poll it directly
        against the real server's `host:port` if needed, but this probe does not use it (relay-observed
        concurrency is the gating signal for H1).

        **Instrumentation**: `ExpTimingPlugin(BasePlugin)` (exact callback signatures confirmed from
        `data/src/google_adk/google/adk/plugins/base_plugin.py`) records a timestamped event per
        `before_model_callback`/`after_model_callback`/`before_tool_callback`/`after_tool_callback`, tagged
        with the branch (`callback_context._invocation_context.branch`, confirmed set by
        `ParallelAgent._create_branch_ctx_for_sub_agent` as `f'{branch}.{agent.name}.{sub_agent.name}'`)
        and agent name. A separate `loop_lag_monitor` coroutine runs alongside the driven `run_async`
        call, scheduling a 50 ms wakeup and recording how late it actually fires -- a sync tool call
        blocking the event loop (H3) shows up here as a lag spike, independent of relay timestamps.

        **Driving a run**: `App(name=<arm_id>, root_agent=compile_submission(...), plugins=[plugin])` +
        `Runner(app=app, session_service=InMemorySessionService())` (the sanctioned non-deprecated
        construction path, confirmed via `data/src/google_adk/google/adk/runners.py` --
        passing `agent=`/`plugins=` directly alongside `app=` raises `ValueError`) +
        `runner.run_async(user_id=..., session_id=..., new_message=..., run_config=RunConfig(max_llm_calls=N))`
        driven to completion via a `run_sync` helper (same pattern as `notebooks/kaggle_eval_l4x4.py`).

        Designed by an Opus/high-effort subagent (full arm/hypothesis design in this session's
        transcript; implemented and arm set reduced for time budget by Sonnet against this doc, after
        independently re-reading every vendored `google_adk`/`adk_submission` source file the design
        relies on -- `parallel_agent.py`, `function_tool.py`, `agent_tool.py`, `base_plugin.py`,
        `run_config.py`, `compiler.py`, `schema.py`, `builders/workflows.py`, `registry.py`,
        `builders/llm.py`, `builders/sub_agents.py`, `limits.py`, `runners.py`, `apps/app.py`,
        `sessions/in_memory_session_service.py`, `discovery.py` -- to verify every constructor field,
        schema shape, and root-config filename convention (`agent.yaml`, not an invented name) before
        writing any implementation code.
        **Reduction from the original design, noted explicitly**: the original design specified
        Stage-0 arms S0-A0..S0-H4 and Stage-1 arms A0-A4 (including an `AgentTool`-based H2 arm and a
        bonus arm). Given H2's low real-world relevance (0 multi-call tool steps observed in 3,278 E0
        steps) and the wall-clock budget, this implementation runs a reduced set: Stage 0 =
        {control-seq, parallel, parallel-sync-block, shared-budget(H4)}; Stage 1 = {control-seq,
        parallel, parallel-sync-block}. H2's `AgentTool` arm is deferred to a follow-up only if H1 passes
        and EXP-008 surfaces a concrete reason to revisit it.
results: **RUN COMPLETE 2026-10-20** (kernel v2, after a v1 crash and bugfix -- see note below), kernel
        `rainm4/gemma4-exp012-adk-parallel-probe`, COMPLETE, `total_wall_s = 766.6` (12.8 min, well
        inside the 25 min soft budget). 31B vLLM booted cleanly (harness-faithful recipe, same as
        EXP-006). All Stage 0 and Stage 1 control/parallel/sync-block arms ran to completion
        (`status: "ok"`); the Stage-0 `shared-budget` (H4) arm errored (see H4 below).

        **v1 crash and fix, noted for the record**: the first push (v1) died partway through
        `s0-control-seq` because the fake relay's handler assumed OpenAI-style `content` fields were
        always a plain string and called `.lower()` on one that was actually a list of
        `{"type": "text", ...}` parts (`AttributeError: 'list' object has no attribute 'lower'`); the
        uncaught exception killed the relay's HTTP response mid-request, which cascaded into a
        `litellm.InternalServerError` on the client side, and with no per-arm exception handling in
        the Stage-0/Stage-1 loops, that one error crashed the whole kernel before any other arm ran.
        v2 added an `_as_text()` helper for list-shaped content, a relay-side `try/except` returning a
        clean 500 instead of dropping the connection, and per-arm `try/except` in both the Stage-0 and
        Stage-1 loops so one bad arm records an error row and the run continues (Stage-1 arms run
        after a ~6-7 min GPU boot, so losing the rest of the run to one bad arm would have wasted real
        GPU-quota as well as wall time).

        | arm | wall_s | relay_max_in_flight | relay_n_requests | max_lag_s |
        |---|---|---|---|---|
        | s0-control-seq | 5.105 | 1 | 2 | 0.674 |
        | s0-parallel | 2.019 | 2 | 2 | 0.0002 |
        | s0-parallel-sync-block | 2.019 | 2 | 2 | 0.0010 |
        | s0-shared-budget (H4) | ERROR | -- | -- | -- |
        | s1-control-seq | 5.452 | 1 | 4 | 0.0020 |
        | s1-parallel | 1.122 | 2 | 4 | 0.0010 |
        | s1-parallel-sync-block | 1.997 | 2 | 4 | **0.961** |

        **H1** (`ParallelAgent` issues genuinely concurrent LLM requests): **CONFIRMED** on real 31B.
        `relay_max_in_flight = 2` for both `s1-parallel` and `s1-parallel-sync-block` (vs 1 for
        `s1-control-seq`), and `wall_ratio_parallel_over_control = 0.206` on Stage 1 (well under the
        0.75 pass bar) -- the parallel arm's two branches genuinely overlap on the wire, not just in
        ADK's own bookkeeping. Stage 0 (fake relay) showed the same qualitative pattern
        (`wall_ratio = 0.395`, `max_in_flight = 2`), confirming the effect isn't an artifact of the real
        vLLM server's batching.

        **H2** (sync `FunctionTool` vs. concurrent `AgentTool` tool dispatch): deferred, not run (see
        reduction note above) -- no data this run.

        **H3** (a long sync tool call in one branch stalls the sibling branch): **CONFIRMED, and the
        cost is significant, not small.** On Stage 1, `s1-parallel-sync-block` (`analyzer_b` calls
        `slow_sync_tool`, a 1s `time.sleep`) took 1.997s wall vs. 1.122s for the matched `s1-parallel`
        arm with no sync tool -- `h3_projected_stall_frac = 0.780` (vs the `<=0.10` pass bar), i.e. the
        parallel arm got ~78% slower once one branch made a 1-second blocking call. The event-loop-lag
        monitor corroborates this independently of relay timestamps: `max_lag_s` jumps from ~0.001s in
        every other real-vLLM arm to **0.961s** in `s1-parallel-sync-block` -- almost exactly the
        `slow_sync_tool`'s 1-second sleep duration shows up as a single missed event-loop tick, direct
        evidence that `FunctionTool._invoke_callable` calling a sync tool directly on the event loop
        (confirmed at `function_tool.py:223-238`) blocks the whole loop, including the sibling
        `analyzer_a` branch's own concurrent LLM call, for the full duration of the sync tool.

        **H4** (`RunConfig.max_llm_calls` shared vs. per-branch budget): **inconclusive from this arm.**
        `s0-shared-budget` (`parallel` arm, `max_llm_calls=1`) raised
        `ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)` rather than completing.
        This confirms a budget of 1 is insufficient for two branches that each need 2 LLM calls, but
        with `max_llm_calls=1` the shared-budget and per-branch-budget hypotheses predict the *same*
        failure (both would exhaust after the first call), so this specific arm doesn't distinguish
        them. A cleaner follow-up would use `max_llm_calls=2` (shared-budget hypothesis predicts
        failure -- 1 call per branch isn't enough for either branch to finish; per-branch hypothesis
        predicts success) -- not run here, low priority since H4 isn't gating for the decision below.
per-repo: n/a -- no task repos involved in this experiment.
decision: **H1 PASS, H3 cost significant → proceed to EXP-008 only after making swegemma's sync tools
        async first.** Per the pre-registered rule: H1 passed cleanly on real 31B
        (`max_in_flight=2 >= 2`, `wall_ratio=0.206 <= 0.75`), which rules out building EXP-008 directly
        on top of today's synchronous tool implementations -- the sibling-branch stall measured under
        H3 (`h3_projected_stall_frac=0.780`, `max_lag_s=0.961s`) is large enough that a real
        `ParallelAgent[analyzer_A, analyzer_B]` wrapping swegemma's actual tools (`run_command`, etc.,
        every one of which is sync today) would likely lose most of the concurrency benefit to
        event-loop stalls on real tasks, where tool calls (e.g. `pytest`) can run far longer than this
        probe's synthetic 1-second `slow_sync_tool`. This matches `summary.json.decision_hint` exactly:
        "H1 PASS but H3 (sync-tool stall) cost is significant -- proceed to EXP-008 only if swegemma
        tools are made async first."
follow-ups:
  1. Done 2026-10-20: kernel pushed (v1 crashed on a relay bug + no per-arm exception handling, fixed
     and re-pushed as v2), `summary.json`/`stage0.json`/`stage1.json` retrieved into
     `runs/EXP-007-adk-parallel-probe/` (gitignored), results/decision above and
     `experiments/README.md` §3 filled in with the real figures.
  2. **Next concrete step, per the decision above**: scope and build the "make swegemma's sync tools
     async" follow-up (likely wrapping `run_command` et al. in `asyncio.to_thread` or similar) *before*
     attempting EXP-008 -- not yet scoped. EXP-008 itself
     (`SequentialAgent[ParallelAgent[analyzer_A, analyzer_B], swe_coder]` vs E0 on dev-48) stays gated
     on that follow-up landing first, per the decision rule.
  3. H2 (`AgentTool`-based concurrent tool dispatch) remains deferred given its low observed
     real-world relevance (0/3,278 E0 tool-call steps carry more than one function call). Revisit only
     if the async-tools follow-up or EXP-008 surfaces a concrete reason multi-tool-call turns matter.
  4. H4 (shared vs. per-branch `max_llm_calls` budget) is still open -- the `max_llm_calls=1` arm run
     here can't distinguish the two hypotheses (see H4 above). Low priority: revisit only if a future
     experiment's budget accounting depends on the answer.
