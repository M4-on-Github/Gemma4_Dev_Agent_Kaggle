---
id: plan
updated: 2026-10-29
direction: D-002, D-003
---

## Next experiments (in order)

| # | Claim | What it tests | Endpoint | Expected gain | GPU-h | Why now |
|---|---|---|---|---|---|---|
| 1 | C-003, C-008, C-007 | EXP-028 Arm R analysis: time profile, projected hours, 28-call incidence | mean/p90/frac at cap; projected hidden hours; T1-T4 | decides the cap and the next arm | 0 (run complete) | both kernels COMPLETE; nothing else can be read until this is |
| 2 | C-005 | EXP-028 RH vs R: post-loss compliance, harm guard | Fisher on first-loss events; McNemar on empty patch | decides the #12 tree | 0 (run complete) | same download |
| 3 | C-002 | Read #11 against EXP-027 §4 | k of 58 | adopt / fall back to 6.0 | 0 | pending since 2026-10-28 22:39 UTC |
| 4 | C-007 | `max_tool_calls` 28 -> 40 on the chosen tree, paired with it | calls-cap incidence, empty patch, time profile | <= 2 tasks, unreadable on LB; readable on dev-48 process endpoints | ~0.8 screen, then ~4-7 | only if EXP-028 T4 fires; L2 screen first (does the 40-call tree breach the 8-min cap on smoke-8?) |
| 5 | C-008 | Cap arm (7 / 9 min) from the measured mean | time profile vs ceiling | safety margin or more finishing time | ~4-7 | only after T1-T3 are known |
| 6 | C-004, C-005 | Paper section 4 from the accepted EXP-028 result | n/a | paper deliverable | 0 | Nov 5 draft |

## GPU budget this week

| Window | Spent (kernel wall, EXP §9) | Committed (running) | Remaining of 30 | Next arms costed |
|---|---|---|---|---|
| unknown (reset day unverified) | EXP-028 R + RH: not yet read from §9 | none running | unknown | item 4 or 5: one dev-48 arm 4-7 h; any new claim: smoke-8 screen ~0.8 h first |

Ask the user to read the sidebar quota counter once; record the figure, the reset day and whether L4x4 counts 1x in the harness-stack skill.

## Next upload slot

Oct 29 UTC slot is open and will likely lapse: #12 is chosen by items 1-3 (EXP-028 §4 rows 1-8 pick R or RH; EXP-027 §4 picks the cap). Do not spend the slot on an unread tree. If #11 is still pending when EXP-028 is read and T2 or T3 holds, #12 = the EXP-028-chosen tree at 8 min with the override written in S-012.

## Waiting on

- #11 grade (Kaggle ref 57750294, PENDING 21.5 h at 2026-10-29 20:14 UTC; longest grading seen).
- Download of `rainm4/gemma4-exp028-armr` and `-armrh` to `runs/EXP-028-armR/`, `runs/EXP-028-armRH/`.
- Critic backfill of migrated claims (start with EXP-024, EXP-025, EXP-027).
- User: prediction for #11 and approval shape for S-012.

## Not pursued

- LoRA adapters (C-013): the only same-model data is -10.8 points; no-go at the Oct 25 gate (EXP-022 §2.3).
- Sub-agents / same-model delegation (C-014): spends time, adds no capability; sync tool stall 78% (EXP-007).
- Best-of-N editing branches (C-015): no selection proxy without hidden tests; shared `/workspace`.
- Graph tools (C-012): lose to grep at every k.
- Further surgery on the 12.8 KB prompt (C-009, D-001 killed).
- Smoke-8 thinking x s/call calibration (EXP-024 §4 item 7): re-measures an owned quantity in the harmful direction.
- `pytest -k` from the 0.24 prompt (C-017): grading runs whole files.
- Context-reset trick from the paper-track forum post: unsourced 96% vs 16%; revisit only if a kaggle-scout note gives its method.
