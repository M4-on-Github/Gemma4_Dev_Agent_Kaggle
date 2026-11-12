#!/usr/bin/env python3
"""EXP-074: divergence stage of each task-run against the gold patch, the draft discriminator, reasoning-text
measures and opportunity counts (zero GPU). Rules: experiments/EXP-074-e4b-reasoning-diagnosis.md section 2.

Prints ids, counts, class letters, step indices and booleans only (hygiene rule: no gold, patch, repository,
command or thought text).
Usage: python -I -X utf8 experiments/EXP-074/diag.py [--margin 5]
"""
from __future__ import annotations

import argparse
import collections
import difflib
import glob
import json
import re
import statistics
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "EXP-063"))
import refs  # noqa: E402

RUNS = ROOT / "runs"
DEV = "EXP-038-e4b-dev48"
SINGLE_SMOKE = "EXP-053-r"
PIPE = ["EXP-064-loc", "EXP-066-srch", "EXP-068-read", "EXP-069-argform", "EXP-071-anchor", "EXP-072-verify"]
PIPE_EARLY = ["EXP-061-r", "EXP-062-r", "EXP-063-p"]
NONSRC = ("docs_src/", "docs/", "scripts/", "tests/")
ORDER = "EFRCS"


def run_dir(name: str) -> Path:
    p = RUNS / name
    nested = p / "runs" / name
    return p if (p / "summary.jsonl").exists() and (p / "traces").is_dir() else nested


def jl(path: Path) -> list[dict]:
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


# ---------- diffs ----------
def norm_path(p: str) -> str:
    p = p.strip().strip("'\"`")
    for pre in ("/workspace/", "/testbed/", "./", "/"):
        if p.startswith(pre):
            p = p[len(pre):]
    return p


def parse_diff(text: str) -> dict[str, set[int]]:
    """file -> changed old-side lines (section 2.2)."""
    out: dict[str, set[int]] = {}
    cur = None
    old_no = 0
    pend_plus = False
    left_old = left_new = 0
    for ln in (text or "").split("\n"):
        if left_old > 0 or left_new > 0:
            if cur is None:
                left_old = left_new = 0
            elif ln.startswith("-"):
                out[cur].add(old_no)
                old_no += 1
                left_old -= 1
                pend_plus = False
                continue
            elif ln.startswith("+"):
                if not pend_plus:
                    out[cur].update({max(old_no - 1, 1), old_no})
                    pend_plus = True
                left_new -= 1
                continue
            elif ln.startswith(" ") or ln == "":
                old_no += 1
                left_old -= 1
                left_new -= 1
                pend_plus = False
                continue
            elif ln.startswith("\\"):
                continue
        if ln.startswith("diff --git "):
            cur = None
            continue
        if ln.startswith("--- "):
            a = ln[4:].split("\t")[0]
            cur = norm_path(a[2:]) if a.startswith("a/") else None
            continue
        if ln.startswith("+++ "):
            b = ln[4:].split("\t")[0]
            if b.startswith("b/"):
                cur = norm_path(b[2:])
            out.setdefault(cur, set()) if cur else None
            continue
        m = re.match(r"^@@ -(\d+)(?:,(\d+))? \+\d+(?:,(\d+))? @@", ln)
        if m:
            old_no = int(m.group(1))
            left_old = int(m.group(2)) if m.group(2) is not None else 1
            left_new = int(m.group(3)) if m.group(3) is not None else 1
            if left_old == 0:
                old_no += 1  # pure insertion after line a: the next old line is a+1
            pend_plus = False
            continue
    return out


def regions(lines: set[int], m: int) -> list[tuple[int, int]]:
    rs: list[list[int]] = []
    for x in sorted(lines):
        if rs and x - rs[-1][1] <= 2 * m:
            rs[-1][1] = x
        else:
            rs.append([x, x])
    return [tuple(r) for r in rs]


