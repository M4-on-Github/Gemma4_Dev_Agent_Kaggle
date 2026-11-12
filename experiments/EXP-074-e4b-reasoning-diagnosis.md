# EXP-074: where the E4B's reasoning leaves gold (zero-GPU diagnosis)

**Date:** 2026-11-11
**Type:** zero-GPU analysis (L1 trace mining against the gold patches), 0 L4x4-h. No kernel, no upload.
**Cohort:** none (existing runs only: EXP-038 on dev-48, 48 task-runs; the pipeline and single-loop runs on smoke-8 listed in section 2.1)
**Ladder:** L1. It ranks the levers for the open-ended E4B loop; it decides no tree by itself.
**Pre-registered:** yes. Sections 2 to 4 (sample, classification rules, blind predictions) are committed before any classification is computed. Only format checks were run before this commit (section 2.6). Results are appended as section 6 and apply the rules as written; defects go in section 5.
**Serves:** D-011 (`knowledge/directions/`, the open-ended E4B loop the user set on 2026-11-11: "diagnose the problems of the model's reasoning and fix them how we can from what we can modify to the harness"); its stopping rule is a dev-48 run at 16/48 or more with projected worst case 11 h or less. E4B stands at 5/48 (EXP-038).
**Relates:** EXP-038 (the single-loop dev-48 run), EXP-063 `refs.py` (draft parser reused), EXP-070 (desk checks over the pipeline runs), EXP-071 and EXP-072 (the last two pipeline rounds).

## 1. Questions

- **Q1, divergence stage.** For each unresolved task-run: where the submitted patch first leaves gold (E, F, R, C, S, section 2.3). Counted per task-run and per distinct task.
- **Q2, draft discriminator (pipeline trees only).** When the applied patch misses gold (E, F or R), does any of the drafts overlap a gold region? Often: selection is the lever. Rarely: selection and verify rounds are dead, and the lever is comprehension or generation.
- **Q3, reasoning text.** Is thought text kept? If so, for every F and R run of EXP-038 and every F and R pipeline run: when does the reasoning name the file it later edits; does a search use the issue's key identifiers before the first edit; is the edited file read before it is edited; was a gold source file shown to the model (in a tool output) before the first edit. Tokens per model step against the 4096 thinking budget.
- **Q4, carrier.** The single loop (EXP-038, EXP-053-r) against the pipeline on the 8 shared ids: stage distributions.
- **Q5, headroom.** Per stage, the levers that can touch it (tree, prompts, sampling, `eval_config`, registered tools; no LoRA), an opportunity count fixed in section 2.5, and how far the sum falls short of +11 (5/48 to 16/48).

## 2. Rules, fixed before computing

### 2.1 Sample

- **Dev-48 (the headline):** `runs/EXP-038-e4b-dev48`, single loop, 48 task-runs, resolved 5 by its `summary.jsonl`. Every headline count is over its 43 unresolved task-runs.
- **Pipeline, smoke-8 (listed in the dispatch):** `runs/EXP-064-loc`, `EXP-066-srch`, `EXP-068-read`, `EXP-069-argform`, `EXP-071-anchor` (downloaded; 8 traces) and `EXP-072-verify`. All are the reader, 5 drafters, applier tree with thinking budget 4096.
- **Pipeline, smoke-8 (not in the dispatch, reported apart):** `runs/EXP-061-r`, `EXP-062-r`, `EXP-063-p`, the earlier pipeline trees (drafts, applier; EXP-063-p adds a reproducer). They enter Q1 and Q2 in a separate column, never in the dispatch-sample totals.
- **Deviation from the dispatch:** `runs/EXP-053-r` is a **single-loop** tree (its `agent/` has `prompts/system.md` and no `sub_agents/`; files nested one level down at `runs/EXP-053-r/runs/EXP-053-r/`). It has no drafts, so it is on the single-loop side of Q4 and outside Q2.
- The smoke-8 ids are all in dev-48 (8 shared ids), so Q4 is paired on 8 tasks.
- **Resolved and empty** are taken from each run's `summary.jsonl` (`resolved`, `patch_empty`), not recounted. The submitted patch text is `task_results.jsonl` `patch` (a `diff --git` unified diff against the base commit; checked on the 38 non-empty EXP-038 patches).
- **Gold:** `data/raw/tasks.jsonl` field `patch` only (never `test_patch`). Snapshots `data/local/snapshots/<id>.tgz` read as data, never extracted.

