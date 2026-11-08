# EXP-059 - What the E4B does next after a failing check: a reference count from the traces we hold

**Date:** 2026-11-08
**Type:** zero-GPU analysis (trace mining), 0 L4x4-h, no kernel, no upload
**Cohort:** none (reads the 8 smoke-8 ids, `experiments/cohorts/smoke-8.txt`, inside runs already on disk)
**Ladder:** L1 (zero-GPU trace mining). L2 and L4 cannot be asked first: the question is a count over runs that exist.
**Pre-registered:** this file is committed before any trace is counted for this question. Sections 2 to 4 are not revised after the numbers land; a defect found while counting is logged in section 7.
**Serves:** the lead's reference for "acting on the check's output", against which a later verifier-agent round would be read; lesson 5 of `knowledge/lessons-e4b-loop.md` (requests_7309 made 0 calls in all 4 skill-tree runs).
**Supersedes / relates:** EXP-055, EXP-056, EXP-057 (9.2, lesson 3: running the check is not acting on it), EXP-042 (check-before-submit, wins vs losses), EXP-033, EXP-038, EXP-045, EXP-052.

## 1. Why this, now

EXP-057 section 9.2 found that the picker works and the E4B runs the printed check in 11 of 14 task-runs, but that 3 last checks ended in a collection error and the model still submitted (fastapi_14605 in both runs, httpx_3672 in r2). A verifier round would be a change aimed at that gap. Before it is built, the gap needs a base rate: when a check fails and points at the model's own edit, what does the model do next, on the trees without any verifier? Only two sequences were read for this (the two fastapi_14605 runs and httpx_3672 r2 of EXP-057, while writing its 9.2). The counting rules below were written before any other trace was counted.

## 2. Design

**Runs covered, 9 runs, 8 smoke-8 task-runs each, 72 in all.** Skill trees: EXP-056 r1 and r2, EXP-057 r1 and r2. Base references: EXP-033 (the E4B single loop), EXP-038 (the same tree on dev-48; only its 8 smoke-8 ids are read), EXP-045 (the base tree plus one prompt bullet to write and run a python reproduction in a scratch location), EXP-052 (the fan-out tree: reader, five drafters, applier). Check-prompt tree without a skill: EXP-055. All from `official/traces/` (the slimmer `traces/` copy omits skill calls); the nested bundles are under `runs/<EXP>/runs/<EXP>/`, EXP-038 is flat.

**Families for totals.** (1) skill: EXP-056 and EXP-057. (2) base references: EXP-033, EXP-038, EXP-045, EXP-052, reported per run and as a sum, with a note that EXP-045 and EXP-052 are base-plus-one-change, not the pure base. (3) EXP-055.

**Counting rules (all fixed now).**

1. *Task-run, order.* One smoke-8 id in one run. Steps are read in file order; the tool calls of a step in the order listed.
2. *Check call.* A `run_command` whose program, after leading `cd` and variable prefixes, is `pytest`, `python` or `python3` (including `-m pytest`, `-m unittest`, `-c` and a script path). A command that only searches for the word (`grep`, `git grep`, `cat`) is not a check.
3. *Failing check.* A check whose result carries a non-zero `exit_code` (a timeout counts). The skill call itself is never a check.
4. *Applied edit.* An `edit_file` or `write_file` call whose result has status `ok`, on a path outside the scratch location. Edits that errored (including lost-argument errors) do not count as edited. "Edited by then" means applied earlier in the same task-run than the check.
5. *Names.* The result text contains a `.py` path (a traceback frame, a pytest location, a `FAILED` or `ERROR` line) that matches an applied-edit path by repo-relative path, or by base name when that is unambiguous in the run. Each failing check lands in exactly one column: **A** names an applied-edit file (the failing-check event of the question); **B** names `.py` files but none that was edited (a test file, an unedited source file, a dependency); **C** names no `.py` path (no tests ran, usage error, empty output, command not found).
6. *Exit code and class.* The exit code as recorded. The class is the exception class named by the result's first failure line, skipping the harness's own `CommandError` wrapper; if no class is named, the pytest label (`failed assertion`, `no tests ran`, `usage error`, `timeout`). Classes are reported by name only.
7. *Next action* is the next tool call after the check, in file order, and falls in one class:
   - (a) `edit_file` or `write_file` on a path that the check's output names;
   - (b) `edit_file` or `write_file` on a path the output does not name;
   - (c) the same check run again with no edit between: the same command text, or the same test target;
   - (d) any other tool call, split (d1) another `run_command` and (d2) `read_file`, `get_status` or any other tool;
   - (e) `submit_patch`;
   - (f) no further tool call: the next agent step is text only, or the trace ends.
   An edit that is attempted and rejected still counts as (a) or (b); the count of rejected ones is given beside.
