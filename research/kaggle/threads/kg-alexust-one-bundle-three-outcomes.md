---
id: kg-alexust-one-bundle-three-outcomes
topic_id: alexust/one-bundle-three-outcomes-0-24-0-17-no-score
title: One Bundle, Three Outcomes: 0.24, 0.17, No Score
author: Alex Ust
author_role: participant
credibility: medium
topics: [budget, noise, prompt]
first_seen: 2026-11-03
last_checked: 2026-11-03
---

## Summary
Notebook by an account at LB 0.17 (rank 1685, 11 submissions, last 2026-11-02). It reports that the honghanhhh 8-min / 28-call bundle, uploaded byte for byte, returned "Your submission notebook exceeded the allowed runtime" (2026-10-30), while the same caps with `max_time_minutes: 7` scored 0.15 (2026-11-02). It also reports a 40-call / 8-min bundle that timed out (2026-10-22). Its timing projection (k = slowdown factor, 101 local tasks scaled to 120) is the author's model, not a host figure. Read as text; nothing executed.

## Claims made (quoted numbers)
- [M] Submission table (author's own uploads): 28/8 with `honghanhhh` bundle, 0.24 (author's draw of that bundle); 28/8 byte-identical, 2026-10-30, "no score: exceeded the allowed runtime"; 28/7 with prompt line changed, 2026-11-02, **0.15, finished in time**; 28/8 + one prompt line, 2026-10-27, 0.17; 28/8 call-saving prompt, 2026-10-29, 0.12; 40/8, 2026-10-22, "no score: exceeded the allowed runtime"; 40/6 with thinking 1024, two draws, 0.12 and 0.10.
- [M] Local timing: "We timed 101 local runs of this exact bundle" on RTX PRO 6000 96 GB, vLLM 0.19.1, `max_model_len` 32768, swegemma 0.2.11, three tasks at a time.
- [I, author's model] "Near k = 1.6-1.7 its projected total is about 12 h" for 8 min. The 7-min total reaches 12 h only at k = 1.83. Depends on an unpublished scorer speed.
- [M] Notebook asserts: "The 12-hour limit covers all ~120 hidden tasks, sandbox setup included, patch validation excluded." Host statement [V] says 12 h including setup; the patch-validation exclusion is the author's reading.
- [V, LB CSV] Alex Ust: rank 1685, 0.17, 11 submissions.

## Possible claims for us
- C-003/C-008: the 8-min / 28-call file set exceeded the runtime on the scorer for an identical copy once (10-30). Its 7-min variant finished once. One draw each. Supports the caution in `plan.md §5.8`.
- C-007: 40 calls at 8 min timed out once (10-22), against the 40-call claim. One draw.

## Files
- untrusted/alexust-one-bundle-three-outcomes/one-bundle-three-outcomes-0-24-0-17-no-score.ipynb, 21,440 B, SHA-256 e4d184182eca894e17261b2b920ab6a85f9457f845293ce86a57cb262fb2c6d1. Licence: not stated in the notebook text read. Embedded timing data read as text only.

## Updates
- 2026-11-03: first read.
