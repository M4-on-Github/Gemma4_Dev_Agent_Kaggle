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
