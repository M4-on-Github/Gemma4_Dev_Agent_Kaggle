---
id: 2026-11-17-run-synthesis-model-faults
title: "Where the model's faults are: a synthesis over every local agent run (31B and E4B)"
authors: "internal synthesis"
year: 2026
url: "local: runs/*/summary.jsonl, task_results.jsonl and traces; experiments/EXP-*.md; knowledge/claims.md"
topics: [edit-reliability, budget, prompt, sampling, multi-agent, selection, noise, grading, paper]
relevance: high
read: full
date_added: 2026-11-17
---

Tags: **[V]** counted in this pass from run data, **[D]** taken from an EXP file or claim (id given), **[I]** inference.
Nothing here is a new experiment and nothing ran on GPU. No code, issue text, trace text or repository path is quoted;
the note holds counts, task ids, EXP ids and class names only.

## Takeaway

1. **On the shipped 31B tree the losses sit in what to change, not in how to call the tools.** Of the agent's own
   losses on dev-48 (31 in Arm R, 28 in Arm RH), 61% and 57% are a patch on the right file that changes the wrong
   place or only some of the places; localization is 19% and 29%; an edit that never landed is 10% and 11% [V].
2. **Gold-patch size predicts the outcome better than any process flag.** On the 43 gradable tasks, those whose gold
   patch has 1 region resolve 19 of 26 times over R and RH (re-graded); 2 regions 5 of 18; 3 or more regions 3 of 42.
   The four E4B dev-48 draws resolve 0 of 84 on tasks with 3 or more regions [V]. This is the part to stop spending on.
3. **8 (R) and 10 (RH) of the 48 "losses" per 31B run are not the model's:** 5 tasks no patch can pass on this grader (C-022 [D])
   and 3 (R) or 5 (RH) patches that pass once the two missing test packages are present (C-021 [D], recounted [V]).
4. **A cap is reached on 23 (R) and 25 (RH) of 48 task-runs, with 0 and 3 resolves [V].** 13 tasks hit a cap in all
   six 31B arms, including the arms with 45 and 64 calls, and one of the 13 was ever resolved. So the cap is mostly a
   sign of a task the model cannot do. The reachable part is 6 small-gold tasks that end cap-bound in both R and RH.
5. **Edit-argument loss, loops, malformed calls, overflow and the submit step lose close to nothing on the shipped
   tree.** 44 of R's 58 lost edit calls are on two tasks whose gold patch has 22 and 82 regions; none of R's or RH's
   empty patches had an argument loss; overflow is 0 in all 43 summaries; the harness grades the working tree, so a
   missing `submit_patch` costs nothing [V].
6. **The E4B fails one stage earlier.** Per dev-48 draw it loses 10.0 tasks to a wrong file and 6.2 to edits that
   never applied, against 4.5 and 3.0 for the 31B; every lever tried moved a process count and not resolves
   (EXP-053 to EXP-078 [D]).

## Ranked fault table, 31B (shipped v24 tree at 8 min / 28 calls; EXP-028 Arm R and Arm RH, dev-48, n = 48 each)

Exclusive attribution: each unresolved task-run gets one row, in the order grader-impossible, grading gap, empty
patch, then the EXP-074 stage class of the patch (margin 5, gold source files). "Six-arm mean" adds E0, EXP-003,
EXP-025 A and B (the retired prompt lineage). All counts [V]; levers [D] with the id.

| Rank | Fault (exclusive class) | Lost, R | Lost, RH | Six-arm mean | Fixable with our levers? | Cheapest test |
|---|---|---|---|---|---|---|
| 1 | Partial fix: some gold regions touched, not all (C) | 13 | 11 | 8.8 | Mostly no. 20 of the 24 are on tasks with 3 or more gold regions (median 6 to 7 regions; median share touched 0.33) | none proposed; capacity |
| 2 | Right file, wrong region (R) | 6 | 5 | 3.2 | Weak. 10 of 11 on tasks with 3 or more regions | trace mining only |
| 3 | Grader-impossible (gold fails too) | 5 | 5 | 5.0 | No (not a model fault; C-022) | none |
| 4 | Wrong file (F) | 3 | 6 | 3.8 | Weak. 3 of RH's 6 are small-gold tasks that R did not lose to F, so part is draw noise | none on GPU |
| 5 | Grading gap: patch right once the two test packages exist | 3 | 5 | 1.8 | Yes on dev-48 (vendoring section, EXP-037 built, not pushed); unknown on the hidden grader | a time desk check, then an LB draw |
| 6 | Edit attempted, none landed (empty) | 3 | 3 | 4.3 | Partly. All 6 are at a cap; 4 of the 6 edits were refused by the call budget | EXP-032 arm T4 (built, held) |
| 7 | Never edits (empty, zero edit or write calls) | 3 | 2 | 9.7 | Already cut from 8 to 17 per run by the v24 prompt and the 8-minute cap | same arm as row 6 |
| 8 | All gold regions touched, change wrong (S) | 3 | 1 | 1.5 | No lever found | none |
| | resolved | 9 | 10 | 9.8 | | |

