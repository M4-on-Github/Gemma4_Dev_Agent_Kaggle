# EXP-018 — Config provenance audit: where our four budget/sampling numbers came from

**Date:** 2026-10-22. **GPU cost: zero.** Read-only analysis of `plan.md`, `experiments/` and runs we already have.
**Question answered:** why do our four headline budget/sampling numbers (`max_time_minutes: 4.0`,
`max_tool_calls: 45`, `max_output_tokens: 4096`, `thinking_budget: 256`) have the values they do?
**Status:** audit only. **No configuration value was changed.** Submission #5 ships unchanged.

---

## 0. Why this exists

These four numbers have been carried across five submissions without anyone re-checking their derivation. Each
later document (EXP-003, EXP-005, EXP-012, EXP-016, EXP-017) took them as given and argued about *other*
variables. This audit asks **where each number came from**, not whether a different value would score better.
The second question needs GPU quota we do not have today; the first one only needs reading.

---

## 1. All four numbers come from one pre-run paragraph

`plan.md` section 4.4 ("Budget math"), written before any GPU run, says verbatim:

> 12 h / 120 tasks = **6.0 min/task all-in**. Subtract setup (Q8, assume 1.0 min) → **5.0 min agent wall max
> average**. Add 15% safety → target **average ≤ 4.3 min**, hard cap 4.5 min.

> Decode 25.5 tok/s [M] → 4.5 min ≈ 270 s ≈ **6,900 output tokens per task total**, minus ~0.6 s × 45 calls ≈ 27 s
> overhead → ~6,200 tokens. With 45 calls that is **~140 output tokens per call including thinking**.
> Consequence: `thinking_budget` ≥ 512 at every step is unaffordable (45 × 512 = 23k tokens ≈ 15 min).

Three derivations fall straight out of those two bullets:

| Setting | Derivation in section 4.4 |
|---|---|
| `thinking_budget: 256` | ≈ 6,900 ÷ 45 calls (the "~140 per call including thinking" ceiling, rounded to a round number) |
| `max_tool_calls: 45` | ≈ 6,900 ÷ 140 tokens per call |
| `max_time_minutes` (4.5, later 4.0) | the 15% safety margin on the 6.0 min/task all-in budget |

**These are not four independent decisions.** They are one calculation, done once, before any measurement,
using a decode speed marked `[M]` (community-reported, not measured by us). `max_output_tokens: 4096` was added
beside them in the same pass as a context-wall guard (section 3c).

---

## 2. The flaw: a cap is not a spend

Section 4.4 treats a **cap** as if it were **spent on every call**. It multiplies `thinking_budget` by the number
of calls and compares the product to the task's total token allowance. That only holds if the model uses its full
allowance at every step. A cap the model rarely reaches costs nothing.

Our `thinking_budget: 256` is a hard ceiling that binds on every step. The rank-3 team's 4096 is a loose ceiling
that binds on almost none. These are different objects, and section 4.4 conflated them.

**Counter-evidence that keeps this from being a clear error.** EXP-003 did raise `thinking_budget` to 4096, and
EXP-009 found that run took **fewer** turns at nearly double the time, with s/turn rising to **7.79–12.13**. So the
budget does get spent when it is offered; "loose cap, rarely reached" is not what we observed at 4096. What is
untested is an **intermediate** value (512–1024). That is EXP-014 and it is still TODO.

**The internal inconsistency.** 45 calls × 256 thinking tokens = **11,520** tokens, against a whole-task output
budget of ~6,900 tokens at a 4.5-min cap (~6,120 at the current 4.0-min cap, i.e. 240 s × 25.5 tok/s). The caps
were sized against each other and could never both bind; time had to win. Measured: the time cap ends **79.2%**
(38/48) of E0's tasks. `plan.md` already conceded the premise failed ("time, not call count, was the binding
constraint", caveat added 2026-10-17), but the caveat left the derivation itself standing, so the other three numbers kept the values it produced.

---

## 3. Setting by setting

### 3a `max_time_minutes: 4.0`

