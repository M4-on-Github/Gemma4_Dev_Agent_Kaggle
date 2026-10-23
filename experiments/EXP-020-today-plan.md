# EXP-020 -- Today's plan (2026-10-23): submission #6 generation-budget swing + a one-hour knob-liveness run

**Date authored:** 2026-10-23. **Authoring GPU cost: zero.** Nothing in this document has been applied:
`submission/` is untouched, no zip was built, no kernel was pushed, no submission was made.

**This document was written before either action was taken. The readings in sections 2.7 and 3.6 are
pre-registered and must not be revised after seeing a result.** Repo convention (plan.md section 5.8): the
reading is written down first, and the number that comes back is read against it, not the other way round.

**Settled premise, not re-argued here:** we submit today. Slots are use-it-or-lose-it, do not convert into GPU
quota, and ~40 remain against 1/day to Dec 2; GPU quota (30 L4x4-h/week) is the scarce resource, not slots. The
leaderboard shows each team's *best* submission, so a bad score cannot lower our standing. `submissions.md`
row 5 already pre-registered exactly this logic. This document only decides *what* to spend the slot on.

**The design constraint that drives everything below:** our minimum detectable effect is ~4 LB tasks (~0.07).
Four scored submissions on the identical 58 public tasks returned 4, 7, 6, 8 (pooled p = 25/232 = 0.1078, sd
2.36 resolves), and the dispersion test gives X2 = 1.57 on 3 df, p = 0.67 -- the spread across four *different*
configs is smaller than noise predicts for four reruns of *one*. Submissions #3, #4 and #5 each proved this the
hard way. A small careful tweak is therefore guaranteed unreadable, and the only defensible use of a free slot
is a **large swing on a knob that is measurably live**. Section 2.4 argues why the swing chosen here is the
largest such swing still available inside the timeout gate, and section 2.5 states the counter-evidence against
it.

---

## 1. Repo facts that contradict the context I was handed

I was asked to verify the time-ladder and gate numbers against the repo rather than trust a summary. Five
things disagree. All five are measured from files in this repo, with the inputs named so each can be
recomputed.

### 1.1 The "5.5-6.0 min is the most promising untested region" claim does not survive

The ladder I was given (4.0 -> 7.51 h, 5.0 -> 8.92, 6.0 -> 9.97, 7.0 -> 10.75, 8.0 -> 11.30) appears nowhere in
the repo: `grep -rn "9\.47|10\.41|7\.51|8\.92|10\.75|11\.30" --include=*.md .` returns nothing. I re-derived it
and three alternatives from the raw `task_results.jsonl` of the only two dev-48 agent runs that exist. All
hours are per-task figures x120; where two numbers are given, the second adds the measured 461.8 s notebook
startup.

| `max_time_minutes` | A: censor EXP-003 durations at cap (= the ladder I was given) | B: EXP-003's 28 call-uncensored tasks only | C: hybrid -- EXP-003's 18 measured self-stoppers keep their durations, everything else runs to cap | D: the ladder recorded in EXP-016 section 3 |
|---|---|---|---|---|
| 4.0 | 7.51 | 7.29 | 7.58 / 7.71 | 7.67 / 7.80 |
| 4.5 | 8.27 | -- | 8.43 / 8.55 | 8.49 / 8.61 |
| 5.0 | 8.92 | -- | 9.22 / 9.34 | 9.30 / 9.43 |
| 5.5 | 9.47 | -- | 9.97 / 10.10 | 10.11 / 10.24 |
| 6.0 | 9.97 | 9.78 | 10.70 / 10.83 | 10.92 / 11.05 |
| 7.0 | 10.75 | -- | 12.09 / 12.21 | 12.55 / 12.68 |
| 8.0 | 11.30 | 11.47 | 13.36 / 13.49 | 14.17 / 14.30 |

Ladder A is biased **downward**, and the reason is mechanical: **20 of EXP-003's 48 tasks (41.7%) were ended by
its 28-call cap, not by time.** Censoring their durations at a time cap records them as cheap, but under our
45-call cap those same tasks would have kept running to the time cap. Ladder C is the defensible model for a
45-call config. Against the ~10.5 h operational ceiling (plan.md section 5.8): **6.0 min is not reachable**
(10.70-10.92 h), and 5.5 min sits exactly on it (9.97-10.11 h). The region I was told was "most promising and
untested" is in fact the region the ceiling forbids. Ladder D, which the repo already records, agrees.

### 1.2 A dev-48 run costs ~3.58 h of kernel wall-clock, not ~8.6 h

From `runs/E0-dev48-baseline/gemma4-e0-dev48-baseline.log`: wheels 41/41 at t=63.3 s, required packages
t=91.9, **vLLM up in 348.9 s at t=448.4**, decode probe `{'completion_tokens': 400, 'seconds': 13.25, 'tok_s':
30.2}` at t=461.6, first task done t=717.3, **last event t=12,878.6 s = 3.577 h for 48 tasks**. So fixed
pre-task overhead is **461.8 s (7.7 min), measured**, and the marginal cost is (12,878.6 - 461.8)/48 = 258.7 s
per task.

**8.61 h is the 120-task projection, not the run cost.** This matters for what is affordable: 30 L4x4-h/week
buys roughly **7-9 dev-48 runs**, not 3.5. The EXP-009 Part C4 repeat baseline (2 x dev-48 ~ 7.2 h) is therefore
affordable on *quota*; what it does not fit is a *one-hour* wall-clock box (section 3.1).

