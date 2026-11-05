---
id: EXP-040-critic
exp: EXP-040
tier: light
verdict: accepted
verified: regenerated
date: 2026-11-05
---

## Verdict
**accepted.** Row 2 governs, and V1 as specified is stopped. Sixteen voters given the same prompt, differing only in temperature, never changed voter 1's pick: D = 0 of 8, with D possible on 6.

Row 1 holds at 6 of 8, but only on pass 1, which is what the committed instrument scores. On the other reading of E1, row 1 would govern.

The lead's ranking takes over row 1's reading ("the candidate source is the binding gap"). The governing row does not license that, and the screen's leads point against it.

## Audit
1. **Order: pass.** §3 and §4 are unchanged since 3f33acd (18:21 UTC), and §4.1 since 75195e5 (18:45 UTC). Both are before the push at 22:03. Every later hunk is in the header, §7 items 8-11 (appended), §8, Status or §9. tally.py is unchanged since 75195e5.
2. **Cohort: pass.**
   - The 8 ids equal smoke-8, and `err` is empty on 8 of 8.
   - The embedded zip is `e476acb6…29d8`, run at 240 / 28 / 8 / 200.
3. **Numbers: pass.**
   - **Row 1 boundary.** I ran `tally.candidate_letters` on each task's pass-1 proposer final step:
     - C = 4 on 6 tasks, and C = 1 on fastapi_14448 and rich_3468.
     - A looser letter pattern agrees, and neither C = 1 text has a numbered list. So **6 of 8 holds**.
     - E1 says "the proposer's final text". httpx_3672's restart-pass proposer gave C = 0, so counting that pass gives 5 of 8, which is row 1.
     - I take pass 1 as the reading as written: tally.main, committed before the push, scores pass 1, and E2 and E12 say pass 1. §9.4 should still record the alternative. Both rows stop V1; they differ only on what follows.
   - **D.** W = P1 on all 8, both by the instrument and by my own contiguous-run segmentation.
   - **The item 8 defect is real and confined to httpx_3672.**
     - voter_01 is emitted first in all 8 pass-1 runs.
     - In httpx_3672's pass 2, 8 voters precede it, the same ids as §7.
     - As written that gives 8 parseable and a lead of 6. Corrected, it gives 16 and 10.
     - W = P1 = B either way, and row 0 has at least 6 of 8 either way.
     - Keeping the committed instrument as the endpoint, with the corrected figure from a new script beside it, is the right handling.
   - **Regenerated.**
     - `analyze_traces.py --out` reproduces `v1/summary.jsonl` and `v1/aggregates.json` exactly.
     - Log span 1,135.6 s, task sum 692.4 s, mean 86.55 s.
     - Paired view: EXP-033 at 56.9 s (V1 slower on 8 of 8) and the EXP-038 subset at 78.3 s (slower on 6 of 8). The resolve 2x2 is as stated.
8. **Hygiene: pass.** Each of these only names and counts, or carries harness, notebook or our own prompt labels:
   - the added EXP text;
   - `results.json` (2 strings over 24 characters: the model name and a note);
   - `v1/*`;
   - the README row;
   - f6d990e.

**Scope (items 4 and 5).**
- §9.6 and §9.7 stay within bounds.
- §9.8 bullet 2 does not. It offers paraphrase sets as a reason for D = 0, yet the 3 sets the experimenter judged distinct were the more unanimous ones: leads 16, 10 (corrected) and 16, against 14, 10 and 4.
- One fact goes unreported: the proposer's prompt-only limit of 4 reads was exceeded on requests_7205 (7), requests_7309 (7) and rich_3468 (13).
- The lead's result and licence entries are accurate. The ranking overstates: where the voters had a real choice, on the experimenter's own judgement, they still agreed with voter 1.

## Required fixes (non-gating)

```
Experimenter, EXP-040 9.4, under row 1: "Row 1 is read on pass 1, as tally.main scores it. Counting
httpx_3672's restart pass, whose proposer gave no candidates, C >= 2 is 5 of 8 and row 1 would govern
(critic light 2026-11-05). Both rows stop V1 as specified."
Experimenter, 9.8 bullet 2: drop "mostly"; replace the sentence beginning "It is one plausible reason"
with "The vote also equalled voter 1's pick on the other 3 four-candidate tasks, which were more
unanimous (leads 16, 10 corrected, 16, against 14, 10, 4), so this does not explain D = 0."
Experimenter, 9.8, new bullet: "The proposer's 4-read limit (prompt only) held on 5 of 8; requests_7205
and requests_7309 read 7 times, rich_3468 13."

Lead, plan "Lead's ranking after EXP-040": replace the sentence beginning "On this evidence" with "The
screen cannot rank the candidate source against the voters: on the 3 four-candidate tasks the
experimenter judged distinct, the vote still equalled voter 1's pick (leads 16, 10, 16); on the other
5 the proposer gave one candidate (2) or one fix in four wordings (3, unblinded judgement)." In the next
sentence, "diverse proposers before diverse voters" -> "diverse proposers and diverse voters".
Lead, plan "EXP-040 result": after "Row 1 does not fire, at the boundary" add "(pass 1; 5 of 8 if
httpx_3672's restart pass counts)"; "no critic review yet" -> "critic light accepted".
Lead, C-023 history: "(no critic review yet)" -> "(critic light accepted)"; after "(experimenter's
judgement)" add "; on the other 3 the vote also equalled voter 1's pick".
```