**Provenance.** 4.5 came from section 4.4's safety margin. E0 ran 4.5 and scored (it survived on the hidden
set). Submission #2 (EXP-003, 8 min, 18.0 h formula worst case) returned **Notebook Timeout, zero score**.
`submission/eval_config.yaml`'s own EXP-005 comment then records trimming 4.5 → 4.0 to buy "1.0 h of formula
margin", pricing the cost at ~9% of resolves (only `fastapi_14301`, edits at 245–262 s, cut by a 240 s cap)
≈ **~0.4 of E0's public tasks**. So 4.0 is a post-timeout safety flinch, not a measurement.

**Current evidence.** EXP-016 section 3 re-derived the gate on projected *actual* time and reversed the premise
4.0 was protecting:

| cap | projected actual time |
|---|---|
| 4.0 min | ≈ 7.9 h |
| 4.5 min | **8.61 h measured** (E0, survived) |
| 5.0 min | 9.40 h |
| 6.0 min | 10.99 h |
| 7.0 min | **12.57 h** (past the 12 h hard limit) |

The calibrated operational ceiling is **~10.5 h** projected actual. Submission #2 projected 11.34 h on actual time
and still timed out, because fixed notebook overhead (wheels, vLLM start, model load) sits outside `task_wall_s`
and is unmeasured.

**Verdict: not justified.** 4.0 sits ~2.5 h below our own ceiling and pays resolves for margin we do not need.

### 3b `max_tool_calls: 45`

**Provenance.** Chosen so calls and time would expire together (6,900 ÷ 140). `plan.md:234` already concedes the
premise failed: time bound first.

**Current evidence.** On E0's dev-48, `tool_calls` min 13 / **median 32** / max 45, and **only 1 task of 48
reached the 45-call cap**. The knob is effectively dead: non-binding, and it costs nothing to keep. Lowering it
to the top teams' 28 **does** cost: EXP-003's `rich_3676` stopped at exactly 28 calls, and EXP-003's
call-capped cohort resolved **0 of 20**.

**Verdict: justified, by accident.** Right value, wrong reason.

### 3c `max_output_tokens: 4096`

**Provenance.** The comment in `configs/sampling.yaml` says it "keeps prompt + output well under the 32,768
context wall". That is the whole rationale. The premise is **already retracted in-repo**: `experiments/README.md`
section "NEW RISK — truncated tool calls from small `max_output_tokens`" records that, per HARNESS_README:365 and
684, when a thought block plus a large `edit_file`/`write_file` call hits `max_output_tokens`, the `<|tool_call|>`
tag is cut off mid-call and the harness issues a nudge. The harness explicitly recommends `thinking_budget: 4096`
**with** `max_output_tokens: 16384`, and "a *lower* `max_output_tokens` makes this truncation **more** likely, not
less — the opposite of plan §4.3/E11's premise". Harness valid range is 1–32768 with **default 16384**
(`thinking_budget` range 0–32768, **default 4096**).

**Current evidence.** The context wall 4096 was guarding does not reach us (EXP-016 section 2e): peak measured
`prompt_tokens` is **16,991 = 51.9%** of the 32,768 window, **zero** tasks exceed the 28,672 trip threshold, and
zero do so even simulated at `max_output_tokens: 8192`. Our **39.6%** empty-patch rate is behavioural, not
overflow.

**Verdict: not justified.** It rests on a premise the repo already retracted, guards a wall that does not reach
us, and sits below the harness default.

### 3d `thinking_budget: 256`

**Provenance.** ≈ 6,900 ÷ 45, from the section 4.4 derivation. See section 2 for why that derivation conflates a
cap with a spend.

**Current evidence.** The derivation is flawed, but EXP-003 showed that 4096 really is spent when offered (fewer
turns, nearly double the time, s/turn 7.79–12.13). A flawed derivation does not make the value wrong; it makes
it unsupported. The 512–1024 middle ground has never been measured.

**Verdict: partially justified.** EXP-014 is the experiment that would settle it.

---

## 4. The prompt

Measured section breakdown of `submission/prompts/swe_coder.md`, total **11,228 B / 109 lines**:

| section | bytes | share |
|---|---|---|
| `# Known sandbox gaps` (the `inline_snapshot`/`dirty_equals` vendoring block) | 3,508 | 31% |
| `# Protocol` (phases + call caps) | 2,500 | 22% |
| `# Hard rules` | 2,286 | 20% |
| `# Budget ledger` | 1,302 | 12% |
| `# Tool-call discipline` | 935 | 8% |
| preamble + `# Forced submission` | 697 | 6% |

