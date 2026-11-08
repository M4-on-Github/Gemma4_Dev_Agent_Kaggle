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

None yet.

---

## 8. Status

Pre-registered, counting not started.
