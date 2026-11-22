# Handoffs from the pleiades cluster

The cluster cannot push Kaggle kernels (no Kaggle CLI there) and does not write `experiments/` or EXP numbers. Work
that needs a real L4x4 run, the Kaggle validator in the real image, or an upload is written here as a handoff. The
session on this machine turns a handoff into an EXP-NNN pre-registration and pushes it; the handoff file is then
marked `taken: EXP-NNN` and kept.

The cluster's full record (rounds R-001..R-015, LoRA rounds L-001..L-005, lessons, directions) is on the
`recursive-harness` branch under `harness-eng/`. This branch's `harness-eng/` stops at R-012 (6d81a84).

| Id | Date | What | Why it needs Kaggle | Status |
|---|---|---|---|---|
| H-001 | 2026-11-21 | 31B LoRA-on vs LoRA-off decode on L4x4, zero-adapter probe, no tasks | the 31B L4 LoRA cost is unmeasured; the 31B adapter (L-005) must fit 11.0 h on L4 | open; suggested EXP-087 |
| H-002 | 2026-11-21 | validator false error `root agent has no way to modify files` on agent_tool roots; pack-closure test | the fix is on this branch's `tools/`, and a kept R-016/R-017 solver tree must pack and pass the Kaggle validator | open; **needed now**: R-016 and R-017 were dropped, but R-021's retry tree (H-003) has the same `agent_tool` root |
| H-003 | 2026-11-22 | E4B retry-on-empty layout (R-021: +1.08 solves per draw, CI +0.08..+2.08, wall 1.23x); tree copied to `harness-eng/trees/e4b-r020-retry/` | the candidate needs the 4.5-min cap, the H-002 fix, packing and a dev-48 L4x4 run before upload | open; suggested EXP-088; needs H-002 |

## Cluster facts this branch does not have yet (counts only)

- **LoRA serving.** R-013: serving the 31B with LoRA on costs 0.916x decode on Ada (same server, zero adapter, outputs
  unchanged), and the cost does not depend on adapter size. EXP-047's 0.75x is the E4B on L4.
- **E4B adapter.** L-003 trains a rank-16 adapter on synthetic edit-copy rows plus 31B fold-A solves; the 1-epoch
  adapter runs about 1.55x base task wall on Turing, which still projects to about 4.6-6.2 h on Kaggle. Results due
  2026-11-21.
- **31B adapter.** L-005 trains on the 31B's own fastest complete fold-A solves (76 rows, median 11 calls). To fit
  11.0 h it must cut mean task wall by about 9% at an L4 LoRA cost of 0.75x; H-001 replaces that planning value.
- **31B prompt.** R-015 (worked example in the system prompt): killed at draw 1 (resolved 25, at the bar).
- **Framework (2026-11-22, `recursive-harness` `harness-eng/framework.md`).** E4B: retry on an empty attempt (H-003). 31B: the
  single agent stays; R-014, R-015, R-016, L-005 and L-006 were each killed at draw 1, most on projected wall.
- **E4B adapters.** L-003 a1 and L-007 a2 killed (a2: call cap in 38 of 40 tasks). No E4B adapter before the freeze.
- **E4B parallel drafts.** Closed by EXP-074 (no selectable draft touches gold on solvable tasks).
