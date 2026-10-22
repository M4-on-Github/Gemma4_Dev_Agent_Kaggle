#!/usr/bin/env python3
"""Budget forensics and paired run comparison (plan.md §5.5).

Three questions `tools/analyze_traces.py` does not answer, all answerable offline from runs already on disk:

  forensics <run_dir>   Where did the per-task wall-clock budget actually go? Splits every task's elapsed
                        time across the tool called in each turn, classifies `run_command` by the shell
                        program invoked, and contrasts resolved / patch-but-failed / empty-patch cohorts on
                        turn count, seconds-per-turn, context size, and -- the decisive one -- the turn
                        index of the FIRST edit_file/write_file call.

  compare <runA> <runB> Paired per-task comparison of two runs over the same cohort. Reports the 2x2
                        concordance table, the exact McNemar two-sided p, and the discordant task ids.
                        Comparing marginal resolve rates hides that most of the "solved" set churns between
                        runs; this is the test that exposes it.

  lb <k1> <n1> <k2> <n2>
                        Is a leaderboard move signal? Wilson 95% CIs, Fisher exact two-sided p, and -- under
                        the pooled rate -- the probability two IDENTICAL runs differ by at least the observed
                        gap. Use this before reading any LB delta as an improvement.

Reads the layout tools/analyze_traces.py reads: <run_dir>/task_results.jsonl and <run_dir>/traces/trace_<id>.json.

Usage:
    python tools/run_forensics.py forensics runs/E0-dev48-baseline/runs/E0-dev48-baseline
    python tools/run_forensics.py compare RUN_A RUN_B
    python tools/run_forensics.py lb 4 58 7 58
"""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

EDIT_TOOLS = ("edit_file", "write_file")

# Classify a run_command invocation by the program it runs. ORDER MATTERS, in two ways:
#
#   1. `heredoc-write` must stay first. The system prompt tells the agent to write scratch repro
#      scripts as `cat > /tmp/repro.py <<EOF ...`, which starts with `cat` and would otherwise be
#      counted as a *read* by the `shell-read` rule. Before 2026-10-21 it was, and 410 of 441
#      "sed/cat/head" calls across E0 + EXP-003 were in fact heredoc writes -- which inverted the
#      headline of the run forensics. See Part C1 of
#      experiments/EXP-009-lb-variance-and-trace-forensics.md.
#   2. `pytest` must stay after `heredoc-write` (and before `python`). The pattern is deliberately
#      unanchored so `python -m pytest` matches, but that also means a heredoc whose script *body*
#      mentions pytest would be scored as a test run. That was 7 further calls.
#
# Known limitation, measured and accepted: the `python` pattern is anchored at the start of the
# command, so a wrapped invocation such as `timeout 5 python /tmp/repro.py` falls through to
# "other". That is 1 call in ~1,500 across both dev-48 runs, so it is left alone rather than
# regenerating the evidence files; do not rely on these labels for exact invocation counts.
# A command is labelled by the FIRST pattern it matches, not by every program it runs, so a
# compound command (`cat > f <<EOF ... && python f`) is attributed wholly to the heredoc write.
CMD_CLASSES = (
    ("heredoc-write", r"<<|^\s*sed\s+-i\b|^\s*(cat|tee)\b[^>]*>"),
    ("pytest", r"pytest"),
    ("grep/rg", r"^\s*(grep|rg|egrep|git\s+grep)\b"),
    ("shell-read", r"^\s*(sed|awk|cat|head|tail|wc)\b"),
    ("python", r"^\s*python"),
    ("find/ls", r"^\s*(find|ls|tree)\b"),
    ("git", r"^\s*git\b"),
)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((centre - margin) / d, (centre + margin) / d)


def classify_command(cmd: str) -> str:
    c = cmd.strip().strip('"').strip("'").lower()
    for label, pattern in CMD_CLASSES:
        if re.search(pattern, c):
            return label
    return "other"


def command_of(tool_call: dict) -> str:
    args = tool_call.get("arguments")
    if isinstance(args, dict):
        return str(args.get("command") or args)
    return str(args or "")


