# EXP-064 — Location-diverse drafters over the EXP-062 pipeline tree (smoke-8 screen, D-008 rank 2)

**Date:** 2026-11-09
**Type:** smoke-8 screen, ~0.33 L4x4-h (EXP-061 0.324, EXP-062 0.323; the longer reader report adds a little). One push, no upload, no dev-48. This job is zero GPU and builds only; the lead releases the push.
**Cohort:** smoke-8
**Ladder:** L2. L0 and L1 are section 1 (counted from `runs/EXP-061-r`, `runs/EXP-062-r`, `runs/EXP-052-t2`, all `official/traces/`).
**Pre-registered:** this file is committed before the push. Sections 3-5 are written blind and are not revised.
**Serves:** D-008 rank 2 (`knowledge/directions/D-008-e4b-loop-restart-pipeline-stages.md`, 63ec30e), amended by the critic's D-008 review (`experiments/EXP-062/critic.md`, ff8654b and 81c907d): harm row, kept row on the drafts, the two movable tasks, applier unchanged.
**Relates:** EXP-052 (pipeline), EXP-061 (LlmAgent root), EXP-062 (re-transferring root; this arm's baseline tree). EXP-063 is the experimenter's reproducer-selector arm; the two are fused only in a later round, so the applier is byte-identical here.

## 1. Reference counts and cue sites (zero GPU, counted from traces on disk)

Method. For each task in each run: the reader's final report (steps where `author` is `reader`), the `FILE:` line of each of the 5 drafts (`drafter_1` to `drafter_5`), and the applier's tool calls. The gold files are the non-test paths in the task's gold patch header (`data/raw/tasks.jsonl`, paths only; no gold content is copied anywhere). A draft "targets the gold file" if its FILE is any non-test gold file. The first-gold-file convention is given beside it. A draft with `NO DRAFT` or no FILE line has no target.

**Gold files (non-test).**

| task | gold files |
|---|---|
| fastapi_14301 | `fastapi/dependencies/utils.py` |
| fastapi_14448 | `fastapi/dependencies/models.py`, `fastapi/dependencies/utils.py` |
| fastapi_14605 | 7 files: `fastapi/dependencies/utils.py`, `fastapi/exceptions.py`, `fastapi/openapi/utils.py`, `fastapi/params.py`, `fastapi/routing.py`, `fastapi/temp_pydantic_v1_params.py`, `fastapi/utils.py` |
| httpx_3672 | 7 files, among them `src/httpx/_parsers.py` and `src/ahttpx/_parsers.py` (first) |
| requests_7205, requests_7309 | `src/requests/utils.py` |
| rich_3006 | `rich/repr.py` |
| rich_3468 | `rich/console.py` |

**The reader names one file and one region, so every task has one target file.** The reader format has one FILE slot, and the drafter prompts say "the path as the reader gave it". Counts per run:

| | EXP-061 | EXP-062 | EXP-052 |
|---|---|---|---|
| tasks with at least one draft FILE | 8 | 7 | 8 |
| distinct target files across the 5 drafts, per task | 1 on every such task | 1 on every such task, 0 on fastapi_14301 | 1 on every such task |
| mean distinct target files over the 8 tasks | 1.00 | 0.875 | 1.00 |
| tasks with 2 or more distinct target files | 0 of 8 | 0 of 8 | 0 of 8 |
| tasks where any draft targets a gold file (any-file convention) | 6 of 8 (misses fastapi_14448, fastapi_14605) | 7 of 8 (miss fastapi_14301, no draft) | 7 of 8 (miss fastapi_14448) |
| same, first-gold-file convention | 5 of 8 | 5 of 8 | 5 of 8 |

EXP-055's 6 of 8 gold-file landings is a patch-level count on the single loop and is a secondary reference, not comparable to the draft-level counts above.

**The reader's single pick varies from run to run on the class-A tasks, and the region inside a file varies on the class-C task.**
- **fastapi_14605** (gold 7 files): EXP-061 `fastapi/_compat/v1.py` (not a gold file), EXP-052 `fastapi/exceptions.py`, EXP-062 `fastapi/utils.py`, 5 drafts each. Three runs, three different files.
- **fastapi_14448**: EXP-061 reader report at step 7, then 5 drafts at steps 8-12, all `fastapi/routing.py` (not a gold file). EXP-052 the same file. EXP-062 `fastapi/dependencies/models.py` (gold).
- **fastapi_14301** (EXP-062): the reader replied at steps 4-5 with no tool call and no report, so all 5 drafts were `NO DRAFT` (steps 6-10). The applier then edited `fastapi/dependencies/utils.py` itself at step 14 (a gold file). EXP-061 and EXP-052 had the reader name that file with 5 drafts.
- **rich_3468**: the reader's region in `rich/console.py` was lines 310-317 (EXP-061), 1593-1650 (EXP-062) and 2128-2138 (EXP-052), three non-overlapping regions of one gold file.
- **requests_7309**: lines 497-503 (EXP-061), 523-533 (EXP-062), 531-538 (EXP-052). EXP-061 has 4 drafts with a FILE line; `drafter_2` (step 12) has none.
- **rich_3006** (EXP-062): reader report at steps 7-8, drafts at steps 9-13; drafters 1-4 are the same one-token edit and drafter 5 reorders the branches. The applier tried draft 1 at step 14 and submitted at step 16. This agrees with the critic's count that the applier took draft 1 on 5 of 6 matched tasks (I verified this one task only).

**What this does to the D-008 kill criterion.** "Distinct target files above EXP-061's count" is cleared by any task on which the reader lists two files, so it separates "exercised" from "not exercised" and no more. The deciding quantity is any-draft-on-gold-file, and its reference is already 6 to 7 of 8, so the room above it is 1 to 2 tasks (fastapi_14448, fastapi_14605, and fastapi_14301 when the reader reports nothing). Only fastapi_14448 and rich_3468 can still change outcome on this cohort (critic; EXP-053 section 1 splits their failures into wrong file 4, wrong fix 4, failed edit 0).

## 2. Design

The change is to the reader's report format and to what each drafter reads from it. One variable: where the five drafts edit.

| | value |
|---|---|
| tree | `experiments/EXP-064/candidate-loc/` = `cp -r experiments/EXP-062/candidate-r`, then `prompts/reader.md`, `prompts/drafter_1.md` to `drafter_5.md` replaced and one comment line added to `sub_agents/reader.yaml` |
| diff | `diff -ru experiments/EXP-062/candidate-r experiments/EXP-064/candidate-loc` shows only those 7 files. `agent.yaml`, `eval_config.yaml`, `configs/`, `prompts/root.md`, `prompts/applier.md` and every other `sub_agents/*.yaml` are byte-identical (the full diff is about 150 lines of prompt text; it is reproduced by the command and is not copied here). Each drafter prompt gains one paragraph, "Your location is LOCATION i ... use LOCATION 1 instead ... NO DRAFT", and changes "REGION" to "the REGION of your location"; the reader prompt gains section 3 and the LOCATION blocks |
| reader | final report is `ISSUE` and then up to 5 blocks `LOCATION n:` with `FILE`, `LINES`, `REGION` (at most 25 lines), `CHANGE`, then `END`. Location 1 is the most likely. A location must be one the reader opened with `read_file`; one honest location is allowed. `read_file` cap 6 -> 8 so the reader can open callers and callees. A different file is preferred, else a different function or branch |
| how the list reaches a drafter | unchanged plumbing. The reader has `output_key: plan` and `include_contents: default`. Its final text (thought parts excluded) is stored in state and reaches each drafter through the `{plan?}` template. Each drafter has `include_contents: none` and `tools: []`, so `{plan?}` is all it sees of the code and all five drafters receive the whole report; the drafter prompt tells drafter i to use only `LOCATION i` and, if the report has fewer than i locations or LOCATION i has no REGION, `LOCATION 1`. The report is also in the applier prompt through `{plan?}`, which is rebuilt from state on every request |
| drafters | each keeps its own angle sentence and its temperature, `max_output_tokens` 3072, `thinking_budget` 1024 (yaml untouched). Drafter 1 also keeps "the smallest change", drafter 2 "the cause", and so on. Keeping the angle is the smaller diff |
| applier | unchanged, byte-identical (critic item 4, so a later fusion with EXP-063 pairs cleanly) |
| eval config | `timeout_seconds` 240, `max_tool_calls` 45, `max_time_minutes` 8, `max_turns` 120 (EXP-062's) |
| zip | `experiments/EXP-064/exp064_loc.zip` (gitignored), sha256 in section 8. Packed with `--skip-budget-gate` because 8 min is above the 4.5 min packing gate (18.00 h nominal, the same override as EXP-061 and EXP-062). **Not an upload.** |
| notebook | `notebooks/exp064_loc/`, EXP-062's build command with only the zip and `EXP_ID` changed; kernel `rainm4/gemma4-exp064-loc` |
| cost | ~0.33 GPU-h; no slot |

**Known limits of the design, written before the run.**
1. **Reader budget.** The reader's sampling is `configs/sampling.yaml`: `max_output_tokens` 8192 with `thinking_budget` 4096. Five regions of 25 lines are about 2,000 to 2,500 output tokens, which fits, but a long free-text reasoning step before the report (seen on rich_3006, EXP-062 step 7) can cut the report. A report with no `END` is recorded as cut.
2. **Regions need real reads.** A drafter has no tools, so a location without an exact REGION gives it nothing to copy. The prompt therefore allows fewer than 5 locations and forbids unopened ones. With K reads of 120 lines, K up to about 4 distinct places is the realistic number.
3. **Fallback to location 1 recreates the duplicates when K is under 5.** If the reader lists 2 locations, drafters 3, 4 and 5 all draft location 1. The one-line alternative is a cyclic rule, drafter i takes location ((i-1) mod K)+1, which spreads the drafters over the K locations present but needs the drafter to count K. It is not built here; the lead can release it as a next round.
4. **Longer prompts.** Each of the five drafter prompts and the applier prompt now carries the whole report (up to 5 regions). EXP-062 already crossed 14,336 prompt tokens on 3 tasks. The expected failure mode is more in-flow compactions and a longer wall; the harm row covers it.
5. **Applier wording.** The applier prompt's fallback names "the reader's CHANGE line" and "the region the reader named" in the singular. With several locations that now means location 1 in practice. It is left as is and counted only if a trace shows the applier confused by it.
6. **The applier tries drafts in order 1 to 5** and keeps the first that applies and passes a check that EXP-059 found rarely tests the edit. So the kept patch will mostly still be draft 1 at location 1. The screen measures the drafts, not the patch (critic item 2).

## 3. Endpoints, fixed in advance

Per task, from `official/traces/`, `task_results.jsonl`, `summary.jsonl` and the kernel log:
- **L (locations listed).** The number of `LOCATION` blocks with a REGION in the reader's final report. Also record a missing `END` (cut) and a reader that gives no report.
- **F (distinct target files).** The number of distinct FILE values across the 5 drafts of the task; a draft with `NO DRAFT` or no FILE adds none. Reference: 1 on every task, mean 1.00 (EXP-061, EXP-052), 0.875 (EXP-062).
- **R (distinct target regions).** The number of drafts' source locations whose LINES ranges do not overlap (a different file counts as distinct). Recorded, because rich_3468 and requests_7309 differ by region inside one file.
- **G (any draft on a gold file).** Tasks where at least one draft's FILE is a non-test gold file of the table in section 1; also the first-gold-file convention. Reference 6, 7, 7 of 8 (any-file) and 5, 5, 5 (first-file).
- **Movable tasks, reported separately:** `fastapi_14448` and `rich_3468`: for each, the L, the 5 draft files and regions, and whether a draft is on a gold file. References: fastapi_14448 gold in EXP-062 only (1 of 3 runs); rich_3468 gold file in 3 of 3 runs with three different regions.
- **Duplicates.** Drafts per task that are near-copies of another draft's NEW block (recorded by reading, not counted as an endpoint).
- **Harm.** Any time, call or turn cap hit; empty patches (EXP-061: 2 of 8, EXP-062: 1 of 8, so the base maximum is 2); mean wall against 89.5 s (EXP-061) and 89.2 s (EXP-062).
- **Errors.** `err` per task: a traceback, a sandbox execution error, a compaction error, the no-submit label.
- **Compaction.** Count, and the largest single-request prompt against 14,336.
- **Recorded only.** Resolves, the draft the applier kept, the applier's edit failures (EXP-061: 6 of 12).

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

First match governs.

| # | outcome | reading |
|---|---|---|
| 1 | **Infrastructure.** Any of: an `err` with a traceback, a sandbox execution error or a compaction error; the tree does not run on some task; the root fails to transfer to `pipeline` in its first invocation; a drafter request fails to build from the new report | A bug, not a reading. Name the task and the step. |
| 2 | **Harm.** Any of: a time, call or turn cap hit; **3 or more empty patches of 8** (above the base maximum of 2); **mean wall over 150 s** | The longer report costs more than it buys. Name the tasks. **Why 150 s:** the base means are 89.5 s and 89.2 s, and the base single-task maxima are already 165.1 s (EXP-061 requests_7205) and 169.6 s (EXP-062 httpx_3672), so a mean of 150 s means every task runs about 60 s longer, about twice what 2 to 3 extra reads and 2,000 more output tokens should cost. The threshold is on the mean so that one tail task cannot fire it. A task over 240 s is named but is not itself a row. |
| 3 | **Not exercised.** The reader lists fewer than 2 locations (L < 2) on 5 or more of the 8 tasks | The reader does not produce diverse locations. **No decision, not "diversity does not help"** and not a kill of the idea. Record L per task. Whether to try the stronger forcing (a required minimum of 3 in the prompt, or a separate localizer stage per location) is the lead's call. |
| 4 | **Kept (diverse drafts).** Rows 1 to 3 did not fire, and **at least 5 of 8 tasks have F >= 2**, and **G = 8 of 8** (every task has a draft on a gold file, which includes fastapi_14448, fastapi_14605 and fastapi_14301 as against references of 6 to 7 of 8) | The drafts differ by place and reach the gold file more often than the references. This is a process reading on the drafts, not on the patch and not on resolves. It promotes the arm to a dev-48 pair (section 5). |
| 5 | **Dropped.** Rows 1 to 3 did not fire, and **F >= 2 on 2 or fewer tasks**, and R >= 2 on fewer than 5 tasks | The reader's several locations are the same place, or the drafters ignore their location. Not above the EXP-061 reference of 0 tasks with F >= 2 by more than 2 tasks. D-008's rank-2 kill rule applies. |
| 6 | **No decision.** Anything else, including F >= 2 on 3 or 4 tasks, F >= 2 on 5 or more tasks with G below 8 of 8, or diversity only by region inside one file | Record F, R and G per task. The resolves are recorded and decide nothing. |

**Not rows, but binding:**
- Per-task resolves at n = 8 are never an endpoint; six of eight must flip the same way for p < 0.05.
- The two movable tasks (`fastapi_14448`, `rich_3468`) are reported by themselves in section 9 whatever row fires, with their draft targets, because the other six cannot change the gold-file count by more than the references already show.
- A reader that gives no report on a task (as EXP-062 fastapi_14301) is counted as L = 0 and F = 0 on that task and is not a harm row unless it ends empty.
- If no prompt reaches 14,336 tokens, the compaction effect of the longer report is recorded as untested.

**Blind prediction.**
- L >= 2 on at least 5 of 8 tasks: probability about 0.6. The E4B reader tends to stop after one or two reads, and the prompt allows a single location.
- Row 3: about 0.3. Row 6: about 0.35. Row 4: about 0.1. Row 5: about 0.1. Row 2: about 0.1. Row 1: about 0.05.
- Mean wall about 110 s (range 95 to 135), mean F about 1.6 over the 8 tasks. When the reader lists 2 or 3 places, drafters 4 and 5 fall back to location 1 and duplicate drafter 1.

## 5. What this does and does not license

**The screen can decide one of two things.**
- **Kill:** row 5, or row 3 with the lead's agreement that the reader cannot be made to list places without a different stage, closes D-008 rank 2 for this form of the prompt.
- **Promote:** row 4 only. The promoted arm is a **dev-48 pair**, the EXP-062 tree against this tree (no pipeline dev-48 exists to my knowledge, so a base arm is needed), with the endpoints F and G on the 48 ids (gold files from the task metadata), the gold-file landing of the applied patch, and the harm row's wall and empty-patch counts. Resolves recorded, not an endpoint. About 2 x 3.6 GPU-h wall, the lead's budget call. Under 4 tasks of 58, no LB draw can see it (plan.md section 5.5).

**Does not license:** any resolve or LB claim, any upload or dev-48 run without the user, a statement about the applier, or a claim that more locations make a better fix.

## 6. Exact commands

```
python tools/validate_submission.py experiments/EXP-064/candidate-loc --official --strict --json
python tools/pack_submission.py --src experiments/EXP-064/candidate-loc --out experiments/EXP-064/exp064_loc.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed experiments/EXP-064/exp064_loc.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-064-loc"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp064_loc/kaggle_eval_l4x4.ipynb
```

The kernel push is released by the lead and is not run in this job. Analysis, a separate job, after `kaggle kernels status` says COMPLETE:
1. Download with `kaggle kernels output rainm4/gemma4-exp064-loc -p runs/EXP-064-loc/`, then flatten.
2. Run `python -I -X utf8 tools/analyze_traces.py runs/EXP-064-loc --cap-minutes 8 --max-calls 45`.
3. Run `python -I -X utf8 tools/run_forensics.py forensics runs/EXP-064-loc`.
4. Count L, F, R and G per task from `official/traces/` as in section 3.

## 7. Defects in this pre-registration, logged after the fact

1. **(Known at pre-registration.)** The reference counts of section 1 were read from traces with `grep` (no script is allowed to this agent), so "distinct edits" per task is not counted exactly; only the FILE lines and the reader's LINES are. Near-copy counts are by reading.
2. **(Known at pre-registration.)** The gold-file table lists a gold patch's non-test files. fastapi_14605 and httpx_3672 have 7 files each, so G on those tasks is lenient; the first-gold-file convention is recorded beside it for that reason.
3. **(Known at pre-registration.)** The tree was built by `cp -r` plus replaced files, not by a hash-verifying tool; the `diff -ru` is the check.

## 8. Built (below the line; nothing above changes)

---

- **Changed files vs EXP-062 `candidate-r`:** `prompts/reader.md`, `prompts/drafter_1.md` to `prompts/drafter_5.md`, `sub_agents/reader.yaml` (one comment line). No CR byte in the tree.
- **Validator** (`--official --strict`): 1 error, the 18.00 h gate, which `--skip-budget-gate` demotes to a warning. 2 warnings, both carried by EXP-061 and EXP-062: the applier's `submit_patch` and `timeout_seconds` 240. The official validator could not be imported.
- **Pack:** `RESULT: VALID (0 errors, 3 warnings)`, PACK OK, 20 files. **sha256 `3b9aea1592178bbbd131c8ac5c0fa10ddfdd8fdbd567a629b346688b0c25ea5e`.**

- **Pre-registration commit:** 380685e. `git ls-files --eol` on the candidate tree: all 20 blobs `i/lf`, worktree `w/lf`, so a repack from the committed blobs is byte-identical to the worktree. A repack to `out/exp064_repack.zip` gives the same sha `3b9aea15...25ea5e`.
- **Notebook:** `notebooks/exp064_loc/`, built with the section 6 command. Against `notebooks/exp062_r/` the notebook differs only in `EXP_ID` and `SUBMISSION_B64`. `kernel-metadata.json` is EXP-062's with only `id` and `title` changed, to `rainm4/gemma4-exp064-loc`. Nothing was copied to `out/submission.zip`.
- **Kernel id for the push:** `rainm4/gemma4-exp064-loc`, directory `notebooks/exp064_loc`.

## Status

2026-11-09: pre-registered (380685e), candidate packed and the sha reproduced, notebook built and committed (dfa1d47). **Pushed 2026-11-09 on the lead's release**: kernel version 1, `rainm4/gemma4-exp064-loc`, first status QUEUED. Kernel COMPLETE, downloaded to `runs/EXP-064-loc/`, analyzed, section 9 written. **Row 3 fired (not exercised): the reader listed fewer than 2 locations on 6 of 8 tasks. No decision.** Measured 0.353 GPU-h (kernel wall 1270.2 s, last log entry). Next: the lead's call (stronger forcing of several locations, or the fused round with EXP-063's selector).

---

## 9. Results, 2026-11-09. Section 4's readings applied as written.

Source: `runs/EXP-064-loc/` (flattened with `cp -r`), `analyze_traces.py --cap-minutes 8 --max-calls 45`, `run_forensics.py forensics`, then greps over `traces/` for L, F, R and G (no script is allowed to this agent). `summary.jsonl` is copied to `experiments/EXP-064/loc/summary.jsonl`.

**Cost.** Kernel wall 1270.2 s (last entry of the kernel log) = **0.353 GPU-h**. All 8 tasks ran; `err` is empty on 8 of 8.

### 9.1 Section 3 endpoints, per task

Drafts d1 to d5 are listed by drafter number. A draft's target is read from its FILE line; R is counted from the drafters' assigned locations (a fallback to location 1 repeats that location), not from the OLD blocks, which were not read.

| task | L (END present on all) | locations (file, lines) | d1 d2 d3 d4 d5 target file | F | R | G any | G first-gold | resolved | wall s | calls | patch files |
|---|---|---|---|---|---|---|---|---|---|---|---|
| requests_7309 | 1 | `src/requests/utils.py` 502-518 | same file x5 | 1 | 1 | yes | yes | no | 53.7 | 4 | utils.py |
| requests_7205 | 1 | `src/requests/utils.py` 233-237 | same file x5 | 1 | 1 | yes | yes | no | 64.6 | 5 | utils.py |
| fastapi_14448 | 1 | `fastapi/routing.py` 80-100 | same file x5 | 1 | 1 | **no** | no | no | 71.5 | 7 | routing.py |
| fastapi_14301 | 1 | `fastapi/dependencies/utils.py` 131-133 | same file x5 | 1 | 1 | yes | yes | **yes** | 66.6 | 7 | dependencies/utils.py |
| httpx_3672 | 4 | `src/httpx/_server.py` 99-101; `src/httpx/_parsers.py` 447-473; `_server.py` 37-46; `_parsers.py` 300-350 | _server, _parsers, _server, _parsers, _server (d5 fell back to location 1) | **2** | **4** | yes (`_parsers.py`) | no | no | 115.9 | 16 | `_parsers.py` and `_server.py` |
| fastapi_14605 | 2 | `fastapi/utils.py` 1-10; `fastapi/temp_pydantic_v1_params.py` 36-41 | utils, temp_pydantic, utils, utils, utils (d3 to d5 fell back to location 1) | **2** | **2** | yes (both are gold files) | no | no | 156.0 | 15 | `fastapi/utils.py` only |
| rich_3468 | 1 | `rich/console.py` 1627-1710 | same file x5 | 1 | 1 | yes | yes | no | 208.6 | 19 | none (empty) |
| rich_3006 | 1 | `rich/repr.py` 67-70 | same file x5 | 1 | 1 | yes | yes | **yes** | 63.0 | 6 | repr.py |

Aggregates against the references (EXP-061, EXP-062, EXP-052):
- **L.** L >= 2 on 2 of 8 tasks (fastapi_14605, httpx_3672); L = 1 on 6; no task without a report. The prompt allowed up to 5.
- **F.** Mean 1.25 (10 distinct target files over 8 tasks); F >= 2 on 2 of 8 (httpx_3672, fastapi_14605). The references' F was not recomputed here.
- **R.** Mean 1.5; R >= 2 on 2 of 8.
- **G, any gold file.** 7 of 8 (the miss is fastapi_14448). References 6, 7, 7. **G, first gold file.** 5 of 8 (references 5, 5, 5). So G is at the reference level.
- **Duplicates.** Not read.
- **Harm.** Time, call or turn cap hits 0. Empty patches 1 of 8 (rich_3468; base maximum 2). Mean wall 100.0 s (sum 799.9 s; references 89.5 s and 89.2 s), longest 208.6 s (rich_3468, under 240 s). Edit failures 15 (fastapi_14605 8, rich_3468 6, requests_7205 1) of 79 tool calls (19.0 percent) and of 25 edit_file calls.
- **Errors.** `err` empty on 8 of 8. `transfer_to_agent` called once on each task.
- **Compaction.** 2 in-flow compactions (fastapi_14605 and rich_3468), neither raising an error. Largest single prompt 22,124 tokens (rich_3468) against 14,336; fastapi_14605 peaked at 15,204. The effect of the longer report on compaction is therefore tested, and its cost is the two tasks with the most edit failures.

### 9.2 Row that fired

- Row 1: no. `err` is empty on 8 of 8, no traceback, the root transferred on 8 of 8, every drafter built its request.
- Row 2: no. Caps 0, empty patches 1 (below 3), mean wall 100.0 s (below 150 s).
- **Row 3: fired.** L < 2 on 6 of 8 tasks (requirement: 5 or more). Reading as written: the reader does not produce diverse locations. **No decision, not "diversity does not help"**, and not a kill of the idea. Whether to try the stronger forcing (a required minimum of 3 in the prompt, or a separate localizer stage per location) is the lead's call.
- Rows 4 to 6 are not reached (first match governs). For the record, row 4 (kept) did not match anyway: F >= 2 on 2 of 8 tasks (needs 5) and G is 7 of 8, not 8 of 8. Its reading, "promotes the arm to a dev-48 pair", would also have needed the user's word before any dev-48 run, and the lead's next step on a keep would be the fused round with EXP-063's selector; neither is in play. F >= 2 on 2 of 8 is inside row 5's count, but row 3 fires first, so "dropped" is not the reading.

On the two tasks where the reader listed several locations, the drafters did follow their locations: httpx_3672 drafts split 3 and 2 across the two files, fastapi_14605 had d2 on its location 2 and d3 to d5 fell back to location 1. The applier's kept patch on httpx_3672 touches both files (edits from drafts in both locations reached the patch); on fastapi_14605 it tried the location-2 file and 8 edit calls failed, leaving only `fastapi/utils.py` in the patch.

### 9.3 Movable tasks, reported on their own

- **fastapi_14448.** L = 1, `fastapi/routing.py` lines 80-100 (not a gold file; the gold files are `dependencies/models.py` and `utils.py`). All 5 drafts on that file, so no draft on a gold file and no change against the references. Patch `fastapi/routing.py`, not resolved, 7 calls, 71.5 s.
- **rich_3468.** L = 1, `rich/console.py` (a gold file) lines 1627-1710. The reference regions were not compared. All 5 drafts on that file and region. The applier made 6 edit calls, all failed, and the task ended with an empty patch after 19 calls, 208.6 s, one compaction and a largest prompt of 22,124 tokens. Not resolved.

### 9.4 Resolves, recorded and not an endpoint

2 of 8 (fastapi_14301, rich_3006). EXP-061 and EXP-062 had 1 of 8 each (rich_3006); EXP-052 had 2 of 8, the same two. n = 8, six of eight must flip the same way, and 14301 alone flipped against EXP-061 and EXP-062.
- **fastapi_14301** (resolved here and in EXP-052, not in EXP-061 or EXP-062): the reader gave one location, the gold file's lines 131-133, all 5 drafts on it, the patch on it. The kept draft did not move on this task, since there was one location.- **rich_3006** (resolved in all four runs): one location in the gold file, 5 drafts on it, patch on that file. The kept-draft number was not read, and with one location it cannot have moved to another place.

### 9.5 Text-form tool calls, EXP-065's definition (recorded, not a row)

Tasks with at least 1 text-form call: 0 of 8. Tool-free tasks: 0 of 8 (every trace carries native `tool_calls`). No agent made one.
### 9.6 Prediction check

- L >= 2 on at least 5 of 8 (predicted about 0.6): did not hold, 2 of 8.
- Row 3 (about 0.3): fired. Row 2 (about 0.1) and row 1 (about 0.05): did not fire.
- Mean wall about 110 s (95 to 135): held, 100.0 s. Mean F about 1.6: did not hold, 1.25.

### 9.7 Defects found in the reading

1. F and R come from FILE lines and the drafters' assigned locations only. The OLD blocks were not read, so R counts a draft that fell back to location 1 as sharing d1's location, and "followed its location" means the FILE line matches. Duplicates were not counted.
2. G counts any non-test gold file, which is lenient on fastapi_14605 and httpx_3672 (7 files each); the first-gold-file column is the strict reading and sits at 5 of 8 like the references.
3. The tool-call count in `summary.jsonl` counts `transfer_to_agent` once per task; the 8 reported above are the per-task `n_calls` field, which excludes it.

---

## 10. Lead-requested follow-up count, 2026-11-09. Changes no reading; row 3 stands.

Question: why did row 3 fire (L < 2 on 6 of 8), and which of section 5's two stronger forms (a required minimum of 3 locations in the prompt, or a separate localizer stage) does the cause point to. Zero GPU. Method: greps over `runs/EXP-064-loc/traces/` for each trace's reader tool calls (function name, `filepath` and `command` arguments, author) and line-number reads of the reader's result lines. No script was run, no text is copied here, and only ids, counts, paths and error kinds are written. "Named" means a file appears in a search result or in a command argument; "opened" means a `read_file` call. A reader step is a trace step authored by the reader; each reader has 2 steps beyond its tool calls (the report steps).

### 10.1 Per task: what the reader saw before it listed locations

| task | reader calls (run_command / read_file) | reader steps | files opened | files named by searches or command arguments | seen (union) | L | gold file among seen | group |
|---|---|---|---|---|---|---|---|---|
| requests_7309 | 2 (1 / 1) | 4 | 1 (`src/requests/utils.py`) | 1 (same) | 1 | 1 | yes | (i) |
| requests_7205 | 2 (1 / 1) | 4 | 1 (`src/requests/utils.py`) | 2 (`sessions.py`, `utils.py`) | 2 | 1 | yes | (ii) |
| fastapi_14448 | 5 (4 / 1) | 7 | 1 (`fastapi/routing.py`) | 1 (same) | 1 | 1 | **no** | (i) |
| fastapi_14301 | 5 (3 / 2, both reads of one file) | 7 | 1 (`fastapi/dependencies/utils.py`) | 1 (same) | 1 | 1 | yes | (i) |
| rich_3468 | 10 (4 / 6) | 12 | 2 (`rich/console.py` 5 reads, `rich/logging.py` 1) | 1 (`rich/console.py`, by command argument) | 2 | 1 | yes | (ii) |
| rich_3006 | 4 (3 / 1) | 6 | 1 (`rich/repr.py`) | 0 | 1 | 1 | yes | (i) |
| httpx_3672 | 11 (4 / 7) | 13 | 2 (`_parsers.py` 6 reads, `_server.py` 1) | 4 (`__init__.py`, `_parsers.py`, `_pool.py`, `_server.py`) | 4 | 4 | yes | L >= 2 |
| fastapi_14605 | 4 (1 / 3) | 6 | 3 (`fastapi/exceptions.py`, `temp_pydantic_v1_params.py`, `utils.py`) | 0 | 3 | 2 | yes | L >= 2 |

Gold file among the seen files is read against the gold list in section 1: fastapi_14448 lists `dependencies/models.py` and `dependencies/utils.py`, and the reader saw only `routing.py`; every other task has a gold file in its seen set.

### 10.2 The split of the 6 tasks with L < 2

- **Group (i), the reader saw one candidate file only: 4 of 6** (requests_7309, fastapi_14448, fastapi_14301, rich_3006). A second location was only possible as another region of the same file, and in fastapi_14448 the one file seen is not a gold file.
- **Group (ii), it saw several files and listed one: 2 of 6** (requests_7205, rich_3468). requests_7205: the second file was named by 4 hit lines of one search result and was never opened (the section 2 rule requires a location to have been opened). rich_3468: the second file was opened (one read) and the reader still listed only `rich/console.py`, a file it read 5 times.

### 10.3 A search failure recorded in the same traces

7 of the 21 reader `run_command` calls (7 of the 16 on the six L < 2 tasks) ended in the same error kind: a `head` invocation with the count detached from its flag, which `head` rejects as a missing file. They fall on fastapi_14448 (3 of its 4 searches), fastapi_14301 (2 of 3), rich_3468 (1 of 4) and rich_3006 (1 of 3). None fell on a task with L >= 2. In fastapi_14448 2 of the 3 failed searches named one function and the third was aimed at `fastapi/dependencies/` (where both gold files live); the only search that ran returned one hit, in `fastapi/routing.py`. In fastapi_14605 the one search ran against a directory path that returned nothing (exit 1, empty), and the reader listed 2 locations from 3 file reads without any search result. This is a defect of the reader's searching, not of the prompt wording, and it is a candidate reason the reader saw one file on 3 of the 4 group (i) tasks (fastapi_14448, fastapi_14301 and rich_3006 each had searches fail; requests_7309 had a single search that ran and a single file named). Whether the searches would have found a second file was not tested.

### 10.4 Reader budget before its report

| task | reader calls | reader `read_file` calls (prompt limit 8) | reader share of the task's tool calls | reader steps |
|---|---|---|---|---|
| requests_7309 | 2 | 1 | 2 of 4 | 4 |
| requests_7205 | 2 | 1 | 2 of 5 | 4 |
| fastapi_14448 | 5 | 1 | 5 of 7 | 7 |
| fastapi_14301 | 5 | 2 | 5 of 7 | 7 |
| rich_3468 | 10 | 6 | 10 of 19 | 12 |
| rich_3006 | 4 | 1 | 4 of 6 | 6 |
| httpx_3672 | 11 | 7 | 11 of 16 | 13 |
| fastapi_14605 | 4 | 3 | 4 of 15 | 6 |

No reader reached its stated `read_file` limit of 8 (most reads 7, httpx_3672). The task-wide caps (`max_tool_calls` 45, `max_turns` 120) were never near: the reader used 2 to 11 calls. Reader calls total 43 of the 79 task calls. The reader stopped early on the L < 2 tasks and was not budget-bound: the four tasks with 2 to 5 calls (requests_7309, requests_7205, fastapi_14448, fastapi_14301) stopped with unused read allowance of 7, 7, 7 and 6.

### 10.5 rich_3468, the 6 failed `edit_file` calls

All 6 applier `edit_file` calls on `rich/console.py` returned the same error kind, `FileEditError` with "old_string not found". None lost its arguments (the arg-loss marker count is 0 for the task, as `summary.jsonl` has it). So 6 of 6 are the old-string-not-in-file kind and 0 of 6 are lost-argument. The applier made 2 `read_file` calls on the file between attempts (after the second and the fifth failure) and the patch stayed empty. Whether the old strings differ from the file by whitespace or by content was not compared; the harness error does not say which.

### 10.6 What the count bears on (not a reading)

- Of the 6 tasks, 4 had one candidate file in view, so a prompt-level minimum of 3 locations would ask the reader for locations it had not seen; on 3 of those 4 its searches had mostly failed. A minimum can be met by padding with other regions of the same file (the section 2 rule requires an opened file).
- Only 2 of 6 (requests_7205, rich_3468) had a second file in view; in one of those two it had not been opened.
- A separate localizer stage with its own searches would address the shortage of candidates, but the search defect in 10.3 appears in this reader's own searches and would need its own guard, for example a shorter command form in the prompt.
- n = 6 and the counts are descriptive. The choice between the two forms is the lead's.

Limits: the count of files named reads only each search's first-seen output (results capped by the reader's own `head` or a single-file search); the in-file searches in rich_3468 name their file only through the command argument; fastapi_14605 and httpx_3672 were counted but not part of the split.

---

## 11. LB draw, recorded only, 2026-11-10.

The EXP-064 tree was uploaded as S-016 (zip `3b9aea15`, ref 58178151) and came back COMPLETE with a public score of **0.01**. S-014 and S-015 scored 0.05 (3 of 58 each).

- Kaggle shows the score to 2 decimals, so 0.01 means k = 0 or k = 1 of 58 resolved; the displayed value does not fix k. The delta against S-015 (k = 3) is therefore 2 tasks down (k = 1) or 3 tasks down (k = 0).
- Both are under the measured MDE of about 4 tasks (plan.md section 5.5), so no effect is read. This is one draw of 58 and it is not an endpoint of EXP-064, whose own readings (section 4, row 3 fired) are unchanged.
- S-016's tree is the EXP-064 tree (EXP-062's root plus the location prompts, section 2); S-015's is the EXP-061 tree. The smoke-8 record is the source for what the location prompts do; this draw adds none.

---
