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

Logged 2026-11-03 at analysis time; nothing in sections 3-5 is changed by these.

- **D1, primary metric vs the section text.** Endpoint B credits compliance only when the *next* call after the
  first loss is `run_command`, but the inserted section tells the model to copy the text "from your last
  `read_file`", so a read-then-heredoc sequence (the instructed path when the model has no fresh read) scores as
  non-compliant. 3 of the 6 RH first-loss tasks went `read_file` next. Row 4 is applied as written; the
  per-task sequences are recorded in section 9 so a later reader can see the gap.
- **D2, row order.** Row 2 (compliance >= 60%, row 7 clean) precedes row 5 (compliance >= 60% with >= 2
  failed heredocs), so under first-match row 5 could only fire when row 7 also fired. Moot here (compliance 0%).
  There is no row 6.
- **D3, which call count.** Section 3 A and T4 say "end at 28 tool calls" without naming the count. The harness
  `tool_calls` field in `task_results.jsonl` and `analyze_traces.py` `calls_cap_hit` (trace calls, free tools
  excluded) differ by one task on Arm R (17 vs 18). Section 9 uses the analyzer value and reports both.
- **D4, artifact path.** The hygiene check and `.gitignore` admit only files named exactly `summary.jsonl`
  under `experiments/`, so the summaries are stored as `experiments/EXP-028/armR/summary.jsonl` and
  `experiments/EXP-028/armRH/summary.jsonl`, not `<arm>-summary.jsonl`.
- **D5, compaction detector (added 2026-11-05, experimenter; tooling defect, not a pre-registration defect).**
  `analyze_traces.py` counted a compaction only when a trace step had `compact` in its `event_type` or
  `author`. ADK 1.36.1 appends the token-threshold summary straight to the session and never yields it as an
  event, so no trace step marks it, and both arms read `compactions = 0`. The EXP-030 critic found the drops.
  The detector now counts a drop in `metrics.prompt_tokens` between consecutive turns of the same author, right
  after a turn at or above `R.COMPACTION_TOKEN_THRESHOLD` = 14,336. The rule is in `count_token_compactions`;
  the test is `test_token_compaction_detected_from_prompt_drops`.

  Corrected counts, from `analyze_traces.py runs/EXP-028-arm{R,RH} --cap-minutes 8 --max-calls 28`:

  | Arm | Compactions | Tasks with ≥1 | Max per task | Resolved tasks | Unresolved tasks | Cap-hit tasks |
  |---|---|---|---|---|---|---|
  | R | 49 | 36 of 48 | 3 | 3 compactions in 3 of 9 | 46 in 33 of 39 | 26 in all 18 |
  | RH | 49 | 35 of 48 | 3 | 4 in 4 of 10 | 45 in 31 of 38 | 26 in all 17 |

  Both `experiments/EXP-028/arm{R,RH}/summary.jsonl` files were regenerated. **The only field that changed is
  `compactions`, per task.** With line endings normalised, every line matches the 2026-11-03 file byte for
  byte except that one value.
  - Endpoint A reports compactions per task, and the §9.1 row reads `compactions | 0 | 0`. That row is left
    as written and is superseded by this table.
  - No reading in section 4 depends on compactions, so no decision changes.

## 8. Built and pushed

Filled below the line at build and push time. Nothing above it changes.

---

**Pre-registration commit `ae7b045`** (this file through §7, `recovery-section.md`, `candidate-RH/`, both
notebook directories), made before either push.

**Built 2026-10-29 ~02:10 UTC** with `tools/build_notebook.py` (`--embed`, `--set EXP_ID`, `--set
RUN_GOLD_CONTROL=False`, `--set TASK_IDS=<48 ids as a JSON list>`, `--set N_TASKS=48`, `--out`). Pre-push
verification, as EXP-025 §8: each notebook's `SUBMISSION_B64` decoded and hashed — **R = `c22069db…`, RH =
`248dd8eb…`, both match**; `EXP_ID` literal, `RUN_GOLD_CONTROL = False` and all **48/48** dev-48 ids present in
each source; both `kernel-metadata.json` differ from `exp025_armA` in `id`/`title` only (checked with
`diff --strip-trailing-cr`), so the explicit pinned `docker_image` sha is carried.

**Pushed 2026-10-29 02:21:44 UTC, version 1 each, both RUNNING at 02:22 UTC:**

| arm | kernel | embedded tree sha256 |
|---|---|---|
| R — #11 as shipped | `rainm4/gemma4-exp028-armr` | `c22069db6623a07c9f133fef33a8c193393dca170c84676e708d0bd9f5077600` |
| RH — R + recovery section | `rainm4/gemma4-exp028-armrh` | `248dd8eb3afecb3cfc7f21af9853442c2f4244e91247b575cd4ad6f8b97c43da` |

