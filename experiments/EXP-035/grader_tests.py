"""EXP-035: the grader's failing tests on EXP-028 R/RH unresolved patches, split by whether the agent could see them.

Definitions are the ones pre-registered in experiments/EXP-035-grader-failing-tests-visibility.md section 2.
Reads runs/ and data/ (gitignored); writes counts only to --out, per-task rows to --rows (keep under runs/).
Run from the repo root as:
    python -I -X utf8 experiments/EXP-035/grader_tests.py --tasks data/raw/tasks.jsonl --snapshots data/local/snapshots \
        --out experiments/EXP-035/aggregates.json --rows runs/EXP-035/rows.jsonl --handcheck runs/EXP-035/handcheck
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import math
import random
import re
import tarfile
from collections import Counter
from pathlib import Path

ARMS = {"R": "runs/EXP-028-armR", "RH": "runs/EXP-028-armRH"}
EXP034_SUMMARY = "experiments/EXP-034/summary.jsonl"
EXPECTED_RFWF = {"R": 30, "RH": 27}


def load_mine():
    spec = importlib.util.spec_from_file_location("exp034_mine", "experiments/EXP-034/mine.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M = load_mine()


def load_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 3), round(c + h, 3)]


# ---------------------------------------------------------------- test patch
def tp_files(tp: str):
    """{path: {"created": bool, "removed": [old line], "runs": [(P, [lines])], "plus": [lines]}}"""
    lines = (tp or "").splitlines()
    out, i = {}, 0
    while i < len(lines):
        if lines[i].startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ "):
            old = lines[i][4:].strip()
            new = lines[i + 1][4:].strip()
            f = new[2:] if new.startswith("b/") else new
            hunks = []
            i += 2
            while i < len(lines) and not (lines[i].startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ ")):
                m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", lines[i])
                if m:
                    hunks.append([int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1), []])
                elif hunks and lines[i][:1] in " +-":
                    hunks[-1][2].append(lines[i])
                elif hunks and lines[i] == "":
                    hunks[-1][2].append(" ")
                i += 1
            created = old == "/dev/null" or (len(hunks) == 1 and hunks[0][0] == 0 and hunks[0][1] == 0)
            removed, runs, plus = [], [], []
            for start, olen, body in hunks:
                pos = start + 1 if olen == 0 else start
                cur = None
                for ln in body:
                    if ln[:1] == "+":
                        plus.append(ln[1:])
                        if cur is None:
                            cur = (pos, [])
                            runs.append(cur)
                        cur[1].append(ln[1:])
                        continue
                    cur = None
                    if ln[:1] == "-":
                        removed.append(pos)
                    pos += 1
            out[f] = {"created": created, "removed": removed, "runs": runs, "plus": plus}
        else:
            i += 1
    return out


def file_key(path: str, files: dict):
    p = M.norm_path(path)
    if p in files:
        return p
    for f in files:
        if p.endswith("/" + f) or f.endswith("/" + p):
            return f
    return None


# ---------------------------------------------------------------- snapshot
class Snap:
    def __init__(self, tgz: Path):
        self.tf = tarfile.open(tgz)
        self.members = {(m.name[2:] if m.name.startswith("./") else m.name): m for m in self.tf.getmembers()}
        self.top = {n.split("/", 1)[0] for n in self.members if n and n != "."}

    def read(self, path):
        m = self.members.get(path)
        if m is None or not m.isfile():
            return None
        return self.tf.extractfile(m).read().decode("utf-8", "replace")


def spans(src: str):
    """[(cls or None, name, start, end, col, is_module_level)]; None if the file does not parse."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    out = []

    def visit(node, cls, top):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                s = min([d.lineno for d in ch.decorator_list] + [ch.lineno])
                out.append((cls, ch.name, s, ch.end_lineno, ch.col_offset, top))
                visit(ch, cls, False)
            elif isinstance(ch, ast.ClassDef):
                visit(ch, ch.name, False)
            else:
                visit(ch, cls, top)

    visit(tree, None, True)
    return out


def blankish(line: str) -> bool:
    s = line.strip()
    return not s or s.startswith("#") or s.startswith("import ") or s.startswith("from ")


def span_changed(sp, fd):
    _c, _n, s, e, col, _t = sp
    if any(s <= L <= e for L in fd["removed"]):
        return True
    for P, lines in fd["runs"]:
        if s < P <= e:
            return True
        nb = [l for l in lines if l.strip()]
        if not nb:
            continue
        if P == s and nb[-1].lstrip().startswith("@"):
            return True
        if P == e + 1 and (len(nb[0]) - len(nb[0].lstrip())) > col:
            return True
    return False


