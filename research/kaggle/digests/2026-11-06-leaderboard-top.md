---
id: kg-digest-2026-11-06-leaderboard-top
date: 2026-11-06
since: 2026-11-05
items: 9
headline: "Nothing new from the top: Yurnero (0.29, 18 uploads, last 2026-10-29) has published nothing, and the only host statement on selection is that a bonus counts 'one of the team's two selected final submissions' (topic 751104, 2026-10-20); the main-track ranking rule is not stated. Six of the nine 0.24 teams uploaded on 2026-11-05 or 11-06; the rank-3 team (23 uploads) is the only 0.24 team with a public bundle we can name (v24 config). A public notebook and a participant report both say a byte-identical archive scored differently on two runs (0.13 vs 0.17; 0.00 vs 0.17) [M]."
---

Reading tools: `research/kaggle/lb_delta.py` and the new `research/kaggle/lb_names.py` (name lookup on the leaderboard zip), `research/kaggle/nb_read.py` for the notebook, `research/kaggle/sha_file.py`, all as `python -I -X utf8`. Kaggle reads by CLI: `kaggle competitions leaderboard`, `kaggle competitions topics list -c gemma-4-developer-agent -p 2 -v`, `kaggle competitions topics show gemma-4-developer-agent <id> --format json`, `kaggle kernels pull -m`, `kaggle kernels list --user <name> -v`, `kaggle datasets list --user <name> -v`. Zero GPU; nothing posted. Tags: [V] official or CLI-verified data, [M] participant or unverified text, [I] our inference.

## Items: new this run and already noted

1. **11-06 leaderboard CSV** (new; `untrusted/lb-2026-11-06/`). Delta against 11-05. Section 2. [V]
2. **Yurnero, rank 1** (already noted in `threads/kg-752848-yurnero-rank1.md`; no new publication). Two new [M] comments in other threads (754295, 755677). Section 1. [V/M]
3. **Nine teams at 0.24 and their upload counts** (new). Section 2. [V]
4. **Rank-3 team's public release** (already noted in `threads/kg-rank3-apache-release.md`; new CLI check of its kernels and datasets). Section 2. [V]
5. **Host selection rule** (already noted in `threads/kg-751104-small-model-prize.md` and `kg-743063-host-scheduling-statements.md`; re-confirmed). Section 3a. [V]
6. **Topic 754295, "Will private leaderboard evaluation use multiple runs?"** (new; `threads/kg-754295-private-lb-multiple-runs.md`). Section 3a. [M]
7. **Same-bytes notebook victorzhong0110/same-bytes-two-scores** (new; `threads/kg-nb-victorzhong0110-same-bytes.md`; file in `untrusted/`). Section 3b. [M]
8. **Topic 743683, 2026-11-06 participant reports** (new note `threads/kg-743683-host-rerun-thread.md`; the host lines are from 2026-09-28). Section 3b. [V host, M participants]
9. **Public-kernel and public-dataset check of the top teams** (new; section 2 table). No Gemma-config kernel found for any team except the rank-3 team's paper-track writeup. [V]

New-vs-noted: the 754295, 743683 (11-06 reports), victorzhong0110 notebook and the 11-06 CSV are new. Already noted and re-checked: 752848, 751104, 749597, the rank-3 release.

## Leaderboard snapshot used

- New: `untrusted/lb-2026-11-06/gemma-4-developer-agent.zip`, member `gemma-4-developer-agent-publicleaderboard-2026-11-06T16:25:06.csv`, 4,928 rows, 152,276 bytes, zip SHA-256 `555a818c0c213e363fe89cb231441e636784ec6f1b99c48f83bdb897403451bf`. [V]
- Old (for the delta): `untrusted/lb-2026-11-05/gemma-4-developer-agent.zip`, member `...2026-11-05T10:50:33.csv`, 4,762 rows, 147,130 bytes, SHA-256 `189a25dd3b0f0d1f337142a4497f6a0612728905ea4e12201d4d431ae0ce873c`. [V]
- The CSV's `SubmissionCount` and `LastSubmissionDate` are the fields used for upload counts. Whether `SubmissionCount` includes failed or errored uploads is not stated in the file. [I]

## 1. Yurnero (the 0.29 team)

- Rank 1, Score 0.29, 18 submissions, last 2026-10-29 08:07:28. Team member username on the row: `samson8`. [V] Unchanged from the 11-05 snapshot.
- No notebook, dataset, discussion or writeup from this team was found. Public kernels and datasets under `samson8` are older and unrelated: `samson8/how-to-create-wikipedia-embeddings` (lastRunTime 2023-09-07) and two Wikipedia-embedding or `all_teams5` datasets (2023 and 2025). [V, CLI]
- Topic 752848 has no new post after 2026-10-26. [V, CLI read]
- Public comments in the window, both [M] and unverified as the same account (the display name matches the rank-1 team):
  - 2026-11-02 07:08 (topic 754295, comment 3548455): "Kaggle has never done that and highly likely never will." About averaging multiple runs for the private score.
  - 2026-11-04 10:30 (topic 755677, the LoRA zero-score thread): "It is possible to score > 0 with a LoRA adapter". No detail.
