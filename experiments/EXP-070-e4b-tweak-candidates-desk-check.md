# EXP-070: desk checks for the E4B pipeline tweak candidates

**Date:** 2026-11-11
**Type:** zero-GPU analysis (L0 desk check and L1 trace mining), 0 L4x4-h
**Cohort:** none (the 56 task-runs of EXP-061-r, EXP-062-r, EXP-063-p, EXP-064-loc, EXP-066-srch, EXP-068-read and EXP-069-argform, 8 smoke-8 ids each)
**Ladder:** L0 and L1, ahead of the five E4B tweak rounds the user approved on 2026-11-11 (`knowledge/user-decisions.md`). Nothing here is designed, built or pushed; EXP-071 onward stay free for the rounds.
**Pre-registered:** no. The checks were asked for by the lead, and the counts were computed before this file was written. The definitions in section 2 are those of the scripts that produced the counts, and section 4 holds decision rules written after the counts were seen; they carry no prediction weight. Section 7 lists what was seen, and in what order.
**Serves:** the 2026-11-11 tweak batch (D-008 and D-009 branches); C-019 (an executed verify step) and C-021 (vendoring the two test-only packages).
**Supersedes / relates:** EXP-063 (`refs.py`, whose draft parser and exit-code reader are reused here), EXP-065 (the text-form counter in `tools/analyze_traces.py`), EXP-067 (edit-failure chain diff), EXP-036 and EXP-038 (the shim re-grade pattern). The window-miss question of EXP-068 and the EXP-069 reading are the screener's job and are not touched here. EXP-069-argform is read only.

## 1. Why this, now (zero GPU)

The user approved five more smoke-8 rounds on the E4B pipeline tree (about 2.0 GPU-h, ceiling 2.5). EXP-063 and EXP-069 both ended "not exercised": their trigger never occurred in 8 sessions. Each candidate tweak therefore needs a reference rate, the number of times its trigger occurs per 8 task-runs in the runs we already have, before a round is spent on it. The lead asked for five checks:

1. the reader's empty-report fault;
2. an executed verify step after the applier's last applied edit (C-019);
3. draft diversity, which decides between a diversity form and a selection form;
4. vendoring (C-021);
5. wall-clock and call headroom for an added verify run.

## 2. Data and definitions

**Data.** The seven local pipeline runs under `runs/` (task_results, official traces). EXP-069 is read from its nested download path. The wall and call figures in check 5 come from each run's committed `summary.jsonl` (`tools/analyze_traces.py`). Everything else comes from two scripts in `experiments/EXP-070/`, which print ids, counts, draft numbers, program names, path arguments and exit codes only.

**Pass.** One run of the pipeline inside a task. A pass starts at a reader step that follows a non-reader step. All tasks have 1 pass, except EXP-068 rich_3006, which has 2. That gives 57 passes over 56 task-runs.

**Check 1, reader class per pass.** Taken from the reader's last final or text turn that has no tool call:
- `ok`: a FILE line naming a path;
- `unknown`: the line reads `FILE: unknown`;
- `jsoncall`: no FILE line, and the turn holds a call-shaped JSON value (`analyze_traces.has_text_form_call`);
- `nofile`: no FILE line, other text;
- `nofinal`: the pass has no such turn.

The script also records the reader's tool calls in the pass.

**Check 2, verify.** Taken from the applier's tool calls of the task, in order. The window runs from just after the last applied `edit_file` up to the next `submit_patch`. A check is any `run_command` in that window with a pytest, python or python3 segment. Commands are split on `&&`, `||`, `;` and `|`. Leading `VAR=value`, `timeout N`, `env`, `time` and `nice` words are dropped. The full sequence of function and program names in each window is printed, so that "none" can be checked by eye. Each check gets a class and its exit code (via `refs.exit_code`):
- `mod`: a path whose name contains `test` and the edited file's stem as a whole `_`-separated word;
- `file`: another path;
- `suite`: no path, or a directory;
- `c`: python -c.

