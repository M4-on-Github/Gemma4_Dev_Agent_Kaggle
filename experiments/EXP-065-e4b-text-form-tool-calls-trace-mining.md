# EXP-065 - how often an E4B turn writes its tool call as text, across every local trace tree

**Date:** 2026-11-09
**Type:** zero-GPU analysis (L1 trace mining), 0 L4x4-h
**Cohort:** none
**Ladder:** L1; follow-up to the requests_7309 zero-call finding (EXP-059 section 9, EXP-064 job). Nothing on disk reads the rate of text-form calls across trees.
**Pre-registered:** the detector and the counted unit are fixed in section 2 before the counts were written; no kernel is involved.
**Serves:** the skill-tree readings of EXP-056 and EXP-057 (a tool-free ending is not a tool-use failure of the task), the pipeline trees (which agent writes text calls).
**Supersedes / relates:** EXP-033, 038, 045, 052, 055, 056, 057, 058, 061, 062; EXP-064 (running).

## 1. Why this, now

requests_7309 makes 0 native tool calls in all 4 skill-tree runs (EXP-056 r1 and r2, EXP-057 r1 and r2): on each, 4 model turns end in text, each followed by a `continuation_nudge`, and the task ends tool-free. The same task makes 4 to 8 native calls in the base runs. The question is whether this is one task or a tree-wide effect, and which agent it hits in the pipeline trees.

## 2. Method

Data: `traces/trace_<id>.json` of each run (one read, not the duplicate under `official/`), 12 runs, 136 task-runs. No script was run; every count is a `grep` over those files.

- **Text-form call:** a model turn (step with `event_type` final or text, no `tool_calls` field on that step) whose message holds a fenced json block whose body is shaped like a call: `{"tool_name": ...}`, `{"tool_calls": [...]}`, `{"tool_call": {"name", "args"}}`, an array of `{"tool", "args"}`, or an object or array of edit arguments (`filepath` plus `old_string`) with no tool name. Detectors: a json fence opening with `{` or `[`; the escaped keys `tool_name`, `tool_calls`, `arguments`, `args`, `command`, `old_string` inside a message. Fenced blocks that are not calls were read and excluded: a status object on EXP-038 fastapi_14512 (step 20) and an error-list array on EXP-057-r1 fastapi_14605 (step 16). A bare tool name as the whole message (EXP-038 fastapi_15800, step 7, `submit_patch`) is not JSON and is not counted.
- **Not detected:** unfenced calls inside prose, other fence languages. Checked and found none: a message that starts with `{`, the strings `tool_code` and `default_api` anywhere. So counts are a floor.
- **Tool-free task:** a trace with no `tool_calls` field at all. `grep -L` over all 12 runs lists 8 such traces; all 8 carry text-form calls, so no tool-free task is outside the count.
- **First-turn prompt tokens:** the first `prompt_tokens` in the file, for requests_7309 and fastapi_14605. In the pipeline trees that is the first model call in file order, the root's.

## 3. Counts per run

