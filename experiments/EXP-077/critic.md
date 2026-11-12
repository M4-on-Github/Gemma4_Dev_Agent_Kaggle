---
id: EXP-077-critic
exp: EXP-077
tier: light
verdict: accepted
verified: regenerated
date: 2026-11-12
---

## Verdict
Accepted. Row 3 was the first matching row and was applied as written. s = 0.0991, from M 61/139 = 0.439 against EXP-038's 53/156 = 0.340. EXP-075's M-falls bound is therefore 0.142, and later one-draw M arms are read at a fall of 2s. That decision stands.

The row's label claims more than one difference shows. s has one df and sits at 1.35 bootstrap SDs of a difference (0.073). A correct bootstrap produces a gap that large about one time in five (two-sided p about 0.18) [I].

Ledger wording, offered as a note, since a light verdict moves no claim: "A second base draw gives an M spread s = 0.099 on one df. The 0.07 bootstrap is neither confirmed nor refuted. One-draw M arms are read at 2s." Do not write "the bootstrap understates the spread". Resolves 3/48 and the holds are a draw, which is how §4 frames them.

## Audit
1. **Pre-registration order: a finding, immaterial.**
   - The readings (1f394df) precede the 05:50 UTC push.
   - 414fd31, at 05:54 UTC, changed text above the line before any result: the header attribution, the boundary of EXP-075's net H1 (3 lost to 2), and a command.
   - None of these changes touches s or rows 1 to 4.
   - Process finding: an arm of about 1.3 GPU-h was pushed with no critic prereg, as its header states. D-011's status line had promised the direction review before any such round.
2. **Cohort and arms: pass.**
   - The 48 ids equal dev-48.
   - The loaded tree equals `experiments/EXP-033/candidate-e4b` under diff -r, and sampling reads 1.0.
   - The repack sha `9de869bd...1ac0` is §9.2's figure; I checked diff -r only.
3. **Numbers: pass, regenerated.**
   - `analyze_traces.py` at 8 min and 28 calls: 0 field differences from the committed `summary.jsonl`.
   - `readings.py` gives s 0.0991, with rich_3006 and rich_3905 lost.
   - `noise.py` and `pair.py` agree: E left 7, F left 6, F entered 2, same class 27/48.
   - Holds: 2 against 0, exact McNemar p 0.50. This is reported, not an endpoint.
8. **Scope: pass, with the label note above.**
   - §9.6 labels the union and the one-draw-only ids post hoc and unread, as §5 requires.
   - §9.7 stays inside §5.

`accepted` despite the check-1 finding: the change was disclosed, came before any result, and cannot alter the row that fired.
