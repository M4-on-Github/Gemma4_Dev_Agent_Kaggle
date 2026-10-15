# Experiments

Index of verification items, experiment logs and LB submissions. Numbers go here, not in chat.
Confidence tags as in plan.md: **[V]** verified against official files/pages, **[M]** community mirror(s),
**[I]** inference. Nothing below has been verified against official files yet (kaggle.com was unreachable
from the build environment); every row starts OPEN.

## 1. Verification checklist (plan §3.4) — status OPEN unless stated

| # | Question | Where to look | Current default in repo | Evidence so far | Status |
|---|---|---|---|---|---|
| Q1 | Exact compile-time tool registry; are `run_skill_script` / `load_skill_resource` real; graph tools present? | `phase0_report.json` from `notebooks/kaggle_eval_l4x4` (greps the installed `swegemma`/`adk_submission` source); `HARNESS_README.md` §6 | 9 tools declared in `submission/agent.yaml`; no skills | HARNESS_README mirror lists exactly 9 harness tools; ADK SkillToolset adds list_skills/load_skill/load_skill_resource/run_skill_script when `skills:` is set; one team hit ToolNotFoundError [M] | OPEN |
| Q2 | `agent.yaml` / `sampling.yaml` / `eval_config.yaml` schema and field names | `data/raw/sample_submission/*` (diff against `submission/`), `adk_submission` schema source, `swegemma/config.py` | `evaluation: {max_time_minutes, max_tool_calls, max_turns, timeout_seconds}`; plain tool-name list; `agent_tool: {config_path, skip_summarization}`; model `gemma-4-31b-it-qat-w4a16-ct` | HARNESS_README mirror §2 + §7.1 and 4 community repos agree [M]. Open sub-questions: does `timeout_seconds` also cap the grading pytest (one source-reading says yes [M]); is `..` allowed in `!include` (mirrors disagree; we allow it when it stays inside the root) | OPEN |
| Q3 | Does `thinking_budget` bind? | `adk_submission/resolvers/generation.py` (grep in phase0_report); compare `total_completion_tokens` for budget 128 vs 1024 on smoke-8 | `include_thoughts: true`, `thinking_budget: 256`, `max_output_tokens: 4096` | Source reading by one team: only `enable_thinking` on/off is forwarded; budget ignored [M]. HARNESS_README mirror recommends budget 4096 + max_output 16384 (too slow for 4.5 min) | **ANSWERED [V]** — `thinking_budget` IS forwarded |
| Q4 | LoRA zeroing in patched vLLM | Kaggle discussions 743508 / 743213; logprob canary notebook (not built yet) | no adapter shipped | host acknowledged adapters wiped [M] | OPEN — gate G-LoRA Oct 25 |
| Q5 | Which public tasks fail with the gold patch? | EXP-000 full sweep, `runs/EXP-000-all/gold_control.jsonl` (+ `runs/EXP-000-final` rerun) + `gold_failures.txt` | all 18 terminal `instance_id`s excluded (see `gold_failures.txt`) | one report: 107/129 pass [M]; another: 119/129 sound [M] - both conflate distinct mechanisms | **ANSWERED [V]: 111/129 sound (86.0%), 18/129 terminal** (full 129-task sweep, 2026-10-14, after making the pygments pin a curation default). By repo: requests 5/13, rich 42/48, fastapi 63/67, httpx 1/1. All 21 originally-failing tasks individually root-caused into 7 mechanisms (see 1g): 3 were pool-version-ambiguity and are now fixed by default (`pygments==2.20.0` pin); 18 are terminal — inherent skipif pair (1), CPython-3.13-vs-legacy-library drift (2), unobtainable pytest plugin at file granularity (8), harness hardcodes `-p no:anyio` for every task regardless of declaration (3), pygments-pool-exhaustion with no further version to try (4). |
| Q6 | Entry/merger deadline: Nov 2 or Nov 25? | competition Overview > Timeline | plan treats Nov 2 as binding until disproven | A Sep-28 capture of the Timeline page says Entry + Team Merger **Nov 25**, final **Dec 2**, paper **Nov 12** [M, near-V]. Confirm on the live page, then update plan.md §1.2 | OPEN |
| Q7 | Compaction interval 5 vs 15; threshold 14,336 | `HARNESS_README.md` §7.2 vs starter notebook; traces (`compactions` column from `tools/analyze_traces.py`) | notebook parameter `COMPACTION_INTERVAL = 5` | README mirror: interval 5, overlap 2, threshold 14,336, retention 5; starter-notebook mirror used 15 [M] | OPEN |
| Q8 | Sandbox setup time per task | `setup_s` column (task wall minus agent duration) in `task_results.jsonl` | 1.0 min assumed in the estimator and the 11 h gate | host: a run with no patches takes ~10 min total incl. server start, i.e. seconds per task [M]; plan assumed 45–60 s [I] | OPEN |
| Q9 | Allowed extensions / size limit | `swegemma/config.py` (`ALLOWED_SUBMISSION_EXTENSIONS`, `MAX_SUBMISSION_SIZE_BYTES`) | `.yaml .yml .md .txt .py .json .safetensors`; < 3 GiB unpacked; no hidden files, no 0-byte files | README mirror §2.4 and the starter notebook's packaging cell [M] | **ANSWERED [V]** |
| Q10 | Decode speed / per-call overhead / prefix caching | notebook decode probe (`decode_probe` in summary.json); `output_tokens` vs `wall_s` in summary.jsonl | 25.5 tok/s + 0.6 s/call in the estimator | g4kit fit: 25.5 tok/s + 0.6 s (3 arms sharing a server, pessimistic) [M]; one real trace: 10,570 completion tokens in 288.6 s → ≥ 36.6 tok/s effective [M] | OPEN |
| Q11 | Actual weekly L4×4 quota | Kaggle account page after the first run | 30 h/week assumed [I] | — | OPEN |
| Q12 | `write_file` cannot create files outside `/workspace` (paths are rewritten under it) | HARNESS_README §6.2; a trace where the model tried `/tmp/repro.py` with write_file | prompt tells the model to create scratch files with a run_command heredoc in /tmp | starter-notebook mirror note + README mirror [M] | OPEN |

Phase 0 exit gate (plan §3): Q1, Q2, Q5, Q9 answered; EXP-000 done; `tools/validate_submission.py --official`
passes on `data/raw/sample_submission`. **Status as of 2026-10-14: gate NOT yet met.** Q5 and Q9
answered; Q1 and Q2 still OPEN (see table above). EXP-000 is done (full 129-task sweep, §1g/§1i).
`tools/validate_submission.py --official` currently reports `INVALID (3 errors, 5 warnings)` against
`data/raw/sample_submission` — missing/placeholder LoRA adapter files, an undeclared sub-agent adapter
path, and a prompt that names a public dev-set repo (FastAPI) in violation of plan §8.2's
repo-agnostic rule. These look like genuine defects in the official sample rather than a validator
bug, but have not been triaged against plan §8.2 to confirm; not yet investigated this session.

