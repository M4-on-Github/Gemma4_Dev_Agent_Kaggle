---
id: D-010
title: E4B pipeline, five adaptive tweak rounds (11-11)
decision: start
status: active on the user's word (2026-11-11, "gi for 5 more harness trweaks for e4b agents", f3df1e5). The critic's `direction` review is pending; it does not block round 1.
track: main
claims: [C-015, C-019, C-021, C-023]
date: 2026-11-11
---

## What are we trying to do?
Five more single-variable changes to the E4B pipeline agents (root, reader, drafters, applier). Each is screened on smoke-8, and each is chosen after the last reading. The aim is a tree with more resolves on the hidden set. Edit reliability is one route to that, but no longer the only one.

## How is it done today?
- **Tree:** EXP-064 `candidate-loc`, scored 0.01 on the leaderboard as S-016. The same shape scored 0.05 as S-014 and S-015. The 31B single loop's best is 0.18 (S-012).
- **D-009 ended by its two-rounds rule:**
  - EXP-068 had drafters read their own lines. Its row 6 moved the failure to line drift.
  - EXP-069 had the applier use bare paths. It read row 3, not exercised: no quoted path occurred.
- **Unresolved classes on EXP-053** (24 unresolved): right file, wrong fix 12; wrong file 8; edit failure 4.
- **Smoke-8 resolves** are 1 to 2 of 8 per run and are recorded only. n = 8 cannot read a resolve effect. Every round is read on a process endpoint.

## What's new in our approach?
- **The rounds are adaptive and ranked by desk-checked evidence.** Round 1 runs now; rounds 2 to 5 are ranked after EXP-070, the experimenter's zero-GPU desk check.
- **Round 1, EXP-071: the anchor form** (screener, dispatched 2026-11-11).
  - The reader's LINES must come from a numbered output it ran, such as `grep -n` or `nl -ba`, not from counting by eye.
  - Evidence (EXP-068 §10): the 3 window misses are in the right file, 7 to 15 lines off. The same 5 to 9 line drift shows on 3 of 12 tasks in the REGION trees. On rich_3468 the reader's own `grep -n` printed the right line and it was not used.
  - Base: EXP-068 `candidate-read`.
- **Candidates for rounds 2 to 5** (EXP-070 measures the numbers each one needs first):
  - **Executed verify step in the applier (C-019):** run the edited module's test file after the last applied edit; if the run shows new failures, revert and try the next draft. This targets the largest class, right file wrong fix. Endpoint: verify executed on N of 8.
  - **Reader empty-report guard:** the reader's final report must open with FILE. One case is known (requests_7309, EXP-068); EXP-070 counts the rate.
  - **Draft diversity or selection (explore quota):** if the 5 drafts are mostly identical, give each drafter a distinct strategy or temperature. If they differ, give the applier a selection rule. This draws on C-015 and C-023, not the public frontier's design.
  - **Vendoring the two test-only packages (C-021):** only if a zero-GPU re-grade of the pipeline's patches flips any task. The E4B single loop flipped 0 of 15.
  - **Wider drafter window (±20):** held back as the anchor form's fallback.
- **Round 5 is chosen by rounds 1 to 4.** If any form is kept, round 5 is the fused tree of the keepers on smoke-8, as an upload candidate for the user. Otherwise it is the next ranked candidate.

## Options
- **A: the five rounds as above.** About 2.0 GPU-h.
  - Strongest argument against: this carrier draws 0.01 to 0.05 against the 31B's 0.18, and n = 8 screens read only process endpoints. A kept form moves the leaderboard only if it moves at least 4 tasks of 58.
- **B: spend the five on the 31B single loop.** Not chosen: the user named E4B agents.
- **Lead's recommendation:** A, on the user's word. Each round is read on a mechanism endpoint, so a kept form has a stated reason to ship.
- **Critic's dissent:** pending.

## Expected score impact
- 0 to 2 tasks of 58 for the batch, P about 0.25 [I].
- Only through an E4B upload on the user's word.
- Below the 4-task MDE: a leaderboard draw cannot read it.

## Risks and kill criteria
- **A round's harm row binds:** its form is dropped.
- **Three rounds in a row not exercised:** stop and put the cohort question to the user. Rare classes miss at n = 8 (EXP-069).
- **Spend reaches the 2.5 GPU-h ceiling:** stop.
- No dev-48, upload or re-run without the user's word.

## Cost
Five smoke-8 runs at about 0.35 to 0.40 each, so about 2.0 GPU-h, with a ceiling of 2.5. No upload slots.

## Midterm check
After rounds 1 and 2: at least one is exercised and reads no harm. Otherwise the remaining rounds go to the candidates with the highest opportunity counts in EXP-070.

## Final check
- Either a fused tree whose smoke-8 shows no harm and at least one kept mechanism, offered to the user as an upload candidate with its sha;
- or a written finding of which forms the E4B did not take up.