def file_strict(src_lines, sps, fd):
    tsp = [sp for sp in sps if sp[1].startswith("test")]
    inside = lambda L: any(sp[2] <= L <= sp[3] for sp in tsp)
    for L in fd["removed"]:
        if not inside(L) and not blankish(src_lines[L - 1] if 0 < L <= len(src_lines) else ""):
            return False
    for P, lines in fd["runs"]:
        if any(sp[2] < P <= sp[3] for sp in tsp):
            continue
        if any(re.match(r"\s*(async\s+)?def test|\s*class Test", l) for l in lines):
            continue
        if not all(blankish(l) for l in lines):
            return False
    return True


def classify_test(tid, files, snap, cache, counters):
    """-> (cat, cat_diff, strict) with cat in a / c_added / c_changed / b / unlocated."""
    path, chain = tid
    name = chain[-1]
    cls = chain[-2] if len(chain) > 1 else None
    f = file_key(path, files)
    if f is None:
        return "a", "a", False
    fd = files[f]
    def_re = re.compile(r"^\s*(async\s+)?def " + re.escape(name) + r"\s*\(")
    plus_def = any(def_re.match(l) for l in fd["plus"])
    cat_diff = "c_added" if (fd["created"] or plus_def) else "b"
    if fd["created"]:
        return "c_added", cat_diff, False
    if f not in cache:
        src = snap.read(f)
        sps = spans(src) if src is not None else None
        if sps is None:
            counters["ast_fail_files"] += 1
        cache[f] = (src, sps, None)
    src, sps, strict = cache[f]
    if sps is None:  # diff-only fallback
        counters["diff_fallback_tests"] += 1
        return cat_diff, cat_diff, False
    if strict is None:
        strict = file_strict(src.splitlines(), sps, fd)
        cache[f] = (src, sps, strict)
    if cls:
        cand = [sp for sp in sps if sp[0] == cls and sp[1] == name]
    else:
        cand = [sp for sp in sps if sp[1] == name and sp[5]] or [sp for sp in sps if sp[1] == name]
    if not cand:
        return ("c_added" if plus_def else "unlocated"), cat_diff, False
    if any(span_changed(sp, fd) for sp in cand):
        return "c_changed", cat_diff, False
    return "b", cat_diff, strict


# ---------------------------------------------------------------- tail
ID_RE = re.compile(r"^(FAILED|ERROR) (\S[^\n]*?)$", re.M)
COUNT_RE = re.compile(r"\bin [\d.]+s\b")
EXC_RE = re.compile(r"^(?:E\s+)?(ModuleNotFoundError|ImportError|SyntaxError|IndentationError|NameError|AttributeError):\s*(.*)$", re.M)


def parse_tail(tail: str):
    t = tail or ""
    if "\nSTDERR:\n" in t:
        t = t[: t.rfind("\nSTDERR:\n")]
    lines = t.splitlines()
    if len(tail or "") >= 1500 and lines:
        lines = lines[1:]
    ids, file_errs, raw_ids = [], [], []
    for ln in lines:
        m = re.match(r"^(FAILED|ERROR) (.+)$", ln)
        if not m:
            continue
        rest = m.group(2)
        if "::" in rest:
            if ln not in raw_ids:  # pytest prints one summary line per failing node id, parameters included
                raw_ids.append(ln)
            core = rest.split(" - ", 1)[0]
            core = core.split("[", 1)[0]
            parts = core.split("::")
            tid = (M.norm_path(parts[0]), tuple(p.strip() for p in parts[1:] if p.strip()))
            if tid[1] and tid not in ids:
                ids.append(tid)
        else:
            p = rest.split(" - ", 1)[0].strip()
            if p.endswith(".py"):
                file_errs.append(p)
    count = None
    for ln in reversed(lines):
        if COUNT_RE.search(ln) and re.search(r"\b(passed|failed|errors?|skipped|no tests ran)\b", ln):
            count = ln
            break
    expected = None
    if count is not None:
        expected = sum(int(x) for x in re.findall(r"\b(\d+) failed\b", count)) + sum(int(x) for x in re.findall(r"\b(\d+) errors?\b", count))
    header = "short test summary info" in t
    interrupted = ("Interrupted:" in t and "during collection" in t) or bool(file_errs)
    # as written in section 2.2: ids cut at "[" and deduplicated, then counted (collapses parametrized cases)
    complete_as_written = header and expected is not None and len(ids) >= expected
    # corrected (section 7 item 1): count failing node ids with their parameters, deduplicated on the full id
    complete = header and expected is not None and len(raw_ids) >= expected
    return {"ids": ids, "file_errs": file_errs, "count_line": count is not None, "expected": expected,
            "header": header, "interrupted": interrupted, "complete": complete,
            "complete_as_written": complete_as_written, "n_raw_ids": len(raw_ids), "text": "\n".join(lines)}


