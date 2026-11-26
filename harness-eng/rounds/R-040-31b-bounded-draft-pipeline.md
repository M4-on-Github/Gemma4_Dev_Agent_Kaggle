# R-040: 31B human-workflow pipeline with script-bounded steps (pre-registration)

Written 2026-11-25, before any job of this round is submitted. Counts only. User request (2026-11-25): review the
failure modes, set out how a person solves these tasks, build an orchestration and skills workflow around that, and
test it. The idea under test: the steps are scripts that manage what the model sees and how long it may look, and the
model is asked only for the judgement.

## Failure modes this targets (`rounds/trace-vs-reference.md`, 286 failing 31B draws)

| Failure | Draws | What a person does instead | Mechanism here |
|---|---|---|---|
| No edit (86 of 105 had read the right file) | 105 | stops reading and commits to a first change | draft step: the only way to see code is `show.py`, which answers four lookups and then refuses; the only other tool is `edit_file` |
| Partial fix (own check passed 30 of 32) | 69 | looks for the other places the same change is needed | `audit.py` lists changed functions and related sites not changed |
| Wrong file, wrong region | 66 | follows names from the report into the code | `locate.py` map: top files, top functions, code of the best two |
| Wrong change | 32 | re-reads the report against the diff | finishing step reviews the diff against the contract |

## What R-039 showed (the basis for the change)

- R-039's draft step had `read_file` and used it 11 times per task (368 s); 25 of 69 tasks never reached the
  finishing step and solved 0 (control expects 4.0). Where the pipeline ran to the end it matched the control
  (21 against 21.6 on 44 tasks).
- The map step took 38 s in 4.5 model turns.

## Arm

| Run | Tree | Draws | Stands in for |
|---|---|---|---|
| `R-040-31b-kfmap2-d1..d8` | `trees/31b-kf-map2` | 8 | Kaggle `trees/31b-map2` (8 min) |
| control: `R-037-31b-kfctl-d1..d8` (reused) | `trees/31b-kf-ctl` | 8 | Kaggle `31b-base` |

Changes against `trees/31b-kf-map` (R-039):
- **Draft step.** Tools: `edit_file` only, plus the `codemap` skill. New script `scripts/show.py` prints the exact
  text of a function, class or line range (120 lines at most) and keeps a count in the checkout's metadata
  directory; after four lookups in a task it prints one line telling the model to edit. Thinking budget 1536, output
  4096 (base 4096, 8192).
- **Script-launch steps (map, audit).** Thinking off, temperature 0.2, output 768.
- **Prompts.** Draft prompt names `show.py` instead of `read_file`; the finishing prompt says about 20 calls.
- Checked at zero GPU: `show.py` on a scratch repository returns decorated, multi-line-signature and nested
  definitions whole, counts lookups and refuses the fifth. Both trees validate with the two known errors only.

Cohort and flags as R-039 (`cohorts/cdev2-79.txt`, concurrency 4, 1 Ada GPU per draw).

## Readings (written before any job runs)

1. **Smoke gate** (`S-040-31b-kfmap2-smoke`, 2 tasks): both tasks served; `locate.py` printed a map; `show.py` was
   started and printed code at least once in total; a source edit exists before the finishing step in at least one
   task; `audit.py` ran in at least one task. A failed smoke is fixed once, logged here, and re-run.
2. **Served check**, every draw: 79 rows, 79 served; one re-run with an `r` suffix, logged first.
3. **Decision.** `tools/paired_boot.py --arm` kfmap2 ×8 `--base` kfctl ×8. Wall ratio = arm mean task wall over
   385.6 s.
   - **Promote:** point estimate +2.0 or more, 90% CI lower bound above 0, wall ratio 1.06 or less.
   - **Harm:** −1.5 or less. **Not kept:** anything else.
   - The kfctl control was not faithful on the call cap (R-037 reading 2), so a promote is a cluster result and needs
     a real upload to count.
4. **Mechanism (every outcome).** Per draw: empty patches; tasks at the time limit and call limit; mean task wall;
   seconds in each step; tasks whose finishing step was reached; tasks with a source edit before the finishing step;
   `show.py` lookups per task and tasks that hit the refusal; solve counts split by "finishing step reached".
5. **Draw-1 kill gate** (by hand at the end of d1; a kill cancels d2-d8 unread): fewer than 79 served after one
   re-run, or 25 or more empty patches, or a mean task wall above 452 s.

**Blind guess (not a reading).** Smoke passes first time 60%. d1 gate passes 65%. Promote 7%, harm 20%, not kept
73%. Empty patches fall below the control's 11.75: 70%. Reason for the low promote guess: where R-039's pipeline ran
to the end, it solved exactly what the control solves.

## Queued
- **R-040 smoke submitted 2026-11-25:** 67756.

## Reading 1 (smoke gate, applied 2026-11-25 from the traces): PASS

Both tasks served. `locate.py` printed a map in both (one repeat start got the one-line answer). `show.py` printed
code in both (1 and 4 lookups). A source edit landed before the finishing step in 1 of 2; in the other, the draft's
two `edit_file` calls failed and `audit.py` correctly reported no draft edit, and the finishing step made the edit.
`audit.py` ran in both. Seconds per step (task 1, task 2): map 19, 8; draft 85, 209; audit 5, 13; finish 88, 364.
- **R-040 draws submitted 2026-11-25** (d1..d8): 67758 67759 67760 67761 67762 67763 67764 67765. Not held; d2-d8 are cancelled unread if d1 fails reading 5.
