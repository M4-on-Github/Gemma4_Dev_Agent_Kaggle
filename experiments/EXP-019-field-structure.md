# EXP-019 -- What the leaderboard's shape says about where 0.13 sits

**Date:** 2026-10-23
**Type:** zero-GPU analysis. No variable changed, nothing built, nothing submitted.
**Inputs:** Kaggle public leaderboard CSV pulled `2026-10-23T10:45:48` (3,505 teams);
`kaggle kernels list` vote counts; per-team `SubmissionCount` and `LastSubmissionDate` from the same CSV.
**Why it exists:** submission #5 scored 0.13 and the pre-registered reading (EXP-017 section 6) is
"uninformative". When a score carries no evidential weight of its own, the only remaining question it can
answer is a relative one: where does 8/58 sit in the field, and what does the field's shape say about what
is actually reachable?

---

## 1. A retraction first

In conversation on 2026-10-23 I reported that "about a thousand teams sit on exactly 10 tasks" and inferred
that this was **a fork cluster** -- a crowd of teams submitting one public baseline unchanged -- and therefore
that we were scoring **below the free starting point**.

**That was a binning artifact and the inference is withdrawn.** The histogram was built with
`Counter(round(s*58) for s in scores)`, and `round(0.17*58) = round(9.86) = 10` while
`round(0.18*58) = round(10.44) = 10`. Two distinct score bins were merged into one, roughly doubling the
apparent spike. Re-run on exact scores:

| score | tasks | teams | share |
|---|---|---|---|
| **0.17** | 10 | **567** | 16.2% |
| 0.15 | 9 | 490 | 14.0% |
| **0.18** | 11 | **433** | 12.4% |
| **0.13 (us)** | **8** | **359** | **10.2%** |
| 0.12 | 7 | 314 | 9.0% |
| 0.10 | 6 | 271 | 7.7% |
| 0.08 | 5 | 224 | 6.4% |
| 0.20 | 12 | 157 | 4.5% |
| 0.06 | 4 | 156 | 4.5% |
| 0.00 | 0 | 153 | 4.4% |
| 0.05 | 3 | 147 | 4.2% |
| 0.03 | 2 | 122 | 3.5% |

The largest bin is **16.2%, not ~29%**, and the distribution around it is a **broad smooth mode**
(9 -> 10 -> 11 tasks hold 14.0%, 16.2%, 12.4%), not a spike sitting on an otherwise empty axis. A fork
cluster would look like a spike. This one does not.

## 2. The submission-count test, which also fails to support the fork story

If 0.17 were mass-forking, its teams would pile up at `SubmissionCount = 1`. They do not -- the 0.17 bin is
spread across 1 to 6+ submissions with no concentration at 1 (bins of ~40-53 teams each at counts 3, 5, 1, 4,
2, 6). So **the fork hypothesis is not supported and is dropped.**

What the submission counts *do* show is a real and different pattern:

| bin | typical `SubmissionCount` |
|---|---|
| 0.17 (567 teams) | **low** -- 1 to 6 |
| 0.18 (433 teams) | **high** -- 7, 8, 9, 12, 17 |

**0.17 is where modest effort lands; 0.18 is where sustained iteration lands.** Sustained iteration buys
**one task**. That is the single most sobering number in this file: the teams grinding hardest in the public
field are one resolve ahead of the teams who barely tried.

We have 5 submissions and 8 tasks, which places us **below both groups** -- we have spent iteration without
yet buying the modest-effort outcome.

## 3. Where we actually stand

Our row: **RainM4, score 0.13, 8 tasks.**

* **1,686 teams strictly ahead (48.1%)**, 359 tied, the rest behind -> **~52nd percentile, the field median.**
* Previous standing was 0.12 = 7/58, rank 2322 of 3470, ~33rd percentile. **One task moved us 19 percentile
  points.** The field is so tightly packed through the middle that single resolves are worth enormous rank
  movement -- and are equally cheap to lose to noise.

Cumulative structure, which is what matters for target-setting:

| threshold | tasks | teams at or above | share |
|---|---|---|---|
| >= 0.24 | 14 | **4** | 0.1% |
| >= 0.22 | 13 | 39 | 1.1% |
| >= 0.20 | 12 | 196 | 5.6% |
| >= 0.18 | 11 | 629 | 17.9% |
| >= 0.17 | 10 | 1,196 | 34.1% |
| >= 0.15 | 9 | 1,686 | 48.1% |
| >= 0.13 | 8 | 2,045 | 58.3% |

**The top is thin and very close.** The leader is at 14/58; we are at 8/58. **Six resolves separate us from
first place.** This is not a competition where the frontier has run away -- it is one where nobody has solved
it, and 0.24 of 1.00 is winning.

Verified rivals: `muhammedidris28` 0.24 / 14 tasks / rank 3; `flexonafft` 0.22 / 13 / 19; `davis0178`
0.22 / 13 / 18; `honghanhhh` 0.18 / 11 / 232; `hitarthjain0` 0.18 / 11 / 320.

## 4. Public notebooks, by votes

| notebook | votes | author on LB? |
|---|---|---|
| `ryanholbrook/getting-started-gemma-4-developer-agent` | **1,812** | **no** |
| `flexonafft/gemma-4-budget-aware-coding-agent-v2` | 270 | yes -- 0.22, rank 19 |
| `romanrozen/gemma-eda-baseline-for-a-start-lb-top-1` | 232 | -- |
| `verracodeguacas/gemma-4-agent-budget-fit-single-agent` | 217 | -- |
| `lucifer19/black-cat-swe-agent-pack-instinct` | 141 | -- |
| `dmitriigluzdov/gemma-4-task-soundness-serving-and-evaluation` | 113 | -- |
| `zhukovoleksiy/gemma-4-walkthrough-findings-submission` | 96 | -- |

The starter notebook has ~7x the votes of anything else and its author never submitted, so **its score is
not readable from the board** and the "what does the free baseline get you" question stays open. It is
answerable cheaply (read its `eval_config` and prompt shape -- zero GPU) and is now the main open thread
here. `flexonafft` is the one notebook whose author's score we can verify, and at **0.22 / rank 19** it is
the highest-value unread artifact in the project, alongside `davis0178`'s (0.22, rank 18, already downloaded
and still unread).

## 5. What this changes

**Nothing about submission #5's reading.** EXP-017 section 6 stands: 0.13 is uninformative about the four
changes, and the pre-registered next action (buy the E0 dev-48 **repeat baseline**, EXP-009 Part C4) is
unchanged. Field structure cannot rescue a submission whose likelihood ratio is 1.07 : 1.

What it does change is the **framing of the target**:

1. **The "we are below the free baseline" claim is withdrawn** (section 1). We are at the median.
2. **+2 tasks reaches the mode (0.17, top 34%). +4 reaches top 5.6%. +6 is first place.** The whole contest
   fits inside six resolves, which is only ~1.5x our measured MDE of ~4 LB tasks. This is simultaneously
   encouraging and the reason every single-variable LB test we have tried has been unreadable.
3. **Iteration demonstrably buys ~1 task in this field** (section 2). That is a strong argument against
   spending further daily slots on LB iteration and for spending GPU quota on the same-config noise floor
   instead -- we cannot tell a 1-task gain from nothing, and 1 task is what effort is worth here.