## 1b. Verified from wheelhouse source — 2026-10-14

Wheelhouse is a **public dataset**, so it downloaded without competition entry. Versions found differ from
plan.md §3.2: **`swegemma 0.2.11`** (plan said 0.2.7), **`adk_submission 0.2.13`** (plan said 0.2.11/0.2.12),
`adk_eval_core 0.1.0`, `google_adk 1.36.1`, `vllm 0.19.1`, `transformers 5.13.1`.
Wheels are **cp312** → harness Python is **3.12**, not the 3.11 in `pyproject.toml` (plan §3.3 guessed wrong).

### Q9 — extensions & size: ANSWERED [V]
`swegemma/config.py:19-31`. Exactly `.yaml .yml .md .txt .py .json .safetensors`; adapters `.safetensors` only;
`MAX_SUBMISSION_SIZE_BYTES = 3 GiB` unpacked. Additional caps the plan did not know, all from
`build_submission_limits()`: `max_yaml_size_bytes` 50 MiB, `max_skill_size_bytes` 50 MiB, `max_file_count` 10,000,
`max_yaml_files` 1,000, `max_instruction_chars` 1,000,000, `max_total_instruction_chars` 10,000,000,
`max_agents` 500, `max_sub_agent_depth` 50, `max_skills` 1,000, `max_loop_iterations` 500.
`!include` targets are restricted to `.md .txt .yaml .yml` (`yaml_loader.py:24-27`).
→ `tools/validate_submission.py` should assert all of these, not just extension + 3 GiB.

### Q3 — thinking budget: ANSWERED [V], community claim was WRONG
`adk_submission/resolvers/generation.py:359-445`, `apply_thinking_config_to_model()`. The budget **is** bridged to
vLLM, not just on/off:
- `thinking_config.thinking_budget` → `extra_body.thinking_token_budget`
- `enable_thinking` → `extra_body.chat_template_kwargs.enable_thinking`
- `thinking_budget <= 0` or `thinking_level: none` → `enable_thinking = False`; any budget > 0 → `True`
- `seed` is also forwarded, so **runs can be seeded** (plan §5.5 assumed seeds only via cohort choice)

`GenerationConstraints` (`config.py:60-67`): `max_output_tokens` range **1–32768**, `thinking_budget` range
**0–32768**; harness **defaults** are `max_output_tokens: 16384` and `thinking_budget: 4096`. Our 4096/256 is
legal and far cheaper. E2 remains worth running, but as a cost question, not a "does it bind" question.

### Harness already truncates output — changes plan §4.2
`swegemma/budget.py`, `HarnessLimits`: `command_timeout_seconds` 300, `max_stdout_chars` **5000**,
`max_file_lines` **150**, `max_file_chars` **10000**, `verification_timeout_seconds` 300.
→ The prompt's `| head -c 4000` guard is largely redundant (harness caps at 5000 chars), and `read_file` cannot
return more than 150 lines regardless of range. Revisit the overflow guards in `prompts/swe_coder.md`.

### Q2 — partially answered [V]; eval_config field names are a real risk
`EvaluationBudget` (`budget.py`) uses **`time_minutes, tool_calls, turns, cost_usd, total_tokens`** — *not* the
`max_*` names we ship. `EvalConfig` separately exposes flat convenience kwargs `max_time_minutes, max_tool_calls,
max_turns, max_llm_calls, timeout_seconds, verification_timeout_seconds`. Which set `eval_config.yaml` is parsed
into is still unresolved — needs `sample_submission/eval_config.yaml`, which is **behind competition entry**.
Two new budget knobs we never considered: **`cost_usd`** and **`total_tokens`** (a token cap may be a safer
budget guard than wall-clock), plus **`max_llm_calls`** distinct from `max_tool_calls`.
Sub-question resolved: `timeout_seconds` does **not** cap grading pytest — `verification_timeout_seconds` does.

### Q7 — partially answered [V]
`EvalConfig.events_compaction_config` defaults to **`None`** → compaction is off unless the harness run sets it.
Interval 5 vs 15 is therefore a *runner* parameter, not a fixed harness constant. Confirm what the official
run passes.

### Q1 — still OPEN
`adk_submission/registry.py` is a generic closed registry; organizers populate it before `compile_submission()`.
Tool names are not in the wheel — they come from the harness run. `swegemma/tools/{base,execution,graph,workspace}.py`
exist and a `graph/` package is present, so graph tools are real, but the exact registered names need a run.

## 1c. BLOCKER — competition not entered (plan §3.1)

`kaggle competitions list -s gemma-4` reports **`userHasEntered False`** for both `gemma-4-developer-agent` and
`gemma-4-developer-agent-paper`. Metadata listing works; every data download returns **403 Forbidden**.
Rules acceptance is click-through only and cannot be done via API.

Blocked until entered: `tasks.jsonl`, `sample_submission/` (closes the rest of Q2), `HARNESS_README.md`
(Q1, Q7, Q12), snapshots, graphs, embeddings — therefore EXP-000, cohort generation, and every L4x4 run.

Kaggle API access is otherwise working: authenticated as **`rainm4`** via `~/.kaggle/access_token`,
`kaggle kernels push/status/output` is the path for notebook runs, and `notebooks/kernel-metadata.json`
still has the placeholder id `YOUR_KAGGLE_USERNAME/gemma4-eval-l4x4` to fix.

## 1d. Verified from official files — 2026-10-14 (main track entered)

Entry accepted for `gemma-4-developer-agent` (`userHasEntered True`); downloads work.
**`gemma-4-developer-agent-paper` is still NOT entered** — separate entry, needed before Nov 12.
Source files: `data/raw/HARNESS_README.md`, `data/raw/sample_submission/*`, `data/raw/tasks.jsonl` (all gitignored).

### Q2 — ANSWERED [V]: our schema was already correct
`sample_submission/eval_config.yaml` + HARNESS_README:98 confirm the `evaluation:` wrapper and exactly four
optional keys `timeout_seconds, max_tool_calls, max_time_minutes, max_turns`. **Our `submission/eval_config.yaml`
matches.** Model name is the bare `gemma-4-31b-it-qat-w4a16-ct` (not the long `google/gemma-4/Other/...` path that
plan.md §1.3/§4.1 quotes) — **our agent.yaml is already correct; plan.md's prose is wrong.**
`adapter: <name>` is a top-level agent key. `..` in `!include` **is** legal (sample uses `../prompts/analyzer.md`);
only paths escaping the submission root raise `PathTraversalError` (HARNESS_README:102).
The official sample budget is **1 min / 10 tool calls / 50 turns / 60 s** — extremely conservative. The community
claim of a 60 min/100/500/3600 s sample (plan §4.4) is **wrong**; delete that warning.

