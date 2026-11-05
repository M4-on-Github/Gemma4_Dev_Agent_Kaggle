---
id: lit-2026-11-05-architecture-families
title: Best-of-N, orchestrator with workers, role pipelines, against a single loop - what the evidence says for one fixed open model with no hidden tests
authors: [lit-scout]
year: 2026
url: none (synthesis of the notes linked below)
topics: [multi-agent, selection, budget]
relevance: high
read: partial
date_added: 2026-11-05
---

Question from the user (2026-11-05), serving D-005. Every number below is in the linked note with its locator; all were read through a fetch tool that summarises HTML pages (flattened tables, no PDFs), so each is "as extracted", none was checked against a PDF. Derived percentages are mine and marked. Notes: lit-2407.01489, lit-2501.14723, lit-2507.23370, lit-2504.07164, lit-2412.21139, lit-2512.13607, lit-2407.21787, lit-2503.23803, lit-2402.05120, lit-2512.08296, lit-2602.03786, lit-2604.13120, lit-2403.17927, lit-2503.13657, lit-2306.09896, lit-2310.01798, lit-2601.12307, lit-2410.20285, lit-2506.03524, lit-2604.05407, lit-cognition2025-dontbuild, lit-2401.07324.

## 1. The answer in three sentences
No source compares all four families on one open model at matched budget on SWE tasks. The evidence points the same way across independent sources: structure helps when it adds an external, executed signal (tests, run results) and does not help when it adds more same-model text opinion; every role or agent added costs turns, and turns are our binding cap. On the one SWE-bench table with equal-budget single and multi-agent arms, every multi-agent topology is at or below the single agent (lit-2512.08296, n=20 per cell, so only the direction is usable).

## 2. Family against measured effect and conditions
| Family | Best measured effect | Conditions of that measurement | Cost reported | Holds for us? |
|---|---|---|---|---|
| F0 single loop | reference. Equal or better than every multi-agent topology on SWE-V (SAS 0.522 vs -2.1 to -14.9% relative) | frontier models, n=20 | turns 7.2 vs 11.4 to 44.3 | the baseline |
| F1 best-of-N, selector uses executed tests | selected 57.4 vs random 45.8 vs oracle 69.8 (CodeMonkeys); 51.0 vs Pass@1 34.4 vs Pass@26 64.4 (R2E-Gym); 32.0@16 vs 20.6 vs 42.8@16 (SWE-Gym); 96 vs 77 vs 126 on Lite (Agentless). Derived: 39 to 55% of the gap to the oracle | N 10 to 40 candidates, repo tests plus model-written tests, strong or trained verifier | 100 test executions per issue (CodeMonkeys); verifier 14B trained (R2E) | partly: the signal exists, the time does not |
| F1 with majority vote over patches only | 77 vs greedy 80/88 (Agentless); 8B plateau 39 to 40 vs 39.2@2 (Nemotron); plateau about 100 samples (Large Monkeys) | | none | no signal; votes tie at N=3 |
| F1 with same-model LLM judge only | worse than test voting; better only after a top-3 test filter (CodeMonkeys); N=3 selector agent recovers 55 to 69% of the oracle gap (Trae, selector model unstated) | frontier | extra agent run | untested at 31B |
| F2 orchestrator with workers | AOrchestra SWE-V 82 vs ReAct 64 / Mini-SWE 56 / OpenHands 48 (Gemini-3-Flash) but 76 vs Mini-SWE 84 (DeepSeek-V3.2); Centralized -3.1% (SWE-V), -19.2% (Terminal-Bench) | n=100 and n=20; worker models partly unstated | Centralized turns 27.7 vs 7.2, overhead 285% | not supported |
| F3 role pipeline | AgentForge: Tester/Debugger/Planner removal -14/-11/-23 points of 100; Critic removal -4. MAGIS: QA removal -3.3 (full), -2.0 (Lite) | GPT-4o / GPT-4; baselines are one-shot, not loops | 2.7x tokens (AgentForge); under 5 min per instance (MAGIS) | partly: the executing roles only |
| F3 same-model text reviewer | no source shows a gain; intrinsic self-correction lowers accuracy (CSQA 75.8 to 38.1; GSM8K GPT-4 95.5 to 89.0); feedback quality is the bottleneck for code (Self-Repair) | reasoning and function-level tasks | | against |
| Small model (<10B) | fixed workflow beats free loop: 19.2 vs 11.2 (Seed-Coder-8B), 14.6 vs 3.4 (Qwen3-8B), 19.4 vs 1.4 (Qwen2.5-Coder-14B); a better edit interface moves Qwen3-8B 13.2 to 13.0 | models not tuned for tool loops | | partly |

