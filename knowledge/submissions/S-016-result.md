---
id: S-016
date: 2026-11-09
status: pending
public_score: null
kaggle_ref: 58178151
submitted_utc: 2026-11-09 23:56:17 (Kaggle list timestamp)
landed_before_midnight_utc: yes (2026-11-09 slot)
sha256: 3b9aea1592178bbbd131c8ac5c0fa10ddfdd8fdbd567a629b346688b0c25ea5e
experiments: [EXP-064]
---

# S-016 result

EXP-064 E4B pipeline: root re-transfer and location-diverse drafters (experiments/EXP-064/exp064_loc.zip, copied to out/submission.zip by the submitter, replacing the EXP-061 zip there).

## Checks before upload
- approvals/S-016.txt content equals the proposal sha: 3b9aea1592178bbbd131c8ac5c0fa10ddfdd8fdbd567a629b346688b0c25ea5e
- `sha256sum experiments/EXP-064/exp064_loc.zip` and, after the `cp`, `sha256sum out/submission.zip` returned the same hash.
- The pre-submit list check was skipped because the slot was closing within minutes; the CLI would have rejected a used slot. The list afterwards shows the previous upload (ref 58143906) dated 2026-11-08, so nothing else was dated 2026-11-09.
- The 18.00 h gate override and the missing critic review rest on the user's word recorded in the proposal; the submitter checked only the approval file and the hash.

## Command (run once)
```
kaggle competitions submit -c gemma-4-developer-agent -f out/submission.zip -m "S-016 EXP-064 E4B pipeline, root re-transfer and location-diverse drafters, zip 3b9aea15"
```

## Kaggle ref
58178151

## CLI output
```
100%|##########| 14.4k/14.4k [00:00<00:00, 43.4kB/s]
Submission ref: 58178151
0 submissions remaining today.
Successfully submitted to Google - The Gemma 4 Developer Agent Competition
```

## List entry after submit
```
58178151,submission.zip,2026-11-09 23:56:17.957000,"S-016 EXP-064 E4B pipeline, root re-transfer and location-diverse drafters, zip 3b9aea15",SubmissionStatus.PENDING,,
```

## Status
pending. It landed at 23:56:17 UTC on 2026-11-09, before 00:00 UTC, so it took the 2026-11-09 slot. Grading has taken 6 to 22 hours. Poll only when asked; then set `status: scored | error` and `public_score`.
