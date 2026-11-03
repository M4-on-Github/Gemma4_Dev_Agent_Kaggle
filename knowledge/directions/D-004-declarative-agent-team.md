---
id: D-004
title: A declarative agent team (role sub-agents with isolated contexts) as the final tree, built one screened handoff at a time
decision: start
status: proposed
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
- Critic's dissent: not yet obtained. The lead dispatches a `direction` review before the user approves; its answer goes here.

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
