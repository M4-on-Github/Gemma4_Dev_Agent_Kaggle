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

## C-002: For the rank-3 v24 prompt, raising `max_time_minutes` from 4.5 to 8 moves the hidden-set score by several tasks, because the cap at 270 s kills the check-and-repair finish rather than the first edit
- status: hypothesis
- confidence: medium
- topics: [budget]
- expected gain: theta ~ 10/58 for the 8-min tree vs 7/58 at 4.5 (EXP-027 §3: +3.3 after removing their best-of-N selection; their 14/58 is a maximum of >= 12 uploads)
- sources: submissions.md row 8 (#8 = v24 at 4.5 min: 7/58); kg-rank3-apache §2-3 (v24 at 8 min: 14/58, Fisher p = 0.147 vs #8; 2-6 of their ~19 resolves per 46-task set finish after 270 s; first edits after 270 s: 0-1); EXP-023 §3 (confound stated before the score)
- tests: EXP-027 (#11, Kaggle ref 57750294, PENDING since 2026-10-28 22:39 UTC); EXP-028 Arm R (time profile, complete, unanalyzed)
- migrated-evidence: EXP-027 §4 holds the blind readings for #11 (blank -> 6.0 min next; k <= 8 -> adopt tree anyway, cap not the lever; 9-10 -> adopt as baseline; >= 11 -> adopt and re-run unchanged).
- history: 2026-10-29 migrated as hypothesis

## C-003: The v24 tree at 8 min / 28 calls completes ~120 hidden tasks inside the 12 h scoring budget
- status: hypothesis
- confidence: medium
- topics: [budget]
- expected gain: none directly; a blank costs one slot (zero for that day). Precondition for C-002 and every later arm on this tree.
- sources: kg-rank3-apache §2-3 (v19 and v24 both completed and scored at 8 min; runs.jsonl mean 275-296 s, 15-24% at cap, proj_h@120 9.9-10.6 h with 0.7 h overhead); EXP-016 §3 (our ~10.5 h operational ceiling; #2 died at an 11.34 h projection that omitted fixed overhead); submissions.md row 2
- tests: EXP-027 (#11 pending); EXP-028 Arm R (dev-48 time profile on our cohort, readings T1-T3)
- migrated-evidence: their prompt self-stops on 76-85% of tasks; ours ran to the cap on 79-96%, which is why `cap x 120` fit ours to 4% and overstates theirs by ~45% (EXP-027 §1c).
- history: 2026-10-29 migrated as hypothesis

## C-004: A large share of `edit_file` calls never reach the file: the model emits an unterminated string literal (the lost call's `new_string` ends in `ng:`), the harness returns "mandatory input parameters are not present: old_string", and the agent retries the identical call
- status: hypothesis
- confidence: high
- topics: [edit-reliability]
- expected gain: none directly; this is the paper's primary contribution (C-005 and C-006 are the mitigations).
- sources: EXP-024 §1 (117 of 309 `edit_file` calls across two dev-48 runs, 37.9%, Wilson 32.6-43.4%; `new_string` survived 116/117, `old_string` 0/117; `write_file` lost 0 of 14, Fisher p = 0.0028; retries up to 19 per task; 84-85% of lost calls are retries); EXP-026 §1 (200/201 lost calls end in `ng:`; ~90% repeat rate; model took the shell route 0 of 31 times after a first loss); EXP-025 §9.1 (Arm A 49 lost of 114 edit calls on 6 tasks, Arm B 35 of 81 on 9 tasks); lit-vllm2026-parser (parser issues #38910, #42696 report corrupted streamed arguments)
- tests: EXP-024, EXP-025, EXP-026 §1 (measurements; no critic yet)
- migrated-evidence: the `"status": "error"` envelope check missed 92 of 92 losses in E0 (EXP-024 §1.4); `analyze_traces.py` now counts the harness string directly.
- history: 2026-10-29 migrated as hypothesis

## C-005: A short prompt section routing every post-loss edit through a single-argument `run_command` python heredoc raises post-loss compliance (next call is `run_command`) from <5% to >= 60% without raising the empty-patch rate
- status: hypothesis
- confidence: medium
- topics: [edit-reliability, prompt]
- expected gain: on the retired lineage, each affected task lost 8-19 calls to retries; on the v24 tree the affected count is unknown. Not powered on resolves. Decides the tree for slot #12 (EXP-028 §4 rows 1-8).
- sources: EXP-026 §1-§3 (route design, baseline 4.6% = 9 of 195 post-loss calls are `run_command`, 0/31 after a first loss); lit-2604.05407 (structured action spaces cut empty patches on small models); lit-aider2025-editformats (single-argument whole-file routes are easiest for small models)
- tests: EXP-028 Arm RH vs Arm R (complete 2026-10-29, unanalyzed; readings in EXP-028 §4); EXP-026 Arm C (pre-registered on the retired 12.8 KB prompt, not run); submissions.md row 10 (#10, same route on the retired prompt: 6/58, uninformative at one draw)
- history: 2026-10-29 migrated as hypothesis

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
- tests: EXP-028 Arm R (28-call incidence; reading T4)
- history: 2026-10-29 migrated as hypothesis
- history: 2026-11-05 note, status unchanged: EXP-032 arm T4 (28 -> 43 calls, same tree) is built and permitted by its pre-registration but held by the lead (knowledge/plan.md); still untested

## C-008: The packing gate `cap x 120` is accurate only for prompts that run to the cap; the right rule is measured mean x 120 + measured overhead <= ~10.5 h, which admits 8 min for the v24 prompt and forbids it for ours
- status: hypothesis
- confidence: medium
- topics: [budget]
- expected gain: none directly; it decides which caps are uploadable without a blank.
- sources: EXP-016 §3 (E0: 79.2% at cap, mean 258.3 s, formula 9.00 h vs actual 8.61 h; overhead setup 3.3 s/task median, grading 14.0 s/task mean, ~35 min per 120 tasks); EXP-027 §1c; submissions.md row 2 (#2 projected 11.34 h on actual time and still timed out)
- tests: EXP-028 Arm R (measured mean and overhead on dev-48 for the v24 tree)
- history: 2026-10-29 migrated as hypothesis; the gate in `submission_rules.py` is unchanged pending a measured rule

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

## C-014: Same-model delegation (sub-agents, `agent_tool`) does not add capability here and costs the binding resource, time
- status: hypothesis
- confidence: low
- topics: [multi-agent]
- expected gain: none expected; the one cited datum (12/18 -> 6/18) is secondhand [M] and was never run here.
- sources: plan.md §4.1 and §6.0.3; EXP-007 (ADK ParallelAgent gives real concurrency, max_in_flight 2, but a sync tool call stalls the sibling branch ~78%); EXP-024 §3 Q7 (no-go); lit-2407.01489 (Agentless: pipeline, not agent loop; selection signals need tests)
- tests: EXP-006, EXP-007 (probes; no agent run)
- history: 2026-10-29 migrated as hypothesis; parked
- history: 2026-11-05 evidence added, status unchanged (no critic verdict): lit-2026-11-05-architecture-families found no source for the 12/18 -> 6/18 figure; lit-2512.08296 has every multi-agent topology at or below the single agent at equal budget (n = 20, direction only); lit-2602.03786 is mixed by model. D-005 ranks the orchestrator last and screens it only on the user's request.
- history: 2026-11-05 evidence added, status unchanged (no critic verdict): EXP-032 arm P1 (ParallelAgent of three read-only localizers, then an editor, smoke-8 on the cap-bound ids): 21 of 24 localizer branches overspent a 5-call prompt limit, the shared 43-call budget was gone before the editor started in 7 of 8 tasks, non-empty patch 1 of 8, mean wall +72.9 s on Arm R; row e fired, parallel stage parked

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

## C-020: The E4B model runs the shipped single loop without malformed calls and finishes in about a minute per task, so for the small-model prize the clock is not the constraint
- status: hypothesis
- confidence: low
- topics: [budget, rules]
- expected gain: none claimed; opens the small-model prize at about 1 GPU-h per dev-48 arm.
- sources: EXP-033 section 9 (8 of 8 ran, 0 malformed in 43 calls, 6 of 8 non-empty patches, mean wall 56.9 s, 423 s left under the cap; resolves 2 of 8 recorded, not read); lit-2506.03524 (fixed workflow beat a free loop below about 10B in one table)
- tests: EXP-033 (smoke-8; critic review pending)
- history: 2026-11-05 added by the lead as hypothesis
- history: 2026-11-05 note: the E4B dev-48 question is unchanged by EXP-036; any E4B number on dev-48 carries the same grading gap (C-021) and the 43 of 48 ceiling (C-022)

## C-021: 15 of 48 dev-48 tasks are graded without two test-only packages; the shipped v24 prompt has no vendoring text and resolves none of them, so part of its measured failure is the sandbox gap, not the fix
- status: hypothesis
- confidence: medium
- topics: [grading, prompt]
- expected gain: +1 to +3 of 48 on dev-48 from porting the vendoring section (lead's inference); on the board unknown, since it is not known whether the hidden grader lacks the packages.
- sources: experiments/EXP-034/critic.md (15 gated tasks; R and RH 0 of 15; E0 2, A25 2, B25 1 through vendored code; X003 3 under the EXP-004 re-grade; non-gated union minus best 3); EXP-035 section 9 (R: 11 of 16 unreadable grader outputs are a missing module; RH 12 of 18); EXP-004 (re-grade with shims: EXP-003 9 -> 12); submissions.md rows 1 to 12 (board does not settle it)
- tests: EXP-035 (zero GPU); EXP-036 planned (CPU re-grade of R and RH with the packages present)
- history: 2026-11-05 added by the lead as hypothesis from the critic's review of EXP-034
- history: 2026-11-05 evidence added, status unchanged (no critic verdict yet): EXP-036 (CPU re-grade, 0 GPU-h) row 1 fired: with the two packages present the v24 patches resolve 3 of 15 gated tasks in Arm R (9 -> 12 of 48) and 5 of 15 in Arm RH (10 -> 15), no non-gated flip, no resolve lost, GOLD 15 of 15 on the gated tasks. R sits exactly on the threshold; RH replicates above it
- history: 2026-11-05 critic light review of EXP-036: needs-work on text only; row 1 holds as applied, numbers reproduced, the five flips hand-checked against stand-in leniency (plain `==`, no risk found); RH is not an independent check of the grader, the robust part is the three tasks that flip in both arms; all 15 gated tasks are fastapi (15 of dev-48's 26). Status unchanged until the fixes are re-reviewed
- history: 2026-11-05 evidence added, status unchanged: grading-environment scout plus the lead's own listing. No pool we can see has the two packages: the public wheelhouse (41 files, created 2026-10-12) and the competition `wheels/` folder (124 wheels, all 524 competition files created 2026-10-13) hold neither, and `Dockerfile.sandbox` installs neither; no host has answered any missing-package thread and no update was announced. Whether the scorer has them (private pool, image, Docker or subprocess) is still not visible, and whether hidden-repo tests import them is unknown
- history: 2026-11-05 note, status unchanged: EXP-037 (a proactive vendoring section on the v24 tree, gated-8) is pre-registered and built, not pushed; trigger mining found R and RH saw the missing-module error on 0 of 15 gated tasks. Critic `prereg` review needs-work: on means the section adds about 24 s per task (lower bound) against 13.8 s of headroom at 8 minutes, so it cannot ship at 8 minutes as built; a leaderboard gain needs at least 4 of 58 hidden tasks to import the packages, untestable from here. The lead withdrew its advice to run the screen first (knowledge/plan.md)

## C-022: Six dev-48 tasks grade the same with the gold patch and with no patch on the Kaggle sandbox, so the reachable dev-48 ceiling is 43 of 48, with one free resolve and five impossible ones
- status: hypothesis
- confidence: medium
- topics: [grading, noise]
- expected gain: none; a correction to every absolute "N of 48" figure (paired comparisons are unaffected). Excluding the six, Arm R is 8 of 42 as run and 11 of 42 re-graded; RH 9 and 14 of 42.
- sources: EXP-036 section 9 (post hoc, not pre-registered: GOLD and BASE give the same exit code, count line and failing test ids on httpx_3672, requests_6644, requests_7205, requests_7309, requests_7315, requests_7427; GOLD 43 of 48, BASE 1 of 48); experiments/README.md section 1 (EXP-000 Kaggle gold-failure classes); EXP-002 (three of these ids failed the smoke-8 gold control)
- tests: EXP-036 (zero GPU)
- history: 2026-11-05 added by the lead as hypothesis from the experimenter's post hoc finding; cause not verified (two gold tails show the installed package's site-packages path, which suggests shadowing)
- history: 2026-11-05 critic light review of EXP-036: evidence is concordance in eight gradings (GOLD, BASE, R re-grade, and all six EXP-034 arms as run), observed, not structural; McNemar comparisons unaffected; changed by it: absolute rates, any power stated on n = 48, EXP-034's always/none counts (6/31 becomes 5/26), the right-file-wrong-fix denominators (R 22), and smoke-8, which holds three of the six (at most 4 informative tasks of 8 for a tree that does not vendor). Status unchanged until the text fixes are re-reviewed
