#!/bin/bash
# Write harness-eng/inputs.sha256: one sha256 line per file under wheelhouse/, data/raw/ and models/.
# The manifest is tracked in git; the files are not. It lets anyone who fetched the inputs with
# tools/fetch_inputs.sh check they have the same bytes this loop ran on.
#
# Usage: bash harness-eng/tools/hash_inputs.sh            write the manifest
#        bash harness-eng/tools/hash_inputs.sh --check    compare the folders with the manifest
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ "${1:-}" == "--check" ]]; then
  sha256sum --check --quiet inputs.sha256 && echo "inputs match inputs.sha256"
  exit
fi

find wheelhouse data/raw models -type f -print0 | LC_ALL=C sort -z | xargs -0 -r sha256sum > inputs.sha256
echo "$(wc -l < inputs.sha256) files hashed into $ROOT/inputs.sha256"
