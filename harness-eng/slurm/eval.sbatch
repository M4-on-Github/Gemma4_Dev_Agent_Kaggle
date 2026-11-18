#!/bin/bash
# One draw of one agent tree on one cohort, on one RTX 6000 Ada.
#   cd harness-eng
#   sbatch -J heng_31b slurm/eval.sbatch <run-id> <tree dir or zip> <cohort file> [extra cluster_eval.py args]
# Example:
#   sbatch -J heng_31b slurm/eval.sbatch R-001-31b-base-d1 trees/31b-base ../experiments/cohorts/smoke-8.txt
# Results go to runs/<run-id>/. The loop holds at most two of these jobs at once: one 31B, one E4B.
#SBATCH -p pleiades
#SBATCH --constraint=RTX6000ADA
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng/logs/%x_%j.out
#SBATCH --error=/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng/logs/%x_%j.out
set -euo pipefail

ROOT=/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng
REPO=$(dirname "$ROOT")
SIF="$ROOT/env/harness.sif"
RUN_ID=${1:?run id}; TREE=${2:?tree dir or zip}; COHORT=${3:?cohort file}; shift 3
cd "$ROOT"

[ -f "$SIF" ] || { echo "$SIF missing: run slurm/build_env.sbatch first"; exit 1; }
[ ! -e "runs/$RUN_ID/task_results.jsonl" ] || { echo "runs/$RUN_ID already holds a run"; exit 1; }

# Throwaway scratch on the node's local disk: the sandbox's per-task workspaces and vLLM's caches.
# It is deleted when the job ends. It is not on the NFS home because every agent command and test run
# happens there, inside the task's time cap, and NFS latency would be charged to the agent.
# Everything that is kept (results, traces, patches, logs) is written under harness-eng/runs/.
SCRATCH="/tmp/heng_${SLURM_JOB_ID}"
mkdir -p "$SCRATCH/tmp" "$SCRATCH/home"
START=$(date +%s)
finish() {   # one line per job for the GPU ledger, failed jobs included
  echo "$RUN_ID,$SLURM_JOB_ID,$(hostname),$(( $(date +%s) - START ))" >> "$ROOT/logs/gpu_seconds.csv"
  rm -rf "$SCRATCH"
}
trap finish EXIT

echo "[$(date -u +%FT%TZ)] job $SLURM_JOB_ID on $(hostname): run=$RUN_ID tree=$TREE cohort=$COHORT $*"
# HENG_SHIMS=1 (sbatch --export=ALL,HENG_SHIMS=1) makes the repo's stand-ins for two test-only
# packages (tools/compat_shims: inline_snapshot, dirty_equals) importable in the sandbox by binding
# them into the image's dist-packages. Nothing is installed. Off by default so earlier runs stay comparable.
SHIMS=""
if [ "${HENG_SHIMS:-0}" = "1" ]; then
  for m in inline_snapshot dirty_equals; do
    SHIMS="$SHIMS --bind $REPO/tools/compat_shims/$m:/usr/local/lib/python3.12/dist-packages/$m"
  done
fi
apptainer exec --nv --cleanenv --containall \
  --bind "$REPO:$REPO" --bind "$SCRATCH/tmp:/tmp" --home "$SCRATCH/home" --pwd "$ROOT" $SHIMS \
  --env "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}" \
  "$SIF" python3 -I -X utf8 tools/cluster_eval.py \
    --tree "$TREE" --cohort "$COHORT" --out "runs/$RUN_ID" \
    --data "$ROOT/data/raw" --models "$ROOT/models" "$@"
echo "[$(date -u +%FT%TZ)] done in $(( $(date +%s) - START )) s"
