---
id: D-010-critic
exp: D-010
tier: direction
verdict: needs-work
verified: regenerated
date: 2026-11-11
---

# D-010 direction review (not a review of EXP-070)

This review is filed here only because the critic's write guard allows no other path and the dispatch named this file. A later review of EXP-070 itself must not treat it as a prior EXP-070 review.

## Verdict: needs-work

Rounds 1 and 2 go ahead under the user's terms. The ranking of rounds 3 to 5 has two defects that change it:

1. Round 4's lever is already in the tree.
2. The signal round 3 would select on is rare in our own grading record.

## Dissent (quotable)

D-010 reads a mechanism endpoint on the E4B as a reason to ship, and the record says otherwise.
- EXP-069 landed the first edit on 8 of 8 tasks with 0 empty patches, and resolved the same 2 of 8 tasks as EXP-064.
- Of 23 unresolved patched task-runs that have an empty-patch grading of the same task, 21 grade like the empty patch. A verify that acts only on new failures therefore has about one event to act on, and a selector built on it will pick draft_1, which the applier already picks in 27 of 40 multi-draft passes.
- Round 4's per-drafter temperatures have been in the tree since EXP-052 (0.3 to 1.0).
- A kept form on a carrier that scores 0 to 3 of 58 cannot approach our 0.18 on a best-of LB. It cannot be read at an MDE of 4. It would also take a final that belongs to a 31B variant.

The one round that could create a selection signal is a reproducer stage with the hard first-call opener. That opener removes the probable cause EXP-068 §1.3 named for EXP-063. It held on 36 of 40 drafter turns, but it has not been tested on a reproducer. D-010 does not rank this round. A kept form justifies a written finding and a time-costed 31B port proposal, not an upload.

## 1. Ranking of rounds 3 to 5

- **Round 4, temperatures: a no-op as written.** `drafter_1..5.yaml` in `candidate-loc` already set temperatures 0.3, 0.5, 0.7, 0.9 and 1.0 (EXP-052).
  - Even a different lever (a wider spread, top_p, thinking) mostly reaches drafts the applier never uses: its first applied edit is draft_1 in 27 of 40 multi-draft passes, and in 14 of 23 on the EXP-064 tree (EXP-070 check 3).
  - Drop round 4, or redefine it and rank it below selection.
