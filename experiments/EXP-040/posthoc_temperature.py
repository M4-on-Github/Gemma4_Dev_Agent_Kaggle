#!/usr/bin/env python3
"""EXP-040 post-hoc look, not pre-registered, no reading applied (section 9.9).

The user asked what the vote would give with every voter at 0.7 or above. This recomputes, from pass 1 of each
trace (segmented by analyze_results.extract_rounds_contiguous, scored by tally.score_round):
  - the 16 picks in voter order (letters only; "-" for a vote that does not parse);
  - per temperature bucket (tally.temperature_bucket: voters 1-6 at 0.20-0.60, 7-11 at 0.68-1.00, 12-16 at
    1.08-1.40), votes against the tally winner, over the tasks with C >= 2 and over all 8;
  - per task, the fraction of the 16 voters whose pick differs from the winner, and its sum over the 8 tasks:
    the expected number of tasks with D true if voter 1 were one of the 16 chosen at random (the 16 votes are
    held fixed, so the winner does not change when a unique plurality exists).

Run: python -I -X utf8 experiments/EXP-040/posthoc_temperature.py
Output: experiments/EXP-040/posthoc_temperature.json (task ids, letters, voter indices, temperatures, counts).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("analyze_results", ROOT / "experiments/EXP-040/analyze_results.py")
AR = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(AR)
T = AR.T
OUT = ROOT / "experiments/EXP-040/posthoc_temperature.json"


def main() -> None:
    ids = AR.ids_of(AR.SMOKE8)
    buckets = {b: {"voters": [k for k in range(1, T.N_VOTERS + 1) if T.temperature_bucket(k) == b]} for b in T.BUCKETS}
    for b in buckets.values():
        b["temperatures"] = [T.voter_temperature(k) for k in b["voters"]]
        b["against_winner_c_ge_2"] = 0
        b["n_c_ge_2"] = 0
        b["against_winner_all"] = 0
        b["n_all"] = 0
        b["unparsed_all"] = 0
    per_task = {}
    for tid in ids:
        trace = json.loads((AR.RUN / "traces" / f"trace_{tid}.json").read_text(encoding="utf-8"))
        s = T.score_round(AR.extract_rounds_contiguous(trace)[0])
        votes, w = s["votes"], s["winner"]
        against = [k for k, v in enumerate(votes, 1) if v != w]
        for b in buckets.values():
            in_b = [k for k in b["voters"]]
            n_against = sum(1 for k in in_b if k in against)
            b["against_winner_all"] += n_against
            b["n_all"] += len(in_b)
            b["unparsed_all"] += sum(1 for k in in_b if votes[k - 1] is None)
            if s["C"] >= 2:
                b["against_winner_c_ge_2"] += n_against
                b["n_c_ge_2"] += len(in_b)
        per_task[tid] = {
            "C": s["C"],
            "picks": "".join(v if v is not None else "-" for v in votes),
            "winner": w,
            "rule": s["rule"],
            "P1": s["P1"],
            "against_winner_voters": against,
            "frac_differs_from_winner": round(len(against) / T.N_VOTERS, 4),
        }
    expected_d = sum(len(p["against_winner_voters"]) for p in per_task.values()) / T.N_VOTERS
    out = {
        "label": "post-hoc, not pre-registered, no reading applied; pass 1, contiguous segmentation",
        "per_task": per_task,
        "buckets": buckets,
        "against_winner_total_c_ge_2": sum(b["against_winner_c_ge_2"] for b in buckets.values()),
        "p1_equals_winner": sum(1 for p in per_task.values() if p["P1"] == p["winner"]),
        "expected_tasks_d_true_random_voter1": round(expected_d, 4),
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
