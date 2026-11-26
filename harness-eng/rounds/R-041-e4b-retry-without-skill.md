# R-041: E4B retry-on-empty without a skill script (pre-registration)

Written 2026-11-26, before any job of this round is submitted. Counts only.

## Why

- **The retry layout is the only kept E4B improvement** (R-021: +1.08 per draw, CI +0.08..+2.08; held-out +0.67), and
  it has never been uploaded. Its retry decision rests on a skill script, `count.py`.
- **Public reports say skill scripts do not see the task repository on the official scorer** (Kaggle topics 758547
  and 758854, read 2026-11-26 through the API; participant reports, no host answer). One team's skill-only bundle
  scored 0.00 twice while its tool-based bundles scored 0.13-0.17; a second team found its skill script had indexed
  its own folder and not the repository.
- **If that holds, `count.py` prints 1 on the scorer** (its fallback on any read error), the root never retries, and
  the upload would be the plain E4B solver inside a wrapper. The cluster gain would not carry over.
- **Upload slots are few.** Turnaround on the scorer is reported at 30-40 h and a team may hold one pending
  submission (topics 760471, 761897, 761733), so about three more scored uploads fit before Dec 2.

## Arm

| Run | Tree | Draws |
|---|---|---|
| `R-041-e4b-rcheck-d1..d8` | `trees/e4b-r041-retry-check` | 8 |
| `R-041-e4b-rskill-d1..d4` (concurrent reference) | `trees/e4b-r020-retry` | 4 |
| comparator, reused: `R-021-e4b-retry-ada-d1..d12` | `trees/e4b-r020-retry` | 12 |

- **Change against `trees/e4b-r020-retry`.** The `change-count` skill is removed. The root gets a second
  `agent_tool`, `count_changes` (`sub_agents/check.yaml`): an E4B agent whose only tool is `run_command` and whose
  prompt is one fixed command that counts changed non-test source files from `git status --porcelain`, then replies
  with the number (or 1 on failure). It receives only its own request, not the issue. `prompts/root.md` calls it
  where it called the script. Solver, sampling and `eval_config.yaml` are unchanged (56 calls, 8 min).
- **Zero-GPU check.** The command counts 3 on a scratch repository with one modified file, two new source files and
  one new test directory. The tree validates with the same three errors as `e4b-r020-retry`.
- Cohort `cohorts/cdev2-79.txt`; flags as R-021: `-J heng_e4b`, concurrency 4, 1 Ada GPU per draw.

## Readings (written before any job runs)

1. **Smoke** (`S-041-e4b-rcheck-smoke`, 2 tasks): both served; `count_changes` is called after `solve` in both; its
   shell ran in both. A failed smoke is fixed once, logged, re-run.
2. **Served check**, every draw: 79 rows, 79 served; one re-run, logged first.
3. **Mechanism (decides the round with reading 4).** Over rcheck ×8:
   - (a) of the tasks whose first `solve` left no changed source file, the share where `solve` was called again:
     **0.85 or more** (skill retry in R-021: 163 of 169);
   - (b) share of `count_changes` calls that ran more than one shell command: **0.10 or less**;
   - (c) tasks where `solve` was called again although the first attempt had changed a source file: **2.0 per draw
     or fewer**;
   - (d) wall ratio against the pooled skill-retry draws (R-021 ×12 and rskill ×4): **1.10 or less**.
4. **Solves.** `tools/paired_boot.py --arm` rcheck ×8 `--base` the 16 skill-retry draws.
   - **Kept as the E4B upload candidate:** all four mechanism bars met and a point estimate of −0.75 or better.
   - **Not kept:** anything else. The E4B candidate is then the plain single loop.
   - Reported beside it: rskill ×4 against R-021 retry ×12 (drift), and empty patches per draw.
5. **Draw-1 kill gate** (by hand): fewer than 79 served after one re-run, or mechanism (a) under 0.5 on d1, or mean
   task wall above 1.3 × the R-021 retry mean. A kill cancels the remaining rcheck draws unread; rskill still runs.

**What this round cannot show.** Whether an `agent_tool` layout scores on the official scorer at all. Our upload
S-015 (an LlmAgent root over sub-agents) completed there at 0.05, which says such layouts run.

**Blind guess (not a reading).** Smoke passes first time 65%. Mechanism bars all met 55%. Kept 50%.

## Queued
