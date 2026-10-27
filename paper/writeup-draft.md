**Status: DRAFT.** Sections 1–3 and 5–7 are complete and rest only on measurements already in hand; every
number in them regenerates from `tools/exp024_stats.py`. Section 4 is the only stub, pending EXP-025 (the
two-arm paired dev-48 pre-registered at `experiments/EXP-025-editfix-dev48.md`, running at the time of
writing); its pre-registered readings live in that file and are deliberately not restated here, so there is
one place to change them and it is not the paper. Body is **2,716 words of the 3,000 limit**, leaving ~280
for section 4 — if it needs more, section 5.2 is the most compressible.

---

## Abstract

We report a failure mode in Gemma-4 agentic coding that is invisible to the obvious instrumentation and
costs a large fraction of an agent's budget. Across two 48-task runs on the competition harness, **117 of
309 `edit_file` calls (37.9%, 95% CI 32.6–43.4%) never reached the file at all**: they failed with
`mandatory input parameters are not present: old_string`, meaning the anchor argument did not survive the
journey from model output to tool invocation. The loss is **positional** — of the 117 lost calls the *last*
argument survived in 116 while the *middle* argument survived in 0, and `write_file`, whose long argument
sits last, lost 0 of 14 (Fisher p = 0.0028). Because the harness's error text does not match the string the
agent's own recovery rule keys on, the agent resent identical arguments 8–19 times; **84–85% of all lost
calls are these retries**, not the initial slip. We also show why this went unnoticed through eight
leaderboard submissions: the natural detector, an `"status": "error"` envelope check, misses this error
entirely and under-reported it roughly tenfold. Separately, we find that the *larger* share of empty
patches comes from tasks that never attempt an edit at all, and that these exhaust the wall-clock budget
(19 of 21, against 5 of 20 resolvers, p = 2.5 × 10⁻⁵) because their calls cost 1.5–2× more — which makes a
deadline expressed in call index unreachable for exactly the tasks it targets. We release the corrected
detector, the analysis scripts, and per-task metrics for every run, and we pre-register a paired test of a
prompt-level mitigation.

## 1. Setting

Every team receives an identical harness, grader and task distribution, and one permitted model
(`gemma-4-31b-it-qat-w4a16-ct`, INT4, served by a patched vLLM on 4×L4). Submissions are **declarative** —
an agent manifest, prompt files, sampling and evaluation configs — with no custom tool code and no custom
entry point. What separates a strong submission from a weak one therefore lives in prompt text and a
handful of integers, which makes the harness's own failure behaviour unusually consequential and unusually
shared: a defect we find is a defect every team has.

Our own trajectory motivated the investigation. Eight scored submissions returned 4, blank, 7, 6, 8, 8, 7
and 7 resolved of 58 — mean 6.7, SD 1.4 — while we varied time caps, call caps, turn limits, thinking
budgets, output limits and prompt length. The distribution did not move. That pattern sent us to the traces
rather than to another configuration.

## 2. The defect

### 2.1 What happens

`edit_file` takes three arguments: a path, an `old_string` anchor to locate, and a `new_string` replacement.
In 117 of 309 observed calls the tool returned

> `failed as the following mandatory input parameters are not present: old_string`

The call never reached the file. No search was performed, nothing was modified, and the model received an
error that does not describe a failed match but a malformed invocation.

### 2.2 The mechanism is positional

Reconstructing each lost call from the trace:

| argument | position in the call | survived |
|---|---|---:|
| `filepath` | first | 117 / 117 |
| `old_string` | **middle** | **0 / 117** |
| `new_string` | last | 116 / 117 |

`write_file` provides a natural control. It also carries a long free-text argument, but that argument is
**last**. It lost **0 of 14** calls (Fisher exact p = 0.0028 against `edit_file`). The pattern is consistent
with the middle argument of a multi-argument call being dropped during tool-call construction, and it is not
consistent with a content-dependent parse failure, which would not respect argument order.

