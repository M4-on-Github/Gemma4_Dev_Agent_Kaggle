"""Paired comparison of two arms, each one or more draws of the same cohort. Standard library, Python 3.6+.

  python3 tools/compare.py R-000-31b-base-d1,R-000-31b-base-d2 R-001-31b-calls40-d1,R-001-31b-calls40-d2

Prints per-draw resolves, the per-task resolve counts of each arm, the tasks that moved, and the
totals. Only ids present in every draw are compared. `--ledger` prints the GPU ledger instead.
"""
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(run):
    rows = {}
    with open(os.path.join(ROOT, "runs", run, "task_results.jsonl")) as fh:
        for line in fh:
            d = json.loads(line)
            rows[d["instance_id"]] = d
    return rows


def arm(spec):
    names = [s for s in spec.split(",") if s]
    return names, [load(n) for n in names]


def describe(names, draws, ids):
    for n, d in zip(names, draws):
        res = sum(bool(d[i]["resolved"]) for i in ids)
        wall = sorted(d[i].get("duration_s") or 0 for i in ids)
        calls = sum(d[i].get("tool_calls") or 0 for i in ids) / float(len(ids))
        capped = sum((d[i].get("tool_calls") or 0) >= (d[i].get("max_tool_calls") or 10 ** 9) for i in ids)
        slow = sum((d[i].get("duration_s") or 0) >= 60 * (d[i].get("max_time_minutes") or 10 ** 9) for i in ids)
        empty = sum(not d[i].get("patch_chars") for i in ids)
        print("  %-34s %2d/%d  wall mean %4.0f s median %4.0f s  calls %.1f  at call cap %d  at time cap %d  empty patch %d"
              % (n, res, len(ids), sum(wall) / len(wall), wall[len(wall) // 2], calls, capped, slow, empty))


def ledger():
    tot = {}
    with open(os.path.join(ROOT, "logs", "gpu_seconds.csv")) as fh:
        for run, job, host, sec in csv.reader(fh):
            key = "31b" if "31b" in run else "e4b" if "e4b" in run else "other"
            tot[key] = tot.get(key, 0) + int(sec)
            print("%-40s %-8s %-14s %6.2f GPU-h" % (run, job, host, int(sec) / 3600.0))
    for k, v in sorted(tot.items()):
        print("TOTAL %-5s %.2f GPU-h" % (k, v / 3600.0))


def main():
    if "--ledger" in sys.argv:
        return ledger()
    (an, a), (bn, b) = arm(sys.argv[1]), arm(sys.argv[2])
    ids = sorted(set.intersection(*[set(d) for d in a + b]))
    print("A (base):"); describe(an, a, ids)
    print("B (candidate):"); describe(bn, b, ids)
    ta = sum(bool(d[i]["resolved"]) for d in a for i in ids)
    tb = sum(bool(d[i]["resolved"]) for d in b for i in ids)
    print("resolves per draw: A %.1f  B %.1f  (B-A %+.1f) over %d tasks" % (ta / float(len(a)), tb / float(len(b)),
                                                                     tb / float(len(b)) - ta / float(len(a)), len(ids)))
    up, down = [], []
    for i in ids:
        ra = sum(bool(d[i]["resolved"]) for d in a) / float(len(a))
        rb = sum(bool(d[i]["resolved"]) for d in b) / float(len(b))
        if rb > ra:
            up.append("%s %.1f->%.1f" % (i, ra, rb))
        elif rb < ra:
            down.append("%s %.1f->%.1f" % (i, ra, rb))
    print("up   (%d): %s" % (len(up), ", ".join(up)))
    print("down (%d): %s" % (len(down), ", ".join(down)))


if __name__ == "__main__":
    main()
