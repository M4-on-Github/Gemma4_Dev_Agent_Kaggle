---
id: kg-paper-756473-ast-retrieval-compression
topic_id: 756473
title: "Retrieval finds the bug, test feedback fixes it: AST retrieval vs. self-correction for Gemma 4 E2B/E4B (two libraries, paired tests)"
author: anisha mehajabin (topic author); Mikhail (commenter, notebook owner msingatullin)
author_role: participants (paper track); no host role
credibility: [M] participant text; the component numbers are from a public notebook (see kg-nb-msingatullin-ast-guided-loops); no end-to-end resolve rate posted by either author as of the reads
topics: [paper, tool-output, edit-reliability, sampling, feedback]
first_seen: 2026-11-17
last_checked: 2026-11-17
---

# 756473: AST retrieval vs self-correction, with pytest compression and capped feedback

Topic posted 2026-11-06 13:43 UTC by anisha mehajabin. The opening post body is not returned by the CLI; the
"26% -> 42%" test-feedback figure below is quoted by a commenter from it, not read by us. Five comments were
returned (CLI `topics show --format json`, read 2026-11-17).

## Comments with numbers

- **3551292, Mikhail, 2026-11-06 23:56 UTC.** Reports, on real multi-file repositories in SWE-bench Lite with
  `gemma-4-31b-it-qat-w4a16-ct` (not the competition harness): deterministic AST slicing gives a **44.6% reduction
  in prompt tokens** on modules over about 600 lines; an instantaneous AST parse gate costs **47.2 microseconds**;
  pytest traceback compression gives a **30.6% token saving** "without losing the fault signal". Points to the
  public notebook and an Apache-2.0 repository. No resolve counts in the comment.
- **3551371, anisha mehajabin, 2026-11-07 06:25 UTC.** Her own runs: on boltons (files mostly fit a ~6k-token
  budget) AST retrieval made **no difference** to the fix rate; on more-itertools (a **5,644-line** module)
  retrieval went from **2% to 22%**. Her feedback design: patches are syntax-checked before any test runs (a
  SyntaxError, a test-file edit or an out-of-repo path is rejected atomically); feedback is the **tail** of the
  pytest output plus traceback frames not yet seen, **capped at about 1,500 tokens**. Her conclusion: fewer tokens
  and better localization alone did not raise fix rates until files outgrew the budget; test feedback did.
- **3551402, Mikhail, 2026-11-07 08:38 UTC.** The public notebook executes only the **31-scenario deterministic
  component benchmark** (latency, AST token reduction, syntax gating, pytest compression). He states an E2E
  SWE-bench Lite comparison is **pre-registered** (10-task paired pilot, frozen manifest, T=0.0, token caps) and
  "currently running"; trajectories and McNemar statistics promised. Also says an E4B run is in progress.
- **3551444, anisha mehajabin, 2026-11-07 10:27 UTC.** E4B runs with the capped feedback above: **about three in
  four failed attempts were patches that applied cleanly but were wrong**, not context or formatting failures.
  She reads this as reasoning about the fix being the limit, and asks whether full compression beats a plain cap.
- **3551448, Mikhail, 2026-11-07 11:14 UTC.** Two proposed mechanisms (runner frames dilute attention on a 4B model;
  sampling at T=1.0 introduces off-by-one or inverted repairs) and a claim that T=0.15 with a 2k thinking budget
  "materially reduces" clean-but-wrong diffs. An A/B of tail-capping vs root-cause compression is promised; no
  numbers given.

## Credibility notes

- Every number above is either a participant's own run or a component measurement. None is a resolve rate on a
  harness like ours. The 26% -> 42% figure is second-hand.
- Models: 31B for the component benchmark and the SWE-bench Lite statements; E4B for the capped-feedback claim.
- The 3551444 "three in four" is one author's E4B runs without a stated n in the comment.

## Relevance to our submission

See the paper-track digest `research/kaggle/digests/2026-11-17-paper-track-applicable.md`, rows 1 and 2. Only the
pytest-output shape is a prompt-level lever; the rest is already covered by our own records (C-019, EXP-034,
EXP-041, EXP-043).

## Untrusted files from this thread

- `untrusted/msingatullin-ast-guided-loops-2026-11-17/` (see kg-nb-msingatullin-ast-guided-loops.md for hashes).