## 3. Part A: selection signals without hidden tests
Gain of each signal as measured (locators in the notes):
- Majority over normalised patches: no gain over the first candidate in the two places it is isolated (Agentless Table 4 vs §5.2.2; Nemotron §7.4). Confidence: medium, the first-candidate baseline in Agentless is ambiguous (80 vs 88).
- Repo regression tests: +4 over voting (Agentless 77 to 81); +4.5 points (R2E-Gym §4.4, 42.9 to 47.4). Available to us, cheap in tokens, but seconds per run unknown here; sibling-test runs are about 70 s on Requests modules (C-017 sources).
- Model-written reproduction tests: the largest single step (Agentless 81 to 96) but 94 of 213 are valid after the gold patch (§5.1.3); under 20% of model-written tests discriminate and up to 10% are toxic (R2E-Gym Fig. 5). Cost: 100 executions per issue in CodeMonkeys.
- Same-model judge: helps only on top of test results (CodeMonkeys §2.3). SWE-Search reports 84% selection accuracy for a discriminator and 73% convergence of the value function, at 100 search iterations.
- Patch-size or syntax heuristics: only tie-breakers (Nemotron §3.3.1) or pruning (Trae Table 2: +3.4 to +5.6 points over ablations). No source isolates a pure length heuristic; I did not find one.
- Candidate diversity: all sources use temperature (0.8 in Agentless), independent runs, or different location sets; none ablates prompt variants or edit formats. Not found.
- Gain against N: SWE-Gym 29.8@8 to 32.0@16; R2E-Gym 47.6 to 48.4 for 16 to 21 trajectories; Agentless plateau near 40 samples; Nemotron 8B 39.2@2 to 43.6@32; Large Monkeys coverage log-linear but verifiers plateau near 100. Oracle minus average is 8.7 points at N=3 (Claude, Trae Table 1: 70.00 vs 61.33) and 20.8 at N=10 (Trae §2). The value of N=2 or 3 comes from the oracle gap, not from a plateau.
- Ceiling for our data (my inference): our dev-48 arms overlap only half to two-thirds (C-016), so the union ceiling is real; D-005 reads it in EXP-034 Q1.

## 4. Part B: orchestrator and worker
- Only head-to-head: AOrchestra (lit-2602.03786). It wins against three of four single-loop scaffolds with Gemini-3-Flash and loses to Mini-SWE with DeepSeek-V3.2. The same model's single-loop score spans 22 to 64 by scaffold, so the claim depends on the baseline chosen. Handoff context quality is measured (GAIA: 86.00 none, 84.00 full, 96.00 curated).
- Equal-budget evidence says no (lit-2512.08296).
- Failure modes with numbers: coordination turns (Table 5); inter-agent misalignment 13.2% of failures (MAST FM-2.6); error amplification 4.4x to 17.2x, though the paper's own regression did not find it significant (p = 0.658).
- Cognition (no data) allows one shape: sequential read-only worker, one writer (lit-cognition2025-dontbuild).
- Our localization is solved (45 of 48 name a gold file by call 2), so a delegated explorer attacks the wrong failure.

