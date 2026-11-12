---
id: D-011
title: E4B research loop, diagnose the reasoning failures and fix them in the harness (11-11)
decision: start
status: active on the user's word (2026-11-11, knowledge/user-decisions.md, 85f31c3). Supersedes D-010's five-round frame and its 2.5 GPU-h ceiling; EXP-071, EXP-072 and EXP-073, built under D-010, are read as this loop's first rounds. The critic's `direction` review runs once EXP-074's ranking is in, before the first round above 1 GPU-h.
track: main
claims: [C-015, C-019, C-021, C-023]
date: 2026-11-11
---

## What are we trying to do?
- Find where the E4B's reasoning leaves the gold fix, then change the submission (its tree, prompts, sampling and `eval_config.yaml`) so that it leaves less often.
- Stop on the user's rule (below): either a config that could best the LB, or the GPU runs out.

## How is it done today?
- **E4B:**
  - single loop: 5/48 on dev-48 (EXP-038); 0.05 on the LB (S-014);
  - pipeline trees: 0.05 (S-015) and 0.01 (S-016) on the LB, 1 to 2 of 8 on smoke-8.
  - The LB top is 0.29 (17/58) on 2026-11-11, and four or more teams sit at 0.24. Our best is the 31B at 0.18 (S-012, 9/48 on dev-48).
- **Where the misses are:**
  - EXP-053 has 24 unresolved: 12 right file wrong fix, 8 wrong file, 4 edit failures.
  - 21 of 23 unresolved patched task-runs grade like an empty patch (EXP-070/critic.md).
  - The same two tasks (fastapi_14301, rich_3006) resolve whatever the tweak.
  - Rounds D-007 to D-010 aimed at the edit-failure 4 of 24.
- **Time:** E4B mean task wall is 85.7 s (EXP-038), against the 31B's 297 s. The E4B has about 3x the time headroom under the 4.5-min cap.

## What's new in our approach?
- **Diagnosis first, at zero GPU: EXP-074 (experimenter).**
  - For every local E4B task-run, it finds the first stage where the patch leaves gold: empty, file, region, the semantics of the change, or completeness. Classes are counted per task-run and per distinct task. The dev-48 sample is weighted, because smoke-8 repeats about 6 distinct unresolved tasks.
  - In pipeline trees it asks whether any of the five drafts overlaps gold when the applied patch does not. That decides whether selection is the lever, or comprehension and generation.
  - It reads the thought text if the traces keep it (thinking_budget 4096), and compares the carriers: the single loop against the pipeline.
- **Rounds are ranked from EXP-074's opportunity counts,** not from the edit-failure history. Each one climbs the screening ladder:
  1. desk check;
  2. smoke-8 (about 0.4 GPU-h), read on a process endpoint tied to the diagnosed stage;
  3. dev-48 (E4B about 1.5 to 2.5 GPU-h wall-scaled [I]) for a form that passes its screen, or for a fused tree of the keepers.
- **The carrier is open.** If EXP-074 shows the single loop is no worse on the shared ids, rounds may use the EXP-033 single-loop tree as base. Its time headroom suits test-time scaling (more exploration, a self-check run).

## Options
- **A: the loop as above.**
  - Strongest argument against: the E4B must go from 5/48 to 16/48, and nothing in the record has moved an E4B resolve count. If the diagnosis's reachable headroom falls short of +11, the loop will end on GPU, not on the LB rule.
- **B: the same loop on the 31B.** Not chosen: the user named the E4B.
- **Lead's recommendation:** A, on the user's word. Whatever EXP-074's headroom number is, it is reported to the user while the loop continues.

## Expected score impact
- To reach stopping rule 1, P is about 0.05 [I].
- A kept form that moves the E4B dev-48 by 3 or more tasks has P about 0.3 [I]. That stays below the LB MDE of 4 of 58 unless it is fused with others.

## Risks and kill criteria
- **Stop 1:** a dev-48 of 16/48 or more, with a projected worst case of 11 h or less. The candidate goes to the user; an upload happens only on the user's word and `approvals/S-NNN.txt`. A dev-48 of 12 to 15 of 48 is reported to the user, and the loop continues.
- **Stop 2:** any one of these:
  - Kaggle refuses a push for quota;
  - the ledger reaches 30 GPU-h for the week counted from 11-08;
  - a kernel stays QUEUED for more than 6 h (the lead asks the user).
- **A round's harm row binds:** its form is dropped.
- **Three rounds in a row not exercised:** the cohort question goes to the user.
- At most 2 kernels live at once.

## Cost
- Smoke-8 about 0.4 GPU-h each; a dev-48 E4B arm about 2 GPU-h [I].
- The quota left this week is unknown. The ledger shows about 6.8 measured since 11-08.

## Midterm check
- After EXP-074 and the first two rounds it ranks: at least one round is exercised on its diagnosed stage, and its stage count moves in the predicted direction.
- Otherwise the remaining budget goes to the next-ranked stage.

## Final check
- A dev-48 count against the 5/48 reference, on a tree whose every change carries a diagnosed stage.
- Otherwise, a written finding on which reasoning stages the E4B could not be moved on through the harness.
