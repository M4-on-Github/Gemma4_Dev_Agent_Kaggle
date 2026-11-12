#!/usr/bin/env python3
"""EXP-072 section 3 counts over one run directory (zero GPU).

Prints ids, counts, program names, git subcommands, path arguments, exit codes and class letters only (hygiene rule:
no file text, no command arguments other than a path, no test names, no model messages).

Per task, the applier's steps in order:
  turn kinds        each applier model step: T<n> (a step with n native tool calls) or X (no tool call; 'x+' when
                    its text holds a call-shaped JSON value by analyze_traces.has_text_form_call)
  calls             each native call: find (git ls-files; exact-recipe-form y when it is the four words
                    git ls-files -- tests/*STEM* for the first usable draft's FILE, pattern-holds-stem y when the
                    pattern contains that STEM), grep (git grep), undo (git checkout -- a path),
                    pytest <path> exit <code> F<n> E<n> (FAILED and ERROR line counts) [pre or post], edit+ / edit-,
                    read, write, status, submit, other:<program>
Then the section 3 endpoints: first tool call kind; find run and whether it printed a test_*.py; baseline exit;
post-edit runs; pair (baseline exit 0/1 and a post-edit run of the same file); E (post-edit run on a mod-class test
file, leading _ of the stem stripped and, apart, kept, with exit 0 or 1); new-failure events (named: a name on a
FAILED/ERROR line not on one in the baseline; collection: exit 2 after a baseline of 0 or 1); undos and what came
before each; submitted patch empty after an undo.
Usage: python -I -X utf8 experiments/EXP-072/verify.py runs/EXP-072-verify
"""
from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-063"))
import analyze_traces as A  # noqa: E402
import refs  # noqa: E402

LINE = re.compile(r"(?:^|\\n|\n)(FAILED|ERROR) (\S+)")


def author(s: dict) -> str:
    return str((s.get("extra") or {}).get("author") or "")


def words_of(cmd: str) -> list[str]:
    try:
        return shlex.split(cmd)
    except ValueError:
        return cmd.split()


def strip_prefix(w: list[str]) -> list[str]:
    while w and (re.match(r"^\w+=", w[0]) or w[0] in ("env", "time", "nice")):
        w = w[1:]
    if w and w[0] == "timeout":
        w = w[2:] if len(w) > 1 and re.match(r"^[\d.]+[smh]?$", w[1]) else w[1:]
    return w


def names(obs: str) -> tuple[set[str], int, int]:
    found = LINE.findall(obs)
    return ({n for _, n in found}, sum(1 for k, _ in found if k == "FAILED"), sum(1 for k, _ in found if k == "ERROR"))


def is_mod(path: str, edited: str, strip: bool) -> bool:
    nm = Path(path).name
    st = Path(edited).stem
    if strip:
        st = st.lstrip("_")
    return "test" in nm and bool(re.search(rf"(^|_){re.escape(st)}(_|\.)", nm))


def task(trace: Path) -> dict:
    steps = json.load(open(trace, encoding="utf-8")).get("steps") or []
    turns, calls = [], []
    applied: list[str] = []
    for s in steps:
        if s.get("source") != "agent" or author(s) != "applier":
            continue
        tcs = s.get("tool_calls") or []
        msg = str(s.get("message") or "")
        if tcs:
            turns.append(f"T{len(tcs)}")
        else:
            turns.append("x+" if A.has_text_form_call(msg) else "X")
        obs = str((s.get("observation") or {}).get("content") or "")
        for tc in tcs:
            fn = str(tc.get("function_name") or tc.get("name") or "")
            ar = refs.args_of(tc)
            c = {"fn": fn}
            if fn == "edit_file":
                ok = not refs.failed(obs) and bool(ar)
                c["kind"] = "edit+" if ok else "edit-"
                fp = str(ar.get("filepath") or "")
                if ok:
                    applied.append(fp)
                c["file"] = fp
            elif fn == "run_command":
                w = strip_prefix(words_of(str(ar.get("command") or "")))
                prog = Path(w[0]).name if w else ""
                ec = refs.exit_code(obs)
                if prog == "git" and len(w) > 1 and w[1] == "ls-files":
                    printed = re.findall(r"(?:^|\\n|\n|\")(\S*test_\w*\.py)", obs)
                    pat = next((x for x in w[2:] if x != "--"), "")
                    c.update(kind="find", exit=ec, test_py=bool(printed), pat=pat, n_words=len(w))
                elif prog == "git" and len(w) > 1 and w[1] == "grep":
                    c.update(kind="grep", exit=ec)
                elif prog == "git" and len(w) > 1 and w[1] == "checkout":
                    c.update(kind="undo", exit=ec, paths=[x for x in w[2:] if x not in ("--",)])
                elif prog == "pytest" or (prog.startswith("python") and len(w) > 2 and w[1] == "-m" and w[2] == "pytest"):
                    rest = w[1:] if prog == "pytest" else w[3:]
                    path = next((x for x in rest if not x.startswith("-") and (x.endswith(".py") or "/" in x or "::" in x)), None)
                    if path and "::" in path:
                        path = path.split("::")[0]
                    nm, nf, ne = names(obs)
                    c.update(kind="pytest", path=path, exit=ec, nf=nf, ne=ne, names=nm,
                             phase="post" if applied else "pre", edited=applied[-1] if applied else None)
                else:
                    c.update(kind=f"other:{prog}", exit=ec)
            else:
                c["kind"] = {"read_file": "read", "write_file": "write", "get_status": "status",
                             "submit_patch": "submit"}.get(fn, fn)
            calls.append(c)
    d1 = None
    for s in steps:
        a = author(s)
        if s.get("source") == "agent" and a.startswith("drafter_") and (s.get("extra") or {}).get("event_type") == "final":
            d = refs.parse_draft(s.get("message") or "")
            if d and (d1 is None or int(a.split("_")[1]) < d1[0]):
                d1 = (int(a.split("_")[1]), d["file"])
    return {"turns": turns, "calls": calls, "first_draft_file": d1[1] if d1 else None}


