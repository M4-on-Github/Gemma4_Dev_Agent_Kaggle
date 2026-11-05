# EXP-030 — D-004 link A6, tree P1: SequentialAgent[ParallelAgent[3 read-only localizers], editor] on the 31B, smoke-8 screen

**Date:** 2026-11-05
**Type:** smoke-8 screen, ~0.8 L4x4-h of the 30/week (estimate 0.7-1.0 h kernel wall; D-004 screen ceiling 3.2 h)
**Cohort:** smoke-8
**Ladder:** L2. L0 was done (no EXP or claim answers it; EXP-007 measured a 2-branch ParallelAgent without tools in the loop of record, never a tree with tools through `compile_submission()`). L1a and L1b could not run in this job (section 1); their numbers are carried into the screen as endpoints.
**Pre-registered:** this file is committed before the push. Sections 3-5 are written blind and are not revised.
**Serves:** C-014, C-004, C-005, C-007, C-015 via D-004 (approved by the user for screens only, 2026-11-05, no upload).
**Supersedes / relates:** EXP-007 (ParallelAgent probe), EXP-006 (vLLM concurrency), EXP-028 (Arm R is the paired reference, same 8 ids), EXP-027 (the baseline tree this one is copied from).

## 1. Why this, now

- EXP-028 Arm R (the shipped tree, v24 at 8 min / 28 calls), recomputed by the lead on 2026-11-05 [I, not pre-registered]: 94% of traced wall is model generation, one request at a time; reads and searches cost a median 0.01-0.02 s and never more than 0.72 s; reads and searches are 58% of all calls (68-70% of the counted ones, since `submit_patch` and `get_status` are not counted against `max_tool_calls`; critic D-004 review, `experiments/EXP-030/critic.md`); 37.5% of tasks end at the 28-call cap. EXP-006: the booted server leaves 88.6% of KV capacity idle and gives 3.60x throughput at 4 concurrent requests. EXP-007: `ParallelAgent` issues genuinely concurrent requests; a synchronous tool call in one branch stalls the sibling ~78% of the time; `max_llm_calls` is one budget shared by all branches.
- The claim: three read-only localizers, run at the same time, return the call budget and reading time to the editor at a bounded wall cost. Hazards found by reading the vendored source (`data/src/`), each turned into an endpoint below: (a) ADK 1.36.1 issue 7324 (`ValueError: No function call event found for function responses ids`) when token-threshold compaction (harness: interval 15, overlap 2, retention 5, token_threshold 14336) runs over out-of-order parallel-branch events; (b) `_ensure_compaction_summarizer` raising `No LlmAgent model available for event compaction summarizer` when the root is a workflow agent; (c) `LlmCallsLimitExceededError` inside a branch arriving wrapped in a TaskGroup error, which the harness's `except` does not catch; (d) every harness nudge re-runs the whole root tree (three more localizer passes); (e) the tool-call, turn and time budgets are one global counter shared by all agents.
- Compaction is live in the single loop, not hypothetical (critic D-004 review, recomputed from Arm R traces, which I did not repeat): 49 prompt-token drops in 36 of 48 Arm R tasks, each right after a turn at 14,339 tokens or more (threshold 14,336), falling to a median of 4,672; first crossing at median turn 15.5. `analyze_traces.py` reports `compactions = 0` only because it matches `compact` in event_type/author (a detector miss). So issue 7324's trigger is live for the editor, whose prompt will cross 14,336 in the same way while the session still holds the parallel stage's out-of-order events. The localizers are capped to stay under it; the editor is not and is the exposure this screen measures.
- Comparator and confound, named now: the paired reference is the single loop at 28 calls / 80 turns (Arm R), while P1 runs at 43 / 100. A difference in calls-bound outcomes may come from the higher cap, which is the EXP-028 T4 confound (T4 = single loop at 40 calls, not run). This screen reads mechanisms and bounds, not whether structure beats the cap.
- Cohort, flagged for the lead: the critic's required fix 1 asks for 8 cap-bound ids instead of smoke-8 (only fastapi_14605 of smoke-8 is cap-bound; Arm R's mean wall on smoke-8 is 202.9 s against 297 s on dev-48, so the added-wall bound E8 is read on easy tasks). The job as dispatched names smoke-8 and the protocol builds screens from `smoke-8.txt` (a subset of dev-48, free pairing); this screen therefore runs smoke-8, and a cap-bound cohort needs its own committed cohort file and a second screen.
- **L1a (fake-relay stage 0 with the P1 tree through the real `compile_submission()`): NOT RUN.** Two hard reasons. (1) `adk_submission`, `swegemma` and ADK are present only as source under `data/src/` and are not installed (`validate_submission.py --official` prints `No module named 'adk_submission'`). (2) The screener's Bash guard admits only `python tools/...`, `python -I -X utf8 tools/...` and `python -m pytest`; a probe script under `experiments/` was refused by the guard, and no workaround was attempted. The crash count therefore becomes endpoint E1 of the GPU screen (a real-model run is a stronger test of the hazard than the fake relay would have been, at 0.8 h instead of 0).
- **L1b over `runs/EXP-028-armR/` (48 traces): the script is written and NOT RUN, for reason (2).** `experiments/EXP-030/l1b_trace_mining.py` reproduces the lead's latency table (tool latency = `observation.extra.elapsed_s` minus `tool_calls[0].extra.elapsed_s`; model turn = the next call's `elapsed_s` minus the previous observation's) and computes the localization bound (did any `edit_file`/`write_file` path match a gold-patch file, split resolved/unresolved, calls and seconds before the first edit; counts only, gold text is never printed or written). It is untested code. Run: `python -I -X utf8 experiments/EXP-030/l1b_trace_mining.py --run runs/EXP-028-armR --tasks data/raw/tasks.jsonl --out experiments/EXP-030/l1b_armR.json`. Needs either `python -I -X utf8 experiments/EXP-030/` added to the screener's Bash prefixes or the experimenter to run it. Until it runs, the latency table stays the lead's [I] and the localization bound is unknown. Neither number gates this screen: the screen is a bound on whether the tree runs and what the stage costs, and a localization bound would only help read E4/E5.
- What `tools/run_forensics.py forensics runs/EXP-028-armR` gives today (run in this job): resolved 9 / patch-but-failed 33 / empty-patch 6; median first edit turn 8 (resolved), 14 (failed), 31 (empty); 4 of 48 tasks never edit. Note its "wall by tool" table attributes each whole turn, generation included, to that turn's tool, so it is not the lead's latency table.
- Paired reference on the same 8 ids (Arm R, `experiments/EXP-028/armR/summary.jsonl`; task wall s / tool calls / resolved): fastapi_14301 78.9 / 13 / yes; fastapi_14448 418.4 / 15 / no; fastapi_14605 156.2 / 29 (cap) / no; httpx_3672 282.3 / 23 / no; requests_7205 165.6 / 10 / no; requests_7309 113.0 / 9 / no; rich_3006 111.2 / 11 / yes; rich_3468 297.4 / 22 / no. Sum 1,623.0 s, mean 202.9 s, 2 of 8 resolved. Arm R `edit_file` arg-loss on these ids: 1 event in 29 `edit_file` calls (fastapi_14605).

