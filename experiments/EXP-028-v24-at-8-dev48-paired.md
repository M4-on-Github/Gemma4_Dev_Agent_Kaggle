# EXP-028 — The adopted tree on dev-48 at 8 minutes: time profile, and one paired addition (lost-edit route)

**Date:** 2026-10-28
**Type:** dev-48 GPU experiment, two arms pushed together. ~8 L4x4-h of the 30/week (48 tasks × ~280 s mean +
startup ≈ 4 h per arm at an 8-min cap; worst case 48 × 8 min + startup ≈ 7 h, inside the kernel limit).
**Pre-registered:** this file is committed **before** either kernel is pushed. Sections 3–5 are written blind.
**Serves:** (i) the budget question behind submission #11 (EXP-027) on our own cohort — whether 8 min projects
inside the ~10.5 h ceiling for this prompt; (ii) the first paired addition to the adopted tree, which becomes the
candidate for slot #12 if it passes; (iii) the paper track's Contribution 2 (the lost-edit mechanism) measured on
the prompt we now ship instead of the one we retired.
**Supersedes:** EXP-026 Arm C as the LB-facing test of the recovery route. Arm C tested the route on the 12.8 KB
prompt lineage, which #11 retires from the LB; its question is re-asked here on the tree we ship. Arm C stays
pre-registered and may still be run for the paper if quota allows.

---

## 1. Why these two arms

**Arm R** is the tree uploaded as submission #11: the rank-3 v24 bundle at `max_time_minutes 8`,
`max_tool_calls 28`, `max_turns 80`, `timeout_seconds 240`, prompt 3,162 chars (their `docs_src/` line dropped).
Nothing we have measured locally describes this prompt at this cap. The team's own `runs.jsonl` gives mean
275–296 s and 15–24% of tasks at the cap on *their* dev sets; our dev-48 is 22 fastapi / 16 rich / 9 requests /
1 httpx, oversampling the small repos, so the mean may differ. EXP-027 §4 row 1 (blank) and the gate
re-derivation both need a measured distribution on our cohort, not theirs.

**Arm RH** is Arm R plus one section, `experiments/EXP-028/recovery-section.md`, inserted verbatim before
"## 4. One check, one repair, then submit" (anchor matched exactly once; everything else byte-identical). It is
the single-argument `run_command` route for the `edit_file` loss EXP-026 §1 verified (200/201 lost calls end in
`ng:`, an unterminated string literal; repeat rate ~90% once a malformed call is in context; the model takes the
shell route unprompted 0 of 31 times after a first loss). Their prompt does not address this failure. At
thinking 4096 it cost ~18% of `edit_file` calls on ~4 of 48 tasks in EXP-003 — small per task, but every one of
those tasks loses its edit phase to retries.

Why not more arms: `max_tool_calls` 28 → 40 (their v25) and a 7-min cap are each a one-variable test worth a
later arm; adding them here would make RH vs R a package test. One addition, paired, is the design that EXP-025
§1 argued for and EXP-026 inherited.

## 2. Design

Same 48 ids (`experiments/cohorts/dev-48.txt`) in both arms; both kernels pushed together so vLLM build,
hardware day and queue are shared. `RUN_GOLD_CONTROL=False` (EXP-000 already did it). Built with
`tools/build_notebook.py`, never hand-edited; `kernel-metadata.json` copied from the working `exp025_armA`
config with only `id`/`title` changed (explicit pinned `docker_image` sha carried; `plan.md:1188`).

