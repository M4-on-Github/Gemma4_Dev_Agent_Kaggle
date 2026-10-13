# Experiments

Index of verification items, experiment logs and LB submissions. Numbers go here, not in chat.
Confidence tags as in plan.md: **[V]** verified against official files/pages, **[M]** community mirror(s),
**[I]** inference. Nothing below has been verified against official files yet (kaggle.com was unreachable
from the build environment); every row starts OPEN.

## 1. Verification checklist (plan §3.4) — status OPEN unless stated

| # | Question | Where to look | Current default in repo | Evidence so far | Status |
|---|---|---|---|---|---|
| Q1 | Exact compile-time tool registry; are `run_skill_script` / `load_skill_resource` real; graph tools present? | `phase0_report.json` from `notebooks/kaggle_eval_l4x4` (greps the installed `swegemma`/`adk_submission` source); `HARNESS_README.md` §6 | 9 tools declared in `submission/agent.yaml`; no skills | HARNESS_README mirror lists exactly 9 harness tools; ADK SkillToolset adds list_skills/load_skill/load_skill_resource/run_skill_script when `skills:` is set; one team hit ToolNotFoundError [M] | OPEN |
| Q2 | `agent.yaml` / `sampling.yaml` / `eval_config.yaml` schema and field names | `data/raw/sample_submission/*` (diff against `submission/`), `adk_submission` schema source, `swegemma/config.py` | `evaluation: {max_time_minutes, max_tool_calls, max_turns, timeout_seconds}`; plain tool-name list; `agent_tool: {config_path, skip_summarization}`; model `gemma-4-31b-it-qat-w4a16-ct` | HARNESS_README mirror §2 + §7.1 and 4 community repos agree [M]. Open sub-questions: does `timeout_seconds` also cap the grading pytest (one source-reading says yes [M]); is `..` allowed in `!include` (mirrors disagree; we allow it when it stays inside the root) | OPEN |
| Q3 | Does `thinking_budget` bind? | `adk_submission/resolvers/generation.py` (grep in phase0_report); compare `total_completion_tokens` for budget 128 vs 1024 on smoke-8 | `include_thoughts: true`, `thinking_budget: 256`, `max_output_tokens: 4096` | Source reading by one team: only `enable_thinking` on/off is forwarded; budget ignored [M]. HARNESS_README mirror recommends budget 4096 + max_output 16384 (too slow for 4.5 min) | OPEN |
| Q4 | LoRA zeroing in patched vLLM | Kaggle discussions 743508 / 743213; logprob canary notebook (not built yet) | no adapter shipped | host acknowledged adapters wiped [M] | OPEN — gate G-LoRA Oct 25 |
| Q5 | Which public tasks fail with the gold patch? | EXP-000 (`runs/EXP-000/gold_failures.txt`) | none excluded yet | one report: 107/129 pass [M]; another: 119/129 sound, `rich_3472`/`rich_3486` unsolvable on py3.13 [M] | OPEN |
| Q6 | Entry/merger deadline: Nov 2 or Nov 25? | competition Overview > Timeline | plan treats Nov 2 as binding until disproven | A Sep-28 capture of the Timeline page says Entry + Team Merger **Nov 25**, final **Dec 2**, paper **Nov 12** [M, near-V]. Confirm on the live page, then update plan.md §1.2 | OPEN |
| Q7 | Compaction interval 5 vs 15; threshold 14,336 | `HARNESS_README.md` §7.2 vs starter notebook; traces (`compactions` column from `tools/analyze_traces.py`) | notebook parameter `COMPACTION_INTERVAL = 5` | README mirror: interval 5, overlap 2, threshold 14,336, retention 5; starter-notebook mirror used 15 [M] | OPEN |
| Q8 | Sandbox setup time per task | `setup_s` column (task wall minus agent duration) in `task_results.jsonl` | 1.0 min assumed in the estimator and the 11 h gate | host: a run with no patches takes ~10 min total incl. server start, i.e. seconds per task [M]; plan assumed 45–60 s [I] | OPEN |
| Q9 | Allowed extensions / size limit | `swegemma/config.py` (`ALLOWED_SUBMISSION_EXTENSIONS`, `MAX_SUBMISSION_SIZE_BYTES`) | `.yaml .yml .md .txt .py .json .safetensors`; < 3 GiB unpacked; no hidden files, no 0-byte files | README mirror §2.4 and the starter notebook's packaging cell [M] | OPEN |
| Q10 | Decode speed / per-call overhead / prefix caching | notebook decode probe (`decode_probe` in summary.json); `output_tokens` vs `wall_s` in summary.jsonl | 25.5 tok/s + 0.6 s/call in the estimator | g4kit fit: 25.5 tok/s + 0.6 s (3 arms sharing a server, pessimistic) [M]; one real trace: 10,570 completion tokens in 288.6 s → ≥ 36.6 tok/s effective [M] | OPEN |
| Q11 | Actual weekly L4×4 quota | Kaggle account page after the first run | 30 h/week assumed [I] | — | OPEN |
| Q12 | `write_file` cannot create files outside `/workspace` (paths are rewritten under it) | HARNESS_README §6.2; a trace where the model tried `/tmp/repro.py` with write_file | prompt tells the model to create scratch files with a run_command heredoc in /tmp | starter-notebook mirror note + README mirror [M] | OPEN |

