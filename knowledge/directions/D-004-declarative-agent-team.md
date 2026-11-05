---
id: D-004
title: A declarative agent team (role sub-agents with isolated contexts) as the final tree, built one screened handoff at a time
decision: start
status: approved
track: both
claims: [C-014, C-004, C-005, C-007, C-015]
date: 2026-11-03
---

Proposed 2026-11-03 after the user set the goal: "the shipped artefact is one model in one loop with a prompt but it is not what the final should be. it should be a sophisticated agent (possibly an agents team)". The method is the user's assume-guarantee idea: write the chain of assumptions a team design rests on, then screen each link at ~0.8 GPU-h before any upload or dev-48 arm.

## What are we trying to do?
Ship a final tree that is more than one prompt in one loop: a `SequentialAgent` root whose children are role agents (locate, edit, verify) with isolated contexts (`include_contents`, `output_key`), possibly a `LoopAgent` verifier, all declarative and all on the one fixed model. The public frontier (0.24) is a single loop; first place needs something the frontier does not do, and this is the one structural lever the harness allows that nobody at the top has shown using.

## How is it done today?
- The harness compiles `LlmAgent`, `SequentialAgent`, `ParallelAgent`, `LoopAgent` (`max_iterations`), `sub_agents`, `agent_tool` (`config_path`, `skip_summarization`), `output_key`, `include_contents`, per-agent `adapter` (`tools/submission_rules.py` lines 27-34; plan.md §4.1 finding of 2026-10-17).
- The only datum against delegation is secondhand: 12/18 -> 6/18 with same-model sub-agents [M], never run here (plan.md:152; C-014 is `hypothesis`, confidence low).
- What we did measure: under one request at a time the booted 31B server leaves 88.6% of its KV capacity idle (EXP-006); `ParallelAgent` issues genuinely concurrent requests, max 2 in flight (EXP-007 H1); a synchronous tool call in one branch stalls the sibling ~78% of the time (EXP-007 H3), and every harness tool is a sync `FunctionTool`; `max_llm_calls` is one budget shared by all branches (EXP-007 H4). Sub-agent sessions reportedly never compact [M].
- The rank-3 team's 0.24 is a single 3,240-byte prompt at 8 min / 28 calls (kg-rank3-apache-release). A paper-track post claims context resets for stuck agents lift 16% to 96% on a toy set, unsourced (digest 2026-10-28).
- Agentless (lit-2407.01489) separates locate, repair and validate as a pipeline and wins with selection by tests; its selection signals are what C-015 lacks.

## What's new in our approach?
Not the idea of roles, which is old, but the way it is bought: an assumption chain with one screen per link, each screen reading a near-deterministic outcome at n = 8, and an upload only for a tree whose links all held. The chain:

| Link | Assumption | Screen (L2, ~0.8 GPU-h each) | Reads at n = 8 because |
|---|---|---|---|
| A1 | A `SequentialAgent[locator, editor]` tree built from the v24 prompt split into two roles compiles, validates, and runs end to end in the harness | smoke-8, tree T1; endpoint: 8 of 8 produce a trace with both agents' turns and a patch attempt | breakage is all-or-none |
| A2 | A handoff with a fresh editor context costs a bounded time per task | same run; endpoint: mean and max added wall vs the EXP-028 Arm R per-task times on the same 8 ids (smoke-8 is a subset of dev-48) | a bound on 8 paired tasks, not a mean contrast |
| A3 | A fresh-context editor given a located plan loses `edit_file` arguments less often than the single loop (C-004: 37.9% of calls; 53.5% at thinking 256 vs 18.2% at 4096 suggests context length drives it) | same run; endpoint: arg-loss rate per edit call, Fisher vs Arm R on the same 8 ids (~50+ edit events) | an event rate, not a per-task outcome |
| A4 | A `LoopAgent` verifier (run tests, fix, at most 2 iterations) fits inside the remaining cap on most tasks | smoke-8, tree T2 = T1 + verifier; endpoint: fraction reaching the verifier before the cap; added wall | a bound |
| A5 | `max_tool_calls` and `max_llm_calls` re-budgeted for the team do not starve the editor (EXP-007 H4; C-007) | within T1/T2 runs; endpoint: calls-cap hits per role | a count |
| A6 | Parallel branches are free in wall-clock only when they make no tool calls (EXP-007 H3) | deferred; only if A1-A5 hold and a tool-less parallel step (two edit proposals from one plan) is designed | event timing |
| A7 | The team tree scores at least the baseline on the LB | upload (L3), two draws, read against the EXP-027 row-3 baseline of 10/58 with the ~4-task MDE | the only instrument for resolves |

