---
name: logbook-conventions
description: Layout, IDs, frontmatter fields, ownership and evidence rules for this project's research logbook (knowledge/, research/, experiments/, submissions.md).
user-invocable: false
---

# Logbook conventions

## Layout and ownership

| Path | What | Written by |
|---|---|---|
| `knowledge/claims.md` | Claims ledger, `C-NNN` | research-lead |
| `knowledge/directions/D-NNN-<slug>.md` | Heilmeier direction proposals | research-lead |
| `knowledge/plan.md` | Next experiments in order, the next upload slot, waiting-on, not-pursued | research-lead |
| `knowledge/briefing.md` | One page for the user, with the calibration table | research-lead |
| `knowledge/user-decisions.md` | The user's standing decisions and predictions, quoted | research-lead |
| `knowledge/submissions/S-NNN.md` | Upload proposals; NNN is the `submissions.md` row the upload becomes | research-lead |
| `knowledge/submissions/S-NNN-result.md` | Upload outcome | submitter |
| `approvals/S-NNN.txt` | Approval: SHA-256 of the exact file to upload | the user only |
| `experiments/EXP-NNN-<slug>.md` | Pre-registration and results, one file per experiment | experimenter |
| `experiments/EXP-NNN/` | Candidate trees, derived text artifacts, `summary.jsonl` | experimenter |
| `experiments/EXP-NNN/critic.md` | Review | critic |
| `experiments/README.md` §3 | Hand-written experiment index row per EXP | experimenter |
| `submissions.md` | Upload log, one row per real upload | experimenter (pending row and score) |
| `notebooks/<expNNN_dir>/` | Built notebook and kernel metadata | experimenter |
| `submission/`, `tools/`, `tests/` | Shipping tree and dev tooling | experimenter |
| `research/lit/lit-<id>.md` | Paper and industry-source notes | lit-scout |
| `research/kaggle/digests/YYYY-MM-DD.md` | Dated digests | kaggle-scout |
| `research/kaggle/threads/kg-<id>-<slug>.md` | Notes on one thread, notebook or released bundle | kaggle-scout |
| `research/YYYY-MM-DD-<slug>.md` | Dated review notes (the two from 2026-10-28 predate this layout) | lead or scouts |
| `paper/` | Writeup draft, outline, figures, release CSVs | paper-writer |
| `plan.md`, `CLAUDE.md`, `README.md` | Plan of record and repo guidance | the user, or an agent on explicit request |

`knowledge/INDEX.md` and `research/INDEX.md` are generated after every write. Never edit them. Hooks block writes outside your own paths.

## Files

- Every logbook file under `knowledge/` and `research/` starts with YAML frontmatter. Keys are flat: `key: value` or `key: [a, b]`.
- `id` must match the filename. Dates are absolute `YYYY-MM-DD`.
- `topics` takes values from: `budget` (time/call caps, 12 h projection), `prompt`, `edit-reliability`, `tools`, `sampling`, `lora`, `multi-agent`, `selection` (best-of-N), `noise` (LB/dev variance), `grading`, `paper`, `rules`.
- EXP files keep their existing shape (no frontmatter): header lines `**Date:**`, `**Type:**`, `**Pre-registered:**`, `**Serves:**`; numbered sections with blind readings in a section whose heading contains "readings"; results appended below a `---` line. The experiment-protocol skill has the template.

## Linking

- Cite by ID inline: `C-004`, `D-002`, `S-012`, `EXP-028 §4`, `lit-2604.05407 §3`, `kg-rank3-apache §2`, `submissions.md` row 8, `plan.md` §5.8.
- Number IDs by taking the next free number. Glob the folder first and never reuse a number.

## Evidence rules

- Papers, Kaggle posts and released bundles can only propose claims (status `hypothesis`).
- Only an experiment with critic verdict `accepted` can move a claim to `supported` or `refuted`. A conflicting accepted result makes it `contested`.
- The migrated record (everything before 2026-10-29) carries its evidence under `migrated-evidence:` and stays `hypothesis` until a critic backfill accepts it.
- A public-LB draw is one noisy observation (MDE ~4 tasks). It is recorded with its pre-registered reading; it never alone supports or refutes a claim about a sub-MDE effect.
- Record a number with its source and the command that produced it. If you did not see it, write `unknown`. Never estimate silently.
- Nothing from `runs/`, `data/` or `untrusted/` is quoted verbatim into a logbook file beyond task ids, counts, error strings and config values.
