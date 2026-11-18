# R-007 (e4b): thinking 2048; issue pinned in the instruction; paged reads; locator then editor

Written 2026-11-18 by the proposer (`proposer/PROPOSER.md` v1.4), before any R-007 run. Nothing here has been
run on a GPU. No R-005 or R-006 result was read (`runs/R-006-e4b-compose-d1` appeared while this was written
and is not used).

- Base: `trees/e4b-base`.
- Base draws read: `R-000-e4b-base-d1`, `-d2`, `-d3` on `cohorts/cdev-56.txt` (168 task-draws). Resolved 4, 7, 7.
- Also read: the other 20 finished E4B draws under `runs/R-00[1-4]-e4b-*` (23 draws in all, 1,287 task-draws;
  `R-004-e4b-syntaxcheck-d3` has 55 rows). They are used for within-task comparisons only, never as a base value.
- Traces read call by call: 50 sessions of 13 tasks (fastapi_13537, _14794, _14873, _15589, _5624, _9425,
  _9555, _9753, rich_3518, rich_3676, rich_3934, rich_3935, rich_4077: the base draws, plus resolving sessions
  of the same tasks from other trees), 38 of them failed. Everything else is counted by script from `traces/`
  and `task_results.jsonl`.
- Screen: `cohorts/screen-e4b-20.txt`. Base on those 20 ids in the three base draws: resolved 2, 5, 5.

## Proposals

| Tweak | Kind | Tree | Change (one sentence) | Evidence (task ids, draw) |
|---|---|---|---|---|
| T-e4b-011 | process (sampling budget) | `trees/e4b-r007-think2048` | `configs/sampling.yaml`: `thinking_budget` 4096 -> 2048. | fastapi_15589 d1, fastapi_13537 d1, fastapi_9555 d3, rich_3518 d2, fastapi_14794 d1 |
| T-e4b-012 | process (context: what the agent still has after compaction) | `trees/e4b-r007-pinissue` | `prompts/system.md` gets a last section that holds `{problem_description}`, so the issue text is in the instruction on every turn (prompt 3,162 -> 3,353 bytes plus the issue). | rich_3518 d1 and temp03-d2, fastapi_14794 d2 d3, fastapi_13537 d3, fastapi_15589 d3 |
| T-e4b-013 | mechanics (how it reads code) | `trees/e4b-r007-pagedread` | `prompts/system.md` section 2: the read bullet ("at most 120 lines") becomes "read_file returns at most 150 lines whatever you ask; ask for N to N+149; if the function is not complete at the returned end_line, read on from end_line+1 before editing" (3,162 -> 3,431 bytes). | fastapi_15589 d1 d2, rich_3518 d1 d2, fastapi_14794 d1 d2, fastapi_13537 d1 d2, fastapi_14873 d1, rich_3676 d1 d2, fastapi_9555 d1 |
| T-e4b-014 | mechanics (how it finds code) | `trees/e4b-r007-locator` | `agent.yaml` becomes a `SequentialAgent` of two agents on the same model: `locator` (run_command, read_file; ends with a five-line LOCATION message) and `editor` (the base agent, section 2 rewritten to start from that message). | rich_4077 d1 d2, fastapi_9753 d1 d2, fastapi_9425 d1, fastapi_9555 d1, rich_3676 d1, fastapi_5624 d2 d3, rich_3935 d1 d2 d3 |

None repeats a ledger row or a queued tree. T-011 is the E4B's first thinking-budget run (T-31b-003 was 1024 on
the 31B, for wall time; here the reason is what the long thoughts are followed by). T-013 does not touch the
search command (T-e4b-008, -009 are queued). T-013 and T-014 both aim at "the reference lines are not on screen
when the edit is made"; they differ in mechanism (a read rule against a structure) and can be composed.

## Miss classes (rule 6)

My script; definitions as in R-004 and R-005 (no edit = empty patch; wrong file = no reference source file
touched; wrong region = right file, no hunk near a reference hunk; partial = some reference hunks reached; wrong
logic = all reached, tests fail). "Near" here is 15 lines plus the hunk length, so partial and wrong logic differ
from R-005 by one task in places; wrong file, wrong region and no edit agree exactly.

