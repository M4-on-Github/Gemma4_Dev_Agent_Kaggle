# EXP-067 - which pipeline stage corrupts the applier's old_string (chain diff over the failed edits of three pipeline runs)

**Date:** 2026-11-10
**Type:** zero-GPU analysis (L1 trace mining), 0 L4x4-h
**Cohort:** none (the 24 task-runs of EXP-061-r, EXP-062-r and EXP-064-loc, 8 smoke-8 ids each)
**Ladder:** L1; follow-up to EXP-064 section 10 (rich_3468: 6 of 6 applier edits failed) and to the lead's count that 31 of 57 applier edits failed over the three runs.
**Pre-registered:** classes, definitions and readings are fixed in sections 2 to 4 before any failed edit was classified. What was seen first is listed in section 7.
**Serves:** D-008 (edit reliability), the user's 2026-11-10 decision to tweak the agents: this count picks which agent to change next.
**Supersedes / relates:** EXP-053 (applier resend wording, spent), EXP-061, EXP-062, EXP-064, EXP-066 (running, not read here).

## 1. Why this, now

Over the three pipeline runs the applier made 57 `edit_file` calls and 31 failed (EXP-061-r 12 and 6, EXP-062-r 20 and 10, EXP-064-loc 25 and 15). `summary.jsonl` marks 6 of the 31 as argument loss. The other 25 are a mix the summary does not split: the harness matcher (`edit.py:401-454`) tries exact, rstrip, strip, regex and JSON-unescaped forms before it answers "old_string not found", so a surviving not-found is a real content mismatch between the applier's old_string and the live file. Which stage put the mismatch there (reader, drafter, or applier) decides which agent prompt to change. Two earlier prompt changes aimed at the applier's wording (EXP-053) are spent; no count says whether the applier is the stage at fault.

## 2. Method

Data: `runs/EXP-061-r`, `runs/EXP-062-r`, `runs/EXP-064-loc`, the `traces/trace_<id>.json` of each (not the duplicate under `official/`), 24 task-runs, and each run's `summary.jsonl`. Reads and greps only; `python -I -X utf8` where a tool is run. No script is written and no tool is changed.

**Failed edit:** an applier `edit_file` call whose observation has `"status": "error"`. Split by error kind first, from the observation text:
- **A, argument loss:** the harness's "mandatory input parameters are not present" answer. Counted, not classified (6 expected from `n_edit_arg_loss`).
- **S, path form:** an error that names the source path (the filepath argument itself is wrong), not a content mismatch. Added after a grep of the error messages showed the kind exists (section 7); not classified further.
- **N, not found:** "old_string not found" (and any ambiguous-match answer, class M below). These are the failures the chain diff classifies.

