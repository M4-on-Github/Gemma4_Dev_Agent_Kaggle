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

## Timeline

| Day | Work |
|---|---|
| Nov 25 | Checks done (above); conclusion: no 31B lever above about one task |
| Nov 26-27 | Pre-register and push the Kaggle dev-48 arm calls 34 / time 7 (needs user approval); L-008b readout |
| Nov 28-29 | Kaggle L4x4 dev-48 of the winner (time profile, 12 h projection); user approves |
| Nov 26-Dec 2 | One upload per day: until a candidate is ready, re-upload the best-known config (the board keeps the best) |
| Dec 1-2 | Pick 2 finals by pooled evidence, not by the single best public draw |
