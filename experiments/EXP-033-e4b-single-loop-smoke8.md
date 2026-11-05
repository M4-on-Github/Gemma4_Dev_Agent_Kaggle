# EXP-033 — the shipped single loop on the E4B (gemma-4-e4b-it-qat-w4a16-ct): does it run end to end in this harness, and how much of the 8-minute clock does it leave

**Date:** 2026-11-05
**Type:** smoke-8 screen, one arm, ~0.45-0.8 L4x4-h expected (worst case about 1.3 h, section 2 gives the arithmetic)
**Cohort:** smoke-8
**Ladder:** L2. L0 was done: no EXP, claim or run on disk has run an E2B or E4B through the agent loop (`.claude/skills/harness-stack/reference/small-variants.md`: EXP-006 sent plain chat completions only). L1 cannot read it: there is no E4B trace.
**Pre-registered:** this file, the tree, the zip's recorded sha and the notebook are committed before the push. Sections 3-5 are written blind and are not revised; results are appended as a new section.
**Serves:** the small-model prize path (competition-brief skill; the critic's D-004 review recommended an E4B single-loop screen over an E2B pair; the user chose E4B on 2026-11-05 in chat).
**Supersedes / relates:** EXP-027 (baseline tree), EXP-028 Arm R (reference, same 8 ids, same eval_config), EXP-006 (E2B/E4B boot and KV room), EXP-032 (its P1 kernel is still running; this job does not touch it).

## 1. Why this, now

- The small-model prize needs an E2B or E4B entry. Nothing has run an E4B through the harness's agent loop. Whether the model loads from the Kaggle model input, whether the gemma4 chat template and tool-call parser give well-formed calls, and whether thinking is emitted are all unverified ([I]/(unverified) list in `small-variants.md`).
- Reference, already measured, same 8 ids and the identical `eval_config.yaml` (240 / 28 / 8 min / 80 turns), 31B: `experiments/EXP-028/armR/summary.jsonl`.

| id | resolved | wall s | calls | turns | compactions | cap that ended it |
|---|---|---|---|---|---|---|
| fastapi_14301 | yes | 78.9 | 13 | 16 | 0 | submit |
| fastapi_14448 | no | 418.4 | 15 | 17 | 1 | submit |
| fastapi_14605 | no | 156.2 | 29 | 31 | 1 | calls |
| httpx_3672 | no | 282.3 | 23 | 25 | 2 | submit |
| requests_7205 | no | 165.6 | 10 | 13 | 0 | submit |
| requests_7309 | no | 113.0 | 9 | 12 | 0 | submit |
| rich_3006 | yes | 111.2 | 11 | 14 | 0 | submit |
| rich_3468 | no | 297.4 | 22 | 23 | 1 | submit |
| sum, mean | 2 of 8 | 1,623.0 s, **202.9 s** | 132, 16.5 | 151, 18.9 | 5 | 1 calls, 0 time, 0 turns, 7 submit |

  31B on these ids: 10.7 s per model turn (1,623.0 s / 151 turns); malformed calls 0 of 132; edit argument loss 1 event. Time left under the 480 s cap: mean 277 s per task.
- E4B facts on disk [V]: TP 4, `max_model_len` 32768, `gpu_memory_utilization` 0.90, parsers `gemma4`, no extra vLLM args; boot 289 s against 31B's 377 s; KV room 45.6x at 32k (EXP-006).

## 2. Design

One arm, one variable.

- Tree: `experiments/EXP-033/candidate-e4b/` = `experiments/EXP-027/candidate-v24-at-8/` with only the `model:` value of `agent.yaml` changed from `gemma-4-31b-it-qat-w4a16-ct` to `gemma-4-e4b-it-qat-w4a16-ct` (dated comment added in the file). `diff -ru experiments/EXP-027/candidate-v24-at-8 experiments/EXP-033/candidate-e4b` shows that and nothing else. `eval_config.yaml` is the baseline's (240 / 28 / 8 / 80); the prompt is the 31B's, still saying 28 tool calls and 8 minutes, and the sampling is the baseline's (temperature 1.0, thinking_budget 4096, include_thoughts true, max_output_tokens 8192). Not tuned for the small model by design.
- Validator (`--strict`): 1 ERROR, 1 WARN, both the baseline's. ERROR `worst case 120 x (8 + 1.0) min = 18.00 h` exceeds the 11.0 h packing gate: overridden with `--skip-budget-gate` because this is a screen of 8 tasks and the zip is never uploaded (UNOFFICIAL TEST BUILD). WARN `timeout_seconds=240 < 300`: also on the baseline. The model name is accepted (`ALLOWED_MODEL_NAMES`). `--official` cannot run here.
- Pack: `dist/EXP-033-e4b.zip`, 4 members (`agent.yaml`, `configs/sampling.yaml`, `eval_config.yaml`, `prompts/system.md`), sha256 `9de869bd2cd8853b72d653d06b9acef3e03794c8b588c26494435774dda11ac0`. Packed from the CRLF worktree and gitignored (not claimed to reproduce from committed blobs, never uploaded).
- Notebook: `notebooks/exp033_e4b/` built with `--cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-033-e4b"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False`. The parameter cell was read back: `EXP_ID`, `MODEL_NAME` quoted, `RUN_AGENT = True`, `RUN_GOLD_CONTROL = False`, `TASK_IDS` = the 8 smoke-8 ids. `kernel-metadata.json` is `notebooks/exp028_armR`'s with only `id` (`rainm4/gemma4-exp033-e4b`), `title` and `model_sources` (`google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2`) changed; the notebook asserts that input's `config.json` exists before the vLLM boot, so a wrong input fails in seconds. That the model input path exists on Kaggle is **unverified** until the push.
- Cost (GPU-h of the 30/week, no upload slot): expected task time 8 x 150-300 s = 0.33-0.67 h, plus kernel overhead about 0.13 h (31B's measured overhead 0.15 h; E4B boots faster) = **0.45-0.8 h**. Worst case, every task running to the 8-minute cap plus grading (about 500 s) = 1.1 h + 0.15 h = **1.3 h**; that needs 8 of 8 tasks at the time cap, which 31B did on 0 of 8 of these ids. The expected estimate is under 1 GPU-h, so no critic `prereg` is needed; a worst case above 1 h is stated here and not hidden.

## 3. Endpoints, fixed in advance

Counts over the 8 tasks (no statistics at n = 8), read from `runs/EXP-033-e4b/traces/trace_<id>.json`, `summary.jsonl` (`tools/analyze_traces.py runs/EXP-033-e4b --cap-minutes 8 --max-calls 28`), `task_results.jsonl` and the kernel log. Reference for each is the Arm R table in section 1.

| # | Endpoint | Definition |
|---|---|---|
| E1 | Tasks with at least one well-formed tool call | tasks with `n_calls - n_malformed >= 1`, executed by the harness |
| E2 | Malformed-call rate | `n_malformed` / (all calls incl. malformed); Arm R 0 of 132 |
| E3 | Thinking | tasks whose model steps carry thought text; whether the budget is honoured: no step with completion tokens above 8192, and thought tokens at most 4096 where the trace separates them (the summary's `thinking_tokens` is null for Arm R; if it is null here, say the budget endpoint is lost and report completion tokens per step instead) |
| E4 | Turns, counted calls, seconds per model turn | per task and totals; seconds per turn = wall / turns; Arm R 10.7 s per turn, 16.5 calls and 18.9 turns per task |
| E5 | Compactions | the fixed detector (`analyze_traces.py` since 4657dce: prompt-token drops at the 14,336 threshold); Arm R 5 in 8 tasks |
| E6 | Which cap ends each task | exactly one of: calls (28), turns (80), time (480 s), or submit (`submit_patch_called` and none of the three); Arm R 1 calls (fastapi_14605, which also called submit), 0 time, 0 turns, 7 submit |
| E7 | Tasks ending with a non-empty patch | `patch_empty` false |
| E8 | First-edit call index | counted-call index of the first `edit_file` or `write_file` per task (Arm R's from `runs/EXP-028-armR`); the prompt's deadline is call 12 |
| E9 | Edit argument loss | `n_edit_arg_loss` summed; Arm R 1 |
| E10 | Server startup and in-flight requests | `vLLM up in N s` from the kernel log (31B 342-397 s, E4B in EXP-006 289 s); peak in-flight requests if the log shows them (a single loop issues one at a time, so 1 is expected) |
| E11 | Time left | per task and mean, 480 s minus the task wall, for tasks that ended before the time cap; Arm R mean 277 s |
| E12 | Resolves | recorded only, no rate claimed, not read |

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Rows are applied in order; the first match governs. "Capped" means E6 is calls, turns or time.

| # | Outcome | Reading and what happens next |
|---|---|---|
| 0 | The loop does not function: the kernel fails before any task (model input missing, vLLM does not boot, chat template or tool-call parser rejects the model), or E1 is below 4 of 8 | Say which of model load, chat template or tool-call format failed, from the log and the first trace. Fix exactly that one cause in a new EXP, re-run once; if the second run also fails, the E4B path is parked and E2B is not tried on this evidence |
| 1 | The loop functions (E1 is 4 or more) and E7 is 0 of 8 | The small model does not produce an edit through this prompt and these tools. The E4B single loop with the 31B prompt earns no dev-48 arm and no upload; the open question is a prompt fitted to the small model (state from the traces whether the first `edit_file` call was ever made, E8, and whether arg loss or malformed calls blocked it). Resolves not read |
| 2 | The loop functions, E7 is 1 or more, and 3 or more of 8 tasks are capped (31B on the same ids: 1 of 8; on dev-48 37.5%) | Cap-bound the same way as 31B or worse. There is no spare clock for an extra stage on this model; the next step is the E4B single loop as an LB-only draw if the lead wants a small-model entry (the read of E6 says which cap binds, which sets whether a lower `max_tool_calls` or turns would help), not a parallel or verify tree |
| 3 | The loop functions, E7 is 1 or more, and 2 or fewer of 8 are capped | The loop finishes inside the clock. Report the time left per task in seconds (E11, mean and minimum) and the seconds per turn (E4): that is the room a parallel or verify stage would have on this model, in turns (room / seconds per turn). A verify or parallel stage is then costed in those seconds on a dev-48 arm with a time-profile endpoint; no upload is licensed by this row |

Recorded in every row, not read: resolves (E12), and E3, E5, E9 as counts. Not readable from this screen: any resolve rate, the effect on the leaderboard, whether E4B beats the 31B on anything.

Predictions, written blind (before any E4B trace exists):
- The kernel boots and the loop functions: 80%. Row 0 20%, most likely a model-input path or template problem.
- Tasks with a well-formed call: 7 or 8 of 8 if it functions. Malformed-call rate 5-20% of calls (31B: 0 of 132), nonzero. Thinking emitted in most tasks.
- Seconds per model turn about 5 s (range 3-8) against 31B's 10.7 s; vLLM up in about 290 s (250-330 s); peak in-flight requests 1.
- Mean task wall about 200 s (range 120-330); kernel wall about 0.55 h.
- Capped tasks: 3 or 4 of 8 (small models loop and repeat); calls or turns more often than time. Row 2 is the likeliest (45%), row 3 (25%), row 1 (10%), row 0 (20%).
- Non-empty patches in 5 to 7 of 8. First-edit call index later than 31B's. Edit argument loss at least as frequent as 31B.
- Resolves 0 of 8 (50%), 1 of 8 (35%), 2 or more (15%); recorded, not read.

## 5. What this does and does not license

**Can decide:** whether the E4B runs through this harness at all (row 0, a bound), whether it produces edits (row 1), and, if it functions, whether a stage of extra work has clock to run in (row 3, stated as seconds and turns) or the loop is already cap-bound (row 2). **Cannot decide:** whether the E4B is competitive, any resolve rate, or the effect of a prompt written for the small model; the 31B prompt is used unchanged on purpose. No upload is licensed by any row; the next rung after a functioning loop is the lead's choice between an LB-only E4B draw (zero GPU) and a dev-48 arm with a time-profile endpoint.

## 6. Exact commands

```
python tools/validate_submission.py experiments/EXP-033/candidate-e4b --strict
python tools/pack_submission.py --src experiments/EXP-033/candidate-e4b --out dist/EXP-033-e4b.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed dist/EXP-033-e4b.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-033-e4b"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp033_e4b/kaggle_eval_l4x4.ipynb
# push, a later step in this job:   kaggle kernels push -p notebooks/exp033_e4b
# after COMPLETE, a separate job:
kaggle kernels output rainm4/gemma4-exp033-e4b -p runs/EXP-033-e4b/
python tools/analyze_traces.py runs/EXP-033-e4b --cap-minutes 8 --max-calls 28
python tools/run_forensics.py forensics runs/EXP-033-e4b
python tools/run_forensics.py compare runs/EXP-028-armR runs/EXP-033-e4b
```

## 7. Defects in this pre-registration, logged after the fact

None yet. Known at writing time: the Arm R per-task fields in section 1 were read from `summary.jsonl` and the cap column is derived from `calls_cap_hit`, `time_cap_hit` and `submit_patch_called`; the first-edit index for Arm R was not computed here (E8 computes it at analysis). `build_notebook.py` printed `kernel-metadata.json id -> rainm4/gemma4-eval-l4x4` but did not write one in the output directory; the file here is hand-written from `exp028_armR`'s with the three changes above.

## 8. Built

Built 2026-11-05 with the section 6 commands; sha in section 2; validator output in section 2. Committed by pathspec before the push. **Push not yet done at the time of this writing**; the push record and `## Status` follow below.

**Push record, 2026-11-05.** Kernel `rainm4/gemma4-exp033-e4b` pushed from `notebooks/exp033_e4b` after the pre-registration commit d2c11da (zip sha256 `9de869bd2cd8853b72d653d06b9acef3e03794c8b588c26494435774dda11ac0`), reply "Kernel version 1 successfully pushed". UTC time of day not recorded (no clock command). First status check straight after: `KernelWorkerStatus.QUEUED` (the EXP-032 P1 kernel may still be running; Kaggle did not refuse the push). Not waited on.

## Status

2026-11-05: `rainm4/gemma4-exp033-e4b` pushed, QUEUED. Next, a separate job when `kaggle kernels status rainm4/gemma4-exp033-e4b` says COMPLETE: download with `kaggle kernels output rainm4/gemma4-exp033-e4b -p runs/EXP-033-e4b/`, then the section 6 analysis, then section 4 as written. If the log shows the model-input assert failing, that is row 0 (model load) and the model input path was the unverified item.