### Q1 — ANSWERED [V]
HARNESS_README:45 says "SwegemmaContext (**9 Bound Tools** + Budget Gate)" and the sample declares exactly the 9
we ship, plus `agent_tool:` as a mapping. No `run_skill_script` / `load_skill_resource` anywhere in the sample.
**Our tool list is correct and complete.**

### Q7 — ANSWERED [V]: interval is 15, not 5
HARNESS_README:568-574 — `compaction_interval = 15`, `overlap_size = 2`, `token_threshold = 14,336`,
`event_retention_size = 5`. The starter-notebook mirror was right; the "interval 5" reading was wrong (5 is the
*retention* size). **`notebooks/kaggle_eval_l4x4` sets `COMPACTION_INTERVAL = 5` → fix to 15.**
State-note cadence in the prompt (§4.2, every ~5 turns) was tuned to the wrong number; E7 should re-centre on 15.

### Q12 — ANSWERED [V], and the real hazard is the OPPOSITE of what we assumed
HARNESS_README:687 — `submit_patch()` runs `git add -N . && git diff HEAD` inside `/workspace`, so **any untracked
scratch file left in `/workspace` is silently included in the submitted patch** (a likely cause of
mysterious test failures). `/tmp` is usable and is path-rewritten to sandbox dirs (line 261).
Our prompt already writes scratch to `/tmp/repro.py` via `run_command` — **correct, and now justified for the
right reason.** Keep it, and add an explicit pre-submit cleanup instruction.

### Q3 — fully CONFIRMED [V]
HARNESS_README:148 — `thinking_budget` 0..32768, default 4096; positive values set `enable_thinking: true` **and**
forward `extra_body.thinking_token_budget` to vLLM's `ThinkingTokenBudgetLogitsProcessor`; `0` sets
`enable_thinking: false`. Matches the wheel source read in §1b.
**Correction to our `configs/sampling.yaml` comment:** `include_thoughts: false` does **NOT** turn thinking off —
it still runs reasoning (`enable_thinking: true`) and merely strips `Part(thought=True)` from the response and
history (line 150). To actually disable thinking, set `thinking_budget: 0`. `sampling_nothink.yaml` must be
checked against this. Also: avoid `thinking_level` on the vLLM `/v1` endpoint (line 149).

### NEW RISK — truncated tool calls from small `max_output_tokens`
HARNESS_README:365 + 684: when a thought block plus a large `edit_file`/`write_file` call hits `max_output_tokens`,
the `<|tool_call|>` tag is cut off mid-call and the harness issues a nudge. The harness explicitly recommends
`thinking_budget: 4096` **with** `max_output_tokens: 16384`. Our 256 / 4096 is far tighter, and a *lower*
`max_output_tokens` makes this truncation **more** likely, not less — the opposite of plan §4.3/E11's premise
("4096 avoids overflow"). The 32k wall constrains prompt+output, but the per-turn truncation failure is a separate
mechanism. E11 must measure the nudge/unclosed-tag rate, not just overflow.

### Confirmed facts
- `tasks.jsonl`: **129 tasks**, fastapi 67 / rich 48 / requests 13 / httpx 1 — matches plan §5.2 exactly [V]
- Task fields: `instance_id, repo, base_commit, patch, test_patch, problem_statement, hints_text, created_at`
  (`patch` = the gold patch, so EXP-000 gold control needs no extra data) [V]
- Harness Python is **3.12** (cp312 wheels); `temperature: 0.2` is the official sample value, so plan §4.3's
  "scorer default 1.0" is wrong and E4's premise needs restating. Sample omits `top_k`; `allowed_fields=None`
  in `GenerationConstraints` means extra fields such as our `top_k: 64` are still permitted.

## 2. Observed numbers (fill in as they arrive)

| Item | Value | Source | Date |
|---|---|---|---|
| vLLM server start on L4×4 | | `summary.json: server_start_s` | |
| Decode tok/s (probe) | | `summary.json: decode_probe` | |
| Mean setup_s | | `aggregates.json: setup_s_used` | |
| Baseline run-to-run variance (same config, 2 seeds, dev-48) | | EXP-001a/b | |
| Weekly GPU quota | | | |

## 3. Experiment index (one row per `EXP-NNN-<slug>.md`)

| ID | Date | Variable | Cohort | Resolve | Empty % | Overflow % | Malformed % | Spin % | Median wall | Proj. 12 h | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EXP-000 | | gold control (no model) | all 129 | | — | — | — | — | | — | |
| EXP-001 | | baseline v1 (phased prompt, thinking 256, T 0.2, 4.5 min/45 calls) | smoke-8 → dev-48 | | | | | | | | |

Log template (`experiments/EXP-NNN-<slug>.md`):

```
id: EXP-NNN-<slug>        date:            owner:
hypothesis:
single variable changed:  (git diff link / file:line)
cohort:                   seed:            GPU-h used:
config: git tag / commit, zip sha256, eval_config, sampling
results: resolve % (Wilson CI), empty %, overflow %, malformed %, spin %, median/p90 wall, projected 12 h, worst case
per-repo: fastapi / rich / requests / httpx
decision: adopt | reject | rerun        (rule: Δ ≥ +3 tasks on dev-48 AND no process-metric regression)
follow-ups:
```

Cohorts live in `experiments/cohorts/*.txt` (task ids only; generated by `tools/make_cohorts.py --seed 20261013`
after excluding EXP-000 failures). Raw traces stay in `runs/` (gitignored); only `summary.jsonl`/`aggregates.json`
may be copied into `experiments/EXP-NNN/`.

## 4. Submissions log (1 per day; 2 finals)

| Date (UTC) | Git tag | zip sha256[:12] | dev-48 | held-out-24 | Public LB | Scoring wall | Notes |
|---|---|---|---|---|---|---|---|
| | v1 | | | | | | first submission target Oct 17 |

Rules reminders: never submit a config that has not run on dev-48 with projected worst case ≤ 11 h; ignore LB
moves < 0.035 (2 tasks); last submission ≤ Dec 1 23:00 UTC.

---

## 1e. EXP-000 run log and the subprocess-sandbox blocker — 2026-10-14

Kernel `rainm4/gemma4-exp000-gold-control`, CPU-only (zero GPU quota). Five pushes; v1–v4 ERROR,
**v5 COMPLETE**. Logs in `runs/EXP-000-push{1..5}/` (gitignored).

