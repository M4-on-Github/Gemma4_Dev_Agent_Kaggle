"""Provisional rows 2 and 3 inputs for EXP-083/084 while data/raw/tasks.jsonl and the baseline run dirs are absent.
Uses screen_read.uptake unchanged for the arm. Baselines come from the committed summary.jsonl copies (no traces, so
baseline uptake is not computed). Field logic copied from screen_read.load. Prints ids and counts only."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "EXP-083"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-074"))
import screen_read as S  # noqa: E402

def summ(p):
    out = {}
    for l in open(ROOT / p, encoding="utf-8"):
        if l.strip():
            r = json.loads(l)
            out[r.get("task") or r.get("instance_id") or r.get("task_id")] = r
    return out

def row(s):
    return {"calls": s["n_calls"], "wall": s["wall_s"], "cap": bool(s["calls_cap_hit"] or s["time_cap_hit"]),
            "tf": bool((s.get("n_text_form_calls") or 0) or s.get("tool_free")), "empty": bool(s["patch_empty"]),
            "malformed": s.get("n_malformed") or 0, "resolved": bool(s["resolved"])}

SETS = {
    "EXP-083": ("experiments/cohorts/sweep-31b-8.txt", "runs/EXP-083-sweep",
                {"EXP-028-armR": "experiments/EXP-028/armR/summary.jsonl", "EXP-028-armRH": "experiments/EXP-028/armRH/summary.jsonl"}, 10.04),
    "EXP-084": ("experiments/cohorts/sweep-e4b-8.txt", "runs/EXP-084-sweep",
                {"EXP-038-e4b-dev48": "experiments/EXP-038/e4b/summary.jsonl", "EXP-077-base": "experiments/EXP-077/summary.jsonl",
                 "EXP-075-t02": "experiments/EXP-075/summary.jsonl", "EXP-078-t02r": "experiments/EXP-078/summary.jsonl"}, None),
}
for exp, (coh, rd, bases, proj) in SETS.items():
    ids = [l.strip() for l in open(ROOT / coh, encoding="utf-8") if l.strip() and not l.startswith("#")]
    a = summ(Path(rd) / "summary.jsonl")
    arm = {t: row(a[t]) for t in ids if t in a}
    up = {t: S.uptake(ROOT / rd, t) for t in ids}
    B = {b: {t: row(v[t]) for t in ids if t in v} for b, p in bases.items() for v in [summ(p)]}
    print(f"== {exp}: arm rows {len(arm)}; baseline rows " + ", ".join(f"{b} {len(v)}" for b, v in B.items()))
    print(f"  uptake arm {sum(up.values())} of {len(ids)}: " + ",".join(t for t in ids if up[t]))
    capn = lambda v: sum(x["cap"] for x in v.values())
    print(f"  tasks at a call or time cap arm {capn(arm)}; " + "; ".join(f"{b} {capn(v)}" for b, v in B.items())
          + f"; baseline mean {S.mean(capn(v) for v in B.values()):.2f}")
    tf = lambda v: sum(x["tf"] for x in v.values())
    print(f"  tasks text-form or tool_free arm {tf(arm)}; " + "; ".join(f"{b} {tf(v)}" for b, v in B.items())
          + f"; baseline mean {S.mean(tf(v) for v in B.values()):.2f}; malformed calls arm {sum(x['malformed'] for x in arm.values())}; "
          + "; ".join(f"{b} {sum(x['malformed'] for x in v.values())}" for b, v in B.items()))
    em = lambda v: sum(x["empty"] for x in v.values())
    print(f"  empty patches arm {em(arm)}; " + "; ".join(f"{b} {em(v)}" for b, v in B.items()) + f"; baseline mean {S.mean(em(v) for v in B.values()):.2f}")
    print(f"  calls mean arm {S.mean(x['calls'] for x in arm.values()):.2f}; " + "; ".join(f"{b} {S.mean(x['calls'] for x in v.values()):.2f}" for b, v in B.items()))
    print(f"  resolves arm {sum(x['resolved'] for x in arm.values())}; " + "; ".join(f"{b} {sum(x['resolved'] for x in v.values())}" for b, v in B.items()))
    bw = S.mean(S.mean(v[t]["wall"] for v in B.values() if t in v) for t in ids)
    dw = S.mean(x["wall"] for x in arm.values()) - bw
    print(f"  mean wall arm {S.mean(x['wall'] for x in arm.values()):.1f} s; baseline mean of per-task means {bw:.1f} s; delta {dw:+.1f} s")
    if proj is not None:
        print(f"  projected worst case = {proj:.2f} + 120 x delta / 3600 = {proj + 120 * dw / 3600:.2f} h (gate 11.0 h)")
