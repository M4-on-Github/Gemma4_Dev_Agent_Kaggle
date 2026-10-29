---
id: kg-rank3-apache-release
topic_id: muhammedidris28/gemma4-agent-runs (dataset) and the paper-track writeup "Git History as a Gym"
title: Rank-3 team Apache-2.0 release - 15 agent bundles v11-v25, runs.jsonl, LoRA metrics, leaderboard.json
author: muhammedidris28
author_role: top-lb
credibility: medium
topics: [budget, prompt, edit-reliability, lora, noise, paper]
first_seen: 2026-10-25
last_checked: 2026-10-28
---

Migrated 2026-10-29 from `research/2026-10-28-kaggle-open-scouting.md` (full detail there; this note is the index entry). Files are in `untrusted/rank3-apache/` (gitignored), read with `python -I -X utf8`, never executed. Licence Apache-2.0 as stated in the dataset.

## Summary
The LB-0.24 configuration and its history. Their lever was the time cap: v13-v18 at 5.5 min scored 0.12-0.17; v19 and v24 at 8 min / 28 calls scored 0.18 and 0.24. v24 and v25 prompts are byte-identical (3,240 bytes); v25 only raises calls to 40 and is unscored. Their best local config (v20_base) resolves 39.1% with 6.5% empty patches, median first edit at step 10, median 25 calls, mean 275 s at an 8-min cap. Three LoRA adapters all lost locally (v20 28.3% vs 39.1%; v21 19.6% with 54.3% empty). Two uploads of v17 scored 0.17 and 0.13.

## Claims made (quoted numbers)
- eval_config v17 comment: "Hidden test set is ~120 tasks run sequentially within 12 h (incl. setup + vLLM startup). 5.5 min/task (forum: hard short caps scored lower; >12 h errors the whole run). At 6.0 the v13 dev40 mean was 314 s (~10.5 h for 120 tasks, too close); 5.5 est. ~9.8 h."
- eval_config v18 comment: "timeout_seconds 240 (was 60). The verifier runs the hidden test files under this same limit ... the Requests test modules already take about 70 s."
- runs.jsonl at 8 min: mean 275-296 s, 15-24% of tasks within 20 s of the cap, 2-6 of ~19 resolves per 46-task set finish after 270 s.

## Possible claims for us
- C-002 (cap is the lever), C-003 (8 min completes), C-007 (40 calls), C-013 (LoRA hurts), C-001 (v17 noise), C-017 (timeout bounds hidden tests).

## Files
- `runs.jsonl` (574 rows), `agents/v11..v25/` (15 bundles), `training/*.metrics.json`, `leaderboard.json`. SHA-256s recorded in `experiments/EXP-022/` and `experiments/EXP-023-v24-at-45.md` for the files we copied (candidate built by `tools/exp022_make_candidate.py`).

## Updates
- 2026-10-25: v24 bundle reconstructed as #8 at 4.5 min (EXP-023): 7/58.
- 2026-10-28: v24 at 8 min uploaded as #11 (EXP-027); dev-48 arms EXP-028 pushed.
- To check next: their paper-track writeup when published; v25's score if uploaded.
