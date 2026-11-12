---
id: S-017
date: 2026-11-12
status: pending
public_score: null
kaggle_ref: 58287318
submitted_utc: 2026-11-12 23:27:28 (Kaggle list timestamp)
landed_before_midnight_utc: yes (2026-11-12 slot)
sha256: c22069db6623a07c9f133fef33a8c193393dca170c84676e708d0bd9f5077600
experiments: [EXP-027, EXP-028, EXP-031]
---

# S-017 result

Fourth leaderboard draw of the 31B v24-at-8 baseline zip (experiments/EXP-027/v24_at8.zip, copied to out/submission.zip; same bytes as S-011, S-012 and S-013).

## Checks before upload
- approvals/S-017.txt content equals the proposal sha: c22069db6623a07c9f133fef33a8c193393dca170c84676e708d0bd9f5077600
- `sha256sum experiments/EXP-027/v24_at8.zip` and, after the `cp`, `sha256sum out/submission.zip` returned the same hash.
- `kaggle competitions submissions gemma-4-developer-agent` before the submit: no pending upload, none dated 2026-11-12 (latest was ref 58178151, 2026-11-09 23:56 UTC, COMPLETE, 0.01).

## Command (run once)
```
kaggle competitions submit -c gemma-4-developer-agent -f out/submission.zip -m "S-017 c22069db fourth LB draw of the v24-at-8 baseline zip"
```

## Kaggle ref
58287318

## CLI output
```
100%|##########| 2.31k/2.31k [00:00<00:00, 6.80kB/s]
Submission ref: 58287318
0 submissions remaining today.
Successfully submitted to Google - The Gemma 4 Developer Agent Competition
```

## List entry after submit
```
58287318,submission.zip,2026-11-12 23:27:28.813000,S-017 c22069db fourth LB draw of the v24-at-8 baseline zip,SubmissionStatus.PENDING,,
```

## Status
pending. It landed at 23:27:28 UTC on 2026-11-12, before 00:00 UTC, so it took the 2026-11-12 slot. Grading has taken 6 to 22 hours. Poll only when asked; then set `status: scored | error` and `public_score`.
