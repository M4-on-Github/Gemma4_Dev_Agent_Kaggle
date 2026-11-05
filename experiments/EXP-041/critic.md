---
id: EXP-041-critic
exp: EXP-041
tier: light
verdict: needs-work
verified: regenerated
date: 2026-11-05
---

## Verdict
**needs-work, for hygiene only.** Row 3 (no single mechanism: d on 1 target, c on 2, a and b both on rich_3067) is applied as written, and every number regenerates. Two passages in §9.1 carry trace and patch content (plan.md:52) and must be removed; no reading changes. The lead's EXP-041 line in `knowledge/plan.md` and the C-020 note stand.

## Audit
1. **Order and blindness: pass.** 618d3b1 was committed at 21:07:19 UTC. The screener's transcript shows its first read of a target trace at 21:07:36. Before the commit it read only summary rows, the resolved list and one nudge count, all disclosed in §2. 2303c4c changed only "Pending." and the Status line above the results.
2. **Cohort: pass.** The 4 targets are the R-only ids on the informative 27. The control is the 19 ids neither arm resolved there: 27 minus the 4 both-resolved and the 4 targets.
3. **Numbers: pass.** I recomputed from `summary.jsonl`, the patch headers and `gold.jsonl`:
   - every §9.1 count field for the 4 targets: calls, turns, wall, patch files, gold files and failed edits;
   - the control flags a 9, b 5, c 8, empty 6, with 3 of 19 running a check, all the same.

   The readings follow: no letter holds on 3 or more targets, so row 3; rows 7 to 9 are as stated.
8. **Hygiene: fail.** `check_repo_hygiene.py` passes, but it only matches patterns.
   - In §9.1, the fastapi_15589 bullet reproduces a fragment of the E4B's patch: the call, its argument, and the old and new values.
   - The fastapi_13537 bullet's "for example" parenthetical reproduces the model's text-form calls.

   Both are trace or patch content. HEAD will be clean once they are removed, but the blobs stay in history; whether that matters under plan.md:52 is the user's call.

## Required fixes (screener)
Delete the original text rather than striking it through, because struck text still carries the content. Add a dated note in §9.6 saying the text was removed for hygiene (critic light, 2026-11-05).
1. In §9.1, the fastapi_13537 bullet: replace the parenthetical that begins "(for example a" with "(a shell search and a file read, written as text)".
2. In §9.1, the fastapi_15589 bullet: replace the sentence that begins "The edit flips the fallback" with "The edit inverts a boolean default in the gold file." Keep the sentence that follows it, on Arm R.
