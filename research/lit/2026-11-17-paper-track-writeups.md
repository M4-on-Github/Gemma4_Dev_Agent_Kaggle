---
id: 2026-11-17-paper-track-writeups
title: "Paper-track writeups of the Gemma 4 Developer Agent competition: what applies to our main-track tree"
authors: "survey of 8 public writeups (Aeterna/Zavdi; Toeda/MOBIUS; draculess99; Ritabanm; Muhammad-Dabeer-23; nazarcoder123; Ronak1167; Bellam arXiv 2610.33958)"
year: 2026
url: "see per-source sections"
topics: [prompt, sampling, edit-reliability, budget, tools, lora, multi-agent, selection, noise, paper]
relevance: medium
read: partial
date_added: 2026-11-17
---

Reading status, stated once. Every source was read through a fetch extractor (a small model summarising the page), not as raw text by me. The numbers below are the extractor's reading, and each was cross-checked only against the page it came from. None has been recomputed. Kaggle's own writeup pages are JavaScript-only and were not read. Several titles named by the lead were searched for and not found (listed at the end). All text read is treated as data. Inferences are marked "(mine)". Nothing here moves a claim status: writeups only propose hypotheses.

## Takeaway

1. Only one source ran on the real `swegemma` harness with public-LB scores attached (Muhammad-Dabeer-23). The largest paired study (Aeterna, 150 tasks) ran on its own virtual-clock replay of the contract, not on `swegemma`. The most rigorous design (Toeda, pre-registered, 5 seeds) used other models, llama.cpp and graph tools. So the evidence that transfers to our tree is thin.
2. Nothing found beats a plain single loop on the 31B for resolves. Where an intervention moved a process metric (submits, long thoughts, test runs), resolves did not move: Aeterna's paired WT deltas all include zero; Muhammad's reviewer stage scored a mean 0.133 on LB against 0.158 for its single-loop v4 adapter (a difference inside single-draw noise).
3. Three results agree with our own record: pointing the agent at the right files did not fix wrong fixes (Muhammad 2 of 33; Aeterna gold file opened in 47 of 52 empty-diff timeouts; our class C, C-011); a test gate on submit did not help (Aeterna P2_B; our EXP-055/057); extra stages and tools hurt the smallest model (Muhammad's E4B pipeline 4/50, LB 0.06).
4. The cheapest new lever for us is a sampling change (thinking cap about 1024) plus one zero-GPU trace-mining check (turn length against resolve), not a prompt rule.

## Ranked ideas

Rung names follow the screening ladder in `experiment-protocol`: desk check, trace mining (0 GPU), smoke-8 (about 0.8 GPU-h), dev-48, upload. Graph-tool items are flagged GT: our tree bans those tools (C-012), so they are not testable without changing that.

| # | Idea | Source | Evidence and credibility | Change to our submission | Already tried by us? | Cheapest rung |
|---|---|---|---|---|---|---|
| 1 | Cap thinking near 1024 tokens (from a large budget) | Aeterna Think-1024; Ronak1167 (claim only) | Aeterna: 31B, 150 tasks, paired, 1 seed, temperature 0.2. WT 48/150 under both budgets, delta 0.0 [-6.0, +5.3]. Long-thought episodes 63 to 3; submitted endings 34 to 45; by stratum +3 and -3. Ronak: 12B, LB 0.03, no ablation. Not tied to an LB score. | `thinking_budget` in `configs/sampling.yaml` (sampling lever, in bounds) | Partly. C-010 compared 4096 with 256 (resolves unchanged, edit-arg loss 18.2% at 4096 against 53.5% at 256, EXP-024 §0). 1024 not found in claims.md (README §3 not read in full, verify). | Trace mining first (idea 2), then smoke-8 reading the lost-call rate, not resolves |
| 2 | Turn length as a failure signal: passing rollouts have fewer long turns | Aeterna failure taxonomy | Observational, 41 mixed tasks: 37 of 129 passing rollouts had a turn over 1,500 tokens against 71 of 117 failing; passing edited about 59 s earlier and used about 91 fewer completion tokens per turn. Same-task contrast, but turn length and outcome may share a cause such as task difficulty (mine). | None directly. It sets the endpoint for idea 1: share of turns over 1,500 tokens | Not found. We track first-edit turn (C-011, EXP-009) and wall (EXP-028 forensics), not per-turn tokens by outcome. | Trace mining on existing dev-48 traces, 0 GPU |
| 3 | Time or submit notice injected before the cap | Aeterna clock guard (P2_A) | Strict metric +8.7 points, CI excludes zero; WT flat (+1 task). Authors say notices are harness-only and not shippable. | A prompt-only version ("submit by call N") is the only form we can ship. | Close relative: EXP-010 tripwire at call 25, LB 6/58, uninformative; C-011 says a call-index rule does not convert never-edited tasks. C-007: 18 of 48 tasks hit the 28-call cap with 0 resolves. | Desk check first: does `swegemma` grade the working-tree diff or only a submitted patch? If working tree, Aeterna's WT-flat result applies and this idea is worth little. |
| 4 | Exact-copy failures are mostly whitespace (89% of not-found edits) | draculess99 | E2B, CPU, 12 QuixBugs single-function tasks, 1 seed; 41 of 46 rejected edits "old matched 0 times", 39 of those whitespace-only. Very low power, not our model. | A prompt line on exact whitespace copy. Low prior: our record says edit prompt lines do not stop resends (EXP-044, EXP-053). | Our dominant mechanism is different: a lost argument (unterminated `new_string`, C-004), 33.1% of calls. The not-found share has not been separated from it, which is the gap. | Trace mining: split our `edit_file` failures into lost-argument and not-found, and for not-found count whitespace-only mismatches, 0 GPU |
| 5 | Do not invest in localization or hints | Muhammad-Dabeer-23; Aeterna | Muhammad (swegemma, 33 unsolved tasks, issue text named the fix files and functions): 2 of 33 solved; in 28 of 31 failures the agent edited exactly those files and still failed. Aeterna: gold file read in 47 of 52 empty-diff timeouts, all gold files opened in 33; 46 of 52 never attempted an edit. Two independent sources agree. | None; supports keeping the tree without graph tools | Yes: class C is 12 of 24 unresolved runs (EXP-053), C-011, C-012, EXP-064/066 (localizer's single location is its choice). | Already covered |
| 6 | Test gate: block `submit_patch` until a test ran since the last edit | Aeterna P2_B | Relative to the clock guard: strict 23.3 to 20.7, WT 33.3 to 32.0, no CI given. One arm, 150 tasks. | A prompt rule only (no tool change allowed). | Yes in prompt form: EXP-055 (obeyed on 7 of 7 tasks that made calls, 3 of 7 checks ran no tests); EXP-056/057 skill check; EXP-072. Consistent, no gain. | Done |
| 7 | Two-stage fixer then reviewer | Muhammad-Dabeer-23 | swegemma, local 50 tasks unpaired: 14/50 at 6.5 min and 13/50 at 6.0 min against adapters at 10-11/50. LB at 6.0 min: 0.15, 0.13, 0.12 (mean 0.133); v4 adapter, 5 draws, mean 0.158. The local gain did not carry to the LB, though the 0.025 gap is about 1.5 tasks and inside noise (mine). I did not read the base-model single-loop local count. | Role split in `agent.yaml` (in bounds, but not in line with our E4B result) | Yes: D-008, EXP-062 to 074 (stages add failure classes, no gain). Muhammad's E4B pipeline 4/50, LB 0.06, against our S-014 E4B. | Done |
| 8 | Scaffold helps the smallest model | Toeda (Zenodo) | Pre-registered, 104 tasks, 5 seeds, llama.cpp q4_0, E4B 10.0% to 15.4%, paired CI +2.3 to +8.8 points. Maximal scaffold = nine-rule prompt plus graph tools plus analyzer sub-agent, so the active part is not separable. GT. | None; cannot isolate a part we may use | Our E4B record: every added stage added a failure class (EXP-072/073/074); longer prompts and more tools pushed text-form calls (EXP-065). Tension, not a clean contradiction (different runtime, graph tools). | Not worth a rung until the part is isolated |
| 9 | Best-of-N headroom | Aeterna | pass@6 oracle 44.0% (66/150) against 31.0% single-draw (93/300 over 2 seeds). 25 always solved, 41 mixed, 84 never. | None without a selector | C-015, C-023; EXP-034 union minus best 5 of 48; EXP-040 D = 0. No selection signal found by us. | Closed |
| 10 | Structured tools for small models | Bellam arXiv 2610.33958; TopoSWE; nazarcoder123 | See the per-source sections. GT. TopoSWE is unverifiable. | None | C-012 for our 31B; EXP-064/066 for E4B | Closed |

Rows 1 and 2 are the only ones that carry a new, testable change in bounds. Row 3 depends on a harness fact I did not check. Row 4 is one trace-mining pass.

## Per-source notes

Fields per source: what changed; model; cohort or benchmark; n; seeds or draws; exact numbers; harness; credibility. "Unread" marks parts of a page the extractor did not show.

### Aeterna (Moran Zavdi), repo Kaggle-Gemma-4-Developer-Agent-Competition, Apache-2.0

- Files named: PAPER.md, reports/LESSONS_FOR_COMPETITORS.md, reports/lb_lattice.csv, evidence/, benchmark/, scripts/reproduce_all_tables.py. The extractor read PAPER.md and LESSONS_FOR_COMPETITORS.md; evidence/ and the scripts were not read.
- Headline, quoted: "better agent process does not mean higher accuracy".
- Model: 31B. Baseline D69 (unadapted; public LB 0.18); tr20 and scale10 are the ForgeSWE LoRA at scale 2.0 and 1.0 (LB 0.17 and 0.13).
- Harness: not `swegemma`. A virtual clock over a six-tool ADK-style contract (`grep_search`, `run_shell`); 420 s cap, 28 tool calls, 80 turns; decode speed fixed at 14.0 tok/s (unadapted) and 13.006 tok/s (adapter). Calibration split 150 tasks (23 competition_public, 35 competition_new, 92 other); test split sealed. The authors state the instrument did not reproduce the Kaggle ordering of D69, tr20 and scale10.
- Metric: WT = the final working-tree diff passes hidden tests. Strict = WT and `submit_patch` before budget exhaustion.
- Results, WT / Strict: D69 31.0% (93/300, 2 seeds) / 19.3%; tr20 s0 31.3% / 18.0%; tr20 s1 32.0% / 14.7%; scale10 30.3% (2 seeds) / 15.7%; P2_A 33.3% / 23.3%; P2_B 32.0% / 20.7%; Think-1024 32.0% / 18.7%; pass@6 oracle 44.0% / 32.7%.
- Paired WT deltas, 95% CI in points: tr20 s1 against D69 +1.0 [-4.7, +6.7]; tr20 pooled +0.7 [-3.3, +4.7]; scale10 -0.7 [-4.7, +3.3]; Think-1024 0.0 [-6.0, +5.3]. All include zero. So the LoRA at scale 2.0 and 1.0 did not hurt on this instrument. This does not contradict C-013 (a different adapter and a different instrument).
- Interventions: P2_A clock guard (notices at 330 s and 375 s): Strict +8.7 points, CI excludes zero; WT +1 task. P2_B test gate (blocks `submit_patch` once if pytest has not run since the last change): see table row 6. Think-1024 (4096 to 1024): long thoughts 63 to 3; time-budget endings 85 to 77; submitted endings 34 to 45; 9 flips each way; WT 48/150 both; temperature 0.2, one seed.
- Failure taxonomy (tr20 s1): 74 timeouts = 52 empty-diff + 22 unsubmitted-with-diff. Of the 52: 47 read a gold file; 33 opened every gold file; 46 never attempted an edit. Median fatal turn began with 67 s left and generated about 1,580 tokens (about 74% reasoning). Median first edit for timeouts with a diff: turn 16, about virtual second 351. Tool wall median 0.33 s, so generation dominates. Removing scratch files fixed 0 of 19 failures that had an untracked file. Mixed tasks (41): passing rollouts edited about 59 s earlier and used about 91 fewer completion tokens per turn; 37 of 129 passing rollouts had a turn over 1,500 tokens against 71 of 117 failing.
- On-policy SFT data shrank to about 90 usable rows; the training run never produced a checkpoint beyond step 0 (their statement).
- Credibility: paired, large n, 1 to 2 seeds, one variable at a time. No LB tie for the process interventions. Their compact "1,350 paired episodes" dataset was not broken down by condition on the page.
- Fit with our record: C-010 (thinking budget); C-011 and EXP-010 (time rules); C-007 (call cap binds). Our 31B tree runs at 8 min and 28 calls (claims C-002, C-007), so their 420 s and 28 calls is a near match; this is the source most worth reading raw.

### Zenodo 23834104 (Taiko Toeda, MOBIUS LLC), v1.0.5, Apache-2.0, published 2026-10-31

- File `gemma4-scaffold-capacity-v1.0.5.zip` (3,405,159 bytes), not downloaded or opened. Read via the Zenodo API record.
- Design: pre-registered, 3 capacities (E4B, 12B, 26B-A4B) x 2 scaffold levels x 5 seeds on 104 public competition tasks; 4,056 task-run records (3,120 confirmatory, 936 exploratory mid level, no rates on the page).
- Setup: Google QAT q4_0 GGUF on llama.cpp, 2 RTX 5070 Ti. Not the competition's 31B on vLLM.
- Scaffolds: low = a two-sentence instruction with six workspace tools. Maximal = a nine-rule instruction plus code-graph tools plus an analyzer sub-agent. GT.
- Results: E4B 10.0% to 15.4%, paired task-bootstrap 95% CI +2.3 to +8.8 points. 12B and 26B-A4B: 90% CIs inside +-5 points, no point estimates on the page. The registered prediction (scaffold helps 12B and 26B-A4B, not E4B) "failed in both directions".
- Credibility: the strongest design here (registered, seeds, paired). Limits: scoring by the official verifier after a repair to the shipped local grader (deviation log D1 to D11, headlines unread); timestamps self-attested; drafted with an AI assistant. No LB tie.
- Use: a source for the paper track (what to pre-register), and a caution that E4B can gain from scaffolding, but the gain is not attributable.

### draculess99/Gemma4-Coding-Agent-Research

- Question: does harness-triggered test feedback help a small local code-repair agent? Single-seed pilot.
- Model E2B (QAT Q4_0 GGUF, llama.cpp b12192, CPU only), custom harness (not `swegemma`), 12 QuixBugs single-function tasks from 28 eligible, 1 seed, 24 runs.
- Arms: no tests; tests run before step 1 and after every applied edit. Resolved 0/12 against 1/12 (sign test p = 1.0; Clopper-Pearson 0-26.5% against 0.2-38.5%). Submit calls 5 against 2; format errors 5 against 0; rejected edits 15 of 24 against 31 of 43; wall 519 s against 576 s.
- Edit failure: 41 of 46 rejected edits were "`old` matched 0 times", 39 whitespace-only. Quoted: "The dominant failure in both arms was exact-string edit application". No fix tried.
- Credibility: very low power; confounded treatment arm; possible contamination; a harness defect (memory addresses in feedback). A 4-run pilot (2/2 against 0/2) did not reproduce.

### Ritabanm/gemma-4-developer-agent-paper (TopoSWE)

- Pipeline: AST multigraph; personalised PageRank (alpha 0.25) over CALLS/INHERITS/IMPORTS/RAISES edges with a 2,400-token folded context; line-anchored SEARCH/REPLACE synthesiser; deterministic gate SSVG (syntax, unbound names, public arity, impacted tests); an optional rank-16 DPO adapter. GT.
- README table, SWE-bench Lite (N = 300 in headline bullets only), resolved / Hit@3 / mean tokens / syntax errors / latency: 9B zero-shot ReAct 18.3 / 44.7 / 21.4k / 24.8% / 194.0 s; 9B + full TopoSWE 33.7 / 76.3 / 5.8k / 2.9% / 78.5 s; 31B zero-shot 29.0 / 58.0 / 24.6k / 16.4% / 268.0 s; 31B + BM25 + ADK sub-agents 35.3; 31B + PPR + folding 41.0; + SSVG gate 44.7 (syntax errors 1.8%); + DPO adapter 48.3 / 84.0 / 5.9k / 1.4% / 89.2 s. "+19.3%" is percentage points (48.3 - 29.0).
- Credibility: very low. No run logs, seeds, harness, variance or DPO details; the table's path runs through a figure-generation script; a "Gemma 4 9B" is not a competition model; mean tokens 5.9-6.4k conflicts with the 2,400-token handoff; no LB score. Treat as unverified.
- Only transferable thought: a syntax and arity gate before submit. It needs a tool, so it is out of bounds.

### Muhammad-Dabeer-23/gemma4-agent-paper (docs/paper_writeup.md)

- Harness: `swegemma` 0.2.11, `adk-submission` 0.2.13, vLLM on four GPUs, about 5 to 6.5 min per task. Model `gemma-4-31b-it-qat-w4a16-ct` unless stated. Closest source to our setup.
- Local benchmark: 50 tasks (20 held out from training plus 30 from the provided set; fastapi, rich, requests, httpx); compared by tasks gained or lost against a reference run; seeds not reported; unpaired.
- Adapters: v2 LoRA on 101 tasks (1.25M tokens, about 70% synthetic) 10/50; v4 105 sequences (0.98M tokens, 68% synthetic), 384-token thinking cap, 11/50 (time-outs 15 against 19 base; empty patches 4 against 6); v5 on reference-fix demonstrations 10/50 with degraded behaviour (repeated stock phrase, 12 tasks with no change).
- Fixer-to-reviewer pipeline (base model fixes; a reviewer without access to the fixer's reasoning runs `git diff`, tests the issue example, repairs or submits): 14/50 at 6.5 min, 13/50 at 6.0 min. E4B with the same pipeline 4/50 (5/50 with two more reviewers); E2B 2/50.
- Hint test: for 33 unsolved tasks the issue text named the files and functions touched by the real fix; 2/33 solved; in 28 of 31 failures the agent edited exactly those files.
- Public LB: v2 0.17, 0.10, 0.15; v4 0.15, 0.17, 0.15, 0.15, 0.17 (mean 0.158); v3 0.13; fixer-reviewer at 6.0 min 0.15, 0.13, 0.12 (mean 0.133); E4B one reviewer 0.06.
- Unread: the README names configs `submission_v4_fast` (5.5 min), `submission_v6c6` (6.0 min), `submission_v6e_e4b` that the extracted paper text does not describe. The v4 adapter is not included.
- Credibility: the only `swegemma` source with repeated LB draws; the LB means are within our measured single-draw noise (C-001: sample sd about 2 tasks; 0.158 against 0.133 is about 1.5 tasks) (mine). The local n = 50 comparison is unpaired.
- Fit: a v4-adapter LB mean of 0.158 equals our three-draw baseline 0.161 (C-001 history, 28/174), so a LoRA neither helped nor hurt on the LB here. This is not a contradiction of C-013, which is about broad-trajectory adapters (mine).

### nazarcoder123 (GraphSWE-Gemma)

- README only: AST NetworkX multigraphs with 256-dim symbol embeddings; caller/callee subgraph compaction "93.1% token compression"; in-memory AST verifier; ADK 2.0 layout. Model variant unnamed; demo data (`mock_graph.json`, `mock_tasks.jsonl`); no resolve rates; no LB score. Stub or demo scale. GT.

### Ronak1167/gemma-4-developer-agent

- README states Candidate v23, submission ID 58187123, public score 0.03. Model `gemma-4-12b-it-qat-w4a16-ct` INT4 on one L4 (not a competition model).
- Changes: thinking budget 1,024 with `include_thoughts: false`; action-only output grammar (assistant turn context 480 to 112 tokens); 12-call target in the prompt plus a hard cap of 28 calls or 5 minutes; turn-1 inspection of pre-injected regression test diffs.
- Claims, no ablation numbers: thinking budgets of 256 tokens or less led to delimiter loops and context overflow; 280-token preambles displaced more than 25% of issue context. Task counts (129, 120, 48) not reconciled.
- Paper files `paper/gemma4_swe_agent_research_paper.md` and `paper/gemma4_swe_agent_kaggle_writeup.md` were not fetched.
- Credibility: LB 0.03 is evidence against the package. The "256 or less" claim is directionally consistent with C-010 but carries no number.

### Bellam, arXiv 2610.33958 (abs page, v2 revised 2026-11-09)

- Title as on the arXiv listing: "How Much Do Structural Tools Help Small Coding Agents? A Pre-Registered Scale Study of Code Localization" (Saurav Bellam, UT Austin). Correction: an earlier extraction (via a third-party summary site) gave a different title and figures (79k episodes; E4B named; gain 17-21 points at 1.7-4B). Those are not on the arXiv page and I do not use them.
- arXiv abstract page (read): nine open-weight models (Qwen3 0.6B-32B; Gemma 4 E2B to 12B), one fixed harness, 500 held-out SWE-bench tasks, four tool sets and a placebo arm, five seeds per condition. Tools raise function Acc@10 by about +0.06 to +0.10 for the two small Gemma 4 models; the 12B shows no gain because it rarely submits an answer; the embedding index, not the code graph, carries the gain. No E4B-specific figure on the page.
- Localization, not resolve. GT (it needs an embedding index tool).
- Relation to C-012: it measures small-model localization with tools, we measured the 31B harness tools against grep; no conflict. The "12B rarely submits" finding resembles our E4B's no-call and text-form failures (EXP-065) (mine).

## Not found or not read

- Not located by search: "Local SWE-Agent: Graph-Guided Retrieval & LoRA Adaptation on Gemma 4"; "Jev"/Graphify dual-process; "Missing edges" audit of code graphs; "Graph-Augmented Multi-Agent SWE with Gemma 4"; "AutoFix"; the 278-bug import-graph PageRank benchmark. Searches also returned unrelated hackathon and Prometheus papers.
- Blocked: a TOPAZ post on blog.gopenai.com returned HTTP 403 in an earlier fetch. A search snippet shows it is a graph-folding paper-track entry; no numbers read.
- Surfaced, not opened: ai-muninn posts (Gemma 4 26B 116/300 = 38.67% on SWE-bench Lite; OpenHands tool-call errors against SWE-agent); a HyperAI "gemma 4 tfd agentic trajectories" dataset (50 SWE-bench Lite tasks, trajectories); a Pebblous multi-agent vLLM Gemma 4 report; the Kaggle writeup pages themselves.
- `experiments/README.md` §3 was not read in full (42k tokens). "Already tried" marks come from `knowledge/claims.md` (C-001 to C-021, read) and `knowledge/lessons-e4b-loop.md` (read before this note); an experiment I did not open may already have covered rows 1 to 4 (verify before screening).

## Ideas to test

- On existing dev-48 traces (R and E4B arms), count turns over 1,500 completion tokens in resolved against unresolved runs, paired within task. Prediction (falsifiable): the resolved share with such a turn is below the unresolved share by at least 20 points (Aeterna saw 29% against 61%). 0 GPU.
- Set `thinking_budget` 1024 in `configs/sampling.yaml` on the 31B tree. Prediction: edit-arg loss rate stays under 33.1% (the v24 rate, C-004), and dev-48 resolves stay within 2 of the 4096 arm. If loss rises toward the 53.5% seen at 256, the cap is rejected.
- Mine our traces for `edit_file` results that say not-found and count whitespace-only mismatches. Prediction: not-found is under 10% of failed edits (our lost-argument mode dominates, C-004), so a whitespace prompt line has under 10% of failures to address.
- Check what the harness grades at timeout (working-tree diff or submitted patch). If the working tree, a notice line is worth at most the Strict-only gain Aeterna measured (resolves flat).

## Caveats

All figures are secondhand through fetch extraction and none was recomputed. Cohorts differ (our dev-48 against Aeterna's 150, Muhammad's 50, Toeda's 104), so no number here sets an expected gain for our submission. Single-draw MDE on the public LB is about 4 tasks (C-001), so LB means quoted from these repos (0.158 against 0.133) do not separate configs.
