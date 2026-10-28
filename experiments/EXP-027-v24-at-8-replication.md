# EXP-027 — The rank-3 v24 bundle at its own 8-minute cap: submission #8 with one variable changed

**Date:** 2026-10-28
**Type:** LB-only, zero GPU. A single-variable follow-up to submission #8 (EXP-023), and a replication of a
public Apache-2.0 configuration that scored 0.24 on this hidden set.
**Pre-registered:** this file is committed **before** upload. Sections 3–5 are written blind and are not revised
after the score; a badly drafted reading gets its defect logged in §7, not rewritten.
**Serves:** the main-track score (the first draw whose expected value sits above our best, 8/58), the
budget-model question that has pinned `max_time_minutes` at 4.5 since submission #2, and the paper track
(a replication of a known-score config is the only clean LB-noise measurement available to anyone).
**Supersedes for the LB lineage:** the 12,795-char `submission/prompts/swe_coder.md` lineage (#1–#10). EXP-026
Arm C is unaffected as a dev-48 experiment but is no longer the LB-facing question; see §6.

---

## 1. What changed in the evidence today

Three things, each from data already on disk, none from a new run.

**(a) Submission #8 vs its source is the largest contrast in the record, and it is a one-variable contrast.**
#8 (EXP-023) shipped the rank-3 team's v24 bundle byte-for-byte except three edits: `max_time_minutes` 8 → 4.5
(E1), the prompt's budget sentence to match (E2), and one FastAPI `docs_src/` bullet our linter rejects (E3,
inert on a private-repo hidden set). #8 scored **7/58**. Their v24 scored **14/58** on the same 58 tasks.
Fisher two-sided p = 0.147: not significant at our ~4-task MDE, but a 7-task gap on a one-variable diff is not
something nine draws of prompt surgery ever produced (series 4, –, 7, 6, 8, 8, 7, 7, 6, 6).

