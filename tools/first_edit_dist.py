"""First-edit turn distribution and tripwire-threshold sweep, per outcome cohort.

Companion to `tools/run_forensics.py`. Answers two questions that `forensics` only reports medians for:

  1. How separated are the outcome cohorts on the first-edit axis? (EXP-009 Part B3)
  2. For a candidate "force an edit by turn N" rule, how many empty-patch tasks does N fire on,
     and how many already-resolved tasks would it force to edit earlier than they did? (EXP-010)

It also runs the confound check that decides whether such a rule can work at all: among tasks that
produced a patch, does first-edit turn still predict resolution? If late editors never resolve, then
late editing is a symptom of poor localisation rather than a cause of failure, and the conversion
prior for a forced edit is the late-editor rate, not the overall 37.9%.

Usage:
    python tools/first_edit_dist.py                      # both default runs
    python tools/first_edit_dist.py <run_dir> [<run_dir> ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import run_forensics as rf  # noqa: E402

DEFAULT_RUNS = {
    "E0 (4.5min/45c)": ROOT / "runs/E0-dev48-baseline/runs/E0-dev48-baseline",
    "EXP-003 (8min/28c)": ROOT / "runs/exp003_public_budget_dev48/runs/EXP-003-public-budget-dev48",
}

BUCKETS = [(1, 10), (11, 18), (19, 25), (26, 99)]
SWEEP_N = (12, 14, 16, 18, 20, 22, 25, 28, 30)


def pct(xs: list[int], q: float) -> float:
    xs = sorted(xs)
    i = (len(xs) - 1) * q / 100.0
    lo = int(i)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def scan(run_dir: Path) -> list[tuple[str, int | None, int, bool, int]]:
    """-> [(task_id, first_edit_turn or None, n_edit_calls, resolved, patch_chars)]"""
    meta: dict[str, tuple[bool, int]] = {}
    results = run_dir / "task_results.jsonl"
    for line in results.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        tid = r.get("task_id") or r.get("instance_id")
        meta[tid] = (bool(r.get("resolved")), r.get("patch_chars", 0) or 0)

    rows = []
    for path in sorted((run_dir / "traces").glob("*.json")):
        tid = path.stem[len("trace_"):] if path.stem.startswith("trace_") else path.stem
        if tid not in meta:
            continue
        try:
            trace = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        first_edit = None
        n_edits = 0
        for idx, turn in enumerate(rf.turns_of(trace), start=1):
            hits = [n for n in (turn.get("tools") or []) if n in rf.EDIT_TOOLS]
            if hits:
                n_edits += len(hits)
                if first_edit is None:
                    first_edit = idx
        resolved, patch_chars = meta[tid]
        rows.append((tid, first_edit, n_edits, resolved, patch_chars))
    return rows


def cohort_of(resolved: bool, patch_chars: int) -> str:
    if resolved:
        return "resolved"
    return "patch-but-failed" if patch_chars > 0 else "empty-patch"


def render(name: str, rows: list, pool: dict) -> None:
    print("=" * 78)
    print(name)
    cohorts: dict[str, list] = {}
    for _tid, fe, _ne, resolved, pc in rows:
        cohorts.setdefault(cohort_of(resolved, pc), []).append(fe)

    print("\n  first-edit TURN distribution by outcome")
    print("  %-18s %4s %5s %5s %5s %5s %5s %5s  never" % ("cohort", "n", "min", "p25", "p50", "p75", "p90", "max"))
    for oc in ("resolved", "patch-but-failed", "empty-patch"):
        v = cohorts.get(oc, [])
        got = [x for x in v if x is not None]
        if not got:
            print("  %-18s %4d  (none ever edited)%28d" % (oc, len(v), len(v)))
            continue
        print("  %-18s %4d %5d %5.0f %5.0f %5.0f %5.0f %5d  %d" % (
            oc, len(v), min(got), pct(got, 25), pct(got, 50), pct(got, 75), pct(got, 90),
            max(got), len(v) - len(got)))

    # confound check: does late editing still convert?
    patched = [r for r in rows if r[1] is not None]
    print("\n  CONFOUND CHECK -- among tasks that edited at all, does first-edit turn predict resolution?")
    print("  %-12s %5s %9s %8s  %s" % ("first-edit", "n", "resolved", "rate", "n_edits median"))
    for lo, hi in BUCKETS:
        sub = [r for r in patched if lo <= r[1] <= hi]
        label = "%d-%d" % (lo, hi) if hi < 99 else "%d+" % lo
        if not sub:
            print("  %-12s %5d %9s %8s" % (label, 0, "-", "-"))
            continue
        res = sum(1 for r in sub if r[3])
        ne = sorted(r[2] for r in sub)
        print("  %-12s %5d %9d %7.1f%%  %d" % (label, len(sub), res, 100.0 * res / len(sub), ne[len(ne) // 2]))
        slot = pool.setdefault((lo, hi), [0, 0])
        slot[0] += len(sub)
        slot[1] += res

    # threshold sweep
    res_fe = [r[1] for r in rows if r[3]]
    emp_fe = [r[1] for r in rows if cohort_of(r[3], r[4]) == "empty-patch"]
    print("\n  tripwire sweep: resolved tasks forced to edit earlier than they did | empty-patch tasks it fires on")
    for n in SWEEP_N:
        disturbed = sum(1 for x in res_fe if x is not None and x > n)
        fires = sum(1 for x in emp_fe if x is None or x > n)
        print("    N=%-3d  disturbed %2d/%-2d resolved   fires on %2d/%-2d empty-patch"
              % (n, disturbed, len(res_fe), fires, len(emp_fe)))


def main(argv: list[str]) -> int:
    runs = {str(Path(a)): Path(a) for a in argv[1:]} or DEFAULT_RUNS
    pool: dict[tuple[int, int], list[int]] = {}
    for name, run_dir in runs.items():
        if not (run_dir / "task_results.jsonl").exists():
            print("skip (no task_results.jsonl): %s" % run_dir)
            continue
        render(name, scan(run_dir), pool)

    if len(runs) > 1 and pool:
        print("=" * 78)
        print("POOLED across runs")
        print("  %-12s %5s %9s %8s" % ("first-edit", "n", "resolved", "rate"))
        for (lo, hi), (n, k) in sorted(pool.items()):
            label = "%d-%d" % (lo, hi) if hi < 99 else "%d+" % lo
            print("  %-12s %5d %9d %7.1f%%" % (label, n, k, 100.0 * k / max(1, n)))
        tot_e = sum(v[0] for kk, v in pool.items() if kk[1] <= 25)
        res_e = sum(v[1] for kk, v in pool.items() if kk[1] <= 25)
        tot_l = sum(v[0] for kk, v in pool.items() if kk[0] > 25)
        res_l = sum(v[1] for kk, v in pool.items() if kk[0] > 25)
        print("\n  edited by turn 25 : %3d tasks, %2d resolved (%.1f%%)" % (tot_e, res_e, 100.0 * res_e / max(1, tot_e)))
        print("  edited after 25   : %3d tasks, %2d resolved (%.1f%%)" % (tot_l, res_l, 100.0 * res_l / max(1, tot_l)))
        print("\n  Fisher exact (early-vs-late x resolved-vs-not): p = %.4f"
              % rf.fisher_exact_2x2(res_e, tot_e - res_e, res_l, tot_l - res_l))
        print("\n  => if the late rate is far below the early rate, a forced edit's conversion prior is the")
        print("     LATE rate, not the overall patch-conversion rate: late editing is partly a symptom of")
        print("     poor localisation, not purely a cause of failure.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
