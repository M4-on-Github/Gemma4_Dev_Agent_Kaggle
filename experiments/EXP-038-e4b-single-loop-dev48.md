# EXP-038 — the shipped single loop on the E4B over dev-48, paired with EXP-028 Arm R: the small-model reference and its time profile

**Date:** 2026-11-05
**Type:** dev-48 arm, one arm, one variable (the model); point estimate 0.88-1.24 L4x4-h, conditional worst case 6.66 h (section 2.2)
**Cohort:** dev-48
**Ladder:** L3 (dev-48). The claim passed its screen: EXP-033 (smoke-8, L2) row 3 fired. The loop functions on the E4B, 0 of 8 tasks were capped, and 6 of 8 patches were non-empty.
**Pre-registered:** this file, the cost script and its output, the zip's recorded sha and the notebook are committed before the push. Sections 2-5 are written blind and are not revised; results are appended as a new section.
**Serves:** D-005 Stage 1b ("E4B single loop on dev-48: the small-model reference and its time profile", about 1 GPU-h). The user approved option (c) on 2026-11-05: "yea if it is only 1 hr of GPU go with c." (`knowledge/user-decisions.md`).
**Supersedes / relates:**
- EXP-033: the screen, the same tree, smoke-8.
- EXP-028 Arm R: the pairing reference, same 48 ids, same eval_config, the 31B.
- EXP-036: the CPU re-grade tool for the follow-up in section 3.3. C-021 and C-022 carry the grading caveats.
- C-023: voting agents on the E4B. The screener is desk-checking it. Nothing from it enters this arm, and this arm is its reference.

## 1. Why this, now

- `plan.md` section 5.8 forbids an upload of a config that has not run on dev-48 with its own projected worst case. No E4B config has a dev-48 profile, so no E4B upload for the small-model line can even be proposed until this arm runs. D-005 line 67 says the same.
- The 8-task screen cannot answer what this arm asks:
  - Resolves on smoke-8 are capped at about 4 informative tasks: three of the six constant tasks of C-022 are in smoke-8.
  - smoke-8 holds 1 of Arm R's 23 cap-hit tasks.

  So the time profile on the hard part of dev-48, the capped count and the paired comparison all need the 48. A second 8-task screen would only repeat EXP-033.
- EXP-033 measured, as 8 counts (EXP-033 section 9, `experiments/EXP-038/cost_estimate.json`):

  | Measure | E4B (EXP-033) | 31B Arm R, same 8 ids |
  |---|---|---|
  | Resolved | 2 of 8 | 2 of 8 (the same two ids) |
  | Mean task wall | 56.9 s (max 90.7 s) | 202.9 s |
  | Capped | 0 of 8 | 1 of 8 |
  | Malformed calls | 0 of 43 | 0 of 132 |
  | Non-empty patches | 6 of 8 | |
  | Model turn | 6.0 s | 10.7 s |
  | vLLM up | 322.9 s | 396.5 s on dev-48 |

  On the E4B, fastapi_14605, the one Arm R task that hit the 28-call cap, ended by submit after 15 calls.
- Arm R on dev-48 (`experiments/EXP-028/armR/summary.jsonl`):

  | Measure | Arm R |
  |---|---|
  | Resolved | 9 of 48 |
  | Mean wall | 297.4 s (p90 483.3 s, max 489.9 s) |
  | Capped | 23 of 48 (18 at the call cap, 6 at the time cap, one both) |
  | Non-empty patches | 42 of 48 |
  | Malformed calls | 1 |
  | First-edit turn | median 14 (n = 44, forensics) |
  | Projected hidden set | 10.04 h |
  | Kernel wall | 4.12 h |

## 2. Design

### 2.1 The arm

One arm, one variable against Arm R: the model.

