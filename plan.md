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

### 6.1 Experiment backlog (one variable at a time; priority order; cost in dev-48 runs ≈ 3–4 GPU-h each)
| ID | Variable | Hypothesis | Measure | Cost |
|---|---|---|---|---|
| E1 | Prompt protocol: phased + ledger vs. flat sample prompt | Phased protocol cuts empty-patch and spin rates by > 50% without hurting resolves | empty %, spin %, resolve | 2 runs |
| E2 | Thinking: off / budget 128 / 256 / 1024 (`thinking_budget` binding per Q3) | Thinking-on reduces malformed (24→2%) and repeats (50→9%) [M] but costs 65–71% of time [M]; a small budget keeps most of the benefit | malformed %, wall, resolve | 4 runs |
| E3 | Thinking-off + strict tool-arg rules | Strict rules alone get malformed ≈ 1.4% [M], freeing time for more calls | malformed %, calls, resolve | 1 run |
| E4 | Temperature 0.2 (scorer default, matches ours) vs 1.0 | Our default already matches the scorer; this now tests whether *raising* T buys exploration diversity at the cost of more spin/malformed | spin %, resolve | 1–2 runs |
| E5 | Graph tools on vs off (prompt-demoted vs declared-and-encouraged vs undeclared) | grep-based localization matches graph tools and avoids 0-byte/async gaps [M] | LOCATE calls, resolve | 2 runs |
| E6 | Budget tuning: calls 35/45/60, time 4/4.5/5 min, timeout 120/150/180 | Resolves saturate around 45 calls; extra time mostly feeds spin | resolve vs wall curve | 3 runs (can reuse traces by truncation analysis first) |
| E7 | Compaction behavior: state-note cadence 0 / 3 / 5 turns; `read_file` range caps | State notes recover post-compaction context; fewer repeated reads | compactions, repeats after compaction, resolve | 2 runs |
| E8 | Skills: `pytest-triage/SKILL.md` and `edit-anchoring/SKILL.md` on vs off | Skills reduce failed edit_file calls | failed edit %, resolve | 1 run (if skills load without `run_skill_script`) |
| E9 | Sub-agent `analyzer` (localization only, via agent_tool) on vs off | Expected negative or neutral [M]; keep only if ≥ +3 tasks | resolve, wall | 1 run |
| E10 | Submit policy: always submit at 80% budget vs only after VERIFY | Early forced submission raises resolve via partial fixes, kills empty patches | empty %, resolve | 1 run |
| E11 | `max_output_tokens` 2048 / 4096 / 6144 / 16384 (official default) | **Premise corrected**: thinking tokens are drawn from this same budget, so a *small* cap is what starves thinking and triggers overflow/nudge chains, not what avoids them — original hypothesis had this backwards. Expect overflow %% to fall, not rise, as the cap grows toward the 16384 default | overflow %, nudges | 1 run |

Order: E1 → E2/E3 → E4 → E6 → E5 → E10 → E7 → E11 → E8 → E9. After each adopted change, re-run the budget estimator. Every ~5 experiments, run held-out-24 to check we are not overfitting dev-48.

Cheap pre-screen without GPU: replay logged decision points under the changed prompt (g4kit-replay idea) and count malformed/spin deltas before spending a dev-48 run.

### 6.2 LoRA / RFT track (gated)
**Gate G-LoRA (Oct 25)** — go only if **all** hold:
1. Canary passes (Q4): adapter trained to shift logprobs on a fixed prompt shows the shift on the scorer stack (patched vLLM, L4 notebook). If deltas are ~0 → adapters are zeroed → **no-go**, redirect effort to prompts + paper.
2. KV-cache check: with the adapter loaded, the harness runs 8 tasks without hangs (LoRA shrinks KV to ~7.6k tokens in some reports [M]); rank ≤ 32, exactly 1 adapter [M].
3. Prompt-only baseline is stable (two consecutive LB submissions without budget/crash failures).

If go:
- **Data**: rejection sampling on dev-48 + public SWE-style trajectories converted to harness tool format (public & free only). Keep only trajectories that resolved **and** had 0 malformed / 0 identical calls; ~200–500 trajectories target. Optionally RFT-style: multiple rollouts per task at T=1.0, keep successes.
- **Training**: TRL/PEFT or Unsloth QLoRA on the bf16 31B; rank 16, alpha 32, target attention+MLP projections, 1–2 epochs, LR 1e-4; compute: Kaggle TPU v5e-8 (~20 h/week) via `notebooks/kaggle_tpu_lora.ipynb`, or a rented 1× 80 GB GPU (Unsloth ~22 GB) — decide by cost at gate time.
- **Adapter verification**: `adapters/<name>/{adapter_config.json, adapter_model.safetensors}`, key names match vLLM expectations (g4kit-check-peft idea), logprob canary again with the real adapter, dev-48 run, size well under 3 GiB.
- Ship only if dev-48 Δ ≥ +4 tasks and held-out-24 does not regress.

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
| W2 | Oct 20–26 | Eval harness notebook + trace analyzer finalized (C); E1, E2 (B); E3, E4 (A); baseline variance (2 seeds); paper outline (B); LoRA canary (C); daily LB submissions | **G-LoRA (Oct 25)** go/no-go; **G2 (Oct 26)**: held-out-24 on current best |
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
| Data leakage into public repo | Low | High (rule breach) | .gitignore + pre-commit size/path check; release only aggregates |
| `.sh`/banned strings in zip → rejection | Low | Med | Validator whitelist; fake-LLM smoke before each submission |
| Paper reads as generated / unverifiable | Med | Med | Human-written, numbers from our CSVs, release code + seeds |

### 10.2 Open questions (tracked in §3.4; summary)
LoRA zeroing status (Q4); compile-time tool registry and skill tooling (Q1); exact config schemas (Q2); `thinking_budget` enforcement (Q3); gold-patch failures (Q5); Nov 2 vs Nov 25 (Q6); compaction interval 5 vs 15 (Q7); sandbox setup time (Q8); extension/size limits (Q9); decode/prefill speed and prefix caching (Q10); actual L4×4 quota; public↔hidden gap magnitude for *our* configs.

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
