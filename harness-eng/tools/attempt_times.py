"""R-025 desk check (2026-11-22). Counts only.

  python3.13 -I tools/attempt_times.py - runs/<RETRY-d1> runs/<RETRY-d2> ...

 Per task in retry-arm runs: attempt start/end elapsed_s (cut at root `solve` calls), the attempt's
state (empty/nonempty by the count or submit), and the row's resolved flag."""
import json, os, sys, statistics as S

FC = __import__("re").compile(r'files_changed\W{0,4}(\d+)')
first_empty_end, solved_first_dur, solved_any_dur, rescued_second_dur, left_after_empty = [], [], [], [], []
for run in sys.argv[2:]:
    for line in open(os.path.join(run, "task_results.jsonl")):
        r = json.loads(line)
        tp = os.path.join(run, "traces", f"trace_{r['instance_id']}.json")
        if not os.path.exists(tp):
            continue
        steps = [s for s in json.load(open(tp))["steps"] if s.get("source") == "agent"]
        starts, vals = [], []
        for s in steps:
            names = [c["function_name"] for c in (s.get("tool_calls") or [])]
            t = s["extra"].get("elapsed_s") or 0
            if s["extra"].get("author") == "swe_agent" and "solve" in names:
                starts.append(t); vals.append([])
            if starts and s["extra"].get("author") == "swe_agent" and "run_skill_script" in names and s.get("observation"):
                try:
                    out = str(json.loads(s["observation"].get("content") or "{}").get("stdout", "")).strip()
                except (ValueError, AttributeError):
                    out = ""
                if out.isdigit():
                    vals[-1].append(int(out))
        if not starts:
            continue
        end = r["task_wall_s"]
        bounds = starts[1:] + [end]
        durs = [b - a for a, b in zip(starts, bounds)]
        st = ["nonempty" if v and max(v) > 0 else ("empty" if v else "unknown") for v in vals]
        if st[0] == "empty":
            first_empty_end.append(bounds[0]); left_after_empty.append(270 - bounds[0])
            if r["resolved"] and len(starts) > 1:
                rescued_second_dur.append(durs[-1])
        if r["resolved"] and len(starts) == 1:
            solved_first_dur.append(durs[0])
q = lambda xs: [round(x) for x in (S.quantiles(xs, n=10)[i] for i in (0, 4, 8))] if len(xs) > 2 else xs
print(json.dumps({"first_empty_n": len(first_empty_end), "first_empty_end_p10_p50_p90": q(first_empty_end),
  "left_after_empty_lt60": sum(x < 60 for x in left_after_empty), "left_lt120": sum(x < 120 for x in left_after_empty),
  "solved_single_attempt_n": len(solved_first_dur), "solved_attempt_dur_p10_p50_p90": q(solved_first_dur),
  "solved_dur_le60": sum(x <= 60 for x in solved_first_dur), "solved_dur_le120": sum(x <= 120 for x in solved_first_dur),
  "rescued_n": len(rescued_second_dur), "rescued_last_attempt_dur": sorted(round(x) for x in rescued_second_dur)}))
