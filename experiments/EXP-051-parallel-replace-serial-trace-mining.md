# EXP-051 — Could parallel work replace serial turns? Trace mining and a source read for D-007

**Date:** 2026-11-07
**Type:** trace mining (L1, zero GPU) plus a source desk check (L0). No kernel, nothing built, nothing pushed.
**Cohort:** none for the screen; the traces are the dev-48 runs EXP-038 (E4B) and EXP-028 arm R (31B), plus every other tracked per-task summary on overlapping ids.
**Ladder:** L0 and L1.
**Pre-registered:** the question list in section 2 is the lead's dispatch of 2026-11-07, copied in substance before any answer was written into this file. The numbers in section 9 were computed in the same session, before this file was committed (the summaries were read first, then this file was written). Section 4 is therefore a statement of what each answer would change, not a blind reading; no reading was set after a number was seen that it could have been bent to.
**Serves:** D-007 (a full-VRAM agent tree whose parallel samples are actions checked by execution: T1 isolated attempts, T2 draft fan-out at the edit point, T3 read fan-out, T4 two models). Also C-015 (best-of-N needs a selector).
**Relates:** EXP-049 (what the scorer fixes; parallel work modelled there only as added decode time), EXP-028 (31B arm R), EXP-032 (parallel localizers against the shared counter), EXP-033, EXP-038, EXP-040, EXP-044, EXP-046 (E4B runs), EXP-034 (best-of-N ceiling on the 31B), EXP-036 (regrades with shims).
**Tags:** [V] counted from a tracked summary or read in source with file:line; [M] mirror or README text whose enforcing code is not on disk; [I] inference or arithmetic from [V] numbers.

Path roots: `workspace.py` = `data/src/swegemma/swegemma/tools/workspace.py`; `execution.py` = `data/src/swegemma/swegemma/tools/execution.py`; `context.py` = `data/src/swegemma/swegemma/context.py`; `agent_runner.py` = `data/src/swegemma/swegemma/harness/agent_runner.py`; `schema.py`, `limits.py`, `discovery.py`, `resolvers/models.py`, `builders/llm.py` = `data/src/adk_submission/adk_submission/...`; `parallel_agent.py` = `data/src/google_adk/google/adk/agents/parallel_agent.py`; `README` = `data/raw/HARNESS_README.md`. The 28 calls, 80 turns and 8 minutes are our own `eval_config` values, not harness limits.

## 1. Why this, now

EXP-049 modelled parallel work as added decode time and found no 31B shape that fits. It did not ask the other question: could parallel work take the place of serial turns the loop already spends? That depends on where a run's budget goes today (how many calls, turns and seconds, and what ends the run), on what a parallel branch may touch, and on how many attempts at the same task have ever been tried. All three are answerable on disk at no GPU cost.

## 2. Design

Four questions, each answered from files already on disk.

1. **E4B single loop, EXP-038 dev-48.** Per task: tool calls (of 28), turns (of 80), wall, how the task ended, compactions; the model-versus-tool wall split and tokens per request if the traces allow.
2. **31B arm R, EXP-028 dev-48.** The same measures, plus calls, turns and wall before the first edit and the pre-edit calls by tool and program name.
3. **The pass-at-k ceiling on record.** Per task, the union of resolves over every E4B run and over every 31B v24 single-loop run on overlapping ids: k, resolved in at least one, resolved in all.
4. **Source read** with file:line: (a) path confinement of the four tools, (b) what `submit_patch` diffs, (c) one model or two per tree, (d) per-branch instruction, tools and model in `ParallelAgent`, (e) any per-sub-agent budget key.

Sources: `runs/EXP-038-e4b-dev48` and `runs/EXP-028-armR` re-analyzed with `tools/analyze_traces.py` (gitignored output); tracked summaries under `experiments/EXP-0NN/**/summary.jsonl`; `experiments/EXP-038/regrade/summary.jsonl`; the wheel sources under `data/src/`. Nothing was fetched.

