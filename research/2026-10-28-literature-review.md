# Literature and industry review — SWE-style coding agents under a fixed small model and a hard time budget

**Date:** 2026-10-28. **Method:** ten web searches (standard and extended modes) run in one pass, plus follow-up
reads of the abstracts and summaries they surfaced. No paper was read in full; every number below is as
reported by the source cited, and secondary sources are marked. Companion document:
`research/2026-10-28-kaggle-open-scouting.md` (the competition-specific, public-bundle evidence). The question
this review serves: **which levers exist for a declarative-only agent config (prompt, caps, sampling, ADK agent
tree, optional LoRA) driving a fixed 31B INT4 model through a fixed six-tool harness under a ~12 h / ~120-task
budget**, and which of them the evidence says to skip.

Our own measured problems, for reference (all from `experiments/`): 96% of dev-48 tasks run to the 4.5-min cap
(EXP-025 Arm A); 40% empty patches; the discriminating variable between scoring and not is the turn of the first
edit (18 vs 43, EXP-009); `edit_file` calls fail as unterminated string literals on ~18% of calls at thinking 4096
(EXP-003/EXP-026) and the model then retries identically; nine LB draws of prompt surgery have not moved the score.

---

## 1. Trajectory and failure-mode studies (academia)

| finding | source | relevance to us |
|---|---|---|
| 35–40% of failed SWE-bench Verified trajectories never reach the correct files, and those failures are **no shorter** than successful localizations — wasted effort on wrong paths, not early quitting | *Understanding Code Agent Behaviour* (arXiv 2511.00197) | Localization matters, but the fix is cheap discipline (one specific grep), not graph tools; our recall check already showed graph tools lose to grep at every k |
| Agents often **reach the correct code and then overwrite or thrash it**; in 5 cases a mid-trajectory patch matched gold and an "edit-commit checkpoint" recovered all 5 | *Coherence Collapse* (arXiv 2603.24631) | Supports "edit, one check, one repair, submit" over open-ended re-investigation after the first edit (our prompt permits the latter) |
| Empty patches typically follow **repeated invalid edits, parse failures or cyclic tool use**; a structured action space cut GPT-5-nano's empty patches 233 → 36 with a +20.8 pp accuracy gain, while Qwen3-8B's empty patches fell 179 → 138 with **no** accuracy gain (reasoning-limited) | CODESTRUCT (arXiv 2604.05407) | Our `edit_file` loss + identical retry is exactly the interface-failure class; the single-argument `run_command` heredoc route (EXP-026) is the declaratively reachable analog of a structured action space. Also a warning: some empty-patch reduction converts to zero resolves |
| 10.7% of **passing** OpenHands trajectories show blind retries, regression cycles or missing verification; "lucky pass" rates 0.5–23.2% across backends | AgentLens (ICML 2026) | LB noise has a mechanistic floor; one draw cannot adjudicate a prompt change (consistent with our ~4-task MDE) |
| Empty-patch rate and loop rate are reported as first-class metrics; runs capped at 30 turns / 32k context | SEAlign (arXiv 2503.18455) | Validates our metric choice (EXP-009 switched primary outcomes to empty-patch rate and first-edit turn) |
| Mid-training on a 14B model cut no-patch failures from ~11 to ~1 per run | Function-aware FIM mid-training (arXiv 2607.12463) | Training-side; out of reach for us (see §5) |

**Gap:** no source tests a *time* budget or an early-edit-commitment policy as an intervention on small models.
Our EXP-010/EXP-017 first-edit deadline and the rank-3 team's "edit by call 12" are, as far as this search found,
ahead of the published literature on that specific point.

## 2. Scaffolds and action spaces

- **Minimal scaffolds win at the frontier.** mini-SWE-agent (a ~100-line bash-only ReAct loop, no tool schema) is
  the SWE-bench team's own evaluation harness; secondary reports put Claude Sonnet 4 at ~65% and Gemini 3 Pro at
  >74% on Verified through it, and a vals.ai archive lists Opus 5 + mini-SWE-agent first at 97% (September 2026).
  Scaffold choice moves a frontier model's score by several points (Opus 4.5: 76.8–80.9% by framework, per
  codesota). Sources: swebench.com/bash-only, mini-swe-agent docs, vals.ai archive, codesota leaderboard.
  **For us:** the harness fixes the scaffold, but the lesson transfers to the prompt: shorter, fewer rules, one
  path. The 0.24 prompt is 3,240 bytes; ours was 12,795.
