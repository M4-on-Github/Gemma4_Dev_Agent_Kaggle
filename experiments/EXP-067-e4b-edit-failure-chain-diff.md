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

Found while counting (added after the pre-registration commit, c36c64a; the readings above were not changed):
1. **Class E (stale) was missing** from section 2's list: 8 of the 23 N failures are an old_string whose text an earlier applied edit of the same task-run had already replaced. It was added in section 9 as a class of its own.
2. **Reading 4's wording is ambiguous for E.** Its condition is "live text equal to the draft and still failed" and its consequence names "the file state"; E fails the condition (the live text no longer equals the draft). Section 9 applies the condition literally, reports E separately, and does not switch the endpoint on it.
3. **First-match rule and applier re-reads.** Two R1 failures (rich_3468 step 30, fastapi_14605 step 23) are applier edits made after the applier re-read the file; the first-match order puts them in R1, not O, because the reader's defect is what was pasted. Their count is stated in 9.1.
4. **Drafters see the reader's tool results: an inference, not a read prompt.** In the httpx_3672 EXP-062-r trace the drafters' OLD blocks are for a method that the reader's report does not contain but its `read_file` result does. If drafters see only the report, that trace needs another explanation. Not checked in any prompt dump.
5. **Draft format.** Some drafts lack the `<<<` opener or the `NEW:` line or use four angle brackets (rich_3468 drafter_1; fastapi_14605 drafters 1, 3, 4 in part; httpx_3672 drafter_5). Not counted; none was the traced cause of a failed edit.
6. **Grep counts.** `grep -c "old_string not found"` is 7 on rich_3468 against 6 failed edits: one hit is the applier's message text. Counts here are by observation status, not by that string.
7. **First-edit rows without a read.** For the task-runs with one edit call and `n_edit_fail` 0 the status came from `summary.jsonl`, not from opening each observation.

## 8. Record

Zero GPU. No push. No candidate tree.

## Status

2026-11-10: pre-registered (c36c64a). Counted the same day; results in section 9 (reading 2: mixed, plurality reader R1; reading 6: first edit applies on 17 of 24, room). Open: whether the drafters see the reader's tool results (inferred from one trace, not read from a prompt dump).

---

## 9. Results, 2026-11-10

Method as in section 2. Failed edits were read from the observation status of every applier `edit_file` call in the 8 traces that carry one or more failures, and from `summary.jsonl` counts for the 16 task-runs with none (the first-edit rows say which). Ids, counts, step numbers and own-words sub-types only; no repo or model text is copied here.

### 9.1 The 31 failures by kind

The lead's count (57 edits, 31 failed, 6 argument loss) reproduces. The other 25 are not all content mismatches: 2 are path-form errors, 3 are ambiguous matches, 8 are stale, and 12 are not-found against the live text.

| Run | edits | failed | A (arg loss) | S (path form) | R1 | R2 | D | P | O | X | M | E (stale) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EXP-061-r | 12 | 6 | 4 (requests_7309 x3, rich_3006) | 2 (requests_7309, httpx_3672) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| EXP-062-r | 20 | 10 | 1 (httpx_3672) | 0 | 0 | 0 | 0 | 0 | 1 (httpx_3672) | 0 | 0 | 8 (fastapi_14448 x5, httpx_3672 x3) |
| EXP-064-loc | 25 | 15 | 1 (requests_7205) | 0 | 11 (rich_3468 x6, fastapi_14605 x5) | 0 | 0 | 0 | 0 | 0 | 3 (fastapi_14605) | 0 |
| Total | 57 | 31 | 6 | 2 | 11 | 0 | 0 | 0 | 1 | 0 | 3 | 8 |
| Task-runs holding the class | | 8 | 4 | 2 | 2 | 0 | 0 | 0 | 1 | 0 | 1 | 2 |

Classified N failures (not A, not S): 23 = R1 11, E 8, M 3, O 1. By stage: reader (R1 + R2) 11, drafter (D) 0, applier (P + O + X) 1, neither (M, E) 11.

Class E is not in section 2's list. It was added when the first 062 trace was read: the failing old_string is the pre-edit text, and an earlier applied edit of the same task-run had already replaced it, so the live text no longer holds it. Section 4 reading 4 names "the file state" in its consequence, but its condition (live text equal to the draft) is not met by E, so E is reported here as a class of its own and reading 4 is not applied to it (section 7, item 2).

