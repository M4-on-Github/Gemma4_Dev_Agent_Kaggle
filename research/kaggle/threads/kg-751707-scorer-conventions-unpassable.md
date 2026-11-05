---
id: kg-751707-scorer-conventions-unpassable
topic_id: 751707
title: -p no:anyio and four other scorer conventions make about a quarter of real fixes unpassable (Hersh Mittelman)
author: Hersh Mittelman (participant)
author_role: participant
credibility: medium
topics: [grading, pytest, swegemma, test-dependencies]
first_seen: 2026-11-05
last_checked: 2026-11-05
---

## Summary
A participant ran real post-release fixes from 38 Python libraries through the verification conventions swegemma 0.2.x uses. Posted 2026-10-22 15:01:25 UTC, 0 votes, 2 comments. Credibility [M]: the author built an external set and reports counts by cause; no host reply. The counts add up (79 + 101 + 65 + 24 + 8 = 277).

## Claims made (quoted numbers)
- "In 277 of 1,143 cases (24%), the reference fix fails verification only because of one of those conventions. The other 111 reference fixes that fail, fail under the repository's own settings too, so they are not counted."
- Causes: "-p no:anyio alone (79 cases)"; "The pytest.ini overwrite (101 cases)"; "Non-test files as targets (65 cases)"; "A required test skipped on Linux (24 cases): swegemma 0.2.11 counts a skipped required test as a failure"; "A JUnit report over 10 MiB (8 cases, python-multipart)".
- "The harness reads the report back through the sandbox's 10 MiB output cap, gets a truncated file and marks the task unresolved even when every test passed."
- The author's stated reading of the hidden set: "if the hidden tasks were checked with the same harness before release, tasks from codebases that test through anyio or rely on their own pytest configuration were filtered out of it; if any were not, no agent patch can pass them."

## Possible claims for us
- Under 0.2.11, a required test skipped on the grader's platform is a failure, so a patch whose new test is platform-skipped cannot pass. This matches the skip-marker issue in fastapi_14186 and rich_3486 (see kg-755554). [M, consistent with our §1g]
- Whether the hidden set was filtered by this harness is not answered by any host. [I]

## Files
None. The author's FreshSWE-Py dataset (663 tasks, 33 repositories) is not fetched here.

## Updates
- 2026-11-05: first full read (saved topic text). Cited in the digest as a caution against reading pass counts across repositories.
