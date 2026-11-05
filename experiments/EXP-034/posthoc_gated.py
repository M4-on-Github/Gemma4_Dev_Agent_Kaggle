"""EXP-034 post-hoc lines required by the critic (experiments/EXP-034/critic.md, Required fixes 1-2).

Not pre-registered. It reuses mine.py's own loaders and Q2 functions and adds a single definition:

  gated task = a task where the as-run grader tail (`test_tail` in task_results.jsonl) of at least one of
  the six arms matches  No module named '?(inline_snapshot|dirty_equals)  (case-sensitive).

It writes counts only:
  - per arm, the number of tasks whose own tail shows the missing package, and the size of the union;
  - Q1 (per arm, union, best, union minus best; V and O) on the non-gated tasks, with resolved flags exactly
    as in mine.py (X003 from the EXP-004 v2 re-grade);
  - Arm R's and RH's RFWF group split into grader-blocked (that arm's own tail shows the missing package) and
    graded, each with its last-visible counts.
Run as:  python -I -X utf8 experiments/EXP-034/posthoc_gated.py --out experiments/EXP-034/posthoc_gated.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("exp034_mine", HERE / "mine.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

GATE_RE = re.compile(r"No module named '?(inline_snapshot|dirty_equals)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", type=Path, default=Path("data/raw/tasks.jsonl"))
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()

    gold = {t["instance_id"]: M.patch_files(t.get("patch") or "") for t in M.load_jsonl(a.tasks)}
    rows, res, pat = {}, {}, {}
    for arm, d in M.ARMS.items():
        rows[arm] = {(r.get("instance_id") or r.get("task_id")): r for r in M.load_jsonl(Path(d) / "task_results.jsonl")}
        res[arm] = {k: bool(v.get("resolved")) for k, v in rows[arm].items()}
        pat[arm] = {k: (v.get("patch") or "") for k, v in rows[arm].items()}
    res["X003"] = {r["instance_id"]: bool(r.get("resolved")) for r in M.load_jsonl(M.X003_REGRADE)}
    ids = sorted(set.intersection(*(set(res[k]) for k in M.ARMS)))

    blocked = {arm: {t for t in ids if GATE_RE.search(rows[arm][t].get("test_tail") or "")} for arm in M.ARMS}
    gated = set().union(*blocked.values())
    nongated = [t for t in ids if t not in gated]
    out = {
        "n_ids": len(ids),
        "gate_regex": GATE_RE.pattern,
        "blocked_per_arm": {k: len(v) for k, v in blocked.items()},
        "n_gated_union": len(gated),
        "gated_resolved_per_arm": {k: sum(res[k][t] for t in gated) for k in M.ARMS},
        "n_nongated": len(nongated),
    }

    def fam(arms, tids):
        per = {k: sum(res[k][t] for t in tids) for k in arms}
        union = sum(any(res[k][t] for k in arms) for t in tids)
        return {"per_arm": per, "union": union, "best": max(per.values()), "union_minus_best": union - max(per.values())}

    out["q1_nongated"] = {f: fam(arms, nongated) for f, arms in M.FAMILIES.items()}
    out["q1_all48_check"] = {f: fam(arms, ids) for f, arms in M.FAMILIES.items()}

    q2 = {}
    for arm in M.Q2_ARMS:
        trc = Path(M.ARMS[arm]) / "traces"
        grp = {"blocked": Counter(), "graded": Counter()}
        for t in ids:
            files = M.patch_files(pat[arm][t])
            if res[arm][t] or not (files & gold.get(t, set())):
                continue
            r = M.q2_task(trc / f"trace_{t}.json", files)
            lv = "fail" if r["last_vis"] in ("fail", "fail_text") else r["last_vis"]
            grp["blocked" if t in blocked[arm] else "graded"][lv or "none"] += 1
        q2[arm] = {g: {"n": sum(c.values()), "last_visible": dict(sorted(c.items()))} for g, c in grp.items()}
    out["rfwf_split"] = q2

    a.out.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
