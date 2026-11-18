# Trace vs reference: why the never-resolved tasks fail

Zero-GPU analysis, 2026-11-18. Script: `tools/trace_vs_reference.py` (stdlib, Python 3.6+).
Quoted test and statement text is redacted here; the full copy is `runs/_analysis/trace-vs-reference.unredacted.md`. Per-draw rows: `runs/_analysis/trace_vs_reference.frozen.jsonl` (gitignored; snapshot taken 2026-11-18T19:27Z).
The S-000 runs were still writing rows; everything below uses the snapshot only.

## Headline

- Gradeable tasks: 101. Of these, 79 have at least one draw so far.
- 31B: 470 draws on 56 tasks. 26 of the 56 are never resolved. 286 draws fail, and 214 of them are on never-resolved tasks.
- E4B: 1573 draws on 79 tasks. 56 of the 79 are never resolved. 1398 draws fail, and 992 of them are on never-resolved tasks.
- Pooled: 45 of 79 attempted tasks have no resolved draw from either model. 58 tasks are never resolved by at least one model; 24 are never resolved by both.
- The two models fail in different ways. 31B mostly runs out of time before it edits (105 of 286 failing draws), or edits only part of a multi-hunk fix (69 of 286). E4B mostly edits too early in the wrong file (440 of 1398) or the wrong part of the right file (349 of 1398).
- No grading failure looks like an environment problem. The list is in section (f).

## (a) Method

Inputs.
- `data/raw/tasks.jsonl`: problem statement, reference `patch` and `test_patch`.
- Gradeable set: resolved in `runs/C-000-gold-all` or `runs/C-001-gold-all-shims`, and not resolved in `runs/C-000-empty-all` or `runs/C-001-empty-all-shims`. That gives 101 tasks. 29 of them grade only with shims.
- Draws: every `runs/R-*`, `S-*` and `F-*` with `task_results.jsonl` and `traces/trace_<id>.json`. `runs/_smoke-*` is skipped. The model comes from the run name.
- A run uses shims if its `summary.json` start time is at or after 2026-11-18T17:10Z. A draw on a shim-only task in a run without shims is not counted. There were 2 such draws, both `fastapi_14605` in F-000, and both failed for agent reasons.
- Never-resolved: attempted in at least one draw, resolved in none. Counted per model.

Per draw, the script computes the following.
1. Reference hunks, in old-file line numbers, from the reference patch.
   - A hunk that only re-wraps code, changes comments, reorders an import line, or moves a line to another hunk counts as cosmetic. The script drops it.
   - 12 of 79 tasks have cosmetic hunks. Example: `rich_3468`'s two black re-wraps.
   - All hunk counts below are substantive hunks.
2. Agent files and hunks, from the final patch in `task_results.jsonl`, which is the patch that was graded.
   - The harness strips protected files from that patch: `tests/`, `test_*.py`, `conftest.py`, `pyproject.toml` and others.
   - A new file at the repo root that the reference does not have (`repro.py`, `debug_wrap.py`) is a scratch script. It does not count as a source edit.
3. From the trace, before the first successful source edit:
   - whether a reference file path appeared in any tool output;
   - whether a reference file was read (`read_file`, or `cat`/`sed -n`/`head`/`nl` in `run_command`);
   - whether the reads covered each reference hunk.
4. Overlap: a reference hunk counts as touched if an agent hunk in the same file comes within 5 lines of it.
5. Edit failures, from tool observations: malformed args (the parser dropped `old_string`), `old_string` not found, not unique, and no-op.
   - `BudgetExceeded` refusals and refused writes outside the repo (`/tmp`) are counted apart. They are not edit failures.
6. Session end, from the row's `error`: time cap (8 min), call cap (28), turn cap, no submit, or submitted.
7. Whether a test or check command ran after the last edit, and whether it exited 0.
8. Grading tail: the first `E ` line of `test_tail`, and its kind (assertion, collection error, syntax error, other).
   - An environment flag is raised for ModuleNotFoundError or ImportError on a non-repo module, VersionConflict, or a missing fixture.
   - The flag is not raised when the agent's own patch added that import.

