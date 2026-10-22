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
| **Nov 12 23:59** | Paper track deadline | 30 | [V] |
| Nov 25 | Main-track entry + team merger deadline | 43 | **[V] confirmed 2026-10-17 directly from the live Kaggle rules page** — the Nov 2 rumor (one X post, [M]) is **disproven**: entry and team-merger deadlines are both Nov 25 |
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
(`--lora-modules`, dynamic `max_loras`/`max_lora_rank`). This means the 12/18→6/18 same-model-delegation
regression cited at line 152 (`[M]`, secondhand/community-reported — E9 itself was never run in this project,
see §6.0.3's 2026-10-18 citation correction) does not rule out a sub-agent architecture outright even if taken
at face value — it would only rule out a sub-agent running the *same* weights as the root. A sub-agent with its own adapter (e.g. a `tool_lora`-tuned read-only analyzer feeding a `main_lora`-tuned coder)
is architecturally supported and untested; see §6.2 for why it's still gated behind G-LoRA rather than
promoted into the v1/E9 backlog now.

**Note (2026-10-20):** by the same reading, "one `LlmAgent`, one LLM request in flight at a time" is our current
design choice, not a harness constraint — `SequentialAgent`/`ParallelAgent` roots compile through the real
`compile_submission()` path (exercised by EXP-007). Whether a parallel tree is worth adopting is an
evidence-gated question tracked in §6.3, not settled here.

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

**Both noise floors were measured on 2026-10-21 (EXP-009) and both are larger than this section originally
assumed. The numbers below replace the estimates.**

- **Public LB: the minimum detectable effect is ~4 tasks (~0.07), not 2 tasks (0.035).** Submissions #1 and
  #3 were near-identical configs -- the only live delta was `max_time_minutes` 4.5 -> 4.0, which was expected
  to *cost* ~0.4 tasks -- and they scored 0.06 = 4/58 and 0.12 = 7/58. Fisher exact two-sided p = 0.53; at
  the pooled rate (11/116 = 9.5%) two **identical** runs differ by >= 3 tasks 42% of the time and by >= 4
  tasks 26% of the time. A doubling of the public score was pure variance. Treat the daily slot as a
  pass/fail budget-and-transfer check, not a measurement instrument -- the public half is only 58 of ~120
  tasks and the private half decides the final standing. Check any move with
  `python tools/run_forensics.py lb <k1> <n1> <k2> <n2>` before reacting to it.
- **dev-48 per-task outcomes churn by more than half between runs.** E0 vs EXP-003 over the same cohort: 14
  distinct tasks solved by either run, only **6 solved by both** (42.9% concordance of the solved set), 8
  discordant pairs, exact McNemar two-sided p = 0.73. Marginal resolve rates alone are therefore **not
  admissible evidence**; always report the paired 2x2 and exact McNemar
  (`python tools/run_forensics.py compare <runA> <runB>`).
- **Resolve rate is the wrong primary outcome at n = 48.** At p ~= 0.23 its sd is ~2.9 tasks, so the
  "delta >= +3 tasks" rule below is barely 1 sigma. Score experiments primarily on high-prevalence process
  metrics that have tight CIs and large expected effects: **empty-patch rate** (39.6% at E0, target < 15%)
  and **median first-edit turn** (18 for tasks that produce a patch vs 43 for tasks that do not -- target
  < 20 for every cohort). Resolve rate stays as a secondary, confirmatory metric.
- **Adoption rule** (unchanged in form, now explicitly secondary to the process metrics): adopt a change only
  if (a) dev-48 delta >= +3 tasks **and** process metrics (malformed, spin, overflow, wall) do not regress,
  or (b) the change is a pure robustness fix with neutral resolve rate -- **and**, in either case, the paired
  table does not show the whole marginal gain coming from discordant churn.
- **Still open:** the 42.9% concordance is measured across two *different* configs, so it bounds config
  effect from above and pure run-to-run noise from below. A same-config number still needs either two
  dev-48 runs of one config (EXP-001a/b, never run) or a free re-analysis of EXP-000's gold-control reruns
  (EXP-009 follow-up 5).

### 5.6 Experiment log format (`experiments/EXP-NNN-<slug>.md`)
```
id, date, owner, hypothesis, single variable changed (diff link), cohort, seed, GPU-h used,
results table (resolve %, empty %, overflow %, malformed %, spin %, median wall, projected 12h),
decision (adopt / reject / rerun), follow-ups
```
Index table in `experiments/README.md`; the current best config is tagged in git (`v1`, `v2`, …) and its zip SHA256 recorded next to each LB submission.

### 5.7 GPU quota budgeting
**Confirmed (2026-10-17, read from the notebook editor's Session options panel): 30 L4×4 hours/week, resets weekly. 10:04 used as of this check (E0 v1's crashed run + v2's in-progress run + exp002–008), ~19:56 remaining this week.** Allocation: 60% experiments (≈ 5 dev-48 runs), 20% held-out/gates, 20% LoRA canary/training-side checks. If quota is tighter, shrink to smoke-8 for screening and dev-48 only for finalists.

### 5.8 Using the 1 submission/day LB slot
- Submit **every day** something useful: a candidate config or a calibration probe (e.g., same config twice to measure LB noise once).
- Never submit a config that has not run on dev-48 with projected worst case ≤ 11 h.
  - **Note added 2026-10-22 (EXP-012):** this gate is now identified as the binding constraint on our score.
    It is what pins us at 4.0 min/task while the public 0.24 config runs 7 min and knowingly ships a 14 h
    *nominal* worst case against the 12 h cap. The rule was adopted after submission #2 (8 min, ~18 h worst
    case) died of Notebook Timeout, and the lesson drawn — "never exceed the gate" — over-corrected; "8 is
    too much, 7 is affordable" was the better reading. **The formula is the actual defect**: `per-task cap
    × 120` is the worst case only if every task runs to its cap, and EXP-003's median at an 8-min cap was
    5.71 min, so it overstates by ~30%. **TODO: re-derive the gate on projected *actual* time** (observed
    median × 120 + setup, with a stated margin) instead of on the cap. Until that is done, EXP-015 needs an
    explicit recorded override rather than a silent one — a timeout still scores **zero**, never partial
    credit.
  - **Measured 2026-10-22 (from E0 and EXP-003 `task_results.jsonl` + traces):** the two phases the
    `cap × 120` formula leaves out are container setup at **3.3 s/task** (median) and grading at
    **14.0 s/task** (mean; 5.8 s median, one 204.6 s outlier) — neither inside the agent cap, together
    **~35 min over 120 tasks**. Use these when re-deriving the gate. Related measurement, recorded so it
    is not re-derived: grading is only **5.4%** of a dev-48 run's wall-clock (E0 11.2 min of 206.7;
    agent 93.4%, setup 1.2%), and `evaluate.py:316 -> :372` runs it inline per task with the vLLM server
    up, so the GPU is held but idle for it. **Splitting the agent run and the validator into separate
    notebooks was considered and dropped 2026-10-22**: 5.4% does not pay for the plumbing or the risk of
    the two grading paths diverging, and the only thing re-grading can actually vary — the *environment*
    a fixed patch is graded in — is already covered at 0 GPU-h by `tools/regrade_patches.py` (EXP-004) and
    `tools/gold_control.py`.
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

### 6.0.1 Related work (added 2026-10-17, in response to a challenge to ground E-STOP against published SOTA)

Three papers bear directly on this, beyond Agentless/AutoCodeRover already cited in E-STOP(a'):

- **Cuadron et al., "The Danger of Overthinking: Examining the Reasoning-Action Dilemma in Agentic Tasks"
  (arXiv 2502.08235)** is the closest published match to what exp005/exp006–008 found. It analyzes 4,018
  agent trajectories **on SWE-bench Verified specifically** and names three failure modes: **analysis
  paralysis** (the agent's attention drifts into long internal planning with little environment progress —
  this is exp005's "18/20 never finish LOCATE/REPRODUCE/EDIT," now with an academic name and an independent
  large-sample confirmation that it's a known, common failure mode, not an artifact of our harness or shim
  cohort); **rogue actions** (firing multiple actions per step when errors appear, breaking sequential tool
  protocols — relevant to our malformed-call rate, E2/E3); and **premature disengagement** (the agent decides
  it's done from its own internal prediction rather than environment feedback — the opposite failure, relevant
  to E10's submit-policy question). Their finding that higher "overthinking score" trajectories correlate with
  lower resolve rate, and that *selecting the lower-overthinking-score sample from several rollouts* recovers
  ~30% better performance at 43% lower cost, is independent support for E2/E3's thinking-budget axis (less
  internal deliberation, not more, helps) and suggests a **best-of-N / overthinking-score reranking** approach
  as a candidate E-STOP variant if (a') and (b) both fail — not yet added to the backlog, flagged here for
  later.
- **Chen et al., "LocAgent: Graph-Guided LLM Agents for Code Localization" (arXiv 2503.09089, ACL 2025)**
  reports a fine-tuned Qwen2.5-Coder-32B-Instruct (same size class as our model) using graph-based tools for
  localization reaches 92.7% file-level accuracy and a **12% Pass@10 resolve-rate lift on SWE-Bench-Lite**
  purely from the localization method. This is independent, size-matched evidence for E5 (graph tools) and
  reinforces E-STOP(a')'s choice to route LOCATE through `get_code_neighbors`/`search_similar_code`/
  `get_code_subgraph` rather than open-ended grep.
- **"Budget-Aware Tool-Use Enables Effective Agent Scaling" (BATS, arXiv 2511.17006)** confirms the general
  principle behind exp006–008 (a bigger or better-tracked budget alone doesn't help without a mechanism that
  acts on it) but does it by injecting a live, harness-generated "remaining budget" block into the agent's
  context at every tool-call step, rather than asking the model to self-report. This is the code-level
  mechanism we assumed was unavailable (`experiments/README.md` Q2: declarative-only harness, no templating
  hook into tool-output text). **Worth a cheap re-check**: confirm in `eval_config.yaml`/harness source whether
  tool-output text can be templated with a harness-computed value at all before ruling this out again — if
  it's genuinely impossible, E-STOP(a')/(b) stand as the best available substitutes; if it turns out to be
  possible, it outranks both, since BATS is closer to removing the decision from the model than either.

### 6.0.2 Research sweep, 2026-10-18 — production-harness grounding + cross-check against E0 traces

Triggered by: before drafting the E-STOP(a') prompt diff, checked both the academic SWE-bench-localization
literature (beyond §6.0.1's three papers) and how production agent harnesses (Claude Code, Devin, Cursor,
Windsurf) actually handle "when does the agent stop searching." Cross-checked every claim against E0's own
trace data where possible, not taken on faith. Documenting all sources found, including ones that turned out
tangential, so the search isn't silently re-done later.

**Direct empirical cross-check (no new GPU spend, reused E0 traces):** parsed all 48
`runs/E0-dev48-baseline/runs/E0-dev48-baseline/official/traces/*.json` files for tool-call names. Result:
**0/48 tasks ever called `get_code_neighbors`, `search_similar_code`, or `get_code_subgraph`** — 861
`run_command` calls and 563 `read_file` calls, zero graph-tool calls. This confirms the current prompt's
framing (`submission/prompts/swe_coder.md` line 100: "Graph tools... are optional: use them only if two grep
queries found nothing") is dead code in practice: grep via `run_command` effectively always "succeeds" (exit
0, some output) long before any two-failed-greps threshold is reached, so the fallback branch never fires.
This is now the primary evidence for redesigning E-STOP(a')'s LOCATE as graph-tools-**first**, not
grep-first-with-structured-fallback.

**Academic sources (new since §6.0.1):**
- **PatchPilot (Li et al., ICML 2025, arXiv 2502.02747)** frames the exact tradeoff our whole E-STOP line
  rests on: "agent-based planning" (flexible, high-ceiling, costly, unstable) vs. "rule-based planning" (fixed
  workflow, efficient, stable, can underperform if the workflow is wrong). Five fixed stages — reproduction →
  localization → generation → validation → refinement — reach competitive SWE-bench numbers at <$1/instance
  with higher stability than open-source agentic baselines. Independent, recent (ICML) validation that a fixed
  staged workflow is a legitimate design point, not a fallback for a weak model — directly supports E-STOP(a')'s
  approach and roughly matches our existing Protocol's phase structure already.
- **SweRank (arXiv 2505.07849)** and **SWE-Search (ICLR 2025)** both bound search architecturally rather than
  through model self-restraint: SweRank via a two-stage retrieve-then-rerank model, SWE-Search via MCTS capped
  at 3 expansions/node. Same family of evidence as Agentless/AutoCodeRover/LocAgent (§6.0.1): bound through
  structure, not instruction.
- **"Model or Harness? An Interaction-Centric Taxonomy for Localizing Agent Failures" (arXiv 2607.28802, 2026)**
  supplies an attribution rule directly applicable to E0: a failure is harness-attributable, not model-
  attributable, when a more-capable model under the *same* harness conditions would not have been expected to
  avoid it. An open-ended search loop with no forcing function is a harness design choice, not a capability
  gap — i.e. this gives a principled reason E-STOP (a harness/prompt fix) is the correct lever for the
  54%-stuck-in-LOCATE finding, rather than "wait for a bigger/better model."
  **This same framing is the governing logic for the LoRA-gate restructuring in §6.2 below**: per this paper's
  rule, a *harness* gap (unbounded loop) should be fixed at the harness/prompt level first, and *then* a
  trained-adapter experiment is judged against whatever the harness-fixed baseline already achieves — not a
  reason to defer LoRA on the calendar, but a reason to keep the LOCATE-adapter idea (§6.2) scoped to the same
  narrow behavior E-STOP(a') targets, rather than a general capability upgrade.
- **SWE-Bench Pro (arXiv 2509.16941)** independently tracks a "Stuck in Loop" failure category with real
  cross-model variance (reports Claude Sonnet 4 markedly higher than Opus 4.1) — confirms this is a named,
  recognized failure class industry-wide, not an artifact specific to our harness, cohort, or model choice.
- **Fail-Fast/RestartSmart (arXiv 2608.03222) and EarlyEval (arXiv 2609.02783)** train a small external
  monitor (0.6B in FailFast's case) to predict trajectory failure from an early prefix and trigger a restart;
  reported +5.2pp resolution (66.6%→71.8%) at a 25%-false-positive operating point on SWE-bench-Verified, on a
  different model stack than ours. Not pursued now — it needs a second trained model served alongside the
  policy, which the current harness (`discover_declared_models()` enforces exactly one base checkpoint,
  §1/4.1 finding) doesn't straightforwardly support — but flagged as a cheaper alternative to SWE-PRM
  (§6.2's "future-work" note) if the harness's single-model constraint is ever relaxed: a classifier is much
  smaller and cheaper to train than a second LLM-based process reward model.

**Industry/production sources (new):**
- **Claude Code** itself: confirmed (an Anthropic engineer stated this directly) that it uses no RAG/vector
  index — pure grep-based search. Its only bounding mechanism is the built-in **Explore subagent**: read-only,
  tool-scoped (no edit tools available to it), used as the *primary* exploration mechanism, not a fallback
  tried only after softer instructions fail. This is the production analogue of our **E-STOP(b)** (tool-scoped
  LOCATE-only sub-agent via `agent_tool`) — but deployed as a first-line design choice, which is evidence
  against treating (b) as contingent purely on (a') underperforming (see the revised note under §6.1's E-STOP
  row below).
- **Devin 2.0 "Devin Search"**: a separate agentic search tool with a tiered depth (default vs. opt-in "Deep
  Mode" for harder queries) — another production pattern for bounding exploration by tier rather than open
  iteration.
- **Cursor**: reported (third-party, not an official Cursor engineering post) two-stage embedding search →
  LLM reranker — bounds by top-k retrieval, structurally identical to what `search_similar_code(k=10)` already
  gives us if used as the default entry point instead of a fallback.
- **Windsurf**: shipped a dedicated retrieval model ("SWE-grep") rather than relying on agentic grep loops —
  another vote for replacing the open loop with a retrieval call as step one.
- **Community tooling** (Semble, grepai, LSP-routing hooks, a widely-shared HackerNoon post "Claude Code was
  burning tokens until I put a gate in front of it"): converging, third-party-sourced consensus that grep-first
  agentic search is recognized in production as token/time-wasteful, and the common fixes are either semantic
  search tools (maps to our `search_similar_code`) or hard pre-call gates blocking unbounded greps (maps to
  making LOCATE a fixed-step pipeline with no grep loop, rather than softening the existing cap). Treat the
  specific numeric claims from these sources (token-savings percentages) as vendor/author-reported, not
  independently verified.

**Net effect on the plan:**
1. E-STOP(a')'s LOCATE redesign changes from "grep-first, graph-tools-as-structured-fallback" to
   **graph-tools-first** (`search_similar_code` as step one, not gated behind two failed greps) — the E0 trace
   evidence above shows the fallback framing produces zero usage, not occasional usage.
2. E-STOP(b) (tool-scoped sub-agent) is no longer framed as strictly contingent on (a') falling short of the
   80% bar — see the updated note in §6.1's backlog table.
3. LoRA (§6.2) is restructured from a date gate to an evidence gate — see §6.2 below; the new LOCATE-adapter
   candidate experiment is a direct, data-cheap application of the LocAgent/PatchPilot findings (fine-tune the
   narrow localization behavior specifically, not general patch-writing capability).
4. Resolve-rate expectations for E-STOP(a') should be read separately from `phase_reached` movement: LocAgent's
   headline numbers (92.7%/+12%) come from a *fine-tuned* model; PatchPilot's fixed-workflow numbers (prompt/
   rule-based, no training) are the closer analogue to what prompt-only E-STOP(a') can realistically achieve.

**Free sanity check, run 2026-10-18 (no GPU/TPU spend):** before committing to the LOCATE-adapter training
pipeline (§6.2), checked whether `search_similar_code` would actually surface the gold-patch file as a
top-10 hit if called with the raw issue text as the query. Reading `embedding_utils.embed()` and
`retrieval_utils.get_similar_nodes()` directly surfaced a prior fact worth recording on its own: **any
free-text (multi-word) query never reaches the real precomputed-embedding path at all** — `embed()` only
resolves a near-exact *symbol-name* match (suffix match against known node names), and any query containing
whitespace is routed straight to the lexical keyword-matching fallback (token-overlap scoring against node
names/text, documented in the tool's own docstring as "falls back to lexical keyword matching if no symbol
matches"). So for the way E-STOP(a') actually intends to call it (`search_similar_code(issue text)`), the
tool's behavior *is* that lexical fallback, not semantic search — there is no separate "real" embedding
behavior being approximated.
This repo checkout also has no local `data/graphs`/`data/embeddings` (those are populated only inside the
Kaggle kernel from the competition's mounted dataset), so the literal tool call can't be exercised here
regardless — confirming the lexical path was the only one worth testing offline anyway.
Ran that exact lexical-scoring algorithm (ported verbatim from `retrieval_utils.py`) against real extracted
source (from `data/local/snapshots/*.tgz`, non-test/non-docs `.py` files parsed into function/class nodes via
`ast`) for a 19-task sample stratified across the 4 repos with local snapshots (fastapi/rich/requests/httpx —
same universe as dev-48), querying with each task's `problem_statement` and checking whether any of the
gold-patch's changed files appeared in the top-10 results. **Result: 11/19 (57.9%) top-10 hits** —
fastapi 3/6, requests 4/6, rich 3/6, httpx 1/1. Script and full per-task results:
`scripts/` not yet committed (ran from scratchpad; rerun-able — see note below).
Reading: 58% is a meaningful, non-trivial hit rate for a pure keyword-overlap heuristic with no training and
no real embeddings, which (a) supports graph-tools-first in E-STOP(a') — `search_similar_code` called on raw
issue text is doing *something* useful roughly 3 times in 5, strictly better than doing nothing, even before
any LOCATE-adapter training; (b) sets a concrete, non-trivial bar for the LOCATE-adapter idea in §6.2 to beat
— training only pays off if it pushes meaningfully past ~58% top-10 (e.g. via better-chosen tokens, symbol
extraction from the issue text first per E-STOP(a')'s L1 step, or a trained reranker), not if it merely
matches what free lexical matching already gets for ~40% of tasks (fastapi/rich sit lower than
requests/httpx, plausibly because larger repos have more token-collision noise — worth rechecking with a
larger sample before trusting the per-repo breakdown). Caveats: n=19 is a quick stratified sample, not the
full 129; "file-level hit" is a looser bar than "exact function/line," so this likely overstates how directly
useful a bare `search_similar_code` call would be without the L3 `get_code_neighbors`/L4 `get_code_subgraph`
narrowing steps that follow it in the E-STOP(a') chain; and querying with the raw multi-paragraph issue text
(rather than an L1-extracted identifier) may be noisier than the chain's actual intended usage — rerunning
with L1-style extracted identifiers as the query is a natural follow-up before trusting this number further.

**Follow-up run, full N=129, both caveats addressed (2026-10-18):** reran the identical lexical-scorer port
against the full local universe (all 129 tasks with a snapshot, not the n=19 stratified sample), and added a
second query variant — an L1-style extracted-identifier query (backtick-quoted spans, dotted.paths,
snake_case/CamelCase tokens pulled from the issue text, since E-STOP(a')'s actual L1 step isn't written into
`submission/prompts/swe_coder.md` yet, so there was nothing to port verbatim; this is a reasonable proxy, not
the literal future prompt). Results:
- **Raw issue-text query, full N (replicates the first pass at full sample size): 76/129 (58.9%)** —
  fastapi 35/67 (52.2%), requests 10/13 (76.9%), rich 30/48 (62.5%), httpx 1/1 (100%). Closely matches the
  n=19 estimate (57.9%), so the first-pass number was not a small-sample artifact.
- **L1-style extracted-identifier query, full N: 84/129 (65.1%)** — fastapi 45/67 (67.2%), requests 10/13
  (76.9%), rich 28/48 (58.3%), httpx 1/1 (100%).
Reading: identifier extraction buys +6.2pp overall (58.9%→65.1%), driven almost entirely by fastapi
(+15pp, 52.2%→67.2%); requests is identical (query construction doesn't matter when the raw text already
contains the right tokens); rich is slightly *worse* (-4.2pp) — plausibly because rich issues lean more on
prose description of visual/rendering behavior than on code-identifier mentions, so stripping prose loses
signal extraction doesn't replace. Net: query construction is a real, non-trivial lever (not noise), but a
modest one — it does not come close to closing the gap to LocAgent's 92.7% (that number is from a *fine-tuned*
model per the correction already on record above), and confirms the §6.2 LOCATE-adapter bar should be read as
"beat ~65%, not ~59%." This also means E-STOP(a')'s L1 step, when written, should extract identifiers before
querying `search_similar_code` rather than passing the raw issue text — a free, no-training win consistent
with the graph-tools-first redesign already adopted above. Script and full per-task results (both variants):
`scripts/` not yet committed (ran from scratchpad; rerun-able — see note above).

**E-STOP(a') prompt diff written, 2026-10-18 (not yet run):** `submission/prompts/swe_coder.md`'s LOCATE step
(`# Protocol`, step 1) is rewritten from "grep-first, graph tools optional only after two failed greps" to the
fixed 4-call sequence this section and §6.0.2 argue for: (a) no-tool-call identifier extraction from the issue
text (backtick spans, dotted.paths, snake_case/CamelCase — the same heuristic validated above at 65.1%, not
the raw issue paragraph), (b) `search_similar_code(identifiers)`, (c) `get_code_neighbors` on the top hit, (d)
`get_code_subgraph` on the candidate list, (e) one `read_file` on the settled-on location — with a single
`git grep` fallback allowed only if (b) returns nothing, then a mandatory move to REPRODUCE/EDIT either way (no
open-ended loop). REPRODUCE/EDIT/VERIFY/SUBMIT and the budget-ledger section are untouched from the E0
baseline (this stays a one-variable change, LOCATE only, per the backlog's "one variable at a time" rule).
Diff is staged (`git diff --cached -- submission/prompts/swe_coder.md`), not yet run on dev-48 — next step is
the E0 baseline run finishing first (so E-STOP(a')'s dev-48 result has an E0 number to compare `phase_reached`
against, per the "done" criteria below), then this prompt runs as E-STOP(a')'s single dev-48 run.

### 6.0.3 EXP-002 smoke-8 result + delegation-vs-alternatives research, incl. a confirmation-bias check (2026-10-18)

**EXP-002 (E-STOP(a') smoke-8) result: rejected, before any dev-48 spend.** The fixed-sequence LOCATE prompt
rewrite from §6.0.2 above ran on the harness. Of smoke-8's 8 tasks only 4 passed gold control (same soundness
filter as `experiments/README.md` Q5); of those 4, resolve was 2/4 (n too small to read against E0's 22.9%).
The result that matters is not the resolve rate but that **the mechanism the rewrite was supposed to force
only partially fired**: `get_code_neighbors`/`get_code_subgraph` were called zero times across all 4 traces.
`search_similar_code` itself, however, *was* called — first in fastapi_14301 and fastapi_14448, second in
rich_3468; only rich_3006 (the fastest-resolving task) skipped it. **Correction, 2026-10-18, after a second
independent trace read (full detail in `experiments/EXP-002-estop-a.md`):** reading the tool *outputs*, not
just call names, shows the chain broke after step (b) because step (b)'s output was unusable in the 3 cases
that reached it (lexical-fallback junk at 0.22 similarity in fastapi_14448; a wrong-but-deceptively-high-
similarity match at 0.9997 in rich_3468) or because step (b) already returned the correct answer, making the
later steps genuinely redundant rather than skipped (fastapi_14301). This is a plausibly rational response to
bad-or-sufficient tool output, not evidence the model ignores prompt instructions — the more likely bottleneck
is `search_similar_code` recall/output quality against real mounted graph/embedding data, untested until the
free CPU-only recall check below runs. Cross-checking the 4 sound tasks against E0's own dev-48 traces for the
identical task ids shows an identical resolve/fail pattern in both runs, i.e. the prompt rewrite was a
behavioral no-op on this sample on the resolve-rate axis, even though step (b) compliance was mostly present.
A second, independent finding from reading the raw traces: `phase_reached` (the regex over the agent's self-
reported `[phase=...]` ledger line, §6.1's current "done" gate) is unreliable — all 4 agents abandon the
ledger tag within 1-3 of 19-39 turns, so the metric measures ledger-tag persistence, not real phase progress,
which calls E0's own "54% stuck in LOCATE" headline into question too (computed with the identical regex).
Full writeup: `experiments/EXP-002-estop-a.md`; ledger entries `experiments/README.md` §3 (EXP-002 row) and
Q13/Q14.
**Conclusion that follows:** the original "fixed sequence is optional advice the model ignores" framing
overstated the evidence — compliance with step (b) was mostly present; the open question is whether
`search_similar_code`'s recall/output quality against the real mounted data is the actual bottleneck, which
the free CPU-only recall check (below) tests directly before any further LOCATE redesign spend.

**Does the published literature support "tool-scoped sub-agent" as the fix, and is it the cheapest one?**
Researched in two deliberate passes — an initial supporting-evidence pass, then a second pass explicitly
tasked with finding disconfirming evidence and cheaper alternatives, per direct instruction, to check the
first pass hadn't just gathered citations for a conclusion already reached.

- *For tool-scoping*: the "grep beats semantic tools" pattern (a model defaulting to a familiar general tool
  over a more specific declared one even under explicit instruction otherwise) is widely documented in
  production, not specific to our model — Claude Code's own Explore sub-agent is read-only/tool-scoped and
  used as the *first-line* exploration mechanism, not a fallback; a widely-shared practitioner account
  describes fixing the identical pattern with a `PreToolUse` hook gate, not stronger wording. Published
  localization architectures (Agentless arXiv 2407.01489, AutoCodeRover arXiv 2404.05427, OrcaLoca
  arXiv 2502.00350) all bound search *structurally* — fixed pipeline or restricted API surface — never by
  prompting an open-ended agent to restrain itself. The competition harness's own official reference
  `sample_submission` already ships exactly this pattern as its reference design: a graph-only
  `code_analyzer_agent` via `agent_tool`, tools restricted to `read_file`/`search_similar_code`/
  `get_code_neighbors`/`get_code_subgraph` (no `run_command`, no `edit_file`), on a separate `tool_lora`
  adapter — i.e. this is the harness's intended shape, not a novel guess. API-level forced tool use
  (`tool_choice: "required"`) was checked and ruled out as a substitute: it forces *a* declared tool or one
  *named* tool, never "one of this named subset," so it cannot reproduce restricted-toolset scoping inside a
  single flat tool list — a separate sub-agent with its own tool list is the correct generalized mechanism,
  not an arbitrary implementation choice among equivalents.
- *Against treating it as risk-free*: multi-agent-system literature independently warns decomposition has a
  real coordination cost that can erase the benefit of scoping — arXiv 2604.02460 (not independently verified
  as a Stanford paper; it is about multi-hop reasoning, not code, and its abstract attributes the gap to
  unaccounted compute, not a "communication bottleneck" as this doc previously stated) shows single agents
  can match/beat multi-agent decompositions at equal compute; Silo-Bench (arXiv 2603.01045) is cited for a
  "15-49% performance loss" figure that is **not actually in its abstract and is unverified** — its setup
  (information distributed across agents on algorithmic tasks) also transfers only loosely to our single-
  handoff sub-agent case; Berkeley's MAST taxonomy (arXiv 2503.13657, 1600+ traces, 7 frameworks, 14 failure
  modes, confirmed accurate) argues most multi-agent failures need structural redesign, not superficial
  patches, with one of its three categories being "system design" issues (corrected from "specification
  issues," which this doc previously had wrong). **Citation-accuracy correction, 2026-10-18**: an independent
  review (Opus 5.5, xhigh effort) also found this doc had wrongly presented the "12/18→6/18 same-model-
  delegation regression" as "our own" result — it is in fact `[M]` (secondhand/community-reported, see line
  ~160 below) and **E9 was never actually run in this project**. The open question EXP-003b must still
  resolve empirically is whether *tool-scoping specifically* (not delegation in general) avoids a regression
  like the one that `[M]` figure describes, since the cited case was same-capability delegation, not tool-
  restricted — but this is a hypothesis to test, not an existing data point from our own backlog.
- *Cheaper alternative, not previously considered*: tool-*description*-quality rewrites alone, no sub-agent,
  no training. Arcade reports ~10x tool-selection-error reduction from description edits alone across 20,000+
  evaluations; ToolScope (+8.38-38.6pp) and RAG-MCP (13.62%→43%) get similar gains from retrieval-based
  shrinking of the visible tool list per turn. Caveat carried forward honestly: these results are typically
  measured on registries with 10+ declared tools, and `submission/agent.yaml` only declares 9 total, so the
  effect size may not transfer directly — this is why it's treated as a cheap, high-ROI-*if*-it-works first
  test, not a confident prediction.
- *Alternative checked and ruled out by harness constraints, not by preference*: Agentless-style automatic
  context injection ahead of the agent's first LLM turn (sidestepping tool-choice compliance entirely by not
  requiring a localization tool call at all). Re-reading `HARNESS_README.md`'s submission-format description
  confirms this is infeasible here: submissions are YAML-only through a closed, sandboxed
  `compile_submission` resolved against closed host registries (`ToolRegistry`/`ModelRegistry`/
  `SkillRegistry`/`CallbackRegistry`) — no custom Python entrypoint (`agent.py`/`agent_fn`) is permitted, so
  there is no hook point to inject retrieved context before the first turn the way Agentless's own reference
  implementation does.

**Net effect — revised order, cheapest-first:**
**EXP-003a (tool-description rewrite in `agent.yaml`) is dropped, not just deprioritized** — it rested on a
false premise twice over: (1) `agent.yaml`'s `tools:` field only accepts tool-name strings/`agent_tool`
references/inline agent dicts, there is no per-tool description-override field to rewrite (confirmed against
`HARNESS_README.md` §2.3 and the file itself — the real JSON-schema description the model sees is fixed by
the host `ToolRegistry`, not editable from the submission); (2) the harness already auto-injects a one-line
capability description for each graph tool into the initial prompt whenever graph/embedding data exists for
the task's repo (`HARNESS_README.md` §5.2, "Code Intelligence Tools" block), and the corrected EXP-002 trace
read above shows `search_similar_code` already gets called 3/4 times — so the premise that the model needs a
better *description* to find the tool is itself unsupported; the actual gap is `search_similar_code` output
quality/recall, which a description rewrite cannot fix.
1. **Free CPU-only recall check** (new, replaces EXP-003a as the immediate next step): call the real
   `search_similar_code`/`get_code_neighbors`/`get_code_subgraph` harness tool implementations (not a hand-
   ported reimplementation) against the actual mounted graph (`data/graphs/<repo>.json`)/embedding
   (`data/embeddings/<repo>.npz`) data for every sound task, checking recall against the gold-patch function
   directly. No GPU spend. Must run inside a CPU-only Kaggle kernel, since this repo checkout has no local
   `data/graphs`/`data/embeddings` — those are only populated inside a Kaggle kernel from the competition's
   mounted dataset.
2. **EXP-003b** (renames/absorbs E-STOP(b); the `[M]`/never-run E9 figure is no longer treated as "our own"
   existing data point, see citation correction above): only after (1), and only if (1) shows real recall
   problems that a tool-scoped sub-agent would plausibly fix — fix `submission/sub_agents/analyzer.yaml`
   (strip `run_command`, which it still has, unlike the official `code_analyzer.yaml` reference) and
   `submission/prompts/analyzer.md` (remove the "graph tools only if two greps fail" escape hatch; add
   `{problem_description}`/`{hints?}` session-state passthrough per `agent_tool.py:227-260`/
   `agent_runner.py:676-681`; change the output contract from `path:start-end` to dotted symbol + derived file
   path + verbatim snippet; cap calls at ≤5, not 8) to match the harness's reference sub-agent, add a root-
   agent instruction to call the analyzer as step 1 (delegation compliance is a parallel problem to tool-
   scoping itself), wire `agent_tool: config_path: sub_agents/analyzer.yaml, skip_summarization: true` into
   `submission/agent.yaml`, run a 1-task dry run to confirm sub-agent trace events are captured, then smoke-8
   screen it — instrumented specifically to check whether the analyzer's top reported location matches the
   gold-patch's changed files (not just aggregate resolve), so a handoff-information-loss regression is
   visible if it happens, not masked by a flat resolve-rate number.
3. Both the recall check and EXP-003b must use a corrected `phase_reached`/compliance signal (observed
   tool-call family, not the self-reported ledger tag) before either one's result is trusted — the §6.1 "done"
   criteria below are updated accordingly.

Mirrored in `experiments/README.md` §1o (narrative) and Q13/Q14 (ledger).

### 6.1 Experiment backlog (one variable at a time; priority order; cost in dev-48 runs ≈ 3–4 GPU-h each)
| ID | Variable | Hypothesis | Measure | Cost |
|---|---|---|---|---|
| **E0** | **Representative baseline**: current prompt (post shim-fix, pre-ledger-experiments — i.e. roll back the exp006–008 ledger-wording churn, keep the exp001–005 shim fix) on **dev-48** (stratified, unbiased), not the shim cohort | Establishes the real resolve-rate baseline and, critically, the `phase_reached` / `time_cap_hit` vs `calls_cap_hit` distribution across a representative sample — tells us whether exp005's "18/20 never finish LOCATE/REPRODUCE/EDIT" generalizes or was partly an artifact of the shim cohort being unusually hard | resolve % (± Wilson CI), empty %, phase_reached histogram, time_cap_hit % vs calls_cap_hit % | 1 run, highest priority — blocks the Oct 17 LB slot decision and informs whether E-STOP is even needed |
| **E-STOP** | Structural forced phase transition that does **not** depend on the model doing arithmetic or complying with self-report instructions. **(a) dropped 2026-10-17** (shrink-cap + worked-example-transcripts): same category as the already-3×-failed exp006–008 ledger-wording fixes. Not adopted; not run. **(a') REJECTED 2026-10-18 on smoke-8 (EXP-002)**: `get_code_neighbors`/`get_code_subgraph` called 0/4 times; `search_similar_code` itself *was* called 3/4 times (first in fastapi_14301/fastapi_14448, second in rich_3468 — corrected 2026-10-18, see `experiments/EXP-002-estop-a.md`), but its output was unusable (lexical-fallback junk, or a wrong-but-high-similarity match) or already sufficient in all 3 cases, so later steps weren't exercised; identical resolve/fail pattern to E0 on the same 4 tasks. The likely bottleneck is `search_similar_code` recall/output quality, not prompt-instruction non-compliance. **Superseded by: (1) a free CPU-only recall check (§6.0.3) testing the real tool against real mounted data; (2) EXP-003b**, only if (1) shows a real recall problem — the harness's own reference-design tool-scoped sub-agent (`agent_tool`, graph-tools-only, no `run_command`/`edit_file`), instrumented against handoff-information-loss risk, not just aggregate resolve. EXP-003a (tool-description rewrite) is dropped entirely — no such override field exists in `agent.yaml`, and the harness already auto-injects graph-tool descriptions into the prompt | The free recall check is free to test (CPU-only, no GPU spend) and resolves whether EXP-002's bottleneck is tool output quality before spending further LOCATE-redesign effort; EXP-003b is the harness's own documented reference shape, not a novel guess, but carries a real coordination-cost risk per multi-agent-failure literature (MAST arXiv 2503.13657, confirmed; arXiv 2604.02460 and Silo-Bench arXiv 2603.01045 citations corrected/caveated, §6.0.3) and must be checked carefully — the "12/18→6/18 same-model-delegation" figure sometimes cited here is `[M]` (secondhand) and was never run in this project, not an existing in-project data point | corrected phase/compliance signal (tool-call family observed, not self-reported ledger tag — fix `tools/analyze_traces.py` first, §6.0.3), resolve, wall; compare against E0 baseline | free recall check: 0 GPU-h (Kaggle CPU kernel only); EXP-003b only if the recall check shows a real problem, 1 smoke-8 + 1–2 dev-48 runs |
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

**Superseded 2026-10-22 by §6.1a below — EXP-013 → EXP-014 → EXP-015 come first, and the E-series order below
resumes only after them. Several E-rows are also partly pre-answered by the published 0.24 config: E5 by its
graph-tool ban, E11 and E2 by its 6144/4096 settings, E6 by its 7 min / 28 calls pairing.**

**Revised order (2026-10-18, post-EXP-002, re-revised 2026-10-18 post-recall-check): E0 → E3 → E6 → E1 → E2 →
E5 → E4 → E10 → E7 → E11 → E8**. E-STOP(a') is removed from the queue (rejected on smoke-8, see §6.0.3 and its
updated row above). **EXP-003b is now dropped from the queue entirely, not deferred** — see the recall-check
result immediately below; EXP-003a (tool-description rewrite) stays dropped for the same §6.0.3 reason.
**Not in this order (added 2026-10-20):** EXP-008 (`SequentialAgent[ParallelAgent[analyzer_A, analyzer_B],
swe_coder]` vs E0 on dev-48) is a candidate in the separate concurrency track (§6.3) and is **blocked**, not
queued — EXP-007 showed swegemma's synchronous tools stall sibling branches, and the prerequisite fix is
not yet scoped.
"Done" criteria to move past each of the first three (the ones that matter for the Oct 25 gate):
- **E0 done** when we have a resolve-rate point estimate + Wilson CI on dev-48 and a `phase_reached` /
  time-cap-vs-calls-cap breakdown. This number is what tells us whether to spend the Oct 17 LB slot now or
  wait one more day for E-STOP(a')'s result — **send back to drawing board** only if the harness itself looks
  broken (e.g. near-zero empty-patch-free resolves even on tasks that clearly reach VERIFY), not if resolve
  rate is merely low (low-but-nonzero is expected and is a reason to keep iterating, not a reason to stop).
  Caveat added 2026-10-18 (EXP-002/Q13): the `phase_reached` histogram this criterion partly rests on is
  measured with the same ledger-tag regex shown unreliable on smoke-8 — read E0's phase breakdown with that
  caveat until `tools/analyze_traces.py` is fixed to derive phase from tool-call family instead.
- **Free CPU-only recall check: DONE, 2026-10-18 — EXP-003b skipped, not escalated to.** Both halves ran: a
  local `git grep` lexical baseline (113 scored tasks, recall@1/3/5/10 = 24.8%/35.4%/37.2%/41.6%) and the
  Kaggle CPU-only kernel (`rainm4/gemma4-recall-check`, COMPLETE, 0 GPU-h) replaying the real
  `search_similar_code`/`get_code_neighbors` against actual mounted graph/embedding data on the identical
  113-task set. **The real tool loses to the free grep baseline at every k** (single-identifier arm
  14.2/19.5/21.2/24.8%, joined-top-3 arm 16.8/23.9/28.3/34.5%; `get_code_neighbors` chain hit rate 16.5%).
  Per the criterion as written, this is the "materially poor, EXP-002 pattern generalizes" branch — but the
  measured root causes make EXP-003b specifically the wrong next step rather than the right one: (a) only
  62.7% of gold symbols exist as graph nodes at all (`gold_in_graph_rate`), a hard recall ceiling no sub-agent
  wrapper can rank its way around; (b) embedding-space anisotropy is real and repo-wide (mean pairwise cosine
  0.72–0.93 depending on repo/snapshot), not an n=1 EXP-002 fluke. A tool-scoped `analyzer` sub-agent calling
  these same two tools inherits both limitations unchanged — it cannot find a node that isn't in the graph or
  rank better in a space that doesn't discriminate. **Decision: do not build EXP-003b.** If LOCATE quality is
  revisited later, the candidates are fixing the underlying tools (graph-construction coverage gap, embedding
  quality) or a lexical-first LOCATE step (grep for candidates, graph only for neighbor expansion once
  seeded) — not a sub-agent wrapper. Full writeup: `experiments/recall_check/README.md`,
  `experiments/EXP-002-estop-a.md` follow-up #3.
  **Correction, 2026-10-19 (independent review):** the 62.7%/anisotropy figures above have real measurement
  bugs (query-extraction regex, `src.`-prefix node-name mismatch — see recall_check/README.md's 2026-10-19
  correction) and should not be cited at face value. The decision to drop EXP-003b still stands, on firmer
  footing: real E0 dev-48 traces show the actual bottleneck is post-LOCATE (wall-clock-bound touch→edit→
  resolved drop-off), not LOCATE recall quality — a tool-scoped sub-agent would narrow a step that usually
  isn't where tasks are lost, regardless of the exact recall numbers once the bugs are fixed.
- **E3 done** when wall-clock time_cap_hit rate drops materially (e.g. ≥ 30% relative) at no malformed-rate
  cost — **adopt**; if time_cap_hit doesn't move, that's evidence time-cap hits are driven by call volume
  (slow convergence to a hypothesis) rather than per-call latency, which redirects weight back toward E-STOP
  and E6 over E2.

After each adopted change, re-run the budget estimator. Every ~5 experiments, run held-out-24 to check we are
not overfitting dev-48.

Cheap pre-screen without GPU: replay logged decision points under the changed prompt (g4kit-replay idea) and count malformed/spin deltas before spending a dev-48 run.

### 6.1a TODO — adopt-the-ceiling-config track (added 2026-10-22 from EXP-012; takes precedence over the §6.1 order above)

**Not yet started. Nothing in this subsection has been implemented or run — it is the queue, not a record.**

Why this jumps the whole §6.1 queue: `experiments/EXP-012-competitive-position.md` establishes that our
0.10 = 6/58 sits at ~the 25th percentile of 3,467 teams (median 8 tasks, mode 10, ceiling 14), and that the
0.24 ceiling config is a **public notebook running the same model and the same nine tools as ours**. The gap
to the top is statistically real (our pooled 17/174 vs their 14/58, Fisher p = 0.0125, and 24.1% is outside
our 95% CI of 6.2–15.1%); the gap to the median is **not** (p = 0.4629, inside the CI). So the whole measured
gap is budget + prompt, and single-variable experiments run 8 tasks below a published baseline cannot close
it at a ~4-task LB MDE with one submission a day.

| ID | Step | Variable(s) | Cost | Measure | Status |
|---|---|---|---|---|---|
| **EXP-013** | **Prompt surgery — do this first** | `prompts/swe_coder.md` only: (1) delete the mandated REPRODUCE heredoc (lines 14 and 102), replace with a one-shot `python -c` rule; (2) add explicit search/read batching (independent greps combined into one `run_command`; `sed` with explicit line ranges, ≤ 3 regions per call); (3) move the first-edit deadline from call 25 to ~12–15; (4) drop the 3 graph tools from the prompt **and** from `agent.yaml`; (5) add the parallel-implementations rule (sync/async, `Client`/`AsyncClient`, typing overloads, `__all__` re-exports) | **0 GPU-h to author**; 1 dev-48 run (~3–4 GPU-h) to verify. *Reduces* per-task time, so it strictly improves timeout safety | **compliance first** (does it stop writing repro files at all?), then empty-patch rate (39.6% at E0) and median first-edit turn (43 for empty-patch at E0). Not the LB on its own — MDE | **TODO** |
| **EXP-014** | Thinking + output budgets | `thinking_budget` 256 → 4096 and `max_output_tokens` 4096 → 6144, **nothing else**. EXP-003 bundled both with a 45→28 call-cap cut that demonstrably cost `rich_3676`, so neither has ever been tested cleanly | 1 dev-48 run | resolve %, overflow %, s/turn (EXP-003's s/turn rose to 7.79–12.13 under similar settings — watch for the same) | **TODO**, after EXP-013 |
| **EXP-015** | Per-task time | `max_time_minutes` 4.0 → 6.0, then → 7.0 if 6.0 scores. **Requires an explicit, recorded override of §5.8's 11 h worst-case gate** (see the note added there 2026-10-22). Largest single knob gap, and also the one that lost submission #2 | 1 dev-48 run per level + LB slots | projected *actual* 12 h time (not cap × 120), resolve % | **TODO** — the gate override is a decision to be taken explicitly, not a default |

Sequencing rationale: EXP-013 is free to author, carries **no** timeout risk (it removes work rather than
adding it), and buys back the 27.3% of wall-clock our own forensics measured going into heredoc repro files
— which is what makes EXP-015's time increase cheaper than it was for submission #2.

Honest expectation for all three together: **+4 to +8 LB tasks (0.17–0.24)**, i.e. the modal-to-ceiling band,
not past it. 39 teams already sit at 13–14 tasks on near-identical configs, so matching the published config
buys a seat in a crowded tie that the private half will reshuffle by a few tasks either way. Treat it as a
floor to build from, not a result — what could go past it is what those notebooks lack: the measured
wall-clock breakdown, the calibrated MDE, the confirmed gold-control flakiness mechanism, and EXP-009 Part
C5's finding that reproduction correlates with *winning* (20/20 resolved runs reproduced before their first
edit). Note the last two are compatible rather than contradictory: the 0.24 prompt bans the repro *file*
while keeping one `python -c`, i.e. cheap reproduction — exactly where EXP-009 Part C2 landed independently.

**Deliberately NOT adopted from the 0.24 config:** its `pytest -k <keyword>` rule. We run whole test files
on purpose, because §1h of `experiments/README.md` established that grading runs whole files and one broken
test anywhere in the file fails the task. Their rule is faster; ours is safer. A genuine open question, not
a copy-this item.

**Carried over, still open (unchanged by EXP-012):** the dev-48 run for EXP-010 (compliance, then
empty-patch rate and first-edit turn) and the E0 dev-48 re-run that would finally give us a same-config
repeat baseline (EXP-009 Part C4 — still the highest-value single quota purchase, since every A/B so far has
had no same-config noise floor beneath it). EXP-013 can be folded into that same run if quota is tight.

### 6.2 LoRA / RFT track (gated)
**Multi-LoRA-per-sub-agent is available** (§4.1 finding, 2026-10-17): the harness serves a distinct adapter per
`LlmAgent`/`agent_tool` as long as every agent shares the same base model (`validate_single_declared_model` only
checks the base, not adapters). Sizing fits the 3 GiB submission cap comfortably: rank-16 ≈110–220MB/adapter (8 fit),
rank-32 ≈220–450MB (6–8 fit), rank-64 ≈450–900MB (3–6 fit), rank-128 max ≈0.9–1.8GB (1–3 fit). The harness's own
documented example is close to our E9 sub-agent idea: `adapter: main_lora` on the root coder, `adapter: tool_lora` on
a read-only analyzer `AgentTool`. This is a **backlog idea gated behind G-LoRA below**, not a v1/E9 change — E9's
same-model delegation test is still the cheap thing to run first (§6.1), and a two-adapter architecture only makes
sense once a single adapter has cleared the canary (step 1 below) and shown it moves behavior at all.

**Gate restructured 2026-10-18 — evidence gate, not a calendar gate.** Previously written as "Gate G-LoRA
(Oct 25)," which tied *starting* LoRA work to a date and to E-STOP(a') first failing. Per explicit user
direction: "we do have time for lora, it should not be gated so long as we are making educated
guesses/experiments/changes — we should not throw things at the wall." The distinction that resolves this:
**when training work starts** and **when a trained artifact is trusted enough to ship** are two different
questions. The date (Oct 25) is dropped. Strict sequencing after E-STOP(a')/prompt-only work is dropped. What
stays, because it's about correctness risk, not about pacing:
- Any specific LoRA idea must be **evidence-grounded** — tied to a concrete, already-observed gap (a failure
  mode in E0/E-STOP traces, a published data recipe at our size class, a free sanity check that confirms the
  mechanism before spending TPU budget) — not a speculative "let's just try fine-tuning." The LOCATE-adapter
  idea below is the first one that clears this bar and can start now, in parallel, on the separate TPU v5e-8
  quota (§1/4.1 — doesn't compete with the L4×4 eval quota dev-48/held-out-24 runs use).
- The three correctness conditions below are **shipping gates**, unchanged in substance, just no longer tied
  to a date — they must still all pass before any trained adapter is used in a real LB submission, however
  early training starts:
  1. Canary passes (Q4): adapter trained to shift logprobs on a fixed prompt shows the shift on the scorer stack (patched vLLM, L4 notebook). If deltas are ~0 → adapters are zeroed → **no-go**, redirect effort to prompts + paper.
  2. KV-cache check: with the adapter loaded, the harness runs 8 tasks without hangs (LoRA shrinks KV to ~7.6k tokens in some reports [M]); rank ≤ 32, exactly 1 adapter [M].
  3. Prompt-only baseline is stable (two consecutive LB submissions without budget/crash failures) — this one
     is about *not shipping an adapter on top of an unstable baseline*, not about waiting for prompt-only work
     to finish; it can be satisfied by the v1 baseline already submitted (§6.0/EXP-001) plus one more clean
     submission, in parallel with adapter training.

**Candidate experiment — LOCATE-adapter from gold-patch-derived targets (added 2026-10-18, evidence-grounded,
startable now):** every one of the 129 public tasks ships its gold/reference patch (`task.get('patch')`,
already used for EXP-000 gold-control sweeps per `experiments/README.md`) — this gives the correct
file/function/line for all 129 tasks **without running a single rollout**, sidestepping the cost of rejection
sampling against our 22.9% base resolve rate (EXP-001). Proposed pipeline:
1. **Free sanity check first, no GPU/TPU spend**: for a sample of gold patches, check whether
   `search_similar_code(query=<issue text or extracted identifier>, k=10)` already surfaces the gold-patch
   file/node in its top-k. If yes for most tasks, this directly validates the premise of E-STOP(a')'s
   graph-tools-first LOCATE redesign (§6.0.2) *and* tells us the adapter's job is narrow (rerank/select, not
   learn code structure from scratch) before committing to a training pipeline. If no, that's equally useful
   signal — it would mean `search_similar_code`'s lexical-fallback path (confirmed in `graph.py`'s docstring)
   isn't matching on issue-text phrasing, which changes what the adapter needs to learn.
2. **If the sanity check is favorable**: build an SFT set of (issue text → gold file/function/line, expressed
   as the L2–L4 tool-call sequence from E-STOP(a')'s deterministic chain) for the 129 gold patches, train a
   narrow LOCATE-only adapter (rank 16, per the existing Training bullet below) targeting exactly the
   compliance/procedural behavior E-STOP(a') targets at the prompt level — this is the Kimi-Dev precedent
   below ("train narrow procedural skill non-agentically first, then adapt to agent form") applied directly,
   and the Model-or-Harness taxonomy's framing (§6.0.2): fix the harness-level gap first, then judge the
   adapter against the harness-fixed baseline, not the raw E0 baseline.
3. This is deliberately **scoped to LOCATE only**, not general patch-authoring capability — narrower than the
   SWE-Gym/R2E-Gym/SWE-agent-LM-32B full-fine-tune recipes below (which target end-to-end resolution), and
   therefore plausibly within a few hundred gold-derived examples rather than thousands of rollout-sampled ones.

If go (data/training mechanics unchanged from the original spec):
- **Data**: rejection sampling on dev-48 + public SWE-style trajectories converted to harness tool format (public & free only), **or** the gold-patch-derived LOCATE targets above (no rollouts needed). Keep only trajectories that resolved **and** had 0 malformed / 0 identical calls; ~200–500 trajectories target for the rollout-based route. Optionally RFT-style: multiple rollouts per task at T=1.0, keep successes.
- **Training**: TRL/PEFT or Unsloth QLoRA on the bf16 31B; rank 16, alpha 32, target attention+MLP projections, 1–2 epochs, LR 1e-4; compute: Kaggle TPU v5e-8 (~20 h/week) via `notebooks/kaggle_tpu_lora.ipynb`, or a rented 1× 80 GB GPU (Unsloth ~22 GB) — decide by cost at gate time.
- **Adapter verification**: `adapters/<name>/{adapter_config.json, adapter_model.safetensors}`, key names match vLLM expectations (g4kit-check-peft idea), logprob canary again with the real adapter, dev-48 run, size well under 3 GiB.
- Ship only if dev-48 Δ ≥ +4 tasks and held-out-24 does not regress.

**Related work (added 2026-10-17)** — how published agentic-SWE training recipes compare to our 31B/LoRA/3 GiB
constraint, and what validates or complicates the note above:

- **Data-recipe precedent, same or adjacent size class.** SWE-Gym (Pan et al.) fine-tuned open Qwen2.5-Coder
  7B/14B/32B on successful agent trajectories and reports a ~13.6-point SWE-bench-Verified lift; its 32B
  checkpoint, data, and verifiers are public. R2E-Gym built 8.1K procedural executable environments (no human
  issue text) and trained with ~3.3K kept trajectories from a Sonnet-3.5 teacher: 32B full fine-tune 20.6→34.4
  pass@1. **SWE-agent-LM-32B** (SWE-smith synthetic bugs, RFT) reports 40.2% pass@1 — the best fully-open
  result in this size class at time of release. **OpenHands-LM-32B** (Qwen2.5-Coder-32B base, trained only on
  the agent's own successful rollouts) reaches 37.2%. All of these are **full fine-tunes at our model's own
  size**, not LoRA — none report LoRA-specific numbers, so the magnitude of our adapter's effect is still an
  open question the canary (Q4) exists to answer, but the *data recipe* (keep only clean, resolved trajectories;
  optionally synthetic/procedural tasks over scarce human-written ones) directly matches what §6.2's "Data" bullet
  already specifies.
- **Kimi-Dev (arXiv 2509.23045, ICLR 2026) is the strongest direct precedent for the training-target note
  above.** Its central claim is exactly our hypothesis, independently validated at SOTA scale: training on
  **Agentless-style data first** (non-agentic localization + repair, RL with verifiable rewards — easier to
  train because the task is narrower and fully supervised) induces reusable **skill priors** (localization,
  edit, self-reflection) that transfer cheaply into agentic form with only ~5K adapted trajectories, reaching
  48.6% pass@1 as a full agent (on par with Claude 3.5 Sonnet 241022) from a 60.4%-Verified Agentless base. This
  is independent confirmation that "train the narrow procedural skill non-agentically, adapt to agent form
  after" is a working recipe, not a speculative one — raises confidence in the §6.2 training-target note, and
  suggests that *if* E-STOP(a')/(b) establish a working structural LOCATE→EDIT split, the resulting cleanly-
  separated trajectories (not just budget-compliance-relabeled ones) are themselves good LoRA training data.
- **SWE-PRM ("When Agents go Astray," arXiv 2509.02360, NeurIPS 2025 SEA workshop)** is the closest published
  analogue to "course-correct a stuck agent without retraining the policy": an inference-time process reward
  model watches the trajectory live and injects taxonomy-guided feedback when it detects redundant exploration
  or looping, lifting SWE-bench-Verified resolution 40.0%→50.6% (+10.6pp) at ~$0.2/task added cost, with the
  largest gains on medium/hard tasks. This is a third, more powerful alternative to E-STOP(a')/(b) — a trained
  monitor rather than a structural prompt or tool-scoping change — but it requires training and serving a
  second model, which is out of scope given the 3 GiB/single-base-model constraints and the Oct 25 timeline;
  noted here as a future-work direction, not added to the backlog.
- **Budget forcing (s1, arXiv 2501.19393)** is the most literal prior art for "force a transition instead of
  asking for one": the technique suppresses/appends a stop delimiter to end a reasoning segment early, or
  appends "Wait" to force continuation, giving hard external control over when a model stops "thinking" and
  starts "answering." Directly analogous to what E-STOP is trying to achieve for "stop searching, start
  editing" — but it requires token-level control over the generation stream (suppressing/injecting at the
  sampler), which (per `experiments/README.md` Q2) our declarative harness does not expose. The harness's
  existing **nudge mechanism** (`tools/analyze_traces.py` `NUDGE_MARKERS`, triggered on truncated tool-call
  tags) is a fixed, harness-internal instance of the same idea — proof the harness *can* inject synthetic
  continuation text under some conditions, but not evidence we can trigger it on our own threshold; worth
  the same cheap re-check as BATS above (§6.0.1) before concluding this path is fully closed.

### 6.3 Concurrency / ParallelAgent track (gated) — added 2026-10-20

**Status: evidence-gated, not buildable yet.** Same gate philosophy as §6.2's 2026-10-18 restructuring: no
date gate. What decides the next step is verified evidence, and the current evidence says a prerequisite is
missing. This is a separate track rather than a §6.1 row because every §6.1 experiment changes one setting of
the single-`LlmAgent` `swe_coder` architecture (§4.1). This track asks a different question: whether the
one-LLM-request-at-a-time pattern itself leaves usable capacity on the table. As noted in §4.1, that pattern
is our design choice. The harness's single-model rule (§1.3) constrains only the shared base checkpoint, not
the agent-tree shape.

**Hypothesis chain and evidence so far (both runs read-only; no agent run on real tasks, no submission change):**
1. *Idle serving capacity exists and is schedulable* — **EXP-006, CONFIRMED** (`experiments/EXP-006-vllm-concurrency-probe.md`,
   22.6 min L4×4, all 4 allowed model sizes booted with the harness-faithful `VllmConfig`). Boot-time
   `max_concurrency_32k` = 8.74 / 19.97 / 45.63 / 67.18 (31B / 12B / e4B / e2B). Even on 31B, the worst case
   and our current model, **88.6% of usable KV-cache capacity sits idle** when only one request is in flight. A
   synthetic HTTP burst showed this capacity can actually be scheduled, so it is not only a KV-cache
   bookkeeping number: `speedup_n4` = 3.21x–3.60x and `speedup_n16` = 9.05x–9.85x across the 4 models. The
   pre-registered rule (`max_concurrency_32k(31B) ≥ 4` AND `speedup_n4 ≥ 2.0`) held (8.74, 3.60x), so EXP-007
   was built.
2. *ADK's own `ParallelAgent` turns that capacity into concurrent agent LLM calls* — **EXP-007 H1, CONFIRMED on
   real 31B** (`experiments/EXP-007-adk-parallel-probe.md`, 12.8 min L4×4). The probe used synthetic read-only
   `analyzer_a`/`analyzer_b` agents built through the real `compile_submission()` path, N=2 branches.
   `relay_max_in_flight = 2` for the parallel arm vs 1 for a sequential control doing the same work, and
   `wall_ratio_parallel_over_control = 0.206` (pass bar ≤ 0.75). The branches overlap on the wire, not just in
   ADK's internal bookkeeping.
3. *A long synchronous tool call in one branch does not stall the sibling* — **EXP-007 H3, FALSIFIED: the stall
   is real and large.** In one branch, a ~1 s `slow_sync_tool` (plain `time.sleep`) made the parallel arm ~78%
   slower (1.997 s vs 1.122 s; `h3_projected_stall_frac = 0.780`, pass bar ≤ 0.10). An independent
   event-loop-lag monitor recorded `max_lag_s = 0.961 s`, against ~0.001–0.002 s in every other real-vLLM
   arm. That lag is almost exactly the length of the sleep, so the asyncio loop itself was blocked and the
   sibling branch's in-flight LLM request was starved with it. Root cause:
   `FunctionTool._invoke_callable` (`data/src/google_adk/google/adk/tools/function_tool.py:223-238`) calls
   sync tool functions directly on the event loop, with no thread pool. **Every swegemma tool `swe_coder`
   uses is that kind of plain sync function** (e.g. `run_command` is a `def`, not `async def`, at
   `data/src/swegemma/swegemma/tools/execution.py:20-21`). Real `pytest`/shell calls run for seconds to tens of
   seconds, far longer than the probe's 1 s stand-in.
4. *Not tested:* EXP-007 H2 (sync `FunctionTool` vs `AgentTool` multi-call dispatch within one turn) was
   deliberately not run. It has low relevance here: 0 of 3,278 E0 tool-call steps carry more than one function
   call. EXP-007 H4 (is `RunConfig.max_llm_calls` shared across branches or per branch?) is
   **inconclusive**. The `max_llm_calls=1` arm errored, but both hypotheses predict that failure; a
   `max_llm_calls=2` arm would separate them. Neither result gates this track.

**Decision (EXP-007's pre-registered rule, now resolved): H1 PASS + H3 cost significant → do NOT build
EXP-008 yet.** EXP-008 is the already-named candidate from EXP-007's follow-ups:
`SequentialAgent[ParallelAgent[analyzer_A, analyzer_B], swe_coder]` vs E0 on dev-48. If it were built on
today's sync tools, event-loop stalls on real tasks would likely eat most of the measured concurrency
benefit. Per the rule, the next step is to make swegemma's sync tools async (or otherwise stop them blocking
the loop) first, and only then attempt a real parallel-agent architecture.

**The prerequisite is unscoped and not in any backlog. Two open questions must be answered before it can
be scoped:**
- *Can a submission reach it at all?* The tools live in the host-side swegemma package, resolved through the
  closed host `ToolRegistry`. Submissions are declarative-only (§1.3: no Python entry point, no custom tools;
  §6.0.3 found the same closed-registry limit for tool descriptions). So "wrap `run_command` et al. in
  `asyncio.to_thread`" (EXP-007 follow-up 2) may not be a change we can ship. It may only be reachable as an
  upstream swegemma/adk change, which is outside our control. Confirm this against `HARNESS_README.md` and
  the `adk_submission` registry source before treating it as buildable.
- *Does the H3 stall actually hit EXP-008's shape?* In
  `SequentialAgent[ParallelAgent[A, B], swe_coder]`, the long `run_command`/`pytest` calls belong to
  `swe_coder`, which runs alone after the parallel stage, so they have no sibling to stall. The stall matters
  only for whatever the *analyzer* branches call. If those branches use only read-only tools, as in the
  harness's reference `code_analyzer` (`read_file` + graph tools, no `run_command`; §6.0.3), the
  multi-second blocking calls H3 models may never happen inside the parallel stage. Those read-only tools are
  still sync, though, and their real per-call latency is unmeasured. **A free first check (no GPU):** pull the
  per-call latency distribution of `read_file`/graph-tool calls from E0's existing traces (per-step
  `elapsed_s`, see §10.1). If those calls are consistently short compared with an LLM call, the prerequisite
  may shrink to "restrict analyzer tools" rather than "async-ize swegemma". That would refine the
  pre-registered decision, not reverse it, and would still need confirmation by re-running EXP-007's
  sync-block arm with the real tools.

**What else must hold before EXP-008 is worth GPU time (beyond the prerequisite):**
- *Where the analyzers point.* EXP-008's front end is a LOCATE-style analyzer stage. §6.1's 2026-10-19
  correction (EXP-003b decision) found from real E0 dev-48 traces that the bottleneck is **post-LOCATE**
  (wall-clock-bound touch→edit→resolved drop-off), not LOCATE quality. Parallel analyzers make a LOCATE stage
  *cheaper in wall time* than sequential analyzers would. Compared with E0, though, that stage is still
  *extra* wall time, plus a handoff, and it carries the coordination-cost risks §6.0.3 lists (MAST
  arXiv 2503.13657). EXP-008's design should say which measured E0 failure it targets before it is run.
- *Branch safety.* Only read-only branches are candidates. All agents share one `/workspace` and
  `submit_patch` diffs the whole workspace, so parallel *coding* branches were ruled out before EXP-007 was
  designed.
- *Scope of the evidence so far.* The evidence covers N=2 and 31B only, with synthetic agents making one tool
  call each. Nothing yet speaks to resolve rate, LB score, or the 12 h budget. Adoption would follow the usual
  §5.5 rule (dev-48 Δ ≥ +3 tasks with no regression in wall/process metrics), plus the estimator's worst-case
  ≤ 11.0 h gate (§4.4).
- *Budget accounting.* Resolve H4 (`max_llm_calls=2` arm, CPU-only Stage 0 is enough) only if EXP-008's
  budget design turns out to depend on whether branches share one budget.
- *The idle capacity buys throughput, not latency -- added 2026-10-21 (EXP-009).* EXP-006's 88.6% idle KV at
  31B is **not** a lever on any bottleneck EXP-009 actually found. The binding costs are sequential *within*
  one agent turn: 46.2% of E0's wall-clock goes to reading and searching, and a further **27.3% to
  generating scratch repro scripts token-by-token** (53.4 min, the largest single line item; corrected
  2026-10-21 -- see EXP-009 Part C1, which withdraws an earlier "73.7% reading" figure), and the tasks that
  score nothing are **not** short of turns -- they spend
  38 turns, as many as the winners, and simply never commit to an edit. Running more requests in parallel
  cannot shorten a turn that is blocked on its own tool call, so this track can do nothing for the
  empty-patch rate or the first-edit turn. It pays off **only** for the best-of-N variant parked below, where
  the spare capacity runs N whole independent attempts instead of speeding one up. Recorded here so the idea
  is not re-derived later as a latency fix.

**Exit criteria, in order:** (1) the two open questions above are answered and the prerequisite is scoped
as a concrete change; (2) EXP-007's `parallel-sync-block` arm, re-run with the real tools the analyzer
branches would use, meets the original H3 bar (`h3_projected_stall_frac ≤ 0.10`, `max_lag_s` near the
~0.001–0.002 s baseline) on real 31B; (3) only then does EXP-008 enter §6.1, as a smoke-8 screen before any
dev-48 spend. GPU spent on this track to date: ~35 min L4×4 (EXP-006 22.6 min + EXP-007 12.8 min).

**Candidate variant, flagged 2026-10-20, not yet scoped — revisit later:** EXP-008 as named uses
`ParallelAgent` branches with *different roles* (analyzer_A/analyzer_B feeding `swe_coder`), which inherits
both the H3 sync-tool-stall risk above and the multi-role handoff/coordination-cost risk §6.0.3 flags
(MAST arXiv 2503.13657). A simpler variant that reuses the same proven concurrency mechanism (EXP-007 H1)
without either risk: run **N identical copies of the single `swe_coder` agent concurrently on the same
task** (self-consistency / best-of-N), rather than splitting work across differently-purposed sub-agents.
Each copy's own tool calls only stall itself, not a differently-purposed sibling, so H3 matters less here
than for EXP-008's analyzer split. The open problem this variant has instead: **no selection mechanism**.
We don't have `test_patch` at inference time, so "pick the best of N patches" needs a cheap proxy (e.g.
majority-vote on touched file/function, or preferring whichever candidate's own repro script passed) —
not designed yet. Not scoped as an experiment; parking here so it isn't lost before someone picks it up.

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
  the single-agent-vs-multi-agent finding (§4.1: same-model delegation hurt 12/18→6/18, `[M]`/secondhand, never
  run in this project — see §6.0.3's 2026-10-18 citation correction) — here the hypothesis is
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
| W2 | Oct 20–26 | **E0 dev-48 baseline first (added 2026-10-17, see §6.0)**, then E-STOP(a') (structured-LOCATE pipeline, revised 2026-10-17 — see §6.1); E3, E6 (A); E1, E2 (B) if E-STOP(a') doesn't already resolve the phase_reached problem; baseline variance (2 seeds); paper outline (B); LoRA canary (C); daily LB submissions once E0 lands | **G-LoRA (Oct 25)** go/no-go (unchanged criteria, see §6.2 note); **G2 (Oct 26)**: held-out-24 on current best |
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
| LB noise misleads decisions | **Confirmed and quantified (2026-10-21, EXP-009)** | Med | **Measured, not assumed**: the same-config repeat submission was finally run (#1 vs #3) and moved +3 tasks (0.06 -> 0.12) on a config change that was expected to *cost* 0.4 -- Fisher p = 0.53, and identical runs reproduce a 3-task gap 42% of the time. Public-LB MDE is **~4 tasks (~0.07)**, not 0.035. dev-48 solved-set concordance between runs is only 42.9%, so marginal rates are inadmissible without the paired McNemar table. Mitigation now: process metrics (empty-patch rate, first-edit turn) as primary outcomes, `tools/run_forensics.py compare` on every A/B, and the LB slot demoted to a budget-and-transfer check. See 5.5 and `experiments/EXP-009-lb-variance-and-trace-forensics.md` |
| Auto-discovered-but-unattached skills: `adk_submission/discovery.py:598` `rglob("SKILL.md")` scans the **whole** submission tree and registers every skill it finds, but `resolvers/tools.py:150` (`if not config.skills: return None`) attaches none of them unless `agent.yaml` declares a `skills:` key -- discovery is not attachment | **Confirmed (2026-10-21, EXP-009 Part A2)** | Med (silent no-op today, silent wrong-skill attachment later) | Currently double-harmless but actively misleading: the `skills/edit-anchoring/SKILL.md` added before submission #3 **never reached the zip at all** (`tools/pack_submission.py` ships only the 4-file closure reachable from `agent.yaml`; verified against `dist/exp005_e0_4min_safe.zip`) and would not have attached even if it had. It was still briefly mistaken for a live change while diagnosing the 0.12 score. The trap fires the day we add a `skills:` key -- `resolve_skills` matches on directory basename (with `_` -> `-` normalisation), not on path, so every stray `SKILL.md` anywhere under `submission/` becomes eligible at once. Mitigation: before adding a `skills:` key, run `find submission -name SKILL.md` and delete or move every one not intended to load; and never log a skill as a shipped change without checking `agent.yaml` for the key |
| Undeclared tool / malformed calls crash tasks | Med | Med | Strict arg rules, declared-tool whitelist in validator, no shell-like tool examples |
| Graph files 0 bytes / async gaps | Med | Low | Graph tools demoted or off (E5) |
| L4×4 quota too small | Med | Med | smoke-8 screening, replay pre-screen, chunked sessions; record quota in W1 |
| Entry/merger deadline is Nov 2 not Nov 25 | Unknown [M] | Critical | Verify by Oct 20; form team early regardless |
| Harness/wheelhouse version changes mid-competition | Med | Med | Pin versions in notebook; rerun gold control + smoke-8 on each change |
| Subprocess sandbox (the only backend Kaggle supports — no Docker daemon, no Bubblewrap, no user namespaces, confirmed independently by discussion/749743) silently skips `install_editable_package`/`install_test_dependencies`, so per-task test deps (inline_snapshot, dirty_equals, pytest-httpbin, ...) may be missing in **both** our gold-control measurements and the real scorer | Med–High (unconfirmed) | High (undercounts true resolve rate; agent may lose points on tasks whose gold patch would pass if the dep were present) | Vendored-shim fix for inline_snapshot/dirty_equals now wired directly into `submission/prompts/swe_coder.md` (agent creates the shim itself, not just our measurement tooling); requests/httpx import-shadowing and rich/Pygments drift remain unfixed (too deep to shim safely). **Recheck discussion/749439 and /749743 periodically** — an organizer answer confirming/denying that scoring differs from the starter notebook changes how much weight to put on gold-control numbers |
| Kaggle's default notebook image has drifted past the wheelhouse's build target (cp312/torch 2.10) to cp313/torch 2.11 (discussion/749505); a fresh kernel created today would silently pin to the wrong image even with `docker_image_pinning_type: original`, since that only freezes whatever image exists *at first push* | **Confirmed (2026-10-16), fix confirmed (2026-10-16)** | Critical (notebook/submission fails to install at all, like discussion/749505) | **Reproduced on a brand-new kernel** (`rainm4/gemma4-exp001-shim-check`, first push): landed on Python 3.13 despite `docker_image_pinning_type: original`; 9/41 wheelhouse wheels (cp312-only: msgspec, outlines_core, xgrammar, pybase64, setproctitle, ...) failed to install, then the image's own `vllm==0.19.1` crashed on startup (`ImportError: vllm/_C.abi3.so: undefined symbol _ZN3c1013MessageLoggerC1EPKciib`, a torch/CUDA ABI mismatch) — confirms "original" pinning does nothing for a kernel with no prior push to pin to. **Fix verified**: forking the organizers' Getting Started kernel directly (`notebooks/exp002_fork_shim_check`, carries the real pinned `docker_image: gcr.io/kaggle-private-byod/python@sha256:37c64f7...` field from fork lineage, a stronger guarantee than `docker_image_pinning_type: original`) installed all 41/41 wheelhouse wheels cleanly and started the vLLM server with no ABI error. **Action before any real submission push: push from a fork of the Getting Started kernel, never a fresh kernel id.** **Regression caught 2026-10-17**: E0's own `notebooks/E0/kernel-metadata.json` and the generator template `notebooks/kernel-metadata.json` (filled by `tools/build_notebook.py`) still had `docker_image_pinning_type: original` instead of the pinned `docker_image` sha — E0 v1 hit the identical `ImportError: vllm/_C.abi3.so: undefined symbol` crash with 0 tasks run. Fixed in both files (explicit `docker_image` field copied from the working exp002–008 configs); E0 v2 repushed and confirmed past server startup. The explicit `docker_image` field works even without going through Kaggle's UI fork action — it is a first-class pinning field, not solely a side effect of forking. |
| `total_cached_tokens: 0` in every step of all 3 exp002 traces | **Investigated (2026-10-16), likely a reporting gap, not a perf bug** | Low (demoted after per-step timing analysis) | Per-step `elapsed_s` deltas (not just token sums) were checked directly against each step's own `prompt_tokens` (5-15k per call, reset periodically by `EventsCompactionConfig(compaction_interval=15)`): no quadratic blowup pattern — step latency (2-28s) tracks how much new content that turn read/wrote, not cumulative context size. `google.adk.agents.context_cache_config.ContextCacheConfig` is a Vertex AI/Gemini **explicit-caching** feature (`cachedContents` API) per `adk.dev/context/caching` — it has no defined meaning against a local vLLM OpenAI-compatible endpoint, so `total_cached_tokens: 0` most likely just means ADK's cache-usage field isn't wired up for this backend, not that caching (vLLM's own automatic prefix caching, on by default in vLLM's V1 engine) is broken. Not worth further investigation unless a future run shows genuine quadratic slowdown |
| Real agent runs with `RUN_AGENT=True` (`exp002_fork_shim_check`, 3 known-affected tasks, 4.5 min/task budget) all hit the wall-clock cap in LOCATE/REPRODUCE before ever running pytest on the real test file — the vendored inline_snapshot/dirty_equals shim in `swe_coder.md` had still never been exercised against a real `ModuleNotFoundError` on Kaggle | **Shim exercised, found buggy, fixed and re-validated (2026-10-16)** | Closed (was High) | Followed up with `exp003_fork_shim_easy` (3 tasks picked by smallest reference-patch size as an easier-task proxy: `fastapi_14361`, `fastapi_14360`, `fastapi_14303`). Mixed result, not a clean win: `fastapi_14361` reached VERIFY cleanly inside budget (19 tool calls) — hit `ModuleNotFoundError: No module named 'inline_snapshot'`, vendored the shim exactly per `swe_coder.md`, reran both affected test files (10/10 and 37/37 passed), called `submit_patch` once correctly (1176 chars, 2 files) — **then ran `rm -rf inline_snapshot` and called `submit_patch` again (512 chars, 1 file), stripping the shim from its own final patch.** Its own step-25 reasoning (trace `results/traces/trace_fastapi_14361.json`) shows it explicitly weighing the Hard-rules scratch-file cleanup instruction against the Known-sandbox-gaps "this is not cheating" wording and resolving the ambiguity the wrong way — a real prompt-wording gap, not a one-off fluke. The other two tasks never reached a point where this could even fire: `fastapi_14303` spent its whole 45-call budget on a different, unrelated bug (multidict query-param handling in `fastapi/dependencies/utils.py`) and never ran the `dirty_equals`-importing test file before being force-submitted at the call cap; `fastapi_14360` (same code area) fully timed out (274s) still in LOCATE/REPRODUCE with patch_chars=0. So reference-patch length was a weak/partial proxy for reachability — 1 of 3 "easier" tasks actually completed a clean VERIFY cycle, the other 2 still didn't reach a test run at all. **Fix applied**: `submission/prompts/swe_coder.md` now has an explicit carve-out in the Hard-rules scratch-file line ("a vendored package from Known sandbox gaps below is not a scratch file... never delete it") and an explicit instruction at the end of the Known-sandbox-gaps paragraph to keep the vendored file in the final patch. **Re-validated (2026-10-16)**: re-ran `fastapi_14361` alone (`notebooks/exp004_shim_fix_check`, same kernel version 3) against the patched prompt — agent vendored the shim, verified tests, called `submit_patch` exactly once (1176 chars, 2 files), no deletion, explicitly reasoning "The files changed are `fastapi/_compat/v2.py` and `inline_snapshot/__init__.py`. This is correct." Kernel log: `resolved=True, exit_code=0, patch_chars=1175` — same task that failed grading under the unpatched prompt now passes. **Scaled check (2026-10-17, `exp005_shim_fix_batch20`)**: batched the remaining 20 of the 25 known-affected tasks in one kernel session (version 4). Only 1/20 resolved overall, but the real finding is reachability, not the shim: only 2 of 20 tasks ever hit the `inline_snapshot`/`dirty_equals` `ModuleNotFoundError` at all — the other 18 never got that far in LOCATE/REPRODUCE within the 4.5 min/45-call budget, the same constraint identified in exp002/exp003, now confirmed at 10x the sample size. Of the 2 that did reach it: `fastapi_14485` vendored both shims, verified via pytest, then got forced-submitted at the 45-call cap with the shim files still intact — `resolved=True`; `fastapi_14356` also vendored the shim correctly (never deleted) but failed on a genuinely incorrect real-code fix for an unrelated bug (`request_params_to_args` multidict handling) — unrelated to the shim mechanism. **Conclusion: the shim-deletion bug is fixed and 2-for-2 clean in this batch (no deletions, no regressions); it is just rarely the limiting factor — step-budget in LOCATE/REPRODUCE is the dominant open problem across the known-affected cohort.** |
| Data leakage into public repo | Low | High (rule breach) | .gitignore + pre-commit size/path check; release only aggregates |
| `.sh`/banned strings in zip → rejection | Low | Med | Validator whitelist; fake-LLM smoke before each submission |
| Paper reads as generated / unverifiable | Med | Med | Human-written, numbers from our CSVs, release code + seeds |
| **Step budget in LOCATE/REPRODUCE/EDIT, not shim bugs or ledger self-report, is the dominant open failure mode (exp005, confirmed by exp006–008's negative result)** | **High (now the #1 open risk, added 2026-10-17)** | Critical (caps resolve rate regardless of any other fix) | E0 representative baseline + E-STOP(a)/(b) structural forced-transition experiments (§6.0/§6.1), promoted ahead of thinking-budget and compaction tuning; LoRA noted as a fallback training target (§6.2) if prompt-only fixes fail |

### 10.2 Open questions (tracked in §3.4; summary)
LoRA zeroing status (Q4); compile-time tool registry and skill tooling (Q1); exact config schemas (Q2); `thinking_budget` enforcement (Q3); gold-patch failures (Q5); Nov 2 vs Nov 25 (Q6); compaction interval 5 vs 15 (Q7); sandbox setup time (Q8); extension/size limits (Q9); decode/prefill speed and prefix caching (Q10); ~~actual L4×4 quota~~ — **answered 2026-10-17: 30 hrs/week, confirmed from the notebook editor's quota display (not exposed via the CLI).** public↔hidden gap magnitude for *our* configs; ~~whether the `swe_coder.md` scratch-file-vs-vendored-shim wording fix stops the agent from deleting its own vendored shim before `submit_patch`~~ — **answered (Q11, closed 2026-10-16): yes, re-validated on a real kernel run (`exp004_shim_fix_check`), `fastapi_14361` now resolves cleanly.**

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
