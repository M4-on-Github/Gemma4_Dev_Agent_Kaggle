---
id: kg-757588-rerun-variance
topic_id: 757588
title: I reran a public 0.24 bundle unchanged and got 0.17 (data and short paper)
author: Harshit Kumar (post); Allan Kipruto, "Unknown" and others (comments)
author_role: participant
credibility: medium; one rerun reported, no run logs attached
topics: [noise, grading, reproducibility]
first_seen: 2026-11-17
last_checked: 2026-11-17
---

## Summary
A participant reran an unchanged public 0.24 bundle and got 0.17 on the public leaderboard. Commenters add that a skill-only change scored 0.13 to 0.20 and that some resolved=True tasks reran as resolved=False. No host reply. This is the clearest report in the window of public-score variance on an identical bundle.

## Claims made (quoted numbers)
- [M] Harshit Kumar, 2026-11-10: an unchanged public bundle at 0.24 rerun scored 0.17 (title).
- [M] Comment 3554013, 2026-11-12, display name "Unknown": "variance is about 4-5 tasks in max(1 / ( 120 / 2 )) = 0.017 per task"; that account changed only skills and reports LB 0.13 to 0.20.
- [M] Comment 3552827, Allan Kipruto, 2026-11-10: "re-runned resolved=True tasks, and some were appearing resolved=False."
- [V, plan §5.5] The public LB has 58 tasks and a measured MDE of about 4 tasks (about 0.07). A 0.07 move is the noise floor; the 0.17 rerun is 0.07 below the reported 0.24.

## Possible claims for us
- [I] A single public draw cannot separate 0.18 from 0.22. Our own S-017 draws (0.13 for the baseline zip, 4 draws pooled to 0.155 per submissions.md) already show the same spread.
- [I] Choose the next upload on a paired dev-48 comparison, not on one public number.
- [M, unverified] Allan Kipruto's "resolved=True to False on rerun" is a claim about the harness. If it holds, a fixed dev-48 result has its own variance; repeat the same task set before reading a difference.

## Files
None downloaded.

## Updates
- 2026-11-17: first read. Comments 3554013 (11-12) and 3552827 (11-10) read; no host reply in the thread.
