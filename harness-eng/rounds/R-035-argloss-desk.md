# R-035: 31B `edit_file` argument loss, desk check (zero GPU)

Written 2026-11-22, after R-034. Counts only; no trace text, code, paths or ids. Tool: `tools/argloss_counts.py`
(new). Question: R-034 showed that about half of the 31B's `edit_file` calls return only `error`, so an argument
never reached the tool. Is the cause a slip that a prompt can steer, and is it worth a sweep?

## Mechanism

- **Parser.** Kaggle and the cluster both serve with vLLM 0.19.1 `--tool-call-parser gemma4`
  (`notebooks/kaggle_eval_l4x4.py:283`, `tools/cluster_eval.py:211`). In `vllm/tool_parsers/gemma4_tool_parser.py`,
  a string value opens with the `<|"|>` token and ends at the next `<|"|>` (`find`, no escaping). Text after that
  delimiter is read as more `key:value` pairs. Synthetic probes of `_parse_gemma4_args` confirm it.
- **Order.** The 31B writes the arguments in schema order, alphabetical: `filepath`, `new_string`, `old_string` (all
  117 OK calls in R-034 ctl d1-d4; `allow_multiple` comes first when given).
- **The 31B slip.** In all 134 lost calls of R-034 ctl d1-d4, the `new_string` value ends in a backtick, a comma and
  the `old_string` key text. So the model closed `new_string` with a backtick instead of the `<|"|>` token. The
  parser then ran on to the next delimiter, the opening of `old_string`'s value. The old text either becomes
  fragment keys (109 of 134, when it holds a colon) or is dropped. The harness then answers that `old_string` was not
  provided. Error length is 205 characters in all 134.
  - **Across every 31B round:** R-000 to R-034, 38 draws. 87% of lost calls have exactly this tail (for example
    R-008 d1 176 of 197, R-016 d1 200 of 246). On the cdev2-79 base draws, lost calls about equal OK calls
    (R-008 d1: 197 lost, 108 OK).
  - No backtick appears elsewhere in those values. Single-line against multi-line and short against long values do
    not separate lost from OK.
- **It persists.** After a lost call, the next `edit_file` call is lost 110 of 123 times in R-034 ctl, and in R-026
  ctl 0.952. After an OK call it is lost 0.069 (R-034) and 0.044 (R-026). First edits are lost 20 of 79. Losses
  sit in 4-6 of 24 tasks per draw, about 8 lost calls per affected task.
- **The E4B slip is different.** E4B `new_string` values end early at an inner double quote. The leftover becomes a
  key that holds the `old_string` text, in 58 of 71 lost calls in R-034 E4B ctl. A further 8 use `old_string=`.
  E4B loss persists less: lost after lost 32 of 71.

## Is it worth fixing? (cdev2-79 base draws R-008 d1-d2, R-011 d3-d4, R-014 d5, R-015 d6)

| Task-draws | Per draw | Resolved | Time cap |
|---|---|---|---|
| no lost call | 61.0 | 0.350 | 0.309 |
| 1-2 lost | 7.33 | 0.432 | 0.250 |
| 3 or more lost | 10.67 | 0.391 | 0.297 |

- **Solves, paired by task.** The 60 heavy-loss task-draws that have a no-loss draw of the same task resolved 25,
  against 22.9 expected from those tasks' no-loss draws. The loss does not cost solves.
- **How they recover.** Of the 64 heavy-loss task-draws:
  - 32 get an OK `edit_file` later;
  - 7 use `write_file`;
  - 30 have neither, and 11 of those resolve (an edit before the loss, or a shell edit).
- **Wall, paired.** Heavy-loss task-draws average 359.6 s against 301.3 s for the same tasks without loss (n 60).
  That is +58 s on 10.67 of 79 tasks, about 7.9 s per task, or 2-3% of the 31B's mean task wall. A third (0.337) of
  completion tokens in those tasks are spent on lost calls.

## Decision

- **Not run.** The ceiling of a perfect fix is about 0 solves per draw, and a 2-3% wall saving. Measuring that wall
  saving would take more than the 16-draw sweep that was drafted: three prompt arms (an argument bullet, a prompt
  with no backticks, and both) on `sw-31b-24` ×4, plus 4 controls. The draft trees were deleted unrun.
- The 31B edit-argument line is closed, with R-034. The loss is real, Kaggle-wide and prompt-shaped, but the 31B
  already works around it.
- For the paper track this is a finding: half of the 31B's edit calls are lost to a one-token slip against the
  Gemma 4 tool-call format, and the model recovers through other tools at a wall cost, not a solve cost.
