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