### 1.3 The packer formula gate pins `max_time_minutes` at <= 4.5

`tools/validate_submission.py:worst_case_hours()` computes `120 x (max_time_minutes + 1.0 setup)/60` and errors
when `hours > PACK_GATE_HOURS + 1e-9` with `PACK_GATE_HOURS = 11.0` (`tools/submission_rules.py`). So 4.0 ->
10.00 h; **4.5 -> exactly 11.00 h, which passes** (the test is strictly greater-than, and submission #1 shipped
at 4.5); 5.0 -> 12.00 h, a hard error needing `--skip-budget-gate`, which stamps the build "UNOFFICIAL TEST
BUILD ONLY" and which plan.md section 5.8 only permits with an explicitly recorded decision. **4.5 is the
largest time cap reachable without an override**, independent of any ladder.

### 1.4 `max_output_tokens: 4096` is not binding today, but it *becomes* binding the moment thinking rises

EXP-018 retracted the premise behind `max_output_tokens: 4096` and argued a low cap makes mid-tool-call
truncation *more* likely. Measured over every turn in both dev-48 runs, that risk is currently ~zero but is
real at thinking 4096:

| Run (thinking / output) | turns | turns with completion_tokens > 2048 | > 3072 | > 4096 |
|---|---|---|---|---|
| E0 (256 / 4096) | 1,753 | 1 (0.06%) | 1 (0.06%) | **0 (0.00%)** |
| EXP-003 (4096 / 8192) | 1,424 | 28 (1.97%) | 18 (1.26%) | **13 (0.91%)** |

So under `thinking_budget: 256`, **not one turn in 1,753 came within 1 KB of the 4096 output cap** -- raising
the cap on its own would change nothing, and EXP-018's truncation worry is theoretically right but empirically
inert. Under `thinking_budget: 4096`, **13 turns in 1,424 (0.91%) exceeded 4096 completion tokens**, i.e. about
0.27 turns per task, so roughly one task in four would suffer a clipped turn. This reframes the knob:
`max_output_tokens: 8192` is **not** part of the swing, it is the **enabling condition** for the swing. Raising
thinking to 4096 while leaving output at 4096 would manufacture exactly the mid-tool-call truncation failure
EXP-018 warned about.

### 1.5 `max_time_minutes: 4.5` is not a new value -- it is E0's own measured value

`submission/eval_config.yaml:35` already says so ("E0 was 4.5"), E0's traces show a 270 s cap (smoke-8 durations
272-282 s), and EXP-017 section 2 records E0's **measured** 8.61 h projected-actual at that cap. The current
4.0 is a *reduction* from the only config we have ever measured end-to-end, taken as a post-timeout flinch
after submission #2; EXP-018 priced that flinch at ~0.4 LB tasks and marked it "NOT justified". Returning to 4.5
restores a measured configuration rather than extrapolating to a new one -- which is why the runtime claim in
section 2.3 is a measurement, not a model.

### 1.6 One further correction to a number in my own briefing

EXP-016 records 38/48 = 79.2% of E0 tasks ended by the time cap. Classifying with `duration_s >= cap - 20 s` I
get 39/48 = 81.2%. This is a classifier-threshold difference, not a contradiction, and nothing below depends on
which is used.

---

## 2. Design (A) -- submission #6: the generation-budget swing

### 2.1 The diff

Three values in two files. Nothing else changes: no prompt edit, no `agent.yaml` change, no tool-set change.

| # | File | Key | From | To | Role |
|---|---|---|---|---|---|
| 1 | `submission/configs/sampling.yaml` | `thinking_config.thinking_budget` | `256` | `4096` | **the swing** (+1,500%) |
| 2 | `submission/configs/sampling.yaml` | `max_output_tokens` | `4096` | `8192` | enabling condition for #1 (section 1.4) |
| 3 | `submission/eval_config.yaml` | `evaluation.max_time_minutes` | `4.0` | `4.5` | restores E0's measured cap; pays for #1 |

This is **EXP-014**, the action the repo already pre-identified. EXP-017 section 1 deferred precisely these two
sampling keys in these words: "`thinking_budget: 256`, `max_output_tokens: 4096` -- these *cost* wall-clock per
step ... **Held for EXP-014, after prompt surgery has created headroom.**" Submission #5 did that prompt
surgery (REPRODUCE 6 calls -> 2, first-edit deadline 25 -> 12) and scored 0.13 = 8/58, our best of five and a
behavioural all-clear. The precondition EXP-017 named has been met; this is the deferred move, not a new idea.

**Deliberately NOT changed, each with the measurement that rules it out:**

- `max_tool_calls: 45` -> 28 (the rank-3 value). EXP-003's 28-call cohort resolved **0 of 20**. Copying it would
  cost resolves. Nor is raising it worth anything: E0's calls were mean 31.5, median 31.5, **1 of 48 tasks at the
  45 cap**, and change #1 *reduces* turns per task, so 45 binds even less after this diff. (This independently
  reproduces the figure already written at `eval_config.yaml:32`.)
- `max_turns: 70`. E0's measured maximum was 53 LLM calls (mean 34.5); it cannot bind, and change #1 pushes
  turns down, not up. Raising it to the rank-3 value of 80 would be cosmetic, and a cosmetic key in the diff
  dilutes the read.
