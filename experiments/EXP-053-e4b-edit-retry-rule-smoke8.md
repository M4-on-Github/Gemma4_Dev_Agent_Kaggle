# EXP-053 — E4B edit loop, round 1: one prompt bullet "after a failed `edit_file`, never resend the same `old_string`", on smoke-8

**Date:** 2026-11-08
**Type:** smoke-8 screen, one arm (`r`), about 0.25-0.33 L4x4-h expected (point 0.27, conditional worst case about 1.24 h, section 2.4). **Built, then pushed under the standing approval** of `knowledge/user-decisions.md` (2026-11-08 entry, df193f3): a smoke-8 round inside the 4.0 GPU-h day ceiling.
**Cohort:** smoke-8
**Ladder:** L2, after L1 (the base-set diagnosis of section 1, zero GPU). Round 1 of the E4B edit loop (`knowledge/lessons-e4b-loop.md`).
**Pre-registered:** this file, the tree, the zip's recorded sha and the notebook are committed before the push. Sections 3 to 5 are written blind and are not revised; results are appended as a new section.
**Serves:** the E4B small-model line (S-014 scored 3/58); C-024 (edit reliability).
**Relates:** EXP-043 (why E4B edits fail: 39 failed calls on 8 ids, 11 non-unique), EXP-044 (the exact-copy line, killed by its own control X0: a not-found line has a prior null), EXP-045 (round 0, row 5), EXP-033 and EXP-038 and EXP-052 (the base set), `submission/skills/edit-anchoring` (the 31B-era rule, never declared in an `agent.yaml`).
**Tags:** [V] verified in trace or by a check run here, [I] inference, [H] hand judgement (a hand count from tool order and step ids).

## 1. Why this, now: the base-set diagnosis (zero GPU, 32 task-runs)

**Base set** = the four E4B runs on the smoke-8 ids: EXP-033 (the single-loop v24 tree), EXP-038 (the same tree, its 8 smoke ids), EXP-052 (the draft fan-out tree, 7 usable), EXP-045 (the repro bullet). **fastapi_14301 and rich_3006 resolved in all 4 runs, 8 of 8 task-runs [V]** (the loop file says about 3 in 4; the summaries say all four). The other six tasks resolved in none of 24.

**Classes** (own letters; the first wrong step is the earliest one in tool order, a flag is a second one in the same run): **A** the edit or the only reads were in a file the gold patch does not change; **B** `edit_file` failing at one place (3 or more failed calls) or an empty patch from failures; **C** applied in a gold file, did not resolve; **D** (flag) no run after the last applied edit that executed; **E** stopped with no edit; **F** a final text announcing a call instead of calling it (the harness nudge fires); **G** a check showed the edited module failing and the run submitted anyway; **H** infrastructure.

| task (gold file set) | EXP-033 | EXP-038 | EXP-052 | EXP-045 |
|---|---|---|---|---|
| fastapi_14448 (`fastapi/dependencies/models.py`) | A@5 (edit in `fastapi/routing.py`) | A@7 (same file) | A@13 (models.py read at 4, edit in routing.py) | C@10 (models.py, check at 11 passed, did not resolve) |
| fastapi_14605 (4 files, `exceptions.py` first) | B@7 (4 failed of 9 edit calls: 7, 14, 15, 17), D | B@9 (steps 9 to 13 all failed, 5 in a row) | C@13 (one edit in `exceptions.py`), D | B@9 (steps 9 to 13 all failed, 5 in a row), D |
| httpx_3672 (`src/ahttpx/`, never `src/httpx/`) | A@3, E@4 (one read of `src/httpx/_server.py`, then `submit_patch` twice) | A@3, B@6 (steps 6 to 9 failed, 7 to 9 the same `old_string`; applied at 10), D | A@3, H (compaction error, no edit) | A@3, G@7 (module fails to import after the edit, submit at 8) |
| requests_7205 (`src/requests/utils.py`) | B@8 (steps 8 to 10 not found, same start, empty patch) | F@8, then C (final text at 8 says it submits, nudge at 9, call at 10) | C (quoted `filepath` lost at 11, applied 12), D | C@5, D |
| requests_7309 (`src/requests/utils.py`) | C@5, D | C@5, D | C, D | C@5 (repro attempt refused, 6 to 8) |
| rich_3468 (`rich/console.py`) | A@6 (edit in `rich/live.py`) | C@10, D | C (edits at 18, 19, 22, one argument loss) | C@9, D (repro refused at 10, 11) |

