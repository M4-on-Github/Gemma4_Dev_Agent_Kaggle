# EXP-040 — Voting agents V1 on the E4B, smoke-8 screen (C-023): sixteen tool-less voters at one vote point, paired against EXP-033

**Date:** 2026-11-05
**Type:** smoke-8 screen, one arm, about 0.31-0.37 L4x4-h expected (conditional worst case about 1.2 h, section 2 gives the arithmetic). ~~**Built, not pushed**: the user has not approved this screen's GPU.~~ **Pushed 2026-11-05 22:03 UTC** (kernel `rainm4/gemma4-exp040-v1` v1). The user approved it at about 22:00 UTC (`knowledge/user-decisions.md`). The push record is under the Status line.
**Cohort:** smoke-8
**Ladder:** L2. L0 is EXP-039 (expressibility, termination, vote format, bound on N, failure modes F1 to F11). L1 cannot read it: no E4B trace holds a candidate list, a vote or a multi-agent run.
**Pre-registered:** this file, the tree, the zip's recorded sha and the notebook are committed before any push. Sections 3 to 5 are written blind and are not revised; results are appended as a new section.
**Serves:** C-023 (hypothesis, D-005), the user's decision of 2026-11-05 about 17:30 UTC: voting agents "with varying temps", a deterministic tie rule, and "maximum allowed agents" on the E4B.
**Relates:** EXP-039 (the desk check this builds and whose section 4 readings it copies), EXP-033 (the reference arm on the same 8 ids and the source tree), EXP-038 (E4B dev-48, not touched), EXP-032 (P1: a prompt-only call limit did not hold; ParallelAgent in the real harness), EXP-006 (concurrency X(N)), D-004.
**Tags:** [V] verified in source, trace or by a check run here, [M] community or mirror, [I] inference.

## 1. Why this, now

The user asked for agents that vote on the best next move. EXP-039 found that the one design that is both expressible and enforceable is a single vote point: `Sequential[proposer, Parallel[N voters], actor]`, and that the E4B has the clock for it (EXP-033: mean 423 s and minimum 389 s left under the 480 s cap, 6.0 s per model turn, 0 of 8 capped). This file builds that design at N = 16 (the largest N with a measured concurrency X, 9.45 in EXP-006) and fixes the readings before any trace exists. The lead is putting the cost to the user; the kernel is not pushed in this job.

Reference arm: EXP-033 on the same 8 ids (`experiments/EXP-033-e4b-single-loop-smoke8.md` section 9). Per task: requests_7309 27.9 s, requests_7205 89.6 s, fastapi_14448 56.8 s, fastapi_14301 31.3 s, httpx_3672 60.4 s, fastapi_14605 90.7 s, rich_3468 56.2 s, rich_3006 42.6 s; mean 56.9 s, 9.5 turns, 5.4 counted calls, 0 of 8 capped, 6 of 8 non-empty patches, resolved 2 of 8 (fastapi_14301, rich_3006; recorded, not read).

## 2. Design

### 2.1 The tree

