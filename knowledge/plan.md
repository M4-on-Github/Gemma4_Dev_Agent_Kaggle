---
id: plan
updated: 2026-11-03
direction: D-002, D-003; D-004 proposed
---

## Next experiments (in order)

| # | Claim | What it tests | Endpoint | Expected gain | GPU-h | Why now |
|---|---|---|---|---|---|---|
| 1 | C-003, C-008, C-007 | ~~EXP-028 Arm R analysis~~ done 2026-11-03 (§9): mean 297 s, 10.04 h projected, T2 + T4 fire | | | 0 | awaiting critic `light` |
| 2 | C-005 | ~~EXP-028 RH vs R~~ done: compliance 0/8 vs 0/6, row 4, section dropped from the LB lineage | | | 0 | awaiting critic `light` (moves C-005) |
| 3 | C-002 | ~~Read #11~~ done: 0.17 = 10/58, EXP-027 row 3, baseline tree adopted; #12 = second draw (S-012, EXP-029) | | | 0 | upload today if approved |
| 4 | C-007 | `max_tool_calls` 28 -> 40 on the chosen tree, paired with it | calls-cap incidence, empty patch, time profile | <= 2 tasks, unreadable on LB; readable on dev-48 process endpoints | ~0.8 screen, then ~4-7 | only if EXP-028 T4 fires; L2 screen first (does the 40-call tree breach the 8-min cap on smoke-8?) |
| 5 | C-008 | Cap arm (7 / 9 min) from the measured mean | time profile vs ceiling | safety margin or more finishing time | ~4-7 | only after T1-T3 are known |
| 6 | C-004, C-005 | Paper section 4 from the accepted EXP-028 result | n/a | paper deliverable | 0 | Nov 5 draft |
| 7 | C-014, C-004 (D-004) | Screen A1-A3: `SequentialAgent[locator, editor]` built from the v24 prompt split by role, on smoke-8, paired against EXP-028 Arm R on the same 8 ids | runs end to end 8/8; added wall per task; edit arg-loss rate per call (Fisher) | decides whether the team direction lives | ~0.8 | needs the user's approval of D-004 and EXP-028 Arm R downloaded for the pairing |

## GPU budget this week

| Window | Spent (kernel wall, EXP §9) | Committed (running) | Remaining of 30 | Next arms costed |
|---|---|---|---|---|
| unknown (reset day unverified) | EXP-028 R 4.12 h + RH 4.09 h = 8.21 h (§9), run week of Oct 28 | none running | unknown; nothing spent this week so far | item 4 or 5: one dev-48 arm 4-7 h; any new claim: smoke-8 screen ~0.8 h first |

Ask the user to read the sidebar quota counter once; record the figure, the reset day and whether L4x4 counts 1x in the harness-stack skill.

## Next upload slot

