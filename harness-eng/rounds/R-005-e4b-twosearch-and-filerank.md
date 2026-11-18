# R-005 (e4b): two searches before the first read; a search that ranks files by hit count

Written 2026-11-18 by the proposer (`proposer/PROPOSER.md` v1.2), before any R-005 run and without reading
any R-003 or R-004 result. Nothing here has been run on a GPU.

- Base: `trees/e4b-base`.
- Draws read: `R-000-e4b-base-d1`, `-d2`, `-d3` on `cohorts/cdev-56.txt` (56 tasks each, 168 task-draws).
  Resolved 4, 7, 7.
- Traces read call by call: all 43 wrong-file task-draws (22 distinct tasks). All 168 counted by script from
  `traces/` and `task_results.jsonl`. For the question "which search shows the reference file", the search
  commands of the 14 E4B runs under `runs/R-00*-e4b-*` were scanned as well (search outputs only, no results).
- Both edits target the largest miss class, wrong file.

## Proposals

| Tweak | Kind | Tree | Change (one sentence) | Evidence (task ids, draw) |
|---|---|---|---|---|
| T-e4b-008 | process (order of work) | `trees/e4b-r005-twosearch` | `prompts/system.md` section 2: "Search once" and the "one follow-up grep" bullet are replaced by "tool calls 1 and 2 are both searches, on two different single words; edit the file that fits both" (prompt 3,162 -> 3,325 bytes). | rich_3935 d1 d2 d3, rich_4076 d2, rich_3480 d1 d3, fastapi_5624 d2 d3, rich_4079 d1 d2, rich_4077 d2, rich_2725 d1 |
| T-e4b-009 | mechanics (how it finds code) | `trees/e4b-r005-filerank` | `prompts/system.md` section 2, first bullet: the search template `git grep -n "SPECIFIC_TOKEN" -- '*.py' \| head -20` becomes `git grep -ic "word" SOURCE_DIR \| sort -t: -k2 -nr \| head -15` (one lowercase word, case-insensitive, one line per file with its hit count, most hits first), followed by `git grep -n -i "word" CHOSEN_FILE` for line numbers (prompt 3,162 -> 3,410 bytes). | rich_3470 d1, rich_3067 d2, rich_3782 d2, rich_3944 d2, rich_3480 d3, fastapi_9753 d2, rich_4076 d1, fastapi_9425 d1 |

Neither repeats a ledger row or a queued tree. Both rewrite a line the base prompt already has; neither adds
a rule to another section. T-008 keeps the base search command and changes how many searches come before the
first read. T-009 keeps "search once" and changes the command. They can be composed later.

## Miss classes in the base draws

Recounted with my own script; same definitions as R-004 (no edit = empty patch; wrong file = no reference
source file touched; wrong region = right file, no hunk within 15 lines of a reference hunk; partial = some
reference hunks reached; wrong logic = all reached, tests fail).

| Draw | Resolved | Wrong file | Wrong region | Partial | Wrong logic | No edit |
|---|---|---|---|---|---|---|
| d1 | 4 | 18 | 9 | 10 | 5 | 10 |
| d2 | 7 | 14 | 8 | 9 | 10 | 8 |
| d3 | 7 | 11 | 11 | 8 | 6 | 13 |

This matches R-004's table except d2 wrong file (14 against 12): R-004 put 2 task-draws in a separate
"test or doc only" column, and my script counts them as wrong file. Spot-checked against R-004's text:
rich_4077 d1 (`console.py`, reference `file_proxy.py`), rich_3935 d2 (`padding.py`, reference `table.py`),
rich_3480 d1 (wrong file), fastapi_15280 d1 (wrong region), rich_3944 d3 (no edit). All five agree.

## What the agent does on the 43 wrong-file task-draws

"Search" means a `run_command` holding `grep`; counts are for calls before the first edit attempt.

