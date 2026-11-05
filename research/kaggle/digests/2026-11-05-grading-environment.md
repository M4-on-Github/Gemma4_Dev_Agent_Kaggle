---
id: kg-digest-2026-11-05-grading-environment
date: 2026-11-05
since: 2026-11-03
track: main (gemma-4-developer-agent)
items: 6
headline: No update seen or announced to the grader's public wheelhouse or harness since our 2026-10-14 record; the only same-version repack was 2026-10-12; the scorer's private test-package pool and image are not visible, and no host has answered any missing-package thread.
author: kaggle-scout (Claude Haiku 5.5), grading-environment question, asked by the lead
---

# Digest 2026-11-05: grading environment (packages, harness, re-score)

## Answer first

**No update seen or announced.** Measured against our 2026-10-14 record (`experiments/README.md` §1b), the public wheelhouse dataset and the five harness package versions are unchanged. The dataset page still says last updated 2026-10-12 19:51:31 UTC, and no host post or notebook mentions a package change after that.

Two caveats keep this from being a clean "no":

- **Same-version repack, 2026-10-12.** A participant reports swegemma 0.2.11 was repackaged under the same version number at 12 Oct 19:51 UTC, with 5 `.py` files different from the 9 Oct build (topic 748323, 2026-10-14 comment). A version string cannot show this, and our §1b record has no checksum. So we cannot say which 0.2.11 build our notes describe.
- **Cannot tell** for the scorer's private per-task test-dependency pool (the one that would hold `inline_snapshot` / `dirty_equals`), the scorer's Docker image contents, and whether the 12 Oct build is the one the scorer runs. Competition data files were not checkable (see below).

**Leaderboard.** Top five: Yurnero 0.29; Yike Xu 0.24; MUHAMMED IDRIS BIN YACOOB 0.24; SAVE 0.24; chizhu 0.24. We are rank 1132 of 4,794 at 0.18 (12 submissions, last 2026-11-04 03:51:09 UTC). 407 teams are at 0.20 or above.

## Evidence per item

### 1. Wheelhouse dataset `metric/gemma-4-developer-agent-wheelhouse` [V, CLI]
- Read through `kaggle datasets files` (read-only). lastUpdated 2026-10-12 19:51:31. The CLI shows no version number, so the "v31" label used by a participant (752490) cannot be checked against it.
- 41 wheel files, read across 3 pages. Harness wheels present: swegemma 0.2.11, adk_submission 0.2.13, adk_eval_core 0.1.0, google_adk 1.36.1, vllm 0.19.1 (creationDate 2026-10-12 19:51).
- Absent: `inline_snapshot`, `dirty_equals`, `pytest-httpbin` / `pytest_httpbin`, `httpbin`, and any `pytest` wheel.
- This digest records the counts and the absences, not the full 41-name list. Re-run `kaggle datasets files metric/gemma-4-developer-agent-wheelhouse` to get it.
- Result: **no change seen** since 2026-10-14.

### 2. Harness (swegemma / ADK packages): current vs the recorded version
| Package | Now (wheel names, 2026-11-05) | Our record (§1b, 2026-10-14) | Result |
|---|---|---|---|
| swegemma | 0.2.11 | 0.2.11 (the plan once said 0.2.7) | no change seen |
| adk_submission | 0.2.13 | 0.2.13 | no change seen |
| adk_eval_core | 0.1.0 | 0.1.0 | no change seen |
| google_adk | 1.36.1 | 1.36.1 | no change seen |
| vllm | 0.19.1 | 0.19.1 | no change seen |

- Same-version repack: swegemma 0.2.11 on 12 Oct 19:51 UTC, 5 `.py` files different from the 9 Oct build, the comment naming "budget, cli, config, context..." [M, participant 748323, comment 2026-10-14 05:56:58 UTC]. The wheel creation time matches the dataset date.
- The 9 Oct build removed `swegemma/models/discovery.py` and `models/registry.py` [M, 748323]. The current starter already imports `adk_submission.discovery` (see item 5).
- 748323 is a participant's replay (314 calls, 70 public tasks); the build table is in `research/kaggle/threads/kg-748323-harness-build-history.md`.

### 3. Competition data files and rules/data pages mentioning the grader
- **Blocked.** `kaggle competitions files` is not on this agent's Bash allow-list (`guard_bash.py`). I did not route around the block. Competition files, the `wheels/` directory and the data-page text were not checked.
- Local `data/raw/HARNESS_README.md` exists and was not read in this job.

### 4. Discussions on missing modules, test deps, wheelhouse, sandbox, grader, re-score, rebuilds
Only one host reply in any of these threads was found.

