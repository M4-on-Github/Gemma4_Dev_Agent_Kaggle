# EXP-076 — Identifier search before commitment on the E4B single loop: desk check; the dispatched arm is NOT BUILT (D-011 lever 2)

**Date:** 2026-11-12
**Type:** zero-GPU analysis (desk check for a dispatched dev-48 arm). The arm itself is not built: section 4 shows that the dispatched form cannot be read on dev-48. 0 GPU-h.
**Cohort:** none
**Ladder:** L1 (trace mining over EXP-038 and the same-tree reruns on disk). The L4 arm the lead dispatched is not bought; section 5 names a different form for the lead to judge.
**Not pre-registered:** the counts were made before any rule was written; nothing here is a reading of a run.
**Serves:** D-011 (diagnosis first), lever 2 of EXP-074 section 6 (search breadth before commitment, opportunity F3). Base: `experiments/EXP-033/candidate-e4b`, the tree that ran as EXP-038.
**Relates:** EXP-038, EXP-074 (classes, the key-identifier rule and its defect 2, gold shown 3 of 12 by path and 5 of 12 by basename), EXP-068 and EXP-073 (the hard first-call opener, 36 of 40 drafter turns), EXP-071 (a multi-flag recipe taken up on about a quarter of tasks), EXP-075 (the noise reference, `experiments/EXP-075/noise.py`).

## 1. The dispatch
The lead asked for one arm: a hard first-call opener ("the first reply must be a search call for an identifier or error string quoted from the issue, before any file is opened"), in the simplest call shape the E4B emits natively, with endpoints "the opener held on N of 48", "the gold file appeared in tool output before the first edit", and "F tasks leaving F". The dispatch allows the exit taken here: "If your desk check shows a lever has no buildable form, say so instead of building it."

## 2. Definitions and scripts
- `experiments/EXP-076/desk.py [run]`: per task, the first native call; **opener** = the first call is a search (`run_command` whose program is `grep`, `egrep`, `rg`, or `git grep`) whose pattern (first non-option word, quotes removed) is at least 4 characters long and occurs in the problem statement; searches before the first `edit_file` / `write_file`; **shown** = a gold source file's path or basename appears in a tool observation before the first edit (EXP-074 section 7 point 2).
- `experiments/EXP-076/trunc.py [run]`: per **qualifying search** (an issue-pattern search before the first edit whose pattern is a literal substring of a gold source file at the base commit): whether its output names a gold file, and if not, the cause (first that applies): `scoped_gold` (searched inside the gold file itself, so grep prints no file name), `scoped_other` (search paths that neither are nor hold a gold file), `head` (a pipe into `head`; a bare `head` keeps 10 lines), `cap` (stdout at least 5000 characters: the harness `max_stdout_chars` 5000, sliced with no marker, `swegemma/budget.py`), `other`. Also **files_with** (snapshot `.py` files holding the pattern, a specificity measure) and **list_ok** (simulation: the path-sorted list of files holding the pattern, one per line, the output shape of `git grep -l PATTERN -- '*.py'`, names a gold file within its first 5000 characters).
- `experiments/EXP-076/rerun.py`: flips of `opener` and `shown` on ids shared with EXP-038, for the same-tree reruns (EXP-033-e4b, EXP-044-X0) and three one-bullet variants (EXP-044-X, EXP-045-p, EXP-053-r).
- Classes: EXP-074 `diag.classify` at margin 5. "Unresolved F" is the EXP-074 count of 12; `desk.py` prints 13 F because it counts the resolved `requests_6644` (class `f`) in its class.

## 3. Counts (EXP-038 dev-48 unless named)

