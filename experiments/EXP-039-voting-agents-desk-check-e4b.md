# EXP-039 — Voting agents on the E4B (C-023): is it expressible, does it terminate, what bounds N, and which one design is worth a smoke-8 screen

**Date:** 2026-11-05
**Type:** zero-GPU desk check (L0) plus a validator probe of one candidate tree. No kernel, no upload, no zip, no notebook, 0.0 L4x4-h.
**Cohort:** none run. The recommended screen, if the user approves its GPU, is smoke-8 on the E4B, paired against EXP-033.
**Ladder:** L0. The screen is not pre-registered here and is not built (the user has not approved its GPU; the D-004 ceiling has about 0.3 GPU-h left after EXP-038).
**Serves:** C-023 (hypothesis, D-005), user decision 2026-11-05 about 17:30 UTC (voting agents "with varying temps", deterministic tie rule, "maximum allowed agents" on the E4B).
**Relates:** EXP-033 (E4B single loop, smoke-8: the reference arm and the cost numbers), EXP-038 (E4B dev-48, the experimenter's; not touched), EXP-032 (P1: a prompt-only call limit did not hold; ParallelAgent in the real harness), EXP-006 (concurrency X(N)), EXP-007 (ParallelAgent overlap), D-004 bounds B3 and B5, `research/lit/lit-2026-11-05-architecture-families.md`.
**Tags:** [V] verified in source or measured here, [M] community or mirror, [I] inference.

The probe tree is `experiments/EXP-039/probe/` (4 voters standing in for N). It is a validator probe, not a candidate: it has not been packed, and its prompts are placeholders, not the prompts a screen would carry.

## 1. Why this, now

The user asked for agents that vote on the best next move, with varying temperatures, a deterministic tie rule, and on the E4B as many as are allowed. The E4B is the only model with room for extra calls: mean spare time under the 480 s cap is 423 s per task and the minimum 389 s, 6.0 s per model turn, 0 of 8 capped (EXP-033 section 9, [V]). The 31B has 13.8 s per task of headroom at 8 minutes (D-004), so a single vote point at N = 16 costs about 33 s per task there [I] and does not fit. This note answers the seven desk questions from the harness source and the traces on disk, names the one design that is both expressible and enforceable, and states what a screen could decide.

## 2. The seven questions

### Q1. Is it expressible? Yes for one vote point, and only weakly for per-step voting. [V] and [I]

- A declarative config can hold `SequentialAgent`, `ParallelAgent`, `LoopAgent` and `LlmAgent` (`tools/submission_rules.py:42-92`; `data/raw/HARNESS_README.md:104-152`). Each `LlmAgent` has its own `generate_content_config`, so each voter has its own temperature (`adk_submission/schema.py`, LlmAgent keys; `generate_content_config`, `include_contents`, `output_key` are allowed keys) [V].
- Voters with `tools: []` are legal. The official schema has `tools` optional (`schema.py:287`); our lint warns when the key is absent, and an explicit empty list clears the warning (probe run, section 6) [V].
- A voter reads the proposer's list through `output_key` and `{cands?}` templating, and the actor reads `{vote_k?}`. With `include_contents: none` a voter sees none of the history, so it cannot be steered by a sibling [V] (`flows/llm_flows/contents.py:748-763`, branch filter; ParallelAgent children get branch `parent.child`).
- The tally and the tie rule cannot be code. They are sentences in the actor's prompt. The actor is a 4B-class model counting letters, so fidelity is a measured quantity (section 5, F3), recomputed offline from the vote texts the trace records [I].
- Per-step voting needs `LoopAgent[proposer, ParallelAgent[voters], actor]`. It is expressible, but the loop exits only on an escalate event or `max_iterations` (`google/adk/agents/loop_agent.py`), the harness registry has no exit tool (`swegemma/tools/__init__.py`: nine tools, none is `exit_loop`), and the only clean exit is the actor's `submit_patch`, which ends the session (`agent_runner.py:854-864`, text-only final event with `patch_submitted`) [V]. "One executed call per round" is then a prompt-only rule, and EXP-032 P1 measured that such a rule does not hold: 21 of 24 localizers ignored a 5-call limit (EXP-032 section 9, row e) [V]. Per-step voting is therefore not the first design.

### Q2. Does it terminate? Yes, by the harness, not by the tree. [V]

The harness outer loop (`agent_runner.py:788-1019`) breaks on `patch_submitted`, the tool-call cap, the clock (`asyncio.timeout` 480 s), the turn cap, or an error. After a pass without `submit_patch` it nudges and re-invokes the whole root tree, up to 3 consecutive nudges without a tool call, so a V1 pass that ends in text re-runs the proposer, the voters and the actor. That restart is a cost, not a hang: it burns clock, and in EXP-033 the 8 traces hold 24 text-only turns out of 76, at least 16 of them ending a pass before submit (counted from the traces for this note) [V]. A `LoopAgent` is capped at `max_iterations` at most 500 (`submission_rules.py` `MAX_LOOP_ITERATIONS`; `compile_loop_agent` rejects more) [V]. The turn cap counts every non-partial model event of every agent, voters included (`context.py:277-299`), and `check_budget` stops the task with "Turn budget exhausted" (`context.py:485-497`) [V]. EXP-033's `eval_config.yaml` has `max_turns: 80`, which a voting arm must raise (limit 500; the probe uses 200) [V].

### Q3. One move per round? Yes for V1 by construction, no for the per-step loop. [V] and [I]

V1 makes exactly one vote per task, then one actor pass. Every call-bearing step in the 8 EXP-033 traces carries exactly one tool call (52 steps: 43 counted calls plus 9 `submit_patch`) [V, grep of the traces]. The shared tool-call counter is not a risk for voters, who have none; it is spent only by the proposer's reads and the actor's calls, against the 28-call cap [V] (D-004 B3). The per-step loop gives no such guarantee (Q1).

### Q4. The vote format. One line, a letter from a short list.

- The proposer ends with at most four lettered candidates A to D, one file and one change each (the E4B writes a first plan in prose; the cap keeps the list short).
- A voter replies exactly `PICK: X`, `max_output_tokens` 256, `thinking_budget` 0 (unverified on the E4B template, F7).
- Temperatures by voter: spread over 0.2 to 1.4 in equal steps, voter 1 lowest (probe: 0.2, 0.6, 1.0, 1.4). The harness allows any temperature the validator passes (`submission_rules.py` generation fields) [V].
- **Tie rule (one, checkable).** The winner is the letter with the most `PICK` lines. If two or more letters tie for most, the winner is the tied letter picked by the lowest-numbered voter. Voter 1 is the lowest temperature, so a tie falls to the most deterministic voter. A recompute needs only the N vote texts and is a pure function of them. A malformed vote counts for nothing.
- Why one rule: with N = 16 and four letters, ties among the top letters are plausible; the rule decides every one, it uses no information the actor does not already have, and it can be re-computed offline.

### Q5. The bound on N. [V] for the limits, [I] for the throughput

| Quantity | Formula | Value |
|---|---|---|
| Schema limit | `MAX_AGENTS` | 500 agents (`limits.py:191`, `swegemma/config.py:52`, `HARNESS_README.md:140`, enforced `compiler.py:226`, mirrored `submission_rules.py:90`). Not the intended reading of "maximum allowed" (user decision: clock- and memory-bound). |
| Turn cap | turns = proposer + N + actor turns; per-step: M x (N + 2) | single vote point: N + about 20 per task, so N <= about 480 under a 500 cap. Per-step: M is the call count, 9.5 turns per task in EXP-033, so N <= about 48. |
| Memory | N x L <= KV tokens | KV room 45.63 x 32,768 = 1,495,000 tokens (EXP-006). With L = 3k a vote prompt, N <= about 490. Never binding. |
| Clock | vote wall V(N) = t_v x N / X(N) | X(4) = 3.47, X(16) = 9.45 (EXP-006, measured with 256-token outputs on short prompts, so under real prefills it is extrapolated; above 16 it is unmeasured). t_v about 3 s for a 3k prompt and a 40-token reply gives V(16) about 5 s and V(100) about 20-30 s if X plateaus (about 15), dominated by prefill. |
| **N_max, single vote point** | min(turn, KV, clock) | **about 100** [I], unmeasured above 16. |
| **N_max, per-step voting** | M x V(N) fits the spare 423 s with margin | **about 16 on measured X, about 45-50 if X plateaus** [I]; and the 4.7x wall below. |

Per-step cost at N = 16: about 4.7 x the 57 s single loop, so about 268 s per task, inside the 480 s cap with 200 s of margin only if the one-call rule held, which Q1 says it does not.

### Q6. What the lit review says. [M], no new search

`research/lit/lit-2026-11-05-architecture-families.md` is not encouraging for this claim at its natural reading, and it does not test the claim's real shape. Majority voting over patches gave no gain over the first candidate in the two places it is isolated (lines 23, 32; Agentless, Nemotron) and ties at N <= 3; a same-model judge helps only after executed test results (lines 24, 35); the only selection gains are with executed tests (line 22, 70). Same-model sampling and voting works for function-level code at N = 40 and not for patch voting at small N (line 54), and debate lost to self-consistency at equal responses (line 50). Candidate generation by temperature is what the sources use, and none ablates prompt or format diversity (lines 37, 84). In its favour: oracle minus average is 8.7 points at N = 3 (line 38), so the ceiling is real, and the small-model row (line 28) says a fixed workflow beats a free loop for sub-10B models. The lit-scout's rule for D2 is "never use majority vote" because it ties at N <= 3; V1 at N = 16 mostly avoids ties but carries no executed signal, which is the part the lit says matters. **Gaps for the lit-scout:** (1) action-level or per-step voting in a repository task with a shared mutable workspace: no source found; (2) a vote by the same model on an enumerated option list rather than on full candidates, and its agreement rate with the model's own greedy pick; (3) temperature-spread voters against prompt-diverse voters; (4) a small-model (4B to 8B) result for N = 8 to 32 votes on a short option list. None is needed before a smoke-8; (2) is the one that predicts whether the vote can change anything.

### Q7. Failure modes that would make a GPU screen empty

| # | Failure | Why it empties the screen | Zero-GPU check available now | Check after the screen (from the traces) |
|---|---|---|---|---|
| F1 | Proposer writes fewer than 2 distinct candidates | the vote has one option; every voter agrees | none: the E4B's candidate lists are not on disk; the first-edit pattern in EXP-033 shows one plan per task, which is weak evidence this fires | count tasks with at least 2 distinct lettered candidates |
| F2 | Voters agree: the same-model, same-context vote returns the one letter for all N | no change vs voter 1 | none; the lit has no agreement rate (Q6 gap 2) | D, the number of tasks where the winner differs from voter 1's pick |
| F3 | Actor does not apply the tally or the tie rule | the vote is decorative | none | recompute tally and tie rule from the N `PICK` lines; compare with the first edited file and hunk |
| F4 | Turn cap `max_turns` 80 ends the task | voters count as turns (`context.py:277-299`) | done: V1 needs about N + 26 = 42 turns at N = 16 on EXP-033's 9.5 per task, under 80 but the nudge restarts repeat the vote; the probe sets 200 | max turns per task, stop reasons |
| F5 | `thinking_budget: 0` or `include_thoughts: false` is not honoured by the E4B template or vLLM | empty or long voter replies; 256 tokens truncates | the validator passes the values; the template is not on disk | share of voter replies that parse |
| F6 | Compaction or ADK issue 7324 in the parallel stage | `ValueError` kills the pass | low: the parallel stage holds only text events (no function call or response in flight), prompts about 3k against the 14,336 threshold; EXP-032 P1 ran 3 parallel branches with 0 crashes [V] | compactions, crash count |
| F7 | Nudge restarts re-run the whole tree (corrected after commit, section 7 item 8: the 3-nudge limit does not bound this) | a second vote, a second proposer pass, repeated up to the call cap | EXP-033: at least 16 of 24 text-only turns ended a pass; the trace does not tag nudges (not found as `continuation_nudge`), so no count is claimed | passes per task from the first-call prompt sizes |
| F8 | Actor with `include_contents: none` re-reads the repository | spends the 28-call cap | the EXP-032 editor did this; its remedy was a list of the proposer's paths | capped count, calls in the actor |
| F9 | `submit_patch` from a sub-agent | lint warns it can end the session inside a sub-call | same as EXP-032's editor, accepted there [V] | patch non-empty and graded |
| F10 | n = 8 cannot show a resolve effect | the baseline is 2 of 8 | by construction | resolves are recorded, never read |
| F11 (added after commit, section 7 item 7) | With `include_contents: none` a voter and the actor never see the task message | the window starts at the latest user event or other-agent reply (`contents.py:569-580`); for a voter that is the proposer's final text, for the actor the last voter's text, so "the issue in the task message" points at nothing and F1 to F3 fire for an infrastructure reason; a nudge restart also resets the proposer's window to the nudge text | done: read of `contents.py:542-582` and `71-86` | the voter prompt in the trace, whether the issue appears |

## 3. The design to screen (V1), and why not the others

**V1: `SequentialAgent[proposer, ParallelAgent[voter_1 .. voter_N], actor]`, all on the E4B.**
- Proposer: read-only tools (`read_file`, `get_status`), at most six reads, ends with an `ISSUE:` line (at most 120 words) and then at most four lettered candidates, `output_key: cands` (the `ISSUE:` line was added after commit, section 7 item 7: voters with `include_contents: none` never see the task message otherwise). The actor runs on default `include_contents` for the same reason.
- Voters: `tools: []`, `include_contents: none`, identical instruction, temperature 0.2 to 1.4 in equal steps, `max_output_tokens` 256, `thinking_budget` 0, each `output_key: vote_k`.
- Actor: the full tool set, reads the N votes through `{vote_k?}`, tallies with the tie rule of Q4, applies the winner, checks once, calls `submit_patch`.
- `eval_config`: 240 / 28 / 8 min with `max_turns` raised to 200.

**N for the first screen: 16.** It is the largest N with a measured X (9.45). The user's "maximum allowed" is about 100 for a single vote point [I], but nothing above 16 has been measured under real prefills. Scaling to the bound is a second arm after a one-call concurrency probe at real prompt sizes (a decode-bound burst test overstates X; EXP-006). The user decision of 2026-11-05 about 17:30 UTC reads "maximum" as that bound, so the user should see that the first screen is at 16 and why.

**Not recommended first:** per-step voting (`LoopAgent`). Expressible but the one-call-per-round rule is unenforceable (EXP-032 P1: 21 of 24), it costs about 4.7 x the single loop in wall, and at 160 turns per task it hits any cap below 200. **Not recommended at all:** voting on the 31B (about 33 s per task against 13.8 s of headroom).

**Probe result.** `experiments/EXP-039/probe/` (Sequential, a `vote` ParallelAgent with 4 voters, proposer, actor; 8 agents) validates structurally with `tools/validate_submission.py --strict`. The two remaining diagnostics are the packing-gate error (120 x 9 min = 18.00 h, so a screen needs `--skip-budget-gate`, as EXP-032 did) and two warnings carried by the EXP-032 P1 tree (sub-agent with `submit_patch`; timeout 240). The official validator wheels are not importable here, so `--official` did not run. The 4-voter tree is a structural probe: the schema count limit is 500.

## 4. Pre-registered readings for the recommended screen (written blind, not revised after the numbers land)

These apply to a V1 smoke-8 on the E4B if the user approves its GPU and the lead dispatches it. They are written here so a screen cannot reread them after the fact; the screen's own EXP file copies them. Order is first match.

Quantities per task, from the traces: C = distinct lettered candidates in the proposer's text; the vote texts of the N voters (the trace records each author); W = the winning letter by the Q4 rule recomputed offline; P1 = voter 1's pick; D = the number of tasks (of 8) with W different from P1; A = the number of tasks where the first edit's file and hunk match the candidate W (hand check of 8); wall, capped count, malformed.

| Row | Condition | Reading |
|---|---|---|
| 0 | infrastructure: a crash in more than 2 of 8, or fewer than 6 of 8 tasks with at least 12 of 16 parseable votes, or the tree does not run | fix the one cause (for example F5) and re-run once; no reading |
| 1 | C >= 2 in fewer than 6 of 8 tasks | the proposer yields no real alternatives; kill V1 as specified and send the gap (Q6, 2) to the lit-scout; the claim is not killed, its candidate source is |
| 2 | D = 0 of 8 | the vote never changed a pick: kill V1 as specified (at N = 16 the voters and voter 1 always agree); C-023 stays a hypothesis pending a prompt-diverse variant |
| 3 | A <= 4 of 8 | the actor does not follow the tally; the vote is decorative; fix the actor prompt, not N |
| 4 | mean wall > 140 s, or 3 or more of 8 capped, or any task past 480 s | the vote costs more than the room (EXP-033 mean 56.9 s); report seconds per vote point; no dev-48 arm at this N |
| 5 | D >= 1, A >= 6 of 8, wall within row 4's bounds | the mechanism works: promote to one dev-48 E4B arm paired against EXP-038, same 48 ids |
| 6 | otherwise | no decision |

**Endpoint a dev-48 arm would carry, if row 5 fires.** Paired resolves against EXP-038 on dev-48 (McNemar), with the E4B single loop as the reference, plus D and A on 48, mean wall, and cap incidence. Resolves of the smoke-8 are recorded and are never an endpoint. The screen can only decide two things: kill V1 (rows 1 to 3) or promote it (row 5). It cannot decide that voting does not help the E4B.

**Predictions (blind).** Loop functions 75%. C >= 2 in at least 6 of 8: 65%. D >= 1: 60% (the proposer's candidates are near-duplicates and a spread of temperatures sometimes flips a close call). A >= 6 of 8: 55%. Row 5 about 25%, row 2 about 20%, row 1 about 20%, row 4 about 10%, row 0 about 15%, row 3 and 6 the rest.

## 5. What this licenses

- It licenses a Stage-0 zero-GPU probe: the experimenter builds a fake-relay check of the template path (`{cands?}`, `{vote_k?}` with empty and with filled values) and the full validator on the real V1 tree with N = 16. It costs no GPU.
- It does not license the screen. The screen is the recommendation, with its cost stated for the user before any push (user decision 2026-11-05 about 17:30 UTC).
- Expected cost of the V1 screen from EXP-033's numbers: kernel overhead about 0.125 h (vLLM up 322.9 s) plus 8 tasks at about 79 to 105 s (57 s single loop plus 22 to 48 s of extra turns, vote wall about 5 to 15 s at N = 16 and the actor's hand-off turns) gives about **0.31 to 0.37 GPU-h**. **Conditional worst case** about 1.2 h (8 tasks at the 495 s cap plus overhead; EXP-033's tasks ran at 57 s, so this needs every nudge restart to fire). The D-004 ledger has about 0.3 to 0.34 h left of 3.2 after EXP-038's roughly 1.0 committed, so the screen fits only if EXP-038 lands under its point estimate or the user raises the ceiling; the lead owns the ledger.
- Tool changes: none needed. `pack_submission.py --skip-budget-gate` is allowed for a screen above 4.5 min, and `tools: []` clears the voters' lint warning so `--allow-warnings` is needed only for the two carried warnings.

## 6. Exact commands run

```
python tools/validate_submission.py experiments/EXP-039/probe --official --strict
python tools/validate_submission.py experiments/EXP-039/probe --strict
```

Result of the second (after adding `tools: []` to the voters): 17 files, 8 agents; 2 warnings (actor can end the session through `submit_patch`; timeout 240 < 300) and 1 error (packing gate 18.00 h at 8 minutes), as in the EXP-032 P1 tree. The first run showed 4 extra warnings, "no tools declared" on the voters. The official validator is not importable in this environment.

## 7. Defects in this desk check, logged after the fact

1. X(N) is a decode-bound burst number (256-token outputs on short prompts), so V(N) under real prefills is extrapolated; N_max about 100 rests on it. Marked [I].
2. The trace does not tag nudge restarts, so the pass-per-task count is inferred from text-only turns, not counted. No nudge number is claimed.
3. Cost per extra turn uses EXP-033's 6.0 s mean; vote replies are far shorter, so the vote wall may be lower, while the actor's hand-off turns may be higher. The 22 to 48 s range is a width, not a distribution.
4. `thinking_budget: 0` on the E4B and `include_thoughts: false` are unverified; the validator passes them only because it knows nothing of the model's template.
5. The probe tree has 4 voters and placeholder prompts; the screen's prompts are the experimenter's to write and are not pre-registered here.
6. The per-step design was not probed. Its cost (4.7 x) is arithmetic from EXP-033, not a measurement.
7. **Found after commit (advisor review, confirmed in source): `include_contents: none` hides the task message from the voters and the actor.** `_get_current_turn_contents` (`contents.py:569-580`) returns the events from the latest branch-visible event that is a user message or another agent's reply. For a voter that is the proposer's final text; for the actor it is the last voter's text. The task message (a `user` event) falls before the window, so section 2 Q1's sentence that a voter "sees none of the history" is true but incomplete, and the probe prompts' "the issue in the task message" point at nothing. A nudge restart has the same effect on the proposer: the latest user event becomes the nudge text. The EXP-032 localizers ran first, so they were not affected; whether the EXP-032 editor was, was not checked. **Fix options, to be decided in the screen's own pre-registration:** (a) the proposer writes an `ISSUE:` line of at most 120 words before the lettered candidates, so the issue reaches voters and the actor through `{cands?}` (cheapest, keeps the voters at about 3k tokens); (b) voters on default `include_contents` (branch isolation already hides siblings), at the price of a prompt that carries the proposer's read outputs, so its size must be recomputed against the 14,336 compaction threshold. For the actor, default `include_contents` is the plain fix (it then sees the task message, the proposer's reads and the votes). The probe tree is updated to option (a) plus an actor on default contents; the Q4 vote format and tie rule do not change. Section 4 is not touched.
8. **Found after commit: F7's bound.** The limit of 3 consecutive nudges applies only to passes without a tool call, and the counter resets when a pass had one (`agent_runner.py:788-1019`). Every re-run of V1 runs the proposer, which makes read calls, so the counter resets on every pass. Re-runs are bounded by the 28-call cap (about 4 passes at 6 reads each) and the turn cap, and the actor's `submit_patch` is the only thing that ends the cycle early. The 1.2 h worst case (495 s per task) is still the ceiling; no cost number changes.
9. The 31B line (single vote point about 33 s per task against 13.8 s of headroom) is an [I] estimate whose composition is not itemised in this note; take it as order of magnitude only.

## 9. Results

None: this is a desk check. The answers to the seven questions are in section 2, the design and its cost in sections 3 and 5.

## Status

L0 COMPLETE 2026-11-05, 0.0 GPU-h. C-023 not killed. V1 (one vote point, N = 16, E4B, tool-less voters, tie to the lowest-numbered voter) is recommended for a smoke-8 screen, pending the user's GPU approval and the ledger; readings in section 4 are blind. No kernel pushed, no candidate built.
