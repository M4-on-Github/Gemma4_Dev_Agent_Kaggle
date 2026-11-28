# Final-week plan (2026-11-25 to Dec 2): highest hidden-test score

Written 2026-11-25. Counts only. User goal (2026-11-25): score as high as possible on the hidden tests, ideally around
0.5 with the 31B, and push the E4B as high as possible too, in the little time left. Scores only; no paper.

## Where we stand

- **Leaderboard.** 58 public tasks (1 task = 0.017), about 120 hidden tasks run one at a time in 12 h. The board keeps
  each team's best upload. Public frontier 0.24 (14/58). Our best 0.18 (11/58); the 31B base tree pooled over 3 uploads
  is 0.161. One upload per UTC day: 7 slots left (Nov 26 to Dec 2), 2 finals. One draw's MDE is about 4 tasks (0.07).
- **The cluster overstates the board.** The 31B base solves 0.36-0.41 per task here and 0.16-0.19 on Kaggle (dev-48
  9/48, board 0.161 pooled). The cluster cohorts hold only tasks that grade here (two repositories); the hidden set is
  private repositories. Cluster gains are relative evidence, not score estimates.
- **What is kept.** E4B: retry-on-empty (`trees/e4b-r020-retry`), +1.08 per draw on 79 tasks (CI +0.08..+2.08), +0.67
  on the locked held-out cohort. 31B: the base; no change beat it in 36 rounds. L-008 (E4B self-distilled LoRA): not
  kept.
- **Budget facts (EXP-049, design-for-l4x4).** The 31B projects 10.04 h of 11 (about 14 s spare per task). The E4B
  projects 2.98 h (about 225 s spare per task). Kaggle serves one task at a time, so the L4s decode one sequence at a
  time and most of their batch capacity is idle.

## Reality check on 0.5

0.5 is about 29 of 58, three times our pooled 31B rate and twice the frontier. No change measured in 36 rounds has
moved the 31B by more than noise. The plan below aims at the largest gain the remaining days can test; it is not
expected to reach 0.5.

## The lever: several attempts per task, one picked (test-time scaling)

Oracle ceilings from existing draws (a perfect picker; not achievable, the upper bound):

| | pass@1 | best of 2 | best of 3 | ever (all draws) |
|---|---|---|---|---|
| E4B retry, cdev2-79 (12 draws) | 7.58 | 11.1 | 13.5 | 24 |
| E4B retry, held-out 22 (6 draws) | 2.17 | 3.1 | 3.9 | 5 |
| 31B base, held-out 22 (4 draws) | 9.00 | 10.3 | 11.3 | 12 |

- Harder task sets have a larger pass@k / pass@1 ratio, so on the hidden set the relative ceiling is likely higher than
  the 31B's +25% here.
- **31B:** no spare wall time, so attempts must run concurrently (ParallelAgent branches batch on the idle L4s at
  close to the cost of one). Feasibility and time cost: see below; it does not fit.
- **E4B:** has the wall time for sequential attempts, and can also run them concurrently.
- **The picker decides it.** R-019's file-set picker lost to plain retry. Execution-free pickers (consensus over
  normalized patches) are being simulated on existing draws.

### Picker simulation (done 2026-11-25; `$CLAUDE_JOB_DIR/tmp/bestofk.py`, every k-subset of draws enumerated)

Rule chosen on E4B R-021 ×12 only: **d2** = the most common set of changed non-test files, then within it the patch
with the highest mean Jaccard similarity of normalized changed lines to the others.

