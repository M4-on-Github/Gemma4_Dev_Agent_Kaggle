# Kaggle digest 2026-11-17: paper track, what could apply to the main track

Scope: paper-track forum posts since 2026-11-05, five linked untrusted files (cap reached), and a short main-track
update since the morning digest. Zero GPU, CLI only, nothing posted. The writeups page is not CLI-reachable; a
browser-read file from the coordinator is pending and is not incorporated here.

## Headline

**Paper track: two ideas could change a main-track prompt (an executed check after the last edit, and a capped
test-output shape); none has a resolve gain measured on a harness like ours, and the submission model is fixed at
31B, so the E4B numbers in these posts do not transfer.**

## Ranked table

Ranked by how directly the idea could change `agent.yaml`, the prompt, or `sampling.yaml` for the 31B submission.
Tags: [V] official or CLI-verified; [M] participant or mirror text; [I] our inference; "ours" means our own
records.

| # | Idea | Source | Evidence and credibility | What it would change | Already tried by us | Cheapest screening rung |
|---|---|---|---|---|---|---|
| 1 | Run the edited module's tests after the last edit, before submit | Our EXP-034 section 9.2 (ours); corroborated by anisha mehajabin, topic 756473, comment 3551444 | Ours: of Arm R's 30 right-file-wrong-fix tasks, 21 had no test after the last edit, and 15 of 30 ended by submit (C-019, hypothesis). [M] 3551444: E4B runs, about three in four failed attempts applied cleanly but were wrong; no n stated. No paper-track resolve numbers. | Prompt rule and/or loop structure (agent.yaml, prompt). No new tool needed; the shell is already available. | C-019 is a hypothesis; the executed check was not run as an arm. C-005 refuted a heredoc-routing variant (0 of 6 compliance). D-010 and D-005 F3 propose the check, not yet screened. | Zero-GPU trace mining on existing dev-48 traces (the EXP-034 counts already exist); then smoke-8 at about 0.7 GPU-h (D-005 Stage 0c ladder). |
| 2 | Capped test feedback: tail of pytest output plus traceback frames not yet seen, about 1,500 tokens; syntax-gate patches before tests | anisha mehajabin, topic 756473, comments 3551371 (2026-11-07 06:25 UTC) and 3551444 | [M] own runs. more-itertools (5,644 lines): retrieval 2% -> 22%; boltons (files near a 6k budget): no difference. The test-feedback 26% -> 42% figure is second-hand; the opening post was not returned. Model not stated in 3551371; 3551444 is E4B. AST retrieval itself needs a custom tool, which the rules forbid. | Shape of pytest output the agent sees, through prompt guidance (`--tb=short`, tail-limited output). Harness fixed (run_command stdout cap 5,000 characters). | C-004 (lost edit arguments), EXP-041 and EXP-043 (capped feedback partly tried). | Desk check of the current prompt's pytest line (swe_coder.md lines 31 and 119); then smoke-8 at about 0.8 GPU-h. |
| 3 | Log compression that keeps the diagnostic, header and summary markers | msingatullin notebook (`msingatullin/ast-guided-loops-verification-for-gemma-4`); Mikhail, topic 756473, comment 3551292 (30.6% token saving on pytest tracebacks) | [M] 11/11 marker preservation for B2 versus 2/11 for head35 or tail35 on 11 logs; 72.01% fewer raw log bytes; the original compressor lost the marker silently on 10 of 88 logs; 5-task pilot 1/5 in each arm; 9.76% fewer reported API tokens. This is a marker test, not a solve rate. E2E pilot pre-registered but not run in the notebook. | Only prompt-level guidance to filter output (for example, pipe through tail). No compressor can ship as a tool. | No `tb=short`, `tb=line` or log-filter rule in submission/, tools/ or experiments/ (grep). Heredoc routing refuted (C-005). | Zero-GPU count of dev-48 tool outputs at the 5,000-character cap, if traces record it; otherwise desk check; then smoke-8. |
| 4 | Runtime margin of 1.4x on projected worst case | mobassir, notebook `mobassir/why-your-leaderboard-can-t-see-a-3-point-gain`; akshaymathur777 `results.csv` (v0.20 TIMEOUT) | [M] local projections at least 1.36x optimistic (2.8x time-dilated local replica, subprocess sandbox). Our own outside data point: the v0.20 hosted run (ref 57985572, 2026-11-04) timed out. Applying the author's 1.4x to our 11 h gate gives 7.9 h [I]; our T2 projection (EXP-028) was 10.04 h, so it would fail that margin. | `max_time_minutes` in agent.yaml; the packing gate 120 x (max_time_minutes + 1.0) min <= 11.0 h. | C-003, C-008, EXP-028 (T2 10.04 h). | Zero GPU: `tools/estimate_budget.py` with a 1.4x factor applied as a sensitivity row. |
| 5 | Thinking budget or temperature changes: T=0.15 with a 2k thinking budget; T=1.0 causes off-by-one repairs | Mikhail, topic 756473, comment 3551448; Japan OpenData Lab, topic 760014 (title only) | [M] 3551448: mechanism claims with no numbers. 760014: title reads "best custom 15/114 vs zero-think baseline 16/114" over 1,800+ trials; no body, no comments; a withdrawal; postDate is after today (see anomalies). Both low credibility until the body is read. | `sampling.yaml` (thinking_budget, temperature). | C-010 (thinking 4096 vs 256 changed the edit-loss rate, not dev-48 resolves). | Smoke-8, one change at a time, about 0.8 GPU-h. |
| 6 | Read the board with the noise figures: sigma about 1.5 tasks per draw; 18 to 37 draws per arm for a one-task difference | mobassir notebook; akshaymathur777 `results.csv` (identical zip scored 0.17 and 0.12); 756483 paired guard | [M] author's own draws; the identical-zip pair is one outside data point. Consistent with our C-001 (MDE about 4 tasks) and C-016. No submission change. | Decision rule for reading the board, not the submission. | C-001, C-016, EXP-012, EXP-031. | Already computed; no run needed. |
| 7 | Prompt hygiene rule H (negative result) | yu_kuo14, topic 756483, comments 3551415 and 3552920 | [M] pre-registered. First grading: cap_no_edit 72/466 for both v6 and H; paired solves -3, two-sided sign test p = 0.70; H dropped. After grading fixes (a shadowed router; 12 empty patches recorded as resolved): paired solves +4 (33 vs 29, p = 0.70). Null on the primary endpoint. | Nothing ships from H. Useful as a warning against prompt-rule variants without a paired arm. | C-005, C-009. Our BASE and gold controls (C-022) check the grader defect class. | Not applicable. |
| 8 | Derived data release on the paper track | Elan Markowitz (reply), topic 757562, comment 3553006 | [M] reply by a competition host-side participant; treat as a host ruling only after checking the rules page. Derived items keyed by task_id are allowed on the paper track; the reply does not cover the main track. | Release path only (`export_release_csv.py` allowlist). | plan.md:52 (stricter rule we currently apply). | Not applicable. |

