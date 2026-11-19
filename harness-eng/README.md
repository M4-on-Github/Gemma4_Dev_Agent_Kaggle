# harness-eng

Harness engineering on the pleiades cluster, started 2026-11-17. Everything done on this cluster for
this work lives in this folder.

This is separate from the research record kept on the other computer. It is not a `D-NNN` direction,
it does not use the `EXP-NNN` numbering, and it does not write to `knowledge/`, `experiments/`,
`submissions.md` or `submission/`. It reads them, and the tools under `tools/`, as inputs.

## What it is for

The competition fixes the harness and the model. What an entry may change is the agent config: prompts,
agent tree, skills, sampling, caps, and a LoRA adapter. This loop searches those for two models, one GPU
each:

- `gemma-4-31b-it-qat-w4a16-ct`
- `gemma-4-e4b-it-qat-w4a16-ct`

Both are quantized by rule. The scorer admits only the four `-it-qat-w4a16-ct` checkpoints, and one
submission may use only one of them across all its agents (`tools/submission_rules.py:25-38`).

Order of work: config search first, LoRA after.

## Layout

| Path | Holds | In git |
|---|---|---|
| `README.md` | this file: scope, rules, decisions | yes |
| `tweaks.md` | one row per tweak tried, append-only | yes |
| `rounds/R-NNN-<model>-<slug>.md` | one file per round, readings written before the run | yes |
| `lessons-31b.md`, `lessons-e4b.md` | one entry per round, created with the first lesson | yes |
| `directions.md` | ranked backlog per model, and why each direction was closed | yes |
| `trees/<id>/` | candidate agent configs | yes |
| `slurm/` | sbatch templates and job scripts | yes |
| `tools/` | cluster-only scripts: `fetch_inputs.sh` (sources of data, wheels and models), `hash_inputs.sh`, the eval runner | yes |
| `inputs.sha256` | hash of every input file, written once the uploads land | yes |
| `gpu-ledger.md` | GPU-hours used on the cluster | yes |
| `wheelhouse/` | the competition wheelhouse dataset (uploaded by the user) | no |
| `data/raw/` | tasks, snapshots, graphs, `HARNESS_README.md` (uploaded) | no |
| `models/<name>/` | served checkpoints, and BF16 parents when LoRA starts | no |
| `runs/` | task results and traces: past runs from the other computer, and cluster runs | no |
| `env/` | the Apptainer definition's build output (`*.sif`) | no |
| `adapters/` | trained LoRA weights | no |
| `logs/` | SLURM job logs | no |

Everything stays inside this folder, weights and results included; nothing is placed under
`/data/mmyatmau/`. The untracked paths are listed in `harness-eng/.gitignore`. The folder is under
`/home/mmyatmau`, which has a 500 GB quota (64 GB used on 2026-11-17).

**Why the inputs are not in git.** The competition rules forbid redistributing its data (tasks,
snapshots, graphs, wheelhouse), and this repo is public, so pushing them would breach the rules
(`plan.md:52`, `.gitignore` line 1). Traces quote the task repos, so they fall under the same rule.
The checkpoints are tens of gigabytes, far over what GitHub accepts. Reproducibility is kept another
way: `tools/fetch_inputs.sh` records where every input comes from and the commands that fetch it, and
`tools/hash_inputs.sh` writes `inputs.sha256`, a tracked manifest of every input file's hash. All data
is still saved on the cluster, in this folder; only git leaves it out.

The environment is Apptainer only, with no venv on the host. The image definition is tracked under
`slurm/`; the built image goes in `env/`.

## Decisions (the user's, 2026-11-17)

1. **Stack source.** First answer: the user uploads the inputs. Changed the same evening: a Kaggle
   token is in the repo's git-ignored `.env`, and the inputs are fetched with it over the Kaggle REST
   API by `tools/fetch_inputs.sh` (competition data, wheelhouse, checkpoints) and
   `tools/fetch_runs.py` (output bundles of our past kernels, into `runs/kaggle/`). No Kaggle CLI is
   installed. `inputs.archives.tsv` records each archive's source, size and sha256.
