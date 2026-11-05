# EXP-035 — Would an existing test have shown the wrong fix? The grader's failing tests on EXP-028's unresolved patches, split by whether the agent could see them

**Date:** 2026-11-05
**Type:** zero-GPU trace mining over runs already on disk. No kernel, no upload, 0.0 L4x4-h.
**Cohort:** dev-48 (EXP-028 Arms R and RH, unresolved tasks with a non-empty patch; no new run)
**Ladder:** L1 (trace mining). L0 is EXP-034 Q2, which could not answer this question from the agent's own test runs (21 of Arm R's 30 right-file-wrong-fix tasks ran no test after the last edit). The grader's output exists for every task, so this level can read it.
**Pre-registered:** this file is committed before any count in sections 3 and 4 is computed. Sections 2 to 6 are written blind and are not revised. Results are appended as section 9, which applies the readings as written.
**Serves:** D-005 (the executed verify-and-fix stage, ranked first in "Stage 0 results"); C-015; the F3 verifier design.
**Relates:** EXP-034 (Q2; its `mine.py` defines the right-file-wrong-fix group and is reused by import), EXP-028 (Arms R and RH), EXP-030 L1b (the "patch touches a gold file" measure).

## 1. Why this, now

D-005 ranks a verify-and-fix stage first. That stage pays only if the check it runs can fail on a wrong fix. EXP-034 Q2 asked the agent's own test runs and got no answer: in Arm R's 30 right-file-wrong-fix (RFWF) tasks, 21 ran no test after the last edit, 7 ended on a visible pass, 1 on a fail. The grader's output answers a narrower question for every task: which tests failed at grading, and did each one exist, unchanged, in the code the agent could see?

**Desk check (done before these readings were written).**
- `test_tail` is the last 1500 characters of `STDOUT:\n<pytest stdout>\nSTDERR:\n<pytest stderr>` (notebook cell, `notebooks/kaggle_eval_l4x4.py:358`). The grader runs `python3 -s -m pytest <files> --junitxml=... -p no:anyio -o timeout=0 -o python_classes="Test* *Test" -q` (`data/src/swegemma/swegemma/harness/verification.py`, the `pytest_cmd` block). With `-q` and pytest's default report characters, the tail ends with a `short test summary info` block that has one `FAILED <path>::<node>` or `ERROR <path>::<node>` line per failing test, then a count line such as `N failed, M passed in Ts`.
- On the two EXP-025 arms (not endpoint arms here), 16 of 18 unresolved non-empty-patch tails in each arm carry the summary header. 8 (A25) and 10 (B25) carry at least one `FAILED <path>::<node>` line. 9 and 8 are collection interrupts, which list files, not tests. 12 and 15 hit the 1500-character limit.
- **So the tail lists failing test ids, not only a count. This experiment uses the per-test-id form**, not the fallback "any failure outside the files the test patch touches".
- **Seen on the endpoint arms before writing (disclosed as prior knowledge).** Arm R's `test_exit_code` over all 48 tasks: 0: 9, 1: 17, 2: 17, -1: 5. It has 33 unresolved tasks with a non-empty patch. I read four R tails: all four were collection errors. Three were a missing third-party test module at grading, and one was an import of a name the patched source does not define. Nothing else from R or RH was looked at.

**Grader facts that shape the categories** (read from `verification.py` and `models/task.py`):
- The grader runs only the test-patch files. The targets are `task.test_files` if set, else `extract_test_files_from_patch(task.test_patch)`, keeping `.py` files only. `data/raw/tasks.jsonl` has no `test_files` field. So **category (a) below is zero by construction.** It is kept only as a sanity check on the parser, and the question reduces to (b) against (c).
- Before the test patch is applied, the target test files and any test or config file the agent touched are reset to the baseline commit.
- Exit 2 is an interrupted run (collection errors). Exit -1 is returned when the test patch fails to apply. A grading-command timeout may also give -1; that is unverified.
- The agent sandbox does not mask pytest for our tree: `enable_sandbox_testing` defaults to True and nothing in our trees sets it (`experiments/README.md` line 755). Running a test-patch file's pre-patch version was therefore possible in principle, unless its imports fail in the sandbox.