**Check 3, drafts.** Usable drafts per pass: drafter_1..5 finals that `refs.parse_draft` turns into (FILE, OLD, NEW). Distinct drafts are counted after whitespace normalization (runs collapsed, ends stripped), comparing FILE by its last path part. The task's first applied edit is put in exactly one class. Draft FILE must be a suffix of the edit's filepath, and OLD and NEW are compared after the same normalization:
- `exact1`: OLD and NEW both equal draft_1's;
- `exact_other`: both equal another draft's, but not draft_1's;
- `old_only`: OLD equals a draft's OLD, NEW differs;
- `new_only`: the converse;
- `own`: there are usable drafts, but the edit matches none of them;
- `nodrafts`: the pass has no usable draft.

Per pass the script also records the size of the largest identical group and whether a strict majority of the usable drafts is identical. Over passes with 2 or more distinct drafts and a first applied edit, it gives a vote class: `nosignal` (the largest group is 1, all drafts differ), `tie` (two or more largest groups of 2 or more), `same` (one largest group of 2 or more, and draft_1 is in it), `diff` (one largest group of 2 or more without draft_1, an unusable draft_1 included). `same` means a majority-vote selector would pick the same edit text as draft_1.

**Check 4a.** A run_command step whose observation has ModuleNotFoundError or ImportError followed within 120 characters by `inline_snapshot` or `dirty_equals`. The script prints the step's author, its programs, its exit code, and whether it comes after (A) or before (B) the last applied edit. It also checks whether the grading `test_tail` holds the same pattern. The tail is the last 1500 characters of the grading output, so the tail count is a lower bound.

**Check 5.** From `summary.jsonl`: mean and max `wall_s`, and max `n_calls`. `n_calls` is 1 to 4 higher than the harness `tool_calls` (1 on every max row; on 46 of 56 rows the gap equals the `transfer_to_agent` count). The harness enforces its cap on its own count, so headroom read from `n_calls` is conservative. The script also reports the applier's counted calls per task (all calls but `get_status` and `submit_patch`). Headroom is the cap minus the max wall. Caps in all seven runs: 8 min (480 s) and 45 calls, from task_results.

## 3. Endpoints (counts)

The endpoints are the per-run counts of section 8.1. No outcome or resolve claim is made.

## 4. Decision rules (written after the counts; not blind)

For each check, a tweak is a candidate for one of the five rounds only if all three hold:
- (a) its trigger occurs on at least 2 task-runs per 8, averaged over the seven runs. Below that, a smoke-8 round is likely to be "not exercised", as EXP-063 and EXP-069 were.
- (b) a process endpoint can be counted from a smoke-8 trace with the tools we have;
- (c) it fits the wall and call headroom of check 5.

A check that fails (a) can still ride free inside another round, as long as it touches a different prompt.

## 5. What this does and does not license

It licenses:
- reference rates for the batch's round designs;
- the statement that the shim re-grade cannot be run on this machine.

It does not license:
- any resolve or LB claim;
- any claim that a verify step, a selection form or vendoring would fix a task;
- any design, build or push.

## 6. Exact commands

```
python -I -X utf8 experiments/EXP-070/desk.py runs/EXP-061-r runs/EXP-062-r runs/EXP-063-p runs/EXP-064-loc runs/EXP-066-srch runs/EXP-068-read runs/EXP-069-argform > out/exp070_desk.txt
python -I -X utf8 experiments/EXP-070/mnf.py  runs/EXP-061-r runs/EXP-062-r runs/EXP-063-p runs/EXP-064-loc runs/EXP-066-srch runs/EXP-068-read runs/EXP-069-argform > out/exp070_mnf.txt
python -I -X utf8 -c "import swegemma"     # ModuleNotFoundError on this machine (check 4b)
```

Each `RUN counts` line of `desk.py` gives the per-run tallies. Wall and calls come from `experiments/{EXP-061,EXP-062,EXP-063/p,EXP-064/loc,EXP-066/srch,EXP-068/read,EXP-069/argform}/summary.jsonl`.

## 7. What was seen, and when (logged after the fact)

