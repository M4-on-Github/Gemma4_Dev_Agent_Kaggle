---
id: EXP-032-critic
exp: EXP-032
tier: prereg
verdict: needs-work
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