**Tree.** `experiments/EXP-033/candidate-e4b/`, unchanged since d2c11da.
- `diff -r experiments/EXP-027/candidate-v24-at-8 experiments/EXP-033/candidate-e4b` shows only `model: gemma-4-31b-it-qat-w4a16-ct` -> `gemma-4-e4b-it-qat-w4a16-ct` and its dated comment.
- `eval_config.yaml` is byte-identical to Arm R's: timeout 240, 28 calls, 8 min, 80 turns.
- Sampling is unchanged: temperature 1.0, thinking_budget 4096, include_thoughts true, max_output_tokens 8192.
- The prompt is the 31B's v24 prompt, 3,162 bytes, and still says 28 calls and 8 minutes.
- Nothing is tuned for the small model, and no vendoring, voting or multi-agent text enters.

**Validator** (`--strict`): 1 ERROR, 1 WARN, both Arm R's.
- The ERROR is the 18.00 h packing gate formula (`120 x (8 + 1.0) min`). It is overridden with `--skip-budget-gate`, as for EXP-027/028/033. At 8 minutes the time rule is the measured dev-48 profile (EXP-032 row: "8 min ships only with its own dev-48 profile"), and this arm is that profile for the E4B.
- The WARN is `timeout_seconds=240 < 300`.

**Pack.** `dist/EXP-038-e4b.zip` (gitignored), 4 members: `agent.yaml` 472 B, `configs/sampling.yaml` 129 B, `eval_config.yaml` 94 B, `prompts/system.md` 3,162 B.
- sha256 **`9de869bd2cd8853b72d653d06b9acef3e03794c8b588c26494435774dda11ac0`**, the same as EXP-033's zip, because the tree is unchanged.
- **Reproduces from committed LF blobs.** `git ls-files --eol` gives `i/lf w/lf` for all four files, and each worktree file's sha256 equals its HEAD blob's.
- Packing from `git -c core.autocrlf=false archive HEAD experiments/EXP-033/candidate-e4b`, extracted to `out/exp038_repro/`, gives the same sha.
- Plain `git archive` under `core.autocrlf=true` writes CRLF and gives `24de9f1d...`. That is an export artifact, not the tree (harness-stack note).

**Notebook.** `notebooks/exp038_e4b_dev48/kaggle_eval_l4x4.ipynb`, built with the section 6 command. The parameter cell was read back:
- `EXP_ID = 'EXP-038-e4b-dev48'`;
- `RUN_PHASE0_CHECKS = True`, `RUN_GOLD_CONTROL = False`, `RUN_AGENT = True`;
- `MODEL_NAME = 'gemma-4-e4b-it-qat-w4a16-ct'`;
- `N_TASKS = 48`, `REPO_FILTER = ''`, `EXCLUDE_IDS = []`;
- compaction 15 / 14,336;
- `TASK_IDS` = the 48 ids of `experiments/cohorts/dev-48.txt`, in file order;
- the embedded `SUBMISSION_B64` decodes to sha256 `9de869bd...`.

The notebook's sha256 is `e58af8388b5f5f6ba28a94ecca8abed14e1a36a79b202814f77f0926b22feb66`.

**Kernel metadata.** `kernel-metadata.json` is `notebooks/exp033_e4b`'s with only `id` (`rainm4/gemma4-exp038-e4b-dev48`) and `title` changed. It keeps `model_sources` `google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2`, `machine_shape` NvidiaL4 and the pinned image.

**Notebook source.** It differs from the one Arm R ran (built at ae7b045) only by 1cd52f8: the model is taken from the zip, plus an assert that the model input exists. EXP-033 ran that version on the E4B without fault.

### 2.2 Cost

All numbers come from `python -I -X utf8 experiments/EXP-038/cost_estimate.py`, which writes `experiments/EXP-038/cost_estimate.json`. Its inputs are the EXP-033 kernel log and summary and Arm R's log and summary. All hours are log-span hours. The Kaggle quota figure runs a few minutes higher: queueing and image start are not in the log (EXP-033 section 7(e)).

**Inputs.**
- E4B kernel overhead = log end 900.3 s minus the task wall sum 455.5 s = **444.8 s**. Per-task wall includes setup and grading (`task_wall_s` wraps `evaluate_task`).
- Arm R's overhead, computed the same way, is 555.5 s, because the 31B boots slower.

**Point estimate (two points).**

