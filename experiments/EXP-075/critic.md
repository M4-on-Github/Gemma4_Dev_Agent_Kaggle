---
id: EXP-075-critic
exp: EXP-075
tier: prereg
verdict: needs-work
verified: regenerated
date: 2026-11-12
---

## Verdict
Built as stated. It can be pushed after a text-only amendment; no rebuild is needed. Four readings would misread a null draw (fixes 1-4). M is an acceptable mechanism primary given the amended guards. Its 0.07 SD comes from a within-run bootstrap, not from a measured rerun.

## Audit
- **P6, P2, P5: pass.**
  - Tree and zip: one hunk.
  - Notebook: differs in `EXP_ID` only.
  - Metadata: differs in id and title only.
  - 1.267 h is measured and 6.66 h is labelled a bound.
- **P3: pass (regenerated).** EXP-038 gives 53/156 notfound, 83 failed, 13 repeats, and first edit applied on 28/47. The bootstrap SD is 0.052. H3's reference holds only on `EXP-075-base038`.
- **P1, P4: fail.**
  - The same-id reruns cover 16 ids and read 18/41, against EXP-038's 23/59 on those ids.
  - The unselected smoke-8 went from 1/20 to 7/17, so the SD is unconfirmed [I].
  - The keep threshold at 0.20 is about 1.9 SD. That is enough for a reversible switch of the base, not for a ledger claim.

## Required fixes
1. **H1 governs before the mechanism rows.**
   - `requests_6644` cannot be lost.
   - `fastapi_14463` and `rich_3905` have one E4B draw each.
   - On other single-loop runs, `fastapi_14301` held 7/9 and `rich_3006` 8/9.
   - Use 3 or more lost, or losses net of a base rerun.
2. **Row 1:** a complete file from a dead server would fire H6 as model harm. Port EXP-038 row 0's non-cap `error` clause and its cancel rule, with a cancel time.
3. **Row 6:** bracket the condition as M ≤ 0.20 and (failed > 0.532 or A < 28 or Eo 11-15). As written, A < 28 alone, the base's point value, fires it ahead of row 7.
4. **Row 3:** 0.30 is about 0.5 SD below the base, and a keep-sized fall is not excluded there. Use 0.33, or reword the reading so it does not close the lever.
5. **Loops outside `edit_file`:** the all-tool `n_identical_repeats` is 25 on EXP-038, and reached 27 on 8 tasks in EXP-068 and in EXP-071. Add a clause with a stated threshold.

Not blocking:
- Wrong-file harm is in no row. Reruns show F entered on 3 of 15 tasks, so net F is unreadable against one draw; state this as a limit.
- Record M over non-repeat calls.

## Slot 2 (direction, not blocking)
**Recommend (a)**, as its own pre-registered file that reuses the EXP-038 zip (`9de869bd...`).
- It measures the draw spread of M, Eo, F and resolve holds that every later arm needs.
- Fix 1's net form and the SD behind rows 3-5 depend on it. Write both files' readings before either result lands.
- (b): its ceiling sits inside the net-F noise this run measures.
- (c): premature before any dose effect is seen.
- (d): none cheaper that I can name [I].
