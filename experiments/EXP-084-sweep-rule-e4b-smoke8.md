# EXP-084 — Sibling-site sweep rule on the E4B single-loop tree, smoke-8 on 8 two-region tasks: does the prompt rule get run, and do more gold regions end up touched?

**Date:** 2026-11-17
**Type:** smoke-8 screen, ~0.8 L4x4-h of the 30/week (dispatch figure; probably well under, since EXP-077's 48-task E4B kernel ran 1.292 h including a 324 s vLLM start). No upload.
**Cohort:** sweep-e4b-8 (`experiments/cohorts/sweep-e4b-8.txt`: fastapi_9753, fastapi_13207, fastapi_14964, rich_3063, rich_3953, fastapi_14873, fastapi_15280, rich_3180; a subset of dev-48, not smoke-8)
**Ladder:** L2. The L1 check is EXP-082. This screen runs on the user's word, not on a GO: the user wrote "yup do the 8 task test on both gemma 3b and e4b" (`knowledge/user-decisions.md`, 357e64b; the lead reads "3b" as the 31B), so both smoke-8s run whatever EXP-082 reads. EXP-082 read, for the E4B: V0 7 of 38, V1 6, V2 5, **row 2, DROP** (GO needs 16, DROP is below 10): the rule can reach few of the missed regions of the E4B's partial fixes, and that file dropped the claim for the E4B at L1.
**Pre-registered:** this file is committed before the kernel push. Sections 3 and 4 are written blind and are not revised.
**Serves:** idea 1 of `research/lit/2026-11-17-next-ideas-web-scout.md`; D-011 (the user's decision of 2026-11-17 reopens it for this one arm); the E4B fault map in `research/lit/2026-11-17-run-synthesis-model-faults.md`.
**Relates:** EXP-082, EXP-083 (the same rule on the 31B), EXP-033 (the tree), EXP-038, EXP-077, EXP-075, EXP-078 (the four baseline draws), EXP-074 section 2.3, EXP-077 (draw-to-draw spread).

**What was already seen when these rules were written.** This list is complete.
- EXP-082's counts and per-task table (`experiments/EXP-082/counts.json`): which of these 8 ids were partial-fix or right-file task-runs in the four E4B draws and which were findable. That is how the cohort was chosen, so it is selected on partial-fix history in the baselines.
- The synthesis note's E4B counts (C 8, 12, 9, 9 per draw; 0 resolves of 84 task-runs at 3 or more gold regions; 5 of 36 at 2).
- The prompt `experiments/EXP-033/candidate-e4b/prompts/system.md`, identical to the 31B tree's.
- EXP-077 section 9's result that the draw-to-draw spread of the notfound share was above the bootstrap (row 3 there), which is why one draw per arm is a weak reference.
- Not seen: any run of this tree with this rule, any new-arm trace, and the baselines' per-task numbers on these 8 ids.

## 1. Why this, now
- Partial fixes are the E4B's second-largest loss class (C 8, 12, 9, 9 over the four draws). The rule asks the agent to list the implied change sites before the first edit and, after the last edit, to search the repo for the changed identifier and mark each hit "same change needed" or "not needed".
- EXP-082 says the opposite of a GO for this model: of 38 partial-fix runs only 7 had every missed region containing an identifier the agent changed. The user chose to run the screen anyway, so this file reads what the E4B does with the rule, not whether the sweep could reach the regions. The E4B resolves nothing at 3 or more gold regions (0 of 84 task-runs), so the cohort is the 2-region band (7 tasks) plus one 3-region task.
- What a smoke-8 can settle: whether the E4B runs the sweep at all (E4B instruction-following is the known weak point, with text-form calls and edit failures), whether it breaks a limit, and whether regions touched move. The E4B's known failure modes (empty patches, wrong file) lie upstream of anything the sweep touches, so a null is the expected result.

## 2. Design

**One variable:** the same sibling-site sweep rule, in `prompts/system.md` of the E4B tree. The inserted text is identical to EXP-083's (two lines; see that file section 2 and `experiments/EXP-084/candidate-sweep/prompts/system.md`). Nothing else differs from `experiments/EXP-033/candidate-e4b/` except one dated history comment line in `agent.yaml` (no value change; repo convention). `eval_config.yaml` unchanged (240 s, 28 calls, 8 min, 80 turns); `configs/sampling.yaml` unchanged (temperature 1.0, thinking budget 4096, as the EXP-038 and EXP-077 draws). Instruction chars 3,162 -> 3,705. The existing "Never ... broad exploration after the first edit" line is left as it was.

**Candidate tree and diff.** `experiments/EXP-084/candidate-sweep/`, copied from `experiments/EXP-033/candidate-e4b/`. `diff -ru` (baseline against candidate): `agent.yaml` +1 comment line; `prompts/system.md` +1 line in section 1 and +1 line in section 4; no other file differs.

**Pack.** `python tools/pack_submission.py --src experiments/EXP-084/candidate-sweep --out dist/EXP-084-sweep.zip --skip-budget-gate`. **Gate override, stated:** as for the EXP-038 base zip, which was packed with `--skip-budget-gate --allow-warnings` (the 8-minute cap fails the 11.0 h formula, 18.00 h); this is a screen, not an upload. Result: VALID with 2 warnings (the gate, demoted; `timeout_seconds=240 < 300`). Members `agent.yaml`, `configs/sampling.yaml`, `eval_config.yaml`, `prompts/system.md`; sha256 `6806d356b20f34d9621ac76fc503db8ecf44542a5aea6330bc73f3d4c46a2248`.

**Notebook.** Settings from `notebooks/exp077_base/` (the EXP-038 base tree at temperature 1.0 on the E4B; `exp078_t02r` embeds the EXP-075 tree, which changes temperature, so it was not used as the template): `tools/build_notebook.py --embed dist/EXP-084-sweep.zip --username rainm4 --cohort experiments/cohorts/sweep-e4b-8.txt --set EXP_ID='"EXP-084-sweep"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp084_sweep/kaggle_eval_l4x4.ipynb`; `kernel-metadata.json` copied from `notebooks/exp077_base/`, changing only `id` (`rainm4/gemma4-exp084-sweep`) and `title`. Model source `google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2`.

**Comparison.** The same 8 ids in the four existing E4B dev-48 draws: `runs/EXP-038-e4b-dev48`, `runs/EXP-077-base`, `runs/EXP-075-t02`, `runs/EXP-078-t02r`. No new baseline arm. The baseline per task is the mean over the four draws. Caution: the two t02 draws (EXP-075, EXP-078) are a tree that differs from this one in temperature (0.2 against 1.0). They are in the baseline because the dispatch named them, and they are partly different from this arm. `screen_read.py` prints the pooled mean only; the analysis job also reads the two temperature-1.0 draws (EXP-038, EXP-077) alone as a check and records both.

**Reading script:** `experiments/EXP-083/screen_read.py`, shared with EXP-083; written before any run, untested; a defect found on first use is logged in section 7.

## 3. Endpoints, fixed in advance

Definitions as EXP-083 section 3 and EXP-082: a gold region is a cluster of changed old-side lines of the gold source files merged at a gap of 10 or less (`diag.gold_regions`, margin 5); touched means one of the patch's changed old-side lines of the same file is within 5 lines; an empty patch touches 0.

- **Primary: gold regions touched per task.** The arm's value per task against the mean of the four draws on the same task: the number of tasks strictly above, strictly below and equal; also the means over the 8.
- **Then: resolves.** Arm of 8 against each draw. Recorded, not an endpoint.
- **Process, gating the primary: sweep uptake.** The number of the 8 tasks with a `run_command` containing `grep` after the first `edit_file` call, arm and each draw.
- **Guards:** calls per task (mean, arm against the draws); tasks at a call or time cap; tasks with a text-form call or `tool_free` (`n_text_form_calls`, `tool_free` of `summary.jsonl`) and malformed calls; empty patches; mean wall. The E4B has no 11 h gate (its 48-task kernel ran 1.292 h; EXP-038's worst case is 6.66 h), so there is no time projection row.
- **Statistic.** None computed. Under no effect, 6 or more of 8 strictly above has probability about 0.145 (one-sided, no ties): the promotion bar buys a dev-48 look, not evidence. The draws differ from one another considerably (EXP-077: spread above the bootstrap), so a per-task baseline mean of four draws is noisy.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Rows are read in order; the first that fires governs.

| # | outcome | reading |
|---|---|---|
| 1 | **Infrastructure.** Fewer than 8 rows, or the run's model is not the E4B, or the embedded zip's sha256 is not `6806d356...2248`, or 2 or more of the 8 rows are infrastructure errors (`llm_calls` 0 or `n_turns` 0, or an `error` that is neither a cap string (`Agent exceeded session timeout`, `Agent exceeded turns budget`) nor `Agent completed execution without calling submit_patch.`), or the kernel did not finish | **Not readable.** Say which from the log. A re-push is the lead's call. |
| 2 | **Not run.** Sweep uptake is 1 or fewer of the 8 tasks, and no baseline draw has an uptake within 2 tasks of 8 below it | **The E4B does not run the sweep at this wording**: the knob is not enforced. The primary is not read. Wording killed for the E4B; the idea is not. No dev-48. |
| 3 | **Limit breached.** Tasks at a call or time cap exceed the draws' mean by 3 or more (of 8), or tasks with a text-form call or `tool_free` exceed the draws' mean by 3 or more, or empty patches exceed the draws' mean by 3 or more | **The rule costs the E4B calls it does not have, or breaks its call form.** Killed for the E4B as written, whatever the primary reads; record the primary beside it. |
| 4 | **Touched rises.** 6 or more of the 8 tasks strictly above their baseline mean, and the arm mean at least 0.5 regions above the baseline mean | **Promote, against EXP-082's drop.** The process measure moves in the screen's near-deterministic sense even though the offline check said the rule reaches few missed regions. Next rung: one dev-48 arm on this tree (needs the user's word), with the endpoint in section 5. A reason to spend the arm, not evidence of an effect. |
| 5 | **Touched falls.** 6 or more of the 8 tasks strictly below their baseline mean | **Kill.** The rule lowers the regions touched on the tasks chosen to be partial fixes. |
| 6 | **Flat or mixed.** Anything else | **Not promoted.** Consistent with EXP-082's drop: the claim is killed for the E4B at L2 as a result, with uptake and guards recorded. |

**Not rows, but binding:**
- Resolves are never an endpoint.
- The cohort was chosen on baseline partial-fix history, so baselines on these ids are biased low for the touched count (regression to the mean); a rise in rows 4 to 6 is partly expected without any rule.
- EXP-082's drop is not overturned by any row here; row 4 would be recorded as a result that contradicts it, which is read at the dev-48 arm, not here.

**Blind predictions (not readings).** Uptake 2 to 5 of 8 (the E4B follows long instruction lists unevenly; its baseline post-edit grep rate is probably 1 to 3 of 8). Touched flat: above on 2 to 4, below on 2 to 4, so row 6 is the most likely (about 0.6); row 3 about 0.2 (extra calls on a model with a 28-call cap and known text-form turns); row 4 about 0.08; row 2 about 0.07; row 5 about 0.05. Resolves 0 to 2 of 8.

## 5. What this does and does not license

**Can decide:**
- **Kill** the sweep rule for the E4B at this wording (rows 2, 3, 5, 6), which matches EXP-082.
- **Promote** it to one dev-48 arm (row 4) on this tree, with the endpoint: gold regions touched per task over the 2-region tasks of dev-48, and the share of them whose final patch touches every gold region, against both temperature-1.0 base draws (EXP-038, EXP-077); two draws of the arm, because EXP-077 shows the draw-to-draw spread is wider than one draw can read. Guards: uptake, empties, text-form calls. Resolves reported, not an endpoint.

**Does not license:** an upload, a resolve claim, anything about the 31B, or any conclusion about causes (selected cohort, small n, baseline of four draws two of which are a different temperature).

## 6. Exact commands

```bash
python tools/pack_submission.py --src experiments/EXP-084/candidate-sweep --out dist/EXP-084-sweep.zip --skip-budget-gate
python tools/build_notebook.py --embed dist/EXP-084-sweep.zip --username rainm4 --cohort experiments/cohorts/sweep-e4b-8.txt --set EXP_ID='"EXP-084-sweep"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp084_sweep/kaggle_eval_l4x4.ipynb
kaggle kernels output rainm4/gemma4-exp084-sweep -p runs/EXP-084-sweep
python -I -X utf8 tools/analyze_traces.py runs/EXP-084-sweep --cap-minutes 8 --max-calls 28
python -I -X utf8 experiments/EXP-083/screen_read.py --cohort experiments/cohorts/sweep-e4b-8.txt --arm EXP-084-sweep --base EXP-038-e4b-dev48 --base EXP-077-base --base EXP-075-t02 --base EXP-078-t02r
python -I -X utf8 experiments/EXP-083/screen_read.py --cohort experiments/cohorts/sweep-e4b-8.txt --arm EXP-084-sweep --base EXP-038-e4b-dev48 --base EXP-077-base
python -I -X utf8 tools/run_forensics.py forensics runs/EXP-084-sweep
```
If the download nests the run, move the inner directory up one level first.

## 7. Defects in this pre-registration, logged after the fact
1. (2026-11-20, experimenter) **Row 2's second clause has two readings.** It says "and no baseline draw has an uptake within 2 tasks of 8 below it"; EXP-083's row 2 uses the same wording. It can be read as "no draw's uptake is 6 of 8 or more", or as "no draw's uptake is within 2 tasks of the arm's". The arm's uptake is 1 of 8, so the clause decides whether row 2 fires. The lead fixes which reading applies before it is applied. Either way it needs the baseline traces, which were not on disk on 2026-11-20.
2. (2026-11-20, lead ruling, recorded by the experimenter before any baseline uptake was computed) **Row 2's second clause takes the grammatical reading.** "No baseline draw has an uptake within 2 tasks of 8 below it" means no baseline draw has an uptake of 6 of 8 or more ("within 2 tasks of 8" is 8 minus 2). The ruling applies to EXP-083 and EXP-084 alike and is applied as given.

## 8. Built and pushed (below the line; nothing above changes)

---

- **Pre-registration commit:** af1c2a3 (this file at sections 1 to 7, the candidate tree, the cohort file and the shared `experiments/EXP-083/screen_read.py`), made before the build.
- **Zip:** `dist/EXP-084-sweep.zip`, sha256 `6806d356b20f34d9621ac76fc503db8ecf44542a5aea6330bc73f3d4c46a2248`, 4 members. The committed blobs of `experiments/EXP-084/candidate-sweep/` are LF in index and worktree (`i/lf w/lf`), so the pack reproduces from them.
- **Notebook:** `notebooks/exp084_sweep/kaggle_eval_l4x4.ipynb`, built with the section 6 command; `TASK_IDS` equals the 8 ids of `experiments/cohorts/sweep-e4b-8.txt`, `N_TASKS = 8`, `EXP_ID = "EXP-084-sweep"`, `MODEL_NAME` the E4B, `RUN_AGENT = True`, `RUN_GOLD_CONTROL = False`. Notebook sha256 `8861e87cd551b7ffc9a75b362f1ceb1620822a94b9b4e0240f6eadd4051e248d`.
- **Kernel metadata:** `notebooks/exp077_base/kernel-metadata.json` with `id` `rainm4/gemma4-exp084-sweep` and `title` `gemma4-exp084-sweep`, nothing else changed (`diff` shows the one line, id and title). Model source `google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2`.

### Push record
- **Pushed** with `kaggle kernels push -p notebooks/exp084_sweep` (bare, after the build commit 42e932e and after EXP-083's push), no guard block. CLI output: `Kernel version 1 successfully pushed.  Please check progress at https://www.kaggle.com/code/rainm4/gemma4-exp084-sweep`.
- **Kernel:** `rainm4/gemma4-exp084-sweep`, version 1.
- **Push time:** about 2026-11-18 03:54 UTC (2026-11-17 22:54 -0500; file stamp as in EXP-083 section 8).
- **First status reading:** `KernelWorkerStatus.QUEUED` (EXP-083's was RUNNING at the same check).

### Download and analysis record (2026-11-20, experimenter)
- **Status at download:** `kaggle kernels status rainm4/gemma4-exp084-sweep` read `KernelWorkerStatus.COMPLETE`.
- **Download:** `kaggle kernels output rainm4/gemma4-exp084-sweep -p runs/EXP-084-sweep`. This is the section 6 name; the dispatch said `runs/EXP-084`. The bundle nested, and its contents were moved up one level.
- **Kernel wall-clock for the GPU ledger: 0.307 h.** This is 1105 s, the last log entry of `gemma4-exp084-sweep.log`. vLLM came up in 324.4 s (tp=4, gpus=4), and the served model is `gemma-4-e4b-it-qat-w4a16-ct`.
- **Embedded zip:** the zip in the committed notebook has sha256 `6806d356b20f34d9621ac76fc503db8ecf44542a5aea6330bc73f3d4c46a2248`. All four extracted `agent/` files are byte-identical to the committed `experiments/EXP-084/candidate-sweep/` files.
- **`analyze_traces.py`:** `python -I -X utf8 tools/analyze_traces.py runs/EXP-084-sweep --cap-minutes 8 --max-calls 28`, copied to `experiments/EXP-084/sweep/summary.jsonl`. It reports:
  - resolved 1/8 (Wilson 95% 2-47%);
  - empty patch 25.0%; time-cap 0.0%, calls-cap 0.0%, overflow 0.0%; submit_patch 100.0%;
  - malformed turns 0.0%, spin 10.3%, edit failures 26.9%;
  - wall median 1.34 min, p90 1.68 min; nudges 0, compactions 3;
  - text-form calls 0, tool-free tasks 0.
- **`screen_read.py` was not run to completion.** Both section 6 commands fail at the first data read with `FileNotFoundError: ... data\raw\tasks.jsonl`. On 2026-11-20 the main checkout has no `data/`, `runs/` or `untrusted/` directory, so the four baseline draws' run directories and the gold patches are not on disk. This is missing input, not a script defect. The script is unchanged.
- **Provisional inputs** come from `python -I -X utf8 experiments/EXP-083/provisional_guards.py`. For the arm it uses `screen_read.uptake` unchanged. For the baselines it uses the committed `summary.jsonl` copies of EXP-038 (`e4b/`), EXP-077, EXP-075 and EXP-078.
  - **Row 1 does not fire.** The run has 8 rows and the model is the E4B. The zip sha256 matches. There are 0 infrastructure rows: `llm_calls` runs 8 to 17, `n_turns` 9 to 18, and no row has an error.
  - **Row 2 is not decidable on these inputs.**
    - The arm's uptake is **1 of 8** (rich_3953), which meets row 2's first clause, "1 or fewer".
    - The second clause concerns the baseline draws' uptake (section 7, item 1), and that needs the baseline traces, which are absent.
    - After its first `edit_file`, the arm made no `run_command` on fastapi_15280, rich_3063 and rich_3180. On fastapi_13207, fastapi_14873, fastapi_14964 and fastapi_9753 it ran one or two commands, none containing `grep`.
  - **Rows 3 onward are not read, because row 2 comes first.** Their guard inputs, for the record:
    - tasks at a call or time cap: arm 0; EXP-038 0, EXP-077 0, EXP-075 0, EXP-078 0;
    - text-form or `tool_free` tasks: arm 0; all draws 0;
    - malformed calls: arm 0; all draws 0;
    - empty patches: arm 2; EXP-038 2, EXP-077 2, EXP-075 2, EXP-078 1 (mean 1.75);
    - calls per task (mean): arm 9.75; EXP-038 10.88, EXP-077 8.88, EXP-075 11.12, EXP-078 9.12;
    - mean wall: arm 82.7 s against 89.7 s (mean of per-task means), delta -7.0 s.
  - **Resolves, recorded only:** arm 1 of 8 (fastapi_9753); EXP-038 0, EXP-077 0, EXP-075 1, EXP-078 0.

## Status

**READ (2026-11-20).** Kernel `rainm4/gemma4-exp084-sweep` v1 is COMPLETE, with a kernel wall of 0.307 h. The four baseline draws were re-downloaded and match their committed summaries, and both `screen_read.py` commands ran as written. **Row 2 governs:** uptake is 1 of 8, and no draw reaches 6 of 8 (section 7, item 2). The sweep wording is killed for the E4B, and the primary is not read. No dev-48. See section 9.

## 9. Results, 2026-11-20. Section 4's readings applied as written.

This section supersedes the provisional inputs recorded in section 8 under "Download and analysis record", including the line "Row 2 is not decidable on these inputs".

**How the inputs were restored and checked**
- The lead restored `data/raw/tasks.jsonl` from the competition files; its sha256 is `e4b3fd60...8ad6`.
- The experimenter re-downloaded the four baseline draws with `kaggle kernels output rainm4/gemma4-<slug> -p runs/<run>`:
  - `exp038-e4b-dev48` to `EXP-038-e4b-dev48`;
  - `exp075-t02` to `EXP-075-t02`;
  - `exp077-base` to `EXP-077-base`;
  - `exp078-t02r` to `EXP-078-t02r`.
- Each bundle was un-nested one level, then run through `analyze_traces.py --cap-minutes 8 --max-calls 28`, the command each EXP file records.
- `python -I -X utf8 experiments/EXP-083/check_baselines.py` checked each download against its committed summary (`experiments/EXP-038/e4b/`, `EXP-075/`, `EXP-077/`, `EXP-078/`). **All four MATCH:**
  - 48 of 48 ids each;
  - resolved 5, 6, 3 and 5, with 0 mismatches;
  - 0 wall, empty-patch or n_calls mismatches.
- **Section 7, item 2** (the lead's ruling on row 2) was recorded before any baseline uptake was counted.
- **Both section 6 `screen_read.py` commands ran as written without error,** so there is no script fix. One is pooled over the four draws; the other uses the two temperature-1.0 draws alone.

### 9.1 The rows, in order
- **Row 1, infrastructure: does not fire.** All 8 of 8 rows are present, with 0 infrastructure rows. The model is the E4B, the zip sha matches, and the kernel finished.
- **Row 2, not run: FIRES and governs.**
  - Uptake is **1 of 8** in the arm (rich_3953), so the first clause, 1 or fewer, holds.
  - Baseline uptake is 1 in EXP-038, 0 in EXP-077, 1 in EXP-075 and 1 in EXP-078.
  - Under the section 7 ruling, the second clause asks that no baseline draw reach 6 of 8 or more. None does, so the clause holds.

**Verdict: row 2. The E4B does not run the sweep at this wording, so the knob is not enforced.** The wording is killed for the E4B; the idea is not, and a different form would be a new claim. No dev-48. The primary is not read (row 2), and rows 3 to 6 are not read.

### 9.2 Primary, as printed (not read; row 2 governs)

| Task | Regions | Arm touched (class) | Baseline mean, 4 draws | Direction | Baseline mean, T 1.0 draws | Direction |
|---|---|---|---|---|---|---|
| fastapi_9753 | 2 | 2 (S, resolved) | 0.50 | + | 0.50 | + |
| fastapi_13207 | 2 | 0 (F) | 0.25 | - | 0.50 | - |
| fastapi_14964 | 2 | 2 (S) | 1.75 | + | 1.50 | + |
| rich_3063 | 2 | 0 (E) | 0.75 | - | 0.50 | - |
| rich_3953 | 2 | 1 (C) | 0.25 | + | 0.00 | + |
| fastapi_14873 | 2 | 0 (R) | 0.25 | - | 0.00 | = |
| fastapi_15280 | 2 | 0 (E) | 0.00 | = | 0.00 | = |
| rich_3180 | 3 | 1 (C) | 1.00 | = | 1.00 | = |

**Summary of the primary:**
- **Pooled over the four draws:** 3 tasks above, 3 below, 2 equal. Mean regions touched 0.750 in the arm against 0.594.
- **The two temperature-1.0 draws alone** (EXP-038, EXP-077): 3 above, 2 below, 3 equal. Mean 0.750 in the arm against 0.500.

**Tasks with every region touched** (class S or resolved): 2 in the arm; EXP-038 1, EXP-077 0, EXP-075 2, EXP-078 2.

### 9.3 Resolves (recorded, not an endpoint)
The arm resolves **1 of 8** (fastapi_9753). On the same ids the draws resolve 0 (EXP-038), 0 (EXP-077), 1 (EXP-075) and 0 (EXP-078).

### 9.4 Guards (recorded; row 3 is not read)
- **Calls per task (mean):** arm 9.75; draws 10.88, 8.88, 11.12 and 9.12.
- **Tasks at a call or time cap:** arm 0; every draw 0.
- **Text-form or tool-free tasks:** arm 0; every draw 0.
- **Malformed calls:** arm 0.
- **Empty patches:** arm 2; draws 2, 2, 2 and 1.
- **Mean wall:** arm 82.7 s.
  - Against the pooled draws (89.7 s mean of per-task means), the delta is -7.0 s.
  - Against the temperature-1.0 draws alone (96.7 s), it is -14.0 s.
- **Kernel wall:** 0.307 h (section 8).

### 9.5 Blind predictions, against the outcome
- **Uptake missed low.** The prediction was 2 to 5 of 8; the arm reached 1.
- **Baseline post-edit grep mostly held.** The prediction was 1 to 3 of 8; the draws came in at 1, 0, 1 and 1.
- **Row 2 governed,** where it had been given about 0.07. Row 6 had been the favourite, at about 0.6.
- **Resolves held.** The prediction was 0 to 2; the arm resolved 1.

### 9.6 Observations, not readings
- **The arm rarely ran a command after its first edit.** It made no `run_command` after the first `edit_file` on fastapi_15280, rich_3063 and rich_3180. On four other tasks it ran one or two, none of them a `grep`. This matches EXP-082's DROP for the E4B, though EXP-082 dropped the E4B for findability, not uptake.
