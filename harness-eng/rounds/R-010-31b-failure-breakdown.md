# R-010 (31B): where the base's failing draws lose, and what the next round should target

Zero-GPU analysis, 2026-11-19. This is not a tweak, and no promotion rule applies. Approved by the user on
2026-11-19 ("go ahead").

- **Draws read:** `runs/R-008-31b-base-te-d1` (28/79) and `-d2` (27/79) on `cohorts/cdev2-79.txt`, with task
  envs on. That is 158 task-draws, 103 of them unresolved.
- **Per-task rows:** `runs/_analysis/failure_breakdown.R-010.jsonl`. The ledger it reads is
  `runs/_analysis/trace_vs_reference.R-010.jsonl`, a fresh `tools/trace_vs_reference.py` run with 4774 rows,
  907 of them 31B draws from 24 runs. Both files are gitignored.
- **Command** (from `harness-eng/`):

  ```
  python3 -I tools/failure_breakdown.py runs/R-008-31b-base-te-d1 runs/R-008-31b-base-te-d2 \
      --tvr runs/_analysis/trace_vs_reference.R-010.jsonl --out runs/_analysis/failure_breakdown.R-010.jsonl
  ```

- **Redaction:** no task, trace or repo text is quoted here. Only task ids, counts and seconds appear.

## Headline

- **Most failures happen on tasks the 31B has never solved.** 78 of the 103 unresolved draws are on tasks that no
  31B draw in the ledger has resolved. Most of those tasks have had about 11 draws. 39 of the 79 cdev2-79 tasks
  have never been resolved by any 31B draw.
- **Only 25 unresolved draws are on tasks that some other 31B draw resolved.** That is the part a process fix
  can plausibly reach. It is about 12 tasks per draw if every one of them flipped. Realistically it is a few.
- **Empty patches on solvable tasks are the biggest reachable group.** There are 14 such draws. In 9 the time
  cap hit before an edit landed; in 5 the call cap did. The most common way in is reading until the call cap: 4
  of the 5 call-cap draws had their first edit refused as over budget at call 29.
- **Wrong-file misses (16 draws) are mostly out of reach.** Only 2 of them are on tasks any 31B draw has solved.
  The agent opened the reference file in only 2 of the 16.
- **The thinking budget is enforced, but the model keeps deliberating in visible text after the forced end.**
  That is a likely reason a smaller thinking budget (T-31b-003) saved no wall time.

## (a) Method

`tools/failure_breakdown.py` (stdlib) uses R-004's time method, so the numbers compare with R-004.

- **Splitting a turn.** A turn's model seconds are its `elapsed_s` minus the previous observation's. Decode
  seconds are `completion_tokens` divided by the draw's median rate on turns of 300 tokens or more. Whatever is
  left is counted as one of:
  - compaction, when the prompt shrank by more than 3000 tokens;
  - stall, when more than 30 s are unexplained;
  - overhead, otherwise.
- **Long turns** are turns of 800 tokens or more.
- **Unfinished final turn** is `duration_s` minus the last recorded `elapsed_s`. It covers a turn that was still
  generating, or a command that was still running, when the session ended.
- **Endings and miss classes** come from the trace_vs_reference rows:
  - endings: time cap, call cap, submitted;
  - miss classes: wrong file, partial fix, and so on.
- **"On tasks some draw resolved"** counts a draw if any 31B draw in the ledger resolved the same task. Ledger
  draws come from several cohorts, and runs before R-008 ran without task envs.
- **Check against R-004** (R-000 d1/d2):
  - The all, resolved, failed and empty-patch rows match R-004 to within a few seconds.
  - The decode rates are 26.8 and 27.4 tokens/s here, against 26.9 and 27.5 in R-004.
  - The time-cap count differs: 13 and 11 here, against 17 and 14 in R-004. This tool reads the time cap from the
    timeout error. R-004 read it from `summary.jsonl`'s `time_cap_hit`.

## (b) Where the wall time goes

Each cell is the share of the group's summed wall seconds.

| Draw | Group | Task-draws | Short-turn decode | Long-turn decode | Compaction | Tool | Unfinished final turn |
|---|---|---|---|---|---|---|---|
| d1 | resolved | 28 | 54% | 33% | 4% | 0% | 3% |
| d1 | at the time cap | 19 | 23% | 41% | 8% | 3% | 22% |
| d1 | time cap and empty | 9 | 16% | 44% | 5% | 0% | 31% |
| d1 | call cap | 12 | 52% | 30% | 11% | 0% | 1% |
| d2 | resolved | 27 | 47% | 36% | 5% | 0% | 2% |
| d2 | at the time cap | 19 | 24% | 41% | 10% | 7% | 11% |
| d2 | time cap and empty | 11 | 25% | 38% | 13% | 5% | 12% |
| d2 | call cap | 16 | 51% | 28% | 11% | 0% | 2% |