## Options
- A. **Sequential role tree, one handoff at a time: T1 = locator -> editor (A1-A3, A5), then T2 = T1 + verifier loop (A4), then upload the best surviving tree (A7). Recommended.** Uses the v24 prompt text split by role so the baseline behaviour is preserved except for the structure.
- B. Parallel candidate generation with a selector (best-of-2 patches). Against: the selector has no signal without hidden tests (C-015), and tool-calling branches stall each other (EXP-007 H3). Revisit as A6 only after A.
- C. Stay single-loop (D-002 alone). Against: its ceiling is the public frontier, which four teams already share; it is the floor, not a route to first.
- Critic's dissent (2026-11-05, `experiments/EXP-030/critic.md`, commit c3f48e9, verdict **needs-work**): "The measured failure is the wrong fix in the right file (30 of 39), and a parallel locate stage targets neither that nor, net, the call budget." D-004 itself prices the gain below the 4-task MDE; the critic rates `max_tool_calls` 40 (EXP-028 T4), the A4 verify loop and repeated uploads of the best tree as better uses of two weeks. What would change its mind: on 8 cap-bound tasks the team tree's editor makes its first gold-file edit by call 10 in at least 5 of 8, with no defect crash and no added wall, while T4 does not move the same tasks. See "Critic review 2026-11-05" at the end.

## Expected score impact
Unknown in sign. The one prior datum (secondhand) says -6/18. The mechanism argument for a gain is A3 (edits lost to context length) plus A4 (a test-fix loop the single prompt cannot afford). If A3 halves the arg-loss rate and C-004's mechanism is real, the gain is of the order of the ~4-task MDE; smaller than that is unreadable and the direction would stand or fall on A1-A5, not on the LB. P(success) is low to moderate; this is the explore-quota direction.

## Risks and kill criteria
- A1 fails after one fix attempt (the harness cannot run the tree): kill.
- A2: mean added wall > 90 s on smoke-8 at the 8-min cap: the design does not fit the budget; drop to one handoff or kill.
- A3: arg-loss rate not lower (Fisher, same 8 ids): the context-isolation rationale is dead; continue only if A4 is the rationale.
- A7: two LB draws both <= baseline - 4: kill. One blank slot (timeout) under this direction: stop, measure the time profile (the one sanctioned dev-48 use) before any further upload.
- Schedule: the paper (Nov 12) is D-003's; this direction takes no paper-writer time before Nov 12 except a one-paragraph mention of the method if A1-A3 are read by then.

## Cost
Screens: 3-4 at ~0.8 GPU-h = ~3 GPU-h. Uploads: 2-4 slots, after the #12 baseline decision. Dev-48: none planned; at most one time-profile arm if a team tree is to be uploaded above 4.5 min with a longer per-task time than Arm R shows, user-approved. Days: screens can start as soon as EXP-028 is read; the main effort runs Nov 13-30.

## Midterm check
A1-A3 read from one smoke-8 run by Nov 8: the tree runs, the handoff cost is bounded, and the arg-loss rate on the same 8 ids is known either way.

## Final check
A team tree with two clean uploads at or above the baseline tree's best, its handoff cost and loss rate measured, as one of the two finals; or a documented kill with the link that failed, which is itself a paper-track result.

## Addendum 2026-11-05 (lead): where the wall-clock goes, and what it does to A6 and plan.md §6.3
The user asked on 2026-11-05 for "parallel agents ... smth that will improve the score by a lot" and whether the L4x4 is meant to be used fully. plan.md §6.3 gated the parallel track on a "free first check (no GPU)" that was never run: the real per-call latency of the tools a branch would use. Run today by the lead over the 48 traces of EXP-028 Arm R (the shipped tree), tool latency = `observation.extra.elapsed_s` minus `tool_calls[0].extra.elapsed_s`, model-turn latency = next call's `elapsed_s` minus the previous observation's. Not pre-registered and not critic-reviewed; a screener L1 should repeat it under an EXP number before anything cites it as more than [I].

| What | n | median s | p90 s | max s | share of traced wall (13,826 s) |
|---|---|---|---|---|---|
| Model turn (generation) | 1,354 | 3.56 | 25.86 | 192.04 | 94.0% |
| All tool calls | 1,353 | 0.02 | 0.10 | 241.02 | 2.9% |
| `read_file` | 420 | 0.01 | 0.02 | 0.03 | 0.0% |
| `run_command` read/search (grep, sed, cat, ls, find, git ...) | 364 | 0.02 | 0.13 | 0.72 | 0.1% |
| `edit_file` | 175 | 0.02 | 0.02 | 0.46 | 0.0% |
| `submit_patch` | 239 | 0.04 | 0.05 | 0.46 | 0.1% |
| `run_command` python | 89 | 0.15 | 0.64 | 241.02 | 1.9% |
| `run_command` pytest | 7 | 1.13 | 81.54 | 81.54 | 0.6% |

