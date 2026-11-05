---
id: kg-751487-scorer-like-sandbox-gold-pass
topic_id: 751487
title: Local eval in a scorer-like sandbox: gold patches pass on 127/129 public tasks (was 52) (Zbigniew Kirchner)
author: Zbigniew Kirchner (participant)
author_role: participant
credibility: medium
topics: [grading, sandbox, test-dependencies, wheelhouse]
first_seen: 2026-11-05
last_checked: 2026-11-05
---

## Summary
A participant ran every public reference (gold) patch through the official swegemma grader in a plain notebook (52 of 129 pass) and in a notebook rebuilt to resemble the published Dockerfile.sandbox (127 of 129 pass). Posted 2026-10-21 20:32:20 UTC, 14 votes, 5 comments. Credibility [M]: a participant calibration with a published notebook and CSV; the mechanism is inferred by the author. Our own EXP-036 (CPU re-grade, 2026-11-05) reports 6 dev-48 tasks that grade the same with the gold and the empty patch, which is a different check.

## Claims made (quoted numbers)
- Plain notebook vs scorer-like, gold pass counts: fastapi 10 / 67 vs 66 / 67; rich 39 / 48 vs 47 / 48; requests 3 / 13 vs 13 / 13; httpx 0 / 1 vs 1 / 1. Totals 52 vs 127 of 129 (the sums check).
- Setup: "a clean venv, pytest, the competition wheels, and the missing test packages", based on "the published Dockerfile.sandbox".
- "The remaining 2 tasks appear internally inconsistent because their required tests have opposite skip conditions." The text read does not name them. kg-755554 describes two tasks with opposing skip markers (fastapi_14186 and rich_3486); whether these are the same two is our inference, not the author's statement.
- "A few old public tasks need period-correct versions (e.g. Pygments for 7 rich tasks). The CSV marks them."
- Comment, 2026-10-22 06:06 (Ahmed Awelkair): "It was clear that subprocess (local) uses python 3.12.13 and the Docker image's used python 3.13. Docker was the default though according to the HARNESS_README.md." Author's reply, 10-22 16:25: "Good question. I don't know whether Kaggle submissions use Docker or subprocess as the san[dbox]". Unanswered by a host.
- Notebooks and CSV are Apache-2.0 (author's reply, 10-27).

## Possible claims for us
- A notebook calibration that installs the missing test packages recovers most fastapi gold passes; the plain subprocess notebook does not. This is what our own §1g and 750345 describe. [M]
- Whether the scorer uses Docker (3.13) or subprocess (3.12) is still unanswered by any host. [I]

## Files
None downloaded in this job (the author's notebook and wheels dataset were not fetched).

## Updates
- 2026-11-05: first full read (saved topic text). Digest uses the counts only.
