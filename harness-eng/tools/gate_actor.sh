#!/bin/bash
# Wait for one gating job, apply its pre-registered gates with tools/d1_gate.py, then act (2026-11-21, weekend
# queueing rule: gated draws are queued up front and cancelled unread when a gate fails).
#   bash tools/gate_actor.sh <job id> <run dir> <expected rows> <jobs to cancel on KILL> <jobs to release on PASS|-> GATE...
# Job lists are comma-separated. INCOMPLETE (exit 2) or a failed job takes no action and is reported for a person.
set -u
cd "$(dirname "$0")/.."
JOB=$1 RUN=$2 N=$3 KILL=$4 REL=$5; shift 5
until [ -z "$(squeue -h -j "$JOB" 2>/dev/null)" ]; do sleep 300; done
sacct -j "$JOB" -X -n -o JobID,State,Elapsed,NodeList
python3 -I tools/d1_gate.py "$RUN" "$N" "$@"; rc=$?
case $rc in
  0) [ "$REL" != "-" ] && scontrol release "$REL" && echo "released $REL"; echo "ACTION pass" ;;
  1) scancel ${KILL//,/ } && echo "cancelled $KILL"; echo "ACTION kill" ;;
  *) echo "ACTION none (rc $rc): read by hand" ;;
esac
