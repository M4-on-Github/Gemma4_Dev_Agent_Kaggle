#!/usr/bin/env python3
"""EXP-076 desk check, part 2 (zero GPU): when the E4B searched a string quoted from the issue that a gold source
file holds at the base commit, did that search's output name the gold file; if not, why not; and would a file-list
form of the same search have named it?

Qualifying search: run_command grep / git grep before the first edit_file / write_file, pattern quoted from the issue
(desk.in_issue), pattern a literal substring of a gold source file at the base commit.
Per qualifying search:
  shows        a gold path or basename appears in the observation
  cause        when it does not show (first that applies):
                 scoped_gold   the command names a gold file as its search path (grep on one file prints no file
                               name, so the output cannot show it; the model had chosen the gold file)
                 scoped_other  the command names search paths (files or directories) none of which is or holds a
                               gold file
                 head          a pipe segment is `head` (bare `head` keeps 10 lines)
                 cap           the observation's stdout is at least 5000 characters (harness max_stdout_chars 5000,
                               sliced with no marker; swegemma budget.py)
                 other
  files_with   snapshot .py files holding the pattern (specificity)
  list_ok      simulation: the path-sorted list of snapshot .py files holding the pattern (one path per line, the
               output shape of `git grep -l PATTERN -- '*.py'`) names a gold file within the first 5000 characters
Prints ids, class letters, cause labels and counts only.
Usage: python -I -X utf8 experiments/EXP-076/trunc.py [run-name]
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for d in ("EXP-074", "EXP-063", "EXP-075", "EXP-076"):
    sys.path.insert(0, str(ROOT / "experiments" / d))
import diag  # noqa: E402
import noise  # noqa: E402
import refs  # noqa: E402
import desk as D  # noqa: E402

BS = chr(92)
CAP = 5000


def stdout_len(obs: str) -> int:
    try:
        o = json.loads(obs)
    except (ValueError, TypeError):
        return len(obs)
    if isinstance(o, dict):
        d = o.get("details") if isinstance(o.get("details"), dict) else o
        return len(str(d.get("stdout") or o.get("stdout") or ""))
    return len(obs)


def scope_paths(cmd: str, pat: str) -> list[str]:
    seg = re.split(r"\|", cmd, maxsplit=1)[0]
    out = []
    for x in D.words(seg):
        if x == pat or x.startswith("-") or x in ("git", "grep", "rg", "egrep", "cd"):
            continue
        if "*" in x:
            continue
        if "/" in x or x.endswith(".py"):
            out.append(diag.norm_path(x.rstrip("/")))
    return out


def cause(cmd: str, pat: str, obs: str, gf: list[str]) -> str:
    sc = scope_paths(cmd, pat)
    if sc and any(diag.same_file(p, g) for p in sc for g in gf):
        return "scoped_gold"
    if sc and not any(g.startswith(p + "/") or diag.same_file(p, g) for p in sc for g in gf) \
            and not any(p in ("", ".") for p in sc):
        return "scoped_other"
    segs = [s.strip().split()[0] for s in cmd.split("|")[1:] if s.strip()]
    if any(Path(s).name == "head" for s in segs):
        return "head"
    if stdout_len(obs) >= CAP:
        return "cap"
    return "other"


def list_ok(pat: str, snap: dict[str, str], gf: list[str]) -> tuple[int, bool]:
    hold = sorted(k for k, v in snap.items() if pat in v)
    n = 0
    for k in hold:
        n += len(k) + 1
        if n > CAP:
            return len(hold), False
        if any(diag.same_file(k, g) for g in gf):
            return len(hold), True
    return len(hold), False


def main() -> int:
    run = sys.argv[1] if len(sys.argv) > 1 else "EXP-038-e4b-dev48"
    tasks = {json.loads(l)["instance_id"]: json.loads(l) for l in open(ROOT / "data/raw/tasks.jsonl", encoding="utf-8")}
    rd = noise.run_dir(run)
    cls = noise.classes(run, tasks)
    agg = collections.Counter()
    per_task: dict[str, dict] = {}
    for tid in sorted(cls):
        g = tasks[tid]
        gf = list(diag.gold_regions(g["patch"], 5))
        ps = g.get("problem_statement") or ""
        snap = diag.snapshot(tid)
        gt = [v for k, v in snap.items() if any(diag.same_file(k, x) for x in gf)]
        steps = json.load(open(rd / "traces" / f"trace_{tid}.json", encoding="utf-8"))["steps"]
        edited = False
        for s in steps:
            if s.get("source") != "agent":
                continue
            obs = str((s.get("observation") or {}).get("content") or "")
            for tc in s.get("tool_calls") or []:
                fn = tc.get("function_name") or tc.get("name")
                ar = refs.args_of(tc)
                if fn in ("edit_file", "write_file"):
                    edited = True
                if fn != "run_command" or edited:
                    continue
                cmd = str(ar.get("command") or "")
                _, pat = D.search_pattern(cmd)
                if pat is None or not D.in_issue(pat, ps):
                    continue
                lit = pat.replace(BS, "")
                if not any(lit in v for v in gt):
                    continue
                shows = any(x in obs for x in gf) or any(Path(x).name in obs for x in gf)
                why = "shows" if shows else cause(cmd, pat, obs, gf)
                nf, lok = list_ok(lit, snap, gf)
                agg[why] += 1
                t = per_task.setdefault(tid, {"cls": cls[tid], "causes": [], "list_ok": False})
                t["causes"].append(why)
                t["list_ok"] |= lok
                print(f"{tid:15s} {cls[tid]} {why:12s} files_with {nf:4d} list_ok {'y' if lok else 'n'} "
                      f"stdout_len {stdout_len(obs)}")
    print(f"{run}: searches by outcome {dict(agg)}")
    # per task, unresolved F only: does any qualifying search show gold (or scope to it); else the causes
    f = {k: v for k, v in per_task.items() if v["cls"] == "F"}
    shown = [k for k, v in f.items() if any(c in ("shows", "scoped_gold") for c in v["causes"])]
    print(f"unresolved F with a qualifying search: {len(f)}; any shows/scoped_gold {len(shown)}; "
          f"list_ok on {sum(v['list_ok'] for v in f.values())}")
    for k, v in sorted(f.items()):
        print(f"   {k:15s} causes {v['causes']} list_ok {'y' if v['list_ok'] else 'n'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
