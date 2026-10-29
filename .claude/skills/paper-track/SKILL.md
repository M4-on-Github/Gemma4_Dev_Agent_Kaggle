---
name: paper-track
description: The paper-track Writeup - rubric, limits, schedule, what the draft already contains, sourcing rules for every number, and the release rules for CSVs and code.
user-invocable: false
---

# Paper track

Competition `gemma-4-developer-agent-paper`. Deadline **2026-11-12 23:59 UTC**; internal target Nov 11 (24 h margin). The user submits the Writeup through the Kaggle UI. `plan.md` §7 is the plan of record; `paper/outline.md` the outline; `paper/writeup-draft.md` the draft.

## Rubric (0-5 each) and how we score it

| Criterion | What earns it here |
|---|---|
| Novelty | A mechanism nobody has published for this harness: the `edit_file` lost-argument failure (positional, unterminated literal, ~38% of calls), why the obvious detector misses it, and a quantified budget/time-cap trade-off for a small model under a 12 h regime. Check `research/INDEX.md` before claiming novelty. |
| Quality / generality | Per-repo breakdown, paired designs on fixed cohorts, CIs, pre-registered readings, held-out behaviour, the public-LB noise measurement. |
| Relevance | Recommendations are config-level and reusable by any team on this harness. |
| Verifiability | Released configs, cohort ids, zip SHA-256s, LB scores, analyzer code, per-task CSVs from `export_release_csv.py`, exact commands next to every number. |
| Clarity | <= 3,000 words, 4-6 figures, one summary table, plain words from our own numbers. |

## Contributions, as the draft stands (2026-10-29)

1. The lost-edit mechanism and the corrected detector (sections 1-3; C-004). Measured, not inferred.
2. A pre-registered paired test of a prompt-level mitigation (section 4, stub). EXP-025 was underpowered (6 affected tasks); EXP-028 Arm R vs RH is the replacement measurement on the adopted tree and is complete but unanalyzed. Section 4 is written only from its critic-accepted result.
3. The never-edited failure class and why a call-index deadline cannot reach it (section 5).
4. The LB noise floor (two identical uploads differ by >= 3 tasks 42% of the time; the rank-3 team's v17 drew 0.17 and 0.13) and the time-cap contrast (#8 at 4.5 min 7/58 vs the same bundle at 8 min 14/58; #11 pending).
5. Best New Resource: `tools/analyze_traces.py`, `tools/estimate_budget.py`, `tools/run_forensics.py`, per-task CSVs.

Word budget: 2,716 used of 3,000; section 5.2 is the most compressible.

## Sourcing rules

- Every number is traceable to: a critic-accepted EXP section, a `submissions.md` row, or a tool command recorded in `paper/` next to the number. Numbers from EXP files whose results the critic has not reviewed are labeled "pre-registered, pending review" or left out.
- Pre-registered readings are cited from the EXP file, never restated in the paper.
- The rank-3 team's bundle and `runs.jsonl` are Apache-2.0 and credited by name wherever used; our contribution is the measurement and the one-variable contrast, and the paper says so.
- No task text, repository snippet, patch, trace excerpt, or hidden-task identifier appears in `paper/`. Task ids from the public set are allowed.
- Figures regenerate from a script in `paper/figures/` or `tools/`; the command is recorded in the figure caption source.

## Release

- `python -I -X utf8 tools/export_release_csv.py runs/<EXP> ... --out paper/release/<name>.csv` is the only path to a per-task file. Its field list is a positive allowlist; do not extend it without the lead's sign-off.
- The release list in the paper names: configs (tree paths and commits), cohort id files, zip SHA-256s, LB scores and dates, analyzer tools, CSV files.
- Apache-2.0 LICENSE is at the repo root; no competition data anywhere in the repo (the hygiene check enforces it).

## Schedule

| Date | Deliverable |
|---|---|
| Oct 30 | EXP-028 analyzed and critic-reviewed; section 4 drafted from it |
| Nov 1 | All experiments the paper cites are run; #11 and the next upload read |
| Nov 5 | Full draft with figures; internal rubric review (critic, `full` tier on the draft's claims) |
| Nov 9 | Numbers frozen; `paper/release/` CSVs exported; final edit |
| Nov 11 | User submits the Writeup |

## Writing

Plain words, short sentences, one idea each. Lead each section with the finding, then the evidence, then the caveat. State what the evidence does not show. Mark inference as inference. No filler, no generated-sounding phrases, no claims the EXP file does not license.