**(b) The team's own release says the cap was their lever, in their own words.** `untrusted/rank3-apache/agents/*/
eval_config.yaml` carries their reasoning: v13–v18 ran **5.5 min** ("forum: hard short caps scored lower; >12 h
errors the whole run. At 6.0 the v13 dev40 mean was 314 s, ~10.5 h for 120 tasks, too close; 5.5 est. ~9.8 h")
and scored 0.12–0.17; v19 and v24 moved to **8 min / 28 calls** and scored 0.18 and 0.24. Their per-task
`runs.jsonl` at 8 min: mean **275–296 s** (v20_base, v19), 15–24% of tasks at the cap, and **2–6 of their 18–20
resolves per 46-task set finished after 270 s** — the point where our 4.5-min cap kills a task.

**(c) Our 11.0 h gate formula is calibrated on *our* prompt, not theirs.** EXP-016 §3 found `cap × 120` accurate to
4% because **79.2% of E0 tasks run to the cap** (EXP-025 Arm A: 95.8%). With their 3,240-byte prompt the agent
stops on its own on 76–85% of tasks, so the same formula overstates by ~45%: 8 min gives a nominal 18.0 h and a
projected actual of **9.9–10.6 h** (mean 275–296 s × 120 + 0.5–0.7 h fixed overhead). Submission #2 died at a
projected 11.34 h; E0 completed at 8.61 h. Their v19 **and** v24 completed at 8 min on this hidden set, which is
an existence proof no projection can beat.

## 2. Design

One artifact, one variable against #8.

| | submission #8 (EXP-023) | **this (#11)** | rank-3 v24 (LB 0.24) |
|---|---|---|---|
| prompt | v24 minus `docs_src/` bullet, "4.5 minutes" | v24 minus `docs_src/` bullet, **"8 minutes"** | v24 |
| `max_time_minutes` | 4.5 | **8** | 8 |
| `max_tool_calls` / `max_turns` / `timeout_seconds` | 28 / 80 / 240 | 28 / 80 / 240 | 28 / 80 / 240 |
| sampling | T 1.0, top_p 0.95, top_k 64, 8192 out, thinking 4096 | same | same |
| tools | the 6 | the 6 | the 6 |

Build: `experiments/EXP-027/candidate-v24-at-8/` = `experiments/EXP-022/candidate-v24/` with E1 and E2 reverted
(each anchor matched exactly once, or the build aborts). `diff -r` against the #8 tree shows exactly those two
lines; `diff` against `untrusted/rank3-apache/agents/v24/` shows exactly the E3 bullet. Packed with
`--skip-budget-gate` (the only path through the 11.0 h formula; the flag demotes the gate to a warning and is
what the record reads as the override). Artifact sha256 and member list are in §8.

**Gate override, recorded as `plan.md` §5.8 requires.** The rule "never submit a config that has not run on dev-48
with projected worst case ≤ 11 h" is overridden knowingly. Justification, in order of weight: (1) this exact
bundle, at this cap, completed and scored twice on this hidden set (v19 0.18, v24 0.24); (2) the team's measured
per-task means project 9.9–10.6 h against a ~10.5 h calibrated ceiling; (3) the one prior override, #2, was a
different prompt whose dev-48 median was 342 s with 18 of 48 tasks ending on a 28-call cap, i.e. an agent that
did not stop on its own — the failure mode this prompt was written to prevent. Risk accepted: a timeout scores
**zero for this slot and nothing else**; the LB keeps our 0.13.

## 3. Endpoints, fixed in advance

Primary: public LB tasks resolved, k of 58. Secondary: whether a score returns at all (the budget question).
There is no dev-48 arm attached to this upload; the paired dev-48 arms that test *additions* to this tree are
pre-registered separately (§6).

**Expected value, stated before the score.** Their 0.24 is the maximum of ≥ 12 uploads, and their own v17 scored
0.17 and 0.13 on two uploads of one config, so 14 is selection-inflated. `submissions.md` row 7 (after the
2026-10-25 retraction) put the honest target for this config at **theta ≈ 10 (+3.3 over our 8/58)** once the
best-of-N advantage is removed. Expected k ≈ 10, 2.5-sigma band roughly 6–14.

## 4. Pre-registered readings. Written blind. Not to be revised after the score.

Rows 1–4 are applied in order; the first match governs.

| # | outcome | reading |
|---|---|---|
| 1 | **Blank / Notebook Timeout** | The budget model for *this* prompt on the hidden set is wrong, or their two completions sat inside variance we cannot see. Record it. Next slot: this prompt at **6.0 min** (their own v13 figure: 314 s mean ≈ 10.5 h), no further override above that without a dev-48 time profile. Cost: one slot. |
| 2 | **k ≤ 8 (≤ 0.13)** | The cap is not the lever on the hidden set; the 7-vs-14 gap was noise plus their selection. Still adopt this tree as the LB baseline: it completed at 8 min (budget question answered) and is 4× shorter than ours with the same resolve on our side. Next lever is edit reliability on top of it (§6), not time. |
| 3 | **k = 9–10 (0.16–0.17)** | Consistent with theta ≈ 10. **Adopt as the baseline tree**; every later arm is paired against it. Do not call it a time effect — a one-draw +1 to +2 is inside the MDE. |
| 4 | **k ≥ 11 (≥ 0.19)** | **Adopt, and re-run it unchanged in the next slot** before any addition, because regression to the mean is the first thing to rule out (EXP-023 row 4, unchanged). Two draws of one config is also the LB-noise measurement the paper needs. |

Additive: **if k ≥ 9 and `submissions.md` later shows our 12.8 KB prompt never beat 8**, the lineage question is
closed in favor of the short prompt and no further slot goes to `prompts/swe_coder.md` as shipped.

## 5. What this does and does not license

**Licenses:** a statement about whether `max_time_minutes` 8 vs 4.5 moves the hidden-set score for this prompt
(one draw, inside-MDE caveats as in §4); a statement about whether the 8-min budget completes on the hidden set
with this prompt; adoption of a baseline tree.

**Does not license:** any claim that *we* improved on the public config (we did not; this is a replication with
one inert line removed); any claim about *why* 8 min helps (more time to finish, or the different stopping
behavior the prompt induces — they ship together); any generalization to our own prompt at 8 min (EXP-003 is the
counter-example); any resolve-rate claim at dev-48 scale.

**Stated plainly for the record and the paper:** the bundle is the rank-3 team's, Apache-2.0, credited in
`README.md` and EXP-022/023. What is ours is the measurement — a known-score config re-drawn on the same hidden
set, and the one-variable contrast with #8.

## 6. What follows, regardless of row

The research pass that preceded this is recorded in `research/2026-10-28-literature-review.md` (academia and
industry) and `research/2026-10-28-kaggle-open-scouting.md` (the team's release and other public bundles). It
points at four things on top of a short, early-committing prompt, in priority order:

1. **Our verified lost-edit route.** The `edit_file` failure (200/201 lost calls end in `ng:`, an unterminated
   string literal; EXP-026 §1) is not addressed by their prompt. At thinking 4096 it still costs ~18% of
   `edit_file` calls on ~4 of 48 tasks (EXP-003). A **short** recovery section (the heredoc template, no ledger)
   is the first paired dev-48 arm on this tree: Arm R (this tree) vs Arm RH (this tree + recovery), same 48 ids.
   External corroboration: vLLM gemma4 parser issues #38910 / #42696 report streamed tool arguments being
   corrupted; a single-argument `run_command` route is the declaratively reachable workaround.
2. **`max_tool_calls` 28 → 40** (their unscored v25) once time is known to complete; EXP-003 showed 28 binding on
   *our* prompt (20/48 at cap, 0 resolves), their median is 20–25 calls.
3. **Cap tuning from a measured mean on dev-48** (7 / 8 / 9 min), not from the `cap × 120` formula, with the fixed
   overhead measured in the same run.
4. **Parked, with reasons:** LoRA — their three adapters (SWE-smith, SWE-rebench recipes) all *lost* ~11 points
   locally (v20 28.3% vs v20_base 39.1%); best-of-N — the only use of the 88.6% idle KV capacity, but no
   selection proxy without hidden tests (Agentless / Nemotron-Cascade select on regression and self-written
   reproduction tests, which costs the time we do not have); graph tools — lose to grep at every k.

EXP-026 Arm C (our heavy prompt + heredoc) stays pre-registered but drops in priority: if row 2–4 fires, the
prompt it tests is no longer the one we ship, and the recovery mechanism is better tested as Arm RH above.

## 7. Defects in this pre-registration, logged after the fact

None yet.

## 8. Built and submitted

Filled at pack and upload time, below the line. Nothing above it changes.

---

**Built 2026-10-28 ~22:30 UTC** from `experiments/EXP-022/candidate-v24/` with the two anchored reverts
(each matched exactly once). `diff -r` against the #8 tree: `eval_config.yaml` line 4 (`4.5` → `8`) and
`prompts/system.md` line 6 (budget sentence). `diff` against `untrusted/rank3-apache/agents/v24/`: the one
dropped `docs_src/` bullet; `eval_config.yaml` identical to theirs.

Validator (`--strict`): **INVALID, 1 error, 1 warning** — the error is the gate line
`worst case 120 x (8 + 1.0 setup) min = 18.00 h (gate 11.0 h, limit 12.0 h) -> EXCEEDS the packing gate`; the
warning is `timeout_seconds=240 < 300 may also cap the grading pytest run` (accepted in EXP-023 §2, unchanged).
Instruction chars 3,162.

Packed with `--skip-budget-gate` (implies `--allow-warnings`) to `experiments/EXP-027/v24_at8.zip`, re-validated
as an archive, 4 members (`agent.yaml`, `configs/sampling.yaml`, `eval_config.yaml`, `prompts/system.md`),
2.3 KiB, **sha256 `c22069db6623a07c9f133fef33a8c193393dca170c84676e708d0bd9f5077600`**. Copied byte-identical to
`out/submission.zip` (verified by `sha256sum` on both).

**Pre-registration commit `de69156`** (this file at §1–§7 plus the candidate tree), made before upload.

**Kaggle submission ref 57750294, accepted 2026-10-28 22:39:49 UTC**, uploaded as `submission.zip`
(`out/submission.zip`), first try, "0 submissions remaining today". Status PENDING at 22:40 UTC. §4 governs how
the score is read; `submissions.md` row 11 carries the same record.