`experiments/EXP-040/candidate-v1/` is built from `experiments/EXP-033/candidate-e4b/` (EXP-027's v24-at-8 prompt, `model: gemma-4-e4b-it-qat-w4a16-ct`). 20 agents, 26 files.

```
swe_agent (SequentialAgent)
  proposer   LlmAgent, read_file + get_status, include_contents none, output_key cands
  vote       ParallelAgent
    voter_01 .. voter_16   LlmAgent, tools [], include_contents none, output_key vote_01 .. vote_16
  actor      LlmAgent, the six EXP-033 tools, include_contents default, instruction = v24 + one inserted section
```

**Every difference from the EXP-033 tree** (the screen's variables; `diff -rq experiments/EXP-033/candidate-e4b experiments/EXP-040/candidate-v1` lists the files, the two modified ones are diffed below):

| # | Difference | File | Why |
|---|---|---|---|
| 1 | Root changes from one `LlmAgent` to a `SequentialAgent` with three sub-agents | `agent.yaml`, `sub_agents/{proposer,vote,actor}.yaml` | the design under test |
| 2 | New proposer: E4B, `read_file` and `get_status` only, at most 4 reads of at most 120 lines, ends with an `ISSUE:` line (at most 120 words) and at most four lettered candidates, `output_key: cands`; sampling temperature 1.0, `max_output_tokens` 4096 (EXP-033: 8192), `thinking_budget` 1024 (EXP-033: 4096) | `sub_agents/proposer.yaml`, `prompts/proposer.md`, `configs/sampling_proposer.yaml` | a short plan, so the voters have options and the proposer cannot spend the actor's clock |
| 3 | 16 voters: E4B, `tools: []`, `include_contents: none`, one shared instruction file, `output_key: vote_NN`; temperatures 0.20, 0.28, 0.36, 0.44, 0.52, 0.60, 0.68, 0.76, 0.84, 0.92, 1.00, 1.08, 1.16, 1.24, 1.32, 1.40 (voter 1 lowest); `top_p` 0.95, `top_k` 64, `max_output_tokens` 256, `thinking_budget` 0, `include_thoughts` false; reply `PICK: X` | `sub_agents/vote.yaml`, `sub_agents/voter_01.yaml` .. `voter_16.yaml`, `prompts/voter.md` | the vote; the voters differ in temperature and nothing else |
| 4 | Actor prompt is the v24 text byte for byte plus one inserted section ("Team plan and votes", 26 lines, before "## 1. Contract") that carries `{cands?}`, `{vote_01?}` .. `{vote_16?}` and the tally and tie rule as sentences; the actor runs on default contents. The inserted text alone is in `experiments/EXP-040/actor_insert.md` | `prompts/actor.md` (EXP-033's `system.md`) | the actor must see the plan and the votes and apply the rule |
| 5 | `max_turns` 80 to 200 (the other three values, 240 / 28 / 8 min, are EXP-033's) | `eval_config.yaml` | every model event of every agent counts as a turn (`context.py:277-299`); one pass is about 34 turns (check c) |
| 6 | The actor's sampling file is EXP-033's `configs/sampling.yaml` unchanged (temperature 1.0, 8192 output, thinking 4096) | `configs/sampling.yaml` | the actor is the EXP-033 agent |

```
$ diff -u experiments/EXP-033/candidate-e4b/eval_config.yaml experiments/EXP-040/candidate-v1/eval_config.yaml
+# EXP-040 2026-11-05: max_turns 80 -> 200. (comment, 2 lines)
 evaluation:
   timeout_seconds: 240
   max_tool_calls: 28
   max_time_minutes: 8
-  max_turns: 80
+  max_turns: 200
```

`prompts/actor.md` against `prompts/system.md`: one hunk, `@@ -5,6 +5,32 @@`, 26 added lines after "## Budget", nothing removed. The actor is told to state the counts and the winner in one sentence that ends "The winner is X." so that the stated winner can be compared with the recomputed one by code.

Every changed value in YAML carries a dated `EXP-040 2026-11-05` comment in the file. Prompts carry no braces other than the 17 placeholders (checked, 17 lines in `actor.md`, 1 in `voter.md`), no forbidden lint word and no URL.

### 2.2 The F11 fix, and why this one

EXP-039 section 7 item 7 (F11): with `include_contents: none` the context window starts at the latest user event or at another agent's reply (`contents.py:569-580`), so a voter or an actor on `none` never sees the task message. Three ways out:

1. **The proposer's `ISSUE:` line reaches the voters through `{cands?}`, and the actor runs on default contents (chosen).** The voter prompt is the same few hundred tokens for all 16 voters, so the vote differs by temperature only. The actor keeps the whole history (the task message, the proposer's reads, the votes as "For context" lines) and the v24 prompt works as it did.
2. Voters on default contents. They would see the task message and the proposer's whole read trace (up to 4 x 120 lines), so a prompt of 4k to 9k tokens times 16, near the compaction threshold, and the voters would no longer be a cheap burst. Rejected on cost and compaction risk.
3. Pass the task text through session state. There is no state key for the task message in the harness path. Rejected as unavailable.

The price of (1): the voters judge the candidates on the proposer's 120-word restatement, not on the issue text. So this screen tests the vote on the proposer's summary, not on the issue. If that summary is wrong the vote cannot be right; C and A (section 3) read it.

### 2.3 Zero-GPU checks, with commands and results

**(a) Validator on the real tree, strict.** `python tools/validate_submission.py experiments/EXP-040/candidate-v1 --strict` gives 26 files, 20 agents, `RESULT: INVALID (1 errors, 2 warnings)`. The one error is the packing gate, `120 x (8 + 1.0 setup) min = 18.00 h (gate 11.0 h)`, expected: a screen at 8 minutes needs `--skip-budget-gate`, as EXP-032 and EXP-033 used (stated here, and recorded in section 6). The two warnings are expected and carried from the EXP-032 P1 tree: "sub-agent with submit_patch can end the session from inside a sub-call" (the actor) and "timeout_seconds=240 < 300 may also cap the grading pytest run (VERIFY(Q2))". There is no "no tools declared" warning on the voters (`tools: []`). The two info lines on thinking being ON for the proposer and the actor are the EXP-033 situation (VERIFY(Q3)). The official validator (`--official`) is not importable here and was not run [V].

**(b) The template path.** Source: `data/src/google_adk/google/adk/utils/instructions_utils.py:81-124`, regex `{+[^{}]*}+` (line 124). [V] from the source lines:
- a trailing `?` makes the key optional (84-86); a key that is absent from `session.state` renders as the empty string when optional (115-120) and raises `KeyError` otherwise (122), so every placeholder carries `?`;
- a value that is `None` renders as the empty string (111-112); any other value is `str(value)` (113);
- a name that is not an identifier is returned unchanged (107-108), so prose with braces is left alone, and the substitution is a single pass over the template, so braces inside an injected `cands` are not templated again (73-79).

The test file `experiments/EXP-040/test_template_relay.py` runs the real prompt files through (i) the real `inject_session_state` if `google.adk` imports and (ii) a line-for-line port of lines 70-149 that runs anywhere. Command: `python -m pytest experiments/EXP-040/test_template_relay.py -q -rs`. Result: the port tests (empty state, filled state with a `None` vote and braces inside `cands`, every placeholder optional and a valid name, 17 placeholders in `actor.md`, a required key raises) pass; the two real-ADK tests are SKIPPED: `google.adk does not import here: ModuleNotFoundError("No module named 'opentelemetry'")`. So the relay has been proved against the source's logic, not against the installed package; the first kernel is the first run of the real one [V for the port, I for the package].

**(c) Prompt size and turn counts.** Source numbers: prompt tokens at the first call of the 8 EXP-033 traces, 2.3k to 3.0k (2,342 to 3,030) [V]; the compaction threshold is 14,336 on the latest prompt-token count (`.claude/skills/harness-stack/reference/compaction.md`).
- Voter prompt = the 100-token template + `cands`. A realistic `cands` (ISSUE 120 words about 170 tokens, four one-sentence candidates about 160) gives **about 0.5 to 0.7k tokens**. Worst case: the proposer ends at its 4096-token cap and all of it is text, **about 4.3k**. 30% of the threshold at worst, 5% at realistic. [I for the realistic length: no E4B candidate list exists on disk]
- Actor's first call: v24 and the task message (2.3k to 3.0k as in EXP-033) + the inserted section (0.5k to 4.3k with `cands`, 0.15k for the votes) + the proposer's reads that default contents carry (the proxy assumes all four reads, each about 0.9k to 1.5k tokens for at most 120 lines [I]). **Proxy range about 6.7k (2.3 + 0.65 + 4 x 0.94) to 13.5k (3.0 + 4.3 + 0.15 + 4 x 1.5), under 14,336 at the top by 0.8k.** A proposer that reads less gives less. Its later calls may compact, as in EXP-033 (1 of 8). A compaction summarizer call counts on the clock, not as a turn. The parallel stage holds only text events, so ADK issue 7324 does not apply there [I].
- Turns per task against `max_turns` 200 (the F7 correction: the 3-nudge limit applies only to passes without a tool call; a pass that ends in text re-runs the whole tree, bounded by the 28-call cap shared with the proposer's reads, the 8-minute clock and the turn cap):

| passes | turns (about 8 proposer + 16 voter + 10 actor = 34 per pass) | against 200 |
|---|---|---|
| 1 | 34 | 17% |
| 2 | 68 | 34% |
| 4 | 136, stress 140 | 68% to 70% |
| 5 | 170 | 85% |
| 6 | 204 | exceeds; the turn cap or the clock ends the task here |

`max_turns: 80` would end a task in its third pass, which is why it is raised. A restart costs one pass of about 34 turns, of which 16 are the parallel voters; in time about 35 to 60 s [I] (proposer and actor turns are serial at 6.0 s, the 16 voters are one concurrent burst of about 5 to 15 s).

**(d) Tally and tie rule by code.** `experiments/EXP-040/tally.py` is a pure function of the proposer's text and the voters' texts as the trace records them (`extra.author` of each agent step: `proposer`, `voter_01` .. `voter_16`, `actor`): `candidate_letters`, `parse_vote` (a line that is exactly `PICK: X`, X a candidate letter), `tally` (most votes; a tie goes to the tied letter picked by the lowest-numbered voter; no valid vote gives A), `d_flag` (D for one task: winner differs from voter 1's pick; undefined when voter 1's vote is invalid), `stated_winner` (the actor's "The winner is X"), and `extract_rounds` for a trace with restarts. `experiments/EXP-040/test_tally.py` has 11 cases: clear majority, tie to the lowest voter, a lower voter whose letter is not in the tie, no valid vote, malformed lines, a letter outside the set, candidate extraction, the D definition, the stated winner, a two-pass extraction fixture, and a trace with no votes. Command and result: `python -m pytest experiments/EXP-040 -q -rs`: 15 passed, 2 skipped (the two real-ADK tests of (b)).

How **A** (the actor followed the winner) is judged: by hand on the 8 traces, blind to the resolved flag. A task counts as followed when the first `edit_file` or `write_file` call touches the file the winning candidate names and the edited span lies in the function or change that candidate names; if the candidate names only a file, a file match is enough; an ambiguous case counts as not followed. The file-level match is also recorded (A_file) and is a supporting number. Separately the code checks whether the actor's stated winner equals the recomputed W (counting fidelity, not following fidelity).

How to run the recompute after the run: `tally.py` takes a traces directory (`main(argv)`), but this agent's shell can run only `python tools/` and `python -m pytest`, so the post-run call needs the experimenter or a thin wrapper under `tools/` (not written here, `tools/` is not mine).

### 2.4 Cost

| item | seconds | basis |
|---|---|---|
| kernel overhead (boot 322.9 s, decode probe, teardown) | about 445 | EXP-033: kernel span 900 s minus 455.5 s of tasks |
| per task, single loop | 57 | EXP-033 mean |
| proposer (about 8 serial turns) | +30 to 48 | 6.0 s per turn |
| 16 voters, one concurrent burst | +5 to 15 | X(16) = 9.45 on short prompts [I above 4 on real prefills] |
| actor, longer prompt and the tally sentence | +5 to 15 | |
| per task, point | 79 to 105 | |
| 8 tasks + overhead | 1,077 to 1,285 s | = **0.30 to 0.36 GPU-h**, the 0.31 to 0.37 of EXP-039 |

**Conditional worst case about 1.2 GPU-h**: every task at the 495 s cap plus overhead, 8 x 495 + 445 = 4,405 s = 1.22 h. EXP-033's tasks ran at 57 s, so this needs every pass to restart until the clock. **What a restart costs:** about 34 turns, 35 to 60 s per extra pass per task, so two tasks with one extra pass add about 0.03 h. **What a failed screen costs to re-run:** if row 0 fires and the one cause is fixed, one more kernel of 0.30 to 0.36 h; the lead owns the ledger and the user's ceiling.

`pack_submission.py --skip-budget-gate --allow-warnings` is used: the screen's 8-minute setting is above the 4.5-minute packing gate (as EXP-032 and EXP-033), the gate is for the real submission, and a screen is never uploaded.

## 3. Endpoints, fixed in advance

Counts over the 8 tasks, read from `runs/EXP-040-v1/.../traces/trace_<id>.json`, `summary.jsonl` and the kernel log, and from `tally.py`. Reference for each is EXP-033's table.

| # | Endpoint | Definition |
|---|---|---|
| E1 | C | per task, distinct lettered candidates in the proposer's final text (`tally.candidate_letters`) |
| E2 | Parseable votes | per task, valid `PICK: X` lines of 16; a task is "voted" at 12 or more |
| E3 | D | tasks of 8 where the recomputed winner W differs from voter 1's pick P1 (undefined when P1 is invalid, reported apart) |
| E4 | Tie rule | tasks where W was decided by the tie rule; the actor's stated winner against W |
| E5 | A | tasks where the actor's first edit follows W (hand check, section 2.3 d) |
| E6 | F11 check | the voter prompt in the trace contains the `ISSUE:` line; the actor's first message mentions the issue |
| E7 | Passes and turns | per task, rounds from `extract_rounds`; model turns from the trace against 200 |
| E8 | Wall | per task and mean (EXP-033 mean 56.9 s); capped (calls 28, turns 200, time 480 s, as E6 of EXP-033); vote-stage wall from the first to the last voter step timestamp |
| E9 | Malformed calls, compactions, non-empty patches | as EXP-033 (0 of 43, 1, 6 of 8) |
| E10 | Resolves | recorded only, no rate claimed, not read |

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Copied from EXP-039 section 4, unchanged in substance. The order is first match. Quantities: C, the vote texts, W, P1, D and A as defined above and in section 3.

| Row | Condition | Reading |
|---|---|---|
| 0 | infrastructure: a crash in more than 2 of 8, or fewer than 6 of 8 tasks with at least 12 of 16 parseable votes, or the tree does not run | fix the one cause (for example F5) and re-run once; no reading |
| 1 | C >= 2 in fewer than 6 of 8 tasks | the proposer yields no real alternatives; kill V1 as specified and send the gap (EXP-039 Q6, 2) to the lit-scout; the claim is not killed, its candidate source is |
| 2 | D = 0 of 8 | the vote never changed a pick: kill V1 as specified (at N = 16 the voters and voter 1 always agree); C-023 stays a hypothesis pending a prompt-diverse variant |
| 3 | A <= 4 of 8 | the actor does not follow the tally; the vote is decorative; fix the actor prompt, not N |
| 4 | mean wall > 140 s, or 3 or more of 8 capped, or any task past 480 s | the vote costs more than the room (EXP-033 mean 56.9 s); report seconds per vote point; no dev-48 arm at this N |
| 5 | D >= 1, A >= 6 of 8, wall within row 4's bounds | the mechanism works: promote to one dev-48 E4B arm paired against EXP-038, same 48 ids |
| 6 | otherwise | no decision |

Recorded in every row, not read: resolves (E10) and the counts E4, E6, E7, E9.

**Blind prediction.** Loop functions: 75%. C >= 2 in at least 6 of 8: 65%. D >= 1: 60%, because the proposer's candidates are near-duplicates and a spread of temperatures sometimes flips a close call. Voted (at least 12 of 16 parseable) in 6 or more of 8: 70%. A >= 6 of 8: 55%. At least one task with more than one pass: 50%. Mean wall 90 to 130 s, kernel 0.30 to 0.40 h. Row 5 about 25%, row 2 about 20%, row 1 about 20%, row 4 about 10%, row 0 about 15%, rows 3 and 6 the rest. Resolves 1 to 3 of 8, recorded not read.

### 4.1 Amendment, 2026-11-05, before any push (added, nothing above is rewritten)

Source: the lit-scout's note `research/lit/lit-2026-11-05-voting-agents.md` (committed 6fd7787), sections 3, 4 and 6(c). The tree, the zip (`e476acb6...29d8`), the notebook and the cohort are unchanged. No row, threshold or pre-registered probability above is altered. Two endpoints are added. **Both are recorded and not read by any row**, and both are pure functions of the 16 vote texts per task, recomputed by `tally.py` after the run.

- **E11, the lead.** Per task, the top letter's count minus the runner-up's count over the valid votes (a tie has lead 0, a unanimous task with all 16 parseable has lead 16, no valid vote has lead 0). D is also reported split by lead: tasks with D true and lead under 3, and with D true and lead 3 or more; the per-task leads are listed and the number of tasks unanimous on all 16 is counted. Reason: a margin rule, apply the leading letter only if it leads by 3 or more and otherwise apply voter 1's pick, is the best-supported design change in the note (MAKER's first-to-ahead-by-k, CATTS margin-gated arbitration; confidence low to medium, the fallback to voter 1 is the scout's choice and no source tests it). It is **not applied in this screen**: by the scout's inference it would revert exactly the close-lead tasks to voter 1, push D toward 0 and could fire row 2 for a reason unrelated to voter agreement. It is a candidate for a later arm only if D >= 1 shows that close-lead tasks exist.
- **E12, the malformed-vote rate by temperature bucket.** Voters 1 to 6 (0.20 to 0.60, "0.6 or below"), voters 7 to 11 (0.68 to 1.00, "above 0.6 up to 1.0"), voters 12 to 16 (1.08 to 1.40, "above 1.0"). Per bucket, over the 8 tasks' first pass: n = voters with a recorded reply, malformed = recorded replies that give no valid vote (not `PICK: X`, or X outside the candidate set, or empty), so a malformed vote counts in its bucket's denominator; a voter with no recorded step is counted apart as absent. Reason: two sources (Renze and Guven; MAKER Fig. 6(b)) report degradation above temperature 1.0 and five of the 16 voters sit above 1.0. The spread stays as built: the user asked for varying temperatures and the screen measures what the hot end costs. Row 0 is unchanged (fewer than 6 of 8 tasks with at least 12 of 16 parseable votes); E12 only shows where the unparseable votes come from.

**Blind expectations that change no reading** (the scout's inference, recorded as such): row 2 (D = 0 of 8) looks a little likelier than the pre-registered 20%, because same-prompt self-consistency adds only 1.6 to 2.0 points over greedy on three agent benchmarks and the voters share one instruction, one candidate order and one letter prior; and at least 3 of 8 tasks are unanimous (all 16 valid votes the same letter), by analogy with CATTS' about 40% of steps unanimous at N = 10. Confidence low: no same-model, same-list number exists. The pre-registered odds in the blind prediction above stand as written.

`tally.py` now computes `lead`, `voter_temperature`, `temperature_bucket` and `malformed_by_bucket`, and prints the D split, the leads, the unanimous count and the bucket totals in its summary line. `test_tally.py` has 18 cases (7 added: a tie has lead 0, a unanimous all-16 task has lead 16, lead margins and the lead-3 boundary, letters outside the set, the bucket boundaries 0.60 and 1.00, a malformed vote in its bucket's denominator, an absent voter, and `score_round` carrying both). `python -m pytest experiments/EXP-040 -q -rs`: 22 passed, 2 skipped (the real-ADK tests of check (b)).

## 5. What this licenses

**The screen can decide one of two things.** It can **kill V1 as specified** (row 1: no real alternatives, row 2: the vote is inert at N = 16, row 3: the actor ignores the tally), or it can **promote V1 to one dev-48 E4B arm** (row 5). It cannot decide that voting does not help the E4B, and it cannot decide that it does: n = 8, resolves are recorded and never an endpoint.

**The dev-48 endpoint if row 5 fires.** Paired resolves against EXP-038 (the E4B single loop on the same 48 ids; McNemar, discordant pairs reported), plus D and A on 48, mean wall, cap incidence and the projected 120-task hours (must stay at or under 11 h at the setting the arm uses). A vote-stage wall at N = 16 and the one-pass share are reported so that a scale-up (section 7) can be costed. Estimated cost of that arm: 48 x 79 to 105 s + overhead = 1.2 to 1.6 GPU-h [I], to be recomputed from this screen's wall before the ask.

Rows 1 to 3 keep C-023 a hypothesis; row 5 asks for a dev-48 arm and for no upload. No row licenses an upload.

## 6. Exact commands

```
python tools/validate_submission.py experiments/EXP-040/candidate-v1 --strict
python -m pytest experiments/EXP-040 -q -rs
python tools/pack_submission.py --src experiments/EXP-040/candidate-v1 --out dist/EXP-040-v1.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed dist/EXP-040-v1.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-040-v1"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp040_v1/kaggle_eval_l4x4.ipynb
# push, a later job, only after the user approves the GPU and the lead dispatches it:   kaggle kernels push -p notebooks/exp040_v1
# after COMPLETE, a separate job:
kaggle kernels output rainm4/gemma4-exp040-v1 -p runs/EXP-040-v1/
python tools/analyze_traces.py <inner bundle dir> --cap-minutes 8 --max-calls 28
python tools/run_forensics.py forensics <inner bundle dir>
python tools/run_forensics.py compare runs/EXP-033-e4b/runs/EXP-033-e4b <inner bundle dir>
# D, A-support and tie-rule fidelity: tally.main(["tally.py", "<inner bundle dir>/traces"])  (a wrapper is needed, see 2.3 d)
```

## 7. Defects, and two paragraphs that are not run

**Defects known at writing.** (1) The real ADK substitution has not run: `google.adk` does not import here (no `opentelemetry`), so (b) is a source read plus a port. (2) The realistic `cands` length is an estimate: no E4B candidate list exists on disk. (3) The voters decide on the proposer's restatement (2.2), so a bad `ISSUE:` line makes a bad vote, and C and A cannot tell the two apart. (4) `thinking_budget: 0` and `include_thoughts: false` are validated but whether the E4B template honours them is unverified (F5); the first trace shows it. (5) The actor on default contents inherits the proposer's reads, so its first call may sit close to 14,336. (6) `tally.py` cannot be run by this agent's shell outside pytest; a wrapper under `tools/` or the experimenter's hand is needed after the run. (7) A is a hand judgement by one reader.

**Found at analysis, 2026-11-05.** Added after the run. Nothing above is rewritten.

**(8) `tally.extract_rounds` puts a restart pass's early votes into the previous pass.** It opens a new pass only when voter_01's step appears. In a restart pass, any voter whose reply completes before voter_01's is written into the previous pass instead.
- **Where it happened:** only httpx_3672, the one task with two passes. In its pass 2, eight voters (2, 7, 8, 10, 12, 13, 14, 16) finished before voter 1. The pass-2 candidate list was empty, so those eight replies parse as malformed.
- **What it moved, in the as-written output:** E2 for that task (8 parseable, corrected 16), E11 (lead 6, corrected 10) and E12 (1, 3 and 4 malformed by bucket, corrected 0, 0 and 0). D for the task is false either way: W = P1 = B.
- **Effect on the readings:** no row changes.
- **The fix:** `tally.py` is the committed instrument and is left unchanged. `experiments/EXP-040/analyze_results.py` re-segments passes as maximal runs of consecutive voter steps, scores them with the same `tally.score_round`, and reports both versions. Section 9 gives the as-written figure as the endpoint and the corrected figure beside it.

**(9) A was not judged blind to resolved.** The kernel log line `RESOLVED 1/8` and the per-task resolved flags were seen before the hand check.

**(10) E6's second clause was not defined as a computation.** The clause is "the actor's first message mentions the issue". It was judged by hand by the same reader.

**(11) The voter prompts are not recorded in the trace.** E6's first clause is therefore read from two proxies:
- whether the proposer's final text, which `{cands?}` carries, has an `ISSUE:` line;
- each voter step's prompt-token count.

**Not run, second arm A: the per-step version** (the user's "vote for the best next move"). It is `LoopAgent[proposer, Parallel[voters], actor]`, and it can be screened honestly only if the executor stops after one counted call per round. The harness has no exit tool and the prompt-only rule failed in EXP-032 P1 (21 of 24 localizers ignored a 5-call limit), so the first thing needed is a zero-GPU read of that rate on traces that exist: the share of actor invocations that end after exactly one counted call (EXP-032 P1 traces and, from this screen, the actor's text-only turns), and, if that is inconclusive, a 3-task two-round stub loop whose executor is told to make one call and reply DONE, about 0.13 to 0.2 GPU-h, boot-dominated [I]. What from this screen would justify trying it: row 5, D >= 2 of 8 (the vote changes the pick more than once at a single point), A >= 7 of 8, mean wall under 90 s (per-step costs about 4.7 times the single loop, EXP-039 Q5), and a one-call rate of at least 80% in the zero-GPU read. Otherwise per-step voting is not screened.

**Not run, scale-up to "maximum": about 100 voters at one vote point.** Nothing above X(16) = 9.45 is measured, and EXP-006 measured decode-bound 256-token bursts on short prompts, which overstates X under real prefills. The first thing needed is a concurrency probe at real prompt sizes: a bursts-only kernel (no agent, the E4B boot plus bursts of 16, 32, 64 and 100 identical requests at 0.5k and 4.3k prompt tokens, `max_output_tokens` 256), about 0.1 to 0.15 GPU-h with the 0.125 h boot dominating [I]. It is not pre-registered here and it needs its own approval. The vote stage itself would add about 5 to 30 s per task (EXP-039 Q5) and 100 turns per pass against `max_turns` 200, so N = 100 leaves room for one pass and a restart only if `max_turns` goes to 500, the schema limit.

## 8. Built

Built 2026-11-05 after the pre-registration commit 3f33acd, with the section 6 commands.

- Pack: `python tools/pack_submission.py --src experiments/EXP-040/candidate-v1 --out dist/EXP-040-v1.zip --skip-budget-gate --allow-warnings` gave 26 reachable files, `RESULT: VALID (0 errors, 3 warnings)` (the packing gate demoted to a warning, the `submit_patch` sub-agent warning, the 240 s timeout warning), 20 agents, `dist/EXP-040-v1.zip` 13.0 KiB. **Zip sha256 `e476acb6ee48d264503e87fe0e4b8b5673e34bff23eb5dd6a3c1b136525429d8`** (confirmed with `sha256sum`). The zip was packed from LF worktree files that equal the committed blobs, so it reproduces from commit 3f33acd. Screen build, never uploaded.
- Notebook: `notebooks/exp040_v1/kaggle_eval_l4x4.ipynb`, parameter cell read back: `EXP_ID = "EXP-040-v1"`, `RUN_GOLD_CONTROL = False`, `RUN_AGENT = True`, `TASK_IDS` = fastapi_14301, fastapi_14448, fastapi_14605, httpx_3672, requests_7205, requests_7309, rich_3006, rich_3468 (the 8 ids of `experiments/cohorts/smoke-8.txt`), `N_TASKS = 8`, `MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"`; 17,788 base64 characters embedded.
- `notebooks/exp040_v1/kernel-metadata.json`: copied from `notebooks/exp033_e4b/` with only `id` (`rainm4/gemma4-exp040-v1`) and `title` (`gemma4-exp040-v1`) changed (`diff` shows those two lines only; model source `google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2`, wheelhouse and competition sources as EXP-033).
- **Kernel id: `rainm4/gemma4-exp040-v1`.** ~~**Not pushed.** The push is a separate job after the user approves the GPU.~~ It was pushed 2026-11-05 22:03 UTC as v1; see the push record under Status. Push command: `kaggle kernels push -p notebooks/exp040_v1`.

## Status

**COMPLETE, ANALYZED (2026-11-05).** Section 9 has the results.
- **Run:** `rainm4/gemma4-exp040-v1` v1, valid. 8 of 8 tasks ran with an empty `err`, on the E4B.
- **Governing row: row 2,** D = 0 of 8, under both the as-written and the corrected tally. V1 as specified is killed at L2.
- **Kernel:** 0.315 GPU-h by log span.
- **Licensed:** none of the following:
  - a dev-48 voting arm (row 5 did not fire);
  - an upload;
  - any change of status for C-023, which stays a hypothesis.
- **Next:** the prompt-diverse variant named by row 2 would be a new design, with its own pre-registration and dispatch.

~~**RUNNING since 2026-11-05 22:03 UTC.** Kernel `rainm4/gemma4-exp040-v1` v1; the push record is below. The lead reports to the user at 22:27 UTC. The worst-case end is 23:16 UTC. Next is a separate job, once the lead reports COMPLETE: `kaggle kernels output rainm4/gemma4-exp040-v1 -p runs/EXP-040-v1/`, un-nest the output, then the section 6 analysis commands.~~

~~2026-11-05: tree built, zip `e476acb6...29d8` packed, notebook built, checks (a) to (d) run, kernel `rainm4/gemma4-exp040-v1` **not pushed**. Awaiting the user's GPU approval, then the lead's dispatch of the push.~~

### Push record, 2026-11-05

**Approval.** The user approved the push on 2026-11-05 at about 22:00 UTC ("yes go ahead"). The verbatim words and the lead's reading are in `knowledge/user-decisions.md`, entry "2026-11-05 ~22:00 UTC: the voting screen EXP-040 goes ahead" (commit 5192295). The lead's working figure is 0.4 GPU-h. One kernel, one version.

**Checks before the push, all passed:**
- `sha256sum dist/EXP-040-v1.zip` gives `e476acb6ee48d264503e87fe0e4b8b5673e34bff23eb5dd6a3c1b136525429d8`, as recorded in section 8.
- The notebook's embedded `SUBMISSION_B64` decodes to a zip with the same sha256.
- `TASK_IDS` equals the 8 ids of `experiments/cohorts/smoke-8.txt`.
- The parameter cell sets `RUN_AGENT = True`, `RUN_GOLD_CONTROL = False`, `MODEL_NAME = "gemma-4-e4b-it-qat-w4a16-ct"` and `N_TASKS = 8`.
- `kernel-metadata.json` sets `is_private: true`, `enable_gpu: true`, `machine_shape: NvidiaL4`, `enable_internet: false`, and model source `google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2`.
- **Nothing changed in the tree since the build.** The worktree is clean for `experiments/EXP-040*` and `notebooks/exp040_v1`. Since the build commit 5b0f266, `git diff --stat 5b0f266 HEAD` shows changes only to:
  - this file (the 75195e5 amendment, an ancestor of HEAD);
  - `experiments/EXP-040/tally.py`;
  - `experiments/EXP-040/test_tally.py`.

  `candidate-v1`, the zip and the notebook are unchanged. `test_tally.py` passes with 18 cases.

**The push.**
- Push time: **2026-11-05 22:03 UTC**, read with `date -u` (22:03:00) right after the push returned.
- CLI output: `Kernel version 1 successfully pushed.  Please check progress at https://www.kaggle.com/code/rainm4/gemma4-exp040-v1`
- Kernel: `rainm4/gemma4-exp040-v1`, **version 1**.
- Status, checked once right after the push: `KernelWorkerStatus.RUNNING`.

**Clock times.** The kernel enforces neither of them.
- push + 0.4 h = **2026-11-05 22:27 UTC**. This is the lead's working figure. At this time the lead reports to the user; cancelling is the user's call, from the Kaggle UI.
- push + 1.22 h = **2026-11-05 23:16 UTC**. This is the pre-registered conditional worst case from section 2.4.

---

## 9. Results, 2026-11-05. Section 4's readings applied as written.

### 9.1 Download and commands

- The lead's status check at 22:28 UTC showed COMPLETE.
- `kaggle kernels output rainm4/gemma4-exp040-v1 -p runs/EXP-040-v1/` downloaded the bundle at 22:29 UTC. I moved the nested `runs/EXP-040-v1/runs/EXP-040-v1/` up one level, so the run directory is `runs/EXP-040-v1/`.

Commands, each run as `python -I -X utf8`:
- `tools/analyze_traces.py runs/EXP-040-v1 --cap-minutes 8 --max-calls 28`
- `tools/run_forensics.py forensics runs/EXP-040-v1`
- `tools/run_forensics.py compare runs/EXP-033-e4b/runs/EXP-033-e4b runs/EXP-040-v1`
- `tools/estimate_budget.py --eval-config experiments/EXP-040/candidate-v1/eval_config.yaml --results runs/EXP-040-v1/summary.jsonl`
- `experiments/EXP-040/tally.py runs/EXP-040-v1/traces`: the pre-registered recompute, run directly; section 7 item (6) said a wrapper would be needed.
- `experiments/EXP-040/analyze_results.py`: writes `experiments/EXP-040/results.json`, which holds ids, counts, letters, voter indices and seconds only.

Copied into `experiments/EXP-040/v1/`: `summary.jsonl` and `aggregates.json`.

Every number below comes from these outputs, except A (E5) and E6's second clause, which are hand judgements (section 7 items 9 and 10).

### 9.2 Run validity

The run is valid on every check, so the endpoints are read.

| Check | Result |
|---|---|
| Rows | 8 in `task_results.jsonl` |
| Ids | exactly the 8 ids of `experiments/cohorts/smoke-8.txt` |
| `err` | empty on 8 of 8; status `SUCCESS` on 8 of 8 |
| Model | the log line `model: gemma-4-e4b-it-qat-w4a16-ct -> /kaggle/input/models/...` is present, and every agent step's `model_name` is the E4B path |
| Server | `vLLM up in 319.8s (tp=4, gpus=4)`; decode probe 400 tokens in 7.14 s |
| Loop | every trace has the proposer, all 16 voters (voter_01 to voter_16, one step each in pass 1) and the actor |
| Truncation | none; `[8/8]` and `RESOLVED 1/8` are both in the log |

### 9.3 Endpoints

Where section 7 item (8) applies, the as-written `tally.py` value is the endpoint and the corrected value is given beside it.

| # | Endpoint | Result | Reference (EXP-033) |
|---|---|---|---|
| E1 | C | 4 candidates on 6 tasks, 1 on 2 (fastapi_14448, rich_3468). **C >= 2 on 6 of 8.** | none |
| E2 | Parseable votes, pass 1 | 16 of 16 on 7 tasks. httpx_3672 has 8 as written and 16 corrected. **Voted (12 or more) on 7 of 8 as written, 8 of 8 corrected.** | none |
| E3 | D | **0 of 8**, both as written and corrected. W = P1 on every task, and D is undefined on none (voter 1's vote is valid on 8 of 8). | none |
| E4 | Tie rule; stated winner | The tie rule decided 0 tasks. The actor's first message names a winner on 2 tasks (fastapi_14301, httpx_3672), and it equals W on both. No actor message after the vote names any other letter. | none |
| E5 | A (hand) | **6 of 8** by the rule as written; A_file is 7 of 8; per task below. | none |
| E6 | F11 check | Below the table. | none |
| E7 | Passes and turns | One pass on 7 tasks, two on httpx_3672. Harness `llm_calls` per task 21 to 41; trace agent steps 25 to 45, all far below 200. | single pass by construction |
| E8 | Wall | Per task 67.0 to 116.8 s; **mean 86.5 s**, median 84.8 s. 0 of 8 at the time, call or turn cap; none past 480 s. Vote stage below. | mean 56.9 s, 0 capped |
| E9 | Calls, compactions, patches | 0 malformed of 67 counted calls. Compactions 5 (1, 1, 0, 0, 0, 1, 2, 0). Non-empty patches 7 of 8. | 0 of 43; 1; 6 of 8 |
| E10 | Resolves | 1 of 8 (fastapi_14301). Recorded, not read. | 2 of 8 |
| E11 | Lead | Below the table. Recorded, not read. | none |
| E12 | Malformed votes by temperature bucket, pass 1 | Below the table. Recorded, not read. | none |

The E1 to E3 rows are `tally.py`'s output.

**E5, A per task.** Followed (first edit in the named file and the named function or change): fastapi_14301, fastapi_14448, requests_7205, requests_7309, rich_3006, rich_3468.
- rich_3468's edit matched through the harness's fallback (unescaped) match. It landed in the named span.
- fastapi_14605 is file-only. The first edit is in the named file, but it adds a supporting line, not the change the winning candidate names. That change follows two edits later. Section 2.3 (d) counts an ambiguous case as not followed. Counting it as followed would give A = 7. That changes no row, because row 2 governs before row 3.
- httpx_3672 is not followed: the actor made no edit in either pass.

**E6, the F11 check.** The voter prompts are not recorded in the trace (section 7 item 11), so the first clause is read from two proxies. The second clause is a hand judgement (section 7 item 10).
- **ISSUE line:** the proposer's final text has an `ISSUE:` line on 5 of 8 tasks; it is missing on fastapi_14448, httpx_3672 and rich_3006.
- **Voter prompt tokens:** 385 to 809 per task in pass 1, the same for all 16 voters of a task. This is consistent with the candidate list reaching every voter.
- **Actor first prompt:** 5,170 to 14,005 tokens on default contents, 0 tasks at or above 14,336. The highest, requests_7205, is 331 tokens under the threshold.
- **Actor first message (hand check):** it refers to the task's issue on 8 of 8.

**E8, the vote stage.** Voter steps are stamped when the parallel stage emits them, so the time from the first to the last voter stamp (0.15 to 0.44 s) is an emission spread, not generation time. From the proposer's last step to the last voter stamp: 0.83 to 1.44 s on 7 tasks, and 11.49 s on requests_7309. The proposer stage, from the task prompt to the proposer's last step, ran 10.0 to 55.0 s.

**E11, the lead, per task.**

| Task | Lead |
|---|---|
| requests_7309 | 10 |
| requests_7205 | 16 |
| fastapi_14448 | 16 |
| fastapi_14301 | 14 |
| httpx_3672 | 6 as written, 10 corrected |
| fastapi_14605 | 16 |
| rich_3468 | 16 |
| rich_3006 | 4 |

- **D by lead:** 0 tasks with D true and lead under 3; 0 with lead 3 or more.
- **Unanimous on all 16:** 4 of 8. Two of these are the C = 1 tasks, so 2 of the 6 tasks with C >= 2 are unanimous.
- **Closest task:** rich_3006, whose 16 votes split 10 to 6 between two letters.

**E12, malformed votes by temperature bucket, pass 1.**

| Bucket | As written | Corrected |
|---|---|---|
| 0.6 or below (n = 48) | 1 | 0 |
| above 0.6 up to 1.0 (n = 40) | 3 | 0 |
| above 1.0 (n = 40) | 4 | 0 |

- No voter was absent.
- All 8 as-written malformed votes are httpx_3672's pass-2 replies (section 7 item 8).
- In pass 1, every voter reply on every task was a single valid pick: 128 of 128 replies were 4 completion tokens each. So `thinking_budget: 0` held for the voters (section 7 item 4).

### 9.4 Readings applied, first match

| Row | Condition | Value | Fires |
|---|---|---|---|
| 0 | Crash in more than 2 of 8; fewer than 6 of 8 voted (12 or more parseable); or the tree does not run | 0 crashes; 7 of 8 voted (8 corrected); the tree ran on 8 of 8 | no |
| 1 | C >= 2 in fewer than 6 of 8 | 6 of 8, exactly at the boundary | no |
| 2 | D = 0 of 8 | **0 of 8**, as written and corrected | **yes, governs** |

*Note under row 1, 2026-11-05 (critic light):* Row 1 is read on pass 1, as tally.main scores it. Counting httpx_3672's restart pass, whose proposer gave no candidates, C >= 2 is 5 of 8 and row 1 would govern (critic light 2026-11-05). Both rows stop V1 as specified. (Experimenter's recount over the traces agrees: 6 of 8 on pass 1, 5 of 8 on the last pass; `out/exp040_critic_check.py`, untracked.)

**Row 2: kill V1 as specified.** At N = 16, the vote and voter 1 agreed on every task. C-023 stays a hypothesis, pending a prompt-diverse variant. Rows 3 to 6 are not reached. For the record:
- A = 6 of 8, so row 3's A <= 4 is not met;
- the mean wall of 86.5 s with 0 capped is within row 4's bounds;
- row 5 needs D >= 1 and is not met.

**Licensed:** stopping V1 as built (a single vote point, 16 same-prompt voters differing only in temperature).

**Not licensed:**
- a dev-48 voting arm, since row 5 did not fire;
- an upload;
- any change of status for C-023;
- a claim that voting does not help the E4B (section 5).

The prompt-diverse variant that row 2 names is a new design: it needs its own pre-registration and the lead's dispatch, and nothing here approves it.

### 9.5 Predictions scored (section 4 and 4.1)

**Section 4:**

| Prediction | Pre-registered | Outcome | Scored |
|---|---|---|---|
| The loop functions | 75% | 8 of 8 | held |
| C >= 2 in at least 6 of 8 | 65% | 6 of 8 | held, at the boundary |
| D >= 1 | 60% | D = 0 | missed |
| Voted in 6 or more of 8 | 70% | 7 of 8 (8 corrected) | held |
| A >= 6 of 8 | 55% | 6 of 8 | held |
| At least one task with more than one pass | 50% | httpx_3672 | held |
| Mean wall 90 to 130 s | | 86.5 s | missed, low |
| Kernel 0.30 to 0.40 h | | 0.315 h | held |
| Resolves 1 to 3 of 8 | | 1 | held |

Row odds:
- row 2 had about 20%, and it fired;
- row 5 had about 25%, rows 1 and 0 about 20% and 15%, row 4 about 10%; none of these fired.

**Section 4.1, the scout's blind expectations:**
- Row 2 a little likelier than 20%: consistent with the outcome. This is one draw, not a test.
- At least 3 of 8 tasks unanimous: 4 of 8. Held as written, but it holds only because the 2 C = 1 tasks are counted. Among the tasks with C >= 2, 2 of 6 were unanimous.

### 9.6 Cost

| Item | Value | Basis |
|---|---|---|
| **Kernel log span** | **1,135.6 s = 0.315 GPU-h** | the last log entry, measured as EXP-033's 0.25 h and EXP-038's 1.267 h were |
| Against the estimate | inside the pre-registered 0.30 to 0.36 h, under the lead's 0.4 h working figure, far under the 1.22 h conditional worst case | section 2.4 |
| Task time | 692.4 s | the sum of `duration_s` |
| Overhead | 443.2 s | span minus task time; section 2.4 estimated about 445 s |
| Mean task | 86.5 s, inside the 79 to 105 s point estimate; max 116.8 s | |
| Caps | no task at any cap; all well under row 4's 140 s mean bar and the 480 s cap | |

The `estimate_budget` projection (mean 8.47 h, worst case 16.00 h, `BLOCK` at the 8-minute cap) is recorded for completeness. A screen is never uploaded.

No upload slot was used.

### 9.7 Paired per-task view, same 8 ids (recorded, not read)

| Reference | Ref. mean wall | V1 mean wall | V1 slower on | Ref. resolves | V1 resolves | 2x2 |
|---|---|---|---|---|---|---|
| EXP-033 (E4B single loop, smoke-8) | 56.9 s | 86.5 s | 8 of 8 | 2 of 8 | 1 of 8 | both fastapi_14301; ref-only rich_3006; V1-only none |
| EXP-038 smoke-8 subset (E4B single loop, dev-48) | 78.3 s | 86.5 s | 6 of 8 | 2 of 8 | 1 of 8 | the same 2x2 |

- **Resolves:** one discordant pair, exact McNemar p = 1.0 (`run_forensics compare`). Eight tasks cannot show a resolve difference, and none is claimed.
- **Wall:** the reference for the same config on the same ids moved from 56.9 s to 78.3 s between two runs (the critic's note). V1's +8.2 s against the EXP-038 subset is inside that drift, so no time effect is read either way.

### 9.8 Outside the readings (recorded, not read)

- **D could only be true on 6 of 8 tasks.** On the 2 tasks with one candidate, every vote must equal voter 1's, so D = 0 there by construction.
- **The candidates were one fix written several ways on 3 of the 6 four-candidate tasks.** On 3 of the 6 tasks with C = 4 (fastapi_14301, requests_7309, rich_3006), the four candidates propose the same change in different words. This is the reader's judgement, not a computed endpoint. The vote also equalled voter 1's pick on the other 3 four-candidate tasks, which were more unanimous (leads 16, 10 corrected, 16, against 14, 10, 4), so this does not explain D = 0. It fits the near-duplicate concern in the section 4 prediction.
  - *Dated correction, 2026-11-05 (critic light).* The opening phrase and one sentence of this bullet were replaced. The earlier wording, kept here: ~~"The candidates were mostly one fix written several ways."~~ and ~~"It is one plausible reason the vote never moved off voter 1's pick, and it fits the near-duplicate concern in the section 4 prediction."~~ The earlier sentence offered the paraphrase sets as a reason for D = 0, which the other three four-candidate tasks contradict.
- **The proposer's 4-read limit (prompt only) held on 5 of 8; requests_7205 and requests_7309 read 7 times, rich_3468 13.** (Added 2026-11-05, critic light; the experimenter's count of proposer `read_file` calls per pass over the traces agrees, and the other 5 tasks made 0 to 3 reads per pass, the 0 being httpx_3672's restart pass.)
- **httpx_3672's restart pass.**
  - The actor ended pass 1 with text and no tool call. The trace then has a harness `continuation_nudge` event, and the whole tree re-ran.
  - The re-run proposer's prompt was 583 tokens, against 1,409 at its first call in pass 1. Its reply had no lettered candidate. This fits its `include_contents: none` window starting at the nudge, the F11 pattern again on a restart [I].
  - With no candidate set, all 16 pass-2 votes parse as invalid, and the fallback letter applies. The 16 pass-2 voter replies ran 19 to 256 completion tokens; 5 hit the 256 cap.
  - The actor then ran commands and submitted an empty patch: the 1 empty patch of 8.
- **The `nudges` counter missed this nudge.** `analyze_traces.py` reports 0 nudges although the trace has one `continuation_nudge` step. This is the counter defect already reported during EXP-038: it looks for user-sourced text markers, while the harness records nudges as system events.
- **A prompt above the threshold with no compaction.** fastapi_14448 reached a 23,720-token prompt with `compactions` 0. That is a note on the counter or on compaction timing, for the lead; it is not read here.
- **A channel-marker leak.** One proposer reply (fastapi_14605) has a thinking-channel marker leaked into its visible text, followed by a repeat of its first candidate. `tally.candidate_letters` still found 4 distinct letters.
- **Where the extra time went.** The proposer stage took 10 to 55 s per task; the 16-voter burst took about 1 s on 7 of 8. Most of V1's added wall over EXP-033 is the proposer [I, by stage stamps].

### 9.9 Votes by voter temperature, 2026-11-05 (post-hoc, not pre-registered, no reading applied)

**Why this is here.** The user asked what a re-run of the vote with every voter at 0.7 or above would give. The figures below describe this one run. They are exploratory, they change no row of section 4 or its application in 9.4, and they license nothing in section 5. The lead looked first, read-only. I recomputed every figure independently and they match the lead's.

**Source.** `python -I -X utf8 experiments/EXP-040/posthoc_temperature.py`, which writes `experiments/EXP-040/posthoc_temperature.json`.
- It uses pass 1 of each trace, segmented by `analyze_results.extract_rounds_contiguous` and scored by `tally.score_round`.
- The winner is the tally winner. It was decided by majority on 8 of 8 tasks.
- All 128 pass-1 votes parse.

**Picks in voter order, voters 1 to 16** (temperature 0.20 + 0.08 (k - 1)):

| Task | C | Picks, voter 1 to 16 | Winner | Voters against the winner |
|---|---|---|---|---|
| fastapi_14301 | 4 | BBBBBBBBDBBBBBBB | B | 9 |
| fastapi_14448 | 1 | AAAAAAAAAAAAAAAA | A | none |
| fastapi_14605 | 4 | AAAAAAAAAAAAAAAA | A | none |
| httpx_3672 | 4 | BBBBBDBABBBBCBBA | B | 6, 8, 13, 16 |
| requests_7205 | 4 | AAAAAAAAAAAAAAAA | A | none |
| requests_7309 | 4 | CCCBCBCCCCCBCCCC | C | 4, 6, 12 |
| rich_3006 | 4 | AADADDADAAAADADA | A | 3, 5, 6, 8, 13, 15 |
| rich_3468 | 1 | AAAAAAAAAAAAAAAA | A | none |

Voter 1 (0.20) picked the winner on 8 of 8.

**Votes against the winner, by temperature bucket, on the 6 tasks with C = 4.** The 2 tasks with C = 1 add voters but cannot add a vote against the winner.

| Bucket | Voters | Against the winner |
|---|---|---|
| 0.20 to 0.60 | 1 to 6 | 6 of 36 |
| 0.68 to 1.00 | 7 to 11 | 3 of 30 |
| 1.08 to 1.40 | 12 to 16 | 5 of 30 |
| all | 1 to 16 | 14 of 96 |

By task, the 14 votes split as fastapi_14301 1, httpx_3672 4, requests_7309 3 and rich_3006 6. In this run, the lowest bucket did not agree with the winner more than the two higher ones.

**The figure that bears on the user's question.** This is a descriptive figure from one run.
- For each task, take the fraction of the 16 voters whose pick differs from the winner:
  - 0.0625 on fastapi_14301;
  - 0.25 on httpx_3672;
  - 0.1875 on requests_7309;
  - 0.375 on rich_3006;
  - 0 on the other 4.
- The sum over the 8 tasks is **0.875**. That is the expected number of tasks with D true if voter 1 were one of the 16 chosen at random rather than the 0.20 voter, with the 16 votes held fixed. With a unique plurality on every task, the winner does not change when voter 1 does.
- So, even with the anchor voter drawn at random, these votes would give D true on fewer than 1 task of 8 on average. The zero D in row 2 does not depend on voter 1 being the coldest voter.
- This does not predict a new run with every voter at 0.7 or above. A re-run would draw new votes from the same 4 candidates, and the bucket rates above, 3 of 30 and 5 of 30, come from 10 voters on 6 tasks.
