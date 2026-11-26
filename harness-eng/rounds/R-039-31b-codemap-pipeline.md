# R-039: 31B code-map pipeline under Kaggle's binding limit (pre-registration)

Written 2026-11-25, before any job of this round is submitted and before any resolved count of R-037 or R-038 is
looked at. Counts only. User goal (2026-11-25): the highest hidden-test score in the days left; the user lifted the
2-running job cap for the final-week rounds the same day ("submit as many as you need", not more than needed).

## Why

`rounds/trace-vs-reference.md` (286 failing 31B draws): 105 never edit, and 86 of those had read the reference file;
69 fix part of a multi-site fix, and the model's own check passed in 30 of the 32 that ran one. Prompt rules aimed at
both (T-31b-002, T-31b-007) were not kept. This round changes what each step is able to do instead of what it is told.

## What was built and measured at zero GPU (2026-11-25)

- `tools/locator_v2/` (`locate.py`, `eval_locator.py`, `anchor_eval.py`): cleaned, title-weighted BM25 plus
  identifier, path and graph terms; symbols by `ast`; related sites (near-duplicate bodies, the same method across a
  class family, overloads, same name elsewhere, callers, callees). Tuned on cdev2-79, checked once on cheld2-22.

| | cdev2-79 | cheld2-22 |
|---|---|---|
| reference file in top 5: R-027 BM25 / v2 | 48 / 53 of 76 | 16 / 20 of 21 |
| a reference symbol in top 8 (v2) | 31 of 73 | 14 of 19 |
| all reference symbols covered, fixes with 2 or more | 5 of 38 | 2 of 9 |
| related sites from one true anchor: recall of the other symbols / precision (top 10) | 0.204 / 0.141 (n 38) | 0.382 / 0.142 (n 9) |
| related sites from the 31B's real partial-fix patches (49 draws, 11 tasks) | recall 0.408, precision 0.106; some missed symbol listed in 39, all in 11 | none |

- The graph terms move file ranking by 2 tasks or fewer; the gain over R-027's ranker is mostly issue cleaning.
- Harness's own `search_similar_code`: top-5 file recall 29-38% on cdev2-79, level with grep; not used.
- Expected size, stated before the run: small. The audit can list every missed symbol in about a fifth of partial-fix
  draws, and the map shows a reference symbol in under half of the tuning tasks.

## Arms

| Run | Tree | Draws | Stands in for |
|---|---|---|---|
| `R-039-31b-kfmap-d1..d8` | `trees/31b-kf-map` | 8 | Kaggle `trees/31b-map` |
| `R-039-31b-kfmaplite-d1..d8` | `trees/31b-kf-maplite` | 8 | Kaggle `trees/31b-maplite` |
| control: `R-037-31b-kfctl-d1..d8` | `trees/31b-kf-ctl` | 8 (reused) | Kaggle `31b-base` |
| smokes `S-039-31b-kfmap-smoke`, `S-039-31b-kfmaplite-smoke` | each arm tree | 1 each, `runs/_cohorts/smoke-te.txt`, concurrency 2 | not read for effect |

- **`31b-map`:** SequentialAgent of four steps on the 31B. `locate` starts `skills/codemap/scripts/locate.py` once.
  `draft` holds `read_file`, `edit_file`, `write_file` only and must edit from the map. `audit` starts
  `scripts/audit.py` once (changed symbols against their related sites; pure file reads). `finish` is the base agent
  with all six tools and the base prompt's rules, told to review the draft and decide each listed site.
- **`31b-maplite`:** `locate`, then the base agent with the base prompt, section 2 pointed at the map. It isolates the
  map from the draft restriction and the audit.
- **`kf` trees:** the same with `max_time_minutes` 9.9 (as `31b-kf-ctl`). Prompts keep the Kaggle wording.
- Validator on all four: the two errors `31b-base` has, plus the expected warnings for skill scripts, a tool-less
  step and a sub-agent holding `submit_patch`.
