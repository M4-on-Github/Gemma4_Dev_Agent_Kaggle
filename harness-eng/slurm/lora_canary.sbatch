#!/bin/bash
# LoRA serving canary (R-013, 2026-11-20): one vLLM boot per adapters root, no task run.
#   cd harness-eng
#   sbatch -J heng_31b slurm/lora_canary.sbatch <run-id> <model name> <adapters root> [<adapters root> ...]
# Each root holds adapters/<name>/ and gets its own boot, so --max-loras and --max-lora-rank are what the harness
# derives for that set. Results go to runs/<run-id>/<root basename>.json. The container setup is eval.sbatch's.
#SBATCH -p pleiades
#SBATCH --constraint=RTX6000ADA
#SBATCH --gpus=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng/logs/%x_%j.out
#SBATCH --error=/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng/logs/%x_%j.out
set -euo pipefail

ROOT=/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng
REPO=$(dirname "$ROOT")
SIF="$ROOT/env/harness.sif"
RUN_ID=${1:?run id}; MODEL=${2:?model name}; shift 2
[ $# -ge 1 ] || { echo "need at least one adapters root"; exit 1; }
cd "$ROOT"
[ -f "$SIF" ] || { echo "$SIF missing"; exit 1; }
[ ! -e "runs/$RUN_ID" ] || { echo "runs/$RUN_ID already exists"; exit 1; }
mkdir -p "runs/$RUN_ID"

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
  FW="--bind /lib/firmware/nvidia:/lib/firmware/nvidia:ro"
  TP="$ROOT/env/turing_patches/triton_unified_attention.py"
  [ -f "$TP" ] || { echo "$TP missing"; exit 1; }
  FW="$FW --bind $TP:/usr/local/lib/python3.12/dist-packages/vllm/v1/attention/ops/triton_unified_attention.py:ro"
fi
echo "[$(date -u +%FT%TZ)] job $SLURM_JOB_ID on $(hostname): run=$RUN_ID model=$MODEL roots=$*"
for R in "$@"; do
  apptainer exec --nv --cleanenv --containall \
    --bind "$REPO:$REPO" --bind "$SCRATCH/tmp:/tmp" --home "$SCRATCH/home" --pwd "$ROOT" $FW \
    --env "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}" \
    "$SIF" python3 -I -X utf8 tools/lora_canary.py \
      --model-dir "$ROOT/models/$MODEL" --adapters-root "$R" --out "runs/$RUN_ID/$(basename "$R").json"
done
echo "[$(date -u +%FT%TZ)] done in $(( $(date +%s) - START )) s"