2. **Main lever.** Config search, then LoRA.
3. **Fidelity.** The cluster screens. A Kaggle L4x4 dev-48 arm confirms before anything is proposed
   for upload.
4. **GPUs.** No more than 2 at a time: one for the 31B, one for the E4B. Improve both.
5. **Autonomy.** The loop runs unattended. The user drops in from time to time with directions.
6. **Uploads.** Candidates are screened here; the user approves what is submitted to Kaggle.
7. **Task pool.** A small representative sample first, then dev-48, then all tasks.
8. **Sandbox.** The harness's subprocess sandbox, the same as the Kaggle kernels.
9. **Pivot rules.** See below; none of them stops the loop.
10. **Scope.** This folder only; directions and the research ledger stay on the other computer.
11. **Environment.** Apptainer only on this cluster, no venv.
12. **Storage.** Model weights, results and everything else stay under this folder.
13. **Run length.** No fixed end date for now. The loop runs for a time period the user sets; the date
    to stop searching is decided later.

## The loop

One instance per model. Each round:

1. **Reference.** Base draws of the current tree. The draw-to-draw spread is measured first; a kept
   edit must beat it.
2. **Propose.** Two candidates, each citing trace moments on at least two tasks: one process edit
   (call budget, checks, edit reliability, sibling-site sweep) and one bug-fix-mechanics edit, written
   repo-agnostically.
3. **Probe.** Each candidate runs paired against the reference on the same task ids.
4. **Compose.** Supported edits are merged into one tree, and that tree is run.
5. **Reflect.** One lesson entry. The next round starts from the last kept tree.

The step follows the Harness² paper (arXiv 2610.14224), with gold tests in place of its behavioural
contrasts.

## Screening ladder

Cohorts on the cluster are built from the controls (see "Setup results"): `cohorts/cdev-56.txt` for
tuning and `cohorts/cheld-16.txt`, locked, for L3.

| Level | What | Passes when |
|---|---|---|
| L0 | desk check and trace mining, no GPU | the trigger occurs often enough to read |
| L1 | screen: `cohorts/screen-<model>-20.txt`, 2 draws, against 2 to 3 fresh base draws on the same 20 | promoted if the candidate's mean beats the base mean by 1.5 or more, or by 0.5 or more with its process endpoint met; dropped otherwise |
| L2 | only for promoted candidates: `cdev2-79` (`HENG_SHIMS=1`), 2 draws (31B) or 3 (E4B), against the pooled base | resolves per draw beat the base mean by 3 or more |
| L3 | cheld-16, 2 draws of base and candidate | no loss on the locked ids |
| L4 | Kaggle L4x4 dev-48, on the other computer | time profile and 12 h projection pass |
| L5 | upload | the user approves it |

Changed 2026-11-18T17:00Z on the user's direction (screen a small subset, run the full cohort only for
what looks promising, so more ideas get tried). Before that, rounds R-001 to R-004 ran every
candidate on cdev-56. The screens are enriched for tasks that resolve in some draws and not others:
on cdev-56 the 31B resolves 14 tasks always, 26 never and 16 sometimes (6 draws); the E4B resolves
none always, 36 never and 20 sometimes (22 draws).

## Pivot rules

| Trigger | Action |
|---|---|
| Three rounds in a row with nothing kept or improved | Close the direction with a lesson, take the next one from `directions.md`. If the backlog is empty, refill it from a trace synthesis and continue. |
| A candidate passes L3 | Record it, add it to the ranked queue for Kaggle confirmation, make it the new base, keep improving. |
| The same infrastructure failure twice | Do not retry unchanged. Diagnose, change the setup, record the change, resume. |

Hard limits: 2 GPUs; the time period the user set for the run; no upload without the user's approval;
if the cluster cannot run jobs, report and wait.