def gold_regions(gold_patch: str, m: int, all_files: bool = False) -> dict[str, list[tuple[int, int]]]:
    g = parse_diff(gold_patch)
    src = {f: l for f, l in g.items() if all_files or not f.startswith(NONSRC)}
    if not src:
        src = g
    return {f: regions(l, m) for f, l in src.items()}


def touches(lines: set[int], reg: tuple[int, int], m: int) -> bool:
    return any(reg[0] - m <= x <= reg[1] + m for x in lines)


def same_file(a: str, b: str) -> bool:
    a, b = norm_path(a), norm_path(b)
    return a == b or a.endswith("/" + b) or b.endswith("/" + a)


def classify(patch: str, empty: bool, greg: dict, m: int) -> str:
    if empty:
        return "E"
    p = parse_diff(patch)
    gf = [f for f in greg if any(same_file(f, x) for x in p)]
    if not gf:
        return "F"
    total = sum(len(r) for r in greg.values())
    hit = 0
    for f, rs in greg.items():
        lines = set().union(*[l for x, l in p.items() if same_file(f, x)] or [set()])
        hit += sum(1 for r in rs if touches(lines, r, m))
    if hit == 0:
        return "R"
    return "S" if hit == total else "C"


# ---------- snapshots and drafts ----------
_SNAP: dict[str, dict[str, str]] = {}


def snapshot(tid: str) -> dict[str, str]:
    if tid not in _SNAP:
        files = {}
        with tarfile.open(ROOT / "data/local/snapshots" / f"{tid}.tgz", "r|*") as tf:
            for mem in tf:
                if mem.isfile() and mem.name.endswith(".py"):
                    f = tf.extractfile(mem)
                    if f:
                        files[norm_path(mem.name)] = f.read().decode("utf-8", "replace")
        _SNAP[tid] = files
    return _SNAP[tid]


def parse_loose(text: str) -> dict | None:
    m = refs.FILE_RE.search(text or "")
    if not m or "OLD:" not in text:
        return None
    old = refs._block(text, "OLD:", ("\n>>>", "\nNEW:", "\nWHY:", "\nEND"))
    new = refs._block(text, "NEW:", ("\n>>>", "\nWHY:", "\nEND")) if "NEW:" in text else None
    return {"file": norm_path(m.group(1).strip("`")), "old": old, "new": new}


def locate(d: dict, snap: dict[str, str]) -> tuple[str | None, int | None, int | None, str]:
    fp = d["file"]
    cands = [p for p in snap if p == fp] or [p for p in snap if same_file(p, fp)]
    if not cands:
        return None, None, None, "nofile"
    old = d["old"]
    olines = [x for x in old.split("\n")]
    for p in cands:
        txt = snap[p]
        if old.strip() and old in txt:
            s = txt[: txt.index(old)].count("\n") + 1
            return p, s, s + len(olines) - 1, "exact"
    want = [x.strip() for x in olines if x.strip()]
    if not want:
        return cands[0], None, None, "unlocated"
    for p in cands:
        fl = snap[p].split("\n")
        nb = [(i + 1, x.strip()) for i, x in enumerate(fl) if x.strip()]
        for k in range(len(nb) - len(want) + 1):
            if all(nb[k + j][1] == want[j] for j in range(len(want))):
                return p, nb[k][0], nb[k + len(want) - 1][0], "norm"
    return cands[0], None, None, "unlocated"


def draft_lines(d: dict, s: int, e: int) -> set[int]:
    if d["new"] is None:
        return set(range(s, e + 1))
    a, b = d["old"].split("\n"), d["new"].split("\n")
    ch: set[int] = set()
    for tag, i1, i2, _, _ in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if i2 > i1:
            ch.update(range(s + i1, s + i2))
        else:
            ch.update({s + i1 - 1, s + i1})
    return ch or set(range(s, e + 1))


def drafts_of(steps: list[dict]) -> list[dict]:
    out = []
    for st in steps:
        a = str((st.get("extra") or {}).get("author") or "")
        if st.get("source") == "agent" and a.startswith("drafter_") and (st.get("extra") or {}).get("event_type") == "final":
            d = parse_loose(st.get("message") or "")
            if d:
                out.append(d)
    return out


