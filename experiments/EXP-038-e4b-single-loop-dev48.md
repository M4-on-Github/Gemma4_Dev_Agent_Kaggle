# EXP-038 — the shipped single loop on the E4B over dev-48, paired with EXP-028 Arm R: the small-model reference and its time profile

**Date:** 2026-11-05
**Type:** dev-48 arm, one arm, one variable (the model); point estimate 0.88-1.24 L4x4-h, conditional worst case 6.66 h (section 2.2). *Amended 2026-11-05 after the critic prereg (143fba1): the critic's central estimate is 1.25-1.3 L4x4-h, and point A is withdrawn as a point (section 2.2).*
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

~~**The point range is 0.88-1.24 h. Its upper end is above the user's "about 1 hr" by about a quarter.**~~

*Amended 2026-11-05, after the critic prereg review (`experiments/EXP-038/critic.md`, 143fba1), fix 4. The table and the struck sentence above are kept as first written.*
- **Point A is withdrawn as a point.** Arm R hit a cap on 22 of the 40 dev-48 ids outside smoke-8 and on 1 of the 8 inside it (`cost_estimate.json`, key `after_critic_prereg_2026_11_05`). So smoke-8 is the easy part of dev-48, and its unscaled mean does not stand for the 48. A stays in the table as a low reference only.
- **The critic's central estimate is 1.25-1.3 GPU-h** [critic]. That equals an E4B mean task wall of 84.5-88.2 s at this kernel's 444.8 s overhead (same key). Point B (1.24 h) sits just below it. The critic's other scalings give 0.94-1.46 h, most of them 1.23-1.30 h.
- **The critic's probabilities** [critic, bootstrap over the 8 smoke-8 pairs], with the ratio-of-means estimator weighted above the mean-of-ratios one:
  - about 45% that the run goes above 1.34 h, which the critic gives as the room left under the 3.2 h ceiling in the lead's ledger;
  - about 25% that it goes above 1.5 h.

  | Estimator | P(> 1.34 h) | P(> 1.5 h) |
  |---|---|---|
  | Ratio of means | 0.35 | 0.17 |
  | Mean of ratios | 0.67 | 0.41 |

- **Scenario C** gets under 5% from the critic [critic, I]: all 8 E4B tasks ended by submit after 1 to 15 counted calls.
- **So the cost does not meet the user's "only 1 hr".** The full-48 run is expected at about 1.25 h, with about a one-in-four chance of exceeding 1.5 h. The 27-id option is in section 2.3.

**Scenario C, not a bound.** Assume the E4B hits the 28-call cap on every one of Arm R's 23 capped ids, at its measured 10.59 s per counted call (296.6 s per task), and the other 25 tasks cost the smoke-8 mean. That gives **2.41 h**.

The one piece of evidence against it: the one R-capped id in smoke-8 took the E4B 15 calls, not 28.

**Conditional worst case, a bound and not a forecast.** Every task at the 8-minute cap plus grading, at the largest capped wall seen (Arm R, 489.9 s), comes to 48 x 489.9 s + 444.8 s = **6.66 h**.
- The evidence against it: smoke-8 capped 0 of 8, and the largest E4B wall seen is 90.7 s.
- Even this is not a hard bound. The session timeout is not a per-task hard stop: one EXP-028 RH task ran 751.9 s at the 8-minute cap.

**Increments.**
- Each task that runs to the time cap instead of the smoke-8 mean adds 0.12 h.
- Each task that runs to 28 calls instead adds 0.067 h.

**Unfunded.** A re-run after a crash is not funded by this pre-registration (section 4, row 0).

### 2.3 Option declined: the 27 informative ids (added 2026-11-05, after the critic prereg)

