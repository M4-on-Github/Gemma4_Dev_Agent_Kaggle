# EXP-073 — A reproducer stage made tool-first: one `python3 -c` check run before the edit, and run again by the applier (smoke-8 screen, D-010 round 4)

**Date:** 2026-11-11
**Type:** smoke-8 screen, ~0.40 L4x4-h of the 30/week (EXP-063 0.401 with a reproducer that made no call; EXP-064 0.353; this tree adds one to two reproducer calls and about one applier call per applied draft). One push, no upload, no dev-48. D-010 spend so far: EXP-071 about 0.38, EXP-072 about 0.45 (planned), this about 0.40; ceiling 2.5.
**Cohort:** smoke-8
**Ladder:** L2. L0 and L1 are section 1 (EXP-063 section 9, EXP-068 section 1.3, EXP-064-loc and the pipeline runs on disk, the harness source for the sandbox's import path).
**Pre-registered:** this file is committed before the push. Sections 3-5 are written blind and are not revised.
**Serves:** D-010 (`knowledge/directions/D-010-e4b-five-tweak-rounds.md`), revision item 3 (the round the critic named in `experiments/EXP-070/critic.md`); C-018 (a check costs wall; the one-line form is the compromise); the E4B pipeline's missing selection signal.
**Relates:** EXP-063 (the reproducer that made 0 tool calls on 8 of 8, row 3), EXP-068 section 1.3 (the desk check that named the probable cause), EXP-064 (the base tree, `candidate-loc`), EXP-072 (the runnable verify, the same applier file edited on the same base; the two trees are not fused here), EXP-070 (the check counts).

## 1. Why this, now (zero GPU)

### 1.1 The record
- **EXP-063** put a reproducer between the reader and the drafters. It had four tools and no first-call line, and its answer form (`TEST` / `RESULT` / `END`) could be written without a call. Result: **0 tool calls on 8 of 8**, `RESULT: FAILS` stated on 6 tasks about a file that did not exist, and the applier ran that absent file on 6 tasks (EXP-063 section 9.2). Row 3, no decision.
- **EXP-068 section 1.3** (my desk check) named the probable cause. The reproducer lacked "Your first reply must be a tool call, not text", its answer form was one a text reply satisfies, its last message was the reader's `END`-closed report, and it held four tools. The drafters of EXP-068 shared the last two of the first three and got the opener: **36 of 40 drafter turns opened with a `read_file` call**, fabricated OLD 0 of 40. The reader, which has the opener, called a tool on 8 of 8 in every tree.
- **D-010 revision item 3** (after the critic) makes this round 4: the reproducer stage with the hard first-call opener, base `candidate-loc`, endpoints the first-turn tool call and the share of reproducer runs that fail before the edit. The critic's reason: it is the one round that could create a selection signal, because a draft's check outcome could tell drafts apart.
- **The selector's reference** (EXP-070, D-010 ranking section): an unprompted check ran after the last applied edit on 15 of 48 edited task-runs; 6 of them ran any test or code; 0 ran an existing test file of the edited module; on all 4 resolved task-runs that had a check, the check exited non-zero and the applier submitted anyway. EXP-063 section 1 counted 0 undos in 16 task-runs.

### 1.2 Desk checks made for this build

**(a) Stage order: kept as EXP-063's (reader, reproducer, draft, applier).** The cause list of EXP-068 section 1.3 has one item that the order sets: the reproducer's last message is the reader's `END`-closed report. The drafters stand in the same position (their `include_contents: none` window starts at the latest event of another agent, which is the reader's final) and held the opener on 36 of 40. So the position does not defeat the opener, and the order is not changed. The reproducer is placed before the drafters so that the check exists on the unfixed code when the applier needs it; an applier-side placement would run on edited code.

