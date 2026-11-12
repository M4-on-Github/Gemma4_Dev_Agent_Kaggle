#!/usr/bin/env python3
"""EXP-079 desk check and endpoint counter (zero GPU): gold path shown before the first edit, and the form of the
first search, on E4B single-loop runs.

Per task of a run directory:
  shown_path   a gold source file's path (as the gold patch names it) appears as a substring of a tool observation
               before the first edit_file / write_file (EXP-074 section 7 point 2, gold_seen by path). The observation
               of the step that carries the first edit is not counted.
  shown_any    the same, by path or basename (EXP-076 desk.py `shown`)
  first_search the first run_command whose first pipeline segment is a search (grep, egrep, rg, git grep; EXP-076
               desk.search_pattern), anywhere in the task:
                 l      it lists files: a `-l`, `--files-with-matches` or `--name-only` option, or a short-option
                        cluster holding `l` (`-rl`, `-il`)
                 n      a short-option cluster holding `n`, or `--line-number`
                 head   a later pipeline segment is `head`
                 recipe the base prompt's recipe form: git grep with n and head, no l
  class        EXP-074 diag.classify at margin 5 (lowercase when resolved)
Totals over the 48 ids, over the run's own F tasks (resolved f included, as desk.py of EXP-076 counts them), and over
a fixed id set (--fixed FILE, one id per line; default: the ids F or f in EXP-038 or EXP-077).
Prints ids, class letters, flags and counts only (no pattern text, no file text).
Usage: python -I -X utf8 experiments/EXP-079/desk.py RUN [RUN ...] [--per-task]
"""
from __future__ import annotations

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
import desk as D76  # noqa: E402

BASES = ["EXP-038-e4b-dev48", "EXP-077-base"]


def flags(cmd: str) -> dict[str, bool]:
    segs = [s.strip() for s in re.split(r"\|\||&&|;", cmd, maxsplit=1)[0].split("|")]
    w = D76.words(segs[0])
    short = "".join(x[1:] for x in w if re.match(r"^-[A-Za-z]+$", x))
    lng = [x for x in w if x.startswith("--")]
    l_ = "l" in short or any(x in ("--files-with-matches", "--name-only") for x in lng)
    n_ = "n" in short or "--line-number" in lng
    head = any(s and Path(s.split()[0]).name == "head" for s in segs[1:])
    git = bool(w) and Path(w[0]).name == "git"
    return {"l": l_, "n": n_, "head": head, "recipe": git and n_ and head and not l_}


def task(rd: Path, tid: str, gold: list[str]) -> dict:
    steps = json.load(open(rd / "traces" / f"trace_{tid}.json", encoding="utf-8")).get("steps") or []
    gb = {Path(f).name for f in gold}
    edited = shown_p = shown_a = False
    first = None
    for s in steps:
        if s.get("source") != "agent":
            continue
        obs = str((s.get("observation") or {}).get("content") or "")
        for tc in s.get("tool_calls") or []:
            fn = str(tc.get("function_name") or tc.get("name") or "")
            if fn in ("edit_file", "write_file"):
                edited = True
            if fn == "run_command" and first is None:
                cmd = str(refs.args_of(tc).get("command") or "")
                prog, pat = D76.search_pattern(cmd)
                if pat is not None:
                    first = dict(flags(cmd), prog=prog, before_edit=not edited)
        if not edited:
            shown_p = shown_p or any(g in obs for g in gold)
            shown_a = shown_a or shown_p or any(b in obs for b in gb)
    return {"shown_path": shown_p, "shown_any": shown_a, "first": first}


def fixed_default(tasks: dict) -> list[str]:
    out = set()
    for b in BASES:
        out |= {t for t, c in noise.classes(b, tasks).items() if c.upper() == "F"}
    return sorted(out)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    per = "--per-task" in sys.argv
    tasks = {json.loads(x)["instance_id"]: json.loads(x) for x in open(ROOT / "data/raw/tasks.jsonl", encoding="utf-8")}
    fixed = fixed_default(tasks)
    print(f"fixed set (F or f in {' or '.join(BASES)}): {len(fixed)} {fixed}")
    for run in args or BASES:
        rd = noise.run_dir(run)
        cls = noise.classes(run, tasks)
        rows = {}
        for tid in sorted(cls):
            gf = list(diag.gold_regions(tasks[tid]["patch"], 5))
            rows[tid] = task(rd, tid, gf)
            if per:
                f = rows[tid]["first"] or {}
                print(f"  {tid:15s} {cls[tid]} shown_path {'y' if rows[tid]['shown_path'] else 'n'} "
                      f"shown_any {'y' if rows[tid]['shown_any'] else 'n'} first_search "
                      + (" ".join(f"{k}={'y' if f[k] else 'n'}" for k in ("l", "n", "head", "recipe", "before_edit"))
                         + f" prog={f['prog']}" if f else "none"))
        ids = sorted(rows)
        fids = [t for t in ids if cls[t].upper() == "F"]
        uf = [t for t in fids if cls[t] == "F"]
        fx = [t for t in fixed if t in rows]

        def cnt(sel: list[str], key: str) -> str:
            return f"{sum(rows[t][key] for t in sel)}/{len(sel)}"
        fs = [rows[t]["first"] for t in ids if rows[t]["first"]]
        print(f"{run}: n {len(ids)}; shown_path all {cnt(ids, 'shown_path')}, run F (with f) {cnt(fids, 'shown_path')}, "
              f"run F unresolved {cnt(uf, 'shown_path')}, fixed {cnt(fx, 'shown_path')}; "
              f"shown_any all {cnt(ids, 'shown_any')}, run F unresolved {cnt(uf, 'shown_any')}")
        print(f"   first search: tasks with one {len(fs)}/{len(ids)}; before the first edit {sum(f['before_edit'] for f in fs)}; "
              f"git grep {sum(f['prog'] == 'git grep' for f in fs)}; l {sum(f['l'] for f in fs)}; n {sum(f['n'] for f in fs)}; "
              f"head {sum(f['head'] for f in fs)}; recipe form {sum(f['recipe'] for f in fs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
