#!/usr/bin/env python3
"""Project the 12 h scorer budget from a cohort run and gate packing (plan.md §4.4, §5.3).

Two modes:
  * cap-only (no results): worst case = N_hidden x (max_time_minutes + setup) from eval_config.yaml.
  * with results: per-task estimate = max(measured wall, decode-model estimate), capped at max_time_minutes,
    where the decode model is per_call_s x n_calls + output_tokens / tok_s (idea from gemma4-swe-kit's
    scorer-time tool, Apache-2.0, re-implemented here). Reports p50 / mean / p90 / worst-case projections.

Accepted result rows (JSON lines; keys are optional except an id):
  task_id|instance_id|id, wall_s|duration_s|duration_seconds, setup_s, n_calls|tool_calls, output_tokens,
  resolved, time_cap_hit.
That covers tools/analyze_traces.py summary.jsonl and the Kaggle notebook's task_results.jsonl.

Gate: exit 1 (BLOCK) if the worst case exceeds --gate hours (default 11.0). Run before every pack.

Usage:
    python tools/estimate_budget.py --eval-config submission/eval_config.yaml
    python tools/estimate_budget.py --eval-config submission/eval_config.yaml --results runs/EXP-001/summary.jsonl
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import submission_rules as R  # noqa: E402


def load_eval_config(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    ev = data.get("evaluation", data) if isinstance(data, dict) else {}
    return ev if isinstance(ev, dict) else {}


def load_rows(paths: list[Path]) -> list[dict]:
    rows = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def _first(row: dict, *keys: str, default=None):
    for k in keys:
        if row.get(k) is not None:
            return row[k]
    return default


def per_task_estimate(row: dict, *, cap_s: float | None, tok_s: float, per_call_s: float) -> dict:
    wall = float(_first(row, "wall_s", "duration_s", "duration_seconds", default=0.0))
    n_calls = int(_first(row, "n_calls", "tool_calls", "llm_calls", default=0) or 0)
    tokens = int(_first(row, "output_tokens", "completion_tokens", default=0) or 0)
    decode = per_call_s * n_calls + tokens / tok_s if (n_calls or tokens) else 0.0
    est = max(wall, decode)
    capped = False
    if cap_s is not None and est > cap_s:
        est, capped = cap_s, True
    return {"task_id": _first(row, "task_id", "instance_id", "id", default="?"), "wall_s": wall,
            "decode_est_s": decode, "est_s": est, "capped": capped, "setup_s": float(row.get("setup_s") or 0.0),
            "resolved": bool(row.get("resolved"))}


def project(estimates: list[dict], *, n_tasks: int, setup_min: float, cap_min: float | None,
            server_start_min: float) -> dict:
    ests = [e["est_s"] for e in estimates]
    measured_setup = [e["setup_s"] for e in estimates if e["setup_s"] > 0]
    setup_s = st.mean(measured_setup) if measured_setup else setup_min * 60
    def hours(per_task_s: float) -> float:
        return n_tasks * (per_task_s + setup_s) / 3600
    out = {
        "n_measured": len(ests),
        "setup_s_used": setup_s,
        "setup_source": "measured" if measured_setup else "assumed",
        "p50_task_s": st.median(ests) if ests else None,
        "mean_task_s": st.mean(ests) if ests else None,
        "p90_task_s": (sorted(ests)[max(0, int(round(0.9 * len(ests))) - 1)] if ests else None),
        "proj_p50_h": hours(st.median(ests)) if ests else None,
        "proj_mean_h": hours(st.mean(ests)) if ests else None,
        "proj_p90_h": None,
        "worst_case_h": hours(cap_min * 60) if cap_min is not None else None,
        "worst_case_all_in_h": (hours(cap_min * 60) + server_start_min / 60) if cap_min is not None else None,
        "resolved": sum(e["resolved"] for e in estimates),
        "cap_hits": sum(e["capped"] for e in estimates),
    }
    if ests:
        out["proj_p90_h"] = hours(out["p90_task_s"])
    return out


def render(p: dict, *, gate: float, limit: float, cap_min: float | None) -> str:
    lines = []
    if p["n_measured"]:
        lines.append(f"measured tasks: {p['n_measured']} (resolved {p['resolved']}, cap hits {p['cap_hits']})")
        lines.append(f"per-task est: p50 {p['p50_task_s']/60:.2f} min, mean {p['mean_task_s']/60:.2f} min, "
                     f"p90 {p['p90_task_s']/60:.2f} min; setup {p['setup_s_used']:.0f} s ({p['setup_source']})")
        lines.append(f"projected hidden run: p50 {p['proj_p50_h']:.2f} h, mean {p['proj_mean_h']:.2f} h, "
                     f"p90 {p['proj_p90_h']:.2f} h")
    if cap_min is None:
        lines.append("WORST CASE: unbounded (no max_time_minutes) -> BLOCK")
    else:
        lines.append(f"worst case (every task hits the {cap_min} min cap): {p['worst_case_h']:.2f} h "
                     f"(+ server start: {p['worst_case_all_in_h']:.2f} h); gate {gate} h, limit {limit} h")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--eval-config", type=Path, help="submission/eval_config.yaml (for max_time_minutes)")
    ap.add_argument("--cap-minutes", type=float, help="override max_time_minutes")
    ap.add_argument("--results", nargs="*", type=Path, default=[], help="JSONL result rows (see docstring)")
    ap.add_argument("--tasks", type=int, default=R.EXPECTED_HIDDEN_TASKS)
    ap.add_argument("--setup-minutes", type=float, default=R.ASSUMED_SETUP_MINUTES,
                    help="assumed per-task setup when rows carry no setup_s (VERIFY(Q8))")
    ap.add_argument("--server-start-minutes", type=float, default=R.ASSUMED_SERVER_START_MINUTES)
    ap.add_argument("--tok-s", type=float, default=R.ASSUMED_DECODE_TOK_S)
    ap.add_argument("--per-call-s", type=float, default=R.ASSUMED_PER_CALL_OVERHEAD_S)
    ap.add_argument("--gate", type=float, default=R.PACK_GATE_HOURS)
    ap.add_argument("--limit", type=float, default=R.RUN_BUDGET_HOURS)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    cap_min = args.cap_minutes
    if cap_min is None and args.eval_config:
        ev = load_eval_config(args.eval_config)
        cap_min = float(ev["max_time_minutes"]) if ev.get("max_time_minutes") is not None else None
    rows = load_rows(args.results) if args.results else []
    ests = [per_task_estimate(r, cap_s=cap_min * 60 if cap_min else None, tok_s=args.tok_s,
                              per_call_s=args.per_call_s) for r in rows]
    p = project(ests, n_tasks=args.tasks, setup_min=args.setup_minutes, cap_min=cap_min,
                server_start_min=args.server_start_minutes)
    worst = p["worst_case_h"]
    block = worst is None or worst > args.gate + 1e-9
    verdict = "BLOCK" if block else "PASS"
    if args.json:
        print(json.dumps({**p, "per_task": ests, "verdict": verdict}, indent=2))
    else:
        print(render(p, gate=args.gate, limit=args.limit, cap_min=cap_min))
        print(f"VERDICT: {verdict}")
    return 1 if block else 0


if __name__ == "__main__":
    sys.exit(main())
