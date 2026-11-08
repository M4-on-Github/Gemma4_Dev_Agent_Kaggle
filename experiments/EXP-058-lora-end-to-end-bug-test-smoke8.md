# EXP-058 — does an adapter-bearing submission run cleanly end to end? The EXP-054 v2 LoRA in the E4B tree, on smoke-8

**Date:** 2026-11-08
**Type:** smoke-8 bug test, one arm (`a`), one kernel, about 0.30 to 0.36 L4x4-h (point; conditional worst case about 1.24 h, section 2.5). Approved by the user about 21:25 UTC (`knowledge/user-decisions.md`, commit 996d879): "make sure our lora can run with no problems or bugs". One kernel push, within today's 4.0 GPU-h ceiling.
**Cohort:** smoke-8
**Ladder:** L2. No critic prereg: under 1 GPU-h and not an upload.
**Pre-registered:** this file, the two build tools, the full-zip manifest and the notebook are committed before the push. Sections 3 and 4 are written blind and are not revised; results are appended as a new section.
**Serves:** the LoRA line (C-024; EXP-047 canary, EXP-054 training and effect). Where and how to use a LoRA is re-derived later; this run makes **no effect claim**. EXP-054 R4 stands as the effect reading.
**Relates:** EXP-054 (the adapter, v2, R4), EXP-047 (adapter serving canary), EXP-033 (the tree), EXP-038, EXP-045, EXP-052, EXP-053, EXP-056 r1 (bug references on the same 8 ids).
**Tags:** [V] verified in source on disk, in a trace, or by a check run here; [I] inference.

## 1. Why this, now

EXP-054 trained and scored the adapter inside its own training notebook. That notebook made its compile path (`notebooks/exp054_copylora/copy_lora.py`, `compile_agent`) register the adapter in the model registry with `server.create_model_registry`. Then `resolve_swegemma_adapter` returned the registry entry. No adapter-bearing tree has been through the eval notebook, the `swegemma` `Evaluator`, the sandbox and the grader.

**What this test exercises that no earlier run did [V, source].**

- The eval notebook registers only the base aliases: `models.register(alias, LiteLlm(model=f'openai/{target_id}', ...))`, in the vLLM cell of `notebooks/kaggle_eval_l4x4.py`. The harness runner passes `adapter_resolver_fn=lambda base, info: resolve_swegemma_adapter(base, info, config.models)` (`data/src/swegemma/swegemma/harness/agent_runner.py:625`).
- `copy_lora` is not in that registry, so `resolve_swegemma_adapter` (`agent_runner.py:64-92`) takes its other branch, `base_model.model_copy(update={'model': 'openai/copy_lora'})` (:75-85). That branch has never run in this repo.
- LiteLlm sends `llm_request.model or self.model` (`google/adk/models/lite_llm.py:2230`) and copies its private `_additional_args` (api_base, api_key) along. It records `model_version=response.model` (:1668), so a trace shows which served model answered.
- `VllmServer.build_cmd` sizes `--max-loras` to the number of mounted adapters (1 here) and rounds `--max-lora-rank` up from the detected ranks (8). The notebook's `max_loras=8, max_lora_rank=128` are fallbacks only (`data/src/adk_submission/adk_submission/server.py:759-797`). This settles the EXP-047 note "3/8, which one wins".

**Per-sub-agent adapters, a desk check (source read, not built, not runtime-tested).** `adapter:` can be set on any LlmAgent in the tree, not only the root:

- `adapter: str | None = None` is a field of `SandboxedLlmAgentConfig` (`adk_submission/adk_submission/schema.py:257`, field at :279, doc at :263). Container agents (Sequential, Parallel, Loop) have no such field.
- Every LlmAgent is built by `build_llm_agent`, which calls `resolve_model(config, ctx)` (`builders/llm.py:71`). Sub-agents compile recursively through `compile_sub_agents` → `_compile_agent` (`builders/sub_agents.py:17-69`, dispatch at `compiler.py:231-233`).
- `resolve_model` (`resolvers/models.py:46-77`):
  - raises `AdapterNotFoundError` if the name is not in the manifest (:47-53);
  - requires `model:` on the same agent (:54-58);
  - calls the runner's `adapter_resolver_fn` when one is given (:61-62).