Primary class of a failing draw, first match wins:
1. **no-edit/empty patch**: no reference file and no other source file in the final patch.
   - If there were 2 or more failed edit calls, or 1 failed edit call that was not in the last 3 calls, the draw is **edit-tool failure** instead.
2. **wrong file**: other source files are patched, but no reference file is. If an edit to a reference file failed, the draw is **edit-tool failure**.
3. **right file wrong region**: a reference file is patched, but no reference hunk is touched.
4. **partial fix**: some reference hunks are touched, but not all.
5. **all hunks touched, wrong change**: every reference hunk is touched, and the test still fails.

Hand-checks.
- I read about 50 traces against the reference, with at least 3 per class per model.
- For the E4B wrong-region, partial and all-touched classes, some checks used the patch, the facts and the test tail rather than the full trace.
- Four fixes came out of the checks:
  - `BudgetExceeded` and `/tmp` refusals had made 51 31B draws look like edit-tool failures.
  - A single malformed edit at the call cap was being called an edit-tool failure (`rich_3472` 31B think1024). It is now no-edit.
  - Agent-introduced bad imports raised the env flag (`from warnings import Warning`, `fastapi_14605`).
  - Root-level repro scripts made 6 31B no-edit draws look like wrong file.
  - Black re-wraps were also inflating the hunk counts, for example `rich_3468`, `rich_4070` and `rich_4075`.

Known limits of the classifier.
- Overlap is by line distance. A fix in a nearby function of the same file can be "wrong region" and still be close in meaning. For example, `rich_3468` 31B catches BrokenPipeError in `_write_buffer`, while the reference catches it in `_check_buffer`.
- A "partial fix" on a 20+ hunk reference (`rich_4070`, `fastapi_15800`, `rich_3930`) is close to automatic.
- The cluster runs 4 sessions at once on one GPU, with the 8 min cap unscaled. Time-cap counts for 31B are therefore higher than they would be alone.

## (b) Class tables

Percentages are of the row's denominator.

### 31B
| class | never-resolved draws | all failing draws |
|---|---|---|
| no-edit/empty patch | 65 / 214 (30%) | 105 / 286 (37%) |
| edit-tool failure | 9 / 214 (4%) | 14 / 286 (5%) |
| wrong file | 30 / 214 (14%) | 34 / 286 (12%) |
| right file wrong region | 26 / 214 (12%) | 32 / 286 (11%) |
| partial fix | 60 / 214 (28%) | 69 / 286 (24%) |
| all hunks touched, wrong change | 24 / 214 (11%) | 32 / 286 (11%) |

### E4B
| class | never-resolved draws | all failing draws |
|---|---|---|
| no-edit/empty patch | 37 / 992 (4%) | 44 / 1398 (3%) |
| edit-tool failure | 93 / 992 (9%) | 144 / 1398 (10%) |
| wrong file | 336 / 992 (34%) | 440 / 1398 (31%) |
| right file wrong region | 197 / 992 (20%) | 349 / 1398 (25%) |
| partial fix | 227 / 992 (23%) | 260 / 1398 (19%) |
| all hunks touched, wrong change | 102 / 992 (10%) | 161 / 1398 (12%) |

Facts per class, over all failing draws. "Read" means a reference file was read before the first edit, or before the session ended if there was no edit. "All hunks read" means the reads covered every substantive hunk.

