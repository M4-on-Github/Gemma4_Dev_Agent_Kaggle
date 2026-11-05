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
- EXP-030 becomes a two-arm screen on a new cohort of 8 cap-bound tasks: T4 (the single loop at 40 calls) against P1 (the parallel tree at the same cap), so a gain cannot be the higher cap alone; about 1.6 GPU-h, critic `prereg` required before the push. Readings carry the critic's test above, a row that one `No function call event found` error falls back to the sequential T1, and the 13.8 s rule.
- Parallel-first is kept because the user asked for parallel agents; the critic prefers sequential-first (no ParallelAgent, cannot trigger the defect, isolates the C-014 handoff link). T1 is the pre-registered fallback. The user may overrule.
- Successor design noted, not scheduled (lead, [I]): since the failure is the fix and not the location, the stage that could use idle capacity on it is a tool-free parallel step of several fix proposals from one located context (this file's original A6 wording), which makes no tool calls, so it neither spends `max_tool_calls` nor produces the function-call events the defect needs. Its open problem is selection (C-015).
- Small models: the critic says an E2B pair reads no resolves at n = 8 and suggests one E4B single-loop screen; put to the user, both small screens held.

