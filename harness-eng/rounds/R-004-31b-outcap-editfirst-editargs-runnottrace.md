# R-004 (31b): output cap, edit before probing, garbled-edit fallback, run instead of hand-tracing

Written 2026-11-18 by the proposer (PROPOSER.md v1.4), before any run of the four trees. No GPU used.

- Base tree: `trees/31b-base` (28 calls, 8 min, thinking 4096, `max_output_tokens` 8192, T=1.0).
- Base draws read in full: `runs/R-000-31b-base-d1` (22/56) and `-d2` (22/56) on `cohorts/cdev-56.txt`: `task_results.jsonl`,
  `summary.jsonl`, and all 112 `traces/trace_<id>.json` (per-step `elapsed_s`, tool, arguments, observation,
  `prompt_tokens`, `completion_tokens`). Reference patches from `data/raw/tasks.jsonl`.
- Other 31B draws read for the per-task comparison only: `R-001-31b-calls40-d1`, `R-001-31b-sweep-d1`,
  `R-002-31b-think1024-d1`, `R-003-31b-nothoughts-d1` (resolve counts only). `R-003-31b-inline-scratch-d1` had no
  `summary.json` (43 of 56 traces) and was not read.
- Screen: `cohorts/screen-31b-20.txt`. Tasks on it are marked (S) below.
- Not repeated: 40 calls (T-31b-001), thinking budget 1024 (T-31b-003), thoughts out of history (T-31b-004), sibling
  sweep (T-31b-002, pending), inline scratch (T-31b-005, pending).

## Where the 8 minutes go

Method. A step's `elapsed_s` is stamped when the model's reply arrives and the observation's when the tool returns, so
model seconds of a turn = its `elapsed_s` minus the previous observation's, and tool seconds = observation minus call.
Decode seconds = `completion_tokens` / the draw's median rate on turns of 300 tokens or more (26.9 tok/s in d1, 27.5 in
d2, four tasks sharing one GPU). The rest of a turn's model seconds is overhead (prompt processing, queueing), or
compaction when `prompt_tokens` fell by more than 3,000 from the previous turn, or a stall when more than 30 s are
unexplained without a compaction. The unfinished final turn is `duration_s` minus the last recorded `elapsed_s`: a
turn that was still generating when the session ended leaves no step in the trace.

