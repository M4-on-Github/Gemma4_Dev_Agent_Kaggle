---
id: EXP-036-critic
exp: EXP-036
tier: light
verdict: needs-work
verified: regenerated
date: 2026-11-05
---

## Verdict
Row 1 on R (G = 3), its replicate on RH (G = 5), and T3 in both arms were applied as written. None of the fixes below changes them. Status moves on a re-review of three textual items, because §9.3 states the RFWF (right-file-wrong-fix) numbers that C-021 and C-022 would carry against the wrong denominator.

Claim to copy once fixed: *with the two test-only packages present at grading, R's patches resolve 3 of the 15 gated fastapi tasks and RH's 5, decided by plain assertions or a strict-equality stand-in. On the RFWF tasks the grader can judge, an existing test in the graded files fails under the patch on 2 of 22 (R) and 1 of 17 (RH); the rest fail only on tests the test patch adds or changes (T3).*

Transfer caveat: all 15 gated tasks are fastapi, 15 of dev-48's 26 fastapi tasks. The hidden set is private repos, so row 1's screen tests a gap §5 cannot show exists there.

## Audit (light: 1, 2, 3, 8)
1. **Order: pass.** d86d09c (14:38:45 UTC) is earlier than the push (15:13:59 UTC).
   - Above `---`, d86d09c..c680b31 changes only §7 item 1. Everything else is §8, Status and §9.
   - `analyze_regrade.py` first appears in c680b31.
   - Q5: §2 to §4 are unrevised.
2. **Cohort and environment: pass.**
   - Each pass has 48 rows, with ids equal to dev-48.
   - The gated set, recomputed from the six as-run tails, is 15.
   - Shims were dropped on 26 tasks per pass, all 15 gated tasks among them. No gated tail still shows the module.
   - No accelerator.
3. **Regenerated.** `analyze_regrade.py`, re-run into scratch, reproduces `aggregates.json`, `summary.jsonl` and `rows.jsonl` byte for byte. Recounted independently from the four `regrade.jsonl`:
   - resolves 12, 15, 43 and 1;
   - G = 3 and 5, every flip on a task GOLD resolves and BASE fails;
   - 0 non-gated flips, 0 True-to-False flips;
   - union 16, best 15;
   - the Wilson intervals match.
8. **Scope: fail, one sentence (Q4).** Hygiene passes: `check_repo_hygiene.py --all` exits 0.

## The five questions
**Q1. The stand-ins are not lenient enough to have produced these flips.**

Both shims are plain `==` against the recorded value; for dirty_equals that means dict, subset, any-of and repr equality. Missing API raises an error, so they fail closed. BASE 0 of 15 rules out vacuous passes, and GOLD 15 of 15 rules out over-strictness, but neither covers the one assertion that separates a wrong fix. I therefore hand-checked the five flips (static, from the test-patch files):
- **R's 3 flips:** the 10 test functions that fail at base contain no `snapshot(` and one `IsPartialDict`. The graded files of 13207 and 14297 import neither package, so the shim only unblocks collection.
- **RH's 14459:** decided by a snapshot comparison. BASE and R fail the same 2 test ids (list equality checked), and RH and GOLD pass them.
- **RH's 14605:** decided at collection. BASE has 11 errors, R has 12, and RH and GOLD pass 99.

No further check is needed.

**Q2. The row-1 reading is safe as applied.**
- Row 0 fires on no clause.
- G = 3 meets row 1's "≥ 3".
- The three flips exit 0 with every test passing, in under 1 s each.
- There are no True-to-False flips, so the defect clause is moot.

RH is "replicated" exactly as §4 defines it. It is not an independent check of the grader: same shims, same ids, and RH is R plus 942 characters. The robust part is the 3 tasks that flip in both draws.

**Q3. "Ceiling 43 of 48" is right for this grader:** GOLD resolves all 42 patch-sensitive tasks, plus 1 free.

The evidence is verified. On all six tasks, GOLD and BASE have equal exit codes, count lines and failing ids. R's re-grade gives the same ids, and all six EXP-034 arms are constant as run. That constancy is observed across eight gradings, not structural.

McNemar is unaffected, since these tasks are concordant in every arm. What changes:
- absolute rates, and any power or rate stated on n = 48;
- EXP-034's always/none counts, from 6/31 to 5/26;
- the RFWF denominators (Q4).

Two consequences of my own [I]:
- On the as-run grader, a tree that does not vendor has about 27 informative tasks (48 minus 6 minus 15).
- smoke-8 holds `httpx_3672`, `requests_7205` and `requests_7309`, all impossible, plus 1 gated task. A non-vendoring tree can therefore resolve at most 4 of 8 as run.

**Q4. Not fair as written.**
- **Five of the six sit in both arms' RFWF groups:** `httpx_3672` as C, and the four always-fail requests tasks as H. GOLD fails the same tests on all five, so none is a judged wrong fix. Without them:
  - R is n′ 22 (V 2, H 15, C 5);
  - RH is n′ 17 (V 1, H 10, C 4, U 2);
  - both still read T3.
- **What was measured is narrower.** The grader runs only the test-patch files, not "the existing test file of the edited module", so V is a lower bound.
- **Base status (40 of 48) does not bind.** No failing (b) test has unknown status.
- **Two C tasks are the patch's own collection errors:**
  - R `fastapi_14605`: SyntaxError, where BASE gives ImportError;
  - RH `fastapi_14448`: BASE exits 1.

  Counting these as visible adds 1 per arm. The other C tasks stay unreadable, so V on R is somewhere between 2 and 7 of 22.

## Required fixes (zero GPU)
1. §9.3: replace "2 of 27 and 1 of 22" with the bounded statement in the Verdict, and add the n′ 22 / 17 line as post hoc.
2. §9.4 item 1: replace "unaffected" with "concordant in all eight gradings". Add the informative set as run (about 27) and the smoke-8 consequence.
3. §9.4 item 2: "mostly the patch's own collection errors" is 1 of 6 in R and 1 of 5 in RH. BASE already fails collection on the others.
