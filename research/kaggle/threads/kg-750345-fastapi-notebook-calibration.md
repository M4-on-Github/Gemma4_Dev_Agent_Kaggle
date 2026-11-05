---
id: kg-750345-fastapi-notebook-calibration
topic_id: 750345
title: Calibrating in a notebook? About a third of the fastapi tasks cannot pass there (missing test dependencies) (Domenic Federico)
author: Domenic Federico (participant)
author_role: participant
credibility: medium-low
topics: [grading, test-dependencies, wheelhouse, sandbox]
first_seen: 2026-11-05
last_checked: 2026-11-05
---

## Summary
Participant report that the hidden tests of 21 of 67 public fastapi tasks import dirty_equals or inline_snapshot, and neither package has a wheel in the competition wheels directory. Posted 2026-10-17 21:01:41 UTC, -1 votes, 1 comment. Credibility [M] for the counts; the claim about the organizers' file is second-hand and unverified (see below).

## Claims made (quoted numbers)
- "the hidden tests of 21 of the 67 public fastapi tasks import dirty_equals or inline_snapshot, and neither package has a wheel in data/wheels. Those test files fail at collection (pytest exit code 2) regardless of the patch."
- A run of v15e on the author's 60-task set: "17 of 35 fastapi tasks exited with code 2, and 7 of those 16 patches pass in a sandbox that has the two packages installed."
- "The organizers' task_soundness.csv shows the gold patches passing in the scoring environment, so this is a notebook-calibration floor, not a scorer issue." This file is not in our data/raw/ and was not read in this job, and no host has posted it. Treat as unverified. (The 754586 thread, 2026-10-31, asks the same kind of question and does not cite this file.)
- Workaround: "preinstall dirty-equals and inline-snapshot in the sandbox base; it would be good if the wheels dataset included them."
- Comment, 2026-10-21 19:43 (Zbigniew Kirchner): "In a plain notebook the gold patch passes on only 10 of 67 fastapi tasks: besides the missing wheels, old commits meet a too-new starlette". See kg-751487.

## Possible claims for us
- The public wheels directory lacks dirty_equals and inline_snapshot (our own check of the 41-file wheelhouse on 2026-11-05 agrees). [V for the wheelhouse listing; our check]
- The claim that organizer soundness data show gold passing in the scorer is unverified until the file or a host statement is seen. [I]

## Files
None.

## Updates
- 2026-11-05: first full read (saved topic text).
