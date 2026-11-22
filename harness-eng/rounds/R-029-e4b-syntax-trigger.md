# R-029: E4B syntax trigger, repair on a patch that does not parse (pre-registration)

Written 2026-11-22, before any job of this round is submitted. Counts only; no trace content, no ids (cohort ids
are in gitignored `runs/_cohorts/`). Tweak ids **T-e4b-029a** (syn-retry) and **T-e4b-029b** (syn-solver). Part of the
goal set by the user on 2026-11-22: raise the solve rate and the models' abilities, with small representative
sweeps before bigger runs.

## Why (desk, zero GPU, read before this file was written)

- R-027 showed that finding the file does not limit the E4B. R-028 showed that its edits do: about 100 failed old
  strings per draw. The question here is what the edits leave behind.
- **`tools/patch_syntax_desk.py`.** It applies each recorded final patch to the changed files of the task's
  snapshot, then runs the builtin `compile()` on every changed `.py` file. A file that already failed before the
  patch is skipped.

  | Runs | Empty | Parses (resolved) | Changed source file does not parse (resolved) |
  |---|---|---|---|
  | R-021 E4B retry, cdev2-79 × 12 | 5.25 | 65.17 (7.58) | **8.58 (0.00)** |
  | R-021 E4B control (one solve), × 12 | 21.0 | 52.42 (6.25) | **5.58 (0.00)** |
  | 31B base, × 6 | 15.5 | 62.0 (28.67) | 1.5 (0.00) |

  - A final patch that does not parse resolved in **0 of 170** E4B task-draws. Every error was in a source file,
    none only in a test file. It is a sure miss, so it can trigger another attempt for free, the way an empty
    attempt does in R-021.
  - The retry layout's empty-retry produced more of these: 5.58 to 8.58 per draw. Some empty first attempts were
    replaced by broken ones.
- **Room left** in the 103 retry-layout task-draws that ended unparseable:
  - median wall 171 s of 480, median tool calls 18 of 56, 11 at 50 calls or more, 1 time cap;
  - solve calls used: 1 in 57, 2 in 26, 3 in 17, 4 in 3.
- **Independent-draw rate.** The same tasks resolve in 5.1% of the other R-021 retry draws. A plain re-draw would
  therefore add about 8.58 × 0.05 ≈ 0.4 solves per draw on cdev2-79.
  - This round asks for a repair instead. The new solve call names the file and line that do not parse, and starts
    from the workspace the earlier attempt left. Whether a repair beats a re-draw is the open question.
- **Precedent.** R-004 T-e4b-007 (2026-11-18, single agent, cdev-56 × 3) replaced the solver's pytest check with a
  `python -m ast` check: +0.3, not kept, against a +3.0 bar. Its parse endpoint was not reported.
  - Arm b is close to that change, now inside the retry layout. It is the cheap comparison arm.
  - Arm a does not depend on the solver following a bullet. The root runs the check, as it runs the change count in
    R-021.

## Arms

| ID | Arm | Tree | Change against `trees/e4b-r020-retry` (the shipping E4B layout, R-021) |
|---|---|---|---|
| T-e4b-029a | syn-retry | `trees/e4b-syn-retry` | `skills/change-count` → `skills/change-check` (`scripts/check.py`); root prompt step 4 (below) |
| T-e4b-029b | syn-solver | `trees/e4b-syn-solver` | one solver bullet in section 4: right after the last edit, run `python -m py_compile` on each changed source file and fix a reported error with one `edit_file` |

- **`check.py`** is `count.py` (R-020) with the same changed-file rules, pure file reads, no other program and
  nothing written.
  - It also runs `compile()` on each changed or new `.py` source file.
  - It prints `0`, or the number of changed source files, or `syntax error in PATH line N` for the first changed
    file that does not parse.
  - A file whose baseline (a loose object) does not parse either is not flagged.
  - On any error it prints 1.
  - Checked on a synthetic repo, and on real snapshots after applying recorded final patches
    (`tools/check_script_desk.py`, 12 per class): empty → `0` 12 of 12, parses → a number 12 of 12, does not parse
    → `syntax error` 12 of 12. Median 0.36 s.
- **syn-retry root prompt**, replacing R-021's steps 2-4:
  - step 2 calls `change-check`;
  - step 3: on `0`, re-solve with the same request, as before;
  - step 4: on a `syntax error` line, and with fewer than 3 solve calls, call `solve` with "Resolve the issue in
    /workspace. The change so far left a syntax error; fix it first." plus the printed line word for word, then
    return to step 2;
  - step 5: otherwise `submit_patch`.
  - The solver, the sampling, the call cap of 56, the 8 min cap and the turn cap are unchanged.