| Run | Tree | task-runs | tasks with at least 1 text-form call | tasks with every call text-form (tool-free) | where (step, agent) | first-turn prompt tokens, requests_7309 / fastapi_14605 |
|---|---|---|---|---|---|---|
| EXP-033 | base flat | 8 | 1 (fastapi_14301) | 0 | 1 turn, step 6, swe_agent (an edit call), native calls before and after | 2342 / 2821 |
| EXP-038 | base flat, dev-48 | 48 | 3 (fastapi_13537, rich_3521, rich_3934) | 1 (fastapi_13537: 4 turns, steps 4, 7, 10, 13, run_command and read_file shapes, 3 nudges) | rich_3521 step 7 and rich_3934 step 7, swe_agent, edit calls, native calls after | 2342 / 2821 |
| EXP-045 | base flat | 8 | 0 | 0 | none | 2378 / 2857 |
| EXP-055 | base flat | 8 | 1 (fastapi_14448) | 1 (4 turns, steps 4, 7, 10, 13, read_file) | swe_agent | 2440 / 2919 |
| EXP-058 | base flat, adapter | 8 | 0 | 0 | none | 2342 / 2821 |
| EXP-056 r1 | skill tree | 8 | 2 (fastapi_14605, requests_7309) | 2 (5 turns and 4 turns) | swe_agent | 3284 / 3763 |
| EXP-056 r2 | skill tree | 8 | 2 (requests_7309, rich_3468) | 2 (4 turns each) | swe_agent | 3284 / 3763 |
| EXP-057 r1 | skill tree | 8 | 1 (requests_7309) | 1 (4 turns, the last an edit shape) | swe_agent | 3335 / 3814 |
| EXP-057 r2 | skill tree | 8 | 1 (requests_7309) | 1 (4 turns) | swe_agent | 3335 / 3814 |
| EXP-052 | pipeline, SequentialAgent root | 8 | 1 (httpx_3672) | 0 | applier, step 15, its last turn (edit shape) | 1877 / 2356 |
| EXP-061 | pipeline, LlmAgent root | 8 | 1 (fastapi_14301) | 0 | applier, step 16, edit shape; the nudge then landed on the root, which went on with native calls | 1215 / 1694 |
| EXP-062 | pipeline, LlmAgent root, re-transfer | 8 | 2 (fastapi_14301, requests_7205) | 0 | reader step 5 (its final report was a run_command call, so the drafters worked from it); applier step 14 (edit shape), native calls after | 1258 / 1737 |

Totals by group:

| Group | task-runs | at least 1 text-form call | tool-free |
|---|---|---|---|
| base flat (033, 038, 045, 055, 058) | 80 | 5 | 2 |
| skill trees (056 r1 and r2, 057 r1 and r2) | 32 | 6 | 6 |
| pipeline trees (052, 061, 062) | 24 | 4 | 0 |

