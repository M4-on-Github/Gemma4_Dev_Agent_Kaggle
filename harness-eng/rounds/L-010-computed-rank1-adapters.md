# L-010: computed rank-1 adapters, no gradient step (pre-registration)

Written 2026-11-27, before the job runs. Counts only. User instruction (2026-11-27): test writing adapter weights
from an analysis of the model instead of training them, after the "weight-space programming" post (Takehi et al.,
2026-11-02), whose language-model result subtracts one direction from the feed-forward output of two layers.

## Method (`tools/lora/wsp_edit.py`, this commit)

1. **Decision points** in rendered solver rows: the last token before an assistant turn. POS = turns whose call is an
   edit, in resolved fold-A rows (`d5`, 299 rows). NEG = turns at call index 8 or later whose call is not an edit, in
   unresolved fold-A rows that never edit (`d6`, built by `solver_to_sft.py --unresolved`: 717 rows, 86 never edit).
2. **Architecture map:** per layer, the mean residual difference POS − NEG on half of the tasks, and its separation
   (AUC) on the other half.
3. **Edit:** add k times that difference at the 1 or 2 best layers through a rank-1 change of the layer's
   `mlp.down_proj`, scaled so the added vector has weight 1 on the average token.
4. **Proxy score, held-out tasks, greedy generation from the decision point:** the share of stalled points whose next
   call is an edit, the same share at early points (call index below 2 in resolved rows), and the share with no
   parsable call. Six candidates and the base.
5. Each candidate is saved as a served-format adapter (rank 1, the edited modules only).

Model: the E4B first (cheap). Note before running: the E4B solver rarely stalls (86 of 717 unresolved attempts never
edit), so this run mainly proves the pipeline; the no-edit class is the 31B's (37% of failing attempts).

## Readings (written before the job runs)

1. **Map:** some layer in 6..34 separates held-out POS from NEG with AUC 0.75 or more. Otherwise no candidate is
   evaluated on tasks.
2. **Proxy:** a candidate is worth task draws only if its stalled-edit share is at least 15 points above the base's,
   its early-edit share is within 10 points of the base's, and its no-call share is within 5 points.
3. Task draws, if any, are pre-registered in this file before they are submitted.

**Blind guess.** Reading 1 met 70%. A candidate meets reading 2: 35%. A task-level gain: 10%.

## E4B run (job 68283, 2026-11-27, 49 min): pipeline works; sample too small to act on

- Points: 131 POS and 21 NEG decision points over 33 tasks (few E4B rows never edit and fit the length limit).
- **Reading 1 (map): met.** Held-out separation is 0.93-0.95 from layer 6 on (0.48-0.84 in layers 0-5), on 2 held-out
  NEG points only. The difference is 6-12% of the residual norm up to layer 12 and 23-33% from layer 16.
- **Reading 2 (proxy): not met, on 6 stalled and 30 early points.** Base: 0 of 6 stalled points edit next. Layer 10
  at k=2: 3 of 6 edit, early edits 1 of 30, but no parsable call in 4 of 30 early points against 1 (bar: within 5
  points). Layer 7 at k=1, 2, 4: 0 of 6. Layers 7 and 10 at k=2: 2 of 6, with 7 of 30 early points without a call.
- No E4B task draws: the sample is 6 points and stalling is not the E4B's failure.

**What it shows.** A rank-1 change computed from residual means does move the next action from reading to editing,
and stronger doses start to break the call format. The same job runs next on the 31B, whose failing attempts stall
far more often.

## 31B run (pre-registered 2026-11-27, before the job is submitted)

- POS: `d2/31b-all-lfold-a.jsonl` (254 resolved rows). NEG: `d6/31b-unres-lfold-a.jsonl`, built by
  `trace_to_sft.py --unresolved` from kfctl x8 on fold A: 187 rows, 95 never edit in their faithful prefix.
- Two Ada GPUs (`--device-map auto`), max length 14000, 24 stalled and 16 early evaluation points, 256 new tokens.
- Readings 1 and 2 as above. A candidate that meets reading 2 gets a served smoke and task draws, pre-registered
  here first; the adapter's decode cost on the 31B is measured in the smoke.

## 31B run: deviations and the edit loop (logged 2026-11-27, before any 31B score exists)

