# EXP-022 — Direction review: where we stand, what could be worth +6 tasks, and what to do with today's slot

**Date:** 2026-10-25 (written 22:00-23:00 UTC; the daily slot closes 23:59 UTC). **GPU cost: zero.** Read-only Kaggle CLI queries,
analysis of dev-48 runs we already own, and one public notebook read as data.
**Status:** findings, a ranked programme, and one **pre-registered** submission recommendation. **This document does not submit
anything.** Sections 4.3 (readings) and 4.2 (config and diffs) were committed **before** the candidate bundle was built; the build
record is Appendix B and was appended afterwards.

**Reproduce every number that is not quoted from another document:**

```
python -I -X utf8 tools/exp022_stats.py --e0 <RUN_DIR E0> --exp3 <RUN_DIR EXP-003> --lb-csv <leaderboard csv>   # seed 22; output in experiments/EXP-022/stats.txt
python -I -X utf8 tools/exp022_make_candidate.py <davis0178 notebook.ipynb> experiments/EXP-022/candidate     # section 4.2, run only after the pre-registration commit
```

`RUN_DIR` is the directory that holds `task_results.jsonl` and `traces/` (`runs/` is gitignored; in the maintainer's main checkout:
`runs/E0-dev48-baseline/runs/E0-dev48-baseline` and `runs/exp003_public_budget_dev48/runs/EXP-003-public-budget-dev48`).
The leaderboard CSV is `gemma-4-developer-agent-publicleaderboard-2026-10-25T21_38_25.csv` (3,758 teams), downloaded with the read-only
CLI into `untrusted/` and never committed.

---

## 0. Verdicts

1. **Deterministic-core test (the mandatory first step): the data were not absent, they were already in the repo, and the answer is
   "neither".** E0 and EXP-003 share **6** resolved dev-48 tasks of 14 distinct (E0-only 5, EXP-003-only 3, neither 34). Under independent
   runs the expected overlap is 2.06; Fisher exact **p = 0.0023**, odds ratio 13.6, inter-run **phi = 0.50** (task-bootstrap 95% CI
   0.16-0.78). Only 6/11 of E0's resolves and 6/9 of EXP-003's recur in the other run. So task difficulty is strongly heterogeneous
   (the "core" is real), but a core that resolves "on nearly every run" is **refuted**: roughly half to two-thirds of a run's resolves
   repeat, the rest are lottery. (Section 1.3.)
2. **The six-submission "underdispersion" (variance 2.267 vs binomial 5.900, X2 = 1.921, P = 0.14) is not evidence of anything.** It is
   what ordinary task-difficulty heterogeneity predicts for six runs on one fixed 58-task set: at the measured phi of 0.50 the predicted
   variance is 2.94 and P(s2 <= 2.267) = 0.47. The binomial null in `submissions.md` rows 5 and 7 was the wrong null. **Retracted (R1, R3).**
3. **Nothing in the repo's remaining knob list is worth +6, and several items are dead** (section 2.3): a time cap above 4.5 min, the
   call/turn/timeout caps, temperature alone, any single-knob LB contrast, and the C4 repeat as the next GPU purchase. The only live
   difference to the externally validated bundles is the **system prompt (11,228 B vs 3,240-3,993 B) together with the 28-call framing**, and
   it can only be tested as a **package**, because any single-knob effect we can imagine (<= +2 tasks) is below the LB MDE.
4. **Of the expected 4.8-task gap between our best-of-6 and a top team's best-of-17, about 3.8 tasks is true skill (theta) and about
   1.1 is selection** (stylised simulation, section 2.1). The four 0.24 teams submitted 15 times on average. A team with theta = 10
   (0.17, the field mode) and 17 submissions has P(best >= 14) = 0.53. **The 14 is a lottery on top of a field-modal bundle**, and the
   private half (plan.md:299) re-draws the lottery.
5. **Today's slot: submit the davis0178 (team DVS, LB 0.22, 11 submissions) bundle with only the two forced edits (cap 8 -> 4.5 min and
   the prompt sentence that states it).** Call it **EXT-19@4.5**. Prior mean theta 8.8 (+2.1 over our six-draw mean); P(k >= 11) = 0.015 if
   nothing transfers, 0.47 if it reaches the field mode, 0.85 if the 0.22 is real at face value. It is a package test with power 0.47-0.85
   for the effects it exists to detect, **not** a knob test. Readings are in section 4.3.
