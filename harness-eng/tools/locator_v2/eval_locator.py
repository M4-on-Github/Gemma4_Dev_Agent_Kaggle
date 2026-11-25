"""Offline evaluator for tools/locator_v2/locate.py (zero GPU, stdlib only, single process).

Usage (from harness-eng/):
  PY="env/py313-scorer/bin/python3.13 -I -W ignore"
  $PY tools/locator_v2/eval_locator.py prepare --scratch <dir> --cohort cohorts/A.txt [--cohort cohorts/B.txt]
  $PY tools/locator_v2/eval_locator.py run --scratch <dir> --cohort cohorts/A.txt --mode v2 [--tag name]
        [--frozen runs/_analysis/trace_vs_reference.frozen.jsonl] [--set NAME=VALUE ...]
  $PY tools/locator_v2/eval_locator.py clean --scratch <dir>

`prepare` unpacks the Python files of each task snapshot (base commit) to <scratch>/ws/<id>/. `run` runs the
locator in-process with cwd = that directory and the full issue text as --issue-file, then prints COUNTS AND RATES
ONLY. Per-task rows go to <scratch>/out/<tag>.jsonl and never anywhere else: tasks are competition data, so no
id, path, issue text or code is printed.

Gold, from the reference patch: gold files = non-test .py files it changes; gold symbols = the innermost
function/class (ast on the base file, old-file line numbers) enclosing each changed line. An inserted block
belongs to the innermost definition holding both old lines around it (a method added between two methods counts
for the class). Changes at module level have no gold symbol and are left out of the symbol metrics (the count of
such tasks is printed).
A listed symbol or related site covers a gold symbol when it is the same definition, or when it is a definition
of at most COVER_SPAN lines in the same file that contains the gold symbol's changed lines.
"""
import argparse
import ast
import collections
import contextlib
import io
import json
import os
import re
import runpy
import shutil
import sys
import tarfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
COVER_SPAN = 150
TST = re.compile(r"(^|/)(tests?|testing|docs?(_src)?)/|test_[^/]*\.py$|_test\.py$|conftest\.py$")
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def read_cohort(paths):
    ids = []
    for p in paths:
        for line in open(p):
            line = line.strip()
            if line and not line.startswith("#") and line not in ids:
                ids.append(line)
    return ids


def load_tasks(data, ids):
    want, out = set(ids), {}
    with open(os.path.join(data, "tasks.jsonl")) as fh:
        for line in fh:
            t = json.loads(line)
            if t["instance_id"] in want:
                out[t["instance_id"]] = t
    return out


def prepare(args):
    ids = read_cohort(args.cohort)
    for i, tid in enumerate(ids):
        d = os.path.join(args.scratch, "ws", tid)
        if os.path.isdir(os.path.join(d, ".git")):
            continue
        tmp = d + ".tmp"
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp)
        with tarfile.open(os.path.join(args.data, "snapshots", tid + ".tgz")) as tf:
            tf.extractall(tmp, members=[m for m in tf if m.isfile() and m.name.endswith(".py")
                                        and "/.git/" not in m.name], filter="data")
        os.makedirs(os.path.join(tmp, ".git"), exist_ok=True)
        os.rename(tmp, d)
        print("prepared %d/%d" % (i + 1, len(ids)), flush=True)


def changed_lines(patch):
    """{file: [sorted old-file sites touched]}. A removed line is (n, n); an insertion between old lines n-1 and n
    is (n-1, n), so its gold symbol is the innermost definition that holds both neighbours."""
    out, cur, old = collections.defaultdict(set), None, 0
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            cur = None
        elif line.startswith("--- "):
            p = line[4:].strip()
            cur = p[2:] if p.startswith("a/") else None
        elif line.startswith("+++ "):
            continue
        elif line.startswith("@@") and cur:
            m = HUNK.match(line)
            old = int(m.group(1)) if m else 0
        elif cur and old:
            if line.startswith("-"):
                out[cur].add((old, old))
                old += 1
            elif line.startswith("+"):
                out[cur].add((max(old - 1, 1), old))
            elif line.startswith(" ") or line == "":
                old += 1
    return {f: sorted(v) for f, v in out.items()}


def defs_of(src):
    """[(start, end, qualname)] for every function/class; start includes decorators."""
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError, RecursionError):
        return []
    out = []

    def walk(node, prefix):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                q = prefix + ch.name
                start = min([ch.lineno] + [d.lineno for d in ch.decorator_list])
                out.append((start, ch.end_lineno, q))
                walk(ch, q + ".")
            else:
                walk(ch, prefix)
    walk(tree, "")
    return out


