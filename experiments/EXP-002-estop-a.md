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
        **`get_code_neighbors`/`get_code_subgraph` were called zero times across all 4 traces** — step (b),
        `search_similar_code`, WAS followed: it was the first call in fastapi_14301 and fastapi_14448 and the
        second call in rich_3468; only rich_3006 (the fastest-resolving task) skipped it. **Correction,
        2026-10-18, after a second independent trace read (see `experiments/README.md` §1o):** this session's
        first pass mischaracterized this as the model "falling straight back into `run_command`-heavy
        exploration" / ignoring the sequence as "optional advice" — that overstates the evidence. Reading the
        tool *outputs*, not just the tool *names called*, the chain instead broke after step (b) because step
        (b)'s output was unusable in all 3 cases that reached it: fastapi_14448's lexical-fallback query
        returned junk (`scripts.notify_translations.PartialGitHubEvent`, similarity 0.22); rich_3468's
        exact-symbol query for `rich.console.Console.print` returned the wrong node at a deceptively high
        similarity (`tests.test_table.render_tables`, 0.9997); fastapi_14301 is the inverse case — it got the
        correct answer directly from (b), making the later `get_code_neighbors`/`get_code_subgraph` steps
        genuinely redundant, not skipped out of non-compliance. Abandoning the chain after bad-or-already-
        sufficient step-(b) output is a plausibly *rational* response to what the tool actually returned, not
        evidence the model disregards prompt instructions. **This means the compliance-failure framing below
        is not well-supported; the more likely bottleneck is `search_similar_code` output quality/recall**
        (lexical-fallback junk, or high-similarity-but-wrong exact-symbol matches) — not tested yet against the
        real mounted graph/embedding data (the 58–65% recall figure in `plan.md` §6.0.2 is from a hand-ported
        scoring script, not the real tool). `get_code_neighbors`/`get_code_subgraph` genuinely never fired in
        any of the 4 traces either way, so that half of the original finding stands.