| Draw | Resolved | Wrong file | Wrong region | Partial | Wrong logic | No edit |
|---|---|---|---|---|---|---|
| d1, cdev-56 | 4 | 18 | 9 | 9 | 6 | 10 |
| d2 | 7 | 14 | 8 | 9 | 10 | 8 |
| d3 | 7 | 11 | 11 | 7 | 7 | 13 |
| d1, screen-20 | 2 | 8 | 6 | 1 | 1 | 2 |
| d2 | 5 | 6 | 4 | 1 | 2 | 2 |
| d3 | 5 | 4 | 4 | 1 | 1 | 5 |

Wrong file is the largest class (43 of 150 failed task-draws). T-014 targets it. What else was tried for it and
dropped is under "Checked and not proposed".

## The 20 sometimes-resolved tasks: what differs first

143 resolving and 317 failing sessions of the same 20 tasks, over the 23 draws.

| Before the first edit attempt | Resolving (143) | Failing, same tasks (317) | 36 never-resolved tasks (827) |
|---|---|---|---|
| a read covers a reference hunk | 90% | 36% | 52% |
| the reference file is read | 94% | 70% | 64% |
| first edit is in a reference file | 93% | 67% | 60% |
| a search output names the reference file | 50% | 52% | 33% |
| tool calls before the first edit (mean) | 5.3 | 6.2 | 5.2 |
| completion tokens of the first-edit turn (mean) | 1,405 | 2,352 | 2,381 |
| failed `edit_file` calls in the session (mean) | 0.5 | 2.1 | 2.1 |
| compactions per session (mean) | 0.20 | 0.54 | 0.45 |

First point of divergence of the 317 failing sessions: first edit in a file the reference does not touch 97
(31%); right file, reference lines not read before the edit 105 (33%); reference lines read and the edit then
failed or was wrong 108 (34%); no edit attempt 7. On the 36 never-resolved tasks the middle group is 10%: the
tasks that can move are the ones where the right file is found and the right lines are missed.

Stratified by task (Mantel-Haenszel over the 20 tasks), odds of resolving:

| Split | Rates | Odds ratio | Tasks better / worse |
|---|---|---|---|
| reference hunk read before the first edit, against not | 129/243 (53%) against 14/210 (7%) | 45 | 16 / 1 |
| no compaction, against a compaction | 117/302 (39%) against 26/158 (16%) | 2.6 | 15 / 5 |
| first-edit thought at most 2,048 tokens (estimate, characters / 3.84), against more | 127/322 (39%) against 16/133 (12%) | 2.2 | 13 / 6 |
| first-edit thought at most 1,024, against more | 77/167 against 66/288 | 1.6 | 9 / 11 |
| first read of the edited file starts below line 1, against at line 1 | 54/152 against 63/221 | 0.8 | 7 / 7 |
| search output names the reference file | (table above) | about 1 | |

So the search output is not what separates a resolving session from a failing one on these tasks; having the
reference lines on screen is. `directions.md` B1 ("the reference file rarely appears in any search output") is
true of the wrong-file sessions but does not explain the movable tasks.

## T-e4b-013: paged reads

Pattern: `read_file` returns 150 lines at most (HARNESS_README 6.2; seen on the cluster in every draw). The
model asks for more, is not aware it got less, and edits from the page it has.

| Count, cdev-56 | d1 | d2 | d3 |
|---|---|---|---|
| `read_file` calls that returned content | 193 | 211 | 223 |
| cut at 150 lines (`is_truncated`) | 107 | 119 | 129 |
| of those, asked with no `end_line` / with an `end_line` past the cap | 42 / 65 | 65 / 54 | 63 / 66 |
| cut reads followed later by a read starting within 15 lines of the cut | 25 | 22 | 16 |
| reads that returned exactly the lines of an earlier read of the session | 31 | 28 | 23 |
| task-draws with a cut read not continued before the first edit | 29 | 37 | 41 |
| same, screen-20 | 9 | 12 | 14 |
| task-draws with a reference hunk read before the first edit | 25 | 29 | 28 |
| same, screen-20 | 5 | 7 | 7 |

