# EXP-078 — A second draw of the temperature 0.2 E4B single loop on dev-48, read alone on empties (D-011 ranked arm 1)

**Date:** 2026-11-12
**Type:** dev-48 GPU replicate, no new variable. The EXP-075 zip runs unchanged on the same 48 ids with the same notebook cells. It costs about 1.3 L4x4-h of the 30/week: EXP-075 ran **1.340 h** and EXP-077 1.292 h, both measured as the last kernel-log entry. The conditional worst case is a bound, not a forecast: 6.66 h (EXP-038 section 2.2). No upload.
**Cohort:** dev-48
**Ladder:** L4 replicate without an L2 screen. The lead ranked it in D-011's second 2026-11-12 revision, on the critic's direction review (`experiments/EXP-074/critic.md`).
- n = 8 cannot read it. The primary counts empties over 48. EXP-038 had 0 empties among the smoke-8 ids, and 3 of those 8 are gold-blocked (EXP-075 section 1).
- Trace mining cannot produce a second draw.
**Pre-registered:** this file is committed before the kernel push. Sections 3 to 5 are written blind, before this run exists, and are not revised. The critic re-checks this file before the push; the arm is above 1 GPU-h (D-011, process line).
**Serves:** D-011 (the E4B single-loop base for later arms). It also serves the empties hypothesis that the critic filed post hoc on EXP-075 (`experiments/EXP-075/critic.md`, light review, "Empties (Eo 5)").
**Relates:**
- EXP-075, the first draw of this zip: Eo 5, 1 task with an arg-loss edit, M 0.380.
- EXP-038 and EXP-077, the two draws of the temperature 1.0 base: Eo 10 and 9, arg-loss tasks 6 and 4.
- EXP-009: vLLM under TP=4 is non-deterministic, so temperature 0.2 is not greedy and two draws differ.