- **Round 3, selection: conditioned on the wrong event.** Make it conditional on EXP-072 showing a new-failure event (post-edit against baseline) on at least 2 of 8 task-runs, not on the check merely running.
  - My count from `task_results.jsonl` (pytest's count lines and the number of FAILED lines in the 1500-character tail) covers 23 unresolved patched task-runs whose task also has an empty-patch grading in the seven pipeline runs:
    - 21 have the same failure counts as the empty patch;
    - 1 is worse (fastapi_14448 in EXP-069);
    - 1 is unreadable (rich_3468 in EXP-066).
  - On the three tasks that can resolve (fastapi_14301, fastapi_14448, rich_3468), the split is 9 same, 1 worse and 1 unreadable of 11.
  - Caveats [I]: the graded file is the hidden version, not the suite the applier runs. The fastapi_14448 rows are compared by FAILED-line count. requests_7205 and requests_7309 fail even with the gold patch, so their rows say nothing about resolves.
  - C-015's own text applies: there is no selection signal without hidden tests.
- **The ±20 window: trigger it on any EXP-071 outcome except promote, and rank it above selection.**
  - By EXP-071's own blind numbers, P(kill) is about 0.07 [I: (0.65 × 0.8 × 0.95) × 0.15]. So "the fallback if killed" almost never fires.
  - The change is arithmetic in the drafter prompt, so it needs no new compliance; drafters opened with a read on 36 of 40 turns.
  - EXP-068 §10 shows that ±20 covers all 3 misses. That width is read off the same three misses, though, and §10.1 shows drifts of 29 to 44 lines at three REGION-tree locations that ±20 would not cover.
  - Cost: the applier sees all five reads. httpx_3672 already had a first applier prompt of 20,709 tokens at ±5. Record it against both 14,336 and 32,768.
- **The fused tree last: right, but it has no base of record.**
  - EXP-071 sits on `candidate-read`, and EXP-072 sits on `candidate-loc`. Fusing them is an interaction that no round screens.
  - Name the base. Require no lost resolve on fastapi_14301 or rich_3006: EXP-068 lost rich_3006, which resolved in the other 6 pipeline runs.

## 2. Do EXP-070's post-hoc rules bias the ranking?

- **Not through the cut.** Any threshold above 0.6 and up to 2.5 per 8 gives the same split:
  - in: verify, selection, diversity;
  - out: majority vote 0.3, empty report 0.4, vendoring 0.6.
- **The definition changes recorded in §7 went toward fewer hits**, and the file says plainly what it saw and when.
- **The bias is in the trigger definitions.**
  - Verify's trigger, "any applied edit" (7.0 per 8), measures opportunity, not the event its mechanism needs. That event, a new failure against baseline, was not counted (see §1).
  - The diversity and selection triggers count how distinct the drafts are, not whether a draft other than draft_1 reaches the file.

## 3. Can n = 8 read these endpoints?

- **Compliance counts: yes, as bounds.**
  - A check that runs on at least 5 of 8, against a reference of 6 of 48, is far outside noise.
  - W ≥ 7 against a reference of 4 has P 0.035 at p 0.5 (EXP-071 §3).
- **A better pick, or any resolve effect: no.**
  - fastapi_14448 and rich_3468 are the only movable tasks, and the E4B has resolved neither.
- **The verify's revert action: probably not exercised.** At the rate in §1 it expects about 0 to 1 events per 8.

## 4. What a kept form justifies for an upload

- **No slot on LB grounds.**
  - The LB keeps the best score. The E4B has scored 3, 3, and 0 or 1 of 58 (S-014 to S-016). Adding D-010's 0 to 2 tasks cannot approach 11 of 58 (0.18, S-012), and no single draw can read the gain.
  - The second final should be a 31B variant.
- **The ports to the 31B are time-bound or have no analog.**
  - A verify run costs 20 to 40 s. All of that range exceeds the 31B's measured room of 13.8 s to the 10.5 h ceiling, and its top exceeds the 28.8 s to the 11 h gate (D-004 B2).
  - The anchor and ±20 forms have no counterpart in a single loop.
- **What a kept form does justify:** a written finding, plus a costed port proposal. Any E4B upload is the user's call, under a recorded plan.md §5.8 override.

## Direction checklist

- **Weakest assumption.** "A mechanism endpoint is a reason to ship." The evidence against it is EXP-069 and the grading record in §1.
- **Option not considered.** A reproducer stage that opens with the first-call rule. It is the only route here to a signal that can tell drafts apart.
- **A top-5 team [I]** would most likely run the 31B single loop with reproduction tests, not a small-model pipeline.

## EXP-072: flags (non-blocking; pre-register them before the push)

1. A count of new-failure events, with a predicted number (reference: about 1 in 23, §1).
2. How fastapi tasks count when collection exits 2 both before and after the edit.
3. The harm row for a lost resolve on fastapi_14301 or rich_3006, as D-010 states.
4. The base tree, by name.

## Required fixes to D-010 (no GPU)

1. Drop round 4, or redefine its lever; the temperatures are already distinct.
2. Make round 3 conditional on EXP-072's new-failure events (at least 2 of 8), not on the check merely running.
3. Trigger the ±20 window on any EXP-071 outcome except promote, and rank it above selection.
4. Name a base of record for the fused tree, and add a no-lost-resolve condition on fastapi_14301 and rich_3006.
5. Rank the reproducer-with-opener option, or say why not.
6. Restate the final check: a kept form yields a finding plus a costed 31B port proposal, and an upload only on the user's word.
