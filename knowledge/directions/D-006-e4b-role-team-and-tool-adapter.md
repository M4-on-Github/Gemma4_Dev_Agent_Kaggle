---
id: D-006
title: On the E4B, a team of small single-job agents bounded by their tools, and a tool-call adapter if the harness applies adapters at all
decision: start
status: proposed
track: both
claims: [C-013, C-014, C-023, C-024]
date: 2026-11-06
---

Proposed 2026-11-06 after the user asked (verbatim in `knowledge/user-decisions.md`) for short prompts per sub-agent, an adapter that fixes the tool-call failures we find, the team setup that is fast and correct, and use of the idle GPU. The zero-GPU stage below is running. Every kernel waits for the user's GPU word (items 1, 2 and 4 approved 2026-11-06). Critic direction review 2026-11-06 (filed in `experiments/EXP-043/critic.md`, 19a8b20, 5ab7020): needs-work on text and two kill criteria; stage order and E4B-only scope right. The critic's replacement text is applied below.

## What are we trying to do?
Find out whether the small model (E4B) resolves more tasks when the work is split into small jobs, each with a short prompt and only the tools that job needs, and whether a narrow adapter can make its edits land. The 31B is not the target: it has about 14 s per task to spare at 8 minutes, the E4B about 225 s.

## How is it done today?
- Both models run one loop with the 3,162-byte v24 prompt. The long prompt lineage (12.8 KB) was retired (C-009).
- E4B, dev-48 (EXP-038): 5 of 48, mean 85.7 s of 480 s. On 8 of 48 tasks no edit ever applied (EXP-043, 39 failed calls: 16 paraphrases, 6 of them past the last line read; 11 exact copies matching more than once; 6 lost or malformed arguments, all 4 of rich_3935's; 5 single-line misquotes; 1 escaping). 16 of the 19 tasks neither arm resolved on the informative 27 ran no test or code before submit (EXP-041).
- 31B, dev-48 (EXP-028 Arm R): 9 of 48. 58 of 175 `edit_file` calls were lost (33.1%, 7 tasks); the loss has one shape, a missing argument from the server's tool-call parser, but its rate depends on what the model emits: the E4B lost 9 of 156 on the same server (EXP-038), and the 31B 53.5% at thinking 256 against 18.2% at 4096 (EXP-024) [I] (C-004).
- Rules stated only in a prompt are not reliably followed (prompt length was never varied): 21 of 24 reader branches broke a 5-call limit (EXP-032), the proposer broke its read limit on 3 of 8 tasks (EXP-040), and the E4B paraphrases although v24 says the old string must match exactly (EXP-043).
- Teams measured so far: parallel readers starved the editor on the one shared call counter (EXP-032, untested rather than refuted); 16 voters never changed a pick (EXP-040). The lit-scout's voting note found no positive per-step voting result below about 20B.
- Adapters: the rules allow them (rank up to 128, one per agent) and the organisers' sample ships a tool-call adapter. The host is reported to have acknowledged that the patched server wiped adapters [M]; we never tested it (Q4). The one public adapter with a measured effect is the rank-3 team's, on the 31B, trained on whole task trajectories: -10.8 points locally (C-013). A public E4B notebook with a declared adapter self-reports 0.03 to 0.06 on the LB [M], inside the 4-task MDE, with no no-adapter control. Topic 755677: the one scored adapter run a participant reports equals its baseline, so it shows the adapter loads, not that it changes output [M].

## What's new in our approach?
1. **Bound each agent by what it is given, not by what it is told.** A reader gets read tools only; an editor gets the file window and the edit tool; a checker gets the run tool. A stage ends because its agent has nothing else it can do, not because a sentence says stop. The harness has one call counter and no per-agent cap, so a stage that can loop will; the desk check must show, per tree, what ends each stage. (2026-11-06, EXP-046: it cannot. Only the model ends a stage that holds a tool; there is no exit tool, no per-stage cap, and callbacks are not wired. The tool split itself works, but call counts stay prompt-bounded. Team line killed at its desk check as the kill criterion below states; it reopens only if the harness gains a per-agent cap, an exit tool or working callbacks.)
2. **Sequential before parallel.** `SequentialAgent[locate, edit, check]` on the E4B is the untested shape. Parallel branches with tools stall each other (EXP-007) and share the counter.
3. **The adapter is narrow and gated.** Target: exact-copy edits on the E4B (C-024). Training pairs can be made without any agent run: a window of a file and an exact, unique substring of it, wrapped as the tool call [I]. No training starts until a canary shows the harness's server applies an adapter.

## Options
- (a) The program below, E4B only. Recommended.
- (b) The same on the 31B: not possible at 8 minutes unless a tree is faster than the single loop; no measurement suggests one is.
- (c) Adapter first: wasted if Q4 comes back "wiped".
- (d) Missed in the first draft (critic): an editor sub-agent at low temperature, or a retry route that avoids `edit_file`. Neither needs training or Q4. Not designed yet.

## Expected score impact
Unknown, and small on what is counted so far: landing every edit on the 8 tasks is worth at most about 1 task of 48, probably less (3 of the 8 are gated, about 3 fail the way the adapter targets, and the 31B resolved none of the 8) [I]; the endpoint has to be the applied-edit share. Teams have no positive datum below about 20B. The case for the program is the small-model standing and the paper's comparison, not a main-board jump.

## Risks and kill criteria
- Adapter line: killed unless the server lists the adapter and answers under its name, and at temperature 0 the outputs with and without an adapter built to have a large effect differ by more than two no-adapter runs do; a Kaggle-notebook pass tests that server, not the scorer's (the harness maps an adapter name to the base model with no error unless the server is vLLM with LoRA enabled [V, critic]; a participant reported no output change after the host's fix, 743508, 2026-10-08 [M]). Also killed if the KV cache with an adapter loaded falls below what the single loop needs (7,600 tokens reported at notebook defaults against 46,048 without and our 14,336-token compaction threshold [M]; added 2026-11-06 from the adapter digest), or if training data cannot be made without competition data leaving the kernel (plan.md:52).
- Team line: a tree is killed at its screen if the editor starts with at least k calls and s seconds left on fewer than 6 of 8 tasks, if fewer than N of 8 end with an applied edit (the single loop: 8 of 8 on smoke-8), or if its mean wall is above about 311 s; k, s, N and the pass row are written before the screen; one fix and one re-run at most. (Replaced 2026-11-06 with the critic's text; the first draft compared with the single loop's 8 of 8, which leaves no room on smoke-8.)
- The direction is killed if neither line passes its screen; the E4B single loop then stays the small-model tree.
- Time: a tree ships on 120 hidden tasks only if its own measured dev-48 mean wall is about 311 s or less (10.5 h less the 0.12 h kernel overhead, over 120), about 225 s above the single loop; a smoke-8 mean does not count (the same 8 ids gave 56.9 s and 78.3 s).
- Attention: the Writeup is due 2026-11-12; this program and the paper share the critic and the lead.

## Cost
| Stage | What | GPU-h | When |
|---|---|---|---|
| 0 | canary build, LoRA costing, sequential-team desk check, lit note, Kaggle digest | 0 | now |
| 1 | adapter canary under the harness's server | about 0.2 to 0.3 | on the user's word |
| 2 | EXP-044 exact-copy line and EXP-045 reproduction before submit (pre-registered, being built) | their cost sections | on the user's word |
| 3 | sequential role team, smoke-8, E4B | 0.30 to 0.43 | killed at its desk check (EXP-046); only on the user's explicit ask |
| 4 | adapter training and one screen of it | not costed yet (experimenter) | only after stage 1 passes |
| 5 | a dev-48 arm of whatever survives | about 1.3 | the user's separate approval |

## Midterm check
By 2026-11-08: the canary result, the two E4B screens and the sequential-team screen are in, each with a critic verdict where one is required.

## Final check
One E4B tree named for the small-model standing with a dev-48 run behind it, or the single loop kept, and the comparison written into the paper whichever way it falls.
