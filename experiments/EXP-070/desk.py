#!/usr/bin/env python3
"""EXP-070 desk checks over the local E4B pipeline runs (zero GPU).

Prints ids, counts, draft numbers, program names, path arguments, exit codes and class letters only (hygiene rule:
no file text, no command arguments other than a path, no model messages).

A *pass* is one run of the pipeline inside a task: it starts at a reader step that follows a non-reader step.
Checks, per run:
  1  reader report per pass. Class: ok (a FILE line naming a path), unknown (`FILE: unknown`), jsoncall (no FILE
     line, and the final holds a call-shaped JSON value by analyze_traces.has_text_form_call), nofile (no FILE line,
     other text), nofinal (the pass has no reader final turn). Also the reader's tool calls in the pass (0 = a
     text-only session). For a non-ok pass: usable drafts in that pass, applier edit_file calls and applied edits in
     that pass, and whether the task's final patch is empty.
  2  verify step: after the applier's last applied edit_file of the task and before the next submit_patch, any
     applier run_command whose program is pytest, python or python3 (incl. -m pytest and -c). Path class:
     mod (a test file whose name holds the edited file's stem as a whole _-separated word), file (another .py path), suite (no path, or a
     directory), c (python -c), and the exit code.
  3  drafts per pass: usable drafts (FILE, OLD, NEW) of drafter_1..5 and distinct ones after whitespace
     normalisation (runs of whitespace collapsed, ends stripped; FILE compared by its last path part). First applied
     edit of the task: the drafts of its pass it matches (FILE suffix plus OLD or NEW equal after normalisation).
  5  task wall (task_results duration_s), the task's counted calls (tool_calls), applier counted calls per task
     (all tool calls but get_status and submit_patch), harness llm_calls.
Usage: python -I -X utf8 experiments/EXP-070/desk.py runs/EXP-061-r runs/EXP-062-r ...
"""
from __future__ import annotations

import json
import re
import shlex
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-063"))
import analyze_traces as A  # noqa: E402
import refs  # noqa: E402

FILE_LINE = re.compile(r"^\s*\**FILE\**\s*:\s*`?([^\s`]+)", re.M)
FREE = {"get_status", "submit_patch"}


def ws(s: str) -> str:
    return " ".join((s or "").split())


def run_paths(run: Path) -> tuple[Path, Path]:
    for base in (run, run / "runs" / run.name):
        if (base / "traces").is_dir() and any((base / "traces").glob("trace_*.json")):
            return base / "traces", base / "task_results.jsonl"
    raise SystemExit(f"no traces under {run}")


def author(s: dict) -> str:
    return str((s.get("extra") or {}).get("author") or "")


def etype(s: dict) -> str:
    return str((s.get("extra") or {}).get("event_type") or "")


def passes(steps: list[dict]) -> list[list[dict]]:
    out: list[list[dict]] = []
    prev = None
    for s in steps:
        a = author(s)
        if s.get("source") == "agent" and a == "reader" and prev != "reader":
            out.append([])
        if out:
            out[-1].append(s)
        if s.get("source") == "agent":
            prev = a
    return out


def classify_reader(ps: list[dict]) -> tuple[str, int]:
    calls = sum(len(s.get("tool_calls") or []) for s in ps if author(s) == "reader")
    finals = [s for s in ps if author(s) == "reader" and etype(s) in ("final", "text") and not s.get("tool_calls")]
    if not finals:
        return "nofinal", calls
    msg = finals[-1].get("message") or ""
    m = FILE_LINE.search(msg)
    if m:
        return ("unknown" if m.group(1).lower().startswith("unknown") else "ok"), calls
    return ("jsoncall" if A.has_text_form_call(msg) else "nofile"), calls


def drafts_of(ps: list[dict]) -> dict[int, dict | None]:
    d: dict[int, dict | None] = {}
    for s in ps:
        a = author(s)
        if s.get("source") == "agent" and a.startswith("drafter_") and etype(s) == "final" and not s.get("tool_calls"):
            d[int(a.split("_")[1])] = refs.parse_draft(s.get("message") or "")
    return d


def key(d: dict) -> tuple[str, str, str]:
    return (Path(d["file"]).name, ws(d["old"]), ws(d["new"]))