| Count | d1 (18) | d2 (14) | d3 (11) | All (43) |
|---|---|---|---|---|
| No search at all (the file is picked from its name) | 3 | 3 | 2 | 8 |
| Exactly one search | 7 | 6 | 5 | 18 |
| No search that printed anything | 6 | 5 | 4 | 15 |
| Fewer than two searches that printed anything | 14 | 12 | 9 | 35 |
| Search commands | 27 | 21 | 15 | 63 |
| of them piped through `head` | 9 | 9 | 8 | 26 |
| of them empty | 7 | 6 | 4 | 17 |
| of them case-insensitive | 2 | 0 | 1 | 3 |
| Reference file named in any search output | 2 | 0 | 3 | 5 |
| Reference file read | 1 | 2 | 0 | 3 |
| Mean call number of the first edit attempt | 5.5 | 6.1 | 5.1 | 5.6 |

Read together: the reference file is never on the screen in 38 of 43. The agent runs 1.5 searches per task,
edits at call 5 or 6 of 28, and uses a median of 8 calls (38 of the 43 use 12 or fewer). The call budget is not the limit; the base
prompt says "Search once" and the model does about that.

Two things R-004 and `directions.md` (B1) say that the traces do not support:

- "The model edits the first grep hit": the edited file is the file of the first output line in 7 of the 27
  wrong-file task-draws that had search output. In 15 there was no output to follow.
- `head - 20` (a space after the dash) appears in 6, 6, 5 tasks per draw. It is not a failed search: `head`
  reads standard input first, so the whole grep output comes back with an error line. It is not worth an edit.

Over all 168 task-draws: 242 searches before the first edit, 54 with a multi-word phrase as the pattern;
30 piped through a well-formed `head -N`, and 19 of those 30 returned exactly N lines (the list was cut).

## Twelve wrong-file tasks, call by call

"Shown elsewhere" is a search command from some E4B session on the same task whose output did name the
reference file (run in brackets). It is what the traces record, not a simulated grep. "Why" is taken from the
order of calls and the model's own text where quoted.

| Task, draw | Issue text | Searches before the edit, and hits | File edited, and why | Reference file | Shown elsewhere by |
|---|---|---|---|---|---|
| rich_4077 d2 | "proxy isatty" | call 1 `git grep -n "isatty" -- ./rich`: `_null_file.py`, `console.py`, `progress.py` | `console.py`, edit at call 3; in d1 the model calls it "the central place where I/O behavior is checked" | `file_proxy.py` | no session; the word "proxy" was never searched, and the file has no `isatty` before the fix |
| rich_4079 d1 | "Inline table code" | calls 1-2 read `table.py`, `protocol.py` whole; call 3 `grep -r "class Table" rich/`: `table.py` and five `markdown.py` classes | `table.py`, chosen by name before the search | `markdown.py` | that same call 3 (base d1); the model did not open it |
| rich_4076 d2 | "preserve newlines" | call 1 `git grep -n "newline" rich/`, first line `pretty.py:156` | `pretty.py`, the first hit, edit at call 3 | `ansi.py` | no session |
| rich_3935 d1 d2 d3 | "fix for padding width" | none in any draw | `padding.py`, by name, edit at call 2 | `table.py` (5 hunks) | `grep -r "padding" rich/` (calls40 d2) |
| rich_3480 d1 | "fix infinite loop in append" | call 1 `git grep -n "infinite loop" -- rich`: one comment in `protocol.py` | `protocol.py`, the only hit, edit at call 3 | `text.py` | `git grep -n "def append" -- ./rich` (calls40 d3) |
| rich_3480 d3 | same | call 1 `git grep -n "append" ./rich \| head -10`: ten lines, first `_inspect.py:198` | `_inspect.py`, the first hit | `text.py` | as above |
| rich_3470 d1 | "Fix record and capture" | call 1 `git grep -n "record" -- '*.py' \| head -5`: `examples/`, `__main__.py`, two `_emoji_codes.py` lines | `_emoji_codes.py`, from the five lines shown | `console.py` | `git grep -i "record" -- rich` without `head` (base d2), which reached the right file |
| rich_3067 d2 | "Allow tilde in URL" | call 1 `"tilde"` empty; call 2 `git grep -n "URL" -- rich/`, first line `style.py:54` | `style.py`, the first hit | `highlighter.py` | `grep -r "url" rich/` in lower case (base d1, d3) |
| rich_3782 d2 | "Syntax padding" | call 1 `git grep -n "padding" rich/ \| head -10`: first `__main__.py`; call 7 `"Padding" \| head -5` | `columns.py`, after reading five files whole | `syntax.py` (7 hunks) | `git grep -n "padding" rich/syntax.py` (base d1) |
| rich_3472 d1 | "fix for missing field in dataclass" | call 1 fails (`--rich/`); call 2 `grep -r "from dataclasses import dataclass" .` lists 10 files, `pretty.py` fifth | `console.py`, read first and never left | `pretty.py` | `grep -r "dataclass" rich` (base d2) |
| fastapi_5624 d2 d3 | "Fix hierarchical security scope propagation" | one search, restricted by the model to the `security/` directory (`"security"`, `"scope"`) | `security/oauth2.py`, the first hit | `dependencies/utils.py` | `git grep -n "security" fastapi/` over the whole package (editfix d2, calls40 d3) |
| fastapi_9425 d1 | "Allow `None` as return type for bodiless responses" | call 1 phrase `'"None" return type'` empty; call 2 `git grep -n 'def' routing.py \| head -10` | `routing.py`, by guess | `dependencies/utils.py` | `git grep -n "return type" fastapi/ \| head -5` (editfix d1) |
| rich_2725 d1 | "fix table rendering order of box elements" | none; reads `table.py` twice from line 1, then `box.py` whole | `box.py`, by name | `table.py` | `git grep -n "row" rich/table.py` (calls40 d1) |
| fastapi_9753 d1 d2 d3 | "Allow using dependables with `functools.partial()`" | `"partial"` under `dependencies/`: empty in all three draws | `dependencies/utils.py`, read next in every draw | `dependencies/models.py` | no session; the word is absent before the fix |

