---
id: EXP-075-critic
exp: EXP-075
tier: light
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
   - On single-loop variant runs, `fastapi_14301` held 7/9 and `rich_3006` 8/9.
   - Use 3 or more lost, or losses net of a base rerun.
2. **Row 1:** a complete file from a dead server would fire H6 as model harm. Port EXP-038 row 0's non-cap `error` clause and its cancel rule, with a cancel time.
3. **Row 6:** bracket the condition as M ≤ 0.20 and (failed > 0.532 or A < 28 or Eo 11-15). As written, A < 28 alone, the base's point value, fires it ahead of row 7.
4. **Row 3:** 0.30 is about 0.5 SD below the base, where a keep-sized fall is not excluded. Use 0.33 and widen row 7 to match, or reword the reading so it does not close the lever.
5. **Loops outside `edit_file`:** the all-tool `n_identical_repeats` is 25 on EXP-038 and reached 27 on 8 tasks on the pipeline trees EXP-068 and EXP-071. Add a clause with a stated threshold.

Not blocking:
- Wrong-file harm is in no row. Reruns show F entered on 3 of 15 non-F tasks, so net F is unreadable against one draw; state this as a limit.

## Slot 2 (direction, not blocking)
**Recommend (a)**, as its own pre-registered file that reuses the EXP-038 zip (`9de869bd...`).
- It measures the draw spread of M, Eo, F and resolve holds that every later arm needs.
- Fix 1's net form and the SD behind rows 3-5 depend on it. Write both files' readings before either result lands.
- (b): its ceiling sits inside the net-F noise this run measures.
- (c): premature before any dose effect is seen.
- (d): none cheaper that I can name [I].

## Light review 2026-11-12 (results, 419e8b3 and 940a1aa)
Supersedes the prereg verdict above.

### Verdict
needs-work: a scope note. Row 3 (kill) was the first matching row, applied as written; its decision stands: no further sampling arm is funded as the M lever. Its blind text and §5 outrun one draw, and the record now says three things: README "dead", plan "closed as a lever on M", D-011 "not closed". Wording to carry: "At temperature 0.2, one dev-48 draw shows no keep-sized fall in the notfound share. M 0.380 (57/150) lies between the base draws (0.340, 0.439) and 0.238 (2.4s) above the M-falls bound 0.142. Not tested: smaller falls, other temperatures, top_p and top_k, endpoints other than M." A light verdict moves no claim.

### Audit
1. **Order: finding, immaterial.** 414fd31 changed text above the line at 05:54 UTC, 4 min after the push and before any result; disclosed in §7. Row 3 reads M only; H1 fires under neither boundary (gross 1 lost). Pushed without a re-review of the needs-work above; fixes 1 to 5 did land (4ec19e5).
2. **Cohort and arms: pass.** Dev-48 ids; loaded tree equals `candidate-t02` (diff -r); sampling 0.2.
3. **Numbers: pass, regenerated.** `analyze_traces.py` 0 field differences; `readings.py` reproduces s, the losses and 0 infrastructure errors; row 2 does not fire.
8. **Scope: pass on the letter, finding on reach.** The README cell and §9.8 repeat row 3 and §5 as written; my fix 4 offered 0.33 in place of rewording, so those texts stood with my assent. §7 item 3: a kill inside the base spread is what a null looks like.

### Empties (Eo 5)
Eo is the pre-registered outcome endpoint beside M; 5 falls inside row 5's band (3 to 10), which also needed M to fall, so it fires nothing. §1.3 states P(at most 5) = 0.039 under 0.214, but no row reads Eo on that null; the comparison with 10 and 9 is post hoc (A 37/48, failed share 0.447 and resolves 6 are outside both too). Paired E flips: 8 left, 3 entered against EXP-038 (McNemar p 0.23); 7 and 3 against EXP-077 (p 0.34) [I]. A hypothesis for a pre-registered replicate; no document should say 0.2 lowers empties.

### Required fixes
1. Append a dated scope note with the wording above below §9.8, and add it beside the applied reading in the README cell; the applied reading is not revised.
2. Plan line and D-011: cite that note.