### 2.2 Line sets

- **Changed old-side lines of a unified diff hunk.** Walk the hunk from its `@@ -a,b` start: a `-` line contributes its old line number; a run of `+` lines with no `-` line contributes the insertion point as the two old lines around it (n-1 and n, n the next old line); context lines advance the old counter. Hunk header ranges are not used (context width differs between patches).
- **Gold source files:** files in gold `patch` not under `docs_src/`, `docs/`, `scripts/` or `tests/`. A task whose gold has no such file (1 of 48 by the format check) uses all its gold files. A sensitivity count uses all gold files on every task.
- **Gold regions:** per gold source file, the changed old-side lines, merged into one region when two changed lines are within 2 * M lines of each other, M the margin.
- **Margin M = 5 lines (primary).** A changed line x "touches" a region [lo, hi] when lo - M <= x <= hi + M. Sensitivity margins: 0 and 15.
- **Draft line set (Q2).** A draft is any drafter `final` message with a `FILE:` line and an `OLD:` block (EXP-063 `refs.py` cut rules; a `NEW:` block is not required to locate it). Its OLD block is located in the snapshot's FILE (path as given, a leading `/` or `./` stripped; matched by suffix against the snapshot's paths when not found as given): first by exact substring after stripping outer blank lines, then by the sequence of its non-blank lines compared with `.strip()` against the file's non-blank lines. The first match gives the OLD range [s, e]. Its line set is the lines `difflib` marks changed between OLD and NEW, offset by s, when NEW is present; else the whole [s, e]. A draft whose FILE is not in the snapshot or whose OLD is not located is **unlocated**. A draft is **appliable** when it has a NEW block and its OLD was located by exact substring.

### 2.3 Divergence stage (unresolved task-runs; first match)

| class | rule |
|---|---|
| **E** | `patch_empty` true in `summary.jsonl` |
| **F** | the patch touches no gold source file (scratch, test or other files only) |
| **R** | the patch touches a gold source file, but none of its changed lines touches a gold region at margin M |
| **C** | at least one gold region is touched, not all of them |
| **S** | every gold region is touched; the change is wrong (unresolved) |

C and S are exclusive by coverage; the order E, F, R, C, S is the precedence. **Resolved task-runs are classed by the same rule, as a validity check of the instrument** (a resolved run in F or R means gold is not the only fix; reported, not reclassed).

**Distinct-task rule.** Per distinct task: its EXP-038 class (the headline, one run per task); for the pipeline sample, the modal class over its unresolved runs, ties broken toward the earlier stage in the order E, F, R, C, S; and the number of runs in each class.

### 2.4 Q2 and Q3 definitions

- **Q2 count:** pipeline task-runs in E, F or R with at least one draft whose line set touches a gold region at margin M (**draft-overlap**); of those, the ones with such a draft that is also appliable. Also: drafts naming a gold source file at all; usable drafts per run (printed per run, so a parser miss cannot pass for a low count). Per distinct task as well.
- **Thought text:** a model step whose `extra.event_type` is `thinking` and whose message is non-empty. Counted per run (steps, task-runs with any).
- **Q3 per run** (F and R runs of EXP-038, all of them; F and R pipeline runs, reader and applier steps):
  - **(a) commit:** the index of the first model step whose thinking message names the file later edited (its path or its basename), against the index of the first `edit_file` call; and the number of distinct repository `.py` paths named in thinking messages before the first edit.
  - **(b) key identifiers:** identifier-like tokens (`[A-Za-z_][A-Za-z0-9_.]{2,}`) in the problem statement inside backticks or written CamelCase, which also occur in the gold patch's changed lines. A run "searched" one when a `run_command` argument or a `read_file` path before the first edit contains it (the last dotted part counts).
  - **(c) read before edit:** before the first `edit_file` on file X, a `read_file` of X or a `run_command` whose argument contains X's path or basename.
  - **(d) gold seen:** a gold source file's path appears in a tool observation before the first edit (the model was shown it); and whether thinking ever names it.
  - Reported as counts; no thought text, command or file text is quoted.
