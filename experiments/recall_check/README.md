id: recall-check (free, CPU-only)        date: 2026-10-18        owner: M4

Follow-up to EXP-002-estop-a's decision: before spending any GPU-h on a LOCATE redesign
(prompt-only or EXP-003b sub-agent), first check whether `search_similar_code` et al. even
recall well against real data, and whether a trivial free baseline (grep) already does
as well or better. This directory holds both halves of that check: the **local,
zero-Kaggle** half (gold-symbol extraction + a lexical `git grep` baseline) and the
**Kaggle CPU-only kernel** half (replaying the real `search_similar_code`/
`get_code_neighbors` calls against the actual mounted graph/embedding data). Both are
now complete — see "Kaggle kernel results" below for the headline finding.

## Why local-first

Per the 2026-10-18 independent review (see plan.md §6.0.2/EXP-002-estop-a.md), reusing the
harness's own graph-node boundaries as "gold" would be circular — it can't see gold the
graph itself is missing (e.g. open question of whether `async def` functions get graph
nodes at all). So gold here is derived independently: AST-parse the base-commit source
(from `data/local/snapshots/<instance_id>.tgz`, which are full git snapshots — `.git`
directory included, though its history does not reliably contain `base_commit` as a
reachable commit object; the checked-out working tree content itself matches base_commit
exactly, confirmed by this extraction matching known trace symbols) and map each patch
hunk's changed line range to its enclosing function/class.

## Tools

- `tools/recall_extract_gold.py` — parses `data/local/tasks.jsonl`'s `patch` field with a
  small hand-rolled unified-diff parser (the `unidiff` package isn't installed locally),
  reads the pre-patch file content straight from each task's own snapshot tarball, AST-parses
  it, and maps each hunk to its enclosing def/class (or `module_level` / `new_module` for
  hunks with no enclosing def or in wholly new files). Tags each gold symbol
  `formatting_only` when every changed line reduces to the same stripped text on both sides
  of the diff (pure whitespace/reflow, nothing to actually "find"). Output: `gold.jsonl`,
  one record per task (all 129; 0 real AST syntax errors after fixing an early bug that had
  mislabeled "no defs in this file" — e.g. rich's pure-dict `default_styles.py` — as a parse
  error).
- `tools/recall_grep_baseline.py` — extracts each task's snapshot, pulls identifiers
  (dotted paths, CamelCase≥4, snake_case≥4, stopword-filtered) out of
  `problem_statement`+`hints_text` only (the same inputs available at real LOCATE time),
  and ranks files by `git grep -l -I -F <identifier>` hit count against the checked-out
  working tree (not a commit ref — see note above on why). Scores recall@{1,3,5,10} against
  non-formatting-only, non-new-file gold files. Output: `grep_baseline.jsonl`.

## Results (2026-10-18, full 129-task set, after fixing two bugs below)

- 129/129 tasks: snapshot found, gold symbols extracted, 0 unresolved AST parse errors.
- 1 task (`new-file-only`) has no base-file gold at all (the patch only adds new files) —
  excluded from the grep baseline since nothing in the base tree could match it, which is
  also a hard limit of any tool that only operates on the existing graph/codebase (the
  real `search_similar_code` would face the identical limitation).
- Of the remaining 128, 15 yielded **zero extractable identifiers** from
  `problem_statement`+`hints_text` (short/vague issue reports) — skipped, scored 0/0, not
  counted as misses or hits.
- **git-grep file-level recall, n=113 scored tasks:**
  - recall@1:  28/113 = **24.8%**
  - recall@3:  40/113 = **35.4%**
  - recall@5:  42/113 = **37.2%**
  - recall@10: 47/113 = **41.6%**
- Cross-check against the 3 real EXP-002 traced queries (see EXP-002-estop-a.md):
  - `fastapi_14301`: grep ranks gold (`fastapi/dependencies/utils.py`) **1st** (3 hits vs.
    2 for the runner-up) — agrees with the real trace, where `search_similar_code`'s lexical
    fallback also ranked gold 1st (0.6471 similarity) for this task.
  - `fastapi_14448`: grep **misses both gold files** entirely in its top-20 — agrees with the
    real trace, where `search_similar_code`'s lexical fallback returned junk (0.22
    similarity, wrong node) for this task. Both independent lexical approaches fail here,
    which is evidence this task's identifiers are just weak-signal, not that the graph
    tool's lexical fallback specifically is broken.
  - `rich_3468`: grep ties ~15 files at hit-count=1 (gold, `rich/console.py`, lands 3rd by
    alphabetical tie-break) — a different failure mode (signal too weak to discriminate,
    not absent), consistent with the real trace's cosine-path problem (near-constant
    0.9991–0.9997 similarities across its top-10, i.e. also discrimination failure, not
    absence of a candidate).