- Our validator collects adapters per visited agent (`tools/validate_submission.py:238-242`) and runs `check_adapter` per agent (:526).
- Server side, each distinct adapter is one `--lora-modules` entry; `--max-loras` equals their count.
- Not built now.

## 2. Design

### 2.1 The tree (zero GPU, built and checked here)

`dist/EXP-058/candidate-a/` (gitignored, because the adapter weights may not enter git) is built by `experiments/EXP-058/make_candidate.py tree`.

- **Base tree.** It is `experiments/EXP-033/candidate-e4b/`, the E4B loop's base tree (zip `9de869bd...1ac0`), with nothing changed except:
  1. one 3-line insert in `agent.yaml` after `model: gemma-4-e4b-it-qat-w4a16-ct`: two dated comment lines and `adapter: copy_lora`. The anchor matched once. `diff -ru` shows only this hunk and `Only in ...: adapters`.
  2. `adapters/copy_lora/` copied from `runs/EXP-054-copy-lora-v2/sub1/adapters/copy_lora/`, the output of kernel `rainm4/gemma4-exp054-copy-lora`, version 2.
- **Why EXP-033.** It is the tree every loop round starts from, and it has the most same-tree references on these 8 ids (EXP-033 and the EXP-038 subset, 16 task-runs). The loop's later trees add prompt or skill levers, and those would mix a second variable into a bug count.
- **Hash checks.** The tool verifies all four source files (LF) and both adapter files (binary) by sha256 before writing:

| file | bytes | sha256 |
|---|---|---|
| `adapters/copy_lora/adapter_config.json` | 645 | `cf87fdf065108e1f77f76fb706bf007cf5e5b5aebf1951310f88baecf1bdf2db` |
| `adapters/copy_lora/adapter_model.safetensors` | 6,676,712 | `c4af0041176a02b7b718d6fc4f9fd8990f30c7aea1946d1da3529f5a190e6d64` |
| `agent.yaml` (edited) | | `2acb50942a18b307802493a0c09131799816c2d5701dc89c74649a63c80dc0c9` |
| `configs/sampling.yaml`, `eval_config.yaml`, `prompts/system.md` | | unchanged from EXP-033 (`63005688...`, `916cf6cb...`, `57a20af4...`) |

- **The adapter config.** peft_type LORA, r 8, lora_alpha 16, target_modules q_proj and o_proj.

### 2.2 Validate and pack: the first adapter-bearing pack in this repo [V]

- **Tree validation.** `validate_submission.py dist/EXP-058/candidate-a --strict` reports 1 ERROR and 2 WARN.
  - ERROR: worst case `120 x (8 + 1.0) min = 18.00 h`, over the gate. This is the EXP-033 tree's own cap, carried unchanged.
  - WARN: shipping an adapter; the VERIFY(Q4) logprob canary must pass on the scorer stack. Q4 is settled by EXP-047 and EXP-054, so this warning is expected.
  - WARN: `timeout_seconds=240 < 300`, also the baseline's.
  - `--official` notes "official adk-submission validator not importable (No module named 'adk_submission')". The wheels do not import on this machine, so the official validator runs in-kernel instead (section 2.4, check A5).
- **Pack.** Command: `pack_submission.py --src dist/EXP-058/candidate-a --out dist/EXP-058-a.zip --skip-budget-gate --allow-warnings`. This is the EXP-033 override, for a smoke screen whose zip is never uploaded (UNOFFICIAL TEST BUILD).
  - Result: PACK OK, 3 WARN, 0 ERROR.
  - The closure has 6 members: the 4 tree files and both adapter files. The packer's closure follows `adapter:` into `adapters/copy_lora` (`validate_submission.py:205-246`).
  - Size: 5,112.2 KiB zipped, 6,524.9 KiB unpacked.
  - **sha256 `25cf9aacefae11aa35c6fc02f12afcad03813608e214b96995d9b73af7634bbb`.** A repack from the same tree gave the same sha.
