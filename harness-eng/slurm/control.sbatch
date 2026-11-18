#!/bin/bash
# Gold or empty-patch control: no model, no GPU. Grades each task's reference patch (or nothing)
# in the same image and sandbox the eval jobs use, to learn which tasks this environment can grade.
#   cd harness-eng && sbatch slurm/control.sbatch <run-id> <gold|empty> <cohort file> [concurrency]
# Teacher patches (teacher/DESIGN.md), graded by the same path; results go to teacher/graded/<run-id>:
#   sbatch slurm/control.sbatch <run-id> patchdir <cohort file> <concurrency> <dir holding <task id>/patch.diff>
#SBATCH -p pleiades
#SBATCH -J heng_control
#SBATCH --cpus-per-task=16
#SBATCH --mem=48G
#SBATCH --time=6:00:00
#SBATCH --output=/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng/logs/%x_%j.out
#SBATCH --error=/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng/logs/%x_%j.out
set -euo pipefail
ROOT=/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng
REPO=$(dirname "$ROOT")
RUN_ID=${1:?run id}; MODE=${2:?gold, empty or patchdir}; COHORT=${3:?cohort file}; CONC=${4:-6}
OUT="runs/$RUN_ID"; PATCHARGS=()
if [ "$MODE" = patchdir ]; then OUT="teacher/graded/$RUN_ID"; PATCHARGS=(--patch-dir "${5:?patch dir}"); fi
cd "$ROOT"
SCRATCH="/tmp/heng_${SLURM_JOB_ID}"; mkdir -p "$SCRATCH/tmp" "$SCRATCH/home"; trap 'rm -rf "$SCRATCH"' EXIT
echo "[$(date -u +%FT%TZ)] job $SLURM_JOB_ID on $(hostname): control=$MODE run=$RUN_ID cohort=$COHORT"
# HENG_SHIMS=1 (sbatch --export=ALL,HENG_SHIMS=1) makes the repo's stand-ins for two test-only
# packages (tools/compat_shims: inline_snapshot, dirty_equals) importable in the sandbox by binding
# them into the image's dist-packages. Nothing is installed. Off by default so earlier runs stay comparable.
# HENG_EVAL_ARGS (e.g. "--py313 env/py313-scorer/bin/python3.13 --extras env/py313-extras") is passed
# to cluster_eval.py as is: tests then run in the copy of the scorer's Python (tools/scorer_env.py).
SHIMS=""
if [ "${HENG_SHIMS:-0}" = "1" ]; then
  for m in inline_snapshot dirty_equals; do
    SHIMS="$SHIMS --bind $REPO/tools/compat_shims/$m:/usr/local/lib/python3.12/dist-packages/$m"
  done
fi
apptainer exec --cleanenv --containall \
  --bind "$REPO:$REPO" --bind "$SCRATCH/tmp:/tmp" --home "$SCRATCH/home" --pwd "$ROOT" $SHIMS \
  "$ROOT/env/harness.sif" python3 -I -X utf8 tools/cluster_eval.py \
    --tree trees/31b-base --cohort "$COHORT" --out "$OUT" --control "$MODE" --concurrency "$CONC" \
    --data "$ROOT/data/raw" --models "$ROOT/models" "${PATCHARGS[@]+"${PATCHARGS[@]}"}" ${HENG_EVAL_ARGS:-}
