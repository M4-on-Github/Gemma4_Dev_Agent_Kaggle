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
# CPUs 2026-11-19 (R-011): 8 -> 4. The partition bills allocated CPUs (billing=8 for cpu=8), and sacct shows these
# jobs use about 2.1 cores on average (R-009 59475-59492: TotalCPU 6:23-6:41 over 3:02-3:12 elapsed; 31B 59441:
# 4:30 over 2:07). Memory stays 64G: MaxRSS reached 46-57 GB, memory is not billed, and rich_3480's grading run
# already hits 64G (README Setup results 8).
#SBATCH --cpus-per-task=4
# Memory 2026-11-22 (L-008): 64G -> 96G. L-008 l8 d1 (60877) reached 64.0 GB and the out-of-memory killer took the
# model server, 29 of 40 tasks unserved; the same as R-034's arm stalls. Control draws of the same period peaked
# at 56.7-59.6 GB, and one (60878) also logged an oom-kill. Memory is not billed; nodes have about 1 TB.
#SBATCH --mem=96G
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
# pleiades-1-10 (Quadro RTX 6000, open kernel module 580, apptainer 1.1.2, persistence mode off): the first open
# of a GPU makes the driver load its GSP firmware, looked up in the opening process's filesystem, so inside the
# container /dev/nvidia0 gives EIO and CUDA reports "unknown error" (999) until /lib/firmware/nvidia is visible.
# Bound only on that GPU type so the Ada jobs keep their exact setup. Run there with
#   sbatch --constraint=QUADRORTX6000 ... (the command line overrides the RTX6000ADA line above). 2026-11-19.
FW=""
if nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | grep -q "Quadro RTX 6000"; then
  FW="--bind /lib/firmware/nvidia:/lib/firmware/nvidia:ro"
  # Turing-safe Triton attention op (64 KB shared memory; see tools/turing_patches/make_triton_attn_patch.py).
  TP="$ROOT/env/turing_patches/triton_unified_attention.py"
  [ -f "$TP" ] || { echo "$TP missing: run tools/turing_patches/make_triton_attn_patch.py"; exit 1; }
  FW="$FW --bind $TP:/usr/local/lib/python3.12/dist-packages/vllm/v1/attention/ops/triton_unified_attention.py:ro"
fi
# R-056/R-057 2026-11-28: a card handed over by the scheduler can still be part-held by a process that outlived
# another job. Wait up to HENG_GPU_WAIT_MIN minutes (default 20) for it to clear, logging the holder's user name,
# then start anyway (the server refuses to start if the card is still held).
for i in $(seq 1 $(( ${HENG_GPU_WAIT_MIN:-20} * 2 ))); do
  USED=$(nvidia-smi -i "${CUDA_VISIBLE_DEVICES:-0}" --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1)
  [ "${USED:-0}" -lt 3000 ] && break
  WHO=$(for q in $(nvidia-smi -i "${CUDA_VISIBLE_DEVICES:-0}" --query-compute-apps=pid --format=csv,noheader 2>/dev/null); do ps -o user= -p "$q" 2>/dev/null; done | sort | uniq -c | tr '\n' ' ')
  echo "[gpu-wait $i] card holds ${USED} MiB before this job starts; holders: ${WHO:-not visible}"
  sleep 30
done
# If the card is still part-held, fit the server into what is left (never above 0.90) and say so in the log; below
# HENG_GPU_MIN (default 0.65, the 31B's need) stop at once instead of failing a minute into the start.
if [ "${USED:-0}" -ge 3000 ] && [ -z "${HENG_GPU_MEM:-}" ]; then
  TOT=$(nvidia-smi -i "${CUDA_VISIBLE_DEVICES:-0}" --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
  HENG_GPU_MEM=$(awk -v u="$USED" -v t="$TOT" 'BEGIN{s=(t-u-2000)/t; if(s>0.90)s=0.90; printf "%.2f", s}')
  echo "[gpu-shared] card holds ${USED} of ${TOT} MiB from another process; server memory share set to ${HENG_GPU_MEM}"
  if awk -v s="$HENG_GPU_MEM" -v m="${HENG_GPU_MIN:-0.65}" 'BEGIN{exit !(s<m)}'; then echo "[gpu-shared] below the minimum share, stopping"; exit 3; fi
fi
apptainer exec --nv --cleanenv --containall \
  --bind "$REPO:$REPO" --bind "$SCRATCH/tmp:/tmp" --home "$SCRATCH/home" --pwd "$ROOT" $SHIMS $FW \
  --env "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}" \
  --env "HENG_GPU_MEM=${HENG_GPU_MEM:-0.90}" \
  "$SIF" python3 -I -X utf8 tools/cluster_eval.py \
    --tree "$TREE" --cohort "$COHORT" --out "runs/$RUN_ID" \
    --data "$ROOT/data/raw" --models "$ROOT/models" "$@"
echo "[$(date -u +%FT%TZ)] done in $(( $(date +%s) - START )) s"
