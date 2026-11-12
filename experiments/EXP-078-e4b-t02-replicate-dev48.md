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
1. **2026-11-12, at analysis: the H2 threshold states no precision.**
   - Row 2 reads "repeat share above 0.16". The references in section 3 are given to three decimals (0.083, 0.093).
   - The result is 21 of 129 = 0.1628. That is above 0.16 as an exact fraction and at three decimals, and it rounds to 0.16 at two.
   - Section 9 applies the threshold to the exact fraction, which is the reading as written. One fewer repeat (20 of 129 = 0.155) would not fire.
   - Logged for the critic. The reading is not revised.

## 8. Built (below the line; nothing above changes)

---

- **Zip:** `dist/EXP-075-t02.zip`, not repacked. `sha256sum` reads `dca506d3f6b9011156ffe4a32ef067fd54ba54d633f44a2aa2aec09a348392a8`.
- **Reproduced from the committed LF blobs:** `git -c core.autocrlf=false archive HEAD experiments/EXP-075/candidate-t02`, packed with `--skip-budget-gate --allow-warnings`, gives the same sha `dca506d3...92a8`. `git ls-files --eol` shows `i/lf w/lf` on all four files.
- **Notebook:** `notebooks/exp078_t02r/kaggle_eval_l4x4.ipynb`, built with `tools/build_notebook.py --embed dist/EXP-075-t02.zip --username rainm4 --cohort experiments/cohorts/dev-48.txt --set EXP_ID='"EXP-078-t02r"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --set N_TASKS=48`.
  - `diff` against `notebooks/exp075_t02/kaggle_eval_l4x4.ipynb` shows one line, the `EXP_ID` assignment. So `TASK_IDS` (the dev-48 ids), `N_TASKS`, `MODEL_NAME`, `RUN_GOLD_CONTROL`, `RUN_AGENT = True` and the embedded zip are the same as EXP-075.
  - The embedded base64 decodes to sha `dca506d3...92a8`.
- **Kernel metadata:** written after the build, copied from `notebooks/exp075_t02/kernel-metadata.json` with only two changes: `id` `rainm4/gemma4-exp078-t02r` and `title` `gemma4-exp078-t02r`. `diff` shows the one line.
- **Not pushed at build.** The critic re-checked this file first (verdict ready, 2d42b07), and the lead then released the push (D-011 process line).
- **Pushed 2026-11-12, about 08:22 UTC, kernel `rainm4/gemma4-exp078-t02r` version 1**, from the committed notebook directory `notebooks/exp078_t02r` (embedded zip sha `dca506d3...92a8`, pre-registered 2b351a3, built 49bbb69, released after the critic verdict 2d42b07). The first status check right after the push read `KernelWorkerStatus.RUNNING`. The push time is a clock stamp taken seconds after the push (08:22:25 UTC, from a file written then and listed with `ls --full-time`, local offset -0500), because `date` is not an allowed command for the screener; it is within about a minute of the push. **Stop-rule time (push + 2.0 h): 10:22 UTC** (section 4.2 clock).

## Status
~~**PUSHED (2026-11-12, about 08:22 UTC).** Kernel `rainm4/gemma4-exp078-t02r` version 1, status RUNNING at the first check. Stop time push + 2.0 h = 10:22 UTC. Expected cost about 1.3 GPU-h (EXP-075: 1.340 h). Next: when `kaggle kernels status rainm4/gemma4-exp078-t02r` says COMPLETE, the analysis job of section 6.~~
**ANALYZED 2026-11-12.** Row 2 (harm) fired, on its H2 clause: repeat share 21 of 129 = 0.163, above 0.16. 0.2 is not kept as the E4B single-loop base. Eo 3 is recorded only. 1.654 GPU-h. See section 9, and section 7 item 1.

## 9. Results, 2026-11-12. Section 4's readings applied as written

### 9.1 The run, the GPU figure, the stop rule
- Kernel `rainm4/gemma4-exp078-t02r` v1 was COMPLETE at the lead's check at 10:09 UTC, before the 10:22 UTC cancel time. The stop rule was not used.
  - It was not COMPLETE by the push + 1.5 h notice point of 09:52 UTC. A 5,955 s kernel pushed at about 08:22 UTC ended no earlier than about 10:01 UTC.
  - Whether the lead told the user at 09:52 is not recorded in this file and is unknown to the analysis. The output was downloaded into `runs/EXP-078-t02r/` (gitignored), and the nested run directory was moved up.
