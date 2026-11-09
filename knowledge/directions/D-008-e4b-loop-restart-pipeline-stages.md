---
id: D-008
title: Restart the E4B smoke-8 harness loop on the pipeline tree, with mechanisms (a copy adapter on the applier, location-diverse drafters, a reproducer stage) and no prompt wording
decision: continue
status: proposed; the restart itself is the user's word (2026-11-09, `knowledge/user-decisions.md`); the ranking below is the lead's, open to the user and the critic's `direction` review
track: main
claims: [C-023, C-024]
date: 2026-11-09
---

Follows D-006 (E4B single-job agents, copy adapter) and D-007 (concurrent work inside one task). The loop's rules are
those of `knowledge/lessons-e4b-loop.md`, restarted: the two-keep-base stop count resets to zero, and a kept edit still
counts only after an LB draw or a dev-48 arm.

## What are we trying to do?
Raise the E4B's hidden-set score above 3/58 by changing what the agents do, not what the prompt says. Rounds 1, 2 and 4
showed that wording moves nothing on this model (EXP-053 row 3, EXP-055 row 3, EXP-057 row 3; lessons rounds 1 to 4).

## How is it done today?
- Two structurally different E4B trees scored the same: the single loop S-014 0.05 = 3/58, and the reader / 5 drafters / applier pipeline S-015 (EXP-061) 0.05 = 3/58, row L3.
- The pipeline's smoke-8 (EXP-061 §9) found the following:
  - the hand-off root works on 8 of 8 tasks;
  - drafts are near-copies of one another: drafters 1-4 were identical on rich_3006, and 1 and 3 on rich_3468;
  - the applier failed 6 of 12 `edit_file` calls, 4 of them by lost arguments;
  - 2 of 8 patches were empty.
- EXP-062 (the root re-transfers on every message; e49eb9a) read row 3, not exercised:
  - no task was nudged, so the fix was never tested;
  - no harm and no infrastructure row fired: 0 caps, the root transferred on its first message on 8 of 8, and all 8
    sessions ended on an applier `submit_patch`;
  - 3 tasks passed 14,336 prompt tokens, and compaction inside the run went through without a crash;
  - mean wall 89.2 s;
  - one patch was empty (requests_7205, no edit made).
  
  So the pipeline base of Option A stands.
- Failure classes over 24 unresolved E4B runs (EXP-053 §1): C, right file but wrong fix, 12; A, wrong file, 8; B, an edit that fails at one place, 4.
- On the base trees, 15 of 18 failing checks named files the model had not edited (EXP-059 §9), so the check rarely tests the edit.
- The temperature vote gave no second opinion: D = 0 of 8 (EXP-040).
- The copy adapter (EXP-054 v2) raised exact copy from 0.483 to 0.708 (McNemar p 1.4e-6), but it failed the free-agent drift gate. Its integration test was clean (EXP-058 row 3).
- The public frontier's design is a 31B single loop (briefing, dated 2026-10-29: about 0.24 = 14/58). The board has not been re-checked since.

## What's new in our approach?
Each stage of the pipeline is a place to put one mechanism, with a process endpoint readable at n = 8:
1. **Copy adapter on the applier only (rank 1).** The applier's job is transcription: it turns a shown draft into
   `edit_file` calls. That is exactly what the adapter was trained for, and the drift gate it failed (first-tool
   agreement, prose drift) concerns a free agent, not this role.
   - Cue sites: httpx_3672 and rich_3006 (EXP-061 §9: 1 of 2 edits failed on each) and requests_7309 (all 4 failed,
     3 by lost arguments).
   - Endpoint: failed and arg-lost `edit_file` calls in the applier, against EXP-061 and EXP-062.
   - Desk checks first:
     - (a) whether one sub-agent's `model:` can name the served adapter while the rest of the tree stays on the base;
     - (b) the open adapter-in-zip question. Until it is decided the arm is smoke-only.
   - Line: the experimenter's.
2. **Location-diverse drafters (rank 2).** The reader names K candidate locations, and drafter i drafts at location i,
   so drafts differ by where they edit, not by temperature.
   - Aimed at class A, and at the duplicate drafts.
   - Endpoint: distinct target files among the 5 drafts, and tasks where any draft edits the gold file. The reference
     is 6 of 8 gold-file landings (EXP-055).
   - Line: the screener's; the change is to prompts and state keys.
3. **Reproducer stage (rank 3, later).** Before drafting, a stage writes a small test at a workspace path, and the
   applier runs it after each applied draft.
   - Aimed at the 15 of 18 checks that test nothing of the edit.
   - Design hazard: a workspace file lands in the submitted diff, since only protected files are stripped. The
     pre-registration must say how it is removed before submit, or show it harmless.
4. **Zero GPU, alongside:** why requests_7309 makes 0 calls in every skill tree (4 of 4) and 4 to 7 on every base tree
   (5 of 5) (EXP-059). This blocks the skill-script route.

## Options
- **A (recommended): the ranking above on the pipeline base,** which is the EXP-062 tree (`experiments/EXP-062/candidate-r/`).
  EXP-062 read with no harm and no infrastructure row; its nudge path is still untested.
  - Strongest argument against: two different trees scored the same 3/58, so the harness may not be the binding
    constraint on this model. Every rank here may read as "no decision" at n = 8.
- **B: the loop on the single-loop base (EXP-033), by the letter of the rule** (nothing has been kept since). Ranks 1
  and 2 need a pipeline, so B leaves only rank 3 and the zero-GPU item.
- **C: stop E4B work and spend on the 31B main line.** The loop does not serve the 31B: at 8 min it has 13.8 s of room
  per task, and every parallel shape failed there (EXP-049 R1, EXP-032 P1). If "the solution" means the main-track
  score, only C funds it.
- Critic's dissent: pending the `direction` review, dispatched 2026-11-09.

## Expected score impact
- About 0.3 to 0.5 task of 58 per kept mechanism, P(success) about 0.2 to 0.3 each [I].
- Source: the C-024 ceiling (at most about 1 of 48 for the adapter on the single loop), and EXP-061's 2 empty patches
  of 8, of which the applier's edit failures are one route.
- Under 4 tasks, so no single LB draw can see it (plan.md §5.5). A kept mechanism goes to the LB only as part of a
  package, on the user's word.

## Risks and kill criteria
- The loop's rule stops it after two keep-base or dropped rounds in a row, at the day's ceiling, or on any
  infrastructure row.
- **Rank 1 is dropped** if the applier's failed `edit_file` count is not below EXP-061's 6 of 12, or if any harm row
  fires (an empty patch on a task that was non-empty in EXP-061 or EXP-062, or a cap hit).
- **Rank 2 is dropped** if the drafts' distinct target files are not above EXP-061's count (to be counted from its
  traces before the pre-registration).
- No upload slot is spent by this direction without the user's word.

## Cost
- About 0.3 GPU-h per smoke-8 round (EXP-053 to EXP-062: 0.27 to 0.32), and about 0.35 for the adapter round (EXP-058 0.316).
- Ranks 1 to 3 cost about 1.0 GPU-h, plus zero-GPU desk work.
- No upload slots and no dev-48.
- The weekly quota figure, its reset day and the L4x4 rate are still unverified (plan.md:25).

## Midterm check
After the first two rounds: does one mechanism move its process endpoint past its reference with no harm row? If
neither does, this direction ends, by the same rule that stopped the loop on 2026-11-08.

## Final check
A package of kept mechanisms whose dev-48 or LB reading, on the user's word, beats 3/58 by 4 or more tasks. Or a
written finding that the E4B's ceiling here is the model, not the harness, which is also paper-track material.
