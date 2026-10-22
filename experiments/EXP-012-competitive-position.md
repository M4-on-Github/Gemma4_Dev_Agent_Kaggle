# EXP-012 -- competitive position: where we actually stand, and what the top configs do

date: 2026-10-22
type: zero-GPU analysis (leaderboard pull + published-config comparison). No variable changed, no run.
inputs: full public leaderboard (3,467 teams, pulled 2026-10-22 14:34 UTC); three public notebooks
        downloaded and **read only, never executed**; our own `submission/` tree at commit `47e53b0`.

## why this exists

Submission #4 scored **0.10**. The pre-registered reading said that outcome would be uninformative about
the tripwire, and it is. But checking it against the field turned up something the project had not
measured in four submissions: **what a normal entry scores.** It turns out we had been grading ourselves
against a reference class we invented.

## 1. The score decoder is now confirmed exactly

Every one of the 15 distinct scores on the board maps to exactly one task count under 2-dp truncation,
with no gaps and no value above 0.24:

| score | tasks | teams | % of teams at or above |
|---|---|---|---|
| 0.24 | 14 | 4 | 0.1% |
| 0.22 | 13 | 35 | 1.1% |
| 0.20 | 12 | 155 | 5.6% |
| 0.18 | 11 | 426 | 17.9% |
| 0.17 | 10 | **560** | 34.0% |
| 0.15 | 9 | 488 | 48.1% |
| 0.13 | 8 | 354 | 58.3% |
| 0.12 | 7 | 311 | 67.3% |
| **0.10** | **6** | **271** | **75.1%  <-- us** |
| 0.08 | 5 | 222 | 81.5% |
| 0.06 | 4 | 158 | 86.1% |
| 0.05 | 3 | 145 | 90.3% |
| 0.03 | 2 | 115 | 93.6% |
| 0.01 | 1 | 70 | 95.6% |
| 0.00 | 0 | 153 | 100.0% |

`k/58` truncated to 2 dp reproduces all 15 values and nothing else, so score and task count are
interchangeable with certainty. **n = 58 public tasks is confirmed**, not inferred.

## 2. CORRECTION: the "null model" this project has been using was circular

EXP-009 and EXP-010 both reasoned against a null of `p ~ 0.0948`, taken from our own pooled submissions
(11/116, later 17/174 = 9.8%). That is our own performance, so of course our scores were "consistent with
the null". It measured our noise and told us nothing about whether 6 tasks is good.

The leaderboard supplies the real reference class:

| | tasks | score |
|---|---|---|
| median team | 8 | 0.13 |
| modal team (largest bin, 560 teams) | 10 | 0.17 |
| ceiling (4 teams, nobody above) | 14 | 0.24 |
| **us (#4)** | **6** | **0.10** |

**Our observed score ranks at roughly the 25th percentile. 2,333 teams (67.3%) are strictly ahead of
us.** Every conclusion of the form "this change is within noise, so our position is unclear" was answering
the wrong question. The position was never unclear; it was just never checked against the field. Section 2a
below separates which parts of that are statistically solid -- the gap to the top is, the gap to the median
is not.

Note what this does *not* overturn: the ~4-task MDE is still right as a statement about binomial noise on
n = 58, and our three scored submissions (4, 7, 6 tasks on identical tasks; mean 5.67, sd 1.53) confirm it
empirically. Single-day moves below ~0.07 remain unreadable. What changes is the baseline those moves are
measured from.

### 2a. How much of this is solid, and how much is one noisy sample

A single 58-task score is noisy enough that our 6 tasks against the ceiling's 14 is only
`Fisher p = 0.0836` -- not significant. The claim survives anyway, because we have three scored
submissions on the identical 58 tasks and can pool them (17/174 = 9.8%, Wilson 95% CI **6.2-15.1%**):

| comparison | their rate | Fisher exact vs our pooled 17/174 | inside our 95% CI? |
|---|---|---|---|
| median team (8/58) | 13.8% | p = 0.4629 | **yes -- indistinguishable** |
| modal team (10/58) | 17.2% | p = 0.1549 | yes |
| ceiling (14/58) | 24.1% | **p = 0.0125** | **no -- outside** |

So the two claims have genuinely different strengths, and it matters for what we do next:

- **The gap to the top is real.** 24.1% lies outside our pooled CI and the pooled test rejects at
  p = 0.0125. We are not a ceiling-class entry having a bad day.
- **The gap to the median is *not* established.** 13.8% sits inside our CI. "25th percentile" is an
  honest statement about where our observed score ranks among 3,467 teams, but it is not evidence that
  our *true* rate is below the median team's -- on scores alone we cannot tell those apart, and the
  median team's single score is just as noisy as ours.

That is the right reason to aim at the published ceiling config rather than at the middle of the field:
the middle is within noise of where we already are, so beating it is not a measurable goal.

## 3. The ceiling config is public, and it is nearly identical to ours

`honghanhhh/gemma-4-baseline-lb-0-24` (public, LB 0.24 = 14/58) states its own lineage: it is
`flexonafft/gemma-4-budget-aware-coding-agent-v2` (public, 0.22) with `max_time_minutes` 8 -> 7 and
`max_output_tokens` 8192 -> 6144, after an earlier version hit *Notebook Timeout*. Its config, read
directly from the notebook:

| knob | ours (#4, 6/58) | public 0.24 (14/58) |
|---|---|---|
| model | `gemma-4-31b-it-qat-w4a16-ct` | **identical** |
| tool list | 9 tools incl. the 3 graph tools | **identical** |
| temperature / top_p | 0.2 / 0.95 | 0.2 / 0.95 |
| `top_k` | 64 | unset |
| `max_output_tokens` | 4096 | **6144** |
| `thinking_budget` | **256** | **4096** |
| `max_time_minutes` | **4.0** | **7** |
| `max_tool_calls` | 45 | 28 |
| `max_turns` | 70 | 80 |
| `timeout_seconds` | 300 | 240 |

**Same model. Same tools. Same temperature.** The entire 8-task gap sits in the budget and the prompt.

### 3a. The dominant lever is per-task time, and our own safety gate is what blocked it

They run **7 minutes per task; we run 4.0.** Their notebook does the arithmetic openly: `120 x 7 = 14 h`
against the 12 h notebook cap, and they ship it anyway, betting that the average task finishes well short
of the cap. Our `plan.md` 5.8 gate forbids any config whose *worst case* exceeds 11.0 h, which is what
pins us at 4.0 min.

That gate was adopted after submission #2 (the 8-min EXP-003 bundle, 18 h worst case) died of Notebook
Timeout and returned no score. The lesson drawn was "never exceed the gate". The leaderboard says the
lesson should have been "8 is too much, 7 is affordable" -- we over-corrected by 3 minutes a task and have
paid for it in every submission since. Submissions #1, #3 and #4 all finished comfortably, three times
confirming time-safety we did not need to keep re-confirming.

### 3b. Their prompt forbids the single most expensive thing ours mandates

From EXP-009 Part C1, our agent spends **27.3% of all wall-clock generating scratch repro scripts** --
5.2 heredoc writes per task, 11.61 s each -- because `prompts/swe_coder.md` line 102 orders it to
("REPRODUCE (at most 6 calls). Write /tmp/repro.py via a run_command heredoc..."). The 0.24 prompt says:

> "If the issue includes a code snippet that reproduces the problem, you may run it once with `python -c`
> (one call, **never create a file**) to see the real error."

So the behaviour we require is the behaviour they prohibit, and our own forensics had already priced it at
over a quarter of the budget. Combining 3a and 3b:

| | per-task budget | lost to repro writing | effective working time |
|---|---|---|---|
| ours | 4.0 min | 27.3% | **2.91 min** |
| public 0.24 | 7 min | ~0 (one `python -c`) | **~6.9 min** |

That is a **2.4x** difference in usable time, against a **2.3x** difference in resolve rate (10.3% vs
24.1%). The arithmetic agreement is suggestive, not causal -- effective time is not the only difference
and this is two points -- but it is the right order of magnitude to explain the whole gap, and it is the
cheapest thing to test.

### 3c. Four more prompt differences, each matching something we measured independently

| their instruction | what our forensics found |
|---|---|
| "combine independent searches into one `run_command`"; read up to 3 regions per command with `sed` | **0 of 3,177 turns** issued more than one tool call. Every read is a full generation round-trip. |
| "You MUST have edited a source file by call 12" (of 28 = 43% of budget) | Our tripwire fires at call 25 of 45 = 56%. Part C5: winners first edit at 35% of their call cap, empty-patch runs at 87%. **Our threshold is set too late.** |
| "Never use `search_similar_code`, `get_code_neighbors` or `get_code_subgraph`. They return nothing useful." | Part C5 tool histogram: `get_code_neighbors` was called **1 time in 96 task-runs**; the other two never. The agent already discovered this; our prompt still offers them. |
| "If the same behaviour has parallel implementations (sync and async, `Client`/`AsyncClient`, backends, typing overloads, re-exports in `__init__.py` or `__all__`), apply the change to every one." | Not addressed anywhere in our prompt. A plausible contributor to our patch-but-failed cohort (41 of 96 task-runs). |

One place where we are **not** obviously wrong: they instruct `pytest ... -k keyword` on one named test
file, while ours deliberately runs the whole file because "grading runs the full file and one broken test
anywhere in it fails the task". Our reasoning is sound and theirs is faster. This is a genuine open
question, not a copy-this item.

## 4. The local-to-LB gap is explained by task difficulty, not by a bug on our side

Our dev-48 resolve rate is 22.9% (11/48); our LB rate is 9.8% pooled (17/174). A 2.3x drop invites the
theory that something breaks in the submission environment. The leaderboard rules that out: the **best of
3,467 teams scores 24.1%**, which is essentially our local dev-48 rate. If the hidden set were as easy as
dev-48, the leaders would be far above 24%.

So dev-48 is substantially easier than the hidden half -- unsurprising, since it was drawn from the 129
gold-sound tasks after excluding the 18 that fail even with the gold patch (EXP-000). The practical
consequences:

- **Expect roughly 0.4x transfer from dev-48 to the LB.** A dev-48 gain of +5 tasks is worth about +2 LB
  tasks. Combined with the ~4-task LB MDE, a change must be worth **~+10 dev-48 tasks** before the public
  LB can see it. That is why local dev-48 runs, not submissions, have to carry every decision.
- There is no missing-environment bug to hunt. EXP-009 Part C6 already cleared the wheel-pool leak for
  agent runs, and this closes the other half of the question.
- The ceiling at 14/58 across 3,467 teams suggests ~44 of the 58 public tasks are out of reach for any
  Gemma-4 agent in budget. Our realistic target band is **9-14 tasks**, not 58.

## 5. Decision

**Queued, not started.** The three steps below are recorded as the live backlog in `plan.md` §6.1a as **EXP-013 / EXP-014 / EXP-015**, ahead of the whole §6.1 E-series; the gate problem step 3 runs into is noted in `plan.md` §5.8.

**Stop running single-variable experiments from 8 tasks below a published baseline.** At a ~4-task LB MDE
and one submission a day, climbing 6 -> 14 by isolated increments is not reachable in the time left; and
the private half (~62 tasks) decides the final standing, so sitting at the 25th percentile forecloses any
result regardless of how clean the methodology is.

Sequenced, cheapest and least risky first:

1. **Prompt surgery, no budget change (free, no timeout risk, testable on dev-48).** Delete the mandated
   REPRODUCE phase and replace it with the one-shot `python -c` rule; add explicit search/read batching;
   move the first-edit deadline from call 25 to ~call 12-15; drop the graph tools from the prompt and from
   `agent.yaml`; add the parallel-implementations rule. This is the reframed EXP-011 from EXP-009 Part C2
   plus three items the 0.24 prompt supplies, and it *reduces* per-task time, so it strictly improves
   timeout safety.
2. **Raise `thinking_budget` 256 -> 4096 and `max_output_tokens` 4096 -> 6144.** EXP-003 bundled these
   with a call-cap cut to 28 that demonstrably cost a resolve (`rich_3676`), so they have never been
   tested cleanly. 16x more thinking is the second-largest knob gap.
3. **Raise `max_time_minutes` 4.0 -> 6.0, then 7.0 if 6.0 scores.** This requires an explicit, recorded
   override of the `plan.md` 5.8 worst-case gate, which is the correct call now that the gate is known to
   be the binding constraint -- but the override must be deliberate, because this is exactly how
   submission #2 was lost. Step 1 buys time back first, which makes step 3 cheaper than it was for #2.

Steps 1 and 2 need one dev-48 run to check compliance and empty-patch rate, which costs GPU quota. Given
0.4x transfer, the honest expectation for all three together is roughly +4 to +8 LB tasks, i.e. 0.17-0.24
-- the modal-to-ceiling band, not past it.

**On copying:** the 0.24 config is a published Kaggle notebook, and forking public baselines is normal and
permitted practice, but it is worth being clear-eyed that 39 teams already sit at 13-14 tasks running
near-identical configs. Matching it buys a seat in a crowded tie that the private half will then shuffle
by a few tasks in either direction. It is a floor to build from, not a result. The things this project has
that those notebooks do not -- a measured wall-clock breakdown, a confirmed grading-flakiness mechanism,
a calibrated MDE, and the finding that reproduction correlates with *winning* (Part C5: 20/20 resolved
runs reproduced first) -- are what could go beyond it. Note the tension in that last point: the 0.24
prompt bans writing a repro *file* while still running one `python -c`, which is cheap reproduction rather
than no reproduction. That is precisely the distinction EXP-009 Part C2 arrived at independently.

## results (summary)

| | |
|---|---|
| Public LB size | 3,467 teams; 58 public tasks confirmed exactly by the decoder |
| Our position (#4 = 0.10 = 6/58) | **~25th percentile; 67.3% of teams strictly ahead** |
| Median / modal / best team | 8 / 10 / 14 tasks (0.13 / 0.17 / 0.24) |
| Ceiling across all 3,467 teams | 14/58 = 24.1%; nobody higher |
| Gap to the ceiling | +8 tasks. Single-sample Fisher p = 0.0836 (n.s.), but against our pooled 17/174 **p = 0.0125** and 24.1% is outside our 95% CI of 6.2-15.1% -- **the gap to the top is real** |
| Gap to the median team | +2 tasks. 13.8% sits **inside** our pooled CI, p = 0.4629 -- **not established**; beating the middle of the field is not a measurable goal |
| Model used by the 0.24 config | `gemma-4-31b-it-qat-w4a16-ct` -- **the same one we already run** |
| Largest knob gaps | `max_time_minutes` 4.0 vs 7; `thinking_budget` 256 vs 4096 |
| Largest prompt gap | we **mandate** the heredoc repro file (27.3% of wall-clock); they **forbid** it |
| Local dev-48 -> LB transfer | ~0.4x (22.9% local vs 9.8% pooled LB); best team's LB ~= our local rate |
| Decision | adopt the public baseline's budget and prompt shape as a floor, in 3 sequenced steps; prompt surgery first because it is free and reduces timeout risk |

follow-ups:

  1. **Step 1 (prompt surgery) is the next experiment.** It subsumes the reframed EXP-011 of EXP-009
     Part C2. Pre-register on dev-48: compliance first (does it stop writing repro files?), then
     empty-patch rate (39.6% baseline) and median first-edit turn. Do **not** read the LB on it alone.
  2. **The `plan.md` 5.8 worst-case gate needs rewriting, not overriding ad hoc.** It should gate on
     *projected actual* time (observed median per task x 120 + setup) with a stated margin, not on the
     per-task cap x 120, which is the worst case only if every task runs to the cap. EXP-003's own data
     shows the median at an 8-min cap was 5.71 min, so the worst-case formula overstates by ~30%.
  3. The three downloaded notebooks are in this session's scratchpad only and are deliberately **not**
     committed to the repo. Re-pull with
     `kaggle kernels pull honghanhhh/gemma-4-baseline-lb-0-24` if needed; check the notebook's licence
     before reusing text verbatim rather than re-deriving the settings.
  4. Our `top_k: 64` is unset in both public configs. Untested either way, cheap to drop, lowest priority
     of the knob differences.
