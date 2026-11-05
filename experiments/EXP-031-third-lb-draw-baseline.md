# EXP-031 — A third LB draw of the v24-at-8 baseline zip (option for the 2026-11-05 slot)

**Date:** 2026-11-05
**Type:** LB-only upload (#13 if used), zero GPU. One draw of 58; no kernel, no dev-48 arm attached.
**Cohort:** n/a (public LB, 58 tasks)
**Ladder:** L3 (LB upload). L0 desk check done: EXP-029 §9 (row 3 fired, pooled baseline 21/116), EXP-028 §9 (Arm R projects 10.04 h on dev-48). No lower rung can read what one LB draw reads: the hidden-set score of a known zip, and whether it completes inside 12 h a third time.
**Pre-registered:** this file is committed **before** any upload. Sections 3-5 are written blind and are not revised after the score. A badly drafted reading gets its defect logged in §7, not rewritten. **This is an option, not a decision:** the user has not decided whether to spend a slot on it. If no upload happens, the file stays at status "pre-registered, not uploaded" and nothing below is read.
**Serves:** the pooled baseline estimate for the v24-at-8 zip that every later 31B tree is read against (D-004's team trees included); C-003 (the v24 tree at 8 min / 28 calls completes ~120 hidden tasks inside 12 h); the paper track's LB-noise measurement (three draws of one zip).
**Supersedes / relates:** EXP-027 (#11, first draw, 10/58), EXP-029 (#12, second draw, 11/58; §7 (c) pooling rule; §9 row 3), EXP-028 (Arm R time profile), plan.md §5.5 (MDE ~4 tasks), plan.md §5.8 (budget gate and its recorded override).

---

## 1. Why this, now

- **Two draws are a thin baseline.** #11 and #12 scored 10 and 11 of 58 on byte-identical zips (sha256 `c22069db...`); pooled 21/116 = 0.181, Wilson 95% CI 0.122-0.261 (EXP-029 §9). The CI is 14 points wide. Every later 31B tree, D-004's above all, will be read against this number, and at one slot per day the comparator should be as tight as the slots allow.
- **What a third draw buys.** At theta = 21/116 the binomial sd of one draw is 2.9 tasks; the sd of a three-draw mean is 1.7 tasks against 2.1 for two. At n = 174 and a pooled rate near 0.18 the Wilson 95% CI narrows to roughly +/- 0.055, against +/- 0.07 at n = 116. (Computed with a one-line Wilson / binomial formula in Python on 2026-11-05; no repo tool covers pooled LB draws.)
- **The tension with EXP-029 row 3, stated plainly.** EXP-029 §4 row 3 says the next slot goes to "the next candidate of the adaptive tree". As of 2026-11-05 there is no candidate that has passed its screen: D-004 is approved by the user for screens only (commit e2e7246, ceiling 3.2 GPU-h, no dev-48 arm); EXP-030 (31B parallel smoke-8) is being built by the screener today and has not run; `max_tool_calls` 40 (EXP-028 T4) has no L2 screen yet. An unused slot cannot be recovered and costs 0 GPU-h. So this draw is the filler that EXP-029 row 3's own rule ("pooled the same way") makes useful: it changes nothing in the tree and tightens the comparator the next candidate needs. If a screened candidate exists on the day a slot is used, that candidate takes precedence over this file.
- **The time question is not why this is run.** Two completions at the 8-min cap so far (#11 ref 57750294, #12 ref 57970005) and the EXP-028 Arm R dev-48 projection of **10.04 h** (analyzer 9.92 + server start 0.11 + residual 0.01; EXP-028 §9, T2) already carry C-003. A third completion adds one more observation to it, not a test.

## 2. Design

One artifact, uploaded at most once under this file.

| | value |
|---|---|
| zip | `experiments/EXP-027/v24_at8.zip`, **not repacked** |
| sha256 | `c22069db6623a07c9f133fef33a8c193393dca170c84676e708d0bd9f5077600` (verified with `sha256sum` on 2026-11-05 at pre-registration; equal to #11 and #12) |
| tree | `experiments/EXP-027/candidate-v24-at-8/` (R), 4 members |
| caps | 8 min / 28 calls / 80 turns / `timeout_seconds` 240 |
| prompt chars | 3,162 |
| variable vs #11 and #12 | **none** |

**Gate override, as in EXP-027 §2 and EXP-029 §2 (plan.md §5.8).** The zip exceeds the packer's formula (`120 x (8 + 1.0) min = 18.00 h`) and was packed at EXP-027 with `--skip-budget-gate`. The rule "never submit a config that has not run on dev-48 with projected worst case <= 11 h" is overridden knowingly. Justification, in order of weight: (1) this exact zip **completed and scored twice** on the hidden set at this cap (#11 10/58, #12 11/58); (2) EXP-028 Arm R measured the tree on dev-48 and projects **10.04 h**, inside the ~10.5 h calibrated ceiling (C-008), with no margin to spare; (3) a timeout zeroes this slot only, since the LB keeps the team's best (0.18).

**Cost: 0 GPU-h; one upload slot.** The 2026-11-05 slot closes 23:59 UTC. If the upload lands on a later day instead, these readings still govern provided the zip is the same sha and no other draw of it has been scored in between; otherwise a new file is needed.

**Upload path.** The lead writes S-013 if the user says yes; the user writes `approvals/S-013.txt` with the sha above; the submitter uploads. Nothing under `knowledge/` or `approvals/` is written by this experiment.

## 3. Endpoints, fixed in advance

Primary: public LB tasks resolved, **k of 58** (the board truncates to 2 dp; k is recovered as the integer whose k/58 truncates to the shown score). Secondary: whether the slot is **blank** (Notebook Timeout / error status; a score that is merely PENDING is not blank). Derived, not a test: the **pooled baseline** under the §4 pooling rule, with its Wilson 95% CI.

Prior stated before the score: theta = 21/116 = 0.181, about 10.5 tasks per draw, binomial sd 2.9 tasks. Under that fixed theta P(k <= 5) is about 4% and P(k >= 15) about 9% (binomial tails computed 2026-11-05), more if theta itself is uncertain. Pooled outcomes by band: k = 5 gives 26/174 = 0.149; k = 6 gives 27/174 = 0.155; k = 14 gives 35/174 = 0.201; k = 15 gives 36/174 = 0.207.

MDE, unchanged: a single-draw difference under ~4 tasks is not an effect (plan.md §5.5). This draw is not a comparison of anything with anything; it has no effect endpoint.

**Pooling rule, binding for this and every later draw of this zip.** (a) Pool only byte-identical zips (sha `c22069db...`); a zip that differs by any byte opens its own count at n = 1 (EXP-029 §7 (c)). (b) Every scored draw of the zip pools, whatever its value: no trimming of a low or high draw, since dropping a tail biases the comparator. (c) A blank is not k = 0: it is excluded from k and n and recorded as a failed completion. (d) The baseline is reported as k_total / (58 x draws) with a Wilson 95% CI; a later tree is read against that pooled rate, never against any single draw.

## 4. Pre-registered readings. Written blind. Not to be revised after the score.

Rows are applied in order; the first match governs. Throughout: **a one-draw difference from #11 or #12 smaller than 4 tasks is not an effect (plan.md §5.5)**, and no row attributes a score to anything, since nothing changed.

| # | outcome | reading |
|---|---|---|
| 1 | **Blank / Notebook Timeout** | The first failure of this zip after two completions. Not pooled (rule (c)); the baseline stays 21/116. C-003's record becomes 2 completions of 3, and the EXP-028 projection (10.04 h, no margin) is read as too optimistic for the hidden set. **Next slot: the same tree at 6.0 min** (EXP-027 §4 row 1 fallback; needs a new zip with `max_time_minutes` and the prompt's budget sentence changed together, built by the experimenter, its own count at n = 1). Any later 31B upload above 4.5 min waits until a 6.0 min draw completes. Cost: one slot. |
| 2 | **k <= 5 (<= 0.09)** | Pool under rule (b): **<= 26/174 (<= 0.149)**. The low draw is not rejected and not explained: it sits below the retired 12.8 KB lineage's mean of about 6.6/58, and with 10 and 11 beside it the pooled rate is still the baseline. The comparator for D-004 trees becomes the pooled figure with its wider-than-hoped CI. **Next slot: the next candidate that has passed its screen; if none has, a fourth draw of this zip**, pooled the same way. |
| 3 | **k = 6 to 14 (0.10-0.24)** | Consistent with theta ~ 10.5. Pool: **27/174 to 35/174 (0.155-0.201)** is the baseline estimate for the v24-at-8 zip. No tree change. **Next slot: the next candidate that has passed its screen** (a D-004 survivor of its smoke-8, or `max_tool_calls` 40 after its L2 screen), read against the three-draw pooled rate; if none has passed, another draw of this zip is permitted as filler under the same rule, not required. |
| 4 | **k >= 15 (>= 0.26)** | Above the public 14/58 that was the maximum of at least 12 uploads, so **regression to the mean is the first suspect**; nothing changed, so nothing is credited. Pool under rule (b): **>= 36/174 (>= 0.207)**. This is already a replicate of a known zip, so EXP-029 row 4's "re-run before any addition" is satisfied by the pooling itself: **next slot as row 3**, with later trees read against the higher pooled rate. Record the draw as the upper tail of LB noise for the paper. |

Not a row, but binding: this score does not alter EXP-027, EXP-028 or EXP-029 and is not appended to them; and no small-variant (E2B / E4B) tree is read against this baseline, since it is a different model.

## 5. What this does and does not license

**Licenses:** a third draw of one zip; with #11 and #12, a three-draw pooled baseline (n = 174) and its CI; one more completion (or not) of this tree at 8 min on the hidden set, recorded against C-003; the choice of the next slot per §4.

**Does not license:** any effect claim from any difference among the three draws; any claim about why a draw is higher or lower; any resolve-rate claim at dev-48 scale; any use of this score to revise a reading in EXP-027, EXP-028 or EXP-029; any claim about the time profile beyond complete / not complete.

## 6. Exact commands

Run by the **submitter only**, after the lead writes S-013 and the user writes `approvals/S-013.txt` holding the sha256 above. Verify before upload:

```
sha256sum experiments/EXP-027/v24_at8.zip
cp experiments/EXP-027/v24_at8.zip out/submission.zip
sha256sum out/submission.zip
kaggle competitions submit -c gemma-4-developer-agent -f out/submission.zip -m "S-013 EXP-031 c22069db third LB draw of the v24-at-8 baseline zip (same zip as #11 and #12), pre-reg EXP-031 <commit>"
```

The filename must be `submission.zip` (EXP-023 §6). The `-m` text must not contain a semicolon (the Bash guard reads it as chaining; S-012-result.md). After upload the submitter writes `knowledge/submissions/S-013-result.md`; the experimenter fills `submissions.md` row 13 and appends §9 here only when a score or a blank returns, applying §4 as written.

## 7. Defects in this pre-registration, logged after the fact

None yet.

## 8. Built and uploaded (filled at upload time, below the line; nothing above changes)

---

No build: the zip is the EXP-027 artifact, not repacked. `sha256sum experiments/EXP-027/v24_at8.zip` on 2026-11-05 = `c22069db6623a07c9f133fef33a8c193393dca170c84676e708d0bd9f5077600`. The zip is a gitignored archive; its provenance is EXP-027 §8 and the `submissions.md` rows 11 and 12 that carry the same sha.

## Status

Pre-registered 2026-11-05, **not uploaded**. Waiting on: the user's decision whether to use a slot for this; if yes, the critic's `prereg` review (required for any upload), then S-013 (lead) and `approvals/S-013.txt` (user). Next command, submitter only, after approval: the §6 block.
