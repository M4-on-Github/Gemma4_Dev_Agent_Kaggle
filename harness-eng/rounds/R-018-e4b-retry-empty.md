# R-018: E4B fresh-context retry when an attempt changes no file (pre-registration)

Written 2026-11-21 (about 21:30Z), before any job of this round is submitted. Counts only; no trace content.
Tweak id **T-e4b-018**. The `tweaks.md` row is added with the results. Part of the goal set by the user on
2026-11-21: find an orchestration framework for both models that can win.

## Why (offline sizing, zero GPU, read before this file was written)

- Every single-agent prompt and sampling change and every two-stage E4B layout so far was noise or worse
  (`tweaks.md`). What no round has tried is a second independent attempt.
- **pass@k on the eight E4B base draws** (R-011-e4b-base-tu5 d1-d8, 79 tasks): pass@1 7.0, pass@2 10.0, pass@3
  11.9, pass@8 18. Per-task resolve counts over 8 draws: 0 for 61 tasks, 1-3 for 12, 5-8 for 6. Most solvable
  tasks are solved only some of the time, so independent attempts add solves if they can be chosen between.
- **The free choice is an empty attempt.** An attempt whose patch changes no file is never right. The policy
  "retry only when the attempt changed no file" needs no selector.
  - Simulated by resampling the base draws (`tools/retry_sim.py`; ordered draw tuples, the shared tool and turn
    counters applied, an attempt that would cross a cap counted as unresolved):

    | Call cap | Max attempts | Resolved per draw | Attempts per task | Wall per task |
    |---|---|---|---|---|
    | 28 (base) | 1 | 7.00 | 1.00 | 607 s |
    | 28 | 2 | 7.86 | 1.14 | 667 s |
    | 40 | 3 | 8.24 | 1.18 | 701 s |
    | **56** | **3** | **8.34** | **1.18** | **717 s** |

  - On the three Ada base draws (R-008-e4b-base-te2 d1-d3) the same tool gives 6.67 → 7.67 at cap 56, 3 attempts
    (1.17 attempts per task, 106 → 122 s per task).
  - So the expected gain is about +1.3 solves per draw (+19%) for about 18% more wall. The E4B has the time
    (Kaggle projection 3.56-3.96 h, EXP-048).
  - Simulated alternatives with a selector over non-empty attempts (file-set vote, smallest patch) reach 8.7-9.0
    but need 2.5-3 attempts on every task (`tools/select_sim.py`). They wait for this round's mechanism result.
- **31B: not tested.** Most 31B empties end at the session timeout. In the six base draws, the 36 task-draws that
  were empty and ended early had a median of 115 s left, and no other draw of those tasks resolved them within
  that time (simulated gain 0.00). The 31B stays a single agent.
- The base simulation assumes attempts are independent draws of the base agent. A retry here starts in the
  workspace the first attempt left. That attempt changed no file, but scratch or test files may remain. This is a
  stated limit.

## Change

| ID | Arm | Tree | Change |
|---|---|---|---|
| T-e4b-018 | retry | `trees/e4b-r018-retry` | R-017's tree; root prompt calls `solve` again (same request) when `submit_patch` reports `files_changed` 0, at most 3 `solve` calls; `max_tool_calls` 28 → 56 |

- Everything else is `trees/e4b-r017-nocompact` byte for byte (solver prompt, solver and root sampling, time cap,
  turn cap). `diff -r` shows only the `agent.yaml` comment, `eval_config.yaml` `max_tool_calls`, and `prompts/root.md`.
- The call cap is raised because the counter is shared across the task, so a second attempt needs calls left. This
  makes it two changes in one arm. Stated. R-001 (calls 40, single agent) showed no effect of the cap alone.
- Validator (`--official`, in `env/harness.sif`): the same profile as R-017's tree. `adk_submission.validate_directory`
  OK; the two cluster-only errors; the lint false error "root agent has no way to modify files" (handoff H-002); the
  intended sub-agent `submit_patch` warning.

## Runs

| Arm | Tree | Cohort | Draws | Run ids |
|---|---|---|---|---|
| smoke (not read) | `trees/e4b-r018-retry` | `runs/_cohorts/smoke-te.txt` (2 tasks), concurrency 2 | 1 | `S-018-e4b-retry-smoke` |
| control | `trees/e4b-r017-nocompact` | `cohorts/cdev2-79.txt` | 12 | `R-018-e4b-ctl-ada-d1..d12` |
| retry | `trees/e4b-r018-retry` | `cohorts/cdev2-79.txt` | 12 | `R-018-e4b-retry-ada-d1..d12` |

- **Ada, not Turing.** Turing holds R-017 d2-d8 and the a2 draws. On Ada the E4B runs at about 105 s per task at
  time scale 1.0 (R-008-e4b-base-te2 d1-d3: 109, 109, 101 s), close to Kaggle, so a draw is about 40 min. The
  control is therefore run fresh on Ada in this round rather than taken from Turing R-017.
- Flags, every job: `sbatch -J heng_e4b slurm/eval.sbatch <run> <tree> cohorts/cdev2-79.txt --concurrency 4
  --py313 env/py313-scorer/bin/python3.13 --task-envs env/taskenvs` (time scale 1.0, cap 8.0 min), 1 Ada GPU,
  4 CPUs, 64G. The smoke uses the same flags with `--concurrency 2`.
- **Order.** Submitted interleaved (ctl d1, retry d1, ctl d2, retry d2, ...), all `afterok` on the smoke, so the two
  arms share time on the node.
