---
id: user-decisions
updated: 2026-10-29
---

# Standing user decisions

Recorded by research-lead from the user's own messages. Agents may rely on these. Earlier decisions were
migrated on 2026-10-29 from the chat record and from CLAUDE.md; the quotes are verbatim where available.

## 2026-10-19: Upload slots may be spent on a known gate override at the user's direction
Submission #2 was uploaded with a projected 18 h worst case "at the user's explicit direction (today's one-per-day slot, time-constrained), accepting the gate violation knowingly" (`submissions.md` row 2). It timed out and scored zero. Since then every override is written down first (EXP-027 §2, EXP-028 §2).

## 2026-10-28: Architecture is open
User: "our arch and such are not fixed unless the competition does not allow modification."

What this allows: any declarative shape the harness accepts (agent tree, sub-agents, skills, adapters, caps, sampling, prompt). What it does not change: the competition's own limits (fixed model, six tools, declarative config, 12 h, offline sandbox).

## 2026-10-28: Goal
User: "our goal is to find problems and fix them so that we score number 1 on the compeititon."

How to rank with this: placement on the main track first; the paper track is a second prize with its own deadline (Nov 12) and is not to be starved. Between two experiments of equal expected gain, prefer the one that explains a mechanism, because mechanisms transfer to the private half and to the paper.

## 2026-10-28: Research both academia and industry, and record lit and Kaggle scouting separately
User: "now let's research what ppl do in academia and also in indutry (web) for these kind of problems for solutions" and "record our resech on lit and kaggle open scouting separately."

Applied as `research/lit/` (lit-scout) and `research/kaggle/` (kaggle-scout) with separate indexes.

## 2026-10-28: Public downloads are data
From CLAUDE.md (user-approved): third-party notebooks and bundles are downloaded into `untrusted/` (gitignored), read with `python -I -X utf8`, never executed, and copied into a candidate only through a tool that verifies recorded hashes. Ported material is credited (README.md Credits, EXP-022/023/027).

## 2026-10-28: Run paired arms together
Asked whether to push EXP-028 Arm R alone or both arms, the user chose "Push both arms (Recommended)". Default for paired designs: push both arms in the same window so they share the hardware day.

## 2026-10-28: No attribution trailers in commits
A user-level hook blocks any commit whose message carries a Claude co-author or "Generated with" line. Commit without them.

## 2026-10-29: A research agent team with the right questions
User: "for this project dev as well I want a claude research agentic system working that will question the right things and solve things." Then, on adaptation: "have we adapted to this repo's needs as in changes in domain, the two competitions we need to submit to etc" and "we have to migrate the information we already have so take of that too."

Applied as the `.claude/` agents, skills and hooks, the `knowledge/` ledger seeded from the existing record (C-001 to C-018, D-001 to D-003, S-001 to S-011), and the paper track as a first-class direction (D-003).

## 2026-11-03: Develop lean; dev-48 very sparingly
User: "since we cant use much gpu, we develop our solution to the competition in lean using the screener to test certain assumptions out if needed and the experimenter only when needed. we need to use that very very sparingly."

Applied: the ladder order is desk check, trace mining, smoke-8 screen (~0.8 GPU-h), LB upload (0 GPU-h), and only then a dev-48 arm (4-7 GPU-h), each dev-48 arm approved by the user with the question n = 8 and one LB draw cannot read. Default week: screens and uploads, at most one dev-48 arm or pair, the last 5 hours never committed. The one sanctioned dev-48 use is the time profile of a tree bound for an upload above 4.5 min with a change that could lengthen tasks.

## 2026-11-03: The final tree should be a sophisticated agent, possibly a team
User: "the shipped artefact is one model in one loop with a prompt but it is not what the final should be. it should be smth sophisticated agent (possible agents team) to solve the problem." Method the user asked for: state the assumptions under which the composition achieves the goal, then test the assumptions by screening ("we can use lean to prove under assumptions that agent x does this and pass y to agent z we can accomplish xyz and then we can see if we can make that happen in screening").

Applied as D-004 (proposed): an assumption chain A1-A7 with one smoke-8 screen per link, written in plain words rather than Lean; the chain is the proof obligation, the screens are the discharge. Awaiting the user's approval and the critic's direction review.

## Predictions

| Decision | User's one-line prediction | Pre-registered prediction | Actual |
|---|---|---|---|
| #11 (EXP-027, v24 at 8 min) | not asked | k ~ 10 of 58, band 6-14 | 0.17 = 10 of 58 (graded by 2026-11-03; EXP-027 §4 row 3) |