- **GPU figure for the ledger: 1.654 h**, the last kernel-log entry at 5,955.0 s, counted as in EXP-075 section 9.1. Queueing is not included.
  - Overhead: 445.2 s (log end minus a task wall sum of 5,509.8 s).
  - vLLM came up in 320.4 s.
  - Wheelhouse: 41 of 41 wheels in 51 s, Python 3.12.
- This is 0.35 h above the 1.3 GPU-h priced in the header, and 0.31 h above EXP-075's 1.340 h. The task wall sum rose 1,140.8 s over EXP-075. The two capped tasks of section 9.3 rose 1,174.9 s between them: `rich_3105` from 47.0 to 784.3 s and `rich_3067` from 45.3 to 482.9 s, paired by id in `summary.jsonl`.
- `summary.jsonl` is copied to `experiments/EXP-078/summary.jsonl` (`analyze_traces.py --cap-minutes 8 --max-calls 28`).

### 9.2 Row 1
| Clause | Value | Fires |
|---|---|---|
| Rows in `task_results.jsonl` | 48; 48 traces | no |
| Model | E4B: `gemma-4-e4b-it-qat-w4a16-ct` in the loaded `agent.yaml`, served from the E4B model input (log at 89.5 s) | no |
| Zip sha256 | The loaded tree `runs/EXP-078-t02r/agent/` repacks to `dca506d3...92a8` (`pack_submission.py --skip-budget-gate --allow-warnings`). The committed notebook's embedded base64 decodes to the same sha. Its four files have the same sha256 as `experiments/EXP-075/candidate-t02/`. | no |
| `runs/EXP-078-t02r/agent/configs/sampling.yaml` | `temperature: 0.2` | no |
| Infrastructure errors (`readings.py`) | 0: `llm_calls` 0 on 0 rows; `n_turns` 0 on 0 rows; other errors 0. There are 2 cap strings, read under H4, and 0 no-submit endings with turns. | no |
| Cancelled | no | no |

