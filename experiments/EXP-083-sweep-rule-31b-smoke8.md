# EXP-083 — Sibling-site sweep rule on the 31B v24-at-8 tree, smoke-8 on 8 partial-fix tasks: does the prompt rule get run, and do more gold regions end up touched?

**Date:** 2026-11-17
**Type:** smoke-8 screen, ~0.8 L4x4-h of the 30/week (dispatch figure; EXP-028's dev-48 kernels ran 4.09 to 4.12 h for 48 tasks plus a 342 to 397 s vLLM start, so 8 tasks at 8 minutes is the same order). No upload.
**Cohort:** sweep-31b-8 (`experiments/cohorts/sweep-31b-8.txt`: rich_3953, fastapi_14448, rich_3468, rich_3480, fastapi_14953, fastapi_11355, rich_3063, rich_3934; a subset of dev-48, not smoke-8)
**Ladder:** L2. The L1 check is EXP-082. This screen runs on the user's word, not on a GO: the user wrote "yup do the 8 task test on both gemma 3b and e4b" (`knowledge/user-decisions.md`, 357e64b; the lead reads "3b" as the 31B), which amends the earlier "only if its check passes" to "both smoke-8s run whatever EXP-082 reads". EXP-082 read, for the 31B: V0 8 of 24, V1 8, V2 5, **row 4, between** (GO needs 10, DROP is below 6), no kernel licensed by that file.
**Pre-registered:** this file is committed before the kernel push. Sections 3 and 4 are written blind and are not revised.
**Serves:** idea 1 of `research/lit/2026-11-17-next-ideas-web-scout.md` (sibling-site sweep prompt rule); the 31B fault map `research/lit/2026-11-17-run-synthesis-model-faults.md` (partial fix C is the largest 31B loss class: 13 of 48 in arm R, 11 in RH).
**Relates:** EXP-082 (findability check), EXP-027 (the v24-at-8 tree), EXP-028 (arms R and RH, the baselines), EXP-084 (the same rule on the E4B), EXP-074 section 2.3 (`diag.classify`, margin 5).

**What was already seen when these rules were written.** This list is complete.
- EXP-082's counts and per-task table (`experiments/EXP-082/counts.json`, section 9 of its file): which of these 8 ids were partial-fix task-runs in arms R and RH and which were findable. That is how the cohort was chosen, so the cohort is selected on partial-fix history in the baselines.
- The synthesis note's baseline counts and the cap-bound figure (23 of 48), and the projected 10.04 h of the baseline (the web scout note quoting the synthesis).
- The prompt `experiments/EXP-027/candidate-v24-at-8/prompts/system.md` in full.
- Not seen: any run of this tree with this rule, any new-arm trace, and the baselines' per-task numbers on these 8 ids (`screen_read.py` prints them for the first time with the arm).

## 1. Why this, now
- Partial fixes are the 31B's largest loss class. The rule asks the agent to list the change sites the issue implies before the first edit, and after the last edit to search the repo for the identifier it changed and mark each hit "same change needed" or "not needed".
- EXP-082 found that of 24 partial-fix runs (R and RH) 8 had every missed region containing an identifier the agent itself changed (a grep-findable upper bound), 8 under V1 (so `self` and `cls` did not inflate it), 5 under V2. That is two below the GO line of 10. The user chose to run the screen anyway. The offline number says the rule can reach at most a third of the partial-fix runs, so a large effect is not expected.
- The question a smoke-8 can settle here is a process one: is the rule run at all (the near-deterministic kind of question the ladder assigns to L2), does it break a limit (the baseline is cap-bound on 23 of 48 at 28 calls and 8 minutes, and the projected worst case is 10.04 h against an 11 h gate, so extra calls and time are the cost), and do the gold regions touched move.

## 2. Design

**One variable:** the sibling-site sweep rule in `prompts/system.md` (the shipped prompt file of this tree; the dispatch named `swe_coder.md`, which is the name in `submission/`, not in this tree). Nothing else differs from `experiments/EXP-027/candidate-v24-at-8/` except one dated history comment line in `agent.yaml` (no value changes; repo convention, CLAUDE.md "config files carry their own history"). `eval_config.yaml` is unchanged: `timeout_seconds: 240`, `max_tool_calls: 28`, `max_time_minutes: 8`, `max_turns: 80`. `configs/sampling.yaml` unchanged (temperature 1.0, thinking budget 4096).

**The rule, as inserted (two anchored insertions, each matched once with the Edit tool):**
- Section 1, after the contract paragraph: "Then list, one line each, every place the issue implies must change: each function, branch, constant, or message that handles the behavior, not only the first one you find."
- Section 4, as the first bullet: "After your last edit and before the check, run one search for the identifier or literal you changed: `git grep -n "CHANGED_TOKEN" -- '*.py' | head -30`. For each hit outside the lines you edited, write "same change needed" or "not needed", then apply each "same change needed" with `edit_file`. Skip this search when `get_status` shows less than 90 seconds remaining."
- The prompt stays repo-agnostic and lint-clean (strict validator: 0 errors other than the packing gate below). The existing "Never ... spend calls on broad exploration after the first edit" line is left as it was; the sweep is one targeted search. This tension is part of what the screen reads (uptake, row 2).
- Instruction chars 3,162 -> 3,705.

**Candidate tree and diff.** `experiments/EXP-083/candidate-sweep/`, copied from `experiments/EXP-027/candidate-v24-at-8/`. `diff -ru` (baseline against candidate): `agent.yaml` +1 comment line; `prompts/system.md` +1 line in section 1 and +1 line in section 4; no other file differs. The inserted lines are in `experiments/EXP-083/candidate-sweep/prompts/system.md`.

**Pack.** `python tools/pack_submission.py --src experiments/EXP-083/candidate-sweep --out dist/EXP-083-sweep.zip --skip-budget-gate`. **Gate override, stated:** the 8-minute cap fails the packing formula by design (120 x (8 + 1.0) min = 18.00 h against 11.0 h), exactly as EXP-027 records for the baseline (its line 151). The endpoint for time is the projection from measured walls (section 3), which must be 11 h or less. This is a smoke screen, not an upload. Result: VALID with 2 warnings (the gate, demoted, and `timeout_seconds=240 < 300`, accepted in EXP-023). Members `agent.yaml`, `configs/sampling.yaml`, `eval_config.yaml`, `prompts/system.md`; sha256 `4005033fda1bfd19e52859dfa44a32f0b2af270f12609f09e5e5602be603a0f4`.

**Notebook.** `tools/build_notebook.py --embed dist/EXP-083-sweep.zip --username rainm4 --cohort experiments/cohorts/sweep-31b-8.txt --set EXP_ID='"EXP-083-sweep"' --set RUN_GOLD_CONTROL=False --out notebooks/exp083_sweep/kaggle_eval_l4x4.ipynb`; `kernel-metadata.json` copied from `notebooks/exp028_armR/` (the 31B arms), changing only `id` (`rainm4/gemma4-exp083-sweep`) and `title`.

**Comparison.** The same 8 ids in the existing EXP-028 arms R (`runs/EXP-028-armR`) and RH (`runs/EXP-028-armRH`). No new baseline arm. The baseline per task is the mean of the two arms. Arm R is this tree's own baseline (the EXP-027 tree); arm RH is arm R plus the recovery section of EXP-028 (`experiments/EXP-028/recovery-section.md`), so it is a different prompt, kept as a second draw as the dispatch asked. Both are single draws of a stochastic model (temperature 1.0), so a per-task baseline is itself noisy.
**Reading script:** `experiments/EXP-083/screen_read.py` (also used by EXP-084). Written before any run and untested; a defect found when it first runs is logged in section 7, not fixed silently.

## 3. Endpoints, fixed in advance

Definitions (the EXP-082 ones): a gold region is a cluster of changed old-side lines of the gold source files, merged when 10 or fewer apart (`diag.gold_regions`, margin 5); a patch touches a region when one of its changed old-side lines of the same file is within 5 lines (`diag.touches`). An empty patch touches 0.

- **Primary: gold regions touched per task.** For each of the 8 tasks, the arm's regions touched against the mean of the same task's R and RH values. Read as the number of tasks strictly above, strictly below and equal (ties count as neither). Also the mean over the 8 for the arm and for the baseline.
- **Then: resolves.** The arm's resolved count of 8 against R and RH on the same ids. Recorded, not an endpoint (n = 8; the ladder's bar is 6 of 8 flipping the same way).
- **Process, gating the primary: sweep uptake.** The number of the 8 tasks in which a `run_command` containing `grep` is issued after the first `edit_file` call, in the arm and in each baseline arm on the same ids (the baseline prompt tells the model to grep before the edit, so its post-edit grep rate is the reference).
- **Guards, each from `summary.jsonl`:** calls per task (mean, arm against R and RH); tasks at a call or time cap (`calls_cap_hit` or `time_cap_hit`), arm against the baseline mean of the two arms; empty patches; the projected worst case, `10.04 h + 120 x (arm mean wall - baseline mean wall on these ids) / 3600`, where 10.04 h is the baseline's projection and the delta is paired on the same ids, which must be **11.0 h or less** (equivalent to a mean-wall rise of at most 28.8 s per task).
- **Statistic and power.** No test is computed. Under no effect the chance of 6 or more of 8 tasks strictly above their baseline is about 0.145 (one-sided, no ties), so the promotion bar in row 4 buys a dev-48 look and is not evidence of an effect. Per-task baselines come from two draws of a stochastic model.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Rows are read in order; the first that fires governs. The inputs are printed by `screen_read.py`.

