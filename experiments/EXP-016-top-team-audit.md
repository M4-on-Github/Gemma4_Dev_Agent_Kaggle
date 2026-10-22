# EXP-016 — Top-team configuration audit, and the two measurements that came out of it

**Date:** 2026-10-22. **GPU cost: zero.** Read-only Kaggle CLI queries plus analysis of runs we already have.
**Status:** findings only. The submission these findings motivate is `EXP-017-submission5-temp-and-prompt.md`.

---

## 0. Why this was run

`EXP-012` concluded that the gap to the top of the leaderboard was "budget + prompt" and queued EXP-013/014/015
to close it. Before spending quota on those, we audited what the highest-scoring teams actually ship. Two of
EXP-012's premises turned out to be wrong, and two new zero-GPU measurements reversed its central
recommendation.

---

## 1. Corrections to EXP-012 and `submissions.md`

**1a. Our standing is 0.12 = 7/58 tasks, rank 2322 of 3470, ~33rd percentile.** Not 0.10 = 6 tasks / 25th
percentile. The leaderboard shows each team's **best** submission, and submission #2 (EXP-005) scored 0.12;
submission #4's 0.10 did not replace it. Our LB row is team `RainM4`, user `rainm4`. Every percentile and
"tasks behind" figure in EXP-012 is computed off the wrong row.

**1b. The notebook EXP-012 is built on is not a 0.24 config.** `honghanhhh/gemma-4-baseline-lb-0-24`
("Gemma 4 Baseline | LB 0.24") belongs to a team at **0.18, rank 232**. Verified by joining
`TeamMemberUserNames` in the leaderboard CSV. `hitarthjain0`'s "What Took LB 0.12 to 0.24" is also **0.18,
rank 320**. EXP-012's sentence "the 0.24 ceiling config is a public notebook running the same model and the
same nine tools as ours" is false as written. The title advertises a score the author did not hold.

**1c. K = 58 is now uniquely confirmed**, not merely consistent. Of the 111 values of K in 10-200 whose
truncation lattice `floor(k/K*100)/100` covers all 15 observed leaderboard scores, only K = 58 predicts
*exactly* those 15 and no others; every other candidate predicts 5-10 scores (0.02, 0.04, 0.07, 0.09, 0.11,
0.14, 0.16, 0.19, 0.21, 0.23) that none of 3470 teams ever hit. Independently corroborated by the rank-3
team's own README: "58 public tasks; one task = 0.017".

---

## 2. What the top teams actually ship

Four teams hold 0.24 = 14/58: `samson8`, `weiyun22021`/`yoruet`/`yunmeng6`, `chenshengabc`, and
`muhammedidris28` (rank 3). Only `muhammedidris28` published competition work — and published all of it,
Apache-2.0, as two datasets (`gemma4-agent-runs`, `locbench-129`) plus three zero-vote notebooks. The datasets
accompany two **paper-track** submissions (deadline Nov 12), which is why they exist: reproducible artifacts
are that track's deliverable, not a leak. They withheld transcripts, patches and snapshots — you get
configurations and outcomes, never trajectories.

### 2a. Their v24 (LB 0.24) vs ours, as submitted before today

