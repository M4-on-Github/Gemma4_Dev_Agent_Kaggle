---
id: EXP-038-critic
exp: EXP-038
tier: full
verdict: accepted
verified: regenerated
date: 2026-11-05
---

## Verdict
**needs-work. The estimate does not honestly meet "only 1 hr": hold the push for the user.**
- My central estimate is about 1.25 to 1.3 GPU-h. I put about 25% on the run going above 1.5 h, and about 45% on it going above 1.34 h, the room left under the 3.2 h ceiling.
- Those figures weight the ratio-of-means bootstrap above the mean-of-ratios one, because a mean of ratios is biased upward on 8 noisy denominators.
- 0.88 h is not a credible point.

Four text fixes are needed and nothing has to be rebuilt.

## Cost (item 1)
- **The script is built right.** `cost_estimate.py`, re-run into scratch, gives byte-identical output. Time outside `wall_s` is 0.02 s per task in the E4B log and 0.07 s in R's, so the 444.8 s overhead is fixed. The McNemar thresholds check by hand.
- **Point A should not be offered as a point.** Arm R capped on 22 of the 40 ids outside smoke-8, against 1 of 8 inside it, so dev-48 is harder than smoke-8.
- **1.466 is defensible, but it is one of several scalings.** The 8 pairs couple only weakly (per-task wall correlation 0.23, turns 0.62). Other scalings give 0.94 to 1.46 h, with most between 1.23 and 1.30 h. Bootstrapping the 8 pairs gives these probabilities [mine]:

  | Estimator | P(> 1.34 h) | P(> 1.5 h) |
  |---|---|---|
  | Ratio of means | 0.35 | 0.17 |
  | Mean of ratios | 0.67 | 0.41 |

  Arm R's walls are censored at the caps, so scaling by them understates the difficulty [I].
- **Scenario C (2.41 h) gets under 5% from me [I].** All 8 E4B tasks ended by submit after 1 to 15 counted calls.
- **The ledger sum uses a point estimate as if it were a bound.** "1.86 + 1.24 = 3.10" treats B as an upper end, the same error as EXP-037 fix 2.

## Pre-registration checks
- **P1: fail, Row 0.** The clause "5 or more rows carry a non-empty `error`" fires on Arm R itself: 10 of R's 48 rows carry the harness cap strings (6 "Agent exceeded session timeout", 4 "turns budget"). A cap-bound E4B would therefore read as a crash, and Row T's cap-bound branch could never be reached.
- **P2: pass, with one inconsistency.** E8 at 1.05 h does not follow from E3's 75 s mean, which gives 1.12 h. Both sit below §2.2's point B.
- **P3: fail, E7.** `estimate_budget.py --results` takes the larger of the wall and a decode estimate. On EXP-033 it gives a mean task of 2.91 min (5.82 h projected) against a measured 56.9 s. Even at `--tok-s 56.4` it gives 2.69 h. Row 2 also uses 11.0 h where the plan's rule is about 10.5 h.
- **P4: pass.** R's 9 resolves include the free `requests_6644`, so there can be at most 8 R-only tasks; §4 states the power limit.
- **P5: pass on the hidden-set clock.**
- **P6: pass.**
  - Only the model line differs.
  - R's as-run agent directory is identical to EXP-027's tree.
  - 1cd52f8 is the only execution change to the notebook.
  - The zip sha, `TASK_IDS` and the metadata match.

## Items 2 to 5
- **Readings.** They cover both directions, the test is paired, and "admissible" means a proposal only. One wording issue: Row 0b treats any as-run resolve of a gated task as a grader change. A resolve whose patch creates the missing module is not one.
- **Pairing.** It is fair, and the 28-of-48 and 43-of-48 ceilings match C-022. The re-grade in §3.3 has no fault row.
- **Row T.** "Room" as 480 minus wall includes grading and ignores the total clock. Under the 10.5 h rule, 120 tasks allow about 311 s per task on average, so at an 85 s mean the room is about 225 s, not 395 [I]. A voting design priced against EXP-033's 423 s would overrun the 12 h clock.
- **Unreadable at 48.** Only the Row 0 and E7 defects.

