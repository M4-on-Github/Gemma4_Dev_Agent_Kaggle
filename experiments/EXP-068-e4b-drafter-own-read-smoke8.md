# EXP-068 — Drafters copy OLD from their own read, not from the reader's REGION (smoke-8 screen, D-008 edit reliability)

**Date:** 2026-11-10
**Type:** smoke-8 screen, ~0.35 L4x4-h (EXP-064 0.353, EXP-066 0.350 GPU-h at kernel wall about 1260 s; each of the 40 drafter turns adds one model turn and one `read_file`, the five reads of a task run one at a time). One push, no upload, no dev-48.
**Cohort:** smoke-8
**Ladder:** L2. L0 and L1 are section 1 (EXP-067 chain diff, the EXP-064 and EXP-066 traces, and the EXP-063 trace read for the reproducer finding).
**Pre-registered:** this file is committed before the push. Sections 3-5 are written blind and are not revised.
**Serves:** D-008 (`knowledge/directions/D-008-e4b-loop-restart-pipeline-stages.md`), the edit-reliability branch that EXP-067 pointed to: the reader's REGION is the origin of 11 of the 12 not-found failures that are not stale.
**Relates:** EXP-064 (the base tree, `candidate-loc`), EXP-067 (the method and references), EXP-066 (reader search form; its two reader-prompt lines 3 and 10 are not touched here, so a later fuse is a clean merge), EXP-063 (the reproducer, section 1.3), EXP-065 (text-form counter).

## 1. Why this, now (zero GPU)

### 1.1 What EXP-067 counted on the EXP-064 tree

Of the 31 failed applier edits over EXP-061-r, EXP-062-r and EXP-064-loc, 23 were classified. The reader's REGION is the origin of **R1 = 11** (rich_3468 6, fastapi_14605 5, both on EXP-064-loc); the drafter's own copying (D) is 0, the applier's (P, O, X) is 1 (O). The drafters copy the REGION faithfully, so the REGION's defect reaches the applier. The first applier edit applies on **6 of 8 task-runs on EXP-064-loc** (the two that do not: requests_7205, argument loss; rich_3468, R1). 2 of the 11 R1 failures came after the applier re-read the file and still pasted the reader's defect, so telling the applier to read is not enough (EXP-067 section 9.5).

The change here moves the source of OLD: the reader no longer copies code; it names FILE and LINES, and each drafter opens those lines itself and copies OLD from that result in its own turn.

### 1.2 What a drafter sees (read from the ADK source, not from a prompt dump)

- `include_contents: none` keeps the turn starting at the latest event authored by the user or another agent: for a drafter, the reader's final event (shown as "For context" text). The drafter's own tool-call and tool-response events after it are included (`data/src/google_adk/google/adk/flows/llm_flows/contents.py:542`, `_get_current_turn_contents`), so a tool works under `none`. Events of sibling branches (`...draft.drafter_M`) are filtered by `_is_event_belongs_to_branch`; the reader's events (no branch) are always visible.
- `output_key` (`llm_agent.py:830-871`) saves state only on a final-response event with a non-thought text part, so a drafter's tool-call event does not write `draft_N`; the text after the read does.
- `swegemma/tools/base.py:72-113`: every tool call goes through `budget_gated` under one global `ctx.tool_lock`, and `check_budget` counts each call against `max_tool_calls`. Five drafters' reads therefore run one after another (no race), add at most 5 calls to a task (45 cap; the largest call count in EXP-064 and EXP-066 was 18 on rich_3468) and about 8 s worst case (`read_file` median 1.5 s, p90 5.7 s).
- `read_file` (`tools/workspace.py:88-177`) truncates at 150 lines and 10,000 characters and returns JSON with `content` (no line-number prefix), `start_line`, `end_line`, `total_lines`.
- Every non-partial model event of any agent counts as an LLM call (`context.py:277-299`), so each drafter adds one model turn per tool round to `n_turns`.
- Compaction (`reference/compaction.md`, issue 7324): in-flow compaction fires at a latest prompt of 14,336 tokens or more and can touch sibling branches. The reader's last prompts are under 10k (EXP-066 httpx 7,370; EXP-064 up to 9,601), a drafter prompt is about 2.6k, so the exposure at the drafter stage is low; the in-flight parallel function-call events are what issue 7324 is about, and row 1 names it if it shows.

### 1.3 Why the EXP-063 reproducer made no tool call (zero GPU, desk check)

The lead's question: the reproducer (EXP-063 `candidate-p`) is an LlmAgent with `read_file`, `run_command`, `get_status` and `write_file`, and called nothing on 8 of 8 tasks, where the reader of the same tree called `run_command` on 8 of 8.

Compared (files `experiments/EXP-063/candidate-p/prompts/reproducer.md`, `sub_agents/reproducer.yaml`, against `prompts/reader.md`, `sub_agents/reader.yaml`; `runs/EXP-063-p/traces/`):

