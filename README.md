# Gemma 4 Developer Agent — Kaggle entry

Our entry to the Kaggle competition **Google – The Gemma 4 Developer Agent** (main track + paper track).
The submission is a declarative Google ADK agent config (`submission/`) that drives the fixed
`gemma-4-31b-it-qat-w4a16-ct` model through the organizers' `swegemma` harness; everything else in this repo is
tooling to validate, pack, budget and evaluate it. Plan of record: [`plan.md`](plan.md). Verification status and
experiment logs: [`experiments/README.md`](experiments/README.md).

> Status (2026-10-13): repo scaffold + v1 baseline agent + tooling + tests. **Nothing has been verified against the
> official dataset files or run on Kaggle yet** (kaggle.com was unreachable from the build environment). Every
> field whose schema rests on community mirrors carries a `VERIFY(Qn)` comment pointing at the checklist in
> `experiments/README.md`.

## Layout

```
submission/                 == contents of submission.zip (agent.yaml at the zip root)
  agent.yaml                root LlmAgent `swe_coder` (9 harness tools, graph tools demoted in the prompt)
  eval_config.yaml          evaluation: 4.5 min / 45 calls / 70 turns / 300 s   (12 h worst case = 11.0 h)
  prompts/swe_coder.md      phased LOCATE -> REPRODUCE -> EDIT -> VERIFY -> SUBMIT protocol, anti-spin, arg rules
  configs/sampling.yaml     T 0.2, top_p 0.95, top_k 64, max_output_tokens 4096, thinking on (budget 256)
  configs/sampling_nothink.yaml, sub_agents/analyzer.yaml, prompts/analyzer.md, skills/pytest-triage/SKILL.md
                            ablation assets; NOT referenced by agent.yaml, so the packer does not ship them
tools/                      dev tooling (never shipped): validate, pack, estimate budget, analyze traces, cohorts,
                            repo hygiene, notebook builder; shared constants in submission_rules.py
tests/                      pytest suite for the tools (synthetic data only)
notebooks/                  Kaggle L4x4 notebook (py:percent source + generated .ipynb + kernel-metadata.json)
scripts/kaggle_setup.sh     one-shot Phase 0 setup on your machine (kaggle CLI, downloads, venv, checks)
experiments/                Q1–Q12 checklist, experiment logs, cohorts (ids only), submissions log
paper/                      paper-track outline, figures, released CSVs
data/, runs/                gitignored: competition data and raw run output (never commit; redistribution rule)
```

## Quickstart (local, no GPU)

```bash
pip install pyyaml pytest                 # Python >= 3.11
python -m pytest -q                       # tool tests
python tools/validate_submission.py submission/            # schema + lint checks
python tools/pack_submission.py                            # -> dist/submission.zip (+ sha256); refuses if invalid
python tools/estimate_budget.py --eval-config submission/eval_config.yaml   # 12 h gate (worst case <= 11 h)
python tools/validate_submission.py dist/submission.zip    # archive-level checks
ln -sf ../../tools/check_repo_hygiene.py .git/hooks/pre-commit   # block data/credentials/large files
```

## Kaggle workflow

1. Accept the rules on both competitions, form the team, confirm the Timeline page (Q6).
2. `bash scripts/kaggle_setup.sh` (add `--full` for the 21 GB dataset). It downloads `HARNESS_README.md`,
   `sample_submission/`, the wheelhouse, installs the harness wheels into `.venv`, and runs
   `tools/validate_submission.py --official` so the hosts' own validator checks `submission/`.
   Then work through `experiments/README.md` §1 (Q1, Q2, Q9 are answered by reading those files).
3. Build the eval notebook with the zip embedded and push it to a competition-attached L4x4 notebook:
   `python tools/build_notebook.py --embed dist/submission.zip --username <you>` then `kaggle kernels push -p notebooks/`.
   EXP-000 (gold control) and EXP-001 (baseline on smoke-8, then dev-48) come out of the same notebook.
4. Download the run bundle to `runs/<EXP_ID>/` and analyze:
   `python tools/analyze_traces.py runs/EXP-001 --cap-minutes 4.5 --max-calls 45` and
   `python tools/estimate_budget.py --eval-config submission/eval_config.yaml --results runs/EXP-001/summary.jsonl`.
5. Cohorts: `python tools/make_cohorts.py --tasks data/raw/tasks.jsonl --exclude runs/EXP-000/gold_failures.txt`.
6. Submit (1/day): `kaggle competitions submit -c gemma-4-developer-agent -f dist/submission.zip -m "v1 <sha256[:12]>"`,
   and log it in `experiments/README.md` §4.

## Rules we build around

- Only `gemma-4-31b-it-qat-w4a16-ct`; declarative YAML only; allowed file types `.yaml .yml .md .txt .py .json .safetensors`.
- 12 h for all hidden tasks including sandbox setup; overrun fails the whole submission → `eval_config.yaml` caps
  and the estimator gate.
- 32,768-token context; `max_output_tokens` 4096, bounded tool output, line-range reads, early `submit_patch`.
- Competition data (tasks, snapshots, graphs, wheelhouse, traces) is never committed; prompts stay repo-agnostic.
- Apache-2.0 (`LICENSE`), as required of winners.

## Credits

Schema and harness behaviour were cross-checked against public community repositories (no code copied):
damsolanke/gemma4-swe-kit (Apache-2.0; the scorer-time idea in `tools/estimate_budget.py` and the malformed-call
taxonomy in `tools/analyze_traces.py` follow its approach), Gosling-dude/gemma4-developer-agent,
HindsightWise/gemma-4-developer-agent, ennydev-2026/gemma-4-developer-agent and rishaviitd/kaggle.gemma.coding.agent
(mirror of `HARNESS_README.md` and the starter notebook).