**Snapshots are on disk.** `data/local/snapshots/<id>.tgz` holds all 129 tasks; each is a full repo, tests included, at the base commit. Checked for the 48 dev-48 ids before this file was written:
- The test patches name 127 test files; 27 are created by the patch, which here means a single `@@ -0,0 +1,N @@` hunk, since no `/dev/null` header is used.
- All 100 modified files exist in the snapshot.
- Every hunk's old side matches the snapshot file exactly at the stated line numbers (0 mismatches).
- `data/local/missing_snaps.txt` is stale.

Existence is therefore read from the snapshot itself. The diff-only method is run only as a cross-check (§2.3).

## 2. Design

### 2.1 Population

- **Arms:** EXP-028 Arm R (primary) and Arm RH (replicate): `runs/EXP-028-armR`, `runs/EXP-028-armRH`, the `task_results.jsonl` of each.
- **All-unresolved group:** tasks with `resolved` false and a non-empty `patch`.
- **RFWF group:** EXP-034's definition, imported from `experiments/EXP-034/mine.py`, not re-written: `not resolved and bool(patch_files(agent_patch) & patch_files(gold_patch))`, with `patch_files` from `mine.py` and the gold patch from `data/raw/tasks.jsonl`. EXP-034 found 30 RFWF tasks in R and 27 in RH; a different count here is an infrastructure failure (row 0).

### 2.2 Parsing the tail

- **Split.** The tail is split at the last `\nSTDERR:\n`, and only the stdout part is parsed. If the tail is 1500 characters long, its first line is dropped as partial.
- **Failing test ids.** Lines `FAILED <id>` or `ERROR <id>` where `<id>` contains `::`. The id is `<path>::<name>[::<name>]`, cut at the first `[`, at ` - `, or at the end of the line. The path is the file, the last name is the test function, and an earlier name is its class. Ids are deduplicated.
- **File-level errors.** Lines `ERROR <path>.py` with no `::` mark a file that failed to collect.
- **Count line.** The last stdout line matching `in <float>s` that also carries a `passed`, `failed`, `error` or `skipped` count, or the words `no tests ran`. The expected number of failing ids is failed plus errors on that line.
- **Complete list.** The `short test summary info` header is present, and the number of parsed ids is at least the expected number. Anything else is a **partial list**.
- **Not readable as a test list:**
  - exit code -1 (**timeout / test patch did not apply**);
  - a collection interrupt (`Interrupted:` with `during collection`, or any file-level `ERROR <path>.py` line) (**collection error**);
  - no count line and no parsed id (**crash**: the test session died, for example on a conftest import);
  - unresolved with zero parsed ids and a count line showing no failures (**no failing test shown**, for example a JUnit-validation rejection).

### 2.3 Classifying one failing test

| cat | rule |
|---|---|
| (a) | the test's file is not among the test patch's files (expected never; any count above 0 is reported as a parser fault) |
| (c) added | the file is created by the test patch, or the test function is not found in the snapshot file but a `+` line of the test patch defines it |
| (c) changed | the test exists in the snapshot file, and the test patch changes its own span. The span runs from its first decorator line to `end_lineno`, from `ast` on the snapshot file. "Changes" means: a `-` line at an old line inside the span; a `+` insertion at an old position P with span start < P <= span end; a `+` run inserted directly before the span start whose last non-blank line is a decorator (`@`); or a `+` run inserted directly after the span end whose first non-blank line is indented deeper than the `def` |
| (b) | the test exists in the snapshot file, in a file the test patch modifies, and none of the (c) changed rules hold |
| unlocated | the function is found neither in the snapshot nor on a `+` line (for example a test inherited from a base class in another file, or generated in a loop) |

