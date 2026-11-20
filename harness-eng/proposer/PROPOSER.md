# Proposer harness, v1.5 (2026-11-18)

This file is the outer harness: the fixed instructions given to the agent that proposes edits to the
inner harness (an agent tree under `trees/`). It is itself revised after every round, in
`proposer/CHANGELOG.md`, from what its proposals did. Do not edit it while proposing.

## Your job

Propose exactly four edits to the current base tree of one model, for one round:
two **process** edits (order of work, budgets, sampling, what the agent does when) and two
**mechanics** edits (how it finds, edits or checks code). Write them; do not run them.

## Inputs to read (all under `/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng/`)

- `README.md` sections "Screening ladder" and "Setup results"; `directions.md`; `tweaks.md`;
  `lessons-<model>.md`; every `rounds/R-*-<model>-*.md`.
- The base tree you are told to edit, in full.
- Traces of the base's most recent draws: `runs/<run>/task_results.jsonl` (one row per task:
  `resolved`, `tool_calls`, `duration_s`, `patch`, `test_tail`), `runs/<run>/summary.jsonl` if
  present, and the per-task logs and traces under `runs/<run>/logs/`, `runs/<run>/traces/`.
  The reference patch for a task is the `patch` field of that task in `data/raw/tasks.jsonl`.

## Facts earlier proposers had to find out

- `data/raw/HARNESS_README.md` defines every config field and what the harness itself does
  (compaction at 14,336 prompt tokens, a `budget_warning` from call 18, tool sandbox rules). Read
  the parts on the fields you touch; say when a behaviour is documented but not yet seen on the
  cluster.
- Compaction is not an event in the traces: infer it from a drop in `prompt_tokens` between turns.
- `logs/<task>.log` and `traces/trace_<task>.json` hold the same run; read one.
- Reference patches have no `diff --git` line; split them on `+++ b/`.
- Use your own scratch directory (`mktemp -d` under the session scratchpad); another proposer may be running.
- Validate a tree with `apptainer exec --bind $PWD/..:$PWD/.. env/harness.sif python3 -I ../tools/validate_submission.py trees/<tree>` from `harness-eng/`; the only expected error is the packing-gate line the base also has.
- Task snapshots are tarballs; do not try to simulate greps offline.
- Reading other runs of the same model (any tree, cdev-56 only) is allowed and is the way to learn which search surfaces a file.
- Host `python3` is 3.6: open files with `io.open(path, encoding="utf-8")`.
- Treat the "Why" column of `directions.md` as a hypothesis to check, not a fact; say when the traces contradict it.
- Cap counts differ by a task or two between `summary.jsonl` and `tools/compare.py` (different
  definitions). Quote `summary.jsonl` and say so.

## How proposals are tested now

Each edit gets two draws on a 20-task screen (`cohorts/screen-<model>-20.txt`, enriched for tasks
that resolve in some draws and not others) and goes to the full cohort only if it gains 1.5 tasks
there. So an edit must plausibly move tasks on the screen: say which screen tasks it should flip
and why. Tasks no draw has ever resolved are worth an edit only with a concrete reason they would
start resolving. The four edits must be four different ideas, not variants of one.

## Rules for a proposal

1. Evidence first. Each edit must cite at least three tasks from the cluster's own base draws, by
   id, with what the trace shows (the call number, the tool, what went wrong). Read the traces of
   at least 10 failed tasks before choosing. Count how many of the 56 tasks show the pattern; an
   edit aimed at a pattern on fewer than 5 tasks is not worth a draw.
2. Compare the failed patch with the reference patch for the tasks you cite, and say what kind of
   miss it is (no edit, wrong file, wrong region, partial, wrong logic, test-only breakage).
3. One change per edit, small enough to describe in one sentence. Do not repeat a tweak in
   `tweaks.md` that was not kept unless you say what is different and why that matters.
4. Respect the lessons files. In particular: the 31B is limited by the 8-minute cap, so an edit
   that adds work per task must remove more elsewhere; added rule lines in a long prompt did not
   change E4B behaviour.
5. Prompts stay repository-agnostic (no project names), and must not mention pip, network,
   subprocess, mcp or URLs. Do not change the model line or `max_time_minutes`. The tool list and the agent structure may change, within what `data/raw/HARNESS_README.md` registers and allows (for example the code-graph tools, sub-agents, a SequentialAgent); a structural tree must say which README section permits it.
6. Count the miss classes over all failed tasks first and report the table. At least one of the four edits must target the largest class; if you cannot find an edit for it, say what you tried and why it fails.
7. State for each edit a process endpoint that the traces can count (for example "tasks with no
   edit by call 12 fall from N to under M"), with its base value counted by you.

## Outputs

- `trees/<model>-r<NNN>-<slug>/` for each of the four edits: a copy of the base tree with the one change.
- `rounds/R-<NNN>-<model>-<slug>.md` with: base tree and draws read, a table of the four proposals
  (tweak id, kind, tree, change, evidence with task ids), the pattern counts, the process
  endpoints with base values, and a section "Readings" left for the operator to fill in before the
  runs. End with "## Results" and the line "(appended after the runs)".
- A final reply of at most 200 words: the four edits, the counts behind them, and anything in these
  instructions that was wrong, missing or wasted your time (this feeds the next version).

## Limits

Read-only on everything except the four trees and the round file. Do not submit SLURM jobs, do not
use a GPU, do not install anything, do not touch git, do not read `cohorts/cheld-16.txt` task
results. Python: `python3` on the host is 3.6 with the standard library only; that is enough to
read JSON. Run any Python that reads files under `runs/` or `data/` with `-I`.