Overlays (not exclusive; a task-run can carry several):

| Overlay | Affected / lost, R | Affected / lost, RH | Reading |
|---|---|---|---|
| Any cap reached (calls, time, session timeout) | 23 / 23 | 25 / 22 | the largest overlay; mostly a symptom (section 1.6) |
| No check after the last change (non-empty patches) | 24 / 23 | 15 / 14 | 16 of R's 23 are capped; unstable between two near-identical arms |
| Check after the last change exits 0, task lost | 8 | 13 | the check passes and the patch is wrong; not a missing-verify fault |
| Edit-argument loss on at least one call | 7 / 6 | 4 / 4 | 0 empties among them; concentrated on very large gold patches |
| Identical repeats of 5 or more | 6 / 6 | 5 / 5 | 4 and 3 of these are a repeated `submit_patch`, not a search loop |
| Two or more context compactions | 12 / 12 | 13 / 13 | 8 and 12 are also capped |
| Malformed turn | 1 / 0 | 2 / 2 | negligible |
| Context overflow (HTTP 400) | 0 | 0 | absent in every run |

## 1. Fault taxonomy

### 1.0 Sources and definitions

**Runs read [V].** 43 `summary.jsonl` files, 36 distinct runs (the six under `runs/EXP-034/` duplicate the six 31B
dev-48 arms; `runs/EXP-075-base038` is EXP-038 re-analysed with the text-form counter).
- 31B, dev-48 (48 ids, the cohort file): E0 (`runs/E0-dev48-baseline`), X003 (`runs/exp003_public_budget_dev48`), A25
  and B25 (`runs/exp025_armA`, `runs/exp025_armB`), R and RH (`runs/EXP-028-armR`, `runs/EXP-028-armRH`). Configs as in
  EXP-034 section 2.1 [D]: E0 4.5 min / 45 calls; X003 8 min / 28 calls; A25 and B25 4.5 min / 64 calls; R and RH the
  shipped v24 tree at 8 min / 28 calls.
- 31B, other: EXP-032-p1 (8 cap-bound ids), EXP-002 (4 tasks).
- E4B, dev-48: EXP-038 and EXP-077 (temperature 1.0), EXP-075-t02 and EXP-078-t02r (temperature 0.2).
- E4B, 8-task runs: 24 runs, EXP-033 to EXP-073 (EXP-044 X and X0 use the failed-edit-8 ids, the rest smoke-8).

**Operational definitions.** Summary fields are those written by `tools/analyze_traces.py`.

| Fault | Definition (recountable) |
|---|---|
| Never edits | `patch_empty` and zero `edit_file` or `write_file` calls in the trace |
| Edit attempted, none landed | `patch_empty` and at least one such call |
| Wrong file (F), wrong region (R), partial (C), all regions wrong (S) | `diag.classify` of EXP-074 section 2.3 on `task_results.jsonl` `patch` against the gold `patch`, margin 5 |
| Edit-argument loss | `n_edit_arg_loss` > 0 (the harness reply that a mandatory parameter is absent) |
| Edit failure of any kind | `n_edit_fail` > 0 |
| Malformed call | `n_malformed` > 0 |
| Loop | `n_identical_repeats` >= 5 (a call equal to one of the previous three; free calls are counted, so it can exceed `n_calls`) |
| Cap | `calls_cap_hit`, or `time_cap_hit` or `timeout_hit` |
| Edit refused by the call budget | an `edit_file` or `write_file` call whose observation is the harness budget refusal |
| Context overflow | `overflow_400`; `compactions` >= 2 as a softer signal |
| No check after the last change | no `run_command` that starts python or pytest after the last call that changed a file in the final patch |
| Text-form call | `n_text_form_calls` > 0; tool-free when `tool_free` |
| Fallback patch | `submit_patch_called` false and the patch non-empty |
| Grader-impossible | the five ids where the gold patch fails (C-022) |
| Grading gap | `R_resolved_regraded` or `RH_resolved_regraded` true and as-run false (`experiments/EXP-036/summary.jsonl`); for X003 the EXP-004 re-grade |

First check of the instrument: R reads E6 F3 R6 C14 S10 with 9 resolved, the figure in EXP-080 section 6.1 [V, D].

### 1.1 Never edits