| Set | k | pass@1 | oracle | d2 | gain | share of oracle gap |
|---|---|---|---|---|---|---|
| E4B R-021 (79, tuning) | 3 | 7.58 | 13.45 | 8.84 | +1.26 | 21% |
| E4B L-008 ctl (40, check) | 3 | 5.38 | 7.95 | 6.20 | +0.82 | 32% |
| E4B R-036 held (22, check) | 3 | 2.17 | 3.90 | 2.25 | +0.08 | 5% |
| 31B cdev2-79 (6 draws) | 3 | 28.67 | 36.10 | 32.95 | +4.28 | 58% |
| 31B cdev2-79 | 5 | 28.67 | 39.17 | 34.67 | +6.00 | 57% |
| 31B R-036 held (22, 4 draws) | 3 | 9.00 | 11.25 | 9.50 | +0.50 | 22% |

- **31B: +15% at k=3 on 79 tasks, and 80% of it (+3.42 of +4.28) is just "never submit an empty patch".** The 31B
  leaves an empty patch on 16-20% of tasks (E4B 7%). Similarity adds about +0.9 on top.
- **E4B: about +1 per 79 on top of retry.** Under the board's MDE; not worth the E4B's GPU slots this week.

### Why the 31B leaves empty patches (2026-11-25, counts)

- R-036 held ×4 (88 task-draws): 14 empty, of which 11 at the time cap and 3 at the 28-call cap. Non-empty patches
  resolve 36 of 74 (0.49). R-008 ×2 on cdev2-79: 30 empty, 20 time cap, 9 call cap, 1 stopped.
- So the 31B's limit is time, and Kaggle is tighter: L4x4 decodes the 31B at about 25.5 tok/s against 34.5 here
  (README Setup 5), so 8 min on Kaggle buys about 0.74 of the decode it buys here. A Kaggle-faithful cluster screen
  for time-bound changes runs at `max_time_minutes` about 6.

### Harness feasibility of concurrent attempts (2026-11-25, source read; swegemma + ADK 1.36.1)

- Buildable. `ParallelAgent` is allowed. The file tools refuse paths outside `/workspace`, but `/workspace/.wN` is
  allowed, and `run_command` is unrestricted bash, so each branch gets `git worktree add /workspace/.wN`.
- The graded patch is `git diff` of `/workspace` (also at timeout), with untracked files included: the worktree dirs
  must go in `.git/info/exclude`. Branches must not hold `submit_patch` (it ends the task).
- Only the LLM calls overlap. Tools are synchronous on the event loop, behind a per-task lock, so tool time is serial;
  `max_tool_calls`, `max_turns` and the wall clock are one budget per task. `PYTHONPATH` points at `/workspace`, so a
  branch must override it to test its own copy.
- The task ends when the slowest branch ends.

### 31B time cost of parallel attempts (2026-11-25; 6 cdev2-79 base draws; random non-empty pick)

| Attempts | Solves per 79 | Mean task wall | Kaggle projection (h, of 11) |
|---|---|---|---|
| 1 (base) | 28.67 | 346 s | 9.8 |
| 2 | 31.10 (+2.43) | 387 s | 10.9 |
| 3 | 32.08 (+3.41) | 404 s | 11.4 (over) |

The projection scales the recorded 10.04 h by the wall ratio and ignores batching slowdown and serial tool waits,
so it is a lower bound. Two attempts gain about +8% at a 10.9 h projection, too close to the 11 h line for an upload
whose overrun scores zero. Parallel attempts are not the 31B's big lever.

## Kaggle against cluster (2026-11-25, desk; `$CLAUDE_JOB_DIR/tmp/gap.py`, `gap2.py`; counts only)

Kaggle: EXP-028 R (byte-identical to `trees/31b-base`), RH and EXP-003, 3×48. Cluster: 31B base `-te` and held
draws, 562 task-draws.

| per task-draw | Kaggle (144) | Cluster (562) |
|---|---|---|
| resolved | 0.194 | 0.370 |
| empty patch | 0.188 | 0.190 |
| ended at the time cap | 0.194 | 0.306 |
| ended at the 28-call cap | 0.375 | 0.185 |
| mean wall | 311 s | 351 s |
| effective decode per stream | 28.7 tok/s | 23.2 tok/s (4 tasks per GPU) |
| tasks with any import error | 8.3% (4.2% on R) | 3.9% |

