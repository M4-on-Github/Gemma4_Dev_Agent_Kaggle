#!/usr/bin/env python3
"""EXP-083 and EXP-084: read a sibling-site sweep smoke-8 against the same ids' existing baseline runs (zero GPU).
Rules: the section 3 and 4 of the EXP file named by --exp (endpoints and readings). Written before the kernels ran, untested.

Prints ids, counts, class letters and booleans only (plan.md:52: no gold, patch, trace or repository text).
Usage (31B):
  python -I -X utf8 experiments/EXP-083/screen_read.py --cohort experiments/cohorts/sweep-31b-8.txt \
      --arm EXP-083-sweep --base EXP-028-armR --base EXP-028-armRH --proj-base-h 10.04
Usage (E4B):
  python -I -X utf8 experiments/EXP-083/screen_read.py --cohort experiments/cohorts/sweep-e4b-8.txt \
      --arm EXP-084-sweep --base EXP-038-e4b-dev48 --base EXP-077-base --base EXP-075-t02 --base EXP-078-t02r
Gold regions touched uses diag.gold_regions and diag.touches (margin 5, gold source files), as EXP-082.
Sweep uptake: a run_command whose command text contains the string grep, issued after the first edit_file call.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "EXP-074"))
import diag  # noqa: E402

M = 5
CAP_PREFIX = ("Agent exceeded session timeout", "Agent exceeded turns budget")
NOSUBMIT = "Agent completed execution without calling submit_patch."


def touched(patch: str, greg: dict) -> tuple[int, int]:
    p = diag.parse_diff(patch)
    total = hit = 0
    for f, rs in greg.items():
        lines = set().union(*[l for x, l in p.items() if diag.same_file(f, x)] or [set()])
        for r in rs:
            total += 1
            hit += diag.touches(lines, r, M)
    return hit, total


def uptake(rd: Path, tid: str) -> bool:
    try:
        steps = json.load(open(rd / "traces" / f"trace_{tid}.json", encoding="utf-8")).get("steps") or []
    except OSError:
        return False
    seen_edit = False
    for s in steps:
        if s.get("source") != "agent":
            continue
        for tc in s.get("tool_calls") or []:
            fn = tc.get("function_name") or tc.get("name")
            if fn == "edit_file":
                seen_edit = True
            elif fn == "run_command" and seen_edit and "grep" in str(diag.refs.args_of(tc).get("command") or ""):
                return True
    return False


def load(name: str, ids: list[str], tasks: dict) -> dict:
    rd, summ, res = diag.load_run(name)
    out = {}
    for tid in ids:
        if tid not in summ:
            continue
        s, r = summ[tid], res.get(tid, {})
        patch = r.get("patch") or ""
        greg = diag.gold_regions(tasks[tid]["patch"], M)
        hit, total = touched(patch, greg)
        out[tid] = {
            "total": total, "hit": 0 if s["patch_empty"] else hit,
            "cls": diag.classify(patch, bool(s["patch_empty"]), greg, M),
            "resolved": bool(s["resolved"]), "calls": s["n_calls"], "wall": s["wall_s"],
            "calls_cap": bool(s["calls_cap_hit"]), "time_cap": bool(s["time_cap_hit"]),
            "text_form": s.get("n_text_form_calls") or 0, "tool_free": bool(s.get("tool_free")),
            "malformed": s.get("n_malformed") or 0, "uptake": uptake(rd, tid),
            "infra": (r.get("llm_calls") == 0) or (s.get("n_turns") == 0)
                     or bool(r.get("error") and not str(r["error"]).startswith(CAP_PREFIX) and str(r["error"]) != NOSUBMIT),
            "empty": bool(s["patch_empty"]),
        }
    return out


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--base", action="append", required=True)
    ap.add_argument("--proj-base-h", type=float, default=None, help="31B only: the baseline projected worst case in hours")
    a = ap.parse_args()
    ids = [l.strip() for l in open(ROOT / a.cohort, encoding="utf-8") if l.strip() and not l.startswith("#")]
    tasks = {}
    for l in open(ROOT / "data/raw/tasks.jsonl", encoding="utf-8"):
        t = json.loads(l)
        tasks[t["instance_id"]] = t
    arm = load(a.arm, ids, tasks)
    bases = {b: load(b, ids, tasks) for b in a.base}
    print(f"arm {a.arm}: rows {len(arm)} of {len(ids)}; baselines {', '.join(f'{b} {len(v)}' for b, v in bases.items())}")
    print(f"row 1 inputs: infrastructure rows {sum(r['infra'] for r in arm.values())} (2 or more reads not readable)")

    print("\nper task: id regions | arm touched cls resolved calls wall caps(c,t) uptake | baseline mean touched, resolves, uptake share | direction")
    up = dn = eq = 0
    for tid in ids:
        r = arm.get(tid)
        bs = [v[tid] for v in bases.values() if tid in v]
        bm = mean(x["hit"] for x in bs)
        if r is None:
            print(f"  {tid:16s} no arm row")
            continue
        d = "+" if r["hit"] > bm else "-" if r["hit"] < bm else "="
        up += d == "+"
        dn += d == "-"
        eq += d == "="
        print(f"  {tid:16s} {r['total']:3d} | {r['hit']:3d} {r['cls']} {int(r['resolved'])} {r['calls']:3d} {r['wall']:6.1f} "
              f"({int(r['calls_cap'])},{int(r['time_cap'])}) {int(r['uptake'])} | {bm:5.2f}, {sum(x['resolved'] for x in bs)}/{len(bs)}, "
              f"{mean(int(x['uptake']) for x in bs):4.2f} | {d}")
    print(f"\nprimary: tasks with arm touched above / below / equal to the baseline mean: {up} / {dn} / {eq} (of {len(arm)})")
    print(f"primary: mean touched arm {mean(r['hit'] for r in arm.values()):.3f}; baseline mean of per-task means "
          f"{mean(mean(v[t]['hit'] for v in bases.values() if t in v) for t in ids):.3f}")
    print(f"resolves (recorded, not an endpoint): arm {sum(r['resolved'] for r in arm.values())} of {len(arm)}; "
          + "; ".join(f"{b} {sum(x['resolved'] for x in v.values())}" for b, v in bases.items()))
    print(f"all regions touched (class S or resolved): arm {sum(1 for r in arm.values() if r['cls'] == 'S' or r['resolved'])}; "
          + "; ".join(f"{b} {sum(1 for x in v.values() if x['cls'] == 'S' or x['resolved'])}" for b, v in bases.items()))
    print(f"row 2 input, uptake: arm {sum(r['uptake'] for r in arm.values())} of {len(arm)}; "
          + "; ".join(f"{b} {sum(x['uptake'] for x in v.values())}" for b, v in bases.items()))
    print(f"guards: calls mean arm {mean(r['calls'] for r in arm.values()):.2f}; "
          + "; ".join(f"{b} {mean(x['calls'] for x in v.values()):.2f}" for b, v in bases.items()))
    capn = lambda v: sum(1 for x in v.values() if x["calls_cap"] or x["time_cap"])
    print(f"guards: tasks at a call or time cap arm {capn(arm)}; " + "; ".join(f"{b} {capn(v)}" for b, v in bases.items())
          + f"; baseline mean {mean(capn(v) for v in bases.values()):.2f}")
    tf = lambda v: sum(1 for x in v.values() if x["text_form"] or x["tool_free"])
    print(f"guards: tasks with a text-form call or tool_free arm {tf(arm)}; " + "; ".join(f"{b} {tf(v)}" for b, v in bases.items())
          + f"; baseline mean {mean(tf(v) for v in bases.values()):.2f}; malformed calls arm {sum(r['malformed'] for r in arm.values())}")
    print(f"guards: empty patches arm {sum(r['empty'] for r in arm.values())}; " + "; ".join(f"{b} {sum(x['empty'] for x in v.values())}" for b, v in bases.items()))
    bw = mean(mean(v[t]["wall"] for v in bases.values() if t in v) for t in ids)
    dw = mean(r["wall"] for r in arm.values()) - bw
    print(f"guards: mean wall arm {mean(r['wall'] for r in arm.values()):.1f} s; baseline mean of per-task means {bw:.1f} s; delta {dw:+.1f} s")
    if a.proj_base_h is not None:
        print(f"31B projected worst case = {a.proj_base_h:.2f} h + 120 x delta / 3600 = {a.proj_base_h + 120 * dw / 3600:.2f} h (gate: 11.0 h)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