## Required fixes (text only, no rebuild)
1. **Row 0:** count only errors other than the harness cap strings.
2. **E7 and Row 2:** read the mean `wall_s` x 120 / 3600, plus the measured overhead, against about 10.5 h. Record `estimate_budget.py` without reading it.
3. **Row T:** define the room in full:
   - the per-task room is 480 minus `wall_s`, a lower bound;
   - the total-clock room is (10.5 h minus E7) x 3600 / 120;
   - the smaller of the two binds;
   - report the mean and the p10, headroom on calls and on turns, seconds per turn as wall sum / turn sum, and the number of capped tasks excluded.
4. **§2.2 and §4.2:**
   - state the central estimate and the probabilities above;
   - make E8 consistent with E3;
   - narrow Row 0b's gated clause;
   - add a fault row to the re-grade: fewer than 48 graded, or GOLD or BASE grading differently from EXP-036.

**Option for the user [mine].** Run only the 27 informative ids. E2 stays intact, because the other 21 are expected to be concordant, and the run takes about 0.75 h. It loses 21 tasks of the time profile and the gated re-grade.

## Re-review 2026-11-05 (after 4024082)

**Verdict: needs-work. Fixes 1 to 4 hold. The new section 8 clause needs two dated notes, and two one-line notes follow from the fixes. Nothing is rebuilt.** If fixes 5 to 8 are committed with the text below verbatim, the push needs no further critic read [mine].

What I checked: `git diff 143fba1 4024082` on the EXP file, on `cost_estimate.{py,json}` and on the README row. The script, re-run into scratch, gives byte-identical JSON.

**Fixes 1 to 4**
- **Fix 1 holds.**
  - The amended Row 0 counts 0 errors on Arm R, where 10 of 10 error rows are cap strings, and 0 on RH (8 of 8).
  - It still catches a failure before the loop, fewer than 44 rows, and non-cap errors.
  - It leaves one gap, closed by fix 7.
- **Fix 2 holds.**
  - E7 for R: 297.44 s x 120 + 555.5 s = 10.07 h.
  - Row 2 threshold: (37,800 - 444.8) / 120 = 311.3 s.
- **Fix 3 holds, and the split is sound.**
  - One count picks the branch: calls or time cap, 23 on R. The room is measured on U under either branch, so no row fires two ways.
  - R's one turns-only task is in neither set, as the file states (24 excluded).
  - Every field exists in `summary.jsonl`. `n_calls` over U is at most 27.
  - On R the per-task room has mean 237 s and p10 101 s. The total-clock room is 13 s, so the total clock binds.
- **Fix 4 holds.**
  - The §2.2 figures match my review.
  - E8 = 75 s x 48 + 444.8 s = 1.12 h.
  - Row 0b and row F are as asked, and the patch path matches R's layout.
  - Keeping 75 s is right. The prediction is the experimenter's blind call; both figures carry their source and both get scored.
- **Item 6.** Every changed first-written line is either struck and kept, or extended by a dated note. Nothing is deleted.

**New defects**
- **A. A truncated run has no reading of its own.**
  - It inherits Row 0's "infrastructure, not the model", and a cancel counts as a "Kaggle stop" there.
  - A truncated run always has fewer than 44 rows, and nothing orders the truncation clause against the crash clauses.
  - Line 210 would also apply Row T to its partial rows.
  - The reading matters for cost. Read as infrastructure, a re-run is priced at 1.25 to 1.3 h. Read as a truncation, the run shows that estimate is wrong.
- **B. The stop rule cannot fire as written [I].**
  - No agent is woken at a set time.
  - The lead's commands are git and `kaggle kernels status`, and the screener has no clock command (EXP-032 push record).
  - If no one acts, the run continues.

**Required fixes (dated notes, text only)**
5. Under Row 0's reading, add: "*Added 2026-11-05 (critic re-check):* a run cancelled under the section 8 stop rule is read as **truncated**, neither infrastructure nor a model reading. It is read as a crash instead only if the surviving output shows a failure before the task loop, or 5 or more errors counted under the clauses above among the surviving rows. Report the elapsed time at the cancel, the number of surviving rows, and their mean `wall_s` and capped count. No endpoint is read and row T is not applied. A re-run is priced from these figures, not from section 2.2."
6. In section 8, add: "*Amended 2026-11-05 (critic re-check):* the push record states the push time in UTC, and the lead's push report gives the user two clock times, push + 1.75 h and push + 2.0 h. The decision at push + 1.75 h is the user's, made from the Kaggle UI. If no one acts, the run continues to its end, 2.0 h is not enforced, and the exposure is section 2.2's tail (scenario C 2.41 h, conditional worst case 6.66 h)."
7. Under Row 0's fix-1 clause, add: "*Added 2026-11-05 (critic re-check):* a cap-string row whose `n_turns` is 0 counts as an error."
   - Without it, a model server that stalls into session timeouts reads under row 1.
   - Every cap-string row in R and RH has at least 12 turns, so the rule cannot fire on a real cap.