8. *Tallies.* Per run and per family: failing-check events in column A with exit code, class and next action; columns B and C counted separately with the same next-action split; events by task so the clustering is visible (the 8 ids repeat across 9 runs). Counts only; no rate is given a confidence interval and nothing is tested.
9. *Q2.* For requests_7309 in each of the 9 runs: its tool-call count (calls in `official/traces`, counting `run_skill_script` and `submit_patch`), its ending (submit; text-only with no submit; other), and nudges. EXP-038's row is the task's row in the dev-48 run.

## 3. Endpoints, fixed in advance

- Q1 table: failing-check events (column A) by family, with exit code, error class, and next action (a) to (f); B and C columns beside it. Primary reading: the share of column-A events whose next action is (a) (the model acts on the output), per family.
- Q2 row: tool-call count and ending of requests_7309 in each run.
- Hygiene: the file names and counts what a trace holds (ids, counts, step numbers, exception class names, program names, exit codes, file paths, the harness's fixed labels) and does not reproduce repo or model text.

## 4. Pre-registered readings. Written blind (see section 1 for what was seen). Not to be revised after the numbers land.

This is a reference count, not a test of a claim; no row drives a change to the tree. The readings fix what the count will be used for.

| # | outcome | reading |
|---|---|---|
| 1 | column A has fewer than 5 events in a family | the family gives no usable base rate; report the counts and say so |
| 2 | in a family with 5 or more events, (a) is at most half of column A | most failing checks that point at an edit are not followed by an edit to that file: the gap a verifier would address is present on this tree |
| 3 | in a family with 5 or more events, (a) is more than half of column A | the E4B already acts on most such checks; a verifier round has less headroom on that tree, and its reference is that share |
| 4 | requests_7309 makes 0 calls in every skill-tree run and in at most 1 base-reference run | lesson 5 stands with a per-task base contrast (task-level, 8 draws at most) |
| 5 | requests_7309 makes 0 calls in 2 or more base-reference runs | lesson 5's tree effect is not supported on this task: the tool-free ending is the task's, not the tree's |
| 6 | requests_7309 makes at least 1 call in some skill-tree run | the "0 of 4" in lesson 5 is wrong as stated; report the run |

Blind expectation: column A is small in the base references (few checks are run before submit there) and larger in the skill and EXP-055 families, where the check is mandatory; in the skill family (a) is at most half of column A; requests_7309 shows 0 calls in the skill runs and at least 1 call in most base runs (rows 2 and 4). Rows 4 to 6 rest on one task and on 4 skill-tree draws and 5 base-reference draws; they are task-level facts, not tree-level.

## 5. What this does and does not license

It sets the reference count for a later verifier round and gives lesson 5 a per-task contrast. It does not show that any tree acts on checks better or worse than another (n of events small, clustered on 8 tasks, 9 runs of the same ids), does not read resolves, and does not decide a claim. A verifier round carries this table as its before-state and measures against its own counts of the same definitions.

## 6. Exact commands

Counts are made with `grep` over `runs/<EXP>/.../official/traces/trace_<id>.json` (function names, command heads, `filepath` arguments, applied-edit statuses, `exit_code`, and `.py` paths and exception classes on lines whose `exit_code` is non-zero), because no committed tool counts events in this shape and `tools/` is outside the screener's paths. Per-event reads of a single trace line are made with the file reader. No tool change is requested; if the lead wants this rerun as code, a `tools/` script that applies rules 1 to 9 is the change, and its counts must equal this file's.

## 7. Defects in this pre-registration, logged after the fact

Found while counting (2026-11-08). Rules 1 to 9 were applied as written; each item below is a case the rules did not foresee and how it was resolved, with the sensitivity where it matters.

1. **Rule 2 is silent on wrappers and on the skill name typed as a command.** `./scripts/test.sh` (EXP-056 r1 and r2, fastapi_14448; output is pytest collection errors, exit 2) and two commands whose program is the skill name or the skill-runner name typed into the shell (EXP-056 r1 httpx_3672, EXP-056 r2 fastapi_14605; exit 127, command not found) have a program that is neither `pytest` nor `python`. Applied as written: not counted as checks, listed as "excluded" (4 events, all with next action (e)). The two wrapper events would be column B.
2. **Rule 5's base-name clause on an echoed nonexistent path.** A usage error (pytest exit 4, "file or directory not found") echoes the path the model typed, which does not exist. Where the typed base name equals an edited file's base name the rule puts it in column A. Two events do: EXP-056 r1 rich_3006 and EXP-055 httpx_3672. Marked **A-dagger**. They are kept in column A (rule as written); the totals are given with and without them. This matters for one reading (section 9.3, skill family).
3. **Rule 5 on other echoed paths.** Three further usage or no-such-file errors echo a path that names no edited file: EXP-056 r2 fastapi_14301 (the skill's script path, no such file), EXP-038 fastapi_14448 and EXP-052 rich_3006 (a test path that does not exist). They are column B by the rule; marked **B-dagger**. No effect on column A.
4. **Rule 7, (a) for a scratch script.** In EXP-045 two failing runs of `python3 /tmp/repro.py` (rich_3006, rich_3468) are followed by a `write_file` of the path the output names, which is the scratch script, not an edit of the repo. Rule 7 read literally gives (a); marked **(a-star)**. Both events are column B, so the primary reading is unaffected.
5. **Rule 4 and the test file.** In EXP-057 r2 httpx_3672 the model edited `tests/test_parsers.py` (applied, status ok) between the first and second check. Its second and third failing checks therefore name an applied-edit file and are column A. EXP-057 section 9.2 had described these as errors at the test file's own import line without saying that the file had been edited.
6. **Method.** Counts were made with `grep` and the file reader (section 6). Command heads are cut at 70 characters or at the first quote inside the command, enough to name the program in every event. Timeouts (rule 3): none in the 72 traces (searched for the timeout class names and the harness's text). Passing checks (exit 0) are not events and were not tabulated. No script reproduces these counts.

---

## 8. Status

Counted 2026-11-08: Q1 and Q2 in section 9. Skill family column A has 8 events, (a) in 4 (row 2 as written, at the threshold; row 3 if the two A-dagger events are removed). Base references column A has 1 event and EXP-055 has 1 (row 1, no usable base rate). requests_7309: 0 calls in 4 of 4 skill runs, 4 to 7 calls and a submit in 5 of 5 base-type runs (row 4). Zero GPU.

---

## 9. Results (2026-11-08, zero GPU)

Notation. A, B, C are the columns of rule 5. Next actions (a) to (f) are rule 7. Exit codes and classes as recorded; "usage error" is pytest exit 4, "no tests ran" is pytest exit 5. A-dagger, B-dagger, (a-star): section 7 items 2 to 4. "Excluded": section 7 item 1. d1 is another `run_command`, d2 is `read_file`, `run_skill_script` or any other tool.

### 9.1 Q1, every counted failing check, by run

All events are in the order of the trace. "Class" is the exception class named by the first failure line, or the pytest label.

**Skill family (14 counted events: A 8, B 3, C 3; 4 excluded)**

| run | task | exit | class | col | next |
|---|---|---|---|---|---|
| EXP-056 r1 | rich_3006 | 4 | usage error | A-dagger | (e) |
| EXP-056 r1 | httpx_3672 | 127 | command not found | excluded | (e) |
| EXP-056 r1 | fastapi_14448 | 2 | ModuleNotFoundError (wrapper script) | excluded | (e) |
| EXP-056 r2 | fastapi_14301 | 2 | no such file (script path) | B-dagger | (d2) |
| EXP-056 r2 | requests_7205 | 1 | ModuleNotFoundError | C | (d2) |
| EXP-056 r2 | rich_3006 | 1 | ModuleNotFoundError | C | (d2) |
| EXP-056 r2 | rich_3006 | 5 | no tests ran | C | (e) |
| EXP-056 r2 | fastapi_14448 | 2 | ModuleNotFoundError (wrapper script) | excluded | (e) |
| EXP-056 r2 | fastapi_14605 | 127 | command not found | excluded | (e) |
| EXP-057 r1 | fastapi_14605 | 2 | ImportError | A | (a) |
| EXP-057 r2 | fastapi_14605 | 2 | NameError | A | (d2) |
| EXP-057 r2 | fastapi_14605 | 2 | ImportError | A | (a), rejected |
| EXP-057 r2 | fastapi_14605 | 2 | ImportError | A | (a) |
| EXP-057 r2 | fastapi_14605 | 2 | ImportError | B | (d2) |
| EXP-057 r2 | fastapi_14605 | 2 | NameError | A | (d2) |
| EXP-057 r2 | httpx_3672 | 2 | AttributeError | B | (d2) |
| EXP-057 r2 | httpx_3672 | 2 | AttributeError | A | (a) |
| EXP-057 r2 | httpx_3672 | 2 | AttributeError | A | (e) |

Remarks on rows. EXP-057 r2 fastapi_14605: the five checks are one sequence; the first names `exceptions.py` and `temp_pydantic_v1_params.py` (both applied edits), the fourth names only `routing.py`, `applications.py` and `__init__.py`, none edited yet (`routing.py` is edited after it), so it is B; the fifth names `routing.py` after that edit. In EXP-057 r2 httpx_3672 the first failing check names only `tests/test_parsers.py`, not yet edited (B); the file is edited next (after one read), after which the same file is named twice (A, A). EXP-056 r1 and r2 other tasks, EXP-057 r1 rich_3006, rich_3468 and r2 fastapi_14448, rich_3468: no failing counted check (the nonzero exits there are `grep` with exit 1; the checks that ran exited 0).

**Base references (18 counted events: A 1, B 15, C 2)**

| run | task | exit | class | col | next |
|---|---|---|---|---|---|
| EXP-033 | fastapi_14448 | 2 | ModuleNotFoundError | B | (e) |
| EXP-033 | rich_3006 | 1 | failed assertion | B | (e) |
| EXP-033 | rich_3468 | 1 | failed assertion | B | (e) |
| EXP-038 | fastapi_14301 | 2 | ModuleNotFoundError | B | (e) |
| EXP-038 | fastapi_14448 | 4 | usage error | B-dagger | (d1) |
| EXP-038 | fastapi_14448 | 2 | ModuleNotFoundError | B | (e) |
| EXP-038 | requests_7205 | 1 | setup error | B | (e) |
| EXP-038 | rich_3006 | 1 | failed assertion | B | (e) |
| EXP-045 | fastapi_14301 | 1 | ImportError | B | (e) |
| EXP-045 | httpx_3672 | 1 | SyntaxError | A | (e) |
| EXP-045 | requests_7309 | 2 | no such file (scratch script) | B | (c) |
| EXP-045 | requests_7309 | 2 | no such file (scratch script) | B | (e) |
| EXP-045 | rich_3006 | 2 | no such file (scratch script) | B | (a-star) |
| EXP-045 | rich_3468 | 2 | no such file (scratch script) | B | (a-star) |
| EXP-052 | fastapi_14301 | 2 | ModuleNotFoundError | B | (e) |
| EXP-052 | rich_3006 | 4 | usage error | B-dagger | (e) |
| EXP-052 | rich_3468 | 5 | no tests ran | C | (d1) |
| EXP-052 | rich_3468 | 5 | no tests ran | C | (e) |

Tasks not listed ran no counted failing check in that run (EXP-033 fastapi_14301, EXP-038 rich_3468 and EXP-052 requests_7309 ran no check at all; their nonzero exits are `grep`). EXP-052's edits come only from the applier; its checks are the applier's. In every B row the output names test files, a conftest, or `__init__.py`, never an edited file.

**EXP-055 (7 counted events: A 1, B 4, C 2)**

| run | task | exit | class | col | next |
|---|---|---|---|---|---|
| EXP-055 | fastapi_14301 | 2 | ModuleNotFoundError | B | (e) |
| EXP-055 | fastapi_14605 | 5 | no tests ran | C | (e) |
| EXP-055 | httpx_3672 | 4 | usage error | A-dagger | (e) |
| EXP-055 | requests_7205 | 1 | setup error | B | (e) |
| EXP-055 | requests_7309 | 1 | setup error | B | (e) |
| EXP-055 | rich_3006 | 1 | failed assertion | B | (e) |
| EXP-055 | rich_3468 | 5 | no tests ran | C | (e) |

### 9.2 Q1 totals by tree family

| family | counted events | A | B | C | excluded | A: (a) | (b) | (c) | (d1) | (d2) | (e) | (f) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| skill (EXP-056 r1, r2, EXP-057 r1, r2) | 14 | 8 (1 is A-dagger) | 3 | 3 | 4 | 4 (1 rejected) | 0 | 0 | 0 | 2 | 2 | 0 |
| base references, sum | 18 | 1 | 15 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| EXP-033 | 3 | 0 | 3 | 0 | 0 | | | | | | | |
| EXP-038 | 5 | 0 | 5 | 0 | 0 | | | | | | | |
| EXP-045 | 6 | 1 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| EXP-052 | 4 | 0 | 2 | 2 | 0 | | | | | | | |
| EXP-055 | 7 | 1 (A-dagger) | 4 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |

Column A in the skill family, by run: EXP-056 r1 1 (A-dagger), EXP-056 r2 0, EXP-057 r1 1, EXP-057 r2 6. Its 8 events fall on three tasks: fastapi_14605 5 (EXP-057 r1 one, r2 four), httpx_3672 2 (EXP-057 r2), rich_3006 1 (A-dagger). Outside the skill family there are 2 more A events, both on httpx_3672 (EXP-045 genuine, EXP-055 A-dagger), so httpx_3672 has 4 in all across the nine runs. Next actions for the 8 skill A events: (a) 4 (EXP-057 r1 fastapi_14605; EXP-057 r2 fastapi_14605 twice, one of them rejected; EXP-057 r2 httpx_3672 once), (d2) 2 (both EXP-057 r2 fastapi_14605, a read before any edit), (e) 2 (EXP-056 r1 rich_3006, A-dagger; EXP-057 r2 httpx_3672 last check). B and C in the skill family: all 6 are (d2) except one (e).

Additional description, post hoc, not one of rules 1 to 9: for each A event, whether an applied edit to a file the output names follows before the next check or the end of the run (this credits a read followed by an edit). Skill family, 8 A events: yes in 5 (EXP-057 r1 one; EXP-057 r2 fastapi_14605 first, second and third; EXP-057 r2 httpx_3672 second), no in 3 (EXP-056 r1 rich_3006 A-dagger, EXP-057 r2 fastapi_14605 fifth, EXP-057 r2 httpx_3672 third). Outside the skill family the one genuine A event (EXP-045 httpx_3672, a syntax error in an edited file) is followed by the submit with no edit, as is the A-dagger in EXP-055.

Where the runs end after a column-A event with no later edit and no later check: EXP-057 r2 fastapi_14605 (NameError at the last check), EXP-057 r2 httpx_3672 (AttributeError at the last check), EXP-045 httpx_3672 (SyntaxError in an edited file), plus the two A-dagger runs. In EXP-057 r1 fastapi_14605 the edit that follows the failing check is not re-checked before the submit.

### 9.3 Readings applied as written (section 4)

| # | fires? | detail |
|---|---|---|
| 1 | yes for base references (A = 1) and for EXP-055 (A = 1); no for the skill family (A = 8) | base and EXP-055 give no usable base rate for column A. Their failing checks are mostly collection or setup errors in the test environment, or a test path that does not exist (B 15 of 18 and B 4 of 7). |
| 2 | yes for the skill family as written: (a) is 4 of 8, which is at most half | at the threshold by exactly one event. Removing the one A-dagger event (a typed path that does not exist) gives (a) 4 of 7, more than half, which is row 3. The row is therefore not robust to a one-event change in rule application, and the 8 events sit on 3 tasks, 5 of them on fastapi_14605. With the post hoc credit for an edit after a read, 5 of 8 are followed by an edit to a named file. |
| 3 | no as written (see row 2 sensitivity) | |
| 4 | yes | requests_7309 makes 0 calls in 4 of 4 skill runs and at least 4 calls in 5 of 5 base-type runs (Q2 below). |
| 5 | no | 0 of 4 base-reference runs and 0 of 1 EXP-055 run have 0 calls. |
| 6 | no | no skill run has a call. |

Blind expectation against the count. Held: column A is near zero in the base references (1 of 18 events); in the skill family (a) is at most half (exactly half); requests_7309 has 0 calls in the skill runs and calls in every base run. Not held: column A is small in EXP-055, which has the mandatory check but 1 of 7 events, and that one is an A-dagger; the mandatory check there is the full test suite or a mistyped path, whose failures do not name the edit.

### 9.4 Q2, requests_7309

Calls are counted from `official/traces` (every tool call, including `run_skill_script` and `submit_patch`); nudges are the continuation-nudge steps. EXP-038's row is the task's row in the dev-48 run.

| run | tree | tool calls | ending | nudges |
|---|---|---|---|---|
| EXP-033 | base single loop | 4 | submit | 0 |
| EXP-038 | base single loop (dev-48 run) | 4 | submit | 0 |
| EXP-045 | base plus the scratch-reproduction bullet | 7 | submit | 0 |
| EXP-052 | fan-out (reader 2, applier 2) | 4 | submit | 0 |
| EXP-055 | mandatory-check prompt, no skill | 5 | submit | 0 |
| EXP-056 r1 | skill | 0 | no tool call, no submit | 3 |
| EXP-056 r2 | skill | 0 | no tool call, no submit | 3 |
| EXP-057 r1 | skill | 0 | no tool call, no submit | 3 |
| EXP-057 r2 | skill | 0 | no tool call, no submit | 3 |

Lesson 5 stands as written with the base contrast: 0 calls in 4 of 4 skill runs, calls in 5 of 5 other runs of the same task (4, 4, 7, 4, 5), a submit in each. The contrast is one task, nine runs. Two of the base-type runs (EXP-045, EXP-055) ran a check on this task and neither check named the edited file (EXP-045: scratch script not found, twice; EXP-055: a setup error in the test fixtures); the nudge count of 3 in each skill run matches a run that never leaves a text-only turn.

### 9.5 What this licenses

A verifier round's before-state on the skill tree is: 8 failing-check events that point at an edit in 4 task-runs of 32 (1 dagger), (a) in 4 of 8, a rejected edit in 1 of the 4, the last check unrepaired at submission in 2 of the genuine events. On the base trees and EXP-055 the count that a verifier would be read against is about 1 event in 25 (2 including EXP-055's dagger), because the checks that run there do not name the model's edit; a verifier on those trees would first need to make the check one that can name it. Not licensed: any statement that a tree acts on checks better or worse, or any rate with an interval. The events are clustered on three tasks and, in the skill family, mostly on one task-run.

No tool change is requested.