## 2. Design

One tree, copied from `experiments/EXP-027/candidate-v24-at-8/` into `experiments/EXP-030/candidate-p1/`. The tree is the variable (a package test: structure, prompt split and budgets move together; read as one).

```
swe_agent            SequentialAgent (root, no model/tools)
  localize           ParallelAgent
    loc_a            LlmAgent, include_contents: none, output_key plan_a, tools read_file run_command get_status   angle: reported behaviour
    loc_b            same, output_key plan_b                                                                       angle: symbols (definitions, callers)
    loc_c            same, output_key plan_c                                                                       angle: existing tests and calling convention
  editor             LlmAgent, include_contents: none, tools run_command read_file edit_file write_file get_status submit_patch
```

| Choice | Value | Why |
|---|---|---|
| Localizers | role-split, not identical | three identical samples at temperature 1.0 would differ only by noise; three angles give E5 (agreement among independent routes) a meaning |
| Localizer limits | at most 5 tool calls, reads of at most 80 lines, plan of at most 120 words in a fixed `FILE / WHERE / CAUSE / CHANGE / EXACT` form; no file may be written, no test or script run | keeps every branch prompt far under the 14,336-token compaction trigger (hazard a) and the stage short |
| Localizer sampling | `configs/sampling_loc.yaml`: thinking_budget 1024, max_output_tokens 2048 (editor keeps 4096 / 8192 from `sampling.yaml`) | generation is 94% of wall and the stage wall is the slowest branch; a second variable, accepted as part of the tree |
| Localizer `include_contents` | `none`, and the issue and `{hints?}` are templated into the instruction | a re-run after a nudge then starts from the nudge, not from the editor's history; first run still sees the harness task prompt |
| Editor `include_contents` | `none`; the instruction carries `{problem_description}`, `{hints?}`, `{plan_a?}`, `{plan_b?}`, `{plan_c?}` | the root sets no branch, so a `default` editor would see all three branches' tool traffic and blow the 32k window (ADK `contents.py`). Cost, stated: the editor does not see the harness task prompt (workspace tree, budget lines, "return text-only to finish"), so the editor prompt restates the budget and the stop rule. Optional placeholders so an empty plan cannot raise `KeyError` |
| Editor prompt | the v24 prompt with: an Issue block, a Plans block, the budget line rewritten ("about 28 ... `get_status` shows the exact remaining"), section 2 replaced by "Start from the plans", "edit by tool call 12" -> "by tool call 8", and a last line "After `submit_patch`, write one short line of text and stop" | the last line is there so the editor ends the turn after submitting; an editor ending without `submit_patch` triggers a nudge that re-runs all four agents |
| `eval_config.yaml` | `max_time_minutes 8` (unchanged), `timeout_seconds 240` (unchanged), `max_tool_calls` 28 -> **43**, `max_turns` 80 -> **100** | tool calls are one shared counter: 3 x 5 localizer calls = 15, plus the 28 the editor had alone = 43. Turns are one shared counter: 3 localizers x up to 6 model turns = 18 more; 100 keeps the turn limit from binding, because a limit error raised inside a branch can arrive wrapped (hazard c) and 4 of 48 Arm R tasks already hit 80 |
| Compaction | harness setting unchanged (interval 15, overlap 2, retention 5, threshold 14336) | cannot be switched off from the submission; recorded as an exposure, not a design choice |