1. The first `desk.py` pass printed per-task lines for all seven runs before any rule in section 4 existed.
2. Two definitions changed after that pass, before this file was written:
   - The `mod` test was a plain substring test. It counted the absent reproducer file of EXP-063 as the edited module's test, because one stem is a prefix of a word in that name. It became the whole-word test of section 2.
   - The first-applied match was "OLD equal or NEW equal". That counts every draft sharing a location as a hit, so it became the exclusive classes of section 2. The earlier "matches draft 1" figure overstated draft_1. It is not used.
3. Check 2 split commands only on their first word at first. Segment splitting and the window dump were added. Neither changed any task's "none".
4. The call maxima at first came from the harness `tool_calls`. They were replaced by `summary.jsonl` `n_calls`, the tool's figure, which is 1 higher on every max row.
5. After the first draft of this file, at the advisor's review, four counters were added to `desk.py` and every figure was re-read from them: the largest-group and vote classes of check 3; the `file`, `c` and ran (exit 0 or 1) tallies of check 2, which had been hand counts, one of them wrong (5 for 6) in that draft; and `ok` passes with 0 reader calls. The check 3 and check 2 lines of 8.2 and the Status were rewritten from these counts.

## 8. Results

### 8.1 Counts per run

Check 1. Reader class per pass. Each non-ok pass is listed with its class and reader calls.

| run | passes | not ok | non-ok passes | empty patch after a non-ok pass |
|---|---|---|---|---|
| EXP-061-r | 8 | 0 | - | - |
| EXP-062-r | 8 | 1 | fastapi_14301 jsoncall, 0 calls | no |
| EXP-063-p | 8 | 0 | - | - |
| EXP-064-loc | 8 | 0 | - | - |
| EXP-066-srch | 8 | 0 | - | - |
| EXP-068-read | 9 | 2 | requests_7309 jsoncall, 0 calls; rich_3006 pass 2 nofile, 0 calls | no |
| EXP-069-argform | 8 | 0 | - | - |
| all | 57 | 3 | 3 non-ok passes, each with 0 reader calls | 0 of 3 |

What followed each non-ok pass:
- **EXP-062 fastapi_14301.** All 5 drafter finals were unusable (0 usable). The applier then composed and applied 1 edit of its own after 5 counted calls (`nodrafts`). It ran a suite pytest, which exited 2 (check 4). The patch was non-empty; unresolved.
- **EXP-068 requests_7309.** 0 of 5 drafts usable. The applier applied 1 edit of its own after 6 counted calls, then ran a python -c check that exited 0. Unresolved. This task never resolves on this grader, gold or empty (harness-stack).
- **EXP-068 rich_3006, pass 2.** 0 of 5 drafts usable, and the applier made no edit in that pass. The task's patch is non-empty only because pass 1's applied edit stands. Unresolved, while rich_3006 resolved in the other six runs; pass 1's first applied edit was `own`.

No reader pass is `unknown` or `nofinal`. No non-ok pass ended in an empty patch. No `ok` pass has 0 reader calls, so the text-only reader sessions (no tool call at all) are exactly the 3 non-ok passes.

Check 2. Checks after the last applied edit, by task-run and by resolved and unresolved.

| run | task-runs with an applied edit | check, resolved | check, unresolved | none, resolved | none, unresolved | any check exit 0 |
|---|---|---|---|---|---|---|
| EXP-061-r | 6 | 1 | 2 | 0 | 3 | 0 |
| EXP-062-r | 7 | 1 | 2 | 0 | 4 | 0 |
| EXP-063-p (prompted reproducer runs) | 6 | 1 | 4 | 0 | 1 | 0 |
| EXP-064-loc | 7 | 0 | 0 | 2 | 5 | 0 |
| EXP-066-srch | 7 | 1 | 1 | 1 | 4 | 0 |
| EXP-068-read | 7 | 1 | 3 | 0 | 3 | 1 |
| EXP-069-argform | 8 | 0 | 3 | 2 | 3 | 0 |
| all but EXP-063 | 42 | 4 | 11 | 5 | 22 | 1 |