Near misses: sessions classed wrong region or no edit that read the reference file and whose nearest read ended
1 to 150 lines above the reference hunk: 13 in the base draws (7, 5, 1), on 7 tasks (rich_3676, fastapi_15589,
fastapi_14873, rich_3934, rich_3518, fastapi_14794, fastapi_13537); 119 over the 23 draws on 21 tasks. The hunk
is below the read in 109 of the 119 and above it in 10; in 61 the read was a full 150-line page.
First `edit_file` call of a session fails in 17% (9/53) when every line the model asked for was returned and in
38% (41/107) when it had asked for lines it did not get (base draws; 23% against 30% over all draws).

Traces (failed patch against the reference):

- fastapi_15589 d1: call 2 asks 530-810, gets 530-679; call 3 edits line 534. Reference: one hunk at 826.
  Wrong region. d2: call 2 reads 790-807, edit at 800; the hunk starts 19 lines lower. Wrong region. The
  resolving session (calls40 d1) read 780-830, then 780-929, then edited at 828.
- rich_3518 d1: calls 3, 5, 6 ask 1-500, 150-400, 300-600 and get 1-150, 150-299, 300-449; edit at 248.
  Reference: one hunk at 451, two lines past the last line seen. Wrong region. d2: reads end at 450; four
  edits fail; empty patch. The resolving session (temp03 d3) read 350-499.
- fastapi_14794 d2: calls 2, 3, 4, 6, 8 ask 1-None, 1-500, 1-1000, 1-200, 1-2000 and get lines 1-150 five
  times (about 8,000 prompt tokens); it resolved only after a grep gave line 400. d1: reads 350-380, six
  failed edits, edit at 368; reference hunks at 449 and 460. Wrong region.
- fastapi_13537 d1: reads 700-800, edits 785; reference at 902. d2: asks 700-900, gets 700-849; four failed
  edits, then a `write_file` that replaces the 1,024-line file with 9,007 characters. Wrong region; wrong logic.
- fastapi_14873 d1: call 6 asks 800-1100 and gets 800-949; the reference hunk starts at 952. Calls 13, 16,
  18, 23 ask for 800-1000, 800-1050, 800-1100, 800-1000 and get 800-949 each time; calls 3, 7, 8 get 1-150
  three times. 20 of its 28 calls are reads, two edits fail at the call cap, empty patch.
- rich_3676 d1: call 2 reads 1-None (1-150 of 797), call 3 edits lines 100-120; reference hunks at 191 to 594.
  d2: asks 1-797, gets 1-150. Wrong region both.
- fastapi_9555 d1: calls 3, 5, 6 ask 1-None, 1-300, 1-500 and get 1-150 three times.

Why a prompt line here, given the lesson that added rules did not move the E4B: this replaces a number the
model is already told (120) with the tool's real behaviour and a call template; R-004 found the model copies
templates literally. It may still be ignored; endpoint 1 says so.

Screen tasks it should flip: fastapi_15589 (resolved 2/5 when the hunk was read, 0/18 when not; 8 near-miss
sessions), rich_3518 (2/4 against 0/19; 12 near misses, most by 1 or 2 lines), fastapi_14794 (6/12 against
0/11; 8), fastapi_13537 (1/2 against 0/21; 15). If every near miss became a hunk read at those rates the screen
gains about 0.9 tasks per draw; that is under the 1.5 bar, so this edit needs its endpoint to pass at 0.5.
rich_3676 (12 near misses, never resolved, 8 hunks) is not expected to flip.

Process endpoints (base values above):

1. Compliance: cut reads continued from the cut: base 25/107, 22/119, 16/129 (18%). Expected over 50%. Under
   30% means the line was not followed.
2. Reads returning exactly the lines of an earlier read: base 31, 28, 23 on cdev-56; 8, 10, 8 on the screen.
   Expected under half.
3. Task-draws with a reference hunk read before the first edit: base 25, 29, 28 of 56; 5, 7, 7 of 20 on the
   screen. Expected 9 or more of 20.
4. Guard: task-draws with a compaction (21, 29, 24; screen 4, 9, 8) do not rise by more than 3 on the screen.

## T-e4b-014: locator, then editor

