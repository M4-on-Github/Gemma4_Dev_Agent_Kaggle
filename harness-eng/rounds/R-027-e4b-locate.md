# R-027: E4B deterministic locate skill, ranked file list passed to the solver (pre-registration)

Written 2026-11-22, before any job of this round is submitted. Counts only; no trace content. Tweak ids
**T-e4b-027a** (loc5) and **T-e4b-027b** (loc10). The `tweaks.md` rows are added with the results. Part of the goal the
user set on 2026-11-22: raise the solve rate and the models' abilities, starting with small representative sweeps.

## Why (desk check, zero GPU, read before this file was written)

- **Where the shipping E4B misses** (R-021 retry ×12 on cdev2-79, per draw; resolved 7.58). Of the unresolved
  task-draws, 24.5 edited only wrong source files, 39.17 touched some or all gold source files, and 7.42 changed no
  source file.
- **In the wrong-file misses the gold file is mostly never seen.** In 17.58 of the 24.5 per draw, the gold path
  appears in no read and no tool output. So the solver does not choose badly between seen files. It never finds the
  right one.
- **A deterministic BM25 ranker finds it** (`tools/bm25_locate_desk.py`, over the non-test `.py` files of each
  snapshot; median 53 files). With the first 400 characters of the issue as the query, the gold file is top 1 in
  42 of 129 tasks, top 5 in 90, top 10 in 106. Crossed with the E4B wrong-file misses, gold is in the top 5 in
  11.08 of 24.5 per draw and in the top 10 in 17.25.
- **The shipped skill script gives the same counts.** `tools/locate_check.py` runs `skills_lib/locate/scripts/rank.py`
  itself on every snapshot: top 5 lists a gold file in 90 of 129 tasks, top 10 in 106; never the plain fallback;
  median 0.13 s, max 0.30 s per task.
- On `sw-e4b-32`: gold in the top 5 for 17 of 32 tasks, top 10 for 24. In the comparator's wrong-file misses on the
  cohort (7.58 per draw) gold is in the top 5 in 3.25, in the top 10 in 4.75.
- **How this differs from the E4B locate attempts that failed.** R-005 filerank (a prompt `git grep -ic` template),
  R-007 (locator agent, then editor) and R-014 (scout) were all model-driven searches, and the file choice did not
  change. Here the ranking is computed by a script and handed to the solver as part of its request. Whether the
  E4B uses the list is the open question.
- **31B: not tested.** In its wrong-file misses gold is in the top 5 in 0.83 of 7.83 per draw. That is consistent
  with the earlier finding that the 31B names the eventual file by call 3 in 293 of 395 draws.

## Arms

| Arm | Tree | Built from | Change |
|---|---|---|---|
| e4b-loc5 | `trees/e4b-sw-loc5` | `e4b-r020-retry` | `skills/locate` added; root step 1 runs `locate` with the issue's first three sentences, every `solve` request is the line it printed (top 5 files) |
| e4b-loc10 | `trees/e4b-sw-loc10` | `e4b-r020-retry` | the same with the top 10 files (`TOP = 10` in `rank.py`) |

- `diff -r` against the parent shows only `agent.yaml` (one comment, one `skills` entry), `prompts/root.md`, and
  `skills/locate`. Solver prompt, sampling, caps and the retry rule are unchanged.
- `rank.py` is pure Python and reads files only. It finds the workspace the way `count.py` does, scores non-test
  `.py` files (test, doc, example, benchmark and script dirs left out, files over 400 KB skipped), and prints one
  line: `Resolve the issue in /workspace. The source files that best match the issue, best first: a.py, ...`. With no
  query, no match or any error it prints the parent's request, `Resolve the issue in /workspace.`
- Validator (`--official`, `env/harness.sif`): the parent's known profile (`adk_submission.validate_directory` OK;
  the cluster-only gate and compile errors; the H-002 false error), plus the same VERIFY warning for `rank.py` that
  `count.py` gets.

## Cohort and comparator

- `sw-e4b-32` from R-026 (ids in gitignored `runs/_cohorts/`). Comparator: R-021-e4b-retry-ada d1-d12 restricted to
  the cohort, per draw 7, 11, 6, 8, 8, 7, 8, 5, 7, 5, 6, 6 (mean 7.0).