- Model setting, prompt, caps, sub-agents, adapter and upload count: not published by them. The only number visible is the 18 uploads above. [V]

## 2. The 0.24 cluster: what they submit and how many uploads

Nine teams sit at 0.24, ranks 2 to 10. Upload counts from the CSV (11-06 snapshot; 11-05 snapshot in brackets):

| rank | team | username (member) | score | uploads | last submission (UTC) |
|---|---|---|---|---|---|
| 2 | Yike Xu | weiyun22021, yoruet, yunmeng6 | 0.24 | 7 (7) | 2026-10-08 06:07:23 |
| 3 | MUHAMMED IDRIS BIN YACOOB | muhammedidris28 | 0.24 | 23 (21) | 2026-11-06 04:03:45 |
| 4 | SAVE | chenshengabc | 0.24 | 26 (25) | 2026-11-05 12:04:39 |
| 5 | chizhu | chizhu2018 | 0.24 | 9 (8) | 2026-11-05 15:28:19 |
| 6 | pluris | pluris | 0.24 | 2 (2) | 2026-10-28 10:19:33 |
| 7 | Alberth Moreira | alberthmoreira | 0.24 | 22 (22) | 2026-10-31 21:16:49 |
| 8 | tammam alasha | tammamalasha | 0.24 | 38 (36) | 2026-11-06 00:03:59 |
| 9 | Pınar Aksoy | xpinara | 0.24 | 19 (17) | 2026-11-06 00:04:31 |
| 10 | Takumu Hata | takumuhata | 0.24 | 26 (25) | 2026-11-05 08:59:45 |

- Six of the nine were dated 2026-11-05 or 2026-11-06: SAVE, chizhu and Takumu Hata (11-05); MUHAMMED IDRIS BIN YACOOB, tammam alasha and Pınar Aksoy (11-06). The lead's count of "five" is corrected to six. [V]
- Between the two snapshots the uploads grew by 0 to 2 for each team. [V, difference of the two CSVs; the old snapshot is about 30 h earlier]
- Public-kernel and public-dataset check, per username (CLI, 2026-11-06):
  - Rank-3 team `muhammedidris28`: 3 kernels, "Git History as a Gym: reproduce every number" (lastRunTime 2026-10-20), "Gold-patch census of the public tasks" (2026-10-15), "Where to Edit? Reproduce every number" (2026-10-15). 3 datasets: `gemma4-agent-runs` (223,281 bytes, updated 2026-10-20, 2,620 downloads), `git-history-gym` ("366 Verified Coding Tasks", 563,578,898 bytes), `locbench-129` ("LocBench-129 Issue Localization Labels", 63,364 bytes, 2026-10-16). [V] None is titled with the v24 config; the bundles are inside `gemma4-agent-runs`. The `locbench-129` title is a candidate source for the "129" task figure in topic 756400; not checked. [I]
  - `samson8` (Yurnero): see section 1. [V]
  - `chenshengabc` (SAVE): 8 kernels and 6 datasets, 2019 to 2021, plus three ARC3 kernels (2026-09-29, 0 votes). No Gemma-titled item. [V]
  - `chizhu2018` (chizhu): 4 kernels (2018 to 2019) and 14 datasets (2019 to 2025). No Gemma-titled item. [V]
  - `takumuhata` (Takumu Hata): 14 kernels titled `casmi26-codex-*` (2026-07 to 2026-11-03) and 18 datasets, mostly `casmi26-*`, plus `swe-pallets-x` and `rdkit-wheel`. The "casmi26" series is not identified as this competition; no Gemma-titled item. [V list; relevance [I]]
  - `pluris`, `alberthmoreira`, `tammamalasha`, `xpinara`, `weiyun22021`, `yoruet`, `yunmeng6`: no public kernels ("Not found") and no public datasets ("No datasets found") under those usernames. [V, CLI] This does not cover private work or accounts under other names.
- Lineage that is public: honghanhhh's kernel "Gemma 4 Baseline | LB 0.24" is the byte-port source for the victorzhong0110 pack, and is v6 of flexonafft's "gemma-4-budget-aware-coding-agent-v2" [M, per the victorzhong notebook]. Its title says 0.24; the board row for `Hanh Tran` (honghanhhh) is 0.18, rank 465, 7 uploads, last 2026-10-23 [V]. The flexonafft row (`Igor Zharov`) is 0.22, rank 25, 30 uploads, last 2026-11-02 [V].
- Which bundle the rank-3 team uploads is not stated publicly. [I]

Score bands, 11-06 CSV (10-28 figures from the victorzhong notebook in brackets, [M]): 0.24: 9 (5); 0.22: 67 (48); 0.20: 352 (214); 0.18: 796 (562); 0.17: 893 (678). [V] Teams at or above 0.20: 429 of 4,928. [V]

