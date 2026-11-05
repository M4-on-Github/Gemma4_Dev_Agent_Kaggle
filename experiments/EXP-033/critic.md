---
id: EXP-033-critic
exp: EXP-033
tier: light
verdict: accepted
verified: regenerated
date: 2026-11-05
---

## Verdict
**accepted.** Row 3 governs, applied as written. The E4B runs the v24 single loop end to end on smoke-8:
- 8 of 8 ran, 0 of 8 capped, 0 malformed calls of 43;
- 6 of 8 tasks ended with a non-empty patch;
- one draw had a mean wall of 56.9 s and left a mean of 423 s under the 480 s cap.

Resolves (2 of 8) are recorded, not read. The 56.9 s and 423 s describe this draw, not the config. EXP-038 ran the same zip on the same ids and took 78.3 s.

## Audit
1. **Order: pass.** The pre-registration is d2c11da (13:36:58 UTC), and the kernel was queued at about 13:37. `git diff d2c11da HEAD` only appends to §7, §8, §9 and Status.
2. **Cohort and arm: pass.**
   - Ids equal smoke-8, and `err` is empty on 8 of 8.
   - The embedded zip is `9de869bd…1ac0`, as in §2, and runs at 240 / 28 / 8 / 80.
   - `diff -ru` against the EXP-027 tree shows the model line only.
3. **Numbers: pass.**
   - `analyze_traces.py --out` (scratch) reproduces `e4b/summary.jsonl` and the run's `aggregates.json` exactly.
   - Wall: total 455.5 s, mean 56.94 s; 76 turns at 5.99 s per turn.
   - Cap room: mean 423.06 s, minimum 389.3 s.
   - 1 compaction, 7 edit failures, 34,955 output tokens.
   - Largest per-step completion: 4,881 tokens (httpx_3672).
   - First-edit indices: 3, 3, 3, 3, 4, 4, 5 and never.
   - Thinking events appear in 8 of 8 traces.
   - The kernel log spans 900.3 s, which is 0.25 GPU-h. `estimate_budget` gives 5.82 h.
8. **Hygiene: pass.** These name and count only:
   - §9;
   - `e4b/summary.jsonl` (its strings are run paths and tool names);
   - the README row.

   The leaked marker named in E3 is a fixed token of the public chat template, not model prose.

**The 56.9 s as a reference (dispatch item).**
- EXP-038 ran the byte-identical zip (same sha, all 4 members equal) at temperature 1.0. On these 8 ids:
  - mean wall 78.35 s, slower on 6 of 8;
  - 54 calls against 43;
  - 7.84 s per turn against 5.99;
  - httpx_3672 and requests_7205 went from empty to non-empty patches.
- What may be said: "EXP-033 measured 56.9 s on one draw".
- What may not be said: that this is the config's speed, or a fixed bar. The steadier reference is the dev-48 mean of 85.7 s.
- The 423 s is per-task cap room. The 10.5 h rule binds first, at 225.6 s per task (EXP-038 row T).
- My inference: `wall_s` includes grading, because the gaps between log stamps equal `agent=`. The room is therefore slightly understated, not overstated.

## Required fixes (non-gating)

```
Lead, plan EXP-033 line: "mean wall 56.9 s, 423 s left under the cap" -> "mean wall 56.9 s and 423 s
left under the cap on one draw (same zip, same ids: 78.3 s in EXP-038; dev-48 mean 85.7 s)";
"Critic `light` review not yet done" -> "critic light accepted".
Lead, plan voting line: "(about 423 s spare, 45.6x KV room)" -> "(about 225 s per task spare under the
10.5 h rule, EXP-038 row T; 423 s cap room on one smoke-8 draw; 45.6x KV room)".
Lead, C-020 sources: "mean wall 56.9 s, 423 s left under the cap" -> "mean wall 56.9 s and 423 s left
under the cap on one draw (78.3 s on the same ids in EXP-038)"; C-020 tests: "smoke-8; critic review
pending" -> "smoke-8; critic light accepted".
Lead, C-023 expected gain: replace "The E4B single loop leaves about 423 s under the cap (EXP-033,
smoke-8), which is the room voting would spend." with "The E4B single loop left 423 s under the cap on
one smoke-8 draw (EXP-033) and 394 s on dev-48 (EXP-038); the 10.5 h rule binds first, at about 225.6 s
per task (EXP-038 row T), which is the room voting would spend."
```
