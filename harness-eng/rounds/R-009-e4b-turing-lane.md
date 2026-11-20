# R-009 (E4B): a Turing lane on pleiades-1-10, and two near-miss tweaks re-drawn six times

Written 2026-11-19T04:00Z (committed 04:00:23Z as 9ef46c6, first job submitted 04:00:30Z; an earlier version of this line said 04:10Z, corrected 2026-11-19T05:15Z), before any R-009 draw except the 2-task smoke `S-009-e4b-turing-smoke` (job 59474),
which checks only that the stack runs (it is not read for resolves). The user offered pleiades-1-10 for the
night ("it is all yours for tonight").

## Why

- **Spare GPUs.** pleiades-1-10 has 8 Quadro RTX 6000 (Turing, sm_75, 24 GB) and was idle.
- **E4B noise.** E4B draws move by 3 or more tasks on cdev2-79 (R-008: 7, 8, 5). Two or three draws per arm
  cannot separate a +2 effect from noise. Six draws per arm on a lane of its own can, roughly.
- **Two tweaks were near misses and were never drawn under the task envs.**
  - T-e4b-013 pagedread: screen 4.33 vs 3.0, cdev2-79 8.67 vs 7.33.
  - T-e4b-001 max_tool_calls 40: 7.5 vs 5.5 on cdev-56 at first, later read as noise.

## What had to change for the node to run (2026-11-19)

| Step | Failure | Fix |
|---|---|---|
| Container sees no GPU | `cuInit` 999 inside apptainer 1.1.2, `/dev/nvidia0` open gives EIO; the host opens it fine | bind `/lib/firmware/nvidia` (GSP firmware is loaded on first open, persistence mode is off) |
| bf16 | vLLM needs sm_80 for bf16; torch's `is_bf16_supported()` says yes on Turing | `tools/cluster_eval.py`: bf16 only at compute capability 8+, else float16 |
| Attention | TRITON_ATTN needs 96 KB shared memory at head size 512 (limit 64 KB); FlexAttention has no KV sharing; FlashInfer stops at head size 256 | `tools/turing_patches/make_triton_attn_patch.py`: on sm < 8, `num_stages=1` and 16-wide tiles above head size 256 |

- All three are bound or applied only when the GPU is a Quadro RTX 6000 (`slurm/eval.sbatch`), so Ada jobs
  run as before.
- Smoke 59474 resolved 1 of 2, with no engine or import errors. The vLLM server came up in 196 s.
- **Speed.** Per model call, Turing took 16.5 and 18.3 s on the two smoke tasks. On Ada the same tasks took
  5.7-11 s per call (R-008 d1, d2). So Turing is about 1.7-2x slower.

## Design

- **Lane settings.** Every R-009 job uses the R-008 flags (`--concurrency 4 --py313 ... --task-envs
  env/taskenvs`) plus `--time-scale 2.0`, so the task cap is 16 min instead of 8.
  - Why the scale: on Ada an E4B task ends before 400 s in 236 of 237 R-008 task-draws (p90 about 200 s). At
    half the speed, an unscaled cap would cut tasks that end normally on Ada.
  - The tool-call cap (28, or 40 in the calls40 arm) is unchanged.
- **Hardware differences that stay.** float16 instead of bfloat16, and a different attention kernel config.
  Either may change what the model writes. That is why Turing arms are read only against the Turing base.

| Arm | Tree | Cohort | Draws | Run ids |
|---|---|---|---|---|
| base | `trees/e4b-base` | `cdev2-79` | 6 | `R-009-e4b-base-tu-d1..d6` |
| pagedread (T-e4b-013) | `trees/e4b-r007-pagedread` | `cdev2-79` | 6 | `R-009-e4b-pagedread-tu-d1..d6` |
| calls40 (T-e4b-001) | `trees/e4b-r001-calls40` | `cdev2-79` | 6 | `R-009-e4b-calls40-tu-d1..d6` |

- **Order.** Jobs are submitted interleaved (base, pagedread, calls40, base, ...), so slots and node load are
  shared evenly across arms.
- **Cost.** 18 jobs at an estimated 1.5 h each is about 27 GPU-h on pleiades-1-10, outside the Ada ledger.

## Checks and readings (written before the draws)

1. **Health, per draw.**
   - Import errors (`envcheck.py`) on at most 2% of task-draws.
   - No engine crash.
   - A draw with fewer than 79 rows is reported and not used.
2. **Lane offset (reported, not a promotion).** The Turing base mean minus the Ada R-008 base (6.67).
   - Within ±3: the lane behaves like Ada within the no-change line.
   - Beyond ±3: the lane is a different setup. That does not affect readings 3 and 4, which use only Turing
     draws.
   - Also reported: the share of task-draws that reach 480 s (the unscaled cap), and seconds per model call.
