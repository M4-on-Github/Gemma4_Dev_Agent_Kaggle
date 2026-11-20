# R-004 (e4b): thoughts out of the history; syntax check in place of the pytest check

Written 2026-11-18T12:40Z by the proposer (`proposer/PROPOSER.md` v1), before any R-004 run and without
reading any R-003 result. Nothing here has been run.

- Base: `trees/e4b-base`.
- Draws read: `R-000-e4b-base-d1`, `-d2`, `-d3` on `cohorts/cdev-56.txt` (56 tasks each, 168 task-draws).
  Resolved 4, 7, 7 (mean 6.0, range 3).
- Traces read call by call: 18 failed task-draws (listed under Evidence); all 168 counted by script from
  `traces/` and `task_results.jsonl`.

## Proposals

| Tweak | Kind | Tree | Change (one sentence) | Evidence (task ids, draw) |
|---|---|---|---|---|
| T-e4b-006 | process (sampling, context budget) | `trees/e4b-r004-nothoughts` | `configs/sampling.yaml`: `thinking_config.include_thoughts` true -> false, so the model still thinks each turn but its thought text is not kept in the history. | rich_3930 d1, rich_3468 d2, fastapi_14258 d2, fastapi_15588 d2, rich_3944 d3, rich_3772 d3 |
| T-e4b-007 | mechanics (how it checks code) | `trees/e4b-r004-syntaxcheck` | `prompts/system.md` section 4: the four pytest-check bullets are replaced by three that make the one check `python -m ast EDITED_FILE.py > /dev/null && echo SYNTAX_OK` and forbid test commands (prompt 3,162 -> 3,111 bytes). | fastapi_15280 d1 d2 d3, rich_3894 d2, rich_3480 d1 d2, rich_3935 d2, rich_4077 d1 |

Neither repeats a ledger row. T-006 is the E4B twin of `trees/31b-r003-nothoughts` (written in parallel, no
result read); the evidence below is from the E4B draws only. T-007 removes rules and swaps one command
template; it does not add edit rules (T-e4b-003) and is not the `git diff --stat` check of T-e4b-005.

## Miss classes in the base draws (unresolved task-draws, patch against the reference patch)

Classes by script: no edit = empty patch; wrong file = no reference source file touched; wrong region = right
file, no hunk within 15 lines of a reference hunk; partial = some reference hunks reached; wrong logic = all
reached, tests fail.

| Draw | Resolved | Wrong file | Wrong region | Partial | Wrong logic | No edit | Test or doc only |
|---|---|---|---|---|---|---|---|
| d1 | 4 | 18 | 9 | 10 | 5 | 10 | 0 |
| d2 | 7 | 12 | 8 | 9 | 10 | 8 | 2 |
| d3 | 7 | 11 | 11 | 8 | 6 | 13 | 0 |

Other counts, all three draws together:

- Wrong file, 39 task-draws with a reference source file: the reference file was never read in 36 and was
  in a grep output in 5. The issue texts are often one line ("fix fonts", "Notes", "proxy isatty"). No
  one-sentence locate change was found for this, so neither edit targets it.
- Empty patches, 31: `submit_patch` was called on 28 with at most 261 s of 480 s used; 3 sessions made no
  tool call; 4 submitted after reading without an edit attempt.
- Failed edit calls with "old_string not found", 243: in 185 at least one line of `old_string` appears in
  no earlier read or command output of that session (67 with no line seen at all); 16 are backslash or quote
  escaping; 2 are whitespace only. 115 of the 243 are longer than three lines.

## T-e4b-006: pattern and evidence

Pattern: the harness compacts the history at 14,336 prompt tokens. The prompt starts at about 3,200
tokens, and the model's own output (thought text plus the call) is 48%, 51% and 46% of all context growth
in d1, d2, d3. Compaction therefore arrives early, and the edits that follow are written from memory.

