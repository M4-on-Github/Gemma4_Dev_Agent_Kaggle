#!/bin/bash
# Build env/harness.sif from slurm/harness.def. CPU only; needs network for the dependency installs.
#   cd harness-eng && sbatch slurm/build_env.sbatch
# Skips the build when the definition, the install script and the wheelhouse are unchanged.
#SBATCH -p pleiades
#SBATCH -J heng_build
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=2:00:00
#SBATCH --output=/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng/logs/%x_%j.out
#SBATCH --error=/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng/logs/%x_%j.out
set -euo pipefail

ROOT=/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng
BASE_SRC=/data/mmyatmau/gemma4_judge.sif       # the user's existing image; read once, never written
BASE="$ROOT/env/base/gemma4_judge.sif"         # the copy the build uses
SIF="$ROOT/env/harness.sif"
cd "$ROOT"
mkdir -p env/base
[ -f "$BASE" ] || cp --reflink=auto "$BASE_SRC" "$BASE"

n_wheels=$(find wheelhouse -name '*.whl' | wc -l)
[ "$n_wheels" -gt 0 ] || { echo "wheelhouse/ holds no wheels; upload it first"; exit 1; }

# The image is a function of these three things.
KEY=$( { sha256sum slurm/harness.def tools/install_wheelhouse.py
         find wheelhouse -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum; } | sha256sum | cut -d' ' -f1)
if [ -f "$SIF" ] && [ "$(cat "$SIF.key.sha256" 2>/dev/null)" = "$KEY" ]; then
  echo "[$(date)] $SIF is up to date ($KEY)"; exit 0
fi

export APPTAINER_TMPDIR="$ROOT/env/tmp" APPTAINER_CACHEDIR="$ROOT/env/cache"
mkdir -p "$APPTAINER_TMPDIR" "$APPTAINER_CACHEDIR"

echo "[$(date)] building $SIF from $n_wheels wheels on $(hostname)"
apptainer build --force --fakeroot --bind "$ROOT/wheelhouse:/wheelhouse" "$SIF" slurm/harness.def
echo "$KEY" > "$SIF.key.sha256"
sha256sum "$BASE" | cut -d' ' -f1 > "$SIF.base.sha256"
apptainer exec "$SIF" cat /usr/local/share/harness_install_report.json > "$ROOT/env/install_report.json"
apptainer exec "$SIF" cat /usr/local/share/harness.lock.txt > "$ROOT/slurm/harness.lock.txt"
rm -rf "$APPTAINER_TMPDIR"
echo "[$(date)] done: $(du -sh "$SIF" | cut -f1); report in env/install_report.json"
