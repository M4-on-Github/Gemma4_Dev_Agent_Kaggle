# R-036: L3 on the locked cohort, both shipping layouts (pre-registration)

Written 2026-11-22, before any job of this round is submitted. Counts only; no trace content, no ids. Goal set by the
user: a system that tackles any SWE project, with a higher solve rate. Small sweeps came first (R-001 to R-035); this
is the larger, held-out check of what they kept.

## Why

- The screening ladder (README) has an L3 rung: the locked cohort, base and candidate, "no loss on the locked ids". It
  has never been run. Every number behind the two shipping layouts comes from tuning cohorts (`cdev2-79` and its
  screens), which 35 rounds have looked at.
- `cohorts/cheld2-22.txt` is the locked cohort (README Setup results 7). It has never had an agent run on it. Its
  controls with task envs (C-003): reference patch 22 of 22, empty patch 0 of 22. It has two repositories, 14 and 8
  tasks, and no overlap with `cdev2-79`.
- What is checked:
  - **E4B.** The retry layout (R-021: +1.08 solves per draw on cdev2-79, CI +0.08..+2.08) is the E4B candidate in
    handoff H-003. Does its gain hold, or at least not reverse, on tasks no round has tuned on?
  - **31B.** The base is the 31B candidate. Its held-out solve rate against its cdev2-79 rate (28.7 of 79, 0.363)
    says whether the tuning cohort flatters it.
- After this round `cheld2-22` is spent as a locked cohort: no later round may tune on it.

## Arms

