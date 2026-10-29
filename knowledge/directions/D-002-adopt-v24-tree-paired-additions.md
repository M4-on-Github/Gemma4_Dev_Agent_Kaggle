---
id: D-002
title: Adopt the rank-3 v24 bundle at its own 8-min cap as the baseline tree, then add one measured, paired change at a time
decision: continue
status: active
track: main
claims: [C-002, C-003, C-005, C-007, C-008]
date: 2026-10-29
---

Migrated 2026-10-29 from EXP-022 §2.4 and §3, EXP-023, EXP-027 and EXP-028. Started 2026-10-25 (#8), committed to on 2026-10-28 (#11). Approved implicitly by the user's go-ahead on #11 and on pushing both EXP-028 arms.

## What are we trying to do?
Ship the one public config that has scored 0.24 on this hidden set, at the cap it was written for, and climb from there with single additions each measured on dev-48 before they take an upload slot.

## How is it done today?
The rank-3 team (Apache-2.0 release, kg-rank3-apache): 3,240-byte prompt, 8 min / 28 calls / 80 turns / 240 s, T 1.0, thinking 4096, graph tools banned; local best 39.1% resolve, 6.5% empty patches, median first edit at step 10; LB 0.18 (v19) and 0.24 (v24). Their unscored v25 raises calls to 40. Their LoRA adapters lost ~11 points.

## What's new in our approach?
The measurement, not the config: a one-variable contrast against #8 (EXP-027), a dev-48 time profile and 28-call incidence on our cohort (EXP-028 Arm R), and the lost-edit route their prompt lacks (EXP-028 Arm RH, C-005). Everything shipped from their bundle is credited.

## Options
- A. **Continue: read #11 and EXP-028 as pre-registered, pick the #12 tree (R or RH), then one arm per lever: `max_tool_calls` 40 (C-007), cap tuned from the measured mean (C-008).** Recommended.
- B. Jump to a package (RH + 40 calls + 9 min) for #12. Against: unreadable at one draw; EXP-003 showed call caps interact with the prompt.
- C. Return to our prompt with their caps. Against: C-009 and EXP-016 (our prompt at 8 min projects 14 h).
- Critic's dissent: not yet obtained; dispatch a `direction` review before the #12 proposal.

## Expected score impact
#11: theta ~ 10/58 (EXP-027 §3). Later additions: each <= 1-3 tasks, not readable on one draw; readable on dev-48 process endpoints only. Reaching the LB top needs more than this direction promises; it is the floor to build from (plan.md §6.1a).

## Risks and kill criteria
- A blank #11 fires EXP-027 row 1: next slot at 6.0 min, no higher override without the dev-48 time profile. Two blanks in a row kill the 8-min branch.
- EXP-028 T1 (projected > 10.5 h) moves the next slot to the cap that projects <= 10 h even if #11 scored.
- Kill the direction if the tree at any safe cap scores <= 8/58 on two draws: then the public config does not transfer to our side and the lever is elsewhere.

## Cost
~8 GPU-h spent (EXP-028), ~4 per further arm; one slot per day. To Nov 25: ~27 flexible slots, 8 reserved for the finals pair.

## Midterm check
Due now: #11 graded, EXP-028 analyzed and critic-reviewed, #12 tree chosen by the readings.

## Final check
A tree with >= 2 clean uploads at >= 11/58, with its dev-48 time profile and lost-edit behaviour measured, as one of the two finals.
