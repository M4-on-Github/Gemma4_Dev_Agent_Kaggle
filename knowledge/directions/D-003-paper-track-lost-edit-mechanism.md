---
id: D-003
title: Paper track - the lost-edit mechanism, its detector, the budget trade-off, and the released toolkit
decision: continue
status: active
track: paper
claims: [C-004, C-005, C-001, C-002, C-011]
date: 2026-10-29
---

Migrated 2026-10-29 from plan.md §7, paper/outline.md and paper/writeup-draft.md (2,716 words, sections 1-3 and 5-7 complete, section 4 stub).

## What are we trying to do?
Submit a <= 3,000-word Writeup by 2026-11-12 23:59 UTC that scores >= 4/5 on Verifiability and Clarity, built only on experiments we run anyway, and qualify for Best New Resource with the analyzer, budget estimator and per-task CSVs.

## How is it done today?
Public writeups known to us: the rank-3 team's "Git History as a Gym" (verified practice tasks from git history) and a context-reset post (96% vs 16% on a 25-task benchmark, unsourced). No published source isolates the `edit_file` argument loss, the detector gap, or a time-cap contrast for a small model under a 12 h regime (research/2026-10-28-literature-review.md §1, §9).

## What's new in our approach?
A measured, mechanism-level harness finding (C-004) with a validated detector; a pre-registered paired mitigation test (C-005, EXP-028); the LB noise floor measured on our own and the frontier's repeated uploads (C-001); a one-variable time-cap contrast (C-002).

## Options
- A. **Finish as outlined: section 4 from the critic-accepted EXP-028 result; keep the backup taxonomy material in section 5.** Recommended.
- B. Pivot the primary contribution to the time-cap contrast if #11 scores high. Against: one draw, inside-MDE caveats; it belongs as a section, not the spine.
- Critic's dissent: not yet obtained; dispatch a `direction` review by Nov 3.

## Expected score impact
Separate prize; no LB effect. Rubric self-assessment in plan.md §7.2.

## Risks and kill criteria
- EXP-028 compliance contrast underpowered (row 1): section 4 reports counts and the mechanism, labelled "not yet testable at this n", as EXP-025 §4 row 1 already provides for.
- Word limit: 284 words left; section 5.2 is the compressible one.
- Clarity: hosts have said generated-sounding prose scores badly; the user reviews every section.

## Cost
0 GPU-h beyond EXP-028; paper-writer dispatches; the user's review time.

## Midterm check
Nov 5: full draft with figures and a `full` critic review of its claims.

## Final check
Nov 11: Writeup submitted by the user; `paper/release/` CSVs exported through `export_release_csv.py`; every number traceable.