def applier_events(ps: list[dict]) -> list[dict]:
    ev = []
    for s in ps:
        if s.get("source") != "agent" or author(s) != "applier":
            continue
        obs = str((s.get("observation") or {}).get("content") or "")
        for tc in s.get("tool_calls") or []:
            fn = str(tc.get("function_name") or tc.get("name") or "")
            ar = refs.args_of(tc)
            e = {"fn": fn, "args": ar, "obs": obs}
            if fn == "edit_file":
                e["ok"] = not refs.failed(obs) and bool(ar)
            ev.append(e)
    return ev


SEP = {"&&", "||", ";", "|"}
PREFIX = {"cd", "timeout", "env", "time", "nice"}


def segments(cmd: str) -> list[list[str]]:
    """Shell words split on &&, ||, ; and |, with leading VAR=value words and a timeout/env/time prefix (and the
    number after timeout) dropped. A `cd x` segment is kept (its program is cd)."""
    try:
        lx = shlex.shlex(cmd, posix=True, punctuation_chars=";&|")
        lx.whitespace_split = True
        w = list(lx)
    except ValueError:
        w = cmd.split()
    out, cur = [], []
    for x in w + [";"]:
        if x in SEP:
            while cur and ("=" in cur[0] and not cur[0].startswith("-") or cur[0] in PREFIX - {"cd"}):
                cur = cur[2:] if cur[0] == "timeout" and len(cur) > 1 and cur[1][:1].isdigit() else cur[1:]
            if cur:
                out.append(cur)
            cur = []
        else:
            cur.append(x)
    return out


def programs(e: dict) -> str:
    if e["fn"] != "run_command":
        return e["fn"]
    segs = segments(str(e["args"].get("command") or ""))
    return "run_command(" + "+".join(Path(sg[0]).name for sg in segs) + ")"


def check_label(e: dict, edited: str) -> str | None:
    if e["fn"] != "run_command":
        return None
    labs = []
    for w in segments(str(e["args"].get("command") or "")):
        prog = Path(w[0]).name
        if prog not in ("pytest", "python", "python3"):
            continue
        if prog.startswith("python") and len(w) > 1 and w[1] == "-c":
            cls, path = "c", None
        else:
            path = next((x for x in w[1:] if (x.endswith(".py") or "/" in x or "::" in x) and not x.startswith("-")), None)
            if path and "::" in path:
                path = path.split("::")[0]
            if prog.startswith("python") and not (len(w) > 2 and w[1] == "-m" and w[2] == "pytest"):
                cls = "file" if path else "suite"
            elif not path or not path.endswith(".py"):
                cls = "suite"
            else:
                stem = re.escape(Path(edited).stem)
                nm = Path(path).name
                cls = "mod" if "test" in nm and re.search(rf"(^|_){stem}(_|\.)", nm) else "file"
        label = prog if not (len(w) > 2 and w[1] == "-m") else f"{prog} -m {w[2]}"
        labs.append(f"{label} {cls}:{path or '-'} exit {refs.exit_code(e['obs'])}")
    return "; ".join(labs) or None