8. In the README row, strike "kernel about 1.05 h" and add "1.12 h (restated)".

**Not required.** Lines 210 and 258 disagree on whether Row T follows rows 0b to 2. The disagreement predates the fixes.

**For the user's decision at 1.75 h [I].**
- My bootstrap p90s, 1.61 h and 1.76 h, put about 5 to 10% on the run not being COMPLETE at 1.75 h of GPU time. Queueing adds to the elapsed time.
- Whether a cancelled kernel keeps any output is unverified: EXP-032's cancelled version was never downloaded.
- So cancelling at 1.75 h buys protection against the tail, at the risk of losing the whole spend.

## Results review 2026-11-05 (a1365bc)

**Verdict: accepted. Row 4 governs, applied as written and amended; row T takes "otherwise", with 225.6 s of total-clock room per task. Every §9 number regenerates. No required fixes.**

**Tier.** The lead dispatched `light`. I raised it to `full` because item 5 asks for a status move, and the checklist reserves status moves for `full`. I ran checks 1 to 6, 8 and 9; check 7 is n/a.

**Audit**
1. **Order: pass.** Fixes 5 to 8 (7964379, 19:00:47 UTC) were committed before the push at 19:02 UTC. Up to a1365bc, the file gained only §8's push record, the Status line and §9 below the line. Two later commits added more: 2eab7b4 a dated §7 item 9 (a re-grade build defect, with no reading changed), and 9ec5c7d the re-grade push record. I have not reviewed either.
2. **Cohort and arms: pass.**
   - The `summary.jsonl` ids equal dev-48 and match Arm R's.
   - The as-run agent tree is the same as `experiments/EXP-033/candidate-e4b` (`diff -r`).
   - The embedded zip is `9de869bd...`.
   - `task_results` carries 8 min and 28 calls.
3. **Numbers: pass.**
   - `analyze_traces.py`, re-run into scratch, gives a byte-identical `summary.jsonl` and `aggregates.json`.
   - The pair table from the two summaries is 5 / 4 / 0 / 39, exact p = 0.125. The 27-id table is as stated.
   - E7 = (85.71 x 120 + 445.6) / 3600 = 2.98 h, and the total-clock room = (37,800 - 10,731) / 120 = 225.6 s.
   - The per-task room over U (48 tasks) has mean 394.3 s and p10 332.5 s.
   - The log ends at 4,559.9 s. Wilson gives 4.5-22.2%.
4. **Readings: pass.** I applied the rows myself before reading §9.4:
   - Row 0: 1 counted error (fastapi_13537, not a cap string) and 0 cap-string rows, so it does not fire.
   - Row 0b: the constants match C-022, and 0 of 15 gated tasks resolved.
   - Row 1: 38 of 48 non-empty and 0% malformed.
   - Row 2: E7 2.98 h.
   - Row 3: p = 0.125.
   - So row 4 fires, as in §9.4.
5. **Statistics: pass.** The test is paired McNemar, and the 9-against-5 marginals are not read.
6. **Budget: pass.** E7 includes the measured overhead.
8. **Scope and hygiene: pass.** §9.6 claims no more than §5 licenses. The hygiene check is OK on the five committed result files.
9. **Reproducibility: pass.** The zip was reproduced at the prereg.

**Item 3: what the data can and cannot exclude [mine].** §9.4 and §9.6 already say the result is not evidence of equality.
- The paired difference, R minus E4B, is 4 of 48. Its 95% interval (Newcombe paired score, continuity-corrected) is -0.5 to +9.1 tasks.
- The upper end exceeds the largest deficit this design can show, which is 8: R's 9 minus the free requests_6644. So the top of the interval carries no information.
- So the data rule out an E4B advantage of more than about 1 task, and rule out no E4B deficit at all.
- For row 3 to fire, the E4B had to lose 6 of R's 8 non-free resolves and gain none.

