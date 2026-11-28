# L-009: adapters trained on public solved trajectories, 31B and E4B (pre-registration)

Written 2026-11-27, before any training job of this round is submitted. Counts only.
User instruction (2026-11-27): train both models on public solved trajectories.

## Why

Every harness-side change since `31b-base` and the E4B retry tree read as a null or harm (R-037 to R-049 so far).
36 of 79 cdev2 tasks are never solved by the 31B in any design. The adapters so far (L-003 to L-008) were trained on
our own models' solves, which cannot teach what the model does not already do. This round trains on a stronger
teacher's solves (D3 in `rounds/L-001-lora-data-desk.md`).

## Data

- **Source.** Hugging Face `SWE-bench/SWE-smith-trajectories`, split `tool` (MIT licence; 24,100 trajectories of an
  agent driven by two Claude Sonnet versions on synthetic bugs in public Python repositories; 9,427 resolved).
  Downloaded 2026-11-27 to `/data/mmyatmau/gemma4-lora/data/d3/` (1.08 GB), on the user's instruction.
- **Conversion.** `tools/lora/smith_to_sft.py` (this commit): resolved trajectories with 4 to 24 mapped tool calls
  and at least one edit; the source agent's shell, view, replace, create and submit actions are mapped onto
  `run_command`, `read_file`, `edit_file`, `write_file` and `submit_patch`, with tool responses rebuilt in the
  harness's JSON shapes and the harness's own task prompt. Trajectories with an unmapped action or an abbreviated
  long-file view are dropped. The two repositories of cdev2-79 are excluded. At most 40 rows per repository.
  - 31B layout: 1,948 rows over 107 repositories, median 14 calls.
  - E4B solver layout (the `solve` sub-agent's prompt, five tools, closing text turn): 1,893 rows, median 12 calls.
- **Loss.** `--default-train call`: only the tool calls and the closing turn are trained. The teacher's text before
  each call stays in the context, cut to 400 characters, and is not trained.
- **Known gaps.** No workspace tree in the task prompt; edit diffs are rebuilt from the two strings without file
  line numbers; a command's exit code is always 0; the source bugs are synthetic.

## Training

| Adapter | Model | Rows | Tokens (trained) | Settings | Est. cost |
|---|---|---|---|---|---|
| `L-009-s31` | 31B (`--packed`) | 400 (dry run on 600: 567 train, 22 val, 5.26M tokens, median 8,786) | about 3.5M (0.6M) | rank 16, alpha 32, lr 1e-4, 1 epoch, accumulation 4, warmup 10, max-len 14000 | about 7 Ada GPU-h |
| `L-009-se4` | E4B | 700 (dry run on 900: 871 train, 25 val, 7.68M tokens) | about 6.0M (1.0M) | same, `--system-from-row`, five tools | about 6-8 Ada GPU-h |

**Training readings.** (1) The job ends with `final/` written and no error. (2) Validation loss at the end is below
its value at step 0. An adapter that fails either is not evaluated.

## Evaluation

Pre-registered in this file before any evaluation job is submitted, once the adapters exist: full cdev2-79 (no
task of it is in the training data), against kfctl x8 for the 31B and rcheck x8 for the E4B, with the L-005 serving
projection for the 31B's time.

**Blind guess.** Either adapter beats its control by 1.5 or more: 15% each. The 31B adapter fits the time budget
without a lower time cap: 25%.

## Training results

- **Deviation (31B).** The first 31B job (68279) ran out of GPU memory after 18 minutes: a cancelled evaluation job
  had not yet released the same GPU. Resubmitted unchanged as 68281.
- **`L-009-se4` (E4B, job 68280, 1 h 40 min).** 676 train rows, 22 validation rows, 169 steps. Training reading 1:
  `final/` written, no error. Reading 2: validation loss 0.3185 at step 0, 0.1457 at the end. Both pass.

## E4B evaluation (pre-registered 2026-11-27, before any evaluation job)

- **Arm.** `trees/e4b-sw-s9` = `trees/e4b-r041-retry-check` (the R-041 tree, the current E4B candidate layout) with
  `adapter: s9` on the solver; the root and the check agent stay on the base weights. The adapter files are copied
  to `trees/e4b-sw-s9/adapters/s9/` (gitignored).
- **Control.** `R-041-e4b-rcheck-d1..d8` (8.12 per draw, mean task wall 149.2 s), reused. They ran two days earlier
  without LoRA serving, so wall is compared with that in mind.
- **Runs.** Smoke on `runs/_cohorts/smoke-te.txt`; then `L-009-e4b-s9-d1..d4` on `cohorts/cdev2-79.txt`,
  concurrency 4, flags as R-041. No cdev2 task or repository is in the training data.
- **Readings.**
  1. Smoke: both tasks served, no engine error, the solver's steps name the adapter.
  2. Served check per draw: 79 rows, all served; one re-run with an `r` suffix.
  3. Draw-1 kill gate: 25 or more empty patches, or mean task wall above 300 s. A kill cancels the rest unread.
  4. Extension: d5-d8 only if d1-d4 read +0.5 or more against rcheck x8.
  5. Decision at 8 draws (`tools/paired_boot.py` against rcheck x8): **promote** at +1.5 or more with CI lower bound
     above -0.5 and mean task wall 300 s or less; **harm** at -1.5 or less; **not kept** otherwise.
  6. Reported: empty patches, time-cap tasks, mean wall, tool calls per task, patch resolve rate.

### E4B smoke (job 68288, 6 min 18 s): PASS

2 of 2 rows SUCCESS and served; no engine error; every solver step names `s9`, the root's steps name the base model.
Draws d1-d4 (68289-68292) started by their `afterok` chain.

### Deviation (logged 2026-11-28 00:06 UTC, before any resolved count of this round is looked at)

The user asked for the E4B result while d4 was at 37 of 79 tasks. d1-d3 (complete, 79 served rows each) are read now
as an interim; the extension rule and the decision are still applied to d1-d4 as written, and the rule is mechanical,
so the early look cannot change it. Draw-1 gate, applied first: d1 has 1 empty patch (bar 25) and a mean task wall of
208.4 s (bar 300 s): pass.

### E4B interim, d1-d3 (2026-11-28; d4 still running)

- Served: 79 rows, all served, in each of d1-d3.
- **s9 solves 2, 0, 1 (1.00 per draw) against rcheck 8.12: −7.12 per draw, 90% CI −10.88..−3.67.**
- Mechanism, per draw or per task (s9 against rcheck):
  - patches 75.3 against 75.1 per draw, but **77% of s9 patches contain only new files** (rcheck 0%); 23% modify an
    existing file (rcheck 99%). New files per patch 2.68; in d1 all 163 are at the repository root and most are
    named as reproduction scripts.
  - a patch resolves at 0.013 against 0.108; time-cap tasks 12.3 against 1.8; mean task wall 203.0 s against 149.2 s.
  - solver calls per task in d1: `write_file` 5.1 (rcheck 0.08); `read_file` 13.9 (4.7), of which 4.1 fail on a path
    that does not exist (0.19); `edit_file` 1.0 succeed and about 4.6 fail (rcheck: about 2.1 fail of 4.1);
    `run_command` errors 7.5 (1.5).

**Reading.** The adapter copied the teacher's routine (explore, write a reproduction script, run it, then edit) and
the E4B cannot finish it: it writes the scripts, guesses file paths, fails most edits and hands in the scripts. The
decision is applied when d4 ends; no extension is possible from here (d1-d3 already put d1-d4 below +0.5).

**Next (L-009b, pre-registered below before training).** Same source, different selection: only trajectories that
create no file and make a successful `edit_file`, at most 14 calls; failed script runs shown as command errors; mixed
with the model's own resolved rows so that its working edit and path habits are kept.

## L-009b: direct-fix selection, mixed with own solves (pre-registered 2026-11-28, before training)

- **Data change.** No teacher trajectory is free of a created file (3,751 of 3,751 candidates create one), so the
  routine is stripped instead: every created file, and every command that names one, is removed from the trajectory
  (31,835 steps). Kept: trajectories with a successful `edit_file` and 3 to 14 remaining calls. A failed script run
  is now shown as the harness shows a failed command. Result: 2,436 rows (31B layout, median 8 calls) and 2,417
  rows (E4B solver layout, median 7 calls) over 109 repositories.
- **Mix.** Each adapter also gets the model's own resolved fold-A rows, so that its working path and edit habits
  stay in the training signal: E4B `d5/e4b-solver-lfold-a.jsonl` (299 rows, at most 8 per task); 31B
  `d2/31b-fast-stop-lfold-a.jsonl` (76 rows).
- **Adapters.** `L-009b-se4`: 500 direct rows + d5. `L-009b-s31`: 400 direct rows + d2-fast. Other settings as
  L-009 (`--default-train call`, rank 16, lr 1e-4, 1 epoch, accumulation 4).
- **Evaluation consequence.** Fold-A tasks are now in training, so the clean reading is on the 40 `lfold-b` tasks
  (against the same control's fold-B rows); the full cdev2-79 count is reported beside it.
- The first 31B adapter (`L-009-s31`, still training on the unstripped data) is kept and gets one draw, as a check
  of whether the 31B copies the routine as the E4B did.
- **Readings.** Training readings as L-009. Per adapter: smoke; d1 with a kill gate (25 or more empty patches, mean
  wall above 300 s for the E4B or 452 s for the 31B, or more than 30% of patches without a modified existing
  file); then d1-d4 on cdev2-79. Decision on fold B over 4 draws against the control's 8: extend to 8 draws at +0.5
  or more; promote at 8 draws with +1.0 or more on fold B and CI lower bound above -0.5.

**Blind guess.** The E4B b-adapter is no longer harmful (within 1.5 of control): 55%; beats control by 1 on fold B:
12%. The 31B b-adapter beats control: 15%.

### E4B decision, d1-d4 (2026-11-28, readings applied as written): harm

All four draws have 79 served rows. s9 solves 2, 0, 1, 0 (0.75 per draw) against rcheck 8.12: **−7.38 per draw, 90%
CI −11.12..−3.88**. No extension. The mechanism is the interim's: the adapter hands in reproduction scripts.

### L-009b-se4 training (job 68297, 1 h 03 min)

536 train rows and 23 validation rows, 134 steps; `final/` written, no error; validation loss 0.3503 at step 0,
0.1560 at the end. Both training readings pass.
- **Deviation from the stated mix.** The trainer's default cap of 8 rows per task and the length limit kept 59 of the
  299 own rows (217 over the cap, 31 too long), so the mix is 500 public to 59 own, not 500 to 299. Evaluated as
  trained; the fold-B reading stands as written.
- Tree `trees/e4b-sw-s9b` (as `e4b-sw-s9` with adapter `s9b`). Smoke, then `L-009b-e4b-s9b-d1..d4` on cdev2-79,
  all queued behind the smoke; the d1 kill gate is applied by hand and cancels d2-d4 unread if it fails.

### L-009b E4B: killed at the draw-1 gate (2026-11-28)

Smoke (68300) passed. d1 (68301): 79 rows, all served; **32 empty patches (bar 25): kill.** d2-d4 (68302-68304)
were cancelled unread (d2 had 10 or more rows). No resolved count of d1 was looked at.
- What the strip fixed: 9% of patches modify no existing file (s9: 77%); `write_file` 0.1 per task (s9: 5.1).
- What is still wrong, per task in d1 against rcheck d1: `edit_file` fails 6.3 times and succeeds 1.3 (rcheck 2.1 and
  1.9); `read_file` fails 3.7 times (0.2). 25 of the 32 empty tasks have no successful edit call. Mean task wall
  120.7 s.

**Cause, found in the data.** The harness shows less than the teacher saw: 150 lines per read and 5,000 characters
per command. The converter cut the teacher's observations to those limits but kept its later actions, so many
trained edits name an `old_string`, and many reads a path, that is nowhere in the context the row shows. Checked on
the stripped set: 2,141 trajectories have such an edit and 505 more such a read, out of about 3,600. Those rows teach
the model to write edit text and paths from nothing.

## L-009c: grounded rows only (pre-registered 2026-11-28, before training)

- **Data.** As L-009b, plus `--grounded`: a trajectory is kept only if every edit's `old_string` and every read
  path occurs in the problem statement or in a tool response shown before it. 954 rows (31B layout, median 7 calls)
  and 933 rows (E4B solver layout, median 6 calls) over 98-99 repositories.
- **Mix.** Own resolved fold-A rows with `--cap-per-task 40`, so that they are not cut to 8 per task as in L-009b.
- **Adapters.** `L-009c-se4`: 600 grounded rows + d5. `L-009c-s31`: 400 grounded rows + d2-fast. Settings as before.
  The L-009b 31B training (68298, on ungrounded rows) was cancelled at step 44, unread and unevaluated.
- **Readings.** As L-009b (training readings; smoke; d1 kill gate; fold-B decision over 4 draws, extension at +0.5,
  promote at 8 draws with +1.0 and CI lower bound above -0.5).

**Blind guess.** The E4B c-adapter passes the d1 gate: 60%; is within 1.5 of control: 45%; beats it by 1 on fold B:
12%. The 31B c-adapter beats control: 15%.

### L-009-s31 training (job 68281) and its check draw

`final/` written, no error. Tree `trees/31b-kf-s31` = `trees/31b-kf-ctl` with `adapter: s31`. As pre-registered in
L-009b it gets a smoke and one draw (`L-009-31b-s31-d1`, cdev2-79, concurrency 4) as a check of whether the 31B
copies the teacher's routine and of the adapter's decode cost; it was trained on the unstripped, ungrounded rows, so
no gain is expected and no further draw follows unless d1 solves 33 or more.

### L-009c-se4 training (job 68316, 1 h 13 min)

691 train rows (600 grounded public rows and 125 own rows before the validation split; 86 own rows over the cap of 40
per task and 88 too long), 34 validation rows; `final/` written, no error; validation loss 0.2925 at step 0, 0.1433
at the end. Tree `trees/e4b-sw-s9c`. Smoke, then `L-009c-e4b-s9c-d1..d4`, d1 gate by hand as for L-009b.
