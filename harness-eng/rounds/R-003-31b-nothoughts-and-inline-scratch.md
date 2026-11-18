# R-003 (31b): thoughts out of the history; inline scratch checks

Written 2026-11-18 by the proposer (PROPOSER.md v1), before any run of either tree. No GPU used.

- Base tree: `trees/31b-base` (28 calls, 8 min, thinking 4096, T=1.0).
- Draws read: `runs/R-000-31b-base-d1` (22/56) and `runs/R-000-31b-base-d2` (22/56), cohort `cohorts/cdev-56.txt`.
- Read for each: `task_results.jsonl`, `summary.jsonl`, `aggregates.json`, and `traces/trace_<id>.json` for all 56 tasks
  (per-call tool, arguments, observation, `elapsed_s`, `prompt_tokens`, `completion_tokens`). Reference patches from
  `data/raw/tasks.jsonl`.
- Not duplicated: `max_tool_calls` 40 (T-31b-001, not kept), `thinking_budget` 1024 (T-31b-003, running), the
  sibling-site sweep section (T-31b-002, queued).

## Proposals

| Tweak | Kind | Tree | Change (one sentence) | Evidence (task ids, draw, what the trace shows) |
|---|---|---|---|---|
| T-31b-004 | process (context budget) | `trees/31b-r003-nothoughts` | `configs/sampling.yaml`: `include_thoughts: true -> false`, so each turn still thinks but its thoughts are not kept in the message history. | Compaction fires before the first successful edit on 25 (d1) and 18 (d2) tasks; those resolve 4 and 3. The model's own completion tokens are 42% (d1) and 50% (d2) of the prompt growth up to the first compaction. `rich_3470` d1: compaction before call 23 (prompt 14,404 -> 2,863 tokens, 53 s); calls 23-28 re-read `rich/console.py` lines 1-100 and re-grep `_write_buffer`, both already seen before call 22; the thought at call 30 says "20 calls were ALREADY used before I started"; first `edit_file` is call 29, rejected `BudgetExceeded`. `fastapi_15280` d1: compaction before call 21 (15,095 -> 4,169, 54 s); calls 21-26 are six reads and greps of regions first opened at calls 1, 2 and 10; first edit at call 27, no check. `rich_3061` d1: compaction before call 21 (34 s); calls 21-28 re-read `rich/style.py` and `rich/text.py`; first edit is call 30, rejected. `rich_3468` d1: compaction before call 20 (44 s); calls 20-23 re-read `rich/console.py` 2010-2075; first edit at call 24. `rich_4075` d2: compaction before call 27 (78 s); calls 27-28 re-read `rich/console.py` 1-50; first edit is call 29, rejected. |
| T-31b-005 | mechanics (how it checks) | `trees/31b-r003-inline-scratch` | `prompts/system.md` section 3: the line "Any scratch script goes in `/tmp` through `run_command`" is replaced by one that says `write_file` rejects `/tmp` paths and gives the inline form (`python -c` or `python - <<'EOF'`). | `write_file` to a `/tmp` path is rejected with `FileWriteError: Path traversal detected` on 19 tasks (21 calls) in d1 and 20 tasks (21 calls) in d2; the rejected call counts against the 28. `rich_3470` d1: call 8 `write_file /tmp/reproduce...` rejected; the first edit is call 29, one past the cap. `rich_4075` d2: call 25 `write_file /tmp/repro.py` rejected after an 83 s turn; the first edit is call 29, rejected. `rich_3506` d1: call 6, a 280 s turn (1,779 completion tokens) writing `/tmp/test_split.py`, rejected; the task ends at the time cap after 11 calls with no edit. `rich_3480` d1: call 12 rejected (67 s turn); time cap, no edit. `rich_3935` d1: call 23 rejected (35 s); the submitted patch holds only `reproduce_padding.py`, a scratch file in the repository. |

## Failed patch against reference patch, for the cited tasks

