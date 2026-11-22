# R-032: E4B solver temperature in the retry layout (pre-registration)

Written 2026-11-22, before any job of this round is submitted. Counts only; no trace content, no ids. Tweak ids
**T-e4b-032a** (0.6) and **T-e4b-032b** (0.3). Same goal as R-029 (set by the user on 2026-11-22): raise the solve
rate and the models' abilities, with small sweeps before bigger runs.

## Why

- **The E4B's measured limit is the edit, not the search** (R-027, R-028). In the R-021 retry draws, `edit_file`
  fails more often than it succeeds (160 other edit errors per draw against 130 `ok`), mostly because the old text is
  written from memory after a read (R-028: 78% mostly present or mostly invented).
- **Desk check, today (zero GPU).** The single-agent R-003 draws on cdev-56, 3 draws each, `edit_file` results with a
  status:

  | Arm | failed / (ok + failed) | empty patches, 3 draws | resolved, 3 draws |
  |---|---|---|---|
  | base, temperature 1.0 | 0.571 | 31 | 18 |
  | temperature 0.3 | 0.465 | 18 | 17 |
  | short prompt | 0.519 | 18 | 18 |

  Lower temperature cut edit failures and empties. It did not move resolves in the single agent, where an empty
  attempt was final. In the retry layout an empty attempt is retried (R-021), so the question here is whether
  cleaner edits per attempt turn into solves once empties are already handled.
- **Risk, stated now.** The retry gains from a fresh draw (R-021: 13 rescued of 169 empty first attempts). At a lower
  temperature a retry is a less independent draw, so the rescue rate may fall. The 0.6 arm is the middle point.
- Prior on sampling levers is low: E4B temperature 0.3 (R-003), thinking 2048 (R-007), 31B temperature 0.6 (R-011)
  were all noise.

## Arms

| ID | Arm | Tree | Change against `trees/e4b-r020-retry` (the shipping E4B layout, R-021) |
|---|---|---|---|
| T-e4b-032a | t06 | `trees/e4b-retry-t06` | solver `configs/sampling.yaml` temperature 1.0 -> 0.6 |
| T-e4b-032b | t03 | `trees/e4b-retry-t03` | solver `configs/sampling.yaml` temperature 1.0 -> 0.3 |

- `diff -r` against the parent shows only the temperature line and its dated comment. The root's
  `sampling_root.yaml`, top_p 0.95, top_k 64, thinking 4096, both caps and both prompts are unchanged.
- Validator (`--official`): the parent's known profile (the 18 h cap-only figure under the recorded 8 min override,
  and the official compile call signature), the same 3 errors and 2 warnings.
- No smoke: the trees differ from the shipping tree in one sampling value, which changes no tool, prompt or agent.
  The d1 gates cover a broken run.

## Runs

| Run | Tree | Cohort | Draws |
|---|---|---|---|
| `R-032-e4b-t06-ada-d1..d4` | `trees/e4b-retry-t06` | `runs/_cohorts/sw-e4b-32.txt` | 4 |
| `R-032-e4b-t03-ada-d1..d4` | `trees/e4b-retry-t03` | `runs/_cohorts/sw-e4b-32.txt` | 4 |
| `R-032-e4b-ctl-ada-d1..d2` | `trees/e4b-r020-retry` | `runs/_cohorts/sw-e4b-32.txt` | 2 (fresh control, drift check) |

- Flags as R-026 (`-J heng_e4b`, concurrency 4, `--py313 env/py313-scorer/bin/python3.13 --task-envs env/taskenvs`,
  1 Ada GPU, 4 CPUs, 64G). d2-d4 of each arm are `afterok` on nothing; they are queued up front and the gate actor
  cancels them on a d1 kill (weekend rule).
- Cost: 10 draws × about 0.4 h ≈ 4 Ada GPU-h.
- **Comparator:** R-021-e4b-retry-ada d1-d12 restricted to `sw-e4b-32` (not used in the cohort selection; per draw 7,
  11, 6, 8, 8, 7, 8, 5, 7, 5, 6, 6, mean 7.0). The R-026 fresh control (2 draws) and this round's 2 are reported.

## Readings (written before any job runs)

