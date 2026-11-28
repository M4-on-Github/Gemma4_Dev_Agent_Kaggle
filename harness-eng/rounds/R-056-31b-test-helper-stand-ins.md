# R-056: 31B, stand-ins for two missing test-helper modules, added by the agent's first command (pre-registration)

Written 2026-11-28, before any GPU job of this round is submitted. Counts only.
User instruction (2026-11-28): think outside the box; do not be confined to the model's own skill.

## Desk checks behind it (CPU only, no model; done before this file)

Two control draws (`R-037-31b-kfctl-d1`, `d2`) were regraded patch by patch in three test environments.

| Test environment | d1 | d2 |
|---|---|---|
| Cluster standard: scorer Python plus each task's own test packages (`env/taskenvs`) | 35 | 32 |
| D-011: our copy of the public scorer, no task packages | 16 | 14 |
| D-011: same, with the two stand-ins appended to each patch | 16 | 14 |
| D-012: task packages at the right versions, only `inline_snapshot` and `dirty_equals` removed (`env/taskenvs-nosnap`) | 26 | 23 |
| D-012: same, with the two stand-ins appended to each patch | 35 | 32 |

- In our scorer copy the reference patch resolves 38 of the 79 tasks. 22 fail first on one of the two missing
  modules, 15 on a library-version `TypeError`. With stand-ins, 17 of the 22 then fail on the version error, so the
  stand-ins gain nothing there.
- With versions right and only the two modules missing, stand-ins recover 9 solves per draw and lose none; the
  result equals the standard cluster grading task for task.
- Which of these the official scorer resembles is not known. The scorer copy as is gives 0.18-0.20, close to the
  Kaggle scores of this kind of tree (0.12-0.18); the Kaggle-notebook check of 2026-11 (EXP-036) had stand-ins
  gaining 3 to 6 solves of 40, which fits the D-012 picture. No current tree adds the stand-ins; the old root
  prompt asked the model to write them by hand.
- Limit: both modules belong to the public repository families. Hidden tasks from other repositories may miss
  other modules.

## Design

`trees/31b-kf-vend` = `trees/31b-kf-ctl` plus prompt section 0: the first tool call is one fixed shell command
(1,194 characters). For each of the two modules it does nothing when the module imports or when no `.py` file
imports it; otherwise it writes a compact stand-in package (765 bytes for both) at the repository root. It runs first so a
task that ends at a cap still carries the stand-ins. Scratch test: the stand-ins pass the equality cases of the
longer versions in `tools/compat_shims`; a second run changes nothing.

Runs use `--task-envs env/taskenvs-nosnap` (the D-012 environment), where the command has work to do. The control
is kfctl x8 regraded in that environment (CPU jobs `D-012-kfctl-d1..d8-v0`); its ceiling is kfctl x8 as graded on
the cluster (30.38).

## Readings (written before any GPU job runs)

1. Smoke (2 tasks that import the modules): the first tool call is the command, copied exactly; the stand-in
   folders are in the graded patch.
2. Draw-1 kill gate: 25 or more empty patches, or mean task wall above 452 s.
3. Mechanism, all draws: share of tasks whose first tool call is the exact command (bar 90%); among tasks that
   import one of the modules, share whose graded patch holds the stand-in (bar 85%).
4. Decision, `R-056-31b-vend-d1..d4` against the regraded control x8: kept as an upload candidate at +5.0 solves or
   more with CI lower bound above +2.0. Against the ceiling (30.38): the loss from spending one call and about
   450 output tokens is reported; more than -2.0 is a harm flag.
5. Wall ratio against kfctl (385.6 s) is reported; above 1.06 is flagged.

**Blind guess.** Exact first-call copy in 90% of tasks: 65%. Kept: 60%. Regraded control near 21.5 per draw; arm
near 28.

## Deviation logged before any result: smoke job 68699 did not start the model server (2026-11-28)

Job 68699 ended after 52 s with no task run: the model server refused to start because 11 GiB of the assigned
card were held by another process (36.1 of 47.4 GiB free against the 42.7 GiB it reserves). No result file was
written. The smoke run is resubmitted unchanged under the same run id; readings as written.
