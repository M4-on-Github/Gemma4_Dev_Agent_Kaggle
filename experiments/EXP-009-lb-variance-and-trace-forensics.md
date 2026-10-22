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

### B1. Where the budget actually goes: reading 26%, WRITING SCRATCH REPRO SCRIPTS 27%, editing 12%

> **Corrected 2026-10-21 -- see Part C1.** The first version of this section reported "73.7% reading"
> because the command classifier counted `cat > /tmp/repro.py <<EOF` as a read. It is a write, and it turns
> out to be the single largest line item in the run. The per-call timings below were always right; only the
> labels were wrong.

| activity | E0 | share | EXP-003 | share |
|---|---|---|---|---|
| **writing scratch repro scripts** (`run_command` heredoc) | **53.4 min** | **27.3%** | **63.4 min** | **24.4%** |
| reading (`read_file` + genuine `sed`/`cat`/`head` reads) | 51.2 min | 26.2% | 66.3 min | 25.5% |
| searching (`grep`/`rg`) | 39.1 min | 20.0% | 51.4 min | 19.7% |
| editing (`edit_file`+`write_file`) | 22.9 min | **11.7%** | 36.8 min | 14.1% |
| **running the test suite** (`pytest`) | **3.0 min** | **1.5%** | **2.7 min** | **1.0%** |
| other `python` (running a script it wrote) | 11.8 min | 6.0% | 7.5 min | 2.9% |
| `find`/`ls`/`git`/other | 4.7 min | 2.4% | 3.3 min | 1.3% |
| harness overhead (`get_status`, `submit_patch`, no-tool) | 9.5 min | 4.9% | 28.9 min | 11.1% |

Reading plus searching is **46.2%** of E0 and 45.2% of EXP-003, not the 73.7%/70.5% first reported. The
headline number is the new top row: the agent spends **more time hand-writing reproduction scripts than it
spends reading the repository**, and roughly **18x more time writing reproductions than running the tests
that ship with the task** (53.4 min vs 3.0 min).

### B2. The expensive path is WRITING repro scripts, not reading code

> **Rewritten 2026-10-21 -- see Part C1.** The original B2 claimed the agent "reads through its slowest
> available path" and proposed routing shell reads to `read_file` as EXP-011. That conclusion was an
> artifact of the classifier bug and is withdrawn.

| `run_command` program (E0) | calls | median s/call | total |
|---|---|---|---|
| **heredoc write** (`cat > /tmp/repro.py <<EOF`) | **248** | **11.61 s** | **53.4 min** |
| `grep`/`rg` | 418 | 4.34 s | 39.1 min |
| `python` (running a script it wrote) | 94 | 8.41 s | 11.8 min |
| `pytest` | 42 | 2.84 s | 3.0 min |
| genuine `sed`/`cat`/`head` reads | **11** | 6.57 s | 1.2 min |
| `read_file` (not a `run_command`; shown for comparison) | 563 | 2.74 s | 50.0 min |

