#!/bin/bash
# harness-eng 2026-11-28: keeps the scheduler from handing an eval job a GPU that a process outside Slurm is using.
# Several free GPUs on the Ada nodes carry 13-34 GB of another user's processes (their Slurm jobs hold no GPU), and
# a model server started there fails at once (it needs 0.9 of the card). This job takes one GPU and looks at its
# memory: clean -> exits at once; in use -> sleeps on it (uses no GPU memory, touches no process) and re-checks every
# 5 min, exiting when the card is clean. Submit one per free GPU on a node, all at once.
#SBATCH -p pleiades
#SBATCH --gpus=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=08:00:00
#SBATCH -J heng_hold
#SBATCH --output=/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng/logs/%x_%j.out
while :; do
  u=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
  echo "$(date -u +%H:%M) used ${u} MiB"
  [ "${u:-0}" -lt 2000 ] && exit 0
  sleep 300
done
