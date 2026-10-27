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
