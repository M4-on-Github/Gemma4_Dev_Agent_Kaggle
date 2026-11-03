---
id: kg-gluzdov-serving-lora-kit
topic_id: dmitriigluzdov/gemma-4-serving-and-lora-verification-kit (dataset) and dmitriigluzdov/gemma-4-task-soundness-and-local-results (dataset)
title: Gemma 4 Serving and LoRA Verification Kit; Gemma 4 Task Soundness and Local Results
author: Dmitrii Gluzdov (LB account dmitriigluzdov, 0.18, rank 379, 29 submissions, last 2026-10-31)
author_role: top-lb
credibility: medium
topics: [edit-reliability, budget, lora, grading, noise]
first_seen: 2026-11-03
last_checked: 2026-11-03
---

## Summary
Two released datasets with per-run data. The serving kit (655,906,742 B, 4,529 downloads, updated 2026-10-20) is the source of the "692 runs" figures quoted in the leoprovorov anytime-patch notebook. Not downloaded here (655 MB, outside this digest's scope). The figures below are therefore second-hand: quoted by another notebook, not checked against the CSV. The soundness dataset (787,003 B, 3,448 downloads, 2026-10-21) is the task-soundness audit that other threads cite for task filtering.

## Claims made (quoted numbers, second-hand)
- [M, quoted by leoprovorov 2026-11-03] 692 runs, 8 bundle configurations on 114 sound public tasks; one A100, eight concurrent workers, seed 42.
- [M, quoted] 194 of 692 (28%) runs ended with no patch; 75 context overflows, all with empty patches; 52 session timeouts with no edit; 53 agent stopped without editing.
- [M, quoted] v4 thinking-on config: 39 of 80 (49%) resolved; at most 14 tool calls 37 of 71 (52%); 15-20 calls 2 of 43 (5%).
- [M, quoted] Public tasks no configuration solved: 64 of 114.
- [M, from the wrapper-stage1 thread's task-selection line] "Dmitrii Gluzdov and Busya PRIME's soundness audit, version 10" is cited as the task-selection source by sukhendu-sain (755066).

## Possible claims for us
- Patchless runs are the largest loss in the cited data (28%); context overflow always produced an empty patch. Medium, pending a check of the CSV.
- The 14-call / 15-20-call split is a correlation in a prompt-era dataset. Not a causal claim.

## Files
Not downloaded. Dataset slugs and sizes from `kaggle datasets list -s "gemma-4 agent"` on 2026-11-03.

## Updates
- 2026-11-03: first logged. The 2026-10-28 digest did not list these two datasets.
