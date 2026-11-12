# EXP-079 — The file-list search recipe on the E4B single loop: desk check. The dispatched two-draw arm is NOT BUILT (D-011 ranked arm 2)

**Date:** 2026-11-12
**Type:** zero-GPU analysis: a desk check for a dispatched dev-48 arm of two kernels, about 2.6 GPU-h. The arm is not built, because section 4 shows its endpoint cannot clear the D-011 rule even at full uptake. 0 GPU-h.
**Cohort:** none
**Ladder:** L1, trace mining over the two temperature 1.0 base draws (EXP-038, EXP-077) and the same-tree reruns on disk. The L4 arm is not bought.
**Not pre-registered:** the counts were made before any reading was written. Nothing here is a reading of a run. The fixed id set and the SD reference in section 3 were chosen with the base counts in view.
**Serves:** D-011, ranked arm 2 in the 2026-11-12 revision after the critic's direction review (`experiments/EXP-074/critic.md`, "Ranked arms" item 2). The recipe comes from EXP-076 section 5.
**Relates:**
- EXP-076: the desk check that offered this recipe, with its simulation script `trunc.py`.
- EXP-074: the classes, and gold seen by path.
- EXP-038 and EXP-077: the two base draws.
- EXP-071 and EXP-072: on recipe uptake, a multi-flag or multi-step recipe was run on 2 or 3 of 8 tasks.
- EXP-078: the temperature 0.2 replicate, built beside this check.