- **31B.** R 3 of 48, RH 2, all lost, all at a cap [V]. The retired lineage: E0 13, X003 8, A25 17, B25 17, all at a
  cap [V].
  - Consistency: high inside the retired lineage. The 15 tasks that were empty in at least 3 of its 4 arms were not
    converted by the shipped tree: in R they read C 4, R 4, E 5, S 1, F 1 and resolve 0; in RH one resolves [V].
  - Lever tried: an edit-by-call rule (EXP-010, LB 6/58, uninformative; C-011 [D]); the v24 prompt and the 8-minute
    cap (EXP-027, EXP-028), which cut the count from 8 to 17 down to 2 to 3 without adding resolves on those tasks.
  - Untried: a higher call cap on the shipped tree (C-007; EXP-032 arm T4 is built and held [D]).
- **E4B.** 1, 1, 0, 0 over the four dev-48 draws [V]. Not an E4B fault. The one case in EXP-038 is the tool-free
  task (1.9).

### 1.2 Wrong file

- **31B.** Lost: R 3, RH 6; E0 1, X003 3, A25 4, B25 6 [V]. One F patch resolves in every arm (requests_6644, the
  free task of C-022).
  - Consistency: low to medium. Tasks in F in 0 / 1 / 2 of R and RH: 41 / 3 / 4. fastapi_14583 is F in 5 of the six arms and
    fastapi_14512 in 3 [V].
  - Lever tried: graph tools dropped (C-012); three parallel read-only localizers (EXP-032 P1: 0 of 8 resolved,
    7 of 8 empty because the shared call budget was spent before the editor ran [D, V]).
  - Untried: nothing cheap. Outside evidence is that pointing at the right file does not fix the fix
    (`2026-11-17-paper-track-writeups` row 5 [D]).
- **E4B.** Lost 11, 8, 12, 9 (the largest single class, mean 10.0) [V]. Tasks in F in 3 or 4 of the 4 draws: 10.
  - Lever tried: location-diverse drafters (EXP-064, not exercised), a search-command recipe (EXP-066, no decision),
    numbered-line anchors (EXP-071, harm) [D]. EXP-074: on 9 of 12 F runs nothing the model ran showed it the gold
    file before it edited [D].
  - Untried: a one-search-per-symbol opener was desk-checked only (EXP-076, EXP-079 [D]).

### 1.3 Right file, wrong fix (R, C and S together)

- **31B.** R + C + S unresolved is 30 in R and 27 in RH [V], the figure of EXP-034 section 9.2 [D]. Remove the 5
  impossible tasks and the grading-gap flips and 22 (R) and 17 (RH) remain: C 13 and 11, R 6 and 5, S 3 and 1 [V].
  - C splits into "a whole gold source file never touched" 8 and 6, and "all gold files touched, a region missed" 5
    and 5 [V].
  - Consistency: this is the most stable class. Of the 37 tasks unresolved in both R and RH, 26 keep the same class;
    11 tasks are C in both; 9 tasks keep one class over all six arms [V].
  - Lever tried: none on the 31B that targets completeness. The verify idea is 1.8.
  - Untried: a prompt step that lists the other definitions and call sites after the first edit (named for the E4B
    in EXP-074 section 6.5, never screened on either model [D]).
- **E4B.** R 6, 8, 7, 12; C 8, 12, 9, 9; S 3, 3, 4, 5 after the 5 impossible tasks are removed [V]. Together 17,
  23, 20 and 26 of the 37 to 40 agent losses per draw.
  - EXP-080: where an E4B run reaches a gold file and fails, it states the gold's cause in 8 of 24 coded runs,
    against 10 of 10 for Arm R; no lever for that is in a shipped file [D].

### 1.4 Edit-argument loss and malformed calls

- **31B, call level.** Lost `edit_file` calls: E0 92 of 172, X003 25 of 137, A25 49 of 114, B25 35 of 81, R 58 of 175,
  RH 10 of 109 [V]. R's 58 of 175 (33.1%) is the critic's count in C-004 [D].
- **31B, task level.** Tasks with a loss / unresolved among them: R 7 / 6, RH 4 / 4, E0 14 / 11, X003 4 / 3,
  A25 6 / 4, B25 9 / 7 [V].
  - In R, 44 of the 58 lost calls are on two tasks (fastapi_14262, fastapi_14609) whose gold patches have 22 and 82
    regions; a third and fourth (fastapi_14605, rich_4070) have 20 and 32 [V].
  - None of R's 6 or RH's 5 empty patches had an argument loss. R's 6 affected losses all end with a patch on disk
    (C 4, F 1, R 1) [V].
  - Consistency: low. Tasks with a loss in 0 / 1 / 2 of R and RH: 39 / 7 / 2; in 3 or more of the six arms: 4 [V].
  - Lever tried: the recovery ladder (EXP-025: wasted retries -40%, not significant; C-006), the shell route (EXP-028
    Arm RH: next call after a first loss is `run_command` in 0 of 6; C-005 refuted), thinking budget (C-010: 53.5% of
    edit calls lost at 256 against 18.2% at 4096, recounted here as 92 of 172 and 25 of 137 [V]).
  - Untried: a thinking budget near 1024 (outside idea, `2026-11-17-paper-track-writeups` row 1).
