#!/usr/bin/env python3
"""EXP-080 Part 1 (zero GPU): EXP-074 classes (margin 5) of EXP-028 arm R (the 31B on the E4B tree's files) against
the four E4B dev-48 draws, and the short / same / further tally of section 2.2 of the EXP-080 file.

Stage rank: E 0, F 1, R 2, C 3, S 4, resolved 5. Short = E4B rank below arm R's; the E4B "leaves at" its own class.
Sensitivity: arm R re-ranked as resolved where experiments/EXP-036/summary.jsonl R_resolved_regraded is true.
Prints ids, class letters and counts only.
Usage: python -I -X utf8 experiments/EXP-080/part1.py
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "EXP-075"))
import noise  # noqa: E402

REF = "EXP-028-armR"
DRAWS = ["EXP-038-e4b-dev48", "EXP-077-base", "EXP-075-t02", "EXP-078-t02r"]
ORDER = "EFRCS"
STAGES = "EFRCSv"  # v = resolved


def stage(c: str) -> str:
    return "v" if c.islower() else c


def rank(c: str) -> int:
    return STAGES.index(stage(c))


def tally(ref: dict, cl: dict, ids: list[str], label: str, skip: set[str] | None = None) -> None:
    tot = collections.Counter()
    mat = collections.Counter()
    leaves = collections.Counter()
    per_task = collections.defaultdict(list)
    for d in DRAWS:
        dm = collections.Counter()
        dl = collections.Counter()
        dt = collections.Counter()
        for t in ids:
            if skip and (d, t) in skip:
                continue
            a, b = ref[t], cl[d][t]
            mat[(stage(a), stage(b))] += 1
            dm[(stage(a), stage(b))] += 1
            if rank(b) < rank(a):
                dt["short"] += 1
                dl[stage(b)] += 1
                leaves[stage(b)] += 1
                per_task[t].append(stage(b))
            elif rank(b) == rank(a):
                dt["same"] += 1
            else:
                dt["further"] += 1
        tot.update(dt)
        print(f"[{label}] {d}: short {dt['short']} same {dt['same']} further {dt['further']}; "
              f"leaves at " + " ".join(f"{k}{dl.get(k, 0)}" for k in ORDER))
    n = sum(tot.values())
    print(f"[{label}] four draws, per task-draw ({n}): short {tot['short']} same {tot['same']} further {tot['further']}; "
          f"leaves at " + " ".join(f"{k}{leaves.get(k, 0)}" for k in ORDER)
          + f"; E+F share of short {(leaves['E'] + leaves['F']) / max(1, tot['short']):.3f}")
    print(f"[{label}] matrix summed over the four draws, arm R stage (rows) -> E4B stage (columns), v = resolved")
    print("        " + "   ".join(STAGES))
    for x in STAGES:
        print(f"   {x}  " + " ".join(f"{mat[(x, y)]:3d}" for y in STAGES) + f"   row {sum(mat[(x, y)] for y in STAGES)}")
    deep = [x for x in "CSv"]
    n_deep = sum(mat[(x, y)] for x in deep for y in STAGES)
    n_deep_ok = sum(mat[(x, y)] for x in deep for y in deep)
    print(f"[{label}] arm R at C, S or resolved: {n_deep} task-draws; E4B also at C, S or resolved in {n_deep_ok}"
          f" ({n_deep_ok / max(1, n_deep):.3f})")
    short_tasks = {t: v for t, v in per_task.items() if len(v) >= 3}
    st_leave = collections.Counter()
    for t, v in sorted(short_tasks.items()):
        c = collections.Counter(v)
        top = max(c.values())
        st_leave["/".join(sorted(k for k in c if c[k] == top))] += 1
    print(f"[{label}] per task: short in at least 3 of 4 draws {len(short_tasks)} tasks; most frequent leave stage "
          + " ".join(f"{k}:{v}" for k, v in sorted(st_leave.items())))
    by_ref = collections.Counter(stage(ref[t]) for t in short_tasks)
    print(f"[{label}] those tasks by arm R stage: " + " ".join(f"{k}{by_ref.get(k, 0)}" for k in STAGES))


def main() -> int:
    tasks = {json.loads(l)["instance_id"]: json.loads(l) for l in open(ROOT / "data/raw/tasks.jsonl", encoding="utf-8")}
    ref = noise.classes(REF, tasks)
    cl = {d: noise.classes(d, tasks) for d in DRAWS}
    ids = sorted(set(ref).intersection(*(set(v) for v in cl.values())))
    print(f"shared ids {len(ids)}")
    for r, c in [(REF, ref)] + [(d, cl[d]) for d in DRAWS]:
        unres = collections.Counter(c[t] for t in ids if c[t].isupper())
        nres = sum(1 for t in ids if c[t].islower())
        print(f"classes {r}: unresolved " + " ".join(f"{k}{unres.get(k, 0)}" for k in ORDER) + f"  resolved {nres}")
    g = {d["task_id"]: d for d in (json.loads(l) for l in open(ROOT / "experiments/EXP-036/summary.jsonl", encoding="utf-8"))}
    asrun = sum(1 for t in ids if g[t]["R_resolved_as_run"])
    agree = sum(1 for t in ids if g[t]["R_resolved_as_run"] == ref[t].islower())
    print(f"EXP-036 check: R_resolved_as_run {asrun} of {len(ids)}; agrees with arm R summary on {agree}; "
          f"re-graded {sum(1 for t in ids if g[t]['R_resolved_regraded'])}; gated {sum(1 for t in ids if g[t]['gated'])}")
    ever = noise.diag.ever_resolved()[0]
    print("table: task | ever | gated | armR as run | armR re-graded | " + " | ".join(DRAWS))
    for t in ids:
        print(f"   {t:15s} {'y' if t in ever else '-'} {'g' if g[t]['gated'] else '-'} {ref[t]} "
              f"{'v' if g[t]['R_resolved_regraded'] else '-'}  " + " ".join(cl[d][t] for d in DRAWS))
    tally(ref, cl, ids, "as run")
    ref2 = {t: (ref[t].lower() if g[t]["R_resolved_regraded"] else ref[t]) for t in ids}
    tally(ref2, cl, ids, "arm R re-graded")
    gated = {t for t in ids if g[t]["gated"]}
    skip = {(d, t) for d in DRAWS[1:] for t in gated}
    print(f"un-regraded gated E4B cells (EXP-077, EXP-075, EXP-078 on {len(gated)} gated ids): {len(skip)}; "
          f"of them unresolved {sum(1 for d, t in skip if cl[d][t].isupper())}")
    tally(ref2, cl, ids, "arm R re-graded, un-regraded gated E4B cells dropped", skip)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
