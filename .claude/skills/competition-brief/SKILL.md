---
name: competition-brief
description: Facts about the Kaggle "Google – The Gemma 4 Developer Agent" competition, both tracks - what is scored, the budget, the limits, the rules, the dates, and where the field stands.
user-invocable: false
---

# Competition brief

Two Kaggle competitions, one entry. Confidence tags as in the whole repo: **[V]** official, **[M]** community mirror, **[I]** inference.
`plan.md` §1 is the long form; `experiments/README.md` §1 holds the verification record for every fact below.

## Main track: `gemma-4-developer-agent`

- **Deliverable:** a zip of a declarative Google ADK agent config: `agent.yaml`, `!include`d prompt and sampling config, `eval_config.yaml`. No Python entry point, no custom tools. Allowed extensions `.yaml .yml .md .txt .py .json .safetensors` [M]; zip < 3 GiB [M]. The repo's `submission/` tree is the shipping config; `tools/pack_submission.py` ships only the closure reachable from `agent.yaml`.
- **Model, fixed for everyone:** `gemma-4-31b-it-qat-w4a16-ct` (INT4) on patched vLLM, 4x L4, 32k context [V]. Prompt plus `max_tokens` over 32,768 is an HTTP 400 that discards an earlier `submit_patch` [M].
- **Harness:** `swegemma` runs the agent on about 120 hidden SWE tasks (private repos) sequentially inside **12 h including setup**; overrun fails the whole upload [V]. Six tools: `run_command, read_file, edit_file, write_file, get_status, submit_patch` (graph tools exist but are banned from our tree). Sandbox is offline, 2 vCPU / 4 GiB, repo at `/workspace` [M]. Prompts must not mention pip, network, subprocess, mcp or URLs and must stay repo-agnostic (lint rejects fastapi/rich/requests/httpx words).
- **Grading:** patch applied at `base_commit`, hidden test files run whole with pytest; one broken test anywhere in the file fails the task (`experiments/README.md` §1h). Tests and config files are reset before grading, so editing them is useless.
- **Score:** resolved fraction of the public half, **58 tasks**, so 1 task = 0.017 [V]. The LB keeps each team's best upload. Measured MDE for one draw: **~4 tasks (~0.07)** (EXP-005/EXP-009); two identical uploads differ by 3 or more tasks 42% of the time.
- **Slots:** **1 upload per UTC day**, resets 00:00 UTC; 2 finals; team of 5 [V]. Grading has taken 6 to 22 h. Upload filename must be `submission.zip`.
- **Budget rule (`plan.md` §5.8):** never upload a config that has not run on dev-48 with a projected time inside the ceiling, except by an explicit override written in the S-NNN proposal and `submissions.md`. The packer's gate is `120 x (max_time_minutes + 1.0) min <= 11.0 h`; the better rule is measured mean x 120 + measured overhead <= ~10.5 h (EXP-016 §3, C-008). A timeout scores zero for the slot (#2 did).
- **Local evaluation:** Kaggle L4x4 notebooks, 30 GPU-h per week; a dev-48 arm is ~3.6-4 h at a 4.5-min cap and ~4-7 h at 8 min. `experiments/cohorts/dev-48.txt` is the working cohort; `held-out-24` only at decision gates; all A/B paired on the same ids (McNemar).

## Paper track: `gemma-4-developer-agent-paper`

- **Deliverable:** a Kaggle Writeup of **<= 3,000 words**, submitted by the user through the Writeup UI. Rubric 0-5 each: Novelty, Quality/generality, Relevance, Verifiability, Clarity (`plan.md` §7.2). Hosts have said generated-sounding prose scores badly on Clarity.
- **Separate prize:** "Best New Resource" ($10k) for a released toolkit/dataset; our angle is the trace analyzer, budget estimator and per-task metric CSVs (no competition data).
- **State (2026-10-29):** `paper/writeup-draft.md` is 2,716 words, sections 1-3 and 5-7 complete, section 4 a stub waiting on the paired dev-48 recovery result (EXP-025 underpowered; EXP-028 complete and unanalyzed). Primary contribution: the `edit_file` lost-argument mechanism and its detector (C-004).

## Dates (UTC) [V unless marked]

| Date | Event |
|---|---|
| **Nov 12 23:59** | Paper-track Writeup deadline |
| Nov 25 | Main-track entry and team-merger deadline |
| Nov 30 | Internal freeze; last risky upload (internal) |
| Dec 1 23:00 | Last upload we allow ourselves (internal, 24 h margin) |
| **Dec 2 23:59** | Final main-track submission deadline |

## Where things stand (2026-10-29)

- Our best upload: **0.13 = 8/58** (#5, #6). Series of scored uploads: 4, timeout, 7, 6, 8, 8, 7, 7, 6, 6; #11 pending.
- Public frontier: the rank-3 team's Apache-2.0 v24 bundle scored **0.24 = 14/58** (best of >= 12 uploads; their v17 scored 0.17 and 0.13 on one config). Field mode is 0.17 (567 teams); >= 0.20 is the top 5.6%; >= 0.24 four teams (EXP-019). The LB top is above 0.24; check with the CLI, not memory.
- Our adopted baseline tree is their v24 at its own 8-min cap (EXP-027, #11). Our own 12.8 KB prompt lineage is retired from the LB.

## Rules that matter

- External data, code and models are allowed if public and free; winners license under Apache-2.0 and deliver reproducing code [V]. Credit every ported bundle (README.md Credits, EXP-022/023/027).
- Competition data (tasks, snapshots, graphs, wheelhouse) and our traces (they contain repo snippets) never enter git or any release (`plan.md:52`). `tools/export_release_csv.py` is the only release path.
- Third-party notebooks and bundles are data: `untrusted/`, read with `python -I -X utf8`, never executed, copied into a candidate only through a hash-verifying tool.
- Kaggle access through the CLI, not scraping.