3. **Tweak readings (the L2 rule, against the Turing base).**
   - **Kept:** mean ≥ Turing base + 3.
   - **Candidate:** mean ≥ base + 1.5 and the paired per-task difference over the 79 tasks has a 90% bootstrap
     CI above 0. A candidate is re-drawn on Ada before it is kept.
   - **Not kept:** anything else.
   - The draw-to-draw SD of the 6 base draws is reported, so later rounds can size their draw counts.
4. **No other comparison is read.** That includes calls40 against pagedread, per-repo splits, and draws
   before the 6th.

## Log

- 2026-11-19T03:49-03:59Z: smoke `S-009-e4b-turing-smoke` (job 59474), see above.
- 2026-11-19T04:00Z: 18 jobs submitted interleaved, 59475-59492 (d1: 59475 base, 59476 pagedread, 59477
  calls40; then in the same order to d6: 59490-59492). 8 run at once. All 8 vLLM servers came up in 225-227 s.
- **2026-11-19T05:10Z, speed under full load (logged, not a reading; the design is unchanged).**
  - With 8 jobs at concurrency 4, decode runs about 13 tokens/s per sequence, against 99 on Ada (R-008
    d1). The median model-step gap is 22.6-24.6 s against 3.3 s. Prompt and completion sizes are the same
    (prompt median about 7.8k tokens, completion about 260). Tool time is near zero on both.
  - The smoke's "1.7-2x" came from 2 tasks on one GPU and does not hold at concurrency 4. The cause has not
    been pinned down (KV-cache room, the patched kernel's small tiles at prefill, or both). The vLLM server
    log is not kept, so this is not checked yet.
  - Consequence: the 16 min cap binds far more often than the 8 min cap on Ada. On 78 base task-draws so far,
    11 timed out, against 0 of 237 on Ada. The readings stay within-Turing and paired as written. But this
    lane measures each tweak under a much tighter effective time budget, and calls40 especially may not get
    to use its extra calls. That goes into the reading-2 report.
  - Pace is about 3.5 h per job, so the three waves end around 07:30Z, 11:00Z and 14:30Z (02:30, 06:00 and
    09:30 EST), not the 1.5 h per job estimated above.

## Results (2026-11-19T13:30Z)

All 18 jobs completed with 79 rows each, between 2:54 and 3:27 h per job. The last one finished at 08:20 EST.

| Arm | d1-d6 | Mean | SD | Paired diff vs base (90% bootstrap CI) | Tasks up / down | Time-cap stops (16 min) | Empty patches |
|---|---|---|---|---|---|---|---|
| base | 5, 8, 9, 10, 9, 9 | **8.33** | 1.75 | - | - | 60/474 | 67/474 |
| pagedread (T-e4b-013) | 7, 5, 10, 6, 4, 10 | 7.00 | 2.53 | -1.33 (-3.0, +0.17) | 6 / 11 | 87/474 | 84/474 |
| calls40 (T-e4b-001) | 9, 6, 6, 8, 8, 8 | 7.50 | 1.22 | -0.83 (-2.5, +0.83) | 6 / 10 | 85/474 | 71/474 |

- **Check 1 holds.**
  - 18 of 1422 task-draws (1.3%) had import errors.
  - Most are `coverage` (6) or names that do not exist, from the agent's own scripts (`pydantic.typing_inspection`,
    `fastapi._compat.v1`, `typing.AnyType`, ...). One is `pip`.
  - Every pytest header says Python 3.13.
  - No engine error appeared in any job log, and no draw is short.
- **Reading 2, lane offset: +1.67** (8.33 against the Ada R-008 base 6.67). That is within ±3, so the lane behaves
  like Ada within the no-change line.
  - 717 of 1422 task-draws ran to 480 s or more. On Ada that was 0 of 237.
  - The median model-step gap is 18.5 s, against 3.3 s on Ada.
  - So this lane runs each task under a much tighter effective time budget, and the resolve rate still matches.
- **Reading 3.**
  - **pagedread: not kept** (7.00 < 8.33 + 1.5).
  - **calls40: not kept** (7.50 < 8.33 + 1.5).
  - Neither meets the candidate mean, so the CI condition is not reached. Both point estimates are below the
    base.
  - Base draw-to-draw SD: **1.75 resolves** on cdev2-79. A +3 bar is about 1.7 SD of one draw.
- **Reported, not read (reading 4).**
  - No base task-draw used 28 or more tool calls, so on this lane the calls40 change has nothing to act on.
  - Its "not kept" says only that raising the cap does not help when the time cap binds first. The same was
    true on Ada (T-e4b-001's lesson).
- **For the ledger.** T-e4b-013 and T-e4b-001 now each have 6 more draws, both below the base. Neither is worth
  re-drawing.
