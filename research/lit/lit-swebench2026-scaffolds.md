---
id: lit-swebench2026-scaffolds
title: Minimal scaffolds at the frontier (SWE-bench Bash Only, mini-SWE-agent, vals.ai, codesota)
authors: [swebench.com, mini-swe-agent docs, vals.ai, codesota]
year: 2026
url: https://www.swebench.com/bash-only.html
topics: [prompt, tools]
relevance: medium
read: partial
date_added: 2026-10-29
---

Migrated 2026-10-29 from `research/2026-10-28-literature-review.md` §2 (leaderboard and docs pages via summary, 2026-10-28).

## Takeaway
mini-SWE-agent (a ~100-line bash-only ReAct loop, no tool schema) is the SWE-bench team's own harness; secondary reports put Claude Sonnet 4 at ~65% and Gemini 3 Pro at >74% on Verified through it; a vals.ai archive lists Opus 5 + mini-SWE-agent first at 97% (September 2026). Scaffold choice moves a frontier model by several points (Opus 4.5: 76.8-80.9% by framework, per codesota).

## Relevance
The harness fixes our scaffold; the lesson transfers to the prompt: shorter, fewer rules, one path. The 0.24 prompt is 3,240 bytes; ours was 12,795 (C-009, D-001).

## Ideas to test
- None beyond D-002's adoption of the short tree.

## Caveats
Frontier models; secondary numbers; no time cap.
