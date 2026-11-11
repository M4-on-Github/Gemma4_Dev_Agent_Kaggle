# EXP-071 — The reader's LINES come from a printed line number, not a count by eye (smoke-8 screen, D-010 round 1)

**Date:** 2026-11-11
**Type:** smoke-8 screen, ~0.38 L4x4-h (EXP-068 0.38 GPU-h at kernel wall about 1369 s; the reader adds at most five `run_command` calls per task, each about 1 s). One push, no upload, no dev-48.
**Cohort:** smoke-8
**Ladder:** L2. L0 and L1 are EXP-068 section 10 (the window-miss desk check, zero GPU): on the 3 window-miss tasks the reader's LINES lay 7 to 15 lines (nearest gap) from the target in the same file, so the miss is an anchor miss, not a localization miss.
**Pre-registered:** this file is committed before the push. Sections 3-5 are written blind and are not revised.
**Serves:** D-010 round 1 of the five E4B pipeline tweak rounds approved by the user on 2026-11-11 (`knowledge/user-decisions.md`; D-009 ended by its two-rounds rule).
**Relates:** EXP-068 (the base tree, `candidate-read`, and the reference run), EXP-066 (the search-form lesson: an exact pipe-free recipe works, 12 of 12 pipe-free searches had no malformed-argument error, 7 of 9 piped ones had), EXP-069 (applier hunks are not in this tree), EXP-064 (the reader that gave LINES with a REGION).

## 1. Why this, now (zero GPU)

### 1.1 What EXP-068 section 10 measured

The drafters of EXP-068 read their own window, the reader's first LINES number minus 5 to its last plus 5, and copy OLD from that read. On 3 of 8 tasks the window did not contain the drafted target:

| task | reader LINES | target in the file | nearest gap | window (LINES -5..+5) |
|---|---|---|---|---|
| fastapi_14448 | 67-71 | 78-85 | 7 lines before | 62-76 |
| rich_3468 | 2081-2119 | 2062-2066 | 15 after | 2076-2124 |
| rich_3006 | 95-96 | 79-82 | 13 after | 90-101 |

