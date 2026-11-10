---
id: D-009-critic
exp: D-009
tier: direction
verdict: needs-work
verified: regenerated
date: 2026-11-10
---

# D-009 direction review (not a review of EXP-067)

This review is filed here only because the critic's write guard allows no other path and the dispatch named this file. A later review of EXP-067 must not treat it as a prior EXP-067 review.

## Verdict: needs-work

D-009 is cheap, and EXP-068 is a fair probe. But the round order, the midterm and the final check rest on 3 of the 5 runs on disk. Over all 5, the applier's argument form causes more empty patches than the reader does.

## Dissent (quotable)

Round 1 targets the cause of only 2 of the 5 edit-failure empties, and both are rich_3468, which has never resolved in 13 E4B runs. The applier's quote-wrapped filepath (S), together with argument loss (A), caused the other 3 empties on three tasks. The same pair caused 8 of the 12 first-edit misses over 40 task-runs, and S already recurred on the EXP-064 tree (EXP-066). The midterm's first-edit ≥7 of 8 passes about a quarter of the time on noise alone. R1 = 0 holds by construction once REGION is gone. The final check is out of reach without an argument-form fix. Little of this ports to the 31B tree, the only carrier that competes on the LB: S does not occur there (0 quoted paths in 284 edits), the reader class has no counterpart in a single loop, and A does occur there but its one prompt mitigation is refuted (C-005). D-009 must therefore say what a success feeds. Make S round 2 unconditionally, restate the midterm on content-class failures and drafter copy mismatches, and let a not-exercised EXP-068 end only this form.

## 1. Class accounting

D-009 transcribes EXP-067 §9 correctly. But it adds EXP-066's 4 S and omits the rest of EXP-066 and all 16 of EXP-063's failures. The table covers all 5 runs: 62 failed edits over 40 task-runs. [I: I reclassified EXP-063 and EXP-066 with a substring test, not a chain diff.]

| class | failed edits | task-runs | empties caused |
|---|---|---|---|
| A + S (applier argument form) | 22 | 9 | 3 (requests_7309 in EXP-061, fastapi_14301 in EXP-063, fastapi_14448 in EXP-066) |
| reader stage (R1, R2-like) | 17-18 | 3 (rich_3468 ×2, fastapi_14605) | 2 (rich_3468 in EXP-063 and EXP-064) |
| E (stale) | 12 | 4 | 0 |
| M (ambiguous) | 9 | 2 (both fastapi_14605) | 0 |

- **First-edit misses.** There are 12 over the 40 task-runs: A 6, S 2, reader content 2 (both rich_3468), and no edit call 2.
- **Round-2 condition already met.** D-009 holds S until it recurs on the EXP-064 tree. EXP-066 is that tree with two reader lines changed, and it has 4 S. In every S task-run the quoted path appears in no upstream text, so the applier generates it.
- **R1 on the current tree** is 0 in EXP-066.

## 2. Kill criteria at n = 8

All are measurable and fixed in advance. The problems:

- **The not-exercised kill is too broad.** D-009 says a not-exercised EXP-068 ends the direction. But the reader calls tools on 8 of 8, and an S or A round needs no new tool step. EXP-068 §5 itself says its row 2 kills nothing.
- **The fabricated-OLD harm threshold conflicts.** D-009 says ≥3 tasks; EXP-068 row 3 says ≥8 of 40 drafter turns. EXP-068's threshold binds.
- **The midterm R1 = 0 is vacuous.** By EXP-067's definition, R1 is 0 by construction once REGION is gone, and EXP-068 uses R1-type ≤2 instead. At the base rate of 28 of 40, first-edit ≥7 of 8 passes about 0.26 by noise, and about 0.37 if every reader-content miss vanished. [I: roughly binomial; the tasks are not exchangeable.]
- **The final check is out of reach.** It passes about 0.065 at base and 0.135 with a perfect reader fix [I]. Only with A and S fixed too does it reach about 0.9.

## 3. "0 to 1 task, P about 0.2"

The size is honest, and D-009 states it is below the MDE. But two things are missing.

- The P is for the whole direction, while round 1's class accounts only for the 2 rich_3468 empties.
- No carrier is named. The E4B's LB draws are 0.05 and 0.01, against the 31B's 0.18, and the paper is dropped. D-009 needs one sentence on what a success feeds, and on which tree.

## 4. Options B and C

- **B is under-argued, not wrong.**
  - The 13.8 s figure is a measured mean plus overhead (D-004 B2). But it is measured to our own 10.5 h ceiling, and there are 28.8 s of room to the 11 h gate.
  - Prompt-only edit work is time-neutral, so the time argument and the failed parallel shapes (EXP-049, EXP-032) do not bear on it.
  - The 31B's edit defect is A: v24 lost 58 of 175 calls (C-004), and C-005 is refuted. Its quoted paths are 0 in 175 edits in EXP-028 Arm R and 0 in 109 in Arm RH. B's edit case is thin too.
- **C is fairly dismissed.** A round costs 0.35 GPU-h, and the final is Dec 2.

## 5. EXP-068: nothing to stop (pushed at 41a1394)

Six points to settle in the analysis:

1. **Failed reads escape A(d).** A drafter whose read fails (path form, range or truncation) has still made a call, so an OLD written after it escapes A(d). The drafter prompts give no failed-read rule, and the drafters now write 40 filepath arguments, so S can appear at this stage too. Count "OLD after a failed or empty read" separately, and count drafter read errors by kind.
2. **Settle the row 3 "stray path" now.** Decide whether a quote-wrapped drafter path is harm or a recorded failure, and write that down before the output is pulled.
3. **Compare compaction to a baseline.** On the base tree applier_first was already 14,383 on rich_3468 (EXP-064), and applier_max was ≥14,336 on 6 of 16 task-runs (EXP-064: fastapi_14605, httpx_3672, rich_3468; EXP-066: fastapi_14448, fastapi_14605, rich_3468). The applier's branch is None, so it now sees all five reads [I, `contents.py:748`], and the blind wall prediction assumes the old applier input. Report applier_first and compactions per task against these numbers. Issue 7324 at the parallel stage stays low (drafter prompts peaked at 2,662, reader_last at 10,775).
4. **The drafter now picks the locus.** LINES is now the reader's read window, not a change region of at most 25 lines. Name G and G1 on fastapi_14301 and rich_3006.
5. **Widen row 1.** It should also name a summarizer ValueError and a blank or crashed run.
6. **One owner for EXP-068.** EXP-068 says it serves D-008, and D-009 claims it as round 1. Reconcile the two.

## Required fixes to D-009 (no GPU)

1. Use the 5-run accounting (§1) and order the rounds by empties caused, or at least make S round 2 unconditionally.
2. Restate the midterm on content-class first-edit failures (reference 2 of 40) and drafter copy mismatches, citing EXP-068's thresholds.
3. Narrow the not-exercised kill to this form.
4. Add the carrier sentence (§3), and restate B in time-neutral terms (§4).
