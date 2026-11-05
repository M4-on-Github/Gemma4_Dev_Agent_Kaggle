"""EXP-030 L1b: zero-GPU trace mining over a finished run (default runs/EXP-028-armR).

Run (reads untrusted-ish data, so isolated mode):
    python -I -X utf8 experiments/EXP-030/l1b_trace_mining.py --run runs/EXP-028-armR \
        --tasks data/raw/tasks.jsonl --out experiments/EXP-030/l1b_armR.json

Part 1: reproduce the 2026-11-05 tool-latency table (D-004 addendum).
    tool latency  = step.observation.extra.elapsed_s - step.tool_calls[0].extra.elapsed_s
    model latency = this step's tool_calls[0].extra.elapsed_s (or, for a step with no tool call, step.extra.elapsed_s)
                    minus the previous step's observation elapsed_s (the task_prompt step's elapsed_s for the first step)
Part 2: localization bound. Per task: did any edit_file or write_file path match a path in the gold patch
    (counts only; gold content is never printed or written), split by resolved / unresolved, with the number of tool calls
    and the seconds before the first edit_file/write_file call that touches a non-/tmp path.

Only aggregates and per-task booleans/counts are written. No trace text, no gold text.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

READ_PROGS = ("grep", "rg", "sed", "cat", "ls", "find", "git", "head", "tail", "wc", "awk", "tree", "nl", "file", "stat")
GOLD_PATH_RE = re.compile(r"^diff --git a/(\S+) b/(\S+)", re.M)


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def classify(name: str, args: dict) -> str:
    if name != "run_command":
        return name
    cmd = str(args.get("command") or "").strip()
    first = cmd.split()[0] if cmd.split() else ""
    if "pytest" in cmd:
        return "run_command:pytest"
    if "<<" in cmd or re.search(r"(^|\s)(cat|tee|echo|printf)\b.*>\s*\S", cmd):
        return "run_command:write"
    if first.startswith("python") or " python" in cmd.split("|")[0] and first not in READ_PROGS:
        return "run_command:python"
    if first in READ_PROGS:
        return "run_command:read/search"
    return "run_command:other"


def norm_path(p: str) -> str:
    p = p.strip().replace("\\", "/")
    for pre in ("/workspace/", "./"):
        if p.startswith(pre):
            p = p[len(pre):]
    return p.lstrip("/")


def gold_files(task: dict) -> set[str]:
    patch = task.get("patch") or ""
    out = set()
    for a, b in GOLD_PATH_RE.findall(patch):
        out.add(norm_path(b))
    return out


def pct(vals: list[float], q: float) -> float:
    if not vals:
        return float("nan")
    s = sorted(vals)
    k = min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))
    return s[k]


def summarize(vals: list[float], total_wall: float) -> dict:
    return {
        "n": len(vals),
        "median_s": round(statistics.median(vals), 3) if vals else None,
        "p90_s": round(pct(vals, 0.9), 3) if vals else None,
        "max_s": round(max(vals), 3) if vals else None,
        "total_s": round(sum(vals), 1),
        "share_of_traced_wall": round(sum(vals) / total_wall, 4) if total_wall else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, default=Path("runs/EXP-028-armR"))
    ap.add_argument("--tasks", type=Path, default=Path("data/raw/tasks.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("experiments/EXP-030/l1b_armR.json"))
    a = ap.parse_args()

    results = {r.get("instance_id") or r.get("task_id"): r for r in load_jsonl(a.run / "task_results.jsonl")}
    tasks = {t["instance_id"]: t for t in load_jsonl(a.tasks)}

    tool_lat: dict[str, list[float]] = defaultdict(list)
    model_lat: list[float] = []
    per_task: dict[str, dict] = {}

    for tp in sorted((a.run / "traces").glob("trace_*.json")):
        tid = tp.name[len("trace_"):-len(".json")]
        if tid not in results:
            continue
        trace = json.loads(tp.read_text(encoding="utf-8"))
        steps = trace.get("steps") or []
        prev_obs = 0.0
        for s in steps:
            if (s.get("extra") or {}).get("event_type") == "task_prompt":
                prev_obs = float((s.get("extra") or {}).get("elapsed_s") or 0.0)
        n_calls = 0
        first_edit_calls = None
        first_edit_s = None
        edited: set[str] = set()
        gold = gold_files(tasks[tid]) if tid in tasks else set()
        for s in steps:
            if s.get("source") != "agent":
                continue
            tcs = s.get("tool_calls") or []
            if not tcs:
                t_end = (s.get("extra") or {}).get("elapsed_s")
                if t_end is not None and t_end >= prev_obs:
                    model_lat.append(t_end - prev_obs)
                    prev_obs = t_end
                continue
            call_t = (tcs[0].get("extra") or {}).get("elapsed_s")
            obs_t = ((s.get("observation") or {}).get("extra") or {}).get("elapsed_s")
            if call_t is None or obs_t is None:
                continue
            if call_t >= prev_obs:
                model_lat.append(call_t - prev_obs)
            args0 = tcs[0].get("arguments")
            if isinstance(args0, str):
                try:
                    args0 = json.loads(args0)
                except ValueError:
                    args0 = {}
            args0 = args0 if isinstance(args0, dict) else {}
            kind = classify(str(tcs[0].get("function_name") or ""), args0)
            tool_lat[kind].append(obs_t - call_t)
            tool_lat["ALL"].append(obs_t - call_t)
            prev_obs = obs_t
            for tc in tcs:
                n_calls += 1
                name = str(tc.get("function_name") or "")
                if name in ("edit_file", "write_file"):
                    args = tc.get("arguments")
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except ValueError:
                            args = {}
                    args = args if isinstance(args, dict) else {}
                    path = norm_path(str(args.get("filepath") or args.get("path") or args.get("file_path") or ""))
                    if path and not path.startswith("tmp/"):
                        edited.add(path)
                        if first_edit_calls is None:
                            first_edit_calls = n_calls
                            first_edit_s = (tc.get("extra") or {}).get("elapsed_s")
        row = results[tid]
        per_task[tid] = {
            "resolved": bool(row.get("resolved")),
            "edited_any_source_file": bool(edited),
            "touched_gold_file": bool(edited & gold),
            "n_gold_files": len(gold),
            "n_files_edited": len(edited),
            "calls_before_first_edit": (first_edit_calls - 1) if first_edit_calls is not None else None,
            "seconds_before_first_edit": round(first_edit_s, 1) if first_edit_s is not None else None,
            "tool_calls": row.get("tool_calls"),
            "duration_s": row.get("duration_s"),
        }

    total_wall = sum(model_lat) + sum(tool_lat["ALL"])
    latency = {"model_turn": summarize(model_lat, total_wall)}
    for k in sorted(tool_lat):
        latency[k] = summarize(tool_lat[k], total_wall)

    def split(flag: bool) -> dict:
        rows = [r for r in per_task.values() if r["resolved"] is flag]
        n = len(rows)
        touched = [r for r in rows if r["touched_gold_file"]]
        def med(key, sel):
            v = [r[key] for r in sel if r[key] is not None]
            return round(statistics.median(v), 1) if v else None
        return {
            "n": n,
            "touched_gold_file": len(touched),
            "edited_other_file_only": len([r for r in rows if r["edited_any_source_file"] and not r["touched_gold_file"]]),
            "never_edited_source": len([r for r in rows if not r["edited_any_source_file"]]),
            "median_calls_before_first_edit": med("calls_before_first_edit", rows),
            "median_seconds_before_first_edit": med("seconds_before_first_edit", rows),
            "median_calls_before_first_edit_touching_gold": med("calls_before_first_edit", touched),
        }

    out = {
        "run": str(a.run),
        "n_tasks": len(per_task),
        "latency": latency,
        "localization_bound": {"resolved": split(True), "unresolved": split(False),
                               "all_touched_gold_file": sum(1 for r in per_task.values() if r["touched_gold_file"])},
        "per_task": per_task,
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"run {a.run}  tasks {len(per_task)}  traced wall {total_wall:.0f} s")
    print(f"{'what':26s} {'n':>6s} {'median':>8s} {'p90':>8s} {'max':>8s} {'share':>7s}")
    for k, v in latency.items():
        print(f"{k:26s} {v['n']:6d} {v['median_s']!s:>8} {v['p90_s']!s:>8} {v['max_s']!s:>8} {v['share_of_traced_wall']!s:>7}")
    lb = out["localization_bound"]
    print("localization bound (edit path matches a gold-patch file; counts only):")
    for key in ("resolved", "unresolved"):
        print(f"  {key:11s} {lb[key]}")
    print(f"  all tasks touching a gold file: {lb['all_touched_gold_file']} of {len(per_task)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