Overhead is 3-6% in every group. Stalls are 0-4%.

- **Time-cap draws spend their time on long turns and on a final turn that never returns.** Tools take almost
  no time.
- **Call-cap draws look like resolved draws:** many short turns that each make a tool call.

### Unfinished final turns

- The long ones run 100-457 s (rich_3506 d1 457 s, rich_3521 302/270 s, rich_4076 297 s).
- Two of them are not generation:
  - rich_3480's ~300 s is a test command held to its 240 s timeout by an infinite loop. R-008 traced its OOM
    flags to the same loop.
  - rich_3772 spends ~500 s after a text-only turn.
- The longest task-draw lasted 919 s. 7 task-draws went past 495 s.

### Long turns

- **Long turns per draw:** failed groups have more than resolved ones.

  | Group | Long turns per draw |
  |---|---|
  | resolved | 1.7 |
  | time cap, empty | 3.0 |
  | time cap, patch | 3.1 |
  | empty, other | 2.0 |

- **Thought length per draw:** resolved draws write 15.5k characters of thoughts. Failed groups write 23.6-26.6k.
- **They are not degenerate.** The zlib ratio has a median of 0.26 in every group, and only 3 turns hit the
  8192-token output cap.
- **The model drafts code inside its thoughts in every group.** Nearly every draw has 3 or more fenced blocks
  before its first edit lands (51 of 55 resolved, all failing time-cap draws). Failing draws draft more before
  landing an edit:

  | Group | Median fenced blocks before the first landed edit |
  |---|---|
  | resolved | 11 |
  | time cap, empty | 17.5 |
  | time cap, patch | 19 |

### Stability over the 2 draws

| State | Tasks in neither draw | Tasks in 1 of 2 | Tasks in both |
|---|---|---|---|
| time cap | 50 | 20 | 9 |
| empty patch | 54 | 20 | 5 |
| resolved | 48 | 7 | 24 |

Time cap and empty patch are mostly draw-level events, not task-level ones. Resolution is mostly task-level.

## (c) When the reference file is reached (unresolved draws)

| Group | Draws | Reference opened | Reference named in thoughts | First source edit |
|---|---|---|---|---|
| time cap, empty | 20 | 17, median 10 s | 18, median 11 s | none |
| time cap, has patch | 18 | 18, median 15 s | 18, median 12 s | 17, median 406 s |
| empty, not time cap | 10 | 9, median 13 s | 10, median 12 s | none |
| other failed | 55 | 39, median 19 s | 46, median 17 s | 52, median 238 s |

- For comparison, resolved draws make their first edit at a median of 164 s (p75 224 s) and end at a median of
  239 s.
- "Named" is a weak signal, because issues often name the function.
- **Empty and time-cap draws are not lost in search.** They reach the right file within seconds and then do not
  commit an edit for the next ~7 minutes.

## (d) Unresolved draws by how they ended

| Bucket | Draws | Tasks | On tasks some draw resolved | What stands out |
|---|---|---|---|---|
| time cap, no edit landed | 20 | 17 | **9** | 11 never tried an edit; 9 tried and none landed |
| time cap, has patch | 18 | 14 | 3 | first edit at a median of 406 s |
| submitted, wrong file | 16 | 10 | 2 | reference file opened in only 2 |
| call cap, has patch | 15 | 12 | 1 | first edit at a median of 259 s |
| submitted, partial fix | 14 | 10 | 1 | first edit at a median of 236 s |
| call cap, empty | 9 | 9 | **5** | first edit refused at call 29 in 5 draws |
| submitted, right file, wrong region | 7 | 5 | 2 | |
| submitted, all hunks touched, wrong change | 3 | 2 | 1 | |
| submitted, edit-tool failure | 1 | 1 | 1 | 15 malformed edit calls |

### The 14 reachable empty-patch draws

| Mechanism | Draws |
|---|---|
| Read until the call cap; the first edit was refused at call 29 | fastapi_14459 d2, fastapi_14419 d2, fastapi_9425 d2, rich_3470 d1 |
| A final turn of 102-457 s that never returned, after 7-19 calls; no edit attempted (rich_3063 d2 had one refused scratch write) | rich_3506 d1, rich_3521 d1/d2, rich_3782 d1, rich_3063 d2 |
| Malformed-edit loops | rich_4079 d1 (22 attempts), rich_3063 d1 (18 attempts) |
| Long turns and few calls, no edit attempted | fastapi_15589 d1 (7 long turns), rich_3506 d2 (4 calls) |
| One malformed edit, then the time cap | fastapi_5624 d2 |

