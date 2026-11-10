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

## Round 3: EXP-056 (pre-registered 8e40ffc, built 9a51a11, r1 pushed 1e21340 and analysed e85703f, r2 pushed 975b340)

- **Why a round 3:** the loop had stopped on its rule after round 2; the user approved one more round on 2026-11-08 (`knowledge/user-decisions.md`, about 19:15 UTC). Two smoke-8 runs (r1, r2) over one zip, after the Meta-Harness baseline's replicates in the Harness² paper.
- **Base tree:** EXP-033.
- **Edit (Candidate S):** a mechanism, not wording. `agent.yaml` declares one skill, `check-picker`, whose script reads the workspace and prints one check command (a named test file under pytest, or an import of the changed module) or a notice; the script runs nothing itself. Zip `1a591945...a33126`, packed with `--allow-warnings` (VERIFY(Q1)).
- **Cue:** round 2's lesson, a check that runs is not a check that tests the edit (3 of 7 EXP-055 checks ran no tests).
- **Readings (EXP-056 section 4, blind, pooled over 16 task-runs; r1 alone reads rows 0 and 1):** row 0 infrastructure (any script error S_x, more than 4 errors, or the tree does not run); row 1 harm, dropped; row 2 Ad (task-runs that call the script) 8 or fewer, dropped; row 3 T (last check tests the edit) 9 or fewer, dropped; row 4 T 10 to 12, no decision; row 5 T 13 or more with G 0 to 1, kept; row 6 T 13 or more with G 2 or more, no decision. Reference T 6 of 16. Blind prediction Ad 12 to 14, T 8 to 11.
- **Measured, r1:** row 0 **fired as written** through S_x = 2 (one `SKILL_NOT_FOUND`, a wrong skill name, on fastapi_14301; one `INVALID_ARGUMENTS`, a rejected argument shape, on requests_7205); row 1 did not fire (A_e 6, mean wall 65.1 s, longest 152.8 s, no caps, stray files or malformed calls). Ad 5 of 8, T 0 of 8 (reference 3), G 0; `load_skill`, `list_skills`, `load_skill_resource` 0. Two tool-free endings (requests_7309, fastapi_14605: 0 calls, 3 nudges, empty patch). Resolves 2 of 8, the same two, not read. 0.281 GPU-h.
- **Why T was 0 [I]:** the picker's root is the constant `/workspace`; in the Kaggle subprocess sandbox the working directory is a per-task temp workspace and `/workspace` is rewritten only inside command strings, so the script saw no files and printed its notice on every call that did not error, well-formed ones included. Inferred from the sandbox source and the pytest rootdir in the traces; the kernel did not print the script's root. The local dry run had laid the workspace out at `/workspace`, so it could not catch this.
- **Lessons:** (1) the harness side of a skill script works on Kaggle: found by its declared name, run through `run_skill_script`, well-formed error replies, no tool-not-found (VERIFY(Q1), skill path). (2) A skill script must find the workspace from its working directory or `PYTHONPATH`, never a constant, and its dry run must use a temp-dir workspace. (3) Our prompt overrode the harness's injected "load the skill first" paragraph, as it asked (0 `load_skill` calls in 8), but the E4B gets the call itself wrong in 4 of 6 calls (a wrong name once, a rejected argument shape once, empty arguments twice), so a prompt that wants the script used must give the exact name and argument shape, and the script must accept both shapes and empty arguments. (4) Tool-free endings were 2 of 8 here and 1 of 8 in EXP-055, against 0 in about 46 earlier E4B traces; with four more tools and the injected paragraph in this tree, a tree effect is not excluded [I].
- **Confidence:** [V] for the counts (EXP-056 section 9.1); [I] for the cause.
- **Outcome (r1):** **row 0, infrastructure: a defect of our build, not a result about the idea.** The loop's rule stops on an infrastructure failure, so **the loop stopped again, 2026-11-08**. r2 runs the identical zip and carries the same defect; it was pushed before r1 was read (the dispatch put the push first) and cannot change the reading. Its analysis, if run, gives a second mechanism sample only (call shapes, skill-name errors, tool-free rate), not a T test. A fixed script is a new tree and a new round, which needs the user's word. Loop spend 1.112 GPU-h with r1, about 1.39 with r2.

## Round 4: EXP-057 (pre-registered a6df3fb, built 2111524, pushed 0093ffa, r1 analysed f6bea23, r2 and pooled a047049)