def results_by_id(run_dir: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for row in load_jsonl(run_dir / "task_results.jsonl"):
        tid = row.get("instance_id") or row.get("task_id")
        if tid:
            out[tid] = row
    return out


def turns_of(trace: dict) -> list[dict]:
    """Collapse trace steps into turns. Steps emitted by one LLM call share an `elapsed_s`."""
    turns: list[dict] = []
    for step in trace.get("steps", []):
        extra = step.get("extra") or {}
        elapsed = extra.get("elapsed_s")
        if elapsed is None:
            continue
        calls = step.get("tool_calls") or []
        tools = [tc.get("function_name") for tc in calls if tc.get("function_name")]
        commands = [command_of(tc) for tc in calls if tc.get("function_name") == "run_command"]
        metrics = step.get("metrics") or {}
        if turns and abs(turns[-1]["elapsed"] - elapsed) < 1e-9:
            turns[-1]["tools"].extend(tools)
            turns[-1]["commands"].extend(commands)
            turns[-1]["prompt_tokens"] = turns[-1]["prompt_tokens"] or metrics.get("prompt_tokens")
            turns[-1]["completion_tokens"] = turns[-1]["completion_tokens"] or metrics.get("completion_tokens")
        else:
            turns.append({
                "elapsed": elapsed,
                "tools": tools,
                "commands": commands,
                "prompt_tokens": metrics.get("prompt_tokens"),
                "completion_tokens": metrics.get("completion_tokens"),
            })
    return turns


def collect_forensics(run_dir: Path) -> dict:
    res = results_by_id(run_dir)
    tool_seconds: dict[str, list[float]] = defaultdict(list)
    cmd_seconds: dict[str, list[float]] = defaultdict(list)
    cmd_counts: Counter = Counter()
    per_task: dict[str, dict] = {}

    for trace_path in sorted((run_dir / "traces").glob("trace_*.json")):
        tid = trace_path.name[len("trace_"):-len(".json")]
        if tid not in res:
            continue
        turns = turns_of(json.loads(trace_path.read_text(encoding="utf-8")))
        prev = 0.0
        first_edit = None
        n_edits = 0
        for idx, turn in enumerate(turns, start=1):
            dt = turn["elapsed"] - prev
            prev = turn["elapsed"]
            tools = turn["tools"] or ["<no-tool>"]
            share = dt / len(tools)
            for tool in tools:
                tool_seconds[tool].append(share)
                if tool in EDIT_TOOLS:
                    n_edits += 1
                    if first_edit is None:
                        first_edit = idx
            for cmd in turn["commands"]:
                label = classify_command(cmd)
                cmd_counts[label] += 1
                cmd_seconds[label].append(share)
        prompts = [t["prompt_tokens"] for t in turns if t["prompt_tokens"]]
        row = res[tid]
        per_task[tid] = {
            "n_turns": len(turns),
            "total_s": turns[-1]["elapsed"] if turns else 0.0,
            "s_per_turn": (turns[-1]["elapsed"] / len(turns)) if turns else 0.0,
            "max_prompt_tokens": max(prompts) if prompts else 0,
            "completion_tokens": sum(t["completion_tokens"] or 0 for t in turns),
            "first_edit_turn": first_edit,
            "n_edits": n_edits,
            "resolved": bool(row.get("resolved")),
            "empty": (row.get("patch_chars") == 0) or not row.get("patch"),
        }
    return {
        "tool_seconds": tool_seconds,
        "cmd_seconds": cmd_seconds,
        "cmd_counts": cmd_counts,
        "per_task": per_task,
    }


def render_forensics(run_dir: Path, f: dict) -> str:
    tool_seconds = f["tool_seconds"]
    cmd_seconds = f["cmd_seconds"]
    cmd_counts = f["cmd_counts"]
    per_task = f["per_task"]
    total = sum(sum(v) for v in tool_seconds.values()) or 1.0
    out = [f"# budget forensics: {run_dir}",
           f"tasks={len(per_task)}  total agent wall={total / 60:.1f} min", ""]

    out.append("## where the wall-clock goes, by tool")
    out.append(f"{'tool':16s} {'calls':>6s} {'total_min':>10s} {'share':>7s} {'median_s':>9s} {'p90_s':>8s}")
    for tool, vals in sorted(tool_seconds.items(), key=lambda kv: -sum(kv[1])):
        p90 = sorted(vals)[max(0, int(0.9 * len(vals)) - 1)]
        out.append(f"{tool:16s} {len(vals):6d} {sum(vals) / 60:10.1f} {sum(vals) / total:6.1%} "
                   f"{st.median(vals):9.2f} {p90:8.2f}")

    if cmd_counts:
        out += ["", "## run_command composition (by program invoked)"]
        ctotal = sum(sum(v) for v in cmd_seconds.values()) or 1.0
        out.append(f"{'program':16s} {'calls':>6s} {'total_min':>10s} {'share_of_rc':>12s} {'median_s':>9s}")
        for label, n in cmd_counts.most_common():
            vals = cmd_seconds[label]
            out.append(f"{label:16s} {n:6d} {sum(vals) / 60:10.1f} {sum(vals) / ctotal:11.1%} "
                       f"{st.median(vals):9.2f}")

    out += ["", "## outcome cohorts"]
    cohorts = (
        ("resolved", lambda d: d["resolved"]),
        ("patch-but-failed", lambda d: not d["resolved"] and not d["empty"]),
        ("empty-patch", lambda d: d["empty"]),
    )
    out.append(f"{'cohort':18s} {'n':>3s} {'turns':>7s} {'s/turn':>7s} {'max_prompt_tok':>15s} "
               f"{'first_edit':>11s} {'n_edits':>8s}")
    for label, pred in cohorts:
        g = [d for d in per_task.values() if pred(d)]
        if not g:
            continue
        fe = [d["first_edit_turn"] for d in g if d["first_edit_turn"]]
        median_fe = st.median(fe) if fe else float("nan")
        out.append(f"{label:18s} {len(g):3d} {st.median([d['n_turns'] for d in g]):7.1f} "
                   f"{st.median([d['s_per_turn'] for d in g]):7.2f} "
                   f"{st.median([d['max_prompt_tokens'] for d in g]):15,.0f} "
                   f"{median_fe:11.1f} {st.median([d['n_edits'] for d in g]):8.1f}")

    never = sorted(t for t, d in per_task.items() if d["n_edits"] == 0)
    out += ["", f"tasks that never called {' or '.join(EDIT_TOOLS)}: {len(never)}/{len(per_task)}"]
    if never:
        out.append("  " + " ".join(never))
    return "\n".join(out)


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar: binomial sign test over the b+c discordant pairs."""
    n = b + c
    if n == 0:
        return float("nan")
    tail = sum(math.comb(n, k) for k in range(0, min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def render_compare(a_dir: Path, b_dir: Path) -> str:
    A, B = results_by_id(a_dir), results_by_id(b_dir)
    common = sorted(set(A) & set(B))
    both = only_a = only_b = neither = 0
    da: list[str] = []
    db: list[str] = []
    for tid in common:
        ra, rb = bool(A[tid].get("resolved")), bool(B[tid].get("resolved"))
        if ra and rb:
            both += 1
        elif ra:
            only_a += 1
            da.append(tid)
        elif rb:
            only_b += 1
            db.append(tid)
        else:
            neither += 1
    union = both + only_a + only_b
    out = [f"# paired comparison over {len(common)} shared tasks",
           f"A = {a_dir}",
           f"B = {b_dir}", "",
           f"both resolved : {both}",
           f"A only        : {only_a}  {' '.join(da)}",
           f"B only        : {only_b}  {' '.join(db)}",
           f"neither       : {neither}", "",
           f"A total {both + only_a}/{len(common)}   B total {both + only_b}/{len(common)}",
           f"discordant pairs: {only_a + only_b}   exact McNemar two-sided p = {mcnemar_exact(only_a, only_b):.4f}"]
    if union:
        out.append(f"concordance of the solved set: {both}/{union} = {both / union:.1%} of tasks solved by "
                   f"either run were solved by BOTH")
    return "\n".join(out)


def fisher_exact_2x2(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p for [[a,b],[c,d]]: sum tables no more likely than the observed one."""
    n, row1, col1 = a + b + c + d, a + b, a + c

    def prob(x: int) -> float:
        return (math.comb(row1, x) * math.comb(n - row1, col1 - x)) / math.comb(n, col1)

    p_obs = prob(a)
    lo, hi = max(0, col1 - (n - row1)), min(row1, col1)
    return min(1.0, sum(prob(x) for x in range(lo, hi + 1) if prob(x) <= p_obs + 1e-12))


def render_lb(k1: int, n1: int, k2: int, n2: int) -> str:
    out = ["# leaderboard move: signal or noise?"]
    for k, n, label in ((k1, n1, "run 1"), (k2, n2, "run 2")):
        lo, hi = wilson(k, n)
        out.append(f"{label}: {k}/{n} = {k / n:.4f}   Wilson 95% [{lo:.3f}, {hi:.3f}]")
    out += ["", f"Fisher exact two-sided p = {fisher_exact_2x2(k1, n1 - k1, k2, n2 - k2):.4f}"]
    pooled = (k1 + k2) / (n1 + n2)
    gap = abs(k1 - k2)
    pmf1 = [math.comb(n1, k) * pooled ** k * (1 - pooled) ** (n1 - k) for k in range(n1 + 1)]
    pmf2 = [math.comb(n2, k) * pooled ** k * (1 - pooled) ** (n2 - k) for k in range(n2 + 1)]
    p_gap = sum(pmf1[i] * pmf2[j]
                for i in range(n1 + 1) for j in range(n2 + 1) if abs(i - j) >= gap)
    sd = math.sqrt(n1 * pooled * (1 - pooled))
    out += [f"pooled rate = {pooled:.4f} ({pooled * n1:.2f} tasks of {n1}); binomial sd = {sd:.2f} tasks",
            f"P(two IDENTICAL runs differ by >= {gap} tasks) = {p_gap:.3f}"]
    if p_gap >= 0.05:
        out.append(f"=> a {gap}-task move is NOT signal: identical configs reproduce it "
                   f"{p_gap:.0%} of the time.")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("forensics", help="where a run's wall-clock budget went")
    f.add_argument("run_dir", type=Path)
    f.add_argument("--out", type=Path, help="also write the report to this path")
    c = sub.add_parser("compare", help="paired per-task comparison of two runs")
    c.add_argument("run_a", type=Path)
    c.add_argument("run_b", type=Path)
    lb = sub.add_parser("lb", help="is an LB move signal?")
    for name in ("k1", "n1", "k2", "n2"):
        lb.add_argument(name, type=int)
    args = ap.parse_args(argv)

    if args.cmd == "forensics":
        report = render_forensics(args.run_dir, collect_forensics(args.run_dir))
    elif args.cmd == "compare":
        report = render_compare(args.run_a, args.run_b)
    else:
        report = render_lb(args.k1, args.n1, args.k2, args.n2)
    print(report)
    if getattr(args, "out", None):
        args.out.write_text(report + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