By agent in the pipeline trees: reader 1, applier 3, root 0, drafters 0 (a drafter's text output is the design, and no drafter wrote a call-shaped block).

## 4. Readings

1. Tool-free endings are 2 of 80 in the base flat trees and 6 of 32 in the skill trees. The 6 are on 3 task ids: requests_7309 (4 of 4 runs), fastapi_14605 (1 of 4, EXP-056 r1) and rich_3468 (1 of 4, EXP-056 r2). The base trees show the same failure on fastapi_13537 (EXP-038) and fastapi_14448 (EXP-055) once each, so the behavior is not new to the skill trees. No test is run on 6 of 32 against 2 of 80, because the task sets differ (EXP-038 is dev-48, the others smoke-8), so this is a pointer, not an endpoint.
2. The skill trees carry a longer first prompt: +844 to +942 tokens on both requests_7309 and fastapi_14605 against the base trees (3284 against 2342 to 2440; 3763 against 2821 to 2919). EXP-057 adds 51 over EXP-056. The pipeline trees' first model call is shorter (1215 to 1258) because it is the root or the reader, so those figures are not comparable.
3. Within a tool-free task the pattern is the same: model call, text-form call, nudge, three times, then the session ends. No task recovered to native calls once it wrote the first text call in these runs (all 8 tool-free traces have 4 or 5 text turns and no native call), while on the 3 mixed base tasks (EXP-033 fastapi_14301, EXP-038 rich_3521 and rich_3934) the model returned to native calls after 1 text turn.
4. In the pipeline trees the text-form call is rare (4 of 24) and the applier is the usual author (3 of 4). An applier text edit after native calls did not stop the task in 061 and 062. In 052 it was the applier's last turn.
5. The mechanism that tips a turn into text form is not read here. A prompt-length effect is a hypothesis; the tool declarations are not in the traces.

## 5. What this licenses

- Do not read a skill-tree resolve gap on requests_7309 as a skill effect: all 4 skill runs are tool-free there, and so are 4 other task-runs in the skill trees.
- A smoke-8 screen that records `n_calls == 0` for a task should say it is a text-form ending before calling it "no tool use". `analyze_traces.py` does not count text-form calls (a tool change, not made here: add a counter keyed on a json fence with a call-shaped body in a final or text turn).
- Not a claim: nothing here shows text-form calls cost a resolve. Resolves were not read.

## 6. Commands

Greps over `runs/<EXP>/traces` (flat trees) and `runs/<EXP>/runs/<EXP>/traces` (EXP-033, 055, 056, 057). Fixed strings: the escaped keys and the json-fence opener. `grep -L '"tool_calls"'` lists tool-free traces; `grep -c ""` over `task_results.jsonl` gives the task-run counts.

## 7. Defects

None yet.

## 8. Record

Zero GPU. No push.

## Status

2026-11-09: counts written, committed. Open: the tool-declaration cause (needs a one-task GPU probe, not requested).

---

## 9. Cross-check against the analyze_traces.py counter, 2026-11-09

`tools/analyze_traces.py` now writes `n_text_form_calls` and `tool_free` per task, and `text_form_calls_total`, `text_form_call_tasks`, `tool_free_tasks` and `tool_free_rate` in `aggregates.json`. The rule is section 2's, restated in code:
- A turn counts when it is an agent step with event_type final or text, has no `tool_calls`, and holds a call-shaped JSON value. Such a value starts a line or follows a fence opener.
- Call-shaped means one of these: a `tool_name` or `function_name` key; a name key (`name`, `tool`, `function`) plus an argument key (`args`, `arguments`, `parameters`, `params`, `input`); a string `tool` key with flat arguments; a non-empty `tool_calls` or `tool_call` wrapper; or `filepath` plus `old_string`. A list counts when any element counts.
- `tool_free` means 0 native calls (free tools included) and at least 1 text-form turn.

Command: `analyze_trace` over each run's `traces/` (scratch driver `out/exp065_xcheck.py`, untracked). Test: `tests/test_analyze_traces.py::test_text_form_calls_and_tool_free`.

| Run | task-runs | tasks with at least 1 text-form call | tool-free | text-form turns | section 3 |
|---|---|---|---|---|---|
| EXP-033 | 8 | 1 (fastapi_14301) | 0 | 1 | match |
| EXP-038 | 48 | 3 (fastapi_13537, rich_3521, rich_3934) | 1 (fastapi_13537) | 6 (4, 1, 1) | match |
| EXP-045 | 8 | 0 | 0 | 0 | match |
| EXP-055 | 8 | 1 (fastapi_14448) | 1 | 4 | match |
| EXP-058 | 8 | 0 | 0 | 0 | match |
| EXP-056 r1 | 8 | 2 (fastapi_14605, requests_7309) | 2 | 8 (4, 4) | tasks match; turns differ, item 1 |
| EXP-056 r2 | 8 | 2 (requests_7309, rich_3468) | 2 | 8 (4, 4) | match |
| EXP-057 r1 | 8 | 1 (requests_7309) | 1 | 4 | match |
| EXP-057 r2 | 8 | 1 (requests_7309) | 1 | 4 | match |
| EXP-052 | 8 | 1 (httpx_3672) | 0 | 1 | match |
| EXP-061 | 8 | 1 (fastapi_14301) | 0 | 1 | match |
| EXP-062 | 8 | 2 (fastapi_14301, requests_7205) | 0 | 2 | match |
| EXP-064 (extra) | 8 | 0 | 0 | 0 | matches the screener's 0 (8612b02) |

The group totals reproduce section 3: base flat 80 task-runs, 5 with a text-form call, 2 tool-free; skill trees 32, 6, 6; pipeline trees 24, 4, 0. Neither of the two non-call fences of section 2 (EXP-038 fastapi_14512 step 20, EXP-057 r1 fastapi_14605 step 16) is counted.

Mismatches and notes:
1. **EXP-056 r1 fastapi_14605: 4 turns, against 5 in section 3.** The fifth call-shaped block is at step 12, which is a thinking step, not a final or text turn. So section 2's own definition gives 4, and section 3's 5 counted the grep hit in the thinking step. The task-level counts (text-form, tool-free) are unchanged.
2. **EXP-038 rich_3521 step 7 has no fence opener.** Its edit object sits on its own lines, with a closing fence after it and no opening fence. A fenced-only detector misses it, so the counter also takes a JSON value that starts a line. Section 2 counted it through the key grep.
3. **EXP-056 r2 rich_3468 steps 7 and 10 use a list of `tool` objects with flat arguments.** A name-plus-args rule alone gives 2 turns there, not 4. The string `tool` rule was added so all four count, as section 3 counts them.
