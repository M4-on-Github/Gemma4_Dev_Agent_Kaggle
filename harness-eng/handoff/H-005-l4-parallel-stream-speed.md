# H-005: 31B decode speed on L4x4 with 1, 2, 3 and 4 parallel streams (no tasks)

2026-11-28, from the cluster (`recursive-harness`, `harness-eng/rounds/R-052-31b-agree-checkpoint.md`).

## Why it needs Kaggle

- The cluster's best open 31B idea runs three attempts of one task in parallel and stops when two agree (R-052).
  Offline it is worth about +3 to +4 solves per 79; every race round so far lost that gain to time.
- Whether it fits 12 h depends on one number we have never measured: how much each stream slows when the L4x4
  server decodes 3 streams at once. Kaggle today runs one stream. On the cluster the server batches well (4 streams
  per GPU run at 0.67 of single-stream speed each), but L4x4 with tensor parallelism may differ.

## What to run (about 20 min of L4x4, no task data, no agent)

1. Start the model server exactly as the eval notebook does (same flags, 32k context).
2. For n in 1, 2, 3, 4: send n chat requests at the same moment, each with a prompt of about 8,000 tokens of plain
   filler text (different per stream, so nothing is cached) and `max_tokens` 400, thinking off, streaming on.
   Repeat three times per n.
3. Record per n: time to first token (prompt processing), decode tokens per second per stream, wall for all n to
   finish.
4. Repeat step 2 once with a 20,000-token prompt at n = 1 and n = 3.

## What to send back

A table of n against time-to-first-token and per-stream decode tok/s (median of three), for both prompt sizes.

## How it is read (fixed here, before the numbers exist)

- Per-stream decode at n = 3 of **0.90 or more** of n = 1: the three-attempt layout fits at the current 8 min cap.
- **0.75 to 0.90:** fits only with a shorter per-attempt budget; the cluster re-tests at that budget first.
- **Below 0.75:** three streams do not fit; fall back to two streams and use the n = 2 row.
- Time to first token at n = 3 above 2x the n = 1 value counts as a further 5% slowdown.