- **The missing-dependency theory is wrong.** The agent rarely runs tests (pytest is 1.3% of commands), and import
  errors touch about 4% of tasks on the shipped prompt.
- **Much of the gap is measurement.** On the 40 dev-48 tasks the cluster also grades, Kaggle R scores 8/40 as the
  notebook grades it. With the two test shims (EXP-036), R scores 11/40 and RH 14/40, against the cluster's 13.3/40
  expected; the agent behaves about the same on both. The other 8 dev-48 tasks barely grade on Kaggle (3 gold passes).
  The cluster cohorts are also easier (0.36-0.41 against 0.33 on the shared tasks).
- **Correction to the line above.** The cluster is *slower* per stream than Kaggle (4 tasks share a GPU), not faster.
  So the cluster is time-bound and Kaggle is call-bound. A Kaggle-faithful cluster screen would need *more* time than
  8 min, not 6. T-31b-001 (calls 28 → 40, not kept) was screened under the wrong binding limit.

### What ends a Kaggle 31B task (3×48)

| Ended by | Task-draws | Resolved | Empty | Mean wall | s per tool call |
|---|---|---|---|---|---|
| 28-call cap | 54 | 2 (4%) | 19 | 320 s | 11.4 |
| time cap | 23 | 2 (9%) | 8 | 495 s | 25 |
| finished | 67 | 24 (36%) | 0 | 242 s | 12.8 |

- Over half of Kaggle tasks hit a cap, and almost none of those resolve. The 31B solves what it converges on in about
  20 calls and rarely anything else.
- **Raising calls on Kaggle costs time the 31B lacks.** 28 → 40 adds up to 12 × 11.4 s on a call-capped task, about
  +47 s per task on average, or +1.6 h, so 11.6 h projected: over. 28 → 34 with `max_time` 8 → 7 nets about +0.4 h
  (10.45 h). On the cluster, base call-capped tasks given 40 calls resolved 1/13 and 2/10 (R-001), then hit the time
  cap. Expected gain is about +1 per 48, under the MDE.

## Conclusion (2026-11-25)

No lever found in the record or in today's checks is worth more than about one board task for the 31B:

| Lever | Expected gain | Blocker |
|---|---|---|
| 31B parallel best-of-2 | about +8% relative (+1 on 58) | 10.9 h projected, lower bound; overrun scores zero |
| 31B best-of-3 | +12% | 11.4 h: over |
| 31B calls 34, time 7 | about +1 per 48 | Kaggle-only effect; a cluster screen cannot show it |
| E4B best-of-3 with the d2 picker | about +1 per 79 on top of retry | under the MDE |
| Public trajectory LoRA | unknown | download permission, about 2 days to train, L-008 LoRA lost |

0.5 is not reachable this week on this evidence. The 31B's hidden-set score is set by the tasks it converges on,
and 36 rounds of prompt and config changes have not moved that. The best use of the last 7 days:

1. **Upload every day.** The board keeps the best upload. Re-upload `31b-base` (pooled 0.161, best 0.18) on days with
   no candidate.
2. **One Kaggle-native arm**, `31b-base` with calls 34 and time 7, as a dev-48 kernel (about 3.6 GPU-h of the Kaggle
   weekly 30). It is the only screen whose binding limit matches the board. Pre-register it first. Use the shim
   re-grade (EXP-036) as the endpoint, since the notebook's own grading drops 3-6 tasks per run.
3. **E4B finals:** `e4b-r020-retry`, the one kept improvement (+1.08, held-out +0.67).
4. **Finals:** pick by pooled evidence, not by the single best public draw.

## Update, 2026-11-25 evening: direction review and three rounds in flight

The user lifted the 2-running GPU cap for the final-week rounds and asked for mechanical fixes (settings,
orchestration, skills) reasoned from the failure modes, since prompt changes have not moved scores.

