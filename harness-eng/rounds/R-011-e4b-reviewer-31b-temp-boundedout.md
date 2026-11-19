# R-011: E4B editor→reviewer on the Turing lane; 31B temperature 0.6 and bounded output on the Ada screen

Written 2026-11-19, before any R-011 job. The user approved the plan on 2026-11-19 ("go ahead"), with
pleiades-1-10 lent for the E4B jobs and the two Ada GPUs for the 31B, and asked that each job request only the
resources it needs.

## Why

- **E4B.** R-010's synthesis over 9 base draws (3 Ada, 6 Turing; 641 unresolved task-draws) found:
  - wrong file 196, wrong region 143, partial 110, wrong change 54, edit-tool failure 52, others 83;
  - 182 of the 641 are on tasks that some E4B draw resolved;
  - 14 E4B tweaks so far, none kept.

  The E4B commits early and in the wrong place. Prompt rules about locating were followed (R-005 search
  template, R-007 locator stage with 19 and 20 of 20 LOCATION messages) and moved nothing. Direction B4 (a
  second look at the diff) has not been tried. It is tried here as a structural stage rather than a prompt rule,
  because the E4B leaves most of its budget unused (tasks end in about 30-50 s of 480 s on Ada, in under 10
  calls).
- **31B.** The pivot rule fired for prompt-process rules (9 tweaks, none kept). R-010 showed:
  - time cap and empty patch are draw-level events;
  - failing draws are hesitant, with 23-27k characters of thoughts against 15.5k, and 3.0 long turns against 1.7.

  The two untried levers in `directions.md` are A5 (temperature) and A4 (bounded observations). A6
  (reproduce first) is dropped: R-010 shows the 31B fails by committing late, and A6 would delay the edit further.

## Changes

| ID | Arm | Tree | Change from base |
|---|---|---|---|
| T-e4b-015 | reviewer | `trees/e4b-r011-reviewer` | SequentialAgent: editor, then reviewer, same model. The editor is the base agent without `submit_patch`; its section 4 ends in a three-line hand-over. The reviewer reads `git diff`, checks it against the issue's contract strings and sibling sites, fixes, and submits. Both stages share the 28-call cap and the time cap. |
| T-31b-010 | temp06 | `trees/31b-r011-temp06` | `configs/sampling.yaml`: temperature 1.0 -> 0.6 |
| T-31b-011 | boundedout | `trees/31b-r011-boundedout` | prompt section 2: every `run_command` ends in `head -40` (`tail -40` for a check); `read_file` ranges 120 -> 80 lines. Section 4's check examples carry the same tail. |

- **Why the editor cannot submit.** The harness ends the run at the first agent text message after a submit
  (`swegemma/harness/agent_runner.py:854-863`, then 920). An editor that submitted would cut the reviewer off.
- **Patch safety.** The reviewer can only add to the editor's work or change it. If the reviewer never reaches
  `submit_patch`, the on-disk diff is graded (`agent_runner.py:1054-1078`), exactly as in the base.
- **Validation.** `tools/validate_submission.py` gives each tree the same profile as its base: the 8-minute
  packing-gate error and the `timeout_seconds` warning that every cluster tree has, and no lint errors. The
  reviewer tree also gets the expected "sub-agent with submit_patch" warning.

## Design

**Resources.** Every job asks for 1 GPU, 4 CPUs and 64G (`slurm/eval.sbatch`, changed from 8 CPUs in this
round). The partition bills CPUs, and these jobs average about 2.1 cores. This is the one setup difference
between the R-011 base draws and the R-008/R-009 bases (8 CPUs). The E4B readings use only R-011 draws, so they
are unaffected. For the 31B screen, see reading 4.

**E4B, Turing lane** (pleiades-1-10, `--constraint=QUADRORTX6000 -w pleiades-1-10`). Flags:
`--concurrency 4 --py313 env/py313-scorer/bin/python3.13 --task-envs env/taskenvs --time-scale 5.0`, with
`HENG_SHIMS` off.

- **Why scale 5.** R-009 measured a median model-step gap of 18.5 s on Turing, against 3.3 s on Ada (about
  5.6x). At scale 2, 60 of 474 base task-draws hit the 16-minute cap, against 0 on Ada. At scale 5 the cap is
  40 minutes, which is close to Ada's effective budget.
- **Fresh base.** The R-009 base was drawn at scale 2, so it is not reused. The prompt still says 8 minutes,
  as at scale 2. `get_status` reports the real remaining time.

| Arm | Tree | Cohort | Draws | Run ids |
|---|---|---|---|---|
| smoke (not read) | `trees/e4b-r011-reviewer` | `runs/_cohorts/smoke-te.txt` (2 tasks), concurrency 2 | 1 | `S-011-e4b-reviewer-smoke` |
| base | `trees/e4b-base` | `cdev2-79` | 8 | `R-011-e4b-base-tu5-d1..d8` |
| reviewer | `trees/e4b-r011-reviewer` | `cdev2-79` | 8 | `R-011-e4b-reviewer-tu5-d1..d8` |

- **Smoke gate.** The smoke runs first. It passes when:
  - both tasks have a reviewer step in the trace (`extra.author == "reviewer"`);
  - there is no engine error.

  If it fails, the tree is fixed and the smoke re-run before any of the 16 jobs. Any fix is logged below.
- **Order.** The 16 jobs are submitted interleaved (base d1, reviewer d1, base d2, ...). That gives two waves
  of 8 on the node's 8 GPUs, sharing load evenly.
- **Cost.** About 4-6 h per job, so about 70-90 GPU-h on pleiades-1-10, outside the Ada ledger.

