# R-028: where edits fail, both models (desk check; no GPU run)

Written 2026-11-22, while R-027 runs. Counts only; no trace content. Lowest rung of the screening ladder.

## Edit argument loss (`tools/edit_argloss_desk.py`; a `edit_file` result holding only `error`, the harness reply
that the call's arguments did not parse)

| Draws | `edit_file` ok / draw | args lost / draw | other edit errors / draw | tasks with a loss / draw | resolved among them | tasks without | resolved among them |
|---|---|---|---|---|---|---|---|
| 31B base ×6 (cdev2-79) | 122.0 | 128.8 | 21.0 | 18.0 | 7.33 | 61.0 | 21.33 |
| E4B retry ×12 (R-021) | 129.8 | 37.8 | 160.1 | 19.83 | 1.42 | 59.17 | 6.17 |

- **31B.** About half of all `edit_file` calls lose an argument (median 4 per affected task). Yet tasks with a loss
  resolve as often as tasks without (41% against 35%), and 11.17 of the 18 per draw get an `ok` edit after it.
  So the loss costs wall (about 7 calls in an affected task), not solves. This agrees with EXP-025: the first
  loss is a generation slip, and the cost is the resends. A line-range skill offered for it was never called
  (R-026 31b-lineedit, 0 of 24 tasks). **Not pursued as a solve lever.**
- **E4B.** The other edit errors are the large class: 160 per draw, more than the `ok` edits.

## E4B old-string mismatch (`tools/edit_fail_desk.py`, R-021 retry d1-d4, against the base snapshot)

404 `Failed to replace` results (about 100 per draw). Classed by the `old_string` against the file at the base
commit:

| Class | Count | Share |
|---|---|---|
| mostly present (half or more of its lines are lines of the file) | 184 | 46% |
| mostly invented | 129 | 32% |
| every line present, but not contiguous | 57 | 14% |
| exact in the base file (stale: the task had already edited that file) | 32 | 8% |
| differs only in whitespace | 2 | 0% |

- 402 of the 404 come after a `read_file` of the same file. So the E4B writes the old text from memory,
  imperfectly, after reading. Whitespace is not the cause (the harness already matches whitespace flexibly).
- On the 31B the same error is rare: 28 in 3 draws.
- Tasks with at least one edit error (34.08 per draw) resolve 1.25; clean tasks (44.92) resolve 6.33. That is
  confounded with difficulty. In 10.83 of those tasks per draw the last edit attempt in the task failed.

- **Fail rate by `old_string` size** (non-blank lines; `ok` against `Failed to replace`, R-021 retry d1-d4): 1 line
  84 of 246 (0.34); 2-3 lines 79 of 209 (0.38); 4-8 lines 146 of 312 (0.47); 9 or more 95 of 160 (0.59). Smaller
  spans fail less, but even a single line fails a third of the time.

## What this suggests (not a decision)

- No edit-tool change can fix invented old text without a risk of writing wrong lines. A tool that applies the
  edit at the most similar region would land 60% of these (mostly present plus non-contiguous), but the
  `new_string` is built on the misremembered text too.
- A lever for the E4B would have to make the exact text cheaper to copy, for example a smaller span (one to three
  lines) per edit. That is a prompt rule, and E4B prompt rules have been noise so far (`tweaks.md`). The size
  table bounds it: moving every edit to one line would cut the fail rate from about 0.43 to 0.34.
- Decided after R-027 reads. Not queued.
