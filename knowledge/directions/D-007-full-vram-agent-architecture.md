---
id: D-007
title: An agent tree that turns the idle L4 memory into concurrent work inside one task, where the extra samples are checked by execution rather than by a vote
decision: start
status: proposed (zero-GPU stage EXP-051 dispatched 2026-11-07; the ranking below is provisional until its numbers land)
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
- **Stage 1, build:** the experimenter builds the top one or two trees EXP-051 leaves open. 0 GPU-h.
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
