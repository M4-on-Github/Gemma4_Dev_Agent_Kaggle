# Execution plan — Kaggle "Google – The Gemma 4 Developer Agent"

Main code track + Paper track. Plan date: **2026-10-13**. Source of truth for facts: `research_report.md`
(scratchpad). Confidence tags are carried over: **[V]** verified (official snippet / 3+ mirrors),
**[M]** community mirror(s) only, **[I]** inference. Anything tagged [M]/[I] that affects a decision is
listed in §3.4 as a checklist item to resolve against `HARNESS_README.md`, `sample_submission/`, or the
Kaggle competition pages once we have access (kaggle.com was unreachable from the research sandbox).

---

## 1. Goal, success metrics, dates, constraints

### 1.1 Goals
| Track | Goal | Stretch |
|---|---|---|
| Main (code) | Reliable prompt-only agent in the **0.12–0.15** public-LB band (top is ~0.15–0.18 as of early Oct [M]) with **zero** budget-overrun / crash submissions | ≥ 0.18 (top-3 band) via LoRA/RFT if the adapter path is unblocked |
| Paper | Submit a Writeup ≤ 3,000 words by **Nov 12** that scores ≥ 4/5 on Verifiability and Clarity, built entirely on experiments we run anyway | Best New Resource ($10k) via a released eval/trace toolkit + per-task CSVs |

Public LB resolution: 1 task ≈ 0.017 [V]. So a 0.12 → 0.15 move is ~2 tasks on the public half; see §5.6 on noise.

**Status note, 2026-10-17 (plan originally targeted first submission today)**: we have not yet made any
scored submission. This is a deliberate hold, not neglect: every agent-performance number collected so far
(exp002–008) is from a small cohort hand-picked for a specific infra bug (the shim-deletion fix), not a
representative sample, and that cohort's own result (exp005: 1/20 resolved, 18/20 never finishing
LOCATE/REPRODUCE/EDIT) is not something we're willing to calibrate a first LB attempt against. §6.0/§6.1 adds
**E0**, a dev-48 representative baseline, as the immediate next step before the first submission — see there
for why. We still intend to use the Oct 17 slot once E0 lands (same day if it lands early, next day
otherwise); the Oct 25 LoRA gate is unaffected by this slip since its prerequisites (canary, prompt-only
stability) don't depend on E0's number, only on the decision of *whether prompt-only is worth stabilizing
further or whether E-STOP-class fixes are needed first* (§6.0).

### 1.2 Key dates (UTC) and countdown from Oct 13
| Date | Event | Days left | Confidence |
|---|---|---|---|
| Oct 17 | Our first scored submission (v1 baseline) | 4 | internal |
| Oct 25 | LoRA go/no-go gate | 12 | internal |
| **Nov 2** | Possible entry/merger deadline per one X post | 20 | **[M] — verify on Kaggle before Oct 20; treat Nov 2 as binding until disproven** |
| **Nov 12 23:59** | Paper track deadline | 30 | [V] |
| Nov 25 | Main-track entry + team merger deadline | 43 | [V] (but see Nov 2 row) |
| Nov 30 | Internal freeze; last "risky" submission | 48 | internal |
| **Dec 1 23:59** | Last submission we allow ourselves (≥ 24 h margin) | 49 | internal |
| **Dec 2 23:59** | Final submission deadline | 50 | [V] |

### 1.3 Constraints summary
- **One model for everyone**: `google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2` (INT4, ~17 GB) served by patched vLLM 0.19.1, TP=4 on 4× L4, `max_model_len=32768`, gpu_mem 0.90, `--tool-call-parser gemma4 --reasoning-parser gemma4 --enable-auto-tool-choice` [V].
- **32k context** hard wall: prompt + `max_tokens` > 32,768 → HTTP 400 → "Sandbox execution error" → empty patch, *discarding an earlier submit_patch* [M].
- **12 h global budget** for ~120 hidden tasks incl. sandbox setup; overrun fails the **whole** submission [V]. Avg ≤ 6.0 min/task all-in.
- **1 submission/day**, 2 finals, team ≤ 5 [V]. Scoring takes ~6–10 h [M] → effectively one LB signal per day.
- **Offline** sandbox: no network/pip/MCP/subprocess references in the zip [M]; 2 vCPU / 4 GiB per task, repo at `/workspace`, wheels at `/wheels`, no memory across tasks [M].
- **Declarative only**: ADK Agent Config (`agent.yaml`, prompts, sub-agents, skills, optional LoRA adapter, `eval_config.yaml`). No Python entry point, no custom tools [V]. Allowed extensions `.yaml .yml .md .txt .py .json .safetensors` (a `.sh` broke a submission) [M]; zip < 3 GiB [M].
- **Fixed tool set** [V]: `run_command, read_file, edit_file, write_file, get_status (free), submit_patch (free), get_code_neighbors, search_similar_code, get_code_subgraph, agent_tool`. `run_skill_script` / `load_skill_resource` documented but one team hit `ToolNotFoundError` [M].
- **Grading**: patch applied at `base_commit`, hidden `test_patch` run with pytest; `tests/`, `conftest.py`, `pytest.ini`, `setup.cfg`, `pyproject.toml` reset before grading [M] → editing tests is useless, editing config is useless.
- **Data redistribution**: competition data (tasks.jsonl, repos, graphs, wheelhouse) must not be redistributed → never in the public GitHub repo. Our traces contain repo snippets → also kept out of git (release only aggregated CSVs / sanitized excerpts in the paper).
- **Winner deliverables**: Apache-2.0 license, training + inference code [V]. External data allowed if public & free [V].

---

## 2. Repository layout (public repo: `M4-on-Github/Gemma4_Dev_Agent_Kaggle`)

```
.
├── LICENSE                         # Apache-2.0 (required for winners; set from day 1)
├── README.md                       # how to build/validate/pack/eval; links to paper
├── plan.md                         # this file
├── pyproject.toml                  # uv-managed; python>=3.11 (match harness wheels; verify)
├── .gitignore                      # see below
├── submission/                     # == contents of submission.zip (zip root = this dir)
│   ├── agent.yaml                  # root LlmAgent `swe_coder`
│   ├── eval_config.yaml            # per-task budgets
│   ├── prompts/
│   │   ├── swe_coder.md            # root system prompt (phased protocol)
│   │   └── analyzer.md             # optional sub-agent prompt (ablated)
│   ├── configs/
│   │   └── sampling.yaml           # !include'd generate_content_config
│   ├── sub_agents/
│   │   └── analyzer.yaml           # exposed via agent_tool (off by default)
│   ├── skills/
│   │   └── pytest-triage/SKILL.md  # SKILL.md-only skills (no scripts until run_skill_script verified)
│   └── adapters/                   # LoRA (only if canary passes); gitignored *.safetensors
├── tools/                          # our dev tooling (never shipped)
│   ├── validate_submission.py      # replicates validate_directory/compile_submission + our lint rules
│   ├── pack_submission.py          # deterministic zip, extension whitelist, hard-link-safe, size check
│   ├── budget_estimator.py         # projects 12 h total from per-task wall/tokens (port of g4kit-scorer-time idea)
│   ├── trace_analyzer.py           # per-run metrics: spin, malformed, overflow, phases, timing
│   ├── make_cohort.py              # stratified dev/held-out split of the 129 public tasks
│   └── gold_control.py             # applies gold patch + runs test_patch via harness to find broken tasks
├── notebooks/
│   ├── kaggle_eval_l4x4.ipynb      # truthful eval on competition-attached L4×4 notebook
│   ├── kaggle_gold_control.ipynb
│   └── kaggle_tpu_lora.ipynb       # TPU v5e-8 LoRA trainer (only if gate passes)
├── experiments/
│   ├── README.md                   # experiment log format + index table
│   ├── EXP-000-gold-control.md
│   └── EXP-001-baseline.md ...
├── data/                           # gitignored: tasks.jsonl, repos, graphs, wheelhouse, traces
├── runs/                           # gitignored: raw traces, per-task results, proxy logs
└── paper/
    ├── outline.md
    ├── writeup.md                  # ≤ 3,000 words, Kaggle Writeup format
    ├── figures/
    └── release/                    # aggregated per-task CSVs, seeds, configs for release
```

