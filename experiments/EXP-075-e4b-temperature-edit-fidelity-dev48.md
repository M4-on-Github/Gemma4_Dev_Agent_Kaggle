# EXP-075 — Sampling temperature 1.0 -> 0.2 on the E4B single loop, read as edit-copy fidelity (dev-48, D-011 lever 1)

**Date:** 2026-11-12
**Type:** dev-48 GPU arm, one arm, one variable (`temperature` in `configs/sampling.yaml`), about 1.3 L4x4-h of the 30/week. Cost reference: EXP-038, the same tree at temperature 1.0 on the same 48 ids, ran **1.267 h** by its kernel log span (EXP-038 section 9, E8). Conditional worst case, a bound and not a forecast: 48 x 489.9 s + 444.8 s = 6.66 h (EXP-038 section 2.2). No upload.
**Cohort:** dev-48
**Ladder:** L4 without an L2 screen, by the lead's decision (`knowledge/plan.md`, 2026-11-12, inside the dev-48 approval of `knowledge/user-decisions.md` 85f31c3). Why n = 8 cannot read it: of the smoke-8 ids, 3 are gold-blocked in the sandbox (EXP-074 section 7) and EXP-038 has 0 empties among them (all 10 of its empties are outside smoke-8), so an empty-patch or failed-edit endpoint has nothing to read there. L1 is section 1 (desk check over the EXP-038 traces and the same-tree reruns on disk).
**Pre-registered:** this file is committed before the kernel push. Sections 3-5 are written blind and are not revised.
**Serves:** D-011 (diagnosis first), lever 1 of EXP-074 section 6 (edit application, opportunity E4). Base: `experiments/EXP-033/candidate-e4b`, the tree that ran as EXP-038 (5/48).
**Relates:** EXP-038 (the base draw), EXP-044 (X0 reran the EXP-038 zip on failed-edit-8; X added a re-read-then-copy bullet, killed), EXP-053 (a retry-rule bullet, dropped), EXP-074 (classes, opportunity), EXP-022 (temperature dead as a lever for the 31B; not tested on the E4B), EXP-009 (0.2 is still non-deterministic under TP=4 and continuous batching).

## 1. Why this, now (zero GPU)

### 1.1 What the empty patches are (desk check, `experiments/EXP-075/desk.py`)
EXP-038 ended empty on 10 of 48 tasks: `fastapi_13537`, `fastapi_13786`, `fastapi_14360`, `fastapi_14459`, `fastapi_14873`, `fastapi_15661`, `rich_3063`, `rich_3676`, `rich_3935`, `rich_4075`.
- `edit_file` outcomes on those 10 tasks: notfound 22, multi 11, argloss 5, same 1, applied 2.
- Dominant failure class per task: **notfound on 6**, multi on 1, argloss on 1, no tool call at all on 1 (`fastapi_13537`, tool-free, text-form calls only), and 1 applied edit to a non-source file later stripped (`rich_4075`).
- The notfound calls are copy errors, not invented code. All 22 came after a `read_file` of the same file. None is a contiguous copy of the file's lines: 15 of 22 skip file lines between two copied lines, and 20 of the 31 missing lines are near-copies of a file line (difflib ratio at least 0.85; a dropped token, a changed character). On 17 of 22 the target file holds at least half of the old_string's lines (all of them on 3, most on 14); on 5, no file of the snapshot holds most of them.
- Re-reading does not rescue it: 4 notfound calls came after a re-read of the file since the previous failure, and all 4 failed again. 5 of 22 resent the previous edit's arguments unchanged.
- Over all 48 tasks: 156 `edit_file` calls, 53 notfound (share **0.340**), 83 failed in any class, 13 identical repeats of the previous edit (share 0.083). The first `edit_file` applied on 28 of the 47 tasks that made one.

### 1.2 The candidate forms, judged against the dispatch
1. **`write_file` on the whole file after a failed edit, when the file is small.** Not buildable as a lever. The targets of the 10 empty tasks are 41 to 4630 lines long, only 2 are small, and one of those 2 is the wrong file (a script outside the package). A whole-file rewrite by the E4B would also carry the same copy errors over every line.
2. **A re-read of the exact lines before the retry.** Already tested and killed: EXP-044 arm X (row 6 fired, the line was dropped). Section 1.1 shows re-reads were made and failed 4 of 4.
3. **A guard against submitting an empty tree while time remains.** No harness key exists for it: `eval_config.yaml` admits only `timeout_seconds`, `max_tool_calls`, `max_time_minutes`, `max_turns` (`tools/submission_rules.py` EVAL_CONFIG_KEYS), and `submit_patch` accepts an empty diff. It could only be prompt text, an exhortation the dispatch rules out; the E4B already reads "An empty diff scores zero" in the base prompt.
4. **Lower sampling temperature.** Buildable, tool-native, no prompt text: one value in `configs/sampling.yaml`. The failure in section 1.1 is character-level copy drift from a text that was in the context, which is the error temperature acts on. **Chosen.**

