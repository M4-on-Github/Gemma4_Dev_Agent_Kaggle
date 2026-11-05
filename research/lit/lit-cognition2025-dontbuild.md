---
id: lit-cognition2025-dontbuild
title: Don't Build Multi-Agents (Cognition)
authors: [Walden Yan, Cognition]
year: 2025
url: https://cognition.com/blog/dont-build-multi-agents
topics: [multi-agent]
relevance: medium
read: partial
date_added: 2026-11-05
---

Industry write-up fetched 2026-11-05 (the old cognition.ai URL redirects to cognition.com); published June 12, 2025 per the page. Read through the fetch tool; quotes are the extractor's.

## Takeaway
The best-known argument against parallel sub-agents that act, stated as design reasoning with no data. Its two principles map exactly to our shared-working-directory constraint.

## Method
Two principles: "Share context, and share full agent traces, not just individual messages" and "Actions carry implicit decisions, and conflicting decisions carry bad results".

## Reported results
| Quantity | Value | Where |
|---|---|---|
| Quantitative evidence | none; "design reasoning and anecdotes" | whole page |
| Acceptable sub-agent | Claude Code sub-agents run sequentially and are "usually only tasked with answering a question, not writing any code"; their investigation stays out of the main history | extractor quote |
| Context compression | a separate (possibly smaller, fine-tuned) model compresses history; described as hard | extractor quote |

## Relevance
Part B/D. The practice it endorses (read-only question-answering sub-agent, one writer) is the only orchestrator shape that does not conflict with `submit_patch` diffing the whole workspace (EXP-007 §design). Whether it helps at 32k is unmeasured here.

Transfers to our constraints: yes as a constraint on design (one writer), no as evidence of a gain.

## Ideas to test
- (mine) Claim: moving file exploration into a read-only `agent_tool` worker reduces root-agent prompt tokens at the first edit by at least 30% but delays the first edit by 2 or more calls; both are readable from traces on smoke-8.

## Caveats
No data; frontier models; opinion.
