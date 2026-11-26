# R-047: E4B race, a runner restarts a solver that changed nothing (pre-registration)

Written 2026-11-27, before any job of this round is submitted and before any resolved count of R-045 is read.
Counts only. Queued on the user's instruction while R-045 runs.

## Why

- R-045's early check: the finish command printed EMPTY in 15 of 20 tasks for at least one runner, and no runner
  applied anything in 4 of 20 tasks. Those 4 are sure misses.
- The E4B's kept gain is retry on empty (R-021). Public result on restarts (Fail-Fast, Restart-Smart, 2026, as
  reported; not checked here): restarting a stalled run gains a little, more when the fresh run is told about the
  stalled one.
- The E4B has the wall time: R-045's early mean task wall was 105 s against an 8-minute cap.

## Arm and control

| Run | Tree | Draws |
|---|---|---|
| `R-047-e4b-race3r-d1..d8` | `trees/e4b-race3r` | 8 |
| control: `R-045-e4b-race3n-d1r, d2..d8` | `trees/e4b-race3n` | 8 (running) |

`trees/e4b-race3r` is `trees/e4b-race3n` with the runner prompt changed: on EMPTY the runner calls its solver once
more, saying the earlier attempt changed no file, then runs the finish command again. Flags as R-045.

## Readings (written before any job runs)

0. **Dependency on R-045.** If R-045 reads as harm against the retry tree, all R-047 draws are cancelled unread.
1. **Early mechanism check on d1 at 20 rows** (no resolved count looked at). Cancel unread and drop if any holds:
   - among runners whose first finish command printed EMPTY, fewer than half call their solver again;
   - a runner calls its solver again after APPLIED or TAKEN in more than 4 of 20 tasks;
   - the graded patch deletes files in more than 8 of 20 tasks;
   - mean task wall above 300 s.
2. **Served check** per draw: 79 rows, all served; one re-run with an `r` suffix.
3. **Decision** (`tools/paired_boot.py`, arm x8 against R-045 x8): **promote** at +1.0 or more with CI lower bound
   above -0.5 and mean task wall 300 s or less; **harm** at -1.5 or less; **not kept** otherwise.
4. **Mechanism, per draw:** restarts made; restarts that end in APPLIED; tasks with no APPLIED; emptied-tree patches;
   mean wall.

**Blind guess.** Early check pass 50%. Promote 20%.