| model | class | n | median calls | ends | ref read | all hunks read | check ran after last edit (passed) |
|---|---|---|---|---|---|---|---|
| 31B | no-edit | 105 | 18 | time 80, calls 24, submitted 1 | 86 | 51 | 2 (2) |
| 31B | edit-tool | 14 | 21 | time 11, calls 3 | 11 | 8 | 0 |
| 31B | wrong file | 34 | 23 | submitted 19, time 11, calls 4 | 2 | 2 | 18 (12) |
| 31B | wrong region | 32 | 22.5 | submitted 15, time 10, calls 7 | 32 | 13 | 17 (10) |
| 31B | partial | 69 | 19 | submitted 38, time 16, calls 13, turns 2 | 69 | 9 | 32 (30) |
| 31B | all touched | 32 | 21.5 | submitted 19, time 8, calls 4, turns 1 | 29 | 29 | 18 (16) |
| E4B | no-edit | 44 | 3 | submitted 28, no submit 16 | 4 | 1 | 13 (11) |
| E4B | edit-tool | 144 | 12 | submitted 132, calls 8, time 2, no submit 2 | 112 | 45 | 18 (6) |
| E4B | wrong file | 440 | 8 | submitted 437, calls 3 | 55 | 2 | 255 (86) |
| E4B | wrong region | 349 | 7 | submitted 342, calls 6, time 1 | 346 | 58 | 193 (48) |
| E4B | partial | 260 | 9 | submitted 249, calls 9, time 2 | 260 | 41 | 138 (38) |
| E4B | all touched | 161 | 6 | submitted 157, calls 3, time 1 | 159 | 141 | 94 (22) |

How sessions end, over all draws.
- 31B: 136 of 470 hit the time cap, and 0 of those 136 resolved. 62 of 470 hit the call cap, and 7 of those 62 resolved.
- E4B: 1520 of 1573 submitted. 29 hit the call cap and 6 hit the time cap, and none of those 35 resolved.
- 31B is slow per call. Time-cap no-edit draws take a median 34.5 s per call; resolved draws take 16.8 s.
- E4B is quick. Its failing draws take a median 70 s.

Syntax errors in the graded tree, as the grading tail shows them: 31B 10 of 286 failing draws, E4B 130 of 1398.

## (c) Never-resolved tasks, per model

"Substantive hunks" excludes cosmetic hunks. "Other model resolved it" means at least one draw of the other model resolved the task.

### 31B: 26 never-resolved tasks
| task | draws | dominant class (k/n) | ref files / substantive hunks | note |
|---|---|---|---|---|
| fastapi_13920 | 9 | wrong file (5/9) | 1 / 2 | edits fastapi/_compat/shared.py in 6/9; ref file read in 1/9 |
| fastapi_14258 | 8 | all touched (7/8) | 1 / 1 | test: FastAPIError (text in the gitignored copy) |
| fastapi_14306 | 8 | partial (5/8) | 2 / 12 | median 1 of 12 hunks overlapped |
| fastapi_14448 | 9 | partial (6/9) | 2 / 3 | median 1.0 of 3 hunks overlapped |
| fastapi_14487 | 8 | all touched (6/8) | 1 / 1 | test: AssertionError (text in the gitignored copy) |
| fastapi_15280 | 8 | no-edit (4/8) | 2 / 3 | ends: call cap 3, time cap 1; short statement |
| fastapi_15588 | 9 | all touched (8/9) | 1 / 2 | test: AssertionError (text in the gitignored copy) |
| fastapi_15661 | 9 | wrong file (4/9) | 1 / 1 | edits scripts/release.py in 4/9; test imports scripts.prepare_release, a name the statement never gives |
| fastapi_15800 | 8 | partial (4/8) | 8 / 20 | median 1.0 of 20 hunks overlapped |
| rich_3061 | 8 | partial (5/8) | 1 / 12 | median 1 of 12 hunks overlapped |
| rich_3105 | 8 | wrong file (5/8) | 1 / 1 | statement is an issue-number-only statement plus a checklist; ref file read in 0/8 |
| rich_3180 | 8 | no-edit (8/8) | 2 / 4 | ends: time cap 8; ref files read in 8/8 |
| rich_3468 | 9 | wrong region (8/9) | 1 / 2 | ref file read in 9/9; 0 ref hunks overlapped; short statement |
| rich_3472 | 8 | no-edit (7/8) | 1 / 1 | ends: call cap 4, time cap 3; short statement |
| rich_3535 | 8 | partial (7/8) | 2 / 2 | median 1 of 2 hunks overlapped; other model resolved it |
| rich_3675 | 8 | partial (8/8) | 2 / 4 | median 1.0 of 4 hunks overlapped; short statement |
| rich_3676 | 8 | partial (7/8) | 2 / 7 | median 4 of 7 hunks overlapped; short statement |
| rich_3772 | 8 | wrong region (7/8) | 1 / 6 | ref file read in 8/8; 0 ref hunks overlapped; short statement; other model resolved it |
| rich_3930 | 8 | partial (6/8) | 26 / 28 | median 2.0 of 28 hunks overlapped |
| rich_3934 | 8 | wrong region (4/8) | 2 / 2 | ref file read in 8/8; 0 ref hunks overlapped; short statement |
| rich_3935 | 8 | no-edit (5/8) | 1 / 1 | ends: time cap 5; short statement |
| rich_3944 | 9 | wrong file (6/9) | 1 / 1 | edits rich/_export_format.py in 5/9; ref file read in 0/9; short statement |
| rich_3953 | 8 | partial (4/8) | 1 / 2 | median 1.0 of 2 hunks overlapped; short statement |
| rich_4070 | 8 | partial (8/8) | 9 / 23 | median 5.0 of 23 hunks overlapped |
| rich_4075 | 8 | no-edit (7/8) | 1 / 1 | ends: call cap 5, time cap 2; a Python-version line in the statement pulls it to pyproject.toml; short statement |
| rich_4076 | 8 | wrong file (4/8) | 1 / 1 | edits rich/pretty.py in 3/8; ref file read in 1/8; short statement |

