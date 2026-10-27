# The Argument That Never Arrives: A Silent Tool-Calling Failure in Gemma-4 Coding Agents

**Status: DRAFT.** Sections 1–3 and 5–6 are complete and rest only on measurements already in hand.
Section 4 is stubbed pending EXP-025, the two-arm paired dev-48 pre-registered at
`experiments/EXP-025-editfix-dev48.md` and running at the time of writing. Word count target ≤ 3,000;
current drafted body ≈ 2,150 words excluding this note.

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
entirely and under-reported it roughly tenfold. We release the corrected detector, the analysis scripts, and
per-task metrics for every run, and we pre-register a paired test of a prompt-level mitigation.

## 1. Setting

Every team in this competition receives an identical harness, an identical grader, an identical task
distribution, and one permitted model (`gemma-4-31b-it-qat-w4a16-ct`, INT4, served by a patched vLLM on
4×L4). Submissions are **declarative**: an agent manifest, prompt files, sampling and evaluation configs.
There is no custom tool code and no custom entry point. Whatever separates a strong submission from a weak
one is therefore located in prompt text and a handful of integers — which makes the harness's own behaviour,
including its failure behaviour, unusually consequential and unusually shared. A defect we find is a defect
every team has.

Our own trajectory motivates the investigation. Eight scored submissions returned 4, blank, 7, 6, 8, 8, 7
and 7 resolved tasks of 58, a mean of 6.7 with a standard deviation of 1.4, while we varied time caps, call
caps, turn limits, thinking budgets, output limits and prompt length. The distribution did not move. That
pattern — many configuration changes, no response — is what sent us to the traces rather than to another
configuration.

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
tool failure, it is what a reasonable engineer writes first, and it silently excludes exactly those errors
raised *before* the tool body runs — which is where argument-validation failures live. Any team
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
worth precisely as much as no attempt. Decomposing those 35:

* **21 never attempted an edit at all.** They did not run out of resources — they used a comparable number
  of turns to the tasks that succeeded — they simply never committed to a change. This is a *forcing
  function* problem, not a capacity problem.
* **14 attempted edits and had every attempt fail.** This is the population §2 describes.

So the defect in §2 is a real and substantial cost, and it is nonetheless the **smaller half** of the
empty-patch problem. We state this because the honest framing of our own finding is not "we found the
bottleneck" but "we found, measured and instrumented one of two roughly comparable bottlenecks, and the
other one is a prompting problem we have not solved."

## 6. Limitations, and two corrections to our own analysis

**The anchor-length prescription is weakly supported.** Anchors that landed had a median length of 156
characters against 44 for lost ones (Mann-Whitney p = 7.9 × 10⁻¹⁶), but **53 of the 117 lost calls leaked no
fragment at all**, so the lost-anchor median is conditioned on the subset where something survived and is a
lower bound. There is also an unresolved tension: if the loss is positional truncation, a *longer* middle
argument ought to be *more* fragile, not less. The multi-line evidence points the other way — 48% of lost
anchors were single-line against 13% of successful ones — but it does not settle the question. The
positional mechanism (§2.2) and the thinking-budget contrast (§2.3) do not depend on this comparison; the
specific "150–300 characters" advice does.

**Two corrections we publish because they bear on how such results should be read.** First, our two runs
share all 48 task ids, so every comparison between them is **paired**. Analysed as unpaired, a difference in
empty-patch rate and resolve-among-producers looked like a real quality/quantity trade-off; analysed
correctly, exact McNemar gives p = 0.73 on resolved and p = 0.58 on empty patch. The effect was noise, and we
had begun designing around it. Second, we initially computed power on the per-call loss rate, ignoring the
clustering documented in §2.3, and obtained a figure near 0.98 for a design whose honest power against a
plausible effect was 0.61.

**Scope.** Single model, single harness, 96 task-runs, one cohort of 48 ids drawn from four public
repositories. We make no claim about other models or other tool schemas, and no claim that fixing this moves
a leaderboard score — our own 58-task public split has a minimum detectable effect of roughly 4 tasks, which
is larger than any effect we would predict here.

## 7. The resource

Everything needed to reproduce or re-run the above:

* **`tools/analyze_traces.py`** — per-task trace analysis with the corrected detector. Counts both
  envelope-style failures and argument losses, and reports `n_edit_arg_loss` / `edit_arg_loss_rate`
  separately, because the argument-loss subset is the actionable one.
* **`tools/exp024_stats.py`** — regenerates every number in §2, §3 and §6 from the run directories,
  including the positional table, the Fisher and McNemar tests and the censoring diagnostic.
* **`tools/export_release_csv.py`** and **`release/per_task.csv`** — per-task metrics for all 96 task-runs,
  35 columns. The exporter enforces a *positive* field allowlist, so a field added upstream is excluded
  until reviewed rather than published by default; the traces themselves are never released, as they contain
  repository content.
* **Pre-registrations** for each experiment, committed before the corresponding run or submission, with
  readings fixed in advance.

The published CSV's `n_edit_arg_loss` column sums to 117, so the central claim of this paper is
recomputable from the released data alone.
