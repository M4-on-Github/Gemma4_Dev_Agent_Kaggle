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

## 8. Built (below the line; nothing above changes)

---

- **Changed files vs EXP-064 `candidate-loc`:** the 15 listed in section 2.
- **Validator** (`--official --strict`): 1 error, the 18.00 h gate, demoted by `--skip-budget-gate`; 2 warnings carried from EXP-064; no new warning. The official validator could not be imported.
- **Pack:** `RESULT: VALID (0 errors, 3 warnings)`, PACK OK, 20 files, `dist/EXP-068-read.zip` (gitignored). **sha256 `176a005df9d2b210dfe50dee6931be9bd00444a63577dd9717198cd2b6a2a326`.**

## Status

2026-11-10: built and packed; pre-registration commit pending in this save. Next: notebook build, commit, push `rainm4/gemma4-exp068-read`.