### E4B: 56 never-resolved tasks
| task | draws | dominant class (k/n) | ref files / substantive hunks | note |
|---|---|---|---|---|
| fastapi_11355 | 3 | wrong file (2/3) | 1 / 3 | edits fastapi/params.py in 1/3; ref file read in 1/3 |
| fastapi_12942 | 3 | wrong file (2/3) | 1 / 1 | edits fastapi/params.py in 2/3; ref file read in 0/3 |
| fastapi_13713 | 3 | wrong region (2/3) | 2 / 5 | ref file read in 3/3; 0 ref hunks overlapped |
| fastapi_13786 | 3 | partial (3/3) | 11 / 25 | median 3 of 25 hunks overlapped |
| fastapi_13920 | 28 | wrong file (26/28) | 1 / 2 | edits fastapi/utils.py in 14/28; ref file read in 2/28 |
| fastapi_14099 | 3 | no-edit (1/3) | 5 / 13 | ends: submitted 1 |
| fastapi_14258 | 26 | edit-tool (10/26) | 1 / 1 | failed edit calls: old_string not found 120, old_string not unique 25 |
| fastapi_14262 | 3 | partial (2/3) | 10 / 29 | median 1.0 of 29 hunks overlapped |
| fastapi_14266 | 3 | wrong file (3/3) | 1 / 2 | edits fastapi/openapi/utils.py in 3/3; ref file read in 0/3 |
| fastapi_14297 | 3 | all touched (3/3) | 1 / 1 | test: TypeError (text in the gitignored copy) |
| fastapi_14306 | 26 | partial (26/26) | 2 / 12 | median 1.0 of 12 hunks overlapped |
| fastapi_14349 | 3 | wrong file (1/3) | 1 / 1 | edits fastapi/openapi/utils.py in 1/3; ref file read in 1/3; short statement |
| fastapi_14356 | 3 | wrong region (1/3) | 1 / 1 | ref file read in 2/3; 0 ref hunks overlapped |
| fastapi_14360 | 3 | all touched (2/3) | 1 / 1 | test: AssertionError (text in the gitignored copy) |
| fastapi_14419 | 29 | partial (25/29) | 2 / 7 | median 1 of 7 hunks overlapped; other model resolved it |
| fastapi_14430 | 3 | wrong file (2/3) | 1 / 2 | edits fastapi/types.py in 2/3; ref file read in 1/3 |
| fastapi_14448 | 27 | partial (14/27) | 2 / 3 | median 1.0 of 3 hunks overlapped |
| fastapi_14459 | 3 | wrong region (2/3) | 3 / 8 | ref file read in 3/3; 0 ref hunks overlapped |
| fastapi_14482 | 3 | wrong file (2/3) | 1 / 5 | edits fastapi/_compat/shared.py in 1/3; ref file read in 0/3 |
| fastapi_14487 | 26 | wrong file (22/26) | 1 / 1 | edits fastapi/exceptions.py in 9/26; ref file read in 4/26 |
| fastapi_14512 | 3 | wrong file (2/3) | 1 / 3 | edits fastapi/params.py in 1/3; ref file read in 0/3 |
| fastapi_14583 | 3 | wrong file (3/3) | 2 / 6 | edits fastapi/_compat/v1.py in 3/3; ref file read in 0/3; short statement |
| fastapi_14605 | 3 | partial (2/3) | 7 / 20 | median 1.0 of 20 hunks overlapped |
| fastapi_14609 | 3 | partial (3/3) | 20 / 91 | median 3 of 91 hunks overlapped |
| fastapi_14953 | 3 | partial (3/3) | 4 / 5 | median 1 of 5 hunks overlapped |
| fastapi_15023 | 3 | wrong file (2/3) | 1 / 1 | edits docs_src/stream_data/tutorial001_py310.py in 1/3; ref file read in 0/3; short statement |
| fastapi_15030 | 3 | wrong region (3/3) | 9 / 17 | ref file read in 3/3; 0 ref hunks overlapped |
| fastapi_15280 | 28 | wrong region (20/28) | 2 / 3 | ref file read in 28/28; 0 ref hunks overlapped; short statement |
| fastapi_15588 | 26 | all touched (23/26) | 1 / 2 | test: AssertionError (text in the gitignored copy) |
| fastapi_15661 | 28 | wrong file (22/28) | 1 / 1 | edits scripts/add_latest_release_date.py in 22/28; test imports scripts.prepare_release, a name the statement never gives |
| fastapi_15800 | 26 | partial (13/26) | 8 / 20 | median 1 of 20 hunks overlapped |
| fastapi_5077 | 26 | partial (18/26) | 1 / 2 | median 1.0 of 2 hunks overlapped; other model resolved it |
| fastapi_5624 | 28 | wrong file (21/28) | 1 / 1 | edits fastapi/security/oauth2.py in 17/28; ref file read in 6/28; short statement; other model resolved it |
| rich_3061 | 26 | partial (17/26) | 1 / 12 | median 1 of 12 hunks overlapped |
| rich_3063 | 26 | edit-tool (13/26) | 1 / 1 | failed edit calls: old_string not found 135, malformed args 7; short statement; other model resolved it |
| rich_3105 | 28 | wrong file (26/28) | 1 / 1 | edits rich/_cell_widths.py in 12/28; ref file read in 0/28 |
| rich_3180 | 26 | partial (24/26) | 2 / 4 | median 1.0 of 4 hunks overlapped |
| rich_3278 | 26 | all touched (11/26) | 1 / 1 | edit-tool failure in 10/26; other model resolved it |
| rich_3468 | 27 | wrong region (16/27) | 1 / 2 | ref file read in 24/27; 0 ref hunks overlapped; short statement |
| rich_3472 | 26 | wrong file (21/26) | 1 / 1 | edits rich/console.py in 10/26; ref file read in 8/26; short statement |
| rich_3480 | 26 | wrong file (16/26) | 1 / 2 | edits rich/_inspect.py in 6/26; ref file read in 9/26; short statement; other model resolved it |
| rich_3521 | 26 | all touched (23/26) | 1 / 1 | test: AssertionError (text in the gitignored copy); short statement; other model resolved it |
| rich_3675 | 26 | wrong region (17/26) | 2 / 4 | ref file read in 24/26; 0 ref hunks overlapped; short statement |
| rich_3676 | 28 | wrong region (19/28) | 2 / 7 | ref file read in 26/28; 0 ref hunks overlapped; short statement |
| rich_3718 | 26 | wrong region (21/26) | 1 / 3 | ref file read in 26/26; 0 ref hunks overlapped; other model resolved it |
| rich_3782 | 26 | wrong file (16/26) | 1 / 6 | edits rich/padding.py in 11/26; ref file read in 20/26; short statement; other model resolved it |
| rich_3882 | 26 | all touched (22/26) | 1 / 1 | test: AssertionError (text in the gitignored copy); other model resolved it |
| rich_3930 | 26 | partial (12/26) | 26 / 28 | median 1.0 of 28 hunks overlapped |
| rich_3934 | 26 | wrong region (23/26) | 2 / 2 | ref file read in 26/26; 0 ref hunks overlapped; short statement |
| rich_3935 | 26 | wrong file (21/26) | 1 / 1 | edits rich/padding.py in 20/26; ref file read in 1/26; short statement |
| rich_3944 | 26 | wrong file (23/26) | 1 / 1 | edits rich/_export_format.py in 12/26; ref file read in 0/26; short statement |
| rich_3953 | 26 | partial (13/26) | 1 / 2 | median 1 of 2 hunks overlapped; short statement |
| rich_4070 | 26 | partial (26/26) | 9 / 23 | median 3.0 of 23 hunks overlapped |
| rich_4075 | 26 | no-edit (18/26) | 1 / 1 | only pyproject.toml edited (stripped by the harness) in 23/26; short statement |
| rich_4076 | 26 | wrong file (24/26) | 1 / 1 | edits rich/text.py in 9/26; ref file read in 0/26; short statement |
| rich_4079 | 28 | wrong file (22/28) | 1 / 1 | edits rich/table.py in 21/28; ref file read in 3/28; short statement; other model resolved it |

