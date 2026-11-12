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
- **P1.** Row 1 covers a blank run, a crash and a cancel. Rows 3 to 5 cover Eo 0 to 15, and H6 covers 16 or more. Splitting my "9 or more" this way is consistent: both end the line.
- **Thresholds.** These match the D-011 review: keep 4 or fewer, no decision 5 to 8, not replicated 9 or more, AL 1 or fewer. `power.py` regenerates all seven section 3 figures.
- **P2.** The predictions are stated blind, with Eo about 7 and row 4 likeliest.
- **P3.** `patch_empty` and `n_edit_arg_loss` exist and give 5 and 1 on EXP-075. `readings.py EXP-075-t02 --rerun EXP-077-base` runs and reports 0 net ids.
- **P4, P5.** Power is 0.43. The 1.3 GPU-h comes from the measured 1.340 and 1.292, not from the cap. 6.66 h is labelled as a bound, and the cancel point is push + 2.0 h.
- **P6.** The notebook diff is the `EXP_ID` line only, and the metadata differs in `id` and `title` only. The embedded zip decodes to `dca506d3...92a8`, and `TASK_IDS` equals dev-48.
- **Independence.** Shared ids are treated as independent (limit 1, my design, disclosed), so the tail figures are optimistic.

## H1 both-draw form: accepted
The net ids in `readings.py` are EXP-038's five resolves missed by the arm, minus EXP-077's two losses. That is exactly the set of three. H1 fires only if fastapi_14301 and fastapi_14463 are both lost, so it is close to inert. That is proportionate, since no row claims resolves. A threshold of 1 would fire on fastapi_14301 alone (lost in 2 of 9 single-loop runs).

## Pinned blind: 1 to 4 infrastructure rows
Eo, AL and H1 are counted over all 48 rows as written. A zero-turn row counts as empty, and nothing is subtracted afterwards. Its count and ids are reported beside the governing row. The experimenter may add this sentence to section 4 (optional).

## Wording fixes (2f91ea9)
EXP-075 section 9.9, EXP-077 section 9.8 and both README cells carry my text verbatim, and D-011 cites it (line 92). Two problems remain in `knowledge/plan.md` line 225, both for the lead and neither blocking:
- It still says temperature is "closed as a lever on M" and does not cite the scope note.
- "Only number outside both base draws" is false: resolves 6 and first edit 37 are also outside.

## EXP-079 no-build
The counts reproduce (`desk.py`, `ceiling.py`), and the recipe-alone +2 is below every reference, so the no-build stands. The fixed-15 upper bound of +4.0 ties the gap. The recipe does not ask for that bound.
