---
id: D-009
title: E4B pipeline edit reliability, one stage defect per round
decision: pivot
status: proposed (the user's word "tweak the agents", 2026-11-10; critic `direction` review pending, experiments/EXP-067/critic.md)
track: main
claims: []
date: 2026-11-10
---

## What are we trying to do?
Make the pipeline's edits land on the file. Today, over 24 task-runs of three pipeline runs, 31 of the applier's 57
`edit_file` calls fail (EXP-067). In 5 of the 40 task-runs since EXP-061, every edit failed and the patch came out empty:
requests_7309 in EXP-061, rich_3468 in EXP-064, fastapi_14301 and rich_3468 in EXP-063, and fastapi_14448 in EXP-066.

## How is it done today?
- The tree is a reader, then five tool-less drafters, then an applier. The reader copies a REGION of each file, the
  drafters copy OLD out of that REGION, and the applier pastes OLD as `old_string`.
- The harness matcher already forgives trailing whitespace, indentation, regex-level drift and JSON escaping
  (edit.py:401-454).
- EXP-067's classes over 31 failures:
  - A, argument loss: 6.
  - S, a quote-wrapped `filepath`: 2. EXP-066 adds 4 more.
  - R1, the reader mis-copied lines it read: 11, all in EXP-064-loc.
  - E, a stale `old_string` after an earlier applied draft: 8, only in the same-location trees.
  - M, an ambiguous match: 3.
  - O, the applier's own edit: 1.
  - D (drafter drift) and P (paste drift): 0 each.
- First-edit-applies: 17 of 24 task-runs; 6 of 8 on EXP-064-loc.
- Applier wording against resends was tried and did not work (EXP-053).

## What's new in our approach?
- Each round removes one copy hop or one argument-form defect, picked by the class that dominates on the current tree.
- Round 1 is EXP-068: each drafter reads its own FILE and LINES with `read_file` and copies OLD from that result, and
  the reader no longer copies a REGION.
- Round 2 is chosen by EXP-068's reading. Candidates: class S, if it recurs on the EXP-064 tree; class M, OLD widened
  to a unique anchor; the E4B's argument loss, already parked as C-024.

## Options
- **A (recommended): one stage defect per smoke-8 round on the EXP-064 tree,** as above, each round with its own
  first-turn tool-call row (the EXP-063 lesson).
  - Strongest argument against: this edit-failure class was 4 of 24 unresolved runs in EXP-053, behind "right file,
    wrong fix" (12) and "wrong file" (8). Edits that apply are necessary but not sufficient, so the LB gain may be zero.
- **B: stop E4B work and spend on the 31B main line** (our best is 0.18, S-012). There are 13.8 s of room per task at
  the 8-min cap, and every parallel shape failed there (EXP-049, EXP-032).
- **C: hold all development and keep the current best for the final pair.** This costs nothing but learns nothing.
- Critic's dissent: pending.

## Expected score impact
- At most about 5 of 40 task-runs (12%) end empty because no edit applied. Turning an empty patch into an applied
  edit resolves only when the drafted fix is right. On the pipeline base, resolves are 2 fixed tasks of 8 (fastapi_14301,
  rich_3006), so the conditional rate on the other tasks is near 0.
- So 0 to 1 task of 58 for the direction, P about 0.2 [I]. That is under the 4-task MDE, so no LB draw can read it.
  It is a process gain that a later package might carry.

## Risks and kill criteria
- **EXP-068 is not exercised:** at most 20 of 40 drafter turns open with `read_file`. The direction ends: the E4B will
  not run a tool step in a tool-holding stage reliably (EXP-063).
- **EXP-068 harm:** any tool_free task, a fabricated OLD on 3 or more tasks, 3 or more empty patches, a cap hit, or a
  mean wall over 150 s. The variant is dropped and round 2 is reconsidered.
- **Two rounds in a row without a kept reading:** the direction ends, under the loop's rule.
- No upload slot and no dev-48 without the user's word.

## Cost
About 0.35 GPU-h per smoke-8 round, so about 0.7 for two rounds. Zero-GPU desk work between rounds. No upload slots.

## Midterm check
After EXP-068: is first-edit-applies above 6 of 8 with R1 at 0, and no harm row?

## Final check
A tree whose first-edit-applies is at least 7 of 8 on two smoke-8 runs, with no empty patch caused by edit failure.
It goes forward only in a package, on the user's word. Otherwise, a written finding of which copy and argument
defects the E4B cannot be prompted out of.
