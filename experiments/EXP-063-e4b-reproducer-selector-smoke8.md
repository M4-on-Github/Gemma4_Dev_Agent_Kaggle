# EXP-063 — A reproducer stage used as the applier's selector, over the EXP-062 pipeline tree (smoke-8 screen, D-008 revised rank 2)

**Date:** 2026-11-09
**Type:** smoke-8 screen, about 0.40 L4x4-h (EXP-062 0.323 plus one stage and one test run per applied draft; worst case about 1.3 h with all 8 tasks at the 8 min cap). One push, no upload, no dev-48. This job is zero GPU and builds only; the lead releases the push.
**Cohort:** smoke-8
**Ladder:** L2. L0 (desk check) and L1 (trace mining from `runs/EXP-061-r`, `runs/EXP-062-r`, `traces/`) are section 1.
**Pre-registered:** this file is committed before the push. Sections 2 to 5 are written blind and are not revised.
**Serves:** D-008 revised order, item 2 (`knowledge/directions/D-008-e4b-loop-restart-pipeline-stages.md`, revision da75a14), after the critic's D-008 review (`experiments/EXP-062/critic.md`, ff8654b and 81c907d). The copy adapter on the applier is parked (lead, 2026-11-09); no adapter file was committed for it, and the one scratch counter written for it (`out/exp063_refs.py`, untracked) was deleted.
**Relates:** EXP-052 (pipeline), EXP-061 (LlmAgent root), EXP-062 (this arm's baseline tree), EXP-064 (location-diverse drafters, the screener's arm; the two are fused only in a later round).

## 1. Desk check and reference counts (zero GPU)

**(a) Which files the harness strips from the patch [V].**
- The rule is `_is_protected_test_or_config_path` (`data/src/swegemma/swegemma/harness/verification.py:62-85`). A diff section is dropped when its file:
  - has one of these names: `conftest.py`, `pytest.ini`, `pyproject.toml`, `tox.ini`, `setup.cfg`, `.pytest.ini`, `sitecustomize.py`, `usercustomize.py`, `_swegemma_stubs.py` (:66-77);
  - ends in `.pth` (:78-79);
  - starts with `test_` and ends in `.py` (:80-81), or ends in `_test.py` (:82-83);
  - is a `.py` file under any directory named `tests`, `test` or `testing`, case-insensitively (:84-85).
- The task's own test files are protected as well (`extra_protected_paths`, :88-101). Paths are read from the `diff --git`, `---` and `+++` headers with the `a/` and `b/` prefixes removed (`swegemma/models/task.py:16-30`).
- When the strip runs:
  - At `submit_patch`. The tool first runs `git add -N .`, so a new untracked file the model writes is in the diff, and then it strips (`swegemma/tools/execution.py:86-110`). So the patch the model sees in `get_status` already lacks the file.
  - Again after the run, for a submitted patch (`harness/agent_runner.py:1098-1103`), and for the on-disk fallback diff when nothing was submitted (`agent_runner.py:1054-1071`).
  - Again at grading, with the task's target test files as extras (`verification.py:429-441`). After the patch is applied, the grader also resets every protected file the agent touched (`verification.py:510-535`).
- **Answer:** a test file the model adds at `test_issue_repro.py` is removed from the patch at submit and again before grading. The critic's claim holds for the `test_*.py` name, and the rule is wider than that name alone.

**(b) Can a later stage run a file an earlier stage wrote [V]? Yes.**
- One sandbox is started per task (`agent_runner.py:493`), with one `SwegemmaContext` on that container (:519-531).
- One tool registry is built from that context (`context.create_tools()`, :600) and given to `compile_submission` for the whole tree (:616-618). Every stage's `write_file` and `run_command` therefore act on the same container.
- `write_file` writes under `/workspace` (`swegemma/tools/workspace.py:181-205`, with the path resolved strictly inside `/workspace` at :22-47). Nothing resets the workspace between the stages of a SequentialAgent.
- The grader runs `python3 -s -m pytest` from `/workspace` (`harness/verification.py:628-629`). Our E4B runs used `python3` for 105 run_command calls that exited 0 (EXP-028 to EXP-062 traces; `python` was never used). So the stage's command is `python3 -m pytest test_issue_repro.py -q`.

