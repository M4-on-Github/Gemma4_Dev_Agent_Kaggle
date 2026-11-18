# R-006 (e4b): compose sweep + calls40

Written 2026-11-18T16:50Z, after the three-draw read of R-001 and R-003, before any R-006 run.

## What was read

| Tree | Draws | Mean | vs base | Verdict by its readings |
|---|---|---|---|---|
| base | 4, 7, 7 | 6.0 | | |
| R-001 calls40 | 8, 7, 9 | 8.0 | +2.0 | kept (R-001: three-draw means differ by 2 or more) |
| R-001 sweep | 11, 5, 8 | 8.0 | +2.0 | kept (same rule) |
| R-003 temp03 | 6, 3, 8 | 5.7 | -0.3 | not kept; range 5, not smaller than the base's 3 |
| R-003 short | 9, 6, 3 | 6.0 | 0.0 | not kept |
| R-004 nothoughts | 5, 5, 5 | 5.0 | -1.0 | not kept |

Both kept trees sit exactly on the +2.0 threshold, and one draw of this model moves by 3 to 6, so
"kept" here means "passed the rule as written", not "shown to be better". The compose run is the
real test: if both effects are real they should add.

## Proposal

T-e4b-010, compose: `trees/e4b-r006-sweep-calls40` = sweep's section 3b plus `max_tool_calls` 40
and the prompt's budget line at 40. Three draws on cdev-56, concurrency 4.

## Readings (fixed now)

- Becomes the new E4B base if the three-draw mean is >= 9.0 (base + 3). Later E4B rounds then start
  from it, and it goes to L3 (cheld-16, base and candidate, two draws each).
- Mean in [8.0, 9.0): the base becomes `e4b-r001-sweep` (the kept tree with a mechanism; calls40
  has none on a model that uses 8 to 10 calls), without an L3 run.
- Mean below 8.0: the two +2.0 results are treated as noise, the base stays `e4b-base`, and the
  lesson is that +2 on three draws is inside this model's noise; the E4B keep bar rises to +3.

## Results (read 2026-11-18T18:35Z)

8, 4, 8 (mean 6.7) against base 4, 7, 7 (6.0): +0.7, below 8.0. By the reading: the two +2.0 results
(calls40, sweep) are treated as noise, the base stays `e4b-base`, and the E4B keep bar on cdev-56
rises to +3. Empty patches 6, 5, 5; calls 9.0 to 10.5; no task at either cap.
