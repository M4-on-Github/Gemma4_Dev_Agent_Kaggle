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
          unchanged since v1/v2/v3 kernel runs). Status immediately after submit: "Notebook Running".
          **LB score (2026-10-19, public half): 0.06 = 4/58 public tasks solved** (public LB covers 58 of the
          ~120-task hidden set; 1 task ≈ 0.017; score truncates to 2 decimals). Local dev-48 → public-LB drop
          ratio is 22.9%→6.9%, ~3.3x — see plan.md §6.0.3/experiments/README.md for the fuller interpretation
          (this ratio is in line with precedent elsewhere in this project and in the literature, not itself
          anomalous; the more actionable finding is an absolute gap to a known public reference config on the
          same hidden tasks, not the drop ratio).
follow-ups: phase_histogram = {LOCATE 26, REPRODUCE 10, VERIFY 4, EDIT 7, SUBMIT 1} — **54% of tasks (26/48)
          never leave LOCATE**, confirming exp005's step-budget bottleneck at full representative-cohort scale.
          time_cap_hit (79.2%) vastly dominates calls_cap_hit (12.5%) — the binding constraint is wall-clock,
          not tool-call count, which should steer E6's budget sweep toward the time-minutes axis over calls.
          This makes E-STOP(a') (forced LOCATE→REPRODUCE→EDIT transition) the clear next priority per plan §6.0/6.1,
          ahead of E3 and the rest of the backlog. Run a second seed/session to measure variance (plan §5.5).

          **CORRECTION, 2026-10-21 (EXP-009, from this run's own traces).** Two claims above need qualifying:

          1. *"the binding constraint is wall-clock ... which should steer E6's budget sweep toward the
             time-minutes axis"* — **the cap-hit counts are right but the inference does not follow.** Buying
             more time does not buy more work: EXP-003 nearly doubled the cap (4.5 → 8 min) and got *fewer*
             turns per task (resolved 26.0 vs this run's 35.0), because its bundled generation changes made
             each turn 1.4–1.8x slower. Empty-patch rate barely moved (39.6% → 33.3%). More decisively, the
             tasks hitting the time cap here are **not** starved of turns: the 19 empty-patch tasks spend
             38.0 turns against the winners' 35.0 and the same ~15k context, and only 1 of the 19 reached the
             45-call cap. They spend a full budget and commit to nothing. The real split is the **turn of the
             first edit** — 18 for tasks that produce a patch, 43 for tasks that produce nothing (replicated
             independently on EXP-003: 14–17 vs 32.5). So this is a commitment problem, not a time-budget
             problem, and the budget sweep is the wrong next move on the time axis too.

          2. *"Run a second seed/session to measure variance"* — still **not done** on dev-48, and it matters
             more than assumed. The cross-config proxy (this run vs EXP-003, same cohort) shows only 6 of the
             14 distinct tasks either run solved were solved by both: **42.9% concordance**, 8 discordant
             pairs, exact McNemar p = 0.73. At that churn rate this run's headline 22.9% (11/48) is not a
             stable per-task result, and the ±12-pt CI quoted above understates how much the *identity* of
             the solved tasks moves. Marginal resolve rates from this run should not be compared to another
             run's without the paired table (`python tools/run_forensics.py compare <runA> <runB>`).

          Also from this run's traces: **73.7% of agent wall-clock goes to reading code** (`sed`/`cat`/`head`
          alone is 27% of the whole run at 11.40 s median per call, vs `read_file`'s 2.74 s for the same job),
          only 11.7% to editing, and 13/48 tasks never call `edit_file`/`write_file` at all. Among the 29
          tasks that do produce a patch, 11 resolve (**37.9%**). Full analysis and the per-tool tables:
          `experiments/EXP-009-lb-variance-and-trace-forensics.md`, evidence in `experiments/EXP-009/`.
