---
id: kg-755291-300s-budget-audit
topic_id: 755291
title: Where 76% of a 300-second agent budget actually goes (4 trace audits)
author: LiangXiaoyu (LB account not found in the 2026-11-03 CSV; notebook xingling666)
author_role: participant
credibility: low
topics: [budget, tools, edit-reliability]
first_seen: 2026-11-03
last_checked: 2026-11-03
---

## Summary
Trace audit of four Gemma-4-12B runs on fastapi (the thread's model size is "12B"; the competition model is 31B, so the numbers do not transfer). The author's LB row was not found in the 2026-11-03 CSV. One comment (2026-11-03) compares three public submissions with declared configs 8192 / 4096 / 8 min / 240 s, reporting that model size is the only difference between scores 0.20, 0.18 and 0.05; this is the commenter's claim, not checked.

## Claims made (quoted numbers)
- [M] "Wall-clock is 76% pure decode at 17.25 tok/s — least-squares fit dt = 0.78 + 0.058·ct, r² = 0.9996 over 39 normal steps."
- [M] "8 of 43 steps hold 56% of the budget": 4 restatements of a file just read (1,788 tokens / 104 s in one message) and 4 prefill spikes (82 s for 251 tokens).
- [M] "read_file truncates at 150 lines. fastapi/params.py is 754 lines, was read 6 times, still never fully seen — and 1,152 lines across four runs were fetched twice."
- [M] Rules proposed by the author: "always pass both start_line and end_line"; "treat any single step over 60 s as a prompt bug".
- [M] Comment: three public submissions 0.20 / 0.18 / 0.05 share "8192 / 4096 / 8 min / 240 s". Only model size is said to differ.

## Possible claims for us
- [M, n=4 runs] read_file's 150-line cap is a tool fact worth a check against our tool registry (`tools/submission_rules.py`). Low: four runs, a different model size.
- [I] The 150-line read cap, if true for the 31B harness, would matter for the 754-line file case. Unverified against the harness.

## Files
Notebook xingling666/a-300-second-budget-is-5-000-output-tokens (3 votes) listed but not pulled.

## Updates
- 2026-11-03: first read.