**Value 0.2.** One arm, so the larger dose: a null at 0.2 says the copy errors are not sampling noise; a null at 0.6 would leave that open. 0.2 is the official sample value and the value the 31B shipped with before EXP-017. No E4B tree on disk has run at any temperature other than 1.0 (every `configs/sampling.yaml` under `experiments/` with an E4B model reads 1.0), so there is no dose reference.

**The risk the readings must catch.** At 1.0 the E4B recovers by drawing a different old_string; at 0.2 it may resend the same one (identical repeats) and spend the budget on it. EXP-044 X0 is the sign that draws matter: the same zip on 8 EXP-038 E tasks left 7 non-empty.

### 1.3 Noise: E is a per-draw state, not a property of the task (`experiments/EXP-075/noise.py`)
- Reruns of the same tree on shared ids: EXP-044-X0 (the EXP-038 zip on failed-edit-8, 7 of its ids E in EXP-038) left E on **7 of 8**; EXP-033-e4b (smoke-8) entered E on 2 of 8 that were not E in EXP-038. Pooled reruns: E_left 7 of 8, E_entered 2 of 8.
- So "EXP-038 E tasks that leave E" cannot read the lever: a rerun of the base would score about 7 of 8 by itself. It is reported (row R5), not read.
- And EXP-074's E opportunity of 4 is overstated as a lever count: in X0, `fastapi_14360`, `fastapi_14873` and `rich_3676` left E without resolving.
- The readable outcome is the **net empty count over 48**. Same-tree draws: EXP-038 10 of 48, EXP-033-e4b 2 of 8 (EXP-044-X0's 1 of 8 is excluded, its ids were chosen on failed edits). Pooled 12 of 56 = 0.214, Wilson 95% [0.127, 0.338]. Under the lower bound 0.127, P(at most 2 of 48) = 0.047 and P(at most 3) = 0.126; under 0.214, P(at most 5) = 0.039.
- The mechanism has its own noise: the notfound share is clustered by task. A task bootstrap of EXP-038 (20,000 resamples) gives 0.340 [0.238, 0.441]. Same-tree draws on other id sets read 0.412 (EXP-033-e4b, 7 of 17) and 0.458 (X0, 11 of 24). Two independent draws of 48 differ by about 0.07 at one standard deviation (about 0.05 per draw, times the square root of 2). Per-task "had a notfound edit" flips are large on reruns (yes to no 5 of 8, no to yes 3 of 8), so the per-task paired form is not used.
- Repeat share: 0.083 [0.037, 0.138] by the same bootstrap.

### 1.4 Ceiling
Temperature can plausibly reach only the 6 notfound-dominant empty tasks, and those only through a different draw. The best case leaves about 4 empties, inside the null band, so the outcome endpoint alone would most likely read inconclusive even when the lever works. That is why the primary endpoint is the call-level mechanism (section 3), and the empty count is the outcome row.

## 2. Design
- **Tree:** `experiments/EXP-075/candidate-t02/` = `experiments/EXP-033/candidate-e4b/` with one value changed: `configs/sampling.yaml` `temperature: 1.0 -> 0.2`, with a dated comment. `top_p` 0.95, `top_k` 64, `max_output_tokens` 8192, `thinking_budget` 4096, `include_thoughts` true, the prompt, `agent.yaml` and `eval_config.yaml` (240 / 28 / 8 / 80) unchanged. `diff -ru` must show the one line and the comment.
- **Arm id:** `EXP-075-t02`; kernel `rainm4/gemma4-exp075-t02`; notebook `notebooks/exp075_t02/`; 48 dev-48 ids, `N_TASKS = 48`, `MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"`, `RUN_GOLD_CONTROL = False`.
- **Pairing:** every endpoint is computed on the same 48 ids as EXP-038 (paired), not as two independent rates where a paired form exists.
- **Gate override, stated:** the packing gate at `max_time_minutes: 8` computes 18.00 h and fails. The zip is packed with `--skip-budget-gate --allow-warnings` (warning: `timeout_seconds` 240, VERIFY(Q2)) because it is a dev-48 measurement, not an upload. `plan.md` section 5.8 is not engaged: no E4B upload follows from this file without its own S-NNN and a cap inside the gate.
- **Limits.** (1) One draw. A positive is a draw-level difference, which section 4 sets above the measured draw-to-draw spread, not a proof. (2) Temperature acts on all tokens, thinking included, so a change in search or reading behavior is part of the treatment, not a confound to be removed; section 3 secondaries record it. (3) vLLM under TP=4 stays non-deterministic at 0.2 (EXP-009), so 0.2 is not greedy.

## 3. Endpoints, fixed in advance
All counts from `tools/analyze_traces.py` (`summary.jsonl`) and `experiments/EXP-075/desk.py --all --run EXP-075-t02` (classes from the harness strings, section 1.1 definitions), paired by id against EXP-038.

**Primary (mechanism).**
- **M:** notfound share of `edit_file` calls over the 48 tasks = notfound calls / all `edit_file` calls. Reference EXP-038 0.340 (53 of 156), bootstrap [0.238, 0.441].

**Outcome.**
- **Eo:** empty patches of 48 (`patch_empty`). Reference EXP-038 10; null 0.214 per task-run, Wilson [0.127, 0.338].

**Secondaries (recorded, read only where section 4 names them).**
- **A:** tasks whose first `edit_file` call applied, of tasks with an `edit_file` call. Reference 28 of 47 [21, 35].
- **Resolves**, paired with EXP-038: both, A only, B only, exact McNemar p. Recorded; not a decision row (5 of 48 base, MDE far above any plausible move).
- **R5:** of EXP-038's 10 E tasks, how many are not E in this arm (`noise.py EXP-075-t02`, E_left). Reported with the rerun reference 7 of 8; not read.
- **Class table:** EXP-074 classes (margin 5) for the arm, and the paired transition counts E, F, R, C, S.
- Failed `edit_file` calls in any class, multi and argloss counts, `n_calls`, mean and max wall, thinking tokens per step.

**Harm inputs.**
- **H1 lost resolves:** EXP-038 resolved 5: `fastapi_14301`, `fastapi_14463`, `requests_6644`, `rich_3006`, `rich_3905`. Lost = resolved in EXP-038 and not in the arm. Rerun reference: the same-tree reruns on disk held their shared resolves 2 of 2 (`fastapi_14301`, `rich_3006` in EXP-033-e4b); `requests_6644` has resolved in every run.
- **H2 identical repeats:** repeat share of `edit_file` calls (desk.py `repeat`, the previous `edit_file` call's arguments resent unchanged). Reference 0.083 [0.037, 0.138].
- **H3 text-form:** tasks with `n_text_form_calls` > 0, and `tool_free` tasks. Reference (the 2026-11-09 analyzer re-run on a copy of the EXP-038 run, `runs/EXP-075-base038/`): 3 tasks (6 calls), `tool_free` 1. The `action`-keyed JSON gap (harness-stack) applies to both runs alike.
- **H4 caps:** `time_cap_hit` and `calls_cap_hit` tasks. Reference 0 and 0.
- **H5 time:** mean task wall (reference 85.7 s, max 207.3 s) and the analyzer's projected hidden-run total (reference 2.86 h) against 11 h.
- **H6 empties up:** Eo itself, on the high side.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.
Rows are read in order; the first that fires governs, later rows are recorded.

| Row | Condition | Reading |
|---|---|---|
| 1 infrastructure | fewer than 48 rows in `task_results.jsonl`, or the run's model is not the E4B, or the embedded zip's sha256 is not the section 8 sha | **Not read.** Endpoints on the rows present are reported. A re-run is a new dispatch. |
| 2 harm | any of: H1 2 or more of the 5 lost; H2 repeat share above 0.16; H3 text-form calls on 6 or more tasks or `tool_free` on 3 or more; H4 3 or more tasks at a cap; H5 mean wall above 150 s or projected total above 11 h; H6 Eo 16 or more (P 0.038 under the 0.214 null) | **Harm. 0.2 is not kept on the E4B.** The clause that fired is named; other rows are recorded only. |
| 3 kill | M at or above 0.30 | **Copy fidelity is not set by sampling temperature at 0.2.** Lever 1 by sampling is dead; edit application on the E4B needs a form that is not a sampling knob (or has none, section 1.2). |
| 4 keep, mechanism and outcome | M at or below 0.20 and Eo at or below 2 | **Kept.** Temperature 0.2 becomes the E4B single-loop base for the next round. Fewer copy errors and fewer empties, each beyond the measured draw spread (M: 0.14 below the base, two draw SDs; Eo: P 0.047 under the null's lower bound). |
| 5 keep, mechanism only | M at or below 0.20 and Eo 3 or more | **The mechanism moved, the outcome is inside noise.** 0.2 is kept as the E4B base (the knob is free in time, no harm row fired), with no claim on empties or resolves. The next E-stage round is read against this tree. |
| 6 no decision | 0.20 < M < 0.30 | **No decision.** Inside two draw SDs of the base. Recorded; no second temperature arm is funded by this file. |

**Blind predictions (not readings):** M about 0.28, Eo about 8, A about 30 of 47, repeat share about 0.12, resolves 4 to 6, mean wall within 15 s of the base. Most likely row: 6, then 3.

## 5. What this does and does not license
- Row 4 or 5 licenses temperature 0.2 as the E4B base for later D-011 rounds. It licenses no upload (the E4B has no upload line here) and no change to the 31B `submission/` tree, where temperature was tested and read as noise (EXP-022).
- Row 3 closes sampling as the edit-application lever. It does not close edit application.
- No row licenses a statement about resolves; at 5 of 48 a McNemar contrast cannot read a plausible move.

## 6. Exact commands
```bash
python -I -X utf8 tools/analyze_traces.py runs/EXP-075-t02 --cap-minutes 8 --max-calls 28
python -I -X utf8 experiments/EXP-075/desk.py --all --run EXP-075-t02        # M, A, H2 (mechanism line)
python -I -X utf8 experiments/EXP-075/noise.py EXP-075-t02                   # R5 and the paired class table
python -I -X utf8 tools/run_forensics.py compare runs/EXP-038-e4b-dev48 runs/EXP-075-t02   # resolves 2x2
python -I -X utf8 tools/run_forensics.py forensics runs/EXP-075-t02
python tools/estimate_budget.py --eval-config experiments/EXP-075/candidate-t02/eval_config.yaml --results runs/EXP-075-t02/summary.jsonl --tok-s 116.63 --per-call-s 0
cp runs/EXP-075-t02/summary.jsonl experiments/EXP-075/summary.jsonl
```
If the download nests the run (`runs/EXP-075-t02/runs/<x>/`), the scripts' `run_dir` finds it; pass the nested path to the tools.

## 7. Defects in this pre-registration, logged after the fact
(none yet)

## 8. Built (below the line; nothing above changes)

---

- **Tree:** `experiments/EXP-075/candidate-t02/`, 4 files. `diff -ru experiments/EXP-033/candidate-e4b experiments/EXP-075/candidate-t02` shows one hunk in `configs/sampling.yaml`: `temperature: 1.0` -> `0.2` and the dated comment above it. Nothing else differs.
- **Validator** (`--strict`): `RESULT: INVALID (1 errors, 1 warnings)`; the error is the 18.00 h packing gate at 8 minutes, the warning `timeout_seconds` 240 (VERIFY(Q2)). Lint clean, instruction 3162 characters.
- **Zip:** `dist/EXP-075-t02.zip`, 2.5 KiB, 4 files (`agent.yaml`, `configs/sampling.yaml`, `eval_config.yaml`, `prompts/system.md`), sha256 `dca506d3f6b9011156ffe4a32ef067fd54ba54d633f44a2aa2aec09a348392a8` (re-checked with `sha256sum`, and the notebook's embedded base64 decodes to the same sha). Packed with `--skip-budget-gate --allow-warnings` (section 2); not an upload.
- **Notebook:** `notebooks/exp075_t02/kaggle_eval_l4x4.ipynb`; `TASK_IDS` = the 48 dev-48 ids (checked equal to `experiments/cohorts/dev-48.txt`), `N_TASKS = 48`, `EXP_ID = "EXP-075-t02"`, `MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"`, `RUN_GOLD_CONTROL = False`, `RUN_AGENT = True`.
- **Kernel metadata:** copied from `notebooks/exp038_e4b_dev48/kernel-metadata.json` (E4B model source `google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2`, the pinned docker image, the wheelhouse dataset and the competition source), `id` `rainm4/gemma4-exp075-t02`, `title` `gemma4-exp075-t02`, nothing else changed.
- **Not pushed.** The critic reviews this pre-registration first (the arm is above 1 GPU-h).

## Status
**BUILT, NOT PUSHED (2026-11-12); awaiting the critic's prereg review.** Kernel `rainm4/gemma4-exp075-t02` does not exist yet. Expected cost about 1.3 GPU-h (EXP-038 reference 1.267 h).