### 3.1 The opener is already the base's habit
- First calls over 48: `git grep` 24, `grep` 11, `read_file` 8, `ls` 3, `cat` 1, none 1 (the tool-free `fastapi_13537`). The base prompt's section 2 already prescribes an issue-token `git grep` first.
- **Opener held on 30 of 48** in EXP-038. On the 12 unresolved F tasks it held on 9; the 3 without it are `fastapi_14962` (first call `read_file`), `rich_3067` and `rich_3953` (a `git grep` whose pattern is not quoted from the issue).
- **Reconciling EXP-074's "identifiers searched on 1 of 12".** That figure is the coverage of EXP-074's key-identifier rule (backticked or CamelCase issue tokens that also occur in the gold patch's changed lines), which yields any identifier on only 1 of the 12 F runs (EXP-074 defect 2); it does not say the E4B failed to search the issue. Under this file's broader definition, 9 of 12 unresolved F runs searched an issue-quoted string before the first edit (the same 9 that opened with one). The broader definition admits generic strings: the qualifying patterns are held by 1 to 311 snapshot files (`trunc.py` files_with).

### 3.2 Why the gold file is not shown (unresolved F, 12 tasks)
| Group | Tasks | Ids |
|---|---|---|
| no opener | 3 | `fastapi_14962`, `rich_3067`, `rich_3953` |
| opener held; the gold file does not hold the searched issue string | 3 | `fastapi_14583`, `fastapi_5624`, `rich_3105` |
| opener held; the gold file holds the searched string; the output did not name it | 6 | `fastapi_11355` (head), `fastapi_13207` (head, head, other), `fastapi_14512` (head; pattern in 311 files), `fastapi_14448` (scoped_other), `requests_7315` (scoped_other), `rich_3480` (cap, then scoped_other) |

- On those 6, the qualifying searches named a gold file **0 times**. Gold shown before the first edit by any observation: 5 of 12 unresolved F (3 by path, as EXP-074 section 7 point 2 has it).
- Over all 48 tasks: 33 qualifying searches; 19 named a gold file, 2 were `scoped_gold` (`fastapi_14297` S, `rich_3676` E: the model was already inside the gold file), 4 `head`, 6 `scoped_other`, 1 `cap`, 1 `other`. Tasks where an issue-pattern search named a gold file: 18 of 48.

### 3.3 Noise (`rerun.py`, `experiments/EXP-075/noise.py`)
- **The opener is per-draw, not per-task:** it flips on 7 of 16 shared task-runs between EXP-038 and the two same-tree reruns (EXP-033-e4b 3 of 8, EXP-044-X0 4 of 8); 9 of 24 on the variants. `shown` flips on 3 of 16 reruns, 1 of 24 variants.
- **F is a per-draw state too:** on reruns F_entered 3 of 15 (EXP-038 not-F tasks that are F in the rerun); F_left 0 of 1, a single task-run and not usable as a reference; on the variants F_left 2 of 2 (one id, `fastapi_14448`, in two runs). Same-tree F rate per task-run: EXP-038 13 of 48 (with `requests_6644`), EXP-033-e4b 2 of 8, pooled 15 of 56 = 0.27; over 48 that is a mean of 13 F with a standard deviation of about 3.1.

## 4. Finding: the dispatched opener has no readable form on dev-48
- The opener is buildable (EXP-068's drafter line held on 36 of 40 turns), and its compliance endpoint would read: from 30 of 48 to about 43 of 48 at the drafters' rate.
- Its causal ceiling on F is the 3 unresolved F tasks without it, and nothing in the record says that an issue-quoted search would have named their gold file: on the 9 F tasks where the opener did hold, an issue-pattern search named a gold file on 1 (`fastapi_14583`, which then edited another file) and the qualifying searches named it 0 times (section 3.2).
- A 3-task ceiling sits inside one standard deviation of the net F count (3.1), and "F tasks leaving F" has no usable rerun reference (F_left 0 of 1). Both outcome endpoints of the dispatch would read inside noise even at full conversion, and the arm would cost about 1.3 GPU-h (EXP-038 ran 1.267 h).
- **So the arm is not built.** No candidate tree, zip or notebook exists for EXP-076.

## 5. What the counts point to instead (for the lead; not built, not pre-registered)
The failure in section 3.2 is in what the search returns, not whether a search is made: 3 F tasks lost the gold file to `| head` on a generic pattern, 1 to the 5000-character cap, and 3 searched inside a file chosen in advance.
- **Candidate form:** the base prompt's search recipe returns a file list, `git grep -l "TOKEN" -- '*.py'`, with no `head`, in place of `git grep -n "TOKEN" -- '*.py' | head -20`. One recipe line, tool-native, no new flag beyond the one replaced.
- **Simulated ceiling (`trunc.py` list_ok):** an unscoped file list names a gold file within 5000 characters on 5 of the 6 tasks in the third group of section 3.2 (all but `fastapi_14512`, 311 files). The recipe alone (no change in scoping) reaches 3 of them (`fastapi_11355`, `fastapi_13207`, `rich_3480`); the other 2 need the model to search the whole repository rather than a chosen file. Every one of the 19 qualifying searches that named gold would still name it in the list form.
- **Readability:** the outcome ceiling (3 to 5 of 12 F) is also inside the net-F noise of section 3.3. Its mechanism endpoint would read: "an issue-pattern search output names a gold file before the first edit", per task, base 18 of 48, and 0 of 6 on the F tasks of the third group.
- **Risks to weigh:** the list carries no line numbers, which the base uses to pick its `read_file` range, so R, C and S tasks could lose in-file anchoring (EXP-074 lever 4); and the E4B rewrote or ignored a multi-flag recipe on about a quarter of tasks (EXP-071), so uptake is not given.

## 6. Defects
1. `desk.py`'s `shown` and `issue_search_shows_gold` look for a gold path or basename in the observation, so a search scoped to the gold file itself (grep prints no file name) counts as not shown. This undercounts by 2 tasks over 48 (`fastapi_14297`, `rich_3676`), neither of them F; the F figures are unaffected. `trunc.py` labels the case `scoped_gold`.
2. The opener's pattern rule takes the first non-option word after the program; a pattern given after `-e` is read correctly, one given after an unlisted option that takes a value is not. No miscount was found by hand in the F rows.

## Status
**DESK CHECK COMPLETE 2026-11-12; the dispatched dev-48 arm is NOT BUILT (section 4).** Section 5's file-list form is offered to the lead as a different lever, not built and not pre-registered.
