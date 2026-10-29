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

## Predictions

| Decision | User's one-line prediction | Pre-registered prediction | Actual |
|---|---|---|---|
| #11 (EXP-027, v24 at 8 min) | not asked | k ~ 10 of 58, band 6-14 | pending |
