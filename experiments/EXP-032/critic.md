---
id: EXP-032-critic
exp: EXP-032
tier: light
verdict: accepted
prereg_verdict: needs-work
verified: regenerated
date: 2026-11-05
---

## Verdict
**needs-work. No section needs re-registration.** The design carries the D-004 fixes and the build is correct. Four readings can misfire, though: row c (degenerate), row b (attributes an editor-stage crash), E11 (confounded), and the residue of fix 5. P1 may be pushed once §7 commits items 1-6 below. No second critic round is needed; the lead checks the §7 diff.

## Audit
- **Build, pass (regenerated).**
  - The cohort rule reproduces exactly: 18 -> 12 re-capped in RH -> the 8 listed.
  - `diff -ru` against EXP-027 shows only `eval_config.yaml`.
  - Validator output matches §2 to the count.
  - The embedded zips decode to the §2 shas, and both carry 240/43/8/100.
  - Parameter cells: EXP_ID quoted, RUN_AGENT True, TASK_IDS = cohort. The metadata differs from exp028_armR only in id and title; the model is 31B.
  - The P1 model resolves: all four LlmAgents declare 31B.
  - The push-guard regexes pass.
  - Correction to §7 item 1: the zips are untracked (`dist/`), though the embedded shas match.
- **Fixes 1-4, pass.**
  - The budget guarantee is stated honestly as soft.
  - Roles are bound by the tool list.
  - The editor uses `none` with placeholders.
  - Caps are identical.
  - Class (i) is counted apart from compaction.
- **14,336, measured margin.** On these ids, Arm R prompt tokens at turn 6 were 4,136-10,951 (120-line reads, thinking 4096). The exception is rich_4070: RH reached 14,126 at turn 6 and 14,532 at turn 7. The margin holds by instruction, not by construction: `read_file` without `end_line` returns 150 lines.
- **Row a cannot practically fire.** The paired RH−R SD on these 8 is 114 s, so SE = 40 s, and P1 would need to be about 66 s per task faster than Arm R. Row c's first clause needs kT ≥ 4, against kR = 1. The live rows are 0, b, d, e and f.
- **Wall rule.** It can be computed from P1 and Arm R `summary.jsonl` alone. 8 min is the right screen cap, because it is Arm R's.
- **Cost, believable.**
  - Measured Arm R kernel overhead is 555 s (0.15 h).
  - On these ids the 28th call came at a mean of 191 s, and the post-cap tail averaged 78 s. T4 should therefore take about 372 s per task, about 0.97 h. P1 should take 0.95-1.2 h.
  - The 2.0-2.5 h estimate is conservative.

## Required fixes (§7 additions)
1. **Push order.**
   - Push P1 first. Push T4 only if P1 is not row 0 and has no localize-stage row-b crash. This saves about 1 h at the EXP's own odds.
   - Apply row 0 per arm.
   - Without T4, read row b's T4 clause against Arm R+RH: 0 class (i)-(iii) in 96 tasks with 98 compactions. Their errors are only turn-budget and session-timeout endings.
2. **Row b and E1.**
   - Record the author of the last step before each defect error.
   - A crash only in the editor stage goes to row f, because T1 keeps the same editor.
   - Class (iii) excludes TaskGroup errors whose inner error is a budget, timeout or sandbox error.
   - Cap endings are E6 outcomes, not crashes. Arm R hit 80 turns on 3 of these 8.
3. **Row c, submit clause.** Define it as `submit_patch_called` and not `calls_cap_hit` and not `time_cap_hit`. Add a floor: T4 must do this in ≥2 of 8 (R and RH: 0 of 8). Without the floor, 0 vs 0 fires row c ahead of row f.
4. **E11 baseline and confound.**
   - kR = 1 of 8 in both R and RH (rich_4070, call 3 and call 4).
   - T4's prompt sets the edit deadline at call 12. P1's editor is told call 8 and to edit first from Report A, and its index is counted from the editor's own first call.
   - So kT ≤ 2 is near-certain, and kP ≥ 5 means "Report A named a gold file and the editor complied", not "the parallel stage locates better". Say so in §5.
   - Report P1's global index too.
   - Normalize `filepath` by stripping `/workspace/`.
