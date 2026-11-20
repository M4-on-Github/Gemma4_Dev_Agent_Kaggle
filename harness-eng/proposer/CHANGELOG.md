# Proposer harness changelog

One entry per round: what the proposer's edits did, what the proposer reported about its own
instructions, and the change made to `PROPOSER.md` because of it.

| Version | Date | Change | Why |
|---|---|---|---|
| v0 | 2026-11-18 | (no file) proposals written by the operator session from `directions.md` | rounds R-001 to R-003; 0 of 6 read tweaks kept; several cited the Kaggle synthesis instead of cluster traces |
| v1 | 2026-11-18 | first written harness: evidence from cluster traces on 3 or more tasks, pattern counts, reference-patch comparison, countable process endpoint | the user asked for the recursive form; v0's proposals were not tied to counted trace patterns |
| v1.1 | 2026-11-18 | added a facts section: HARNESS_README pointer, compaction inferred from prompt_tokens drops, budget_warning at call 18, logs duplicate traces, which cap counts to quote | the first v1 proposer (31B R-003) reported each as missing; its proposals (thoughts out of history; scratch code inline, not via write_file) are queued, results pending |
| v1.2 | 2026-11-18 | new rule 6: count miss classes and aim at least one edit at the largest; facts: reference patch format, own scratch dir, how to validate a tree, snapshots are tarballs | the E4B R-004 proposer counted wrong file as the largest class (18, 12, 11 of 56) and targeted it with neither edit; it also reported the listed gaps and that the two proposers overwrote each other's scratch files |
| v1.3 | 2026-11-18 | facts: other runs of the same model may be read; io.open on the host; directions.md reasons are hypotheses | the E4B R-005 proposer (first under rule 6) aimed both edits at wrong file with counted search behaviour, found the backlog's 'edits the first grep hit' true on only 7 of 27, and asked whether reading other runs was allowed |
| v1.4 | 2026-11-18 | four edits per round (two process, two mechanics), each must name the screen tasks it should flip; new section on the screen | the user asked for a small screen and more ideas per round; results so far: 0 of 2 read proposer edits kept (thoughts out of history: 31B 15 vs 22, E4B 5.0 vs 6.0) |
| v1.5 | 2026-11-18 | rule 5 no longer freezes the tool list or the agent structure | the E4B R-007 proposer found code-graph tools registered by the harness with data on the cluster and reported that rule 5 blocked using them; the freeze was the operator's over-restriction, not a competition rule. Also from R-007: resolving sessions read the reference lines before the first edit in 90% against 36% for failing ones |
