# EXP-032 — D-004 link A6 on the cap-bound 8: tree P1 (three read-only readers in parallel, then an editor) against T4 (the single loop at the same 43-call cap), 31B

**Date:** 2026-11-05
**Type:** smoke-8 screen, two arms on a cap-bound cohort of 8 ids (not the smoke-8 ids); estimate 2.0-2.5 L4x4-h for both arms (worst case 2.8 h), section 2 gives the arithmetic. D-004 screen ceiling 3.2 h.
**Cohort:** capbound-8 (`experiments/cohorts/capbound-8.txt`, 8 ids: fastapi_14512, fastapi_14609, fastapi_14873, fastapi_15280, rich_3063, rich_3676, rich_4070, rich_4075)
**Ladder:** L2. L0 was done (EXP-007 measured a 2-branch ParallelAgent without tools; no EXP answers a tree with tools through `compile_submission()`). L1 was not run (Bash guard, see EXP-030 section 1). L1a and L1b numbers enter as endpoints.
**Pre-registered:** this file, both trees, both zips and both notebooks are committed before any push. Sections 3-5 are written blind and are not revised; results are appended as a new section. **Gate: a critic `prereg` review is required before the kernels are pushed (combined cost above 1 GPU-h). This job pushes nothing; the push is a later job.**
**Serves:** C-014, C-004, C-005, C-007, C-015 via D-004 (approved by the user for screens only, 2026-11-05, no upload).
**Supersedes / relates:** EXP-030 (same P1 idea on smoke-8; its kernel failed in cell one, no data), `experiments/EXP-030/critic.md` (the direction review whose required fixes 1-6 this design follows), EXP-028 (Arm R and Arm RH are the references, both already run on these 8 ids), EXP-027 (baseline tree).

## 1. Why this, now

- EXP-030 (P1 on smoke-8) ran nothing: the notebook's parameter cell held an unquoted `EXP_ID` (EXP-030 section 7 item 3). Meanwhile the critic's D-004 direction review (`experiments/EXP-030/critic.md`, needs-work) changed the design: a cap-bound cohort instead of smoke-8 (which holds 1 of the 18 cap-bound ids), a named same-cap comparator for the confound, an editor with `include_contents: none` and state placeholders, localizers kept under the 14,336-token compaction trigger, and a stated number of calls the editor is guaranteed. This experiment is that redesign.
- Carried forward from EXP-030 section 1 (hazards found in the vendored source, each an endpoint below): ADK 1.36.1 issue 7324 (`ValueError: No function call event found for function responses ids`) with token-threshold compaction (interval 15, overlap 2, retention 5, threshold 14,336); `No LlmAgent model available for event compaction summarizer` when the root is a workflow agent; a `LlmCallsLimitExceededError` inside a branch arriving wrapped in a TaskGroup error; every harness nudge re-running the whole root tree; the tool-call, turn and time budgets being one global counter. Compaction is live in the single loop too (critic: 49 prompt-token drops in 36 of 48 Arm R tasks), so T4 can also show a crash class that the screen must not blame on the parallel stage.
- The measured failure on this pool: the 18 Arm R cap-bound tasks end at the 28-call cap with 0 resolved (EXP-028 T4 row; 37.5% of Arm R tasks), and 12 of them hit the cap again in Arm RH with 0 resolved (critic fix 1). The pool is stable and hard. The critic's dissent stands and is not argued away here: the measured failure is the wrong fix in the right file (30 of 39), and a locate stage targets neither that nor, net, the call budget. This screen can only show whether the mechanism works (no crash, early gold-file edit, bounded wall); it cannot show that it resolves more.
- Reference runs on the same 8 ids, already measured, no new GPU needed (task wall s / `n_calls` from `experiments/EXP-028/{armR,armRH}/summary.jsonl`; resolved 0 of 8 in both):

