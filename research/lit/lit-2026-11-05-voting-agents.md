---
id: lit-2026-11-05-voting-agents
title: Voting agents on a small model - action-level and per-step voting, same-model agreement over a lettered list, temperature against prompt diversity, N of 8 to 32 (gaps 1 to 4 of EXP-039 section 2 Q6)
authors: [lit-scout]
year: 2026
url: none (synthesis of the notes linked below)
topics: [multi-agent, selection, sampling]
relevance: high
read: partial
date_added: 2026-11-05
---

Question (2026-11-05, serving C-023 and D-005; EXP-039 section 2 Q6): voting agents on the E4B, voters at different temperatures, fixed tie rule, first screen V1 = one proposer, 16 tool-less voters answering `PICK: X`, one actor. Notes written for this synthesis: lit-2511.09030 (MAKER), lit-2602.12276 (CATTS), lit-2402.13212 (Soft-SC), lit-2309.03882 (option-letter bias), lit-2402.05201 (temperature), lit-2310.07088 (prompt diversity), lit-2602.11619, lit-2608.11403, lit-2604.03809, lit-2408.00724. Reused without re-reading: lit-2512.13607, lit-2407.21787, lit-2402.05120, lit-2026-11-05-architecture-families. The 2026-10-28 literature review has no entry on voting, MAKER or action-level self-consistency (read to line 130 on 2026-11-05; its section 4 covers patch voting only). Every paper was read through a fetch tool that summarises HTML (no PDFs), so each number is "as extracted"; the read depth is in each note. Tags: [S] what a source shows, [I] my inference.

## 1. Short answer
- MAKER exists and I opened it: arXiv:2511.09030, Meyerson et al. (Cognizant AI Lab, UT Austin), submitted 12 Nov 2025. It measured Towers of Hanoi with 20 disks (2^20 - 1 steps) at zero errors with gpt-4.1-mini, plus 5x5 and 6x6 multiplication. It is not a repair or repository task and its smallest model (Llama-3.2-3B) failed completely (error 1.0).
- Nobody I found votes on the next action of a repository-repair agent. The nearest are a web agent (CATTS, gpt-oss-120b) and shell/web/household agents on 2023 models (Soft-SC). Both show small gains at best and saturation at N of about 5 to 10.
- No source gives the agreement rate of a same-model vote over a list the same model wrote, nor how often it differs from the model's own greedy pick. The nearest number is CATTS App. J (about 40% of web steps unanimous at N = 10, free-form actions).
- Prompt diversity beats temperature at equal ensemble size in the one paper that compares them (lit-2310.07088), on reasoning tasks and without a temperature-only control; a persona-only committee of a 14B model writes near-identical rationales (lit-2604.03809).
- For 7B to 8B models the vote helps the aggregate by 2.7 to 4.0 points at N = 64 on hard multiple choice while lowering accuracy on 56.6% to 65.7% of individual problems (lit-2608.11403). In trained-model SWE work, majority voting plateaus at 39 to 40% against 43.6% for test-based selection at 32 (lit-2512.13607 section 7.4).

## 2. Gap 1: action-level and per-step voting

| Source | What is voted | Model | Measured | Where | Confidence |
|---|---|---|---|---|---|
| lit-2511.09030 MAKER | one-step answer, exact match, first to lead by k | gpt-4.1-mini main; others in Fig. 6(b) | per-step error 0.0022 (tau 0.1) and 0.0040 (tau 1.0) for gpt-4.1-mini; k_min 3 and 4; 20-disk Hanoi with zero errors | Fig. 6(b), section 4.4 | medium: HTML extract; run cost not seen |
| same, smaller models | | gpt-oss-20B error .0358, k_min 6; gpt-4.1-nano .3571, k_min 29; Llama-3.2-3B 1.0 | | Fig. 6(b), App. E | medium; what "1.0" measures is not defined in the text I saw |
| lit-2602.12276 CATTS | next browser action, majority of N | gpt-oss-120b | WebArena-Lite 38.8 (N=1), 42.4 (5), 43.2 (10), 43.0 (20); Online-Mind2Web 22.6, 20.2, 17.9, 15.1 | Table 1 | medium; Table 1 and App. H disagree at N=20 (43.0 vs 43.8) |
| same, gated | arbiter only when vote margin or entropy is low | | margin-gated 47.9 at 405K tokens vs majority 42.4 at 460K; Online-Mind2Web entropy-gated 32.0 vs majority 20.2 | Table 3 | medium |
| lit-2402.13212 Soft-SC | exact-match vote of k actions | CodeLlama-34B | Bash 27.1 greedy, 28.7 SC; WebShop 16.0, 18.0; ALFWorld 18.7, 20.5 at k=10; no majority in 86% of Bash steps at k=5 | main table, footnote 2 | medium |
| lit-2602.11619 | not a vote; run-to-run action divergence | 4 unnamed models | 2.3 to 4.2 distinct action sequences per 10 runs; divergence at step 2 in 50.5% of Llama tasks | abstract page | low: abstract only |