## Recording

- A round file is written, with its readings, before the round's first run.
- Every tweak gets a row in `tweaks.md`, kept or not.
- Every job's GPU time goes in `logs/gpu_seconds.csv` (written by `slurm/eval.sbatch`), and its per-run totals
  go in `runs-index.md`. The `gpu-ledger.md` named above was never created; the CSV replaced it.
- Jobs request only what they use: 1 GPU, 4 CPUs, 64G (since R-011, 2026-11-19). The partition bills CPUs,
  and the user's fairshare pays for idle ones. Re-size from `sacct` (TotalCPU, MaxRSS) if concurrency changes.
- Numbers go in these files, not in chat.
- Competition data and traces stay out of git, as in the rest of the repo.
- `runs-index.md` lists every run under `runs/` with counts only (resolved, empty, caps, wall and GPU hours).
  It is regenerated by `tools/run_index.py` after runs land. The run folders themselves are never committed.

## Open

| Item | Default until the user says otherwise |
|---|---|
| Per-task dependencies in the sandbox | not installed. 57 of 129 tasks do not grade here (below). Installing each task's pinned wheels from `data/raw/wheels` would fix most; it is an install, so it waits for the user's word. |
| LoRA training data | public repos only |
| Past runs Kaggle could not give | `EXP-032-t4` and `EXP-037-vendor` returned HTTP 403; the EXP-030 kernel has no output. Needed only if a round pairs against them. |

## Run 1

- Period set by the user: 1 day. Start 2026-11-18T06:29Z (first reference draw submitted), end
  2026-11-19T06:29Z. No new job is submitted after the end; running jobs finish.
- One Ada GPU per model, jobs named `heng_31b` and `heng_e4b`, submitted with
  `--dependency=singleton` so each model holds one GPU at a time.
- `--concurrency 4` for both models; the time cap is not scaled (8 min as shipped).

## Setup results (2026-11-18)

1. Inputs: fetched with `tools/fetch_inputs.sh` (Kaggle API, token in `../.env`); hashes in
   `inputs.sha256`. 43 past kernel bundles in `runs/kaggle/` (`tools/fetch_runs.py`).
2. Image: `env/harness.sif` (11 GB), built by `slurm/build_env.sbatch` from `slurm/harness.def` over a
   local copy of `/data/mmyatmau/gemma4_judge.sif`; no image pulled. Network installs approved by the
   user 2026-11-18: torch 2.10.0 cu128 stack, litellm 1.82.4 and the missing PyPI dependencies, apt
   git and patch. `flashinfer-jit-cache` from the base is removed (it stops vLLM 0.19.1 starting).
   Resolved set: `slurm/harness.lock.txt`.
3. Nodes: only `pleiades-0-17` and `pleiades-0-23` (RTX 6000 Ada) work. On `pleiades-1-10` CUDA
   fails to initialise (`cuInit` 999) with this image and with the base image.
4. Runner: `tools/cluster_eval.py` via `slurm/eval.sbatch`; controls via `slurm/control.sbatch`.
   Comparison and GPU ledger: `python3 tools/compare.py`.
5. First end-to-end draws, smoke-8, one task at a time (`runs/F-000-*`):

   | Model | Server start | Decode alone | Resolved | Tasks wall | Kaggle L4x4 on record |
   |---|---|---|---|---|---|
   | 31B | 210 s | 34.5 tok/s | 3/8 | 2,061 s | ~25.5 tok/s |
   | E4B | 192 s | 89.9 tok/s | 3/8 | 482 s | 104 to 117 tok/s |

