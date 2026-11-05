---
id: S-012
date: 2026-11-04
status: scored
public_score: 0.18
kaggle_ref: 57970005
sha256: c22069db6623a07c9f133fef33a8c193393dca170c84676e708d0bd9f5077600
---

## Command
```
kaggle competitions submit -c gemma-4-developer-agent -f C:/Users/moemy/Documents/Kaggle/Gemma4_Dev_Agent_Kaggle/out/submission.zip -m "S-012 EXP-029 c22069db second LB draw of the v24-at-8 baseline tree (same zip as #11), pre-reg EXP-029 f56b226"
```

Note: the requested message had a semicolon before "pre-reg"; the Bash guard rejected it as chaining before anything ran (no upload happened on that attempt), so the semicolon was replaced by a comma. Submitted exactly once.

## Pre-submit check
`sha256sum out/submission.zip` = c22069db6623a07c9f133fef33a8c193393dca170c84676e708d0bd9f5077600, equal to `approvals/S-012.txt` and to the proposal. File already named `submission.zip`, so no copy was made.

## CLI output
```
100%|##########| 2.31k/2.31k [00:00<00:00, 8.25kB/s]
Submission ref: 57970005
0 submissions remaining today.
Successfully submitted to Google - The Gemma 4 Developer Agent Competition
```

## Top row of `kaggle competitions submissions -c gemma-4-developer-agent` (2026-11-04 03:51 UTC)
```
ref       fileName        date                        status                     publicScore
57970005  submission.zip  2026-11-04 03:51:09.290000  SubmissionStatus.PENDING   (blank)
description: S-012 EXP-029 c22069db second LB draw of the v24-at-8 baseline tree (same zip as #11), pre-reg EXP-029 f56b226
```
Previous row for the same zip (#11): ref 57750294, COMPLETE, 0.17.

## Polling
Not polled. Grading has taken 6 to 22 hours (up to 5 days observed); update this file to `status: scored | error` with `public_score` only when asked.

## Score (read 2026-11-05 by the lead; reported by the user first)
`kaggle competitions submissions`: ref 57970005 COMPLETE, public 0.18 = 11 of 58 (scores are truncated k/58).
Reading, EXP-029 §4 as written: **row 3 (k = 6 to 14)** fires. Same zip as #11 (10/58), so the one-task difference
is draw noise. Pooled baseline for the v24-at-8 zip: 21 of 116 = 0.181, about 10.5 tasks per draw, sd ~2.9 per draw.
Second completion at the 8-min cap on the hidden set. No tree change on this alone; the next slot goes to the next
candidate. Not yet in `submissions.md` row 12 or EXP-029 §9 (experimenter job).
