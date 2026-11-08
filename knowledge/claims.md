---
id: claims
updated: 2026-10-29
---

# Claims ledger

One section per claim, newest at the bottom. Only research-lead edits this file.
Status changes to `supported` or `refuted` require an experiment whose critic verdict is `accepted`.

**Migration note (2026-10-29).** C-001 to C-018 were migrated from `plan.md` §6, `experiments/README.md` §3,
EXP-009/016/022/024/025/026/027 and `research/2026-10-28-*.md`. No critic existed before this date, so every
migrated claim is `hypothesis` with its evidence under `migrated-evidence`; a backfill review (critic, `light`
or `full` on the cited EXP) is what moves it. Numbers are copied from the cited files, not re-derived.

<!-- Template:
## C-NNN: <one-line statement, falsifiable>
- status: hypothesis | supported | refuted | contested
- confidence: low | medium | high
- topics: [budget | prompt | edit-reliability | tools | sampling | lora | multi-agent | selection | noise | grading | paper | rules]
- expected gain: <tasks of 58, with P(success) and its source; or "none directly">
- sources: <lit-..., kg-..., EXP-..., submissions.md row N>
- tests: <EXP-NNN (critic verdict)>
- history: <YYYY-MM-DD status change and why>
-->

## C-001: Two uploads of one config differ by 3 or more public-LB tasks about 42% of the time, so the single-draw MDE is ~4 tasks (~0.07) and no one-draw move below that is an effect
- status: hypothesis
- confidence: high
- topics: [noise]
- expected gain: none directly. It sets what any upload can show, and it is a paper-track deliverable (the noise floor).
- sources: submissions.md rows 1 and 3 (E0 config: 4/58 then 7/58 with a 4.5 -> 4.0 min change expected to cost ~0.4 tasks); EXP-009 (Fisher p = 0.53, pooled 11/116); EXP-019 (exact score decoder, n = 58); kg-rank3-apache §2 (their v17 scored 0.17 and 0.13 on one config); lit-icml2026-agentlens (lucky-pass rates 0.5-23.2%)
- tests: EXP-005 and EXP-009 (no critic yet)
- migrated-evidence: plan.md §5.5 adopted the ~4-task MDE on 2026-10-21, replacing the +/-2 assumed before; EXP-022 §1.3 adds dev-48 run-to-run phi = 0.50 (two runs share 6 of 14 distinct resolves, Fisher p = 0.0023).
- history: 2026-10-29 migrated as hypothesis
- history: 2026-11-06 third LB draw of the v24-at-8 zip (S-013, ref 58037856, sha c22069db) scored 7/58 (0.12); EXP-031 section 9 row 3 (6306942); pooled three-draw baseline 28/174 = 0.161, Wilson 95% 0.114 to 0.223 (was 21/116 = 0.181); identical-byte draws 10, 11, 7, a 4-task range, sample sd 2.08 tasks; no effect read from the differences (EXP-031 section 5). Status not moved: no critic verdict.

