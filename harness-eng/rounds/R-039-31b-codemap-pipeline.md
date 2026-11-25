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