- `timeout_seconds: 300` -> 240 (the rank-3 value). Our own comment at `eval_config.yaml:38-40` records two
  reasons: per the community source reading this *also* caps the Phase-2 grading pytest, and the command timeout
  is `min(timeout_seconds, remaining task time)`, so 300 already costs nothing.
- `max_time_minutes` above 4.5. Blocked by the formula gate (section 1.3) and worthless on our own data
  (section 2.5, last bullet).
- The prompt, including the 3,508 B vendoring block. Spent in #5 and read null; re-cutting it now would confound
  the one knob this slot is testing.

### 2.2 Why `thinking_budget` is the knob

Measured paired across all 48 dev-48 tasks (per-task means, paired t on 47 df):

| Quantity | E0 (thinking 256) | EXP-003 (thinking 4096) | paired diff | sd_d | t | paired MDE at 80% power |
|---|---|---|---|---|---|---|
| mean completion tokens/turn | 194.7 | 311.4 | **+116.7** | 113.8 | +7.11 | 53.5 |
| mean seconds/turn | 7.09 | 11.62 | **+4.53** | 4.38 | +7.17 | 2.06 |
| turns/task | 36.5 | 29.7 | **-6.85** | 9.36 | -5.07 | 4.40 |

The knob is unambiguously live on behaviour: it moves tokens per turn by +60% and seconds per turn by +64%,
both at t > 7. And per-turn wall-clock is **98-99% decode** in both runs (implied decode 32.4 and 32.2 tok/s
against the 30.2 tok/s probe), so this is the only knob we have found that directly sets the exchange rate
between depth and breadth on the binding resource. At a 270 s cap and ~32 tok/s a task has ~8,600 decode tokens
to spend; change #1 re-spends them as roughly 26 deeper turns instead of 36.5 shallow ones. That is the whole
bet, and it is not reckless: EXP-003's resolved tasks needed a median of 26 turns (min 20, max 35), so ~26
turns is inside the resolving range rather than below it.

### 2.3 Runtime against the gate

Validator output on a scratchpad copy of the tree carrying all three proposed values (`submission/` itself
untouched, no zip built):

```
tools/validate_submission.py <scratchpad copy>/submission --strict
  info  10 files, 24.7 KiB unpacked
  info  1 agent(s): swe_coder; instruction chars: 11226
  info  eval_config.yaml: worst case 120 x (4.5 + 1.0 setup) min = 11.00 h (gate 11.0 h, limit 12.0 h)
  RESULT: VALID (0 errors, 6 warnings)
```

All 6 warnings are the pre-existing unreferenced-file notices (`adapters/README.md`,
`configs/sampling_nothink.yaml`, `prompts/analyzer.md`, two `skills/*/SKILL.md`, `sub_agents/analyzer.yaml`),
unchanged by this edit. **No `--skip-budget-gate` is used or needed.**

| Figure | Hours | Basis |
|---|---|---|
| Formula worst case (what the packer gates on) | **11.00** | `120 x (4.5 + 1.0)/60`, exactly the 11.0 h gate, passes |
| **Hard physical upper bound** | **9.71** | `120 x (270 s cap + 3.3 s setup + 14.0 s grading)/3600 + 461.8 s startup`; all four inputs measured |
| Projected actual | **8.6 - 8.9** | E0's measured 8.61 h at this exact cap (EXP-017 section 2), plus a small allowance for self-stoppers that now run longer |
| Operational ceiling | 10.5 | plan.md section 5.8 |
| Hard limit (scores ZERO) | 12.0 | `RUN_BUDGET_HOURS` |