What this says:
- The only demonstrations of per-step voting that works are MAKER (exact-checkable answer, per-step error about 0.2% to 0.4%) and a web agent with a large model (+4.4 points WebArena-Lite from N = 1 to 10, flat after, negative on a second benchmark).
- MAKER's cost formula is `c * s * k_min / (v(2p - 1))` (Eq. 19, [S]): votes per step diverge as p approaches 0.5. gpt-4.1-nano at p about 0.643 needs k_min = 29 (Fig. 6(b)), and the 3B model is at zero. The per-step success rate of the E4B on "pick a correct next repair move" is unknown here, and a repair step has no exact-match answer to check. [I]
- Mutable shared workspace: I found no source that tests it. MAKER passes the whole state through the prompt and mutates nothing until the vote ends; CATTS votes before a browser action and is scored at the end of the task. In our harness a voter has no tools, so the workspace is never touched by voting itself; the risk is in what the actor does with a wrong winner, which no source measures. [I]
- Self-consistency on actions has a known failure: exact-match over free-form text rarely matches (86% of Bash steps have no majority at k=5, lit-2402.13212 footnote 2). The lettered list is the standard remedy for this and it is what EXP-039 uses; it moves the problem to the proposer.
- SWE: the SWE-bench items I opened vote on finished patches (lit-2512.13607, lit-2407.21787, lit-2026-11-05-architecture-families section 3), not on actions.
- Not opened (search summaries only, so unverified and not used for any number): RCAgent (arXiv 2310.16340, reported as sampling only at finalisation and keeping greedy decoding for earlier steps). A search result described arXiv 2603.25764 as voting on trajectories in astropy tasks; that was wrong when I opened the abstract (it is a submit-versus-resolve study of 50 SWE-bench Verified tasks and says nothing about voting).

## 3. Gap 2: agreement of a same-model vote over an enumerated list

No direct measurement found. What exists:
- CATTS App. J, Fig. 7 [S, medium]: WebArena-Lite, N = 10, free-form web actions, gpt-oss-120b: mean top-1 vote probability 0.762; about 42% of steps above 0.9; about 40% of steps zero entropy (unanimous); about 49% above 0.6 normalized entropy. Not reported: how often the majority differs from the first or greedy sample.
- Soft-SC footnote 2 [S, medium]: free-form Bash, k = 5, no majority 86% of the time. This is what an enumerated list avoids.
- Zheng et al. (lit-2309.03882) [S, medium]: letter choice among four options has a model-specific letter prior. Default RStd on MMLU: llama-2-7B 23.0, llama-2-13B 7.5, llama-2-70B 4.1, vicuna-v1.3-7B 5.3, falcon-inst-7B 28.7, gpt-3.5-turbo 5.5 (Table 3). Models of 2023; nothing from the Gemma family.
- lit-2608.11403 [S, low-medium]: voting on 7B and 8B models raises aggregate accuracy 0.342 to 0.369 and 0.273 to 0.313 at N = 64 while 56.6% and 65.7% of problems get worse; the agreement-gate and entropy-gate did not recover the lost accuracy.
- lit-2604.03809 [S, low]: same-model role-prompted agents, rationale cosine similarity 0.888 (nomic) and 0.908 (mxbai), effective rank 2.17 of 3.0.

Inference [I]: a voter answering with one letter samples from the model's next-token distribution over A to D at its own temperature. At low temperature the plurality of many such samples is that distribution's mode, which is the greedy letter; voter 1 at 0.2 is close to greedy. So the vote can differ from voter 1 only where the top two letters are close in probability or where high temperature flattens the distribution; the flips caused by flattening are noise. The voters share one instruction, one candidate order and one letter prior (Zheng), so their agreement is not independent evidence. If the proposer lists its preferred candidate first, A is both the proposer's pick and the likeliest letter prior; D = 0 then does not show that the vote is useless, only that it repeats the proposer.

## 4. Gap 3: temperature-diverse against prompt-diverse voters

