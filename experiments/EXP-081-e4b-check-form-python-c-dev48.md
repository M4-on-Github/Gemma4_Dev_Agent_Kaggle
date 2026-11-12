# EXP-081 — The check form on the E4B single loop: a desk check, then (only if it supports it) a two-draw python -c check arm on dev-48

**Date:** 2026-11-12
**Type:** first a zero-GPU desk check (sections 1 to 4). A dev-48 arm of two kernels of one zip, about 1.3 to 1.65 GPU-h each, is pre-registered and built only if section 4's rule supports it. Nothing is pushed before the critic's prereg review. No upload.
**Cohort:** dev-48
**Ladder:** L1, trace mining over the four E4B dev-48 draws, EXP-028 arm R (31B), and the E4B runs on disk. L4 only if the desk check supports it.
**Pre-registered:** sections 1 to 4 (the rules, the decision rule and the predictions) are committed before `experiments/EXP-081/desk.py` exists or any count in section 3 is made. The counts are appended in section 5. If the arm is built, its design and readings are a later section, written before any arm kernel exists.
**Serves:** D-011, from EXP-080 (the post hoc check-form table and the e2 to e4 lever).
**Relates:**
- EXP-080: check items e1 to e4 and the post hoc form table. The E4B's checks are pytest runs (109 of 113 over the four draws), 106 of the 109 exit non-zero, and its last check passed on 1/16, 0/21, 3/32 and 1/27 of the tasks with a check. Arm R's checks are `python -c` (32) and scripts (18); 34 of 50 exit 0.
- EXP-045 (smoke-8, a "write and run a short python reproduction" bullet): the E4B used `python3 -c` after its last edit on 6 of 8. A `write_file` to `/tmp` was refused on 3 of 8, and a workspace repro file ended up in one patch.
- EXP-055 (smoke-8, last call a one-command check): of 7 checks, 3 ran no tests (exit 4 or 5) and 1 hit a pre-existing collection error.
- EXP-057 lesson 4: an exit 2 whose error points into an edited file is a check that found the model's breakage.
- EXP-071 and EXP-072: a multi-flag recipe is taken up on about a quarter of tasks, and a recipe in prose comes back as text.

**What was already seen when these rules were written.** This list is complete.
- EXP-080's exit-code table for the four draws (exit 2 is the most common code, then exit 1, then exit 4).
- The EXP-045 and EXP-055 section 9 counts above.
- The JSON envelope of one `run_command` observation (`status`, `stdout`, `stderr`, `exit_code`). No check output was read.

## 1. The questions (the dispatch)
1. **Q1.** Why do the E4B's pytest checks fail? Split them by exit code and by cause class (section 2.2). What share carries any signal about the change?
2. **Q2.** What does the E4B do in the step after a failed check?
3. **Q3.** Arm R: what share of its python checks exercises the changed code, and what did it do after its failed checks?
4. **Q4.** Uptake: what happens when the E4B runs a `python -c` or script check? Does it emit that form at all?

## 2. Definitions (fixed before any count)

### 2.1 Scope
- **A check:** EXP-080's definition (`items.scripted`): a `run_command` in a step after the run's first successful change, whose command matches `items.CHECK_RE` (`python`, `python3` or `pytest` as a program).
- **Form:**
  - `pytest`: the command holds the word `pytest`. This includes `python -m pytest`.
  - `python -c`: the command holds ` -c `.
  - `script`: any other match.
- **Q1 and Q2 runs:** the four E4B dev-48 draws, `EXP-038-e4b-dev48`, `EXP-077-base`, `EXP-075-t02` and `EXP-078-t02r`, all 48 tasks each.
- **Q3 run:** `EXP-028-armR`, all 48 tasks.
- **Q4 runs:** every E4B run dir on disk, resolved by `noise.run_dir`.
  - The list: EXP-033-e4b, EXP-038-e4b-dev48, EXP-040-v1, EXP-044-X, EXP-044-X0, EXP-045-p, EXP-046-team, EXP-052-t2, EXP-053-r, EXP-055-v, EXP-056-r1, EXP-056-r2, EXP-057-r1, EXP-057-r2, EXP-061-r, EXP-062-r, EXP-063-p, EXP-064-loc, EXP-066-srch, EXP-068-read, EXP-069-argform, EXP-071-anchor, EXP-072-verify, EXP-073-repro, EXP-075-t02, EXP-077-base and EXP-078-t02r.
  - `EXP-075-base038` is a copy of EXP-038 and is left out.
  - Q4 counts every python-form command (forms `python -c` and `script`) at any step, and separately those that are checks.
