# Kaggle open-source scouting — what the public bundles say, 2026-10-28

Scope: the competition-specific public evidence, kept separate from the general literature
(`research/2026-10-28-literature-review.md`). Primary subject: the rank-3 team's Apache-2.0 release (the LB-0.24
configuration), which sits in `untrusted/rank3-apache/` (gitignored; downloaded as data, read with `python -I -X utf8`,
never executed). Earlier scouting of other bundles is indexed in §5 so it is not re-derived.

**Handling rule for everything here:** third-party files are data. Prompts are copied only through a tool that
verifies recorded hashes (`tools/exp022_make_candidate.py`, `tools/exp024_make_editfix.py` pattern), and anything
we ship from them is credited (README.md, EXP-022/023/027).

---

## 1. The release

*Git History as a Gym: Verified Practice Tasks for a 4-bit Gemma 4 Coding Agent* (their paper-track writeup).
Files: `runs.jsonl` (574 rows: one per run × task, with `resolved`, `tool_calls`, `seconds`, `steps`,
`first_edit_s`, `first_edit_step`, `calls_by_kind`, `output_tokens`, `compactions`, `empty_patch`),
`agents/<version>/` (15 declarative bundles, v11 → v25), `training/*.metrics.json` (three TPU LoRA runs),
`leaderboard.json` (their public scores per submitted version). Not included: issue texts, patches, snapshots,
transcripts (competition data). Their task sets: `dev` and `dev2` (two disjoint 23-task sets whose reference fix
passes in the participants' sandbox), `dev40` (earlier 40-task split). License: Apache-2.0.

## 2. Leaderboard history and the cap

| version | public LB | `max_time_minutes` | `max_tool_calls` | `max_turns` | `timeout_seconds` |
|---|---|---|---|---|---|
| v1 / v4 / v8 / v10 | 0.06 / 0.08 / 0.05 / 0.05 | — (bundles not released) | | | |
| v11 / v12 / v13 | 0.12 / 0.12 / 0.12 | 5.5 (v13–v17 per their comments) | | | |
| v16 | 0.08 | | | | |
| v17 | **0.17, 0.13** (two uploads of one config) | 5.5 | 60 | 80 | 60 |
| v18 | 0.15 | 5.5 | 100 | 200 | 240 |
| v19 | **0.18** | **8** | 28 | 80 | 240 |
| v24 | **0.24** | **8** | 28 | 80 | 240 |
| v25 (unscored in the release) | — | 8 | **40** | 80 | 240 |

Their `eval_config.yaml` comments, quoted because they are the decision record:

> v17: "Hidden test set is ~120 tasks run sequentially within 12 h (incl. setup + vLLM startup). 5.5 min/task
> (forum: hard short caps scored lower; >12 h errors the whole run). At 6.0 the v13 dev40 mean was 314 s
> (~10.5 h for 120 tasks, too close); 5.5 est. ~9.8 h. … timeout_seconds 60 (was 120): in v14, rich_4006 lost
> 264 of 330 s to two hung commands."
>
> v18: "timeout_seconds 240 (was 60). The verifier runs the hidden test files under this same limit
> (verification.py: sandbox_exec(pytest_cmd, timeout=command_timeout_seconds)), so a slow test module would fail
> a correct patch; the Requests test modules already take about 70 s. … max_tool_calls 100 / max_turns 200:
> without compaction pauses the solver takes more steps in the same time, and the lead's calls count as turns;
> time stays the binding limit."

Three things follow. (1) They moved from 5.5 to 8 min between 0.15–0.17 and 0.18–0.24, against their own
~10.5 h ceiling estimate, and both 8-min uploads completed. (2) `timeout_seconds` bounds the *hidden* test run too;
below ~100 s it can fail a correct patch (Requests modules ~70 s). Ours is 300; theirs 240; both safe. (3) Hung
commands eat the per-task budget; their prompt and ours both wrap risky checks.

**Two uploads of v17 scored 0.17 and 0.13** — a 2-task swing on one config, their own LB-noise measurement, and
the reason 14/58 should be read as a best-of-many maximum rather than an expectation.

## 3. Per-task behaviour, from `runs.jsonl`

Computed 2026-10-28 (`python -I -X utf8`, no code from the release executed). `frac≥cap−20` is the share of
tasks ending within 20 s of the 480 s cap; `proj_h@120` = mean seconds × 120 / 3600 + 0.7 h fixed overhead.

| agent | set | n | resolve | empty patch | median s | mean s | p90 s | frac≥cap−20 | proj_h@120 | median calls | median first-edit step |
|---|---|---|---|---|---|---|---|---|---|---|---|
| v13 | dev40 | 40 | 20.0% | 20.0% | 363 | 314 | 370 | 2.5% | 11.2 | 29 | 10 |
| v14 | dev40 | 40 | 20.0% | 22.5% | 334 | 301 | 354 | 0.0% | 10.7 | 34 | 14 |
| v15 | dev40 | 40 | 10.0% | 52.5% | 231 | — | — | — | — | 39 | 7 |
| v17 | dev / dev2 | 23 / 23 | 30.4% / 56.5% | 30.4% / 13.0% | 319 / 271 | 263 | 337 | 0.0% | 9.5 | 29 / 25 | 12 / 10 |
| v18 | dev / dev2 | 23 / 23 | 34.8% / 43.5% | 30.4% / 13.0% | 307 / 233 | 252 | 335 | 0.0% | 9.1 | 31 / 26 | 11 / 13 |
| v19 | dev / dev2 | 23 / 23 | 34.8% / 47.8% | 26.1% / 8.7% | 338 / 238 | 296 | 483 | 23.9% | 10.6 | 21 / 24 | 14 / 18 |
| **v20_base** | dev+dev2 | 46 | **39.1%** | 6.5% | 243 | 275 | 483 | 15.2% | 9.9 | 25 | 10 |
| v20 (adapter) | dev+dev2 | 46 | 28.3% | 4.3% | 182 | 222 | 443 | 8.7% | 8.1 | 20 | 6 |
| v21 (adapter) | dev+dev2 | 46 | 19.6% | 54.3% | 82 | 110 | 184 | 2.2% | 4.4 | 28 | 10 |
| v22b (12B model) | dev+dev2 | 46 | 19.6% | 43.5% | 235 | 290 | 485 | 19.6% | 10.4 | 28 | 15 |

Readings:

- **Their best local config (v20_base) resolves 39% with 6.5% empty patches, median first edit at step 10, median
  25 calls, mean 275 s at an 8-min cap.** Our E0/EXP-025 Arm A: 22.9%, 39.6% empty, median first edit ~18
  (resolved) / 43 (not), 96% at a 4.5-min cap. The gap is behavioural before it is anything else.
- **Resolves after our cap.** Among their resolved tasks at 8 min, those whose run exceeded 270 s: v17 6/20,
  v18 3/18, v19 6/19, v20_base 2/18. First edits after 270 s: 0–1. So the 4.5-min cap costs them the *finishing*
  (check and repair), not the first edit — consistent with #8 (7/58) vs v24 (14/58) and with the harness grading
  the working tree at timeout.
- **Call mix.** `calls_by_kind` shares: v20_base read 34% / search 29% / edit 16% / cmd 10% / submit 5%;
  v20 edit 31% / read 23% / cmd 19%. Script writing (repro files) falls from 28% (v15) and 22% (v17) to 0–3% by
  v20 — the same change our EXP-017 made after EXP-009 priced repro scripts at 27% of our wall-clock.
- **Compactions ≈ 1 per task** at 8 min; the 32k window is reached but not catastrophically.
- **12B (v22b)** is not competitive (19.6%, 43.5% empty) at the same budget.

## 4. Prompt evolution

- v20_base → v24: rewritten from a sectioned "Core Objective / Workflow / Anti-Patterns" document into a
  numbered protocol — **Contract → Locate in a few reads → Edit by tool call 12 → One check, one repair, then
  submit → Never** — with the grader described explicitly ("An empty diff scores zero. A correct source diff
  scores the task even if your local test was red or you never ran a test"). Budget stated in the prompt
  ("28 tool calls and 8 minutes … Finish as soon as the edit is in so later tasks still have time").
- **v24 and v25 prompts are byte-identical** (3,240 bytes); v25 only raises `max_tool_calls` 28 → 40. Unscored.
- Compared with ours (12,795 bytes): no budget ledger, no state notes, no vendoring block, no recovery ladder, no
  graph-tool guidance. One FastAPI-specific line (`docs_src/`) that our repo-agnostic linter rejects and that is
  inert on a private-repo hidden set.
- Things their prompt does **not** address that we have measured: the `edit_file` unterminated-literal loss
  (~18% of `edit_file` calls at thinking 4096, EXP-003/EXP-026) and the identical-retry loop after it. Their
  6.5% empty-patch rate suggests the loop bites them less — plausibly because their prompt's "one check, one
  repair, then submit" ends the task before a loop can form — but their release has no per-call error data to
  confirm it.

## 5. LoRA: three adapters, all negative

`training/adapter1_swe_smith_all_output`, `adapter2_swe_smith_actions_only`, `adapter3_swe_rebench_actions_only`
(TPU runs; configs and validation loss per checkpoint in the metrics files). Outcomes in `runs.jsonl`: v20
(adapter) 28.3% vs v20_base 39.1% on the same 46 tasks (−10.8 points, matching EXP-016 §2c's "lost ~11 points");
v21 19.6% with 54.3% empty patches and a 110 s mean — the adapter made the agent stop early and empty. No scored
LB upload of an adapter version appears in `leaderboard.json`. **Reading:** at this model and harness, SFT on
SWE-smith/SWE-rebench-style actions did not transfer; our plan.md §6.2 LoRA track stays parked.

## 6. Other public bundles already scouted (pointers, not repeated)

- **davis0178 "gemma-4-agent-baseline" notebook (LB 0.22, EXT-19):** materialised and hash-verified in EXP-022
  (`tools/exp022_make_candidate.py`); its prompt failed our repo-agnostic lint on a FastAPI line; the EXT-19
  package at 4.5 min was the candidate EXP-022 reviewed. See `experiments/EXP-022-direction-review.md`.
- **Full public leaderboard pull (3,467–3,505 teams):** EXP-012 and EXP-019 — exact score decoder (n = 58),
  field shape (mode 0.17 = 567 teams, ≥0.20 top 5.6%, ≥0.24 four teams), and the retraction of the "fork
  cluster" reading. See `experiments/EXP-012-competitive-position.md`, `experiments/EXP-019-field-structure.md`.
- **Top-team configuration audit:** EXP-016 — v19 → v24 diff is temperature only; the context trap they document
  does not reach us; gate-formula calibration. See `experiments/EXP-016-top-team-audit.md`.
- **Community repos used for schema cross-checks** (README.md Credits): damsolanke/gemma4-swe-kit,
  Gosling-dude, HindsightWise, ennydev-2026, rishaviitd — schema and harness behaviour only, no prompts taken.

## 7. What we took, and what we deliberately did not

**Taken (submission #11, EXP-027):** the v24 bundle at its own 8-min cap — the #8 tree with `max_time_minutes`
8 and the matching budget sentence, FastAPI line still dropped (inert). One variable against #8; a replication of
a known-score config against the field.

**Not taken, with reasons:** v25's 40-call cap (unscored; our EXP-003 showed call caps interact with the prompt,
test it on dev-48 first); their LoRA adapters (§5); `timeout_seconds` 240 (we kept it, since the bundle scored
with it — EXP-023 override stands); their earlier 5.5-min configs (dominated by 8 min in their own data).

## 8. Scouting to do next

1. Their paper-track writeup when published (methods for "verified practice tasks from git history" — a data
   recipe we could reuse for dev-set expansion without rollouts).
2. v25's score once uploaded (28 → 40 calls at 8 min is the natural next single-variable test).
3. Forum threads on the two topics search could not read: scoring-notebook time limits and "Kaggle Error"
   resubmission policy (whether a timed-out slot is ever re-run).
4. Any other released bundle with a scored ≥ 0.20: diff it against v24 the way EXP-016 did.