All are the same file as the target, 7 to 15 lines off, in both directions, so a fixed shift would not repair it. `read_file` returns its `content` with no line-number prefix (checked in the rich_3006 trace), so the reader counts by eye. On fastapi_14448 and rich_3006 the reader's `git grep -n` printed no line number for the change site. On rich_3468 the reader's own grep printed `console.py:2063`, its draft thinking said 2055-2063 and then 2055-2139, and its final report said 2081-2119: the right number was in its context and was not used. The base reader prompt already says to take LINES "from the `start_line` and `end_line` of your `read_file` call, or from the line numbers `git grep -n` printed"; that wording is implied, not a command shape, and a read of 1-149 or 2000-2149 gives start and end numbers far wider than the region, so the reader narrowed by eye. In EXP-064 and EXP-066 the same drift existed (the reader's LINES were 5 to 9 lines off on 3 of 12 single-location tasks, 44 off on 1) and cost nothing because the REGION text carried the code; EXP-068 removed the REGION and kept the drift.

### 1.2 The change

One variable: **the source of the reader's line numbers.** The reader prompt gets one exact command per location, run after the lines are opened, with no pipe:

`git grep -n -F -e 'FIRST' -e 'LAST' -- path/to/file.py`

FIRST is a piece (at most 40 characters, no `'`) of the first line of the code to change and LAST a piece of its last line, each copied from the `read_file` result. Every hit prints as `path:number:line` (checked on a single-file `git grep -n` result in the EXP-066 requests_7309 trace: `src/requests/utils.py:504:def ...`); the number is the one between the first and second colon. The rule for the report: LINES is the number printed for FIRST, a hyphen, the number printed for LAST, and "write no line number that you did not see printed"; if the command printed nothing after two tries, LINES falls back to the `read_file` call's `start_line` and `end_line` (the base behavior), so a failed command does not produce a report with no LINES. The recipe and the rule together are one variable (the EXP-057 and EXP-066 lesson: the literal command shape is what works).

Choices made from the evidence:
- **No pipe.** The base prompt's own search line keeps `| head -20` (not touched: it is line 10 of the prompt and EXP-066 owns it). The new command has no `|`, as EXP-066's pipe-free form had no malformed-argument errors in 12 of 12.
- **`-F` and single quotes.** EXP-066 saw `git grep` return no match twice on a token holding quote and bracket characters. `-F` makes brackets and dots literal; single quotes make `"`, `$`, backtick and backslash literal; the only forbidden character is `'`. The command is a read-only `git grep -n`, already allowed by the reader prompt's line 3.
- **Two `-e` pieces in one command** give both boundary numbers in one call. A one-line change takes one `-e`. A piece that matches several lines prints all of them; the reader is told to take the one inside the region it opened.
- **Output bound.** `run_command` returns stdout truncated at `max_stdout_chars` (`swegemma/tools/execution.py:54-56`); a single-file pathspec bounds the hit count. The command runs in the workspace, so a relative path works.
- **Repo-agnostic and the lint.** No repository words, no pip, network, subprocess or URL; the validator reports no new warning (section 2).

What is not changed: the drafters' prompts, the drafter window (LINES -5 to +5), the five drafter yamls, the applier, `agent.yaml`, `eval_config.yaml`, sampling. A wider window is a separate candidate held back.

### 1.3 References (EXP-068, section 9)

Window contained the drafted target: **4 of 8 held** (fastapi_14301, requests_7205, fastapi_14605, httpx_3672), **3 of 8 missed** (fastapi_14448, rich_3468, rich_3006), **1 of 8 had no window** (requests_7309: the reader's report had no FILE or LINES, a JSON-fence final). The lead's wording was "5 of 8 contained"; section 9.3 names four tasks as held and requests_7309 has no window to contain anything, so the reference here is 4 of 8, and a task without a window counts as not contained. First applier edit applies 6 of 8; drafter first turn `read_file` 36 of 40 (4 `NO DRAFT` or text-line on requests_7309); A (d) 0 of 40; 16 of 35 drafted OLDs not in the drafter's own read (14 window misses on 3 tasks, 2 form faults); R1-type failures 5 on 1 task-run; G 7 of 8; empties 1 of 8; mean wall 110.3 s; compactions httpx_3672 3, fastapi_14605 1, rich_3468 1; nudges 5 (all rich_3006); resolved 1 of 8; reader reports with no FILE or LINES: 2 of 8 task-runs (requests_7309; rich_3006's second pass).

## 2. Design

| | value |
|---|---|
| tree | `experiments/EXP-071/candidate-anchor/` = `cp -r experiments/EXP-068/candidate-read` (committed, `i/lf` blobs), then the two edits below |
| `prompts/reader.md` | **one added bullet in section 2** (after "Open the matching region ... You must open the lines you will quote.", before "You may do follow-up searches"): the sentence that `read_file` prints no line numbers, the exact command, the FIRST and LAST rule, the several-hits and no-hit rules. **`LINES:` line of section 4 rewritten**: the number printed for FIRST then the number printed for LAST, "write no line number that you did not see printed", the fallback to the read call's `start_line` and `end_line` after two empty tries. Lines 1-12 other than the added bullet and the rest of the prompt are byte-identical to EXP-068's |
| `sub_agents/reader.yaml` | one history comment line; nothing else |
| everything else | byte-identical to `experiments/EXP-068/candidate-read/` (18 files) |
| diff | `diff -ru experiments/EXP-068/candidate-read experiments/EXP-071/candidate-anchor` shows exactly two changed files, `prompts/reader.md` (+1 added bullet, 1 changed line) and `sub_agents/reader.yaml` (+1 comment line). The added bullet and the changed line are the text of section 1.2 in the prompt's own words and are in the committed tree |
| lint | `python tools/validate_submission.py experiments/EXP-071/candidate-anchor --official --strict --json`: 1 error, the 18.00 h gate (`max_time_minutes` 8), demoted by `--skip-budget-gate`; 2 warnings carried (the applier's `submit_patch`, `timeout_seconds` 240); the official validator is not importable here; no new warning |
| eval config | `timeout_seconds` 240, `max_tool_calls` 45, `max_time_minutes` 8, `max_turns` 120 (EXP-068's) |
| zip | `dist/EXP-071-anchor.zip`, sha256 in section 8; 20 files. Packed with `--skip-budget-gate`: 8 min is above the 4.5 min packing gate (18.00 h nominal; the same override and reasoning as EXP-061, EXP-062, EXP-064, EXP-066, EXP-068, EXP-069). **Not an upload.** |
| notebook | `notebooks/exp071_anchor/`, kernel `rainm4/gemma4-exp071-anchor` |
| cost | ~0.38 GPU-h. No kernel is live at the time of writing (the lead's statement). The experimenter may push one later; the total stays at 2 or fewer |

**Known limits of the design, written before the run.**
1. **The reader may not run the command.** It is a bullet in section 2, not the opening rule; the E4B follows exact opening rules (the first-call rule held 8 of 8 in EXP-064 and EXP-066) and was not seen to run a two-`-e` `git grep -n -F` in any local trace. Row 3 measures it.
2. **The command can fail or mislead.** A piece that matches the wrong line (a common line such as `return x`) gives a number outside the region; a piece with a stray `'` breaks the shell quoting; the model may write two `-e` badly (an `-e` with no string, a missing `--`). Each is counted by kind in section 9; a failed command falls back to the read call's start and end, which is the EXP-068 behavior.
3. **The base search line still has `| head -20`.** EXP-066 found 7 of 9 piped searches had a malformed-argument error; it is not touched here and a failed first search can end in a report with no FILE (2 of 8 in EXP-068). Row 2 counts reports with no FILE.
4. **The target is where the applier edited, not the gold location.** The endpoint is read against the drafted target (the same method as EXP-068 section 10); the applier's edit follows the drafts, which follow the window. A window that contains the target the applier chose when the drafts came from that window is partly circular; the numbers in section 9 give the distance per task so the reader of the result can see it.
5. **The reader varies between runs of an unchanged prompt** (EXP-061, EXP-062, EXP-066): a different file or region on a task is a location change, not an anchor effect; it is named by task and counted in the endpoint only through the window rule.
6. **n = 8.** The endpoint is a count of tasks (section 3 gives its noise).

## 3. Endpoints, fixed in advance

Per task, from `runs/EXP-071-anchor/traces/`, `task_results.jsonl`, `summary.jsonl` and the kernel log, by Grep and line reads as in EXP-068 section 3 and section 10.

- **W (primary, the window contains the target).** Per task, W = 1 when the first applied `edit_file` (its diff hunk: the first changed line is the hunk start plus the leading context lines, the last changed line likewise) lies entirely inside the drafter window of at least one location of the reader's report on the same file, where the window is the first LINES number minus 5 (at least 1) to the last plus 5. A task whose reader report has no FILE or LINES, or whose applier applied no edit, has W = 0 and is named. **Reference 4 of 8** (section 1.3). The distance is reported per task as in EXP-068 section 10: the target's range, the reader's LINES, the start offset and the nearest gap.
- **X (the numbered command, row 3 and the compliance counts).** A task **runs the command** when the reader makes at least one `run_command` whose command string holds `git grep` with `-n`, `-F` (alone or in a flag cluster such as `-nF`), at least one `-e`, and the path of a FILE named in the report. Counted per task: the number of tasks that run it; per location whether its LINES numbers are numbers printed in that command's output (**printed-source compliance**); the command's failures by kind (shell-quote, a missing pathspec, an error result, a no-match).
- **Secondaries (recorded; they decide nothing alone):** OLD not in the drafter's own read, of the drafted OLDs (reference 16 of 35); first-edit-applies E1 (reference 6 of 8); R1-type failed edits (reference 5 on 1 task-run), by the EXP-068 method; A, S, E, M counts apart; empties (reference 1 of 8); mean wall (110.3 s); compactions per task and the applier's first prompt tokens (references above); G and G1; nudges; resolved (never an endpoint).
- **Harm inputs:** empties; time, call and turn cap hits; mean wall; `tool_free`; text-form calls by any agent (counted two ways: `n_text_form_calls` and a bare `read_file(...)` or `run_command(...)` line in a final text; both are reported and the row below uses **either**, the EXP-068 definition defect not repeated); the reader's and the drafters' first turn; reader reports with no FILE or LINES; `scratch_in_patch`; a `read_file` path outside `/workspace`; the largest call count against 45.

Noise at n = 8, stated in the rows: W is a count of Bernoulli tasks; at a true rate p the chance of W >= 7 is 0.035 (p 0.5), 0.135 (p 0.625) and 0.657 (p 0.85); of W <= 4 it is 0.637 (p 0.5), 0.194 (p 0.7) and 0.022 (p 0.85). Resolves are not an endpoint: 6 of 8 must flip the same way for p < 0.05 (EXP-020 section 3).

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Rows 1 to 3 are gates: if any holds it is reported and the endpoint rows 4 to 6 are **not read** (the numbers are still recorded). Rows 4 to 6 are first-match.

| # | outcome | reading |
|---|---|---|
| 1 | **Infrastructure.** Any of: an `err` with a traceback, a sandbox execution error, a summarizer or compaction `ValueError`; a blank or crashed run; the root fails to transfer to `pipeline`; a `draft_N` state key lost | A bug, not a reading. Name the task and the step. |
| 2 | **Harm.** Any of: **empty patches 3 or more of 8**; any time, call or turn cap hit; **mean wall over 150 s**; any `tool_free` task; **a text-form call by any agent, either counting way** (the reader's JSON fence on requests_7309 in EXP-068 would have fired it: that was 1 of 8 and a known base fault, so row 2 here reads **2 or more tasks with a text-form call by any agent**); **the reader's first reply is not a native tool call on 2 or more of 8 tasks**; **fewer than 30 of the 40 drafter turns open with a `read_file` call** (EXP-068 36 of 40; a legitimate `NO DRAFT` for a report with no FILE or LINES counts as not opened and is listed); **a reader report with no FILE or LINES on 4 or more of 8 tasks** (EXP-068 2 of 8; at a rate of 0.25 the chance of 4 or more is 0.11); fabricated OLD (an OLD with no earlier `read_file` in the drafter's own events) on 8 or more of 40 turns; `scratch_in_patch` on any task or a `read_file` outside `/workspace` | The change costs more than it buys or breaks the E4B's tool use. Name the tasks and counts. A task over 240 s is named, not a row. |
| 3 | **Not exercised.** The reader runs the numbered command (section 3, X) on **4 or fewer of 8 tasks** | The recipe did not move the reader; the line-number source did not change, so W says nothing about it. No kill, no promote. The lead decides whether to put the command at the head of the prompt (a first-call rule) or to take the window-width candidate. |
| 4 | **Kill.** Rows 1 to 3 did not fire, and **W <= 4 of 8** | With the command run on 5 or more tasks the window still held the target on no more tasks than the reference. Noise: if the true rate with the command is 0.5 (no effect) this row fires 64% of the time; if it is 0.7 it fires 19%, and 0.85 it fires 2%, so a kill says "no gain large enough for n = 8 to see", not "no gain". The form is dropped as the base for the later rounds, which then stay on EXP-068 `candidate-read`; the window-width candidate is next. |
| 5 | **Promote.** Rows 1 to 4 did not fire, and **W >= 7 of 8**, with the command run on **6 or more of 8** tasks | The printed number carried LINES to the target on 7 or more tasks against the reference 4. Noise: if nothing changed (p 0.5) this chance is 0.035, at the lead's 5-of-8 reference rate (p 0.625) it is 0.135, so promotion is a bound on a mechanism (LINES now come from a printed number), not an estimate of its size; the three tasks that missed in EXP-068 (fastapi_14448, rich_3468, rich_3006) are named whatever the row, since a reader that picked a new location on them is not an anchor result. Promote = the numbered LINES become part of the base tree for rounds 2 to 5 of D-010. |
| 6 | **No decision.** Anything else (W = 5 or 6 of 8, or W >= 7 with the command run on exactly 5) | Record per task; the form rides on as a free rider only if the harm gates are clear and the lead so decides. Resolves decide nothing. |

**Not rows, but binding:**
- Resolves are recorded and are never an endpoint.
- Secondaries (OLD not in the read, E1, R1-type, empties, wall, compactions) are reported next to W and read against their references; none of them fires a row.
- A fall-back LINES (the read call's start and end) counts as a LINES for W; printed-source compliance is reported separately so a W gain with no printed numbers is seen as such.
- requests_7309, whose reader gave no FILE or LINES in EXP-068, is named whatever the row.

**Blind prediction.**
- The reader runs the command on 5 or more of 8 tasks (row 3 not firing): about 0.65. The reader opens with a tool call (8 of 8 in EXP-064 and EXP-066), and a literal command shape was followed in EXP-057 and EXP-066; the two-`-e` form and single quotes are new to the E4B.
- Printed-source compliance on the locations of the tasks that ran the command: about 0.8 (one in five takes a number from a wrong hit or counts by eye).
- Row 2 (harm): about 0.2. Row 1: about 0.05.
- Given rows 1 to 3 clear: W >= 7 about 0.3 (row 5), W <= 4 about 0.15 (row 4), row 6 about 0.55; the most probable single outcome is W = 5 or 6.
- Mean wall about 118 s (range 100 to 150): up to five extra `run_command` calls per task and a longer prompt; 0 cap hits; largest call count about 24.

## 5. What this does and does not license

**The screen can decide one of two things.**
- **Kill (row 4):** the numbered-command form of the reader's LINES, on this tree. The later rounds then stay on EXP-068 `candidate-read` and the window-width candidate is the next round.
- **Promote (row 5):** the numbered LINES as part of the base tree for D-010's later rounds. The endpoint a dev-48 arm would carry, if the lead ever buys one: **the window-contains-target rate W per task over the 48** (paired against a rerun of EXP-068 `candidate-read`), with first-edit-applies and the OLD-not-in-the-read count as bounds and empties as the harm input; **resolves recorded, not the endpoint** (n = 48 cannot see the move that edit reliability would make). No dev-48 run is licensed by this screen or by this file; it needs the user's word and a critic `prereg`.

**Does not license:** any resolve or LB claim; any upload or dev-48 run; a statement that a window that holds the target makes a better fix; a claim about the reader's location quality beyond W and the per-task distances (the target is the applied edit, not the gold patch).

## 6. Exact commands

```
python tools/validate_submission.py experiments/EXP-071/candidate-anchor --official --strict --json
python tools/pack_submission.py --src experiments/EXP-071/candidate-anchor --out dist/EXP-071-anchor.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed dist/EXP-071-anchor.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-071-anchor"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp071_anchor/kaggle_eval_l4x4.ipynb
kaggle kernels push -p notebooks/exp071_anchor
```

Analysis, a separate job, after `kaggle kernels status` says COMPLETE:
1. `kaggle kernels output rainm4/gemma4-exp071-anchor -p runs/EXP-071-anchor/`, then flatten.
2. `python -I -X utf8 tools/analyze_traces.py runs/EXP-071-anchor --cap-minutes 8 --max-calls 45`.
3. `python -I -X utf8 tools/run_forensics.py forensics runs/EXP-071-anchor` and `compare runs/EXP-068-read runs/EXP-071-anchor`.
4. X, W and the per-task distance, the secondaries and the harm inputs by Grep and line reads of `traces/` (the method of EXP-068 sections 9 and 10). Also recompute EXP-068's W by the section 3 rule (`runs/EXP-068-read/traces/`) and report it beside the pre-registered 4 of 8 (section 7 item 7).

## 7. Defects in this pre-registration, logged after the fact

1. **(Known at pre-registration.)** The reference for W is 4 of 8, not the lead's 5 of 8, for the reason in section 1.3 (requests_7309 had no window). The endpoint rows use W >= 7 and W <= 4, which are one task apart under either reference.
2. **(Known at pre-registration.)** The thresholds (W >= 7, W <= 4, 30 of 40, 4 reports without a FILE, 2 text-form tasks) are chosen, with their noise stated in rows 2, 4 and 5, not derived from a model of the E4B's reader.
3. **(Known at pre-registration.)** The tree was built by `cp -r` plus two edits; `tar` is outside this agent's commands, so no `git archive` repack was run (as EXP-068 item 2).
4. **(Known at pre-registration.)** The numbered command has no precedent in an E4B trace (section 2, limit 1); the screen tests it and does not assume it works.
5. **(Found 2026-11-11 after the pre-registration commit 27fee48 and before the push; the readings in section 4 are unchanged.)** The first text of the added reader bullet and of section 1.2 said each hit prints as `number:line` with the number before the first colon. A `git grep -n` with a pathspec prints `path:number:line`. Corrected in `prompts/reader.md` and section 1.2 (the number is between the first and second colon), the tree was re-validated, re-packed and re-built; the sha256 in section 8 is the corrected zip's, and the sha in the README row and section 2 is updated. Rows, thresholds and endpoints are not touched.
6. **Overlap of two row-2 clauses (found before the push, not retrofitted).** Row 2 fires on "4 or more reports with no FILE or LINES" and on "fewer than 30 of 40 drafter first calls", where a `NO DRAFT` for a report with no FILE counts as not opened. Each report without a FILE costs about 5 drafter first calls, so 3 such tasks give about 25 of 40 and fire the second clause before the first. The overlap is **intended as written**: the second clause is the stricter one and reads "fewer than 30 of 40 open with a call" whatever the cause; the section 9 job names which tasks produced the shortfall.
7. **W's reference was not measured with W's rule.** The reference 4 of 8 is EXP-068 section 9.3's "window held" tasks (the drafters' OLD matched their read), not "the first applied hunk lies inside a window". The analysis job recomputes EXP-068's W by the section 3 rule (the traces are on disk) and reports both; rows 4 and 5 key on the pre-registered 4 of 8 and 7 of 8 as written, and a recomputed reference that differs is reported beside them, not used to move a row.

## 8. Built (below the line; nothing above changes)

---

- **Changed files vs EXP-068 `candidate-read`:** two (`prompts/reader.md`, `sub_agents/reader.yaml`), as section 2.
- **Validator** (`--official --strict`): 1 error, the 18.00 h gate, demoted by `--skip-budget-gate`; 2 warnings carried from EXP-068; no new warning. The official validator could not be imported.
- **Pack:** `RESULT: VALID (0 errors, 3 warnings)`, PACK OK, 20 files, `dist/EXP-071-anchor.zip` (gitignored). **sha256 `3250d189c6b21a9bbd34db13d433be3e5db66da36f461f07106eaa574e6889bc`** (the corrected zip of section 7 item 5; the first pack, `6569da25...ace4`, carried the `number:line` wording and was never pushed).
- **Pre-registration commit:** 27fee48 (this file, the candidate tree, the README row); the section 7 items 5 to 7 correction is the next commit.
- **Notebook:** `notebooks/exp071_anchor/`, built with the section 6 command (`TASK_IDS` = the 8 smoke-8 ids, `N_TASKS` 8, `RUN_AGENT` True). `kernel-metadata.json` is EXP-069's with only `id` and `title` changed, to `rainm4/gemma4-exp071-anchor`. Nothing was copied to `out/submission.zip`.
- **Kernel id for the push:** `rainm4/gemma4-exp071-anchor`, directory `notebooks/exp071_anchor`.
