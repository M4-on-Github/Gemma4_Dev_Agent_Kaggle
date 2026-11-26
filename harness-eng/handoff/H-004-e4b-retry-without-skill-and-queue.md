# H-004: upload plan for the last week, and the E4B retry without a skill script (handoff, not a pre-registration)

Written 2026-11-26 on pleiades. Counts only. Source: `recursive-harness`, `harness-eng/final-week-plan.md` and rounds
R-037 to R-041 (commit 67bc792).

## 1. The queue now sets the pace (Kaggle topics 760471, 761897, 761733, read 2026-11-26)

- Participants report 30-40 h from upload to score, and rising. The host's Nov 19 post gave 20-24 h.
- A team may hold one pending submission. So about three more scored uploads fit before Dec 2 23:59 UTC.
- No host answer on whether a submission still pending at the deadline is scored.
- Our account (API list, 2026-11-26): 17 submissions, all complete, none pending; the last is 2026-11-12 (row 17).
- A faulty scorer GPU, back to Oct 12, gave about 125 submissions a 0.00 at 3,230 bytes (topic 761004); the host is
  rerunning them. None of our 17 has that size.

## 2. Skill scripts on the official scorer (topics 758547, 758854; participant reports, no host answer)

- A skill-only bundle scored 0.00 twice while the same team's tool-based bundles scored 0.13-0.17.
- A second team found its skill script had indexed its own folder, not the task repository.
- If this holds, `e4b-r020-retry` (H-003) never retries on the scorer: `count.py` prints 1 on a read error.
  **H-003's tree should not be uploaded as an improvement.**

## 3. Replacement tree: `harness-eng/trees/e4b-r041-retry-check/` (copied here byte for byte)

- **Layout.** As H-003, with the skill removed. The root has `submit_patch`, the `solve` agent_tool and a second
  agent_tool `count_changes` (`sub_agents/check.yaml`): an E4B agent whose only tool is `run_command`, with one fixed
  command that counts changed non-test source files from `git status --porcelain`. It runs inside the task sandbox.
- **Cluster result (R-041, cdev2-79, Ada, 8 min).** 8 draws against 16 skill-retry draws (R-021 ×12 and 4 concurrent):
  8.12 against 7.81 solves per draw, **+0.31 (90% CI −0.94..+1.62)**; wall ratio 1.06; empty first attempts retried
  98 of 101; empty patches 3.88 per draw against 5.25.
- **The round's rule reads "not kept".** One mechanism bar was missed: re-solves after a count of 1 or more, 9.0 per
  draw against a bar of 2.0. The skill retry shows 7.1-7.8 on the same count, so the bar was set wrongly. The user
  decides whether to upload regardless; this file does not decide it.
- **Zip built on pleiades** with the packer's own `build_tree` and `write_zip` (the packer refuses the tree on the
  H-002 false error and the cap-only gate): 9 members, 5,157 bytes, sha256
  `fc9321c8a67046b8b37d7dd2cb6dac768bdfbdea1227cd12000a5d434ec496d9`. With LF blobs the same hash should reproduce
  here once H-002 is in; verify before any upload.
- **Not run on Kaggle.** Time projection as H-003 (about 4.4-4.9 h on L4x4). Our S-015 (an LlmAgent root over
  sub-agents) completed on the scorer at 0.05, so such layouts run there.

## 4. Suggested use of the remaining uploads (the user approves each one)

1. **Now: the 31B base zip `c22069db…`** (rows 11-13, 17). No 31B change beat it in R-037 to R-040.
2. **Next: the E4B.** `e4b-r041-retry-check` if the user accepts the layout risk; otherwise the EXP-050 single loop
   (row 14, 0.05).
3. **Last slot:** whichever final still lacks a scored run by then.

## 5. Closed on the cluster since H-003 (so they are not re-tried here)

| Round | Change | Result |
|---|---|---|
| R-037 | 31B calls 34, time 7 | −0.50 per draw (CI −2.62..+1.62), not kept |
| R-038 | 31B temperature 0.2 | −1.75 (CI −3.88..+0.25), harm |
| R-039 | 31B code-map pipeline; map only | killed at the d1 time gate; no gain where it ran in full |
| R-040 | 31B bounded-draft pipeline | killed at d1 (28 empty, 499 s) |
| L-008, L-008b | E4B self-distilled LoRA | −0.50 and −0.75, not kept |