Zero steps carry more than one tool call. Readings the lead draws (interpretation, [I]):
- The run is bound by generation, one request at a time: 94% of wall is the model writing, on a server that EXP-006 measured at 88.6% idle KV capacity and 3.60x throughput at 4 concurrent requests.
- EXP-007 H3 (a sync tool stalls the sibling branch) does not bite read-only branches: no read or search call exceeded 0.72 s against a 3.56 s median model turn. It still bites a branch that runs tests or scripts (max 81.5 s and 241 s), so those belong to a stage that runs alone.
- 784 of 1,353 calls (58%) are reads and searches and 239 (18%) are `submit_patch`; 37.5% of tasks end at the 28-call cap with nothing resolved (EXP-028 §9). ~~A parallel read-only stage that hands the editor a located plan would return most of the call budget and the reading time to editing. That is a named, measured target, which §6.3 required of EXP-008.~~ **Retracted 2026-11-05 (lead's error, found by the critic):** the tool-call and turn counters are one per task shared by every agent, so three branches spend about three times the calls from the same budget and return none; the stage can buy wall-clock only. Also `submit_patch` and `get_status` do not count against `max_tool_calls`; of the 1,112 calls that do, 68-70% are reads and searches.
- Therefore A6 need not wait for A1-A5. Proposed order if the user approves: screen P1 = `SequentialAgent[ParallelAgent[3 read-only localizers], editor]` first (one smoke-8, ~0.8 GPU-h, `max_tool_calls` raised in the same run since branches share the budget, EXP-007 H4), with the sequential T1 as the fallback if P1 breaks.
- What is still excluded: parallel editors in the one shared `/workspace` (`submit_patch` diffs all of it). Whole parallel attempts in separate copies of the repo with a selector are a later desk check (can `edit_file` write outside the workspace; what selects), not part of P1.
- Constraints unchanged: EXP-028 projects 10.04 h at the 8-min cap, so the parallel stage must replace reading time, not add to it; a blank slot under this direction stops uploads until the time profile is measured.
- Expected impact stays as written above: of the order of the ~4-task MDE if the mechanism holds. Rank 1 is 6 to 7 tasks above our pooled baseline (17 vs 10.5 of 58); nothing in the logbook predicts that much from structure alone.

## Approval 2026-11-05 (user, in chat)
"since we have time, lets start with our experiments first and decide what to submit for the day later." Scope as the lead reads it: the D-004 screens in the parallel-first order of the addendum, on the 31B and on one small model (the user's steer of the same day), up to about 3.2 GPU-h. It does not cover any upload; each upload still needs its own S-NNN and approval file. The critic `direction` review was dispatched the same hour, after the approval rather than before it as this file promised; its dissent goes here when it returns and may change the branch design of later screens.

## Critic review 2026-11-05 and what the lead changed
Verdict needs-work; the screens may run, the first screen as the addendum described it could not read its own mechanism. Facts from the review (traces of EXP-028 Arm R and the vendored harness source; the critic recomputed the latency table and it holds: tools 2.9% of wall, median model turn 3.56 s):
- Budgets are shared per task and the harness ends the task at the cap, so the editor may never start; the screen must state the editor's guaranteed calls.
- File-level location is not the failure: 45 of 48 tasks name a gold file by about call 2; 30 of 39 unresolved tasks edited the right file. The 18 cap-bound tasks made their first gold-file edit at a median of call 25 against 10 for resolved tasks. Generous ceiling for a locate stage: about 5 of 48 [I].
- The ADK defect's trigger is live: token-threshold compaction fired 49 times in 36 of 48 Arm R tasks (threshold 14,336 prompt tokens; from our notebook, the scorer's setting is unverified, Q7 open). `analyze_traces.py` reports 0, a detector miss.
- The editor needs `include_contents: none`, the task text from `{problem_description}` and the reports through `output_key`.
- Headroom at 8 min is 0.46 h, 13.8 s per task; a team tree ships at 8 min only with its own dev-48 profile or a paired screen whose mean plus 2 SE stays within that.

Changes the lead made the same day:
- (Corrected the same hour: EXP-030 had already been pre-registered and pushed as the single-arm P1 on smoke-8 before the hold reached the screener; its kernel `rainm4/gemma4-exp030-p1` failed in the parameter cell on an unquoted `EXP_ID` (`SyntaxError`), ran no task and spent no GPU time. EXP-030 stays as written and is superseded.) The redesign is **EXP-032**, a two-arm screen on a new cohort of 8 cap-bound tasks: T4 (the single loop at 40 calls) against P1 (the parallel tree at the same cap), so a gain cannot be the higher cap alone; about 1.6 GPU-h, critic `prereg` required before the push. Readings carry the critic's test above, a row that one `No function call event found` error falls back to the sequential T1, and the 13.8 s rule.
- Parallel-first is kept because the user asked for parallel agents; the critic prefers sequential-first (no ParallelAgent, cannot trigger the defect, isolates the C-014 handoff link). T1 is the pre-registered fallback. The user may overrule.
- Successor design noted, not scheduled (lead, [I]): since the failure is the fix and not the location, the stage that could use idle capacity on it is a tool-free parallel step of several fix proposals from one located context (this file's original A6 wording), which makes no tool calls, so it neither spends `max_tool_calls` nor produces the function-call events the defect needs. Its open problem is selection (C-015).
- Small models: the critic says an E2B pair reads no resolves at n = 8 and suggests one E4B single-loop screen; put to the user, both small screens held.

## Addendum 2026-11-05 (lead): bounds and the measurement matrix (user request, ~13:35 UTC)

The user asked that every ability on their list be tested, plus what the lead adds, with mathematically stated maximum
bounds where they make sense. Each bound below is a formula, its inputs with a tag ([V] official or our own measured
run, [M] mirror, [I] inference), and what it rules out. Inputs come from `tools/submission_rules.py`, EXP-006, EXP-007,
EXP-028 Arm R (`experiments/EXP-028/armR/summary.jsonl` and its traces), `experiments/EXP-030/critic.md` and the
2026-11-05 scout digest. A bound is a ceiling, not an expected gain.

Symbols: N = 120 hidden tasks; c = `max_time_minutes` cap; K = `max_tool_calls`; B = parallel branches; X(B) = server
throughput multiplier at B concurrent requests; tau = wall seconds per counted call.

| # | Bound | Formula | Inputs | Value | What it rules out |
|---|---|---|---|---|---|
| B1 | Worst-case time cap | N (c + 1.0 min) <= 11.0 h | N = 120, setup 1.0 min, gate 11.0 h [V rules] | c <= 4.5 min | any cap above 4.5 min without a measured profile |
| B2 | Measured-profile headroom at 8 min | h = (H - N (w + s)/3600 - o) 3600/N | w = 297.44 s, s = 0.05 s, o = 0.12 h server start and residual, so 10.04 h projected [V EXP-028 section 9] | 13.8 s per task to our own 10.5 h ceiling; 28.8 s to the 11 h gate; 58.8 s to the 12 h limit | any stage that adds more mean wall than this while shipping at 8 min |
| B3 | Shared call budget | editor calls >= K - sum of localizer allowances | one counter per task for all agents; `submit_patch` and `get_status` free [V source] | 28 - 15 = 13; 43 - 15 = 28 | "a locate stage returns calls to the editor" (retracted above) |
| B4 | Least added wall of a pre-stage | >= k turns x turn time; a branch is never faster than one request | median turn 3.56 s, p90 25.86 s [V Arm R traces] | 5 calls + 1 report = 6 turns: >= 21 s median | a pre-stage that fits B2's 13.8 s unless it displaces editor turns |
| B5 | Concurrency and stage wall | B <= 8.74 at 32k context; stage wall for B branches of k turns ~ k t1 B / X(B) | 31B: X(4) = 3.60, X(16) = 9.85; E4B 45.63, X(4) = 3.47; E2B 67.18, X(4) = 3.21 [V EXP-006]; real overlap in ParallelAgent, wall ratio 0.206 [V EXP-007] | B = 4 does 4x the turns in 1.11x the wall of one branch | more than 8 full-context branches on 31B; any claim that parallelism shortens a single chain of dependent calls |
| B6 | Tool stall | a synchronous tool blocks siblings for its duration | stall share 78% [V EXP-007 H3]; `read_file` max 0.03 s, read/search commands max 0.72 s, pytest max 81.5 s, python max 241 s [V Arm R] | reads cost nothing; one test run can stall every sibling for over a minute | execution tools inside a parallel stage |
| B7 | Compaction margin | reads before crossing = (14,336 - P0) / g | threshold 14,336 on the latest prompt of any branch [V source]; first prompt P0 median 2,926, max 5,808; growth g per unranged read median 1,472, p90 1,991; per ranged read median 621, p90 1,427 [V Arm R traces, lead's count] | unranged: 7.7 reads at the median, 4.3 at max P0 and p90 g; ranged: 18 at the median, 6.0 at the worst | a localizer allowance above 4 unranged reads; 5 ranged reads stay under at the worst (12.9k) |
| B8 | Which cap binds | time binds when c < K tau | tau = 12.83 s per counted call, 10.18 s per turn (mean) [V Arm R] | K = 28: crossover 359 s = 6.0 min. At 8 min the call cap binds (18 of 48 tasks), at 4.5 min the clock binds (30 of 48 walls above 270 s) | reading a cap-bound result at 8 min as a time problem, or the reverse |
| B9 | Calls that fit at the safe cap | K_fit(c, B) = c X(B) / tau, parallelisable share only | c = 270 s | single loop 21 calls; ceiling 76 call-equivalents at B = 4 if every call were independent [I] | nothing yet: this is the case for parallelism, and it holds only at 4.5 min with a raised K |
| B10 | Amdahl ceiling per task | speedup <= 1 / ((1 - p) + p / X(B)) | p <= 0.69, the share of counted calls that are reads or searches [V critic]; treats them as independent, which overstates [I] | <= 2.0x at B = 4 | wall savings above half, on any design |
| B11 | Locate-stage score ceiling | tasks whose miss is location | 45 of 48 name a gold file by about call 2; 30 of 39 unresolved touch a gold file [V critic, L1b] | about 5 of 48, about 6 of 58 on the public board [I] | a locate stage as the source of a jump: the pool is the wrong fix in the right file, at most 30 of 48 |
| B12 | Selection ceiling | union of two runs' resolves minus the better run | R 9, RH 10, union 11 of 48 [V] | +1 over the better arm with a perfect selector | best-of-two editing without a selector that beats chance (C-015) |
| B13 | Board resolution | sd = sqrt(58 p (1 - p)); best of k draws | p = 0.18: sd 2.9 tasks; MDE about 4 tasks [V plan.md 5.5]; 18 draws at a true 11 or 12 of 58 give a 17 with probability 0.50 or 0.76 [V scout] | reading a move under 4 tasks as an effect; reading 0.29 as a true 17 of 58 |
| B14 | What 4.5 min costs the single loop | resolves finishing under 270 s | 8 of 9 Arm R resolves end by 212 s, one at 372 s [V] | at most 1 of 9 lost [I, n = 9] | the belief that 8 min is where the resolves are |

Reading across B2, B3, B8 and B9, written before EXP-032 and EXP-033 report: at the 8 min and 28 call setting the call
cap binds and parallelism buys nothing a single loop lacks. The setting where idle server capacity can become work is
the worst-case-safe one, 4.5 min with a raised call cap, where the clock binds and B14 says the single loop loses little.
That is an inference to be tested, not a result.

### Measurement matrix: the user's list, the endpoint that reads it, and where

| Ability | Endpoint (count or seconds) | Bound it is read against | Read in |
|---|---|---|---|
| Multi-agent communication | editor's first edit lands in a file a report named; editor re-reads a report-named file before editing; report length | B3 (calls a re-read wastes) | EXP-032 E4, E11 |
| Collaboration | pairwise agreement of the three reports on files; gold-file hit by the union against the best single report | B11 | EXP-032 |
| SWE ability | resolves (dev-48 or the board only; reported without a rate at n = 8); patch touches a gold file; first gold-file edit index; edit argument loss; malformed calls | B11, B13 | EXP-032, EXP-033, every dev-48 arm |
| Task orchestration | all three reports present when the editor starts; which role is running when a cap ends the task; crashes by class and by author; nudges | B3 | EXP-032 E1, E6, E7 |
| Parallel agents | peak requests in flight; stage wall against the sum of branch walls (realised speedup against X(B)); compactions per branch; sibling stall seconds | B5, B6, B7, B10 | EXP-032 |
| Sequential tool calling | calls per model turn (1.00 in Arm R, no multi-call step in 48 traces); seconds per call; identical repeats | B8 | every run |
| Time constraints | wall per task; which cap ends each task; projected hidden hours; seconds left under the cap | B1, B2, B8, B14 | every run; EXP-033 reads the seconds left on E4B |
| Model size (lead's addition) | the same endpoints on E4B: seconds per turn, malformed-call rate, whether thinking is honoured | B5 with E4B's X(B) | EXP-033 |
| Efficiency (lead's addition) | realised over bound for B5 and B9; resolves per GPU-hour once a dev-48 arm exists | B9, B10 | EXP-032 onward |

What a smoke-8 cannot read: any resolve rate, and B11 to B14 as effects. Those need a dev-48 arm (user approval) or the board.

