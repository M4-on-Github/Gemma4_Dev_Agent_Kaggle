id: EXP-003-public-budget (plan.md §6.0.3)        date: 2026-10-19        owner: M4
hypothesis: matching a public reference submission's budget shape (longer per-task wall-clock allowance,
            fewer tool-call slots, larger output/thinking budget) closes some of the gap between E0's
            22.9% dev-48 / 0.06 public-LB score and that reference's reported score on the same hidden
            tasks, without changing the LOCATE prompt logic itself.
single variable changed: eval_config.yaml (max_time_minutes/max_tool_calls/max_turns/timeout_seconds) and
        configs/sampling.yaml (max_output_tokens/thinking_budget) only, matched exactly to
        verracodeguacas/gemma-4-agent-budget-fit-single-agent (confirmed directly from its notebook source
        via `kaggle kernels pull`, not secondhand — see below). swe_coder.md otherwise reverted to the
        E0/EXP-001 LOCATE text (grep-first, graph tools optional-after-two-grep-misses, unchanged from the
        actually-scored E0 zip) plus one added rule ("Edit-by-call-12") lifted from the same public
        notebook's own stated rationale. Graph tools are left declared in agent.yaml but unused in the
        prompt (not stripped) — deliberate choice, so this experiment isolates the budget-shape variable
        from a tool-list variable; the public notebook's own prompt explicitly prohibits the graph tools,
        but that is a second, uncontrolled variable this run does not also change.
public reference, verified directly (not secondhand): verracodeguacas/gemma-4-agent-budget-fit-single-agent
        ("Gemma 4 Agent: Budget-Fit Single Agent" by Wilmer E. Henao, 211 votes). Its own markdown states:
        max_time_minutes 4->8 ("only about half of the fixes Gemma eventually finds are in the file after
        4 minutes"); max_tool_calls 40-100->28 ("runs still exploring after many calls almost never
        succeed"); an explicit "edit by the 12th call" rule ("runs with no source edit by call 12 fail 87%
        of the time"); max_output_tokens 16384->8192 ("vLLM refuses any request with prompt + max output
        above 32,768 tokens"); timeout_seconds 60-120s->240s (local `requests` test files need ~100s, and
        the same timeout value caps the grading pytest run); graph tools explicitly prohibited in its own
        prompt ("Do NOT use search_similar_code, get_code_neighbors or get_code_subgraph: they only accept
        exact fully-qualified ids and usually return nothing"). It also states directly: "Scores on the
        58-task public leaderboard move by about ±2 tasks between identical submissions, so one score is
        not a comparison." No explicit license field found in its kernel-metadata.json (unresolved; only
        matters if the unmodified-notebook "Option A" path is pursued later instead of this prompt-matched
        "Option B").
cohort: dev-48 (same 48-task cohort as EXP-001-baseline / E0, listed in that doc), for direct comparability
        to E0's 22.9% local score and 0.06 public-LB score.        GPU-h used: TBD (not yet run)
config: working tree at time of pack (not a separate commit/tag): submission/eval_config.yaml and
        submission/configs/sampling.yaml rewritten to the public-notebook values above; submission/
        prompts/swe_coder.md reverted to the E0 LOCATE text with the Edit-by-call-12 rule added.
        eval_config: 8 min / 28 calls / 80 turns / 240 s (was 4.5/45/70/300 in E0); sampling: T 0.2,
        top_p 0.95, max_output_tokens 8192, thinking on, thinking_budget 4096, no top_k set (was
        4096/256/top_k 64 in E0).
        Worst case = 120 x (8 + 1.0 setup) / 60 = 18.0 h, which EXCEEDS this project's own 11.0 h packing
        gate (tools/validate_submission.py, vs. the true 12 h hidden-set run budget) -- the public author's
        own claim is that a real scored run finished under 12 h despite the 8-minute cap (most tasks finish
        well before hitting it). Per user decision (2026-10-19, "test first, decide gate after"): built as
        an UNOFFICIAL TEST BUILD ONLY via `python tools/pack_submission.py --out dist/exp003_test.zip
        --skip-budget-gate`, which demotes the gate to a warning; do not upload this zip to the leaderboard
        as-is. The gate formula itself is not revised until this run's real measured wall-times justify a
        specific change, one way or the other.
        zip sha256 (tools/pack_submission.py --skip-budget-gate): e820ba81c69226d291eb7b9cfe07edaf21571286819be72f5826a840d7c622cd
        kernel: rainm4/gemma4-exp003-public-budget-dev48 (notebooks/exp010_public_budget_dev48/), not yet
        pushed.
results: not yet run.
decision: pending the dev-48 GPU run. Needs explicit user go-ahead before the kernel push/GPU spend (~3-4
        GPU-h), per this project's pattern of confirming before any GPU spend or Kaggle account action.
follow-ups:
  1. After the run: compare resolve rate against E0's 22.9% (Wilson 95% CI 13.3-36.5%, n=48). If clearly
     better, consider this config for the next LB slot. If flat/worse, revisit whether submitting the
     public notebook unmodified ("Option A", a pure calibration point against a known-external score on
     the same hidden tasks) is worth a slot instead of further prompt-side iteration on Option B.
  2. Use this run's real measured wall-times (tools/estimate_budget.py --results ...) to decide, with
     actual evidence, whether the 11.0 h packing gate's worst-case-only formula should be revised -- not
     before.
  3. The `pack_submission.py --skip-budget-gate` flag used to build this test zip was itself a two-step fix
     this session: the archive re-validation step (step 4 of pack()) initially didn't thread the flag
     through to `validate_zip`, causing a false "PACKING REFUSED: archive invalid" on a build that was
     actually fine; fixed by adding `skip_budget_gate` to `validate_zip()`'s signature and its inner
     `validate_dir()` call. Confirmed working end-to-end 2026-10-19 (dist/exp003_test.zip built, 4 files,
     6.7 KiB, sha256 above).