## (d) Patterns

1. **31B runs out of time before it edits.**
   - 105 of 286 failing 31B draws end with no source edit. 80 of those 105 hit the 8 min time cap and 24 hit the call cap.
   - It had found the place. 86 of 105 had read a reference file, and 51 of 105 had read every reference hunk.
   - No 31B draw that hit the time cap resolved (0 of 136).
   - Evidence:
     - `rich_3180` ends at the time cap in all 8 of 8 draws, after reading both reference files.
     - `rich_3472` is no-edit in 7 of 8 draws. Even in the one draw that edited (calls40-d1), it had read the reference lines (`pretty.py` 780-820) by call 8, but made its first edit only at call 14, 188 s in, in the wrong place.
     - `rich_3935` is no-edit in 5 of 8 draws, and `rich_4075` in 7 of 8.
     - `rich_3934` (inline-scratch) has long gaps between calls.
2. **Edit calls break, and E4B gives up on them.**
   - 31B: 354 edit calls with malformed args across the failing draws. 58 of 286 failing draws have at least one, and so do 44 of 184 resolved draws. The tool-call parser splits an `old_string` that contains `x: y, z` text into bogus keys.
   - E4B: 2125 `old_string not found`, 322 `not unique` and 393 malformed calls. 627 of 1398 failing draws have at least one failed edit, and 144 of 1398 fail mainly because of them.
   - Evidence:
     - `rich_3782` 31B base-d1 has 10 malformed edits.
     - `fastapi_15280` E4B short-d3 has 7 `not found` in a row, then submits an empty patch.
     - `fastapi_14258` E4B has 120 `not found` calls over 26 draws.
     - `rich_3063` E4B has 135 `not found` calls over 26 draws.
