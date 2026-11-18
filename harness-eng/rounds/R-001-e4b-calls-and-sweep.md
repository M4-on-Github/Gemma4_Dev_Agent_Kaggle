# R-001 (e4b): more tool calls; sibling-site sweep

Written 2026-11-18 before any candidate run, and before the R-000 reference draws were read.

- Base: `trees/e4b-base`, reference draws `R-000-e4b-base-d1`, `-d2` on `cohorts/cdev-56.txt`, concurrency 4.
- Directions: A1/A2 (31B) and their E4B twins (B2, and the call cap as a control of B4's premise).

## Proposals

| Tweak | Kind | Tree | Change | Evidence it cites |
|---|---|---|---|---|
| T-e4b-001 | process (budget) | `trees/e4b-r001-calls40` | `max_tool_calls` 28 -> 40; the prompt's budget line says 40 | Kaggle baseline arms: fastapi_14873, fastapi_15280, rich_3063, rich_3105, rich_3480, rich_3521 end at the 28-call cap with small reference patches (run synthesis 2026-11-17); all six are in cdev-56. F-000 smoke: fastapi_14605 at 28 calls, rich_3468 and rich_3006 at 27. |
| T-e4b-002 | bug-fix mechanics | `trees/e4b-r001-sweep` | new prompt section 3b: one grep of the changed identifier after the first edit, equivalent edit at every sibling site | run synthesis: partial fixes on multi-region reference patches are the largest loss class (31B), 9.5 tasks per draw (E4B). F-000 31B fastapi_14448: one-property edit where the reference touches several. |

## Runs

Two draws of each tree on cdev-56, concurrency 4: `R-001-e4b-calls40-d1/-d2`, `R-001-e4b-sweep-d1/-d2`.

## Readings (fixed now)

Let B = base mean resolves per draw, S = |d1 - d2| of the base.

- Kept: candidate mean > B + max(S, 3). Margin between 2 and max(S, 3): one more draw of both arms decides (kept if the three-draw means differ by 2 or more). Otherwise not kept.
- T-001 process endpoint: tasks ending at the call cap fall; if tasks at the 8-minute cap rise by more than 3 per draw the tweak is not kept whatever the resolves (it will not fit Kaggle's slower decode).
- T-002 process endpoint: share of tasks whose patch touches two or more hunks rises. If it does not move, the rule is not being followed and the result is a prompt-compliance lesson, not a verdict on the idea.
- Compose: if both are kept, or both are positive without either reaching the bar, run the two together as R-002's first candidate.
- No draw is rerun for a bad result. A job that fails for infrastructure reasons is rerun once.

## Results


Read 2026-11-18T10:26Z. Base 4, 7 (mean 5.5, range 3; bar 8.5).

| Tree | d1 | d2 | Mean | vs base | Empty patches | Edit failures | Tasks at call cap |
|---|---|---|---|---|---|---|---|
| base | 4 | 7 | 5.5 | | 10, 8 | 17.1%, 27.9% | 1, 0 |
| calls40 | 8 | 7 | 7.5 | +2.0 | 3, 5 | 17.8%, 14.2% | 0, 0 |
| sweep | 11 | 5 | 8.0 | +2.5 | 5, 6 | 14.9%, 15.6% | 0, 1 |

Readings applied: neither reaches 8.5; both margins are in the 2-to-3 band, so one more draw of
each arm and of the base decides (queued in R-003). T-001's process endpoint had no room to move:
the E4B base uses 8 to 10 calls and hits the cap on at most one task. T-002's endpoint (patches
with two or more hunks) is not yet counted.
