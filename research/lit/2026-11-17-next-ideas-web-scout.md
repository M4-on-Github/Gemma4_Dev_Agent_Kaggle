---
id: 2026-11-17-next-ideas-web-scout
title: "Web scout for the known 31B faults: two ideas with some evidence, and what was not found"
authors: "web scout over arXiv abstract pages, a JetBrains paper, the SWE-agent paper and two blog posts"
year: 2026
url: "see Evidence lines"
topics: [prompt, budget, edit-reliability]
relevance: medium
read: partial
date_added: 2026-11-17
---

Scope and reading status. The fault map is `2026-11-17-run-synthesis-model-faults` (takeaway and ranked table read). Sources were read through a fetch extractor, mostly as arXiv abstract pages, not as full text, and no number was recomputed. Anything I could not see is marked "unknown". Papers and posts only propose hypotheses. I excluded everything on the already-tried list. Only two ideas met the bar of having some outside evidence; I did not pad to three.

## Takeaway

1. **Multi-location completeness has well-documented failures and no measured prompt-only remedy.** I found three sources that describe the fault, and none that tests a "find the other sites" instruction in a paired ablation. Idea 1 is therefore a mechanism-level proposal with an offline test that can kill it for free.
2. **Observation size has the best measured evidence, but it buys time, not calls.** It targets the compaction cost and the time gate, not the 28-call cap directly.

## Idea 1 (rank 1): a sibling-site sweep and a requirements list in the one prompt, for partial fixes

