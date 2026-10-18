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
results: TBD — fill in from tools/analyze_traces.py once the kernel finishes (resolve, phase_histogram,
        time_cap_hit vs calls_cap_hit, per-repo).
decision: TBD. If phase_reached clears the 80% bar on smoke-8 with no resolve regression, proceed to the full
        dev-48 run before deciding adopt/escalate (n=8 is a screening signal, not the "done" criteria evidence
        — those require dev-48 per plan.md §6.1). If phase_reached barely moves even on this easy a cohort,
        that is itself informative (structural fix insufficient) and worth a quick look before burning a
        dev-48 run on it.
follow-ups: TBD.
