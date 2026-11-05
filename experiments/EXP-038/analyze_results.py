#!/usr/bin/env python3
"""EXP-038 results: endpoints E1-E9, row 0 / 0b / 1 / 2 checks, the paired 2x2 against Arm R (48 and 27 ids)
and row T's room, all as defined (and amended) in experiments/EXP-038-e4b-single-loop-dev48.md sections 3-4.

Inputs (read as data; run with `python -I -X utf8`):
  runs/EXP-038-e4b-dev48/{summary.jsonl, task_results.jsonl, gemma4-exp038-e4b-dev48.log, patches/}
  experiments/EXP-028/armR/summary.jsonl, runs/EXP-028-armR/gemma4-exp028-armr.log
  experiments/cohorts/dev-48.txt, experiments/EXP-036/aggregates.json
Output: experiments/EXP-038/results.json -- ids, counts, error strings and config values only (plan.md:52).
"""
from __future__ import annotations

import json
import math
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "runs/EXP-038-e4b-dev48"
R_SUM = ROOT / "experiments/EXP-028/armR/summary.jsonl"
R_LOG = ROOT / "runs/EXP-028-armR/gemma4-exp028-armr.log"
DEV48 = ROOT / "experiments/cohorts/dev-48.txt"
EXP036 = ROOT / "experiments/EXP-036/aggregates.json"
OUT = ROOT / "experiments/EXP-038/results.json"

TIME_CAP_S, CALL_CAP, TURN_CAP, HIDDEN, CEILING_H = 480.0, 28, 80, 120, 10.5
CAP_PREFIXES = ("Agent exceeded session timeout", "Agent exceeded turns budget")
MODULES = {"inline_snapshot", "inline_snapshot.py", "dirty_equals", "dirty_equals.py"}

sys.path.insert(0, str(ROOT / "tools"))
from run_forensics import collect_forensics  # noqa: E402  (repo tool, not run data)


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def ids_of(p: Path) -> list[str]:
    return [s.strip() for s in p.read_text(encoding="utf-8").splitlines() if s.strip() and not s.startswith("#")]


def log_end(p: Path) -> float:
    return float(json.loads(p.read_text(encoding="utf-8"))[-1]["time"])


def mcnemar(b: int, c: int) -> float | None:
    n = b + c
    if n == 0:
        return None
    return min(1.0, 2 * sum(math.comb(n, k) for k in range(min(b, c) + 1)) / 2 ** n)


def p10(x: list[float]) -> float | None:
    return round(statistics.quantiles(x, n=10, method="inclusive")[0], 1) if len(x) >= 2 else None


def capped(s: dict) -> bool:          # E3 / row T cap-bound count: calls or time cap (section 7 item 7)
    return bool(s["calls_cap_hit"] or s["time_cap_hit"])


def at_no_cap(s: dict) -> bool:       # set U of the row T room definition
    return not capped(s) and s["n_turns"] < TURN_CAP


def added_paths(patch: str) -> list[str]:
    out, prev = [], None
    for line in patch.splitlines():
        if line.startswith("--- "):
            prev = line[4:].strip()
        elif line.startswith("+++ ") and prev == "/dev/null":
            out.append(re.sub(r"^b/", "", line[4:].strip()))
    return out


def paired(e: dict, r: dict, ids: list[str]) -> dict:
    both = [i for i in ids if e[i]["resolved"] and r[i]["resolved"]]
    r_only = [i for i in ids if r[i]["resolved"] and not e[i]["resolved"]]
    e_only = [i for i in ids if e[i]["resolved"] and not r[i]["resolved"]]
    neither = len(ids) - len(both) - len(r_only) - len(e_only)
    p = mcnemar(len(r_only), len(e_only))
    return {"n": len(ids), "both": len(both), "R_only": len(r_only), "E4B_only": len(e_only), "neither": neither,
            "R_only_ids": r_only, "E4B_only_ids": e_only, "mcnemar_exact_two_sided_p": None if p is None else round(p, 4)}


