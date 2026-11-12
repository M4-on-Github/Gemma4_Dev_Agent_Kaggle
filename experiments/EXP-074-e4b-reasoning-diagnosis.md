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

Logged 2026-11-11 while computing. Sections 2 to 4 are not changed.

1. **A resolved run entered Q3 on the first pass.** The script's first version picked F and R runs by class without checking `resolved`, so requests_6644 (resolved, class `f`) was in the EXP-038 F list. Fixed before section 6 was written; Q3 is over unresolved runs only (EXP-038 F 12, R 6).
2. **The key-identifier rule (2.4 b) is too narrow to read widely.** It yields at least one identifier on only 5 of the 18 EXP-038 F and R runs (F 1 of 12, R 4 of 6) and on 7 of the 11 pipeline F and R runs. "Searched" is reported, but it covers few runs.
3. **"Named before the first edit" (2.4 a) holds on every run** (18 of 18 EXP-038, 11 of 11 pipeline), since the first naming can come at the edit's own step. The step at which the edited file is first named is the informative part and is reported.
4. **Margin 0 does not merge adjacent changed lines** (regions merge within 2 * M = 0 lines), so at M = 0 a block of changed lines is several regions and S needs every line. This affects the M = 0 sensitivity column only (more C, fewer S).
5. **The opportunity count (2.5) bounds by evidence, not by proof.** A task no run has resolved is not shown to be unresolvable. And every resolve in the ever-resolved set came from a 31B run first: the six 31B dev-48 runs (E0-dev48-baseline, EXP-028-armRH, EXP-028-armR, exp003, exp025 armA and armB) give 11, 3, 1, 0, 1 and 0 new tasks, 16 in all. The union of every E4B run on dev-48 ids is EXP-038's 5. Runs under `EXP-000-*` (gold control) were left out, as were the shim re-grade directories, which have no `task_results.jsonl`.
6. **EXP-038's `summary.jsonl` has `tool_free` and `n_text_form_calls` null** (written before those fields existed). fastapi_13537 is tool-free by its trace: 0 native calls, and 4 thinking-plus-final turns with 3 continuation nudges, ending "Agent completed execution without calling submit_patch".
7. **Not pre-registered, reported as description:** the section 6.1 detail on EXP-038's E runs (`summary.jsonl` fields) and F runs (the top directory of each patched file).

## 6. Results, 2026-11-11

Script `experiments/EXP-074/diag.py` (`python -I -X utf8 experiments/EXP-074/diag.py [--margin 0|5|15] [--all-gold-files] [--brief]`). Its self-test classes each task's gold patch against itself as S on 48 of 48 at margins 0, 5 and 15. Output is not committed: it holds paths only, but is long.

### 6.1 Q1, divergence stage (margin 5, gold source files)

| sample | unresolved task-runs | E | F | R | C | S | resolved runs, classed |
|---|---|---|---|---|---|---|---|
| **EXP-038 dev-48, single loop (distinct tasks = runs)** | **43** | **10** | **12** | **6** | **9** | **6** | 5: S 4, F 1 (requests_6644: a fix outside the gold file) |
| EXP-053-r, single loop, smoke-8 | 6 | 0 | 0 | 1 | 3 | 2 | 2: S 2 |
| Pipeline, dispatch sample (064, 066, 068, 069, 071, 072) | 39 | 7 | 5 | 6 | 9 | 12 | 9: S 9 |
| Pipeline, early (061, 062, 063) | 21 | 5 | 4 | 3 | 4 | 5 | 3: S 3 |

Per run, the dispatch sample is: 064 E1 F1 R1 C1 S2; 066 E1 F1 R1 C1 S2; 068 E1 F0 R1 C2 S3; 069 E0 F2 R1 C1 S2; 071 E2 F1 R1 C2 S1; 072 E2 F0 R1 C2 S2.

**Sensitivity.**
- EXP-038 at margin 15 and with all gold files: E10 F12 R6 C9 S6, unchanged.
- EXP-038 at margin 0: E10 F12 R9 C11 S1 (defect 4).
- The dispatch pipeline is E7 F5 R7 C15 S5 at margin 0, E7 F5 R5 C10 S12 at margin 15, and unchanged with all gold files.
- So the E, F and R counts on dev-48 do not depend on the margin.

