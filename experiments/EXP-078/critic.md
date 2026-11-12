---
id: EXP-078-critic
exp: EXP-078
tier: prereg
verdict: ready
verified: regenerated
date: 2026-11-12
---

## Verdict
Ready to push (2b351a3, 49bbb69). No text fix is required.

## Checks
- **P1.** Row 1 covers blank, crash and cancel; rows 3 to 5 cover Eo 0 to 15, H6 16 or more. Splitting my "9 or more" this way is consistent: both end the line.
- **Thresholds.** These match the D-011 review: keep 4 or fewer, no decision 5 to 8, not replicated 9 or more, AL 1 or fewer. `power.py` regenerates every section 3 figure.
- **P2.** The predictions are stated blind, with Eo about 7 and row 4 likeliest.
- **P3.** `patch_empty` and `n_edit_arg_loss` exist and give 5 and 1 on EXP-075. `readings.py EXP-075-t02 --rerun EXP-077-base` runs and reports 0 net ids.
- **P4, P5.** Power is 0.43. The 1.3 GPU-h comes from the measured 1.340 and 1.292, not from the cap; 6.66 h is labelled a bound; cancel at push + 2.0 h.
- **P6.** The notebook differs in `EXP_ID` only and the metadata in `id` and `title` only. The embedded zip decodes to `dca506d3...92a8`; `TASK_IDS` equals dev-48.
- **Independence.** Shared ids are treated as independent (limit 1, my design, disclosed), so the tail figures are optimistic.

## H1 both-draw form: accepted
`readings.py` net ids (EXP-038's five resolves missed, less EXP-077's two losses) are exactly the set of three. H1 fires only if both fastapi ids are lost, so it is close to inert, which is proportionate since no row claims resolves. A threshold of 1 would fire on fastapi_14301 alone (lost in 2 of 9 single-loop runs).

## Pinned blind: 1 to 4 infrastructure rows
Eo, AL and H1 are counted over all 48 rows as written, and nothing is subtracted afterwards. Each such row is counted by its recorded `patch_empty`; the analyzer sets it from zero patch characters, so a zero-turn row should read empty [I; no zero-turn row exists in any local run]. Their count and ids are reported beside the governing row.

## Wording fixes (2f91ea9)
Landed verbatim in EXP-075 section 9.9, EXP-077 section 9.8 and both README cells; D-011 cites it (line 92). Outstanding in `knowledge/plan.md` line 225, for the lead, not blocking:
- It still says temperature is "closed as a lever on M" and does not cite the scope note.
- "Only number outside both base draws" is false: resolves 6 and first edit 37 are also outside.

## EXP-079 no-build
The counts reproduce (`desk.py`, `ceiling.py`), and the recipe-alone +2 is below every reference, so the no-build stands. The fixed-15 upper bound of +4.0 ties the gap. The recipe does not ask for that bound.