Expected wall ~4 h each (48 × ~280 s + startup); results expected from ~06:30 UTC. Download to
`runs/EXP-028-armR/` and `runs/EXP-028-armRH/`, then the §6 analysis commands. Submission #11 (ref 57750294) was
still PENDING at push time; §4's time-profile rows are read against it once both exist.

**Downloaded and analyzed 2026-11-03 ~21:10 UTC** (both kernels COMPLETE). `kaggle kernels output` nests the
bundle as `runs/<EXP>/runs/<EXP>/` plus a `.zip`; the inner directory was moved up so each run dir holds
`task_results.jsonl` (48 rows each) and `traces/` (48 traces each). No archive needed extracting.

## Status

Analyzed; section 9 below. No kernel running. Next: slot #12 upload per EXP-029 with the tree section 9 names.

---

## 9. Results and readings applied, 2026-11-03. Section 4 applied as written.

Commands (all `python -I -X utf8`): `tools/analyze_traces.py runs/EXP-028-arm{R,RH} --cap-minutes 8
--max-calls 28`; `tools/run_forensics.py forensics` on each; `tools/run_forensics.py compare runs/EXP-028-armR
runs/EXP-028-armRH`; `tools/estimate_budget.py --eval-config experiments/EXP-027/candidate-v24-at-8/eval_config.yaml
--results runs/EXP-028-armR/summary.jsonl`; the EXP-026 section 1 lost-call pass as a scratch script that reads the
traces as data and imports `run_forensics.fisher_exact_2x2` / `mcnemar_exact` / `collect_forensics`. Kernel log
timestamps (`gemma4-exp028-arm*.log`, seconds since kernel start) give server start, per-task spacing and the
kernel wall. Summaries: `experiments/EXP-028/armR/summary.jsonl`, `experiments/EXP-028/armRH/summary.jsonl`.

### 9.1 Time profile (endpoint A; Arm R governs)

| | Arm R | Arm RH |
|---|---:|---:|
| mean `wall_s` (48 tasks) | 297.4 s | 296.7 s |
| median / p90 (analyzer) | 302.8 s / 483.3 s | 268.7 s / 485.2 s |
| max wall | 489.9 s | **751.9 s** (`rich_3480`, 272 s past the 480 s cap) |
| ending within 20 s of 480 s (wall >= 460 s) | 6/48 = 12.5% | 10/48 = 20.8% |
| `time_cap_hit` (analyzer, wall >= 475 s) | 12.5% | 20.8% |
| ending at 28 calls: analyzer `calls_cap_hit` | **18/48 = 37.5%, 0 resolved** | 17/48 = 35.4%, 2 resolved |
| ending at 28 calls: harness `tool_calls` >= 28 | 17/48, 0 resolved | 17/48, 2 resolved |
| harness errors | 6 session timeout (8.0 min), 4 turns budget (80) | 7 session timeout, 1 turns budget |
| per-task `setup_s` mean | 0.05 s | 0.05 s |
| per-task time outside `wall_s` (log task-loop span minus summed agent walls, / 48) | 0.35 s | 0.35 s |
| compactions | 0 | 0 |
| prompt-token peak (any turn) | 22,019 | 23,247 |
| vLLM server start (`summary.json`) | 396.5 s | 341.9 s |
| analyzer `projected_12h_total_h` (walls + setup, x 120/48) | 9.92 h | 9.89 h |
| **projected hidden hours** = analyzer projection + server start + residual per-task overhead x 120 | **9.92 + 0.11 + 0.01 = 10.04 h** | 9.89 + 0.09 + 0.01 = 10.00 h |

Grading time sits inside `duration_s` in this notebook (the grading sandbox is created ~3.5 s before each
`[k/48]` log line and `agent=` equals the spacing), so no separate grading term is added. Using the full pre-loop
time (kernel start to vLLM up, 521 s) instead of server start gives 10.07 h; the row is the same either way.

`estimate_budget.py --results` on Arm R reports per-task mean 5.66 min, projected mean 11.32 h, p50 12.22 h,
VERDICT BLOCK. It takes max(measured wall, decode-model estimate) per task, so it is a different model from the
section 3 formula (measured mean); recorded, not used for the reading.

**T rows.** **T2 fires**: projected 10.04 h is inside 9.5-10.5. 8 min stands with no margin; nothing that
lengthens turns (thinking, output tokens) is added without re-measuring. **T4 also fires** (an independent
condition): 37.5% of Arm R tasks end at 28 calls (>= 25%) and none of them resolve (harness count 17/48, also 0
resolved). The call cap binds; `max_tool_calls` 40 (their v25) is the next single-variable arm, before any prompt
change. Not in any row but relevant to the T2 caveat: one RH task ran 751.9 s against an 8-min cap, so the session
timeout is not a hard per-task bound, and the projection does not model such overruns.

### 9.2 Recovery route (endpoints B and C)

