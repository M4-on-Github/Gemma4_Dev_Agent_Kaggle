# R-001 (31b): more tool calls; sibling-site sweep

Written 2026-11-18 before any candidate run, and before the R-000 reference draws were read.

- Base: `trees/31b-base`, reference draws `R-000-31b-base-d1`, `-d2` on `cohorts/cdev-56.txt`, concurrency 4.
- Directions: A1/A2 (31B) and their E4B twins (B2, and the call cap as a control of B4's premise).

## Proposals

| Tweak | Kind | Tree | Change | Evidence it cites |
|---|---|---|---|---|
| T-31b-001 | process (budget) | `trees/31b-r001-calls40` | `max_tool_calls` 28 -> 40; the prompt's budget line says 40 | Kaggle baseline arms: fastapi_14873, fastapi_15280, rich_3063, rich_3105, rich_3480, rich_3521 end at the 28-call cap with small reference patches (run synthesis 2026-11-17); all six are in cdev-56. F-000 smoke: fastapi_14605 at 28 calls, rich_3468 and rich_3006 at 27. |
| T-31b-002 | bug-fix mechanics | `trees/31b-r001-sweep` | new prompt section 3b: one grep of the changed identifier after the first edit, equivalent edit at every sibling site | run synthesis: partial fixes on multi-region reference patches are the largest loss class (31B), 9.5 tasks per draw (E4B). F-000 31B fastapi_14448: one-property edit where the reference touches several. |

## Runs

Two draws of each tree on cdev-56, concurrency 4: `R-001-31b-calls40-d1/-d2`, `R-001-31b-sweep-d1/-d2`.

## Readings (fixed now)

Let B = base mean resolves per draw, S = |d1 - d2| of the base.

- Kept: candidate mean > B + max(S, 3). Margin between 2 and max(S, 3): one more draw of both arms decides (kept if the three-draw means differ by 2 or more). Otherwise not kept.
- T-001 process endpoint: tasks ending at the call cap fall; if tasks at the 8-minute cap rise by more than 3 per draw the tweak is not kept whatever the resolves (it will not fit Kaggle's slower decode).
- T-002 process endpoint: share of tasks whose patch touches two or more hunks rises. If it does not move, the rule is not being followed and the result is a prompt-compliance lesson, not a verdict on the idea.
- Compose: if both are kept, or both are positive without either reaching the bar, run the two together as R-002's first candidate.
- No draw is rerun for a bad result. A job that fails for infrastructure reasons is rerun once.

## Results



Amendment 2026-11-18T09:30Z, before any R-001 31B result: d2 of each tree runs only if its d1 >= 22 (see rounds/R-002-31b-think1024.md). The reference is 22/22.
### T-31b-001 calls40, read 2026-11-18T12:30Z

d1 23/56 (base 22, 22). Tasks at the call cap 3 (base 13, 10); tasks at the 8-minute cap 27
(base 16, 14); empty patches 11 (base 11, 12); median wall 480 s (base ~356 s).

Readings applied: time-cap tasks rose by 11 to 13 per draw, over the limit of 3, so the tweak is
not kept whatever the resolves; d2 not run. The call cap was hiding the time cap: with 40 calls
the same tasks run into 8 minutes instead.

### T-31b-002 sweep, d1 read 2026-11-18T14:10Z

d1 23/56 (base 22, 22). Empty patches 7 (base 11, 12); time cap 14, call cap 12 (unchanged).
Readings applied: d1 >= 22, so d2 is queued. Three fastapi tasks the base resolved in one or both
draws (fastapi_14873, fastapi_14419, fastapi_5624) were lost by every candidate so far (calls40,
think1024, sweep), which suggests the two base draws were lucky on them; a third base draw
(`R-000-31b-base-d3`) is queued so the base is pooled over three.

### T-31b-002 sweep, read 2026-11-18T19:00Z

23, 23 against base 22, 22: +1.0, under the margin of 2. Not kept. Empty patches 7, 10 (base 11, 12);
tasks at the time cap 14, 19 (base 16, 14).
