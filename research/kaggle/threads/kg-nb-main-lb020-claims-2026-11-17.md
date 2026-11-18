---
id: kg-nb-main-lb020-claims-2026-11-17
topic_id: none (public notebooks; no topic)
title: Public notebooks with a claimed LB of 0.20 or more, pulled 2026-11-17 (four qualifying, two checked and not qualifying)
author: owners ccuuuuy, flexonafft, evgendvorkin, crsuthikshnkumar; hanifnoerrofiq, spiritofvishwakarma (not qualifying)
author_role: participant (no staff)
credibility: file text read as data [V]; scores are the authors' claims [M]; board rows [V, CSV 11-17]
topics: [configs, notebooks, bundles, noise]
first_seen: 2026-11-17
last_checked: 2026-11-17
---

## Summary
Four public notebooks since 11-07 claim a public LB of 0.20 or more, and their owners' rows on the 11-17 leaderboard CSV show 0.20 or 0.22. Their configs share caps (temperature 0.2, 240 s timeout, 8 to 10 minutes, 28 or 40 tool calls, 80 turns, thinking 2048 to 4096). Two more public notebooks were pulled and checked; neither claims a score. Each download was read with `nb_read.py` and not run.

## Claims made (quoted; authors' text)
- ccuuuuy/lb-0-22-4-config-files-no-training, title "LB 0.22 | 4 config files, no training"; markdown "# G4 Sub BF Public", "Writes the bundle (digest `c9829b6ac709`) into `submission.zip`." The owner's CSV row reads 0.20. The notebook names no other author or source.
- flexonafft/gemma-4-budget-aware-coding-agent-lean-conte, header "Efficient Navigation 0.22 + Thinking 2048 + 10 Minutes"; text "public leaderboard 0.17"; "thinking 256 scored 0.10, thinking 1024 about 0.16 and the original thinking 4096 bundle 0.22". Owner row (Igor Zharov) reads 0.22.
- evgendvorkin/can-gemma-4-become-a-software-engineer, "our best observed Public LB 0.20" (V40 to V41 Hybrid; "the exact scored Hybrid ZIP is not independently recovered"); "Variant E ... Our November 17 Public LB returned 0.17". Owner row reads 0.20.
- crsuthikshnkumar/gemma4-testgraph-ai-code-comp-crsk, "Best reported baseline: TestGraph-AI v4 = 0.20"; "Experimental target: public leaderboard score > 0.24. A higher score is not guaranteed." Owner row reads 0.20.
- Not qualifying: hanifnoerrofiq/patchsmith-gemma-4-developer-agent (owner row 0.20, rank 518); spiritofvishwakarma/gemma4-agent1 (owner row 0.18, rank 1038). Neither notebook claims a score.

## Board rows (CSV 2026-11-17, bound to owner by TeamMemberUserNames, [V])
| owner | CSV team name | score | rank | uploads | last submission (UTC) |
|---|---|---|---|---|---|
| flexonafft | Igor Zharov | 0.22 | 29 | 39 | 2026-11-16 10:38:36 |
| ccuuuuy | cc uuuuy | 0.20 | 580 | 15 | 2026-11-17 01:11:00 |
| evgendvorkin | Дворкин Евгений Владимирович | 0.20 | 593 | 22 | 2026-11-16 19:57:49 |
| crsuthikshnkumar | C R Suthikshn Kumar | 0.20 | 625 | 14 | 2026-11-16 15:46:48 |
| hanifnoerrofiq | Hanif Noer Rofiq | 0.20 | 518 | 15 | 2026-11-16 04:00:45 |
| spiritofvishwakarma | Aditya Vishwakarma | 0.18 | 1038 | 36 | 2026-11-16 13:38:54 |

Leaderboard snapshot: `untrusted/lb-2026-11-17/gemma-4-developer-agent.zip`, SHA-256 `74b839aa32f35294c220c9d4395ccfc549857caca5cdd79edbf1d0ef4cce02d7`, member SHA-256 `73b932b27b92c2be569d348c74cf0c50092a5d580d3cae1fc78ba74238216db9`.

