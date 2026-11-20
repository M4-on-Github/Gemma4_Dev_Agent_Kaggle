# EXP-085 — Per-file readers feeding an orchestrator on the 31B v24-at-8 tree, smoke-8 on 8 wrong-file and wrong-region tasks: does the root call the readers within budget, and does its patch reach the gold file and regions more often?

**Date:** 2026-11-20
**Type:** smoke-8 screen, ~0.8 L4x4-h of the 30/week (dispatch figure; EXP-028's dev-48 kernels ran 4.09 to 4.12 h for 48 tasks plus a 342 to 397 s vLLM start, so 8 tasks at 8 minutes is the same order). No upload.
**Cohort:** reader-31b-8 (`experiments/cohorts/reader-31b-8.txt`: fastapi_14512, fastapi_14583, rich_3935, fastapi_14962, fastapi_15030, fastapi_15800, fastapi_5624, rich_3468; a subset of dev-48, not smoke-8)
**Ladder:** L0 desk check (section 1b), then L2. Runs on the user's word: "alright now I want to experiment on kaggle where there is read agents first where the we spawn one agent per file to analyse and note abt the file, then an agent that takes that and then ochestrates on the fix." (`knowledge/user-decisions.md`, 2026-11-20), with one smoke-8 per model.
**Pre-registered:** this file is committed before the build and the kernel push. Sections 3 and 4 are written blind and are not revised.
**Serves:** the user's reader-then-orchestrator request of 2026-11-20; the 31B fault map `research/lit/2026-11-17-run-synthesis-model-faults.md` (wrong file F and wrong region R are the two stages before a partial fix).
**Relates:** EXP-086 (the same architecture on the E4B), EXP-027 (the tree), EXP-028 (arms R and RH, the baselines), EXP-032 section 9 (P1 localizers, 21 of 24 branches overspent a prompt-only limit, editor guaranteed calls 0 in 7 of 8), EXP-046 section 2.2 (only the model ends a stage that holds a tool), EXP-049 (the shared counters), EXP-064 section 10.4 (reader call table), EXP-080 section 6.1 (the per-task stage table), C-014 (same-model delegation costs time without adding capability; hypothesis), D-005 F2.

**What was already seen when these rules were written.** This list is complete.
- The per-task stage table of EXP-080 section 6.1 (arm R stage and the four E4B draws), which is the cohort source. The 31B arm RH classes were not on disk locally and were not seen; the EXP-082 counts exist for class C runs only.
- The prompt `experiments/EXP-027/candidate-v24-at-8/prompts/system.md` in full, `submission/sub_agents/analyzer.yaml` (an unused agent_tool pattern), the validator source for the `agent_tool` key shape and checks.
- The harness facts as recorded in `.claude/skills/harness-stack` and EXP-046, EXP-049, EXP-064, EXP-032. The harness source and `runs/` are not in this checkout; nothing was read from them.
- Not seen: any run of an `agent_tool` sub-agent (none exists), any trace of this tree, the baselines' file-hit values per task other than through the EXP-080 table.

## 1. Why this, now
- The user asked for one reader agent per candidate file, writing notes, and an orchestrator that takes the notes and plans the fix. The 31B's early faults are F (wrong file) and R (right file, wrong region), the two stages before a partial fix (EXP-080 section 6.1 lists them per task). The reader gives each candidate file one focused read before the root commits to a file.
- Two earlier failures bound the design and are what the screen reads:
  - **C-014, same-model delegation costs time without adding capability.** The reader here has its own sampling file with `thinking_budget` 512 and `max_output_tokens` 1536, so a reader model call is time-bounded; the count of its calls is not (below).
  - **EXP-032 P1, a prompt-only call limit was overspent in 21 of 24 branches and starved the editor.** All agents of a task share one tool counter and one turn counter (`context.py:139-140`, EXP-049), so any reader call is a call the root does not have. The config offers no per-agent cap (EXP-046 2.2). The reader is therefore limited by prompt to one `read_file` call (a second only if the function runs past the window), and the screen has a row for the case where this fails (row 3).

## 1b. Desk check (L0, zero GPU), answers
Source: the cited EXP files and the skills; the harness source is not in this checkout. [V] verified in a cited run or source line, [I] inferred, [U] unknown.

| # | question | answer |
|---|---|---|
| D1 | Does the harness accept `agent_tool` in the root's tools? | **Yes by documentation** [V in the HARNESS_README shape, never run by us]. The official sample ships it, and the key shape `{agent_tool: {config_path, skip_summarization}}` is in the validator (`AGENT_TOOL_KEYS`). |
| D2 | Do the validator and the packer pass it? | **Yes.** `python tools/validate_submission.py experiments/EXP-085/candidate-reader --strict` reads 2 agents (file_reader, swe_agent), 7 files, 0 warnings other than the known `timeout_seconds=240` one, and 1 error, the packing gate (18.00 h), which the screen overrides with `--skip-budget-gate`. No warning about the root instruction naming `file_reader`. `--official` could not run (`adk_submission` not importable here). |
| D3 | Has any of our kernels run `agent_tool`? | **No.** EXP-049 records "No run on record"; EXP-003b and E9 were planned and never run. This screen is the first. |
| D4 | How do reader calls count? | One tool counter and one turn counter per task, one clock, one `/workspace` [V]. Counted calls are `read_file`, `run_command`, `edit_file`, `write_file`; `get_status` and `submit_patch` are free. The inner Runner inherits the parent's plugins, so reader tool calls pass the same budget check and reader model events count as turns [I]. Whether the `agent_tool` call itself counts is [U]. The screen measures it (`unaccounted` in `screen_read.py`). `max_turns` is 80 and baseline turns are about 25 to 35, so 6 to 9 reader turns do not threaten it. |
| D5 | Where do the notes land, and how big can the reader's prompt get? | The notes are the `file_reader` function response, an event in the root's history; the root's compaction (at 14,336 prompt tokens) may summarize them later, so notes are kept to about 300 words and the root re-reads the exact region before every `edit_file`. The reader runs in a fresh session with no compaction (the inner Runner has no App, `agent_tool.py:241-249`): instruction about 400 tokens, request about 100, each `read_file` result up to 150 lines or 10,000 characters (about 3k tokens), so 1 to 2 reads fit under 10k and 8 reads could approach the 32k window. Not a blocker at the prompted 1 to 2 reads. |
| D6 | Budget arithmetic at 28 calls and 8 minutes (31B) | Locate 1 to 2 calls. Readers for 3 files: case A, limit held, 1 read each, 3 calls; case B, mild overspend (EXP-064's reader used 2 to 11, mean about 5.5, with `run_command` too), 6 to 9 calls; case C, EXP-032-like, up to 15. The fix needs about 4 to 7 calls (1 to 2 re-reads, 1 to 3 edits, 1 check; submit is free). Calls left for the fix: A about 23 (20 if the `agent_tool` call counts), B about 19 (16), C about 11 (8). The expected cases A and B stay at or above the dispatch's stop line of 15; only C breaches it. **No blocker, so the arm was built.** The risk is the wall: EXP-032 P1 with 3 localizers cost +72.9 s per task against a 28.8 s allowance, so row 4's time test may fire on the 31B. |

**Caveats on the desk check.** The `skip_summarization` behaviour is from memory of the ADK source and unverified here: `true` is believed to make the tool response the final response and end the root's turn, so the key is left out (default false). The baseline's own pre-edit reads (median first edit at call 6 if resolved, 12 if unresolved with a patch) are comparable to the reader overhead, so the "edit by call 12" rule was moved to 16.

## 2. Design

**One variable:** the architecture "root orchestrates per-file reader notes", with the prompt changes it needs. Nothing else differs from `experiments/EXP-027/candidate-v24-at-8/`: `eval_config.yaml` unchanged (`timeout_seconds: 240`, `max_tool_calls: 28`, `max_time_minutes: 8`, `max_turns: 80`), `configs/sampling.yaml` unchanged (temperature 1.0, thinking budget 4096).

**The steps the prompt asks for.**
1. Locate: one `git grep`, then at most 3 candidate source files chosen from the hits.
2. Read: the root calls `file_reader` once per candidate file, one at a time, passing in `request` the path, the hit line numbers and one sentence of the need. Never twice for a file, never after the first edit.
3. Fix: the root decides from the notes, re-opens the exact region with `read_file` before `edit_file`, edits, runs one check, submits. "Edit by tool call 12" becomes "by tool call 16 (reader calls count)".

**The reader** (`sub_agents/file_reader.yaml`, `prompts/file_reader.md`, `configs/reader_sampling.yaml`): same model, tools `read_file` only, a `description` (the tool description the root sees), instruction asking for one `read_file` (a second only if the function runs past the window, never a third) and a fixed note form under 300 words: FILE, PURPOSE, RELEVANT (up to 3 functions with line ranges and the 3 to 8 key lines copied with their line numbers), CHANGE (yes or no, where, why). Sampling: temperature 0.2, top_p 0.95, top_k 64, `max_output_tokens` 1536, `thinking_budget` 512, `include_thoughts` false. These bound tokens per reader call. **They do not bound the number of reader calls**; that rests on the prompt (the EXP-032 failure), and row 3 and the budget lines read it.

**Candidate tree and diff.** `experiments/EXP-085/candidate-reader/`, built by writing the base files and the new ones (the screener's shell has no `mkdir`/`cp -r` path here). `diff -ru experiments/EXP-027/candidate-v24-at-8 experiments/EXP-085/candidate-reader`, recorded in full below:
- `agent.yaml`: +1 dated comment line; +2 lines in `tools`: `- agent_tool:` with `config_path: sub_agents/file_reader.yaml` (no `skip_summarization`).
- `prompts/system.md`: Budget +1 sentence ("Everything a reader does spends calls from these same 28 and the same clock."); section 2 retitled "Locate, then have each candidate file read for you" with 5 bullets (grep once; choose at most 3 files; call `file_reader` once per file with path, hit lines and need; notes content; decide from the notes) replacing 4; section 3 retitled "Edit by tool call 16", a new first bullet (re-open the exact region with `read_file`, at most 120 lines, notes can be wrong by a character) and "12th" and "12 calls" become "16th (reader calls count)" and "16 calls".
- New files: `prompts/file_reader.md`, `sub_agents/file_reader.yaml`, `configs/reader_sampling.yaml`.
- Instruction chars (both agents) 5,152 against 3,162 for the base. Lint-clean (no repository names, no network or install words; strict validator as D2).

**Pack.** `python tools/pack_submission.py --src experiments/EXP-085/candidate-reader --out dist/EXP-085-reader.zip --skip-budget-gate`. **Gate override, stated:** the 8-minute cap fails the packing formula by design (120 x (8 + 1.0) min = 18.00 h against 11.0 h), exactly as EXP-027 records for the baseline. The endpoint for time is the projection from measured walls (section 3), which must be 11 h or less. This is a smoke screen, not an upload. Zip sha256 in section 8.

**Notebook.** `tools/build_notebook.py --embed dist/EXP-085-reader.zip --username rainm4 --cohort experiments/cohorts/reader-31b-8.txt --set EXP_ID='"EXP-085-reader"' --set RUN_GOLD_CONTROL=False --out notebooks/exp085_reader/kaggle_eval_l4x4.ipynb`; `kernel-metadata.json` copied from `notebooks/exp083_sweep/` (a working 31B arm), changing only `id` (`rainm4/gemma4-exp085-reader`) and `title`.

**Cohort selection rule (declared before the runs).** Pool: the 48 ids of dev-48. For each id take the stage letters of arm R (EXP-080 section 6.1 table, column "arm R"; the 31B has one draw on disk with a letter, the arm RH letters were not available). Keep ids whose arm R letter is F or R (the empty-patch, partial and full classes are out). Rank by letter F first, then R, then id ascending, and take the first 8: F gives fastapi_14512, fastapi_14583, rich_3935; R gives (of nine R ids) fastapi_14962, fastapi_15030, fastapi_15800, fastapi_5624, rich_3468; rich_3934 is the one cut. Grading-gap ids (EXP-036 `g`: fastapi_14512, fastapi_14583, fastapi_14962, fastapi_15030) are kept: the primary is a gold file hit, which grading does not touch; their resolves are not read.
**Regression to the mean:** the cohort is chosen on baseline faults, so the baseline file-hit and region values here are biased low, and a rise is partly expected with no change. The comparison supports the screen's bar only, not an effect size.

**Comparison.** The same 8 ids in the existing EXP-028 arms R and RH (`runs/EXP-028-armR`, `runs/EXP-028-armRH`). No new baseline arm. Both are single draws at temperature 1.0. Arm R is this tree's own baseline; arm RH is arm R plus a recovery section, a different prompt, kept as a second draw.
**Reading script:** `experiments/EXP-085/screen_read.py` (also used by EXP-086), written before any run and untested. The screener cannot run it (the shell guard allows only `tools/` scripts); an agent with `runs/` and an allowlist that admits `python -I -X utf8 experiments/EXP-085/screen_read.py` must. A defect found when it first runs is logged in section 7, not fixed silently.

## 3. Endpoints, fixed in advance

Definitions: class letters from `diag.classify` with margin 5 (EXP-074 2.3): E empty patch, F no gold source file in the patch, R a gold file but no gold region within 5 lines, C some regions touched, S every region touched and the change wrong. **Gold file hit** = class not E and not F. **Region touched** = class C, S, or resolved.

- **Primary: gold file hit per task.** Count of the 8 tasks whose patch contains a gold source file, in the arm against the mean count over the two baseline arms on the same ids; plus per task the arm's 0 or 1 against the task's baseline share, read as above, below, equal. **Ceiling note:** in arm R 5 of these 8 ids are class R, so already hit the file; the 31B primary can rise on only the 3 F ids of arm R (fastapi_14512, fastapi_14583, rich_3935) unless arm RH was F on others. That is why row 5's promotion bar for the 31B rests on regions as well.
- **Then: gold regions touched.** Tasks at class C, S or resolved, in the arm against arm R (0 of 8 by selection) and arm RH.
- **Then: resolves.** Recorded, never an endpoint (the ladder's bar is 6 of 8 flipping the same way).
- **Guards, from `summary.jsonl` and the traces:**
  - **file_reader calls per task**, and the counter accounting: `n_calls` against the root-visible counted calls (reader gap = `unaccounted`), so we learn whether reader calls reach the counter and whether the `agent_tool` call itself counts. Mean `n_calls` and the orchestrator's calls left after the readers (28 minus the readers' share).
  - **Starved tasks:** empty patch, a call or time cap hit, and at least one reader call.
  - tasks at a call or time cap; empty patches; mean turns (limit 80); wall per task.
  - **Projected worst case** `10.04 h + 120 x (arm mean wall - baseline mean wall on these ids) / 3600`, must be **11.0 h or less** (a mean-wall rise of at most 28.8 s per task); the delta is paired on the same ids.
- **Statistic and power.** No test is computed. 6 of 8 strictly above a baseline gives a no-effect probability of about 0.145 for a fair 3-vs-5 chance split; the bars in row 5 buy a dev-48 look, not evidence.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Rows are read in order; the first that fires governs. Inputs are printed by `screen_read.py`.

| # | outcome | reading |
|---|---|---|
| 1 | **Infrastructure.** Fewer than 8 rows in `task_results.jsonl`, or the run's model is not the 31B, or the embedded zip's sha256 differs from section 8, or 2 or more of the 8 rows are infrastructure errors (`llm_calls` 0 or `n_turns` 0, or an `error` that is neither a cap string beginning `Agent exceeded session timeout` or `Agent exceeded turns budget` nor `Agent completed execution without calling submit_patch.`), or an `agent_tool` call fails to run (a tool error, not a model error) in 4 or more tasks, or the kernel did not finish | **Not readable.** Say which (model load, vLLM boot, harness, `agent_tool` unsupported or mis-shaped, Kaggle stop) from the log. A re-push is the lead's call. |
| 2 | **Not used.** `file_reader` called in 1 or fewer of the 8 tasks | **The 31B does not call the reader at this wording**: the knob is not enforced. The primary is not read. The wording is killed; the idea is not. No dev-48. |
| 3 | **Starved.** 3 or more of the 8 tasks are starved (empty patch, a cap hit, readers used) | **Uninformative, not a kill.** The readers used up the calls or time; the architecture's value is not read. Record the reader call counts and the unaccounted gap. A budget-bounded variant (a tighter one-read form, or one file) is a new claim and the lead's call. |
| 4 | **Limit breached.** The projected worst case exceeds 11.0 h, or tasks at a call or time cap in the arm exceed the baseline mean by 3 or more (of 8), or mean file_reader calls per task exceed 3 | **The architecture costs the budget the tree runs inside**, whatever the primary reads. Killed for this tree as written. Record the primary beside it. |
| 5 | **Promote.** At least 4 of the 8 tasks touch a gold region (class C, S or resolved), and the gold file hit count is 5 or more of 8, and no row above fired | **Promote.** Next rung: one dev-48 arm on this tree (needs the user's word), paired with arm R, endpoint in section 5. This is a reason to spend the arm, not evidence of an effect. |
| 6 | **Falls.** Gold file hit count 3 or fewer of 8, with the readers used in 6 or more tasks | **Kill.** The orchestrator with readers reaches the gold file less often than the two baselines on tasks chosen for file faults. |
| 7 | **Flat or mixed.** Anything else | **Not promoted.** Killed at L2 as written, with the file-hit and region counts, the reader calls and the guards recorded for the lead. |

**Not rows, but binding:**
- Resolves are reported and never an endpoint.
- The cohort is selected on baseline faults; every direction is read against regression to the mean.
- Row 5's count of 4 regions touched is against an arm R baseline of 0 of 8 by selection and an unseen arm RH; the script prints RH.
- The result is also the first measurement of `agent_tool` on this harness, whatever the row: the counter accounting, reader call counts and any tool error are reported to the lead.

**Blind predictions (not readings).** `file_reader` used in 7 or 8 of 8 (the 31B follows tool instructions). Reader calls 3 to 8 per task in total (1 to 2 reads per file, 2 to 3 files). Gold file hit 5 to 7 of 8 (baseline about 5). Regions touched 1 to 3 of 8. Wall: a rise of 25 to 50 s per task, so the projection sits near 11 h. Probabilities: row 4 about 0.45 (the time test), row 7 about 0.3, row 3 about 0.1, row 5 about 0.08, row 2 about 0.03, row 6 about 0.02, row 1 about 0.02. Resolves 1 to 3 of 8.

## 5. What this does and does not license

**Can decide (the screen's two outcomes):**
- **Kill** the reader-orchestrator architecture for the 31B at this wording (rows 2, 4, 6, 7), or leave it **uninformative** for budget starvation (row 3).
- **Promote** it to one dev-48 arm (row 5), on this tree, paired with EXP-028 arm R. The endpoint it should carry: the share of tasks whose patch contains a gold source file and the share touching at least one gold region, over the whole dev-48 and over the F and R tasks of arm R separately, with the projected worst case from measured walls at 11 h or less and the orchestrator's calls left after the readers as a guard. Resolves reported, not an endpoint.

**Does not license:** an upload, a resolve claim, a claim about any task outside these 8, or a conclusion that the readers are the cause of any change.

## 6. Exact commands

```bash
python tools/pack_submission.py --src experiments/EXP-085/candidate-reader --out dist/EXP-085-reader.zip --skip-budget-gate
python tools/build_notebook.py --embed dist/EXP-085-reader.zip --username rainm4 --cohort experiments/cohorts/reader-31b-8.txt --set EXP_ID='"EXP-085-reader"' --set RUN_GOLD_CONTROL=False --out notebooks/exp085_reader/kaggle_eval_l4x4.ipynb
kaggle kernels output rainm4/gemma4-exp085-reader -p runs/EXP-085-reader
python -I -X utf8 tools/analyze_traces.py runs/EXP-085-reader --cap-minutes 8 --max-calls 28
python -I -X utf8 experiments/EXP-085/screen_read.py --cohort experiments/cohorts/reader-31b-8.txt --arm EXP-085-reader --base EXP-028-armR --base EXP-028-armRH --proj-base-h 10.04
python -I -X utf8 tools/run_forensics.py forensics runs/EXP-085-reader
```
If the download nests the run, move the inner directory up one level first.

## 7. Defects in this pre-registration, logged after the fact
1. **`screen_read.py` counter accounting is 0 by construction** (found 2026-11-20 at its first run, after the results).
   - **The defect.** `trace_counts` treats every `source: "agent"` step and tool call as the root's. The trace also carries the reader's inner steps and calls, which are marked `extra.author == "file_reader"`. So the "counted calls visible in the root trace" include the reader's inner `read_file` calls, and `unaccounted` (n_calls minus root-visible minus reader calls) is 0 on every task, whatever the counter does.
   - **A second gap.** `n_calls` in `summary.jsonl` is analyze_traces' trace count, not the harness counter (`tool_calls` in `task_results.jsonl`). On EXP-085 fastapi_14962 the trace count is 43 against a harness count of 27. That task made no reader call, hit the 80-turn budget, and carries 4 budget-refusal observations.
   - **No reading changes.** The inputs to rows 1 to 7 do not use these two counts:
     - `file_reader` calls are counted by function name, on calls the root makes;
     - starved, empty patch, the caps and the primary come from `summary.jsonl` and the patches, as for the baselines.
     - The analyze_traces `calls_cap_hit` uses the trace count, the same way on arm and baselines. Row 4's cap test needs 3 or more above a baseline mean of 4.00, and the arm has 4 cap tasks under either count.
   - **The fix.** `screen_read.py` is left unchanged. The accounting is measured instead by a new script, `experiments/EXP-085/counter_check.py`, written after the runs. Per task, it compares the harness counter with the trace calls split by `extra.author`. Its output is in section 9.
2. **Row 1's clause "an `agent_tool` call fails to run"** is not computed by `screen_read.py`. `counter_check.py` flags `file_reader` responses that begin as an error envelope, and finds 0 in this arm.

## 8. Built and pushed (below the line; nothing above changes)

---

- **Pre-registration commit:** 8eaa438 (this file at sections 1 to 7, the candidate tree, the cohort file, `screen_read.py`, the README row), made before the build.
- **Zip:** `dist/EXP-085-reader.zip`, sha256 `623f32f1790cd7bccaf8bc10b368ff85dac0d49823efd954c6efa053efb859c9`, 7 members: `agent.yaml`, `configs/reader_sampling.yaml`, `configs/sampling.yaml`, `eval_config.yaml`, `prompts/file_reader.md`, `prompts/system.md`, `sub_agents/file_reader.yaml`. The packer's closure followed the `agent_tool` `config_path` into the reader file and its includes. Pack result VALID with 2 warnings (the gate, demoted, and `timeout_seconds=240 < 300`). The worktree blobs are LF.
- **Notebook:** `notebooks/exp085_reader/kaggle_eval_l4x4.ipynb`, built with the section 6 command; `TASK_IDS` equals the 8 ids of `experiments/cohorts/reader-31b-8.txt`, `N_TASKS = 8`, `EXP_ID = "EXP-085-reader"`, `RUN_AGENT = True`, `RUN_GOLD_CONTROL = False`. Notebook sha256 `8a96e4c098ecc7e9235b87359e4cd19e60be6d6933374cdd29ae5a9581b88362`.
- **Kernel metadata:** `notebooks/exp083_sweep/kernel-metadata.json` (a working 31B arm) with `id` `rainm4/gemma4-exp085-reader` and `title` `gemma4-exp085-reader`, nothing else changed. The builder printed `kernel-metadata.json id -> rainm4/gemma4-eval-l4x4` but wrote no metadata file in the output directory; the file was written by hand from the arm named.
- **Kernels live at push time:** `rainm4/gemma4-exp083-sweep` and `rainm4/gemma4-exp084-sweep` both read `KernelWorkerStatus.COMPLETE` before this push, so 0 live before and 2 live after EXP-085 and EXP-086.

### Push record
- **Pushed** with `kaggle kernels push -p notebooks/exp085_reader` (bare, after the build commit a49ba50), no guard block. CLI output: `Kernel version 1 successfully pushed.  Please check progress at https://www.kaggle.com/code/rainm4/gemma4-exp085-reader`.
- **Kernel:** `rainm4/gemma4-exp085-reader`, version 1. Pushed first; EXP-086 pushed right after, so two kernels live.
- **Push time:** 2026-11-20 (the shell has no `date` under the guard; the time is not recorded more finely).
- **First status reading:** `KernelWorkerStatus.RUNNING`.

### Download and analysis record (2026-11-20, experimenter)
- **Status:** `kaggle kernels status rainm4/gemma4-exp085-reader` read `KernelWorkerStatus.COMPLETE` (one check).
- **Download:** `kaggle kernels output rainm4/gemma4-exp085-reader -p runs/EXP-085-reader`. The bundle nested as `runs/EXP-085-reader/runs/EXP-085-reader/`, and its contents were moved up one level. A copy `runs/EXP-085-reader/runs/EXP-085-reader.zip` stays, as in the baseline downloads.
- **Kernel wall-clock for the GPU ledger: 0.838 h.** That is 3018.3 s, the last log entry of `gemma4-exp085-reader.log`.
  - vLLM came up in 357.9 s (tp=4, gpus=4).
  - The served model is `gemma-4-31b-it-qat-w4a16-ct`.
- **Embedded zip.** The `SUBMISSION_B64` zip in the committed notebook has sha256 `623f32f1790cd7bccaf8bc10b368ff85dac0d49823efd954c6efa053efb859c9`, which is section 8's. The extracted `runs/EXP-085-reader/agent/` is identical to `experiments/EXP-085/candidate-reader/` (`diff -r` empty).
- **Baselines.** `runs/EXP-028-armR` and `runs/EXP-028-armRH` were re-downloaded on 2026-11-20 for EXP-083. Both MATCH their committed summaries (`experiments/EXP-083/check_baselines.py`; EXP-083 section 9).
- **`analyze_traces.py --cap-minutes 8 --max-calls 28`** results are copied to `experiments/EXP-085/reader/summary.jsonl`:
  - resolved 1/8 (Wilson 95% 2-47%);
  - empty patch 0.0%, time-cap 0.0%, calls-cap 50.0%, overflow 0.0%, submit_patch 100.0%;
  - malformed turns 0.3%, spin 48.4%, edit failures 7.5%;
  - wall median 5.14 min, p90 6.46 min;
  - nudges 1, compactions 10;
  - text-form calls 0, tool-free tasks 0;
  - projected hidden-run total 10.54 h (its own formula).
  - Two tasks ended on `Agent exceeded turns budget (80 turns)`: fastapi_14962 and rich_3468. This is a cap string, not infrastructure.
- **`run_forensics.py forensics`:**
  - total agent wall 41.6 min;
  - `run_command` 42.1% of the wall, `read_file` 31.2%;
  - `file_reader` 8 calls at 0.7%. The reader's inner time is filed under `read_file` and `<no-tool>`.
  - 0 of 8 tasks never edited.

## Status

**READ (2026-11-20).** Kernel `rainm4/gemma4-exp085-reader` v1 is COMPLETE, with 0.838 h of kernel wall. `screen_read.py` ran as written; its counter line is defective (section 7) and no reading uses it. **Row 7 governs.** Gold file hit is 5 of 8 against 5.00 (0 above, 0 below, 8 equal), and 2 of 8 tasks touch a region. The reader-orchestrator is not promoted and is killed at L2 for the 31B. No dev-48. Projected 9.35 h. The agent_tool call is not counted against the 28 and the reader inner calls are (section 9.5). See section 9.

## 9. Results, 2026-11-20. Section 4's readings applied as written.

`python -I -X utf8 experiments/EXP-085/screen_read.py --cohort experiments/cohorts/reader-31b-8.txt --arm EXP-085-reader --base EXP-028-armR --base EXP-028-armRH --proj-base-h 10.04` ran as written without error. Its counter-accounting line is defective (section 7 item 1); no reading uses it.

### 9.1 The rows, in order
- **Row 1, infrastructure: does not fire.**
  - 8 of 8 rows;
  - model is the 31B; zip sha matches; kernel finished;
  - 0 infrastructure rows. The two turn-budget endings are cap strings.
  - `file_reader` error responses: 0 tasks (`counter_check.py`).
- **Row 2, not used: does not fire.** `file_reader` was called in 5 of 8 tasks.
- **Row 3, starved: does not fire.** 0 of 8 tasks are starved; no patch is empty.
- **Row 4, limit breached: does not fire.**
  - Projected worst case 10.04 + 120 x (-20.7 s) / 3600 = **9.35 h**, against 11.0 h. The mean wall is 316.2 s against 336.9 s.
  - Tasks at a call or time cap: arm 4, against R 5 and RH 3 (mean 4.00).
  - Mean `file_reader` calls per task: **1.00**, against a limit of 3.
- **Row 5, promote: does not fire.** Regions touched: 2 of 8, below the bar of 4.
- **Row 6, falls: does not fire.** Gold file hit: 5 of 8, above 3.
- **Row 7, flat or mixed: FIRES and governs.**

**Verdict: row 7. Not promoted; the reader-orchestrator architecture is killed at L2 for the 31B as written.** No dev-48.

### 9.2 Primary: gold file hit
- Arm **5 of 8**, against R 5 and RH 5 (mean 5.00); the difference is +0.00.
- Per task: 0 above, 0 below, 8 equal.
- **The arm's class letters match arm R's file outcome on every id:**
  - the three F ids of arm R (fastapi_14512, fastapi_14583, rich_3935) stay F in the arm, although each got 1 or 2 reader calls;
  - the five R ids stay at a gold file.

| Task | Arm class | Resolved | Calls (trace) | Turns | Wall s | Caps (calls, time) | file_reader calls | Baseline file-hit share | Baseline region share |
|---|---|---|---|---|---|---|---|---|---|
| fastapi_14512 | F | 0 | 23 | 25 | 299.8 | (0,0) | 2 | 0.00 | 0.00 |
| fastapi_14583 | F | 0 | 26 | 27 | 446.6 | (0,0) | 2 | 0.00 | 0.00 |
| rich_3935 | F | 0 | 28 | 30 | 317.5 | (1,0) | 1 | 0.00 | 0.00 |
| fastapi_14962 | C | 0 | 43 | 80 | 387.5 | (1,0) | 0 | 1.00 | 0.50 |
| fastapi_15030 | R | 0 | 14 | 16 | 257.6 | (0,0) | 0 | 1.00 | 0.00 |
| fastapi_15800 | R | 0 | 20 | 23 | 204.2 | (0,0) | 0 | 1.00 | 0.00 |
| fastapi_5624 | S | 1 | 30 | 32 | 302.8 | (1,0) | 2 | 1.00 | 0.50 |
| rich_3468 | R | 0 | 29 | 79 | 313.8 | (1,0) | 1 | 1.00 | 0.50 |

**Then, regions touched (class C, S or resolved):** arm 2 (fastapi_14962, fastapi_5624); R 0; RH 3.

**Class letters:**
- arm: CFFFRRRS;
- R: FFFRRRRR;
- RH: CCFFFRRS.

### 9.3 Resolves (recorded, not an endpoint)
The arm resolves 1 of 8 (fastapi_5624), against R 0 and RH 1. fastapi_5624 is not one of the grading-gap ids (EXP-036 `g`: fastapi_14512, fastapi_14583, fastapi_14962, fastapi_15030).

### 9.4 Guards
- **Calls (analyze_traces trace count):** mean 26.62, against R 26.12 and RH 20.88.
- **Turns:** mean 39.00, against 27.88 and 31.12. Two tasks reached the 80-turn budget, fastapi_14962 and rich_3468, the second with one reader call.
- **Caps, starvation, call form:**
  - starved 0;
  - empty patches 0, as in both baselines;
  - text-form or tool-free tasks 0;
  - malformed calls 1.
- **Mean wall:** 316.2 s, against 336.9 s (delta -20.7 s); projection 9.35 h.
- **Kernel wall:** 0.838 h.

### 9.5 Observation 1: the `agent_tool` call and the 28-call cap
Source: `python -I -X utf8 experiments/EXP-085/counter_check.py runs/EXP-085-reader runs/EXP-086-reader`. It compares the harness counter (`tool_calls` in `task_results.jsonl`) with the trace calls split by `extra.author`. Counted calls exclude `get_status` and `submit_patch`.

**Result: the `agent_tool` call itself is not counted, and the reader's inner `read_file` calls are.**
- Over the 5 tasks with a reader call, the harness counter equals:
  - root calls plus reader inner calls in **5 of 5**;
  - root calls plus `agent_tool` calls plus inner calls in **0 of 5**.
- The one task where the two single additions differ is fastapi_14583 (2 `file_reader` calls, 3 inner reads; harness 24). There, only root plus inner matches.
- On the E4B (EXP-086 section 9.5) the same split holds in 4 of 6 reader tasks, and the version that counts the `agent_tool` call matches 0 of 6.
- **Consequence:** a reader call costs the shared 28 calls exactly its own `read_file` calls (here 1 to 3 per reader call). The delegation adds no charge.
- Turns are not settled. Reader model steps appear in the trace, and the harness `llm_calls` exceeds the root's model steps on the reader tasks. But step counts do not reproduce `llm_calls` even on reader-free E4B tasks.

**Per task (31B):**

| Task | Harness count | Root calls | `file_reader` calls | Reader inner calls | Matches |
|---|---|---|---|---|---|
| fastapi_14512 | 21 | 19 | 2 | 2 | root + agent_tool, root + inner |
| fastapi_5624 | 28 | 26 | 2 | 2 | root + agent_tool, root + inner |
| rich_3935 | 27 | 26 | 1 | 1 | root + agent_tool, root + inner |
| fastapi_14583 | 24 | 21 | 2 | 3 | root + inner |
| rich_3468 | 28 | 27 | 1 | 1 | root + agent_tool, root + inner |

### 9.6 Observation 2: reader calls per task
- **Totals:** 8 `file_reader` calls over 8 tasks, mean 1.00, in 5 of 8 tasks.
- **Per task:** 2, 2, 1, 0, 0, 0, 2, 1 (cohort order).
- **Inner reads per reader-using task:** 1 to 3.
- Whether a reader was called after the first edit or twice for one file is not measured; `screen_read.py` does not test it.
- **The three tasks with no reader call** (fastapi_14962, fastapi_15030, fastapi_15800) are all arm R class R ids, and they stayed at a gold file.
- **The prompt's 3-file ceiling held on every task** (at most 2 reader calls).

### 9.7 Blind predictions, against the outcome
- `file_reader` used in 7 or 8 of 8: **missed low**, 5.
- Reader calls 3 to 8 per task: **missed low**, mean 1.00 and at most 2.
- Gold file hit 5 to 7: **held**, 5.
- Regions touched 1 to 3: **held**, 2.
- Wall rise 25 to 50 s: **contradicted**, -20.7 s, so the projection is 9.35 h, not near 11 h.
- Row probabilities:
  - row 7 had about 0.3 and governed;
  - the favourite, row 4 at about 0.45 (the time test), did not fire.
- Resolves 1 to 3: **held**, 1.