The 11.61 s median for a heredoc is **not** I/O. It is the time to *generate the whole script as tool-call
arguments, token by token*. At 248 calls across 48 tasks that is 5.2 repro writes per task, and the shipped
prompt explicitly asks for them (`prompts/swe_coder.md` line 102: "REPRODUCE (at most 6 calls). Write
/tmp/repro.py via a run_command heredoc..."). The agent is complying with the call cap; the cap just does
not price generation.

Genuine shell reading is a rounding error: **11 of E0's 253** originally-labelled `sed`/`cat`/`head` calls,
and 31 of 441 pooled across both runs. Verified twice independently.

Crucially, **winners reproduce too** -- the resolved cohort spends 22.6% of its wall-clock on heredoc writes
against the empty-patch cohort's 38.1% (pooled: 24.1% vs 32.7%). So reproduction is not dead weight to be
deleted; failing tasks simply do more of it. The lever is making it *cheaper*, which is the reframed EXP-011
in Part C2.

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

## Part C -- corrections and a second round of analysis (2026-10-21, later)

Four follow-up analyses were run after the sections above were written. Two of them changed conclusions
already recorded here, so they are documented as corrections rather than additions.

### C1. CORRECTION: the command classifier was counting heredoc writes as reads

`tools/run_forensics.py` classified `run_command` calls with this table, checked in order:

```python
("pytest",       r"pytest"),                              # unanchored
("grep/rg",      r"^\s*(grep|rg|egrep|git\s+grep)\b"),
("sed/cat/head", r"^\s*(sed|awk|cat|head|tail|wc)\b"),
```

Two bugs. First, the agent writes scratch files as `cat > /tmp/repro.py <<EOF`, which starts with `cat` and
so landed in `sed/cat/head` -- the bucket the analysis treated as *reading*. Second, `pytest` is unanchored
and checked first, so any heredoc whose script *body* mentioned pytest was scored as a test run.

Measured impact, pooled over E0 + EXP-003 (441 calls in that bucket):

| | calls | share |
|---|---|---|
| write-like (`<<` heredoc, `sed -i`, or `cat`/`tee` with a redirect) | **410** | **93.0%** |
| genuine reads (`sed -n`, `cat f.py`, `head`, `tail`) | 31 | 7.0% |
| heredocs additionally mislabelled as `pytest` | 7 | -- |

Example of what was being counted as a read:

```
cat > /tmp/repro.py <<EOF
from __future__ import annotations
from fastapi import FastAPI
...
```

Fixed in `tools/run_forensics.py` by adding a `heredoc-write` class **first** in the table (so it wins over
both `cat` and a pytest-mentioning body) and renaming the read bucket to `shell-read`. The evidence files in
`experiments/EXP-009/` were regenerated; B1, B2 and the summary table above are corrected. Downstream
corrections were applied to `EXP-001-baseline.md`, `plan.md` 6.3, this README's section 2, and EXP-010's
follow-up 1.

**Process note worth keeping.** Every number in the original B1/B2 was arithmetically correct. The error was
entirely in a label, in a 7-line regex table written to support the analysis, and it survived because the
conclusion it produced ("the agent reads inefficiently") was plausible. The check that caught it was asking
a *different* question of the same data -- "does heavy shell-reading predict failure?" -- which forced an
inspection of what was actually in the bucket. Plausible-and-wrong is the expensive failure mode here;
nothing in the statistics would ever have flagged it.

### C2. EXP-011 retired as conceived, and reframed

**Retired:** "route code reading from `sed`/`cat`/`head` to `read_file`." There are 31 genuine shell reads
across 96 task-runs. At the measured 6.57 s vs 2.74 s per call, rerouting all of them saves about **2.8 s
per task** out of a 240 s budget. Not worth a submission slot.

**Reframed -- EXP-011 is now about the cost of reproduction.** The target is the 27.3% of wall-clock spent
generating repro scripts (53.4 min in E0, 63.4 min in EXP-003), against 1.5% spent running the repository's
own test suite. Three sub-levers, in order of expected value:

1. **Prefer the existing failing test over a hand-written repro.** These are SWE-bench-style tasks: a test
   patch ships with the task and the issue usually names the behaviour under test. `pytest` costs 2.84 s
   median; a heredoc costs 11.61 s and the agent does 5.2 of them per task. Instruct it to try
   `pytest -k <keyword>` on the existing suite *before* writing anything.
2. **Cap repro size.** The observed scripts open with `from __future__ import annotations` and rebuild a
   full app. A "15 lines maximum" instruction attacks the generation cost directly, since cost here is
   token count.
3. **Write it once.** 5.2 heredoc writes per task means the agent is rewriting the repro repeatedly. One
   explicit "you have already written a repro; edit it with `sed -i` or move on" rule may be enough.

Expected effect, conservatively: if heredoc writes fall from 5.2 to ~2 per task, that returns roughly
3.2 x 11.61 s = **37 s per task**, about **15% of the 240 s budget**, to searching and editing. Unlike the
EXP-010 tripwire this does not force a behaviour change -- it makes an existing behaviour cheaper -- so the
downside is bounded by whatever reproduction is actually worth. Note the constraint from B2 that winners
reproduce too: do **not** test "stop reproducing", test "reproduce more cheaply".

### C3. Harness grading is itself flaky, and the mechanism is identified

Analysis of all 19 `runs/EXP-000-*/gold_control.jsonl` files (373 records, 129 distinct tasks, grade field
`resolved`):

| | tasks |
|---|---|
| unanimous PASS across every dir it appears in | 98 |
| unanimous FAIL | 18 |
| **MIXED -- same task, same gold patch, different outcome** | **13 (10.1%)** |

10.1% is an **upper bound**, because the 19 dirs are not repeats of one configuration -- they differ in
wheel pins and `--curate-wheels` settings. Decomposing:

- 3 of the 13 (`rich_3782`, `rich_4070`, `rich_4079`) flip between the `all` and `final` dirs, which is the
  deliberate `pygments==2.20.0` default pin. **Config, not noise** -- and this is the 108/129 vs 111/129
  discrepancy in this README.
- Excluding the outlier dir `probe2` (14 of its 15 tasks fail, 9 with `ModuleNotFoundError`) drops the mixed
  rate to **5.4%**; excluding `negctl` too (which the `--negative-control` flag suggests *should* fail)
  gives **4.7%**.
- The cleanest same-config comparison is `probe2` vs `v2`: 9 shared task ids, **identical recorded curation
  dicts**, and all 9 disagree (probe2 FAIL, v2 PASS). `v2` vs `v3` disagree on 0 of 15.

**Mechanism, documented in our own code.** `tools/gold_control.py:32-46` describes
`container_setup._build_unpacked_wheels_tar` caching to `{tempdir}/swegemma_sp_cache_v8/{cache_name}.tar`
under the literal name `sp_base`, returning early whenever that file exists. The tar is therefore built from
whichever pool the *first* task used and reused for every later task regardless of its own `wheels_dir`, and
it outlives the process. The docstring's own example is `fastapi_13920` passing alone but failing with
`ModuleNotFoundError: typing_inspection` when a requests task ran first -- which is exactly `probe2`'s
dominant failure (`typing_inspection` x7). `_clear_sitepackages_tar_cache()` is called **only** under
`if args.curate_wheels:` (line 168), so any run without that flag is fully exposed.

**Consequences:**

1. A floor of a few percent of per-task outcome churn is **environmental, not the agent's sampling**. It
   does not explain the E0-vs-EXP-003 42.9% concordance (far too small), but it means that concordance is
   an upper bound on *agent* churn with a non-zero environmental component underneath.
2. **Open question to check before the next local comparison:** do the dev-48 *agent* runs share one wheel
   pool across tasks? If they do, they are safe, exactly as official grading is. If any run varied the pool
   per task without `--curate-wheels`, its per-task grades may carry the same leak. This is a code-reading
   question, no GPU required.
3. The 18 unanimous-FAIL tasks are stable across all dirs, so the EXP-000 exclusion list is sound.

### C4. No same-config agent repeat exists anywhere in the repo

Checked while setting up C3: only **three** directories under `runs/` contain `task_results.jsonl` at all --
`E0-dev48-baseline`, `exp002_estop_a_smoke8` (8 tasks) and `exp003_public_budget_dev48`. The 19 EXP-000 dirs
are gold-patch controls, not agent runs.

So the 42.9% cross-config concordance in A5 has **nothing beneath it**: there is no measurement of what two
runs of the *same* config do to the same task. Every noise statement in this document and in `plan.md` 5.5
rests on a cross-config number used as a proxy. Getting the real one requires re-running E0 on dev-48 and
costs GPU quota, which is why it keeps being deferred -- but it is the single highest-value quota purchase
available, because it calibrates every A/B comparison the project will ever run.

### C5. What happens BEFORE the first edit: volume separates winners from losers, composition does not

This is the analysis that bears most directly on EXP-010 (submitted as #4 and currently awaiting a score).
Define a task's **prefix** as every turn before the first turn containing `edit_file`/`write_file`; if the
task never edits, the whole trace is the prefix. 96 run-task pairs (E0 + EXP-003), cohorts: resolved n=20,
patch-but-failed (PBF) n=41, empty-patch n=35.

**Prefix length, median (min-max):**

| cohort | n | tool-bearing turns | seconds | share of call cap | share of time cap |
|---|---|---|---|---|---|
| resolved | 20 | **12** (3-27) | **108.0** (18-230) | 0.350 | 0.282 |
| patch-but-failed | 41 | 14 (2-38) | 140.5 (18-385) | 0.356 | 0.404 |
| empty-patch | 35 | **30** (13-47) | **267.7** (69-476) | **0.867** | **0.901** |

The separation is large and one-directional. As AUC, P(resolved prefix > empty-patch prefix) = 0.069 on
turns, 0.027 on seconds, 0.067 on tool calls -- i.e. **P(empty-patch > resolved) = 0.93 to 0.97**. It holds
*within* each run, so it is not an artifact of pooling two budgets: E0 17 vs 38 turns, EXP-003 13 vs 30.5.

**Composition, by contrast, separates nothing.** Every ratio tested came back at chance:

| metric | resolved vs empty-patch | reading |
|---|---|---|
| grep:read ratio | AUC 0.488 (0.533 heredoc-excluded) | no signal |
| reproduced before first edit | 20/20 vs 32/35, Fisher **p = 0.293** | no signal |
| distinct files touched (median) | 2 vs 3, AUC 0.668 | weak at best |

So the agent that solves the task is not searching *differently* -- it is reaching its first edit in a third
of the time. That is exactly the premise EXP-010's tripwire is built on, which is reassuring, but:

> **Direction is NOT identified, and this is the key caveat for reading submission #4.** 25 of 35
> empty-patch runs hit the session timeout and 12 of 35 hit the tool cap (against **0 of 20** resolved runs
> hitting either). A long prefix is therefore partly *caused* by the budget running out rather than causing
> the failure. "Investigating too long prevents the edit" and "it ran out of budget before it could edit"
> predict the same table. EXP-010 is the intervention that distinguishes them -- which is precisely why its
> compliance check must come before its resolve rate.

**Two findings that cut against doing less:**

1. **All 20 resolved runs reproduced before their first edit** (20/20, strict test: a real `python`/`pytest`
   invocation outside a heredoc body). Reproduce-first is also the *only* composition metric that separates
   resolved from PBF (AUC 0.622; 20/20 vs 31/41; p = 0.064 vs not-resolved). Combined with B2's cohort
   split, this is the second independent reason the reframed EXP-011 must make reproduction **cheaper, not
   optional**.
2. The empty-patch cohort splits **21 never edited at all / 14 edited but shipped an empty final patch**,
   with near-identical prefixes (31 turns / 269 s vs 32 turns / 257 s). The tripwire only addresses the
   first group.

**Third independent confirmation of the C1 bug.** This analysis was run against the *unfixed* classifier and
hit the same artifact from a different direction: of 351 commands whose label disagreed with a strict
invocation test, **350 contained a heredoc**, and 195 of the empty-patch cohort's 213 `sed/cat/head` calls
were heredoc writes. The label-based reproduce rate reads 26/96 (27.1%) against the strict test's **83/96
(86.5%)** -- the bug was understating reproduction by a factor of three. `/tmp/repro.py` alone appears 546
times, and **0** `read_file` calls ever target a `/tmp` path.

*Caveat carried from the source analysis:* the Fisher p-values treat 96 run-task pairs as independent, but
the same 48 task ids appear in both runs under different budgets, so they are optimistic. The AUCs are
descriptive and unaffected.

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
| Share of wall-clock WRITING scratch repro scripts | **27.3%** (E0), 24.4% (EXP-003) -- largest single item |
| Share spent reading + searching | **46.2%** (E0), 45.2% (EXP-003) -- corrected down from 73.7%, see Part C1 |
| Share spent editing | **11.7%** (E0), 14.1% (EXP-003) |
| Share spent running the test suite | **1.5%** (E0), 1.0% (EXP-003) |
| Genuine shell reads (`sed`/`cat`/`head`) | **11 of 253** (E0); 31 of 441 pooled -- a rounding error |
| Gold-control disagreement across EXP-000 dirs | **13/129 = 10.1%** upper bound; mechanism is a harness tar-cache leak, see Part C3 |
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
  1. **DONE -- shipped as EXP-010, "commit to an edit early" (submission #4, 2026-10-21).**
     Prompt-only change to `submission/prompts/swe_coder.md`, targeting B3:
     a hard first-edit deadline -- make the first `edit_file` call by ~turn 15, and if the bug is not
     located by then, edit the best candidate anyway.
     ~~(a) route code reading to `read_file` and forbid `sed`/`cat`/`head` for reading file contents
     (reclaims up to ~27% of wall-clock at 4.2x cheaper per call)~~ -- this half was split out as EXP-011
     rather than bundled, and has since been **retired entirely**: the ~27% was heredoc *writes*, not reads
     (Part C1), and only 31 genuine shell reads exist across both runs, so rerouting them saves ~2.8 s per
     task. The splitting decision is what kept a measurement artifact out of a submission. EXP-011 is
     reframed onto the real 27% in Part C2.
     Part C5 adds the strongest support yet for the tripwire's premise -- resolved runs reach their first
     edit at a median 12 tool-bearing turns / 108 s against empty-patch's 30 / 268 s, P(empty > resolved)
     = 0.93-0.97, holding within each run -- **and** the reason the premise is not yet proven: 0 of 20
     resolved runs hit the time or call cap, while 25 of 35 empty-patch runs timed out, so budget
     exhaustion and over-investigation predict the same table. Check EXP-010's *compliance* before its
     resolve rate.
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
  5. **DONE, but it does not answer the question it was written for -- see Parts C3 and C4.** The 19
     `EXP-000-*` directories are **gold-patch controls, not agent runs**, so they cannot yield agent churn
     at all; only 3 directories under `runs/` contain `task_results.jsonl`, and no two of them share a
     config. What the analysis did produce is a different and useful number: **13/129 = 10.1%** of tasks
     disagree with themselves across dirs on the *gold patch* (5.4% excluding the `probe2` outlier), caused
     by a harness tar-cache keyed by a constant that leaks one task's dependencies into the next. So the
     42.9% concordance still has **no same-config baseline beneath it**, and getting one requires re-running
     E0 on dev-48 at GPU cost. That re-run is now the highest-value quota purchase on the list, because it
     calibrates every A/B this project will run.
  6. **DONE (commit `e983d0c`).** `experiments/README.md` §3's index table now carries rows for
     EXP-000/001/003/004/005.
  7. **NEW, free, no GPU (from Part C3):** check whether the dev-48 *agent* runs share one wheel pool across
     tasks. If they do they are safe, exactly as official grading is; if any varied the pool per task
     without `--curate-wheels`, its per-task grades carry the same tar-cache leak. This is a code-reading
     question about `container_setup`/`gold_control.py`, not a run.