## Could any of this change a main-track submission?

- Rows 1, 2, 3 and 5 are prompt or sampling changes that agent.yaml can carry. Row 4 is a single `max_time_minutes`
  value. None needs a custom tool, a new model, or a new dependency.
- None has a resolve gain on a harness like ours. The strongest number (2% -> 22%) is one repository with no n
  stated. The lit note (commit 26dc15b) found no paper-track writeup showing a resolve gain over a plain 31B single
  loop.
- The E4B numbers (3551444, 760014 if E4B) do not transfer to our 31B submission model.
- Each candidate would still need its own pre-registered experiment and a paired arm on dev-48 before any upload.

## Part B: main-track update since the morning digest (c5f401f)

I could not verify c5f401f (git log is blocked for this agent; see guard blocks). The items below come from the
CLI only.

- **759781**, Mauricio Lopez, 2026-11-17 03:57 UTC, "My Agent Approach - Gemma 4 Developer Agent": -3 votes, 0
  comments. Title only; body not returned.
- **759279**, michael2026, 2026-11-14 16:54 UTC, "Lora permission on model": 0 votes, 0 comments. Relevant to the
  open Q4 and to the LoRA hold (C-024). Title only.
- **760012**, Murugesan Narayanaswamy, postDate 2026-11-18 00:53:50 UTC, "On the competition experience": 0 votes,
  0 comments. **Timestamp anomaly** (see below).
