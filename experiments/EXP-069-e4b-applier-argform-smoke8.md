# EXP-069 — Applier edit_file argument form: a bare-path recipe and a one-resend rule (smoke-8 screen, D-009 round 2, class S and A)

**Date:** 2026-11-10
**Type:** smoke-8 screen, ~0.35 L4x4-h (same tree as EXP-064 with one prompt paragraph changed; EXP-064 0.353 GPU-h at kernel wall about 1260 s). One push, no upload, no dev-48.
**Cohort:** smoke-8
**Ladder:** L2. L0 and L1 are section 1 (the traces of EXP-061-r, EXP-062-r, EXP-063-p, EXP-064-loc, EXP-066-srch, plus `workspace.py`).
**Pre-registered:** this file is committed before the push. Sections 3-5 are written blind and are not revised.
**Serves:** D-009 round 2 (class S and A, the applier's argument form), user decision 2026-11-10 (option A, class S on the E4B). The critic's D-009 review (`experiments/EXP-067/critic.md`) put A + S at 22 failed edits over 9 task-runs and 3 of the 5 edit-failure empties.
**Relates:** EXP-064 (base tree, `candidate-loc`), EXP-067 (method, first-edit reference), EXP-068 (round 1, same base tree, a separate and in-flight kernel; not stacked here), EXP-057 lesson 1 (an exact literal recipe worked where implied wording did not), EXP-053 (a design must not rest on wording alone).

## 1. Desk check (zero GPU)

### 1.1 How the harness resolves `filepath` (`data/src/swegemma/swegemma/tools/workspace.py`)

`edit_file` (lines 217-289) calls `_resolve_workspace_path(filepath, allow_root=False)` (lines 22-55). It strips a leading `/workspace/`, rejects any other leading `/`, and builds `Path(norm_filepath)`. A quote character is just a character of the first path component, so the file is looked up as `/workspace/'src/pkg/mod.py'` and `copy_from` fails with `Source path /workspace/'...' not found in sandbox ...` (`FileEditError`, kind **S**). `./src/pkg/mod.py` and `/workspace/src/pkg/mod.py` both resolve to the right file, so the quote character is the whole defect. That is noted and not built on: the recipe asks for the plain path.

### 1.2 Every quote-wrapped `edit_file` filepath on the five runs

Defined as an `edit_file` call whose `filepath` value begins with `'` or `"`. Found by Grep and line reads of `runs/<EXP>/traces/` (gitignored). **8 of 40 task-runs** (EXP-062-r: 0). Step numbers are trace `step_id`s.

| run | task | quote | applier answers (in order) | next call after the first answer |
|---|---|---|---|---|
| 061-r | requests_7309 | single | A (step 13), A (14), A (15), S (16), then `submit_patch` patch_size 0 | quote kept on every retry; never bare. **Empty** |
| 061-r | httpx_3672 | single | S (17) | bare path, applied (step 18), patch 411 |
| 061-r | rich_3006 | single | A (13) | bare path, applied (14), patch 558 |
| 063-p | fastapi_14301 | single | S x6 (steps 15-20, same call each time) | identical resend x5, never bare. **Empty** |
| 063-p | requests_7309 | single | A (15) | bare path, applied (16), patch 529 |
| 064-loc | requests_7205 | double | A (13) | bare path, applied (14), patch 561 |
| 066-srch | rich_3006 | single | A (14) | bare path, applied (15), patch 558 |
| 066-srch | fastapi_14448 | double | A (17), A (18), S x4 (19-22, the last on routing.py), then `submit_patch` patch_size 0 | quote kept; never bare. **Empty** |

- Calls: S 12 over 4 task-runs (061 x2, 063 x6, 066 x4); A on a quote-wrapped path 9 over 6 task-runs. 21 failed calls here against the critic's 22 (the difference is one A call I did not locate; it is not a quote-wrapped one). Quote kind: single 6 task-runs, double 2.
- **Where the quotes come from: the applier, at its first `edit_file` call.** Every one of the 8 first quoted calls is the applier's first `edit_file` of the session. FILE lines in the drafters' and reader's text are bare (Grep `FILE: ?[^a-zA-Z_/. ]` over the five runs: the only hit in a quote-wrapped task-run is 066 fastapi_14448 step 19, a backtick form inside the applier's own reasoning text, written after its first quoted call at step 17). The reader's `run_command` calls in these task-runs use bare paths; a quoted pathspec exists upstream in only one of the 8 (063 requests_7309, `git grep ... -- '*'`, a glob, and that task-run recovered) and in several non-quoted task-runs (061 fastapi_14448, fastapi_14605, requests_7205, rich_3468; 063 rich_3468, httpx_3672, fastapi_14605; 064 rich_3006, rich_3468; 066 fastapi_14301). So no stage's output is the source; the stage-prompt fix is not indicated. 064 and 066 were Grepped; the quoted-pathspec count for 061 and 063 is by task, not by step.
- **The quote wrap rides with a malformed call.** In 066 fastapi_14448 step 17 the call has fragment keys (`"'__wrapped__')"`, `"functools.partial)"`) and a quoted `new_string`: the model wrote a Python-style call with the code, and the argument parser split it at commas and parentheses. The A answer ("mandatory input parameters ... old_string") is that mangle; S is the same filepath defect without the loss. I read only that trace's call body; the other seven I did not read argument by argument, so the link is shown for one.
- **Recovery behaviour (the reference for the screen):** after the first quote-wrapped answer, the applier's next `edit_file` is a bare path on **5 of 8** (it applied each time). On **3 of 8** it never is: it resends the same quoted call (063 x5, 066 x4 + the A pair) or goes to `submit_patch` with nothing applied. Those 3 are the three A+S empties of the critic; each ended by an applier `submit_patch` at patch_size 0 (I did not check the remaining time and call budget in those three). After A, bare retry 4 of 6; after S, bare retry 1 of 4 (httpx_3672).
- **A base-prompt conflict.** `prompts/applier.md` section 2 step 1 says "If the call reports no match **or fails**, go straight to the next draft. Do not retry the same draft with changes." The applier that recovers is breaking that sentence; the one that does not is mostly obeying it (the drafts are often one draft deep, so "the next draft" is the same call again). A resend rule placed below that sentence would contradict it, so the sentence itself is rewritten.
- **Opportunity rate for this screen.** 8 of 40 task-runs, 1.6 per 8, so the chance of 0 in 8 is about 0.17 if the rate is 0.2 per task-run. It is a low-incidence event; the screen cannot measure whether the recipe lowers it (section 5).