- **Archive validation.** `validate_submission.py dist/EXP-058-a.zip --strict` gives the same set: 6 members, the gate ERROR (there is no `--skip-budget-gate` at archive level) and 2 WARN. No adapter-specific error.
- **Upload rule conflict.** `.gitignore` has `*.safetensors`. `check_repo_hygiene.py` fails `.safetensors` (BAD_EXT) and any file over 5 MiB. plan.md:78 gitignores adapter weights. So **no adapter-bearing zip can reproduce from committed LF blobs**, the check `submissions.md` relies on. Here the adapter's sha256 is recorded in this file instead and checked in-kernel. For an upload, how to verify an adapter zip is the user's decision (section 5).

### 2.3 Transport: light zip embedded, weights from `kernel_sources`

- **Light zip.** `make_candidate.py light` drops the one `.safetensors` member from the full zip, keeping order, date_time, compression and modes. It writes `dist/EXP-058-a-light.zip` (3,065 bytes, **sha256 `73aedc886db14212ea4abfef8b0036f7c7db68250caffa859e72d2c4c6b051f0`**). It also writes `experiments/EXP-058/full_manifest.json`, the path → sha256 map of all 6 members of the full zip (hashes only, committed).
- **Weights.** `kernel-metadata.json` has `kernel_sources: ["rainm4/gemma4-exp054-copy-lora"]`. That is our own private kernel, and its latest version is v2. No new dataset or public resource is created.
- **Why not embed the full zip.** It would put about 6.8 MB of base64 adapter weights into a notebook. Under the hygiene rule that notebook could not be committed, and the push size limit is unknown. kernel_sources keeps the notebook at about 49 KB and committable. Its one unknown, the mount path, is handled by a search plus a sha check.
- **Version pin.** A later v3 of the source kernel would fail the sha check and stop the run before boot. It would not run a different adapter.

### 2.4 In-kernel checks (generated by `experiments/EXP-058/make_nb_src.py` from the eval template, LF sha `f307ac36...2d19`)

The generator inserts three cells and four parameters and changes nothing else. Each anchor must match once. Output: `notebooks/exp058_lora/kaggle_eval_adapter.py`, 598 lines. All results go to `RUN_DIR/adapter_check.json`. Any failure in A or B raises `SystemExit` before the first task.

- **A, pre-boot (after unpack):**
  - A1: the embedded light zip has the recorded sha.
  - A2: mounts under `/kaggle/input` (3 levels) are searched for names containing `exp054` or `copy-lora`; only a file with the recorded sha is accepted for each adapter file, and it is copied into `AGENT_DIR/adapters/copy_lora/`.
  - A3: the assembled tree's path → sha map equals the full manifest exactly.
  - A4: `discover_adapters` returns `{copy_lora: rank 8}`.
  - A5: the official `validate_directory` with `build_submission_limits()` does not raise.
- **B, post-boot (after the base decode probe):**
  - B1: `/v1/models` lists `copy_lora`.
  - B2: the vLLM LoRA flags (`--max-loras`, `--max-lora-rank`, `--lora-modules`) and the KV pool (from `server.log_path`), recorded only.
  - B3: `compile_submission` with the notebook's own `models` registry and `resolve_swegemma_adapter`, the runner's path. Stub tools are used, as in EXP-054.
  - B4: the root model string must end in `copy_lora`.
  - B5: one live call through that model object must come back with a `model_version` ending in `copy_lora`.
  - B6: an adapter decode probe, 400 tokens, beside the base probe.
  - A compile exception whose class name is not adapter-, model- or validation-related is recorded and does not stop the run.
- **C, post-run:** for each trace, counts of steps whose `model_name` ends in `copy_lora`, other, or none, and the same for `tool_calls[].extra.model_version`, plus the ids of any task with an "other" step. Counts and ids only.

### 2.5 Cost

- **Point estimate.** The prior E4B smoke-8 kernels spanned 0.25, 0.31, 0.281 and 0.281 h (EXP-033, 052, 053, 056 r1), with server start 323 to 349 s. EXP-054 measured a decode drop of 0.168 with the adapter. Scaling the generation share gives **0.30 to 0.36 h**.
- **Conditional worst case.** If all 8 tasks hit the 8-minute cap, about 1.24 h.
- **Day.** About 2.18 used, plus EXP-057 (about 0.6), plus this run, is about 3.1 h at point estimates. That is inside 4.0. The joint worst case could pass 4.0; whether to accept that is the lead's call.

