#!/usr/bin/env python3
"""Per-task and aggregate metrics from a harness run (plan.md §5.3).

Input layout (what notebooks/kaggle_eval_l4x4 writes, mirroring the official harness results dir):
    <run_dir>/task_results.jsonl          one row per task (see FIELDS below); optional but recommended
    <run_dir>/traces/trace_<id>.json      official SessionTrace (ATIF-like): {"steps": [...], "final_metrics": {...}}

task_results.jsonl rows (any subset): instance_id|task_id, repo, resolved, duration_s|duration_seconds, setup_s,
    tool_calls, llm_calls, error, status, patch|agent_patch|patch_chars, trace (path), max_tool_calls, max_time_minutes.

Trace steps (observed format, VERIFY against a real trace): {"step_id", "source": "system"|"user"|"agent",
    "message", "tool_calls": [{"function_name", "arguments", "extra": {"elapsed_s", ...}}], "observation": {"content"},
    "extra": {"event_type", ...}}; final_metrics: total_prompt_tokens, total_completion_tokens, total_steps.

Per-task output columns (summary.jsonl): task_id, repo, resolved, patch_empty, submit_patch_called, wall_s,
    setup_s, n_calls, n_turns, n_malformed, n_identical_repeats, n_undeclared_tool, overflow_400, nudges,
    compactions, phase_reached, output_tokens, prompt_tokens, thinking_tokens, timeout_hit, calls_cap_hit,
    time_cap_hit, n_edit_fail, n_edit_arg_loss, n_whole_file_reads, scratch_in_patch, error.
Aggregates (aggregates.json): resolve rate with Wilson 95% CI, rates of the failure modes, median/p90 wall,
    projected 12 h total = sum(wall+setup) * (120/N), worst case = 120 * (cap + setup).

Usage:
    python tools/analyze_traces.py runs/EXP-001 [--out runs/EXP-001] [--cap-minutes 4.5] [--max-calls 45]
"""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics as st
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import submission_rules as R  # noqa: E402

TOOL_CALL_START = "<|tool_call>"
PHASES = ("LOCATE", "REPRODUCE", "EDIT", "VERIFY", "SUBMIT")
LEDGER_RE = re.compile(r"\[phase=([A-Z]+)")
NUDGE_MARKERS = ("Please continue your work using the available tools",
                 "reached the token limit")
OVERFLOW_MARKERS = ("ContextWindowExceeded", "context length", "maximum context", "context window",
                    "Error code: 400", "status code 400", "HTTP 400")
TIMEOUT_MARKERS = ("exceeded session timeout", "TimeoutError", "timed out", "Session timeout")
SCRATCH_RE = re.compile(r"^\+\+\+ b/((?:repro|reproduce|scratch|test_repro|tmp)[^\s]*)", re.M)


def _first(row: dict, *keys, default=None):
    for k in keys:
        if row.get(k) is not None:
            return row[k]
    return default


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((centre - half) / denom, (centre + half) / denom)


def canonical(name: str, args) -> str:
    try:
        return name + json.dumps(args, sort_keys=True, ensure_ascii=False)
    except TypeError:
        return name + str(args)


