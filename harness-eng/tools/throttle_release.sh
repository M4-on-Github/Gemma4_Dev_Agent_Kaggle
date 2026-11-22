#!/bin/bash
# Release held jobs one at a time so that at most MAX of my GPU jobs run at once (user rule 2026-11-22: no more than
# 2 running on the biggest GPUs unless the user says otherwise; queueing is fine).
#   bash tools/throttle_release.sh <max running> <job,job,...>
set -u
MAX=$1; IFS=, read -ra JOBS <<< "$2"
running() { squeue -u "$USER" -h -t R -o "%j" | grep -c '^heng_'; }
for j in "${JOBS[@]}"; do
  [ -z "$(squeue -h -j "$j" 2>/dev/null)" ] && { echo "skip $j (gone)"; continue; }
  until [ "$(running)" -lt "$MAX" ]; do sleep 60; done
  scontrol release "$j" && echo "released $j $(date +%H:%M)"
  until [ -n "$(squeue -h -j "$j" -t R,CD,CA,F 2>/dev/null)" ] || [ -z "$(squeue -h -j "$j" 2>/dev/null)" ]; do sleep 30; done
done
echo "throttle done"