`diff -ru experiments/EXP-027/candidate-v24-at-8 experiments/EXP-030/candidate-p1`: `agent.yaml` replaced by the Sequential root; new `eval_config.yaml` values above; new files `configs/sampling_loc.yaml`, `prompts/{loc_a,loc_b,loc_c,editor}.md`, `sub_agents/{localize,loc_a,loc_b,loc_c,editor}.yaml`; `prompts/system.md` is the unchanged v24 prompt left over from the copy, no longer referenced, not packed (the screener has no delete command). The recorded `diff -ru` output is in the commit that adds the tree.

**Validator** (`python tools/validate_submission.py experiments/EXP-030/candidate-p1 --official --strict`): `--official` did not run (`adk_submission` not importable). Findings: 1 ERROR, the 8-minute packing gate (18.00 h worst case; identical to EXP-027 and EXP-028, overridden with `--skip-budget-gate`, a screen of 8 tasks, zip is for the notebook only and is never uploaded); 3 WARN: `timeout_seconds=240 < 300` (also on the baseline), the unreferenced `prompts/system.md` (source directory only; the packed archive re-validates with 0 errors), and one **new** WARN `sub_agents/editor.yaml: sub-agent with submit_patch can end the session from inside a sub-call`. The new warning is the design (the editor must call `submit_patch`; the validator note says the harness falls back to `git diff` without it, which would also lose the end-of-task signal). "Zero errors and zero warnings" is therefore not reachable for this tree without editing `tools/`, which this job may not do.

Pack: `python tools/pack_submission.py --src experiments/EXP-030/candidate-p1 --out dist/EXP-030-p1.zip --skip-budget-gate`: VALID (0 errors, 3 warnings: submit_patch in a sub-agent, the 8-minute gate demoted, timeout 240); 13 members (agent.yaml, eval_config.yaml, configs/sampling.yaml, configs/sampling_loc.yaml, prompts/{editor,loc_a,loc_b,loc_c}.md, sub_agents/{editor,loc_a,loc_b,loc_c,localize}.yaml). sha256 `0377116b7fbd62e92f93ef2bc57e5f0d235a6434446361c13d145bed9998a7a6` (packed from the CRLF worktree; it is a screen artifact and not claimed to reproduce from committed blobs).

Build: `tools/build_notebook.py --embed dist/EXP-030-p1.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID="EXP-030-p1" --set RUN_GOLD_CONTROL=False --out notebooks/exp030_p1/kaggle_eval_l4x4.ipynb`; `kernel-metadata.json` copied from `notebooks/exp028_armR` with only `id` and `title` changed. Cost ~0.7-1.0 L4x4-h (vLLM start ~0.1 h; Arm R took 202.9 s mean on these ids, P1 adds the localizer stage and runs three streams at once). No upload slot is spent and none may be.