All six EXP-063 checks target the absent reproducer file the EXP-063 prompt names (exit 4 five times, exit 2 once). They are prompt-induced, so they are kept out of the unprompted total.

The 15 unprompted task-runs with a check break down as follows:

| class | task-runs | exit codes | what it targeted |
|---|---|---|---|
| suite | 8 | 1, 1, 1, 1 (four rich and requests runs); 2, 2, 2 (three fastapi runs, each at collection on the missing packages, check 4); 5 (rich_3468 in EXP-069, no tests collected) | whole suite or a directory |
| file | 3 | 2 each | the edited source module itself, not a test file: requests_7309 in EXP-062 and EXP-069, requests_7205 in EXP-068 |
| mod | 2 | 4 each | a test file named for the edited module that does not exist (usage error): EXP-061 fastapi_14448, EXP-062 rich_3006 |
| c | 2 | 1, 1 (EXP-066 requests_7309); 0 (EXP-068 requests_7309) | python -c |

- In the 4 resolved task-runs with a check, the check exited 1, 4, 1 and 2; the applier submitted after each of them.
- The only exit 0 anywhere is a python -c on a task that never resolves on this grader.
- No unprompted check ran an existing test file of the edited module.
- In 6 of 15 task-runs (the four exit-1 suite runs and both c runs), tests or code ran (exit 0 or 1). The class counters over the six unprompted runs: suite 8, file 3, mod 2, c 2, ran 6.
- Every "none" window holds only edit_file, read_file or get_status calls, or nothing. No pytest is hidden behind a prefix.

Check 3. Draft diversity per pass, and the class of the first applied edit.

| run | passes with usable drafts | all identical (1 distinct) | 2 distinct | 3 to 5 distinct | first applied edits | exact1 | exact_other | old_only | new_only | own | nodrafts | exact1 where the pass had 2+ distinct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EXP-061-r | 8 | 0 | 2 | 6 | 6 | 5 | 0 | 1 | 0 | 0 | 0 | 5 of 6 |
| EXP-062-r | 7 | 1 | 4 | 2 | 7 | 4 | 0 | 1 | 1 | 0 | 1 | 3 of 5 |
| EXP-063-p | 8 | 0 | 4 | 4 | 6 | 5 | 1 | 0 | 0 | 0 | 0 | 5 of 6 |
| EXP-064-loc | 8 | 0 | 2 | 6 | 7 | 5 | 1 | 1 | 0 | 0 | 0 | 5 of 7 |
| EXP-066-srch | 8 | 0 | 4 | 4 | 7 | 5 | 0 | 1 | 0 | 1 | 0 | 5 of 7 |
| EXP-068-read | 6 | 1 | 1 | 4 | 7 | 2 | 0 | 0 | 0 | 3 | 2 | 1 of 4 |
| EXP-069-argform | 8 | 3 | 2 | 3 | 8 | 4 | 1 | 3 | 0 | 0 | 0 | 3 of 5 |
| all | 53 | 5 | 19 | 29 | 48 | 30 | 3 | 7 | 1 | 4 | 3 | 27 of 40 |

- 24 of 53 passes with usable drafts have 2 or fewer distinct drafts, and 29 have 3 or more. A strict majority of the usable drafts is identical in 23 of 53.
- Where the drafts differ (2 or more distinct) and an edit was applied, the first applied edit is exactly draft_1 in 27 of 40.
- Over all 45 first applied edits with usable drafts, it is exactly draft_1 in 30 and another draft in 3.
- EXP-068, whose drafters read the file themselves, is the outlier: 3 `own` and 2 `nodrafts` of 7.

Vote classes over passes with 2 or more distinct drafts and a first applied edit:

| run | such passes | strict-majority passes (of all usable) | same | diff | tie | nosignal |
|---|---|---|---|---|---|---|
| EXP-061-r | 6 | 2 of 8 | 2 | 1 | 0 | 3 |
| EXP-062-r | 5 | 5 of 7 | 3 | 0 | 0 | 2 |
| EXP-063-p | 6 | 4 of 8 | 2 | 1 | 0 | 3 |
| EXP-064-loc | 7 | 2 of 8 | 2 | 0 | 0 | 5 |
| EXP-066-srch | 7 | 3 of 8 | 4 | 0 | 0 | 3 |
| EXP-068-read | 4 | 2 of 6 | 1 | 0 | 0 | 3 |
| EXP-069-argform | 5 | 5 of 8 | 3 | 0 | 0 | 2 |
| all | 40 | 23 of 53 | 17 | 2 | 0 | 21 |
| EXP-064 tree (064, 066, 068, 069) | 23 | 12 of 30 | 10 | 0 | 0 | 13 |

The EXP-064 tree, with its location-diverse drafters, is the base of the batch. In it, 13 of 30 passes with usable drafts have 2 or fewer distinct drafts (4 all identical, 9 with 2), 17 have 3 or more, and the first applied edit is exactly draft_1 in 14 of 23 multi-draft passes.

Check 4a. ModuleNotFoundError or ImportError naming inline_snapshot or dirty_equals.

| run | run_command hits (task-runs) | where | grading tail names a package |
|---|---|---|---|
| EXP-061-r | 0 | - | 0 |
| EXP-062-r | 2 | fastapi_14301 applier pytest exit 2 (A, the verify run); fastapi_14448 applier pytest exit 2 (B) | 0 |
| EXP-063-p | 0 | - | 0 |
| EXP-064-loc | 0 | - | 0 |
| EXP-066-srch | 0 | - | 0 |
| EXP-068-read | 1 | fastapi_14301 applier pytest exit 2 (A, the verify run; resolved) | 1 (fastapi_14605) |
| EXP-069-argform | 1 | fastapi_14448 applier pytest exit 2 (A, the verify run) | 0 |
| all | 4 of 56 | all fastapi, all the applier, all both packages; 3 of 4 are the verify run | 1 of 56 (lower bound) |

Grading of fastapi_14605 exited 2 in 7 of 7 runs. Its tail is cut at 1500 characters, and the package line falls inside the tail only in EXP-068. So the cause of the other six exit-2 gradings cannot be seen here.

Check 4b. `tools/regrade_patches.py` imports `swegemma`, and importing it on this machine gives ModuleNotFoundError. The re-grade with `tools/compat_shims` needs a Kaggle CPU kernel, the EXP-036 and EXP-038 pattern recorded in harness-stack:
- builder `experiments/EXP-036/build_regrade_notebook.py`;
- `--exp-id EXP-NNN-regrade --passes <ARM>,GOLD,BASE`;
- `--timeout 240 --verification-timeout 300`;
- CPU-only metadata copied from `notebooks/exp036_regrade/`.

Stopped there, as instructed. The re-grade of EXP-064-loc and EXP-068-read was not run, and no flips are reported.

Check 5. Wall and call headroom against the 480 s and 45-call caps (summary.jsonl).

| run | mean wall s | max wall s | headroom to 480 s | max n_calls (task) | calls left to 45 | max applier counted calls | time or call caps hit |
|---|---|---|---|---|---|---|---|
| EXP-061-r | 89.46 | 165.1 | 314.9 | 9 (httpx_3672) | 36 | 4 | 0 |
| EXP-062-r | 89.25 | 169.6 | 310.4 | 16 (rich_3468) | 29 | 9 | 0 |
| EXP-063-p | 119.47 | 164.0 | 316.0 | 19 (rich_3468) | 26 | 8 | 0 |
| EXP-064-loc | 99.99 | 208.6 | 271.4 | 19 (rich_3468) | 26 | 10 | 0 |
| EXP-066-srch | 99.81 | 157.6 | 322.4 | 18 (rich_3468) | 27 | 11 | 0 |
| EXP-068-read | 110.33 | 203.9 | 276.1 | 21 (rich_3468) | 24 | 9 | 0 |
| EXP-069-argform | 97.70 | 201.8 | 278.2 | 23 (httpx_3672) | 22 | 14 | 0 |