## 3. Endpoints, fixed in advance

All endpoints come from `adapter_check.json`, `task_results.jsonl`, the official traces, `tools/analyze_traces.py runs/EXP-058-a --cap-minutes 8 --max-calls 28` and `tools/run_forensics.py forensics runs/EXP-058-a`.

- **P:** all of A1 to A5 and B1 to B5 passed, and `ADAPTER_CHECK.failures` is empty.
- **F (fall-through):** the number of trace steps with a non-null `model_name` not ending in `copy_lora`, plus the number of tool-call `extra.model_version` values not ending in `copy_lora`. **Routing unread** if no step in any trace has a non-null `model_name`.
- **E:** tasks with a non-empty `error`. E_ad is those whose error names an adapter-side class: AdapterNotFoundError, ModelNotFoundError, NotFound/404, or an exception text containing `lora` or `adapter`.
- **M:** tasks with at least one malformed call. **Z:** tool-free endings, meaning zero calls, or the harness's fixed "completed execution without calling submit_patch" message.
- **K:** tasks with `time_cap_hit` or `calls_cap_hit`. **W:** tasks with `wall_s` over 495 s.
- **Record, not read:**
  - applied edits, `n_edit_fail` and `n_edit_arg_loss`, first tool;
  - resolves of 8, mean and longest wall;
  - base and adapter decode tok/s, server start, KV pool, the LoRA flags.
  - GPU-h comes from the kernel-log span.

**References** on the same 8 ids, from committed `summary.jsonl` files (`out/exp058_refs.py`):

| run | E | Z | M | K | max wall s | edit fails |
|---|---|---|---|---|---|---|
| EXP-033 | 0 | 0 | 0 | 0 | 90.7 | 7 |
| EXP-038 (smoke subset) | 0 | 0 | 0 | 0 | 147.2 | 10 |
| EXP-045 | 0 | 0 | 0 | 0 | 83.7 | 5 |
| EXP-052 | 1 | 0 | 0 | 0 | 141.9 | 3 |
| EXP-053 | 0 | 0 | 0 | 0 | 150.5 | 8 |
| EXP-056 r1 | 2 | 2 | 0 | 0 | 152.8 | 6 |

- **Same-tree base.** EXP-033 plus the EXP-038 subset is 16 task-runs: 0 E, 0 M, 0 Z, 0 K, longest 147.2 s.
- **Tool-free endings.** The E4B base rate is about 1 in 54 task-runs (EXP-038 dev-48 fastapi_13537, EXP-055 fastapi_14448).

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

The first row that matches is the reading.

| row | condition | reading |
|---|---|---|
| 1 Infrastructure | P false (any pre-task check failed, or the kernel stopped before task 1), or routing unread, or F ≥ 1 | the adapter-bearing path has an infrastructure defect; name the failed check or the fall-through tasks; no bug reading of the agent run |
| 2 Bug | E_ad ≥ 1, or E ≥ 2, or M ≥ 2, or Z ≥ 2, or K ≥ 1, or W ≥ 1 | an adapter-bearing submission does not run cleanly; name the trigger(s) and tasks |
| 3 Clean | none of the above | an adapter-bearing E4B submission runs end to end through the eval notebook, the runner's `model_copy` routing, the sandbox and the grader without an attributable bug, on 8 tasks |

- **Thresholds.** The bug thresholds sit above what the references show: E 0 to 2 of 8, Z 0 to 2, M and K 0, longest wall 152.8 s. One error or one tool-free ending is within the base E4B's behaviour and is recorded, not read.
- **A slower decode is not a bug.** EXP-054 measured a drop of 0.168; it is recorded.
- **Resolves are not read**, in either direction.

**Blind prediction:**

| reading | probability |
|---|---|
| row 3, Clean | 0.65 |
| row 1, Infrastructure | 0.20 |
| row 2, Bug | 0.15 |

- **Row 1.** The likeliest cause is the mount search (A2), then the untested `model_copy` branch (B4/B5).
- **Row 2.** The likeliest cause is a malformed-call or tool-free-ending rise from the adapter's effect on the call format; EXP-054's drift gate failed on G1 and G4.
- **Resolves.** 1 to 3 of 8.
- **Adapter decode.** About 45 to 50 tok/s against about 56 base.

