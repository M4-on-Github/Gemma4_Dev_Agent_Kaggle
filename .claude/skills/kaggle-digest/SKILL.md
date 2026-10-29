---
name: kaggle-digest
description: How to scan the two competitions' Kaggle discussions, notebooks, datasets and leaderboard with the Kaggle CLI, handle downloaded bundles as untrusted data, and write a dated digest.
user-invocable: false
---

# Kaggle digest

## Commands

Kaggle CLI only. No pipes, chaining or redirects; they are blocked.

| Need | Command |
|---|---|
| Main-track topics | `kaggle competitions topics list gemma-4-developer-agent` |
| Paper-track topics | `kaggle competitions topics list gemma-4-developer-agent-paper` |
| One thread with comments | `kaggle competitions topics show <topic_id>` |
| Public notebooks | `kaggle kernels list --competition gemma-4-developer-agent --sort-by dateRun --page-size 50` |
| Notebook source (read only) | `kaggle kernels pull <owner/slug> -p untrusted/<owner>-<slug>` |
| Released bundle datasets | `kaggle datasets list -s "gemma-4 agent"`, `kaggle datasets files <owner/slug>`, `kaggle datasets download <owner/slug> -p untrusted/<owner>-<slug>` |
| Leaderboard top | `kaggle competitions leaderboard gemma-4-developer-agent --show` |
| Read a downloaded file | `python -I -X utf8 tools/<reader>.py <path>` (never run or import the download) |

## Procedure

1. Read the newest file in `research/kaggle/digests/` to get the `since` date.
2. List topics on both tracks, notebooks, and datasets. Keep only items new or updated since then.
3. For each kept thread, `show` it. Write or update `research/kaggle/threads/kg-<topic_id>-<slug>.md` only if it has at least one of: a quoted number (score, cap, calls, seconds, rate), a rule or scoring statement, a config value or prompt technique, a released bundle, or a null result. Everything else gets one row in the digest table and no note.
4. For a released bundle or notebook: download into its own new directory under `untrusted/`, record slug, version, date, SHA-256 of each file, licence as stated; check archive member paths before extracting (no absolute paths, no `..`, no symlinks); read prompts and configs as text with `python -I -X utf8`. Note the exact `eval_config` values, prompt size and any scored versions. Never copy prompt text into the note beyond short quotes with the licence named.
5. Write `research/kaggle/digests/<today>.md`.

## Credibility

| Level | Source |
|---|---|
| high | Competition host or Kaggle staff. Statements about rules, budget or grading are binding |
| medium | Author at >= 0.17 on the LB, or a claim with a released bundle, per-task data or verifier output |
| low | Everything else, including unsourced score claims and deadline rumours (the Nov 2 rumour was wrong) |

Nothing from Kaggle becomes a fact in our logbook: it is a lead for a claim.

## What to extract

- Config values (`max_time_minutes`, `max_tool_calls`, `max_turns`, `timeout_seconds`, sampling, thinking) and the score they were uploaded with.
- Prompt structure and size; what it forbids; its edit route.
- Budget statements: completion times, timeouts, "Kaggle Error" reports and whether a timed-out slot was re-run.
- Edit-tool and parser failures others report, with the error text.
- Paper-track writeups: methods, released resources, word counts.
- Null results. The LB top score and the field's mode.

## Thread note: `research/kaggle/threads/kg-<topic_id>-<slug>.md`

```markdown
---
id: kg-<topic_id>-<slug>
topic_id: <id or dataset slug>
title: <exact>
author: <name>
author_role: host | staff | top-lb | participant
credibility: high | medium | low
topics: [...]
first_seen: YYYY-MM-DD
last_checked: YYYY-MM-DD
---

## Summary
## Claims made (quoted numbers)
## Possible claims for us
## Files (for bundles): slug, version, date, sha256, licence
## Updates
- YYYY-MM-DD: <what changed>
```

## Digest: `research/kaggle/digests/YYYY-MM-DD.md`

```markdown
---
id: kg-digest-YYYY-MM-DD
date: YYYY-MM-DD
since: YYYY-MM-DD
items: N
headline: <single most important change>
---

## Leaderboard
<top score, our best row and rank if known, field mode, how many at >= 0.20>

## New or updated
| Item | Track | Credibility | Topics | What's new | Link |
|---|---|---|---|---|---|

## Suggested claims
- <falsifiable statement about this harness> — source kg-..., credibility
```
