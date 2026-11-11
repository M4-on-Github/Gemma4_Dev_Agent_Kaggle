---
id: D-010
title: E4B pipeline, five adaptive tweak rounds (11-11)
decision: start
status: active on the user's word (2026-11-11, "gi for 5 more harness trweaks for e4b agents", f3df1e5). The critic's `direction` review came back needs-work (experiments/EXP-070/critic.md, 49784a4, 3d0fc69). All six fixes are accepted; see the revision below.
track: main
claims: [C-015, C-019, C-021, C-023]
date: 2026-11-11
---

## What are we trying to do?
Five more single-variable changes to the E4B pipeline agents (root, reader, drafters, applier). Each is screened on smoke-8, and each is chosen after the last reading. The aim is a tree with more resolves on the hidden set. Edit reliability is one route to that, but no longer the only one.

## How is it done today?
- **Tree:** EXP-064 `candidate-loc`, scored 0.01 on the leaderboard as S-016. The same shape scored 0.05 as S-014 and S-015. The 31B single loop's best is 0.18 (S-012).
- **D-009 ended by its two-rounds rule:**
  - EXP-068 had drafters read their own lines. Its row 6 moved the failure to line drift.
  - EXP-069 had the applier use bare paths. It read row 3, not exercised: no quoted path occurred.
- **Unresolved classes on EXP-053** (24 unresolved): right file, wrong fix 12; wrong file 8; edit failure 4.
- **Smoke-8 resolves** are 1 to 2 of 8 per run and are recorded only. n = 8 cannot read a resolve effect. Every round is read on a process endpoint.

## What's new in our approach?
- **The rounds are adaptive and ranked by desk-checked evidence.** Round 1 runs now; rounds 2 to 5 are ranked after EXP-070, the experimenter's zero-GPU desk check.
- **Round 1, EXP-071: the anchor form** (screener, dispatched 2026-11-11).
  - The reader's LINES must come from a numbered output it ran, such as `grep -n` or `nl -ba`, not from counting by eye.
  - Evidence (EXP-068 §10): the 3 window misses are in the right file, 7 to 15 lines off. The same 5 to 9 line drift shows on 3 of 12 tasks in the REGION trees. On rich_3468 the reader's own `grep -n` printed the right line and it was not used.
  - Base: EXP-068 `candidate-read`.
- **Candidates for rounds 2 to 5** (EXP-070 measures the numbers each one needs first):
  - **Executed verify step in the applier (C-019):** run the edited module's test file after the last applied edit; if the run shows new failures, revert and try the next draft. This targets the largest class, right file wrong fix. Endpoint: verify executed on N of 8.
  - **Reader empty-report guard:** the reader's final report must open with FILE. One case is known (requests_7309, EXP-068); EXP-070 counts the rate.
  - **Draft diversity or selection (explore quota):** if the 5 drafts are mostly identical, give each drafter a distinct strategy or temperature. If they differ, give the applier a selection rule. This draws on C-015 and C-023, not the public frontier's design.
  - **Vendoring the two test-only packages (C-021):** only if a zero-GPU re-grade of the pipeline's patches flips any task. The E4B single loop flipped 0 of 15.
  - **Wider drafter window (±20):** held back as the anchor form's fallback.
- **Round 5 is chosen by rounds 1 to 4.** If any form is kept, round 5 is the fused tree of the keepers on smoke-8, as an upload candidate for the user. Otherwise it is the next ranked candidate.

## Options
- **A: the five rounds as above.** About 2.0 GPU-h.
  - Strongest argument against: this carrier draws 0.01 to 0.05 against the 31B's 0.18, and n = 8 screens read only process endpoints. A kept form moves the leaderboard only if it moves at least 4 tasks of 58.
- **B: spend the five on the 31B single loop.** Not chosen: the user named E4B agents.
- **Lead's recommendation:** A, on the user's word. Each round is read on a mechanism endpoint, so a kept form has a stated reason to ship.
- **Critic's dissent (needs-work, 2026-11-11, verbatim):** "D-010 reads a mechanism endpoint on the E4B as a reason to ship, and the record says otherwise. EXP-069 landed the first edit on 8 of 8 tasks with 0 empty patches, and resolved the same 2 of 8 tasks as EXP-064. Of 23 unresolved patched task-runs that have an empty-patch grading of the same task, 21 grade like the empty patch. A verify that acts only on new failures therefore has about one event to act on, and a selector built on it will pick draft_1, which the applier already picks in 27 of 40 multi-draft passes. Round 4's per-drafter temperatures have been in the tree since EXP-052 (0.3 to 1.0). A kept form on a carrier that scores 0 to 3 of 58 cannot approach our 0.18 on a best-of LB. It cannot be read at an MDE of 4. It would also take a final that belongs to a 31B variant. The one round that could create a selection signal is a reproducer stage with the hard first-call opener. That opener removes the probable cause EXP-068 §1.3 named for EXP-063. It held on 36 of 40 drafter turns, but it has not been tested on a reproducer. D-010 does not rank this round. A kept form justifies a written finding and a time-costed 31B port proposal, not an upload."
  - **Lead's response:** accepted in full (see the revision below).

