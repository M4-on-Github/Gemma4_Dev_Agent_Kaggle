# R-016: 31B solver run as an agent_tool, outside the scorer's compaction (pre-registration)

Written 2026-11-21 (about 16:30Z), before any job of this round is submitted. Counts only; no trace content.
Tweak id **T-31b-014**. The `tweaks.md` row is added with the results. The idea comes from an independent review
of the logbook (2026-11-21, focus item 2). The source facts below were re-read by the operator before writing.

## Why

- The scorer summarizes the session once a prompt reaches 14,336 tokens. It keeps the last 5 events, and older tool
  outputs leave the model's view. The summary is one extra model call that is not in the trace but counts against
  the task clock. A submission cannot set this: it is an `App` argument
  (`.claude/skills/harness-stack/reference/compaction.md`).
- **31B, from the review's recount over the six base draws on cdev2-79 (474 task-draws).**
  - Compaction happens in 314 of the 474 task-draws.
  - 72 of those 314 resolve, against 100 of the 160 without; trajectory length confounds this.
  - The summarizer's model time is 26.4 s per task-draw, 7.4% of the 354.6 s mean wall.
  - R-003 counted 56-82 repeated reads or greps after the first compaction per 56-task draw.
- The 31B is wall-bound (10.04 h projected, gate 11.0 h). Time caps are 15-21 of 79 in every base draw below.
- No earlier arm tested context management directly:
  - R-003 nothoughts removed reasoning, a different lever.
  - T-31b-011 had low compliance.
  - E4B pin-issue (R-007) kept compaction and pinned the issue.

## Facts relied on (source read 2026-11-21)

- **No compaction inside an agent_tool.**
  - `google_adk 1.36.1` `tools/agent_tool.py` runs the child in `Runner(app_name=..., agent=...)` with no `app`.
  - `runners.py:1429` passes `events_compaction_config=None` when there is no app.
  - `flows/llm_flows/compaction.py:39-41` returns when that config is None.
  - The child session copies the parent state (keys not starting `_adk`). Plugins are forwarded
    (`include_plugins` defaults to true), so the trace recorder and retry plugin apply. R-014 saw inner steps in the
    trace with `extra.author` set to the helper.
- **The issue reaches the child.**
  - The harness puts the issue in state as `problem_description`, and `hints` when present
    (`swegemma agent_runner.py:676-681`). ADK fills `{name}` in a string instruction from state
    (`instructions.py:55-56`), and `{name?}` is optional (`instructions_utils.py:84-86`).
  - The trace records the unfilled template (`agent_runner.py:731` reads `agent.instruction`). In the R-007 pin-issue
    smoke, first-call prompts were 15 to 3,062 tokens longer than base for the same tasks, so the issue was sent.
- **Clocks and caps.**
  - The 8-minute cap is `asyncio.timeout` around the whole run, child included.
  - Any exception (an HTTP 400 for context length included) ends the run, and the harness takes the on-disk
    `git diff` as the patch when none was submitted (`agent_runner.py:1026-1078`).
  - Tools refuse with `BudgetExceeded` once 28 tool calls are used (`context.py:470-480`), and the counter is shared
    with the child (R-014).
  - The loop that ends the task at the call cap runs only on root events, so inside the child the model keeps
    getting refusals until it stops or the clock ends.
  - `submit_patch` sets the shared `patch_submitted`, and the root loop then ends at its next event.
- **What the child does not see.** Its first user message is the root's request, not the harness task prompt. It
  loses the repository name, the 3-level workspace tree, the budget and environment lines and the harness's
  numbered instructions 0-5. The solver instruction restores the issue, the hints and those rules in words, without
  numbers; our prompt already states the budget. The tree is not restored, since the root would have to decode it.
- **Context window.** The cluster serves `max_model_len=32768` (`tools/cluster_eval.py:212`), and the solver keeps
  `max_output_tokens: 8192`.
  - A request whose prompt passes about 24,576 tokens can fail (HTTP 400) and end the task with its on-disk diff.
  - The review estimates 75 of the 474 base task-draws would pass that uncompacted, with 5 of them resolved.