| v | Outcome | Cause |
|---|---|---|
| 1 | ERROR | one bulk `pip install ... check=True`; a single cp312 wheel (`apache_tvm_ffi`) on Kaggle's **py3.13** CPU image aborted all 41 |
| 2 | ERROR | our own guard used the *distribution* name `google_adk`; the import is `google.adk` |
| 3 | ERROR | submission-unpack cell ran unconditionally, but a gold-control run has no submission |
| 4 | ERROR | `validate_single_declared_model` **does not exist** — invented name from a community starter mirror |
| 5 | COMPLETE | ran end-to-end; 8/8 tasks graded |

### Q5 is NOT answered. The 0/8 result is an artifact of our harness, not the tasks. [V]

v5 reported `0/8 resolved`, every task failing with the *same* error:

```
TypeError: Router.__init__() got an unexpected keyword argument 'on_startup'
```

Identical failure across 8 unrelated tasks = environment, not task breakage. Root cause, from source:

```python
# swegemma/harness/container_setup.py:513 and :528
def install_editable_package(...):
    if type(docker).__name__ in {'SubprocessManager', 'SubprocessSandbox'}:
        return          # <-- early return
def install_test_dependencies(...):
    if type(docker).__name__ in {'SubprocessManager', 'SubprocessSandbox'}:
        return          # <-- early return
```

**`sandbox='subprocess'` never installs per-task dependencies — by design.** It assumes a pre-built
image. Tests therefore ran against Kaggle's *inherited* site-packages, whose Starlette is far newer
than these FastAPI commits expect.

Corroborating evidence that per-task deps are the intended mechanism: the competition ships
**57 distinct `starlette-*.whl` versions** (0.19.0 … 1.6.0) in `wheels/` — one per task pin. There is
**no pip wheel** in that set, and the kernel runs with internet disabled.

A secondary, independent defect in the same path (would still bite even if the above were fixed):
`SubprocessManager.__init__` defaults `system_site_packages=True`, and its `_host_env.pth` workaround
filters `sys.path` for the literal substring `'site-packages'` — Kaggle/Debian install to
**`dist-packages`**, so that workaround silently exposes nothing, and every venv was created without
pip (`WARNING: ensurepip unavailable ... task package installation may be skipped`, 8/8 sandboxes).

**Conclusion:** Q5 requires the Docker sandbox (`docker/Dockerfile.sandbox`, `python:3.13-slim`) with
`wheels/` mounted at `/wheels`. Kaggle notebooks cannot run Docker, so **Q5 moves off Kaggle to local
Docker** (verified available: Docker 29.1.3, Linux containers). Kaggle stays the host for anything
needing the L4x4 GPUs.

### Confirmed good from v5 (reusable)

- Install: 32/41 wheels on py3.13; the 9 skipped are all vLLM/serving-only (`apache_tvm_ffi`, `cbor2`,
  `ijson`, `msgspec`, `nvidia_cudnn_frontend`, `outlines_core`, `pybase64`, `setproctitle`, `xgrammar`).
- Versions: swegemma 0.2.11, adk-submission 0.2.13, adk-eval-core 0.1.0, google-adk 1.36.1,
  vllm 0.19.1, litellm 1.85.7.
- Task set: 129 tasks — fastapi 67, rich 48, requests 13, httpx 1. [V]
- Competition data sizes: snapshots **21.5 GB** (129 x ~167 MB), embeddings 468 MB, graphs 422 MB,
  wheels 28 MB, tasks.jsonl 2 MB. Full local mirror is ~22 GB; per-task download is the sane route.
- Sample submission ships **two** adapters, `main_lora` and `tool_lora` (relevant to Q4).
- `GoldEvaluator` override contract verified: `_run_agent_sandbox` -> `tuple[str, str|None, SessionTrace]`
  (`swegemma/evaluate.py:194`); gold patch comes from the task after `_hydrate_task_from_secret`.
- API names verified against the wheelhouse, replacing community-mirror guesses:
  `adk_submission.discover_declared_models(dir) -> set[str]` (`discovery.py:659`);
  `swegemma.models.load_tasks`; `google.adk.apps._configs.EventsCompactionConfig`;
  `google.adk.agents.context_cache_config.ContextCacheConfig`. One of five such names was fiction —
  treat every unverified starter-notebook symbol as suspect.
- A missing snapshot returns `resolved=False, test_exit_code=-1, error='Snapshot file not found'`,
  which is indistinguishable from a broken task at a glance. `status` is now recorded per row so
  SUCCESS/ERROR/TIMEOUT can never be misread as a test failure.

### 1f. EXP-000 resolved: the gold control works, and Q5's blocker was the wheel pool — 2026-10-14

**Result: 8/8 local snapshots sound (`resolved=True`, `exit=0`). Zero task defects found so far.**
Every failure in §1e was environmental. Validity confirmed by a negative control: handing back an
**empty** patch instead of the reference patch flips the same tasks to `0/3`, `exit=1` (real test
failures, not collection errors), so grading discriminates and a gold pass is meaningful.

| run | patch | wheel pool | result |
|---|---|---|---|
| §1e Kaggle subprocess | gold | public 124 | 0/8 — deps never installed (sandbox returns early) |
| docker, raw pool | gold | public + 2 | 0/8 — starlette 1.6.0 / missing test deps |
| docker, curated | gold | curated 144 | **8/8 sound** |
| docker, curated | **empty** | curated 144 | 0/3 — negative control, as required |

#### Root cause: the harness installs the highest version of every wheel, ignoring the repo's pins

This took four wrong turns to find, so the call chain is worth recording:

1. `setup_container_wheels` **never populates `/wheels`** in Docker mode — it returns early when the
   manager exposes `extract_archive_to_container` (`container_setup.py:407`), to avoid a 1.7 GB tar
   copy per task.
2. Instead `install_test_dependencies` → `_ensure_container_site_packages` (`:318`) streams
   *unpacked* wheels straight into `/usr/local/lib/python3.13/site-packages`, choosing them via
   `_inspect_wheels_dir` → `_deduplicate_wheels`: *"Selects the highest version wheel per normalized
   distribution name."*
3. The container runs with `network_mode='none'` (`sandbox/docker.py:86`), so nothing can be fetched
   or corrected afterwards.
4. `sandbox/setup.py` would discard constraints regardless: `clean_requirement_line` does
   `re.split(r"[=<>!~]", line)[0]`, and its dep install skips anything absent from the pool silently
   (`if norm in available`). With `--fast-path` (the default, `install_test_dependencies(fast_path=True)`)
   it installs nothing at all and only writes `.pth` files — it presumes a **prebaked** image
   (`is_prebaked_env` → `SWE_PREBAKED`).