S-012 (tree R, second draw) scored 0.18 = 11/58 (ref 57970005); EXP-029 row 3: pooled baseline 21/116, about 10.5 per draw; next slot goes to the next candidate. No screened candidate exists as of 2026-11-05. Candidates in order: (a) D-004 P1, a parallel read-only locate stage feeding one editor, with `max_tool_calls` raised in the same smoke-8 (D-004 addendum 2026-11-05; needs the user's approval of D-004 and a critic `direction` review); (b) `max_tool_calls` 40 alone (EXP-028 T4) after an L2 screen. A third draw of R is the only zero-risk filler for an otherwise empty slot. Digest 2026-11-05 (rank 1 at 0.29, board sweep) pending.

## Waiting on

- Critic `light` review of EXP-028 (moves C-003/C-008 time profile and C-005).
- Fix in experiment-protocol step 7: summaries live at `experiments/EXP-NNN/<arm>/summary.jsonl` (hygiene accepts only that name).
- Critic backfill of migrated claims (start with EXP-024, EXP-025, EXP-027).
- D-004 approved 2026-11-05 for screens only, ceiling 3.2 GPU-h, no dev-48 arm, no upload. Spent so far: 0 GPU-h (EXP-030 kernel `rainm4/gemma4-exp030-p1` failed in the parameter cell on an unquoted `EXP_ID`, no task ran; superseded).
- Critic direction review of D-004: needs-work (`experiments/EXP-030/critic.md`). Budgets are shared per task, so a parallel locate stage buys wall-clock only; the measured failure is the wrong fix in the right file, not location. Redesign: EXP-032, two arms on `capbound-8` (T4 single loop at the raised cap against P1 parallel tree at the same cap), about 1.6 GPU-h, critic `prereg` before push.
- EXP-032 (commits 1118e9b, 40cc718, e96ceb7): critic `prereg` needs-work with six §7 additions, applied, lead checked the diff. Arm P1 kernel `rainm4/gemma4-exp032-p1` pushed 2026-11-05, seen RUNNING at 13:29 UTC; estimated 1.0 to 1.35 GPU-h. Arm T4 held: pushed only if P1 is not row 0 and has no localize-stage crash (about 1 GPU-h more). GPU ledger for D-004 screens: 0 spent before this kernel, ceiling 3.2. Next: analysis job to the screener when the kernel completes.
- Zero-GPU items done by the experimenter (d0e994b, f7bf6d5, 4657dce, 86fc90f): builder refuses unparsable `--set`; L1b aggregates in `experiments/EXP-030/l1b_armR.json` (match the critic except cap-bound first gold-file edit at median call 23, not 25); compaction detector fixed (EXP-028 R 49 in 36/48, RH 49 in 35/48, every cap-hit task compacted; older committed summaries still read 0); Q7 answered from source (`.claude/skills/harness-stack/reference/compaction.md`): threshold 14,336 checked before every model call of every agent on the session's latest prompt count regardless of branch, summarizer on the task clock, no `agent.yaml` control.
- EXP-033 E4B single-loop smoke-8: done (f8f7a5a), row 3 fired: loop works, 0 of 8 capped, 0 malformed calls, 6 of 8 non-empty patches, mean wall 56.9 s, 423 s left under the cap; resolves 2 of 8 recorded, not read. Critic `light` review not yet done. GPU ledger for the D-004 screens: E4B about 0.25 spent; first P1 push canceled by the user by accident at about 14:10 UTC after about 40 minutes, about 0.7 lost, no output read; P1 re-push 1.0 to 1.35 expected, which brings the total to 1.95 to 2.3; T4 (about 1.0) would pass the 3.2 ceiling at the upper end, so it runs this week only if P1 comes in near 1.0 or the user raises the ceiling.
- Bounds B1 to B14 and the measurement matrix are in D-004 (addendum 2026-11-05).
- D-005 (architecture-family benchmark): Stage 0 and the critic's `direction` review are in (`experiments/EXP-034/critic.md`, needs-work). Main finding (C-021): 15 of 48 dev-48 tasks are graded without two test-only packages, the shipped v24 prompt has no vendoring text and resolves 0 of them, and 11 of Arm R's 30 right-file-wrong-fix tasks were never graded on their fix. D-005 revised the same day: zero-GPU re-grade first (EXP-036, CPU kernel), then one change at a time on smoke-8 against Arm R at 8 min (vendoring section, then a required executed check, structures only after), the 4.5 min common setting and the F0 arm dropped, the E4B dev-48 arm moved out as the user's separate decision. EXP-035 (1309bd9): no reading, 16 of 30 grader outputs unreadable. EXP-034 fixes done (85ad54d). EXP-036 is pre-registered and built (d86d09c, 3d9d12c, 5c239ff, 1c8e9c8) but **not run: `guard_push.py` refused the push** ("RUN_AGENT is not True"; the rule allows a kernel that does not run the agent only from an exp000 directory, and the re-grade kernel is CPU-only with no agent run). No workaround was tried. The user approved a CPU-only exception to the guard the same day (`knowledge/user-decisions.md`, ~15:00 UTC); the push is re-dispatched to the experimenter. Also raised by the experimenter, the user's call: the tracked EXP-004 files `notebooks/regrade_shim_dev48/kaggle_regrade_shim.{py,ipynb}` embed zips of agent patches (plan.md:52). After EXP-036 runs: its analysis job, EXP-035 on the re-graded outputs, check 0d, then the user's decision on the revised screens.
- Done: `submissions.md` row 12 = 0.18 (11/58), EXP-029 §9, small-model names in the rules (commits 2538bc6, 1cd52f8); EXP-031 pre-registered and S-013 proposed (third baseline draw, not uploaded).
- User: today's upload slot (S-013 or empty; closes 2026-11-05 23:59 UTC), what "resets at 7pm" refers to and the GPU-hours left this week, plan.md §5.8 rewording.

## Not pursued

- LoRA adapters (C-013): the only same-model data is -10.8 points; no-go at the Oct 25 gate (EXP-022 §2.3).
- Sub-agents / same-model delegation (C-014): spends time, adds no capability; sync tool stall 78% (EXP-007).
- Best-of-N editing branches (C-015): no selection proxy without hidden tests; shared `/workspace`.
- Graph tools (C-012): lose to grep at every k.
- Further surgery on the 12.8 KB prompt (C-009, D-001 killed).
- Smoke-8 thinking x s/call calibration (EXP-024 §4 item 7): re-measures an owned quantity in the harmful direction.
- `pytest -k` from the 0.24 prompt (C-017): grading runs whole files.
- Context-reset trick from the paper-track forum post: unsourced 96% vs 16%; revisit only if a kaggle-scout note gives its method.
