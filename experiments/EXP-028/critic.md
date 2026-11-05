---
id: EXP-028-critic
exp: EXP-028
tier: light
verdict: accepted
verified: regenerated
date: 2026-11-05
---

## Verdict
**accepted.** Section 9 applies section 4 as written.
- **Time profile.** T2 fires: 10.04 h projected, and 10.03 to 10.07 h across the three overhead windows, all inside T2's range.
- **Call cap.** T4 fires on both of D3's counts: 18 of 48 by the analyzer and 17 by the harness, with 0 resolved under either.
- **Recovery, first match.** Row 1 does not fire (R has 8 first-loss events) and rows 2-3 do not apply. **Row 4 fires:** RH 0 of 6, R 0 of 8, Fisher p = 1.0. Rows 7 and 8 do not fire.
- **Method.** The projection is the measured mean plus measured overhead, not the cap. Row 8 covered a blank or a crash. The ~280 s mean was stated before the run.

**Claims covered** (each one's tests line):
- **C-003: supported at T2, with no margin.** My inference: the wall SD of 124 s gives an SE of 17.9 s per task, about 0.6 h on the projection, so one SE reaches both the T1 and the T3 boundary. RH's rich_3480 ran 751.9 s, an overrun the projection does not model.
- **C-005: refuted on this prompt at this n.** 0 of 6 has a one-sided 95% upper bound of 39% (my computation). That excludes "≥ 60%" but not row 3's 25-60% band. D1 does not rescue it: in RH the earliest heredoc after a first loss is the 5th call (fastapi_15030).
- **C-007: premise only.** The cap binds, with 0 resolves among capped tasks. The gain from 40 calls is untested.
- **C-008: the v24 half only.** The measured rule gives 10.04 h against 18.00 h from cap x 120. The clause about our retired prompt is not tested here.
- **C-002: tests line only.** EXP-028 does not test the score.

## Audit
1. **Order: pass.**
   - ae7b045 was committed at 02:21:38 UTC, and both kernels were pushed at 02:21:44.
   - Since ae7b045 the EXP file's only deletion is §7's placeholder line; everything else is appended.
   - 4657dce adds D5 and regenerates the `compactions` field and nothing else.
   - The notebooks, candidate trees and section file are unchanged.
2. **Cohort and arms: pass.**
   - The embedded zips decode to c22069db… and 248dd8eb….
   - TASK_IDS and the 48 result rows equal dev-48.
   - Each run's `agent/` equals its candidate. R and RH differ by 15 lines, at 3,162 against 4,104 chars, and both run at 240/28/8/80.
3. **Numbers: pass, with one mislabel.**
   - `analyze_traces.py --out` (scratch) reproduces both summaries with 0 field differences. The README row reproduces.
   - Every §9.1 row reproduces from the summaries, `summary.json` and the log stamps. Residual overhead: 0.35 s per task measured from vLLM-up, 0.06 s from the first task start; each is under 0.02 h.
   - Every §9.2 count reproduces from my own lost-call pass and from `collect_forensics`, as do the §9.3 McNemar tests (1 vs 2 and 4 vs 3, p = 1.0) and §9.5's 14,832 s and 14,716 s.
   - **Mislabel, which moves no row (row 5 cannot be reached).** RH's "non-zero" heredoc counts are error-status results:
     - of the 36, 26 have a non-zero exit, 9 are call-cap refusals that never ran, and 1 is a timeout;
     - of the 10 template heredocs, 8 ran with exit 0 and the 2 counted are refusals;
     - after a first loss, 1 is a non-zero exit and 2 are refusals.
     R's 2 are real non-zero exits.
   - **Fisher test.** Fisher is the pre-registered test, but it treats the arms as independent although fastapi_14262, 14605 and 15661 appear in both. Moot at 0 vs 0.
   - **Lost calls, per task (mine).**
     - Tasks with any lost call: R-only 5, RH-only 3, McNemar p = 0.73.
     - Tasks with `edit_file` losses only: 5 against 2, p = 0.45.
     - The 67 vs 17 count rests largely on fastapi_14262 (26 calls).
8. **Hygiene: pass, one note.**
   - What §9, both summaries and the README row contain:
     - ids, counts and harness messages;
     - our own template marker;
     - run paths and tool names.
   - `check_repo_hygiene.py` reports OK.
   - Note: the three-character suffix quoted in §1 (line 29) and in C-004 (claims lines 57 and 62) is text the model wrote. It predates the dispatch's line; whether to change it is the lead's call.

## Required fixes (non-gating)

```
Experimenter, EXP-028 (append a 9.2 note or a section 7 D6; the 9.2 rows stay): the 135 / 36 heredoc
row counts error-status results: 26 non-zero exit, 9 refused at the call cap (never ran), 1 timeout;
template heredocs 10 / 2 / 3: 8 ran with exit 0, the 2 are call-cap refusals, 0 failed; heredocs after
a first loss 13 / 3: 1 non-zero exit, 2 refusals.
Lead, C-002 tests: "EXP-028 Arm R (time profile, complete, unanalyzed)" -> "EXP-028 Arm R (time profile
only, T2 at 10.04 h; not a test of the score; critic light accepted)".
Lead, C-003 tests: "EXP-028 Arm R (dev-48 time profile on our cohort, readings T1-T3)" -> "EXP-028 Arm R
(T2: 10.04 h from mean 297.4 s plus measured overhead, no margin, about 0.6 h per SE; one RH task ran
751.9 s against the 8-min cap; critic light accepted)".
Lead, C-005 tests: "EXP-028 Arm RH vs Arm R (complete 2026-10-29, unanalyzed; readings in EXP-028 §4)" ->
"EXP-028 Arm RH vs Arm R (row 4 fired: next call after a first loss is `run_command` in 0 of 6 RH and
0 of 8 R tasks, Fisher p = 1.0, one-sided 95% upper bound 39%; critic light accepted)".
Lead, C-007 tests: "EXP-028 Arm R (28-call incidence; reading T4)" -> "EXP-028 Arm R (T4 fired: 18 of 48
at 28 calls by the analyzer, 17 by the harness, 0 resolved; tests the premise, not the gain; critic
light accepted)".
Lead, C-008 tests: "EXP-028 Arm R (measured mean and overhead on dev-48 for the v24 tree)" -> "EXP-028
Arm R (10.04 h from measured mean and overhead against 18.00 h from cap x 120; admits 8 min for v24;
does not test the clause on our retired prompt; critic light accepted)".
Lead, plan: "T2 + T4 fire | | | 0 | awaiting critic `light` |" -> "T2 + T4 fire | | | 0 | critic light
accepted |"; "awaiting critic `light` (moves C-005)" -> "critic light accepted (row 4 supports moving
C-005)"; "every cap-hit task compacted" -> "every call-cap task compacted (18 of 18 R, 17 of 17 RH; 21
of 23 and 24 of 25 counting the time cap)"; "- Critic `light` review of EXP-028 (moves C-003/C-008 time
profile and C-005)." -> "- Critic `light` review of EXP-028: accepted (experiments/EXP-028/critic.md)."
Lead, briefing: "A single-argument shell route is the mitigation under test (C-005, EXP-028)." -> "A
single-argument shell route did not move the next call after a first loss (0 of 6, EXP-028 row 4;
C-005)."; "| EXP-028 | T1-T4, rows 1-8 | not asked | complete, unanalyzed | |" -> "| EXP-028 | T1-T4,
rows 1-8 | not asked | T2 + T4, row 4; critic light accepted | |".
```

Optional for C-004 (my count): on the shipped prompt, 58 of Arm R's 175 `edit_file` calls were lost (33.1%), in 7 of 48 tasks.