*Note (the critic's optional sentence, `experiments/EXP-078/critic.md`, "Pinned blind: 1 to 4 infrastructure rows"; added here as a results note, not above the line):* Eo, AL and H1 are counted over all 48 rows as written, with nothing subtracted. The infrastructure rows number 0, with no ids, so no row's recorded `patch_empty` enters Eo from an infrastructure failure.

### 9.3 Row 2, harm
| Clause | Value | Fires |
|---|---|---|
| H1, both-draw form | 0 of `fastapi_14301`, `fastapi_14463`, `requests_6644` lost. `readings.py --rerun EXP-077-base`: net ids 0, gross lost 0 against EXP-038's 5, 0 against EXP-077's 3 | no |
| H7 | `n_identical_repeats` total 26; 0 tasks at 8 or more; at most 5 on one task | no |
| **H2** | **repeat share 21 of 129 = 0.163** (`desk.py --all --run EXP-078-t02r`, `repeat` / `edit_calls`). Threshold: above 0.16 | **yes** |
| H3 | text-form calls on 0 tasks; `tool_free` 0 | no |
| H4 | time cap 2 (`rich_3105` 784.3 s, `rich_3067` 482.9 s); calls cap 0 | no (2 < 3) |
| H5 | mean wall 114.8 s (max 784.3 s); analyzer projection 3.83 h | no |
| H6 | Eo 3 | no |

**Row 2 fires, on the H2 clause.** The reading, as written: **harm. 0.2 is not kept as the E4B single-loop base.** Rows 3 to 5 are recorded only (section 9.4). The single-loop base stays at temperature 1.0.
- The H2 instrument is the one that gave the references: the same script and field give 13 of 156 = 0.083 (EXP-038), 14 of 139 = 0.101 (EXP-077) and 14 of 150 = 0.093 (EXP-075) in this session.
- The 21 repeats fall on 9 tasks: `fastapi_13786` 4, `rich_3067` 4, `rich_3063` 3, `rich_3521` 3, `fastapi_15800` 2, `rich_4070` 2, `fastapi_14953` 1, `fastapi_9753` 1, `rich_3061` 1. By the outcome of the repeated call: 16 notfound, 5 multi.
- The margin is one repeat: 20 of 129 = 0.155 would not fire. Section 7 item 1 records that the threshold states no precision. It is applied here to the exact fraction, as written.

### 9.4 Rows 3 to 5 and the secondary, recorded only
- **Eo = 3 of 48** (`patch_empty`): `rich_4075`, `fastapi_13207`, `rich_3067`. This is the band row 3 names (4 or fewer). Row 3 is not the governing row, because row 2 fired first. No keep is read.
- **AL = 4 of 48** (`n_edit_arg_loss` > 0): `fastapi_14609`, `fastapi_13207`, `fastapi_15800`, `rich_3067`, one arg-loss call each. Under row 2 the secondary is "any, under rows 1 or 2: recorded only". It would otherwise read as "2 or more, not replicated on this draw".

### 9.5 Recorded only (section 3)
- **M** = 35 of 129 = 0.271. **M over non-repeat calls** = 19 of 108 = 0.176 (`desk.py`).
- **Failed share** of `edit_file` calls: 49 of 129 = 0.380. By outcome: ok 80, notfound 35, multi 10, argloss 4.
- **A, the first edit applied:** 40 of 48. All 48 tasks made an `edit_file` call.
- **Phases reached** (`analyze_traces.py`): SUBMIT 46, VERIFY 1 (`rich_3105`), EDIT 1 (`rich_3067`); `submit_patch` on 46 of 48.
- **The stage table:** EXP-074 divergence-stage classes (`experiments/EXP-078/pair4.py`, margin 5), E3 F10 R12 C10 S13.

  | Against | Same class | E left, entered | F left, entered | R left, entered |
  |---|---|---|---|---|
  | EXP-038 | 32 of 48 | 9, 2 | 5, 2 | 0, 6 |
  | EXP-077 | 30 of 48 | 7, 1 | 3, 4 | 2, 6 |
  | EXP-075 | 33 of 48 | 4, 2 | 5, 2 | 1, 6 |

- **Resolves** (reported, not an endpoint): 5 of 48, `fastapi_14301`, `fastapi_14463`, `requests_6644`, `rich_3006`, `rich_3905`. Paired, exact McNemar:
  - against EXP-038: 5 both, 0 and 0 discordant, p 1.000;
  - against EXP-077: 3 both; EXP-078 only `rich_3006`, `rich_3905`; p 0.500;
  - against EXP-075: 4 both; EXP-075 only `fastapi_14873`, `rich_3067`; EXP-078 only `rich_3006`; p 1.000.

  `run_forensics.py compare` gives the same 2x2 tables.
- **Wall:** mean 114.8 s, median 76.25 s, p90 173.6 s. Analyzer projection 3.83 h; worst case 16.00 h at the 8-minute cap. Three tasks ran over 380 s: `rich_3105` 784.3 s (capped), `rich_3067` 482.9 s (capped), `rich_3480` 388.5 s. `run_forensics.py forensics`: `edit_file` holds 48.0% of agent wall (129 calls, median 10.80 s).

### 9.6 Predictions scored (blind, not readings)
| Prediction | Observed | Held |
|---|---|---|
| Eo about 7 | 3 | no (lower) |
| AL about 2 | 4 | no (higher) |
| M between 0.30 and 0.45 | 0.271 | no (lower) |
| Mean wall within 15 s of EXP-075 (91.0 s) | 114.8 s | no (+23.8 s) |
| Resolves 3 to 6, `requests_6644` held | 5, held | yes |
| Most likely row 4, then 5, then 3 | row 2 | no |

### 9.7 Post hoc, outside the readings (requested by the lead)
Four E4B single-loop draws on the same 48 ids. Nothing here is pooled or read; it is labelled post hoc.

| Draw | Temperature | Eo | AL | A, first edit applied | M | Resolves |
|---|---|---|---|---|---|---|
| EXP-038 | 1.0 | 10 | 6 | 28 of 47 | 53/156 = 0.340 | 5 |
| EXP-077 | 1.0 | 9 | 4 | 33 of 47 | 61/139 = 0.439 | 3 |
| EXP-075 | 0.2 | 5 | 1 | 37 of 48 | 57/150 = 0.380 | 6 |
| EXP-078 | 0.2 | 3 | 4 | 40 of 48 | 35/129 = 0.271 | 5 |

- Sources:
  - Eo, AL and resolves come from each run's `summary.jsonl`.
  - A and M come from `experiments/EXP-075/desk.py --all --run <run>`, which prints the A denominator as the tasks with an `edit_file` call.
- **Union of resolved ids over the four draws: 7.** They are `fastapi_14301`, `fastapi_14463`, `fastapi_14873`, `requests_6644`, `rich_3006`, `rich_3067`, `rich_3905` (`pair4.py`; its line reads "over the three runs", a fixed string in `experiments/EXP-077/pair.py`, but it is computed over the four `RUNS`).
- A pooled 0.2 Eo of 8 of 96 may be printed only as a post hoc figure (section 4.1). It is not read.

### 9.8 What this licenses
- Row 2's reading only: temperature 0.2 is not kept as the E4B single-loop base, and the base stays at 1.0.
- No statement that 0.2 lowers or raises empties. No statement on resolves. No upload, and no change to `submission/`.
- Section 5 lists no follow-up arm for row 2, and none is built here.
