# R-014: 31B scout→editor on the Ada lane; E4B agent_tool edit applier on the Turing lane

Written 2026-11-20, before any R-014 job. The user asked on 2026-11-20 to explore orchestration under the allowed
harness, one change at a time, for both models, while LoRA prep runs in parallel ("go ahead"; "we'll try to do for
both E4b and 31b"). pleiades-1-10 may be used whenever nobody else has jobs on it, so `squeue -w pleiades-1-10` is
checked before each submit. Each job asks for 1 GPU, 4 CPUs and 64G, and the 31B uses at most two Ada GPUs at once.
R-013 (LoRA canary) is running alongside and shares neither trees nor readings with this round.

## Why

R-012 sized what each failure group can still give, using the leave-one-out flip rate over the 16 noisy 31B tasks
(4 base draws: 20 always solved, 16 noisy, 43 never). The orchestration candidates were ranked from that pool.

- **31B, late commitment.** Of the unresolved draws on noisy tasks, 3.5 per draw land no source edit: 8 hit the
  time cap and 6 the call cap, over 4 draws. The ceiling for that group is 1.92 resolves per draw, the largest of
  the four groups. Within the same task, unresolved draws make their first edit about 4 calls later than resolved
  ones (9 of the 11 tasks that have both). Prompt rules that ask for an earlier edit were not followed (R-004
  T-31b-007). This round tries a structural version of the same rule: a stage that cannot edit, and a hand-over to
  an editor told to edit within two calls.
- **E4B, copy fidelity.** Over the 8 R-011 Turing base draws (632 task-draws), 46.5% of task-draws have at least one
  failed edit, and 35.0% have an `old_string not found`. The R-012 review recounted 808 not-found failures: 265
  quote lines the agent never read, 306 lines it mostly read, 118 non-contiguous lines it read, 88 stale, 31
  whitespace-only. The E4B rarely hits the call cap (no base task-draw reached 28 calls in R-009). This round
  spends calls on a helper that re-reads the lines in a fresh, short context and builds `old_string` from that
  read.

Tried before and not repeated: EXP-032 (three parallel localizers used up all the calls); T-e4b-014 (locator then
editor on the E4B: format followed, same files chosen); T-e4b-015 (E4B editor then reviewer: 7.5 vs 7.0, not kept).

## Changes

| ID | Arm | Tree | Change from base |
|---|---|---|---|
| T-31b-012 | scout | `trees/31b-r014-scout` | SequentialAgent: scout, then editor, same model. The scout has `run_command`, `read_file` and `get_status`. Its prompt is base sections 1-2, a soft limit of 8 calls, and a three-line hand-over (TARGET, CHANGE, ALSO). The editor is the base agent with all six tools and history (`include_contents` default). Its prompt drops the search section, says to start from TARGET without a new search, and puts `edit_file` at the first or second call. Caps and sampling are unchanged. |
| T-e4b-016 | applier | `trees/e4b-r014-applier` | `edit_file` replaced by `agent_tool: sub_agents/apply_edit.yaml` (`skip_summarization: true`). The root prompt's section 3 says to call `apply_edit` with FILE, LINES and NEW, and on FAILED to read again and retry once with a narrower range. The helper (E4B, `read_file` and `edit_file` only) reads LINES ±5, copies `old_string` from that read, retries once with a 1-3 line anchor, and answers APPLIED or FAILED. Caps and sampling are unchanged. |

- **Facts relied on.**
  - The harness ends the run at the first agent text after a submit (`agent_runner.py:854-863`), so the scout has
    no `submit_patch`.
  - Calls and time are counted once per session, across stages and inside an agent_tool (`tools/base.py:86-100`,
    `context.py:468-552`). No per-agent cap exists, so the scout's 8 calls is a prompt rule only.
  - A nudge restarts a Sequential root at index 0, so a nudged 31B draw re-runs the scout. This is counted in
    reading 3.
  - The final stage submits, which avoids the EXP-052 crash (R-011 ran 632 Sequential draws with 0 errors).
  - The agent_tool runs in a fresh session (`agent_tool.py:203-290`) and takes one string, `request`.
    `read_file` returns raw lines without line numbers (`workspace.py:125-170`).
- **Validation.**
  - `tools/validate_submission.py --official` gives each tree its base's profile: the 8-minute packing-gate
    error, the `compile_submission` signature error from the validator's call, and the `timeout_seconds` warning.
    The official `validate_directory` is OK for both. The scout tree also gets the expected "sub-agent with
    submit_patch" warning.
  - An offline `compile_submission` with stub tools and the two models
    (`tools/compile_check.py`) builds both trees:
    - scout tree: `SequentialAgent[scout: run_command, read_file, get_status; editor: all six]`;
    - applier tree: `LlmAgent[run_command, read_file, write_file, get_status, submit_patch, apply_edit]`, with the
      AgentTool wrapping `apply_edit[read_file, edit_file]`.

## Design

**31B, Ada** (`--constraint=RTX6000ADA`, at most two jobs at once). Flags: `--concurrency 4 --py313
env/py313-scorer/bin/python3.13 --task-envs env/taskenvs`, the R-008/R-011 flags, at 4 CPUs.

| Arm | Tree | Cohort | Draws | Run ids |
|---|---|---|---|---|
| smoke (not read) | `trees/31b-r014-scout` | `runs/_cohorts/smoke-te.txt` (2 tasks), concurrency 2 | 1 | `S-014-31b-scout-smoke` |
| scout | `trees/31b-r014-scout` | `cohorts/cdev2-79.txt` | 8 | `R-014-31b-scout-d1..d8` |
| base | `trees/31b-base` | `cohorts/cdev2-79.txt` | 4 new | `R-014-31b-base-te-d5..d8` |

- **Comparison set.** Arm d1-d8 against base R-008 d1, d2 (8 CPUs), R-011 d3, d4 and R-014 d5-d8 (all at 4 CPUs).
  The 4 existing draws are 28, 27, 30, 28 (mean 28.25). Their mean task wall is 361 s on Ada.
- **Order.** After the smoke, scout d1 runs alone with base d5 beside it. The rest start only after the draw-1 gate
  (reading 3), as two `afterany` chains: scout d2 → base d6 → scout d3 → base d7 → scout d4, and scout d5 →
  base d8 → scout d6 → scout d7 → scout d8.
- **Cost.** About 2.05 GPU-h per draw, so 12 draws plus the smoke is about 25 Ada GPU-h. A kill at the draw-1 gate
  costs about 4.3 GPU-h (smoke, scout d1, base d5).

**E4B, Turing lane** (pleiades-1-10, `--constraint=QUADRORTX6000 -w pleiades-1-10`). Flags: `--concurrency 4
--py313 env/py313-scorer/bin/python3.13 --task-envs env/taskenvs --time-scale 5.0`, exactly as R-011.

| Arm | Tree | Cohort | Draws | Run ids |
|---|---|---|---|---|
| smoke (not read) | `trees/e4b-r014-applier` | `runs/_cohorts/smoke-te.txt`, concurrency 2 | 1 | `S-014-e4b-applier-smoke` |
| applier | `trees/e4b-r014-applier` | `cohorts/cdev2-79.txt` | 8 | `R-014-e4b-applier-tu5-d1..d8` |

- **Comparison set.** R-011-e4b-base-tu5-d1..d8: same node, flags, scale and CPUs, mean 7.0, SD 1.31, 56 of 632
  resolved.
- **Order.** After the smoke, d1 runs alone (reading 3). d2-d8 then go in at once if the node has 7 free GPUs, or
  as GPUs free.
- **Cost.** About 4-6 h per job, so about 40 GPU-h on pleiades-1-10, outside the Ada ledger.

**Extension (E4B only, decided by reading 5).** One extension to 16v16: 8 more applier draws and 8 more base draws,
`R-014-e4b-{applier,base}-tu5-d9..d16`.

## Checks and readings (written before the draws)

1. **Smoke gates (not resolve readings).**
   - 31B passes when both tasks show a scout step and an editor step in the trace (`extra.author`), the scout makes
     no edit, and there is no engine error.
   - E4B passes when there is no engine error, and at least one task calls `apply_edit` and gets back APPLIED or
     FAILED.
   - The E4B smoke also records whether the helper's inner `read_file`/`edit_file` calls appear in the trace. If
     they do not, readings 4 and 5 count edit failures from the helper's answers (FAILED) and from the on-disk diff.
     They do not count them from inner steps. The switch is logged below before d1 is read.
   - A failed smoke is fixed, the fix logged below, and the smoke re-run before any draw.
2. **Health, per draw.** No engine crash. A draw with fewer rows than its cohort is reported and not used. Import
   errors stay at or below 2% of task-draws.
3. **Draw-1 kill gates.** Each is computed from draw 1 alone, and any one kills the arm.
   - **31B scout:**
     - the scout's median calls per task exceed 10;
     - more than 15% of tasks reach the editor with fewer than 8 calls left (20 or more used);
     - more than 15% of tasks show a second scout turn after an editor turn (nudge re-runs);
     - the projected Kaggle time exceeds 11.0 h. That is 10.04 h × (arm mean task wall / 361 s), so the arm mean
       task wall must stay at or below 395 s;
     - resolved ≤ 24, which is the base mean minus 4.
   - **E4B applier:**
     - `apply_edit` is called on fewer than 60% of task-draws that change a source file;
     - more than 25% of task-draws have a failed edit (base 46.5%): a not-found, not-unique, no-op or malformed
       `edit_file`, inside the helper or not, or an `apply_edit` answer that is not APPLIED;
     - empty patches exceed 24.4% of task-draws (base 14.4% + 10 points);
     - resolved ≤ 4.
4. **31B scout (T-31b-012), 8v8, the R-012 rule.**
   - **Kept:** mean(arm) − mean(base) ≥ +1.9, and the projected Kaggle time from all 8 arm draws is ≤ 11.0 h. A
     kept arm becomes the 31B config that the LoRA adapter is trained on, after a held-out check that is its own
     round.
   - **Not kept:** anything else. There are no extension draws.
   - **Reported for every outcome:**
     - the paired per-task difference (79 tasks, resolve rate per task over 8 draws), with a 90% bootstrap CI;
     - the base SD over 8 draws;
     - the mechanism endpoint: no-source-edit unresolved draws on the 16 noisy tasks, per draw, against 3.5 (met
       at 1.5 or fewer);
     - median first-edit call, against 12-14;
     - time-cap and call-cap task-draws per draw;
     - scout calls per task (median and p90);
     - tasks where the editor searched again (a `git grep`/`grep`/`find` before its first edit);
     - TARGET file = reference file share. This is read from `runs/_analysis`, and only counts go in this file.
5. **E4B applier (T-e4b-016), 8v8 against the R-011 Turing base.**
   - **Harm stop:** after d1-d4, an arm mean at or below base mean − 1 (≤ 6.0) stops the arm.
   - **Candidate:** the paired per-task difference over the 79 tasks has a 90% bootstrap CI lower bound above 0.
     A candidate is re-drawn once on Ada (4 draws each) before it is kept.
   - **Extend:** a point estimate of +1.0 or more without a CI above 0 extends once to 16v16. The same CI rule is
     then applied to all 16 and 16, and there is no further extension.
   - **Not kept:** anything else.
   - **Reported for every outcome:**
     - the failed-edit task-draw share, against 46.5%, and the not-found share, against 35.0%;
     - `apply_edit` calls per task, and the APPLIED/FAILED split;
     - empty patches, time-cap and call-cap task-draws per draw. The call cap matters here because the helper's
       calls count;
     - median task wall, and the projected Kaggle time, 2.98 h × (arm mean wall / base mean wall on the same lane),
       against 11.0 h;
     - the harm check: resolve rate on tasks the base resolves in at least 4 of 8 draws.

Results are appended below as new sections and apply these readings as written.
