---
id: kg-755066-wrapper-stage1
topic_id: 755066
title: Stage 1 of wrapper engineering: settings, budgets and lessons
author: Sukhendu Sain (LB account ssain18)
author_role: top-lb
credibility: medium
topics: [sampling, budget, prompt, selection, noise]
first_seen: 2026-11-03
last_checked: 2026-11-03
---

## Summary
Local study, not the LB: 376 attempts across 40 public tasks (4 studies) with a basic six-tool wrapper on Gemma 4 31B QAT, four L4 GPUs, 32,768-token context. The author's LB row is 0.17 (rank 1142, 20 submissions, last 2026-10-25), which makes the account medium credibility under the rule. Numbers are per-study with different task sets; the author warns to compare within columns only. Read in full (text post, no comments).

## Claims made (quoted numbers)
- [M] Sweep 1 (130 attempts, 5 tasks x 2, 13 profiles) and sweep 2 (126 attempts, 7 tasks x 3, 6 profiles). Temperature 0 vs 1: 7/10 vs 7/10 and 11/21 vs 12/21. Output 4k / 6k / 8k: 7/10 / 6/10 / untested and 10/21 / 12/21 / 10/21. Thinking 2k vs 4k: 6/10 vs 6/10 and 10/21 vs 10/21. Top-p 0.5 / 0.8 / 1: 3/10 / 4/10 / 6/10 (sweep 1 only).
- [M] "Temperature 0 was faster than 1 on average in both comparisons, with close scores." Author kept 0 as default.
- [M] Larger comparison, 15 tasks x 3 repeats, 20 min per attempt: profile A (temp 0, out 4k, thinking 4k) 24/45, mean agent time 470.10 s; profile B (temp 1, out 6k, thinking 2k) 23/45, mean 437.26 s. On 22 matched attempts both passed, B used 23.6% less evaluator time.
- [M] Profile temp 0, out 6k, thinking 2k, top-p 1, on 30 tasks, 10 min and 50 model requests: 12/30, mean 346.49 s; 18 tasks labelled complex; on 14 overlapping tasks 7/14 (matches B).
- [M] "every B success and every success in the latest run finished within 45 model requests. Forty would interrupt several successful histories. I chose 50."
- [M] "Of 7,424 completed commands, 24 exceeded 120 seconds and all failed or timed out." Three successful checks took about 104 s.
- [M] Author's next setting: 10 min, 50 requests, 120 s per command. "120 tasks in 12 hours leaves six minutes each before overhead."

## Possible claims for us
- [M, n=10 to 21 per arm] Top-p below 1.0 scored lower (3/10 and 4/10 vs 6/10) in one sweep; temperature 0 vs 1 and thinking 2k vs 4k tie. Low: small n, different defaults.
- [M] Commands over 120 s failed in all 24 cases in the author's data (none succeeded). Supports a per-command cap question, not a settled rule.
- [I] A request cap of 40 would cut several successful histories on this wrapper (author's data), which bears on C-007.

## Files
None downloaded; text read from the topic.

## Updates
- 2026-11-03: first read.
