# EXP-086 — Per-file readers feeding an orchestrator on the E4B single-loop tree, smoke-8 on 8 wrong-file tasks: does the root call the readers within budget, and does its patch reach the gold file more often?

**Date:** 2026-11-20
**Type:** smoke-8 screen, ~0.8 L4x4-h of the 30/week (dispatch figure; probably well under, since EXP-077's 48-task E4B kernel ran 1.292 h including a 324 s vLLM start). No upload.
**Cohort:** reader-e4b-8 (`experiments/cohorts/reader-e4b-8.txt`: fastapi_14583, fastapi_5624, rich_3105, fastapi_14448, fastapi_14962, fastapi_11355, fastapi_15661, rich_3480; a subset of dev-48, not smoke-8)
**Ladder:** L0 desk check (the answers are in section 1b of `experiments/EXP-085-reader-orchestrator-31b-smoke8.md`, restated below for the E4B), then L2. Runs on the user's word of 2026-11-20 (`knowledge/user-decisions.md`): "alright now I want to experiment on kaggle where there is read agents first where the we spawn one agent per file to analyse and note abt the file, then an agent that takes that and then ochestrates on the fix.", one smoke-8 per model.
**Pre-registered:** this file is committed before the build and the kernel push. Sections 3 and 4 are written blind and are not revised.
**Serves:** the same request; the E4B fault map in `research/lit/2026-11-17-run-synthesis-model-faults.md` (E and F are 0.625 of the E4B's short-of-31B stages, EXP-080).
**Relates:** EXP-085 (the same architecture on the 31B; its section 1b is the desk check), EXP-033 (the tree), EXP-038, EXP-077, EXP-075, EXP-078 (the four baseline draws), EXP-064 (E4B pipeline reader: 2 to 11 reader calls, 43 of 79 task calls, `run_command` failures), EXP-068 (read_file truncation facts), EXP-032 section 9, EXP-046 section 2.2, C-014, EXP-080 section 6.1.

**What was already seen when these rules were written.** This list is complete.
- The per-task stage table of EXP-080 section 6.1 (the four E4B draws and arm R), the cohort source.
- The prompt `experiments/EXP-033/candidate-e4b/prompts/system.md` (identical to the 31B's: `diff -ru` of the two trees differs only in `agent.yaml`).
- The validator and harness facts as in EXP-085 section 1b. Not seen: any run of `agent_tool`, any trace of this tree, per-task gold-file values other than via the EXP-080 table.

## 1. Why this, now
- The E4B's dominant fault is the wrong file: in the EXP-080 table, of the 8 chosen ids the four draws stand at F in 27 of 32 task-draws, E in 2, R in 2 and C in 1 (by selection), so the file is the lever. A reader reads one candidate file at a time and says whether the file must change.
- The E4B's copy fidelity is a known fault (EXP-064: edit arguments lost), so the root re-reads the exact region before `edit_file`.
- The risks are the 31B's and sharper: E4B readers overspent (EXP-064: 2 to 11 calls per pipeline reader), the root's tool-call form is less reliable (text-form calls), and the same-model delegation (C-014) adds no capability, only time. The screen reads all three.

## 1b. Desk check for the E4B
D1 to D5 are as in EXP-085 section 1b (an `agent_tool` entry is accepted and packed; never run by us; one shared counter and clock [V], reader calls count by propagation [I], the `agent_tool` call itself [U]; notes land in the root's history; reader prompt under 10k at 1 to 2 reads). Validator on this tree: `python tools/validate_submission.py experiments/EXP-086/candidate-reader --strict`: 2 agents, 7 files, only the packing-gate error and the 240 s warning.
**D6, budget at the E4B's own settings (28 calls, 8 minutes, `max_turns` 80, same as the 31B).** Locate 1 to 2; readers 3 (limit held) to 9 (mild overspend) to 15 (EXP-032-like); the fix 4 to 7. Calls left for the fix: about 23, 19, 11 in cases A, B, C (3 fewer if the `agent_tool` call counts). Not a blocker on the expected cases. The E4B baseline is not call-capped as the 31B is (its tool calls rarely reach 28), so the call budget is not the E4B's tight resource; the clock and the form of its calls are.

## 2. Design

**One variable:** the same architecture as EXP-085, on the EXP-033 E4B tree (settings of EXP-077 base: temperature 1.0, thinking budget 4096, `max_output_tokens` 8192, eval_config unchanged: `timeout_seconds` 240, `max_tool_calls` 28, `max_time_minutes` 8, `max_turns` 80). The root prompt is the EXP-085 prompt byte for byte (the EXP-027 and EXP-033 prompts are identical). The reader is the EXP-085 reader with `model: gemma-4-e4b-it-qat-w4a16-ct`, tools `read_file` only, its own sampling (temperature 0.2, `thinking_budget` 512, `max_output_tokens` 1536, `include_thoughts` false), one `read_file` asked for, not enforced.

**Candidate tree and diff.** `experiments/EXP-086/candidate-reader/`. `diff -ru experiments/EXP-033/candidate-e4b experiments/EXP-086/candidate-reader`: `agent.yaml` +1 dated comment line and +2 `tools` lines (`- agent_tool:` with `config_path: sub_agents/file_reader.yaml`, no `skip_summarization`); `prompts/system.md` the same changes as EXP-085 (Budget +1 sentence, section 2 rewritten, section 3 retitled to 16 with a re-read-before-edit bullet; recorded in `diff -ru` of EXP-085); new `prompts/file_reader.md`, `sub_agents/file_reader.yaml`, `configs/reader_sampling.yaml`. Lint-clean as validated.

**Pack.** `python tools/pack_submission.py --src experiments/EXP-086/candidate-reader --out dist/EXP-086-reader.zip --skip-budget-gate`. **Gate override, stated:** 120 x (8 + 1.0) min = 18.00 h against 11.0 h by design, as EXP-033 and EXP-077 record for the E4B trees; there is no upload. Zip sha256 in section 8.

**Notebook.** `tools/build_notebook.py --embed dist/EXP-086-reader.zip --username rainm4 --cohort experiments/cohorts/reader-e4b-8.txt --set EXP_ID='"EXP-086-reader"' --set RUN_GOLD_CONTROL=False --out notebooks/exp086_reader/kaggle_eval_l4x4.ipynb`; `kernel-metadata.json` copied from `notebooks/exp084_sweep/` (a working E4B arm), changing only `id` (`rainm4/gemma4-exp086-reader`) and `title`.

**Cohort selection rule (declared before the runs).** Pool: the 48 ids of dev-48. For each id count, over the four E4B draws (EXP-038, EXP-077, EXP-075, EXP-078; EXP-080 section 6.1 columns), the draws at stage F, and at stage R. Keep ids with F in 3 or more of 4 draws; rank by F count descending, then R count descending, then id ascending; take the first 8. F in 4 of 4: fastapi_14583, fastapi_5624, rich_3105. F in 3 with an R: fastapi_14448, fastapi_14962. F in 3, no R: fastapi_11355, fastapi_15661, rich_3480 (taken); rich_3953 is the one cut by the id tie-break. Gated ids (EXP-036 `g`: fastapi_14583, fastapi_14962, fastapi_11355) are kept for the same reason as in EXP-085: the primary is a file hit, resolves are not read.
**Regression to the mean:** the cohort is chosen on baseline wrong-file history; the baseline file-hit mean count is 0.75 of 8 by this selection (EXP-038 0, EXP-077 1, EXP-075 1, EXP-078 1), and a fresh draw regresses upward with no change at all. The bar in row 5 (4 or more of 8) is set above that expectation (a fair rate of 0.2 per task gives about 0.06 for 4 or more), and the comparison remains the screen's bar only.

**Comparison.** The same 8 ids in the four existing E4B draws (`runs/EXP-038-e4b-dev48`, `runs/EXP-077-base`, `runs/EXP-075-t02`, `runs/EXP-078-t02r`). No new baseline arm. **Reading script:** `experiments/EXP-085/screen_read.py` (shared; untested; the screener cannot run it; a defect found when it first runs is logged in section 7).

## 3. Endpoints, fixed in advance

Definitions as in EXP-085 section 3: classes E, F, R, C, S by `diag.classify` margin 5; gold file hit = class not E and not F; region touched = C, S or resolved.

- **Primary: gold file hit per task.** Count of the 8 tasks whose patch contains a gold source file, arm against the mean count over the four draws (0.75 from the table); per task the arm's 0 or 1 against the task's baseline share, above, below, equal.
- **Then: gold regions touched** (tasks at C, S or resolved), arm against the draws (baseline: 1 task, once, in 4 draws).
- **Then: resolves.** Recorded, never an endpoint.
- **Guards:** file_reader calls per task and the counter accounting (`unaccounted`, as EXP-085); starved tasks (empty patch, a cap hit, readers used); tasks at a call or time cap; empty patches; tasks with a text-form call or `tool_free` and malformed calls (E4B form faults); mean turns (limit 80); wall per task (recorded; no projection is read for the E4B).
- **Statistic and power.** None computed; the bar is the screen's.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Rows are read in order; the first that fires governs.

| # | outcome | reading |
|---|---|---|
| 1 | **Infrastructure.** Fewer than 8 rows in `task_results.jsonl`, or the run's model is not the E4B, or the embedded zip's sha256 differs from section 8, or 2 or more of the 8 rows are infrastructure errors (`llm_calls` 0 or `n_turns` 0, or an `error` that is neither a cap string beginning `Agent exceeded session timeout` or `Agent exceeded turns budget` nor `Agent completed execution without calling submit_patch.`), or an `agent_tool` call fails to run (a tool error, not a model error) in 4 or more tasks, or the kernel did not finish | **Not readable.** Say which from the log. A re-push is the lead's call. |
| 2 | **Not used.** `file_reader` called in 1 or fewer of the 8 tasks | **The E4B does not call the reader at this wording**: the knob is not enforced. Primary not read. Wording killed; the idea is not. No dev-48. |
| 3 | **Starved.** 3 or more of the 8 tasks are starved (empty patch, a cap hit, readers used) | **Uninformative, not a kill.** Readers used up the calls or time. Record the reader call counts and the unaccounted gap. A tighter variant is a new claim and the lead's call. |
| 4 | **Limit breached.** Tasks at a call or time cap exceed the baseline mean by 3 or more (of 8), or tasks with a text-form call or `tool_free` exceed the baseline mean by 3 or more, or mean file_reader calls per task exceed 3, or empty patches exceed the baseline mean by 3 or more | **The architecture costs the budget or the call form the E4B runs inside**, whatever the primary reads. Killed for this tree as written; record the primary beside it. |
| 5 | **Promote.** Gold file hit count 4 or more of 8 (baseline 0.75), and no row above fired | **Promote.** Next rung: one dev-48 arm on this tree (needs the user's word), paired with the four draws, endpoint in section 5. A reason to spend the arm, not evidence of an effect. |
| 6 | **No uplift.** Gold file hit count 0 of 8 with the readers used in 6 or more tasks | **Kill.** The readers do not move the E4B to the gold file on tasks chosen for that fault. |
| 7 | **Flat or mixed.** Anything else (a file-hit count of 1 to 3) | **Not promoted.** Killed at L2 as written, with counts and guards recorded for the lead. |

**Not rows, but binding:** resolves are reported and never an endpoint; every direction is read against regression to the mean; this is also the first measurement of `agent_tool` on this harness and its model, so the reader call counts, the counter accounting and any tool error are reported to the lead whatever the row.

**Blind predictions (not readings).** `file_reader` used in 6 to 8 of 8. Reader calls 4 to 10 per task (the E4B overspends: EXP-064 2 to 11 per reader). Gold file hit 1 to 3 of 8. Text-form or malformed calls rise on 2 to 4 of 8. Probabilities: row 4 about 0.35, row 7 about 0.3, row 3 about 0.1, row 5 about 0.12, row 6 about 0.05, row 2 about 0.05, row 1 about 0.03. Resolves 0 to 1 of 8.

## 5. What this does and does not license

**Can decide:**
- **Kill** the reader-orchestrator architecture for the E4B at this wording (rows 2, 4, 6, 7), or leave it **uninformative** (row 3).
- **Promote** it to one dev-48 arm (row 5) on this tree, paired with the four E4B draws, with the endpoint: the share of dev-48 tasks whose patch contains a gold source file (baseline per draw from the EXP-080 table), and the share at C, S or resolved, with reader calls per task and text-form and empty-patch counts as guards. Resolves reported, not an endpoint.

**Does not license:** an upload, a resolve claim, a claim outside these 8 ids, or that the readers are the cause of a change.

## 6. Exact commands

```bash
python tools/pack_submission.py --src experiments/EXP-086/candidate-reader --out dist/EXP-086-reader.zip --skip-budget-gate
python tools/build_notebook.py --embed dist/EXP-086-reader.zip --username rainm4 --cohort experiments/cohorts/reader-e4b-8.txt --set EXP_ID='"EXP-086-reader"' --set RUN_GOLD_CONTROL=False --out notebooks/exp086_reader/kaggle_eval_l4x4.ipynb
kaggle kernels output rainm4/gemma4-exp086-reader -p runs/EXP-086-reader
python -I -X utf8 tools/analyze_traces.py runs/EXP-086-reader --cap-minutes 8 --max-calls 28
python -I -X utf8 experiments/EXP-085/screen_read.py --cohort experiments/cohorts/reader-e4b-8.txt --arm EXP-086-reader --base EXP-038-e4b-dev48 --base EXP-077-base --base EXP-075-t02 --base EXP-078-t02r
python -I -X utf8 tools/run_forensics.py forensics runs/EXP-086-reader
```

## 7. Defects in this pre-registration, logged after the fact
None yet.

## 8. Built and pushed (below the line; nothing above changes)

---

- **Pre-registration commit:** 8eaa438 (this file at sections 1 to 7, the candidate tree, the cohort file, the README row), made before the build.
- **Zip:** `dist/EXP-086-reader.zip`, sha256 `371761696f84737ada8f1a1485919d468a7f05b79b9a1f997e1a9ad6b151b96e`, 7 members as in EXP-085 (the reader file is pulled in by the `agent_tool` closure). Pack result VALID with 2 warnings (the gate, demoted, and `timeout_seconds=240 < 300`). The worktree blobs are LF.
- **Notebook:** `notebooks/exp086_reader/kaggle_eval_l4x4.ipynb`, built with the section 6 command; `TASK_IDS` equals the 8 ids of `experiments/cohorts/reader-e4b-8.txt`, `N_TASKS = 8`, `EXP_ID = "EXP-086-reader"`, `RUN_AGENT = True`, `RUN_GOLD_CONTROL = False`. Notebook sha256 `939cce4167f49a7e4c488fadd897b2a3af306d8b6f1035a3756cb0774c39fd6b`.
- **Kernel metadata:** `notebooks/exp084_sweep/kernel-metadata.json` (a working E4B arm) with `id` `rainm4/gemma4-exp086-reader` and `title` `gemma4-exp086-reader`, nothing else changed (model source `google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2`). Written by hand, as for EXP-085.
- **Kernels live at push time:** see EXP-085 section 8 (EXP-083 and EXP-084 COMPLETE, so 2 live after the two pushes).

## Status

**BUILT, NOT PUSHED.**