| | reader | reproducer |
|---|---|---|
| `include_contents` | default | default (same) |
| tools declared | 3 | 4 |
| "your first reply must be a tool call, not text" | **present** (reader.md line 9: "Your first reply must be a tool call, not text") | **absent** |
| where the tool use is asked for | at the top of its job, with a penalty sentence ("whole team fails") | inside step 1 and 2 of a numbered list, after the report and a paragraph on the team |
| the last message it sees | the task message | the reader's finished report ending in `END` |
| the final form | an answer after the work | `TEST: ... RESULT: ... END`, which can be written with no tool call |
| trace: its first turn | a tool call | in each of the 8 traces, exactly 2 trace entries authored by `reproducer` (a thinking entry and a final entry from one model call), no tool-call entry; on rich_3006 that call has 4,713 prompt tokens and 1,763 completion tokens |

**Finding (probable, not proven; no prompt dump exists):** the reproducer was never told to open with a tool call, and its answer form is one a text reply satisfies, with the reader's `END`-closed report as the last message in its window. The one thing the drafters share with it is exactly those three: no first-call line (the EXP-064 drafters were told they had no tools), an answer form a text reply satisfies, and a window whose last message is the reader's `END`-closed report. So it is fixed here in the drafter prompts by the lead's two changes: each drafter prompt **opens** with the reader's hard rule adapted ("Your first reply must be a read_file call, not text. An OLD written without that read is wrong and every edit built on it fails."), and the read step comes before the angle, the location and the format. What is not removable is the last-message shape (`include_contents: none` shows the reader's report); the adherence row (section 4, row 2) measures whether the opener is enough. The cause might also be the 4-tool declaration or thinking; that is not separable from these traces and is recorded as unknown beyond the three shared items above.

### 1.4 References (EXP-064-loc, counted in EXP-064 section 9, EXP-067 section 9)

First applier edit applies 6 of 8; R1 failures 11 (2 task-runs); F >= 2 on 2 of 8; G any 7 of 8; G1 5 of 8; empty patches 1 of 8; mean wall 100.0 s; 0 cap hits; tool_free 0 of 8; text-form calls 0.

## 2. Design

One variable: the source of OLD. It is the drafter's own `read_file` result, not the reader's REGION. Three prompt edits carry it (the reader's report form, the five drafters, one applier sentence) and the five drafter yamls carry the tool.

| | value |
|---|---|
| tree | `experiments/EXP-068/candidate-read/` = `cp -r experiments/EXP-064/candidate-loc` (the base tree is committed with `i/lf` blobs, so the copy equals the committed tree), then the edits below |
| `prompts/reader.md` | line 1: the sentence "Only you can open files, so what you copy into the report is all the later stages will ever see of the code" becomes "Only you search the repository, so the file and the line numbers you give are all the later stages will have to find the code; each writer opens those lines itself". Section 4: `LINES:` is now two numbers with a hyphen (from the `read_file` call's `start_line` and `end_line` or from `git grep -n`); the `REGION:` block and its copy instructions are deleted, "Do not copy any code into the report" is added; "FILE, LINES, REGION and CHANGE" becomes "FILE, LINES and CHANGE". **Lines 3, 9, 10, 11, 13 and 16 are untouched** (EXP-066 edits lines 3 and 10; line 9's "its region cannot be exact" and line 11's "You must open the lines you will quote" stay as the search and read sections stay) |
| `prompts/drafter_1..5.md` | opens with the hard rule; then the identity and location line (with the fall-back to LOCATION 1 for writers 2 to 5); then Step 1, the read: `read_file` exactly once, `filepath` = the location's FILE, `start_line` = first LINES number minus 5 (at least 1), `end_line` = last LINES number plus 5, no other call; no FILE or LINES: no call and `NO DRAFT`; then Step 2, the angle (each angle sentence kept, with "the region" changed to "the lines you read" where it said so); then `{plan?}`; the rules (OLD copied character for character from the `read_file` result, plain text with real line breaks and quotes, not the escaped tool form, 3 to 12 contiguous lines, never a line not in that result; NEW; no tests and no comments) and the same FILE / OLD / NEW / WHY / END form. "You have no tools and must not call any" is gone |
| `sub_agents/drafter_1..5.yaml` | `tools: []` -> `tools: [read_file]`; one history comment line each. `include_contents: none`, `output_key`, temperatures (0.3, 0.5, 0.7, 0.9, 1.0), `max_output_tokens` 3072 and `thinking_budget` 1024 unchanged |
| `sub_agents/draft.yaml`, `reader.yaml`, `applier.yaml` | one history comment line each (and `draft.yaml`'s description no longer says "tool-less") |
| `prompts/applier.md` | line 44 only: "on the region the reader named" -> "on the FILE and LINES the reader named" |
| diff | `diff -ru experiments/EXP-064/candidate-loc experiments/EXP-068/candidate-read` shows 15 changed files (7 prompts, 8 yamls): `prompts/{applier,reader,drafter_1..5}.md` and `sub_agents/{applier,draft,reader,drafter_1..5}.yaml`. `agent.yaml`, `eval_config.yaml`, `configs/`, `prompts/root.md` and `sub_agents/pipeline.yaml` are byte-identical. The full diff is the pair of committed trees (30 KB; the command is reproducible and not pasted) |
| lint | `python tools/validate_submission.py experiments/EXP-068/candidate-read --official --strict --json`: 1 error, the 18.00 h gate, which `--skip-budget-gate` demotes (as EXP-064, EXP-066); 2 warnings carried (the applier's `submit_patch`, `timeout_seconds` 240); no new warning |
| eval config | `timeout_seconds` 240, `max_tool_calls` 45, `max_time_minutes` 8, `max_turns` 120 (EXP-064's) |
| zip | `dist/EXP-068-read.zip`, sha256 in section 8. Packed with `--skip-budget-gate`: 8 min is above the 4.5 min packing gate (18.00 h nominal; the same override and reasoning as EXP-061, EXP-062, EXP-064, EXP-066). **Not an upload.** |
| notebook | `notebooks/exp068_read/`, kernel `rainm4/gemma4-exp068-read` |
| cost | ~0.35 GPU-h; the slot rule is cleared (both other kernels COMPLETE at 16:24 UTC) |

**Known limits of the design, written before the run.**
1. **The window can miss.** The `read_file` result has no line-number prefix, so a reader that narrows LINES by counting gives numbers that can be off by more than 5, and the drafter's window then excludes the code the CHANGE line names. The drafter then copies a faithful OLD from the wrong lines; the edit applies (no R1) and fixes nothing. G (a draft on a gold file) cannot see this; the row-5 condition G >= 6 is a proxy and section 9 will name the tasks whose window missed the CHANGE.
2. **Fabricated OLD.** A drafter that skips the read writes OLD from the reader's CHANGE line and memory. The hard rule is the guard; row 2 and row 3 count the failure.
3. **Drafters 2 to 5 fall back to LOCATION 1** when the report has fewer locations, so up to five concurrent reads of one file occur on a task with L = 1 (serialized by the lock, harmless).
4. **Text-form calls.** The E4B's native tool-call form is fragile to a longer prompt and to a tool declaration (`knowledge/lessons-e4b-loop.md`); a drafter that writes its call as a fenced block makes no native call. `n_text_form_calls` and `tool_free` count it; row 3 is the guard.
5. **A drafter 150-line truncation.** A LINES span over about 140 lines reads only its first 150 lines (the tool's cap). The reader has been asked for 25-line regions and gave at most 120-line reads; the case is recorded if seen.
6. **Issue 7324 and the reader's compaction** are listed in 1.2; not expected, named if seen (row 1).
7. **n = 8 and the reader's run-to-run variation.** The reader picks a different file or region between runs of an unchanged prompt (EXP-061, EXP-062, EXP-066), so a first-edit change on one task is not read alone.

## 3. Endpoints, fixed in advance

Per task, from `official/traces/`, `task_results.jsonl`, `summary.jsonl` and the kernel log; by the same method as EXP-067 section 2 and EXP-064 sections 9 and 10 (no script is allowed to this agent; Grep and line-number reads of `traces/`).

- **A (drafter adherence).** Drafter turns, 40 (8 tasks x 5 drafters), counted as: (a) the first event of the drafter's own turn is a `read_file` call; (b) the drafter made exactly one `read_file` call; (c) the drafter made a `read_file` on its location's FILE (a mismatch is recorded); (d) **fabricated OLD**: the drafter's final text has an `OLD:` block and no `read_file` call earlier in its own events. Drafters with legitimate `NO DRAFT` and no call (the reader's report has no FILE or no LINES) are listed by task and are in the denominator of 40.
- **E1. First-edit-applies per task-run:** the applier's first `edit_file` call returns `status` ok (EXP-067 section 9.3). Reference 6 of 8.
- **E2. R1-type failures:** failed applier `edit_file` calls classified not-found by the EXP-067 method (first match, from the live file outward), where the failure is **OLD differs from the lines the drafter's own read returned** (the drafter's copy; the reader's REGION no longer exists). Argument loss (A), path-form (S), stale (E) and non-unique (M) are counted apart as in EXP-067. Reference R1 = 11 on 2 task-runs.
- **E3. F, G and G1** as in EXP-064 section 3 (F distinct target files across the 5 drafts; G any draft on a gold file; G1 on the first gold file). References F >= 2 on 2 of 8, G 7 of 8, G1 5 of 8. Recorded, with G >= 6 as a promote condition (limit 1 above).
- **Text-form counter:** `n_text_form_calls`, `tool_free` (EXP-065), and the drafter-authored text-form calls among them (a call-shaped fence in a drafter's final text).
- **Harm inputs:** time, call and turn cap hits; empty patches (reference 1 of 8); mean wall against 100.0 s (EXP-064), 99.8 s (EXP-066); the call count per task against 45; `scratch_in_patch`; any drafter `read_file` of a path outside `/workspace`; compactions and the largest prompt against 14,336.
- **Window miss (limit 1):** tasks where the lines a drafter read do not contain the target of the reader's CHANGE line. Recorded only.
- **Recorded only:** resolves (never an endpoint), the draft the applier kept, the applier's edit failures by class.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Rows 1 to 3 are gates: any that holds is reported, and if any holds the endpoint rows 4 to 6 are **not read** (the numbers are still recorded). The endpoint rows are first-match.

| # | outcome | reading |
|---|---|---|
| 1 | **Infrastructure.** Any of: an `err` with a traceback, a sandbox execution error or a compaction error; the tree does not run on some task; the root fails to transfer to `pipeline`; a drafter request fails to build, or a `draft_N` state key is lost after a tool round | A bug, not a reading. Name the task and the step. |
| 2 | **Not exercised (drafter adherence).** **20 or fewer of the 40 drafter turns open with a `read_file` call** (A (a)) | The hard rule did not make the drafters call the tool; the E4B writes OLD from memory. No decision about the source of OLD, no endpoint read. Record the drafters' first-turn kind (text, text-form call, call on a different path). This is the EXP-063 reproducer outcome again, and the lead decides the next form (a non-LLM or applier-side route; see section 5). |
| 3 | **Harm.** Any of: **empty patches 3 or more of 8**; any time, call or turn cap hit; **mean wall over 150 s**; **any tool-free task**; **any text-form call authored by a drafter**; **fabricated OLD (A (d)) on 8 or more of the 40 drafter turns**; `scratch_in_patch` true on any task or a drafter `read_file` outside `/workspace` (a stray path) | The change costs more than it buys or breaks the E4B's tool use. Name the tasks and the counts. A task over 240 s is named, not a row. |
| 4 | **Kill.** Rows 1 to 3 did not fire, and **E1 <= 5 of 8** or **E2 R1-type failures >= 6** (more than half of the 11 of EXP-064) | A fresh read in the drafter's own turn does not make OLD match: the drafters (or the window, or the file state) corrupt it as the reader did, or the tree is worse than 6 of 8. The route is killed as a prompt-and-tool change on this tree; the remaining routes are a non-LLM applier step (a line-range edit tool for the applier) or a reader that stops listing 25-line regions at all. |
| 5 | **Promote.** Rows 1 to 4 did not fire, and **E1 >= 7 of 8**, **E2 R1-type <= 2**, and **G >= 6 of 8** | With the code in the drafter's own turn, the first edit applies on 7 or more of 8 and the reader's mis-copy failures have gone (the two that stay may be argument loss or non-unique matches, counted apart). A process reading on edit reliability, not on resolves. Promoted to a fused round with EXP-066's reader search form (the two share no reader line) and a dev-48 pair with the endpoint of section 5; the user's word is needed. |
| 6 | **No decision.** Anything else (for example E1 = 6 of 8, or E2 = 3 to 5, or G <= 5 with E1 >= 7) | Record per task. Resolves decide nothing. |

**Not rows, but binding:**
- Per-task resolves at n = 8 are never an endpoint; six of eight must flip the same way for p < 0.05.
- E1 of 7 of 8 is one task above the reference of 6 of 8 and the argument-loss failure on requests_7205 does not depend on this change, so row 5 reads a bound (the R1 failures gone, the first edit failing only for a reason outside this change), not a rate; it is not read as an effect size.
- A fabricated OLD that happens to match the file is still counted in A (d).
- The window-miss tasks are named whatever row fires.

**Blind prediction.**
- Drafter turns that open with a `read_file` call above 20 of 40 (row 2 not firing): about 0.7. The reader's rule held 8 of 8 in EXP-064 and EXP-066; the reproducer without it called nothing on 8 of 8; the drafter's window ends in the reader's `END`-closed report, which is the reproducer's condition.
- Any text-form call by a drafter: about 0.2. Fabricated OLD on 8 or more: about 0.15.
- Row 3 (harm): about 0.25. Row 2: about 0.25. Row 1: about 0.05.
- If rows 1 to 3 do not fire: row 5 about 0.4, row 4 about 0.2, row 6 about 0.4.
- Mean wall about 112 s (range 95 to 140): five extra model turns and five serialized reads add 10 to 15 s. 0 cap hits; the largest call count about 23.

## 5. What this does and does not license

**The screen can decide one of two things.**
- **Kill:** row 4, the route "drafter reads its own lines and copies OLD" on this tree. Row 2 kills nothing; it says the drafters did not follow the rule, and the reproducer shows the E4B does not call a tool it is not hard-ruled to call, so the next form is a path that does not depend on the E4B's tool choice (an applier-side `read_file` before the first edit, the applier already holds the tool).
- **Promote:** row 5 only. The dev-48 endpoint it should carry: **first-edit-applies per task-run over the 48** (paired against a rerun of the EXP-064-loc tree on the 48, or against the pipeline tree of record), with **R1-type failed edits per task-run** as the bound and the empty-patch count as the harm input; **resolves recorded, not the endpoint** (n = 48 cannot see the move that edit reliability would make: EXP-067 section 9.5). A dev-48 pair needs the user's word and a critic `prereg` (above 1 GPU-h).

**Does not license:** any resolve or LB claim, any upload or dev-48 run without the user, a statement that fewer failed edits make a better fix, or a claim about the reader's location quality beyond F, G and G1 (the window-miss list is recorded only).

## 6. Exact commands

```
python tools/validate_submission.py experiments/EXP-068/candidate-read --official --strict --json
python tools/pack_submission.py --src experiments/EXP-068/candidate-read --out dist/EXP-068-read.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed dist/EXP-068-read.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-068-read"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp068_read/kaggle_eval_l4x4.ipynb
kaggle kernels push -p notebooks/exp068_read
```

Analysis, a separate job, after `kaggle kernels status` says COMPLETE:
1. `kaggle kernels output rainm4/gemma4-exp068-read -p runs/EXP-068-read/`, then flatten.
2. `python -I -X utf8 tools/analyze_traces.py runs/EXP-068-read --cap-minutes 8 --max-calls 45`.
3. `python -I -X utf8 tools/run_forensics.py forensics runs/EXP-068-read` and `compare runs/EXP-064-loc runs/EXP-068-read`.
4. A (a) to (d) per drafter, E1, E2 (EXP-067 method against the drafter's own read result), E3, harm inputs and window misses by Grep and line reads of `traces/`.

## 7. Defects in this pre-registration, logged after the fact

1. **(Known at pre-registration.)** The EXP-063 reproducer cause is read from prompt text and 8 trace shapes, not from a prompt dump; it is "probable" (section 1.3).
2. **(Known at pre-registration.)** The tree was built by `cp -r` plus edits; `tar` is outside this agent's commands, so no `git archive` repack was run.
3. **(Known at pre-registration.)** The thresholds 20 of 40, 8 of 40 fabricated and R1 >= 6 / <= 2 are chosen, not derived; n = 8 task-runs with 40 drafter turns gives a count that is a bound on a behavior, not a rate. Drafter turns within a task share a reader report, so the 40 are not independent.
4. **(Known at pre-registration.)** Drafters 2 to 5 on a task with L = 1 read the same lines as drafter 1; their adherence counts are not independent of drafter 1's.

**Added 2026-11-10 after the critic's D-009 review (`experiments/EXP-067/critic.md`, d372a76 and 53be9fb), while the kernel was still RUNNING and before any output was downloaded. Nothing above section 7 changes. Items 5 to 10 are interpretations or added descriptive counts, fixed before the results; they change no row except where item 5 and item 9 say so.**

5. **Stray path (row 3), interpretation.** A drafter `read_file` "outside /workspace" means an absolute path that resolves outside the workspace (for example under /usr or /tmp). A quote-wrapped path or a nonexistent relative path is a read failure, not a stray path. Read failures are counted by kind (quote-wrapped path, not found, other) and are not harm.
6. **Fabrication, added counts (descriptive, no row).** A (d) counts an OLD written with no read call before it. Two counts are added: OLD written after a failed or empty read, and drafter read errors by kind (quote-wrapped path, not found, other). Row 3's "8 or more of 40 fabricated" still uses A (d) only.
7. **Applier context, descriptive.** Per task, the applier's first prompt tokens, its maximum prompt tokens and the compactions, against EXP-064-loc. The applier now also sees the five drafter reads. rich_3468 on EXP-064 started at 14,383 tokens, already above the 14,336 threshold.
8. **Location, descriptive.** LINES is now the reader's read window, so the drafter picks the edit spot inside it. G and G1 are reported by task, and fastapi_14301 and rich_3006 are named in the report whatever the numbers are.
9. **Row 1 (infrastructure) also covers** a summarizer or compaction `ValueError` and a blank or crashed run.
10. **Direction.** EXP-068 serves D-009 round 1. D-008's ranks 2 and 3 ended at its midterm (a5e02ea); the header's "Serves: D-008" line is kept as written and read as superseded by this item.

## 8. Built (below the line; nothing above changes)

---

- **Changed files vs EXP-064 `candidate-loc`:** the 15 listed in section 2.
- **Validator** (`--official --strict`): 1 error, the 18.00 h gate, demoted by `--skip-budget-gate`; 2 warnings carried from EXP-064; no new warning. The official validator could not be imported.
- **Pack:** `RESULT: VALID (0 errors, 3 warnings)`, PACK OK, 20 files, `dist/EXP-068-read.zip` (gitignored). **sha256 `176a005df9d2b210dfe50dee6931be9bd00444a63577dd9717198cd2b6a2a326`.**

- **Pre-registration commit:** 570e52b (this file, the candidate tree, the README row). All 20 candidate blobs were written with LF (0 CR bytes in the edited files).
- **Notebook:** `notebooks/exp068_read/` (commit 3874589), built with the section 6 command. Against `notebooks/exp066_srch/` the notebook differs in exactly two lines: `EXP_ID` and `SUBMISSION_B64`. `kernel-metadata.json` is EXP-066's with only `id` and `title` changed, to `rainm4/gemma4-exp068-read`. Nothing was copied to `out/submission.zip`.
- **Kernel id for the push:** `rainm4/gemma4-exp068-read`, directory `notebooks/exp068_read`.

## 9. Results (analysis job, 2026-11-10; sections 1 to 8 above are unchanged)

Kernel `rainm4/gemma4-exp068-read` v1, COMPLETE. Kernel wall about 22.8 min (last log stamp 1369 s, so about 0.38 GPU-h); agent wall 882.6 s over the 8 tasks. Output in `runs/EXP-068-read/` (gitignored); `summary.jsonl` copied to `experiments/EXP-068/read/summary.jsonl`; traces stay out of git. Commands as section 6, `analyze_traces.py --cap-minutes 8 --max-calls 45`, `run_forensics.py forensics` and `compare runs/EXP-064-loc runs/EXP-068-read`; A, E1 to E3, window and the applier counts by Grep and line reads of `traces/`.

### 9.1 Per task

| task | wall s | calls | compactions | nudges | edit fails | applier first / max prompt tok | E1 | resolved |
|---|---|---|---|---|---|---|---|---|
| requests_7309 | 72.1 | 8 | 0 | 0 | 0 | 3,033 / 9,780 | ok | no |
| requests_7205 | 59.2 | 10 | 0 | 0 | 0 | 7,272 / 9,193 | ok | no |
| fastapi_14448 | 88.4 | 13 | 0 | 0 | 0 | 10,411 / 13,200 | ok | no |
| fastapi_14301 | 64.5 | 12 | 0 | 0 | 0 | 8,843 / 13,075 | ok | **yes** |
| httpx_3672 | 203.9 | 17 | 3 | 0 | 2 (applier-own) | 20,709 / 24,519 | ok | no |
| fastapi_14605 | 111.3 | 17 | 1 | 0 | 3 (A) | 10,343 / 14,390 | **fail (A)** | no |
| rich_3468 | 155.3 | 21 | 1 | 0 | 8 (S 1, R1-type 5, applier-own 2) | 14,392 / 14,392 | **fail (S)** | no (empty patch) |
| rich_3006 | 127.9 | 12 | 0 | **5** | 0 | 10,708 / at least 14,079 | ok | no |

Resolved 1 of 8 (EXP-064-loc 2 of 8; the compare shows rich_3006 as the only paired difference, McNemar p = 1.0; recorded, never an endpoint). Mean wall 110.3 s (median 99.85 s; EXP-064-loc 100.0 s, EXP-066 99.8 s); httpx_3672 at 203.9 s is the longest (under the 240 s naming line). Largest call count 21 (rich_3468). `n_undeclared_tool` is 1 on every task (2 on rich_3006): the root's `submit_patch` ValueError "Tool 'submit_patch' not found" after the transfer, the known root artifact, not a compaction error.

### 9.2 A: drafter adherence (40 turns)

- **A (a), first event is a `read_file` call: 36 of 40.** All 5 drafters on 7 tasks read first in pass 1 (35), plus requests_7309 drafter_2 (it read the directory `src/requests/`, "Is a directory"). The 4 that did not: requests_7309 drafters 1, 3, 4 wrote a compliant `NO DRAFT` (the reader's report had no FILE or LINES, section 9.5) and requests_7309 drafter_5 wrote a text line `read_file(filepath="src/requests/utils.py", start_line=1, end_line=100)` as its final text (see row 3, section 9.7). On rich_3006 the root transferred a second time; all 5 drafters of pass 2 wrote `NO DRAFT` with no read (the reader had no FILE or LINES); they are legitimate and are not in the 40 of pass 1.
- **A (b), exactly one `read_file`: 36 of 36 that read** (35 + drafter_2).
- **A (c), the read was on the location's FILE: 35 of 36** (drafter_2 read a directory; no FILE existed).
- **A (d), fabricated OLD (an OLD block with no `read_file` call earlier in its own events): 0 of 40.**
- **OLD written after a failed or empty read (item 6): 0.** requests_7309 drafter_2 wrote `NO DRAFT` after the directory error.
- **Drafter read errors by kind (item 6): 1**, kind other (directory, not quote-wrapped, not nonexistent). Quote-wrapped 0; not found 0. **Stray absolute path outside /workspace: 0.**

### 9.3 Descriptive: OLD blocks that are not in the drafter's own read

This is not A (d) and no row uses it. 35 drafters wrote an OLD (all but requests_7309). Of them, **16 of 35 wrote an OLD that is not in their own read result**:

| task | OLD not in the drafter's own read | why |
|---|---|---|
| fastapi_14448 | 5 of 5 | window 62-76 (reader LINES 67-71) does not contain the CHANGE target `_unwrapped_call` (about line 77 on); d1 to d4 invented it, d5 copied a `for sub_dep` line with wrong indentation and a NEW equal to OLD |
| rich_3468 | 4 of 5 | window 2076-2124 (reader LINES 2081-2119) does not contain the target near 2063 (the reader had seen the write at 2063); d1, d3, d4, d5 invented OLD (d4's begins with `>>>`); d2's OLD is in the read but NEW = OLD (WHY says the snippet lacks the code) |
| rich_3006 | 5 of 5 | reader LINES 95-96, window 90-101; the lines `if param.default == param.empty:` and the others the drafters wrote are not in 90-101. **Checked against the 90-101 window only**, not against a wider read |
| fastapi_14605 | 1 of 5 | d4's OLD is in escaped `\\n` form with a trailing `"` (a form fault, not a window miss); d2's OLD matches but NEW = OLD; d5's OLD begins with `>>>` and matches |
| httpx_3672 | 1 of 5 | d2's OLD has one line (`self.recv_chunked = True`) beyond the window end 317, and its final text leaked a thinking channel; d4's final is a degenerate repetition loop (its first OLD block matches) |
| requests_7205 | 0 | all 5 in the read (d5's form is defective) |
| fastapi_14301 | 0 | all 5 identical, window 121-134 |
| requests_7309 | no OLD | no drafts |

14 of the 16 come from a window that excludes the target; 2 are form faults. **Window miss (limit 1): 3 of 8 tasks (fastapi_14448, rich_3468, rich_3006)**, whatever the row. Window held on fastapi_14301, requests_7205, fastapi_14605 (three locations), httpx_3672 (three locations: `_server.py` 33-37, `_parsers.py` 301-312 and 425-427). Whether the reader's LINES were miscounted or its location was wrong is not established per task here.

### 9.4 E1, E2 and E3

- **E1, first applier edit applies: 6 of 8** (reference 6 of 8). Fails: fastapi_14605 (three argument-loss edits at steps 19 to 21, then steps 23, 25, 26 applied) and rich_3468 (path-form S at step 22). **Both first-edit failures are form-class; content-class (not-found) first-edit failures: 0 of 8.** fastapi_14448 applied its first edit from the applier's own OLD (copied from the reader's earlier read of `models.py` 1-100), ignoring all five drafts; requests_7309's applier read, grepped, edited and submitted by itself (no drafts).
- **E2 failed `edit_file` calls: 13 on 3 task-runs** (summary `n_edit_fail` 2 + 3 + 8). By class: **A (argument loss) 3** (fastapi_14605); **S (path form) 1** (rich_3468 step 22: `filepath` `"rich/console.py"` double-quoted and the arguments garbled, "Source path /workspace/\"rich/console.py\" not found"); **R1-type (OLD differs from the drafter's own read) 5 failed calls on 1 task-run** (rich_3468 steps 23 d4, 24 d1, 25 d3, 26 d5 and 30 d1 again; 4 distinct drafts, all of them invented OLDs of section 9.3); **applier-own 4** (httpx_3672 2: a `def complete(self)` docstring OLD after a truncated read, not any draft; rich_3468 steps 28 and 29: after its own read of 2063-2100 it pasted a stray literal `\n` after an f-string); E (stale) 0; M (non-unique) 0. **R1-type 5 against the reference 11 on 2 task-runs** (EXP-064); but the R1-type edits that remain are copies of OLDs the drafter never read.
- **E3.** G (any draft on a gold file) **7 of 8** (fails only on requests_7309, no drafts); G1 **7 of 8**; F >= 2 on **2 of 8** (fastapi_14605: `exceptions.py`, `_compat/v1.py`, `dependencies/utils.py`; httpx_3672: `_server.py` and `_parsers.py`). The reader gave one location on fastapi_14301, fastapi_14448, requests_7205 and rich_3468. Named, as item 8 asks: **fastapi_14301** (resolved; 5 drafts, one location, window held, first edit applied) and **rich_3006** (G yes in pass 1; not resolved; window miss; 5 nudges; the pass-2 reader had no calls and the 5 drafters wrote `NO DRAFT`).

### 9.5 Harm inputs and the other counts

Empty patches 1 of 8 (rich_3468; reference 1). Time, call and turn cap hits 0. Mean wall 110.3 s (under 150 s). `tool_free` 0. `scratch_in_patch` false on all 8. Stray path 0. Compactions: httpx_3672 3 (EXP-064-loc 0), fastapi_14605 1, rich_3468 1 (EXP-064-loc: fastapi_14605 1, rich_3468 1); the rich_3468 first applier prompt is 14,392 against 14,383 in EXP-064 (both above 14,336, as item 7 foresaw); httpx_3672's first applier prompt is 20,709 (it now carries five drafter reads). Nudges 5, all rich_3006 (EXP-064-loc 0): the applier ended without a submit and the root was nudged to submit. `n_text_form_calls` 1: requests_7309's **reader** final is a JSON fence `{"tool_name": "run_command", ...}` (the analyzer's one hit, not drafter-authored); that reader report had no FILE or LINES, which produced on requests_7309 the three `NO DRAFT`, one read of a directory and one text-form read line.

### 9.6 Row 1 and row 2

Row 1 did not fire: no `err` with a traceback, no compaction or summarizer error in the log, no blank or crashed run, the root transferred to `pipeline` on 8 of 8, no `draft_N` key was lost after a tool round (drafters ran a tool round and 35 of 40 wrote a draft). The `submit_patch` ValueErrors in the log are the root artifact above. Row 2 did not fire: 36 of 40 is above 20.

### 9.7 Row 3, stated openly

Every other row-3 condition is clear: empties 1 of 8 (limit 3), no cap hit, mean wall 110.3 s (limit 150), no tool-free task, A (d) 0 of 40 (limit 8), no `scratch_in_patch`, no stray path. **One condition is ambiguous and is not settled here.** Row 3 reads "any text-form call authored by a drafter"; section 3 defines it as "the drafter-authored text-form calls among them (a call-shaped fence in a drafter's final text)", "among them" being the analyzer's `n_text_form_calls`. Whose call is it:
- **Literal section 3 reading: 0 drafter-authored.** The analyzer's one text-form call is the reader's JSON fence (requests_7309), and the analyzer's detector finds JSON-shaped values only.
- **requests_7309 drafter_5** wrote, as its final text and with no fence and no JSON, the line `read_file(filepath="src/requests/utils.py", start_line=1, end_line=100)`: a call written as text where a native call was required. The analyzer does not count it. On the substance of row 3 (the E4B writing a call as text) this is 1 drafter text-form call; under a literal fence-only reading it is not one.

I record both. The endpoint does not depend on which reading is taken: **if row 3 fires, rows 4 to 6 are not read (gate) and the numbers are recorded; if it does not fire, rows 4 to 6 read E1 = 6 of 8 (above the kill bound 5, below the promote bound 7) and R1-type = 5 (between 3 and 5, so neither the kill bound 6 nor the promote bound 2), so row 6.** Neither reading kills the claim and neither promotes it. I took no gate reading for the record beyond saying that the lead or the critic may read it either way and should know that this was a single instance, caused by an empty reader report and not by the drafter instruction.

### 9.8 Row fired

**Row 6, no decision.** Rows 1 to 3 are clear under section 3 as written (the pre-registered operationalization of row 3's text-form condition is a call-shaped fence in a drafter's final text; there is none). requests_7309 drafter_5's bare `read_file(...)` line is outside that definition and is recorded as an observation and a definition defect (9.7, 9.11 item 1), not applied after the result. No kill, no promote; the decision would be the same on the wider reading.

**Blind prediction check.** A (a) above 20 of 40 (about 0.7): held, 36 of 40. Drafter text-form call (about 0.2): 0 under the fence definition, 1 bare line under the broader one. Fabricated OLD on 8 or more (about 0.15): A (d) 0 (held), although the descriptive count of OLDs not in the read is 16 of 35, which A (d) was not designed to catch. Row 3 (about 0.25): see 9.7. Row 2 (about 0.25): did not fire. Row 1 (about 0.05): did not fire. Rows 4 to 6 given the gates clear (0.2, 0.4, 0.4): row 6, the most probable of the blind readings. Mean wall about 112 s (95 to 140): actual 110.3 s, held. 0 cap hits: held. Largest call count about 23: actual 21.

### 9.9 D-009 midterm inputs (counts)

- **Content-class (OLD not found) first-edit failures: 0 of 8** (reference 2 of 40 task-runs on the earlier trees, i.e. 0 to 1 per 8). The two first-edit failures are form-class: A (fastapi_14605) and S (rich_3468).
- **Drafter copy mismatches (OLD not in the drafter's own read): 16 of 35 drafts with an OLD** (14 window misses on 3 tasks, 2 form faults); A (d) fabrication by the pre-registered definition 0 of 40.
- **Content-class not-found failures later in the task: 9 of the 13 edit failures** (R1-type 5, applier-own 4); form-class 4 (A 3, S 1). The first edit is the E1 endpoint; the later failures are the cost the applier pays after a bad draft.
- **Gate rows: row 1 no, row 2 no, row 3 ambiguous (section 9.7), one drafter text-form line.**
- E1 6 of 8 (reference 6 of 8); R1-type 5 on 1 task-run (reference 11 on 2).

### 9.10 Reading for the next round (lessons-ready)

The drafters followed the hard first-call rule (36 of 40; no fabricated OLD by the A (d) definition), so the tool-choice failure of the EXP-063 reproducer did not recur and the route is exercised. What it exposed is not drafter behaviour but the **window**: the drafter's read is bounded by the reader's LINES, and on 3 of 8 tasks (fastapi_14448, rich_3468, rich_3006) that window does not contain the CHANGE target, so 14 of the 16 mismatching OLDs are drafters inventing the code the window lacked, then the applier either failed on those drafts (rich_3468: R1-type 5) or ignored them and read or recalled the file itself (fastapi_14448, requests_7309, rich_3468 step 27). The reader's REGION copy failure of EXP-064 (R1 11) became a window-miss failure; E1 stayed at 6 of 8 and the two first-edit failures are argument-formation (A, S), which the design does not touch and which EXP-069 attacks. The route also cost context (httpx_3672 3 compactions against 0; rich_3468 over the threshold at first prompt) and five nudges on rich_3006. A 3-of-8 window-miss rate is a count of a mechanism, not a rate, and n = 8 cannot separate a miscounted LINES from a wrong location. The next form, if the lead takes it, is one that does not depend on the reader's line numbers matching the file: an applier-side read with line prefixes, or a LINES anchored on a string the drafter reads around, rather than more drafter prompt text. The empty reader report (JSON fence, no FILE) is a separate recurring fault that left the 5 requests_7309 drafters with three `NO DRAFT`, a directory read and a text-form read line.

### 9.11 Defects and limits of this analysis

1. The row-3 ambiguity of section 9.7: the definition was fence-based, the row text was not; not retrofitted.
2. The rich_3006 pass-1 count of 5 mismatches was checked against the 90-101 window only.
3. Counts were taken by Grep and line reads of `traces/`; the A (a) to (d) and OLD-in-read classifications are by hand and were not re-run by a second reader.
4. Mean wall is the mean of `wall_s` in `summary.jsonl` (110.3 s); the harness-side total of 14.2 min seen in the forensics output is a different clock and is not used.
5. The EXP-069 applier bare-path recipe was not in this tree; the rich_3468 S event (a double-quoted `filepath` with garbled arguments at the first edit, then five R1-type retries) is one more data point for it.
6. The 40 drafter turns are not independent (shared reader report per task, item 4 of section 7); every count above is a bound on a behavior.

## Status

**2026-11-10 ANALYZED**: kernel COMPLETE. Row 6 (no decision); rows 1 to 3 clear under section 3 as written. requests_7309 drafter_5's bare `read_file(...)` line is outside the fence definition and is recorded, not applied; no kill and no promote either way. A (a) 36 of 40, A (d) 0, E1 6 of 8, R1-type 5, G 7 of 8, window miss on 3 of 8; resolved 1 of 8. Section 9 above.

2026-11-10 (earlier): pre-registered (570e52b), candidate packed with sha `176a005d...a2326`, notebook built (3874589). **Pushed 2026-11-10**: kernel version 1, `rainm4/gemma4-exp068-read`, first status RUNNING (not QUEUED, so no second check). Next, when the lead reports COMPLETE: `kaggle kernels output rainm4/gemma4-exp068-read -p runs/EXP-068-read/`, flatten, then the analysis commands in section 6, then apply section 4.