Pattern: the edit is made without the lines that need changing on screen, and in the largest class without the
file. Task-draws with an edit attempt: 53, 54, 54. First edit attempt made before any read covers a reference
hunk: 28, 25, 26 (screen 13, 12, 12). First edit in a file the reference does not touch: 20, 20, 18 (screen
8, 7, 6). In the 43 wrong-file task-draws the reference file was read before the edit in 3.

The model can pick the right file: for 14 of the 22 wrong-file tasks some session did (R-005), and the first-edit
file varies from draw to draw (fastapi_9753: routing.py 9, models.py 8, utils.py 6 of 23; rich_3067: style.py
11, highlighter.py 8; rich_3782: padding.py 10, syntax.py 8). The base prompt asks for the choice and the edit
in one run ("edit by call 12", "finish as soon as the edit is in"). The edit gives the choice to an agent that
cannot edit and must end by writing file, function, line range and one sentence of reason; the editor then
starts by reading that range.

Traces:

- rich_4077 d1, d2: call 1 greps "isatty", call 2 reads `console.py` 960-980, call 3 edits it. Reference:
  `file_proxy.py` (57 lines), never opened. Wrong file. d3 (resolved): the same grep, then call 2 reads
  `file_proxy.py` whole, call 3 edits it.
- fastapi_9753 d1: call 1 grep "partial" empty, call 2 reads `dependencies/utils.py` 1-150, calls 4, 5 edit it.
  Reference: `dependencies/models.py` (113 lines), never opened. Wrong file. Resolving sessions (calls40 d2,
  sweep d1) list the directory and read `models.py` whole before editing.
- fastapi_9425 d1: call 3 reads `routing.py` 1-100, call 4 edits line 89. Reference: `dependencies/utils.py`
  254. Wrong file. d3 (resolved) reads both files, greps the function, reads 250-290, edits 263.
- fastapi_9555 d1: five reads of `dependencies/utils.py`, edit at 630 in the function the issue names. Wrong
  file by the reference (`models.py`). Resolving sessions edit `utils.py` near line 236 (base d2, calls40 d1)
  or `models.py` (calls40 d3), so this task has more than one passing location.
- fastapi_5624 d2, d3: one search inside `security/`, edit at call 3 (d2) and call 4 (d3) in
  `security/oauth2.py`; reference `dependencies/utils.py`. rich_3935 d1, d2, d3: read `padding.py`, edit, submit in three calls; reference
  `table.py`. Wrong file.
- rich_3676 d1: grep, one read of lines 1-150, edit at call 3 inside that page. Wrong region.

What is not known and must be smoke-tested on one task before the screen (documented in HARNESS_README 2.3 and
5.2, none of it seen on the cluster):

- that a `SequentialAgent` root compiles and runs here, and that `!include ../prompts/x.md` from
  `sub_agents/` resolves (the sample submission does this);
- that the editor sees the locator's last message (ADK passes other agents' events as context when
  `include_contents` is the default; no state templating is used, so a locator that never answers cannot
  raise a missing-key error);
- that the 28-call budget is shared (the prompts say so) and what a locator that never stops costs;
- the continuation nudge re-runs the whole sequence, locator included, when the editor ends without
  `submit_patch`;
- trace authors become `locator` and `editor`; any tool that filters on `swe_agent` needs a look.

Rule 5 note: the root no longer has a `tools` list. The tools declared across the tree are the same six, the
model line is the same on both agents, `max_time_minutes` is unchanged. The validator gives the base's
packing-gate error, the base's warning, and one more warning ("sub-agent with submit_patch can end the session
from inside a sub-call"), which is the intended behaviour. If the operator reads rule 5 as forbidding this,
drop the tree.

Screen tasks it should flip: the same four as T-013 (the editor must read the located range first), plus
rich_4077 (1/1 when the hunk was read, 0/22 when not), fastapi_9425 (13/16 against 2/7) and fastapi_9555. The
never-resolved wrong-file screen tasks (fastapi_13920, fastapi_15661, rich_3105, rich_4079, fastapi_5624) have
no concrete reason to start resolving: their issue text is a title or a number, and no session of any tree has
read the reference lines of fastapi_15661, rich_3105 or rich_4079.

Process endpoints:

