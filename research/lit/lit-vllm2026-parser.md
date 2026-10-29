---
id: lit-vllm2026-parser
title: vLLM gemma4 tool parser defects (issues #38910, #42696, #47906, #44522; PRs #47909, #54778)
authors: [vllm-project]
year: 2026
url: https://github.com/vllm-project/vllm/issues/38910
topics: [edit-reliability, tools]
relevance: high
read: partial
date_added: 2026-10-29
---

Migrated 2026-10-29 from `research/2026-10-28-literature-review.md` §6 (issue pages read via summary, 2026-10-28; comment dates not recorded).

## Takeaway
Open and recently fixed defects in the gemma4 tool parser: streamed tool arguments corrupted (#38910, HTML-like content in `write_file` content), streaming failures under concurrency producing invalid JSON arguments (#42696), bare values returned as strings (#47906 / PR #47909), raw `<|` `|>` tokens leaking (#44522), openers that omit `call:` (PR #54778). A third-party guide recommends non-streaming first and shallow argument schemas.

## Relevance
Our unterminated-literal loss (C-004) is consistent with argument corruption in the parser path, not only with model slips. The harness pins the vLLM build, so the reachable mitigation is routing long edits through a single-argument call (C-005). The error string we see ("mandatory input parameters are not present") is emitted by the ADK/harness tool layer, not vLLM.

## Ideas to test
- None we can run (serving is fixed). Cite in the paper's mechanism section with the issue numbers.

## Caveats
Issue reports, not controlled measurements; the competition's patched vLLM 0.19.1 may or may not include the fixes.