The rate is strongly modulated by `thinking_budget`:

| run | `thinking_budget` | lost / total `edit_file` | rate | affected tasks |
|---|---:|---:|---:|---:|
| E0 | 256 | 92 / 172 | **53.5%** | 14 / 48 |
| EXP-003 | 4096 | 25 / 137 | **18.2%** | 4 / 48 |

Call-level Fisher p = 1.2 × 10⁻¹⁰; task-level p = 0.0169. A larger thinking budget substantially protects
against the loss. This is worth stating plainly because the intuition runs the other way: thinking budget is
usually discussed as a quality knob, not a tool-call *integrity* knob.

### 2.3 The expensive part is the loop, not the slip

The initial loss is a generation-level event. What follows is not. The prompt in use instructed the agent,
on a failed edit, to retry "if `edit_file` reports that `old_string` was not found or is not unique" — a
**different error string**. The observed error matches no recovery rule, so the agent treated the call as
transient and resent **identical arguments**, between 8 and 19 times on the worst tasks.

| run | lost calls | affected tasks | per-task counts | retries after the first |
|---|---:|---:|---|---:|
| E0 | 92 | 14 | 19, 12, 12, 10, 10, 7, 6, 5, 3, 3, 2, 1, 1, 1 | **78 / 92 = 85%** |
| EXP-003 | 25 | 4 | 10, 8, 5, 2 | **21 / 25 = 84%** |

In E0 this consumed **92 calls ≈ 712 seconds across 14 of 48 tasks**. The losses are heavily clustered: a
single task accounts for 21% of all losses in E0 and 40% in EXP-003. Any analysis treating calls as
independent observations will therefore overstate its own precision by roughly an order of magnitude — a
trap we fell into ourselves before correcting it (§6).

## 3. Why it stayed invisible for eight submissions

Our trace analyser detected failed edits by testing whether the tool observation contained an
`'"status": "error"'` envelope. **This error carries no such envelope.** The consequences:

| run | reported by the envelope detector | actual argument losses |
|---|---:|---:|
| E0 | 9 | **92** |
| EXP-003 | 27 | **25** |

The metric under-reported the dominant failure mode roughly tenfold on one run, and — worse for anyone
using it to choose between configurations — it was **not comparable between runs**, because the two runs'
errors fell into the envelope in different proportions. `edit_fail_rate` was a number we steered on for
eight submissions. It was measuring something else.

We think this generalises beyond our own code. A structured-envelope check is the natural way to detect
tool failure and the first thing a reasonable engineer writes, and it silently excludes exactly those
errors raised *before* the tool body runs — which is where argument-validation failures live. Any team
instrumenting this harness the obvious way has the same blind spot.

## 4. Does a prompt-level mitigation work?

**[PENDING — EXP-025.]** Section to be completed from the pre-registered two-arm paired dev-48 at
`experiments/EXP-025-editfix-dev48.md`. Arms differ by exactly two prompt edits and nothing else (verified:
the three configuration files are byte-identical; only `prompts/swe_coder.md` differs). The intervention
reverses the prompt's anchor-shortening advice and adds an always-resident recovery section keyed on the
literal error string, with a three-rung ladder: a longer verbatim anchor, then a single `write_file` carrying
complete content, then one shell command.

The primary endpoint is **wasted retries per task** (losses after the first in that task), tested by paired
Wilcoxon over the same 48 task ids. It is *not* the per-call loss rate: §2.3 shows the prompt cannot prevent
the initial slip, only the loop, and the loop is 84–85% of the cost. Power is explicitly **conditional** on
the baseline arm's affected-task count (0.97–1.00 at 14 affected, but only 0.42–0.73 at 6), and the
underpowered branch is pre-registered as uninterpretable rather than as a null. Resolved count is
pre-registered as **not** an endpoint: at 48 tasks its MDE is +6 to +8, so it cannot speak either way.