- **Tokens:** `metrics.completion_tokens` per model step (there is no thought-token field; `thinking_tokens` is null), so it is an **upper bound** on thought tokens: a step under 4096 completion tokens did not truncate its thinking. Reported: median, p90, max, steps at or over 4096, steps at or over 8000 (near `max_output_tokens` 8192), per run group.

### 2.5 Q5 opportunity counts, defined in advance

- **Ever-resolved set:** task ids resolved by at least one run in any `runs/*/task_results.jsonl` (any model, any tree; the Kaggle subprocess sandbox). A task never resolved by any run is not counted as opportunity for any lever (it may be blocked by the sandbox, for example a collection exit 2 in every run).
- **Per stage s:** opportunity(s) = EXP-038 unresolved task-runs in class s whose task is in the ever-resolved set. This is the upper bound on resolves a lever acting on s could add on dev-48 (one per task).
- **Selection (pipeline):** distinct smoke-8 tasks with a draft-overlap run (Q2). The dev-48 figure obtained by scaling from 8 to 48 is labelled [I].
- The levers per stage are named in section 6 from the evidence, restricted to the tree, prompts, sampling, `eval_config` and the registered tools.
- **Shortfall:** 11 minus the sum of the per-stage opportunity counts, and 11 minus the largest single-lever count, both stated.

### 2.6 Checks run before this commit (format only)

Patch format (38 of 38 non-empty EXP-038 patches begin `diff --git`); gold files (134 `.py` files over 48 tasks, top directories `fastapi/` 67, `rich/` 27, `docs_src/` 26, `src/` 12, `scripts/` 2; no new files); gold hunks per task; usable drafts per pipeline run (`refs.parse_draft`; 0 on 2 tasks of EXP-068-read and 1 of EXP-062-r, where drafts have no `NEW:` block or are near-empty); the step fields (`event_type` `thinking` on 522 EXP-038 steps; the raw channel marker on 12 messages). No classification was computed.

## 3. Blind predictions

- **Q1, EXP-038, 43 unresolved:** E 10 (known from `summary.jsonl`: 10 empties), F about 12, R about 6, C about 10, S about 5. Resolved runs: 5 of 5 in C or S.
- **Q1, pipeline (dispatch sample, about 40 unresolved of 48):** E about 6, F about 6, R about 10, C about 12, S about 6. Localization (F) lower than the single loop; the reader helps, the window misses (R) more.
- **Q2:** among pipeline E, F or R runs, a draft overlaps a gold region in about 30% (about 6 of 20); appliable in about half of those.
- **Q3:** thought text exists (seen in the format check). (a) the edited file is named in thinking at or before the first read of it on about 80% of runs; (b) a key identifier is searched before the first edit on about 70%; (c) read before edit on about 80%; (d) a gold source file shown before the first edit on about 50% of F runs. Steps at or over 4096 completion tokens: under 5%.
- **Q5:** ever-resolved covers about 20 of the 43; the per-stage opportunity sum is about 15, so +11 needs most opportunities converted; the largest single lever is about 5.

## 4. What this does and does not license

It ranks levers for the next rounds and names the stage each targets. It licenses no tree change, kernel, dev-48 run or upload, and no resolve claim: overlap with gold is necessary, not sufficient. Opportunity counts are upper bounds.

## 5. Defects, logged after the fact

(none yet)