- Job 68285 ran out of GPU memory on 2 GPUs (all layers' states were kept on the GPU); the script now records only
  the decision positions and caps memory per GPU. Job 68286 found 7 stalled points: whole rows over the length limit
  were skipped, and stalled turns sit late in long rows; the script now uses the fitting prefix of a long row.
- Settings changed with that fix: a stalled turn counts from call index 6 (was 8); max length 13000 (was 14000);
  3 GPUs.
- **Edit loop (user instruction, 2026-11-27: run it the way the post does).** Job 68287 (one pass) was cancelled 37
  minutes in, before any output, and restarted with `--serve-hours`: after the preset candidates the job keeps the
  model loaded and scores candidate specs dropped into its queue (layer, strength, add or remove, source layer,
  sign, number of coordinates kept). After each score the next candidates are chosen from which stalled and early
  points changed. Reading 2 is unchanged and applies to the best candidate found; the number of candidates tried is
  reported with it, since picking the best of many on 24 + 16 points flatters it. Task draws decide.

## Edit loops, state on 2026-11-28 05:00 UTC

**Architecture finding (config files, 2026-11-28).** Full-attention layers: 31B 5, 11, 17, 23, 29, 35, 41, 47, 53, 59
(the other 50 see 1,024 tokens); E4B 5, 11, 17, 23, 29, 35, 41 (the other 35 see 512 tokens).

**E4B loop (job 68299; POS 181, NEG 151 points; 17 stalled and 20 early replay points; 22 candidates).**
Base: 0 of 17 stalled and 0 of 20 early points edit next; no call in 6 and 2.

| Candidate (layer 17 unless noted) | stalled edit | stalled no call | early edit | early no call |
|---|---|---|---|---|
| k 0.5 to 4, all coordinates | 13-14 | 0-1 | 13-18 | 2-6 |
| k 0.25 | 13 | 3 | 8 | 6 |
| k 0.18 | 7 | 10 | 4 | 6 |
| k 0.12 | 0 | 13 | 0 | 5 |
| 256 coordinates, k 0.5 | 15 | 1 | 9 | 2 |
| 256 coordinates, k 0.35 | 8 | 5 | 4 | 2 |
| 256 coordinates, k 0.25 | 5 | 8 | 2 | 2 |
| **128 coordinates, k 0.5** | **4** | **7** | **1** | **1** |
| 128 coordinates, k 0.35 | 2 | 8 | 0 | 3 |
| 64 coordinates, k 0.5; 32 coordinates, k 1 | 2; 5 | 11; 5 | 0; 0 | 2; 6 |
| layers 11, 14, 19, 23; 17+19; remove mode | 0 | 5-16 | 0-5 | 2-16 |

- Only layer 17, a full-attention layer, carries the switch. Layers 11 and 23 (also full attention) and 14 and 19
  (local) do not.
- **Reading 2 is met by one candidate, `c04` (128 coordinates, k 0.5):** stalled-edit share +23.5 points (bar +15),
  early-edit share +5 points (bar within 10), no-call share 8 of 37 against 8 of 37 (bar within 5 points). It is the
  best of 22 candidates on 37 points, so the replay numbers are optimistic.

**31B loop (job 68293; POS 115, NEG 274 points; 24 stalled and 16 early points; 9 candidates so far).** Base 0 of 24
and 0 of 16. Layers 21, 22 (k up to 8), 40 and 41: no stalled edit. Layer 23 at k 2: 1 of 24. **Layer 29 at k 2: 5
of 24, with 12 of 16 early points left without a call.** Lower doses and narrower forms of layer 29 are queued.

## E4B task draws for `c04` (pre-registered 2026-11-28, before any job)

- **Arm.** `trees/e4b-wsp-c04` = `trees/e4b-r041-retry-check` with the computed adapter on the solver (rank 1, one
  module, 26 kB). Control: rcheck x8 (8.12).
- **Smoke first.** It is also the first time the server loads a rank-1, one-module adapter file. Pass: both tasks
  served, no engine error, the solver's steps name the adapter.
- **Draws.** `L-010-e4b-c04-d1..d4` on cdev2-79, chained behind the smoke. Draw-1 kill gate: 25 or more empty
  patches or mean task wall above 300 s.
- **Decision** against rcheck x8: extend to 8 draws at +0.75 or more; promote at 8 with +1.5 and CI lower bound
  above -0.5; harm at -1.5.
- **Mechanism:** empty patches per draw (rcheck 3.9); first-edit call index; solver calls per attempt; retries.

**Blind guess.** The server loads the file: 75%. Empty patches fall: 40%. Extension: 12%.

## E4B `c04` on tasks: smoke and draw 1 (2026-11-28)

- **Smoke (job 68338):** both tasks served; the server loads the rank-1, one-module adapter file; the solver calls
  tools with it. The blind guess (75%) held.
- **Draw 1 (`L-010-e4b-c04-d1`, job 68339): 79 of 79 patches empty, mean wall 74 s. Kill gate met (25 or more
  empty); draws 2-4 cancelled unread** (they had also failed at server start on GPUs occupied by another user's
  processes and been resubmitted).
- Mechanism, calls per task against rcheck d1: `solve` 2.9 against 1.3, `edit_file` 4.0 against 4.1, `read_file`
  2.5 against 4.7, `run_command` 5.9 against 6.7. Per solver call that is about 1.4 edits after 0.9 reads: the
  solver edits almost at once, the edit changes nothing, and the root retries until its three attempts are used.
- **Reading.** The switch is causal on real tasks and far stronger served than on the 37 replay points, where the
  same edit left 16 of 20 early points untouched. The replay bar did not predict task behaviour.

## Dose step (pre-registered 2026-11-28, before any job)

The served strength is set by `lora_alpha` in the adapter's config, so the same file is served weaker without
recomputing: `trees/e4b-wsp-c04a50` (alpha 0.5, effective k 0.25) and `trees/e4b-wsp-c04a25` (alpha 0.25,
effective k 0.125). One draw each on cdev2-79 (`L-010-e4b-c04a50-d1`, `L-010-e4b-c04a25-d1`), about 0.5 GPU-h each.

- A dose goes on to three more draws only if its draw has 4 or fewer empty patches and 9 or more solves (rcheck
  draws: 2-6 empty, 7-10 solves). Otherwise the dose is closed.
- Reported for both: empty patches, solves, `solve` and `read_file` calls per task, mean wall.

**Blind guess.** Alpha 0.5 still above 25 empty: 60%. Alpha 0.25 indistinguishable from the control: 60%. Either
dose goes on: 12%.
