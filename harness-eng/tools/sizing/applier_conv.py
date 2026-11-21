"""How far would a rescued edit go? E4B base R-011: resolve rate of draws that land a source edit, and whether the
draws a fuzzy (NEAR) or window-anchored applier would rescue sit on tasks the E4B ever solves. Counts only.

Usage: python3 -I applier_conv.py OUT_JSON
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import applier_e4b as A  # noqa: E402

out = {}
for arm in ("base_r011", "full0_l003_partial"):
    draws = []
    for run in A.ARMS[arm]:
        for line in open(os.path.join(A.HE, "runs", run, "task_results.jsonl")):
            row = json.loads(line)
            if not os.path.exists(os.path.join(A.HE, "runs", run, "traces", f"trace_{row['instance_id']}.json")):
                continue
            r = A.scan(run, row["instance_id"])
            r.update(iid=row["instance_id"], resolved=bool(row["resolved"]))
            draws.append(r)
    solved_tasks = {d["iid"] for d in draws if d["resolved"]}
    landed = [d for d in draws if d["landed_src"]]
    nolanded_fail = [d for d in draws if not d["landed_src"] and any(f["bucket"] != "BUDGET" for f in d["fails"])]
    near = [d for d in nolanded_fail if any(f["bucket"] == "NOT_FOUND" and f.get("cls") == "NEAR" and not f["stale"]
                                            for f in d["fails"])]
    anchor = [d for d in nolanded_fail if any(f["bucket"] == "NOT_UNIQUE" and f.get("win_unique") and not f.get("stale")
                                              for f in d["fails"])]
    either = {id(d) for d in near} | {id(d) for d in anchor}
    either_d = [d for d in nolanded_fail if id(d) in either]
    # resolve rate of landed draws on the same tasks as the rescued draws
    rate = lambda ds: (sum(d["resolved"] for d in ds), len(ds))
    tasks_e = {d["iid"] for d in either_d}
    out[arm] = dict(
        draws=len(draws), solved_tasks=len(solved_tasks),
        landed=rate(landed), not_landed=rate([d for d in draws if not d["landed_src"]]),
        failed_never_landed=len(nolanded_fail),
        rescued_near=len(near), rescued_anchor=len(anchor), rescued_either=len(either_d),
        rescued_either_on_ever_solved_task=sum(1 for d in either_d if d["iid"] in solved_tasks),
        landed_resolve_on_rescued_tasks=rate([d for d in landed if d["iid"] in tasks_e]),
    )
    print(arm, out[arm])
json.dump(out, open(sys.argv[1], "w"), indent=1)
