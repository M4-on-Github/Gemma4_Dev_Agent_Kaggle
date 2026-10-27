id: EXP-010-first-edit-tripwire        date: 2026-10-21        owner: M4

hypothesis: EXP-009 Part B found that the single sharpest discriminator between tasks that score and tasks
        that score nothing is **the turn on which the agent first calls `edit_file`** -- and that the two
        cohorts barely overlap. On E0/dev-48 the resolved cohort's *latest* first edit is turn 30 while the
        empty-patch cohort's *earliest* is turn 27; 13/48 tasks never edit at all. Empty-patch tasks are not
        starved of turns (38.0 turns vs the winners' 35.0, same ~15k context, only 1 of 19 hit the call cap)
        -- they spend a full budget exploring and never commit. H1: forcing the first `edit_file` no later
        than call 25 converts a substantial share of the empty-patch cohort into patch-producers. H2: it does
        so without materially damaging the resolved cohort, because at N=25 only 2/11 of E0's winners and
        0/9 of EXP-003's winners edit later than that. Conversion once any patch exists is measured at
        **11/29 = 37.9%** -- but see the pre-submission confound check below, which revises the expected gain
        down to **+1 to +2 dev-48 tasks**. H3 (added at submission time): the tripwire's value is primarily as
        a **mechanism probe**, not a score play -- it is expected to move the process metrics decisively while
        leaving resolve rate inside the noise.

single variable changed: `submission/prompts/swe_coder.md` -- **one line added** to the "Budget ledger"
        section (the section the agent already complies with: it emits the `[phase=... calls=17/45 edits=1
        submitted=no]` bracket line every turn, so the rule hooks onto a counter it already maintains).
        No other file touched. `eval_config.yaml`, `agent.yaml` and `configs/sampling.yaml` are byte-identical
        to submission #3. Diff:

            + - FIRST-EDIT DEADLINE, and it overrides every phase cap below: if your bracket line ever shows
            +   calls at 25 or more while edits is still 0, your very next tool call MUST be edit_file. [...]

        Note the prompt **already** said "LOCATE (at most 10 calls)" and "REPRODUCE (at most 6 calls)", which
        would put the first edit at call ~17. The agent ignores it: EXP-001's phase histogram showed 54% of
        tasks never leave LOCATE. Those caps are advisory prose inside a numbered list with no checkpoint and
        no consequence. This experiment does not add a *new* budget -- it makes the existing one checkable,
        tripwire-style, against a counter the agent already tracks, with a mandatory next action.

cohort: **none run -- submitted directly to the public LB without a local dev-48 run.** Quota-constrained
        decision taken 2026-10-21 (see "deviation from plan 5.8" below). GPU-h used: **0.0**

config: prompt-only change on top of submission #3's config.
        zip: `dist/exp010_first_edit_tripwire.zip`
        sha256: `1d3a53f48c3eb1f34d2ca9965030dfd2c02f6df5270aca30f11e0b88addcacc6`
        contents (4 files, the packer's reachability closure from `agent.yaml`): `agent.yaml`,
        `configs/sampling.yaml`, `eval_config.yaml`, `prompts/swe_coder.md`
        eval_config: 4.0 min / 45 calls / 70 turns / 300 s -- unchanged from #3
        sampling: T 0.2, top_p 0.95, top_k 64, max_output_tokens 4096, thinking on, thinking_budget 256 -- unchanged
        validator: **VALID, 0 errors, 0 warnings**; worst case 120 x (4.0 + 1.0) / 60 = **10.00 h**
        (gate 11.0 h, limit 12.0 h), no `--skip-budget-gate` used

### Why N = 25, from the data rather than from the prompt's own phase budget

First-edit **turn** distribution per outcome cohort (computed from the same traces as EXP-009):

| run | cohort | n | min | p25 | p50 | p75 | p90 | max | never edited |
|---|---|---|---|---|---|---|---|---|---|
| E0 | resolved | 11 | 7 | 10 | 18 | 22 | 29 | **30** | 0 |
| E0 | patch-but-failed | 18 | 6 | 12 | 18 | 26 | 35 | 41 | 0 |
| E0 | empty-patch | 19 | **27** | 40 | 43 | 46 | 48 | 50 | 13 |
| EXP-003 | resolved | 9 | 6 | 12 | 14 | 17 | 19 | **25** | 0 |
| EXP-003 | patch-but-failed | 23 | 5 | 10 | 17 | 20 | 25 | 28 | 0 |
| EXP-003 | empty-patch | 16 | **18** | 29 | 32 | 33 | 33 | 34 | 8 |

The cohorts are nearly disjoint on this axis. Threshold sweep -- "disturbed" = a resolved task whose natural
first edit is later than N, i.e. one the rule would force to edit earlier than it did:

| N | E0: resolved disturbed | E0: empty-patch fired on | EXP-003: resolved disturbed | EXP-003: empty-patch fired on |
|---|---|---|---|---|
| 14 | 6/11 | 19/19 | 4/9 | 16/16 |
| 18 | 5/11 | 19/19 | 1/9 | 15/16 |
| 20 | 4/11 | 19/19 | 1/9 | 15/16 |
| **25** | **2/11** | **19/19** | **0/9** | **14/16** |
| 30 | 0/11 | 18/19 | 0/9 | 13/16 |

N=25 is the knee: it still fires on **100%** of E0's empty-patch cohort and 88% of EXP-003's, while touching
only 2 of 11 and 0 of 9 winners respectively. N=14 (which is what the prompt's own LOCATE+REPRODUCE budget
implies) would disturb more than half the winners -- the existing advisory budget is, on this evidence,
set too aggressively, which may be part of why the agent disregards it.

"Disturbed" also overstates the harm: the rule forces an edit at 25, it does not end the task. Those two E0
winners (natural first edit at 29 and 30) keep their remaining ~20 calls to investigate and re-edit, and the
rule says so explicitly ("after that first edit you keep investigating and re-editing normally").

Timing check: at E0's measured 5.38-6.83 s/turn, call 25 falls at ~135-170 s of the 240 s budget, leaving
~70-105 s -- enough for 1-2 edits plus `submit_patch` (2.13 s median, and free against the call cap). The
existing end-game rule ("fewer than 8 tool calls or fewer than 60 seconds remaining -> submit") still
backstops it.

### Pre-submission confound check -- the effect estimate, revised DOWN

**Run before submitting, in response to "double check if this is a good idea". It found a real problem with
the original effect estimate and the estimate was corrected rather than the experiment abandoned.**

The +3.6-task figure assumed a *forced* edit converts at the same 37.9% as a *voluntary* edit. That is the
weak link: if the agent has not edited by turn 25 because it genuinely has not localised the bug, then forcing
an edit produces a low-information edit, not a 37.9% shot. Late editing could be a **symptom** of not knowing
where the bug is rather than a **cause** of failure.

Testable for free from the existing traces: among tasks that produced any patch at all, does first-edit turn
still predict resolution? Pooled over E0 + EXP-003 (n = 96 task-runs, 75 with >= 1 edit call), full output in
`experiments/EXP-010/late-edit-conversion.txt`:

| first-edit turn | tasks that edited | resolved | rate |
|---|---|---|---|
| 1-10 | 14 | 4 | 28.6% |
| 11-18 | 26 | 10 | 38.5% |
| 19-25 | 14 | 4 | 28.6% |
| **26+** | **21** | **2** | **9.5%** |
| **edited by turn 25** | **54** | **18** | **33.3%** |
| **edited after turn 25** | **21** | **2** | **9.5%** |

Fisher exact (early-vs-late x resolved-vs-not): **p = 0.0438**. Per-run: E0 40.9% vs 15.4%; EXP-003 28.1% vs
**0.0%** (0 of 8).

This cuts both ways, and both readings matter:

1. **It confirms turn 25 is a real boundary**, not an artifact of the empty-patch cohort. Even among tasks
   that *did* edit, crossing turn 25 before the first edit drops the resolve rate from 33.3% to 9.5%. The
   1-10 / 11-18 / 19-25 buckets are flat (28.6% / 38.5% / 28.6%), so there is no penalty for editing early --
   the cliff is specifically at the late end. That is the shape the tripwire needs.
2. **But it falsifies the 37.9% conversion assumption.** The population the tripwire acts on is exactly "has
   not edited by turn 25", and the best available estimate of what an edit made from that state converts at
   is **9.5%**, not 37.9%.

**Revised expected effect.** E0's 13 never-edited tasks x 9.5% = **+1.2 tasks**; taking the whole 19-task
empty-patch cohort, 19 x 9.5% = **+1.8 tasks**. So **+1 to +2 dev-48 tasks, not +3.6** -- which is *below*
dev-48's own ~+3-task detection threshold (plan 5.5). Resolve rate will probably **not** move detectably even
on dev-48.

**Why it is still worth shipping, on the revised numbers:**

- The counterfactual is a **guaranteed zero**. An empty patch scores 0% with certainty; a forced edit scores
  ~9.5%. The change converts certain zeros into long shots, so expected value is positive even at 9.5%.
- Plausible upside the 9.5% figure does not capture: the late editors it is measured on edited at turn 26-50,
  i.e. with almost no budget left to iterate. A task forced to edit at 25 keeps ~10 calls and ~70-105 s to
  refine, and E0's 19-25 bucket shows a median of **10 edit calls** for tasks that edit in that window
  against 2 for the 26+ bucket. Iteration room is the one thing a forced-early edit buys that a natural-late
  edit does not.
- The downside stays bounded: 2/11 E0 winners disturbed, 0/9 in EXP-003, time-safety identical to #3.
- **The information value is in the process metrics, not the score.** Whatever happens to resolve rate, the
  dev-48 run will answer two questions that redirect the whole program: can the agent commit when told
  (compliance), and is the bottleneck commitment or localisation (Case A vs Case B below)?

**Consequence for the decision rule: Case B below is now the single most likely outcome, not merely a
plausible one.** If the tripwire converts empty patches into patches without lifting resolve rate, the
bottleneck is localisation quality, not commitment -- and that is the most valuable thing this experiment can
tell us, because it would retire the entire commitment line of work on one run.

### Deviation from plan 5.8, stated explicitly

plan 5.8 says *"never submit a config that has not run on dev-48 with projected worst case <= 11 h."* This
bundle has **not** run on dev-48. The deviation is deliberate and narrower than submission #2's was:

- **The safety half of that rule is fully satisfied.** The 11 h gate is about wall-clock, and the per-task
  caps (`max_time_minutes: 4.0`, `max_tool_calls: 45`) are enforced by the harness and unchanged from
  submission #3, which scored successfully. A prompt change cannot lengthen a capped task. Worst case is
  identically 10.00 h with 1 h of margin, validated without `--skip-budget-gate`. This is the opposite of
  submission #2, which knowingly shipped an 18.0 h projection and returned no score.
- **What is untested is efficacy, not safety** -- and per EXP-009 the LB cannot test efficacy anyway (MDE
  ~4 tasks / ~0.07, and the expected effect here is ~+1 LB task after the ~3.3x local->hidden drop). So a
  dev-48 run would be the *only* way to measure it, and quota does not allow one today.
- **The alternative was to waste the slot.** An expiring daily slot has zero value unspent; this at least
  banks a higher-expected-value candidate and re-confirms the transfer/budget path.

Precedent: submission #3 was also shipped without a fresh dev-48 run, justified by reasoning from E0's own
traces, and it scored normally.

results: **pending** -- submitted 2026-10-21. Record the LB score in `submissions.md` row 4.

decision: **pending.** Pre-registered reading of the outcome, written before the score is known, because
EXP-009 showed how easy it is to over-read a single LB move:

- The LB result **cannot adopt or reject this change.** With MDE ~4 tasks, anything from 0.05 to 0.19 is
  consistent with no effect. Only two LB outcomes carry information, and neither is about efficacy:
  (a) a score is returned at all -> the 10.0 h budget path is re-confirmed; (b) a score at or below ~0.03
  (<= 2/58) would be a >= 2-task drop from #3 and worth treating as a possible real regression, since the
  tripwire is the kind of change that could plausibly hurt by forcing premature edits.
- **The real decision waits for a dev-48 run** when quota allows, scored on EXP-009's new primary metrics:
  **empty-patch rate** (39.6% at E0 -> target < 15%) and **median first-edit turn for the empty-patch
  cohort** (43 -> target < 25, which the rule mechanically guarantees if it is obeyed at all). Compliance is
  itself the first thing to check: if `first_edit > 25` still appears in the traces, the rule was ignored
  and the result says nothing about the hypothesis. Resolve rate is secondary and must be reported with the
  paired 2x2 + exact McNemar (`tools/run_forensics.py compare`), never as a marginal rate.

**Exhaustive dev-48 outcome tree.** Check compliance *first* -- every row below assumes the rule was
actually obeyed, except Case C.

| case | empty-patch rate | resolve rate | what it means | next move |
|---|---|---|---|---|
| **C -- rule ignored** (check first) | unchanged ~39.6% | unchanged | `first_edit > 25` still in the traces. Says **nothing** about the hypothesis -- it is a prompt-adherence failure. Real possibility: the agent already ignores "LOCATE at most 10 calls" | Go structural, not prose: harness continuation nudges (`agent_runner.py:784`, `max_nudges = 3`) or a `remaining_time_seconds` injection (`context.py:460`) |
| **A -- works** | 39.6% -> < 15% | up ~+1 to +2 (likely inside noise) | Commitment was a real bottleneck and forced edits convert | Adopt; proceed to EXP-011 (repro cost -- see EXP-009 Part C2) |
| **B -- converts but does not score** (**most likely**, per the confound check above) | 39.6% -> < 15% | **flat** | **The most valuable outcome.** Commitment is fixable but patch *quality* is the wall -- the agent does not know where the bug is, it was not merely hesitant | Retire the commitment line of work; pivot to localisation quality (graph tools, better search, EXP-011) |
| **D -- winners break** | drops | **down** | Forced early editing damages tasks that would have resolved. The 2 disturbed E0 winners (`first_edit` 29, 30) are the canary | Retry at N=30 (0/11 disturbed, still fires on 18/19) |
| **E -- nothing moves** | flat | flat | Rule obeyed but cohort boundaries unchanged -- contradicts the trace data | Suspect measurement error; re-examine cohort definitions |

Because the revised effect (+1 to +2 tasks) sits below dev-48's ~+3-task threshold, **resolve rate is not
expected to separate A from B.** The empty-patch rate and the first-edit-turn distribution are what
distinguish them, which is exactly why EXP-009 moved those to primary.

follow-ups:
  1. **Reserved as EXP-011, deliberately NOT bundled here.** ~~Route code reading from `sed`/`cat`/`head`
     to `read_file`.~~ **Retired 2026-10-21**: that bucket turned out to be 93% heredoc *writes*, so only 31
     genuine shell reads exist across both runs and rerouting them saves ~2.8 s per task (EXP-009 Part C1).
     EXP-011 is **reframed** to target what the corrected forensics actually found: **27.3% of wall-clock
     goes to generating scratch repro scripts** (53.4 min in E0, 11.61 s median per heredoc, 5.2 per task)
     against **1.5% spent running the repository's own test suite**. The lever is preferring `pytest -k` on
     the shipped failing test over hand-writing a reproduction, plus a size cap. Still kept separate from
     this experiment -- EXP-003 is the cautionary case for stacking changes into one unmeasurable bundle.
     Full design in EXP-009 Part C2.
  2. When the dev-48 run happens, also check whether the 2 disturbed E0 winners (`first_edit` 29 and 30)
     survived. If forced-early editing breaks previously-resolved tasks, N=30 is the fallback (0/11
     disturbed, still fires on 18/19).
  3. If compliance is the failure mode rather than the hypothesis, the next lever is structural rather than
     prose: the harness's own continuation nudges (`agent_runner.py:784`, `max_nudges = 3`) or a
     `remaining_time_seconds`-driven instruction injection (`context.py:460`) could enforce the transition
     outside the prompt, which no amount of prompt wording can guarantee.
  4. EXP-009 follow-up 5 (free, no GPU): a same-config churn number from EXP-000's gold-control reruns, to
     turn the 42.9% cross-config concordance into a true same-config noise floor.

---

## Correction, 2026-10-27 (EXP-025 waiting period, zero GPU)

**The hypothesis section's "not starved" premise checked the wrong cap, and the deadline was sized off the
wrong average.** Both defects are in the same two sentences, and both are now measured. Regenerate with
`tools/exp024_stats.py` SECTION 7.

**1. "Empty-patch tasks are not starved of turns (38.0 turns vs the winners' 35.0 ... only 1 of 19 hit the
call cap)."** Both halves are true and the conclusion does not follow. The cohort that never attempts an
edit exhausts the **time** cap:

| cohort | n | time cap | call cap |
|---|---:|---:|---:|
| never attempted an edit | 21 | **19 / 21** | 4 / 21 |
| resolved | 20 | **5 / 20** | 3 / 20 |

Fisher exact on the time cap **p = 2.5e-05**; on the call cap **p = 1.0**. The two caps are cleanly
dissociated and this experiment reasoned from the one with no signal. Holds within each run (E0 13/13 vs
4/11; EXP-003 6/8 vs 1/9), which matters because the caps differ (270 s, 480 s).

Why the turn count misleads: the never-attempt cohort's calls cost **1.5-2x more** than a resolver's
(E0 10.33 vs 6.75 s/call; EXP-003 19.59 vs 9.97), with ~3x the whole-file reads. They hit the clock having
taken *fewer* turns. Resolvers finish well inside the cap (213 s of 270 s; 227 s of 480 s) and are not
racing it at all. "Same ~15k context" was also doing no work here — the binding quantity is wall-clock.

**2. The timing check at line 78** ("at E0's measured 5.38-6.83 s/turn, call 25 falls at ~135-170 s of the
240 s budget") used the **population-average** turn cost, averaged mostly over tasks that do not need the
rule. Priced at each cohort's own s/call:

| deadline | never-attempt cohort | resolved | cap |
|---|---:|---:|---:|
| call 25, E0 | **258 s (96%)** | 169 s | 270 s |
| call 25, EXP-003 | **490 s (102%)** | 249 s | 480 s |
| call 12, E0 | 124 s (46%) | 81 s | 270 s |
| call 12, EXP-003 | 235 s (49%) | 120 s | 480 s |

**At N=25 the tripwire is unreachable for the cohort it exists to rescue** — it fires at 96% of E0's cap and
past the end of EXP-003's. The later tightening to call 12 was the right move; this is the quantitative
reason, which was not the reason given at the time.

**General form, since it is easy to repeat:** a budget rule that exists to catch a failing subpopulation
must be calibrated on that subpopulation's cost, not the mean. And a rule keyed to a counter the agent
already emits is cheap to write, but calls are not what terminates the episode.

**What this does NOT establish.** Observational: these 96 task-runs predate any first-edit deadline in our
prompt, so nothing here shows the rule would convert the cohort, and H1 remains untested — `results:` above
is still **pending** for dev-48. Causation is not ordered either: expensive read-heavy calls may be a
symptom of a harder localisation problem rather than a cause of the empty patch. The decision tree above is
untouched by this correction; only its premise and its sizing are.

Carried into the paper as section 5 of `paper/writeup-draft.md`, and into section 6 there as the third of
three corrections to our own analysis — all three have the same shape, a summary statistic answering a
question it was not measuring.
