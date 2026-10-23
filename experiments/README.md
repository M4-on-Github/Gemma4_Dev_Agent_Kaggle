# Experiments

Index of verification items, experiment logs and LB submissions. Numbers go here, not in chat.
Confidence tags as in plan.md: **[V]** verified against official files/pages, **[M]** community mirror(s),
**[I]** inference. Nothing below has been verified against official files yet (kaggle.com was unreachable
from the build environment); every row starts OPEN.

## 1. Verification checklist (plan §3.4) — status OPEN unless stated

| # | Question | Where to look | Current default in repo | Evidence so far | Status |
|---|---|---|---|---|---|
| Q1 | Exact compile-time tool registry; are `run_skill_script` / `load_skill_resource` real; graph tools present? | `phase0_report.json` from `notebooks/kaggle_eval_l4x4` (greps the installed `swegemma`/`adk_submission` source); `HARNESS_README.md` §6 | 9 tools declared in `submission/agent.yaml`; no skills | **ANSWERED [V] 2026-10-17** — official competition Overview page (`/overview/timeline`, read live, not a mirror) lists the exact predefined-tool signatures: `run_command`, `submit_patch`, `get_status`, `read_file`, `edit_file`, `write_file`, `get_code_neighbors`, `search_similar_code`, `get_code_subgraph` — matches our declared 9 exactly, including argument names (`filepath`, `old_string`/`new_string`, `node`, `query`, `k`, `nodes`). Skill tools (`run_skill_script`/`load_skill_resource`) are separately confirmed real and described (sandboxed, share filesystem with `run_command`, debit the central budget) | **ANSWERED [V]** |
| Q2 | `agent.yaml` / `sampling.yaml` / `eval_config.yaml` schema and field names | `data/raw/sample_submission/*` (diff against `submission/`), `adk_submission` schema source, `swegemma/config.py` | `evaluation: {max_time_minutes, max_tool_calls, max_turns, timeout_seconds}`; plain tool-name list; `agent_tool: {config_path, skip_summarization}`; model `gemma-4-31b-it-qat-w4a16-ct` | HARNESS_README mirror §2 + §7.1 and 4 community repos agree [M]. Open sub-questions: does `timeout_seconds` also cap the grading pytest (one source-reading says yes [M]); is `..` allowed in `!include` (mirrors disagree; we allow it when it stays inside the root) | OPEN |
| Q3 | Does `thinking_budget` bind? | `adk_submission/resolvers/generation.py` (grep in phase0_report); compare `total_completion_tokens` for budget 128 vs 1024 on smoke-8 | `include_thoughts: true`, `thinking_budget: 256`, `max_output_tokens: 4096` | Source reading by one team: only `enable_thinking` on/off is forwarded; budget ignored [M]. HARNESS_README mirror recommends budget 4096 + max_output 16384 (too slow for 4.5 min) | **ANSWERED [V]** — `thinking_budget` IS forwarded |
| Q4 | LoRA zeroing in patched vLLM | Kaggle discussions 743508 / 743213; logprob canary notebook (not built yet) | no adapter shipped | host acknowledged adapters wiped [M] | OPEN — gate G-LoRA Oct 25 |
| Q5 | Which public tasks fail with the gold patch? | EXP-000 full sweep, `runs/EXP-000-all/gold_control.jsonl` (+ `runs/EXP-000-final` rerun) + `gold_failures.txt` | all 18 terminal `instance_id`s excluded (see `gold_failures.txt`) | one report: 107/129 pass [M]; another: 119/129 sound [M] - both conflate distinct mechanisms | **ANSWERED [V]: 111/129 sound (86.0%), 18/129 terminal** (full 129-task sweep, 2026-10-14, after making the pygments pin a curation default). By repo: requests 5/13, rich 42/48, fastapi 63/67, httpx 1/1. All 21 originally-failing tasks individually root-caused into 7 mechanisms (see 1g): 3 were pool-version-ambiguity and are now fixed by default (`pygments==2.20.0` pin); 18 are terminal — inherent skipif pair (1), CPython-3.13-vs-legacy-library drift (2), unobtainable pytest plugin at file granularity (8), harness hardcodes `-p no:anyio` for every task regardless of declaration (3), pygments-pool-exhaustion with no further version to try (4). |
| Q6 | Entry/merger deadline: Nov 2 or Nov 25? | competition Overview > Timeline | plan treats Nov 2 as binding until disproven | **ANSWERED [V] 2026-10-17** — read live from `/overview/timeline`: Start Sep 23; Paper deadline Nov 12 (optional); **Entry Deadline Nov 25**; **Team Merger Deadline Nov 25**; Final Submission Dec 2. All at 23:59 UTC. The Nov 2 rumor is disproven; plan.md §1.2 updated | **ANSWERED [V]** |
| Q7 | Compaction interval 5 vs 15; threshold 14,336 | `HARNESS_README.md` §7.2 vs starter notebook; traces (`compactions` column from `tools/analyze_traces.py`) | notebook parameter `COMPACTION_INTERVAL = 5` | README mirror: interval 5, overlap 2, threshold 14,336, retention 5; starter-notebook mirror used 15 [M] | OPEN |
| Q8 | Sandbox setup time per task | `setup_s` column (task wall minus agent duration) in `task_results.jsonl` | 1.0 min assumed in the estimator and the 11 h gate | host: a run with no patches takes ~10 min total incl. server start, i.e. seconds per task [M]; plan assumed 45–60 s [I] | OPEN |
| Q9 | Allowed extensions / size limit | `swegemma/config.py` (`ALLOWED_SUBMISSION_EXTENSIONS`, `MAX_SUBMISSION_SIZE_BYTES`) | `.yaml .yml .md .txt .py .json .safetensors`; < 3 GiB unpacked; no hidden files, no 0-byte files | README mirror §2.4 and the starter notebook's packaging cell [M] | **ANSWERED [V]** |
| Q10 | Decode speed / per-call overhead / prefix caching | notebook decode probe (`decode_probe` in summary.json); `output_tokens` vs `wall_s` in summary.jsonl | 25.5 tok/s + 0.6 s/call in the estimator | g4kit fit: 25.5 tok/s + 0.6 s (3 arms sharing a server, pessimistic) [M]; one real trace: 10,570 completion tokens in 288.6 s → ≥ 36.6 tok/s effective [M] | OPEN |
| Q11 | Actual weekly L4×4 quota | Kaggle account page after the first run | 30 h/week assumed [I] | — | OPEN |
| Q12 | `write_file` cannot create files outside `/workspace` (paths are rewritten under it) | HARNESS_README §6.2; a trace where the model tried `/tmp/repro.py` with write_file | prompt tells the model to create scratch files with a run_command heredoc in /tmp | starter-notebook mirror note + README mirror [M] | OPEN |
| Q13 | Is `phase_reached` (regex over the agent's self-reported `[phase=...]` ledger line, `tools/analyze_traces.py` `LEDGER_RE`) a trustworthy measure of real phase progress? | EXP-002 smoke-8 raw traces: all 4 agents stop emitting the ledger tag within 1-3 of 19-39 turns, one still tagged `LOCATE` while `edit_file`/`pytest` calls are underway | metric assumed reliable; used for E0's "54% stuck in LOCATE" headline and the §6.1 "done" criteria | **ANSWERED [V] — NO.** It measures how long the model keeps maintaining the bracket convention, not actual phase. E0's headline finding is suspect under the same regex. Needs a harness-side signal (tool-call family/order or `get_status`-derived phase) before it can gate any decision — not yet built | OPEN (fix needed before reusing as a gate) |
| Q14 | Does a prompt-only fixed tool-call sequence (no tool-availability restriction) actually constrain which tools the model calls? | EXP-002 smoke-8: `get_code_neighbors`/`get_code_subgraph` called 0/4 times despite being step 2-3 of the rewritten LOCATE protocol; `search_similar_code` itself called first/second in 3/4 traces (corrected 2026-10-18, see §1o — only rich_3006 skipped it) | implicit assumption behind E-STOP(a')'s prompt-only design | **PARTIALLY ANSWERED, revised 2026-10-18 — original "ANSWERED [V] NO" overstated the evidence.** Step (b) (`search_similar_code`) compliance was real: 3/4 traces called it as instructed, vs. 0/48 in E0. The chain breaking after (b) in all 3 cases that reached it tracks with step (b)'s *output quality* (lexical-fallback junk; a wrong-but-high-similarity exact match; one case where (b) already gave the right answer, making later steps redundant, not ignored) at least as well as it tracks with "the model ignores instructions." `get_code_neighbors`/`get_code_subgraph` genuinely never fired (0/4), so a fixed sequence still isn't reliably enforced end-to-end, but "optional advice the model is free to ignore" is not the demonstrated mechanism — a free CPU-only recall check against the real tools (not the hand-ported scorer) is needed before concluding this one way or the other | OPEN (re-opened; see `experiments/EXP-002-estop-a.md` follow-up 2) |

Phase 0 exit gate (plan §3): Q1, Q2, Q5, Q9 answered; EXP-000 done; `tools/validate_submission.py --official`
passes on `data/raw/sample_submission`. **Status as of 2026-10-17: Q1, Q5, Q6, Q9 answered [V]; Q2 partially
answered [V] (see §1b below), one field-name sub-question still open.** EXP-000 is done (full 129-task sweep,
§1g/§1i).
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
| Baseline run-to-run variance (same config, 2 seeds, dev-48) | **still not run**; upper bound from two *different* configs: solved-set concordance 6/14 = **42.9%**, 8 discordant pairs, McNemar p = 0.73 | `experiments/EXP-009-lb-variance-and-trace-forensics.md` (Part A5) | 2026-10-21 |
| **Public-LB run-to-run variance / minimum detectable effect** | +3 tasks (0.06 -> 0.12) between near-identical bundles; Fisher p = 0.53; identical runs differ by >= 3 tasks 42% of the time. **MDE ~4 tasks (~0.07)** | `experiments/EXP-009-lb-variance-and-trace-forensics.md` (Part A4), `submissions.md` #1 vs #3 | 2026-10-21 |
| Best estimate of our true public rate (pooled #1+#3+#4) | **17/174 = 9.8%** (was 11/116 = 9.5% before #4; not the 12% once assumed). Against the field this is the **25th percentile**, not a neutral baseline -- see the leaderboard rows below | `experiments/EXP-009-lb-variance-and-trace-forensics.md` (Part A4), `experiments/EXP-012-competitive-position.md` | 2026-10-22 |
| Agent wall-clock split, dev-48 (repro-write : read/search : edit : test : other) | E0 **27.3% : 46.2% : 11.7% : 1.5% : 13.3%**; EXP-003 24.4% : 45.2% : 14.1% : 1.0% : 15.3%. Supersedes an earlier "73.7% : 11.7% : 8.5% : 6.1%" split, whose read bucket was 93% heredoc writes (Part C1) | `experiments/EXP-009/forensics-*.txt` | 2026-10-21 |
| Biggest single cost in a run | **writing scratch repro scripts = 27.3%** of all wall-clock (E0: 53.4 min, 248 heredocs, 11.61 s median, 5.2 per task); vs **1.5%** running the repo's own test suite | `experiments/EXP-009/forensics-E0-dev48.txt` | 2026-10-21 |
| Share of wall-clock reading + searching | **46.2%** (E0), 45.2% (EXP-003). Supersedes an earlier "73.7% reading" figure, which was a classifier bug counting `cat > /tmp/repro.py <<EOF` as a read | EXP-009 Part C1 | 2026-10-21 |
| Genuine shell reads vs `read_file` | only **11 of 253** E0 `sed`/`cat`/`head` calls are real reads (31 of 441 pooled); `read_file` 2.74 s vs shell-read 6.57 s median | EXP-009 Part C1 | 2026-10-21 |
| Gold-patch control disagreement across EXP-000 dirs | **13/129 = 10.1%** (upper bound; 5.4% excluding the `probe2` outlier, 4.7% also excluding `negctl`). Mechanism: a harness tar-cache keyed by a constant leaks one task's dependencies into the next (`tools/gold_control.py:32-46`) | EXP-009 Part C3 | 2026-10-21 |
| Same-config agent repeat runs available | **none.** Only 3 dirs under `runs/` have `task_results.jsonl` (E0, EXP-002 smoke-8, EXP-003); all 19 EXP-000 dirs are gold controls. The 42.9% concordance has no same-config baseline beneath it | EXP-009 Part C4 | 2026-10-21 |
| Turns before the first edit, by outcome | resolved **12** tool-bearing turns / 108 s (35% of the call cap); empty-patch **30** turns / 268 s (87%). AUC P(empty > resolved) = 0.93-0.97, holds within each run. **Composition** (grep:read ratio, distinct files) separates nothing | EXP-009 Part C5 | 2026-10-21 |
| Budget exhaustion by outcome | resolved **0/20** hit the session timeout or the tool cap; empty-patch 25/35 timed out and 12/35 hit the cap. So a long prefix is partly *caused* by the budget -- direction is not identified without EXP-010 | EXP-009 Part C5 | 2026-10-21 |
| Reproduce-before-first-edit | **20/20 resolved runs did** (strict test). Only composition metric separating resolved from patch-but-failed (20/20 vs 31/41, AUC 0.622). Do not remove reproduction -- make it cheaper | EXP-009 Part C5 | 2026-10-21 |
| Median first-edit turn, by outcome (E0) | resolved **18**, patch-but-failed **18**, empty-patch **43**; 13/48 tasks never edit at all | `experiments/EXP-009/forensics-E0-dev48.txt` | 2026-10-21 |
| Conversion once any patch exists (E0) | **11/29 = 37.9%** resolved | `experiments/EXP-009/forensics-E0-dev48.txt` | 2026-10-21 |
| **Public-LB field, 3,467 teams** (pulled 2026-10-22) | median team **8 tasks (0.13)**; modal team **10 (0.17)**, 560 teams = the largest single bin; ceiling **14 (0.24)**, 4 teams. Nobody exceeds 14/58 = 24.1%. All 15 distinct scores decode exactly to `k/58` truncated, which **confirms n = 58** rather than assuming it | `experiments/EXP-012-competitive-position.md` §1 | 2026-10-22 |
| **Our standing (#4 = 0.10 = 6/58 = 10.3%)** | **~25th percentile. 2,333 teams (67.3%) strictly ahead**, 863 (24.9%) behind. **The gap to the top is real**: +8 tasks, and against our pooled 17/174 the ceiling's 24.1% gives Fisher p = 0.0125 and falls outside our 95% CI of 6.2-15.1%. **The gap to the median is not established** -- 13.8% is inside that CI (p = 0.4629), so beating the middle of the field is not a measurable goal | `experiments/EXP-012-competitive-position.md` §2 | 2026-10-22 |
| CORRECTION -- the "null model" used throughout EXP-009/EXP-010 | `p ~ 0.0948` was fitted to **our own** submissions, so it measured our own noise and not any baseline. The leaderboard above is the honest reference class. The ~4-task MDE itself is unaffected | `experiments/EXP-012-competitive-position.md` §2 | 2026-10-22 |
| Config behind the public 0.24 notebook vs ours | **same model** (`gemma-4-31b-it-qat-w4a16-ct`), **same 9 tools**, same T 0.2 / top_p 0.95. Differs only in `max_time_minutes` **7 vs 4.0**, `thinking_budget` **4096 vs 256**, `max_output_tokens` 6144 vs 4096, `max_tool_calls` 28 vs 45, `max_turns` 80 vs 70, no `top_k`. Its own changelog shows it ships a 14 h nominal worst case against the 12 h cap | `experiments/EXP-012-competitive-position.md` §3 | 2026-10-22 |
| Effective working time per task | ours **2.91 min** (the 4.0 min cap less the 27.3% spent writing the repro files our prompt mandates) vs the 0.24 config's **~6.9 min** (it **forbids** creating a file: "you may run it once with `python -c`") = **2.4x**. The LB rate ratio is 24.1/10.3 = **2.3x** -- suggestive of the mechanism, not causal evidence | `experiments/EXP-012-competitive-position.md` §3a-3b | 2026-10-22 |
| dev-48 -> public-LB transfer factor | **~0.4x** (dev-48 22.9% vs pooled LB 9.8%). The best of 3,467 teams scores 24.1%, i.e. about our *local* rate, so dev-48 is simply easier than the hidden half -- there is no environment bug to hunt. **A change must be worth ~+10 dev-48 tasks before the public LB can resolve it** | `experiments/EXP-012-competitive-position.md` §4 | 2026-10-22 |
| Weekly GPU quota | | | |
| Max concurrency @ 32k ctx, per model (31B/12B/e4b/e2b) | 8.74 / 19.97 / 45.63 / 67.18 | `experiments/EXP-006-vllm-concurrency-probe.md` | 2026-10-20 |
| Idle KV-cache fraction @ 32k, 1 agent (31B/12B/e4b/e2b) | 88.6% / 95.0% / 97.8% / 98.5% | `experiments/EXP-006-vllm-concurrency-probe.md` | 2026-10-20 |
| Burst speedup @ N=4 (31B/12B/e4b/e2b) | 3.60x / 3.54x / 3.47x / 3.21x | `experiments/EXP-006-vllm-concurrency-probe.md` | 2026-10-20 |

## 3. Experiment index (one row per `EXP-NNN-<slug>.md`)

| ID | Date | Variable | Cohort | Resolve | Empty % | Overflow % | Malformed % | Spin % | Median wall | Proj. 12 h | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EXP-000 | 2026-10-14 | gold control (no model) | all 129 | 111/129 (86.0%) sound | n/a | n/a | n/a | n/a | n/a | n/a | **exclude the 18 terminal failures** from scored cohorts (listed in `gold_failures.txt`). 111/129 is after the default pygments pin; the pre-pin count was 108/129, and the 52/129 Kaggle-subprocess figure is a sandbox artifact (no dependency installation), i.e. a lower bound, not the organizers' ceiling. See `experiments/EXP-000-gold-control.md` (results fields are blank in the doc; the numbers live in this README, sections 1 and 1g) |
| EXP-001 | 2026-10-17 | baseline v1 (phased prompt, thinking 256, T 0.2, 4.5 min/45 calls) | dev-48 | 11/48 (22.9%), Wilson 95% CI 13.3-36.5% | 39.6% | 0.0% | 0.06% | 7.2% | 4.56 min | 8.61 h (worst case 9.00 h) | **submit v1 to LB** (resolve and worst case both cleared the plan 4.6 bar); submitted 2026-10-18, public LB **0.06 = 4/58** (2026-10-19). Partly **corrected 2026-10-21** by EXP-009: the wall-clock-is-binding inference is withdrawn, and the 42.9% cross-config concordance means this run's per-task outcomes are not stable. See `experiments/EXP-001-baseline.md` |
| EXP-002 | 2026-10-18 | E-STOP(a') prompt-only LOCATE rewrite (fixed 4-call sequence, graph-tools-first) | smoke-8 (4/8 sound) | 2/4 (50%) | 25% | — | — | — | 4.55 min | — | reject-pending-recheck: step (b) `search_similar_code` WAS called 3/4 (corrected 2026-10-18, see §1o); `get_code_neighbors`/`get_code_subgraph` still 0/4; likely a recall-quality issue, not compliance — see `experiments/EXP-002-estop-a.md` |
| EXP-003 | 2026-10-19 | **budget-shape bundle, 8 changes vs E0** (confounded): 8 min / 28 calls / 80 turns / 240 s, max_output 8192, thinking_budget 4096, top_k removed, edit-by-call-12 rule | dev-48 (same as E0) | 9/48 (18.75%) as scored; 12/48 (25.0%) after the EXP-004 re-grade | 33.3% | not recorded | not recorded | not recorded | 342.5 s | 11.34 h (worst case not recorded; gate skipped) | **do not adopt** -- flat-to-slightly-worse as scored, and the 45->28 call cut cost `rich_3676`, which stopped at exactly the new cap. EXP-004 lifts it to 12/48, one task above E0, well inside both CIs. Unofficial test zip only (`--skip-budget-gate`), never submitted. EXP-009 adds the key reading: this run nearly doubled the time cap yet took **fewer** turns (s/turn rose to 7.79-12.13), which is evidence against raising max_output_tokens/thinking_budget. See `experiments/EXP-003-public-budget.md` |
| EXP-004 | 2026-10-19 | n/a -- zero-GPU re-grade of the already-collected E0 and EXP-003 patches with `inline_snapshot`/`dirty_equals` shims present (no agent run) | dev-48 (E0 and EXP-003 patches) | E0 11/48 (22.9%), 0 flips; EXP-003 12/48 (25.0%), up from 9/48 | n/a | n/a | n/a | n/a | n/a (0.0 GPU-h) | n/a | **shim artifact confirmed**: exactly 3 EXP-003 tasks flip False->True (`fastapi_14459`, `fastapi_14360`, `fastapi_14297`); E0 unchanged; `rich_3676` remains a genuine loss. The remaining gap is 1 task, inside both Wilson CIs, so the EXP-003 bundle is still not adopted. See `experiments/EXP-004-regrade-shim.md` |
| EXP-005 | 2026-10-20 | **single change vs E0**: `max_time_minutes` 4.5 -> 4.0 (safety-margin tweak, not a new idea) | n/a (no dev-48 run; reasoned from E0's own traces -- 10/11 resolved tasks made their last edit by 227 s, inside the new 240 s cutoff) | n/a locally; **public LB 0.12 = 7/58** (graded 2026-10-21) | n/a | n/a | n/a | n/a | n/a | 10.00 h worst case, gate-clean | **not an improvement -- this is the LB-variance measurement.** 0.06 -> 0.12 (+3 tasks) on a config expected to score the same or ~0.4 tasks *worse* than E0. Fisher exact p = 0.53; pooled true rate 11/116 = 9.5%; two identical runs differ by >=3 tasks 42.4% of the time. Sets the public-LB MDE at ~4 tasks (~0.07), replacing the +/-2 assumed in plan 5.5. No doc of its own -- see `submissions.md` row 3 and `experiments/EXP-009-lb-variance-and-trace-forensics.md` |
| EXP-006 | 2026-10-20 | n/a — vLLM boot-time KV-cache concurrency probe across all 4 allowed model sizes, no task/agent run | n/a (no tasks; 4 model variants) | n/a | n/a | n/a | n/a | n/a | 22.6 min total (all 4 models) | n/a | **adopt (proceed)** — max_concurrency_32k(31B)=8.74≥4, speedup_n4=3.60≥2.0; decision rule says proceed to EXP-007 ParallelAgent probe. See `experiments/EXP-006-vllm-concurrency-probe.md` |
| EXP-007 | 2026-10-20 | n/a — ADK `ParallelAgent` concurrency probe on 31B only (synthetic analyzer_A/analyzer_B agents, fake-relay stage 0 + real-vLLM stage 1), no task/agent run | n/a (no tasks; synthetic 2-branch agent tree) | n/a | n/a | n/a | n/a | n/a | 12.8 min total | n/a | **H1 PASS, H3 significant** — real concurrency confirmed (max_in_flight=2, wall_ratio=0.206) but a sync tool call stalls the sibling branch by ~78% (h3_projected_stall_frac=0.780, max_lag_s=0.961s); proceed to EXP-008 only after making swegemma's sync tools async. See `experiments/EXP-007-adk-parallel-probe.md` |
| EXP-009 | 2026-10-21 | n/a — zero-GPU retrospective analysis (no variable changed): LB-variance test of submissions #1 vs #3 + bundle provenance audit + wall-clock/trace forensics on E0 and EXP-003 | dev-48 (reused E0 + EXP-003 traces) and the 58-task public LB half | n/a (analysis) | n/a | n/a | n/a | n/a | n/a (0.0 GPU-h) | n/a | **H1 rejected, H2 adopted** — the 0.06 -> 0.12 "doubling" is noise (Fisher p = 0.53; identical runs reproduce a 3-task gap 42% of the time); public-LB MDE raised to ~4 tasks (~0.07); primary outcome metrics switched to empty-patch rate and median first-edit turn; paired McNemar now required on every A/B. Key finding: the split between scoring and not scoring is the **turn of the first edit** (18 vs 43), not the time budget. **Part C (added later the same day) corrects this document's wall-clock analysis**: the original "73.7% goes to reading code" was a classifier bug counting `cat > /tmp/repro.py <<EOF` as a read; reading+searching is 46.2% and the largest single line item is **writing scratch repro scripts at 27.3%** against **1.5%** spent running the repo's own test suite. Part C also kills the planned read-path EXP-011, documents a 10.1% gold-control flakiness upper bound traced to a harness tar-cache leak, establishes that **no same-config agent repeat run exists in this repo**, and confirms the first-edit gap (12 vs 30 turns) while showing its direction is unidentified because 25/35 empty-patch runs timed out. See `experiments/EXP-009-lb-variance-and-trace-forensics.md` |
| EXP-012 | 2026-10-22 | n/a -- zero-GPU competitive analysis (no variable changed): full public-leaderboard pull (3,467 teams) plus a read-only comparison of our `submission/` tree against the published 0.22 and 0.24 notebooks | n/a (the 58-task public half, as scored for every team) | n/a (analysis) | n/a | n/a | n/a | n/a | n/a (0.0 GPU-h) | n/a | **change strategy.** Three findings. (1) The score decoder is exact, so n = 58 is confirmed and the field is readable: median 8 tasks, mode 10, **ceiling 14 -- and our 0.10 = 6 tasks is the ~25th percentile, with 67.3% of teams ahead.** (2) **The null model used in EXP-009 and EXP-010 was circular** -- `p ~ 0.095` was fitted to our own submissions. (3) The 0.24 config is public and runs **the same model and the same tool list as ours**, so the whole 8-task gap is budget (`max_time_minutes` 7 vs 4.0, `thinking_budget` 4096 vs 256) and prompt -- it **forbids** writing the repro file our prompt **mandates**, which our own forensics priced at 27.3% of wall-clock. Decision: stop running single-variable experiments 8 tasks below a published baseline; adopt its shape in three sequenced steps, prompt surgery first because it is free and *reduces* timeout risk. Also fixes the dev-48 -> LB transfer factor at ~0.4x. See `experiments/EXP-012-competitive-position.md` |
| EXP-010 | 2026-10-21 | **prompt-only, 1 line**: first-edit tripwire -- `calls >= 25` with `edits=0` forces the next call to be `edit_file` (N=25 chosen from a threshold sweep over E0 + EXP-003 traces) | **none -- submitted straight to the public LB, no dev-48 run (quota)** | **public LB 0.10 = 6/58** (graded 2026-10-22) | not measured (no dev-48 run; 39.6% at E0, target <15%) | n/a | n/a | n/a | n/a (caps unchanged) | **10.00 h** worst case, gate-clean | **uninformative, exactly as pre-registered** -- 6/58 against #3's 7/58 is -1 task, Fisher p = 1.0000, so the tripwire is neither adopted nor rejected. Both readings that *would* have carried information are clean: a score came back (a third confirmation of the 10 h budget path) and it sits far above the <= 0.03 regression threshold, so forcing early edits does not break the agent. A dev-48 run on empty-patch rate + median first-edit turn is still what would decide it -- but that is no longer the next action, because `experiments/EXP-012-competitive-position.md` shows this config sitting at the **25th percentile of 3,467 teams**, 8 tasks below a *published* baseline that runs the same model and the same tools. See `experiments/EXP-010-first-edit-tripwire.md` |
| EXP-016 | 2026-10-22 | n/a -- zero-GPU top-team configuration audit (no variable changed): `submission/` tree vs the published rank-3 team bundles v19 (LB 0.18) and v24 (LB 0.24), plus two new measurements on runs we already have | n/a (the 58-task public half; E0's 96 traces for the context check) | n/a (analysis) | n/a | n/a | n/a | n/a | n/a (0.0 GPU-h) | n/a | **corrects EXP-012 and reverses its central recommendation.** (1) Our standing is **0.12 = 7/58, rank 2322 of 3470, ~33rd percentile** (the LB keeps each team's best submission), and the "LB 0.24" notebook EXP-012 built on belongs to a team at 0.18. (2) The v19 -> v24 diff is `temperature` 0.2 -> 1.0 and nothing else; our sampling already matched theirs except `temperature`. (3) **The section 5.8 gate formula is accurate at our cap**: 38/48 = 79.2% of E0 tasks sit at the cap, projected actual **8.61 h** = 96% of formula; 6.0 min projects to 10.99 h and 7.0 min to 12.57 h, so EXP-015 (adopt their 7-8 min budget) is dead as specified and **~10.5 h projected actual is the real ceiling**. (4) The context trap they document does not reach us (peak 16,991 prompt tokens = 51.9% of the window; zero tasks over the trip threshold). Motivated submission #5. See `experiments/EXP-016-top-team-audit.md` |
| EXP-017 | 2026-10-22 | **4-change bundle (submission #5), deliberately not a single-variable test**: `temperature` 0.2 -> 1.0; drop the 3 graph tools; first-edit deadline call 25 -> 12; REPRODUCE 6 calls + heredoc file -> 2 calls, `python -c` only, skippable. `max_time_minutes`, `max_tool_calls`, `thinking_budget`, `max_output_tokens` untouched | **none -- submitted straight to the public LB, no dev-48 run (quota)** | **0.13 = 8/58** (graded 2026-10-23; readings were pre-registered and are not revised -- see its section 6) | not measured | n/a | n/a | n/a | not measured | **10.00 h** worst case, gate-clean (projected actual unchanged from E0's 8.61 h) | **submitted (ref 57539741) and graded 0.13 = 8/58; the pre-committed 0.17 threshold was NOT crossed, so the bundle is neither adopted nor rejected.** Fisher exact vs our previous 7/58 gives p = 1.0000, and the likelihood ratio between no-effect and the rank-3 team's v19 level is **1.07 : 1** -- essentially zero evidential weight. **Decisive instead: the four scored submissions now read 4, 7, 6, 8 on the identical 58 tasks, and the dispersion test gives X2 = 1.57 on 3 df, p = 0.67 -- observed between-run variance 2.92 against a binomial expectation of 5.58. The spread between four different configs is smaller than noise predicts for four reruns of one, so no variant is distinguishable from any other.** Positives: a score returned (4th confirmation of the ~10 h budget path), and 8 tasks sits far above the pre-registered <= 0.08 regression line, so temperature 1.0, the 6-tool set and the prompt surgery are behaviourally safe -- deleting the repro-file phase EXP-009 priced at 27.3% of wall-clock cost nothing measurable. Bundled because our MDE is ~4 LB tasks and a single-variable test is unresolvable at that MDE, so this is a score attempt, not an experiment. Pre-registered readings are in the doc (blank = Notebook Timeout and would contradict EXP-016 section 3; <= 0.08 = real regression; 0.10-0.15 = inside noise and uninformative; >= 0.17 = +3 tasks or more, matches or beats the rank-3 team's v19). Zip sha256 `edd94341586e60cf7cbd88d6ad59b93eee3cb16a0ea3efb3f650f98b7532d96a` (re-packed after the EXP-018 annotations; the pre-annotation build was `b7b3610ca8c9...` and differs only in YAML comments, no value). Section 1 vendoring-block size corrected by EXP-018. See `experiments/EXP-017-submission5-temp-and-prompt.md` |
| EXP-018 | 2026-10-22 | n/a -- zero-GPU config provenance audit (no variable changed): where `max_time_minutes: 4.0`, `max_tool_calls: 45`, `max_output_tokens: 4096`, `thinking_budget: 256` and the 11,228 B prompt came from | n/a (documents and runs we already have) | n/a (analysis) | n/a | n/a | n/a | n/a | n/a (0.0 GPU-h) | n/a | **no value changed; submission #5 ships unchanged.** All four numbers trace to the single pre-run calculation in `plan.md` section 4.4 (6,900 tokens / 45 calls / 15% margin), which treats a **cap as if it were spent on every call**: 45 x 256 = 11,520 tokens against ~6,900 available, so the caps could never all bind and time won (79.2% of E0 tasks time-capped). Verdicts: `max_tool_calls: 45` justified by accident (median 32, 1/48 at cap; 28 costs resolves); `thinking_budget: 256` partially (4096 is really spent per EXP-003; 512-1024 untested, EXP-014); **`max_output_tokens: 4096` not justified** (premise already retracted in this README; harness default 16384; the 32k wall does not reach us); **`max_time_minutes: 4.0` not justified** (post-timeout flinch, ~2.5 h below the ~10.5 h measured ceiling, self-priced at ~0.4 LB tasks); prompt unknown (~69% is untested insurance against `[M]` failure modes). Also corrects EXP-017: the vendoring block is 3,508 B = 31% of the prompt, not "~6 KB, 55%". The two "not justified" settings are candidates for the next experiment once dev-48 quota exists, not changes to make under time pressure (both raise timeout risk; submission #2 timed out to zero). See `experiments/EXP-018-config-provenance-audit.md` |
| EXP-019 | 2026-10-23 | n/a -- zero-GPU leaderboard-structure analysis (no variable changed, nothing built, nothing submitted): where 8/58 sits in a 3,505-team field, and what the field's shape says about what is reachable | n/a (public LB CSV pulled 2026-10-23T10:45:48; kernel vote counts; per-team SubmissionCount) | n/a (analysis) | n/a | n/a | n/a | n/a | n/a (0.0 GPU-h) | n/a | **retracts my own '0.17 is a fork cluster' claim** -- it was a `round(s*58)` binning artifact that merged 0.17 and 0.18; on exact scores the largest bin is **567 teams (16.2%) at 0.17**, not ~1,000, and the shape is a broad smooth mode (0.15/0.17/0.18 = 14.0%/16.2%/12.4%), not a spike. The submission-count test kills the fork story too (0.17 teams are spread over 1-6 submissions, not piled at 1). **What survives: 0.17 is where modest effort lands and 0.18 is where sustained iteration lands (7-17 submissions), so iteration in this field buys ~1 task.** We are **0.13 = 8/58, 1,686 teams strictly ahead (48.1%), ~52nd percentile = the field median**; +1 task moved us 19 percentile points. Cumulative: >=0.17 is top 34.1%, >=0.20 top 5.6%, >=0.22 top 1.1%, >=0.24 only **4 teams**. **Six resolves separate us from first place.** Open thread: the starter notebook has 1,812 votes (7x the next) but its author never submitted, so the free-baseline score is still unknown and worth a zero-GPU read. Does **not** change EXP-017's reading or the pre-registered next action. See `experiments/EXP-019-field-structure.md` |

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

Rules reminders: never submit a config that has not run on dev-48 with projected worst case ≤ 11 h; **ignore LB
moves < ~0.07 (4 tasks) — measured 2026-10-21, EXP-009; the old 0.035 threshold was an underestimate and a
+3-task move (0.06 → 0.12) turned out to be pure noise**; last submission ≤ Dec 1 23:00 UTC.

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

---

## 1j. Real Kaggle gold-control run (full 129 tasks) diverges sharply from the local sweep — 2026-10-15

The local sweep above (§1g/1i) used our own wheel pool, assembled and then curated by
`tools/curate_wheels.py` before invoking the harness. That curation step — dropping the package under
test from the pool, pinning `pygments==2.20.0`, filtering non-importable ABI tags — is **pure dev
tooling**: it runs before the harness is called, so it has no equivalent during real grading. To find
out what the gold patch actually scores against the organizers' own environment, we ran
`notebooks/exp000/exp000_gold_control.ipynb` for real on Kaggle (kernel `rainm4/gemma4-exp000-gold-control`,
version 7, `N_TASKS=129`, no curation — the notebook's `GoldEvaluator` calls the stock `Evaluator`
directly against whatever `/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse` and the
harness's own `resolve_wheels_dir`/`_deduplicate_wheels` (highest-version-wins, no curation) hand it).

**Result: 52/129 sound (40.3%), 77/129 failing — far below the local curated 111/129 (86.0%).**

**Correction (2026-10-15, later same day): the 52/129 number is not the real ceiling either — it's an
artifact of the sandbox backend, not a measurement of organizer infrastructure.** The notebook passes
`sandbox='subprocess'` to `EvalConfig` (it mirrors the organizers' own Getting-Started recipe, which does
the same, because Kaggle notebooks cannot run a nested Docker daemon — `swegemma/sandbox/docker.py` calls
`docker.from_env()`, which needs a real `/var/run/docker.sock`, unavailable on Kaggle). Both
`install_editable_package` and `install_test_dependencies` in `container_setup.py` no-op immediately
whenever `type(docker).__name__ in {'SubprocessManager', 'SubprocessSandbox'}` (lines 512, 529). So the
Kaggle run never installed a single per-task test dependency — every task was graded against whatever
fastapi/starlette/rich/requests/pygments versions happened to already be sitting in the Kaggle kernel's
base image. 52/129 measures base-image happenstance, not the organizers' actual per-task dependency
resolution.

Checked the other side too: our local curated 111/129 isn't organizer ground truth either. The public
`metric/gemma-4-developer-agent-wheelhouse` Kaggle dataset (41 files) is infra-only (vllm, bitsandbytes,
adk, flashinfer...) — it contains zero fastapi/starlette/rich/requests/inline_snapshot/dirty_equals
wheels. The actual per-task test-dependency wheelhouse the real harness's `install_test_dependencies`
would draw from is a separate, non-public dataset (a Kaggle competitor independently flagged this same
gap — see below, referencing `gemma4swe-wheelhouses`, which they also can't access). Our
`data/local/wheels*` pools were fetched from PyPI by us (`experiments/README.md` §1g), standing in for
infrastructure we can't see.

**Bottom line: the real grading ceiling is unknown and currently unknowable from our side** — it depends
on a private wheelhouse dataset neither we nor (per the forum) other competitors have access to. 52/129 is
a lower bound produced by a sandbox mode that does no dependency installation at all; 111/129 is an upper
bound produced by our own best-effort PyPI substitute. Treat both as bracketing estimates, not as "the"
number, until organizers answer whether real scoring infrastructure resolves per-task test dependencies
properly (which their own harness code is clearly built to do, via `install_test_dependencies`, so there
is no structural reason to expect it to fail at a ~60% rate the way our forced-subprocess Kaggle run did).

Breaking down all 77 failures by cause (`runs/EXP-000-push6/runs/EXP-000-gold-control/gold_control.jsonl`):

| Cause | Count | Notes |
|---|---|---|
| `starlette.routing.Router.__init__()` rejects `on_startup`/`on_shutdown` kwarg | 21 | pool's starlette is too new for the fastapi commit under test; a version-pin class, same family as local class B/C'. |
| `ModuleNotFoundError: inline_snapshot` | 20 | package is simply **absent** from the pool entirely — not a version conflict, a missing wheel. |
| `ModuleNotFoundError: dirty_equals` | 5 | same: wheel never shipped in the pool. |
| `requests` (pytest-httpbin, whole-file grading) | 10 | matches local class D exactly (8 known + `requests_6644`, `requests_7205` newly seen at full scale). |
| `rich` (pygments pool: ANSI/markdown rendering) | 9 | matches local classes A/C/G plus the 3 tasks (`rich_4070/4079/3782`) our local pygments pin fixes — unpinned here since no curation runs. |
| `httpx_3672` | 1 | the exact package-under-test-gets-shadowed-by-a-wheel bug `curate_wheels.py`'s "drop the package under test" step exists to fix. |
| other fastapi (mixed, multiple collection errors) | 11 | same three fastapi causes above, compounding within one task. |

The harness-level mechanics (`install_test_dependencies` → organizer's own pre-baked `/sandbox/setup.py`;
`agent_runner.py:375`'s system prompt telling the model the environment is offline with no PyPI access)
still stand and still mean a submission has no way to influence *which* wheels populate the sandbox at
grading time — that part is genuinely 100% organizer infrastructure. What changed is the conclusion drawn
from it: that fact doesn't tell us the per-task installs *fail* at grading time, only that an agent can't
fix a bad install by `pip install`-ing at runtime. Whether the installs succeed in real grading is exactly
the open question above.

**Forum corroboration (not yet answered by organizers):** a competitor independently hit the identical
five failure categories on a 12-task sample using the same subprocess-sandbox starter-notebook path
(`discussion/749439`, "baharak Al", posted 2026-10-14) — missing `inline_snapshot`, missing
`pytest-httpbin`, requests/httpx package-shadowing, rich/pygments version drift — and asked organizers
directly: *"Does the actual competition scoring use the same environment as the starter notebook?"* and
*"I also noticed a reference to `gemma4swe-wheelhouses` but I can't access. Is that dataset supposed to be
available to participants?"* Zero organizer replies as of this writing. A second thread
(`discussion/748323`, "kimdonggyu1255") shows organizers do actively rebuild/fix the `swegemma` harness
package and wheelhouse in response to forum reports, so this is a live, trackable channel if we want
official clarification later — not posted yet per standing instruction (no public posting without
explicit go-ahead).

**What IS fixable from the submission side, verified empirically:** `inline_snapshot` and `dirty_equals`
are simply absent from whatever pool is in play — not a version conflict, a missing wheel — and the
harness's own protected-path filter
(`swegemma/harness/verification.py:_is_protected_test_or_config_path`) strips patch edits to
`conftest.py`/`pytest.ini`/`pyproject.toml`/`tox.ini`/`setup.cfg`/`.pth`/`sitecustomize.py` but does
**not** touch a plain new top-level package directory. fastapi's test tree has no root `conftest.py` and
`tests/__init__.py` exists, so pytest's default "prepend" import mode walks up past `tests/` to the repo
root and inserts the repo root onto `sys.path[0]` — meaning a new `inline_snapshot/` or `dirty_equals/`
package dropped at the repo root by the agent's own patch is importable, survives the patch filter, and
needs no wheel at all.

Verified by extracting two real task snapshots (`fastapi_11355`, `fastapi_12942`) and running pytest
directly: baseline reproduces `ModuleNotFoundError: inline_snapshot` / `dirty_equals` exactly as seen on
Kaggle; after dropping in two small stub packages implementing the real, narrow public API fastapi's tests
actually call (`inline_snapshot.snapshot`/`Snapshot` — a transparent equality wrapper; `dirty_equals.IsDict`
/ `IsPartialDict` / `IsOneOf` / `HasRepr`, all supporting `|` for alternation, matching the real library's
semantics, not a trivially-always-pass stub), all affected test files pass (41/41 and 2/2 in the files
tried). This recovers 25/77 (32%) of the Kaggle-run failures and is a genuine, generalizable technique —
not test-cheating, since nothing in the harness prohibits adding new files, and the stubs faithfully
reimplement real equality/comparison semantics rather than forcing a pass.

The starlette version mismatch (21), requests/httpx package-shadowing (11), and rich/pygments render-drift
(9) categories remain **not** fixable this way: starlette and rich are too large/behaviorally deep to
faithfully reimplement as a stub, and the shadowing bug is about wheel-resolution order inside the sandbox
(outside repo control) rather than a missing import.

**Practical upshot:**
1. For our own cohort construction, don't treat either the local-curated 18-item list (§1g) or the
   Kaggle-run 77-item list (`gold_failures.txt`) as ground truth — both are proxies bracketing an unknown
   real number. Pending organizer clarification, prefer excluding the intersection of mechanisms we're
   confident are structural (starlette/rich/shadowing — 41 tasks net of overlap) rather than the full
   77, since 25 of those are our own fixable-stub-recoverable gap, not a real environment limit.
2. Don't recalibrate the leaderboard ceiling to ~40% — that number came from a sandbox mode that does no
   dependency installation at all and should not be treated as representative of anything except "what
   happens if nothing gets installed."
3. The `inline_snapshot`/`dirty_equals` vendoring technique is a real, actionable idea for the agent's own
   patch-generation behavior (teach it: on `ModuleNotFoundError` for a narrow test-only dependency, vendor
   a minimal faithful reimplementation as a new top-level package rather than giving up) — not yet wired
   into the submission's prompting/behavior; that's a separate decision from this research finding.

## 1k. `RUN_AGENT=True` real-harness test (exp001/exp002) — 2026-10-16

§1j's vendoring technique (point 3 above) was since wired into `submission/prompts/swe_coder.md`'s "Known
sandbox gaps" section. Validating it requires `RUN_AGENT=True` against the real agent harness — a
gold-control sweep (`RUN_AGENT=False`) never invokes the agent or the submission prompt at all, so it
cannot test this. Also fixed two real packaging bugs found while preparing the test push: `swe_coder.md`
said "do not try to pip install", tripping `tools/submission_rules.py`'s `FORBIDDEN_TEXT_PATTERNS` ban on
the literal phrase (reworded to "vendor the fix yourself, never fetch or install it"); and three vendored
`dirty_equals` `__repr__` methods used f-strings with literal `{...}` braces, which collide with ADK's
instruction-template placeholder scan (rewritten as plain string concatenation). Both would have silently
broken packing or produced confusing warnings had a real submission push hit them first.

**exp001 (`rainm4/gemma4-exp001-shim-check`, fresh kernel id, 3 target tasks: `fastapi_11355`,
`fastapi_12942`, `fastapi_13920`): failed outright**, before the agent ever ran. Landed on Python 3.13
despite `docker_image_pinning_type: original`; 9/41 wheelhouse wheels (cp312-only) failed to install, then
the image's own `vllm==0.19.1` crashed on startup with `ImportError: vllm/_C.abi3.so: undefined symbol
_ZN3c1013MessageLoggerC1EPKciib` (a torch/CUDA ABI mismatch). This independently confirms discussion/749505:
`docker_image_pinning_type: original` does nothing for a kernel with no prior push history — it pins to
whatever image resolves *right now*, not to the wheelhouse's cp312 build target.

**exp002 (`notebooks/exp002_fork_shim_check`, pushed as a new version onto a real user-performed fork of
the organizers' Getting Started kernel, same 3 target tasks): environment fixed, test goal still not
reached.**
- All 41/41 wheelhouse wheels installed cleanly (`"Wheelhouse installation complete."`); vLLM server
  started with no ABI error (`vLLM server started on http://127.0.0.1:8000/v1 (tp=4)`). **Forking the real
  kernel — which carries forward an explicit `docker_image: gcr.io/kaggle-private-byod/python@sha256:...`
  field, a stronger guarantee than `docker_image_pinning_type: original` — is the confirmed fix** for the
  image-drift risk. Never push a real submission from a fresh kernel id; always fork first.
- But the actual thing this experiment was built to test — does the vendored inline_snapshot/dirty_equals
  shim fire and recover a passing patch — **was never exercised**. All 3 tasks: `resolved=False`, durations
  279.2s / 273.6s / 274.1s, each stopped almost exactly at the `max_time_minutes: 4.5` wall-clock cap
  (`submission/eval_config.yaml`), not the 45-call tool budget (only 25-39/45 calls used). Per the full
  traces (`results/traces/trace_fastapi_*.json`, downloaded via `kaggle kernels output`), all 3 agents spent
  the entire budget stuck in LOCATE/REPRODUCE on genuinely hard FastAPI typing-annotation bugs, never
  collected pytest against the real test file, never saw the `ModuleNotFoundError` for
  `inline_snapshot`/`dirty_equals`, and never called `submit_patch`. Only `fastapi_13920` reached
  `edit_file` (5 edits) before being cut off; its final `patch_chars=0` suggests the edits were never
  harvested into a patch before the timeout killed the run.
- **`total_cached_tokens: 0` in every single step of all 3 traces, investigated and downgraded to a
  likely non-issue.** Initial read: zero vLLM prefix-cache hits despite 290k-380k total prompt tokens per
  task looked like a plausible reason all 3 tasks burned the full 4.5 minutes. Closer look at the raw
  per-step data changed that conclusion: each trace step's own `prompt_tokens` (not a running total) stays
  in the 5k-15k range throughout, periodically reset by `EventsCompactionConfig(compaction_interval=15)`;
  cross-checking `elapsed_s` deltas against these per-step token counts shows ordinary 2-28s step latency
  tracking how much new content that turn read or wrote, not a quadratic blowup from reprocessing an
  ever-growing uncached context. Two of the three runs each paid a one-time ~30-38s cost exactly at a
  compaction event (a real but bounded overhead, not a sign of missing caching). Separately,
  `google.adk.agents.context_cache_config.ContextCacheConfig` (set in cell 10 with
  `min_tokens=2048, ttl_seconds=1800, cache_intervals=10`) turns out to be ADK's wrapper around **Vertex
  AI/Gemini's explicit context-caching API** (`cachedContents`, confirmed via `adk.dev/context/caching`
  docs) — a GCP-specific feature with no defined meaning against a local vLLM OpenAI-compatible endpoint.
  `total_cached_tokens: 0` is almost certainly just that field never getting wired up for this backend, not
  evidence that caching (vLLM's own automatic prefix caching, on by default in vLLM's V1 engine) is broken.
  Downgraded in `plan.md` accordingly; not worth further investigation unless a future run shows genuine
  quadratic slowdown.

**Practical upshot:** the image-drift risk is now closed (fork before every real push). The shim-fix
validation is still open, and the real lever is step count, not caching: all 3 tasks needed 39-43 tool
calls to approach VERIFY on genuinely hard FastAPI typing bugs, more than 4.5 min at ~6s/step allows. Next
attempt should either pick an easier/shallower known-affected task (shorter LOCATE phase, so pytest
collection and the `ModuleNotFoundError` are reached well inside budget) or do one throwaway diagnostic
push with a temporarily raised `max_time_minutes` (never the real submission's `eval_config.yaml`) purely
to confirm the shim fires and resolves a task end-to-end.

## 1l. `RUN_AGENT=True` easier-task follow-up (exp003) — 2026-10-16

Followed up on exp002 by forking the same kernel (new version, same `rainm4/getting-started-gemma-4-developer-agent`
kernel id — `notebooks/exp003_fork_shim_easy/`, version 2) and re-targeting `TARGET_IDS` at 3 known-affected
tasks chosen for smallest reference-patch size in `data/raw/tasks.jsonl`, as a cheap proxy for a shallower
LOCATE phase: `fastapi_14361` (462 chars), `fastapi_14360` (518 chars), `fastapi_14303` (629 chars) — all
three fail gold-control with `ModuleNotFoundError: No module named 'dirty_equals'`/`'inline_snapshot'` per
`runs/EXP-000-push6/runs/EXP-000-gold-control/gold_control.jsonl`.

Kernel log per-task summary:
```
fastapi_14361: resolved=False, exit_code=2,  patch_chars=511,  tool_calls=20, duration=142.5s
fastapi_14360: resolved=False, exit_code=-1, patch_chars=0,    tool_calls=23, duration=274.0s
fastapi_14303: resolved=False, exit_code=2,  patch_chars=1427, tool_calls=45, duration=237.2s
```

**The patch-size proxy only partly worked.** Only `fastapi_14361` actually completed a clean, self-paced
VERIFY cycle inside budget (19 tool calls, reached `get_status`/`submit_patch` on its own). The other two
never got there: `fastapi_14303` spent its entire 45-call budget investigating a different, unrelated bug
(multi-value query-param handling in `fastapi/dependencies/utils.py`'s `request_params_to_args`/
`_get_multidict_value`) and never ran the test file that imports `dirty_equals` — its final patch (1432
chars) was force-submitted only because it hit the tool-call cap (`get_status` at step 49 showed
`tool_calls_remaining: 0`), not because it finished. `fastapi_14360` (same code area as 14303) fully timed
out at 274s still inside LOCATE/REPRODUCE, patch_chars=0, never reaching pytest at all — the same failure
mode as all 3 exp002 tasks. Reference-patch length tracks the size of the *real* fix, not how many
exploratory tool calls the LOCATE phase needs, so it's a weak proxy for reachability within the 4.5 min cap.

**`fastapi_14361` is the one real shim-mechanism validation, and it found a genuine bug, not an environment
problem.** Full step trace (`results/traces/trace_fastapi_14361.json`):
- Steps 4-14: correctly located and fixed the real issue (`_remap_definitions_and_field_mappings` in
  `fastapi/_compat/v2.py`, missing a `"$ref" not in schema` guard) — matches the real gold patch exactly.
- Step 16: `pytest -q tests/test_compat.py` fails to collect: `ModuleNotFoundError: No module named
  'inline_snapshot'`.
- Step 17: vendors the shim exactly as `swe_coder.md` instructs — `write_file inline_snapshot/__init__.py`.
- Steps 18-19: reruns both affected test files — 10/10 and 37/37 pass.
- Step 24: `submit_patch` → `{"patch_size": 1176, "files_changed": 2}` — correct, complete patch.
- **Step 25 (thinking, verbatim excerpt):** "Wait, `files_changed: 2`. I also created
  `inline_snapshot/__init__.py`. I should delete it before submitting if it's not supposed to be part of
  the patch. The instructions say: 'If you ever created a scratch file in /workspace, delete it with
  run_command before submitting.' ... Wait, the instructions also say [the Known-sandbox-gaps 'this is not
  cheating' wording] ... Ho[pefully this works out]" — then runs `rm -rf inline_snapshot` anyway.
- Step 26: `submit_patch` again → `{"patch_size": 512, "files_changed": 1}` — the shim is now stripped from
  the final submitted patch, which would almost certainly re-trigger the exact `ModuleNotFoundError` the
  agent had already fixed once the grader reruns `tests/test_compat.py`.

This is a real, reproducible prompt-wording gap, not a one-off: the agent read both rules, noticed the
tension, and the "cleanup" framing won. **Fix applied** to `submission/prompts/swe_coder.md`: the Hard-rules
scratch-file line now has an explicit carve-out ("a vendored package from Known sandbox gaps below is not a
scratch file... never delete it"), and the Known-sandbox-gaps paragraph now ends with an explicit
keep-it-in-the-patch instruction naming `submit_patch` and `files_changed` directly, so the agent doesn't
have to resolve the ambiguity itself. Not yet re-validated on a real kernel run.

**Practical upshot:** the shim logic itself is sound — when an agent actually reaches it, it vendors and
verifies correctly. The bug was entirely in how the prompt framed "do you keep this file," and that's now
fixed in `swe_coder.md`. Separately, the reachability problem from exp002 is only one-third solved: picking
tasks by reference-patch size got one task to a clean VERIFY cycle but left two still timing out or
exhausting budget without ever reaching the shim-triggering test — step count in LOCATE/REPRODUCE, not the
eventual fix size, is still the real constraint. The next useful check is re-running `fastapi_14361` (or a
similarly-reachable task) against the patched prompt to confirm the shim now survives into the final patch.

## 1m. Shim-fix re-validation (exp004) — 2026-10-16

Rebuilt `dist/submission.zip` from the patched `submission/` tree (`tools/pack_submission.py`; new sha256
`33eed6f5d49e2b73f6b488f637ea5c86f2d5d1da5cbf42bd7f819ddb3cd9098c`, confirming the prompt content actually
changed) and pushed a new notebook (`notebooks/exp004_shim_fix_check/`, same forked kernel
`rainm4/getting-started-gemma-4-developer-agent`, version 3) re-targeting only `fastapi_14361` — the one
task from exp003 that reliably reaches VERIFY inside budget and is the task whose agent previously deleted
its own vendored shim.

Result: the agent followed the identical path as exp003 up through vendoring the shim (hit
`ModuleNotFoundError: No module named 'inline_snapshot'` on `tests/test_schema_ref_pydantic_v2.py`, wrote
`inline_snapshot/__init__.py`, reran that file and `tests/test_pydantic_v1_v2_mixed.py` — 2/2 and 26/26
passed) — but this time called `submit_patch` exactly once (`patch_size: 1176, files_changed: 2`), with no
`rm -rf` and no resubmission. Its own trace shows it explicitly reasoning the shim belongs in the patch:
"The files changed are `fastapi/_compat/v2.py` and `inline_snapshot/__init__.py`. This is correct." The
kernel log confirms `resolved=True, exit_code=0, patch_chars=1175, tool_calls=22, duration=194.2s` — the
same task that failed grading under the unpatched prompt (exp003: `resolved=False, exit_code=2,
patch_chars=511`) now passes end to end.

**Conclusion:** the scratch-file-vs-vendored-shim prompt fix is validated on a real kernel run. The shim
mechanism, once an agent reaches it, now survives correctly into the final submitted patch.

## 1n. Scaled shim-fix check across the remaining cohort (exp005) — 2026-10-17

Batched the remaining 20 of the 25 known-affected tasks (the 25-task `inline_snapshot`/`dirty_equals`
cohort from `runs/EXP-000-push6/runs/EXP-000-gold-control/gold_control.jsonl`, minus the 5 already covered
across exp002/exp003/exp004: `fastapi_11355`, `fastapi_12942`, `fastapi_14361`, `fastapi_14360`,
`fastapi_14303`) into a single kernel session (`notebooks/exp005_shim_fix_batch20/`, same forked kernel,
version 4) against the already-validated patched prompt. Setup cost 454.6s; total session wall time
5941.3s (~99 min) for setup + 20 tasks.

**Result: 1/20 resolved.** But the headline number obscures the real finding — of the 20 tasks, only **2**
ever actually reached the `inline_snapshot`/`dirty_equals` `ModuleNotFoundError` at all (checked by
searching every step's observation across all 20 traces for that exact error, and for any `write_file` /
`rm` call touching the shim path):

- `fastapi_14485`: hit the error on `tests/test_annotated.py`, vendored both `inline_snapshot` and
  `dirty_equals` shims, reran pytest to confirm, then ran out of the 45-call budget one step later with no
  explicit `submit_patch` call — the harness's forced-submission-at-cap path (same mechanism seen in
  exp003's `fastapi_14303`) used whatever was in `/workspace`, **shim files included, undeleted**.
  `resolved=True, exit_code=0, patch_chars=3451`.
- `fastapi_14356`: also hit the error (on `tests/test_query.py`), vendored both shims correctly and never
  deleted them, but the agent's actual library fix (a multidict/`ImmutableMultiDict` handling change in
  `fastapi/dependencies/utils.py`'s `request_params_to_args`) was logically wrong — pytest ran and failed on
  a real assertion, not a collection error. `resolved=False, exit_code=1, patch_chars=3426`. This is an
  incorrect-fix case, unrelated to the shim.

The other 18 tasks never wrote a shim file and never saw the `ModuleNotFoundError` in any step — they spent
their full budget (20-45 tool calls, 238-281s each) on LOCATE/REPRODUCE/EDIT for the task's real bug and
either ran out of time, ran out of calls, or finished with an unverified/wrong patch, without ever reaching
the point where the missing test dependency would even matter.

**Conclusion:** the shim-deletion bug (1l/1m) is fixed and clean in this larger sample too — 2/2 tasks that
reached it kept the shim through to submission, including through the forced-submission-at-cap path, with
zero regressions. But it is rarely the limiting factor: 18/20 tasks never got far enough to need it at all.
**The dominant open problem across the known-affected cohort — and most likely across the full hidden set —
is step budget in LOCATE/REPRODUCE/EDIT, not the shim.** Any further investment should target reducing
tool-call/time cost per task (tighter LOCATE heuristics, fewer exploratory reads, earlier pytest checks)
rather than further shim-prompt tuning.

## 1o. EXP-002 trace-level findings + research into delegation vs. alternatives, and a confirmation-bias check — 2026-10-18

EXP-002 (E-STOP(a'), smoke-8) completed and raised two questions beyond its own result (full writeup:
`experiments/EXP-002-estop-a.md`; summary row in §3 above): (1) is `phase_reached` even measuring what we
think it measures, and (2) given the fixed-sequence prompt rewrite demonstrably didn't constrain tool
choice, is a tool-scoped sub-agent (user's "graph only specialised agent" question) actually the right next
move, or just the first idea that came to mind? This section records both the direct trace evidence and the
literature/industry research done to answer the second question without falling into confirmation bias (the
research was explicitly re-run a second time looking for disconfirming evidence and cheaper alternatives,
per direct instruction, after an initial pass had only gathered supporting citations).

**Trace-level findings (Q13/Q14 above).** Reading the 4 raw smoke-8 traces directly, rather than trusting
the aggregate `phase_reached` histogram, surfaced two things the aggregate metric hid: (a) all 4 agents
abandon the self-reported `[phase=...]` ledger tag within 1-3 of 19-39 turns, so `phase_reached` is measuring
ledger-tag persistence, not real phase progress — this calls E0's own "54% stuck in LOCATE" headline into
question, since it was computed with the identical regex; (b) `get_code_neighbors`/`get_code_subgraph` were
called zero times across all 4 traces. Cross-referencing the 4 sound smoke-8 tasks against E0's locally-saved
`task_results.jsonl` for the same task ids showed an identical resolve/fail pattern in both runs (fastapi_14301
and rich_3006 resolved in both; fastapi_14448 and rich_3468 timed out unresolved in both).

**Correction, 2026-10-18, after an independent agent re-read the same 4 traces at the tool-output level (not
just tool-call-name level):** the first-pass claim that `search_similar_code` was "skipped even in the
fastest-resolving task" / that the model "fell straight back into `run_command`-heavy exploration" overstated
the evidence. `search_similar_code` was actually the first call in fastapi_14301 and fastapi_14448 and the
second call in rich_3468 — only rich_3006 skipped it. So step (b) compliance was real: 3/4 vs. 0/48 in E0. The
chain breaking after (b) tracks with what (b) actually *returned*: fastapi_14448's lexical-fallback query
returned junk (similarity 0.22 on an unrelated symbol); rich_3468's exact-symbol query returned the wrong node
at a deceptively high similarity (0.9997); fastapi_14301's query returned the correct answer directly, making
the later graph-tool steps genuinely redundant rather than skipped. This is at least as consistent with "the
model responded rationally to bad-or-sufficient tool output" as with "the model ignores prompt instructions."
The identical E0-vs-EXP-002 resolve/fail pattern still stands as evidence the rewrite didn't change *outcomes*,
but it no longer supports "the prompt rewrite was ignored" as the mechanism — see the revised Q14 row above and
`experiments/EXP-002-estop-a.md`'s corrected results section. Net: the more likely bottleneck is
`search_similar_code` recall/output quality against the real mounted graph+embedding data, untested directly
(the 58-65% recall figure elsewhere in this doc and in `plan.md` §6.0.2 is from a hand-ported scoring script,
not the real harness tool) — a free, CPU-only check of the real tools against real data is the next step,
before either further prompt tuning or EXP-003b.

**Does published research support solving this with a restricted-toolset sub-agent?** Yes, but not
unconditionally. Advisory prompt text asking a model to prefer one declared tool family over another is
widely documented as unreliable once the model already has a more familiar/general tool (`run_command`)
available — the same "grep beats semantic tools" pattern shows up in Claude Code's own production design
(its Explore sub-agent is read-only and tool-scoped, used as the *first-line* exploration mechanism, not a
fallback tried only after softer instructions fail) and in a widely-shared practitioner account of gating
grep with a `PreToolUse` hook rather than an instruction. Published localization architectures — Agentless
(arXiv 2407.01489), AutoCodeRover (arXiv 2404.05427), OrcaLoca (arXiv 2502.00350) — all bound search
*structurally* (no free tool choice, fixed pipeline, or AST-query APIs replacing raw grep), not through
stronger wording. The competition harness's own official reference `sample_submission` already ships exactly
this pattern as its reference design: a graph-only `code_analyzer_agent` sub-agent via `agent_tool`, tools
restricted to `read_file`/`search_similar_code`/`get_code_neighbors`/`get_code_subgraph` only (no
`run_command`, no `edit_file`), on a separate `tool_lora` adapter. API-level forced tool use
(`tool_choice: "required"`) was checked and ruled out as a substitute: it can force "any declared tool" or
one *named* tool, but not "one of this named subset," so it can't recreate restricted-toolset scoping within
a single flat tool list — tool-scoping via a separate sub-agent is the correct generalized mechanism for that,
not an arbitrary choice among equivalent options.

**Confirmation-bias check: what does the counter-evidence say?** Multi-agent-system literature independently
warns that decomposition itself carries a real coordination cost that can erase the benefit of scoping: a
preprint (arXiv 2604.02460) on multi-hop reasoning reports single agents matching or beating multi-agent
decompositions at equal compute; Silo-Bench (arXiv 2603.01045, algorithmic tasks with information distributed
across agents) reports performance loss from coordination failure; Berkeley's MAST taxonomy (arXiv 2503.13657,
confirmed: 1600+ traces across 7 frameworks, 14 failure modes in 3 categories including "system design" issues)
argues most multi-agent failures need structural redesign, not superficial patches — i.e. "add a sub-agent" is
not automatically safe just because the underlying idea (tool-scoping) is sound; the handoff itself is a new
failure surface. **Citation-accuracy correction, 2026-10-18 (independent agent re-check, abstracts only):**
arXiv 2604.02460 is not a Stanford paper, is not about code, and its reported mechanism is unaccounted compute
rather than a communication bottleneck as this doc previously implied; Silo-Bench's "15-49% performance loss"
figure is not stated in its abstract and should be treated as unverified until read in full, and its setup
(information distributed across agents) transfers only loosely to our single-handoff case; MAST's categories
are confirmed but one was previously mislabeled here ("system design," not "specification issues"); the
Arcade/ToolScope/RAG-MCP tool-selection figures cited elsewhere in this doc have not been independently
re-checked either. Treat all of these as directionally-suggestive industry/research texture, not as verified
quantitative support, until re-read in full. **The E9 citation in this doc was also wrong**: "E9, a
same-capability `analyzer` sub-agent regressed 12/18→6/18" was written here and in `plan.md` as if it were our
own completed experiment — `plan.md` tags that number `[M]` (secondhand/community-reported) and confirms E9
itself has never actually been run in this project. The open question EXP-003b must answer empirically is
still whether *tool-scoping* specifically (not delegation in general) avoids a handoff regression — but there
is no in-project negative data point for that yet, only the secondhand number and the general multi-agent-
failure literature above.

**Was there a cheaper alternative worth trying first?** One candidate was proposed and then independently
discarded, 2026-10-18: a contrastive tool-description sentence added to `swe_coder.md` (e.g. "prefer
`search_similar_code` over grep when you have a name"), since `agent.yaml` has no per-tool description-override
field — the real JSON-schema description is fixed by the closed `ToolRegistry`. Two things killed it: (1) the
harness already auto-injects a capability-descriptive "Code Intelligence Tools" blurb into the initial prompt
whenever graph data exists (`HARNESS_README.md` §5.2 item 6), and all 4 EXP-002 traces saw it plus the
explicit forced sequence, so a text-only addition competes with text already there; (2) more decisively, an
independent re-check found the proposed contrastive claim itself false — `search_similar_code` returns dotted
names with no file/line, and the exact query type EXP-002's own step (a) builds routes straight into the
lexical fallback that produced the step-(b) failure cases above, so "prefer it over grep" isn't an honest claim
to put in the prompt. Industry tool-selection literature (Arcade ~10x tool-selection-error reduction; ToolScope
+8.38-38.6pp; RAG-MCP 13.62%→43%) was cited in support of description rewrites generally, but none of those
specific figures were independently re-checked this session — treat them as unverified background texture, not
confirmation. A second, structurally-infeasible-here alternative was checked rather than assumed away:
Agentless-style automatic context injection ahead of the model's first LLM turn. Re-reading
`HARNESS_README.md`'s submission-format description confirms this is ruled out by the competition's own
constraints: submissions are YAML-only through a closed, sandboxed `compile_submission` resolved against
closed host registries — no custom Python entrypoint is permitted, so there is no hook point to inject
retrieved context before the agent's first turn.

**Net effect — revised order, 2026-10-18:** (1) **free CPU-only recall check** (no GPU spend) — call the real
`search_similar_code`/`get_code_neighbors`/`get_code_subgraph` against the actual mounted graph/embedding data
for every sound task, checking recall against the gold-patch function directly (not the hand-ported scoring
script the 58-65% recall numbers elsewhere in this doc and in `plan.md` §6.0.2 came from) — needed before
trusting either a prompt-only LOCATE redesign or a graph-only sub-agent is even premised correctly, since
EXP-002's step-(b) failures look like a recall-quality problem, not a compliance problem; (2) **EXP-003b** —
fix `submission/sub_agents/analyzer.yaml` (strip `run_command`, which it still has unlike the official
`code_analyzer.yaml` reference) and `submission/prompts/analyzer.md` (remove the "graph tools only if two
greps fail" escape hatch, fix the output contract, pass `{problem_description}`/`{hints?}` session state, cap
the analyzer's own call budget) to match and improve on the harness's reference-design sub-agent, wire
`agent_tool: config_path: sub_agents/analyzer.yaml, skip_summarization: true` into `submission/agent.yaml`,
verify with a 1-task dry run that sub-agent events land in the trace, and smoke-8 screen it — instrumented
specifically to check the sub-agent's own report quality/empty-rate and whether its top location is among the
gold-patch files, not just aggregate resolve rate. Both steps need the corrected recall/compliance signal from
(1) first, and EXP-003b's design notes are mirrored in `plan.md` §6.0.3/§6.0.4.

Follow-ups this section raises: fix `tools/analyze_traces.py`'s `phase_reached` instrumentation (Q13) before
trusting it as a gate again; switch future screening runs to a cohort of tasks already known to pass gold
control (8 gradeable data points at the cost of today's smoke-8, which only yields 4).

## 1p. EXP-004: zero-GPU re-grade isolates a shim-gap artifact in EXP-003's measured loss — 2026-10-19

Full writeup: `experiments/EXP-004-regrade-shim.md`. Follow-up to EXP-003-public-budget's dev-48 result
(9/48 resolved vs. E0's 11/48). Re-graded (not re-ran) both runs' own already-captured final patches with
`inline_snapshot`/`dirty_equals` (`tools/compat_shims/*`) present in the sandbox, gated per task on whether
that task's extracted test files import them — zero GPU cost, CPU-only Kaggle kernel
(`rainm4/gemma4-exp004-regrade-shim`), no model/agent loop.

A real bug surfaced and was fixed before trusting any number: v1 of `tools/regrade_patches.py` pre-seeded the
shim files into `/workspace` *before* applying the agent's own patch, so any patch that had itself vendored
the same file (exactly the case under study) failed `git apply` outright (`already exists in working
directory`), producing false `resolved=False` rows. Fixed in v2 by skipping pre-seeding a shim file the
stored patch's own diff already adds (`_patch_adds_file`), rerun on the same kernel id, confirmed zero apply
errors across all 96 regraded rows.

Clean v2 result: **E0 regrade 11/48 (22.9%), exactly matching E0's original scored result with zero flips**
(no E0 task needed the shim that it didn't already have — this doubles as the methodology's own sanity
check). **EXP-003 regrade 12/48 (25.0%), up from EXP-003's original scored 9/48 (18.75%)**, via 3 tasks
flipping False→True (fastapi_14459, fastapi_14360, fastapi_14297) once the sandbox gap stopped consuming the
agent's remaining budget before resubmission. Of EXP-003-public-budget.md's 5 originally-contested "E0 won,
EXP-003 lost" tasks, 4 (fastapi_13207, fastapi_14873, fastapi_13537, rich_3676) hold up as genuine losses —
rich_3676 in particular confirms that doc's own finding that it was cut off at exactly the new 28-call cap —
but fastapi_14297 (previously unexplained: "stopped earlier, at 26, for a different reason not yet
investigated") is now explained as the shim artifact.

Net: EXP-003-public-budget.md's "flat-to-slightly-worse" verdict rested partly on this artifact. Once
equalized, EXP-003's config is a hair *above* E0 (25.0% vs. 22.9%, n=48, well inside overlapping Wilson CIs,
not a basis for adoption) rather than below it. The call-count cut's real, mechanistic cost (rich_3676) still
stands, but the broader "5 lost tasks" framing over-attributed to it; the honest picture after this
correction is closer to parity than the original write-up suggested. Any future budget-shape experiment
should re-grade its own patches with this same shim-equalization step before comparing resolve rates to E0.