def gold_of(task, ws):
    """gold files, gold symbols {(file, start, end): [changed lines]}, count of module-level changed lines."""
    files, syms, module_level = [], collections.defaultdict(list), 0
    for f, lines in changed_lines(task["patch"]).items():
        if not f.endswith(".py") or TST.search(f):
            continue
        files.append(f)
        try:
            src = open(os.path.join(ws, f), encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        defs = defs_of(src)
        nlines = src.count("\n") + 1
        for lo, hi in lines:
            hi = min(hi, nlines)
            inner = None
            for s, e, q in defs:
                if s <= lo and hi <= e and (inner is None or e - s < inner[1] - inner[0]):
                    inner = (s, e, q)
            if inner is None:
                module_level += 1
            else:
                syms[(f, inner[0], inner[1])].extend((max(lo, inner[0]), hi))
    return files, dict(syms), module_level


def covers(sites, gkey, glines):
    f, s, e = gkey
    for sf, ss, se in sites:
        if sf != f:
            continue
        if (ss, se) == (s, e):
            return True
        if se - ss + 1 <= COVER_SPAN and ss <= min(glines) and max(glines) <= se:
            return True
    return False


def run_locator(script, ws, issue_path, argv, overrides):
    g = runpy.run_path(script, run_name="__locator__")
    for k, v in overrides.items():
        g["main"].__globals__[k] = v
    buf, cwd = io.StringIO(), os.getcwd()
    os.chdir(ws)
    t0 = time.time()
    try:
        with contextlib.redirect_stdout(buf):
            res = g["main"](["--issue-file", issue_path] + argv, want_struct=True)
    finally:
        os.chdir(cwd)
    return buf.getvalue(), res, time.time() - t0


def pct(a, b):
    return "%d/%d (%.0f%%)" % (a, b, 100.0 * a / b) if b else "0/0"


_GOLD = {}


def evaluate(scratch, ids, tasks, argv, overrides):
    """Run the locator on every task; one row of counts per task (plus the printed text)."""
    script = os.path.join(HERE, "locate.py")
    issue_path = os.path.join(scratch, "issue.txt")
    rows = []
    for tid in ids:
        ws = os.path.join(scratch, "ws", tid)
        t = tasks[tid]
        with open(issue_path, "w", encoding="utf-8") as fh:
            fh.write(t["problem_statement"])
        if tid not in _GOLD:
            _GOLD[tid] = gold_of(t, ws)
        gfiles, gsyms, modlvl = _GOLD[tid]
        text, res, secs = run_locator(script, ws, issue_path, argv, overrides)
        files = res["files"]
        syms = [(s["file"], s["start"], s["end"]) for s in res["symbols"]]
        rel = [(s["file"], s["start"], s["end"]) for s in res["related"]]
        row = {"id": tid, "n_gold_files": len(gfiles), "n_gold_syms": len(gsyms), "module_level_lines": modlvl,
               "chars": len(text), "secs": secs, "n_related": len(rel),
               "file_rank": min([files.index(f) + 1 for f in gfiles if f in files], default=None),
               "all_files_at5": bool(gfiles) and all(f in files[:5] for f in gfiles)}
        hit_rank = None
        for i, s in enumerate(syms):
            if any(covers([s], k, v) for k, v in gsyms.items()):
                hit_rank = i + 1
                break
        row["sym_rank"] = hit_rank
        row["cov_syms"] = sum(covers(syms[:8], k, v) for k, v in gsyms.items())
        row["cov_syms_related"] = sum(covers(syms[:8] + rel, k, v) for k, v in gsyms.items())
        row["out"] = text
        rows.append(row)
    os.remove(issue_path)
    return rows


def run(args):
    ids = read_cohort(args.cohort)
    tasks = load_tasks(args.data, ids)
    overrides = {}
    for kv in args.set or []:
        k, v = kv.split("=", 1)
        overrides[k] = json.loads(v)
    os.makedirs(os.path.join(args.scratch, "out"), exist_ok=True)
    argv = ["--mode", args.mode, "--top-files", str(args.top_files), "--top-symbols", str(args.top_symbols)]
    if args.query_chars:
        argv += ["--query-chars", str(args.query_chars)]
    rows = evaluate(args.scratch, ids, tasks, argv, overrides)
    tag = args.tag or args.mode
    with open(os.path.join(args.scratch, "out", tag + ".jsonl"), "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    report(rows, tag, args)


def report(rows, tag, args):
    fr = [r for r in rows if r["n_gold_files"]]
    n = len(fr)
    print("== %s | cohort %s | tasks %d, with gold source file %d" % (
        tag, ",".join(os.path.basename(c) for c in args.cohort), len(rows), n))
    for k in (1, 3, 5):
        print("file recall@%d: %s" % (k, pct(sum(1 for r in fr if r["file_rank"] and r["file_rank"] <= k), n)))
    print("all gold files in top 5: %s" % pct(sum(r["all_files_at5"] for r in fr), n))
    sr = [r for r in rows if r["n_gold_syms"]]
    m = len(sr)
    print("tasks with a gold symbol: %d (left out, module-level only: %d)" % (m, n - m))
    for k in (1, 5, 8):
        print("symbol recall@%d: %s" % (k, pct(sum(1 for r in sr if r["sym_rank"] and r["sym_rank"] <= k), m)))

    def share(sub, key):
        return sum(r[key] / r["n_gold_syms"] for r in sub) / len(sub) if sub else float("nan")
    multi = [r for r in sr if r["n_gold_syms"] >= 2]
    print("mean share of gold symbols covered, top-8 symbols: all %.3f | >=2-symbol tasks (n=%d) %.3f" % (
        share(sr, "cov_syms"), len(multi), share(multi, "cov_syms")))
    print("mean share of gold symbols covered, top-8 + related: all %.3f | >=2-symbol tasks (n=%d) %.3f" % (
        share(sr, "cov_syms_related"), len(multi), share(multi, "cov_syms_related")))
    print(">=2-symbol tasks with ALL gold symbols covered (top-8 + related): %s" % pct(
        sum(1 for r in multi if r["cov_syms_related"] == r["n_gold_syms"]), len(multi)))
    ch = sorted(r["chars"] for r in rows)
    se = sorted(r["secs"] for r in rows)
    print("output chars: median %d, max %d | related sites per task: mean %.1f | seconds: median %.2f, max %.2f" % (
        ch[len(ch) // 2], ch[-1], sum(r["n_related"] for r in rows) / len(rows), se[len(se) // 2], se[-1]))
    if args.frozen and os.path.isfile(args.frozen):
        by = {r["id"]: r for r in rows}
        cls = collections.defaultdict(set)
        with open(args.frozen) as fh:
            for line in fh:
                d = json.loads(line)
                if d.get("model") == "31b" and not d.get("resolved") and d["instance_id"] in by:
                    if d.get("class") == "partial fix":
                        cls["partial multi-hunk"].add(d["instance_id"])
                    if d.get("class") == "no-edit/empty patch" and d.get("end") in ("time cap", "call cap"):
                        cls["no edit before cap"].add(d["instance_id"])
        for name in ("partial multi-hunk", "no edit before cap"):
            sub = [by[i] for i in sorted(cls[name])]
            ss = [r for r in sub if r["n_gold_syms"]]
            print("31B '%s' tasks in cohort: %d | gold file top-1 %d, top-5 %d | with gold symbol %d: any gold "
                  "symbol in top-8 %d, all gold symbols covered (top-8 + related) %d, mean share %.3f" % (
                      name, len(sub), sum(1 for r in sub if r["file_rank"] == 1),
                      sum(1 for r in sub if r["file_rank"] and r["file_rank"] <= 5), len(ss),
                      sum(1 for r in ss if r["sym_rank"] and r["sym_rank"] <= 8),
                      sum(1 for r in ss if r["cov_syms_related"] == r["n_gold_syms"]), share(ss, "cov_syms_related")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prepare", "run", "clean"])
    ap.add_argument("--data", default="data/raw")
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--cohort", action="append", default=[])
    ap.add_argument("--mode", default="v2")
    ap.add_argument("--tag")
    ap.add_argument("--top-files", type=int, default=5)
    ap.add_argument("--top-symbols", type=int, default=8)
    ap.add_argument("--query-chars", type=int, default=0)
    ap.add_argument("--frozen")
    ap.add_argument("--set", action="append")
    args = ap.parse_args()
    if args.cmd == "prepare":
        prepare(args)
    elif args.cmd == "clean":
        shutil.rmtree(os.path.join(args.scratch, "ws"), ignore_errors=True)
    else:
        run(args)


if __name__ == "__main__":
    main()
