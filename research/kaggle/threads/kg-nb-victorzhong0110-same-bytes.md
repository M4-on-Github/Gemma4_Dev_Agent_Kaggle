---
id: kg-nb-victorzhong0110-same-bytes
topic_id: none (public notebook victorzhong0110/same-bytes-two-scores, kernel id_no 141297208)
title: Same Bytes, Two Scores (public notebook, title "Same Bytes, Two Scores")
author: victorzhong0110 (team "Victor Zhong" on the board, 0.20 rank 299 on 2026-11-06)
author_role: participant (team of the upstream-v8 pack kernel)
credibility: medium-low
topics: [noise, grading, budget]
first_seen: 2026-11-06
last_checked: 2026-11-06
---

## Summary
A participant notebook with the claim that one archive, submitted twice, scored 0.13 and 0.17. The notebook is offline and self-contained (it says so; `enable_internet` false in the metadata). Its numbers come from its own submissions and its own LB snapshot of 2026-10-28, not from the host. The sha256 check on the two archives is the author's own: we did not download kernel outputs, so the identity of the bytes is not verified by us.

## Claims made (quoted numbers)
- [M] Submissions to `gemma-4-developer-agent` (its table, section 1): 57516570 submitted 2026-10-22 08:14:01 UTC, "rerun crashed - removed from the board"; 57598496 2026-10-24 15:13:42 UTC, 0.15; 57629857 2026-10-25 12:28:14 UTC, 0.13 (kernel upstream-v8 v2); 57667013 2026-10-26 12:56:42 UTC, 0.17 (kernel upstream-v8 v4).
- [M] Both 57629857 and 57667013 produced a `submission.zip` with sha256 `205a677fdcbd122f50ac3138b1cda0403aeb625453c93edf4c53b7b691926186`. The author says both kernel outputs were downloaded and hashed on 2026-10-28; not verified by us.
- [M] Quoted host error text on the crashed rerun: "Your notebook hit an unhandled error while rerunning your code. Note that the hidden dataset can be larger/smaller/different than the public dataset".
- [M] "measured rerun noise (same bytes, different score): 0.04", and the author's rule of thumb: a gain must clear about 2 standard errors of noise / sqrt(draws).
- [M] Bands on the 2026-10-28 snapshot (N = 3974): 0.24 = 5 teams, 0.22 = 48, 0.20 = 214, 0.18 = 562, 0.17 = 678. Our 2026-11-06 snapshot (N = 4928, see the digest): 0.24 = 9, 0.22 = 67, 0.20 = 352, 0.18 = 796, 0.17 = 893. The bands have grown since 10-28; the author's band numbers are dated.
- [M] Its own row at 10-28: 0.17, rank 1484, 4 submissions. Our 2026-11-06 CSV row for `Victor Zhong` (`victorzhong0110`): 0.20, rank 299, 13 submissions, last 2026-11-05 12:00:47 [V, CSV].
- [M] honghanhhh's kernel title "Gemma 4 Baseline | LB 0.24" with the board row 0.18 rank 304 with 7 submissions (10-28). Our 2026-11-06 CSV row for `Hanh Tran` (`honghanhhh`): 0.18, rank 465, 7 submissions, last 2026-10-23 08:12:20 [V, CSV]. The 0.24 in the title is not a board score.
- [M] flexonafft's row at 10-28: 0.22, rank 20, 24 submissions. Our CSV row for `Igor Zharov` (`flexonafft`): 0.22, rank 25, 30 submissions, last 2026-11-02 08:41:55 [V, CSV]. Name differs; username matches.

## Possible claims for us
- A single submission is a draw: the same archive gave 0.13 and 0.17 in one participant's report (their 0.04 spread), and the 0.12, 0.17 and 0.18 spread of our own three draws (coordinator's data) is the same order. Plan §5.5 MDE is about 4 tasks (about 0.07). [I]
- The author's rule "read the bronze cut-off as a band" is a reading of the board; it is not a host rule. [I]

## Files
- `untrusted/victorzhong0110-same-bytes-two-scores-2026-11-06/same-bytes-two-scores.ipynb`: 27,537 bytes, SHA-256 `a176bd47566c898a75f35725166c96c76bfde0d824ab645ceafb1836253b6afe`. 13 cells (6 code), read with `research/kaggle/nb_read.py` as data (`python -I -X utf8`), never executed.
- `untrusted/victorzhong0110-same-bytes-two-scores-2026-11-06/kernel-metadata.json`: 715 bytes, SHA-256 `6a3bfc1e490719c47dad0d2cd935b416e184aa1b4b5514ccff6404f2b486fc33`. `enable_gpu` false, `enable_internet` false, `dataset_sources` metric/gemma-4-developer-agent-wheelhouse, `competition_sources` gemma-4-developer-agent.
- Kernel slug victorzhong0110/same-bytes-two-scores. Version: not in the metadata; the pull was on 2026-11-06 (`kaggle kernels pull -m`). Kernel last-run date not read.

## Not read
- The kernel's saved outputs and the author's pack-kernel outputs (`gemma4-submission-pack-upstream-v8`). The sha256 claim is not verified by us.

## Updates
- 2026-11-06: first read.