Seconds (share of the group's wall time):

| Draw | Group | Tasks | Wall s | Decode, turns under 800 tokens | Decode, turns of 800 tokens or more | Turn overhead | Compaction | Stall | Tool execution | Unfinished final turn |
|---|---|---|---|---|---|---|---|---|---|---|
| d1 | all 56 | 56 | 19635 | 7620 (39%) | 6980 (36%) | 1109 (6%) | 1342 (7%) | 498 (3%) | 293 (1%) | 1724 (9%) |
| d1 | resolved | 22 | 5633 | 2725 (48%) | 1948 (35%) | 366 (7%) | 295 (5%) | 0 (0%) | 21 (0%) | 250 (4%) |
| d1 | failed | 34 | 14002 | 4895 (35%) | 5032 (36%) | 743 (5%) | 1047 (7%) | 498 (4%) | 272 (2%) | 1474 (11%) |
| d1 | at the time cap | 17 | 8568 | 1981 (23%) | 3589 (42%) | 392 (5%) | 417 (5%) | 409 (5%) | 259 (3%) | 1500 (18%) |
| d1 | empty patch | 11 | 5064 | 1480 (29%) | 1849 (37%) | 262 (5%) | 292 (6%) | 498 (10%) | 247 (5%) | 426 (8%) |
| d1 | at the call cap, not the time cap | 12 | 4462 | 2319 (52%) | 1191 (27%) | 265 (6%) | 500 (11%) | 89 (2%) | 12 (0%) | 70 (2%) |
| d2 | all 56 | 56 | 19919 | 7466 (37%) | 6919 (35%) | 1149 (6%) | 1323 (7%) | 264 (1%) | 295 (1%) | 2073 (10%) |
| d2 | resolved | 22 | 5660 | 2965 (52%) | 1657 (29%) | 413 (7%) | 370 (7%) | 0 (0%) | 23 (0%) | 195 (3%) |
| d2 | failed | 34 | 14259 | 4501 (32%) | 5262 (37%) | 735 (5%) | 953 (7%) | 264 (2%) | 273 (2%) | 1878 (13%) |
| d2 | at the time cap | 14 | 7528 | 1471 (20%) | 2952 (39%) | 323 (4%) | 405 (5%) | 0 (0%) | 249 (3%) | 1794 (24%) |
| d2 | empty patch | 12 | 5538 | 1367 (25%) | 2238 (40%) | 295 (5%) | 361 (7%) | 230 (4%) | 20 (0%) | 1006 (18%) |
| d2 | at the call cap, not the time cap | 11 | 4334 | 2260 (52%) | 1052 (24%) | 318 (7%) | 351 (8%) | 230 (5%) | 22 (1%) | 65 (2%) |

Group flags are `summary.jsonl` `time_cap_hit`, `calls_cap_hit`, `patch_empty` (17 and 14 tasks at the time cap by
that file; the lessons file says 16 and 14).

What the table says about the five suspects:

- **Decode of long outputs: yes, this is where the time goes.** Turns of 800 tokens or more are 8% of turns (111 of
  1,374 in d1, 102 of 1,286 in d2) and 35-36% of all wall time, 39-42% on time-cap tasks. Together with the unfinished
  final turn (18-24% on time-cap tasks; it is itself a long generation) they are about 60% of a time-cap task. The long
  turns are thought text, not arguments: in d1 the 111 long turns hold 588k characters of thought and 43k characters
  of tool arguments. 51 and 52 of them end in a plain grep or read.
- **Slow commands, command timeouts, test runs that hang: no.** Tool execution is 293 and 295 s per draw (1.5%). One
  task accounts for 241 s of it in each draw: `rich_3480` (S) reproduces the infinite loop the issue describes and
  waits out `timeout_seconds: 240`. No other command took more than 6.1 s. Only 16 and 15 commands per draw run pytest
  at all (17 and 19 s in total).
- **Repeated reads after compaction: some.** Compaction turns cost 1,342 and 1,323 s (7%). Reads that return lines
  already read in the same task (80% overlap or more): 87 calls, 1,392 s on 39 tasks (d1); 64 calls, 1,128 s on 30
  tasks (d2), turn time included.
- **Not on the suspect list, and larger than compaction on time-cap tasks:** the unfinished final turn. 7 (d1) and 8
  (d2) tasks end with a turn that had already run more than 76 s; three (d1) and four (d2) had run more than 240 s
  (`fastapi_15588`, `rich_3535`, `rich_3772`; `rich_3480`, `rich_3506`, `rich_3521`, `rich_3772`). The session is not
  cut at 480 s while a turn is generating: 4 and 6 tasks ran past 495 s, up to 675 and 759 s (`rich_3772`), 343 and
  770 s over the cap per draw. This matters for the 12 h projection on Kaggle.
- **Stall** (498 s in d1, 264 s in d2) is two or three turns per draw whose seconds the recorded tokens do not explain
  (`rich_3506` d1 call 6: 281 s for 1,779 tokens; `rich_3521` d1 call 10: 278 s for 3,045). Nothing in the trace or
  log says why.

Per task, the 17 + 14 tasks that ended at the time cap. The first seven second-columns add up to the wall time; the
last four are overlapping views of the same seconds (turn time of: scripts, tests and scratch writes before the first
source edit; `edit_file` calls that arrived without `old_string`; `write_file` calls rejected for a `/tmp` path; reads
of lines already read).

| Task | Draw | Outcome | Calls | Wall | Decode <800 | Decode >=800 | Overhead | Compaction + stall | Tool | Unfinished final turn | Pre-edit probes | Garbled edits | Rejected /tmp writes | Duplicate reads |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `fastapi_14448` | d1 | wrong file | 25 | 489 | 127 | 281 | 22 | 48 | 0 | 9 | 0 | 39 | 0 | 164 |
| `fastapi_15588` (S) | d1 | wrong logic | 12 | 489 | 62 | 135 | 21 | 0 | 0 | 268 | 0 | 0 | 0 | 7 |
| `fastapi_15661` (S) | d1 | wrong file | 25 | 489 | 226 | 176 | 21 | 57 | 1 | 6 | 0 | 0 | 0 | 59 |
| `rich_3063` (S) | d1 | resolved | 25 | 477 | 153 | 279 | 20 | 18 | 1 | 5 | 247 | 0 | 94 | 46 |
| `rich_3105` | d1 | wrong file | 28 | 486 | 140 | 225 | 36 | 52 | 9 | 24 | 11 | 0 | 0 | 0 |
| `rich_3180` | d1 | no edit | 11 | 483 | 51 | 349 | 22 | 30 | 0 | 30 | 0 | 0 | 0 | 0 |
| `rich_3278` (S) | d1 | no edit | 12 | 484 | 118 | 277 | 27 | 35 | 0 | 26 | 426 | 0 | 53 | 2 |
| `rich_3480` (S) | d1 | no edit | 13 | 484 | 63 | 61 | 14 | 0 | 241 | 104 | 339 | 0 | 68 | 2 |
| `rich_3506` | d1 | no edit | 11 | 517 | 104 | 66 | 13 | 214 | 0 | 117 | 346 | 0 | 281 | 12 |
| `rich_3521` (S) | d1 | no edit | 16 | 564 | 65 | 176 | 14 | 202 | 1 | 105 | 102 | 0 | 0 | 0 |
| `rich_3535` | d1 | partial | 10 | 507 | 56 | 166 | 1 | 38 | 0 | 245 | 0 | 0 | 0 | 121 |
| `rich_3772` | d1 | wrong region | 11 | 675 | 79 | 239 | 26 | 24 | 1 | 305 | 0 | 0 | 0 | 6 |
| `rich_3782` (S) | d1 | no edit | 25 | 483 | 224 | 198 | 22 | 21 | 0 | 16 | 0 | 138 | 0 | 2 |
| `rich_3934` | d1 | partial | 15 | 488 | 112 | 270 | 26 | 4 | 3 | 72 | 164 | 0 | 0 | 0 |
| `rich_3935` | d1 | wrong file | 29 | 486 | 216 | 186 | 30 | 24 | 1 | 29 | 133 | 0 | 35 | 54 |
| `rich_4077` (S) | d1 | no edit | 18 | 482 | 99 | 296 | 45 | 34 | 0 | 7 | 0 | 0 | 0 | 14 |
| `rich_4079` (S) | d1 | resolved | 23 | 485 | 88 | 209 | 34 | 23 | 0 | 131 | 0 | 0 | 0 | 0 |
| `fastapi_13920` (S) | d2 | no edit | 19 | 484 | 129 | 267 | 21 | 48 | 0 | 17 | 0 | 217 | 0 | 6 |
| `fastapi_14419` (S) | d2 | resolved | 26 | 489 | 143 | 234 | 29 | 74 | 0 | 7 | 0 | 0 | 0 | 9 |
| `fastapi_14448` | d2 | no edit | 12 | 484 | 63 | 252 | 30 | 35 | 0 | 102 | 0 | 0 | 0 | 50 |
| `fastapi_15589` | d2 | resolved | 26 | 507 | 143 | 222 | 30 | 55 | 3 | 51 | 108 | 0 | 0 | 0 |
| `fastapi_15661` (S) | d2 | no edit | 18 | 486 | 137 | 210 | 26 | 72 | 0 | 37 | 128 | 0 | 0 | 187 |
| `rich_3180` | d2 | no edit | 10 | 483 | 21 | 348 | 19 | 0 | 0 | 94 | 0 | 0 | 0 | 153 |
| `rich_3480` (S) | d2 | wrong logic | 17 | 752 | 166 | 55 | 11 | 0 | 241 | 278 | 294 | 0 | 28 | 3 |
| `rich_3506` | d2 | no edit | 6 | 516 | 17 | 190 | 3 | 0 | 0 | 304 | 157 | 0 | 0 | 0 |
| `rich_3521` (S) | d2 | no edit | 15 | 616 | 27 | 312 | 12 | 0 | 0 | 264 | 0 | 73 | 0 | 0 |
| `rich_3772` | d2 | wrong region | 13 | 759 | 132 | 274 | 11 | 35 | 1 | 306 | 0 | 0 | 0 | 7 |
| `rich_3782` (S) | d2 | no edit | 19 | 483 | 111 | 183 | 13 | 17 | 1 | 156 | 122 | 0 | 47 | 0 |
| `rich_3930` | d2 | partial | 26 | 487 | 199 | 160 | 44 | 32 | 0 | 51 | 23 | 276 | 0 | 42 |
| `rich_3934` | d2 | wrong file | 7 | 500 | 29 | 36 | 5 | 0 | 1 | 116 | 17 | 0 | 0 | 0 |
| `rich_3935` | d2 | no edit | 23 | 483 | 154 | 210 | 68 | 38 | 1 | 10 | 350 | 0 | 0 | 0 |

## Miss classes (all 34 failed tasks per draw)

Our patch against the reference patch, by file and by hunk position (a reference hunk counts as touched when one of
ours starts within 15 lines of it).

| Class | d1 | d2 |
|---|---|---|
| No edit (empty patch) | 11 | 12 |
| Partial (some reference hunks touched, not all) | 9 | 9 |
| Wrong file | 7 | 2 |
| Wrong region (right file, no reference hunk touched) | 4 | 4 |
| Wrong logic (every reference hunk touched, tests fail) | 3 | 7 |
| Test-only breakage | 0 | 0 |

No edit is the largest class in both draws. 7 (d1) and 8 (d2) of those tasks end at the time cap, 4 and 4 at the call
cap only. In 9 of the 11 (d1) and 6 of the 12 (d2) the reference file had been opened with `read_file` by call 6,
within 8 to 21 s; the agent has the file and never changes it. T-31b-006 and T-31b-007 aim at this class; T-31b-008
and T-31b-009 each take a part of it. On the screen it is nearly the whole problem: of the 11 failures of sometimes-
resolved screen tasks in the two base draws, 7 are empty patches at the time cap (`rich_3278` d1, `rich_3480` d1,
`rich_3521` d1 and d2, `rich_3782` d1 and d2, `rich_4077` d1).

## Proposals

| Tweak | Kind | Tree | Change (one sentence) | Evidence (task, draw, what the trace shows) |
|---|---|---|---|---|
| T-31b-006 | process (budget) | `trees/31b-r004-out2048` | `configs/sampling.yaml`: `max_output_tokens` 8192 -> 2048, so one turn cannot run longer than about 76 s. | `rich_3521` (S) d1: call 10 is a 3,045-token turn of 278 s that ends in `grep -r "split_cells" .`; the session ends 105 s into a later turn; d2: calls 7, 11, 14 are 1,844, 2,156 and 3,047 tokens (64, 70, 107 s), each ending in a grep or a read, the first edit attempt comes at 352 s and the last turn runs 264 s unfinished. `rich_4077` (S) d1: reference file read at call 4 (21 s); calls 8, 15, 16 are 2,767, 2,510 and 2,679 tokens (104, 96, 129 s), each ending in a grep for `isatty` or `fileno`. `rich_3782` (S) d2: call 19 is 4,124 tokens (151 s) ending in `grep -n "class Syntax"`, then 156 s unfinished. `rich_3180` d1: call 9 is 7,685 tokens (287 s) ending in `grep -r "3176" .`. `rich_3063` (S) d2: call 19 is 6,941 tokens (218 s) ending in a re-read of 19 lines. `fastapi_15588` (S) d1, `rich_3772` d1 and d2, `rich_3506` d2: final turns of 268, 305, 306 and 304 s that never finished. |
| T-31b-007 | process (order of work) | `trees/31b-r004-editfirst` | `prompts/system.md` section 3 gets a first line: no reproduction script, test or `python -c` probe until a source file is edited. | `rich_3278` (S) d1: reference file read at call 2 (14 s); calls 3 to 9 are seven `python3 -c` regex probes and call 10 a rejected `/tmp` write, 426 s together; the first edit attempt is call 11 at 456 s and fails. `rich_3480` (S) d1: the function is read at call 5 (23 s); call 7 reproduces the hang and waits 240 s for the command timeout; call 12 is a rejected `/tmp` write (68 s). `rich_3506` d1: region read at call 2 (9 s); call 6 is a 281 s turn writing a `/tmp` test, calls 7 to 10 are probes; d2: call 3 is a 4,209-token turn ending in a probe. `rich_3782` (S) d2: calls 7 to 16 are ten calls writing and running `/tmp/test_syntax_padding.py` (122 s) before any edit. `rich_3935` d2: 12 scratch calls, 350 s. `rich_3521` (S) d1: calls 7 to 9 are probes (65 s), then the 278 s turn. |
| T-31b-008 | mechanics (how it edits) | `trees/31b-r004-editargs` | `prompts/system.md` section 3 gets a line: when `edit_file` answers that `old_string` is not present, do not resend the call; make the change with a `python3 - <<'EOF'` replace through `run_command`. | The call arrives with `new_string` ending in `` `,old_string: `` and the old text split into stray keys; the harness answers "mandatory input parameters are not present: old_string"; it is not counted as a tool call, and the agent sends the same text again. `rich_3782` (S) d1: the first edit attempt is at 341 s and is sent ten times unchanged until the cap. `fastapi_13920` (S) d2: first edit attempt at 338 s, seven garbled calls until the cap. `rich_3521` (S) d2: the only edit attempt (352 s, a 73 s turn) is garbled. `rich_4079` (S) d2: calls 21 and 22 garbled (111 and 63 s), the real edit lands at 407 s with three calls left. `rich_4070` d2: 23 garbled calls; `rich_3930` d2: 13; `fastapi_5624` d1: 13. Other draws: `fastapi_9753` (S) resolves in the three draws without garbled calls and fails in the two with them (calls40: 13 calls, 214 s; think1024: 10 calls, 84 s); `fastapi_14873` (S) fails in sweep-d1 with 5 garbled calls (269 s). |
| T-31b-009 | mechanics (how it checks) | `trees/31b-r004-runnottrace` | `prompts/system.md` "Never" list gets a line: do not step through code by hand in reasoning, run one `python3 -c "print(...)"` line instead. | `rich_3180` d1: the 7,685-token turn at call 9 steps `chop_cells` and `divide_line` over "ABCDE" character by character, more than once, and ends by grepping for the issue number; d2: 250 s of hand traces. `rich_3063` (S) d2: call 19 (6,941 tokens, 218 s) works out by hand what `escape` and `_parse` return for five backslash strings, one call after its own probe script ran (call 18, 1 s). `rich_3278` (S) d1: call 3 (3,152 tokens, 119 s) works out which character codes a regex class covers. `rich_3953` d1: 176 s stepping a zero-width-joiner loop; d2: 328 s of hand traces. `rich_3506` d1 (281 s), `rich_3521` (S) d1 (278 s), `rich_3935` d2 (191 s), `fastapi_9753` (S) d1 (136 s, resolved). |

Validation: all four trees pass `tools/validate_submission.py` with the base's packing-gate error only.
`31b-r004-out2048` adds one warning, "thinking_budget (4096) >= max_output_tokens (2048); tool calls may be cut off".
That is the intended effect, and the thinking budget does not bound a turn on this cluster (see the notes below); a
packed candidate would need the budget lowered or `--allow-warnings`.

## Failed patch against reference patch, for the cited tasks

| Task (draw) | Reference patch | Our patch | Kind of miss |
|---|---|---|---|
| `rich_3521` (d1, d2) | 1 hunk, `rich/segment.py` | empty | no edit (function read at call 2 in both draws) |
| `rich_4077` (d1) | 1 hunk, `rich/file_proxy.py` | empty | no edit (file read at call 4) |
| `rich_3782` (d1, d2) | 7 hunks, `rich/syntax.py` | empty | no edit (d1: the edit was written and sent ten times garbled) |
| `rich_3278` (d1) | 1 hunk, `rich/ansi.py` | empty | no edit |
| `rich_3480` (d1; d2) | 2 hunks, `rich/text.py` (`append`, `append_text`) | empty; 1 hunk, `append` only | no edit; partial (the 15-line rule above counts it as wrong logic) |
| `rich_3506` (d1, d2) | 1 hunk, `rich/segment.py` | empty | no edit |
| `rich_3180` (d1, d2) | 2 hunks each in `rich/_wrap.py` and `rich/cells.py` | empty | no edit |
| `rich_3935` (d2) | 5 hunks, `rich/table.py` | empty | no edit (worked in `rich/padding.py`, would have been the wrong file) |
| `fastapi_13920` (d2) | 2 hunks, `fastapi/dependencies/utils.py` | empty | no edit (the garbled edit was for `fastapi/_compat/shared.py`, the wrong file) |
| `rich_3063` (d2) | 2 hunks, `rich/markup.py` | 1 hunk, `rich/markup.py` | partial |
| `rich_4079` (d2) | 1 hunk, `rich/markdown.py` | 2 hunks, `rich/markdown.py` | wrong logic |
| `rich_4070` (d2) | 33 hunks in 9 files | 12 hunks in 2 files | partial |
| `rich_3930` (d2) | 29 hunks in 26 files | 1 hunk, `rich/cells.py` | partial |
| `rich_3953` (d1, d2) | 2 hunks, `rich/cells.py` | 2 hunks, `rich/cells.py` (one reference hunk untouched) | partial |
| `fastapi_15588` (d1) | 2 hunks, `fastapi/sse.py` | 2 hunks, `fastapi/sse.py` | wrong logic |
| `rich_3772` (d1, d2) | 6 hunks, `rich/traceback.py` | 3 and 2 hunks elsewhere in `rich/traceback.py` | wrong region |

## Pattern counts (of 56 tasks per draw)

| Pattern | d1 | d2 |
|---|---|---|
| Turns over 2,048 completion tokens; tasks with one; seconds in them | 31; 25 (19 unresolved); 3,919 | 36; 29 (21 unresolved); 4,101 |
| Seconds those turns spend past token 2,048 | 1,359 | 1,765 |
| Tasks whose unfinished final turn had run more than 76 s; seconds past 76 | 7; 745 | 8; 1,013 |
| Successful source edits made in a turn over 2,048 tokens (in resolved tasks) | 6 (2) | 5 (1) |
| Tasks that run a script, test or scratch write before the first source edit | 24 (11 unresolved) | 27 (13 unresolved) |
| of which 60 s or more on it | 12 (8 unresolved) | 18 (9 unresolved) |
| Empty-patch tasks with pre-edit probes; seconds on them | 6; 1,379 | 6; 899 |
| Tasks with no source edit by 240 s (of which resolved) | 28 (5) | 30 (5) |
| `edit_file` calls arriving without `old_string`; tasks; seconds | 33; 7; 544 | 98; 14; 1,611 |
| Tasks with three or more such calls in a row | 3 | 7 |
| Long turns (800 tokens or more) that step through values by hand; tasks; seconds | 19 of 111; 13 (8 unresolved); 2,361 | 23 of 102; 16 (10 unresolved); 2,335 |
| Empty patches at the time cap (`patch_empty` and `time_cap_hit`) | 7 | 8 |
| Harness nudges (`summary.jsonl` `nudges`) | 2 | 1 |

How the less obvious ones are counted:

- Garbled edit: an `edit_file` step whose arguments have no `old_string`. Over five draws (the two base draws,
  calls40, sweep, think1024) there are 89 runs of such calls: 29 of length one, 23 of two, 37 of three or more, 15 of
  ten or more. What follows a run: a well-formed `edit_file` 30 times, a scripted or `sed` replace that works 17
  times, the end of the session 8 times. No feature of the new text predicts it (length, line count, double quotes:
  14% to 17% of edit attempts either way).
- Hand trace: a long turn whose thought has 9 or more lines of the form "`name` is / = / returns <literal>", or 15 or
  more numbered or bulleted steps that assign a value. On 14 long turns labelled by reading, it found 6 of 6 hand
  traces and flagged 1 of 8 others. All flagged turns come before the first source edit.
- Pre-edit probe: a `run_command` that runs Python or pytest, a heredoc or redirect that writes a file, or a
  `write_file`, before the first successful edit of a source path.

Checks against the outcome, on the 16 sometimes-resolved tasks over five draws (80 task-draws):

- 150 s or more in turns over 2,048 tokens plus the unfinished final turn: 11 of 28 resolved (39%); less: 31 of 52 (60%).
- Three or more garbled edit calls: 5 of 11 resolved; fewer: 37 of 69. This is a weak link over the whole set. The
  case for T-31b-008 rests on the single tasks named above, where the garbled calls sit between a written edit and
  the cap.

## Which screen tasks each edit should flip

| Tweak | Screen tasks (resolves in 6 draws) | Why |
|---|---|---|
| T-31b-006 | `rich_3521` (1), `rich_4077` (5), `rich_3782` (1), `rich_3480` (2), `rich_3278` (4) | each lost base draw has 96 to 278 s turns that end in a grep, or a final turn of 104 to 278 s that never ends; capped at 76 s, that time goes to further turns. `rich_3480` d2 already had its edit in at call 9 and then lost 278 s to one turn. |
| T-31b-007 | `rich_3278` (4), `rich_3480` (2), `rich_3782` (1), `rich_3521` (1) | the reference file is open by call 2 to 5 in every lost draw; the edit attempt comes after 100 to 430 s of probes. With the edit first, the 240 s hang in `rich_3480` falls after the edit, and an edit made in time is graded. |
| T-31b-008 | `rich_3782` (1), `fastapi_9753` (3), `fastapi_14873` (2), `rich_4079` (2), `rich_3521` (1) | the edit text exists at 340 to 350 s and is lost to resends (`rich_3782` d1, `rich_3521` d2); `fastapi_9753` fails only in its two draws with 10 or more garbled calls. |
| T-31b-009 | `rich_3063` (3), `rich_3278` (4), `rich_3521` (1), `fastapi_9753` (3) | 119 to 278 s hand traces in the lost draws; `rich_3063` d2 loses 218 s to one and reaches the call cap six failed edits later. |

No edit here gives a reason for the four never-resolved screen tasks (`fastapi_13920`, `fastapi_15588`,
`fastapi_15661`, `rich_3944`) to start resolving: three are wrong-file or wrong-logic misses in every base draw.

## Why these respect the lessons

- T-31b-006 adds no work and no prompt text. It differs from thinking budget 1024 (T-31b-003): that field did not
  bound turns (below); `max_output_tokens` is the server's own stop. It differs from thoughts out of history
  (T-31b-004): every completed thought stays in context.
- T-31b-007 removes work before the edit and adds none; one line of prompt.
- T-31b-008 fires only after an error the agent has just seen; it replaces resends that are not counted as calls
  with one counted call.
- T-31b-009 trades a turn of 90 to 290 s for a counted call of about 10 s. The empty-patch tasks at the time cap end with 6 to 23
  of their 28 calls used, so the calls are there.
- The three prompt edits add 209 to 334 characters to a 3,162-character prompt. On the 31B a prompt line has moved
  behaviour once (sweep: empty patches 7 against 11 and 12).

## Process endpoints (base values counted above)

| Tweak | Endpoint | Base d1, d2 (56 tasks) | Expected if the edit works |
|---|---|---|---|
| T-31b-006 | tasks whose unfinished final turn had run more than 76 s | 7, 8 | 2 or fewer |
| T-31b-006 | empty patches at the time cap | 7, 8 | 4 or fewer |
| T-31b-006 | guard: empty patches, all tasks (`patch_empty`) | 11, 12 | not above 12 |
| T-31b-006 | reported, no threshold: harness nudges (`nudges`); with 31 and 36 turns over the cap in the base, expect 30 or more | 2, 1 | - |
| T-31b-006 | guard: tasks running past 495 s | 4, 6 | 0 |
| T-31b-007 | tasks with a script, test or scratch write before the first source edit | 24, 27 | under 10 |
| T-31b-007 | tasks with no source edit by 240 s | 28, 30 | 20 or fewer |
| T-31b-008 | tasks with three or more garbled `edit_file` calls in a row | 3, 7 | 1 or fewer |
| T-31b-008 | seconds in garbled `edit_file` turns | 544, 1,611 | under 300 |
| T-31b-009 | long turns that step through values by hand (the heuristic above) | 19, 23 | under 10 |
| T-31b-009 | seconds in turns of 800 tokens or more (`decode >= 800` column, all tasks) | 6,980, 6,919 | under 5,000 |
| T-31b-009 | guard: tasks at the call cap | 14, 11 | not above 16 |

On the 20-task screen the same endpoints are counted on the screen ids only. Base values there, d1 and d2: unfinished
final turn over 76 s on 4 and 3 tasks; empty patches at the time cap 5 and 4; any garbled edit call on 2 and 6 tasks;
60 s or more of pre-edit probes on 6 and 9 tasks; a hand-trace turn on 6 and 6 tasks.

## Notes for the operator

- **The token-limit nudge is documented and was seen once.** `HARNESS_README.md` section 5.3: a turn that ends on
  `MAX_TOKENS` without a tool call gets "Do NOT repeat your analysis in thought ... emit your next tool call
  immediately", and four such turns in a row end the session. `rich_3934` d2 is the only base turn that reached
  8,192 tokens; the nudge was sent, and the next turn was still generating 116 s later when the session ended. One
  case, so T-31b-006 may trade long finished turns for cut ones. Whether a cut thought stays in the history is not
  documented; the first tasks of the run will show it (`prompt_tokens` after a nudge).
- **`thinking_budget` does not bound a turn here.** The README says it is forwarded to a logits processor. With
  budget 4096 the base has turns of 7,685 and 6,941 tokens; with budget 1024 (`R-002-31b-think1024-d1`) 58 of 1,221
  turns exceed 1,100 tokens and the longest is 7,078. Turns over 2,048 tokens did fall there (18 against 31 and 36).
- **Turns of 2,049 to 3,072 tokens** are 18 and 21 of the turns T-31b-006 would cut; in the base they finish in 76 to
  114 s and act. If the screen shows the cap costing more than it saves, 3,072 is the next value (13 and 15 turns
  over it, 558 and 844 s past it, 5 and 6 unfinished final turns longer than it).
- **`directions.md` checked against the traces.** A3 ("thinking tokens are most of the decode time") holds for the
  text of the thoughts, but its tweak used a field that does not bound them. A4 ("compaction drops what the model
  read"): compaction costs 7% of wall time; `read_file` is 70% of all observation characters (1,092k of 1,562k in
  d1, 889k of 1,288k in d2). A1's "time is not the binding limit at 28" is contradicted, as R-001 found.
- **Seen and not proposed.** `timeout_seconds` 240 -> 30 would give `rich_3480` (S) 210 s back in both base draws;
  it is one task, under the five-task bar, and costs nothing if composed later. Duplicate reads (87 and 64 calls)
  have no lever short of a rule the agent already ignores (93 and 64 `read_file` calls without a line range against
  "at most 120 lines"). The rejected `/tmp` writes (19 and 20 tasks, 760 and 817 s of turn time) are T-31b-005's.
- Cap counts are from `summary.jsonl`; `tools/compare.py` may differ by a task or two.

## Readings

Fixed by the operator 2026-11-18T17:25Z, before any run of the four trees and before the base screen draws were read.

- L1 screen: two draws of each tree on `cohorts/screen-31b-20.txt`, concurrency 4 (`S-004-31b-<slug>-s1/-s2`), against the base screen draws `S-000-31b-base-s1/-s2`.
- Promoted to cdev2-79 if the two-draw mean beats the base mean by 1.5 or more, or by 0.5 or more with the edit's process endpoint met (as the proposer defined it above, scaled to 20 tasks). Dropped otherwise.
- Guard for all four: tasks ending with no edit must not rise by more than 2 per draw over the base screen draws.
- T-31b-006 extra guard: turns cut at the output cap that leave a malformed tool call on more than 2 tasks per draw mean the cap is too low; then 4096 is the follow-up, not a verdict on the idea.
- If two or more are promoted, their composition is screened in the next round before any full run.

## Results

(appended after the runs)

### Base screen draws (read 2026-11-18, before any S-004 result)

- S-000-31b-base-s1 and -s2 on screen-31b-20 each resolved 9 of 20, and on the same 9 tasks: no task flipped between the two draws. The base mean is 9.0, so the promotion bars are a mean of 10.5 or more, or 9.5 or more with the endpoint met.
- The two draws differ in how they fail.
  - s1: 2 tasks at the call cap, 6 at the time cap, 6 with an empty patch.
  - s2: 0 at the call cap, 12 at the time cap, 2 with an empty patch.
  - Mean wall time was 387 s and 406 s.
- For the no-edit guard, the base reference is about 4 empty patches per draw (6 and 2).
- The time-cap count moves by 6 between two draws of the same tree, so a change of that size is not attributable to a tweak.

### S-004 screens read (2026-11-19T01:40Z)

| Tree | s1 | s2 | Mean | vs base 9.0 | Process endpoint (screen, s1 / s2; base s1 / s2) | Empty patches (base 6 / 2) | Reading |
|---|---|---|---|---|---|---|---|
| out2048 (T-31b-006) | 8 | 7 | 7.5 | -1.5 | not needed: the mean is under 9.5 | 5 / 6 | **dropped** |
| editfirst (T-31b-007) | 7 | 12 | 9.5 | +0.5 | tasks with a pre-edit probe: 9 / 8 (base 14 / 10); the 56-task target "under 10" scales to under 4 of 20 | 5 / 3 | **dropped**: endpoint not met |
| editargs (T-31b-008) | 9 | 11 | 10.0 | +1.0 | tasks with 3+ garbled `edit_file` calls in a row: 2 / 2 (base 2 / 2); target 1 or fewer of 56 scales to 0. Seconds in garbled turns: 130 / 109 (base 492 / 388); target under 300 of 56 scales to under 107 | 6 / 3 | **dropped**: endpoint not met |
| runnottrace (T-31b-009) | 9 | 8 | 8.5 | -0.5 | not needed: the mean is under 9.5 | 7 / 6 | **dropped** |

- **Counter.** Endpoints are counted by my script, using the definitions above: garbled means `edit_file`
  without `old_string`; a pre-edit probe is Python, pytest, a heredoc, a redirect or `write_file` before the
  first successful non-/tmp edit; a turn's seconds are the gap between successive call timestamps.
  - On the base screen draws it does not reproduce the proposer's counts exactly. 60 s-or-more probes come out
    10 / 6 (theirs 6 / 9), and any garbled call 4 / 3 (theirs 2 / 6).
  - Neither verdict depends on this. editfirst's probe count stayed at 8-9 of 20, against a target under 4.
    editargs's 3+-run count did not move from base.
- **No-edit guard.** No tree went more than 2 empty patches over the base reference of about 4 per draw.
  runnottrace s1 had 7, which is +3 over 4 but +1 over base s1's 6. It is dropped anyway.
- **T-31b-006 extra guard (cut turns leaving a malformed call).** Not counted, because out2048 is dropped on
  its mean. So 4096 is not queued as a follow-up.
- **editargs is the nearest miss.** Garbled-turn time fell about 70% (from 440 to 120 s per draw), and the mean
  is +1.0. But the edit's own endpoint (3+-call runs) did not move, so the rule drops it. If it is tried again,
  it needs a new proposal that names time in garbled turns as the endpoint before any run.
- **Next.** No R-004 tree goes to cdev2-79. Later 31B screens are read against the R-008 task-env base, not
  9.0.
