# EXP-077 — A second draw of the EXP-038 E4B base on dev-48: the draw-to-draw spread of the mechanism and outcome counts

**Date:** 2026-11-12
**Type:** dev-48 GPU measurement, no variable: the EXP-038 zip unchanged, rerun on the same 48 ids with the same notebook cells. About 1.3 L4x4-h of the 30/week (EXP-038 ran **1.267 h** by its kernel log span, EXP-038 section 9; conditional worst case, a bound and not a forecast, 6.66 h, EXP-038 section 2.2). No upload.
**Cohort:** dev-48
**Ladder:** L4 measurement without an L2 screen, by the lead's decision (dispatch of 2026-11-12, accepting the critic's slot-2 recommendation in `experiments/EXP-075/critic.md`). Why n = 8 cannot read it: the quantity is the spread of dev-48 counts themselves (M over about 150 calls, empties over 48, the class counts over 48); an 8-task draw estimates a different, wider spread, and the 8-task reruns on disk are already the weak reference this run replaces (EXP-075 section 1.3).
**Pre-registered:** this file is committed before the kernel push. Sections 3 and 4 are written blind, final before this run's or EXP-075's result lands, and are not revised. It is pushed on the lead's release without its own critic `prereg` pass: the lead counts the critic's EXP-075 review and slot-2 recommendation as covering it.
**Serves:** EXP-075 (section 4.1 there: the spread s and the net form of H1); every later D-011 arm read on the E4B single loop against one base draw.
**Relates:** EXP-038 (the first draw of this zip on these ids), EXP-033-e4b and EXP-044-X0 (same zip, 8-id reruns: smoke-8 and failed-edit-8), EXP-074 (divergence classes), EXP-009 (vLLM under TP=4 is non-deterministic, so two draws at temperature 1.0 differ by construction).

## 1. Why this, now (zero GPU)
- EXP-075's rows set a keep at M <= 0.20, 0.14 below the base's 0.340, on a draw SD of 0.07 for the difference of two draws. That 0.07 is a task bootstrap inside one run (0.052 per draw, times the square root of 2), not a measured rerun. The critic regenerated it and flagged it unconfirmed: the same-id reruns read 18 of 41 against EXP-038's 23 of 59 on those ids, and smoke-8 went from 1 of 20 to 7 of 17 (`experiments/EXP-075/critic.md`).
- EXP-075's lost-resolve clause (H1) was inside noise because two of the five base resolves have one E4B draw each; a second draw of the base gives each resolve a hold count and lets H1 be read net.
- Empties and the divergence classes are per-draw states (EXP-075 section 1.3, EXP-076): the 8-task reruns put E per task-run at 12 of 56 and F at 15 of 56, but on selected or small id sets.
- Nothing cheaper measures it: trace mining cannot produce a second draw, and an 8-id rerun was the weak reference. This is the one run every later single-draw E4B arm leans on.

## 2. Design
- **Zip:** `dist/EXP-038-e4b.zip`, sha256 `9de869bd2cd8853b72d653d06b9acef3e03794c8b588c26494435774dda11ac0`, the zip EXP-038 ran (EXP-038 push record). Tree `experiments/EXP-033/candidate-e4b/`, unchanged since d2c11da; `configs/sampling.yaml` reads `temperature: 1.0`; `eval_config.yaml` 240 / 28 / 8 / 80. Not repacked for the run; the sha is reproduced from the committed LF blobs (section 8).
- **Arm id:** `EXP-077-base`; kernel `rainm4/gemma4-exp077-base`; notebook `notebooks/exp077_base/`; the 48 ids of `experiments/cohorts/dev-48.txt`, `N_TASKS = 48`, `MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"`, `RUN_GOLD_CONTROL = False`, `RUN_AGENT = True`. The notebook differs from `notebooks/exp038_e4b_dev48/kaggle_eval_l4x4.ipynb` in the `EXP_ID` line only; the kernel metadata in `id` and `title` only.
- **Pairing:** every spread is the paired difference on the same 48 ids, EXP-077 against EXP-038.
- **Gate override, stated:** as in EXP-038 the zip was packed with `--skip-budget-gate --allow-warnings` (18.00 h gate at 8 minutes; it is a dev-48 measurement, not an upload). `plan.md` section 5.8 is not engaged.
- **Concurrent arm.** EXP-075 (`rainm4/gemma4-exp075-t02`) is pushed beside it. If the two kernels share any Kaggle-side resource it is not visible here; each is a separate L4x4 session [I].
- **Limits.** (1) Two draws give one degree of freedom per spread. A spread is one realization of a difference, not an SD with an interval; a small value does not prove a small spread. (2) Kaggle's vLLM build, the image and the wheelhouse are pinned in the metadata as for EXP-038, but anything outside the pinned image that changed since 2026-11-05 is part of the draw and cannot be separated from it [I]. (3) Nothing here measures the spread of a variant tree; EXP-075 assumes the arm's draw spread equals the base's.

