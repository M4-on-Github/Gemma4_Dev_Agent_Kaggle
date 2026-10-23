# EXP-017 — Submission #5: temperature 1.0 + prompt surgery (pre-registered)

**Date authored:** 2026-10-22. **Authoring GPU cost: zero.** No dev-48 validation run — see
"Deviation from plan section 5.8" below. Motivated by `EXP-016-top-team-audit.md`.

**This document was written before the submission was pushed.** The readings in section 4 are pre-registered;
do not revise them after seeing the score.

---

## 1. What changed, and why each change is here

Four changes, bundled deliberately (section 3). Every one is either time-neutral or time-*reducing*, because
EXP-016 section 4 establishes wall-clock as the binding constraint on 79.2% of our tasks and EXP-016 section 3
establishes that we cannot buy more of it.

| # | Change | File | Evidence |
|---|---|---|---|
| 1 | `temperature: 0.2` → `1.0` | `configs/sampling.yaml` | The **only** difference between the rank-3 team's published v19 (LB 0.18) and v24 (LB 0.24). `top_p`/`top_k` already matched theirs. 1.0 is also the harness scorer default — our 0.2 was the deviation. This is E4, planned and never run. |
| 2 | Drop the 3 graph tools | `agent.yaml`, prompt | The 0.24 and 0.22 bundles both declare exactly 6 tools, no graph tools. The rank-3 team's own local runs put their graph-tool versions below their 6-tool ones. Our prompt had already demoted them to "only if two greps found nothing", so they cost prompt budget on every step while being reachable almost never. This is E5, taken on external evidence. |
| 3 | First-edit deadline call 25 → **12** | prompt | Their winning prompt says "Edit by tool call 12". Targets the measured 47.4% empty-patch rate inside our time-capped cohort. |
| 4 | REPRODUCE: 6 calls + `/tmp/repro.py` heredoc → **2 calls, `python -c` only, skippable** | prompt | Our own forensics measured 27.3% of wall-clock going into heredoc repro files. Their prompt bans the repro *file* while keeping cheap reproduction. Directly buys back the binding resource. |

Phase caps rebalanced to stay coherent with a call-12 first edit: LOCATE 10→8, REPRODUCE 6→2, EDIT 12→14,
VERIFY 10 unchanged. Also added, free and evidenced by `verification.py:297` which we confirmed independently:
submit even when the local check is red, and `git checkout --` any test path that lands in the diff.

**Deliberately NOT changed:**

- `max_time_minutes: 4.0` — EXP-016 section 3: 6.0 min projects to 10.99 h and 7.0 min to 12.57 h, past the
  12 h hard limit. Submission #2 died at a 11.34 h projection. Unchanged is the only safe value.
- `max_tool_calls: 45` — EXP-016 section 4: calls do not bind for us (median 32, 1 task of 48 at cap), and
  EXP-003's 28-call cohort resolved **0 of 20**. Copying their 28 would cost resolves.
- `thinking_budget: 256`, `max_output_tokens: 4096` — these *cost* wall-clock per step. At 79.2% time
  saturation they trade steps for depth, and EXP-003 saw s/turn rise to 7.79-12.13 under similar settings.
  Held for EXP-014, after prompt surgery has created headroom.
- The `inline_snapshot` / `dirty_equals` vendoring block (3,508 B, 31% of the prompt). It is load-bearing for up
  to 35 of 129 tasks (their census: 71 solvable, 106 with env repair) and is one of the few places we may be
  ahead of other teams. Moving it into an on-demand `skills/` entry is the right fix and is **not** being
  attempted under time pressure. Logged as follow-up.
  [Correction 2026-10-22: this bullet originally read "~6 KB, 55% of the prompt". That figure was wrong: it was
  written from memory, not measured. Measured, the block is 3,508 B and 31% of the 11,228 B prompt. Corrected
  by `EXP-018-config-provenance-audit.md` section 4. Section 4 of this document is unchanged.]

Net prompt size 11,175 → 11,226 B. It did **not** shrink; the win here is runtime calls, not prompt bytes.

## 2. Validation performed (zero GPU)

```
tools/validate_submission.py submission --strict
  info  1 agent(s): swe_coder; instruction chars: 11226
  info  eval_config.yaml: worst case 120 x (4.0 + 1.0 setup) min = 10.00 h (gate 11.0 h, limit 12.0 h)
  RESULT: VALID (0 errors, 6 warnings)
```

All 6 warnings are pre-existing unreferenced-file notices (`adapters/README.md`,
`configs/sampling_nothink.yaml`, `prompts/analyzer.md`, two `skills/*/SKILL.md`, `sub_agents/analyzer.yaml`),
unchanged by this edit. Projected actual time is **unchanged from E0's measured 8.61 h** and strictly improved
by change #4.

## 3. Why bundled rather than one variable at a time

Our MDE is ~4 LB tasks (three scored submissions on the identical 58 tasks read 4, 7, 6 — mean 5.67, sd 1.53).
A single submission returns exactly one integer, truncated to 2 dp. **No single-variable test is resolvable at
this MDE**, so splitting these four across four days would spend four slots and learn nothing about any of
them. Today's submission is therefore a score attempt, not an experiment, and is labelled as such.

The honest cost: if it moves, we will not know which change moved it. The ablation order afterwards is
temperature first (one line, and the one with external LB evidence attached).

## 4. Pre-registered readings

Our current best is **0.12 = 7/58**. MDE ~4 tasks. Reference class: median team 8 tasks, mode 10, ceiling 14.

