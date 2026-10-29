---
id: lit-icml2026-agentlens
title: AgentLens (ICML 2026) - blind retries, regression cycles and lucky passes in agent trajectories
authors: [unknown]
year: 2026
url: https://icml.cc/virtual/2026/77962
topics: [noise]
relevance: medium
read: abstract
date_added: 2026-10-29
---

Migrated 2026-10-29 from `research/2026-10-28-literature-review.md` §1 (secondary summary; locators not recorded; verify before citing).

## Takeaway
10.7% of passing OpenHands trajectories show blind retries, regression cycles or missing verification; "lucky pass" rates range 0.5-23.2% across backends.

## Reported results
| Quantity | Value | Setting | Where |
|---|---|---|---|
| Passing trajectories with blind retries / regression cycles / missing verification | 10.7% | OpenHands | summary |
| Lucky-pass rate | 0.5-23.2% | across backends | summary |

## Relevance
LB noise has a mechanistic floor (C-001): one draw cannot adjudicate a prompt change.

## Ideas to test
- None beyond C-001's noise measurement; cite in the paper's noise section.

## Caveats
Frontier backends; different scaffold.
