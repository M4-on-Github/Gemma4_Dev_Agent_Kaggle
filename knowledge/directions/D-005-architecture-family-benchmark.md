---
id: D-005
title: Benchmark the architecture families (best-of-N, orchestrator, role pipeline with verifier) against the single loop on the competition model, at a setting that can ship
decision: start
status: proposed
track: both
claims: [C-014, C-015]
date: 2026-11-05
---

Proposed 2026-11-05 after the user asked (verbatim in `knowledge/user-decisions.md`): "we can take the approach of best of N type of thing, or orchestrator type of thing or multi agent collaboration agents right? and we don't know which type do best? maybe do some lit review on the setups and meanwhile plan to benchmark it one the model for the competition and figure out which one we should go with?" Stage 0 below is already running because it costs no GPU time. Everything from Stage 1 on waits for the user's approval and for the critic's `direction` review, which is dispatched when Stage 0 has reported. Slots marked **pending** are filled from Stage 0, not guessed.

## What are we trying to do?
Decide by measurement, on Gemma 4 31B in this harness, which agent structure the final tree should have: one loop (F0), best-of-N with a selector (F1), an orchestrator that delegates to workers (F2), or a role pipeline with a verifier (F3). The answer is allowed to be "the single loop".

## How is it done today?
- Every public bundle at or above 0.22 that we have read is one `LlmAgent` loop (digest 2026-11-05). Rank 1 is 0.29 with 18 uploads and an unknown method; the best-of-18 arithmetic makes a true 11 or 12 of 58 enough to show a 17 (D-004 bound B13).
- Our baseline: 9 of 48 on dev-48 (EXP-028 Arm R), 10 and 11 of 58 on the board. Where it fails: 45 of 48 tasks name a gold file by about call 2, and 30 of 39 failures touch a gold file with the wrong fix (`experiments/EXP-030/critic.md`, `experiments/EXP-030/l1b_armR.json`).
- What each family is aimed at, against that failure:

| Family | Aimed at the wrong fix in the right file? | What we already hold |
|---|---|---|
| F0 single loop, raised call cap | partly: more attempts on the same fix | 18 of 48 tasks end on the 28-call cap (B8); arm T4 of EXP-032 is built and held |
| F1 best-of-N with selection | yes, if the candidates differ and a selector can tell them apart | C-015: no selection signal without hidden tests, never measured here; B12: union of R and RH is 11 against 10, but those two configs are nearly the same. EXP-034 Q1: **pending** |
| F2 orchestrator with workers | no, by itself: it reorganises the same calls | C-014: one secondhand datum, 12 of 18 down to 6 of 18 with same-model sub-agents [M]; a synchronous tool stalls siblings 78% of the time (EXP-007) |
| F3 role pipeline with a verifier | the verifier yes, the locate stage no (B11: about 5 of 48) | EXP-032 arm P1 running (parallel locate, then editor). EXP-034 Q2 says whether visible tests carry any signal: **pending** |

- Literature: Agentless (lit-2407.01489) is a locate, repair, validate pipeline that wins by selecting among patches with tests. The comparative review across the three families under our constraints (one model, no hidden tests, shared budgets, shared working directory) is with the lit-scout: **pending**.

## What's new in our approach?
Three things the usual comparison leaves out.

1. **Zero-GPU gates first (Stage 0).** Two numbers from runs we already own decide whether a family can pay before any hour is spent. EXP-034 Q1: the union of resolves across all our dev-48 arms minus the best arm is the ceiling of a perfect selector; below 4 tasks, best-of-N cannot be read on dev-48 or on the board and goes last. EXP-034 Q2: in the right-file-wrong-fix tasks, did the last test the agent saw pass or fail? A pass means a same-model verifier has no signal from existing tests and must rest on a model-written reproduction that fails before the fix; a fail means the constraint is budget.
2. **One common setting that can ship.** Every family runs with the same `eval_config.yaml`, and that setting is the one the 12-hour rule admits without a waiver: 4.5 min (B1) with a raised call cap (about 40; B8 says the clock, not the call cap, then binds; B14 says the single loop loses at most 1 of 9 resolves at that cap, n = 9, [I]). A family that wins only at 8 min cannot be uploaded without its own dev-48 time profile (B2: 13.8 s per task of headroom).
3. **Each family is built in the form the harness allows, and screened on its own mechanism.**

