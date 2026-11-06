---
name: harness-stack
description: How to validate, pack, run and analyze agent configs for this competition - the tools under tools/, Kaggle kernels, run analysis, and the Windows and git pitfalls that have cost time.
user-invocable: false
---

# Harness stack

> The experimenter maintains this skill. `SKILL.md` holds only verified facts every run needs; `reference/` holds details read on demand. Prune a note when a later fact supersedes it. Anything marked (unverified) must be checked before you rely on it. CLAUDE.md is the short form of the same material.

## Environment

- Python 3.13 (miniconda) is `python` in the Bash tool; the repo needs >= 3.12 with `pyyaml` and `pytest`. `python -m pytest -q` runs 49 tests (2026-11-05) in seconds on synthetic data; run it after touching `submission/`, `tools/` or adding a tracked file (two tests check the live tree and every tracked file).
- Anything that reads downloaded or third-party files (`untrusted/`, run bundles, notebooks) runs as `python -I -X utf8 ...` so nothing is imported from the data's directory and encoding is stable.
- `core.autocrlf=true`: the zip sha256 reproduces only from committed LF blobs. Pack from a clean export of the committed tree, compare `sha256sum` with the recorded value before any upload. Export with `git -c core.autocrlf=false archive HEAD <tree> | tar -x -C out/<dir>`: plain `git archive` applies autocrlf and writes CRLF, so the repack differs even when the worktree is LF (EXP-038, 2026-11-05). `git ls-files --eol <tree>` showing `i/lf w/lf` means the worktree pack already matches.
- User-level hook blocks any `git commit` message carrying a Claude co-author or "Generated with" line. Commit without attribution lines.
- Bash heredocs whose body contains an apostrophe break the tool wrapper; use the Write tool for such files, or keep heredoc bodies apostrophe-free.
- Odd directories `runs;C` and `tools;C` at the repo root are artifacts of a PowerShell path error, empty, untracked; ignore them.

## Rules module and the validate -> pack -> gate chain