- **Cost.** About 24 × 0.7 = 17 Ada GPU-h.
- Queueing follows the weekend rule. If the smoke gate fails, all draws are cancelled. If retry d1 fails a draw-1
  kill gate, every pending or running draw of both arms is cancelled and not read.

## Readings (written before any job runs)

1. **Smoke gate.** Every condition must hold:
   - both rows SUCCESS, no engine error;
   - both traces show `solve` steps that make the repository tool calls;
   - root model calls at most 7 per task; no task with more than 3 `solve` calls.

   A failed smoke is fixed once, the fix is logged here, and the smoke is re-run.
2. **Draw-1 kill gates**, on retry d1 alone (`tools/d1_gate.py`, Ada base R-008-te2 resolved 5-8, empty 9-13):
   - resolved ≤ 3;
   - empty patches ≥ 23;
   - time caps ≥ 7;
   - mechanism fails: `retry_miss` ≥ 3 (first attempt empty by `submit_patch`, and no second `solve` call), or any
     task with more than 3 `solve` calls.
3. **Decision, retry d1-d12 against control d1-d12**, paired over the 79 tasks with `tools/paired_boot.py` (per-task
   resolve rate over each arm's draws; mean difference × 79, solves per draw; 90% bootstrap CI over tasks, 10,000
   resamples, seed 0). The wall ratio (retry / control mean task wall) is reported.
   - **Helps:** the CI lower bound is above 0. The E4B frozen config then uses the retry layout.
   - **Kept on mechanism:** the CI lower bound is at or below 0, but all of these hold:
     - rescued (resolved with an empty first attempt) is at least 0.5 per draw over the 12 retry draws;
     - the point estimate is at least +0.5;
     - the wall ratio is at most 1.4.

     The E4B frozen config then also uses the retry layout, and the reason is stated as mechanism plus point
     estimate, not a significant effect.
   - **Dropped:** anything else.
4. **Mechanism (reported, not gates)**, per draw for both arms (`tools/retry_counts.py`, `tools/round_counts.py`):
   - the `solve`-call histogram;
   - first-attempt empty, non-empty and unknown;
   - retried, rescued, over-retry;
   - empty patches; time caps; turn-budget ends; mean task wall; root model calls.
   - The R-018 control against R-017 Turing and R-011 base: resolved and empties, as a drift check only.

## What each outcome means

- **Helps or kept.** The E4B framework becomes: a root that runs fresh-context `solve` attempts and retries an
  attempt that changed nothing. The next round adds a selector over non-empty attempts (simulated +1.9 at 2.5
  attempts per task), within the Kaggle time.
- **Dropped with rescued near 0.** A retry in the leftover workspace does not behave like an independent draw.
  Resetting the workspace between attempts is the next variant.
- **Dropped with rescued well above 0 but the point estimate not positive.** The higher call cap or the new root
  prompt changed the first attempt. Read the first-attempt empty rate of each arm.

**Blind guess (not a reading).** Passes the smoke and d1 gates: 75%. Helps: 15%. Kept on mechanism: 30%.

## Queued (2026-11-21)

- Smoke `S-018-e4b-retry-smoke`: job 60087. Draws, all `afterok:60087`, as (control, retry): d1 60088/60089,
  d2 60090/60091, d3 60092/60093, d4 60094/60095, d5 60096/60097, d6 60098/60099, d7 60100/60101,
  d8 60102/60103, d9 60104/60105, d10 60106/60107, d11 60108/60109, d12 60110/60111.
- Gate actors: smoke gate on 60087; retry d1 kill gates on 60089 (cancels every other R-018 job on a kill).

## Smoke gate (reading 1), 2026-11-21

- 60087 COMPLETED in 4 min 25 s. 2 rows, both SUCCESS, no engine error; resolved 1; empty 0; root model calls at most
  1 per task; `solve` calls more than 3: 0; first attempt non-empty in both tasks.
- Traces: both tasks show `solve` steps that make the repository tool calls (checked by step counts by author).
- **PASS.** The draws were released. Stated limit: neither smoke task had an empty first attempt, so the retry
  branch itself was not exercised by the smoke; the d1 `retry_miss` and `solve_calls_gt3` gates cover it.

## Draw-1 kill gate (reading 2), 2026-11-21: KILLED

- Retry d1 (60089) COMPLETED: 79 rows, all SUCCESS; resolved 6; empty 10; time caps 0; mean task wall 107 s.
- `retry_counts.py`: first attempt empty 7, retried 0, so **`retry_miss` = 7 ≥ 3, and the round is killed.**
  `solve_calls_gt3` was 0.
- `tools/gate_actor.sh` cancelled every other R-018 job as pre-registered. That includes control d1 (60088), which was
  running and is not read.
- **Cause, from the harness source and the event order.** Tool names and counts only:
  - In all 7 empty first attempts the solver itself called `submit_patch` (files_changed 0) and then replied, and
    the task ended there. The root never regained control.
  - `swegemma/tools/execution.py` sets `patch_submitted` on any `submit_patch`, even an empty one.
  - `harness/agent_runner.py` (about line 859) ends the task on the next final text event from any agent once
    `patch_submitted` is set.
  - So a retry is possible only if no agent submits before the last attempt. The R-017/R-018 solver had
    `submit_patch`. This is a design error in this round, not a property of retries.
- Also seen: 10 tasks had a second `solve` call. In all of them the first solver returned without submitting, in
  some after editing, and the root called `solve` again instead of `submit_patch`. That is over-retry on a
  non-empty workspace, against the prompt.
- Rounds that fix the mechanism: R-020 (solver without `submit_patch`; the root counts changed source files with a
  fixed command and submits).