## 3. Endpoints, fixed in advance

All are per-task bounds or counts over the 8 ids, read from the kernel's `traces/trace_<id>.json` (steps carry `extra.author`), `task_results.jsonl` and the kernel log. Resolves are recorded and are not an endpoint.

| # | Endpoint | Definition | User's category |
|---|---|---|---|
| E1 | Runs end to end; crash classes | per task: both a localizer-authored and an editor-authored step in the trace and a non-error finish. Crashes counted by class: (i) `No function call event found for function responses ids` (issue 7324), (ii) `No LlmAgent model available for event compaction summarizer`, (iii) any error containing `TaskGroup`, (iv) `Sandbox execution error` or other. Also: max `prompt_tokens` per author, and compaction evidence = a drop of more than 4,000 `prompt_tokens` between consecutive steps of the same author | orchestration (A1) |
| E2 | Parallel overlap | per task, from step timestamps: stage wall (first localizer step to last localizer step) divided by the sum of the three branches' own spans. 1/3 = perfect overlap, 1 = serial. Also the number of tasks where the three branches' first model call start within 5 s of each other | parallel overlap |
| E3 | Sequential tool calling and sibling stall | for every localizer `run_command`/`read_file`: latency = observation `elapsed_s` minus call `elapsed_s`; count of calls above 1 s, median and max; for each such call, whether a sibling model turn was in flight and finished late. Expected, from Arm R: none above 1 s | sequential tool calling, sibling stall |
| E4 | Communication and handoff fidelity | plans written: of 24 plan slots, how many are non-empty and carry a parseable `FILE:` line, how many say `unknown`; per task whether the editor's first `read_file`/`run_command` touches a path named in at least one plan; whether the editor's first `edit_file` path appears in at least one plan; whether any localizer `run_command` wrote (a harm check, expected 0) | handoff |
| E5 | Collaboration (agreement) | per task, the number of distinct `FILE:` values among the three plans (1 = agree, 3 = disagree) and whether the editor's edited file is the majority file. With gold paths (counts only), whether a majority file or any plan file matches a gold-patch file | collaboration |
| E6 | Budgets (A5) | per task: total counted tool calls against 43, calls by author, localizer calls per branch against the limit of 5, model turns against 100, whether the call cap was hit and which author was running when it was; whether the time cap was hit and which stage was running | budgets |
| E7 | Nudge re-runs | parallel-stage executions per task (1 + number of harness nudge messages seen as user steps; expected 1). More than 1 means the editor ended a turn without `submit_patch` | orchestration, budgets |
| E8 | Time bounds | per task wall minus Arm R wall for the same id (table in section 1): mean, max, and number of tasks over +90 s; stage-1 wall; whether any task passes 480 s | time bounds |
| E9 | Edit quality (A3) | `edit_file` arg-loss events over `edit_file` calls (analyzer count). Arm R on these ids is 1 in 29, so this is **unreadable at this screen** (no contrast is possible); reported only so a dev-48 arm can budget for it | edit quality |
| E9b | Do the plans replace the editor's reads | per task, count of editor `read_file` calls (and read-type `run_command`) on files named in a plan before the editor's first `edit_file`, and the editor's call number of its first edit. Critic's weakest assumption: the editor re-reads anyway because `edit_file` needs an exact `old_string`. Also the editor's counted calls left at its start (from `get_status` or the call count), and whether the editor hit the cap | handoff, budgets |
| E10 | SWE ability | resolves of 8, reported next to Arm R's 2 of 8; **not an endpoint** and not read (6 of 8 must flip the same way for p < 0.05) | SWE ability |

Statistics: none. n = 8 reads bounds and all-or-none events only; the paired per-task differences in E8 are listed, not tested. Power: a crash class that occurs in 1 of 8 tasks has a 64% chance of showing at least once at a true rate of 12%; zero crashes in 8 bounds the true crash rate below 31% (95% one-sided), which is why a clean screen promotes to a larger arm and not to an upload.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Rows are applied in order; the first match governs.