def main(runs: list[str]) -> int:
    for r in runs:
        tdir, res = run_paths(Path(r))
        rows = {json.loads(l)["instance_id"]: json.loads(l) for l in res.read_text(encoding="utf-8").splitlines() if l.strip()}
        print(f"=== {Path(r).name}")
        walls, appl_calls, tcalls = [], [], []
        c = {k: 0 for k in ("passes", "reader_notok", "notok_empty", "edited_tasks", "v_res", "v_unres", "nv_res",
                            "nv_unres", "v_exit0", "v_mod", "v_suite", "usable_passes", "d1", "d2", "d3p", "fa",
                            "fa_exact1", "fa_exact_other", "fa_old_only", "fa_new_only", "fa_own", "fa_nodrafts", "fa_multi", "fa_multi_exact1")}
        for tp in sorted(tdir.glob("trace_*.json")):
            tid = tp.stem[len("trace_"):]
            row = rows.get(tid, {})
            steps = json.loads(tp.read_text(encoding="utf-8")).get("steps") or []
            pss = passes(steps)
            empty = not (row.get("patch") or "")
            walls.append(float(row.get("duration_s") or 0))
            tcalls.append(int(row.get("tool_calls") or 0))
            print(f"  {tid:15s} res {'Y' if row.get('resolved') else '.'} empty {'Y' if empty else '.'} wall {float(row.get('duration_s') or 0):6.1f} "
                  f"calls {row.get('tool_calls')} llm {row.get('llm_calls')} passes {len(pss)}")
            first_applied = None
            all_ev = []
            for i, ps in enumerate(pss, 1):
                cls, rcalls = classify_reader(ps)
                ds = drafts_of(ps)
                usable = {k: v for k, v in ds.items() if v}
                distinct = len({key(v) for v in usable.values()})
                c["passes"] += 1
                if cls != "ok":
                    c["reader_notok"] += 1
                    c["notok_empty"] += empty
                if usable:
                    c["usable_passes"] += 1
                    c["d1" if distinct == 1 else "d2" if distinct == 2 else "d3p"] += 1
                ev = applier_events(ps)
                all_ev += ev
                n_edit = sum(1 for e in ev if e["fn"] == "edit_file")
                n_ok = sum(1 for e in ev if e.get("ok"))
                match = "-"
                for e in ev:
                    if e.get("ok") and first_applied is None:
                        fp = str(e["args"].get("filepath") or "")
                        o, n = ws(e["args"].get("old_string") or ""), ws(e["args"].get("new_string") or "")
                        fm = {k: v for k, v in sorted(usable.items()) if fp.endswith(v["file"].lstrip("/").lstrip("./"))}
                        both = [k for k, v in fm.items() if o == ws(v["old"]) and n == ws(v["new"])]
                        oo = [k for k, v in fm.items() if o == ws(v["old"]) and k not in both]
                        no = [k for k, v in fm.items() if n == ws(v["new"]) and k not in both and k not in oo]
                        first_applied = both
                        c["fa"] += 1
                        if not usable:
                            fcls = "nodrafts"
                        elif 1 in both:
                            fcls = "exact1"
                        elif both:
                            fcls = "exact_other"
                        elif oo:
                            fcls = "old_only"
                        elif no:
                            fcls = "new_only"
                        else:
                            fcls = "own"
                        c["fa_" + fcls] += 1
                        if distinct >= 2:
                            c["fa_multi"] += 1
                            c["fa_multi_exact1"] += fcls == "exact1"
                        match = (f"{fcls} exact[{','.join(map(str, both)) or '-'}] old-only[{','.join(map(str, oo)) or '-'}] "
                                 f"new-only[{','.join(map(str, no)) or '-'}]")
                print(f"    pass {i}: reader {cls} calls {rcalls}; drafts usable {len(usable)} distinct {distinct} "
                      f"(of {len(ds)} finals); applier edits {n_edit} applied {n_ok}; first applied edit {match}")
            # check 2 over the whole task
            last_ok = max((j for j, e in enumerate(all_ev) if e.get("ok")), default=None)
            if last_ok is None:
                print("    verify: no applied edit")
            else:
                edited = str(all_ev[last_ok]["args"].get("filepath") or "")
                nxt = next((j for j in range(last_ok + 1, len(all_ev)) if all_ev[j]["fn"] == "submit_patch"), None)
                window = all_ev[last_ok + 1: nxt if nxt is not None else len(all_ev)]
                labs = [x for x in (check_label(e, edited) for e in window) if x]
                rs = "res" if row.get("resolved") else "unres"
                c["edited_tasks"] += 1
                c[("v_" if labs else "nv_") + rs] += 1
                c["v_exit0"] += any(x.endswith(" exit 0") for x in labs)
                c["v_mod"] += any(" mod:" in x for x in labs)
                c["v_suite"] += any(" suite:" in x for x in labs)
                print(f"    window: {' '.join(programs(e) for e in window) or '-'}")
                print(f"    verify: after last applied edit ({Path(edited).name}) -> {'; '.join(labs) or 'none'}"
                      f"{'' if nxt is not None else ' [no submit after it]'}")
            ac = 0
            for s in steps:
                if s.get("source") == "agent" and author(s) == "applier":
                    ac += sum(1 for tc in s.get("tool_calls") or [] if str(tc.get("function_name")) not in FREE)
            appl_calls.append(ac)
            print(f"    applier counted calls {ac}")
        print(f"  RUN wall mean {st.mean(walls):.2f} max {max(walls):.1f} headroom-to-480s {480 - max(walls):.1f}; "
              f"task calls max {max(tcalls)}; applier calls max {max(appl_calls)}")
        print("  RUN counts " + " ".join(f"{k}={v}" for k, v in c.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
