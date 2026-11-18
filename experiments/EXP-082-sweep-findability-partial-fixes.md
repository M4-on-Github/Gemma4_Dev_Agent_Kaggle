# EXP-082 — Sibling-site sweep, step 1: would a grep of the edited identifiers have found the gold regions a partial fix missed? (31B and E4B, zero GPU)

**Date:** 2026-11-17
**Type:** zero-GPU analysis (trace and patch mining over runs on disk, 0 GPU-h, no upload)
**Cohort:** none
**Ladder:** L1. It gates two L2 smoke-8 screens (EXP-083 for the 31B, EXP-084 for the E4B), which are built only for a model whose count reads GO (section 4).
**Pre-registered:** this file and `experiments/EXP-082/sweep_check.py` are committed before any count is made. Sections 2 to 6 are written blind and are not revised; a defect found later is logged in section 7.
**Serves:** idea 1 of `research/lit/2026-11-17-next-ideas-web-scout.md` (sibling-site sweep prompt rule), the user decision of 2026-11-17 in `knowledge/user-decisions.md` (fa03ed9): try it on both the 31B and the E4B, zero-GPU check first.
**Relates:** `research/lit/2026-11-17-run-synthesis-model-faults.md` (fault map: partial fix C is 13 and 11 of the 31B's losses in arms R and RH, and 8, 12, 9, 9 over the four E4B dev-48 draws), EXP-074 section 2.3 (`diag.classify`, margin 5), EXP-034 (`mine.py` patch parsing), EXP-080 section 6.1 (arm R reads E6 F3 R6 C14 S10 with 9 resolved), EXP-028 (arms R and RH), EXP-038, EXP-077, EXP-075, EXP-078 (the four E4B draws).

**What was already seen when these rules were written.** This list is complete.
- The synthesis note's counts above and the idea note's text, which names the rule and the first-pass test ("recoverable by a grep of the edited token").
- The source of `experiments/EXP-074/diag.py` and `experiments/EXP-034/mine.py`.
- The list of files in each run directory and the field names of `task_results.jsonl`, `summary.jsonl` and `experiments/EXP-036/summary.jsonl`. One 600-byte fragment of one agent patch (a task in EXP-028 arm R) was displayed by a `head -c` while checking the field names; it was not read for content and nothing was derived from it.
- No gold patch, no other agent patch, no trace and no count of any measure below.

## 1. Why this, now

Partial fixes are the largest 31B loss class (13 of 48 in R, 11 in RH) and the second-largest E4B class (8, 12, 9, 9 per draw). The idea is a prompt rule that makes the agent look for the other sites. The rule can only help if the missed sites are findable by the move it prescribes: search the repo for an identifier the agent changed and judge each hit. If the missed gold regions mostly contain no identifier the agent touched, the rule cannot reach them and no GPU is spent. This file counts that, per model, at 0 GPU.

## 2. Definitions (fixed before any count)

### 2.1 Unit: a partial-fix task-run
A task-run of the pool below whose exclusive class is **C** (`diag.classify`, margin 5, gold source files): the agent's patch touches some gold regions and not all.
- **Exclusive class order** (the synthesis note's): resolved as run, grader-impossible (`httpx_3672`, `requests_7205`, `requests_7309`, `requests_7315`, `requests_7427`; C-022), grading gap (31B arms only: `R_resolved_regraded` or `RH_resolved_regraded` true in `experiments/EXP-036/summary.jsonl` and not resolved as run), empty patch, then the `diag.classify` letter.
- **31B pool:** EXP-028 arm R (`runs/EXP-028-armR`) and arm RH (`runs/EXP-028-armRH`), 48 task-runs each. Expected C: 13 and 11, so 24 task-runs.
- **E4B pool:** `runs/EXP-038-e4b-dev48`, `runs/EXP-077-base`, `runs/EXP-075-t02`, `runs/EXP-078-t02r`, 48 task-runs each. Expected C: 8, 12, 9, 9, so 38 task-runs. No grading-gap exclusion (the EXP-038 re-grade found 0; the later draws have no re-grade).
- **Instrument check.** The script prints the exclusive C count per run against these expected values, and the raw class counts of arm R against E6 F3 R6 C14 S10 with 9 resolved (EXP-080 section 6.1).

### 2.2 Gold region, missed region
`diag.gold_regions(gold patch, margin 5)`: changed old-side lines of the gold source files, merged when 10 or fewer lines apart; a region is **touched** by a patch when a changed old-side line of the same file lies within 5 lines of it (`diag.touches`). A **missed region** is a gold region the task-run's patch does not touch (all regions of a gold file the patch does not name are missed).

### 2.3 Sweep-findable
A missed region is **sweep-findable** if the region contains an identifier that also appears on a line the agent's own patch changed.
- **Identifier:** a token `[A-Za-z_][A-Za-z0-9_]*` of 4 or more characters that is not a Python keyword (`keyword.kwlist` and `softkwlist`) and not a builtin name (`dir(builtins)`). Case-sensitive, whole token.
- **The region's text** is the old-side text of the gold patch for that region: its removed lines and its context lines whose old line number lies within 3 lines of the region's first or last changed line (the unified-diff context depth). This is what a grep run on the agent's finished tree would hit at the missed site, since the missed site still holds its old text. Added lines of the gold patch are not part of the region's text (new names do not exist yet).
- **The agent's changed lines:** every added or removed line of the agent's patch in a file that is not under `docs/`, `docs_src/`, `scripts/` or `tests/`.
- **Variants, all computed, one governs.**
  - **V0 (primary, the lead's definition as written):** as above.
  - **V1 (generic names removed):** V0 with `self`, `cls` and dunder names (`__name__` form) removed from both sides. `self` has 4 characters and is neither a keyword nor a builtin, so under V0 almost every method region matches on it; V1 shows how much of V0 is that.
  - **V2 (removed lines only):** V1 with the region's text restricted to its removed lines, so a region of pure insertions has no text and is never findable.

### 2.4 Counts, per model, over its pool
- **Primary:** the number of unit task-runs whose missed regions are **all** sweep-findable (V0), with at least one missed region (always true for class C). Beside it, the same under V1 and V2.
- **Secondary:** the number of unit task-runs with **any** missed region sweep-findable (V0, V1, V2).
- **Third count:** the number of right-file-wrong-region task-runs (exclusive class R, same exclusions) and, among them, how many have all regions sweep-findable under V0 and V1. Recorded only; not in the thresholds.
- Also recorded: distinct tasks behind each count, the per-run unit counts, and the number of unit task-runs whose region rows disagree with the class letter (must be 0).

## 3. Thresholds, on the primary V0 count (set by the lead's dispatch)

| model | pool (expected) | GO | DROP | between |
|---|---|---|---|---|
| 31B | 24 | 10 or more | fewer than 6 | 6 to 9 |
| E4B | 38 | 16 or more | fewer than 10 | 10 to 15 |

Pre-registered guard on V0: a model is **GO** only if its V0 count is at or above the GO threshold **and its V1 count is at or above its DROP threshold**. A V0 at or above GO with a V1 below DROP is read **between**. (Reason: section 2.3 on `self`.)

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Rows are per model (the two models are read independently). Row 1 is a gate; rows 2 to 4 are first-match.

| # | outcome | reading |
|---|---|---|
| 1 | **Instrument.** Any unit count differs from its expected value in section 2.1, or arm R's raw classes differ from E6 F3 R6 C14 S10 with 9 resolved, or any region row disagrees with its class letter, or the script errors | The counts are recorded and the verdict is **not read**; the lead decides whether the discrepancy is a defect of the instrument or of the expectation. |
| 2 | **DROP.** V0 primary below the DROP threshold | The sweep cannot reach enough of the missed regions on this model. The claim is dropped for this model at L1; no kernel. |
| 3 | **GO.** V0 primary at or above the GO threshold and V1 at or above the DROP threshold | One smoke-8 for this model (section 6), nothing more. |
| 4 | **Between.** Anything else | Counts and the per-task table go to the lead; no kernel is built. |

**Not rows, but binding:**
- Findability is an **upper bound** on what a sweep can reach (a hit is not a decision to change the site, and the model may answer "not needed" to every hit). A GO reads "worth one 8-task look", never "the rule will help".
- Resolves are not computed here.
- Counts are over task-runs; the R and RH arms (and the four E4B draws) overlap in tasks, so the distinct-task counts are recorded beside each count.

**Blind prediction.**
- 31B V0 primary about 11 of 24 (P(GO) about 0.5, P(DROP) about 0.15), V1 about 8; the V0 inflation from `self` and short generic names is the most likely way a GO turns into a between.
- E4B V0 primary about 14 of 38 (P(GO) about 0.35, P(DROP) about 0.2), V1 about 10.
- Row 1 about 0.2 for the first run of an untested script (a counting disagreement in the instrument check).

## 5. What this does and does not license

**Decides:** per model, whether one smoke-8 screen of the sweep rule is built (rows 3) or the claim is dropped for that model (row 2). Nothing else.

**Does not license:** a resolve claim, a dev-48 arm, an upload, or any statement about whether a model obeys the rule (that is what the smoke reads, on gold regions touched).

## 6. Exact commands, and the rule for step 2 (written before any count)

```bash
python -I -X utf8 experiments/EXP-082/sweep_check.py --out experiments/EXP-082/counts.json
```
It prints ids, counts and booleans only (plan.md:52) and writes the same to `counts.json`. Results are appended below as section 9, applying section 4 per model.

**If a model reads GO, its smoke-8 (EXP-083 for the 31B, EXP-084 for the E4B) is written before it is built, with these fixed here:**
- **One variable:** the sibling-site sweep rule in `prompts/swe_coder.md`: before the first edit list the change sites the issue implies; after the last edit search the repository for the identifier you changed and mark each hit "needs the same change" or "not needed". Repo-agnostic wording; no package, network, subprocess, mcp or URL words. Searching goes through `run_command`.
- **Bases:** 31B `experiments/EXP-027/candidate-v24-at-8/` (8 min, 28 calls, 80 turns unchanged); E4B the EXP-033 single-loop tree.
- **Cohort:** the 8 ids the script prints under "step 2 selection" for that model, written to a file under `experiments/cohorts/` and named in that EXP's `**Cohort:**` line. The rule the script applies, fixed now:
  - eligible: dev-48 ids not grader-impossible;
  - band: 31B gold source regions 2 to 3; E4B exactly 2 (a partial fix needs at least 2 regions, and the E4B resolves 0 of 84 task-runs at 3 or more regions, synthesis 1.11);
  - tier 1: band tasks that are a unit task-run in at least one baseline run of that model; tier 2: band tasks with a right-file-wrong-region run; tier 3: the next region count up (31B 4, E4B 3), unit tasks; within a tier by the number of unit runs that are all-findable under V1, then any-findable under V1, then unit runs, then id; the first 8.
- **Comparison:** the same ids' existing baseline results (31B arms R and RH, E4B four draws); no baseline arm is run.
- **Endpoints, blind, in that EXP:** primary, gold regions touched per task against the baseline mean; then resolves (recorded); guards: calls per task, cap hits (31B is cap-bound on 23 of 48 task-runs), 31B projected worst case at or under 11 h, text-form and malformed calls (E4B).
- **Cost:** about 0.8 GPU-h per kernel, under the 1 GPU-h line that needs a critic prereg. No dev-48, no upload.

## 7. Defects in this pre-registration, logged after the fact
None yet.

## 8. Run record (below the line; nothing above changes)

---

- **Script:** `experiments/EXP-082/sweep_check.py`, written and committed before any count. It imports `parse_diff`, `gold_regions`, `touches`, `same_file`, `norm_path`, `classify`, `load_run` and `jl` from `experiments/EXP-074/diag.py` and adds the line walker, the identifier sets and the region and selection logic.
- **Run by the screener:** not run (see Status).

## Status

PRE-REGISTERED, NOT COUNTED (2026-11-17). The screener's Bash guard allows `python tools/...` and no other script path, so `python -I -X utf8 experiments/EXP-082/sweep_check.py` is blocked for it; the exact guard text is in the handback. Next: someone whose command list allows the script runs the one command in section 6, then appends section 9.
