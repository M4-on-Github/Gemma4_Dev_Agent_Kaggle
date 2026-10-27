# EXP-026 — Does routing a dead `edit_file` through `run_command` break the retry loop? One paired arm against EXP-025 Arm A

**Date:** 2026-10-27
**Type:** dev-48 GPU experiment, **one** arm (Arm C). ~3.6 L4x4-h of the 30/week.
**Pre-registered:** this file is committed **before** any Arm C result exists. Sections 3-6 are written blind and
are not revised after the numbers land; where a reading turns out to be badly drafted, the defect is logged in
section 9, not repaired in place.
**Serves:** the LB prompt for submission #10, and the paper track's Contribution 2 (the recovery-ladder result).
**Supersedes:** the recovery ladder of EXP-024/EXP-025 (submission #9, `dbe9248ca7b8…`). Section 1 says why.

---

## 1. What the research and the held-out traces changed

The brief ranked five options. Evidence gathered before writing this file moved the ranking:

| id | option | verdict | why |
|---|---|---|---|
| R3 | route the retry through `run_command` | **SHIPS; the *ladder* it replaces is the finding** | §1.1 |
| R2 | temperature arm | **dropped** | no published evidence that lowering temperature fixes a *terminator-token* slip; the only in-house contrast (EXP-003 at 0.2) is confounded three ways (EXP-025 §9.4), so there is nothing to build a dose-response on |
| R4 | locator sub-agent | **dropped** | public oracle ablations (Apache-2.0, third party) put perfect localization at roughly +5 of 129 and knowledge of what the hidden tests check at roughly +25 of 129; localization is not where the points are |
| R1 | prompt diet | **not done** | rests on one trace and on the `compactions` metric, which reads 0 on all 192 tasks, so it cannot move |
| R5 | cap / thinking | **untouched** | the cap is gate-fixed at 4.5 min (section 5) |

### 1.1 Why the ladder was the wrong shape, from the four dev-48 trace sets already in hand

Pooled over E0, EXP-003, Arm A and Arm B there are 201 lost `edit_file` calls. Their sequence is a **two-state
process**, not independent slips:

| run | fresh slip rate (previous `edit_file` landed) | repeat rate (previous `edit_file` was lost) |
|---|---:|---:|
| E0 | 16/88 = 18.2% | 76/84 = 90.5% |
| EXP-003 | 4/113 = 3.5% | 21/24 = 87.5% |
| Arm A | 6/69 = 8.7% | 43/45 = 95.6% |
| Arm B (ladder) | 9/52 = 17.3% | 26/29 = 89.7% |

Once a malformed call is in the context it is emitted again about nine times in ten, and Arm B's ladder did not
change that (89.7% against Arm A's 95.6%). The ladder's rung 1 is "re-send `edit_file` with a LONGER anchor".
What the model actually did on the call right after a lost one:

| run | next call is `edit_file` | next call is `run_command` | lost calls |
|---|---:|---:|---:|
| E0 | 77 | 3 | 87 |
| EXP-003 | 22 | 0 | 24 |
| Arm A | 38 | 4 | 48 |
| Arm B (ladder) | 25 | **1** | 33 |
| **pooled** | **162** | **8 (4.2%)** | **192** |

(The remaining calls were `read_file`, and one `write_file`. 192 rather than 201 because the last call of a trace has no successor.)
For the first lost call in each task, the very next call was `edit_file` 26 times, `read_file` 4, `run_command`
**0 of 30**. The ladder put rung 1 first and the model took it: 25 of 33. Of the 8 times the model went to
`run_command` on its own, 6 were shell edits (`sed -i`, a python replace, `printf >>`) and each exited 0; the
other 2 were `grep`. So the escape works and the model does not take it unprompted.

The mechanism is the one EXP-025 §9.4 found: the model closes a **non-final** string argument with a backtick or
a plain quote instead of the special token, so the parser swallows `,old_string:` into `new_string`.
`run_command`'s only parameter is its **last**, and it is structurally immune: 0 stray terminators in 2,863 calls.
A recovery that stays inside `edit_file` stays inside the defect.

A public bundle (author flexonafft, CC BY 4.0; it carries a self-reported 0.22 score badge that I have not
verified) ships the same idea: edits go through a python heredoc in `run_command` after two matching failures.
Independent convergence is weak evidence and is noted as such; the evidence is the table above.

### 1.2 What #10 changes against #9, and why each change is there

| change | direction | basis |
|---|---|---|
| ladder rungs 1-3 removed | removed | rung 1 is the loop (above); rung 2 (`write_file` a whole file) is also a non-final-argument tool; the shell route is kept as the *only* route |
| new section: after the error, **never `edit_file` again in this task**; the next call is a quoted-heredoc python replace | added | §1.1. "Never again" rather than "not for this edit" because the malformed call stays in history and the repeat rate is about 90% |
| "150-300 char anchor" advice removed | removed | the evidence was a censored comparison (EXP-024 §6, carried in EXP-025 §6). Held out it points the wrong way: Arm B's fresh slip rate is 17.3% against Arm A's 8.7% (Fisher p = 0.17, not significant, but not the predicted sign). Arm A's anchor text is restored |
| two pointer edits: the FIRST-EDIT DEADLINE bullet and the EDIT-phase retry line | added | without them the prompt would say "your next call MUST be edit_file" and "retry with a shorter anchor" in the same breath as "never edit_file again". A contradiction is exactly the kind of thing that costs a run |

The base tree is `submission/` (Arm A, `99b750a02d1f…`). The three config files are untouched.

## 2. Design

One kernel, cohort `experiments/cohorts/dev-48.txt` (48 ids, seed 20261013). **Paired against EXP-025 Arm A**,
which ran the same 48 ids on the same image with a tree that differs from Arm C in `prompts/swe_coder.md` and
nothing else.

| arm | tree | prompt |
|---|---|---|
| A (existing, EXP-025) | `99b750a02d1f…` | 11,226 chars |
| **C (this run)** | `8b962a79682023911d043d8b503f249feff57891c614fc8c1fc7948269f1dc88` | 12,795 chars |

Arm B is **context only**, not a comparator: it differs from C in two ways (the anchor advice and the ladder).

**Known weakness of the design, stated now:** Arm A ran on 2026-10-26 and Arm C will run later. Sampling is at
temperature 1.0, so even an identical tree would not reproduce Arm A task for task. The pairing controls for task
difficulty, not for run-to-run noise. EXP-025's two arms ran together and had no such gap; this one does.

## 3. Endpoints, fixed in advance

**Primary — compliance.** Over all lost `edit_file` calls in Arm C that have a following call, the fraction whose
**next call is `run_command`**. Compared against Arm A's **4 of 48** by two-sided Fisher exact. Baseline pooled over
all four earlier runs: 8 of 192 (4.2%). This is a mechanism endpoint, chosen because it is the thing the prompt can
change, and because it is far better powered than any outcome endpoint.

**Co-primary — the route works.** For the first lost call in each Arm C task, `recovered` = a `run_command` within
the next 3 calls whose observation has `exit_code` 0 and contains neither `Traceback` nor `AssertionError`.
Reported as k of n, with the failing commands quoted.

**Power for the primary (simulated, 4,000 reps, Fisher against 4/48), as a function of how many lost calls Arm C
produces:**

| Arm C lost calls | true compliance 90% | 60% | 40% |
|---|---|---|---|
| 4 | 0.94 | 0.47 | 0.18 |
| 6 | 1.00 | 0.83 | 0.47 |
| 10 | 1.00 | 0.95 | 0.63 |
| 15 | 1.00 | 0.99 | 0.79 |

Expected Arm C lost calls: if compliance is high there are few, because the loop is cut. A pooled fresh slip rate
of 12.4% (Arms A+B, 15/121) over about 100 `edit_file` calls gives roughly 12 slips in roughly 7 tasks. **The count
of Arm C lost calls is the first number to read.**

**Secondary, none decisive:** wasted retries per task (lost calls after the first; paired Wilcoxon against Arm A);
`edit_file` calls issued after a task's first loss (a direct violation count: the rule says zero); total lost
calls; affected-task count; empty-patch rate; `submit_patch` called; never-attempted-an-edit; time cap hit.

**Explicitly NOT an endpoint: resolved count.** The dev-48 MDE is +6 to +8 of 48. Both arms report it; neither
direction is called a result.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Rows 1-6 are applied in order and the first match governs. Rows 7 and 8 are additive.

| # | outcome | reading |
|---|---|---|
| 1 | **Arm C has fewer than 4 lost calls** | **Underpowered; the compliance contrast is uninterpretable.** Not a null. The tree stays on the §5 argument; record the count and move on. |
| 2 | **Compliance >= 60% and recovered >= 70% of first losses** | **The prompt can move the loop.** Keep the section for the remaining LB slots. This is the paper's Contribution 2 with an effect size, replacing the ladder's null-at-this-n. |
| 3 | **Compliance 25-60%** | **Partial.** The model sometimes obeys. Keep (the cost is bounded, §5); the next lever is wording strength or placement, not a new mechanism. |
| 4 | **Compliance < 25%** | **A prompt rule cannot reach this.** The section costs about 500 prompt tokens for nothing; **revert to the `submission/` Arm A text** for the remaining slots. The only declaratively reachable lever left would be sampling penalties (`presence_penalty` / `frequency_penalty`), which is speculative and untested. |
| 5 | **Compliance >= 60% but recovered < 70%** | **The template is defective, not the rule.** Quote the failing commands, fix the template, and do not re-spend a full arm on it: replay the template in a sandbox first. |
| 6 | **Compliance >= 60%, recovered >= 70%, but `edit_file` calls after the first loss occur in more than 2 tasks** | The rule is half-followed; the "never again" clause is not holding. Report the violation count; do not weaken the clause on this evidence alone. |
| 7 | **Harm guard (additive):** empty-patch rate worse than Arm A at exact McNemar p < 0.05 (about 10 C-only against 2 A-only) | **Revert the section.** The heredoc replace is the only instruction here that can touch source; it asserts the old text occurs exactly once before it writes, so a corrupting edit would be a template bug, and this guard catches it. |
| 8 | **Either run returns blank or crashes (additive)** | Infrastructure, not science. Check the pinned `docker_image` first (`plan.md:1188`). |

## 5. Why the LB takes the tree before this arm reports

The same asymmetry argument as EXP-025 §5, restated rather than assumed. The section fires only after an error that
already means the call did nothing. Its downside is one wasted call and about 500 prompt tokens on every task. Its
upside is the 84-85% of the failure cost that is retry loops. Unlike the anchor-length advice (removed), it does not
change behaviour on every edit, so it does not need significance to be defensible. If the parent prefers to wait for
Arm C before submitting #10, nothing here forbids it; the readings above then decide the tree.

Gate arithmetic for the tree as built: `120 x (max_time_minutes + 1.0) = 120 x 5.5 min = 11.00 h <= 11.0 h`, which
passes at **4.5 min**. A 5.0 min cap would be 12.00 h and a hard error; exceeding the real notebook timeout scores
zero (submission #2). `max_tool_calls` and `max_turns` do not enter the formula. `eval_config.yaml` is unchanged
from `submission/` (`git diff` empty). `tools/validate_submission.py`: VALID, 0 errors, 0 warnings. Two packs of
the tree gave the identical sha256 above.

## 6. What this does and does not license

**Licenses:** a claim about whether a prompt instruction moves the post-loss behaviour, on dev-48, at this n; and
a comparison of the "stay inside `edit_file`" ladder against the "leave `edit_file`" rule, as two experiments
against shared baselines.

**Does not license:** any claim about LB movement (one task is 0.017; eight scored draws have mean 6.6 and SD
1.3 tasks); any claim about resolves; any attribution of C's effect to the heredoc *template* versus the "never
again" *clause*, since they ship together; any claim about the backtick-priming hypothesis below.

**Unaddressed confound, stated now.** The wrong closer is a backtick in 178 of 201 lost calls, and the prompt
itself contains backticks (inline code and fences). Whether prompt backticks prime the slip is untested. The new
section adds one fence (the template, two fence lines) and **no inline backticks**. If the fresh slip rate in C is
higher than A's 8.7%, look here first; with 6-9 events per arm it will not be distinguishable from noise.

## 7. Exact commands

To be built with `tools/build_notebook.py`, never hand-edited, exactly as EXP-025 §7: explicit pinned
`docker_image` sha copied from the working exp010/E0 configs, `RUN_GOLD_CONTROL=False`, `EXP_ID` and `TASK_IDS`
as Python literals. The authoring session does not push kernels; **the parent session builds and pushes**, and
records the kernel slug and the embedded-tree sha in section 8.

## 8. Pushed

Not yet pushed.

## 9. Results

None. Written before any exists.