## 3. Selection and variance

### 3a. How the final ranking selects submissions

- [V] Topic 751104 (2026-10-20, Elan Markowitz): the $10,000 small-model bonus is open only to "one of the team's two selected final submissions". The rule is written for the bonus. The main-track selection rule is not stated in anything we read. [I]
- [V, per `threads/kg-743063-host-scheduling-statements.md`] Topic 749597 (2026-10-15): "Naively setting unfinished tasks to 0 could lead to inconsistent results on the public and private leaderboards." Not a selection rule.
- [V] Topic 743683 (2026-09-28, host): "I'm going to pause the rescore until we can resolve the queueing for the L4x4 machines"; "Your notebook needs to generate a submission file (submission.zip) before that submission can be scored." Queueing and file requirements only.
- Topic 754295 (2026-10-30, Haoran Zhang): "Will private leaderboard evaluation use multiple runs to reduce variance?" 3 comments, 12 votes. The opening body was not returned by the CLI. No host reply. The only answer is Yurnero's [M] "Kaggle has never done that". Heisenberg [M] says "60 right" for the final task count, which conflicts with the 58 public tasks in the brief and the 129 figure in topic 756400.
- Answer to "is the hidden score a separate run": not stated by the host in anything we read. The victorzhong notebook quotes a host error text that says the hidden dataset "can be larger/smaller/different than the public dataset" [M, quoted by a participant]. [I] The host has said public and private results can differ (749597). [V]

### 3b. Variance from re-uploading the same zip

- [M] victorzhong0110 notebook "Same Bytes, Two Scores" (kernel `victorzhong0110/same-bytes-two-scores`, note `threads/kg-nb-victorzhong0110-same-bytes.md`): submissions 57629857 (2026-10-25, 0.13) and 57667013 (2026-10-26, 0.17), both claimed to be sha256 `205a677f...6186`. The author says both kernel outputs were downloaded and hashed; we did not verify. Their measured "rerun noise" is 0.04. The same notebook has 57598496 at 0.15 and 57516570 as a crashed rerun. Verifiable part: the notebook file's own SHA-256 is `a176bd47566c898a75f35725166c96c76bfde0d824ab645ceafb1836253b6afe`.
- [M] Topic 743683 participant report, 2026-11-06 (Veronika Yaitskikh; note `threads/kg-743683-host-rerun-thread.md`): submission 58049571 scored 0.00 after about 5 hours, byte-identical to 58012317, which scored 0.17 on 11-05. Our CSV row for her team: 0.18, rank 799, 19 uploads, last 2026-11-06 07:10:06. [V on the row; the 0.00 is her report]
- Ours (coordinator's data, not read by us here): three draws of one zip at 0.17, 0.18 and 0.12. The CSV row for `RainM4` shows Score 0.18 (the team's best, [I]), rank 1147, 13 uploads, last 2026-11-05 23:34:14. [V on the row]
- Plan §5.5: the public-LB MDE is about 4 tasks (about 0.07). A spread of 0.04 (0.13 vs 0.17) is inside that band. The 0.00 vs 0.17 report is a single participant's account, not a measured noise level. [I]

## 4. Items that were not read in this run

- Topic 754295 opening post body (not returned by the CLI).
- 11-06 topics 756461 (gold patches fail), 756438 (time allocations), 756433 (public code E2B failure study), 756336 (swegemma ADK), 756044 (stuck pending), 756051 (tool-call serialization): not read. They are for the next digest if the lead wants them.
- Topic 747519 ("Update on Kaggle Error Submissions & Queue Delays", 101 comments): already in a note; not re-read here.
- Rank-3 dataset README (`muhammedidris28/gemma4-agent-runs`, 1,859 bytes): not read in this run.
- Kernel source of the rank-3 team's three kernels: not pulled.
- victorzhong kernel saved outputs: not downloaded.
- The full 743683 thread: only the lines in the note were read; Mr. Mrinmoy Choudhury's "stuck at Notebook Running" is a single line.

## 5. Suggested claims (for the lead to decide; not our status to set)

- A single upload is a draw, not a measurement: one participant reports the same archive at 0.13 and 0.17 [M], and our own three draws are 0.17, 0.18, 0.12 [coordinator data]. Use with the plan §5.5 MDE.
- The 0.24 cluster is nine teams with 2 to 38 uploads each, six of them dated 11-05/11-06 [V, CSV]. Of the nine, only the rank-3 team has a public Gemma-related release (dataset and kernels). [V] The other eight show no public Gemma-config kernel or dataset under their usernames. [V, CLI, with the caveat above]
- The host's only written selection rule is "two selected final submissions" for the small-model bonus (751104, 2026-10-20) [V]. The main-track rule is not stated. [I]
- Upload count does not track score in this snapshot: the 0.29 team has 18 uploads, the rank-3 0.24 team has 23 [V]. [I] on what that means.
