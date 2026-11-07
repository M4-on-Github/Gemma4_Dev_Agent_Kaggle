---
id: kg-digest-2026-11-07-small-model-board
date: 2026-11-07
since: 2026-11-03
items: 4
headline: "The host's small-model board is stale: its stored output says 'Last Updated: 2026-10-20 19:27 UTC' and lists 24 teams, top 0.06 (NullPointers, GZ_F, Bart Agent); a participant asked on 2026-11-06 for daily updates and the host has not replied. Topic 751104 has no host post after 2026-10-20, and no host text defines what counts as an E2B/E4B submission (model in agent.yaml, sub-agents, adapters)."
---

Reading tools: `research/kaggle/nb_outputs.py` (new; prints notebook cells and stored outputs), `research/kaggle/sha_file.py`, all as `python -I -X utf8`. Kaggle reads by CLI: `kaggle kernels pull -m`, `kaggle competitions topics show ... --format json`, `kaggle competitions topics list ... -v`, `kaggle datasets list --user`, `kaggle kernels list --user`. Zero GPU; nothing posted. Tags: [V] official or CLI-verified, [M] participant or unverified, [I] our inference.

Blocked: `kaggle kernels output` is not on the Bash allow-list, so the stored `leaderboard.csv` output was not downloaded. The table below comes from the notebook's own stored cell output, which is the same table the notebook prints.

## 1. The host small-model notebook (the board)

- Kernel `ryanholbrook/gemma-4-developer-agent-small-model-leaderboard`, pulled with `-m` into `untrusted/ryanholbrook-small-model-board-2026-11-07/`. [V]
  - Notebook `gemma-4-developer-agent-small-model-leaderboard.ipynb`, 6,232 bytes, SHA-256 `f2feb34cb3c9d50ad3683524a5ce10a80098b7f617ebb108d96236ca785af917` (same bytes as the 11-03 copy). [V]
  - `kernel-metadata.json`, 733 bytes, SHA-256 `4670979d911af87b88fd1f6e3f2b4f70579f672ea584f9837b4ec2fe9e7684dd`. id_no 139881074; enable_internet false; competition_sources gemma-4-developer-agent. [V]
  - Last run: lastRunTime 2026-11-02 23:54 (from our 11-03 note; not re-read today). [V, earlier read]
- Stored output, cell 1: "Last Updated: 2026-10-20 19:27 UTC", read from `/kaggle/input/notebooks/ryanholbrook/gemma-4-small-model-data/last_updated.txt`. [V] So the run of 11-02 read an input that was last written on 10-20. [I]
- Stored output, cell 2 (`pd.read_csv` of `leaderboard.csv`, `head(100)`): 24 rows, not 100. The markdown says "top 100 teams" and "the full leaderboard.csv file in the output data". [V]

Top 10 (PublicScore, two decimals):

| Rank | Team | PublicScore |
|---|---|---|
| 1 | NullPointers | 0.06 |
| 2 | GZ_F | 0.06 |
| 3 | Bart Agent | 0.06 |
| 4 | Luxshan Thavarasa | 0.05 |
| 5 | Sebastian Brestin | 0.05 |
| 6 | kuto | 0.05 |
| 7 | XuHorace | 0.05 |
| 8 | Christian Czura | 0.03 |
| 9 | Hoai Vo | 0.03 |
| 10 | prince22466 | 0.03 |

- Score needed: rank 1 = 0.06; rank 3 = 0.06 (tied with ranks 1 and 2); rank 10 = 0.03. [V for the stored table; the scores are rounded to two decimals, so ties and sub-0.01 gaps are not visible.]
- Teams listed: 24 (ranks 1 to 24; last score 0.00, Luv Bhargava). [V]
- `gemma-4-small-model-data` is not in the public datasets list of `ryanholbrook` (`kaggle datasets list --user ryanholbrook`, 20 items shown). The notebook reads it as a notebook source path, not a dataset slug. Version date from its own file: 2026-10-20 19:27 UTC. [V for the listing; the date is the printed stamp]. Its contents were not read.

## 2. Topic 751104 (the bonus) after 2026-10-20

- Topic 751104, Elan Markowitz, posted 2026-10-20 19:12:03 UTC; 8 comments, 36 votes (CLI, 2026-11-07). [V]
- No host (staff) comment after 2026-10-20. The comments after it are participant only:
  - 2026-10-21 ZHYLAR (7 votes): asks whether the prize can be a separate competition so the two final slots stay for the main track. [M]
  - 2026-10-25 Aditya Vishwakarma: the harness readme lists `gemma4-27b-it`, `gemma4-27b` and the E2B/E4B aliases, asks for correction to @elanlearns. No host reply. [M]
  - 2026-10-28 erich_prompt_perfect and 2026-10-22 roll0ver, RISHAV KUMAR: short replies. [M]
  - 2026-11-06 amunozo: "Could you update the leaderboard's notebook daily?" [M]
  - 2026-11-07 Mikhail (vote -1): a long reply about local Gemma 4 context and AST gating, with a link to a public repo and notebook. Not about eligibility. [M]
- What makes a submission count as E2B/E4B: the post's stated rule is "utilizing Gemma E2B or Gemma E4B" (quoted in `threads/kg-751104-small-model-prize.md`, 2026-10-20) and "the best submission whose base model is Gemma E2B or E4B" (our 11-03 paraphrase). No host text in 751104 addresses the model in `agent.yaml`, sub-agent models or adapters. [V for the gap; I for the reading that the rule is silent]
- Context from topic 748287 (2026-10-11, host Ryan Holbrook, 38 comments): asked whether small variants are scored under the same conditions as 31B, the host replied "Yes, everything is the same." [V] Also "The scorer has this update already." on the 12B `--hf-overrides` config. [V] This is before the 10-20 post and is not a rule about eligibility.

## 3. Topic list since 2026-11-03: small-model posts

- Scan: page 1 of the current listing (2026-11-04 to 2026-11-07) and the page-2 listing read earlier in this session (2026-11-02 to 2026-11-03). Titles only, per the dispatch. [V]
- Small-model titles in the window: 756433 "Public code: configs, trajectories and analysis scripts for a Gemma 4 E2B agent failure study" (2026-11-06 08:38, 0 comments, 2 votes). No host reply. [V]
- Other window posts with no small-model title: 756792 (hand-constructed LoRA adapters, 11-07), 756693 (team merger score, 11-07), 756622 (getting started, 11-06), 756607, 756587, 756461, 756438, 756400, 756336 (11-06), 755677 (LoRA zero score, 11-04), and 755542 and 755554 (11-03). [V]
- No host post in the window on small-model eligibility or the board. [V]

## 4. Items not read

- The stored `leaderboard.csv` (kernel output): blocked by the guard.
- The full `ryanholbrook/gemma-4-small-model-data` source: not a public dataset; not opened.
- Topic 751104 opening post body: not returned by the CLI; the quoted rule is from our 11-03 read.

## Suggested claims (for the lead to decide; not our status to set)

- The host's public small-model board was last written on 2026-10-20 and showed 0.06 at the top with 24 teams [V]; a participant asked for daily updates on 2026-11-06 [M]. So the board is not a current measure of the small-model track. [I]
- The bonus rule is "utilizing Gemma E2B or E4B" plus the two-selected-submissions condition [V]. Whether a 31B main model with E2B/E4B sub-agents or adapters counts is not stated. [I]
- The 12B and E4B variants are scored under the same conditions as the 31B [V, 748287, 2026-10-11 host reply].
