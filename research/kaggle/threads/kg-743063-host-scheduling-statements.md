---
id: kg-743063-host-scheduling-statements
topic_id: 743063
title: Host statements on task scheduling, concurrency, models per run and the 12 h limit (topics 743063, 743964, 744258, 745805, 746008, 748287, 749597)
author: Ryan Holbrook (host)
author_role: host
credibility: high
topics: [rules, budget, multi-agent, grading]
first_seen: 2026-11-05
last_checked: 2026-11-05
---

## Summary
Host replies, read in full on 2026-11-05 with `kaggle competitions topics show <id> --format json`. All [V] (host account). Dates are post times in UTC.

## Claims made (quoted numbers)
- 743063, 2026-09-24 19:48, to "task concurrency, eval_config keys, and the 12 h limit": "1. Sequentially. 2. The scorer reads those, and only those, four fields. The default is no limit. 3. Currently, hitting the 12-hour limit will error, but I'm planning on a fix that will score unfinished tasks as 0. You may want to set `max_time_minutes` to something moderate as a failsafe."
- 743964, 2026-09-28 10:32: "12h overrun: Not yet. Budget per task using `eval_config.yaml`. Parallel: I we don't support parallel calls. ... There's also a total submission limit of 3GB. ... Training on gemma-4-31b itself is fine."
- 744258, 2026-09-29 14:04: "There are ~120 tasks in the test set, or about 60 in each of the public and private splits. They are scored during the same 12-hour run."
- 745805, 2026-10-07 15:57: "I'm reconsidering this request [unfinished tasks as 0]. The trouble is that we run both the public and the private tasks in the same 12 hour evaluation, and it's not clear to me yet how to assign 0 to unanswered tasks in a way that's fair and consistent." Also: "I'm working on support for other models. We will retain the restriction to one model type per submission however (no main 31b agent and 12b subagent, for instance). Memory management on the L4x4s is too complex trying to support multiple models per run." And: "Both public and private tasks are evaluated during the same 12 hour run." And "Information like this makes it too easy to extract information about the test set through probing." (answer to a request, text of the question not visible in this reply).
- 746008, 2026-10-07 14:45: "We opted for the full evaluation during submission time here because of the complexity of the tasks and the increased risk of submission errors. ... if your submission succeeds at all (you get a public LB score), you know that it succeeded on the private split too."
- 748287, 2026-10-11 (topic body): "We don't support mixing variants within a submission, however. Every agent and subagent in your submission must use the same variant (though they can attach different LoRA adapters.) ... More test time compute: Inference is faster and memory burden lower so you can execute more and longer reasoning turns and iteration cycles. You could also experiment with using ParallelAgent for concurrent LLM calls (though tool calls are still executed sequentially)."
- 748287, 2026-10-11 16:23, answering a report that ParallelAgent fails on the competition's ADK v1.36 (user degen, GitHub issue google/adk-python 7324): "Ah, okay, good catch. I think it's too risky to attempt a migration to ADK v2 at this point, but good to know." Another user (2026-10-14): "ParallelAgent with tool calls is relatively important". Another (2026-10-13): "there are workarounds (ex - keeping sub-agents tool-free)" [M].
- 748287, 2026-10-11 16:25: smaller variants: "Yes, everything is the same." (same 4xL4, same 12 h limit, same per-task budgets).
- 749597, 2026-10-15 15:04: "Naively setting unfinished tasks to 0 could lead to inconsistent results on the public and private leaderboards. I will try to think of other ways we could allow teams to better utilize the 12 hours, though."

## Possible claims for us
- Tasks run one at a time inside the 12 h (V, 2026-09-24). Concurrency inside a task is the only parallelism available. [I]
- The two host statements on parallel LLM calls disagree in time: 2026-09-28 "we don't support parallel calls" vs 2026-10-11 ParallelAgent "for concurrent LLM calls (though tool calls are still executed sequentially)". The later one is the topic body; but the same thread reports ParallelAgent with tool calls broken on ADK v1.36 and the host declined to migrate. Whether a ParallelAgent of tool-free sub-agents works on the scorer is unverified by us. [I]
- Mixed models are excluded by host rule; every sub-agent uses the same 31B. [V]
- Unanswered by the host in any thread read: whether the scorer's vLLM uses tensor_parallel_size 4 with one server (asked by tammamalasha 2026-10-11, no reply), max_num_seqs, and whether the harness issues more than one request at a time. [unknown]

## Files
None.

## Updates
- 2026-11-05: first read. Related staff line (Ashley Oldacre, 742807, 2026-09-29): "As long as you are using those models in accordance with their model license terms, and the output you're using to submit to that competition doesn't 'conflict with the license requirement of the rules of this competition, you may use them."
