# R-012: synthesis after R-011 (zero GPU)

2026-11-20. This round runs no draws. It answers one question: after R-001 to R-011, where is reachable headroom
left for each model on cdev2-79?

Inputs:
- `runs/_analysis/trace_vs_reference.jsonl`, regenerated over all 6,278 draw rows by `tools/trace_vs_reference.py`.
- The current bases:
  - 31B: R-008 d1/d2 and R-011 d3/d4, 4 draws.
  - E4B: R-011 Turing scale-5 base, 8 draws, and the reviewer arm, 8 draws.

The analysis scripts were one-off and are not kept (the review's own recount scripts are not kept either; see below). Every number below is a count over those rows and traces.

## Headline

- **The 31B's reachable pool is small.**
  - 20 tasks are solved in all 4 draws, 16 in 1-3 draws, and 43 in none.
  - Only 6 of the 43 have been solved by any draw of either model in the whole ledger.
  - The unresolved draws on the 16 noisy tasks total 31, which is 7.75 per draw. A process lever reaches at most
    that, and realistically a fraction of it.
- **The E4B's ceiling is set by the tasks it can solve at all.**
  - Over 16 draws, only 20 of 79 tasks were ever resolved.
  - On tasks whose reference patch has 3 or more hunks, it resolved 0 of 216 base draws.
  - The 31B resolves some draw of 22 of the tasks the E4B never solves. [Review: 17 against the 31B's 4 base draws;
    22 counts any 31B draw in the ledger.]
- **The E4B's edit failures are a fidelity limit, not a prompt problem.**
  - 48-71% of its `edit_file` calls fail in every E4B arm since R-000, including the edit-rules arm R-002.
  - Of 812 "old_string not found" failures in the R-011 base:
    - 4 were whitespace-only mismatches;
    - 173 strung together lines the agent had read, but not as contiguous text;
    - 357 contained mostly lines it had read;
    - 247 were mostly lines it had never read.
  - The agent paraphrases code instead of copying it.
- **The 31B's own check predicts its result; the E4B's does not.**

  | Draw state at the end | 31B draws | 31B resolved | E4B draws | E4B resolved |
  |---|---|---|---|---|
  | check after the last edit passed | 138 [was 142, corrected in review] | 92 (67%) | 47 | 5 (11%) |
  | check after the last edit failed | 18 [was 19] | 3 (17%) | 282 | 34 (12%) |
  | edited, no check after the last edit | 83 | 13 (16%) | 224 | 17 (8%) |
  | no successful source edit | 77 | 5 (6%) | 79 | 0 (0%) |

  The 31B table is confounded by task difficulty; easy tasks both pass checks and resolve. Even so, the E4B's
  checks carry no signal, so any "iterate until your check passes" lever is empty for it.

## 31B: how the unresolved draws end

| Task group | Unresolved draws | Largest end x class cells |
|---|---|---|
| noisy (1-3 of 4) | 31 | time cap, no edit 6; submitted, wrong region 4; call cap, no edit 4; submitted, wrong file 3; edit-tool failure 4 (call cap 2, time cap 2) |
| never (0 of 4) | 172 | time cap, no edit 34; partial fix 58 (submitted 27, time cap 17, call cap 14); wrong file 33; wrong region 21 |

- **Late commitment, again.**
  - Resolved draws make their first edit at a median call of 9.
  - Unresolved draws make it at call 14-15.
  - Unresolved draws use a median of 23 calls and 448 s, against 14 calls and 241 s for resolved ones.
- **Malformed edit calls.**
  - 516 of 1,065 31B `edit_file` calls fail with missing mandatory parameters, in 68 of 316 draws.
  - [Review: all 516 lack `old_string`; 228 carry no stray keys, and in the other 288]  part of the code text arrives as an
    argument name, so the tool-call arguments were split.
  - These calls cost 5,723 s over 316 draws.
  - On the noisy tasks, 9 of the 31 unresolved draws have at least one malformed edit, and 3 of those ended at a
    cap.
  - So a fix reaches about 1 task per draw at most.
  - T-31b-008 (scripted replace after a failed edit, R-004) cut garbled-turn seconds by about 70%. It scored 10.0
    on the old screen lane but missed its endpoint. It was never drawn on the current lane.

## E4B: how the unresolved draws end (base, 8 draws)

| Task group | Unresolved draws | Largest end x class cells |
|---|---|---|
| noisy (17 tasks) | 88 | edit-tool failure 23; wrong region 20; all hunks touched, wrong change 18; wrong file 17 |
| never (61 tasks) | 488 | wrong file 169; partial fix 107; wrong region 102; all hunks touched, wrong change 41; edit-tool failure 40 |

- Draws with at least one failed edit resolve 5% of the time (14 of 294), against 12% without (42 of 338).
- The time cap is no longer a factor at scale 5 (2 of 632).

## What is left (ranked)

| # | Model | Lever | Reachable | Cost | Comment |
|---|---|---|---|---|---|
| 1 | 31B | T-31b-008 re-screen on the current lane: scripted `str.replace` after a failed `edit_file` | at most ~1 task/draw | 2 screen draws, about 1.3 Ada GPU-h | The only near miss with a measured mechanism. Its effect is likely under what a 2-draw screen can see; an L2 pair would need about +3. |
| 2 | E4B | B5: thinking budget 4096 -> 8192 | unknown | 8 + 8 Turing draws, or 2 + 2 Ada | The last open E4B backlog row. Nothing in the traces points at thinking as the limit. |
| 3 | both | LoRA adapter (`adapter:` is an allowed agent key) | the only lever aimed at model ability: copy fidelity, localization, multi-hunk fixes | training compute and a data decision | In "Later" since R-000. The data rule there is "public data only unless the user says otherwise". There are Kaggle threads on LoRA uploads: `../research/kaggle/threads/kg-755677-*` and `kg-758968-*`. |
| 4 | both | Stop tuning the cluster base. Write R-001 to R-011 up as a negative result for the paper track. | - | none | Eleven rounds of prompt, sampling and structure levers moved neither model beyond draw noise. |

Dropped from consideration by this synthesis:
- An E4B "iterate until your check passes" rule: its checks carry no signal.
- More E4B edit-rule prompts: five arms, no change in the failure rate.
- Graph tools: C-012, they lose to grep.
- A 31B "check before submit" rule: it is confounded with difficulty, and late commitment is the binding limit.

## Independent review (2026-11-20)

A Fable reviewer at xhigh effort re-derived the numbers from `trace_vs_reference.jsonl` and the traces. It ran
read-only and used no GPU. The user's instruction was to proceed with rows 1-3 if the reviewer approved them.

Corrections. The 31B check table is fixed in place above (138/92 and 18/3; recounted here too). Other corrections:
- The E4B not-found classes were recounted over 808 failures; the synthesis's 812 sums to 781. The recount:
  - 88 stale: the text was already replaced by the agent's own earlier edit;
  - 31 whitespace-only;
  - 118 lines it had read, but not contiguous;
  - 306 mostly lines it had read;
  - 265 mostly lines it had never read.

  Single-line `old_string`s still fail 41%. "Paraphrases" is too strong: a tenth of the failures are stale edits,
  and a third are anchors the agent never read.
- The 31B check signal is a difficulty artifact. On the 16 noisy tasks, a passed check resolves 24 of 35 draws and
  an edit with no later check resolves 8 of 10.
- The E4B check never focuses. 268 of 414 pytest calls target a directory or the whole suite. 223 of 236 failing
  outputs are cut near 5 kB with no summary line. It wrote 1 script check in 632 draws, against 665 for the 31B in
  316. The research ledger already tried focused-check levers (EXP-055/056/057/072/073), with no gain.
- The malformed-edit ceiling is about 0.5 task per draw (90% CI -1.3 to +0.35), not 1. Same-task draws with 3 or
  more malformed calls resolve 4.8 pp less than clean ones over 30 tasks, at 10.5 such draws per cdev2-79 draw.
- "Never" is not a hard ceiling. Four of the 6 ledger-solved never tasks are solved by other 31B draws, at 3-7 of
  13-29 draws each.
- Ladder power:
  - L1 promotes a null arm 15% of the time at the +1.5 bar, against 25-37% for a true +0.5 to +1 (pooled screen SD
    1.46).
  - L2 at 2 draws per arm has 26% power at a true +2 if SD is 1.8.
  - The 31B base SD of 1.26 (4 draws) is probably low; the per-task binomial floor is 1.79.

Verdicts on "What is left":

| # | Verdict | Reason |
|---|---|---|
| 1 | REJECT | The fourth test of an idea the research ledger marks refuted: `../knowledge/claims.md` C-005; EXP-028 compliance 0/6, 10 vs 9 of 48; upload #10 scored 6/58. In S-004 a scripted replace followed only 4 of 28 malformed calls. An L1 screen holds 8 of the 16 noisy tasks, so it cannot see the effect. An L2 test needs 14-29 draws per arm for +1. |
| 2 | REJECT, closed at L0 | 67 of 7,378 E4B turns reach 4,096 thinking tokens. The 79 task-draws with a 3,900+ turn resolve 2; lifting them to the cohort rate gives about +0.7 per draw, against an 8v8 MDE of 1.4. 8192 equals `max_output_tokens`. |
| 3 | APPROVE WITH CHANGES: stage 0 desk only | The repo already knows: E4B adapters load on the harness vLLM path (EXP-047/054/058, C-013, C-024). An exact-copy adapter failed its drift gates and decoded 17-25% slower, and C-024 caps its gain at 1 of 48. Stage 0 gates as read today: budget fails for the 31B (10.04 h x 1.17 = 11.7 h); pool fails (nothing worth +3); feasibility partial (no peft, no BF16 parent, the 31B handle is unverified). Stage 1, a <=0.5 Ada GPU-h canary with the organisers' zero-B sample adapter, needs those gates to pass. |

Outcome: no GPU job was started. Row 4 (stop) is the reviewer's first alternative. Its second is one composed 31B
arm of the positive-point-estimate levers at 8v8 on cdev2-79, about 25 GPU-h, which it ranks below stopping. It
also recommends fixing the ladder before any further lever: drop the L1 resolve bars and size L2 from SD 1.8 or
more. The paper outlet for row 4 needs the user: the Writeup was declined (`../knowledge/plan.md:159`).
