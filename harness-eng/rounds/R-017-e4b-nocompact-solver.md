# R-017: E4B solver run as an agent_tool, outside the scorer's compaction (pre-registration)

Written 2026-11-21 (about 19:30Z), before any job of this round is submitted. Counts only; no trace content.
Tweak id **T-e4b-017**. The `tweaks.md` row is added with the results. This is R-016's layout (T-31b-014) on the E4B,
queued now on the user's instruction to queue everything before analysis (2026-11-21), not after R-016's results.

## Why

- The scorer summarizes a session once a prompt reaches 14,336 tokens, and older tool outputs leave the model's
  view (`.claude/skills/harness-stack/reference/compaction.md`). A submission cannot change that setting.
- **E4B, R-011-e4b-base-tu5 d1-d8 on cdev2-79 (632 task-draws), counted 2026-11-21 with `tools/round_counts.py`.**
  - Compaction happens in 31-37 of 79 task-draws per draw (271 of 632).
  - Resolved 8, 5, 7, 8, 6, 7, 6, 9 (mean 7.0).
- The E4B is not wall-bound, so the question here is solves only. R-016 asks the same question for the 31B, where
  wall time is the main endpoint.

## Facts relied on

- These are the same as R-016's "Facts relied on" (source read 2026-11-21). They are re-checked by R-016's smoke
  (job 59992), which passed:
  - The solver's prompts show no compaction.
  - The issue reaches the solver through `{problem_description}`.
  - The `solve` call does not count against the 28-call cap.
- **Context window.** The cluster serves both models at `max_model_len=32768` (`tools/cluster_eval.py:212`). The
  solver keeps `max_output_tokens: 8192`, so a prompt past about 24,576 tokens can fail (HTTP 400). The task then
  ends and the harness keeps its on-disk diff.
  - From R-011, about 51 of 632 E4B task-draws would pass that size without compaction. This is a rough estimate:
    the sum of the positive prompt-token increments per task.

## Change

| ID | Arm | Tree | Change |
|---|---|---|---|
| T-e4b-017 | nocompact | `trees/e4b-r017-nocompact` | Single agent → root `swe_agent` with tools `submit_patch` and `agent_tool` `solve` (`skip_summarization: true`); `solve` is the E4B base agent |

- The tree is `trees/31b-r016-nocompact` with the model set to `gemma-4-e4b-it-qat-w4a16-ct` in both agents.
  - `configs/sampling.yaml` and `eval_config.yaml` come from `trees/e4b-base`.
  - `prompts/root.md`, `prompts/solver.md` and `configs/sampling_root.yaml` are R-016's, unchanged. The E4B base
    prompt is byte-identical to the 31B base prompt, so `solver.md` is the E4B base prompt plus R-016's task
    section (prefix checked with `cmp`).
- Validator (`--official`, in `env/harness.sif`): the same profile as R-016's tree.
  - `adk_submission.validate_directory` OK.
  - The two cluster-only errors.
  - The lint false error "root agent has no way to modify files". The lint fix goes to the other branch as handoff
    H-002.
  - The intended warning that a sub-agent holds `submit_patch`.

## Runs

| Arm | Tree | Cohort | Draws | Run ids |
|---|---|---|---|---|
| smoke (not read) | `trees/e4b-r017-nocompact` | `runs/_cohorts/smoke-te.txt` (2 tasks), concurrency 2 | 1 | `S-017-e4b-nocompact-smoke` |
| nocompact | `trees/e4b-r017-nocompact` | `cohorts/cdev2-79.txt` | 8 | `R-017-e4b-nocompact-tu5-d1..d8` |

- **Smoke.** It runs on Ada (1 GPU, 4 CPUs, 64G), where a GPU is free now. It uses the draw flags below, and it
  checks the mechanism only.
- **Draws.** Turing (`--constraint=QUADRORTX6000 -w pleiades-1-10`, after `squeue -w pleiades-1-10`), 1 GPU,
  4 CPUs, 64G. Flags: `--concurrency 4 --py313 env/py313-scorer/bin/python3.13 --task-envs env/taskenvs
  --time-scale 5.0`, exactly as R-011.
