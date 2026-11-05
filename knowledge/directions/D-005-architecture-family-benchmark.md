---
id: D-005
title: Benchmark the architecture families (best-of-N, orchestrator, role pipeline with verifier) against the single loop on the competition model, at a setting that can ship
decision: start
status: proposed
track: both
claims: [C-014, C-015]
date: 2026-11-05
---

Proposed 2026-11-05 after the user asked (verbatim in `knowledge/user-decisions.md`): "we can take the approach of best of N type of thing, or orchestrator type of thing or multi agent collaboration agents right? and we don't know which type do best? maybe do some lit review on the setups and meanwhile plan to benchmark it one the model for the competition and figure out which one we should go with?" Stage 0 below is already running because it costs no GPU time. Everything from Stage 1 on waits for the user's approval and for the critic's `direction` review, which is dispatched when Stage 0 has reported. Slots that were marked pending were filled on 2026-11-05 from Stage 0 (section "Stage 0 results"); the critic's `direction` review arrived the same day (`experiments/EXP-034/critic.md`, needs-work) and the section "Critic review and revision" supersedes the staging, the common setting and the impact table wherever they differ.

## What are we trying to do?
Decide by measurement, on Gemma 4 31B in this harness, which agent structure the final tree should have: one loop (F0), best-of-N with a selector (F1), an orchestrator that delegates to workers (F2), or a role pipeline with a verifier (F3). The answer is allowed to be "the single loop".

## How is it done today?
- Every public bundle at or above 0.22 that we have read is one `LlmAgent` loop (digest 2026-11-05). Rank 1 is 0.29 with 18 uploads and an unknown method; the best-of-18 arithmetic makes a true 11 or 12 of 58 enough to show a 17 (D-004 bound B13).
- Our baseline: 9 of 48 on dev-48 (EXP-028 Arm R), 10 and 11 of 58 on the board. Where it fails: 45 of 48 tasks name a gold file by about call 2, and 30 of 39 failures touch a gold file with the wrong fix (`experiments/EXP-030/critic.md`, `experiments/EXP-030/l1b_armR.json`).
- What each family is aimed at, against that failure:

| Family | Aimed at the wrong fix in the right file? | What we already hold |
|---|---|---|
| F0 single loop, raised call cap | partly: more attempts on the same fix | 18 of 48 tasks end on the 28-call cap (B8); arm T4 of EXP-032 is built and held |
| F1 best-of-N with selection | yes, if the candidates differ and a selector can tell them apart | C-015: no selection signal without hidden tests, never measured here; B12: union of R and RH is 11 against 10, but those two configs are nearly the same. EXP-034 Q1: union minus best is 5 of 48 over six arms (the gate passes), but 1 between R and RH, the two arms that are nearly one config |
| F2 orchestrator with workers | no, by itself: it reorganises the same calls | C-014: one secondhand datum, 12 of 18 down to 6 of 18 with same-model sub-agents [M]; a synchronous tool stalls siblings 78% of the time (EXP-007) |
| F3 role pipeline with a verifier | the verifier yes, the locate stage no (B11: about 5 of 48) | EXP-032 arm P1 running (parallel locate, then editor). EXP-034 Q2: neither reading fired. 21 of 30 right-file-wrong-fix tasks ran no test after the last edit; 7 ended on a visible pass and were still wrong |

- Literature: Agentless (lit-2407.01489) is a locate, repair, validate pipeline that wins by selecting among patches with tests. The comparative review (`research/lit/lit-2026-11-05-architecture-families.md`, 22 notes) finds no source that compares the families on one open model at a matched budget. What repeats across sources: structure pays when it adds an executed signal (tests, run results) and does not pay when it adds more same-model opinion. Details in "Stage 0 results".

## What's new in our approach?
Three things the usual comparison leaves out.