- **The text of a check:** the `stdout` and `stderr` fields of the observation envelope, decoded. If the envelope does not parse, the decoded raw observation is used.
- **Changed files at a check:** the `filepath` arguments of the successful changes (`items.is_change`) in steps before the check's step, with any leading `/workspace/` or `./` removed.
- **Own new text at a check:** the `new_string` and `content` arguments of those changes.

### 2.2 Q1 cause classes (first match wins, in this order)
| Class | Rule | Counted as |
|---|---|---|
| P | exit 0 | pass |
| X | exit not found (`?`) | noise (unknown) |
| U, usage or path | exit 4 or 5 or 127. Or the text holds one of: `file or directory not found`, `no tests ran`, `unrecognized arguments`, `can't open file`, `fixture '` followed by `' not found`, `command not found` | noise |
| M-own | the text holds `No module named` and the named module (or its top-level name) appears in the own new text | signal |
| M-repo | the text holds `No module named`, and the top-level name is a top-level package dir or module of the repo snapshot (the repo itself does not import from where the check ran) | noise (sandbox or path) |
| M-env | the text holds `No module named`, any other module (absent from the repo and the sandbox) | noise (sandbox) |
| L, linked | the text names a changed file. Match the file's last two path components, or the file name alone when the file sits at the repo root | signal |
| C, other collection | exit 2 or 3, or the text holds `ERROR collecting`, `ImportError`, `conftest` or `PluginValidationError` | noise (collection) |
| F, failure not linked | anything else: a test or script failure that names no changed file | ambiguous |

- **Signal share, lower bound:** (M-own + L) / non-zero checks.
- **Signal share, upper bound:** (M-own + L + F) / non-zero checks. F can be a failure of the behaviour the change targets, a failure that predates the change, or an environment failure. The base commit cannot be run offline, so F is not split further.
- **Noise share:** (X + U + M-repo + M-env + C) / non-zero checks.
- Q1 is read on the non-zero pytest checks. The same classes are printed for the E4B's non-pytest checks and for arm R's non-zero checks, for comparison.

### 2.3 Q2 next action
For each non-zero check, take the next tool call after the check: the next call in the same step, else the first call of a later step.

| Code | Next call |
|---|---|
| S | `submit_patch` |
| R | `run_command` with the identical command string |
| K | another check (`CHECK_RE`, a different string) |
| E | `edit_file` or `write_file`, successful or not |
| D | `read_file`, or a `run_command` that is not a check |
| T | `get_status` |
| N | none, the run ends |

The table is printed over all non-zero E4B checks and cross-tabbed by Q1 class.
- **Fixed after a failure:** EXP-080's e3, a successful change later than the run's last failed check. It is reprinted per draw.

### 2.4 Q3 exercises the changed code (arm R, and the E4B's python-form checks in Q4)
- **The source of a check:**
  - For `python -c`, the command string.
  - For `script`, the script path: the first argument ending in `.py` after the interpreter. Its source is the `content` of the last earlier `write_file` whose `filepath` ends with that path, or the body of an earlier `run_command` that writes that path with `cat >` or `tee`. If neither is found, the check is `unknown`.
- **Exercises (y):** the source holds any one of the following:
  - the dotted module path (2 or more components) of a changed file, e.g. `pkg.sub.mod` for `pkg/sub/mod.py`, with `/__init__` dropped;
  - `from <parent dotted path> import <module name>` for a changed file;
  - as a whole word of 3 or more characters, an enclosing `def` or `class` name of the run's final patch hunks (`items.enclosing_names` applied to the run's own patch).
- **Otherwise:** n.
- **Reported:** y / n / unknown over all checks, and split by exit 0 against non-zero. Q2's next-action table is reprinted for arm R's non-zero checks, with e3 (fixed after a failure) over its tasks with a failed check.