## Expected score impact
- 0 to 2 tasks of 58 for the batch, P about 0.25 [I].
- Only through an E4B upload on the user's word.
- Below the 4-task MDE: a leaderboard draw cannot read it.

## Risks and kill criteria
- **A round's harm row binds:** its form is dropped.
- **Three rounds in a row not exercised:** stop and put the cohort question to the user. Rare classes miss at n = 8 (EXP-069).
- **Spend reaches the 2.5 GPU-h ceiling:** stop.
- No dev-48, upload or re-run without the user's word.

## Cost
Five smoke-8 runs at about 0.35 to 0.40 each, so about 2.0 GPU-h, with a ceiling of 2.5. No upload slots.

## Midterm check
After rounds 1 and 2: at least one is exercised and reads no harm. Otherwise the remaining rounds go to the candidates with the highest opportunity counts in EXP-070.

## Final check
- Restated 2026-11-11 (revision item 5): a kept form yields a written finding plus a time-costed 31B port proposal. An E4B upload happens only on the user's word.
- Otherwise, a written finding of which forms the E4B did not take up.

## Ranking after EXP-070 (6780768, 66f43cc; zero GPU), 2026-11-11
- **Round 2, EXP-072: a runnable verify, which the experimenter builds on the EXP-064 `candidate-loc` tree.**
  - Trigger: an unprompted check ran after the last applied edit on 15 of 48 edited task-runs. Only 6 of those ran any test or code (about 1 per 8), and 0 ran an existing test file of the edited module.
  - On all 4 resolved task-runs that had a check, the check exited non-zero and the applier submitted anyway.
  - Hence a revert on "any failure" would have undone resolved fixes. The form must compare against a run before the edit and act only on new failures, with a harm row for a lost resolve on fastapi_14301 or rich_3006 (both resolved by EXP-064 and EXP-069).
  - Headroom: at least 271 s and 22 calls on the tightest task-run.
- **Round 3 depends on rounds 1 and 2:**
  - if EXP-072's check runs, a per-draft selection form: try a draft, run the check, keep the first draft with no new failure. Its trigger is "all drafts distinct" on 13 of 32 task-runs in the EXP-064 tree. Majority vote is ruled out, since it would change the pick on 2 of 40;
  - if EXP-071 is killed, the wider drafter window (±20), the anchor form's fallback.
- **Round 4, explore quota:** drafter diversity by sampling, a distinct `generate_content_config` temperature per drafter (config, not wording; C-023's lever on the drafter stage). Trigger: 2 or fewer distinct drafts on 13 of 32 task-runs.
- **Round 5:** the fused keepers, or the next ranked form.
- **Not a round of their own:**
  - the reader empty-report guard (3 of 57 passes, about 0.4 per 8), which may ride free;
  - vendoring (4 of 56 hits; the re-grade needs a Kaggle CPU kernel, not run).

## Revision 2026-11-11 after the critic (supersedes the ranking above)
1. **Round 4, drafter temperatures, is dropped.** The drafters have run at 0.3 to 1.0 since EXP-052, so the lever is already pulled.
2. **Round 3 is the wider drafter window.** It runs on any EXP-071 outcome except promote, and on the `candidate-read` base. Its width must cover the measured drifts, which reach 29 to 44 lines in EXP-068 §10.1; ±20 does not cover them. It ranks above selection.
3. **Round 4 is the reproducer stage with the hard first-call opener** ("Your first reply must be a run_command call, not text"). This is EXP-063 again, with the probable cause of its 0 tool calls removed. The opener held on 36 of 40 drafter turns in EXP-068. It is the one round that could create a selection signal, and it fills the explore quota, since it is a parked lever re-examined with new evidence.
   - Endpoints: the reproducer's first-turn tool call, and the share of reproducer runs that fail before the edit.
   - Base: `candidate-loc`.
4. **Round 5, in this order:**
   - (a) per-draft selection, only if EXP-072 shows new-failure events on at least 2 of 8 (the critic's reference is about 1 in 23);
   - (b) otherwise the fused keepers on a named base: `candidate-read` if EXP-071 or round 3 is kept, else `candidate-loc`;
   - (c) otherwise a written finding.
   - Any fused round must lose no resolve on fastapi_14301 or rich_3006. EXP-068 lost rich_3006, which resolved in the other six pipeline runs.
5. **The final check is restated:** a kept form yields a written finding plus a time-costed proposal to port it to the 31B. A verify costs 20 to 40 s, against the 31B's 13.8 s of room to the 10.5 h ceiling and 28.8 s to the 11 h gate. An E4B upload happens only on the user's word; a kept form does not justify a slot on leaderboard grounds.
6. **EXP-072's flags,** sent to the experimenter before its push:
   - a new-failure event count with a blind prediction;
   - collection that exits 2 both before and after counts as no signal;
   - the lost-resolve harm row;
   - the base named.
