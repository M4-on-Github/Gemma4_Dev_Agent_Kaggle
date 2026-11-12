#!/usr/bin/env python3
"""EXP-081 desk check (zero GPU): sections 2.1 to 2.5 of experiments/EXP-081-e4b-check-form-python-c-dev48.md.

Q1 cause classes of the checks (P, X, U, M-own, M-repo, M-env, L, C, F), Q2 next action after a non-zero check,
Q3 exercises-the-change for python-form checks, Q4 uptake of python-form commands over the E4B runs on disk, and the
B1 / B2 decision rule. Prints ids, forms, exit codes, class letters and counts only (plan.md:52: no command text,
no check output, no patch text).

Usage: python -I -X utf8 experiments/EXP-081/desk.py [--per-check]
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "EXP-080"))
PER_CHECK = "--per-check" in sys.argv
sys.argv = sys.argv[:1]
import items as I  # noqa: E402

diag, refs, noise = I.diag, I.refs, I.noise

DRAWS = I.DRAWS
REF = I.REF
E4B_ALL = ["EXP-033-e4b", "EXP-038-e4b-dev48", "EXP-040-v1", "EXP-044-X", "EXP-044-X0", "EXP-045-p", "EXP-046-team",
           "EXP-052-t2", "EXP-053-r", "EXP-055-v", "EXP-056-r1", "EXP-056-r2", "EXP-057-r1", "EXP-057-r2", "EXP-061-r",
           "EXP-062-r", "EXP-063-p", "EXP-064-loc", "EXP-066-srch", "EXP-068-read", "EXP-069-argform",
           "EXP-071-anchor", "EXP-072-verify", "EXP-073-repro", "EXP-075-t02", "EXP-077-base", "EXP-078-t02r"]
NOISE = ("X", "U", "M-repo", "M-env", "C")
SIGNAL = ("M-own", "L")
CLASSES = ("P", "X", "U", "M-own", "M-repo", "M-env", "L", "C", "F")
U_TEXT = ("file or directory not found", "no tests ran", "unrecognized arguments", "can't open file",
          "command not found")
C_TEXT = ("ERROR collecting", "ImportError", "conftest", "PluginValidationError")
MOD_RE = re.compile(r"No module named '?\"?([A-Za-z_][\w.]*)")
FIXTURE_RE = re.compile(r"fixture '[^'\n]*' not found")
PYC_RE = re.compile(r"\s-c\s")


def form(cmd: str) -> str:
    if re.search(r"\bpytest\b", cmd):
        return "pytest"
    return "python -c" if PYC_RE.search(cmd) else "script"


def text_of(obs: str) -> str:
    try:
        env = json.loads(obs)
        if isinstance(env, dict) and ("stdout" in env or "stderr" in env):
            return I.decoded(str(env.get("stdout") or "") + "\n" + str(env.get("stderr") or ""))
    except ValueError:
        pass
    return I.decoded(obs)


def tops(tid: str) -> set[str]:
    out = set()
    for k in diag.snapshot(tid):
        parts = k.split("/")
        if len(parts) == 1:
            out.add(parts[0][:-3])
        else:
            out.add(parts[0])
            if parts[0] == "src" and len(parts) > 2:
                out.add(parts[1])
    return out


def names_file(text: str, f: str) -> bool:
    parts = [p for p in diag.norm_path(f).split("/") if p]
    if not parts:
        return False
    if len(parts) == 1:
        return re.search(r"(?:^|[\s/\"'(])" + re.escape(parts[0]) + r"\b", text) is not None
    return "/".join(parts[-2:]) in text


def dotted(f: str) -> tuple[str, str, str]:
    p = diag.norm_path(f)
    p = p[:-3] if p.endswith(".py") else p
    parts = [x for x in p.split("/") if x]
    if parts and parts[0] == "src":
        parts = parts[1:]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts), ".".join(parts[:-1]), parts[-1] if parts else ""


def cause(exitc: str, text: str, changed: list[str], own: str, top: set[str]) -> str:
    if exitc == "0":
        return "P"
    if exitc == "?":
        return "X"
    low = text.lower()
    if exitc in ("4", "5", "127") or any(u in low for u in U_TEXT) or FIXTURE_RE.search(text):
        return "U"
    m = MOD_RE.search(text)
    if m:
        mod = m.group(1).strip(".")
        head = mod.split(".")[0]
        if re.search(r"\b" + re.escape(mod) + r"\b", own) or re.search(r"\b" + re.escape(head) + r"\b", own):
            return "M-own"
        return "M-repo" if head in top else "M-env"
    if any(names_file(text, f) for f in changed):
        return "L"
    if exitc in ("2", "3") or any(c in text for c in C_TEXT):
        return "C"
    return "F"


def script_source(cmd: str, before: list[tuple[str, dict, str]]) -> str | None:
    toks = cmd.replace(";", " ").replace("&&", " ").split()
    path = None
    for i, tk in enumerate(toks):
        if re.search(r"(?:^|/)python3?$", tk):
            for nx in toks[i + 1:]:
                if nx.endswith(".py"):
                    path = diag.norm_path(nx)
                    break
            break
    if not path:
        return None
    src = None
    for fn, a, _obs in before:
        if fn == "write_file" and diag.norm_path(str(a.get("filepath") or "")).endswith(path.split("/")[-1]) \
                and diag.same_file(str(a.get("filepath") or ""), path):
            src = str(a.get("content") or "")
        elif fn == "run_command":
            c = str(a.get("command") or "")
            if re.search(r"(?:cat\s*>|tee)\s*['\"]?" + re.escape(path) + r"\b", c) or \
                    re.search(r"(?:cat\s*>|tee)\s*['\"]?\S*" + re.escape(path.split("/")[-1]) + r"\b", c):
                src = c
    return src


def write_refused(cmd: str, before: list[tuple[str, dict, str]]) -> str:
    toks = cmd.split()
    pys = [diag.norm_path(t) for t in toks if t.endswith(".py")]
    if not pys:
        return "na"
    hits = [refs.failed(obs) for fn, a, obs in before if fn == "write_file"
            and any(diag.same_file(str(a.get("filepath") or ""), p) for p in pys)]
    return "none" if not hits else ("refused" if all(hits) else "written")


def exercises(src: str | None, changed: list[str], encl: list[str]) -> str:
    if src is None:
        return "unknown"
    for f in changed:
        full, parent, mod = dotted(f)
        if full.count(".") >= 1 and re.search(r"\b" + re.escape(full) + r"\b", src):
            return "y"
        if parent and mod and re.search(r"from\s+" + re.escape(parent) + r"\s+import\s+[^\n]*\b" + re.escape(mod) + r"\b", src):
            return "y"
    for n in encl:
        if n and len(n) >= 3 and re.search(r"\b" + re.escape(n) + r"\b", src):
            return "y"
    return "n"


def run_rows(name: str, T: dict, all_python: bool = False) -> list[dict]:
    """One row per check (and, with all_python, per python-form command at any step)."""
    rd = noise.run_dir(name)
    res = {d["instance_id"]: d for d in diag.jl(rd / "task_results.jsonl")}
    rows = []
    for tid in sorted(res):
        if not (rd / "traces" / f"trace_{tid}.json").exists():
            continue
        ms = I.steps_of(name, tid) if name in DRAWS or name == REF else steps_any(rd, tid)
        fc = I.first_change(ms)
        calls = [(i, I.fn_of(tc), refs.args_of(tc), I.obs_of(s)) for i, s in enumerate(ms) for tc in (s.get("tool_calls") or [])]
        encl = None
        top = None
        for k, (i, fn, a, obs) in enumerate(calls):
            if fn != "run_command":
                continue
            cmd = str(a.get("command") or "")
            if not I.CHECK_RE.search(cmd):
                continue
            is_check = fc is not None and i > fc
            fm = form(cmd)
            if not is_check and not (all_python and fm != "pytest"):
                continue
            if all_python and fm == "pytest" and not is_check:
                continue
            before = [(f2, a2, o2) for (i2, f2, a2, o2) in calls[:k]]
            changed, own = [], []
            for (i2, f2, a2, o2) in calls[:k]:
                if i2 < i and f2 in I.CHANGE and a2 and not refs.failed(o2):
                    changed.append(str(a2.get("filepath") or ""))
                    own.append(str(a2.get("new_string") or "") + "\n" + str(a2.get("content") or ""))
            exitc = refs.exit_code(obs)
            if top is None:
                top = tops(tid)
            cl = cause(exitc, text_of(obs), changed, "\n".join(own), top)
            nxt = next_action(cmd, calls[k + 1:])
            row = {"run": name, "task_id": tid, "step": i, "check": is_check, "form": fm, "exit": exitc, "cls": cl,
                   "next": nxt}
            if fm != "pytest":
                if encl is None:
                    encl = I.enclosing_names(tid, res[tid].get("patch") or "") if (res[tid].get("patch") or "").strip() else []
                src = cmd if fm == "python -c" else script_source(cmd, before)
                row["ex"] = exercises(src, changed, [n for n in encl if n])
                row["wr"] = write_refused(cmd, before) if fm == "script" else "na"
            rows.append(row)
    return rows




def steps_any(rd: Path, tid: str) -> list[dict]:
    st = json.load(open(rd / "traces" / f"trace_{tid}.json", encoding="utf-8")).get("steps") or []
    return [s for s in st if s.get("source") == "agent"]


def next_action(cmd: str, rest: list[tuple]) -> str:
    if not rest:
        return "N"
    _i, fn, a, _o = rest[0]
    if fn == "submit_patch":
        return "S"
    if fn == "run_command":
        c = str(a.get("command") or "")
        if c == cmd:
            return "R"
        return "K" if I.CHECK_RE.search(c) else "D"
    if fn in I.CHANGE:
        return "E"
    if fn == "read_file":
        return "D"
    if fn == "get_status":
        return "T"
    return "D:" + fn


def ctr(rows: list[dict], key: str, order: tuple | None = None) -> str:
    c = collections.Counter(r[key] for r in rows)
    ks = list(order) + sorted(k for k in c if k not in order) if order else sorted(c)
    return " ".join(f"{k}:{c[k]}" for k in ks if c[k])


def shares(rows: list[dict]) -> dict:
    nz = [r for r in rows if r["exit"] != "0"]
    n = len(nz)
    c = collections.Counter(r["cls"] for r in nz)
    lo = sum(c[k] for k in SIGNAL)
    return {"n": n, "noise": sum(c[k] for k in NOISE), "lo": lo, "hi": lo + c["F"],
            "noise_share": sum(c[k] for k in NOISE) / n if n else float("nan"),
            "lo_share": lo / n if n else float("nan"), "hi_share": (lo + c["F"]) / n if n else float("nan")}


def main() -> int:
    T = I.tasks()
    print("== Q1: checks in the four E4B dev-48 draws ==")
    draw_rows = {d: run_rows(d, T) for d in DRAWS}
    allc = [r for d in DRAWS for r in draw_rows[d]]
    for d in DRAWS:
        rs = draw_rows[d]
        print(f"{d}: checks {len(rs)} on {len({r['task_id'] for r in rs})} tasks; forms {ctr(rs, 'form')}; "
              f"exits {ctr(rs, 'exit')}")
    py = [r for r in allc if r["form"] == "pytest"]
    print(f"pooled: checks {len(allc)}; pytest {len(py)} (non-zero {sum(1 for r in py if r['exit'] != '0')}); "
          f"other forms {len(allc) - len(py)}")
    print("pytest checks, exit x class:")
    for e in sorted({r["exit"] for r in py}):
        print(f"   exit {e}: {ctr([r for r in py if r['exit'] == e], 'cls', CLASSES)}")
    pnz = [r for r in py if r["exit"] != "0"]
    print(f"non-zero pytest by class: {ctr(pnz, 'cls', CLASSES)}")
    for d in DRAWS:
        print(f"   {d}: {ctr([r for r in pnz if r['run'] == d], 'cls', CLASSES)}")
    sh = shares(py)
    print(f"Q1 shares over {sh['n']} non-zero pytest checks: noise {sh['noise']} ({sh['noise_share']:.3f}); "
          f"signal lower bound M-own+L {sh['lo']} ({sh['lo_share']:.3f}); upper bound +F {sh['hi']} ({sh['hi_share']:.3f})")
    oth = [r for r in allc if r["form"] != "pytest"]
    print(f"E4B non-pytest checks in the draws: {len(oth)}: " + " ".join(
        f"{r['run']}:{r['task_id']}:{r['form']}:exit{r['exit']}:{r['cls']}:ex={r.get('ex')}" for r in oth))
    print(f"tasks with a pytest check whose every check is noise (non-zero, noise class): "
          + " ".join(f"{d}:{sum(1 for t in {r['task_id'] for r in draw_rows[d]} if all(r['cls'] in NOISE for r in draw_rows[d] if r['task_id'] == t))}"
                     f"/{len({r['task_id'] for r in draw_rows[d]})}" for d in DRAWS))

    print("\n== Q2: next action after a non-zero check (E4B draws, all forms) ==")
    nz = [r for r in allc if r["exit"] != "0"]
    print(f"all {len(nz)}: {ctr(nz, 'next', ('S', 'R', 'K', 'E', 'D', 'T', 'N'))}")
    for d in DRAWS:
        print(f"   {d}: {ctr([r for r in nz if r['run'] == d], 'next', ('S', 'R', 'K', 'E', 'D', 'T', 'N'))}")
    print("by Q1 class:")
    for k in CLASSES[1:]:
        sub = [r for r in nz if r["cls"] == k]
        if sub:
            print(f"   {k} ({len(sub)}): {ctr(sub, 'next', ('S', 'R', 'K', 'E', 'D', 'T', 'N'))}")
    for d in DRAWS:
        failed_tasks = {r["task_id"] for r in draw_rows[d] if r["exit"] != "0"}
        fixed = 0
        for t in failed_tasks:
            sc = I.scripted(d, t, T[t], {"submit_patch_called": True, "calls_cap_hit": False, "time_cap_hit": False,
                                         "timeout_hit": False, "wall_s": 0, "n_calls": 0})
            fixed += sc["e3"] == "fix"
        print(f"   e3 {d}: fixed after a failure {fixed}/{len(failed_tasks)} tasks with a failed check")

    print("\n== Q3: arm R (EXP-028-armR) ==")
    rr = run_rows(REF, T)
    print(f"checks {len(rr)} on {len({r['task_id'] for r in rr})} tasks; forms {ctr(rr, 'form')}; exits {ctr(rr, 'exit')}")
    pyr = [r for r in rr if r["form"] != "pytest"]
    print(f"python-form {len(pyr)}: exercises {ctr(pyr, 'ex', ('y', 'n', 'unknown'))}")
    for lab, sub in (("exit 0", [r for r in pyr if r["exit"] == "0"]), ("non-zero", [r for r in pyr if r["exit"] != "0"])):
        print(f"   {lab} ({len(sub)}): exercises {ctr(sub, 'ex', ('y', 'n', 'unknown'))}")
    for fm in ("python -c", "script"):
        sub = [r for r in pyr if r["form"] == fm]
        print(f"   {fm} ({len(sub)}): exercises {ctr(sub, 'ex', ('y', 'n', 'unknown'))}")
    rnz = [r for r in rr if r["exit"] != "0"]
    print(f"non-zero {len(rnz)} on {len({r['task_id'] for r in rnz})} tasks: classes {ctr(rnz, 'cls', CLASSES)}; "
          f"next {ctr(rnz, 'next', ('S', 'R', 'K', 'E', 'D', 'T', 'N'))}")
    shr = shares(rr)
    print(f"arm R shares over {shr['n']} non-zero checks: noise {shr['noise_share']:.3f}, lower {shr['lo_share']:.3f}, "
          f"upper {shr['hi_share']:.3f}")
    ft = {r["task_id"] for r in rnz}
    rsumm = {d["task_id"]: d for d in diag.jl(ROOT / "runs" / REF / "summary.jsonl")}
    fixed = sum(1 for t in ft if I.scripted(REF, t, T[t], rsumm[t])["e3"] == "fix")
    print(f"e3 arm R: fixed after a failure {fixed}/{len(ft)} tasks with a failed check")

    print("\n== Q4: python-form commands in the E4B runs on disk ==")
    q4 = {}
    for name in E4B_ALL:
        rows = [r for r in run_rows(name, T, all_python=True) if r["form"] != "pytest"]
        ntasks = len(diag.jl(noise.run_dir(name) / "summary.jsonl"))
        q4[name] = rows
        pyc_after = {r["task_id"] for r in rows if r["form"] == "python -c" and r["check"]}
        print(f"{name} ({ntasks} tasks): python-form cmds {len(rows)} on {len({r['task_id'] for r in rows})} tasks; "
              f"checks {sum(r['check'] for r in rows)}; python -c after a change on {len(pyc_after)} tasks; "
              f"forms {ctr(rows, 'form')}; exits {ctr(rows, 'exit')}; script write {ctr([r for r in rows if r['form'] == 'script'], 'wr')}")
    pool = [r for n in E4B_ALL for r in q4[n]]
    chk = [r for r in pool if r["check"]]
    nzc = [r for r in chk if r["exit"] != "0"]
    print(f"pooled all runs: python-form cmds {len(pool)} on {len({(r['run'], r['task_id']) for r in pool})} task-runs; "
          f"checks {len(chk)}: exit 0 {sum(1 for r in chk if r['exit'] == '0')}; non-zero classes {ctr(nzc, 'cls', CLASSES)}; "
          f"exercises {ctr(chk, 'ex', ('y', 'n', 'unknown'))}")
    for lab, sub in (("exit 0", [r for r in chk if r["exit"] == "0"]), ("non-zero", nzc)):
        print(f"   {lab} ({len(sub)}): exercises {ctr(sub, 'ex', ('y', 'n', 'unknown'))}")
    dr = [r for n in DRAWS for r in q4[n]]
    print(f"four dev-48 draws: python-form cmds {len(dr)} on {len({(r['run'], r['task_id']) for r in dr})} of 192 task-draws; "
          f"checks {sum(r['check'] for r in dr)}")

    print("\n== Decision rule (section 3) ==")
    b1 = sh["noise_share"] >= 0.50 and sh["lo_share"] <= 0.25
    print(f"B1: noise {sh['noise_share']:.3f} >= 0.50 and lower bound {sh['lo_share']:.3f} <= 0.25 -> {b1}")
    a_runs = {n: len({r['task_id'] for r in q4[n] if r['form'] == 'python -c' and r['check']}) for n in E4B_ALL}
    print("B2(a) python -c after a change, tasks per run: " + " ".join(f"{n}:{v}" for n, v in a_runs.items() if v))
    n_ok = sum(1 for r in chk if r["exit"] == "0")
    mrepo = sum(1 for r in nzc if r["cls"] == "M-repo")
    if len(chk) >= 6:
        b2b = n_ok / len(chk) >= 0.40 and (mrepo / len(nzc) if nzc else 0.0) <= 0.25
        print(f"B2(b) over {len(chk)} python-form checks: exit 0 share {n_ok / len(chk):.3f} >= 0.40, "
              f"M-repo share of non-zero {mrepo}/{len(nzc)} <= 0.25 -> {b2b}")
    else:
        b2b = None
        print(f"B2(b) not read: {len(chk)} python-form checks (< 6)")
    print("B2(a) needs a run whose prompt directs a python command with 4 or more of 8 (judged in the file, by run).")

    print("\n== Post hoc, added after the counts above were read (not part of the decision rule) ==")
    pc = [r for r in chk if r["form"] == "python -c"]
    print(f"python -c checks only, all E4B runs: {len(pc)}: exit 0 {sum(1 for r in pc if r['exit'] == '0')} "
          f"({sum(1 for r in pc if r['exit'] == '0') / len(pc):.3f}); non-zero classes "
          f"{ctr([r for r in pc if r['exit'] != '0'], 'cls', CLASSES)}; exercises {ctr(pc, 'ex', ('y', 'n', 'unknown'))}")
    last = {}
    for r in sorted(pc, key=lambda z: (z["run"], z["task_id"], z["step"])):
        last[(r["run"], r["task_id"])] = r["exit"]
    print(f"python -c task-runs, last python -c check passed: {sum(1 for v in last.values() if v == '0')}/{len(last)} "
          f"({sum(1 for v in last.values() if v == '0') / len(last):.3f}); runs {dict(collections.Counter(k[0] for k in last))}; "
          f"distinct ids {len({k[1] for k in last})}")
    exc_re = re.compile(r"\b([A-Z]\w*(?:Error|Exception|Exit)|AssertionError)\b")
    excs = collections.Counter()
    for r in pc:
        if r["exit"] == "0":
            continue
        ms = I.steps_of(r["run"], r["task_id"])
        found = exc_re.findall(text_of(I.obs_of(ms[r["step"]])))
        tx = text_of(I.obs_of(ms[r["step"]]))
        snip = "snippet" if 'File "<string>"' in tx else "file"
        excs[(found[-1] if found else "none") + "/" + snip + "/" + r["cls"]] += 1
    print(f"non-zero python -c checks by the last exception name in the output: {dict(excs.most_common())}")
    auth = collections.Counter()
    for r in pc:
        ms = I.steps_of(r["run"], r["task_id"])
        auth[(r["run"], str((ms[r["step"]].get("extra") or {}).get("author") or "?"))] += 1
    print("python -c checks by run and step author: " + " ".join(f"{a}:{b}:{v}" for (a, b), v in sorted(auth.items())))
    c1 = sum(1 for r in pnz if r["cls"] == "C" and r["exit"] == "1")
    print(f"B1 margin: lower bound with the {c1} exit-1 C checks moved to signal {(sh['lo'] + c1) / sh['n']:.3f}; "
          f"noise without them {(sh['noise'] - c1) / sh['n']:.3f}")
    for lab, k in (("S", "S"), ("R+K", ("R", "K")), ("E", "E")):
        v = sum(1 for r in nz if r["next"] in (k if isinstance(k, tuple) else (k,)))
        print(f"Q2 share next {lab}: {v}/{len(nz)} ({v / len(nz):.3f})")
    mods = collections.Counter()
    menv = [r for r in pnz if r["cls"] == "M-env"]
    for r in menv:
        ms = I.steps_of(r["run"], r["task_id"])
        m = MOD_RE.search(text_of(I.obs_of(ms[r["step"]])))
        mods[m.group(1).split(".")[0] if m else "?"] += 1
    print(f"M-env pytest checks by missing top-level module: {dict(mods.most_common())}; "
          f"tasks {len({(r['run'], r['task_id']) for r in menv})}, distinct ids {len({r['task_id'] for r in menv})}")

    if PER_CHECK:
        print("\n== per check (ids, forms, exits, classes, next) ==")
        for r in allc + rr + chk:
            print(f"{r['run']} {r['task_id']} step{r['step']} {r['form']} exit{r['exit']} {r['cls']} next={r['next']} "
                  f"ex={r.get('ex', '-')} wr={r.get('wr', '-')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