## 5. Part C: role pipelines, debate, same-model reviewer
- Roles that execute carry the gain (AgentForge Table III; MAGIS QA runs the Developer's change). A critic with no execution adds 4 of 100, which is inside the noise of that table.
- Debate lost to self-consistency at equal responses (Huang Table 7: debate 83.0 at 9 vs self-consistency 88.2 at 9).
- Same-model reviewer rubber-stamping: no source measures the false-approval rate of a patch reviewer. MAST reports superficial verifiers (FC3 about 24% of failures) and R2E-Gym finds a trained verifier is biased toward the agent's own stated thoughts (Fig. 7: patch-only 37.6 vs with trajectory 42.8). The honest reading: unmeasured, with indirect evidence against.

## 6. Part D: when multi-agent loses
Sequential tasks with a single-agent baseline above about 45% lose with every topology (-39 to -70% relative on PlanCraft; coefficient -0.236). One model role-playing the stages in one conversation matches the multi-agent run (lit-2601.12307), so separate agents add overhead without information. Same-model sampling and voting works for function-level code (HumanEval 0.14 to 0.18, 0.24 to 0.33, 0.67 to 0.73 at N=40) and not for patch voting at small N.

## 7. Part E: under 10B
- A fixed locate-repair workflow beat an autonomous loop for every sub-35B model in one table (lit-2506.03524), with a large exception pattern: the gap is about tool-loop training, not parameter count.
- Interface fixes do not rescue a reasoning-limited 8B (CODESTRUCT 13.2 to 13.0).
- Narrow roles help only when each role is trained (alpha-UMi). Not reachable.
- Open-model test-time scaling with trained 8B/14B works at k up to 32 (Nemotron), not at our budget.

## 8. The three designs the evidence most supports under our constraints
Ranking, weakly ordered because nothing here is a head-to-head on our setting: D1 above D2 above D3; the orchestrator is not on the list.

**D1. Single loop with an executed verify-and-repair step (one LlmAgent, or LoopAgent of verify and fix, max 2 rounds).**
Mechanism: the only measured gains from review come from an executed signal (R2E-Gym regression +4.5; AgentForge Tester/Debugger; Self-Repair; Huang oracle rows).
Confirm: the verify step runs a command in at least 80% of runs and, among the 30 right-file-wrong-fix tasks, the last test result before submit was a fail in at least half (EXP-034 Q2); paired dev-48 net at least +5 tasks. Kill: the check passes on almost every patch (D-005 rule), or the verify turn is reached in fewer than 4 of 8 tasks inside the cap.

**D2. Two or three tool-free parallel proposals, selection executed-first, one applier.**
Mechanism: oracle minus average is 8.7 points at N=3 even for a strong model (Trae); selection beats a random pick by 39 to 55% of the gap only where tests ran (Agentless, CodeMonkeys, R2E); a same-model judge helps only after test results (CodeMonkeys). Rule from the evidence: rank by tests passed, break ties with the smaller patch, never use majority vote (it ties at N<=3).
Confirm: EXP-034 Q1 union minus best arm at least 4 tasks; proposals differ in at least 2 of 3 (D-005); pairwise judge accuracy on disagreeing pairs at least 70% with order swapped (SWE-Search reports 84% for its discriminator; I found no 31B number). Kill: proposals identical in 6 of 8; applying and testing each candidate costs over 60 s so three candidates cannot fit in 270 s; or judge accuracy under 60%.
Conflict to flag: ParallelAgent is offered by the host (kg-743063, 2026-10-11) but tool-calling branches break on ADK v1.36 (the same thread) while EXP-007 measured real concurrency (max_in_flight 2) and a 78% sibling stall from a synchronous tool. Tool-free proposers avoid both; unresolved for anything else.

**D3. Narrow sequential locate-then-edit pipeline for the ~4B variant only.**
Mechanism: a fixed workflow removes planning load from a model that cannot sustain a free loop (Seed-Coder Table 15), and one stage's job fits a short context. Evidence for 31B is the opposite (OneFlow, Scaling Agent Systems), so this is not a 31B design.
Confirm: on E4B smoke-8 the pipeline reaches a first edit in at least 2 more tasks than the loop at the same cap; resolves are not the endpoint (CODESTRUCT warns empty patches can fall with no resolves).

## 9. Repeated claims I could not support
1. "Majority voting over patches is a useful selector": isolated twice (Agentless, Nemotron) and does not beat the first candidate or plateaus at once.
2. "An LLM selector peaks at 5 to 6 candidates" (Trae product note, in the 2026-10-28 review): not in the Trae paper as I read it; the per-N curve is in Figure 10, which I could not read.
3. "A same-model reviewer improves patches": the only SWE ablations are a Critic at +4 of 100 and a QA engineer at +2 to +3 points, both GPT-class with no false-approval rate.
4. "Orchestrators beat single agents": mixed in AOrchestra, negative in the equal-budget table.
5. "Same-model sub-agents drop 12 of 18 to 6 of 18" (C-014): I found no source for the figure with a web search; leave as unverified.
6. "More agents is all you need" for SWE: the evidence is HumanEval with BLEU voting.
7. "Agentless beats agents for small models" as a general rule: one table (Seed-Coder). A secondary snippet says Kimi-Dev's agent variant has pass@10 74.0 against Agentless pass@30 73.8; I did not read that paper.
8. "Debate helps": Huang Table 7 says no.
9. Prompt-level or edit-format diversity as a candidate generator: no measurement found.

## 10. What does not transfer, in one place
Frontier or trained models (GPT-4o, Claude, Gemini, fine-tuned Qwen), tens of candidates, no wall-clock cap, separate trained verifiers, custom tool code, per-branch isolated working directories, SWE-bench Verified/Lite with public tests.

## 11. Not verified
All numbers come through a summarising fetch tool, not PDFs. Not read: Trae Figure 10, CodeMonkeys Figure 6 (majority and model-only numbers), Nemotron Fig. 12 itself, Self-Repair same-model-versus-GPT-4 table, MAST appendix, AOrchestra appendices beyond A.1, SWE-Search Appendix I. Author lists of several papers were not printed by the tool and are marked in each note. The Scaling Agent Systems SWE numbers rest on n=20 and an extraction that disagrees with itself in places.