## Change

| ID | Arm | Tree | Change |
|---|---|---|---|
| T-31b-014 | nocompact | `trees/31b-r016-nocompact` | Single agent → root `swe_agent` with tools `submit_patch` and `agent_tool` `solve` (`skip_summarization: true`); `solve` is the base agent |

- `sub_agents/solver.yaml`: the base model, tools and `configs/sampling.yaml`, all unchanged. Its instruction
  `prompts/solver.md` is the base `prompts/system.md` byte for byte (first 3,162 bytes; checked) plus one section,
  "## The task" (3,915 bytes in all). The section holds the issue through `{problem_description}`, then
  `{hints?}`, plus five lines restoring the harness rules described above.
- Root: `prompts/root.md` (289 bytes). It calls `solve` once, then `submit_patch` if the session is still open, then
  one sentence. Its own `configs/sampling_root.yaml` uses `max_output_tokens: 1024` and `thinking_budget: 256`,
  because the root never reasons about the task.
- `eval_config.yaml` is identical to base.
- Validator (`--official`):
  - `adk_submission.validate_directory` OK.
  - The two cluster-only errors every tree here has (8-minute cap gate, compile_submission signature).
  - One error from our own lint, "root agent has no way to modify files", because it does not follow `agent_tool`.
    That rule needs a fix before any Kaggle pack; it does not affect a cluster run.
  - A warning that a sub-agent holds `submit_patch`, which is intended.

## Runs

| Arm | Tree | Cohort | Draws | Run ids |
|---|---|---|---|---|
| smoke (not read) | `trees/31b-r016-nocompact` | `runs/_cohorts/smoke-te.txt` (2 tasks), concurrency 2 | 1 | `S-016-31b-nocompact-smoke` |
| nocompact | `trees/31b-r016-nocompact` | `cohorts/cdev2-79.txt` | 6 | `R-016-31b-nocompact-d1..d6` |

- Ada, 1 GPU, 4 CPUs, 64G; `--concurrency 4 --py313 env/py313-scorer/bin/python3.13 --task-envs env/taskenvs`, as
  R-015.
- **Control: the six existing base draws on cdev2-79.**
  - The draws are R-008 d1/d2, R-011 d3/d4, R-014 d5 and R-015 d6, with no new base draws.
  - Values read 2026-11-21:
    - resolved 28, 27, 30, 28, 32, 27 (mean 28.7);
    - mean task wall 352.6, 367.7, 368.5, 355.1, 348.6, 335.1 s (mean 354.6);
    - empty patches 13, 17, 17, 17, 13, 16;
    - time caps 19, 19, 21, 17, 15, 15.
  - R-015 d6 ran today on the same flags. Drift across the earlier dates is a stated limit.
- **Order.** Smoke, then d1. After the draw-1 gate, d2-d6 are submitted at once.
- **Cost.** About 0.3 GPU-h for the smoke and about 2.1 Ada GPU-h per draw, so about 13 GPU-h for 6 draws. A kill at
  draw 1 costs about 2.4.
- Projection, unchanged from R-014/R-015: projected Kaggle time = 10.04 h × (arm mean task wall / 361 s).

## Readings (written before any job runs)

1. **Smoke gate.** Every condition must hold:
   - both rows SUCCESS, no engine error;
   - both traces show `solve` steps (`extra.author`) that make the tool calls;
   - the root makes at most 3 model calls per task;
   - no solver prompt-token drop of over 40% from above 8,000 (no compaction).

   A failed smoke is fixed once, the fix logged here, and re-run. The smoke also records:
   - whether the agent_tool call counts as a tool call;
   - whether the first solver call's prompt holds the issue (compared with base first-call tokens for the same task).