**Item 4: "admissible" is all the result supports.** An S-NNN also needs:
- **The §5.8 override, written out.** The first line of §5.8 asks for a worst case of at most 11 h. This tree's worst case is 16.00 h by `analyze_traces`, and the packer's 120 x 9 min gives 18 h. The override must be recorded as #11's was (EXP-027 §2). E7 meets only the operational 10.5 h rule.
- **A predicted k of 58.** dev-48 rates do not map onto the board (§3.2).
- **The re-grade result, F and G.** Admissibility does not depend on it, but G is unknown until the re-grade runs.
- **fastapi_13537, listed as a resolve risk.** It is not a clock risk (see the analysis below).

**Item 5: claims.**
- **C-020** may move to `supported`. Confidence is high for the time profile on dev-48; that it carries over to the hidden repos is my inference.
  - **Its title must be restated.** "Without malformed calls" and "about a minute per task" both come from smoke-8. dev-48 shows an uncounted format failure and an 85.7 s mean.
  - Wording I accept: "The E4B runs the shipped v24 single loop at 8 min / 28 calls well inside the clock: on dev-48 (EXP-038) 0 of 48 tasks hit a cap, the mean task wall is 85.7 s (max 207.3 s), and the projection is 2.98 h for 120 tasks against the 10.5 h rule. `analyze_traces` counts 0 malformed calls in 478. That count does not see one task, fastapi_13537, which wrote its calls as text and ended with 0 tool calls. For an E4B upload of this tree the clock is not the constraint. It resolves 5 of 48 as run against the 31B's 9 (paired 4-0, p = 0.125), which does not show that the two are equal."
- **C-023** keeps its status and may cite: "On the E4B single loop, the 10.5 h rule leaves 225.6 s per task on average for an extra stage (EXP-038 row T). This binds before the per-task cap room, mean 394 s. A voting tree's dev-48 mean task wall must stay below about 311 s."

**Item 6: no note is needed.**
- The two p90s differ only by method: nearest-rank gives 147.2 s and interpolation gives 147.5 s. No reading uses p90.
- `estimate_budget` (7.77 h, BLOCK) is correctly recorded and not read. It belongs in the S-NNN, under item 4.

**Analysis [mine, I]**
- **The E4B stops early.** The clock is slack because the E4B stops early, not because it solves faster:
  - its median first edit is at turn 6, against R's 14;
  - 47 of 48 tasks end by submit;
  - no task uses more than 21 calls.
- **Why the E4B trails by 4 (competing explanations):**
  - it submits before the fix is complete (an early stop);
  - it edits the wrong file;
  - it cannot write the fix even when it finds the right file;
  - chance, since 4-0 is consistent with no deficit.

  The cheapest test is below, at zero GPU.
- **fastapi_13537 is a format failure that no endpoint counts.**
  - Three of its replies put a tool name inside a fenced block, each one after a harness continuation nudge, and the task ended with 0 tool calls.
  - `n_malformed` counts only a tool-call token left in the content. So "0 malformed" does not mean that every intended call parsed.
- **Instrument gap, for the experimenter.**
  - `nudges` counts only user-source markers, so it misses the harness's `continuation_nudge` system events: 9 on 7 E4B tasks and 2 in R.
  - As a result every `nudges` value reads 0.
- **Run-to-run spread.**
  - On the 8 smoke ids the E4B averaged 78.3 s here, against 56.9 s in EXP-033. The other 40 ids averaged 87.2 s.
  - So most of the 1.51x gap between dev-48 and smoke-8 is run-to-run variation, not task mix (one pair of runs).
  - EXP-040's 140 s wall bar sits on a reference that moved about 38%.

**Suggested next.** All zero GPU:
- mine the 4 R-only ids (fastapi_13537, fastapi_15589, fastapi_9753, rich_3067): E4B call counts and first-edit turn, and the files edited against the gold files. This separates the first three explanations; chance needs a larger cohort;
- fix the `nudges` count in `analyze_traces.py`;
- read the re-grade (F, then G) when it completes. It is already running on CPU (9ec5c7d).

## Re-grade review 2026-11-05 (9c68639, with 2eab7b4 and 9ec5c7d)

**Verdict: accepted. Fault row F does not fire; G = 0 of 15 takes the "G <= 1" row. Both were applied as written and in order, F first. Every §9.7 number regenerates.** This section is a `light` review. The frontmatter keeps `full` from the review above, on which C-020 rests. The corrections at the end do not gate.

**Audit**
1. **Order: pass.**
   - §3.3's G rows and row F predate both commits.
   - 2eab7b4 (20:50:06 UTC) adds §7 item 9, dated, and the checklist allows that above the line. The push followed at 20:50:23 UTC.
   - 9c68639 touches only the Status block, the README row and the text below the line.