- **Validator** (`--official`, `env/harness.sif`): both trees give the parent's known profile.
  - `adk_submission.validate_directory` OK.
  - The cluster-only gate and compile errors, and the H-002 false error.
  - The VERIFY warning for the skill script.

## Cohorts and comparators

- **Stage A: `syn-36`** (36 tasks, `runs/_cohorts/syn-36.txt`).
  - The tasks that ended unparseable in at least one of the **R-021 control** draws.
  - They were chosen with the control draws, so the comparator, **R-021 retry d1-d12** restricted to the cohort,
    is not biased by the selection.
  - Comparator per draw: 4, 5, 3, 2, 4, 2, 4, 1, 3, 1, 3, 2 (mean 2.83). Unparseable final patches: 6.25 per draw.
  - Two fresh controls (`trees/e4b-r020-retry`) run on the cohort as a drift check.
- **Stage B: `cohorts/cdev2-79.txt`.**
  - Comparator: R-021 retry d1-d12, per draw 7, 12, 6, 9, 9, 7, 8, 6, 8, 5, 7, 7 (mean 7.58), mean task wall
    139.7 s, unparseable 8.58 per draw.
  - Two fresh controls run on cdev2-79.
- The smoke uses `runs/_cohorts/smoke-syn2.txt`: the 2 tasks that ended unparseable most often in the R-021 retry
  draws (9 and 8 of 12).

## Runs

| Stage | Job | Tree | Cohort | Draws | Dependency |
|---|---|---|---|---|---|
| smoke (not read for effect) | `S-029-synr-smoke`, `S-029-syns-smoke` | each arm | smoke-syn2, concurrency 2 | 1 each | none |
| A | `R-029-e4b-synr-ada-d1..d4` | `trees/e4b-syn-retry` | syn-36 | 4 | `afterok` its smoke |
| A | `R-029-e4b-syns-ada-d1..d4` | `trees/e4b-syn-solver` | syn-36 | 4 | `afterok` its smoke |
| A | `R-029-e4b-ctl-ada-d1..d2` | `trees/e4b-r020-retry` | syn-36 | 2 | none |
| B | `R-029-e4b-synr-c79-d1..d12` | `trees/e4b-syn-retry` | cdev2-79 | 12 | `afterok` the syn-retry smoke |
| B | `R-029-e4b-ctl-c79-d1..d2` | `trees/e4b-r020-retry` | cdev2-79 | 2 | none |

- Flags as R-027: `sbatch --parsable -J heng_e4b slurm/eval.sbatch <run> <tree> <cohort> --concurrency 4 --py313
  env/py313-scorer/bin/python3.13 --task-envs env/taskenvs`, 1 Ada GPU, 4 CPUs, 64G. Smokes use `--concurrency 2`.
- **Stage B is queued with stage A** (the weekend rule: queue gated draws up front and cancel them unread if a gate
  fails). It is gated on the syn-retry smoke and on syn-retry's stage-A d1 gate.
  - The trigger fires only on a sure miss, so stage A cannot show the solve effect at 4 draws on 36 tasks. Its job
    is to show that the mechanism works.
- Cost: about 2 × 0.15 + 10 × 0.45 + 14 × 0.75 ≈ 15 Ada GPU-h.

## Readings (written before any job runs)

1. **Smoke gate, per arm.** A kill cancels that arm's draws unread, and for syn-retry also every stage-B synr job.
   A failed smoke is fixed once, the fix is logged here, and the smoke is re-run.
   - Gate fields: `status_SUCCESS<2 solve_calls_gt3>=1 root_calls_max>11`.
   - Read by hand, also a kill: `check.py` raised or printed anything other than an integer or a `syntax error`
     line.
2. **Stage-A d1 kill gates, per arm** (`tools/gate_actor.sh`; it cancels that arm's d2-d4, and for syn-retry all
   stage-B synr jobs as well).
   - Bars: `empty>=9 timecap>=6 mean_wall>250 retry_miss>=4 solve_calls_gt3>=3 callcap>=14`. Checked with
     `tools/d1_gate.py` on all 12 comparator draws restricted to syn-36: 12 of 12 PASS (maxima empty 6, time caps
     2, wall 210 s, `retry_miss` 1, `solve_calls_gt3` 2, callcap 11).
   - syn-retry only: `syntax_retry_miss>=3`, meaning a `syntax error` print with solves left and no further solve
     call in 3 or more tasks.
