# R-046: 31B race, the three solvers start from different places (pre-registration)

Written 2026-11-27, before any job of this round is submitted and before any resolved count of R-043 is read.
Counts only. Queued on the user's instruction ("queue what we need") while R-043 runs.

## Why

- Wrong file and wrong region are 23% of failing 31B attempts (trace-vs-reference round). A ranked file list and a
  code map did not move a single attempt (R-027, R-039): the model goes with its first search hit.
- Three identical solvers re-draw the same first hit. Public result (Agentless, 2024, as reported; not checked
  here): attempts started from several sampled location sets solved more than the same number from one set.
- In a race a different start costs nothing when it loses.

## Arm and control

| Run | Tree | Draws |
|---|---|---|
| `R-046-31b-kfrace3v-d1..d8` | `trees/31b-kf-race3v` | 4 first, 4 more by the rule below |
| control: `R-043-31b-kfrace3d-d1..d8` | `trees/31b-kf-race3d` | 8 (running) |

`trees/31b-kf-race3v` is `trees/31b-kf-race3d` with one sentence changed in section 2 of two solver prompts:
- solver a: unchanged;
- solver b: searches the issue's quoted text first (error message), else its second identifier;
- solver c: first finds and reads at most 60 lines of the nearest existing test, then searches as a.

Flags as R-043 (`--concurrency 1`, cohort `cohorts/cdev2-79.txt`).

## Readings (written before any job runs)

0. **Dependency on R-043.** If R-043 is killed at its draw-1 gate or reads as harm, all R-046 draws are cancelled
   unread.
1. **Served check** per draw: 79 rows, all served; one re-run with an `r` suffix.
2. **Draw-1 kill gate:** 25 or more empty-or-deleted-tree patches, or mean task wall above 443 s.
3. **Extension rule.** After d1-d4: d5-d8 are submitted only if the point estimate against R-043's finished draws is
   0 or better and the wall ratio against R-043 is 1.10 or less. Otherwise the round ends as not kept.
4. **Decision** (`tools/paired_boot.py`, arm x8 against R-043 x8): **promote** (replaces the R-043 tree) at +1.5 or
   more with CI lower bound above -0.5 and wall ratio 1.05 or less; **harm** at -1.5 or less; **not kept** otherwise.
5. **Mechanism, per draw:** which solver's patch won (a, b, c shares); solver c's calls before its first edit against
   a's; tasks where the winners' changed files differ from R-043's most common file set; empty patches; mean wall.

**Blind guess.** Promote 15%, not kept 70%, harm 15%.

## Results (2026-11-27, readings applied as written)

Draw ids: d1-d4 = 68070-68073.

0. **Dependency: met.** R-043 passed its draw-1 gate and read not kept (−0.25), not harm.
1. **Served check: pass.** All 4 draws have 79 rows and 79 served tasks.
2. **Draw-1 kill gate: pass.** 13 empty-or-deleted-tree patches (bar 25), mean task wall 329.8 s (bar 443 s).
3. **Extension rule: not met; the round ends as not kept.** Varied starts 32, 29, 28, 29 (29.50) against R-043 x8
   (30.12): **−0.62 per draw, 90% CI −2.38..+1.00**. Wall ratio 335.7 / 330.3 = 1.016. Against kfctl x8: −0.88
   (CI −3.62..+1.75). d5-d8 are not submitted.
5. **Mechanism:** empty patches 0.5 per draw, deleted-tree patches 12.75 per draw (R-043 10.4), mean wall 335.7 s.
   The winner shares, solver c's calls before its first edit and the changed-file comparison were not computed: the
   round ended at the extension rule.

**Lesson.** Sending the three solvers to different starting points (issue text, a second identifier, the nearest test)
does not raise what the race solves. Together with R-043: the 31B's misses are not a matter of where it starts.