Phase 0 exit gate (plan §3): Q1, Q2, Q5, Q9 answered; EXP-000 done; `tools/validate_submission.py --official`
passes on `data/raw/sample_submission`.

## 2. Observed numbers (fill in as they arrive)

| Item | Value | Source | Date |
|---|---|---|---|
| vLLM server start on L4×4 | | `summary.json: server_start_s` | |
| Decode tok/s (probe) | | `summary.json: decode_probe` | |
| Mean setup_s | | `aggregates.json: setup_s_used` | |
| Baseline run-to-run variance (same config, 2 seeds, dev-48) | | EXP-001a/b | |
| Weekly GPU quota | | | |

## 3. Experiment index (one row per `EXP-NNN-<slug>.md`)

| ID | Date | Variable | Cohort | Resolve | Empty % | Overflow % | Malformed % | Spin % | Median wall | Proj. 12 h | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EXP-000 | | gold control (no model) | all 129 | | — | — | — | — | | — | |
| EXP-001 | | baseline v1 (phased prompt, thinking 256, T 0.2, 4.5 min/45 calls) | smoke-8 → dev-48 | | | | | | | | |

Log template (`experiments/EXP-NNN-<slug>.md`):

```
id: EXP-NNN-<slug>        date:            owner:
hypothesis:
single variable changed:  (git diff link / file:line)
cohort:                   seed:            GPU-h used:
config: git tag / commit, zip sha256, eval_config, sampling
results: resolve % (Wilson CI), empty %, overflow %, malformed %, spin %, median/p90 wall, projected 12 h, worst case
per-repo: fastapi / rich / requests / httpx
decision: adopt | reject | rerun        (rule: Δ ≥ +3 tasks on dev-48 AND no process-metric regression)
follow-ups:
```

Cohorts live in `experiments/cohorts/*.txt` (task ids only; generated by `tools/make_cohorts.py --seed 20261013`
after excluding EXP-000 failures). Raw traces stay in `runs/` (gitignored); only `summary.jsonl`/`aggregates.json`
may be copied into `experiments/EXP-NNN/`.

## 4. Submissions log (1 per day; 2 finals)

| Date (UTC) | Git tag | zip sha256[:12] | dev-48 | held-out-24 | Public LB | Scoring wall | Notes |
|---|---|---|---|---|---|---|---|
| | v1 | | | | | | first submission target Oct 17 |

Rules reminders: never submit a config that has not run on dev-48 with projected worst case ≤ 11 h; ignore LB
moves < 0.035 (2 tasks); last submission ≤ Dec 1 23:00 UTC.