3. **E4B submits an empty patch and says it is done.**
   - 187 of 1398 failing E4B draws have an empty final patch, and 167 of those 187 called `submit_patch`.
   - The tool answers `patch_size: 0, files_changed: 0`. The final message still describes a fix.
   - Evidence: `fastapi_15280` short-d3 (agent message in the gitignored copy), `fastapi_14099` base-x1.
4. **E4B edits the first file its search turns up.**
   - Wrong file is 440 of 1398 failing E4B draws. In those 440, the reference file was named in a tool output before the first edit in only 69, and read in only 55.
   - The median first edit comes at call 6.
   - Evidence:
     - `fastapi_5624`: `security/oauth2.py` in 17 of 28 draws, while the reference is `dependencies/utils.py`.
     - `rich_3935`: `padding.py` in 20 of 26 draws, while the reference is `table.py`.
     - `rich_4079`: `table.py` in 21 of 28 draws, while the reference is `markdown.py`.
     - `fastapi_13920`: `utils.py` or `types.py` in 22 of 28 draws, while the reference is `dependencies/utils.py`.
   - 31B is wrong file in 34 of 286 failing draws, and read the reference file in only 2 of those 34.
5. **Thin problem statements.**
   - A statement counts as short when it is under 120 characters after URLs and comments are removed.
   - 31B never resolves 12 of 21 short-statement tasks, against 14 of 35 longer ones. E4B never resolves 20 of 24 short ones, against 36 of 55.
   - Evidence:
     - `rich_3944` "fix fonts" (reference in `cells.py`; both models edit `_export_format.py`).
     - `rich_4076` "preserve newlines".
     - `rich_3105` an issue-number-only statement plus a checklist. 31B inline-scratch grepped for "3104" for 28 calls.
     - `rich_4075` a short statement that mentions a Python-version drop. It sends E4B to `pyproject.toml`, which the harness strips; 23 of 26 E4B draws end with only that edit and an empty patch.
