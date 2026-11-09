# EXP-062 — The EXP-061 tree with a root prompt that re-transfers on every message (smoke-8 bug test)

**Date:** 2026-11-09
**Type:** smoke-8 screen, ~0.32 L4x4-h (EXP-061: 0.324). One push, no upload, no dev-48. The user approved one round (knowledge/user-decisions.md, 2026-11-09 about 00:40 UTC, 9eadeb9).
**Cohort:** smoke-8
**Ladder:** L2. L0 desk check in section 1. L1 cannot read this question: the root prompt has never run, and EXP-061 had only one nudged task.
**Pre-registered:** this file is committed before the push. Sections 3-5 are written blind and are not revised.
**Serves:** EXP-061 row S1 (`fastapi_14301`: the nudge re-run landed on the handoff root, which ended in text); D-007 tree T2 on the E4B.
**Supersedes / relates:** EXP-061 (tree and smoke-8, row S1), EXP-052 (pipeline, compaction crash).

## 1. Why this, now. Desk check (zero GPU, `data/src`, all [V])

**(a) Where a nudge re-run starts.**
- **The harness reuses the session.** It sends each nudge with `runner.run_async(user_id, session_id, new_message=...)` on the same session and passes no `invocation_id` (`swegemma/harness/agent_runner.py:806-811`). Each nudge is therefore a new invocation, and the runner picks its agent with `_find_agent_to_run` (`google_adk/google/adk/runners.py:1299`, inside `_setup_context_for_new_invocation`, 1264).
- **How `_find_agent_to_run` chooses** (`runners.py:1082-1134`):
  - If the last event is a function response, it returns the agent that made that call (1107-1109). A nudge is a user text message, so this branch does not apply.
  - Otherwise it walks non-user events backwards, skipping agent-state and end-of-agent events (1111-1119).
  - An event authored by the root returns the root (1120-1122).
  - Any other author is returned only if `_is_transferable_across_agent_tree` holds (1131-1132). That check requires every agent on the path up to the root to have `disallow_transfer_to_parent`, and that flag to be false (1136-1156).
  - If nothing qualifies, it falls back to the root (1133-1134).
- **In this tree every walk ends at the root.**
  - `reader` and `applier` have parent `pipeline`, a `SequentialAgent`. It has no `disallow_transfer_to_parent` attribute, so they fail at the parent step.
  - The drafters' parent `draft` is a `ParallelAgent`, which has no such attribute either.
  - `pipeline` itself is not an `LlmAgent`.
  - So the walk reaches the root's own transfer event and returns the root, or hits the fallback. **A nudge re-run always starts at `swe_agent`.** This matches EXP-061 `fastapi_14301`, step 18.
- **Landing on the pipeline instead.** The runner cannot select the pipeline or any of its descendants directly. That would need an `LlmAgent` whose whole parent chain consists of transfer-capable `LlmAgent`s, for example the applier as a direct sub-agent of the root `LlmAgent`. The other routes are a root that re-transfers (this experiment) or a `SequentialAgent` root, which is the EXP-052 crash hazard.
- **A second pass starts from the reader.** swegemma sets no resumability config (grep for `resumab` under `swegemma/` finds nothing). So the `SequentialAgent` has no saved state and starts at index 0 (`google_adk/google/adk/agents/sequential_agent.py:61-67`, `94-108`).

**(b) The nudge mechanism** (`swegemma/harness/agent_runner.py`).
- **Text.** The plain nudge is "Please continue your work using the available tools, or call submit_patch when you have completed and verified your changes." (`:997-1000`). Two other variants exist, for a truncated tool call and for a length stop (`:983-996`).
- **Count.** `max_nudges = 3` (`:784`). The session ends when `consecutive_nudges >= 3` (`:965-971`). The counter resets to 0 after any turn that contained a function call (`:962-963`, set at `:832-839`). This is why EXP-061 `fastapi_14301` got 4 nudges: the root's refused `submit_patch` reset the counter.
  - **Consequence for this tree [I, from the code].** If the root re-transfers on each nudge, every nudged turn holds a function call. The counter then never reaches 3, and passes repeat until the 8-minute time cap (`:924-930` and the `asyncio.timeout` at `:724-728`), the 45-call cap (`:932-946`) or the 120-turn cap (`:947-958`).