- `tools/submission_rules.py` holds every constant (tool registry, allowed keys, limits, lint patterns, `RUN_BUDGET_HOURS`, `PACK_GATE_HOURS`, `EXPECTED_HIDDEN_TASKS`, `ASSUMED_SETUP_MINUTES`). Change a rule there, not in consumers.
- `python tools/validate_submission.py <tree> --strict [--official --json]`: schema plus lint; exit 0 VALID. `--official` also runs the harness's own validator when its wheels import.
- `python tools/pack_submission.py [--src <tree>] [--out <zip>] [--allow-warnings] [--skip-budget-gate]`: ships the closure reachable from `agent.yaml` plus `eval_config.yaml`; deterministic zip; prints sha256; refuses rejected prompt markers. Shipped set for the repo tree is exactly `{agent.yaml, eval_config.yaml, prompts/swe_coder.md, configs/sampling.yaml}` (asserted by a test).
- Gate: `120 x (max_time_minutes + 1.0) min <= 11.0 h`; 4.5 passes at exactly 11.00 h; 5.0 is a hard error; `--skip-budget-gate` demotes it to a warning (used for #2, which timed out, and #11, override recorded in EXP-027 §2).
- `python tools/estimate_budget.py --eval-config <eval_config.yaml> [--results <summary.jsonl>]` projects the 12 h total; with `--results` it uses the measured distribution.
- `timeout_seconds` also bounds the hidden test run; below ~100 s a slow test module fails a correct patch (rank-3 v18 comment). 240 and 300 are both safe.

## Kaggle kernels

- `python tools/build_notebook.py --embed <zip> --username rainm4 --cohort experiments/cohorts/<cohort>.txt --out notebooks/<expNNN_dir>/kaggle_eval_l4x4.ipynb` builds from `notebooks/kaggle_eval_l4x4.py` (py:percent). `--set` rewrites parameter-cell assignments. The value is Python source and must be a literal: quote strings as `--set EXP_ID='"EXP-0NN-x"'`. Since 2026-11-05 the builder refuses a non-literal value or a parameter cell that does not parse; the EXP-030 kernel died on an unquoted value. Hazard (EXP-020): cell 5 sets `max_time_minutes: 60.0` under `if not RUN_AGENT:`.
- `kernel-metadata.json`: copy from the last working arm (`notebooks/exp025_armA`, `exp028_armR`) changing only `id` and `title`; keep `enable_gpu`, `machine_shape: NvidiaL4`, the pinned `docker_image` sha (`plan.md:1188`), `dataset_sources` (wheelhouse), `competition_sources`, `model_sources`. `enable_internet: false`. `build_notebook.py` itself writes a default `kernel-metadata.json` (id `rainm4/gemma4-eval-l4x4`) into the output directory, so write the copied one after the build, not before (seen in EXP-037, 2026-11-05).
- Adapters (LoRA): how a submission's `adapters/` reaches vLLM, the `--max-loras` and `--max-lora-rank` sizing, and the silent fall-through to the base model are in `reference/adapters.md` (read from the wheel source, 2026-11-05). Whether the served model applies them is open (Q4, EXP-047).
- Serving (2026-11-06, EXP-049): a submission cannot set any vLLM memory or batching flag except LoRA sizing. Our server and the scorer both run max_num_seqs 256 and max_num_batched_tokens 2048, the vLLM defaults below 70 GiB (`arg_utils.py:2053-2072`). `agent_tool` runs its inner agent in a fresh session with no compaction (`agent_tool.py:241-249`). Details and the in-task concurrency facts are in `reference/serving.md`.
- Running a small variant (2026-11-05): the eval notebook takes the model from the embedded zip's `agent.yaml` (31B, E4B or E2B, `-it-qat-w4a16-ct`; mirror of `ALLOWED_MODEL_NAMES`); the only metadata change is `model_sources` = `google/gemma-4/other/<name>/2`. Serving recipe and budgets are the same as 31B; 12B is not supported by our notebook (needs `--hf-overrides`). Facts, tags and the step list: `reference/small-variants.md`.
- `kaggle kernels push -p notebooks/<expNNN_dir>` (the push guard always needs the committed, clean EXP file with a readings heading. On top of that, the notebook must meet one of these:
  - `RUN_AGENT = True` and a `**Cohort:**` line matching its `TASK_IDS`;
  - `RUN_AGENT = False`, from an exp000 directory;
  - no `RUN_AGENT` parameter at all, with CPU-only metadata (`enable_gpu` and `enable_tpu` false, no `machine_shape`, empty `model_sources`). This case has no cohort check (45996cd, user decision 2026-11-05).

  `RUN_AGENT = False` outside exp000 is still blocked. A zero-task GPU probe (no `RUN_AGENT`, GPU metadata) matches none of the three and is refused; seen with EXP-047, 2026-11-05.) `kaggle kernels status rainm4/<slug>`; `kaggle kernels output rainm4/<slug> -p runs/<EXP>-<arm>/`.
- Quota 30 L4x4 GPU-h per week; no CLI query exists, the lead keeps a ledger in `knowledge/plan.md` from kernel wall-clock. UNVERIFIED (2026-11-03, web sources disagree): whether L4x4 hours count 1x against the 30, and the reset day (Saturday 00:00 UTC per one source). Settle it by reading the quota counter in the notebook sidebar before and after a run, then replace this line. Measured: dev-48 at 4.5 min / thinking 4096 ~3.9 h; at 8 min / 28 calls with the v24 prompt 4.09-4.12 h kernel wall (EXP-028 §9.5: mean task 297 s, vLLM start 342-397 s). smoke-8 ~0.8 h. vLLM start ~0.25 h.
- Kernel outputs: `task_results.jsonl` (one row per task) and `traces/trace_<id>.json`. Both are competition data: `runs/` is gitignored.
- `kaggle kernels output <id> -p runs/<EXP>-<arm>/` nests the bundle as `runs/<EXP>-<arm>/runs/<EXP>-<arm>/` plus a `.zip` copy; move the inner directory up before running `analyze_traces.py`. The kernel log (`<slug>.log`, JSON list of `{time, data}`, seconds since kernel start) holds `vLLM up in N s`, one `[k/48] <id> ... agent=<s>` line per task and the kernel wall (last entry); `duration_s` already includes grading in this notebook.
- The session timeout is not a hard per-task bound: one EXP-028 RH task ran 752 s at an 8-min cap.
- Hygiene and `.gitignore` admit a jsonl in `experiments/` only when it is named exactly `summary.jsonl`; store per-arm copies as `experiments/EXP-NNN/<arm>/summary.jsonl`.
- Pitfall: the push guard reads the text of every Bash command, so a heredoc, commit message or patch script whose text contains the exact push command (the three words in sequence) is blocked as if it were a push. Write such files with the Write tool, or keep the command out of the text.

## Run analysis

- `python tools/analyze_traces.py runs/<EXP> --cap-minutes <cap> --max-calls <calls>` -> `summary.jsonl` + `aggregates.json`. Counts arg-loss failures by the harness string `mandatory input parameters are not present` (the `"status": "error"` envelope misses them ~10x).
- Compaction is live in the scorer, and no trace step records it (Q7, 2026-11-05).
  - Before each model call of any agent, sub-agents included, if the latest prompt count is ≥ 14,336, everything but the last 5 events is summarized by one extra model call. That call counts on the task clock but not as a turn.
  - It fired 49 times in EXP-028 Arm R. `compactions` before 2026-11-05 read 0 and is wrong in every older `summary.jsonl`.
  - `agent.yaml` cannot set it. Details, including the ParallelAgent issue 7324 risk, are in `reference/compaction.md`.
- **ParallelAgent sub-agent steps in a trace** (EXP-040, 2026-11-05):
  - They appear in completion order, not agent order, and they are stamped when the stage emits them. All 16 voters of one burst fall within 0.15-0.44 s, so stamp spreads are not generation times.
  - Segment passes as maximal runs of consecutive sub-agent steps, not by the first agent's name. Keying on voter_01 misfiled 8 restart-pass votes in EXP-040 (§7 item 8).
- The harness records a nudge as a `source: "system"` step with `extra.event_type == "continuation_nudge"`. `analyze_traces.py` counts those since 522c561 (2026-11-05); `summary.jsonl` files made before it show `nudges` 0 (EXP-038 has 9, EXP-028-armRH 4).
- Run directories hold each trace twice (`traces/` and `official/traces/`); a recursive glob over the run dir double-counts. Read `traces/` only, as `analyze_traces.py` does.
- `python tools/run_forensics.py forensics runs/<EXP>` (where wall-clock went, first-edit turn); `python tools/run_forensics.py compare runs/<A> runs/<B>` (paired 2x2 on shared ids).
- `python tools/regrade_patches.py` re-grades collected patches at 0 GPU-h. It runs only on a Kaggle CPU kernel: `swegemma` and the pinned image are not available locally.
  - Match the scored grade with `--timeout 240 --verification-timeout 300`. The eval notebook passes `timeout_seconds` from `eval_config` but no `verification_timeout_seconds`, so the harness default of 300 s applies.
  - Empty patches are graded, as base plus the test patch.
  - Template and builder: `experiments/EXP-036/`. The built `.ipynb` embeds agent patches and must stay untracked: give the notebook directory a `.gitignore` of `*.ipynb`, as `notebooks/exp036_regrade/` does, and track only that file and `kernel-metadata.json`.
  - The template's `EXP_ID` and `PASSES` are literals for EXP-036 (R, RH, GOLD, BASE). For any other arm set, pass `--exp-id EXP-NNN-regrade --passes <ARM>,GOLD,BASE`, or the notebook dies at its count assert. The defaults rebuild EXP-036 byte for byte (EXP-038, 2026-11-05).
  - The push guard passes such a notebook only when it has no `RUN_AGENT` parameter and its metadata is CPU-only. Copy `notebooks/exp036_regrade/kernel-metadata.json` and change only `id` and `title`. EXP-036 v1 was pushed this way on 2026-11-05.
  - Runtime, measured by EXP-036: four 48-task passes at a 20000-character tail took 0.72 h on the CPU image (Python 3.12.13, 4 CPUs), including the 75 s wheel install. The output bundle nests: move `runs/<EXP>/` up a level after `kaggle kernels output`.
  - On this grader, 6 dev-48 tasks grade the same with the gold patch and with an empty patch: `requests_6644` always resolves, and `httpx_3672`, `requests_7205`, `requests_7309`, `requests_7315` and `requests_7427` never do. Paired comparisons are concordant on them in all eight gradings seen so far (observed, not structural; EXP-036 critic); absolute dev-48 rates are not. A tree that does not vendor has about 27 informative dev-48 tasks as run (48 - 6 - 15 gated), and smoke-8 at most 4 of 8.
- `tools/gold_control.py` needs the Docker orchestrator and cannot run on Kaggle.
- `python -I -X utf8 tools/exp024_stats.py` and `tools/exp022_stats.py` regenerate the paper's and the direction reviews' numbers.
- Only `python -I -X utf8 tools/export_release_csv.py runs/<EXP> ... --out paper/release/<file>.csv` produces a publishable per-task file (positive allowlist of fields).

## Measured facts to reuse, not re-derive

- Our 12.8 KB prompt at 4.5 min: 79-96% of tasks run to the cap (E0 79.2%, EXP-025 Arm A 95.8%); mean ~258-274 s; `cap x 120` is accurate to 4% for it. Fixed per-task overhead outside the cap: setup ~3.3 s median, grading ~14 s mean (EXP-016).
- The rank-3 v24 prompt at 8 min on their dev sets: mean 275-296 s, 15-24% at cap, median 25 calls, median first edit at step 10 (`research/2026-10-28-kaggle-open-scouting.md` §3).
- `edit_file` arg loss: 37.9% of calls across two dev-48 runs (EXP-024); 53.5% at thinking 256 vs 18.2% at 4096; the lost call's `new_string` ends in `ng:` on 200/201 (EXP-026 §1); ~90% identical-retry rate after a loss.
- A per-agent call or read limit stated only in a prompt is not enforced: the harness has one shared call counter and no per-agent cap. The EXP-032 localizers broke their 5-call limit (§7 item 15), and the EXP-040 proposer broke its 4-read limit on 3 of 8 tasks (7, 7 and 13 reads; §9.8). Do not design on such a limit holding.
- Grading runs whole test files; `pytest -k` is faster but a broken sibling test fails the task (`experiments/README.md` §1h).
- The grading data was confirmed from the harness source and EXP-035 (2026-11-05).
  - **Which tests run.** pytest runs only the files that the test patch touches (`Task.test_files` = `extract_test_files_from_patch`). A failing test in any other file is therefore impossible by construction.
  - **The test-patch diff.** It has `---`/`+++` headers with no `diff --git` line, and a created file is a lone `@@ -0,0 +1,N @@` hunk.
  - **`test_tail`.** It holds the last 1500 characters of `STDOUT:...STDERR:`. The `FAILED`/`ERROR` lines carry parametrized ids, so to check that the list is complete, count those lines against the count line; do not deduplicate them.
  - **`test_exit_code`.** 2 means collection was interrupted, -1 means the test patch did not apply, and 124 means a timeout with an empty tail.
  - **Snapshots.** Base-commit repo snapshots for all 129 tasks are at `data/local/snapshots/<id>.tgz`. Read them in one sequential pass (`tarfile.open(p, "r|*")`, keep the members you need). Per-member `extractfile` on the random-access handle re-seeks the gzip stream, so scanning a tests tree over 15 snapshots ran over 120 s; one sequential pass took 27 s (EXP-037 `desk_checks.py`).
  - **Known gap.** In the EXP-028 grading, fastapi tests fail collection on a missing test-only package (EXP-035 §9.3).
  - **Protected files are stripped from the agent's patch** (2026-11-05, from the critic's EXP-043 review, checked against swegemma 0.2.11 source).
    - **Where.** `strip_protected_files_from_patch` (`harness/verification.py`) runs on the diff in three places: `submit_patch` (`tools/execution.py`), before it reports `patch_size` and `files_changed`; the runner's fallback working-tree diff; and the final `agent_patch` (`harness/agent_runner.py`). It drops whole file sections.
    - **What is protected.**
      - By base name: `conftest.py`, `pytest.ini`, `pyproject.toml`, `tox.ini`, `setup.cfg`, `.pytest.ini`, `sitecustomize.py`, `usercustomize.py` and the harness's own stub module.
      - Any `*.pth` file.
      - Files named `test_*.py` or `*_test.py`.
      - Any `.py` file with a parent directory named `tests`, `test` or `testing`, matched case-insensitively.
      - The task's `test_files`.
    - **Consequence.** An edit confined to those files submits an empty patch (rich_4075 in EXP-038; EXP-043 §9.7 item 11). A top-level package such as `<pkg>/__init__.py` is not stripped. The same file under `tests/` would be.
- Upload under any filename other than `submission.zip` returns a bare 400 and costs an attempt, not the slot (EXP-023 §6).
- Grading time for an upload: 6 to 22+ h observed (#11 pending at 21.5 h on 2026-10-29).