- **Locating a test.** Name lookup: for `Class::name`, a method `name` of a class `Class` anywhere in the module. For a bare `name`, a module-level function `name`; if there is none, any function `name`.
- **Unparseable snapshot files.** If `ast` cannot parse a snapshot file, that file falls back to the diff-only rule, and the number of such files is reported.
- **(b-strict)**, a secondary category: (b), and every test-patch change in that file that lies outside the spans of the snapshot's `test*` functions is one of these:
  - a blank line;
  - a comment;
  - an `import` / `from ... import` line;
  - part of a `+` run that contains a `def test` or `class Test` line.

  b-strict excludes the case where the patch changed a fixture, helper, parametrization list or module-level constant that an unchanged test uses. In that case the agent's pre-patch copy of the test might pass where the hidden copy fails.
- **Diff-only cross-check** (the method a missing snapshot would force; reported as test-level agreement with the snapshot method):
  - (c) if the file is created, or a `+` line defines `def <name>(`;
  - (b) otherwise.

  It cannot see a test's existence when the test lies outside every hunk's context. It cannot tell a changed body from an unchanged one unless the `def` line is inside a hunk. And it cannot tell a moved or renamed test from an added one. So it errs toward (b).

### 2.4 Per-task category (primary)

First match governs:
1. **Unreadable**: no failing test id parsed and the run is a timeout / patch-not-applied, collection error, crash, or no-failing-test-shown case (§2.2).
2. **Visible**: at least one parsed failing test is (a) or (b). A partial list can establish this, because one listed visible test is enough.
3. **Hidden only**: the list is complete and every parsed failing test is (c).
4. **Unreadable**: everything else (a partial list with no visible test, or an unlocated test and no visible one).

**Sensitivity lines** (reported, not governing):
- S1 **literal rule**: a partial list is unreadable even when it lists a (b) test.
- S2 **visible-strict**: visible requires a b-strict test.
- S3 **visible-broad**: visible, plus unreadable tasks whose collection error or crash comes from the agent's own patch (cause u2 below). Any test importing that module would have failed for the agent.

**Unreadable causes** (secondary, from the tail):
- **u0** timeout / patch not applied.
- **u1** missing third-party module: `ModuleNotFoundError: No module named 'X'`, where the top-level name X is not a top-level directory or `.py` file in the snapshot.
- **u2** the agent's patch breaks import: `SyntaxError`, `IndentationError`, `NameError`, `AttributeError` or `ImportError`, whose traceback names a file in the agent's patch, and not u3.
- **u3** the hidden test imports a name the fix never created: `ImportError: cannot import name 'N'`, where N appears on a `+` line of the test patch.
- **u4** partial list with no visible test, or an unlocated test.
- **u5** other (no failing test shown, or an error not matched above).

### 2.5 Did the agent run that test after its last edit?

For each visible task:
- (i) **any test** after the last edit: EXP-034's per-task boolean `tested_after_last_edit_<arm>`, read from `experiments/EXP-034/summary.jsonl`;
- (ii) **that file**: a test run after the last edit whose command contains the path of a file holding a visible failing test (matched as the path relative to the repo root, or its basename). This uses `mine.py`'s `calls_of`, `is_edit` and `test_kind` on the trace, with the edit set as in EXP-034.

**Consistency check:** the R tasks with `last_visible_pass_R` true in EXP-034's summary (7, all RFWF), and RH's 4. They should be hidden only, since a visible failing test that the agent ran and saw pass would contradict the grading. For each such task that is visible, (ii) is reported. A visible task with (ii) true is a contradiction, and is described by kind.

### 2.6 Hand check

- **Draw.** 10 (arm, task) items, with `random.Random(35)`, from the all-unresolved groups of R and RH pooled. The draw is stratified by `test_exit_code`, which is blind to the label: 5 with exit 1, 3 with exit 2, 2 with any other code. A short stratum is filled from exit 1.
- **Files.** For each item the tool writes `runs/EXP-035/handcheck/dossier.txt`, holding the tail, the test-patch file list with created flags, and the test patch, and separately `runs/EXP-035/handcheck/key.txt`.
- **Blind labels.** I label each item visible / hidden only / unreadable from the dossier alone and write `runs/EXP-035/handcheck/eye.txt` before opening the key.
- **Report.** Agreement k/10, with each disagreement described by kind, not by text.