So the test environment is exactly *"the highest version of every wheel in `wheels_dir`"*, assembled
with no resolution. The public pool ships **57 starlette versions up to 1.6.0**, so a fastapi tree
pinned `starlette<0.49` receives 1.6.0 and every router construction dies with
`TypeError: Router.__init__() got an unexpected keyword argument 'on_startup'`. It also over-installs
**pytest 9.1.1** where tasks pin `<9.0.0`, plus `sqlmodel` and `typer`.

**Dead ends to not revisit:** `Evaluator._install_test_dependencies` (`evaluate.py:188`) and
`container_setup.setup_container_workspace` (`:941`) are both **never called** — overriding them
intercepts nothing. The live binding is `swegemma.harness.verification.install_test_dependencies`
(`verification.py:410`). An in-container `pip install` cannot work either: the container is offline
and `/wheels` is empty.

#### Fix: curate the pool per task (`tools/curate_wheels.py`)

Since selection is "highest wins", the pool is the only lever that reaches the env. Per task we parse
every constraint the repo declares (`pyproject` dependencies + optional-dependencies +
`dependency-groups`, and `requirements*.txt`, intersecting specifiers per distribution) and link only
the highest version each pin actually allows. It only ever *removes* candidates, so it cannot
construct an environment the organizers' pool could not. Docs requirement files are excluded
(`requirements-docs*`, `-translations`, `-github-actions`): the harness globs them indiscriminately,
but they pull a huge irrelevant tree whose pins fight the test deps.

Typical narrowing: `starlette 1.6.0 -> 0.50.0`, `pytest 9.1.1 -> 8.3.4`, `sqlmodel 0.0.39 -> 0.0.25`,
`dirty_equals 0.11 -> 0.9.0`, `typer 0.26.7 -> 0.21.1`.

#### The public wheel pool is incomplete

~37 declared deps per fastapi task are absent from the public 124-wheel set, and absences fail
**silently**. Test-relevant ones had to be fetched from PyPI into `data/local/wheels_extra/`
(now 144 merged): `python-multipart` (caused all three remaining `exit=2`:
`RuntimeError: Form data requires "python-multipart"`), `inline-snapshot`, `dirty-equals==0.9.0`,
`typing_inspection`, `email-validator`, `pyyaml`, `orjson`, `ujson`, `uvicorn`, `PyJWT==2.9.0`,
`passlib`, `pwdlib`, `python-slugify`, `annotated-doc`, `pydantic-extra-types`, `pydantic-settings`,
`flask`, `coverage`, `asttokens`, `executing`. Compiled wheels **must** be fetched with
`--platform manylinux2014_x86_64`; the default on this host silently yields `win_amd64` wheels that
the Linux sandbox ignores.

This implies official grading does **not** use the public pool alone — consistent with the private
`secret/` bundle (`_get_secret_bundle_data` → `secret/solution.parquet`, `secret/sandbox/snapshots`).
Our curated pool is therefore a *reconstruction*, so "sound" here means "sound in a correctly-pinned
environment" — the right notion for cohort selection, and it cannot be stated as identical to the
organizers' env.

#### Strategic find, unrelated to Q5

`container_setup.disable_test_runners_in_sandbox` (`:968`) **masks pytest in the agent container**
and "suppresses unconstrained test discovery", explicitly to stop agents running the suite; the
evaluation container keeps it ("Container B (evaluation) does not run this"). `unittest` and
`unittest.mock` are deliberately preserved. **Our agent cannot verify its patch with pytest** —
this invalidates any prompt plan that assumes a run-the-tests loop and feeds directly into Q8/Q10/Q11.

#### Reproduce

```bash
docker run --rm -v //var/run/docker.sock:/var/run/docker.sock \
  -v "$(pwd -W)/data/local:/data:ro" -v "$(pwd -W)/tools:/work/tools:ro" \
  -v "$(pwd -W)/runs:/work/runs" gemma4-orchestrator:latest \
  python /work/tools/gold_control.py --tasks /data/tasks.jsonl --snapshots /data/snapshots \
  --wheels /data/wheels_merged --out /work/runs/EXP-000-curated --curate-wheels
```
Add `--negative-control` to re-check that grading still fails an empty patch.

**Q5 status: method proven, 8/8 of the available sample sound.** Remaining: the other 121 snapshots
(~20 GB) to classify the full 129-task set.

### 1g. EXP-000 across four repos: five classes of unresolvable task, and how grading actually selects tests — 2026-10-14

§1f proved the method on fastapi alone. Extending it to `rich`, `requests` and `httpx` (28 snapshots,
two sweeps) turned up five *separate* reasons a task can be unresolvable, only two of which are wheel
problems. Conflating them is how an earlier pass concluded "107/129" and another "119/129": they are
counting different things.

It also turned up the single most consequential fact about grading, which is not about wheels at all
and is restated in §1h because it constrains the agent prompt, not just the cohorts.

#### The result

| task | status | class | mechanism |
|---|---|---|---|
| 8 x `fastapi_*` | sound [V] | — | pass once the pool honours the pins (§1f) |
| `httpx_3672` | sound [V] | — | needed `click==8.2.1`, and `httpx` itself excluded from the pool |
| `rich_4077` | sound [V] | — | |
| 5 x `requests_*` (7427, 7315, 7309, 7205, 6644) | sound [V] | — | test_patch touches `test_utils.py` / `test_adapters.py`, which contain no `httpbin` tests |
| `rich_4070` | sound **only with a narrowed pool** [V] | B | pool ships pygments 2.20.0 *and* 2.21.0; highest-wins picks 2.21.0, whose monokai lexer colours `iter` as a plain name, so every `test_syntax` snapshot assertion diffs. Passes with 2.20.0. |
| `requests_6644` | sound **only after the ABI fix** [V] | E | pool's winning `charset_normalizer` was a **cp312** wheel on a cp313 sandbox (below) |
| 8 x `requests_*` (7505, 7502, 7433, 7328, 6757, 6629, 6589, 6592) | UNRESOLVABLE [V] | D | test_patch touches `tests/test_requests.py`, where 135+ tests request the `httpbin` fixture; `pytest-httpbin` cannot be supplied (below) |
| `rich_3472` | UNRESOLVABLE [V] | C | `test_attrs_broken_310` expects `"'Foo' object has no attribute 'bar'"`; CPython 3.13 emits the qualname `'tests.test_pretty.test_attrs_broken_310.<locals>.Foo'`. (Also needed `attrs`, absent from the public pool — class B on top.) |
| `rich_3486` | UNRESOLVABLE [V] | A | test_patch adds a `skipif minor >= 11` / `skipif minor < 11` pair; one is always skipped, and a skipped *required* node fails the task. |

**Of the 28 snapshots measured, 16 are sound given a correct environment and 10 are not** (`rich_4070`
counts as sound only with the pygments override). `requests` is **5/13 sound, not 0/13** — see the
correction below.

