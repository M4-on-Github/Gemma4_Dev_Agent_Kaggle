---
id: EXP-050-critic
exp: EXP-050
tier: prereg
verdict: ready
verified: regenerated
date: 2026-11-07
---

## Verdict
**Ready** (in the dispatch's terms, ready with no change needed before the upload). Variant A, sha `9de869bd...1ac0`, is the config EXP-038 ran, byte for byte, and the readings are complete and blind. Upload A as S-014 names it. This verdict does not replace the user's `approvals/S-014.txt`.

## Audit
- **P1 Readings: pass.** Rows 0 to 4 cover a blank and every k from 0 to 58, with no overlap. The MDE edges check out against 9.33: k = 5 is 4.33 below, k = 6 is 3.33 below, k = 13 is 3.67 above and k = 14 is 4.67 above. 77122bb precedes S-014, and nothing has been uploaded.
- **P2 Prediction: pass.** I recompute 5/48 x 0.8582 x 58 = 5.19. The Wilson interval on 5/48 is 0.0453 to 0.2217, which scales to 2.26 to 11.03. The Wilson interval on 28/174 is 0.114 to 0.223. The row probabilities sum to 100%. The 80% interval of 2 to 9 is a judgement, not derived, but it agrees with them.
- **EXP-038 item 4, all four present and correct.** §2.3 items 1 to 4 match EXP-038 critic lines 156 to 159:
  - the §5.8 override, with 18.00 h and 16.00 h;
  - k = 5;
  - F not fired and G = 0 of 15 (EXP-038 §9.7);
  - fastapi_13537 at 8 turns, 0 calls and 19.6 s (EXP-038 line 579).

  S-014's Risks section repeats them.
- **Zip identity: pass, and stronger than §2.1 states.**
  - The `agent/` directory in the bundle Kaggle returned (`runs/EXP-038-e4b-dev48/agent/`) matches all four members of A by sha256.
  - The kernel log shows budgets of 240 / 28 / 8 / 80 and the E4B model path.
  - The embedded zip decodes to `9de869bd`.
  - My own repack from LF blobs (`git -c core.autocrlf=false archive`) also gives `9de869bd`.
  - The tree has not changed since d2c11da.
- **Cap visibility: confirmed.** In `agent_runner.py`, lines 341-343 and 387 put the cap into the task message. A re-run of `out/exp050_time_visibility.py` reproduces the §2.2 counts: 48/48 at 8.0, 1 `get_status` call, 0 time-exhausted messages.
- **P5, A over B: A is right.**
  - The scorer completed #11 to #13 at the same 240 / 28 / 8 / 80 caps. The 31B's mean task time was 297 s, about 3.5 times the E4B's 85.7 s.
  - A would time out only if roughly 55-65% of hidden tasks ran to the cap (41% if each ran 752 s). On dev-48, 0 of 48 tasks reached the cap (Wilson upper bound 7.4%) [I].
  - B's 4.5-minute task message against the 8-minute system prompt is a contradiction no run has shown the model. B's gate compliance therefore buys an untested change and no measurable safety.

## Changes that can wait (none block)
1. **Clarification of row 0, written before the result.** Its time-profile clause and the contrary C-020 observation apply to a Notebook Timeout only. Any other scoring error is not a time observation and leaves C-020 alone. Its next step is to read the error, not to switch to B. Copy this line into §7 before the score lands.
2. **Row 0 names B as the next E4B upload, but §2.2 calls B untested.** Any later B upload needs its own pre-registration.
3. **`submissions.md` row 14 must carry the §5.8 override text when it is written at upload,** as rows 11 to 13 do.