| Task (draw) | Reference patch | Our patch | Kind of miss |
|---|---|---|---|
| `rich_3470` (d1) | 1 hunk, `rich/console.py` `_write_buffer` | empty | no edit (the function was open at call 25; the edit came at call 29) |
| `rich_3061` (d1) | 13 hunks, `rich/text.py` | empty | no edit (attempt on `expand_tabs` in the right file at call 30) |
| `rich_4075` (d2) | 4 hunks, `rich/console.py` | empty | no edit |
| `fastapi_15280` (d1) | `fastapi/applications.py` 2 hunks, plus a new example file | 1 hunk each in `fastapi/applications.py` and `fastapi/routing.py`, made at calls 27-28, never run | wrong logic in the right file |
| `rich_3468` (d1) | 4 hunks in `rich/console.py` (`render_lines`, `render_str`, `log`, `_check_buffer`) | 3 hunks, all near `_check_buffer` (2027-2069) | partial |
| `rich_3506` (d1) | 1 hunk, `rich/segment.py` near `_split_cells` | empty | no edit (the region was read at call 2) |
| `rich_3480` (d1) | 2 one-line hunks, `rich/text.py` | empty | no edit |
| `rich_3935` (d1) | 5 hunks, `rich/table.py` | `reproduce_padding.py` only | wrong file (agent worked in `rich/padding.py`), scratch file in the diff |

## Pattern counts (of 56 tasks per draw)

Compaction is detected as a model call whose `prompt_tokens` is more than 3,000 below the previous model call's.
A successful edit is an `edit_file` or `write_file` to a repository source path with status ok, or a `sed -i`.

| Pattern | d1 | d2 |
|---|---|---|
| Tasks with at least one compaction (this detector) | 37 | 33 |
| Compactions in total (`aggregates.json` `compactions_total`) | 45 | 39 |
| Tasks whose first compaction comes before the first successful edit (or that never edit) | 25, of which 4 resolved | 18, of which 3 resolved |
| Tasks with no compaction | 19, of which 12 resolved | 23, of which 13 resolved |
| Tasks whose first compaction is at call 14 or earlier | 16 | 16 |
| Seconds spent in the turn that contains a compaction, summed | 1,768 | 1,614 |
| Reads and greps after the first compaction that repeat a file or command used before it | 82 | 56 |
| Share of prompt growth before the first compaction that is the model's completion tokens | 0.42 (median 0.44) | 0.50 (median 0.52) |
| Tasks with no successful edit whose only edit attempt is rejected at the call cap | 4 (`rich_3061`, `rich_3470`, `rich_3472`, `rich_3935`) | 4 (`fastapi_15280`, `rich_3105`, `rich_3472`, `rich_4075`) |
| Empty patches (`summary.jsonl` `patch_empty`) | 11 | 12 |
| Tasks with a `write_file` rejected for a `/tmp` path | 19 (11 resolved) | 20 (12 resolved) |
| Such calls; seconds of model time on them; seconds on the retry that follows | 21; 759; 223 | 21; 816; 258 |

Other patterns seen and not chosen this round:

