# S6 spec: 31B LoRA decode cost on Kaggle L4x4 (handoff, not a pre-registration)

Written 2026-11-21 on pleiades. Handed off as `harness-eng/handoff/H-001-*.md` on `all-work-consolidated-2026-11-20` (ec9cd31), suggested EXP-087. It cannot run from here: pleiades has no Kaggle CLI (installing it needs the user's
OK), and EXP-NNN files are kept on the other machine (memory note of 2026-11-17). The session there turns this into
the next free EXP-NNN, pre-registers it, and pushes it. Counts only.

## Question

What does serving the 31B with LoRA on cost in decode speed on the real L4x4 machine? L-005's Kaggle projection uses
r_L4 = 0.75 (the E4B value, EXP-047) until this is measured.

## Design (zero tasks, no agent)

- Notebook pattern: `notebooks/exp047_q4canary/q4_canary.py`. Metadata from `notebooks/exp083_sweep/kernel-metadata.json`
  (31B model source, pinned image), `competition_sources` exactly `["gemma-4-developer-agent"]` (without it the
  kernel gets 2 GPUs, EXP-047 v1). The EXP file carries `**Cohort:** none`; the notebook has no `RUN_AGENT` or
  `TASK_IDS`, which `guard_push.py` admits as a zero-task probe.
- Server config as the eval notebook: tp 4, gpu_memory_utilization 0.90, max_model_len 32768, the gemma4 parsers,
  thinking on.
- Adapters are built inside the notebook with `harness-eng/tools/make_lora_canary.py` logic from the served
  `*.weight_packed` header (zero B matrices, rank 16, alpha 32). Assert 410 modules / 820 tensors for `full_zero`
  and 230 modules for `attn_zero` (q 60, k 60, v 50, o 60).
- Boots: boot 0 LoRA off (base); boot 1 `--enable-lora --max-loras 1 --max-lora-rank 16` with `full_zero` only,
  as a shipped single-adapter tree serves it. `attn_zero` is optional (a third boot, about +0.15 h); R-013 already
  found the cost does not depend on adapter size.
- Probes per boot: 256 decoded tokens after a 12k-token prefill, 3 repeats, at 1 and 4 streams.

## Readings to pre-register

- R1, health: both boots up; in boot 1, `full_zero` vs the base name on the same server, mean |logprob delta| <= 1e-3.
- R2, the number: r_L4 = boot-1 `full_zero` decode tok/s / boot-0 base tok/s at 4 streams. Also record the same-boot
  ratio (boot-1 `full_zero` / boot-1 base name), since EXP-047's 0.75 and R-013's 0.916 are same-boot ratios.
- Readings: r_L4 >= 0.913 (as Ada; a 31B adapter needs only to break even on wall), 0.80-0.913 (an adapter must cut
  wall by the matching amount, L-005 formula), < 0.80 (a 31B adapter must cut wall by about 10% or more to fit
  11.0 h; L-005 is read with that value).

## Cost

Expected about 0.45 L4x4-h (two boots), worst case about 0.9 h at a 50-minute hard cap.
