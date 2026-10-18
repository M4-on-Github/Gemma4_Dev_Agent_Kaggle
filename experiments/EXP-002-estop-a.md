id: EXP-002-estop-a (= E-STOP(a'), plan.md §6.0.2/§6.1)        date: 2026-10-18        owner: M4
hypothesis: replacing the open-ended grep-first LOCATE phase with a fixed, non-agentic 4-call sequence
            (identifier extraction -> search_similar_code -> get_code_neighbors -> get_code_subgraph ->
            read_file) gets >= 80% of tasks to phase_reached in {EDIT, VERIFY, SUBMIT}, vs E0's 46% (22/48),
            without a net resolve-rate regression.
single variable changed: LOCATE step of submission/prompts/swe_coder.md only (`# Protocol` step 1); REPRODUCE/
        EDIT/VERIFY/SUBMIT and the budget-ledger section are byte-identical to EXP-001-baseline's config.
cohort: smoke-8 first (experiments/cohorts/smoke-8.txt, seed=20261013) as a cheap screening pass before
        spending a full dev-48 run — fastapi 3 / rich 2 / requests 2 / httpx 1.        GPU-h used: TBD
config: HEAD d87806f with the E-STOP(a') LOCATE rewrite already committed (this commit, not a working-tree
        diff on top of it).
        zip sha256 (tools/pack_submission.py): 18e9e29c45b79a3a6850b16beade9efebff356ee22be55367038bea500f17330
        kernel: rainm4/gemma4-exp009-estop-a-smoke8 (notebooks/exp009_estop_a_smoke8/), pushed 2026-10-18,
        version 1
        eval_config: 4.5 min / 45 calls / 70 turns / 300 s ; sampling: T 0.2, top_p 0.95, top_k 64,
        max_output_tokens 4096, thinking on, thinking_budget 256 (unchanged from E0)
results: kernel COMPLETE (v1, 2026-10-18). Gold control (RUN_GOLD_CONTROL, reference patch replayed, no model)
        found only **4/8 smoke-8 tasks sound**: fastapi_14448, fastapi_14301, rich_3468, rich_3006 passed;
        requests_7309, requests_7205, httpx_3672, fastapi_14605 failed gold and were skipped (same
        soundness-filter mechanism as experiments/README.md Q5). Agent ran on the 4 sound tasks only.
        resolve 2/4 = 50.0% (Wilson 95% CI 15–85%, n too small to compare to E0's 22.9% point estimate).
        empty patch 25%, timeout 50%, time-cap 75%, calls-cap 0%, submit_patch called 25% (1/4, rich_3006;
        the other 3 — including both resolves, fastapi_14301 and rich_3006 — never called submit_patch
        inside budget; the harness still graded the on-disk workspace diff at session end, so an uncalled
        submit_patch did not cost fastapi_14301 its resolve). wall median 4.55 min, p90 4.58 min.
        phase_histogram (regex over the agent's own `[phase=...]` ledger line): {LOCATE 3, EDIT 1}.
        **Critical caveat on that phase_histogram, found by reading the raw traces directly:** all 4 agents
        stop emitting the ledger bracket line almost immediately — 1–3 tags total out of 19–39 agent turns,
        the last one still saying `LOCATE` even while the trace's own tool-call sequence shows `edit_file`
        and `pytest` calls well underway (rich_3006 is the sole task that updated its tag to `EDIT`, once,
        at turn 25). So `phase_reached` is not measuring real phase progress here, it is measuring how long
        the model keeps bothering to maintain the ledger convention before abandoning it — this calls E0's
        "54% stuck in LOCATE" headline finding into question too, since it used the identical regex. The
        plan.md §6.1 "done" criterion (phase_reached ∈ {EDIT,VERIFY,SUBMIT} ≥ 80%) is not a trustworthy metric
        as currently instrumented and needs a harness-side signal (e.g. last tool-call family used, or a
        get_status-derived phase) instead of a self-reported bracket tag, before it can gate any decision.
        **The actual mechanism the LOCATE rewrite was supposed to force never fired: `get_code_neighbors` and
        `get_code_subgraph` were called zero times across all 4 traces**, and `search_similar_code` itself was
        skipped entirely in the one task (rich_3006) that resolved fastest. In every trace the model instead
        fell straight back into `run_command`-heavy exploration (grep/cat-style) + `read_file` loops — the same
        shape of behavior E-STOP(a') was designed to replace. The prompt rewrite changed the LOCATE *text*,
        not the agent's actual tool-call choices: a fixed sequence written as instructions is optional advice
        the model is free to ignore, not a structural constraint.
decision: **Do not proceed to the full dev-48 run on this prompt-only implementation of E-STOP(a') — the
        n=4 smoke screen already shows the intervention isn't reaching its own mechanism** (0/4 traces touch
        get_code_neighbors/get_code_subgraph), so a dev-48 run would mostly be re-measuring E0's grep-driven
        behavior under a relabeled LOCATE section, not testing the hypothesis. Before spending a dev-48 run on
        any LOCATE redesign, first address: (a) the phase_reached instrumentation (recompute it from tool-call
        family / get_status calls, not the self-reported ledger tag) so later "done" criteria checks are
        trustworthy, and (b) actual enforcement of the fixed call sequence — e.g. temporarily restricting which
        tool names are offered during an explicit LOCATE sub-turn budget, or a harness-side check that fails
        LOCATE after N calls if get_code_neighbors/get_code_subgraph haven't been called — rather than relying
        on prompt text alone. The resolve rate itself (2/4 = 50%, n too small to read as a regression or an
        improvement over E0's 22.9%) is not the limiting signal here; the compliance failure is.
follow-ups:
  1. Fix phase_reached instrumentation in tools/analyze_traces.py (or in the harness trace schema) to derive
     phase from observed tool-call family/order, not the agent's self-reported bracket line — re-run this
     check against E0's existing dev-48 traces too, since "54% stuck in LOCATE" may shrink or grow once
     measured correctly.
  2. Re-design E-STOP(a') (call it E-STOP(a'')) with an actual enforcement mechanism for the fixed LOCATE
     sequence rather than prompt instructions alone, then re-screen on smoke-8 before any dev-48 spend.
  3. gold control failed 4/8 on smoke-8 (same ~50% unsound rate pattern worth tracking per cohort — note in
     experiments/cohorts/README.md if this recurs on dev-48 gold reruns).
  4. E0's Kaggle leaderboard score is still pending (submitted 2026-10-18); record it in EXP-001-baseline.md
     once grading completes.
