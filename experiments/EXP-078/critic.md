---
id: EXP-078-critic
exp: EXP-078
tier: light
verdict: accepted
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

## Light review 2026-11-12 (results, a2af572 and a2a865e)
### Verdict
Accepted. Row 2 is the first matching row, on H2: repeat share 21 of 129 = 0.163, above 0.16. It licenses the decision only: 0.2 is not kept as the single-loop base. It does not show that 0.2 raises repeats (0.2 draws 0.093 and 0.163; 1.0 draws 0.083 and 0.101). Eo 3 sits in the row 3 band and is recorded only.

### Audit
1. Pass. Readings 2b351a3 and critic-ready 2d42b07 precede the push (about 08:22 UTC). Since 49bbb69 only section 7, section 8, Status and section 9 change.
2. Pass. `summary.jsonl` ids equal dev-48; `diff -r` of the loaded tree against `experiments/EXP-075/candidate-t02` is empty; eval_config 240/28/8/80.
3. Pass. `analyze_traces.py` re-run to scratch: 0 field differences from the committed `summary.jsonl`. `desk.py`: repeats 21/129, and the references 13/156, 14/139, 14/150. `readings.py`: 0 infra rows, H7 26, H1 0. `pair4.py` gives section 9.5. Log end 5,954.97 s = 1.654 h. No instrument changed after 2b351a3.
8. Pass for the EXP file: section 9.8 claims only row 2. Not pass for the lead's post hoc lines (below).

### Question 1
The lead's reading is fair. "No further temperature draw is funded" is the lead's decision, consistent with section 9.8, not a reading of row 2. Section 7 item 1 applies "above 0.16" to the exact fraction, as written; rounding after the result would be a reinterpretation.

### Question 2: not fairly worded (lead's fix, `knowledge/plan.md` and `knowledge/lessons-e4b-loop.md`)
- "Halves empties" is the general statement section 5 bars.
- Of the 16 tasks empty in either 1.0 draw, the 0.2 draws placed F4 R2 C3 S2 plus 2 resolved (EXP-075), and F4 R4 C3 S3 (EXP-078). That is all four later stages, not R and S.
- fastapi_14873 and rich_3067, both empty in a base draw, resolved in EXP-075. "S 13" holds 4 resolved runs.
- Between the two 1.0 draws, 7 tasks left E and none resolved, with no temperature change.
- "Mechanics fixes move mechanics counts only" rests on one lever: mark it [I].

Suggested replacement: "Post hoc, four draws: empties 10 and 9 at 1.0, 5 and 3 at 0.2; resolves 5 and 3, 6 and 5. The tasks that left E spread over F, R, C and S; 2 resolved in EXP-075, 0 in EXP-078, and 0 of 7 between the 1.0 draws. Conversion is not readable on these counts."

## D-011 ranking 2026-11-12 (requested; my inference throughout)
- **GPU: none.**
  - A third 0.2 draw would at best keep a base with no resolve signal.
  - The motivation for the top_p arm, AL 1, did not recur (AL 4).
  - Pacing reads on wall only, and EXP-042 found no trace support for a check before submit.
  - On resolves against the two 1.0 draws (5 and 3), a keep needs about +4 per draw over two arm draws [I].
- **To the user, record-bound:**
  - The best single dev-48 run of any model or tree is 11 (EXP-074 defect 5).
  - EXP-028 arm R, the E4B tree's files with the 31B on the model line, reached 9. The E4B read 3 to 6, with a union of 7.
  - No tested or desk-checked E4B arm clears D-011's rule. EXP-078 adds that the one lever landing in its keep band moved no readable resolve. EXP-079 adds that search sits below the base spread.
  - So harness tuning of the E4B has no readable path to rule 1 on this record. That does not prove that no path exists.
- **Zero GPU** (none of these changes that answer):
  1. Arm R against the four draws with `pair.py`: a model swap at a fixed harness. Unresolved, arm R reads E6 F3 R6 C14 S10 with 9 resolved; the E4B draws read F 8 to 12.
  2. Change-level thought text on R, C and S runs, within the 16 tasks ever resolved. EXP-074 Q3 already covered F and R at file level.
  3. What the 7 share: it describes the easy set.