2. **Cohort and build: pass.**
   - In all three passes the ids equal dev-48.
   - Rebuilt into scratch with its default flags, the builder reproduces the untracked EXP-036 notebook byte for byte (`73df67c8...`). The flags rewrite the template only when they differ from the defaults.
   - The EXP-038 build equals the pushed notebook (`4932f0bc...`). Its metadata differs from EXP-036's only in id and title.
   - The patches and the `regrade_patches.py` that ran equal the repo copies.
3. **Numbers: pass.**
   - `analyze_regrade.py`, run with only `OUT_DIR` pointed at scratch, gives the same `summary.jsonl`. Its `aggregates.json` is the same once line endings are normalised: `write_text` writes CRLF on Windows.
   - GOLD's and BASE's exit codes, tails at the cap, shim drops and the -9 id all equal EXP-036's.
8. **Hygiene: pass.** The check is OK on six files. The outputs hold only ids, booleans, exit codes and error class names, and §9.7-9.8 quote no tail or patch text.

**Item 3.** The 7-0 may be cited only within the block below.
- Four of its discordant pairs are the as-run informative split. The other three are gated tasks that R resolves only with the stand-ins.
- It grades the same patches under a condition that neither tree ships.
- Any stronger use (the abstract, "finding", a claim move) needs a `full` review on new ids.

**Item 4.**
- **The rule matches EXP-036 by construction:** the same `err_files`, and the same group (unresolved under the re-grade, the patch touches a gold-patch file, exit 2).
- **The three exit-2 tasks that are not own errors** fail on exactly BASE's file sets.
- **The fastapi_15800 call is sound, but its caveat is wrong.** The call fires on BASE exiting 1: no collection interruption, and the summary is present. BASE's capped tail therefore never enters it, and it is as firm as fastapi_14964 and fastapi_15280.
- **"5 against 2" needs its denominators:** 5 of 21 against R's 2 of 27 and RH's 2 of 22. Paired with R it is both 2, E4B only 3.

**Item 5.**
- The C-020 and C-022 lines stand. C-022's line understates: 14 gradings now agree.
- C-021's "not model-independent" overstates. On the gated 15, paired, the E4B is 0-3 against R (p = 0.25) and 0-5 against RH (p = 0.0625).

**Permitted and corrected text** (copy as written):

```
Item 3, ledger and paper, as a ceiling:
"Re-graded with stand-ins for two test-only packages (a grading condition neither tree ships; its match to the
hidden scorer is unknown), the 31B's v24 loop resolves 12 of 48 dev-48 tasks and the E4B 5. Paired, that is 7-0,
exact McNemar p = 0.016, which EXP-038 section 3.3 reports with no reading. Three of the 7 are gated tasks that
only the stand-ins make resolvable for R. The pre-registered as-run comparison is 4-0, p = 0.125: no difference
detected."
Not to be called significant or detected, and not to be read as the E4B being worse on the hidden set.

C-021, replacing the 57d60be history line (lead):
"history: 2026-11-05 note, status unchanged: on the E4B's patches the stand-ins flip 0 of 15 gated tasks
(EXP-038 re-grade, 9c68639), against 3 (R) and 5 (RH). Paired on the 15, the E4B is 0-3 against R (p = 0.25)
and 0-5 against RH (p = 0.0625), so the data do not show whether the gain depends on the model. C-021's 3 to 5
is a 31B v24 figure. 5 of the E4B's 21 unresolved patches that touch a gold-patch file break collection
themselves (file-set rule), 3 of them gated."

C-022, optional (lead): "in ten gradings" -> "in fourteen gradings (adding the E4B as run and re-graded, and
GOLD and BASE repeated in the EXP-038 re-grade)".

knowledge/plan.md, the re-grade entry (lead): strike "the last is the least certain". Replace "Reading it
needs a new pre-registration" with "Reading it needs new ids (held-out-24) or a replicate run; a
pre-registration written now on these 48 would be post hoc."

Section 9.7, a dated note under the fastapi_15800 caveat (experimenter):
"*Corrected 2026-11-05 (critic light):* the fastapi_15800 call does not use BASE's file set. It fires because
BASE exits 1, with no collection interruption and its summary present, so it is as firm as fastapi_14964 and
fastapi_15280. The capped BASE tail does not weaken it."
```
