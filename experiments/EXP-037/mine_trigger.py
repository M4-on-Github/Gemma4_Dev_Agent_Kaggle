"""EXP-037 zero-GPU trigger mining, done before the vendoring text was written (EXP-037 section 1).

For the 15 gated dev-48 tasks (EXP-034 posthoc_gated.py: as-run grader tail of any of six arms matches
GATE_RE), in each of the six arms on disk:
  - seen:      some tool result shown to the agent matches GATE_RE (and the call index of the first one);
  - pytest:    the agent ran pytest/unittest at all, and after its last source edit;
  - vendored:  the agent wrote a file whose path is <...>/inline_snapshot/... or <...>/dirty_equals/...
               (write_file / edit_file path, or a run_command that names such a path with a write verb);
  - in_patch:  the final patch adds such a path; under_tests: that path sits under a tests directory.
On the 33 non-gated tasks it counts vendoring writes and in-patch stand-ins (the harm baseline).

Separately, from the base-commit snapshots (data/local/snapshots/<id>.tgz) of all 48 ids it counts the tasks
whose repository has at least one file under a `tests/` directory that mentions either import name: the
reach of a proactive "search the tests directory for the two names" trigger.

Writes counts and ids only (allowlist as EXP-034/035/036).
Run as:  python -I -X utf8 experiments/EXP-037/mine_trigger.py --tasks data/raw/tasks.jsonl \
             --snapshots data/local/snapshots --cohort experiments/cohorts/dev-48.txt \
             --out experiments/EXP-037/trigger_mining.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import tarfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("exp034_mine", HERE.parent / "EXP-034" / "mine.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

GATE_RE = re.compile(r"No module named '?(inline_snapshot|dirty_equals)")
VENDOR_PATH_RE = re.compile(r"(?:^|/)(inline_snapshot|dirty_equals)(?:/|\.py\b)")
WRITE_VERB_RE = re.compile(r"\bmkdir\b|\bcat\s*>|>\s*\S*(?:inline_snapshot|dirty_equals)|\btee\b|\bcp\b|\.write\(|\bprintf\b|\becho\b")
NAME_RE = re.compile(r"\b(inline_snapshot|dirty_equals)\b")


def under_tests(p: str) -> bool:
    return bool(re.search(r"(?:^|/)tests?/", M.norm_path(p)))


def obs_text(o) -> str:
    _ec, _st, text = M.obs_fields(o)
    return text + "\n" + (o if isinstance(o, str) else json.dumps(o, default=str) if o is not None else "")


def vendor_writes(calls):
    """[(call index, path, under_tests)] for writes of a stand-in package."""
    out = []
    for i, (n, a, _o) in enumerate(calls):
        if n in ("write_file", "edit_file"):
            p = str(a.get("filepath") or a.get("path") or a.get("file_path") or "")
            if VENDOR_PATH_RE.search(M.norm_path(p)):
                out.append((i, M.norm_path(p), under_tests(p)))
        elif n == "run_command":
            cmd = str(a.get("command") or "")
            m = re.search(r"[\w./-]*(?:inline_snapshot|dirty_equals)(?:/[\w./-]*|\.py)", cmd)
            if m and WRITE_VERB_RE.search(cmd) and not re.search(r"\bgrep\b|\bimport\b", cmd.split("&&")[0]):
                out.append((i, M.norm_path(m.group(0)), under_tests(m.group(0))))
    return out


def patch_vendor_files(patch: str):
    return sorted(f for f in M.patch_files(patch) if VENDOR_PATH_RE.search(f))


def snapshot_reach(tgz: Path) -> dict:
    hit_files, n_test_py = 0, 0
    with tarfile.open(tgz) as tf:
        for m in tf:
            name = m.name
            if not m.isfile() or "/.git/" in name or not name.endswith(".py"):
                continue
            if not re.search(r"(?:^|/)tests?/", name):
                continue
            n_test_py += 1
            data = tf.extractfile(m).read().decode("utf-8", "replace")
            if NAME_RE.search(data):
                hit_files += 1
    return {"test_py_files": n_test_py, "files_naming_either": hit_files}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", type=Path, required=True)
    ap.add_argument("--snapshots", type=Path, required=True)
    ap.add_argument("--cohort", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()

    cohort = [l.strip() for l in a.cohort.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    gold = {t["instance_id"]: M.patch_files(t.get("patch") or "") for t in M.load_jsonl(a.tasks)}
    rows = {}
    for arm, d in M.ARMS.items():
        rows[arm] = {(r.get("instance_id") or r.get("task_id")): r for r in M.load_jsonl(Path(d) / "task_results.jsonl")}
    ids = sorted(set(cohort) & set.intersection(*(set(v) for v in rows.values())))
    blocked = {arm: {t for t in ids if GATE_RE.search(rows[arm][t].get("test_tail") or "")} for arm in M.ARMS}
    gated = sorted(set().union(*blocked.values()))
    nongated = [t for t in ids if t not in gated]

    per_arm = {}
    for arm, d in M.ARMS.items():
        trc = Path(d) / "traces"
        g = Counter()
        g_ids = {"seen": [], "vendored": [], "in_patch": [], "vendored_then_dropped": [], "resolved_as_run": []}
        first_seen, first_vendor, n_calls = [], [], []
        for t in gated:
            tp = trc / f"trace_{t}.json"
            if not tp.exists():
                g["missing_trace"] += 1
                continue
            calls = M.calls_of(tp)
            n_calls.append(len(calls))
            seen = [i for i, (_n, _a, o) in enumerate(calls) if GATE_RE.search(obs_text(o))]
            files = M.patch_files(rows[arm][t].get("patch") or "")
            src_files = {f for f in files if not VENDOR_PATH_RE.search(f)}
            edits = [i for i, (n, aa, _o) in enumerate(calls) if M.is_edit(n, aa, src_files)]
            tests = [i for i, (n, aa, _o) in enumerate(calls) if M.test_kind(n, aa)[0] == "suite"]
            vw = vendor_writes(calls)
            pv = patch_vendor_files(rows[arm][t].get("patch") or "")
            g["n"] += 1
            g["own_tail_blocked"] += t in blocked[arm]
            g["ran_pytest"] += bool(tests)
            g["ran_pytest_after_last_edit"] += bool(edits and tests and tests[-1] > edits[-1])
            g["no_source_edit"] += not edits
            if seen:
                g["seen"] += 1
                g_ids["seen"].append(t)
                first_seen.append(seen[0])
            if vw:
                g["vendored"] += 1
                g_ids["vendored"].append(t)
                first_vendor.append(vw[0][0])
                g["vendored_under_tests"] += any(x[2] for x in vw)
                g["vendored_without_seen"] += not seen
            if pv:
                g["in_patch"] += 1
                g_ids["in_patch"].append(t)
                g["in_patch_under_tests"] += any(under_tests(f) for f in pv)
            if vw and not pv:
                g["vendored_then_dropped"] += 1
                g_ids["vendored_then_dropped"].append(t)
            if rows[arm][t].get("resolved"):
                g["resolved_as_run"] += 1
                g_ids["resolved_as_run"].append(t)
            if seen and not vw:
                g["seen_not_vendored"] += 1
        ng = Counter()
        ng_ids = []
        for t in nongated:
            tp = trc / f"trace_{t}.json"
            if not tp.exists():
                continue
            calls = M.calls_of(tp)
            ng["n"] += 1
            ng["seen"] += any(GATE_RE.search(obs_text(o)) for (_n, _a, o) in calls)
            ng["vendored"] += bool(vendor_writes(calls))
            pv = patch_vendor_files(rows[arm][t].get("patch") or "")
            if pv:
                ng["in_patch"] += 1
                ng["in_patch_under_tests"] += any(under_tests(f) for f in pv)
                ng["in_patch_resolved"] += bool(rows[arm][t].get("resolved"))
                ng_ids.append(t)
        per_arm[arm] = {
            "gated": dict(sorted(g.items())),
            "gated_ids": g_ids,
            "first_seen_call_index": sorted(first_seen),
            "first_vendor_call_index": sorted(first_vendor),
            "gated_calls_per_task": sorted(n_calls),
            "nongated": dict(sorted(ng.items())),
            "nongated_in_patch_ids": ng_ids,
        }

    reach = {}
    for t in ids:
        tgz = a.snapshots / f"{t}.tgz"
        reach[t] = snapshot_reach(tgz) if tgz.exists() else None
    reach_hit = [t for t in ids if reach[t] and reach[t]["files_naming_either"] > 0]
    out = {
        "n_ids": len(ids),
        "gated_ids": gated,
        "n_gated": len(gated),
        "gate_regex": GATE_RE.pattern,
        "per_arm": per_arm,
        "snapshot_reach": {
            "rule": "base-commit file under a tests/ or test/ directory, .py, naming inline_snapshot or dirty_equals",
            "n_tasks_hit": len(reach_hit),
            "gated_hit": sorted(set(reach_hit) & set(gated)),
            "gated_miss": sorted(set(gated) - set(reach_hit)),
            "nongated_hit": sorted(set(reach_hit) - set(gated)),
            "snapshots_missing": [t for t in ids if reach[t] is None],
        },
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "per_arm"}, indent=1))
    for arm, v in per_arm.items():
        print(arm, json.dumps(v["gated"]), "first_seen", v["first_seen_call_index"], "first_vendor",
              v["first_vendor_call_index"], "nongated", json.dumps(v["nongated"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
