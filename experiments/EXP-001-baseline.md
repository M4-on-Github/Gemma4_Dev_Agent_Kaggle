id: EXP-001-baseline (= E0, plan.md §6.0)        date: 2026-10-17        owner: M4
hypothesis: the v1 phased prompt with 4.5 min / 45 calls finishes every task inside the cap, with empty-patch
            and overflow rates well below community baselines, at a dev-48 resolve rate of 10–25%.
single variable changed: baseline (reference point for E1–E11)
cohort: dev-48 (experiments/cohorts/dev-48.txt, seed=20261013, generated 2026-10-17; actual composition
        fastapi 26 / rich 16 / requests 5 / httpx 1 — see cohorts/README.md for why this differs from the
        plan §5.2 design target of 22/16/9/1)        GPU-h used: ~1.6 h (incl. v1/v2 crashed attempts)
config: HEAD ee1b209 with submission/prompts/swe_coder.md reverted to its e1d61fb state (shim fix kept,
        exp006–008 ledger-wording churn rolled back, per plan §6.0's E0 spec — not re-committed as a tag,
        just the working-tree state the zip below was packed from)
        zip sha256 (tools/pack_submission.py): c2bf932104e9e544254d28a0efd693c6a1d85e4b82ff0923ad4f99bfe78e4a07
        kernel: rainm4/gemma4-e0-dev48-baseline (notebooks/E0/), pushed 2026-10-17, **version 3** (v1 crashed
        on a stale `docker_image_pinning_type: original` vLLM ABI mismatch — fixed by pinning the explicit
        `docker_image` sha; v2 crashed on a code bug, `for alias in {declared, TARGET}:` nesting an unhashable
        `set` inside a set literal — fixed to `{next(iter(declared)), TARGET}` in notebooks/kaggle_eval_l4x4.py,
        both regenerated and fixed in the shared template too; see plan.md §10.1 risk log)
        eval_config: 4.5 min / 45 calls / 70 turns / 300 s ; sampling: T 0.2, top_p 0.95, top_k 64,
        max_output_tokens 4096, thinking on, thinking_budget 256
results: resolve 11/48 = 22.9% (Wilson 95% CI 13.3–36.5%), empty patch 39.6%, timeout 66.7%, time-cap 79.2%,
         calls-cap 12.5%, overflow 0.0%, malformed 0.06%, spin 7.2%, edit-fail 0.6%, submit_patch 29.2%,
         median wall 4.56 min, p90 4.64 min, projected 12 h total 8.61 h, worst case 9.00 h
per-repo: fastapi 6/26, rich 4/16, requests 1/5, httpx 0/1
decision: **resolve rate (22.9%) and worst case (9.00 h ≤ 11 h) both clear the plan §4.6 bar — submit v1 to
          the LB.** Submitted 2026-10-18 via Competitions > Submit Prediction > File Upload (the competition
          grades a directly-uploaded `submission.zip`, not a notebook's output — the Notebook tab explicitly
          rejects E0's kernel since it produces eval results, not a submission artifact). Uploaded
          dist/submission.zip (sha256 c2bf932104e9e544254d28a0efd693c6a1d85e4b82ff0923ad4f99bfe78e4a07,
          unchanged since v1/v2/v3 kernel runs). Status immediately after submit: "Notebook Running". LB score
          pending — record it here once Kaggle finishes grading.
follow-ups: phase_histogram = {LOCATE 26, REPRODUCE 10, VERIFY 4, EDIT 7, SUBMIT 1} — **54% of tasks (26/48)
          never leave LOCATE**, confirming exp005's step-budget bottleneck at full representative-cohort scale.
          time_cap_hit (79.2%) vastly dominates calls_cap_hit (12.5%) — the binding constraint is wall-clock,
          not tool-call count, which should steer E6's budget sweep toward the time-minutes axis over calls.
          This makes E-STOP(a') (forced LOCATE→REPRODUCE→EDIT transition) the clear next priority per plan §6.0/6.1,
          ahead of E3 and the rest of the backlog. Run a second seed/session to measure variance (plan §5.5).