#### The mechanism that explains most of it: pytest is pointed at FILES, never at nodes

`verification.py:619-646`:

```python
pytest_targets = [p for p in target_test_files
                  if Path(p).name != 'conftest.py' and p.endswith('.py')] or target_test_files
pytest_cmd = (f'cd /workspace && PYTHONSAFEPATH=1 PYTHONNOUSERSITE=1 python3 -s -m pytest '
              f'{test_files_str} --junitxml={junit_xml_path} -p no:anyio -o timeout=0 '
              '-o python_classes="Test* *Test" -q')
...
resolved = test_res.exit_code == 0
```

`target_test_files` is `extract_test_files_from_patch(task.test_patch)` — the files the test_patch
touches. Three consequences, all verified:

1. A task is graded on **every test in those files**, not only the tests it adds.
2. The gate is the **exit code of the whole invocation**. One error or failure anywhere in a touched
   file fails the task, even if every required node passed. (The JUnit check at `:266-341` runs only
   *after* `exit_code == 0`, so it can only ever narrow the pass set further.)
3. Therefore "is this task resolvable" is a property of the *files*, not of the task's own tests.

This is also a constraint on us, not just on task triage — see §1h.

#### Class D, corrected twice: `pytest-httpbin` poisons whole files

`container_setup.py:156-165` refuses to inject a fixed set of names when it unpacks the pool into
site-packages:

```python
skip_base_pkgs = {'pytest','pytest_timeout','pytest_asyncio','pytest_httpbin','pytest_xdist',
                  'pluggy','pip','setuptools','wheel'}
...
if pkg_norm in skip_base_pkgs:
    continue
```

The assumption is that the image already has them. It does not: `data/raw/docker/Dockerfile.sandbox`
installs only `pytest pytest-timeout==2.1.0 typer pdm-backend setuptools wheel poetry-core hatchling
flit-core editables`. So `pytest-httpbin`, `pytest-asyncio` and `pytest-xdist` are in **neither** the
image nor (verified) the public wheel pool, and adding them to a pool cannot work — the loop skips
them by name. `requests/tests/conftest.py:25` wraps the plugin's fixture:

```python
@pytest.fixture
def httpbin(httpbin):          # the inner name is the plugin's fixture
```

With no plugin, that resolves to itself: `E recursive dependency involving fixture 'httpbin'
detected`, at *setup*, for every test that requests it.

**Two wrong versions of this claim were published here before the right one, both corrected by
measurement rather than by argument:**

| screen | predicted doomed | measured | why it was wrong |
|---|---|---|---|
| repo *declares* `pytest-httpbin` | all 13 `requests_*` | 8 | the whole repo declares it; most individual tests never ask for it |
| an *added* test requests the fixture | 6 | 8 | pytest runs whole files, so tests the task never mentions still error |
| **any test in a touched file requests it** | **8** | **8** | matches, with no false positives |

The third screen separates the 13 exactly, and the split is clean with no exceptions:

| touched file | `httpbin` tests in it | tasks | outcome |
|---|---|---|---|
| `tests/test_requests.py` | 135–142 | 8 | all fail |
| `tests/test_utils.py`, `tests/test_adapters.py` | 0 | 5 | all pass |

`requests_6629` is the clearest demonstration: none of the tests *it* adds touch `httpbin`, and it
still dies with 185 setup errors because its test_patch happens to touch `test_requests.py`.

Two caveats, both unresolved: the organizers' private `secret/` bundle may carry these wheels, and
grading may use `Dockerfile.public` (identical plus `COPY wheels/ /wheels/`) or an image prebaked via
`SWE_PREBAKED`. Either would change the verdict. What is certain is that **the public path as shipped
cannot pass those 8 tasks**, so they must be excluded from our own cohorts regardless.

#### Class E — the pool's own ABI trap, and the harness has no tag check

Four `requests` tasks failed with `exit=4` and a `ModuleNotFoundError` for a package that was sitting
in the pool:

```
tests/conftest.py:12: in <module>
    from requests.compat import urljoin
src/requests/compat.py:13: in <module>
    import charset_normalizer as chardet
E   ModuleNotFoundError: No module named 'charset_normalizer'
```

`deduplication._deduplicate_wheels` "selects the highest version wheel per normalized distribution
name" and performs **no platform or ABI check at all**. The public pool ships cp312 *and* cp313 builds
of the same packages, and for two of them the **cp312 build carries the higher version**:

| package | cp313 build | cp312 build | highest-wins picks | importable on py3.13? |
|---|---|---|---|---|
| `charset_normalizer` | 3.4.9 | **3.5.1** | 3.5.1 (cp312) | **no** |
| `sqlalchemy` | 2.0.51 | **2.0.52** | 2.0.52 (cp312) | **no** |
| `markupsafe` | 3.0.3 | 3.0.3 | tie — filename order | coin flip |
| `pydantic_core` | 2.46.4 | 2.46.4 | tie — filename order | coin flip |

Unpacked into the 3.13 sandbox the cp312 extension module simply is not importable, and the failure
surfaces far from its cause. Fixed by `wheel_is_importable()` in `tools/curate_wheels.py`, applied
*before* version order: candidates are restricted to `py3-none-any`, `cp313`, and `cpXY-abi3` with
XY <= 313, on `any`/`manylinux*`/`linux_x86_64`, and a name is only filtered when a compatible build
survives (otherwise a version problem would become a missing module). Over the 144-wheel pool it
filters exactly those four names and nothing else, and the two ties become deterministic.

That converted `requests_6644` from `exit=4` to sound. It did **not** rescue 6629/6589/6592 — the ABI
fix let collection proceed far enough to reveal that they were class D underneath. Both bugs were
present at once, which is why the first `requests` sweep showed two different exit codes.

#### A side effect worth noting: pins on `skip_base_pkgs` names are inert

Because the skip happens before injection, narrowing `pytest` in the pool does nothing — every task
runs under the image's **pytest 9.1.1** no matter what it declares. `tools/curate_wheels.py` still
reports e.g. `pytest: 9.1.1 -> 7.4.4`; that line is cosmetic and must not be read as the version in
use. The same applies to `setuptools` and `wheel`.

#### Classes A and D are statically screenable — `tools/screen_tasks.py`

`tasks.jsonl` ships no `FAIL_TO_PASS`/`PASS_TO_PASS`, so `verification.py:303-305` falls back to
*every test the test_patch adds*, and `:328-340` fails the task if any of them is skipped:

```python
if not has_pass or has_non_pass:
    return False, f'Required test node did not pass: {req}'
```

A test_patch that adds a mutually exclusive `skipif` pair therefore guarantees failure. Class A needs
neither a container nor a snapshot; class D needs the snapshot, to read the *other* tests in a touched
file.

