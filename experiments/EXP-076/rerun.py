#!/usr/bin/env python3
"""EXP-076 noise reference for the opener endpoints (zero GPU): on ids shared with EXP-038, how often does a rerun of
the same E4B tree flip desk.py's per-task flags `opener` and `shown`?

Reruns (same tree): EXP-033-e4b (smoke-8), EXP-044-X0 (failed-edit-8). Variants (one prompt bullet added):
EXP-044-X, EXP-045-p, EXP-053-r. Prints ids, class letters and y/n flags only.
Usage: python -I -X utf8 experiments/EXP-076/rerun.py
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for d in ("EXP-074", "EXP-063", "EXP-075", "EXP-076"):
    sys.path.insert(0, str(ROOT / "experiments" / d))
import diag  # noqa: E402
import noise  # noqa: E402
import desk as D  # noqa: E402

BASE = "EXP-038-e4b-dev48"


def flags(name: str, tasks: dict, ids=None) -> dict[str, tuple[str, bool, bool]]:
    rd = noise.run_dir(name)
    cls = noise.classes(name, tasks)
    out = {}
    for tid in sorted(cls):
        if ids is not None and tid not in ids:
            continue
        g = tasks[tid]
        t = D.task(rd, tid, g.get("problem_statement") or "", list(diag.gold_regions(g["patch"], 5)))
        out[tid] = (cls[tid], t["opener"], t["shown"])
    return out


def yn(b: bool) -> str:
    return "y" if b else "n"


def main() -> int:
    tasks = {json.loads(l)["instance_id"]: json.loads(l) for l in open(ROOT / "data/raw/tasks.jsonl", encoding="utf-8")}
    base = flags(BASE, tasks)
    pooled = {"rerun": collections.Counter(), "variant": collections.Counter()}
    for name, kind in noise.OTHERS:
        o = flags(name, tasks)
        c = collections.Counter()
        for tid in sorted(set(o) & set(base)):
            b, x = base[tid], o[tid]
            print(f"{name:12s} {tid:15s} class {b[0]}->{x[0]} opener {yn(b[1])}->{yn(x[1])} "
                  f"shown {yn(b[2])}->{yn(x[2])}")
            c["n"] += 1
            c["opener_flip"] += b[1] != x[1]
            c["shown_flip"] += b[2] != x[2]
            c["opener_base"] += b[1]
            c["opener_other"] += x[1]
        print(f"{name} ({kind}): {dict(c)}")
        pooled[kind].update(c)
    for k, c in pooled.items():
        print(f"pooled {k}: {dict(c)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