## 5. What this licenses

- **Row 3.** It licenses the statement "an adapter-bearing tree runs cleanly on the eval path" for later LoRA experiments. It does not license an upload, a dev-48 arm, or any effect claim.
- **Row 1 or 2.** It names the defect. No re-run without the user's word.
- **Upload verification.** For any future upload of an adapter-bearing zip, the repo's check that the sha reproduces from committed LF blobs cannot hold, because the weights may not be committed (section 2.2). How such a zip is verified is **the user's decision**. This file proposes nothing.

## 6. Exact commands

```
python -I -X utf8 experiments/EXP-058/make_candidate.py tree experiments/EXP-033/candidate-e4b runs/EXP-054-copy-lora-v2/sub1/adapters/copy_lora dist/EXP-058/candidate-a
python tools/validate_submission.py dist/EXP-058/candidate-a --strict
python tools/pack_submission.py --src dist/EXP-058/candidate-a --out dist/EXP-058-a.zip --skip-budget-gate --allow-warnings
python tools/validate_submission.py dist/EXP-058-a.zip --strict
python -I -X utf8 experiments/EXP-058/make_candidate.py light dist/EXP-058-a.zip dist/EXP-058-a-light.zip experiments/EXP-058/full_manifest.json
python -I -X utf8 experiments/EXP-058/make_nb_src.py notebooks/kaggle_eval_l4x4.py experiments/EXP-058/full_manifest.json notebooks/exp058_lora/kaggle_eval_adapter.py
python tools/build_notebook.py --src notebooks/exp058_lora/kaggle_eval_adapter.py --embed dist/EXP-058-a-light.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-058-a"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp058_lora/kaggle_eval_l4x4.ipynb
# analysis job (later):
python tools/analyze_traces.py runs/EXP-058-a --cap-minutes 8 --max-calls 28
python tools/run_forensics.py forensics runs/EXP-058-a
```

Then hand-write `kernel-metadata.json` from `notebooks/exp056_r1/`'s, with id and title `gemma4-exp058-lora` and the kernel_sources entry.

## 7. Defects and limits of this pre-registration

- **Not tested in-kernel.** The A and B check cells were syntax-checked and clash-scanned here, but `adk_submission` does not import locally, so they first execute in the kernel. A defect in a check cell stops the run in row 1. The analysis must then say whether the check or the path failed.
- **Untested mount path.** The kernel_sources mount path is not known in advance; A2 searches for it. If the mount is absent, A2 fails and the reading is row 1, not a defect of the adapter path.
- **One tree, one adapter, root agent only.** The per-sub-agent case is a desk fact (section 1), not tested.
- **Small n.** 8 tasks cannot detect a rare bug. Row 3 bounds only frequent failures.
- **Sandbox.** It is the Kaggle `subprocess` sandbox, as in every E4B smoke run, not the scorer's Docker.
- **A gap in check B (found before the push; the readings are unchanged).** Suppose `compile_submission` raises an exception whose class name is not adapter-, model- or validation-related. Cell B then records `compile_error`, skips B4 and B5, and leaves `failures` empty, so P would read true with the routing checks not evaluated. If `adapter_check.json` carries `compile_error`, the analysis reports B4 and B5 as not evaluated. Row 1 then rests on F and E, which cover the same routing at run time through the traces and the task errors.

- **Logged after the fact (2026-11-08, analysis):** cell A's A5 record reads the adapter count from the wrong attribute (`adapters`; the field is `adapter_files`), so that count is unread. A5's pass condition, that the validator does not raise, is unaffected (section 9.4).

## 8. Built

- **Commit 8cf11a8:** this file, `experiments/EXP-058/make_candidate.py`, `make_nb_src.py`, `full_manifest.json`, `notebooks/exp058_lora/` (the source `kaggle_eval_adapter.py`, the notebook and `kernel-metadata.json`) and the README row.
- **Kernel:** id `rainm4/gemma4-exp058-lora`, kernel_sources `rainm4/gemma4-exp054-copy-lora`, model source `google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2`, NvidiaL4, no internet.
- **Notebook:** embeds the light zip, sha `73aedc88...b051f0`, which the check read back from the built notebook. The parameter cell has `RUN_AGENT = True`, `RUN_GOLD_CONTROL = False`, `EXP_ID = "EXP-058-a"` and `TASK_IDS` = the 8 smoke-8 ids.
- **Local checks:** `python -m pytest`, 49 passed; repo hygiene OK.
- **Push held.** One status call each at 21:46 UTC found `rainm4/gemma4-exp057-r1` and `rainm4/gemma4-exp057-r2` both RUNNING, so both GPU slots were in use. Per the lead's slot note there was no wait and no polling.