Of the 22 distinct wrong-file tasks, some E4B session printed the reference file with a search in 14. In the
other 8 none did (fastapi_13920, fastapi_14487, fastapi_15661, fastapi_9753, rich_3105, rich_3944, rich_4076,
rich_4077): the issue is a bare title or a number, the fix adds a word the file does not yet hold, or the
reference is a new file. No search change reaches those, so the ceiling for both edits is the other 14 tasks, which
account for 11, 6 and 6 wrong-file task-draws in d1, d2, d3 (the 8 unreachable tasks account for 7, 8, 5).

The searches that did show the reference file share a form: one lower-case word, the whole package directory,
no `head`. The ones that missed are a phrase copied from the title (rich_4076 d1 "preserve newlines",
fastapi_9425 d1, rich_3535 d1 "single-width"), an upper-case word (rich_3067 d2), a directory the model
narrowed by name (fastapi_5624), or a list cut by `head` (rich_3470 d1, rich_3480 d3, rich_3782 d2).

## T-e4b-008: two searches before the first read

Pattern: one search or none, then a commitment. Counted over all 56 tasks per draw, before the first edit
attempt: no search on 15, 13, 15; exactly one on 21, 20, 22; fewer than two searches with output on 46, 40, 42.
Affected among wrong-file: 35 of 43 task-draws.

The change is to the number in a rule the model already follows ("Search once"), not a new rule elsewhere,
which is what distinguishes it from T-e4b-003. The two commands are given as a template because the base
templates are copied literally (R-004 found the `tests/test_file.py` template filled in on 22 commands).

Traces:

- rich_3935 d1, d2, d3: no search; call 1 reads `padding.py`, call 2 edits it, call 3 submits. Miss: wrong
  file (reference: 5 hunks in `table.py`). A search for "padding" lists `table.py` (calls40 d2).
- rich_4076 d2: call 1 `git grep -n "newline" rich/`, call 2 reads `pretty.py` 150-165, call 3 edits it.
  Miss: wrong file (reference `ansi.py`). No second word was tried.
