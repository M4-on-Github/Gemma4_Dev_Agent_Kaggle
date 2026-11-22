"""R-035 mechanism counts (2026-11-22): edit_file argument loss per draw. Counts only; never prints trace text,
code, paths or argument contents.

  python3 -I tools/argloss_counts.py LABEL=runs/A,runs/B [LABEL=...]

Per group, per draw:
  edit_calls, edit_ok, edit_failed  edit_file results: status ok / any other result that is not a loss
  lost                              results holding only `error` (an argument did not reach the tool)
  bt_close                          lost calls whose new_string value ends in a backtick, a comma and the old_string
                                    key text (the 31B slip found by the R-035 desk check)
  lost_tasks                        tasks with at least one lost call
  first_lost                        tasks whose first edit_file call was lost
  resolved, empty, timecap (task_wall_s >= 470), calls (mean tool_calls), wall (mean task_wall_s)
plus, pooled over the group: lost_after_lost = P(lost | previous edit_file call lost), lost_after_ok likewise,
and lost_share = lost / edit_calls.
"""
import collections
import json
import os
import statistics
import sys

TAIL = "`,old_string:"


def outcome(s):
    try:
        d = json.loads((s.get("observation") or {}).get("content") or "")
    except (ValueError, TypeError):
        return None
    if not isinstance(d, dict):
        return None
    return "ok" if d.get("status") == "ok" else "lost" if set(d) == {"error"} else "failed"


def args_of(c):
    a = c.get("arguments")
    if isinstance(a, str):
        try:
            a = json.loads(a)
        except ValueError:
            return {}
    return a if isinstance(a, dict) else {}


def scan(runs):
    C = collections.Counter(); T = collections.Counter(); walls = []; calls = []
    for run in runs:
        for line in open(os.path.join(run, "task_results.jsonl")):
            r = json.loads(line)
            walls.append(r.get("task_wall_s") or 0); calls.append(r.get("tool_calls") or 0)
            C["resolved"] += bool(r.get("resolved")); C["empty"] += not r.get("patch_chars")
            C["timecap"] += (r.get("task_wall_s") or 0) >= 470
            tp = os.path.join(run, "traces", f"trace_{r['instance_id']}.json")
            if not os.path.exists(tp):
                C["no_trace"] += 1
                continue
            h = []
            for s in json.load(open(tp))["steps"]:
                for c in s.get("tool_calls") or []:
                    if c["function_name"] != "edit_file":
                        continue
                    st = outcome(s)
                    if st is None:
                        continue
                    h.append(st); C["edit_calls"] += 1; C["edit_" + st if st != "lost" else "lost"] += 1
                    if st == "lost" and str(args_of(c).get("new_string", "")).endswith(TAIL):
                        C["bt_close"] += 1
            C["lost_tasks"] += "lost" in h
            C["first_lost"] += bool(h) and h[0] == "lost"
            for x, y in zip(h, h[1:]):
                T[(x, y)] += 1
    return C, T, walls, calls


for spec in sys.argv[1:]:
    label, runs = spec.split("=", 1)
    runs = [x for x in runs.split(",") if x]
    C, T, walls, calls = scan(runs)
    n = len(runs)
    out = {"group": label, "draws": n}
    for k in ("edit_calls", "edit_ok", "edit_failed", "lost", "bt_close", "lost_tasks", "first_lost",
              "resolved", "empty", "timecap", "no_trace"):
        out[k] = round(C[k] / n, 2)
    for prev in ("lost", "ok"):
        tot = sum(v for (x, _), v in T.items() if x == prev)
        out[f"lost_after_{prev}"] = round(T[(prev, "lost")] / tot, 3) if tot else None
    out["lost_share"] = round(C["lost"] / C["edit_calls"], 3) if C["edit_calls"] else None
    out["calls"] = round(statistics.mean(calls), 1) if calls else None
    out["wall"] = round(statistics.mean(walls), 1) if walls else None
    print(json.dumps(out))
