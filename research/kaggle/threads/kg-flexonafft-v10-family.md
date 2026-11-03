---
id: kg-flexonafft-v10-family
topic_id: flexonafft/gemma-4-budget-aware-coding-agent-v2 (v10) and its public forks honghanhhh/gemma-4-baseline-lb-0-24 and kawh1111/g4-baseline-024, plus dennis6886/best-score-reproduction-artifacts-oct2026 (dataset)
title: The 8-min / 28-call public config family: one file set, several public scores
author: flexonafft (Igor Zharov on LB); forks by Hanh Tran (honghanhhh), kawh1111; archive by dennis6886
author_role: top-lb
credibility: medium
topics: [budget, prompt, noise, selection]
first_seen: 2026-11-03
last_checked: 2026-11-03
---

## Summary
Three public notebooks and one dataset carry the same `agent.yaml`, `configs/sampling.yaml` and `eval_config.yaml` (identical SHA-256 across all three). They differ only in the prompt (6,985 B in the two notebooks; 6,323 B in the dataset). The file set has been scored at 0.12 to 0.24 by different accounts. A single LlmAgent loop, no `sub_agents`. Read as text with `python -I -X utf8`-style inspection of the `.ipynb` JSON; nothing executed.

## Claims made (quoted numbers)
- [M] honghanhhh notebook (title "Gemma 4 Baseline | LB 0.24", lastRunTime 2026-10-23): markdown says base is `flexonafft/gemma-4-budget-aware-coding-agent-v2` (public 0.22); "8 min, 28 calls, 240 s, 8192 output tokens, temperature 0.2, thinking on"; "v5 lowered those limits and scored 0.13".
- [V, LB CSV 2026-11-03] honghanhhh's LB row is Hanh Tran, rank 394, score 0.18, 7 submissions, last 2026-10-23. The notebook title's 0.24 is not on the account's LB row. Credibility of the 0.24 title: low until reconciled.
- [V, LB CSV] Igor Zharov (flexonafft), rank 24, 0.22, 30 submissions, last 2026-11-02. [V, LB CSV] DVS (davis0178), rank 23, 0.22, 14 submissions.
- [M] kawh1111 fork (lastRunTime 2026-11-03 13:47, title "G4 v2 edit9" in list; pulled copy is "g4-baseline-024"): "Config bytes unchanged"; v6 prompt edits, "v5 lowered those limits and scored 0.13".
- [M] dennis6886 dataset (2026-10-27, CC BY 4.0, 11,432,812 bytes): folder `gemma-best/` is the same config; provenance.json says "official_public_score": 0.18, "source badge 0.22", "source_version": 10. Note: the dataset also holds unrelated tabular CSVs from other competitions (not used).
- [V, LB CSV] Dennis6886 team row: rank 334, 0.20, 9 submissions (best of the account, so a different upload).

## Possible claims for us
- The same bytes scored 0.18 (dennis6886's own upload, per provenance) and 0.22 (the source badge). That is the noise the MDE memo predicts; it is not an effect. [I]
- The graph-tool names (`get_code_neighbors`, `search_similar_code`, `get_code_subgraph`) appear in the honghanhhh and kawh1111 agent.yaml. Our tree bans them. Not portable as-is. [I]

## Files
- untrusted/honghanhhh-gemma-4-baseline-lb-0-24/gemma-4-baseline-lb-0-24.ipynb, 10,245 B, SHA-256 17cb26fcc95ce9b587b7a7bf98a0321882c4f4deb0cfa7a02445a05740b5f60f. Licence: not stated in the notebook text read.
- untrusted/kawh1111-g4-baseline-024/g4-baseline-024.ipynb, 10,379 B, SHA-256 e8cfe09359ee1c2aa3042d959ed185749af354103183860409bc3fb3d4b89124. Fork; attribution line to honghanhhh.
- untrusted/dennis6886-best-score-reproduction-artifacts-oct2026/best-score-reproduction-artifacts-oct2026.zip, 11,432,812 B, SHA-256 69caf2d495f3e05ffe05d1b3d30d83d958af42cef4597d416ac65f51656336dc, CC BY 4.0 (kaggle datasets download). Zip members checked for absolute paths, `..` and drive letters: none. Used: gemma-best/ only.
- Embedded file-set hashes (decoded from the notebooks): agent.yaml 314 B sha 68079929…; configs/sampling.yaml 119 B sha 571a934e…; eval_config.yaml 94 B sha 916cf6cb34a6cc3d…; prompts/system.md 6,985 B sha 37dbbed1… (honghanhhh and kawh1111); dennis6886 system.md 6,323 B sha 7f8dde62….
- Config values (all three): timeout_seconds 240; max_tool_calls 28; max_time_minutes 8; max_turns 80. sampling: temperature 0.2, top_p 0.95, max_output_tokens 8192, thinking_budget 4096, include_thoughts true. Tools listed: run_command, read_file, edit_file, write_file, get_status, submit_patch, get_code_neighbors, search_similar_code, get_code_subgraph (9). No `max_llm_calls` key.

## Updates
- 2026-11-03: honghanhhh and kawh1111 read; dennis6886 zip downloaded and hashed. LB rows checked against the 2026-11-03 CSV.