- `edit_file` rejected with "mandatory input parameters are not present: old_string" (the call carries `new_string`
  ending in `` `,old_string: ``): 33 calls on 7 tasks (d1), 98 calls on 15 tasks (d2); three or more in a row on 3 and
  8 tasks, repeated with identical arguments (`fastapi_14301` d2 14 times, `rich_3782` d1 10 times, `rich_4070` d2 23
  times). These do not count as tool calls but cost 137 to 275 s on the worst tasks. The E4B edit-rule tweak
  (T-e4b-003) was not kept, so this needs a different form before it is tried on the 31B.
- The harness sends `budget_warning` from call 18 on ("Only 10 tool call(s) remaining ... Finalize your edits"). The
  agent keeps reading through it: `rich_3472` d1 quotes the "edit by call 12" rule after its 28th call and then calls `read_file` (rejected).

## Why these two respect the lessons

- T-31b-004 adds no work and no prompt text. It removes prompt tokens from every model call and should remove
  compaction calls (30 to 80 s each) and the re-reading after them. It differs from `thinking_budget` 1024: that
  shortens what each turn generates; this leaves the turn alone and changes what later turns are sent.
- T-31b-005 replaces a line that sends the agent to a path the tool rejects; it adds no rule and no step.

## Process endpoints (base values counted above)

| Tweak | Endpoint | Base d1, d2 | Expected if the edit works |
|---|---|---|---|
| T-31b-004 | tasks whose first compaction comes before the first successful edit | 25, 18 | 10 or fewer |
| T-31b-004 | `compactions_total` | 45, 39 | 22 or fewer |
| T-31b-004 | tasks with no successful edit whose edit attempt is rejected at the call cap | 4, 4 | 2 or fewer |
| T-31b-004 | guard: tasks at the 8-minute cap (`summary.jsonl` `time_cap_hit`; the lessons file counts 16, 14) | 17, 14 | not higher |
| T-31b-005 | tasks with a `write_file` rejected for a `/tmp` path | 19, 20 | under 5 |
| T-31b-005 | calls so rejected | 21, 21 | under 5 |
| T-31b-005 | guard: tasks with a scratch file in the patch (`scratch_in_patch`) | 2, 1 | not higher |

## Checks for the operator before reading T-31b-004

- Thinking must still be on. `data/raw/HARNESS_README.md` section 2 (generation config table) says
  `include_thoughts: false` with a positive `thinking_budget` keeps `enable_thinking: true` and strips the thought
  parts from the response and the outgoing history. If completion tokens per turn collapse on the first tasks
  (base output tokens per task: 7,195 in d1, 7,377 in d2), thinking was switched off and the run tests something else.
- The trace `message` field will probably be empty for tool-calling turns, so the endpoints above are counted from
  calls and token counts only.
- The estimate behind "10 or fewer": removing about half of the growth roughly doubles the call index of the first
  compaction, and 16 tasks per draw compact at call 14 or earlier.

## Readings

Fixed by the operator 2026-11-18T12:40Z, before any run of either tree.

- Each tree runs d1 on cdev-56 at concurrency 4; d2 only if d1 >= 22 (base 22, 22).
- Kept: two-draw mean > 25. Mean in (24, 25]: a third draw of each arm decides. d1 < 22: not kept on one draw.
- T-31b-004 endpoint: tasks whose first compaction comes before the first successful edit, 25 and 18 in the base, at 10 or fewer. If the endpoint is met and resolves do not rise, the lesson is that compaction was a symptom of slow localisation, not a cause of the losses.
- T-31b-004 guard: if empty patches rise above 15 or tool-call format errors appear on more than 3 tasks, dropping the thoughts from history broke the model's continuity; not kept whatever the resolves.
- T-31b-005 endpoint: tasks with a "Path traversal detected" rejection, 19 and 20 in the base, under 5.
- If both are kept, or both are positive (d1 > 22) without reaching the bar, the next round composes them.

## Results

(appended after the runs)

### T-31b-004 nothoughts, read 2026-11-18T16:45Z

d1 15/56 (base 22, 22). Empty patches 27 (base 11, 12), tasks at the time cap 36 (16, 14), mean
calls 14.7 (19.3, 18.3). Guard applied (empty patches above 15): not kept; d2 not run. Without its
earlier thoughts the model made fewer calls in the same time, so it re-derives its plan each turn;
the compaction endpoint is moot.

### T-31b-005 inline-scratch d1, read 2026-11-18T18:35Z

24 against base 22, 22 (up 5, down 3). At call cap 11, at time cap 13, empty patches 12. d1 >= 22,
so d2 is queued (R-003-31b-inline-scratch-d2); kept only if the two-draw mean is above 25.
