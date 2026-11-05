---
id: EXP-040-critic
exp: EXP-040
tier: light
verdict: accepted
verified: regenerated
date: 2026-11-05
---

## Verdict
**accepted.** Row 2 governs, and V1 as specified is stopped. The 16 voters share one prompt and differ only in temperature, and they never changed voter 1's pick: D = 0 of 8, with D possible on 6.

Row 1 holds at 6 of 8 only on pass 1, which is what the committed instrument scores. On the other reading of E1, row 1 would govern.

The lead's ranking takes over row 1's reading ("the candidate source is the binding gap"). The governing row does not license that, and the screen's own leads point against it.

## Audit
1. **Order: pass.** Both sets of readings were committed before the push at 22:03:
   - §3 and §4 are unchanged since 3f33acd (18:21 UTC);
   - §4.1 is unchanged since 75195e5 (18:45 UTC).

   Every later hunk is in the header, §7 items 8-11 (appended), §8, Status or §9. tally.py is unchanged since 75195e5.
2. **Cohort: pass.** The 8 ids equal smoke-8, and `err` is empty on 8 of 8. The embedded zip is `e476acb6…29d8`, run at 240 / 28 / 8 / 200.
3. **Numbers: pass.**
   - **Row 1 boundary.** I ran `tally.candidate_letters` on each task's pass-1 proposer final step.
     - It gives C = 4 on 6 tasks and C = 1 on fastapi_14448 and rich_3468.
     - A looser letter pattern agrees, and neither C = 1 text has a numbered list, so **6 of 8 holds**.
     - Caveat: E1 says "the proposer's final text". httpx_3672's restart-pass proposer gave C = 0, so counting that pass makes it 5 of 8, which is row 1.
     - I read pass 1 as the as-written application. tally.main was committed before the push and scores the first pass, and E12 (§4.1) names the first pass.
     - §9.4 should record the alternative. Both rows stop V1; they differ only on what follows.
   - **D.** W = P1 on all 8, by the instrument and by my own contiguous-run segmentation.
   - **The item 8 defect is real and confined to httpx_3672.**
     - voter_01 is emitted first in all 8 pass-1 runs. In httpx_3672's pass 2, 8 voters precede it, the same ids as §7.
     - As written: 8 parseable, lead 6. Corrected: 16 and 10. W = P1 = B either way, and row 0 has at least 6 of 8 either way.
     - Keeping the committed instrument as the endpoint, with a new script's corrected figure beside it, is the right handling.
   - **Regenerated:**
     - `analyze_traces.py --out` reproduces `v1/summary.jsonl` and `v1/aggregates.json` exactly;
     - log span 1,135.6 s, task sum 692.4 s, mean 86.55 s;
     - EXP-033 at 56.9 s (V1 slower on 8 of 8);
     - the EXP-038 subset at 78.3 s (slower on 6 of 8);
     - the resolve 2x2 as stated.
8. **Hygiene: pass.** Each of these names and counts only, or carries harness, notebook or our own prompt labels:
   - the added EXP text;
   - `results.json` (2 strings over 24 characters: the model name and a note);
   - `v1/*`;
   - the README row;
   - f6d990e.

**Scope (items 4 and 5).**
- §9.6 and §9.7 stay within bounds.
- §9.8 bullet 2 does not. It offers the 3 paraphrase sets as a reason for D = 0. The other 3 four-candidate tasks were more unanimous: leads 16, 10 (corrected) and 16, against 14, 10 and 4.
- One fact is missing: the proposer's prompt-only 4-read limit was exceeded on requests_7205 (7 reads), requests_7309 (7) and rich_3468 (13).
- The lead's result and licence entries are accurate.
- The ranking overstates. On the tasks the experimenter did not call paraphrase sets, the voters still agreed with voter 1.
- A and the paraphrase judgement are unblinded hand calls. I did not re-judge them.

## Required fixes (non-gating)

```
Experimenter, EXP-040 9.4, under row 1: "Row 1 is read on pass 1, as tally.main scores it. Counting
httpx_3672's restart pass, whose proposer gave no candidates, C >= 2 is 5 of 8 and row 1 would govern
(critic light 2026-11-05). Both rows stop V1 as specified."
Experimenter, 9.8 bullet 2: "mostly one fix written several ways" -> "one fix written several ways on 3
of the 6 four-candidate tasks"; replace the sentence beginning "It is one plausible reason" with "The
vote also equalled voter 1's pick on the other 3 four-candidate tasks, which were more unanimous (leads
16, 10 corrected, 16, against 14, 10, 4), so this does not explain D = 0."
Experimenter, 9.8, new bullet: "The proposer's 4-read limit (prompt only) held on 5 of 8; requests_7205
and requests_7309 read 7 times, rich_3468 13."

Lead, plan "Lead's ranking after EXP-040": replace the sentence beginning "On this evidence" with "The
screen cannot rank the candidate source against the voters: on the 3 four-candidate tasks not named as
paraphrase sets, the vote still equalled voter 1's pick (leads 16, 10 corrected, 16); on the other 5
the proposer gave one candidate (2) or one fix in four wordings (3, unblinded judgement)." In the next
sentence, "diverse proposers before diverse voters" -> "diverse proposers and diverse voters".
Lead, plan "EXP-040 result": after "Row 1 does not fire, at the boundary" add "(pass 1; 5 of 8 if
httpx_3672's restart pass counts)"; "no critic review yet" -> "critic light accepted".
Lead, C-023 history: "(no critic review yet)" -> "(critic light accepted)"; after "(experimenter's
judgement)" add "; on the other 3 the vote also equalled voter 1's pick".
```