| Point | Assumption | Task time | Kernel |
|---|---|---|---|
| A, unscaled | smoke-8 mean 56.9 s x 48 | 2,733 s | **0.88 h** |
| B, scaled | the same mean x Arm R's dev-48 / smoke-8 wall ratio (297.4 / 202.9 = 1.466; dev-48 is harder than smoke-8) | 4,007 s | **1.24 h** |

**The point range is 0.88-1.24 h. Its upper end is above the user's "about 1 hr" by about a quarter.**

**Scenario C, not a bound.** Assume the E4B hits the 28-call cap on every one of Arm R's 23 capped ids, at its measured 10.59 s per counted call (296.6 s per task), and the other 25 tasks cost the smoke-8 mean. That gives **2.41 h**.

The one piece of evidence against it: the one R-capped id in smoke-8 took the E4B 15 calls, not 28.

**Conditional worst case, a bound and not a forecast.** Every task at the 8-minute cap plus grading, at the largest capped wall seen (Arm R, 489.9 s), comes to 48 x 489.9 s + 444.8 s = **6.66 h**.
- The evidence against it: smoke-8 capped 0 of 8, and the largest E4B wall seen is 90.7 s.
- Even this is not a hard bound. The session timeout is not a per-task hard stop: one EXP-028 RH task ran 751.9 s at the 8-minute cap.

**Increments.**
- Each task that runs to the time cap instead of the smoke-8 mean adds 0.12 h.
- Each task that runs to 28 calls instead adds 0.067 h.

**Unfunded.** A re-run after a crash is not funded by this pre-registration (section 4, row 0).

## 3. Endpoints, fixed in advance

Computed by:
- `tools/analyze_traces.py <run> --cap-minutes 8 --max-calls 28`, giving `summary.jsonl` and `aggregates.json`;
- `tools/run_forensics.py forensics <run>`;
- `tools/run_forensics.py compare runs/EXP-028-armR <run>`;
- `tools/estimate_budget.py --eval-config experiments/EXP-033/candidate-e4b/eval_config.yaml --results <run>/summary.jsonl`;
- the kernel log.

`<run>` is the un-nested `runs/EXP-038-e4b-dev48/` (section 7, item 3).

### 3.1 Endpoints

| # | Endpoint | Definition | Arm R |
|---|---|---|---|
| E1 | Resolved of 48 as run, with Wilson 95% | `resolved` in `summary.jsonl`; the interval from `aggregates.json` | 9 of 48 |
| E2 | Paired 2x2 against Arm R | both / R only / E4B only / neither, exact two-sided McNemar on the discordant pairs, discordant ids listed (`run_forensics.py compare`) | |
| E3 | Wall profile | mean, p90, max of `wall_s`; tasks at each cap: calls (`calls_cap_hit`), time (`time_cap_hit`), turns (80, `n_turns >= 80`), and none (`submit_patch_called` and no cap) | mean 297.4, p90 483.3, max 489.9; 18 calls, 6 time, 23 either |
| E4 | Malformed calls | sum `n_malformed` / all calls including malformed | 1 call |
| E5 | Non-empty patch rate | `patch_empty` false, of 48 | 42 of 48 |
| E6 | First-edit turn | the median of `first_edit_turn` over all tasks that edited, and the count that never edited, from `run_forensics.collect_forensics` imported by a short analysis script (as EXP-028 did; the `forensics` CLI prints only per-outcome cohort medians). This is a turn index, not EXP-033's counted-call index | median 14, n = 44 |
| E7 | Projected hidden-set hours at 120 tasks | `estimate_budget.py --results`; cross-check: mean task wall x 120 / 3600 + this kernel's measured overhead (log end minus the task wall sum) | 10.04 h |
| E8 | Kernel wall, for the GPU ledger | last kernel-log entry, in hours; the Kaggle figure if one is shown | 4.12 h |
| E9 | Recorded, not read | seconds per model turn, compactions, `n_edit_arg_loss`, `vLLM up`, decode tok/s, resolves by repo | |

### 3.2 Caveats on the as-run number (C-021, C-022)

E1 is an as-run count on the Kaggle subprocess grader. It carries two known distortions.