### 2.5 Q4 uptake
- **Per E4B run:**
  - the tasks with any python-form command at any step;
  - the python-form commands, with their form and exit codes;
  - how many of them are checks;
  - for scripts, whether an earlier `write_file` of the script path was refused (`refs.failed`);
  - the Q1 class of each non-zero python-form check;
  - the Q3 exercises code of each python-form check.
- **Pooled:** over all E4B runs on disk, and over the four dev-48 draws alone.

## 3. Decision rule (written before any count)
Build the arm if both B1 and B2 hold; otherwise do not build, and say which failed.
- **B1, the failed pytest checks carry little signal.** Over the non-zero pytest checks of the four draws:
  - the noise share is 0.50 or more;
  - **and** the lower-bound signal share (M-own + L) is 0.25 or less.
  - If the lower bound is above 0.25, the E4B's checks do find its breakage, and the gap is acting on them, not their form. Do not build.
- **B2, the form has an uptake path.** Both parts must hold:
  - **(a)** in at least one E4B run whose prompt directs a python command, a `python -c` or `python3 -c` command after a change appears on 4 or more of 8 tasks. EXP-045-p is the known candidate; Q4 recounts it with this file's rules.
  - **(b)** over all E4B python-form checks on disk, the exit 0 share is 0.40 or more, and the M-repo share of the non-zero ones is 0.25 or less (the repo is importable from where the check runs).
  - (b) is read only if there are 6 or more such checks. With fewer, B2 rests on (a) alone, and the file says so.
- **What does not decide:** Q2 and Q3. They shape the arm's wording (whether a failed check should lead to one more edit, and whether the 31B's form reaches the change). They do not decide whether to build.

## 4. Blind predictions (before any count)
- **Q1:** noise share about 0.6. U and C dominate, from the exit 4 and exit 2 mass. L about 0.1 to 0.2, F about 0.2 to 0.3, M-own 0 or 1.
- **Q2:** submit is the most common next action, about half. R and K together about a quarter, E about 0.1.
- **Q3:** arm R exercises the changed code on about 0.7 of its checks. After a failed check it edits more often than the E4B does.
- **Q4:** python-form commands appear on fewer than 1 in 10 tasks in the dev-48 draws. EXP-045-p reproduces 6 of 8 by this file's rules. The exit 0 share of the E4B's python-form checks is about 0.5.
- **Decision:** build. B1 and B2 both hold.

## 5. Desk-check counts
- **Command:** `python -I -X utf8 experiments/EXP-081/desk.py`, plus `--per-check` for the per-check list.
- **When:** 2026-11-12, after the commit of sections 1 to 4 (6a554d5).
- **Post hoc lines:** the script's block headed "Post hoc" was added after the first read (section 7, defect 2). It is not part of the decision rule.
- **Cross-check:** the check counts reproduce EXP-080 (113 checks, 109 pytest, 106 non-zero), as do e3 (1/16, 1/21, 2/30, 0/26; arm R 3/12).

### 5.1 Q1: why the E4B's pytest checks fail (four dev-48 draws)
| Draw | Checks (tasks) | Forms | Non-zero pytest by class |
|---|---|---|---|
| EXP-038 | 19 (16) | pytest 17, script 2 | U 3, M-env 11, C 2, F 1 |
| EXP-077 | 24 (21) | pytest 24 | U 6, M-env 8, L 5, C 1, F 4 |
| EXP-075 | 39 (32) | pytest 37, script 2 | U 6, M-env 12, L 7, C 3, F 7 |
| EXP-078 | 31 (27) | pytest 31 | X 2, M-env 10, L 5, C 3, F 10 |

**Pooled pytest checks, exit code by class:**
| Exit | Classes |
|---|---|
| 0 | P 3 |
| 1 | L 11, C 9, F 22 |
| 2 | M-env 41, L 6 |
| 4 | U 15 |
| ? | X 2 |

**Shares over the 106 non-zero pytest checks:**
| Share | Count | Share |
|---|---|---|
| Noise (X + U + M-repo + M-env + C) | 67 | 0.632 |
| Signal, lower bound (M-own 0 + L 17) | 17 | 0.160 |
| Signal, upper bound (adding F 22) | 39 | 0.368 |

