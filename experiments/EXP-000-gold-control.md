id: EXP-000-gold-control        date:            owner:
hypothesis: some public tasks fail even with the reference patch in the Kaggle subprocess sandbox (py3.13);
            those must be excluded from cohorts and counted (plan §5.4, Q5).
single variable changed: none (no model; GoldEvaluator returns task.patch)
cohort: all 129 public tasks (chunk into ≤ 65 per notebook session if needed)   seed: n/a   GPU-h used:
config: notebooks/kaggle_eval_l4x4 with RUN_GOLD_CONTROL=True, RUN_AGENT=False, N_TASKS=129
results: sound / total = ___ / 129 ; failures listed in runs/EXP-000/gold_failures.txt (copy ids here)
per-repo: fastapi ___/67, rich ___/48, requests ___/13, httpx ___/1
decision: exclude failures; regenerate cohorts with tools/make_cohorts.py --exclude runs/EXP-000/gold_failures.txt
follow-ups: rerun whenever the wheelhouse/harness version changes.