- **31B, malformed turns.** 1, 2, 2, 4, 1, 2 tasks per arm; 9 of the 12 unresolved [V]. Too few to rank.
- **E4B.** Argument loss is rare: 9 of 156, 13 of 139, 1 of 150, 4 of 129 `edit_file` calls [V]. The E4B's edit
  failures are content failures: 82, 78, 67 and 49 failed calls per draw, on 25, 22, 19 and 18 tasks, 15, 14, 11
  and 9 of them with 3 or more failures [V]. EXP-043: of 39 failed calls on 8 tasks, 22 not found, 11 non-unique,
  5 lost arguments [D].
  - Empty patches after failed edits: 9, 8, 5, 3 [V].
  - Lever tried: exact-copy line (EXP-044, killed by its control), retry rule (EXP-053, dropped), copy LoRA
    (EXP-054, EXP-058; out of bounds now), drafter-own-read (EXP-068), bare-path recipe (EXP-069), temperature 0.2
    (EXP-075, EXP-078: empties 10 and 9 down to 5 and 3; resolves 5 and 3 against 6 and 5, not readable) [D].

### 1.5 Identical repeats and loops

- **31B.** Tasks with 5 or more identical repeats: R 6, RH 5, E0 10, X003 2, A25 5, B25 4; resolved among them
  0, 0, 3, 1, 2, 0 [V].
  - In R, 4 of the 6 are a repeated `submit_patch` (34, 50, 51 and 63 calls on fastapi_14609, rich_4075,
    fastapi_14873, fastapi_14360); in RH, 3 of 5 (20, 23, 51). The harness answers each with an ok status and the run
    goes on to the 80-turn budget (R has 4 turn-budget endings, EXP-028 section 9.1 [D]) [V].
  - Tasks with 3 or more `submit_patch` calls: R 4, RH 4, X003 1, E0 1; 0 resolved; mean 53 to 58 s spent after the
    first submit; total 466 s (R) and 468 s (RH) over 48 tasks [V].
  - The other 2 in R are the argument-loss retries of 1.4.
  - Lever tried: none for the submit repeat. I found no earlier note that names it.
  - Untried: one prompt line (stop after the first ok from `submit_patch`). It buys time, about 9.7 s per task on
    average, not resolves [I].
- **E4B.** 0, 0, 0, 1 tasks [V]. Resends of a failed `old_string` are not counted by this field (EXP-053 [D]).

### 1.6 Call cap or time cap reached

- **31B.** Any cap: R 23 (0 resolved), RH 25 (3), X003 30 (1), E0 38 (4), A25 46 (10), B25 39 (6). Calls cap alone:
  R 18 (0), RH 17 (2), X003 21 (1) [V]. EXP-028 has 18 and 17 [D].
  - What the capped runs hold in R: C 9, E 6, F 3, R 2, S 3. 16 of the 17 capped non-empty losses have no check
    after the last change [V].
  - Capped runs are not mainly loop or retry victims: of R's 23, 5 have 5 or more repeats, 3 have 3 or more lost
    edits, 3 have 8 or more whole-file reads, and 16 have none of the three [V].
  - Consistency: high and task-bound. Tasks capped in 0 / 1 / 2 of R and RH: 18 / 12 / 18. 13 tasks are capped in
    all six arms; one of the 13 (rich_3180) was ever resolved [V].
  - Of the 18 capped in both R and RH, 3 were resolved by at least one of the six 31B arms (fastapi_14873,
    rich_3180, rich_3676) [V].
  - Lever tried: the time cap 4.5 to 8 min (C-002; the LB read 7 at 4.5 min and 10, 11, 7, 8 over four draws at 8 min,
    `submissions.md` rows 8, 11, 12, 13, 17 [D]). The call cap itself: never as one variable (C-007 untested; EXP-032
    T4 built, not pushed [D]).
  - No arm on disk pairs a long clock with many calls: 4.5 min with 45 or 64 calls, or 8 min with 28 [D, EXP-034].
- **E4B.** 0, 0, 0, 2 of 48 [V]. Not a constraint (C-020 [D]).

### 1.7 Context overflow