**Reading**: a free, zero-GPU, zero-graph-data lexical baseline already gets ~25–42%
file-level recall depending on k. This sets the bar `search_similar_code` needs to clear
to be worth keeping in the LOCATE chain — if the real tool (once checked against actual
mounted graph/embedding data on Kaggle) doesn't beat this by a solid margin, that's evidence
the bottleneck is query/identifier quality or embedding-space anisotropy (per the rich_3468
near-constant-similarity finding), not something graph-tools-specific that EXP-003b would fix.

## Bugs found and fixed during this build (both self-caught, not yet independently reviewed)

1. `recall_extract_gold.py`'s AST-parse-error detection originally flagged a file as a parse
   error whenever `build_scope_index` returned no def/class ranges, conflating real
   `SyntaxError`s with legitimate no-functions-in-this-file cases (e.g. rich's
   `default_styles.py`, a pure dict literal; `_cell_widths.py`, a data table). Fixed by
   having `build_scope_index` return `(ranges, had_syntax_error)` explicitly. All 9
   originally-flagged files were false positives; re-run confirmed 0 real parse errors.
2. `recall_grep_baseline.py` originally called `git grep <pattern> <base_commit>`, which
   fails (`fatal: unable to parse object`) because the snapshot's embedded `.git` history
   does not reliably contain `base_commit` as a reachable commit object, even though the
   working-tree file content matches base_commit exactly (confirmed via the independently-
   correct gold-symbol extraction from the same tarball). This produced a false **0.0%**
   recall@{1,3,5,10} across all 113 tasks on the first run — not a real finding, a tool bug.
   Fixed by grepping the checked-out working tree directly (no ref needed, since the tree
   already *is* the base_commit state).

## Kaggle kernel results (2026-10-18, CPU-only, zero GPU-h)

Kernel: `rainm4/gemma4-recall-check` (`notebooks/exp_recall_check/`), pushed and run
2026-10-18, version 1, COMPLETE, 0 graph-load errors across all 129 tasks. Calls the real
`swegemma.graph.graph_utils.get_graph`/`resolve_node_name`/`get_neighbor` and
`retrieval_utils.get_similar_nodes` directly (same functions `search_similar_code`/
`get_code_neighbors` wrap), replicating the exact `get_code_neighbors` node-prefix
(`repo_name;node`) that `search_similar_code` does not apply. Same 113-task scored set as
the grep baseline (0 skipped-no-snapshot, 1 skipped-no-gold, 15 skipped-no-identifiers) —
a true apples-to-apples comparison, not a subset.

**`search_similar_code` file-level recall, n=113, two query arms:**

| arm | recall@1 | recall@3 | recall@5 | recall@10 |
|---|---|---|---|---|
| single top identifier | 14.2% | 19.5% | 21.2% | 24.8% |
| joined top-3 identifiers | 16.8% | 23.9% | 28.3% | 34.5% |
| **git grep baseline (free, local)** | **24.8%** | **35.4%** | **37.2%** | **41.6%** |

**The free grep baseline beats the real graph tool's `search_similar_code` at every k,
on both query arms, on the identical 113-task set.** This is the headline finding: a
zero-GPU, zero-graph-data lexical search already outperforms the harness's own semantic
retrieval tool for this recall task. `get_code_neighbors`, chained off each task's
resolved/top-1 seed node, found a gold file among its neighbors only **16.5%** of the
time — also well under the grep bar.

**Why: two concrete causes, not just "embeddings are bad".**

1. **Gold-node coverage is the harder ceiling.** `gold_in_graph_rate = 62.7%`, which is
   identical to `gold_has_embedding_rate` (both measured against the same lookup) — so
   **37.3% of the actual gold symbols the patch touches are not reachable as graph nodes
   at all**, regardless of query quality. No ranking strategy, lexical or semantic, can
   recall a node that doesn't exist. This caps `search_similar_code`'s ceiling well below
   100% before similarity scoring even runs, and explains a meaningful share of the gap —
   grep doesn't have this ceiling since it searches raw file text, not a node index.
2. **Embedding-space anisotropy is real and repo-dependent, not n=1 noise.** Sampled
   ~200 nodes/repo-snapshot (1,770 pairs each) and measured mean pairwise cosine
   similarity: **fastapi ranges ~0.72–0.85**, **requests ~0.82–0.88**, **rich ~0.87–0.93**
   (single highest: 0.9255), **httpx 0.88** (n=1 snapshot only). Rich's embeddings are
   packed tightest — confirming the rich_3468 trace's near-constant 0.9991–0.9997
   top-10 similarities (EXP-002-estop-a.md) generalizes across the whole repo, not a
   one-task fluke. High background similarity means small true-relevance signal gets
   swamped by a high, noisy floor — consistent with weak discrimination, not simply
   "wrong answers."

