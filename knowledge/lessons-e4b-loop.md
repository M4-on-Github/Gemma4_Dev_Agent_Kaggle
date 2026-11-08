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

## Round 1: EXP-053 (pre-registered 69092da, pushed 29d9035, analysed bdea22a)

- **Diagnosis first (zero GPU, 32 task-runs, EXP-053 section 1):** over the 24 unresolved runs, class C (right file, wrong fix) 12, A (wrong file) 8, B (an edit failing at one place) 4; no check after the last edit in 12 of 24; a prose action in 1 of 32 (2 counting the EXP-052 compaction-crash ending). Failed `edit_file` calls by run 7, 10, 3, 5; resends of the same `old_string` 3, 4, 0, 2, which `n_identical_repeats` does not count.
- **Edit (Arm R):** one prompt bullet. After a failed edit, never resend the same `old_string`; on not-found, re-read the lines and copy them exactly; on more-than-once, start at a unique line above the change with at least three whole lines; after two failures at one place, make a smaller edit.
- **Cue:** a failed `edit_file` followed by a resend of the same `old_string` (requests_7205 EXP-033 steps 8 to 10; httpx_3672 EXP-038 steps 7 to 9; fastapi_14605 EXP-038 steps 9 to 11, EXP-045 steps 10 to 12, EXP-033 steps 14 to 15).
- **Lesson:** a prompt line against resending a failed `old_string` does not stop it on the E4B. The model changed its string in 4 of 6 retries and resent in the 2 that mattered (fastapi_14605 step 11, httpx_3672 step 11), so more wording on this is the wrong next move. A harness reply naming the other occurrences would be a tool-side change, not reachable from `submission/`.
- **Measured:** R_x 2 (base 3, 4, 0, 2); N_f 8 (base 7, 10, 3, 5); non-empty patches 8 of 8; mean wall 66.8 s, longest 150.5 s; no errors, nudges, caps or stray files; resolves 2 of 8, the same two, not read. 0.281 GPU-h (kernel-log span). R_x is a hand count by EXP-053 section 2.2.
- **Evidence:** base resends 3, 4, 0, 2 over 3 tasks. The not-found half has a null prior (EXP-044's control X0).
- **Confidence:** [V] for the counts.
- **Outcome:** **dropped, row 3** (first keep-base round in a row; round 0 does not count). Readings as written in EXP-053 section 3: row 0 infrastructure; row 1 harm, dropped; row 2 N_f below 3, not exercised; row 3 R_x 2 or more, dropped; row 4 R_x 0 with N_f 3 or more, kept; row 5 otherwise, keep-base. Blind prediction N_f 5, R_x 1. Expected 0.27 GPU-h (0.25 to 0.33).
- **Named for a later round (Arm L, not built):** edit where the behaviour is decided, not where it is called (fastapi_14448 EXP-033 step 5, EXP-038 step 7, EXP-052 step 13; rich_3468 EXP-033 step 6). Its process endpoint has references 5, 6, 6, 7 of 8, so one step of room at n = 8.

## Round 2: EXP-055 (pre-registered 9601dd0, pushed 3be1b7d, analysed b6da125)

- **Base tree:** EXP-033 (round 1 dropped).
- **Edit (Candidate V):** three hunks in section 4 of the prompt. A new bullet makes the last call before `submit_patch` a one-command check after the last edit (the named test file or an import of the changed module; no scratch file, after the round 0 `/tmp` finding), with one repair when the output shows a syntax, indentation, name or import error pointing into an edited file. Two phrases that licensed skipping the check or ignoring an import error are removed.
- **Cue:** D, the run ends on an edit with no command after it (fastapi_14448 and httpx_3672 in EXP-053; fastapi_14605 in EXP-038 and EXP-045; requests_7205 in EXP-052). G, a failing check pointing into the edited file and submitted anyway (httpx_3672 in EXP-045, steps 7 to 8).
- **Evidence (base):** D 14 of 30 non-resolving runs; G 1 of 32; tasks with a check after the last edit at most 6 of 8 in any reference run.
- **Readings (EXP-055 section 4, blind):** row 0 infrastructure; row 1 harm, dropped; row 2 V1 (tasks with a check after the last edit) 6 or fewer, dropped; row 3 V1 = 7, no decision; row 4 V1 = 8 and G = 0, kept; row 5 V1 = 8 and G 1 or more, no decision. Blind prediction V1 = 7. Expected 0.30 GPU-h.
- **Measured:** V1 = 7 of 8 (reference maximum 6), G 0, repairs 0; applied edits 7; non-empty patches 7; gold-file landings 6 of 8 (wrong file still on httpx_3672 and rich_3468); mean wall 75.4 s, longest 166.5 s; no caps, stray files or malformed calls; one task `error` (fastapi_14448). Resolves 2 of 8, the same two, not read. 0.302 GPU-h (kernel-log span 1,088.8 s). Blind prediction (V1 7, G 0) landed.
- **Lesson:** the mandatory-check sentence was obeyed on 7 of the 7 tasks that made calls, but a check that runs is not a check that tests the edit: 3 of 7 ran no tests (pytest exit 4 on httpx_3672, exit 5 on fastapi_14605 and rich_3468) and 1 hit a collection error that predates the edit (exit 2, fastapi_14301). More wording about whether to check is not the next gain; what the check runs is a mechanism problem.
- **New observation [I]:** fastapi_14448 made 0 tool calls; four of its final messages carried a tool call written as fenced text, with nudges between them and an empty patch (class F, 1 of 8; 0 in about 46 earlier E4B traces searched). It came before any check, so the edit is not an evident cause; a tree effect is not excluded at n = 1.
- **Confidence:** [V] for the counts (hand counts by EXP-055 section 2.2); [H] for the interpretation.
- **Outcome:** **row 3, no decision, keep-base.** Second keep-base round in a row (rounds 1 and 2), so **the loop stopped on its rule, 2026-11-08**. Loop spend 0.831 GPU-h of its 2.8 share. Its next design (for example two runs per candidate, after the Meta-Harness baseline's 3 replicates in the Harness² paper) is the user's call.
- **Considered and not built:** Arm L (edit where the behaviour is decided). Its target tasks already land in the gold file on 2 of 5 base runs (fastapi_14448) and 4 of 5 (rich_3468), so a smoke-8 has no kept row beyond chance (screener, 2026-11-08); no GPU spent.

