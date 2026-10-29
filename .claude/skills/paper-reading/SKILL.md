---
name: paper-reading
description: How to find, read and write a verifiable note on a paper or industry source for research/lit/.
user-invocable: false
---

# Paper reading

## Finding

- Prefer arXiv for papers (abstract page, then `arxiv.org/html/<id>` or the PDF). For industry sources (vLLM issues, tool docs, vendor write-ups, leaderboards) fetch the page itself and record the retrieval date.
- Before writing, Glob `research/lit/` and read `research/2026-10-28-literature-review.md`; update an existing note rather than duplicate it.

## Hard rules

- Every claim, number and method step carries a locator: `§3.2`, `Table 2`, `Fig. 5`, `Alg. 1`, an issue comment date, or a page anchor. If you can't point to where it is, leave it out.
- Copy numbers exactly as printed, with units and the benchmark they are on. Never convert, round or estimate.
- Keep what the source shows separate from what you infer. Inferences go only under "Relevance" and "Ideas to test", marked as yours.
- If you read only the abstract or part of the source, say so in `read:` and don't fill sections you didn't read.
- Translate every idea into this harness's terms: a config value, a prompt rule, a tool route, a measurable rate from `analyze_traces.py`. Ideas that need training, custom tools or serving changes are recorded as out of reach with the reason.

## Note template: `research/lit/lit-<id>.md`

Non-arXiv sources: `lit-<firstauthor-or-vendor><year>-<word>` (for example `lit-vllm2026-38910`, `lit-aider2025-editformats`).

```markdown
---
id: lit-<id>
title: <exact title>
authors: [<first author>, <...>, <last author>]  (or the vendor / repo)
year: YYYY
url: <url>
topics: [budget | prompt | edit-reliability | tools | sampling | lora | multi-agent | selection | noise | grading | paper | rules]
relevance: high | medium | low
read: full | partial | abstract
date_added: YYYY-MM-DD
---

## Takeaway
<2-3 sentences: what this source offers us>

## Method
- <step> (§x)

## Reported results
| Quantity | Value | Setting | Where |
|---|---|---|---|

## Relevance
<which of our measured problems it speaks to (C-NNN), and why — your inference>

## Ideas to test
- <falsifiable idea: change X in the config/prompt, expect rate Y to move by ~Z, because §w>

## Caveats
<assumptions that don't hold here: frontier model, custom scaffold, training needed, no time cap>
```