**Counts over the 24 runs that did not resolve [H]:** A 8 (fastapi_14448 3, rich_3468 1, httpx_3672 4), B 4 (fastapi_14605 3, requests_7205 1), C 12; flags: D 12 of 24, E 1, G 1, H 1, F 1. **Prose class F: 1 of 32 task-runs** (EXP-038 requests_7205); counting the EXP-052 httpx_3672 text ending that hit the compaction crash (EXP-052 section 9), 2 of 32, flagged. `analyze_traces.py` already counts it as `nudges`, no tool change: nudges in the four runs on the 8 ids 0, 1, 0, 0 (EXP-038's other 40 ids carry 6 more, on ids outside this cohort, not citable here).

**Edit failures, the class this round targets [V from summary.jsonl and hand reads of the traces].** Failed `edit_file` calls on the 8 ids per run (`n_edit_fail`): EXP-033 7, EXP-038 10, EXP-052 3, EXP-045 5. Tasks with 3 or more failed calls in a row (T): 1, 2, 0, 1 (requests_7205 s8 to 10; httpx_3672 s6 to 9 and fastapi_14605 s9 to 13; none; fastapi_14605 s9 to 13). **Failed calls that resend an `old_string` whose first 90 characters equal an earlier failed call on the same file (R_x), 3, 4, 0, 2 [H]:** EXP-033 requests_7205 s9 and s10 (same as s8) and fastapi_14605 s15 (same as s14); EXP-038 httpx_3672 s8 and s9 (same as s7) and fastapi_14605 s10 and s11 (same as s9); EXP-052 none (at most one failure per task); EXP-045 fastapi_14605 s11 and s12 (same as s10). The harness answers each with "provide more surrounding context" or "not found, check whitespace", and the model resends. Three tasks, four runs with a failure run of 3 or more.

**Cue, this candidate (R).** An edit fails and the next call at the same place carries the same text: requests_7205 EXP-033 s8 to 10, httpx_3672 EXP-038 s7 to 9, fastapi_14605 EXP-038 s9 to 11, EXP-045 s10 to 12, EXP-033 s14 to 15. Citing 3 tasks (at least 2 required). Seen on a non-unique match (httpx, fastapi_14605) and on not-found (requests_7205, fastapi_14605 EXP-033). EXP-044's "read then copy" line addressed only the not-found half and was killed by its own control; this bullet adds the half that was not tried (non-unique: start from a unique line above the change, three or more whole lines) and a stop (two failures at one place, then a smaller edit in the same function). A held-out sign that the half is not empty: in EXP-038 httpx_3672 the call that finally applied (s10) used a long, distinctive start, the shape the bullet asks for.

**Candidate L, not built this round (named so the next round can take it).** "When the first search hits more than one file, edit where the behavior is decided, not where it is merely called." Cue: fastapi_14448 EXP-033 s5, EXP-038 s7, EXP-052 s13 (edit in the caller file), rich_3468 EXP-033 s6 (edit in a different file from the one the fix is in). Two tasks, so it qualifies; not taken now because its process endpoint (an applied edit in a gold file) has references 5, 6, 6, 7 of 8, a range that leaves one step of room, and the largest wrong-file case (httpx_3672, 4 of 4) needs the sibling-package rule, not this one.

## 2. Design

### 2.1 The tree

`experiments/EXP-053/candidate-r/` is `experiments/EXP-033/candidate-e4b/` (the S-014 / EXP-038 tree: 8 minutes, 28 calls, `timeout_seconds` 240, `model: gemma-4-e4b-it-qat-w4a16-ct`) with **one bullet added** to `prompts/system.md`, section 3, directly after the `edit_file` bullet. EXP-045's edit is not kept (row 5), so the round starts from the base tree. The bullet, alone in `experiments/EXP-053/r_insert.md`:

```
- If `edit_file` fails because `old_string` occurs more than once or was not found, never send the same `old_string` again. Not found: re-read those lines with `read_file` (`start_line`, `end_line`) and copy them exactly. Occurs more than once: begin `old_string` at a line that appears only once above the change (the `def` or `class` line, or a distinctive neighbouring line) and include at least three whole lines. Use `allow_multiple` only when every occurrence must change. After two failed calls at one place, make a smaller edit in the same function.
```

It adds and removes nothing else. `agent.yaml`, `configs/sampling.yaml` and `eval_config.yaml` are byte for byte EXP-033's. Repo-agnostic: no repo, library, package, network, subprocess or URL word. `allow_multiple` is a parameter of the harness edit tool that the traces show (EXP-038 httpx_3672 s8 and s9 sent it as false). It is a prompt edit, lever (a); no skill and no script.

### 2.2 Measures, defined operationally and now

- **N_f**: failed `edit_file` calls, `n_edit_fail` of `summary.jsonl` (the error envelope plus argument loss). References 7, 10, 3, 5.
- **R_x**: failed `edit_file` calls whose `old_string` has the same first 90 characters as an earlier failed `edit_file` call on the same file in the same task [H, from the trace]. References 3, 4, 0, 2.
- **T**: tasks of 8 with 3 or more failed `edit_file` calls in a row. References 1, 2, 0, 1. Recorded, not read.
- **A_e / P**: tasks with an applied edit, and non-empty patches (EXP-033 6 and 6, EXP-038 8 and 8, EXP-052 7 and 7, EXP-045 8 and 8).
- **W**: mean and longest wall (EXP-033 56.9 s, EXP-038 78.3 s, EXP-052 82.5 s, EXP-045 54.4 s; longest 84 to 148 s).
- **M** (mechanism, recorded): for each failed non-unique or not-found call that is followed by another `edit_file` on the same file, whether the next `old_string` differs and is longer, and whether `allow_multiple` was set.
- **F**: `nudges` and `submit_patch_called` (references 0, 1, 0, 0; 8, 8, 7, 8 of 8).
- Malformed turns, scratch in patch, resolves (recorded only).

### 2.3 The cohort

smoke-8 (`experiments/cohorts/smoke-8.txt`), the strict subset of dev-48, paired against the four references above. With N_f spanning 3 to 10 across references, an N_f of 3 to 10 is inside the range and says nothing; the rule is tested only through R_x on runs that exercised it (N_f of 3 or more).

### 2.4 Cost

Kernel overhead about 430 to 500 s plus about 55 to 85 s per task at the references: 0.25 to 0.33 h (EXP-045 0.248 h, EXP-046 0.293 h, EXP-052 0.309 h by kernel log span); point 0.27 h. **Conditional worst case about 1.24 h** (every task at the 495 s cap), not expected: no reference task ran past 148 s. Day ledger: 4.0 GPU-h ceiling, the loop's share about 2.8, EXP-045 took 0.248, so about 2.55 h remain before this kernel and about 2.3 h after it.

`pack_submission.py --skip-budget-gate --allow-warnings` is used: 8 minutes is above the 4.5-minute packing gate (the EXP-033 situation); a screen is never uploaded.

## 3. Endpoints, fixed in advance

| # | endpoint | definition |
|---|---|---|
| E1 | R_x | 2.2, the target |
| E2 | N_f | 2.2, the exercise of the rule |
| E3 | A_e and P | applied-edit tasks and non-empty patches of 8 |
| E4 | W | mean and longest wall, cap hits |
| E5 | T and M | recorded |
| E6 | F, malformed, scratch in patch, resolves | recorded, resolves not read |

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

First match, in order.

- **Row 0, infrastructure.** Any `error` string in more than 2 of 8 rows, or the tree does not run, or a stage the harness cannot start: a mechanism result, no reading, no re-run without the user's word.
- **Row 1, harm: dropped.** A_e below 6 of 8 (EXP-033's floor), or mean wall above 140 s, or 3 or more tasks capped, or any task past 495 s, or a stray file in 2 or more patches, or malformed turns in 2 or more tasks.
- **Row 2, rule not exercised: no decision, keep-base.** N_f below 3 (every reference had 3 or more; a lower count is drift or an effect and cannot be told apart at n = 8).
- **Row 3, not enforced: dropped.** R_x of 2 or more (3 of the 4 references are at 2 or more).
- **Row 4, enforced: kept for the loop.** R_x = 0 with N_f of 3 or more and row 1 not fired. The next round starts from this tree. It is not a dev-48 result: a dev-48 arm needs the user's word (endpoint then: R_x per failed call and the applied-edit share on all 48 ids, paired against EXP-038, and the failed-edit-8 subset).
- **Row 5, otherwise: no decision, keep-base** (R_x = 1, or R_x = 0 with N_f of 3 or more and row 1 fired is impossible by order, so this is R_x = 1).

T, M, F, P, resolves: recorded, not read. **Blind prediction:** N_f = 5 (range 3 to 8), R_x = 1 (range 0 to 3), T = 1; the most likely rows are 5 and 3. This is a bound on whether a prompt-only rule of this shape holds (EXP-020 section 4), not a mean.

## 5. What this licenses

**It can kill the bullet** (rows 1 and 3) or **keep it for the loop** (row 4); row 2 and row 5 decide nothing. It cannot show that fewer resends raise the resolve rate (n = 8, resolves not read; the six tasks that fail are mostly wrong-place or wrong-fix, A and C, which this bullet does not touch: 20 of the 24 non-resolving runs). A kept edit counts only after an LB draw or a dev-48 arm.

## 6. Exact commands

```
cp -r experiments/EXP-033/candidate-e4b experiments/EXP-053/candidate-r      # then the one-bullet edit of section 2.1
diff -ru experiments/EXP-033/candidate-e4b experiments/EXP-053/candidate-r
python tools/validate_submission.py experiments/EXP-053/candidate-r --strict
python tools/pack_submission.py --src experiments/EXP-053/candidate-r --out dist/EXP-053-r.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed dist/EXP-053-r.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-053-r"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp053_r/kaggle_eval_l4x4.ipynb
kaggle kernels push -p notebooks/exp053_r
```

Analysis (a separate job): `kaggle kernels output rainm4/gemma4-exp053-r -p runs/EXP-053-r/`, lift the nested directory, `python -I -X utf8 tools/analyze_traces.py runs/EXP-053-r --cap-minutes 8 --max-calls 28`, then section 3 and 4 as written, row 0 first.

## 7. Defects and limits of this pre-registration

1. **R_x is a hand count with a 90-character prefix rule.** It matches the resends seen; a resend with a changed first line would be missed and a different edit with the same opening lines counted. The same rule is applied to the references and to the arm.
2. **N_f references span 3 to 10, and R_x is a rare event** (0 to 4 per run on 8 tasks, from 1 to 3 tasks). Row 4 (R_x = 0 with N_f of 3 or more) happened in one reference (EXP-052, which had no repeat failure), so row 4 is not unlikely by chance alone [I]; this is stated, and row 4 means "kept for the loop", not "worked".
3. **The not-found half of the bullet has a prior null** (EXP-044: arm X was no better than its control X0). It is included because the resends on not-found in the base (requests_7205 EXP-033, fastapi_14605 EXP-033) have the same shape. If row 4 fires, the bullet's two halves are not separated.
4. **Task-level confound:** the retries sit on 3 tasks (fastapi_14605, httpx_3672, requests_7205). A change in R_x is a change on those tasks.
5. **The diagnosis counts are hand counts from tool order and step ids** (section 1, tag [H]); two step numbers (EXP-052 requests_7309 and rich_3468 edit steps) are given as "edit" without a number.
6. **Seen-before:** the whole section 1 was read before the bullet was written; the bullet is written from it, and sections 3 and 4 after it, before any arm output.
7. **No check against the EXP-052 and EXP-045 changes:** the tree is the EXP-033 one; EXP-045's `/tmp` wording is not carried.
8. **Stray directory:** an accidental copy of the baseline tree, `experiments/EXP-053-candidate-tmp/`, exists untracked (a mistaken `cp -r` destination; `rm` is not an allowed command here); it is not part of this experiment and not committed.

## 8. Built

Built 2026-11-08 with the section 6 commands. Sections 1 to 7 are unchanged.

- **Diff, tree against baseline** (`diff -ru experiments/EXP-033/candidate-e4b experiments/EXP-053/candidate-r`): one hunk, `@@ -17,6 +17,7 @@` of `prompts/system.md`, the section 2.1 bullet added after the `edit_file` bullet (one line added, none removed).
- **Validate:** `python tools/validate_submission.py experiments/EXP-053/candidate-r --strict` gave 4 files, 1 agent, `RESULT: INVALID (1 errors, 1 warnings)`: the error is the packing gate (`120 x (8 + 1.0) min = 18.00 h`), the warning is the 240 s timeout (VERIFY(Q2)); both are the EXP-033 situation.
- **Pack:** `python tools/pack_submission.py --src experiments/EXP-053/candidate-r --out dist/EXP-053-r.zip --skip-budget-gate --allow-warnings`: 4 reachable files, `RESULT: VALID (0 errors, 2 warnings)`, 2.7 KiB, no rejected-prompt marker. **Zip sha256 `9f467adc9f8df3ff4206fea68e2e4e3c89db1c1f639b533d93e09b6822434cb8`.** Screen build, never uploaded.
- **Notebook:** `notebooks/exp053_r/kaggle_eval_l4x4.ipynb`: `EXP_ID = "EXP-053-r"`, `RUN_GOLD_CONTROL = False`, `N_TASKS = 8`, `MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"`, `TASK_IDS` = the 8 ids of `experiments/cohorts/smoke-8.txt`; 3,624 base64 characters embedded.
- `notebooks/exp053_r/kernel-metadata.json`: copied from `notebooks/exp045_p/`, only `id` (`rainm4/gemma4-exp053-r`) and `title` (`gemma4-exp053-r`) changed (`diff` shows those two lines).
- **Kernel id: `rainm4/gemma4-exp053-r`.** Push command: `kaggle kernels push -p notebooks/exp053_r`.

### 8.1 Push

Committed as `69092da` (hygiene OK, 9 files) before the push; the worktree files are LF, so the zip sha is the one of the committed blobs. `kaggle kernels push -p notebooks/exp053_r` on 2026-11-08 after that commit: "Kernel version 1 successfully pushed", kernel `rainm4/gemma4-exp053-r` (version 1), and the first `kaggle kernels status` read `RUNNING`. Pushed once, not re-run. Analysis is a separate job once the status is COMPLETE.

## Status

2026-11-08: **ANALYSED, ROW 3 FIRED: the bullet is dropped** (kernel `rainm4/gemma4-exp053-r`, version 1, COMPLETE, 0.281 GPU-h by kernel log span). Section 9 below. Zip `9f467adc...34cb8`. Nothing further runs from this experiment.

---

## 9. Results, 2026-11-08. Section 4's readings applied as written.

Kernel `rainm4/gemma4-exp053-r` version 1, COMPLETE. Output downloaded with `kaggle kernels output rainm4/gemma4-exp053-r -p runs/EXP-053-r` (the CLI nests the bundle under `runs/EXP-053-r/runs/EXP-053-r/`; analysed there, nothing moved). `python -I -X utf8 tools/analyze_traces.py runs/EXP-053-r/runs/EXP-053-r --cap-minutes 8 --max-calls 28`. Copy of the summary: `experiments/EXP-053/r/summary.jsonl`.

### 9.1 Numbers

- **Cost:** kernel log span 1,012.5 s = **0.281 GPU-h** (vLLM up in 338.9 s, task agent times 31.9 to 150.5 s). Inside the 0.25-0.33 expectation.
- **Per task** (wall s, calls, `n_edit_fail`, resolved): requests_7309 31.9, 4, 0, no; requests_7205 150.5, 4, 0, no; fastapi_14448 57.6, 4, 0, no; fastapi_14301 45.2, 8, 0, yes; httpx_3672 91.1, 9, 3, no; fastapi_14605 69.1, 12, 4, no; rich_3468 42.4, 9, 0, no; rich_3006 46.6, 5, 1 (one argument loss), yes.
- **Aggregates:** resolved 2 of 8 (the same two as in all four base runs; reported, not an endpoint); empty patches 0; `error` non-null 0 of 8; malformed turns 0; nudges 0; compactions 0; time or call cap hit 0; scratch in patch 0 of 8; `submit_patch` called 8 of 8. Wall mean **66.8 s**, median 0.87 min, longest 150.5 s.
- **E3, A_e and P:** every one of the 8 patches is non-empty and each task has at least one applied `edit_file`, so A_e = 8 and P = 8 (references 6, 8, 7, 8). Tasks whose patch is in a gold-patch file: 7 of 8 (httpx_3672 again edits `src/httpx/`, not `src/ahttpx/`), references 5, 6, 6, 7. fastapi_14448 is in the right file this time (it was not in 3 of the 4 base runs; recorded, one task, not read).
- **E2, N_f:** 0 + 0 + 0 + 0 + 3 + 4 + 0 + 1 = **8** (references 7, 10, 3, 5). Row 2's floor of 3 is passed.
- **E1, R_x, counted by the section 2.2 rule (same first 90 characters as an earlier failed `edit_file` on the same file in the same task) from the traces [H]:**
  - fastapi_14605: the four failed calls are steps 8, 9, 10, 11. Step 8 is a one-line `old_string` (occurs 4 times), step 9 starts at a line that occurs twice, steps 10 and 11 both start at the same line (occurs 2 times) and share their first 330 characters. Step 11 repeats step 10: **1**. Step 12 (applied, `allow_multiple` true on the one-line `old_string` that failed at step 8) is not a failed call and is not counted; that is the escape the bullet itself allows.
  - httpx_3672: edit calls at steps 9 (applied), 10, 11, 13; failed 10, 11, 13. Steps 10 and 11 share their first 104 characters. Step 11 repeats step 10: **1**. Step 13 starts elsewhere.
  - rich_3006: one failed call (argument loss): **0**.
  - **R_x = 2** (references 3, 4, 0, 2).
- **E5, recorded, not read:** T (3 or more failed edits in a row) = 1 strictly by step (fastapi_14605, 4 in a row), 2 if httpx_3672's 10, 11, 13 are counted as consecutive among its edit calls (references 1, 2, 0, 1). M (mechanism): of the 6 failed calls followed by another `edit_file` on the same file, 4 changed `old_string` (fastapi_14605 8 to 9, 9 to 10, 11 to 12 where it became the one-line `allow_multiple` form; httpx_3672 11 to 13) and 2 resent the same text (fastapi_14605 10 to 11, httpx_3672 10 to 11).- **E6:** F and nudges 0 (references 0, 1, 0, 0). D (no run after the last applied edit): 2 of 8 tasks (fastapi_14448, httpx_3672), against 2 to 4 of 8 in the references; three tasks (requests_7309, requests_7205, rich_3468) ran a command after their edit.

### 9.2 Readings applied, in order

- **Row 0:** not fired (no `error` in any row, every stage ran).
- **Row 1:** not fired (A_e 8, mean wall 66.8 s, no cap hit, longest 150.5 s, no stray file, malformed turns 0).
- **Row 2:** not fired (N_f = 8, at least 3).
- **Row 3: FIRED, R_x = 2 (2 or more).** The bullet is **dropped as measured**: the rule did not stop the resend in either of the two tasks where it had a chance, one non-unique (fastapi_14605 step 11) and one not found (httpx_3672 step 11), each right after an error text that the bullet answers.
- Rows 4 and 5 are not reached.

**Blind prediction (N_f = 5, R_x = 1, rows 5 or 3 most likely):** N_f was higher than predicted (8, inside the reference range 3 to 10), R_x was higher by one (2); the row range held (row 3). Wall mean was predicted at 60 to 80 s and was 66.8 s.

### 9.3 What it does and does not say

It kills this bullet for the loop (the next round starts from the EXP-033 tree again). It does not say the rule can never work: with a null prior on the not-found half (EXP-044) and a non-unique half that fired once in two tasks, n = 8 and R_x of 0 to 4 per run mean the reading is a bound, as section 4 says. Two things are worth carrying: (a) in 4 of 6 retries the model did change its `old_string`, so there is a partial effect that a count of resends at the 90-character level cannot reward; (b) the two resends sit exactly on the two tasks that dominate the base-set failures in class B, so a second arm on the same lever would need a mechanism, not more wording. Whether a tool-side change (a harness answer that names the line numbers of the other occurrences) could do it is not testable from `submission/`: it is a harness fact, not a config.

The run was short: 4 of 8 tasks ended in 4 or 5 calls and the mean was 66.8 s, so the loop's cost per round stays near 0.28 GPU-h.

### 9.4 Cost and ledger

0.281 GPU-h (log span 1,012.5 s). Loop ledger today: EXP-045 0.248 + EXP-053 0.281 = 0.529 h of about 2.8 h (about 2.27 h left under the loop's share; the day's 4.0 h ceiling is the lead's to count).

### 9.5 Report line

Row 3 fired (R_x = 2, N_f = 8): bullet dropped; a keep-base round, the first in a row (round 0 does not count, per the lead).