def analyze_trace(trace: dict, *, declared: set[str]) -> dict:
    """Metrics derived from one SessionTrace."""
    steps = trace.get("steps") or []
    calls: list[tuple[str, dict]] = []
    n_turns = n_malformed = n_undeclared = nudges = compactions = n_edit_fail = n_whole_reads = 0
    n_edit_arg_loss = 0
    submit_called = False
    phase = None
    last_calls: list[str] = []
    identical = 0
    edit_ids: set[str] = set()
    for s in steps:
        src = s.get("source")
        msg = s.get("message") or ""
        extra = s.get("extra") or {}
        etype = str(extra.get("event_type") or "")
        if "compact" in etype.lower() or "compact" in str(extra.get("author") or "").lower():
            compactions += 1
        if src == "user":
            if any(m in msg for m in NUDGE_MARKERS):
                nudges += 1
            continue
        if src != "agent":
            continue
        n_turns += 1
        if TOOL_CALL_START in msg:
            n_malformed += 1   # a call vLLM could not parse stayed in the content
        for m in LEDGER_RE.finditer(msg):
            if m.group(1) in PHASES:
                phase = m.group(1)
        for tc in s.get("tool_calls") or []:
            name = str(tc.get("function_name") or tc.get("name") or "")
            args = tc.get("arguments")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except ValueError:
                    pass
            calls.append((name, args if isinstance(args, dict) else {}))
            if declared and name not in declared:
                n_undeclared += 1
            key = canonical(name, args)
            if key in last_calls[-3:]:
                identical += 1
            last_calls.append(key)
            if name == "submit_patch":
                submit_called = True
            if name == "edit_file":
                edit_ids.add(str(tc.get("tool_call_id")))
            if name == "read_file" and isinstance(args, dict) and not args.get("start_line") and not args.get("end_line"):
                n_whole_reads += 1
        obs = s.get("observation") or {}
        content = obs.get("content") if isinstance(obs, dict) else None
        if content and (s.get("tool_calls") or [{}])[-1].get("function_name") == "edit_file":
            c = str(content)
            # The '"status": "error"' envelope misses the DOMINANT failure mode: an edit_file
            # call whose old_string argument never arrived fails with a bare
            # 'mandatory input parameters are not present: old_string' and NO envelope.
            # Measured in EXP-024: 117 of 309 edit_file calls across both dev-48 runs. This
            # detector reported 9 for E0 against 92 real losses -- a ~10x understatement, and
            # not comparable between runs. Both forms are counted now; the arg-loss subset is
            # tracked separately because it is the actionable one (the call never reached the
            # file, so retrying identical arguments loops forever).
            envelope_err = '"status": "error"' in c or '\\"status\\": \\"error\\"' in c
            arg_loss = "mandatory input parameters are not present" in c
            if envelope_err or arg_loss:
                n_edit_fail += 1
            if arg_loss:
                n_edit_arg_loss += 1
    if phase is None:
        names = [c[0] for c in calls]
        if submit_called:
            phase = "SUBMIT"
        elif "edit_file" in names or "write_file" in names:
            after_edit = names[max(i for i, n in enumerate(names) if n in ("edit_file", "write_file")) + 1:]
            phase = "VERIFY" if any(n == "run_command" for n in after_edit) else "EDIT"
        elif names:
            phase = "LOCATE"
        else:
            phase = "NONE"
    fm = trace.get("final_metrics") or {}
    counted = [c for c in calls if c[0] not in R.FREE_TOOLS]
    return {
        "n_calls": len(counted), "n_calls_incl_free": len(calls), "n_turns": n_turns, "n_malformed": n_malformed,
        "n_identical_repeats": identical, "n_undeclared_tool": n_undeclared, "nudges": nudges,
        "compactions": compactions, "submit_patch_called": submit_called, "phase_reached": phase,
        "output_tokens": fm.get("total_completion_tokens"), "prompt_tokens": fm.get("total_prompt_tokens"),
        "thinking_tokens": fm.get("total_thinking_tokens"),   # not in the observed format; stays null
        "n_edit_fail": n_edit_fail, "n_edit_arg_loss": n_edit_arg_loss,
        "n_whole_file_reads": n_whole_reads,
        "tool_histogram": dict(Counter(c[0] for c in calls)),
    }


def find_trace(run_dir: Path, task_id: str, hint: str | None) -> Path | None:
    cands = []
    if hint:
        cands.append(Path(hint))
        cands.append(run_dir / "traces" / Path(hint).name)
    cands += [run_dir / "traces" / f"trace_{task_id}.json", run_dir / f"trace_{task_id}.json",
              run_dir / task_id / "traces" / f"trace_{task_id}.json"]
    for c in cands:
        if c.is_file():
            return c
    return None


