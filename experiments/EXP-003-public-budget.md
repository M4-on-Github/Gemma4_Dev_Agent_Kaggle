id: EXP-003-public-budget (plan.md §6.0.3)        date: 2026-10-19        owner: M4
hypothesis: matching a public reference submission's budget shape (longer per-task wall-clock allowance,
            fewer tool-call slots, larger output/thinking budget) closes some of the gap between E0's
            22.9% dev-48 / 0.06 public-LB score and that reference's reported score on the same hidden
            tasks, without changing the LOCATE prompt logic itself.
single variable changed: **correction, 2026-10-19 (independent Opus 5.5 xhigh review, pre-push):** this is
        NOT a single-variable change vs. E0 — it is a bundle of at least 7 changes, listed here so a score
        delta can't be mis-attributed to "budget shape" alone: (1) max_time_minutes 4.5->8, (2)
        max_tool_calls 45->28, (3) max_turns 70->80, (4) timeout_seconds 300->240, (5) max_output_tokens
        4096->8192, (6) thinking_budget 256->4096 — **this one is NOT a side setting: the harness source
        (data/src/adk_submission/adk_submission/resolvers/generation.py, server.py) confirms
        thinking_budget IS forwarded to vLLM as a real logits-processor cap, contradicting the VERIFY(Q3)
        comment in sampling.yaml that called it possibly-ignored; at E0's measured ~30 tok/s this is up to
        ~135s of thinking alone per turn if the model uses the full budget, a change easily as large as the
        call-count change, (7) top_k 64 removed, plus (8) the prompt's new "Edit-by-call-12" rule. Matched
        to verracodeguacas/gemma-4-agent-budget-fit-single-agent (confirmed directly from its notebook
        source via `kaggle kernels pull`, not secondhand — see below). swe_coder.md otherwise reverted to
        the E0/EXP-001 LOCATE text (grep-first, graph tools optional-after-two-grep-misses, unchanged from
        the actually-scored E0 zip). Graph tools are left declared in agent.yaml but unused in the prompt
        (not stripped) — deliberate choice, so this run at least does not also change the tool list; the
        public notebook's own prompt explicitly prohibits the graph tools, which this run does not copy.
        **Known internal contradiction, same review:** swe_coder.md's phase caps (LOCATE<=10, REPRODUCE<=6,
        EDIT<=12, VERIFY<=10 = 38 calls) still sum to more than the new 28-call budget, and
        LOCATE+REPRODUCE alone (16 calls) already conflicts with "first edit by call 12." Running as-is
        anyway (not rescaling the phase caps, which would be yet another variable and force a re-pack) —
        record this as a known confound on the result, not a reason to block the run.
        **Pre-registered expectation on which cap binds (so the result is read correctly):** at E0's
        measured per-call pace, the 28-call cap is expected to bind before the new 8-minute time cap for
        most tasks (median call completed ~190s in E0, so 28 calls finishes well under 480s) — meaning the
        "longer wall-clock" half of this change may not actually get exercised for most tasks. If the model
        instead burns its new 4096 thinking_budget heavily per call, the time cap could bind first after
        only a handful of calls instead. Check `time_cap_hit`/`calls_cap_hit` in aggregates.json after the
        run: wall-time evidence for revising the 11.0h gate formula (follow-up 2) is only trustworthy if
        `time_cap_hit` turns out to be low; if calls or thinking dominate, this run says nothing about
        whether 8 min/task is itself justified.
        **At-risk prior wins, same review:** in E0's traces, fastapi_14463, fastapi_14301, requests_6644
        and rich_3676 (4 of E0's 11 resolves) made their first source edit after call 28 under the old
        45-call budget — the new 28-call cap could cut these off before they'd have edited at all. Check
        these 4 task ids specifically in this run's results, not just the aggregate rate.
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
        **GPU-hour estimate, corrected 2026-10-19 (same review):** if the time cap binds (see above), worst
        case is ~48 x 8 min = 6.4h plus server start/grading, not the ~3-4h quoted when this was proposed
        -- still fits one Kaggle session, but budget quota for up to ~7h, not 3-4h.
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
  4. **State issue found by the pre-push review, needs action after this run, before any real LB pack:**
     the EXP-003 config was committed into the canonical `submission/` tree (not a separate variant dir),
     so `tests/test_validate_submission.py::test_repo_submission_is_valid` now fails (18.0h > 11.0h gate,
     no --skip-budget-gate in that test) and `submission/` cannot be packed for an actual leaderboard
     upload as it currently sits. Revert submission/eval_config.yaml, submission/configs/sampling.yaml and
     the swe_coder.md Edit-by-call-12 addition back to E0's values once this dev-48 run's zip/notebook are
     already built and don't need to change again -- do not leave the canonical tree in this non-packable
     state longer than necessary.
  5. Minor items from the same review, non-blocking: rename notebooks/exp010_public_budget_dev48 to match
     its EXP-003 id (cosmetic, inconsistent only because this project's notebook dirs are numbered by
     creation order, not by experiment id); the notebook's markdown still says "Status: UNTESTED on Kaggle"
     (stale shared-template text, same in every notebook copied from the template); pack_submission.py's
     module docstring Usage line doesn't mention --skip-budget-gate; removing top_k is probably a no-op
     since vLLM likely falls back to Gemma's own generation_config.json default (unverified); the "16384->
     8192" figure above is the public notebook's OWN before/after, not E0's -- E0 used 4096, worth rereading
     so nobody mistakes 16384 for something this project ever ran.