| # | outcome | reading |
|---|---|---|
| 1 | **Infrastructure.** Fewer than 8 rows in `task_results.jsonl`, or the run's model is not the 31B, or the embedded zip's sha256 is not `4005033f...a0f4`, or 2 or more of the 8 rows are infrastructure errors (`llm_calls` 0 or `n_turns` 0, or an `error` that is neither a cap string beginning `Agent exceeded session timeout` or `Agent exceeded turns budget` nor `Agent completed execution without calling submit_patch.`), or the kernel did not finish | **Not readable.** Say which (model load, vLLM boot, harness, Kaggle stop) from the log. A re-push is the lead's call. |
| 2 | **Not run.** Sweep uptake is 1 or fewer of the 8 tasks, and no baseline arm has an uptake rate within 2 tasks of 8 below it | **The rule is not followed by the 31B at this wording**: the knob is not enforced. The primary is not read. The wording is killed for the 31B; the idea is not (a different form is a new claim). No dev-48. |
| 3 | **Limit breached.** The projected worst case exceeds 11.0 h, or tasks at a call or time cap in the arm exceed the baseline mean by 3 or more (of 8) | **The rule costs the budget the tree runs inside**, whatever the primary reads. Killed for this tree as written. Record the primary beside it. A shorter form (list only, or sweep only) is a new claim. |
| 4 | **Touched rises.** 6 or more of the 8 tasks strictly above their baseline mean, and the arm mean at least 0.5 regions above the baseline mean | **Promote.** The process measure moves in the screen's near-deterministic sense. Next rung: one dev-48 arm on this tree (needs the user's word), paired with arm R, with the endpoint in section 5. This is a reason to spend the arm, not evidence of an effect. |
| 5 | **Touched falls.** 6 or more of the 8 tasks strictly below their baseline mean | **Kill.** The rule lowers the regions touched on the tasks chosen to be partial fixes. |
| 6 | **Flat or mixed.** Anything else (fewer than 6 of 8 in either direction) | **Not promoted.** An effect on the process measure smaller than a 6-of-8 move is not worth a 4 to 7 GPU-h dev-48 slot. The claim is killed for this tree at L2 as a result, with the uptake and the guards recorded for the lead. |

