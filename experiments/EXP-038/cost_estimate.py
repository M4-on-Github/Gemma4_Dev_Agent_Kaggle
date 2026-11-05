#!/usr/bin/env python3
"""EXP-038 pre-registration cost estimate, computed from measured runs only (no new run).

Inputs (read as data; run with `python -I -X utf8`):
  - EXP-033 E4B smoke-8 kernel log      runs/EXP-033-e4b/gemma4-exp033-e4b.log
  - EXP-033 E4B smoke-8 summary         experiments/EXP-033/e4b/summary.jsonl
  - EXP-028 Arm R dev-48 kernel log     runs/EXP-028-armR/gemma4-exp028-armr.log
  - EXP-028 Arm R dev-48 summary        experiments/EXP-028/armR/summary.jsonl
  - smoke-8 cohort ids                  experiments/cohorts/smoke-8.txt

Output: experiments/EXP-038/cost_estimate.json, numbers only (no task text, no repo content).

Kernel hours here are log-span hours (last log entry time). The Kaggle quota figure runs a few minutes
higher (EXP-033 section 7: queueing and image start are not in the log).

Usage:
    python -I -X utf8 experiments/EXP-038/cost_estimate.py
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
E4B_LOG = ROOT / "runs/EXP-033-e4b/gemma4-exp033-e4b.log"
E4B_SUM = ROOT / "experiments/EXP-033/e4b/summary.jsonl"
R_LOG = ROOT / "runs/EXP-028-armR/gemma4-exp028-armr.log"
R_SUM = ROOT / "experiments/EXP-028/armR/summary.jsonl"
SMOKE8 = ROOT / "experiments/cohorts/smoke-8.txt"
OUT = ROOT / "experiments/EXP-038/cost_estimate.json"

N_TASKS = 48
TIME_CAP_S = 8 * 60          # eval_config max_time_minutes 8.0 (unchanged from Arm R)
CALL_CAP = 28                # eval_config max_tool_calls 28 (unchanged from Arm R)
HIDDEN_TASKS = 120


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_ids(p: Path) -> list[str]:
    return [s.strip() for s in p.read_text(encoding="utf-8").splitlines() if s.strip() and not s.startswith("#")]


def log_anchors(p: Path) -> dict:
    entries = json.loads(p.read_text(encoding="utf-8"))
    out = {"log_end_s": round(float(entries[-1]["time"]), 1)}
    for e in entries:
        m = re.search(r"vLLM up in ([0-9.]+)s", e.get("data", ""))
        if m:
            out["vllm_up_s"] = float(m.group(1))
            out["vllm_up_at_s"] = round(float(e["time"]), 1)
        m = re.search(r"'tok_s': ([0-9.]+)", e.get("data", ""))
        if m:
            out["decode_tok_s"] = float(m.group(1))
    return out


def h(seconds: float) -> float:
    return round(seconds / 3600.0, 3)


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return float("nan")
    tail = sum(math.comb(n, k) for k in range(0, min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def main() -> int:
    e4b = read_jsonl(E4B_SUM)
    r = read_jsonl(R_SUM)
    smoke = set(read_ids(SMOKE8))
    assert len(e4b) == 8 and {x["task_id"] for x in e4b} == smoke, "E4B summary is not the smoke-8 cohort"
    assert len(r) == N_TASKS, "Arm R summary is not 48 tasks"

    ea, ra = log_anchors(E4B_LOG), log_anchors(R_LOG)
    e_sum = sum(x["wall_s"] for x in e4b)
    r_sum = sum(x["wall_s"] for x in r)
    e_overhead = ea["log_end_s"] - e_sum
    r_overhead = ra["log_end_s"] - r_sum
    e_mean = e_sum / len(e4b)
    r_mean48 = r_sum / N_TASKS
    r_smoke = [x for x in r if x["task_id"] in smoke]
    r_mean8 = sum(x["wall_s"] for x in r_smoke) / len(r_smoke)
    composition = r_mean48 / r_mean8           # how much harder dev-48 is than smoke-8, in Arm R wall
    e_calls = sum(x["n_calls"] for x in e4b)
    e_turns = sum(x["n_turns"] for x in e4b)
    s_per_call = e_sum / e_calls
    s_per_turn = e_sum / e_turns

    # point A: smoke-8 mean as measured, applied to 48 tasks
    a_tasks = N_TASKS * e_mean
    # point B: the same mean scaled by Arm R's dev-48 / smoke-8 wall ratio (cohort composition)
    b_tasks = a_tasks * composition
    # scenario C: Arm R's capped tasks (either cap) cost the E4B its measured wall per counted call x 28;
    # the rest cost the smoke-8 mean.  A scenario, not a bound.
    r_capped = [x for x in r if x["calls_cap_hit"] or x["time_cap_hit"]]
    c_tasks = len(r_capped) * CALL_CAP * s_per_call + (N_TASKS - len(r_capped)) * e_mean
    # conditional worst case: every task at the 8-min cap plus grading, using the largest capped wall seen
    largest_capped_wall = max(x["wall_s"] for x in r_capped)
    worst_tasks = N_TASKS * largest_capped_wall

    def kernel(tasks_s: float) -> dict:
        return {"tasks_s": round(tasks_s, 1), "kernel_s": round(tasks_s + e_overhead, 1),
                "kernel_h": h(tasks_s + e_overhead)}

    mde = []
    for d in range(4, 13):
        need = next((b for b in range((d + 1) // 2, d + 1) if mcnemar_exact(b, d - b) < 0.05), None)
        mde.append({"discordant": d, "min_majority_for_p_lt_0.05": need,
                    "p_at_min": round(mcnemar_exact(need, d - need), 4) if need is not None else None})

    out = {
        "inputs": {"e4b_log": str(E4B_LOG.relative_to(ROOT)), "e4b_summary": str(E4B_SUM.relative_to(ROOT)),
                   "r_log": str(R_LOG.relative_to(ROOT)), "r_summary": str(R_SUM.relative_to(ROOT))},
        "e4b_smoke8": {"n": len(e4b), "log_end_s": ea["log_end_s"], "vllm_up_s": ea.get("vllm_up_s"),
                       "decode_tok_s": ea.get("decode_tok_s"), "task_wall_sum_s": round(e_sum, 1),
                       "task_wall_mean_s": round(e_mean, 1), "task_wall_max_s": max(x["wall_s"] for x in e4b),
                       "capped": sum(bool(x["calls_cap_hit"] or x["time_cap_hit"]) for x in e4b),
                       "overhead_s": round(e_overhead, 1), "counted_calls": e_calls, "turns": e_turns,
                       "s_per_counted_call": round(s_per_call, 2), "s_per_turn": round(s_per_turn, 2),
                       "resolved": sum(x["resolved"] for x in e4b)},
        "armR_dev48": {"n": N_TASKS, "log_end_s": ra["log_end_s"], "vllm_up_s": ra.get("vllm_up_s"),
                       "task_wall_sum_s": round(r_sum, 1), "task_wall_mean_s": round(r_mean48, 1),
                       "smoke8_ids_mean_s": round(r_mean8, 1), "composition_ratio": round(composition, 3),
                       "overhead_s": round(r_overhead, 1), "capped_either": len(r_capped),
                       "calls_cap_hit": sum(bool(x["calls_cap_hit"]) for x in r),
                       "time_cap_hit": sum(bool(x["time_cap_hit"]) for x in r),
                       "largest_capped_wall_s": largest_capped_wall,
                       "capped_on_smoke8_ids": sorted(x["task_id"] for x in r_capped if x["task_id"] in smoke),
                       "e4b_calls_on_those": {x["task_id"]: x["n_calls"] for x in e4b
                                              if x["task_id"] in {y["task_id"] for y in r_capped}},
                       "max_wall_s": max(x["wall_s"] for x in r),
                       "resolved": sum(x["resolved"] for x in r)},
        "estimate": {
            "A_unscaled_smoke8_mean": kernel(a_tasks),
            "B_scaled_by_armR_composition": kernel(b_tasks),
            "C_scenario_armR_capped_ids_at_28_calls": kernel(c_tasks),
            "worst_every_task_at_largest_capped_wall": kernel(worst_tasks),
            "per_task_at_cap_instead_of_smoke8_mean_h": h(largest_capped_wall - e_mean),
            "per_task_at_28_calls_instead_of_smoke8_mean_h": h(CALL_CAP * s_per_call - e_mean),
            "note": "log-span hours; worst case is conditional, not a hard bound (EXP-028 RH had one task at 751.9 s)",
        },
        "mcnemar_exact_two_sided_thresholds": mde,
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out["estimate"], indent=1))
    print(json.dumps({k: out["e4b_smoke8"][k] for k in ("overhead_s", "task_wall_mean_s", "task_wall_max_s", "capped", "s_per_counted_call")}))
    print(json.dumps({k: out["armR_dev48"][k] for k in ("overhead_s", "composition_ratio", "capped_either", "largest_capped_wall_s")}))
    print(json.dumps(mde))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
