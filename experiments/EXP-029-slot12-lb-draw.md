# EXP-029 — Slot #12: a second LB draw of the adopted v24-at-8 lineage

**Date:** 2026-11-03
**Type:** LB-only upload (#12), zero GPU. One draw of 58; no kernel, no dev-48 arm attached.
**Cohort:** n/a (public LB, 58 tasks)
**Ladder:** L3 (LB upload). L0 desk check done: EXP-027 §4 row 3 fired on #11 (0.17 = 10/58), EXP-028 is the L4 arm that picks the tree and cap. No lower rung can read what one LB draw reads (whether this tree completes inside 12 h on the hidden set, and a second draw of the baseline lineage).
**Pre-registered:** this file is committed **before** upload. Sections 3-5 are written blind and are not revised after the score. A badly drafted reading gets its defect logged in §7, not rewritten. Nothing here depends on the EXP-028 pick: §2 binds this file to whichever tree and cap EXP-028 §9 names, and §4 is written to govern either.
**Serves:** the main-track score; the pooled baseline estimate for the v24-at-8 lineage that every later arm (D-004 included) is read against; the paper track's LB-noise measurement (a second draw of a known-score config).
**Supersedes / relates:** EXP-027 (#11, the first draw; §4 row 3 fired and adopted the tree), EXP-028 (R vs RH on dev-48; its §9 picks the tree by §4 recovery rows and the cap by T1-T3), EXP-023 (row 4 pattern: re-run before any addition), plan.md §5.5 (MDE ~4 tasks), plan.md §5.8 (budget gate and its recorded override).

---

## 1. Why this slot, now

- **The slots lapsed.** Five daily slots went unused between Oct 29 and Nov 2 while #11 sat in grading (21.5 h to 5 days, the longest seen; `knowledge/submissions/S-011-result.md`). Today's slot closes 23:59 UTC. An unused slot cannot be recovered and the upload costs 0 GPU-h.
- **The LB is the only instrument for resolves.** dev-48 is not powered for them (EXP-028 §3 D) and the measured MDE for one public draw is ~4 tasks (EXP-005/EXP-009). Separating a 0.07 gap (4 tasks) with a per-draw sd of about 0.05 (binomial at theta ~ 10/58: sd = sqrt(58 x 0.172 x 0.828) = 2.9 tasks = 0.05) needs on the order of 8 draws per arm in an adaptive upload tree. At one slot per day that is the binding resource, so every slot should be a draw of something that will be pooled.
- **A second draw of the baseline lineage is needed either way.** #11 scored 10/58 (EXP-027 §4 row 3: adopt the tree as the baseline, not a time effect). One draw is not a baseline estimate: EXP-027 §3 itself expects theta ~ 10 after removing the rank-3 team's best-of-N selection, with a 2.5-sigma band of roughly 6-14, and their own v17 scored 0.17 and 0.13 on one config. A second draw halves the variance of the pooled estimate (sd of the mean of two draws at theta ~ 10: 2.0 tasks) and is what every later arm, including D-004, is paired against.
- **Whether the pick matters for the reading.** If EXP-028 §9 names R the draw is a pure replication of #11. If it names RH the draw also carries the recovery section, whose evidence is EXP-028's paired dev-48 compliance endpoint, not this slot's score.

## 2. Design

One artifact, uploaded once. **The tree and the cap are not chosen here; they are whatever `experiments/EXP-028-v24-at-8-dev48-paired.md` §9 names, and §8 below records the pick, the zip and its sha256 at upload time.** Selection rules, copied from EXP-028 so that nothing is decided in this file:

| | R (pure second draw) | RH (R + recovery section) |
|---|---|---|
| picked when | EXP-028 §4 recovery rows 4, 5 or 7 name R | EXP-028 §4 recovery rows 2 or 3 name RH |
| row 1 (R has fewer than 4 first-loss events) | names no tree: the tree §9 names on its cost argument; if §9 names none, R | same |
| zip (8 min) | `experiments/EXP-027/v24_at8.zip`, sha256 `c22069db6623a07c9f133fef33a8c193393dca170c84676e708d0bd9f5077600` | `experiments/EXP-028/v24_at8_RH.zip`, sha256 `248dd8eb3afecb3cfc7f21af9853442c2f4244e91247b575cd4ad6f8b97c43da` |
| prompt chars | 3,162 | 4,104 |
| variable vs #11 | **none** | the 942-char recovery section (`experiments/EXP-028/recovery-section.md`) |
| caps | 8 min / 28 calls / 80 turns / 240 s | same |
| sampling, tools | as #11 | same |

**Cap.** 8 minutes unless EXP-028 §9 reports T1 (projected hidden hours > 10.5 on Arm R). If T1 fires, the cap is the one EXP-028 §9 names; if §9 names none, **6.0 min** (EXP-027 §4 row 1's fallback, the team's own v13 figure). A cap other than 8 needs a new zip (`max_time_minutes` and the prompt's budget sentence changed together, the mirror of EXP-023's E1/E2), built by the experimenter from the committed tree, with its sha256 recorded in §8; it then also counts as a change against #11 (the cap, plus the section if RH), and §4 reads it so.

**If EXP-028 §9 names no tree** (e.g. recovery row 1 applied without a stated choice): the tree is **R**, the pure second draw, so that this slot's information value does not depend on a tie-break made after the fact.

**Gate override, as in EXP-027 §2 and plan.md §5.8.** Every candidate above exceeds the packer's 11.0 h formula (`120 x (8 + 1.0) min = 18.00 h`), and the zips were packed with `--skip-budget-gate`. The rule "never submit a config that has not run on dev-48 with projected worst case <= 11 h" is overridden knowingly. Justification, in order of weight: (1) #11, this exact tree at this cap, **completed and scored (10/58) on the hidden set**, and v19 and v24 did before it; (2) EXP-028 ran both arms on dev-48 and its §9 gives the measured projected hidden hours (the override is made against that number, T1-T3, not against the formula); (3) risk accepted is zero for this slot only, since the LB keeps our best. Grading latency for #11 was up to 5 days; the score of this slot may take as long and is read when it returns.

Cost: **0 GPU-h; one upload slot.**

## 3. Endpoints, fixed in advance

Primary: public LB tasks resolved, **k of 58**. Secondary: whether the slot is **blank** (Notebook Timeout / error status; a score that is merely PENDING is not blank). Nothing else is read from this slot.

Prior stated before the score: theta ~ 10/58 (0.17), from #11 (10/58) and the selection-adjusted target in EXP-027 §3. One fresh draw at theta = 10/58 has binomial sd 2.9 tasks, so P(k >= 15) and P(k <= 5) are each about 6 percent under a fixed theta, more if theta itself is uncertain. The §4 thresholds sit about 1.7 binomial sd from 10 on each side.

## 4. Pre-registered readings. Written blind. Not to be revised after the score.

Rows are applied in order; the first match governs. "Tree" means whichever tree and cap §8 records. Throughout: **a one-draw difference from #11 smaller than 4 tasks is not an effect (plan.md §5.5)**, whatever the tree.

| # | outcome | reading |
|---|---|---|
| 1 | **Blank / Notebook Timeout** | The time profile question reopens: either EXP-028's projection was wrong for the hidden set or #11 survived inside variance. Stop adding. Record it with the zip sha. **Next slot: the same tree at 6.0 min**, no other change. Cost: one slot. |
| 2 | **k <= 5 (<= 0.09)** | Five or more below #11. If the tree was R: two draws of one tree, 10 and <= 5, pooled <= 7.5/58, i.e. no better than our retired lineage's best (8/58); #11 is read as the upper tail, the baseline estimate is the pooled one, and EXP-027's additive clause (lineage question closed for the short prompt) does not get stronger. If the tree was RH: the gap is confounded with draw noise and **is not read as harm from the section**. In both cases next slot: **the pure R tree** at the same cap (a third draw for R, or the discriminating draw for RH). |
| 3 | **k = 6 to 14 (0.10-0.24)** | Consistent with theta ~ 10. **Pool with #11 as the baseline estimate** for the v24-at-8 lineage (k1 + k2 over 116); if RH, the pooled figure is labelled "R + RH" and **the difference from #11 is not read as the section's effect** (the section's evidence stays EXP-028's paired dev-48 endpoint). No tree change on this alone; the next slot is the next candidate of the adaptive tree, to be pooled the same way. |
| 4 | **k >= 15 (>= 0.26)** | Above the public 14/58 that was the maximum of at least 12 uploads, so **regression to the mean is the first suspect** (EXP-023 row 4, EXP-027 row 4 pattern). **Re-run the same tree unchanged next slot before any addition.** If the tree was RH, the score is not attributed to the section. Record the draw as the upper tail of LB noise for the paper. |

Not a row, but binding: the score of this slot does not alter EXP-028's §9 pick (that was made on dev-48 evidence before the upload) and is not appended to it.

## 5. What this does and does not license

**Licenses:** a second draw of the baseline lineage and, with #11, a pooled baseline estimate (two draws, sd of the mean ~ 2 tasks at theta ~ 10); a statement that the tree at this cap completes (or not) within 12 h on the hidden set; the choice of the next upload per §4.

**Does not license:** any effect claim from a difference against #11 smaller than 4 tasks; any claim that the recovery section helps or hurts on the LB (if RH: the evidence for that is EXP-028's dev-48 compliance endpoint, and one LB draw cannot add to it); any claim about why the score moved; any resolve-rate claim at dev-48 scale; any use of this score to revise a reading in EXP-027 or EXP-028.

## 6. Exact commands

Run by the **submitter only**, after `approvals/S-012.txt` (written by the user) holds the sha256 of the zip named in §8. Verify before upload:

```
sha256sum out/submission.zip
kaggle competitions submit -c gemma-4-developer-agent -f out/submission.zip -m "S-012 EXP-029 <sha prefix> <tree> <cap>"
```

`out/submission.zip` is a byte copy of the zip §8 names (`experiments/EXP-027/v24_at8.zip` or `experiments/EXP-028/v24_at8_RH.zip`, or the new build if the cap is not 8); the filename must be `submission.zip` or the upload returns a bare 400 (EXP-023 §6; the attempt, not the slot, is spent). The `-m` text carries the sha prefix, the tree name (R or RH) and the cap. After upload: the submitter writes `knowledge/submissions/S-012-result.md`; this file's §9 is appended only when a score returns, applying §4 as written.

## 7. Defects in this pre-registration, logged after the fact

Logged 2026-11-04 from the critic's prereg review (`experiments/EXP-029/critic.md`, verdict `ready`, commit fdd5147). These are defects, not revisions: §4 stands as written and is applied as written when the score returns.

- **(a) Row 2, case R, uses the wrong comparator.** It compares a two-draw pooled mean (<= 7.5/58) with the retired lineage's best-of-9 maximum (8/58). The like-for-like comparator is that lineage's mean, about 6.6/58 (critic P1 (a)).
- **(b) Row 2 calls a pure-R draw "the discriminating draw for RH".** One draw per tree cannot resolve a gap below the ~4-task MDE, so no single draw discriminates R from RH (critic P1 (b)).
- **(c) Row 3 would pool an RH draw into the R baseline** (critic Required fix 1). The "R + RH" label does not cure it: any sub-MDE effect of the section would shift the comparator by half that effect. Rule going forward: pool only byte-identical zips; an RH draw opens its own count at n = 1 and the R baseline stays at the R draws. The Serves line carries the same defect. Moot for this slot, since R shipped (§8).
- **(d) Recommended, not blocking (critic Required fix 2):** §2 did not say which EXP-028 §9 governs if §9 landed after the approval, nor what the next slot does while #12 is pending. In fact EXP-028 §9 was committed at 6cba51b, before the approval commit cc6b679, so the pick was fixed before `approvals/S-012.txt` existed.

## 8. Built and uploaded (filled at upload time, below the line; nothing above changes)

---

Tree picked by EXP-028 §9: **R** (= submission #11, `experiments/EXP-027/candidate-v24-at-8/`), by EXP-028 §4 recovery row 4 (EXP-028 §9.4). EXP-028 §9 was committed at 6cba51b, before the approval commit cc6b679.
Cap picked by EXP-028 §9 (T1-T3): **8 min** / 28 calls / 80 turns / `timeout_seconds` 240 (T2 fired: Arm R projects 10.04 h; T1 did not fire, so no move to 6.0 min). No new zip was built.
Zip path and sha256: `experiments/EXP-027/v24_at8.zip`, uploaded as its byte copy `out/submission.zip`; `sha256sum` of both on 2026-11-04 = `c22069db6623a07c9f133fef33a8c193393dca170c84676e708d0bd9f5077600`, equal to `approvals/S-012.txt` and to submission #11. Variable vs #11: none.
Pre-registration commit of this file: f56b226; critic prereg verdict `ready` for the R upload at fdd5147 (`experiments/EXP-029/critic.md`); approval cc6b679 (`approvals/S-012.txt`, user, 2026-11-04 03:31 UTC).
Kaggle submission ref and upload time (UTC): **57970005**, 2026-11-04 03:51:09 UTC, status PENDING; CLI reported "0 submissions remaining today". The Nov 3 slot lapsed; this went into the Nov 4 slot.

Submit command as run by the submitter (`knowledge/submissions/S-012-result.md`):

```
kaggle competitions submit -c gemma-4-developer-agent -f C:/Users/moemy/Documents/Kaggle/Gemma4_Dev_Agent_Kaggle/out/submission.zip -m "S-012 EXP-029 c22069db second LB draw of the v24-at-8 baseline tree (same zip as #11), pre-reg EXP-029 f56b226"
```

The planned message had a semicolon before "pre-reg"; the Bash guard rejected that attempt as chaining before anything ran (no upload), so the semicolon became a comma. Submitted exactly once.

Defects the critic named are logged in §7 (a)-(d); none revises §4.

## Status

Uploaded 2026-11-04 03:51 UTC, ref 57970005, PENDING (grading has taken 6 h to 5 days). No kernel. Next action: when the lead reports a score or a blank, append §9 applying §4 as written, and fill LB in `submissions.md` row 12.