# ---------- traces ----------
PY_RE = re.compile(r"[\w./-]+\.py\b")
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_.]{2,}")
CAMEL = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]*)+\b")


def key_identifiers(ps: str, gold_patch: str) -> set[str]:
    toks = set()
    for b in re.findall(r"`([^`\n]{1,80})`", ps or ""):
        toks.update(IDENT.findall(b))
    toks.update(CAMEL.findall(ps or ""))
    changed = "\n".join(l for l in gold_patch.split("\n") if l[:1] in "+-" and not l.startswith(("+++", "---")))
    keep = set()
    for t in toks:
        last = t.rstrip(".").split(".")[-1]
        if len(last) >= 3 and re.search(rf"\b{re.escape(last)}\b", changed):
            keep.add(last)
    return keep


def q3(steps: list[dict], authors: set[str] | None, patch: str, gold_files: list[str], keys: set[str]) -> dict:
    ms = [s for s in steps if s.get("source") == "agent"
          and (authors is None or str((s.get("extra") or {}).get("author") or "") in authors)]
    pfiles = list(parse_diff(patch))
    edited = None
    first_edit = None
    for i, s in enumerate(ms):
        for tc in s.get("tool_calls") or []:
            if (tc.get("function_name") or tc.get("name")) == "edit_file":
                fp = norm_path(str(refs.args_of(tc).get("filepath") or ""))
                if first_edit is None:
                    first_edit = i
                if edited is None and any(same_file(fp, x) for x in pfiles):
                    edited = next(x for x in pfiles if same_file(fp, x))
    if edited is None and pfiles:
        edited = pfiles[0]
    if first_edit is None:
        first_edit = len(ms)
    base = Path(edited).name if edited else None
    name_step = None
    named_py: set[str] = set()
    gold_named_path = gold_named_base = False
    gold_seen = gold_seen_base = False
    searched = False
    read_before = False
    edit_on_x = None
    for i, s in enumerate(ms):
        ev = (s.get("extra") or {}).get("event_type")
        msg = str(s.get("message") or "")
        if ev == "thinking" and msg:
            if name_step is None and edited and (edited in msg or (base and base in msg)):
                name_step = i
            if i < first_edit:
                named_py.update(norm_path(x) for x in PY_RE.findall(msg))
            for g in gold_files:
                gs = g[4:] if g.startswith("src/") else g
                gold_named_path |= g in msg or gs in msg
                gold_named_base |= Path(g).name in msg
        obs = str((s.get("observation") or {}).get("content") or "")
        for tc in s.get("tool_calls") or []:
            fn = tc.get("function_name") or tc.get("name")
            ar = refs.args_of(tc)
            if fn == "edit_file" and edited and same_file(norm_path(str(ar.get("filepath") or "")), edited) and edit_on_x is None:
                edit_on_x = i
            if i < first_edit:
                argtxt = str(ar.get("command") or "") if fn == "run_command" else str(ar.get("filepath") or "") if fn == "read_file" else ""
                if keys and any(k in argtxt for k in keys):
                    searched = True
            if edited and (edit_on_x is None or i < edit_on_x) and fn in ("read_file", "run_command"):
                argtxt = str(ar.get("filepath") or "") if fn == "read_file" else str(ar.get("command") or "")
                if fn == "read_file" and same_file(norm_path(argtxt), edited):
                    read_before = True
                if fn == "run_command" and (edited in argtxt or (base and base in argtxt)):
                    read_before = True
        if i < first_edit:
            for g in gold_files:
                gs = g[4:] if g.startswith("src/") else g
                if g in obs or gs in obs:
                    gold_seen = True
                if Path(g).name in obs:
                    gold_seen_base = True
    return {"steps": len(ms), "first_edit": first_edit if first_edit < len(ms) else None, "name_step": name_step,
            "named_before_edit": name_step is not None and name_step <= first_edit, "n_py_named": len(named_py),
            "keys": len(keys), "searched": searched, "read_before": read_before, "gold_seen": gold_seen,
            "gold_named_path": gold_named_path, "gold_named_base": gold_named_base, "gold_seen_base": gold_seen_base}


