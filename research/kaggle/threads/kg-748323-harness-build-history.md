---
id: kg-748323-harness-build-history
topic_id: 748323
title: Same 314 code-graph queries, four wheelhouse builds (CPU replay), with the 12 Oct same-version repack (kimdonggyu1255)
author: kimdonggyu1255 (participant)
author_role: participant
credibility: medium
topics: [wheelhouse, harness, graph-tools, grading]
first_seen: 2026-11-05
last_checked: 2026-11-05
---

## Summary
Participant replay of 314 recorded code-graph tool calls (70 public tasks, nine practice runs) through four harness builds, plus a diff of the archived wheels. Posted 2026-10-11 14:49:45 UTC, 5 votes, 3 comments. The author gives a method and a replay notebook (public CPU notebook, 2026-10-12). Credibility [M]: a participant's measurement, not a host statement; the build labels are the author's.

## Claims made (quoted numbers)
- Build table, same 314 calls: before 30 Sep (swegemma 0.2.7) 82 calls with results; 30 Sep (still 0.2.7) 11; 8 Oct (0.2.10) 270; 9 Oct (0.2.11) 270. Median response 79, 94.5, 5,763, 5,763 characters.
- "Compare builds by file checksum, not by version: the 30 Sep build changed 10 swegemma .py files, 5 of them in the graph code, without bumping 0.2.7." The 8 Oct build changed 9 .py files; the 9 Oct build changed 4 and removed 2.
- Replay check: each run replayed under its own build reproduces the recorded outcome for 314 of 314 calls.
- From 8 Oct: "include_thoughts: false no longer switches thinking off when a thinking budget is set; it only hides the thoughts" (also reported in 747914).
- "The 8 Oct build drops edits to test files from the submitted patch and prunes the repository listing in the first prompt." (participant diff of archived wheels; not host-confirmed)
- "The 9 Oct build removed swegemma/models/discovery.py (and models/registry.py). The official starter notebook ... still runs from swegemma.models.discovery import validate_single_declared_model, so notebooks built from it stop at that line on the current wheelhouse." The author wrapped the import and redefined the check on top of `adk_submission.discovery.discover_declared_models`. The current starter (read 2026-11-05) already imports from `adk_submission.discovery`.
- Update, 2026-10-14 05:56:58 UTC (kimdonggyu1255, comment on the same topic): "a fifth harness build appeared on 12 Oct 19:51 UTC — swegemma 0.2.11 repackaged under the same version number (5 .py files differ from the 9 Oct build: budget, cli, config, context...)".
- Measured on the 9 Oct build, public Budget-Fit configuration (112 tasks): 105 of 524 edit_file/write_file calls rejected with "mandatory input parameters are not present"; from 15 tasks, 6 of which account for 85; in 47 of the 105 code appears as argument names. Participant measurement; the same error string is in our own EXP-024 notes.

## Possible claims for us
- The harness version string does not identify the build: 0.2.11 names at least two builds (9 Oct and 12 Oct repack) with different .py files. Any claim keyed to "0.2.11" needs a file checksum. [I]
- Our §1b record (2026-10-14) lists swegemma 0.2.11 without a checksum, so we cannot say which 0.2.11 build our notes describe. [I]
- The 12 Oct repack has the same creation date as the wheelhouse dataset (2026-10-12 19:51:31), so no change is visible after it on the dataset page. [V for the dataset date; the file diff is the author's]

## Files
None (the replay notebook is the author's; not downloaded in this job).

## Updates
- 2026-11-05: first read in full (saved topic text). Cross-references: the "v31" wheelhouse claim is in 752490 (Sukhendu Sain, 2026-10-25), a private GPU diagnostic, not a build diff; see the digest.