| Family | Tree (one model, declarative) | Mechanism endpoint at n = 8 | Kill at the screen |
|---|---|---|---|
| F0 | the shipped loop at 4.5 min and the raised cap | which cap ends each task; resolves finishing under the cap | none: it is the reference |
| F1 | locate, then `ParallelAgent` of 3 proposers that call no tools and each write one patch proposal, then one applier that applies the selected one and tests. Branches cannot each edit: the working directory is shared (C-015). Selector: **pending** (lit section A, EXP-034 Q1c) | proposals for a task differ in at least 2 of 3; the selector's pick differs from proposal 1 in at least 2 of 8 tasks; stage wall against B5 | proposals identical in 6 of 8 tasks, or the stage does not fit the cap |
| F2 | root `LlmAgent` with workers as `agent_tool` (explore, fix); design **pending** (lit section B) | delegations made and returned; calls and seconds spent on delegation against B3 and B4; context lost at the return | no delegation in 6 of 8, or the root runs out of calls before an edit in 4 of 8 |
| F3 | `SequentialAgent[locate, edit]` then `LoopAgent[verify, fix]` with at most 2 rounds (D-004 trees T1 and T2; P1 is the parallel-locate variant) | the verifier's reproduction fails before the fix in at least 4 of 8; the loop is reached before the cap | the verifier is reached in under 4 of 8, or its check passes on every patch |

A smoke-8 reads these counts and nothing about resolve rates (D-004 addendum, measurement matrix).

## Options
- A. **Stage 0 gates, then one mechanics screen per surviving family at the common setting, then at most two families on dev-48 paired against F0, then two board draws each. Recommended.** It spends hours only on families that passed a free gate and a cheap screen.
- B. Run all four families on dev-48 straight away. Against: 4 arms are 13 to 15 GPU-h at 4.5 min, half a week of quota, and a paired dev-48 contrast only reads large effects (about 5 net tasks: 5 wins to 0 losses, or 7 to 1).
- C. Decide from the literature alone. Against: no source we hold matches the constraints (one 31B model for every role, no hidden tests, 4.5 min, shared call budget); the review ranks hypotheses, it does not replace the run.
- Strongest argument against A: the instrument is weak. dev-48 and the board both need about 4 to 5 tasks of true gain to see anything, and the largest pool any family acts on is unknown until EXP-034. The plan may end with "no family is distinguishable from the loop", having cost about 17 to 20 GPU-h. That outcome is still the paper-track result and keeps the loop as the final tree.
- Critic's dissent: **pending** (`direction` review after Stage 0).

## Expected score impact
Unknown until Stage 0. The ceiling of F1 is EXP-034's union minus best; the ceiling of a verifier is the count of right-file-wrong-fix tasks whose failure is visible to a test the agent can run (EXP-034 Q2); the ceiling of a locate stage is about 5 of 48 (B11). P(some family beats F0 by 4 tasks of 58): low to moderate, lead's estimate, [I]; to be restated with numbers when Stage 0 reports.

## Risks and kill criteria
- Stage 0 kills: F1 if union minus best is under 4 tasks; the existing-test verifier if most right-file-wrong-fix tasks end on a visible pass (F3 then needs the reproduction form or is dropped).
- A family is killed at its screen by the rule in its table row, after at most one fix and re-run.
- `ParallelAgent` with tool-calling branches can crash on compaction in ADK 1.36 (issue 7324, [M]); F1's proposers call no tools for that reason. One such crash in a screen sends that family to its sequential form.
- Time: any family whose dev-48 profile projects above 11 h at 4.5 min is not uploaded. A blank slot costs a day.
- The whole direction is killed if no family passes its screen, or if after two board draws no surviving family is within 4 tasks above F0's pooled mean; the single loop at the common setting is then the final tree.

## Cost
| Stage | What | GPU-h | Slots | When |
|---|---|---|---|---|
| 0 | lit review, EXP-034 (running); EXP-032 P1 and EXP-033 E4B already approved under D-004 | 0 new | 0 | Nov 5 to 6 |
| 1 | F0 at the common setting on dev-48: the reference every family is paired against, and its time profile | about 3.5 | 1 to 2 draws | week of Nov 10 |
| 2 | one smoke-8 screen per surviving family at the common setting | about 0.7 each, at most 2.1 | 0 | week of Nov 10 |
| 3 | at most two families on dev-48, paired against F0 | about 3.5 each, at most 7 | 0 | week of Nov 17 |
| 4 | two board draws per surviving family | 0 | at most 4 | Nov 17 to 30 |
| 5 | the winning family re-screened on E4B for the small-model prize | about 0.7 | 1 to 2 | after Stage 3 |

Total about 14 GPU-h if two families survive, against 30 per week; each dev-48 arm is approved by the user one at a time. Paper track (Nov 12): Stage 0 and the two running screens are what can be reported by then. Rule for this week, fixed now: if EXP-032 P1 and EXP-033 both reach their worst cases (1.35 and 1.3 GPU-h), arm T4 moves to next week's quota.

## Midterm check
By Nov 7: the lit synthesis, EXP-034's two readings, and the P1 and E4B screens are in; the family table above has no pending cell; the critic's `direction` review is in Options; the user approves, changes or rejects Stages 1 to 5.

## Final check
One family (possibly F0) named as the final tree by the rule: it passed its screen, projects at or under 11 h at its shipping cap, has the largest paired net on dev-48 with ties going to the cheaper tree, and two board draws that are not below F0's pooled mean. The comparison table, with every family's mechanism counts and time cost, goes to the paper track whichever way it falls.
