# R-002 (e4b): edit-failure recovery

Written 2026-11-18 after reading the R-000 E4B reference draws, before any R-001 or R-002 result.

- Base: `trees/e4b-base`; reference `R-000-e4b-base-d1` 4/56, `-d2` 7/56 (mean 5.5, range 3).
- Runs in parallel with R-001 on the same base (R-001's results are not known), so it is a third
  independent probe, not a step from R-001's outcome.

## Proposal

| Tweak | Kind | Tree | Change | Evidence |
|---|---|---|---|---|
| T-e4b-003 | bug-fix mechanics (edit tool use) | `trees/e4b-r002-editfix` | three prompt lines under "Edit": `old_string` of one to three lines copied from the last read; after an error re-read and retry with one line; after a second error do the change with a scripted `str.replace` and check `git diff --stat` | R-000 d1/d2: 17.1% and 27.9% of edit calls fail; empty patch on 10 and 8 of 56 tasks; 68 FileEditError lines in d1's log, e.g. four in a row on `fastapi/applications.py` and three on `rich/console.py`, the model's own note: "context matching is proving extremely brittle" |

## Runs

`R-002-e4b-editfix-d1/-d2` on cdev-56, concurrency 4.

## Readings (fixed now)

- Kept: mean resolves > 5.5 + 3 = 8.5 per draw. Mean in (7.5, 8.5]: one more draw of each arm decides.
- Process endpoints: edit-failure rate below 12% and empty patches at most 5 per draw. If these move
  and resolves do not, the lesson is that edit failures were not what cost the tasks; the tweak is
  then kept only as a component to compose, not as a base.
- If the scripted fallback appears in under 3 tasks per draw, the third line is not being followed.

## Results


Read 2026-11-18T10:26Z. d1 6/56, d2 2/56 (mean 4.0, base 5.5). Edit failures 9.1% and 15.1%
(endpoint: below 12%, met on one draw). Empty patches 8 and 7 (endpoint: at most 5, not met).

Readings applied: not kept. The process endpoints did not move reliably either, so this is a
compliance result: three more rule lines in a 3.1 kB prompt did not change how the E4B edits.