def unreadable_cause(row, pt, snap, agent_files, tp_plus):
    if row.get("test_exit_code") == -1:
        return "u0"
    text = pt["text"]
    excs = EXC_RE.findall(text)
    for typ, msg in excs:
        if typ == "ModuleNotFoundError":
            m = re.search(r"No module named '([^']+)'", msg)
            if m:
                top = m.group(1).split(".")[0]
                if top not in snap.top and f"{top}.py" not in snap.top:
                    return "u1"
    for typ, msg in excs:
        if typ == "ImportError":
            m = re.search(r"cannot import name '([^']+)'", msg)
            if m and any(re.search(r"\b" + re.escape(m.group(1)) + r"\b", l) for l in tp_plus):
                return "u3"
    if excs and any(f and f in text for f in agent_files):
        return "u2"
    return "u5"


# ---------------------------------------------------------------- per task
def task_row(arm, tid, row, task, snap, trace_path, e34):
    files = tp_files(task.get("test_patch") or "")
    tp_plus = [l for fd in files.values() for l in fd["plus"]]
    agent_files = M.patch_files(row.get("patch") or "")
    pt = parse_tail(row.get("test_tail") or "")
    counters = Counter()
    cache = {}
    tests = []
    for t in pt["ids"]:
        cat, cat_diff, strict = classify_test(t, files, snap, cache, counters)
        tests.append({"id": t, "cat": cat, "cat_diff": cat_diff, "strict": strict})
    cats = [x["cat"] for x in tests]
    vis_tests = [x for x in tests if x["cat"] in ("a", "b")]
    form = ("timeout_or_apply" if row.get("test_exit_code") == -1 else
            "collection" if pt["interrupted"] and not pt["ids"] else
            "crash" if not pt["count_line"] and not pt["ids"] else
            "no_fail_shown" if not pt["ids"] else
            "complete" if pt["complete"] else "partial")
    def per_task(complete):
        if not pt["ids"]:
            return "unreadable"
        if vis_tests:
            return "visible"
        if complete and all(c.startswith("c_") for c in cats):
            return "hidden_only"
        return "unreadable"

    primary = per_task(pt["complete"])
    primary_as_written = per_task(pt["complete_as_written"])
    form_as_written = "partial" if (form == "complete" and not pt["complete_as_written"]) else form
    # post-hoc diagnostics (section 9): every failing file created by the test patch; installed copy of the repo package in the tail
    fail_files = {file_key(t[0], files) for t in pt["ids"]}
    all_created = bool(pt["ids"]) and None not in fail_files and all(files[f]["created"] for f in fail_files)
    pkg = (row.get("repo") or "").split("/")[-1].lower()
    site_pkg_in_tail = bool(pkg) and f"dist-packages/{pkg}/" in (row.get("test_tail") or "")
    s1 = "unreadable" if (primary == "visible" and not pt["complete"]) else primary
    if primary == "visible" and not any(x["strict"] or x["cat"] == "a" for x in vis_tests):
        s2 = "visible_nonstrict"
    else:
        s2 = primary
    cause = None
    if primary == "unreadable":
        cause = "u4" if pt["ids"] else unreadable_cause(row, pt, snap, agent_files, tp_plus)
    s3 = "visible" if (primary == "visible" or cause == "u2") else primary
    # did the agent run that file / any test after its last edit
    ran_file = None
    if primary == "visible":
        calls = M.calls_of(trace_path)
        pfiles = M.patch_files(row.get("patch") or "")
        edits = [i for i, (n, a, _o) in enumerate(calls) if M.is_edit(n, a, pfiles)]
        last = edits[-1] if edits else None
        vfiles = {x["id"][0] for x in vis_tests}
        ran_file = False
        if last is not None:
            for i, (n, a, _o) in enumerate(calls):
                if i <= last:
                    continue
                k, _sp = M.test_kind(n, a)
                if not k:
                    continue
                cmd = str(a.get("command") or "")
                if any(v in cmd or v.rsplit("/", 1)[-1] in cmd for v in vfiles):
                    ran_file = True
    return {
        "arm": arm, "task_id": tid, "exit": row.get("test_exit_code"), "form": form, "primary": primary,
        "form_as_written": form_as_written, "primary_as_written": primary_as_written,
        "all_fail_files_created": all_created, "site_pkg_in_tail": site_pkg_in_tail, "repo": row.get("repo"),
        "s1": s1, "s2": s2, "s3": s3, "cause": cause, "tests": [[x["id"][0], list(x["id"][1]), x["cat"], x["cat_diff"], x["strict"]] for x in tests],
        "ran_any_after": e34.get(f"tested_after_last_edit_{arm}"), "ran_file_after": ran_file,
        "last_pass_034": e34.get(f"last_visible_pass_{arm}"), "counters": dict(counters),
        "tail_len": len(row.get("test_tail") or ""), "has_tail": bool((row.get("test_tail") or "").strip()),
    }


