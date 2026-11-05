# EXP-043 — Why do the E4B's `edit_file` calls fail on the 8 tasks where every edit failed? Zero-GPU trace mining over EXP-038

**Date:** 2026-11-05
**Type:** zero-GPU trace mining (L1) over an existing run directory. No kernel, no upload, no zip, no notebook, 0.0 L4x4-h.
**Cohort:** none run. Reads `runs/EXP-038-e4b-dev48/` read-only (the 8 ids below, then the other 17 ids with a failed edit).
**Ladder:** L1. Follows EXP-042 section 9.7 (8 of 48 E4B tasks had every `edit_file` call fail, 9 submitted an empty patch, 0 resolved). No claim status moves.
**Pre-registered:** commit of this file, before the arguments (`filepath`, `old_string`, `new_string`) of any failed `edit_file` call were read for this purpose (see "What was seen before writing").
**Serves:** the lead's decision whether a prompt line, a rule on submit, or neither can address the failed-edit path; C-020 context only.
**Relates:** EXP-042 (counts), EXP-041 (the 19-id control, whose classes a, b, c, d are a different scheme), EXP-038 (the run), EXP-024 and EXP-026 (the lost-argument mechanism, C-004).
**Tags:** [V] verified in the trace, [H] read by hand, [I] inference.

## 1. Why this, now

EXP-042 recorded that 8 of 48 E4B tasks had every `edit_file` call fail and 9 submitted an empty patch, and none of the 9 resolved. Which fix, if any, is worth building depends on why the calls fail: a copy error (a prompt line or a different edit habit could address it), a failure of the call itself (argument loss, which C-004 already covers), or something no prompt fixes. This reads the failed calls to say which.

## 2. Design

**Population.**

- Primary: every failed `edit_file` call on the 8 E4B ids where all edits failed: fastapi_15661, fastapi_14873, fastapi_14459, fastapi_14360, fastapi_13786, rich_3935, rich_3676, rich_3063. `summary.jsonl` gives 39 failed calls in all (5, 4, 4, 5, 8, 4, 3, 6 in that order). The unit for a call table is a failed call, the unit for a reading is a task.
- Separate case: rich_4075 (two `edit_file` calls that did not fail, empty patch).
- Recorded, no reading: the other 17 ids with at least one failed edit (25 minus 8), 43 failed calls in all (`summary.jsonl`). Their error type is tallied for all 43 calls. A full class per call is attempted after the 8 are done and says which calls it covers; if it is not completed the file says "stopped at" and which ids are not classed.

**What counts as a failed call.** A call whose observation has `"status": "error"` (the same count as `n_edit_fail` in `summary.jsonl`). Every failed call is first typed by the error text of its observation:

- E1: the old string was not found (the harness's "old_string not found" message).
- E2: missing mandatory parameters (the harness's "mandatory input parameters are not present" string).
- E3: any other error text (for example a non-unique match, a missing file or a permission error).

**Classes of an E1 call (hand classification, [H]).** Applied in this precedence, first match governs, because the earlier the cause in the chain the more it explains:

| # | Class | Test |
|---|---|---|
| f | call-format or argument loss | the call is E2, or an argument is empty or visibly truncated (ends mid-line or mid-token) |
| e | wrong file or path | the error is a missing file, or the old string occurs verbatim in a file the trace shows but not in the file named in the call |
| d | stale state | an earlier successful `edit_file` on the same file changed the region and the old string equals the text before that edit. Structurally impossible on the 8 ids (no edit there succeeded); it is only possible on the other 17 |
| c | from memory | no non-blank line of the old string, stripped of surrounding whitespace and at least 8 characters, appears in any earlier observation of this trace |
| h | escaping | the old string carries escape artefacts that the file does not (a literal backslash-n or backslash-quote in place of a newline or quote, doubled backslashes), and with them removed it would match or differ only in whitespace |
| a | whitespace only | the old string differs from the file's text only in whitespace or indentation (leading or trailing spaces, tabs against spaces, blank lines added or removed, a line wrapped or joined) |
| b | paraphrase | some lines of the old string appear in the file's text as the trace shows it, but the old string differs in non-whitespace characters (elision, a changed comment, reordered arguments, an abbreviated name, an invented line) |
| g | other | none of the above fit; the reason is stated |

E2 calls are class f by construction; E3 calls are classed by the same table (a missing file is e, the rest g). The file's text is taken from the earliest earlier observation in the trace that shows the region (a `read_file` of the file, or a `grep`, `sed` or `cat` output). Where the trace never shows the region, the call is c, and the record says whether the file was read at some other range.

**Per task, recorded.**

1. Region read before the first failed edit: yes if an earlier observation shows at least one non-blank line of that call's old string (the same test as c), and whether the file was read at all (any `read_file` of it) before the first failed edit.
2. The number of failed calls that repeat the previous failed call unchanged (identical `filepath` and `old_string`), counted as consecutive repeats, and the longest run.
3. What the agent did after the last failed edit and before `submit_patch`: S1, `submit_patch` is the next tool call; S2, other reads or commands then `submit_patch`; S3, a different edit route was tried (`write_file`, or a `run_command` that writes a file) and the diff stayed empty. Also: whether the last message before submit says the fix was applied (yes, no, or does not say).
4. `wall_s` and `n_calls` from `summary.jsonl`, against the cap of the tree as read from EXP-038 section 2 (stated in section 9).

**Task class.** The class of the majority of a task's failed calls. A tie goes to the class of the task's first failed call. A task also lists every class that occurs in its calls.

**rich_4075.** The question is why two `edit_file` calls that did not fail left an empty patch. Candidate explanations, fixed now: (i) each call replaces a string with an identical string; (ii) the file edited is a config or build file that the harness leaves out of the extracted patch (the competition brief says tests and config files are reset before grading); (iii) the edit was written and then undone; (iv) the call reports success but the file is unchanged; (v) none of these fit. The evidence is the two observations, the `submit_patch` observation, whether the old and new strings are equal, and whether any other trace in either run edited a file of the same name and got a non-empty patch.

**Instruments.** `summary.jsonl` for counts; `grep -o -H -n` over the trace for `function_name`, `filepath`, error text and step numbers; `Read` of single trace lines for the arguments and the observation they should be compared with. The shell of this agent allows no ad-hoc scripts, so classes are by hand and each is reproducible from the line numbers listed in section 9. Nothing from a trace goes into git except counts, task ids, class letters and step numbers.

**Cap and scope.** No GPU, no kernel. Nothing in `submission/`, `tools/`, `tests/`, EXP-038, EXP-041, EXP-042 or another agent's row is touched.

### What was seen before writing this file

Not blind, disclosed so the readings are weighed accordingly:

- The counts: `n_edit_fail` and `edit_file` per task for all 48 (EXP-042 section 9.7), including that the 8 ids have every edit failed.
- The error text "Failed to replace: old_string not found. Ensure you're not escaping content incorrectly and check whitespace, indentation, and context." in rich_3105 (not one of the 8), and the agent's own messages in fastapi_14262, fastapi_14463 and fastapi_13207 saying an edit failed because the old string was not found, and in fastapi_13207 one saying it failed on missing mandatory parameters (so E2 occurs in the run; fastapi_13207 is not one of the 8).
- For rich_4075: the file it edited (`pyproject.toml`), that the first call's old and new strings both begin with the same 8 characters (`python = ` and a quote), that the second call's old string begins with four spaces and a quote, and that its first command was a search for a python-version string. I have not compared the full strings.
- EXP-041's classes a, b, c, d for the 19 control ids and 4 targets, which included several of the 8 ids here (the five empty-patch control tasks). Those classes were about where the edit went and why the fix did not land, not about the old string against the file; I recorded no old-string comparison then.
- The 8 ids' tool histograms and that none of them has a `write_file` call [recheck at mining, not recorded].

## 3. Endpoints

1. The call table: for the 39 failed calls, the error type (E1, E2, E3) and the class (f, e, d, c, h, a, b, g), with the step number of each call.
2. The task table: task class, classes present, region read before the first failed edit, file read before, repeats, post-failure behaviour, last-message claim.
3. The rich_4075 account.
4. The other 17 ids: error type for 43 calls, and a class table for whichever are classed.
5. No test statistic is an endpoint. Eight tasks and 39 calls support none.

## 4. Readings (blind)

Notation: for the 8 tasks, T(x) is the number of tasks whose task class is x. Families: the copy family is a + b + h, the read family is c.

| # | Observed | Reading |
|---|---|---|
| 1 | T(a) + T(b) + T(h) + T(c) >= 5 | A prompt line points: "read the exact lines immediately before editing and copy them". Split: T(c) >= 3 supports the read half, T(a) + T(b) + T(h) >= 3 supports the copy half. What the line would do to the rate is not read here |
| 2 | T(f) >= 3 | Argument loss, not a copy error. No new prompt line points; it is the C-004 path already measured, and the reading goes to that claim, not to a new lever |
| 3 | T(e) + T(g) >= 3 | Neither a prompt line nor a rule on submit points; these are failures of localization or of the tool, not of copying |
| 4 | no class with T >= 3 | No single mechanism: nothing is licensed |
| 5 | any class with T < 3 | That class licenses nothing on its own (rows 1 to 3 may still combine as written) |
| 6 | S1 on >= 6 of 8 tasks | The agent submitted straight after the last failure without trying anything else, so a rule on submit (no submit with an empty diff) points. It would only help to the extent the classes of rows 1 to 3 say a further edit could land |
| 7 | S1 on <= 2 of 8 tasks | The agent kept trying after the last failure; a rule on submit alone does not point |
| 8 | S1 on 3 to 5 of 8 tasks | No reading on the submit rule |
| 9 | the last message before submit says the fix was applied on >= 6 of 8 tasks | The agent does not register that the edit failed. Reported with row 6, not a separate lever |
| 10 | rich_4075: one of (i) to (iv) is shown by the evidence | That is the account. If the evidence does not decide, (v) and the answer is "unresolved" |

Rows 1 to 3 are read together: the task classes are exclusive, so at most one of the rows 1 to 3 can reach a share of 5 or more of 8, and a split such as 3 + 3 + 2 is row 5 for the class of 2 and a partial reading for each of the others. The readings decide what the lead may rank, not what is true. For the 17 other ids the same table is applied and marked recorded, with no reading.

**Predictions, written blind.** Error types over the 39 calls: E1 33, E2 5, E3 1. Task classes: a 3, b 3, c 1, f 1, g 0, e 0, h 0, d impossible. Calls: a 14, b 12, c 5, f 5, g 3. Region read before the first failed edit on 6 of 8 tasks. S1 on 5 of 8 tasks. The last message says the fix was applied on 5 of 8. rich_4075: (ii), the file is a config or build file that the harness leaves out. Uncertainty is high; none of the old strings was compared.

## 5. Licenses

What the table can decide: whether the E4B's failed edits are failures to copy or read (and so address-able by an instruction or a different edit habit), failures of the call itself, or something else, and whether a rule on submit would catch an agent that has not tried anything further. What it cannot show: **whether the E4B would write a correct fix once the edit lands.** A copy error fixed by a prompt line gives an applied edit, not a resolved task; EXP-041 found that on some of these tasks the right file was edited with a fix that did not resolve (class c there). It is observational, there are 8 tasks and 39 calls from one run of a stochastic loop, and the classes are hand judgements ([H]) with the precedence above. No claim status moves; a pointing reading licenses a smoke-8 screen of the prompt line whose endpoint is the share of tasks with an applied edit, not the resolve rate.

## 6. Commands

```
grep -n -o -e "\"function_name\": \"edit_file\"" -e "\"function_name\": \"submit_patch\"" runs/EXP-038-e4b-dev48/traces/trace_<id>.json
grep -n -o -e "Failed to replace[^\\]\{0,40\}" -e "mandatory input parameters[^\\]\{0,30\}" runs/EXP-038-e4b-dev48/traces/trace_<id>.json
Read runs/EXP-038-e4b-dev48/traces/trace_<id>.json  (offset = the line of the call, limit 1)
```

## 7. Defects

Written before the run; section 9 appends any found.

1. **Task class by majority** is a convention; a task with a 2-2-1 split is decided by the first failed call, which is arbitrary.
2. **The c test is a line match.** A paraphrased single-line old string looks like "never read" under the test; the record carries whether the file was read at all so the reader can tell.
3. **Hand classification.** Borderline calls between a and b, and between b and c, are marked [H] and listed.
4. **Seen-before disclosure** above.

## 8. Built

Nothing. No tree, zip, notebook or kernel. 0.0 L4x4-h.

## 9. Results

Pending.

## Status

2026-11-05: pre-registered, committed before any failed call's arguments were read for this purpose. Results pending.