- Prompt-diverse (lit-2310.07088, medium): GPT-4 zero-shot CoT, graph coloring: SC-3 18.0, SC-10 23.0, Div-Se 97.0; Blocksworld 4/5: SC-10 41.2, Div-Se 69.6 (Table 1). GPT-3.5 zero-shot AQuA: SC-5 63.37, Div-Se 72.83 (Table 2). LLaMA-2 70B AQuA few-shot: CoT 29.1, Div-Se 39.9 (Table 3). Personas alone as a single prompt: +4.33 and +8.27 points on AQuA with GPT-3.5 (Table 4). Caveat: members generate a different method per question; there is no temperature-only control; SC at T = 0.7, others at T = 0 (section 3).
- Persona or role prompt alone (lit-2604.03809, low): three same-model agents, similarity 0.888.
- Temperature range: no isolated evidence of diversity from a spread; the safe-range evidence is Renze and Guven (lit-2402.05201): no significant effect from 0.0 to 1.0 across nine models (GPT-3.5 CoT H(10) = 10.439, p = 0.403), rapid drop after 1.0, incoherent text at 1.6 (section 3.1). Llama 2 7B Chat did no better than chance (39% malformed, 36% well-formed and wrong). MAKER found the same model's per-step error 0.0040 at temperature 1.0 and 0.0022 at 0.1, k_min 4 against 3 (Fig. 6(b)), and runs its votes at 0.1 after a first vote at 0 (section 4.4). Soft-SC samples at 0.7 and 0.9.
- For EXP-039's 0.2 to 1.4 spread with 16 voters in equal steps of 0.08, voters 12 to 16 (five) lie above 1.0 [I]. Whether the E4B degrades at 1.2 to 1.4 on a one-letter task is unknown; the first screen records the malformed rate by temperature and answers it at no extra cost.
- The most direct statement for our case: no source varies temperature alone against prompt alone on the same small model at matched N. The two sides are lit-2310.07088 (for prompts) and MAKER's low-temperature practice.

## 5. Gap 4: small models, N of 8 to 32, cost against a stronger pass

| Quantity | Value | Source |
|---|---|---|
| Nemotron 8B, trained, Agentless, SWE-bench Verified | best@32 43.6 (from 39.2 at k=2), pass@32 57.7, majority voting plateaus at 39 to 40 | lit-2512.13607 section 7.4 (Fig. 12; read as extracted) |
| Llama2-13B, HumanEval, N = 40, BLEU voting | 0.14 to 0.18 | lit-2402.05120 Table 2 |
| Llemma-7B at 32 samples, MATH500 / GSM8K | majority vote 41.0 / 80.0; reward-weighted 43.5 / 85.4 | lit-2408.00724 Table 4 |
| 7B against 34B at equal FLOPs | the 7B wins until 128 samples | lit-2408.00724 section 1 |
| Web agent, N = 1 to 20 | gains flat after 10; a second benchmark declines 22.6 to 15.1 | lit-2602.12276 Table 1 |
| Qwen2.5-7B and Llama-3-8B, GPQA Diamond, N = 64 | aggregate +2.7 and +4.0 points (0.342 to 0.369; 0.273 to 0.313, my subtraction); 56.6% and 65.7% of problems worse | lit-2608.11403 |
| Weak model, 5 samples against one stronger-model sample | the weak model's coverage of issues exceeds single Claude or GPT samples (coverage, ground-truth tests) | lit-2407.21787 section 1 |

Saturation by this evidence: the voting gain with an inexpensive selector stops at about 5 to 10 samples for agents (CATTS) and at a few samples for patch voting (lit-2512.13607); verifier-based selection keeps rising to 32 (Nemotron) and to 100 samples (lit-2407.21787). Cost against a single stronger pass in wall-clock: nothing found; the FLOPs-matched result (lit-2408.00724) uses a trained reward model, and the one stronger-pass comparison for SWE (lit-2407.21787) uses test-based coverage.

## 6. What the evidence predicts

### (a) The one-vote-point screen (V1), against EXP-039 section 4
- Will voters agree? Probably in many tasks: CATTS has about 40% of steps unanimous for free-form actions at N = 10, so a four-letter list should be at least as concentrated [I]. My expectation: 3 or more of 8 tasks unanimous, and the contested tasks are where D comes from. Confidence: low; no same-model, same-list number exists.
- Will the winner differ from voter 1? It can only do so where the letter distribution is close or where the hot voters add noise [I]. The pre-registered 60% for D >= 1 is not contradicted; I would not raise it, because letter bias (Zheng) and the "proposer lists its preferred first" mechanism both work toward the vote repeating voter 1.
- Row 2 (D = 0) is the more likely reading if the proposer's candidates are near-duplicates; the pre-registered 20% looks a little low given that same-prompt self-consistency adds only 1.6 to 2.0 points over greedy on three agent benchmarks (lit-2402.13212 main table, my subtraction). This is my reading, not a source statement.
- Does the actor follow the tally (A >= 6 of 8)? No source on a 4B model counting 16 letters; MAKER and CATTS tally in code. This is the weakest link and sits outside the lit.

