---
id: S-014
date: 2026-11-07
status: scored
public_score: 0.05
kaggle_ref: 58106393
submitted_utc: 2026-11-07 22:44:47 (Kaggle list timestamp)
sha256: 9de869bd2cd8853b72d653d06b9acef3e03794c8b588c26494435774dda11ac0
experiments: [EXP-050]
---

# S-014 result

E4B single loop, variant A (experiments/EXP-050/variant-a-e4b-8min.zip, byte copy at out/submission.zip).

## Checks before upload
- approvals/S-014.txt content equals the proposal sha and the dispatch sha: 9de869bd2cd8853b72d653d06b9acef3e03794c8b588c26494435774dda11ac0
- `sha256sum out/submission.zip` returned the same hash.
- `kaggle competitions submissions gemma-4-developer-agent` before the submit: no pending upload, none dated 2026-11-07 (latest was ref 58037856, 2026-11-05 23:34 UTC, COMPLETE, 0.12).

## Command (run once)
```
kaggle competitions submit -c gemma-4-developer-agent -f out/submission.zip -m "S-014 EXP-050 E4B single loop variant A 9de869bd"
```

## Kaggle ref
58106393

## CLI output
```
100%|##########| 2.43k/2.43k [00:00<00:00, 8.14kB/s]
Submission ref: 58106393
0 submissions remaining today.
Successfully submitted to Google - The Gemma 4 Developer Agent Competition
```

## List entry after submit
```
58106393,submission.zip,2026-11-07 22:44:47.313000,S-014 EXP-050 E4B single loop variant A 9de869bd,SubmissionStatus.PENDING,,
```

## Score (polled 2026-11-08)
Polled once with `kaggle competitions submissions gemma-4-developer-agent --csv` on 2026-11-08. List entry as the CLI printed it:
```
58106393,submission.zip,2026-11-07 22:44:47.313000,S-014 EXP-050 E4B single loop variant A 9de869bd,SubmissionStatus.COMPLETE,0.05,
```
status: scored, public_score: 0.05 (the board shows two decimals; the lead reads this as 3 of 58).
