---
id: lit-aider2025-editformats
title: Aider edit formats and per-model editing-format defaults
authors: [aider.chat]
year: 2025
url: https://aider.chat/docs/more/edit-formats.html
topics: [edit-reliability]
relevance: high
read: partial
date_added: 2026-10-29
---

Migrated 2026-10-29 from `research/2026-10-28-literature-review.md` §3 (page read via summary; retrieval 2026-10-28). Related: https://aider.chat/docs/llms/editing-format.html and the agentpatterns.ai summary of Diff-XYZ.

## Takeaway
Switching GPT-4 from strict unified diff to search/replace blocks raised its edit-benchmark score 26% -> 59% with no model change. Diff-XYZ (via the same summary): search/replace beats unified diff for larger models while small open models gain almost nothing from any format change. Aider defaults lesser-known models to whole-file format "since it is the easiest format for an LLM to use".

## Reported results
| Quantity | Value | Setting | Where |
|---|---|---|---|
| GPT-4 edit benchmark, unified diff -> search/replace | 26% -> 59% | aider benchmark | edit-formats page |

## Relevance
`edit_file` already is search/replace; the failure we measured (C-004) is the model emitting an unterminated literal in the tool-call syntax, which no in-tool format change fixes. Single-argument routes (`write_file` whole-file for small files, `run_command` heredoc) sidestep the multi-argument slip, which is C-005.

## Ideas to test
- Count `write_file` losses in EXP-028 (0 of 14 in EXP-024) to confirm the single-argument tools stay loss-free on the v24 tree.

## Caveats
Industry bug reports (Claude Code Edit rejections, Cursor whole-file rewrites after failed edits, Copilot replace reporting success without writing) are anecdotes, not measurements.