- **Why:** round 3's test never ran (our picker's fixed root); the user approved round 4 on 2026-11-08 about 21:25 UTC and lifted the two-keep-base stop (`knowledge/user-decisions.md`).
- **Base tree:** EXP-033. **Edit (Candidate F):** the EXP-056 package with the picker fixed: root from `PYTHONPATH` then `sys.path` (the skill wrapper runs the script from a temp dir holding only the skill files, with `PYTHONPATH` naming the workspace; screener, from the sandbox and ADK source), both argument shapes, newest-file fallback on empty arguments, and the exact skill name and call shape in the prompt. Zip `e402d6dd...6362e6`.
- **Readings:** EXP-056's rows and thresholds, with S_x split (script-side errors row 0; model-side M_x counted) and a first-trace check (at least one pick that is not the notice) before T is read.
- **Measured, pooled over 16:** rows 0 to 2 did not fire (S_s 0 over 17 calls, S_p 17 of 17 real picks, A_e 14 of 16, Ad 14 of 16, mean wall 73.8 s, no time caps, one call-cap hit); **row 3 fired: T 8 of 16** (4 in each run; reference 6 of 16), G 1, M_x 0, V1 10 of 16, tool-free 2 of 16. 0.273 + 0.306 = 0.579 GPU-h. Resolves 2 of 16, not read. Blind prediction (T 7 to 10, row 3 or 4) landed.
- **Lessons:** (1) Given the exact name and call shape in the prompt, the E4B makes skill calls without error: M_x 0 of 17, against 4 of 6 in EXP-056 r1 and 1 of 4 in r2. Exact recipes work; implied ones do not. (2) A pick the model receives is not a pick it runs: 3 of 16 printed checks were never run, and once the model's own text claimed a result it had not seen. (3) Running the check is not acting on it: fastapi_14605 got a collection error pointing into a file it had patched, in both runs, and submitted (G 1 in r2, after calling the picker 4 times). The gap from here is acting on the check's output, not choosing or running it. (4) T as pre-registered excludes pytest exit 2, which also drops a check that did find the model's breakage (the two fastapi_14605 cases); a later definition should count an exit 2 whose error points into an edited file. Not applied here (readings are not revised). (5) Tool-free endings follow the skill tree: requests_7309 made 0 calls in all 4 skill-tree runs (EXP-056 r1, r2; EXP-057 r1, r2), against none in about 46 earlier E4B traces on the base trees [I]; declaring a skill (four more tools and the injected paragraph) costs a task its first call.
- **Confidence:** [V] for the counts (EXP-057 sections 9.1, 9.2); [I] for lessons 2 to 5.
- **Outcome:** **row 3, dropped** as written. Two draws over 8 clusters, so T 8 against 6 is inside what the draw moves. Loop spend 1.972 GPU-h with EXP-056 r2 (0.281) and EXP-057 (0.579).

## Addendum 2026-11-08: EXP-059 trace count (zero GPU, 6042bfc) on round 4's lessons 3 and 5

- **Lesson 3, revised:** acting on a failing check is half there, and the larger gap is upstream. Over 72 task-runs in 9 runs, a failing check named a file the model had edited 8 times in the skill trees (3 tasks; 5 on fastapi_14605) and once each in the base references and EXP-055. After those 8, the next action was an edit to the named file 4 times (one rejected), a read or skill call 2, a submit 2; post hoc, 5 of 8 reached an applied edit to the file before the next check or the end. On the base trees 15 of 18 failing checks named only files the model had not edited (collection and setup errors of the test environment, full-suite assertions, a scratch path that does not exist). So on the base trees the check rarely tests the edit at all, and a verifier stage would first need a check that does.
- **Lesson 5, confirmed per task:** requests_7309 made 4 to 7 calls and submitted in all 5 non-skill runs (EXP-033, 038, 045, 052, 055) and made 0 calls with 3 nudges in all 4 skill-tree runs. One task, 9 runs [I].
- **Confidence:** [V] for the counts (hand counts by grep and file reads, EXP-059 section 9); events are few and clustered, no intervals.

## Restart 2026-11-09 under D-008 (user's word about 16:30 UTC)

- **Base tree:** the EXP-062 pipeline. A reader, five tool-less drafters in parallel and an applier under an `LlmAgent` hand-off root. It read row 3, not exercised, with no harm or infrastructure row (e49eb9a). The two-keep-base count resets.
- **Order after the critic's needs-work (experiments/EXP-062/critic.md):**
  - EXP-064, location-diverse drafters (the screener; 380685e, dfa1d47, zip 3b9aea15, push released).
  - EXP-063, a reproducer stage as the applier's selector (the experimenter, being built).
  - The two fused, later.
  - The copy adapter on the applier is parked (D-008 revision).
- **Zero-GPU finding (screener, 2026-11-09), requests_7309 in the skill trees:**
  - **What happens:** in all 4 skill-tree runs the model never makes a native tool call. On each of 4 turns it writes the call as a fenced JSON block in its final text, naming `run_command` or `read_file`. The harness counts that turn as having no tool call and nudges, until the session ends.
  - **Base tree:** in EXP-045 the first turn makes a native `run_command` call.
  - **What differs:** the first-turn prompt is 3,284 tokens in the skill tree against 2,378 in the base, and the skill tree adds the skill tools and the injected protocol. The first-turn reasoning is nearly the same in both; only the output format differs.
  - **Cause:** untested [I]. The cross-run count of text-form calls is dispatched.
  - **Lesson:** the E4B's tool-call format is fragile to a longer system prompt and more tool declarations. A tree that adds tools or protocol text must count text-form calls as a harm signal.