6. **Multi-hunk and multi-file references are almost never solved (capability).**
   - Resolve rate by number of substantive reference hunks:
     | substantive hunks | 31B resolved | E4B resolved |
     |---|---|---|
     | 1 | 134 / 252 | 132 / 833 |
     | 2-3 | 46 / 128 | 42 / 416 |
     | 4-9 | 4 / 50 | 1 / 176 |
     | 10+ | 0 / 40 | 0 / 148 |
   - Two or more reference files: 31B 2 of 98, E4B 1 of 350.
   - Every task with 10 or more hunks is never resolved: 5 of 5 for 31B, 11 of 11 for E4B.
   - 31B partial-fix draws all read a reference file (69 of 69), but only 9 of 69 had read every hunk before the first edit.
   - Evidence: `rich_4070` (23 hunks in 9 files), `fastapi_15800` (20 in 8), `rich_3930` (28 in 26), `fastapi_14306` (12 in 2).
7. **E4B reads the right file and edits the wrong part of it.**
   - Wrong region is 349 of 1398 failing E4B draws. 346 of 349 had read the reference file, but only 58 had read the reference hunks.
   - Evidence: `rich_3934` 23 of 26, `rich_3718` 21 of 26, `fastapi_15280` 20 of 28, `rich_3676` 19 of 28.
   - 31B shows this on `rich_3468` 8 of 9 and `rich_3772` 7 of 8. In `rich_3772` 31B edits `install()`, while the reference changes `extract()`.
8. **Right place, plausible change, but the hidden test pins a name, message or exception type that the statement does not give.**
   - `fastapi_15661`: 32 of 37 draws fail on a ModuleNotFoundError for a module. The reference creates that file, and the statement never names it.
   - `rich_3930`: 20 of 34 fail on `cannot import name 'CellSpan'`, a name absent from the statement.
   - `fastapi_15588`: 31B is all-touched in 8 of 9 draws; the test fails with "Regex pattern did not match" on the error text.
   - `fastapi_14258`: the test wants an `AssertionError`, and the agents raise `FastAPIError`.
   - `fastapi_14487`: the test wants the text to start with "Validation errors:".