| Score | Tasks | Reading | Next action |
|---|---|---|---|
| **blank** | — | Notebook Timeout. Would contradict EXP-016 section 3 directly, since projected actual is unchanged at ~8.6 h and change #4 only reduces it. Would mean fixed notebook overhead is far larger than assumed. | Stop all budget work. Instrument notebook startup overhead before any further submission. |
| **≤ 0.08** | ≤ 5 | Real regression, below all three prior replicates (4, 7, 6 is the floor only if 4 was the true floor). Most likely culprit is change #3 forcing premature edits, or temp 1.0 degrading edit-anchor precision. | Revert to the sub-#2 config. Re-ablate changes #3 and #1 separately on dev-48 before resubmitting. |
| **0.10 - 0.15** | 6 - 9 | **Inside noise. The modal outcome, and uninformative.** Our own replicate spread covers this entire band. Not evidence for or against any of the four changes. | Do not iterate on the LB. Spend the next quota on the E0 dev-48 **repeat baseline** (EXP-009 Part C4) — we still have no same-config noise floor, which is why this band is unreadable. |
| **0.17 - 0.18** | 10 - 11 | +3 to +4 tasks, at the MDE boundary. Matches the rank-3 team's **v19** (their config at temp 0.2 = 0.18) almost exactly, which is the predicted landing spot if the config is what matters and temperature is noise. Would put us ~rank 230-320. | Treat as real but unattributed. Ablate temperature (revert #1 alone) to test whether the 0.18→0.24 step reproduces for us. |
| **0.20 - 0.22** | 12 - 13 | Above MDE, top-20 territory. Would mean the bundle beat their own v19 — plausible, since we keep 45 calls where they run 28, and EXP-003 showed the 28-call cap resolving 0/20. | Lock the config. Then EXP-014 (thinking/output budgets) on the headroom change #4 bought. |
| **0.24** | 14 | Ties the ceiling. Would be inside their noise rather than past them. | Lock it, stop changing the agent, and spend remaining slots on replicates to characterise variance before the private half. |

**What this submission cannot tell us**, stated in advance: which of the four changes acted; whether the
empty-patch rate fell (the LB returns a score, not a rate); and whether the 47.4%-empty time-capped cohort
shrank. All three need a dev-48 run with traces. The LB result is one integer and will be treated as one.

## 5. Deviation from plan section 5.8

Section 5.8 requires a dev-48 run before submitting. This submission has none; quota and time were
unavailable. Precedent: submission #4 (EXP-010) took the same deviation, recorded in that document.

The risk the gate exists to prevent is specifically Notebook Timeout, and it is addressed on measurement
rather than on a run: `max_time_minutes` and `max_tool_calls` are **untouched**, projected actual time is
E0's measured 8.61 h, the validator's formula worst case is 10.00 h against an 11.0 h gate, and the one change
that touches runtime (#4) removes work. No change here can lengthen a task. The residual risk is behavioural
(the agent performing worse), which costs a score but not the run.

Accepted knowingly, and recorded here rather than silently.

---

## 6. Outcome (added 2026-10-23, after grading)

**Score: 0.13 = 8/58.** Section 4's readings are **not revised** -- this section records what happened
against them, which is the point of pre-registering.

The relevant row of the section 4 table is **0.10 - 0.15: "Inside noise. The modal outcome, and
uninformative."** That is what we got, and the stated next action ("Do not iterate on the LB. Spend the next
quota on the E0 dev-48 **repeat baseline**") stands unchanged.

| quantity | value |
|---|---|
| score / tasks | 0.13 = 8/58 |
| vs previous best (7/58) | +1 task, Fisher exact **p = 1.0000** |
| pre-committed threshold | k >= 10 (0.17) -- **not crossed** |
| likelihood of k=8 under no-effect (5.67/58) | 0.0933 |
| likelihood of k=8 under their v19 (11/58) | 0.0871 |
| **likelihood ratio no-effect : v19** | **1.07 : 1** |
| likelihood ratio no-effect : v24 (14/58) | 4.21 : 1 |

A likelihood ratio of 1.07 : 1 means this submission carries **essentially zero evidential weight** between
"the four changes did nothing" and "they work as well as the rank-3 team's v19". The only hypothesis it bears
on is v24-level capability, which it disfavours ~4 : 1.

**The dispersion test is the finding worth keeping.** Four scored submissions on the identical 58 public tasks
now read **4, 7, 6, 8** (mean 6.25, sd 1.71). Pooled p = 25/232 = 0.1078; observed between-run variance
**2.92** against a binomial expectation of **5.58**; dispersion X2 = 1.57 on 3 df, **p = 0.67**. The spread
between four *different configurations* is smaller than coin-flip noise predicts for four reruns of *one*
configuration. **There is no evidence that any of our four variants differs from any other.** This is section
3's "no single-variable test is resolvable at this MDE" confirmed the hard way, and it is the direct argument
for buying the repeat baseline before spending another slot.

**What the slot did buy, both minor but real:** a score returned at all, which is the **fourth** confirmation
of the ~10 h budget path; and at 8 tasks we sit far above the pre-registered `<= 0.08` regression line, so
temperature 1.0, the 6-tool set and the prompt surgery are **behaviourally safe**. Deleting the repro-file
phase that EXP-009 Part C priced at 27.3% of wall-clock cost nothing measurable -- mild evidence it was never
load-bearing.

Kaggle submission ref **57539741**, accepted 2026-10-22 22:25:34 UTC, graded 2026-10-23.