- `overflow_400` is false on every row of all 43 summaries [V].
- Compactions: R 49 in total on 36 tasks, RH 49 on 35; two or more on 12 and 13 tasks, 0 resolved; 8 and 12 of those
  are also capped [V]. The older four arms record 0, which may be the analyzer version of the time [I].
- E4B: two or more compactions on 2, 1, 1, 3 tasks [V]. One pipeline run crashed on a compaction (EXP-052 [D]).
- No lever tried and none proposed.

### 1.8 No test after the last edit

- **31B.** Non-empty patches with no python or pytest command after the last change, affected / lost: R 24 / 23,
  RH 15 / 14, X003 12 / 11, E0 6 / 5, A25 12 / 11, B25 8 / 5 [V]. EXP-034 counts 21 of R's 30 right-file-wrong-fix
  tasks with a stricter rule that does not count `python -c` [D]; mine gives 20 of the same 30 [V].
  - Resolved runs check and pass: R 8 of 9 end on a check that exits 0, RH 8 of 10 [V].
  - Split by cap in R: capped non-empty losses 17, no check 16; uncapped non-empty losses 16, no check 7, check
    exits 0 on 8, non-zero on 1. Restricted to the agent's own wrong patches (25): no check 19, of which 3 are
    uncapped [V].
  - RH: its own wrong patches 23, no check 9 (4 uncapped), check exits 0 on 10 [V].
  - Consistency: low. Tasks with the flag in 0 / 1 / 2 of R and RH: 20 / 17 / 11 [V].
  - Lever tried on the 31B: none run. EXP-036: an existing visible test would have exposed the wrong fix on 2 to 7
    of 22 tasks [D].
- **E4B.** No check: 23, 22, 14, 21 non-empty patches per draw; a check that exits non-zero and the task lost: 12,
  14, 22, 19; a check that exits 0: 0, 0, 1, 1 [V]. EXP-080 and EXP-081: 106 of 109 pytest checks exit non-zero,
  0.632 of them for reasons unrelated to the change, and the next action is a submit on 80 of 107 [D].
  - Lever tried: repro bullet (EXP-045), last-check rule (EXP-055: obeyed on 7 of 7, 3 of 7 ran no tests), check
    picker skill (EXP-056, EXP-057: dropped), runnable verify in the applier (EXP-072: harm), reproducer stage
    (EXP-063, EXP-073: harm), `python -c` form (EXP-081: not built) [D].

### 1.9 Text-form tool calls (E4B)

- Dev-48 single loop: 3 tasks with a text-form call and 1 tool-free (fastapi_13537) in EXP-038; 0 in the other three
  draws [V]. So 1 of 192 task-draws is lost to it.
- By tree (EXP-065 [D]): tool-free endings 2 of 80 in the flat trees, 6 of 32 in the skill trees, 0 of 24 in the
  early pipelines; EXP-071 then has 2 of 8 tasks with a text-form call in a pipeline (recounted here from its
  summary [V]).
- Not seen on the 31B: the field is absent from the 31B summaries and nudges are 2 and 0 in R and RH [V].
- Lever: keep the tree small. A longer first prompt and more tool declarations go with the fault (EXP-065 [D, I]).

### 1.10 Submitted versus fallback patch

- **The harness grades the working tree.** Runs with no `submit_patch` call and a non-empty patch resolve: A25 9 of
  26, B25 6 of 18, E0 4 of 16, X003 1 of 4, RH 1 of 7, R 0 of 3 [V]. 9 of A25's 11 resolves never called submit.
- So a missing submit loses nothing by itself, and a "submit by call N" rule has no direct payoff. This answers the
  open desk check in `2026-11-17-paper-track-writeups` row 3.
- Submit with an empty patch: R 3, RH 4, X003 9; E4B 9, 9, 5, 2 [V]. These are 1.1 and 1.4 seen at the end.

### 1.11 What else the data shows

- **Gold-patch size.** Gradable tasks by gold regions (margin 5): 1 region 13 tasks, 2 regions 9, 3 to 4 regions 9,
  5 or more 12. Resolves over R and RH re-graded: 19 of 26, 5 of 18, 1 of 18, 2 of 24. Six 31B arms as run: 46 of
  78, 11 of 54, 1 of 54, 1 of 72. Four E4B draws: 14 of 52, 5 of 36, 0 of 36, 0 of 48 [V].
- **Grading.** 5 impossible tasks in every run. Grading gap: R 3, RH 5, X003 3 (EXP-004), E0 0; E4B 0 (EXP-038
  re-grade) [V, D].
- **A passing check on a wrong patch.** R 8, RH 13 task-runs end on a check that exits 0 and are lost [V].
- **Long turns.** A turn above 1,500 completion tokens occurs on 7 of 19 resolved and 47 of 77 unresolved task-runs
  over R and RH [V]. Same direction as the outside finding (`2026-11-17-paper-track-writeups` row 2), and confounded
  with task size in the same way [I].
