"""Paired task-level comparison of two arms over the same cohort (counts only), as the round readings define it.

  python3 -I tools/paired_boot.py --arm runs/A-d1 runs/A-d2 ... --base runs/B-d1 runs/B-d2 ... [--subset FILE]

Per task: resolve rate over the arm's draws minus the base's. Statistic = mean difference x number of tasks
(solves per draw), with a 90% percentile bootstrap over tasks (10,000 resamples, random.Random(0)). Also prints the
per-draw resolved counts. Tasks missing from any draw are dropped and counted.
"""
import argparse, json, os, random

p = argparse.ArgumentParser()
p.add_argument("--arm", nargs="+", required=True)
p.add_argument("--base", nargs="+", required=True)
p.add_argument("--n", type=int, default=10000)
a = p.parse_args()


def load(runs):
    per = []
    for r in runs:
        per.append({json.loads(l)["instance_id"]: bool(json.loads(l)["resolved"])
                    for l in open(os.path.join(r, "task_results.jsonl"))})
    return per


A, B = load(a.arm), load(a.base)
tasks = sorted(set.intersection(*[set(d) for d in A + B]))
dropped = len(set.union(*[set(d) for d in A + B])) - len(tasks)
d = [sum(x[t] for x in A) / len(A) - sum(x[t] for x in B) / len(B) for t in tasks]
n = len(tasks)
rng = random.Random(0)
boots = sorted(sum(d[rng.randrange(n)] for _ in range(n)) for _ in range(a.n))
# R-032 2026-11-22: per-draw counts are over the paired tasks only; before this they summed each run's own rows, so a
# base run on a larger cohort printed its full-cohort counts (the statistic and CI were always on the paired tasks).
print(json.dumps({"tasks": n, "dropped": dropped, "arm_per_draw": [sum(x[t] for t in tasks) for x in A],
                  "base_per_draw": [sum(x[t] for t in tasks) for x in B], "diff_solves_per_draw": round(sum(d), 2),
                  "ci90": [round(boots[int(0.05 * a.n)], 2), round(boots[int(0.95 * a.n) - 1], 2)]}))