| Run | Tree | Draws | Role |
|---|---|---|---|
| `R-036-e4b-retry-held-d1..d6` | `trees/e4b-r020-retry` (shipping E4B layout, unchanged) | 6 | candidate |
| `R-036-e4b-ctl-held-d1..d6` | `trees/e4b-r020-ctl` (R-021's control: the same root, one `solve`) | 6 | base |
| `R-036-31b-base-held-d1..d4` | `trees/31b-base` (shipping 31B, unchanged) | 4 | reference |

- No tree is edited. They are the trees R-021, R-033 and R-034 ran.
- Flags as R-034: `sbatch --parsable -J heng_<e4b|31b> slurm/eval.sbatch <run> <tree> cohorts/cheld2-22.txt
  --concurrency 4 --py313 env/py313-scorer/bin/python3.13 --task-envs env/taskenvs`, 1 Ada GPU, 4 CPUs, 64G.
- E4B retry and control draws are submitted interleaved, so they share the queue period (the R-033 lesson). No smoke:
  every tree has run many times.
- Cost: 12 × about 0.35 plus 4 × about 0.75, about 7 Ada GPU-h.

## Readings (written before any job runs)

1. **Served check, every draw, before any reading.**
   - A task is served if any agent step has prompt tokens.
   - A draw is read only if it has 22 rows and every task is served. An OUT_OF_MEMORY job is kept under R-021's rule
     only when that holds.
   - A draw that fails is re-run once under the same run name with an `r` suffix. The re-run is logged as a deviation
     before any draw is read.
2. **L3, E4B (the decision).** `tools/paired_boot.py --arm` retry ×6 `--base` ctl ×6. The statistic is solves per draw
   on the 22 tasks, with a 90% CI over tasks.
   - **Pass** if the point estimate is 0.00 or more ("no loss on the locked ids").
   - **Fail** otherwise.
   - Power: R-021's +1.08 per 79 tasks is about +0.3 per 22. This rung guards against a reversal. It cannot confirm a
     gain, and none is claimed from it.
3. **Mechanism, E4B (reported).** `tools/retry_counts.py` on the retry draws: first attempt empty, retried, rescued,
   retry_miss, `solve_calls_gt3`. Per draw, both arms: empty patches, time caps (`task_wall_s` ≥ 470), mean task wall,
   and the wall ratio retry over control.
4. **Held-out rates (reported, not gates).**
   - Per arm: resolved per draw on 22 and per task, beside the same tree's cdev2-79 rate: E4B retry 7.58 of 79
     (R-021), E4B ctl 6.50 of 79 (R-021), 31B base 28.7 of 79 (R-008 d1-d2, R-011 d3-d4, R-014 d5, R-015 d6).
   - Per repository share, as counts (two repositories, unnamed here).
   - Tasks resolved at least once, per arm.

## What each outcome means

- **E4B pass:** the retry layout does not reverse on held-out tasks. H-003 stands and the handoff README gets the
  L3 line.
- **E4B fail:** the gain did not carry to tasks no round tuned on. H-003 gets a note with the numbers; the user decides
  whether the Kaggle dev-48 check (L4) still runs. The cluster does not re-tune on `cheld2-22`.
- **31B held-out rate well below 0.363:** the cdev2-79 numbers flatter the 31B. That would matter for the paper's
  claims, not for the 31B config, which has no candidate.

**Blind guess (not a reading).** E4B pass: 65%. 31B held-out rate per task: 0.30-0.45, 70%.

## Queued

Submitted 2026-11-22, all 16 at once, interleaved:
- E4B retry d1-d6: 60816, 60819, 60822, 60825, 60828, 60830.
- E4B ctl d1-d6: 60817, 60820, 60823, 60826, 60829, 60831.
- 31B base d1-d4: 60818, 60821, 60824, 60827.
- No gate actor: this round has no kill gate. Reading 1 is applied by hand once every job has ended.

## Side note: 31B output-cap desk (T-31b-036; zero GPU, not part of this round's readings)

Written 2026-11-22 while the jobs run. On the six cdev2-79 base draws:
- A pooled fit of step time gives about 36 s per 1k completion tokens. Decode is 0.84 of step time. Tool intercepts
  run 4-12 s, the highest after pytest. This agrees with R-004 and R-010.
- Capped tasks average 9,524 completion tokens against 6,571 for the rest, and 1.01 turns of 2,000+ tokens against
  0.31.
- `max_output_tokens` 4096 would cut 8.8 recorded turns per draw (219 s above 4096 tokens per draw). It would also
  shorten the final turns that run 152 s or more in 3.5 capped tasks per draw, none of which resolved. The ceiling is
  about 7 s per task, 2% of wall, before counting the turns a cut breaks. **Not run.**
- `thinking_budget` does reach vLLM. `adk_submission/resolvers/generation.py` maps it to
  `extra_body.thinking_token_budget`, and `adk_submission/server.py` adds `--reasoning-config` for the gemma4 parser.
  So T-31b-003 tested a real budget (R-010: the model keeps deliberating in visible text after the forced end).

## Deviation (logged 2026-11-22, before any reading)

- Reading 1 on the 12 E4B draws: 11 have 22 rows and 22 served tasks. `R-036-e4b-ctl-held-d3` (job 60823) has 22
  rows but 21 served, so it fails and is not read.
- It is re-run once as `R-036-e4b-ctl-held-d3r` (job 60848), the same tree, cohort and flags. Reading 2 uses ctl d1, d2, d3r and
  d4-d6.
- The served-check script also printed each draw's resolved count, so those were seen before this entry. The bars
  are as pre-registered and are not changed.
- Job 60848 stopped after 14 s on its start-up check (visible GPU count not 1), before any task ran. Nothing was
  served, so it is not a draw. The same `d3r` re-run was submitted again as job 60849.

## Results (2026-11-22; readings applied as written)

**Reading 1.** All 16 draws plus `ctl-d3r` (job 60849) have 22 rows. Every task is served in each except
`ctl-d3` (21 of 22), which is replaced by `d3r` as the deviation says. All jobs COMPLETED.

**Reading 2: E4B L3 passes.** On `paired_boot.py`, retry ×6 against ctl (d1, d2, d3r, d4-d6), 22 tasks, 0 dropped:

| | Per draw | Mean |
|---|---|---|
| retry | 4, 1, 1, 4, 1, 2 | 2.17 |
| ctl | 3, 1, 1, 1, 1, 2 | 1.50 |
| **paired difference** | | **+0.67 (90% CI 0.00..+1.33)** |

The point estimate is at least 0.00, so it passes. As pre-registered, no gain is claimed from this rung. The direction
and size agree with R-021: +1.08 per 79 tasks is +0.30 per 22, against +0.67 here.

**Reading 3: mechanism, retry draws (sums over 6).**
- First attempt empty in 20; retried 20; retry_miss 0; rescued 2.
- First attempt unknown 19; `solve_calls_gt3` 1; solve_after_submit 1.
- Per draw, retry against ctl:
  - empty patches 1.67 vs 3.33;
  - time caps 0.67 vs 0.50;
  - mean task wall 155.2 vs 129.7 s, a ratio of 1.20 (R-021: 1.23).

**Reading 4: held-out rates against the tuning cohort.**

| Arm | cheld2-22: per draw | Per task | cdev2-79: per task | Ever resolved | Repository A (14 tasks) | Repository B (8 tasks) |
|---|---|---|---|---|---|---|
| E4B retry | 2.17 | 0.098 | 0.096 | 5 | 1.83, ever 4 | 0.33, ever 1 |
| E4B ctl | 1.50 | 0.068 | 0.082 | 3 | 1.50, ever 3 | 0.00, ever 0 |
| 31B base | 9.00 (9, 10, 8, 9) | 0.409 | 0.363 | 12 | 6.50, ever 9 | 2.50, ever 3 |

- 31B base also: empty patches 3.5 per draw, time caps 7.25 per draw, mean task wall 331.2 s.
- Neither layout's held-out rate falls below its tuning rate, so the tuning cohort does not flatter them. The E4B
  retry rate is the same on both cohorts (0.098 against 0.096). The 31B is 0.05 higher held out, inside the noise
  of 4 draws on 22 tasks.

**What it means (per the pre-registered outcomes).**
- E4B pass: the retry layout does not reverse on tasks no round tuned on. H-003 stands, and its README gets the L3
  line.
- 31B: no candidate. Its held-out rate supports the cdev2-79 numbers used in the paper.
- `cheld2-22` is now spent as a locked cohort.

Blind guess against outcome: E4B pass (guessed 65%); 31B rate 0.409, inside the guessed 0.30-0.45.
