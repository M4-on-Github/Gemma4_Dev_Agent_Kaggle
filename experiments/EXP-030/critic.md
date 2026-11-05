---
id: D-004-critic
exp: D-004
tier: direction
verdict: needs-work
verified: regenerated
date: 2026-11-05
---

# D-004 direction review (not a review of EXP-030)

Filed here only because the critic write guard admits no path but `experiments/EXP-*/critic.md`. It reviews `knowledge/directions/D-004-declarative-agent-team.md` including the 2026-11-05 addendum and approval. A later review of the EXP-030 screen itself must not treat this file as a prior EXP-030 review under the re-review rule; append it as its own section with its own tier.

## Verdict
**needs-work.** The screens may run, but the first one as described (smoke-8, P1 with three localizers, `max_tool_calls` "raised") cannot read its own mechanism and walks into two measured hazards. Four corrections to the addendum, all from Arm R traces or the vendored harness source:
1. `submit_patch` and `get_status` are `budget_gated(count_tool_call=False)` (`swegemma/tools/execution.py`), so they do not count against `max_tool_calls`. Of 1,112 counted calls, reads and searches are 68-70%, not 58%.
2. `tool_calls_used` and `llm_calls_used` are one counter per task on one `SweContext`. Every agent's tool call increments it, and `agent_runner` ends the loop when it reaches the cap. A three-branch read stage spends about 3x from the shared budget and returns nothing to it. The ADK-side `max_llm_calls` counter also looks shared: `ParallelAgent` uses `model_copy`, which copies the private cost manager by reference [I].
3. Token-threshold compaction already fires in the single loop: 49 prompt-token drops in 36 of 48 Arm R tasks, every one right after a turn at 14,339 tokens or more (threshold 14,336), falling to a median of 4,672. The first crossing comes at a median of turn 15.5 (quartiles 11.75 and 20). `analyze_traces.py` reports `compactions = 0`, which is a detector miss (it only matches `compact` in event_type or author). Issue 7324's named trigger is therefore live in our runs, not hypothetical.
4. A root-level editor with `include_contents: default` sees every branch's events, because `_is_event_belongs_to_branch(None, e)` is True. That puts three localizer histories in its prompt. The only shape that fits is `include_contents: none`, with `{problem_description}` taken from session state (the harness sets it) and the reports passed through `output_key` templating. The harness App sets no `resumability_config`, so a continuation nudge re-runs the whole `SequentialAgent`, localizers included [I from source].