1. **Zero-GPU gates first (Stage 0).** Two numbers from runs we already own decide whether a family can pay before any hour is spent. EXP-034 Q1: the union of resolves across all our dev-48 arms minus the best arm is the ceiling of a perfect selector; below 4 tasks, best-of-N cannot be read on dev-48 or on the board and goes last. EXP-034 Q2: in the right-file-wrong-fix tasks, did the last test the agent saw pass or fail? A pass means a same-model verifier has no signal from existing tests and must rest on a model-written reproduction that fails before the fix; a fail means the constraint is budget.
2. **One common setting that can ship.** Every family runs with the same `eval_config.yaml`, and that setting is the one the 12-hour rule admits without a waiver: 4.5 min (B1) with a raised call cap (about 40; B8 says the clock, not the call cap, then binds; B14 says the single loop loses at most 1 of 9 resolves at that cap, n = 9, [I]). A family that wins only at 8 min cannot be uploaded without its own dev-48 time profile (B2: 13.8 s per task of headroom).
3. **Each family is built in the form the harness allows, and screened on its own mechanism.**

| Family | Tree (one model, declarative) | Mechanism endpoint at n = 8 | Kill at the screen |
|---|---|---|---|
| F0 | the shipped loop at 4.5 min and the raised cap | which cap ends each task; resolves finishing under the cap | none: it is the reference |
| F1 | locate, then `ParallelAgent` of 3 proposers that call no tools and each write one patch proposal, then one applier that applies the selected one and tests. Branches cannot each edit: the working directory is shared (C-015). Selector: executed first. The applier applies a proposal and runs one check, keeps the first proposal whose check passes, breaks ties by the smaller patch, and never votes (a majority vote ties at N = 3 and added nothing where it was isolated; lit section A). Free proxies carry little: the best one, submit before the cap, is +1.12 of 48 over a random non-empty patch (EXP-034 section 9.1) | proposals for a task differ in at least 2 of 3; the selector's pick differs from proposal 1 in at least 2 of 8 tasks; stage wall against B5 | proposals identical in 6 of 8 tasks, or the stage does not fit the cap, or one apply-and-check takes over 60 s (three then cannot fit in 270 s) |
| F2 | root `LlmAgent`, the only writer, with one read-only investigator called through `agent_tool` that returns a short curated brief (the one shape the sources allow; lit section B). Ranked last after Stage 0 and screened only if the user wants it measured | delegations made and returned; calls and seconds spent on delegation against B3 and B4; context lost at the return | no delegation in 6 of 8, or the root runs out of calls before an edit in 4 of 8 |
| F3 | `SequentialAgent[locate, edit]` then `LoopAgent[verify, fix]` with at most 2 rounds (D-004 trees T1 and T2; P1 is the parallel-locate variant) | the verifier's reproduction fails before the fix in at least 4 of 8; the loop is reached before the cap | the verifier is reached in under 4 of 8, or its check passes on every patch |

A smoke-8 reads these counts and nothing about resolve rates (D-004 addendum, measurement matrix).

## Stage 0 results (2026-11-05)
Sources: `research/lit/lit-2026-11-05-architecture-families.md`; `experiments/EXP-034-bestofn-ceiling-and-test-signal.md` section 9; `experiments/EXP-033-e4b-single-loop-smoke8.md` section 9. None of the three has a critic verdict yet, so none moves a claim.

