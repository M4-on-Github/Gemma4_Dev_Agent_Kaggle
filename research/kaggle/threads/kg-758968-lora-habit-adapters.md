---
id: kg-758968-lora-habit-adapters
topic_id: 758968, 759514 (LoRA probes); 759848 (legality, see deadline note)
title: LoRA habit adapters changed the agent's behaviour offline but not the live score (758968); five LoRA probes with identical scores (759514)
author: Nir Aberman (758968); xz, VELVRIN, Ankith Savio (759514); Mohammad Shadab Alam (reply in 758968)
author_role: participant
credibility: medium to low; offline counts quoted, no live draw counts given
topics: [lora, adapters, noise, grading]
first_seen: 2026-11-17
last_checked: 2026-11-17
---

## Summary
Two participant threads report that LoRA adapters changed behaviour in offline tests (reasoning and tool-call habits) but not the public score, and that the same public notebook can span 0.13 to 0.20. A commenter reports one rank-8 LoRA scoring 0.17 "more often than the base", with no draw counts. The organiser's sample tool-call adapter was read in an earlier pass; nothing new about it in this window.

## Claims made (quoted)
- [M] Nir Aberman, 758968, 2026-11-13, "LoRA habit adapters changed the agent's behaviour offline but not the live score: three mechanisms": reasoning rate dropped to 0 of 109 calls; training targets had 0 of 993 rows with reasoning.
- [M] Reply 3554629, Mohammad Shadab Alam, 2026-11-13: "My rank-8 LoRA trained to enforce edit deadline + forced get_code_neighbors, scores 0.17 more often than the base." No draw counts; the author asked for them (3554663), no answer posted.
- [M] 759514, "five LoRA probes with identical scores", xz, 2026-11-16, 6 comments. xz (11-17): temperature 0.2, "the same as in the public notebook". VELVRIN (11-17): "same here i tried with different different and same score 0.15". Ankith Savio (11-16): "Same public notebook : 0.13 - 0.20 The variance is quite high."
- [M] 759848 (Marco Pereira, 2026-11-17): "Host ruling: is a PEFT LoRA derived by SVD of the model's own tensor acceptable? (not trained)". No comments; no host text. See the deadline and rules note.

## Possible claims for us
- [I] A LoRA changes what the model does offline without changing the public score in these reports; do not assume an adapter gain from offline traces alone.
- [I] No scored LoRA result in this window has a draw count. Any adapter claim we make must be a paired dev-48 result with the base, per plan §5.5.
- [I] Legality is unsettled (no host text in 759848 or 756792). Hold LoRA candidates until a staff answer exists.

## Files
None downloaded for these threads. The sample adapter reading from the earlier pass is under `untrusted/` and is not re-read here.

## Updates
- 2026-11-17: first read of 758968 (body and reply 3554629) and 759514 (comments 11-16 and 11-17). Nothing from the organiser on adapters in the window.
