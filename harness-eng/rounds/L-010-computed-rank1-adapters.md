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
