# EXP-025 — Does the recovery ladder break the retry loop? A two-arm paired dev-48

**Date:** 2026-10-26
**Type:** dev-48 GPU experiment, two arms. ~7.2 L4x4-h of the 30/week.
**Pre-registered:** this file is committed **before** either kernel is pushed. Sections 4-6 are written blind.
**Serves:** the LB keep/revert decision on the EXP-024 prompt fix (submission #9, live now), **and** the
paper track's Contribution 2, **and** the released toolkit's held-out validation (`plan.md:17`).
**Supersedes:** EXP-024 §2 item 2, a single arm against EXP-003's 25/137. §1 says why that design was wrong.

---

## 1. Why two arms, and why EXP-024's endpoint was the wrong one

EXP-024 proposed **one** arm of the shipping bundle, with the per-call `edit_file` argument-loss rate as the
primary endpoint, compared against EXP-003's existing 25/137, quoting power 0.982 at a true 5%. Three defects,
all fixable before spending any GPU:

**(a) The comparator is confounded.** EXP-003 differs from the shipping config in the prompt **and both caps**
(8 min / 28 calls versus 4.5 min / 64 calls). A drop in loss rate could not be attributed to the prompt edits.
This is the same multi-way-difference flaw EXP-024 §6 correctly identified in the brief that commissioned it;
repeating it here would be indefensible. Two arms on the **same 48 task ids**, differing by **exactly the two
prompt edits**, cost one extra run and remove the confound entirely. Verified by pack: `submission/` is
`99b750a02d1f…` at 11,226 instruction chars, the candidate is `dbe9248ca7b8…` at 12,832, and the three config
files are **byte-identical by diff** — the two trees differ in `prompts/swe_coder.md` and nothing else.

**(b) The per-call rate treats clustered observations as independent, so 0.982 is not real.** Measured:

| run | lost calls | affected tasks | per-task counts | losses that are **retries after the first** |
|---|---:|---:|---|---:|
| E0 | 92 | 14 | 19,12,12,10,10,7,6,5,3,3,2,1,1,1 | **78 of 92 = 85%** |
| EXP-003 | 25 | 4 | 10,8,5,2 | **21 of 25 = 84%** |

One task supplies 21% (E0) and 40% (EXP-003) of all losses on its own. Treating ~140 calls as ~140 independent
trials inflates the effective sample by roughly an order of magnitude. Recomputed as an honest unclustered
two-proportion test at n=140/arm, power against a *halving* of the rate is **0.61**, not 0.98, and the MDE is an
**11-point absolute drop** — the design was not powered for any plausible effect.

**(c) It measures the one thing the intervention cannot change.** The first argument loss in a task is a
generation-level slip: the model emitted the call, the middle argument did not survive, and no prompt wording
prevents that. What the prompt *can* prevent is everything after it — the 8-to-19 identical resends. That is
**84-85% of the whole cost**, and it is what the recovery ladder is written to stop. So the primary endpoint
must be **wasted retries**, not loss rate.

## 2. Design

Two kernels, same cohort `experiments/cohorts/dev-48.txt` (48 ids, seed 20261013), same everything else.

| arm | tree | sha256 | prompt | what it is |
|---|---|---|---|---|
| **A — baseline** | `submission/` | `99b750a02d1f…` | 11,226 chars | **The shipping config's first ever dev-48.** 4.5 min / 64 calls / turns 96 / thinking 4096 has never been run end to end, across eight submissions. |
| **B — fix** | `experiments/EXP-024/candidate-editfix/` | `dbe9248ca7b8…` | 12,832 chars | Arm A plus the two anchored prompt edits, and **byte-identical to live submission #9**. |

Paired: the same 48 ids in both arms, so every contrast is a within-task difference.

## 3. Endpoints, fixed in advance

**Primary — wasted retries per task**, i.e. lost `edit_file` calls after the first in that task. Paired
Wilcoxon signed-rank over 48 tasks. Reported with the total wasted-call count and the seconds they consumed.

**Power (simulated, 4,000 reps, seed 11), and it is conditional — state Arm A's affected count first:**

| Arm A affected tasks | ladder removes 100% | 80% | 50% | 25% |
|---|---|---|---|---|
| 14 (as E0) | 1.000 | 1.000 | 0.998 | 0.969 |
| 10 | 0.990 | 0.989 | 0.976 | 0.868 |
| **6 (as EXP-003)** | **0.733** | **0.712** | **0.638** | **0.423** |

**The live risk, stated before the run:** affected-task *count* tracks `thinking_budget`, and Arm A is at 4096,
the same as EXP-003, which had only **4** affected tasks. If Arm A lands near 4-6 the contrast is
**underpowered and must not be read as a null**. Arm A allows 64 calls against EXP-003's 28, so there is more
room to loop, which pushes the other way — but that is a hypothesis, not a guarantee. **Arm A's affected-task
count is the first number to read, and it decides whether the contrast is interpretable at all.**

**Secondary, pre-registered, none of them decisive:** affected-task count; max loop length per task; empty-patch
rate (the mechanism this is all upstream of — 0 of 35 empty patches has ever resolved); first-edit call index;
never-attempted-an-edit count; resolve-among-producers.

**Explicitly NOT an endpoint: resolved count.** dev-48's MDE on resolves is +6 to +8 of 48. Both arms will
report it, and in neither direction will it be called a result. This is written down because an arm that
happens to resolve 14 will be very tempting to over-read.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

| outcome | reading |
|---|---|
| **Arm A affected ≤ 6** | **Underpowered. The contrast is uninterpretable either way.** The finding itself still stands (it was measured, not inferred), but the *mitigation* claim goes to the paper as "not yet testable at this n", and the LB keeps the fix on the §5 asymmetry argument alone. |
| **Arm A affected ≥ 10, and wasted retries drop with p < 0.05** | **The ladder works.** Keep the fix for the remaining LB slots. This is the paper's Contribution 2, stated with its effect size. |
| **Arm A affected ≥ 10, no drop** | **The ladder does not work, and that is a publishable result** — it localizes the loop to something prompt wording cannot reach, which is a sharper claim than "we fixed it". Revert the EDIT-phase edit, keep the detector. |
| **Wasted retries drop but empty-patch rate does not move** | Expected, and **not** a disappointment: it would localize the remaining gap to the **21 never-attempted** tasks, i.e. the forcing-function problem, which is then the clear next experiment. |
| **Either arm returns blank / crashes** | Infrastructure, not science. Check the `docker_image` sha pin first (`plan.md:1188`: a missing pin already cost E0 v1 a run with 0 tasks). |
| **Arm B worse than Arm A on empty patches** | The ladder's rung 3 (`run_command` rewriting a whole file) is the only instruction here that can corrupt source. **Revert rung 3 first**, before touching the anchor-length advice. |

## 5. Why the LB keeps the fix even if this comes back underpowered

Asymmetry, not optimism. The ladder's cost is bounded: it only fires after an error that already means the
call did nothing. Its upside is 84-85% of a failure mode that burned 712 s across 14 tasks in E0. A prompt
instruction that activates only on a confirmed-dead call has close to no downside risk, so the decision does
not need statistical significance — unlike the anchor-length advice, which changes behaviour on **every** edit
and therefore does.

## 6. What this does and does not license

**Licenses:** a causal claim about the two prompt edits versus the shipping baseline on the wasted-retry
endpoint, on dev-48, at this n. The shipping config's first process-level baseline. A held-out third trace set
for validating `tools/analyze_traces.py`'s `n_edit_arg_loss` detector on data it was not derived from.

**Does not license:** any claim about LB movement (the MDE forbids it); any claim about resolves; any claim
that the *anchor-length* half of the prompt edit works, since both edits ship in one prompt and this design
cannot separate them (a third arm could, and is not worth 3.6 GPU-h today); any inference about the private
half.

**Carried-forward caveat from EXP-024, unresolved and stated again:** the "150-300 char anchor" prescription
rests on a **censored** comparison — 53 of the 117 lost calls leaked no fragment, so the lost-anchor median of
44 chars is a lower bound. And if the loss is positional truncation, a *longer* middle argument should be
*more* fragile, not less; the multi-line evidence (48% of lost anchors single-line vs 13% of successes) points
the other way but does not settle it. **This experiment does not test that prescription.**

## 7. Exact commands

Built with `tools/build_notebook.py`, never hand-edited. `--set` inserts values verbatim as Python source and
fails loudly on an unknown name, so `EXP_ID` and `TASK_IDS` must arrive as Python literals.
`RUN_GOLD_CONTROL=False` because EXP-000 already did it and it would burn cap time for nothing.

Both `kernel-metadata.json` files carry the explicit pinned `docker_image` sha copied from the working E0 and
exp010 configs — **not** `docker_image_pinning_type: original`, which does nothing on a kernel with no prior
push and already cost E0 v1 a zero-task run (`plan.md:1188`). The exact invocations and the resulting kernel
slugs are recorded in §8 as they are run.

## 8. Pushed

Both kernels pushed 2026-10-26, version 1, **both RUNNING in parallel**:

| arm | kernel | embedded tree (sha256 verified from the notebook's own base64) |
|---|---|---|
| A — baseline | `rainm4/gemma4-exp025-arma-baseline` | `99b750a02d1f2c6ccf1d1a6cb8ee61ca2095afe15579c1b37453fc32514a3462` |
| B — fix | `rainm4/gemma4-exp025-armb-editfix` | `dbe9248ca7b8a0f74478e4dfdad0bbe65740cb4dc39b725e67540457658488a5` |

Pre-push verification, done because a silent mis-build is the failure mode that costs a whole run:

* each notebook's embedded `SUBMISSION_B64` was decoded and hashed, and **both match the intended tree**;
* `EXP_ID` and all 48 cohort ids confirmed present in the built notebook source;
* both `kernel-metadata.json` files are **byte-identical to the known-good `exp010` config apart from
  `id`/`title`** (diffed), so the explicit pinned `docker_image` sha is carried and
  `docker_image_pinning_type` is absent — the regression at `plan.md:1188` that gave E0 v1 a zero-task run.

Expected wall time ~3.6 h each from the two prior dev-48 runs; ~7.2 L4x4-h of the 30/week quota.

---

## 9. Results, 2026-10-27. Section 4's readings applied as written.

Both arms COMPLETE, 48/48 tasks each, 48 traces and 48 patches apiece. Cohort verified identical between
arms and to `experiments/cohorts/dev-48.txt` (set equality and order). `eval_config` as run was identical
in both: 4.5 min / 64 calls / 96 turns / timeout 300. Both at `thinking_budget: 4096`.

### 9.1 Step 1, the number section 3 said to read first

| arm | affected tasks | lost calls | `edit_file` calls | loss rate | per-task losses | wasted retries |
|---|---:|---:|---:|---:|---|---:|
| A baseline | **6 / 48** | 49 | 114 | 43.0% | 14, 11, 11, 9, 2, 2 | 43 |
| B editfix | 9 / 48 | 35 | 81 | 43.2% | 9, 9, 8, 4, 1, 1, 1, 1, 1 | 26 |

**Arm A affected = 6. This is section 4 row 1: UNDERPOWERED, and the contrast is uninterpretable either
way.** The live risk named in section 3 is exactly what happened -- affected-task count tracked
`thinking_budget` to EXP-003's neighbourhood (4) rather than E0's (14), and the 64-call allowance did not
push it up. The pre-registered prediction was right and the design still lost; that is the cost of running
the arm at the config we ship rather than at the config that shows the defect most clearly.

### 9.2 Primary endpoint, reported because it was pre-registered, not because it is readable

Wasted retries per task: **A 43, B 26, difference -17 (-40%)**. Nine non-zero pairs: B lower on 6, higher
on 3, 39 tied. **Exact paired Wilcoxon W = 15.5, p = 0.4531.**

Per section 4 row 1 this is **not** evidence the ladder works and **not** evidence it fails. The point
estimate is in the predicted direction and of the predicted size; at 6 affected tasks the design had power
0.42-0.73 and it did not resolve. Max loop length fell 14 -> 9, `n_edit_fail` 51 -> 38,
`n_identical_repeats` 68 -> 58 -- all the same direction, none of them independent of the primary.

**Decision, per section 5: keep the fix for the remaining LB slots,** on the asymmetry argument alone. The
ladder only fires after an error that already means the call did nothing. Nothing here changes that.

### 9.3 Secondaries, and one exploratory result that is NOT pre-registered

| endpoint | A | B | A-only | B-only | exact McNemar |
|---|---:|---:|---:|---:|---:|
| resolved **[NOT an endpoint]** | 11/48 | 9/48 | 3 | 1 | 0.6250 |
| empty patch | 19/48 | 21/48 | 4 | 6 | 0.7539 |
| never attempted an edit | 19/48 | 20/48 | 5 | 6 | 1.0000 |
| submit_patch called | 3/48 | 9/48 | 1 | 7 | 0.0703 |
| **time cap hit** *(exploratory)* | 46/48 | 39/48 | 7 | 0 | **0.0156** |

**The time-cap result was not pre-registered** -- section 3's secondary list does not contain it. I went
looking for it only because of the wall-clock finding in EXP-010's correction, written the same day. With
roughly eight comparisons on this table, p = 0.0156 does not survive multiplicity honestly, and
`submit_patch` at 0.0703 does not either. **Recorded as a hypothesis for a future pre-registration, not as
a result.** It is a coherent one: 7 tasks moved off the clock and 0 moved onto it, and B spent fewer calls
everywhere (`edit_file` 114 -> 81, `read_file` 485 -> 424, `run_command` 689 -> 662).

**Section 4 row 6 fired on its letter and not on its evidence.** "Arm B worse than Arm A on empty patches"
is literally true, 21 against 19 -- but A-only 4 versus B-only 6 at McNemar p = 0.75 is noise, and the row
named no threshold. **Rung 3 is not reverted.** The pre-registration should have said "worse by more than
the paired MDE"; that it did not is a drafting defect in section 4, logged here rather than quietly
resolved in whichever direction suited the result.

**Arm A is also the shipping config's first dev-48 baseline**, which section 2 called out as never having
been run end to end: **11/48 resolved (22.9%)**, empty patch 39.6%, time cap 95.8%.

### 9.4 What the held-out data did to the EXP-024 findings

This is what section 6 licensed the arms for: a third and fourth trace set for the detector and the
mechanism, on data neither was derived from. Pooled over all four runs there are now **201 lost
`edit_file` calls**.

**REPLICATES, and strongly.** `old_string` present on **0 of 201** lost calls; `new_string` present on
**200 of 201**. On the 111 surviving held-out calls both arguments are present 111/111. Anchor length:
held-out surviving median 202 chars against a lost-call reconstruction median of 39, pooled
**p = 7.5e-08, AUC 0.857** (still censored -- 61 of 84 held-out lost calls leaked no fragment, so the lost
median remains a lower bound).

**DOES NOT REPLICATE: `thinking_budget` as the driver of the loss rate.** EXP-024 reported 256 -> 53.5% and
4096 -> 18.2% at Fisher p = 1.2e-10. Both new arms ran `thinking_budget: 4096`, the same as EXP-003:

| run | thinking_budget | lost / `edit_file` | rate |
|---|---:|---:|---:|
| E0 | 256 | 92/172 | 53.5% |
| EXP-003 | 4096 | 25/137 | **18.2%** |
| EXP-025 Arm A | 4096 | 49/114 | **43.0%** |
| EXP-025 Arm B | 4096 | 35/81 | **43.2%** |

Three runs at an identical thinking budget give 18.2%, 43.0% and 43.2%: chi-square homogeneity **22.50 on
2 df, p = 1.3e-05**. Each new arm differs from EXP-003 at p < 1e-3 with the budget held fixed. **The
dose-response was confounded** -- EXP-003 differs from the new arms in prompt and in both caps -- and the
residual 256-versus-4096 contrast (53.5% vs 32.8% pooled, p = 9.5e-06) cannot be attributed to thinking
budget given between-run heterogeneity this large at a fixed budget. The claim is withdrawn.

**WEAKENED: `write_file` as a clean control.** EXP-024 reported 0/14. Held out it is **3/30** (all three in
Arm A; Fisher against 0/14 gives p = 0.54, so this is not a detected change, but it is no longer a clean
zero). More important, the three losses drop **`filepath`, the FIRST argument**, not a middle one.

**So the "middle argument" framing is wrong.** What holds across all four runs and both tools is: **the
final argument survives** (200/201 `edit_file`, 3/3 `write_file`), while a **non-final** argument vanishes --
`old_string` for `edit_file`, `filepath` for `write_file`. The comma-splitting story is also not sufficient
on its own: **69% of the 303 surviving anchors contain a comma** (67-78% in every run), so comma content is
ordinary in calls that land.

### 9.5 Carried forward

* The paper's sections 2.2 and 2.3 both need correcting before Nov 12 -- 2.3 withdrawn, 2.2 reframed from
  "middle" to "non-final". Section 4 can now be written, as a measured null-at-this-n with a point estimate.
* The wall-clock/time-cap hypothesis needs its own pre-registration if it is to count.
* Still unseparated, as section 6 said it would be: the anchor-length edit and the recovery ladder shipped
  in one prompt, and this design cannot attribute the -17 to either.
* GPU: ~7.2 L4x4-h spent of the 30/week.
