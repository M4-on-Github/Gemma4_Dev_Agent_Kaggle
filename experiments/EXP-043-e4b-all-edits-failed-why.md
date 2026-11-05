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
- The harness's not-found error text in rich_3105 (not one of the 8), and the agent's own messages in fastapi_14262, fastapi_14463 and fastapi_13207 saying an edit failed because the old string was not found, and in fastapi_13207 one saying it failed on missing mandatory parameters (so E2 occurs in the run; fastapi_13207 is not one of the 8).
- For rich_4075: the file it edited (`pyproject.toml`), that the first call's old and new strings both begin with the same 8 characters, that the second call's old string begins with indentation, and that its first command was a search. I have not compared the full strings.
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

Pre-registration commit e94b925. Sections 1 to 8 above are unchanged; this section applies them as written. The traces are `runs/EXP-038-e4b-dev48/traces/trace_<id>.json`; the budget in the agent's own system prompt is 28 tool calls and 8 minutes, and `n_calls` in `summary.jsonl` does not count `submit_patch`. All 8 tasks ended far inside the budget (longest 190.1 s and 17 calls).

### 9.1 Error types, 39 calls on the 8 ids

| Type | Calls | Where |
|---|---|---|
| E1 old string not found | 22 | 15661 4, 14873 4, 14459 4, 14360 2, 13786 4, rich_3676 3, rich_3063 1 |
| E2 missing mandatory parameters | 5 | rich_3935 4, 14360 1 |
| E3 other | 12 | 11 are non-unique-match errors (13786 4, rich_3063 5, 14360 2), 1 is an identical-strings error (15661) |

The identical-strings error was not anticipated in section 2; its call is class f (arguments malformed and cut mid-token, with a stray extra key, so both strings ended up equal).

### 9.2 Call classes, 39 calls

| Class | Calls | Tasks with at least one such call |
|---|---|---|
| b paraphrase | 16 | 5 (14873, 14459, 14360, 13786, rich_3676) |
| g other | 11 | 3 (14360, 13786, rich_3063); all 11 are non-unique matches |
| f call-format or argument loss | 6 | 3 (15661, 14360, rich_3935) |
| c from memory (the test as written) | 5 | 2 (15661 4 calls, rich_3063 1 call) |
| h escaping | 1 | 1 (14459) |
| a whitespace only, d stale state, e wrong file | 0 | 0 |

**The c test fires on single-line old strings that are not verbatim lines of any observation.** As pre-registered (defect 2 of section 7 foresaw it), a one-line old string that paraphrases or escapes a line of a file the agent has just read has no line that matches, so it is class c under the precedence c before h, a, b. That applies to the four E1 calls of fastapi_15661 (a pattern line written in a different form from the line in the read) and to the one E1 call of rich_3063 (a line with doubled backslashes). In both tasks the file had been read whole or at that region, so c here does not mean "never looked": the table in 9.3 carries the read column for that reason. A first pass of this section classed those five as b (4) and h (1); the precedence as written was then applied and the counts above are the result.