- **760014**, Japan OpenData Lab, withdrawal, postDate 2026-11-18 01:06:31 UTC: **timestamp anomaly**; see row 5.
- 759630, 759702, 759580 and 759322 are already in existing threads; nothing new retrieved for them.
- No new leaderboard, host ruling or notebook with LB >= 0.20 was found in this pass.

Thread notes: `research/kaggle/threads/kg-main-759781-759279-760012.md`.

## Timestamp anomaly

Four timestamps are later than the current date (2026-11-17):

- 760012 postDate 2026-11-18 00:53:50 UTC
- 760014 postDate 2026-11-18 01:06:31 UTC
- dariushafshar notebook `lastRunTime` 2026-11-18 01:14 (phase-1 read of the kernel listing)
- the LB CSV member timestamp 2026-11-18T00:49:37 (phase-1 read)

Possible causes are a timezone or export-label mismatch. Not verified. Treat the affected dates as unverified in
any claim.

## Data notes

- Telemetry `episode_metrics.csv`: 124 episode rows; the `analyze_traces.py` docstring says 128. Unresolved.
- Telemetry `results.csv`: 11 hosted rows; the `analyze_traces.py` docstring says 9 hosted submissions. Unresolved.
- Telemetry `episode_metrics.csv`: 51 of 124 resolved; 8 rows with `repro_file_leaked` set, 2 of them resolved.
  The `CWE` termination label and `repro_file_leaked` are not defined in the files read.
- Six paper-track topics (758545, 758783, 758727, 759153, 758323, 758859) have titles only; no bodies or comments
  returned. Listed in `kg-paper-titles-2026-11-12-batch.md`.

## Untrusted files pulled (cap of five reached; all read with `python -I -X utf8`, never executed)

| Slug | File | Bytes | SHA-256 |
|---|---|---|---|
| msingatullin/ast-guided-loops-verification-for-gemma-4 | ast-guided-loops-verification-for-gemma-4.ipynb | 111,363 | `aca4b0e227ff7d176714c721cd67e0f5019e62fdead77482685c93709ed91eb3` |
| msingatullin/ast-guided-loops-verification-for-gemma-4 | kernel-metadata.json | 792 | `e3ef6888ed8aceeb5e1d49bfa039e064fde6d9eb3b1165272ea8558d556ab538` |
| mobassir/why-your-leaderboard-can-t-see-a-3-point-gain | why-your-leaderboard-can-t-see-a-3-point-gain.ipynb | 62,020 | `df51ae0bc5333a7a2ff5fd5214852ff9503972407515bd6a92e066737508c4a4` |
| mobassir/why-your-leaderboard-can-t-see-a-3-point-gain | kernel-metadata.json | 779 | `bbebb1bd2e02130b86af5d22212e5b7d31702d087fe8378076776325765fdbf6` |
| dariushafshar/gemma-4-lb-58-tasks-bronze-is-a-124-team-tie | gemma-4-lb-58-tasks-bronze-is-a-124-team-tie.ipynb | 149,971 | `c85492554c47b7c4ec5ff8db77ea405d1f825deba2531a5034c63ff10f5510f2` |
| dariushafshar/gemma-4-lb-58-tasks-bronze-is-a-124-team-tie | kernel-metadata.json | 837 | `5df43a1c8ea0b421ca1f7493671c7abb362eebf2c8746e74356a53492135c804` |
| akshaymathur777/gemma4-agent-paper-telemetry | gemma4-agent-paper-telemetry.zip | 48,190 | `596ea6fa5c99737327dd45e2c604050f0317179bb8116f41ef4cce14800ff826` |
| mobassir/swe-agent-eval-validity-gemma4 | swe-agent-eval-validity-gemma4.zip | 12,789,423 | `8d31688c6a45ed17c3f3062079b1d3ec3915501565a26ce8ad5d02326f035186` |

Kernel and dataset metadata carry no version fields. Pull date for all: 2026-11-17. The telemetry hash in an
earlier draft was truncated; the value above was recomputed with `research/kaggle/sha_file.py`.

## Guard blocks (exact text)

1. Git log for c5f401f (Bash):
   `PreToolUse:Bash hook error: [...]: Blocked: allowed commands start with: kaggle competitions topics; kaggle competitions leaderboard; kaggle kernels list; kaggle kernels pull; kaggle datasets list; kaggle datasets download; kaggle datasets files; python -I -X utf8`
   Not worked around. c5f401f is unverified.