### (b) Per-step voting on a 4B model
Not supported. The two successes (MAKER, CATTS) need either an exact-checkable answer with per-step error near 0.4% or a large model; with p below 0.65 MAKER needs k of 29 or more (gpt-4.1-nano), and a 3B model scored error 1.0. CATTS shows the web-agent gain flattening by N = 10 and reversing on a second benchmark; Soft-SC shows exact-match SC adding about 1.6 to 2.0 points on three agent tasks. For a 4B model I found no positive result. At N = 16 and about 4.7x single-loop wall (EXP-039 section 2 Q5) it is also the costlier option.

### (c) The one design change with the best support
A margin rule on the tally, which is the expressible form of first-to-ahead-by-k: the actor applies the leading letter only if it leads the runner-up by at least k votes (start with k = 3), otherwise it applies voter 1's pick. Support: MAKER's whole mechanism is a lead of k (Algorithm 2; k_min 3 and 4 at p about 0.998, Fig. 6(b)); CATTS finds vote margin or entropy is the signal that tells when extra compute helps, and margin-gated arbitration beat plain majority by 5.5 points at fewer tokens on WebArena-Lite (47.9 against 42.4, Table 3) while overrides of a high-consensus vote were followed by lower task success (46.9% with none, 35.0% with at least one, p = 0.026, section 4.1). Mehta (lit-2602.11619, abstract only) reports that answering only when 3 runs agree gave 87 to 88% accuracy at 54 to 62% coverage. Confidence: low to medium; the fallback to voter 1 is my choice and no source tests it.

**How to use it without breaking the pre-registered readings.** Applying the margin rule inside the smoke-8 would change what D measures: by the inference in section 3 the plurality differs from voter 1 only in close-lead tasks, and the rule reverts exactly those to voter 1, so D would fall toward 0 and row 2 (the kill condition) could fire for a reason unrelated to voter agreement. So, in the screen, record the lead (top count minus runner-up count) as a quantity only. It is a pure function of the 16 vote texts, like the tie rule, so it is recomputed offline at no cost, and D can be reported split by lead (under 3, 3 or more). Apply the rule as a rule only in a later arm, if D >= 1 shows that close-lead tasks exist.

Not chosen, with reason: prompt-diverse voters have the largest measured effect (lit-2310.07088) but on reasoning chains with per-question generated prompts, and the counter-evidence (lit-2604.03809) is for personas; a red-flag filter is already in the design (a malformed vote counts for nothing; 256 tokens against MAKER's 750).
A parameter correction, not a design change: the two sources on temperature both argue against the top of the 0.2 to 1.4 spread (Renze section 3.1; MAKER Fig. 6(b)). Cap it at 1.0, or record the malformed rate by temperature bucket in the screen.

### (d) What I could not find
1. Any vote on the next action of a repository-repair agent, with a shared mutable workspace. No source.
2. A same-model vote's agreement rate over options the same model wrote, or its rate of differing from greedy. Only the free-form CATTS App. J figures and 2023 letter-bias numbers.
3. A temperature-only against prompt-only comparison on a small model at matched N, and any number for Gemma 4 at temperature above 1.0.
4. Wall-clock cost of voting against one stronger pass in an agentic task.
5. Opened only in part or not at all: MAKER's Appendix D vote-round distribution, the 20-disk run's cost, Appendix F detail; CATTS Appendix N; Mehta (abstract only); lit-2604.03809 (abstract only). Not opened, so no numbers used: Universal Self-Consistency (arXiv 2311.17311; the search summary gave no small-model numbers), Self-MoA (2502.00674), Hegazy et al. on multi-model debate (2410.12853, model diversity, not prompt diversity), Panickssery et al. self-preference (2404.13076; search summary says the bias scales with self-recognition), RCAgent (2310.16340), "Does Inference Scaling Improve Reasoning Faithfulness" (2601.06423). The search-engine claim that Llama 3.1 70B at temperature 0.0 has 2.2 distinct trajectories against 4.2 at 0.7 is not on the Mehta abstract page; unverified.