- **First edit.** Median call index of the first edit attempt: R resolved 6, unresolved with a patch 12, empty 29;
  RH 7, 14.5. A first edit after call 14 resolves 1 of 15 in R and 1 of 18 in RH [V]. Consistent with C-011.

## 2. Per-task view on dev-48, 31B arms

### 2.1 The split

Six arms, same 48 ids [V].

| Grading | Always (6 of 6) | Sometimes | Never |
|---|---|---|---|
| As run | 6 | 10 | 32 |
| With the re-grades of X003, R and RH | 7 | 11 | 30 |

EXP-034 reports 6 / 11 / 31 with only X003 re-graded [D]; the as-run recount is 6 / 10 / 32 [V].

- **Always:** fastapi_14301, fastapi_14463, requests_6644, rich_3006, rich_3067, rich_3905. Five have a one-region
  gold patch; requests_6644 passes with no patch (C-022).
- **Sometimes (as run), with the arms that resolve it:** fastapi_13537 (5), fastapi_15589 (4), fastapi_14297 (3),
  fastapi_5624 (3), fastapi_9753 (3), fastapi_13207 (1), fastapi_14360 (1), fastapi_14873 (1), rich_3180 (1),
  rich_3676 (1).
  - Three of them (fastapi_13207, fastapi_14297, fastapi_14360) resolve in both R and RH once re-graded. Their
    "sometimes" is the grading gap, not a model flip.
  - Their failures are budget-shaped: of 37 failing task-runs, 29 are at a cap and 15 are empty patches [V].
- **Never, 32:**
  - 5 grader-impossible (httpx_3672, requests_7205, requests_7309, requests_7315, requests_7427);
  - 2 that a re-grade resolves at least once (fastapi_14459, fastapi_14605);
  - 25 structural.

### 2.2 The never-solved set

Dominant class of the 25 structural tasks [V]:

| View | E | F | R | C | S |
|---|---|---|---|---|---|
| Modal class over the six arms (ties to the earlier stage) | 16 | 2 | 1 | 5 | 1 |
| Class in R and RH (50 task-runs) | 8 | 8 | 10 | 20 | 4 |

- Over all six arms the modal fault is an empty patch at a cap, because four of the six arms are the retired
  lineage. On the shipped tree the same tasks mostly reach a gold file and stop at a partial or misplaced change.
- 19 of the 27 non-impossible never-solved tasks have 3 or more gold regions; 13 touch more than one gold source
  file. The 8 with a small gold patch are fastapi_14964, fastapi_15280, fastapi_15661, rich_3063, rich_3105,
  rich_3480, rich_3521, rich_3953 [V].
- No E4B draw resolves any of the 32 [V].

### 2.3 Noise against structure

- **Structural:** 6 always, plus 25 never, plus 5 impossible: 36 of 48 tasks do not move between arms.
- **Flips:** the 10 sometimes-tasks. R and RH share 8 resolves and differ on 3 (fastapi_9753 for R; fastapi_5624
  and rich_3180 for RH). E0 against A25: 8 shared, 3 and 3. E0 against X003: 6 shared, 5 and 3 [V]. This matches
  C-016 [D].
- **Stage class is less stable than the outcome.** R and RH agree on the class of 34 of 48 tasks; the two E4B
  temperature-1.0 draws agree on 26, the two 0.2 draws on 33 [V] (EXP-077 has 27 [D]).
- **Board.** Four draws of the shipped zip read 10, 11, 7 and 8 of 58 (`submissions.md` rows 11, 12, 13, 17 [D]). A
  dev-48 difference of 3 tasks between arms is inside what two draws of one arm give.

## 3. Where in the episode the faults occur

Exclusive stage of each agent-attributable loss (impossible tasks and grading-gap flips removed) [V]. Localize =
never edits or wrong file. Understand = right file, wrong region or partial. Apply = an edit was attempted and
nothing landed. Content = every gold region touched, change wrong.

| Run | Losses | Localize | Understand | Apply | Content |
|---|---|---|---|---|---|
| 31B R | 31 | 6 (19%) | 19 (61%) | 3 (10%) | 3 (10%) |
| 31B RH | 28 | 8 (29%) | 16 (57%) | 3 (11%) | 1 (4%) |
| 31B E0 | 32 | 14 (44%) | 10 (31%) | 6 (19%) | 2 (6%) |
| 31B X003 | 31 | 11 (35%) | 11 (35%) | 8 (26%) | 1 (3%) |
| 31B A25 | 32 | 20 (62%) | 9 (28%) | 2 (6%) | 1 (3%) |
| 31B B25 | 34 | 22 (65%) | 7 (21%) | 4 (12%) | 1 (3%) |
| E4B EXP-038 | 38 | 12 (32%) | 14 (37%) | 9 (24%) | 3 (8%) |
| E4B EXP-077 | 40 | 9 (22%) | 20 (50%) | 8 (20%) | 3 (8%) |
| E4B EXP-075 | 37 | 12 (32%) | 16 (43%) | 5 (14%) | 4 (11%) |
| E4B EXP-078 | 38 | 9 (24%) | 21 (55%) | 3 (8%) | 5 (13%) |

