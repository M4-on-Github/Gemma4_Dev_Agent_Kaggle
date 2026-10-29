---
id: D-001
title: Our own 12.8 KB phased-prompt lineage, improved by single-variable surgery
decision: kill
status: killed
track: main
claims: [C-009, C-010, C-011, C-006, C-012, C-018]
date: 2026-10-29
---

Migrated 2026-10-29. This direction ran from the plan's Phase 1 (2026-10-14) to submission #10 (2026-10-27) without a written proposal; this file records it so its kill is on the ledger.

## What are we trying to do?
Reach the 0.12-0.15 band and then the top-3 band with our own phased prompt (LOCATE, REPRODUCE, EDIT, VERIFY, SUBMIT, with a budget ledger and state notes), changing one knob or one prompt rule per upload.

## How is it done today?
The public frontier is a 3,240-byte numbered protocol (contract, locate in a few reads, edit by call 12, one check, one repair, submit) at an 8-min cap with 28 calls (kg-rank3-apache §4), scored 0.24 as the best of >= 12 uploads.

## What's new in our approach?
Nothing that scored. Ten uploads on the lineage read 4, timeout, 7, 6, 8, 8, 7, 7, 6, 6 of 58 (`submissions.md` rows 1-10). The measured mechanisms it produced are real and carry over: the `edit_file` loss (C-004), the first-edit split (C-011), the thinking/loss link (C-010), the LB noise floor (C-001), the gate calibration (C-008).

## Options
- A. Continue surgery. Argument against: nine draws, no move; any single-knob LB contrast needs ~9 slots per arm (EXP-022 §2.3).
- B. **Kill for the LB; keep for the paper.** Chosen 2026-10-28 by EXP-027 ("Supersedes for the LB lineage"). The paper's contribution 1 rests on this lineage's traces and stays valid.
- Critic's dissent: not obtained (no critic existed). Backfill: a `direction` review may still be dispatched to record the weakest assumption in the kill.

## Expected score impact
None further. Best achieved 8/58.

## Risks and kill criteria
Kill criterion met: no upload above 8/58 in ten draws, including a 4-change bundle with a pre-committed 0.17 threshold (EXP-017).

## Cost
Ten upload slots, ~25 GPU-h (E0, EXP-003, EXP-025 two arms), Oct 14 to Oct 27.

## Midterm check
n/a (closed).

## Final check
Closed 2026-10-28. EXP-026 Arm C (heredoc route on this prompt) stays pre-registered for the paper and is run only if quota allows after D-002's arms.