**Reference counts.** Script: `experiments/EXP-063/refs.py`, run as `python -I -X utf8 experiments/EXP-063/refs.py runs/EXP-061-r runs/EXP-062-r`. It prints ids, letters, program names, path arguments and exit codes only.
- A check is an applier `run_command` whose program is `pytest` or `python3` (not `git`).
- "Names the edited file" means the path argument is the edited file, or a file whose name contains the edited file's stem.
- "Kept" is the draft of the last applied edit that no undo reverted. An edit is matched to a draft when its `old_string` or `new_string` equals that draft's block. `?` means the edit text is in no draft.

| task | EXP-061: applied, check after applied draft (exit), kept | EXP-062: applied, check after applied draft (exit), kept |
|---|---|---|
| fastapi_14301 | 0 applied, no check, none (empty) | 1, `pytest tests/` (2), `?` (all 5 drafts NO DRAFT) |
| fastapi_14448 | 1, `pytest` on a test path naming the stem, absent (4), 1 | 2, bare `pytest` (2), `?` (after 5 failed resends of draft 2) |
| fastapi_14605 | 1, no check, 1 | 1, no check, 1 |
| httpx_3672 | 1, no check, 2 | 3, no check, `?` (drafts 2 and 3 stacked, then own edit) |
| requests_7205 | 1, bare `pytest` (1), 1 | 0, no check, none (empty) |
| requests_7309 | 0 (4 failed edits), none (empty) | 1, `pytest` on the edited source file (2), 1 |
| rich_3006 | 1, `pytest tests/` (1), 1 | 1, `pytest` on a test path naming the stem, absent (4), 1 |
| rich_3468 | 1, no check, 1 | 1, no check, 1 |

Pooled over 16 task-runs:
- 13 had an applied edit. 7 checks followed an applied draft, on 7 tasks.
- Of those 7 checks:
  - 0 exited 0. Exit codes were 1 on 2, 2 on 3 and 4 on 2.
  - 3 named the edited file, and none of the 3 ran a test: two paths did not exist (exit 4) and one was a source file (exit 2).
  - 0 ran a test that both executed (exit 0 or 1) and concerned the edit.