- **Host, Ryan Holbrook, topic 751339 (opened 2026-10-21 by Sultan Fawad, 19 votes, 44 comments), 2026-10-22 13:45:08 UTC [V]:** "This looks like a failure on our side. We're investigating the root cause and will rerun any submissions that failed on account of it. Our apologies for the incident." Scope: "Notebook Threw Exception" / "unhandled error" incidents. It says nothing about packages. Thread note: `kg-751339-notebook-threw-exception-host-reply.md`.
- Re-score status: no host confirmation of reruns. Participants report otherwise: Ayush Thakur, 10-24, "is this fixed on your end?"; Jason Krijgsman, 10-28, a 22 Oct submission "still shows COMPLETE with no score" six days after the promise; Sungjoon Park, 10-29, a config-only bundle "Succeeded with score 0.00, no error". These are participant posts.
- **No host reply** was found on any package or test-dependency thread listed below.

Missing-package and grader threads (title, date, votes/comments, source):

| Topic | Date (UTC) | Title (short) | Votes / comments | Note |
|---|---|---|---|---|
| 744807 | 10-01 | Submission errors after the Sep 30 wheelhouse update | 21 / 22 | title and counts only from the topic list |
| 744370 | 09-29 | FastAPI tasks fail even with the gold patch, typing_inspection seems to be missing | 5 / 5 | title and counts only |
| 745249 | 10-02 | Missing python-multipart dependency in the FastAPI task environment | 0 / 0 | title only |
| 745775 | 10-04 | Missing FastAPI test dependencies in the evaluation sandbox | 8 / 8 | title and counts only |
| 745850 | 10-04 | inline_snapshot wheel missing for notebook environment but required by tasks | 0 / 1 | title only |
| 743973 | 09-28 | Gold patches fail offline for most FastAPI and requests tasks (missing test deps in grading env?) | 7 / 3 | title and counts only |
| 747248 | 10-08 | fastapi tasks can't pass even with the gold patch | 15 / 12 | title and counts only |
| 749439 | 10-14 | Reference patches failing in the starter notebook (4 of 12 pass: inline_snapshot x2, pytest-httpbin x2, system requests x2, httpx x1) | 1 / 0 | first lines of the body read |
| 750253 | 10-17 | [Observation] Pytest 8 incompatibility with legacy httpbin | - | title only |
| 750345 | 10-17 | Calibrating in a notebook? About a third of fastapi tasks cannot pass there | -1 / 1 | read; thread note written |
| 750509 | 10-18 | Scorer test environment: published image resolves 0/64 fastapi reference patches | 0 / 0 | read. Nir Aberman: "the published image resolves the reference patch on 0 of 64 fastapi tasks (dirty_equals / typing_inspection missing), while a fully pinned environment resolves 107/129" |
| 751487 | 10-21 | Local eval in a scorer-like sandbox: gold patches pass on 127/129 (was 52) | 14 / 5 | read; thread note written |
| 751707 | 10-22 | -p no:anyio and four other scorer conventions make about a quarter of real fixes unpassable | 0 / 2 | read; thread note written |
| 752490 | 10-25 | Scorer sandbox/runtime parity (author's private GPU diagnostic cites "starter v3", "wheelhouse v31") | 0 / 0 | first lines read. Participant label "v31" is not visible on the CLI |
| 752672 | 10-25 | Local notebook evaluation imports the installed package instead of the snapshot for some repos | 0 / 0 | first lines read |
| 753521 | 10-28 | Scorer's vLLM 0.19.1 drops Gemma 4 tool calls emitted before the thought channel closes (MRE) | -3 / 0 | first lines read |
| 754586 | 10-31 | Which public tasks cannot pass in the scorer's sandbox? Four questions about the grading image | -3 / 0 | first lines read. Asks about the pytest pin, Docker vs subprocess and network mode; cites requests_6589/6592/6629/6757/7328/7433/7502/7505 with "Network is unreachable", fastapi_14186, rich_3486, rich_3472. Asks; does not claim organizer data |
| 755554 | 11-03 | [fastapi_14186] Task unresolvable: required test skipped due to @needs_pydanticv1 and Pydantic v2 setup | 0 / 0 | read; thread note written |
| 755391 | 11-03 | Dataset inquiry on private libraries | - | title only; no answer found |

Key quoted lines (participant unless noted):
- 750345: "The organizers' task_soundness.csv shows the gold patches passing in the scoring environment". The file is not in our `data/raw/` and was not read. Unverified.
- 751707: "In 277 of 1,143 cases (24%), the reference fix fails verification only because of one of those conventions." Causes: -p no:anyio 79; pytest.ini overwrite 101; non-test files as targets 65; required test skipped on Linux 24; JUnit report over 10 MiB 8.
- 755554: "No single environment can run all required tests, so a skipped required test makes the task impossible to resolve with any patch."
- 751487 comment (Ahmed Awelkair, 10-22): "subprocess (local) uses python 3.12.13 and the Docker image's used python 3.13. Docker was the default though according to the HARNESS_README.md." Author's reply: "I don't know whether Kaggle submissions use Docker or subprocess". Unanswered by a host.

### 5. Public host notebooks: pins, wheelhouse, install cell
Both notebooks were pulled with `kaggle kernels pull` into new untrusted directories and read as data (`python -I -X utf8`, `nb_pins.py`). Neither was executed.

- **Starter** `ryanholbrook/getting-started-gemma-4-developer-agent`. SHA-256 `8e7d84a326acae509fb596163ba085831961b588b86d51af31e037c5319b917c`, 18,034 bytes.
  - Pins: kernelspec `python3`, language_info Python 3.12.13. No `kaggle` metadata block, so no docker image id and no `dataSources` in the file. The last-run time 2026-10-12 21:17 is from the kernel list earlier in this job.
  - Install cell 2: `[sys.executable, '-m', 'pip', 'install', '-q', '--no-deps', '--force-reinstall', *wheels]` from `/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse` (unversioned path). Restores `+cu128` wheel names into `/tmp/wheelhouse`. The dataset holds no `inline_snapshot`, `dirty_equals` or `pytest-httpbin` wheel, so the cell installs none of them.
  - Cell 8 imports `from adk_submission.discovery import discover_declared_models` (the 9 Oct build had moved this away from `swegemma.models.discovery`).
  - Cell 10: `sandbox='subprocess'`, `wheels_dir=DATA_DIR / 'wheels'`, `DATA_DIR = /kaggle/input/competitions/gemma-4-developer-agent`. Model path `/kaggle/input/models/google/gemma-4/other/{declared_model}/2`.
- **Small-model leaderboard** `ryanholbrook/gemma-4-developer-agent-small-model-leaderboard`. SHA-256 `f2feb34cb3c9d50ad3683524a5ce10a80098b7f617ebb108d96236ca785af917`, 6,232 bytes.
  - Metadata: language_info Python 3.13.15. Kaggle block `dockerImageVersionId` 28755, `dataSources` [], `isInternetEnabled` false, accelerator none.
  - No install cell and no harness import. Reads `ryanholbrook/gemma-4-small-model-data` (`last_updated.txt`, `leaderboard.csv`).
- **Pinned docker image sha:** none in either file. The only image pin visible is `dockerImageVersionId` 28755 in the small-model notebook.

### 6. Leaderboard
- Public leaderboard CSV from `kaggle competitions leaderboard`, saved 2026-11-05 (member name stamped 16:28:23 UTC), 4,794 rows. The zip contains the CSV only.
- Top five: Yurnero 0.29; Yike Xu 0.24; MUHAMMED IDRIS BIN YACOOB 0.24; SAVE 0.24; chizhu 0.24.
- Us: **rank 1132 of 4,794, 0.18**, 12 submissions, last 2026-11-04 03:51:09.
- 407 teams at 0.20 or above. One public task is 0.017 (58 tasks); the measured MDE is about 4 tasks.

## What is new, and what was already in `research/kaggle/threads/`
- **New threads written this job:** `kg-748323-harness-build-history.md`, `kg-751487-scorer-like-sandbox-gold-pass.md`, `kg-750345-fastapi-notebook-calibration.md`, `kg-751707-scorer-conventions-unpassable.md`, `kg-755554-fastapi-14186-unresolvable.md`, `kg-751339-notebook-threw-exception-host-reply.md`.
- **Already on file, cross-referenced:** `kg-743063-host-scheduling-statements.md` (host statements on the 12 h limit and parallel calls); `kg-747519-kaggle-error-queue.md` (staff queue statements). Neither is changed.
- **Earlier digests:** the 2026-10-28 and 2026-11-03 digests record no harness version change. The 2026-11-05 digest's headline was read; it does not cover package versions.
- **Our notes** (`research/kaggle/`, `knowledge/`), keyword pass for swegemma, wheelhouse, inline_snapshot, dirty_equals, httpbin, docker, rescore, environment update: 4 hits, all already known (the helper scripts themselves and `threads/kg-alexust-one-bundle-three-outcomes.md`, which quotes swegemma 0.2.11 as a local setup).

## What could not be checked
- Competition data files, `wheels/` directory listing, and rules/data pages (item 3): blocked by the Bash guard.
- The private per-task test-dependency pool (`gemma4swe-wheelhouses`, cited in 749439 and our README): not public, not checked.
- The scorer's Docker image contents and whether it matches the 12 Oct build.
- `task_soundness.csv` (cited by 750345 as an organizer file): not in `data/raw/`, not read. Claims built on it are unverified.
- Re-score outcome: no host confirmation of reruns as of this read.
- Topic pages 1 to 16 were scanned by title, votes and counts. Full text was read only for the threads marked "read" above.
- Our `version_grep.py` run over the whole repo is not clean: it reaches `.claude/worktrees` stale copies first. Re-run excluding `.claude` before relying on it.
- The author's FreshSWE-Py dataset, the two participant notebooks and wheels (751487, 751707), and the host notebooks' runs were not fetched or executed.

## Suggested claims
1. "No update seen or announced: the public wheelhouse (41 files, dataset dated 2026-10-12 19:51:31) and the five harness versions (swegemma 0.2.11, adk_submission 0.2.13, adk_eval_core 0.1.0, google_adk 1.36.1, vllm 0.19.1) match our 2026-10-14 record." [V, CLI listing]
2. "A same-version repack of swegemma 0.2.11 on 2026-10-12 changed 5 `.py` files, so the version string alone does not identify the grader build." [M, participant diff; cite 748323]
3. "inline_snapshot and dirty_equals are not in the public wheelhouse. Whether the scorer's private per-task pool has them is not visible to us." [V for the listing; I for the rest]
4. Cohort check: "fastapi_14186 and rich_3486 cannot pass under the required-test set derived by a participant (opposing skip markers). Candidates for exclusion from dev-48 headroom; check against our §1g before use." [M; 755554, 751487]
5. "A host said failed submissions would be rerun (2026-10-22); participants report outstanding failures through 2026-10-29; no host has confirmed completion." [V for the statement; outcome unverified]
6. Do not claim: "gold patches pass in the scorer" (750345's organizer file is unverified); "wheelhouse v31" (752490's label is not visible on the CLI).

## Reading tools and recorded hashes (all read as data)
- Leaderboard zip `untrusted/lb-2026-11-05-environment-scout/gemma-4-developer-agent.zip`, 148,061 bytes, SHA-256 `55ae96f80176626db0e891625cbe0bba7c7c2bf60cf224aa29fc9cfdecc9a267`, downloaded 2026-11-05. Member `gemma-4-developer-agent-publicleaderboard-2026-11-05T16:28:23.csv`, 334,409 bytes, SHA-256 `c52025c7a04fc78bd7ed5c40cd083b0405f2962d01b4d4bc2d6301fb70c2ffcc`. Correction: an earlier scratch note gave `55ae96f8…` as the CSV hash. That was the zip. The CSV hash is `c52025c7…`.
- Host starter `untrusted/ryanholbrook-getting-started-2026-11-05/getting-started-gemma-4-developer-agent.ipynb`, 18,034 bytes, SHA-256 `8e7d84a326acae509fb596163ba085831961b588b86d51af31e037c5319b917c`. Kernel `ryanholbrook/getting-started-gemma-4-developer-agent`, pulled 2026-11-05, kernel version not recorded by this job; last run 2026-10-12 21:17.
- Host small-model leaderboard `untrusted/ryanholbrook-small-model-leaderboard-2026-11-05/gemma-4-developer-agent-small-model-leaderboard.ipynb`, 6,232 bytes, SHA-256 `f2feb34cb3c9d50ad3683524a5ce10a80098b7f617ebb108d96236ca785af917`. Kernel `ryanholbrook/gemma-4-developer-agent-small-model-leaderboard`, pulled 2026-11-05, version not recorded.
- Dataset `metric/gemma-4-developer-agent-wheelhouse`: CLI listing only; version not shown by the CLI; lastUpdated 2026-10-12 19:51:31. No wheels downloaded.
- Helper scripts, all in `research/kaggle/`: `kg_grep.py` (keyword search over our notes, comma-separated terms), `lb_zip.py` (leaderboard zip members and hashes), `sha_file.py` (SHA-256 of files), `nb_pins.py` (notebook pins), `version_grep.py` (version lines in our notes; needs `.claude` excluded), `tx_find.py` and `tx_topic.py` (read saved tool results from our own transcript; data only).

## Answer summary (for the lead)
- Yes / no / cannot tell: **no update seen or announced** for the public wheelhouse or harness, both values as recorded; **cannot tell** for the private test pool and the scorer image.
- Digest: `research/kaggle/digests/2026-11-05-grading-environment.md`
