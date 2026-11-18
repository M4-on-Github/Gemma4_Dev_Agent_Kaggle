---
id: kg-ds-akshaymathur-telemetry
topic_id: companion dataset of paper-track writeup "Gemma 4 agent paper telemetry" (slug inferred from the untrusted directory name `akshaymathur777/gemma4-agent-paper-telemetry`; not confirmed by a kernel reference)
title: "Gemma 4 agent paper telemetry (derived episode and run metrics)"
author: akshaymathur777
author_role: participant (paper track)
credibility: [M] derived metrics from the author's 28 L4x4 kernels and 9 to 11 hosted submissions; the author's own holdout sets are 5 tasks each, so per-run counts are too small to rank configs; column meanings for CWE and repro_file_leaked are not defined in the files we read
topics: [noise, budget, tools, edit-reliability, grading]
first_seen: 2026-11-17
last_checked: 2026-11-17
---

# akshaymathur777: telemetry dataset

## Untrusted file record (read as data; never executed or extracted)

| File | Bytes | SHA-256 | Licence | Pulled |
|---|---|---|---|---|
| `untrusted/akshaymathur777-gemma4-agent-paper-telemetry-2026-11-17/gemma4-agent-paper-telemetry.zip` | 48,190 | `596ea6fa5c99737327dd45e2c604050f0317179bb8116f41ef4cce14800ff826` | Apache-2.0 (phase-1 note) | 2026-11-17 |

- **Hash correction:** the phase-1 summary recorded a shorter string for this archive. The full SHA-256 above was
  recomputed with `research/kaggle/sha_file.py` on 2026-11-17.
- Members: `analyze_traces.py` (9,647 B), `episode_metrics.csv` (16,878 B), `results.csv` (5,766 B),
  `step_trajectories.csv` (268,147 B; not read).

## Counts we computed from `episode_metrics.csv` (`research/kaggle/zip_csv_count.py`, read as data)

- **124 episode rows** (the docstring of `analyze_traces.py` says 128 episodes; the count does not match).
- Resolved: **51 of 124**.
- `termination_class`: Resolved 51, CWE 49, TestFailed 9, Timeout 8, BudgetExceeded 5, EmptyPatch 2. The label
  CWE is not defined in the files we read.
- `repro_file_leaked` = 1 on **8 rows**; of those, **2 resolved**. The column is not defined in the files we read.
- Holdout and practice rows are grouped by kernel slug; the largest group is 5 tasks.

## Hosted submissions in `results.csv` (their public LB draws)

- `v0.4`, 2026-10-14, kaggle ref 57183476, **0.17**, sha `6b0fccec...0870`.
- `v0.4-repeat`, 2026-10-26, ref 57667599, **0.12**, **byte-identical** to the 0.17 zip (the file's own note:
  "noise span 0.12..0.17").
- `v0.20`, 2026-11-04, ref 57985572: **TIMEOUT**, "runtime exceeded; COMPLETE with blank publicScore; error:
  submission notebook exceeded allowed runtime" (agenttool, max_tool_calls 36).
- `v0.24`, 2026-11-11, ref 58246283: **PENDING** at the last file date (single-agent tc28, min 8, out 8192).
- The `results.csv` lists **11 hosted rows**; the `analyze_traces.py` docstring says 9 hosted submissions.

## Relevance

- The identical-zip pair (0.17 and 0.12) is an outside data point for C-001's noise floor; it does not change it.
- The v0.20 timeout on the same tree family is a second outside case for the runtime margin question (C-003, C-008).