**EXP-038 per distinct task:**
- **E:** fastapi_13537, fastapi_13786, fastapi_14360, fastapi_14459, fastapi_14873, fastapi_15661, rich_3063, rich_3676, rich_3935, rich_4075.
- **F:** fastapi_11355, fastapi_13207, fastapi_14448, fastapi_14512, fastapi_14583, fastapi_14962, fastapi_5624, requests_7315, rich_3067, rich_3105, rich_3480, rich_3953.
- **R:** fastapi_14605, fastapi_15030, fastapi_15280, fastapi_15589, rich_3468, rich_3934.
- **C:** fastapi_14262, fastapi_14609, fastapi_14953, fastapi_15800, fastapi_9753, httpx_3672, rich_3061, rich_3180, rich_4070.
- **S:** fastapi_14297, fastapi_14964, requests_7205, requests_7309, requests_7427, rich_3521.

**What the E and F runs did (description, defect 7).**
- **EXP-038 E, 10 runs:**
  - 8 submitted after 3 or more failed `edit_file` calls: 3, 4, 4, 4, 4, 5, 5, 6 and 8 failures, with arg-loss on 2 of the runs (1 and 4).
  - fastapi_13537 is tool-free (defect 6).
  - rich_4075 made 5 calls with no failed edit and submitted without an edit.
  - No cap was hit on any of them. So the dev-48 empties are an edit-application failure, not a budget or search failure.
- **EXP-038 F, 12 unresolved runs:** every patch changes one source file in the same top-level package as the gold file (rich_3105 also changes one other file). The model edits a plausible neighbour, not a test, scratch or docs file.

### 6.2 Q2, the draft discriminator (pipeline)

| sample | runs that miss (E, F, R) | with a draft touching a gold region | also appliable | by class of the miss | runs that hit (C, S) with such a draft |
|---|---|---|---|---|---|
| Dispatch | 18 | **4** (22%) | 4 | E 2 (EXP-071 requests_7205, EXP-072 fastapi_14301), R 2 (EXP-066 and EXP-071 fastapi_14605) | 18 of 21 |
| Early | 12 | **4** | 3 | E 4 (EXP-061 fastapi_14301 and requests_7309, EXP-062 requests_7205, EXP-063 fastapi_14301) | 7 of 9 |

- **Selection proper (an F or R run that held a gold-touching draft):** 2 of 11 dispatch F and R runs, both fastapi_14605, which no run of any model has ever resolved. In the early pipeline, 0 of 7.
- The other 6 overlapping misses are **E runs**: a draft touched gold, and the applier submitted nothing. That is an application failure, not a selection failure.
- Drafts naming a gold source file: 12 of 18 dispatch miss-runs (R 6 of 6, E 6 of 7, F 0 of 5).
- **Margins:** at margin 0, the dispatch count is 4 of 19, 3 appliable; at margin 15, it is 4 of 17, 4 appliable.
- **Drafts counted.** The parser's draft counts are in the per-run listing (199 dispatch drafts, 157 located).
  - The runs with few or no located drafts: EXP-068-read requests_7309 (0 drafts, near-empty finals) and rich_3006; rich_3468 in 064, 068 and 072 (0, 1 and 0 located), where OLD is not found in the file.
  - None of these changes the selection count, since they are S runs or E runs on a task whose drafts never touch gold.
- **Reading:** rarely. Selecting among the drafts (and any verify round used to select) has no resolvable opportunity on smoke-8. The lever upstream is comprehension: what the reader and drafters target. The lever downstream is the applier getting a right draft into the tree.

### 6.3 Q3, reasoning text

- **Thought text is kept.** Every task-run in every sampled run has steps labelled `thinking` with a non-empty message: EXP-038 522 steps on 48 of 48 task-runs, and 94 to 118 per pipeline run on 8 of 8. The raw channel marker leaks into at most 1 message per run. No thought text is quoted here.
- **Tokens against the 4096 budget.** These are completion tokens per model step, an upper bound on thought tokens.

  | sample | steps | median | p90 | max | steps ≥ 4096 |
  |---|---|---|---|---|---|
  | EXP-038 | 534 | 259 | 1419 | 5358 | 6 (1.1%) |
  | pipeline drafters | 347 | 1136 | | | 0 |
  | pipeline readers | 286 | 248 | | | 0 |
  | pipeline appliers | 283 | 358 | | | 0 |

  No step reaches 8000 in any run. **The thinking budget is barely used and almost never binding.** Raising it is not a lever.