The safety argument is structural, not statistical: **none of the three changes can extend a task past
`max_time_minutes`.** The harness cuts the agent loop at the cap and grades whatever is on disk. Changes #1 and
#2 can only alter how a task spends its 270 s, never how many seconds it gets. So 9.71 h is a true upper bound
over *any* behaviour the model might produce, with 2.3 h of headroom to the 12 h limit, and the only way to
exceed it is for a measured input (startup, setup, grading, or the cap's enforcement) to be wrong. That is
exactly the risk submission #2 realised, and it is the one thing design (B) checks before we ship.

### 2.4 Why this is the largest readable swing still available

1. **The other half of the rank-3 bundle is already spent.** EXP-016 priced the rank-3 LB-0.24 configuration at
   ~+4 tasks over their own v19, and the v19 -> v24 diff was temperature alone. Submission #5 took temperature
   1.0, their 6-tool set, their first-edit-by-call-12 rule and their cheap-reproduction rule, and read null.
   `top_p: 0.95` and `top_k: 64` already matched theirs. **After this diff our configuration differs from the
   LB-0.24 bundle in exactly two knobs**, both deliberate: `max_tool_calls` (45 vs their 28, because their value
   resolved 0/20 for us) and `max_time_minutes` (4.5, gate-forced), plus the prompt. The generation-budget half
   is the untried remainder of the only externally validated configuration we have.
2. **Every other knob is measured dead or measured harmful.** `max_tool_calls`: 1/48 at cap. `max_turns`: max 53
   of 70. `timeout_seconds`: `min()`-shadowed. `max_time_minutes` beyond 4.5: gate-blocked *and* worth zero
   measured resolves (section 2.5). Lowering `thinking_budget` toward 0 to buy more turns is the only other live
   direction, and it runs against both our paired data and the external evidence.
3. **It is the only knob with a positive paired direction on resolves.** Section 2.5 gives the number -- it is
   small, and I am not going to dress it up.
4. **It is large in the units that matter.** +1,500% on the knob, +60% tokens/turn, +64% s/turn, -19%
   turns/task, all at t > 5 paired. Whatever this does to the score, it is not a small careful tweak, which is
   the failure mode of #3, #4 and #5.

### 2.5 The counter-evidence, stated before the result

**This is the honest case against the diff, and it is not weak.**

- **EXP-003 resolved fewer tasks than E0.** On dev-48: E0 11/48 = 22.9% (Wilson 13.3-36.5%), EXP-003 9/48 =
  18.8% (10.2-31.9%). The paired table is both 6, E0-only 5, EXP-003-only 3, neither 34; exact McNemar p =
  0.7266. Taken at face value, the high-thinking config is 2 tasks *worse*.
- **Removing the call-cap confound reverses the direction, but not by much.** On the 28 tasks where EXP-003's
  28-call cap did not bind, E0 resolved 7 and EXP-003 resolved 9 (discordant 1 vs 3, exact McNemar p = 0.6250).
  EXP-003's three unique wins were `fastapi_15589`, `fastapi_5624`, `fastapi_9753`.
- **One of those three is bought by the time cap, not the thinking budget.** EXP-003 ran a 480 s cap. Censoring
  its resolves by last-edit time: 270 s retains 8 of 9, and only `fastapi_15589` (last edit 414.2 s) needs more
  -- and `fastapi_15589` is one of the three unique wins. So at a matched 270 s cap the isolated comparison is
  roughly **8 vs 7 on 28 tasks, i.e. +1**.
- **Scaled to the public 58, our own data prices this swing at +2 to +4 tasks**, i.e. straddling the ~4-task MDE
  from below. The external evidence (~+4) sits at the top of that range. **I am not claiming this swing is
  comfortably above the MDE. It is at its edge** -- see the explicit power numbers at the end of section 2.7.
- **EXP-003 is a confounded witness in both directions.** It differed from E0 in thinking budget, output cap,
  call cap *and* time cap simultaneously. It is the only evidence we have on thinking 4096, and it is bad
  evidence. That is the strongest single argument for design (B).
- **A time cap above 4.5 min is worth a measured zero**, which is why change #3 is 4.5 and not an override. The
  quantity a cap must exceed is the *last useful edit*, not task duration, because edits on disk are graded.
  Resolves retained by cap: E0 -- 210 s: 9/11, 240 s: 10/11, 270 s: 11/11, and 300-480 s: still 11/11 (latest
  last edit `fastapi_14301` at 261.9 s). EXP-003 (cap 480 s, the only run where late edits are observable) --
  210 s: 7/9, 240 s: 8/9, 270 through 390 s: 8/9, 480 s: 9/9. So 4.0 -> 4.5 buys about +1/48 (~+1.2 LB tasks)
  and 4.5 -> 5.5 buys **nothing measurable**.

### 2.6 Threshold decode -- so the reading table cannot be ambiguous

The public score is `floor(k/58*100)/100` on k resolved of 58. The reachable scores near our range:

| k | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 |
|---|---|---|---|---|---|---|---|---|---|
| score | 0.10 | 0.12 | **0.13 (= #5, current best)** | 0.15 | **0.17** | 0.18 | **0.20** | 0.22 | 0.24 |

**No score can land on 0.11, 0.14, 0.16, 0.19, 0.21 or 0.23.** In particular nothing lands on 0.16, so "0.17"
and "k >= 10" are the same statement with no boundary case, and "0.20" and "k >= 12" likewise. Every threshold
below is written as an integer k; the score is given only as a convenience.

### 2.7 Pre-registered readings for submission #6

Computed against the pooled no-effect rate p0 = 25/232 = 0.1078 (mean 6.25, sd 2.36), against a +2-task
alternative (p = 0.1422) and against the +4-task alternative that EXP-016 prices the rank-3 config at
(p = 0.1767).

| Outcome | k | Pre-registered reading -- written now, not revised later |
|---|---|---|
| **blank / error / zero** | -- | **The runtime model is falsified, and that is the finding.** Section 2.3 gives a 9.71 h hard upper bound from four measured inputs with 2.3 h of headroom; a timeout means one of startup (461.8 s), setup (3.3 s/task), grading (14.0 s/task) or the cap's enforcement is wrong. Revert all three changes, re-ship the 4.0 tree, and open an experiment on which input broke. This is the only unambiguous reading on the table. |
| **<= 0.05** | <= 3 | **Behavioural regression: revert.** P = 11.6% under no-effect but 0.5% under +4, so ~23:1 evidence against the swing. Most likely mechanism: 26 turns is below what these tasks need, i.e. we bought depth we could not afford. |
| **0.06 - 0.08** | 4 - 5 | **Uninformative, lean negative.** P = 27.9% under no-effect, 14.7% under +4. Do not revert on this alone; do not adopt. Our four scored runs already include a 4. |
| **0.10 - 0.15** | 6 - 9 | **Uninformative. The swing is neither adopted nor rejected.** This band holds 51.5% of the no-effect mass and 34.6% of the +4 mass -- it is where a free slot lands by default. If this happens, the correct conclusion is the one submission #5 already reached: the slot was spent correctly and returned nothing, and the next move is dev-48 quota, not another slot. |
| **0.17 - 0.18** | 10 - 11 | **Consistent with the +4 effect, not separable from noise.** Likelihood ratio (+4 vs no-effect) is 2.96:1 at k=10 and 5.26:1 at k=11. Keep the three changes in the tree as the new baseline, but **do not** record the swing as established and do not let it license a third knob. Field position for context: EXP-019 puts >= 0.17 in the top 34.1%. |
| **>= 0.20** | >= 12 | **Adopt: the swing is established at this repo's evidence bar.** P = 1.94% under no-effect, LR >= 9.35:1, and >= 0.20 is the top 5.6% of the 3,505-team field. Make the three values canonical and spend the next dev-48 run confirming rather than exploring. |

**Power, stated before the fact.** Primary threshold k >= 10 (0.17), chosen for continuity with submission #5's
pre-registration: false-positive rate **9.0%**, power **58.8%** if the effect is truly +4 tasks, **30.7%** if it
is +2, **81.0%** if it is +6. At the stricter k >= 12: false-positive rate 1.9%, power 32.3% at +4. **So the
most likely single outcome of this slot is still "uninformative", and that is a property of a 58-task
leaderboard, not of this design.** Submission #5's doc put it correctly and it still holds: this slot is a
cheap, properly-powered test of a large effect and near-powerless below that; spending it is right, expecting
information from it is not.

### 2.8 Deviation from plan.md section 5.8

Section 5.8 asks for a dev-48 validation run before a submission. There is none here, for the same reason as
#5: a dev-48 run is ~3.58 h of kernel wall-clock and the slot expires today. Design (B) is the partial
mitigation and it is deliberately scoped to the one thing a short run *can* establish (section 3.3). The
`--skip-budget-gate` escape hatch is **not** used: the build passes the official gate at exactly 11.00 h.

### 2.9 Mechanical steps for the user, in order

1. Apply the three values in section 2.1 by hand. Nothing else in `submission/` changes.
2. `python tools/validate_submission.py submission --strict --official` and confirm the
   `worst case 120 x (4.5 + 1.0 setup) min = 11.00 h` line and `0 errors`.
3. Pack the zip and record its sha256 in `submissions.md` as row 6, together with the thresholds from section
   2.7, **before** pushing anything.
4. If running design (B) first (recommended, section 3.8), use **this** zip for it, so the calibration and the
   submission are the same artifact.
5. Submit. Record the ref id and the pending state in `submissions.md` row 6.

---

## 3. Design (B) -- a one-hour run: is the knob we just bet on actually connected?

### 3.1 The pre-registered right experiment does not fit in an hour, and I will not pretend otherwise

EXP-009 Part C4 specifies the same-config repeat baseline: only three directories under `runs/` have
`task_results.jsonl` (`E0-dev48-baseline`, `exp002_estop_a_smoke8`, `exp003_public_budget_dev48`), **no
same-config agent repeat exists anywhere in this repo**, and re-running E0 on dev-48 is recorded there as "the
single highest-value quota purchase available". It needs 2 x 3.58 h = ~7.2 h of kernel wall-clock. That is
affordable on quota (section 1.2) and impossible inside a one-hour box. **Design (B) is explicitly NOT the
pre-registered action.** It does not advance C4 by a single data point, because it runs a different
configuration.

### 3.2 What a one-hour run cannot do -- quantified, not waved

A one-hour box allows about 8-10 tasks: 461.8 s measured startup plus 8 x (270 + 3.3 + 14.0) s worst case =
2,760 s = **46.0 min**. At n=8 the statistical endpoints are dead:

- **Resolve rate.** At E0's 22.9% the expectation is 1.8 resolves with sd 1.19. The Wilson 95% interval for 2/8
  is **7.1% - 59.1%**; for 1/6 it is 3.0% - 56.4%. That interval contains both "half of E0's rate" and "double
  it". It cannot calibrate a noise floor, which is what C4 exists to do.
- **Paired resolve flips.** This is worse than imprecise, it is arithmetically impossible. With 8 paired tasks
  the exact two-sided McNemar p-value when *every* discordant pair falls the same way is 0.500 at 2 discordant
  pairs, 0.250 at 3, 0.125 at 4, 0.0625 at 5, and only reaches **0.0312 at 6**. So **6 of 8 tasks would have to
  flip in the same direction** to clear p < 0.05, against an expected 1-3 discordant pairs. A smoke-8 resolve
  comparison cannot return a significant result in practice.
- **Even the mechanism endpoint is marginal at n=8.** Paired on the smoke-8 subset, the MDE at 80% power for
  mean seconds/turn is **4.55 s**, against an expected effect of **4.53 s** from the full dev-48 pair -- i.e.
  about 50% power. The same comparison restricted to smoke-8 in the existing data gave +1.92 s, t = 1.38, not
  significant, where the full 48-task pair gave +4.53 s, t = 7.17. On dev-48 the MDE is 2.06 s. **A one-hour run
  is underpowered even for the per-turn mechanism**, and anyone claiming otherwise is reading the dev-48 t
  statistic and quietly attaching it to an 8-task design.

Conclusion: **no one-hour experiment is adequately powered for any comparative question we care about.** The
only honest one-hour design is therefore one whose endpoint is near-deterministic rather than statistical.

### 3.3 What it can do: knob liveness and runtime safety

Two questions about design (A) are **binary and large-effect**, and n=8 settles both.

**Q1 -- is `thinking_budget` actually enforced?** This is still formally open in the repo. The validator prints
`info agent.yaml: thinking ON (VERIFY(Q3): thinking_budget may not be enforced by the harness)`, and
`sampling.yaml:7` records that a pre-push review confirmed it is forwarded to vLLM -- confirmed by *source
reading*, never by measurement on our own tree. If it is not enforced, **the entire swing in design (A) is a
no-op** and submission #6's score is a pure noise re-draw that must not be read as evidence about generation
budget at all. The measurement is a large shift in a quantity with ~240 observations: E0's smoke-8 mean
completion tokens/turn is **206.7**, and EXP-003 at thinking 4096 gave **268.5** on the same 8 tasks (311.4 on
all 48). Post-run the test is a threshold, not a t-test: near 207 means the knob is dead, 260+ means it is live.

**Q2 -- does the 9.71 h hard bound hold?** Section 2.3's bound rests on four measured inputs. An 8-task run
re-measures all four under the *exact* submitted artifact: startup seconds, per-task setup, per-task grading,
and above all whether any task's `duration_s` exceeds the 270 s cap. This is the failure mode that cost us
submission #2 (a scored zero), and it is deterministic -- one task over the cap falsifies it.

**Cohort.** `experiments/cohorts/smoke-8.txt` (fastapi_14301, fastapi_14448, fastapi_14605, httpx_3672,
requests_7205, requests_7309, rich_3006, rich_3468), generated by
`python tools/make_cohorts.py --tasks data/raw/tasks.jsonl --exclude runs/EXP-000/gold_failures.txt --seed 20261013`.
**It is a strict subset of dev-48 and both existing runs cover all 8 of its tasks**, so every quantity above is
paired against two measured baselines on identical tasks. Known limitation: it is repo-skewed (3 fastapi, 2
requests, 2 rich, 1 httpx) and `rich_3006` is a fast self-stopper (80.7 s in E0, 90.8 s in EXP-003), so
effectively 7 tasks exercise the cap. For a liveness check that skew is tolerable; for a resolve-rate estimate
it would not be, which is another reason resolve rate is not an endpoint here.

### 3.4 Exact commands

Run against the **same** zip that will be submitted, after step 3 of section 2.9.

```
python tools/build_notebook.py \
  --embed dist/submission.zip \
  --set EXP_ID='"EXP-020-thinking-liveness-smoke8"' \
  --set RUN_PHASE0_CHECKS=True \
  --set RUN_GOLD_CONTROL=False \
  --set RUN_AGENT=True \
  --set MEASURE_DECODE_SPEED=True \
  --set TASK_IDS='["fastapi_14301","fastapi_14448","fastapi_14605","httpx_3672","requests_7205","requests_7309","rich_3006","rich_3468"]' \
  --out notebooks/exp020/kaggle_eval_l4x4.ipynb

kaggle kernels push -p notebooks/exp020
```

`--set` inserts the value verbatim as Python source and fails loudly on an unknown name, so the quoting above is
deliberate: `EXP_ID` and `TASK_IDS` must arrive as Python literals. `TASK_IDS` takes precedence over `N_TASKS`
in the notebook's selection logic (`notebooks/kaggle_eval_l4x4.py:190`), so `N_TASKS` needs no override.
`RUN_PHASE0_CHECKS=True` is kept because it is pre-server, costs about a minute, and is the cell that addresses
the Q3 thinking-enforcement question directly. `RUN_GOLD_CONTROL=False` because EXP-000 already did it and it
would burn cap time for nothing. Accelerator **L4 x4**, internet off, and the three inputs attached per the
notebook header (competition `gemma-4-developer-agent`, dataset
`metric/gemma-4-developer-agent-wheelhouse`, model `google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2`).

Afterwards, download `/kaggle/working/runs/EXP-020-thinking-liveness-smoke8.zip` and run:

```
python tools/analyze_traces.py runs/EXP-020-thinking-liveness-smoke8
python tools/estimate_budget.py runs/EXP-020-thinking-liveness-smoke8
```

### 3.5 GPU cost

| Component | Seconds | Basis |
|---|---|---|
| Startup (wheels, vLLM, decode probe) | 461.8 | measured, E0 kernel log |
| Phase-0 checks | ~60 | estimate, pre-server |
| 8 tasks worst case at the 4.5 min cap | 8 x 287.3 = 2,298 | 270 cap + 3.3 setup + 14.0 grading, all measured |
| **Total worst case** | **2,820 s = 47.0 min = 0.78 h** | |

**GPU cost: ~0.8 L4x4-hours, 1.0 even rounding up generously.** The quota unit in plan.md section 5.7 is L4x4
session hours against 30/week, consistent with plan.md:269's "~1 GPU-h per 10 tasks". Expected actual is below
worst case because `rich_3006` self-stops. **Assumption to check before pushing: that this week's 30 L4x4-h are
substantially unspent.** EXP-016 through EXP-019 were all zero-GPU and the last agent runs are much older, so
the week is almost certainly clean -- but current quota consumption is not visible from inside the repo and the
user should confirm it on Kaggle.

### 3.6 Pre-registered readings for design (B)

| Observation | Pre-registered reading |
|---|---|
| mean completion tokens/turn **>= 250** | `thinking_budget` is live and roughly as costly as EXP-003 measured. Design (A)'s swing is real and the LB score can be read as evidence about generation budget. Proceed exactly as in section 2.7. |
| mean completion tokens/turn **200 - 250** | Partially enforced, or shifted by task mix. Design (A) still ships unchanged, but **section 2.7's adopt threshold is not relaxed** and the swing's effective size is smaller than designed, so a 0.17-0.18 reading stays "not separable". |
| mean completion tokens/turn **< 200** (indistinguishable from E0's 206.7 on these same 8 tasks) | **`thinking_budget` is not enforced on our tree. VERIFY(Q3) resolves negative.** This is the highest-value outcome available from one hour: changes #1 and #2 are inert, submission #6's score carries no information about generation budget, and EXP-014 as specified is unrunnable. Record it against section 2.7 and treat #6's score as a fifth no-effect sample. Do **not** revert change #3, which is independent. |
| **any** task with `duration_s` > 285 s | The cap is not enforced as modelled and the 9.71 h bound is void. **If seen before submitting, revert `max_time_minutes` to 4.0 and re-validate**; the submission still goes out today with changes #1 and #2 only. |
| startup > 700 s, or setup/grading per task materially above 3.3 s / 14.0 s | Re-derive the section 2.3 bound with the new inputs before submitting. There is 2.3 h of headroom to the 12 h limit, so this is unlikely to change the decision, but it must be recomputed rather than assumed. |
| resolves on the 8 tasks (any value, 0 through 8) | **Not an endpoint. Pre-registered as uninformative and recorded without interpretation.** E0 resolved 2/8 and EXP-003 resolved 2/8 on this cohort; per section 3.2 a Wilson interval of 7.1-59.1% and a minimum achievable paired p of 0.50 at 2 discordant pairs mean no resolve count here licenses any conclusion. **Writing this down now is the point: it is the number we will be most tempted to read, and it is the one we must not.** |

### 3.7 What (B) licenses and what it does not

**Licenses:** a yes/no on whether `thinking_budget` is enforced on our own tree (closing VERIFY(Q3) by
measurement rather than source reading); a re-measurement of all four inputs to the 9.71 h bound under the exact
submitted artifact; a paired per-turn cost figure on 8 tasks against two existing baselines; and a go/no-go on
change #3 before the slot is spent.

**Does not license:** any statement about resolve rate, any statement about whether the swing helps, any
contribution to the EXP-009 C4 noise floor, and any generalisation from a repo-skewed 8-task cohort to the 120
hidden tasks. If it comes back with 4/8 resolved, that is not good news; it is noise, and section 3.6 says so in
advance.

### 3.8 Ordering against (A), and why (B) is complementary rather than redundant

**Recommended order: (B) first, then (A).** (B) needs ~47 min of kernel time plus a few minutes of analysis, and
both of its findings are actionable *only* before the slot is spent -- the `duration_s` tripwire can still
revert change #3, and a dead-knob result changes how row 6 of `submissions.md` is written. The submission slot
is not at risk: it expires at 23:59 UTC, not on the hour.

**If the user prefers to submit first, (B) still earns its hour**, and this is pre-registered too: it then
cannot change the artifact, but it determines *how the score is read*. A dead-knob result would retroactively
convert submission #6's number from "a test of generation budget" into "a fifth draw from the no-effect
distribution", and under this repo's rules that reinterpretation is legitimate only because it is written here,
in advance, rather than after the score arrives.

(B) is not a smaller version of (A). (A) spends a free slot on a large swing at 58-task resolution; (B) spends
~0.8 GPU-h checking that the swing is mechanically connected and that the runtime bound holds. Neither answers
the other's question, and the pre-registered right experiment (C4) answers neither -- it remains the correct
next purchase once a 3.6 h block of quota is available, and nothing in this document displaces it.

---

## 4. Outcome (filled in 2026-10-23, after the fact)

Recorded against sections 2.7 and 3.6 as written. Those sections are **not edited**.

- **Submission #6:** Kaggle ref **57574012**, accepted 2026-10-23 22:54:59 UTC, zip sha256
  `45ad01a68412a8b71a24ac5d57fc29012126a297b2df931583631ec26f4d3e00`, message
  `EXP-020 45ad01a6 - thinking_budget 4096 (liveness confirmed), output 8192, cap 4.5`.
  CLI returned "0 submissions remaining today". **Score pending.**
- **EXP-020 smoke-8 run:** kernel `rainm4/gemma4-exp020-thinking-liveness-smoke8` version 1,
  status COMPLETE, 8/8 tasks SUCCESS, 32.82 min of task time, ~0.8 L4x4-hours.

### 4.1 The pre-registered metric came back AMBIGUOUS, and section 3.6 did not disambiguate it

Section 3.6 keys its three readings to "mean completion tokens/turn" without specifying whether that is
**pooled** (total completion tokens / total turns) or the **mean of per-task ratios**. The two give different
answers, so the pre-registered table does not resolve:

| run | thinking_budget | pooled tok/turn | mean of per-task ratios |
|---|---|---|---|
| E0 | 256 | 180.3 | 184.5 |
| EXP-003 | 4096 | 236.8 | 239.6 |
| **EXP-020** | **4096** | **190.9** | **226.0** |

Pooled 190.9 falls in the `< 200` row ("**not enforced**, VERIFY(Q3) resolves negative"); mean-of-ratios 226.0
falls in the `200 - 250` row ("**partially enforced**"). The split is driven by one task, `fastapi_14448`
(620.3 tok/turn over only 11 turns): pooling weights by turn count and mean-of-ratios weights tasks equally.
This is section 3.2's underpowered-at-n=8 warning arriving exactly as predicted.

**Also correct the baselines.** Sections 3.3/3.6 quote E0 at 206.7 and EXP-003 at 268.5 completion tokens/turn
on this cohort. Recomputed from the traces, both are lower (above). The discrepancy is a turn-counting
convention -- `final_metrics.total_steps` includes the 2 non-agent steps (one `system`, one `user`) that every
trace carries, and trace step `source` is `agent`, not `model`. The relative ordering is unaffected, so no
conclusion in this document turns on it, but the absolute thresholds in 3.6 were set against figures that are
~26 tokens/turn too high.

### 4.2 A post-hoc measure settles liveness decisively: the thinking-event ceiling

The traces carry `extra.event_type == "thinking"` steps, so thinking volume is **directly observable** rather
than inferred from aggregate token counts. Section 3.6 did not use this, because the design was written without
knowing the field existed. The decisive quantity is the **maximum** single thinking event, not any mean:

| run | thinking_budget | thinking events | chars/event | **max single event** |
|---|---|---|---|---|
| E0 | 256 | 248 | 402.3 | **1,338** |
| EXP-003 | 4096 | 222 | 721.3 | 17,655 |
| **EXP-020** | **4096** | **211** | **561.5** | **12,055** |

At `thinking_budget: 256`, **no thinking event in any of the 8 tasks exceeded 1,338 characters** (per-task
maxima 1060, 962, 858, 1076, 810, 1131, 1048, 1338). At ~4 chars/token, 256 tokens is ~1,024 chars, so E0's
ceiling sits right at the cap with tokenizer slack: **the 256 cap was binding.** At 4096, **seven of the eight
tasks exceed E0's global maximum**, peaking at 12,055 chars -- 9x E0's ceiling.

**A 12,055-character thinking event cannot be produced under a 256-token cap.** So `thinking_budget` is
enforced on our tree, and **VERIFY(Q3) resolves POSITIVE** after being open on source-reading alone since
2026-10-19. Change #1 is mechanically connected and submission #6 is a genuine configuration change, not a
re-skin of #5.

**The epistemic cost, stated plainly rather than buried.** This metric is **post hoc**. We pre-registered
tokens/turn, it came back ambiguous, and we then reached for a different measure -- normally the exact move
pre-registration exists to prevent. The defence is that it is a **bound, not a mean**: the inference is a
physical impossibility argument that does not depend on sample size, averaging convention, or task mix, none of
which can manufacture a 12,055-char event under a 1,024-char ceiling. The honest summary is that **3.6 chose
the wrong statistic**, and the right one is near-deterministic where the chosen one was ~50% powered. For
completeness, the paired mean test on thinking chars/event is weak and is **not** relied on: E0 -> EXP-020
mean diff **+369.6 chars, sd 750.6, t = +1.393 on 7 df (not significant), 6 of 8 tasks increased.**

### 4.3 The runtime tripwire did NOT fire; the bound is more conservative than modelled

Section 3.6's tripwire was **any task with `duration_s` > 285 s**. Observed maximum: **279.5 s**
(`fastapi_14301`), with six of eight tasks between 272.6 and 279.5 s. **The tripwire did not fire, so change
#3 stands and `max_time_minutes: 4.5` was not reverted.** For comparison E0, at the identical 4.5-min cap,
reached 282.3 s on this cohort -- also under 285 -- so nothing about the cap's behaviour changed.

Two inputs to the section 2.3 bound came back *better* than assumed: measured **`setup_s` averages 0.03 s**
against plan.md 5.8's assumed 3.3 s, and startup did not exceed 700 s. The 9.71 h hard bound therefore stands
with room to spare, and the 11.00 h formula gate the packer enforces is unchanged.

### 4.4 Non-endpoints, recorded without interpretation per section 3.6

**Resolves: 2 of 8.** E0 resolved 2/8 and EXP-003 resolved 2/8 on this identical cohort. Section 3.6 pre-committed
that no resolve count here licenses any conclusion, and that holds: this is the number we were most tempted to
read, it moved not at all, and **that is neither good news nor bad news.** It contributes nothing to the
EXP-009 C4 noise floor.

### 4.5 What stands after today

1. **Q3 is closed positive.** `thinking_budget` is enforced. Every future experiment touching generation budget
   can now assume the knob is connected -- the single durable result of the day.
2. **Submission #6 is a real swing**, pending a score, read strictly against section 2.7 and **not** revised.
3. **EXP-009 C4 (the same-config repeat baseline) remains the correct next purchase** and nothing today
   displaces it. Section 1.2's correction makes it affordable: a dev-48 run is ~3.58 h of kernel wall-clock, so
   30 L4x4-h/week buys 7-9 runs, and the two-run C4 pair is ~7.2 h. It did not fit a one-hour box; it fits the
   week comfortably.
4. **A hazard worth remembering:** notebook cell 5 sets `max_time_minutes: 60.0` under an
   `if not RUN_AGENT:` guard (so a gold-control pass is not killed by the official sample config's 1-minute demo
   caps). It is inert at `RUN_AGENT=True`, but any future build with `--set RUN_AGENT=False` is one flag from an
   ~8 h kernel.