`.gitignore` must contain: `data/`, `runs/`, `*.safetensors`, `*.zip`, `*.jsonl` (except `experiments/**/summary.jsonl`
if sanitized), `.kaggle/`, `*.env`. Add a pre-commit hook (`tools/check_no_data.sh`-equivalent in Python) that fails
if any file under `data/` or a file > 5 MB is staged.

---

## 3. Phase 0 — Setup & verification (Oct 13 → Oct 15)

### 3.1 Accounts & access
- [ ] Every member: accept rules for **both** competitions (main + paper). Form the team on Kaggle before the earliest plausible merger deadline (Nov 2 [M] / Nov 25 [V]).
- [ ] Kaggle API token on each dev machine: `~/.kaggle/kaggle.json` (chmod 600); `uv tool install kaggle`.
- [ ] Verify L4×4 availability: competition-attached notebooks only, ~2× normal quota [M]. Record actual weekly GPU hours in `experiments/README.md`.

### 3.2 Downloads
```bash
kaggle competitions download -c gemma-4-developer-agent -p data/raw   # ~21 GB [V]
kaggle datasets download metric/gemma-4-developer-agent-wheelhouse -p data/wheelhouse  # ~827 MB [V]
```
Unzip into empty dirs; treat as untrusted. Then read **in this order**: `HARNESS_README.md`, `sample_submission/`
(every file), the starter notebook (`ryanholbrook/getting-started-gemma-4-developer-agent`), the wheelhouse
packages `swegemma 0.2.11`, `adk-submission 0.2.13`, `adk-eval-core 0.1.0`, `google-adk 1.36.1` (read
`validate_directory` / `compile_submission` source — this is the real schema).

### 3.3 Local environment
- `uv venv --python 3.11` (or whatever the wheelhouse targets — verify); `uv pip install --no-index --find-links data/wheelhouse ...`.
- No GPU locally. The orchestrator/agent-side process runs Python 3.12; the grading **sandbox** container is Python 3.13 — pin wheel curation to the sandbox's 3.13 (VERIFIED this phase: wheel ABI tags must match 3.13, not 3.12, or `_deduplicate_wheels` silently picks an unimportable cp312 build — see `experiments/README.md` §1g class E). Local work = validation, packing, trace analysis, fake-LLM smoke tests. Truthful evals happen on Kaggle L4×4 (§5).
- Optional: install `damsolanke/gemma4-swe-kit` (Apache-2.0) for `g4kit-fake-llm` + `g4kit-harness run` GPU-free smoke tests and `g4kit-scorer-time`.