def analyze_run(run_dir: Path, *, cap_minutes: float | None, max_calls: int | None,
                declared: set[str] | None = None) -> tuple[list[dict], dict]:
    declared = declared if declared is not None else set(R.HARNESS_TOOLS)
    results_path = run_dir / "task_results.jsonl"
    rows = load_jsonl(results_path) if results_path.is_file() else []
    if not rows:  # traces only
        for p in sorted(run_dir.rglob("trace_*.json")):
            rows.append({"instance_id": p.stem[len("trace_"):], "trace": str(p)})
    per_task: list[dict] = []
    for row in rows:
        task_id = str(_first(row, "instance_id", "task_id", "id", default="?"))
        cap = float(_first(row, "max_time_minutes", default=cap_minutes) or 0) or None
        mcalls = int(_first(row, "max_tool_calls", default=max_calls) or 0) or None
        wall = float(_first(row, "duration_s", "duration_seconds", "wall_s", default=0.0) or 0.0)
        patch = _first(row, "patch", "agent_patch", default=None)
        patch_chars = len(patch) if isinstance(patch, str) else int(row.get("patch_chars") or 0)
        err = str(_first(row, "error", "error_message", default="") or "")
        rec = {
            "task_id": task_id, "repo": row.get("repo"), "resolved": bool(row.get("resolved")),
            "patch_empty": patch_chars == 0, "wall_s": wall, "setup_s": row.get("setup_s"),
            "n_calls": row.get("tool_calls"), "n_turns": row.get("llm_calls"), "n_malformed": None,
            "n_identical_repeats": None, "n_undeclared_tool": None,
            "overflow_400": any(m.lower() in err.lower() for m in OVERFLOW_MARKERS),
            "nudges": None, "compactions": None, "phase_reached": None, "output_tokens": row.get("total_tokens") or None,
            "prompt_tokens": None, "thinking_tokens": None,
            "timeout_hit": any(m.lower() in err.lower() for m in TIMEOUT_MARKERS),
            "calls_cap_hit": None, "time_cap_hit": bool(cap and wall >= cap * 60 - 5),
            "n_edit_fail": None, "n_edit_arg_loss": None, "n_whole_file_reads": None,
            "scratch_in_patch": bool(isinstance(patch, str) and SCRATCH_RE.search(patch)),
            "submit_patch_called": None, "error": err[:200] or None, "trace": None,
        }
        tp = find_trace(run_dir, task_id, row.get("trace"))
        if tp is not None:
            try:
                tm = analyze_trace(json.loads(tp.read_text(encoding="utf-8")), declared=declared)
            except (ValueError, OSError) as exc:
                tm = {"trace_error": str(exc)}
            rec["trace"] = str(tp)
            for k, v in tm.items():
                if k == "tool_histogram":
                    rec[k] = v
                elif rec.get(k) is None or k in ("n_calls", "n_turns", "submit_patch_called"):
                    rec[k] = v
            if rec.get("n_calls") is not None and mcalls:
                rec["calls_cap_hit"] = rec["n_calls"] >= mcalls
        per_task.append(rec)
    agg = aggregate(per_task, cap_minutes=cap_minutes)
    return per_task, agg


def _rate(rows: list[dict], key: str) -> float | None:
    vals = [r[key] for r in rows if r.get(key) is not None]
    return (sum(1 for v in vals if v) / len(vals)) if vals else None


def aggregate(rows: list[dict], *, cap_minutes: float | None, n_hidden: int = R.EXPECTED_HIDDEN_TASKS,
              setup_default_s: float = R.ASSUMED_SETUP_MINUTES * 60) -> dict:
    n = len(rows)
    k = sum(1 for r in rows if r["resolved"])
    lo, hi = wilson(k, n)
    walls = sorted(r["wall_s"] for r in rows)
    setups = [r["setup_s"] for r in rows if r.get("setup_s") is not None]
    setup_s = st.mean(setups) if setups else setup_default_s
    total = sum(r["wall_s"] + (r["setup_s"] if r.get("setup_s") is not None else setup_default_s) for r in rows)
    by_repo: dict[str, dict] = {}
    for r in rows:
        d = by_repo.setdefault(str(r.get("repo")), {"n": 0, "resolved": 0})
        d["n"] += 1
        d["resolved"] += int(r["resolved"])
    agg = {
        "tasks": n, "resolved": k, "resolve_rate": k / n if n else None, "resolve_ci95": [lo, hi],
        "empty_patch_rate": _rate(rows, "patch_empty"), "timeout_rate": _rate(rows, "timeout_hit"),
        "time_cap_hit_rate": _rate(rows, "time_cap_hit"), "calls_cap_hit_rate": _rate(rows, "calls_cap_hit"),
        "overflow_rate": _rate(rows, "overflow_400"),
        "submit_patch_rate": _rate(rows, "submit_patch_called"),
        "scratch_in_patch_rate": _rate(rows, "scratch_in_patch"),
        "malformed_turn_rate": _ratio(rows, "n_malformed", "n_turns"),
        "spin_rate": _ratio(rows, "n_identical_repeats", "n_calls"),
        "edit_fail_rate": _ratio(rows, "n_edit_fail", "n_calls"),
        "edit_arg_loss_rate": _ratio(rows, "n_edit_arg_loss", "n_calls"),
        "median_wall_s": st.median(walls) if walls else None,
        "p90_wall_s": walls[max(0, int(round(0.9 * n)) - 1)] if walls else None,
        "mean_calls": _mean(rows, "n_calls"), "mean_output_tokens": _mean(rows, "output_tokens"),
        "nudges_total": sum(r["nudges"] or 0 for r in rows), "compactions_total": sum(r["compactions"] or 0 for r in rows),
        "phase_histogram": dict(Counter(str(r.get("phase_reached")) for r in rows)),
        "setup_s_used": setup_s, "setup_source": "measured" if setups else "assumed",
        "projected_12h_total_h": (total * n_hidden / n / 3600) if n else None,
        "worst_case_h": (n_hidden * (cap_minutes * 60 + setup_s) / 3600) if cap_minutes else None,
        "by_repo": by_repo,
    }
    return agg


