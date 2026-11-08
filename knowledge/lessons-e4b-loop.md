---
id: lessons-e4b-loop
updated: 2026-11-08
topics: [prompt, tools, edit-reliability]
---

# E4B smoke-8 edit loop: lessons

The experience file of the loop the user started on 2026-11-08 (`knowledge/user-decisions.md`), after the Harness² paper's Experience Reflector. Kept by the research lead from each round's handback; one entry per round.

**Entry format:** round and EXP; cue (the class of trace moment, with task ids and step numbers only); lesson (own words); evidence (counts and the EXP section); confidence ([V] measured here, [I] inference); outcome (kept, revised, dropped, or keep-base). The hygiene line applies: ids, counts, step numbers, class letters, file paths, program names, exit codes and own words only; nothing a repo or the model wrote.

## Rules of the loop

- Base set: E4B runs on the smoke-8 ids (EXP-033, EXP-038, EXP-052, EXP-045). fastapi_14301 and rich_3006 resolve on about 3 runs in 4; the other six on none.
- Each round tries one or two candidate edits, each its own pre-registered smoke-8, each citing trajectory moments on at least 2 of the 8 tasks. A failure seen on one task is noise.
- An edit may be found from a repo-specific moment (the user's development relaxation); it is written repo-agnostically before its push.
- Readings are written blind on process endpoints: edit attempts, applied edits, a non-empty patch, wall, malformed calls, and the count of the failure the edit targets. Resolves on 8 decide nothing.
- The next round starts from the tree of the last kept edit.
- Stop at the day's GPU ceiling, after two keep-base rounds in a row, or on any infrastructure failure.
- A kept edit counts only after an LB draw or a dev-48 arm; the small-model reference is S-014's 3/58.

## Round 0: EXP-045 (analysis dispatched 2026-11-08)