- Noise (R-026): the same arm against itself, 4 draws against 8, has quantiles 75% +0.75, 90% +1.5, 95% +1.88.
- Drift: R-026's two fresh controls on the cohort resolved 9 and 7 (mean 8.0; paired against the comparator +1.0,
  CI −1.33..+3.5). Two more fresh controls run in this round (`R-027-e4b-ctl-ada-d1..d2`, `trees/e4b-r020-retry`), so
  the arms can also be read against 4 fresh control draws.

## Runs

| Job | Tree | Cohort | Draws |
|---|---|---|---|
| smoke, one per tree (not read for effect) | each arm tree | `runs/_cohorts/smoke-te.txt` (2 tasks), concurrency 2 | 1 each, `S-027-<arm>-smoke` |
| arms | 2 trees | `runs/_cohorts/sw-e4b-32.txt` | 4 each, `R-027-<arm>-ada-d1..d4`, `afterok` on that arm's smoke |
| fresh control | `trees/e4b-r020-retry` | `sw-e4b-32` | 2, `R-027-e4b-ctl-ada-d1..d2`, no dependency |

- Flags as R-026: `sbatch --parsable -J heng_e4b slurm/eval.sbatch <run> <tree> <cohort> --concurrency 4 --py313
  env/py313-scorer/bin/python3.13 --task-envs env/taskenvs`, 1 Ada GPU, 4 CPUs, 64G. Smokes use `--concurrency 2`.
- 12 jobs, about 10 × 0.4 + 2 × 0.2 = 4.4 Ada GPU-h. Queued up front.

## Readings (written before any job runs)

1. **Smoke gate, per arm** (kill = cancel that arm's draws, unread; a failed smoke is fixed once, logged here, and
   re-run): `status_SUCCESS` < 2, `solve_calls_gt3` ≥ 1, `root_calls_max` > 11. Read by hand, also a kill: `rank.py`
   raised, or printed the plain request on both tasks.
2. **Draw-1 kill gates, per arm** (`tools/gate_actor.sh`, cancels that arm's d2-d4): the R-026 E4B bars
   `resolved<=2 empty>=9 timecap>=6 mean_wall>250 retry_miss>=4 solve_calls_gt3>=3 callcap>=14`, checked with
   `tools/d1_gate.py` on all 12 comparator draws restricted to the cohort before this file was written: 12 of 12
   PASS. Also `locate_passed_tasks<=23`: fewer than 24 of 32 tasks with a `solve` request that carries the list
   means the lever is not tested. This one is about the arm and is not checked on the comparator.
3. **Promotion, per arm, after its 4 draws** (`tools/paired_boot.py`, solves per draw on the cohort against the 12
   comparator draws, 90% CI over tasks; wall ratio = arm mean task wall / comparator mean task wall): **promote** if
   the point estimate is ≥ +1.25 and the wall ratio ≤ 1.25. **Drop** anything else, and any arm a gate stopped.
   If both arms pass, the one with the higher point estimate is promoted.
   - Secondary (reported, not the decision): each arm against the 4 fresh control draws (R-026 d1-d2, R-027
     d1-d2). If that point estimate is below +0.5 while the primary one promotes, that is stated next to the
     promotion, and the cdev2-79 round in reading 5 decides.
4. **Mechanism (reported, not gates).** Per arm: `locate_listed_tasks`, `locate_passed_tasks`, `lever_skill_errors`;
   the wrong-file / touched-gold / no-source-edit classes per draw against the comparator's on the cohort; tasks
   whose first edited source file is in the printed list; first-attempt empty, retried, rescued
   (`retry_counts.py`); calls per task; mean wall.
5. **What promotion buys.** The promoted arm runs 12 draws on `cohorts/cdev2-79.txt` against the 12 R-021 retry
   draws (paired, R-021 readings), pre-registered as its own round.

**Blind guess (not a reading).** Each arm passes its smoke and d1: 75%. Promoted: loc5 20%, loc10 15%. At least one
promoted: 25%.

## Queued (2026-11-22)

- Smokes: loc5 60609, loc10 60614.
- loc5 d1-d4, all `afterok` on 60609: 60610, 60611, 60612, 60613.
- loc10 d1-d4, all `afterok` on 60614: 60615, 60616, 60617, 60618.
- Fresh controls, no dependency: 60619, 60620.
- Gate actors (`tools/gate_actor.sh`, logs `logs/gate_R-027_<job>.log`): each smoke (cancels that arm's d1-d4 on a
  kill) and each arm's d1 (cancels its d2-d4), with the bars of readings 1 and 2. The by-hand smoke checks of
  reading 1 are read when the smokes finish; a by-hand kill cancels that arm's draws then.
