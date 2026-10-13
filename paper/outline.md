# Paper track outline (due Nov 12; draft outline by Oct 20 per plan §7.3)

Primary study: thinking budget × tool-argument discipline under a hard 32k / 12 h regime (E2 + E3 + E4).
Backup: taxonomy of agent failure modes (spin, malformed calls, overflow, compaction loss) and mitigations (E1, E7, E10, E11).
Best New Resource angle: release `tools/analyze_traces.py` + `tools/estimate_budget.py` + per-task CSVs (metrics only).

Sections (≤ 3,000 words): problem & constraints · method (configs, cohorts, seeds) · results (tables from
`experiments/EXP-*/aggregates.json`, per-repo breakdown, CIs) · cost-aware recommendation (tokens per resolved task)
· limitations (public↔hidden gap) · release list (configs, cohort ids, zip SHA256s, LB scores).
Figures land in `paper/figures/`; released CSVs in `paper/release/`.