## 3. Endpoints

Counts and file:line only. No test of significance is run; nothing here is a rate comparison.

## 4. What each answer would change (written with the question list, not after the numbers)

| Q | If the answer is | It would change |
|---|---|---|
| 1 | E4B runs end at a cap or the clock in a large share | a parallel tree has serial turns to replace; the budget is the binding thing |
| 1 | E4B runs end by submit with most of the budget unused | the budget does not bind on the E4B; a tree competes with a loop that is not short of turns, so it must win on quality, not on time |
| 2 | the 31B spends a large share of calls and wall before its first edit | a parallel localizer (T3) has a serial cost to replace |
| 2 | the 31B ends mostly at the call cap | any tree on the 31B pays from the same shared counter, so it must spend fewer calls per branch than the loop it replaces |
| 3 | union much larger than best single run, with tasks resolved in some runs but not all | an attempts tree (T1, T2) has a ceiling worth a selector |
| 3 | union equals the best single run | extra attempts have added nothing on record; a tree has no ceiling to buy |
| 4a | file tools confined, shell not | a per-branch tree under a private path is reachable by shell only |
| 4b | `submit_patch` diffs `/workspace` only | whatever a branch does elsewhere is lost unless copied back |
| 4c | one base model per tree | T4 as two models is closed; only adapters on one base remain |
| 4d | branches are separate files with their own fields | branches can differ in prompt and tools |
| 4e | no per-sub-agent budget | branches share one cap; a tree is a split of 28 calls, not extra calls |

## 5. What this licenses

It licenses ranking D-007 shapes against numbers (section 9) and against the shared-counter and shared-workspace facts. It does not license a screen on its own: no shape here has a selector, and the one thing the ceiling can say is how much a selector could be worth. Two measures the lead asked for could not be produced with the allowed tools (section 7), and a tool change is requested there.

## 6. Exact commands

```
python tools/analyze_traces.py runs/EXP-038-e4b-dev48 --cap-minutes 8 --max-calls 28
python tools/analyze_traces.py runs/EXP-028-armR --cap-minutes 8 --max-calls 28
python tools/run_forensics.py forensics runs/EXP-038-e4b-dev48
python tools/run_forensics.py forensics runs/EXP-028-armR
python tools/first_edit_dist.py runs/EXP-028-armR
```

Tracked summaries listed in section 9.3 were read as they are. The caps used for analysis are the values the runs were made under (EXP-038 and EXP-028 sections 2).

## 7. Defects and limits

- **No allowed tool gives calls or seconds before the first edit, the pre-edit calls by tool, or a true model-versus-tool wall split.** `tools/first_edit_dist.py` gives first-edit turn by cohort only. `tools/run_forensics.py forensics` charges each turn's elapsed time to the tool called in that turn, so a turn's model time is inside the tool's share. Ad-hoc scripts are outside what this agent may run, and a trick path to one was rejected as circumventing the guard. **Tool change requested (not made; `tools/` is not in the screener's paths):** a pre-edit profile in `tools/run_forensics.py` giving per task the calls and elapsed seconds before the first `edit_file` or `write_file`, counts by tool, and `run_command` counts by program name; and a model-versus-tool split from the per-step stamps (`extra.timestamp`, `extra.elapsed_s`). The natural hook is `turns_of(trace)` at `tools/run_forensics.py:108`. Why: the 31B pre-edit exploration is the one serial cost a parallel localizer could replace, and the turn proxy below is only a proxy.
- `n_calls` in `summary.jsonl` excludes the free `get_status` and `submit_patch`; on the 31B it can exceed 28, which is attempts refused after the cap [I]. `summary.jsonl` has no turn-cap flag, so "80 or more turns" is read as the turn cap [I]. `thinking_tokens` is null. Tokens per request use turns as the request count [I].
- Compaction (a prompt of 14,336 tokens or more, before each model call) is not visible in traces; the compaction counts are the analyzer's event counts.
- `summary.jsonl` `n_edit_fail` is lower by 1 than the trace on one EXP-044 arm X0 task (fastapi_13786); no effect on any verdict.
- EXP-040 (16 tool-less voters) and EXP-046 (a role team) are not single-loop runs; they are counted in 9.3 because the lead asked for every E4B run on overlapping ids, and marked there.

