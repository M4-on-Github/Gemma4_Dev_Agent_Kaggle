# EXP-048 — Desk costing of a narrow exact-copy LoRA for the E4B (C-024): data, training, size, and the risk outside edits

**Date:** 2026-11-05
**Type:** desk note, L0 of the screening ladder. Zero GPU, nothing built, nothing pushed. Adapter training is not approved (user decision 2026-11-06, D-006); this file only prices it.
**Cohort:** none (no task runs)
**Ladder:** D-006 stage 2, priced ahead of its gate. Gated on EXP-047 (the Q4 canary): nothing here is asked for unless EXP-047 reads A3 or A4 and B2 or B3 (EXP-047 section 5).
**Serves:** C-024 (narrow exact-copy adapter), C-013 (the negative adapter datum), Q4.
**Relates:** EXP-043 (why the E4B's `edit_file` calls fail), EXP-044 (the failed-edit-8 screen design C-024's endpoint borrows), EXP-046 (the role team, killed at its desk check, so the adapter would serve the whole single loop), EXP-047 (the canary), lit note in 3bc1162 (format LoRA trainable at 8B; exact-copy arguments unmeasured).
**Tags:** [V] verified in source or by a check run here, [M] community or mirror, [I] inference.

## 1. The adapter being priced

A LoRA on the E4B trained only to do one thing: given a file window as the harness's file-reading tool shows it, emit an `edit_file` call with every mandatory argument present and an old string that is an exact, unique substring of that window. Only the weights ship (`submission/adapters/<name>/`, discovered by `discover_adapters`, served by the harness's vLLM; EXP-047 section 1). No training data, script output or window text enters git or the submission (`plan.md:52`).

