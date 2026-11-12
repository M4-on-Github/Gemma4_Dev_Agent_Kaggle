#!/usr/bin/env python3
"""EXP-076 desk check and endpoint counter (zero GPU): the E4B single loop's first call and its searches.

Per task of one run directory (default EXP-038 dev-48):
  first      the first native tool call: read_file, edit_file, ..., or run_command:<program> (git subcommand kept)
  opener     the first call is a search (run_command whose program is grep or rg, or git grep) and its pattern
             (first non-option word after the program or subcommand, quotes removed) occurs in the problem
             statement, at least 4 characters long ("quoted from the issue")
  searches   search calls before the first edit_file / write_file, and how many of them have an issue pattern
  shown      a gold source file's path or basename appears in a tool observation before the first edit
             (EXP-074 section 7 point 2 definition: gold_seen by path, or by basename)
  class      EXP-074 diag.classify at margin 5 (lowercase when resolved)
Prints ids, program names, counts, class letters and y/n flags only (no pattern text, no file text).
Usage: python -I -X utf8 experiments/EXP-076/desk.py [run-name]
"""
from __future__ import annotations

import collections
import json
import re
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "EXP-074"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-063"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-075"))
import diag  # noqa: E402
import noise  # noqa: E402
import refs  # noqa: E402


def words(cmd: str) -> list[str]:
    try:
        return shlex.split(cmd)
    except ValueError:
        return cmd.split()


def search_pattern(cmd: str) -> tuple[str, str | None]:
    """(program, pattern) for the first pipeline segment; pattern None when not a search."""
    seg = re.split(r"\|\||&&|\||;", cmd, maxsplit=1)[0]
    w = words(seg)
    while w and (re.match(r"^\w+=", w[0]) or w[0] in ("cd", "env", "time")):
        w = w[2:] if w[0] == "cd" else w[1:]
    if not w:
        return "", None
    prog = Path(w[0].split()[0]).name if w[0].split() else ""
    rest = w[1:]
    if prog == "git" and rest:
        prog = "git " + rest[0]
        rest = rest[1:]
    if prog not in ("grep", "rg", "git grep", "egrep"):
        return prog, None
    pat = None
    skip_next = False
    for x in rest:
        if skip_next:
            skip_next = False
            continue
        if x in ("-e", "--regexp"):
            skip_next = False
            continue
        if x in ("-A", "-B", "-C", "-m", "--include", "--exclude", "-g", "-t"):
            skip_next = True
            continue
        if x.startswith("-"):
            continue
        pat = x
        break
    return prog, pat


def in_issue(pat: str | None, ps: str) -> bool:
    if not pat:
        return False
    p = pat.replace("\\b", "").replace("\\", "").strip("^$")
    return len(p) >= 4 and p in ps


def task(rd: Path, tid: str, ps: str, gold_files: list[str]) -> dict:
    steps = json.load(open(rd / "traces" / f"trace_{tid}.json", encoding="utf-8")).get("steps") or []
    first = None
    opener = False
    n_search = n_issue = 0
    edited = False
    shown = False
    gb = {Path(f).name for f in gold_files}
    pats: list[tuple[str, bool, str]] = []
    for s in steps:
        if s.get("source") != "agent":
            continue
        obs = str((s.get("observation") or {}).get("content") or "")
        for tc in s.get("tool_calls") or []:
            fn = str(tc.get("function_name") or tc.get("name") or "")
            ar = refs.args_of(tc)
            kind = fn
            pat = None
            if fn == "run_command":
                prog, pat = search_pattern(str(ar.get("command") or ""))
                kind = f"run_command:{prog}"
            if first is None:
                first = kind
                opener = pat is not None and in_issue(pat, ps)
            if fn in ("edit_file", "write_file"):
                edited = True
            if not edited and pat is not None:
                n_search += 1
                n_issue += in_issue(pat, ps)
                pats.append((pat, in_issue(pat, ps), obs))
        if not edited and not shown:
            shown = any(g in obs for g in gold_files) or any(b in obs for b in gb)
    # issue-pattern searches before the edit: does a gold file at the base commit hold the pattern (literal), and
    # did that search's own output name a gold file?
    snap = diag.snapshot(tid)
    gold_text = [v for k, v in snap.items() if any(diag.same_file(k, g) for g in gold_files)]
    hold = any(ok and any(pp.replace("\\", "") in v for v in gold_text) for pp, ok, _ in pats)
    hit = any(ok and (any(g in o for g in gold_files) or any(b in o for b in gb)) for pp, ok, o in pats)
    return {"first": first or "none", "opener": opener, "searches": n_search, "issue_searches": n_issue,
            "shown": shown, "gold_holds_issue_pattern": hold, "issue_search_shows_gold": hit}


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "EXP-038-e4b-dev48"
    tasks = {json.loads(l)["instance_id"]: json.loads(l) for l in open(ROOT / "data/raw/tasks.jsonl", encoding="utf-8")}
    rd = noise.run_dir(name)
    cls = noise.classes(name, tasks)
    tot = collections.Counter()
    by_cls = collections.defaultdict(collections.Counter)
    firsts = collections.Counter()
    for tid in sorted(cls):
        g = tasks[tid]
        gf = list(diag.gold_regions(g["patch"], 5))
        t = task(rd, tid, g.get("problem_statement") or "", gf)
        c = cls[tid].upper()
        firsts[t["first"]] += 1
        for k in ("opener", "shown", "gold_holds_issue_pattern", "issue_search_shows_gold"):
            tot[k] += t[k]
            by_cls[c][k] += t[k]
        tot["any_issue_search"] += t["issue_searches"] > 0
        by_cls[c]["any_issue_search"] += t["issue_searches"] > 0
        by_cls[c]["n"] += 1
        print(f"{tid:15s} class {cls[tid]} first {t['first']} opener {'y' if t['opener'] else 'n'} "
              f"searches_before_edit {t['searches']} issue_pattern {t['issue_searches']} "
              f"gold_shown_before_edit {'y' if t['shown'] else 'n'} "
              f"gold_holds_issue_pattern {'y' if t['gold_holds_issue_pattern'] else 'n'} "
              f"issue_search_shows_gold {'y' if t['issue_search_shows_gold'] else 'n'}")
    print(f"{name}: n {len(cls)} totals {dict(tot)}")
    print("first call kinds:", dict(firsts.most_common()))
    for c in "EFRCS":
        print(f"  class {c}: {dict(by_cls[c])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