| Count | d1 | d2 | d3 |
|---|---|---|---|
| Tasks with at least one compaction (prompt-token drop of over 40% from above 8,000) | 21 | 29 | 24 |
| Compactions | 30 | 36 | 30 |
| Call number of the first compaction, range | 6-14 | 7-16 | 7-16 |
| Edit calls before any compaction: failed / all | 51/109 (47%) | 107/153 (70%) | 58/120 (48%) |
| Edit calls after a compaction: failed / all | 29/38 (76%) | 55/72 (76%) | 35/53 (66%) |
| Edit calls after a compaction on a file not re-read since it | 21 | 27 | 23 |
| Resolved, tasks with a compaction | 1/21 | 4/29 | 0/24 |
| Resolved, tasks without | 3/35 | 3/27 | 7/32 |

Caveat: sessions that fail edits run longer and so compact more; the table shows association, and the run
is the test of cause.

Traces (call number: what happened; miss against the reference patch):

- rich_3930 d1: calls 6 and 8 read `cells.py`; compaction after call 8 (16,032 -> 8,583 tokens); calls
  9-13 are five edits with a 20-line `old_string`, all not found; call 14 submits an empty patch. Miss: no
  edit (reference: 4 hunks in that file and 25 other files).
- rich_3468 d2: calls 2-13 read `console.py`; compaction after call 9 (14,661 -> 7,576); calls 14-20 are
  six edits of 17 to 58 lines, all not found, a second compaction after call 19; empty patch. Miss: no
  edit, right file (reference: 4 hunks in `console.py`).
- fastapi_14258 d2: edits at calls 11-14 not found; compaction after call 14 (14,399 -> 8,090); calls 15
  and 16 send a 41-line `old_string`, not found; three empty submits. Miss: no edit, and aimed at the wrong
  file (`applications.py`; reference: 1 hunk in `routing.py`).
- fastapi_15588 d2: compaction after call 16 (14,708 -> 3,241); edits at calls 17, 18, 20 not found.
  Miss: partial (1 of 2 reference hunks).
- rich_3944 d3: compaction after call 14 (14,543 -> 3,036); calls 15-21 repeat the earlier read and greps
  and two more ambiguous edits; empty patch. Miss: no edit, wrong file.
- rich_3772 d3: one edit at call 6, `pytest tests/` at call 7, compaction after call 8 (16,076 ->
  7,647); edits at calls 9 and 11-14 not found. Miss: wrong region (2 hunks, reference 6).

Process endpoints (base values counted above):

1. Tasks with at least one compaction: base 21, 29, 24 per draw (mean 24.7). Expected under 12 per draw.
2. Edit calls made after a compaction: base 38, 72, 53 (mean 54.3). Expected under 25 per draw.
3. Guard: tasks ending at the 8-minute cap stay at 0 to 1 per draw, and median wall time does not rise
   by more than half (base median about 65 s).

## T-e4b-007: pattern and evidence

Pattern: the check step of the base prompt gives the model no usable signal, and patches that do not parse
are submitted.

- 141 task-draws have a successful edit. 46 run no command after it. The other 95 issue 112 pytest
  commands after the first successful edit: 39 broad runs whose 5,000-character output is cut before any
  summary (`pytest tests/`, bare `pytest`), 22 on a test path that does not exist (the prompt's
  `tests/test_file.py` template filled with an invented name), 18 stopped by an import error at collection,
  11 showing a syntax error in the edited file, 7 that ran no test, 2 other errors, 10 all-pass, 3 with a
  failing test. So 13 of 112 return a pass or fail. No task-draw runs a `python -c` check.
- None of the 18 resolved task-draws had a passing pytest check; all 10 all-pass results are on
  unresolved patches.
- Submitted non-empty patches whose grader output is a SyntaxError or IndentationError: 2, 7, 5 per draw
  (14 task-draws, 10 tasks: fastapi_13920, fastapi_14306, fastapi_15280, fastapi_15800, rich_3180,
  rich_3480, rich_3772, rich_3894, rich_3930, rich_3935). In 8 of the 14 the agent never saw the error (5
  ran no check after the last edit, 3 ran pytest on a missing path); in 6 a broad pytest showed it and the
  repair edits failed or were not made.