```
screened 129 tasks  |  clean 119  |  DOOMED 9  |  SUSPECT 1
missing-plugin screen applied to 28/129 (needs a local snapshot)
```

The nine are the eight class-D `requests` tasks and `rich_3486`, which matches every measurement
taken. `rich_3468` is flagged SUSPECT: a platform-gated `skipif` the screen cannot decide.

The screen cannot see class B, C or E. B and C need execution; E is a property of the pool rather than
of the task, and is now fixed at the source in curation instead of being screened for.

#### Classes B and C cannot be screened, and C cannot be fixed

Class B (wrong version chosen from an ambiguous pool) and class C (test expectations that encode
CPython's own behaviour) only surface by running. C is terminal: `rich_3472` asserts on an
`AttributeError` message that changed in CPython, and no patch an agent writes can alter the
test_patch's expected string. B is a pool question and so in principle fixable, but note that it
requires choosing a *lower* allowed version than the pins permit — `pygments ^2.13.0` admits both
2.20.0 and 2.21.0, and only the older one reproduces the snapshot. Pins alone are not enough; the
correct version is only discoverable empirically.

#### Fixes made while diagnosing

- `wheel_is_importable()` in `tools/curate_wheels.py` — ABI/platform filter applied before version
  order, with an `abi_filtered` list in the curation report (class E above).
- `curate(..., extra_pool=)` — the supplemental dir is now a real wheel *source*, not just a set of
  names to gate on. Previously a wheel dropped there was invisible unless also copied into the main
  pool, and the report showed the package as neither kept nor dropped while the task failed with a
  missing module. That cost a cycle on `rich_3472`'s `attrs`.
- `attrs==21.4.0` added to the supplements: declared by rich in the *legacy*
  `[tool.poetry.dev-dependencies]` table, absent from the public pool.
- Both `head` and `tail` of the test output are now logged. The tail alone was useless for `requests`,
  where 197 identical `ERROR` summary lines pushed the one informative traceback out of the window.
- `tools/screen_tasks.py` class-D screen rewritten to file granularity (table above).

#### A process note

Two of the five classes were first published here with the wrong scope, and both were caught by
running the measurement rather than by rereading the argument. The class-D claim in particular was
stated as "13 tasks, 10% of the benchmark, lost" when the true figure is 8. Static screens derived
from harness source are worth building — the class-A screen independently found `rich_3486` before
its run finished — but a screen is a hypothesis until a sweep agrees with it, and the published
number should be the measured one.

#### Reproduce

```bash
# static screen (class A needs nothing; class D needs snapshots)
python tools/screen_tasks.py data/local/tasks.jsonl --snapshots data/local/snapshots \
  --json-out runs/screen/screen.json

# a gold-control sweep (omit --task-ids for all 129)
docker run --rm -v //var/run/docker.sock:/var/run/docker.sock \
  -v "$(pwd -W)/data/local:/data:ro" -v "$(pwd -W)/tools:/work/tools:ro" \
  -v "$(pwd -W)/runs:/work/runs" -e PYTHONIOENCODING=utf-8 gemma4-orchestrator:latest \
  python /work/tools/gold_control.py --tasks /data/tasks.jsonl --snapshots /data/snapshots \
  --wheels /data/wheels_merged --supplemental-wheels /data/wheels_extra \
  --out /work/runs/EXP-000-all --curate-wheels

# rich_4070 additionally needs the empirical pygments pin
#   ... --task-ids rich_4070 --pin pygments==2.20.0
```

**Q5 status: ANSWERED. Full 129-task sweep complete (2026-10-14, `runs/EXP-000-all/gold_control.jsonl`,
`gold_failures.txt`): 108/129 sound (83.7%), 21/129 unresolvable even with the gold patch.**

By repo: `requests` 5/13 sound (38%), `rich` 39/48 sound (81%), `fastapi` 63/67 sound (94%), `httpx` 1/1.
The 5 classified mechanisms from the 28-snapshot sample (classes A-E above) account for 11 of the 21
failures (`rich_3486`=A, `rich_4070`=B, `rich_3472`=C, the 8 `requests_*`=D; class E was already fixed
at curation time and no longer appears). The other 10 failures were not visible in the earlier
partial sample and were root-caused individually on 2026-10-14 (below): 3 more turn out fixable the
same way as `rich_4070`, 2 are a new harness-level class (F), and 5 are a new terminal pool-exhaustion
class (C'/G). Cohort construction should exclude the terminal ones from scored cohorts; the fixable
ones are now handled automatically by `tools/curate_wheels.py`'s `DEFAULT_OVERRIDES`.

#### The 10 newly-surfaced failures, individually root-caused — 2026-10-14

Each was tested empirically; "looks like class B" was not assumed to transfer (`fastapi_14186` below
is the proof it doesn't always).

1. **`rich_4079`, `rich_3782` — class B, confirmed fixable.** Same pygments ANSI-truecolor mechanism
   as `rich_4070`. `--pin pygments==2.20.0` makes both pass. **Now the default**: added
   `DEFAULT_OVERRIDES = {"pygments": "==2.20.0"}` to `tools/curate_wheels.py`, merged under any
   caller-supplied `--pin` (so an explicit pin still wins), so every future sweep gets this without
   remembering the flag. This raises the sound rate without needing cohort exclusion for these two.
   Caveat while testing: the bare `--pin` reproduce command in §1f's recipe (no
   `--supplemental-wheels`) made all six look broken with an unrelated `INTERNALERROR` from the
   ungated `inline_snapshot` plugin crashing on rich's own `examples/attrs.py` — a reminder that the
   supplemental-gating step is not optional, it is part of what makes this pool curation correct.

2. **`rich_3296`, `rich_3469`, `rich_3130`, `rich_3064` — new class G, terminal, pool-exhaustion.**
   Same family (pygments ANSI-truecolor / markdown inline-code rendering), but `pygments==2.20.0`
   does not fix them, and the wheel pool contains only two pygments builds total (2.20.0, 2.21.0) —
   there is no third version left to try. Confirmed terminal because the lever (pool version choice)
   is provably exhausted, not because we stopped looking.

3. **`fastapi_14186` — new sub-case of class C, terminal, NOT a pin fix.** Looks like class B on the
   surface: the pool ships `pydantic-1.10.15` and `pydantic-2.13.4`, and `tests/utils.py` has
   `needs_pydanticv1 = pytest.mark.skipif(PYDANTIC_V2, reason=...)` on one required test, which
   highest-wins (2.13.4) skips. Pinning `pydantic==1.10.15` to un-skip it was tried and made things
   *worse*: pydantic v1 (EOL'd before Python 3.13 existed) is incompatible with 3.13's
   `typing.ForwardRef`, so pytest *collection itself* fails with
   `TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'`
   across 3 test files. The lesson generalizes: a pool version-ambiguity that *looks* like class B
   needs its own empirical pin test — "pin the lower version" is not a universal fix, and here the
   newer default is the only version actually compatible with the fixed Python 3.13 sandbox.

4. **`fastapi_15785`, `fastapi_15763`, `fastapi_15745` — new class F, terminal, harness-level, not a
   curation problem at all.** All three fail identically: tests marked `@pytest.mark.anyio` in
   `tests/test_router_include_context.py` die with "async def functions are not natively supported...
   You need to install a suitable plugin." `anyio` is declared by the task, kept by curation, and
   present as a wheel — this is not a dropped/undeclared/ABI problem. Root cause, confirmed by reading
   `data/src/swegemma/swegemma/harness/verification.py:628-633`: the harness's own grading pytest
   command hardcodes `-p no:anyio` unconditionally, for every task, with no conditional logic around
   it — it explicitly disables anyio's pytest plugin regardless of what a task declares. Any task
   whose official tests depend on `@pytest.mark.anyio` async tests is therefore structurally
   unwinnable, by a flag baked into the official harness itself. This is outside our wheel pool, our
   curation, and our submission entirely — nothing on the submission side can turn this on.

**Updated full-sweep tally after the default pygments pin**: 111/129 sound (86.0%), 18/129 terminal
(13.9%). By repo: `requests` 5/13 (class D, 8), `rich` 42/48 (class A ×1, class C ×1, class G ×4),
`fastapi` 63/67 (class C' ×1, class F ×3), `httpx` 1/1. See `runs/EXP-000-final/gold_control.jsonl` for
the rerun that confirms this with the new default baked into `tools/curate_wheels.py` (no manual
`--pin` needed).

### 1h. Grading runs whole test FILES — this changes the agent prompt, not just the cohorts — 2026-10-14

Found while diagnosing class D (§1g), but it is a scoring rule rather than a wheel problem, so it
belongs on its own. `verification.py:619-646`:

```python
pytest_targets = [p for p in target_test_files
                  if Path(p).name != 'conftest.py' and p.endswith('.py')] or target_test_files
pytest_cmd = f'... python3 -s -m pytest {test_files_str} --junitxml=... -q'
...
resolved = test_res.exit_code == 0
```

`target_test_files` comes from `extract_test_files_from_patch(task.test_patch)`. There is no `::node`
selection anywhere, and no `-k`. So:

> **A task is scored on every test in every file its test_patch touches, and the gate is the exit
> code of the whole pytest invocation.**

`requests/tests/test_requests.py` is ~600 tests. A patch that makes the one target test pass but
breaks any other test in that file scores exactly the same as an empty patch.

#### What this implies for the prompt (plan §4.2)

The current prompt tells the model to make the failing test pass. That is necessary but not
sufficient, and three specific behaviours become actively dangerous:

1. **Editing a test file to make it agree with the implementation.** Already partly guarded:
   `verification.py:437` passes `extra_protected_paths=target_test_files` and `:540-548` hard-resets
   those paths from `HEAD` before grading, so edits there are reverted. But a model that spends its
   budget there produces an effectively empty patch.
2. **Local assertions tightened "while I'm here".** Any collateral change to shared helpers,
   fixtures or module-level state in the touched file's blast radius is scored.
3. **Verifying with a narrowed command.** `pytest path::test_name` passing says very little; the
   grader runs `pytest path`. The prompt should ask for the *file* to be run, which is also the
   cheapest faithful reproduction of grading.

#### Status

Prompt revision **applied** this session: `submission/prompts/swe_coder.md` now tells the model to
verify at file granularity ("name the file, not a single node id") in both the hard-rules block and
the VERIFY phase, matching how grading actually runs pytest. `plan.md` §4.2/§4.3/§4.4 corrected to
match (version numbers, Python 3.12 orchestrator vs 3.13 sandbox, temperature/max_output_tokens
commentary, the mis-transcribed sample eval_config numbers, E4/E11 premises).

Correction to an earlier draft of this section: pytest is **not** masked in the agent container for
our submission. `disable_test_runners_in_sandbox` only runs when `enable_sandbox_testing` is
explicitly `False`; it defaults to `True` in `swegemma/config.py` and neither `agent.yaml` nor
`eval_config.yaml` overrides it. So the model can and does run real pytest during VERIFY — the fix
needed was only that it must run the whole file, not a node id.

Note the asymmetry this creates: a repo whose tests are split into small files (fastapi: 63/67 sound,
94%, per the full sweep in §1g) is far more tractable than one with a single large suite file
(requests: 5/13 sound, 38%; the 8 tasks touching `test_requests.py` all fail). Cohort construction
should not treat the 129 tasks as exchangeable. (This note originally cited "fastapi: 8/8 sound" from
an 8-task partial sample; the full 67-task fastapi sweep still supports the same direction of the
claim but at 94%, not 100% — see §1g for the 4 fastapi failures not yet root-caused.)

---

## 1i. Pause/resume log, and the full sweep's completion — 2026-10-14

Session was paused mid-sweep ("cancel everything ... lets pause") at 22/129 graded, 111/129 snapshots,
with both Docker containers stopped cleanly. On resume, the snapshot downloader finished (129/129),
and the gold-control sweep was restarted twice more:

1. First resume ran 74/129 → was killed by the harness's own background-shell memory-pressure reaper
   (not a bug in the sweep itself; both orphaned containers were then stopped manually to free memory).
2. Second resume ran 74→108/129, then crashed on a **corrupted snapshot** (`rich_3535.tgz`, truncated
   mid-gzip — `EOFError: Compressed file ended before the end-of-stream marker was reached`). Deleted
   and re-downloaded it (89.9 MB, 584 tar members, verified readable), then resumed again.
3. Third resume ran the final 21 tasks to completion.

**Full sweep complete: 129/129 graded, 108 sound / 21 unresolvable.** Results folded into the Q5 row
and §1g above; raw tally in `runs/EXP-000-all/gold_control.jsonl` and `runs/EXP-000-all/gold_failures.txt`.

Still open from plan §3.4: Q6 partially answered via `kaggle competitions list -s
gemma-4-developer-agent` — confirmed main-track final deadline **2026-12-02 23:59** and paper-track
deadline **2026-11-12 23:59:08**; the CLI's own competition listing does not expose a separate
entry/merger date, so the Nov 2 vs Nov 25 question is still unresolved (needs the Timeline page, which
needs a logged-in browser — Claude-in-Chrome was not connected this session). Q4, Q7, Q8, Q10, Q11
still open.

Remaining work: root-cause the 10 newly surfaced failures (6 `rich`, 4 `fastapi`) listed in
`gold_failures.txt`; apply the pending `tools/validate_submission.py` cap-assertion change; enter the
paper track (user's call).