**Where the 31B's failing draws go** (`rounds/trace-vs-reference.md`, 286 failing draws): no edit 105 (86 of them had
read the reference file), partial fix 69, wrong file 34, wrong region 32, wrong change 32, edit tool 14. The two
harness-addressable groups are never-edit (37%) and partial fix (24%).

**Desk checks that closed a line (zero GPU):**

| Idea | Result | Verdict |
|---|---|---|
| Regression check, then retry | ceiling about 0.4 tasks per 79 per draw | closed |
| Harness built-in graph tools | top-5 file recall 29-38% on cdev2-79, level with grep | not worth a round |
| Locator v2 (`tools/locator_v2/`) | file in top 5: 53 of 76 tuning, 20 of 21 check (old BM25 48, 16) | built into R-039 |
| Related sites from real partial-fix patches | some missed symbol listed in 39 of 49 draws, all in 11; precision 0.11 | built into R-039 |

**Rounds, all against one control (kfctl ×8, Kaggle-faithful time scaling ×1.2375):**

| Round | Change | Aimed at | Promote bar |
|---|---|---|---|
| R-037 | calls 34, time 7 | Kaggle's binding call cap | +1.5, CI lower > −0.5, wall ≤ 1.06 |
| R-038 | temperature 0.2 | draw-to-draw variance on tasks the 31B can solve | +2.0, CI lower > 0, wall ≤ 1.06 |
| R-039 kfmap | map script, search-free draft, audit script, finish | never-edit and partial fix | +2.0, CI lower > 0, wall ≤ 1.06 |
| R-039 kfmaplite | map script, then the normal agent | wrong file, never-edit | +2.0, CI lower > 0, wall ≤ 1.06 |

Two promoted changes are not stacked untested; the combination would be its own round. A promoted tree must finish
one real upload by about Nov 28 to be a final.

### Outcome of the four rounds (2026-11-26)

| Round | Result | Outcome |
|---|---|---|
| R-037 calls 34, time 7 | −0.50 per draw (CI −2.62..+1.62), wall 0.976 | not kept |
| R-038 temperature 0.2 | −1.75 per draw (CI −3.88..+0.25) | harm |
| R-039 map pipeline, map only | both killed at the d1 time gate; where the pipeline ran in full it matched the control | not kept |
| R-040 bounded-draft pipeline | killed at d1 (28 empty, 499 s); d1 solved 13 where the control expects 30.4 | not kept |

The 31B candidate stays `31b-base`. The E4B candidate stays `e4b-r020-retry`. No cluster round since R-021 has
produced a change to ship.

### Field check (2026-11-26, Kaggle API read-only; notebooks read as data, nothing executed)

- **Main board.** The top is still 0.24 (14 of 58), and at least the first 15 teams sit on exactly that score, most
  dated Nov 23-24. No team shows above it.
- **Small-model board (host notebook, now live with 1,516 teams).** Top 0.12 (2 teams), 0.10 (34), 0.08 (196), 0.06
  (412), 0.05 (439). We are at 0.05, rank 827.
- **Public write-ups agree with our record.**
  - One team scored a single 31B bundle eleven times unchanged: 7 to 12 of 58, mean 9.45 (ours: 36 of 232, mean 9.0).
    Its eight paired single-change tests (291 task pairs) found no gain; the one change that moved the count was a loss.
  - One E4B write-up: six E4B uploads between 3 and 5 of 58 whatever the prompt; three 31B-to-E4B distillation
    adapters all worse on held-out tasks; a public E4B adapter no better and 48% slower; thinking 1024 no gain.
- **Reading.** No public bundle or method scores above what we already run. Both boards look like many draws of
  near-equal configurations, so the top public scores are mostly the best of many uploads.

### Upload state and the E4B candidate zip (2026-11-26)

- **No upload since Nov 12.** The upload log on `all-work-consolidated-2026-11-20` ends at row 17 (2026-11-12) and
  that branch's last commit is 2026-11-22. `e4b-r020-retry` has never been uploaded; handoff H-003 is still open.
