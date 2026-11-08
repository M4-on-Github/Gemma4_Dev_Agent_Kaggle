---
id: S-015
date: 2026-11-08
status: pending
public_score: null
kaggle_ref: 58143906
submitted_utc: 2026-11-08 23:57:43 (Kaggle list timestamp)
landed_before_midnight_utc: yes (2026-11-08 slot)
sha256: 98bd942fe17aea64d8aa7211e28b4590207c69f6308a27a0caf3b5aa94947a05
experiments: [EXP-061]
---

# S-015 result

EXP-061: an `LlmAgent` root over the EXP-052 draft fan-out pipeline (E4B). out/submission.zip is a byte copy of the EXP-061 pack.

## Checks before upload
- approvals/S-015.txt content equals the proposal sha: 98bd942fe17aea64d8aa7211e28b4590207c69f6308a27a0caf3b5aa94947a05
- `sha256sum out/submission.zip` returned the same hash (run before the submit, not after; the dispatch asked for the reverse order and the submitter kept the standing order).
- The pre-submit list check was skipped because the slot was closing within minutes; the CLI would have rejected a used slot. The list after the submit shows the previous upload (ref 58106393) dated 2026-11-07, so nothing else was dated 2026-11-08.
- The plan.md 5.8 override and the skipped critic `prereg` rest on the user's word recorded in the proposal; the submitter did not verify them beyond the approval file and hash.

## Command (run once)
The dispatch's command lacked `-c`; the run used:
```
kaggle competitions submit -c gemma-4-developer-agent -f out/submission.zip -m "S-015 EXP-061 LlmAgent root over EXP-052 draft fan-out, sha 98bd942f"
```

## Kaggle ref
58143906

## CLI output
```
100%|##########| 13.2k/13.2k [00:00<00:00, 45.8kB/s]
Submission ref: 58143906
0 submissions remaining today.
Successfully submitted to Google - The Gemma 4 Developer Agent Competition
```

## List entry after submit
```
58143906,submission.zip,2026-11-08 23:57:43.563000,"S-015 EXP-061 LlmAgent root over EXP-052 draft fan-out, sha 98bd942f",SubmissionStatus.PENDING,,
```

## Status
pending. It landed at 23:57:43 UTC on 2026-11-08, before 00:00 UTC, so it took the 2026-11-08 slot. Grading has taken 6 to 22 hours. Poll only when asked; then set `status: scored | error` and `public_score`.
