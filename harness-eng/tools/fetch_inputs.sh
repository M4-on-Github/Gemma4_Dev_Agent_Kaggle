#!/bin/bash
# Fetch every untracked input of harness-eng/ from Kaggle, and record where each one comes from.
#
# Needs only curl, unzip and tar: it calls the Kaggle REST API with the token in the repo's .env
# (KAGGLE_API_TOKEN=...; the file is git-ignored). The account must have accepted the competition
# rules. No Kaggle CLI is installed or used.
#
# Usage: bash harness-eng/tools/fetch_inputs.sh [competition] [wheelhouse] [31b] [e4b] [parent-e4b] [parent-31b]
#   no arguments = competition wheelhouse 31b e4b (what the eval loop needs)
# Each archive's sha256 and size are appended to inputs.archives.tsv (tracked) before it is unpacked
# and deleted. Afterwards run tools/hash_inputs.sh for the per-file manifest.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API="https://www.kaggle.com/api/v1"

# --- sources -------------------------------------------------------------------------------------
COMP="gemma-4-developer-agent"                                # tasks, snapshots, graphs, embeddings, wheels, HARNESS_README.md
WHEELHOUSE_DS="metric/gemma-4-developer-agent-wheelhouse"      # swegemma, adk_submission, patched vLLM 0.19.1, torch
MODEL_31B="google/gemma-4/other/gemma-4-31b-it-qat-w4a16-ct/2" # served 31B, the scorer's checkpoint
MODEL_E4B="google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2" # served E4B
# LoRA parents (Apache-2.0), fetched only when named. The E4B handle is recorded in the repo's
# harness-stack skill (reference/small-variants.md). The 31B handle follows the same pattern and is
# NOT yet verified; its Hugging Face name is google/gemma-4-31B-it-qat-q4_0-unquantized.
PARENT_E4B="google/gemma-4/transformers/gemma-4-e4b-it-qat-q4_0-unquantized/2"
PARENT_31B="google/gemma-4/transformers/gemma-4-31b-it-qat-q4_0-unquantized/2"

# --- helpers -------------------------------------------------------------------------------------
set -a; . "$ROOT/../.env"; set +a
: "${KAGGLE_API_TOKEN:?KAGGLE_API_TOKEN missing from $ROOT/../.env}"

download() {   # url, output file. The token goes through stdin, never the command line.
  printf 'header = "Authorization: Bearer %s"\n' "$KAGGLE_API_TOKEN" |
    curl -K - -fSL --retry 5 --retry-delay 10 -C - -o "$2" "$1"
}
record() {     # name, source handle, archive
  printf '%s\t%s\t%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "$1" "$2" "$(stat -c %s "$3")" "$(sha256sum "$3" | cut -d' ' -f1)" \
    >> "$ROOT/inputs.archives.tsv"
}
fetch_zip() {  # name, source handle, url, target dir
  mkdir -p "$4"; local f="$4/.download.zip"
  echo "[$(date -u +%T)] $1: downloading $2"
  download "$3" "$f"; record "$1" "$2" "$f"
  unzip -q -o "$f" -d "$4"; rm -f "$f"
  echo "[$(date -u +%T)] $1: $(find "$4" -type f | wc -l) files, $(du -sh "$4" | cut -f1)"
}
fetch_model() {  # name, handle, target folder name
  local d="$ROOT/models/$3" f="$ROOT/models/.$3.tar.gz"
  mkdir -p "$d"
  echo "[$(date -u +%T)] $1: downloading $2"
  download "$API/models/$2/download" "$f"; record "$1" "$2" "$f"
  tar -xf "$f" -C "$d"; rm -f "$f"
  echo "[$(date -u +%T)] $1: $(find "$d" -type f | wc -l) files, $(du -sh "$d" | cut -f1)"
}

# --- fetch ---------------------------------------------------------------------------------------
[ $# -gt 0 ] || set -- competition wheelhouse 31b e4b
for what in "$@"; do
  case "$what" in
    competition) fetch_zip competition "$COMP" "$API/competitions/data/download-all/$COMP" "$ROOT/data/raw" ;;
    wheelhouse)  fetch_zip wheelhouse "$WHEELHOUSE_DS" "$API/datasets/download/$WHEELHOUSE_DS" "$ROOT/wheelhouse" ;;
    31b)         fetch_model 31b "$MODEL_31B" gemma-4-31b-it-qat-w4a16-ct ;;
    e4b)         fetch_model e4b "$MODEL_E4B" gemma-4-e4b-it-qat-w4a16-ct ;;
    parent-e4b)  fetch_model parent-e4b "$PARENT_E4B" gemma-4-e4b-it-qat-q4_0-unquantized ;;
    parent-31b)  fetch_model parent-31b "$PARENT_31B" gemma-4-31b-it-qat-q4_0-unquantized ;;
    *) echo "unknown input: $what"; exit 2 ;;
  esac
done

# runs/ is not fetched here: past runs are the outputs of our own Kaggle kernels.
echo "Done. Now run: bash harness-eng/tools/hash_inputs.sh"