6. **I disagree with the project's slot premise in one specific way** (section 4.1): slots are indeed use-it-or-lose-it, but they are
   **substitutable with GPU hours as measurement instruments**, and a slot is the better instrument (MDE 4.5/58 = 7.8 pp, on the real
   distribution, free) than a dev-48 run (MDE 8-10/48 = 16-21 pp, 3.6-4.7 GPU-h, transfers at ~0.4x). The scarce resource is **distinct
   hypotheses with expected effect above the MDE**, not slots and not quota. Spending the slot on a knob with expected effect ~0 (sub #7)
   bought nothing; leaving it unspent would also have bought nothing; spending it on a package that can move the posterior is strictly better.
7. **No orientation number contradicts the repo.** Nuances are listed in section 1.1 (the 11,226-11,336 B prompt range is LF vs CRLF; the
   0.22 bundle's timeout is 300 s, the 240 s belongs to the rank-3 v24 bundle; "8.61 h measured" is a projection; the zip sha reproduces
   only from LF blobs).

---

## 1. Where the project stands

### 1.1 Orientation numbers checked against the repo (the repo wins; none of them lost)

| Orientation claim | Source I checked | Result |
|---|---|---|
| Six scored submissions read 4,7,6,8,8,7; variance 2.267; binomial 5.900; X2 1.921, df 5, P 0.14 | `submissions.md` rows 1,3,4,5,6,7; recomputed in `stats.txt` section C | **agrees** (mean 6.667, s2 2.267, pooled p = 40/348 = 0.11494, npq = 5.900, X2 = 1.921, P(X2 <= obs) = 0.140) |
| E0 11/48, EXP-003 9/48 | `task_results.jsonl` `resolved` field | **agrees** |
| Rank 2218, score 0.13 | leaderboard CSV 2026-10-25T21:38:25 | **agrees**: RainM4 rank 2218 of 3,758, 0.13, 7 submissions; 1,897 teams strictly ahead (50.5%), 390 tied |
| LB top is 0.24 = 14/58, four teams | same CSV | **agrees**: 4 teams at 0.24, 40 at 0.22, 188 at 0.20, 511 at 0.18, 624 at 0.17 (mode), median 0.15 |
| Remaining differences: calls 28/64, minutes 8/4.5, turns 80/96, timeout 240/300, prompt 3,240 B vs ~11.2 kB | `experiments/EXP-016-top-team-audit.md` 2a, `submission/*.yaml` | **agrees**. Prompt: 11,228 B with LF line endings (11,226 characters), 11,336 B with CRLF; EXP-018's 11,228 is the LF figure. **Nuance:** davis0178's scored bundle (the one I can reconstruct byte-exactly) has `timeout_seconds` 300, not 240, and a 3,993 B (LF) prompt, `temperature 0.2` and no `top_k`; the 240 / 3,240 B values belong to the rank-3 v24 bundle that only exists as a README table |
| ~69% of our prompt is untested insurance | EXP-018 line 181 | **agrees** |
| Sub #7 zip sha256 `99b750a0...3462` | `dist/submission.zip` in the main checkout | **agrees, with a hazard**: it reproduces only from the committed **LF** blobs (`git show HEAD:<path>`). Packing the worktree (autocrlf = true gives CRLF files) gives `b87cb430...` instead. I verified both (R9) |
| "8.61 h" for the 4.5 min cap | `submission/eval_config.yaml` comment says "measured" | **nuance**: 8.61 h = 120 x 258.3 s mean E0 `duration_s`, a projection that excludes startup, setup and grading. What was measured is that sub #1 (E0, 4.5 min) completed. The measured-input hard bound is 9.70 h (section 1.5) |
| Wall-clock is decode-bound; 79.2% of E0 tasks end on the clock | EXP-016 section 4, `forensics-E0-dev48.txt` | **agrees** |

### 1.2 Standing

Best 0.13 = 8/58. Median of the field is 0.15 = 9 tasks; the mode is 0.17 = 10 tasks (624 teams). The field has a sharp ceiling:
`stats.txt` section G gives successive tier ratios 1.22, 2.72, 4.70, 10.0 going up (624 -> 511 -> 188 -> 40 -> 4 teams at 10..14 tasks) and
**no team at 15 or more**, which is what a bounded reachable pool (~16 tasks, EXP-019) plus selection noise looks like. We are 6 tasks
from the top and 1-2 tasks from the median.

Post-hoc (labelled; not pre-registered): mean submission count by tier is 15.0 (0.24, median 17), 14.7 (0.22), 11.9 (0.20), 11.0 (0.18),
8.3 (0.17), 6.0 (0.15), 5.2 (0.13); Spearman(score, submission count) = 0.556 over 3,758 teams. This is confounded (capable teams submit
more), so it shows that **selection is available to the top teams**, not that it explains them. Our own count is 7 (one of them the blank #2).

### 1.3 The deterministic-core test

**What was asked.** `submissions.md` row 7 proposed: if the low variance of the six scores means "a largely deterministic core ... roughly the
same handful of tasks resolving on nearly every run", then the resolved sets of two existing runs should overlap heavily; "heavy overlap
supports it, near-disjoint sets refute it". The two dev-48 runs we own are E0 (11/48; 4.5 min, 45 calls, thinking 256) and EXP-003
(9/48; 8 min, 28 calls, thinking 4096). The data were present all along, in the main checkout's gitignored `runs/` and, as a count, in
`plan.md:302-306` and `submissions.md` row 3 (see R4).

**Measured** (`stats.txt` section A; N = 48 tasks present in both runs):

|  | EXP-003 resolved | EXP-003 not |
|---|---:|---:|
| **E0 resolved** | 6 | 5 |
| **E0 not** | 3 | 34 |

* both (6): `fastapi_14301, fastapi_14463, requests_6644, rich_3006, rich_3067, rich_3905`
* E0 only (5): `fastapi_13207, fastapi_13537, fastapi_14297, fastapi_14873, rich_3676`
* EXP-003 only (3): `fastapi_15589, fastapi_5624, fastapi_9753`
* neither (34): `fastapi_11355, 13786, 14262, 14360, 14448, 14459, 14512, 14583, 14605, 14609, 14953, 14962, 14964, 15030, 15280, 15661, 15800;
  httpx_3672; requests_7205, 7309, 7315, 7427; rich_3061, 3063, 3105, 3180, 3468, 3480, 3521, 3934, 3935, 3953, 4070, 4075`
* per repo (tasks / E0 / EXP-003 / union): fastapi 26/6/5/9, rich 16/4/3/4, requests 5/1/1/1, httpx 1/0/0/0.

| Statistic | Value |
|---|---|
| Expected "both" if the runs were independent | 2.06 (observed 6) |
| P(overlap >= 6), one-sided hypergeometric (= Fisher two-sided here) | **0.002275** |
| Odds ratio (Woolf 95% CI) | 13.6 (2.55 - 72.5) |
| Inter-run correlation phi = across-run ICC of the 0/1 outcome | **0.50** (task bootstrap 95% CI 0.16 - 0.78, 4,000 resamples) |
| Repeat rates | 6/11 = 0.545 of E0's resolves recur; 6/9 = 0.667 of EXP-003's |
| P(solved in EXP-003 given not solved in E0) | 3/37 = 0.081 |
| Jaccard of the resolved sets | 0.429 (independence would give ~0.11) |
| Exact McNemar on the discordant 5:3 | 0.727 (tests marginal symmetry; says nothing about overlap, see R4) |
| Chapman capture-recapture estimate of tasks this agent family can solve | 16.1 +/- 4.2 of 48 (a **lower bound**; assumes equal catchability) |
| LR test "runs are independent" | G2 = 10.35 on 1 df, P = 0.0013 |

**Finding (measured).** The runs are strongly positively dependent: task identity explains about half the variance of a 0/1 outcome (phi 0.50,
wide CI because n = 48). The dependence is **intermediate**: 8 of the 14 distinct solved tasks were solved by only one run.

**What the table cannot separate (measured, `stats.txt` section B).** A model with a sharp always-solved core of c tasks plus an independent
periphery fits the table for c = 2 to 6 of 48 (profile 95%), best at c = 5-6 with periphery rates 0.125 (E0) and 0.08 (EXP-003). A smooth
Beta-distributed difficulty gives the same four cell probabilities. The 2x2 cannot tell a sharp core from the upper tail of a continuum.

**Reading of the hypothesis (verdict).**
* "Task difficulty is heterogeneous and some tasks are repeatedly solved": **supported** (p = 0.0023).
* "The same handful of tasks resolve on **nearly every run**": **refuted** at 55-67% repeat rate; even the best core model leaves ~5 of E0's 11
  resolves and ~3 of EXP-003's as lottery.
* "Underdispersion of the six scores is the signature of a deterministic core": **refuted as an inference** (next paragraph).
* "+6 needs a capability change rather than a setting": **not supported by this test.** A periphery that is ~35% of resolves and spans most
  tasks at 8-12% per-run solve probability is exactly where a setting that moves per-task probability can add tasks. The test is silent on
  how far settings can move it; it does not say they cannot.

**Why the underdispersion is not evidence of a core (measured, `stats.txt` section C).** For a fixed task set the count is Poisson-binomial,
variance sum p_i(1-p_i) = n mu (1-mu)(1-rho), **below** the binomial n mu (1-mu) whenever tasks differ. Simulated (20,000 reps each), the
sample variance of six runs on one task set with p_i ~ Beta(mean 0.1149, ICC rho):

| rho | E[s2] | P(s2 <= 2.267) | P(s2 >= 5.9) |
|---:|---:|---:|---:|
| 0.00 (binomial) | 5.89 | 0.156 | 0.403 |
| 0.25 | 4.43 | 0.252 | 0.235 |
| 0.40 | 3.55 | 0.362 | 0.139 |
| **0.50 (measured phi)** | **2.94** | **0.471** | 0.078 |
| 0.60 | 2.33 | 0.603 | 0.034 |
| 0.75 | 1.48 | 0.830 | 0.004 |

The "P = 0.14 low tail" came from comparing six reruns of a fixed task set with a homogeneous binomial. Post-hoc consistency check: a sharp-core
model moment-matched to the six LB scores (mean 6.667, variance 2.267) needs c = 4-5 always-solved tasks (c = 4 gives variance 2.54, c = 5
gives 1.61), i.e. two-thirds of a typical LB run is "core" and one-third lottery, the same split as dev-48 from independent data. That is a
consistency check, not a second proof: LB variance cannot separate a core from smooth heterogeneity either.

### 1.4 Resolution of the instruments (all from `stats.txt`)

* **LB, one new draw against our six-draw mean (same 58 tasks):** SE = sqrt(2.267 x (1 + 1/6)) = 1.63; MDE (two-sided .05, power .80)
  = **4.55 tasks**; one-sided **4.04** (this is the repo's "~4"). If the new config also changes the task-level probability vector, the marginal
  model gives 5.1 - 7.2 (rho 0.65 - 0.30). **I use 4.5, and treat 5-6 as the honest range.**
* **LB, n draws of each of two configs:** SE = sqrt(2.267 (1/n + 1/m)); MDE 4.5 (1 vs 6 baseline), 3.4 (2 vs 6), 2.7 (4 vs 6), 2.4 (6 vs 6),
  2.2 (9 vs 6). Resolving a 2-task effect costs about 9 slots per arm.
* **dev-48, single paired run, exact McNemar, arm A at 11/48:** power 0.05 / 0.09 / 0.17 / 0.36 / 0.59 / 0.80 at a true gain of 2 / 3 / 4 / 6 / 8 / 10
  tasks. **MDE ~ 10 tasks of 48 (21 pp)**; the normal approximation (7.8 tasks at phi 0.5) is optimistic. dev-48 -> LB transfer has been ~0.4x.
* **Empty-patch rate is not a tight metric** at n = 48 (it is 19/48 = 39.6%, Wilson 95% 0.27 - 0.54; inter-run phi 0.42; paired MDE 21 pp). R5.

### 1.5 Time model (cited from EXP-020 section 2.3 for the inputs; recomputed in `stats.txt` F2)

Hard bound = 120 x (cap + 3.3 s setup + 14.0 s grading) + 461.8 s startup. It is 8.70 h at 4.0 min, **9.70 h at 4.5**, 10.70 h at 5.0, 11.70 h
at 5.5, 12.0 h at 5.65 and 16.70 h at 8.0. The packer's gate prices setup at 60 s (3.5x the measured 17.3 s), which is why 5.0 min reads
12.00 h and is rejected although the measured-input bound is 10.70 h. The **largest cap with a hard bound <= 11.0 h is 5.15 min.**
Pooled seconds per tool call: E0 (thinking 256) **8.2 s**, EXP-003 (thinking 4096) **14.0 s**. So a 270 s cap buys ~33 calls at thinking
256 and only **~19 calls at thinking 4096** (an 8 min cap would buy ~34). Resolve timing: of the 20 resolves in the two runs, **1** has its last
`edit_file`/`write_file` after 270 s (`fastapi_15589`, EXP-003, 414 s); E0 loses 0 of 11, EXP-003 1 of 9.

---

## 2. What could be worth +6 tasks, and what cannot

### 2.1 What the 6-task gap is made of

Stylised model (`stats.txt` D2; every submission of a team has the same theta, tasks have rho = 0.50 Beta heterogeneity, E[max of N graded draws]):

| theta (share) | N = 6 | N = 17 | N = 44 | P(max >= 14) at N = 17 |
|---|---:|---:|---:|---:|
| 6.67 (ours, 0.115) | 8.86 | 9.86 | 10.56 | 0.00 |
| 8.0 | 10.37 | 11.40 | 12.17 | 0.04 |
| 9.0 | 11.50 | 12.55 | 13.39 | 0.19 |
| **10.0 (field mode, 0.172)** | 12.63 | **13.69** | 14.57 | **0.53** |
| 11.0 | 13.70 | 14.87 | 15.70 | 0.88 |

Our expected best-of-6 is 8.86 (we observed 8). A top team at theta = 10 with 17 submissions expects 13.69. The expected gap is 4.8: **3.8 from
theta (6.67 -> 10 at N = 6) and 1.1 from selection (6 -> 17 draws)**. The observed 6-task gap adds our unlucky and their lucky tail. Two
consequences: (a) the realistic target is **theta ~ 10, i.e. +3.3**, not +6; (b) the extra ~2.7 tasks of the "+6" are selection, which free slots
can buy us for board position (N = 44 at theta 6.67 expects 10.6) but which the private half (~62 tasks; plan.md:299) will not honour.
**Expected final standing depends on theta only.**

### 2.2 The differences from the externally validated LB-0.24 bundle, priced

Rank-3 v24 (`muhammedidris28`, LB 0.24) from EXP-016 2a; davis0178 (team DVS, rank 18, LB 0.22, 11 submissions) from the notebook I
reconstructed byte-exactly (its four files' sha256, re-serialised with CRLF, all match the notebook's own recorded hashes; I did **not** and
cannot verify that this archive is the one that scored 0.22, only that the author says so and that DVS's best on the board is 0.22).

| Knob | Theirs | Ours (#7) | My price | Verdict |
|---|---|---|---|---|
| `max_tool_calls` | 28 | 64 | At thinking 4096 and a 270 s cap the agent makes ~19 calls (14.0 s/call), so neither 28 nor 64 binds; the number acts only through the prompt text ("You have 28 tool calls", "edit by call 12"). EXP-003's "28-call-capped cohort resolved 0 of 20" selects the long tasks and is not a causal estimate. | **Not a lever on its own.** Part of the package. |
| `max_time_minutes` | 8 | 4.5, gated | 1 of 20 resolves comes after 270 s, so 4.5 -> 8 buys <= ~5% of resolves, <= ~0.4 LB task at theta 8-9. The 8 min cap is also unreachable: hard bound 16.7 h; EXP-003 (mean 340 s) timed out as sub #2. 5.0 min is safe by the measured model (10.70 h) and is worth <= 0.4. | **Dead as a +6 source.** 5.0 min is a free <= 0.4 and should come from recalibrating the gate (review), not an override. |
| `max_turns` | 80 | 96 | Turns >= calls in both; non-binding. | **Dead.** |
| `timeout_seconds` | 240 (v24), 300 (davis) | 300 | Per-command timeout; both 240 and 300 bundles score >= 13. | **Dead.** |
| system prompt | 3,240 B (v24); 3,993 B LF (davis) | 11,228 B LF | ~69% untested insurance (EXP-018). The only difference that changes what the agent does on every step. | **The one live difference, testable only inside a package** (section 4). Expected single effect <= +2, below MDE. |
| `temperature` / `top_k` (not in the orientation list) | v24: 1.0 / 64; davis: **0.2 / absent** | 1.0 / 64 | Two bundles that differ on temperature both reach >= 13. EXP-016 2b's v19 -> v24 (temperature only) +3 tasks is inside their own replicate noise. | **Dead as a lever.** |

**EXP-016 2b's caveat is stronger than it reads.** Their v17 scored 0.17 and 0.13 on identical configs, and v24 has no local validation run. Under D2,
theta = 9 with 17 submissions already has E[max] = 12.55 and P(>= 14) = 0.19; theta = 10 has 0.53. So **0.24 is fully compatible with a true
0.15-0.17 bundle**, and the 0.22 of a team with 11 submissions (DVS) is compatible with theta ~ 8-10. The right prior for "adopt the public bundle"
is therefore theta 8-10, not 12.8.

### 2.3 Directions I call dead (for the purpose of closing a 6-task gap)

1. **Raising the time cap above 4.5 min.** Priced at <= 0.4 tasks (1/20 late resolves); the 8 min cap is infeasible. Recalibrating the gate to allow
   5.0 min is fine housekeeping, not a direction.
2. **`max_tool_calls`, `max_turns`, `timeout_seconds` on their own.** Non-binding at the actual time budget (19 calls at thinking 4096).
3. **Temperature / top_k on their own.** See above.
4. **Any single-knob LB contrast.** Needs ~9 slots per arm for a 2-task effect; we have ~38 slots total.
5. **Resolve-count screening of sub-10-task effects on dev-48.** MDE ~10 tasks of 48 per run; transfer ~0.4x.
6. **The C4 E0 repeat (7.2 GPU-h) as "the next purchase".** After the overlap result it adds a tighter phi (CI 0.16-0.78 -> maybe +/-0.2) and
   no decision depends on it. If it is wanted, it belongs to the paper track (Nov 12), not the LB programme.
7. **LoRA (today is the plan's go/no-go gate, plan.md section 1.2): no-go.** The only external datum is strongly negative (rank-3's
   adapter 18/46 -> 13/46 -> 9/46 locally, 54.3% empty patches, EXP-016 2c), the open Q4 (zeroing status) means a trained adapter could not even
   be trusted to load, and any adapter effect smaller than ~4 tasks cannot be read from the LB. I cannot put a probability on success from data in
   this repo; I would not bet 38 days on it.
8. **Multi-agent / delegation.** Same-model delegation hurt in the one reference the plan cites (12/18 -> 6/18, secondhand); nothing here contradicts it.

### 2.4 What is live

* **Package lineage swap** (prompt + 28-call framing + sampling of a field-modal bundle). Prior effect +2.1 (range 0 to +6). Measurable only at
  >= 4.5; section 4.
* **Measuring the native bundle's wall-clock** (8 min cap) on dev-48: precise (+/-0.4 h on the 120-task projection) and it decides whether a
  gate override for the native bundle could ever be justified.
* **Call-matching the time budget**: with thinking 4096 our 270 s buys 19 calls against the 28 the external prompts assume; a thinking budget of
  ~1024-1536 restores ~27 calls. Mechanistic, not yet measured; a candidate for slot 2 after the first reading.

---

## 3. Ranked experiment programme (to Dec 2: 39 slots including today; ~163 L4x4-h if the 30 h/week quota holds)

Pricing: GPU-h are L4x4-hours (a dev-48 run at 258 s/task is 3.58 h; a run at 340 s/task scales to ~4.7 h, unmeasured for this bundle).
"Resolvable" means distinguishable from zero at the stated power.

| # | Item | GPU-h | Slots | Power / MDE | Resolvable at our MDE? | Decision it drives |
|--:|---|---:|---:|---|---|---|
| 1 | **EXT-19@4.5 on the LB (today)** | 0 | 1 | P(k >= 11): 0.015 if no transfer, 0.145 if +1.8, 0.47 if field mode, 0.85 if face value | **Yes, but only for large effects** (>= ~4) | adopt or retire the public-bundle lineage |
| 2 | Native EXT-19 (8 min cap) on dev-48, **duration and call counts, not resolves** | ~4.7 | 0 | duration: SE ~ 80 s/sqrt(48) = 12 s per task, +/-0.4 h on the projection; resolves: MDE ~10/48 | **Duration yes; resolves no** | whether a gate override for the native bundle is defensible (needs 120 x mean + 17 s + 0.13 h <= ~10.5 h, i.e. mean <= ~310 s) |
| 3 | Gate recalibration (measured-input bound, cap <= 5.15 min at 11.0 h) | 0 | 0 | worth <= +0.4 tasks | **No** | free housekeeping; needs review, not an override |
| 4 | **Slot 2, chosen by the reading of #1** (table below) | 0 | 1 | single draw, MDE 4.5 | only if package-sized | see tree |
| 5 | Call-matched variant of #1 (thinking ~1024-1536) on dev-48 for calls/min and empty-patch rate | ~3.6 | 0 | empty-patch paired MDE 21 pp | mechanism yes, resolves no | feeds slot 2 or 3 |
| 6 | Native-8-min LB submission with a justified override | 0 | 1 | package-sized effect | yes if >= 4.5 | only if #2 supports it; accepts a blank as the cost |
| 7 | Finals reserve: 2 candidates x >= 3 draws each (plan.md section 8: "at least 2 clean LB runs") | 0 | 8 (Nov 22 - Dec 1) | n = 3 vs 3: MDE 3.2 | partly | choose the two finals |
| 8 | Paper track (due Nov 12): C4 E0 repeat pair, E1-E4 ablations with per-task CSVs | ~7 + ~15 | 0 | n/a (descriptive) | n/a | the writeup; also the only place the noise floor is a deliverable |
| 9 | LoRA | 0 GPU (TPU quota) | 0 | unreadable below +4 | no | **no-go** (2.3 item 7) |

Slot ledger: 39 total = 1 today + 8 finals reserve + 30 flexible. The flexible slots should be spent as an **adaptive tree** (one reading per day, each
chosen by the last), because a screening design of 30 independent single-knob contrasts has no power. Slot 2 by reading of #1:

| Reading of #1 | Slot 2 | Why |
|---|---|---|
| R-A (k >= 11) | the **same bundle again, unchanged** | one extra draw halves the variance of theta; regression to the mean is the main threat to R-A; no LB decomposition |
| R-B (k = 9-10) | call-matched variant (#5) if its dev-48 process metrics look better, else the same bundle again | LR(H1:H0) is only 2.8; do not adopt |
| R-C (k <= 8) | native-8-min (#6) **only if** #2 supports it; otherwise stop package-chasing and spend flexible slots on board-position draws of the best two bundles | H2 (face value) is dead at LR 0.03; H1 is 5:1 against |
| R-D (blank) | repeat the cap-only config (sub #7) | a blank falsifies the hard-bound model and nothing else is trustworthy until it is understood |

---

## 4. Today's slot

### 4.0 Clock

The slot resets at 23:59 UTC. The candidate must be built, validated, packed and uploaded inside that window; Appendix B and the handback carry
the exact commands. If the window is missed, nothing in this document changes except which day the draw lands on.

### 4.1 Argument about the slot premise (stated explicitly, as asked)

The project premise (EXP-020 line 11; submissions.md row 7): "daily slots are use-it-or-lose-it", "GPU quota is the scarce resource, not slots", and
by implication that slots and GPU are not exchangeable.

* **Use-it-or-lose-it: agree.** A slot cannot be banked.
* **Non-fungible with GPU quota: disagree, as a statement about instruments.** A submission does not draw on our 30 L4x4-h/week (it runs on the
  grader), so in resources they are separate. But both are ways to learn whether a config is better, and per unit of information a slot is the
  better instrument: one draw on the real test distribution has SD 1.5 tasks (MDE 4.5 of 58 = 7.8 pp); one dev-48 run costs 3.6-4.7 GPU-h, has
  MDE ~10 of 48 (21 pp), and has transferred at ~0.4x. So **quota is not scarce relative to what it can resolve** (163 h buys ~45 dev-48 runs, none
  of which can resolve an effect under 10 tasks), and **slots are not scarce either** (39). What is scarce is **distinct hypotheses whose expected
  effect exceeds the MDE**. The repo has had one such candidate (the public-bundle lineage) and has spent six of seven slots on knobs priced at
  <= 2 tasks.
* **The "free change because the slot expires" rationale (sub #7) bought nothing**: expected effect ~0 against MDE 4, reading pre-registered as
  "uninformative whatever happens". Because the board shows each team's **best** score, a bad draw costs nothing displayed, so slot content
  should be **high-variance and large-mean-shift**, not the most conservative thing that can be built in seven minutes. The conservative posture is
  correct for the **two finals**, not for exploration slots.
* **Against leaving the slot unspent:** it would be right only if the submission could mislead, e.g. a lucky 11 read as proof. The pre-registered
  readings below carry the false-positive rate (0.015 under no transfer) and the posterior, which is the guard. A timeout costs this slot and
  nothing else (R10).

### 4.2 The candidate: EXT-19@4.5

**Base.** `davis0178/gemma-4-agent-baseline` notebook ("Historical public LB 0.22", `BUILD_MODE = "reproduce"`, `ORIGINAL_ARCHIVE_SHA256 =
4ff3ee29c06394861804030519ec57cbf99114d3f1ed36640deb175093d6bd00`). Read as JSON; its four files recovered with `ast.literal_eval` (the notebook is
never executed) by `tools/exp022_make_candidate.py`, which re-serialises each with CRLF and refuses to proceed unless sha256 matches the notebook's
recorded value (all four matched during analysis). Licence/attribution of the notebook text is **unchecked** (flagged in section 6).

**Exact values** (candidate vs sub #7):

| File | Key | Sub #7 | **EXT-19@4.5** |
|---|---|---:|---:|
| `eval_config.yaml` | `timeout_seconds` | 300 | **300** |
| | `max_tool_calls` | 64 | **28** |
| | `max_time_minutes` | 4.5 | **4.5** (davis native 8; forced edit E1) |
| | `max_turns` | 96 | **80** |
| `configs/sampling.yaml` | `temperature` | 1.0 | **0.2** |
| | `top_p` | 0.95 | **0.95** |
| | `top_k` | 64 | **absent** |
| | `max_output_tokens` | 8192 | **8192** |
| | `thinking_config.thinking_budget` / `include_thoughts` | 4096 / true | **4096 / true** |
| `agent.yaml` | `name` | `swe_coder` | **`swe_agent`** |
| | `model` | `gemma-4-31b-it-qat-w4a16-ct` | **same** |
| | `tools` | run_command, read_file, edit_file, write_file, get_status, submit_patch | **same six, same order** |
| | `instruction` | `!include prompts/swe_coder.md` (11,228 B LF) | **`!include prompts/system.md`** (3,993 B LF before edit E2; ~3,995 B after) |
| | `generate_content_config` | `!include configs/sampling.yaml` | **same** |

**Declared edits to the source files (the complete diff against the notebook's bytes; each must match exactly once):**

```
E1  eval_config.yaml     -  max_time_minutes: 8        +  max_time_minutes: 4.5
E2  prompts/system.md    -  You have 28 tool calls and 8 minutes.   +  You have 28 tool calls and 4.5 minutes.
E3  (fallback only, applied iff the validator rejects it)
    prompts/system.md    -  - FastAPI documentation tasks: edit the executable example under `docs_src/`.   (line deleted)
```

E1 is forced by the packer's gate (`120 x (cap + 1.0) h <= 11.0 h` pins the cap at 4.5); E2 keeps the stated budget true. E3 exists because the
validator enforces repo-agnostic prompts (`tools/submission_rules.py: PUBLIC_REPO_WORDS`, plan section 8.2) and the line names FastAPI; it is
declared now so that dropping it is not a post-hoc choice. No other change is made. Line endings are LF (repo convention); the CRLF sha256 values of
the source are what was verified.

**Handicap, stated up front.** The replica gets 4.5 min where its authors had 8 and runs at ~14 s/call, so it will get ~19 of its nominal 28 calls.
The price of the cap on resolves is small (1/20 late resolves), but the call count is not measured for this prompt. The test is therefore of "this
bundle at our time budget", not "this bundle".

### 4.3 Pre-registered readings (written and committed before the candidate was built)

**Mapping.** Score = floor(k/58 x 100)/100: k = 7 -> 0.12, 8 -> 0.13, 9 -> 0.15, 10 -> 0.17, 11 -> 0.18, 12 -> 0.20, 13 -> 0.22.

**Hypotheses on theta (expected tasks on the 58 public tasks) and my prior, stated before the draw:**

| H | theta | Meaning | Prior |
|---|---:|---|---:|
| H0 | 6.67 | no transfer; same as our six-draw mean | 0.35 |
| H-low | 8.5 | bundle is worth ~+1.8 (cap handicap and partial noise in the public score) | 0.30 |
| H1 | 10.4 | reaches the field mode (0.18) | 0.25 |
| H2 | 12.8 | the 0.22 is real at face value | 0.10 |

Prior mean theta = 8.76 (**expected effect +2.1 tasks** over our mean). Prior-predictive: P(k <= 8) = 0.501, P(9-10) = 0.247, P(k >= 11) = 0.252.
Probabilities of each outcome are Poisson-binomial with p_i ~ Beta (rho = 0.50), 150 task-vector draws per theta (`stats.txt` section D; the values for
rho = 0.30 and 0.65 are in the same file and move P(k >= 11 | H0) between 0.034 and 0.006).

| Outcome | P under H0 | H-low | H1 | H2 | LR H1:H0 | LR H2:H0 |
|---|---:|---:|---:|---:|---:|---:|
| **R-A: k >= 11** (>= 0.18) | **0.015** | 0.145 | 0.474 | 0.848 | 30.8 | 55.2 |
| **R-B: k = 9-10** (0.15, 0.17) | 0.125 | 0.347 | 0.347 | 0.127 | 2.8 | 1.0 |
| **R-C: k <= 8** (<= 0.13) | 0.860 | 0.508 | 0.180 | 0.025 | 0.21 | 0.03 |
| **R-D: blank** (Notebook Timeout) | ~0.02 | | | | | |

Posterior if R-A: H0 0.02, H-low 0.17, H1 0.47, H2 0.34. Posterior if R-C: H0 0.60, H-low 0.30, H1 0.09, H2 0.00.

**Readings (fixed now; not to be revised after the score):**

* **R-A, 0.18 or higher.** The public-bundle lineage reaches or exceeds the field mode at our time budget. False-positive rate 1.5% (0.6-3.4%
  across rho). **Action:** adopt as the base for the flexible slots; slot 2 is this bundle unchanged (regression to the mean is the main threat);
  start item 2 of the programme. **Not concluded:** which of prompt / temperature / call cap did it.
* **R-B, 0.15 or 0.17.** Inconclusive, mildly favouring a modest gain (LR 2.8 for H1, 1.0 for H2). **Not adopted, not rejected.** 9 or 10 will not be
  described as an improvement.
* **R-C, 0.13 or lower.** The bundle at 4.5 min does **not** show a >= 4-task gain: H2 is dead (LR 0.03), H1 is 5:1 against, H0 and H-low survive.
  **Not concluded:** that the lineage is worthless (the 4.5 min cap is a confound; H-low is still 30% after a miss). Action per section 3.
* **R-D, blank.** The cap-only hard bound (9.70 h at 4.5 min; held for six returned scores) is falsified; stop all submissions that rely on it
  until it is understood. This would be the one genuinely new risk of the candidate; a shorter prompt and a smaller call cap cannot lengthen a
  capped task.
* **Also fixed now:** a score returning at all is a seventh confirmation of the 4.5 min path; k = 11 is not proof (P(k >= 11 | H-low) = 0.145);
  no cross-submission contrast beyond this table will be read from a single draw.

**Power, plainly.** If the effect is real and large (H2) the slot detects it with probability 0.85; if it is the field mode (H1) with 0.47; if it is
+1.8 (H-low) with 0.145. A miss therefore cannot retire a moderate gain; a hit is strong evidence for a large one.

---

## 5. What the project got wrong (self-corrections, with evidence)

* **R1. "Largely deterministic core" from underdispersion** (`submissions.md` row 7). Wrong null: a fixed task set is Poisson-binomial, with variance
  below binomial whenever tasks differ. At the measured phi 0.50, P(s2 <= 2.267) = 0.47. The overlap test the row asked for does show dependence
  (p = 0.0023), but not "nearly every run" (55-67% repeat). Section 1.3.
* **R2. "Non-negative by construction"** (row 7). Already partly retracted in the row (the call count is an input to planning). Additionally,
  under thinking 4096 the 270 s cap binds at ~19 calls (14.0 s/call, EXP-003 trace data), so the 45 -> 64 call ceiling was inert in both
  directions; the "frees the call-capped tail" premise came from E0's thinking-256 regime (median 32 calls, 1/48 at the cap) and was not
  recomputed for the regime that sub #6 had just created. (Caveat: the 14.0 s/call was measured on an 8 min / 28-call config and applied to
  sub #6/#7 by assumption.)
* **R3. The dispersion test as evidence that "no configuration we have built is distinguishable from any other"** (rows 5, 7). Besides the wrong
  null, non-rejection at an MDE of 4.5 cannot support equivalence; the six means spanning 4 tasks equals the MDE.
* **R4. The overlap data were already in the repo and mis-read.** `plan.md:302-306` and `submissions.md` row 3 report "6 solved by both of 14
  distinct ... McNemar p = 0.73 ... per-task outcomes churn by more than half". McNemar tests whether the two marginals differ (5 vs 3), not whether
  the sets overlap; the correct statistic is Fisher p = 0.0023 / phi 0.50. "Churn" and "core" were both over-readings of the same 2x2, and row 7
  then listed this as the "highest-value unspent analysis".
* **R5. "High-prevalence process metrics that have tight CIs" such as empty-patch rate** (`plan.md:307-311`). 19/48 has Wilson 95% 0.27-0.54; the
  paired MDE is 21 pp, larger than the resolve rate's 16 pp (normal approximation), and the inter-run phi is 0.42, not higher than the resolve
  outcome's 0.50.
* **R6. "The only powered knob left requires overriding the budget gate"** (row 7). The knob (time above 4.5) is weak (1/20 late resolves,
  <= 0.4 task), and the gate that pins it prices setup at 60 s against a measured 17.3 s; the project's own 9.70 h bound (EXP-020 2.3) allows
  5.15 min at 11.0 h. The remedy is a reviewed gate recalibration, not an override and not a narrative that "nothing is left".
* **R7. "4.5 = 8.61 h (measured; E0 survived)"** (`submission/eval_config.yaml`). 8.61 h = 120 x 258.3 s is a projection from dev-48 means that excludes
  startup, setup and grading. What was measured is that sub #1 completed.
* **R8. Sub #6's thinking swing silently traded breadth for depth.** At 270 s, thinking 256 gives ~33 calls and thinking 4096 gives ~19 (8.2 vs
  14.0 s/call, `stats.txt` F2), while the external prompts assume 28. This was not priced when the swing was chosen "as the untried remainder of the
  only externally validated config", and is a candidate explanation for why #5, #6, #7 are indistinguishable. Hypothesis, not finding.
* **R9. Reproducibility of the pinned sha.** Row 7's `99b750a0...` reproduces only from the committed LF blobs; the autocrlf worktree packs to
  `b87cb430...`. Build submissions from `git show <commit>:<path>` blobs or from LF files written directly (as the candidate is).
* **R10. Timeout aversion priced as catastrophe for exploration slots.** Row 2 records "the slot was spent for zero LB signal" and the repo then
  treats a blank as the failure to avoid at all cost. The board shows the best score, so a blank costs one slot; the gate is the right instrument for
  the **finals**, not for every exploration slot.
* **R11. dev-48 composition.** `plan.md:276` says "fastapi 22 / rich 16 / requests 9 / httpx 1"; the task list of both runs is **26 / 16 / 5 / 1**
  (`stats.txt` section A). With fastapi 54% of dev-48 the FastAPI-specific line in the candidate's prompt matters more here than it may on the hidden set.

---

## 6. Provenance and limits

* **Measured by me this session (scripts committed):** everything labelled `stats.txt`; byte-exact reconstruction of the davis0178 bundle and its
  hash check; sub #7's sha from LF blobs and from the CRLF worktree; the leaderboard tier table.
* **Quoted from other repo documents, not re-measured:** startup 461.8 s, setup 3.3 s, grading 14.0 s (EXP-020 2.3); EXP-016's rank-3 table and v19/v24 diff;
  EXP-018's 69% and 11,228 B; the field-structure estimate of ~16 reachable tasks (EXP-019).
* **Models, not measurements:** the Beta-heterogeneity rho = 0.50 for new draws (taken from a dev-48 cross-config phi with a wide CI); the
  priors in section 4.3 (opinions, written before the draw); the winner's-curse table (every submission of a team has equal theta).
* **Unverified:** that davis0178's archive hash is the submission that scored 0.22; whether the notebook's text may be reused (licence not checked);
  how many calls the replica actually makes at 4.5 min.
* **Literature (recalled from memory, not fetched this session; none of it changes a ranking above):** SWE-agent's agent-computer-interface result
  (tool design matters), Agentless (localise, repair, validate; relies on sampling many patches, which a 270 s / 30 tok/s budget cannot afford),
  mini-SWE-agent (a bash-only loop is a strong baseline), SWE-Gym / SWE-smith (trajectory data for fine-tuning; relevant only to the LoRA track
  that I recommend against). The competition-specific evidence above (public bundles, the board) outweighs these.
* **Not done:** no Kaggle push, no submission, nothing under `submission/` modified (the candidate lives in `experiments/EXP-022/candidate/`).

---

## Appendix A. Files

* `tools/exp022_stats.py`, `experiments/EXP-022/stats.txt` (seed 22)
* `tools/exp022_make_candidate.py`, `experiments/EXP-022/candidate/` (built after the pre-registration commit)

## Appendix B. Build record

*(appended after the candidate was built; see below)*