9. **The agent's own check says little.**
   - 31B: 87 of 286 failing draws ran a check after the last edit, and it passed in 70 of 87.
   - E4B: 711 of 1398 failing draws ran one, and 211 passed. On resolved E4B draws the check passed in only 33 of 109.
   - In 149 of 1573 E4B draws the agent's own pytest hit a missing `dirty_equals` or `inline_snapshot`. 40 of those 149 resolved anyway. No 31B draw hit it.
10. **Small: E4B makes no tool calls at all.** This happens in 14 of 1573 draws. It writes the calls as text instead, for example `rich_3675` base-d1 and `rich_4079`.

## (e) What a prompt or budget change could reach

These look reachable with a prompt or budget change:

- **Pattern 1 (31B time cap): budget and prompt.**
  - 80 time-cap no-edit draws, and 51 of 105 no-edit draws had already read every hunk.
  - A rule to edit as soon as the region is read, or a scaled time cap, targets about 80 of 286 failing 31B draws.
  - Caveat: on Kaggle the cap is 4.5 min. The cluster runs 4 sessions at once on one GPU, so the cluster counts mix model slowness with contention.
- **Pattern 2 (edit failures): prompt.**
  - Short, single-line `old_string` anchors without `key: value, ...` text would avoid the parser split. Re-reading the lines before retrying after `not found` would help E4B.
  - Up to 144 E4B and 14 31B failing draws are in this class. Most 31B draws with a malformed edit still recover (44 resolved).
- **Pattern 3 (empty submit): prompt or harness nudge.**
  - "If `submit_patch` reports `files_changed: 0`, you are not done."
  - This covers 167 E4B draws. It fixes the stop, not the edit, so the true gain is smaller.
- **Pattern 5 (protected files): one prompt line.**
  - Changes to `pyproject.toml` and tests are discarded.
  - This reaches only `rich_4075` (24 draws).
- **Pattern 4 (first-hit localization): partly prompt.**
  - Ask for the reference symbol's definition and callers to be read before the first edit.
  - E4B named the reference file in only 69 of 440 wrong-file draws, so search breadth is the gap. A second search may help; earlier rounds (R-005 twosearch/filerank) are the place to check.

These look like capability limits:

- **Pattern 6.** Multi-hunk and multi-file changes. 0 of 188 draws resolved on 10+ hunk references.
- **Pattern 7.** Wrong region in E4B, beyond what reading would fix.
- **Pattern 8.** Hidden interface names and exact messages. A prompt cannot supply names the statement does not give.
- The "all hunks touched, wrong change" class: 32 of 286 31B failing draws and 161 of 1398 E4B.
- **Patterns 5 and 6 together.** Thin statements on rich tasks, where the fix needs knowledge of the issue the model cannot see.

## (f) Grading or environment problems

None found among the graded tails.
- The environment flag fired on 0 of 1684 failing draws.
- 117 failing draws have collection errors. Each one is caused by the agent's patch or by a name the reference adds, not by the sandbox:
  - a repo symbol that the reference adds: `scripts.prepare_release` in 34 draws, `CellSpan` in 20
  - a name the agent's own edit removed: `inspect`, after its import was dropped, in 12
  - a name the agent invented, or a regex error in the agent's code
- The 2 shim-only draws without shims (F-000, `fastapi_14605`) failed on the agent's own `EndpointContext` and syntax errors.

Related, but not grading problems:
- **Agent sandbox:** 149 E4B draws hit a missing `dirty_equals` or `inline_snapshot` in their own pytest runs (pattern 9). This misleads the agent. It does not affect the grade.
- **Specification gaps:** `fastapi_15661` and `rich_3930` need names that the problem statement does not give (pattern 8). This is a task-text issue, not an environment one.