- **EXP-038 F runs (12):**
  - The edited file is first named at median model step 1 (by step 1 on 7 of 12); the first edit comes at median step 6.5.
  - The edited file was read before it was edited on 12 of 12.
  - A gold source file appeared in any tool output before the first edit on only **3 of 12**; thinking named a gold file at any point on 5 of 12.
  - The key-identifier rule found identifiers on 1 of 12, and that run searched for them.
  - **Reading:** the model commits early to a plausible file in the right package and reads it with care. On 9 of 12 runs, nothing it ran before editing ever showed it the gold file. The failure is search breadth before commitment, not careless editing or a cut-off chain of thought.
- **EXP-038 R runs (6):**
  - The gold file was shown 6 of 6, named in thinking 6 of 6, and read before the edit 6 of 6.
  - It was named by step 1 on 6 of 6, with the first edit at median step 3.5.
  - Key identifiers exist on 4 runs and were searched on 1.
  - **Reading:** right file, wrong function or block, chosen without a search for the issue's identifiers inside the file.
- **Pipeline F (5) and R (6) runs:**
  - F: gold shown on 3 of 5, edited file read first on 5 of 5.
  - R: gold shown 6 of 6, key identifiers on 6 of 6 and searched on 0 of 6.
  - The same picture as the single loop.

### 6.4 Q4, carrier (8 shared ids)

- **EXP-038 on smoke-8:** resolved fastapi_14301 and rich_3006. Unresolved F 1 (fastapi_14448), R 2 (fastapi_14605, rich_3468), C 1 (httpx_3672), S 2 (requests_7205, requests_7309).
- **EXP-053-r:** R1 C3 S2.
- **Dispatch pipeline (39 unresolved runs over 6 runs):** E7 F5 R6 C9 S12.
- **Per task, the class string over 064, 066, 068, 069, 071, 072** (lower case = resolved):

  | task | classes |
  |---|---|
  | fastapi_14301 | s s s s s E |
  | fastapi_14448 | F E C F C C |
  | fastapi_14605 | R R R C R C |
  | httpx_3672 | C C C R C R |
  | requests_7205 | S S S S E S |
  | requests_7309 | S S S S S S |
  | rich_3006 | s s S s F s |
  | rich_3468 | E F E F E E |

- **Reading:**
  - Both carriers fail the same tasks at the same stages: fastapi_14605 R, httpx_3672 C, the requests pair S.
  - The pipeline adds **E**: 7 of 39 runs against 0 of 12 single-loop unresolved runs on these ids. It loses rich_3468 to the applier's empties (4 of 6 runs) where both single-loop runs reach R. A pipeline E is often a run whose drafts were right (section 6.2).
  - The carrier does not move F, R, C or S on these 8 tasks.

### 6.5 Q5, headroom and the ranked levers

**Ever-resolved:** 16 dev-48 tasks across every agent run (defect 5), so 11 of EXP-038's 43 unresolved tasks have been resolved by some run. By EXP-038 class:

| stage | EXP-038 unresolved | ever resolved (opportunity) | ids |
|---|---|---|---|
| E | 10 | **4** | fastapi_13537, fastapi_14360, fastapi_14873, rich_3676 |
| F | 12 | **3** | fastapi_13207, fastapi_5624, rich_3067 |
| R | 6 | **1** | fastapi_15589 |
| C | 9 | **2** | fastapi_9753, rich_3180 |
| S | 6 | **1** | fastapi_14297 |
| sum | 43 | **11** | |

- At margin 0 the split is E4 F3 R2 C1 S1, and at margin 15 it is E4 F3 R1 C2 S1. The sum is 11 in both.
- **Selection (Q2):** 0 resolvable, both in the smoke-8 sample and carried to 48 [I].