- **Agentless** (arXiv 2407.01489): localize → repair → validate, no agent loop; samples several candidate
  diffs, filters syntax errors, selects by regression tests and self-written reproduction tests. Its *pipeline*
  is not expressible in one declarative agent with a shared `/workspace`, but its *selection signals* are the
  reference for any future best-of-N design (see §4).
- **Structured action spaces** (CODESTRUCT, §1) reduce interface failures for small models. In our harness the
  action space is fixed; what we control is which tool the prompt routes an edit through after a failure.

## 3. Edit formats and edit-tool reliability (industry)

- Aider's benchmark: switching GPT-4 from strict unified diff to search/replace blocks raised its edit-benchmark
  score 26% → 59% with no model change ("Unified diffs make GPT-4 Turbo 3× less lazy", via agentpatterns.ai
  summary). A separate benchmark the same summary cites (Diff-XYZ) found **search/replace beats unified diff
  for larger models while small open models gain almost nothing from any format change.** Aider defaults
  lesser-known models to the **whole-file** format "since it is the easiest format for an LLM to use"
  (aider.chat/docs/more/edit-formats.html, aider.chat/docs/llms/editing-format.html).
- Industry reports on str_replace-style tools are bug reports, not measurements: Claude Code's Edit rejecting
  multi-line matches that are in the file (dev.to), Cursor agents failing a targeted edit and then rewriting the
  whole file (forum.cursor.com), Copilot replace reporting success without writing (CopilotForXcode #628), Cursor
  StrReplace truncating >8 MiB files (forum.cursor.com). Summer Engine's design: str_replace for small edits, a
  separate tool for large ones, file writes only for new files.
- **For us:** `edit_file` *is* search/replace; the failure we measured is not anchor matching but the model
  emitting an unterminated string literal in the Gemma 4 tool-call syntax (`new_string` ends in `ng:` on
  200/201 lost calls). No format change inside `edit_file` fixes that. `write_file` (whole-file) sidesteps the
  multi-argument slip for small files at the cost of truncation risk on large ones; `run_command` with a quoted
  heredoc is the single-argument route and is what EXP-026 ships. The rank-3 team's `calls_by_kind` shows
  `edit_cmd` (shell edits) at 1–3% of calls — they use that route occasionally, unprompted.

## 4. Test-time scaling and candidate selection

- Pass@k rises monotonically with k; **majority voting saturates early** (Nemotron-Cascade, arXiv 2512.13607,
  which ranks k patches by regression-test passes, then curated reproduction tests, then majority vote, then
  patch length). Satori-SWE (arXiv 2505.23604): 32B Best@50 = 41.6 on Verified using a reward model plus unit
  tests. SWE-World (arXiv 2602.03419): 55.0 at K=1 → 68.2 at TTS@8 with a verifier. Trae: an LLM-as-selector
  **peaks at 5–6 candidates and then declines**. Verifier survey (mdpgroup summary): execution-based and
  execution-free verifiers each plateau ~42–43% on a 32B model; hybrid 51%.
- **For us:** EXP-006 measured 88.6% idle KV capacity at 31B and EXP-007 confirmed ADK `ParallelAgent` gives real
  concurrency, so N independent attempts are physically affordable in wall-clock. What is missing is (a) a
  selection signal without hidden tests — the literature's answer (regression + self-written reproduction tests)
  costs the time we do not have, and majority vote on patches is weak; (b) isolation — all branches share one
  `/workspace`, so parallel *editing* branches are ruled out (plan.md §6.3). **Parked**, not dead: the one
  shape that fits is N read-only localizers feeding one editor, which attacks the §1 localization failure, not
  the empty-patch failure.

## 5. Training: SFT, RL and LoRA at the 32B class

- Full fine-tunes/RL on 32B bases reach 59–62% on Verified: OpenSWE-32B 62.4% (SWE-agent scaffold; arXiv
  2603.13023, self-reported), DeepSWE-Preview 59% (pure RL on Qwen3-32B; Agentica). Earlier: SWE-Gym, R2E-Gym,
  SWE-agent-LM-32B 40.2%, OpenHands-LM-32B 37.2%, Kimi-Dev 48.6% (already in plan.md §6.2). All use thousands of
  verified trajectories or synthetic environments (daVinci-Env, SWE-smith, R2E-Gym) and **full fine-tunes**; none
  report LoRA numbers.
- The one LoRA data point at our exact model and harness is negative: the rank-3 team trained three adapters
  (SWE-smith all-output, SWE-smith actions-only, SWE-rebench actions-only) and **lost ~11 points locally** (v20
  adapter 28.3% vs v20_base 39.1%; v21 19.6% with 54% empty patches). Details in the scouting document.
- **For us:** deprioritize LoRA. The recipes that work need data and compute we do not have, and the one
  same-model trial hurt. plan.md §6.2's gold-patch-derived LOCATE adapter remains the only evidence-grounded
  variant, and it attacks the smaller problem.

## 6. The model and the serving stack

- **Gemma 4 31B:** no official SWE-bench Verified figure found. Independent: vals.ai 53.9% on a Verified subset;
  benchlm SWE-rebench 41.6%; a secondary guide quotes ~63 against the model card loosely. LiveCodeBench v6 80.0%
  and Codeforces ELO 2150 are on the card (aurigait summary). **Reading:** the model is capable of far more than
  8/58; our gap is harness, budget and interface, not capability.
- **vLLM gemma4 tool parser** has open and recently fixed defects: streamed tool arguments corrupted
  (vllm #38910, HTML-like content in `write_file` content), streaming failures under concurrency producing
  invalid JSON arguments (#42696), bare values returned as strings (#47906 / PR #47909), raw `<|` `|>` tokens
  leaking (#44522), openers that omit `call:` (PR #54778). A third-party guide recommends testing non-streaming
  first and keeping argument schemas shallow. **Reading:** our unterminated-literal loss is consistent with
  argument corruption in the parser path, not only with model slips; the harness pins the vLLM build, so the
  only reachable mitigation is routing long edits through a single-argument call.
- The error string we see (`mandatory input parameters are not present`) is emitted by the ADK/harness tool
  layer, not vLLM — no web hit for it.

## 7. The competition's public discussion

The Kaggle discussion pages (main and paper track) show threads on a $10k small-model bonus, "Kaggle Error"
submissions and queue delays, the new 12B/E4B/E2B sizes, and a paper-track post on context resets for stuck
agents (96% vs 16% on a 25-task "Trap-25" benchmark). No thread contents on prompts, caps or `agent.yaml` were
retrievable by search. Third-party summaries disagree on deadlines (Nov 2 vs Nov 25 entry; Dec 2 close); the
live rules page, read 2026-10-17, is authoritative: entry/merger Nov 25, final Dec 2 (plan.md §1.2).

## 8. What this review says we should do, in order

1. **Adopt a short, early-committing prompt and give it the time budget it was written for.** The one
   published config that scored 0.24 on this hidden set is 3,240 bytes with an 8-min cap, and our own run of it
   at 4.5 min scored 7/58. Submitted as #11 (EXP-027). This is the only lever with a one-variable contrast behind it.
2. **Add the single-argument edit route for the measured `edit_file` loss**, as a short section, tested as a
   paired dev-48 arm on top of the adopted tree (EXP-027 §6 item 1). §1 and §6 above both support it.
3. **Re-derive the time gate from measured means, not caps**, once a dev-48 run of the adopted prompt exists;
   test `max_tool_calls` 28 → 40 (their unscored v25) in the same run.
4. **Park** LoRA (§5), best-of-N (§4, no selection proxy), graph tools (recall check), and any further surgery on
   the 12.8 KB prompt lineage (nine flat draws).

## 9. Gaps this search did not close

- No study isolates time caps or forced early edits as interventions on small models.
- No controlled str_replace vs whole-file failure rates for any model.
- No independently verified SWE-bench Verified number for Gemma 4 31B, and nothing on its tool-calling accuracy.
- Nemotron-Cascade's ablation of reproduction-test selection vs majority vote (its Figure 12) was not read.

## Sources

Academia: [Understanding Code Agent Behaviour, 2511.00197](https://www.alphaxiv.org/overview/2511.00197) ·
[Coherence Collapse, 2603.24631](https://www.alphaxiv.org/abs/2603.24631) · [CODESTRUCT, 2604.05407](https://arxiv.org/pdf/2604.05407) ·
[AgentLens, ICML 2026](https://icml.cc/virtual/2026/77962) · [SEAlign, 2503.18455](https://arxiv.org/pdf/2503.18455) ·
[FIM mid-training, 2607.12463](https://arxiv.org/pdf/2607.12463) · [Agentless, 2407.01489](https://arxiv.org/html/2407.01489v2) ·
[Nemotron-Cascade, 2512.13607](https://arxiv.org/pdf/2512.13607) · [Satori-SWE, 2505.23604](https://arxiv.org/pdf/2505.23604) ·
[SWE-World, 2602.03419](https://arxiv.org/pdf/2602.03419) · [Thinking Longer, Not Larger, 2503.23803](https://arxiv.org/html/2503.23803v1) ·
[OpenSWE-32B / daVinci-Env, 2603.13023](https://arxiv.org/pdf/2603.13023) · [SWE-Dev, 2506.07636](https://arxiv.org/pdf/2506.07636) ·
[SWE-RL, 2502.18449](https://arxiv.org/pdf/2502.18449) · [Can Old Tests Do New Tricks, 2510.18270](https://arxiv.org/pdf/2510.18270) ·
[Gemma 4 Technical Report, 2607.02770](https://arxiv.org/pdf/2607.02770)

Industry and leaderboards: [SWE-bench Bash Only](https://www.swebench.com/bash-only.html) · [mini-SWE-agent](https://docsearch.algolia.com/mcp/docs/repo/swe-agent/mini-swe-agent) ·
[vals.ai SWE-bench archive](https://www.vals.ai/benchmarks/swebench-2025-09-24) · [codesota SWE-bench](https://codesota.com/browse/agentic/swe-bench) ·
[Trae product update](https://www.trae.ai/blog/product_update_0528) · [DeepSWE / Agentica](https://thursdai.news/companies/agentica) ·
[verifier write-up (mdpgroup)](https://mdpgroup.com/?p=26259) · [aider edit formats](https://aider.chat/docs/more/edit-formats.html) ·
[aider editing format per model](https://aider.chat/docs/llms/editing-format.html) · [edit-format selection summary](https://agentpatterns.ai/tool-engineering/llm-edit-format-selection/) ·
[Claude Code Edit rejections (dev.to)](https://dev.to/terminalblog/beware-claude-codes-edit-tool-rejects-strings-that-are-in-the-file-o1a) ·
[Cursor: whole-file rewrites after failed edits](https://forum.cursor.com/t/a-way-to-reduce-whole-file-rewrites-after-failed-llm-edits/167947) ·
[Cursor: StrReplace truncation](https://forum.cursor.com/t/agent-strreplace-truncates-files-8-mib-silent-data-loss/166573) ·
[CopilotForXcode #628](https://github.com/github/CopilotForXcode/issues/628) · [Summer Engine 0.4.2](https://www.summerengine.com/changelog/0.4.2.md)

Model and stack: [vals.ai Gemma 4 31B](https://www.vals.ai/models/google_gemma-4-31b-it) · [benchlm Gemma 4 31B](https://benchlm.ai/models/gemma-4-31b) ·
[aurigait Gemma 4 guide](https://aurigait.com/blog/gemma-4-features-benchmarks-guide/) · [vLLM #38910](https://github.com/vllm-project/vllm/issues/38910) ·
[vLLM #42696](https://github.com/vllm-project/vllm/issues/42696) · [vLLM #47906](https://github.com/vllm-project/vllm/issues/47906) ·
[vLLM #44522](https://github.com/vllm-project/vllm/issues/44522) · [vLLM PR #54778](https://github.com/vllm-project/vllm/pull/54778) ·
[vLLM gemma4_tool_parser docs](https://docs.vllm.ai/en/latest/api/vllm/tool_parsers/gemma4_tool_parser/) ·
[Gemma 4 tool-calling troubleshooting](https://gemma4home.pro/blog/gemma-4-tool-calling-troubleshooting-ollama-vllm-opencode) ·
[HF forum: Gemma 4 bug fixes](https://discuss.huggingface.co/t/gemma-4-bug-fixes-and-research-request/176979)

Competition: [main-track discussion](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion) ·
[paper-track discussion](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion)
