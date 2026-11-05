---
id: S-013
date: 2026-11-05
status: pending
public_score: null
kaggle_ref: 58037856
submitted_utc: 2026-11-05 23:34:14 (Kaggle list timestamp)
sha256: c22069db6623a07c9f133fef33a8c193393dca170c84676e708d0bd9f5077600
experiments: [EXP-031]
---

# S-013 result

Third draw of the v24-at-8 baseline zip (same sha as #11 and #12).

## Checks before upload
- approvals/S-013.txt content equals the proposal sha: c22069db6623a07c9f133fef33a8c193393dca170c84676e708d0bd9f5077600
- `sha256sum out/submission.zip` returned the same hash.
- `kaggle competitions submissions gemma-4-developer-agent` before the submit: no pending upload, none dated 2026-11-05 (latest was ref 57970005, 2026-11-04 03:51 UTC, COMPLETE, 0.18).

## Command (run once)
```
kaggle competitions submit -c gemma-4-developer-agent -f out/submission.zip -m "S-013 EXP-031 c22069db third LB draw of the v24-at-8 baseline zip"
```

## Kaggle ref
58037856

## CLI output
```
100%|##########| 2.31k/2.31k [00:00<00:00, 6.38kB/s]
Submission ref: 58037856
0 submissions remaining today.
Successfully submitted to Google - The Gemma 4 Developer Agent Competition
```

## List entry after submit
```
58037856,submission.zip,2026-11-05 23:34:14.750000,"S-013 EXP-031 c22069db third LB draw of the v24-at-8 baseline zip",SubmissionStatus.PENDING,,
```

## Status
pending. Grading has taken 6 to 22 hours. Poll only when asked; then set `status: scored | error` and `public_score`.