def _ratio(rows: list[dict], num: str, den: str) -> float | None:
    nums = [r[num] for r in rows if r.get(num) is not None and r.get(den)]
    dens = [r[den] for r in rows if r.get(num) is not None and r.get(den)]
    return sum(nums) / sum(dens) if dens and sum(dens) else None


def _mean(rows: list[dict], key: str) -> float | None:
    vals = [r[key] for r in rows if r.get(key) is not None]
    return st.mean(vals) if vals else None


def render(per_task: list[dict], agg: dict) -> str:
    lines = [f"{'task':22s} {'res':3s} {'wall':>6s} {'calls':>5s} {'malf':>4s} {'rep':>3s} {'ovf':>3s} {'sub':>3s} phase"]
    for r in per_task:
        lines.append(f"{r['task_id'][:22]:22s} {'Y' if r['resolved'] else '.':3s} {r['wall_s']:6.0f} "
                     f"{str(r.get('n_calls') if r.get('n_calls') is not None else '-'):>5s} "
                     f"{str(r.get('n_malformed') if r.get('n_malformed') is not None else '-'):>4s} "
                     f"{str(r.get('n_identical_repeats') if r.get('n_identical_repeats') is not None else '-'):>3s} "
                     f"{'Y' if r.get('overflow_400') else '.':>3s} "
                     f"{'Y' if r.get('submit_patch_called') else '.':>3s} {r.get('phase_reached')}")
    def pct(v):
        return "n/a" if v is None else f"{100 * v:.1f}%"
    lo, hi = agg["resolve_ci95"]
    lines.append("")
    lines.append(f"resolved {agg['resolved']}/{agg['tasks']} = {pct(agg['resolve_rate'])} (Wilson 95% {100*lo:.0f}-{100*hi:.0f}%)")
    lines.append(f"empty patch {pct(agg['empty_patch_rate'])}  timeout {pct(agg['timeout_rate'])}  time-cap {pct(agg['time_cap_hit_rate'])}  "
                 f"calls-cap {pct(agg['calls_cap_hit_rate'])}  overflow {pct(agg['overflow_rate'])}  submit_patch {pct(agg['submit_patch_rate'])}")
    lines.append(f"malformed turns {pct(agg['malformed_turn_rate'])}  spin (repeat calls) {pct(agg['spin_rate'])}  "
                 f"edit failures {pct(agg['edit_fail_rate'])}  scratch-in-patch {pct(agg['scratch_in_patch_rate'])}")
    if agg["median_wall_s"] is not None:
        lines.append(f"wall median {agg['median_wall_s']/60:.2f} min, p90 {agg['p90_wall_s']/60:.2f} min; "
                     f"nudges {agg['nudges_total']}, compactions {agg['compactions_total']}; phases {agg['phase_histogram']}")
    if agg["projected_12h_total_h"] is not None:
        wc = f"{agg['worst_case_h']:.2f} h" if agg["worst_case_h"] is not None else "n/a (no cap)"
        lines.append(f"projected hidden-run total {agg['projected_12h_total_h']:.2f} h (setup {agg['setup_s_used']:.0f} s "
                     f"{agg['setup_source']}); worst case {wc}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--out", type=Path, help="directory for summary.jsonl + aggregates.json (default: run_dir)")
    ap.add_argument("--cap-minutes", type=float, help="max_time_minutes used in the run (for cap-hit + worst case)")
    ap.add_argument("--max-calls", type=int, help="max_tool_calls used in the run")
    ap.add_argument("--declared-tools", nargs="*", help="tool names declared in agent.yaml (default: 9 harness tools)")
    args = ap.parse_args(argv)
    declared = set(args.declared_tools) if args.declared_tools else None
    per_task, agg = analyze_run(args.run_dir, cap_minutes=args.cap_minutes, max_calls=args.max_calls, declared=declared)
    out = args.out or args.run_dir
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "summary.jsonl", "w", encoding="utf-8") as fh:
        for r in per_task:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    (out / "aggregates.json").write_text(json.dumps(agg, indent=2), encoding="utf-8")
    print(render(per_task, agg))
    print(f"\nwrote {out / 'summary.jsonl'} and {out / 'aggregates.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