The rank-3 team's (LB 0.24) prompt is **3,240 B**. Ours is **3.5×** theirs.

**Where the length came from.** It is accumulated scar tissue: each block was added after a specific observed
failure, per `plan.md` lines 190–194 — malformed tool args (positional/kwarg style parses to `{}`; ~31%
malformed in a replay), identical-call spin (up to 35% of calls in community data), compaction state notes
(~14,336-token text-only compaction that drops tool results), output overflow guards, and the three-consecutive-
nudge session kill.

**The qualifier that matters.** Most of those failure rates are marked `[M]` in this repo's notation —
community-reported or mirror data, **not measured by us**. One block is confirmed load-bearing by our own GPU
run: Q11 (closed 2026-10-16), where the scratch-file-vs-vendored-shim wording fix made `fastapi_14361` resolve
cleanly, re-validated on kernel `exp004_shim_fix_check`. The rest is untested insurance. Prefill is not free:
`plan.md:212` notes 45 calls × ~14k tokens = 630k prefill tokens per task, with prefix caching assumed but never
measured (Q10).

**Correction to EXP-017.** EXP-017 section 1 described the vendoring block as "~6 KB, 55% of the prompt".
Measured, it is **3,508 B and 31%**. The earlier figure was written from memory, not measured. This matters
because the figure sized a follow-up task: "move the vendoring block to an on-demand `skills/` entry" was
presented as the main lever on prompt size, when on the measured numbers it is under a third of the prompt.
EXP-017 section 1 has been corrected in place; its section 4 pre-registered readings are untouched.

---

## 5. Verdict

| setting | justified on current evidence? |
|---|---|
| `max_tool_calls: 45` | Yes, by accident. Non-binding (median 32, 1/48 at cap); lowering it to 28 costs resolves. |
| `thinking_budget: 256` | Partially. The derivation conflates a cap with a spend, but EXP-003 showed 4096 really is spent. The 512–1024 middle ground is untested (EXP-014). |
| `max_output_tokens: 4096` | **No.** Rests on a premise `experiments/README.md` already retracted; the 32k context wall it guards does not reach us; harness default is 16384. |
| `max_time_minutes: 4.0` | **No.** Post-timeout flinch, ~2.5 h below our measured ~10.5 h ceiling, self-priced at ~0.4 LB tasks. |
| prompt 11,228 B | Unknown, never tested. ~69% is insurance against `[M]` community-reported failure modes, not ones we measured. |

---

## 6. What this does and does not license

This is an audit. **No configuration value was changed**, and submission #5 (zip sha256
`edd94341586e60cf7cbd88d6ad59b93eee3cb16a0ea3efb3f650f98b7532d96a`, packer VALID 0 errors 0 warnings,
formula worst case 10.00 h against the 11.0 h gate) ships unchanged. The zip was **re-packed** after these
annotations landed, because `configs/sampling.yaml` and `eval_config.yaml` ship inside it and both gained
comments; that moves the recorded sha off the pre-annotation `b7b3610ca8c9...` build while leaving agent
behaviour byte-identical in every value. Re-packing keeps the recorded sha reproducible from the committed tree,
which is the only reason the hash is recorded at all. Only comments and prose were edited:
`submission/eval_config.yaml` and `submission/configs/sampling.yaml` carry provenance notes, `plan.md` section 4.4
carries a dated correction beside the original text, and EXP-017 section 1 carries the corrected prompt figure.

The two "No" verdicts, `max_time_minutes` and `max_output_tokens`, become **candidates for the next experiment**
once dev-48 quota exists. They are explicitly **not** being changed under time pressure, because both increase
timeout risk (a longer cap adds wall-clock directly; a larger output cap lets each step run longer) and
submission #2 is the cautionary case: a timeout scores zero, never partial credit.

For context on how much a single submission can tell us: our best LB score is **0.12 = 7/58**, rank 2322 of
3470, ~33rd percentile; the public LB covers 58 of ~120 hidden tasks; the MDE is **~4 LB tasks (~0.07)**, since
three scored submissions on the identical 58 tasks read 4, 7, 6 (mean 5.67, sd 1.53). With one submission per day
and a Dec 2 23:59 final deadline, the dev-48 run is what turns any of the above into evidence.
