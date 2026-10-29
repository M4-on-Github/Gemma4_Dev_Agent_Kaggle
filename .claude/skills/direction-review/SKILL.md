---
name: direction-review
description: How the research lead ranks claims, budgets GPU-hours and upload slots, writes Heilmeier direction proposals, updates claims, proposes uploads, and writes the plan and briefing.
user-invocable: false
---

# Direction review

## Ranking claims

Rank open claims by expected public-LB tasks gained per unit of the two scarce resources: L4x4 GPU-hours (30/week) and upload slots (one per UTC day, ~34 left to Dec 2 including 8 reserved for the finals pair).
- Expected gain = P(success) x tasks of 58 moved on the hidden set. Write the estimate in the claim's `expected gain`, with the source of P.
- Prefer measurements that are readable: a dev-48 process endpoint (compliance, loss rate, time profile) is readable at n = 48; a resolve-rate contrast is not (MDE ~10 of 48); a single LB draw reads only effects of >= 4 tasks.
- Prefer zero-GPU analysis of owned data over a new arm when it answers the same question.
- **Adaptive tree, not a screen.** Each upload slot is chosen by the reading of the last one; thirty independent single-knob draws have no power (EXP-022 §3).
- **Explore quota.** Of every four experiments, at least one tests an idea that is not the public frontier's design: a paper's mechanism, a parked lever re-examined with new data, a different tool route. Expected-value ranking alone always picks the safe reproduction.
- **Nothing evaporates.** Every digest "Suggested claims" entry and every `relevance: high` paper note becomes a claim or a "Not pursued" line in `knowledge/plan.md` with the reason.
- **Paper track has its own clock** (Nov 12). Rank its experiments by what the writeup needs, not by LB gain.

## Updating claims

After a critic verdict:
- `accepted`: set the claim to supported or refuted per the result and add a dated `history` line.
- `needs-work` or `rejected`: leave the status, note it, decide whether the fix is worth the cost.
- A migrated claim stays `hypothesis` until a backfill review accepts its evidence.

## Direction proposal: `knowledge/directions/D-NNN-<slug>.md`

Write one whenever a direction should start, continue, pivot or be killed, and at least weekly. The user approves it before work starts. Before it goes to the user, dispatch the critic (`direction` tier) and put its answer in Options with your response.

```markdown
---
id: D-NNN
title: <short>
decision: start | continue | pivot | kill
status: proposed | approved | rejected | active | done | killed
track: main | paper | both
claims: [C-NNN]
date: YYYY-MM-DD
---

## What are we trying to do?          <plain words>
## How is it done today?              <public frontier with kg-/lit-/EXP- refs and numbers>
## What's new in our approach?
## Options                            <at least two, with your recommendation, the strongest argument against it, and the critic's dissent>
## Expected score impact              <tasks of 58, with P(success) and its source>
## Risks and kill criteria            <the measurable result that ends this direction; the blank-slot cost if any>
## Cost                               <GPU-hours, upload slots, days>
## Midterm check                      <what we should see after the first experiment or draw>
## Final check                        <what "done" looks like>
```

## Plan: `knowledge/plan.md`

Rewrite every loop; keep it under a page.

```markdown
---
id: plan
updated: YYYY-MM-DD
direction: D-NNN
---

## Next experiments (in order)
| # | Claim | What it tests | Endpoint | Expected gain | GPU-h | Why now |

## Next upload slot
<tree, sha if packed, the EXP whose readings govern, what each reading does to the slot after>

## Waiting on
<user decisions, running kernels, pending reviews, pending LB grades>

## Not pursued
- <claim or idea> — <one-line reason, with the ID of the evidence>
```

## Briefing: `knowledge/briefing.md`

For the user. One page, plain words, rewritten every loop. Each number carries its ID.

```markdown
---
id: briefing
updated: YYYY-MM-DD
---

## Where we stand
| Track | Ours | Frontier | Gap in tasks | Next move |

## What we learned
- <finding, and the mechanism in one or two plain sentences> (EXP-, C-, lit-, kg-)

## Open decisions
- <decision> — option A costs/gives ..., option B ... — recommended: ... — needed by: <date>

## Calibration
| EXP / upload | Predicted (pre-registered) | User's prediction | Actual | Held? |

## Worth your time
- <up to three logbook files and why>
```

## Upload proposal: `knowledge/submissions/S-NNN.md`

NNN is the `submissions.md` row this upload becomes. Name the exact file and its SHA-256, the EXP whose pre-registered readings govern the draw, and the budget projection. The user approves by writing `approvals/S-NNN.txt` with that hash; only then dispatch the submitter. The submit hook enforces all of this.

```markdown
---
id: S-NNN
date: YYYY-MM-DD
status: proposed | approved | submitted | declined
experiments: [EXP-NNN]
file: <path to the zip>
sha256: <hash of that file>
tree: <candidate dir>
max_time_minutes: <value>
projected_hours: <measured mean x 120 + overhead, with the source run>
gate_override: none | <justification>
---

## What changed vs the last upload      <one variable, or "package" named as such>
## Prediction                          <k of 58 expected, range, and the EXP section with the readings>
## Why this slot                       <what we learn or gain; what the next slot does under each reading>
## Risks                               <blank-slot probability and cost; anything not critic-accepted>
```