**(b) Tools: the stage drops to `run_command` only. The desk check does not show that the count of four was part of the cause, so this is a package, not an isolated change.** EXP-068 section 1.3 records the tool count as not separable from the missing opener. Two precedents bracket it: the reader's three-tool declaration complied on 8 of 8, and the drafters' one-tool declaration on 36 of 40. Why drop anyway: `write_file` is dead weight for a one-line check and is the route to the file the harness would strip, `read_file` and `get_status` are covered by the reader's REGION text in the report. If the screen reads row 3 (not exercised), the opener and the tool strip cannot be told apart in the cause; if it passes, the pair is the one variable "the stage made tool-first" (section 7 item 3).

**(c) Check form: one line, `PYTHONPATH=src:. python3 -c "..."`, no file.**
- A test file under `/workspace` named `test_*.py` is stripped from the patch at `submit_patch` and at grading (harness-stack, patch strip), and a stage that writes a file has the route to the EXP-063 failure (a stated result for a file never written). A one-line command leaves no file and gives the applier a string it can run itself.
- **The import path.** On a src-layout package (requests, httpx: `src/requests`, `src/httpx` in this cohort, 3 of 8 tasks) a plain `import` may not reach the workspace copy. Evidence: in EXP-028 Arm R on `requests_7309` the 31B ran `python3 -c "from requests.utils import ..."` after its edit, got the unedited behavior, reasoned that it was importing an installed copy, and `PYTHONPATH=src python3 -c ...` then gave the edited behavior (trace `runs/EXP-028-armR/traces/trace_requests_7309.json`, observations at lines 227 and 315). The harness is consistent with that [I]: the subprocess sandbox skips the editable install (`harness/container_setup.py:512-513`) and sets `PYTHONPATH` to the workspace root only (`sandbox/subprocess.py:488`). So a check without `src` can pass or fail on stale code after an edit and would make the applier reject a right draft. The command therefore carries `PYTHONPATH=src:.` (repo-agnostic, no lint word). Layouts other than `src/` and top-level are not covered (section 2 limit 2).
- **The result shape.** `run_command` returns an error envelope with `exit_code` and `stderr` when the exit is non-zero, and `{"status": "ok", ..., "exit_code": 0}` otherwise (`swegemma/tools/execution.py:58-73`). Exit 1 covers an `AssertionError` and an `ImportError` alike (the same 31B trace shows exit 1 on a `NameError`), so the readings split by the last line of `stderr`, which the stage copies into its report.
- **Why no `def`:** the one `python3 -c` an E4B pipeline wrote in the four trees on disk (EXP-062 to EXP-069) defined a test function and never called it, which exits 0 vacuously. The prompt forbids a function and requires an `assert`.

**(d) Verdict channel.** The applier's window may not carry the reproducer's tool events (compaction keeps the last 5 events, and five drafter finals follow), so the verdict travels through `output_key: repro` as text: `COMMAND`, `EXIT`, `LAST LINE`. The applier does not trust it. It runs the COMMAND itself once before its first edit, and takes it as the check only when its own run fails on an assertion or a behavior error. This makes the verdict verifiable by construction, and it gives a second, independent measurement of "fails before the edit" (V, section 3).

**(e) Rejected-prompt markers and lint.** `tools/pack_submission.py` `_REJECTED_PROMPT_MARKERS` holds one entry (the EXP-002 `search_similar_code` marker). EXP-063's prompt is not on it, and neither is this one. The validator reports 0 errors besides the 18.00 h gate that `--skip-budget-gate` demotes, and no new warning. The templater scans the instruction for braces, so the prompt has none besides `{plan?}`.

**(f) Base.** EXP-063 was built on `EXP-062/candidate-r`. `diff -ru EXP-062/candidate-r EXP-064/candidate-loc` touches only the reader prompt, the five drafter prompts and the reader yaml, so `candidate-loc`'s applier prompt and yaml are byte-identical to EXP-062's and EXP-063's applier edit ports with anchored edits.

