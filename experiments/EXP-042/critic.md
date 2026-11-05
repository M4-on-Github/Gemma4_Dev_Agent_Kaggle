---
id: EXP-042-critic
exp: EXP-042
tier: light
verdict: accepted
verified: regenerated
date: 2026-11-05
---

## Verdict
**accepted.** Both measures were read as written:
- as-written (the primary): row 2, no reading, not robust;
- sharpened: row 1, robust;
- Arm R: R-B.

Every count regenerates except one hand call, rich_3105, which changes no row. The result licenses "no trace support", not a negative. Three lead lines overstate, and replacements are given below. Nothing here gates the verdict.

## Audit
1. **Order and blindness: pass.**
   - 510e2a2 was committed at 21:44:59 UTC. Between the dispatch (21:41:13) and the commit the screener ran only `ls` and `git log`. Its first grep of a win trace was at 21:45:03.
   - During EXP-041 it opened only the 4 targets and the 19 control ids, so §2's disclosure is accurate.
   - cf3035f changed only "Pending." and the Status line above the results.

   **Contamination.** It can have shaped the design but not the counts.
   - The sharpened rule was written knowing that a bare fastapi pytest dies at collection here, and 2 of the 4 non-free wins are fastapi. Sharpened W <= 1 was therefore foreseeable. The blind prediction of 3 suggests it was not foreseen [I].
   - The informative-27 threshold L' <= 5 sits on the already-known 5 of 23, so that variant read row 3 by construction. The weakest-row rule gives row 2 either way.
2. **Cohort: pass.** Both arms have the 48 dev-48 ids.
3. **Numbers: pass, with one correction.** I used my own per-run parser: it counts runs before the last `submit_patch` and takes failure classes from each run's own output.
   - **E4B, as-written:** the same 17 ids, and every §9.3 table matches.
   - **E4B, sharpened:** W = 1 (rich_3006), as reported. rich_3105's second counted run returns status ok, exit 0 and no error class, so under the rule as written it is informative. L is therefore 4 of 43, not 3, and 2 of 23 on the informative 27, not 1. W does not change.
   - **The other three hand calls agree.** R's fastapi_14360 dies on an ImportError. requests_7205 and requests_7427 exit 1 with no failure class.
   - **R:** 37 of 48, with the same 11 non-checkers. Sharpened gives 9 of 9 against 27 of 39, and the per-run classes include the "No such file" string that the §6 grep omits; none occurs.
   - **R-B is at the margin:** 28 points against a 25-point bar. One of the 9 wins without a counted run, or two more losses with one, sends it to R-C. Each win has an exit-0 counted run, so it holds.
   - **§9.7 (i) to (iii):** the same sets and breakdowns. R's submitters give 23 of 33.
4. **The two disclosed wording errors (item 4) change no row.** requests_6644 is free under any patch. The "3 wins" variant never entered the robustness rule. R's 6 no-submit ids give 23 of 39 if counted strictly and 23 of 33 if excluded; R-B fires either way.
8. **Hygiene: pass.** The check is OK. §9.2 names two command lines with repo paths (rich_3935, rich_3105). Paths are allowed, and nothing else from the traces appears.

**Item 3.**
- Row 1 fires because only 5 of 48 E4B tasks ran an informative check. The table cannot show whether requiring one would turn losses into wins; it shows only that the wins did not need one (fastapi_14301 and fastapi_14463 resolved after a pytest that died at collection).
- The collection failure is a fastapi fact: 11 of the 12 fastapi pytest tasks died there, while all 4 non-fastapi runs executed.
- The repro candidate has no E4B evidence: the E4B ran no reproduction on any of its 48 tasks. Its only support is R-B, which is confounded [I]. 8 of R's 11 non-checkers hit a cap, against 15 of its 37 checkers; the other 3 are gated or impossible; and on the informative 27 all 6 non-checkers capped.
- Keeping both candidates unlicensed is fair. "Dropped", "a negative" and "governing" are not.

**Item 6 [I].** A union of single draws (R and RH as run, plus the E4B's own smoke-8 run, EXP-033) is a proxy for "within reach":
- (iii), the 9 empty-patch submits, which contain all 8 ids of (ii): R 0, RH 0, none in smoke-8, 3 gated.
- E4B losses with a failed edit that another arm resolved: fastapi_9753 (R) and rich_3180 (RH).
- E4B losses with no informative check that R or RH resolved: 6, or 5 without the format failure.

**Corrections (copy as written)**

```
EXP-042 section 9.10, new dated item (screener):
"*Corrected 2026-11-05 (critic light):* rich_3105's second counted run exited 0 with no error; by the rule as
written it is informative, so the sharpened loss count is 4 of 43 (2 of 23 on the informative 27). W and every
reading are unchanged."

knowledge/plan.md, EXP-042 entry (lead). Replace "A negative for the check-before-submit lever on the E4B." and
the sentence beginning "Governing reading" with:
"No trace support for the check-before-submit lever on the E4B, and not a test of it. Primary (as-written)
measure: 3 of 5 wins and 14 of 43 losses ran a check, row 2, no reading, not robust. Sharpened measure: 1 of 5
wins and 4 of 43 losses (critic count; EXP-042 says 3), row 1 in all three variants. Only 5 of 48 E4B tasks ran
an informative check, so the table cannot show whether requiring one would help."
Replace the sentence beginning "So a "run the tests before submit" rule" with:
"11 of the 12 fastapi tasks on which the E4B ran pytest died at collection on the two missing test-only
packages, and two of them resolved anyway; its 4 non-fastapi pytest runs executed tests. A bare test-run rule
would carry no information on dev-48's fastapi tasks in this sandbox; whether hidden-repo suites collect is
unknown."

knowledge/plan.md, failed-edit entry (lead). Replace "lever (1) as "run the tests" is dropped for the E4B" with
"lever (1) as "run the tests" is deprioritised for the E4B (no trace support; uninformative on dev-48's fastapi
tasks), not rejected", and append: "The reproduction candidate has no E4B evidence (no reproduction run on any
of the 48 tasks); its support is Arm R's R-B, observational, another model, and confounded with budget: 8 of
R's 11 non-checkers hit a cap and the other 3 are gated or impossible."

C-018, replacing the EXP-042 history line (lead):
"- history: 2026-11-05 note, status unchanged (EXP-042, cf3035f, zero GPU, observational; critic light):
EXP-042 counts a check before submit, not before the first edit, so it does not test this claim's timing. In
Arm R 9 of 9 resolved and 28 of 39 unresolved tasks ran one, mostly a python reproduction (script or inline);
8 of R's 11 non-checkers hit a cap and the other 3 are gated or impossible, so within R the association is
confounded with running out of budget. The E4B ran no reproduction on any of its 48 tasks, and an informative
check on 1 of 5 resolved and 4 of 43 unresolved, too few to show or exclude a correlation."

C-019, replacing the EXP-042 history line (lead):
"- history: 2026-11-05 note, status unchanged (EXP-042, cf3035f; critic light): on the E4B single loop the
trace record neither shows nor excludes that an executed check separates resolved from unresolved tasks
(informative check on 1 of 5 wins, 4 of 43 losses). 11 of the 12 fastapi tasks where the E4B ran pytest died
at collection on the two missing test-only packages, so a required test run carries no information on dev-48's
fastapi tasks in this sandbox; its 4 non-fastapi pytest runs executed. The claim's wrong-fix pool was measured
on the 31B (EXP-034) and is not shown for the E4B."
```

The C-020 EXP-041 note stands.
