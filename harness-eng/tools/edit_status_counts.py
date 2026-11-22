"""edit_file result status counts per group of runs (counts only; R-032 mechanism reading).

  python3 -I tools/edit_status_counts.py [--subset COHORT] LABEL=runs/A-d1,runs/A-d2 [LABEL=...]

Per group: edit_file results with status ok, with status error, without a parseable status; the failed share
error / (ok + error).
Only tasks in COHORT (one id per line) are counted when --subset is given.
"""
import json, os, sys

args = sys.argv[1:]
subset = None
if args and args[0] == "--subset":
    subset = {l.split()[0] for l in open(args[1]) if l.strip() and not l.startswith("#")}
    args = args[2:]
for g in args:
    label, runs = g.split("=", 1)
    ok = err = none = tasks = 0
    for run in runs.split(","):
        for line in open(os.path.join(run, "task_results.jsonl")):
            r = json.loads(line)
            if subset is not None and r["instance_id"] not in subset:
                continue
            tasks += 1
            tp = os.path.join(run, "traces", "trace_%s.json" % r["instance_id"])
            if not os.path.exists(tp):
                continue
            for s in json.load(open(tp))["steps"]:
                for c in (s.get("tool_calls") or []):
                    if c["function_name"] != "edit_file":
                        continue
                    try:
                        st = json.loads((s.get("observation") or {}).get("content") or "{}").get("status")
                    except (ValueError, TypeError, AttributeError):
                        st = None
                    ok += st == "ok"
                    err += st == "error"
                    none += st not in ("ok", "error")
    n = len(runs.split(","))
    print(json.dumps({"group": label, "draws": n, "task_rows": tasks, "ok": ok, "error": err, "no_status": none,
                      "failed_share": round(err / max(1, ok + err), 3)}))
