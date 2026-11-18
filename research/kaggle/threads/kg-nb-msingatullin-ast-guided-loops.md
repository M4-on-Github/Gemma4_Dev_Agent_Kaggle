---
id: kg-nb-msingatullin-ast-guided-loops
topic_id: 756473 (companion notebook named in comment 3551292)
title: "AST-Guided Loops Verification for Gemma 4"
author: msingatullin (notebook owner; slug `msingatullin/ast-guided-loops-verification-for-gemma-4`, id_no 142080990)
author_role: participant (paper track)
credibility: [M] own CPU benchmark of 31 scenarios; no end-to-end resolve rate in the notebook; 11-log marker test on logs from eight upstream repositories
topics: [paper, tool-output, prompt]
first_seen: 2026-11-17
last_checked: 2026-11-17
---

# msingatullin: AST-guided loops verification (notebook)

## Untrusted file record (read as data with `python -I -X utf8`; never executed)

| File | Bytes | SHA-256 | Pulled |
|---|---|---|---|
| `untrusted/msingatullin-ast-guided-loops-2026-11-17/ast-guided-loops-verification-for-gemma-4.ipynb` | 111,363 | `aca4b0e227ff7d176714c721cd67e0f5019e62fdead77482685c93709ed91eb3` | 2026-11-17 |
| `untrusted/msingatullin-ast-guided-loops-2026-11-17/kernel-metadata.json` | 792 | `e3ef6888ed8aceeb5e1d49bfa039e064fde6d9eb3b1165272ea8558d556ab538` | 2026-11-17 |

- Kernel metadata: `competition_sources` = `gemma-4-developer-agent-paper`; `enable_gpu` false; **`enable_internet`
  true**; `dataset_sources` empty. No version field in the metadata; the pull date is 2026-11-17.

## Numbers quoted in the notebook text

- "On 11 authentic failing pytest logs from eight upstream repositories, B2 preserves a predefined
  diagnostic/header/summary marker contract on **11/11** logs versus **2/11** for head35 or tail35, at **72.01%
  fewer raw log bytes**."
- The original compressor silently lost the marker on **10 of 88** logs (phase-1 read).
- A 5-task pilot reports 1 of 5 for each of Raw, B2 and tail35, and **9.76% fewer reported API tokens** (phase-1
  read; the exact pilot table was not re-read in this pass).
- The notebook states an E2E pilot of 10 tasks was pre-registered but **not run** at the time of the notebook text.

## What the numbers do and do not show

- The 11/11 result is a **marker-preservation** test on logs, not a solve rate. It says the compressor keeps the
  fields a parser wants; it says nothing about whether the agent fixes more bugs.
- Our harness caps `run_command` stdout at 5,000 characters (`max_stdout_chars`; `experiments/README.md` §1b). The
  compressor's byte savings matter only where the raw log exceeds that cap.
- Companion writeup "ast-guided-deterministic-gemma4-agent" is not readable through the CLI.
