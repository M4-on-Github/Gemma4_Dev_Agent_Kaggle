---
id: D-006
title: On the E4B, a team of small single-job agents bounded by their tools, and a tool-call adapter if the harness applies adapters at all
decision: start
status: proposed
track: both
claims: [C-013, C-014, C-023, C-024]
date: 2026-11-06
---

Proposed 2026-11-06 after the user asked (verbatim in `knowledge/user-decisions.md`) for short prompts per sub-agent, an adapter that fixes the tool-call failures we find, the team setup that is fast and correct, and use of the idle GPU. The zero-GPU stage below is running. Every kernel waits for the user's GPU word.

## What are we trying to do?
Find out whether the small model (E4B) resolves more tasks when the work is split into small jobs, each with a short prompt and only the tools that job needs, and whether a narrow adapter can make its edits land. The 31B is not the target: it has about 14 s per task to spare at 8 minutes, the E4B about 225 s.

## How is it done today?
- Both models run one loop with the 3,162-byte v24 prompt. The long prompt lineage (12.8 KB) was retired (C-009).
- E4B, dev-48 (EXP-038): 5 of 48, mean 85.7 s of 480 s. On 8 of 48 tasks no edit ever applied (EXP-043: the old string was a paraphrase or matched more than once). 16 of 19 control losses ran no test or code before submit (EXP-041).
- 31B, dev-48 (EXP-028 Arm R): 9 of 48. 58 of 175 `edit_file` calls were lost (33.1%, 7 tasks); the lost calls arrive with a missing argument, which looks like a fault in the server's tool-call parser, not a model habit [I] (C-004).
- Rules stated only in a prompt are not followed, whatever the prompt's length: 21 of 24 reader branches broke a 5-call limit (EXP-032), the proposer broke its read limit on 3 of 8 tasks (EXP-040), and the E4B paraphrases although v24 says the old string must match exactly (EXP-043).
- Teams measured so far: parallel readers starved the editor on the one shared call counter (EXP-032, untested rather than refuted); 16 voters never changed a pick (EXP-040). The lit-scout's voting note found no positive per-step voting result below about 20B.
- Adapters: the rules allow them (rank up to 128, one per agent) and the organisers' sample ships a tool-call adapter. The host is reported to have acknowledged that the patched server wiped adapters [M]; we never tested it (Q4). The one public same-model adapter, trained on whole task trajectories, lost 10.8 points (C-013).

## What's new in our approach?
1. **Bound each agent by what it is given, not by what it is told.** A reader gets read tools only; an editor gets the file window and the edit tool; a checker gets the run tool. A stage ends because its agent has nothing else it can do, not because a sentence says stop. The harness has one call counter and no per-agent cap, so a stage that can loop will; the desk check must show, per tree, what ends each stage.
2. **Sequential before parallel.** `SequentialAgent[locate, edit, check]` on the E4B is the untested shape. Parallel branches with tools stall each other (EXP-007) and share the counter.
3. **The adapter is narrow and gated.** Target: exact-copy edits on the E4B (C-024). Training pairs can be made without any agent run: a window of a file and an exact, unique substring of it, wrapped as the tool call [I]. No training starts until a canary shows the harness's server applies an adapter.

## Options
- (a) The program below, E4B only. Recommended.
- (b) The same on the 31B: not possible at 8 minutes unless a tree is faster than the single loop; no measurement suggests one is.
- (c) Adapter first: wasted if Q4 comes back "wiped".

## Expected score impact
Unknown, and small on what is counted so far: landing every edit on the 8 tasks is worth about 1 task of 48 at the E4B's rate [I]. Teams have no positive datum below about 20B. The case for the program is the small-model standing and the paper's comparison, not a main-board jump.

## Risks and kill criteria
- Adapter line: killed if the canary shows no output change with an adapter loaded, or if training data cannot be made without competition data leaving the kernel (plan.md:52).
- Team line: a tree is killed at its screen if the editor is reached on fewer than 6 of 8 tasks, or the share of tasks with an applied edit is below the single loop's on the same ids; one fix and one re-run at most.
- The direction is killed if neither line passes its screen; the E4B single loop then stays the small-model tree.
- Time: any tree that adds more than about 225 s per task cannot ship on 120 hidden tasks.
- Attention: the Writeup is due 2026-11-12; this program and the paper share the critic and the lead.

## Cost
| Stage | What | GPU-h | When |
|---|---|---|---|
| 0 | canary build, LoRA costing, sequential-team desk check, lit note, Kaggle digest | 0 | now |
| 1 | adapter canary under the harness's server | about 0.2 to 0.3 | on the user's word |
| 2 | EXP-044 exact-copy line and EXP-045 reproduction before submit (pre-registered, being built) | their cost sections | on the user's word |
| 3 | sequential role team, smoke-8, E4B | about 0.3 to 0.45 | after its desk check |
| 4 | adapter training and one screen of it | not costed yet (experimenter) | only after stage 1 passes |
| 5 | a dev-48 arm of whatever survives | about 1.3 | the user's separate approval |

## Midterm check
By 2026-11-08: the canary result, the two E4B screens and the sequential-team screen are in, each with a critic verdict where one is required.

## Final check
One E4B tree named for the small-model standing with a dev-48 run behind it, or the single loop kept, and the comparison written into the paper whichever way it falls.
