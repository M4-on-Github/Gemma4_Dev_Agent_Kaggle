---
name: harness-stack
description: How to validate, pack, run and analyze agent configs for this competition - the tools under tools/, Kaggle kernels, run analysis, and the Windows and git pitfalls that have cost time.
user-invocable: false
---

# Harness stack

> The experimenter maintains this skill. `SKILL.md` holds only verified facts every run needs; `reference/` holds details read on demand. Prune a note when a later fact supersedes it. Anything marked (unverified) must be checked before you rely on it. CLAUDE.md is the short form of the same material.

## Environment

- Python 3.13 (miniconda) is `python` in the Bash tool; the repo needs >= 3.12 with `pyyaml` and `pytest`. `python -m pytest -q` runs 38 tests in seconds on synthetic data; run it after touching `submission/`, `tools/` or adding a tracked file (two tests check the live tree and every tracked file).
- Anything that reads downloaded or third-party files (`untrusted/`, run bundles, notebooks) runs as `python -I -X utf8 ...` so nothing is imported from the data's directory and encoding is stable.
- `core.autocrlf=true`: the zip sha256 reproduces only from committed LF blobs. Pack from a clean checkout of the committed tree, compare `sha256sum` with the recorded value before any upload.
- User-level hook blocks any `git commit` message carrying a Claude co-author or "Generated with" line. Commit without attribution lines.
- Bash heredocs whose body contains an apostrophe break the tool wrapper; use the Write tool for such files, or keep heredoc bodies apostrophe-free.
- Odd directories `runs;C` and `tools;C` at the repo root are artifacts of a PowerShell path error, empty, untracked; ignore them.

## Rules module and the validate -> pack -> gate chain

- `tools/submission_rules.py` holds every constant (tool registry, allowed keys, limits, lint patterns, `RUN_BUDGET_HOURS`, `PACK_GATE_HOURS`, `EXPECTED_HIDDEN_TASKS`, `ASSUMED_SETUP_MINUTES`). Change a rule there, not in consumers.
- `python tools/validate_submission.py <tree> --strict [--official --json]`: schema plus lint; exit 0 VALID. `--official` also runs the harness's own validator when its wheels import.
- `python tools/pack_submission.py [--src <tree>] [--out <zip>] [--allow-warnings] [--skip-budget-gate]`: ships the closure reachable from `agent.yaml` plus `eval_config.yaml`; deterministic zip; prints sha256; refuses rejected prompt markers. Shipped set for the repo tree is exactly `{agent.yaml, eval_config.yaml, prompts/swe_coder.md, configs/sampling.yaml}` (asserted by a test).
- Gate: `120 x (max_time_minutes + 1.0) min <= 11.0 h`; 4.5 passes at exactly 11.00 h; 5.0 is a hard error; `--skip-budget-gate` demotes it to a warning (used for #2, which timed out, and #11, override recorded in EXP-027 §2).
- `python tools/estimate_budget.py --eval-config <eval_config.yaml> [--results <summary.jsonl>]` projects the 12 h total; with `--results` it uses the measured distribution.
- `timeout_seconds` also bounds the hidden test run; below ~100 s a slow test module fails a correct patch (rank-3 v18 comment). 240 and 300 are both safe.

## Kaggle kernels

- `python tools/build_notebook.py --embed <zip> --username rainm4 --cohort experiments/cohorts/<cohort>.txt --out notebooks/<expNNN_dir>/kaggle_eval_l4x4.ipynb` builds from `notebooks/kaggle_eval_l4x4.py` (py:percent). `--set` rewrites parameter-cell assignments. Hazard (EXP-020): cell 5 sets `max_time_minutes: 60.0` under `if not RUN_AGENT:`.
- `kernel-metadata.json`: copy from the last working arm (`notebooks/exp025_armA`, `exp028_armR`) changing only `id` and `title`; keep `enable_gpu`, `machine_shape: NvidiaL4`, the pinned `docker_image` sha (`plan.md:1188`), `dataset_sources` (wheelhouse), `competition_sources`, `model_sources`. `enable_internet: false`.
- `kaggle kernels push -p notebooks/<expNNN_dir>` (the push guard needs the committed EXP file, with a `**Cohort:**` line matching the notebook's `TASK_IDS`, and `RUN_AGENT = True` outside exp000); `kaggle kernels status rainm4/<slug>`; `kaggle kernels output rainm4/<slug> -p runs/<EXP>-<arm>/`.
- Quota 30 L4x4 GPU-h per week; no CLI query exists, the lead keeps a ledger in `knowledge/plan.md` from kernel wall-clock. UNVERIFIED (2026-11-03, web sources disagree): whether L4x4 hours count 1x against the 30, and the reset day (Saturday 00:00 UTC per one source). Settle it by reading the quota counter in the notebook sidebar before and after a run, then replace this line. Measured: dev-48 at 4.5 min / thinking 4096 ~3.9 h; at 8 min / 28 calls ~4-7 h (EXP-028, both arms completed within the kernel limit; exact wall in EXP-028 §9 once analyzed). smoke-8 ~0.8 h. vLLM start ~0.25 h.
- Kernel outputs: `task_results.jsonl` (one row per task) and `traces/trace_<id>.json`. Both are competition data: `runs/` is gitignored.

## Run analysis

- `python tools/analyze_traces.py runs/<EXP> --cap-minutes <cap> --max-calls <calls>` -> `summary.jsonl` + `aggregates.json`. Counts arg-loss failures by the harness string `mandatory input parameters are not present` (the `"status": "error"` envelope misses them ~10x).
- `python tools/run_forensics.py forensics runs/<EXP>` (where wall-clock went, first-edit turn); `python tools/run_forensics.py compare runs/<A> runs/<B>` (paired 2x2 on shared ids).
- `python tools/regrade_patches.py` re-grades collected patches at 0 GPU-h; `tools/gold_control.py` needs the Docker orchestrator and cannot run on Kaggle.
- `python -I -X utf8 tools/exp024_stats.py` and `tools/exp022_stats.py` regenerate the paper's and the direction reviews' numbers.
- Only `python -I -X utf8 tools/export_release_csv.py runs/<EXP> ... --out paper/release/<file>.csv` produces a publishable per-task file (positive allowlist of fields).

## Measured facts to reuse, not re-derive

- Our 12.8 KB prompt at 4.5 min: 79-96% of tasks run to the cap (E0 79.2%, EXP-025 Arm A 95.8%); mean ~258-274 s; `cap x 120` is accurate to 4% for it. Fixed per-task overhead outside the cap: setup ~3.3 s median, grading ~14 s mean (EXP-016).
- The rank-3 v24 prompt at 8 min on their dev sets: mean 275-296 s, 15-24% at cap, median 25 calls, median first edit at step 10 (`research/2026-10-28-kaggle-open-scouting.md` §3).
- `edit_file` arg loss: 37.9% of calls across two dev-48 runs (EXP-024); 53.5% at thinking 256 vs 18.2% at 4096; the lost call's `new_string` ends in `ng:` on 200/201 (EXP-026 §1); ~90% identical-retry rate after a loss.
- Grading runs whole test files; `pytest -k` is faster but a broken sibling test fails the task (`experiments/README.md` §1h).
- Upload under any filename other than `submission.zip` returns a bare 400 and costs an attempt, not the slot (EXP-023 §6).
- Grading time for an upload: 6 to 22+ h observed (#11 pending at 21.5 h on 2026-10-29).