- **Zip built here so the upload needs no other machine:** `harness-eng/dist/e4b-r020-retry/submission.zip` (not in
  git), 9 members, 7,565 bytes, sha256 `e776e776ff9cdf11ccb4c215c4896259d3948572674f16b60119bfaa8daa44c0`, the same
  hash on a second build.
  - Built with `tools/pack_submission.py`'s own `build_tree` and `write_zip`, called directly, because the packer
    refuses this tree on two known errors: the false "root agent has no way to modify files" (H-002, an `agent_tool`
    root) and the cap-only time gate (the tree projects about 4.4-4.9 h on L4x4; rows 11-17 were uploaded under the
    same recorded override). No rejected prompt marker.
  - **Not run on Kaggle.** An `agent_tool` root with a skill has never been through the real scorer. The risk is one
    upload slot scoring zero; the slots are otherwise unused.
  - Uploading it needs the user's approval file with this hash and a recorded `plan.md` 5.8 override.

### Forum findings that change the upload plan (2026-11-26, topics read through the API)

- **Queue.** Participants report 30-40 h from upload to score and rising; the host's Nov 19 post gave 20-24 h. A team
  may hold one pending submission, so the daily cap no longer sets the pace. About three more scored uploads fit
  before Dec 2 23:59 UTC. No host answer on whether a submission still pending at the deadline is scored.
- **Skill scripts on the official scorer.** Two teams report that skill scripts do not see the task repository there
  (a skill-only bundle scored 0.00 twice; a search script indexed its own folder). No host answer. If true:
  - `e4b-r020-retry` would never retry on the scorer (`count.py` prints 1 on a read error), so its cluster gain
    would not carry over. **The recommendation to upload the zip built above is withdrawn** until R-041 reads.
  - R-039 and R-040 could not have shipped even if they had won.
- **Skill names** must be lowercase kebab-case or the agent does not start and the board shows 0.00 (`change-count`
  and `codemap` pass).
- **Faulty scorer GPU.** The host found one, back to Oct 12; about 125 submissions scored 0.00 at 3,230 bytes and
  will be rerun. None of our 17 submissions has that size.
- **Our submissions (API list):** 17, all complete, none pending; the last is 2026-11-12.
- **R-041** tests the retry with the count made inside the sandbox by a shell-only `agent_tool` instead of a skill.

## Timeline

| Day | Work |
|---|---|
| Nov 25 | Checks done (above); conclusion: no 31B lever above about one task |
| Nov 26-27 | Pre-register and push the Kaggle dev-48 arm calls 34 / time 7 (needs user approval); L-008b readout |
| Nov 28-29 | Kaggle L4x4 dev-48 of the winner (time profile, 12 h projection); user approves |
| Nov 26-Dec 2 | One upload per day: until a candidate is ready, re-upload the best-known config (the board keeps the best) |
| Dec 1-2 | Pick 2 finals by pooled evidence, not by the single best public draw |

## Race rounds R-042 to R-048 (added 2026-11-27)

| Round | Model | Change | Result per draw (79 tasks) | Decision |
|---|---|---|---|---|
| R-042 | 31B | race of three solvers in git worktrees | dropped at the early check (edits landed in the shared root) | not kept |
| R-043 | 31B | R-042 with the root's files removed | 30.12 vs kfctl 30.38 (−0.25, CI −2.62..+2.00) | not kept |
| R-044 | E4B | the R-043 race | dropped at the early check (submits without an applied patch) | not kept |
| R-045 | E4B | race with no submit tool | 5.75 vs rcheck 8.12 (−2.38, CI −4.50..−0.50) | harm |
| R-046 | 31B | race, varied starting points | 29.50 vs R-043 30.12 (−0.62) | not kept |
| R-047 | E4B | race, restart on empty | cancelled unread after R-045 | closed |
| R-048 | 31B | race, restart on empty and late hand-in of another copy | 30.50 vs kfctl 30.38 (+0.12, CI −2.50..+2.88) | not kept |