- **The diff at the end.** If no `submit_patch` succeeded, after the nudge limit or at a time, call or turn cap, the runner takes the working tree's diff against the baseline as the patch (`:1054-1078`). Protected files are stripped from it. Only an empty diff gives the "Agent completed execution without calling submit_patch." error (`:1080-1083`). A timeout goes through the `except TimeoutError` branch (`:1026-1031`) and then the same fallback. So a later pass starts on a dirty workspace, and any partial edit it leaves is still graded.

**The change.** Only `prompts/root.md`. The new text says:
- the root's only tool is `transfer_to_agent`, and it has no file, command or submit tools;
- whatever message arrives, including a reminder to continue or to submit, its only action is `transfer_to_agent` to `pipeline`;
- never answer in text and never call another tool.

## 2. Design

| | value |
|---|---|
| tree | `experiments/EXP-062/candidate-r/` = `cp -r experiments/EXP-061/candidate-r`, then `prompts/root.md` replaced |
| diff vs EXP-061 | `diff -r` shows only `prompts/root.md` (1 line becomes 3); every other file is byte-identical, including `agent.yaml` and its EXP-061 comments |
| model, caps | E4B everywhere; 8 min / 45 calls / 120 turns / `timeout_seconds` 240 (EXP-061's) |
| zip | `experiments/EXP-062/exp062_r.zip` (gitignored), sha256 in section 8; packed with `--skip-budget-gate` as EXP-061 (18.00 h nominal); **not an upload** |
| notebook | `notebooks/exp062_r/`, EXP-061's build command with only the zip and `EXP_ID` changed; kernel `rainm4/gemma4-exp062-r` |
| cost | ~0.32 GPU-h; no slot |

## 3. Endpoints, fixed in advance

Per task, from `traces/`, `task_results.jsonl` and the kernel log:
- **First transfer.** Did the root call `transfer_to_agent` naming `pipeline` in the first invocation, before any pipeline agent ran? Record any other call it made first.
- **Nudged tasks (N).** Tasks with at least one `continuation_nudge` step.
- **Re-transfers (T).** Among nudged tasks, those where every root turn after a nudge is a `transfer_to_agent` call to `pipeline`.
- **Second passes (P2).** Tasks where `reader` runs again after a nudge.
- **Later-pass submits (S).** Tasks that end on a successful `submit_patch` from a pass after the first.
- **Harm.**
  - Any time, call or turn cap hit.
  - A nudged task ending with an empty patch.
  - Tasks with a non-empty patch in EXP-061 that end empty here, split into nudged and not nudged.
  - Mean wall against EXP-061's 89.5 s.
- **Errors.** `err` per task: a traceback, a sandbox execution error, any compaction error, or the no-submit label.
- **Compaction.** Count, and the largest single-request prompt against 14,336.
- **Recorded only.** Resolves, the draft kept, edit failures.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

First match governs.

| # | outcome | reading |
|---|---|---|
| 1 | **Infrastructure.** Any of: an `err` with a traceback, a sandbox execution error or a compaction error; the tree does not run on some task; the root fails to transfer to `pipeline` in its first invocation | A bug, not a reading. Name the task and the step. No later run of this tree until it is understood. |
| 2 | **Harm.** Any time, call or turn cap hit; or a nudged task that ends with an empty patch | The re-transfer loop costs more than it buys on that task. Name the task, its pass count and its walls. The next step is a design that bounds the passes, for example the applier as a transfer-capable child of the root, or a stop rule. Do not carry this root forward unchanged. |
| 3 | **Not exercised.** No task is nudged (N = 0) | The mechanism was not exercised: **no decision, not "the fix works".** Record first-transfer behaviour (row 1 was clear) and the walls. Whether to spend another smoke is the user's call. |
| 4 | **Prompt insufficient.** N ≥ 1 and T < N: after a nudge the root answers in text or calls another tool | The prompt does not hold the root to transferring. The fix fails on that task. |
| 5 | **Mechanism works.** N ≥ 1, T = N, and S ≥ 1 | The root re-transfers and at least one later pass ends on `submit_patch`. Record N, T, P2, S, and the walls of each pass. This is a bug-test verdict, not an effect; any upload remains the user's call. |
| 6 | **Re-transfers, no later submit.** N ≥ 1, T = N, S = 0 | The routing is fixed, but later passes do not end on a submit. Record how each nudged task ended (on-disk diff fallback, empty, or cap). |

**Not rows, but binding:**
- Tasks that were non-empty in EXP-061 and are empty here without a nudge are recorded as sampling variation, not as harm from the fix. The root prompt touches only the root's turns.
- If no prompt reaches 14,336 tokens, the compaction fix is recorded as **untested again**.
- The mean wall is recorded against 89.5 s, not read as an effect.

**Blind prediction.**
- N: 0 or 1 nudged tasks, probability 0.7 (EXP-061 had 1 of 8).
- Row 3 fires: about 0.45.
- Row 5: about 0.3. Row 2: about 0.1. Row 4: about 0.1. Row 1: about 0.05.
- The root transfers on its first message on 8 of 8. The two EXP-061 tasks that called `read_file` first are expected to transfer directly here, with probability 0.6.

## 5. What this does and does not license

**Licenses:**
- A bug-test verdict on whether the root re-transfers after a nudge and whether a later pass can submit.
- The first-transfer behaviour under the new prompt.

**Does not license:**
- Any resolve or LB claim.
- Any upload or dev-48 run without the user.
- A verdict on the compaction fix unless a prompt reaches 14,336 tokens.

## 6. Exact commands

```
python tools/validate_submission.py experiments/EXP-062/candidate-r --official --strict --json
python tools/pack_submission.py --src experiments/EXP-062/candidate-r --out experiments/EXP-062/exp062_r.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed experiments/EXP-062/exp062_r.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-062-r"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp062_r/kaggle_eval_l4x4.ipynb
```

Analysis, a separate job:
1. Download with `kaggle kernels output rainm4/gemma4-exp062-r -p runs/EXP-062-r/`, then flatten.
2. Run `python -I -X utf8 tools/analyze_traces.py runs/EXP-062-r --cap-minutes 8 --max-calls 45`.
3. Run `python -I -X utf8 tools/run_forensics.py forensics runs/EXP-062-r`.
4. Count per stage from `traces/`.

## 7. Defects in this pre-registration, logged after the fact

1. **(Known at pre-registration.)** `analyze_traces.py` counted a `submit_patch` call that the ADK had refused as a submit. This affected EXP-061 `fastapi_14301`. Fixed in this commit: a call whose observation carries "Tool 'submit_patch' not found" no longer sets `submit_patch_called`. The fix is covered by `tests/test_analyze_traces.py::test_refused_submit_patch_is_not_a_submit`. Re-running on `runs/EXP-061-r` (output to `out/`) gives `fastapi_14301` `submit_patch_called` false and a run rate of 87.5% instead of 100%. The committed `experiments/EXP-061/summary.jsonl` keeps the old value.
2. **(Known at pre-registration.)** The tree was built by `cp -r` plus one replaced file, not by a hash-verifying tool. Section 2 records the `diff -r` result instead.
3. **(Found at analysis, 2026-11-09.)** The binding note on compaction asks only whether any prompt reaches 14,336 tokens. It does not separate the two compaction paths. The EXP-052 crash comes from the post-invocation path (`harness-stack/reference/compaction.md` § Hazard, conditions 1-6). The in-flow path passes the calling `LlmAgent` and cannot raise that error. The three compactions in this run are in-flow drops inside an invocation. An in-flow compaction sets the skip flag for the post-invocation path (condition 2), so the crash path was not reached [I from source]. Section 9 applies the note as written and states this limit next to it.

## 8. Built and pushed (below the line; nothing above changes)

---

- **Validator** (`--official --strict`): 1 error, the 18.00 h gate, which `--skip-budget-gate` demotes to a warning. 2 warnings, both carried by EXP-061: the applier's `submit_patch` and `timeout_seconds` 240. The official validator could not be imported.
- **Pack:** `RESULT: VALID (0 errors, 3 warnings)`, PACK OK. **sha256 `0fefd79d3d37a4cd7ca7de084a669ff19152e4f78e0320291bedb184db6faa12`.** The tree has no CR byte.
- **Tests:** `python -m pytest -q`, 52 passed.

- **Pre-registration commit:** d1286b5. Repacking from `git -c core.autocrlf=false archive HEAD` gives the same sha `0fefd79d...6faa12`.
- **Notebook:** `notebooks/exp062_r/`, built with the section 6 command. Against `notebooks/exp061_r/` it differs in only 2 lines, both in cell 1: `EXP_ID` and `SUBMISSION_B64`. The embedded base64 decodes to sha `0fefd79d...6faa12`. `kernel-metadata.json` is EXP-061's with only `id` and `title` changed, to `rainm4/gemma4-exp062-r`. Nothing was copied to `out/submission.zip`.

## Status

~~2026-11-09: pre-registered and packed; the notebook is not built yet. Next: verify that the sha reproduces from committed blobs, build `notebooks/exp062_r/`, push.~~

~~2026-11-09: notebook built and committed; push follows this commit. Kernel `rainm4/gemma4-exp062-r`. Next, when COMPLETE: the analysis commands in section 6.~~

~~2026-11-09 00:44 UTC: pushed after 3f79d7d ("Kernel version 1 successfully pushed"); first status RUNNING. Kernel `rainm4/gemma4-exp062-r` v1. Next, when COMPLETE: the analysis commands in section 6, then apply section 4.~~

2026-11-09: COMPLETE (lead, 16:18 UTC), downloaded and analysed (section 9). **Row 3 fires: not exercised, no task nudged, no decision.** 0.323 GPU-h. Nothing running.

---

## 9. Results, 2026-11-09. Section 4 readings applied as written.

**Run.**
- Kernel `rainm4/gemma4-exp062-r` v1: the lead reported it COMPLETE at 16:18 UTC 2026-11-09.
- Downloaded with `kaggle kernels output rainm4/gemma4-exp062-r -p runs/EXP-062-r/`, and the nested `runs/EXP-062-r/` was moved up one level.
- `python -I -X utf8 tools/analyze_traces.py runs/EXP-062-r --cap-minutes 8 --max-calls 45` and `python -I -X utf8 tools/run_forensics.py forensics runs/EXP-062-r`.
- Per-stage counts from `traces/` with the scratch counter `out/exp062_mech.py` (untracked; it prints ids, agent names, tool names and token counts only).
- `summary.jsonl` is copied to `experiments/EXP-062/summary.jsonl`.

**GPU cost.**
- Kernel wall **1161.8 s = 0.323 GPU-h** (the last entry of the kernel log).
- vLLM came up in 325.9 s.

### 9.1 Per task

| task | root's first step | nudges | reader runs | how the session ended | patch chars | max prompt (agent) | inferred compactions | wall s | EXP-061 patch |
|---|---|---|---|---|---|---|---|---|---|
| fastapi_14301 | step 3, transfer to `pipeline` | 0 | 1 | applier `submit_patch` ok, then text | 637 | 11,545 (applier) | 0 | 68.5 | empty |
| fastapi_14448 | step 3, transfer to `pipeline` | 0 | 1 | applier `submit_patch` ok | 811 | 14,657 (applier) | 1 (applier) | 141.9 | non-empty |
| fastapi_14605 | step 3, transfer to `pipeline` | 0 | 1 | applier `submit_patch` ok, then text | 342 | 8,420 (applier) | 0 | 49.7 | non-empty |
| httpx_3672 | step 3, transfer to `pipeline` | 0 | 1 | applier `submit_patch` ok, no text after it | 1,419 | 19,482 (applier) | 1 (applier) | 169.6 | non-empty |
| requests_7205 | step 3, transfer to `pipeline` | 0 | 1 | applier `submit_patch` ok twice, no edit made, then text | **0** | 7,969 (applier) | 0 | 58.8 | non-empty |
| requests_7309 | step 3, transfer to `pipeline` | 0 | 1 | applier `submit_patch` ok, then text | 529 | 8,600 (applier) | 0 | 53.5 | empty |
| rich_3006 | step 3, transfer to `pipeline` | 0 | 1 | applier `submit_patch` ok, then text | 558 | 8,406 (applier) | 0 | 53.9 | non-empty |
| rich_3468 | step 3, transfer to `pipeline` | 0 | 1 | applier `submit_patch` ok | 1,009 | 15,852 (reader) | 1 (reader) | 118.1 | non-empty |

### 9.2 Mechanism counts

**(a) First transfer: 8 of 8.**
- On every task, the root's only step is step 3, the first agent step. It is a `transfer_to_agent` call naming `pipeline`. It comes as a `thinking` event, and the model's reasoning is attached to it.
- The root never produced a `final` text event and never called any other tool.
- The two EXP-061 tasks that called `read_file` first (`fastapi_14301`, `fastapi_14605`) transferred directly this time.
- The stages ran in order once on 8 of 8: reader, five drafters, applier.

**(b) Nudges: N = 0.**
- No `continuation_nudge` step on any task (`analyze_traces`: nudges 0), so T, P2 and S are all 0.
- Every session ended on the applier, after a `submit_patch` that returned ok, in the first and only pass. None of these calls was refused.
- No session ended on a cap or on the empty-diff fallback.

**(c) Errors and compaction.**
- **Errors:** `err` is empty on all 8 tasks (`task_results.jsonl`, and the kernel log `[k/8]` lines). The kernel log holds no `Traceback`, no `ValueError` and no sandbox execution error.
- **Prompt size:** prompts reached 14,336 tokens on 3 tasks: `httpx_3672` 19,482 (applier), `rich_3468` 15,852 (reader) and `fastapi_14448` 14,657 (applier).
- **Compactions:** `analyze_traces` infers 3, one on each of those tasks, all within the invocation:
  - `fastapi_14448` applier, 14,657 to 5,853;
  - `httpx_3672` applier, 15,649 to 8,883;
  - `rich_3468` reader, 15,852 to 5,915.
- **The `httpx_3672` invocation:** its last model call carried 19,482 prompt tokens. It ended on a `submit_patch` with no text after it. The task finished without error.

**(d) Harm.**
- **Caps:** 0 time-cap, 0 call-cap and 0 turn-cap hits; 0 overflow.
- **Patches:** the two EXP-061 empties (`fastapi_14301`, `requests_7309`) are non-empty here. One EXP-061 non-empty task is empty here: `requests_7205`. It was not nudged; its applier made no edit and submitted twice.
- **Walls:**
  - mean **89.2 s**, against 89.5 s in EXP-061;
  - median 63.6 s, max 169.6 s (`httpx_3672`);
  - total agent wall 714.0 s.
- **Projection:** `analyze_traces` projects **2.98 h** for 120 tasks.
- **Dirty workspace:** none seen. The diff fallback was never used, and every patch came from a `submit_patch` that returned ok.

### 9.3 Readings applied, first match governs

- **Row 1, infrastructure: does not match.** No `err` on any task, with no traceback, sandbox execution error or compaction error. The tree ran on 8 of 8, and the root transferred to `pipeline` in its first invocation on 8 of 8.
- **Row 2, harm: does not match.** There were no cap hits, and no task was nudged, so no nudged task ended empty.
- **Row 3, not exercised: FIRES.** N = 0. **The mechanism was not exercised: no decision, not "the fix works".**
  - First-transfer behaviour: 8 of 8 at the first agent step, with no refused calls before it. EXP-061 had 2 tasks with refused calls first.
  - Mean wall 89.2 s against 89.5 s, recorded and not read as an effect.
  - Whether to spend another smoke is the user's call.
- **Rows 4-6:** not reached.

**Binding notes, applied.**
- **`requests_7205`:** it was non-empty in EXP-061, is empty here and was not nudged. It is recorded as **sampling variation, not harm from the fix**.
- **The compaction note:** "If no prompt reaches 14,336 tokens, the compaction fix is recorded as untested again". Its condition is false: prompts reached 14,336 on 3 tasks, and all 3 tasks compacted and finished without error. So "untested again" is not recorded.
- **What that does not cover:** these were in-flow compactions, which cannot raise the EXP-052 error (section 7 item 3). So this run shows compaction under the `LlmAgent` root without a crash. It does not exercise the post-invocation path that crashed EXP-052. That path was never reachable with this root: from the source, an `LlmAgent` root supplies the summarizer [V, `reference/compaction.md` (d)].
- **Mean wall:** recorded above, against 89.5 s.

**Prediction check.**
- N = 0 fell in the predicted 0-1, given probability 0.7.
- Row 3 fired; it was predicted at about 0.45.
- The root transferred on its first message on 8 of 8, as predicted.
- The two EXP-061 `read_file`-first tasks transferred directly; this was predicted at 0.6.
- The prediction held.

**Resolves, recorded and not read:** 1 of 8 (`rich_3006`, as in EXP-061). n = 8, and resolves are not an endpoint.

**Not licensed:**
- Any verdict on the re-transfer prompt after a nudge.
- Any resolve or LB claim.
- Any upload or dev-48 run.
