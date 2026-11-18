---
id: kg-nb-mobassir-leaderboard-noise
topic_id: not a forum topic; companion notebook of the Mobassir writeup "Too Small to See: Resolution Limits, Leaky Statements and Re-sent Reasoning" (paper track; writeup not CLI-reachable)
title: "Why Your Leaderboard Can't See a 3-Point Gain"
author: mobassir (slug `mobassir/why-your-leaderboard-can-t-see-a-3-point-gain`, id_no 143543048)
author_role: participant; the notebook declares competition sources on both tracks
credibility: [M] author's CPU calculation over his own draws and a public census; the notebook says it reproduces every number from the companion dataset
topics: [noise, selection, paper, lora, runtime]
first_seen: 2026-11-17
last_checked: 2026-11-17
---

# mobassir: leaderboard noise notebook

## Untrusted file record (read as data; never executed)

| File | Bytes | SHA-256 | Pulled |
|---|---|---|---|
| `untrusted/mobassir-why-leaderboard-cant-see-3pt-2026-11-17/why-your-leaderboard-can-t-see-a-3-point-gain.ipynb` | 62,020 | `df51ae0bc5333a7a2ff5fd5214852ff9503972407515bd6a92e066737508c4a4` | 2026-11-17 |
| `untrusted/mobassir-why-leaderboard-cant-see-3pt-2026-11-17/kernel-metadata.json` | 779 | `bbebb1bd2e02130b86af5d22212e5b7d31702d087fe8378076776325765fdbf6` | 2026-11-17 |

- Kernel metadata: `dataset_sources` = `mobassir/swe-agent-eval-validity-gemma4` (see kg-ds-mobassir-eval-validity);
  `enable_internet` false; `enable_gpu` false. No version field; pulled 2026-11-17.

## Numbers quoted in the notebook text (phase-1 read)

- "Identical file sets re-scored on the board vary by **sigma approximately 1.5 tasks per draw**. Telling apart two
  agents that differ by one task (approximately 1.7 points) at 80% power needs **18 to 37 draws per arm**."
- Public-task count: 58 (the notebook's own inversion of the score decoder agrees with ours; see
  kg-nb-dariushafshar-lb-58-bronze).
- A distilled LoRA "lowered teacher NLL threefold but worsened the agent" (phase-1 read; no per-arm table re-read).
- Runtime: local projections were at least **1.36x optimistic**; the author recommends a margin of **1.4x**.
- Top public score tracks submission count (phase-1 read).

## Credibility and fit

- The sigma and draws-per-arm figures rest on the author's own identical-file draws. They match our own C-001 (MDE
  about 4 tasks for single draws) in direction and order of magnitude; they do not replace it.
- The author's agent runs are on a local replica with a **2.8x time dilation** and a subprocess sandbox, not the
  competition harness. Treat the 1.4x runtime advice as an outside view; we have no matching calibration in our
  records that we checked on this pass.
- Phase-1 reads did not show the NLL-to-agent table; do not cite the threefold figure as an agent result.