We will report the measured effect whichever direction it falls. A mitigation that removes the loop without
moving the empty-patch rate would be the more informative outcome, because it would localise the remaining
gap to the tasks described in §5.

## 5. The upstream fact this all serves, and the limit of fixing it

Across both runs, **35 tasks produced an empty patch and exactly 0 of them resolved.** An empty patch is
worth precisely as much as no attempt. Those 35 split cleanly:

* **14 attempted edits and had every attempt fail.** This is the population §2 describes.
* **21 never called `edit_file` or `write_file` at all.** They explored and never committed to a change.

The second group is the larger half, so the defect in §2 — real and substantial as it is — is **not** the
dominant cause of empty patches. It is worth being explicit about that, because the tempting framing of
§2 is "we found the bottleneck", and the measured answer is "we found one of two, and it is the smaller one."

### 5.1 What the 21 actually ran out of

A prior experiment of ours concluded these tasks were "not starved" of budget, because they used a
comparable number of turns to the winners and almost none hit the **call** cap. Both observations are
correct; the conclusion does not follow, because the binding resource is neither turns nor calls:

| group | n | hit **time** cap | hit call cap | s per call | `read_file` calls | whole-file reads |
|---|---:|---:|---:|---:|---:|---:|
| never attempted | 21 | **19 / 21** | 4 / 21 | — | 10.5 | 1.8 |
| all attempts failed | 14 | 7 / 14 | 9 / 14 | — | 14.1 | 1.4 |
| resolved | 20 | **5 / 20** | 3 / 20 | — | 7.9 | 0.6 |

Time-cap exhaustion against resolved tasks: Fisher exact **p = 2.5 × 10⁻⁵**. The pattern holds inside each
run separately (E0: 13/13 of the never-attempt group against 4/11 of resolvers; EXP-003: 6/8 against 1/9),
which matters because the two runs have different caps (270 s and 480 s). The two caps are cleanly
dissociated: on the **call** cap the same comparison gives 4/21 against 3/20, Fisher **p = 1.0**. Note also
which group does exhaust calls — the all-attempts-failed group, 9 of 14, which is §2's retry loop spending
them.

The mechanism is cost per call, which is also why a turn count misleads. Within each run:

| run (time cap) | group | wall s | turns | **s per call** | whole-file reads |
|---|---|---:|---:|---:|---:|
| E0 (270 s) | never attempted | 273.8 | 32.5 | **10.33** | 2.00 |
| E0 (270 s) | resolved | 213.2 | 38.2 | **6.75** | 0.73 |
| EXP-003 (480 s) | never attempted | 431.2 | 28.0 | **19.59** | 1.50 |
| EXP-003 (480 s) | resolved | 227.3 | 28.2 | **9.97** | 0.33 |

The never-attempt group takes **1.5× to 2× longer per call**, reads more files and reads far more of them
whole. It therefore reaches the clock having taken *fewer* turns — which is exactly how a turn-count
comparison hides the exhaustion. Resolvers finish well inside the cap (213 s of 270 s; 227 s of 480 s) and
are not racing it at all.

### 5.2 Why this breaks a deadline expressed in call index

The natural mitigation is a forcing function: *if you have made N calls and still have no edit, edit now.*
We ship one. But N is a call index, and the table above shows call index is a badly calibrated proxy for
elapsed time — **mis-calibrated worst on precisely the population the rule exists to rescue.** Priced at
each group's own seconds-per-call:

| deadline | never-attempt group reaches it at | resolved group | cap |
|---|---:|---:|---:|
| call 25, E0 | **258 s** | 169 s | 270 s |
| call 25, EXP-003 | **490 s** | 249 s | 480 s |
| call 12, E0 | 124 s | 81 s | 270 s |
| call 12, EXP-003 | 235 s | 120 s | 480 s |