3. **Stage A (reported; it decides nothing except through gates 1 and 2)**, per arm on syn-36, 4 draws:
   - unparseable final patches per draw (`tools/patch_syntax_desk.py`), against 6.25. The **mechanism works** when
     this is at most 3.0;
   - solves per draw against the 12 comparator draws and against the 2 fresh controls (`tools/paired_boot.py`);
   - wall ratio;
   - syn-retry: `syntax_flagged`, `syntax_retried`, `syntax_retry_miss`, `syntax_last`, `syntax_rescued`
     (`tools/retry_counts.py`);
   - syn-solver: tasks whose solver ran `py_compile` (from `tools/round_counts.py` command counts, if available,
     otherwise a counts-only scan).
4. **Stage B decision, syn-retry on cdev2-79**: 12 draws against R-021 retry d1-d12, paired per task with
   `tools/paired_boot.py` (90% CI over tasks, 10,000 resamples, seed 0). The wall ratio is reported.
   - **Helps:** the CI lower bound is above 0. The E4B shipping layout becomes `trees/e4b-syn-retry`.
   - **Adopted on mechanism:** the CI lower bound is at or below 0, but every one of these holds:
     - the point estimate is at least +0.25;
     - unparseable final patches are at most 4.3 per draw, half of 8.58;
     - `syntax_rescued` is at least 0.5 per draw;
     - the wall ratio is at most 1.15.

     The shipping layout then also becomes `trees/e4b-syn-retry`, and the reason is stated as mechanism plus point
     estimate. The rationale: the trigger fires only on attempts that are sure misses, so it can cost a solve only
     through wall, calls or a changed root.
   - **Dropped:** anything else.
   - Secondary (reported): against the 2 fresh cdev2-79 controls. If the point estimate against them is below 0,
     that is stated.
5. **Arm b (syn-solver)** has no stage B in this round. If its stage-A unparseable count is at most 3.0 and its
   point estimate against the comparator is at least the syn-retry arm's, a later round may combine the two.

## What each outcome means

- **syn-retry adopted.** The E4B framework becomes: retry on empty, repair on a patch that does not parse, at
  most 3 solves, then submit. A Kaggle handoff (H-NNN) is written to re-run the dev-48 wall check with the new tree.
- **Mechanism works but no solves** (unparseable count halved, rescued near 0). The repaired patches parse but are
  still wrong. This matches the 5% re-draw rate: those tasks are hard either way. Dropped.
- **Mechanism fails** (the count stays near 6 on syn-36). The repair attempt breaks the file again or fails to fix
  it. Read `syntax_last`.

**Blind guess (not a reading).** Both smokes and d1 gates pass: 75%. Mechanism works (syn-retry): 60%. Stage B
helps: 10%. Adopted on mechanism: 30%. syn-solver mechanism works: 25%.

## Queued (2026-11-22)

- Smokes: syn-retry 60648, syn-solver 60649.
- Stage A: synr d1-d4 60650, 60652, 60654, 60656 (`afterok` 60648); syns d1-d4 60651, 60653, 60655, 60657
  (`afterok` 60649); fresh controls 60658, 60659.
- Stage B: synr cdev2-79 d1-d12 60660-60671 (`afterok` 60648); fresh controls 60672, 60673.
- Gate actors (`logs/gate_R-029_<job>.log`): smoke 60648 (cancels synr stage A and stage B), smoke 60649 (cancels
  syns stage A), synr d1 60650 (cancels synr d2-d4 and stage B), syns d1 60651 (cancels syns d2-d4), with the bars
  of readings 1 and 2. The by-hand smoke checks are read when the smokes finish.

## Smoke gates (reading 1), 2026-11-22: both PASS

- syn-retry 60648 COMPLETED in 7 min 58 s. 2 rows SUCCESS; resolved 0; root model calls at most 8; `solve_calls_gt3` 0.
  `check.py` printed an integer once and a `syntax error` line 3 times, with empty stderr and no exception. One task
  was flagged, re-solved once, and still did not parse at submit (`syntax_last` 1). Both tasks reached the call cap.
- syn-solver 60649 COMPLETED in 7 min 59 s. 2 rows SUCCESS; root calls at most 5; `solve_calls_gt3` 0; one task hit
  the call cap.
- The gate actors released nothing (the draws are `afterok` on the smokes). Stage A and stage B run as queued.

