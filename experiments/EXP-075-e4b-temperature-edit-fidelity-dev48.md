# EXP-075 — Sampling temperature 1.0 -> 0.2 on the E4B single loop, read as edit-copy fidelity (dev-48, D-011 lever 1)

**Date:** 2026-11-12
**Type:** dev-48 GPU arm, one arm, one variable (`temperature` in `configs/sampling.yaml`), about 1.3 L4x4-h of the 30/week. Cost reference: EXP-038, the same tree at temperature 1.0 on the same 48 ids, ran **1.267 h** by its kernel log span (EXP-038 section 9, E8). Conditional worst case, a bound and not a forecast: 48 x 489.9 s + 444.8 s = 6.66 h (EXP-038 section 2.2). No upload.
**Cohort:** dev-48
**Ladder:** L4 without an L2 screen, by the lead's decision (`knowledge/plan.md`, 2026-11-12, inside the dev-48 approval of `knowledge/user-decisions.md` 85f31c3). Why n = 8 cannot read it: of the smoke-8 ids, 3 are gold-blocked in the sandbox (EXP-074 section 7) and EXP-038 has 0 empties among them (all 10 of its empties are outside smoke-8), so an empty-patch or failed-edit endpoint has nothing to read there. L1 is section 1 (desk check over the EXP-038 traces and the same-tree reruns on disk).
**Pre-registered:** this file is committed before the kernel push. Sections 3-5 are written blind and are not revised. *Amended 2026-11-12, after the first commit (979c35c) and before the critic's review, the push and any result: section 1.3's X0 count corrected (8 of 8 ids were E, not 7); row 1 gains the loaded-config check and section 2 the matching limit; the keep rows require that failed edits overall and first-edit application are no worse than the base, and row 5 is capped at the base's 10 empties, with a new row 6 for the cases the old rows left open. The old row 6 is now row 7.* *Amended again 2026-11-12, critic fixes: after the critic's prereg review (36f7a27, 729c72f, needs-work, text fixes only) and before the push and any result. The five fixes and the two non-blocking items are applied where section 7 item 1 lists them; EXP-077 (a same-tree rerun of the EXP-038 zip, the critic's slot-2 recommendation) is pre-registered beside this file and section 4.1 states how its spread enters these rows. The tree, the zip `dca506d3...92a8` and the notebook are unchanged.*
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
- Reruns of the same tree on shared ids: EXP-044-X0 (the EXP-038 zip on failed-edit-8, all 8 of its ids E in EXP-038) left E on **7 of 8**; EXP-033-e4b (smoke-8) entered E on 2 of 8 that were not E in EXP-038. Pooled reruns: E_left 7 of 8, E_entered 2 of 8.
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
- **Limits.** (1) One draw. A positive is a draw-level difference, which section 4 sets above the measured draw-to-draw spread, not a proof. (2) Temperature acts on all tokens, thinking included, so a change in search or reading behavior is part of the treatment, not a confound to be removed; section 3 secondaries record it. (3) vLLM under TP=4 stays non-deterministic at 0.2 (EXP-009), so 0.2 is not greedy. (4) *Added 2026-11-12 (amendment):* the request's temperature is not logged in the trace or the kernel log. The path in the harness source: the submission's `generate_content_config` is checked against `swegemma/config.py`'s `GenerationConstraints` (no temperature range; defaults only for `max_output_tokens` and `thinking_budget`, which a submission value overrides) and passed by `google/adk/models/lite_llm.py` as `temperature` in the completion parameters. The notebook writes the extracted submission to the run directory (`runs/<run>/agent/`), the directory it hands to the harness as `submission_dir`; row 1 checks that copy. (5) *Added 2026-11-12 (critic fixes, non-blocking item):* wrong-file harm (more F tasks) is in no row and cannot be read here. On the same-tree reruns, F was entered on 3 of 15 task-runs that were not F in EXP-038 (F per task-run 15 of 56 = 0.27, SD about 3.1 tasks over 48), so a net F change against one base draw is inside the draw spread. The paired class table is recorded; EXP-077 records the base's own F spread beside it. (6) *Added 2026-11-12 (critic fixes):* the draw-to-draw SD behind rows 3 to 6 was a within-run bootstrap (0.052 per draw, about 0.07 for a difference of two draws), not a measured rerun. EXP-077 measures it; section 4.1 says how it replaces the 0.07.

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
- *Added 2026-11-12 (critic fixes):* **M_nr**, the notfound share over the `edit_file` calls that are not identical repeats of the previous edit (desk.py `notfound_share_nonrepeat`), so that a rise in resent edits cannot carry M by itself. Reference EXP-038 45 of 143 = 0.315 (EXP-033-e4b 4 of 14, EXP-044-X0 8 of 21). Recorded, not a decision row.

**Harm inputs.**
- **H1 lost resolves:** EXP-038 resolved 5: `fastapi_14301`, `fastapi_14463`, `requests_6644`, `rich_3006`, `rich_3905`. Lost = resolved in EXP-038 and not in the arm. Rerun reference: the same-tree reruns on disk held their shared resolves 2 of 2 (`fastapi_14301`, `rich_3006` in EXP-033-e4b); `requests_6644` has resolved in every run.
  - *Added 2026-11-12 (critic fixes, fix 1):* `requests_6644` cannot be lost (it resolves in every run, C-022), `fastapi_14463` and `rich_3905` have one E4B draw each, and on single-loop variant runs `fastapi_14301` held 7 of 9 and `rich_3006` 8 of 9 (the critic's counts). So 2 lost is inside the draw spread. Two forms are recorded: **H1 gross** = the number of the 5 lost in the arm; **H1 net** = the number of the 5 that the arm lost and EXP-077 held (an id-level difference, never a count difference). Section 4.1 says which form is read.
- **H7 loops over all tools** *(added 2026-11-12, critic fixes, fix 5)*: the sum over the 48 tasks of `n_identical_repeats` from `summary.jsonl` (identical tool calls, any tool), and the number of tasks at 8 or more. Reference EXP-038: 25 in total, on 14 tasks, at most 4 on one task; a task bootstrap (20,000 resamples) of the total gives [13, 40], SD 7.0 [I] (within-run, the same weakness as the 0.07). Pipeline trees reached 27 on 8 tasks (EXP-068-read, at most 6 on one task; EXP-071-anchor, at most 12 on one task).
- **H2 identical repeats:** repeat share of `edit_file` calls (desk.py `repeat`, the previous `edit_file` call's arguments resent unchanged). Reference 0.083 [0.037, 0.138].
- **H3 text-form:** tasks with `n_text_form_calls` > 0, and `tool_free` tasks. Reference (the 2026-11-09 analyzer re-run on a copy of the EXP-038 run, `runs/EXP-075-base038/`): 3 tasks (6 calls), `tool_free` 1. The `action`-keyed JSON gap (harness-stack) applies to both runs alike.
- **H4 caps:** `time_cap_hit` and `calls_cap_hit` tasks. Reference 0 and 0.
- **H5 time:** mean task wall (reference 85.7 s, max 207.3 s) and the analyzer's projected hidden-run total (reference 2.86 h) against 11 h.
- **H6 empties up:** Eo itself, on the high side.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.
Rows are read in order; the first that fires governs, later rows are recorded.

| Row | Condition | Reading |
|---|---|---|
| 1 infrastructure | fewer than 48 rows in `task_results.jsonl`, or the run's model is not the E4B, or the embedded zip's sha256 is not the section 8 sha, or *(amendment)* `runs/EXP-075-t02/agent/configs/sampling.yaml` does not read `temperature: 0.2`, or *(critic fixes, fix 2)* 5 or more of the 48 rows are infrastructure errors, or the kernel was cancelled under the stop rule of section 4.2. An infrastructure error is a row whose `llm_calls` in `task_results.jsonl` is 0 or whose `n_turns` in `summary.jsonl` is 0, whatever its `error` string, or a row with a non-empty `error` that is neither a cap string (beginning `Agent exceeded session timeout` or `Agent exceeded turns budget`) nor the no-submit ending `Agent completed execution without calling submit_patch.` with `n_turns` above 0 | **Not read.** Endpoints on the rows present are reported. A re-run is a new dispatch. *(critic fixes)* Say which (model load, vLLM boot or death, harness error, Kaggle stop) from the log and the first failing row, so a dead server is not read as model harm (H6). A run cancelled under section 4.2 is read as **truncated**: report the elapsed time at the cancel, the surviving rows, their mean `wall_s` and capped count; no endpoint is read. Cap-string rows are read under H4; no-submit endings with turns are model behaviour, counted beside H3 and reported (EXP-038 had 1, `fastapi_13537`, 8 turns, 4 model calls, the H3 `tool_free` reference). |
| 2 harm | any of: H1 ~~2 or more of the 5 lost~~ *(critic fixes, fix 1)* 3 or more of the 5 lost, in the form section 4.1 names (net when EXP-077 is readable, gross otherwise); H7 *(critic fixes, fix 5)* `n_identical_repeats` summed over the 48 tasks at 50 or more (twice the base's 25, above its bootstrap [13, 40]), or 3 or more tasks at 8 or more each (the base's maximum is 4); H2 repeat share above 0.16; H3 text-form calls on 6 or more tasks or `tool_free` on 3 or more; H4 3 or more tasks at a cap; H5 mean wall above 150 s or projected total above 11 h; H6 Eo 16 or more (P 0.038 under the 0.214 null) | **Harm. 0.2 is not kept on the E4B.** The clause that fired is named; other rows are recorded only. |
| 3 kill | M at or above ~~0.30~~ *(critic fixes, fix 4)* 0.33 (0.01 below the base's 0.340; a true fall of the keep's size, 0.14, would have to be overturned by about 1.9 draw SDs of 0.07 to read here) | **Copy fidelity is not set by sampling temperature at 0.2.** Lever 1 by sampling is dead; edit application on the E4B needs a form that is not a sampling knob (or has none, section 1.2). |
| 4 keep, mechanism and outcome | M at or below 0.20 *(critic fixes: and M falls, section 4.1)*, and *(amendment)* the failed share of `edit_file` calls in any class at or below the base's 0.532 (83 of 156) and A at or above 28, and Eo at or below 2 | **Kept.** Temperature 0.2 becomes the E4B single-loop base for the next round. Fewer copy errors and fewer empties, each beyond the measured draw spread (M: 0.14 below the base, two draw SDs; Eo: P 0.047 under the null's lower bound). |
| 5 keep, mechanism only | M at or below 0.20 *(critic fixes: and M falls, section 4.1)*, the failed share at or below 0.532, A at or above 28, and Eo 3 to 10 *(amendment: capped at the base's 10)* | **The mechanism moved, the outcome is inside noise.** 0.2 is kept as the E4B base (the knob is free in time, no harm row fired), with no claim on empties or resolves. The next E-stage round is read against this tree. |
| 6 shifted, not kept *(amendment)* | ~~M at or below 0.20, and the failed share above 0.532, or A below 28, or Eo 11 to 15~~ *(critic fixes, fix 3)* M at or below 0.20 and M falls (section 4.1), and (the failed share above 0.532, or A below 28, or Eo 11 to 15) | **Not kept.** Notfound fell, but the failures moved to another class, or first edits applied less often, or empties rose above the base: fewer copy errors did not become applied edits. Recorded; the clause that held is named; no further temperature arm is funded by this file. |
| 7 no decision | ~~0.20 < M < 0.30~~ *(critic fixes, fix 4)* none of rows 1 to 6 fired: 0.20 < M < 0.33, or M at or below 0.20 without M falling (section 4.1) | **No decision.** Inside two draw SDs of the base. Recorded; no second temperature arm is funded by this file. |

**Blind predictions (not readings):** M about 0.28, Eo about 8, A about 30 of 47, repeat share about 0.12, resolves 4 to 6, mean wall within 15 s of the base. Most likely row: 7 (written as 6 before the amendment), then 3.

### 4.1 How EXP-077 enters the rows *(added 2026-11-12, critic fixes; final before either result lands)*
EXP-077 reruns the EXP-038 zip unchanged on the same 48 ids (`experiments/EXP-077-e4b-base-rerun-dev48.md`). This file stays paired with EXP-038: every endpoint and threshold above is computed against EXP-038 as written, and no second comparison against EXP-077 is made. EXP-077 enters in two places only.
- ~~**EXP-077 is readable** when its own row 1 did not fire (not cancelled, not infrastructure) and its kernel is COMPLETE before this file's analysis. Otherwise both places below take their fallback, and this file is read without waiting further.~~
- *Amended 2026-11-12 05:55 UTC, after the push and before any result (section 7 item 2):* **this file is not analysed until EXP-077 is terminal** (COMPLETE, ERROR, or cancelled under its stop rule). EXP-077 is **readable** when it is terminal and its own row 1 did not fire; the fallbacks below apply only when it is terminal and its row 1 fired. The timing of the analysis therefore cannot choose between s and 0.07, or between net and gross H1.
- **The spread s.** s = |M(EXP-077) - M(EXP-038)|, the notfound shares of `edit_file` calls of the two base draws (desk.py `notfound_share`, unrounded call counts). It is one realization of the difference of two draws, one degree of freedom, and it replaces the bootstrap 0.07 literally (no floor: the fixed 0.20 in rows 4 to 6 already floors a small s). Fallback: s = 0.07.
- **M falls** (rows 4 to 7) means M(arm) <= 0.340 - 2s, where 0.340 is EXP-038's 53 of 156. With the fallback, 0.340 - 0.14 = 0.20, so the rows read exactly as before EXP-077 existed. If s is above 0.07, M falls is stricter than M <= 0.20 and governs; below 0.07 the 0.20 governs. If s is 0.17 or more, M falls needs M at or below 0 (0.340 - 2s <= 0), so in practice rows 4 to 6 cannot fire, and row 7 records that one draw per arm cannot read the mechanism at this spread.
- **H1.** If EXP-077 is readable, H1 is read in its **net** form only: it fires when 3 or more of the 5 ids are lost in the arm and held in EXP-077. ~~If EXP-077 itself lost 3 or more of the 5, net H1 cannot reach 3; it is then reported as **unreadable**, not as no harm, and the gross count is recorded beside it.~~ *Amended 2026-11-12 05:55 UTC, after the push and before any result (section 7 item 2):* if EXP-077 itself lost 2 or more of the 5, net H1 is reported as **unreadable**, not as no harm, and the gross count is recorded beside it: `requests_6644` cannot be lost (section 3), so with 2 of the other four lost in EXP-077 a net of 3 could only come through it. If EXP-077 is not readable, H1 is read in its **gross** form (3 or more of the 5 lost in the arm). Both forms are always recorded.
- Nothing else in EXP-077 changes a row here. Its Eo, A, class and repeat spreads are recorded beside this file's secondaries.

### 4.2 Stop rule *(added 2026-11-12, critic fixes, fix 2)*
- The kernel has no total-wall deadline (EXP-038 section 8 found the same in the notebook source; unchanged). The dispatch prices this arm at about 1.3 GPU-h (EXP-038 1.267 h).
- **Cancel time: push + 2.0 h**, about 1.5 times the dispatch figure, with queueing counted in the elapsed time (the safe side). The push record states the push time in UTC (`date -u` right after the push) and the two clock times push + 1.5 h (the lead tells the user if the kernel is not COMPLETE) and push + 2.0 h (the cancel time).
- Cancelling is the user's action in the Kaggle UI. No agent cancels. If no one acts, the run continues to its end, 2.0 h is not enforced, and the exposure is the conditional worst case 6.66 h. This 2.0 h is a figure for the lead to own; the user's 2.0 GPU-h of EXP-038 section 8 covered that arm only and is not cited as an approval here.
- A run cancelled at that point is read as truncated under row 1.

## 5. What this does and does not license
- Row 4 or 5 licenses temperature 0.2 as the E4B base for later D-011 rounds. It licenses no upload (the E4B has no upload line here) and no change to the 31B `submission/` tree, where temperature was tested and read as noise (EXP-022).
- Row 3 closes sampling as the edit-application lever. It does not close edit application.
- No row licenses a statement about resolves; at 5 of 48 a McNemar contrast cannot read a plausible move.

## 6. Exact commands
```bash
python -I -X utf8 tools/analyze_traces.py runs/EXP-075-t02 --cap-minutes 8 --max-calls 28
python -I -X utf8 experiments/EXP-075/desk.py --all --run EXP-075-t02        # M, A, H2 (mechanism line)
python -I -X utf8 experiments/EXP-075/noise.py EXP-075-t02                   # R5 and the paired class table
python -I -X utf8 experiments/EXP-075/readings.py EXP-075-t02 --rerun EXP-077-base   # added 05:55 UTC (section 7 item 2): row 1 errors, H7, H1 gross and net, s
python -I -X utf8 tools/run_forensics.py compare runs/EXP-038-e4b-dev48 runs/EXP-075-t02   # resolves 2x2
python -I -X utf8 tools/run_forensics.py forensics runs/EXP-075-t02
python tools/estimate_budget.py --eval-config experiments/EXP-075/candidate-t02/eval_config.yaml --results runs/EXP-075-t02/summary.jsonl --tok-s 116.63 --per-call-s 0
cp runs/EXP-075-t02/summary.jsonl experiments/EXP-075/summary.jsonl
```
If the download nests the run (`runs/EXP-075-t02/runs/<x>/`), the scripts' `run_dir` finds it; pass the nested path to the tools.

## 7. Defects in this pre-registration, logged after the fact
1. *2026-11-12, critic prereg (36f7a27, 729c72f), needs-work; text fixes applied before the push, the tree, zip and notebook unchanged.* Where each item landed:
   - Fix 1 (H1 inside noise): section 3 H1 (gross and net forms, the critic's hold counts), row 2 (3 or more), section 4.1 (net form when EXP-077 is readable, unreadable if EXP-077 lost 3 or more, gross fallback).
   - Fix 2 (a complete file from a dead server): row 1 (infrastructure-error clause with the zero-turn and zero-call marker, the cap and no-submit strings excluded, 5 or more rows; truncated reading), section 4.2 (cancel time push + 2.0 h).
   - Fix 3 (row 6 grouping): row 6 bracketed.
   - Fix 4 (kill inside the draw SD): row 3 at 0.33, row 7 widened to every case rows 1 to 6 leave.
   - Fix 5 (loops outside `edit_file`): H7 in section 3 and row 2 (total 50 or more, or 3 or more tasks at 8 or more).
   - Non-blocking (wrong-file harm): section 2 limit (5).
   - Lead's additions: M_nr recorded (section 3, desk.py `notfound_share_nonrepeat`); the measured spread s replaces the 0.07 (section 4.1, section 2 limit (6)).
2. *2026-11-12 05:55 UTC, after the push of both kernels and before any result.* Three gaps in the critic-fix text (4ec19e5), closed in place with strikes: (a) section 4.1 let the time of the analysis choose between the measured s and the fallback; this file now waits until EXP-077 is terminal. (b) The unreadable boundary for net H1 was 3 or more lost in EXP-077; it is 2 or more, because `requests_6644` cannot be lost. (c) Section 6 had no command printing row 1's error count, H7, H1 gross and net, or s; `experiments/EXP-075/readings.py` prints them (checked on EXP-038: 48 rows, 0 infrastructure errors, 1 no-submit ending with turns, H7 total 25 with 0 tasks at 8 or more and at most 4 on one task, M 53 of 156, gross lost 0).

## 8. Built (below the line; nothing above changes)

---

- **Tree:** `experiments/EXP-075/candidate-t02/`, 4 files. `diff -ru experiments/EXP-033/candidate-e4b experiments/EXP-075/candidate-t02` shows one hunk in `configs/sampling.yaml`: `temperature: 1.0` -> `0.2` and the dated comment above it. Nothing else differs.
- **Validator** (`--strict`): `RESULT: INVALID (1 errors, 1 warnings)`; the error is the 18.00 h packing gate at 8 minutes, the warning `timeout_seconds` 240 (VERIFY(Q2)). Lint clean, instruction 3162 characters.
- **Zip:** `dist/EXP-075-t02.zip`, 2.5 KiB, 4 files (`agent.yaml`, `configs/sampling.yaml`, `eval_config.yaml`, `prompts/system.md`), sha256 `dca506d3f6b9011156ffe4a32ef067fd54ba54d633f44a2aa2aec09a348392a8` (re-checked with `sha256sum`, and the notebook's embedded base64 decodes to the same sha). Packed with `--skip-budget-gate --allow-warnings` (section 2); not an upload.
- **Reproduced from the committed LF blobs** of 979c35c (the four files written out with `git cat-file blob`, repacked): the same sha256 `dca506d3...92a8`.
- **Notebook:** `notebooks/exp075_t02/kaggle_eval_l4x4.ipynb`; `TASK_IDS` = the 48 dev-48 ids (checked equal to `experiments/cohorts/dev-48.txt`), `N_TASKS = 48`, `EXP_ID = "EXP-075-t02"`, `MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"`, `RUN_GOLD_CONTROL = False`, `RUN_AGENT = True`.
- **Kernel metadata:** copied from `notebooks/exp038_e4b_dev48/kernel-metadata.json` (E4B model source `google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2`, the pinned docker image, the wheelhouse dataset and the competition source), `id` `rainm4/gemma4-exp075-t02`, `title` `gemma4-exp075-t02`, nothing else changed.
- ~~**Not pushed.** The critic reviews this pre-registration first (the arm is above 1 GPU-h).~~ The critic's prereg review (36f7a27, 729c72f) was needs-work with text fixes only; they are applied in 4ec19e5 (section 7 item 1), and the lead counts them as applied, so no second critic pass blocks the push.

### Push record, 2026-11-12
- **Push time: 2026-11-12 05:50 UTC** (`date -u` immediately after the push returned, 05:50:29). Released by the lead with EXP-077, pushed 11 s later.
- **CLI output:** `Kernel version 1 successfully pushed.  Please check progress at https://www.kaggle.com/code/rainm4/gemma4-exp075-t02`
- **Kernel:** `rainm4/gemma4-exp075-t02`, version 1.
- **Status, checked once right after the push:** `KernelWorkerStatus.RUNNING`.
- **Checks before the push:** `git diff --quiet 9be7306 -- notebooks/exp075_t02 experiments/EXP-075/candidate-t02` clean (the tree and notebook unchanged since the first build); `sha256sum dist/EXP-075-t02.zip` = `dca506d3...92a8`; the pushed notebook is the committed one.
- **Clock times for the stop rule (section 4.2):** push + 1.5 h = **2026-11-12 07:20 UTC** (the lead tells the user if not COMPLETE); push + 2.0 h = **2026-11-12 07:50 UTC** (the cancel time, the user's action in the Kaggle UI). If no one acts, the run continues to its end.

## Status
~~**BUILT, NOT PUSHED (2026-11-12); awaiting the critic's prereg review.** Kernel `rainm4/gemma4-exp075-t02` does not exist yet. Expected cost about 1.3 GPU-h (EXP-038 reference 1.267 h).~~
**PUSHED 2026-11-12 05:50 UTC, RUNNING.** Kernel `rainm4/gemma4-exp075-t02` version 1. Expected cost about 1.3 GPU-h (EXP-038 reference 1.267 h). The analysis waits for EXP-077's status (section 4.1) and uses its fallbacks if EXP-077 is not readable.
