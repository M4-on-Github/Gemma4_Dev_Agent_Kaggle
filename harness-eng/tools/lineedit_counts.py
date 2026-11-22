"""R-034 mechanism counts (2026-11-22): edit attempts and their outcomes per draw, for edit_file trees and line-edit
trees alike. Counts only; never prints trace text, code, paths or argument contents.

  python3 -I tools/lineedit_counts.py LABEL=runs/A,runs/B [LABEL=...]

Per group: draws, task rows, and per draw
  edit_ok / edit_failed       edit_file results with status ok / anything else (argument loss included)
  replace_ok / replace_error  run_skill_script results of line-edit replace.py whose stdout starts OK / ERROR
  replace_raised              replace.py stdout starting "ERROR replace failed" (the script raised)
  show_calls                  run_skill_script calls of line-edit show.py
  write_file_calls            write_file calls
  argloss_edit / argloss_skill  results holding only `error` (arguments did not parse), on edit_file / run_skill_script
  empty, timecap (task_wall_s >= 470), calls (mean tool_calls), wall (mean task_wall_s)
plus fail_share = failed / (ok + failed) over edit_file and replace.py together.
"""
import collections
import json
import os
import statistics
import sys


def obs(s):
    try:
        d = json.loads((s.get("observation") or {}).get("content") or "")
    except (ValueError, TypeError):
        return None
    return d if isinstance(d, dict) else None


def script_of(c):
    a = c.get("arguments")
    if isinstance(a, str):
        try:
            a = json.loads(a)
        except ValueError:
            a = {}
    fp = str((a or {}).get("file_path", "")) if isinstance(a, dict) else ""
    return "replace" if fp.endswith("replace.py") else "show" if fp.endswith("show.py") else "other"


def scan(runs):
    C = collections.Counter(); walls = []; calls = []; rows = 0
    for run in runs:
        for line in open(os.path.join(run, "task_results.jsonl")):
            r = json.loads(line); rows += 1
            walls.append(r.get("task_wall_s") or 0); calls.append(r.get("tool_calls") or 0)
            C["empty"] += not r.get("patch_chars"); C["timecap"] += (r.get("task_wall_s") or 0) >= 470
            tp = os.path.join(run, "traces", f"trace_{r['instance_id']}.json")
            if not os.path.exists(tp):
                C["no_trace"] += 1
                continue
            for s in json.load(open(tp))["steps"]:
                for c in s.get("tool_calls") or []:
                    fn = c["function_name"]; d = obs(s)
                    lost = isinstance(d, dict) and set(d) == {"error"}
                    if fn == "edit_file":
                        C["edit_ok" if d and d.get("status") == "ok" else "edit_failed"] += 1
                        C["argloss_edit"] += lost
                    elif fn == "write_file":
                        C["write_file_calls"] += 1
                    elif fn == "run_skill_script":
                        C["argloss_skill"] += lost
                        k = script_of(c)
                        if k == "show":
                            C["show_calls"] += 1
                        elif k == "replace":
                            out = str((d or {}).get("stdout", "")).strip()
                            if out.startswith("OK"):
                                C["replace_ok"] += 1
                            else:
                                C["replace_error"] += 1
                                C["replace_raised"] += out.startswith("ERROR replace failed")
    return C, rows, walls, calls


for spec in sys.argv[1:]:
    label, runs = spec.split("=", 1)
    runs = [x for x in runs.split(",") if x]
    C, rows, walls, calls = scan(runs)
    n = len(runs)
    out = {"group": label, "draws": n, "task_rows": rows}
    for k in ("edit_ok", "edit_failed", "replace_ok", "replace_error", "replace_raised", "show_calls",
              "write_file_calls", "argloss_edit", "argloss_skill", "empty", "timecap", "no_trace"):
        out[k] = round(C[k] / n, 2)
    ok, bad = C["edit_ok"] + C["replace_ok"], C["edit_failed"] + C["replace_error"]
    out["fail_share"] = round(bad / (ok + bad), 3) if ok + bad else None
    out["calls"] = round(statistics.mean(calls), 1) if calls else None
    out["wall"] = round(statistics.mean(walls), 1) if walls else None
    print(json.dumps(out))
