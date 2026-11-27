#!/bin/bash
# Any tools/lora script on one GPU (L-010, 2026-11-27): sbatch -J heng_wsp slurm/lora_py.sbatch <run-id> <script.py> <args>
#   cd harness-eng
#   sbatch -J heng_lora --constraint=QUADRORTX6000 -w pleiades-1-10 --gpus=1 slurm/lora_train.sbatch <run-id> <train_lora.py args>
# The GPU type and count come from the command line. Data and adapters live under /data/mmyatmau/gemma4-lora
# (bound explicitly: --containall hides /data); the job log carries counts and losses only.
#SBATCH -p pleiades
#SBATCH --constraint=RTX6000ADA
#SBATCH --gpus=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --output=/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng/logs/%x_%j.out
#SBATCH --error=/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng/logs/%x_%j.out
set -euo pipefail

ROOT=/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng
REPO=$(dirname "$ROOT")
SIF="$ROOT/env/harness.sif"
DATA=/data/mmyatmau/gemma4-lora
RUN_ID=${1:?run id}; shift
SCRIPT=${1:?script under tools/lora}; shift
cd "$ROOT"
[ -f "$SIF" ] || { echo "$SIF missing"; exit 1; }

SCRATCH="/tmp/heng_${SLURM_JOB_ID}"
mkdir -p "$SCRATCH/tmp" "$SCRATCH/home"
START=$(date +%s)
finish() {
  echo "$RUN_ID,$SLURM_JOB_ID,$(hostname),$(( $(date +%s) - START ))" >> "$ROOT/logs/gpu_seconds.csv"
  rm -rf "$SCRATCH"
}
trap finish EXIT

FW=""
if nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | grep -q "Quadro RTX 6000"; then
  FW="--bind /lib/firmware/nvidia:/lib/firmware/nvidia:ro"   # GSP firmware, see eval.sbatch
fi
echo "[$(date -u +%FT%TZ)] job $SLURM_JOB_ID on $(hostname): run=$RUN_ID gpus=${CUDA_VISIBLE_DEVICES:-0}"
apptainer exec --nv --cleanenv --containall \
  --bind "$REPO:$REPO" --bind "$DATA:$DATA" --bind "$SCRATCH/tmp:/tmp" --home "$SCRATCH/home" --pwd "$ROOT" $FW \
  --env "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}" --env "PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True" \
  "$SIF" python3 -I -X utf8 "tools/lora/$SCRIPT" "$@"
echo "[$(date -u +%FT%TZ)] done in $(( $(date +%s) - START )) s"