**Shortfall against +11, stated plainly.**
- The sum of every per-stage opportunity is **11, exactly +11: a shortfall of 0 only if every lever converts every task it can reach.**
- 16 of 48 is the union of all six 31B dev-48 runs. It is above the best single 31B dev-48 run (11 of 48, E0-dev48-baseline and exp025 armA).
- Reaching 16 of 48 therefore means the E4B must:
  - solve every dev-48 task any run of ours has ever solved;
  - across five separate stages;
  - while keeping its own 5;
  - and on 11 tasks no E4B run has ever resolved.
- The largest single lever (E) reaches 4, a **shortfall of 7**. The two largest (E and F) reach 7, a shortfall of 4.
- On this evidence the 16 of 48 stopping rule is not reachable by a single-lever loop. The likelier stop is GPU quota.

**Ranked levers** (dev-48 opportunity, then evidence):
1. **Edit application, stage E: 4.**
   - The evidence:
     - 8 of 10 dev-48 empties followed 3 or more failed `edit_file` calls with no cap hit;
     - 1 was tool-free;
     - 6 pipeline E runs held a gold-touching draft the applier failed to apply.
   - Levers, all within what may be modified:
     - the prompt's edit recipe: copy `old_string` from a fresh `read_file` of the exact lines; a smaller unique anchor; when two edits fail on one file, a `write_file` of a small file;
     - a first turn that must be a call (the tool-free ending, also EXP-072's fastapi_14301);
     - in the tree, an applier that applies the first draft whose OLD matches the file exactly.
   - This also guards the 5 already resolved (EXP-072 lost fastapi_14301 this way).
2. **Search breadth before commitment, stage F: 3.**
   - The evidence: on 9 of 12 F runs the gold file never appeared in a tool output before the first edit; the edited file was chosen by step 1 at the median; all 12 edited a neighbour file in the same package.
   - Levers: a prompt step that lists where each symbol named in the issue is defined and used (one search per symbol) before any file is chosen; the reader's FILE chosen from that list.
3. **Multi-site completeness, stage C: 2.**
   - The evidence: 9 dev-48 runs touched some but not all gold regions, and gold is often spread out (31 of 48 tasks have one gold source file, only 17 of 48 have one gold hunk).
   - Lever: a prompt step after the first edit that searches for the other definitions and call sites of the changed symbol. In the tree, drafters assigned to distinct regions, not 5 drafts of one region.
4. **In-file anchoring, stage R: 1.**
   - The evidence: the gold file was shown, named and read on 6 of 6 R runs, and key identifiers were searched on 1 of 6 (0 of 6 in the pipeline).
   - Lever: an identifier search inside the chosen file before choosing the block (EXP-071's printed line numbers are of this kind).
5. **Generation, stage S: 1.**
   - Levers: sampling (temperature, more drafts). The verify forms of D-010 were not exercised or harmed (EXP-072).
6. **Not levers on this evidence:** draft selection and verify-based selection (0 resolvable); the thinking budget (not binding).

**Against the blind predictions (section 3).**
- **EXP-038:** E10 (known), F12 (predicted about 12), R6 (6), C9 (10), S6 (5) were close.
- **Resolved runs:** 1 of 5 classes F where 5 of 5 C or S was predicted.
- **Pipeline:** S 12 against about 6, R 6 against about 10, E 7 against about 6, F 5 against about 6.
- **Q2:** 22% against about 30%; appliable 4 of 4, not about half; but only 2 of the 4 are selection cases.
- **Q3:**
  - read before edit 18 of 18 against about 80%;
  - gold shown on F 3 of 12 against about 50%;
  - key identifiers searched on 2 of 18 against about 70% (defect 2);
  - steps at 4096 or more 1.1%, under the predicted 5%.
- **Q5:** ever-resolved 11 of 43 against about 20; the sum 11 against about 15; the largest lever 4 against about 5.

## Status

ANALYZED 2026-11-11 (section 6), 0 GPU-h. EXP-038 unresolved 43: E10 F12 R6 C9 S6. Draft discriminator: 4 of 18 dispatch miss-runs hold a gold-touching draft (2 E, 2 R on a never-resolved task), so selection has 0 resolvable opportunity. Thought text kept; the budget is not binding; F runs commit early without being shown the gold file (9 of 12). Opportunity E4 F3 C2 R1 S1 = 11, exactly +11 with full conversion; the largest lever (edit application) reaches 4.