- **Verify** is not an exclusive stage: a wrong patch was already wrong before the check. As an overlay on the
  wrong-patch losses: R 25, of which no check 19 (16 of them capped) and a passing check 5; RH 23, no check 9, a
  passing check 10 [V].
- **Submit:** 0 losses on either model. The working tree is graded (1.10).
- The 31B's "apply" losses are budget events (4 of 6 edits refused by the call budget, all 6 at a cap). The E4B's
  are content mismatches of `old_string` with no cap reached [V].
- The retired prompt lost at localize because it ran out of clock before editing. The shipped tree moved those
  tasks to understand without resolving them (1.1).

## 4. Ranking and what to do with it

### 4.1 31B, by tasks lost per run (mean of R and RH, of 48)

1. Partial multi-site fix: 12.0.
2. Right file, wrong region: 5.5.
3. Empty at a cap (never edits 2.5, edit refused or failed 3.0): 5.5.
4. Grader-impossible: 5.0 (not the model).
5. Wrong file: 4.5.
6. Grading gap: 4.0 (not the model's fix).
7. All regions touched, wrong change: 2.0.

By gold size the same losses read: 19.5 per run on the 21 gradable tasks with 3 or more gold regions (39 of 42
task-runs lost), and 10 per run on the 22 with 1 or 2 regions, 6 to 7 of those at a cap [V].

### 4.2 Fixable with our levers

| Fault | Lever | Pool on dev-48 | Cheapest test |
|---|---|---|---|
| Cap-bound small-gold tasks (fastapi_14873, fastapi_15280, rich_3063, rich_3105, rich_3480, rich_3521: lost in both R and RH, at a cap in both) | `max_tool_calls` 28 to about 40 in `eval_config.yaml` | at most 6 [V]; 1 of the 6 was ever resolved by any arm | First, trace mining at 0 GPU: on these 12 task-runs, whether the refused or last edit touched a gold region. Then the EXP-032 T4 arm that is already built (about 0.9 GPU-h). |
| Repeated `submit_patch` after an ok | one prompt line | 0 resolves; about 0.3 h of the 12 h budget per 120 tasks [I] | a desk check of why the session continues, then it rides on the T4 screen as a process count |
| Grading gap | the vendoring section (EXP-037, built) | 3 to 5 on dev-48 [D]; unknown on the hidden grader | no local test can answer the hidden-grader question; the desk check is time (about 24 s per task against 13.8 s of headroom, EXP-037 critic [D]) |
| Sampling on the shipped tree | `thinking_budget` near 1024; temperature | unknown; no single-variable 31B contrast on disk | trace mining of turn length against outcome is done here (1.11, weak); a smoke-8 would read the lost-call rate, not resolves |

A higher call cap lengthens capped runs. R projects 10.04 h with no margin (EXP-028 [D]); if R's 18 call-capped
runs ran on to the clock, the mean wall would rise by about 48 s and the projection by about 1.6 h [I]. T4 cannot
ship at 8 minutes without taking time back elsewhere.

### 4.3 Stop spending (model capacity or no signal)

- **Multi-site completeness on large gold patches.** 3 of 42 on the 31B and 0 of 84 on the E4B. No prompt, cap or
  sampling arm on disk has moved one of these tasks.
- **Edit-argument loss as a score lever.** It is real at the call level and worth the paper (C-004), and it costs
  about zero tasks on the shipped tree (1.4).
- **A verify-before-submit rule.** The uncapped no-check pool is 3 (R) and 4 (RH); 5 to 10 wrong patches per run
  pass their own check; the failing hidden tests are mostly ones the agent cannot see (EXP-036 [D]); every E4B form
  was dropped or harmed.
- **Localization aids and extra stages.** EXP-032 P1 on the 31B and D-008 to D-010 on the E4B each added a failure
  class and no resolve.
- **Best-of-N without a selector.** The union of R and RH adds 1 task over the better arm (EXP-034 [D]); the flips
  are 3 tasks.
- **On the E4B, everything but tree size.** Wrong file and wrong region are comprehension (EXP-074, EXP-080);
  fewer empties did not become more resolves (EXP-075, EXP-078).

### 4.4 E4B, by tasks lost per dev-48 draw (mean of four, of 48)

1. Wrong file: 10.0 (11, 8, 12, 9).
2. Partial fix: 9.5 (8, 12, 9, 9).
3. Right file, wrong region: 8.2 (6, 8, 7, 12).
4. Edits attempted, none applied: 6.2 (9, 8, 5, 3).
5. Grader-impossible: 5.0.
6. All regions touched, wrong change: 3.8 (3, 3, 4, 5).

Resolved 5, 3, 6, 5. Always resolved in the four draws: fastapi_14301, fastapi_14463, requests_6644; sometimes:
rich_3905 (3), rich_3006 (2), rich_3067 (1), fastapi_14873 (1); never: 41 [V].

8-task E4B runs, pooled by tree [V]: single loop 56 task-runs, 9 resolved, 6 empty; skill trees 32, 6 resolved,
6 empty; pipelines 104, 17 resolved, 18 empty. Three of the eight smoke ids are grader-impossible, so these pools
say little about the fix stage (EXP-074 section 7 [D]).

## 5. Disagreements with claims and earlier taxonomies

1. **C-019 (no test after the last edit is the change with the most room).** The count holds (21 of 30 [D], 20 of
   30 by my rule [V]). The reading does not: 16 of R's 23 no-check losses are capped runs, the uncapped pool of the
   agent's own wrong patches is 3 (R) and 4 (RH), and RH has 9 no-check against R's 19 on nearly the same tree. Where
   the agent had budget it checked, the check passed, and the patch was wrong (8 and 13 task-runs). C-018's 2026-11-05
   note already says 8 of R's 11 non-checkers hit a cap [D]; C-019's title was not revised.
2. **C-004 (a large share of edit calls never reach the file).** Agrees at the call level (58 of 175 [V] = the
   critic's 33.1%). At the task level it is 7 tasks in R and 4 in RH, 44 of 58 calls on two tasks with 22 and 82 gold
   regions, and no empty patch. The claim says nothing false; the briefing's weight on it as a score lever is not
   supported on the shipped tree.
3. **C-007 (the 28-call cap binds with no resolves among the capped).** Agrees for R (18, 0 resolved [V]). RH has
   17 with 2 resolved [V, D]. Added bound: 13 tasks are capped in every arm, including the 45- and 64-call arms,
   and 1 of the 13 was ever resolved, so the premise ("the cap binds") overstates the gain; the pool with a small
   gold patch is 6.
4. **EXP-053 class C, 12 of 24.** 7 of those 12 class-C runs are on requests_7205 and requests_7309, which no patch
   can pass [D, from its own table and C-022]. On dev-48 the share of right-file losses is still the largest for
   the E4B (17 to 26 of 37 to 40 per draw [V]), but the smoke-8 figure was a cohort artefact, as EXP-074 section 7
   found for class S.
5. **EXP-028 section 9.1, "compactions 0 / 0".** The summaries on disk give 49 compaction events in each of R and
   RH, on 36 and 35 tasks [V]. The table predates a counter change or is wrong; `aggregates.json` in the run dir
   says 49.
6. **EXP-034 section 9.1, always / some / none 6 / 11 / 31.** As run it is 6 / 10 / 32; with all three re-grades
   7 / 11 / 30 [V]. EXP-034 mixes one re-graded arm with five as-run arms and says so.
7. **`2026-11-17-paper-track-writeups` row 3** leaves open whether the harness grades the working tree. It does
   (1.10 [V]).
8. **Agreements worth recording.** C-010 (92 of 172 against 25 of 137 lost edit calls [V]); C-011 (first edit
   after call 14 resolves 2 of 33 over R and RH [V]); C-016 (R and RH share 8 of 11 distinct resolves [V]); C-020
   (E4B caps 0, 0, 0, 2 [V]); C-022 (the five ids are unresolved in all ten dev-48 runs read here [V]); the 16
   ever-resolved tasks of EXP-074 (recounted 16, all of them resolved by one of the six 31B arms [V]).

## 6. Limits

- One draw per 31B config. R and RH differ by one prompt section, so they are the nearest thing to two draws of the
  shipped tree and are not that.
- The stage classes compare the patch with the gold patch. Gold is not the only fix (one resolved patch per arm
  touches no gold file), and "regions" is a proxy for task size.
- The check detector matches commands that start python or pytest. RH's shell route writes files through python
  heredocs, which the detector may count as a check when the command does not name a patched file [I].
- The grading-gap flag exists only for R, RH, X003, E0 and EXP-038. A25 and B25 vendor the packages themselves.
- Runs not read are listed in the handback, not here.