### Malformed-edit loops

- They are not specific to failures. 10 resolved and 10 unresolved draws each have 5 or more malformed edit
  calls (139 calls in resolved draws, 184 in unresolved ones). They cost time, but resolved draws survive them.

### Wrong file

- 9-10 tasks, mostly wrong in both draws: fastapi_13920, 14487, 14583, 15023, 15661 and 9753; rich_3105, 3472,
  3944 and 4076.
- The issue never names the reference file.
- The agent edits a sibling: in the same directory in 10 of 16 draws, and in the same package otherwise.
- Several of the reference files are tutorial sources or scripts, not library code.

### `get_status` is rarely called

- It was called in 15 of 158 task-draws, and in 2 of the 38 time-cap draws.
- So the prompt's "under 90 s, submit" rule almost never fires.
- This does not matter for empty patches, because the grader takes the working tree whether or not
  `submit_patch` is called.

## (e) The thinking budget path (T-31b-003, mechanism only)

- **The config does reach the model.** `adk_submission`'s `apply_thinking_config_to_model` sets
  `extra_body.thinking_token_budget` and `chat_template_kwargs.enable_thinking`. vLLM's
  `ThinkingTokenBudgetLogitsProcessor` then forces the reasoning-end marker once the budget is spent. With the
  gemma4 parser, the markers come from the server's default `reasoning_config`.
- **The forced end shows in the traces.**
  - think1024 d1 has 75 thoughts in the 3k-character band. Base has 24.
  - 30 of those 75 end mid-sentence. Base has 0 of 51 in its 2.5-4.5k band.
  - 31 of 1221 think1024 turns run past 1.1x the budget. The processor checks only every `budget` tokens, so some
    overrun is expected. Base 4096 has 2-4 such turns per draw.
- **The model then keeps deliberating outside the thought.**
  - 24 think1024 turns still run past 4.5k characters (base 47), and no thought marker is reopened.
  - At the cut, the visible text goes on with hedges ("Actually", "Wait", "But let's") around drafted code.
- **So the budget moves deliberation from the thought into the visible text instead of shortening it.** That
  fits R-002's finding of no wall-time saving.
- T-31b-003's status (d2 pending) does not change.

### The output-cap screen (T-31b-006)

- **The 2048-token cap cut off the tool call.** In `S-004-31b-out2048-s1/-s2`, 21 and 22 turns reached 2000 or
  more tokens, and none of them ended in a tool call. In the base screens, 11 of 11 and 13 of 14 such turns ended
  in a tool call.
- That is the mechanism behind "cutting long turns cost more than it saved".

## (f) Next-round target (proposed, not pre-registered)

### Ranking by reachable draws

| # | Target | Reachable draws (of 103) | Already tried | Comment |
|---|---|---|---|---|
| 1 | **No edit lands before a cap, on a solvable task** | 14 (9 time cap, 5 call cap) | calls40 (T-31b-001), think1024 (T-31b-003), out2048 (T-31b-006), edit-first rule (T-31b-007) | every lever tried on time, thinking or the call budget failed; the "edit by call 12" line is already in the prompt and is not followed in these draws |
| 2 | Patch lands late, then the time or call cap hits | 4 (3 + 1) | same as row 1 | the same late commitment, but the edit was made |
| 3 | Wrong region, partial fix, or wrong change | 4 | sibling sweep (T-31b-002) | |
| 4 | Wrong file | 2 | sibling sweep (T-31b-002) | large bucket, mostly unsolvable for this model |
| 5 | Malformed-edit loops | 3, overlapping row 1 | scripted replace after a failed edit (T-31b-008, nearest miss) | as common in resolved draws |

### Recommendation

Target row 1, **late commitment on tasks the model can solve**, through the two mechanisms no tried lever
reached:

1. **The final turn that never returns** (5 of the 14 draws). One last turn runs for minutes with no edit
   attempted.
   - A lever has to make the edit happen before that turn, not make the turn shorter. Cutting turns cost the tool
     call (T-31b-006). Cutting thoughts moved the text into the visible reply (T-31b-003).
2. **Reading until the call cap** (4 of the 14 draws). The edit arrives as call 29.
   - Raising the cap moves these draws to the time cap (T-31b-001). A lever has to move the edit earlier.

### Upside and next step

- The ceiling is small: about 7 tasks per draw if all 14 flipped. Against the 31B base on cdev2-79 (27.5, SD not
  yet measured with task envs), a realistic gain of +2 to +3 would need several draws per arm to see.
- Whatever lever is chosen gets its own pre-registered round file before any draw, with its draw count sized
  from a measured 31B base SD.