| Knob | v24 (0.24) | `flexonafft` (0.22, r19) | Ours (E0 to sub #4) |
|---|---|---|---|
| tools | 6 | 6 | **9** (3 graph tools) |
| `temperature` | **1.0** | 1.0 | **0.2** |
| `top_p` / `top_k` | 0.95 / 64 | 0.95 / 64 | 0.95 / 64 — already matched |
| `thinking_budget` | 4096 | ~4096 | **256** |
| `max_output_tokens` | 8192 | 6144 | **4096** |
| `max_tool_calls` | 28 | 28 | 45 |
| `max_time_minutes` | 8 | 7 | **4.0** |
| `max_turns` | 80 | — | 70 |
| `timeout_seconds` | 240 | — | 300 |
| system prompt | 3,240 B | — | 11,175 B |

**Our sampling config was already byte-identical to theirs except `temperature`.** `top_p: 0.95` and
`top_k: 64` match exactly. Our own comment on that line read "scorer default is 1.0; E4 A/Bs 0.2 vs 1.0" — we
deliberately moved off the harness default to 0.2, planned the A/B as E4, and never ran it.

### 2b. The v19 to v24 diff is temperature and nothing else

`diff -r agents/v19 agents/v24`, in full:

```
diff -r v19/configs/sampling.yaml v24/configs/sampling.yaml
1c1
< temperature: 0.2
---
> temperature: 1.0
2a3
> top_k: 64
```

Same prompt (md5 `b0138cb6...` shared across v19/v22b/v24/v25), same tools, same budgets, same model. Their
published LB scores: **v19 = 0.18, v24 = 0.24.** Two caveats that matter: v24 has **no local validation run**
in `runs.jsonl`, and +3 tasks is inside their own replicate noise — their **v17 scored 0.17 and 0.13 on
identical configs**.

### 2c. Their LoRA adapter lost ~11 points locally

`v20_base` 18/46 (39.1%) → `v20`, identical but `adapter: distill`, 13/46 (28.3%) → `v21` 9/46 (19.6%) with a
54.3% empty-patch rate. This lands directly on `plan.md` section 6.2's LoRA track as a strong external negative.

### 2d. Their winning prompt confirms four of our five queued EXP-013 items

"Edit by tool call 12"; one targeted `git grep -n "TOKEN" -- '*.py' | head -20`; `read_file` at most 120 lines
with explicit ranges; at most one focused check. It also independently encodes the `verification.py:297`
mechanism we derived ourselves — "a correct source diff scores the task even if your local test was red" — and
bans concluding the code is already correct, forbids test-file edits, and puts scratch files in `/tmp`.
It **contradicts** our whole-file rule: "Never run bare `pytest`, `pytest .`".

### 2e. The context trap they document does not reach us

Their `eval_config.yaml` warns that prompt + `max_output_tokens` > 32,768 ends a task with an empty patch
(forum #744692, which we have not read directly). Checked against all 96 E0 traces: peak `prompt_tokens`
**16,991 = 51.9%** of the window, **zero** tasks over the 28,672 trip threshold, and zero would cross it even
at `max_output_tokens: 8192`. **Our 39.6% empty-patch rate is behavioural, not overflow**, and raising output
tokens carries no overflow risk.

---

## 3. NEW MEASUREMENT: the section 5.8 gate formula is accurate at our cap, not 30% pessimistic

`plan.md` section 5.8 computes worst case as `cap x 120` and flags the formula as the defect, citing EXP-003's
5.71 min median under an 8-min cap as evidence it overstates by ~30%. Re-derived from per-task `task_wall_s`:

| | E0 (cap 4.5 min) | EXP-003 (cap 8.0 min) |
|---|---|---|
| mean per-task wall | 258.3 s | 340.1 s |
| median | 273.8 s | 342.6 s |
| **tasks at/over the cap** | **38 / 48 = 79.2%** | 12 / 48 = 25.0% |
| `cap x 120` formula | 9.00 h | 16.00 h |
| **projected actual (mean x 120)** | **8.61 h = 96% of formula** | 11.34 h = 71% of formula |

The ~30% slack is real **only at an 8-minute cap**, where the 28-call cap binds first. At our own 4.0-4.5 min
cap the agent saturates on 79.2% of tasks, so `cap x 120` is within 4% of the truth. **The formula is not the
defect at the cap we actually run.**

Projected actual time if the cap were raised, holding everything else:

| new cap | projected actual |
|---|---|
| 5.0 min | 9.40 h |
| 6.0 min | **10.99 h** — exactly on the 11 h gate |
| 7.0 min | **12.57 h — over the 12 h hard limit** |
| 8.0 min | 14.15 h |

And the calibration point: submission #2 ran the 8 min / 28 call config, projected **11.34 h**, and died of
Notebook Timeout. So a projection of 11.34 h is already fatal — fixed notebook overhead (wheel installs, vLLM
server start, model load) is outside `task_wall_s` and unmeasured. **Treat ~10.5 h projected actual as the
real ceiling.**

**Consequence: EXP-015 is dead as specified.** We cannot adopt the top teams' 7-8 min per-task budget. Their
8 min is not a time budget, it is a safety net — their binding cap is 28 tool calls, which is cheap in
wall-clock, so their mean task lands near 5.7 min. We run 45 calls, so time binds instead. Copying their time
cap without their call cap times out; copying their call cap costs resolves (below).

---

## 4. NEW MEASUREMENT: time is the binding constraint, and it is where the score is going

Classifying every task by what ended it (`task_wall_s` within 20 s of the cap vs `tool_calls` at the cap):

**E0 — 4.5 min / 45 calls, n=48**

| ended by | n | resolved | empty patch | mean calls | mean s |
|---|---|---|---|---|---|
| **TIME cap** | **38 (79.2%)** | **4 (10.5%)** | **18 (47.4%)** | 32.3 | 274.6 |
| agent stopped on its own | 9 (18.8%) | **7 (77.8%)** | **0 (0.0%)** | 26.4 | 187.9 |
| both caps | 1 (2.1%) | 0 | 1 | 45.0 | 273.5 |

`tool_calls`: min 13, median 32, max 45 — **only 1 task of 48 reached the 45-call cap.**

**EXP-003 — 8 min / 28 calls, n=48**

| ended by | n | resolved | empty patch |
|---|---|---|---|
| agent stopped on its own | 18 (37.5%) | 8 (44.4%) | 0 (0.0%) |
| **CALL cap** | **18 (37.5%)** | **0 (0.0%)** | 9 (50.0%) |
| TIME cap | 10 (20.8%) | 1 (10.0%) | 5 (50.0%) |
| both caps | 2 (4.2%) | 0 | 2 |

20 of 48 tasks hit the 28-call cap and **resolved zero of them.**

### What this establishes

1. **Our 45-call budget is nearly irrelevant** (median 32, one task at cap). The call cap is not what limits
   us, so trimming it toward their 28 can only hurt — EXP-003 shows the 28-call cohort resolving 0/20.
2. **Wall-clock time is the binding constraint on 79.2% of tasks**, and those tasks resolve at 10.5% and go
   home empty 47.4% of the time. We are being guillotined mid-work.
3. **We cannot buy more time** (section 3). So the only available lever is making each task *cheaper*: fewer
   wasted calls and less time per call. That is prompt surgery — EXP-013 — and it is the only one of the three
   queued experiments that is both available and gate-safe.
4. The 77.8%-vs-10.5% split is **not** a treatment effect and must not be read as one. Easy tasks finish
   early *and* resolve; the cohorts are self-selected by difficulty. The defensible quantity is the 47.4%
   empty-patch rate inside the time-capped cohort — that is pure waste, and it is what the first-edit
   deadline and the repro-file ban target.

---

## 5. Is there even a capability gap? Not on the strongest available test

Their 41.3% local resolve is measured only on gold-solvable tasks; our 22.9% is on dev-48, of which **20 tasks
are `gold_fails` in their census**. On matched denominators:

- unpaired: our E0 10/46 (Wilson 12.3-35.6%) vs their v19 19/46 (28.3-55.7%) → **Fisher p = 0.0717**
- paired on the 21 tasks both agents actually ran: both resolved 7, neither 13, v19-only 1, E0-only 0 →
  ours 7/21 vs theirs 8/21, **exact McNemar p = 1.0000**

**The agent-capability gap to a 0.24 team is not statistically established.** Decomposing their 14 vs our 7:
their own config at temp 0.2 (v19) scored 11, so the config is worth ~4 tasks — right at our measured MDE —
and temperature carried the remaining 3, unvalidated and inside their noise.

**Sandbox validated:** our EXP-000 gold control passes 108/129 against their env-repaired 106/129 (68
both-solvable, 18 both-fail, 37 we-pass/they-fail, 3 we-fail/they-solvable, 3 degenerate). Their census: 71
solvable, 55 gold_fails, 3 passes_without_patch; 106 solvable with env repair, the two missing libraries being
`inline_snapshot` and `dirty_equals` — which our prompt already vendors.

---

## 6. Retracted hypothesis

I proposed that the leaderboard's shape was max-of-N selection bias, from the monotone rise of median
submission count with score (0.24 to 15.5, 0.22 to 12, 0.18 to 9, 0.12 to 3). Their published
`leaderboard.json` shows a genuine capability ramp (0.06, 0.08, 0.12, 0.17, 0.18, 0.24), not a flat series
whose maximum happens to be high. **Selection is not the primary mechanism.** It survives only as a secondary
effect, evidenced by their v17 scoring 0.17 and 0.13 on one config. The submission-count arithmetic still
stands on its own: we have used 4 slots and have ~41 days to Dec 2.

---

## 7. Sources

All Kaggle-native; no peer-reviewed papers and no blogs were used.

| Source | What it gave |
|---|---|
| `muhammedidris28/gemma4-agent-runs` (dataset, Apache-2.0) | `leaderboard.json`, `runs.jsonl` (574 rows), `agents/v11...v25/` bundles, LoRA metrics |
| `muhammedidris28/locbench-129` (dataset, Apache-2.0) | `gold_census.jsonl`, localization labels, `codegraph/`, `test_deps_standins/` |
| `muhammedidris28/{where-to-edit,git-history-as-a-gym,gold-patch-census}-*` (3 notebooks, 0 votes) | method writeups; the "leaderboard cannot rank agents" argument |
| `flexonafft/gemma-4-budget-aware-coding-agent-v2` (0.22, r19) | independent config corroboration |
| `honghanhhh/gemma-4-baseline-lb-0-24` (0.18, r232) | the notebook EXP-012 was built on |
| `davis0178/gemma-4-agent-baseline` (0.22, r18) | **downloaded, not yet read** |
| public leaderboard CSV, 3470 teams, 2026-10-22T15:54 | score distribution, K=58 proof, author-to-score joins, our rank |
| `kaggle competitions submissions` | our four refs: 57341732=0.06, 57412440=blank/timeout, 57445081=0.12, 57500339=0.10 |

**Referenced but not read:** the two paper-track papers themselves (*Git History as a Gym...*, *Where to
Edit?...*) — only their companion notebooks and datasets; forum #744692 and the "short caps scored lower"
thread, both quoted second-hand from their `eval_config.yaml` comments; `hitarthjain0`'s notebook (its 0.18 is
from the leaderboard join only); `muhammedidris28/git-history-gym`, the practice-task corpus.
