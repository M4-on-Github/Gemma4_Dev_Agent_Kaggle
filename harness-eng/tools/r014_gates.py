"""R-014 draw-level gate counts (reading 3), counts only.

  python3 tools/r014_gates.py scout runs/R-014-31b-scout-d1 [...]
  python3 tools/r014_gates.py applier runs/R-014-e4b-applier-tu5-d1 [...]
  python3 tools/r014_gates.py wall runs/<base draw> [...]        # mean task wall, for the projection baseline

Prints per-run counts as JSON; never prints trace, task or code text.
"""
import glob
import json
import os
import re
import statistics
import sys

SRC_EXCL = re.compile(r"(^|/)(tests?/|test_[^/]*\.py$|[^/]*_test\.py$|conftest\.py$|pytest\.ini$)")


def rows(run):
    return [json.loads(l) for l in open(os.path.join(run, "task_results.jsonl"))]


def trace(run, iid):
    p = os.path.join(run, "traces", f"trace_{iid}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def patch_files(patch):
    return [m.group(1) for m in re.finditer(r"^diff --git a/(\S+) b/", patch or "", re.M)]


def obs_dict(step):
    o = (step.get("observation") or {}).get("content")
    if o is None:
        return {}
    try:
        d = json.loads(o)
        return d if isinstance(d, dict) else {"raw": str(d)}
    except Exception:
        return {"raw": o}


def norm_path(p):
    if not isinstance(p, str):
        return ""
    p = p.strip().strip('"').strip("'")
    m = re.search(r"/workspace/(.*)$", p)
    if m:
        p = m.group(1)
    while p.startswith("./"):
        p = p[2:]
    return p


def base_counts(run):
    rs = rows(run)
    walls = [r["task_wall_s"] for r in rs if r.get("task_wall_s") is not None]
    return {"run": os.path.basename(run), "rows": len(rs), "resolved": sum(bool(r["resolved"]) for r in rs),
            "status_not_success": sum(r.get("status") != "SUCCESS" for r in rs),
            "mean_wall_s": round(statistics.mean(walls), 1) if walls else None,
            "median_wall_s": round(statistics.median(walls), 1) if walls else None,
            "time_cap": sum("timeout" in (r.get("error") or "") for r in rs),
            "call_cap": sum(r.get("tool_calls", 0) >= r.get("max_tool_calls", 28) for r in rs),
            "empty_patch": sum(not (r.get("patch") or "").strip() for r in rs)}


def scout(run):
    out = base_counts(run)
    scout_calls, editor_start, rerun, research, n = [], [], 0, 0, 0
    for r in rows(run):
        t = trace(run, r["instance_id"])
        if t is None:
            continue
        n += 1
        seq = []  # (author, tool name or TEXT)
        for s in t["steps"]:
            a = s["extra"].get("author")
            for tc in s.get("tool_calls") or []:
                seq.append((a, tc["function_name"], tc.get("arguments") or {}))
        sc = sum(1 for a, _, _ in seq if a == "scout")
        scout_calls.append(sc)
        authors = []
        for a, _, _ in seq:
            if not authors or authors[-1] != a:
                authors.append(a)
        if "editor" in authors:
            editor_start.append(next(i for i, (a, _, _) in enumerate(seq) if a == "editor"))
            if "scout" in authors[authors.index("editor"):]:
                rerun += 1
            ed = [(f, g) for a, f, g in seq if a == "editor"]
            first_edit = next((i for i, (f, _) in enumerate(ed) if f in ("edit_file", "write_file")), len(ed))
            if any(f == "run_command" and re.search(r"\b(grep|find|rg)\b", str(g.get("command", "")))
                   for f, g in ed[:first_edit]):
                research += 1
    q = sorted(scout_calls)
    out.update({"traced": n, "scout_calls_median": statistics.median(q) if q else None,
                "scout_calls_p90": q[min(len(q) - 1, -(-9 * len(q) // 10) - 1)] if q else None,  # nearest rank
                "reach_editor": len(editor_start),
                "editor_with_20plus_used": sum(x >= 20 for x in editor_start),
                "scout_rerun_after_editor": rerun, "editor_researched_before_edit": research})
    out["gates"] = {
        "scout_median_le_10": out["scout_calls_median"] is not None and out["scout_calls_median"] <= 10,
        "editor_late_le_15pct": out["editor_with_20plus_used"] <= 0.15 * out["rows"],
        "rerun_le_15pct": rerun <= 0.15 * out["rows"],
        "wall_le_395": out["mean_wall_s"] is not None and out["mean_wall_s"] <= 395,
        "resolved_gt_24": out["resolved"] > 24}
    out["projection_h"] = round(10.04 * out["mean_wall_s"] / 361, 2) if out["mean_wall_s"] else None
    return out


def applier(run):
    out = base_counts(run)
    src_change, src_change_with_apply, failed_any, notfound_any = 0, 0, 0, 0
    calls, applied, failed, other = 0, 0, 0, 0
    for r in rows(run):
        t = trace(run, r["instance_id"])
        files = [f for f in patch_files(r.get("patch")) if not SRC_EXCL.search(f)]
        used_apply, bad, nf = False, False, False
        if t is not None:
            for s in t["steps"]:
                a = s["extra"].get("author")
                for tc in s.get("tool_calls") or []:
                    if tc["function_name"] == "apply_edit":
                        used_apply = True
                        calls += 1
                    if tc["function_name"] in ("edit_file", "write_file"):
                        # same definition as trace_vs_reference.py (the 46.5% / 35.0% base figures): a call
                        # that is not ok, except the call cap and scratch paths outside the repo
                        d = obs_dict(s)
                        args = tc.get("arguments") or {}
                        p = norm_path(args.get("filepath") or args.get("path") or "")
                        repo_target = bool(p) and not p.startswith("/") and not p.startswith("tmp/")
                        ok = not ("error" in d and "status" not in d) and d.get("status") == "ok"
                        if not ok and d.get("error_type") != "BudgetExceeded" and repo_target:
                            bad = True
                            nf = nf or "not found" in (d.get("error_message") or "")
                if a == "apply_edit" and s["extra"].get("event_type") == "final":
                    m = (s.get("message") or "").strip()
                    if m.startswith("APPLIED"):
                        applied += 1
                    elif m.startswith("FAILED"):
                        failed += 1
                        bad = True
                    else:
                        other += 1
                        bad = True
        if files:
            src_change += 1
            src_change_with_apply += used_apply
        failed_any += bad
        notfound_any += nf
    n = out["rows"]
    out.update({"src_change_draws": src_change, "src_change_with_apply_edit": src_change_with_apply,
                "apply_edit_calls": calls, "helper_applied": applied, "helper_failed": failed,
                "helper_other_answer": other, "failed_edit_draws": failed_any, "notfound_draws": notfound_any})
    out["gates"] = {
        "apply_on_ge_60pct_src": src_change == 0 or src_change_with_apply >= 0.60 * src_change,
        "failed_edit_le_25pct": failed_any <= 0.25 * n,
        "empty_patch_le_24.4pct": out["empty_patch"] <= 0.244 * n,
        "resolved_gt_4": out["resolved"] > 4}
    return out


if __name__ == "__main__":
    mode, runs = sys.argv[1], sys.argv[2:]
    fn = {"scout": scout, "applier": applier, "wall": base_counts}[mode]
    for run in runs:
        print(json.dumps(fn(run)))