Per failure (steps are the trace's step_id):

- **rich_3468, EXP-064-loc, 6 failures, all R1** (steps 21, 22, 24, 25, 26, 30). The reader read lines 1600 to 1700 of the file and reported a region for lines 1627 to 1710 that differs from what it read, in three places inside the block every draft and every applier edit copied: one keyword-argument line inside a call is skipped; the last line is completed as a full call with arguments where the file has the bare name (the read ended on that line); and, outside the block the drafts used, the docstring differs (quote form changed, one line invented, one rewritten). The five drafts all carry the reader's block unchanged (D = 0). Step 30 is the applier's own edit after it re-read lines 1600 to 1750, and it still kept the skipped-line defect, so the live text was in its context and the reader's defect was still pasted (counted R1 by the first-match rule; noted as "live text in context").
- **fastapi_14605, EXP-064-loc, 8 failures: 5 R1 (steps 16, 17, 20, 23, 24), 3 M (steps 18, 21, 22).** The reader read lines 1 to 150 of the second file and reported a region for it that differs from the read in three ways: the first six lines are indented 4 columns deeper than the file, a comma is added at the end of one string line, and a closing line is invented (outside the block the edits used). Steps 16, 20 and 24 are one old_string sent three times; 17 shares the defects. Step 23 is the applier's own old_string after it re-read the file (step 19): indentation correct, comma kept (R1, "live text in context"). The 3 M answers are a short sub-block (2 old_strings, steps 18 and 21 identical, and step 22 a block with correct indentation) that occurs 8 times in the file, one per parameter class: the content is right, the block is not unique, and the reader's region carries no class header that would make it so. Which of the drafter's 3-to-12-line rule or the reader's region choice is at fault is not resolved here.
- **fastapi_14448, EXP-062-r, 5 failures, all E** (steps 15 to 19). Step 13 applied the first draft. The check (step 14) failed on missing test packages. The prompt says to keep the edit and stop in that case; the applier went on to drafts 2 to 5, whose OLD blocks are the same text (the five drafts share one LOCATION) and no longer exist in the file. All six calls (13, 15 to 19) carry one identical old_string.
- **httpx_3672, EXP-062-r, 4 N failures: 3 E (steps 18, 24, 25), 1 O (step 20); plus 1 A (step 23).** Drafts 2 and 3 applied (steps 16 and 17; step 16's old_string differs from draft 2's OLD in one type-annotation form and applied, because the applier corrected the draft to the reader's region). Draft 5 (step 18) failed because draft 3 had already replaced two of its lines. The applier then made its own edits with no read (no applier `read_file` in the trace): step 19 applied; step 20 invented lines it never read (O); step 23 lost an argument (A); steps 24 and 25 sent the original text of a whole method that draft 3 had already changed (E, identical old_strings). No check was run in the applier's turns, which is why the applied drafts were never undone.
- **S, 2 failures (EXP-061-r requests_7309 step 4 of 4, httpx_3672 first edit):** the filepath argument is wrapped in single quote characters, so the harness answers that the source path was not found. The 4 A failures of EXP-061-r show the same wrap on the filepath (rich_3006, requests_7309 x3). So 6 of the 8 A and S failures are in one run, EXP-061-r, and wrap the path in single quotes; of the other 2 A failures, requests_7205 (EXP-064-loc) sent a lone escaped quote as the filepath and httpx_3672 (EXP-062-r) lost its old_string. None of EXP-062-r or EXP-064-loc has a quote-wrapped path apart from that one.

### 9.2 Resends (item 2)

Identical old_string resends per task-run (calls minus distinct old_strings; full-string search of the escaped form in the trace):

| Task-run | edit calls | resends | where | `n_identical_repeats` |
|---|---|---|---|---|
| fastapi_14605, EXP-064-loc | 9 | 3 | steps 20 and 24 repeat 16; step 21 repeats 18 | 1 |
| httpx_3672, EXP-062-r | 8 | 1 | step 25 repeats 24 | 1 |
| fastapi_14448, EXP-062-r | 7 | 5 | steps 15 to 19 repeat 13 | 2 |
| rich_3468, EXP-064-loc | 6 | 2 | step 24 repeats 21, step 26 repeats 22 | 0 |

Every other task-run with 2 or more calls has 0: EXP-061-r requests_7309, httpx_3672 and rich_3006 and EXP-064-loc requests_7205 resend nothing (the resend after a path or argument error uses a different string), and EXP-064-loc httpx_3672 (4 calls, none failed) cannot resend an old_string it replaced. Total 11 resends over 24 task-runs, in 4 task-runs. The counter undercounts them (11 against 4 for these four).

Reading 5 (2 or more resends on each of the 3 named tasks): not met. httpx_3672 has 1, not 2. fastapi_14605 has 3 and fastapi_14448 has 5.

### 9.3 First edit (item 3)

The first applier `edit_file` call per task-run, in step order:

| Run | applies | fails | no edit call | the fails |
|---|---|---|---|---|
| EXP-061-r | 4 (requests_7205, fastapi_14448, fastapi_14605, rich_3468) | 3 (requests_7309 A, httpx_3672 S, rich_3006 A) | 1 (fastapi_14301) | quote-wrapped path or lost argument, 3 of 3 |
| EXP-062-r | 7 | 0 | 1 (requests_7205) | none |
| EXP-064-loc | 6 | 2 (requests_7205 A, rich_3468 R1) | 0 | 1 arg loss, 1 reader mis-copy |
| Total | 17 | 5 | 2 | |

First edit applies on 17 of 24 task-runs (17 of 22 where a call was made). Both no-call task-runs are on EXP-065's text-form list. Reading 6 (applies on 18 or fewer of 24): met; the endpoint has room, with 7 of 24 not applying (4 argument form, 1 reader mis-copy, 2 no call). For the EXP-064 tree alone the reference is 6 of 8. The first-edit statuses of the task-runs with one edit and no failure come from `summary.jsonl` (`n_edit_fail` is 0), not from a read of each observation.

### 9.4 Readings applied as written

1. **Not met.** The reader's classes hold 11 of 23 classified N failures (48%), below half; drafter 0; applier 1; the 11 others are M and E. R1 sits in 2 task-runs.
2. **Fires: mixed.** The plurality is the reader (R1 11 of 23, 2 task-runs, both in EXP-064-loc), followed by E (8, 2 task-runs, both in EXP-062-r). That is a plurality and not a finding. Had E and M been left out of the denominator, R1 would hold 11 of 12 (92%); the denominator in reading 1 is "classified N failures", and M and E are classified N failures, so this is not applied.
3. Not triggered: no class meets reading 1.
4. **Literal condition not met.** No N failure has live text equal to the draft's OLD and still failed. The 8 E failures fail because the file had already changed, which is the file-state clause of the reading's consequence but not its condition (section 7, item 2).
5. Not met (9.2).
6. **Met** (9.3): room, 17 of 24.
7. R1 sub-types are in 9.1. D is 0 so has none.

### 9.5 What the count licenses

- The reader's report is the origin of 11 of the 12 not-found failures that are not stale, and the 11 are on 2 task-runs of 8 in EXP-064-loc. A screen of a reader change is therefore a bound question, not a rate: "R1 failures on the 8 are 0" and "first edit applies on 8 of 8, or 7 of 8 with the lost one named", on the EXP-064 tree whose reference is 6 of 8. With 2 of 8 task-runs affected, a mean cannot be read.
- 2 of the 11 R1 failures were made after the applier re-read the file and still pasted the reader's defect. A change that only tells the applier to read first is not enough; the applier must be told to build old_string from the read result and not from the report or the draft.
- E (8) is a process failure of the applier in the same-location trees (EXP-061, EXP-062): the drafts share one OLD, the first applied draft replaces it, and the applier goes on to apply the rest without a check or an undo. It does not occur in EXP-064-loc (0 of 15), whose drafts are at different locations, and the current tree is that one, so it is not the next change.
- A and S (8 of 31) are an argument-form problem concentrated in EXP-061-r (6 of 8); EXP-062-r and EXP-064-loc have 2 A failures between them and no quote-wrapped path.
- Not a claim: nothing here is an effect of any change. The unit is 4 task-runs behind 23 failures (rich_3468 and fastapi_14605 in EXP-064-loc, fastapi_14448 and httpx_3672 in EXP-062-r); a second run of any tree could move every class.
- Recommendation: change the reader first, in the EXP-064 tree: give each location a FILE, LINES and CHANGE and no REGION, and have the drafters or the applier take old_string from a `read_file` of those lines made in their own turn, copied from that result. If the reader keeps a REGION, require it to be copied from its own read result for the same lines. The candidate endpoint is first-edit-applies per task-run, plus the bound on R1-type failures. Whether a REGION-free reader costs the drafters their context is untested; that is what the screen is for. No dev-48 arm is licensed.

## 10. Commands run

`grep -c "old_string not found"` per trace; `grep -n -o` for step ids, authors, function names, `filepath`, line ranges, error kinds and observation statuses; `Read` with offset and limit on the trace lines named by those; the `Grep` tool with the escaped full old_string as a regex to test equality of resent strings (EXP-064-loc fastapi_14605 and rich_3468, EXP-062-r fastapi_14448). Outputs of `analyze_traces.py` already on disk were read (`summary.jsonl`). No script was written, no tool changed.