**The grading gap (C-021).**
- 15 fastapi tasks are graded without `inline_snapshot` / `dirty_equals`.
- This tree does not vendor them, so it is expected to resolve 0 of the 15 as run, as R and RH did.

**Six constant tasks (C-022).**
- `requests_6644` always resolves.
- `httpx_3672`, `requests_7205`, `requests_7309`, `requests_7315` and `requests_7427` never do.

So the as-run ceiling for this tree is **28 of 48**: 27 informative tasks plus 1 free resolve. With the packages present it is 43 of 48.

The paired 2x2 (E2) is expected to be concordant on these 21 tasks. Any discordance there is reported as a grading anomaly (section 4, row 0b) and is not counted as an effect.

Absolute rates are reported with this caveat attached and are not compared with board scores.

### 3.3 Pre-registered follow-up, not part of this run

This is a zero-GPU CPU re-grade of this arm's 48 stored patches with the stand-ins present.

**How it runs.**
- Tool: the EXP-036 tool, `experiments/EXP-036/build_regrade_notebook.py` with `--arm E4B=runs/EXP-038-e4b-dev48/patches`, the EXP-036 template, `tools/regrade_patches.py --timeout 240 --verification-timeout 300`.
- Kernel: a CPU-only kernel whose metadata is copied from `notebooks/exp036_regrade`.
- Cost: 0 GPU-h, about 0.2-0.7 CPU-h. EXP-036's four passes took 0.72 h.
- It is a separate job after the analysis.
- If the builder requires them, it re-runs GOLD and BASE; their values are known from EXP-036.

**Its readings, written blind now.** Let G be the gated tasks resolved under the re-grade.

| Condition | Reading |
|---|---|
| G >= 2 of 15 | Some of the E4B's dev-48 failures are the grading gap, as for the 31B (R 3 of 15). Any E4B vendoring screen ranks on that. |
| G <= 1 | The gap costs the E4B little on dev-48, and vendoring is not a priority for the small-model line. |

Either way, the paired re-graded 2x2 against R's re-grade (12 of 48) is reported. Neither row licenses a tree change or an upload.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Rows are applied in order, and the first match governs. Row T is applied in addition to the governing row. Threshold arithmetic for E2 at n = 48 (exact two-sided McNemar, `cost_estimate.json`): p < 0.05 needs a split of at least 6-0, 7-0, 8-0, 8-1, 9-1, 10-1 or 10-2 for 6 to 12 discordant pairs; with 5 or fewer discordant pairs, no split reaches it. With R at 9 of 48 and an as-run ceiling of 28, most outcomes will read as "no difference detected". That is a statement about this test's power, not evidence that the two models are equal.

**No row licenses an upload by itself.** At most a row admits an E4B upload *proposal* for the small-model line under `plan.md` section 5.8. That proposal is the lead's S-NNN. It then needs the user's decision, a critic `prereg` review, and the user-written `approvals/S-NNN.txt` holding the zip's sha. Nothing here bears on the 31B LB lineage.

### 4.1 Readings rows

**Row 0. Blank or crash.**
- **Condition:** the kernel fails before the task loop, or fewer than 44 of 48 tasks have a `task_results.jsonl` row, or 5 or more rows carry a non-empty `error`.
- **Reading:** infrastructure, not the model. Say which (model input, vLLM boot, harness error, Kaggle stop) from the log and the first failing row.
- **Next step:** report to the lead. No re-run is funded by this file. A re-run is a new dispatch and needs the user's GPU approval, because the user's condition was about 1 GPU-h. Endpoints on the rows present are reported, not read. No E4B proposal.

**Row 0b. Grading anomaly.**
- **Condition:** rows are present (not row 0), but a C-022 constant task grades against its constant (requests_6644 unresolved, or one of the five resolved), or a C-021 gated task resolves as run.
- **Reading:** the grader differs from EXP-028's. E2 is not read until the anomaly is explained from `test_tail`.
- **Next step:** report the ids and tails to the lead. The other endpoints are recorded. No E4B proposal until it is explained.