## Files (SHA-256 per file, `sha_file.py`; kernel metadata is the Kaggle API record)
| slug | file | bytes | SHA-256 | lastRunTime (kernel list) |
|---|---|---|---|---|
| ccuuuuy/lb-0-22-4-config-files-no-training | lb-0-22-4-config-files-no-training.ipynb | 6,526 | bb6fe201d845eadc6ba1c5370b3b6030ddf243ceaf515785f64613f8555c314b | 2026-11-17 01:10:22 |
| ccuuuuy | kernel-metadata.json | 659 | 79e44e8060ba293e92270ba8e46763f5772a04d0ec5fc9e0319af062da0291fd | |
| flexonafft/gemma-4-budget-aware-coding-agent-lean-conte | gemma-4-budget-aware-coding-agent-lean-conte.ipynb | 13,751 | a4178839d5f62230e0fd2cb37bf9a465ff907fd9c13e2b8d34adaf1b61aef878 | 2026-11-17 09:44:00 |
| flexonafft | kernel-metadata.json | 692 | f7dcacba8140a5237d694b1881bdd748065f530aba3592aadf603b560cadb823 | |
| evgendvorkin/can-gemma-4-become-a-software-engineer | can-gemma-4-become-a-software-engineer.ipynb | 34,241 | 7e3c79d2b66e7d8d5c947711c8beb80e626160b471534f8e84ba8613fccbf507 | 2026-11-17 21:11:53 |
| evgendvorkin | kernel-metadata.json | 857 | e54f2fb1e9b4617eb7736277760c343349823f2d9f02dbdfde83452c8ad1fa66 | |
| crsuthikshnkumar/gemma4-testgraph-ai-code-comp-crsk | gemma4-testgraph-ai-code-comp-crsk.ipynb | 109,151 | dbc6acf01d76a8201bb8142dec7427c123765d8f93bade87a3b8f58534777aed | 2026-11-17 16:07:41 |
| crsuthikshnkumar | kernel-metadata.json | 674 | 89739d0fdc2f5a6577f8b766545107ae59a94eb53fcc69e88c0b20681391d19c | |
| hanifnoerrofiq/patchsmith-gemma-4-developer-agent (not qualifying) | patchsmith-gemma-4-developer-agent.ipynb | 11,091 | 6ceb34eda72903798ae93b1ef48df90213a8c7461db4b8faee3f9727853f4581 | |
| hanifnoerrofiq | kernel-metadata.json | 674 | 2f8a20f5ba407fda888c1e686542516ab285ac0e18b2eedcb5d96a192681ae62 | |
| spiritofvishwakarma/gemma4-agent1 (not qualifying) | gemma4-agent1.ipynb | 28,787 | 505220f131f65ddbfb9fe7d5a0d0f61c745b82c576b7b3fe249f15fdadd69f4f | |
| spiritofvishwakarma | kernel-metadata.json | 753 | 00d3bdf122a7152025c202d94fc8d2469551917863b128c32b3c9a060c509a43 | |

Kernel metadata gives slug, title, flags and sources only; no version number and no author display name are in it. Competition source for all six: `gemma-4-developer-agent`; enable_internet false for ccuuuuy.

## Config read from the files (data, not run)
- Shared: temperature 0.2, top_p 0.95 (ccuuuuy, flexonafft, evgendvorkin). crsk uses 0.1 and 0.9 in a fallback block and 0.2 and 0.95 later.
- thinking_budget 4096 (ccuuuuy, evgendvorkin, crsk); 2048 (flexonafft lean). timeout_seconds 240 throughout. max_tool_calls 28 (ccuuuuy, flexonafft, crsk) or 40 (evgendvorkin Variant C). max_time_minutes 8 (ccuuuuy, evgendvorkin, crsk) or 10 (flexonafft). max_turns 80.
- Prompt shape: flexonafft is a single agent whose prompt requires an edit by call 12. crsk also writes `sub_agents/code_analyzer.yaml` (timeout 150, max_turns 70) and offers code-graph tools. crsk's header names `MODEL = gemma-4-12b-it-qat-w4a16-ct`; the harness scores the 31B only, so that line is not the scored model [I].
- Not compared with the rank-3 config note in this run.

## Possible claims for us
- [I] The public band for these configs is 0.20 to 0.22 on the board. Our 0.18 best sits in the same band, so a fresh copy of a public config is a reasonable 0.20 target. No row above 0.22 is a config we can name.
- [I] The scores are one-draw claims by their owners. Expect 0.13 to 0.20 spread on identical files (see 757588 and 759514).

## Updates
- 2026-11-17: first read. Qualifying count: four (ccuuuuy, flexonafft, evgendvorkin, crsuthikshnkumar). Earlier draft had a wrong author credit for ccuuuuy and display names not bound to the owners; corrected here.