Descriptive sub-tags added after reading (not in the pre-registration, they change no count above). Of the 16 b calls, 10 altered text the agent had been shown (an altered character run, an added line, one changed token) and 6 ran past the last line the trace shows (the old string closes a statement whose continuation the agent never read: 14459 3 calls, where the read hit the 10000-character limit and cut the function, and rich_3676 3 calls, where the agent's own read range ended mid-statement). The 11 g calls are exact copies that occur 2 to 5 times in the file.

### 9.3 Task table

| Task | Failed calls | Error types | Class per call | Task class | Region read before first failed edit (file read) | Consecutive unchanged repeats | After the last failure | Message before submit | wall_s, n_calls |
|---|---|---|---|---|---|---|---|---|---|
| fastapi_15661 | 5 | E3 E1 E1 E1 E1 | f c c c c | c (by the test as written, the file was read whole) | yes (yes, whole file) | 1 | S1 | acknowledges failure | 59.6, 6 |
| fastapi_14873 | 4 | E1 x4 | b b b b | b | yes (yes) | 0 | S1 | hedges (assumes applied) | 110.7, 10 |
| fastapi_14459 | 4 | E1 x4 | h b b b | b | yes (yes, function cut by the read limit) | 0 | S1 | acknowledges failure | 121.0, 16 |
| fastapi_14360 | 5 | E2 E1 E1 E3 E3 | f b b g g | b (b and g tied 2 to 2 and the first call is f, so the rule has a gap, see 9.7) | yes (yes) | 2 | S2 (2 searches, then 3 submits) | acknowledges failure | 190.1, 17 |
| fastapi_13786 | 8 | E1 E1 E1 E3 E3 E3 E1 E3 | b b b g g g b g | b (4 to 4 with g; the first call is b, so the rule decides) | yes (yes) | 2 | none: 2 submits between failures, then a final text with no submit | claims applied | 91.5, 11 |
| rich_3935 | 4 | E2 x4 | f f f f | f | yes (yes, whole file) | 3 | S2 (ls, one test run, then submit) | claims applied | 79.6, 7 |
| rich_3676 | 3 | E1 x3 | b b b | b | yes (yes) | 1 | S1 | hedges | 84.2, 6 |
| rich_3063 | 6 | E3 E1 E3 E3 E3 E3 | g c g g g g | g | yes (yes) | 3 | S1 | hedges | 121.3, 11 |

Totals: region read before the first failed edit on 8 of 8; file read on 8 of 8; 12 of 39 failed calls repeat the previous failed call's file and old string. The categories "acknowledges failure, hedges, claims applied" and the S0 case (no submit after the last failure) were added at mining; "hedges" is counted as not saying the fix was applied.

### 9.4 Readings applied as written

| Row | Observed | Result |
|---|---|---|
| 1 | T(a) + T(b) + T(h) + T(c) = 6 (T(b) 5, T(c) 1, a and h 0); T(c) = 1, T(a) + T(b) + T(h) = 5 | **Fires**, copy half only (5 >= 3); the read half is not supported (T(c) 1 < 3, and 8 of 8 tasks had read the region, so even the one c task is a misquote of a line in view). Holds under the one open tie resolution: see 9.7 |
| 2 | T(f) = 1 | no |
| 3 | T(e) + T(g) = 1 | no; 2 under the other resolution of the one gap, still no |
| 4 | b has 5 | not fired (a class has T >= 3) |
| 5 | c 1, f 1, g 1, a d e h 0 | those classes license nothing on their own |
| 6, 7, 8 | S1 on 5 of 8 | **Row 8, no reading on the submit rule** |
| 9 | claims applied on 2 of 8 | no |
| 10 | rich_4075 | not decided, so (v): see 9.5 |

Predictions against what was seen. Error types: predicted E1 33, E2 5, E3 1; seen 22, 5, 12 (the E3 count was the large miss: non-unique matches were not in my model). Task classes: predicted a 3, b 3, c 1, f 1; seen b 5, c 1, f 1, g 1, a 0. Calls: predicted a 14, b 12, c 5, f 5, g 3; seen b 16, g 11, f 6, c 5, h 1, a 0. Region read before the first failed edit: predicted 6, seen 8. S1: predicted 5, seen 5. Message says applied: predicted 5, seen 2. rich_4075: predicted (ii), seen unresolved with (ii) favoured.

### 9.5 rich_4075

Two `edit_file` calls on `pyproject.toml` (the problem statement pairs a rendering fix with a request to drop support for an old Python version). Both returned status ok, one occurrence, strategy exact, with a diff in the observation; the next call, `submit_patch`, returned patch size 0 and files changed 0. The file `runs/EXP-038-e4b-dev48/patches/rich_4075.patch` is empty. Against the candidates fixed in section 2: (i) is excluded, the old and new strings differ in both calls; (iii) is excluded, no call sits between the second edit and the submit and no call undoes anything; (ii) and (iv) both fit and the traces cannot separate them: no trace in EXP-038 or in EXP-028 (Arm R) touched a file named pyproject.toml, setup.cfg or tox.ini other than by reading it (a search for these three names only), so there is no non-empty patch to set against it, and the agent made no read after the edits. (ii) is the one the competition brief supports (tests and config files are reset before grading) and edits to source files in other tasks of this run do reach the patch, which makes a tool that silently writes nothing less likely, but this is a reading of documentation, not of this trace. Row 10 is not fired. The edit calls themselves worked; if (ii) holds, what the agent lost was an edit to a file the grader does not take.

### 9.6 The other 17 ids with a failed edit (recorded, no reading)

Error type counted for all 43 failed calls: E1 30, E2 4 (fastapi_13207, 14301, 15800, requests_6644, one each), E3 9 (fastapi_14605 5, httpx_3672 3, fastapi_13207 1; every E3 error seen is a non-unique match). Counts per id: E1 15280 1, 14964 4, requests_7315 1, rich_4070 2, 14463 1, 14512 4, 9753 3, 14262 1, httpx_3672 1, 15800 4, rich_3180 4, rich_3480 2, rich_3105 2. All 25 tasks with a failed edit together: E1 52, E2 9, E3 21 of 82 calls. **Stopped at the error type:** the 30 E1 calls of these 17 ids were not classed by letter (a hand comparison of each old string with the file was not done); E2 calls are f and E3 calls are g by construction (4 and 9). fastapi_14605's five failures are all non-unique matches. The per-call classes of the 17 are open for a later job.

### 9.7 Defects and caveats found

1. **The tie rule has one gap, and the verdict does not depend on it.** Two tasks have a tied majority: 13786 (4 b, 4 g), which the rule decides (first failed call is b), and 14360 (1 f, 2 b, 2 g), where the first call is f, which is not among the tied classes, so the rule is silent; I took the tied class whose first call comes earliest (b). Resolved the other way (g), T(b) is 4, T(c) 1 and T(g) 2: the row 1 sum is 5 and still fires, and row 3 (T(e) + T(g) = 2 < 3) does not fire. The counts of tasks with at least one call of a class do not depend on the rule: b 5, g 3, f 3, c 2, h 1. The honest summary is two independent failure families, a mis-copy of text (5 tasks with a b call, 2 more with a c call) and a non-unique match (3 tasks), plus lost arguments (3 tasks); row 1 as written does not say which dominates.
1a. **The c test was applied as written** (no non-blank line of old_string of 8 or more characters appears in any earlier observation). It fires on 15661's four not-found calls and on rich_3063's second call, where the old string is a paraphrase of a line the agent had been shown; the first draft of this section called those b and h and was corrected after review.
2. **Row 3 as written says g licenses neither a prompt line nor a rule on submit, and this was written without the non-unique case in mind.** The error text of those calls already tells the agent to give more surrounding context, and in 13786, 14360 and rich_3063 the agent repeated an identical call or went back to an earlier one rather than adding context. That is a behaviour a prompt line could address ("when the error says the text occurs more than once, copy lines before and after it"). It is not licensed by a reading; it is recorded as outside the readings.
3. **The prompt already says old_string must match the file exactly, including indentation** (system prompt in every trace). Row 1's line therefore repeats an existing instruction; what is different is only emphasis or form. Compliance is untested and 8 of 8 tasks had read the region.
4. **A harness inconsistency, one task.** In rich_3063 the first and second failed calls have the same old string and differ in their new string only by a trailing newline, yet the first got a non-unique-match error (4 occurrences) and the second a not-found error. Whether the tool normalises escapes inconsistently or something else, the trace does not say. Same task: all six old strings carry doubled backslashes relative to the file, and the tool still reported matches for five of them.
5. **Lost arguments are two different shapes.** In 14360 one call lost old_string (E2). In rich_3935 the model emitted all arguments as a single mangled key and repeated that exact call four times, the same shape every time, saying each time that it had provided the parameters. This is the C-004 path; it was not a copy error and the harness's error text did not change the behaviour.
6. **Most of these agents stop early.** Wall 59.6 to 190.1 s of the 480 s and at most 17 of 28 calls: the failed-edit tasks did not run out of budget; the agent submits after 3 to 8 failures. 13786 submitted twice with an empty diff and then went back to editing, both times with calls that failed again, and ended with a final text and no submit after the last failure.
7. **Classification is by hand** and the b calls in particular are a mix of two sub-kinds (altered text 10 calls, and text beyond the read 6). The second sub-kind (6 calls, 2 tasks) would not be helped by "copy exactly" and points instead at read ranges that cover the whole span to be replaced.
8. EXP-041 and EXP-042 are unchanged. The rich_4075 strings were compared in full only after the pre-registration commit, as the disclosure says.
9. 2026-11-05: quoted harness error text, a file-content fragment and a code-level description were removed from the disclosure, 9.1, 9.2, 9.6 and 9.7 for hygiene (critic light on EXP-041, lead job); no number or reading changed.

### 9.8 What this study cannot show

**It cannot show whether the E4B would write a correct fix once the edit lands.** An applied edit is not a resolved task. In rich_3935 the agent says in its own text that it does not know the failing test and is guessing at the fix, and on rich_4075 the edit landed and left no diff.

### 9.9 What it licenses

Observational, one run of a stochastic loop, 8 tasks, hand classes. Row 1 as written fires on the copy half (T(a) + T(b) + T(h) = 5 of 8 tasks, 4 under the one open tie, and the row 1 sum T(a) + T(b) + T(h) + T(c) stays at 5 or 6 under either resolution) and licenses at most a smoke-8 screen of a prompt line about exact copying, with the endpoint being the share of tasks with an applied edit, not the resolve rate, and with 9.7 items 1 to 3 in view. Row 8 gives nothing on a submit rule. Nothing in rows 2 and 3 licenses a lever. Claim status does not move.

## Status

2026-11-05: pre-registered (e94b925), mined and appended 2026-11-05, zero GPU. Row 1 fires as written (copy half, a + b + h + c = 6 of 8 tasks, 5 under the alternative resolution of the one task whose tie the rule does not decide; row 1 fires and row 3 does not under both), row 8 on the submit rule (no reading), row 10 not decided for rich_4075 ((ii) favoured). Other 17 ids stopped at the error type.