## 1. Why this, now (zero GPU)
- **Empties: a post hoc hypothesis.** EXP-075 at temperature 0.2 had 5 empty patches of 48. The two base draws had 10 (EXP-038) and 9 (EXP-077). No EXP-075 row read Eo on that comparison.
  - Paired E flips against EXP-038: 8 left and 3 entered, McNemar p 0.23. Against EXP-077: 7 left and 3 entered, p 0.34 (the critic's figures).
  - The critic files the comparison as a hypothesis for a pre-registered replicate. No document may say that 0.2 lowers empties.
- **Why read it alone.** The first draw picked this endpoint, so pooling it with this draw would reuse the selection. A replicate Eo of 4 or fewer is the same event as a pooled count of 9 or fewer of 96 (5 + 4); the critic reads it on this draw alone.
- **What the first draw showed.** M did not fall at 0.2 (EXP-075 section 9.4 and the section 9.9 scope note). So a real fall in empties would have come through some other channel [I].
  - Tasks with an arg-loss edit (`n_edit_arg_loss` > 0 in `summary.jsonl`): 6 in EXP-038, 4 in EXP-077, 1 in EXP-075.
  - Those arg-loss tasks were empty on only 2 and 2 in the base draws (critic). The arg-loss count is therefore a blind secondary, not a mechanism that explains the empties.
- **Why no smaller form.** A keep at 0.2 changes the base every later single-loop arm is read against. The process figure this needs is the empties count, and only a dev-48 draw can produce one.

## 2. Design
- **Zip:** `dist/EXP-075-t02.zip`, sha256 `dca506d3f6b9011156ffe4a32ef067fd54ba54d633f44a2aa2aec09a348392a8`, the zip EXP-075 ran (EXP-075 section 8). It is not repacked.
  - Tree: `experiments/EXP-075/candidate-t02/`, unchanged since 979c35c. That is the EXP-033 single-loop tree with `temperature: 1.0 -> 0.2`; `eval_config.yaml` 240 / 28 / 8 / 80.
  - The sha is re-checked on the file and reproduced from the committed LF blobs (section 8).
- **Arm id:** `EXP-078-t02r`; kernel `rainm4/gemma4-exp078-t02r`; notebook `notebooks/exp078_t02r/`.
  - Task list: the 48 ids of `experiments/cohorts/dev-48.txt`, `N_TASKS = 48`.
  - Parameters: `MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"`, `RUN_GOLD_CONTROL = False`, `RUN_AGENT = True`.
  - The notebook differs from `notebooks/exp075_t02/kaggle_eval_l4x4.ipynb` in the `EXP_ID` line only. The kernel metadata differs in `id` and `title` only.
- **Read alone.** No endpoint is pooled with EXP-075. The base references are the two temperature 1.0 draws, 19 empties of 96 and 10 arg-loss tasks of 96. Each draw keeps its own paired tables against EXP-038 and EXP-077, recorded only.
- **Gate override, stated:** as in EXP-075, the zip was packed with `--skip-budget-gate --allow-warnings`. At 8 minutes the gate computes 18.00 h; this is a dev-48 measurement, not an upload. `plan.md` section 5.8 is not engaged.
- **Limits.**
  1. **Independence.** The 48 ids are the same ids as in the base draws, and rows 3 to 5 treat the draws as independent binomial samples. The E churn makes this roughly tenable: 7 of 10 E tasks left E between the two base draws, and 6 entered [I]. Shared-task effects would make the tail probabilities below optimistic.
  2. **Power is low.** At a true rate of 5/48, P(Eo at or below 4) is 0.43. The middle band 5 to 8 is the likeliest single outcome, at 0.51 (section 3). A no-decision result is therefore the expected outcome, not a failure.
  3. **No direct measurement.** The request temperature is not logged in the trace. Row 1 checks the loaded `sampling.yaml` copy in the run directory, as in EXP-075 (EXP-075 section 2, limit 4).

## 3. Endpoints, fixed in advance
All counts come from `tools/analyze_traces.py` (`summary.jsonl`) on `runs/EXP-078-t02r`, except row 1's error count, H7 and H1, which come from `experiments/EXP-075/readings.py`. The figures in this section come from `experiments/EXP-078/power.py`, a closed-form script that reads no data; they reproduce the critic's figures exactly.

**Primary: Eo, empty patches of 48** (`patch_empty` in `summary.jsonl`).
- Base reference: 19 of 96 over the two temperature 1.0 draws (10 + 9).
- At Eo 4 or fewer:
  - With the base rate 19/96 taken as known, the one-sided binomial P is 0.027.
  - With the base estimated, the one-sided Fisher P against 19 of 96 is 0.059.
- Power: P(Eo at or below 4) is 0.431 at a true rate of 5/48, the first 0.2 draw's rate.
- At that rate, P(5 to 8) is 0.512 and P(9 or more) is 0.057.
- Under the base rate 19/96: P(at or below 4) 0.027, P(5 to 8) 0.344, P(9 to 15) 0.610, P(16 or more) 0.019.

**Blind secondary: AL, tasks with an arg-loss edit** (`n_edit_arg_loss` > 0 in `summary.jsonl`).
- Base: 6 (EXP-038) and 4 (EXP-077), so 10 of 96. First 0.2 draw: 1.
- Read at 1 or fewer: one-sided P 0.034 under 10/96 as known, and Fisher 0.067 against 10 of 96.

**Harm inputs,** as in EXP-075 section 3 after its critic fixes, with one disclosed difference in H1.
- **H1 lost resolves, both-draw form. This differs from EXP-075.**
  - EXP-075's net form was "lost in the arm and held in EXP-077, 3 or more fires". By EXP-075's own section 4.1 that form is unreadable on any arm read against these base draws: EXP-077 lost 2 of EXP-038's 5.
  - Here the lost set is the 3 ids resolved in both base draws: `fastapi_14301`, `fastapi_14463`, `requests_6644`. `requests_6644` resolves with an empty patch on this grader and cannot be lost (harness-stack; C-022). So only 2 ids can be lost.
  - H1 counts how many of the 3 the arm did not resolve. This is the same count `readings.py --rerun EXP-077-base` prints as the net ids, since the net ids are the ids lost here and held in EXP-077.
  - Gross losses against EXP-038's 5 and against EXP-077's 3 are recorded beside it.
  - Hold reference: `fastapi_14301` and `fastapi_14463` resolved in EXP-038, EXP-077 and EXP-075 alike. `fastapi_14301` held 7 of 9 on the single-loop variant runs (the critic's count, EXP-075 critic).
- **H7, all-tool loops:** `n_identical_repeats` summed over the 48 tasks, and the number of tasks at 8 or more.
  - References: 25 (EXP-038), 22 (EXP-077), 25 (EXP-075). No task reached 8 in any of the three.
- **H2, identical edit repeats:** the repeat share of `edit_file` calls (`experiments/EXP-075/desk.py` `repeat`). References 0.083 (EXP-038) and 0.093 (EXP-075).
- **H3, text-form endings:** tasks with `n_text_form_calls` > 0, and `tool_free` tasks. EXP-075 had 0 and 0. The `action`-keyed gap in the analyzer (harness-stack) applies to every run alike.
- **H4, caps:** `time_cap_hit` and `calls_cap_hit` tasks. 0 and 0 in all three runs.
- **H5, time:** mean task wall and the analyzer's projected hidden-run total. References: 85.7 s and 2.86 h (EXP-038), 87.6 s and 2.92 h (EXP-077), 91.0 s and 3.04 h (EXP-075).
- **H6, empties up:** Eo itself, on the high side.

**Recorded only:**
- M and M over non-repeat calls (desk.py).
- The failed share of `edit_file` calls.
- A, the first edit applied.
- The EXP-074 class table (`experiments/EXP-077/pair.py` pattern), paired by id against EXP-038, EXP-077 and EXP-075.
- E flips against each of the three earlier runs.
- Resolves, paired with exact McNemar, against each of the three earlier runs. These are reported, not an endpoint.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.
Rows are read in order; the first that fires governs. Rows 3 to 5 cover every Eo from 0 to 15, and Eo of 16 or more fires row 2 (H6).

| Row | Condition | Reading |
|---|---|---|
| 1 infrastructure | Any of:<br>- fewer than 48 rows in `task_results.jsonl`;<br>- the run's model is not the E4B;<br>- the embedded zip's sha256 is not `dca506d3...92a8`;<br>- `runs/EXP-078-t02r/agent/configs/sampling.yaml` does not read `temperature: 0.2`;<br>- 5 or more of the 48 rows are infrastructure errors;<br>- the kernel was cancelled under the stop rule of section 4.2.<br><br>An infrastructure error is any of:<br>- a row whose `llm_calls` in `task_results.jsonl` is 0;<br>- a row whose `n_turns` in `summary.jsonl` is 0, whatever its `error` string;<br>- a row with a non-empty `error` that is neither a cap string (beginning `Agent exceeded session timeout` or `Agent exceeded turns budget`) nor the no-submit ending `Agent completed execution without calling submit_patch.` with `n_turns` above 0. | **Not read.**<br>- Say which failure it was (model load, vLLM boot or death, harness error, Kaggle stop), from the log and the first failing row. A dead server is not read as model harm (H6).<br>- A cancelled run is **truncated**: report the elapsed time, the surviving rows, their mean `wall_s` and capped count. No endpoint is read.<br>- Cap-string rows are read under H4. No-submit endings with turns are model behaviour, counted beside H3.<br>- A re-run is a new dispatch. |
| 2 harm | Any of:<br>- H1: 2 or more of the 3 both-draw ids lost. With `requests_6644` never lost, that means both `fastapi_14301` and `fastapi_14463` are lost.<br>- H7: `n_identical_repeats` total 50 or more, or 3 or more tasks at 8 or more each.<br>- H2: repeat share above 0.16.<br>- H3: text-form calls on 6 or more tasks, or `tool_free` on 3 or more.<br>- H4: 3 or more tasks at a cap.<br>- H5: mean wall above 150 s, or projected total above 11 h.<br>- H6: Eo 16 or more. | **Harm. 0.2 is not kept as the E4B single-loop base.** The clause that fired is named. Other rows are recorded only. |
| 3 keep | Eo 4 or fewer | **Replicated: the empties fall at temperature 0.2 holds on a second draw read alone.**<br>- Temperature 0.2 becomes the single-loop base for later D-011 arms. Each later arm states its references on this tree's draws (EXP-075 and EXP-078).<br>- No claim on resolves. No upload is licensed (section 5). |
| 4 no decision | Eo 5 to 8 | **No decision, recorded as untested at this power** (P 0.51 of landing here at a true 5/48, 0.34 at the base rate).<br>- The empties line ends here. No further 0.2 replicate is funded by this file.<br>- 0.2 is not adopted. The single-loop base stays at temperature 1.0.<br>- A second 5 reads here: no decision. |
| 5 not replicated | Eo 9 to 15 | **Not replicated. The first draw's 5 is filed as draw noise.**<br>- The empties line ends here. 0.2 is not adopted. The single-loop base stays at temperature 1.0. |

**Secondary reading (AL).** It is applied after the row that governs and does not change that row's decision in any band.

| AL | Reading |
|---|---|
| 1 or fewer | **The arg-loss fall at 0.2 recurs on this draw** (P 0.034 under 10/96).<br>- Recorded beside the governing row.<br>- Under row 3 it is reported as consistent with a fall in token-level argument loss, not as the mechanism of the empties: the base arg-loss tasks were empty on only 2 and 2.<br>- Under rows 4 and 5 it does not turn the reading into a keep. It is offered to the lead as a hypothesis for a top_p arm at temperature 1.0 (D-011, "also noted"). |
| 2 or more | **Not replicated on this draw.** Recorded; it feeds no row. |
| any, under rows 1 or 2 | Recorded only. |

**Blind predictions (not readings):**
- Eo about 7.
- AL about 2.
- M between 0.30 and 0.45.
- Mean wall within 15 s of EXP-075.
- Resolves 3 to 6, with `requests_6644` held.
- Most likely row: 4, then 5, then 3.

### 4.1 Pooling
None. EXP-075 and this run are read separately. A pooled 0.2 Eo over 96 may be printed as a post hoc figure only, labelled as such.

### 4.2 Stop rule
- The kernel has no total-wall deadline (EXP-038 section 8; the notebook source is unchanged). The run is priced at about 1.3 GPU-h; EXP-075 took 1.340 h.
- **Cancel time: push + 2.0 h,** with queueing counted in the elapsed time.
  - The push record states the push time in UTC (`date -u +%Y-%m-%dT%H:%M:%SZ` right after the push).
  - It also states two clock times: push + 1.5 h, when the lead tells the user if the kernel is not COMPLETE, and push + 2.0 h, the cancel time.
- Cancelling is the user's action in the Kaggle UI; no agent cancels. If no one acts, the run continues to its end and the exposure is the conditional worst case of 6.66 h. The 2.0 h is a figure for the lead to own.
- A run cancelled at that point is read as truncated under row 1.

## 5. What this does and does not license
- **Row 3:** temperature 0.2 becomes the E4B single-loop base for later D-011 arms.
  - It makes no claim on resolves.
  - It licenses no upload. The E4B has no upload line, and the tree runs at an 8-minute cap outside the packing gate.
  - It makes no change to the 31B `submission/` tree.
  - EXP-079, dispatched on the temperature 1.0 tree before this result, is not re-read or rebuilt because of it.
- **Rows 4 and 5:** they end the empties line for temperature 0.2. They say nothing about M, which EXP-075's scope note covers, or about other temperatures, top_p or top_k.
- **No row** licenses a statement that 0.2 lowers empties in general, or a statement about resolves.
- **The AL secondary** licenses at most a hypothesis.

## 6. Exact commands
```bash
kaggle kernels output rainm4/gemma4-exp078-t02r -p runs/EXP-078-t02r/     # then move the nested runs/EXP-078-t02r/ up
python -I -X utf8 tools/analyze_traces.py runs/EXP-078-t02r --cap-minutes 8 --max-calls 28
python -I -X utf8 experiments/EXP-075/readings.py EXP-078-t02r --rerun EXP-077-base   # row 1 errors, H7, H1 (net ids = the both-draw losses), gross
python -I -X utf8 experiments/EXP-075/desk.py --all --run EXP-078-t02r                 # H2, M, A (recorded)
python -I -X utf8 experiments/EXP-075/noise.py EXP-078-t02r                            # E flips and classes against EXP-038
python -I -X utf8 tools/run_forensics.py compare runs/EXP-038-e4b-dev48 runs/EXP-078-t02r
python -I -X utf8 tools/run_forensics.py compare runs/EXP-077-base runs/EXP-078-t02r
python -I -X utf8 tools/run_forensics.py compare runs/EXP-075-t02 runs/EXP-078-t02r
python -I -X utf8 tools/run_forensics.py forensics runs/EXP-078-t02r
python -I -X utf8 experiments/EXP-078/power.py                                         # the section 3 figures
cp runs/EXP-078-t02r/summary.jsonl experiments/EXP-078/summary.jsonl
```
Eo is the count of `patch_empty` true and AL the count of `n_edit_arg_loss` > 0, both over the 48 rows of `runs/EXP-078-t02r/summary.jsonl`.

## 7. Defects in this pre-registration, logged after the fact
None yet.

## 8. Built (below the line; nothing above changes)

---

- **Zip:** `dist/EXP-075-t02.zip`, not repacked. `sha256sum` reads `dca506d3f6b9011156ffe4a32ef067fd54ba54d633f44a2aa2aec09a348392a8`.
- **Reproduced from the committed LF blobs:** `git -c core.autocrlf=false archive HEAD experiments/EXP-075/candidate-t02`, packed with `--skip-budget-gate --allow-warnings`, gives the same sha `dca506d3...92a8`. `git ls-files --eol` shows `i/lf w/lf` on all four files.
- **Notebook:** `notebooks/exp078_t02r/kaggle_eval_l4x4.ipynb`, built with `tools/build_notebook.py --embed dist/EXP-075-t02.zip --username rainm4 --cohort experiments/cohorts/dev-48.txt --set EXP_ID='"EXP-078-t02r"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --set N_TASKS=48`.
  - `diff` against `notebooks/exp075_t02/kaggle_eval_l4x4.ipynb` shows one line, the `EXP_ID` assignment. So `TASK_IDS` (the dev-48 ids), `N_TASKS`, `MODEL_NAME`, `RUN_GOLD_CONTROL`, `RUN_AGENT = True` and the embedded zip are the same as EXP-075.
  - The embedded base64 decodes to sha `dca506d3...92a8`.
- **Kernel metadata:** written after the build, copied from `notebooks/exp075_t02/kernel-metadata.json` with only two changes: `id` `rainm4/gemma4-exp078-t02r` and `title` `gemma4-exp078-t02r`. `diff` shows the one line.
- **Not pushed.** The critic re-checks this file first, and the lead then releases the push (D-011 process line).

## Status
**BUILT, NOT PUSHED (2026-11-12).** It waits for the critic's prereg re-check and the lead's release. Kernel `rainm4/gemma4-exp078-t02r` does not exist yet. Expected cost about 1.3 GPU-h (EXP-075: 1.340 h). Next command after the release, run bare and unchained: the kaggle CLI kernel push with `-p notebooks/exp078_t02r`, then `date -u +%Y-%m-%dT%H:%M:%SZ` for the push record and the stop-rule clock times (section 4.2).