- **Every exit 2 with a missing module names one of two test-only packages.** All 41 M-env checks: `dirty_equals` 27 and `inline_snapshot` 14. They fall on 40 task-draws over 19 distinct ids.
  - These two packages are absent from the sandbox. `tools/compat_shims/` exists for them.
  - On those tasks, the test file fails at import before any test runs, whatever the change.
- **Tasks whose every check was noise:** 14/16, 14/21, 19/32 and 13/27 of the tasks with a check.
- **The E4B's non-pytest checks in the draws:** 4, all scripts, on 2 task-draws.
  - rich_3105 in EXP-038: exit 1 (L), then exit 0.
  - fastapi_15661 in EXP-075: exit 0 twice.
  - Their sources were not found, so exercises is `unknown`.

### 5.2 Q2: the next action after a non-zero check (E4B draws, all forms; 107 checks)
| Set | S | R | K | E | D | T | N |
|---|---|---|---|---|---|---|---|
| All 107 | 80 | 0 | 3 | 16 | 7 | 0 | 1 |
| EXP-038 | 15 | | 2 | 1 | | | |
| EXP-077 | 16 | | | 5 | 3 | | |
| EXP-075 | 27 | | 1 | 5 | 2 | | |
| EXP-078 | 22 | | | 5 | 2 | | 1 |
| by class: X (2) | | | | 1 | | | 1 |
| U (15) | 11 | | 3 | | 1 | | |
| M-env (41) | 39 | | | 1 | 1 | | |
| L (18) | 6 | | | 10 | 2 | | |
| C (9) | 9 | | | | | | |
| F (22) | 15 | | | 4 | 3 | | |

- **Shares:**
  - submit next 80/107 (0.748);
  - identical rerun or another check 3/107 (0.028);
  - edit next 16/107 (0.150).