**Not rows, but binding:**
- Resolves are reported and never an endpoint. A rise in resolves with the touched count flat is not a promotion.
- The cohort was chosen from the baselines' partial-fix history, so the baseline values on these ids are biased low for the touched count (regression to the mean). Every direction in rows 4 to 6 is read against that: a rise is partly expected without any rule. The comparison therefore carries no claim about the size of an effect; it is the screen's bar only.
- The EXP-082 reading (between, 8 of 24) is not overturned by any row here.

**Blind predictions (not readings).** Uptake 5 to 8 of 8 (the 31B follows format rules; the existing prompt also greps before the edit, so baseline post-edit grep is probably 2 to 4 of 8). Touched: above on 3 or 4 of 8, below on 1 or 2, so row 6 is the most likely (about 0.5); row 4 about 0.15 (regression to the mean helps it); row 3 about 0.25 (the projection has 0.96 h of room, 28.8 s a task, and 1 to 2 extra calls at 8 to 15 s each plus a possible extra compaction come close); row 2 about 0.05; row 5 about 0.05. Resolves 2 to 4 of 8.

## 5. What this does and does not license

**Can decide (the screen's two outcomes):**
- **Kill** the sweep rule for the 31B at this wording (rows 2, 3, 5, 6).
- **Promote** it to one dev-48 arm (row 4), on this tree, paired with EXP-028 arm R. The endpoint it should carry: the share of the 31B's 2-to-3-gold-region tasks whose final patch touches every gold region (class S or resolved), and gold regions touched per task over those tasks, with the projected worst case from measured walls at 11 h or less. Resolves are reported, not an endpoint, unless the arm is powered for about 10 tasks.

**Does not license:** an upload, a resolve claim, a claim about any task outside these 8, a conclusion that the rule is the cause of any change (the 8 ids were selected on baseline partial fixes, and the baseline is two draws).

## 6. Exact commands

```bash
python tools/pack_submission.py --src experiments/EXP-083/candidate-sweep --out dist/EXP-083-sweep.zip --skip-budget-gate
python tools/build_notebook.py --embed dist/EXP-083-sweep.zip --username rainm4 --cohort experiments/cohorts/sweep-31b-8.txt --set EXP_ID='"EXP-083-sweep"' --set RUN_GOLD_CONTROL=False --out notebooks/exp083_sweep/kaggle_eval_l4x4.ipynb
kaggle kernels output rainm4/gemma4-exp083-sweep -p runs/EXP-083-sweep
python -I -X utf8 tools/analyze_traces.py runs/EXP-083-sweep --cap-minutes 8 --max-calls 28
python -I -X utf8 experiments/EXP-083/screen_read.py --cohort experiments/cohorts/sweep-31b-8.txt --arm EXP-083-sweep --base EXP-028-armR --base EXP-028-armRH --proj-base-h 10.04
python -I -X utf8 tools/run_forensics.py forensics runs/EXP-083-sweep
```
If the download nests the run, move the inner directory up one level first.

## 7. Defects in this pre-registration, logged after the fact
None yet.

## 8. Built and pushed (below the line; nothing above changes)

---

- **Pre-registration commit:** af1c2a3 (this file at sections 1 to 7, the candidate tree, the cohort file and `screen_read.py`), made before the build.
- **Zip:** `dist/EXP-083-sweep.zip`, sha256 `4005033fda1bfd19e52859dfa44a32f0b2af270f12609f09e5e5602be603a0f4`, 4 members. The committed blobs of `experiments/EXP-083/candidate-sweep/` are LF in index and worktree (`git ls-files --eol` shows `i/lf w/lf`), so the pack reproduces from them.
- **Notebook:** `notebooks/exp083_sweep/kaggle_eval_l4x4.ipynb`, built with the section 6 command; `TASK_IDS` equals the 8 ids of `experiments/cohorts/sweep-31b-8.txt`, `N_TASKS = 8`, `EXP_ID = "EXP-083-sweep"`, `RUN_AGENT = True`, `RUN_GOLD_CONTROL = False`. Notebook sha256 `edfea8c86e4fb3d505c55238fec318137677e959fa5de7961e3b146892f4010f`.
- **Kernel metadata:** `notebooks/exp028_armR/kernel-metadata.json` with `id` `rainm4/gemma4-exp083-sweep` and `title` `gemma4-exp083-sweep`, nothing else changed (`diff` shows those two lines only). The 31B model source is `google/gemma-4/other/gemma-4-31b-it-qat-w4a16-ct/2`.

## Status

BUILT, NOT PUSHED (2026-11-17). Next: push `notebooks/exp083_sweep`, record the kernel id, status and push time here.
