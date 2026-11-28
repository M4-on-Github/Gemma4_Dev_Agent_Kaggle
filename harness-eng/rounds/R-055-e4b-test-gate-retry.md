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
