# R-054: 31B, R-052's agreement layout plus a test gate in the finish command (pre-registration)

Written 2026-11-28, before any job of this round is submitted. Counts only. User go-ahead 2026-11-28.

## Why

Desk check (final-week-plan.md, 2026-11-28): 26% of failing 31B patches stop the graded run at a collection error
that is not a missing new name, or fail a test the test patch does not touch. As a selector over three attempts the
gate simulates at 33.87 solves against 33.14 without it (one attempt 30.38). An upper bound, since the agent does
not know which test files are graded.

## Arm

`trees/31b-kf-agree-gate` = `trees/31b-kf-agree` (R-052) with a longer finish command (about 2,000 characters):

- It picks up to three tracked test files whose name contains the stem of a changed non-test `.py` file, and runs
  them (45 s limit) with the attempt applied; if they fail or do not collect, it runs them again without it.
- An attempt that breaks tests which pass without it is **flagged**: not saved for agreement. It is applied and
  submitted only as a provisional first patch, once, when no unflagged attempt exists yet.
- Everything else as R-052. No model call is added.

Scratch test (throwaway repository): flagged first attempt FIRST (provisional), good attempt FIRST (replaces it),
second flagged attempt AGAIN, agreeing good attempt FINAL; working copy clean afterwards.

## Readings (written before any job runs)

1. Smoke: both tasks served, a finish command run without a shell error, no engine error.
2. Draw-1 kill gate: 25 or more empty patches, or 3 or more tasks graded on a tree with deleted files.
3. Decision, `R-054-31b-gate-d1..d4`: against kfctl x8 as in R-052 (extend at +1.5; promote at 8 draws with +2.0 and
   CI lower bound above 0); and against R-052's draws for the gate itself (kept in the layout at +0.5 or more).
4. Mechanism: finish commands that match the prompt text exactly; attempts flagged per draw; test-run tool time per
   task; flagged attempts that were the only patch; solve rate of tasks with and without a flag; mean wall.

**Blind guess.** The 31B copies the command exactly in 90% of calls or more: 65%. Flagged attempts per draw between
10 and 40: 55%. Gate worth +0.5 over R-052: 25%.

## Smoke and a deviation, logged 2026-11-28 07:50 UTC before any draw is read

- **R-052 smoke (job 68464, after two server-start failures on GPUs occupied by another user's processes):** both
  tasks served. Task 1: two finish commands, both copied exactly, two `submit_patch` calls, resolved in 194 s.
  Task 2: no solver finished before the cap (605 s), no finish command ran, and the task was graded on the
  emptied tree, as in the race rounds' no-apply tasks. Reading 1 passes.
- **Deviation.** Kill-gate clause "3 or more tasks graded on a tree with deleted files" was written for tasks that
  had a submitted patch and were still graded on an emptied tree. As written it would also count every task where
  no attempt finished, which the race rounds show at about 11 per draw and which this layout cannot remove. The
  clause is read as: 3 or more tasks **with a submit** graded on an emptied tree. Tasks with no finished attempt
  are counted and reported under reading 4/5. Changed before any draw result exists.

## Smoke (job 68474, 2026-11-28 08:05 UTC)

Both tasks served and resolved (208 s, 504 s). Five finish commands, all copied exactly; outputs FIRST, FINAL on
task 1 and FIRST, AGAIN, FINAL on task 2; two `submit_patch` calls per task. Reading 1 passes; draws released.

## Draws d1-d4 void: submitted at the wrong task concurrency (logged 2026-11-28 10:55 UTC)

Same setup error as R-052 (see that file): `--concurrency 4` put twelve solver streams on one GPU. The four draws
were cancelled at 52-57 of 79 tasks; partial counts (0-4 solves, 52-54 tasks at the cap with nothing applied, same
slow pace) were seen in the diagnosis and are void. Rerun: same tree and cohort, `--concurrency 1`, run ids
`R-054-31b-gate-r1..r4`, job time limit 15 h. Readings apply to r1..r4 as written, with R-052 r1..r4 as the
comparison arm.