**(g) What false-fires the lost-resolve row.** EXP-064-loc resolved `fastapi_14301` and `rich_3006` (summary). In the five pipeline runs on disk that have both tasks (EXP-063, 064, 066, 068, 069), with no selector in four of them, `rich_3006` was lost once (EXP-068: resolved in 4 of 5) and `fastapi_14301` once (EXP-063: 4 of 5, an empty patch), so **2 of 5 runs lose one of the two tasks with no check in the tree**. A bare "lost resolve" row would fire about 0.4 of the time on noise. Section 4 row 2 therefore counts a lost resolve only when the trace attributes it to the check.

### 1.3 References (EXP-064-loc, `experiments/EXP-064/loc/summary.jsonl`)
- First applier edit applies 6 of 8; empty patches 1 of 8 (rich_3468); mean wall 100.0 s; compactions 2 task-runs (fastapi_14605 1, rich_3468 1); the most calls on a task 19 of 45 (`n_calls`, including `transfer_to_agent`); 0 cap hits; `tool_free` 0 of 8; text-form calls 0.
- Resolved 2 of 8: `fastapi_14301`, `rich_3006` (recorded, not an endpoint).
- EXP-063 reproducer: first-turn tool call 0 of 8.

## 2. Design

One variable: the reproducer stage made tool-first (the opener, a one-line check command, a verdict that is a copy of a tool result, and the applier's own run of it). It is a package of four parts that cannot be varied separately at n = 8; section 7 item 3 says so.

| | value |
|---|---|
| tree | `experiments/EXP-073/candidate-repro/` = `cp -r experiments/EXP-064/candidate-loc` (committed `i/lf` blobs, so the copy equals the committed tree), then the edits below |
| new `prompts/reproducer.md` | line 1 is the opener: "Your first reply must be a run_command call, not text." with the reason (the applier runs the command again and compares). Section 1: the exact shape `PYTHONPATH=src:. python3 -c "from PKG.MODULE import NAME; r = NAME('INPUT'); assert r == EXPECTED, r"`, one line, single quotes inside, no `$`, backslash, backtick, newline, pipe, redirect, file or function; PKG.MODULE from the FILE of LOCATION 1; assert the behavior the issue asks for with the issue's strings copied exactly; it must exit 1 now and 0 once fixed. Section 2: read the last error line; an `AssertionError` or a behavior error is final; an import, name or syntax error or exit 0 allows one corrected re-run, then stop; no other program and no pytest. Then `{plan?}`. Section 3: the answer form `COMMAND:` (the last command, copied) / `EXIT:` (the exit_code the tool printed) / `LAST LINE:` (the last error line, or OK) / `END`; `FILE: unknown` takes one `git status --short` call and `COMMAND: none` |
| new `sub_agents/reproducer.yaml` | an E4B LlmAgent, `tools: [run_command]`, `include_contents: default`, `output_key: repro`, the reader's sampling file |
| `sub_agents/pipeline.yaml` | the stages become reader, reproducer, draft, applier (one comment line, one list line); the description line is unchanged |
| `prompts/applier.md` | Budget: "A reader, a checker and five writers ran before you, and the reader's and the checker's calls count toward the same budget." Team paragraph names the checker. A `Checker report: {repro?}` block follows the reader report. Section 1 becomes: if the checker report has a COMMAND other than `none`, run it once before any edit, exactly as written; if it exits 1 and its last error line is an `AssertionError` or an error about the behavior the issue names (not `ModuleNotFoundError`, `ImportError`, `NameError`, `SyntaxError`), it is the check and is reused unchanged for every draft; otherwise EXP-062's rule word for word. Sections 2 to 4 (undo on an assertion failure, keep on an uninformative failure, re-apply the first that applied when none passed, submit) are untouched |
| `sub_agents/applier.yaml` | one history comment line |
| unchanged | `agent.yaml`, `eval_config.yaml` (240 s, 45 calls, 8 min, 120 turns), `configs/`, `prompts/root.md`, `prompts/reader.md`, the five drafter prompts and yamls, `draft.yaml` |
| diff | `diff -ru experiments/EXP-064/candidate-loc experiments/EXP-073/candidate-repro`: 3 changed files (`prompts/applier.md`, `sub_agents/applier.yaml`, `sub_agents/pipeline.yaml`) and 2 new (`prompts/reproducer.md`, `sub_agents/reproducer.yaml`). The command is reproducible; the files are the committed pair of trees |
| lint | `python tools/validate_submission.py experiments/EXP-073/candidate-repro --official --strict --json`: 1 error, the 18.00 h gate, demoted by `--skip-budget-gate` (as EXP-061 to EXP-071); 2 warnings carried (the applier's `submit_patch`, `timeout_seconds` 240); no new warning; the official validator could not be imported (no `adk_submission`) |
| zip | `dist/EXP-073-repro.zip` (gitignored), 22 files, 17.3 KiB. **Packed with `--skip-budget-gate`: 8 min is above the 4.5 min packing gate (18.00 h nominal); the same override and reason as EXP-061 to EXP-071. Not an upload.** sha256 in section 8 |
| notebook | `notebooks/exp073_repro/`, kernel `rainm4/gemma4-exp073-repro`; EXP-071's build command with the zip, the `EXP_ID` and `--out` changed |
| cost | about 0.40 GPU-h; slot rule: D-010's two-kernel limit (see section 8 for the state at the push) |

Calls: the reader's worst pass was 13 in the EXP-064 tree; the reproducer adds at most 2; the applier adds one baseline run plus one run per applied draft and one undo per failed check (at most about 3 per draft). EXP-064-loc's most calls on a task was 19 of 45.

**Known limits of the design, written before the run.**
1. **The E4B must write a quoted one-liner in a native tool call.** A command with nested quotes can fail to parse (shell exit 2, a `syntax error` last line) or arrive as a malformed argument; EXP-066 found piped searches with quote and bracket characters failing in 7 of 9 runs where pipe-free ones had 0 of 12. The `LAST LINE` field and the class split of section 3 record it.
2. **Import reach.** `PYTHONPATH=src:.` covers a top-level package and `src/`. A package under another root (`lib/`, a namespace) is not covered, and a check may then fail on an import line (not tied to the issue, not counted in Fb).
3. **The ceiling on "fails for an issue reason".** A one-line assertion is natural for a utility function (`requests_7205`, `requests_7309`, `rich_3006`, `httpx_3672` parsers) and hard for a route or an app-level behavior (`fastapi_14301`, `fastapi_14448`, `fastapi_14605` need an app object and a client). I expect the realistic ceiling of Fb at about 4 to 5 of 8 and the prediction in section 4 at about 3 [I]. This sets the kill row (Fb at most 1) and the promote row (Fb at least 4).
4. **A wrong check selects wrongly** (EXP-063 limit 1). If the check fails a right draft 1 and passes a wrong later draft, the applier's undo rule does harm. The harm row names a lost resolve attributed to the check. If no draft passes, the applier re-applies the first draft that applied (EXP-062's rule), which is the EXP-064 behavior.
5. **A check that passes on the unfixed code** (an assertion that is already true) is a false `OK`; the applier's own baseline run exits 0, the check is not adopted, and EXP-062's rule applies. Recorded as a class.
6. **The stage holds a free shell.** `run_command` is a free shell (EXP-052), so "no file change" holds by the prompt; the harm row counts any reproducer command with a write or an install form and `scratch_in_patch`.
7. **Windows.** The applier's window gains the reproducer's events and the checker report; EXP-064-loc crossed 14,336 prompt tokens on 2 task-runs. Compactions are recorded.
8. **A nudge re-run** restarts the pipeline at the reader (`reference/routing.md`); the reproducer would run again on edited code. EXP-064 and EXP-068 had no nudges except rich_3006 (5 in EXP-068, a known case).
9. **n = 8 and the cohort.** Four tasks are src-layout or utility-shaped; `fastapi_14301` and `rich_3006` are the only resolves; the reader picks different regions between runs of an unchanged prompt.

## 3. Endpoints, fixed in advance

Per task, from `traces/` (authors `reproducer` and `applier` in `extra.author`), `task_results.jsonl`, `summary.jsonl` and the kernel log; by the EXP-068 method (Grep and line-number reads of `traces/`, no script).

- **T (tool-first).** Tasks where the first step authored by `reproducer` that holds a model call carries a native `run_command` tool call. A task whose reproducer step is text with no call, or a text-form call (a call-shaped fence in a final), is not in T and is listed.
- **X (executed).** Tasks where the reproducer got a `run_command` result with an exit code.
- **Last reproducer run** (the stage precedes every edit, so it is a before-edit run). Class by its exit code and the last line of its `stderr`:
  - **Fb (fails before, tied to the issue; the endpoint):** exit 1 and the last line begins `AssertionError`.
  - Recorded beside it, not an endpoint: **Fb-wide** = Fb, or exit 1 with an exception raised in a project frame (a `File "/workspace/..."` line below the `<string>` frame) whose type is not `ImportError`, `ModuleNotFoundError`, `NameError` or `SyntaxError`.
  - The other classes: pass (exit 0), import-class, name or syntax class, other exception from the `<string>` frame only, shell parse error, timeout, no run.
- **P (passes after the applied edit).** Among Fb tasks, those where the applier's last run of the COMMAND (its string equal to the reproducer's COMMAND after unescaping) after its last applied `edit_file` exits 0. Fb tasks where the applier ran no such command after an applied edit are counted as **unverified** and are not in P.
- **V (the applier's baseline reproduces).** Among Fb tasks, those where the applier's run of the COMMAND before its first `edit_file` has the same exit code and the same last line.
- **D (selection departure).** Tasks where the applier undid an applied draft after the check failed on an assertion and kept a later draft whose check exited 0. Reference: 0 of 16 in EXP-061/062 (EXP-063 section 1), 0 of 8 in EXP-063.
- **Fabricated verdict.** A report with a COMMAND other than `none` for which the reproducer made no `run_command` call, or whose COMMAND is not equal (after unescaping) to the command of one of its `run_command` calls, or whose EXIT is not the `exit_code` of that call.
- **Harm inputs.** Time, call and turn cap hits; empty patches (reference 1 of 8); mean wall against 100.0 s (EXP-064-loc), and the largest; calls against 45; `scratch_in_patch`; reproducer commands with a write or an install form (`>`, `tee`, `rm`, `mv`, `git checkout`, `sed -i`, `pip`); `n_text_form_calls` and `tool_free` (EXP-065), by author.
- **Secondaries, recorded.** Reproducer calls per task and its wall; the applier's first applied edit applies (reference 6 of 8); R1-type failed edits; compactions and the largest prompt against 14,336; resolves (reported, not an endpoint; paired against EXP-064-loc per task; `fastapi_14301` and `rich_3006` named).
- **Attribution (for the lost-resolve clause).** A lost resolve on `fastapi_14301` or `rich_3006` is **attributed** if on that task the trace shows an applier undo after a COMMAND failure, or a kept draft other than the first applied one chosen after a COMMAND run, or an applier edit made after a COMMAND failure that the EXP-064-loc run did not make. Otherwise it is unattributed.

**Power.** n = 8 reads counts, not rates. T at least 5 of 8 under a true first-call rate p: P = 0.886 at p = 0.75, 0.363 at p = 0.5; T of 4 or fewer is 0.114 at p = 0.75 and 0.005 at p = 0.9 (the reader's and the drafters' observed levels). Fb of 1 or fewer: 0.035 at p = 0.5, 0.255 at p = 0.3, 0.503 at p = 0.2. Fb of 4 or more: 0.637 at p = 0.5, 0.194 at p = 0.3, 0.056 at p = 0.2. So row 4 kills only a stage whose true Fb rate is about 0.5 or more, with a 25% false-kill at p = 0.3; row 5 is reached by a stage at p = 0.3 about one run in five.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Rows 1 to 3 are gates: any that holds is reported, and then rows 4 to 6 are **not read** (the numbers are still recorded). Rows 4 to 6 are first-match.

| # | outcome | reading |
|---|---|---|
| 1 | **Infrastructure.** Any of: an `err` with a traceback, a sandbox execution error or a compaction error; the tree does not run on some task; the root fails to transfer to `pipeline`; the reproducer stage produces no step on some task; the `repro` state renders empty in the applier's prompt on a task where the reproducer ended with a final text | A bug, not a reading. Name the task and the step. |
| 2 | **Harm.** Any of: **a lost resolve on `fastapi_14301` or `rich_3006` against EXP-064-loc that is attributed** (section 3; an unattributed loss is named and recorded and does not fire this row, since 2 of 5 unselected pipeline runs on disk lose one of the two); **2 or more empty patches of 8**; **any time, call or turn cap hit**; **mean wall over 150 s**; **any `tool_free` task or any text-form call, by any author**; **a fabricated verdict** on any task; a stray write (`scratch_in_patch` true, or a reproducer command with a write or an install form) | The stage costs more than it buys or it breaks the E4B's tool use. Name the tasks and counts. A task over 240 s is named, not a row. |
| 3 | **Not exercised.** **T at most 4 of 8** (the reproducer's first turn is a `run_command` call on 4 or fewer tasks) | The opener and the tool strip together did not make the stage call its tool. No decision on the reproducer, and no claim about which of the two changes failed (section 7 item 3). Record the first-turn kind per task (text, text-form call, a call of another tool, none). EXP-063's 0 of 8 stands as the reference. |
| 4 | **Kill.** Rows 1 to 3 did not fire and **Fb at most 1 of 8** | The one-line reproducer, with the opener, runs but does not produce a failing-before check tied to the issue on more than 1 of 8 tasks: the E4B cannot state a behavior check from the issue and the REGION in one line often enough to act as a selector here. The reproducer-as-selector route is killed on this carrier as a one-line `python3 -c` stage. A stronger form (a file, two attempts) is the lead's call, not decided here. |
| 5 | **Promote.** Rows 1 to 3 and 4 did not fire, and **T at least 6 of 8**, **Fb at least 4 of 8**, and among the Fb tasks **V on at least 3**, the applier's post-edit run of the COMMAND on at least 3 of them, and **P at least 1 with at least one Fb task whose post-edit run exits non-zero** | A tool-first reproducer produces a failing-before check on at least half the tasks, the applier reproduces its failure itself, and the post-edit result separates at least once in each direction: the stage creates a selection signal. A process reading, not a resolve claim: with 4 Fb tasks the mixed outcome is a bound, not a rate. It keeps the form as a candidate for D-010 round 5's fused tree and for the written finding (section 5). |
| 6 | **No decision.** Anything else, including Fb of 2 or 3, Fb at least 4 with every post-edit run exit 0 (a check that cannot fail after an edit tells nothing) or every post-edit run non-zero, V on fewer than 3 Fb tasks, T of exactly 5 | Record T, X, the classes, Fb, Fb-wide, V, P, D and the per-task commands. Resolves decide nothing. |

**Not rows, but binding:**
- Resolves at n = 8 are never an endpoint; six of eight must flip the same way for p < 0.05.
- A lost resolve that is unattributed is named with both runs' kept drafts; the paired reference is EXP-064-loc and the unselected pipeline runs (063, 066, 068, 069).
- D counts only departures made by the check (section 3). A kept draft other than the first applied one with no failing COMMAND run before it is recorded, not counted.
- If no prompt reaches 14,336 tokens, the compaction cost of the longer window is recorded as untested.
- The Fb-wide count and the class table are reported whatever row fires.

**Blind prediction.**
- T: 6 of 8 expected, P(row 3, T at most 4) about 0.2. The opener held on 8 of 8 reader runs and 36 of 40 drafter turns, and the one-tool declaration matches the drafters; the shell-quoted command is the new fragility.
- X about 6; Fb (strict) about 3 (the ceiling of limit 3 is 4 to 5); P among Fb about 1. P(Fb at least 4) about 0.25; P(Fb at most 1) about 0.22. V holds on most Fb tasks (the same command on the same unfixed code gives the same result).
- Mean wall about 125 s (range 105 to 160): the reproducer adds 1 to 2 calls and about 15 to 20 s, the applier adds a baseline run and a run per draft. The largest call count about 24 of 45.
- Row 1 about 0.06; row 2 about 0.28 (an attributed lost resolve 0.07, wall over 150 s 0.08, a fabricated verdict 0.08, 2 or more empties 0.10, tool_free or a text-form call 0.07; overlapping); row 3 about 0.15.
- Given rows 1 to 3 clear: row 4 about 0.25, row 5 about 0.15, row 6 about 0.60.
- A fabricated verdict is the sharper risk than a text first turn: a model that makes the call can still misquote the exit code.

## 5. What this does and does not license

**The screen can decide one of two things.**
- **Kill:** row 4, the route "a one-line, tool-first reproducer as the applier's check" on the E4B pipeline. Row 3 and row 6 kill nothing.
- **Promote:** row 5 only. What it promotes to: a candidate for D-010 round 5 (the fused keepers on a named base, with the no-lost-resolve condition on `fastapi_14301` and `rich_3006`), and an input for the written finding with the time-costed 31B port proposal that D-010's restated final check calls for. A 31B port would add a reproducer stage and an applier baseline run: C-018 measured about 27% wall cost for a file, the one-line form is the cheaper form, and the 31B has 13.8 s of room to the 10.5 h ceiling and 28.8 s to the 11 h gate, so the cost needs its own measurement.
- **The dev-48 endpoint it should carry, if the user ever buys one (not licensed here):** per task-run over the 48, the Fb rate (a check that fails before the edit for an issue reason) and, among those, the agreement between the post-edit check result and the grader's resolve (a check that exits 0 where the grade is resolved and non-zero where it is not), with the count of applier undos that changed the kept draft and the empty-patch count as the harm input. Resolves recorded, not the endpoint. About 27 informative dev-48 tasks as run (harness-stack), so the agreement is read as a count with its interval.

**Does not license:** any resolve or LB claim, an upload, a dev-48 run, a fused tree, or a claim that the opener alone (as against the tool strip) caused the first-turn call.

## 6. Exact commands

```
python tools/validate_submission.py experiments/EXP-073/candidate-repro --official --strict --json
python tools/pack_submission.py --src experiments/EXP-073/candidate-repro --out dist/EXP-073-repro.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed dist/EXP-073-repro.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-073-repro"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp073_repro/kaggle_eval_l4x4.ipynb
```

Then copy `notebooks/exp072_verify/kernel-metadata.json` to `notebooks/exp073_repro/kernel-metadata.json` and change only `id` (`rainm4/gemma4-exp073-repro`) and `title` (`gemma4-exp073-repro`); `build_notebook.py` writes a default metadata file, so the copy comes after the build. The push is `kaggle kernels push -p notebooks/exp073_repro`, bare, when the lead releases it.

Analysis, a separate job, after `kaggle kernels status rainm4/gemma4-exp073-repro` says COMPLETE:
1. `kaggle kernels output rainm4/gemma4-exp073-repro -p runs/EXP-073-repro/`, then move the nested `runs/EXP-073-repro/runs/EXP-073-repro/` up one level.
2. `python -I -X utf8 tools/analyze_traces.py runs/EXP-073-repro --cap-minutes 8 --max-calls 45`
3. `python -I -X utf8 tools/run_forensics.py forensics runs/EXP-073-repro`
4. Read `traces/` (authors `reproducer`, `applier`) with Grep and line-number reads for T, X, the class of the last reproducer run, Fb, Fb-wide, V, P, D, the fabricated-verdict test and the attribution test; copy `summary.jsonl` to `experiments/EXP-073/repro/summary.jsonl`; record the kernel wall in section 9.

## 7. Defects in this pre-registration, logged after the fact

1. **(Known at pre-registration.)** The tree is built by `cp -r` of the committed base and anchored `Edit` calls, not by a hash-verifying tool; `diff -ru experiments/EXP-064/candidate-loc experiments/EXP-073/candidate-repro` is the check (section 2).
2. **(Known at pre-registration.)** The lost-resolve row is the lead's, with one clause added by me: only an attributed loss fires it. The reason is section 1.2 (g): 2 of 5 unselected pipeline runs lose one of the two tasks on noise. An unattributed loss is recorded and named.
3. **(Known at pre-registration.)** Four parts change together: the opener, the one-line command form, the tool strip to `run_command`, and the applier's use of the COMMAND. A row 3 cannot say which part failed; a row 5 does not say which part carried it. The lead's brief names the first three as one variable; the fourth is EXP-063's inherited selector use, kept because the endpoint P needs the applier to run the command after the edit.
4. **(Known at pre-registration.)** P counts the applier's own post-edit run. An applier that skips the run leaves the task unverified, which lowers P and can make row 6 fire; it is a measure of the applier's compliance as well as of the check.
5. **(Known at pre-registration.)** The `src:.` prefix rests on a 31B trace and the harness source, not on a run of the E4B in this sandbox [I].
6. **(Known at pre-registration.)** Which of the 8 tasks a one-line check can express is a prior, not a measurement (limit 3); the blind prediction of Fb (about 3) uses it.

## 8. Built (below the line; nothing above changes)

---

- **Tree:** `experiments/EXP-073/candidate-repro/`, 22 files. `diff -ru --brief experiments/EXP-064/candidate-loc experiments/EXP-073/candidate-repro` lists exactly 3 changed files (`prompts/applier.md`, `sub_agents/applier.yaml`, `sub_agents/pipeline.yaml`) and 2 new (`prompts/reproducer.md`, `sub_agents/reproducer.yaml`).
- **Validator** (`--skip-budget-gate`, `--allow-warnings`): `RESULT: VALID (0 errors, 3 warnings)`: the applier's `submit_patch`, `timeout_seconds` 240, and the demoted 18.00 h gate. Official validator not importable. Lint clean.
- **Zip:** `dist/EXP-073-repro.zip`, 17.3 KiB, sha256 `0c3ce653a9b67426d3376ca24182900b73030a940f035c6d01d711a04302cc13` (re-checked with `sha256sum` at build). Packed with `--skip-budget-gate`; not an upload.
- **Notebook:** `notebooks/exp073_repro/kaggle_eval_l4x4.ipynb`; `TASK_IDS` = the 8 smoke-8 ids, `N_TASKS = 8`, `EXP_ID = "EXP-073-repro"`, `MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"`, `RUN_GOLD_CONTROL = False`, `RUN_AGENT = True`.
- **Kernel metadata:** copied from `notebooks/exp071_anchor/kernel-metadata.json` (E4B model source `google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2`), `id` `rainm4/gemma4-exp073-repro`, `title` `gemma4-exp073-repro`, nothing else changed.
- **Slot check at build, 2026-11-11:** `rainm4/gemma4-exp071-anchor` RUNNING and `rainm4/gemma4-exp072-verify` RUNNING, so D-010's two-kernel limit holds and the kernel is not pushed.

## Status

PUSHED 2026-11-11 from commit 5baad58 (the build was held until EXP-071 and EXP-072 were COMPLETE and both slots were free). Kernel `rainm4/gemma4-exp073-repro` version 1, zip sha256 `0c3ce653a9b67426d3376ca24182900b73030a940f035c6d01d711a04302cc13`, status RUNNING at the first check. Next: when `kaggle kernels status rainm4/gemma4-exp073-repro` says COMPLETE, the analysis job of section 6.
