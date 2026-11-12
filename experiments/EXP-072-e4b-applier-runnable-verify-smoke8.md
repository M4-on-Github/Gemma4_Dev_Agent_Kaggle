# EXP-072 — The applier runs the edited module's test file before and after its edit, and undoes only on a new failure (smoke-8 screen, D-010 round 2)

**Date:** 2026-11-11
**Type:** smoke-8 screen, ~0.45 L4x4-h (EXP-064 smoke-8 0.353 GPU-h at a kernel wall of about 1260 s; the recipe adds up to 4 applier calls per task, about 25 to 40 s, so about 1580 s). One push, no upload, no dev-48.
**Cohort:** smoke-8
**Base tree:** `experiments/EXP-064/candidate-loc` (copied whole; not stacked on EXP-066, EXP-068, EXP-069 or EXP-071).
**Ladder:** L2. L0 and L1 are EXP-070 check 2 (the unprompted check after the last applied edit, zero GPU) and section 1 below (which pipe-free command finds a test file of the edited module on the smoke-8 snapshots, zero GPU).
**Pre-registered:** this file is committed before the push. Sections 3-5 are written blind and are not revised.
**Serves:** D-010 round 2 of the five E4B pipeline tweak rounds (`knowledge/directions/D-010-e4b-five-tweak-rounds.md`); C-019 (an executed verify step). Takes in the four EXP-072 flags of the critic's D-010 review (`experiments/EXP-070/critic.md`, "EXP-072: flags", commit 3d0fc69).
**Relates:** EXP-070 (the desk counts this design answers), EXP-066 (the pipe lesson: 12 of 12 pipe-free searches had no malformed-argument error, 7 of 9 piped ones had, all of those a detached `head` count), EXP-064 (the base tree and the reference run `runs/EXP-064-loc`), EXP-069 (same base, the applier's argument form; its hunks are not in this tree), EXP-071 (round 1, on another base, running at the same time).

## 1. Why this, now (zero GPU)

**1.1 What the applier does today (EXP-070 check 2).** Over the 48 task-runs of the six unprompted E4B pipeline runs, a check followed the last applied edit on 15 (2.5 per 8). 6 of those ran at all (exit 0 or 1; 1.0 per 8), and **0 ran an existing test file of the edited module** (EXP-070's `mod` class: a test file whose name holds the edited file's stem as a whole `_`-separated word). The rest were the whole suite (8, exit 2 at collection on the fastapi tasks), the edited source module given to pytest (3, exit 2), a test file named for the module that does not exist (2, exit 4) and `python -c` (2). All 4 resolved task-runs that had a check exited non-zero. In the base run, EXP-064-loc, no applied edit was followed by a check. So the candidate is "make the check runnable", not "add a check".

**1.2 Which command finds the test file (desk check, `experiments/EXP-072/desk.py`).** The script reads each smoke-8 task's repository snapshot (`data/local/snapshots/<id>.tgz`, read as data, never extracted) and, for each source file an E4B applier edited in EXP-061-r, 062-r, 064-loc, 066-srch, 068-read or 069-argform plus the gold patch's files, simulates two pipe-free commands:
- **dot:** `git grep -l -F 'pkg.sub.mod' -- tests` (the dotted import path, with a `src/` prefix dropped; the lead's example form);
- **name:** `git ls-files -- 'tests/*STEM*'` (git's default pathspec glob, where `*` also matches `/`; STEM the file name without `.py` and a leading `_`).

For each form it takes the first sorted printed path named `test_*.py`. On the 8 files EXP-064-loc's applier actually edited (7 tasks; rich_3468 had no applied edit):

| task | file EXP-064-loc edited | dot pick | name pick |
|---|---|---|---|
| fastapi_14301 | `fastapi/dependencies/utils.py` | a test file that imports it, not `mod`, not graded | none |
| fastapi_14448 | `fastapi/routing.py` | a test file that imports it, not `mod`, not graded | none |
| fastapi_14605 | `fastapi/utils.py` | none | none |
| httpx_3672 | `src/httpx/_parsers.py` | none | `tests/test_parsers.py` (`mod`, graded) |
| httpx_3672 | `src/httpx/_server.py` | none | none |
| requests_7205 | `src/requests/utils.py` | `tests/test_requests.py` (not `mod`, not graded) | `tests/test_utils.py` (`mod`, graded) |
| requests_7309 | `src/requests/utils.py` | `tests/test_requests.py` (not `mod`, not graded) | `tests/test_utils.py` (`mod`, graded) |
| rich_3006 | `rich/repr.py` | `tests/test_repr.py` (`mod`, graded) | `tests/test_repr.py` (`mod`, graded) |

Over all 24 modules in the script's output (the edited files of six runs plus the gold files), the name form picks a `test_*.py` for 13 (all 13 in the `mod` class) and the dot form for 14 (3 of them in the `mod` class); the pick is a graded test file for 7 by name and 3 by dot. On rich_3468 the gold file `rich/console.py` gives `tests/test_console.py` (graded) by name and 43 files by dot. One name pick (fastapi_14605, `fastapi/_compat/v1.py`, edited in EXP-062-r and EXP-068-read) and two dot picks name `inline_snapshot` or `dirty_equals` in the file or a `conftest.py` on its path, a predicted exit 2; none of the picks on the table above does.

So **the name form is used**: every pick it makes is in EXP-070's `mod` class (the endpoint's definition), it needs only the file name (no dotted-path arithmetic), and it does not print the whole test directory for a central module. It is a deviation from the lead's `git grep -l -F ... | head -n 3` example, for two reasons: the pipe (EXP-066) and the pick quality above. Its ceiling on the base run's edits is **4 tasks of 8** (httpx_3672, requests_7205, requests_7309, rich_3006), 5 if rich_3468's edit lands on `console.py`. The fastapi tasks mostly get no test file and run as today.

**1.3 Output and exit codes, checked locally.** The harness keeps the first 5000 characters of a command's stdout (`swegemma/tools/execution.py:54-56`, `budget.py:30`), so the output is bounded by pytest's own flags, not by a pipe (a pipe would report the pipe's last program's exit code and lose pytest's). On a synthetic test file in the scratch directory, `python -m pytest FILE -q --tb=no -rfE --disable-warnings -p no:cacheprovider` printed one progress line, `FAILED` lines (with parametrized ids) and `ERROR` lines for a fixture error, and a count line, exit 1; an import of a missing module gave `ERROR FILE` and "Interrupted: 1 error during collection", exit 2; a missing file gave exit 4. The sandbox's interpreter is `python3` (harness-stack).

**1.4 How much a new-failure rule can act on (critic, D-010 review).** Of 23 unresolved patched task-runs that also have an empty-patch grading of the same task in the seven pipeline runs, 21 grade with the same failure counts as the empty patch, 1 worse (fastapi_14448 in EXP-069), 1 unreadable. So a rule that acts only on a new failure has about 1 event in 23 to act on on the graded file. That reference is the hidden graded file, not the file the applier runs, so it is a guide, not a rate.

## 2. Design

One variable: **the applier's check, replaced by a runnable verify recipe and a rule for what to do with its result.** One file's sections 1-3 and one sentence of its Budget section.

| | value |
|---|---|
| tree | `experiments/EXP-072/candidate-verify/` = `cp -r experiments/EXP-064/candidate-loc`, then `prompts/applier.md` edited and one history comment in `sub_agents/applier.yaml` |
| `prompts/applier.md` Budget | "Finish as soon as an edit is in" becomes "Finish as soon as an edit is kept" |
| section 1 | "Choose the check, before any tool call" (a self-chosen `python -c` or one `pytest -k`) is replaced by "Before any edit: find the test file and run it once": (1) STEM from the first usable draft's FILE (file name without `.py` and a leading `_`, one example), run exactly `git ls-files -- 'tests/*STEM*'`, one program per command, never `\|`; (2) TEST_FILE is the first printed `test_*.py`, else no test file and no test runs; (3) the baseline, once, before any edit: `timeout 90 python3 -m pytest TEST_FILE -q --tb=no -rfE --disable-warnings -p no:cacheprovider`, noting the exit code and the names on `FAILED` and `ERROR` lines; (4) only exit 0 or 1 is a usable baseline; any other (2 collection or import error such as `ModuleNotFoundError`, 4, 5, 124) gives no signal and no further runs |
| section 2 | steps 2-5 replaced: run the same command after an applied edit when the baseline was usable, after at most 2 edits per task (then keep the next edit that applies with no run); a NEW failure is a name on a `FAILED` or `ERROR` line not in the baseline, or exit 2 when the baseline gave 0 or 1; a failure already in the baseline is never a reason to undo; on a new failure undo with `git checkout -- FILE` (the draft's file) and go to the next draft; otherwise keep the edit and stop (no new failure, exit 0, the same failures, an exit other than 0, 1 or 2, or no run) |
| section 3 | heading "When no draft passed" becomes "When no draft was kept"; the re-apply bullet becomes "If one or more drafts applied but all were undone, apply the first one that applied again with `edit_file`. Never submit with every edit undone." The rest of section 3, section 4 and "Never" are unchanged |
| `sub_agents/applier.yaml` | one comment line (EXP-072, no behavior); tools unchanged (`run_command` was already held) |
| diff | `diff -ru experiments/EXP-064/candidate-loc experiments/EXP-072/candidate-verify` shows those 2 files only; `agent.yaml`, `eval_config.yaml`, `configs/`, `prompts/root.md`, the reader and the five drafters are byte-identical. The applier prompt grows from 693 to 890 words |
| post-edit exit 2 | read as a new failure (the edit broke the test file's import, so tests that passed no longer run). Exit 2 both before and after the edit (the fastapi `ModuleNotFoundError` case) is no signal: the baseline is unusable, so no post-edit run follows |
| lint | `validate_submission.py ... --official --strict --json`: 1 error, the 18.00 h gate, which `--skip-budget-gate` demotes; 2 warnings carried (applier `submit_patch`, `timeout_seconds` 240); no new warning, no forbidden or public-repo word, no rejected marker (pack OK) |
| eval config | EXP-064's: `timeout_seconds` 240, `max_tool_calls` 45, `max_time_minutes` 8, `max_turns` 120 |
| zip | `dist/EXP-072-verify.zip`, sha256 in section 8. Packed with `--skip-budget-gate`: 8 min is above the 4.5 min packing gate (18.00 h nominal, the same override as EXP-061 to 069). **Not an upload.** |
| notebook | `notebooks/exp072_verify/`, kernel `rainm4/gemma4-exp072-verify` |
| cost | ~0.45 GPU-h. Live kernels at push: EXP-071's `rainm4/gemma4-exp071-anchor` (RUNNING) and this one, 2 |

**Known limits, written before the run.**
1. **Ceiling 4 of 8.** On the base run's edits the name form finds a test file on 4 tasks (section 1.2); the three fastapi tasks mostly find none and run as EXP-064-loc. The reader and drafters vary between runs (EXP-061, 062, 066), so the edited file, and the ceiling, move by a task or two. The not-exercised row (3 or fewer of 8) sits one task under the ceiling.
2. **The cap of 2 post-edit runs is prompt-stated only.** The harness has one shared call counter and no per-agent limit; a third run is recorded as a deviation, not prevented.
3. **The test file is fixed once, from the first usable draft's FILE.** A later draft on another file is checked against the same test file.
4. **Wall cost can fire the harm row by design.** The recipe adds up to 4 applier calls (find, baseline, up to 2 post-edit runs), where EXP-070 sized 1 to 2 calls at 20 to 40 s. On a task with a test file, about +25 to +40 s; on the others, +1 call. A mean over 140.0 s (EXP-064-loc 99.99 s + 40) is possible from the design alone; `timeout 90` bounds one run, not the sum.
5. **The new-failure event is rare.** About 1 in 23 on the graded file (section 1.4). A screen with 0 or 1 events reads whether the check runs, not whether undoing helps.
6. **Prompt length.** +197 words on the applier, against the tool-call fragility of long E4B prompts (`knowledge/lessons-e4b-loop.md` line 101, as cited by EXP-069); the first-turn and text-form rows are the guard.
7. **The comparison is by the model, by eye.** It compares `FAILED` and `ERROR` names across two outputs; a misread shows up as an undo after an output with no new name (row 4) or a kept edit after one with a new name (recorded).
8. `git ls-files` has not been seen in any E4B trace (a grep over every local run's traces found it in none). The screen tests that the model runs it as written.

## 3. Endpoints, fixed in advance

By `analyze_traces.py`, `run_forensics.py` and a script over `traces/` written for the analysis job (EXP-070 `desk.py` style: ids, counts, program names, paths and exit codes only).

- **Pair:** a task-run where the applier ran the baseline (a pytest run of one test file before its first `edit_file`) with exit 0 or 1 **and** then ran the same file after an applied edit. Reported per task.
- **Endpoint E:** edited task-runs whose post-edit check ran an existing test file of the edited module (EXP-070's `mod` class) with exit 0 or 1. Reference 0 of 48 (EXP-070; any check that ran at all, 6 of 48). A post-edit run that exits 2 at collection is not counted in E (it is a new-failure event when the baseline was 0 or 1, and no signal when the baseline was also 2).
- **First tool call of the applier,** per task: the find command, a pytest run, `edit_file`, other; and whether the applier's first model turn holds a tool call.
- **Find and baseline:** tasks with the find command; tasks where it printed a `test_*.py`; baseline exit codes by task (0, 1, 2, 4, 5, 124); `ModuleNotFoundError` in a baseline.
- **New-failure events:** post-edit runs with a name on a `FAILED` or `ERROR` line not in the baseline, or exit 2 after a baseline of 0 or 1; counted per task-run, with the kind (named test, collection). Undo calls (`git checkout --` on a source file) and what preceded each (a new failure, no new failure, no run).
- **Draft finally kept** per task (EXP-063 `refs.py` matching), and post-edit runs per task (cap 2).
- **Harm inputs:** time, call and turn cap hits; mean wall against 99.99 s; empties; `tool_free`, `n_text_form_calls` and applier-authored text-form calls; a submitted empty patch after an undo; `scratch_in_patch`; resolves on fastapi_14301 and rich_3006 paired with EXP-064-loc.
- **Recorded only:** wall per task; resolves, paired with EXP-064-loc by `run_forensics.py compare` (never an endpoint).

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Rows 1 and 2 are gates: if either holds it is reported and rows 3 to 6 are **not read** (the numbers are still recorded). Rows 3 to 6 are first-match. Row 7 is read whenever rows 1 and 2 did not fire, alongside the first-match row.

| # | outcome | reading |
|---|---|---|
| 1 | **Infrastructure.** Any of: an `err` with a traceback, a sandbox execution error, a compaction or summarizer `ValueError`; the tree does not run on some task; the root fails to transfer to `pipeline`; a blank or crashed run | A bug, not a reading. Name the task and the step. |
| 2 | **Harm.** Any of: **a lost resolve on fastapi_14301 or rich_3006** (both resolved by EXP-064-loc and EXP-069; paired with EXP-064-loc); **empty patches 2 or more of 8**; any time, call or turn cap hit; **mean wall over 140.0 s** (EXP-064-loc 99.99 s + 40); **any `tool_free` task**; **any applier text-form call**; **the applier's first model turn is text with no tool call on 2 or more tasks**; **a submitted empty patch on a task where an edit had applied and was undone** | The recipe costs more than it buys or breaks the applier. Name the tasks and counts. The form is dropped from D-010 (a harm row binds). A task over 240 s is named, not a row. |
| 3 | **Not exercised.** Rows 1 and 2 did not fire, and **pairs on 3 or fewer of 8 tasks**. Reported with the first-tool-call row: on how many tasks the applier's first tool call is the find command, and for each task without a pair, which step stopped it (no find, no `test_*.py` printed, baseline exit not 0 or 1, no applied edit, no post-edit run) | The recipe did not reach its check on enough tasks to read. No effect is claimed and none is read. If the find command was the first call on 5 or more tasks, the cause is the cohort (no test file, or a baseline without signal), not the model; if on 3 or fewer, the model did not follow the recipe. No decision for this form; it is not killed (D-010: three not-exercised rounds in a row stop the batch). |
| 4 | **Kill (rule not followed).** Rows 1 to 3 did not fire, and **any undo of a source edit that follows a post-edit run with no new failure** (an undo on a baseline failure), **or an undo with no post-edit run before it, or a third post-edit run on one task** | The model does not apply the new-failure rule as written, so it cannot be trusted to keep a resolved fix. The prompt-wording form of the runnable verify is killed on this tree. The lead names the next form. |
| 5 | **Promote.** Rows 1 to 4 did not fire, and **E on 4 or more of 8** | The check runs on the edited module's test file on 4 or more tasks against 0 of 48 before, with the rule followed. Promoted as the base for the next D-010 round on this tree, subject to row 7, and as a free rider for an E4B dev-48 arm run for another reason; not its own dev-48 arm (no resolve claim). |
| 6 | **No decision.** Anything else (pairs on 4 or more with E of 3 or fewer, for example post-edit runs exiting 2) | Record per task. Resolves decide nothing. |
| 7 | **Nothing to act on (round-3 gate; not a kill).** Rows 1 and 2 did not fire, and **new-failure events on 1 or fewer of 8 task-runs** | The check runs but finds nothing to undo, as the critic's 1-in-23 reference expects. Round 3 (per-draft selection on this check) runs only if new-failure events are on **2 or more of 8**; with 1 or fewer it does not run and the lead picks round 3 from the D-010 alternatives. |

**Noise at n = 8 (binomial, per-task probability p that the recipe yields E).** E of 4 or more: p 0.3 gives 0.19, p 0.5 gives 0.64, p 0.6 gives 0.83. Pairs on 3 or fewer: p 0.5 gives 0.36, p 0.6 gives 0.17, p 0.75 gives 0.03. So with a ceiling near 4 of 8 (section 1.2), the promote row needs nearly every task with a test file to run it, and a not-exercised reading is likely even if the model follows the recipe. New-failure events of 2 or more of 8 at the 1-in-23 reference (p about 0.04): about 0.04.

**Not rows, but binding:**
- Per-task resolves at n = 8 are never an endpoint (six of eight must flip the same way for p < 0.05). Only the lost-resolve harm row reads resolves, and only as a one-way bound.
- The endpoint reference (0 of 48) uses EXP-070's narrower `mod` class; a check on another existing test file that imports the module is recorded but not counted in E.
- A post-edit exit 2 with a baseline of 2 is no signal; it is never counted in E and never as a new failure.
- An edit kept after an output with a new name (the model missing a new failure) is recorded per task; it is not row 4, which is about undoing a good edit.
- The task named in the report for each row reached is whatever the traces show, not the prediction below.

**Blind prediction.**
- The find command as the applier's first tool call: about 6 of 8. A `test_*.py` printed: about 4 of 8. Baseline exit 0 or 1 on those: 4 (requests_7205 and 7309 exit 1 with failures already in the file, httpx_3672 and rich_3006 about 0 or 1).
- Pairs: about 4 of 8; E: about 4 of 8.
- New-failure events: 0 (about 0.65), 1 (about 0.3), 2 or more (about 0.05).
- Mean wall about 125 s; P(mean wall over 140 s) about 0.25.
- Row 1: about 0.05. Row 2 (harm): about 0.35 (mostly the wall row). Row 3: about 0.3. Row 4 among the rest: about 0.1. Row 5: about 0.15. Row 6: about 0.05. Row 7 (read with the others): about 0.95.

## 5. What this does and does not license

**The screen can decide one of three things, all about whether the check runs and how its result is used.**
- **Kill:** row 4, the prompt-wording form of the runnable verify on this tree. Row 3 kills nothing.
- **Promote:** row 5 only: the recipe becomes the applier of the next round built on `candidate-loc`, and a free rider for an E4B dev-48 arm run for another reason. A standalone dev-48 arm is not licensed: the event the rule acts on is about 1 in 23 (section 1.4), so the effect on resolves it can show is below the MDE (plan.md section 5.5). A dev-48 endpoint, if one is wanted, is E and new-failure events per 48, with resolves recorded; it needs the user's word and, above 1 GPU-h, a critic `prereg`.
- **Round 3:** row 7 decides whether a per-draft selection form on this check is run (2 or more of 8 events) or not.

**Does not license:** any resolve or LB claim, any upload or dev-48 run, a claim that undoing on a new failure keeps better fixes, any claim about the 31B, or the fused tree with EXP-071 (an interaction no round screens).

## 6. Exact commands

```
python -I -X utf8 experiments/EXP-072/desk.py runs/EXP-061-r runs/EXP-062-r runs/EXP-064-loc runs/EXP-066-srch runs/EXP-068-read runs/EXP-069-argform
python tools/validate_submission.py experiments/EXP-072/candidate-verify --official --strict --json
python tools/pack_submission.py --src experiments/EXP-072/candidate-verify --out dist/EXP-072-verify.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed dist/EXP-072-verify.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-072-verify"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp072_verify/kaggle_eval_l4x4.ipynb
cp notebooks/exp069_argform/kernel-metadata.json notebooks/exp072_verify/kernel-metadata.json   (then id and title changed)
kaggle kernels push -p notebooks/exp072_verify
```

Analysis, a separate job, after `kaggle kernels status rainm4/gemma4-exp072-verify` says COMPLETE: `kaggle kernels output rainm4/gemma4-exp072-verify -p runs/EXP-072-verify/`, flatten, `python tools/analyze_traces.py runs/EXP-072-verify --cap-minutes 8 --max-calls 45`, `python tools/run_forensics.py forensics runs/EXP-072-verify` and `python tools/run_forensics.py compare runs/EXP-064-loc runs/EXP-072-verify`, then the section 3 counts by a script over `traces/`, copied to `experiments/EXP-072/`.

## 7. Defects in this pre-registration, logged after the fact

**Pre-analysis notes, 2026-11-11, written after the push while the kernel was RUNNING and before any output was read. Section 4 is not changed.**

1. **Which `mod` rule E uses.** EXP-070's `desk.py` (line 176-178) takes the stem with its leading `_` kept, so its regex `(^|_)stem(_|\.)` does not class `tests/test_parsers.py` as `mod` for `src/httpx/_parsers.py`. Section 1.2's table and `experiments/EXP-072/desk.py` strip a leading `_` first, and the prompt's STEM does the same. **E is counted with the leading `_` stripped**, the rule section 1.2 already used; E under EXP-070's unstripped rule is reported beside it. The 0 of 48 reference holds under both: EXP-070's checks were suite 8, file 3 (the edited source module, no leading `_`), mod 2 (files that do not exist) and c 2, so stripping moves none of them.
2. **Can the ceiling's four test files collect?** The four name picks are the graded files, so the graded exit code (`test_exit_code` in `task_results.jsonl`) over the seven local E4B pipeline runs (EXP-061-r, 062-r, 063-p, 064-loc, 066-srch, 068-read, 069-argform) is the nearest evidence: requests_7205 1 in 7 of 7, requests_7309 1 in 7 of 7, rich_3006 0 in 6 and 1 in 1, httpx_3672 **2 in 7 of 7**. The httpx_3672 exit 2 is a collection error with `AttributeError` in the tail, raised by the graded (test-patched) version of the file; the local pre-patch `tests/test_parsers.py` imports only `httpx` and `pytest`. So three of the four ceiling baselines are expected to give exit 0 or 1, and httpx_3672's is likely but unconfirmed. If its baseline exits 2, the ceiling is 3 of 8 (4 with rich_3468 on `console.py`) and row 3 is the expected reading by design.
3. **Row 4 governs a third post-edit run.** Known limit 2 calls a third run a recorded deviation; row 4 lists it as a kill. Row 4 is the binding one; the known-limit wording only says the harness does not prevent it.
4. **Row 7 counts both kinds of new-failure event.** A named test new on a `FAILED` or `ERROR` line and an exit 2 after a baseline of 0 or 1 both count toward "2 or more of 8"; the analysis reports the two kinds apart.
5. **Deviations from the lead's dispatch, all in the committed design (section 2):** the find command is `git ls-files -- 'tests/*STEM*'`, not `git grep -l -F ... | head -n 3` (section 1.2: pipe risk and pick quality); the pytest run has no `| tail` (pytest's own flags bound it, and a pipe would hide pytest's exit code); an exit 2 after a usable baseline counts as a new failure and leads to an undo, where the dispatch read a collection error as "submit as is" (exit 2 at both baseline and post-edit stays no signal, as dispatched and as the critic's flag 2 asks); the harm row carries the EXP-069 clause on the applier's first turn being text on 2 or more tasks, which the dispatch did not list.

---

## 8. Built

- **Tree:** `experiments/EXP-072/candidate-verify/` (commit 5ed5b81). `diff -rq experiments/EXP-064/candidate-loc experiments/EXP-072/candidate-verify` lists 2 files: `prompts/applier.md` (Budget sentence, sections 1-3 as in section 2) and `sub_agents/applier.yaml` (one comment line). Applier prompt 693 -> 890 words.
- **Validator:** `--official --strict --json`: 1 error (the 18.00 h packing gate, demoted by `--skip-budget-gate`), 2 warnings (applier `submit_patch`; `timeout_seconds` 240), 20 files, 25.2 KiB, the official validator not importable locally. Same as EXP-069. `python -m pytest -q` passed; `check_repo_hygiene.py --all` OK.
- **Zip:** `dist/EXP-072-verify.zip`, 15.0 KiB, sha256 `2cfe1f9e65af423e0a1fe3091a82135b1c1e03eeba9ba2bf976a1c5f74b6857d`, PACK OK with `--skip-budget-gate --allow-warnings`. Not an upload.
- **Desk check:** `experiments/EXP-072/desk.py` (commit 5ed5b81), output as in section 1.2.
- **Notebook:** `notebooks/exp072_verify/kaggle_eval_l4x4.ipynb`, built with `--cohort experiments/cohorts/smoke-8.txt`, `EXP_ID "EXP-072-verify"`, `MODEL_NAME "gemma-4-e4b-it-qat-w4a16-ct"`, `RUN_GOLD_CONTROL False`, `RUN_AGENT True`, `N_TASKS 8`; `kernel-metadata.json` from `notebooks/exp069_argform` with id and title changed (commit a8ee5f2).
- **Kernel:** `rainm4/gemma4-exp072-verify` version 1, pushed 2026-11-11; status RUNNING right after the push. Live with it: `rainm4/gemma4-exp071-anchor` (RUNNING), 2 in all.

## 9. Results, 2026-11-11. Section 4's readings applied as written.

**Run.** `rainm4/gemma4-exp072-verify` v1 COMPLETE. Kernel wall 1456.97 s = **0.405 GPU-h** (pre-registered estimate about 0.45); vLLM up in 339.4 s. 8 of 8 tasks ran, 8 traces. Output downloaded to `runs/EXP-072-verify/` (one nested `runs/EXP-072-verify/` level flattened). `summary.jsonl` copied to `experiments/EXP-072/verify/summary.jsonl`; the section 3 script is `experiments/EXP-072/verify.py`.

**Row 1 (infrastructure): does not fire.** No traceback `err`, no sandbox execution error, no compaction or summarizer `ValueError` (5 compactions ran without error), the root transferred to `pipeline` on 8 of 8, no blank run.

**Row 2 (harm): FIRES, on three clauses.**
- **A lost resolve on fastapi_14301.** Paired with EXP-064-loc by `run_forensics.py compare`: both 1 (rich_3006), EXP-064-loc only 1 (fastapi_14301), EXP-072 only 0, neither 6; McNemar p = 1.0. rich_3006 kept its resolve.
- **Empty patches 2 of 8:** fastapi_14301 and rich_3468.
  - fastapi_14301: the applier made **no native tool call**. Its first model turn was a thinking step and a final whose text holds a JSON object with an `action` key naming `run_command` and the recipe's find command; then 3 continuation nudges went to the root `swe_agent`, which ended in text. Harness error "Agent completed execution without calling submit_patch", `test_exit_code` -1. This is the recipe's first step written as text in place of a call.
  - rich_3468: 6 `edit_file` calls all failed (2 with a quote-wrapped filepath, EXP-069's class), 1 `read_file`, then `submit_patch` on an empty tree. EXP-064-loc's rich_3468 was also empty; EXP-069-argform's was not. Not new with this recipe, but the clause counts empties, not new empties.
- **Any applier text-form call.** `analyze_traces.py` counts 1 text-form call on 1 task: requests_7205, an applier text turn after its `submit_patch`. fastapi_14301's applier final above is a text-form call by reading as well; the tool does not count it (instrument gap, below).

Clauses that do not fire: no time, call or turn cap hit; **mean wall 124.29 s** (threshold 140.0; median 84.4 s, p90 229.6 s); `tool_free` 0; the applier's first model turn is text on **1** task (fastapi_14301; threshold 2); no undo, so no empty patch after an undo. One task over 240 s is named, not a row: rich_3468 at 245.5 s.

**Reading (row 2):** the recipe costs more than it buys or breaks the applier. **The prompt-wording form of the runnable verify is dropped from D-010** (a harm row binds; D-010 has since been superseded by D-011, and the drop carries over as a result). **Rows 3 to 6 are not read. Row 7 is not read** (section 4: it is read only when rows 1 and 2 did not fire).

**Numbers recorded, not read** (`verify.py`, totals line):
- **First applier tool call:** the find command on **2 of 8** (fastapi_14605, requests_7205; predicted about 6). `edit_file` first on httpx_3672, requests_7309, rich_3006 and rich_3468 (a failed edit with a quote-wrapped filepath on requests_7309, rich_3006 and rich_3468); none on fastapi_14301.
- **Find run on 3 of 8** (fastapi_14448, fastapi_14605, requests_7205), and it printed a `test_*.py` on 3 of 3. On **all 3 the STEM was the package name, not the edited module's stem** (exact-recipe-form n and pattern-holds-stem n on 3 of 3), so the files found were `tests/test_fastapi_cli.py` and `tests/test_requests.py`, neither in the `mod` class of the module edited. The recipe's STEM derivation was not followed on any task that ran the find.
- **Baseline exit 0 or 1 on 2 of 8:** fastapi_14605 exit 1 (2 FAILED lines), requests_7205 exit 1 (58 ERROR lines). No other baseline ran.
- **Post-edit runs on 4 of 8:** fastapi_14448 (no baseline before it), fastapi_14605, requests_7205, rich_3006 (a pytest run with no path argument, the suite, exit 1). No task ran a third post-edit run.
- **Pairs 2 of 8** (fastapi_14605, requests_7205; predicted about 4). **E = 0 of 8** with the leading `_` stripped and 0 of 8 with it kept (predicted about 4; reference 0 of 48). **Tasks that reached a test file of the edited module: 0 of 8.**
- **New-failure events: 0 of 8 task-runs** (named 0, collection 0; predicted 0 at about 0.65). Row 7 is not read, but the count is below its 2-of-8 gate for round 3 selection.
- **Undos 0.** No undo with no new failure, none with no run, no third run: row 4's triggers did not occur.
- **Draft kept** (EXP-063 `refs.py` matching): draft 1 on 4 tasks, '?' on 1 (fastapi_14605), draft 4 on httpx_3672, none standing on 2 (the two empties).
- **Resolves 1 of 8** (rich_3006), recorded only; EXP-064-loc 2 of 8.
- `run_forensics.py forensics`: the run_command mix was grep or rg 13, pytest 6, git 3; fastapi_14301 never edited.

**Against the blind prediction.** Row 2 was given about 0.35, "mostly the wall row"; it fired, but not on the wall (124.29 s, close to the predicted 125 s). It fired on a lost resolve, the empties and text-form calls. The find-first (2 against 6), pairs (2 against 4) and E (0 against 4) predictions all missed high. The new-failure prediction (0) held.

**Instrument gap (a defect, not a revised reading).** `analyze_traces.has_text_form_call` recognises a call-shaped JSON value by the keys `name`, `tool` or `function` with an argument key (`_CALL_NAME_KEYS`, `_CALL_ARG_KEYS`), among other shapes. A JSON object keyed `action` plus a top-level `command`, as in fastapi_14301's applier final, is not recognised, so `n_text_form_calls` undercounts it. Row 2 fires on the requests_7205 count and the other two clauses without it. The tool is not changed here; an `action` key is a candidate for `_CALL_NAME_KEYS` in a later tooling change, tested on fixtures.

**Commands run.**
```
kaggle kernels output rainm4/gemma4-exp072-verify -p runs/EXP-072-verify/
python tools/analyze_traces.py runs/EXP-072-verify --cap-minutes 8 --max-calls 45
python tools/run_forensics.py forensics runs/EXP-072-verify
python tools/run_forensics.py compare runs/EXP-064-loc runs/EXP-072-verify
python -I -X utf8 experiments/EXP-072/verify.py runs/EXP-072-verify
```

## Status

ANALYZED 2026-11-11 (section 9): **row 2, harm** (lost resolve on fastapi_14301, empties 2 of 8, an applier text-form call). The form is dropped. Rows 3 to 7 not read; pairs 2, E 0, new-failure events 0 recorded. 0.405 GPU-h.
