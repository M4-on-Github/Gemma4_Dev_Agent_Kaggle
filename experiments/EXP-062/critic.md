---
id: D-008-critic
exp: D-008
tier: direction
verdict: needs-work
verified: regenerated
date: 2026-11-09
---

# D-008 direction review (not a review of EXP-062)

This review sits in this file only because the critic's write guard allows no other path. A later review of EXP-062 itself must not treat it as a prior EXP-062 review.

## Verdict: needs-work

The two kill rules fire on noise from the base runs alone. The top-ranked mechanism's base evidence points away from it. The final check cannot be reached at the gains D-008 itself states.

## Findings

1. **The harm row is the same as "any empty patch".**
   - Every smoke-8 task has a non-empty patch in EXP-061 or EXP-062, so the row covers all eight tasks.
   - The base runs had empty patches on 3 of 16 task-runs. EXP-062 itself would have fired this row against EXP-061, on requests_7205.
   - Restate the row over the 5 tasks that are non-empty in both runs. Those 5 tasks had 0 empty patches in 10 base task-runs.
2. **The rank-1 kill rule cannot be read.**
   - With the base model, the applier failed 6 of 12 `edit_file` calls in EXP-061 and 10 of 20 in EXP-062. The base therefore fails "below 6 of 12" by itself.
   - All failures fall on 2 or 3 tasks per run.
   - Use a task-level endpoint against a pooled reference: in the base runs, 5 of 16 task-runs had a failed applier edit.
   - Even 0 of 8 against that reference gives a one-sided Fisher p of about 0.10. So this is a screen, not a decision. Rank 3 has no kill rule at all.
3. **Most applier failures are not transcription errors** (my count from the EXP-061 and EXP-062 traces) [I].
   - The two runs had 16 failed applier calls between them:
     - 5 lost an argument;
     - 7 used an `old_string` copied word for word from a draft, which did not match the file;
     - 4 used text found in no draft.
   - Copying the draft exactly can fix at most 4 of the 16.
   - The one agent run with this adapter (EXP-058 §9.4, recorded and not read) failed 10 of 20 edit calls. The base failed 7 of 17 on the same tasks.
   - EXP-054 §10.5 says no agent run with this adapter is licensed. D-008 must name that override.

## The dispatch's questions

- **(a) Does the evidence support the ranking? No: on the tasks that can move, rank 1 targets the empty class.**
  - Of the 24 unresolved runs in EXP-053 §1, 12 are on the three tasks the gold patch fails (httpx_3672, requests_7205, requests_7309).
  - Only fastapi_14448 and rich_3468 can still change: fastapi_14605 is gated, and the other two (fastapi_14301, rich_3006) are the only tasks that ever resolve. On those two tasks the classes are A 4, C 4, B 0.
  - Rank 1's cue sites are two gold-fail tasks and rich_3006, which resolved in 12 of the 13 runs.
- **(c) Gains, and whether the harness binds.**
  - All three mechanisms kept would add at most 1.5 tasks; the final check needs 4. Say that the realistic product is the finding that the model is the ceiling.
  - Cite the stronger evidence for the harness argument. 13 E4B runs on the smoke-8 ids, from EXP-033 to EXP-062 and spanning every tree, resolved only fastapi_14301 and rich_3006 (from the committed `summary.jsonl` files).
- **(d) Moving the adapter does not answer its failed gate.**
  - The move is a fair answer to G1, which measured the first tool chosen.
  - It does not answer G4, which measured drift on every token, `new_string` included.
  - The applier also copies from a draft, not from a read window as in training. This is a hypothesis to test, not a passed gate.
- **(e) Missing items.**
  - **A selector.** In EXP-061 the applied edit was draft 1 on 5 of 6 matched tasks. Location diversity without a selector changes little. Rank 3 is that selector, so fuse it with rank 2.
  - **Rank 3's hazard costs nothing to fix.** Name the scratch test `test_*.py` and the harness strips it from the patch (harness-stack).
  - **Desk check (a) is done.** EXP-058 §1 settled it from source.
  - **A screen cohort.** Consider screening on unresolved, informative dev-48 tasks instead of smoke-8. If a later dev-48 arm confirms a result found that way, beware the winner's curse.
