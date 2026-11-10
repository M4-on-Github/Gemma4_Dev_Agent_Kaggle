# EXP-066 — Reader search command form over the EXP-064 tree (smoke-8 screen, D-008 follow-up)

**Date:** 2026-11-10
**Type:** smoke-8 screen, ~0.35 L4x4-h (EXP-064 measured 0.353 GPU-h at kernel wall 1270.2 s; the reader may make one more search call per task). One push, no upload, no dev-48. This job is zero GPU and builds only; the lead releases the push.
**Cohort:** smoke-8
**Ladder:** L2. L0 and L1 are section 1 (counted from `runs/EXP-064-loc`, `traces/`, and EXP-064 section 10).
**Pre-registered:** this file is committed before the push. Sections 3-5 are written blind and are not revised.
**Serves:** D-008 rank 2 (`knowledge/directions/D-008-e4b-loop-restart-pipeline-stages.md`), the follow-up to EXP-064 section 10: whether the reader's failed searches, not the prompt's wording about several locations, are why it listed one place.
**Relates:** EXP-064 (this arm's baseline tree, row 3 fired, 6 of 8 tasks with L < 2), EXP-062, EXP-063 (the reproducer-selector arm; fused only in a later round, so the applier stays byte-identical here), EXP-065 (the text-form counter).

## 1. Why this, now (counted from `runs/EXP-064-loc/traces/`, zero GPU)

EXP-064 section 10 found that 7 of the 21 reader `run_command` calls ended in one error kind: a `head` invocation whose count is detached from its flag (the prompt's own search line carried `| head -20`, and the reader wrote it with a space). They fell on fastapi_14448 (3 of 4 searches), fastapi_14301 (2 of 3), rich_3468 (1 of 4) and rich_3006 (1 of 3), all four tasks with L = 1, and on none of the tasks with L >= 2. Of the 6 tasks with L < 2, 4 had one candidate file in view (group (i)) and 2 saw several (group (ii)).

**Which command forms the E4B already ran without error.** The 21 reader searches of EXP-064 split by form:

| form | calls | malformed-argument error | returned hits | no match (exit 1 or empty) |
|---|---|---|---|---|
| a pipe into `head`, count attached (`head -N`) | 2 | 0 | 1 | 1 |
| a pipe into `head`, count detached (`head - N`) | 7 | **7** | 0 (one result still showed 1 hit line in its details) | 0 |
| no pipe, `git grep` with a directory or glob pathspec | 8 | 0 | 3 | 5 |
| no pipe, `grep` or `ls` on one named file | 4 | 0 | 4 | 0 |

So **12 of 12 pipe-free searches had no malformed-argument error** and 7 of the 9 piped ones had. Pipe-free tasks: requests_7309, requests_7205, fastapi_14301, rich_3468 (3 of its 4), rich_3006 (1), httpx_3672 (all 4), fastapi_14605 (1). The pipe-free `git grep -n "TOKEN" -- <directory>` or `-- <path>` form is the one used by requests_7309, requests_7205 and httpx_3672 with hits and no error. A single-file `grep -n` / `grep -A` form ran without error on fastapi_14301 and rich_3468 (3 calls).

**What is not covered by that count.** `git grep -l` (the file-list flag) was used by no E4B in any local trace (a grep over every `runs/` trace tree for `-l`, `-n -l`, `--files-with-matches` and `-c` returned 0 files). It is a plain `git` flag and cannot fail as a malformed `head` argument, but the E4B has not been seen to use it. Whether it follows the two-step form is part of what this screen tests; section 3 records it.

Reference outcomes (EXP-064): reader searches failing 7 of 21 (tasks with at least one failed search: 4 of 8, namely fastapi_14448, fastapi_14301, rich_3468, rich_3006); searches returning no match 6 of 21; L >= 2 on 2 of 8 (httpx_3672, fastapi_14605); F >= 2 on 2 of 8; any-gold 7 of 8, first-gold 5 of 8; empty patches 1 of 8; mean wall 100.0 s; 0 cap hits; text-form tool calls 0 of 8. The gold files are the table of EXP-064 section 1.

## 2. Design

One variable: the reader's search command form. The prompt's search line gives a command with no `|`: first `git grep -l "TOKEN" -- '*.py'` to list the files, then `git grep -n "TOKEN" -- path/to/file.py` in one file. Everything else is EXP-064's `candidate-loc` as committed.

| | value |
|---|---|
| tree | `experiments/EXP-066/candidate-srch/` = `cp -r experiments/EXP-064/candidate-loc` (the tree is clean, `git ls-files --eol` shows all 20 blobs `i/lf w/lf`, so the copy equals `git -c core.autocrlf=false archive`; `tar` is not available to this agent), then two edits in `prompts/reader.md` and one comment line in `sub_agents/reader.yaml` |
| diff | `diff -ru experiments/EXP-064/candidate-loc experiments/EXP-066/candidate-srch` shows 2 files. `prompts/reader.md`: the tool-list sentence drops `head`, drops `-n` from `git grep`, and gains "Run one program per command and do not chain programs together with `\|`"; the one search bullet "Search once with ... `\| head -20`" is replaced by the two-step no-pipe form, "if a search prints nothing, try a shorter or different token", and "if a result is too long, search again in a single file instead of cutting the output". `sub_agents/reader.yaml`: one history comment line (EXP-066, no behavior). No other line changes: the report format, the read cap of 8, the five drafter prompts, the applier, `agent.yaml`, `eval_config.yaml`, `configs/` and `prompts/root.md` are byte-identical |
| lint | `python tools/validate_submission.py experiments/EXP-066/candidate-srch --official --strict --json`: 1 error, the 18.00 h gate, which `--skip-budget-gate` demotes (the same as EXP-064); 2 warnings, both carried from EXP-064 (the applier's `submit_patch`, `timeout_seconds` 240). No new warning, so the prompt is repo-agnostic and mentions no pip, network, subprocess, mcp or URL |
| eval config | `timeout_seconds` 240, `max_tool_calls` 45, `max_time_minutes` 8, `max_turns` 120 (EXP-064's) |
| zip | `dist/EXP-066-srch.zip`, sha256 in section 8. Packed with `--skip-budget-gate` because 8 min is above the 4.5 min packing gate (18.00 h nominal, the same override as EXP-061, EXP-062 and EXP-064). **Not an upload.** |
| notebook | `notebooks/exp066_srch/`, EXP-064's build command with only the zip and `EXP_ID` changed; kernel `rainm4/gemma4-exp066-srch` |
| cost | ~0.35 GPU-h; no slot |

**Known limits of the design, written before the run.**
1. **A search can still fail** by a route this form does not close: a wrong path in the second step, a regex character in the token (EXP-064 httpx_3672's no-match came from one), or a pipe typed anyway. The endpoint counts those; the screen does not assume the failure is zero.
2. **The prompt gives the reader more to do before it reads** (a file-list search and then a line search); the harm row covers the wall and the reader's share of the 45 calls.
3. **The prompt still allows one honest location.** If the files named by `-l` are many, the reader may open one and list one. Fixing the search does not force several places; row 5 reads that outcome.
4. **n = 8 and the reader's run-to-run variation.** In EXP-061, EXP-062 and EXP-052 the reader's picks varied on fastapi_14605 and fastapi_14448 without any prompt change, so a change in L on one task is not read alone.

## 3. Endpoints, fixed in advance

Per task, from `official/traces/`, `task_results.jsonl`, `summary.jsonl` and the kernel log, by the same grep method as EXP-064 sections 9 and 10 (no script is allowed to this agent):

- **S (reader search failures).** Reader `run_command` calls whose result is `"status": "error"` with a non-empty error message (a malformed argument, an unknown path, an unsupported flag). A no-match (exit 1 with an empty message, or exit 0 with empty output) is counted apart, not as a failure. Reported as calls (reference 7 of 21) and as tasks with at least one failed search (reference 4 of 8). Also the form used: reader calls with a `|`, reader calls with `git grep -l`, reader calls with `git grep -n` in one file.
- **L (locations listed).** The number of `LOCATION` blocks with a REGION in the reader's final report, and a missing `END` or a report-less reader recorded as in EXP-064.
- **(i)/(ii) split.** For the tasks with L < 2: (i) the reader saw one candidate file only (opened plus named by searches), (ii) it saw several and listed one. Reference 4 and 2 (EXP-064 section 10).
- **F, G and G1 as in EXP-064 section 3.** F distinct target files across the 5 drafts; G any draft on a gold file; G1 on the first gold file by the EXP-064 convention. References F >= 2 on 2 of 8, G 7 of 8, G1 5 of 8.
- **Text-form counter.** `n_text_form_calls`, `tool_free` and the four aggregates now in `analyze_traces.py` (EXP-065): tasks with at least 1 text-form call and tool-free tasks. Reference 0 of 8 and 0 of 8.
- **Harm inputs.** Time, call and turn cap hits; empty patches (EXP-064: 1 of 8; the base maximum is 2); mean wall against 100.0 s (EXP-064), 89.5 s (EXP-061), 89.2 s (EXP-062); the reader's calls and `read_file` calls against the prompt's 8; compactions and the largest prompt against 14,336.
- **Movable tasks, reported separately:** `fastapi_14448` (reference: reader saw `fastapi/routing.py` only, no gold file, 3 of 4 searches failed) and `rich_3468` (reference: reader opened `console.py` and `logging.py`, listed one, 6 of 6 applier edits failed, empty patch): the searches' form and result, the files seen, L, the 5 draft targets, whether a draft is on a gold file, and the applier's edit failures by kind.
- **Errors.** `err` per task as in EXP-064.
- **Recorded only.** Resolves (never an endpoint), the draft the applier kept, the applier's edit failures.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

First match governs. "Searches fixed" means tasks with at least one failed reader search (S) number below 3 of 8.

| # | outcome | reading |
|---|---|---|
| 1 | **Infrastructure.** Any of: an `err` with a traceback, a sandbox execution error or a compaction error; the tree does not run on some task; the root fails to transfer to `pipeline`; a drafter request fails to build from the report | A bug, not a reading. Name the task and the step. |
| 2 | **Harm.** Any of: **empty patches above 2 of 8** (3 or more); any time, call or turn cap hit; **mean wall over 150 s**; **any tool-free task** (`tool_free` true in `summary.jsonl`) | The new search form costs more than it buys, or breaks the E4B's tool use. Name the tasks. A task over 240 s is named but is not itself a row. |
| 3 | **Not exercised.** Tasks with at least one failed reader search are **3 or more of 8** | The form did not remove the failures: the reader did not follow it, or another route fails. No decision about L. Record which route failed (a pipe typed anyway, a wrong path, a token with a regex character). The lead decides whether a shorter prompt form or the localizer stage is next. |
| 4 | **Kept.** Rows 1 to 3 did not fire (searches fixed), and **L >= 2 on 5 or more of 8 tasks** | Failed searches were a cause of single locations. A process reading on the reader's report, not on the patch. The form is kept as the base of the next round (the fused round with EXP-063's selector, which needs the lead and for any dev-48 arm the user's word). |
| 5 | **Dropped.** Rows 1 to 3 did not fire (searches fixed), and **L >= 2 on 2 or fewer of 8 tasks** | With working searches the reader still lists one place. The search failures were not the cause (or not enough of it). The remaining routes are the required minimum of 3 in the prompt and the separate localizer stage (EXP-064 section 5); this form is not a path to diverse locations. |
| 6 | **No decision.** Anything else, including searches fixed and L >= 2 on 3 or 4 of 8 tasks | Record S, L, the split, F, G and G1 per task. The resolves are recorded and decide nothing. |

**Not rows, but binding:**
- Per-task resolves at n = 8 are never an endpoint; six of eight must flip the same way for p < 0.05.
- The two movable tasks are reported by themselves in section 9 whatever row fires.
- The reference L is 2 of 8 (EXP-064). L >= 2 on 3 or 4 of 8 is not read as a rise: the run-to-run variation of the reader's picks in earlier runs is of that size.
- The text-form counter is recorded. A nonzero tool-free count is row 2 whatever else holds.

**Blind prediction.**
- Tasks with at least one failed search below 3 of 8 (searches fixed): about 0.75. The risk is that the reader still pipes or uses a path that does not exist.
- L >= 2 on at least 5 of 8: about 0.2. Group (i) tasks (4 of 6) had one candidate file in view, and a working search finds more candidates only if the token occurs in other files.
- Row 5: about 0.3. Row 6: about 0.3. Row 3: about 0.15. Row 2: about 0.1. Row 4: about 0.1. Row 1: about 0.05.
- Mean wall about 105 s (range 90 to 135), 0 cap hits.

## 5. What this does and does not license

**The screen can decide one of two things.**
- **Kill (of this form as a route to diverse locations):** row 5 says working searches alone do not make the reader list several places, and leaves the required minimum and the localizer stage as the remaining forms. Row 3 kills nothing; it says the form was not followed.
- **Promote:** row 4 only. It promotes this reader prompt to the base of the next round (the fused round with EXP-063's selector). A dev-48 pair would still need the user's word and an endpoint of its own; this screen does not name one.

**Does not license:** any resolve or LB claim, any upload or dev-48 run without the user, a statement about the applier, or a claim that more locations make a better fix.

## 6. Exact commands

```
python tools/validate_submission.py experiments/EXP-066/candidate-srch --official --strict --json
python tools/pack_submission.py --src experiments/EXP-066/candidate-srch --out dist/EXP-066-srch.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed dist/EXP-066-srch.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-066-srch"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp066_srch/kaggle_eval_l4x4.ipynb
```

The kernel push is released by the lead and is not run in this job. Analysis, a separate job, after `kaggle kernels status` says COMPLETE:
1. Download with `kaggle kernels output rainm4/gemma4-exp066-srch -p runs/EXP-066-srch/`, then flatten.
2. Run `python -I -X utf8 tools/analyze_traces.py runs/EXP-066-srch --cap-minutes 8 --max-calls 45`.
3. Run `python -I -X utf8 tools/run_forensics.py forensics runs/EXP-066-srch`.
4. Count S, L, the split, F, G and G1 per task from `traces/` as in section 3, and the reader's call forms.

## 7. Defects in this pre-registration, logged after the fact

1. **(Known at pre-registration.)** The `git grep -l` form is not in any E4B trace (section 1); the rest of the form is. The screen tests it and does not assume it works.
2. **(Known at pre-registration.)** The form counts of section 1 were read from the 21 reader calls by grep and line-number reads, not by a script, so a call of mixed form could be misfiled; the 7 malformed ones are the exact `head` errors.
3. **(Known at pre-registration.)** The tree was built by `cp -r` plus edits, not by `git archive`, because `tar` is outside this agent's commands; the clean `i/lf w/lf` check and the `diff -ru` stand in for it.

## 8. Built (below the line; nothing above changes)

---

- **Changed files vs EXP-064 `candidate-loc`:** `prompts/reader.md` and `sub_agents/reader.yaml` (one comment line). No CR byte in either.
- **Validator** (`--official --strict`): 1 error, the 18.00 h gate, which `--skip-budget-gate` demotes to a warning. 2 warnings, both carried from EXP-064 (the applier's `submit_patch`, `timeout_seconds` 240). The official validator could not be imported. No new warning.
- **Pack:** `RESULT: VALID (0 errors, 3 warnings)`, PACK OK, 20 files, `dist/EXP-066-srch.zip` (gitignored). **sha256 `fab2dd152923686ae4bd27b53564d6b753573de13fee04bb732c7afeef2a805d`.**
- **Pre-registration commit:** 39a1421 (this file and the candidate tree). `git ls-files --eol` on the candidate tree: all 20 blobs `i/lf`, worktree `w/lf`, so a repack from the committed blobs is byte-identical to the worktree pack (the same argument as EXP-064; `tar` is outside this agent's commands, so no `git archive` repack was run).
- **Notebook:** `notebooks/exp066_srch/`, built with the section 6 command. Against `notebooks/exp064_loc/` the notebook differs in exactly two lines: `EXP_ID` and `SUBMISSION_B64`. `kernel-metadata.json` is EXP-064's with only `id` and `title` changed, to `rainm4/gemma4-exp066-srch`. Nothing was copied to `out/submission.zip`.
- **Kernel id for the push:** `rainm4/gemma4-exp066-srch`, directory `notebooks/exp066_srch`. Expected cost about 0.35 GPU-h.

## Status

2026-11-10: pre-registered (39a1421), candidate packed with sha `fab2dd15...a805d`, notebook built (92b3904, pushed to origin by the lead). **Pushed 2026-11-10 on the lead's release**: kernel version 1, `rainm4/gemma4-exp066-srch`, first status RUNNING (not QUEUED, so no second check). Two kernels were live (EXP-063 v2 also RUNNING). Next, when the lead reports COMPLETE: `kaggle kernels output rainm4/gemma4-exp066-srch -p runs/EXP-066-srch/`, flatten, then the analysis commands in section 6, then apply section 4.

2026-11-10 (later): kernel COMPLETE, downloaded, flattened and analyzed; section 9 below applies section 4. **Row 6 fired** (no decision). Nothing is running for this experiment.

---

## 9. Results, 2026-11-10. Section 4's readings applied as written.

Source: `runs/EXP-066-srch/` (nested bundle copied up with `cp -r`), `analyze_traces.py --cap-minutes 8 --max-calls 45`, `run_forensics.py forensics` and `compare` against `runs/EXP-064-loc`, then Grep reads of `traces/` for the reader's calls and results, the reader's final report, and the draft FILE lines (no script is allowed to this agent). Only ids, counts, paths, line numbers and error kinds are written here. `summary.jsonl` is copied to `experiments/EXP-066/srch/summary.jsonl`.

**Cost.** Kernel wall 1258.7 s (last entry of the kernel log) = **0.350 GPU-h** (EXP-064: 0.353). All 8 tasks ran; `task_results.jsonl` has `status` SUCCESS and `error` null on 8 of 8.

### 9.1 Reader searches (S, forms), per task

A search failure is a reader `run_command` whose result is an error with a non-empty error message. All 4 error results in the reader's calls carried an empty message with exit code 1, so they are no-matches, counted apart.

| task | reader run_command calls | forms | failed (S) | no-match | reader read_file | reader calls total |
|---|---|---|---|---|---|---|
| requests_7309 | 2 | `git grep -l` dir, `git grep -n` one file | 0 | 0 | 2 | 4 |
| requests_7205 | 2 | `git grep -l` dir (no `--`), plain `grep -n` one file | 0 | 0 | 3 | 5 |
| fastapi_14448 | 1 | `git grep -l` dir | 0 | 0 | 5 | 6 |
| fastapi_14301 | 6 | `git grep -l` x4 (2 on the whole tree, 2 on one file), `git grep -n` one file x2 | 0 | 2 | 2 | 8 |
| httpx_3672 | 3 | `git grep -l` dir, `git grep -n` one file x2 | 0 | 0 | 4 | 7 |
| fastapi_14605 | 2 | `ls` dir, `git grep -n` one file | 0 | 0 | 2 | 4 |
| rich_3468 | 2 | `git grep -n` on `./rich` (a directory), `find` | 0 | 1 | 4 | 6 |
| rich_3006 | 2 | `git grep` with no flag, directory, x2 | 0 | 1 | 1 | 3 |
| **total** | **20** | pipes 0, `git grep -l` 8, `git grep -n` one file 6, plain `grep -n` one file 1, other 5 | **0** | **4** | 23 | 43 |

- **S.** Failed searches 0 of 20 calls (reference 7 of 21); tasks with at least one failed search **0 of 8** (reference 4 of 8). "Searches fixed" holds (below 3).
- **Form followed.** No reader call used a `|` (0 of 20; EXP-064 had 9 of 21). `git grep -l`, which no E4B had been seen to use, ran 8 times on 5 tasks with no error; 6 of the 8 returned hits and 2 (fastapi_14301, both with a token holding quote and bracket characters) returned no match. The prompt's two-step form (`-l` then `-n` on one file) was followed in full on 3 tasks (requests_7309, fastapi_14301, httpx_3672), and with a plain `grep -n` as step two on requests_7205. fastapi_14448 stopped after the `-l` step and went straight to reading 5 files. rich_3468, rich_3006 and fastapi_14605 did not use `-l` (a directory-wide `git grep`, `find` or `ls` instead).
- **Reader read cap.** Reader `read_file` calls 5 at most (fastapi_14448), under the prompt's 8.

### 9.2 L, the (i)/(ii) split, F, G and G1, per task

L is counted as LOCATION blocks with a REGION in the reader's final report; END is present on 8 of 8 (one `ISSUE:` report per trace). A report-less reader: none.

| task | L (blocks) | locations (file, lines) | draft files d1..d5 (5 FILE lines, completion order) | F | G any | G1 | resolved | wall s | calls |
|---|---|---|---|---|---|---|---|---|---|
| requests_7309 | 1 | `src/requests/utils.py` 527-531 | same x5 | 1 | yes | yes | no | 87.0 | 8 |
| requests_7205 | 1 | `src/requests/utils.py` 281-283 | same x5 | 1 | yes | yes | no | 61.5 | 7 |
| fastapi_14448 | **3** (labels 1, 1, 2) | `fastapi/utils.py` 10-20; `fastapi/utils.py` 19-20; `fastapi/routing.py` 34 | routing x1, utils x4 | **2** | **no** | no | no | 136.5 | 13 |
| fastapi_14301 | 1 | `fastapi/dependencies/utils.py` 128-131 | same x5 | 1 | yes | yes | **yes** | 66.2 | 10 |
| httpx_3672 | **5** | `src/httpx/_parsers.py` 68-108, 381-413, 57-72, 397-401, 370-380 | same file x5 | 1 | yes | no | no | 98.9 | 12 |
| fastapi_14605 | **2** | `fastapi/exceptions.py` 10; `fastapi/temp_pydantic_v1_params.py` 58 | exceptions x4, temp_pydantic x1 | **2** | yes | no | no | 157.6 | 12 |
| rich_3468 | 1 | `rich/file_proxy.py` 30-42 | same x5 | 1 | **no** | no | no | 127.1 | 18 |
| rich_3006 | 1 | `rich/repr.py` 73-74 | same x5 | 1 | yes | yes | **yes** | 63.7 | 7 |

- **L >= 2 on 3 of 8** (fastapi_14448, httpx_3672, fastapi_14605); reference 2 of 8 (httpx_3672, fastapi_14605). The fastapi_14448 report repeated the label "LOCATION 1" for two overlapping blocks of one file, so by distinct location numbers it is 2 and by blocks 3; either way the task is at 2 or more, so the count is 3 of 8 under both readings. httpx_3672's 5 locations are all in one file. L by distinct files: 2 of 8 (fastapi_14448, fastapi_14605), the same as EXP-064.
- **(i)/(ii) split of the 5 tasks with L < 2.** (i) the reader saw one candidate file only: **2** (requests_7309, fastapi_14301). (ii) it saw several and listed one: **3** (requests_7205, which opened `sessions.py` and `utils.py`; rich_3468, which opened `console.py`, `_fileno.py` and `file_proxy.py`; rich_3006, whose one search printed hit lines in `style.py` and `text.py` and which opened `repr.py` only). EXP-064's split on its 6 was 4 and 2. The two searches that find more than one file now sit with the (ii) tasks, so the failed-search explanation for (i) does not carry here: with working searches, the tasks that still have one location mostly saw several files.
- **F >= 2 on 2 of 8** (fastapi_14448, fastapi_14605); reference 2 of 8 (httpx_3672, fastapi_14605). **G any 6 of 8** (misses fastapi_14448 and rich_3468); reference 7 of 8. **G1 4 of 8**; reference 5 of 8. The G drop is one task: rich_3468's reader listed `rich/file_proxy.py` where EXP-064's listed the gold file `rich/console.py`; the reader's picks varied between runs without a prompt change on fastapi_14605 and fastapi_14448 (EXP-064 section 1), and on rich_3468 the region varied inside `console.py` in three earlier runs; this is the first run to list another file there. One task at n = 8 is not read as an effect.
- **Text-form counter.** `n_text_form_calls` 0 on 8 of 8 tasks; `tool_free` false on 8 of 8 (reference 0 of 8 and 0 of 8).

### 9.3 Row that fired

- Row 1: no. `error` null on 8 of 8, no traceback, the root transferred on 8 of 8, every drafter built its request.
- Row 2: no. Empty patches **1 of 8** (fastapi_14448; not above 2), time, call and turn cap hits **0**, mean wall **99.8 s** (sum 798.5 s; EXP-064 100.0 s, EXP-061 89.5 s, EXP-062 89.2 s) against the 150 s line, `tool_free` 0 of 8. Longest task 157.6 s (fastapi_14605), under 240 s.
- Row 3: no. Tasks with at least one failed reader search 0 of 8 (the row needs 3 or more).
- Row 4: no. L >= 2 on 3 of 8 (needs 5 or more).
- Row 5: no. L >= 2 on 3 of 8 (needs 2 or fewer).
- **Row 6: fired.** Searches fixed (0 of 8), L >= 2 on 3 of 8. **No decision.** The binding note applies: L >= 2 on 3 or 4 of 8 is not read as a rise on the reference 2 of 8. Resolves are recorded and decide nothing.

What the row licenses (section 5): nothing is promoted and nothing is killed. For the record, the numbers sit nearer row 5's finding than row 4's: the reader's searches ran with no failure and L was 3 of 8, not 5, so the failed searches of EXP-064 were not what held L at 1 on most tasks. That is a descriptive note, not the row; row 5 needed 2 or fewer.

### 9.4 Movable tasks, reported on their own

- **fastapi_14448.** The reader ran one search (`git grep -l` on `fastapi`, 11 files printed, `dependencies/utils.py` among them), then read 5 files (`params.py`, `dependencies/utils.py`, `routing.py`, `types.py`, `utils.py`), so a gold file was opened. It listed `fastapi/utils.py` (twice) and `fastapi/routing.py`, neither of which is a gold file. Drafts: 4 on `utils.py`, 1 on `routing.py`; G no. The applier made 6 edit calls, all failed: 2 argument-loss and 4 with the filepath wrapped in double quotes ("Source path not found", the class S of EXP-067). Patch empty after 3 `submit_patch` calls, 136.5 s, 13 calls, one compaction. Not resolved. EXP-064's run listed `routing.py` only (no gold file either) and ended with a non-empty patch; here the patch is empty because every edit call failed on the argument form or the path, not on content.
- **rich_3468.** The reader ran `git grep -n` on `./rich` (no match) and a `find`, then read `console.py` twice, `_fileno.py` and `file_proxy.py`. It listed one location, `rich/file_proxy.py` 30-42 (not the gold file; EXP-064 listed `console.py` 1627-1710). 5 drafts on that file; G no. The applier made 6 edit calls, 2 failed with "old_string not found" (the other 4 applied), and the patch is not empty (EXP-064: 6 of 6 failed, empty patch). Not resolved. 127.1 s, 18 calls, one compaction.

### 9.5 Resolves, recorded and not an endpoint

2 of 8 (fastapi_14301, rich_3006), the same two as EXP-064 and EXP-052; `compare` against EXP-064: both 2, A only 0, B only 0, neither 6, no discordant pair.

### 9.6 Other recorded counts

- Edit failures 17.2 percent of tool calls (`analyze_traces`): fastapi_14448 6 (2 argument-loss, 4 quote-wrapped path), fastapi_14605 6 (all "target occurs 2 times" in `temp_pydantic_v1_params.py`, one repeated 3 times), rich_3468 2, rich_3006 1 (argument-loss). Identical repeats 2, 3 and 3 on fastapi_14448, fastapi_14605 and rich_3468.
- Compactions 3 (fastapi_14448, fastapi_14605, rich_3468), none raising an error; largest single prompt 14,979 tokens (fastapi_14448) against 14,336 (EXP-064: 22,124).
- Projected hidden-run total 3.33 h by `analyze_traces` (setup 0 s measured here), recorded only.

### 9.7 Prediction check

- Searches fixed (below 3 of 8 with a failed search), about 0.75: held, 0 of 8.
- L >= 2 on 5 or more, about 0.2: did not hold, 3 of 8. Row 6 (about 0.3): fired. Row 5 (about 0.3), row 4 (about 0.1), row 3 (about 0.15), row 2 (about 0.1), row 1 (about 0.05): did not fire.
- Mean wall about 105 s (90 to 135): held, 99.8 s. 0 cap hits: held.

### 9.8 Defects found in the reading

1. L counts LOCATION blocks by label, and fastapi_14448's report used one label twice (two overlapping blocks of the same file), so L is 3 by blocks and 2 by distinct labels. The task is at 2 or more either way; the count of 3 of 8 does not change. Section 3 did not say how to count a repeated label.
2. The (i)/(ii) split reads the hit lines of one search per task only to the first 400 to 500 characters, so "saw several files" for rich_3006 rests on two files named in the leading hit lines of a longer result.
3. `git grep -l` returned no match twice on fastapi_14301 for a token holding quote and bracket characters, as the section 2 known limit 1 foresaw; it is counted as no-match, not as a failure.
4. Against section 3, the reader's call counts here include the `ls` and `find` forms; section 1 had no category for them and they are in "other".