**Row 1. The loop fails at scale.**
- **Condition:** not row 0 or 0b, and E5 is below 24 of 48 or E4 is above 10% of calls.
- **Reading:** the smoke-8 result (6 of 8 non-empty, 0 malformed) does not hold on dev-48. The E4B with the 31B prompt is not an upload candidate.
- **Next step:** the small-model question becomes a prompt or format fix for the E4B (state from the traces whether edits failed, never started, or calls were malformed). This goes to the lead's ranking. C-023 is not built on this loop until a fixed loop passes this row. No E4B proposal.

**Row 2. The time profile fails.**
- **Condition:** not rows 0 to 1, and E7 is above 11.0 h.
- **Reading:** the E4B at 8 min does not fit the hidden-set clock with the plan's margin. The cause will be in E3: which cap, and how many tasks.
- **Next step:** no E4B proposal at 8 min. The lead's options are a lower-cap arm, its own pre-registration, or none. E2 is reported, not read.

**Row 3. E4B worse than R, detected.**
- **Condition:** not rows 0 to 2, and E2 has more R-only than E4B-only with exact McNemar p < 0.05.
- **Reading:** on dev-48 the E4B single loop resolves measurably fewer tasks than the 31B loop. It still functions and fits the clock, so it is the small-model reference.
- **Next step:**
  - An E4B upload proposal for the small-model line is *admissible* (section 5.8 is met: dev-48 run, projected hours from E7). Whether to make one is the lead's and the user's decision, with this deficit stated in it.
  - C-023 and any later E4B design are read paired against this arm.

**Row 4. No difference detected.**
- **Condition:** not rows 0 to 2, and E2 has p >= 0.05, in either direction or tied.
- **Reading:** the 48 ids cannot separate the two models. Report the split and the discordant ids. Do not read the marginal counts as an effect, whatever their order.
- **Next step:** as row 3. An E4B proposal is admissible but not licensed, and this arm is the E4B reference.

**Row 5. E4B better than R, detected.**
- **Condition:** not rows 0 to 2, and E2 has more E4B-only than R-only with exact McNemar p < 0.05.
- **Reading:** unexpected. Suspect a grading or harness difference before any model effect. Check each E4B-only flip's `test_tail` and trace for a grader-side cause, and check the notebook-source difference of section 2.1.
- **Next step:** report to the lead with the flips checked. An E4B proposal is admissible as in row 3. Any reading for the 31B main-track lineage is the lead's, and needs a replication first. No 31B change follows from this row.

**Row T. Time profile, applied in addition to rows 3 to 5.**
- **Cap-bound** (E3 capped, either cap, in 15 or more of 48):
  - **Reading:** the E4B is cap-bound on the hard part of dev-48, as the 31B is (R 23 of 48).
  - **Next step:** any extra-stage design (C-023 voting) has no clock on those tasks. Its desk check must price it against E3's per-cap counts, not against EXP-033's 423 s.
- **Otherwise:**
  - **Reading:** report the mean and the 10th percentile of seconds left under 480 s, over tasks not at a cap, together with seconds per model turn. These are the room an extra stage would have on this model, in seconds and turns.

### 4.2 Predictions, written blind (before any E4B dev-48 trace exists)

| Endpoint | Prediction | Interval |
|---|---|---|
| E1 | 5 of 48 resolved | 80% interval 2 to 9 |
| E2 | R-only 5, E4B-only 1 | 80% intervals 2-8 and 0-3 |
| E3 | mean wall 75 s, p90 150 s, max about 300 s; capped 1 of 48, the call cap more often than the time cap | mean 50-150 s, capped 0-5 |
| E4 | malformed under 2% of calls | |
| E5 | 36 of 48 non-empty | 28-44 |
| E6 | median first-edit turn 6 | 4-9 |
| E7 | about 2.6 h | 1.8-5 h |
| E8 | kernel wall about 1.05 h | 0.85-1.6 h |

**E2 reading, conditional on the arm reaching rows 3 to 5.** p >= 0.05 at 63%, R better detected at 34%, E4B better detected at 3% (the governing-row figures below, renormalized).

**Governing row.**

| Row | Probability |
|---|---|
| 4 | 55% |
| 3 | 30% |
| 0 / 0b | 7% |
| 1 | 5% |
| 2 | 1% |
| 5 | 2% |

