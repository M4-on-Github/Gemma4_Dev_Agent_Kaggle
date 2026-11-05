---
id: kg-752848-yurnero-rank1
topic_id: 752848
title: Why does nobody have a score of over 0.24? (and every other public post by Yurnero / samson8)
author: Yurnero (account samson8, LB team "Yurnero")
author_role: top-lb
credibility: medium
topics: [selection, noise, multi-agent, budget]
first_seen: 2026-11-05
last_checked: 2026-11-05
---

## Summary
Rank 1 (0.29 = 17/58, 18 entries, last entry 2026-10-29 08:07 UTC, unchanged on 2026-11-05) has published no notebook, dataset, model or method statement. Everything public from the account is forum opinion. No sentence in it states a cap, call budget, prompt length, thinking budget, agent class, tool set or number of re-uploads. Identity: LB row `TeamMemberUserNames = samson8` [V]; the kernel `samson8/how-to-create-wikipedia-embeddings` shows author name "Yurnero" [V].

## Claims made (quoted numbers)
All [M] (forum text, author's own words), source topic in brackets.
- 2026-10-05, 746008: "Simple answer: thats just how Kaggle competitions with fixed data are being hosted. You cant guarantee that your selected submission wont time out / errored out on a new data." Hints at awareness that the private half can time out. No config given.
- 2026-10-18, 750521: "It is not trivial to make LLM inference deterministic, fixing a seed won't help." A participant (RISHAV KUMAR, 2026-10-18 23:05) asked "@samson8 were you able to achieve 0.24 on leaderboard after finetuning or just optmizing the prompts, skills and subagents." No answer by the account in the thread as read. [I] The account already held 0.24 by 2026-10-18 (inferred from the question, not from the LB).
- 2026-10-26 17:51, 752848: "The winner solved 9 out of 120 problems. Now we have 14 out of 58 and we are not even near the end. I think 0.31 is pretty reachable". 0.31 is 18/58. 14/58 was then the public top (0.24).
- 2026-10-26 17:55, 752848: "Gold patches are not working for all public tasks, but all private gold patches are correct, since hosts have properly verified them." Unverified, but consistent with the host's staff line that the public split has environment artifacts (see kg-751487 style EDA).
- 2026-10-30 08:25, 752848 (Anh Tuan Nguyen): "The guy above got 0.29, what method do you think he used?" So 0.29 was on the board by 2026-10-30 08:25 UTC; the 2026-10-28 digest top was 0.24.
- 2026-10-31 07:11, 752848 (Nir Aberman) asked the account directly: "whether your jump past 0.24 came from shrinking that find-to-commit gap, and if so, whether it was config/tooling rather than prompt wording?" Nir's own data: gold file opened by call 2-3 in about 84% of 163 runs; first edit about 106 s in solved vs about 183 s in failed runs. No reply from Yurnero in the thread on 2026-11-05.
- 2026-11-02 07:08, 754295: "Kaggle has never done that and highly likely never will. I think making your solution stable is one of the intended challenges". A follow-up (Ankith Savio, 2026-11-02 09:38) asked "do you get your score reliably or does it fluctuate a lot?"; no answer seen.

## Possible claims for us
- Nothing here supports a method claim. The "stable solution" remark is the only hint and it is generic.
- Best-of-N arithmetic (research/kaggle/binom_tail.py, binomial over 58 tasks, an upper bound on per-draw spread because tasks are not homogeneous):
  true rate 9/58: P(>=17 in one draw) 0.6%, best of 18 draws 9.8%; 10/58: 1.6%, 25%; 11/58: 3.8%, 50%; 12/58: 7.6%, 76%.
  The 2026-11-03 census of ten draws of one config (range 0.13-0.18) suggests a smaller spread than binomial, which makes a 17 from a 10-11 true rate less likely than these figures. [I]
- The entry pattern does not contradict repeated uploads of one config but does not show it either: 18 entries; at 1 per UTC day that fits any time span of 18+ days; the 0.24 existed by 10-18, 0.29 by 10-30, last entry 10-29. [I] Because the LB keeps only the best score and shows the last-entry time, the date of the 0.29 entry is unknown.
- What would contradict a pure lucky draw: a true rate of 14-15/58 (0.24-0.26) plus one favourable draw also gives 17. Both readings predict the same row. The only separating evidence is a second 0.29 or a stated config.

## Files
Public artifacts of the account: kernel `samson8/how-to-create-wikipedia-embeddings` (2023-09-07, 106 votes), datasets `samson8/all-mp-net-base-v2-embedings` (2023, 33.7 GB) and `samson8/all-teams5` (2025-03-20, 126 MB). `kaggle kernels list --user Yurnero` returned "Not found". None relates to Gemma; none downloaded.

## Updates
- 2026-11-05: LB CSV 2026-11-05T10:50:33 shows rank 1 unchanged (0.29, 18 entries, last 2026-10-29 08:07:28). Full discussion text of 752848, 750521, 754295, 746008 read.