## 1. The dispatch
The lead asked for one arm, run as two kernels of the same zip and pooled, on the EXP-033 single-loop tree at temperature 1.0.
- **The change:** one prompt edit. Section 2's search bullet becomes `git grep -l "TOKEN" -- '*.py'` with no `head`, in the shortest tool-native wording. The minimal form replaces `-n` with `-l` and drops `| head -20` from the existing bullet.
- **The endpoint (the critic's):** a gold path appears in a tool output before the first edit. Keep is set beyond the larger of the base-draw gap and two reference SDs (the D-011 endpoint rule).
- **Harm rows:** lost base resolves (noise-aware form), text-form calls, repeats, caps, wall, and R tasks entering through the lost line numbers.
- **Recorded:** uptake, the share of tasks whose first search uses `-l`.
- **The exit:** "If the desk check shows uptake cannot be expected, or the endpoint cannot clear the rule, say so and do not build."

## 2. Definitions and scripts
- **`experiments/EXP-079/desk.py RUN ...`** prints, per task:
  - **shown_path:** a gold source file's path, as the gold patch names it, appears as a substring of a tool observation before the first `edit_file` or `write_file`. This is EXP-074 section 7 point 2, gold seen by path. The observation of the step that carries the first edit is not counted.
  - **shown_any:** the same test, by path or basename (EXP-076's `shown`).
  - **first search:** the first `run_command` whose first pipeline segment is `grep`, `egrep`, `rg` or `git grep`. Its flags are recorded: `-l` (or `--files-with-matches`, `--name-only`, or a short cluster holding `l`), `-n`, a `head` pipe, and the recipe form (git grep with `-n` and `head`, without `-l`).
  - Totals are given over the 48 ids, over the run's own F tasks, and over a fixed id set.
- **`experiments/EXP-079/ceiling.py`** runs per base draw on the tasks with shown_path n, the misses. For each miss it records:
  - whether there is a qualifying search: EXP-076 `trunc.py`, a pattern quoted from the issue that a gold file holds at the base commit;
  - whether the file-list form of that search names a gold file within 5000 characters (`trunc.list_ok`). The recipe alone counts only searches not scoped elsewhere; a wider scope counts searches whose paths held no gold file;
  - an upper bound: any search pattern of 3 or more characters that a gold file holds, quoted from the issue or not, in any scope.
  - It then prints the paired shown_path table between the two draws and the threshold arithmetic.
- **The fixed id set:** the 15 ids that are F (resolved `f` included) in EXP-038 or EXP-077.
  - `fastapi_11355`, `fastapi_13207`, `fastapi_14448`, `fastapi_14512`, `fastapi_14583`, `fastapi_14962`, `fastapi_15661`, `fastapi_5624`, `requests_6644`, `requests_7315`, `rich_3067`, `rich_3105`, `rich_3468`, `rich_3480`, `rich_3953`.
  - It is taken from the base draws, so it is not conditioned on the arm's own classes. It includes `requests_6644`, which resolves with any patch.

## 3. Counts

### 3.1 The endpoint on the two base draws (`desk.py`)
| Set | EXP-038 | EXP-077 | Gap | Paired flips (038 only, 077 only) |
|---|---|---|---|---|
| All 48 | 33 | 40 | 7 | 2, 9 |
| Fixed 15 | 5 | 9 | 4 | 2, 6 |
| Run's own F, unresolved (recorded only: the denominator depends on the class the run lands in) | 3 of 12 | 5 of 8 | | |
| By path or basename, all 48 | 35 | 40 | 5 | |

- The critic's base of F 3 of 12 is reproduced on EXP-038 by path.
- An unchanged rerun of the base moved the endpoint by 7 of 48 (`desk.py --per-task`, paired):
  - 31 tasks are shown in both draws and 6 are missed in both: `fastapi_14512`, `fastapi_15661`, `rich_3105`, `rich_3935`, `rich_3953`, `rich_4075`.
  - 11 of the 17 tasks missed in either draw are discordant.
  - Shown in EXP-038 only (2): `requests_6644`, `rich_3480`.
  - Shown in EXP-077 only (9): `fastapi_11355`, `fastapi_13207`, `fastapi_13537`, `fastapi_14360`, `fastapi_14448`, `fastapi_14962`, `requests_7315`, `rich_3063`, `rich_3067`.

### 3.2 What the recipe could reach (`ceiling.py`), per base draw
| | EXP-038 | EXP-077 |
|---|---|---|
| Misses (shown_path n) | 15 | 8 |
| Misses with a qualifying search | 6 | 2 |
| List form names gold, the recipe alone | 2 (`fastapi_11355`, `fastapi_13207`) | 2 (`fastapi_14512`, `rich_3480`) |
| List form names gold only with a wider scope | 3 (`fastapi_14360`, `fastapi_14448`, `requests_7315`) | 0 |
| Upper bound: any pattern a gold file holds, any scope | 6 (adds `rich_3067`) | 3 (adds `rich_3953`) |
| Upper bound inside the fixed 15 | 5 | 3 |

- **Reconciling with EXP-076.** EXP-076 section 5 put the recipe-alone figure at 3 on EXP-038, including `rich_3480`. That count was over qualifying searches whose own output did not name gold. On this endpoint, `rich_3480` is not a miss in EXP-038, because another observation before the first edit shows its gold path (`desk.py --per-task`).
- **`fastapi_14512`, a miss in both draws.**
  - EXP-076 judged it unreachable, because its EXP-038 pattern is held by 311 files.
  - In EXP-077, `trunc.py EXP-077-base` prints one search held by 311 files (not list_ok) and another held by 166 files, which would list gold within 5000 characters.
  - So whether the recipe reaches it depends on which pattern the draw chose.
- **EXP-077 is the out-of-sample draw.** The recipe was chosen on EXP-038. On EXP-077 it reaches 2, with no wider-scope case.
- **The reachable ids against the base's own spread.**
  - All 6 of EXP-038's upper-bound ids are shown by the unchanged base in EXP-077 (they are among its 9 EXP-077-only ids).
  - Of EXP-077's 3: `rich_3480` is shown in EXP-038; `fastapi_14512` and `rich_3953` are missed in both draws.
  - The recipe-alone ids are disjoint between the draws.

### 3.3 Uptake (`desk.py`, first search)
| | EXP-038 | EXP-077 | EXP-075 (0.2) |
|---|---|---|---|
| Tasks with a search | 39 of 48 | 37 of 48 | 45 of 48 |
| First search is `git grep` | 27 | 24 | 40 |
| Uses `-n` | 30 | 24 | 40 |
| Has a `head` pipe | 11 | 10 | 21 |
| Recipe form (git grep, `-n`, `head`) | 10 | 9 | 21 |
| Uses `-l` | 0 | 0 | 0 |

- The base prompt's recipe is copied in full on about a quarter of first searches. Its `-n` is kept on most of them, and its `head` is dropped on most.
- So `-l` would likely be taken up on more tasks than the recipe form. The other way round, the `head` truncation the recipe removes is present on only 10 or 11 tasks per draw.
- This bears on the size of the expected move, not on whether it can clear the rule. Section 4 holds even at full uptake.

## 4. Finding: the endpoint cannot clear the D-011 rule, so the arm is not built
- **The rule.** Keep is set beyond the larger of the base-draw gap and two reference SDs. The SDs are binomial at the pooled base rate, with the draws treated as independent.
- **The thresholds, as per-draw counts the arm would need to beat:**

  | Set | Pooled base mean | Two pooled draws against two | One draw against one | Room to the ceiling |
  |---|---|---|---|---|
  | All 48 | 36.5 | more than +7.0: the gap 7 governs (2 SD = 5.91). Mean above 43.5 | more than +8.36. Mean above 44.86 | 11.5 |
  | Fixed 15 | 7.0 | more than +4.0: the gap 4 governs (2 SD = 3.86). Mean above 11.0 | more than +5.47. Mean above 12.47 | 8.0 |

- **The ceiling at full uptake.**
  - The recipe alone reaches +2 per draw on both draws.
  - The upper bound, which drops the issue-quote and scope conditions, reaches +6 and +3 over all 48, a mean of +4.5. Inside the fixed 15 it reaches +5 and +3, a mean of +4.0.
  - All 48: every figure is below the +7.0 pooled threshold.
  - Fixed 15: the upper bound only ties the +4.0 threshold, and the rule asks for more than the gap. That bound also needs the model to search more broadly, which the recipe does not ask for.
- **One draw cannot read it either.** Its thresholds are higher: +8.36 and +5.47.
- **The same answer from a paired reference.** The square root of the base's discordant pairs is 3.32 over all 48 and 2.83 over the fixed set. Two of those is 6.6 and 5.7, still above the recipe-alone ceiling of 2.
- **So the arm is not built.** No candidate tree, prompt file, zip or notebook exists for EXP-079, and the 2.6 GPU-h are not spent.
- **What the counts say instead.**
  - At this endpoint the base's own draw spread, 7 of 48, is larger than the recipe's best case.
  - Whether gold reaches the context before the first edit varies by draw on 11 of the 17 tasks missed in either draw. The other 6 are missed in both.
  - On the misses outside the upper bound (9 of 15 and 5 of 8), no search before the first edit would name gold in list form. These include tasks with no search before the first edit, and searches whose held pattern lists too many files.
  - This is reported as a finding on reach for the lead, not as a new lever.

## 5. Limits of this check
1. **The simulation holds the model's search patterns fixed.** With a list in place of matching lines, the model might choose different follow-up searches or reads. That could move the endpoint either way [I].
2. **The fixed set and the SD reference were chosen with the base counts in view.** The conclusion holds under every reference printed: binomial pooled, binomial one draw, and paired flips.
3. **Basename matching is not the endpoint.** By path or basename, the base values are 35 and 40, and the conclusion is unchanged.
4. **The anchoring harm (R tasks entering) is not estimated,** because the arm is not run.

## 6. Commands
```bash
python -I -X utf8 experiments/EXP-079/desk.py EXP-038-e4b-dev48 EXP-077-base EXP-075-t02 EXP-033-e4b EXP-044-X0
python -I -X utf8 experiments/EXP-079/desk.py EXP-038-e4b-dev48 EXP-077-base --per-task
python -I -X utf8 experiments/EXP-079/ceiling.py
python -I -X utf8 experiments/EXP-076/trunc.py EXP-077-base
```

## 7. Defects
1. **2026-11-12, corrected in place before any review.** This record has no pre-registered readings, so the corrections were made in place.
   - **§3.1** first said the two draws' miss lists "overlap little" and named `fastapi_14512` and `rich_3480` as shown in EXP-038 and missed in EXP-077. The paired table shows 6 tasks missed in both, `fastapi_14512` among them. The draw-038-only ids are `requests_6644` and `rich_3480`. §3.1 now gives the full paired lists.
   - **§3.2** now gives the source of the 311 and 166 file counts and adds the reachable ids set against the paired lists.
   - **§4** last bullet first said that on the misses outside the upper bound no chosen pattern is held by gold. The bound also requires the list form to name gold, so it now says what `ceiling.py` computes.
   - No count, threshold or conclusion changed.

## Status
**DESK CHECK COMPLETE 2026-11-12. The dispatched two-draw dev-48 arm is NOT BUILT (section 4).** The endpoint's base-draw gap is 7 of 48, and the recipe's full-uptake ceiling is 2 per draw (upper bound 4.5). 0 GPU-h.
