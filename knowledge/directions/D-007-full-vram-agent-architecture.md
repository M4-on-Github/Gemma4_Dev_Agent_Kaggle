---
id: D-007
title: An agent tree that turns the idle L4 memory into concurrent work inside one task, where the extra samples are checked by execution rather than by a vote
decision: start
status: proposed (direction open); T2 as built closed 2026-11-08 after EXP-052 (6859aca, row 0, no reading); T1 and T4 closed; T3 not opened; next step is a selector the E4B executes, the user's choice pending
track: both
claims: [C-015, C-020, C-024]
date: 2026-11-07
---

Proposed 2026-11-07 on the user's instruction (verbatim in `knowledge/user-decisions.md`, correction entry): the
full-VRAM direction is open, and the job is to engineer an agent architecture that uses the L4 memory. Only the naive
form, a tool-less vote, is dropped. EXP-049's verified facts are used here as the design envelope, not as a verdict.

## What are we trying to do?
Build an agent tree that issues many model requests at once inside one task, since the GPUs are mostly idle while one
loop runs, so that more tasks end with a patch that applies and passes what the agent can run. The design is E4B
first, because it has the time to spare. The 31B is in scope where parallel work replaces serial turns instead of
adding to them.

## How is it done today?
**The envelope** (EXP-049, harness-stack `reference/serving.md`) [V]:
- **The server.** One vLLM server per scoring run, with tasks run one at a time. Its settings are fixed: tp 4, util
  0.90, 32,768 context, 256 sequences, prefix caching and chunked prefill on.
- **Concurrency.** A submission changes none of the server settings except LoRA sizing. The only route to concurrent
  requests is `ParallelAgent`. Its branches share one call counter, one turn counter, one `/workspace`, the clock,
  and compaction at 14,336 tokens. `agent_tool` runs sequentially.
