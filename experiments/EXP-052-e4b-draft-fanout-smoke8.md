# EXP-052 — Draft fan-out at the edit point on the E4B, `SequentialAgent[reader, ParallelAgent[5 drafters], applier]`: smoke-8 screen (D-007 tree T2)

**Date:** 2026-11-07
**Type:** smoke-8 screen
**Cohort:** smoke-8
**Ladder:** L2 (built, **not pushed**: the GPU word is the user's and has not been given). Source read and prompts are L0 work; no trace was mined here (EXP-051 did that).
**Pre-registered:** this file is committed **before** any kernel push. Sections 3 and 4 are written blind and are not revised after the numbers land. A badly drafted reading gets its defect logged in section 7, not rewritten.
**Serves:** D-007 (`knowledge/directions/D-007-full-vram-agent-architecture.md`, "Ranking after EXP-051": T2 is the only open tree), C-023.
**Folds in:** EXP-045's question (does the E4B run an informative python reproduction after its last edit?), added to this screen by the lead before anything was committed: endpoints E12 to E14 and reading Q. EXP-045 stays built and not pushed and its file is not edited here.
**Relates:** EXP-042 (informative checks after the last edit on 1 to 2 of 8 smoke-8 tasks), EXP-045 (measures C and I, section 2.2), EXP-051 (T1 and T4 closed, the budget does not bind on the E4B), EXP-049 (the VRAM desk check), EXP-046 (the sequential team killed on its locate stage), EXP-040 (the only tree with a Parallel stage that has run), EXP-033 and EXP-038 (the single-loop references), EXP-032 (call budget per stage), EXP-050 (the gate-override wording).
**Tags:** [V] verified in source or a committed EXP section, with file:line or section; [I] inference or arithmetic; [H] hand judgement.

## 0. Verdict, first

A tree is built and packed, and **nothing is pushed**. The shape is **S**: `SequentialAgent[reader, ParallelAgent(5 tool-less drafters), applier]`. K = 5. The screen asks one near-deterministic question: **does a tree that forces five drafted edits to the applier produce a non-empty applied patch on more of the 8 tasks than the single loop did, inside the clock, without the tree re-running?** It can kill the claim or promote it to a dev-48 arm. It cannot show an effect on resolves.

## 1. Why this, now

EXP-051 closed T1 (replace serial turns) and T4 (two base models) and left T2 open: the E4B ends 47 of 48 tasks by its own submit with a mean of 8.9 of 28 calls and 86 s of 480, so the budget does not bind and idle VRAM can buy several drafts per edit at the point where the single loop fails (edits that do not match the file: EXP-033, EXP-038, EXP-046). EXP-046 killed the sequential team because its locate stage skipped its reads on 5 of 8 tasks and handed over guesses. This tree changes two things against that kill: the reader's report must carry the **exact current text** of the region (a report without a read cannot), and five drafts replace one planned edit, so that one inexact draft is not the whole attempt.

## 2. Design

### 2.1 Source read: the two shapes, and the choice

**Chosen: S.** All K drafts reach the applier, the applier is the last stage and holds `submit_patch`, and nothing runs after a submit.

| Fact | Source | Consequence |
|---|---|---|
| A `SequentialAgent` runs its sub-agents in order on the same context and does not change the branch | `google/adk/agents/sequential_agent.py:55-92` [V] | reader, then the drafters, then the applier; the applier starts only after every drafter has finished |
| A `ParallelAgent` gives each child its own branch name and runs the children as concurrent tasks | `parallel_agent.py:35-48`, `:51-85` [V] | five drafters at once; each drafter's events carry its own branch |
| `include_contents: default` gives the full history; an event is visible if the current invocation branch is empty or the event has no branch, otherwise only on an equal or dotted-prefix branch | `flows/llm_flows/contents.py:71-91`, `:748-763` [V] | the applier (no branch) sees every drafter's events; a drafter sees the reader's events (no branch) and not its siblings' (sibling branches) |
| Other agents' events are shown as user-role "For context" text; tool calls and results become text; thoughts are left out | `contents.py:616-681` [V] | the applier reads each draft as text in its history |
| `output_key` stores the final text with thought parts excluded | `agents/llm_agent.py:859-863` [V] | a drafter's thinking does not land in `draft_N` |
| `{key?}` in an instruction is replaced from session state; the template is scanned once and the substituted value is not scanned again | `utils/instructions_utils.py:81-124` (the sub is one pass over the template at `:124`) [V] | drafts that contain braces cannot break the applier's instruction; an unset key becomes an empty string |
| The instruction is rebuilt on every request from state, so templated text survives compaction; the events copy does not | `instructions_utils.py:81-124`; compaction fires at a prompt of 14,336 tokens or more and keeps the last 5 events (EXP-049) [V] | the drafts reach the applier by two channels, state (compaction-proof) and events (not) |
| `with include_contents: none` the window starts at the latest user event or another agent's reply, so the task message is dropped | `contents.py:569-580` [V] | the drafters use `none` and read the reader's report through `{plan?}`; the reader and the applier use `default` |
| `patch_submitted` breaks the harness loop; a final text from a non-user author after it also breaks it | `swegemma/harness/agent_runner.py:920-922`, `:854-864` [V] | the tree does not re-run after `submit_patch` |
| A pass with no tool call gets a nudge (up to 3), a `continuation_nudge` step is recorded, and the whole root tree re-runs on the nudge message | `agent_runner.py:962-973`, `:1008-1010`, `:1021-1024` [V] | a text ending of the applier before a submit is the re-run route (EXP-049, EXP-040 on httpx_3672); the applier's prompt forbids it and the trace counts it (row 1) |
| One `run_async` pass per loop iteration; `max_llm_calls` is `budget.turns` | `agent_runner.py:788-811`, `:714-716`, `:801` [V] | `max_turns` bounds model calls over the whole tree, drafters included |
| Shared counters with a lock: calls, turns | `swegemma/harness/context.py:139-140`, `:277-299`, `:468-551` [V] | one budget for all stages; there is no per-stage cap |

**Shape A rejected** (a single loop plus one `agent_tool` wrapping the `ParallelAgent`). The dispatch feared that K-1 drafts are lost. That is not quite true: `AgentTool` copies the parent state in (`google/adk/tools/agent_tool.py:251-260`), forwards every `state_delta` back to the parent (`:270-272`) and returns only the last event's text (`:281-289`), so `output_key` values do come back, and a parent instruction with `{draft_N?}` would show them. A is rejected for three other reasons [V, [I] for the effect]: (1) the child runs in a fresh in-memory session and its only input is one `request` string argument (`:162-181`, `:227-230`), so the exact region would have to travel through a model-written tool argument, a copy the E4B does not do reliably (EXP-043); (2) the fan-out becomes a choice of the single loop, which may never call the tool, and this screen needs the fan-out on every task; (3) the single loop has no stage boundary, so it can submit, or end in text, before or after the call, and the control flow is the model's. S forces the order by construction.

### 2.2 The tree

`experiments/EXP-052/candidate-t2/` (18 files). Root `SequentialAgent` `swe_agent`, three children:

| Stage | Class | Tools | Window | Hand-off |
|---|---|---|---|---|
| `reader` | LlmAgent, E4B, `sampling.yaml` (EXP-033's) | `read_file`, `run_command`, `get_status` | default | `output_key: plan` |
| `draft` | ParallelAgent of `drafter_1` to `drafter_5` | none (`tools: []`) | none | `output_key: draft_1` to `draft_5`, read by `{plan?}` |
| `applier` | LlmAgent, E4B, `sampling.yaml` | `run_command`, `read_file`, `edit_file`, `write_file`, `get_status`, `submit_patch` (the EXP-033 six) | default | instruction carries `{plan?}` and `{draft_1?}` to `{draft_5?}` |

- **Reader.** It holds no edit tool, but `run_command` is a free shell (`swegemma/tools/execution.py:47`, EXP-051), so "no edit" holds **by the prompt and not by the tool list**; section 7 item 2 says so and row 1 checks the command names. A read-only `read_file` reader (as EXP-040's proposer) was the alternative; it was not chosen because the shell is the only search the registry has and EXP-046's locate, which had no search, skipped its reads. The prompt (`prompts/reader.md`) is written against EXP-046's kill (section 9 there: locate made no read on 5 of 8 tasks, and handed over a plan from the problem statement alone; on requests_7205 the planned replacement equalled its search text; on fastapi_14301 5 of 5 edits failed to match; on rich_3468 six reads were followed by text and no edit). Its mechanisms: the first reply must be a tool call; a report with no `read_file` on the named file is declared wrong and said to make every later stage fail; at most six `read_file` calls and no test files; the report's form is fixed (`ISSUE`, `FILE`, `LINES`, `REGION`, `CHANGE`, `END`), with `REGION` the **exact current text copied from the `read_file` result, as plain text, not the escaped form the tool result shows** (`read_file` returns a JSON string, `swegemma/tools/workspace.py:88-172`, 150 lines and 10,000 characters at most). **Only the model ends a stage that holds a tool (EXP-046 section 0); this prompt cannot make the reads happen, it can make a report without them recognisable, and the readings count them.**
- **Drafters.** Five prompts, each with its own angle at the **front** of its instruction, so no prefill is shared between the five requests: 1 the smallest change, 2 the cause (the first place the wrong value is produced), 3 the guard (a branch for exactly the input the issue names), 4 the contract word for word (every required string checked against the new lines), 5 a different shape (the opposite route to the obvious change). Temperatures 0.3, 0.5, 0.7, 0.9, 1.0 (chosen, not tuned). Output form: `FILE`, `OLD` and `NEW` blocks between `<<<` and `>>>`, a one-line `WHY`, and `END`; `NO DRAFT` if the report has no region. `max_output_tokens` 3072 and `thinking_budget` 1024 with thoughts excluded: a draft is label plus old and new text, and a cut draft loses its new text, so the voters' 256 is not used; a draft with no closing `END` counts as cut.
- **Applier.** `prompts/applier.md` is the EXP-033 prompt with its contract, locate and edit-by-call-12 sections replaced by: decide one reproduction before any call and reuse it; try the usable drafts in order 1 to 5 with `edit_file` (a failed match goes straight to the next draft, no re-read); after an applied draft run the check once; keep the first draft that passes (or whose check fails only for missing fixtures, imports or pre-existing breakage); otherwise undo with `git checkout -- FILE` and take the next; if none passed, re-apply the first that applied; if none applied, one `read_file` of the region and one edit of its own; **the last action must be `submit_patch`, never a closing text** (the re-run route). No numeric budget is written in the prompts; the task message states the budgets (`agent_runner.py:339-352`, `:385-390`).
- **Lint.** The prompts contain no pip, network, subprocess, mcp or URL wording and no repo-specific names; the validator and the packer's rejected-marker scan passed (section 8). The prompts contain no braces other than the `{plan?}` and `{draft_N?}` placeholders (the templater would try every other `{...}`).

### 2.3 K and the caps

| Setting | Value | Why |
|---|---|---|
| K | **5** | within the dispatch's 4 to 6; five angles are distinct; one more adds a request and an applier attempt for little diversity |
| `max_tool_calls` | **45** (EXP-033: 28) | reader worst measured 13 counted calls (EXP-040 section 9.8); applier about 3 per draft (edit, check, undo) so 15 at K = 5, plus 1 to 3 for the fallback; 13 + 18 = 31 worst case, so 45 starves neither stage and leaves room for the start of a re-run; `get_status` and `submit_patch` are free (EXP-046 section 9 note) |
| `max_turns` | **120** (EXP-033: 80) | every model event of every agent is a turn (`context.py:277-299`); a pass is about 14 to 22 turns typical (reader 4 to 9, drafters 5, applier 4 to 8) and about 40 to 55 worst; 80 would cut a restarted pass mid-applier and hide the re-run, 120 lets it finish (EXP-040 raised 80 to 200 for the same reason) |
| `max_time_minutes` | **8** | as S-014 and EXP-033 |
| `timeout_seconds` | 240 | as EXP-033 |

**The 10.5 h projection** (the operational rule, C-008), written as EXP-050 section 2.3 item 1 writes it [I]. Estimated mean 125 s (blind, section 4) x 120 tasks = 4.17 h, plus about 0.12 h of measured overhead (EXP-038: 444.8 s; EXP-040: 443.2 s) = **4.3 h**. At the kill line of row 3 (mean 240 s) it is 120 x 240 s = 8.0 h + 0.12 h = **8.1 h**. Both are under 10.5 h. The packer's formula gives 120 x (8 + 1.0) min = **18.00 h**, which exceeds the 11 h gate, and `analyze_traces` would give a worst case of 16.00 h (120 x 480 s). So this zip needs `--skip-budget-gate` (and `--allow-warnings` for the timeout and the sub-agent `submit_patch` notes), as EXP-033, EXP-038, EXP-040 and EXP-046 packed. **This is a screen and is never uploaded**; an upload would need its own override or a clock of 4.5 min (EXP-050 variant B pattern), decided after a dev-48 arm.

### 2.4 Cost

| Item | Seconds | Basis |
|---|---|---|
| kernel overhead (boot, decode probe, teardown) | about 445 | EXP-040: 443.2 s; EXP-046: 1,054 s span minus 551 s of tasks |
| per task: reader | 15 to 50 | EXP-040's proposer stage took 10 to 55 s |
| per task: five drafters, one concurrent burst | 10 to 30 | each 300 to 1,500 tokens; the EXP-040 burst of sixteen one-line votes took about 1 s, so the drafts' longer decode sets this stage [I, not measured] |
| per task: applier, one to five attempts | 30 to 90 | the single loop averaged 78.3 s (EXP-038 on these ids) with its own reads; here the reads are the reader's |
| per task, point | 100 to 150 | blind mean 125 s |
| 8 tasks + overhead | 1,245 to 1,645 s | = **0.35 to 0.46 GPU-h, point 0.40** |

Anchors: EXP-040 0.315 GPU-h (kernel log span 1,135.6 s) and EXP-046 0.293 GPU-h (1,054.1 s). **Conditional worst case:** all 8 tasks at the 480 s clock, 8 x 480 + 445 = 4,285 s = **1.19 GPU-h**. **Stop rule:** no re-run of a failed kernel without asking.

## 3. Endpoints

All are computed from `runs/EXP-052-t2/traces/trace_*.json`, `task_results.jsonl` and `summary.jsonl` (by `tools/analyze_traces.py --cap-minutes 8 --max-calls 45`) and hand counts, pass 1 unless stated. Counted calls are `read_file`, `edit_file`, `run_command` and `write_file` calls; `get_status` and `submit_patch` are free.

| # | Endpoint | Definition |
|---|---|---|
| E1 | Edit attempts | `edit_file` calls by the applier, per task |
| E2 | Successful edits | `edit_file` calls whose result is ok, per task |
| **P** | **Non-empty applied patch** | the task has at least one successful `edit_file` **and** its submitted patch is not empty (`patch_empty` false in `summary.jsonl`). A non-empty patch from a stray file does not count |
| E3 | Resolved | recorded, never an endpoint (n = 8) |
| E4 | Wall | per task and mean; tasks at the 8 min clock, the 45-call or the 120-turn cap |
| E5 | Turns and calls | per task, per stage author (reader, `drafter_1` to `drafter_5`, applier); counted and free calls |
| E6 | Stage presence and drafts | per task: which stage authors appear on pass 1; how many drafts have a `FILE` line, an `OLD` and a `NEW` block and a closing `END` (usable) or lack the `END` (cut) or say `NO DRAFT`; counts only, no text copied |
| E7 | Draft follow | per task with at least one usable draft and an `edit_file` call: whether the applier's first `edit_file` `old_string` equals (whitespace-stripped) some draft's `OLD` block, compared in memory, counts only recorded; and the index (1 to 5) of the draft whose edit the final patch carries, if any |
| E8 | Restarts | tasks with a `continuation_nudge` event (the `nudges` counter in `analyze_traces.py` misses these, EXP-040 section 9.8) |
| E9 | Reader reads | `read_file` calls by the reader per task, and the program name of each reader `run_command` (names only, to check that the reader stayed read-only) |
| E10 | Drafter-phase time | the gap between the reader's last step stamp and the applier's first step stamp, per task (the only stage-level time the trace gives: a parallel burst's step stamps fall within 0.15 to 0.44 s of each other, EXP-040 section 9, so per-drafter prefill and decode times are **not recoverable**); recorded, not read |
| E11 | Edit failure rate | failed `edit_file` calls over all `edit_file` calls; recorded, with EXP-046's 12 of 59 counted calls as the reference |
| **E12** | **C, compliance (EXP-045 section 2.2, as defined there)** | after the last `edit_file` call (any status), in step order and before the final `submit_patch` (or the end of the task), a `run_command` that **runs a python interpreter** (`python` or `python3` as the program, a heredoc that is then run included), that is **not** a `pytest`, `unittest` or `tests/` run, and whose observation is **not** an environment or launcher failure by EXP-042 section 2's sharpened rule (a collection error from `ModuleNotFoundError` or `ImportError`, `command not found`, `No such file or directory` for the target, `no tests ran`). A task with no `edit_file` call cannot comply and stays in the denominator of 8 |
| **E13** | **I, the EXP-042 sharpened measure** | tasks with at least one informative run of any kind (pytest, unittest, `tests/`, python) after the last `edit_file` call; a run whose output is an environment or launcher failure is not informative. References, same 8 ids: **2 of 8 (EXP-038) and 1 to 2 of 8 (EXP-033)** [V, EXP-045 section 2.2]. C is a subset of I. Also recorded: tasks with a python run after the last edit whose output is an environment or launcher failure (executed, not informative) |
| **E14** | **Which draft was kept, and what decided it** | per task, one label, counts only: (a) **reproduction-decided**: at least one applied draft was undone (a `git checkout --` run after an applied edit) after a run whose output was informative and showed the behavior unchanged, and a later draft was kept; (b) **first applied kept, check informative**: the first draft that applied was kept after an informative run, nothing was rejected; (c) **first applied kept, no informative check**: the first applied draft was kept with no informative run (none, or an environment or launcher failure), so the edit simply applied; (d) **fallback**: no draft passed and the first applied draft was applied again; (e) **own edit**: no draft applied and the applier made its own edit; (f) **no edit**. Plus the index (1 to 5) of the kept draft. **Selection by reproduction happened only in (a); (b) is a confirmation of the first draft that applied and selects nothing** |

**The references**, on the same 8 ids. In the order of the EXP-046 table (requests_7309, requests_7205, fastapi_14448, fastapi_14301, httpx_3672, fastapi_14605, rich_3468, rich_3006):
- EXP-038 single loop (the like-for-like tree, dev-48 run): counted calls 3, 4, 7, 5, 12, 11, 8, 4; turns 6, 9, 10, 8, 15, 14, 11, 7 (sum 80); mean wall 78.3 s; applied edit on 8 of 8; empty patches 0 [V, EXP-046 section 9, EXP-040 section 9.7].
- EXP-033 single loop (the paired smoke-8 draw): counted calls 3, 6, 4, 3, 1, 15, 5, 6; mean wall 56.9 s; applied edit on **6 of 8** (requests_7205 every edit failed, httpx_3672 never edited); empty patches 2 [V, EXP-046 section 4, section 9].
- EXP-046 sequential team (killed): applied edit on 5 of 8, empty patches 3, mean wall 69.0 s.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

First match, in order. The trace of the first task in kernel order, `fastapi_14301` (the order of `TASK_IDS`), is read first as the one-task control-flow check: rows 1(a) and 1(b) can fire on that trace alone. The kernel runs all 8 whatever it shows (the notebook has no early stop), so this saves analysis, not GPU.

| # | Condition | Reading |
|---|---|---|
| 0 | not exactly the 8 ids, `err` non-empty on any task, a model other than the E4B, or a kernel error | infrastructure; fix and re-run, no reading |
| 1 | **control-flow failure**, any of: (a) any task with a `continuation_nudge` event (the tree ran again); (b) a stage author missing from pass 1 of any task (reader, any of the five drafters, applier); (c) drafts did not reach the applier: among tasks with at least one usable draft and an `edit_file` call, the applier's first `edit_file` equals no draft's `OLD` on more than half of them (E7) | **kill**: the shape does not do what section 2.1 says it does; a fixed tree would be a new claim and a new screen |
| 2 | **P is 6 or fewer of 8** | **kill**: the non-empty applied patch did not rise above the single loop's (EXP-033's 6 of 8, see below) |
| 3 | the E4B mean wall is above **240 s** | **kill**: 120 x 240 s + 0.12 h is 8.1 h, and a tree this slow cannot be raised to a dev-48 arm at the 8 min clock without leaving no margin for the gate and the paired mean of EXP-038 (78.3 s) |
| 4 | rows 0 to 3 not met (so P is 7 or 8 of 8, mean wall at or under 240 s, no re-run, all stages present, drafts followed) | **promote** to one dev-48 E4B arm, paired against EXP-038, same 48 ids; **this is a recommendation only, a dev-48 arm needs the user's word** |

**The reference for rows 2 and 4, fixed here, with its ceiling.** "Rise above the single loop's" is read against **EXP-033's 6 of 8**, so the screen needs **P of 7 or 8**. It cannot be read against EXP-038: its subset has an applied edit on 8 of 8 and 0 empty patches, so 8 of 8 cannot be exceeded and one missed task would kill, which is not a near-deterministic reading at n = 8. **This bar therefore detects a tree that is worse than the single loop's lower draw, and it cannot show that the tree beats the single loop's higher draw; P of 8 of 8 is not evidence of an improvement on EXP-038.** (EXP-046 chose its floor the same way, section 4 there.) The 8 of 8 is recorded beside the reading and is not read. **A tied or near tie on P is not a promotion argument on its own**: the promotion in row 4 licenses the dev-48 measurement of section 5 and nothing else.

**Reading Q (a qualifier beside any row above; it changes no kill and no promotion, and it limits what the run may be said to have tested).** **If C (E12) is 2 or fewer of 8, the run is recorded as a test of edit landing only, and nothing is claimed about reproduction-based selection**, whatever row fires: in that case the applier's selector was in practice "the edit applies", and E14 is expected to show (c) or (e) on most tasks. The bar is EXP-045's row 2 (C of 2 or fewer of 8, against references with I of 2 or fewer). If C is 3 or more of 8, E14 is reported and (a) is counted, but 8 tasks do not support a claim that reproduction selected well; at most the count of (a) is carried to the dev-48 recommendation as a rate to watch. A task with C satisfied under (b) is not a selection.

**Recorded, not read:** resolves (E3); the number of tasks at a cap, with 3 or more written next to a promotion as a concern (as EXP-046 section 8.3 D); a mean wall above 140 s, written as a concern next to a promotion; the draft counts (E6); where the first `edit_file` came from (E7); the drafter-phase gap (E10); edit failure rate (E11); the reader's reads (E9).

**Prediction, blind.** P of 7 (6 to 8) [H]: the reader's report now carries the region and five drafts give the applier five tries, which should lift the edit match above EXP-046's 5, but the E4B's copy fidelity of a region out of an escaped JSON result is the weak link (EXP-043). Reader `read_file` calls: at least one on 7 or 8 of 8 tasks (EXP-046's locate made none on 5 of 8; the prompt now says the first reply is a tool call; EXP-040's proposer, with a read-only tool list, made 0 to 13 reads per pass, EXP-040 section 9.8). Mean wall 100 to 150 s, point 125 s. At least 4 usable drafts on most tasks. Applier follows draft 1 first on at least 5 of 8. No re-run (a text ending of the applier is the risk; EXP-040 had one in 8). Cost 0.35 to 0.46 GPU-h, point 0.40. **C (E12): 2 to 4 of 8** [H]: the applier's prompt makes the check an explicit step after each draft, which EXP-033 and EXP-038's prompts did not (I of 2 or fewer there), but it allows pytest as well as python, and E4B ignored a prompt-only rule in EXP-032 and EXP-040, so C may land at 2 or fewer and fire Q. **E14:** (c) on at least 4 of 8.

## 5. What this licenses

The screen decides one of two things.
- **Kill** (rows 1, 2 or 3): the claim "five drafted edits at the edit point raise the non-empty applied patch above the single loop" is not supported at this prompt, and no dev-48 arm is recommended. A kill on row 1 says the control flow of shape S does not hold on the E4B; on row 2 that the hand-over still loses the region or the drafts do not apply; on row 3 that the stage costs more clock than the loop has. A different reader or drafter prompt would be a new claim and a new screen, not a reading of this one. T2's sibling shapes (A) were rejected on source reasons in 2.1 and are not tested here.
- **Promote** (row 4): a recommendation to buy **one dev-48 E4B arm**, same 48 ids, paired against EXP-038, the same zip family. **The endpoint it should carry** is the non-empty applied patch share P (tasks with at least one successful `edit_file` and a non-empty submitted patch) with the edit-failure rate E11, paired per task against EXP-038 (the EXP-038 tasks with no applied edit are the cell that can move), and the mean wall against the ship line of about 311 s (mean x 120 plus overhead inside about 10.5 h, EXP-046 section 8.3 D). **Not resolves**: 5 of 48 or so gives no power (EXP-046 section 5). The arm costs about **1.7 GPU-h at the blind 125 s mean (48 x 125 + 445 = 6,445 s) and at most about 3.3 GPU-h at the 240 s kill line** (48 x 240 + 445 = 11,965 s).
- **EXP-045's question is folded in here.** Its enforcement screen (a prompt bullet asking for an informative python run after the last edit) stays built and not pushed; this screen measures the same C and I (E12, E13) on the applier's check, so a separate EXP-045 kernel is not needed to learn whether the E4B runs one. If reading Q fires (C of 2 or fewer of 8), whatever the row, the result is a test of edit landing only and says nothing about picking a draft by reproduction.
- It licenses nothing about the 31B (the 31B budget binds, EXP-051) and no upload. No claim status moves (only a critic `accepted` moves one).

## 6. Exact commands

```
python tools/validate_submission.py experiments/EXP-052/candidate-t2 --strict
python tools/pack_submission.py --src experiments/EXP-052/candidate-t2 --out dist/EXP-052-t2.zip --skip-budget-gate --allow-warnings
sha256sum dist/EXP-052-t2.zip
python tools/build_notebook.py --embed dist/EXP-052-t2.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-052-t2"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp052_t2/kaggle_eval_l4x4.ipynb
# after the user's GPU word, a separate job (none of this was run):
#   kaggle kernels push -p notebooks/exp052_t2   (kernel id rainm4/gemma4-exp052-t2)
#   later: kaggle kernels output, move the nested directory up to runs/EXP-052-t2, analyze_traces --cap-minutes 8 --max-calls 45, then count E1 to E14 and apply section 4 (rows, then reading Q)
```

## 7. Defects and limits of this pre-registration

1. **The reference's ceiling.** Row 2 is read against EXP-033's 6 of 8 because EXP-038's 8 of 8 cannot be exceeded (section 4). The lead's wording "rise above the single loop's on the same 8" is undecidable against EXP-038 and is decided here against EXP-033; **the lead should read this before the push**, and a different floor must be said before any kernel runs.
2. **The reader holds a write-capable shell.** `run_command` can edit the workspace; only the prompt bounds it. E9 lists the program names; a reader command that writes would leave a diff the applier did not make, and would be written up as a defect, not as a kill.
3. **Fan-out is not verified in a trace.** The parallelism of the five drafters, and that each drafter sees the report, rest on the ADK source (2.1) and EXP-040's run of the same constructs; E6 and E10 check presence and the gap, not concurrency. The per-drafter time is not recoverable (a burst's step stamps are 0.15 to 0.44 s apart).
4. **Drafter quality depends on the E4B copying a region.** The region comes out of a JSON-escaped tool result; a drafter that copies the escaped form fails to match. The edit failure rate (E11) shows it.
5. **Compaction is invisible in traces** and fires at a prompt of 14,336 tokens or more before any agent's call; the drafts reach the applier also through state, which survives it, so the tree does not rely on events.
6. **Applier prompt: the reproduction is the model's choice.** A check that does not exercise the changed behaviour passes every draft, and the first applied draft is then kept; the tree degrades to the single loop with a better first edit. It is not detected by any endpoint except E7 and E1.
7. **A one-task kernel was not built.** The "one-task trace check" is the order of reading the first task's trace (section 4); a separate one-task kernel would cost about 445 s overhead plus one task, about 0.15 GPU-h of the 0.40, so it saves little.
8. **The `max_turns` of 120 and `max_tool_calls` of 45 differ from EXP-033's 80 and 28**; the task message shows the budgets to the model (`agent_runner.py:339-352`), so the applier sees a larger allowance than the single loop did. This is a second changed variable beside the tree, and is noted, not removed.
9. **Cost is an estimate** built from EXP-033, EXP-040 and EXP-046 stage times; no E4B five-way drafter burst was measured.
10. **C excludes pytest by EXP-045's definition, and the applier's prompt allows a pytest check as an alternative.** A task whose applier runs only a named test counts toward I (E13) and not C (E12); that is as EXP-045 defined it, so the two screens stay comparable, and it can make Q fire although a check ran. The two numbers are both reported. The "informative" judgement on an output is by hand ([H]) where the rule is ambiguous, as in EXP-042 section 9.2; the labels of E14 are hand counts and mark ambiguous tasks.
11. **Thinking budgets are unverified** (VERIFY(Q3): the harness may not enforce `thinking_budget`); a drafter that thinks to the output cap loses its draft, which E6 counts as cut.

## 8. Built

Built 2026-11-07, **not pushed** (the GPU word is the user's and has not been given).

- **Tree:** `experiments/EXP-052/candidate-t2/`, 18 files: `agent.yaml`, `eval_config.yaml`, `configs/sampling.yaml` (EXP-033's values), `prompts/{reader,drafter_1..5,applier}.md`, `sub_agents/{reader,draft,drafter_1..5,applier}.yaml`. Dated EXP-052 comment headers on every YAML. Model `gemma-4-e4b-it-qat-w4a16-ct` on every LlmAgent. There is no baseline diff: the tree is new; `configs/sampling.yaml` is EXP-033's file with one comment line added, and the applier's tool list is EXP-033's.
- **Validate:** `python tools/validate_submission.py experiments/EXP-052/candidate-t2 --strict`: `RESULT: INVALID (1 errors, 2 warnings)`; the error is the packing gate (`120 x (8 + 1.0) min = 18.00 h`), the warnings the sub-agent `submit_patch` note and the 240 s timeout. The same as EXP-046's tree.
- **Pack:** `python tools/pack_submission.py --src experiments/EXP-052/candidate-t2 --out dist/EXP-052-t2.zip --skip-budget-gate --allow-warnings` (gate override, section 2.3; a screen, never uploaded): 18 reachable files, `RESULT: VALID (0 errors, 3 warnings)`, the rejected-marker scan raised nothing, 12.6 KiB. **Zip sha256 `29b7f4796ed1598680b0576927d6e9f3803bd791423a816f2daa5bd464594e47`** (confirmed with `sha256sum`; the worktree files were LF, no CR byte in any file). Members: `agent.yaml`, `configs/sampling.yaml`, `eval_config.yaml`, `prompts/{applier,drafter_1..5,reader}.md`, `sub_agents/{applier,draft,drafter_1..5,reader}.yaml`.
- **Notebook:** `notebooks/exp052_t2/kaggle_eval_l4x4.ipynb`, built with the command of section 6; `TASK_IDS` are the 8 smoke-8 ids in the cohort file's order (fastapi_14301, fastapi_14448, fastapi_14605, httpx_3672, requests_7205, requests_7309, rich_3006, rich_3468), `N_TASKS = 8`, `RUN_AGENT = True`, `RUN_GOLD_CONTROL = False`. `kernel-metadata.json` is EXP-046's with `id` `rainm4/gemma4-exp052-t2` and `title` `gemma4-exp052-t2` changed (`diff` shows those two lines only).
- **Cost:** 0.35 to 0.46 GPU-h, point 0.40; conditional worst case 1.19 GPU-h (section 2.4).

### 8.1 Pushed 2026-11-07, approved by the user (`knowledge/user-decisions.md`, c3ea250: "go ahead")

Sections 3 and 4 are unchanged. Before the push the worktree matched the build commit c66d68a (`git status --short` on the notebook directory and this file showed nothing) and `sha256sum dist/EXP-052-t2.zip` gave `29b7f4796ed1598680b0576927d6e9f3803bd791423a816f2daa5bd464594e47`. Nothing was rebuilt.
- **Push:** shortly before 2026-11-08 00:06 UTC (this record was written at 19:06 local, UTC-5, on 2026-11-07, read from the file mtime because `date` is not an allowed command, so the push time is a few minutes earlier than this and approximate), the bare push of `notebooks/exp052_t2`. Output: "Kernel version 1 successfully pushed." Kernel **`rainm4/gemma4-exp052-t2` version 1**, private, GPU on, `enable_internet` false, model source `google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2`. The guard did not refuse.
- **Status seen once, right after the push:** `KernelWorkerStatus.RUNNING`.
- **Stop rule:** no re-run of a failed kernel without the user's word. The download and analysis (E1 to E14, rows then reading Q, the first task in kernel order, fastapi_14301, read first) is a separate job, dispatched when the status says COMPLETE: `kaggle kernels output rainm4/gemma4-exp052-t2 -p runs/EXP-052-t2/`, move the nested inner directory up, `python tools/analyze_traces.py runs/EXP-052-t2 --cap-minutes 8 --max-calls 45`.

## 9. Results

Not run.

## Status

2026-11-07: **PUSHED, RUNNING** (approved by the user 2026-11-07, c3ea250). Kernel `rainm4/gemma4-exp052-t2` version 1, status seen right after the push `KernelWorkerStatus.RUNNING`, at about 2026-11-08 00:06 UTC (see 8.1). Tree `experiments/EXP-052/candidate-t2/` (shape S, K = 5, calls 45, turns 120, 8 min), zip `29b7f479...4e47`, notebook `notebooks/exp052_t2/`. Cost 0.40 GPU-h point, 1.19 worst case. Next: when `kaggle kernels status rainm4/gemma4-exp052-t2` says COMPLETE, the lead dispatches the download and analysis as a separate job (E1 to E14, rows then reading Q, fastapi_14301 read first). No re-run of a failed kernel without the user's word.