C-024's own ceiling: about 1 task of 48 at most, probably less [I, the critic's text in `knowledge/claims.md` C-024]. Not measurable on resolves; the endpoint is the share of failed-edit-8 tasks with an applied edit (EXP-044's design).

## 2. Where the training pairs come from, and the rules question

**Pairs need no agent run.** Each pair is (a shown window, the target call):

1. Pick a source file and a window of 40 to 150 lines.
2. Render the window with the harness's own file-reading tool from the wheelhouse (`swegemma`), called in the kernel on that file, so that line numbering and headers are exactly what the model sees in a run. Wrap it as a tool-result turn after a short own-words instruction ("change X in this file").
3. Pick a span of 2 to 8 lines inside the window that occurs exactly once in the file; make a small, valid change to it (rename a local name, change a literal, add or drop one line).
4. The target is the assistant turn that calls `edit_file` with the file path, the span as the old string and the changed span as the new string, rendered through the E4B tokenizer's own chat template and tool-call format.
5. Loss on the assistant call tokens only.

Data generation is CPU work inside a kernel: minutes for a few thousand pairs [I]. Zero GPU-h.

**The source files.**

- **Recommended: public files only.** The Python standard library and the site-packages sources already present in the Kaggle image (thousands of `.py` files under permissive licences, PSF and others). Rule status: "External data, code and models are allowed if public and free" (`.claude/skills/competition-brief/SKILL.md:47`, [V] as recorded there). A training kernel built this way attaches no competition source at all, like EXP-047. That removes the question of competition data leaving the kernel.
- **The competition's repo snapshots: unknown.** We hold no record of the rules or data pages on whether competition data may be used to train weights that ship. The brief records only that competition data never enters git or a release (`plan.md:52`). The scout's 2026-11-05 grading-environment digest notes that the rules and data pages were not read (blocked by the Bash guard). Even if allowed, the gain over public files is unclear: the hidden set is private repos, so the snapshots' code is no closer to it than the standard library is [I]. **Status: unknown; not needed for this design.**

## 3. Training cost on Kaggle hardware [I unless tagged]

Assumptions:

- About 4e9 compute parameters per token (the "E4B" effective size).
- 3,000 pairs of about 1,000 tokens each, so 3M tokens per epoch, for 1 to 2 epochs.
- FLOPs about 6 N per token as an upper bound. LoRA with frozen weights is nearer 4 N, since no weight gradients are needed for the base.
- L4 at about 121 TFLOPs dense BF16 peak, 30% utilisation, so about 36 TFLOPs effective per GPU.

The arithmetic:

- 6 x 4e9 x 3e6 = 7.2e16 FLOPs per epoch.
- That is about 2,000 s on one L4, or about 500 to 700 s on L4x4 data-parallel.
- Per training kernel: setup and loading (wheel installs, about 5 to 10 min), 1 to 2 epochs, and an offline eval (section 5 item 2).

| Stage | Work | GPU-h (L4x4) | Basis |
|---|---|---|---|
| 0 | EXP-047 canary (applied? KV with an adapter?) | 0.20-0.35, capped 0.5 | EXP-047 section 2.5 |
| 1 | Pair generation in a CPU kernel, public files | 0 | CPU only, minutes |
| 2 | Training kernel: load, 1-2 epochs of 3M tokens, save | 0.3-0.7 | FLOPs above; overhead from EXP-033 (about 445 s to a served model) |
| 3 | Offline eval in the same or a second kernel: vLLM with the adapter, held-out public windows, exact-copy rate and drift probe, base against adapter | 0.15-0.3 | EXP-047 boot of about 5 to 7 min plus short greedy requests |
| 4 | Failed-edit-8 screen (EXP-044's design), adapter against the unchanged tree | about 0.8 | ladder smoke-8 |
| 5 | Dev-48 paired arm, only if stage 4 passes | 4-7 | ladder dev-48 |
| | **To a screen read (stages 0-4)** | **about 1.5-2.3** | |
| | **To a dev-48 read (stages 0-5)** | **about 5.5-9.3** | |

**Open feasibility points, each a stop before stage 2 if it fails:**

1. **Which weights to train against.** The served model is the QAT `w4a16` compressed-tensors checkpoint. Training needs either a BF16 E4B among the public Kaggle models (not checked) or the compressed checkpoint decompressed to BF16 in the kernel. An adapter trained on weights other than the served ones can still transfer [I], but the stage 3 eval must run on the served checkpoint under vLLM.
2. **The training stack.** `transformers` and `peft` with Gemma 4 support must be importable in the kernel. The wheelhouse carries what the harness needs, not necessarily `peft`. A training kernel without the competition attached may use internet for installs (no competition data is mounted), but that has not been checked.
3. **Memory.** The E4B's BF16 weights are about 8B stored parameters with the per-layer embeddings [I]. That is about 16 GB on one 24 GB L4 before activations, so it needs gradient checkpointing and short sequences, or the model split across the 4 GPUs.

## 4. Adapter size [I: hidden 2,560, head dim 256, MLP 10,240 assumed; layers 42, 8 heads, 2 KV heads are [V] from EXP-006, `.claude/skills/harness-stack/reference/small-variants.md:16`]

Parameters per layer and module are r x (in + out), stored in BF16 at 2 bytes. Per layer, in + out sums:

- 9,216 for `q_proj` + `o_proj`;
- 15,360 for all four attention projections;
- 53,760 for all seven linear projections.

| Targets | r = 8 | r = 16 | r = 32 |
|---|---|---|---|
| `q_proj`, `o_proj` | 6.2 MB | 12.4 MB | 24.8 MB |
| attention (`q`, `k`, `v`, `o`) | 10.3 MB | 20.6 MB | 41.3 MB |
| all linear (attention + MLP) | 36.1 MB | 72.2 MB | 144.5 MB |

All are far under the 3 GiB limit and `MAX_LORA_RANK` 128. The server rounds the rank up to a vLLM bucket (1, 8, 16, 32, ...; `server.py:58-67` [V]). EXP-047 records the real per-layer shapes and replaces these figures.

**The serving cost is not the file size.** It is:

- the KV cache lost to LoRA slots (EXP-047 reading B; the 31B lost 46,048 to 7,600 tokens at loose settings [M]);
- the decode slowdown (EXP-047 records tok/s; 755677 reports 29% per task on the 31B [M]).

The E4B's spare is the binding resource (D-006: about 225 s mean per task). A 10 to 30% slower decode could take most of it [I]. A decode slowdown is a stop even if the adapter works.

## 5. The risk outside edits (C-013)

**What C-013 is.** C-013's -10.8 points (28.3% against 39.1% on 46 tasks) is a third party's 31B adapter trained on whole task trajectories [M, kg-rank3-apache]. It is not ours, and not narrow. EXP-047 does not say whether that adapter was even applied.

**Why the risk is larger here.** The EXP-046 desk check killed the role team. There is therefore no editor sub-agent to carry the adapter alone, so the adapter would serve every turn of the single loop: reads, searches, test runs, the final patch. A narrow loss does not keep the weights narrow: a LoRA trained only on edit calls can still shift the following, all [I]:

- tool choice;
- call length;
- how often the model stops.

**Mitigations, all priced inside stages 2 and 3:**

1. A small rank (8) on attention only, or `q_proj`/`o_proj` only.
2. Loss on the call tokens only. A share of pairs whose target is a non-edit call (a file read, a search) copied from the base model's own greedy output, so the adapter is anchored to base behaviour there.
3. A **drift probe before any agent run**: on held-out public windows and own-words prompts, compare base against adapter on:
   - the tool chosen;
   - the next-token logprobs (as in EXP-047);
   - the call length.

   A drift gate is pre-registered before stage 3 runs.
4. Per-agent `adapter:` exists in the schema, but with no team the whole loop carries it. That leaves only the stage 4 screen (applied-edit share, empty-patch rate, wall) to catch behaviour change before dev-48.

## 6. Gate and what this licenses

Nothing is built. Stage 2 may be asked for only if all of the following hold:

- EXP-047 reads A3 or A4, and B2 or B3;
- the canary's decode tok/s with an adapter is within the E4B's spare at the single loop's call counts (to be computed from EXP-047's numbers and EXP-038's per-task decode);
- the three feasibility points in section 3 are cleared on paper.

On A5, A1, A1f or B1 the line stops here. C-024 is then blocked by infrastructure, not refuted.

## Status

2026-11-05: desk note. Zero GPU. No pre-registered readings, because nothing is run; a training kernel would get its own EXP file with endpoints and readings before any push.

2026-11-08: **GATE PASSED** (section "Gate check, 2026-11-08" below): EXP-047 v2 read A3 / B3, the decode check fits the spare, and the three feasibility points are cleared (point 1 [V]; point 2 by design, without `peft`; point 3 on paper, measured in the kernel). Stages 1 to 3 go to EXP-054 with their own readings. Sections 1 to 6 are unchanged.

---

## Gate check, 2026-11-08 (user decision 2026-11-08, df193f3; sections 1 to 6 unchanged)

### G1. EXP-047 readings

EXP-047 v2 read **A3 (applied) / B3**: `experiments/EXP-047-q4-adapter-canary-e4b.md` section 10. The first condition of section 6 holds.

### G2. Decode check

**Command:** `python -I -X utf8 experiments/EXP-048/gate_check.py runs/EXP-047-q4-canary-v2 experiments/EXP-038/e4b/summary.jsonl <scratch dir>`. All figures below are its printout.

**Inputs:**
- the EXP-047 v2 `kind == "decode"` probes: base 116.63 tok/s (n = 2, boot 0 and its repeat); with an adapter loaded 86.96 tok/s (n = 3, boot 1). The drop is **25.4%**, so seconds per token scale by 1.3412;
- the 48 EXP-038 rows (single loop, 8 min cap): mean wall 85.7 s, max 207.3 s, mean output tokens 5,970, max 15,402, mean calls 8.9;
- D-006's mean budget of 311 s per task, so the unchanged tree's spare is **225.3 s** per task.

| Model of the slowdown | Mean wall per task | Added | Share of the spare | Max task (cap 480 s) | Tasks over the cap | E7-style projection (mean x 120 / 3600 + 445.6 s) |
|---|---|---|---|---|---|---|
| unchanged tree | 85.7 s | 0 | 0 | 207.3 s | 0 | 2.98 h |
| decode component (output tokens x the per-token increase) | 103.2 s | +17.5 s (max +45.1 s) | 7.8% | 251.4 s | 0 | 3.56 h |
| whole-wall bound (every second x 1.3412) | 115.0 s | +29.2 s | 13.0% | 278.0 s | 0 | 3.96 h |

**Reading:** both models fit inside the spare, with no task over the cap and a projection far under 10.5 h. **The decode condition of section 6 holds.**

**Caveats:**
- The probes are single-stream 256-token decodes. Prefill with an adapter was not measured, and the whole-wall bound is the stand-in for it [I].
- n = 2 and n = 3 probes; the per-task figures are a model, not a run.

**Tooling pitfall.** `tools/estimate_budget.py --results` with its default decode model (25.5 tok/s, 0.6 s per call) overstates the E4B, so this check uses the E7 formula. Recorded in the harness-stack skill.

### G3. The three feasibility points of section 3

**Point 1, which weights: CLEARED [V].**
- `kaggle models get google/gemma-4` (2026-11-08) lists two public BF16 E4B instances under the `transformers` framework, both Apache 2.0:
  - `gemma-4-e4b-it-qat-q4_0-unquantized` v2, 15,914,702,139 bytes;
  - `gemma-4-e4b-it` v1, 16,024,808,340 bytes.
- `model_sources` takes them as `google/gemma-4/transformers/<instance>/<version>`.
- The decompress path exists in the image:
  - transformers 5.13.1 `quantizers/quantizer_compressed_tensors.py:74-78` decompresses when `run_compressed=False`;
  - `:96-97` marks the decompressed model trainable;
  - `compressed_tensors` `model_compressor.py:156-175` decompresses in place.
- **Plan:** train on the served checkpoint decompressed to BF16. The public QAT-unquantized instance is attached as the fallback. Which weights trained is a recorded field.
- Whether a fake-quant forward stays on the decompressed modules is [I]. The eval runs on the served checkpoint under vLLM in either case.

**Point 2, training stack: CLEARED BY DESIGN, without `peft`.**
- What is there:
  - the wheelhouse carries transformers 5.13.1 with `models/gemma4/modeling_gemma4.py` [V];
  - the image carries torch 2.10.0+cu128 [V, EXP-047 v2 `env.json`].
- What is not: `peft` is not in the wheelhouse [V].
- **Plan:** a hand-written torch LoRA on `q_proj`/`o_proj` that writes the same PEFT file layout as the EXP-047 canary writer. vLLM loaded and applied that layout (A3 [V]).
- **Internet is not tested.** The kernel saw 4 GPUs only with the competition attached (EXP-047 v1 section 9.4 against v2 section 10), so internet installs are not needed. Whether a kernel without the competition may install from the internet stays [I].

**Point 3, memory: CLEARED ON PAPER, measured in the kernel.**
- **Weights:** about 15.9 GB BF16 (the CLI sizes above) against about 22.5 GB usable on one L4.
- **Adapter:** rank 8 on `q_proj`/`o_proj` is about 6 MB (section 4).
- **Activations [I]:** gradient checkpointing, batch 1, and loss only at the call positions (hidden states sliced before `lm_head`, so the 262,144-wide logits exist only for those tokens).
- **In-kernel check:** EXP-054 stage 0 measures `torch.cuda.max_memory_allocated` over one forward and backward. If that fails, the kernel writes an infrastructure row.

**Gate: PASSED.** Stage 2 is pre-registered as EXP-054 (stages 1 to 3, one kernel, zero tasks).