## Answers to the dispatch
1. **Latency table holds.** I recomputed it with `python -I -X utf8` over the 48 traces. Traced wall 13,826.5 s, tool time 400.8 s = 2.9%, median model turn 3.56 s, 0 steps with more than one call, `read_file` max 0.03 s, read/search `run_command` max 0.22 s with my first-token classifier (0.72 s with the lead's), pytest max 81.5 s, python max 241 s. Generation is 95.7% with my chaining and 94.0% in the lead's table; the gap comes only from my counting the 48 agent turns that make no tool call. So H3 does not bite reads. The catch is that "read-only" can be enforced only through the prompt: `run_command` is a single tool, and Arm R made 139 python calls (89 by the lead's classifier).
2. **It mostly buys time and calls. File-level location is not the failure.** 45 of 48 tasks name a gold file in a command (median call 2). 38 of 48 patches touch a gold file. 30 of the 39 unresolved tasks edited the right file and still failed. Among the 18 cap-bound tasks, 15 named the gold file early, but their first gold-file edit came at a median of call 25, against 10 for the resolved tasks. That gap fits either function-level search or slow understanding; function-level location is unmeasured. Upper bound: the 18 cap-bound tasks, 0 resolved. Giving them the non-cap resolve rate (9/30) yields about 5 of 48, a generous ceiling [I]. On time, a perfectly partitioned three-way stage saves at most about 2/3 of the pre-edit time (median 137 s, quartiles 49 and 196 s). Identical localizers save about 0. The direct single-variable test of "calls bind" is EXP-028 T4, which raises `max_tool_calls` from 28 to 40.
3. **Role-split is the better first screen.** Identical localizers repeat the same reading: they cost 3x the shared calls, the stage takes as long as the slowest of the three, and all they buy is a vote on a location that is already right in 45 of 48 tasks. Roles must partition the reading with no execution: (a) the code site with its exact current text, (b) tests and usages, (c) callers and config. A "reproduce the failing behaviour" role invites the 241 s python calls. The merge problem is real. The editor has no way to settle conflicting reports, and report length is bounded only by a per-agent `generate_content_config.max_output_tokens`, which the rules module admits. Score each report against the gold files offline after the run, at zero GPU.
4. **Sequential-first wastes less.** T1 contains no `ParallelAgent`, so it cannot trigger 7324, and it isolates the handoff, which is the link with the adverse prior (C-014). Parallel-first saves a screen only if both the handoff and the parallel stage hold. The defect's blast radius is one task: `agent_runner` catches the exception and harvests the on-disk diff, which is empty during the locate stage [I from source].
5. **Shared budgets.** The first screen has to fix three things:
   - set `max_tool_calls` = 28 + the localizer allowance, and `max_turns` above 80 by the same logic;
   - write down how many calls the editor is guaranteed when it starts;
   - name the comparator: the single loop at that same cap. Otherwise a gain may come from the higher cap, which is the T4 confound.

   Note that the ≤10-remaining warning, which tells the agent to submit, reaches whichever agent is calling at that moment. Measure per-role calls and turns, the editor's calls left at start, editor cap hits, and nudge re-runs.
6. **12 h rule.** Headroom is 10.5 − 10.04 h = 0.46 h, or 13.8 s per task. The SD of the paired RH−R wall difference is 103.5 s, so the standard error is 37 s on smoke-8 and 15 s on dev-48. A team tree may ship at 8 min only with its own dev-48 time profile meeting measured mean × 120 + overhead ≤ 10.5 h, or with a paired screen whose mean + 2 SE added wall is ≤ +13.8 s per task (in practice about 60 s per task faster than Arm R). Otherwise it ships at 4.5 min. Smoke-8 is also easy: Arm R mean wall is 203 s on those ids against 297 s on dev-48.
7. **The E2B pair reads nothing about resolves.** At about 4 of 58, a run of 8 tasks expects about 0.5 resolves. A small-model smoke-8 can read malformed calls, empty patches, submit rate, arg loss, wall time and compactions. The prize gives E2B no credit over E4B. My suggestion is one E4B single-loop smoke-8 for mechanics, then a dev-48 at 4.5 min as the resolve instrument, and parallel only after the 31B screen shows a mechanism. Only the user can change the "smallest" steer, so the lead should put this to the user.
8. **Dissent.** The measured failure is the wrong fix in the right file (30 of 39), and a parallel locate stage targets neither that nor, net, the call budget. D-004 itself prices the gain below the 4-task MDE. Two weeks have better uses: T4, the A4 verify loop, and repeated uploads of the best tree, since the LB keeps the best draw and rank 1 is consistent with the best of 18 draws (digest 2026-11-05). What would change my mind: on the cap-bound 8, the team tree's editor makes its first gold-file edit by call 10 in at least 5 of 8 tasks, with 0 occurrences of `No function call event found` and paired added wall ≤ 0, while T4 at 40 calls does not move the same tasks.

## Skill items
- **Weakest assumption:** that the localizer reports replace the editor's own reads. `edit_file` needs an exact `old_string`, so the editor may re-read anyway. Test it in the screen by counting editor `read_file` calls on report-named files before its first edit.
- **Evidence the other way:** no public bundle at 0.22 or above is more than one LlmAgent (digest 2026-11-05). A participant reports a search subagent taking about 90 s for 3,000 tokens [M]. The community workaround for 7324 is tool-free sub-agents [M] (kg-743063).
- **What a top-5 team does:** a single loop, budget tweaks (v25 raises calls to 40), and many uploads to harvest the best draw.
- **Options not considered:**
  - (a) T4 at 40 calls on the cap-bound 8, as the precondition test;
  - (b) a CPU fake-relay plumbing run of the P1 tree, as in EXP-007 Stage 0, to check the shared counters, the editor's view, templating and the nudge re-run before any GPU;
  - (c) tool-free parallel reviewers after the edit. They make no function calls, so they cannot trigger 7324, and they target the right-file, wrong-fix failure.

## Required fixes (for the EXP-030 design, before push)
1. Cohort: 8 tasks drawn from the 18 Arm R cap-bound ids: fastapi_14262, 14512, 14583, 14605, 14609, 14873, 14953, 14962, 15280, 15661, 15800, rich_3061, 3063, 3105, 3676, 3935, 4070, 4075. In RH, 12 of these hit the cap again and 0 resolved, so they form a stable pool. The current smoke-8 contains only 1 of them (fastapi_14605). `guard_push.py` accepts any `experiments/cohorts/<name>.txt`.
2. Budgets as in answer 5, with the comparator named.
3. Editor `include_contents: none` + `{problem_description}` + `output_key` reports; per-agent `max_output_tokens` on localizers.
4. Keep each localizer under 14,336 prompt tokens (ranged reads, a stated call allowance). Detect compaction from prompt-token drops, not from the `compactions` field.
5. Readings rows: any `No function call event found` in 1 or more of 8 tasks means falling back to T1. Add rows for nudge re-runs of the localizers and for editor reads before the first edit.
