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

Only aggregates are written (plan.md:52): no trace text, no gold text, no file paths, no per-task rows.

Experimenter fixes 2026-11-05 (first run):
  - the gold patches in tasks.jsonl carry `--- a/` / `+++ b/` headers and no `diff --git` line, so the original
    GOLD_PATH_RE matched nothing and every task read touched_gold_file = False (0 of 48). Paths now come from the
    `+++ b/` header (or `--- a/` when the file is deleted); the same parser reads our own patch.
  - the per-task table (task id -> gold-file booleans) was dropped from the output; it is per-task gold information.
  - added, to match the critic's figures in critic.md: tasks whose tool-call arguments name a gold file (full
    relative path, and basename), tasks whose submitted patch touches a gold file, a cap-bound split
    (calls_cap_hit from the run's analyze_traces summary.jsonl), and the 1-based call number of the first edit
    that touches a gold file.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

READ_PROGS = ("grep", "rg", "sed", "cat", "ls", "find", "git", "head", "tail", "wc", "awk", "tree", "nl", "file", "stat")
PLUS_RE = re.compile(r"^\+\+\+ b/(\S+)", re.M)
MINUS_RE = re.compile(r"^--- a/(\S+)", re.M)
DIFF_GIT_RE = re.compile(r"^diff --git a/(\S+) b/(\S+)", re.M)


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


def patch_files(patch: str) -> set[str]:
    """Files a unified diff touches: `+++ b/x`, or `--- a/x` when the new side is /dev/null."""
    out = set()
    for _a, b in DIFF_GIT_RE.findall(patch or ""):
        out.add(norm_path(b))
    for p in PLUS_RE.findall(patch or "") + MINUS_RE.findall(patch or ""):
        out.add(norm_path(p))
    return out


def gold_files(task: dict) -> set[str]:
    return patch_files(task.get("patch") or "")


def arg_text(args: dict) -> str:
    return " ".join(str(v) for v in args.values() if isinstance(v, (str, int, float)))


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
    ap.add_argument("--summary", type=Path, default=None,
                    help="analyze_traces summary.jsonl for calls_cap_hit (default <run>/summary.jsonl)")
    a = ap.parse_args()

    results = {r.get("instance_id") or r.get("task_id"): r for r in load_jsonl(a.run / "task_results.jsonl")}
    tasks = {t["instance_id"]: t for t in load_jsonl(a.tasks)}
    summary_path = a.summary or (a.run / "summary.jsonl")
    cap_hit = ({r["task_id"]: bool(r.get("calls_cap_hit")) for r in load_jsonl(summary_path)}
               if summary_path.is_file() else {})

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
        gold_base = {g.rsplit("/", 1)[-1] for g in gold}
        first_name_path = first_name_base = first_gold_edit = None
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
                args = tc.get("arguments")
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except ValueError:
                        args = {}
                args = args if isinstance(args, dict) else {}
                if name not in ("edit_file", "write_file"):
                    txt = arg_text(args)
                    if first_name_path is None and any(g in txt for g in gold):
                        first_name_path = n_calls
                    if first_name_base is None and any(b in txt for b in gold_base):
                        first_name_base = n_calls
                if name in ("edit_file", "write_file"):
                    path = norm_path(str(args.get("filepath") or args.get("path") or args.get("file_path") or ""))
                    if path and not path.startswith("tmp/"):
                        edited.add(path)
                        if first_edit_calls is None:
                            first_edit_calls = n_calls
                            first_edit_s = (tc.get("extra") or {}).get("elapsed_s")
                        if first_gold_edit is None and path in gold:
                            first_gold_edit = n_calls
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
            "cap_bound": cap_hit.get(tid),
            "names_gold_path_call": first_name_path,
            "names_gold_basename_call": first_name_base,
            "patch_touches_gold": bool(patch_files(row.get("patch") or "") & gold),
            "first_gold_edit_call": first_gold_edit,
        }

    total_wall = sum(model_lat) + sum(tool_lat["ALL"])
    latency = {"model_turn": summarize(model_lat, total_wall)}
    for k in sorted(tool_lat):
        latency[k] = summarize(tool_lat[k], total_wall)

    def med(key, sel):
        v = [r[key] for r in sel if r[key] is not None]
        return round(statistics.median(v), 1) if v else None

    def split(rows: list[dict]) -> dict:
        touched = [r for r in rows if r["touched_gold_file"]]
        return {
            "n": len(rows),
            "touched_gold_file": len(touched),
            "edited_other_file_only": len([r for r in rows if r["edited_any_source_file"] and not r["touched_gold_file"]]),
            "never_edited_source": len([r for r in rows if not r["edited_any_source_file"]]),
            "names_gold_path_in_args": sum(1 for r in rows if r["names_gold_path_call"] is not None),
            "names_gold_basename_in_args": sum(1 for r in rows if r["names_gold_basename_call"] is not None),
            "patch_touches_gold": sum(1 for r in rows if r["patch_touches_gold"]),
            "median_call_first_names_gold_path": med("names_gold_path_call", rows),
            "median_call_first_names_gold_basename": med("names_gold_basename_call", rows),
            "median_call_first_gold_edit": med("first_gold_edit_call", rows),
            "median_calls_before_first_edit": med("calls_before_first_edit", rows),
            "median_seconds_before_first_edit": med("seconds_before_first_edit", rows),
            "median_calls_before_first_edit_touching_gold": med("calls_before_first_edit", touched),
        }

    allr = list(per_task.values())
    out = {
        "run": str(a.run).replace("\\", "/"),
        "n_tasks": len(per_task),
        "latency": latency,
        "localization_bound": {
            "definitions": "touched_gold_file: an edit_file/write_file path (non-/tmp) equals a gold-patch file. "
                           "names_gold_*: a non-edit tool call's arguments contain a gold file's relative path / "
                           "basename. *_call values are 1-based tool-call numbers. cap_bound: calls_cap_hit in "
                           "analyze_traces summary.jsonl.",
            "all": split(allr),
            "resolved": split([r for r in allr if r["resolved"]]),
            "unresolved": split([r for r in allr if not r["resolved"]]),
            "cap_bound": split([r for r in allr if r["cap_bound"] is True]),
            "not_cap_bound": split([r for r in allr if r["cap_bound"] is False]),
            "cap_bound_known": bool(cap_hit),
        },
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"run {a.run}  tasks {len(per_task)}  traced wall {total_wall:.0f} s")
    print(f"{'what':26s} {'n':>6s} {'median':>8s} {'p90':>8s} {'max':>8s} {'share':>7s}")
    for k, v in latency.items():
        print(f"{k:26s} {v['n']:6d} {v['median_s']!s:>8} {v['p90_s']!s:>8} {v['max_s']!s:>8} {v['share_of_traced_wall']!s:>7}")
    lb = out["localization_bound"]
    print("localization bound (edit path matches a gold-patch file; counts only):")
    for key in ("all", "resolved", "unresolved", "cap_bound", "not_cap_bound"):
        print(f"  {key:13s} {lb[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