- **Pushed 2026-11-08, 21:56 UTC**, on the lead's word that a slot was free (`rainm4/gemma4-exp057-r1` COMPLETE at 21:56, r2 still RUNNING). The push was the bare command run once from `notebooks/exp058_lora`, and the guard passed it. The CLI reported "Kernel version 1 successfully pushed." One status call right after gave `KernelWorkerStatus.RUNNING`.
- **Cost:** the lead accepted the joint worst case, because no E4B task has passed 176 s.

---

## 9. Results, 2026-11-08. Section 4's readings applied as written.

**Source.** Kernel `rainm4/gemma4-exp058-lora` version 1 was COMPLETE at 22:15 UTC. It was downloaded to `runs/EXP-058-a/` and the nested bundle moved up one level. The analysis read the following files with `-I -X utf8`, and copied `summary.jsonl` to `experiments/EXP-058/a/summary.jsonl`:
- `adapter_check.json`;
- `python tools/analyze_traces.py runs/EXP-058-a --cap-minutes 8 --max-calls 28`;
- `python tools/run_forensics.py forensics runs/EXP-058-a`;
- the kernel log;
- the per-trace counts from `out/exp058_tasks.py` (names and counts only).

### 9.1 Pre-task checks (from `adapter_check.json`; `failures` is empty, and there is no `compile_error`)

| check | result |
|---|---|
| A1 light zip sha | `73aedc88...b051f0`, equal to the recorded value |
| A2 mount and weights | one mount, `/kaggle/input/notebooks/rainm4/gemma4-exp054-copy-lora`; 1 candidate per file, both sha-matched; the config came from the light zip, the weights were copied in from `sub1/adapters/copy_lora/` |
| A3 tree equals the full manifest | true (6 files) |
| A4 `discover_adapters` | `{copy_lora: rank 8, safetensors, 6,676,712 bytes}` |
| A5 `validate_directory` | did not raise; returned `SubmissionDirectory`. Its adapter count is **unread** (section 9.4 item 1) |
| B1 `/v1/models` | the base model path and `copy_lora` |
| B2 LoRA flags | `--enable-lora`, `--max-loras 1`, `--max-lora-rank 8`, `--lora-modules copy_lora=<AGENT_DIR>/adapters/copy_lora`. The notebook passed 8 and 128, and the manifest sizing won, as the source says (section 1) |
| B3 compile | `swegemma.create_tools` with stub context; registry without the adapter (`registry_has_adapter` false), so the `model_copy` branch ran |
| B4 root model | `openai/copy_lora`; `api_base` is the server's |
| B5 live call | `model_version` `copy_lora` |
| B6 decode probes | adapter 87.2 tok/s (400 tokens in 4.59 s); base 56.2 tok/s (400 in 7.11 s) |

KV pool: 263,360 tokens, max concurrency 40.26. vLLM came up in 392.5 s.

**P is true.** All of A1 to A5 and B1 to B5 passed and were evaluated. None were skipped.

### 9.2 Served model per trace

Each of the 8 traces has 2 unnamed steps (non-model steps). Every model-named step and every tool-call `model_version` was `copy_lora`.

| task | adapter steps | other | share | call versions adapter / other |
|---|---|---|---|---|
| fastapi_14301 | 9 | 0 | 1.000 | 7 / 0 |
| fastapi_14448 | 6 | 0 | 1.000 | 4 / 0 |
| fastapi_14605 | 14 | 0 | 1.000 | 11 / 0 |
| httpx_3672 | 16 | 0 | 1.000 | 14 / 0 |
| requests_7205 | 11 | 0 | 1.000 | 5 / 0 |
| requests_7309 | 14 | 0 | 1.000 | 9 / 0 |
| rich_3006 | 13 | 0 | 1.000 | 11 / 0 |
| rich_3468 | 12 | 0 | 1.000 | 6 / 0 |
| total | 95 | 0 | 1.000 | 67 / 0 |