| # | Outcome | Reading and decision |
|---|---|---|
| 1 | The kernel does not complete, or no trace of any task has a localizer-authored step (traces cannot carry sub-agent events) | Infrastructure row. A1 unread. Read the kernel log for the error class; if the traces lack author labels while the tree ran, read E1-E8 from the log timings only and say which endpoints are lost. No promotion. A re-push needs the lead |
| 2 | All 8 tasks crash before the editor produces a step | **Kill the parallel stage as built (A1 fails).** Fall back to D-004 tree T1 (sequential locator then editor). One repair attempt is allowed only if the error class is a configuration error rather than class (i), (ii) or (iii) |
| 3 | Class (i) `No function call event found for function responses ids` in 1 or more of 8 tasks | **Fall back to D-004 tree T1** (sequential locator then editor; no `ParallelAgent`, so the issue cannot fire); the parallel claim is parked. Record the localizer and editor `prompt_tokens` peaks and whether a compaction drop (E1) preceded the error. No repair of the parallel tree |
| 3b | Class (ii) or (iii) in 1 or more of 8 tasks (and no class (i)) | One repair, then a second screen: for (iii) check the turn counter first (E6) and raise `max_turns`; for (ii) replace the ParallelAgent by a SequentialAgent of the same three localizers. Both outcomes recorded. A tree with any crash is not an upload candidate: a hidden-set crash is a blank slot |
| 4 | No crash, and the harness nudged (E7 above 1) in 6 or more of 8 tasks | The editor ends turns without submitting and each nudge re-runs the localizers. **Repair the editor ending, no promotion.** 1 to 5 of 8: reported, noted as a cost in E8 |
| 5 | No crash, and the call cap was hit while a localizer was the running author in any task | Budget repair (E6): cut localizer calls to 3 or raise `max_tool_calls`; no promotion from this run |
| 6 | No crash, and mean E8 added wall above 90 s, or more than 2 of 8 tasks above +90 s, or any task above 480 s that Arm R did not already exceed | **Kill or repair on time (A2, D-004 kill criterion).** Repair candidate: localizer thinking budget 0 and a 3-call limit. The design does not fit the 8-minute budget as built |
| 7 | No crash; fewer than 6 of 24 plans non-empty with a parseable `FILE:` that is not `unknown`, or the editor's first edit path is in a plan in fewer than 3 of 8 tasks | Handoff fails (E4): the plans are not reaching or not helping the editor. **Kill this prompt pair**; the tree can be retried once with a rewritten plan format only if E2 shows real overlap |
| 8 | No crash, mean added wall at most 90 s, E7 at most 2 tasks, E2 stage ratio at most 0.6 in 6 or more of 8 tasks, E3 no localizer tool call above 1 s in 6 or more of 8 tasks, E4 at least 18 of 24 plans usable | **Promote the claim to a dev-48 arm** (not to an upload: EXP-028 projects 10.04 h at the 8-minute cap with no margin, and any lengthening needs its measured time profile, `plan.md` §5.8). The dev-48 arm's primary endpoint: per-task wall and its p90 and the share of tasks above 480 s, with crash count at n = 48 as the safety endpoint; secondary: `edit_file` arg-loss per call against Arm R (E9) and the calls-before-first-edit count, paired by id. Resolves reported, not an endpoint |
| 9 | No crash, mean added wall at most 90 s, but E2 stage ratio above 0.6 in more than 2 of 8 tasks (branches are effectively serial) | The parallel stage buys no wall time. **Kill the "parallel" claim (A6)**; the localizer-then-editor structure is a sequential T1 question for a separate screen. Report the E3 stall counts as the cause if above zero |
| 10 | None of the above | Report the numbers; no decision. The lead decides whether a repair screen is worth 0.8 h |

Not readable from this screen, stated now: any resolve difference; edit arg-loss (E9); any effect on the LB; the L1a fake-relay crash count (the real-model run replaces it).

Prediction, written blind: the tree runs end to end in 8 of 8 tasks (60% confidence); the stage costs 30-80 s wall (50%); plan format compliance is high but the three plans disagree on the file in 2-4 of 8 tasks (E5); at least one task nudges (E7) because the editor omits its closing line (35%). Roughly even odds that row 3 fires.

## 5. What this does and does not license

**Can decide:** kill the claim (rows 2, 6, 7, 9) or promote it to one dev-48 arm with a time-profile and crash endpoint (row 8); rows 3, 4 and 5 license one repair screen of 0.8 h and nothing else.
**Cannot decide:** whether the tree resolves more tasks; whether an editor with the plans loses fewer `edit_file` arguments; whether the LB moves. Rank 1 is 6 to 7 tasks above our pooled baseline and nothing here predicts that much from structure alone (D-004 addendum).
Time-bound caveat: the 12 h headroom at 8 minutes is 10.5 - 10.04 h = 0.46 h, about 13.8 s per task (critic D-004 review). A team tree may ship at 8 minutes only with its own dev-48 time profile meeting measured mean x 120 + overhead <= 10.5 h; otherwise it ships at 4.5 minutes. The 90 s threshold in row 6 is the D-004 kill criterion for the design, not the shipping criterion; the SD of the paired wall difference is ~104 s, so the standard error on 8 tasks is ~37 s.
No upload is licensed by any row. Parallel editors in the shared `/workspace` are excluded.

