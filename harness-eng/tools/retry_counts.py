"""Retry mechanism counts for a tree whose root calls the `solve` agent_tool (R-018 onward). Counts only; never prints
trace text, code or paths.

  python3 -I tools/retry_counts.py runs/<RUN> [runs/<RUN> ...]

Per task the steps are cut into attempts at each root `solve` call. An attempt is empty when every submit_patch
result inside it reports files_changed 0, non-empty when one reports more than 0, and unknown when it holds no
submit_patch result. Prints, per run: the histogram of solve calls per task; first-attempt empty / non-empty /
unknown; retried (first attempt empty and a second solve call followed); over-retry (a second solve call after a
non-empty first attempt); retry_miss (first attempt empty, not retried); rescued (resolved, first attempt empty); and tasks with more than 3 solve calls.
"""
import collections, json, os, re, sys

FC = re.compile(r'files_changed\W{0,4}(\d+)')


def attempts(steps):
    segs, cur, started = [], [], False
    for s in steps:
        if s.get("source") != "agent":
            continue
        names = [c["function_name"] for c in (s.get("tool_calls") or [])]
        if s["extra"].get("author") == "swe_agent" and "solve" in names:
            if started:
                segs.append(cur)
            cur, started = [], True
        if "submit_patch" in names and s.get("observation"):
            m = FC.findall(str(s["observation"].get("content")))
            if m:
                cur.append(int(m[-1]))
    if started:
        segs.append(cur)
    return segs


def state(seg):
    if not seg:
        return "unknown"
    return "nonempty" if max(seg) > 0 else "empty"


for run in sys.argv[1:]:
    agg = collections.Counter(); hist = collections.Counter()
    for line in open(os.path.join(run, "task_results.jsonl")):
        r = json.loads(line)
        tp = os.path.join(run, "traces", f"trace_{r['instance_id']}.json")
        if not os.path.exists(tp):
            agg["no_trace"] += 1
            continue
        segs = attempts(json.load(open(tp))["steps"])
        hist[len(segs)] += 1
        agg["solve_calls_gt3"] += len(segs) > 3
        if not segs:
            continue
        first = state(segs[0])
        agg["first_" + first] += 1
        if first == "empty":
            agg["retried"] += len(segs) > 1
            agg["rescued"] += bool(r["resolved"])
        if first == "nonempty" and len(segs) > 1:
            agg["over_retry"] += 1
    out = {"run": os.path.basename(run.rstrip("/")), "solve_calls_hist": dict(sorted(hist.items()))}
    out.update(agg)
    out["retry_miss"] = agg["first_empty"] - agg["retried"]   # first attempt empty, no second solve call
    print(json.dumps(out))
