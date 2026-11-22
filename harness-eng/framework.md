# Orchestration framework for the 31B and the E4B (recommendation, 2026-11-22; revised after R-024)

> **Revised 2026-11-22 after R-024.** At the Kaggle cap (4.5 min) the E4B retry layout gave **+0.33 solves per draw,
> CI −1.08..+1.83** (wall 1.13x, rescued 0.83 per draw), and the pre-registered reading is **dropped**. Both models
> therefore ship the single agent: the 31B `submission/`, and the E4B EXP-050 loop. The E4B section below is the
> 8-min result, kept as the record. Handoff H-003 is withdrawn.

This answers the goal the user set on 2026-11-21: find an orchestration framework for both models that can win.
It summarizes the cluster record (rounds R-001 to R-021, L-001 to L-007, `tweaks.md`). Counts only. Every number here
comes from a round file, which is the source.

## E4B (small-model prize): retry on an empty attempt (8-min result; dropped at 4.5 min, R-024)

**Layout** (`trees/e4b-r020-retry`, round R-021, tweak T-e4b-021):

```
root (E4B, tools: submit_patch, agent_tool solve, skill change-count; no shell)
  1. solve("Resolve the issue in /workspace.")        -> solver (E4B, base solver prompt, run_command,
                                                         read_file, edit_file, write_file, get_status; NO submit_patch)
  2. run_skill_script(change-count, scripts/count.py, []) -> prints the number of changed source files
  3. if 0 and fewer than 3 solve calls: go to 1
  4. submit_patch, one sentence, stop
eval: max_tool_calls 56 (shared by every attempt), max_turns 80
```

**Evidence.**

- Measured against the same tree with one `solve` call: **+1.08 solves per draw, 90% CI +0.08 to +2.08**. That is
  12 paired draws on 79 tasks on Ada, with wall 1.23x.
- 163 of 169 empty first attempts were retried, and 13 were rescued. Empty patches fell from 17.3 to 5.3 per
  draw, and 24 tasks were solved at least once against 16.
- This is the first E4B layout with a significant gain. Across 21 rounds, every prompt, sampling and two-stage
  change before it was noise or worse.

**Why each part is there.** Each part is a failure that was observed:

| Part | Without it |
|---|---|
| Solver has no `submit_patch` | Any `submit_patch`, even an empty one, ends the task on the next final text. The root never got control back (R-018: `retry_miss` 7, killed). |
| Root has no shell | Given `run_command` for the count, the root worked on the issue itself, and once never called `solve` (R-020 smoke, killed). |
| Count in a pure-Python skill script | The E4B calls `run_skill_script` reliably with the exact three fields and no `load_skill` (EXP-057). The script reads `.git/index` itself and runs no program. |
| Call cap 28 -> 56 | The counter is shared by every attempt, so a second attempt needs calls left. |

**Not adopted on the E4B.**

- No-compaction solver alone (R-017): −0.12.
- Best-of-3 file-set selector (R-019): no better than retry at twice the wall, at the desk check.
- An edit helper (R-014): killed.
- Reviewer stage (R-011): dropped.
- LoRA adapters (L-003, L-007 a2): killed. With a2 the call cap was hit in 38 of 40 tasks, 11.3 submits per
  submitting task.

**Open before it can ship** (handoff H-002 on `all-work-consolidated-2026-11-20`):

1. Kaggle uses a 4.5-minute cap, and this round used 8.0. Cutting resolved rows at 270 s gives 7.42 against 6.42
   per draw on the same rows, so the gain should survive.
2. The repo validator's false error "root agent has no way to modify files" needs fixing first. Its reachable
   tool set leaves out `agent_tool` children.
3. A Kaggle L4x4 run on dev-48 must confirm the wall within the 11.0 h gate (`plan.md §5.8`).

## 31B (main track): stay a single agent

**Layout:** the current `submission/` single LlmAgent. No orchestration and no adapter.

**Evidence.** The 31B has no wall to spend:

- The base projects about 9.3-10.3 h of Kaggle time against the 11.0 h gate. Its six cdev2-79 draws (R-008 d1-d2,
  R-011 d3-d4, R-014 d5, R-015 d6) resolve 28, 27, 30, 28, 32, 27 (mean 28.7), at mean task walls of 335-369 s.
- Every 31B layout that added a step or a call cost more wall than it gained:

  | Layout | Round | Outcome |
  |---|---|---|
  | Scout then editor | R-014 | killed at d1: 26 vs 29.0, 11.84 h projected |
  | No-compaction solver | R-016 | killed at d1 |
  | Worked example in the prompt | R-015 | killed at d1: 25, 10.71 h |
  | Adapter l5 | L-005 | killed at d1: 13.9 h projected |
  | Adapter l6 with a stop turn | L-006 | killed at d1: 13.5 h projected |
  | Temperature 0.6, bounded output, think 1024, no thoughts | R-002, R-003, R-011 | noise or worse |

- **Retry on empty does not transfer to the 31B.** Most 31B empties end at the session timeout. The 36 empty
  task-draws that ended early had a median of 115 s left, and no other draw solved those tasks within that time.
  The simulated gain is 0.00 (R-018 sizing).

**What would change this.**

- H-001: the 31B LoRA decode cost on L4x4. If it is near 1.0, an adapter needs only to break even on wall.
- A layout that cuts 31B wall per task.
- Nothing like that is queued, and orchestration freezes about 2026-11-26.

## Summary

| Model | Framework | Change vs current | Status |
|---|---|---|---|
| E4B | single loop (EXP-050) | none | the retry layout (+1.08 at 8 min, R-021) gave +0.33, CI −1.08..+1.83 at the Kaggle 4.5 min (R-024): dropped |
| 31B | single agent (`submission/`) | none | every alternative was killed on wall or was noise |