The in-kernel cell C gave the same totals (95, 0, 16; 67, 0). **F = 0, and the routing is read.** For contrast, the EXP-033 base traces on the same ids have 76 named steps, all served by the base path.

### 9.3 Endpoints and the reading

| endpoint | EXP-058 | same-tree base (EXP-033 + EXP-038 subset, 16 runs) |
|---|---|---|
| E (error tasks) / E_ad | 0 / 0 | 0 |
| M (malformed-call tasks) | 0 | 0 |
| Z (tool-free endings: zero calls or no `submit_patch`) | 0 (8 of 8 submitted) | 0 |
| K (time or call caps) | 0 | 0 |
| W (over 495 s) | 0; longest 136.8 s | longest 147.2 s |

- **Row 1, Infrastructure:** no. P is true, the routing is read, and F = 0.
- **Row 2, Bug:** no. Every trigger is zero.
- **Row 3, Clean: fires.** An adapter-bearing E4B submission runs end to end without an attributable bug, on 8 tasks. The path covered the eval notebook, the runner's `model_copy` routing, the sandbox and the grader.

As section 5 says, this licenses no upload, no dev-48 arm and no effect claim.

### 9.4 Recorded, not read

| field | EXP-058 | EXP-033 (same tree, base model, same ids) |
|---|---|---|
| edit_file calls / not found or failed / applied | 20 / 10 / 10 | 17 / 7 / 10 |
| per task, failed of edit calls | fastapi_14605 3 of 6, httpx_3672 4 of 5, rich_3006 3 of 4, other five 0 of 1 | fastapi_14605 4 of 9, requests_7205 3 of 3, httpx_3672 no edit call, other five 0 of 1 |
| arg-loss | 0 | 0 |
| first tool | `run_command` 8 of 8 | `run_command` 6, `read_file` 2 |
| write_file calls | 0 | 0 |
| identical repeats | 2 | 4 |
| compactions | 2 | 1 |
| resolves | 1 of 8 (fastapi_14301) | 2 of 8 |
| mean / median / longest wall | 75.7 / 69.1 / 136.8 s | 56.9 / n.r. / 90.7 s |
| mean calls | 7.25 | n.r. |

- EXP-038 subset edit fails on these ids: 10. "n.r." means not computed for the reference here.
- **Decode speed.** The adapter probe ran 87.2 tok/s against 56.2 for the base. That is the opposite of the 45 to 50 predicted, but **the order confounds it**. The base probe is the first request after boot in every eval kernel, and it has read 55.6 to 56.4 in all four prior E4B kernels. The adapter probe ran second, after warm-up. EXP-054's 0.168 drop was measured under matched conditions, and this run neither replaces nor reads against it.
- **Server start.** 392.5 s here, against 322.9 to 348.5 s in the four prior E4B eval kernels: about 44 to 70 s longer with LoRA enabled. That is one boot, not per task.

**Check-cell defect, A5 (found here; it does not change P).** Cell A read the adapter count from `getattr(_sd, 'adapters', [])`. The field of `SubmissionDirectory` is `adapter_files` (`adk_submission/discovery.py:50`), so the recorded 0 is a wrong attribute, not a count. A5 tests that `validate_directory` does not raise, and it did not.

### 9.5 Cost and prediction

- **GPU-h:** the last kernel-log entry is at 1,136.1 s, so **0.316 h**. That is inside the 0.30 to 0.36 point estimate. The 8 tasks took 9.5 min of agent wall (`run_forensics`).
- **Prediction.** Clean was the most likely row (0.65) and it fired. Resolves landed inside the predicted 1 to 3. The adapter-decode prediction was wrong in direction, and it is not interpretable here (section 9.4).

## Status

COMPLETE 2026-11-08. Pre-registered and built at 8cf11a8; pushed 21:56 UTC; kernel COMPLETE at 22:15 UTC. **Row 3, Clean.** GPU-h 0.316. No follow-up is queued. Where and how to use a LoRA is to be re-derived, and an adapter-zip upload needs the user's decision on verification (section 5).