## 6. Exact commands

```
python tools/validate_submission.py experiments/EXP-030/candidate-p1 --official --strict
python tools/pack_submission.py --src experiments/EXP-030/candidate-p1 --out dist/EXP-030-p1.zip --skip-budget-gate
sha256sum dist/EXP-030-p1.zip
python tools/build_notebook.py --embed dist/EXP-030-p1.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID="EXP-030-p1" --set RUN_GOLD_CONTROL=False --out notebooks/exp030_p1/kaggle_eval_l4x4.ipynb
cp notebooks/exp028_armR/kernel-metadata.json notebooks/exp030_p1/kernel-metadata.json     # then edit id and title only
kaggle kernels push -p notebooks/exp030_p1
# later, separate job:
kaggle kernels output rainm4/gemma4-exp030-p1 -p runs/EXP-030-p1/
python tools/analyze_traces.py runs/EXP-030-p1 --cap-minutes 8 --max-calls 43
python tools/run_forensics.py compare runs/EXP-028-armR runs/EXP-030-p1
python -I -X utf8 experiments/EXP-030/l1b_trace_mining.py --run runs/EXP-030-p1 --tasks data/raw/tasks.jsonl --out experiments/EXP-030/l1b_p1.json
```

## 7. Defects in this pre-registration, logged after the fact

1. The kernel was pushed before the coordinator's hold (critic direction review, cohort and design) reached the screener; see section 8. The cohort is smoke-8 against the critic's request for 8 cap-bound ids. 2. Known at writing time and not defects: L1a and L1b not run (section 1); the new `submit_patch`-in-sub-agent validator warning; the unreferenced `prompts/system.md`; E5's agreement measure and E2's stage ratio are defined on step timestamps, and if the trace schema stamps sub-agent steps differently from the single-loop traces the analysis will say so.

## 8. Built and pushed

**Pre-registration commit `341a9e1`** (this file through section 7, `candidate-p1/`, `l1b_trace_mining.py`, `notebooks/exp030_p1/`). Section 4 was committed before the push and is not revised here.

**Built 2026-11-05** with the Section 6 build command: `TASK_IDS` = the 8 smoke-8 ids, `N_TASKS = 8`, `EXP_ID = EXP-030-p1`, `RUN_GOLD_CONTROL = False`; embedded zip `dist/EXP-030-p1.zip` sha256 `0377116b7fbd62e92f93ef2bc57e5f0d235a6434446361c13d145bed9998a7a6`. The embedded zip was not decoded and re-hashed (no tool permitted to the screener for that).

**Pushed 2026-11-05 (clock time not captured), version 1:** kernel `rainm4/gemma4-exp030-p1`, status RUNNING at the check right after the push. **Ordering defect, logged here and in section 7:** the push went out before a hold from the coordinator ("do not push yet; the critic direction review changes the design") was delivered; the message reached the screener after the push command had returned. The kernel is the design of section 2, smoke-8, 43 calls / 100 turns, with the critic's cohort objection (section 1) unresolved.

Source facts checked while waiting: `submit_patch` and `get_status` are `budget_gated(count_tool_call=False)` (`data/src/swegemma/swegemma/tools/execution.py` lines 76 and 119), as the critic states. The other critic facts (shared per-task counters, compaction 49 drops in 36 of 48, root-level `default` editor sees all branches) were read in the same source earlier in this job (`context.py`, `agent_runner.py`, `contents.py`) and agree.

## Status

Kernel `rainm4/gemma4-exp030-p1` RUNNING (started by the push above). Next, a separate job once `kaggle kernels status rainm4/gemma4-exp030-p1` says COMPLETE: `kaggle kernels output rainm4/gemma4-exp030-p1 -p runs/EXP-030-p1/`, move the nested inner directory up, run the commands of section 6, apply section 4 as written. L1a and L1b are not run (Bash guard); `experiments/EXP-030/l1b_trace_mining.py` is untested.
