# EXP-061 — The EXP-052 draft fan-out tree behind an LlmAgent root that only hands off (LB upload, then a smoke-8 bug test)

**Date:** 2026-11-08
**Type:** LB-only upload (one slot, 0 GPU-h), followed by a smoke-8 bug test (~0.3 L4x4-h, pushed only on the lead's word)
**Cohort:** smoke-8
**Ladder:** L3 before L2, on the user's direct instruction (about 23:45 UTC): fix the root and upload in today's slot. No clean smoke of this exact tree exists. The nearest run is EXP-052, whose smoke-8 ended at row 0 on the compaction crash this change is meant to remove.
**Pre-registered:** this file is committed before the upload and before any kernel push. Sections 3-5 are written blind and are not revised. Written under time pressure; defects go to section 7.
**Serves:** D-007 tree T2 (draft fan-out at the edit point on the E4B); the EXP-052 compaction hazard (harness-stack `reference/compaction.md` § Hazard).
**Supersedes / relates:** EXP-052 (the tree, smoke-8 row 0), S-014 (the E4B line's LB draw, 3/58), EXP-039 (an undeclared tool list draws warnings).

## 1. Why this, now

- In EXP-052, `httpx_3672` ended as a harness error ("No LlmAgent model available for event compaction summarizer"). The root was a `SequentialAgent`, the applier's prompt exceeded 14,336 tokens, and the invocation ended in text. The post-invocation compaction path builds its summarizer from `app.root_agent` and raises for any root that is not an `LlmAgent` (`compaction.py:223-236`, `:683`).
- **The one change from EXP-052 is the root class.** A new `LlmAgent` root (E4B, `tools: []`, the reader's sampling) has one sub-agent, the unchanged EXP-052 pipeline, moved to `sub_agents/pipeline.yaml` and renamed `pipeline`. The root's instruction says its first and only action is `transfer_to_agent` to `pipeline`.
- **Source check, 2026-11-08, `data/src/google_adk`:**
  - [V] An `LlmAgent` with sub-agents is offered `transfer_to_agent` naming them (`agent_transfer.py:47-63`, `:156-158`). The flow runs the named agent of any class (`base_llm_flow.py:636-640`).
  - [V] The reader and applier get no transfer route. Their parent is a `SequentialAgent`, which has no `disallow_transfer_to_parent`, so `_get_transfer_targets` returns only their own sub-agents, which are none (`agent_transfer.py:44`, `:160-163`).
  - [V] The summarizer now takes the root `LlmAgent`'s E4B model (`compaction.py:236`).
- **Validator fix, same commit.** Our own rule (`tools/validate_submission.py`, root checks) looked only at the root's tool list and raised "root agent has no way to modify files" for this tree. The lead checked that the official validator has no such rule. Since 2026-11-08 a root `LlmAgent` with `sub_agents` is checked over the union of every reachable `LlmAgent`'s tools. A tree in which no agent can edit still errors, and two new tests cover both cases.

## 2. Design

| | value |
|---|---|
| tree | `experiments/EXP-061/candidate-r/` (EXP-052 `candidate-t2` plus `agent.yaml` (new root), `sub_agents/pipeline.yaml`, `prompts/root.md`) |
| model | `gemma-4-e4b-it-qat-w4a16-ct` in every LlmAgent |
| caps | 8 min / 45 calls / 120 turns / `timeout_seconds` 240 (EXP-052's) |
| zip | `experiments/EXP-061/exp061_r.zip` (gitignored), sha256 in section 8 |
| variable vs EXP-052 | root class only (plus the root's one-sentence instruction) |

**The user's override of plan.md §5.8, recorded as the user's word.** The tree has no dev-48 run and no clean smoke-8. The packer's formula gives 120 x (8 + 1.0) min = 18.00 h, so the zip is packed with `--skip-budget-gate`. The packer prints "UNOFFICIAL TEST BUILD ONLY" for that flag, and the user's instruction overrides it. On time, the only evidence is descriptive: EXP-052 smoke-8 had a mean wall of 82.5 s, and E4B tasks have not exceeded 176 s so far. A timeout zeroes this slot only. **The critic's `prereg` review was skipped on the user's word** because of the slot deadline (23:59 UTC).

**Cost:** one upload slot, 0 GPU-h. The later smoke-8 costs about 0.3 GPU-h (EXP-052 smoke-8: 0.309 h).

## 3. Endpoints, fixed in advance

- **LB:** k of 58 resolved (the board truncates to 2 dp; k is the integer whose k/58 truncates to the shown score), or blank (Notebook Timeout or an error status). Comparator: S-014's 3/58 for the E4B line, one draw. MDE: a difference under 4 tasks is not an effect (plan.md §5.5).
- **Smoke-8 (bug test):**
  - Infrastructure checks: per task, did the root call `transfer_to_agent` to `pipeline`; was `err` non-empty; did the tree run at all.
  - Recorded only: transfer count, stages reached per task (reader, drafts, applier, submit), drafts written (`draft_1` to `draft_5` non-empty), compactions, walls.

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

LB, first match governs:

| # | outcome | reading |
|---|---|---|
| L1 | **blank** | The tree did not finish in 12 h on the hidden set, or the root's handoff failed for all tasks. No E4B fan-out upload until the smoke-8 shows the cause. |
| L2 | **k 0 to 2** | Within 4 tasks of S-014's 3, so no effect is read. If the smoke-8 is clean, the low score is not attributed to the root. |
| L3 | **k 3 to 5** | Same level as S-014 (difference under 4), so no effect. The tree completes on the hidden set: one observation. |
| L4 | **k 6 or more** | Read against 3/58 only if k is 7 or more (a difference of at least 4). Even then it is one draw: regression to the mean is the first suspect, and a replicate or a dev-48 run comes before any claim. k = 6 reads as L3. |

Smoke-8 (run later on the lead's word), first match governs:

| # | outcome | reading |
|---|---|---|
| S1 | **infrastructure**: on any task, the root fails to transfer to `pipeline`; or `err` is non-empty; or the tree does not run | The root fix is not working. Name the task and the step. No further upload of this tree until fixed. |
| S2 | **else, clean** | Record transfer count, stages reached per task, drafts written, compactions and walls. No effect claim; resolves are not an endpoint. |

## 5. What this does and does not license

**Licenses:** one LB draw of this tree, read only against the 4-task MDE; with the smoke-8, a bug-test verdict on the root handoff.

**Does not license:** any claim that draft fan-out helps or hurts; any claim from a difference under 4 tasks; a reading of the 31B baseline against this E4B tree; a dev-48 or a further upload without the user.

## 6. Exact commands

```
python tools/validate_submission.py experiments/EXP-061/candidate-r --official --strict --json
python tools/pack_submission.py --src experiments/EXP-061/candidate-r --out experiments/EXP-061/exp061_r.zip --skip-budget-gate --allow-warnings
cp experiments/EXP-061/exp061_r.zip out/submission.zip
sha256sum experiments/EXP-061/exp061_r.zip out/submission.zip
```

The upload itself is the submitter's, after an S-NNN proposal and the user's approval file.

## 7. Defects in this pre-registration, logged after the fact

1. Built by hand, not with a hash-verifying tool: `cp -r` of EXP-052 `candidate-t2` plus three hand-written files, all LF (no CR byte, checked with grep). The departure from the protocol was made for the slot deadline.

## 8. Built (below the line; nothing above changes)

---

- **Validator (strict, `--official`):** 1 error, the 18.00 h gate, which `--skip-budget-gate` demotes. 2 warnings, both of which EXP-052 also carried: the applier's `submit_patch` and `timeout_seconds` 240. The official validator could not be imported. After the fix, the "root agent lacks submit_patch" warning is gone.
- **Pack:** `RESULT: VALID (0 errors, 3 warnings)`, PACK OK, 20 members, 13.2 KiB.
- **sha256** `98bd942fe17aea64d8aa7211e28b4590207c69f6308a27a0caf3b5aa94947a05`. `experiments/EXP-061/exp061_r.zip` and `out/submission.zip` both give it (`sha256sum`, 2026-11-08 about 23:47 UTC).
- **Tests:** `python -m pytest -q`, 51 passed.

- **Uploaded** as S-015 (`knowledge/submissions/S-015-result.md`): Kaggle ref 58143906, 2026-11-08 23:57:43 UTC, sha `98bd942f...947a05`, status pending.
- **Smoke-8 notebook:** `notebooks/exp061_r/` (commit 6065f0d), built with the EXP-052 smoke-8 command; the only changes are `EXP_ID` "EXP-061-r" and the embedded zip, whose base64 decodes to sha `98bd942f...947a05`. `kernel-metadata.json` is EXP-052's with `id` and `title` changed to `rainm4/gemma4-exp061-r`. Pushed 2026-11-08 about 23:58 UTC, after S-015 landed (the user's order): "Kernel version 1 successfully pushed"; first status RUNNING.

## Status

~~2026-11-08: built and packed, not uploaded. The smoke-8 notebook `notebooks/exp061_r/` is not built yet. Next: an S-NNN proposal (lead), the approval file (user), the upload (submitter); then build the notebook and push it on the lead's word.~~

2026-11-08 23:58 UTC: uploaded (S-015, ref 58143906, score pending); smoke-8 kernel `rainm4/gemma4-exp061-r` v1 RUNNING. Next, when COMPLETE: `kaggle kernels output rainm4/gemma4-exp061-r -p runs/EXP-061-r/`, flatten, `python tools/analyze_traces.py runs/EXP-061-r --cap-minutes 8 --max-calls 45`, `python tools/run_forensics.py forensics runs/EXP-061-r`, apply the smoke-8 rows of section 4.