- **The race line is closed for both models.** Where a runner applies a patch the 31B race is 2.3 to 2.6 solves ahead
  of the control's expectation; the 11 to 13 tasks per draw where none applies cost 2.4 to 2.6. Two fixes did not
  shrink that group.
- **Agreement picker, simulated on kfctl (no GPU):** 34.12 if all three attempts run to their end (mean task wall
  480 s against 386 s), 33.66 if the first two finishers are taken when their patches overlap (417 s). Both exceed
  the 31B's time budget before any slowdown from three streams, and neither is built.
- **State on 2026-11-27:** no round since `31b-base` (0.18) and the E4B bundle (0.05) has beaten its control. No
  upload is proposed.

## Weight-side work, L-009 and L-010 (added 2026-11-28)

The harness-side lines are closed (race rounds above; R-049, the background timer, was dropped at its early check).
From 2026-11-27 the work is on the weights, which the submission may carry as a LoRA adapter.

| Line | What | State on 2026-11-28 01:30 UTC |
|---|---|---|
| L-009 `s9` (E4B) | LoRA trained on public solved trajectories of a stronger agent (SWE-smith, MIT) | **harm**: 0.75 vs 8.12 per draw (−7.38); the adapter copies the teacher's reproduce-script routine |
| L-009 `s31` (31B) | the same data for the 31B | training; gets one draw as a check |
| L-009b `s9b` (E4B) | the routine stripped from the data, own solves mixed in (59 rows made it in) | trained; smoke and 4 draws queued |
| L-009b `s31b` (31B) | the same for the 31B | training |
| L-010 (E4B, 31B) | computed rank-1 adapters, no gradient step, scored by replaying stalled turns; run as an edit loop | both loops running; first E4B candidates move stalled turns to edits but also early turns |

**Plan, in order.**
1. Read `s9b` (fold-B reading, d1 kill gate on patches that modify no existing file).
2. Evaluate `s31` (one draw) and `s31b` when trained; the 31B's decode cost under an adapter is read from the same
   draws. If an adapter helps but is too slow, pair it with an early give-up on stalled tasks.
3. Edit loops: find a dose that moves stalled turns without moving early turns; then unit-level edits (the units
   most responsible for the difference, as in the weight-space-programming post); a candidate that passes the
   replay bar gets a served smoke and task draws, pre-registered in `rounds/L-010` first.
4. A computed adapter has not yet been loaded by the server; its first smoke is also the check that a rank-1,
   one-module adapter file is accepted.
5. Upload window: Kaggle grading has taken 30-40 h and the deadline is 2026-12-02 23:59 UTC, so a candidate must
   be ready by about 2026-11-30. Any upload needs the user's approval file.

## Desk check 2026-11-28: could a run of the existing tests catch a failing patch before it is handed in?

Zero GPU, from the graded test output of the control draws (kfctl x8, rcheck x8) and each task's test patch.
A failing patch is "checkable" when the graded run stops at a collection error that is not a missing new name, or
fails a test the test patch does not touch. This is an upper bound: the agent does not know which test files are
graded.

| | 31B (295 failing patches) | E4B (536) |
|---|---|---|
| only new or changed tests fail (not checkable) | 62% | 50% |
| collection error, not a missing new name (checkable) | 18% | 28% |
| breaks a test the test patch does not touch (checkable) | 8% | 13% |
| collection error on a new name the test needs | 8% | 7% |

Selection simulation over the same draws (solves per 79): 31B one attempt 30.38; first non-empty of three 33.14;
with the test gate 33.87; oracle of three 37.39. E4B 8.12; 8.45; 9.46; 12.79. Tasks solved in any of eight draws:
43 of 79 (31B). So the gate is worth about +0.7 (31B) and +1.0 (E4B) as a selector on top of three attempts; its
value as repair feedback is not measured.