- **Fault and tasks at stake.** Rank 1 and 2 of the fault table: C (partial fix) 13 in R and 11 in RH, and R (right file, wrong region) 6 and 5. The sub-class that a sweep could reach is "all gold files touched, a region missed" (5 and 5) and "a whole gold source file never touched" (8 and 6, synthesis section 1.3). 20 of the 24 C losses are on tasks with 3 or more gold regions, so the realistic pool is the 2-to-3-region band (5 of 18 resolve at 2 regions). I do not estimate a gain.
- **Change in our terms.** One prompt rule in `prompts/swe_coder.md`, repo-agnostic and without package, network or URL words. Before the first edit, list in one line each place the issue implies must change. After the last edit and before the final answer, run one `grep -n` for the identifier or literal you changed, across the repo's source, and for each hit state "same change needed" or "not needed". This is a count-the-sites step, not a test run. It does not rely on the check passing.
- **Evidence, and how thin it is.**
  - Beyond Accuracy: Behavioral Dynamics of Agentic Multi-Hunk Repair, arXiv 2511.11012 (abstract page). Claude Code, Codex, Gemini-cli, Qwen Code on 404 multi-hunk bugs (372 Java, 32 Python from SWE-bench Verified), 1,616 trajectories. Agents can name every file to change and still write a wrong patch; accuracy falls as hunk divergence rises; Qwen Code's repair accuracy is the lowest at 26.98%; failed repairs use 33% to 440% more input tokens. No prompt intervention on completeness. The only intervention named is a repository-context tool (Maple, +21% for Gemini-cli), which needs a tool we do not have. Not paired, mostly Java, not 30B open-weight except Qwen Code (model size unknown).
  - Blog: ai-muninn, Qwen 3.6 35B-A3B on SWE-bench Lite (https://ai-muninn.com/en/blog/swe-bench-qwen36-failure-modes). 145/300 resolved; of 155 unresolved, 21 (13.5%) were self-classified "incomplete_patch". Self-labelled by the model in one pass; no intervention measured.
  - Search-snippet claim, not verified: HarnessX (arXiv 2606.14249) reports "incomplete fix" at 62% of SWE-bench Verified failures. The abstract page I fetched does not mention it; treat as unconfirmed.
  - Coherence Collapse (arXiv 2603.24631, existing note `lit-2603.24631`): on strong models 60-69% of failures edit the correct functions and still produce a wrong patch. Same direction.
- **Why it is not already tried.** It is not verify or test-before-submit (EXP-055/057, C-019 pool analysis): the check can pass while a sibling site is wrong (8 and 13 of the losses pass their last check). It is not a localizer stage (EXP-032) and adds no sub-agent. `2026-11-17-run-synthesis-model-faults` section 1.3 lists "a prompt step that lists the other definitions and call sites after the first edit" as named for the E4B in EXP-074 section 6.5 and never screened on either model.
- **Cheapest test.** Rung 1, trace mining at 0 GPU, which can reject the idea. For each of the 24 C-class runs (R and RH), take the gold hunks the agent missed and test whether any identifier or literal from the agent's own removed or added lines appears in those hunks. That is "recoverable by a grep of the edited token". Suggested reading (mine, to pre-register before running): fewer than 6 of 24 recoverable, drop the idea; 10 or more, run a smoke-8 on 2-to-3-region C tasks, with the endpoint the count of gold regions touched in the final patch (a process measure), not resolves, since smoke-8 reads at most about 2 tasks of room.
- **Risk (mine).** The model may run the grep and answer "not needed" for every hit; that would show as sweep calls with unchanged region counts. It also spends 1 to 2 calls of the 28.

## Idea 2 (rank 2): bounded observations, to defer compaction and buy time for a higher call cap

- **Fault and tasks at stake.** Rank 6 and 7 (empty at the cap: 3 and 3 plus 3 and 2) and the six small-gold tasks cap-bound in both R and RH. The synthesis says a higher cap costs time (about 40 calls adds an estimated 1.6 h against 10.04 h projected and an 11 h gate) and that compaction fires about once per task at 14,336 prompt tokens, costing an estimated 30 to 38 s each. Two or more compactions: 12 tasks in R, 13 in RH, 8 and 12 of them capped. This idea does not raise the cap; it only frees time that a cap change would spend.
- **Arithmetic (mine, an upper bound).** Removing one compaction on every task saves 120 x 30 s to 120 x 38 s = 1.0 to 1.27 h. That covers most of the 1.6 h estimate only if every compaction is avoided, which is unlikely. A realistic saving is a fraction of it.
- **Change in our terms.** A prompt rule on read and search sizes: read a window of lines (the harness `read_file` takes a path only, per Q1; ranged reads would go through `run_command` with `sed -n 'A,Bp'`) rather than a whole file once the target is known, and pipe search output through `head`, or list files and hit counts before lines. This changes no tool. It is a prompt line that adds about 1 to 2 sentences, which itself costs prompt tokens (mine).
- **Evidence.**
  - SWE-agent, arXiv 2405.15793, Table 3 (read via the HTML version): GPT-4 Turbo, SWE-bench Lite, 300 instances, baseline 18.0% (54/300). File viewer 100 lines 18.0; 30 lines 14.3 (-3.7); full file 12.7 (-5.3). Search: summarized 18.0, iterative 12.0, none 15.7. Context: last 5 observations 18.0, full history 15.0. Single run, unpaired, GPT-4 Turbo, so the direction is the only transferable part.
  - The Complexity Trap, arXiv 2508.21433 (JetBrains), SWE-agent on SWE-bench Verified, n = 500 per configuration, one run each, paired-bootstrap CIs (values not on the page). Observations are about 84% of an average turn. Observation masking (window 10) against the raw agent: Qwen3-32B 17.0% to 15.0% (cost $1.12 to $0.55); Qwen3-32B thinking 23.0% to 24.6% ($0.51 to $0.46); Qwen3-Coder (480B total, 35B active) 53.4% to 54.8% ($1.29 to $0.61). So the non-thinking 32B lost 2.0 points while halving cost. This masks old observations, which is different from shorter reads, so it does not test our rule.
  - Blog (https://ai-muninn.com/en/blog/swe-bench-lite-gemma4-26b-38-percent): Gemma 4 26B-A4B 116/300 on SWE-bench Lite; the page states no measured ablation, so it gives no evidence for this idea.
- **Why it is not already tried.** It is not a call-index rule or an early-edit rule. EXP-068/069/079 treated read form for the E4B only. On the 31B tree the synthesis finds 3 or more whole-file reads in only 3 of R's 23 capped runs, so for most capped tasks size is not the cause (16 of 23 have no repeats, no lost edits and no heavy reads). I expect a small effect on caps and the saving to come mainly from compaction time (mine).
- **Cheapest test.** Rung 1, trace mining at 0 GPU. From the R and RH traces, for each compaction record which call's observation pushed the prompt over 14,336 tokens and its size. Counterfactual: cap every read at 150 lines and every search at 50 lines and count tasks whose first compaction would move past call 28 or disappear. Pre-register: if fewer than 15% of tasks change, drop it. If it passes, a smoke-8 reading mean wall and compaction count, not resolves.
- **Risk.** The Qwen3-32B result shows a cost cut can lose resolves; a window rule can hide the line the model needs. The check is edits per window read.

## Runners-up, one line each

- Coherence Collapse mining (an agent reaching a resolving state, then rewriting it): already in `lit-2603.24631`; the 0-GPU test it names is not run. Source: https://arxiv.org/abs/2603.24631.
- Thinking cap near 1024 (63 to 3 long-thought episodes, WT unchanged, Aeterna): see `2026-11-17-paper-track-writeups` row 1; the test is the lost-call rate. Source in that note.
- MultiFixer (coordinator-proposer for multi-hunk, ASE 2026, arXiv 2607.26591): needs stages and Claude-3.5 or GPT-3.5, no per-component numbers on the abstract page; not applicable.
- REAgent issue-requirements preprocessing (+17.40% over five baselines, DeepSeek-V3.2, test-generation stages; as described on https://agentpatterns.ai/patterns/agent-design/issue-requirements-preprocessing/): multi-stage with generated tests; not a prompt line.
- LAGO decomposition ablation (30 against 26 of 50 on a SWE-bench Pro split, arXiv 2610.19843): a different system; the authors say it does not show decomposition is needed; read from a search snippet only.
- Step-limit and budget-prompt claims (ai-muninn posts, Gemma 4 26B and Qwen 3.6): unmeasured; they overlap the call-index tripwire already tried (EXP-010).

## Not found

- No paired ablation, on any model, of a prompt instruction to find and fix all occurrences or all call sites.
- No controlled study of chained shell commands or batching on a 30B-or-smaller model with calls per task (searched twice; one vendor claim, Tura, is self-reported and has no ablation).
- No open-weight multi-hunk study with a hunk-count breakdown I could read: the abstract page of 2511.11012 gives none.

## Ideas to test

- Grep-recoverability of missed gold regions on the 24 C runs; kill below 6 of 24.
- Observation-size counterfactual on compaction position; kill below 15% of tasks changing.

## Caveats

Evidence is thin and mostly from other models and scaffolds. The 31B's own failure counts come from the synthesis note and were not recounted here. SWE-agent's Table 3 is one GPT-4 Turbo run on Lite; The Complexity Trap's per-model values come from the extractor's table and I did not see the paired-bootstrap intervals.