1. Compliance: sessions in which `locator` ends with a LOCATION message naming an existing file: base not
   applicable. Expected 16 or more of 20. Under 10 is a compliance reading, not a verdict on the idea.
2. First edit in a reference file: base 33, 34, 36 of 56; 10, 12, 13 of 20 on the screen. Expected 15 or more.
3. Reference hunk read before the first edit: base 5, 7, 7 of 20. Expected 10 or more.
4. Guards: empty patches (screen 2, 2, 5) not above 5; sessions with 28 or more tool calls (base 1, 0, 0 on
   cdev-56 and 0, 0, 0 on the screen, from `task_results.jsonl`; `summary.jsonl` exists for d1 and d2 only and
   agrees: 1, 0) not above 2 of 20.

## T-e4b-011: thinking budget 2048

Pattern: the long thought comes at the first edit, and what follows it rarely resolves. The budget is enforced
here: thought text tops out near 15,600 to 16,000 characters (about 4,096 tokens) and 30 base task-draws have a
turn of 3,900 completion tokens or more.

| First-edit turn, thought size (estimate) | Sessions, 23 draws | Resolved |
|---|---|---|
| over 1,024 tokens | 862 of 1,274 (68%) | 66 (7.7%) |
| over 2,048 | 459 (36%) | 16 (3.5%) |
| over 3,000 | 216 (17%) | 6 (2.8%) |
| over 3,900 (at the cap) | 95 (7%) | 1 (1.1%) |

Base draws: first-edit thought over 2,048 tokens on 25, 25, 25 task-draws (screen 8, 8, 7); turns of 3,000
completion tokens or more: 22, 18, 17 (screen 6, 5, 4). Within task the split at 2,048 has odds ratio 2.2
(13 tasks better short, 6 worse); at 1,024 it has none (9 against 11), and 50% of resolving first edits think
more than 1,024 tokens, so 1,024 would cut into the sessions that work. A larger budget has no support: turns
at the cap resolve 1 in 95. Longer thoughts also go with larger patches (on the 32 tasks whose reference adds
8 lines or fewer, a first-edit turn of 3,000 completion tokens or more gives a patch more than 2 lines over
the reference size 27% of the time, against 10% under 1,500).

Traces:

- fastapi_15589 d1: call 3, thought 15,605 characters, edit at the first grep hit (line 534). Wrong region.
- fastapi_13537 d1: turn 3, thought 15,172 + 2,768 characters, edit at 785. Wrong region.
- fastapi_9555 d3: turn 4, thought 15,957 + 6,824 characters, then `submit_patch` with no edit. No edit.
  calls40 d2: thought 15,853, edit at 630. Wrong file.
- rich_3518 d2: call 8, thought 10,482 characters, `edit_file` sent without `old_string`; four more failed
  edits. No edit.
- fastapi_14794 d1: call 4, thought 12,136 characters, `old_string` not found; five more failures. Wrong region.

Honest size: this is an association. The cap removes the tail; whether the shorter turn then lands a better
edit is what the run tests. Screen tasks it should flip: fastapi_9555 (5/11 with a short first-edit thought,
2/10 long), rich_3518 (2/12, 0/11), rich_4077 (1/16, 0/7), rich_3470 (1/14, 0/9). It may cost fastapi_14794
(2/11 short, 4/12 long) and fastapi_13537 (its one resolve had a long thought). Expected screen gain is under
1 task per draw.

Process endpoints:

1. Compliance: turns of 3,000 completion tokens or more: base 22, 18, 17 on cdev-56; 6, 5, 4 on the screen.
   Expected at most 1 per screen draw (2,048 thinking plus an edit of p90 375 tokens).
2. First `edit_file` call of the session fails: base 14, 28, 21 of 56; 3, 11, 10 of 20. Expected 5 or fewer
   of 20.
3. Task-draws with a compaction: base 21, 29, 24; screen 4, 9, 8. Expected 5 or fewer of 20 (thoughts stay in
   the history).
4. Guard: empty patches on the screen (2, 2, 5) not above 5.

## T-e4b-012: the issue pinned in the instruction