2. Pipe and redirect (Bash, `2>&1` on a kg_grep call, and a pipe on an lb helper):
   `PreToolUse:Bash hook error: [python "$CLAUDE_PROJECT_DIR/.claude/hooks/guard_bash.py" "kaggle competitions topics" "kaggle competitions leaderboard" "kaggle kernels list" "kaggle kernels pull" "kaggle datasets list" "kaggle datasets download" "kaggle datasets files" "python -I -X utf8"]: Blocked: chaining, pipes and redirects are not allowed for this agent.`
   Fixed by removing the redirect and running single commands.
3. A placeholder Bash command (`kg_grep_placeholder`) was my mistake and had no effect; it was blocked with the allow-list message in item 1.
4. Write to the session scratchpad:
   `PreToolUse:Write hook error: [python "$CLAUDE_PROJECT_DIR/.claude/hooks/guard_paths.py" "research/kaggle/**"]: Blocked: this agent may only write to research/kaggle/**; got C:\Users\moemy\AppData\Local\Temp\claude\c47af029e2d97a18\a3330dbc-ae18-40d8-9d0c-3b81d26158a6\scratchpad\count_telemetry.py`
   Fixed by writing the helper to `research/kaggle/zip_csv_count.py`.

## Suggested claims (for the lead to decide; this agent does not edit `knowledge/claims.md`)

- **C-019 (update evidence, no status change):** add anisha mehajabin 3551444 as [M] corroboration, a clean-but-wrong
  rate of about three in four failed E4B attempts with n not stated. Keep "hypothesis" until an arm runs.
- **New hypothesis (proposed):** a capped test-output shape (tail plus unseen frames, about 1,500 tokens) raises fix
  rate on modules that exceed the context budget. Evidence: one [M] repository, 2% -> 22%, n not stated. Screen on
  smoke-8 only after a desk check.
- **New hypothesis (proposed):** marker-preserving log filtering keeps diagnostic fields on 11/11 logs versus 2/11
  for head or tail cuts. Evidence [M], marker test only; no resolve claim.
- **Budget sensitivity (proposed, [I]):** with the outside 1.4x margin, the 11 h gate implies a projected worst case
  of at most 7.9 h. Our T2 projection (10.04 h) would fail that sensitivity check. Zero GPU to check.
- **Negative evidence for C-009:** prompt hygiene rule H gave cap_no_edit 72/466 in both arms with paired solves
  -3 (p = 0.70); after grading fixes, +4 (p = 0.70). Supports keeping prompt-rule variants behind paired arms.
- **Rules point (not a claim):** derived items keyed by task_id are allowed on the paper track (host reply, 757562);
  the lead should decide whether our release allowlist stays stricter.

## Files written this pass

- `research/kaggle/digests/2026-11-17-paper-track-applicable.md` (this file)
- `research/kaggle/threads/kg-paper-756473-ast-retrieval-compression.md`
- `research/kaggle/threads/kg-paper-756483-prompt-hygiene-null.md`
- `research/kaggle/threads/kg-paper-757562-derived-data-ruling.md`
- `research/kaggle/threads/kg-nb-msingatullin-ast-guided-loops.md`
- `research/kaggle/threads/kg-nb-mobassir-leaderboard-noise.md`
- `research/kaggle/threads/kg-ds-mobassir-eval-validity.md`
- `research/kaggle/threads/kg-nb-dariushafshar-lb-58-bronze.md`
- `research/kaggle/threads/kg-ds-akshaymathur-telemetry.md`
- `research/kaggle/threads/kg-760014-japan-4b-withdrawal.md`
- `research/kaggle/threads/kg-paper-titles-2026-11-12-batch.md`
- `research/kaggle/threads/kg-main-759781-759279-760012.md`
- Helpers under `research/kaggle/`: `zip_members.py` (rewritten), `zip_csv_count.py` (new), `sha_file.py`, `kg_grep.py`.

Untrusted files under `untrusted/` (gitignored) are listed in the table above.

## Not yet done

- The browser-read writeups file from the coordinator has not arrived and is not incorporated. The writeups page
  is not CLI-reachable.
- The six title-only topics were not pulled (cap reached).
- The comments on the opening posts of 756473 and 756483 are the only sources for those posts' numbers; the opening
  bodies were not returned by the CLI.
