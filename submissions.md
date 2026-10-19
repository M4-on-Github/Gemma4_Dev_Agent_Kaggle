# Submissions log

Per plan.md §5.8: date, git tag/commit, zip SHA256, dev-48 score, LB score, scoring wall time, notes.
One row per actual Kaggle leaderboard submission (not every packed zip — only ones uploaded).

| # | date | commit | zip sha256 | dev-48 score | public LB score | notes |
|---|---|---|---|---|---|---|
| 1 | 2026-10-18 | ee1b209 (prompt reverted to e1d61fb state at pack time, see EXP-001-baseline.md config) | `c2bf932104e9e544254d28a0efd693c6a1d85e4b82ff0923ad4f99bfe78e4a07` | 22.9% (11/48, Wilson 95% CI 13.3–36.5%) | 0.06 = 4/58 public tasks (graded 2026-10-19) | E0 baseline. Local→LB drop ratio ~3.3x, in line with precedent, not itself anomalous. Absolute score sits below a known public reference-config's reported score on the same hidden tasks — see plan.md §6.0.3/experiments/README.md for the follow-up plan (budget-shape match against a public bundle before further LOCATE work). |