## Stage-A d1 gates (reading 2), 2026-11-22

- **syn-retry d1 (60650): KILLED** by `solve_calls_gt3>=3` (value 3; comparator maximum 2). 36 rows SUCCESS;
  resolved 5; empty 3; time caps 0; mean wall 190 s; callcap 12; `retry_miss` 0; `syntax_retry_miss` 0.
  - The gate actor cancelled synr d2-d4 (60652 was running and is not read) and all 12 stage-B synr draws, as
    pre-registered. Stage B does not run, so reading 4 has no data and syn-retry is **dropped** in this round.
  - Mechanism, reported only: 7 tasks flagged, 7 re-solved, 4 still unparseable at the last check, 0 rescued.
  - Cause, from root call orders (counts only; S = solve, x = a syntax line, 0 = an empty count, n = a count, P =
    submit_patch). The 7 tasks with more than 2 solve calls: `SxSxSnP` 2, `SxSxSxP`, `SxSxSP`, `SxSxSxSxS`,
    `S0SSxSxS`, `S0S0SSnP` 1 each.
    - The root loses count of its solve calls once the repair branch loops: repeated syntax prints lead to a 4th
      or 5th solve call.
    - It sometimes calls solve twice with no check in between.
    - A repair often fails to make the file parse (4 of 7).
- **syn-solver d1 (60651): PASS.** 36 rows SUCCESS; resolved 3; empty 4; mean wall 138 s; callcap 7; `retry_miss` 2;
  `solve_calls_gt3` 1. d2-d4 continue.
- Both jobs carry the OUT_OF_MEMORY flag after writing all rows. This is the known grading kill of one task's
  infinite-loop test (R-008), not a lost row.

## Results (readings applied as written), 2026-11-22

All R-029 jobs have ended. syn-retry d2-d4 (60652, 60654, 60656) had started next to d1, because all three waited
only on the smoke. They hold partial rows from before the kill cancelled them. The reading script printed their
counts by accident. **They are not read and not used.**

### syn-retry (T-e4b-029a): dropped at the d1 gate (reading 2)

- Reading 4 has no data, since stage B was cancelled. The d1 mechanism counts are in the section above.
- The follow-up that fixes the kill cause is R-030 (the check script keeps the attempt count), queued on 2026-11-22.

### syn-solver (T-e4b-029b), stage A (reading 3) and reading 5

| | syn-solver d1-d4 | comparator (R-021 retry ×12 on syn-36) | fresh controls d1-d2 |
|---|---|---|---|
| resolved per draw | 3, 3, 3, 3 | 2.83 (range 1-5) | 3, 6 |
| unparseable final patches per draw (`patch_syntax_desk.py`) | **6.5** | 6.25 | 5.5 |
| empty per draw | 2.0 | | 2.0 |
| mean task wall | 148.4 s (ratio 0.88) | 169.5 s | 153.8 s |

- Paired against the comparator: +0.17 (CI −1.00..+1.25). Against the fresh controls: −1.50 (CI −3.75..+0.50).
- **Mechanism fails:** 6.5 per draw against the bar of at most 3.0.
  - The solver follows the bullet: it ran `py_compile` in 29, 26, 30 and 30 of 36 tasks.
  - In the 26 unparseable rows:
    - 9 never ran `py_compile`;
    - in 15, the last `py_compile` reported an error, and the solver ended anyway;
    - 76 `edit_file`/`write_file` calls came after the first `py_compile`.
  - So the error is seen, and the fix edits fail. This matches R-028, where the E4B's limit is the edit, at about
    100 failed old strings per draw.
- Reading 5: the unparseable count is above 3.0, so no later combination round. **Dropped.**

### Other observations (reported)

- Fresh controls, against their comparators:
  - syn-36 (3, 6): +1.67, CI +0.08..+3.42 against the 12 R-021 draws;
  - cdev2-79 (60672, 60673): unparseable 8.0 per draw, resolved 8.0 mean against 7.58.
  - Two draws only, so drift is not established. It is stated because the syn-36 controls sit above all but one
    comparator draw.
- Across this round's E4B draws, unparseable final patches resolved 0 of 57 more task-draws (syns 26, synr d1 4,
  controls 27). The sure-miss premise holds.
- Large single-file deletions (more than 10 lines removed in one file) that still parse: 1.5 per draw in R-021
  retry, 0 resolved. That is a second sure-miss class, small at about 0.08 solves per draw. Held back for R-030's
  outcome.
