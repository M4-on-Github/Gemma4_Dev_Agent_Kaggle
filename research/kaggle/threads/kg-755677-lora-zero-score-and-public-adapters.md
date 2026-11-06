---
id: kg-755677-lora-zero-score-and-public-adapters
topic_id: 755677 (cross-ref 755611, 743213)
title: Scoring zero when using LoRA adapters (Luca Massaron, 2026-11-04) and the public adapter artifacts read this run
author: Luca Massaron (opener); Yurnero, Heisenberg, Ankith Savio, Kapil Chopra, kingofeverything, Harisdak Singh Banwait, xz (replies)
author_role: participants; no host reply
credibility: OP numbers and replies [M]; no host statement; artifacts read as data only, none run
topics: [adapters, lora, scoring, timeout]
first_seen: 2026-11-05
last_checked: 2026-11-05
---

## Summary
The opener reports adapter submissions scoring 0.00 against 0.18 without an adapter ([M], OP's own numbers, taken from the topic read on 2026-11-05; the topic JSON carries replies only). The replies disagree: one says a score above 0 with an adapter is possible, one says a timed-out submission scores 0, one reports a non-zero rank-32 score at a 4-minute cap (no number), and one team reports an adapter run that completed with "no score" and a later run with the same adapter at 0.17 (the no-adapter baseline). No reply is from the host. No public notebook or released bundle read in this run shows an adapter changing model output under the harness.

## Replies (participant text)
- Yurnero, 2026-11-04 10:30: "I think something is wrong with either your setup or with your submission stucture. It is possible to score > 0 with a LoRA adapter." [M] The display name matches the rank-1 team (`kg-752848-yurnero-rank1`); this is not verified as the same account.
- Heisenberg, 2026-11-04 10:50: "I think you also get 0 if your submission timed out." [M]
- Ankith Savio, 2026-11-04 11:41: "I got a non zero score with rank 32 lora for the same model with 4 minute task timeout." No score given. [M]
- Harisdak Singh Banwait, 2026-11-04 18:41: "I believe something is wrong with submission structure". [M]
- kingofeverything, 2026-11-04 23:26: asks why the tensor is 509 MB. [M]
- Kapil Chopra, 2026-11-04 23:57 [M, measured by his team; the table is his]. Same base model; adapter "rank 16, alpha 32, all 7 projections on all 60 language layers, served as main_lora". Runs:
  - A: run1, alpha 16, 8 min / 4096 tokens: "complete, no score".
  - B: run2, alpha 32, 8 min / 4096: "complete, no score".
  - C: run2, alpha 32 (same adapter as B), 6 min / 2048: 0.17, "same as our no-adapter baseline".
  - Also says on a Kaggle 4xL4 test run the adapter was listed and served, each task took about 29% longer (about 45% more tokens per step); 120 tasks at an 8-minute cap went over the 12-hour total; cutting the task cap and the thinking budget fixed it.
  - His reading: "So the adapter does load and score on the grader." His only scored run is C, which equals the baseline (0.17). That is not evidence of an effect on output. He suggests rerunning the 0.00 submission at 5-6 min with thinking 2048 and checking loading if it stays 0.00.
- xz, 2026-11-04 12:51 (also topic 755611, 0 comments): asks whether the claim that LoRA reduces decoding speed and context is true; "I can't even test these claims easily with submissions being 30+ hours."
- Host: no reply in 755677 as of 2026-11-05.

## Related host statements (see also kg-743508, kg-744331)
- Host last statement on adapters (2026-09-30, 743508): "It should be fixed in the most recent wheelhouse version". Host 2026-09-30, 744331: "I will patch to set the loras parameters based on the submission." No host statement on 755677 or 745364.

## Public artifacts read this run (untrusted/, data only, not executed)
Searched with `kaggle datasets list -s "gemma-4 lora adapter"` and `kaggle kernels list --competition gemma-4-developer-agent --sort-by dateRun`. Downloads are into new `untrusted/<slug>-2026-11-05/` directories. Hashes below are of the files as downloaded.

1. `scottweeden/gemma-4-developer-agent-tool-lora-kit` (Apache-2.0; lastUpdated 2026-11-04 23:52:48; 775 downloads; 1 vote; usability 1.0).
   - Zip: `untrusted/scottweeden-tool-lora-kit-zip-2026-11-05/gemma-4-developer-agent-tool-lora-kit.zip`, 393,668 bytes, SHA-256 `7935ba070d8895de3577476cbd71320d09ef98beaae147c75b204ad9937c29e7`.
   - Extracted copy: `untrusted/scottweeden-tool-lora-kit-2026-11-05/`. Its `README.md` (5,786 bytes) SHA-256 `b7323bc9622c201f253f3f98f976127659d7a9f5cb63dc298fc997b6d9d396f6`.
   - Contains no adapter weights (the zip is 384 KB). Files include bundles/, plora/ (PLORA-RESULTS.md, benchmarks/plora_bench_kaggle_l4x4.json), evidence/ (a1_harness_runs.json, rebuild_*.json) and history/SUBMISSIONS.md.
   - NOT READ this run: the README was denied by the auto-mode classifier (two attempts), so the kit's claims, evidence/ and plora/ results are unverified. Recorded as not read.
2. `verracodeguacas/gemma-4-31b-agent-lora-r16` (license "other"; lastUpdated 2026-10-24 16:03:32; 87 downloads; usability 0.5).
   - Files on the dataset: README.md 2,996 bytes; adapter_config.json 423 bytes; adapter_model.safetensors 489,840,784 bytes (NOT downloaded; header not read).
   - Downloaded: `untrusted/verracodeguacas-31b-agent-lora-r16-2026-11-05/adapter_config.json`, SHA-256 `3973549c06f885d38c0f63bd32f17fc34f4536b3d05841ffc08291cbaaaa8d4d`; `README.md`, SHA-256 `2b8d568048b0984d6bf433a722db17486395db748c56c2bd616559c4f6920c1d` (NOT read: the read was denied by the classifier).
   - Config (read as data with `research/kaggle/adapter_cfg.py`): PEFT LORA, CAUSAL_LM, base `google/gemma-4-31b-it-qat-w4a16-ct`, r=16, lora_alpha=32.0, lora_dropout 0.0, use_dora false, use_rslora false, target_modules q/k/v/o/gate/up/down, no layers_to_transform (all layers). The shape matches Kapil Chopra's adapter in 755677; not confirmed to be the same file.
   - Demonstrated output change: none in what we could read (no outputs in the dataset metadata, README unread).
3. `boristown/gemma-4-e2b-lora-fine-tuning-swe-agent-baseline` (kernel; lastRunTime 2026-11-04 03:16:33; 45 votes).
   - Pulled with `kaggle kernels pull -m` into `untrusted/boristown-e2b-lora-baseline-2026-11-05/`. Notebook `gemma-4-e2b-lora-fine-tuning-swe-agent-baseline.ipynb`, 118,912 bytes, SHA-256 `8e75cffc182221d5dcf447fc3833e6fd1c048e5ee114a520fdc9fcc6a3fa304c`; `kernel-metadata.json`, 1,102 bytes, SHA-256 `0bbc939295345fe7eff56751210e386f3402478607a569470918a779240c754d`.
   - Scanned as data with `research/kaggle/nb_lora_scan.py`: 15 cells, no saved outputs in any cell. Describes an in-house int4 LoRA (r=8, alpha=8) and a packaging/audit flow. No score, eval number or harness output is shown. Cell 1 names the E4B checkpoint while the competition checkpoint is the 31B.
   - Demonstrated output change: none.
4. Not downloaded: the other LoRA datasets from the search (fieldbridge, lisper, edulens, microlens, linguaforge, clover, ntl-ts, multi-LoRA hot-swap kit, dmitriigluzdov serving kit 655 MB). They are for E2B/E4B or other models, or are kits without evidence we could check; not opened.

## Sample tool-call adapter (organisers' sample, read as data)
- Root agent `agent.yaml` line 3: `adapter: main_lora`. Sub-agent `sub_agents/code_analyzer.yaml` line 4: `adapter: tool_lora` (its tools: read_file, search_similar_code, get_code_neighbors, get_code_subgraph).
- Held copy `data/raw/sample_submission/adapters/main_lora/adapter_config.json` (664 bytes, SHA-256 `75a46da2db7f3c70442e5c728f64059aff52cf64174cee7aeb3a4ec37f6e78fb`). Our `data/raw` copy has no `tool_lora` folder and no `adapter_model.safetensors`.
- Staged copies under `runs/EXP-028-armR/phase0/sample_submission/adapters/` (our run, not checked against the organiser's zip):
  - `main_lora` and `tool_lora` configs are byte-identical (SHA-256 `75a46da2...`): PEFT LORA, base `google/gemma-4-31b-it-qat-w4a16-ct`, r=4, lora_alpha=8, lora_dropout 0, target_modules [q_proj, o_proj], layers_to_transform [0], rank_pattern {}, alpha_pattern {}.
  - `main_lora` and `tool_lora` `adapter_model.safetensors` are byte-identical: SHA-256 `dcbedd989af34f5201a39606e0bd4014d351a29162dd96da418782cbbe487ad9`, 217,672 bytes, 4 tensors, all BF16 (lora_A.weight [4, 8192] x2, lora_B.weight [5376, 4] x2), layer 0 only, q_proj and o_proj.
  - Header read with `research/kaggle/adapter_cfg.py`; tensor values not read.
- Read: the sample's "tool-call" adapter is the analyzer sub-agent's adapter, and in our staged copy it is identical in config and weights to `main_lora`. No separate tool-call-specific training is visible in the sample.

## Files
- Listed above under "Public artifacts read this run". All paths are under `untrusted/` (gitignored). No artifact was executed or imported.