### 3.4 Verification checklist (each item: owner, resolved-by date, answer recorded in `experiments/README.md`)
| # | Open question | How we resolve it | Default until resolved |
|---|---|---|---|
| Q1 | Exact compile-time **tool registry** (are `run_skill_script`/`load_skill_resource` real? graph tools present?) | grep `adk-submission` source; run fake-LLM smoke test with each tool name | Declare only the 10 tools listed in §1.3; no skill scripts |
| Q2 | `agent.yaml` / `sampling.yaml` / `eval_config.yaml` **schema** and field names (`max_time_minutes, max_tool_calls, max_turns, timeout_seconds` [M]) | `sample_submission/` + `validate_directory` source | Copy sample field names verbatim |
| Q3 | Does `thinking_budget` actually bind? (maps to vLLM `thinking_token_budget` [M]; compiler wants `include_thoughts: true` [M]) | Kaggle L4 run with budget 128 vs 1024 on 5 tasks; compare reasoning-token counts in traces | Assume it binds loosely; cap via `max_output_tokens` too |
| Q4 | **LoRA zeroing** in patched vLLM (host's sample with 2 adapters failed; discussions 743508/743213) | Logprob canary: adapter trained to flip one token on a fixed prompt; compare base vs adapter logprobs on the scorer stack in a Kaggle notebook | Ship **no** adapter |
| Q5 | **Gold-patch control**: which of the 129 public tasks fail even with the gold patch? | `tools/gold_control.py` on Kaggle (EXP-000) | Exclude failures from cohort; count them |
| Q6 | Deadline: Nov 2 vs Nov 25 for entry/merger | Read competition "Timeline" page | Treat Nov 2 as binding |
| Q7 | Compaction interval (5 per HARNESS_README vs 15 per hosts' notebook [M]) and threshold 14,336 tokens | HARNESS_README + observe in traces | Design prompts to survive compaction (§4.2) |
| Q8 | Sandbox setup time per task (counts toward 12 h) | Measure in Kaggle harness run; log `setup_seconds` | Assume 45–60 s [I] |
| Q9 | Allowed extension list / size limit | `validate_directory` source | Whitelist in §1.3 |
| Q10 | Decode speed and prefix caching on scorer (25.5 tok/s + 0.6 s/call [M]) | Measure from L4 traces | Use 25 tok/s in estimator |

Phase 0 exit gate: Q1, Q2, Q5, Q9 answered; EXP-000 gold control done; `tools/validate_submission.py` passes on `sample_submission/`.

---

## 4. Phase 1 — Baseline agent (Oct 14 → Oct 17, first submission Oct 17)

### 4.1 Architecture
Single root `LlmAgent` **`swe_coder`**. No sub-agents in v1 (same-model delegation hurt: 12/18 → 6/18 [M]; sub-agent
sessions never compact [M]). Graph tools **declared but demoted** in v1 prompt ("use only if grep fails"); v2 ablates
on/off (AST omits `async def`; zip hard-links can yield 0-byte graph files [M]).

**Finding (2026-10-17, `data/raw/HARNESS_README.md` §3.4 "Multi-LoRA Serving")**: the single-declared-model rule
(`validate_single_declared_model` / `discover_declared_models`, §4.5) only constrains the shared **base** checkpoint —
every `LlmAgent` in the hierarchy (root or any `sub_agents`/`agent_tool` entry) may additionally set its own
`adapter: <name>`, and the harness auto-discovers and serves all of them via vLLM's multi-LoRA support
(`--lora-modules`, dynamic `max_loras`/`max_lora_rank`). This means our 12/18→6/18 same-model-delegation regression
does not rule out a sub-agent architecture outright — it only rules out a sub-agent running the *same* weights as the
root. A sub-agent with its own adapter (e.g. a `tool_lora`-tuned read-only analyzer feeding a `main_lora`-tuned coder)
is architecturally supported and untested; see §6.2 for why it's still gated behind G-LoRA rather than
promoted into the v1/E9 backlog now.

```yaml
# submission/agent.yaml (shape to be matched against sample_submission — Q2)
name: swe_coder
model: google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2   # or whatever sample uses
instruction: !include prompts/swe_coder.md
generate_content_config: !include configs/sampling.yaml
tools: [run_command, read_file, edit_file, write_file, get_status, submit_patch]   # + graph tools when ablating
```

### 4.2 Prompt protocol (`prompts/swe_coder.md`)
Phased, with an explicit budget ledger the model repeats every turn (`[phase=EDIT calls=17/45 edits=1]`):

1. **LOCATE** (≤ 10 calls): `run_command` with `grep -rn`/`ls`; `read_file` on ≤ 3 files, ranges only. Never read whole large files (cap by line range to protect the 32k window).
2. **REPRODUCE** (≤ 6 calls): write `/tmp/repro.py` (never inside `tests/` — tests are reset [M]); run it; if the bug cannot be reproduced in 6 calls, proceed to EDIT anyway.
3. **EDIT** (≤ 12 calls): minimal change, `edit_file` anchored on **short distinct strings** [M]; after each edit, `read_file` the modified range once.
4. **VERIFY** (≤ 10 calls): rerun repro; run **targeted** `pytest -x -q <path>::<test>` (≤ 60 s via `timeout`). Never edit tests/config. If still failing after 2 fix cycles → go to SUBMIT with best effort.
5. **SUBMIT**: `get_status` then `submit_patch` **immediately** after the last verified edit (overflow later discards it [M]). Always submit something non-empty before 80% of the call budget.

Hard rules baked into the prompt (each from a measured failure mode):
- **Tool-arg format**: one JSON object per call; positional/kwarg-style (`f{k="v"}`) parses to `{}` [M]. No tool names other than the declared list (undeclared → ADK raises → task lost [M]). **No shell-command examples written as if they were tools** in the prompt (they get emitted as tool names, ~31% malformed in a replay [M]) — all examples are shown inside a single `run_command` JSON.
- **Anti-spin**: never issue a call identical to any of the last 3; if a command fails twice, change approach; identical-call cost up to 35% of calls in the community [M].
- **Overflow guards**: `run_command` outputs piped through `| head -c 4000` (or `| tail -n 60` for pytest); `read_file` always with line ranges; compaction (≈14,336 tokens, text-only, drops tool results [M]) → every ~5 turns the model writes a 3-line **state note** in plain text (files touched, hypothesis, next step) so it survives compaction.
- **Nudges**: three consecutive "token limit" nudges end the session [M] → `max_output_tokens` sized so a normal turn never truncates.

### 4.3 Sampling starting values (`configs/sampling.yaml`)
```yaml
temperature: 0.2          # matches the official scorer default 0.2 (corrected from an earlier [M] claim of 1.0); we A/B 0.1–0.3 vs 0.2
top_p: 0.95
top_k: 64
max_output_tokens: 4096   # official default is 16384 WITH thinking enabled (thinking tokens share this budget,
                          # so a small cap truncates thinking first, not output) [VERIFIED]; see E11 below—this
                          # is a deliberate A/B point, not yet the recommended value
thinking_config:
  include_thoughts: true  # compiler requires per [M]
  thinking_budget: 256    # see budget math; A/B 0/128/512/1024
```

### 4.4 Budget math → `eval_config.yaml`
- 12 h / 120 tasks = **6.0 min/task all-in**. Subtract setup (Q8, assume 1.0 min) → **5.0 min agent wall max average**. Add 15% safety → target **average ≤ 4.3 min**, hard cap 4.5 min.
- Decode 25.5 tok/s [M] → 4.5 min ≈ 270 s ≈ **6,900 output tokens per task total**, minus ~0.6 s × 45 calls ≈ 27 s overhead → ~6,200 tokens. With 45 calls that is **~140 output tokens per call including thinking**. Consequence: `thinking_budget` ≥ 512 at every step is unaffordable (45 × 512 = 23k tokens ≈ 15 min). Either thinking small (128–256) or thinking only on a few turns. This is Experiment E2's core question.
- Prefill is not free: a 14k-token prompt every call for 45 calls = 630k prefill tokens; prefix caching should make this cheap but must be measured (Q10).

```yaml
# submission/eval_config.yaml — field names per sample (Q2) [M]
max_time_minutes: 4.5
max_tool_calls: 45
max_turns: 70
timeout_seconds: 150      # per run_command
```
Sanity: 120 × 4.5 min = 9.0 h worst case for agent time + 2.0 h setup = 11.0 h < 12 h. The reported sample config values were mis-transcribed earlier; the actual sample is
(1 min / 10 calls / 60 s / 50 turns [VERIFIED against `sample_submission/eval_config.yaml`]), which is *tighter*
than ours, not looser — our 4.5 min/45 calls/70 turns/150 s budget is intentionally larger than the sample and
still fits the 12 h cap per the sanity check below; it would not "blow the cap". `tools/budget_estimator.py` must print the
projected total (p50 and worst-case) from a cohort run before every submission; **block packing if worst case > 11.0 h**.

**Caveat added 2026-10-17**: this math assumes calls and time are roughly interchangeable constraints (45
calls *or* 4.5 min, whichever binds first, each sized off the same decode-speed estimate). exp005's real-agent
data complicates that: of the 20 tasks run, several that never finished hit the 274s wall-clock cap, not the
45-call cap — i.e. **time, not call count, was the binding constraint** for at least some fraction of tasks,
which the 140-tokens/call budget math in the paragraph above doesn't obviously predict (it would predict
calls running out first, if every call used close to its 140-token allowance). Two explanations are both
plausible and not yet distinguished: (a) per-call latency is higher than the 25.5 tok/s + 0.6s overhead
estimate under real thinking-token usage, so the time cap binds before 45 calls are used — in which case E3
(thinking-off/strict-rules, promoted in §6.1) directly addresses it; or (b) the 45/4.5min pairing itself is
miscalibrated for the actual call volume real tasks need before a hypothesis is reachable, independent of
thinking cost. **Do not re-derive this budget math further until E0 (§6.1) reports the actual
`time_cap_hit` vs `calls_cap_hit` split on a representative sample** — tuning either number without that
split risks fixing the wrong constraint. E6 (budget tuning) is promoted in §6.1 partly for this reason.

### 4.5 Tooling to build in Phase 1
- `tools/validate_submission.py`: calls the wheelhouse `validate_directory`/`compile_submission` if importable, plus our checks: extension whitelist, no `network|pip|http|mcp|subprocess` strings, declared tools ⊆ registry, `!include` targets exist, eval_config worst case ≤ 11.0 h, no sub-agent referencing an undeclared tool.
- `tools/pack_submission.py`: `zip -X -r` with `agent.yaml` at root, **copies not hard-links** (0-byte graph-file bug [M]), prints SHA256 + size; refuses if validator fails.
- `tools/trace_analyzer.py` (first version): per task → resolved, wall s, calls, malformed calls (content-embedded), identical-call count, HTTP 400 / overflow, submit_patch present, phase reached.
- Fake-LLM smoke test (`g4kit-fake-llm` or own stub) so the zip is exercised end-to-end without GPU.

### 4.6 First submission (v1, target Oct 17)
Precondition: EXP-000 gold control + EXP-001 baseline on the dev cohort on Kaggle L4×4, projected worst-case ≤ 11 h.
Submit v1 even if dev resolve rate is low — the LB run tells us (a) the budget holds, (b) the public↔local gap
(one paper saw 34.5% local vs 6.9% hidden [M]).

---

## 5. Phase 2 — Evaluation infrastructure (Oct 15 → Oct 22, then continuous)

### 5.1 Where evals run
| Tier | What | Cost | Use |
|---|---|---|---|
| T0 local, no GPU | validator, packer, fake-LLM smoke, trace analysis, replay of logged decision points | free | every change |
| T1 Kaggle L4×4 notebook (competition-attached) | official harness + vLLM 0.19.1 on the exact model; 10–60 tasks | ~1 GPU-h per 10 tasks [I] (4.5 min/task + model load ~10 min) | every experiment |
| T2 Kaggle LB | hidden ~120 tasks | 1/day | confirm transfer, not for exploration |

Notebook `kaggle_eval_l4x4.ipynb`: load model once; loop over task ids from a cohort file; dump per-task JSON (result, wall, tokens, trace path) to `/kaggle/working/runs/<exp-id>/`; download and feed `trace_analyzer.py`. Save as a notebook *version* per experiment so results are reproducible. Keep sessions under the notebook time limit (verify: 9 h/12 h) — chunk cohorts into ≤ 30 tasks per session.

### 5.2 Cohorts (from 129 public tasks: fastapi 67, rich 48, requests 13, httpx 1 [V])
`tools/make_cohort.py --seed 20261013` after removing gold-control failures:
- **dev-48**: stratified by repo ≈ fastapi 22 / rich 16 / requests 9 / httpx 1 — oversample requests/httpx relative to prevalence so we don't tune to fastapi/rich idioms (hidden set is private repos [V]).
- **held-out-24**: same stratification, never looked at while iterating; run only at decision gates (G2, G4, freeze).
- **smoke-8**: 2 per repo, for quick checks of a prompt change (~40 min GPU).
Cohort ids committed to `experiments/cohorts/*.txt` (task ids only — not data).

### 5.3 Metrics logged per run (`runs/<exp>/summary.json`, one row per task)
`task_id, repo, resolved, patch_empty, submit_patch_called, wall_s, setup_s, n_calls, n_turns, n_malformed, n_identical_repeats, n_undeclared_tool, overflow_400, nudges, compactions, phase_reached, output_tokens, thinking_tokens, timeout_hit, calls_cap_hit, time_cap_hit`

Aggregates: resolve rate (± Wilson 95% CI), empty-patch rate, timeout rate, overflow rate, malformed rate, spin rate, median/p90 wall, **projected 12 h total** = Σ(wall+setup)·(120/N) scaled, worst case = 120 × (cap + setup).

### 5.4 Gold control (EXP-000, first L4 run)
Apply each task's gold patch + run test_patch through the harness. Tasks that fail are removed from cohorts and counted (public sandbox fails some gold patches [M]). Rerun gold control whenever the harness/wheelhouse version changes.

### 5.5 Noise handling
- With N=48 and p≈0.25, the 95% CI is roughly ±12 pts; a single-run difference of < 3 tasks on dev-48 is **not** evidence. Decision rule: adopt a change only if (a) dev-48 Δ ≥ +3 tasks **and** process metrics (malformed, spin, overflow, wall) do not regress, or (b) the change is a pure robustness fix with neutral resolve rate.
- Run the baseline config twice (two seeds / two sessions) early to measure run-to-run variance; record it in `experiments/README.md` and use it as the minimum detectable effect.
- Public LB: ±1 task = ±0.017; do not react to single-day LB moves < 0.035.

### 5.6 Experiment log format (`experiments/EXP-NNN-<slug>.md`)
```
id, date, owner, hypothesis, single variable changed (diff link), cohort, seed, GPU-h used,
results table (resolve %, empty %, overflow %, malformed %, spin %, median wall, projected 12h),
decision (adopt / reject / rerun), follow-ups
```
Index table in `experiments/README.md`; the current best config is tagged in git (`v1`, `v2`, …) and its zip SHA256 recorded next to each LB submission.

### 5.7 GPU quota budgeting
Unknown exact quota (Q — record it). Planning assumption: ~30 L4×4 hours/week [I]. Allocation: 60% experiments (≈ 5 dev-48 runs), 20% held-out/gates, 20% LoRA canary/training-side checks. If quota is tighter, shrink to smoke-8 for screening and dev-48 only for finalists.

### 5.8 Using the 1 submission/day LB slot
- Submit **every day** something useful: a candidate config or a calibration probe (e.g., same config twice to measure LB noise once).
- Never submit a config that has not run on dev-48 with projected worst case ≤ 11 h.
- Keep a `submissions.md` log: date, git tag, zip SHA256, dev-48 score, LB score, scoring wall time (from the kawchar85 tracker's observed time), notes.

---

## 6. Phase 3 — Research & iteration (Oct 18 → Nov 20)

### 6.0 Backlog reordering, 2026-10-17 — why E0/E-STOP jump the queue

Context forcing this reorder (full detail in `experiments/README.md` §1n and the exp006–008 commit): every
real-agent number we have so far (exp002/003/004/005, and now exp006–008) comes from a **biased cohort**
(2–25 tasks hand-picked because they hit the `inline_snapshot`/`dirty_equals` shim bug), not from dev-48. On
that cohort, exp005 (20 tasks) found only 2/20 ever reached the shim error at all — the other 18/20 spent
their entire budget on LOCATE/REPRODUCE/EDIT for the task's real bug and never finished. exp006–008 then
spent three further rounds trying to fix this by making the model self-report its remaining tool-call budget
more faithfully (`get_status` cadence: vague → fixed checkpoints → mandatory alternation). All three failed
to achieve compliance, and — the more important result — **in none of the three did the agent call
`edit_file` even once** on either of the 2 test tasks. That means ledger-accuracy was never the thing standing
between the agent and a submitted patch: a perfectly-accurate self-tracking agent that still never edits
scores the same zero as an inaccurate one. We were optimizing a proxy metric (self-report compliance) that
doesn't correlate with the outcome that scores points (reaching `edit_file` with budget left over to verify
and submit). This duplicates, almost exactly, the conclusion exp005 already reached on a larger sample one
day earlier — the two findings weren't connected until this reorder.

Two consequences for ordering:

1. **We have no resolved-rate number on a random/representative sample of the 129 tasks at all.** Every number
   in this plan and in `experiments/README.md` so far is either a gold-control sanity check (measures infra,
   not agent behavior) or a run on the shim-biased cohort (measures a rare failure mode, not typical
   performance). Before spending the Oct 17 LB slot, before deciding the E1–E11 order below still makes sense,
   and before the Oct 25 LoRA gate, we need **E0** — the dev-48 baseline the plan always intended EXP-001 to
   be, but which has not actually been run yet (`experiments/README.md` §3's EXP-001 row is still empty).
2. **Stop iterating on ledger/self-report wording.** Any further self-tracking-accuracy experiment is
   deprioritized indefinitely (not deleted — if E0/E-STOP below show the bottleneck genuinely is "the model
   doesn't know when to stop looking," a get_status-based fix is still on the table, just not as the next
   thing to try). The next lever to pull is a **structural, non-arithmetic forced transition** — see E-STOP.

### 6.1 Experiment backlog (one variable at a time; priority order; cost in dev-48 runs ≈ 3–4 GPU-h each)
| ID | Variable | Hypothesis | Measure | Cost |
|---|---|---|---|---|
| **E0** | **Representative baseline**: current prompt (post shim-fix, pre-ledger-experiments — i.e. roll back the exp006–008 ledger-wording churn, keep the exp001–005 shim fix) on **dev-48** (stratified, unbiased), not the shim cohort | Establishes the real resolve-rate baseline and, critically, the `phase_reached` / `time_cap_hit` vs `calls_cap_hit` distribution across a representative sample — tells us whether exp005's "18/20 never finish LOCATE/REPRODUCE/EDIT" generalizes or was partly an artifact of the shim cohort being unusually hard | resolve % (± Wilson CI), empty %, phase_reached histogram, time_cap_hit % vs calls_cap_hit % | 1 run, highest priority — blocks the Oct 17 LB slot decision and informs whether E-STOP is even needed |
| **E-STOP** | Structural forced phase transition that does **not** depend on the model doing arithmetic or complying with self-report instructions: (a) cheapest version — shrink the LOCATE+REPRODUCE guide-cap from 16 to ~8–10 calls and add 1–2 worked-example transcripts in the prompt showing a transition to `edit_file` by call ~8–10, no ledger-wording changes; (b) if (a) doesn't move `phase_reached`, escalate to an architectural split: a LOCATE-only sub-agent (via `agent_tool`) that is declaratively given *only* `read_file`/`run_command`/graph tools and a short budget, hands a terse hypothesis back to the root `swe_coder`, which only then gets `edit_file`/`write_file`/`submit_patch` — making "stop exploring" a tool-availability fact, not a request the model has to honor | (a) is cheap and should be tried first; (b) revisits the E9 same-model-delegation regression (12/18→6/18) but changes *why* it might work this time — tool-scoping forces the transition structurally, where the E9 regression was attributed to context/continuity loss across a redundant re-reasoning hop, not to tool availability | phase_reached ≥ EDIT %, resolve, wall; compare against E0 baseline | (a) 1 run; (b) only if (a) fails, 1–2 runs |
| E1 | Prompt protocol: phased + ledger vs. flat sample prompt | Phased protocol cuts empty-patch and spin rates by > 50% without hurting resolves | empty %, spin %, resolve | 2 runs |
| E3 | Thinking-off + strict tool-arg rules | **Promoted ahead of E2/E4**: exp005's two time-cap-hit examples (`fastapi_14360` at 274s against a 270s/4.5min cap) suggest wall-clock, not call count, is the binding constraint for a meaningful share of tasks — if so, cutting per-call latency (less thinking) buys more usable calls within the same wall-clock budget more directly than any LOCATE-cap mechanism. Strict rules alone get malformed ≈ 1.4% [M], freeing time for more calls | malformed %, wall, time_cap_hit %, resolve | 1 run |
| E2 | Thinking: off / budget 128 / 256 / 1024 (`thinking_budget` binding per Q3) | Thinking-on reduces malformed (24→2%) and repeats (50→9%) [M] but costs 65–71% of time [M]; a small budget keeps most of the benefit — read jointly with E3 and E0's time_cap_hit rate, not in isolation | malformed %, wall, resolve | 4 runs |
| E6 | Budget tuning: calls 35/45/60, time 4/4.5/5 min, timeout 120/150/180 | **Also promoted**: E0 should report whether failing tasks are overwhelmingly hitting the *time* cap or the *calls* cap (both are logged by `tools/analyze_traces.py`, no new tooling needed) — if time-cap-bound, the 45-call/4.5-min pairing in §4.4 may itself be miscalibrated (see §4.4 note) and is worth revisiting before further prompt tuning, not after | resolve vs wall curve, time_cap_hit % vs calls_cap_hit % | 3 runs (can reuse traces by truncation analysis first) |
| E5 | Graph tools on vs off (prompt-demoted vs declared-and-encouraged vs undeclared) | grep-based localization matches graph tools and avoids 0-byte/async gaps [M]; also a direct lever on LOCATE call cost if E0 shows LOCATE is where budget is lost | LOCATE calls, resolve | 2 runs |
| E4 | Temperature 0.2 (scorer default, matches ours) vs 1.0 | Our default already matches the scorer; this now tests whether *raising* T buys exploration diversity at the cost of more spin/malformed | spin %, resolve | 1–2 runs |
| E10 | Submit policy: always submit at 80% budget vs only after VERIFY | Early forced submission raises resolve via partial fixes, kills empty patches | empty %, resolve | 1 run |
| E7 | Compaction behavior: state-note cadence 0 / 3 / 5 turns; `read_file` range caps | State notes recover post-compaction context; fewer repeated reads | compactions, repeats after compaction, resolve | 2 runs |
| E11 | `max_output_tokens` 2048 / 4096 / 6144 / 16384 (official default) | **Premise corrected**: thinking tokens are drawn from this same budget, so a *small* cap is what starves thinking and triggers overflow/nudge chains, not what avoids them — original hypothesis had this backwards. Expect overflow %% to fall, not rise, as the cap grows toward the 16384 default | overflow %, nudges | 1 run |
| E8 | Skills: `pytest-triage/SKILL.md` and `edit-anchoring/SKILL.md` on vs off | Skills reduce failed edit_file calls | failed edit %, resolve | 1 run (if skills load without `run_skill_script`) |
| E9 | Sub-agent `analyzer` (localization only, via agent_tool) on vs off, **same model** | Expected negative or neutral [M] on its own terms (redundant re-reasoning hop, context/continuity loss); superseded in intent by E-STOP(b), which tests a *tool-scoped* sub-agent rather than a same-capability one — run E9 only if E-STOP(b) is inconclusive and a cheap negative-control data point is still wanted | resolve, wall | 1 run |

**Revised order: E0 → E-STOP(a) → E3 → E6 → E1 → E2 → E5 → E4 → E10 → E7 → E11 → E8 → [E-STOP(b) / E9]**.
"Done" criteria to move past each of the first three (the ones that matter for the Oct 25 gate):
- **E0 done** when we have a resolve-rate point estimate + Wilson CI on dev-48 and a `phase_reached` /
  time-cap-vs-calls-cap breakdown. This number is what tells us whether to spend the Oct 17 LB slot now or
  wait one more day for E-STOP(a)'s result — **send back to drawing board** only if the harness itself looks
  broken (e.g. near-zero empty-patch-free resolves even on tasks that clearly reach VERIFY), not if resolve
  rate is merely low (low-but-nonzero is expected and is a reason to keep iterating, not a reason to stop).
- **E-STOP(a) done** when ≥ 80% of dev-48 tasks reach `phase_reached ∈ {EDIT, VERIFY, SUBMIT}` (vs whatever
  E0 measures as the baseline) without a net resolve-rate regression — **adopt** at that bar; **escalate to
  E-STOP(b)** if phase_reached barely moves (e.g. < 10pp improvement), since that would mean the problem isn't
  "LOCATE budget is 2 calls too generous," it's that the model doesn't stop regardless of the cap's size.
- **E3 done** when wall-clock time_cap_hit rate drops materially (e.g. ≥ 30% relative) at no malformed-rate
  cost — **adopt**; if time_cap_hit doesn't move, that's evidence time-cap hits are driven by call volume
  (slow convergence to a hypothesis) rather than per-call latency, which redirects weight back toward E-STOP
  and E6 over E2.

After each adopted change, re-run the budget estimator. Every ~5 experiments, run held-out-24 to check we are
not overfitting dev-48.

Cheap pre-screen without GPU: replay logged decision points under the changed prompt (g4kit-replay idea) and count malformed/spin deltas before spending a dev-48 run.

### 6.2 LoRA / RFT track (gated)
**Multi-LoRA-per-sub-agent is available** (§4.1 finding, 2026-10-17): the harness serves a distinct adapter per
`LlmAgent`/`agent_tool` as long as every agent shares the same base model (`validate_single_declared_model` only
checks the base, not adapters). Sizing fits the 3 GiB submission cap comfortably: rank-16 ≈110–220MB/adapter (8 fit),
rank-32 ≈220–450MB (6–8 fit), rank-64 ≈450–900MB (3–6 fit), rank-128 max ≈0.9–1.8GB (1–3 fit). The harness's own
documented example is close to our E9 sub-agent idea: `adapter: main_lora` on the root coder, `adapter: tool_lora` on
a read-only analyzer `AgentTool`. This is a **backlog idea gated behind G-LoRA below**, not a v1/E9 change — E9's
same-model delegation test is still the cheap thing to run first (§6.1), and a two-adapter architecture only makes
sense once a single adapter has cleared the canary (step 1 below) and shown it moves behavior at all.

**Gate G-LoRA (Oct 25)** — go only if **all** hold:
1. Canary passes (Q4): adapter trained to shift logprobs on a fixed prompt shows the shift on the scorer stack (patched vLLM, L4 notebook). If deltas are ~0 → adapters are zeroed → **no-go**, redirect effort to prompts + paper.
2. KV-cache check: with the adapter loaded, the harness runs 8 tasks without hangs (LoRA shrinks KV to ~7.6k tokens in some reports [M]); rank ≤ 32, exactly 1 adapter [M].
3. Prompt-only baseline is stable (two consecutive LB submissions without budget/crash failures).

If go:
- **Data**: rejection sampling on dev-48 + public SWE-style trajectories converted to harness tool format (public & free only). Keep only trajectories that resolved **and** had 0 malformed / 0 identical calls; ~200–500 trajectories target. Optionally RFT-style: multiple rollouts per task at T=1.0, keep successes.
- **Training**: TRL/PEFT or Unsloth QLoRA on the bf16 31B; rank 16, alpha 32, target attention+MLP projections, 1–2 epochs, LR 1e-4; compute: Kaggle TPU v5e-8 (~20 h/week) via `notebooks/kaggle_tpu_lora.ipynb`, or a rented 1× 80 GB GPU (Unsloth ~22 GB) — decide by cost at gate time.
- **Adapter verification**: `adapters/<name>/{adapter_config.json, adapter_model.safetensors}`, key names match vLLM expectations (g4kit-check-peft idea), logprob canary again with the real adapter, dev-48 run, size well under 3 GiB.
- Ship only if dev-48 Δ ≥ +4 tasks and held-out-24 does not regress.

**Note added 2026-10-17 — a candidate training target, not a gate change**: the gate criteria above (canary,
KV-cache, prompt-only stability) are unchanged. But exp006–008 (see §6.0) showed that three rounds of
prompt-only attempts to get the model to reliably self-track budget and transition out of LOCATE/REPRODUCE
all failed, and failed in the same way (never reaching `edit_file` at all). If E-STOP(a)'s cheap prompt-side
fix (§6.1) also fails to move `phase_reached`, "transition to EDIT by call N reliably" becomes a concrete,
well-specified **procedural/behavioral** training target for a LoRA — teaching a compliance habit rather than
new task capability, which is a narrower and plausibly easier data/training problem than general SWE
capability (candidate data: trajectories truncated/relabeled at the point a human would have switched to
editing, rather than full successful trajectories only). This is **not** a reason to move the Oct 25 gate or
its pass/fail criteria; it is only a note for what to train on *if* the gate passes and *if* E-STOP(a) alone
doesn't already fix the problem for free.

---

## 7. Phase 4 — Paper track (Oct 20 → Nov 12)

### 7.1 Study choice (tied to experiments we run anyway)
**Primary: "Thinking budget × tool-argument discipline under a hard 32k/12 h regime"** — a 2×k ablation
(E2 + E3 + E4) on dev-48/held-out-24 reporting resolve rate, malformed-call rate, spin rate, wall time and
projected scorer time, with a cost-aware recommendation (tokens per resolved task). Novelty: the budget-constrained
trade-off, not just "thinking helps".

**Backup: "A taxonomy of agent failure modes (spin, malformed calls, overflow, compaction loss) and mitigations"**
from the same traces (E1, E7, E10, E11) — lower novelty, high relevance and verifiability.

**Best New Resource angle**: release `tools/trace_analyzer.py` + `budget_estimator.py` + per-task CSVs
(aggregates and metrics only, no competition data) as an Apache-2.0 toolkit.

### 7.1b Backlog — speculative paper-track ideas (not committed; standalone harness, not `submission/`)
Both items below are blocked from the live competition submission by infra, not by choice (the Kaggle harness
loads exactly one vLLM checkpoint per episode; `discover_declared_models()` enforces this — 2026-10-17 finding),
so either would need its own small multi-model harness outside `submission/`, run only if primary-study time
(§7.3) allows:
- **Small-model-as-searcher ablation**: a cheap/fast model (e.g. an `e2b`-class Gemma-4 variant, if available as
  a standalone served checkpoint outside the competition harness) does LOCATE/REPRODUCE search-and-report only
  (terse artifact: file/function/line/hypothesis), handing off to the 31B model for EDIT/VERIFY/SUBMIT. Question:
  does cost-adjusted resolve rate (tokens or GPU-seconds per resolved task) beat single-31B end-to-end? Ties into
  the single-agent-vs-multi-agent finding (§4.1: same-model delegation hurt 12/18→6/18) — here the hypothesis is
  that a *size-asymmetric* handoff (small model cheaply narrows the search space, big model does the precision
  work) could win where same-size delegation lost due to context/continuity loss, since the division of labor
  is more clearly asymmetric capability, not a redundant re-reasoning step.
- **COCONUT-style latent/continuous-reasoning note**: investigated 2026-10-17 and ruled out for the live
  submission — requires feeding the model's own hidden states back as input embeddings instead of discrete
  tokens, which needs control of the decode loop/serving code; our declarative-only submission (prompts/agent
  config/LoRA weight-delta only, vLLM token-in/token-out API, no `inputs_embeds` injection surface) cannot do
  this, and a LoRA alone can't replicate it since it doesn't change the harness's input/output interface. If
  revisited at all, it would only be as a from-scratch paper-track side experiment on a separately hosted model
  (not the competition's patched vLLM), explicitly scoped as "not reproducible within the submission format" —
  low priority given the primary study already has a clear novelty angle.

### 7.2 Rubric mapping (0–5 each)
| Criterion | How we score it |
|---|---|
| Novelty | Quantified budget/thinking trade-off and failure taxonomy specific to the Gemma 4 harness; no prior writeup we know measures tokens-per-resolve under the 12 h cap |
| Quality / generality | Per-repo breakdown (fastapi/rich/requests/httpx), held-out split, CIs, two seeds; discuss transfer to private repos via LB |
| Relevance | Directly about building the Gemma 4 developer agent; recommendations are config-level and reusable by any team |
| Verifiability | Release configs, cohort ids, seeds, per-task CSVs, analyzer code, exact zip SHA256s and LB scores |
| Clarity | ≤ 3,000 words, 4–6 figures, one summary table; written by humans from our own numbers ("LLM slop will not score well") |

### 7.3 Writing schedule
- Oct 20: `paper/outline.md` (questions, tables/figures list, which EXP ids feed each).
- Nov 1: all required experiments done (E1–E4, E6, E10 at minimum, each ≥ 1 dev-48 run; held-out-24 for the final config).
- Nov 5: first full draft + figures (`paper/figures/`), internal review against rubric.
- Nov 9: freeze numbers; release `paper/release/` CSVs; final edit.
- **Nov 11**: submit Writeup (24 h margin before Nov 12 23:59 UTC).

---

## 8. Phase 5 — Hardening & final submission (Nov 13 → Dec 1)

### 8.1 Robustness passes
- **Budget**: final config's dev-48 p90 wall and worst case re-projected; worst case must be ≤ 11.0 h; the harness overrun = zero score.
- **Overflow**: inject 3 adversarial tasks (huge files, noisy test output) in a smoke run; verify no HTTP 400.
- **Validator**: run against the final zip; confirm no `.sh`, no banned strings, `agent.yaml` at root, no hard-links, size.
- **Determinism check**: same zip run twice on smoke-8; differences only within noise.

### 8.2 Generalization to private repos
- Prompts must not mention fastapi/rich/requests/httpx idioms, file paths or test names. Grep the prompts for repo names before freeze.
- Prefer generic strategies (grep → read ranges → repro → targeted pytest). Favor configs whose held-out-24 and LB behavior agree, over configs that only win on dev-48.
- Watch requests/httpx subsets: small but closer to "unseen" behavior.

### 8.3 Freeze policy and finals
- **Nov 30**: freeze. No prompt changes after; only validator/packaging fixes.
- Choose **2 finals**: (1) the best-LB config with ≥ 2 clean LB runs; (2) the most robust config (lowest empty/overflow/timeout rates, lowest worst-case wall) if different; if the LoRA path shipped, it may be one of the two only with ≥ 2 clean LB runs.
- Last submission **Dec 1 ≤ 23:00 UTC** (≥ 24 h margin for 6–10 h scoring and a retry).

### 8.4 Winner-deliverable readiness (do during Phase 5, not after)
- Apache-2.0 LICENSE at repo root; `README.md` with reproduce steps for inference (pack + harness run) and training (if LoRA shipped); no competition data in repo; tag `final-1`, `final-2` with zip SHA256s.

---

## 9. Week-by-week timeline (owners are placeholders A/B/C)

| Week | Dates | Deliverables | Decision gate |
|---|---|---|---|
| W1 | Oct 13–19 | Join both tracks (all); Kaggle creds + downloads (A); read HARNESS_README/sample/validate source, fill Q1/Q2/Q9 (B); repo scaffold, LICENSE, .gitignore, validator+packer (C); EXP-000 gold control (A); EXP-001 baseline on dev-48 (A/B); **submit v1 Oct 17**; Q6 deadline check | **G1 (Oct 19)**: v1 scored without budget/crash failure; dev/LB gap recorded |
| W2 | Oct 20–26 | **E0 dev-48 baseline first (added 2026-10-17, see §6.0)**, then E-STOP(a); E3, E6 (A); E1, E2 (B) if E-STOP(a) doesn't already resolve the phase_reached problem; baseline variance (2 seeds); paper outline (B); LoRA canary (C); daily LB submissions once E0 lands | **G-LoRA (Oct 25)** go/no-go (unchanged criteria, see §6.2 note); **G2 (Oct 26)**: held-out-24 on current best |
| W3 | Oct 27–Nov 2 | E6, E5, E10 (A/B); if LoRA go: data generation via rejection sampling (C); confirm team formed before Nov 2 (if binding) | Nov 2 entry/merger (if [M] is true) |
| W4 | Nov 3–9 | E7, E11, E8 (A); held-out + LB confirm of final paper config; paper draft Nov 5 → figures, CSV release (B/C); LoRA training + adapter verification if go (C) | **G3 (Nov 9)**: paper numbers frozen |
| W5 | Nov 10–16 | **Paper submit Nov 11**; E9 and remaining ablations; LoRA dev-48 eval if trained | Paper in (Nov 12) |
| W6 | Nov 17–23 | Robustness passes (§8.1); generalization audit (§8.2); 2–3 candidate finals each with ≥ 2 LB runs | **G4 (Nov 23)**: candidate finals list |
| W7 | Nov 24–30 | Team merger deadline Nov 25 (V); README/reproduce docs; last variance submissions; **freeze Nov 30** | **G5 (Nov 30)**: finals chosen |
| W8 | Dec 1–2 | Final submission ≤ Dec 1 23:00 UTC; select 2 finals in Kaggle UI; tag repo | Dec 2 23:59 deadline |

---

## 10. Risks, open questions, references

### 10.1 Risks & mitigations
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| 12 h budget overrun → whole submission fails | Med | Critical | Estimator gate (worst case ≤ 11 h) before every pack; caps 4.5 min/45 calls; measure setup time (Q8) |
| Context overflow (HTTP 400) → empty patch, lost submit_patch | High | High | `max_output_tokens` 4096, output truncation in commands, line-range reads, submit immediately after edits, state notes |
| LoRA adapters silently zeroed / KV shrink hangs | High [M] | Med (wasted effort) | Canary gate Oct 25; no adapter by default; rank ≤ 32, 1 adapter |
| Public↔hidden gap (34.5% vs 6.9% in one report) | High | High | Held-out split, LB confirmation of every adopted change, repo-agnostic prompts, requests/httpx oversampling |
| LB noise misleads decisions | High | Med | 3-task rule on dev-48, ignore LB moves < 0.035, same-config repeat submission once |
| Undeclared tool / malformed calls crash tasks | Med | Med | Strict arg rules, declared-tool whitelist in validator, no shell-like tool examples |
| Graph files 0 bytes / async gaps | Med | Low | Graph tools demoted or off (E5) |
| L4×4 quota too small | Med | Med | smoke-8 screening, replay pre-screen, chunked sessions; record quota in W1 |
| Entry/merger deadline is Nov 2 not Nov 25 | Unknown [M] | Critical | Verify by Oct 20; form team early regardless |
| Harness/wheelhouse version changes mid-competition | Med | Med | Pin versions in notebook; rerun gold control + smoke-8 on each change |
| Subprocess sandbox (the only backend Kaggle supports — no Docker daemon, no Bubblewrap, no user namespaces, confirmed independently by discussion/749743) silently skips `install_editable_package`/`install_test_dependencies`, so per-task test deps (inline_snapshot, dirty_equals, pytest-httpbin, ...) may be missing in **both** our gold-control measurements and the real scorer | Med–High (unconfirmed) | High (undercounts true resolve rate; agent may lose points on tasks whose gold patch would pass if the dep were present) | Vendored-shim fix for inline_snapshot/dirty_equals now wired directly into `submission/prompts/swe_coder.md` (agent creates the shim itself, not just our measurement tooling); requests/httpx import-shadowing and rich/Pygments drift remain unfixed (too deep to shim safely). **Recheck discussion/749439 and /749743 periodically** — an organizer answer confirming/denying that scoring differs from the starter notebook changes how much weight to put on gold-control numbers |
| Kaggle's default notebook image has drifted past the wheelhouse's build target (cp312/torch 2.10) to cp313/torch 2.11 (discussion/749505); a fresh kernel created today would silently pin to the wrong image even with `docker_image_pinning_type: original`, since that only freezes whatever image exists *at first push* | **Confirmed (2026-10-16), fix confirmed (2026-10-16)** | Critical (notebook/submission fails to install at all, like discussion/749505) | **Reproduced on a brand-new kernel** (`rainm4/gemma4-exp001-shim-check`, first push): landed on Python 3.13 despite `docker_image_pinning_type: original`; 9/41 wheelhouse wheels (cp312-only: msgspec, outlines_core, xgrammar, pybase64, setproctitle, ...) failed to install, then the image's own `vllm==0.19.1` crashed on startup (`ImportError: vllm/_C.abi3.so: undefined symbol _ZN3c1013MessageLoggerC1EPKciib`, a torch/CUDA ABI mismatch) — confirms "original" pinning does nothing for a kernel with no prior push to pin to. **Fix verified**: forking the organizers' Getting Started kernel directly (`notebooks/exp002_fork_shim_check`, carries the real pinned `docker_image: gcr.io/kaggle-private-byod/python@sha256:37c64f7...` field from fork lineage, a stronger guarantee than `docker_image_pinning_type: original`) installed all 41/41 wheelhouse wheels cleanly and started the vLLM server with no ABI error. **Action before any real submission push: push from a fork of the Getting Started kernel, never a fresh kernel id.** |
| `total_cached_tokens: 0` in every step of all 3 exp002 traces | **Investigated (2026-10-16), likely a reporting gap, not a perf bug** | Low (demoted after per-step timing analysis) | Per-step `elapsed_s` deltas (not just token sums) were checked directly against each step's own `prompt_tokens` (5-15k per call, reset periodically by `EventsCompactionConfig(compaction_interval=15)`): no quadratic blowup pattern — step latency (2-28s) tracks how much new content that turn read/wrote, not cumulative context size. `google.adk.agents.context_cache_config.ContextCacheConfig` is a Vertex AI/Gemini **explicit-caching** feature (`cachedContents` API) per `adk.dev/context/caching` — it has no defined meaning against a local vLLM OpenAI-compatible endpoint, so `total_cached_tokens: 0` most likely just means ADK's cache-usage field isn't wired up for this backend, not that caching (vLLM's own automatic prefix caching, on by default in vLLM's V1 engine) is broken. Not worth further investigation unless a future run shows genuine quadratic slowdown |
| Real agent runs with `RUN_AGENT=True` (`exp002_fork_shim_check`, 3 known-affected tasks, 4.5 min/task budget) all hit the wall-clock cap in LOCATE/REPRODUCE before ever running pytest on the real test file — the vendored inline_snapshot/dirty_equals shim in `swe_coder.md` had still never been exercised against a real `ModuleNotFoundError` on Kaggle | **Shim exercised, found buggy, fixed and re-validated (2026-10-16)** | Closed (was High) | Followed up with `exp003_fork_shim_easy` (3 tasks picked by smallest reference-patch size as an easier-task proxy: `fastapi_14361`, `fastapi_14360`, `fastapi_14303`). Mixed result, not a clean win: `fastapi_14361` reached VERIFY cleanly inside budget (19 tool calls) — hit `ModuleNotFoundError: No module named 'inline_snapshot'`, vendored the shim exactly per `swe_coder.md`, reran both affected test files (10/10 and 37/37 passed), called `submit_patch` once correctly (1176 chars, 2 files) — **then ran `rm -rf inline_snapshot` and called `submit_patch` again (512 chars, 1 file), stripping the shim from its own final patch.** Its own step-25 reasoning (trace `results/traces/trace_fastapi_14361.json`) shows it explicitly weighing the Hard-rules scratch-file cleanup instruction against the Known-sandbox-gaps "this is not cheating" wording and resolving the ambiguity the wrong way — a real prompt-wording gap, not a one-off fluke. The other two tasks never reached a point where this could even fire: `fastapi_14303` spent its whole 45-call budget on a different, unrelated bug (multidict query-param handling in `fastapi/dependencies/utils.py`) and never ran the `dirty_equals`-importing test file before being force-submitted at the call cap; `fastapi_14360` (same code area) fully timed out (274s) still in LOCATE/REPRODUCE with patch_chars=0. So reference-patch length was a weak/partial proxy for reachability — 1 of 3 "easier" tasks actually completed a clean VERIFY cycle, the other 2 still didn't reach a test run at all. **Fix applied**: `submission/prompts/swe_coder.md` now has an explicit carve-out in the Hard-rules scratch-file line ("a vendored package from Known sandbox gaps below is not a scratch file... never delete it") and an explicit instruction at the end of the Known-sandbox-gaps paragraph to keep the vendored file in the final patch. **Re-validated (2026-10-16)**: re-ran `fastapi_14361` alone (`notebooks/exp004_shim_fix_check`, same kernel version 3) against the patched prompt — agent vendored the shim, verified tests, called `submit_patch` exactly once (1176 chars, 2 files), no deletion, explicitly reasoning "The files changed are `fastapi/_compat/v2.py` and `inline_snapshot/__init__.py`. This is correct." Kernel log: `resolved=True, exit_code=0, patch_chars=1175` — same task that failed grading under the unpatched prompt now passes. **Scaled check (2026-10-17, `exp005_shim_fix_batch20`)**: batched the remaining 20 of the 25 known-affected tasks in one kernel session (version 4). Only 1/20 resolved overall, but the real finding is reachability, not the shim: only 2 of 20 tasks ever hit the `inline_snapshot`/`dirty_equals` `ModuleNotFoundError` at all — the other 18 never got that far in LOCATE/REPRODUCE within the 4.5 min/45-call budget, the same constraint identified in exp002/exp003, now confirmed at 10x the sample size. Of the 2 that did reach it: `fastapi_14485` vendored both shims, verified via pytest, then got forced-submitted at the 45-call cap with the shim files still intact — `resolved=True`; `fastapi_14356` also vendored the shim correctly (never deleted) but failed on a genuinely incorrect real-code fix for an unrelated bug (`request_params_to_args` multidict handling) — unrelated to the shim mechanism. **Conclusion: the shim-deletion bug is fixed and 2-for-2 clean in this batch (no deletions, no regressions); it is just rarely the limiting factor — step-budget in LOCATE/REPRODUCE is the dominant open problem across the known-affected cohort.** |
| Data leakage into public repo | Low | High (rule breach) | .gitignore + pre-commit size/path check; release only aggregates |
| `.sh`/banned strings in zip → rejection | Low | Med | Validator whitelist; fake-LLM smoke before each submission |
| Paper reads as generated / unverifiable | Med | Med | Human-written, numbers from our CSVs, release code + seeds |
| **Step budget in LOCATE/REPRODUCE/EDIT, not shim bugs or ledger self-report, is the dominant open failure mode (exp005, confirmed by exp006–008's negative result)** | **High (now the #1 open risk, added 2026-10-17)** | Critical (caps resolve rate regardless of any other fix) | E0 representative baseline + E-STOP(a)/(b) structural forced-transition experiments (§6.0/§6.1), promoted ahead of thinking-budget and compaction tuning; LoRA noted as a fallback training target (§6.2) if prompt-only fixes fail |

### 10.2 Open questions (tracked in §3.4; summary)
LoRA zeroing status (Q4); compile-time tool registry and skill tooling (Q1); exact config schemas (Q2); `thinking_budget` enforcement (Q3); gold-patch failures (Q5); Nov 2 vs Nov 25 (Q6); compaction interval 5 vs 15 (Q7); sandbox setup time (Q8); extension/size limits (Q9); decode/prefill speed and prefix caching (Q10); actual L4×4 quota; public↔hidden gap magnitude for *our* configs; ~~whether the `swe_coder.md` scratch-file-vs-vendored-shim wording fix stops the agent from deleting its own vendored shim before `submit_patch`~~ — **answered (Q11, closed 2026-10-16): yes, re-validated on a real kernel run (`exp004_shim_fix_check`), `fastapi_14361` now resolves cleanly.**

### 10.3 References
- Competition: https://www.kaggle.com/competitions/gemma-4-developer-agent
- Paper track: https://www.kaggle.com/competitions/gemma-4-developer-agent-paper
- Starter notebook: https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent
- Wheelhouse dataset: `metric/gemma-4-developer-agent-wheelhouse`; model `google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2`
- LB tracker: https://github.com/kawchar85/gemma4-agent-leaderboard (live: gemma4agent.kawchar.online)
- Local eval/distill kit (Apache-2.0): https://github.com/damsolanke/gemma4-swe-kit (`g4kit-fake-llm`, `g4kit-harness`, `g4kit-scorer-time`, `g4kit-canary`, `g4kit-check-peft`)
- Community repos: Gosling-dude/gemma4-developer-agent, HindsightWise/gemma-4-developer-agent, usp787/Gemma4_paper_track, yosh95/g4-developer-agent-paper, ennydev-2026/gemma-4-developer-agent
- Kaggle discussions on LoRA zeroing: 743508, 743213
- Our repo: https://github.com/M4-on-Github/Gemma4_Dev_Agent_Kaggle

### 10.4 Forum follow-ups to recheck (not yet answered by organizers as of 2026-10-15)
| Thread | Question | Why it matters | Re-check for |
|---|---|---|---|
| discussion/749439 ("Reference patches failing in the starter notebook") | Does real scoring use the same subprocess-sandbox environment as the starter notebook? | If organizers confirm scoring differs (e.g. uses the private `ryanholbrook/gemma4swe-wheelhouses` dataset we got 403'd on), the dependency-install gap may not apply to real grading at all, and our vendored-shim prompt addition becomes purely defensive rather than point-recovering | Any organizer reply; any mention of `gemma4swe-wheelhouses` becoming public |
| discussion/749743 ("Supported isolation backend for Kaggle notebook development") | Is there an officially supported sandbox for dev/eval work on Kaggle besides raw subprocess? | Would let us measure gold-control fidelity without the install no-op, no shim-guessing needed | Any organizer reply |
| discussion/749505 ("Getting Started notebook fails: wheelhouse is cp312 but environment is Python 3.13") | Will the wheelhouse be rebuilt for the new default image, or does `docker_image_pinning_type: original` + forking the Getting Started kernel remain the correct workaround indefinitely? | Determines whether our kernel-metadata.json pin is a permanent fix or a stopgap that breaks on the next Kaggle image bump. **We independently reproduced the exact failure on 2026-10-16** on a fresh kernel (see §10.1) — `docker_image_pinning_type: original` alone did not help | Any organizer reply beyond "fork the Getting Started notebook"; also recheck whether `swegemma` has moved past 0.2.11 (was 0.2.10 as of 747519) |
| discussion/747519 ("Update on Kaggle Error Submissions & Queue Delays") | Ryan Holbrook already confirmed the wheelhouse is updated periodically (swegemma 0.2.7→0.2.10, adk_submission 0.2.12→0.2.13) for scoring-time fixes | Any further wheelhouse bump can change harness behavior underfoot; rerun gold control + smoke-8 whenever this happens (already tracked as a general risk above) | New version-bump announcements |
