#!/usr/bin/env python3
"""EXP-075 / EXP-076 noise reference (zero GPU): how often does a rerun of the E4B single loop move a task in or out
of a divergence stage, against EXP-038 on shared ids?

Classes are EXP-074 `diag.classify` at margin 5 (E, F, R, C, S; lowercase when resolved). Runs:
  EXP-033-e4b  smoke-8, the same tree as EXP-038 (EXP-033 candidate-e4b)            -> a rerun
  EXP-044-X0   failed-edit-8, the EXP-038 zip itself                                  -> a rerun
  EXP-044-X    failed-edit-8, plus one prompt bullet (re-read, then copy)             -> near-rerun, a variant
  EXP-045-p    smoke-8, plus one prompt bullet (repro in /tmp)                        -> near-rerun, a variant
  EXP-053-r    smoke-8, plus one prompt bullet (never resend a failed old_string)     -> near-rerun, a variant
Prints ids, class letters and counts only. Usage: python -I -X utf8 experiments/EXP-075/noise.py [RUN-NAME]
With RUN-NAME, that run alone is compared with EXP-038 (the arm's paired transition table).
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "EXP-074"))
import diag  # noqa: E402

BASE = "EXP-038-e4b-dev48"
OTHERS = [("EXP-033-e4b", "rerun"), ("EXP-044-X0", "rerun"), ("EXP-044-X", "variant"), ("EXP-045-p", "variant"),
          ("EXP-053-r", "variant")]


def run_dir(name: str) -> Path:
    p = ROOT / "runs" / name
    if (p / "summary.jsonl").exists() and (p / "traces").is_dir():
        return p
    for q in sorted((p / "runs").glob("*")) if (p / "runs").is_dir() else []:
        if q.is_dir() and (q / "summary.jsonl").exists():
            return q
    raise SystemExit(f"no run dir for {name}")


def classes(name: str, tasks: dict) -> dict[str, str]:
    rd = run_dir(name)
    summ = {d["task_id"]: d for d in diag.jl(rd / "summary.jsonl")}
    res = {d["instance_id"]: d for d in diag.jl(rd / "task_results.jsonl")}
    out = {}
    for tid in summ:
        greg = diag.gold_regions(tasks[tid]["patch"], 5)
        c = diag.classify(res[tid].get("patch") or "", bool(summ[tid]["patch_empty"]), greg, 5)
        out[tid] = c.lower() if summ[tid]["resolved"] else c
    return out


def main() -> int:
    tasks = {json.loads(l)["instance_id"]: json.loads(l) for l in open(ROOT / "data/raw/tasks.jsonl", encoding="utf-8")}
    base = classes(BASE, tasks)
    others = [(sys.argv[1], "arm")] if len(sys.argv) > 1 else OTHERS
    pooled = {k: collections.Counter() for k in ("rerun", "variant", "arm")}
    for name, kind in others:
        o = classes(name, tasks)
        ids = sorted(set(o) & set(base))
        print(f"{name} ({kind}) vs {BASE} on {len(ids)} shared ids")
        for tid in ids:
            print(f"   {tid:15s} {base[tid]} -> {o[tid]}")
        c = collections.Counter()
        for tid in ids:
            b, x = base[tid].upper(), o[tid].upper()
            for st in "EF":
                if b == st:
                    c[f"{st}_n"] += 1
                    c[f"{st}_left"] += x != st
                else:
                    c[f"not{st}_n"] += 1
                    c[f"{st}_entered"] += x == st
            c["same_class"] += b == x
            c["n"] += 1
            c["res_base"] += base[tid].islower()
            c["res_other"] += o[tid].islower()
        print(f"   counts {dict(c)}")
        pooled[kind].update(c)
    for k, c in pooled.items():
        print(f"pooled {k}: {dict(c)}")
    e = collections.Counter(v.upper() for v in base.values())
    print(f"{BASE} classes over 48: {dict(e)} (lowercase resolved counted in their class)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
