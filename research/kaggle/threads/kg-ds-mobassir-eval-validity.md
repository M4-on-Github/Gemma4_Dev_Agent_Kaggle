---
id: kg-ds-mobassir-eval-validity
topic_id: companion dataset of the Mobassir writeup (paper track); slug `mobassir/swe-agent-eval-validity-gemma4` (confirmed by the notebook's `dataset_sources`)
title: "Mined SWE Tasks and Paired Results for Gemma 4 Software-Engineering Agents" (zip: swe-agent-eval-validity-gemma4.zip)
author: mobassir (Syed Mobassir Hossain, as named in the dataset README)
author_role: participant (paper track)
credibility: [M] the author's own tasks, runs and draws; leak flags and statement classes are heuristics the README says are not hand-validated; FreshSWE-297 tasks are third-party and referenced by id only
topics: [noise, selection, compaction, dpo, rules, paper]
first_seen: 2026-11-17
last_checked: 2026-11-17
---

# mobassir: eval-validity companion dataset

## Untrusted file record (read as data with `python -I -X utf8`; never executed or extracted)

| File | Bytes | SHA-256 | Licence | Pulled |
|---|---|---|---|---|
| `untrusted/mobassir-swe-agent-eval-validity-gemma4-2026-11-17/swe-agent-eval-validity-gemma4.zip` | 12,789,423 | `8d31688c6a45ed17c3f3062079b1d3ec3915501565a26ce8ad5d02326f035186` | Apache-2.0 (LICENSE in the archive) | 2026-11-17 |

- Archive members: 54 (listed with `research/kaggle/zip_members.py`). The archive has no version field we could read;
  the pull date is 2026-11-17.
- Notable members: `data/tasks.jsonl` (50.9 MB; not read), `results/*.csv`, `results/leaderboard_draws.csv`,
  `results/leaderboard_bands_2026-11-10.csv`, `results/leaderboard_bands_2026-11-16.csv` (5,840 teams and 48,085
  submissions on 2026-11-16, per the README), `results/census_config_draws.csv` (six file sets derived from
  Afshar's CC BY 4.0 census), `code/analysis/noise.py` (paper Eqs. 2 to 4), `figures/*.png`, `paper.pdf` (not read).
- README claims: 4,207 tasks from 64 permissively licensed repositories; per-task labels (`leak_flag`,
  `statement_type`, `upstream_license`); the four public repositories and 17 OOD repositories excluded at import.

## Numbers in the README and results (phase-1 read)

- Noise calculator defaults in the README reproduction command: `--n 58 --d 0.127 --sigma 1.53 --delta 1`.
- Compaction (paper Section 6): odds ratios **0.50 and 0.39** (README, from `compaction_analysis.py`).
- The README says the leaderboard draws are the author's own (ref, date, agent, public score, tasks of 58), e.g.
  ref 58144820 on 2026-11-09 with agent B+R2 at 0.13 (8 tasks).

## Limitations stated by the author

- Leak flag and statement-type classifier are heuristics, not hand-validated.
- Full rollout trajectories are not included (machine-specific paths).
- Local replica with a 2.8x time dilation and a subprocess sandbox; the paper discusses the remaining differences.

## Relevance

See the paper-track digest rows on leaderboard noise (row 3) and runtime margin (row 6). The compaction
odds ratios concern FreshSWE-297 runs, not our hidden-set harness.
