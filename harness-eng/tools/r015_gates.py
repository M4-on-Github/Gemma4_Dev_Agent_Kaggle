"""R-015 draw-level counts (readings 3-4), counts only.

  python3 -I tools/r015_gates.py R-015-31b-example-d1 [R-008-31b-base-te-d1 ...]

Arguments are run names under runs/. For each run it prints, as JSON: rows, resolved, mean task wall, the projected
Kaggle hours (10.04 h x mean wall / 361 s, the R-014 rule), empty patches, time-cap and call-cap task-draws, the
worked-example leak count, and the call-level mechanism numbers computed with the conventions of
tools/sizing/locate_31b.py (first edit attempt call; calls from the first naming of the file that is first edited
to that edit). Never prints trace, task or code text.
"""
import json
import os
import re
import statistics
import sys

HE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HE, "tools", "sizing"))
import locate_31b as L  # noqa: E402

# Names that exist only in the prompt's made-up example (trees/31b-r015-example/prompts/system.md, section 5).
LEAK = re.compile(r"ledgerkit|format_amount")
BASE_WALL_S = 361.0
BASE_HOURS = 10.04


def leak(run_dir, row):
    """True if any tool-call argument or the patch names the example. The system prompt itself is not searched."""
    if LEAK.search(row.get("patch") or ""):
        return True
    p = os.path.join(run_dir, "traces", f"trace_{row['instance_id']}.json")
    if not os.path.exists(p):
        return False
    for s in json.load(open(p)).get("steps", []):
        if s.get("source") != "agent":
            continue
        for tc in s.get("tool_calls") or []:
            if LEAK.search(json.dumps(tc.get("arguments") or {})):
                return True
    return False


def med(xs):
    return statistics.median(xs) if xs else None


def one(run):
    run_dir = os.path.join(HE, "runs", run)
    rows = [json.loads(l) for l in open(os.path.join(run_dir, "task_results.jsonl"))]
    walls = [r["task_wall_s"] for r in rows if r.get("task_wall_s") is not None]
    first, gaps, gaps_res, gaps_unres, clocks = [], [], [], [], []
    no_attempt = 0
    for r in rows:
        cs = L.parse(run, r)
        fe = next((c for c in cs if c["edit"]), None)
        if fe is None:
            no_attempt += 1
            continue
        first.append(fe["i"])
        clocks.append(fe["clock"])
        pre = [c for c in cs if c["i"] < fe["i"]]
        tgt = fe["path"]
        named = [c["i"] for c in pre if (tgt and tgt in (c.get("out") or "")) or
                 (c["cls"] in ("READ", "SHREAD") and c["path"] == tgt)]
        if named:
            g = fe["i"] - named[0]
            gaps.append(g)
            (gaps_res if r["resolved"] else gaps_unres).append(g)
    mean_wall = statistics.mean(walls) if walls else None
    return dict(
        run=run, rows=len(rows), resolved=sum(bool(r["resolved"]) for r in rows),
        mean_wall_s=round(mean_wall, 1) if mean_wall else None,
        projected_h=round(BASE_HOURS * mean_wall / BASE_WALL_S, 2) if mean_wall else None,
        empty_patch=sum(1 for r in rows if not (r.get("patch") or "").strip()),
        time_cap=sum("timeout" in (r.get("error") or "") for r in rows),
        call_cap=sum((r.get("tool_calls") or 0) >= L.CAP_CALLS for r in rows),
        non_success=sum(1 for r in rows if r.get("status") not in (None, "SUCCESS")),
        example_leak_tasks=sum(leak(run_dir, r) for r in rows),
        no_edit_attempt=no_attempt,
        first_edit_call_median=med(first),
        first_edit_clock_median_s=round(med(clocks), 1) if clocks else None,
        named_to_edit_median=med(gaps), named_to_edit_median_resolved=med(gaps_res),
        named_to_edit_median_unresolved=med(gaps_unres), named_to_edit_n=len(gaps),
    )


if __name__ == "__main__":
    for run in sys.argv[1:]:
        print(json.dumps(one(run)))
