---
id: lessons-e4b-loop
updated: 2026-11-08
topics: [prompt, tools, edit-reliability]
---

# E4B smoke-8 edit loop: lessons

The experience file of the loop the user started on 2026-11-08 (`knowledge/user-decisions.md`), after the Harness² paper's Experience Reflector. Kept by the research lead from each round's handback; one entry per round.

**Entry format:** round and EXP; cue (the class of trace moment, with task ids and step numbers only); lesson (own words); evidence (counts and the EXP section); confidence ([V] measured here, [I] inference); outcome (kept, revised, dropped, or keep-base). The hygiene line applies: ids, counts, step numbers, class letters, file paths, program names, exit codes and own words only; nothing a repo or the model wrote.

## Rules of the loop

- Base set: E4B runs on the smoke-8 ids (EXP-033, EXP-038, EXP-052, EXP-045). fastapi_14301 and rich_3006 resolve on all 4 runs each (8 of 8 task-runs, EXP-053 section 1, corrected 2026-11-08 from "about 3 runs in 4"); the other six on none of 24.
- Each round tries one or two candidate edits, each its own pre-registered smoke-8, each citing trajectory moments on at least 2 of the 8 tasks. A failure seen on one task is noise.
- An edit may be found from a repo-specific moment (the user's development relaxation); it is written repo-agnostically before its push.
- Readings are written blind on process endpoints: edit attempts, applied edits, a non-empty patch, wall, malformed calls, and the count of the failure the edit targets. Resolves on 8 decide nothing.
- The next round starts from the tree of the last kept edit.
- Stop at the day's GPU ceiling, after two keep-base rounds in a row, or on any infrastructure failure.
  - Round 0 does not count toward "two keep-base in a row": it is the reading of an experiment pre-registered before the loop began (EXP-045, 2026-11-05), not an edit the loop chose (lead's reading, 2026-11-08).
- A kept edit counts only after an LB draw or a dev-48 arm; the small-model reference is S-014's 3/58.

## Round 0: EXP-045 (analysed 2026-11-08, ee6b6a3)

- **Edit:** a bullet to write and run a short reproduction through `run_command` after the last edit and before `submit_patch` (pre-registered 2026-11-05, before the loop).
- **Cue:** `write_file` to a path under `/tmp` is refused (requests_7309 step 6, rich_3468 step 11, rich_3006 step 8).
- **Lesson:** a scratch path outside the workspace is reachable only through `run_command`; a prompt that asks for a scratch file must name a workspace path or ask for a one-line command.
- **Evidence:** 3 of 8 tasks hit the refusal; informative checks C = 3 of 8 (C = 2 if httpx_3672's run is read as uninformative); EXP-045 sections 9.0 to 9.2. 0.248 GPU-h (kernel-log span).
- **Confidence:** [V] for the refusal; the check-rate reading is row 5, no decision.
- **Outcome:** not kept (row 5). Round 1 starts from the EXP-033 tree.

## Round 1: EXP-053 (pre-registered 69092da, pushed 29d9035, kernel `rainm4/gemma4-exp053-r` v1)

- **Diagnosis first (zero GPU, 32 task-runs, EXP-053 section 1):** over the 24 unresolved runs, class C (right file, wrong fix) 12, A (wrong file) 8, B (an edit failing at one place) 4; no check after the last edit in 12 of 24; a prose action in 1 of 32 (2 counting the EXP-052 compaction-crash ending). Failed `edit_file` calls by run 7, 10, 3, 5; resends of the same `old_string` 3, 4, 0, 2, which `n_identical_repeats` does not count.
- **Edit (Arm R):** one prompt bullet. After a failed edit, never resend the same `old_string`; on not-found, re-read the lines and copy them exactly; on more-than-once, start at a unique line above the change with at least three whole lines; after two failures at one place, make a smaller edit.
- **Cue:** a failed `edit_file` followed by a resend of the same `old_string` (requests_7205 EXP-033 steps 8 to 10; httpx_3672 EXP-038 steps 7 to 9; fastapi_14605 EXP-038 steps 9 to 11, EXP-045 steps 10 to 12, EXP-033 steps 14 to 15).
- **Lesson (pending):** an edit that fails and is resent unchanged wastes turns; whether a prompt rule stops the resend on the E4B is what EXP-053 reads (resends R_x; failed edits N_f).
- **Evidence:** base resends 3, 4, 0, 2 over 3 tasks. The not-found half has a null prior (EXP-044's control X0).
- **Confidence:** [I] until the run is read.
- **Outcome:** pending. Readings as written in EXP-053 section 3: row 0 infrastructure; row 1 harm, dropped; row 2 N_f below 3, not exercised; row 3 R_x 2 or more, dropped; row 4 R_x 0 with N_f 3 or more, kept; row 5 otherwise, keep-base. Blind prediction N_f 5, R_x 1. Expected 0.27 GPU-h (0.25 to 0.33).
- **Named for a later round (Arm L, not built):** edit where the behaviour is decided, not where it is called (fastapi_14448 EXP-033 step 5, EXP-038 step 7, EXP-052 step 13; rich_3468 EXP-033 step 6). Its process endpoint has references 5, 6, 6, 7 of 8, so one step of room at n = 8.
