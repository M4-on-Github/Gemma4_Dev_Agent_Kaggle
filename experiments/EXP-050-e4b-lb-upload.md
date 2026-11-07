# EXP-050 — An LB upload of the E4B single loop, for the small-model bonus line

**Date:** 2026-11-07
**Type:** LB-only upload (#14 if used), zero GPU. One draw of 58, with no kernel. Two packed variants; the lead's S-014 names one, and the user approves it by sha.
**Cohort:** n/a (public LB, 58 tasks)
**Ladder:** L3 (LB upload). The rung below is EXP-038 (L4, dev-48, the exact bytes of variant A). Its accepted critic review (`experiments/EXP-038/critic.md` item 4, d1d78a2) makes an E4B upload proposal admissible, subject to the four items in section 2.3. No lower rung can read what one LB draw reads: the hidden-set score of the E4B tree, and whether it completes inside 12 h.
**Pre-registered:** this file is committed **before** any upload. Sections 3 to 5 are written blind and are not revised after the score. A badly drafted reading gets its defect logged in section 7, not rewritten. **This is an option, not a decision:** if no upload happens, the file stays at "pre-registered, not uploaded" and nothing below is read.
**Serves:** the small-model bonus line (topic 751104, `research/kaggle/threads/kg-751104-small-model-prize.md`); C-020 (the E4B runs the v24 single loop well inside the clock); the paper track (a board figure for a small model).
**Supersedes / relates:** EXP-033 (the E4B tree, smoke-8), EXP-038 (the same zip on dev-48, plus the CPU re-grade), EXP-027, EXP-029 and EXP-031 (the 31B v24-at-8 draws and the pooling rule), plan.md 5.5 (MDE about 4 tasks), plan.md 5.8 (the budget rule and its overrides).
**Tags:** [V] verified in source, a run directory, or a committed EXP section, with file:line or section; [I] inference or arithmetic.

## 1. Why this, now

- **The user is leaning towards an E4B upload for the 2026-11-07 UTC slot,** which is free until 23:59 UTC.
- **The board effect.** The LB keeps each team's best upload (0.18 = 11/58, `submissions.md` row 12). An E4B draw therefore cannot lower the main-track standing. It spends the day's slot.
- **What EXP-038 measured on dev-48, with variant A's bytes** (section 9) [V]:

  | Measure | Value |
  |---|---|
  | Resolved | 5 of 48 |
  | Paired against the 31B Arm R | 4-0 against the E4B, McNemar p 0.125 |
  | Mean task wall | 85.7 s |
  | Max task wall | 207.3 s |
  | Tasks at a cap | 0 of 48 |
  | Projection for 120 tasks (E7) | 2.98 h, against the 10.5 h rule |
- **The bonus.** It goes to the highest-ranking submission whose base model is E2B or E4B, scored on the private set. **It counts only if this submission is one of the team's two selected final submissions** (topic 751104, `kg-751104-small-model-prize.md:17-18`) [V].
  - So an E4B entry for the bonus costs one of the two final-selection slots, which then cannot hold a 31B tree.
  - The host notebook also states that teams with no eligible submission are dropped from the private small-model leaderboard (`kg-751104-small-model-prize.md:21`) [V]. This upload would give the team an eligible submission.
- **What counts as an E4B entry.** No host text defines it (`kg-751104-small-model-prize.md:36`) [V for the gap]. This tree is a single `LlmAgent` whose only model is the E4B, with no sub-agents and no adapters, so any definition covers it [I].
- **The last stored small-model standings** (2026-10-20, stale) top out at 0.06, about 3.5 of 58 (`kg-751104-small-model-prize.md:20`) [V for the stored output].

## 2. Design

### 2.1 The two variants

| Variant | Tree | `eval_config` (timeout / calls / minutes / turns) | zip | sha256 | Packer gate |
|---|---|---|---|---|---|
| **A** | `experiments/EXP-033/candidate-e4b`, unchanged since d2c11da | 240 / 28 / **8** / 80 | `experiments/EXP-050/variant-a-e4b-8min.zip` (gitignored), 2,493 B | **`9de869bd2cd8853b72d653d06b9acef3e03794c8b588c26494435774dda11ac0`** | 120 x 9 min = 18.00 h: **exceeds**, needs the section 2.3 override |
| **B** | `experiments/EXP-050/candidate-e4b-4p5`, built from the EXP-033 tree's HEAD blobs by `experiments/EXP-050/make_candidate_b.py` (one anchored edit, matched once), committed at d99a116 | 240 / 28 / **4.5** / 80, with a dated EXP-050 comment on the changed line | `experiments/EXP-050/variant-b-e4b-4p5min.zip` (gitignored), 2,666 B | **`1733ec5480744298ea7b5aa4459df34d0e3d084476d7845c96fd414b57d262fd`** | 120 x 5.5 min = 11.00 h: **passes**, no override |

**Members** (name, size, sha256 of the member):

| Member | A | B |
|---|---|---|
| `agent.yaml` | 472 B, `a14d765a...a0f4` | identical |
| `configs/sampling.yaml` | 129 B, `63005688...c3f6` | identical |
| `eval_config.yaml` | 94 B, `916cf6cb...c531` | 360 B, `e87b4d5b...f29e` (only `max_time_minutes` and its comment differ) |
| `prompts/system.md` | 3,162 B, `57a20af4...8041` | identical |

The model in both is `gemma-4-e4b-it-qat-w4a16-ct`. Sampling is temperature 1.0, top_p 0.95, top_k 64, max_output_tokens 8192 and thinking budget 4096, with the six harness tools.

**Byte identity of A with what EXP-038 ran.** The `SUBMISSION_B64` embedded in `notebooks/exp038_e4b_dev48/kaggle_eval_l4x4.ipynb` decodes to sha256 `9de869bd...1ac0`, with the same four member hashes as A. The notebook's own sha256, `e58af838...eb66`, equals EXP-038's record (EXP-038 section 8 line 455). It was read by `out/exp050_embedded_sha.py`, which parses the JSON and executes nothing [V].

**Reproduction from committed LF blobs** (EXP-022 R9):
- `git ls-files --eol` gives `i/lf w/lf` for every file of both trees.
- `git -c core.autocrlf=false archive HEAD` of both trees, repacked from `out/exp050_repro/`, gives the same two sha256 values [V].

**Validator, `--strict`, on each zip:**
- A: INVALID, with 1 error (the 18.00 h gate) and 1 warning (`timeout_seconds` 240 < 300).
- B: VALID, with 0 errors and the same 1 warning.

The warning is moot on the scorer, where the verification timeout is fixed at 300 s (`data/raw/HARNESS_README.md:560`). It is the same warning EXP-038's zip carried. The `--official` validator is not importable on this machine [V].

**Pack commands:**
- A: `--skip-budget-gate --allow-warnings`, as EXP-038 packed it.
- B: `--allow-warnings` only, for the timeout warning. The gate itself passes.

### 2.2 Is `max_time_minutes` visible to the model? **Yes.** So variant B is an untested config.

| Channel | Shows a time figure? | Source |
|---|---|---|
| Task message (the first user turn) | **Yes.** `build_agent_prompt` adds a "Task Budget" section with a time-allowance line carrying `config.budget.time_minutes`, beside the call and turn allowances | `swegemma/harness/agent_runner.py:339-352` (lines), `:385-390` (section appended), `:700` (call site); `HARNESS_README.md:318-321` [V] |
| Our own prompt (`prompts/system.md`, the system instruction) | **Yes, a fixed 8.** Its budget section states 28 tool calls and 8 minutes. Variant B leaves this line unchanged | `experiments/EXP-033/candidate-e4b/prompts/system.md:5-6` [V] |
| `get_status` tool result | **Yes.** It returns the seconds remaining, `max_time_minutes` and the agent's elapsed seconds | `swegemma/tools/execution.py:137-140`; `HARNESS_README.md:415-427` [V] |
| Tool error at the clock | **Yes.** It names the cap in minutes when a tool is refused after time is up | `swegemma/context.py:527-546` [V] |
| `run_command` timeout | Not shown as text. The per-command timeout shrinks to the time remaining | `HARNESS_README.md:389` [V] |
| Continuation nudges | **No.** The three nudge texts carry no time figure | `agent_runner.py:983-1001` [V] |
| Low-budget warning | **No time figure.** It counts tool calls only, at 10 or fewer remaining | `swegemma/tools/base.py:47-69` [V] |

**What the EXP-038 traces show.** These are counts only, from `out/exp050_time_visibility.py` over the 48 traces under `runs/EXP-038-e4b-dev48/traces` [V]:
- **48 of 48** task messages carry the harness time-allowance line, with the value 8.0.
- **48 of 48** system steps carry our prompt's budget line, with the value 8.
- 1 of 48 tasks called `get_status` (1 call). That is the one task where a time-remaining field appears in model-visible text.
- 0 of 48 traces carry the harness time-exhausted message.

**Consequence, stated plainly.**
- **Variant B is an untested config.** Under B, the model's task message would state a 4.5-minute allowance, while its system prompt still states 8 minutes. No run on record has shown the E4B that text, or that contradiction.
- **The clock itself would likely not bind.** The longest EXP-038 task wall was 207.3 s, under B's 270 s cap [V EXP-038 section 9]. So no dev-48 task would have been cut, had the model behaved the same [I].
- **Whether it behaves the same is not measured.** For example, it might stop earlier because the stated allowance is shorter. B's score would therefore be one draw of an untested config. It could not pool with A or be read as a draw of EXP-038's tree.
- **Variant A is the config EXP-038 measured, byte for byte.**

### 2.3 The four items the critic required (EXP-038 critic item 4, d1d78a2)

1. **The plan.md 5.8 override, written out (variant A only).** The rule "never submit a config that has not run on dev-48 with projected worst case at most 11 h" is overridden knowingly, as for #11 (EXP-027 section 2) and #12-#13 (EXP-031 section 2).
   - **The worst cases.** The packer's formula gives 120 x (8 + 1.0) min = 18.00 h. `analyze_traces` gives a worst case of 16.00 h (EXP-038 section 9, E9). `estimate_budget --results` reports 7.77 h with verdict BLOCK; that figure is the script's own model, not read (EXP-038 section 3.1 amendment; critic item 6) [V].
   - **Justification, in order of weight:**
     - (a) EXP-038 measured this exact zip on dev-48: 0 of 48 at a cap, mean 85.7 s, max 207.3 s, projected 2.98 h. That meets the operational 10.5 h rule (C-008) with about 7.5 h to spare [V].
     - (b) Even if every hidden task ran as long as the longest dev-48 task, 120 x 207.3 s is 6.9 h, plus about 0.12 h of measured overhead (444.8 s, EXP-038 line 92) [I, arithmetic on V numbers].
     - (c) A timeout zeroes this slot only. The LB keeps the team's best, 0.18.
   - **Variant B needs no override.** The packer gate passes at 11.00 h. `estimate_budget --results` against EXP-038 reports a mean of 6.77 h, a worst case of 9.25 h and verdict PASS. That model is not read, for the same reason as above.
2. **A predicted k of 58:** section 4.1.
3. **The re-grade's F and G (EXP-038 section 9, lines 472-473)** [V]:
   - Fault row F did not fire: the CPU re-grade reproduced the kernel's gold and base grades.
   - G = 0 of 15: no E4B failure on dev-48 was the missing-test-package grading gap. So vendoring is not a priority for this tree.
4. **fastapi_13537, a resolve risk (not a clock risk).**
   - **What happened.** It is one of the 4 dev-48 tasks Arm R resolved and the E4B did not. The E4B wrote its tool calls as text inside fenced blocks after continuation nudges, made 0 tool calls, never edited, and ended without `submit_patch` after 19.6 s (EXP-038 section 9, line 579; critic analysis) [V].
   - **Why no count shows it.** `analyze_traces` counts 0 malformed calls in 478 because it does not see this failure. The same failure on a hidden task costs that task and nothing on the clock.
   - **Its rate.** One task in 48 on dev-48. Its rate on the hidden set is unknown.

**Cost: 0 GPU-h, and one upload slot** (the 2026-11-07 slot if used). The final-selection cost is in section 1. If the upload lands on a later day, these readings still govern, provided the zip has the same sha and no other draw of it has been scored in between.

**Upload path.**
1. The lead writes S-014 and names A or B by sha.
2. The critic reviews it (`prereg`, an upload).
3. The user writes `approvals/S-014.txt` with that sha.
4. The submitter uploads it under the filename `submission.zip`.

Nothing under `knowledge/` or `approvals/` is written by this experiment. The pending `submissions.md` row is written once the variant is named, since it carries one sha.

## 3. Endpoints, fixed in advance

1. **Primary:** k, resolved of 58 on the public LB (score x 58), for the uploaded variant.
2. **Completion:** whether the submission scores, against Notebook Timeout or an error.
3. **Comparators:**
   - the prediction in 4.1;
   - the 31B v24-at-8 pooled baseline, 28 of 174 over three byte-identical draws, a per-draw mean of 9.33 of 58 (Wilson 95% 0.114 to 0.223; EXP-031 section 9) [V];
   - the board MDE of about 4 tasks for one draw (plan.md 5.5) [V].
4. **Pooling** (EXP-031 section 3, binding):
   - Only byte-identical zips pool. A draw of A pools only with later draws of `9de869bd`, and B opens its own count.
   - A blank is not k = 0. It is recorded as a failed completion.

## 4. Pre-registered readings. Written blind. Not to be revised after the score.

### 4.1 Predicted k (the critic's item 2)

**Basis, restating the lead's arithmetic with the numbers recomputed:**
- The E4B dev-48 rate is 5/48 = 0.104.
- The 31B's ratio of board rate to dev-48 rate on the same tree is (28/174) / (9/48) = 0.161 / 0.1875 = 0.858.
- So the E4B board rate is 0.104 x 0.858 = 0.089, which is **5.2 of 58, so k = 5**.
- **Interval.** The Wilson 95% interval on 5/48 is 0.045 to 0.222. Scaled by the same ratio, that is 2.3 to 11.0 of 58, so **2 to 11**. The lead's "roughly 2 to 10" is corrected to 2 to 11 at the top. Without the ratio it is 2.6 to 12.9.
- **Inputs not counted.** One draw also carries binomial noise on 58: at p = 0.09, the sd is about 2.2 tasks. So the realized interval is somewhat wider. The ratio itself rests on one tree and on three draws.

**Prediction: k = 5, 80% interval 2 to 9.** Probabilities by the rows below: row 0, 3%; row 1, 10%; row 2, 50%; row 3, 36%; row 4, 1%.
- Row 0 is low because the clock is not the constraint for this tree (section 2.3, item 1).
- The same probabilities apply to B. B's untested prompt-cap contradiction adds risk in an unknown direction, which is not modelled.

### 4.2 Readings (first matching row governs)

| # | Outcome | Reading |
|---|---|---|
| 0 | **Blank, Notebook Timeout, or a scoring error** | A failed completion, not k = 0. **For A** it contradicts EXP-038's time profile (2.98 h). The next E4B upload is B, or A after a forensic read of what differs on the hidden set; A is not re-uploaded as is. **For B** it is an infrastructure or format failure. In either case C-020's "well inside the clock" gets a contrary observation, recorded for the critic. The small-model line still has no scored entry |
| 1 | **k ≤ 1** | Below the predicted interval. The E4B tree on the hidden set is weaker than dev-48 suggests, or format failures like fastapi_13537 cost more tasks there. This draw is the small-model reference, at its value. No E4B tree goes to a final-selection slot on this draw alone. The next E4B step is a change tested on dev-48 or smoke-8 first, not a re-draw |
| 2 | **2 ≤ k ≤ 5** | Inside the predicted interval, and at least 4 tasks (the MDE) below the 31B's per-draw mean of 9.33. On one draw, the E4B trails the 31B by at least the MDE on the board, which agrees in direction with dev-48 (4-0). This is the small-model baseline: any later E4B tree is read against it, and against later draws pooled under section 3 item 4. Whether it holds a final-selection slot is a user decision, given section 1 |
| 3 | **6 ≤ k ≤ 13** | No board difference from the 31B can be read: \|k - 9.33\| < 4, within one MDE. k = 12 or 13 is above the predicted interval (row 3 still governs). No claim that the E4B equals the 31B, and no claim either way; one draw against a three-draw pool. It is the small-model baseline as in row 2. A second draw of the same bytes is the only way to tighten it, and it is not licensed here |
| 4 | **k ≥ 14** | Above the 31B pool's 95% upper bound (0.223 x 58 = 12.9) and more than one MDE above its mean. Recorded as a surprising draw, with no effect claim. Before any E4B tree is preferred over the 31B on this basis, a second draw of the same bytes must land at 10 or above |

**For variant B, every row applies with one addition.** The draw is of an untested config (section 2.2). It cannot be read as a board figure for EXP-038's tree, and it does not pool with A.

## 5. What this does and does not license

**It licenses:**
- one board draw of one E4B zip;
- a scored entry on the small-model line;
- one completion, or not, of the E4B tree on the hidden set, recorded against C-020;
- for A, the first board figure for a config measured on dev-48;
- the choice of the next small-model step, per section 4.2.

**It does not license:**
- any claim that the E4B and the 31B differ, or are equal, from a single-draw gap below the MDE;
- any claim about why a draw is high or low;
- any use of B's score as a measure of A's tree;
- changing a reading in EXP-038 or EXP-031;
- the final-selection decision, which is the user's.

## 6. Exact commands

```
python -I -X utf8 experiments/EXP-050/make_candidate_b.py
python tools/validate_submission.py experiments/EXP-050/candidate-e4b-4p5 --strict
python tools/pack_submission.py --src experiments/EXP-033/candidate-e4b --out experiments/EXP-050/variant-a-e4b-8min.zip --skip-budget-gate --allow-warnings
python tools/pack_submission.py --src experiments/EXP-050/candidate-e4b-4p5 --out experiments/EXP-050/variant-b-e4b-4p5min.zip --allow-warnings
python tools/validate_submission.py experiments/EXP-050/variant-a-e4b-8min.zip --strict
python tools/validate_submission.py experiments/EXP-050/variant-b-e4b-4p5min.zip --strict
python -I -X utf8 out/exp050_embedded_sha.py notebooks/exp038_e4b_dev48/kaggle_eval_l4x4.ipynb experiments/EXP-050/variant-a-e4b-8min.zip experiments/EXP-050/variant-b-e4b-4p5min.zip
git -c core.autocrlf=false archive HEAD experiments/EXP-033/candidate-e4b experiments/EXP-050/candidate-e4b-4p5 | tar -x -C out/exp050_repro
python tools/pack_submission.py --src out/exp050_repro/experiments/EXP-033/candidate-e4b --out out/exp050_repro/a.zip --skip-budget-gate --allow-warnings
python tools/pack_submission.py --src out/exp050_repro/experiments/EXP-050/candidate-e4b-4p5 --out out/exp050_repro/b.zip --allow-warnings
python -I -X utf8 out/exp050_time_visibility.py runs/EXP-038-e4b-dev48/traces
python tools/estimate_budget.py --eval-config experiments/EXP-050/candidate-e4b-4p5/eval_config.yaml --results runs/EXP-038-e4b-dev48/summary.jsonl
# before upload, the submitter: sha256sum of the approved zip, copied to a file named submission.zip
```

`out/` scripts are untracked working files. Their outputs are the counts recorded in section 2.

## 7. Defects in this pre-registration, logged after the fact

None yet.

---

## 8. Built and uploaded (filled at upload time; nothing above changes)

**Built 2026-11-07.** Both zips are packed and verified as recorded in section 2.1. B's tree and builder were committed at d99a116, and this file is committed after them. Not uploaded.

## Status

PRE-REGISTERED, NOT UPLOADED (2026-11-07). Waiting on S-014, written by the lead, which names A (`9de869bd...1ac0`, override in section 2.3) or B (`1733ec54...62fd`, untested config). Then the critic `prereg`, then the user's approval. After the score: append section 9, applying section 4.2.