5. **Fix-5 residue.** Rows a and d also require E7 nudges in ≤1 of 8. If E4 shows a re-read of a report-named file before the first edit in ≥6 of 8, row d reads as row f.
6. **P2 and the localizer read check.**
   - State a predicted kP and a predicted P1 mean wall.
   - Report unranged localizer reads by author.
   - Replace "by construction" with "by instruction".
   - E1's remark about a "detector miss" has been stale since 4657dce.

## Results review 2026-11-05 (light, arm P1, 09ddb3a)

**Verdict: accepted.** Row e governs as written.
- kP = 1 on the strict reading and 4 on the attempt-inclusive one. Row e needs at most 4, so the loose reading sits exactly on the boundary and still holds.
- kT is read against kR = 1 (item 6).
- There are 0 defect crashes.

What the run supports is narrower than row e's text:
- a prompt-only 5-call limit was broken on 21 of 24 localizer branches;
- the readers took 43-45 of the 43 shared calls in 7 of 8 tasks;
- so the editor started with 0 guaranteed calls in 7 of 8, and 18 in fastapi_14609.

The parallel stage's value was not tested. It is parked, not refuted. T4 did not run.

**Audit**
1. **Order: pass.**
   - The §7 fixes went in at 40cc718 (13:27 UTC). Version 2 was pushed at about 14:15, and version 1's output was never read.
   - `git diff 40cc718 HEAD` adds only §7 items 14-15, the §8 records, §9 and Status.
   - The notebook is unchanged since 1118e9b.
2. **Cohort and arm: pass.**
   - The 8 ids equal capbound-8.
   - The run's `agent/` equals `candidate-p1`. The embedded sha was checked at prereg.
   - The only errors are the harness session timeout, on fastapi_14609 and rich_3063.
3. **Numbers: pass, with two corrections that move no row.**
   - `analyze_traces.py --out` (scratch) reproduces `p1/summary.jsonl` exactly. The kernel log spans 3,280.1 s.
   - My own author split from the traces reproduces, per task:
     - localizer calls a/b/c and calls before the editor;
     - 21 of 24 branches over 5;
     - editor guaranteed calls 0 in 7 tasks and 18 in one;
     - first editor step at 180.3-308.0 s.
   - kP is 1 strict and 4 loose. The loose count adds the refused gold-file attempts on fastapi_14873, rich_3676 and rich_4075, at editor index 1, 2 and 6. kR = 1 (rich_4070, call 3).
   - Paired wall against Arm R: +72.9 s, SD 83.3, SE 29.4, +2SE 131.8, 3 tasks above +90 s.
   - Crash strings: 0 of the class (i)-(iv) strings in traces, `task_results` and the log.
   - Nudges: 0 `continuation_nudge` steps, counted directly, so E7 = 0 holds.
   - **Corrections:**
     - (a) fastapi_14609's first gold-file edit is its 9th editor call, not the 8th: 7 reads and 1 command precede it. Its global index is 34, not 33.
     - (b) E1's peak over the other seven tasks is 16,687 (rich_4070), not 15,101. All 8 peaked above 14,336.
8. **Hygiene: pass.**
   - §9 names ids, counts, harness messages, our class strings and file paths. Gold file paths are paths, which my line allows; no gold text appears.
   - `p1/summary.jsonl` holds only the timeout message, repo names and ids.
   - The README row is clean.

**Scope.** §9's paragraph on what row e does not carry is the right text to cite downstream. The lead's plan entry is accurate, except that it does not say the parallel stage was left untested.

## Required fixes, results review (non-gating)

```
Experimenter, EXP-032 9 E11: "at its 8th editor call" -> "at its 9th editor call"; "25 + 8 = 33" ->
"25 + 9 = 34".
Experimenter, 9 E1: "and 15,101 over the other seven" -> "and 16,687 (rich_4070) over the other seven;
every task peaked above 14,336 (14,925 to 18,556)".
Lead, plan EXP-032 P1 entry: "the parallel stage is parked as row e says" -> "the parallel stage is
parked as row e says, untested rather than refuted (the editor had 0 guaranteed calls in 7 of 8)".
Lead, C-014 history: after "row e fired, parallel stage parked" add "; not evidence on delegation
capability, since the editor had 0 guaranteed calls in 7 of 8 (critic light accepted)".
Lead, C-023 sources: "EXP-032 P1 row e (prompt-only call limits ignored, the editor starved)" ->
"EXP-032 P1 section 9 E6 (21 of 24 localizer branches broke a prompt-only 5-call limit; the editor had
0 guaranteed calls in 7 of 8)".
```