6. Controls over all 129 tasks (`runs/C-000-gold-all`, `runs/C-000-empty-all`): the reference patch
   passes on 77, the empty patch passes on 5, so 72 tasks grade correctly here. The failures are
   test dependencies the image lacks or has at another version (fastapi: `inline_snapshot`,
   `dirty_equals`; requests: 10 of 13 fail; rich: 5 of 48; httpx: 1 of 1). The real scorer installs
   each task's pinned wheels in a Docker sandbox, which this cluster cannot run.

   | Cohort | Reference passes | Empty passes | Usable |
   |---|---|---|---|
   | smoke-8 | 5 | 1 | 4 |
   | dev-48 | 30 | 3 | 27 |
   | held-out-24 | 18 | 2 | 16 |
   | all 129 | 77 | 5 | 72 |

   Cluster cohorts: `cdev-56` (35 rich, 21 fastapi; the usable tasks outside held-out-24) and
   `cheld-16` (8 rich, 8 fastapi; locked). Limit: no requests or httpx task, and a rich-heavy mix,
   so a gain here is evidence for the Kaggle dev-48 confirmation, not a score estimate.

7. Shims (2026-11-18T17:10Z). 33 of the 52 reference failures were fastapi tests importing
   `inline_snapshot` or `dirty_equals`, which are not in `data/raw/wheels` (the harness already
   copies those wheels into each sandbox). `HENG_SHIMS=1` on `slurm/eval.sbatch` and
   `slurm/control.sbatch` binds the repo's stand-ins (`../tools/compat_shims/`) into the container;
   nothing is installed. Controls with shims (`runs/C-001-*`): reference passes 106, empty passes 5,
   usable 101 (was 72; none lost). New cohorts, all run with `HENG_SHIMS=1`: `cdevx-23` (the 23 new
   tuning tasks, all fastapi), `cdev2-79` (cdev-56 + cdevx-23), `cheld2-22` (locked). Runs on
   cdev-56 before this had no shims; a tree's cdev2-79 result is its cdev-56 draws plus cdevx-23
   draws, so nothing is rerun. Still failing: 10 requests, 5 rich, 7 fastapi, 1 httpx.

8. Task envs for agent runs (2026-11-19, `rounds/R-008-taskenv-base.md`). From R-008 on, every eval
   job appends `--py313 env/py313-scorer/bin/python3.13 --task-envs env/taskenvs` and leaves
   `HENG_SHIMS` off:
   - The agent's sandbox and grading both run Python 3.13 with each task's own declared test deps
     at the task date (C-003).
   - `tools/build_task_envs.py` `EXTRA_REQS` adds two fixes the declarations miss: `werkzeug<3`
     for requests_6592 (C-004), and setuptools (for `pkg_resources`) in 10 rich tasks.
   - Gradeable: 120/129.
   - Import errors in the agent's test runs went from about 1 in 5 E4B task-draws to 1 in 357.
   - The new E4B bases are screen-e4b-20 3.67 and cdev2-79 6.67. The 31B bases are screen-31b-20 8.5
     and cdev2-79 27.5 (cdev-56 19.5).
   - The OUT_OF_MEMORY flag on many jobs is the `rich_3480` grading run (an unfixed infinite loop) hitting
     the 64G limit; it is a normal fail of that task, not lost rows.
   - Runs before R-008 are not comparable to runs after it as a base.

9. pleiades-1-10 Turing lane (2026-11-19, `rounds/R-009-e4b-turing-lane.md`). E4B only (the 31B does not
   fit in 24 GB). Submit with `sbatch --constraint=QUADRORTX6000 -w pleiades-1-10 slurm/eval.sbatch ...`.
   - On that GPU `eval.sbatch` binds `/lib/firmware/nvidia` and the patched Triton attention op, and
     `cluster_eval.py` picks float16. Ada jobs are unchanged.
   - The patched op is built from the image, once, with
     `apptainer exec --containall --bind $PWD:$PWD --pwd $PWD env/harness.sif python3 -I tools/turing_patches/make_triton_attn_patch.py env/turing_patches/triton_unified_attention.py`.
   - Decoding is about 2x slower, so jobs add `--time-scale 2.0`. Turing draws are read only against the
     Turing base, never pooled with Ada.
   - The node was lent for one night. Ask before queuing there again.
