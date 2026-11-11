#!/usr/bin/env python3
"""EXP-072 desk check (zero GPU): can the applier find a test file of the module it edited, with one pipe-free
command, on the smoke-8 tasks?

For each smoke-8 task it takes the source files the E4B applier actually edited (an applied edit_file in any of
the given run dirs) and the gold patch's source files, then reads the task's repository snapshot (a .tgz under
data/local/snapshots, read as data, never extracted) and counts, under tests/:
  dot   test files holding the module's dotted import path as a fixed string (pkg/sub/mod.py or src/pkg/sub/mod.py -> pkg.sub.mod),
        the hit set of `git grep -l -F 'pkg.sub.mod' -- tests`
  name  tracked files matching `git ls-files -- 'tests/*STEM*'` (fnmatch on the whole path, as git's default
        pathspec glob, where * also matches /), STEM the file name without .py and without a leading _
and whether a graded test file (a file of the task's test patch) is in each set. It also prints the file the
each form would pick (the first sorted `test_*.py` of its set), whether it is in EXP-070's `mod` class and whether that file
or a conftest.py on its directory path names inline_snapshot or dirty_equals (the two test-only packages missing
from the sandbox, a predicted collection error, exit 2).

Prints ids, file paths and counts only (hygiene rule: no file text, no patch text).
Usage: python -I -X utf8 experiments/EXP-072/desk.py runs/EXP-064-loc runs/EXP-069-argform ...
"""
from __future__ import annotations

import fnmatch
import json
import re
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "EXP-063"))
import refs  # noqa: E402

COHORT = [l.strip() for l in open(ROOT / "experiments/cohorts/smoke-8.txt", encoding="utf-8")
          if l.strip() and not l.startswith("#")]
HDR = re.compile(r"^\+\+\+ b/(\S+)", re.M)


def is_test(p: str) -> bool:
    name = p.rsplit("/", 1)[-1]
    return name.startswith("test_") or name.endswith("_test.py") or "/tests/" in "/" + p or name == "conftest.py"


def applied_files(run: Path, tid: str) -> set[str]:
    for base in (run, run / "runs" / run.name):
        tr = base / "traces" / f"trace_{tid}.json"
        if tr.is_file():
            break
    else:
        return set()
    out = set()
    for s in json.load(open(tr, encoding="utf-8")).get("steps") or []:
        if s.get("source") != "agent" or (s.get("extra") or {}).get("author") != "applier":
            continue
        obs = str((s.get("observation") or {}).get("content") or "")
        for tc in s.get("tool_calls") or []:
            if (tc.get("function_name") or tc.get("name")) != "edit_file":
                continue
            ar = refs.args_of(tc)
            fp = str(ar.get("filepath") or "").strip().strip("'\"")
            if ar and not refs.failed(obs) and fp:
                fp = fp.removeprefix("/workspace/").removeprefix("./")
                if not is_test(fp):
                    out.add(fp)
    return out


def main(runs: list[str]) -> int:
    tasks = {}
    for l in open(ROOT / "data/raw/tasks.jsonl", encoding="utf-8"):
        d = json.loads(l)
        if d["instance_id"] in COHORT:
            tasks[d["instance_id"]] = d
    tot = {"mods": 0, "dot>0": 0, "name>0": 0, "either>0": 0, "graded_dot": 0, "graded_name": 0, "graded_either": 0}
    print("task | module | src | dot hits | name hits | graded files | graded in dot | graded in name | per form: first sorted test_*.py, a graded file?, names a missing package?, EXP-070 mod class?")
    for tid in COHORT:
        d = tasks[tid]
        gold = [p for p in HDR.findall(d["patch"]) if not is_test(p)]
        graded = sorted(set(HDR.findall(d["test_patch"])))
        edited: dict[str, set[str]] = {}
        for r in runs:
            for fp in applied_files(Path(r), tid):
                edited.setdefault(fp, set()).add(Path(r).name.split("-", 2)[-1])
        for g in gold:
            edited.setdefault(g, set()).add("gold")
        tf = tarfile.open(ROOT / "data/local/snapshots" / f"{tid}.tgz")
        tests: dict[str, bytes] = {}
        names = set()
        tracked: set[str] = set()
        for m in tf.getmembers():
            n = m.name.removeprefix("./")
            names.add(n)
            if m.isfile() and n.startswith("tests/"):
                tracked.add(n)
                if n.endswith(".py"):
                    tests[n] = tf.extractfile(m).read()
        for fp in sorted(edited):
            if not fp.endswith(".py"):
                continue
            exists = fp in names
            dotted = fp[:-3].removeprefix("src/").replace("/", ".").removesuffix(".__init__")
            stem = fp.rsplit("/", 1)[-1][:-3]
            dot = {n for n, b in tests.items() if dotted.encode() in b}
            st = stem.lstrip("_")
            name = {n for n in tracked if fnmatch.fnmatchcase(n, f"tests/*{st}*")} if stem != "__init__" else set()
            picks = {}
            for form, pool in (("dot", dot), ("name", name)):
                cands = sorted(n for n in pool if n.endswith(".py") and n.rsplit("/", 1)[-1].startswith("test_"))
                pk = cands[0] if cands else None
                blocked = "-"
                if pk:
                    parts = pk.split("/")
                    chain = [pk] + ["/".join(parts[:i]) + "/conftest.py" for i in range(1, len(parts))]
                    blocked = "y" if any(b"inline_snapshot" in tests.get(c, b"") or b"dirty_equals" in tests.get(c, b"")
                                         for c in chain) else "n"
                mod = bool(pk) and bool(re.search(rf"(^|_){re.escape(st)}(_|\.)", pk.rsplit("/", 1)[-1]))
                picks[form] = (pk, blocked, mod)
            pick = picks["dot"][0] or picks["name"][0]
            gd = any(g in dot for g in graded)
            gn = any(g in name for g in graded)
            tot["mods"] += 1
            tot["dot>0"] += bool(dot)
            tot["name>0"] += bool(name)
            tot["either>0"] += bool(dot or name)
            tot["graded_dot"] += gd
            tot["graded_name"] += gn
            tot["graded_either"] += gd or gn
            print(f"{tid} | {fp}{'' if exists else ' (not in snapshot)'} | {','.join(sorted(edited[fp]))} | "
                  f"{len(dot)} | {len(name)} | {len(graded)} graded | {'y' if gd else 'n'} | {'y' if gn else 'n'} | "
                  + " | ".join(f"{f} pick {pk or 'none'} graded {'y' if pk in graded else 'n'} blocked {b} mod {'y' if m else 'n'}"
                               for f, (pk, b, m) in picks.items()))
    print("totals:", tot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