| | Arm R | Arm RH |
|---|---:|---:|
| lost calls (`mandatory input parameters are not present`), all tools | 67 (58 `edit_file`, 9 `write_file`) | 17 (10 `edit_file`, 7 `write_file`) |
| analyzer `n_edit_arg_loss` sum | 58 | 10 |
| **first-loss events** (tasks with >= 1 lost call) | **8** | **6** |
| **compliance: next call after the first loss is `run_command`** | **0/8** | **0/6** |
| next call after the first loss | 7 `edit_file`, 1 `write_file` | 3 `read_file`, 2 `write_file`, 1 `edit_file` |
| Fisher two-sided, first-loss compliance R vs RH | p = 1.0000 | |
| repeat-loss rate (lost after a task's first / all lost) | 59/67 = 88.1% | 11/17 = 64.7% |
| next edit-tool call after a loss is itself lost | 50/55 | 11/12 |
| identical `edit_file`/`write_file` resends of a lost call | 44 | 11 |
| `edit_file` calls after the first loss (the section says zero) | 71, in 7 of 8 tasks | 13, in 4 of 6 tasks |
| heredoc `run_command` calls, all / non-zero exit | 43 / 2 | 135 / 36 |
| template heredocs (`assert s.count(old)`), calls / non-zero / tasks | 0 / 0 / 0 | 10 / 2 / 3 |
| heredocs after a first loss / non-zero | 2 / 0 | 13 / 3 |
| empty patch | 6/48 | 5/48 (discordant 4 R-only, 3 RH-only; exact McNemar p = 1.0000) |
| `submit_patch` called | 42/48 | 40/48 |
| never called `edit_file` or `write_file` (forensics) | 4/48 | 3/48 |
| first-edit turn, median (forensics per task) | 14 (n = 44) | 13 (n = 45) |

RH first-loss tasks, calls after the loss: `fastapi_13207` read, read, run, read (first heredoc 9 calls later, 3
`edit_file` after); `fastapi_14262` read, run (heredoc at 9, 0 `edit_file`); `fastapi_14297` write, run (no
heredoc, 1 `edit_file`); `fastapi_14605` 7 losses, then 8 template heredocs and 8 `edit_file`; `fastapi_15030`
read, read, run (heredoc at 5, 1 `edit_file`); `fastapi_15661` 6 `write_file` losses, heredoc at 6, 0 `edit_file`.

Heredoc wrong-span or wrong-file harm was **not read** (it needs a per-heredoc diff against the intended target);
only exit codes were counted. It matters only to row 5, which cannot fire here.

**Rows, in order.** Row 1: R has 8 first-loss events (>= 4), does not fire. Row 2: RH compliance 0% (< 60%), no.
Row 3: not 25-60%, no. **Row 4 fires: compliance 0/6 < 25%. A prompt rule does not reach the next call on this
prompt either. R is the tree for #12; the route is dropped from the LB lineage.** Row 7 (additive): empty patch 6
vs 5, McNemar p = 1.0, does not fire. Row 8 (additive): neither kernel blank or crashed, does not fire.

**The prediction did not hold** on the pre-registered metric: the section did not move the next call after a
first loss (0/6, against 0/8 without it). What the secondaries show, recorded without changing the reading: RH had
a quarter of the lost calls (17 vs 67) and three times the heredoc edits (135 vs 43), so the section changed how
edits were made from the start of a task rather than after a loss; the post-loss loop was shorter (identical
resends 44 vs 11, `edit_file` after the first loss 71 vs 13), but these are not paired-tested here and 26 of the
67 R losses come from one task (`fastapi_14262`). D1 in section 7 notes why the next-call metric undercounts the
read-then-heredoc path the section instructs. None of this licenses a claim; it is input for the paper and for
any later wording or placement test.

### 9.3 Resolves (reported, not an endpoint)

R 9/48 (Wilson 10-32%), RH 10/48 (12-34%). Paired: both 8, R only 1 (`fastapi_9753`), RH only 2 (`fastapi_5624`,
`rich_3180`), neither 37; exact McNemar p = 1.0000.

### 9.4 Decision for slot #12

**Tree: R** (= submission #11, `experiments/EXP-027/candidate-v24-at-8/`, zip sha256
`c22069db6623a07c9f133fef33a8c193393dca170c84676e708d0bd9f5077600`), by recovery row 4. **Cap: 8 min / 28 calls**
(T2; T1 did not fire, so no move to 6.0 min). Next GPU arm named by T4: `max_tool_calls` 28 -> 40, one variable.

### 9.5 Kernel wall-clock for the GPU ledger

From the kernel logs (time of the last log entry, seconds since kernel start): **Arm R 14,832 s = 4.12 h; Arm RH
14,716 s = 4.09 h; total 8.21 L4x4-h.** Queue time before kernel start is not in the log.