- **The L row includes one non-pytest check** (rich_3105's script), so L is 18 here against 17 pytest L in section 5.1.
- **Next action E is not e3.** E counts any edit attempt as the next call, successful or not. e3 counts a successful change later than the run's last failed check, which is 1, 1, 2 and 0 tasks per draw. So most of the 10 edits after an L check did not leave a successful change after the run's last failed check [I].
- **The E4B treats the check by its class [I].** It edits after 10 of 18 linked failures and submits after 39 of 41 missing-module failures. The base prompt says to do exactly that: its section 4 says to ignore import errors and pre-existing breakage, and to submit even when the check is red.

### 5.3 Q3: arm R (EXP-028-armR)
- **Checks:** 50 on 21 tasks, `python -c` 32 and scripts 18; exit 0 34, exit 1 16.
- **Exercises the changed code** (section 2.4): y 30, n 18, unknown 2 of 50.

  | Subset | y | n | unknown |
  |---|---|---|---|
  | exit 0 (34) | 19 | 13 | 2 |
  | non-zero (16) | 11 | 5 | |
  | `python -c` (32) | 19 | 13 | |
  | scripts (18) | 11 | 5 | 2 |

- **Its 16 non-zero checks (12 tasks):**
  - classes L 2 and F 14, so noise 0.000;
  - next action K 9, D 5, E 2, and never a submit;
  - e3, fixed after a failure: 3/12 tasks.

### 5.4 Q4: python-form commands in the E4B runs on disk (27 runs)
| Run (tasks) | Python-form cmds (tasks) | Checks | `python -c` after a change, tasks | Forms | Exits |
|---|---|---|---|---|---|
| EXP-038 (48) | 2 (1) | 2 | 0 | script 2 | 0:1 1:1 |
| EXP-045-p (8) | 8 (6) | 8 | 3 | `python -c` 3, script 5 | 0:2 1:2 2:4 |
| EXP-046-team (8) | 9 (6) | 8 | 5 | `python -c` 9 | 0:3 1:6 |
| EXP-056-r1 (8) | 1 (1) | 1 | 1 | `python -c` 1 | 0:1 |
| EXP-056-r2 (8) | 3 (3) | 3 | 0 | script 3 | 1:2 2:1 |
| EXP-063-p (8) | 1 (1) | 1 | 0 | script 1 | 2:1 |
| EXP-066-srch (8) | 2 (1) | 2 | 1 | `python -c` 2 | 1:2 |
| EXP-068-read (8) | 1 (1) | 1 | 1 | `python -c` 1 | 0:1 |
| EXP-075-t02 (48) | 2 (1) | 2 | 0 | script 2 | 0:2 |
| the other 18 runs | 0 | 0 | 0 | | |

- **Pooled over all 27 runs:**
  - python-form commands 29 on 21 task-runs, 28 of them checks;
  - of the checks, exit 0 9; the non-zero ones are U 6, M-repo 2, L 3, C 1, F 7;
  - exercises y 17, n 1, unknown 10.
- **EXP-045-p scripts:** an earlier `write_file` of the script path was refused on 2 script checks. Both exited 2, class U. Two more script checks exited 2, class U, with no earlier write of the path found.
- **The four dev-48 draws:** 4 python-form commands on 2 of 192 task-draws, all scripts. There is **no `python -c` command at all** in the single loop, although its check line already offers that form.

## 6. Decision (section 3 as written): NOT BUILT
| Part | Rule | Measured | Holds |
|---|---|---|---|
| B1 | noise share 0.50 or more, and lower-bound signal 0.25 or less | noise 0.632, lower bound 0.160 | yes |
| B2(a) | in a run whose prompt directs a python command, `python -c` after a change on 4 or more of 8 tasks | EXP-046-team 5 of 8: its check stage's prompt (`experiments/EXP-046/candidate-team/prompts/check.md`) directs a `python3 -c` import-and-call check. EXP-045-p 3 of 8: its prompt directed a script written to `/tmp`. | yes, on EXP-046-team |
| B2(b) | over the E4B python-form checks on disk (28, so it is read), exit 0 share 0.40 or more, and M-repo 0.25 or less of the non-zero ones | exit 0 9/28 = 0.321; M-repo 2/19 | **no**: the exit 0 clause fails, the M-repo clause holds |

**B2 fails on B2(b)'s exit 0 clause, so the arm is not built.** As section 3 requires, these are not written:
- the arm design and readings;
- the candidate tree, zip and notebooks.

0 GPU-h.

**What the decision does and does not say.** Corrected in the commit after 4a12dd6 (defect 7). The lead should read the decision with these points beside it.
- **Neither of the dispatch's two do-not-build conditions is what fired.**
  - The failed pytest checks mostly carry no signal (B1 holds).
  - A path for the form exists: python -c after a change on 5 of 8 in EXP-046-team. All 8 of that run's python -c checks were made by its check stage (step author `check`), whose prompt directs the form.
- **B2(b)'s exit 0 clause did catch the form failing on this model.** It was meant to show that the form runs; it cannot by itself separate a broken snippet from a wrong change. The post hoc exception count separates them for the python -c checks:
  - python -c checks alone: 15, exit 0 5 (0.333).
  - Of the 10 non-zero ones, the last exception name in the output is SyntaxError on 7: 6 in class F (no changed file named, so the error is in the -c code itself) and 1 in class L (a changed file named). The other 3 are ImportError on 2 (1 C, 1 L) and TypeError on 1 (F).
  - So **6 of the 15 python -c checks were snippets that did not compile**. That is a failure of the form for the E4B, which is what B2(b) was written to catch. Why the snippets did not compile (quoting of a multi-line snippet inside one command string, for example) is not counted here [I].
  - "Exercises y" (14 of 15) is a text match on the command. It shows that the snippet names the changed code, not that the code ran.
  - The repo was importable where the checks ran: M-repo 2 of 19, both skill-tree scripts (EXP-056-r2).
  - Post hoc, on the task unit: the last python -c check passed on 5 of 11 task-runs (0.455). Those 11 task-runs come from 5 smoke-8 runs (EXP-045-p 3, EXP-046-team 5, and one each from EXP-056-r1, EXP-066-srch and EXP-068-read) over 7 distinct ids. That is too few to set beside the rule's line, and the rule reads checks, not task-runs.
- **The step the arm would take is untested.** That step is removing the pytest option from the single loop's check line.
  - The single loop emits no python -c while pytest is offered (0 of 192 task-draws).
  - The measured uptake comes from a dedicated check stage in a Sequential team (EXP-046) and from smoke-8 pipeline stages, not from the single loop.
- **Re-dispatch is the lead's call.** A re-dispatch would also have to meet the snippet-compile failure: 6 of 15 python -c checks did not compile.

**Contradicted predictions (section 4), stated plainly:**
- **Q2 missed.** Submit next was 0.748, not about half. Rerun or another check was 0.028, not about a quarter. Edit was 0.150, close to the predicted 0.1.
- **Q3 missed.** "Arm R edits more often after a failure" is contradicted: arm R's next actions were K 9, D 5 and E 2, against the E4B's E 16 of 107. Arm R does not submit after a failure; it runs another check or reads. Exercises was 30 of 50, against the predicted about 0.7.
- **Q4 partly missed.**
  - Python-form commands in the dev-48 draws: 2 of 192 task-draws, which landed (fewer than 1 in 10).
  - EXP-045-p by this file's rules gives `python -c` after a change on 3 of 8, not 6 of 8. Its 6 counts python-form commands of any form; scripts were 5 of its 8 commands.
  - The exit 0 share was 0.321, not about 0.5.
- **Decision missed.** The prediction was build; the rule reads not built.
- **Landed:** Q1, noise 0.632 (predicted about 0.6), L 0.160 (0.1 to 0.2), M-own 0. F was 22 of 106, against the predicted 0.2 to 0.3.

**B1's margin (post hoc).** C includes 9 exit 1 checks, matched by text (`ImportError`, `conftest` and the like). With those 9 moved to signal, the lower bound is 0.245 and noise 0.547, so B1 still holds. B1 does not hinge on that text match.

## 7. Defects
1. **B2(b)'s exit 0 clause cannot by itself separate a broken snippet from a wrong change.** Both exit non-zero. The post hoc exception count in section 6 shows that on the python -c checks most non-zero exits were snippets that did not compile (6 of 10), so the clause read the form's failure, as intended. (Corrected: 4a12dd6 said the clause mixed runnability with correctness and that the python -c checks failed with real failures; the counts do not support that.)
   - The rule also pools forms the arm would not use: scripts whose `/tmp` write was refused, and skill-tree scripts. It reads checks, not task-runs.
   - Not revised. The post hoc figures in section 6 sit beside it.
2. **Post hoc lines were added to `desk.py` after the first read.** These are the `python -c`-only share, the task-unit last-pass share (with its runs and distinct ids), the exception names and step authors of the python -c checks, B1's margin, the Q2 shares, and the missing-module names. They sit in a block headed "Post hoc", and the decision rule's output above that block is unchanged.
3. **M-repo reads a `src/` layout as a top-level package.** The rule says a top-level package dir or module of the repo snapshot. `desk.py` also counts `src/<pkg>`, the layout requests uses. This is a clarification in the implementation, not a change of rule. M-repo is 0 in Q1 and 2 in Q4, both from skill-tree scripts.
4. **The exercises code is `unknown` for 10 of 28 E4B python-form checks**, and for 2 of arm R's 50. The script path's source was not found by the `write_file` or `cat >`/`tee` rule. Examples are a heredoc piped to the interpreter, or a script that already sat in the repo. This does not touch the decision.
5. **The noise share depends on the C class's text rule.** It is bounded by the B1 margin line in section 6.
6. **B2(a) was met by a run that section 3 did not name.** Section 3 named EXP-045-p as the known candidate; it reads 3 of 8 by this file's rules and misses. EXP-046-team (5 of 8) was found to qualify, under "a run whose prompt directs a python command", by reading its `prompts/check.md` after the counts were seen. Its python -c checks are by the check stage (step author printed post hoc). The qualifying run is a Sequential team's check stage, not the single loop.
7. **Correction commit after 4a12dd6.** Section 6's commentary and defect 1 claimed that the python -c checks reached the change and failed with real failures. The post hoc exception and author lines were added to `desk.py`, and the commentary was rewritten from them. F is ambiguous by section 2.2, and "exercises" is a text match. The decision and every count above the post hoc block are unchanged.

## Status
**DESK CHECK COMPLETE 2026-11-12; the arm is NOT BUILT (B2(b) fails on its exit 0 clause, 0.321 against 0.40), 0 GPU-h.** There is no tree, zip, notebook or kernel, and no blind threshold, because no arm was pre-registered. Of the E4B's 15 python -c checks on disk, 6 did not compile (post hoc). Re-dispatch is the lead's call.