**31B, Ada** (`--constraint=RTX6000ADA`, at most two jobs at once). Flags: `--concurrency 4 --py313
env/py313-scorer/bin/python3.13 --task-envs env/taskenvs`, the R-008 flags.

| Arm | Tree | Cohort | Draws | Run ids |
|---|---|---|---|---|
| temp06 | `trees/31b-r011-temp06` | `screen-31b-20` | 2 | `S-011-31b-temp06-s1, s2` |
| boundedout | `trees/31b-r011-boundedout` | `screen-31b-20` | 2 | `S-011-31b-boundedout-s1, s2` |
| base (SD) | `trees/31b-base` | `cdev2-79` | 2 | `R-011-31b-base-te-d3, d4` |

- **Chains.** The jobs run as two `afterany` chains: temp06-s1 → s2 → base-d3, and boundedout-s1 → s2 → base-d4.
- **Cost.** About 0.6 GPU-h per screen and 2.1 GPU-h per cdev2-79 draw, about 6.6 GPU-h in all.
- **Promotion.** An arm promoted by reading 4 gets 2 cdev2-79 draws (L2) in a follow-up, logged below. Nothing
  goes to cdev2-79 before its screen is read.

## Checks and readings (written before the draws)

1. **Health, per draw.**
   - No engine crash.
   - A draw with fewer rows than its cohort is reported and not used.
   - Import errors on at most 2% of task-draws.
2. **E4B lane at scale 5 (reported, not a promotion).**
   - The base mean, compared with the R-009 scale-2 Turing base (8.33).
   - Task-draws at the time cap per draw, against 60 of 474 at scale 2.
   - The draw-to-draw SD of the 8 base draws.
3. **E4B reviewer (T-e4b-015), the L2 rule against the R-011 Turing base, as in R-009.**
   - **Compliance first.** A reviewer step must appear in at least 70% of task-draws. Under 50% means the editor
     used up the caps or the hand-over failed. That is a compliance reading, not a verdict on the idea, and the
     resolve readings below are reported only.
   - **Kept:** reviewer mean ≥ base mean + 3.
   - **Candidate:** reviewer mean ≥ base mean + 1.5, and the paired per-task difference over the 79 tasks
     (per-task resolve rate over 8 draws) has a 90% bootstrap CI above 0. A candidate is re-drawn on Ada
     before it is kept.
   - **Not kept:** anything else.
   - **Process endpoints, reported for every outcome:**
     - **Reviewer changes.** The share of task-draws where the reviewer made at least one accepted
       `edit_file`/`write_file` call. This is "reviewer changed the diff", counted from trace steps with
       `extra.author == "reviewer"`.
     - **Harm check.** Among task-draws where the reviewer edited, the resolve rate, against the base arm's
       per-task resolve rate on the same tasks. A lower rate on tasks the base resolves at least half the time
       is a resolved→unresolved warning. The editor's own diff is not graded separately, so this is the
       closest available measure.
     - Per draw, both arms: empty patches, time-cap task-draws, task wall time, and model calls per task.
     - Thought characters per task, and the zlib repetition check (compressed/raw ratio of the visible text
       under 0.2 flags a loop).
     - Editor calls to the missing `submit_patch` tool.
4. **31B screens (the L1 rule), against S-008-31b-base-te-s1/s2 on screen-31b-20 (8, 9; mean 8.5).**
   - **Promoted:** the two-draw mean is 10.0 or more (+1.5), or 9.0 or more (+0.5) with the arm's process
     endpoint met.
     - temp06 endpoint: summed over the two draws, time-cap plus empty-patch task-draws fall below the
       base's 17 (S-008 s1 + s2: empty 4 + 5, time cap 4 + 4).
     - boundedout endpoint: the median per-task peak prompt tokens falls by 15% or more against S-008 (the
       compaction trigger is 14,336), and fewer tasks compact.
   - **Dropped:** anything else.
   - **CPU caveat.** The base screens ran at 8 CPUs. If a promoted arm's lift is under +2, 2 base screens at
     4 CPUs are drawn before its L2 draws.
5. **31B base SD (reported).** The SD of the four cdev2-79 base draws: R-008 d1, d2 (28, 27) and R-011 d3, d4.
   The 4-CPU draws d3, d4 are also compared with d1, d2. A gap above 3 means the CPU change matters, and it is
   recorded before any further 31B run.
6. **No other comparison is read.** That excludes temp06 against boundedout, per-repo splits, and partial draws.

## Log
- **2026-11-19T21:53Z, pre-registration committed** as 051ea98 and pushed.
- **21:53Z, 31B chains submitted** (Ada, 4 CPUs, 64G each):
  - chain 1: `S-011-31b-temp06-s1` 59692 → `-s2` 59694 → `R-011-31b-base-te-d3` 59696;
  - chain 2: `S-011-31b-boundedout-s1` 59693 → `-s2` 59695 → `R-011-31b-base-te-d4` 59697.

  At submission another user's jobs held all 16 Ada GPUs, so the chains wait for two to free.
- **21:53-22:06Z, smoke `S-011-e4b-reviewer-smoke`** (job 59691, 741 s): **gate passed.**
  - Both tasks show the editor ending with a hand-over, then a reviewer stage that called `submit_patch`.
  - No engine error, and no editor call to `submit_patch`.
  - Resolved 0/2 (not read).
  - One reviewer opened with `read_file` instead of the `git diff` the prompt asks for, and submitted an empty
    diff after the editor's two edit calls left nothing on disk. Recorded for the compliance count, not fixed:
    the gate is that the stages run.
- **22:07Z, the 16 E4B draws submitted** on pleiades-1-10, interleaved: jobs 59706 (base d1), 59707 (reviewer
  d1) and so on, through 59720 (base d8) and 59721 (reviewer d8).
