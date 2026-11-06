---
id: briefing
updated: 2026-10-29
---

## Where we stand

| Track | Ours | Frontier | Gap in tasks | Next move |
|---|---|---|---|---|
| Main | 0.13 = 8/58 best (#5, #6); #11 pending 21.5 h | 0.24 = 14/58 (rank-3 v24, best of >= 12 uploads); field mode 0.17 | 6 to the frontier, 2 to the mode | read EXP-028 (both arms complete), then #11, then choose #12 (D-002) |
| Paper | draft 2,716 / 3,000 words, section 4 stub | unknown; two public writeups scouted | n/a | section 4 from EXP-028 after critic review (D-003); due Nov 12 |

## What we learned

- The cap, not the prompt wording, is the one lever with a one-variable contrast behind it: the same bundle scored 7/58 at 4.5 min and 14/58 at 8 min, and their own release says 5.5 -> 8 min took them from 0.12-0.17 to 0.18-0.24 (C-002, kg-rank3-apache). Their prompt stops on its own, so 8 min projects 9.9-10.6 h; ours ran to the cap and would project 14 h (C-003, C-008).
- About 38% of `edit_file` calls never reached the file because the model emits an unterminated string literal and the agent then repeats the same call up to 19 times (C-004, EXP-024/026). The detector everyone would write misses it. A single-argument shell route did not move the next call after a first loss (0 of 6, EXP-028 row 4; C-005).
- One LB draw cannot see anything smaller than ~4 tasks; ten draws of prompt surgery read 4-8 with no trend (C-001, C-009). The lineage is retired (D-001).

## Open decisions

- #12 tree and cap — decided by EXP-028 §4 and EXP-027 §4 once read; needs your approval as S-012 (sha in `approvals/S-012.txt`) — needed by: the next UTC day you want to use.
- Critic backfill order for the migrated claims — recommended EXP-024, EXP-025, EXP-027 first (they feed the paper) — needed by: Nov 3.
- Your one-line prediction for #11 (k of 58) for the calibration table.

## Calibration

| EXP / upload | Predicted (pre-registered) | User's prediction | Actual | Held? |
|---|---|---|---|---|
| #5 EXP-017 (4-change bundle) | 0.17 or it did not happen; dead band 0.06-0.15 | not asked | 0.13 = 8/58 | inside dead band: uninformative |
| #8 EXP-023 (v24 at 4.5) | readings in EXP-023 §4 | not asked | 0.12 = 7/58 | per EXP-023 §4 (not re-read here) |
| EXP-025 Arm A affected tasks | risk named: near 4-6 means underpowered | not asked | 6 | the risk fired |
| #11 EXP-027 (v24 at 8) | k ~ 10, band 6-14 | not asked | pending | |
| EXP-028 | T1-T4, rows 1-8 | not asked | T2 + T4, row 4; critic light accepted | |

## Worth your time

- `experiments/EXP-028-v24-at-8-dev48-paired.md` §4: the readings that will pick #12, written before the data.
- `knowledge/claims.md` C-002 to C-005: the four claims the next two weeks turn on.
- `research/2026-10-28-kaggle-open-scouting.md` §3: the rank-3 team's per-task behaviour, the clearest picture of what a scoring run looks like.
