---
id: EXP-031-critic
exp: EXP-031
tier: prereg
verdict: ready
verified: inspected
date: 2026-11-05
---

## Verdict
**ready.** EXP-031 may serve as the pre-registration for S-013: one more draw of the byte-identical v24-at-8 zip. This verdict is a review gate only. It does not authorise the upload: the user's yes and `approvals/S-013.txt` are still required.

## Checks
1. **Order and blindness: pass.**
   - EXP-031 has one commit, fdb0b95 (11:33:44 UTC). That is after #12's score was recorded at 2538bc6 (11:32:12 UTC), so #12 is used as the prior, which is legitimate.
   - The file has not changed since: `git diff fdb0b95 HEAD` is empty and the worktree is clean.
   - The §4 rows are blank, k <= 5, k = 6-14 and k >= 15. They are exhaustive, applied first match, and each names the next slot.
   - The prediction is written in §3 and in S-013: theta 21/116, about 10.5 tasks, sd 2.9.
2. **Zip sha: pass.** `sha256sum` gives `c22069db…7600` for both `out/submission.zip` and `experiments/EXP-027/v24_at8.zip`. This equals S-013's frontmatter and `submissions.md` rows 11 and 12.
3. **Gate override: pass.** It is stated in §2 and in the S-013 frontmatter as before:
   - 18.00 h nominal;
   - 10.04 h projected from the measured Arm R dev-48 mean plus the measured server start, not from the cap;
   - two completions on the hidden set (#11, #12).

   The cost of a blank is accepted explicitly: one slot, and the best-of LB keeps 0.18.
4. **Tension with EXP-029 row 3: disclosed, not blocking.**
   - Row 3 sends the next slot to "the next candidate of the adaptive tree". It gives no instruction for the case where no candidate exists.
   - No 31B candidate has passed a screen as of now:
     - EXP-030 died in its parameter cell;
     - EXP-040 stopped V1;
     - EXP-032 P1 is not a tree candidate.
   - The E4B (EXP-038, accepted) is outside this comparison under §4's last paragraph. It has no S-NNN, no §5.8 override and no predicted k, so it cannot take today's slot under the rules. My inference: EXP-031 §1's precedence clause does not bite.
5. **What changed since S-012: nothing that makes the draw unsafe.**
   - The 2026-11-05 grading-environment digest finds no wheelhouse or harness update since 2026-10-12, which is before #11 and #12.
   - The only new timeout report (756044) gives no config.
   - The two-phase "10 h for tasks" belief (748618, 10-12, [M]) predates both completions.
   - The risk is the same as at S-012: 10.04 h against about 10.5 h, with no margin.

## Required fixes (non-gating)
- Lead, S-013 "Why this slot": the clause saying EXP-030 "is only being pushed" is stale. Its kernel failed in the parameter cell and it is superseded.
- Submitter: before submitting, confirm with the read-only submissions list that no upload is already pending or scored today (UTC), since one slot per day is allowed.
