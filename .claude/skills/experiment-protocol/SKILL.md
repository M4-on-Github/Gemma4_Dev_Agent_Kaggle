---
name: experiment-protocol
description: Pre-registered protocol for running and logging experiments in this repo - dev-48 GPU arms, zero-GPU analyses, and LB-only uploads - using the existing EXP-NNN file shape and the tools under tools/.
user-invocable: false
---

# Experiment protocol

Three experiment types share one file shape: **dev-48 GPU arm** (Kaggle L4x4 kernel), **zero-GPU analysis** (re-grade, forensics, audit of owned data), **LB-only upload** (pre-registered reading of one public-LB draw). Every change to the shipping tree is one of these.

## Order of work

1. Glob `experiments/EXP-*` and take the next free NNN. Create `experiments/EXP-NNN-<slug>.md` and, if there are artifacts, `experiments/EXP-NNN/`.
2. Write the header and sections 1-7 (template below). The readings in section 4 are written blind and are never revised; a drafting defect found later is logged in section 7, not fixed.
3. Commit (`EXP-NNN: pre-register <title>`). The lead sends the critic (`prereg` tier). Apply Required fixes as a new commit; do not reword readings after the critic has passed them.
4. Build. Candidate trees go in `experiments/EXP-NNN/candidate-<arm>/` and are produced by a tool from a committed source (`exp022_make_candidate.py`, anchored edits that must match exactly once), never hand-edited. Validate with `tools/validate_submission.py <tree> --strict`, pack with `tools/pack_submission.py`, record the sha256 and member list. A gate error (`max_time_minutes` above 4.5) may be packed with `--skip-budget-gate` only when section 2 states the override and its justification.
5. For a GPU arm: `tools/build_notebook.py --embed <zip> --username rainm4 --set N_TASKS=48 --out notebooks/expNNN_<arm>/kaggle_eval_l4x4.ipynb`; copy `kernel-metadata.json` from the last working arm changing only `id` and `title` (keep the pinned `docker_image`); `kaggle kernels push -p notebooks/expNNN_<arm>`. The push guard checks that the EXP file is committed and has a readings section. Push paired arms together so they share the hardware day.
6. Fill section 8 below the `---` line: build time, validator output, sha256s, pre-registration commit, push time, kernel ids, status. Commit. Add the `experiments/README.md` §3 row (ID, date, variable, cohort, resolve, rates, median wall, projected 12 h, decision).
7. Wait in the background (`kaggle kernels status <id>`); a dev-48 arm at 8 min takes 4-7 h. Download with `kaggle kernels output <id> -p runs/EXP-NNN-<arm>/`. Then:
   ```
   python tools/analyze_traces.py runs/EXP-NNN-<arm> --cap-minutes <cap> --max-calls <calls>
   python tools/run_forensics.py forensics runs/EXP-NNN-<arm>
   python tools/run_forensics.py compare runs/EXP-NNN-<A> runs/EXP-NNN-<B>
   python tools/estimate_budget.py --eval-config <tree>/eval_config.yaml --results runs/EXP-NNN-<arm>/summary.jsonl
   ```
   Copy `summary.jsonl` to `experiments/EXP-NNN/<arm>-summary.jsonl` (the one jsonl the hygiene check admits). Traces stay in `runs/`.
8. Append section 9 (results), applying section 4 row by row, first matching row governs. Report resolves only as "reported, not an endpoint" unless the design was powered for them. Update the §3 index row and the `submissions.md` row if an upload is involved. Commit (`EXP-NNN: results`). The lead sends the critic.
9. Report back: the row that fired, in one line, and whether the pre-registered prediction held.

## Checkpoints

Runs get cut off (quota, context, permission blocks). Commit after each milestone: pre-registration, critic fixes, built, pushed, downloaded, analyzed. Keep a `## Status` line at the bottom of section 8 with the kernel ids, what is running and the exact next command. A restarted run reads this first.

Never call `kaggle competitions submit` from experiment code, kernels or this protocol. Only the submitter uploads.

## Design rules

- **One variable per arm.** Paired arms share the 48 ids and are pushed together. Two changes in one arm make a package test; say so in the title and read it as one.
- **Endpoints before data.** Primary, secondaries, and the statistic for each: Wilson CI for a rate; exact McNemar for a paired per-task outcome; Fisher for event counts between arms; paired Wilcoxon for per-task counts. Write the power or MDE down; if the design is not powered for resolves, resolves are not an endpoint.
- **Readings cover every outcome**, including blank/crash (infrastructure row), underpowered (count below threshold), and both directions, each with the decision it drives (the next arm, the next upload tree, or revert). Name thresholds in paired terms ("worse by more than the paired MDE"), not in raw counts.
- **Time projection** is measured mean x 120 / 3600 + the overhead measured in the same run (server start, per-task setup, grading), compared with the ~10.5 h ceiling. Never the cap x 120 alone.
- **Cost stated up front:** GPU-hours against the 30/week, and whether an upload slot is spent.
- **Prompt edits** are anchored insertions or replacements (each anchor matched exactly once); the inserted text lives as its own file in `experiments/EXP-NNN/` so the diff is reviewable. Rejected prompt variants get a marker in `pack_submission.py` so they cannot ship by accident.

## File template

```markdown
# EXP-NNN — <title>

**Date:** YYYY-MM-DD
**Type:** dev-48 GPU experiment, N arms, ~X L4x4-h of the 30/week | zero-GPU analysis | LB-only upload (#N)
**Pre-registered:** this file is committed before <push | upload>. Sections 3-5 are written blind and are not revised.
**Serves:** <claim IDs; the main-track decision; the paper section>
**Supersedes / relates:** <EXP ids>

## 1. Why this, now            <evidence on disk, with IDs and numbers>
## 2. Design                   <table of arms: tree, caps, sampling, prompt chars, zip sha; build method; cost; any gate override and its justification>
## 3. Endpoints, fixed in advance   <primary, secondaries, statistics, power/MDE>
## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.
| # | outcome | reading |
## 5. What this does and does not license
## 6. Exact commands
## 7. Defects in this pre-registration, logged after the fact
None yet.
## 8. Built and pushed / uploaded      (below the line; nothing above changes)
---
## 9. Results, YYYY-MM-DD. Section 4's readings applied as written.
```

## summary.jsonl and aggregates.json

`tools/analyze_traces.py` writes per task: `resolved`, `task_wall_s`, `n_calls`, `n_malformed`, `n_identical_repeats`, `n_edit_arg_loss`, `overflow`, `phase_reached`, `first_edit_turn`, `time_cap_hit`, `calls_cap_hit`, `empty_patch`, `submit_called`; and `aggregates.json` with Wilson CIs, failure-mode rates and the projected 12 h total. Read the field list from the tool, not from memory, before writing endpoints.
