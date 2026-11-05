---
id: EXP-043-critic
exp: EXP-043
tier: light
verdict: accepted
verified: regenerated
date: 2026-11-05
---

## Verdict
**accepted.**
- Row 1 fires on the copy half (a + b + h = 5 of 8). It does not fire on the read half (c = 1). This holds under every resolution of the fastapi_14360 tie.
- The submit rule gets row 8. Row 10 does not fire.
- a6ee841 fixes an application error. It is not a change of rule.
- One recorded quantity is misapplied. No reading uses it.
  - Region read is reported as 8 of 8.
  - By the test as written it is 4 of 8.

## Audit
1. **Order: pass.**
   - Blind: the commit is at 21:58:45 and the first trace read at 21:58:48.
   - a6ee841 changes no rule text and opens no trace.
     - My mechanical c test fires on exactly the 5 calls it reclassed (fastapi_15661 x4, rich_3063 x1).
     - It fires on 2 more calls, but under the written precedence f and E3 take those first.
   - fastapi_13786's change follows the tie rule, because its first failed call is b.
   - The "after review" in §9.7 1a was the screener's own review.
   - 466a296 redacts the §2 disclosure, which sits above the results. It is logged in §9.7 item 9 and touches no design or reading text.
2. **Cohort: pass.** The 8 ids are those where `n_edit_fail` equals the `edit_file` count, with 39 calls. The other 17 ids carry 43.
3. **Numbers: pass, with one correction.**
   - These regenerate:
     - error types 22/5/12;
     - §9.6's 30/4/9, by id;
     - 12 repeats (file plus old string);
     - S1 on 5;
     - walls and calls.
   - a = 0 and e = 0 regenerate. No not-found old string matches the text it was shown, either verbatim or ignoring whitespace.
   - Correction, region read before the first failed edit (§3 item 1, that call's old string): 4 of 8 by the test as written.
     - fastapi_15661 and rich_3063 fail the line test.
     - The first failed calls of fastapi_14360 and rich_3935 carry no old string, so the test cannot pass.
     - Taking each task's first failed call that has an old string gives 5 of 7. rich_3935 has none.
     - The file was read on 8 of 8. The blind prediction was 6.
   - The 14360 tie, resolved three ways (b / g / f, literally the first call's class):
     - row 1 sum 6 / 5 / 5;
     - copy half 5 / 4 / 4;
     - rows 2 and 3 never fire.
8. **Hygiene: pass**, under the rule below.

**rich_4075 [V, outside the readings].** In swegemma 0.2.11 (the wheelhouse version), `submit_patch` applies `strip_protected_files_from_patch` before it reports the size. That removes the pyproject.toml edits, which is (ii).

**Hygiene ruling (item 4).**
- **Keep:**
  - the unquoted feature descriptions in EXP-043 §9.2/§9.7 and in EXP-041;
  - the harness error prefixes in EXP-043 §6/§2;
  - pytest labels with counts, exception class names, and the two package names in EXP-042;
  - EXP-041's first-word command labels and its paraphrase of our own prompt.
- **Remove:** the example search command in EXP-042 §2. It is rich_4075's search term, found in 1 trace.
- The over-removals in 466a296 need no restoring.

Proposed line for the logbook conventions:

> A committed file may name and count what a trace or repo holds but not reproduce it. Allowed: ids, counts, step numbers, class letters, file paths, a command's program name, exit codes, exception class names, public package names, the fixed messages and labels of the harness and pytest, and own-words descriptions that copy no characters. Not allowed, even as a fragment or example: anything the repo or the model wrote (file or patch text, code, command arguments other than a path, problem-statement wording, test names, the model's messages).

**Item 5.** 466a296 changed no number or reading in any of the three files.

## Required fixes (non-gating)

```
Screener, EXP-043 9.7, new items:
"10. *Corrected 2026-11-05 (critic light):* region read before the first failed edit, by the test as written,
is 4 of 8, not 8: fastapi_15661 and rich_3063 fail the line test, and the first failed calls of fastapi_14360
and rich_3935 carry no old string. On each task's first failed call with an old string it is 5 of 7. The file
was read on 8 of 8. No reading uses this. Supersedes "8 of 8" for region read in 9.3, 9.4 row 1 and item 3."
"11. *Added 2026-11-05 (critic light, outside the readings) [V]:* swegemma 0.2.11 strips diff sections touching
protected test and runner-config files, pyproject.toml among them, inside submit_patch before reporting the size:
(ii) for rich_4075. Row 10 stays as applied."
Screener, EXP-042 section 2: "(for example `grep python_version`)" -> "(for example a search for a version
string)", plus a dated 9.10 item.

Lead, knowledge/plan.md EXP-043 entry:
- "no critic review" -> "critic light accepted".
- "By class:" sentence -> "By class [H]: 16 paraphrase calls (10 altered shown text, 6 ran past the last line
  read), 11 exact copies matching more than once, 6 lost or malformed arguments, 5 single-line old strings
  matching no shown line (c by the pre-registered test; the file had been read), 1 escaping."
- "By task:" sentence -> "By task: b 5, c 1, f 1, g 1; row 1's sum is 6 of 8 (5 under either other resolution
  of the fastapi_14360 tie), copy half 5 (4) supported, read half 1 not; the submit-rule row gets no reading."
- "On all 8 the region had been read before the first failed edit." -> "All 8 had read the file before the
  first failed edit; the pre-registered region test passes on 4 of 8 (5 of the 7 with an old string)."
- "12 of 39 calls repeated the previous call unchanged" -> "12 of 39 failed calls repeated the previous failed
  call's file and old string".
- "the traces cannot settle it" -> "row 10 does not fire on the pre-registered evidence; the harness source
  settles it [V]: submit_patch strips protected config and test files from the diff".
- "The shipped prompt already says" -> "The prompt the E4B ran with (v24) already says".
- "Screener's recommendation, not licensed: at most one smoke-8 screen of an edit-recovery line" -> "Row 1's
  copy half licenses at most one smoke-8 screen of an exact-copy line (EXP-043 sections 5, 9.9)".
Lead, plan "Where a screen should look": "the edit-recovery line second" -> "the exact-copy line second".
```