Row T: "otherwise" 85%.

**Follow-up re-grade.** G 0 or 1 of 15, at 65%.

## 5. What this does and does not license

**Can decide:**
- whether the E4B single loop, as shipped for the 31B, functions on dev-48 (rows 0 and 1);
- whether it fits the hidden-set clock at 8 min (row 2);
- whether the paired test detects a difference from the 31B (rows 3 to 5);
- how much clock an extra stage would have (row T).

It also produces the dev-48 profile that `plan.md` section 5.8 requires before any E4B upload proposal.

**Cannot decide:**
- the E4B's board score or its rank on the small-model line;
- any effect of a prompt written for the small model;
- vendoring or voting;
- anything about the 31B.

No row licenses an upload. Section 4 says what an upload still needs.

## 6. Exact commands

```
python -I -X utf8 experiments/EXP-038/cost_estimate.py
python tools/validate_submission.py experiments/EXP-033/candidate-e4b --strict
python tools/pack_submission.py --src experiments/EXP-033/candidate-e4b --out dist/EXP-038-e4b.zip --skip-budget-gate --allow-warnings
git -c core.autocrlf=false archive HEAD experiments/EXP-033/candidate-e4b | tar -x -C out/exp038_repro
python tools/pack_submission.py --src out/exp038_repro/experiments/EXP-033/candidate-e4b --out out/exp038_repro/repro.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed dist/EXP-038-e4b.zip --username rainm4 --cohort experiments/cohorts/dev-48.txt --set EXP_ID='"EXP-038-e4b-dev48"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp038_e4b_dev48/kaggle_eval_l4x4.ipynb
# then copy notebooks/exp033_e4b/kernel-metadata.json, changing only id and title (the builder does not write one there)
# push: a separate job, after the critic prereg review; kernel id rainm4/gemma4-exp038-e4b-dev48, directory notebooks/exp038_e4b_dev48
# after COMPLETE, a separate job (un-nest runs/EXP-038-e4b-dev48/runs/EXP-038-e4b-dev48/ first):
kaggle kernels output rainm4/gemma4-exp038-e4b-dev48 -p runs/EXP-038-e4b-dev48/
python -I -X utf8 tools/analyze_traces.py runs/EXP-038-e4b-dev48 --cap-minutes 8 --max-calls 28
python -I -X utf8 tools/run_forensics.py forensics runs/EXP-038-e4b-dev48
python -I -X utf8 tools/run_forensics.py compare runs/EXP-028-armR runs/EXP-038-e4b-dev48
python tools/estimate_budget.py --eval-config experiments/EXP-033/candidate-e4b/eval_config.yaml --results runs/EXP-038-e4b-dev48/summary.jsonl
# copy runs/EXP-038-e4b-dev48/summary.jsonl to experiments/EXP-038/e4b/summary.jsonl
```

## 7. Defects in this pre-registration, logged after the fact

None yet. Known at writing time:

1. Arm R ran an older notebook source (before 1cd52f8, model selection only, section 2.1).
2. `thinking_tokens` is null in `summary.jsonl` (EXP-033 section 7(a)), so the thinking budget is not an endpoint.
3. The kernel output nests one level (EXP-033 section 7(d)).
4. GPU-h is the log span unless Kaggle shows a figure (section 2.2).
5. The cost script reads only counts, and its output holds no task text.
6. Before the push and before any run, section numbers were aligned to the usual shape: predictions became 4.2, and licenses, commands, defects and built moved up one (5 to 8). E6 now names `collect_forensics` for the overall median. No reading, threshold or prediction text changed.

## 8. Built

Built 2026-11-05 with the section 6 commands. Committed by pathspec.

**Not pushed.** The critic `prereg` review comes first: the conditional worst case is above 1 GPU-h, and this arm is the section 5.8 gate for a small-model upload. The point estimate's upper end (1.24 h) is above the user's "about 1 hr", and the lead takes that to the user before any push.

## Status

BUILT, NOT PUSHED (2026-11-05). Awaiting the critic `prereg` review and the lead's word to the user on the 0.88-1.24 h point range.