- The control is reused (R-038's reasoning; same day, same GPU type). Cohort and flags as R-037.
- Cost: about 16 × 2.3 = 37 Ada GPU-h plus two smokes.

## Readings (written before any job runs)

1. **Smoke gate, per arm** (a kill stops that arm; a failed smoke is fixed once, logged here, and re-run). Pass needs,
   in both smoke tasks: the task served; `locate.py` returned a map, not its fallback line; for `kfmap`, `audit.py`
   ran; and in at least one task a source edit exists before the last step starts (kfmap) or at all (kfmaplite).
2. **Served check** as R-037 reading 1.
3. **Fidelity**: R-037 reading 2 on kfctl applies; "not faithful" downgrades a promote here.
4. **Decision, each arm on its own** against kfctl ×8: `tools/paired_boot.py`, 79 tasks, 90% CI; wall ratio as R-037.
   - **Promote:** +2.0 or more, CI lower bound above 0, wall ratio 1.06 or less. Next: propose an upload of the
     Kaggle tree to the user. If both promote, the higher point estimate goes forward.
   - **Harm:** −1.5 or less. **Not kept:** anything else. No extension.
5. **Mechanism (reported).** Per arm, means per draw: empty patches; time-cap and call-cap tasks; tool call index of
   the first source edit; tasks where the draft step edited (kfmap); tasks where the finish step changed a second
   file or symbol after the audit (kfmap); mean task wall; and, from `tools/trace_vs_reference.py` classes if it
   runs on these draws, no-edit and partial-fix counts against kfctl.
6. **Draw-1 kill gate, per arm** (by hand; a kill cancels that arm's d2-d8 unread): fewer than 79 served after one
   re-run, or 25 or more empty patches, or a mean task wall above 452 s.

**Blind guess (not a reading).** Smoke passes first time: map 55%, maplite 70%. Promote: map 10%, maplite 8%. Harm:
map 35%, maplite 20%. Empty patches fall in map: 75%.

## Queued
- **R-039 smokes submitted 2026-11-25:** kfmap 67707, kfmaplite 67708. The 16 draws are submitted after reading 1 is applied.

## Reading 1 (smoke gate, applied 2026-11-25 from the traces): PASS, both arms

| | kfmap smoke | kfmaplite smoke |
|---|---|---|
| Tasks served | 2 of 2 | 2 of 2 |
| `locate.py` returned a map (not the fallback) | 2 of 2 | 2 of 2 |
| `audit.py` ran and listed sites | 2 of 2 | not in this arm |
| Source edit before the last step | 2 of 2 | not in this arm |
| Source edit at all | 2 of 2 | 2 of 2 |
| `locate.py` calls per task | 5 and 2 | 5 and 2 |
| Tool calls, task wall | 23 and 16; 390 s and 531 s | 7 and 18; 134 s and 311 s |

The smoke's resolved column was seen while reading the rows (4 of 4 task-runs); it is not a reading and two tasks say
nothing.

## Deviation (logged 2026-11-25, before any of the 16 draws is submitted)

- **What the smoke showed.** The map step started `locate.py` 2 to 5 times per task instead of once. Each repeat costs
  one of the 28 tool calls and puts a second copy of the map (about 5,000 characters) into the 32k context.
- **Change, all four trees.** `locate.py` now writes a marker inside the checkout's own metadata directory after it
  prints a map. A second start within 900 s prints one line (map already printed; reply `mapped`) instead of the map.
  The marker is not a source file, so it is not part of the patch. Checked on a scratch repository: first start prints
  the map, second prints the one line, and the working tree stays clean. Prompts are unchanged. The four trees validate
  as before.
- **No second smoke.** The gate passed, and a second smoke would wait about an hour for a GPU. Instead the first
  finished tasks of each arm's d1 are checked for this: a map on the first start, the one line on repeats. If the map
  is ever missing on a first start, that arm's draws are cancelled unread and the round file says so.
- **R-039 draws submitted 2026-11-25** (interleaved kfmap, kfmaplite d1..d8): 67714-67729, not held; they start as GPUs free up.

## Reading 6, kfmap (applied 2026-11-25, early; deviation logged before the cancel): KILL

- **Deviation.** The gate is written for the end of d1. It was applied at 66 of 79 rows: mean task wall 530.1 s (bar
  452 s), 17 empty, 66 served. The 13 unfinished tasks would need a mean of 55 s to bring d1 under the bar, and no
  task of this arm has finished that fast. Waiting would only hold 6 GPUs from R-038.
- **Kill.** kfmap d2-d8 (67716, 67718, 67720, 67722, 67724, 67726, 67728) are cancelled and not read. d1 runs to its
  end and is read for mechanism only.
- **Mechanism so far (60 traces, no solve counts looked at).** The draft step averaged 368 s and 11 `read_file` calls
  per task (the prompt allows three); 37 of 59 tasks ended at the time limit and 21 never reached the audit script.
  Removing the search tool did not make the first edit early: the model browsed with `read_file` instead.
- **Repeat guard (the pre-run deviation above).** In the first 8 finished tasks of the two d1 runs, every first start
  printed a map and the script was started once per task (twice in one task).

## Reading 6, kfmaplite (applied 2026-11-25 at the end of d1): KILL

- kfmaplite d1: 79 rows, 79 served, 16 empty (bar 25), mean task wall **456.1 s (bar 452 s)**. The wall bar is
  crossed, so the arm is killed. d3-d8 (67719, 67721, 67723, 67725, 67727, 67729) are cancelled unread. d2 (67717)
  had already finished; its solve count is not read (its wall, 441.9 s, and 17 empty were seen with the gate numbers).
- The arm could not have promoted in any case: its wall ratio against kfctl (385.6 s) is about 1.18, over the 1.06
  bar. R-038 d1 ran beside these jobs at 392.7 s, so the extra time is the arm's own and not node load.
- **Where the time went.** The map step took 38 s per task (4.5 model turns of about 9 s), and the agent that
  followed used as much time as the control uses for the whole task (384 s). The map did not replace the agent's own
  search: 18.4 tool calls per task against 19.7. Tasks at the time limit: 32 of 79 (control 15.5).

## Outcome: both arms killed at the d1 gate, not kept

The d1 runs of both arms are read below for mechanism only (exploratory; no decision rests on them).

## d1 mechanism (exploratory, 2026-11-25; one draw per arm, read after both kills)

"Control expects" is the mean kfctl ×8 solve count on the same tasks.

| Group | Tasks | Resolved | Control expects | Empty |
|---|---|---|---|---|
| kfmaplite d1, all | 79 | 31 | 30.38 | 16 |
| kfmap d1, rows written when read | 69 | 21 | 25.62 | 18 |
| kfmap: finishing step reached, draft took 180 s or less | 10 | 8 | 8.12 | 0 |
| kfmap: finishing step reached, draft took longer | 34 | 13 | 13.50 | 4 |
| kfmap: finishing step not reached | 25 | 0 | 4.00 | 14 |

- Where the whole pipeline ran (44 tasks), it solved what the control solves on those tasks (21 against 21.6). The
  map, the draft and the audit list neither helped nor hurt there.
- The arm's whole loss is the 25 tasks whose draft step used up the time.
- The map alone is neutral on solves in one draw and costs about 70 s per task.