- rich_3480 d1: call 1 finds one comment with "infinite loop" in `protocol.py`, call 3 edits it. Miss: wrong
  file (reference: 2 hunks in `text.py`). The second word of the title, "append", leads to `text.py`.
- fastapi_5624 d2: call 1 `git grep "security" fastapi/security`, call 2 reads `oauth2.py`, call 3 edits.
  d3 the same with "scope". Miss: wrong file (reference `dependencies/utils.py`).
- rich_4077 d2: call 1 "isatty", call 3 edits `console.py`. The other title word, "proxy", is in the
  reference file's name. Miss: wrong file.
- rich_4079 d1 and rich_2725 d1: the first calls are whole-file reads of a file picked by name.

Process endpoints (base values counted by me, all 56 tasks per draw, calls before the first edit attempt):

1. Tasks with fewer than two searches that printed something: base 46, 40, 42 (mean 42.7). Expected under 20.
   Above 35 means the instruction was not followed, and the result is a compliance reading.
2. Tasks where a reference source file is named in a search output: base 15, 22, 19 (mean 18.7). Expected 26
   or more.
3. Wrong-file task-draws by the script above: base 18, 14, 11 (mean 14.3). Expected 10 or fewer.
4. Guard: tasks with a compaction (R-004 count: 21, 29, 24) do not rise by more than 5 per draw; two more
   outputs of up to 20 lines are about 1,000 tokens against the 14,336-token trigger.

## T-e4b-009: rank files by hit count

Pattern: the search output the model sees is the first 5 to 20 matching lines in path order, or nothing.
It never sees the list of candidate files.

- 26 of the 63 wrong-file searches are piped through `head`; over all draws 19 of 30 well-formed `head -N`
  searches returned exactly N lines. Tasks with a cut list before the first edit: 5, 4, 7 per draw.
- 17 of the 63 are empty, most from a phrase or an upper-case word; 3 of 63 use `-i`.
- `git grep -c` or `grep -c` is used in no base session (0 logs of 168).

The new command prints one line per file, so 15 lines cover 15 files instead of 15 lines of the first file,
and `-i` with a single word removes the case and phrase misses. If the model writes `head - 15`, the sorted
list still comes back whole. The pipe has three stages where the base has two; that is the risk.

Documented, not seen on the cluster: `HARNESS_README.md` section 6.1 cuts command output at 5,000 characters;
a count list of a large package stays under it only because of the `head`.

Traces:

- rich_3470 d1: call 1 `git grep -n "record" -- '*.py' | head -5` returns five lines, none in `console.py`;
  calls 2-7 read and edit `_emoji_codes.py`. Miss: wrong file. In d2 the uncut `git grep -i "record" -- rich`
  shows `console.py` and the session edits it.
- rich_3067 d2: call 2 `git grep -n "URL" -- rich/` gives `style.py:54` first; edit at call 8 in `style.py`.
  Miss: wrong file (reference `highlighter.py`, which lower-case "url" shows in d1 and d3).
- rich_3782 d2: call 1 `git grep -n "padding" rich/ | head -10` shows `__main__.py` lines; five whole-file
  reads follow; edit at call 9 in `columns.py`. Miss: wrong file (reference: 7 hunks in `syntax.py`).
- rich_3944 d2: call 1 `grep -r "font" rich | head -n 20`, twenty docstring lines starting in `table.py`;
  five failed edits there, one edit in `panel.py`. Miss: wrong file (reference `cells.py`; no session found it,
  so this task shows the cut list, not a case the new command is known to fix).
- rich_3480 d3: call 1 `git grep -n "append" ./rich | head -10`, first line `_inspect.py:198`, edited at
  call 5. Miss: wrong file (reference `text.py`).
- fastapi_9753 d2: call 2 `git grep -n "Depends" fastapi/ | head -5` returns re-export lines of `__init__.py`.
  Miss: wrong file.
- rich_4076 d1 and fastapi_9425 d1: call 1 is a phrase from the title, empty; the file is then guessed.