The smallest headroom is 271.4 s and 22 calls. A verify run of 20 to 40 s and 1 to 2 calls fits every observed task-run, with at least 231 s and 20 calls to spare. This holds on smoke-8 only; the 8-minute cap is the tree's, not the shipped 4.5.

### 8.2 One line per check (rules of section 4)

1. **Reader empty report.** Trigger rate: 3 of 57 passes, about 0.4 per 8. It fails rule (a), so it is not a candidate for its own round. It could ride free, with this process endpoint: non-ok reader passes and the usable drafts that follow them (reference 3 passes, all with 0 reader calls and 0 usable drafts).
2. **Executed verify (C-019).** Unprompted checks occur on 15 of the 48 task-runs of the six unprompted runs (15 of 42 edited), about 2.5 per 8 task-runs. Tests or code ran on only 6 (1.0 per 8), and none passed on a resolved task. So the candidate is "make the check runnable", not "add a check". Its trigger is any applied edit: 42 of 48, 7.0 per 8. Process endpoints:
   - edited task-runs with a check after the last applied edit that runs (exit 0 or 1, with no exit 2, 4 or 5): reference 6 of 48;
   - checks of class `mod` on an existing file: reference 0.

   It passes rules (a) to (c), with the caveat that fastapi suite runs die at collection (check 4).
3. **Draft diversity.** Mixed: the drafts are neither mostly identical nor uniformly different. The split depends on the form.
   - **Majority-vote selection is not a candidate.** It would change the applier's pick in 2 of 40 multi-draft passes (diff), 0 of 23 in the EXP-064 tree. Where draft_1 sits in a plurality group (same, 17), a vote picks the same text. In the 21 all-distinct passes (nosignal), a vote has nothing to go on.
   - **Selection by a non-vote signal, such as a check per draft,** has a trigger on 21 of 56 task-runs (13 of 32 in the EXP-064 tree, about 3.3 per 8). It needs a check that runs, so it depends on check 2's tweak landing first.
   - **A diversity form** has a trigger, a pass with 2 or fewer distinct drafts, on 13 of 32 task-runs in the EXP-064 tree, about 3.3 per 8. Process endpoint: distinct drafts per pass (EXP-064 tree reference 17 of 30 passes with 3 or more), and the first applied edit's class.
   - Both forms pass rules (a) to (c) on rate alone. A smoke-8 trace cannot show that a different draft or a different pick is a better one.
4. **Vendoring (C-021).** Trigger rate: 4 of 56 task-runs, about 0.6 per 8, all fastapi. It fails rule (a) alone. It is linked to check 2: 3 of the 4 hits are the verify run itself, so it could ride with a verify round as an enabler. Process endpoint: package ModuleNotFoundError hits in run_command (reference 4 of 56). The grading question (fastapi_14605 grades exit 2 in 7 of 7 runs) needs the Kaggle CPU re-grade kernel. It cannot be settled here.
5. **Headroom.** Not a tweak. It is a constraint, and it is met: at least 271.4 s and 22 calls of room on every run, against an added 20 to 40 s and 1 to 2 calls. Process endpoint for any verify round: mean wall within +40 s of its base run, and 0 caps.

## Status

**2026-11-11 COUNTED.** Zero GPU.
- The trigger rates per 8 task-runs:
  - reader non-ok passes 0.4;
  - unprompted verify checks 2.5, of which 1.0 ran tests or code;
  - a majority vote that would change the pick 0.3 (0 in the EXP-064 tree);
  - all-distinct multi-draft passes 3.0;
  - passes with 2 or fewer distinct drafts in the EXP-064 tree 3.3;
  - package ModuleNotFoundError 0.6.
- Candidates by section 4: a runnable-verify form first. Then either a draft-diversity form, or a selection form whose signal is a per-draft check, which depends on the runnable verify landing. Majority-vote selection is not a candidate. The reader fault and vendoring can only ride free; vendoring is the enabler for fastapi checks.
- The shim re-grade needs a Kaggle CPU kernel and was not run.