## C-002: For the rank-3 v24 prompt, raising `max_time_minutes` from 4.5 to 8 moves the hidden-set score by several tasks, because the cap at 270 s kills the check-and-repair finish rather than the first edit
- status: hypothesis
- confidence: medium
- topics: [budget]
- expected gain: theta ~ 10/58 for the 8-min tree vs 7/58 at 4.5 (EXP-027 §3: +3.3 after removing their best-of-N selection; their 14/58 is a maximum of >= 12 uploads)
- sources: submissions.md row 8 (#8 = v24 at 4.5 min: 7/58); kg-rank3-apache §2-3 (v24 at 8 min: 14/58, Fisher p = 0.147 vs #8; 2-6 of their ~19 resolves per 46-task set finish after 270 s; first edits after 270 s: 0-1); EXP-023 §3 (confound stated before the score)
- tests: EXP-027 (#11, Kaggle ref 57750294, PENDING since 2026-10-28 22:39 UTC); EXP-028 Arm R (time profile only, T2 at 10.04 h; not a test of the score; critic light accepted)
- migrated-evidence: EXP-027 §4 holds the blind readings for #11 (blank -> 6.0 min next; k <= 8 -> adopt tree anyway, cap not the lever; 9-10 -> adopt as baseline; >= 11 -> adopt and re-run unchanged).
- history: 2026-10-29 migrated as hypothesis

## C-003: The v24 tree at 8 min / 28 calls completes ~120 hidden tasks inside the 12 h scoring budget
- status: supported
- confidence: medium
- topics: [budget]
- expected gain: none directly; a blank costs one slot (zero for that day). Precondition for C-002 and every later arm on this tree.
- sources: kg-rank3-apache §2-3 (v19 and v24 both completed and scored at 8 min; runs.jsonl mean 275-296 s, 15-24% at cap, proj_h@120 9.9-10.6 h with 0.7 h overhead); EXP-016 §3 (our ~10.5 h operational ceiling; #2 died at an 11.34 h projection that omitted fixed overhead); submissions.md row 2
- tests: EXP-027 (#11 pending); EXP-028 Arm R (T2: 10.04 h from mean 297.4 s plus measured overhead, no margin, about 0.6 h per SE; one RH task ran 751.9 s against the 8-min cap; critic light accepted)
- migrated-evidence: their prompt self-stops on 76-85% of tasks; ours ran to the cap on 79-96%, which is why `cap x 120` fit ours to 4% and overstates theirs by ~45% (EXP-027 §1c).
- history: 2026-10-29 migrated as hypothesis
- history: 2026-11-06 hypothesis -> supported: EXP-028 critic light accepted (b691244), T2 at 10.04 h with no margin (about 0.6 h per SE, critic's inference); #11 and #12 completed on the hidden set at this cap. The 8-minute cap is not a hard per-task bound (one RH task ran 751.9 s) and the projection does not model such overruns
- history: 2026-11-06 the v24 tree at 8 min / 28 calls completed on the hidden set a third time (S-013, ref 58037856, COMPLETE): 3 of 3 completions; one more observation, not a test (EXP-031 sections 1 and 9, 6306942).

## C-004: A large share of `edit_file` calls never reach the file: the model emits an unterminated string literal (the lost call's `new_string` ends in `ng:`), the harness returns "mandatory input parameters are not present: old_string", and the agent retries the identical call
- status: hypothesis
- confidence: high
- topics: [edit-reliability]
- expected gain: none directly; this is the paper's primary contribution (C-005 and C-006 are the mitigations).
- sources: EXP-024 §1 (117 of 309 `edit_file` calls across two dev-48 runs, 37.9%, Wilson 32.6-43.4%; `new_string` survived 116/117, `old_string` 0/117; `write_file` lost 0 of 14, Fisher p = 0.0028; retries up to 19 per task; 84-85% of lost calls are retries); EXP-026 §1 (200/201 lost calls end in `ng:`; ~90% repeat rate; model took the shell route 0 of 31 times after a first loss); EXP-025 §9.1 (Arm A 49 lost of 114 edit calls on 6 tasks, Arm B 35 of 81 on 9 tasks); lit-vllm2026-parser (parser issues #38910, #42696 report corrupted streamed arguments)
- tests: EXP-024, EXP-025, EXP-026 §1 (measurements; no critic yet)
- migrated-evidence: the `"status": "error"` envelope check missed 92 of 92 losses in E0 (EXP-024 §1.4); `analyze_traces.py` now counts the harness string directly.
- history: 2026-10-29 migrated as hypothesis
- history: 2026-11-06 evidence added, status unchanged: on the shipped v24 prompt Arm R lost 58 of its 175 `edit_file` calls (33.1%) across 7 of 48 tasks (critic's count, `experiments/EXP-028/critic.md`)

## C-005: A short prompt section routing every post-loss edit through a single-argument `run_command` python heredoc raises post-loss compliance (next call is `run_command`) from <5% to >= 60% without raising the empty-patch rate
- status: refuted
- confidence: medium
- topics: [edit-reliability, prompt]
- expected gain: on the retired lineage, each affected task lost 8-19 calls to retries; on the v24 tree the affected count is unknown. Not powered on resolves. Decides the tree for slot #12 (EXP-028 §4 rows 1-8).
- sources: EXP-026 §1-§3 (route design, baseline 4.6% = 9 of 195 post-loss calls are `run_command`, 0/31 after a first loss); lit-2604.05407 (structured action spaces cut empty patches on small models); lit-aider2025-editformats (single-argument whole-file routes are easiest for small models)
- tests: EXP-028 Arm RH vs Arm R (row 4 fired: next call after a first loss is `run_command` in 0 of 6 RH and 0 of 8 R tasks, Fisher p = 1.0, one-sided 95% upper bound 39%; critic light accepted); EXP-026 Arm C (pre-registered on the retired 12.8 KB prompt, not run); submissions.md row 10 (#10, same route on the retired prompt: 6/58, uninformative at one draw)
- history: 2026-10-29 migrated as hypothesis
- history: 2026-11-06 hypothesis -> refuted as stated, on this prompt at n = 6: EXP-028 critic light accepted (b691244), row 4; compliance 0 of 6 (RH) and 0 of 8 (R), one-sided 95% upper bound 39% against the claimed 60%

## C-006: A recovery ladder in the 12.8 KB prompt (EXP-024 editfix: long verbatim anchors, then write_file) cuts wasted identical retries after a lost edit
- status: hypothesis
- confidence: low
- topics: [edit-reliability, prompt]
- expected gain: superseded for the LB by C-005 on the adopted tree; paper-relevant only.
- sources: EXP-025 §9 (Arm A 43 wasted retries vs Arm B 26, -40%, paired Wilcoxon p = 0.4531; Arm A affected 6 tasks -> §4 row 1 UNDERPOWERED; `submit_patch` called 3 -> 9, McNemar p = 0.0703; exploratory time-cap hit 46 -> 39, p = 0.0156, not pre-registered)
- tests: EXP-025 (results written, no critic yet); submissions.md row 9 (#9: 6/58, uninformative)
- migrated-evidence: EXP-025 §9.3 logged a drafting defect: row 6 ("B worse on empty patches") fired on its letter at 21 vs 19, McNemar p = 0.75, and was not acted on.
- history: 2026-10-29 migrated as hypothesis; the lineage it belongs to is retired from the LB (D-001)

## C-007: At an 8-min cap the 28-call cap binds on a large share of tasks with no resolves among them, so `max_tool_calls` 40 (the rank-3 unscored v25) gains tasks
- status: hypothesis
- confidence: low
- topics: [budget, tools]
- expected gain: unknown; EXP-028 T4 (>= 25% of tasks at 28 calls, none resolved) makes it the next single-variable arm.
- sources: EXP-003 (our prompt at 8 min / 28 calls: 20 of 48 tasks ended at the call cap, 0 resolves among them; `rich_3676` stopped exactly at the cap); kg-rank3-apache §2-3 (their median 21-25 calls at 8 min; v25 raises 28 -> 40, unscored)
- tests: EXP-028 Arm R (T4 fired: 18 of 48 at 28 calls by the analyzer, 17 by the harness, 0 resolved; tests the premise, not the gain; critic light accepted)
- history: 2026-10-29 migrated as hypothesis
- history: 2026-11-05 note, status unchanged: EXP-032 arm T4 (28 -> 43 calls, same tree) is built and permitted by its pre-registration but held by the lead (knowledge/plan.md); still untested
- history: 2026-11-06 status unchanged: the accepted EXP-028 review covers the premise only (the call cap binds, 0 resolved among capped tasks); the gain from 40 calls is untested

## C-008: The packing gate `cap x 120` is accurate only for prompts that run to the cap; the right rule is measured mean x 120 + measured overhead <= ~10.5 h, which admits 8 min for the v24 prompt and forbids it for ours
- status: hypothesis
- confidence: medium
- topics: [budget]
- expected gain: none directly; it decides which caps are uploadable without a blank.
- sources: EXP-016 §3 (E0: 79.2% at cap, mean 258.3 s, formula 9.00 h vs actual 8.61 h; overhead setup 3.3 s/task median, grading 14.0 s/task mean, ~35 min per 120 tasks); EXP-027 §1c; submissions.md row 2 (#2 projected 11.34 h on actual time and still timed out)
- tests: EXP-028 Arm R (10.04 h from measured mean and overhead against 18.00 h from cap x 120; admits 8 min for v24; does not test the clause on our retired prompt; critic light accepted)
- history: 2026-10-29 migrated as hypothesis; the gate in `submission_rules.py` is unchanged pending a measured rule
- history: 2026-11-06 status unchanged: the accepted EXP-028 review covers the v24 half only

## C-009: Prompt surgery on the 12.8 KB phased-prompt lineage cannot move the public LB above 8/58
- status: hypothesis
- confidence: medium
- topics: [prompt, noise]
- expected gain: none; it is the reason the lineage is retired (D-001).
- sources: submissions.md rows 1-10 (series 4, timeout, 7, 6, 8, 8, 7, 7, 6, 6 on the same 58 tasks); EXP-017 (4-change bundle: 8/58, pre-committed 0.17 threshold not crossed, LR 1.07:1); EXP-010 (tripwire 6/58, Fisher p = 1.0); EXP-022 §2.3 (any single-knob LB contrast needs ~9 slots per arm)
- tests: none designed; EXP-027 §4 additive reading closes it in favour of the short prompt if #11 >= 9
- history: 2026-10-29 migrated as hypothesis

## C-010: `thinking_budget` 4096 vs 256 does not change resolves or empty patches on dev-48 but changes the edit-loss rate three-fold (lower budget, more loss)
- status: hypothesis
- confidence: medium
- topics: [sampling, edit-reliability]
- expected gain: none directly; it forbids lowering thinking to buy calls (EXP-022 §2.4 item 3).
- sources: EXP-024 §0 (paired E0 vs EXP-003: McNemar resolved p = 0.7266, empty p = 0.5811; arg loss 53.5% at 256 vs 18.2% at 4096, Fisher p = 1.2e-10 call-level, 0.0169 task-level; 7.73 vs 13.50 s/call); EXP-020 (thinking moves tokens/turn +116.7, s/turn +4.53, turns/task -6.85)
- tests: EXP-024 analysis (no critic yet); submissions.md row 6 (#6 at 4096: 8/58)
- history: 2026-10-29 migrated as hypothesis

## C-011: The turn of the first edit separates scoring from empty-patch tasks (median 18 vs 43 in E0), but forcing an early edit through a prompt rule does not convert never-edited tasks
- status: hypothesis
- confidence: medium
- topics: [prompt]
- expected gain: none for a call-index rule (EXP-024 §3 Q1: the 21 never-edited tasks pass call 12 with only `run_command` and `read_file`, and their calls cost 1.5-2x more, so a deadline in call index is unreachable for them).
- sources: EXP-009 (first-edit turn 18 vs 43); EXP-010 (tripwire at call 25: LB 6/58, uninformative); EXP-024 §1.3, §3 Q1; kg-rank3-apache §4 ("Edit by tool call 12", median first edit step 10 in their best local config)
- tests: EXP-010 (LB only); EXP-025 (never-edited 19 vs 20, McNemar p = 1.0)
- history: 2026-10-29 migrated as hypothesis

## C-012: The harness's graph tools (`search_similar_code`, `get_code_neighbors`, `get_code_subgraph`) lose to a plain grep baseline at every k, so banning them from the tree costs nothing
- status: hypothesis
- confidence: medium
- topics: [tools]
- expected gain: none directly; it is already applied (the v24 tree bans them; our #5 dropped them).
- sources: experiments/recall_check/README.md (grep recall@1/3/5/10 = 24.8/35.4/37.2/41.6% vs tool 14.2-16.8/19.5-23.9/21.2-28.3/24.8-34.5% on 113 tasks; 2026-10-19 correction: the 62.7% gold-in-graph and anisotropy figures have measurement bugs and are not to be cited at face value); EXP-002; lit-2511.00197 (localization failures are wasted effort on wrong paths, fixed by cheap discipline)
- tests: recall check (CPU kernel `rainm4/gemma4-recall-check`); EXP-002 smoke-8
- history: 2026-10-29 migrated as hypothesis; not pursued further (plan.md §6.1 E-STOP dropped)

## C-013: LoRA adapters trained on SWE-smith / SWE-rebench style actions hurt this model on this harness
- status: hypothesis
- confidence: medium
- topics: [lora]
- expected gain: negative on the only same-model data (-10.8 points locally). Parked: no-go at the Oct 25 gate (EXP-022 §2.3 item 7).
- sources: kg-rank3-apache §5 (v20 adapter 28.3% vs v20_base 39.1% on 46 tasks; v21 19.6% with 54.3% empty patches); EXP-016 §2c; lit-2603.13023 and lit-2512.13607 (32B gains need full fine-tunes on thousands of verified trajectories; no LoRA numbers reported); plan.md §6.2
- tests: none of ours
- history: 2026-10-29 migrated as hypothesis; parked
- history: 2026-11-06 note, status unchanged: the user asked for an adapter aimed at tool-call failures only (D-006, C-024). C-013's evidence is about adapters trained on whole task trajectories; it does not test a narrow one. Q4 (whether the harness's server applies an adapter at all) is still open and gates both

## C-014: Same-model delegation (sub-agents, `agent_tool`) does not add capability here and costs the binding resource, time
- status: hypothesis
- confidence: low
- topics: [multi-agent]
- expected gain: none expected; the one cited datum (12/18 -> 6/18) is secondhand [M] and was never run here.
- sources: plan.md §4.1 and §6.0.3; EXP-007 (ADK ParallelAgent gives real concurrency, max_in_flight 2, but a sync tool call stalls the sibling branch ~78%); EXP-024 §3 Q7 (no-go); lit-2407.01489 (Agentless: pipeline, not agent loop; selection signals need tests)
- tests: EXP-006, EXP-007 (probes; no agent run)
- history: 2026-10-29 migrated as hypothesis; parked
- history: 2026-11-05 evidence added, status unchanged (no critic verdict): lit-2026-11-05-architecture-families found no source for the 12/18 -> 6/18 figure; lit-2512.08296 has every multi-agent topology at or below the single agent at equal budget (n = 20, direction only); lit-2602.03786 is mixed by model. D-005 ranks the orchestrator last and screens it only on the user's request.
- history: 2026-11-05 evidence added, status unchanged (no critic verdict): EXP-032 arm P1 (ParallelAgent of three read-only localizers, then an editor, smoke-8 on the cap-bound ids): 21 of 24 localizer branches overspent a 5-call prompt limit, the shared 43-call budget was gone before the editor started in 7 of 8 tasks, non-empty patch 1 of 8, mean wall +72.9 s on Arm R; row e fired, parallel stage parked; not evidence on delegation capability, since the editor had 0 guaranteed calls in 7 of 8 (critic light accepted)

## C-015: Best-of-N attempts are affordable in wall-clock (88.6% idle KV capacity) but there is no selection signal without hidden tests, so N parallel editing branches cannot pay; N read-only localizers feeding one editor is the only fitting shape
- status: hypothesis
- confidence: low
- topics: [selection, multi-agent]
- expected gain: unknown; parked until a selection proxy exists.
- sources: EXP-006 (max_concurrency_32k(31B) = 8.74); lit-2512.13607 (regression tests then reproduction tests then majority vote; majority vote saturates early); lit-2505.23604 (Best@50 = 41.6 with a reward model); lit-2602.03419 (55.0 -> 68.2 at TTS@8 with a verifier); research/2026-10-28-literature-review.md §4 (Trae selector peaks at 5-6 candidates)
- tests: EXP-034 (zero GPU; critic review pending)
- history: 2026-10-29 migrated as hypothesis; parked
- history: 2026-11-05 evidence added, status unchanged (no critic verdict): EXP-034 Q1 union minus best is 5 of 48 over six arms but 1 between R and RH; best free proxy +3.0 over a random arm, +1.12 over a random non-empty patch. lit-2026-11-05-architecture-families: selectors that run tests close 39 to 55% of the gap to the oracle, majority vote adds nothing. Unparked as family F1 of D-005 with an executed selector.

## C-016: Task difficulty on dev-48 is strongly heterogeneous but only about half to two-thirds of a run's resolves repeat across runs of different configs
- status: hypothesis
- confidence: medium
- topics: [noise]
- expected gain: none directly; it sets the dev-48 MDE on resolves (~10 of 48) and argues for process endpoints.
- sources: EXP-022 §1.3 (E0 and EXP-003 share 6 resolved of 14 distinct; expected overlap 2.06; Fisher p = 0.0023; phi 0.50, bootstrap CI 0.16-0.78); EXP-009 (42.9% cross-config concordance)
- tests: EXP-022 analysis (no critic yet)
- history: 2026-10-29 migrated as hypothesis

## C-017: Grading runs whole hidden test files, so a patch that breaks any sibling test fails the task; running whole files locally is safer than `pytest -k`
- status: hypothesis
- confidence: high
- topics: [grading]
- expected gain: none directly; it is the reason we did not adopt the 0.24 prompt's `-k` rule (plan.md §6.1a).
- sources: experiments/README.md §1h (2026-10-14, from the harness source [V]); kg-rank3-apache §2 (their v18 comment: the verifier runs hidden tests under `timeout_seconds`; Requests modules take ~70 s)
- tests: EXP-000 gold control
- history: 2026-10-29 migrated as hypothesis

## C-018: Reproducing before the first edit correlates with resolving, but writing a reproduction file costs ~27% of wall-clock; a one-shot `python -c` check is the compromise
- status: hypothesis
- confidence: medium
- topics: [prompt, budget]
- expected gain: already applied in #5 (EXP-017) and inherent in the v24 tree ("one check, one repair, then submit").
- sources: EXP-009 Part C5 (20/20 resolved runs reproduced before their first edit) and Part C2; plan.md §6.1a (27.3% of wall-clock in heredoc repro files); kg-rank3-apache §3 (script-writing calls fell from 28% to 0-3% of calls by v20)
- tests: EXP-017 (LB only, uninformative)
- history: 2026-10-29 migrated as hypothesis
- history: 2026-11-05 note, status unchanged (EXP-042, cf3035f, zero GPU, observational; critic light): EXP-042 counts a check before submit, not before the first edit, so it does not test this claim's timing. In Arm R 9 of 9 resolved and 28 of 39 unresolved tasks ran one, mostly a python reproduction (script or inline); 8 of R's 11 non-checkers hit a cap and the other 3 are gated or impossible, so within R the association is confounded with running out of budget. The E4B ran no reproduction on any of its 48 tasks, and an informative check on 1 of 5 resolved and 4 of 43 unresolved (critic count; EXP-042 says 3), too few to show or exclude a correlation. (Line replaced with the critic's text, c275b97.)

## C-019: On right-file-wrong-fix tasks the agent hands in its patch without running any test after its last edit, so an executed verify step is the structural change with the most room
- status: hypothesis
- confidence: low
- topics: [multi-agent, prompt, budget]
- expected gain: about +2 of 48 if the published effect of regression-test checking transfers (lead's inference); the pool is at most 23 of 48 and unsized until EXP-035.
- sources: EXP-034 section 9.2 (R: 21 of 30 with no test after the last edit, 7 on a visible pass and wrong, 15 of 30 ended by submit; RH replicates); lit-2504.07164 (regression tests +4.5 points); lit-2604.13120 (Tester -14, Debugger -11, Critic -4 of 100 on removal); lit-2310.01798 (self-correction without an external signal lowers accuracy)
- tests: EXP-034 (zero GPU; critic review pending); EXP-035 planned
- history: 2026-11-05 added by the lead as hypothesis from D-005 Stage 0
- history: 2026-11-05 evidence added, status unchanged (no critic verdict): EXP-036 recomputed the EXP-035 table on re-graded outputs, T3 in both arms: the failing tests are ones the hidden patch adds or changes in 19 of 27 (R) and 14 of 22 (RH) unresolved right-file tasks; an existing test would have exposed the wrong fix in 2 of 27 and 1 of 22. A required run of existing tests therefore has a pool of 1 to 2 tasks; the claim survives only for a check the agent writes from the issue
- history: 2026-11-05 correction to the line above from the critic's light review of EXP-036 (needs-work): the groups are 22 tasks in R (visible 2, hidden-only 15, collection error 5) and 17 in RH (1, 10, 4, 2 unclassified) once the patch-insensitive tasks are removed; visible is a lower bound and for R lies between 2 and 7 of 22. The pool for a required run of existing tests is 2 to 7 of 22 in R, not 1 to 2
- history: 2026-11-05 note, status unchanged (EXP-042, cf3035f; critic light): on the E4B single loop the trace record neither shows nor excludes that an executed check separates resolved from unresolved tasks (informative check on 1 of 5 wins, 4 of 43 losses; critic count, EXP-042 says 3). 11 of the 12 fastapi tasks where the E4B ran pytest died at collection on the two missing test-only packages, so a required test run carries no information on dev-48's fastapi tasks in this sandbox; its 4 non-fastapi pytest runs executed. The claim's wrong-fix pool was measured on the 31B (EXP-034) and is not shown for the E4B. (Line replaced with the critic's text, c275b97.)

## C-020: The E4B runs the shipped v24 single loop at 8 min / 28 calls well inside the clock: on dev-48 (EXP-038) 0 of 48 tasks hit a cap, the mean task wall is 85.7 s (max 207.3 s), and the projection is 2.98 h for 120 tasks against the 10.5 h rule. `analyze_traces` counts 0 malformed calls in 478. That count does not see one task, fastapi_13537, which wrote its calls as text and ended with 0 tool calls. For an E4B upload of this tree the clock is not the constraint. It resolves 5 of 48 as run against the 31B's 9 (paired 4-0, p = 0.125), which does not show that the two are equal
- status: supported
- confidence: high
- topics: [budget, rules]
- expected gain: none claimed; opens the small-model prize at about 1 GPU-h per dev-48 arm.
- sources: EXP-033 section 9 (8 of 8 ran, 0 malformed in 43 calls, 6 of 8 non-empty patches, mean wall 56.9 s and 423 s left under the cap on one draw (78.3 s on the same ids in EXP-038); resolves 2 of 8 recorded, not read); lit-2506.03524 (fixed workflow beat a free loop below about 10B in one table)
- tests: EXP-033 (smoke-8; critic light accepted); EXP-038 (dev-48, paired with Arm R; critic `full`, accepted, `experiments/EXP-038/critic.md`, d1d78a2)
- history: 2026-11-05 added by the lead as hypothesis
- history: 2026-11-05 note: the E4B dev-48 question is unchanged by EXP-036; any E4B number on dev-48 carries the same grading gap (C-021) and the 43 of 48 ceiling (C-022)
- history: 2026-11-05 note: the user approved the E4B dev-48 reference arm on the condition of about 1 GPU-h (EXP-038, to be pre-registered; `knowledge/user-decisions.md`)
- history: 2026-11-05 note, status unchanged pending critic review: EXP-038 (a1365bc), the E4B single loop on dev-48 paired with Arm R: 5 of 48 against 9 of 48, R only 4, E4B only 0, exact McNemar p = 0.125 (row 4, no difference detected); mean wall 85.7 s, 0 of 48 capped, projected 2.98 h for 120 tasks
- history: 2026-11-05 hypothesis -> supported, confidence low -> high for the dev-48 time profile (that it carries to the hidden repos is the critic's inference), reworded as the critic required: critic results review of EXP-038, verdict accepted, tier raised by the critic from light to full for this move, numbers regenerated byte for byte (`experiments/EXP-038/critic.md`, d1d78a2). Earlier title: "The E4B model runs the shipped single loop without malformed calls and finishes in about a minute per task, so for the small-model prize the clock is not the constraint". Not covered by the verdict: the re-grade with stand-ins (fault row F, endpoint G; CPU kernel running), and any leaderboard result. Paired difference, R minus E4B: 95% interval -0.5 to +9.1 tasks (critic's calculation), so no E4B deficit is ruled out
- history: 2026-11-05 note, status unchanged: EXP-041 (zero-GPU trace mining, no critic review, 2303c4c) finds no single mechanism behind the four tasks the E4B loses to Arm R (one format failure, two wrong fixes in the gold file, one wrong file); on the 19 ids neither arm resolves, 16 submit without running any test or code and 5 submit after every edit call failed
- history: 2026-11-05 note, status unchanged pending critic `light`: EXP-038 re-grade (9c68639): fault row F does not fire; G = 0 of 15, so the stand-ins move no E4B task; E4B with stand-ins 5 of 48 against R's 12 and RH's 15 on the same ids (paired against R's re-grade 7 and 0, p = 0.0156, reported with no pre-registered reading)
- history: 2026-11-05 critic light review of the EXP-038 re-grade: accepted (45b2511; numbers regenerated, builder defaults rebuild EXP-036 byte for byte). The re-graded 7-0 against R may be cited only as a ceiling in the critic's wording (`experiments/EXP-038/critic.md`, re-grade review, item 3); it is not a detected difference

## C-021: On the Kaggle subprocess grader, 15 of 48 dev-48 tasks (all fastapi) are graded without two test-only packages. The shipped v24 prompt does not vendor them, and R and RH resolve 0 of 15. With API-faithful stand-ins present, the same patches resolve 3 of 15 (R) and 5 of 15 (RH), 3 of them in both. So 3 to 5 of the v24 lineage's dev-48 failures are the grading gap, not the fix
- status: supported
- confidence: high
- topics: [grading, prompt]
- expected gain: +1 to +3 of 48 on dev-48 from porting the vendoring section (lead's inference); on the board unknown, since it is not known whether the hidden grader lacks the packages.
- sources: experiments/EXP-034/critic.md (15 gated tasks; R and RH 0 of 15; E0 2, A25 2, B25 1 through vendored code; X003 3 under the EXP-004 re-grade; non-gated union minus best 3); EXP-035 section 9 (R: 11 of 16 unreadable grader outputs are a missing module; RH 12 of 18); EXP-004 (re-grade with shims: EXP-003 9 -> 12); submissions.md rows 1 to 12 (board does not settle it)
- tests: EXP-035 (zero GPU); EXP-036 planned (CPU re-grade of R and RH with the packages present)
- history: 2026-11-05 added by the lead as hypothesis from the critic's review of EXP-034
- history: 2026-11-05 evidence added, status unchanged (no critic verdict yet): EXP-036 (CPU re-grade, 0 GPU-h) row 1 fired: with the two packages present the v24 patches resolve 3 of 15 gated tasks in Arm R (9 -> 12 of 48) and 5 of 15 in Arm RH (10 -> 15), no non-gated flip, no resolve lost, GOLD 15 of 15 on the gated tasks. R sits exactly on the threshold; RH replicates above it
- history: 2026-11-05 critic light review of EXP-036: needs-work on text only; row 1 holds as applied, numbers reproduced, the five flips hand-checked against stand-in leniency (plain `==`, no risk found); RH is not an independent check of the grader, the robust part is the three tasks that flip in both arms; all 15 gated tasks are fastapi (15 of dev-48's 26). Status unchanged until the fixes are re-reviewed
- history: 2026-11-05 evidence added, status unchanged: grading-environment scout plus the lead's own listing. No pool we can see has the two packages: the public wheelhouse (41 files, created 2026-10-12) and the competition `wheels/` folder (124 wheels, all 524 competition files created 2026-10-13) hold neither, and `Dockerfile.sandbox` installs neither; no host has answered any missing-package thread and no update was announced. Whether the scorer has them (private pool, image, Docker or subprocess) is still not visible, and whether hidden-repo tests import them is unknown
- history: 2026-11-05 note, status unchanged: EXP-037 (a proactive vendoring section on the v24 tree, gated-8) is pre-registered and built, not pushed; trigger mining found R and RH saw the missing-module error on 0 of 15 gated tasks. Critic `prereg` review needs-work: on means the section adds about 24 s per task (lower bound) against 13.8 s of headroom at 8 minutes, so it cannot ship at 8 minutes as built; a leaderboard gain needs at least 4 of 58 hidden tasks to import the packages, untestable from here. The lead withdrew its advice to run the screen first (knowledge/plan.md)
- history: 2026-11-05 hypothesis -> supported, confidence medium -> high (on dev-48 only), reworded as the critic required: critic re-review of EXP-036 after the text fixes of 6090294, verdict accepted (`experiments/EXP-036/critic.md`, light tier; the critic judged it full-equivalent for a zero-GPU re-grade because its first review already checked that row 1 was the first matching row applied as written and that the flips are paired on the same patches and ids; the lead accepts that call). Earlier title: "15 of 48 dev-48 tasks are graded without two test-only packages; the shipped v24 prompt has no vendoring text and resolves none of them, so part of its measured failure is the sandbox gap, not the fix". Not covered by the verdict: whether the hidden grader lacks the packages, and any leaderboard gain
- history: 2026-11-05 note, status unchanged: on the E4B's patches the stand-ins flip 0 of 15 gated tasks (EXP-038 re-grade, 9c68639), against 3 (R) and 5 (RH). Paired on the 15, the E4B is 0-3 against R (p = 0.25) and 0-5 against RH (p = 0.0625), so the data do not show whether the gain depends on the model. C-021's 3 to 5 is a 31B v24 figure. 5 of the E4B's 21 unresolved patches that touch a gold-patch file break collection themselves (file-set rule), 3 of them gated. (Line replaced with the critic's text, light review 45b2511; the earlier wording "not model-independent" overstated.)

## C-022: Six dev-48 tasks grade the same with the gold patch and with no patch on the Kaggle subprocess grader in ten gradings (GOLD, BASE, the R and RH re-grades, and the six EXP-034 arms as run). So the dev-48 ceiling is 43 of 48 with the two test-only packages present, installed or vendored, and 28 as run for a tree that does not vendor (27 informative tasks plus 1 free resolve)
- status: supported
- confidence: high
- topics: [grading, noise]
- expected gain: none; a correction to every absolute "N of 48" figure (paired comparisons are unaffected). Excluding the six, Arm R is 8 of 42 as run and 11 of 42 re-graded; RH 9 and 14 of 42.
- sources: EXP-036 section 9 (post hoc, not pre-registered: GOLD and BASE give the same exit code, count line and failing test ids on httpx_3672, requests_6644, requests_7205, requests_7309, requests_7315, requests_7427; GOLD 43 of 48, BASE 1 of 48); experiments/README.md section 1 (EXP-000 Kaggle gold-failure classes); EXP-002 (three of these ids failed the smoke-8 gold control)
- tests: EXP-036 (zero GPU)
- history: 2026-11-05 added by the lead as hypothesis from the experimenter's post hoc finding; cause not verified (two gold tails show the installed package's site-packages path, which suggests shadowing)
- history: 2026-11-05 critic light review of EXP-036: evidence is concordance in eight gradings (GOLD, BASE, R re-grade, and all six EXP-034 arms as run), observed, not structural; McNemar comparisons unaffected; changed by it: absolute rates, any power stated on n = 48, EXP-034's always/none counts (6/31 becomes 5/26), the right-file-wrong-fix denominators (R 22), and smoke-8, which holds three of the six (at most 4 informative tasks of 8 for a tree that does not vendor). Status unchanged until the text fixes are re-reviewed
- history: 2026-11-05 correction to the line above: the gradings are ten, not eight (GOLD, BASE, the R and RH re-grades, and the six EXP-034 arms as run); requests_6644 resolves and the other five do not in each
- history: 2026-11-05 hypothesis -> supported, confidence medium -> high as an observation (the mechanism is not verified), reworded as the critic required: critic re-review of EXP-036, verdict accepted (`experiments/EXP-036/critic.md`). Earlier title: "Six dev-48 tasks grade the same with the gold patch and with no patch on the Kaggle sandbox, so the reachable dev-48 ceiling is 43 of 48, with one free resolve and five impossible ones". The 28 as run is the critic's inference
- history: 2026-11-05 note, status unchanged pending critic `light`: the GOLD and BASE passes repeat: in the EXP-038 re-grade GOLD resolves 43 of 48 with the same five ids unresolved and BASE resolves requests_6644 only (9c68639)
- history: 2026-11-05 note from the critic's light review of the EXP-038 re-grade (accepted, 45b2511): fourteen gradings now agree, adding the E4B as run and re-graded, and GOLD and BASE repeated in the EXP-038 re-grade

## C-023: On the E4B, tool-less voters at different temperatures that vote on the executor's next move, with a fixed tie rule, raise the resolve count over the E4B single loop within the 8 minute cap
- status: hypothesis
- confidence: low
- topics: [architecture, budget]
- expected gain: unknown; no bound yet. The E4B single loop left 423 s under the cap on one smoke-8 draw (EXP-033) and 394 s on dev-48 (EXP-038); the 10.5 h rule binds first, at about 225.6 s per task (EXP-038 row T), which is the room voting would spend.
- sources: user request 2026-11-05 (`knowledge/user-decisions.md`); D-004 bounds B3 (one call counter for all agents), B5 (E4B 45.63x KV room, X(4) = 3.47); EXP-032 P1 section 9 E6 (21 of 24 localizer branches broke a prompt-only 5-call limit; the editor had 0 guaranteed calls in 7 of 8); `research/lit/lit-2026-11-05-architecture-families.md` (majority vote over patches: no gain, ties at N of 3 or fewer; nothing on per-step voting in a repo task)
- tests: EXP-039 (L0 desk check, zero GPU, no critic review): one vote point is expressible and enforceable, per-step voting is not enforceable; design V1 with 16 voters; no screen run yet
- history: 2026-11-05 added by the lead as hypothesis, on the user's request; filed under D-005 as a family, no GPU approved yet
- history: 2026-11-05 note, status unchanged: EXP-039 desk check (cc4fb18, 38a7c27). The claim's "next move" form needs a one-call-per-round rule that is prompt-only, so the first screen is one vote point (proposer, 16 tool-less voters at temperatures 0.2 to 1.4, actor; tie to the lowest-numbered voter). The lit review's finding that majority vote over patches gives no gain is a prior against it; the screen can kill or promote the design, not show that voting helps. Cost 0.31 to 0.37 GPU-h, not yet approved
- history: 2026-11-05 note, status unchanged: EXP-040 (the V1 screen, smoke-8, E4B, 16 voters) is pre-registered and built, not pushed (3f33acd, 5b0f266); cost 0.30 to 0.36 GPU-h, not yet approved. The critic's EXP-038 review puts the total-clock room for an extra stage on the E4B near 225 s per task, not 423 [I]
- history: 2026-11-05 note, status unchanged: lit-scout note `research/lit/lit-2026-11-05-voting-agents.md`. No source votes on a repair agent's next action; per-step voting has no positive result below about 20B (MAKER, arXiv:2511.09030, fails on its 3B model); no measurement of how often a same-model vote over a lettered list differs from greedy. A prior against the claim, not a test of it
- history: 2026-11-05 note, status unchanged: EXP-038 gives the paired E4B reference (5 of 48, mean wall 85.7 s, 0 capped) and the measured room for extra stages, 225.6 s per task on the total clock (a1365bc, not yet critic-reviewed)
- history: 2026-11-05 note, status unchanged, citation accepted by the critic (d1d78a2): on the E4B single loop, the 10.5 h rule leaves 225.6 s per task on average for an extra stage (EXP-038 row T). This binds before the per-task cap room, mean 394 s. A voting tree's dev-48 mean task wall must stay below about 311 s. The critic also notes run-to-run drift: the 8 smoke ids took 78.3 s here against 56.9 s in EXP-033, so EXP-040's 140 s wall bar is measured against a moving reference
- history: 2026-11-05 note, status unchanged (critic light accepted, a4cdc5b, 037eb9e): EXP-040 (a396b12, smoke-8, E4B, 0.315 GPU-h), row 2 fired: with 16 same-prompt voters at temperatures 0.2 to 1.4 at one vote point, the winner equalled voter 1's pick on 8 of 8 tasks (D = 0; D could be true on 6). V1 as specified is stopped. Two or more candidates on 6 of 8 tasks, but on 3 of those 6 the candidates were one fix in different words (experimenter's judgement); on the other 3 the vote also equalled voter 1's pick. Mean wall 86.5 s, 0 of 8 capped; resolves 1 of 8 against 2 of 8 for the single loop, recorded, not read. The claim is neither supported nor rejected: the screen tested one design at n = 8; the row names a prompt-diverse variant, not built

## C-024: A LoRA adapter trained only on exact-copy edit calls (given a shown file window, emit an `edit_file` call whose old string is an exact, unique substring of it) raises the share of E4B tasks with an applied edit, without lowering resolves
- status: hypothesis
- confidence: low
- topics: [lora, edit-reliability]
- expected gain: at most about 1 task of 48, probably less [I]: 3 of the 8 are gated (the E4B resolves 0 of 15 gated even re-graded); the other 5 at the non-gated rate (5 of 28) give 0.9; about 3 of the 5 fail the way the adapter targets; Arm R and RH resolved 0 of the 8 as run. Not measurable on resolves. (Replaced 2026-11-06 with the critic's text.)
- sources: user request 2026-11-06 (`knowledge/user-decisions.md`); EXP-043 (critic light accepted); C-013 (the only same-model adapter datum is negative, for a different kind of adapter); `experiments/README.md` Q4 (host acknowledged adapters wiped [M], open); the organisers' sample submission ships a tool-call adapter
- tests: none; gated on the Q4 canary. Endpoint when tested: share of failed-edit-8 tasks with an applied edit, paired against the unchanged tree (EXP-044's design), with empty-patch rate and wall recorded.
- history: 2026-11-06 added as hypothesis with D-006
- history: 2026-11-06 expected gain and tests replaced with the critic's text (D-006 direction review, `experiments/EXP-043/critic.md`, 19a8b20, 5ab7020)
- history: 2026-11-06 evidence, status unchanged (no critic verdict): EXP-044 X0 (1f8a156), the unchanged E4B tree re-run on failed-edit-8, applied an edit on 7 of 8; so the no-edit population this adapter targets is mostly one bad draw, and the ceiling of about 1 of 48 overstates it [I].
- history: 2026-11-08 evidence, status unchanged (no critic verdict): EXP-054 v2 (1170009; R4 positive, costly; offline, per call, zero tasks): rank-8 q/o LoRA on the BF16 parent, 67 steps. Exact copy on 120 held-out stdlib windows 0.483 to 0.708 (30 against 3 discordant, McNemar p 1.4e-6). The drift gate failed G1 (first-tool agreement 0.625 against 0.70 or more; `run_command` first 18 to 2 of 48) and G4 (prose logprob mean |delta| 0.72 against 0.15 or less). Decode drop 0.168. Q4 settled for the E4B: the harness's server loads and routes the adapter. No resolve rate measured; section 4 licenses no stage 4 on this adapter.
- history: 2026-11-08 evidence, status unchanged (no critic verdict): EXP-058 (dce3e7a; row 3, Clean; a bug test, no effect reading by design): the EXP-054 v2 adapter on the EXP-033 tree ran end to end on smoke-8 through the eval notebook (weights mounted by `kernel_sources`, not committed); server sized `--max-loras 1 --max-lora-rank 8` from the adapter; every model step served by `copy_lora`; 0 errors, malformed calls, tool-free endings or caps. Recorded, not read: 10 applied edits against 10 on EXP-033, 10 failed edits against 7. Where to use the adapter is to be re-derived (user, 2026-11-08).
