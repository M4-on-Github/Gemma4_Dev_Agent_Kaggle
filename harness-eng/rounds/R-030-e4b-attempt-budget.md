# R-030: E4B syntax trigger with the attempt budget kept by the check script (pre-registration)

Written 2026-11-22, before any job of this round is submitted, and before R-029's syn-solver draws and controls
are read. Counts only; no trace content, no ids. Tweak id **T-e4b-030**. Same goal as R-029 (set by the user on
2026-11-22): raise the solve rate and the models' abilities, with small sweeps before bigger runs.

## Why

- **The desk case is R-029's**, unchanged. A final E4B patch that leaves a changed source file unparseable resolved
  in 0 of 170 task-draws, at 8.58 per draw in the retry layout. It is a sure miss, so it can trigger another
  attempt for free.
- **R-029 syn-retry was killed at d1** by `solve_calls_gt3>=3`, with value 3 against a comparator maximum of 2.
  - The root call orders show why: the root loses count of its solve calls once the repair branch loops. One task
    made 5 solve calls and never submitted.
  - The trigger itself worked: 7 tasks flagged, 7 re-solved, `syntax_retry_miss` 0.
  - The limit lived in the root prompt ("fewer than three times"), and the E4B root does not keep that count.
- **The change here:** the check script owns the budget, so the root only follows one word.
  - The script counts its own calls in a file inside the workspace's `.git` directory, which is never part of the
    patch, with `/tmp` as the fallback.
  - On calls 1 and 2 it prints `retry: ...` (no source file changed) or `repair: syntax error in PATH line N`.
  - From call 3 on, or whenever the change parses, it prints `submit`.
  - So at most 3 solve calls follow from the script, whatever the root counts. This fixes the R-029 cause. It does
    not address the second finding, that a repair often fails (4 of 7 still unparseable).

## Arm

| ID | Arm | Tree | Change against `trees/e4b-r020-retry` (the shipping E4B layout, R-021) |
|---|---|---|---|
| T-e4b-030 | synb-retry | `trees/e4b-synb-retry` | `skills/change-count` → `skills/attempt-check`; root steps 2-5 follow the printed word (retry: same request; repair: the R-029 repair request plus the printed error; submit) |

- `trees/e4b-synb-retry` is `trees/e4b-syn-retry` (R-029) with three changes:
  - the `agent.yaml` comment;
  - the skill swap;
  - the root prompt (`diff -r` shows only these).
- The solver, the sampling, the call cap of 56, the 8 min cap and the turn cap are unchanged.
- **`attempt-check/scripts/check.py`** is R-029's `check.py` with a new `main`, plus the counter.
  - Synthetic repo: empty × 4 printed retry, retry, submit, submit. A syntax error printed repair, and once fixed
    printed submit. Syntax error × 3 printed repair, repair, submit.
  - The counter file does not appear in `git status`.
  - On any error it prints `submit`.
- Validator (`--official`): the parent's known profile, the same as R-029's trees.
- `tools/retry_counts.py` reads the new lines: `retry` as an empty count, `repair` as a syntax line.

## Runs

| Stage | Run | Tree | Cohort | Draws | Dependency |
|---|---|---|---|---|---|
| smoke (not read for effect) | `S-030-synb-smoke` | `trees/e4b-synb-retry` | `runs/_cohorts/smoke-syn2.txt`, concurrency 2 | 1 | none |
| A | `R-030-e4b-synb-ada-d1..d4` | `trees/e4b-synb-retry` | `runs/_cohorts/syn-36.txt` | 4 | `afterok` the smoke |
| B | `R-030-e4b-synb-c79-d1..d12` | `trees/e4b-synb-retry` | `cohorts/cdev2-79.txt` | 12 | `afterok` the smoke |

- **Comparators**, as R-029:
  - stage A: R-021 retry d1-d12 restricted to syn-36 (mean 2.83, unparseable 6.25 per draw);
  - stage B: R-021 retry d1-d12 on cdev2-79 (mean 7.58, wall 139.7 s, unparseable 8.58).
- **Fresh controls:** R-029's `R-029-e4b-ctl-ada-d1..d2` (syn-36) and `R-029-e4b-ctl-c79-d1..d2` (cdev2-79),
  queued on 2026-11-22 in the same period. No new controls are run.
- Flags as R-029. Cost: about 0.15 + 4 × 0.5 + 12 × 0.75 ≈ 11 Ada GPU-h.

## Readings (written before any job runs)

1. **Smoke gate.** A kill cancels every R-030 job.
   - Gate fields: `status_SUCCESS<2 solve_calls_gt3>=1 root_calls_max>11`.
   - Read by hand, also a kill: the script printed anything other than a `retry`, `repair` or `submit` line, or
     printed `submit` on a first call with an empty count.
   - A failed smoke is fixed once, the fix is logged here, and the smoke is re-run.
2. **Stage-A d1 kill gates** (the gate actor cancels A d2-d4 and all of stage B):
   - R-029's bars, unchanged: `empty>=9 timecap>=6 mean_wall>250 retry_miss>=4 solve_calls_gt3>=3 callcap>=14
     syntax_retry_miss>=3`;
   - checked on the 12 comparator draws in R-029 (12 of 12 PASS; `syntax_retry_miss` is 0 there).
3. **Stage A (reported):**
   - unparseable final patches per draw (`tools/patch_syntax_desk.py`) against 6.25, with **mechanism works** when
     this is at most 3.0;
   - the flagged, retried, `syntax_last` and rescued counts;
   - solves against the comparator and against the 2 fresh controls (noise at this size);
   - wall ratio.
4. **Stage B decision:** R-029's reading 4 word for word, with synb-retry in place of syn-retry.
   - **Helps:** the paired 90% CI lower bound is above 0.
   - **Adopted on mechanism:** the CI lower bound is at or below 0, but all of these hold:
     - the point estimate is at least +0.25;
     - unparseable final patches are at most 4.3 per draw;
     - `syntax_rescued` is at least 0.5 per draw;
     - the wall ratio is at most 1.15.
   - **Dropped:** anything else.
   - Secondary: the point estimate against the 2 fresh cdev2-79 controls.

## What each outcome means

- **Adopted:** the E4B shipping layout becomes `trees/e4b-synb-retry`, and a Kaggle handoff re-runs the dev-48 wall
  check.
- **Mechanism works, no solves:** the repaired patches parse but are still wrong, which matches the 5% re-draw
  rate. Dropped.
- **Mechanism fails:** repairs do not make the file parse. Read `syntax_last`. A whole-file rewrite request would
  be the next variant.

**Blind guess (not a reading).** Smoke and d1 pass: 75%. Mechanism works: 45%. Helps: 10%. Adopted on mechanism:
25%.

## Queued (2026-11-22)

- Smoke 60702. Stage A d1-d4: 60703-60706. Stage B d1-d12: 60707-60718. All draws are `afterok:60702`.
- Gate actors: smoke 60702 (cancels every R-030 draw), stage-A d1 60703 (cancels 60704-60706 and stage B), with
  the bars of readings 1 and 2.