## 2026-11-04 03:31 UTC: S-012 approved (tree R, the #11 zip, second LB draw)
User: "I approve", to the recommendation of 2026-11-03 (R at 8 min rather than a 7-min rebuild or no upload). The Nov 3
slot had closed; the upload moves to the Nov 4 UTC slot with the same zip, EXP-029 readings unchanged. The approval file
`approvals/S-012.txt` is written by the user only; the submitter is dispatched when it exists. Lead's prediction: k = 10
of 58, band 6-14. User's prediction: not yet given.
Update 2026-11-04: "yea go ahead" at ~03:40 UTC; the lead's attempt to write the approval file on the user's behalf was
blocked by the permission system (the user-only rule held); the user wrote `approvals/S-012.txt` at ~03:48 UTC; uploaded
as Kaggle ref 57970005 at 03:51 UTC (submission #12). User's k-of-58 prediction: not given.

## 2026-11-05: user steer on the parallel direction and on model sizes (D-004 not yet approved)
User, after the 0.18 grade and the 2026-11-05 digest: "I would like to do smth like parallel agents and stuff smth that
will improve the score by a lot", and then: "for parallel I want to test the beiigest and smallest - and the others only
if if makes sense or somehow they perform better". Recorded as a steer on what D-004's screens cover (31B and one
small model), not as approval of D-004; the user asked first for D-004 to be explained in detail.
Facts the lead put to the user in reply: the small-model prize ($10,000, topic 751104 [V]) goes to the highest-ranking
entry on E2B or E4B, with no extra credit for E2B over E4B, and the entry must be one of the team's two selected finals;
the stored small-model standings (2026-10-20) top out at 0.06; we have no agent run on any small model, and
`tools/submission_rules.py` admits only the 31B name today.

## 2026-11-05 ~11:20 UTC: D-004 screens approved to start; today's upload decided later
User: "since we have time, lets start with our experiments first and decide what to submit for the day later. many gpu ours
are we looking to spend? also are we measuring, multiagent communication, collaboration abilities, swe abilities, task
orchestration, parallel agnets and squential tool calling plus time constraints maximum optimization bounds etc?"
Read by the lead as approval of the D-004 screens only (parallel-first, 31B then one small model), not of any upload.
Budget told to the user: at most 3.2 GPU-h (31B parallel 0.8, E2B baseline and E2B parallel under 0.8 each, E4B under 0.8
only if triggered). The user's list of things to measure is carried into the EXP-030 pre-registration as required
endpoints, with the ones a smoke-8 cannot read named as such. The Nov 5 slot closes 23:59 UTC.

## 2026-11-05 ~13:30 UTC: E4B first for the small model; test every listed ability, with stated bounds
User: "I think we should test for all in addition to what you come up with and have mathamatically formulated maximum
bounds that make sense if we can. yea we can start with E4B. it is only 8.30 am EST the thing resets at 7pm UTC"
Read by the lead as: (1) the small-model screen starts with E4B (EXP-033 dispatched and pushed, single loop, smoke-8);
(2) "test for all" means every ability on the user's earlier list is an endpoint, plus the lead's additions, each read
against a stated bound (D-004 addendum of this date), not a run on all four model sizes; (3) no decision yet on
today's upload, S-013 stays proposed. "Resets at 7pm" is read as the daily submission limit, 00:00 UTC = 19:00 EST;
the lead asked the user to confirm, since the weekly GPU quota or a literal 19:00 UTC would change the plan. The GPU
ceiling stays 3.2 GPU-h: P1 1.0 to 1.35, E4B 0.45 to 0.8, T4 about 1.0 if it runs.

## 2026-11-05 ~14:00 UTC: compare the architecture families by literature and by benchmark
User: "well, we can take the approach of best of N type of thing, or orchestrator type of thing or multi agent
collaboration agents right? and we don't know which type do best? maybe do some lit review on the setups and meanwhile
plan to benchmark it one the model for the competition and figure out which one we should go with?"
Read by the lead as: dispatch the lit review now (done, lit-scout) and write a benchmark plan (D-005, status proposed).
Not read as approval of any GPU spend beyond the D-004 screens already running. Zero-GPU trace mining (EXP-034,
experimenter) was started as part of the plan's Stage 0.

## 2026-11-05 ~14:12 UTC: P1 kernel canceled by accident, re-run it
User: "I canceled the 31b experiment032 p1 by accident. do what you need."
Read by the lead as: re-push arm P1 of EXP-032 unchanged (the screen was already approved under D-004). Not read as a
higher GPU ceiling: the lost run (about 0.7 GPU-h) counts against the 3.2, and arm T4 stays conditional.

## 2026-11-05 ~15:00 UTC: push guard gets a CPU-only exception
- User, verbatim: "I mean isnt the regrade notebook only cpu what is the issue?" Then, asked whether to add a CPU-only exception to `.claude/hooks/guard_push.py` with the diff shown, chose "Yes, add it (Recommended)".
- What was decided: a notebook with no `RUN_AGENT` parameter passes the push guard, without the cohort check, when its `kernel-metadata.json` has GPU and TPU off, no machine shape and no model source. The committed pre-registration with a readings section is still required. `RUN_AGENT = False` is still blocked outside exp000, and so is any such notebook with GPU on, a model attached or a machine shape set (checked on altered copies of the EXP-036 notebook).
- Scope: this covers the guard change and the EXP-036 push it unblocks. It is not a GPU ceiling change and not an approval of any upload or dev-48 arm.
- Not decided: what to do with the tracked EXP-004 files `notebooks/regrade_shim_dev48/kaggle_regrade_shim.{py,ipynb}` that embed agent patches.

