---
id: kg-leoprovorov-budget-fit-and-anytime
topic_id: leoprovorov/score-to-gemma-4 and leoprovorov/single-agent-anytime-patch
title: Budget-Fit Single Agent (lineage: verracodeguacas) and its "never empty diff" fork
author: AlekseiProvorov (leoprovorov)
author_role: top-lb
credibility: medium
topics: [budget, prompt, edit-reliability, noise, selection]
first_seen: 2026-11-03
last_checked: 2026-11-03
---

## Summary
A single LlmAgent on the official starter prompt with an 8-min / 28-call budget. The account is at LB 0.20 (rank 290, 9 submissions, last 2026-11-01). The notebook states the file set is reproduced by "ten scored draws" (census by Dariush Afshar, read 2026-10-22: mean 0.166, lowest 0.13, highest 0.18). The fork (2026-11-03) changes only `prompts/system.md`, adding a never-empty-diff rule. It cites a public task-level dataset (Gluzdov) for the failure split.

## Claims made (quoted numbers)
- [M] score-to-gemma-4 (Budget-Fit): "In 129 local runs, only about half of the fixes Gemma eventually finds are in the file after 4 minutes"; "Runs with no source edit by call 12 fail 87% of the time"; "a scored run with these caps finished in under 12 hours"; "Scores on the 58-task public leaderboard move by about ±2 tasks between identical submissions".
- [M] Census (cited by the notebook, not verified by us): ten scored draws of the Budget-Fit file set, mean 0.166, lowest 0.13, highest 0.18. "the 0.22 of a neighbouring bundle is the best of eight draws of those files, which averaged 0.156."
- [M] Anytime-patch (2026-11-03) cites Dmitrii Gluzdov's dataset (692 local runs, 8 configs on 114 public tasks, one A100, seed 42): 194 of 692 (28%) runs ended without any patch; 75 context overflows, "every one of them had an empty patch"; 52 session timeouts with no edit; 53 stopped without editing. Thinking-on v4: 39 of 80 (49%) resolved; runs that reached at most 14 calls 37 of 71 (52%); 15-20 calls 2 of 43 (5%). Public tasks no configuration solved: 64 of 114.
- [V, LB CSV] AlekseiProvorov rank 290, 0.20, 9 submissions.
- [M] Anytime-patch author's own draw: no score stated in the notebook.

## Possible claims for us
- Patchless runs are the largest single loss in the cited dataset (28%); overflow runs were all patchless. Supports an edit-early, never-empty-diff prompt rule. Medium: credibility rests on a dataset we have not downloaded.
- Calls beyond ~14 with no edit resolve rarely (5% vs 52%). Correlational, prompt-era data; not a causal claim.

## Files
- untrusted/leoprovorov-score-to-gemma-4/score-to-gemma-4.ipynb, 11,176 B, SHA-256 7aaa02a953219fe91055c02c66be807ea85f05934007d607c4f5ddd75552f003. Embedded file set: agent.yaml 314 B; configs/sampling.yaml 119 B; eval_config.yaml 94 B; prompts/system.md 4,683 B (sha of the decoded file not computed). Tools: 9 incl. graph tools. Licence: notebook says Apache 2.0 for the lineage (verracodeguacas) only in the fork's text.
- untrusted/leoprovorov-single-agent-anytime-patch/single-agent-anytime-patch.ipynb, 23,722 B, SHA-256 9689224fbc5ac465f9c425944ec264d65e520ab574c007625da8ec939610db8c. Prompt-only change; config byte-identical to parent (asserts in cell 2: timeout 240, calls 28, minutes 8, turns 80; thinking 4096, include_thoughts true).
- Config (both): name swe_agent, single agent, no sub_agents; temperature 0.2; top_p 0.95; max_output_tokens 8192; thinking_budget 4096; eval timeout 240 s, max_tool_calls 28, max_time_minutes 8, max_turns 80. No `max_llm_calls` key.

## Updates
- 2026-11-03: both notebooks read; embedded file sets decoded and checked for config keys.
