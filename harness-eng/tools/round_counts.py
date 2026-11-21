"""Per-run counts for a round's gates (R-016 onward). Counts only; never prints trace text, code or paths.

  python3 -I tools/round_counts.py runs/<RUN> [runs/<BASE_RUN>] [-v]

Prints rows, mean task wall, resolved, empty patches, time caps (session timeout), error kinds, compactions (a
prompt-token drop of over 40% from above 8,000 between consecutive calls of the working agent), prompts above 24,576,
model calls after the 28th tool call, submit_patch calls and calls per submitting task, and the root's model calls
when the tree has a `solve` agent_tool. -v prints one line per task.
"""
import collections, json, os, statistics, sys

args = [a for a in sys.argv[1:] if a != "-v"]
verbose = "-v" in sys.argv
run = args[0]
rows = [json.loads(l) for l in open(os.path.join(run, "task_results.jsonl"))]
agg = collections.Counter(); walls = []; rootcalls = []; submitting = 0
for r in rows:
    walls.append(r["task_wall_s"])
    agg["status_" + str(r["status"])] += 1
    agg["resolved"] += bool(r["resolved"])
    agg["empty"] += (r["patch_chars"] or 0) == 0
    err = str(r.get("error")) if r.get("error") else ""
    agg["timecap"] += "session timeout" in err
    agg["err_" + (err[:40] or "none")] += 1
    tp = os.path.join(run, "traces", f"trace_{r['instance_id']}.json")
    if not os.path.exists(tp):
        agg["no_trace"] += 1
        continue
    st = [s for s in json.load(open(tp))["steps"] if s["source"] == "agent"]
    au = collections.Counter(s["extra"].get("author") for s in st)
    worker = "solve" if au.get("solve") else "swe_agent"
    rc = sum(1 for s in st if s["extra"].get("author") == "swe_agent" and s.get("metrics")) if worker == "solve" else 0
    rootcalls.append(rc)
    pt = [s["metrics"]["prompt_tokens"] for s in st if s["extra"].get("author") == worker and s.get("metrics")]
    comp = any(a > 8000 and b < 0.6 * a for a, b in zip(pt, pt[1:]))
    agg["compacted"] += comp
    # R-016 d1 (2026-11-21): a second `solve` call opens a fresh child session whose first prompt is short, which the
    # test above reads as compaction. compacted_in_session compares calls within one solve session only.
    segs, cur = [], []
    for s in st:
        if s["extra"].get("author") == "swe_agent" and any(c["function_name"] == "solve" for c in (s.get("tool_calls") or [])):
            segs.append(cur); cur = []
        elif s["extra"].get("author") == worker and s.get("metrics"):
            cur.append(s["metrics"]["prompt_tokens"])
    segs.append(cur)
    agg["compacted_in_session"] += any(a > 8000 and b < 0.6 * a for g in segs for a, b in zip(g, g[1:]))
    if worker == "solve":
        nsolve = sum(1 for s in st if s["extra"].get("author") == "swe_agent"
                     for c in (s.get("tool_calls") or []) if c["function_name"] == "solve")
        agg["solve_calls_gt1"] += nsolve > 1
    agg["over24576"] += any(p > 24576 for p in pt)
    n = 0
    for s in st:
        if s["extra"].get("author") == worker and s.get("metrics") and n >= 28:
            agg["calls_after_cap"] += 1
        n += len(s.get("tool_calls") or [])
    subs = sum(1 for s in st for c in (s.get("tool_calls") or []) if c["function_name"] == "submit_patch")
    agg["submit_calls"] += subs
    submitting += subs > 0
    if verbose:
        print(f"status={r['status']} resolved={r['resolved']} tool_calls={r['tool_calls']} authors={dict(au)} "
              f"root_calls={rc} first_prompt={pt[:1]} max_prompt={max(pt) if pt else None} compacted={comp} "
              f"submits={subs} wall={r['task_wall_s']:.0f}")
out = {"rows": len(rows), "mean_wall": round(statistics.mean(walls), 1),
       "submits_per_submitting_task": round(agg["submit_calls"] / submitting, 2) if submitting else None,
       "root_calls_max": max(rootcalls or [0])}
out.update(agg)
print(json.dumps(out))