def main(run: str) -> int:
    rp = Path(run)
    res = {json.loads(l)["instance_id"]: json.loads(l) for l in open(rp / "task_results.jsonl", encoding="utf-8")}
    tot = dict(first_find=0, find=0, find_test=0, baseline01=0, post=0, pair=0, E_strip=0, E_keep=0,
               ev_named=0, ev_coll=0, ev_tasks=0, undo=0, undo_no_new=0, undo_no_run=0, third=0,
               empty_after_undo=0, first_text=0, text_form=0)
    for p in sorted((rp / "traces").glob("trace_*.json")):
        tid = p.stem[len("trace_"):]
        t = task(p)
        calls = t["calls"]
        print(f"{tid}: resolved {res[tid]['resolved']} patch_chars {res[tid]['patch_chars']} "
              f"turns {' '.join(t['turns']) or '(none)'}")
        line = []
        for c in calls:
            k = c["kind"]
            if k == "pytest":
                line.append(f"pytest[{c['phase']}] {c['path']} exit {c['exit']} F{c['nf']} E{c['ne']}")
            elif k == "find":
                fd = t["first_draft_file"]
                stem = Path(fd).stem.lstrip("_") if fd else None
                ok = stem is not None and c["pat"] == f"tests/*{stem}*" and c["n_words"] == 4
                line.append(f"find exit {c['exit']} test_py {'y' if c['test_py'] else 'n'} "
                            f"exact-recipe-form {'y' if ok else 'n'} "
                            f"pattern-holds-stem {'y' if stem and stem in c['pat'] else 'n'}")
            elif k == "undo":
                line.append(f"undo {' '.join(c['paths'])} exit {c['exit']}")
            elif k in ("edit+", "edit-"):
                line.append(f"{k} {c['file']}")
            else:
                line.append(k + (f" exit {c['exit']}" if "exit" in c else ""))
        print("   calls: " + (" | ".join(line) or "(none)"))
        first = calls[0]["kind"] if calls else "none"
        tot["first_find"] += first == "find"
        tot["first_text"] += bool(t["turns"]) and t["turns"][0] in ("X", "x+")
        tot["text_form"] += sum(1 for x in t["turns"] if x == "x+")
        finds = [c for c in calls if c["kind"] == "find"]
        tot["find"] += bool(finds)
        tot["find_test"] += any(c["test_py"] for c in finds)
        pre = [c for c in calls if c["kind"] == "pytest" and c["phase"] == "pre"]
        post = [c for c in calls if c["kind"] == "pytest" and c["phase"] == "post"]
        base = pre[-1] if pre else None
        b01 = base is not None and base["exit"] in ("0", "1")
        tot["baseline01"] += b01
        tot["post"] += bool(post)
        tot["third"] += len(post) > 2
        pair = b01 and any(c["path"] == base["path"] for c in post)
        tot["pair"] += pair
        e_s = any(c["exit"] in ("0", "1") and c["path"] and c["edited"] and is_mod(c["path"], c["edited"], True)
                  for c in post)
        e_k = any(c["exit"] in ("0", "1") and c["path"] and c["edited"] and is_mod(c["path"], c["edited"], False)
                  for c in post)
        tot["E_strip"] += e_s
        tot["E_keep"] += e_k
        evn = evc = 0
        new_after = []
        for c in post:
            nw = False
            if b01 and c["path"] == base["path"]:
                if c["exit"] in ("0", "1") and c["names"] - base["names"]:
                    evn += 1
                    nw = True
                elif c["exit"] == "2":
                    evc += 1
                    nw = True
            new_after.append((calls.index(c), nw))
        tot["ev_named"] += evn
        tot["ev_coll"] += evc
        tot["ev_tasks"] += bool(evn or evc)
        undo_note = []
        for i, c in enumerate(calls):
            if c["kind"] != "undo":
                continue
            tot["undo"] += 1
            prior = [nw for j, nw in new_after if j < i]
            if not prior:
                tot["undo_no_run"] += 1
                undo_note.append("undo with no post-edit run before it")
            elif not prior[-1]:
                tot["undo_no_new"] += 1
                undo_note.append("undo after a post-edit run with no new failure")
            else:
                undo_note.append("undo after a new failure")
        if any(c["kind"] == "undo" for c in calls) and res[tid]["patch_chars"] == 0 and \
                any(c["kind"] == "edit+" for c in calls):
            tot["empty_after_undo"] += 1
        print(f"   first call {first}; baseline exit {base['exit'] if base else '-'}; post-edit runs {len(post)}; "
              f"pair {'y' if pair else 'n'}; E strip {'y' if e_s else 'n'} keep {'y' if e_k else 'n'}; "
              f"new-failure events named {evn} collection {evc}; {'; '.join(undo_note) or 'no undo'}")
    print("totals:", tot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