Traces:

- fastapi_15280 d1: successful edit at call 7, `submit_patch` at call 8, no check; grader: `SyntaxError:
  expected ':'`. d2: edit at call 4, submit at call 5; `SyntaxError: invalid syntax`. d3: `pytest tests/`
  at call 6, a second edit at call 7, submit; `IndentationError`. Miss in all three: wrong region of the
  right file (reference: 2 hunks in `applications.py`).
- rich_3894 d2: edit at call 3, call 4 is `pytest tests/test_rich/_inspect.py -q` (no such path), submit;
  grader: `SyntaxError: invalid syntax`. Miss: wrong logic in the right file and region; the same task
  resolved in d3.
- rich_3480 d2: `write_file` at call 10, call 11 is `pytest rich/test_text.py -q` (no such path), submit;
  grader: `IndentationError: unexpected indent`. Miss: wrong logic, both reference hunks reached. d1:
  `pytest tests/` at call 4 showed the IndentationError, repair edits at calls 5, 6, 8 not found; wrong
  file.
- rich_3935 d2: read, edit, submit in 3 calls; grader: `SyntaxError: cannot assign to expression`. Miss:
  wrong file (`padding.py`, reference `table.py`).
- rich_4077 d1: call 4 `pytest tests/test_console.py`, 100 passed, submit. Miss: wrong file (`console.py`,
  reference `file_proxy.py`). The passing check said nothing about the change.

Expected size: small. Of the 14 unparseable patches only 2 are in the right file and region (rich_3894 d2,
rich_3480 d2) and 3 more are partial; the rest would still miss on location. The second effect is fewer
calls and less context spent on pytest output (which also feeds T-006's compaction count).

Process endpoints:

1. Submitted non-empty patches that fail to parse at grading (SyntaxError or IndentationError in
   `test_tail`): base 2, 7, 5 per draw (mean 4.7). Expected at most 1 per draw.
2. Pytest commands after the first successful edit: base 112 over three draws (mean 37 per draw). Expected
   under 8 per draw, with the `python -m ast` command present in at least 30 of the task-draws that have a
   successful edit (base 0). If the command appears in fewer than 15, the template is not being followed
   and the result is a compliance reading, not a verdict on the idea.

Not checked: neither tree was run through `tools/validate_submission.py` (host Python is 3.6). The new
prompt text contains none of the forbidden words. `python -m ast` needs Python 3.9 or later in the
sandbox (the traces show 3.12) and writes no bytecode file into the workspace.

## Readings

Fixed by the operator 2026-11-18T12:50Z, before any run of either tree.

- Three draws of each tree on cdev-56 at concurrency 4. Base pooled over three draws: 4, 7, 7 (mean 6.0).
- Kept: three-draw mean >= 9.0. Mean in [8.0, 9.0): positive, not kept, may be composed.
- T-e4b-006 endpoint: tasks with a compaction (21, 29, 24 in the base) under 12 per draw. Guard: empty patches above 12 in any draw means the missing thoughts broke continuity; not kept.
- T-e4b-007 endpoint: submitted patches that fail to parse at grading (2, 7, 5 in the base) at most 1 per draw.
- Neither edit targets the largest miss class the proposer counted (wrong file: 18, 12, 11). Whatever these give, the next E4B round must take that class.

## Results

(appended after the runs)

### T-e4b-006 nothoughts, read 2026-11-18T16:45Z

5, 5, 5 (mean 5.0) against base 4, 7, 7 (6.0): not kept.

### T-e4b-007 syntaxcheck, read 2026-11-18T18:35Z

7, 7, 5 (mean 6.3) against base 4, 7, 7 (6.0): +0.3, not kept. Empty patches 9, 11, 7.
