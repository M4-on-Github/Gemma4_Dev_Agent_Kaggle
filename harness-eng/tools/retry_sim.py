"""Offline sizing of retry-on-empty (R-018). Counts only.

  env/py313-scorer/bin/python3.13 -I tools/retry_sim.py runs/<BASE-d1> runs/<BASE-d2> ... [--caps 28:80 56:80] [--max-att 2 3]

For every ordered tuple of distinct draws, a task's attempt j is draw j's row of that task. Attempts run in order
until one has a non-empty patch; that attempt's resolved value is the task's. The task's tool calls and model calls
(+1 root call per attempt) accumulate against the shared caps; an attempt that would cross a cap ends the task
unresolved. Prints the mean resolved per draw, attempts per task and wall per task over all tuples.
"""
import argparse, itertools, json, statistics

p = argparse.ArgumentParser()
p.add_argument("runs", nargs="+")
p.add_argument("--caps", nargs="+", default=["28:80", "40:80", "56:80"])
p.add_argument("--max-att", nargs="+", type=int, default=[1, 2, 3])
a = p.parse_args()
D = [{json.loads(l)["instance_id"]: json.loads(l) for l in open(r + "/task_results.jsonl")} for r in a.runs]
T = sorted(set.intersection(*(set(d) for d in D)))
for cap in a.caps:
    calls_cap, turn_cap = map(int, cap.split(":"))
    for k in a.max_att:
        res, att, wall = [], [], []
        for perm in itertools.permutations(range(len(D)), k):
            s = n = w = 0
            for t in T:
                c = l = 0
                for i in perm:
                    r = D[i][t]
                    n += 1
                    if c + r["tool_calls"] > calls_cap or l + r["llm_calls"] + 1 > turn_cap:
                        break
                    c += r["tool_calls"]; l += r["llm_calls"] + 1; w += r["task_wall_s"]
                    if r["patch_chars"]:
                        s += bool(r["resolved"])
                        break
            res.append(s); att.append(n / len(T)); wall.append(w / len(T))
        print(json.dumps({"calls_cap": calls_cap, "turn_cap": turn_cap, "max_attempts": k, "tasks": len(T),
                          "resolved_per_draw": round(statistics.mean(res), 2),
                          "attempts_per_task": round(statistics.mean(att), 2),
                          "wall_per_task_s": round(statistics.mean(wall))}))
