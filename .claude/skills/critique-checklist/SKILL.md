---
name: critique-checklist
description: Review tiers (prereg, light, full, direction), audit checklist, re-run rules, synthesis questions, writing guidelines and verdict format for reviewing a pre-registration or a finished experiment before it moves a claim or an upload.
user-invocable: false
---

# Critique checklist

Review one pre-registration, one finished experiment, or one direction. Audit it from what is committed and from the local run directories, then explain it against everything else the logbook knows.

## Tiers

The lead names the tier. If it didn't, pick one and say which.

- **prereg**: a pre-registration before push or upload, dispatched for arms above 1 GPU-hour and for every upload (screens and zero-GPU work are not reviewed before they run). No results exist. Check P1-P6 below. Under 400 words. Verdict `ready` or `needs-work`.
- **light**: infrastructure, packaging, byte-identical reproductions, and results whose numbers can't change any claim's status. Audit checks 1, 2, 3 and 8 only. No synthesis. Under 400 words.
- **full**: everything that moves a claim to supported/refuted/contested, decides an upload tree, or goes into the paper. All audit checks, synthesis.
- **direction**: dispatched on a D-NNN. No audit, no files. Answer in your report, under 300 words: the weakest assumption and what evidence would test it; public evidence (kg-, lit-, EXP-) that points the other way; what a top-5 team on this LB would most likely do instead; one option the proposal didn't consider.

## Re-review

When `critic.md` already exists for this experiment, check only the previous Required fixes plus anything the fixes changed. Append a dated `## Re-review YYYY-MM-DD` section with the new verdict and update the frontmatter `verdict`. Keep the earlier text.

## Pre-registration checks (prereg tier)

- **P1 Blind and complete.** The readings table covers blank/crash, underpowered, both directions, and each row names the decision it drives (next arm, upload tree, revert). A row with no threshold, or a threshold in raw counts where the endpoint is paired ("B worse than A"), is a defect: EXP-025 §9.3 row 6 fired on its letter.
- **P2 Prediction stated.** An expected number or range is written before the run (resolve, rate, projected hours, or k of 58), with what would refute it.
- **P3 Endpoints match the instruments.** Every endpoint is a field `analyze_traces.py` or `run_forensics.py` emits, or the EXP names the exact command that computes it. The statistic is paired where the arms share ids.
- **P4 Power.** The affected-event count that makes the contrast readable is stated, and the design does not rely on resolves unless powered for them (dev-48 MDE on resolves is ~10 of 48; LB MDE ~4 of 58).
- **P5 Budget.** For any tree above 4.5 min: the projection is measured mean x 120 + overhead against ~10.5 h, the override is written in §2, and the cost of a blank slot is accepted explicitly. For GPU arms: GPU-hours stated against the weekly 30.
- **P6 One variable.** The arm differs from its comparator in the one thing the title names; the diff method (anchored edit, `diff -r`) is stated and the comparator exists on disk.

## Audit (finished experiment)

1. **Pre-registration order.** `git log --follow` on the EXP file: the readings commit precedes the push time or upload time recorded in §8, and `git diff <prereg-commit> HEAD -- <file>` only appends below the `---` line (plus §7 and §8). Any change above the line is a finding, whatever the result.
2. **Cohort and arms.** `summary.jsonl` task ids equal the cohort file the EXP's `**Cohort:**` line names (dev-48, or smoke-8 for a screen) in every arm; a smoke-8 screen that reads resolves as an endpoint is a finding; `eval_config` as run matches §2; the zip sha in the kernel equals §2's.
3. **Numbers regenerate.** Re-run `tools/analyze_traces.py` on `runs/<arm>` with the cap and call values from §2 and compare with the EXP's tables; recompute each McNemar/Fisher/Wilson from the stated counts. Free, so always do it when the run directory exists; if it does not, say so and mark `verified: inspected`.
4. **Readings applied as written.** Identify the first matching row yourself before reading the experimenter's §9, then compare. A row applied out of order, a threshold reinterpreted, or a result read "in the predicted direction" below its MDE is a finding.
5. **Statistics.** Paired tests on paired data; no two independent rates on the same 48 ids; multiplicity acknowledged when a table has many rows; an exploratory result is labeled as one and not carried into the claim.
6. **Budget arithmetic.** Projected hidden-set hours from the measured mean and overhead; the fixed overhead is not forgotten (submission #2 died at a 11.34 h projection that omitted it).
7. **LB readings.** A one-draw move is compared with the ~4-task MDE and with the series on the same 58 tasks; the LB keeps best-of, so "our score" is the best row, not the latest.
8. **Scope and hygiene.** The conclusion claims no more than §5 licenses. No competition data, trace excerpt or repo snippet is in any committed file. Prompts remain repo-agnostic. Ported material is credited.
9. **Reproducibility.** Candidate trees were produced by a tool from committed sources; the zip sha reproduces from LF blobs; the exact commands in §6 run.

## Re-run rules

- Re-running `analyze_traces.py`, `run_forensics.py`, `estimate_budget.py`, `regrade_patches.py` and the stats scripts is free: do it.
- Never order a GPU re-run or a new kernel. If one is needed, list it under Required fixes with the question it answers.
- Never upload anything or touch `submission/`.

## Synthesis (full tier)

- Does the result agree with the claim's sources (lit-, kg-, EXP-) and with earlier runs? Where does it conflict?
- Why did it come out this way? Point at the mechanism: which cap bound, which tool failed, which phase ate the wall-clock, which tasks moved.
- What else could explain it? Rank the explanations.
- What is the cheapest experiment that tells the leading explanations apart (zero-GPU first)?
- Which other claims does this strengthen, weaken or suggest? Does it change the next upload tree or the paper?

## Writing

The lead reads every `critic.md`, so write for a reader with the EXP file open.
- Don't restate the method or results. Refer to sections.
- Lead with the finding, then the one piece of evidence that settles it. Quote the decisive line of a command's output, not the whole output.
- A check that passed gets one line. Spend words on what failed, what surprised you, and what the lead should do next.
- Numbers over adjectives. Cite IDs. Mark inference as yours. Cite task ids and counts, never trace contents.

## Output: `experiments/EXP-NNN/critic.md`

```markdown
---
id: EXP-NNN-critic
exp: EXP-NNN
tier: prereg | light | full
verdict: ready | accepted | rejected | needs-work
verified: inspected | regenerated
date: YYYY-MM-DD
---

## Verdict
<one paragraph: what the evidence supports, as a claim the lead can copy>

## Audit
<numbered, matching the list above: pass / fail / n/a, with evidence. Any re-run: command, result>

## Analysis            (full tier)
<ranked explanations, citing IDs. Mark speculation as such>

## Suggested next      (full tier)
<cheapest discriminating experiment; claims to add or revise; effect on the next upload tree and the paper>

## Required fixes
<only for needs-work / rejected>
```

- `ready`: a pre-registration may be pushed or uploaded.
- `accepted`: every applicable audit check passed.
- `needs-work`: fixable issues, including missing evidence the experimenter should produce without GPU.
- `rejected`: the result is wrong, or the claim isn't supported.