2. **Draw-1 kill gates** (d1 alone; any one kills the arm):
   - resolved ≤ 24 (base mean − 4; base range 27-32);
   - mean task wall above 368.5 s, which is slower than every base draw and is the endpoint this arm exists for;
   - empty patches ≥ 23 (base maximum + 6);
   - time caps ≥ 27 (base maximum + 6);
   - the mechanism fails: compaction (reading 1's test) in more than 2 of 79 task-draws.
3. **Decision, d1-d6 against the six base draws.**
   - Statistics: wall ratio = arm mean task wall / 354.6 s. Solves: paired over the 79 tasks, using each task's
     resolve rate over its draws per arm. The statistic is mean(arm − base) × 79 in solves per draw, with a 90%
     bootstrap CI over tasks (10,000 resamples, seed 0).
   - **Helps:** CI lower bound above 0 and projected ≤ 11.0 h. It becomes the 31B frozen-config candidate.
   - **Kept for time:** wall ratio ≤ 0.97, point estimate ≥ −0.5 and CI lower bound above −2.0. It becomes the 31B
     frozen-config candidate and gives back time for an adapter's decode cost.
   - **Dropped:** anything else.
4. **Mechanism (reported, not gates).** For each draw:
   - compactions;
   - context-length errors (`Sandbox execution error` rows), and how many of those are resolved;
   - empty patches;
   - time caps;
   - model calls after the 28th tool call;
   - root model time;
   - calls before the first edit;
   - identical repeated calls per task.
   Each is reported beside the base counts.

## What each outcome means

- Helps or kept for time: the frozen 31B config uses the solver layout.
  - Every resolved run becomes an uncut training row, so the 31B adapter's data is rebuilt from these traces.
  - The same arm is run for the E4B (295 of 632 E4B task-draws compact) as the next round.
- Wall not lower: the summarizer's time is not the cost it looked like, or overflow and the lost workspace tree eat
  the saving. The next variant would be a lower `max_output_tokens` for the solver, but only if the overflow count
  explains the miss.
- Resolves lower: losing the task prompt and tree, or the longer context, hurts more than summaries do.

**Blind guess (not a reading).**
- Passes its draw-1 gates: 55%.
- Kept for time or helps after 6 draws: 30%.
- Helps: 10%.

## Deviation, queueing (2026-11-21, recorded before the smoke has a result)

The user approved queueing every gated job at once for the weekend (2026-11-21).
- d1-d6 are submitted now with `afterok` on the smoke (job 59992), instead of d2-d6 after the draw-1 gate.
- If the smoke gate (reading 1) fails, all six are cancelled. If d1 fails a draw-1 kill gate (reading 2), d2-d6 are
  cancelled or stopped, their rows are not read, and the arm is dropped.
- No bar, reading or comparison set changes. The cost of a kill rises by whatever d2-d6 ran in parallel with d1.

## Results

### Smoke (`S-016-31b-nocompact-smoke`, job 59992, pleiades-0-17, 10 min 20 s)

**Reading 1 passes.**
- 2 of 2 SUCCESS, no engine error.
- Agent steps by author: 13 `solve` and 1 `swe_agent`, then 23 `solve` and 1 `swe_agent`.
- Every repository tool call comes from `solve`. The root makes 1 model call per task; its only tool call is
  `solve`, and its session ends after the child's `submit_patch`.
- No compaction: no solver prompt-token drop. The largest solver prompts are 6,396 and 22,378 tokens, both under
  24,576.
- 1 resolved, 0 empty patches, 0 time caps. Task walls 97 s and 424 s. One submit_patch per task.

Recorded:
- **The `solve` call does not count as a tool call.** Reported tool calls are 11 and 21, against 12 and 22 calls made
  by `solve` in the traces. Base traces show the same gap of one or more (65 of 79 rows in R-015 base d6), so the
  solver gets the full 28.
- **The issue reaches the solver.** `{problem_description}` is not optional, so a missing state key would raise a
  KeyError and end the run. Both runs completed. The first solver prompt is 1,929 and 1,974 tokens, against 2,929 and
  2,922 for base first calls on the same tasks. The roughly 1,000 tokens missing are the harness task prompt's tree
  and rule lines; the issues are 739 and 815 characters.
- **Not in the design: the root writes more than the fixed request.** Its `solve` argument is 194 and 508
  characters, against about 50 for the request alone. This is root decode time; reported under reading 4 as root
  model time.

d1 (job 59994) started at once on `afterok`. d2 (job 60002) is running; d3-d6 are queued.
