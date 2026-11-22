# H-003: E4B retry-on-empty candidate for Kaggle L4x4 (handoff, not a pre-registration)

Written 2026-11-22 on pleiades. Counts only.

- **Source.** `recursive-harness`: round R-021 (`harness-eng/rounds/R-021-e4b-retry-skill.md`, decision at 93a0c94)
  and the recommendation `harness-eng/framework.md` (ad2f996).
- **Tree.** The tree as run is copied here, byte for byte, to `harness-eng/trees/e4b-r020-retry/` (cluster commit
  cccd61b).
- **Prerequisite.** H-002, the validator fix for `agent_tool` roots.
- **Suggested id.** EXP-088 (087 is H-001's).

## Result on the cluster

- **R-021, 12 paired draws per arm on cdev2-79 (79 tasks), Ada, task cap 8.0 min, concurrency 4.** The control is
  the same tree with one `solve` call.
  - Paired difference **+1.08 solves per draw, 90% CI +0.08..+2.08** (bootstrap over tasks, 10,000, seed 0).
    Retry mean 7.58 against control 6.50.
  - Wall ratio 1.23: mean task wall 139.7 s against 113.3 s.
  - Pre-registered reading "helps": the E4B frozen config uses this layout.
- **Mechanism.**
  - 163 of 169 empty first attempts were retried, and 13 were rescued, which is 1.08 per draw and matches the
    gain.
  - Empty patches fell to 5.3 per draw from 17.3.
- **Base drift.** The control's 6.50 sits with the earlier E4B base: R-011 7.00 and R-008 Ada 6.67, on the same
  cohort.
- **No Kaggle number exists yet.** On Kaggle the E4B comparison points are EXP-038 (the EXP-033 tree on dev-48, 5 of 48)
  and the EXP-050 upload (`submissions.md` row 14).

## Layout (what the tree does)

- **Root** (E4B): `submit_patch`, an `agent_tool` `solve` (`sub_agents/solver.yaml`) and `skills: [skills/change-count]`.
  It has no shell. `prompts/root.md` loops:
  1. call `solve`;
  2. call `run_skill_script(change-count, scripts/count.py, [])`;
  3. if it printed 0 and `solve` ran fewer than 3 times, call `solve` again;
  4. otherwise `submit_patch` and stop.
- **Solver** (E4B): `run_command`, `read_file`, `edit_file`, `write_file`, `get_status`. It has **no `submit_patch`**:
  any `submit_patch`, even an empty one, ends the task on the next final text (R-018). The prompt is the E4B base
  prompt plus the R-016 task section.
- **`count.py`** reads `.git/index` and the `_swegemma_baseline` commit time and prints the number of changed source
  files. It leaves out tests and junk, starts no program and makes no connection, and prints 1 on any error.
- **`eval_config.yaml` as run:** `max_tool_calls` 56 (shared by every attempt), `max_time_minutes` 8, `max_turns`
  80, `timeout_seconds` 240.

## What the Kaggle-side session needs to do

1. **H-002 first.** On this tree the repo validator gives the false error `root agent has no way to modify files`.
   The tree also ships 9 files, not 4: the 7 in H-002's list plus `skills/change-count/SKILL.md` and
   `skills/change-count/scripts/count.py`. The shipped-closure test needs that set.
2. **Candidate eval_config.** Set `max_time_minutes` 8 → 4.5, so that `120 x (4.5 + 1.0) = 11.0 h` passes the pack
   gate, as EXP-050 did. Keep `max_tool_calls` 56, `max_turns` 80 and `timeout_seconds` 240.
   - `prompts/solver.md` still says "28 tool calls and 8 minutes", which is the text as tested. Leave it, one
     variable, as EXP-050 did.
   - **Cap estimate from the cluster rows (not a measurement).** Counting a resolved row as lost when its task
     wall is over 270 s gives 7.42 against 6.42 per draw, so the gain should survive 4.5 min.
   - 11.5% of retry rows run past 270 s (control 7.4%). Task wall p50/p90/p99: 104/295/485 s, control 88/228/454 s.
3. **Expected validator profile** (cluster `--official` in `env/harness.sif`):
   - `adk_submission.validate_directory` OK;
   - warning VERIFY(Q1), skill scripts rely on `run_skill_script` (EXP-057 found the E4B calls it on Kaggle with
     exactly this call shape);
   - warning `timeout_seconds` 240 < 300, as EXP-050;
   - the H-002 false error;
   - the pack-gate error at 8 min, which item 2 removes;
   - the cluster-only `compile_submission` TypeError.
   Packing therefore needs `--allow-warnings` for the two warnings.
4. **Kaggle run.** dev-48 on L4x4 (`plan.md §5.8`):
   - the readings to pre-register are wall per task, projected worst case at most 11.0 h, and resolved against EXP-038's
     5 of 48 (the E4B single loop on dev-48);
   - the E4B's Kaggle time projection before this layout was 3.56-3.96 h (EXP-048), and at 1.23x wall that is
     about 4.4-4.9 h;
   - a paired dev-48 against EXP-038 is the only Kaggle-side efficacy check that fits before the freeze. Its
     MDE is about 4 tasks at 48, so it confirms health and time, not the +1.08 (which is about 0.7 on 48 tasks).

## Not for the 31B

The 31B stays the single-agent `submission/` (`framework.md`). Most of its empty patches end at the session timeout,
and the R-018 sizing gives 0.00 for a retry. It has no wall to spend: projected 9.3-10.3 h against the 11.0 h gate.