# ---------- main ----------
def load_run(name: str) -> tuple[Path, dict, dict]:
    rd = run_dir(name)
    summ = {d["task_id"]: d for d in jl(rd / "summary.jsonl")}
    res = {d["instance_id"]: d for d in jl(rd / "task_results.jsonl")}
    return rd, summ, res


def ever_resolved() -> tuple[set[str], set[str]]:
    anyr, e4b = set(), set()
    paths = glob.glob(str(RUNS / "*" / "task_results.jsonl")) + glob.glob(str(RUNS / "*" / "runs" / "*" / "task_results.jsonl"))
    for p in sorted(set(paths)):
        if "EXP-000" in p:
            continue
        top = Path(p).parent
        ay = [top / "agent" / "agent.yaml", RUNS / Path(p).relative_to(RUNS).parts[0] / "agent" / "agent.yaml"]
        model = ""
        for a in ay:
            if a.exists():
                mm = re.search(r"^model:\s*(\S+)", a.read_text(encoding="utf-8", errors="replace"), re.M)
                model = mm.group(1) if mm else ""
                break
        for d in jl(Path(p)):
            if d.get("resolved"):
                anyr.add(d["instance_id"])
                if "e4b" in model:
                    e4b.add(d["instance_id"])
    return anyr, e4b


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--margin", type=int, default=5)
    ap.add_argument("--all-gold-files", action="store_true")
    ap.add_argument("--brief", action="store_true", help="stage tables only")
    a = ap.parse_args()
    M = a.margin
    tasks = {}
    for l in open(ROOT / "data/raw/tasks.jsonl", encoding="utf-8"):
        t = json.loads(l)
        tasks[t["instance_id"]] = t
    print(f"margin {M}; gold files: {'all' if a.all_gold_files else 'source only'}")

    stage: dict[str, dict[str, str]] = {}   # run -> tid -> class (lowercase when resolved)
    q3rows: list[tuple[str, str, str, dict]] = []
    q2rows: list[tuple[str, str, str, dict]] = []
    tok: dict[str, list[int]] = collections.defaultdict(list)
    think = {}
    for name in [DEV, SINGLE_SMOKE] + PIPE + PIPE_EARLY:
        rd, summ, res = load_run(name)
        stage[name] = {}
        nthink = tr_think = nraw = 0
        for tid in sorted(summ):
            g = tasks[tid]
            greg = gold_regions(g["patch"], M, a.all_gold_files)
            c = classify(res[tid].get("patch") or "", bool(summ[tid]["patch_empty"]), greg, M)
            stage[name][tid] = c.lower() if summ[tid]["resolved"] else c
            if a.brief:
                continue
            steps = json.load(open(rd / "traces" / f"trace_{tid}.json", encoding="utf-8")).get("steps") or []
            anyt = False
            for s in steps:
                if s.get("source") != "agent":
                    continue
                au = str((s.get("extra") or {}).get("author") or "")
                role = "single" if au == "swe_agent" and name in (DEV, SINGLE_SMOKE) else re.sub(r"_\d+$", "", au)
                grp = name if name in (DEV, SINGLE_SMOKE) else ("pipe:" if name in PIPE else "early:") + role
                ct = (s.get("metrics") or {}).get("completion_tokens")
                if isinstance(ct, int):
                    tok[grp].append(ct)
                msg = str(s.get("message") or "")
                if (s.get("extra") or {}).get("event_type") == "thinking" and msg:
                    nthink += 1
                    anyt = True
                nraw += "<|channel>thought" in msg
            tr_think += anyt
            gfiles = list(greg)
            keys = key_identifiers(g.get("problem_statement") or "", g["patch"])
            if c in "FR" and not summ[tid]["resolved"] and name not in PIPE_EARLY:
                authors = None if name in (DEV, SINGLE_SMOKE) else {"reader", "applier"}
                q3rows.append((name, tid, c, q3(steps, authors, res[tid].get("patch") or "", gfiles, keys)))
            if name in PIPE + PIPE_EARLY and not summ[tid]["resolved"]:
                snap = snapshot(tid)
                info = {"n": 0, "located": 0, "appliable": 0, "names_gold": 0, "overlap": 0, "overlap_app": 0, "kinds": collections.Counter()}
                for d in drafts_of(steps):
                    info["n"] += 1
                    p, s0, e0, kind = locate(d, snap)
                    info["kinds"][kind] += 1
                    ng = any(same_file(d["file"], f) for f in greg)
                    info["names_gold"] += ng
                    if s0 is None:
                        continue
                    info["located"] += 1
                    app = d["new"] is not None and kind == "exact"
                    info["appliable"] += app
                    dl = draft_lines(d, s0, e0)
                    ov = any(touches(dl, r, M) for f, rs in greg.items() if same_file(f, p) for r in rs)
                    info["overlap"] += ov
                    info["overlap_app"] += ov and app
                q2rows.append((name, tid, c, info))
        think[name] = (nthink, tr_think, len(summ), nraw)

    # ---- Q1 tables ----
    def dist(cls: list[str]) -> str:
        cc = collections.Counter(cls)
        return " ".join(f"{k}{cc.get(k, 0)}" for k in ORDER)

    print("\n== Q1 per run (unresolved classes; resolved runs in lower case)")
    for name, d in stage.items():
        un = [c for c in d.values() if c.isupper()]
        rs = [c for c in d.values() if c.islower()]
        print(f"  {name:18s} n {len(d):2d} unresolved {len(un):2d}: {dist(un)} | resolved {len(rs)}: {' '.join(sorted(rs)) or '-'}")
    for label, group in (("dispatch pipeline", PIPE), ("early pipeline", PIPE_EARLY), ("all pipeline", PIPE + PIPE_EARLY)):
        un = [c for n in group for c in stage[n].values() if c.isupper()]
        print(f"  {label:18s} task-runs unresolved {len(un)}: {dist(un)}")

    print("\n== Q1 per distinct task (EXP-038 class; pipeline modal class over unresolved runs, tie -> earlier)")
    smoke = sorted(stage[PIPE[0]])
    for tid in sorted(stage[DEV]):
        row = f"  {tid:15s} 038 {stage[DEV][tid]}"
        if tid in smoke:
            pc = [stage[n][tid] for n in PIPE]
            un = [c for c in pc if c.isupper()]
            mode = min(collections.Counter(un).items(), key=lambda kv: (-kv[1], ORDER.index(kv[0])))[0] if un else "-"
            ec = [stage[n][tid] for n in PIPE_EARLY]
            row += f" | 053 {stage[SINGLE_SMOKE][tid]} | pipe {''.join(pc)} mode {mode} | early {''.join(ec)}"
        print(row)
    dev_un = [c for c in stage[DEV].values() if c.isupper()]
    print(f"  EXP-038 distinct unresolved {len(dev_un)}: {dist(dev_un)}")
    modes = []
    for tid in smoke:
        un = [stage[n][tid] for n in PIPE if stage[n][tid].isupper()]
        if un:
            modes.append(min(collections.Counter(un).items(), key=lambda kv: (-kv[1], ORDER.index(kv[0])))[0])
    print(f"  pipeline distinct (dispatch, modal) {len(modes)}: {dist(modes)}")
    if a.brief:
        return 0

    # ---- Q1 detail for EXP-038 (actions only) ----
    print("\n== Q1 detail, EXP-038: E runs (summary.jsonl fields) and F runs (classes of patched files)")
    rd, summ, res = load_run(DEV)
    for tid, c in sorted(stage[DEV].items()):
        sm = summ[tid]
        if c == "E":
            print(f"  E {tid:15s} calls {sm['n_calls']} edit_fail {sm['n_edit_fail']} arg_loss {sm['n_edit_arg_loss']} "
                  f"submit {sm['submit_patch_called']} time_cap {sm['time_cap_hit']} calls_cap {sm['calls_cap_hit']} "
                  f"text_form {sm.get('n_text_form_calls')} tool_free {sm.get('tool_free')} phase {sm['phase_reached']} "
                  f"wall {sm['wall_s']} err {'y' if res[tid].get('error') else 'n'}")
        if c in "F":
            pf = list(parse_diff(res[tid].get("patch") or ""))
            kinds = collections.Counter("test" if (f.startswith("tests/") or Path(f).name.startswith("test_")) else
                                        "docs" if f.startswith(("docs/", "docs_src/")) else
                                        "same-pkg-src" if any(f.split("/")[0] == g.split("/")[0] for g in gold_regions(tasks[tid]["patch"], M)) else
                                        "other" for f in pf)
            print(f"  F {tid:15s} patched files {len(pf)} {dict(kinds)} gold source files {len(gold_regions(tasks[tid]['patch'], M))}")

    # ---- Q2 ----
    print("\n== Q2 drafts (pipeline unresolved runs)")
    for grp_label, group in (("dispatch", PIPE), ("early", PIPE_EARLY)):
        tot = collections.Counter()
        tasks_ov = set()
        tasks_ov_app = set()
        for name, tid, c, info in q2rows:
            if name not in group:
                continue
            k = collections.Counter(info["kinds"])
            print(f"  {name:16s} {tid:15s} {c} drafts {info['n']} located {info['located']} ({dict(k)}) appliable {info['appliable']} "
                  f"names-gold {info['names_gold']} overlap {info['overlap']} overlap+appliable {info['overlap_app']}")
            tot["runs"] += 1
            tot["drafts"] += info["n"]
            tot["located"] += info["located"]
            tot["names_gold"] += info["names_gold"]
            tot["overlap_drafts"] += info["overlap"]
            if c in "EFR":
                tot["miss_runs"] += 1
                tot["miss_any_overlap"] += info["overlap"] > 0
                tot["miss_any_overlap_app"] += info["overlap_app"] > 0
                tot["miss_any_names_gold"] += info["names_gold"] > 0
                if info["overlap"]:
                    tasks_ov.add(tid)
                if info["overlap_app"]:
                    tasks_ov_app.add(tid)
            else:
                tot["hit_runs"] += 1
                tot["hit_any_overlap"] += info["overlap"] > 0
        print(f"  {grp_label} totals {dict(tot)}; distinct tasks with a miss-run overlap {sorted(tasks_ov)}; with appliable {sorted(tasks_ov_app)}")

    # ---- Q3 ----
    print("\n== Q3 thought text per run: thinking steps, task-runs with any, task-runs, raw channel marker messages")
    for name, v in think.items():
        print(f"  {name:18s} {v}")
    print("\n== Q3 F and R runs")
    for grp_label, group in (("EXP-038", [DEV]), ("EXP-053-r", [SINGLE_SMOKE]), ("pipeline", PIPE)):
        rows = [(n, t, c, d) for n, t, c, d in q3rows if n in group]
        for n, t, c, d in rows:
            print(f"  {n:16s} {t:15s} {c} steps {d['steps']} first_edit {d['first_edit']} name_step {d['name_step']} "
                  f"named<=edit {d['named_before_edit']} py_named {d['n_py_named']} keys {d['keys']} searched {d['searched']} "
                  f"read_before {d['read_before']} gold_seen {d['gold_seen']} gold_named path {d['gold_named_path']} base {d['gold_named_base']}")
        for cls in "FR":
            rr = [d for _, _, c, d in rows if c == cls]
            if not rr:
                continue
            s = {k: sum(1 for d in rr if d[k]) for k in ("named_before_edit", "searched", "read_before", "gold_seen", "gold_seen_base", "gold_named_path", "gold_named_base")}
            s["keys>0"] = sum(1 for d in rr if d["keys"])
            s["searched|keys>0"] = sum(1 for d in rr if d["keys"] and d["searched"])
            print(f"  {grp_label} {cls} n {len(rr)}: {s}; median py_named {statistics.median(d['n_py_named'] for d in rr)}; median name_step {statistics.median(d['name_step'] for d in rr if d['name_step'] is not None)}; median first_edit {statistics.median(d['first_edit'] for d in rr if d['first_edit'] is not None)}; name_step<=1 {sum(1 for d in rr if d['name_step'] is not None and d['name_step'] <= 1)}")

    print("\n== Q3 completion tokens per model step (upper bound on thought tokens)")
    for grp, v in sorted(tok.items()):
        v = sorted(v)
        print(f"  {grp:20s} steps {len(v):4d} median {statistics.median(v):6.0f} p90 {v[int(0.9 * (len(v) - 1))]:5d} max {v[-1]:5d} "
              f">=4096 {sum(x >= 4096 for x in v)} >=8000 {sum(x >= 8000 for x in v)}")

    # ---- Addendum (not pre-registered): grading block and distinct-task denominators ----
    print("\n== Addendum: EXP-038 graded exit code by stage; gold patch unresolved in the sandbox (EXP-038 re-grade GOLD pass)")
    gold_rg = RUNS / "EXP-038-regrade" / "GOLD" / "regrade.jsonl"
    gold_fail = {d["instance_id"] for d in jl(gold_rg) if not d.get("resolved")} if gold_rg.exists() else set()
    print(f"  gold unresolved in the sandbox: {len(gold_fail)}: {','.join(sorted(gold_fail))}")
    rd, summ, res = load_run(DEV)
    for k in ORDER:
        ids = sorted(t for t, c in stage[DEV].items() if c == k)
        ex = collections.Counter(str(res[t].get("test_exit_code")) for t in ids)
        print(f"  {k} n {len(ids)} exit {dict(sorted(ex.items()))} gold-blocked {sum(t in gold_fail for t in ids)} "
              f"{','.join(t for t in ids if t in gold_fail) or '-'}")
    for label, group in (("dispatch", PIPE), ("early", PIPE_EARLY)):
        fr = sorted({t for n in group for t, c in stage[n].items() if c in "FR"})
        sc = collections.Counter(c for n in group for t, c in stage[n].items() if c.isupper() and t in gold_fail)
        print(f"  {label}: distinct tasks with an F or R run {len(fr)}: {','.join(fr)}; unresolved runs on gold-blocked tasks {dict(sc)}")

    # ---- Q5 ----
    anyr, e4b = ever_resolved()
    print(f"\n== Q5 ever-resolved: any agent run {len(anyr)} tasks; E4B runs {len(e4b)} tasks")
    dev_ids = sorted(stage[DEV])
    print(f"  dev-48 ids ever resolved (any) {sum(t in anyr for t in dev_ids)}; (E4B) {sum(t in e4b for t in dev_ids)}")
    opp = collections.Counter()
    opp_e4b = collections.Counter()
    for tid, c in stage[DEV].items():
        if c.isupper():
            opp[c] += tid in anyr
            opp_e4b[c] += tid in e4b
    print(f"  EXP-038 unresolved by class, task in ever-resolved (any): {dist([c for t, c in stage[DEV].items() if c.isupper() and t in anyr])}")
    print(f"  EXP-038 unresolved by class, task in ever-resolved (E4B): {dist([c for t, c in stage[DEV].items() if c.isupper() and t in e4b])}")
    print(f"  ids: " + "; ".join(f"{k}: {','.join(sorted(t for t, c in stage[DEV].items() if c == k and t in anyr))}" for k in ORDER))
    print(f"  opportunity sum (any) {sum(opp.values())}, shortfall vs 11: {11 - sum(opp.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
