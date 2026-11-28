# R-053: 31B, a one-call map of a name's definitions, users and import path (pre-registration)

Written 2026-11-28, before any job of this round is submitted. Counts only.
User instruction (2026-11-28): try the graph idea again; an earlier null closes a variant, not the idea.

## What was tested before, and what is different

- R-039/R-040 ran a code map as a separate step (a skill script, then the agent). The map did not change solves on one
  draw (31 against 30.4 expected) and the extra step broke the time gate (456 s against 452 s). Skill scripts are
  also reported not to see the repository on the official scorer.
- This arm has no extra step and no script file: one shell command inside the agent's own loop prints, for one name,
  where it is defined, which files use it and how it is imported (a two-hop neighbourhood, at most about 25 lines).
- Targets, from the failure record: partial fixes (24% of failing attempts: the change is right but not everywhere
  it is needed) and tests that import a name from the repository that the patch did not provide (7.5% of failing
  31B patches).

## Arm

`trees/31b-kf-graph` = `trees/31b-kf-ctl` plus one prompt section of two bullets (the command, and how to use its
three parts before submitting). Validator: the two known errors only.

## Readings (written before any job runs)

1. Served check per draw. 2. Draw-1 kill gate: 25 or more empty patches or mean task wall above 452 s.
3. Decision, `R-053-31b-graph-d1..d4` against kfctl x8: extend to 8 draws at +1.0 or more; promote at 8 draws with
   +1.5, CI lower bound above -0.5, wall ratio 1.06 or less; harm at -1.5.
4. Mechanism: tasks where the command is run; files changed per patch (kfctl as reference); share of failing
   patches ending in an import error from the repository's own package; tool calls and wall per task.

**Blind guess.** The command is run in half the tasks or more: 55%. Extension: 15%. Promote: 7%.