| | Arm R | Arm RH |
|---|---|---|
| tree | `experiments/EXP-027/candidate-v24-at-8/` (= submission #11) | `experiments/EXP-028/candidate-RH/` (= R + the section) |
| prompt chars | 3,162 | 4,104 (section = 942 chars, 15 lines) |
| caps | 8 min / 28 calls / 80 turns / 240 s | same |
| sampling, tools | as #11 | same |
| zip sha256 | `c22069db6623a07c9f133fef33a8c193393dca170c84676e708d0bd9f5077600` | `248dd8eb3afecb3cfc7f21af9853442c2f4244e91247b575cd4ad6f8b97c43da` |

Build check, done before this commit: `diff -r` R → RH shows exactly the 15 inserted lines; validator on RH:
1 error (the 18.00 h gate line, overridden as in EXP-027) + 1 warning (`timeout_seconds 240`), instruction chars
4,104; packed with `--skip-budget-gate`; both zips 4 members.

## 3. Endpoints, fixed in advance

**A. Time profile, estimated on both arms (not a contrast).** Per-task `task_wall_s`: mean, median, p90, the
fraction ending within 20 s of 480 s, and the fraction ending at 28 tool calls. Projected hidden-set hours
= mean × 120 / 3600 + the overhead measured in the same run (server start + per-task setup + grading). Also
`setup_s`, compactions per task, prompt-token peak.

**B. Primary contrast, RH vs R: compliance after a lost call.** Among tasks with ≥ 1 call failing with
`mandatory input parameters are not present`, the fraction whose **next** call is `run_command`. Baseline from
the retired lineage: 4.6% (EXP-025 Arm A, 9 of 195), 0 of 31 after a *first* loss. Two-sided Fisher exact on
first-loss events, R vs RH.

**C. Secondaries (paired, exact McNemar where per-task):** repeat-loss rate (lost calls after a task's first
÷ all lost calls); `n_edit_arg_loss` per arm; wasted retries (identical `edit_file` resends); empty-patch rate;
never-attempted-an-edit; `submit_patch` called; first-edit turn (median); resolved **[reported, not an
endpoint]**; whether any heredoc edit exited non-zero or touched a file outside the intended one (harm).

**D. Power, written down.** Compliance: if R shows k first-loss events, RH needs about the same k; with k ≈ 6
per arm, 0/6 vs 4/6 gives Fisher p ≈ 0.06, so **fewer than 4 first-loss events in R makes B uninterpretable**
(EXP-026 §3 row 1, unchanged). Resolves: a paired resolve difference needs ≥ 6 same-direction discordant pairs
of 48 to reach p < 0.05; not powered, hence not an endpoint.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

**Time profile (Arm R governs; RH reported alongside):**

| # | outcome | reading |
|---|---|---|
| T1 | projected hidden hours **> 10.5** | 8 min is unsafe on our own measure even with this prompt. If #11 also blanked, the next slot is this tree at **6.0 min**; if #11 scored, read #11 as having survived inside variance and still move the next slot to the cap that projects ≤ 10 h. |
| T2 | projected hidden hours **9.5–10.5** | 8 min stands but has no margin: do not add anything that lengthens turns (thinking, output tokens) without re-measuring. |
| T3 | projected hidden hours **≤ 9.5** | 8 min stands with margin; a 9–10 min arm is a legitimate later single-variable test. |
| T4 | **≥ 25% of tasks end at 28 calls and none of those resolve** | the call cap binds the way it did in EXP-003; `max_tool_calls` 40 (their v25) is the next single-variable arm, before any prompt change. |

**Recovery route (RH vs R), rows applied in order, first match governs:**

| # | outcome | reading |
|---|---|---|
| 1 | **R has fewer than 4 first-loss events** | Underpowered for B; not a null. Record counts; the section stays or goes on §5's cost argument alone (it fires only after an error). |
| 2 | **Compliance ≥ 60% in RH and no harm (row 7 clean)** | The route works on this prompt. **RH is the tree for slot #12.** |
| 3 | **Compliance 25–60%** | Partial. Keep for #12 (bounded cost); the next lever is wording/placement, not mechanism. |
| 4 | **Compliance < 25%** | A prompt rule does not reach this on this prompt either. **R is the tree for #12**; drop the route from the LB lineage. |
| 5 | **Compliance ≥ 60% but ≥ 2 heredoc edits exit non-zero or hit the wrong span** | Template defect. Fix the template offline (replay in a sandbox), do not re-spend an arm; #12 ships R. |
| 7 | **Harm guard (additive):** RH empty-patch rate worse than R at exact McNemar p < 0.05 | Revert the section regardless of compliance; #12 ships R. |
| 8 | **Either kernel blank/crash (additive)** | Infrastructure. Check the pinned `docker_image` first (`plan.md:1188`); re-push the failed arm alone. |

## 5. What this does and does not license

**Licenses:** the time distribution of this prompt at 8 min on dev-48 and a projection from it; a statement
about whether the recovery section moves post-loss behaviour on this prompt, at this n; the choice of tree for
slot #12 between R and RH.

**Does not license:** any resolve-rate claim (not powered); any LB claim (one task = 0.017, MDE ~4); any
inference about the 12.8 KB lineage (retired; EXP-026 Arm C is that question); generalization of the time
profile to the hidden set beyond the stated projection (private repos may be slower or faster than our four).

**Cost asymmetry for the section, stated now:** it adds ~900 prompt chars on every task and changes behaviour
only after an error that already means the call did nothing. Downside: ~250 tokens/turn of prompt; upside:
the retry loop that consumed 8–19 calls per affected task in the retired lineage.

## 6. Exact commands

```
python -I -X utf8 tools/validate_submission.py experiments/EXP-028/candidate-RH --strict          # 1 error = gate, 1 warning = timeout 240
python -I -X utf8 tools/pack_submission.py --src experiments/EXP-028/candidate-RH --out experiments/EXP-028/v24_at8_RH.zip --skip-budget-gate
python tools/build_notebook.py --embed experiments/EXP-027/v24_at8.zip   --set EXP_ID="EXP-028-armR"  --set RUN_GOLD_CONTROL=False --set TASK_IDS=<48 ids> --set N_TASKS=48 --out notebooks/exp028_armR/kaggle_eval_l4x4.ipynb
python tools/build_notebook.py --embed experiments/EXP-028/v24_at8_RH.zip --set EXP_ID="EXP-028-armRH" --set RUN_GOLD_CONTROL=False --set TASK_IDS=<48 ids> --set N_TASKS=48 --out notebooks/exp028_armRH/kaggle_eval_l4x4.ipynb
kaggle kernels push -p notebooks/exp028_armR ; kaggle kernels push -p notebooks/exp028_armRH
```
Pre-push verification as EXP-025 §8: decode each notebook's `SUBMISSION_B64` and hash it against the zip; confirm
`EXP_ID` and all 48 ids in the source; diff both `kernel-metadata.json` against `exp025_armA` (id/title only).
Analysis: `tools/analyze_traces.py runs/EXP-028-arm{R,RH} --cap-minutes 8 --max-calls 28`, then
`tools/run_forensics.py compare`, then the lost-call pass from EXP-026 §1 on both trace sets.

## 7. Defects in this pre-registration, logged after the fact

None yet.

## 8. Built and pushed

Filled below the line at build and push time. Nothing above it changes.

---