| id | Arm R (28 calls) | Arm RH (28 calls + recovery section) |
|---|---|---|
| fastapi_14512 | 198.2 / 29 | 418.9 / 29 (80 turns: turn exhaustion) |
| fastapi_14609 | 432.2 / 46 | 327.5 / 28 |
| fastapi_14873 | 273.2 / 29 | 236.0 / 29 |
| fastapi_15280 | 170.4 / 30 | 226.5 / 30 |
| rich_3063 | 333.9 / 28 | 477.4 / 29 |
| rich_3676 | 174.2 / 28 | 193.1 / 28 |
| rich_4070 | 305.3 / 32 | 264.5 / 28 |
| rich_4075 | 292.8 / 30 | 456.5 / 31 |
| sum, mean | 2,180.2 s, **272.5 s** | 2,600.4 s, 325.1 s |

  The Arm R column is the wall reference for reading (a). Arm R mean on dev-48 is 297 s, so this cohort is not easier than dev-48 on average by wall, but it is the cap-bound subset by construction.
- Cohort rule (also in the cohort file header): pool = the 18 Arm R cap-bound ids of critic fix 1; keep those whose `calls_cap_hit` is true in Arm RH (12: six fastapi, six rich); per repo keep the 4 whose sha256 of the file text `20261105:<id>` plus a line feed (LF only, no byte-order mark) has the smallest hex digest; seed 20261105. Result: 4 fastapi, 4 rich. Both repos are represented; the requests and httpx repos have no cap-bound ids in the pool.

## 2. Design

Two trees, same `eval_config.yaml` values (so a gain cannot be the higher cap alone), same cohort, same model, same sampling for the editor / single loop. Both arms are pushed as separate kernels by a later job.

**Arm T4** = `experiments/EXP-027/candidate-v24-at-8/` copied to `experiments/EXP-032/candidate-t4/`, with only `max_tool_calls` 28 -> 43 and `max_turns` 80 -> 100 changed. `diff -ru experiments/EXP-027/candidate-v24-at-8 experiments/EXP-032/candidate-t4` shows only `eval_config.yaml`: four comment lines added, `max_tool_calls: 28` -> `43`, `max_turns: 80` -> `100`. The prompt text still says "You have 28 tool calls and 8 minutes"; it is not touched by design (one variable), and the harness's task message and `get_status` carry the real remaining count. Read this as a stale number in T4, stated now.

**Arm P1** = `experiments/EXP-032/candidate-p1/` (13 files; `prompts/system.md` is not copied):

```
swe_agent            SequentialAgent (root, no model/tools)
  localize           ParallelAgent
    loc_a            LlmAgent, include_contents: none, output_key plan_a, tools read_file get_status   part: code site, exact current text
    loc_b            same, output_key plan_b                                                          part: tests
    loc_c            same, output_key plan_c                                                          part: callers and configuration
  editor             LlmAgent, include_contents: none, tools run_command read_file edit_file write_file get_status submit_patch
```