### 2.7 Cost and data

- **Cost:** 0 GPU-h, no upload slot.
- **Committed:** `experiments/EXP-035/aggregates.json` (counts only) and the script `experiments/EXP-035/grader_tests.py`, committed with the results.
- **Not committed:** there is no `summary.jsonl`, because the per-task visible / hidden label is derived from the gold test patch. EXP-034 kept the RFWF membership aggregate-only for the same reason. Per-task rows stay in `runs/EXP-035/` (gitignored), per plan.md:52.

## 3. Endpoints, fixed in advance

1. **Primary:** in Arm R's RFWF group (n = 30), the counts V (visible), H (hidden only) and U (unreadable).
2. **Secondary:**
   - the same over R's all-unresolved group;
   - both groups in RH;
   - among visible tasks, how many ran any test after the last edit (EXP-034 boolean), and how many ran that file;
   - of the 7 R tasks whose last visible result was a pass, how many are hidden only (and RH's 4);
   - sensitivity lines S1 to S3;
   - unreadable causes u0 to u5;
   - test-level counts (a), (b), (b-strict), (c) added, (c) changed, unlocated;
   - diff-only agreement;
   - hand-check agreement.
3. **Statistics:** counts and shares with Wilson 95% intervals. There is no hypothesis test. The question is descriptive, and n = 30 gives intervals about ±0.17 wide near a share of 1/3.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Applied to Arm R's RFWF group (n = 30). First matching row governs.

| # | outcome | reading |
|---|---|---|
| 0 | the RFWF count is not 30 (R) / 27 (RH), or more than 2 RFWF tasks lack a tail, or `ast` fails on more than 2 of the needed snapshot files | **infrastructure: no reading.** Fix the tool and re-run; nothing is reported as a result |
| 1 | U >= 15 of 30 (half or more unreadable) | **no reading.** The grader's output cannot say whether existing tests would have exposed the wrong fix. The readable subset and the u0 to u5 causes are reported descriptively. If u1 (missing third-party module at grading) dominates, the next step is the lead's: a re-grade with the dependencies present (`regrade_patches.py` / the Docker orchestrator), not a design decision |
| 2 | V >= 10 of 30 (at least a third visible) | **existing tests would have exposed the wrong fix in a substantial share.** Running the existing test file of the edited module after the last edit, which the agent could do, would have shown a failure that the agent did not see or ignored. A verify stage can rest partly on existing tests. Candidate next rung (the lead decides): a smoke-8 screen of a "run the existing test file for the module you edited, after your last edit" rule |
| 3 | H >= 2/3 of (V + H) | **mostly hidden only.** The failing tests are ones the test patch adds or changes, so existing tests cannot carry a verify stage. It needs a model-written reproduction that fails before the fix (D-005 F3's "executed first" selector must write its own check) |
| 4 | none of the above | **mixed.** Both mechanisms occur and neither dominates. Report V, H and U; a verify stage would need both, and this experiment does not rank them |

- **Replicate.** RH's RFWF group (n = 27) is read with the same rules at its own n: row 1 at U >= 14, row 2 at V >= 9, row 3 as written. If RH fires a different row from R, the R reading is reported as **not replicated**.
- **All-unresolved group.** Read the same way, descriptively. It does not govern.
- **Sensitivity lines.** If S1, S2 or S3 alone would move R to a different row, that is stated next to the governing row.
- **Consistency check.** Any of the 7 last-pass tasks that is visible with (ii) true is reported as a contradiction. If there are 2 or more, the classifier or the EXP-034 pass label is suspect, and that is stated next to the reading.

**Prediction (written before computing).**
- R RFWF: V 5, H 11, U 14 of 30. **Predicted visible share 17%** (80% interval 5% to 35%).
- Row 3 is the likeliest at about 50%, and row 1 at about 40%, because the four R tails I saw were all collection errors. Row 2 is about 10%.
- Of the 7 last-pass tasks, at least 5 are hidden only or unreadable, and none is a contradiction.
- Hand-check agreement at least 8 of 10.

## 5. What this does and does not license

**Can decide:**
- whether the grader's failing tests on wrong fixes were tests the agent could have run before submitting (the pre-patch version, in the same file);
- hence whether a verify stage built on running existing tests has anything to catch, or must write its own failing check.

**Cannot decide:**
- whether the agent would have acted on a visible failure;
- whether the pre-patch copy of a (b) test fails for the agent's patch. That needs a run; b-strict narrows the gap but does not close it;
- anything on the hidden set;
- the effect of any prompt or architecture.

Tasks that fail only through a missing test-only package at grading say nothing about the fix. They are counted as u1 and not read.

No upload, tree change or GPU arm is licensed by any row.

## 6. Exact commands

```bash
# the script is written after this file is committed, and committed with the results
python -I -X utf8 experiments/EXP-035/grader_tests.py --tasks data/raw/tasks.jsonl --snapshots data/local/snapshots \
    --out experiments/EXP-035/aggregates.json --rows runs/EXP-035/rows.jsonl --handcheck runs/EXP-035/handcheck
```

## 7. Defects in this pre-registration, logged after the fact

1. **(2026-11-05, found by the hand check) The completeness rule in §2.2 collapsed parametrized cases.**
   - **What the text says.** Ids are cut at `[` and deduplicated, then compared with the count line's failed-plus-errors.
   - **What goes wrong.** Four failing cases of one parametrized test become one id. A complete list is then read as partial, and a hidden-only task as unreadable. Hand-check item #2 showed it: the eye said hidden only, the tool said unreadable.
   - **Correction.** The tool now counts one failing node id per summary line, parameters included. That is what pytest prints, and what "the list is complete" means. The cut-and-deduplicate ids are still used to classify each test.
   - **Effect.** §9 applies §4 to the corrected count and reports the as-written count beside it. The two fire the same row in both arms.
2. **(2026-11-05) Exit code 124 is not in u0.** §1 and §2.2 name only -1. One RH task has exit 124, the GNU `timeout` code, and an empty tail, which is a grading timeout. The tool labels it crash / u5. Only the cause split moves; the task is unreadable either way.
3. **(2026-11-05) The order of the unreadable causes was fixed in the code, not in §2.4.** The tool takes the first that matches, in the order u0, u1, u3, u2, u5. A missing third-party module comes first because such a task says nothing about the fix. This affects only the u0 to u5 split.
4. **(2026-11-05) §2.3 does not separate a (b) failure caused by the agent's patch from a failure the grading environment causes under any patch.** Dev-48 drops tasks whose gold patch failed the gold control, but that control ran in a different environment from these kernels. §9.4 reports one such case as a post-hoc line. The counts are not changed.
5. **(2026-11-05) The RH last-pass set.** §2.5 says "RH's 4". EXP-034's 4 counts RFWF tasks only; RH's per-task boolean is true for 5 unresolved tasks with a non-empty patch, 4 of them RFWF. §9 gives both counts.

## 8. Runs

There is no kernel and no upload. The script ran locally over `runs/EXP-028-armR/` and `runs/EXP-028-armRH/` (task results, traces), `data/raw/tasks.jsonl` and `data/local/snapshots/`, using the §6 command. The pre-registration was commit 372ab10, before anything was computed. After the §7.1 correction, the script was re-run with the same command. Per-task rows, the hand-check dossier, the key and the eye labels are in `runs/EXP-035/` (gitignored).

## 9. Results (2026-11-05)

GPU: 0.0 h. Every number comes from `experiments/EXP-035/aggregates.json` except the hand check (§9.5). The hand check compares `runs/EXP-035/handcheck/eye.txt`, written before the key was opened, with `key.txt` (the corrected tool) and `key_v1.txt` (the tool as written).

### 9.1 Row 0, infrastructure: does not fire

- RFWF n: R 30, RH 27. Both match EXP-034.
- RFWF tasks without a tail: 0 in each arm.
- Snapshot files where `ast` failed: 0.
- Tests that fell back to the diff-only rule: 0.

### 9.2 Primary endpoint and governing row

| group | n | V | H | U | V share (Wilson 95%) | U share (Wilson 95%) | H / (V + H) |
|---|---|---|---|---|---|---|---|
| R RFWF | 30 | 4 | 10 | 16 | 0.133 (0.053-0.297) | 0.533 (0.361-0.698) | 0.714 |
| R all unresolved non-empty | 33 | 4 | 11 | 18 | 0.121 (0.048-0.273) | 0.545 (0.380-0.702) | 0.733 |
| RH RFWF | 27 | 3 | 6 | 18 | 0.111 (0.039-0.281) | 0.667 (0.478-0.814) | 0.667 |
| RH all unresolved non-empty | 33 | 3 | 8 | 22 | 0.091 (0.031-0.236) | 0.667 (0.496-0.802) | 0.727 |

Applying §4 to R RFWF:

- **Row 1 fires (U = 16 >= 15): no reading.** The grader's output cannot say whether existing tests would have exposed the wrong fix.
- **u1 dominates** (11 of 16; §9.3). By the row as written, the next step is the lead's, a re-grade with the dependencies present, not a design decision.
- **Replicated.** RH fires row 1 too (U = 18 >= 14).
- **Rows 2 and 3 are not reached.**
  - V = 4 (RH 3) is far below row 2's 10 (RH 9).
  - The readable subset leans hidden only: H / (V + H) is 0.714 in R and 0.667 in RH, both at or above row 3's 2/3. This is descriptive only, because row 1 governs. On 14 and 9 readable tasks it is not a reading.
- **As written (§7.1).** The uncorrected completeness rule gives R V 4, H 7, U 19 and RH V 3, H 5, U 19. That is the same row in both arms.
  - The correction moves 3 R tasks and 1 RH task from unreadable to hidden only.
  - R RFWF tail forms, as written: complete 9, partial 6, collection 15. Corrected: complete 14, partial 1, collection 15.
- **Sensitivity lines.**
  - S1 (literal) and S2 (visible-strict) equal the primary in both arms.
  - **S3 (visible-broad, which counts u2 as visible) alone would move R to row 4 (mixed).** It gives V 6, H 10, U 14: U < 15, V < 10, and H / (V + H) = 0.625 < 2/3.
  - RH under S3 stays in row 1 (V 6, H 6, U 15 >= 14).
- **Consistency check: 0 contradictions.**
  - R: all 7 last-pass tasks are RFWF. 5 are hidden only, 2 unreadable, 0 visible.
  - RH: 5 last-pass tasks, 4 of them RFWF (§7.5). 3 are hidden only, 2 unreadable, 0 visible.

### 9.3 Why so much is unreadable

| arm, group | u0 patch did not apply | u1 missing third-party module | u2 agent patch breaks import | u3 hidden test imports a new name | u4 partial list / unlocated | u5 other |
|---|---|---|---|---|---|---|
| R RFWF (U 16) | 0 | 11 | 2 | 1 | 1 | 1 |
| R all (U 18) | 0 | 13 | 2 | 1 | 1 | 1 |
| RH RFWF (U 18) | 0 | 12 | 3 | 0 | 1 | 2 |
| RH all (U 22) | 0 | 14 | 3 | 0 | 2 | 3 |

- **By repository** (`posthoc_primary_by_repo`):
  - fastapi accounts for 15 of R's 16 unreadable RFWF tasks, and for 15 of RH's 18.
  - 15 of the 17 fastapi RFWF tasks in R are unreadable.
  - The u1 tails are collection errors: a test-only package is missing when the tests are imported at grading. In the tails I read for this experiment and for the hand check, it was the snapshot-testing package that the compat shims stand in for.
- **Post-hoc: a partial list whose failing files were all created by the test patch.** There is 1 such task in R RFWF, 1 in RH RFWF and 2 in RH all-unresolved. Logically these are hidden only, but §2.4 makes them u4. Moving them would give R V 4, H 11, U 15 and RH V 3, H 7, U 17. R would still be row 1 (U = 15 >= 15).
- **Post-hoc: exit 124.** The one RH exit-124 task, a grading timeout, is u5 (§7.2).
- **Tail forms.**
  - R RFWF: collection 15, complete 14, partial 1.
  - RH RFWF: collection 15, complete 9, crash 2, partial 1.
- **Exit codes.**
  - R RFWF: 1 x15, 2 x15.
  - RH RFWF: 1 x11, 2 x15, 124 x1.

### 9.4 Test level, and the visible tasks

- **Failing tests by category.**
  - R RFWF: (a) 0, as the grader's design implies; (b) 13, of which b-strict 11; (c) added 19; (c) changed 6.
  - RH RFWF: (b) 8, of which b-strict 8; (c) added 18; (c) changed 3.
- **Diff-only rule against the snapshot rule** (R RFWF): b|b 13, c|b 5, c|c 20, b|c 0. The diff-only rule never calls a test (b) when the snapshot calls it (c). It does miss 5 (b) tests in R (RH 3).
- **Did the visible tasks run the failing test after their last edit?**
  - R (V = 4): 1 ran any test, 0 ran that file.
  - RH (V = 3): 1 ran any test, 1 ran that file.
- **Post-hoc, unverified (§7.4).** Of the visible tasks, 2 of 4 in R and 2 of 3 in RH are in the requests repository.
  - In each arm, one visible task's tail traces into the installed copy of that package in site-packages, not into the workspace.
  - So the requests (b) failures may come from the grading environment, not from the agent's fix: a shadowing install, or a test that fails under any patch.
  - If they do, the visible count falls to 2 in R and 1 in RH, all in rich.
  - This was not checked against the gold patch in the same environment. It changes no row.

### 9.5 Hand check

The sample was 10 tasks, pooled over R and RH with `random.Random(35)` and stratified 5 / 3 / 2 by exit code (1 / 2 / other). The eye labels were written before the key was opened.

- **Eye against the tool as written: 9/10 on the per-task category.** The one disagreement is the §7.1 defect: the eye read hidden only, the tool read unreadable (partial).
- **Eye against the corrected tool: 10/10.**
- **Sub-label differences.**
  - The tail form of one visible task (partial against complete). The correction fixes this.
  - The cause of the exit-124 task (the eye read a timeout, the tool reads u5; §7.2).

### 9.6 Prediction against the outcome

| | predicted | observed |
|---|---|---|
| R RFWF V / H / U | 5 / 11 / 14 | 4 / 10 / 16 |
| visible share | 17% (80% interval 5-35%) | 13.3%, inside the interval |
| governing row | row 3 (about 50%), row 1 (about 40%), row 2 (about 10%) | **row 1**, the second likeliest |
| last-pass tasks hidden only or unreadable | at least 5 of 7 | 7 of 7, with 0 contradictions |
| hand check | at least 8/10 | 9/10 as written, 10/10 corrected |

The miss is in U. fastapi's u1 collection errors exceeded what I allowed for, and that moved the row from 3 to 1.

### 9.7 What this licenses

- **Nothing on the main question.** Row 1 fires and replicates.
- **Descriptive only.** In both arms:
  - few readable wrong fixes (4 and 3) fail a test that existed before the test patch;
  - those that do rarely ran that file after the last edit;
  - half of them may be environmental.
- **Next step, by row 1.** Re-grade R's and RH's patches with the missing test-only package present, so the fastapi tasks become readable. The routes are `regrade_patches.py` (the EXP-004 pattern) or the Docker orchestrator. The decision is the lead's.
- No upload, tree change or GPU arm is licensed (§5).