**Literature.** All numbers were read through a summarising fetch tool, not from PDFs (the scout's own caveat).
- Selection that runs tests closes 39 to 55% of the gap between a random candidate and the oracle (CodeMonkeys 45.8 random, 57.4 selected, 69.8 oracle; R2E-Gym 34.4, 51.0, 64.4; Agentless 77 by vote, 96 with tests, 126 oracle). Those runs use 10 to 40 candidates and no wall-clock cap. A majority vote over patches added nothing where it was isolated, and a same-model judge helped only on top of test results.
- The one table with equal-budget single and multi-agent arms on SWE tasks puts every multi-agent topology at or below the single agent; the centralized (orchestrator) one is 3.1% lower with about 3.8 times the turns (lit-2512.08296, n = 20 per cell, direction only). AOrchestra wins with one model and loses with another.
- In role pipelines the gain sits in the roles that execute: removing the Tester costs 14 of 100, the Debugger 11, the text-only Critic 4 (lit-2604.13120); repository regression tests add 4.5 points as a check (lit-2504.07164). No source shows a gain from a same-model reviewer that only reads.
- Below about 10B, a fixed locate-then-repair workflow beat a free loop in one table (Seed-Coder-8B 19.2 against 11.2, lit-2506.03524).
- Not found: any ablation of prompt or edit-format diversity as a way to generate candidates; a source for C-014's "12 of 18 down to 6 of 18".

**EXP-034 Q1, the selection ceiling.** Resolves per arm 11, 12, 11, 9, 9, 10; union 17; union minus best 5, so the pre-registered gate keeps F1. Two qualifications, both in the EXP file: between R and RH the number is 1 (most of the 5 is difference between configs, not between draws of one), and the best free proxy scores 13.33 of 48 over six full runs against 12 for the best single arm. Tasks solved always, sometimes, never: 6, 11, 31. A selector can act on the 11.

**EXP-034 Q2, the test signal.** Of Arm R's 30 right-file-wrong-fix tasks: last visible result after the last edit was a pass in 7, a fail in 1, an error in 1, and there was no test after the last edit in 21 (16 ran no test anywhere). RH replicates it (4, 1, 0, 22 of 27). Endings: 15 by `submit_patch`, 11 on the call cap, 3 on the clock, 1 on the turn cap. Lead's reading [I], **retracted 2026-11-05 after the critic's count**: "half of these tasks handed in a wrong fix with budget left and without checking it". The record supports less: 8 of 30 submitted with no counted test after the last edit (4 if a `python -c` run counts as a check), 4 of those 8 are tasks the grader could not test, and only 2 submitted before 270 s. What stands: 21 of 30 ran no counted test after the last edit, and 10 of the 15 submits came after 270 s. A reproduction that failed before the first edit exists in at most 6 of 48 tasks (3 in this group).

**EXP-033, E4B single loop, smoke-8.** The loop works: 8 of 8 tasks ran and submitted, 0 malformed calls in 43, 6 of 8 non-empty patches, 6.0 s per turn, mean wall 56.9 s, 423 s left under the 8 min cap, about 0.25 GPU-h. Resolves 2 of 8 are recorded and not read (n = 8). For E4B the clock does not bind, so every family fits, and a dev-48 arm costs about 1 GPU-h instead of 3.5.

**Ranking after Stage 0 (lead, weakly ordered, [I]).** F3 in its executing form, then F0 with the raised cap, then F1, then F2. Changes to the plan that follow:
1. F3 is screened first, and its verify stage must run a command; a reviewer that only reads is dropped. It is screened in two forms on the same 8 tasks if hours allow: one loop told to check after its last edit, and `LoopAgent[verify, fix]`, because a model playing the stages in one conversation matched the multi-agent run in lit-2601.12307 and our traces say the instruction alone is not followed.
2. F1 passes its gate and keeps its screen, second in line. Its proposers get different instructions or edit formats, not one prompt three times, since draws of one config differ by about 1 task.
3. F2 gets no screen unless the user asks for one (0.7 GPU-h). The evidence against it is from other models, so this is a ranking, not a measurement.
4. EXP-035 (zero GPU, added to Stage 0): for the right-file-wrong-fix tasks, read the grader's own test output and split the failing tests into those that already exist in the task snapshot, which the agent could have run, and those the hidden test patch adds. This sizes the pool an executed check on existing tests can see.
5. E4B gets its own reference arm on dev-48 (Stage 1b, about 1 GPU-h, user approval), which `plan.md` section 5.8 requires before any E4B upload for the small-model prize.

## Options
- A. **Stage 0 gates, then one mechanics screen per surviving family at the common setting, then at most two families on dev-48 paired against F0, then two board draws each. Recommended.** It spends hours only on families that passed a free gate and a cheap screen.
- B. Run all four families on dev-48 straight away. Against: 4 arms are 13 to 15 GPU-h at 4.5 min, half a week of quota, and a paired dev-48 contrast only reads large effects (about 5 net tasks: 5 wins to 0 losses, or 7 to 1).
- C. Decide from the literature alone. Against: no source we hold matches the constraints (one 31B model for every role, no hidden tests, 4.5 min, shared call budget); the review ranks hypotheses, it does not replace the run.
- Strongest argument against A: the instrument is weak. dev-48 and the board both need about 4 to 5 tasks of true gain to see anything, and the largest pool any family acts on is unknown until EXP-034. The plan may end with "no family is distinguishable from the loop", having cost about 17 to 20 GPU-h. That outcome is still the paper-track result and keeps the loop as the final tree.
- Critic's dissent (2026-11-05, verbatim): "The benchmark's instrument partly measures the sandbox: 15 of the 48 dev-48 tasks are graded without two test-only packages the Kaggle sandbox lacks, and the shipped v24 prompt, which dropped our vendoring section, resolves none of them while the older-lineage arms resolve 1-2 through vendored code; 11 of Arm R's 30 right-file-wrong-fix tasks never had their hidden tests run, and on the other 33 tasks the six-arm best-of-N ceiling is 3, not 5. Re-grade R and RH with the shims on a CPU kernel, finish EXP-035 on the graded tasks, and test porting the vendoring section as its own one-variable arm, keeping ship decisions on the as-run grade until we know whether the hidden grader has these packages. Then screen one change at a time against Arm R at its shipped 8 minutes, starting with a required executed check, rather than four structures at 4.5 minutes, where 10 of R's 15 wrong-fix submits would never happen because they came after 270 s." The lead accepts it; see "Critic review and revision".

## Expected score impact
**Superseded the same day by the table in "Critic review and revision"; kept for the record.** Restated 2026-11-05 from Stage 0. Every figure here is the lead's inference [I] from the numbers in "Stage 0 results"; none is a measured effect.

| Family | Pool it can act on | Expected gain on dev-48 | P(at least 4 of 58 on the board) |
|---|---|---|---|
| F3, executed verify and fix | at most 23 of 48: the 30 right-file-wrong-fix tasks less the 7 whose visible tests passed on a wrong patch. How many of the 23 a runnable test can see is unknown; EXP-035 sizes it | +2 of 48 if the published effect of regression-test checking transfers (+4.5 points, lit-2504.07164); more only if EXP-035 finds a large visible pool | about 0.2 |
| F0, raised call cap | the 11 right-file-wrong-fix tasks that ended on the call cap | unknown until arm T4 of EXP-032 runs | about 0.15 |
| F1, best-of-3 with an executed selector | expected union of 3 arms 14.2 against a random arm 10.3, a gap of 3.9; selectors that run tests close 39 to 55% of such a gap in the sources | +1.5 to +2.1 of 48, and less if the three proposals come from one config (R and RH: gap 1.5, so +0.6 to +0.8) | about 0.1 |
| F2, orchestrator | none identified: location is already found in 45 of 48 | 0 or negative | under 0.05 |

No family has evidence for a gain the instruments can read with confidence (dev-48 needs about 5 net tasks, the board about 4). The likeliest end state is the single loop with an executed check, as a `LoopAgent` if the model does not run the check when only told to.

## Critic review and revision (2026-11-05)
Review: `experiments/EXP-034/critic.md` (verdict needs-work on EXP-034; every Q1 number regenerated exactly; readings applied as written). EXP-035 (`experiments/EXP-035-grader-failing-tests-visibility.md`) reported in the same hour and agrees with the critic's main finding.

**The finding that changes the plan: part of what we called wrong fixes was never tested.**
- 15 of the 48 dev-48 tasks have hidden tests that import two test-only packages the sandbox lacks. Unless the agent's patch carries stand-ins for them, the hidden tests fail at collection whatever the fix is.
- Arms R and RH ran the v24 prompt, which has no vendoring text, and resolve 0 of those 15. Our older prompt lineage has the "Known sandbox gaps" section and resolves 1 to 2 of them; EXP-004's re-grade of EXP-003 with the packages present resolved 3.
- 11 of Arm R's 30 right-file-wrong-fix tasks are in this group, so their fix was never graded. EXP-035: 16 of the 30 grader outputs are unreadable (11 of them this cause), 10 fail only on tests the hidden patch adds, 4 fail on a test that existed (2 of those 4 may be environmental); RH replicates.
- EXP-034's pre-registration said every later arm was graded with the packages present. That is false for A25, B25, R and RH; the union of 17 mixes two grading environments. On the 33 tasks that are not gated, union minus best is 3 over six arms, not 5.
- Not known: whether the hidden grader lacks these packages, or whether the hidden repos use them. Board record (`submissions.md`): our older lineage with the vendoring section scored 0.06 to 0.13, the v24 tree without it 0.17 and 0.18, at different caps, so the board does not settle it.

**Corrections the critic required, applied here.**
1. The probability column meant P(true gain of at least 4 of 58), not P(one draw shows +4), which is about 13% under no effect.
2. F3: "at most 23 of 48" is withdrawn. 5 of the 7 subtracted passes were the agent's own scripts, and 11 of the 23 were never graded. The literature's +4.5 points is from selecting among 26 candidates, not from a verify-and-fix loop.
3. F0: the 11 call-cap tasks are arm T4's pool at 8 min. At 4.5 min the clock stops the loop at about 21 calls, so a cap of 40 does nothing there.
4. F1: the 39% gap closure is measured against a majority-vote baseline, not a random pick; on the 33 non-gated tasks the expected gain is 0.9 to 1.3.
5. F2: "no pool" ignored our compaction data (36 of 48 Arm R tasks compacted, 3 of them resolved; 12 did not, 6 resolved; confounded by task length). A tester worker that runs the check through `agent_tool` is an orchestrator form the plan had not considered.

| Change | Pool | Expected gain on dev-48 [I] | P(true gain >= 4 of 58) [I] |
|---|---|---|---|
| Port the vendoring section into the v24 prompt | the 15 gated tasks, where v24 resolves 0 | +1 to +3 if the hidden grader also lacks the packages; 0 on the board if it has them | unknown until the re-grade; the only change here with a hard zero to recover from |
| Required executed check after the last edit (in the loop, or `LoopAgent[verify, fix]`) | the graded wrong fixes: 19 of 48, of which at most 4 show a failure on an existing test | under +2 | at most 0.1 |
| Raised call cap at 8 min (arm T4) | 11 call-cap tasks | unknown until T4 runs | under 0.1 |
| Best-of-3 with an executed selector | 3 of 33 non-gated tasks over six arms | +0.9 to +1.3 | about 0.05 |
| Orchestrator, tester-worker form | unknown; the zero-GPU compaction check below | unknown | under 0.05 |

**Revised staging (replaces Stages 0 to 3 above; Stages 4 and 5 unchanged).**
- 0c, zero GPU, dispatched: EXP-036 re-grades R's and RH's patches with the two packages present on a CPU kernel (the EXP-004 pattern), then finishes EXP-035 on the tasks that become readable. EXP-034 gets the section 7 defect and the two post-hoc lines the critic asked for.
- 0d, zero GPU, after 0c: within the 11 sometimes-solved tasks, compare compaction before the first edit between resolving and failing arms (the critic's check for the orchestrator's pool).
- Reference: Arm R at 8 min, already on disk, at no GPU cost. The 4.5 min common setting is withdrawn as the comparison setting: 10 of R's 15 wrong-fix submits came after 270 s. The cost is that anything that adds wall time at 8 min has 13.8 s per task of headroom (B2) and needs its own dev-48 time profile before upload.
- Screens, one change at a time on smoke-8 against R's rows for the same ids, about 0.7 GPU-h each, in this order: the vendoring section; the required executed check; then a structure (`LoopAgent[verify, fix]`, best-of-3, tester worker) only if the check screen shows the model does not run the check when told to, or EXP-036 shows a pool for it.
- A dev-48 arm (3.5 GPU-h, user approval each) only for a change that passed its screen. The F0 arm at 4.5 min is dropped. If nothing passes, the final tree is the measured 8 min tree, not an unmeasured 4.5 min one.
- The E4B dev-48 arm (about 1 GPU-h) serves the small-model prize and is moved out of this direction; it is the user's separate decision.
- Smoke-8 kill rules, with the critic's binomials: "reached in fewer than 4 of 8" kills a true 60% rate 17% of the time, so a kill at the screen gets one re-run on a second set of 8 before it stands.
- Ship decisions stay on the as-run grade until we know whether the hidden grader has the packages.

**Stage 0c result (2026-11-05, EXP-036, c680b31; not yet critic-reviewed).** Row 1 fired: with the two packages present the baseline's patches resolve 3 of the 15 gated tasks in Arm R (9 -> 12 of 48) and 5 in RH (10 -> 15), with no other task changing. The vendoring screen is therefore next, on a cohort of gated tasks (smoke-8 holds one). The recomputed EXP-035 table is T3: the wrong fixes fail on tests the hidden patch adds or changes (19 of 27 in R, 14 of 22 in RH) and an existing test would have exposed 2 of 27 and 1 of 22. Corrected by the critic's light review (`experiments/EXP-036/critic.md`, needs-work, readings hold): five of the six patch-insensitive tasks sit in these groups and fail the same tests under GOLD, so the groups are 22 tasks in R (existing-test visible 2, hidden-only 15, collection error 5) and 17 in RH (1, 10, 4, 2 unclassified); visible is a lower bound because the grader runs only the test-patch files, and for R it lies between 2 and 7 of 22. Still T3. So the "required executed check" row of the table above has a pool of 2 to 7 of 22 tasks in R if the check is the existing tests (the table's 19 becomes 22 minus the gated ones still unresolved); it moves below the vendoring screen. Smoke-8 holds three patch-insensitive tasks, so its mechanism endpoints are read on at most 4 to 5 tasks; screens that need wrong-fix tasks get their own cohort. Six dev-48 tasks ignore the patch (C-022): the reachable ceiling is 43 of 48. Check 0d (compaction on the sometimes-solved tasks) is deferred: EXP-032 P1 parked the parallel stage the same day and the orchestrator forms are last in the order.

## Risks and kill criteria
- Stage 0 kills: F1 if union minus best is under 4 tasks; the existing-test verifier if most right-file-wrong-fix tasks end on a visible pass (F3 then needs the reproduction form or is dropped).
- A family is killed at its screen by the rule in its table row, after at most one fix and re-run.
- `ParallelAgent` with tool-calling branches can crash on compaction in ADK 1.36 (issue 7324, [M]); F1's proposers call no tools for that reason. One such crash in a screen sends that family to its sequential form.
- Time: any family whose dev-48 profile projects above 11 h at 4.5 min is not uploaded. A blank slot costs a day.
- The whole direction is killed if no family passes its screen, or if after two board draws no surviving family is within 4 tasks above F0's pooled mean; the single loop at the common setting is then the final tree.

## Cost
| Stage | What | GPU-h | Slots | When |
|---|---|---|---|---|
| 0 | lit review and EXP-034 (done), EXP-035 (zero GPU); EXP-033 E4B done at about 0.25; EXP-032 P1 running, both approved under D-004 | 0 new | 0 | Nov 5 to 6 |
| 1 | F0 at the common setting on dev-48: the reference every family is paired against, and its time profile | about 3.5 | 1 to 2 draws | week of Nov 10 |
| 1b | E4B single loop on dev-48: the small-model reference and its time profile | about 1 | 1 to 2 draws | when approved |
| 2 | smoke-8 screens at the common setting, in order: F3 (two forms), F1, and F2 only on request | about 0.7 each, at most 2.8 | 0 | week of Nov 10 |
| 3 | at most two families on dev-48, paired against F0 | about 3.5 each, at most 7 | 0 | week of Nov 17 |
| 4 | two board draws per surviving family | 0 | at most 4 | Nov 17 to 30 |
| 5 | the winning family re-screened on E4B for the small-model prize | about 0.7 | 1 to 2 | after Stage 3 |

Total about 15 GPU-h if two families survive and E4B gets its arm, against 30 per week; each dev-48 arm is approved by the user one at a time. Paper track (Nov 12): Stage 0 and the two running screens are what can be reported by then. Rule for this week, fixed now: if EXP-032 P1 and EXP-033 both reach their worst cases (1.35 and 1.3 GPU-h), arm T4 moves to next week's quota.

## Midterm check
By Nov 7: the lit synthesis, EXP-034's two readings, and the P1 and E4B screens are in; the family table above has no pending cell; the critic's `direction` review is in Options; the user approves, changes or rejects Stages 1 to 5.

## Final check
One family (possibly F0) named as the final tree by the rule: it passed its screen, projects at or under 11 h at its shipping cap, has the largest paired net on dev-48 with ties going to the cheaper tree, and two board draws that are not below F0's pooled mean. The comparison table, with every family's mechanism counts and time cost, goes to the paper track whichever way it falls.