## 8. Built

Nothing. No kernel, no notebook, no candidate.

## 9. Results

### 9.1 Q1, E4B single loop, EXP-038 dev-48 (n = 48) [V]

| Measure | mean | median | p90 | max | sum |
|---|---|---|---|---|---|
| tool calls (cap 28) | 8.85 | 7.5 | 17 | 21 | 425 |
| turns (cap 80) | 12.5 | 11 | 20 | 26 | 601 |
| wall, seconds (cap 480) | 85.8 | 82 | 147 | 207 | |

- **How tasks ended:** submit 47; text with no submit 1 (fastapi_13537); call cap 0; turn cap 0; clock 0. Nudges after a text-only pass: 9.
- **Compactions:** 20 events over 18 tasks.
- **Tokens per request** (turns as the request count [I]): about 7,170 prompt and about 477 output.
- **Wall by tool in forensics** (includes the model's time for the turn, so not a split): edit_file 49.3%, read_file 18.8%, turns with no tool call 14.0%, submit_patch 9.1%, run_command 8.8%.
- **Model versus tool split:** not computed (section 7).
- [I] The loop used at most 21 of 28 calls and 207 of 480 seconds on any task. Its budget does not bind. If a tree splits 28 calls across branches, at the mean call use of 8.85 it fits about 3 branches (28 / 8.85); at the p90 of 17, one.

### 9.2 Q2, 31B arm R, EXP-028 dev-48 (n = 48) [V unless marked]

| Measure | mean | median | p90 | max |
|---|---|---|---|---|
| tool calls (cap 28) | 23.2 | 24.5 | 30 | 54 |
| turns (cap 80) | 29.2 | 27 | 56 | 82 |
| wall, seconds (cap 480) | 297.5 | 303 | 483 | 490 |

- **How tasks ended:** call cap 18; clock 6 (the six tasks with no submit; one also hit the call cap); turn cap 1 (fastapi_14360); four tasks at 80 or more turns; 24 submitted with no cap reached. Submit_patch share 87.5%; spin 24.4%.
- **Compactions:** 49 events over 36 tasks.
- **Wall by tool in forensics** (model time included): run_command 43.5%, read_file 25.7%, edit_file 18.8%, write_file 4.5%, submit 4.3%.
- **Pre-edit, by turn** (`first_edit_dist.py`; 44 of 48 tasks edit): median first-edit turn 8 for resolved tasks, 14 for failed, 31 for empty-patch. Tasks binned by first-edit turn 1-10 / 11-18 / 19-25 / 26 and later: 13 / 20 / 5 / 6. Share of turns before the first edit [I proxy, not wall]: about 47% for resolved and for failed tasks, about 97% for empty-patch tasks.
- **Run_command programs over the run** (whole run, not pre-edit): grep or rg 286, python 95, heredoc writes 48.
- **Not computed:** calls and wall before the first edit, and the pre-edit counts by tool and program (section 7).
- [I] The loop meets the call cap on 37.5% of tasks and the clock on 12.5%, so on the 31B the budget binds, and any branch pays from the same 28.

### 9.3 Q3, the pass-at-k ceiling on record [V]

**E4B** (runs: EXP-033 e4b, EXP-038 e4b, EXP-040 v1, EXP-046 team, EXP-044 x and x0; EXP-045 was never run):

| Group of dev-48 ids | n ids | runs per id (k) | which runs | resolved in at least 1 | resolved in all k |
|---|---|---|---|---|---|
| smoke-8 | 8 | 4 | EXP-033, EXP-038, EXP-040 (voters), EXP-046 (team) | 2 (fastapi_14301, rich_3006) | 0 |
| failed-edit-8 (EXP-044 set) | 8 | 3 | EXP-038, EXP-044 x, EXP-044 x0 | 0 | 0 |
| the other 32 | 32 | 1 | EXP-038 | 3 (fastapi_14463, rich_3905, requests_6644) | the same 3 (k = 1, so "all" and "at least one" coincide) |

- fastapi_14301 and rich_3006 are each resolved in 3 of their 4 runs and not in the fourth. The other six smoke-8 tasks are 0 of 4; the eight failed-edit tasks are 0 of 3.
- The total union is 5 tasks, the same 5 EXP-038 alone resolved. No later run added a task. Among tasks with k of 3 or more, none is resolved in all k.
- Regrade sensitivity (`experiments/EXP-038/regrade/summary.jsonl`, same patches, so not extra attempts): the E4B regrade with shims is 5 resolved, equal to as run. 15 of the 48 ids are gated (cannot be graded in the sandbox without shims).

**31B v24 single loop** (arm R and arm RH of EXP-028; k = 2 on all 48; EXP-023, EXP-027 are upload-only and have no per-task rows on disk):

| Measure | count |
|---|---|
| resolved by R | 9 |
| resolved by RH | 10 |
| both | 8 |
| at least one (union) | 11 |
| R only | fastapi_9753 |
| RH only | fastapi_5624, rich_3180 |

- Regrade sensitivity (same patches): R regraded with shims is 12 resolved against 9 as run.
- Wider 31B record (EXP-034 section 9.1, six dev-48 arms of which only R and RH are the v24 loop at 8 minutes; the other four are earlier variants): union 17, best single arm 12, resolved in all six 6, in some 11, in none 31. Within {R, RH}: union 11, union minus the best arm 1.
- [I] The ceiling on record: on the E4B, 5 of 48 (all from one run); on the 31B v24 loop, 11 of 48 from two runs, 1 task above the best run. Repeating the same loop has added at most 1 task on the 31B and 0 on the E4B.

### 9.4 Q4, source read [V unless marked]

**(a) Paths.** The three file tools are confined; `run_command` is not.
- `read_file`, `write_file` and `edit_file` each call `_resolve_workspace_path` (`workspace.py:113`, `:190`, `:239`; definition `:22-55`). A path beginning with `/` other than `/workspace` or `/workspace/...` raises the fixed message "Path traversal detected ... escapes workspace root" (`workspace.py:41-44`); a relative path that resolves outside raises the same (`:46-50`). A per-branch copy under `/tmp` is therefore not addressable by the file tools.
- `run_command` passes the string to `/bin/bash -c` with no path check (`execution.py:47`; Docker sandbox `data/src/swegemma/swegemma/sandbox/docker.py:704-712`; subprocess sandbox `sandbox/subprocess.py:495-501`). The subprocess sandbox maps `/tmp` to a per-sandbox directory (`subprocess.py:441-443`), so shell access to a private tree works in both sandboxes [V for the subprocess code; the scorer's sandbox choice is not on disk, I].
- Consequence for a private per-branch tree: it can be built, edited and tested only through `run_command`. That is the heredoc route arm R already uses 48 times (9.2) and that EXP-026 studied.

**(b) `submit_patch`.** It runs `git add -N .` and `git diff --binary` inside `cd /workspace` only (`execution.py:86-89`), strips protected and test files (`execution.py:103-110`), and stores the result (`:111-112`). Nothing outside `/workspace` is in the patch. A branch's result outside `/workspace` is lost unless a later step copies it back into `/workspace`.

**(c) One model or two.**
- The README states the rule: all agents in a submission share a single declared base model, `len(models) == 1`, checked in the scorer's `scripts/inference.py`; two declared base models raise `ParticipantVisibleError` (`README:181`, `:186-189`). The allowed names are listed at `README:109` and `:174-177`. [M: the enforcing script is not on disk.]
- What is on disk: `discover_declared_models` collects every `model` string across the tree (`discovery.py:761-804`), and the compiler resolves `model` per agent from the registry (`resolvers/models.py:77-79`; `builders/llm.py:71`) and would not refuse two aliases by itself. So the closure of T4 rests on the README text, not on code I could read.
- Per-agent LoRA adapters on the one base model are permitted (`README:205`; `schema.py:279`, `resolvers/models.py:46-76`). That is the only two-"model" form left.

**(d) `ParallelAgent` branches.** Each branch is a separate YAML file named by `SubAgentRef`, which holds only `config_path` (`schema.py:45-59`). Each LlmAgent file carries its own `instruction`, `tools`, `model`, `adapter` and `generate_content_config` (`schema.py:277-293`). `SandboxedParallelAgentConfig` adds nothing but `sub_agents` (`schema.py:338-347`). Branches run as concurrent tasks (`parallel_agent.py:51-85`), each on its own branch name (`parallel_agent.py:35-48`), but one `InvocationContext` copy shares the same harness context. So per-branch prompt and tools: yes. Per-branch model: only an adapter on the one base (c).

**(e) Per-sub-agent budget.** None. `ParallelAgent` has no budget field (`schema.py:338-347`); `LoopAgent` has `max_iterations` only (`schema.py:361`, cap `limits.py:193`); `generate_content_config` has `max_output_tokens` per call (`schema.py:207`), which bounds one answer, not a branch. The call and turn counters are the shared `tool_calls_used` and `llm_calls_used` (`context.py:139-140`), checked under one lock (`context.py:468-497`); the turn check sits under `count_tool_call`, so `submit_patch` and `get_status` bypass both (`execution.py:76`, `:119`). `eval_config` has four budget keys and `schema.py:179-202` forbids extra keys. A "per-branch call limit" in a prompt is not enforced (EXP-032, EXP-040, EXP-046).

### 9.5 Which D-007 shapes each answer opens or closes

- **Q1 (E4B budget):** opens T1 and T2 on time and calls (the loop uses a fraction of both), and closes any argument that a tree is needed to rescue capped runs, since none ended at a cap; at the mean call use about 3 branches fit in 28 calls [I].
- **Q2 (31B budget):** closes T1 and T2 on the 31B as a time or call purchase (the loop is already capped 37.5% of the time); leaves T3 only if a pre-edit profile (section 7) shows the read calls are separable from the editing calls.
- **Q3 (ceiling):** closes whole-attempt best-of-N on the E4B (union 5 equals one run, none resolved in all k), and bounds it on the 31B at 1 task above the best run in {R, RH}, below the board MDE of about 4 tasks; the only shape with headroom is one with a selector that has not been shown to exist (C-015).
- **Q4a (paths):** T1 branches can live under a private path only through `run_command`; T2 and T3 branches that edit or read `/workspace` use the file tools but share one tree.
- **Q4b (`submit_patch`):** closes any branch output kept outside `/workspace` unless copied back before the single submit.
- **Q4c (one model):** closes T4 as two base models on the README's word (enforcing code not on disk); leaves adapters on one base.
- **Q4d (branches):** opens T2 and T3 with different prompts and tools per branch.
- **Q4e (no budget key):** closes any split of the cap by configuration; a branch's share of the 28 calls can only be advised in a prompt, which is not enforced.

## Status

2026-11-07: zero-GPU desk check and trace mining complete. Q1, Q3 and Q4 are answered; Q2 is answered except for calls and wall before the first edit, the pre-edit breakdown by tool and program, and any model-versus-tool split, which the allowed tools cannot produce (tool change requested in section 7). The numbers were computed before this file was committed (see the header). Not pushed. No GPU used.
