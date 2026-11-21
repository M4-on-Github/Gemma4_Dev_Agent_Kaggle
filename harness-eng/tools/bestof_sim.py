"""Offline sizing of the R-019 best-of policy, using the tree's own pick.py choose(). Counts only.

  env/py313-scorer/bin/python3.13 -I tools/bestof_sim.py --pick trees/e4b-r019-bestof/skills/best-of/scripts/pick.py \
      --cap-s 480 --time-div 1 runs/<BASE-d1> runs/<BASE-d2> runs/<BASE-d3>

For every ordered tuple of 3 distinct draws, a task's attempt j is draw j's row of that task. Attempts run while
pick.choose() says NEXT. Tool calls (+2 root calls per attempt, +2 at the end), model calls (+3 per attempt, +3 at
the end) and wall (task_wall_s / time-div, +overhead per attempt) accumulate against the shared caps. An attempt that
would cross a cap is not run; the task then keeps the last non-empty attempt so far (the solver's own submit_patch
is what the harness evaluates when the root never submits). Prints resolved per draw, attempts per task, mean wall
per task and the share of tasks that hit a cap, next to the single-attempt base.
"""
import argparse, importlib.util, itertools, json, statistics

p = argparse.ArgumentParser()
p.add_argument("runs", nargs="+")
p.add_argument("--pick", required=True)
p.add_argument("--cap-s", type=float, default=480)
p.add_argument("--time-div", type=float, default=1.0)
p.add_argument("--calls", type=int, default=64)
p.add_argument("--turns", type=int, default=80)
p.add_argument("--overhead-s", type=float, default=6.0)
p.add_argument("--policy", default="pick", choices=["pick", "retry_empty", "oracle"])
a = p.parse_args()
spec = importlib.util.spec_from_file_location("pick", a.pick); pick = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pick)
D = [{json.loads(l)["instance_id"]: json.loads(l) for l in open(r + "/task_results.jsonl")} for r in a.runs]
T = sorted(set.intersection(*(set(d) for d in D)))


def cand(r):
    text = r.get("patch") or ""
    src = [(q, s) for q, s in pick.sections(text) if q and not pick.is_protected(q)]
    return tuple(sorted(q for q, _ in src)), sum(len(s) for _, s in src), text


base = statistics.mean(sum(bool(d[t]["resolved"]) for t in T) for d in D)
res, att, wall, capped = [], [], [], []
for perm in itertools.permutations(range(len(D)), min(3, len(D))):
    s = n = w = hit = 0
    for t in T:
        c = l = 0; tw = 0.0; cands, rows = [], []
        for i in perm:
            r = D[i][t]
            dt = r["task_wall_s"] / a.time_div + a.overhead_s
            if c + r["tool_calls"] + 2 + 2 > a.calls or l + r["llm_calls"] + 3 + 3 > a.turns or tw + dt > a.cap_s:
                hit += 1
                break
            c += r["tool_calls"] + 2; l += r["llm_calls"] + 3; tw += dt
            cands.append(cand(r)); rows.append(r)
            if a.policy == "pick":
                decision, text = pick.choose(cands)
            elif a.policy == "retry_empty":   # R-018: stop at the first non-empty attempt
                decision, text = ("APPLY", cands[-1][2]) if cands[-1][0] or len(cands) == 3 else ("NEXT", None)
            else:   # oracle over the attempts the pick policy would run
                decision, text = pick.choose(cands)
                if decision == "APPLY":
                    good = [x for x, rr in zip(cands, rows) if x[0] and rr["resolved"]]
                    text = good[0][2] if good else text
            if decision == "APPLY":
                break
        else:
            decision, text = "APPLY", None
        n += len(cands); w += tw
        if decision == "APPLY" and text is not None:
            k = next((j for j, x in enumerate(cands) if x[2] == text), None)
            s += bool(rows[k]["resolved"]) if k is not None and cands[k][0] else 0
        else:   # stopped by a cap: the last non-empty attempt so far
            k = next((j for j in range(len(cands) - 1, -1, -1) if cands[j][0]), None)
            s += bool(rows[k]["resolved"]) if k is not None else 0
    res.append(s); att.append(n / len(T)); wall.append(w / len(T)); capped.append(hit / len(T))
print(json.dumps({"policy": a.policy, "tasks": len(T), "draws": len(D), "cap_s": a.cap_s, "time_div": a.time_div, "calls": a.calls,
                  "turns": a.turns, "base_resolved": round(base, 2),
                  "resolved_per_draw": round(statistics.mean(res), 2),
                  "attempts_per_task": round(statistics.mean(att), 2),
                  "wall_per_task_s": round(statistics.mean(wall), 1),
                  "base_wall_s": round(statistics.mean(r["task_wall_s"] / a.time_div for d in D for r in d.values()), 1),
                  "cap_hit_share": round(statistics.mean(capped), 3)}))
