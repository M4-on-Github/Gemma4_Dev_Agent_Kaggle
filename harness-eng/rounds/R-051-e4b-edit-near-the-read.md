# R-051: E4B, keep the edit inside the local attention window (pre-registration)

Written 2026-11-28, before any job of this round is submitted. Counts only.

## Why

- **Architecture (model config, checked 2026-11-28).** The E4B has 42 layers, of which 35 attend only to the last 512
  tokens and 7 (layers 5, 11, 17, 23, 29, 35, 41) to the whole context. The 31B: 50 layers at 1,024 tokens, 10 full.
- The solver prompt lets it read up to 120 lines at once, far more than 512 tokens, and the issue text sits at the
  top of the context. At the edit, the text to copy and the requirement are visible to 7 layers only.
- rcheck d1: `edit_file` fails 2.1 times per task and succeeds 1.9; 26% of failing E4B patches end in an import,
  attribute, name or type error.
- Earlier edit-failure work (R-034 line-edit, L-008 adapter) changed the tool or the weights; none moved the text
  to be copied next to the call.

## Arm

`trees/e4b-near` = `trees/e4b-r041-retry-check` with two solver bullets: read at most 30 lines covering the change
right before each `edit_file` and copy `old_string` from that output; restate the issue's required names and
behavior in one line in the same step.

## Readings (written before any job runs)

1. Served check per draw. 2. Draw-1 kill gate: 25 or more empty patches or mean wall above 300 s.
3. Decision, `R-051-e4b-near-d1..d4` against rcheck x8: extend to 8 at +0.75 or more; promote at 8 draws with +1.5,
   CI lower bound above -0.5, wall 300 s or less; harm at -1.5.
4. Mechanism: failed and successful `edit_file` calls per task; share of failing patches ending in an import,
   attribute, name or type error; calls per task; mean wall.

**Blind guess.** Failed edits per task fall by a third: 45%. Extension: 20%. Promote: 8%.

## Draw 1 (job 68326, read 2026-11-28 05:45 UTC)

79 rows; resolved 9 (rcheck draws 7-10, mean 8.12); empty 2 (rcheck 2-6); mean wall 130.8 s (rcheck 149.2 s). Kill
gate not met. Draws 2-4 continue; no reading before four draws.