**Chain diff, for each N failure, in order:**
- (a) the OLD block of the drafter the applier took it from (the drafter's final text in the same trace; matched by content, else by the applier's draft order 1 to 5);
- (b) the reader's REGION for that drafter's LOCATION (the reader's last report, the text the drafters were given through `{plan?}`);
- (c) the live file text: the reader's `read_file` result for that FILE over that LINES range, taken from the trace's JSON-escaped observation. If the reader never read those lines, say so.

Equality is tested on the JSON-escaped form as it sits in the trace (a fixed-string search of the failing old_string, or of a distinctive full line, inside the drafter and reader messages and the read_file observation), then by reading the two lines side by side where they differ.

**Classes, each N failure in exactly one (first match in this order from the live file outward):**
- **R1:** the reader's REGION differs from the live text it did read (the reader mis-copied lines it read).
- **R2:** the reader's REGION quotes lines it never read (no `read_file` or search output covers them).
- **D:** the drafter's OLD differs from the reader's REGION (it altered, extended, merged, or cut OLD beyond a correct REGION). REGION is correct here, or this failure's REGION equals live text.
- **P:** the drafter's OLD equals the live text but the applier's old_string differs from the draft's OLD (the applier did not paste it verbatim).
- **O:** the applier's own edit after the drafts: an old_string that matches no draft (it was written by the applier, after the drafts or in place of them).
- **X:** a retry after the drafts ran out: an old_string identical to one already sent in the same task-run, when all usable drafts have been tried.
- **M:** the matcher's answer is an ambiguous or more-than-once match, not a not-found.
For R1 and D a sub-type is given in own words (a token changed, lines skipped, lines invented, line-number prefixes copied, quote or escape form, and so on). Where the live text equals the draft and the old_string still failed, that is recorded as "unexplained" and not put in a class.

Stages: reader = R1 + R2; drafter = D; applier = P + O + X; neither = M, S, A.

**Resends (item 2):** per task-run, the number of `edit_file` calls whose old_string is identical to an earlier call's in the same task-run (calls minus distinct old_strings), for fastapi_14605 (EXP-064-loc), httpx_3672 (EXP-062-r) and fastapi_14448 (EXP-062-r); also for every other task-run with at least 2 calls. `n_identical_repeats` does not count these (EXP-053 section 2.2).

**First edit (item 3):** per task-run, the first applier `edit_file` call in step order: applied (observation status ok) or not (error, or no call at all). Reference count over the 24 runs, shown as applies, fails, no call. The candidate endpoint for the next smoke-8 screen is "first applier edit applies" per task-run, because "at least 1 applied edit" is 7 of 8 and has no room.

## 3. Endpoints

1. The class table: counts of A, S and each of R1, R2, D, P, O, X, M per run and in total, plus the number of task-runs each class sits in.
2. The resend counts of item 2.
3. The first-edit-applies reference of item 3 per run and over the 24.
4. The stage recommended for the next agent change.

## 4. Readings (written before the classes were counted)

1. **A stage is named** when its classes hold at least half of the classified N failures and the failures sit in at least 2 distinct task-runs. The recommendation is then to change that stage's agent: reader (R1 + R2), drafter (D), or applier (P + O + X).
2. **Mixed:** no stage meets reading 1. The recommendation is the stage with the most failures, stated as a plurality and not as a finding, and the next step is a per-class screen, not an agent change.
3. **One task, not a stage:** if a class that would meet reading 1 sits in a single task-run, the finding is recorded as that task-run's, and the stage is not named.
4. **Unexplained:** if 3 or more N failures have live text equal to the draft and still failed, the matcher or the file state (an earlier edit changed the file) is the cause and the chain diff is not the explanation. Then the first-edit count, not the stage, is the endpoint.
5. **Resends:** if each of the 3 named tasks carries 2 or more identical-old_string resends, resend is a standing behavior and the applier's no-retry rule is not being followed; this is recorded and is not attributed to a stage by this count.
6. **First edit:** if the first applier edit applies on 18 or fewer of the 24 task-runs (6 or more do not), the endpoint has room and is the recommended one for the next screen. If it applies on 22 or more, it has none and the next screen needs another endpoint.
7. A class of 1 or 2 failures is reported with its count only; the sub-type words are given for R1 and D whatever their size.

## 5. What this licenses

Nothing in this count is an effect of any change; it reads three finished runs. A named stage licenses a smoke-8 screen of one change to that stage with first-edit-applies as the endpoint and a bound on the failed-edit count per task-run. It does not license a dev-48 arm. The failures cluster in a few task-runs (section 7), so the unit of evidence is the task-run, not the edit.

## 6. Commands

`grep -c "old_string not found"` and `grep -n -o` over the traces for error kinds and line numbers; Read with offset and limit on the trace lines named by those greps; fixed-string `grep -c` for equality of a copied line between messages. No tool is run beyond `analyze_traces.py` outputs already on disk (`summary.jsonl`: `n_edit_fail`, `n_edit_arg_loss`, `tool_histogram.edit_file`, `n_identical_repeats`).

## 7. Defects

Seen before this file was written (so not blind): the per-run `n_edit_fail`, `n_edit_arg_loss` and `edit_file` counts from `summary.jsonl`; that the 25 non-arg-loss failures sit in 6 task-runs (EXP-061-r requests_7309 and httpx_3672 with 1 each, EXP-062-r fastapi_14448 and httpx_3672, EXP-064-loc fastapi_14605 and rich_3468) and the rest of the 24 task-runs have none; that 2 of the 25 (EXP-061-r requests_7309 and httpx_3672) are the path-form error S, not a not-found; and the first edit of EXP-064-loc rich_3468 (it failed). None of the 23 remaining failures had been classified. Class S was added because of that grep; the lead's class list did not carry it.

## 8. Record

Zero GPU. No push. No candidate tree.

## Status

2026-11-10: pre-registered, committed, counting.