def group_stats(rows):
    n = len(rows)
    pc = Counter(r["primary"] for r in rows)
    V, H, U = pc["visible"], pc["hidden_only"], pc["unreadable"]
    tc = Counter(t[2] for r in rows for t in r["tests"])
    agree = Counter((t[2] if t[2] in ("a", "b") else ("c" if t[2].startswith("c_") else t[2]),
                     t[3] if t[3] in ("a", "b") else "c") for r in rows for t in r["tests"])
    vis = [r for r in rows if r["primary"] == "visible"]
    return {
        "n": n, "visible": V, "hidden_only": H, "unreadable": U,
        "visible_share": round(V / n, 3) if n else None, "visible_wilson95": wilson(V, n),
        "hidden_only_share": round(H / n, 3) if n else None, "hidden_only_wilson95": wilson(H, n),
        "unreadable_share": round(U / n, 3) if n else None, "unreadable_wilson95": wilson(U, n),
        "hidden_share_of_readable": round(H / (V + H), 3) if V + H else None,
        "s1_literal": dict(sorted(Counter(r["s1"] for r in rows).items())),
        "s2_strict": dict(sorted(Counter(r["s2"] for r in rows).items())),
        "s3_broad": dict(sorted(Counter(r["s3"] for r in rows).items())),
        "unreadable_causes": dict(sorted(Counter(r["cause"] for r in rows if r["cause"]).items())),
        "tail_form": dict(sorted(Counter(r["form"] for r in rows).items())),
        "exit_codes": dict(sorted(Counter(str(r["exit"]) for r in rows).items())),
        "test_level": dict(sorted(tc.items())),
        "test_level_b_strict": sum(1 for r in rows for t in r["tests"] if t[2] == "b" and t[4]),
        "diff_only_vs_snapshot": {f"{k[0]}|{k[1]}": v for k, v in sorted(agree.items())},
        "as_written_primary": dict(sorted(Counter(r["primary_as_written"] for r in rows).items())),
        "as_written_tail_form": dict(sorted(Counter(r["form_as_written"] for r in rows).items())),
        "posthoc_unreadable_partial_all_fail_files_created": sum(1 for r in rows if r["primary"] == "unreadable" and r["cause"] == "u4" and r["all_fail_files_created"]),
        "posthoc_exit124_by_cause": dict(sorted(Counter(r["cause"] or r["primary"] for r in rows if r["exit"] == 124).items())),
        "posthoc_installed_repo_package_in_tail_by_primary": dict(sorted(Counter(r["primary"] for r in rows if r["site_pkg_in_tail"]).items())),
        "posthoc_primary_by_repo": {k: dict(sorted(Counter(r["primary"] for r in rows if r["repo"] == k).items())) for k in sorted({r["repo"] for r in rows})},
        "visible_ran_any_test_after_last_edit": sum(bool(r["ran_any_after"]) for r in vis),
        "visible_ran_that_file_after_last_edit": sum(bool(r["ran_file_after"]) for r in vis),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", type=Path, default=Path("data/raw/tasks.jsonl"))
    ap.add_argument("--snapshots", type=Path, default=Path("data/local/snapshots"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--rows", type=Path, required=True)
    ap.add_argument("--handcheck", type=Path, default=None)
    a = ap.parse_args()

    tasks = {t["instance_id"]: t for t in load_jsonl(a.tasks)}
    e34 = {r["task_id"]: r for r in load_jsonl(EXP034_SUMMARY)}
    allrows, agg, raw = [], {"arms": list(ARMS)}, {}
    snaps = {}
    for arm, d in ARMS.items():
        rows = {(r.get("instance_id") or r.get("task_id")): r for r in load_jsonl(Path(d) / "task_results.jsonl")}
        raw[arm] = rows
        out = []
        for tid, row in sorted(rows.items()):
            if row.get("resolved") or not (row.get("patch") or "").strip():
                continue
            task = tasks[tid]
            gold = M.patch_files(task.get("patch") or "")
            rfwf = (not bool(row.get("resolved"))) and bool(M.patch_files(row.get("patch") or "") & gold)
            if tid not in snaps:
                snaps[tid] = Snap(a.snapshots / f"{tid}.tgz")
            r = task_row(arm, tid, row, task, snaps[tid], Path(d) / "traces" / f"trace_{tid}.json", e34.get(tid, {}))
            r["rfwf"] = rfwf
            out.append(r)
        allrows += out
        rf = [r for r in out if r["rfwf"]]
        lastpass = [r for r in out if r["last_pass_034"]]
        agg[arm] = {
            "rfwf": group_stats(rf), "all_unresolved_nonempty": group_stats(out),
            "last_pass_034": {
                "n": len(lastpass), "n_rfwf": sum(r["rfwf"] for r in lastpass),
                "primary": dict(sorted(Counter(r["primary"] for r in lastpass).items())),
                "visible_with_that_file_run_after_last_edit": sum(1 for r in lastpass if r["primary"] == "visible" and r["ran_file_after"]),
            },
            "infra": {
                "rfwf_n": len(rf), "rfwf_expected_exp034": EXPECTED_RFWF[arm],
                "rfwf_missing_tail": sum(not r["has_tail"] for r in rf),
                "ast_fail_files": sum(r["counters"].get("ast_fail_files", 0) for r in out),
                "diff_fallback_tests": sum(r["counters"].get("diff_fallback_tests", 0) for r in out),
            },
        }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(agg, indent=2) + "\n", encoding="utf-8")
    a.rows.parent.mkdir(parents=True, exist_ok=True)
    with open(a.rows, "w", encoding="utf-8", newline="\n") as fh:
        for r in allrows:
            fh.write(json.dumps(r) + "\n")

    if a.handcheck:
        rng = random.Random(35)
        pool = sorted(((r["arm"], r["task_id"], r["exit"]) for r in allrows))
        strata = {"1": [p for p in pool if p[2] == 1], "2": [p for p in pool if p[2] == 2], "o": [p for p in pool if p[2] not in (1, 2)]}
        pick = []
        for s, k in (("1", 5), ("2", 3), ("o", 2)):
            got = rng.sample(strata[s], min(k, len(strata[s])))
            pick += got
        short = 10 - len(pick)
        if short > 0:
            rest = [p for p in strata["1"] if p not in pick]
            pick += rng.sample(rest, min(short, len(rest)))
        rng.shuffle(pick)
        a.handcheck.mkdir(parents=True, exist_ok=True)
        lab = {(r["arm"], r["task_id"]): r for r in allrows}
        with open(a.handcheck / "dossier.txt", "w", encoding="utf-8") as fh, open(a.handcheck / "key.txt", "w", encoding="utf-8") as kh:
            for i, (arm, tid, ex) in enumerate(pick):
                row = raw[arm][tid]
                files = tp_files(tasks[tid].get("test_patch") or "")
                fh.write(f"########## #{i} arm={arm} exit={ex} tail_len={len(row.get('test_tail') or '')}\n")
                fh.write("TEST PATCH FILES: " + ", ".join(f"{f}{' (created)' if v['created'] else ''}" for f, v in files.items()) + "\n")
                fh.write("----- TAIL -----\n" + (row.get("test_tail") or "") + "\n")
                fh.write("----- TEST PATCH -----\n" + (tasks[tid].get("test_patch") or "")[:15000] + "\n\n")
                r = lab[(arm, tid)]
                kh.write(f"#{i} {arm} {tid} {r['primary']} form={r['form']} cause={r['cause']} tests={[(t[0].rsplit('/',1)[-1], t[1][-1], t[2]) for t in r['tests']][:6]}\n")
    print(json.dumps({arm: {"infra": agg[arm]["infra"], "rfwf": {k: agg[arm]["rfwf"][k] for k in ("n", "visible", "hidden_only", "unreadable")}} for arm in ARMS}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
