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
To be appended after `desk.py` runs.