A deadline at call 25 fires at 96% of E0's cap and **past the end** of EXP-003's: for the slow tail it is
not a late deadline but an unreachable one. Our own sizing of that rule put call 25 at roughly 135–170 s by
multiplying the **population-average** turn cost — averaged, that is, mostly over tasks that do not need
the rule. Call 12 lands inside the cap in both runs, with room to act afterwards.

The general form of the error is easy to repeat: a budget rule that exists to catch a failing
subpopulation must be calibrated on that subpopulation's cost, not the mean. A rule keyed to a counter the
agent already emits is cheap to write, but calls are not what terminates the episode — wall-clock is.

**What this does not establish.** These 21 task-runs happened *before* any first-edit deadline existed in
our prompt, so this is observational. We cannot claim the rule would convert them, and we cannot order the
causation: expensive, read-heavy calls may be a symptom of a genuinely harder localisation problem rather
than a cause of the empty patch. What is established is that the empty-patch population exhausts wall-clock
while the resolving population does not, and that call-indexed deadlines are mis-sized for it.

## 6. Limitations, and three corrections to our own analysis

**The anchor-length prescription is weakly supported.** Anchors that landed had a median length of 156
characters against 44 for lost ones (Mann-Whitney p = 7.9 × 10⁻¹⁶), but **53 of the 117 lost calls leaked no
fragment at all**, so the lost-anchor median is conditioned on the subset where something survived and is a
lower bound. There is also an unresolved tension: if the loss is positional truncation, a *longer* middle
argument ought to be *more* fragile, not less. The multi-line evidence points the other way — 48% of lost
anchors were single-line against 13% of successful ones — but it does not settle the question. The
positional mechanism (§2.2) and the thinking-budget contrast (§2.3) do not depend on this comparison; the
specific "150–300 characters" advice does.

**Corrections we publish because they bear on how such results should be read.** The third is §5.1's: we
had accepted "not starved of budget" from a turn count and a call cap, and the group was in fact exhausting
the clock in 19 of 21 runs. First, our two runs
share all 48 task ids, so every comparison between them is **paired**. Analysed as unpaired, a difference in
empty-patch rate and resolve-among-producers looked like a real quality/quantity trade-off; analysed
correctly, exact McNemar gives p = 0.73 on resolved and p = 0.58 on empty patch. The effect was noise, and we
had begun designing around it. Second, we initially computed power on the per-call loss rate, ignoring the
clustering documented in §2.3, and obtained a figure near 0.98 for a design whose honest power against a
plausible effect was 0.61. All three share a shape — a summary statistic answered a question it was not
measuring — which is also the shape of §3.

**Scope.** Single model, single harness, 96 task-runs, one cohort of 48 ids drawn from four public
repositories. We make no claim about other models or other tool schemas, and no claim that fixing this moves
a leaderboard score — our own 58-task public split has a minimum detectable effect of roughly 4 tasks, which
is larger than any effect we would predict here.

## 7. The resource

Everything needed to reproduce or re-run the above:

* **`tools/analyze_traces.py`** — per-task trace analysis with the corrected detector. Counts envelope
  failures and argument losses, reporting `n_edit_arg_loss` separately because that subset is the
  actionable one.
* **`tools/exp024_stats.py`** — regenerates every number in §2, §3, §5 and §6 from the run directories,
  including the positional table, the Fisher and McNemar tests and the censoring diagnostic.
* **`tools/export_release_csv.py`** and **`release/per_task.csv`** — per-task metrics for all 96 task-runs,
  35 columns. The exporter enforces a *positive* field allowlist, so a field added upstream is excluded
  until reviewed rather than published by default. The traces are never released: they contain repository
  content.
* **Pre-registrations** for each experiment, committed before the corresponding run or submission, with
  readings fixed in advance.

The published CSV's `n_edit_arg_loss` column sums to 117, so the central claim of this paper is
recomputable from the released data alone.