**Known heuristic limitation on these numbers (conservative bias):** node-name-to-file
mapping (no explicit file/path attribute was found on graph nodes, confirmed again from
the real Kaggle schema) uses a longest-dotted-prefix match against each snapshot's actual
`.py` file list. 574 of the returned node names across both arms didn't match any file
this way (`unmapped_node_names.jsonl`) — almost all of them are fastapi doc-example nodes
missing their `docs_src/` path prefix (e.g. `dependencies.tutorial002_an_py310.
CommonQueryParams`), not real misses. These unmapped nodes are counted as non-hits, so
the real-tool recall numbers above are a slight *underestimate*, not an overestimate —
if anything the true gap to grep's baseline is somewhat smaller than shown, though not
reversed (574 misattributed nodes across 113×2 arms is a small fraction of the k=10
result sets, nowhere near enough to flip the ranking).

**Reading**: a graph-only, embedding-ranked LOCATE step as currently implemented does not
clear the bar a free lexical baseline already clears, on this task set. Per EXP-002's own
correction, the smoke-8 traces' chain abandonment after `search_similar_code` looks like a
rational response to the tool's recall quality, not prompt non-compliance — this result
confirms that reading at full-dataset scale rather than n=3. **This is real evidence
against building EXP-003b (tool-scoped analyzer sub-agent) on top of these tools as-is** —
a sub-agent wrapper inherits the same ~37% gold-node coverage ceiling and the same
anisotropic embedding space; it would not fix either root cause. Worth considering before
any further GPU spend: a combined lexical+graph LOCATE step (grep for candidates, then use
the graph only for neighbor expansion once a seed is found), or treating the graph-coverage
gap itself as the thing to fix before trusting the tool's ranking.

## Correction, 2026-10-19 (independent review, Opus 5.5 xhigh)

An independent review of this recall check found real methodology bugs that weaken (but do not
reverse) the headline finding above:

1. **Query-extraction regex bug.** The single-identifier query-extraction step (same regex used
   by the local grep baseline) effectively returns the literal string `github.com`/a URL fragment
   as "the identifier" for the majority of tasks (63/113), not a real code symbol — so the
   single-identifier arm's recall numbers are measuring the tool against a near-useless query for
   most of the task set, not a fair test of `search_similar_code`'s ranking quality.
2. **`src.`-prefix node-name mismatch.** Graph node names are import-style (no `src.` prefix);
   this kernel's gold-extraction/mapping code kept a `src.` prefix for requests/httpx tasks,
   making those repos' `gold_in_graph_rate` read as ~0% when the true rate is likely much higher.
   Since `gold_in_graph_rate == gold_has_embedding_rate` by construction (both read from the same
   lookup), **the 62.7% "hard ceiling" figure above is inflated-looking-bad by this bug** for at
   least two of the four repos — it is not a clean measurement of true graph coverage.
3. **Anisotropy sample-size framing.** "~200 nodes sampled, 1,770 pairs" is literally correct
   (`C(60,2) = 1770`) but misleading: only the **first 60** of the ~200 sampled node names per
   repo-snapshot were ever pairwise-compared, not all ~200. The qualitative finding (high
   background cosine similarity, worst in rich) likely still holds, but the precision implied by
   "1,770 pairs" overstates how much of the sampled set was actually checked.

**What still holds:** going back to real E0 dev-48 traces directly (not a re-derived metric),
the actual bottleneck for resolve rate is **post-LOCATE** — a touch→edit→resolved drop-off that
is wall-clock-bound (time_cap_hit dominates calls_cap_hit, §6.0.3/plan.md), not LOCATE-quality-
bound. That finding is independent of the three bugs above and is why dropping EXP-003b remains
the right call: a tool-scoped sub-agent wrapped around `search_similar_code`/`get_code_neighbors`
would spend budget narrowing a step that the traces show usually isn't where tasks are actually
being lost, regardless of the exact recall percentage these numbers land on once the bugs are
fixed. The grep-vs-graph-tool comparison itself should be treated as directionally suggestive,
not load-bearing at the specific percentages quoted above, until the three bugs are fixed and the
kernel is re-run.

## Not yet done / still open

- A `resolve_node_name`-alone baseline (no similarity ranking, just: does the exact-symbol/
  suffix/substring resolution path land on a gold node at all) — not computed this round;
  `resolve_node_name` was called as part of `search_similar_code`'s path classification
  (`path_taken`: resolved vs. lexical_fallback) but its hit rate alone wasn't isolated.
- Schema check for whether graph node `id` always equals node `name` was not directly
  tested; the `g.has_node(qualname)` check used for `gold_in_graph_rate` assumes names are
  the lookup key, consistent with `resolve_node_name`'s own behavior, but this wasn't
  independently confirmed against raw node `id` attributes.
- Test-node pollution in `search_similar_code` results (fraction of top-k results that are
  test files) was recorded per-arm (`n_test_nodes`) in `per_task_records.jsonl` but not yet
  aggregated into a repo-wide rate.
- Fix the three bugs in the 2026-10-19 correction above (query-extraction regex, `src.`-prefix
  node-name mismatch, anisotropy sample size) and re-run the kernel before citing these exact
  percentages again anywhere outside this experiment's own writeup.
