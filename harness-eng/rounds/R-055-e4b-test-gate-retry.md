# R-055: E4B, the retry layout with a test gate in the check command (pre-registration)

Written 2026-11-28, before any job of this round is submitted. Counts only. User go-ahead 2026-11-28.

## Why

- Desk check (final-week-plan.md, 2026-11-28): 41% of failing E4B patches are catchable by a run of existing tests.
  Selection over three attempts simulates at 9.46 solves with the gate, 8.45 without, 8.12 for the control.
- The E4B uses about a third of its time (149 s of 480 s), so sequential fresh attempts fit without parallel
  streams. R-045 showed the E4B cannot run the three-runner race mechanics; this arm keeps the retry layout it
  already follows.
- R-029 fed a syntax error back as a repair request and failed. Here a flagged attempt is set aside and the next
  attempt starts fresh.

## Arm

`trees/e4b-gate` = `trees/e4b-r041-retry-check` with one change, the check agent's command (about 850 characters):

- Counts changed non-test `.py` files (the control counts ten source extensions).
- Runs up to three tracked test files named after the changed modules (50 s limit). If they fail or do not
  collect, the attempt is stashed and the same files run on the clean tree. If they pass there, the attempt stays
  stashed and the command prints 0, so the root starts another attempt, as it does for an empty one.
- On the third check, if nothing is in place, the stashed attempt is restored and counted.

Scratch test (throwaway repository): no change 0; breaking attempt 0 and set aside; third check restores it and
prints 1; good attempt 1; no matching test 1; tests failing before the attempt 1.

## Readings (written before any job runs)

1. Smoke: both tasks served; the check command run without a shell error.
2. Draw-1 kill gate: 25 or more empty patches or mean task wall above 300 s.
3. Decision, `R-055-e4b-gate-d1..d4` against rcheck x8 (8.12): extend to 8 draws at +0.75 or more; promote at 8
   draws with +1.0, CI lower bound above -0.5 and mean wall 300 s or less; harm at -1.5.
4. Mechanism: check commands matching the prompt text exactly; attempts flagged; flagged attempts replaced by a
   later attempt and their solve rate; attempts restored on the third check; solver calls per task; mean wall.

**Blind guess.** The E4B copies the command exactly in 90% of calls or more: 50%. Flagged first attempts per draw
10 or more: 60%. Extension: 20%. Promote: 8%.

## Smoke (job 68469, 2026-11-28 08:05 UTC)

Both tasks served; one resolved (62 s), one not (347 s, three solver calls). The one check command visible in the
root traces is copied exactly. Reading 1 passes; draws released.

## Result, four draws (read 2026-11-28 10:00 UTC)

- Solved 6, 6, 9, 9: mean 7.50 against rcheck 8.12. **Paired -0.62, 90% CI -2.12..+0.75. Not extended, not kept.**
- Empty patches 10, 8, 5, 15 (rcheck 2-6). Mean wall 168, 210, 173, 214 s (rcheck 149 s).
- Per task: `solve` 1.78 calls against 1.47, `count_changes` 1.47 against 1.14. The root calls the check less often
  than the solver, so a set-aside attempt is not always restored: the gate turns some non-empty patches into empty
  ones. Flag counts per draw were not extracted (the check command's output is inside the check agent's session).

## R-055b (pre-registered 2026-11-28, before any job)

`trees/e4b-gate2`: the same command with the restore moved from the third check to the second (two numbers in the
command change). A flagged first attempt gets one fresh attempt; if that changes nothing, the flagged attempt comes
back. Draws `R-055b-e4b-gate2-d1..d4`; same gates and bars as R-055. Additional reading: empty patches per draw at
or below 6. **Blind guess.** Empty patches back to 6 or fewer per draw: 55%. Extension: 12%.

## R-055b draws (read 2026-11-28 12:20 UTC, all four complete)

- Solves 2, 8, 10, 8; empty patches 48, 7, 8, 7; mean task wall 307, 182, 188, 178 s.
- **Draw 1 is void (deviation, logged with its evidence).** In completion order its last 43 tasks are 36
  consecutive session timeouts followed by 7 `litellm.InternalServerError` results: the model server stopped
  answering part-way and never recovered. The decode probe at start was normal (154.7 tokens/s, same as draws 2-4).
  This is a server fault, not the tree. As read with d1 included the result would be -1.12 (CI -2.88..+0.50) and
  the draw-1 kill gate (25 empty, 300 s) would fire; both are set aside. Draw 1 is rerun as
  `R-055b-e4b-gate2-d1r`, and the four-draw reading is taken on d1r, d2, d3, d4 when d1r is complete.
- Draws 2-4 alone (not a reading): 8, 10, 8, empties 7-8 against 5-15 for R-055, so the earlier restore removed
  most of the extra empty patches.

## R-055b four-draw reading (2026-11-28 13:35 UTC; d1r, d2, d3, d4)

Rerun draw `d1r`: 8 solves, 7 empty patches, 169 s. Four draws: 8, 8, 10, 8 = 8.50 against 8.12 for the control.
Paired difference +0.38, 90% interval -1.25 to +2.00. Empty patches 7-8 per draw (control 2-6); wall 169-188 s
(control 149 s). The extension bar (+0.75) is not met: **not kept**. Moving the restore to the second check
removed the harm of R-055 (-0.62) but the gate still adds no solves and a few empty patches.