- **0 undos in 16 task-runs.** No check ever rejected a draft, so the applier never moved off the first draft that applied.
- Kept: draft 1 on 9, draft 2 on 1, unmatched on 3, none on 3. Among tasks whose kept edit matches a draft, draft 1 was kept on 5 of 6 in EXP-061 (the critic's count) and 4 of 4 in EXP-062.
- **The selector reference is therefore 0 departures in 16.**

## 2. Design (the one variable: a reproducer stage and the applier's use of its test)

| item | value |
|---|---|
| tree | `experiments/EXP-063/candidate-p/` = the committed `experiments/EXP-062/candidate-r` (exported LF with `git -c core.autocrlf=false archive`), then 2 new files and 3 edited ones |
| new | `sub_agents/reproducer.yaml`: an E4B LlmAgent with `read_file`, `run_command`, `get_status` and `write_file`, no `edit_file`. It has `include_contents: default` (it needs the task message), `output_key: repro` and the reader's sampling file. `prompts/reproducer.md`: write one test of at most 30 lines with `write_file` at `test_issue_repro.py`, using the standard library, pytest and the project only. Run `python3 -m pytest test_issue_repro.py -q` once, rewrite it once if it errors or passes, and report `TEST:` / `RESULT: FAILS, PASSES or ERROR` / `END`. At most 2 `read_file`, no test reads, no source changes |
| edited | `sub_agents/pipeline.yaml`: the stages become reader, reproducer, draft, applier (one comment line and one list line). `prompts/applier.md`: the team paragraph names the test writer, a `Test writer report: {repro?}` block follows the reader report, and section 1 says the check is `python3 -m pytest test_issue_repro.py -q`, reused for every draft, when the report says `RESULT: FAILS` (otherwise EXP-062's rule, word for word). It also says not to edit or delete that file. `sub_agents/applier.yaml`: one comment line |
| unchanged | `agent.yaml`, `eval_config.yaml` (240 s, 45 calls, 8 min, 120 turns), `configs/`, `prompts/root.md`, `prompts/reader.md`, the drafters, and the applier's sections 2 to 4. So "undo with `git checkout -- FILE` on an assertion failure and go to the next draft", "keep on an uninformative failure" and "re-apply the first that applied when none passed" are EXP-062's rules as written |
| zip | `experiments/EXP-063/exp063_p.zip` (gitignored). Packed with `--skip-budget-gate` because the 8 min cap is above the 4.5 min packing gate (18.00 h nominal, the same override as EXP-061, EXP-062 and EXP-064) and with `--allow-warnings` for the two warnings EXP-062 already carries. **Not an upload** |
| notebook | `notebooks/exp063_p/`, EXP-062's build command with only the zip and `EXP_ID` changed; kernel `rainm4/gemma4-exp063-p` |
| cost | about 0.40 GPU-h (EXP-062 0.323 plus about 30 to 60 s per task); worst case about 1.3 h. No slot is used |

Calls: the reader's worst pass is 13. The reproducer adds at most about 6 (2 reads, 2 writes, 2 runs), and the applier at most 3 per draft plus submit. That is about 35 of 45.

**Known limits, written before the run.**
1. **A wrong test selects wrongly.** If the test fails a correct draft 1 and passes a wrong later draft, the selector does harm. That would show as a lost resolve on fastapi_14301 or rich_3006, the only tasks that resolve on this cohort, and it is named in section 9. If no draft passes, the applier falls back to the first draft that applied, which is EXP-062's behaviour.
2. **The Kaggle sandbox lacks some test dependencies** (15 of dev-48 are gated, harness-stack). A test that imports a missing package errors at collection (exit 2) and is uninformative. The prompt forbids the project's test fixtures for this reason.
3. **Exit 1 is the failing-on-base signal.** It also counts an exception raised inside a test function, not only an assert. The stage's own RESULT line is recorded beside it.
4. **Longer windows.** The reproducer and the applier have `include_contents: default`, so the applier now also sees the reproducer's events. EXP-062 crossed 14,336 prompt tokens on 3 tasks. The expected cost is more in-flow compactions and a longer wall, and the harm row covers it.
5. **The reader prompt and the pipeline description still describe three stages.** They are left unchanged so that only the stage and its use change.
6. **A nudge re-run** restarts the pipeline at the reader (harness-stack `reference/routing.md`). The reproducer would then overwrite the file. EXP-062 had no nudges.
7. **Mixed message to the applier.** Its unchanged section 3 says files left in the repository fail grading, while the new section 1 says the test file is removed automatically. The applier may delete the test to be safe. That would show as later drafts going unchecked; it is recorded, not a row.

## 3. Endpoints, fixed in advance

Per task, from `traces/`, `task_results.jsonl`, `summary.jsonl` and the kernel log:
- **W (written).** Tasks where the reproducer called `write_file` on `test_issue_repro.py`.
- **Rf (fails on base).** Tasks where the reproducer's last run of that file, a `run_command` of `pytest` or `python3` whose path argument is `test_issue_repro.py`, exited **1**. Also record its RESULT line and any disagreement.
- **U (selector used).** Tasks **in Rf** where the applier ran `test_issue_repro.py` after at least one applied draft, so U <= Rf. The same count over all 8 tasks is recorded beside it, since the applier acts on the RESULT line and not on the exit code.
- **D (departure).** Tasks where all three of these hold:
  - the first draft that applied (draft 1, or a later one when draft 1 did not apply) was followed by an applier run of `test_issue_repro.py` that exited 1;
  - the kept draft is a later draft;
  - the applier's run of `test_issue_repro.py` after the kept draft exited 0.

  The reference is 0 of 16 (section 1), counted the same way.
- **Ignored verdict.** Tasks where the applier ran `test_issue_repro.py` after an applied draft, the run exited 1, and that draft was kept or submitted with no undo after it.
- **Per task:** which check followed each applied draft (program, path, exit), undos, and the kept draft, as in section 1.
- **Reproducer writes.** Every `write_file` path by the reproducer, and, by program name, any `run_command` of its other than `pytest`, `python3` or a read-only program (`ls`, `sed`, `head`, `cat`, `wc`, `git grep`).
- **Stray path.** Any path in a task's final `patch` that no applier `edit_file` or `write_file` touched (a misnamed test, a scratch file or a shell-written file, whoever wrote it).
- **Leak.** Whether `test_issue_repro.py` appears in any task's final `patch`.
- **Harm inputs.** Any time, call or turn cap hit; empty patches (the base maximum is 2 of 8: EXP-061 2, EXP-062 1); mean wall against 89.5 s (EXP-061) and 89.2 s (EXP-062).
- **Errors.** `err` per task: a traceback, a sandbox execution error, a compaction error, or the no-submit label.
- **Compaction.** The count, and the largest single-request prompt against 14,336.
- **Movable tasks, reported separately:** fastapi_14448 and rich_3468, with W, Rf, the checks and the kept draft.
- **Recorded only:** resolves, applier edit failures, and tokens.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

First match governs.

| # | outcome | reading |
|---|---|---|
| 1 | **Infrastructure.** Any of: an `err` with a traceback, a sandbox execution error or a compaction error; the tree does not run on some task; the root fails to transfer to `pipeline` in its first invocation; the reproducer stage runs on no task; `test_issue_repro.py` appears in a final patch (the strip of section 1 (a) failed) | A bug, not a reading. Name the task and the step. |
| 2 | **Harm.** Any of: a time, call or turn cap hit; **3 or more empty patches of 8** (above the base maximum of 2); **mean wall over 150 s**; a stray path (section 3) in a final patch | The stage costs more than it buys. Name the tasks. 150 s is D-008's restated line: the base means are about 89 s and the base task maxima already about 165 to 170 s, so a 150 s mean is about 60 s more per task. That is twice what one stage of about 5 calls and one test run per draft should cost. |
| 3 | **Not exercised.** Rf < 3: the reproducer writes a test that fails on the unfixed code on fewer than 3 of 8 tasks | The stage cannot produce a failing-on-base test often enough to act as a selector here. **No decision**, not "a reproducer does not help". Record W, Rf and the exit codes. A stronger form (a test from the task's own test module, or two attempts) is the lead's call. |
| 4 | **Kept.** Rows 1 to 3 did not fire, **U >= 3 and U > Rf / 2** (the applier uses the test on most tasks where it exists), and **D >= 1** (at least once, the first applied draft failed the test and a later draft that passed it was kept) | The selector works as built: the test is run, it rejects a draft, and the selection moves, against a reference of 0 departures in 16. This is a process reading, not a resolve claim. It licenses the fusion with EXP-064 (D-008 revised item 3), not a dev-48 by itself. |
| 5 | **Dropped.** Rows 1 to 3 did not fire, and either **U <= 1** (the applier does not run the test where it exists), or **ignored verdict on 2 or more tasks** (the applier runs the test and keeps a draft that failed it, with no undo) | The applier does not act on the test as built, so the selector adds nothing over EXP-062. D-008's item 2 is closed for this form. Record which branch fired. |
| 6 | **No decision.** Anything else, including U = 2, U at most Rf / 2, U >= 3 with D = 0, and U >= 3 with the test passing after no applied draft on any task. That last case is the mechanism working with nothing to pick: at n = 8 it cannot be told apart from drafts that are all wrong (13 E4B runs resolved only fastapi_14301 and rich_3006, critic) | Record W, Rf, U, D and the per-task checks. |

**Not rows, but binding:**
- Resolves at n = 8 are never an endpoint. A resolve lost or gained on fastapi_14301 or rich_3006 is named, with whether the selector moved the kept draft on that task.
- The two movable tasks are reported by themselves in section 9 whatever row fires.
- D counts only departures made by the test. A kept draft other than the first applied one with no failing test run after the first applied one (for example stacked drafts with no check) is recorded and not counted.
- If no prompt reaches 14,336 tokens, the compaction cost of the longer windows is recorded as untested.

**Blind prediction.**
- W on 7 or 8 of 8. Rf on about 3 to 4: several tests will error at collection or pass on the unfixed code.
- Row 3 about 0.35, row 5 about 0.20, row 2 about 0.15 (mostly the wall), row 6 about 0.13, row 4 about 0.12, row 1 about 0.05.
- Mean wall about 125 s (range 105 to 160). Where the test exists, the applier uses it (U close to Rf), and drafts that apply mostly all fail it or all pass it, so D is 0 or 1.

## 5. What this does and does not license

- **Kill:** row 5 closes D-008 item 2 for this form. Row 3 with the lead's agreement closes it, unless the lead releases the stronger form.
- **Promote:** row 4 only, to the fused round with EXP-064's drafters (still a smoke-8 screen). Even a perfect smoke-8 gives a one-sided p of about 0.10 against the pooled base (critic). A dev-48 pair needs the lead's budget call and the user.
- **Does not license:** any resolve or LB claim, any upload or dev-48 run without the user, or a claim about the copy adapter.

## 6. Exact commands

```
python -I -X utf8 experiments/EXP-063/refs.py runs/EXP-061-r runs/EXP-062-r
python tools/validate_submission.py experiments/EXP-063/candidate-p --official --strict
python tools/pack_submission.py --src experiments/EXP-063/candidate-p --out experiments/EXP-063/exp063_p.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed experiments/EXP-063/exp063_p.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-063-p"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp063_p/kaggle_eval_l4x4.ipynb
```

This job does not run the kernel push; the lead releases it. The analysis is a separate job, run after `kaggle kernels status` says COMPLETE:
1. Download with `kaggle kernels output rainm4/gemma4-exp063-p -p runs/EXP-063-p/`, then flatten.
2. Run `python -I -X utf8 tools/analyze_traces.py runs/EXP-063-p --cap-minutes 8 --max-calls 45`.
3. Run `python -I -X utf8 tools/run_forensics.py forensics runs/EXP-063-p`.
4. Run `python -I -X utf8 experiments/EXP-063/refs.py runs/EXP-063-p` for the applier's checks and the kept draft. Count W, Rf, U and D from `traces/` as in section 3, and the leak from `task_results.jsonl`.

## 7. Defects in this pre-registration, logged after the fact

1. **(Known at pre-registration.)** `refs.py` matches an edit to a draft by exact equality of either block after removing fence lines. An edit that changes one character of a draft reads as `?`, so "kept draft 1" may be undercounted.
2. **(Known at pre-registration.)** The tree was built by exporting the committed EXP-062 tree and editing it, not by a hash-verifying tool. `diff -ru experiments/EXP-062/candidate-r experiments/EXP-063/candidate-p` is the check (section 8).

## 8. Built (below the line; nothing above changes)

---

- **Changed files vs EXP-062 `candidate-r`:** new `prompts/reproducer.md` and `sub_agents/reproducer.yaml`; edited `prompts/applier.md` (team paragraph, `{repro?}` block, section 1), `sub_agents/pipeline.yaml` (one comment line, one stage line), `sub_agents/applier.yaml` (one comment line). `diff -ru` shows nothing else. No CR byte in the tree.
- **Validator** (`--official --strict`): 1 error, the 18.00 h gate, which `--skip-budget-gate` demotes to a warning. 2 warnings, both carried by EXP-061 and EXP-062: the applier's `submit_patch` and `timeout_seconds` 240. The official validator could not be imported (no `adk_submission` locally). 11 agents, 22 files.
- **Pack:** `RESULT: VALID (0 errors, 3 warnings)`, PACK OK, 22 files, 15.7 KiB. **sha256 `48dfee068198201f8ada36ce91e045ef3d3d0641ad5362b70e2115fd3420e7af`.**
- **Pre-registration commit:** 6b605cf. `git ls-files --eol` on the candidate tree: all 22 blobs `i/lf`, worktree `w/lf`. The committed tree exported with `git -c core.autocrlf=false archive HEAD` and repacked to `out/exp063_repack.zip` gives the same sha `48dfee06...20e7af`.
- **Notebook:** `notebooks/exp063_p/`, built with the section 6 command; the embedded zip decodes to sha `48dfee06...20e7af`. Against `notebooks/exp062_r/` the code cells differ only in `EXP_ID` and `SUBMISSION_B64`; `TASK_IDS` is the 8 smoke-8 ids, `RUN_AGENT = True`, `RUN_GOLD_CONTROL = False`. `kernel-metadata.json` is EXP-062's with only `id` and `title` changed, to `rainm4/gemma4-exp063-p`.
- **Kernel id for the push:** `rainm4/gemma4-exp063-p`, directory `notebooks/exp063_p`. Expected about 0.40 GPU-h; worst case about 1.3 h.

## Status

PUSHED 2026-11-09, released by the lead: kernel `rainm4/gemma4-exp063-p` version 1, first status QUEUED. No upload, no dev-48. Next, when the lead reports COMPLETE: `kaggle kernels output rainm4/gemma4-exp063-p -p runs/EXP-063-p/`, move the nested bundle up, then the section 6 commands.

2026-11-10: v1 cancelled by the user after about 20 h QUEUED, never ran; v2 pushed 2026-11-10 (kernel version 2, first status RUNNING at 13:30 UTC). Next command unchanged.

2026-11-10: version 2 COMPLETE (lead, 16:24 UTC), downloaded and analysed (section 9). **Row 3 fires: not exercised (Rf 0 of 8; the reproducer made no tool call on any task), no decision.** 0.401 GPU-h. Nothing running.

---

## 9. Results, 2026-11-10. Section 4's readings applied as written.

**Row 3 fires: not exercised.** Rf = 0 of 8, below 3. The reproducer made **no tool call on any task**: no `write_file`, no `run_command`, no `read_file`. On each task its stage was one model call, a thinking step and a final turn. In the final turn it named `test_issue_repro.py` as its test without having written it, and it gave the RESULT label FAILS on 6 tasks. W = 0, Rf = 0, U = 0, D = 0. **No decision** on D-008 item 2. Whether to release a stronger form is the lead's call (section 4 row 3).

### 9.1 Run

- Kernel `rainm4/gemma4-exp063-p`, version 2. Version 1 was cancelled by the user after about 20 h QUEUED and never ran. Version 2 was pushed 2026-11-10 and was COMPLETE by 16:24 UTC (lead).
- Downloaded with `kaggle kernels output rainm4/gemma4-exp063-p -p runs/EXP-063-p/`. The nested `runs/EXP-063-p/runs/EXP-063-p/` was copied up one level.
- **Kernel wall 1441.9 s = 0.401 GPU-h**, from the last entry of the kernel log. vLLM was up in 345.9 s (tp 4, 4 GPUs).
- The shipped `agent/` copy in the bundle matches the committed tree: `sub_agents/reproducer.yaml` sha `292c3cd1...` and `prompts/reproducer.md` sha `49a2fff9...` are identical. The reproducer was declared with `read_file`, `run_command`, `get_status` and `write_file`.
- Commands, as in section 6:
  - `python -I -X utf8 tools/analyze_traces.py runs/EXP-063-p --cap-minutes 8 --max-calls 45`
  - `python -I -X utf8 tools/run_forensics.py forensics runs/EXP-063-p`
  - `python -I -X utf8 experiments/EXP-063/refs.py runs/EXP-063-p`
- The section 3 counts per task were read from `traces/` with an untracked scratch driver (`out/exp063_wrfud.py`, `out/exp063_facts.py`) that uses refs.py's helpers.
- `summary.jsonl` is copied to `experiments/EXP-063/p/summary.jsonl`.

### 9.2 Section 3 endpoints per task

Columns:
- **W:** the reproducer wrote `test_issue_repro.py`.
- **Rf:** the reproducer's last run of the file exited 1.
- **U (in Rf / all 8):** the applier ran the file after an applied draft.
- **D:** a departure made by the test.

The applier checks are listed in order (program, exit code). Every one named `test_issue_repro.py`; requests_7309's second check named it under `tests/`. The kept draft is refs.py's label.

| task | W | repro RESULT label | Rf | applied drafts | applier checks of the file | U (in Rf / all) | D | kept | patch |
|---|---|---|---|---|---|---|---|---|---|
| fastapi_14301 | 0 | FAILS | 0 | none (6 `edit_file`, all failed) | `python3 -m pytest` (4), after no applied draft | 0 / 0 | 0 | none | empty |
| fastapi_14448 | 0 | FAILS | 0 | 1, then 3 (no undo between) | `pytest` (4) after draft 1; `pytest` (4) after draft 3 | 0 / 1 | 0 | 3 | `fastapi/routing.py` |
| fastapi_14605 | 0 | FAILS | 0 | 1 | `python3 -m pytest` (4) | 0 / 1 | 0 | 1 | `fastapi/_compat/__init__.py` |
| httpx_3672 | 0 | FAILS | 0 | 5, then one unmatched edit | `pytest` (4) after draft 5 | 0 / 1 | 0 | ? | `src/httpx/_parsers.py` |
| requests_7205 | 0 | none of the three | 0 | 1 | `python3` on the file (2) | 0 / 1 | 0 | 1 | `src/requests/utils.py` |
| requests_7309 | 0 | FAILS | 0 | 1 (after one arg-loss failure) | `python3 -m pytest` (4), twice | 0 / 1 | 0 | 1 | `src/requests/utils.py` |
| rich_3006 | 0 | FAILS | 0 | 1 | `python3 -m pytest` (4) | 0 / 1 | 0 | 1 | `rich/repr.py` |
| rich_3468 | 0 | none of the three | 0 | none (7 `edit_file`, all failed) | none | 0 / 0 | 0 | none | empty |
| **total** | **0** | FAILS 6 | **0** | | 9 checks, 8 after an applied draft | **0 / 6** | **0** | | 2 empty |

- **Exit codes.** No reproducer or other agent wrote the file, so every applier check ran a file that did not exist. Exit 4 is pytest's usage-error exit and 2 is the interpreter's cannot-open exit [I, from the absent file]. No check exited 0 or 1.
- **Ignored verdict:** 0, since no run exited 1.
- **What the applier did.** On 6 of 8 tasks it acted on the report's FAILS label and ran the named file after an applied draft. On requests_7205 it ran the file although the report had no FAILS label.
- **Reproducer writes:** none. It made no `run_command` at all.
- **Stray path:** none. Every final-patch path was touched by an applier `edit_file`.
- **Leak:** `test_issue_repro.py` is in no final patch.
- **Text-form calls** (analyze_traces 2f9de11): `n_text_form_calls` 0 on all 8 and `tool_free` false on all 8. On 6 tasks the reproducer's final turn held a python-fenced test body. That is a written test, not a call-shaped JSON value, so it is not a text-form call by the EXP-065 rule.

### 9.3 Harm inputs and errors

- **Caps.** No time, call or turn cap was hit: the most calls on a task was 19 of 45, and the most turns was 29 harness LLM calls (30 agent steps by the analyzer), against 120.
- **Empty patches:** 2 of 8 (fastapi_14301, rich_3468), equal to the base maximum of 2.
- **Wall.** Mean 119.47 s against 89.5 s (EXP-061) and 89.2 s (EXP-062). The median was 1.96 min and the maximum 164.0 s (fastapi_14448).
- **Errors.** `err` is empty on all 8; all 8 have status SUCCESS and submitted.
- **Compactions:** 2 (fastapi_14448, httpx_3672). The largest single-request prompt was 25,472 on rich_3468, against 14,336. No compaction error.
- **Edit failures:**
  - by task: requests_7309 1, fastapi_14448 2, fastapi_14301 6, rich_3468 7, the rest 0;
  - 16 in all, 1 of them an argument loss (requests_7309).

### 9.4 Rows applied in order

1. **Infrastructure, does not fire.**
   - No traceback, sandbox error or compaction error.
   - The tree ran on all 8, and the root transferred to the pipeline at step 3 on every task.
   - The reproducer stage ran on all 8: it produced a turn each time, but no tool call.
   - There was no leak.
   - Whether the E4B was offered the reproducer's tools cannot be read from a trace, because tool declarations are not recorded. The shipped yaml declares them, and the reader in the same tree used `run_command` on every task [I: not a registry fault].
2. **Harm, does not fire.** No cap hit; empty patches 2, not 3 or more; mean wall 119.47 s, not over 150; no stray path.
3. **Not exercised, fires.** Rf = 0 < 3.

Rows 4 to 6 are not reached.

### 9.5 Movable tasks

- **fastapi_14448.** W 0, Rf 0; the report gave FAILS. The applier applied draft 1 and ran the absent file (pytest, exit 4). It then made two failed `edit_file` attempts at draft 1 and applied draft 3 on top of draft 1 with no undo. It ran the absent file again (exit 4) and submitted. The patch has `fastapi/routing.py`; not resolved; wall 164.0 s; 1 compaction. Draft 3 was kept, but not because of a test: under the binding note in section 4 it is recorded, not counted as D.
- **rich_3468.** W 0, Rf 0; the report gave none of the three RESULT labels. All 7 applier `edit_file` calls on `rich/console.py` failed, so no draft applied and no check ran. `submit_patch` was called twice; the patch is empty. Not resolved; wall 155.4 s; largest prompt 25,472.

### 9.6 Resolves, recorded only

1 of 8 (rich_3006).
- **Against EXP-061 and EXP-062:** no resolve lost or gained on fastapi_14301 (unresolved in all three) or rich_3006 (resolved in all three).
- **On rich_3006** the selector did not move the kept draft. Draft 1 was kept, after a check of the absent file.

### 9.7 Prediction against outcome

- **Rows.** Row 3 was the modal prediction (0.35), and it fired.
- **W.** The prediction was 7 or 8 of 8; the outcome was 0. The predicted failure route was tests that error at collection or pass on the unfixed code. That is not what happened: the stage never called a tool.
- **Mean wall.** Predicted about 125 s (range 105 to 160); observed 119.47 s.
- **U.** The prediction said U would be close to Rf. The applier did run the named file on 6 of 8 tasks, but Rf was 0.

### 9.8 What this bears on (not a reading)

- The applier took a FAILS label at face value on 6 tasks and ran a file that did not exist. The selector as built has no check that the test exists.
- The reproducer's failure is a single-call stage that answers in text without using its tools. It is not the predicted failure, a test that does not fail.
- Any stronger form has to make the write happen, for example:
  - a stage whose final answer is only accepted after a `write_file`;
  - or a check of the file inside the applier's rule.
- Both are design choices for the lead. This screen did not test them.