- **Queueing.** This follows the weekend rule: all eight draws are submitted now with `afterok` on the smoke.
  - If the smoke gate fails, all eight are cancelled.
  - If d1 fails a draw-1 kill gate, d2-d8 are cancelled or stopped, their rows are not read, and the arm is dropped.
  - The draws start as Turing GPUs free up, behind the L-003 a1 draws.
- **Control: R-011-e4b-base-tu5-d1..d8.** It ran on the same node with the same flags, scale and CPUs, with no new
  base draws. Values read 2026-11-21:
  - resolved 8, 5, 7, 8, 6, 7, 6, 9 (mean 7.0);
  - mean task wall 699.0, 599.1, 569.3, 596.7, 639.7, 603.2, 564.6, 585.9 s (mean 607.2);
  - empty patches 8, 9, 10, 14, 10, 17, 14, 9;
  - time caps 1, 0, 0, 1, 0, 0, 0, 0;
  - compactions 37, 33, 31, 34, 34, 37, 32, 33.
  - Drift since 2026-11-19 is a stated limit.
- **Cost.** About 0.2 Ada GPU-h for the smoke. A draw takes about 3.2-4.0 Turing GPU-h (R-011: 11,615-14,248 s),
  so about 29 GPU-h for 8 draws.

## Readings (written before any job runs)

1. **Smoke gate.** Every condition must hold:
   - both rows SUCCESS, with no engine error;
   - both traces show `solve` steps (`extra.author`) that make the repository tool calls;
   - the root makes at most 3 model calls per task;
   - no solver prompt-token drop of more than 40% from above 8,000.

   A failed smoke is fixed once, the fix is logged here, and the smoke is re-run. The draws' `afterok` is then
   re-pointed to the new smoke.
2. **Draw-1 kill gates.** These are read on d1 alone, and any one of them kills the arm:
   - resolved ≤ 3 (base mean − 4; base range 5-9);
   - empty patches ≥ 23 (base maximum + 6);
   - time caps ≥ 7 (base maximum + 6);
   - the mechanism fails: compaction (reading 1's test) in more than 2 of 79 task-draws.

   Wall time is not a gate here, because the E4B has spare time on Kaggle.
3. **Decision, d1-d8 against the eight base draws.**
   - Solves are compared paired over the 79 tasks, using each task's resolve rate over its draws per arm. The
     statistic is mean(arm − base) × 79, in solves per draw, with a 90% bootstrap CI over tasks (10,000 resamples,
     seed 0). The wall ratio (arm mean task wall / 607.2 s) is reported.
   - **Helps:** the CI lower bound is above 0. The E4B frozen config then uses the solver layout.
   - **Dropped:** anything else.
4. **Mechanism (reported, not gates).** Per draw, beside the base counts:
   - compactions;
   - context-length errors (`Sandbox execution error` rows) and how many of them resolved;
   - empty patches;
   - time caps;
   - turn-budget ends;
   - model calls after the 28th tool call;
   - root model time;
   - calls before the first edit.

## What each outcome means

- **Helps.**
  - E4B adapter data can be rebuilt as uncut on-policy rows, since a solver trace has no summary gap.
  - The fresh-context retry (a second `solve` when the first returns without `submit_patch`) is not tested here.
    It covers only 16 of 632 base task-draws (no submit call), so it waits for a reason.
- **Not helped, with many context-length errors.** The E4B needs compaction or a shorter context, and a lower
  solver `max_output_tokens` is the next variant.
- **Not helped, without those errors.** Losing the task prompt and the tree, or the longer context, costs the E4B
  as much as the summaries do.

**Blind guess (not a reading).**
- Passes its draw-1 gates: 70%.
- Helps: 15%.

## Queued (2026-11-21)

- Smoke: job 60015 (Ada). d1-d8: jobs 60016-60023 (Turing), `afterok:60015`.
- The smoke gate and the draw-1 gates are applied mechanically by `tools/gate_actor.sh` (it calls
  `tools/d1_gate.py`). These are the gates as written in readings 1-2, with no change:
  - smoke: `status_SUCCESS<2`, `root_calls_max>3`, `compacted>0`;
  - d1: `resolved<=3`, `empty>=23`, `timecap>=7`, `compacted>2`.
  - The `solve`-steps check in reading 1 is read by hand from the smoke traces.
