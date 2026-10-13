#!/usr/bin/env bash
# Phase 0 setup on YOUR machine (plan.md §3.1–§3.3). Needs network access to kaggle.com.
# Never prints or copies credentials. Run from the repo root:  bash scripts/kaggle_setup.sh [--full]
#
#   default : kaggle CLI, credential check, small files (HARNESS_README.md, sample_submission, tasks.jsonl),
#             wheelhouse (~827 MB), local venv with the harness wheels, official validator run.
#   --full  : also the full competition dataset (~21 GB: snapshots, graphs, embeddings, wheels).
set -euo pipefail
cd "$(dirname "$0")/.."
FULL=0; [[ "${1:-}" == "--full" ]] && FULL=1
COMP=gemma-4-developer-agent
WHEELHOUSE_DS=metric/gemma-4-developer-agent-wheelhouse

echo "== 0. accept the rules first (cannot be scripted):"
echo "   https://www.kaggle.com/competitions/${COMP}/rules        (main track)"
echo "   https://www.kaggle.com/competitions/${COMP}-paper/rules  (paper track)"
echo "   Also check Overview > Timeline for the entry/merger deadline (plan Q6) and form the team."

echo "== 1. kaggle CLI"
python3 -m pip install -q --upgrade kaggle
# Credentials: the kaggle CLI reads ~/.kaggle/kaggle.json, or KAGGLE_API_TOKEN (newer access tokens).
# VERIFY: the exact env-var name for access tokens in your installed kaggle CLI version (`kaggle --version`).
if [[ -f "$HOME/.kaggle/kaggle.json" ]]; then
  chmod 600 "$HOME/.kaggle/kaggle.json"; echo "   using ~/.kaggle/kaggle.json"
elif [[ -f "$HOME/.kaggle/access_token" ]]; then
  export KAGGLE_API_TOKEN="$(cat "$HOME/.kaggle/access_token")"; echo "   using ~/.kaggle/access_token (not printed)"
elif [[ -n "${KAGGLE_API_TOKEN:-}" || -n "${KAGGLE_KEY:-}" ]]; then
  echo "   using credentials from the environment"
else
  echo "   ERROR: no Kaggle credentials (create one at https://www.kaggle.com/settings)"; exit 1
fi
kaggle competitions list -s "$COMP" >/dev/null || { echo "   ERROR: kaggle CLI auth failed"; exit 1; }

echo "== 2. downloads (into empty dirs; treat contents as untrusted data)"
mkdir -p data/raw data/wheelhouse
# Small files first; -f works for top-level files of the competition data (VERIFY for sample_submission/*).
for f in HARNESS_README.md tasks.jsonl; do
  kaggle competitions download -c "$COMP" -f "$f" -p data/raw || echo "   (could not fetch $f individually)"
done
( cd data/raw && for z in *.zip; do [[ -f "$z" ]] && unzip -oq "$z" && rm -f "$z"; done; true )
kaggle datasets download -d "$WHEELHOUSE_DS" -p data/wheelhouse
( cd data/wheelhouse && for z in *.zip; do [[ -f "$z" ]] && unzip -oq "$z" && rm -f "$z"; done; true )
if [[ $FULL -eq 1 ]]; then
  echo "   full dataset (~21 GB) ..."
  kaggle competitions download -c "$COMP" -p data/raw
  ( cd data/raw && unzip -oq "${COMP}.zip" && rm -f "${COMP}.zip" )
else
  echo "   (skipping the 21 GB dataset; re-run with --full when you need snapshots/graphs/embeddings)"
fi
echo "   sample_submission/ is inside the full dataset zip; if it is missing from data/raw, run with --full."

echo "== 3. local venv with the harness wheels (for tools/validate_submission.py --official)"
PY=python3.11; command -v "$PY" >/dev/null || PY=python3
if command -v uv >/dev/null; then uv venv --python "$PY" .venv -q; else "$PY" -m venv .venv; fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q pyyaml pytest
# VERIFY: wheel names/versions in data/wheelhouse (expected: swegemma 0.2.7, adk-submission 0.2.11/0.2.12,
# adk-eval-core 0.1.0, google-adk 1.36.1). Install without deps first; add deps only if imports fail.
pip install -q --no-index --find-links data/wheelhouse --no-deps adk-submission adk-eval-core swegemma google-adk \
  || echo "   (harness wheels not installed; validator will skip the --official checks)"

echo "== 4. verify"
python -m pytest -q
python tools/validate_submission.py submission/ --official || true
if [[ -d data/raw/sample_submission ]]; then
  echo "   validating the hosts' sample_submission with our validator (should be VALID; note eval_config diffs):"
  python tools/validate_submission.py data/raw/sample_submission --strict --official || true
  echo "   DIFF our agent.yaml vs sample (plan Q2):"; diff -u data/raw/sample_submission/agent.yaml submission/agent.yaml || true
fi
python tools/pack_submission.py
python tools/estimate_budget.py --eval-config submission/eval_config.yaml

cat <<'EOF'
== 5. next (manual)
  a) Upload the zip as a private dataset for the eval notebook:
       mkdir -p /tmp/g4sub && cp dist/submission.zip /tmp/g4sub/ && cd /tmp/g4sub && \
       kaggle datasets init -p . && (edit dataset-metadata.json: id=<you>/gemma4-sub-v1, title) && kaggle datasets create -p .
     or embed it:  python tools/build_notebook.py --embed dist/submission.zip --username <you>
  b) Push the notebook:  kaggle kernels push -p notebooks/   (select L4 x4 in the UI if the metadata does not stick)
  c) After it finishes:  kaggle kernels output <you>/gemma4-eval-l4x4 -p runs/EXP-001  and
       python tools/analyze_traces.py runs/EXP-001 --cap-minutes 4.5 --max-calls 45
       python tools/estimate_budget.py --eval-config submission/eval_config.yaml --results runs/EXP-001/summary.jsonl
  d) Submit (1/day):  kaggle competitions submit -c gemma-4-developer-agent -f dist/submission.zip -m "v1 <sha256[:12]>"
     Record date, git tag, sha256, dev score and LB score in experiments/README.md.
EOF