Pattern: the harness compacts the history at 14,336 prompt tokens (HARNESS_README 7.2: the last 5 events are
kept, the rest are summarised). The issue text is the first event. After a compaction the model works from a
summary of it; the system prompt is the only text that is never summarised. HARNESS_README 5.1 says
`{problem_description}` in an instruction is filled from session state. Documented, not seen on the cluster.

| Count, cdev-56 | d1 | d2 | d3 |
|---|---|---|---|
| task-draws with a compaction (prompt-token drop of over 40% from above 8,000) | 21 | 29 | 24 |
| same, screen-20 | 4 | 9 | 8 |
| resolved among them | 1 | 4 | 0 |
| first edit attempt made after a compaction | 2 | 4 | 5 |
| tool calls made after the first compaction | 104 | 155 | 142 |
| of those, a call already made before it with the same arguments | 8 | 11 | 12 |

(`summary.jsonl` gives 23 and 31 compaction tasks for d1 and d2 and has no d3 file; the counts above are mine,
by the PROPOSER.md definition.) Within task, sessions without a compaction resolve at 39% against 16% (odds
ratio 2.6, 15 tasks against 5); sessions whose first edit comes after a compaction resolve 7 of 43.

Traces:

- rich_3518 d1: `pytest tests/` at call 6 takes the prompt to 15,034 tokens; it drops to 8,358 for the last
  turn. temp03 d2: drop 17,833 -> 8,124 after call 12; calls 13 to 24 hold eight failed edits on the signature
  it had already changed, and two empty submits. No edit.
- fastapi_14794 d3: drop 15,294 -> 5,598 before the submit. d2: drop 14,852 -> 5,950 between two edits.
- fastapi_13537 d3: drop 15,288 -> 5,999 after call 18 with no edit yet; the edit at call 25 goes into
  `request_params_to_args`, a function the issue does not name. Wrong region.
- fastapi_15589 d3: drop 15,058 -> 7,737 between two identical failed edits; three empty submits. No edit.

What I could not check: the traces do not show the compacted prompt, so whether the issue is lost, kept, or
well summarised is not known. The post-compaction prompt is a median 2.1 times the first prompt (n = 74), which
does not settle it. This is the weakest of the four on evidence; it is cheap, and one smoke task with a forced
compaction would show whether the post-compaction thoughts still quote the issue.

Cost: the issue text is in the prompt twice until the first compaction (typically a few hundred tokens), so
compaction can arrive one call earlier.

Screen tasks it should flip: those whose failing sessions compact and whose resolving sessions do not:
rich_3518 (0/11 with a compaction, 2/12 without), fastapi_9555 (1/8, 6/15), fastapi_14794 (2/8, 4/15),
fastapi_15589 (1/6, 1/17). Expected gain is under 1 task per draw.

Process endpoints:

1. Resolved among screen task-draws with a compaction: base 1, 3, 0 of 4, 9, 8 (all trees, screen tasks:
   13 of 125, 10%). Expected 25% or more of the compacted task-draws, pooled over the two draws.
2. Calls after the first compaction that repeat an earlier call with the same arguments: base 8 of 104, 11 of
   155, 12 of 142 (8%). Expected under 4%.
3. Guard: task-draws with a compaction on the screen (4, 9, 8) do not rise above 10.

## Checked and not proposed