- **Reference fact (EXP-064 section 1):** across the 5 drafts, distinct target files are structurally 1 on every reference task, and some draft targets the gold file on 6 to 7 of 8. So EXP-064 is a screen for diversity and harm, with 1 to 2 tasks of room.

- **EXP-064 (8612b02, §10 1f37a93): row 3, not exercised, 0.353 GPU-h.** The reader listed fewer than 2 locations on 6 of 8.
  - Of those 6, 4 saw one candidate file only and 2 saw several but listed one. The reader was not budget-bound (2 to 11 calls; no task reached its 8 reads).
  - 7 of its 21 `run_command` searches hit one malformed `head` argument (a count detached from its flag), all on L < 2 tasks. Candidate reason, untested.
  - **Lesson:** a mechanism that needs several candidates inherits the search defect. A "list at least 3" prompt would pad with regions of one file on 4 of 6. Any localizer form must fix the search command form first; the graph tools are not the route (C-012: they lose to grep at every k).
  - rich_3468, a movable task, went empty after 6 applier `edit_file` calls, all "old_string not found", none arg-lost. Its failures now include class B.
  - **Tooling:** `analyze_traces.py` counts text-form calls (`n_text_form_calls`, `tool_free`; 2f9de11), cross-checked against EXP-065 over 13 runs.

## Round 5 diagnosis: EXP-067 (zero GPU, c36c64a, a6c09bb), edit failures by stage
- **Cue:** 31 of 57 applier `edit_file` calls failed over EXP-061-r, EXP-062-r and EXP-064-loc. 6 were argument loss.
- **What the count found:** the 31 split as 6 A, 2 S, 11 R1, 8 E, 3 M and 1 O. There are 23 classified failures in 4 task-runs. Drafters never altered a correct REGION (D 0), and the applier never mis-pasted a draft (P 0).
  - R1 (reader mis-copy): 11, all in EXP-064-loc on rich_3468 and fastapi_14605. Lines were skipped, a line was completed, extra indentation was added, and a comma was added.
  - E (stale old_string): 8, only in the same-location trees. After an inconclusive check, the applier went on to drafts 2 to 5, whose OLD the first applied draft had already replaced.
  - S (quote-wrapped `filepath`): 2, in EXP-061-r.
  - M (ambiguous match): 3, a correct block that recurs 8 times in its file.
  - O (applier's own edit): 1.
- **Lesson:** the copy defect sits in the stage that copies from furthest back: the reader, after several reads. When the applier re-read the file, it still pasted the reader's defect (2 of 2), because the defective text was also in its context. So a fresh read helps only where the defective copy is absent.
- **Endpoint with room:** first-edit-applies is 17 of 24, and 6 of 8 on EXP-064-loc. "Tasks with at least 1 applied edit" is 7 of 8 and has no room.
- **Confidence:** [V] for the counts. Drafters seeing the reader's tool results is [I], from one trace.
- **Outcome:** EXP-068 is built on the EXP-064 tree. Each drafter reads its own lines and copies OLD from that result, and the reader gives no REGION.

## EXP-063 v2 (de6848f, 0.401 GPU-h): reproducer stage as the applier's selector
- **Outcome:** row 3, not exercised. W 0, Rf 0 of 8.
- **Cue:** on 8 of 8 tasks the reproducer, which held `read_file`, `run_command`, `get_status` and `write_file`, made 0 tool calls. In the same tree the reader called `run_command` on 8 of 8.
  - On each task the reproducer named its test file, wrote the test body in a python fence, and gave a verdict label: "RESULT: FAILS" on 6.
  - The applier trusted the label and ran the missing file: exit 4, 8 times.
- **Lesson:** an E4B stage that holds tools can answer entirely in text and make up the result of a command it never ran.
  - `n_text_form_calls` does not catch this, because the fenced body is not call-shaped.
  - A tool-holding stage needs a first-turn tool-call row in its readings.
  - A downstream stage must not trust a verdict whose file or command it cannot see.
- **Cause:** untested [I]. The screener desk-checks it under EXP-068: the reproducer's prompt shape and include_contents against the reader's.
- **Confidence:** [V] for the counts; [I] for the cause.

## EXP-066 (7eed5a8, 0.350 GPU-h): the reader's search command form
- **Outcome:** row 6, no decision.
- **Measured:** failed searches 0 of 20 (reference 7 of 21) and pipes 0. `git grep -l` ran 8 times on 5 tasks with no error.
  - L >= 2 on 3 of 8 (reference 2 of 8); by distinct files still 2 of 8.
  - Of the 5 tasks with L < 2, the reader saw several files on 3 and listed one.
  - G 6 of 8, G1 4 of 8. 1 empty patch, mean wall 99.8 s, 0 tool_free tasks.
- **Lesson:** an exact command recipe fixes the command form (as with the skill-call shape in EXP-057). But the reader's single location is its choice, not a search failure, so a diversity mechanism needs a chooser, not better search.
- **Also seen:** fastapi_14448 had 6 failed edits, 4 of them a double-quote-wrapped `filepath` ("Source path not found", EXP-067's class S), and ended with an empty patch. Class S is now 6 edit calls over 2 runs.
- **Confidence:** [V] for the counts.