Process endpoints (all 56 tasks per draw, before the first edit attempt):

1. Tasks whose first search is the count form (`grep` with `-c`): base 0, 0, 0. Expected 30 or more. Under 15
   means the template was not taken up; then the result is a compliance reading, not a verdict on the idea.
2. Searches that print nothing: base 18 of 71, 14 of 83, 24 of 88 (25%, 17%, 27%). Expected under 12%.
3. Tasks where a reference source file is named in a search output: base 15, 22, 19 (mean 18.7). Expected 28
   or more.
4. Wrong-file task-draws: base 18, 14, 11. Expected 10 or fewer.
5. Guard: tasks where the reference file is read before the first edit (base 34, 38, 39) do not fall. A fall
   would mean the count list is read as an answer and the line-level search is skipped.

## Not done

- No grep was simulated on the task snapshots. Whether the count list puts the reference file in its first
  15 lines is known only for the tasks where a session's own output shows it.
- Both trees were validated with `tools/validate_submission.py` in `env/harness.sif`: the same one error
  (packing gate, 18.00 h) and one warning as `trees/e4b-base`, nothing else.
- Only `prompts/system.md` differs from the base in each tree.

## Readings

Fixed by the operator 2026-11-18, before any run of either tree and before any R-003 or R-004 three-draw result was read.

- Three draws of each tree on cdev-56 at concurrency 4. Base pooled: 4, 7, 7 (mean 6.0).
- Kept: three-draw mean >= 9.0. Mean in [8.0, 9.0): positive, not kept, may be composed.
- T-e4b-008 endpoint: tasks with fewer than two searches with output before the first edit (46, 40, 42 in the base) under 20 per draw.
- T-e4b-009 endpoint: tasks using the count-form search at least once (0 in the base) on 30 or more per draw.
- Shared outcome endpoint: wrong-file tasks (18, 14, 11 in the base) at 9 or fewer per draw, counted the proposer's way. If the search endpoints move and wrong-file does not, the E4B's file choice is not a search problem; the direction closes.

## Results

(appended after the runs)


Amendment 2026-11-18T17:00Z, before any run: the six cdev-56 draws were cancelled; both trees run the L1 screen instead (`S-005-e4b-<tree>-s1/-s2` on screen-e4b-20, base `S-000-e4b-base-s1..3`). The cdev-56 readings above apply only if a tree is promoted, on cdev2-79 with a bar of base + 3. The process endpoints are read on the screen, scaled to 20 tasks.

### Screen results (2026-11-18, read by the rules above and the 17:00Z amendment)

Resolves on screen-e4b-20: base S-000-e4b-base-s1..s3 3, 3, 3 (mean 3.0); twosearch 5, 2 (3.5); filerank 1, 3 (2.0).
Process counts are per 20 tasks, before the first edit attempt. The bars are scaled from 56 tasks.
"Wrong file" is the trace_vs_reference.py class.

| Draw | <2 searches with output | count-form search used | reference file named in a search output | wrong file |
|---|---|---|---|---|
| base s1, s2, s3 | 18, 20, 11 | 0, 0, 0 | 9, 7, 7 | 5, 5, 7 |
| twosearch s1, s2 | 14, 16 (bar < 7.1) | 0, 0 | 6, 11 | 6, 7 |
| filerank s1, s2 | 12, 11 | 13, 9 (bar >= 10.7) | 11, 10 | 8, 7 (bar <= 3.2) |

Readings:
- T-e4b-008 is not promoted. Its +0.5 is at the promotion threshold, but its process endpoint is missed by a wide margin, so this is a compliance reading.
- T-e4b-009 is not promoted, at -1.0. The template was taken up (mean 11 per 20) and the reference file was named more often. Wrong-file did not fall.
- By the shared outcome rule, direction B1 closes: the search changed and the file choice did not.
- Counting script: a session scratch file, not kept. It uses `tools/trace_vs_reference.py`'s parser: a search is a `run_command` containing `grep` before the first edit call, and "with output" means non-empty stdout.