### 1.3 References (from the five runs, 40 task-runs; section 1.2)

First-edit applies on EXP-064-loc 6 of 8 (EXP-067 9.3); first-edit misses caused by A or S 8 of 40 (A 6, S 2; critic); edit-failure empties 5 of 40, of which A+S 3 (critic); S calls per run: 061 2, 062 0, 063 6, 064 0, 066 4; quote-wrapped task-runs per run: 3, 0, 2, 1, 2; identical resends after S 8 over 2 task-runs (063 fastapi_14301 5, 066 fastapi_14448 3).

## 2. Design

One variable: **how the applier is told to write the `edit_file` filepath and what to do after an A or S answer.** Two prompt edits in one file, one concept. Nothing upstream changes (section 1.2).

| | value |
|---|---|
| tree | `experiments/EXP-069/candidate-argform/` = `cp -r experiments/EXP-064/candidate-loc`, then `prompts/applier.md` edited. Not stacked on EXP-068 or EXP-066 |
| `prompts/applier.md` section 2 step 1 | after "copied exactly as written in the draft." adds: "Send exactly these three arguments. `filepath` is the FILE line verbatim with nothing around it: `src/pkg/mod.py`, never `'src/pkg/mod.py'` and never `\"src/pkg/mod.py\"`." The sentence "If the call reports no match or fails, go straight to the next draft." becomes "If the call reports no match, go straight to the next draft. If the answer says `old_string` is not present, or says a `Source path` was not found, send that same call once more with every quotation mark removed from `filepath` and with all three arguments present. Never send an identical call twice." The closing "Do not retry the same draft with changes and do not re-read the file." becomes "Do not otherwise retry ..." |
| `prompts/applier.md` section 3 | "Prefer `edit_file`." becomes "Prefer `edit_file`, with a bare `filepath` as in section 2." (the applier's own edit, when no draft applied, takes the same form) |
| the literal shape | argument names and a literal bare path, not Python-call syntax, because the `'allow_multiple'` quote-wrapped key and the fragment keys in 066 fastapi_14448 look like Python-repr leaking into the call; showing `edit_file(filepath='...')` would put that form in the prompt |
| diff | `diff -ru experiments/EXP-064/candidate-loc experiments/EXP-069/candidate-argform` shows exactly two hunks in one file, `prompts/applier.md` (the two above). It is the whole diff; `agent.yaml`, `eval_config.yaml`, `configs/`, the reader, the drafters and every yaml are byte-identical. Added length: 2 sentences and a clause (about 90 words), against lessons-e4b-loop line 101 (tool-call form is fragile to prompt length) |
| lint | `validate_submission.py ... --official --strict --json`: 1 error, the 18.00 h gate, which `--skip-budget-gate` demotes; 2 warnings carried (applier `submit_patch`, `timeout_seconds` 240); no new warning |
| eval config | EXP-064's: `timeout_seconds` 240, `max_tool_calls` 45, `max_time_minutes` 8, `max_turns` 120 |
| zip | `dist/EXP-069-argform.zip`, sha256 in section 8. Packed with `--skip-budget-gate`: 8 min is above the 4.5 min packing gate (18.00 h nominal; same override as EXP-061, 062, 064, 066, 068). **Not an upload.** |
| notebook | `notebooks/exp069_argform/`, kernel `rainm4/gemma4-exp069-argform` |
| cost | ~0.35 GPU-h; the slot rule is clear (EXP-068's kernel is COMPLETE, so 0 live) |

**Known limits, written before the run.**
1. **The recipe is wording, and the failure is in call generation.** The quote wrap rides with a Python-style malformed call (section 1.2). A sentence in the prompt may not stop the model emitting that call (the EXP-053 lesson). What the sentence does change, by construction, is the rule after an answer: it is now in the instruction instead of against it. So the screen reads recovery, not incidence.
2. **n = 8 and a 0.2 per task-run event.** About 1.6 quoted events expected; P(0) about 0.17. Under no effect, each quoted event recovers on its own 5 of 8 of the time (reference), so "all recover" has probability about 0.63 at 1 event, 0.39 at 2, 0.24 at 3 (rows 3 and 5).
3. **The rule can misfire.** A "no match" answer still goes to the next draft; an A or S answer now gets one resend. A resend after a no-match is recorded as a deviation (descriptive). The `edit_file` A answer can also arise from a mangled body with a clean path; the rule's "all three arguments present" covers it, and whether the resend repairs a mangled body is exactly what the screen reads.
4. **The base prompt carries two mentions of the same call form** (section 2 step 1 and section 3), 90 words more than EXP-064. The first-turn and text-form rows are the guard.
5. **Reader variation** (EXP-061, 062, 066): the tasks see different locations between runs, so a first-edit count moves by more than this change. Only quoted-event recovery is read as a behaviour; the first-edit count is a harm bound.

## 3. Endpoints, fixed in advance

By Grep and line reads of `traces/`, `task_results.jsonl`, `summary.jsonl` and the kernel log (no script is allowed to this agent), the EXP-067 and EXP-068 method.

- **Q (opportunity):** task-runs, and events, with a quote-wrapped `edit_file` filepath (section 1.2 definition), by kind (single, double). Reference 8 of 40 task-runs, 1.6 per 8.
- **S:** failed calls with `FileEditError` "Source path ... not found" where the path has a quote character; reported per run (reference 12 over the 5 runs, by run 2, 0, 6, 0, 4) and per task-run. **A:** failed calls with the "mandatory input parameters ... old_string" answer, split into a quote-wrapped filepath and a clean filepath.
- **Recovery, per quoted event:** the applier's next `edit_file` call after the first A or S answer on a quote-wrapped path (the "Q event") is (i) bare and applies, (ii) bare and fails (class recorded), (iii) quote-wrapped again with different body, (iv) an identical call (same filepath string and body), or (v) none, with `submit_patch` next. Reference: (i) 5 of 8, (iv) or (v) 3 of 8.
- **First-edit misses caused by A or S** over the 8 task-runs (reference 8 of 40, 1.6 per 8), and **first-edit applies** per task-run (EXP-064-loc 6 of 8).
- **Empty patches, and those caused by edit failure** (reference 5 of 40, 3 of them A+S; EXP-064-loc 1 of 8).
- **Harm inputs:** time, call and turn cap hits; mean wall against 100.0 s; **first-turn kind of the applier** (tool call in its first model turn, per task: a task where the applier's first turn is text with no tool call, listed); `n_text_form_calls`, `tool_free`, and applier-authored text-form calls; `scratch_in_patch`; the call count against 45; compactions and the largest prompt against 14,336.
- **Descriptive, no row:** resends after a no-match answer (a deviation from the rule), the extra applier prompt length, the draft kept, F and G and G1, R1-type failures (the reader's REGION is unchanged here; reference 11 on 2 task-runs).
- **Recorded only:** resolves (never an endpoint).

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Rows 1 and 2 are gates: if either holds it is reported and rows 3 to 6 are **not read** (the numbers are still recorded). Rows 3 to 6 are first-match.

| # | outcome | reading |
|---|---|---|
| 1 | **Infrastructure.** Any of: an `err` with a traceback, a sandbox execution error, a compaction or summarizer `ValueError`; the tree does not run on some task; the root fails to transfer to `pipeline`; a blank or crashed run | A bug, not a reading. Name the task and the step. |
| 2 | **Harm.** Any of: **empty patches 3 or more of 8**; any time, call or turn cap hit; **mean wall over 150 s**; **any tool-free task**; **any applier text-form call**; **the applier's first model turn is text with no tool call on 2 or more tasks**; **first-edit applies 4 or fewer of 8** (two below the EXP-064-loc reference of 6; reader variation alone moves it by one) | The paragraph costs more than it buys or breaks the applier's tool use. Name the tasks and counts. A task over 240 s is named, not a row. |
| 3 | **Not exercised.** Rows 1 and 2 did not fire, and **Q = 0 task-runs** (no quote-wrapped `edit_file` filepath in any of the 8 applier sessions) | No quoted event, so the rule was never tested. **No effect is claimed and none is read:** 0 quoted events at a 0.2 per task-run rate is about a one-in-six draw, and A or S absent is not the recipe working. No decision for this form; the form is not killed (D-009: a not-exercised round ends only this form's screen, which the lead may repeat or fold into a dev-48 arm without its own screen). Clean-path A answers are recorded. |
| 4 | **Kill (rule not followed).** Rows 1 to 3 did not fire, and **at least one Q event is followed by an identical resend or by `submit_patch` with patch_size 0 and no bare `edit_file` call between them, while turns and time remained** | The recipe does not enforce recovery on this model, the bound "a quoted event always ends in a bare resend" fails. The prompt-wording route for the applier's argument form is killed as a stand-alone change (reference non-recovery is 3 of 8, so this is a bound on enforcement, not a rate). The next forms are not prompt wording: a harness-side route is outside our levers, and the lead names the next. |
| 5 | **Promote.** Rows 1 to 4 did not fire, and **Q >= 3 task-runs**, and every Q event is followed by a bare `edit_file` call that applies (recovery (i) on all of them) | Recovery held on 3 or more events (under no effect all 3 recover with probability about 0.24, so this is a bound on behaviour, not an estimate of effect). Promoted **as a free rider, not as its own dev-48 arm** (section 5). |
| 6 | **No decision.** Anything else (Q of 1 or 2 with all recovered; or a Q event whose resend is bare but fails for another class; or A and S absent with the quoted form unseen) | Record per task. Resolves decide nothing. |

**Not rows, but binding:**
- Per-task resolves at n = 8 are never an endpoint; six of eight must flip the same way for p < 0.05.
- The S count per run (reference 0 to 6, mean 2.4) and the first-edit misses caused by A or S (reference 1.6 per 8) are reported as references only. A lower number than the reference is not read as the recipe working: the event is rare (about 0.2 per task-run), 0 to 6 across five runs of the same tree family, and the 8 tasks may simply not draw it.
- A quoted call that recovers through the rule counts as recovered; a quoted call that recovers with no rule text involved (the 5 of 8 of the reference) cannot be told apart at n = 8.
- The task named in the report for each row reached is whatever the traces show, not the prediction below.

**Blind prediction.**
- Q >= 1: about 0.83 (1.6 expected). Q = 0 (row 3): about 0.17. Q >= 3: about 0.2.
- Given Q >= 1, every Q event recovers: about 0.6.
- Row 1: about 0.05. Row 2 (harm): about 0.2. Row 4 (kill) among the rest: about 0.3. Row 5: about 0.1. Row 6: about 0.25.
- Mean wall about 100 s (EXP-064 100.0 s), 0 cap hits, the largest call count about 18.

## 5. What this does and does not license

**The screen can decide one of two things, and both are about recovery behaviour, not incidence.**
- **Kill:** row 4, the prompt-wording route "bare-path recipe plus a one-resend rule" for the applier's argument form on this tree. Row 3 kills nothing.
- **Promote:** row 5 only, and only **as a free rider**: the paragraph costs no GPU and no time, so it is carried inside the next E4B dev-48 arm that is run for another reason, and not run as its own arm. A standalone dev-48 arm cannot be justified from this screen: the event is about 0.2 per task-run (about 10 events in 48), the effect it can remove is 3 empties over 40 task-runs (below the MDE, plan.md section 5.5), and the 31B tree, the only carrier on the LB, has 0 quoted paths in 284 edits (critic). If a dev-48 endpoint is wanted, it is **non-recovered quoted events per quoted event, and empty patches caused by A or S**, with first-edit applies recorded and resolves not the endpoint; it needs the user's word and, above 1 GPU-h, a critic `prereg`.

**Does not license:** any resolve or LB claim, any upload or dev-48 run, a statement that fewer failed edits make a better fix, any claim that the recipe reduces how often the model writes a quoted path, or any claim about the 31B.

## 6. Exact commands

```
python tools/validate_submission.py experiments/EXP-069/candidate-argform --official --strict --json
python tools/pack_submission.py --src experiments/EXP-069/candidate-argform --out dist/EXP-069-argform.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed dist/EXP-069-argform.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-069-argform"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp069_argform/kaggle_eval_l4x4.ipynb
cp notebooks/exp068_read/kernel-metadata.json notebooks/exp069_argform/kernel-metadata.json   (then id and title changed)
kaggle kernels push -p notebooks/exp069_argform
```

Analysis, a separate job, after `kaggle kernels status` says COMPLETE: `kaggle kernels output rainm4/gemma4-exp069-argform -p runs/EXP-069-argform/`, flatten, `analyze_traces.py runs/EXP-069-argform --cap-minutes 8 --max-calls 45`, `run_forensics.py forensics` and `compare runs/EXP-064-loc runs/EXP-069-argform`, then Q, S, A, recovery, first-edit, empties and harm inputs by Grep and line reads of `traces/` (section 3).

## 7. Defects in this pre-registration, logged after the fact

1. **(Known at pre-registration.)** Section 1.2's list is from Grep patterns on the `filepath` line and line reads of 8 trace files, not a script over every `edit_file` call; a quote-wrapped path in a form the pattern missed (for example a backtick wrap) would be absent from the 8. The 21 versus the critic's 22 failed calls is one call not located.
2. **(Known at pre-registration.)** The "quote wrap rides with a malformed call" statement is shown for one trace (066 fastapi_14448 step 17) and only inferred for the other seven.
3. **(Known at pre-registration.)** The recipe is two sentences and a clause in one file (one concept: the filepath form and the one resend); if it shows an effect, the two parts are not separable.
4. **(Known at pre-registration.)** Row 2's `first-edit applies <= 4 of 8` and row 5's `Q >= 3` are chosen, not derived; they are bounds on behaviour at n = 8.
5. **(Known at pre-registration.)** The tree was built by `cp -r` plus edits; `tar` is outside this agent's commands, so no `git archive` repack was run.

## 8. Built (below the line; nothing above changes)

---

- **Changed files vs EXP-064 `candidate-loc`:** `prompts/applier.md` only (2 hunks).
- **Validator** (`--official --strict`): 1 error, the 18.00 h gate, demoted by `--skip-budget-gate`; 2 warnings carried; no new warning. The official validator could not be imported.
- **Pack:** `RESULT: VALID (0 errors, 3 warnings)`, PACK OK, 20 files, `dist/EXP-069-argform.zip` (gitignored). **sha256 `3892b1cd3278d7a10dbeee8d18e0f8fa75551a27de63b705f3bc462b1d1b7f60`.**
- **Pre-registration commit:** 1a3cf75 (this file, the candidate tree, the README row).
- **Notebook:** `notebooks/exp069_argform/` (commit 19d9914), built with the section 6 command; `kernel-metadata.json` is EXP-068's with only `id` and `title` changed, to `rainm4/gemma4-exp069-argform`. Nothing was copied to `out/submission.zip`.
- **Kernel id for the push:** `rainm4/gemma4-exp069-argform`, directory `notebooks/exp069_argform`. Kernel version 1.

## 9. Results (analysis job, 2026-11-11; sections 1 to 8 above are unchanged)

Kernel `rainm4/gemma4-exp069-argform` v1, COMPLETE. Kernel wall about 20.6 min (last log stamp 1233 s, about 0.34 GPU-h); agent wall 781.6 s over the 8 tasks. Output in `runs/EXP-069-argform/` (gitignored); `summary.jsonl` copied to `experiments/EXP-069/argform/summary.jsonl`; traces stay out of git. Commands as section 6 (`analyze_traces.py --cap-minutes 8 --max-calls 45`, `run_forensics.py forensics`, `compare runs/EXP-064-loc runs/EXP-069-argform`); Q, S, A, recovery, first edit, empties and the harm inputs by Grep and line reads of `traces/`.

### 9.1 Per task

| task | wall s | calls | compactions | edit_file calls / fails | first applier turn | first edit | resolved |
|---|---|---|---|---|---|---|---|
| requests_7309 | 62.9 | 6 | 0 | 1 / 0 | `edit_file` (step 14) | ok | no |
| requests_7205 | 64.3 | 4 | 0 | 1 / 0 | `edit_file` (step 13) | ok | no |
| fastapi_14448 | 104.8 | 11 | 1 | 1 / 0 | `edit_file` (step 19) | ok | no |
| fastapi_14301 | 47.6 | 4 | 0 | 1 / 0 | `edit_file` (step 13) | ok | **yes** |
| httpx_3672 | 201.8 | 23 | 2 | 10 / 8 | `edit_file` (step 19) | ok | no |
| fastapi_14605 | 177.2 | 13 | 2 | 7 / 5 | `edit_file` (step 15) | ok | no |
| rich_3468 | 60.7 | 6 | 0 | 1 / 0 | `edit_file` (step 14) | ok | no |
| rich_3006 | 62.3 | 7 | 0 | 1 / 0 | `edit_file` (step 16) | ok | **yes** |

Resolved 2 of 8 (fastapi_14301, rich_3006), the same two as EXP-064-loc; the compare shows 0 discordant pairs. Recorded, never an endpoint. Mean wall 97.7 s (EXP-064-loc 100.0 s); median 1.06 min; longest httpx_3672 at 201.8 s (under the 240 s naming line); largest call count 23 (httpx_3672). Empty patches 0 of 8 (reference 1 of 8). Cap hits 0, nudges 0, `scratch_in_patch` false on all. Compactions 5 (httpx_3672 2, fastapi_14605 2, fastapi_14448 1; EXP-064-loc: fastapi_14605 1, rich_3468 1). `n_undeclared_tool` 1 on every task (the root `submit_patch` artifact).

### 9.2 Q, S, A and recovery

- **Q (quote-wrapped `edit_file` filepath): 0 task-runs, 0 events.** All 23 `edit_file` calls (the forensics count) carry a bare `filepath`: Grep of `filepath` followed by a quote, backtick, `./` or `/` over the 8 traces found no match, and the sibling Python-repr signs of EXP-068/069 section 1.2 (quote-wrapped argument keys, fragment keys) are absent. The one `allow_multiple` key hit (fastapi_14605, 4) is a plain key, not a quote-wrapped one.
- **S (edit_file "Source path ... not found" with a quote): 0 per run** (references by run 2, 0, 6, 0, 4). The three "Source path ... not found" strings in the traces are the **reader's** `read_file` errors on httpx_3672 (a file `src/httpx/_servers.py` that does not exist, and two reads whose path swallowed `,start_line:251` / `,start_line:351`): `FileReadError`, no quote character, not `edit_file`, not S.
- **A (mandatory-parameter answer): 0** (`n_edit_arg_loss` 0 on all 8). A-or-S first-edit misses: **0 of 8** (reference 8 of 40, 1.6 per 8). First-edit applies: **8 of 8** (EXP-064-loc 6 of 8).
- **Recovery per quoted event: none to classify.** (i) to (v) are all empty. No applier `edit_file` call was answered by an A or S answer, so the one-resend rule's trigger never occurred.
- **Edit-failure empties: 0** (reference 5 of 40, 3 of them A+S). Empties 0 of 8.

### 9.3 Edit failures that did occur (descriptive, no row)

13 failed `edit_file` calls on 2 task-runs, all `FileEditError` "old_string not found" (the class the rule says goes to the next draft; the rule's resend clause is for A and S answers only).
- **httpx_3672: 8.** The first edit (step 19, draft 1) applied. Steps 20 to 23 are drafts 2, 3, 4, 5 in order, each failed, each followed by the next draft (rule followed, no resend; the drafts 2 and 3 OLDs carry `\\\"` escape runs copied from the reader's report, drafts 4 and 5 OLDs carry the lines `self.reset_state() # Assuming ...`: invented, not in the file). After a read of its own the applier wrote its own OLDs: steps 28, 29, 30 and 34 failed, step 33 applied; the applier then submitted a patch it said was only partly applied (patch non-empty, resolved no). Draft-sourced not-found failures 4, applier-own 4.
- **fastapi_14605: 5.** First edit (step 15, the `FastAPIDeprecationWarning` definition in `fastapi/exceptions.py`) applied. Steps 16 and 17 (drafts 2 and 3 on `temp_pydantic_v1_params.py`) failed, each followed by the next draft; after a read (step 18) its own OLDs failed at steps 19, 20, 21 and step 22 applied. Then `submit_patch` three times (the same redundant-submit pattern as EXP-068), `n_identical_repeats` 2 are those submits, not edit calls. Draft-sourced 2, applier-own 3.
- Draft-sourced not-found failures 6 on 2 task-runs (EXP-064-loc R1 reference 11 on 2); classified by the applier's own message and the call order, **not** by a line-by-line OLD-against-file check (EXP-067 method not re-run). No edit call was an identical resend of an earlier one. Resend after a no-match answer (the deviation of section 3): **0**.

### 9.4 Harm inputs

First applier turn is a tool call on **8 of 8** (an `edit_file` call, listed above; no task with a text first turn). `n_text_form_calls` 0, `tool_free` 0, applier text-form calls 0. Mean wall 97.7 s (limit 150 s). Cap hits 0. Empties 0. First-edit applies 8 of 8 (limit: 4 or fewer). The prompt is about 90 words longer than EXP-064; no harm to the applier's call form is seen at 23 of 23 well-formed `edit_file` calls. Compactions and the largest prompt: 5 compactions on 3 tasks; EXP-064-loc had 2 on 2 tasks (httpx_3672 now 2 against 0). The applier first prompt is not tabulated here.

### 9.5 Rows

- **Row 1 (infrastructure): did not fire.** No traceback or sandbox execution error in the kernel log, no compaction or summarizer `ValueError`, the root transferred to `pipeline` on 8 of 8, no blank or crashed run. The word "Traceback" in two traces is `TracebackType` inside a file read (rich_3468) and, in fastapi_14448 (step 20), the applier's own `run_command pytest` returning `CommandError` with 148 collection errors (`ModuleNotFoundError: dirty_equals`, `inline_snapshot`, the known test-only packages missing in the sandbox, EXP-035 section 9.3): a tool answer to a command the applier ran, not a harness or sandbox failure.
- **Row 2 (harm): did not fire.** Empties 0 (limit 3), no cap hit, mean wall 97.7 s (limit 150), no tool-free task, no applier text-form call, first turn is a tool call on 8 of 8 (limit: text on 2 or more), first-edit applies 8 of 8 (limit 4 or fewer).
- **Row 3 (not exercised): fires. Q = 0 task-runs.**
- Rows 4 to 6 are not read (row 3 is first-match). For the record the numbers could not have reached row 4 (no Q event, so no identical resend or empty submit after one), row 5 (needs Q >= 3) or row 6 on the Q count.

### 9.6 What row 3 licenses, plainly

**Row 3 says: no decision for this form, and the form is not killed.** It does not promote. Promote is row 5 only, and row 5 needs 3 or more quoted events, all recovered; there were none. No effect of the paragraph is claimed or read. In particular the 0 quoted events, the 0 S, the 8 of 8 first-edit applies and the 0 empties are **not** read as the recipe working (section 4, "Not rows, but binding": the event is about 0.2 per task-run and the same 8 tasks drew 0 events at P about 0.17 under that rate; a lower number than the reference is not evidence). The applier hunk (two sentences and a clause in `prompts/applier.md`) is neither shown to help nor shown to hurt on this tree (harm inputs clear on 8 tasks). On D-009's two-rounds rule: round 2 is read as "not exercised", which ends this form's screen. EXP-069 does not keep its form as a promoted change; the base for later rounds stays the EXP-064 `candidate-loc` tree, and the argform hunk may ride as a zero-cost free rider in a later arm run for another reason but with no support from this screen beyond "no harm seen on 8 tasks". Repeating it would need a tree that draws quoted paths often enough (a draw of 3 or more events at 0.2 per task-run needs about 15 task-runs for even odds), which the dev-48 free-rider route would give without its own slot.

### 9.7 Blind prediction check

Q >= 1 (about 0.83): **did not hold** (Q = 0; the 0.17 outcome). Row 3 (about 0.17): held. Row 1 (about 0.05) and row 2 (about 0.2): did not fire. Mean wall about 100 s: 97.7 s, held. 0 cap hits: held. Largest call count about 18: 23 (httpx_3672), not held (within the 45 bound).

### 9.8 For the next round (lessons-ready)

The applier's argument-form fault that EXP-061 to EXP-066 saw (a quote-wrapped `filepath` on the first edit, 8 of 40 task-runs) did not appear on any of the 8 applier sessions here, and no A answer appeared either, so the one-resend rule was never tested; what the screen shows is an incidence of 0 of 8, which 0.2 per task-run draws about one time in six, and a paragraph cannot be credited for it. The edit failures that did occur (13 on httpx_3672 and fastapi_14605) are content-class, the OLD not being in the file, and are the draft-copy and applier-copy faults of EXP-067 and EXP-068, not argument form: 6 of 13 are drafts copied from the reader's report with escape runs or invented lines, 7 are the applier's own OLDs after a read. The applier followed the "no match, next draft" rule and made no identical resends. D-009's class S and A therefore leaves round 2 without a reading, and the content-class failure (the OLD that does not match) is the one that remained visible on this tree, as on EXP-068 where the same failure came from the drafter window.

### 9.9 Defects and limits of this analysis

1. Q = 0 by Grep of the `filepath` text of all 8 traces; a quote form the pattern did not cover (for example a wrap in the argument key rather than the value) would be missed. The key-form Grep found none.
2. R1-type failures (draft-sourced) are classified by the applier's messages and call order, not by a line-by-line OLD-against-file check; F, G and G1 were not computed (descriptive, no row).
3. "Draft skipped that would have applied" was not checked draft by draft; the only draft the applier skipped without trying is none (every draft on httpx_3672 and fastapi_14605 was tried in order).
4. The 8 tasks are a reader-variable draw (EXP-061, 062, 066): the first-edit 8 of 8 against 6 of 8 is one-run reader variation in the first place and is not read.

## Status

**2026-11-11 ANALYZED**: kernel COMPLETE. Row 3 (not exercised): Q = 0 task-runs, 0 quote-wrapped `edit_file` filepaths on 23 of 23 calls, S 0, A 0. Rows 1 and 2 clear (first-edit applies 8 of 8, empties 0, mean wall 97.7 s, 0 caps, first applier turn a tool call on 8 of 8). No decision, form not killed, not promoted. Section 9 above.

2026-11-10: pre-registered (1a3cf75), candidate packed with sha `3892b1cd...b7f60`, notebook built (19d9914). **Pushed 2026-11-10**: kernel version 1, `rainm4/gemma4-exp069-argform`, first status RUNNING. Next, when the lead reports COMPLETE: `kaggle kernels output rainm4/gemma4-exp069-argform -p runs/EXP-069-argform/`, flatten, then the analysis in section 6, then apply section 4.
