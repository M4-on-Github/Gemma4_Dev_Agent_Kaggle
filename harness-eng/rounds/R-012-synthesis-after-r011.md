# R-012: synthesis after R-011 (zero GPU)

2026-11-20. This round runs no draws. It answers one question: after R-001 to R-011, where is reachable headroom
left for each model on cdev2-79?

Inputs:
- `runs/_analysis/trace_vs_reference.jsonl`, regenerated over all 6,278 draw rows by `tools/trace_vs_reference.py`.
- The current bases:
  - 31B: R-008 d1/d2 and R-011 d3/d4, 4 draws.
  - E4B: R-011 Turing scale-5 base, 8 draws, and the reviewer arm, 8 draws.

The analysis scripts were one-off and are not kept. Every number below is a count over those rows and traces.

## Headline

- **The 31B's reachable pool is small.**
  - 20 tasks are solved in all 4 draws, 16 in 1-3 draws, and 43 in none.
  - Only 6 of the 43 have been solved by any draw of either model in the whole ledger.
  - The unresolved draws on the 16 noisy tasks total 31, which is 7.75 per draw. A process lever reaches at most
    that, and realistically a fraction of it.
- **The E4B's ceiling is set by the tasks it can solve at all.**
  - Over 16 draws, only 20 of 79 tasks were ever resolved.
  - On tasks whose reference patch has 3 or more hunks, it resolved 0 of 216 base draws.
  - The 31B resolves some draw of 22 of the tasks the E4B never solves.
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
  | check after the last edit passed | 142 | 96 (68%) | 47 | 5 (11%) |
  | check after the last edit failed | 19 | 3 (16%) | 282 | 34 (12%) |
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
  - In 228 of them `old_string` is absent. In others, part of the code text arrives as an argument name,
    so the tool-call arguments were split.
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
