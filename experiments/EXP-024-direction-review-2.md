# EXP-024 — Direction review 2: the experiment is wrong, and here is the defect it was hiding

Adversarial review requested on 2026-10-26, after submission #8 graded 0.12 = 7/58.
Scope: (1) is the experiment we are about to run correct, (2) what to run next, ranked, with GPU cost
and power, (3) what to submit for today's slot.

Every number labelled **[M]** is measured from the repo and is reproduced by
`python -I -X utf8 tools/exp024_stats.py <main-checkout-root>` (the two dev-48 runs live under
`runs/`, which is `.gitignored`, so the script takes the main checkout as an argument and must not be
pointed at a worktree). Numbers labelled **[Mod]** come from a seeded Monte Carlo over a stated model
inside that same script. Numbers labelled **[A]** are assumptions and are flagged as such.
No Kaggle submission and no kernel push was made in producing this document.

---

## 0. Bottom line

**(1) The experiment is the wrong question, and the version of it written into `submissions.md` row 8
("Next action is therefore item 1 of the EXP-024 programme: calibrate s/call against `thinking_budget`
on smoke-8") should not be run.** Three independent reasons, all from existing data:

- The knob's two endpoints are **already measured at dev-48 scale**: 7.73 s/call at
  `thinking_budget: 256` (E0, 1,603 calls) and 13.50 s/call at 4096 (EXP-003, 1,209 calls) **[M]**. The
  experiment buys an interpolation between two points we own.
- The **outcome** of sweeping that knob is also already measured, and it is null. E0 ran at ~33.4
  calls/task, EXP-003 at ~25.2. The two runs share all 48 task ids, so the contrast is **paired**:
  exact McNemar on resolved gives **p = 0.7266**, on empty patch **p = 0.5811** **[M]**.
- The one effect of `thinking_budget` that **is** significant in our entire dataset points the other
  way: lowering it from 4096 to 256 **tripled** the rate at which `edit_file` calls are destroyed in
  transport, 18.2% → 53.5%, Fisher **p = 1.2e-10** at the call level and **p = 0.0169** at the task
  level **[M]**. The proposed direction (256–1536) is the harmful direction.

**The finding that replaces it.** Across both dev-48 runs, **117 of 309 `edit_file` calls (37.9%,
Wilson 32.6–43.4%) never reached the file at all** **[M]**. The harness returned
`failed as the following mandatory input parameters are not present: old_string`. The mechanism is
positional: among those 117 calls, `new_string` — the **last** argument — survived in **116/117**, and
`old_string` — the **middle** argument — survived in **0/117** **[M]**. `write_file`, whose long
argument `content` is last, lost **0 of 14** (Fisher vs `edit_file` **p = 0.0028**) **[M]**. The agent
then retried the identical call up to 19 times, because the prompt's recovery rule (line 103) keys on
"not found or is not unique" and this error says something else.

**(2) Ranked programme** in §4. The top two items cost **zero GPU**; the first GPU purchase is a single
dev-48 arm (~3.9 L4×4-h) read on a **call-level** endpoint against a comparator that already exists, at
power 0.98 for a drop to 5% and MDE ≈ 7% **[Mod]**. The paper track (Nov 12, $10k, untouched) is ranked
high and is the only item whose deadline is not Dec 2.

**(3) Today's slot: submit `experiments/EXP-024/editfix_v9.zip`.**
sha256 `dbe9248ca7b8a0f74478e4dfdad0bbe65740cb4dc39b725e67540457658488a5`.
Validator `VALID (0 errors, 0 warnings)`; gate line
`worst case 120 x (4.5 + 1.0 setup) min = 11.00 h (gate 11.0 h, limit 12.0 h)`; no
`--skip-budget-gate`, no `--allow-warnings`. It is our own submission-#7 tree with two anchored prompt
edits and nothing else. **Upload it under the filename `submission.zip`** (EXP-023 §6: a different
filename returns a bare `400 Client Error`, which did not consume the slot but cost an attempt).
Honest expected effect **+1 to +2 tasks of 58**, below the single-draw MDE of ~4.5, so **one draw
cannot confirm it** — the pre-registered readings in §5 say so in advance, and the readout is the
dev-48 in §4 item 2, not this slot.

---

## 1. The defect: `edit_file` loses its middle argument

### 1.1 What was measured

| | `edit_file` lost | rate | Wilson 95% |
|---|---|---|---|
| E0 (`thinking_budget: 256`, 4.5 min, 45 calls) | 92 / 172 | **53.5%** | 46.0 – 60.8% |
| EXP-003 (`thinking_budget: 4096`, 8 min, 28 calls) | 25 / 137 | **18.2%** | 12.7 – 25.6% |
| pooled | 117 / 309 | **37.9%** | 32.6 – 43.4% |
| `write_file`, pooled | 0 / 14 | 0.0% | 0.0 – 21.5% |

All **[M]**. Fisher `edit_file` vs `write_file`: **p = 0.0028**. Fisher E0 vs EXP-003 at the call
level: **p = 1.222e-10**; at the task level (14/48 vs 4/48 tasks touched): **p = 0.0169**.

That task-level contrast is, as far as I can find, **the only statistically significant config contrast
anywhere in our data.** Everything else we have ever compared is null.

### 1.2 The mechanism is positional, not semantic

Among the 117 lost `edit_file` calls: `new_string` present **116/117**, `old_string` present
**0/117** **[M]**. In **64 of the 117** the anchor the model was trying to send survives as *spurious
argument keys*, i.e. the tool-call text was split on the commas inside the anchor and each fragment
became a key. Examples, verbatim from E0 traces:

```
["if isinstance(param_details.field, may_v1.ModelField)", "}"]
["use_security_scopes = security_scopes or []\n            if isinstance(param_details.depends, params.Security)"]
["def get(\n        self,\n        path", " ... ", "<|\"|>,allow_multiple"]
```

The last one leaks a raw gemma4 tool-call delimiter (`<|"|>`) into a key. So this is a **serialisation
failure in the middle argument of a three-argument call**, and `write_file` is immune because its long
argument is last. That is a mechanism, not a correlation, and it predicts the `write_file` result
before looking at it.

### 1.3 What it costs, and what the agent does about it

- In E0: 92 wasted calls = **5.7% of all 1,603 calls = ~712 s = 14.8 s/task** at the measured 7.73
  s/call, concentrated on **14 tasks** **[M]**. On those tasks it is roughly a fifth of the budget.
- The agent retried the identical call **8 to 19 times in a row** — violating both its own anti-spin
  rule (prompt line 19) and its own edit-recovery rule (line 103). Line 103 is keyed on
  "not found or is not unique"; the real error text is different, so the rule never fires **[M]**.
- Anchor length, successes vs the 64 reconstructable failures: median **156** chars (n=192, 13%
  single-line) vs **44** chars (n=64, 48% single-line); Mann-Whitney **z = 8.06, p = 7.9e-16**,
  P(success longer) = 0.84 **[M]**. **Caveat, stated plainly:** 53 of the 117 lost calls leaked no
  fragment at all, and the reconstruction is a lower bound on what was attempted, so this is
  *suggestive*, not clean. It is the weakest number in this document.
- The four tasks that actually recovered did so by **lengthening** (requests_6644: 9 failures at ~34
  chars, shortened to 11, 3 more failures, then 65 chars → OK; rich_3676: 7 failures at 33–44 → 189
  chars → OK, then four more long anchors all OK; fastapi_15589: 8 failures at 92 → 270 chars → OK) or
  by **switching to `write_file`** (fastapi_14463, 12 failures, then one 1,971-char `write_file`) **[M]**.
  3 of 4 by lengthening, 1 of 4 by `write_file`. That is exactly the two-rung ladder the candidate
  bundle encodes, and it is why the fix is not a guess.

### 1.4 Why nobody saw this for eight submissions

`tools/analyze_traces.py:137` detects an edit failure by looking for `"status": "error"` in the
observation. In E0 the loss error does **not** carry that envelope: the metric reported
`n_edit_fail = 9` for the whole run while **92** `edit_file` calls were being destroyed **[M]**. In
EXP-003 the envelope matched (27 reported, 25 of them losses). So the headline `edit_fail_rate`
(0.56% for E0, 2.2% for EXP-003) **both understated the dominant failure mode by an order of magnitude
and was not comparable between the two runs** — and `edit_fail_rate` is one of the numbers the
programme has been steering on. This is a one-regex fix and it is item 1 of §4.

---

## 2. Deliverable 1 — is the experiment we are about to run correct?

The experiment: smoke-8, measure median s/call as a function of `thinking_budget` ∈ {256, 1024, 1536},
pick the budget that fits 28 tool calls inside the 4.5-min cap. ~1.5 GPU-h claimed.

**Verdict: no. Do not run it.** Taking its reasoning chain in order:

**(a) "28 calls inside 4.5 min" is a target copied from a bundle that scored 7/58 for us.** The 28-call
operating point comes from the rank-3 v24 bundle, submitted as #8 and graded **7/58** — the mode of our
own seven draws. The pre-registered reading was R-C: no improvement **[M]**. Reverse-engineering a
budget shape from an artifact that did not beat us is not a hypothesis, it is cargo-culting. And note
our own best draw (8/58) was produced at ~33 calls, not 28.

**(b) The endpoint is already owned, twice, at 170× the sample size.** 7.73 s/call over 1,603 calls at
`thinking_budget: 256`; 13.50 s/call over 1,209 calls at 4096 **[M]**. (Over billable calls only,
excluding free `get_status`/`submit_patch`: 7.91 and 14.41.) At a 270 s cap those rates buy ~35 and ~20
calls respectively. "28 calls" needs ~9.6 s/call, which is *between two measured points*. A three-arm
smoke-8 would spend GPU to interpolate.

**(c) Even granting the interpolation, the quantity does not determine the outcome.** We have run both
endpoints of the call-budget axis on the *same 48 tasks*. Paired, exact McNemar **[M]**:

| endpoint | E0-only | EXP-003-only | p |
|---|--:|--:|---|
| resolved | 5 | 3 | **0.7266** |
| empty patch | 8 | 5 | **0.5811** |
| produced a patch | 5 | 8 | **0.5811** |
| never attempted an edit | 9 | 4 | 0.2668 |
| attempted, every attempt failed | 4 | 4 | 1.0000 |

Sweeping ~20 → ~35 effective calls/task moved nothing measurable. A smoke-8 at n=8 cannot see what a
paired dev-48 at n=48 could not.

**(d) The one thing the knob provably controls, it controls in the wrong direction.** Lowering
`thinking_budget` 4096 → 256 tripled the argument-loss rate (p = 1.2e-10) **[M]**. The proposed arms
are 256/1024/1536 — all **below** our shipping 4096. The most likely outcome of "succeeding" at this
experiment is buying ~8 extra calls per task and paying for them with destroyed edits. We would be
optimising the budget of a mechanism that is broken.

**(e) It targets neither half of the actual failure population** (see Q1 below). Of 35 empty patches,
21 never attempted an edit and 14 attempted and had every attempt destroyed. Neither group is short of
calls: in E0 all 19 empty-patch tasks hit the **time** cap while using 33.4 calls of 45 **[M]**.

**One thing the brief got right and one it got wrong about this experiment.** Right: it is cheap. Wrong
in two directions — (i) the worry that "n=8 may be too small" is misplaced *for an s/call endpoint*,
because smoke-8 is 8 × ~30 ≈ 240 calls and is perfectly adequate to estimate a mean duration; the
problem is the endpoint's irrelevance, not its precision; (ii) the cost is understated — three arms is
~2.4 L4×4-h at ~0.8 h/arm (the measured smoke-8 cost, submissions row 6), not ~1.5, unless the arms
share one server start.

---

## 3. The seven questions

### Q1 — "Empty-patch tasks use more turns than winners, so the fix is the forcing function" vs "we need post-edit calls". Which is it? Can both be true? Can it be settled without GPU?

**Settled on existing JSONL, zero GPU. Both framings are real and they describe *disjoint* populations
— and neither is short of calls.**

First, an exact equivalence: **empty patch ⟺ no edit ever landed.** Of 35 empty patches across both
runs, **0 landed a single successful edit** **[M]**. Of 61 producers, 20 resolved; of 35 empty patches,
**0 ever resolved**. So the whole problem is upstream of patch quality.

Splitting those 35 **[M]**:

| | never attempted an `edit_file`/`write_file` at all | attempted, every attempt failed |
|---|--:|--:|
| E0 | 13 | 6 |
| EXP-003 | 8 | 8 |
| **pooled** | **21** | **14** |

The 14 are the defect in §1. The 21 are a forcing-function failure — **but a forcing function already
exists and is being ignored.** All 21 had ≥ 12 calls (E0: 19–41 calls; EXP-003: 13–29), so the
prompt's `FIRST-EDIT DEADLINE` at call 12 (line 11) was in force and was passed. Their pooled tool
histograms contain **only** `run_command` and `read_file` — E0: 245 + 141 calls, zero `edit_file`,
zero `submit_patch`; EXP-003: 113 + 80, two `submit_patch` **[M]**. `phase_reached` was LOCATE for 14
of the 21 and REPRODUCE for 6. In E0 all 13 then hit the time cap at ~273 s.

**This is the adversarial point against my own fix as well as against the brief's:** a *verbal*
forcing function has already failed 21 times. Strengthening the wording is unlikely to be enough; the
remedy for that half is probably structural (see §4 item 3), and I am not proposing to ship one today
on no evidence.

**Neither population is resource-starved.** E0: 19/19 empty-patch tasks hit the time cap at mean wall
273.9 s on 33.4 calls, while resolvers finished at 213.2 s on 32.0 calls with only 4/11 capped **[M]**.
More calls would be spent the same way.

**Where the brief is wrong:** "empty-patch tasks use more turns than winners (38 vs 35)" is **refuted
for E0**, where empty patches used **fewer** turns (36.4 vs 38.2) **[M]**. It holds only in EXP-003
(31.7 vs 28.2). Quoting it as a single fact across both runs is a sign-flip.

**Reasoning-chain link (c) is refuted too.** EXP-003's resolvers resolved with a **median of 7**
post-edit calls (E0: 13) **[M]**. So "16 calls of verification" is not a requirement, and "call 12 of
~19 leaves only 7" is not what sank #8 — 7 is what a resolver actually used.

### Q2 — Is the see-saw real, or am I building a programme on noise?

**It is noise. Bluntly: yes, the programme has been built on noise, and the clearest symptom is that
the brief describes a paired experiment as if it were unpaired.**

The two dev-48 runs share **all 48 task ids** **[M]**, so every contrast must be paired. Paired exact
McNemar p-values are in §2(c): 0.7266 (resolved), 0.5811 (empty patch), 0.5811 (produced a patch). The
specific "see-saw" claim — empty-patch 39.6% → 33.3% *down* while resolve-among-producers 37.9% → 28.1%
*up* in badness — is two sides of one unpaired 2×2 with **Fisher p = 0.5856** on the producers arm and
p = 0.6718 on the empty rate. Per-task churn is large: **13 of 48 tasks flip empty-patch status** and 8
of 48 flip resolved status between the runs **[M]**. The "see-saw" is the arithmetic consequence of that
churn, not an effect.

**What would settle it:** nothing cheaper than a **repeat pair** — the same config run twice on dev-48
— which is the only way to measure the noise floor, and which is also the single most valuable artifact
for the paper (§4 item 4). Until that exists, **no task-level resolve comparison on 48 tasks can
resolve anything smaller than ~6–8 tasks** (power table in Q3). That is the honest state of play.

**Two further corrections to the brief's framing of this contrast.** (i) It presents E0 → EXP-003 as a
tightening of the call cap, but the two runs differ in **at least five** ways at once:
`thinking_budget` 256 → 4096, `max_time_minutes` 4.5 → 8, `max_tool_calls` 45 → 28,
`timeout_seconds`, and the prompt. (ii) EXP-003's prompt **already contained an edit-by-call-12 rule**
(the two runs' system prompts differ by only 8 lines, and both used our `swe_coder` prompt), so
EXP-003 was *already* a forcing-function test — which is why "the fix is the forcing function" cannot
be inferred from the E0 → EXP-003 difference.

### Q3 — Is s/call the right thing to measure? Design the run properly. Is smoke-8 big enough, or is this a dev-48 question?

Not the right thing (§2). The right primary endpoint is a **call-level** one, because each dev-48 arm
produces ~1,200–1,600 calls and ~140 `edit_file` calls against 48 task-level outcomes, which makes it
roughly an order of magnitude more sensitive per GPU-hour.

**Primary endpoint: the `edit_file` argument-loss rate.** Its comparator **already exists and need not
be re-run** — EXP-003's measured 25/137 = 18.2% on the very `thinking_budget` we ship. So a new arm is
tested against a fixed column of the 2×2, which is what makes even a small arm informative **[Mod,
3,000 reps, seeded]**:

| new arm | true post-fix rate | 0% | 2% | 5% | 9% | 12% |
|---|---|--:|--:|--:|--:|--:|
| dev-48 (~137 calls) | power | 1.000 | 1.000 | **0.982** | 0.519 | 0.146 |
| smoke-8 (~23 calls) | power | 1.000 | 0.632 | 0.298 | 0.115 | 0.060 |

**MDE at 80% power, dev-48: a post-fix rate of ~7%**, i.e. an 11-percentage-point absolute (≈ 61%
relative) reduction. A smoke-8 arm is a **mechanics go/no-go only**: it is conclusive if the rate goes
to zero and near-blind otherwise. So the run should be **dev-48, one arm**.

**Secondary endpoints, pre-specified, descriptive only** (reported with Wilson intervals, no
significance claimed): the three-way empty-patch classification of §Q1; number of tasks landing a
first edit; identical-retry runs; mean wall and `calls_cap_hit`.

**Explicitly NOT the endpoint: resolve count.** At the measured discordance of 8/48 **[Mod]**:

| true effect | +2 | +4 | +6 | +8 |
|---|--:|--:|--:|--:|
| power (paired exact McNemar) | 0.024 | 0.103 | 0.352 | ~1.0 |

(The +8 cell is degenerate at this discordance — it forces all 8 discordant pairs one way — so read the
MDE as **between +6 and +8 of 48**, confirming EXP-022's "~10" as the right order.) **Resolve-count
screening on dev-48 is useless** for anything we can plausibly build, and should stop being reported as
if it were a readout.

**One honest confound in the design.** EXP-003's 18.2% comparator was produced at an 8-min cap and a
28-call cap, not at our 4.5/64. If the loss rate depends on context length or call index rather than
only on `thinking_budget`, the comparison is biased. Mitigation: stratify the reported rate by call
index and by elapsed context, and state the stratified result alongside the pooled one. The
alternative comparator, E0, is worse: it differs on `thinking_budget`, the one factor we *know* moves
this endpoint (p = 1.2e-10).

### Q4 — Is there a better use of ~1.5–4 GPU-h right now?

Yes, and the two best uses cost **zero**. See §4. In short: fix the instrumentation (0 h), read the 21
never-attempted traces (0 h), then spend ~3.9 h on **one** dev-48 arm of the bundle submitted today,
read at the call level. Do not buy a three-arm smoke-8.

### Q5 — Check the selection arithmetic

**Both of your models are defensible and neither is identified by the data. The quantities you and
EXP-022 were comparing are different quantities, so there is no contradiction to resolve.**

Measured **[M]**: seven scored draws `4, 7, 6, 8, 8, 7, 7` — mean 6.714, variance 1.905, **sd 1.380**.
Under an independent binomial(58, 0.1158) the sd would be **2.437**. So our draws *are* less dispersed
than independence predicts, and the right reading of that is **heterogeneous fixed task difficulty**:
with per-task probabilities `p_i` fixed across draws,
`Var(K) = Σ p_i(1−p_i) = n·p̄(1−p̄) − n·Var(p)`, so writing `ρ = Var(p)/(p̄(1−p̄))` gives
`Var(K) = (1−ρ) × binomial`. Point estimate **ρ̂ = 1 − 1.905/5.942 = 0.679** — which is where the 0.68
in the brief comes from. (A shared-latent-factor model that re-randomises per draw moves the variance
the *wrong* way and is rejected; the script says so and implements the beta-binomial form.)

**The variance is not identified.** χ² 95% CI for the single-draw sd from n=7: **[0.889, 3.039]**,
implying **ρ ∈ [0.000, 0.867]** **[M]**. That spans the entire range. **θ therefore cannot be pinned**,
and any statement of the form "their true level is ~11.5" is a point estimate with essentially no
interval.

**Inverting E[max of 17 draws] = 14** (their best-of-17 board score) **[Mod]**:

| ρ | 0.00 | 0.50 | 0.679 |
|---|--:|--:|--:|
| implied θ | 8.8 | 10.3 | **11.1** |

So the brief's θ ≈ 11.5 (correlated) and θ ≈ 9 (independent) are both recovered; they are the two ends
of an unidentified range. **The honest gap is +2.1 to +4.4 tasks over our mean of 6.71, centred ≈ +3.5
— so EXP-022's "honest target θ ≈ 10, i.e. +3.3" survives**, and commit 2898957's claim that EXP-022
was "too generous to us in BOTH directions" is overstated: EXP-022's target sits inside the honest
range.

**The "contradiction" between 1.1 and 2.5 is not one.** EXP-022's ~1.1 is the *differential* winner's
curse, `E[max17] − E[max6] = 13.61 − 12.56 = 1.05` — selection they enjoy *over us*. The brief's ~2.5
is the *total* winner's curse, `E[max17] − θ`. Different estimands. Nothing to reconcile.

**The E[max of 44] claim is confirmed; the "cannot reach 0.24" claim is too strong** **[Mod]**, at
θ = 6.714:

| ρ | E[max 17] | E[max 44] | P(max of 38 ≥ 14) | P(max of 38 ≥ 11) |
|---|--:|--:|--:|--:|
| 0.00 | 11.32 | 12.55 | 0.195 | 0.933 |
| 0.50 | 9.77 | 10.49 | 0.077 | 0.467 |
| 0.679 | 9.20 | **9.78** | **0.060** | **0.353** |

"E[max of 44] ≈ 10 tasks = 0.17" is right at ρ ≈ 0.5–0.68. But **"we CANNOT reach 0.24 by drawing
repeatedly" is false as stated** — P(max of the 38 remaining slots ≥ 14) is 6–20% depending on ρ. It is
*unlikely*, not impossible, and the strategic conclusion is unchanged because a 0.24 reached that way
would be pure selection on 58 public tasks and **would not carry to the private half**. Conversely
P(max ≥ 11) is 35–93%: **board position is cheaply buyable and nearly meaningless**, which is the real
reason not to spend slots on repeat draws — and a strong reason not to pick the two final submissions
by public-LB rank.

**One caveat that cuts against my own numbers:** the seven draws are seven *different configs*, so
sd 1.380 bounds **pure draw noise from above** — it also contains real between-config differences.
ρ̂ = 0.679 is therefore an upper bound on the true inter-draw correlation, and every E[max] above is
correspondingly a lower bound. The repeat pair in §4 item 4 is the only thing that fixes this.

### Q6 — Is EXP-022 programme item #2 (native 8-min) dead? And what to submit?

**Dead, on three independent grounds** — one of which is empirical, not a projection:

1. **Its own criterion failed.** Item #2 required mean ≤ ~310 s to justify an override. EXP-003 measured
   mean **340.0 s**, median 342.5, p90 483.7 **[M]**.
2. **It has already been tried and it returned a zero.** EXP-003's own
   `projected_12h_total_h = 11.336` **[M]** — i.e. *inside* the 12.0 h limit — and that exact config
   was submission #2, which returned **Notebook Timeout, no score**. The mean-based projection was
   not merely tight, it was **wrong**.
3. **The gate forbids it.** `120 × (8 + 1) = 18.00 h` against `PACK_GATE_HOURS = 11.0`, so it needs
   `--skip-budget-gate`, which the brief rules out for a submission.

**New corollary, and it changes a programme item.** Because an 11.34 h *mean-based* projection actually
timed out, our dev-48 projections carry **≥ 6% optimism** (12.0/11.336 = 1.059) **[M]**. EXP-022 item
#3 proposes recalibrating the gate to allow `max_time_minutes ≤ 5.15` on measured inputs. That
recalibration is worth **≤ +0.4 tasks** by EXP-022's own estimate and would spend our only
demonstrated safety margin on it. **Recommendation: leave the cap at 4.5 min.** For reference, E0's own
aggregate records `worst_case_h = 9.001` and `setup_s_used = 0.03125 (measured)` **[M]**, so the gate
formula over-prices setup by ~1,900× and the *true* worst case at 4.5 min is ~9.0 h plus one vLLM
server start — comfortable, and that comfort is the asset.

What to submit is §5. Short version: **not** candidate (i) from the brief (v24 prompt + thinking
256–1024 + 28–34 calls). Its rationale is refuted in §2, and it would ship the 37.9% `edit_file`
defect unmitigated *and* triple it by lowering `thinking_budget`. Not (ii) a repeat draw for board
position either — Q5 shows board position is both cheap and uninformative. Not (iii) banking the slot:
the slot is use-it-or-lose-it, the artifact is already built and validated at zero marginal cost, and
its downside is bounded and pre-registered.

### Q7 — Are sub-agents / skills worth anything? Was "multi-agent is dead" sound on one secondhand datum?

**The datum is not sound evidence; the conclusion stands for better reasons.** A secondhand
12/18 → 6/18 is a single unpaired contrast on n=18 from a source we cannot audit; Fisher on 12/18 vs
6/18 is p ≈ 0.09, and we have no provenance for the configs. It should not be load-bearing, and
EXP-022 should not have rested on it.

The reasons that do hold, in order of force:

1. **`agent_tool` delegation spends the binding resource.** A sub-agent's calls come out of the same
   wall-clock budget, and **79.2% of E0 tasks were time-capped** **[M]**. We are not short of agents,
   we are short of seconds.
2. **It adds no capability.** Same model, same tool set, same 32k context, same sandbox. There is no
   asymmetry for a second agent to exploit.
3. **It does not touch the defect.** A sub-agent calling `edit_file` hits the same serialiser. Worse,
   delegation adds a layer of argument passing to a system whose demonstrated failure mode is losing
   arguments.

**For skills the decisive argument is placement, and it also tells us where the fix belongs.** A skill
is loaded conditionally; it may simply not be in context at the moment the error arrives. A
~1.4 kB always-present system-prompt section is **guaranteed** to be in context when `edit_file`
fails. Since the fix is a reaction to a specific error string, it has to be resident. That is why the
candidate puts it in the prompt and not in a skill — and this is a mechanism-level argument, not a
preference.

**Separately, a live hazard worth clearing.** `submission/skills/edit-anchoring/SKILL.md` exists, is
**not** declared in `agent.yaml`, and its line 21 says *"a short unique anchor beats a long verbatim
block that is more likely to contain a transcription slip."* Our data say the opposite (§1.3: success
median 156 chars vs 44, and 3 of the 4 recoveries were lengthenings). It also instructs
"re-read the file ... rather than retrying the same `old_string`", which does not address an error
where `old_string` never arrived. **If that skill were ever declared it would actively re-create the
doom loop.** It should be corrected or deleted so it cannot ship by accident. (I have not touched it;
it is outside today's candidate, which changes only the prompt.)

---

## 4. Deliverable 2 — ranked programme

Pricing: L4×4-hours. A dev-48 arm at 4.5 min / `thinking_budget: 4096` will be time-capped on most
tasks, so budget **48 × ~273 s ≈ 3.6 h plus ~0.25 h of vLLM start ≈ 3.9 h** **[A, from E0's measured
273.9 s capped mean]** — higher than EXP-022's 3.58 h because 4096 pushes tasks to the cap. A smoke-8
is ~0.8 h (measured, submissions row 6). Quota is 30 L4×4-h/week and is the scarce resource.

| # | Item | GPU-h | Slots | Primary endpoint and power | Decision it drives |
|--:|---|--:|--:|---|---|
| **1** | **Fix `tools/analyze_traces.py` to count argument-loss failures** (one regex on `mandatory input parameters are not present`), add an `n_arg_loss` column, re-derive both runs' `edit_fail_rate` | **0** | 0 | n/a (instrumentation) | Nothing below can be read automatically until this is done; §1.4 shows the current metric missed 92 of 92 losses in E0. ~30 minutes. |
| **2** | **EXP-025: one dev-48 arm of the exact bundle submitted today** | **~3.9** | 0 | `edit_file` argument-loss rate vs EXP-003's **fixed** 25/137; power **0.982** at a true 5%, **MDE ≈ 7%** (≥ 11 pp drop) at 80% **[Mod]**. Secondaries descriptive. **Not** powered on resolves (MDE +6 to +8/48). | Adopt the prompt permanently or revert it. **Bonus: this is the first dev-48 of our actual shipping config** (4.5 min, 64 calls, `thinking_budget: 4096`) — E0 had the cap but `thinking_budget: 256` and 45 calls; EXP-003 had 4096 but an 8-min cap and 28 calls. That alone justifies the quota. |
| **3** | **Trace forensics on the 21 never-attempted-an-edit tasks** | **0** | 0 | n/a (descriptive, n=21) | Whether the forcing function must become *structural*. Already begun here: all 21 passed call 12, histograms are **only** `run_command` + `read_file`, `phase_reached` LOCATE×14 / REPRODUCE×6, zero `submit_patch` in E0 **[M]**. Open question the traces can answer for free: did the model emit its bracket ledger at all, and what was it doing on call 12? |
| **4** | **Paper track** (Writeup ≤ 3,000 words, **due Nov 12**, separate $10k "Best New Resource", currently untouched) | 0 for writing; optionally reuses #2 | 0 | n/a | **Highest expected value per hour in this table and the only deadline that is not Dec 2** (17 days). §1 is a genuinely novel, reproducible, mechanism-level finding about the harness's tool-call transport plus a validated mitigation — precisely resource-shaped. The repeat pair Q2 asks for is also a paper deliverable, so it is costed once. |
| 5 | **Repeat pair** of one config on dev-48 (the noise floor) | ~7.8 | 0 | measures the dev-48 replicate sd directly; the only thing that fixes the ρ̂ upper-bound caveat in Q5 | Every future power statement, and the paper's methods section. Rank below #2 only because #2 is cheaper and decision-bearing today. |
| 6 | Gate recalibration review (5.15 min) | 0 | 0 | worth ≤ +0.4 tasks | **Recommend no change.** §Q6 corollary: projections carry ≥ 6% optimism and 4.5 min is our only demonstrated margin. |
| 7 | ~~Smoke-8 `thinking_budget` × s/call calibration~~ | ~2.4 | 0 | — | **Rejected, §2.** Re-measures an owned quantity, on an irrelevant endpoint, in the direction that triples the defect. |
| 8 | ~~Sub-agents / skills~~ | — | — | — | **No-go, §Q7.** Spends the binding resource, adds no capability, does not touch the defect. |
| 9 | ~~LoRA~~ | 0 (TPU) | 0 | unreadable below +4 | No-go, unchanged from EXP-022. |

**Slot ledger, unchanged in shape:** ~38 slots including today, of which 8 should stay reserved for the
finals pair (Nov 22 – Dec 1). Q5's P(max ≥ 11) = 0.35–0.93 is the reason **not** to choose the finals by
public-LB rank: that would be selecting on noise with a 58-task public half.

**Housekeeping found while verifying:** `submissions.md` row 8's **public LB column still reads
`**pending**`** although the notes column in the same row records `GRADED 0.12 = 7/58` and commit
2898957 was made to record it. One-line fix; not done here because it is outside this document's scope
and would collide with whoever is editing that ledger.

---

## 5. Deliverable 3 — today's slot

### 5.1 The artifact

| | |
|---|---|
| zip | `experiments/EXP-024/editfix_v9.zip` (9.9 KiB, 4 members, `agent.yaml` at root) |
| **sha256** | **`dbe9248ca7b8a0f74478e4dfdad0bbe65740cb4dc39b725e67540457658488a5`** |
| source tree | `experiments/EXP-024/candidate-editfix/` (4 files, 21.6 KiB unpacked) |
| builder | `tools/exp024_make_editfix.py` — aborts unless **each anchor matches exactly once** |
| validator | `python -I -X utf8 tools/validate_submission.py experiments/EXP-024/candidate-editfix --official --strict` → **`RESULT: VALID (0 errors, 0 warnings)`**, `instruction chars: 12832` |
| **gate line** | **`eval_config.yaml: worst case 120 x (4.5 + 1.0 setup) min = 11.00 h (gate 11.0 h, limit 12.0 h)`** |
| flags | **no `--skip-budget-gate`, no `--allow-warnings`** |
| determinism | repacked twice, identical sha256; the duplicate was deleted |
| **upload filename** | **`submission.zip`** — EXP-023 §6: another name returns a bare `400 Client Error` (it did not consume the slot, but it cost an attempt) |

**Two reproduction hazards, recorded because they can silently change the sha.** (i) `*.zip` is
gitignored repo-wide (`.gitignore:23`), so `editfix_v9.zip` is **not** in the commit — only the source
tree, the builder and the sha above are, and the builder reproduces the zip bit-for-bit (verified: two
independent packs, identical sha256). (ii) `experiments/EXP-024/candidate-editfix/` is committed as LF
but **checks out as CRLF under `core.autocrlf`** (git warns on `add`). Packing that checked-out tree
directly would change the sha256 — this is exactly EXP-022 R9. **Always rebuild with
`tools/exp024_make_editfix.py` before packing**, since it reads the LF blobs from `HEAD` and asserts
they are CRLF-free.

**Provenance discipline.** Every file is taken byte-for-byte from `git show HEAD:submission/<path>`, so
`agent.yaml` (1,330 B), `configs/sampling.yaml` (3,374 B) and `eval_config.yaml` (4,551 B) are
**unchanged** from submission #7's tree. `submission/` itself was never touched (`git status
submission/` is clean). The builder also asserts each HEAD blob is CRLF-free, which is how EXP-022's R9
packing hazard (autocrlf worktree bytes changing the sha) is handled — an earlier attempt to solve it
with a `.gitattributes` file was **rejected by `--official --strict` as a hidden file**, so the blobs
are copied directly instead.

### 5.2 What changed, and why exactly this

Two anchored edits to `prompts/swe_coder.md` only (**11,228 → 12,834 bytes, +1,606**; the validator's `instruction chars: 12832` counts characters, and the file holds one 3-byte non-ASCII character, so chars = bytes − 2):

- **E1 — reverse the advice that causes the doom loop.** Line 103 told the agent to use "2 to 4 unique
  lines, short and distinct" and, on failure, "retry with a **shorter**, more distinctive anchor". It
  now says to copy **3 or more consecutive whole lines, roughly 150–300 characters** verbatim from the
  most recent `read_file`, and on failure to **re-anchor on MORE surrounding lines, never fewer**. This
  matches the measurement (success median 156 chars vs 44) and the four observed recoveries.
- **E2 — a new always-resident section keyed on the exact error text**, inserted before
  `# Budget ledger`: it states that the call never reached the file, forbids re-sending identical
  arguments, and gives a three-rung ladder — (1) re-send once with a much longer `old_string`;
  (2) if the file is under ~150 lines, `read_file` it whole and rewrite with **one `write_file`**,
  explicitly because `content` is that tool's **last** argument and therefore does not get lost
  (0/14 losses, §1.1); (3) for larger files, one `run_command` that reads, replaces a short unique
  single-line fragment, and writes back.

Each of E1/E2's anchors is asserted to match exactly once or the build aborts, so the diff cannot
drift silently.

### 5.3 Risks, stated before the result

- **Timeout risk: none introduced.** `eval_config.yaml` is byte-identical to #7 at
  `max_time_minutes: 4.5`, and the gate line above is the unmodified 11.00 h. The prompt grew by
  ~400 tokens of a 32k context, which does not enter the gate.
- **The real downside is ladder rung 3.** A `run_command` one-liner that rewrites a file is the only
  instruction in the bundle that can *corrupt* source. It is gated behind two prior failures so it
  should be rare, and the existing prompt already forbids touching test paths and runs
  `git checkout -- <path>` before the final submit — but this is the component I would revert first
  (see reading R-D).
- **The 21 never-attempted tasks are untouched by this bundle.** By §Q1 that is roughly 60% of the
  empty-patch population, so a large effect is not expected and is not being claimed.
- **No PUBLIC_REPO_WORDS / offline-pattern hits** — the validator reports 0 warnings, so the new text
  is repo-agnostic and mentions no network or install.

### 5.4 Pre-registered readings — fixed now, not to be revised after the score

Baseline: our own tree scored **7/58** as submission #7 (sha `99b750a0…`); our best draw is 8/58 and our
seven-draw mean is 6.714.

**Honest expected effect, computed in advance.** The fix addresses the 14 all-attempts-failed tasks
(EXP-003 alone: 8/48 = 16.7% of task-runs). If it converts half of them into producers at the measured
resolve-among-producers rate of 0.281–0.379, that is `0.167 × 0.5 × ~0.33 ≈ 2.3%` of tasks ≈ **+1.3
tasks of 58** **[Mod]**; call it **+1 to +2**. The single-draw MDE is ~**+4.5**. **One draw therefore
cannot confirm this fix, and I am not proposing it as an experiment.**

Pre-registered probabilities, normal approximation to the correlated binomial at ρ̂ = 0.679 (single-draw
sd 1.41 at θ=7, 1.53 at θ=8.5), with continuity correction **[Mod — crude at these counts, stated
anyway so it cannot be adjusted later]**:

| | if the fix is worth 0 | if worth +1.5 | LR |
|---|--:|--:|--:|
| P(k ≥ 11) | 0.006 | 0.095 | ≈ 15 : 1 |
| P(k ≥ 9) | 0.143 | 0.500 | ≈ 3.5 : 1 |

- **R-A, k ≥ 11 (≥ 0.18):** adopt the prompt permanently **and re-draw it unchanged** on the next slot,
  because regression to the mean is the main threat to R-A. Still run §4 item 2.
- **R-B, k = 9–10 (0.15–0.17):** inside our own 4-to-8 replicate spread. **Will not be called a win.**
  Keep the prompt (it is mechanism-justified and free) and let §4 item 2 decide.
- **R-C, k = 6–8:** the expected outcome under the honest prior. Neither confirms nor refutes; it does
  **not** retire the fix, because the slot was never powered to test it. Proceed to §4 items 1–2.
- **R-D, k ≤ 5:** materially worse than our mean. First suspect is **ladder rung 3** (the only
  instruction that can corrupt a file); revert rung 3, keep E1 and rungs 1–2, and look for corrupted
  source in §4 item 2's patches.
- **R-E, blank / Notebook Timeout:** the 11.00 h gate model is falsified **even at 4.5 min**, which
  would be bigger news than anything about the prompt. Nothing else is trustworthy until it is
  understood; next slot reverts to #7's exact bytes.

### 5.5 Why not the alternatives

- **(i) v24 prompt + `thinking_budget` 256–1024 + 28–34 calls.** Rejected. Its rationale is refuted in
  §2; it ships the 37.9% defect unmitigated; and lowering `thinking_budget` is the one intervention we
  have *significant* evidence for, in the harmful direction (18.2% → 53.5%, p = 1.2e-10).
- **(ii) A repeat draw of our best config for board position.** Rejected. Q5: P(max of 38 ≥ 11) is
  0.35–0.93, so board position is cheap, and it is also uninformative — a public-LB-selected peak would
  not carry to the private half. Buying it would also waste the only slot where a mechanism change can
  be observed at all.
- **(iii) Bank the slot and buy information with GPU.** Half-right, and the GPU half is adopted
  (§4). But slots are use-it-or-lose-it, the artifact is built and validated at zero marginal cost, and
  its worst case is bounded by a pre-registered R-E. Banking strictly dominates nothing.

---

## 6. Where the brief was wrong

Recorded plainly, as requested.

1. **"The two dev-48 runs are an unpaired comparison."** They share all 48 task ids. Every contrast is
   paired, and the paired tests are null (McNemar p = 0.73 resolved, 0.58 empty). Treating them as
   unpaired is what made the see-saw look like a finding.
2. **"Empty-patch tasks use more turns than winners (38 vs 35)."** Refuted for E0: 36.4 vs **38.2** —
   empty patches used **fewer** turns. The ordering holds only in EXP-003.
3. **"EXP-003 was the call-tightening arm"** — it differs from E0 in at least five ways at once
   (`thinking_budget` 256→4096, cap 4.5→8 min, calls 45→28, `timeout_seconds`, prompt), and it
   **already contained an edit-by-call-12 rule**, so it was already a forcing-function test.
4. **"We cannot reach 0.24 by drawing repeatedly."** Too strong: P(max of 38 ≥ 14) is 0.06–0.20. The
   right objection is that such a 0.24 would be selection on the public half and would not transfer.
5. **"Reaching only ~7 post-edit calls is what sank #8."** EXP-003's resolvers used a **median of 7**
   post-edit calls. Seven is what success looks like, not what failure looks like.
6. **"smoke-8 may be too small (n=8)."** Misplaced for an s/call endpoint — smoke-8 is ~240 calls and
   is plenty. The problem is the endpoint, not the sample size. (And the cost is ~2.4 h for three arms,
   not ~1.5.)
7. **"~1.1 selection (EXP-022) vs ~2.5 (commit 2898957) is a contradiction."** They are different
   estimands — differential vs total winner's curse. Also, commit 2898957's claim that EXP-022 was
   "too generous in BOTH directions" is overstated: EXP-022's θ ≈ 10 target sits inside the honest
   unidentified range of 8.8–11.1.
8. **Not wrong, but omitted and load-bearing:** `tools/analyze_traces.py` under-reported edit failures
   by ~10× in E0 (9 reported, 92 real) and inconsistently between runs. The programme has been steering
   partly on that number.

**And where I may be wrong.** The weakest link in §1 is the anchor-length comparison: 53 of 117 lost
calls leaked no fragment, so the "44 chars" median is censored and the reconstruction is a lower bound
(§1.3). The positional mechanism (116/117 vs 0/117, and `write_file` 0/14) does **not** depend on that
number, and neither does the E0-vs-EXP-003 contrast; but the *specific* prescription "make anchors
150–300 chars" rests partly on the censored comparison, and §4 item 2 is the test of it.

---

## 7. Reproduction

```
# all [M] numbers, and the [Mod] Monte Carlo (seeded, stdlib only)
python -I -X utf8 tools/exp024_stats.py C:/Users/moemy/Documents/Kaggle/Gemma4_Dev_Agent_Kaggle

# rebuild the candidate (aborts unless each anchor matches exactly once)
python -I -X utf8 tools/exp024_make_editfix.py experiments/EXP-024/candidate-editfix
python -I -X utf8 tools/validate_submission.py experiments/EXP-024/candidate-editfix --official --strict
python -I -X utf8 tools/pack_submission.py --src experiments/EXP-024/candidate-editfix \
    --out experiments/EXP-024/editfix_v9.zip
sha256sum experiments/EXP-024/editfix_v9.zip
# -> dbe9248ca7b8a0f74478e4dfdad0bbe65740cb4dc39b725e67540457658488a5
```

`tools/exp024_stats.py` prints `[MEASURED]` and `[MODELLED]` section headers so the two can never be
confused in a later reading, and carries the censoring and identification caveats inline rather than
only here.

### Measured / assumed ledger

| quantity | status |
|---|---|
| all per-run counts, rates, Wilson/Fisher/McNemar/Mann-Whitney p-values, the 117/309 defect, the 21+14 split, the 7 LB draws | **[M]** — `tools/exp024_stats.py` |
| `projected_12h_total_h` 11.336 (EXP-003) and 8.611 (E0); `worst_case_h` 9.001; `setup_s_used` 0.03125 "measured" | **[M]** — `aggregates.json` |
| validator result, gate line, sha256, instruction chars | **[M]** — tool output, quoted verbatim in §5.1 |
| ρ̂ = 0.679, E[max N], θ inversions, all power tables, the R-A/R-B probabilities | **[Mod]** — seeded Monte Carlo / normal approximation over the stated model |
| ~3.9 L4×4-h for a dev-48 arm at 4.5 min / 4096 | **[A]** — extrapolated from E0's measured capped mean of 273.9 s plus ~0.25 h server start |
| "+1 to +2 tasks" expected effect of the fix | **[Mod]** — 16.7% × 0.5 conversion × 0.281–0.379 resolve rate; the 0.5 conversion is **[A]** |
| 30 L4×4-h/week quota | **[A]** — EXP-020 line 11; not visible from inside the repo |

---

## Submitted

**Kaggle submission ref 57680438, accepted 2026-10-26** ("0 submissions remaining today").
Artifact `out/submission.zip`, sha256 `dbe9248ca7b8a0f74478e4dfdad0bbe65740cb4dc39b725e67540457658488a5`,
uploaded as `submission.zip` per the filename rule recorded in `EXP-023 §6` — accepted on the first try.

The candidate was **repacked independently from `experiments/EXP-024/candidate-editfix/`** rather than
submitted as handed over: `RESULT: VALID (0 errors, 0 warnings)`, gate line
`worst case 120 x (4.5 + 1.0 setup) min = 11.00 h (gate 11.0 h, limit 12.0 h)`, no `--skip-budget-gate`,
and the sha256 reproduced exactly, so the pack is deterministic. The three config files were confirmed
**byte-identical to `submission/`** by diff; only `prompts/swe_coder.md` differs.

**The central finding was verified against the raw traces before anything was submitted**, not accepted on
the strength of the review that proposed it: 92 argument-loss calls on 14/48 tasks in E0 and 25 on 4/48 in
EXP-003, counted directly out of `runs/*/traces/*.json`. The detector fix at `a6af225` reproduces both
numbers through `tools/analyze_traces.py` itself.

§4's pre-registered readings govern how the score is read. The expected effect is **+1 to +2 of 58, below
the single-draw MDE**, so this slot cannot confirm the fix; the dev-48 arm powered on **loss rate** is the
real test and still needs a GPU-quota decision.
