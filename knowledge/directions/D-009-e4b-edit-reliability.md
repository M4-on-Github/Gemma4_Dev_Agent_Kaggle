---
id: D-009
title: E4B pipeline edit reliability, one stage defect per round
decision: pivot
status: done, ended 2026-11-11 by its two-rounds rule (EXP-068 row 6 kept nothing; EXP-069 row 3, not exercised, kept nothing); successor D-010. Was active (approved 2026-11-10: the user chose option A, round 2 on the E4B, over option B, answering "1."; knowledge/user-decisions.md, 4db058b). Revised 2026-11-10 after the critic's `direction` review (needs-work; experiments/EXP-067/critic.md, d372a76, 53be9fb). The pivot is on the user's word "tweak the agents" (2026-11-10).
track: main
claims: []
date: 2026-11-10
---

## Revision 2026-11-10 after the critic (read first)
All four required fixes are accepted.
1. **The accounting covers all 5 runs** (EXP-061, 062, 063, 064, 066; 62 failed edits over 40 task-runs). This is the critic's text-match count, not a chain diff:

   | Class | Failed edits | Task-runs | Empties caused |
   |---|---|---|---|
   | A + S, the applier's argument form (argument loss, quote-wrapped `filepath`) | 22 | 9 | 3 |
   | Reader stage (R1) | 17 to 18 | 3 | 2, both rich_3468 |
   | E, a stale old_string | 12 | 4 | 0 |
   | M, an ambiguous match | 9 | 2 | 0 |

   The rounds are ordered by empties caused. **S is round 2 unconditionally**: it already recurred on the EXP-064 tree (4 in EXP-066). EXP-068, the reader-stage form, was pushed before this review and stays round 1.
2. **The midterm is restated** on content-class first-edit failures (reference 2 of 40) and on drafter copy mismatches, with EXP-068's thresholds. "R1 = 0" holds by construction once REGION is gone, and first-edit ≥ 7 of 8 passes by noise about a quarter of the time (critic's estimate).
3. **A not-exercised EXP-068 ends only that form** (a drafter that chooses to call `read_file`), not the direction. That is EXP-068's own §5.
4. **What a success feeds:** only an E4B package upload, which so far draws 0.05 and 0.01 against the 31B's 0.18.
   - Little ports to the 31B: S does not occur there (0 quoted paths in 284 edits); the reader class has no counterpart in a single loop; and A occurs there, but its one prompt mitigation is refuted (C-005).
   - So D-009 is a process direction for the E4B carrier. Option B below is restated on time-neutral terms.

## What are we trying to do?
Make the E4B pipeline's edits land on the file. Over 40 task-runs of five pipeline runs, 62 `edit_file` calls failed, and 5 task-runs ended empty because every edit failed.

## How is it done today?
- **The tree:** a reader, then five tool-less drafters, then an applier. The reader copies a REGION, the drafters copy OLD from it, and the applier pastes OLD.
- **The harness matcher** already forgives whitespace, indentation, regex-level drift and JSON escaping (edit.py:401-454).
- **Where failures come from:** EXP-067's chain diff on three runs found drafter drift and paste drift at 0. The classes are in the table above.
- **First-edit-applies:** 17 of 24 task-runs in EXP-067.
- **Applier wording against resends** was tried and did not work (EXP-053).

## What's new in our approach?
- Each round removes one copy hop or one argument-form defect.
  - **Round 1 is EXP-068** (pushed; RUNNING). Each drafter reads its own FILE and LINES and copies OLD from that read, and the reader gives no REGION.
  - **Round 2 is S**, the quote-wrapped `filepath`. Its form is to be designed so it does not rest on wording alone (the EXP-053 lesson). A desk check comes first: where the quotes enter, whether it is a drafter FILE line or the applier's own argument.
- Each round carries a first-turn tool-call row (the EXP-063 lesson).

## Options
- **A: D-009 as revised.** Two smoke-8 rounds, about 0.7 GPU-h.
  - Strongest argument against: a success feeds only the E4B carrier, whose LB draws are 0.05 and 0.01. The edit-failure class was 4 of 24 unresolved runs in EXP-053, behind "right file, wrong fix" (12) and "wrong file" (8). The LB gain may be zero.
- **B: the 31B single loop.** Our best is 0.18 (S-012).
  - Time-neutral prompt changes cost no wall time there. The room to the 11 h gate is 28.8 s per task at the measured mean, and 13.8 s to our own 10.5 h ceiling.
  - The 31B's edit defect is A: 58 of 175 calls lost (C-004). Its one prompt fix failed (C-005), so a new form would need a mechanism, not wording.
  - This is the only carrier that has competed on the LB.
- **C: hold development and keep the current best for the final pair.** Fairly dismissed: it learns nothing.
- **Lead's recommendation:**
  - Finish EXP-068, already spent. Then put the question to the user: round 2 (S) on the E4B, or B.
  - On LB value alone, B ranks higher. A's case rests on the user's "tweak the agents" and on cheap smoke-8 reads.