## 3. Endpoints, fixed in advance
All from `tools/analyze_traces.py` (`summary.jsonl`), `experiments/EXP-075/desk.py --all --run EXP-077-base` (mechanism line) and `experiments/EXP-075/noise.py EXP-077-base` (EXP-074 classes at margin 5, paired with EXP-038). Each is reported as the EXP-077 value, the EXP-038 value, and the paired difference.

**Primary.**
- **s = |M(EXP-077) - M(EXP-038)|**, M the notfound share of `edit_file` calls over the 48 tasks (desk.py `notfound_share`). EXP-038: 53 of 156 = 0.340. Bootstrap reference for the difference: 0.07 (0.052 per draw).

**Recorded spreads (no row reads them except as section 4 names).**
- **Eo**, empty patches of 48: EXP-038 10. Binomial reference for the difference of two draws at 0.214 per task-run: SD about 4.0 tasks [I].
- **Classes:** the E, F, R, C, S counts (lowercase included) per draw, EXP-038 E10 F13 R6 C9 S10, and the paired transition table; F_entered and F_left beside the 8-id rerun references (F_entered 3 of 15, F_left 0 of 1). F per task-run 15 of 56 = 0.27 gives a binomial SD about 3.1 tasks per draw [I].
- **A**, tasks whose first `edit_file` call applied, of tasks with one: EXP-038 28 of 47. Binomial reference for the difference about 4.8 tasks [I].
- **Repeats:** desk.py `repeat` (the previous edit resent unchanged; EXP-038 13 of 156) and `summary.jsonl` `n_identical_repeats` summed over the 48 (any tool; EXP-038 25, bootstrap [13, 40]) with the number of tasks at 8 or more (EXP-038 0).
- **M_nr**, the notfound share over non-repeat calls (desk.py `notfound_share_nonrepeat`): EXP-038 45 of 143 = 0.315.
- **Holds:** for each of the 5 EXP-038 resolves (`fastapi_14301`, `fastapi_14463`, `requests_6644`, `rich_3006`, `rich_3905`), resolved or not here; the number lost of the 5; and the paired resolve 2x2 over 48 (both, EXP-038 only, EXP-077 only).
- Failed `edit_file` calls in any class, mean and max wall, the analyzer's projected total, text-form calls and `tool_free` tasks, cap hits, no-submit endings.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.
Rows are read in order; the first that fires governs the reading of s. Rows 2 to 4 cover every value of s. No row makes a claim about resolves: a base draw resolving 3 or 8 of 48 is a draw, and the holds are inputs to EXP-075's H1, not a finding.

| Row | Condition | Reading |
|---|---|---|
| 1 infrastructure | fewer than 48 rows in `task_results.jsonl`, or the run's model is not the E4B, or the embedded zip's sha256 is not `9de869bd...1ac0`, or `runs/EXP-077-base/agent/configs/sampling.yaml` does not read `temperature: 1.0`, or 5 or more of the 48 rows are infrastructure errors, or the kernel was cancelled under the stop rule (section 4.1). An infrastructure error is a row whose `llm_calls` in `task_results.jsonl` is 0 or whose `n_turns` in `summary.jsonl` is 0, whatever its `error` string, or a row with a non-empty `error` that is neither a cap string (beginning `Agent exceeded session timeout` or `Agent exceeded turns budget`) nor the no-submit ending `Agent completed execution without calling submit_patch.` with `n_turns` above 0 | **Not readable.** Say which (model load, vLLM boot or death, harness error, Kaggle stop) from the log and the first failing row. A cancelled run is **truncated**: report the elapsed time, the surviving rows, their mean `wall_s` and capped count. Spreads on the rows present are reported, not read. EXP-075 takes its fallbacks (s = 0.07, gross H1). A re-run is a new dispatch. |
| 2 bootstrap not contradicted | s at or below 0.07 | **The measured spread is within the bootstrap.** EXP-075 reads M falls at 0.340 - 2s, and its fixed 0.20 governs. Later single-draw E4B arms on M may cite s with its one degree of freedom; the bootstrap is not confirmed by one difference, only not contradicted. |
| 3 spread above the bootstrap | 0.07 < s < 0.17 | **The within-run bootstrap understates the draw spread.** EXP-075's M falls (0.340 - 2s) is stricter than 0.20 and governs its keep rows. A later mechanism arm on one draw needs a fall of at least 2s to be read. |
| 4 M unreadable on one draw | s at or above 0.17 | **One dev-48 draw per arm cannot read the notfound share.** 0.340 - 2s is at or below 0: EXP-075 rows 4 to 6 cannot fire, and its row 7 records this. Later mechanism arms on the E4B need two draws per arm or a different endpoint. |

**H1 net, as EXP-075 reads it (EXP-075 section 4.1).** The holds feed EXP-075 only when row 1 did not fire. If this run lost 3 or more of the 5, EXP-075's net H1 is unreadable (it cannot reach 3), and that is recorded here and there.