The critic offered running only the 27 informative ids, about 0.75 h (dev-48 minus EXP-036's 15 gated and 6 constant ids; `cost_estimate.json` key `after_critic_prereg_2026_11_05.informative27`). The user declined it and approved the full 48 instead (section 8). Not built.

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
| E7 | Projected hidden-set hours at 120 tasks | ~~`estimate_budget.py --results`; cross-check: mean task wall x 120 / 3600 + this kernel's measured overhead (log end minus the task wall sum)~~ *Amended 2026-11-05 (critic fix 2):* mean `wall_s` x 120 / 3600 + this kernel's measured overhead (log end minus the task wall sum), in hours, read against about 10.5 h. `estimate_budget.py --results` is recorded under E9, not read | ~~10.04 h~~ 10.07 h restated (Arm R's 297.4 s mean and 555.5 s overhead, `cost_estimate.json`) |
| E8 | Kernel wall, for the GPU ledger | last kernel-log entry, in hours; the Kaggle figure if one is shown | 4.12 h |
| E9 | Recorded, not read | seconds per model turn, compactions, `n_edit_arg_loss`, `vLLM up`, decode tok/s, resolves by repo; *added 2026-11-05 (critic fix 2):* `estimate_budget.py --results` | |

*E7, amended 2026-11-05 after the critic prereg (143fba1), fix 2.* `estimate_budget.py --results` takes the larger of the measured wall and a decode estimate. On EXP-033 it gives a mean task of 2.91 min (5.82 h projected) against a measured 56.9 s, and 2.69 h even at `--tok-s 56.4` [critic, P3]. For a fast model it does not measure the clock, so it is recorded and not read. Row 2 reads E7 as amended in the table above.

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

*Fault row added 2026-11-05, after the critic prereg (143fba1), fix 4. It is applied before the two rows above; the first match governs.*

| Condition | Reading |
|---|---|
| **F.** Fewer than 48 rows in any pass. Or, if GOLD or BASE is re-run, it grades differently from EXP-036: GOLD not 43 of 48 (15 of 15 gated, the five unresolved ids being `httpx_3672`, `requests_7205`, `requests_7309`, `requests_7315`, `requests_7427`), or BASE not 1 of 48 (`requests_6644`) (`experiments/EXP-036/aggregates.json`) | **Re-grade fault, G not read.** Report the counts and the differing ids. Fixing the tool and re-running is a new CPU dispatch (0 GPU-h) |

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Rows are applied in order, and the first match governs. Row T is applied in addition to the governing row. Threshold arithmetic for E2 at n = 48 (exact two-sided McNemar, `cost_estimate.json`): p < 0.05 needs a split of at least 6-0, 7-0, 8-0, 8-1, 9-1, 10-1 or 10-2 for 6 to 12 discordant pairs; with 5 or fewer discordant pairs, no split reaches it. With R at 9 of 48 and an as-run ceiling of 28, most outcomes will read as "no difference detected". That is a statement about this test's power, not evidence that the two models are equal.

**No row licenses an upload by itself.** At most a row admits an E4B upload *proposal* for the small-model line under `plan.md` section 5.8. That proposal is the lead's S-NNN. It then needs the user's decision, a critic `prereg` review, and the user-written `approvals/S-NNN.txt` holding the zip's sha. Nothing here bears on the 31B LB lineage.

### 4.1 Readings rows

**Row 0. Blank or crash.**
- **Condition:** the kernel fails before the task loop, or fewer than 44 of 48 tasks have a `task_results.jsonl` row, ~~or 5 or more rows carry a non-empty `error`.~~
  - *Amended 2026-11-05, after the critic prereg (143fba1), fix 1:* or 5 or more rows carry a non-empty `error` that is not a harness cap string. The cap strings are those beginning `Agent exceeded session timeout` (as run: `Agent exceeded session timeout (8.0 min)`) or `Agent exceeded turns budget` (as run: `Agent exceeded turns budget (80 turns)`). Rows with a cap string are read under E3 and row T, not here. The first-written clause fired on Arm R itself: 10 of its 48 rows carry these strings (6 session timeout, 4 turns budget; `runs/EXP-028-armR/task_results.jsonl`). So it would have read a cap-bound E4B as a crash, and row T's cap-bound branch could never have been reached.
  - *Added 2026-11-05 (critic re-check):* a cap-string row whose `n_turns` is 0 counts as an error.
  - *Added 2026-11-05, before the push, with the user's 2.0 GPU-h approval (section 8):* or the kernel was cancelled under the section 8 stop rule, whatever number of rows survive. Such a run is read as truncated.
- **Reading:** infrastructure, not the model. Say which (model input, vLLM boot, harness error, Kaggle stop) from the log and the first failing row.
  - *Added 2026-11-05 (critic re-check):* a run cancelled under the section 8 stop rule is read as **truncated**, neither infrastructure nor a model reading. It is read as a crash instead only if the surviving output shows a failure before the task loop, or 5 or more errors counted under the clauses above among the surviving rows. Report the elapsed time at the cancel, the number of surviving rows, and their mean `wall_s` and capped count. No endpoint is read and row T is not applied. A re-run is priced from these figures, not from section 2.2.
- **Next step:** report to the lead. No re-run is funded by this file. A re-run is a new dispatch and needs the user's GPU approval, because the user's condition was about 1 GPU-h. Endpoints on the rows present are reported, not read. No E4B proposal.

**Row 0b. Grading anomaly.**
- **Condition:** rows are present (not row 0), but a C-022 constant task grades against its constant (requests_6644 unresolved, or one of the five resolved), ~~or a C-021 gated task resolves as run.~~
  - *Amended 2026-11-05, after the critic prereg (143fba1), fix 4:* or a C-021 gated task resolves as run and its stored patch (`runs/EXP-038-e4b-dev48/patches/<id>.patch`) does not itself create the missing module. "Creates the module" means that the patch adds a file whose path has a component named `inline_snapshot`, `inline_snapshot.py`, `dirty_equals` or `dirty_equals.py`.
  - A gated resolve whose patch does create the module is not a grader change. It is the agent vendoring on its own: it is counted in E2 as a real flip and named in the report.
- **Reading:** the grader differs from EXP-028's. E2 is not read until the anomaly is explained from `test_tail`.
- **Next step:** report the ids and tails to the lead. The other endpoints are recorded. No E4B proposal until it is explained.

**Row 1. The loop fails at scale.**
- **Condition:** not row 0 or 0b, and E5 is below 24 of 48 or E4 is above 10% of calls.
- **Reading:** the smoke-8 result (6 of 8 non-empty, 0 malformed) does not hold on dev-48. The E4B with the 31B prompt is not an upload candidate.
- **Next step:** the small-model question becomes a prompt or format fix for the E4B (state from the traces whether edits failed, never started, or calls were malformed). This goes to the lead's ranking. C-023 is not built on this loop until a fixed loop passes this row. No E4B proposal.

**Row 2. The time profile fails.**
- **Condition:** not rows 0 to 1, and E7 is above ~~11.0 h~~ 10.5 h.
  - *Amended 2026-11-05, after the critic prereg (143fba1), fix 2.* The threshold is the plan's rule of about 10.5 h (C-008, EXP-016 section 3), on E7 as amended in section 3.1: mean `wall_s` x 120 / 3600 plus this kernel's measured overhead. At the 444.8 s overhead seen on EXP-033, this fires at a mean task wall above 311.3 s (`cost_estimate.json`). `estimate_budget.py --results` is not read here.
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

*Row T's room, defined in full on 2026-11-05 after the critic prereg (143fba1), fix 3. The two branches above are kept as first written, and this definition governs what they report.*

**Sets.**
- U is the set of tasks at no cap: not `calls_cap_hit`, not `time_cap_hit`, and `n_turns` below 80 (E3's caps).
- The number excluded as capped is 48 minus the size of U. It is always reported.

**Per-task room.** For each task in U, 480 s minus `wall_s`.
- This is a lower bound: `wall_s` includes setup and grading, which are not on the session clock.
- Report its mean and its 10th percentile, by `statistics.quantiles(x, n=10, method="inclusive")[0]`.

**Total-clock room.** (10.5 h minus E7) x 3600 / 120 seconds per task. E7 is as amended in section 3.1, over all 48.
- This is the average extra time per task that the hidden-set clock admits under the plan's 10.5 h rule.
- Under the 10.5 h rule, 120 tasks allow 311.3 s per task on average at the 444.8 s overhead (`cost_estimate.json`).

**The binding room** is the smaller of the per-task room and the total-clock room, taken once at the per-task mean and once at the per-task 10th percentile.

**Also reported, over U:**
- headroom on calls: 28 minus `n_calls`, mean and 10th percentile;
- headroom on turns: 80 minus `n_turns`, mean and 10th percentile;
- seconds per turn: the `wall_s` sum divided by the `n_turns` sum.

**Both branches.** In the cap-bound branch the total-clock room is reported as well. Any extra-stage design is priced against the binding room, not against 480 s minus wall alone.

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

**Prediction restated 2026-11-05, after the critic prereg (143fba1), fixes 2 to 4.** The tables above are kept as first written. No E4B dev-48 trace exists yet. The arithmetic is in `cost_estimate.json`, key `after_critic_prereg_2026_11_05.prediction_arithmetic_by_E3_mean_s`.

**E3: unchanged.** Mean wall 75 s (range 50-150 s), capped 1 of 48.

**E7 under the amended definition: about 2.62 h.** The range is 1.79-5.12 h, from E3's 50-150 s. The first-written 2.6 h (1.8-5 h) agrees within rounding.

**E8 made consistent with E3 (critic P2): kernel wall about 1.12 h.** That is 75 s x 48 + 444.8 s.
- The range is 0.79-2.12 h, from E3's 50-150 s.
- The first-written 1.05 h (0.85-1.6 h) did not follow from E3 and is withdrawn.
- The top of the range is above the user's 2.0 GPU-h (section 8). The stop rule there covers it.

**The critic's figures, next to mine.** The critic's central estimate is 1.25-1.3 h, a mean of 84.5-88.2 s. It gives about 45% to more than 1.34 h and about 25% to more than 1.5 h (section 2.2).
- My 75 s is a judgement made before the critic's bootstrap, and it is kept as my prediction.
- For the cost decision, the critic's figures are the ones to use, because they come from a bootstrap over the 8 pairs.
- For a bound, use the scenario C and worst-case figures of section 2.2.

**Row T.** "Otherwise" is unchanged at 85%. The predicted binding room is the total-clock room:
- about 236 s per task at a 75 s mean, and 161-261 s over E3's range;
- against a per-task room of about 405 s at the mean.

So the total clock binds, as the critic said [I].

**Governing row: unchanged.**
- Row 0 / 0b stays at 7%. The cap-string fix matters only if many tasks cap, and I predict 1 of 48.
- Row 2 stays at 1%: at 10.5 h it needs a mean task wall above 311.3 s.

**Re-grade.** Fault row F at 5%. Conditional on not F, G is 0 or 1 of 15 at 65%, as first written.

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
7. *Logged 2026-11-05, from the critic prereg (`experiments/EXP-038/critic.md`, 143fba1, verdict needs-work).* Four text fixes are applied as dated notes, with the first-written text struck or kept in place. The tree, zip, cohort and notebook are unchanged.
   - Fix 1 is in row 0.
   - Fix 2 is in the E7 row and the note below the section 3.1 table, in E9 and in row 2.
   - Fix 3 is the room definition under row T.
   - Fix 4 is in four places: section 2.2 (the critic's central estimate and probabilities; point A withdrawn), section 4.2 (the restated prediction, with E8 = 1.12 h), row 0b (the gated clause narrowed) and section 3.3 (re-grade fault row F).
   - *Clarified 2026-11-05.* Two counts of "capped" now appear in section 4.1:
     - Row T's cap-bound test, 15 or more of 48, keeps its first-written rule: either cap, meaning `calls_cap_hit` or `time_cap_hit` (Arm R 23).
     - The set U in the room definition also excludes the turns cap (Arm R would be 24 excluded), so the room is measured only on tasks at no cap at all.
   - `cost_estimate.py` gained one output key, `after_critic_prereg_2026_11_05`. Every earlier key is unchanged: the re-run output was compared key by key with the committed JSON.
8. *Logged 2026-11-05.* The ledger arithmetic elsewhere ("1.86 + 1.24 = 3.10") used point B as if it were an upper end (critic, item 1). This file never stated B as a bound, but the 1.24 h figure handed to the lead was read that way.
9. *Logged 2026-11-05, before the re-grade push. This is a build defect, and no reading changes.* Section 3.3 names the EXP-036 builder with `--arm E4B=...` and the EXP-036 template, but that pair cannot build this run as written.
   - The template sets `EXP_ID = "EXP-036-regrade"` and `PASSES = ["R", "RH", "GOLD", "BASE"]` as fixed values, and the builder never rewrites them.
   - Built with only `--arm E4B=...`, the notebook would stop at its count assert, because it would look for an `R` pass that no `--arm` supplies.
   - **The fix.** `experiments/EXP-036/build_regrade_notebook.py` gained two optional flags, `--exp-id` and `--passes`. The builder writes them into the template's parameter cell only when they differ from the defaults. The template file is not edited.
   - **The defaults still reproduce EXP-036.** I rebuilt the EXP-036 notebook from `runs/EXP-028-armR/patches` and `runs/EXP-028-armRH/patches` and compared it with the untracked `notebooks/exp036_regrade/kaggle_regrade.ipynb`. Both have sha256 `73df67c8453bd2ac31abf77aa6f6d6dc59590666b92a59d76e90020310e9686e`, so they are byte-identical.
   - **This run uses** `--exp-id EXP-038-regrade --passes E4B,GOLD,BASE`, so GOLD and BASE are re-run and fault row F can be read in full.
   - **Unchanged from section 3.3:** the timeouts (240 s and 300 s), the 20000-character tail and the shims.
   - **Cosmetic.** The built notebook's markdown header still names EXP-036.

## 8. Built

Built 2026-11-05 with the section 6 commands. Committed by pathspec.

**Not pushed.** The critic `prereg` review comes first: the conditional worst case is above 1 GPU-h, and this arm is the section 5.8 gate for a small-model upload. The point estimate's upper end (1.24 h) is above the user's "about 1 hr", and the lead takes that to the user before any push.

**Critic fixes applied, 2026-11-05.** The critic `prereg` review (143fba1) was needs-work, with four text fixes and nothing to rebuild. They are applied as listed in section 7, item 7. The zip (`9de869bd2cd8853b72d653d06b9acef3e03794c8b588c26494435774dda11ac0`), the cohort (dev-48) and the notebook (`e58af838...`) are unchanged.

**The user's GPU approval and the stop rule, 2026-11-05, before the push.**

The user, verbatim (`knowledge/user-decisions.md`, 6fd7787): "2 hrs should be fine for full 48". This is read as: this run is approved at up to **2.0 GPU-h**. The user named a number for this arm, not a new ceiling for other work. The 27-id variant is declined (section 2.3).

Against 2.0 h:
- The critic's central estimate is 1.25-1.3 h, with about 25% above 1.5 h.
- The only figure above 2.0 h in section 2.2 is scenario C (2.41 h), which the critic puts under 5%.
- The 6.66 h conditional worst case is above it too.

**Nothing in the kernel enforces 2.0 h.**
- `notebooks/kaggle_eval_l4x4.py` has no total-wall or deadline parameter. Its task loop runs every id in the cohort in order, with no time check.
- The only time limits are the per-task caps in `eval_config.yaml`: 8 min session timeout, 28 calls, 80 turns. The session timeout is not a hard per-task bound (harness-stack: one EXP-028 RH task ran 752 s).
- The notebook and zip are not rebuilt to add a deadline, so the cohort and the sha stay as committed.

**The rule, applied by people, not by the kernel:**
1. ~~The lead counts elapsed time from the push. That count includes queueing, so it runs ahead of GPU time, which is the safe side.~~
2. ~~If the kernel is not COMPLETE at 1.75 h elapsed, the lead tells the user then, and does not let the run go on past 2.0 h on its own reading.~~
3. Cancelling is the user's action in the Kaggle UI. No guarded agent command list in `.claude/agents/*.md` includes a cancel; the experimenter's commands are not prefix-guarded, and whether the Kaggle CLI has a cancel command is not verified here [I].
4. A kernel cancelled there is read as **truncated under row 0** (section 4.1, the clause dated 2026-11-05 for a cancellation under this rule), whatever number of rows survive. Endpoints on any rows that survive are reported, not read, and no E4B proposal follows.
5. A re-run needs a new GPU approval from the user.

Whether a cancelled Kaggle batch kernel keeps any of its output is unverified here. The download job reports what it finds.

*Amended 2026-11-05 (critic re-check):* the push record states the push time in UTC, and the lead's push report gives the user two clock times, push + 1.75 h and push + 2.0 h. The decision at push + 1.75 h is the user's, made from the Kaggle UI. If no one acts, the run continues to its end, 2.0 h is not enforced, and the exposure is section 2.2's tail (scenario C 2.41 h, conditional worst case 6.66 h).


### Push record, 2026-11-05

- **Push time: 2026-11-05 19:02 UTC.** Taken with `date -u` immediately after the push returned (19:02:40).
- **CLI output:** `Kernel version 1 successfully pushed.  Please check progress at https://www.kaggle.com/code/rainm4/gemma4-exp038-e4b-dev48`
- **Kernel:** `rainm4/gemma4-exp038-e4b-dev48`, version 1.
- **Status, checked once right after the push:** `KernelWorkerStatus.RUNNING`. Before the push, the status command returned a `kernels.get` permission error, because the kernel did not exist yet. No earlier version was running.
- **Source:** the pushed notebook is the one committed in ba3adaf. It is unchanged since: sha256 `e58af8388b5f5f6ba28a94ecca8abed14e1a36a79b202814f77f0926b22feb66`. The file text was committed at 7964379 and the plan at 1a695f3.
- **Zip:** `dist/EXP-038-e4b.zip` and the embedded `SUBMISSION_B64` both have sha256 `9de869bd2cd8853b72d653d06b9acef3e03794c8b588c26494435774dda11ac0`.
- **Checks before the push:**
  - `git status` was clean for `experiments/EXP-038*`, `notebooks/exp038_e4b_dev48` and `experiments/cohorts`.
  - `TASK_IDS` equals the 48 ids of `experiments/cohorts/dev-48.txt`, and `RUN_AGENT = True`.
  - The embedded `eval_config.yaml` is 240 / 28 / 8 / 80, Arm R's values.
  - The metadata has `enable_gpu` true and `enable_internet` false.
- **Clock times for the stop rule (section 8, critic re-check):**
  - push + 1.75 h = **2026-11-05 20:47 UTC**, the user's decision point, made from the Kaggle UI;
  - push + 2.0 h = **2026-11-05 21:02 UTC**.
  - If no one acts, the run continues to its end, and 2.0 h is not enforced.

## Status

~~BUILT, NOT PUSHED (2026-11-05). Awaiting the critic `prereg` review and the lead's word to the user on the 0.88-1.24 h point range.~~

**COMPLETE, ANALYZED (2026-11-05).** Section 9 has the results. The governing row is row 4, no difference detected: E2 is 4-0 against the E4B, p = 0.125. Row T takes its "otherwise" branch, with 225.6 s of room per task. The kernel ran 1.267 h by its log span. The follow-up is the section 3.3 CPU re-grade, a separate zero-GPU job, where fault row F and G are read. No row licenses an upload.

~~BUILT, NOT PUSHED (2026-11-05).~~ ~~**RUNNING since 2026-11-05 19:02 UTC**~~ (superseded by the line above): kernel `rainm4/gemma4-exp038-e4b-dev48` v1. The stop-rule clock times are 20:47 and 21:02 UTC. Next, a separate job when the lead reports COMPLETE: `kaggle kernels output rainm4/gemma4-exp038-e4b-dev48 -p runs/EXP-038-e4b-dev48/`, un-nest, then the section 6 analysis commands. The lines below are kept as written before the push.

- The critic's four text fixes are applied (section 7, item 7).
- The user has approved the full dev-48 at up to 2.0 GPU-h, with the section 8 stop rule.
- Next: the critic re-checks the fixes. Then the push is a separate job: directory `notebooks/exp038_e4b_dev48`, kernel `rainm4/gemma4-exp038-e4b-dev48`.
- ~~The lead starts the 1.75 h clock at the push.~~ The push record states the push time in UTC; the push report gives push + 1.75 h and push + 2.0 h (section 8, critic re-check).

---

## 9. Results, 2026-11-05. Section 4's readings applied as written and as amended before the push

**Governing row: row 4, no difference detected.** E2 is 4-0 against the E4B, exact McNemar p = 0.125. Row T takes its "otherwise" branch: 0 of 48 tasks hit a cap. The binding room is the total clock: 225.6 s per task.

**Sources.** Every number below comes from one of the commands listed here. None is worked out by hand.
- `python -I -X utf8 experiments/EXP-038/analyze_results.py` writes `experiments/EXP-038/results.json`. It holds ids, counts, error strings and config values only.
- `tools/analyze_traces.py runs/EXP-038-e4b-dev48 --cap-minutes 8 --max-calls 28` writes `summary.jsonl` and `aggregates.json`. Both are copied to `experiments/EXP-038/e4b/`.
- `tools/run_forensics.py forensics runs/EXP-038-e4b-dev48` and `tools/run_forensics.py compare runs/EXP-028-armR runs/EXP-038-e4b-dev48`.
- `tools/estimate_budget.py --results`, recorded under E9 only.
- The kernel log, `gemma4-exp038-e4b-dev48.log`.

The download nested one level and was un-nested (section 7, item 3). Traces and patches stay in `runs/`.

### 9.1 The run, the GPU figure, the stop rule

- Kernel `rainm4/gemma4-exp038-e4b-dev48` v1 was COMPLETE at the lead's status check, 20:36 UTC.
- **E8, the GPU figure for the ledger: 1.267 h.** This is the last kernel-log entry, at 4,559.9 s. It is counted the way Arm R's 4.12 h was: kernel hours on the 4x L4 machine, as a log span.
  - No Kaggle UI figure was seen, and queueing time is not included (section 7, item 4).
  - It is within the user's 2.0 GPU-h.
- **Overhead: 445.6 s.** This is the log end minus the task wall sum of 4,114.3 s. EXP-033 measured 444.8 s.
  - vLLM came up in 323.8 s.
  - The decode probe ran at 56.2 tok/s.
- **The stop rule (section 8) was not used.** The lead saw COMPLETE at 20:36 UTC, before the 20:47 UTC decision point. Nothing was cancelled.

### 9.2 Row 0, row 0b and fault row F

| Check (as amended) | Value | Fires? |
|---|---|---|
| Kernel failed before the task loop | no; vLLM up, 48 of 48 tasks ran | no |
| Rows in `task_results.jsonl` | 48 (threshold: fewer than 44); ids equal dev-48; every status `SUCCESS` | no |
| Errors that are not cap strings | 1: `fastapi_13537`, `Agent completed execution without calling submit_patch.` | no (fewer than 5) |
| Cap-string rows | 0 | — |
| Cap-string rows with `n_turns` 0, which count as errors | 0 | — |
| Errors counted under row 0 | 1 | no |
| Cancelled under the stop rule | no | no |

**Row 0 does not fire.**

**Row 0b does not fire.**
- Constant tasks: `requests_6644` resolved and the other five did not. That matches the constants.
- Gated tasks: 0 of the 15 resolved, so the vendoring clause was not needed.

**Fault row F cannot be checked yet.** F belongs to the section 3.3 CPU re-grade, which is a separate follow-up job. It has not run, so G is not read here.

### 9.3 Endpoints

| # | Result | Arm R |
|---|---|---|
| E1 | **5 of 48** resolved as run. Wilson 95% 4.5-22.2%, from `aggregates.json`. Section 3.2's caveat applies: the as-run ceiling is 28 of 48, and these rates are not compared with board scores | 9 of 48 |
| E2, 48 ids | both 5 / R only **4** / E4B only **0** / neither 39. Exact McNemar two-sided p = **0.125**; `run_forensics compare` agrees. The R-only ids are `fastapi_13537`, `fastapi_15589`, `fastapi_9753` and `rich_3067` | |
| E2, 27 informative ids | both 4 / R only 4 / E4B only 0 / neither 19, p = 0.125. These are the same four R-only ids. The 21 gated and constant ids are all concordant: `requests_6644` resolved in both arms, and none of the others resolved in either | 8 of 27 |
| E3 | wall mean **85.7 s**, median 82.0 s, p90 147.5 s, max 207.3 s (`rich_4070`). **Capped: 0** (0 at the call cap, 0 at the time cap, 0 at the turns cap). 47 tasks ended by `submit_patch` with no cap. Most calls in a task: 21; most turns: 26 | mean 297.4 s; 23 capped |
| E4 | **0** malformed out of 478 calls, free calls included | 1 call |
| E5 | **38 of 48** non-empty | 42 of 48 |
| E6 | median first-edit turn **6** (n = 47, `collect_forensics`). One task never edited: `fastapi_13537` | 14 (n = 44) |
| E7 | 85.7 s x 120 / 3600 + 445.6 s = **2.98 h**, read against 10.5 h | 10.07 h restated |
| E8 | **1.267 h** log span | 4.12 h |
| E9 (recorded, not read) | 6.85 s per turn (smoke-8: 6.0 s); 20 compactions; 9 `edit_file` argument losses. Resolved by repo: rich 2, fastapi 2, requests 1, httpx 0. `estimate_budget.py --results` reports a per-task mean of 3.88 min, a projected 7.77 h, p90 12.01 h, "cap hits 3" and VERDICT BLOCK. As amended in section 3.1 these figures are not read: they are the script's own model, and the run had 0 caps and a measured 85.7 s mean. `analyze_traces` projects 2.86 h, with a worst case of 16.00 h | |

### 9.4 The readings, in order

1. **Row 0 does not fire** (9.2).
2. **Row 0b does not fire** (9.2).
3. **Row 1 does not fire.** E5 is 38 of 48, not below 24. E4 is 0%, not above 10%.
4. **Row 2 does not fire.** E7 is 2.98 h, not above 10.5 h. The mean task wall is 85.7 s, against the 311.3 s threshold.
5. **Row 3 does not fire.** R only (4) is more than E4B only (0), but p = 0.125 is not below 0.05. Section 4 already noted that with 5 or fewer discordant pairs, no split can reach p < 0.05.
6. **Row 4 fires: no difference detected.**
   - The 48 ids cannot separate the two models. The split is 4-0 against the E4B, and the discordant ids are listed under E2.
   - The marginal counts, 9 against 5, are not read as an effect.
   - The result reflects the test's power with 4 discordant pairs. It is not evidence that the models are equal.
   - **Next step, as written: as row 3.**
     - An E4B upload proposal for the small-model line is *admissible*, not licensed. Section 5.8 is met: dev-48 has run, and E7 is 2.98 h.
     - Whether to make that proposal is for the lead and the user to decide. It still needs an S-NNN, a critic `prereg` and `approvals/S-NNN.txt`.
     - This arm becomes the E4B reference: C-023 and any later E4B design are read paired against it.
7. **Row T: the "otherwise" branch.** 0 of 48 tasks were capped by calls or time, below the 15 that would make the run cap-bound. The room is measured over U:

   | Quantity | Value |
   |---|---|
   | Tasks in U | 48 |
   | Excluded as capped | 0 |
   | Per-task room, 480 s minus `wall_s` (a lower bound) | mean 394.3 s, p10 332.5 s |
   | Total-clock room, (10.5 h minus E7) x 3600 / 120 | **225.6 s** |
   | Binding room, at the mean and at p10 | **225.6 s**. The total clock binds at both |
   | Call headroom (28 minus `n_calls`) | mean 19.1, p10 11.7 |
   | Turn headroom (80 minus `n_turns`) | mean 67.5, p10 60.7 |
   | Seconds per turn over U | 6.85 s |

   Any extra stage on this model, such as C-023 voting, is priced against 225.6 s per task on average. Neither the per-task room nor EXP-033's 423 s is the price.

**Did not fit a pre-registered row: `fastapi_13537`.** This is the one error that is not a cap string, and one of R's four R-only flips.
- The E4B ran 8 turns, 0 tool calls, 1,236 output tokens and a 19.6 s wall, with no edit and no submit.
- One task is below row 0's error threshold and below row 1's empty-patch threshold. It is reported here and governs nothing.

### 9.5 Predictions scored

| Endpoint | Predicted (section 4.2; restated where marked) | Observed | Held? |
|---|---|---|---|
| E1 | 5 of 48 (2-9) | 5 | yes, exact |
| E2 | R only 5 (2-8), E4B only 1 (0-3) | 4 and 0 | yes, both in their intervals |
| E3 mean | 75 s (50-150 s) | 85.7 s | in range; the point was low |
| E3 p90 / max | 150 s / about 300 s | 147.5 s / 207.3 s | p90 yes; max lower |
| E3 capped | 1 of 48 (0-5), call cap more often than time cap | 0 | count yes; which cap is untestable at 0 |
| E4 | under 2% malformed | 0% | yes |
| E5 | 36 of 48 (28-44) | 38 | yes |
| E6 | median 6 (4-9) | 6 | yes, exact |
| E7 | restated 2.62 h (1.79-5.12 h) | 2.98 h | in range; the point was low |
| E8 | restated 1.12 h (0.79-2.12 h); first-written 1.05 h (0.85-1.6 h), withdrawn | 1.267 h | in both ranges; both points low |
| Governing row | row 4 at 55% | row 4 | yes |
| Row T | "otherwise" at 85%; binding room about 236 s, total clock; per-task room about 405 s | "otherwise"; 225.6 s, total clock; 394.3 s | yes |

**My 75 s was low.** The observed mean is 85.7 s, so my 1.12 h kernel figure was also low against 1.267 h. Point A (0.88 h), which the critic had withdrawn, was further off.

**The critic's cost estimate held.**
- Its central 1.25-1.3 h, which is a mean task wall of 84.5-88.2 s, contains both the observed 1.267 h and the observed 85.7 s.
- Point B (1.24 h) was just under.
- The critic gave about 45% to a run over 1.34 h and about 25% to one over 1.5 h. Neither happened, but one run is a single draw, not a calibration test.
- Scenario C (2.41 h) did not occur: no task hit the call cap.

**The re-grade predictions** (F at 5%; G 0 or 1 of 15 at 65%) wait for the section 3.3 job.

### 9.6 What this licenses and what it does not

**Licensed:**
- EXP-038 as the E4B single-loop reference on dev-48;
- the dev-48 profile that `plan.md` section 5.8 requires before any E4B upload proposal (E7 2.98 h against the 10.5 h rule);
- the row T room of 225.6 s per task, for pricing any extra stage on the E4B.

**Not licensed:**
- an upload. No row licenses one, and an E4B proposal would go through the lead, the user, a critic `prereg` and `approvals/S-NNN.txt`;
- any claim that the E4B equals the 31B, since the test had only 4 discordant pairs;
- any board-score estimate;
- anything about the 31B lineage.

**Still to run:** the section 3.3 CPU re-grade, pre-registered as a separate zero-GPU job. Fault row F and G are read when it runs.