decision: **Do not proceed to the full dev-48 run on this prompt-only implementation of E-STOP(a') — the
        n=4 smoke screen doesn't exercise the chain's later steps often enough to say anything about them, and
        reading the trace outputs (not just call counts) suggests the limiting factor is more likely
        `search_similar_code` recall quality than prompt-instruction non-compliance (see correction above).**
        Before spending a dev-48 run on any LOCATE redesign, first run a **free, CPU-only check (no GPU spend)**
        that calls the real `search_similar_code`/`get_code_neighbors`/`get_code_subgraph` against the actual
        mounted graph/embedding data for every sound task, checking recall against the gold-patch function
        directly — not a hand-ported scoring script — before deciding whether a graph-tools-first LOCATE
        redesign (prompt-only or sub-agent) is even premised correctly. Also still needed regardless of that
        result: (a) fix the phase_reached instrumentation (recompute from tool-call family/get_status calls,
        not the self-reported ledger tag) so later "done" criteria checks are trustworthy. The resolve rate
        itself (2/4 = 50%, n too small to read as a regression or an improvement over E0's 22.9%) remains
        uninformative either way.
follow-ups:
  1. Fix phase_reached instrumentation in tools/analyze_traces.py (or in the harness trace schema) to derive
     phase from observed tool-call family/order, not the agent's self-reported bracket line — re-run this
     check against E0's existing dev-48 traces too, since "54% stuck in LOCATE" may shrink or grow once
     measured correctly.
  2. Run the free CPU-only recall check (real `search_similar_code`/`get_code_neighbors`/`get_code_subgraph`
     against real mounted graph/embedding data, gold-patch-function recall) before any further LOCATE redesign
     work — this is the direct follow-up to the 2026-10-18 correction above, and should happen before EXP-003b
     is built, since a graph-only sub-agent is handicapped by design if the underlying tools don't recall well.
     **Done, 2026-10-18 (see experiments/recall_check/README.md), both halves.** Local-first half: AST-diff
     gold extraction (129/129 tasks, 0 parse errors) and a `git grep` lexical baseline (24.8%/35.4%/37.2%/41.6%
     recall@1/3/5/10 on 113 scorable tasks). Kaggle CPU-only kernel half (`notebooks/exp_recall_check/`,
     kernel `rainm4/gemma4-recall-check`, COMPLETE, 0 GPU-h): replayed the real `search_similar_code`/
     `get_code_neighbors` against the actual mounted graph/embedding data on the identical 113-task set.
     **Result: the real tool loses to the free grep baseline at every k** — single-identifier arm
     14.2%/19.5%/21.2%/24.8%, joined-top-3 arm 16.8%/23.9%/28.3%/34.5%, both below grep's 24.8%/35.4%/37.2%/
     41.6%; `get_code_neighbors` chain hit rate only 16.5%. Two measured root causes: (a) only 62.7% of gold
     symbols exist as graph nodes at all (`gold_in_graph_rate`/`gold_has_embedding_rate`), a hard ceiling no
     ranking strategy can fix; (b) embedding-space anisotropy is real and repo-wide, not n=1 noise — mean
     pairwise cosine 0.72–0.85 (fastapi), 0.82–0.88 (requests), 0.87–0.93 (rich, confirming rich_3468's
     0.9991–0.9997 trace finding generalizes). The 3-trace cross-check against EXP-002's own traced queries
     lines up with both the local grep baseline and this full-dataset Kaggle result (fastapi_14301
     grep/lexical-fallback both rank gold 1st; fastapi_14448 both miss; rich_3468's tied grep ranking echoes
     the cosine near-constant-similarity problem). **This is real evidence against building EXP-003b as-is —
     a sub-agent wrapper inherits the same ~37% node-coverage ceiling and anisotropic embedding space; it
     would not fix either cause.**
  3. **Superseded, 2026-10-18 — do not build EXP-003b on the current graph tools.** (2)'s Kaggle result shows
     `search_similar_code`/`get_code_neighbors` losing to a free grep baseline at every k, with two measured
     root causes (62.7% gold-node coverage ceiling; real repo-wide embedding anisotropy) that a sub-agent
     wrapper around the same tools would inherit unchanged. Before any further LOCATE redesign spend, the open
     question is whether to (a) fix the underlying tools (graph coverage gap, embedding quality) or (b) use a
     lexical-first LOCATE step (grep for candidates, graph only for neighbor expansion once seeded) — not
     whether to wrap them in a sub-agent. `plan.md` §6.0.3/§6.0.4's sub-agent design fixes (root-agent
     delegation compliance, session-state passthrough, output contract, per-call budget cap, dry-run trace
     verification) remain relevant if a sub-agent is ever built on improved tools, just not now.
     **Correction, 2026-10-19 (independent review):** the 62.7%/anisotropy numbers above have real measurement
     bugs (query-extraction regex returning `github.com` as "the identifier" for most tasks; a `src.`-prefix
     node-name mismatch deflating requests/httpx coverage) — see `experiments/recall_check/README.md`'s
     2026-10-19 correction for detail. The **decision to drop EXP-003b still stands**, but on firmer footing
     than those two numbers: reading real E0 dev-48 traces directly shows the actual bottleneck is
     **post-LOCATE** (a touch→edit→resolved drop-off that's wall-clock-bound, not LOCATE-quality-bound) — a
     tool-scoped sub-agent would spend budget narrowing a step that usually isn't where tasks are being lost,
     independent of exactly how good `search_similar_code`'s recall turns out to be once the bugs are fixed.
  4. gold control failed 4/8 on smoke-8 (same ~50% unsound rate pattern worth tracking per cohort — note in
     experiments/cohorts/README.md if this recurs on dev-48 gold reruns). Also noted independently: smoke-8
     yields only 4 gradeable tasks per run; a cohort drawn from tasks already known to pass gold control would
     give 8 real data points at the same cost — worth switching to for future screening runs.
  5. E0's Kaggle leaderboard score is still pending (submitted 2026-10-18); record it in EXP-001-baseline.md
     once grading completes.
