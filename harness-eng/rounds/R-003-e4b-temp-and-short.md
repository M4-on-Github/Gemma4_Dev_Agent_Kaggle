# R-003 (e4b): third draws for R-001; temperature 0.3; short prompt

Written 2026-11-18T10:30Z after reading R-001 and R-002 E4B results, before any R-003 run.

- Base: `trees/e4b-base` (nothing was kept in R-001 or R-002).
- The draw-to-draw noise is larger than the two reference draws showed: the same tree gave 11 and 5
  (sweep), 6 and 2 (editfix). From here every E4B arm gets three draws and the base is pooled over
  three.

## Runs

1. Deciding draws called for by R-001's readings (margins of +2.0 and +2.5): `R-000-e4b-base-d3`,
   `R-001-e4b-calls40-d3`, `R-001-e4b-sweep-d3`.
2. T-e4b-004, process (sampling): `trees/e4b-r003-temp03`, temperature 1.0 -> 0.3. Evidence: the
   spread above; identical trees differ by up to 6 resolves of 56, and tasks such as rich_3067,
   rich_3535, fastapi_14794 flip between draws of one tree. Three draws.
3. T-e4b-005, process (prompt length): `trees/e4b-r003-short`, the 3.1 kB prompt replaced by a
   six-step 1.3 kB prompt that keeps the edit and test-path rules and adds a `git diff --stat` check
   before submit. Evidence: 8 to 10 empty patches per base draw with `submit_patch` called on 95% of
   tasks (the model submits without a diff), and R-002 showing that adding edit rules to the long
   prompt did not lower edit failures on d2 (15.1%) or empty patches (8, 7). Three draws.

## Readings (fixed now)

Let B3 = mean of the three base draws.

- R-001 trees: kept if the three-draw mean beats B3 by 2 or more (as written in R-001).
- T-004, T-005: kept if the three-draw mean beats B3 by 3 or more; a margin of 2 to 3 is recorded as
  "positive, not kept" and may be composed.
- T-004 process endpoint: range over its three draws is smaller than the base's.
- T-005 process endpoint: empty patches at most 4 per draw.
- If two or more trees are kept or positive, R-004 composes them.

## Results

(appended after the runs)