| Choice | Value | Why |
|---|---|---|
| Localizer roles | a partition of the reading, no execution at all: (a) the code site with its exact current text, (b) tests and usages, (c) callers and configuration | critic: roles that split the reading, not identical samples; execution-free so no sibling tool stall and no write is possible. Cost, stated: `read_file` is the only working tool, so no grep; paths come from the 3-level workspace tree in the harness task message (`agent_runner.py` lines 468-472) and from the issue text. `read_file` truncates to 150 lines or 10,000 characters (`workspace.py` line 98), so reads are ranged |
| Localizer limits | at most 5 tool calls, at most 60 lines per read, always with `start_line` and `end_line`; report (a) at most 60 words plus 25 lines of code, reports (b) and (c) at most 120 words | each localizer's prompt stays under 14,336 tokens: task message with tree and issue (the issue appears twice, in the task message and in the instruction), 5 reads of at most 60 lines about 1,000 tokens each, plus the report; worst case about 11,000. Compaction detection is an endpoint (E1), not an assumption |
| Localizer sampling | `configs/sampling_loc.yaml`: thinking_budget 1024, max_output_tokens 2048 | generation is 94% of wall (EXP-028 s9); a report cannot run long. Thoughts are excluded from `output_key` (`llm_agent.py` line 851-854) |
| Localizer `include_contents` | `none`, issue and `{hints?}` templated into the instruction | **Checked in the source (advisor's question: can a sibling's event cut a branch's own call/response pair?).** `_get_current_turn_contents` (`contents.py` lines 570-574) picks the start of the current turn with `_should_include_event_in_context` first, which applies `_is_event_belongs_to_branch` (lines 299-317, 748-763); a sibling branch's events (branch `...loc_b` against `...loc_a`) fail the prefix test and are skipped. The turn start is the harness's user message, before every localizer event, so `none` and `default` give the same contents for a localizer, and the 7324 shape is not produced by sibling interleaving through this path. Kept `none` for the nudge re-run (a re-run starts from the nudge, not from stale history) |
| Editor `include_contents` | `none`; the instruction carries `{problem_description}`, `{hints?}`, `{plan_a?}`, `{plan_b?}`, `{plan_c?}` | the root sets no branch (a SequentialAgent creates none), so a `default` editor would see all three branches' tool traffic. With `none`, `_get_current_turn_contents` starts at the last non-editor event (the last localizer to finish; ADK renders it as a "For context" user message), so the editor sees one report twice and does not see the harness task message; its prompt restates the repository location, the budget and the stop rule. Optional placeholders so an empty report cannot raise `KeyError` |
| Editor prompt | the v24 prompt plus: an Issue block, a Reports block, a budget line "at least 28 tool calls left if the readers spent their full allowance", a "Start from the reports" section (edit directly with Report A's CURRENT text as `old_string`, read only if `edit_file` says not found), "edit by tool call 8", and a last line "After `submit_patch`, write one short line of text and stop" | the last line ends the turn after submitting; an editor ending without `submit_patch` triggers a nudge that re-runs all four agents |
| `eval_config.yaml` (both arms) | `max_time_minutes 8`, `timeout_seconds 240` (unchanged), `max_tool_calls` **43**, `max_turns` **100** | one shared counter: 3 localizers x 5 counted calls = 15, plus the 28 the single loop had = 43. Turns: 3 x up to 6 = 18 more, so 100 |
| Compaction | harness setting unchanged (interval 15, overlap 2, retention 5, threshold 14,336) | cannot be switched off from the submission; an exposure for both arms |

**How many calls the editor is guaranteed when it starts.** The harness has no per-agent call cap; the counter is shared and a localizer's 5-call limit is a prompt instruction, not a harness limit. The hard guarantee is therefore **43 minus the counted calls the three localizers actually spent**. The design target is **at least 28 counted calls** (if each localizer spends its full 5 and `get_status`, which is `count_tool_call=False` in `execution.py` line 119, is free), and more if they spend fewer; at most 82 of 100 turns remain if each localizer uses 6 model turns. The actual number is endpoint E6 (calls consumed before the editor's first step), not assumed. The harness's 10-calls-remaining warning reaches whichever agent is calling at that moment (critic).

**Validator.** `python tools/validate_submission.py experiments/EXP-032/candidate-p1 --strict` (`--official` cannot run: `adk_submission` is not importable here, as in EXP-030): 1 ERROR, 2 WARN, no others. Recorded as accepted, with the reason, not worked around:
- ERROR `eval_config.yaml: worst case 120 x (8 + 1.0 setup) min = 18.00 h` exceeds the 11.0 h packing gate: the same value as EXP-027 and EXP-028 (8 min); overridden with `--skip-budget-gate` because this is a screen of 8 tasks and the zip is for the notebook only and is never uploaded. Reading (a) applies the real time rule (section 4).
- WARN `timeout_seconds=240 < 300`: also on the baseline tree (EXP-027); unchanged on purpose so the only differences are the tree and the cap.
- WARN `sub_agents/editor.yaml: sub-agent with submit_patch can end the session from inside a sub-call`: the design. The editor has to call `submit_patch`; without it the harness falls back to `git diff` and the end-of-task signal is lost. Not removable without editing `tools/`.
The T4 tree has the first two findings only. The stray-`system.md` warning of EXP-030 is gone because the file is not copied.

**Packs and builds** (both with `--skip-budget-gate --allow-warnings`, VALID with 0 errors):
- P1: `dist/EXP-032-p1.zip`, 13 members, sha256 `86c609598a876c936e2b7dcfe6e9eab7b6c137da5d9103487e38de390b8b3338`.
- T4: `dist/EXP-032-t4.zip`, 4 members (agent.yaml, eval_config.yaml, configs/sampling.yaml, prompts/system.md), sha256 `3af1479d1c591d7379e0204f8b65d3da3d48da45e39bb17eba9e03f8ea8dce69`.
- Both packed from the CRLF worktree (screen artifacts, not claimed to reproduce from committed blobs). Neither is an upload candidate.
- Notebooks: `notebooks/exp032_p1/` and `notebooks/exp032_t4/`, built with `--set EXP_ID='"EXP-032-p1"'` (and `-t4`) and `--set RUN_GOLD_CONTROL=False`, cohort `capbound-8.txt`. **The generated notebooks' parameter cells were opened and every assignment read as valid Python**: `EXP_ID = "EXP-032-p1"` (quoted), `RUN_GOLD_CONTROL = False`, `TASK_IDS = ["fastapi_14512", "fastapi_14609", "fastapi_14873", "fastapi_15280", "rich_3063", "rich_3676", "rich_4070", "rich_4075"]`, `N_TASKS = 8`. The embedded base64 zip was not decoded and re-hashed (no tool permitted). `kernel-metadata.json` copied from `notebooks/exp028_armR` with only `id` (`rainm4/gemma4-exp032-p1`, `rainm4/gemma4-exp032-t4`) and `title` changed.

**Cost.** The kernel overhead (wheelhouse install, vLLM start, decode probe) was about 0.25 h in EXP-020's smoke-8 (task time 0.55 h of a 0.8 h kernel). Cap-bound tasks run to the cap, so the smoke-8 default does not apply. T4: 8 tasks at an expected 300-400 s (Arm R 272.5 s at 28 calls, RH 325.1 s; a higher call cap lets some tasks run toward the 480 s wall) = 0.67-0.89 h, plus 0.25 h = **0.9-1.15 h**. P1: the localize stage adds an estimated 60-120 s per task (critic cites a search sub-agent at about 90 s), so 8 x 380-500 s = 0.84-1.1 h plus 0.25 h = **1.1-1.35 h**. Both arms **about 2.0-2.5 h**, worst case 8 x 510 s per arm = 1.13 h + 0.25 h, **2.8 h** for both, inside the 3.2 h D-004 screen ceiling. This is why a critic `prereg` review precedes the push.

## 3. Endpoints, fixed in advance

All are per-task bounds or counts over the 8 ids in each arm, read from `traces/trace_<id>.json` (steps carry `extra.author`), `task_results.jsonl`, `summary.jsonl` and the kernel log; Arm R and Arm RH figures come from their existing runs on the same ids. Resolves are recorded and are not an endpoint (6 of 8 must flip the same way for p < 0.05).

| # | Endpoint | Definition | User's category |
|---|---|---|---|
| E1 | Orchestration; crash classes; compaction | per task and arm: a non-error finish; in P1 both a localizer-authored and an editor-authored step. Crashes counted by class: (i) `No function call event found for function responses ids` (issue 7324), counted **separately and first**; (ii) `No LlmAgent model available for event compaction summarizer`; (iii) any error containing `TaskGroup`; (iv) `Sandbox execution error` or other. Compaction events per task and per author: a drop of more than 4,000 `prompt_tokens` between consecutive steps of the same author (the analyzer's `compactions` field is a detector miss and is not used). Max `prompt_tokens` per author, against 14,336 | orchestration |
| E2 | Parallel overlap; max in flight | per P1 task from step timestamps: stage wall (first localizer step to last) divided by the sum of the three branches' own spans (1/3 = perfect overlap, 1 = serial); the maximum number of model requests in flight at once (expected 3); tasks where the three first requests start within 5 s of each other | parallel overlap |
| E3 | Sibling tool stall | for every localizer `read_file`: latency = observation `elapsed_s` minus call `elapsed_s`; count above 1 s, median, max; for each, whether a sibling model turn was in flight and finished late. Arm R: reads cost a median 0.01-0.02 s | sequential tool calling |
| E4 | Handoff fidelity and re-reads | of 24 report slots, how many are non-empty with a parseable `FILE:` (a) or `TEST FILE:` (b) or `CALLERS:` (c), how many say `unknown`; per task whether Report A's CURRENT text is a substring of the file text at the editor's first `edit_file` `old_string` (fidelity), whether the editor's first `edit_file` succeeded without a prior `read_file` of that file (the critic's weakest assumption: the editor re-reads anyway), and the count of editor `read_file` calls on files named in a report before its first edit | handoff |
| E5 | Plan agreement and gold-file hit | per task: the number of distinct files named across Reports A, B (source file implied by the test path) and C (counts, 1 = agree, 3 = disagree); with the gold patch's file list from `data/raw/tasks.jsonl` (counts only, gold text never printed or written), whether Report A names a gold file, whether any report does, and whether the editor's edited file is a gold file | collaboration |
| E6 | Budgets: calls per role, role at a cap | per task: counted calls (excluding `submit_patch` and `get_status`) against 43, split by author; localizer calls per branch against 5; **counted calls consumed before the editor's first step (the editor's guaranteed calls = 43 minus this)**; model turns against 100; whether the call cap was hit and **which author was running when it was**; whether the time cap was hit and which stage; number of harness nudges (user steps after the first), expected 0 | budgets |
| E7 | Nudge re-runs | localize-stage executions per task (1 + nudges). More than 1 means the editor ended without `submit_patch` and the readers ran again | orchestration, budgets |
| E8 | Wall and projected hours | per task wall; paired difference from Arm R (section 1 table) and from T4: mean, SD, SE (SD / sqrt 8), max, tasks above +90 s; stage-1 wall; tasks above 480 s. Projected hours with `analyze_traces.py --cap-minutes 8 --max-calls 43` (an upper bound, since this cohort is the cap-bound subset) | time bounds |
| E9 | Edit quality | `edit_file` arg-loss events over `edit_file` calls, per arm. Arm R on this pool is 1 or fewer per task; unreadable at n = 8, reported so a dev-48 arm can budget for it | edit quality |
| E10 | Resolves | per arm, with Arm R and RH at 0 of 8; **recorded, not an endpoint, not read** | SWE ability |
| E11 | **First gold-file edit, counted call index** | per task and arm: the index (counting only counted calls, 1 = first) of the first `edit_file` or `write_file` whose `filepath` matches a file in the gold patch's file list. P1 reports two numbers: the editor-own index (counting from the editor's first call) and the global index (readers' calls included). T4's index is the single loop's. Arm R's index on the same ids is computed from `runs/EXP-028-armR` for the third column. A task has "reached the gold file by call 10" if the index is 10 or less (editor-own index for P1). No gold-file edit = not reached | the critic's mind-changer, localization |

Statistics: none. n = 8 reads bounds and all-or-none events only; paired differences are listed, not tested. Zero crashes in 8 tasks bounds the true crash rate below 31% (95% one-sided), so a clean screen promotes to a larger arm and never to an upload.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Let kP and kT be the number of the 8 tasks that reach the gold file by counted call 10 (E11) in P1 (editor-own index) and in T4. A "defect crash" is a class (i), (ii) or (iii) crash (E1) in a P1 task. Rows are applied in order; the first match governs.

| # | Outcome | Reading and what happens next |
|---|---|---|
| 0 | A kernel does not complete, or no P1 trace carries a localizer-authored step | Infrastructure row. Read the log for the error class; read what remains from log timings and say which endpoints are lost. No promotion; a re-push needs the lead |
| b | **One defect crash in any P1 task** (1 or more of 8). If T4 shows the same class in 1 or more tasks, the defect is the single loop's compaction and not the parallel stage: state that, and apply row b to class (iii) only | **Fall back to the sequential T1 tree** (a read-only locator, then the editor; no `ParallelAgent`, so the issue cannot fire). The parallel claim is parked. Record localizer and editor `prompt_tokens` peaks and whether a compaction drop (E1) preceded the error. No repair of the parallel tree |
| a | No defect crash; kP is 5 or more; the editor's calls at its start are 28 or more in at least 6 of 8 tasks (E6); mean added wall against Arm R plus 2 SE is at most +13.8 s per task (E8); and T4 does not move the same tasks (kT is 2 or fewer) | **P1 goes forward** to one dev-48 arm. Its primary endpoint: per-task wall, its p90 and the share of tasks above 480 s, with crash count at n = 48 as the safety endpoint (zero tolerated); secondary: the E11 index paired by id against Arm R, and arg-loss per `edit_file` call. Resolves reported only. No upload is licensed |
| d | As row a in every respect except the wall rule (mean added wall plus 2 SE above +13.8 s per task) | P1 **may ship only at 4.5 minutes or after its own dev-48 time profile** (measured mean x 120 + overhead at most 10.5 h; headroom at 8 min is 10.5 - 10.04 = 0.46 h = 13.8 s per task). With an SE of about 37 s on 8 tasks the +13.8 s bound cannot pass unless P1 is faster than Arm R, so a P1 that is no faster than Arm R lands here. The decision is for the lead: a dev-48 time-profile arm, or a 4.5-minute arm. Also report P1 minus T4 wall (the structure's cost at equal cap) |
| c | No defect crash; P1 meets the first-edit condition of row a (kP is 5 or more) but T4 moves the same tasks: kT is within 1 of kP, or T4's share of tasks that end on `submit_patch` before any cap (E6) is within 1 task of P1's | **The gain is the cap.** T4 goes forward alone to a dev-48 arm (`max_tool_calls` 40-43, endpoint: share of tasks ending at the call cap and projected hours; resolves reported); the parallel locate stage is dropped |
| e | Neither arm moves the tasks: kP is 4 or fewer and kT is 2 or fewer, no defect crash | **Reading and cap are both ruled out as the limit on this pool** for these 8 ids: the failures are not a localization or a call-budget problem the tested trees fix. That leaves D-004's other links (the critic's A4 verify loop for the wrong-fix-in-the-right-file failure, 30 of 39), repeated uploads of the best tree, and the sequential T1 question; the parallel stage is parked and T4 is not pursued unless row c's T4 condition on `submit_patch` before the cap held |
| f | None of the above (for example kP of 3 to 4 with kT of 3, or the editor's calls at start below 28 in 3 or more tasks) | Report the numbers; no decision. The lead decides whether a repair screen of about 1.2 h is worth it; if the editor's start calls are the cause, the repair is a 3-call localizer allowance |

Not readable from this screen, stated now: any resolve difference; edit arg-loss (E9); any effect on the leaderboard; plan agreement as a predictor of anything beyond the E11 index.

Prediction, written blind: P1 runs end to end in 7 or 8 of 8 tasks (60%); the localize stage costs 60-120 s wall (50%); Report A names a gold file in about half the tasks, the lower bound being the loss of grep; at least one task nudges (E7) (35%); kT is 2 or fewer because T4 differs from Arm R only in its cap (70%). Row d or f is the likeliest outcome. Even odds that row b fires.

## 5. What this does and does not license

**Can decide:** kill the parallel stage (rows b, e), promote P1 to one dev-48 arm with a time-profile and crash endpoint (row a) or to a 4.5-minute or time-profile question (row d), or promote T4 alone to a dev-48 arm with the call-cap-ending endpoint (row c). Row f licenses one repair screen and nothing else. **Cannot decide:** whether either tree resolves more tasks; whether the LB moves; whether the result holds off this pool. Rank 1 is 6 to 7 tasks above our pooled baseline (21/116) and nothing here predicts that from structure alone.
The cohort is the cap-bound subset by construction, so kP and kT are not rates on dev-48 and the wall of both arms is not a dev-48 projection. No upload is licensed by any row. Parallel editors in the shared `/workspace` are excluded.

## 6. Exact commands

```
python tools/validate_submission.py experiments/EXP-032/candidate-p1 --strict
python tools/validate_submission.py experiments/EXP-032/candidate-t4 --strict
python tools/pack_submission.py --src experiments/EXP-032/candidate-p1 --out dist/EXP-032-p1.zip --skip-budget-gate --allow-warnings
python tools/pack_submission.py --src experiments/EXP-032/candidate-t4 --out dist/EXP-032-t4.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed dist/EXP-032-p1.zip --username rainm4 --cohort experiments/cohorts/capbound-8.txt --set EXP_ID='"EXP-032-p1"' --set RUN_GOLD_CONTROL=False --out notebooks/exp032_p1/kaggle_eval_l4x4.ipynb
python tools/build_notebook.py --embed dist/EXP-032-t4.zip --username rainm4 --cohort experiments/cohorts/capbound-8.txt --set EXP_ID='"EXP-032-t4"' --set RUN_GOLD_CONTROL=False --out notebooks/exp032_t4/kaggle_eval_l4x4.ipynb
# later, a separate job after the critic prereg review (kernel push of each notebook directory, p1 and t4):
#   kaggle kernels push -p notebooks/exp032_p1      and      -p notebooks/exp032_t4
# later still, after kaggle kernels status says COMPLETE for each:
kaggle kernels output rainm4/gemma4-exp032-p1 -p runs/EXP-032-p1/
kaggle kernels output rainm4/gemma4-exp032-t4 -p runs/EXP-032-t4/
python tools/analyze_traces.py runs/EXP-032-p1 --cap-minutes 8 --max-calls 43
python tools/analyze_traces.py runs/EXP-032-t4 --cap-minutes 8 --max-calls 43
python tools/run_forensics.py compare runs/EXP-028-armR runs/EXP-032-p1
python tools/run_forensics.py compare runs/EXP-028-armR runs/EXP-032-t4
python -I -X utf8 experiments/EXP-030/l1b_trace_mining.py --run runs/EXP-032-p1 --tasks data/raw/tasks.jsonl --out experiments/EXP-032/l1b_p1.json   # untested script; E11 and E3 need it or an equivalent
```

## 7. Defects in this pre-registration, logged at writing time

1. The E11 index, the E4 fidelity test and the E2 in-flight count are defined on trace fields (`extra.author`, step timestamps, `tool_calls[].arguments.filepath`) that have not been seen for a ParallelAgent run. If the trace schema stamps sub-agent steps differently from the single-loop traces, the analysis will say so and name the endpoints lost. `experiments/EXP-030/l1b_trace_mining.py` is untested and does not yet compute E11 for the editor-own index.
2. Reading rows c and e use "within 1 task" and "2 or fewer" thresholds on n = 8, chosen as a gap that n = 8 cannot test; they are decision bounds, not significance claims.
3. T4 shares P1's budget by cap only. T4's prompt still says 28 calls, so a T4 that behaves as Arm R below 28 calls and idles above it would understate what a 43-call prompt could do. This is deliberate (one variable) and is why row c sends T4 forward only to a dev-48 arm that can see the effect.
4. A stray directory `experiments/EXP-032-t4-tmp/` (an untracked copy of the baseline tree made by a mistyped copy command) exists in the worktree because the screener has no delete or move command. It is not committed and is not part of this experiment; the lead may remove it.
5. The generated notebooks start with `RUN_PHASE0_CHECKS = True` and `MEASURE_DECODE_SPEED = True` as in EXP-028; not changed.

## 8. Built

Built 2026-11-05 with the section 6 commands; shas in section 2. Committed by pathspec before any push. **No kernel has been pushed.** Next, a separate job, only after the critic `prereg` review returns: push `notebooks/exp032_p1` and `notebooks/exp032_t4` (or the lead's chosen order), then record the kernel ids and a `## Status` line.

## Status

Pre-registered, built, committed, not pushed. Waiting for the critic `prereg` review (combined cost 2.0-2.5 L4x4-h, above 1 GPU-h). Kernels would be `rainm4/gemma4-exp032-p1` and `rainm4/gemma4-exp032-t4`.
