---
id: kg-davis0178-baseline-notebook
topic_id: davis0178 "gemma-4-agent-baseline" notebook
title: Public LB-0.22 bundle (EXT-19), materialised and hash-verified in EXP-022; licence unchecked at the time
author: davis0178
author_role: top-lb
credibility: medium
topics: [prompt, budget, rules]
first_seen: 2026-10-25
last_checked: 2026-11-03
---

Migrated 2026-10-29 from `research/2026-10-28-kaggle-open-scouting.md` §6 and `experiments/EXP-022-direction-review.md`.

## Summary
A public notebook whose bundle scored 0.22. EXP-022 materialised it with `tools/exp022_make_candidate.py` (hash-verified) as the EXT-19@4.5 candidate; its prompt failed our repo-agnostic lint on a FastAPI line. EXP-023 chose the rank-3 Apache-2.0 bundle instead because this notebook's licence was unchecked (a gap left open in three documents).

## Claims made (quoted numbers)
- LB 0.22 (notebook card). No per-task data released.
- 2026-11-03 LB CSV: DVS (davis0178) rank 23, 0.22, 14 submissions, last 2026-10-30. [V] The LB 0.22 matches the card.

## Possible claims for us
- None beyond what kg-rank3-apache-release covers better with a stated licence.

## Files
- kernel-metadata (2026-10 pull): id davis0178/gemma-4-agent-baseline, enable_internet false, enable_gpu false, competition_sources gemma-4-developer-agent. Licence still unchecked.

## Updates
- 2026-10-25: not uploaded; superseded by the rank-3 bundle (EXP-023 §1).
- 2026-11-03: LB row confirmed (rank 23, 0.22). Same 0.22 public score as the flexonafft-v10 family (see kg-flexonafft-v10-family); the family's configs differ from this notebook's and were not compared byte-for-byte here.