| Idea | What the traces say |
|---|---|
| Code graph or embeddings | The harness has three graph tools (`search_similar_code`, `get_code_neighbors`, `get_code_subgraph`, HARNESS_README 6.3) and `data/raw/graphs`, `data/raw/embeddings` are on the cluster. They are only reachable by adding them to `tools`, which PROPOSER.md rule 5 forbids. `search_similar_code` has a word-overlap fallback for a multi-word query, which is the one mechanism here that could reach the 8 wrong-file tasks no search has ever reached. Not written; the operator decides on rule 5. |
| `agent_tool` locator (README section 10, item 4) | Adds a tool to the list; rule 5. T-014 uses `sub_agents` instead. |
| Skills | `skills:` adds the skill tools (`load_skill`, `run_skill_script`) to the agent, so it also changes the tool list; the E4B would have to choose to load a skill. `.py` skill scripts are an allowed file type and could carry a real locator; not explored. |
| Thinking 0, 1024, 8192 | 1024: no within-task effect (above). 8192: turns at the cap resolve 1 in 95, and `max_output_tokens` would have to rise with it. 0: first-edit turns under 500 completion tokens resolve 14 of 53, the same rate as 500 to 1,499; not chosen because 2,048 has the within-task support and one budget value per round. |
| `max_output_tokens` | 7 of 15,121 model calls reach 8,000 completion tokens. Not a limit. |
| `top_p`, `top_k` | No trace pattern points at them; temperature 0.3 was a null (T-e4b-004). |
| Start the read at the search hit, not at line 1 | In 35, 40, 40 task-draws the first read of the edited file (over 150 lines) starts at line 1; but within task it makes no difference (odds ratio 0.8, 7 tasks against 7). |
| Re-read after a failed edit; recover from an empty submit | The edit after a re-read succeeds 24% of the time, an immediate retry 18%. T-e4b-003 raised the re-read rate from 18% to 26% and scored lower. 28 of the 31 base empty patches were submitted, 3 tried an edit afterwards; on the screen that is 1, 1, 5 task-draws. |
| Smaller edits | On tasks whose reference adds 8 lines or fewer, patches more than 8 lines over it are 2, 3, 2 per draw (0 of 29 resolved over all draws). Under 5 tasks. |
| Escaped newlines in `old_string` | 23 of 279 failed edits with an `old_string` in the base draws. 55 more failed edits arrive with no `old_string` at all (the tool-call text breaks on quotes inside `new_string`). Neither has a one-line fix. |
| File name from an issue word; small sibling file | 3 tasks (rich_4077, rich_3782, rich_2725) and 4 tasks (fastapi_9555, _9753, _14419, _14448). Under 5. |

## Not done

- No grep or read was simulated on a task snapshot.
- All four trees were validated with `tools/validate_submission.py` in `env/harness.sif`: the base's one error
  (packing gate, 18.00 h) and one warning in each; `e4b-r007-locator` has the one extra warning named above.
- `e4b-r007-locator` and `e4b-r007-pinissue` use harness behaviour that no cluster run has exercised
  (`SequentialAgent`, instruction templating). One smoke task each before the screen.
- Thought sizes are estimated from characters (3.84 characters per token, the median of thought plus arguments
  over completion tokens); the traces give completion tokens per turn, not thinking tokens.

## Readings

Fixed by the operator 2026-11-18T17:35Z, before any run of the four trees and before the base screen draws were read.

- Smoke first for the two trees that change structure: `S-007-e4b-locator-smoke` and `S-007-e4b-pinissue-smoke`, two tasks each. A tree whose smoke run errors or makes no tool call is fixed once by the operator (recorded here) or dropped.
- L1 screen: two draws of each tree on `cohorts/screen-e4b-20.txt`, concurrency 4 (`S-007-e4b-<slug>-s1/-s2`), against `S-000-e4b-base-s1..3`.
- Promoted to cdev2-79 (three draws) if the two-draw mean beats the base mean by 1.5 or more, or by 0.5 or more with the edit's process endpoint met (the proposer's, scaled to 20 tasks). Dropped otherwise.
- Because one E4B draw on 20 tasks is noisy, a promoted tree gets a third screen draw alongside its first full draw; a tree whose third draw brings its mean back under base + 0.5 is stopped.
- If two or more are promoted, their composition is screened next.

## Results

(appended after the runs)

### Screen results (2026-11-18, read by the rules above)

Resolves on screen-e4b-20 (base S-000-e4b-base-s1..s3: 3, 3, 3, mean 3.0; bars 4.5 outright, 3.5 with endpoint):

| Tree | s1, s2 | Mean | vs base | Reading |
|---|---|---|---|---|
| T-e4b-013 pagedread | 6, 3 | 4.5 | +1.5 | promoted (outright bar); compaction guard holds |
| T-e4b-011 think2048 | 4, 3 | 3.5 | +0.5 | dropped: endpoints missed |
| T-e4b-014 locator | 3, 4 | 3.5 | +0.5 | dropped: compliance met, effect endpoints missed |
| T-e4b-012 pinissue | 3, 2 | 2.5 | -0.5 | dropped |

