id: EXP-009-lb-variance-and-trace-forensics        date: 2026-10-21        owner: M4

hypothesis: submission #3 (EXP-005) scored 0.12 against submission #1 (E0)'s 0.06 -- a doubling. H1: the
        move is signal, i.e. something in bundle #3 caused it. H2 (the alternative): the move is run-to-run
        variance, and the public LB cannot resolve effects of this size at all. Pre-registered decision rule:
        H1 survives only if (a) an effective config difference between the two SCORED bundles exists and
        plausibly adds tasks, AND (b) the move is larger than the measured same-config spread. Otherwise
        adopt H2 and treat the LB as a pass/fail budget check, not a measurement instrument.
        Secondary, exploratory (no pre-registered rule): where does the per-task wall-clock budget actually go,
        and which process metric separates tasks that score from tasks that score nothing?

single variable changed: none -- **zero-GPU retrospective analysis** of artifacts already on disk
        (submissions #1/#3 git trees, E0 + EXP-003 dev-48 traces). No kernel pushed, no model run.
        New tool: `tools/run_forensics.py` (subcommands `forensics` / `compare` / `lb`), which answers the
        three questions `tools/analyze_traces.py` does not: per-tool wall-clock attribution, paired
        per-task run comparison, and LB-move significance.

cohort: no new cohort. Reuses dev-48 (`experiments/cohorts/dev-48.txt`, seed 20261013) as already run by
        EXP-001 (E0) and EXP-003, plus the 58-task public LB half as scored for submissions #1 and #3.
        GPU-h used: **0.0**

config: analysis only. Evidence committed under `experiments/EXP-009/`:
        `forensics-E0-dev48.txt`, `forensics-EXP003-dev48.txt`, `paired-E0-vs-EXP003.txt`,
        `lb-variance-sub1-vs-sub3.txt`. Reproduce with:
          `python tools/run_forensics.py lb 4 58 7 58`
          `python tools/run_forensics.py compare runs/E0-dev48-baseline/runs/E0-dev48-baseline runs/exp003_public_budget_dev48/runs/EXP-003-public-budget-dev48`
          `python tools/run_forensics.py forensics runs/E0-dev48-baseline/runs/E0-dev48-baseline`

---

## Part A -- the 0.06 -> 0.12 move is noise. H2 adopted, H1 rejected.

### A1. Provenance audit: what actually differed between the two SCORED bundles

Checked at the artifact level, not from config comments. Submission #1's zip was **not** commit `ee1b209`'s
tree: per `EXP-001-baseline.md`, it was packed from `ee1b209` with `submission/prompts/swe_coder.md` reverted
to its `e1d61fb` state. So the comparison that matters is (ee1b209 + e1d61fb prompt) vs `6bff133`.

Stripping comments and blank lines from every file in both bundles, the **complete** list of effective
differences is:

| what | submission #1 (scored 0.06) | submission #3 (scored 0.12) | live? |
|---|---|---|---|
| `eval_config.yaml: max_time_minutes` | 4.5 | **4.0** | **yes -- the only live change** |
| `submission/skills/edit-anchoring/SKILL.md` | absent | present in the *source tree* | **no -- never reached either zip, see A2** |
| `prompts/swe_coder.md` | `e1d61fb` state | `6bff133` state | no -- **byte-identical** (`git diff` empty) |
| `agent.yaml` | | | no -- identical |
| `sampling.yaml: max_output_tokens` | 4096 | 4096 | no -- identical |
| `sampling.yaml: thinking_budget` | 256 | 256 | no -- identical (trailing comment only) |
| `temperature` / `top_p` / `top_k` | 0.2 / 0.95 / 64 | 0.2 / 0.95 / 64 | no -- identical |

**The `max_output_tokens` 4096 -> 8192 and `thinking_budget` 256 -> 4096 bump never appeared in a scored
submission.** Its full history: `1681df9` set 4096/256 (shipped as #1); `e4b2f3b` raised it to 8192/4096 as
part of the EXP-003 bundle (shipped as **#2, which hit Notebook Timeout and produced no score**); `ae9f3ee`
reverted both to E0's values before #3. This is the single most likely thing to misremember as "we changed
it and the score doubled" -- it was changed, on the submission that returned nothing.

The one live change, `max_time_minutes` 4.5 -> 4.0, is **strictly time-dominated by E0** and can only cost
tasks. EXP-005's own pre-registered estimate from E0's traces was **-0.4 tasks**. We observed +3.

### A2. The new SKILL.md is inert -- but the discovery path is a trap worth recording

**Corrected 2026-10-21 after packing EXP-010:** the skill was not merely unattached, it was never
shipped. `tools/pack_submission.py` computes a reachability closure from `agent.yaml` and ships only what
that reaches -- **4 files** (`agent.yaml`, `configs/sampling.yaml`, `eval_config.yaml`,
`prompts/swe_coder.md`). Verified directly against the archives: `dist/exp005_e0_4min_safe.zip`
(sha `9a98ff89...`, the bundle scored as #3) and `dist/exp003_test.zip` both contain exactly those 4 names
and no `SKILL.md`. The validator lists the skill under "unreferenced (not shipped by the packer)".

**So the two scored bundles differ by exactly one thing: `max_time_minutes` 4.5 -> 4.0.** That is a stronger
version of A1's conclusion, not a weaker one.

The attachment gate is still worth recording as a trap, because it is the *second* line of defence and it
behaves unintuitively. `adk_submission/discovery.py:598` discovers skills by `rglob("SKILL.md")` -- it scans
the **entire** submission tree, regardless of what `agent.yaml` says, and registers everything it finds into
a `SkillRegistry`. Attachment is gated separately: `adk_submission/resolvers/tools.py:150` is
`if not config.skills: return None`. Our `agent.yaml` declares no `skills:` key at all ("prompt-only, single
agent, no adapter, no skills"), so even a skill that *did* reach the zip would be discovered, loaded into the
registry, and never attached.

**Trap for later:** the day we add a `skills:` key, every stray `SKILL.md` anywhere under `submission/`
becomes eligible for name-matching in `resolve_skills` (it matches on directory basename, with `_`->`-`
normalisation, not on path). Recorded in plan.md §10.1.

### A3. The truncation hypothesis is dead

The one mechanism that would have made +3 real: E0 at 4.5 min sat exactly on the 11.0 h gate, so if its LB
run had been partly cut off by the notebook clock, the 4.0-min cap would have bought ~1 h and let more tasks
be attempted. Ruled out:

- `swegemma/budget.py` defines only `EvaluationBudget` ("terminate or conclude a **task session**") and
  `HarnessLimits` (per-tool). There is **no run-level budget** anywhere in the harness.
- A global overrun is therefore enforced only by Kaggle's notebook timeout, which is **fatal, not
  partially-credited** -- demonstrated by submission #2: 18.0 h projected, "Notebook Timeout", *no score at all*.

Both #1 and #3 returned a score, so both completed all ~120 hidden tasks. Nothing was truncated. +3 cannot
be "more tasks got attempted".

### A4. The move is inside the same-config spread

`python tools/run_forensics.py lb 4 58 7 58`:

| statistic | value |
|---|---|
| #1 = 4/58 = 0.0690 | Wilson 95% [0.027, 0.164] |
| #3 = 7/58 = 0.1207 | Wilson 95% [0.060, 0.229] |
| Fisher exact two-sided | **p = 0.5281** |
| pooled rate | 11/116 = 9.48% (5.50 of 58); binomial sd = 2.23 tasks |
| P(two **identical** runs differ by >= 3 tasks) | **0.424** |
| P(two identical runs differ by >= 4 tasks) | 0.264 |

Each score sits inside the other's CI, and identical configs reproduce a 3-task gap 42% of the time.

### A5. Mechanism, confirmed locally: the solved set churns by more than half

`python tools/run_forensics.py compare <E0> <EXP-003>` over the same 48 tasks:

```
both resolved : 6
E0 only       : 5   fastapi_13207 fastapi_13537 fastapi_14297 fastapi_14873 rich_3676
EXP-003 only  : 3   fastapi_15589 fastapi_5624 fastapi_9753
neither       : 34
discordant pairs: 8    exact McNemar two-sided p = 0.7266
concordance of the solved set: 6/14 = 42.9%
```

Only **6 of the 14 distinct tasks** either run solved were solved by both, and the 8 flips are symmetric
(p=0.73) -- i.e. mostly noise, not config effect, even though EXP-003 changed five variables at once. At
`temperature: 0.2`, with a non-deterministic vLLM reduction order under TP=4 and continuous batching, there
is a wide band of borderline tasks that coin-flip per run. On 58 hidden tasks at a ~9.5% base rate that band
is worth +/-3 easily.

**This also means our marginal-resolve-rate comparisons have been reading mostly noise.** EXP-003's headline
"18.75% vs E0's 22.9%" is a -2-task marginal difference sitting on top of 8 discordant pairs.

---

## Part B -- where the 4.5 minutes actually go (exploratory)

`python tools/run_forensics.py forensics runs/E0-dev48-baseline/runs/E0-dev48-baseline` -- E0, 48 tasks,
195.5 min of agent wall-clock, time attributed to the tool called in each turn.

### B1. 74% of the budget is spent reading code; 12% editing

| activity | E0 | share | EXP-003 | share |
|---|---|---|---|---|
| reading/searching (`grep`+`sed/cat/head`+`find`+`read_file`) | 144.0 min | **73.7%** | 183.4 min | **70.5%** |
| editing (`edit_file`+`write_file`) | 22.9 min | **11.7%** | 36.8 min | 14.1% |
| executing/verifying (`python`+`pytest`) | 16.6 min | 8.5% | 10.4 min | 4.0% |
| overhead (`get_status`, `submit_patch`, `git`, no-tool) | 12.0 min | 6.1% | 29.7 min | 11.4% |

Exploration:edit **call** ratio is 8:1 (1,424 read/search calls vs 179 edit calls).

### B2. The agent reads code through its slowest available path

| how it reads | calls | median s/call |
|---|---|---|
| `read_file` (the purpose-built tool, capped at 150 lines / 10k chars) | 563 | **2.74 s** |
| `run_command` with `sed`/`cat`/`head`/`awk` | 253 | **11.40 s** |
| `run_command` with `grep`/`rg` | 418 | 4.34 s |

`sed/cat/head` is the single most expensive activity in the whole run: 253 calls, 52.7 min, **27% of all
agent wall-clock**, at 4.2x the per-call cost of `read_file`. Replicated in EXP-003 (188 calls, 67.2 min,
13.02 s median). `pytest` is almost free by comparison (48 calls, 4.8 min, 2.2% of run_command time) -- the
cost is in reading, not in testing.

### B3. The metric that separates scoring from not scoring is the turn of the FIRST edit

| cohort | n | turns | s/turn | max prompt tok | **first-edit turn** | n_edits |
|---|---|---|---|---|---|---|
| resolved | 11 | 35.0 | 5.38 | 14,510 | **18.0** | 3.0 |
| patch-but-failed | 18 | 39.5 | 6.62 | 14,918 | **18.0** | 2.0 |
| empty-patch | 19 | 38.0 | 6.83 | 14,882 | **43.0** | 0.0 |

Replicated independently on EXP-003's different config (resolved 14.0, patch-but-failed 17.0, empty-patch 32.5).

The split is **not** resolved vs unresolved -- it is *edited* vs *never edited*. Tasks that reach an edit by
~turn 18 produce a patch; tasks whose first edit would land around turn 43 never get there, because the clock
kills them around turn 38.

Supporting facts:
- **13/48 tasks never called `edit_file`/`write_file` at all** (8/48 in EXP-003).
- All 19 empty-patch tasks ran to the wall (271-276 s against a 270 s cap).
- Empty-patch tasks are **not** starved of turns: 38.0 turns vs 35.0 for resolved, and the same ~15k context.
  They spend a full budget and commit to nothing.
- The call cap is **not** binding: only 1 of the 19 reached 45 calls.
- **Among the 29 tasks that produced any patch, 11 resolved = 37.9%.** Producing a patch is worth ~0.38 tasks.

### B4. The "binding constraint is wall-clock" reading needs qualifying

EXP-001's follow-up concluded `time_cap_hit` (79.2%) >> `calls_cap_hit` (12.5%), so budget work should steer
to the time axis. The cap-hit counts are right, but the inference does not follow: the tasks hitting the cap
are largely the ones that were never going to score, and **buying more time does not buy more work**.
EXP-003 nearly doubled the cap (4.5 -> 8 min) and got *fewer* turns per task (resolved 26.0 vs E0's 35.0),
because its own bundled generation changes made each turn 1.4-1.8x slower (s/turn 7.79-12.13 vs E0's
5.38-6.83). Empty-patch rate barely moved: 39.6% -> 33.3%.

This is **confounded** -- EXP-003 bundled six changes -- but `max_output_tokens` 4096->8192 and
`thinking_budget` 256->4096 are the two that directly control tokens generated per turn, and they are the
most plausible cause of the s/turn regression. Read as: raising output/thinking budget is a **net negative on
step throughput**, and the untested 8192 config is likely worse than E0, not better. Needs isolation to confirm.

---

## results (summary)

| finding | status |
|---|---|
| H1 (the LB move is signal) | **REJECTED** -- only live delta could only cost tasks (-0.4 expected); Fisher p=0.53 |
| H2 (the move is variance; LB cannot resolve it) | **ADOPTED** |
| Public-LB minimum detectable effect | **~4 tasks (~0.07)**, not the +/-2 tasks (0.035) assumed in plan.md §5.5 |
| Best estimate of our true public rate | **pooled 11/116 = 9.5%**, not 12% |
| Per-task outcome stability, same cohort, two runs | **42.9% concordance** of the solved set (6/14) |
| Harness run-level budget | **does not exist**; global overrun is fatal, never partially credited |
| Auto-discovered-but-undeclared skills | **never packed** (packer ships only `agent.yaml`'s 4-file closure); and even if packed, discovered by `rglob` but **not attached** without a `skills:` key |
| Share of agent wall-clock spent reading code | **73.7%** (E0), 70.5% (EXP-003) |
| Share spent editing | **11.7%** (E0), 14.1% (EXP-003) |
| `sed`/`cat`/`head` vs `read_file` per-call cost | **11.40 s vs 2.74 s** (4.2x), 27% of total wall-clock |
| First-edit turn, scoring vs empty | **18 vs 43** (E0); 14-17 vs 32.5 (EXP-003) |
| Tasks that never edit a file | **13/48** (E0), 8/48 (EXP-003) |
| Conversion once a patch exists | **11/29 = 37.9%** |

decision: **no config change adopted from this analysis** (it changed no variable). Three process decisions,
all adopted into plan.md:

1. **Stop reading single-day LB deltas as signal.** The daily slot is a pass/fail budget-and-transfer check,
   not an experiment. Threshold raised from 0.035 to **~0.07**; and since the public half is only 58 of ~120
   with a private half deciding the final standing, public-LB tuning has low value regardless. (plan.md §5.5)
2. **Primary outcome metrics change.** Score the next experiments on **empty-patch rate** (39.6%, target
   <15%) and **median first-edit turn** (18 vs 43, target <20 for all cohorts) rather than resolve rate.
   These are high-prevalence, tight-CI, large-effect metrics; resolve rate at n=48 has sd ~2.9 tasks, so the
   existing "Δ >= +3 tasks" adoption rule is barely 1 sigma. (plan.md §5.5)
3. **Always report the paired comparison.** `tools/run_forensics.py compare` on every A/B from now on;
   marginal rates alone are not admissible evidence. (plan.md §5.5)

follow-ups:
  1. **Proposed next experiment (NOT started, needs go-ahead): EXP-010, "commit to an edit early".**
     Prompt-only, single-variable-in-spirit change to `submission/prompts/swe_coder.md`, targeting B2+B3:
     (a) route code reading to `read_file` and forbid `sed`/`cat`/`head` for reading file contents
     (reclaims up to ~27% of wall-clock at 4.2x cheaper per call);
     (b) a hard first-edit deadline -- make the first `edit_file` call by ~turn 15, and if the bug is not
     located by then, edit the best candidate anyway.
     Pre-registered primary metrics: empty-patch rate (39.6% -> <15%) and median first-edit turn for the
     empty-patch cohort (43 -> <20). Secondary: resolve rate, reported with the paired table.
     Expected effect: **revised to +1 to +2 dev-48 tasks** (originally estimated +3.6). The 37.9%
     conversion figure is measured on *voluntary* edits; a stratified check run before submitting EXP-010
     (`experiments/EXP-010/late-edit-conversion.txt`, pooled n=96 task-runs) shows that tasks which first
     edit *after* turn 25 resolve at only **9.5%**, against **33.3%** for turn <= 25 (Fisher exact
     p = 0.0438) -- and that late population is exactly what a tripwire acts on, so 9.5% is the right
     conversion prior, not 37.9%. Still positive expected value, because the counterfactual is a guaranteed
     zero, but **below dev-48's own ~+3-task detection threshold**, so the experiment's value is as a
     mechanism probe on the process metrics rather than a resolve-rate win. Shipped as submission #4 on
     2026-10-21; see `experiments/EXP-010-first-edit-tripwire.md`.
  2. **`max_output_tokens` / `thinking_budget` are genuinely untested** and should be isolated *downward*,
     not upward, per B4: E0 is 4096/256; the 8192/4096 variant has never been scored on the LB and was never
     isolated locally. A cheap smoke-8 pass at 2048/256 would test whether step throughput buys more than
     generation headroom costs. Lower priority than follow-up 1.
  3. **De-prioritise EXP-003c** (isolating `max_tool_calls` 28 vs 45). B3 shows the call cap is not binding
     (1 of 19 empty-patch tasks reached it); the time wall binds, and it binds for behavioural reasons.
  4. **Idle GPU buys throughput, not latency** -- EXP-006's 88.6% idle KV at 31B cannot make a sequential
     turn faster, so it cannot help B2/B3. It only pays off for the best-of-N variant parked in plan.md §6.3.
     Recorded there so the idea is not re-derived as a latency fix.
  5. Re-run `tools/run_forensics.py compare` across EXP-000's gold-control reruns to get a **same-config**
     churn number (this analysis's 42.9% concordance is across two *different* configs, so it is an upper
     bound on config effect and a lower bound on pure noise). Free, no GPU.
  6. `experiments/README.md` §3's index table is still missing rows for EXP-000/001/003/004/005 even though
     detailed log sections exist. Carried over, still not fixed.
