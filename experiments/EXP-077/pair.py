#!/usr/bin/env python3
"""EXP-077 / EXP-075 results (zero GPU): EXP-074 classes (margin 5) of the three dev-48 E4B draws, the paired
class transition tables, the paired resolve 2x2 with exact McNemar, and (post hoc) the resolved-id union.

Runs: EXP-038-e4b-dev48 (base draw 1), EXP-077-base (base draw 2), EXP-075-t02 (temperature 0.2).
Prints ids, class letters and counts only.
Usage: python -I -X utf8 experiments/EXP-077/pair.py
"""
from __future__ import annotations

import collections
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "EXP-075"))
import noise  # noqa: E402

RUNS = ["EXP-038-e4b-dev48", "EXP-077-base", "EXP-075-t02"]
PAIRS = [("EXP-038-e4b-dev48", "EXP-077-base"), ("EXP-038-e4b-dev48", "EXP-075-t02"), ("EXP-077-base", "EXP-075-t02")]
ORDER = "EFRCS"


def mcnemar(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def main() -> int:
    tasks = {json.loads(l)["instance_id"]: json.loads(l) for l in open(ROOT / "data/raw/tasks.jsonl", encoding="utf-8")}
    cl = {r: noise.classes(r, tasks) for r in RUNS}
    ids = sorted(set.intersection(*(set(v) for v in cl.values())))
    print(f"shared ids {len(ids)}")
    res = {r: sorted(t for t in ids if cl[r][t].islower()) for r in RUNS}
    for r in RUNS:
        cnt = collections.Counter(cl[r][t].upper() for t in ids)
        print(f"classes {r}: " + " ".join(f"{k}{cnt.get(k, 0)}" for k in ORDER) + f"  resolved {len(res[r])} {res[r]}")
    for a, b in PAIRS:
        m = collections.Counter((cl[a][t].upper(), cl[b][t].upper()) for t in ids)
        print(f"transitions {a} (rows) -> {b} (columns), same class {sum(m[(k, k)] for k in ORDER)} of {len(ids)}")
        print("      " + "  ".join(ORDER))
        for x in ORDER:
            print(f"   {x}  " + "  ".join(str(m[(x, y)]) for y in ORDER))
        for st in ORDER:
            print(f"   {st}: count {sum(m[(st, y)] for y in ORDER)} -> {sum(m[(x, st)] for x in ORDER)}, "
                  f"left {sum(m[(st, y)] for y in ORDER if y != st)}, entered {sum(m[(x, st)] for x in ORDER if x != st)}")
        ra, rb = set(res[a]), set(res[b])
        both, a_only, b_only = sorted(ra & rb), sorted(ra - rb), sorted(rb - ra)
        print(f"resolves {a} vs {b}: both {len(both)} {both}; {a} only {len(a_only)} {a_only}; "
              f"{b} only {len(b_only)} {b_only}; exact McNemar p {mcnemar(len(a_only), len(b_only)):.3f}")
    union = sorted(set().union(*(set(v) for v in res.values())))
    print(f"post hoc union over the three runs: {len(union)} {union}")
    b1, b2 = set(res[RUNS[0]]), set(res[RUNS[1]])
    print(f"post hoc base draws: either {len(b1 | b2)} {sorted(b1 | b2)}; both {len(b1 & b2)}; "
          f"one but not both {len(b1 ^ b2)} {sorted(b1 ^ b2)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