Process counts per draw, from the traces by one script for base and trees alike (session scratch, not kept). It does
not reproduce the proposer's base numbers exactly (its definitions were not kept). So each reading is given both
against the proposer's absolute bar and against the base as counted here.

| Draw | turns >= 3000 tokens | first edit_file fails | compacted | resolved among compacted | empty patch | first edit in a reference file | reference hunk read before first edit | locator LOCATION | calls >= 28 |
|---|---|---|---|---|---|---|---|---|---|
| base s1, s2, s3 | 2, 6, 5 | 6, 6, 5 | 9, 5, 10 | 1, 1, 2 | 5, 2, 2 | 12, 15, 13 | 6, 10, 7 | - | 0, 0, 0 |
| think2048 | 1, 3 | 7, 8 | 9, 11 | 1, 0 | 1, 1 | 13, 11 | 7, 6 | - | 0, 0 |
| pinissue | 5, 5 | 5, 3 | 6, 9 | 0, 1 | 4, 2 | 11, 12 | 6, 5 | - | 0, 0 |
| pagedread | 4, 6 | 3, 8 | 9, 9 | 0, 1 | 1, 1 | 14, 11 | 10, 6 | - | 0, 0 |
| locator | 6, 5 | 4, 8 | 6, 4 | 0, 0 | 2, 2 | 14, 11 | 9, 9 | 19, 20 | 0, 1 |

- think2048: missed every endpoint on both counts. Long turns 1 and 3 (bar at most 1 per draw). First-edit failures 7 and 8 (bar 5 or fewer). Compacted 9 and 11 (bar 5 or fewer). Not promoted.
- locator: compliance met (19 and 20 sessions end with a LOCATION message, against a bar of 16). The effect endpoints were missed. First edit in a reference file 14 and 11 (bar 15). Reference hunk read before the edit 9 and 9 (bar 10); that is above this script's base mean of 7.7 but under the bar. Guards hold. Not promoted.
  - Like B1 (R-005), the E4B followed the new search or locate step, and its file choice did not change.
- pinissue: -0.5. Resolved among compacted task-draws 1 of 15 (7%), against a bar of 25% or more. Not promoted.
- pagedread: promoted on the outright bar, +1.5. The compaction guard (no rise of more than 3) holds at 9 and 9 against 5 to 10. On its own endpoint 3, reference hunk read before the first edit, it scored 10 and 6 (bar 9), so the mechanism is unclear.
  - The two draws are 6 and 3, so the third-screen-draw rule applies. Next are `S-007-e4b-pagedread-s3` and the first full draw. If s3 brings the three-draw mean under 3.5 (that is, s3 resolves 1 or fewer), the tree is stopped.
- Full level (README L2, rule by README Setup 7): cdev2-79 = cdev-56 + cdevx-23, with `HENG_SHIMS=1`. The base's cdev-56 part is R-000-e4b-base-d1..d3 (6.0 per draw). Its cdevx-23 part does not exist yet, so the base is run there three times: `R-000-e4b-base-x1..x3`. The candidate runs on cdev2-79 (`R-007-e4b-pagedread-d1..d3`). Bar: the pooled-base mean plus 3.
- Only one tree is promoted, so there is no composition screen.

### pagedread follow-up (2026-11-18T23:50Z)

- The third screen draw, S-007-e4b-pagedread-s3, resolved 4 of 20. The three-draw mean is 4.33, against a stop line of 3.5, so the tree continues.
- The first full draw, R-007-e4b-pagedread-d1, resolved 8 of 79 (one row has an error: no submit_patch). The job ended with a cgroup oom-kill event after all 79 rows were written. The same event is in most earlier job logs, at teardown.
- The cdevx-23 base draws R-000-e4b-base-x1..x3 already existed (started 18:26Z), so the re-queued jobs exited on "already holds a run" and nothing was rerun. They resolved 2, 1 and 1.
- The pooled base on cdev2-79 is 6.0 (cdev-56 d1..d3) + 1.33 (cdevx-23 x1..x3) = 7.33 per draw. The L2 bar is 10.33.
- d1's 8 is under the bar. d2 and d3 are queued, and the reading waits for all three.
