---
id: D-008
title: Restart the E4B smoke-8 harness loop on the pipeline tree, with mechanisms (a copy adapter on the applier, location-diverse drafters, a reproducer stage) and no prompt wording
decision: continue
status: proposed, revised 2026-11-09 after the critic's `direction` review (needs-work; `experiments/EXP-062/critic.md`, ff8654b, 81c907d). The restart is the user's word (2026-11-09, `knowledge/user-decisions.md`); the ranking is the lead's.
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

## Revision 2026-11-09 after the critic (read first; the original ranking below is kept as written)
- **New order:**
  1. Location-diverse drafters (EXP-064, the screener).
  2. A reproducer stage used as the applier's selector (EXP-063, the experimenter). It writes one test at a path the harness strips from the patch, and the applier keeps the first draft that passes it.
  3. The two fused, in a later round.
  
  The copy adapter on the applier is **parked** for three reasons:
  - of the 16 failed applier edits in EXP-061 and EXP-062, 5 lost an argument and 7 were exact copies of drafts whose text did not match the file, so exact copying fixes at most about 4;
  - the adapter's one agent run, EXP-058, failed 10 of 20 edits against the base's 7 of 17;
  - it would override EXP-054 §10.5, and the drift gate's G4 (prose drift on every token) is not answered by changing the role.
- **Harm row, restated:** empty patches above the base maximum of 2 of 8, or any cap hit, or mean wall over about 150 s. The original "non-empty in EXP-061 or EXP-062" fires on any empty patch, since every task is non-empty in at least one base run; EXP-062 itself would have fired it, on requests_7205.
- **Kill rules are per EXP** and set in each pre-registration against the pooled EXP-061 and EXP-062 reference.
- **Each smoke-8 here is a screen, not a decision.** Even a perfect result gives p of about 0.10 against the pooled base (critic).
- **Only fastapi_14448 and rich_3468 can still change outcome on smoke-8.** Their failed runs split into wrong file 4, wrong fix 4, failed edit 0 (EXP-053 §1), which is why diversity and selection rank first. Both are reported separately in each EXP.
- **Final check, restated:** three kept mechanisms at 0.3 to 0.5 task each make at most about 1.5 tasks, against the 4 that one LB draw can see. The honest final state is therefore one of two:
  - a package of kept process endpoints, put to the LB once on the user's word, read as one draw;
  - a written finding that on smoke-8, 13 E4B runs resolved only fastapi_14301 and rich_3006 (critic), so the ceiling here is the model, not the harness. That finding is paper-track material.

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
- **Critic's dissent (needs-work, 2026-11-09, verbatim):** "Rank 1 belongs below ranks 2 and 3. Of the 16 failed applier edits in EXP-061 and EXP-062, 5 lost an argument and 7 copied a draft exactly whose text did not match the file, so exact copying fixes at most 4. The adapter's one agent run, EXP-058, failed 10 of 20 edits against the base's 7 of 17. The harm row and the rank-1 kill must be restated before any pre-registration, because the unchanged base fires both. Three kept mechanisms at 0.3 to 0.5 tasks each make at most 1.5 against the 4 the final check needs."
  - **Lead's response:** accepted in full; see the revision section above. The critic also recommended fusing ranks 2 and 3, because the applier took draft 1 on 5 of 6 matched tasks, so diverse drafts need a selector; that is now the order. The critic's claim that a `test_*.py` name is stripped from the patch is to be confirmed in EXP-063's desk check.

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

## Note 2026-11-10: the user's "tweak the agents" and the midterm rule
- **User's word:** "no writeup let's tweak the agents" (`knowledge/user-decisions.md`, 323abfe). The lead reads it as a request to go on changing the pipeline's agents.
- **Reconciliation:** the midterm rule above still governs the stage mechanisms; it is not rewritten here.
  - EXP-064 did not move its endpoint (row 3).
  - If EXP-063 also reads dropped or not exercised, ranks 2 and 3 end as written. EXP-066 (the reader's search form) is the follow-up that EXP-064 §10 named.
  - Whatever those read, the user's word keeps the loop going on a **new target: edit reliability**.
- **Lead's count (zero GPU) behind the new target:** across EXP-061-r, EXP-062-r and EXP-064-loc, 31 of the applier's 57 `edit_file` calls failed. Only 6 were argument loss. The harness matcher already forgives whitespace, indentation and JSON escaping (edit.py:401-454), so the lead read the rest as content mismatches. (Corrected 2026-11-10 by EXP-067: 2 of the 25 are a quote-wrapped `filepath`, "Source path not found", not a content mismatch.) Two of the 24 task-runs ended with an empty patch because every edit failed.
- **Next steps:**
  - EXP-067 (screener, zero GPU) finds which stage corrupts `old_string`: the reader's REGION copy, the drafter's OLD, or the applier's paste.
  - The class that dominates picks the one variable for the next smoke-8.
  - That direction change, a pivot to edit reliability, goes to the critic at the `direction` tier once EXP-067's count is in.
- **Honest scope:** EXP-053 put class B (an edit failing at one place) at 4 of 24 unresolved runs, behind C (right file, wrong fix) 12 and A (wrong file) 8. This target saves budget and fills empty patches; it does not by itself make fixes correct.
- **EXP-067 read (screener; c36c64a, a6c09bb; zero GPU).** 23 of the 31 failures could be classified. They fall in 4 task-runs:
  - R1, the reader's REGION differs from the lines it read: 11, all in EXP-064-loc.
  - E, a stale old_string after an earlier applied draft: 8, only in the same-location trees.
  - M, an ambiguous match: 3.
  - O, the applier's own edit: 1.
  - Drafter drift D and paste drift P: 0 each.
  - The reading is "mixed, plurality reader". First-edit-applies is 17 of 24 (EXP-064-loc 6 of 8).
- **Next:** EXP-068 (screener) builds the one variable. Each drafter reads its own FILE and LINES with `read_file` and copies OLD from that result, and the reader gives no REGION. Base tree EXP-064. Push when a kernel slot frees.