def main() -> int:
    ids = ids_of(DEV48)
    s = {x["task_id"]: x for x in jl(RUN / "summary.jsonl")}
    tr = {x["instance_id"]: x for x in jl(RUN / "task_results.jsonl")}
    r = {x["task_id"]: x for x in jl(R_SUM)}
    agg = json.loads(EXP036.read_text(encoding="utf-8"))
    gated, const = set(agg["gated_ids"]), set(agg["posthoc_gold_equals_base_ids"])
    assert sorted(s) == sorted(ids) and sorted(r) == sorted(ids)

    # row 0 (as amended: fix 1, fix 7, cancellation clause)
    errs = {i: (tr[i].get("error") or "") for i in tr}
    cap_rows = [i for i, e in errs.items() if e.startswith(CAP_PREFIXES)]
    cap_rows_0_turns = [i for i in cap_rows if s[i]["n_turns"] == 0]
    noncap_err = sorted(i for i, e in errs.items() if e and not e.startswith(CAP_PREFIXES))
    row0_errors = len(noncap_err) + len(cap_rows_0_turns)
    log_txt = json.loads((RUN / "gemma4-exp038-e4b-dev48.log").read_text(encoding="utf-8"))
    vllm = next((float(m.group(1)) for e in log_txt for m in [re.search(r"vLLM up in ([0-9.]+)s", e.get("data", ""))] if m), None)
    tok_s = next((float(m.group(1)) for e in log_txt for m in [re.search(r"'tok_s': ([0-9.]+)", e.get("data", ""))] if m), None)

    # row 0b
    const_expect = {i: (i == "requests_6644") for i in const}
    const_against = sorted(i for i in const if bool(s[i]["resolved"]) != const_expect[i])
    gated_res = sorted(i for i in gated if s[i]["resolved"])
    gated_res_vendoring = []
    for i in gated_res:
        pp = RUN / "patches" / f"{i}.patch"
        paths = added_paths(pp.read_text(encoding="utf-8", errors="replace")) if pp.exists() else []
        if any(set(Path(x).parts) & MODULES for x in paths):
            gated_res_vendoring.append(i)
    gated_anomaly = [i for i in gated_res if i not in gated_res_vendoring]

    # E1-E8
    wall = [s[i]["wall_s"] for i in ids]
    wall_sum = sum(wall)
    end = log_end(RUN / "gemma4-exp038-e4b-dev48.log")
    overhead = end - wall_sum
    mean_wall = wall_sum / len(ids)
    e7 = (mean_wall * HIDDEN + overhead) / 3600
    calls_all = sum(s[i]["n_calls_incl_free"] for i in ids)
    malformed = sum(s[i]["n_malformed"] for i in ids)
    per_task = collect_forensics(RUN)["per_task"]
    assert sorted(per_task) == sorted(ids), "forensics did not see all 48 traces"
    fe = [d["first_edit_turn"] for d in per_task.values() if d["first_edit_turn"]]
    never_edit = len(ids) - len(fe)

    # row T room on U
    U = [i for i in ids if at_no_cap(s[i])]
    room = [TIME_CAP_S - s[i]["wall_s"] for i in U]
    clock_room = (CEILING_H - e7) * 3600 / HIDDEN
    call_head = [CALL_CAP - s[i]["n_calls"] for i in U]
    turn_head = [TURN_CAP - s[i]["n_turns"] for i in U]
    s_per_turn = sum(s[i]["wall_s"] for i in U) / sum(s[i]["n_turns"] for i in U)

    r_end = log_end(R_LOG)
    r_wall_sum = sum(r[i]["wall_s"] for i in ids)
    inf = [i for i in ids if i not in gated and i not in const]

    out = {
        "row0": {"rows": len(tr), "ids_equal_cohort": sorted(tr) == sorted(ids), "noncap_error_ids": noncap_err,
                 "noncap_error_strings": sorted({errs[i] for i in noncap_err}), "cap_string_rows": len(cap_rows),
                 "cap_string_rows_with_0_turns": cap_rows_0_turns, "errors_counted": row0_errors,
                 "vllm_up_s": vllm, "decode_tok_s": tok_s, "statuses": sorted({str(tr[i].get("status")) for i in tr})},
        "row0b": {"constant_tasks_against_constant": const_against,
                  "constant_resolved": sorted(i for i in const if s[i]["resolved"]),
                  "gated_resolved": gated_res, "gated_resolved_patch_creates_module": gated_res_vendoring,
                  "gated_anomaly": gated_anomaly},
        "E1": {"resolved": sum(bool(s[i]["resolved"]) for i in ids), "n": len(ids)},
        "E2_48": paired(s, r, ids),
        "E2_27_informative": paired(s, r, inf),
        "E3": {"mean_wall_s": round(mean_wall, 1), "median_wall_s": round(statistics.median(wall), 1),
               "p90_wall_s": round(statistics.quantiles(wall, n=10, method="inclusive")[8], 1), "max_wall_s": max(wall),
               "max_wall_id": max(ids, key=lambda i: s[i]["wall_s"]),
               "calls_cap": sum(bool(s[i]["calls_cap_hit"]) for i in ids), "time_cap": sum(bool(s[i]["time_cap_hit"]) for i in ids),
               "turns_cap": sum(s[i]["n_turns"] >= TURN_CAP for i in ids), "capped_calls_or_time": sum(capped(s[i]) for i in ids),
               "none_submit_no_cap": sum(bool(s[i]["submit_patch_called"]) and at_no_cap(s[i]) for i in ids),
               "max_calls": max(s[i]["n_calls"] for i in ids), "max_turns": max(s[i]["n_turns"] for i in ids)},
        "E4": {"malformed": malformed, "calls_incl_free": calls_all},
        "E5": {"non_empty": sum(not s[i]["patch_empty"] for i in ids), "n": len(ids)},
        "E6": {"median_first_edit_turn": statistics.median(fe) if fe else None, "n_edited": len(fe), "never_edited": never_edit},
        "E7": {"mean_wall_s": round(mean_wall, 1), "overhead_s": round(overhead, 1), "projected_h": round(e7, 3),
               "ceiling_h": CEILING_H},
        "E8": {"log_end_s": round(end, 1), "kernel_h": round(end / 3600, 3), "task_wall_sum_s": round(wall_sum, 1)},
        "E9": {"compactions": sum(s[i]["compactions"] or 0 for i in ids),
               "edit_arg_loss": sum(s[i]["n_edit_arg_loss"] for i in ids),
               "s_per_turn_all": round(wall_sum / sum(s[i]["n_turns"] for i in ids), 2),
               "resolved_by_repo": {rp: sum(bool(s[i]["resolved"]) for i in ids if s[i]["repo"] == rp) for rp in sorted({s[i]["repo"] for i in ids})}},
        "rowT": {"capped_calls_or_time": sum(capped(s[i]) for i in ids), "U": len(U), "excluded": len(ids) - len(U),
                 "per_task_room_mean_s": round(statistics.mean(room), 1), "per_task_room_p10_s": p10(room),
                 "total_clock_room_s": round(clock_room, 1),
                 "binding_at_mean_s": round(min(statistics.mean(room), clock_room), 1),
                 "binding_at_p10_s": round(min(p10(room), clock_room), 1),
                 "call_headroom_mean": round(statistics.mean(call_head), 1), "call_headroom_p10": p10(call_head),
                 "turn_headroom_mean": round(statistics.mean(turn_head), 1), "turn_headroom_p10": p10(turn_head),
                 "s_per_turn_U": round(s_per_turn, 2)},
        "armR_reference": {"mean_wall_s": round(r_wall_sum / len(ids), 1), "overhead_s": round(r_end - r_wall_sum, 1),
                           "kernel_h": round(r_end / 3600, 3)},
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
