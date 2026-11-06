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
- Row 1 fires on the copy half (a + b + h = 5 of 8) and not on the read half (c = 1). This holds under every resolution of the fastapi_14360 tie.
- The submit rule gets row 8. Row 10 does not fire.
- a6ee841 fixes an application error. It does not change a rule.
- One recorded quantity is misapplied, and no reading uses it: region read is 8 of 8 in the file but 4 of 8 by the test as written.

## Audit
1. **Order: pass.**
   - Blind: the commit is at 21:58:45 and the first trace read at 21:58:48.
   - a6ee841 changes no rule text and opens no trace.
     - My mechanical c test fires on exactly the 5 calls it reclassed (fastapi_15661 x4, rich_3063 x1).
     - It also fires on 2 more calls, which f and E3 take first under the written precedence.
   - fastapi_13786's change follows the tie rule: its first failed call is b.
   - The "after review" in §9.7 1a was the screener's own review.
   - 466a296 redacts the §2 disclosure, which sits above the results. It is logged in §9.7 item 9 and touches no design or reading text.
2. **Cohort: pass.** The 8 ids where `n_edit_fail` equals the `edit_file` count carry 39 calls. The other 17 ids carry 43.
3. **Numbers: pass, with one correction.**
   - These regenerate:
     - error types 22/5/12;
     - §9.6's 30/4/9, by id;
     - 12 repeats (file plus old string);
     - S1 on 5;
     - walls and calls.
   - a = 0 and e = 0 regenerate. No not-found old string matches the text it was shown, verbatim or ignoring whitespace.
   - Correction: region read before the first failed edit (§3 item 1, that call's old string) is 4 of 8 by the test as written.
     - fastapi_15661 and rich_3063 fail the line test.
     - The first failed calls of fastapi_14360 and rich_3935 carry no old string, so the test cannot pass.
     - Taking each task's first failed call that has an old string gives 5 of 7; rich_3935 has none.
     - The file was read on 8 of 8. The blind prediction was 6.
   - The 14360 tie, resolved three ways (b / g / f, the literal class of the first call):
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
- **Remove:** EXP-042 §2's example search command, which is rich_4075's search term (1 trace).
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
Screener, EXP-042 section 2: the parenthetical example after "merely contains the word python" is rich_4075's
search term; replace it with "(for example a search for a version string)" and add a dated 9.10 item.

Lead, knowledge/plan.md EXP-043 entry (line 91 only):
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

## D-006 direction review, 2026-11-05 (verdict for D-006 and C-024: needs-work)

This section reviews `knowledge/directions/D-006-e4b-role-team-and-tool-adapter.md` and C-024. It is filed here because C-024 rests on EXP-043, following the D-005 review in `experiments/EXP-034/critic.md`. The frontmatter above stays EXP-043's.

**Verdict: needs-work on text, and on two kill criteria.** The E4B-only scope stands, and so does the stage order. Stage 0 can go on. Stage 1 should not be costed until the canary has the endpoints set out below. This verdict decides no GPU spend.

**Lead's fixes from the EXP-033, EXP-032 and EXP-028 reviews: confirmed.** All are in one commit, 7756057:
- C-003 is supported and C-005 refuted, each with a history line.
- C-007, C-008 and C-002 stay hypotheses, each with a "status unchanged" line.
- The C-004 history line, the plan text and the briefing text are as I proposed them.
- No stale anchors remain.

### Facts in "How is it done today?"
| Line | Fact | Check |
|---|---|---|
| 17 | v24 is 3,162 bytes | Holds: the EXP-027 and EXP-033 trees at HEAD. |
| 18 | E4B 5 of 48, mean 85.7 s | Holds: SD 43.6 s, SE 6.3 s. |
| 18 | On 8 tasks no edit applied, from paraphrase or a repeated match | **Partial.** That covers 27 of the 39 failed calls (b 16, g 11). Also in the table: f 6 calls on 3 tasks (rich_3935 is class f, 4 of 4 calls), c 5, h 1. EXP-043 §9.2 and §9.7 item 7 add that 6 of the 16 b calls (fastapi_14459, rich_3676) ran past the last line read, which exact copying does not fix. |
| 18 | 16 of 19 control losses | Holds. The 19 are the informative-27 ids that neither arm resolved (EXP-041 control). |
| 19 | 31B 58 of 175 lost, "not a model habit" | **Numbers hold, the inference does not.** On the same server the E4B lost 9 of 156 `edit_file` calls (5.8%, 6 tasks; EXP-038 `n_edit_arg_loss`). EXP-024 found 53.5% at thinking 256 against 18.2% at 4096, confounded with the cap. One shape, from the parser; the rate depends on what the model emits [I]. Arm RH's drop from 67 lost calls to 17 is not evidence for this. It is mostly fewer retries after a first loss and fewer `edit_file` calls; tasks with a loss were 5 vs 3, p = 0.73 (my EXP-028 review). |
| 20 | "not followed, whatever the prompt's length" | **Overstated.** No arm varied length. The proposer held on 5 of 8, and RH's section moved behaviour (heredoc edits 43 to 135). The three counts hold. |
| 21 | EXP-032, EXP-040, lit note | Holds: EXP-040 had D = 0 of 8. The lit note's smallest positive result is gpt-oss-20B on Towers of Hanoi, not on repair. |
| 22 | Rank up to 128, one adapter per agent, sample ships a tool adapter | Holds: `MAX_LORA_RANK`; host quote in digest 2026-11-05 line 97; sample ships `main_lora` and `tool_lora`. When adapters are mounted, the wheel's server enables LoRA, sets max-loras to the number mounted and rounds the rank up from them [V, wheel]. |
| 22 | "the one public same-model adapter" | **Ambiguous in an E4B direction.** C-013's adapters are the rank-3 team's, on the 31B (scouting note §5) [M]. Not cited: `untrusted/boristown-e2b-lora-baseline-2026-11-05/`, an E4B with a declared adapter, self-reports 0.03 to 0.06 on the LB across versions [M]. That is inside the 4-task MDE, with prompt changes and no no-adapter control, so it settles neither Q4 nor C-024. Digest row 755677 (11-04, adapters scoring zero) is unread. |

### Kill criteria and the 225 s bound
- **Team line, the applied-edit test.** "Below the single loop's on the same ids" cannot work on smoke-8: there the single loop applied an edit on 8 of 8 (EXP-038 summary). One miss kills, and no gain is possible. It needs an absolute floor, or a reading on failed-edit-8 paired with the unchanged tree, as EXP-044 does.
- **Team line, "editor is reached".** This must mean reached with at least k counted calls and s seconds left. EXP-032's editor had 0 guaranteed calls on 7 of 8.
- **No pass row is written for either line.** "Neither line passes" needs one. A time kill belongs in the screen.
- **Adapter line, the canary.** "No output change" passes on noise: the E4B samples at temperature 1.0 (EXP-033 sampling). A silent failure is also possible. In `data/src/adk_submission/adk_submission/server.py` (lines 432 to 439) an adapter name maps to the base model, with no error, unless the server is vLLM with LoRA enabled [V, wheel]. Pre-register three conditions:
  1. The server lists the adapter and answers under its name.
  2. At temperature 0, adapter against no-adapter differs by more than no-adapter against no-adapter.
  3. The adapter is built to have a large effect, so a null means the adapter was not applied.

  Record completion, the empty-patch rate and malformed calls; rank-3's v21 adapter made the 31B stop early and empty in 54.3% of tasks. A pass in a Kaggle notebook tests that notebook's server, not the scorer's. Only an LB upload of a signature adapter tests the scorer [I].
- **Adapter line, the data clause.** It is right (plan.md:52). Add [I]: windows cut from dev-48 repos contaminate the dev-48 screen, and pairs built from Python source that is not competition data avoid both problems.
- **The 225 s bound.** (10.5 − 2.98) × 3600 / 120 = 225.6 holds: EXP-038 row T, with E7 = mean × 120 + 0.12 h. But a tree replaces the loop. The test is the tree's own measured dev-48 mean, at about 311 s or less, not "adds 225". That mean cannot come from smoke-8: the same 8 ids gave 56.9 s in EXP-033 and 78.3 s in EXP-038.

### C-024, "about 1 task of 48"
Fair as a ceiling, not as an estimate.
- The arithmetic is 8 × 5/40 = 1.0.
- Three of the 8 are gated (fastapi_13786, fastapi_14360, fastapi_14459). The E4B resolves 0 of 15 gated tasks even after re-grading. That leaves 5 tasks.
- The non-gated rest is 28 tasks, of which the E4B resolved 5. Or 4 of 22, after dropping the 5 tasks the gold patch fails and requests_6644, which the unpatched base resolves. Either way, 5 tasks give 0.9.
- About 3 of the 5 (fastapi_15661, fastapi_14873, rich_3063) fail the way the adapter targets: about 0.5 [I].
- R and RH resolved 0 of the 8 as run, against 8 and 9 of the clean 22, so these tasks look harder than average [I].
- Any harm an adapter does is not counted (C-013).

Range 0 to 1. That is below both MDEs, so the endpoint is the applied-edit share.

### Stage order
- **Canary before training: right.** Put one zero-GPU read before it: the kaggle-scout reads 755677, and 755611 if that is the LoRA-fixes topic. If an adapter scored non-zero, and differently from its base, after the patch, Q4 moves without a canary.
- **Sequential before parallel: right.** See EXP-007; the host also says ParallelAgent runs tool calls sequentially [M].

### Direction questions
- **Weakest assumption: principle 1.**
  - The wheel's agent schema forbids keys it does not list, and `output_schema` is not among them. Its callback fields resolve through a registry that swegemma never fills [V, wheel]. So only a tool-less agent ends by construction.
  - A reader or editor with tools ends only when the model stops or the shared counter runs out.
  - Test: the desk check names what ends each stage, and the screen records calls per stage.
  - Mitigation [I]: the E4B averages 8.9 of 28 calls.
- **Evidence the other way:**
  - C-013: −10.8 points, and v21's early stops.
  - An E4B adapter notebook at 0.03 to 0.06 [M].
  - No positive voting result below about 20B.
- **What a top-5 team would do [I]:** fix the E4B single loop as the small-model final (EXP-038 row 3: admissible). They would get one more measurement of it and keep D-006 as paper material. Stages 4 and 5 are unlikely to reach a verdict before 2026-11-12.
- **Missed option:** an editor sub-agent at low temperature (its own `generate_content_config`), or a non-`edit_file` retry route after a not-found error. Either needs no training and no Q4, and screens on failed-edit-8 like EXP-044.

### Replacement text (lead)
```
D-006 line 18, parenthetical -> "(EXP-043, 39 failed calls: 16 paraphrases, 6 of them past the last line read;
11 exact copies matching more than once; 6 lost or malformed arguments, all 4 of rich_3935's; 5 single-line
misquotes; 1 escaping)". "16 of 19 control losses" -> "16 of the 19 tasks neither arm resolved on the
informative 27".
D-006 line 19, from "the lost calls arrive" -> "the loss has one shape, a missing argument from the server's
tool-call parser, but its rate depends on what the model emits: the E4B lost 9 of 156 on the same server
(EXP-038), and the 31B 53.5% at thinking 256 against 18.2% at 4096 (EXP-024) [I] (C-004)."
D-006 line 20: "are not followed, whatever the prompt's length:" -> "are not reliably followed (prompt length was
never varied):".
D-006 line 22, last sentence -> "The one public adapter with a measured effect is the rank-3 team's, on the 31B,
trained on whole task trajectories: -10.8 points locally (C-013). A public E4B notebook with a declared adapter
self-reports 0.03 to 0.06 on the LB [M], inside the 4-task MDE, with no no-adapter control."
D-006 line 35: "is worth about 1 task of 48" -> "is worth at most about 1 task of 48, probably less (3 of the 8
are gated, about 3 fail the way the adapter targets, and the 31B resolved none of the 8)".
D-006 line 38, first clause -> "killed unless the server lists the adapter and answers under its name, and at
temperature 0 the outputs with and without an adapter built to have a large effect differ by more than two
no-adapter runs do; a Kaggle-notebook pass tests that server, not the scorer's".
D-006 line 39 -> "a tree is killed at its screen if the editor starts with at least k calls and s seconds left
on fewer than 6 of 8 tasks, if fewer than N of 8 end with an applied edit (the single loop: 8 of 8 on smoke-8),
or if its mean wall is above about 311 s; k, s, N and the pass row are written before the screen; one fix and
one re-run at most."
D-006 line 41 -> "Time: a tree ships on 120 hidden tasks only if its own measured dev-48 mean wall is about
311 s or less (10.5 h less the 0.12 h kernel overhead, over 120), about 225 s above the single loop; a smoke-8
mean does not count (the same 8 ids gave 56.9 s and 78.3 s)."
C-024 expected gain -> "at most about 1 task of 48, probably less [I]: 3 of the 8 are gated (the E4B resolves
0 of 15 gated even re-graded); the other 5 at the non-gated rate (5 of 28) give 0.9; about 3 of the 5 fail
the way the adapter targets; Arm R and RH resolved 0 of the 8 as run. Not measurable on resolves."
C-024 tests -> "none; gated on the Q4 canary. Endpoint when tested: share of failed-edit-8 tasks with an
applied edit, paired against the unchanged tree (EXP-044's design), with empty-patch rate and wall recorded."
```

### Not verified
- The 755677 and 755611 topics: unread.
- Whether the scorer's server matches the wheel's.
- The untrusted notebook's LB claims.