- **Memory.** KV room at 32k is 45.6 sequences on the E4B and 8.7 on the 31B.
- **Decode is nearly free to widen.** On the 31B, a 256-token burst takes 8.6 s at N 1 and 13.9 s at N 16 [I from
  EXP-049's model], so 16 samples cost about 1.6 times one. Prefix caching means branches that share the actor's
  context pay its prefill once.
- **The budgets are ours.** The 28 calls, 80 turns and 8 minutes are our `eval_config` values. They are bounded only
  by the 12 h run: the gate is 11 h nominal, and the operational rule is 10.5 h on measured time.

**The two loops today:**
- **E4B:** 5 of 48, mean 85.7 s, max 207.3 s, 225.6 s of room per task (EXP-038). On 8 of 48 tasks no edit ever
  applied (EXP-043); the screen had empty patches on 3 of 8 (EXP-046).
- **31B:** 9 of 48, mean about 297 s, 13.8 s of room per task at 8 minutes (EXP-028 Arm R).

**Already tried, and not to be re-proposed:**

| Tried | Result | Source |
|---|---|---|
| Parallel readers on the shared counter | Starved the editor: 21 of 24 broke the limit, 0 of 8 resolved | EXP-032 |
| Same-prompt voters | Never moved a pick | EXP-040 |
| Prompt-bounded sequential roles | Row 2, killed | EXP-046 |
| Exact-copy edit line | Killed by X0 | EXP-044 |
| 31B whole-loop best-of-N | All-arm union minus best was 5 tasks, against a selector bar of +3.0 | EXP-034 |
| Prompt-diverse voter screen | Dropped by the user, 2026-11-07 | `knowledge/user-decisions.md` |

## What's new in our approach?
1. **The extra samples are actions, not opinions.** Each parallel branch produces something the actor can try, such
   as a candidate edit or a patch in its own copy of the repo. What is kept is chosen by execution: whether it
   applies, whether it imports, and whether the reproduction and the visible tests pass. Nothing is chosen by a vote
   or by the model's own judgment. EXP-034 showed that visible tests barely separate right from wrong patches. But
   the E4B's commonest failure is earlier than that, an edit that never lands or a patch that is empty, and a
   mechanical check does separate that.
2. **Parallel work replaces serial turns.** A branch is worth its cost only if it removes turns the single loop would
   otherwise spend in sequence (for the 31B), or if it raises the chance that at least one try lands within time the
   loop leaves idle (for the E4B).
3. **Budgets sized for the tree.** The call and turn caps are raised to fit the branches, so no branch can starve the
   actor. This was the EXP-032 failure. The time profile is then measured, not assumed.

## Options
Candidate trees, provisionally ranked. EXP-051 decides the order and may close any of them.

| # | Tree | Model | Concurrency used | Selector | Opens if (EXP-051) | Kill rule |
|---|---|---|---|---|---|---|
| **T1** | **Isolated parallel attempts with an execution gate.** K = 3 full single loops, each in its own copy of the repo. A final agent with tools checks each copy (patch non-empty, applies to `/workspace`, reproduction and visible tests run) and applies the first that passes, then submits | E4B | K full loops, decode batched | Mechanical first; the actor picks among the passes | Q4a: tools reach paths outside `/workspace`, or Q4b: copies inside it stay out of the diff. Q3: the E4B union over runs exceeds a single run by at least 3 of 48 | Structurally closed by Q4a/b. On smoke-8: no more tasks with a non-empty applied patch than the single loop, or mean wall above 240 s |
| **T2** | **Draft fan-out at the edit point.** Once the actor has read the target, a `ParallelAgent` of K = 4 to 8 tool-less drafters, sharing the actor's cached context and given different framings, each writes one exact candidate edit. The actor tries them in order with `edit_file`, running the reproduction after each, until one applies and passes | E4B first; 31B if the numbers allow | K drafts at about one burst's wall | Applies, then reproduction | Q1: E4B tasks that never land an edit are a large share of failures. Q4d: branches can carry their own instruction | On smoke-8: edit-applied tasks not above the single loop, or the tree hands control back badly (turn or restart blow-up) |
| **T3** | **Read fan-out replacing serial exploration.** The actor names the files it wants; a `ParallelAgent` of single-file readers returns one short summary each | 31B (E4B possible) | K reads at once | None; the actor merges | Q2: the 31B spends at least 4 serial pre-edit turns, more than a third of its wall, on reads whose targets are known after its first look | EXP-032's starvation recurs even with raised caps; or wall per task does not fall |
| T4 | **Two models:** the 31B as actor, E4B branches as drafters or readers | Both | E4B branches | As T2 | Q4c says one tree may name two base models (expected no) | Closed by Q4c |

## Ranking after EXP-051 (2026-11-07; the opening rules in the table above are applied as written, not revised)
Evidence: EXP-051 (cec0b47), zero GPU. Its header says the numbers were computed before its file was committed, so its section 4 is not a blind reading. The opening rules here were committed first (d9dcb29), before the lead saw any number.

| # | Rule | EXP-051 answer | Verdict |
|---|---|---|---|
| T1 | Q3: E4B union at least a single run + 3 of 48; Q4a/b: a private tree is reachable | Union 5, single run 5, so +0. The failed-edit-8 ids are 0 of 3 runs, the six unresolved smoke-8 ids 0 of 4. A private tree exists only through `run_command`, and `submit_patch` diffs `/workspace` only | **Closed** by its own rule |
| T2 | Q1: no-edit tasks a large share of E4B failures; Q4d: branches carry their own instruction | Q4d yes (`schema.py:277-293`). No E4B task ended at a cap; `edit_file` holds 49.3% of E4B wall in forensics (model time included). 8 of 48 never landed an edit (EXP-043) | **Open.** Weak prior, below |
| T3 | Q2: at least 4 serial pre-edit turns and more than a third of 31B wall | Only a turn proxy (about 47% of turns before the first edit); wall before the first edit could not be computed. Every swegemma tool is a plain sync function (`workspace.py`, `execution.py`), and a sync tool in one branch stalls its siblings (EXP-007 H3, stall fraction 0.78). No per-branch budget (Q4e) on a counter the 31B hits on 37.5% of tasks | **Not opened.** The pre-edit profile the screener asked for is not commissioned unless T3 is reopened |
| T4 | Q4c: one tree may name two base models | README says one base model per submission [M; enforcing code not on disk] | **Closed.** Adapters on one base remain, which is the canary's question |

**T2's prior, stated plainly.** The one earlier attack on T2's target set, EXP-044 on the failed-edit-8, resolved 0, and those 8 tasks are 0 of 3 across every run on record. Q3 says repeated E4B attempts have added no task. What favours T2 is narrower: edit retries take the largest share of E4B wall across many tasks, not only the 8, and a tool-less drafter costs no tool call. P(T2 lifts the small-model line by 2 or more of 58) is lowered from about 0.3 to about 0.15 [I].

**Correction 2026-11-07, after EXP-052 was built (c66d68a): T2's target is smaller than this ranking said.** The ranking cited "8 of 48 never landed an edit (EXP-043)" as the failure T2 fixes. EXP-044's control arm X0, the unchanged EXP-038 zip re-run on those 8 ids, applied an edit on 7 of 8 (EXP-044 section 9.1), so that 0 of 8 was one draw, not a lasting failure. On smoke-8 the single loop applied an edit on 8 of 8 (EXP-038) and 6 of 8 (EXP-033). So EXP-052 can show only that T2 is not worse at landing edits, which its row 2 floor of 7 of 8 against EXP-033's 6 of 8 states. It cannot show a gain. The E4B's failures are mostly edits that land but are wrong, which a mechanical check does not catch (EXP-034). P(T2 lifts the small-model line by 2 or more of 58) is lowered again, to about 0.1 [I]. EXP-052 is now a feasibility screen of the tree's control flow, time and draft selection, not a test of the lever.

**Correction to the T2 row.** "K drafts at about one burst's wall" assumed a shared prefix. Each drafter's `instruction` is the system prompt at the front of its request, so different framings there break the prefix for the roughly 7,170 tokens behind it, and each drafter pays its own prefill. On the E4B, with 225.6 s of room per task, this does not block; EXP-052 measures it. Drafters hold no tools, so they draw turns (cap 80, E4B mean 12.5, p90 20), not calls. K is sized against turns.

**Correction 2026-11-08, after EXP-052 ran (6859aca, 0.309 GPU-h): T2 as built is closed; the direction is not.** Row 0 fired as written (a non-empty `err` on httpx_3672), so the screen has no reading and nothing moves on it. The cause is the tree, not Kaggle: the applier ended in text with no tool call after a prompt of 16,805 tokens (the report and drafts arrive by instruction and by events both), and the post-invocation compaction path hands the root agent, here a `SequentialAgent`, to the summarizer, which raises for a non-`LlmAgent` (EXP-052 section 9.1, source read by the screener). So row 0's "fix and re-run" is not a free re-run: every fix (an `LlmAgent` root, one channel for the drafts, an enforced check) changes the control flow EXP-052 section 2.1 described, and is a new claim and a new EXP number. Described, not read: on the 7 tasks that ended on `submit_patch` the tree ran in order with no restart, mean wall 82.5 s over all 8 against EXP-038's 78.3 s on the same ids, so five concurrent drafters cost the E4B a few seconds; but no applier ran a python interpreter (C would be 0 of 8 by program name; pytest 4 runs), so the selector was in practice "the first draft that applies"; 3 of 11 `edit_file` calls failed; and the two resolves (fastapi_14301, rich_3006) are the two smoke-8 ids every E4B tree resolves about 3 runs in 4. The concurrency is cheap; what it buys needs a selector the E4B actually executes, which three unenforced screens (EXP-033, EXP-038, EXP-052) did not show. **Harness hazard, [I] until the experimenter confirms it from source:** a tree whose root is not an `LlmAgent` ends a task with an error, not a nudge, when its last stage ends in text with a prompt at or above 14,336 tokens; a `submit_patch` ending is believed to break the loop before that path runs. If confirmed, it binds every tree in this direction and goes into harness-stack.

**2026-11-08, hazard confirmed [V]** (experimenter, 0a60173; harness-stack `reference/compaction.md`, ADK 1.36.1, swegemma 0.2.11). The summarizer error arises only on the end-of-invocation path, with a root that is not an `LlmAgent`, a prompt at or above 14,336 tokens, no in-flow compaction and no cached summarizer; the summarizer is cached on the shared config, so the hazard depends on order. `submit_patch` only sets a flag and the harness stops at the first final text after it, so submit-then-text is safe. Safe shapes: an `LlmAgent` root; an `agent_tool` subtree (its own Runner, never compacted); a `ParallelAgent` reached by transfer under an `LlmAgent` root [I]. A summarizer cannot be set in yaml.

**Build gates for EXP-052** (0 GPU-h; each is checked on the one-task trace inside the smoke-8 kernel):
1. **The shape is named in the pre-registration with source file:line.** Candidate S is `SequentialAgent[reader, ParallelAgent(K drafters), applier]`, where the applier sees the drafts through shared session events or state. Candidate A is the single loop with one `agent_tool` wrapping the `ParallelAgent`; that runs in a fresh session (harness-stack `reference/serving.md:26`) and returns one output, so K-1 drafts are lost unless state carries them back. The trace must show all K drafts reaching the applier and no tree re-run after the submit.
2. **EXP-046's kill applies to the reader.** Only the model ends a tool-holding stage, and EXP-046's locate skipped its reads on 5 of 8. The reader's prompt is written with that failure in front of it.
3. **The caps are sized for the tree** and stated before the push, so no stage can starve the applier (EXP-032).
4. **The process endpoint** is per task: `edit_file` attempts, successful `edit_file` calls, and a non-empty applied patch. It is read against EXP-038's traces on the same 8 ids. Resolves are reported, but n = 8 decides nothing about them.
5. **The time kill** stays as written: an E4B mean wall above 240 s kills the upload without a dev-48.

The canary (EXP-047, running on the user's word) bears on every tree. An adapter cuts the KV pool these trees need,
and reading B measures by how much.

## Expected score impact
- **Main track.** By EXP-049 R5, an E4B tree must beat the E4B single loop by about 8 tasks of 48 to displace the 31B.
  P is low, under 0.15 [I], until T1 or T2 shows a process effect on smoke-8.
- **Small-model bonus line.** Any gain counts directly against an E4B baseline now on the board (S-014, pending).
  P(at least 2 tasks of 58 over S-014) is about 0.3 [I], resting on the E4B's no-edit and empty-patch failures being
  the part a mechanical gate fixes.
- **Paper track.** A measured statement either way, on whether batched concurrency inside one task buys resolves on
  a fixed scorer.

## Risks and kill criteria
- **Structure.** One `/workspace` and one diff may make T1 impossible (Q4a/b), and two models are probably not served
  (Q4c). Both are read from source before any GPU.
- **Control flow.** A tree that ends a stage in text re-runs or stalls (EXP-049: a `LoopAgent` pass that ends in text
  re-runs the tree). Each tree is first validated and traced on one task inside its smoke-8 kernel, not on its own.
- **Time.** K loops share the 8-minute clock. A smoke-8 whose mean wall passes 240 s on the E4B is killed for upload
  without a dev-48.
- **Selection power.** The gate fixes "nothing landed", not "landed but wrong" (EXP-034). If EXP-051 Q3 shows the
  E4B's union barely exceeds one run, T1 is closed.

## Cost
- **Stage 0, EXP-051** (screener): 0 GPU-h. Running.
- **Stage 1, build:** ~~the experimenter builds the top one or two trees EXP-051 leaves open~~ **Corrected 2026-11-07: only T2 is left open; the screener builds it as EXP-052, since a smoke-8 is its level.** 0 GPU-h.
- **Stage 2, smoke-8 per tree on the E4B:** about 0.3 to 0.5 GPU-h each (EXP-040 0.315, EXP-046 0.293).
  This needs the user's GPU word.
- **Stage 3, dev-48 on the E4B:** about 1.2 to 1.6 GPU-h, only for a tree that passes its smoke-8. Needs the user's
  word, as a dev-48 arm always does.
- **Stage 4, upload** through an S-NNN the user approves by sha (plan.md 5.8).
- **Whole direction:** about 2 to 4 GPU-h for two trees through dev-48, against 30 per week.

## Midterm check
After EXP-051 and the first smoke-8: did the gate raise the number of tasks with a non-empty applied patch above the
single loop's on the same 8? If no tree moves that process count, stop.

## Final check
A dev-48 E4B arm at or above the single loop + 3 tasks with a measured time profile inside 10.5 h. That earns an
upload on the small-model line. An arm at +8 or more would reopen the main-track model choice.