- **Critic's dissent (needs-work, 2026-11-10, verbatim):** "Round 1 targets the cause of only 2 of the 5 edit-failure empties, and both are rich_3468, which has never resolved in 13 E4B runs. The applier's quote-wrapped filepath (S), together with argument loss (A), caused the other 3 empties on three tasks. The same pair caused 8 of the 12 first-edit misses over 40 task-runs, and S already recurred on the EXP-064 tree (EXP-066). The midterm's first-edit ≥7 of 8 passes about a quarter of the time on noise alone. R1 = 0 holds by construction once REGION is gone. The final check is out of reach without an argument-form fix. Little of this ports to the 31B tree, the only carrier that competes on the LB: S does not occur there (0 quoted paths in 284 edits), the reader class has no counterpart in a single loop, and A does occur there but its one prompt mitigation is refuted (C-005). D-009 must therefore say what a success feeds. Make S round 2 unconditionally, restate the midterm on content-class failures and drafter copy mismatches, and let a not-exercised EXP-068 end only this form."
  - **Lead's response:** accepted in full (Revision above).

## Expected score impact
- 0 to 1 task of 58 for the whole direction, P about 0.2 [I], and only through an E4B package upload.
- Round 1 alone touches the causes of 2 of the 5 edit-failure empties, both on one task that has never resolved.
- All of it is under the 4-task MDE, so no LB draw can read it.

## Risks and kill criteria
- **EXP-068 not exercised** (at most 20 of 40 drafter turns open with `read_file`): this form ends, the direction does not, and round 2 goes ahead.
- **EXP-068 harm (its row 3 binds):** fabricated OLD on 8 or more of 40 drafter turns, 3 or more empties, a cap hit, mean wall over 150 s, a tool_free task, or a drafter text-form call. The form is dropped.
- **Two rounds in a row with nothing kept:** the direction ends.
- No upload slot or dev-48 without the user's word.

## Cost
About 0.35 GPU-h per round, so about 0.7 for two. No upload slots.

## Midterm check
- **After EXP-068:** content-class first-edit failures not above the reference 2 of 40 (scaled to 8: 0 to 1), drafter copy mismatches (OLD not in the drafter's own read) of 2 or fewer, and no gate row.
- **After round 2:** fewer A+S first-edit misses than the reference (8 of 12 misses over 40, about 1.6 per 8).

## Final check
- A tree with no edit-failure empty patch on two smoke-8 runs and first-edit-applies of at least 7 of 8 on both. It goes forward only in a package, on the user's word.
- Otherwise, a written finding of which copy and argument defects the E4B cannot be prompted out of.

## Midterm after EXP-068 applied, 2026-11-10
- **EXP-068 read row 6, no decision** (9fb6996, b231ee6; 0.38 GPU-h). On requests_7309, drafter_5 wrote a bare `read_file(...)` line as its final text. Under the wider reading of row 3 that is a drafter text-form call and harm binds; under section 3's fence-only definition it is not. The action is the same either way: the form is not carried forward.
- **Midterm criteria:**
  - Content-class first-edit failures 0 of 8 (limit 0 to 1): pass.
  - Drafter copy mismatches 16 of 35 (limit 2 or fewer): **fail**. 14 of them come from a reader LINES window that misses the CHANGE target on 3 of 8 tasks.
  - Gate rows: none on the literal definitions; row 3 is ambiguous as above.
- **Round 1 keeps nothing.** The rule "two rounds in a row with nothing kept ends the direction" therefore binds on EXP-069. If round 2 keeps nothing, D-009 ends, and the lead puts the window-anchor form (a string anchor, or an applier-side read with line prefixes) to the user as a new proposal, not as a round 3.
- Both first-edit misses in EXP-068 are form-class: A on fastapi_14605 and S on rich_3468. That is one more S event, which supports round 2's target.

## Ended 2026-11-11: two rounds in a row with nothing kept
- **Round 1, EXP-068:** row 6. Round 2, EXP-069: row 3, not exercised (Q = 0 quoted filepaths in 23 edits; 17e0804).
- **The finding the final check asks for:**
  - Of the copy defects, the reader's REGION mis-copy goes away when drafters read the file themselves. In its place comes line-number drift: the reader counts lines by eye, and `read_file` shows none. The drift is 7 to 15 lines on 3 of 8 tasks in EXP-068, and 5 to 9 lines on 3 of 12 in the REGION trees (EXP-068 §10).
  - Of the argument defects, S is about 1 in 5 task-runs. It did not occur on this cohort draw, so its form is untested rather than failed.
  - The E4B's edit failures on EXP-069 were all content-class.
- **What carries forward:**
  - the anchor form, LINES from a numbered output, as a D-010 candidate;
  - EXP-069's applier hunk, only as a free rider with no harm seen.