**Blind predictions (not readings):** s about 0.05 (M between 0.29 and 0.40), Eo 6 to 13, F 10 to 16, A 24 to 32 of 47, resolves 4 to 6 with `requests_6644` held, `fastapi_14301` and `rich_3006` held, one of `fastapi_14463` and `rich_3905` lost, `n_identical_repeats` 15 to 40, mean wall within 15 s of EXP-038. Most likely row: 2, then 3.

### 4.1 Stop rule
- The kernel has no total-wall deadline (EXP-038 section 8; the notebook source is unchanged). The dispatch prices this run at about 1.3 GPU-h.
- **Cancel time: push + 2.0 h**, about 1.5 times the dispatch figure, with queueing counted in the elapsed time. The push record states the push time in UTC (`date -u` right after the push) and the clock times push + 1.5 h (the lead tells the user if the kernel is not COMPLETE) and push + 2.0 h (the cancel time).
- Cancelling is the user's action in the Kaggle UI; no agent cancels. If no one acts, the run continues to its end and the exposure is the conditional worst case 6.66 h. The 2.0 h is a figure for the lead to own; the user's 2.0 GPU-h of EXP-038 section 8 covered that arm only and is not cited as an approval here.
- A run cancelled at that point is read as truncated under row 1.

## 5. What this does and does not license
- It licenses the s that EXP-075 section 4.1 uses and the holds behind EXP-075's net H1, and a citable second base draw for later E4B arms on dev-48.
- It licenses no change to any tree, no upload, and no statement about the base's resolve rate beyond the two draws' counts.
- It does not license reading a variant arm against the pooled two-draw base: EXP-075 stays paired with EXP-038 as written there.

## 6. Exact commands
```bash
python -I -X utf8 tools/analyze_traces.py runs/EXP-077-base --cap-minutes 8 --max-calls 28
python -I -X utf8 experiments/EXP-075/desk.py --all --run EXP-077-base        # M, M_nr, A, repeats (mechanism line)
python -I -X utf8 experiments/EXP-075/noise.py EXP-077-base                   # classes and paired transitions vs EXP-038
python -I -X utf8 tools/run_forensics.py compare runs/EXP-038-e4b-dev48 runs/EXP-077-base   # resolves 2x2, holds
python -I -X utf8 tools/run_forensics.py forensics runs/EXP-077-base
python tools/estimate_budget.py --eval-config experiments/EXP-033/candidate-e4b/eval_config.yaml --results runs/EXP-077-base/summary.jsonl --tok-s 116.63 --per-call-s 0
cp runs/EXP-077-base/summary.jsonl experiments/EXP-077/summary.jsonl
```
If the download nests the run (`runs/EXP-077-base/runs/<x>/`), the scripts' `run_dir` finds it; pass the nested path to the tools. s is computed from the unrounded call counts of the two mechanism lines.

## 7. Defects in this pre-registration, logged after the fact
(none yet)

## 8. Built (below the line; nothing above changes)

---

- **Zip:** `dist/EXP-038-e4b.zip`, unchanged, sha256 `9de869bd2cd8853b72d653d06b9acef3e03794c8b588c26494435774dda11ac0` (re-checked with `sha256sum`).
- **Reproduced from the committed LF blobs** of `experiments/EXP-033/candidate-e4b/` (the four files written out with `git cat-file blob` into a gitignored `runs/` directory and repacked with `--skip-budget-gate --allow-warnings`): the same sha256 `9de869bd...1ac0`.
- **Notebook:** `notebooks/exp077_base/kaggle_eval_l4x4.ipynb`, built with `tools/build_notebook.py --embed dist/EXP-038-e4b.zip --username rainm4 --cohort experiments/cohorts/dev-48.txt --set EXP_ID='"EXP-077-base"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --set N_TASKS=48`. `diff` against `notebooks/exp038_e4b_dev48/kaggle_eval_l4x4.ipynb` shows the `EXP_ID` line only. Checked: `TASK_IDS` equals the 48 ids of `experiments/cohorts/dev-48.txt`, `N_TASKS = 48`, `RUN_AGENT = True`, `RUN_GOLD_CONTROL = False`, the model the E4B; the embedded `SUBMISSION_B64` decodes to sha256 `9de869bd...1ac0` and its `configs/sampling.yaml` reads `temperature: 1.0`. Notebook sha256 `07b3bcf9ae0953463ea850570ca4602dd8a717b7d4ab8a844ec39335faf2de72`.
- **Kernel metadata:** `notebooks/exp038_e4b_dev48/kernel-metadata.json` with `id` `rainm4/gemma4-exp077-base` and `title` `gemma4-exp077-base`, nothing else changed (E4B model source, the pinned docker image, the wheelhouse dataset, the competition source, GPU on, internet off).

## Status
**BUILT, NOT PUSHED (2026-11-12).** Released for push by the lead together with EXP-075. Expected cost about 1.3 GPU-h.