1. **Draw-1 kill gates, per arm** (`tools/gate_actor.sh` on d1, which cancels that arm's d2-d4): R-026's E4B bars,
   unchanged, which passed on 12 of 12 comparator draws:
   `resolved<=2 empty>=9 timecap>=6 mean_wall>250 retry_miss>=4 solve_calls_gt3>=3 callcap>=14`.
2. **Promotion, per arm, after its 4 draws** (`tools/paired_boot.py`, solves per draw on the cohort, 90% CI over
   tasks, against the 12 comparator draws), R-026's bar: **promote** if the point estimate is ≥ +1.25 and the wall
   ratio (arm mean task wall / comparator mean task wall) is ≤ 1.25. **Drop** anything else.
   - If both arms promote, the larger point estimate goes on.
   - Drift check (reported): if the mean of the 2 fresh controls is outside 5-9, that is stated next to each
     reading, and each arm is also compared with the 4 fresh control draws (R-026's 2 and these 2).
3. **Mechanism (reported, not gates):** `edit_file` failed / (ok + failed); empty final patches; first-attempt empty,
   retried, rescued (`tools/retry_counts.py`); unparseable final patches (`tools/patch_syntax_desk.py`); calls per
   task; time caps.
   - **Mechanism works:** the failed-edit share is at least 0.05 below the comparator's on the same cohort.
4. **What promotion buys:** 12 draws on `cohorts/cdev2-79.txt` against the 12 R-021 retry draws, with R-021's
   readings, pre-registered as its own round.

**Blind guess (not a reading).** Both pass d1: 85%. Mechanism works: t03 60%, t06 40%. Promoted: t06 10%, t03 8%.

## Queued (2026-11-22)

- t06 d1-d4: 60732-60735. t03 d1-d4: 60736-60739. Fresh control d1-d2: 60740-60741.
- Gate actors on 60732 (cancels 60733-60735) and 60736 (cancels 60737-60739), with the bars of reading 1.
- Comparator value for reading 3, computed after queueing and before any R-032 row exists
  (`tools/edit_status_counts.py --subset runs/_cohorts/sw-e4b-32.txt`, R-021 retry d1-d12): failed share 0.478
  (617 ok, 565 failed). So **mechanism works** means a failed share of 0.428 or less.

## Results (2026-11-22, all 10 jobs COMPLETED, 20-32 min each)

**Gates (reading 1):** t06 d1 PASS, t03 d1 PASS. Nothing was cancelled.

**Promotion (reading 2),** `tools/paired_boot.py` on the 32 tasks against R-021 retry d1-d12 (7.0 per draw):

| Arm | Per draw | Point | 90% CI | Wall ratio | Bar | Reading |
|---|---|---|---|---|---|---|
| t06 | 9, 10, 7, 7 | +1.25 | −0.33..+3.00 | 1.04 (135.0 / 129.7 s) | ≥ +1.25, ≤ 1.25 | **promote** (the bar is met exactly) |
| t03 | 8, 8, 6, 6 | 0.00 | −1.75..+1.92 | 1.16 | ≥ +1.25, ≤ 1.25 | **drop** |
| fresh control | 9, 8 | +1.50 | −0.67..+3.75 | 0.87 | (drift check) | mean 8.5, inside 5-9 |

- **Drift, reported.** The fresh-control mean is inside the 5-9 window, so reading 2's drift clause does not fire.
  But the control gains as much as t06 does over the comparator. Against the 4 fresh control draws (R-026's 9, 7 and
  these 9, 8; mean 8.25), t06 is **0.00 (CI −2.50..+2.75)** and t03 is **−1.25 (CI −3.50..+1.00)**. So the t06
  promotion is most likely comparator drift, not the temperature. The reading is applied as written. The
  cdev2-79 round that it buys (reading 4) gets concurrent controls (R-033).
- **Mechanism (reading 3)**, `tools/edit_status_counts.py` on the cohort (bar: failed share ≤ 0.428):

  | Arm | ok | failed | failed share | Mechanism | Empty final patches per draw | Calls per task |
  |---|---|---|---|---|---|---|
  | comparator (R-021 ×12) | 617 | 565 | 0.478 | | 1.75 | 14.8 |
  | fresh control ×2 | 80 | 89 | 0.527 | | 1.5 | 14.5 |
  | t06 | 248 | 193 | 0.438 | not met | 1.0 | 15.2 |
  | t03 | 227 | 164 | 0.419 | **works** | 0.75 | 15.4 |

  - Retry counts over 4 draws: t06 first-empty 16, retried 15, rescued 6; t03 first-empty 15, retried 15, rescued 2,
    `solve_calls_gt3` 2. Fresh control (2 draws): 11, 11, 2.
  - As in R-003, temperature 0.3 makes edits land more often but does not add solves. The lower rescue rate at 0.3
    (2 of 15 against 6 of 16) fits the risk stated in Why: a retry at low temperature is a less independent draw.
- Tool fix, recorded: `paired_boot.py` printed each base run's per-draw count over all of its rows, so a cdev2-79
  base showed full-cohort counts. The statistic and CI were always on the paired tasks. Per-draw counts are now on
  the paired tasks too. Every earlier reading used the statistic, so none changes.

**Outcome.** T-e4b-032a (t06) is promoted to R-033 by the written bar, with the drift caveat above. T-e4b-032b (t03)
is dropped.
