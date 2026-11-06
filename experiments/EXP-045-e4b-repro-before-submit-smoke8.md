# EXP-045 — E4B, one prompt bullet "after the last edit, write and run a short python reproduction, then submit", on smoke-8: an enforcement screen

**Date:** 2026-11-05
**Type:** smoke-8 screen, one arm, about 0.25-0.45 L4x4-h expected (point 0.33, conditional worst case about 1.24 h, section 2.4). **Built, not pushed**: the user has not approved this screen's GPU.
**Cohort:** smoke-8
**Ladder:** L2. L0 and L1 are EXP-042 (the check-before-submit mining) and EXP-041 section 9.5. EXP-042 gives **no trace support for this lever on the E4B** (sharpened measure: W 1 of 5, L 3 of 43, row 1 fires): the wins mostly ran nothing informative. So this screen tests **enforcement only**, whether the E4B follows a prompt-only rule of this shape, and it does not test whether a check helps.
**Pre-registered:** this file, the tree, the zip's recorded sha and the notebook are committed before any push. Sections 3 to 5 are written blind and are not revised; results are appended as a new section.
**Serves:** C-019 (an executed verify step after the last edit is the structural change with the most room), C-018 (a one-shot python check as the compromise).
**Relates:** EXP-042 (the definition of "informative" and the baselines), EXP-041 (9.5, the informative 27 ids), EXP-033 and EXP-038 (the two references on the same 8 ids), EXP-032 (P1: a prompt-only call limit held on 3 of 24 localizers), EXP-040 (the proposer's read cap held on 5 of 8), EXP-044 (the other screen of this job).
**Tags:** [V] verified in trace or by a check run here, [M] community or mirror, [I] inference, [H] hand judgement.

## 1. Why this, now

The lead asked for the second one-variable E4B screen: after the last edit and before `submit_patch`, write and run a short python reproduction of the reported behaviour through `run_command`. On this model the checks that exist are rare and mostly uninformative. EXP-042 (sharpened): of 48 E4B tasks, 4 ran an informative check (1 win, 3 losses). On smoke-8 the references give 2 of 8 (EXP-038: requests_7205, rich_3006) and 1 to 2 of 8 (EXP-033: rich_3468 has no environment-failure string in its trace; rich_3006 has one matching line, not read; fastapi_14448's pytest died in collection) [V for EXP-038 from EXP-042 9.1, I for EXP-033 from string counts]. That is a measurable base rate, so a count of 6 or more of 8 would be a bound that no reference approaches. The three fastapi ids in smoke-8 are gated: a `pytest` check dies in collection on the missing test-only packages, so a python script that imports the changed code is the only check on them that can be informative. That is the mechanism this screen can show is reachable, or not.

Prompt-only rules have not held on either model (EXP-032 P1: the 5-call limit held on 3 of 24; EXP-040: the proposer's read cap held on 5 of 8). So the question this screen asks is narrow: **does the E4B comply with this one rule often enough to build a dev-48 arm on?**

## 2. Design

### 2.1 The tree

`experiments/EXP-045/candidate-p/` is `experiments/EXP-033/candidate-e4b/` (the v24 prompt at 8 minutes and 28 calls, `model: gemma-4-e4b-it-qat-w4a16-ct`; EXP-038 ran it unchanged) with **one bullet replaced** in `prompts/system.md`, section 4 "One check, one repair, then submit". The replaced bullet is the first of section 4:

```
- After the edit, run at most one focused check: `pytest tests/test_file.py -k test_name -q` or `python -c "..."`.
```

and the bullet that takes its place (alone in `experiments/EXP-045/p_insert.md`):

```
- After your last edit, write a short Python script that reproduces the behavior the issue reports into `/tmp/repro.py` and run it once with `python3`, both through `run_command`. It must import the code you changed, call it the way the issue does, and print the value the contract requires. This is your one check.
```

It replaces rather than adds, so that the prompt does not carry two different instructions about the one check. `agent.yaml`, `configs/sampling.yaml` and `eval_config.yaml` are byte for byte EXP-033's (no value changes, so no dated comment is added to the YAML). The script goes to `/tmp` so that the existing rule ("never write scratch files into `/workspace`, files left in the repository become part of the diff") holds. The `diff -ru` of the two trees is recorded in section 8 once built.

**Known design risk (the tension, written before the run).** Two sentences of the unchanged section 4 and one of the preamble pull the other way: "Call `submit_patch` after that, even when the local check is red or you skipped it", and "A correct source diff scores the task even if your local test was red or you never ran a test." Those say the check is optional. They are left in place on purpose: the screen asks whether the new bullet beats them as written, and rewriting them is a second variable. The expected cost is lower compliance than a clean rewrite would give; a low count (row 2) is therefore a result about this wording against the prompt as it stands, and the next step if it is low is to say that, not to conclude the lever is dead.

### 2.2 Measures, defined operationally and now

- **After the last edit.** The step order in the trace: a `run_command` that follows the last `edit_file` call (any status) and precedes the final `submit_patch` call, or the end of the task when there is none. A task with no `edit_file` call at all cannot comply (counted in the denominator of 8).
- **C, compliance.** A task complies if such a `run_command` **runs a python interpreter** (the command contains `python` or `python3` as the program, including a heredoc that is then run) and **is not** a `pytest`, `unittest` or `tests/` run, and its observation is not an environment or launcher failure by EXP-042 section 2's sharpened rule (a collection error from `ModuleNotFoundError` or `ImportError`, `command not found`, `No such file or directory` for the target, `no tests ran`). So C counts informative python runs after the last edit. The file the script is written to is not a condition.
- **I, the EXP-042 sharpened measure.** Tasks with at least one informative run of any of the EXP-041/EXP-042 kinds (pytest, unittest, `tests/`, python) after the last edit, as in EXP-042 section 2. References: 2 of 8 (EXP-038) and 1 to 2 of 8 (EXP-033). C is a subset of I.
- **Executed, not informative.** Tasks with a python run after the last edit whose output is an environment or launcher failure; recorded, not read.
- **Stray file.** A patch that adds a new file (`new file mode` in `patches/<id>.patch`); references: none of the 8 in EXP-038 [I, not checked per file here].

### 2.3 The cohort, and drift between the references

smoke-8 (`experiments/cohorts/smoke-8.txt`), the strict subset of dev-48, so every per-task number pairs with EXP-038, and EXP-033 ran the same 8. The two references drift on the same tree (mean wall 56.9 s against 78.3 s; non-empty patches 6 of 8 against 8 of 8). So no row compares a mean with a mean: counts are read as bounds (6 or more of 8, against references of 2 or fewer), and wall is read only against a fixed bound (row 3). A count counts as changed only if it lies outside the range spanned by both references.

### 2.4 Cost

| item | seconds | basis |
|---|---|---|
| kernel overhead | 432 to 504 (0.12 to 0.14 h) | EXP-040 about 443 s, EXP-033 about 445 s |
| per task, single loop | 57 (EXP-033) to 78 (EXP-038 subset) | the two references |
| the reproduction | +2 to 4 turns at about 6.0 s, plus the script run: about +15 to 45 | EXP-033 per-turn 6.0 s [I for the number of turns]; the python run is short |
| per task, point | 72 to 125 | |
| 8 tasks + overhead | 1,008 to 1,504 s = **0.28 to 0.42 h, range 0.25 to 0.45 h, point 0.33 h** | |

**Conditional worst case about 1.24 h**: every task at the 495 s cap plus 504 s overhead. The references ran far inside the cap (0 of 8 capped in both), so this needs the reproduction to loop to the clock.

`pack_submission.py --skip-budget-gate --allow-warnings` is used: the 8-minute setting is above the 4.5-minute packing gate (as EXP-032, EXP-033 and EXP-040), the gate is for the real submission, and a screen is never uploaded.

## 3. Endpoints, fixed in advance

Counts over the 8 tasks, from `runs/EXP-045-p/.../traces/trace_<id>.json`, `summary.jsonl`, `patches/` and the kernel log. References are EXP-033 and the EXP-038 subset.

| # | Endpoint | Definition |
|---|---|---|
| E1 | C | tasks of 8 that comply (2.2) |
| E2 | I | tasks of 8 with an informative run after the last edit, any kind (2.2) |
| E3 | Executed, uninformative | tasks with a python run after the last edit that is an environment or launcher failure |
| E4 | Added wall | per task `wall_s`, and mean; capped (28 calls or 480 s); recorded against the bound in row 3, never against a reference mean |
| E5 | Stray files and empty patches | tasks whose patch adds a new file; tasks with an empty patch (references: 0 of 8 and 2 of 8) |
| E6 | Resolves | recorded only, never read |

## 4. Pre-registered readings. Written blind. Not to be revised after the numbers land.

Order is first match.

| Row | Condition | Reading |
|---|---|---|
| 0 | infrastructure: a crash in more than 2 of 8, or the tree does not run | fix the one cause and re-run once; no reading |
| 1 | stray file in 2 or more of 8 patches, or 3 or more of 8 empty patches | the passage leaks scratch files into the diff or costs applied edits: kill the wording as written, whatever C is; a rewrite is a new screen |
| 2 | C is 2 or fewer of 8 | the E4B does not follow this rule at the rate the references already show (I is 2 or fewer there): **kill it as a prompt-only lever on this prompt**, which is a third recorded prompt-only compliance failure (EXP-032 P1, EXP-040). It does not show that a check does not help, and it does not rule out an enforced form |
| 3 | mean wall above 140 s, or 3 or more of 8 capped, or any task past 495 s | the reproduction costs more than the room; no dev-48 arm at this wording; report seconds per task |
| 4 | C is 6 or more of 8, wall inside row 3's bounds | the rule is enforced at a rate no reference approaches: **promote** to one dev-48 E4B arm (section 5) |
| 5 | C is 3 to 5 of 8 | no decision |

Recorded in every row, not read: E2 (I), E3, E5 beyond row 1, E6.

**Blind prediction, with the compliance rate stated.** C: **4 of 8** (range 3 to 5), from the two prompt-only precedents (P1 limit held 3 of 24, EXP-040 proposer read cap held 5 of 8) and the two sentences left in the prompt that say the check is optional (2.1). I (any informative run): 4 to 5 of 8. Executed but uninformative: 1 of 8. Mean wall 85 to 120 s, 0 of 8 capped. Stray files 0 of 8 (the passage names `/tmp`), empty patches 0 or 1 of 8. Resolves 2 to 3 of 8, recorded and not read. Row probabilities: row 0 5%, row 1 8%, row 2 28%, row 3 4%, row 4 20%, row 5 35%. **If compliance is low, row 2 fires**, and what it says is stated in the table: a prompt-only lever, third failure, nothing about checks in general.

## 5. What this licenses

**The screen can decide one of two things.** It can **kill the rule as a prompt-only lever on this prompt** (rows 1 to 3), or **promote it to one dev-48 E4B arm** (row 4). Row 5 decides nothing. It cannot show that an informative check helps (n = 8, resolves are not read, and EXP-042 gives no trace support), and it cannot show it does not.

**The dev-48 endpoint if row 4 fires.** The share of tasks with an informative run after the last edit at n = 48 (primary; EXP-042: 4 of 48 on the E4B single loop), with C beside it, and paired resolves against EXP-038 (McNemar, discordant pairs reported) read on the informative 27 ids of EXP-041 section 9.5 as the primary resolve population (the gated and impossible ids cannot resolve on this grader as run), the other 21 recorded. Calls and wall as cost, with the projected 120-task hours at the setting used. **Explicitly not an upload.** Cost of that arm: 48 x 72 to 125 s + about 450 s overhead = about 1.1 to 1.7 L4x4-h [I], to be recomputed from this screen's wall before the ask.

No row licenses an upload and no row moves a claim.

## 6. Exact commands

```
python tools/validate_submission.py experiments/EXP-045/candidate-p --strict
python tools/pack_submission.py --src experiments/EXP-045/candidate-p --out dist/EXP-045-p.zip --skip-budget-gate --allow-warnings
python tools/build_notebook.py --embed dist/EXP-045-p.zip --username rainm4 --cohort experiments/cohorts/smoke-8.txt --set EXP_ID='"EXP-045-p"' --set MODEL_NAME='"gemma-4-e4b-it-qat-w4a16-ct"' --set RUN_GOLD_CONTROL=False --out notebooks/exp045_p/kaggle_eval_l4x4.ipynb
# push, a later job, only after the user approves the GPU and the lead dispatches it:   kaggle kernels push -p notebooks/exp045_p
# after COMPLETE, a separate job:
kaggle kernels output rainm4/gemma4-exp045-p -p runs/EXP-045-p/
python tools/analyze_traces.py <inner bundle dir> --cap-minutes 8 --max-calls 28
python tools/run_forensics.py compare runs/EXP-033-e4b/runs/EXP-033-e4b <inner bundle dir>
```

## 7. Defects

Written before the run.

1. **The two "check is optional" sentences stay** (2.1), by design, and may drive row 2 on their own.
2. **n = 8.** Resolves are not read; compliance is a count of 8 with references of 1 to 2 in the broader measure I.
3. **C's baseline is not computed.** The references' informative runs are counted by EXP-042's broader measure (pytest and python); how many of them were python-script runs is not read here [I: few; requests_7205's informative run in EXP-038 was a pytest run, the others not read]. Row 4 needs 6 or more, which no reference approaches in either measure.
4. **"After the last edit" counts a failed edit as an edit.** A task whose last edit failed and which then ran a reproduction counts as complying; the variant restricted to tasks with an applied edit is recorded alongside.
5. **The script is written to `/tmp` through `run_command` or `write_file`**; both are accepted so long as the python run is a `run_command`. A reproduction that reads the file the agent just edited from `/workspace` is fine.
6. **Seen-before:** the references' command histories on these 8 ids (function order only, for the cost of the check; EXP-042 9.1 for the informative runs). The passage was written after seeing them.

## 8. Built

Not built yet. Sections 1 to 7 are the pre-registration; the build record follows below the Status line when the tree, zip and notebook exist.

## Status

2026-11-05: pre-registered, not built, not pushed. Zero GPU. An enforcement screen only; EXP-042 gives no trace support for the lever on the E4B.
