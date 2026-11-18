---
id: kg-paper-757562-derived-data-ruling
topic_id: 757562
title: "May we publish a derived PatchGraph-QA JSONL (graph-relative Q&A) for the Paper Track?"
author: VíctorAndrade (topic author); Elan Markowitz (reply)
author_role: topic author is a participant; Elan Markowitz's reply is treated as a host ruling in our notes, to be confirmed against the competition rules page
credibility: [M] for the topic author; reply text read via CLI, high credibility as a rules answer if the role holds
topics: [rules, paper, data-release]
first_seen: 2026-11-17
last_checked: 2026-11-17
---

# 757562: may a derived QA JSONL be published on the paper track

Topic posted 2026-11-10 01:31 UTC by VíctorAndrade, asking four questions about publishing derived, graph-relative
Q&A items. Reply 3553006 from Elan Markowitz, 2026-11-10 19:25 UTC:

1. Yes, that is fine. Releasing the derived data only with linking via task id metadata is "perfect".
2. Yes, that is okay.
3. If it is just for verification or reproducibility, that is fine.
4. Yes, that is fine too; (1) is allowed and probably preferable.

The author then released **613 derived QA items**, each linked to its source task via `task_id`, in a public
repository (comment 3553040, 2026-11-10 20:31 UTC).

## Relevance

- Not a submission change. It is a rules point for our release path. Our plan (plan.md:52) says competition
  data never enters any release; this reply says derived items keyed by task id are acceptable on the paper track.
  The lead should decide whether our `export_release_csv.py` allowlist should stay stricter than the ruling.
- The reply is limited to this paper-track topic; it does not say whether the same applies to the main track.
