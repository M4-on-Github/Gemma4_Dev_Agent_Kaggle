#!/usr/bin/env python3
"""EXP-080 Part 2 (zero GPU): the sample, the scripted items (c', d, e1 to e4, g), the reading windows, and, once the
hand codes exist, the join, the task-unit separation call and the D-011 opportunity counts (EXP-080 sections 2.3-2.7).

Modes:
  python -I -X utf8 experiments/EXP-080/items.py scripted
      scripted items over the sample and over all 48 tasks of each run; thresholds. Prints ids, labels, counts only.
  python -I -X utf8 experiments/EXP-080/items.py dump OUTDIR
      writes the reading windows under shuffled opaque keys to OUTDIR (scratchpad only, never committed: they hold
      thought text, issue text and patch lines) and the key map OUTDIR/keymap.json.
  python -I -X utf8 experiments/EXP-080/items.py join CODES KEYMAP
      CODES: one line per key, "KEY a b c f [added...]". Writes experiments/EXP-080/codes.csv (ids and labels only)
      and prints the separation and opportunity tables.
"""
from __future__ import annotations

import collections
import json
import math
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "EXP-075"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-063"))
import noise  # noqa: E402
import refs  # noqa: E402

diag = noise.diag
REF = "EXP-028-armR"
DRAWS = ["EXP-038-e4b-dev48", "EXP-077-base", "EXP-075-t02", "EXP-078-t02r"]
BASE = DRAWS[:2]
RUNS = [REF] + DRAWS
CAP_S, CAP_CALLS, CUT = 480.0, 28, 2500
DEF_RE = re.compile(r"^\s*(?:async\s+)?(?:def|class)\s+(\w+)")
CHECK_RE = re.compile(r"(?:^|&&|;|\|\||\||\()\s*(?:timeout\s+\S+\s+)?(?:\S*/)?(?:python3?|pytest)\b")
CHANGE = ("edit_file", "write_file")


def tasks() -> dict:
    return {json.loads(l)["instance_id"]: json.loads(l) for l in open(ROOT / "data/raw/tasks.jsonl", encoding="utf-8")}


def rdir(name: str) -> Path:
    return ROOT / "runs" / REF if name == REF else noise.run_dir(name)


def steps_of(name: str, tid: str) -> list[dict]:
    st = json.load(open(rdir(name) / "traces" / f"trace_{tid}.json", encoding="utf-8")).get("steps") or []
    return [s for s in st if s.get("source") == "agent"]


def fn_of(tc: dict) -> str:
    return tc.get("function_name") or tc.get("name") or ""


def obs_of(s: dict) -> str:
    return str((s.get("observation") or {}).get("content") or "")


def decoded(text: str) -> str:
    out = [text, text.replace("\\n", "\n").replace('\\"', '"').replace("\\t", "\t").replace("\\\\", "\\")]

    def walk(x):
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    try:
        walk(json.loads(text))
    except ValueError:
        pass
    return "\n".join(out)


def is_change(s: dict, tc: dict) -> bool:
    return fn_of(tc) in CHANGE and bool(refs.args_of(tc)) and not refs.failed(obs_of(s))


def first_change(ms: list[dict]) -> int | None:
    for i, s in enumerate(ms):
        if any(is_change(s, tc) for tc in s.get("tool_calls") or []):
            return i
    return None


def submit_step(ms: list[dict]) -> int | None:
    for i, s in enumerate(ms):
        if any(fn_of(tc) == "submit_patch" for tc in s.get("tool_calls") or []):
            return i
    return None


def thought(s: dict) -> str:
    return str(s.get("message") or "") if (s.get("extra") or {}).get("event_type") == "thinking" else ""


def enclosing_names(tid: str, gold_patch: str) -> list[str | None]:
    snap = diag.snapshot(tid)
    out = []
    for f, rs in diag.gold_regions(gold_patch, 5).items():
        src = next((v for k, v in snap.items() if diag.same_file(k, f)), None)
        lines = src.split("\n") if src else []
        for lo, _hi in rs:
            name = None
            for j in range(min(lo, len(lines)) - 1, -1, -1):
                m = DEF_RE.match(lines[j])
                if m:
                    name = m.group(1)
                    break
            out.append(name)
    return out


def scripted(name: str, tid: str, t: dict, summ: dict) -> dict:
    ms = steps_of(name, tid)
    fc, sub = first_change(ms), submit_step(ms)
    # c'
    upto = ms if sub is None else ms[: sub + 1]
    text = "\n".join(thought(s) for s in upto)
    names = enclosing_names(tid, t["patch"])
    cprime = sum(1 for n in names if n and re.search(r"\b" + re.escape(n) + r"\b", text))
    # d
    seen = []
    edits = ok = 0
    for s in ms:
        for tc in s.get("tool_calls") or []:
            if fn_of(tc) == "edit_file" and is_change(s, tc):
                old = str(refs.args_of(tc).get("old_string") or "")
                lines = [x.strip() for x in old.split("\n") if x.strip()]
                pool = "\n".join(seen)
                edits += 1
                ok += bool(lines) and all(x in pool for x in lines)
        seen.append(decoded(obs_of(s)))
    d = "na" if edits == 0 else ("y" if ok == edits else "n")
    # e
    checks = []
    forms = []
    last_change = None
    for i, s in enumerate(ms):
        for tc in s.get("tool_calls") or []:
            if is_change(s, tc):
                last_change = i
            if fc is not None and i > fc and fn_of(tc) == "run_command":
                cmd = str(refs.args_of(tc).get("command") or "")
                if CHECK_RE.search(cmd):
                    checks.append((i, refs.exit_code(obs_of(s))))
                    forms.append(("pytest" if re.search(r"\bpytest\b", cmd) else "python -c" if re.search(r"\s-c\s", cmd)
                                  else "python other", checks[-1][1]))
    e1 = "y" if checks else "n"
    bad = [i for i, x in checks if x not in ("0",)]
    e2 = "na" if not checks else ("y" if bad else "n")
    e3 = "na" if e2 != "y" else ("fix" if last_change is not None and last_change > bad[-1] else "ign")
    e4 = "na" if not checks else ("pass" if checks[-1][1] == "0" else "fail")
    g = "y" if summ["submit_patch_called"] and not (summ["calls_cap_hit"] or summ["time_cap_hit"] or summ["timeout_hit"]) else "n"
    return {"cprime": cprime, "k": len(names), "d": d, "d_edits": edits, "d_ok": ok, "e1": e1, "e2": e2, "e3": e3,
            "e4": e4, "n_checks": len(checks), "check_forms": forms, "g": g, "time_left": round(CAP_S - float(summ["wall_s"]), 1),
            "calls_left": max(0, CAP_CALLS - int(summ["n_calls"] or 0))}


def sample(T: dict) -> tuple[list[tuple[str, str]], list[str], dict]:
    ever = sorted(diag.ever_resolved()[0])
    cl = {r: noise.classes(r, T) for r in RUNS}
    e4b = [(d, t) for d in DRAWS for t in ever if cl[d][t] in ("R", "C", "S")]
    tids = sorted({t for _d, t in e4b})
    return e4b, tids, cl


def thresholds() -> dict:
    res = [sum(1 for d in diag.jl(rdir(b) / "summary.jsonl") if d["resolved"]) for b in BASE]
    p = sum(res) / (2 * 48)
    sd = math.sqrt(48 * p * (1 - p))
    gap = abs(res[0] - res[1])
    return {"base": res, "p": p, "gap": gap, "two_v_two": max(gap, 2 * sd), "one_v_one": max(gap, 2 * math.sqrt(2) * sd)}


def regraded() -> dict:
    return {d["task_id"]: d for d in (json.loads(l) for l in open(ROOT / "experiments/EXP-036/summary.jsonl", encoding="utf-8"))}


YES = {"a": "y", "b": "y", "c": "all", "f": "y", "d": "y", "e1": "y", "e2": "y", "e3": "fix", "e4": "pass", "g": "y"}


def rate(vals: list[str], item: str) -> tuple[int, int]:
    v = [x for x in vals if x not in ("na", "w")]
    return sum(1 for x in v if x == YES[item]), len(v)


def cmd_scripted() -> int:
    T = tasks()
    e4b, tids, cl = sample(T)
    print(f"sample: {len(e4b)} E4B runs on {len(tids)} tasks {tids}")
    print("   by draw " + " ".join(f"{d}:{sum(1 for x, _ in e4b if x == d)}" for d in DRAWS)
          + "; by class " + str(dict(collections.Counter(cl[d][t] for d, t in e4b))))
    G = regraded()
    print("arm R on the 11: " + " ".join(f"{t}:{cl[REF][t]}{'v' if G[t]['R_resolved_regraded'] else '-'}" for t in tids))
    th = thresholds()
    print(f"D-011 thresholds: base resolves {th['base']}, pooled p {th['p']:.4f}, gap {th['gap']}, "
          f"two against two more than {th['two_v_two']:.2f}, one against one more than {th['one_v_one']:.2f}")
    allrows = {}
    for r in RUNS:
        summ = {d["task_id"]: d for d in diag.jl(rdir(r) / "summary.jsonl")}
        allrows[r] = {t: scripted(r, t, T[t], summ[t]) for t in sorted(summ)}
    print("scripted, sample runs (draw task class: c'/k d(ok/edits) e1 e2 e3 e4 g time_left calls_left)")
    for d, t in e4b:
        x = allrows[d][t]
        print(f"   {d:18s} {t:15s} {cl[d][t]} {x['cprime']}/{x['k']} {x['d']}({x['d_ok']}/{x['d_edits']}) {x['e1']} {x['e2']} "
              f"{x['e3']} {x['e4']} {x['g']} {x['time_left']} {x['calls_left']}")
    for t in tids:
        x = allrows[REF][t]
        print(f"   {REF:18s} {t:15s} {cl[REF][t]} {x['cprime']}/{x['k']} {x['d']}({x['d_ok']}/{x['d_edits']}) {x['e1']} {x['e2']} "
              f"{x['e3']} {x['e4']} {x['g']} {x['time_left']} {x['calls_left']}")
    print("scripted items over all 48 tasks, per run: yes/denominator")
    items = ["d", "e1", "e2", "e3", "e4", "g"]
    for r in RUNS:
        rows = allrows[r].values()
        tl = sorted(x["time_left"] for x in rows)
        cl_ = sorted(x["calls_left"] for x in rows)
        print(f"   {r:18s} " + " ".join(f"{it} {'/'.join(map(str, rate([x[it] for x in rows], it)))}" for it in items)
              + f"  median time left {tl[len(tl) // 2]:.1f} calls left {cl_[len(cl_) // 2]}")
    print("model-level separation over 48 (arm R outside the four-draw range by more than 2 SD one against one)")
    for it in items:
        rs = []
        for d in DRAWS:
            y, n = rate([x[it] for x in allrows[d].values()], it)
            rs.append((y, n))
        p = sum(y for y, _ in rs) / max(1, sum(n for _, n in rs))
        ry, rn = rate([x[it] for x in allrows[REF].values()], it)
        rr = ry / max(1, rn)
        lo, hi = min(y / max(1, n) for y, n in rs), max(y / max(1, n) for y, n in rs)
        sd2 = 2 * math.sqrt(2 * p * (1 - p) / 48)  # as written in section 2.7
        n_avg = sum(n for _, n in rs) / 4
        sd2_own = 2 * math.sqrt(2 * p * (1 - p) / max(1.0, n_avg))  # sensitivity: the item's own mean denominator
        out = rr - hi if rr > hi else lo - rr if rr < lo else 0.0
        print(f"   {it}: draws " + " ".join(f"{y}/{n}" for y, n in rs) + f" range {lo:.3f}-{hi:.3f}; arm R {ry}/{rn} = {rr:.3f}; "
              f"outside by {out:.3f}, 2 SD {sd2:.3f} -> {'separates' if out > sd2 else 'does not separate'}"
              f" (own-denominator 2 SD {sd2_own:.3f} -> {'separates' if out > sd2_own else 'does not separate'})")
        if out > sd2:
            fail_yes = rr < lo
            opp = []
            for d in DRAWS:
                bad = [t for t, x in allrows[d].items() if x[it] not in ("na", "w") and (x[it] == YES[it]) == fail_yes]
                opp.append((len(bad), sum(1 for t in bad if G[t]["R_resolved_regraded"]),
                            sum(1 for t in bad if G[t]["R_resolved_regraded"] and cl[d][t].isupper())))
            m = (opp[0][1] + opp[1][1]) / 2
            m2 = (opp[0][2] + opp[1][2]) / 2
            print(f"      opportunity {it} over 48: per draw loose/conditioned/conditioned-unresolved " + " ".join(f"{a}/{b}/{c}" for a, b, c in opp)
                  + f"; base-pair mean conditioned {m:.1f} -> "
                  + ("exceeds" if m > th["two_v_two"] else "cannot clear the rule at full conversion")
                  + f"; with resolved E4B runs left out {m2:.1f} -> "
                  + ("exceeds" if m2 > th["two_v_two"] else "cannot clear the rule at full conversion"))
    print("post hoc (not pre-registered): check form and exit codes of the e1 checks, per run")
    pool = {False: collections.Counter(), True: collections.Counter()}
    for r in RUNS:
        form, ex, fx = collections.Counter(), collections.Counter(), collections.Counter()
        for t in allrows[r]:
            for f_, x_ in allrows[r][t]["check_forms"]:
                form[f_] += 1
                ex[x_] += 1
                fx[(f_, "0" if x_ == "0" else "non-zero")] += 1
        print(f"   {r:18s} forms {dict(sorted(form.items()))} exits {dict(sorted(ex.items()))}")
        print(f"   {'':18s} form x exit " + "; ".join(f"{a} {b} {n}" for (a, b), n in sorted(fx.items())))
        pool[r != REF].update(fx)
    for side, lab in ((False, "arm R"), (True, "E4B four draws pooled")):
        tot = collections.Counter()
        for (a, b), n in pool[side].items():
            tot[a] += n
        print(f"   {lab}: " + "; ".join(f"{a} non-zero {pool[side][(a, 'non-zero')]} of {tot[a]}" for a in sorted(tot))
              + f"; all forms exit 0 {sum(n for (a, b), n in pool[side].items() if b == '0')} of {sum(tot.values())}")
    return 0


def window(ms: list[dict]) -> tuple[list[str], float]:
    fc, sub = first_change(ms), submit_step(ms)
    th = [i for i, s in enumerate(ms) if thought(s)]
    if fc is not None:
        w1 = [i for i in (fc - 1, fc) if i >= 0 and thought(ms[i])]
    else:
        w1 = th[-2:]
    w2 = sub if sub is not None and thought(ms[sub]) else (th[-1] if th else None)
    idx = list(w1) + ([w2] if w2 is not None and w2 not in w1 else [])
    parts = [thought(ms[i])[-CUT:] for i in idx]
    total = sum(len(thought(s)) for s in ms)
    return [f"--- step {i} of {len(ms)} ---\n{p}" for i, p in zip(idx, parts)], sum(len(p) for p in parts) / max(1, total)


def changed(patch: str, cap: int) -> str:
    keep = [l for l in patch.split("\n") if l.startswith(("+", "-", "@@", "diff --git"))]
    return "\n".join(keep[:cap])


def src_only(patch: str, files: list[str]) -> str:
    out, keep = [], False
    for line in patch.split("\n"):
        if line.startswith(("diff --git", "--- ")):
            keep = False
        if line.startswith("+++ "):
            name = line[4:].split("\t")[0].strip()
            name = name[2:] if name.startswith("b/") else name
            keep = any(diag.same_file(f, name) for f in files)
            if keep:
                out.append("diff --git " + name)
            continue
        if keep:
            out.append(line)
    return "\n".join(out)


def cmd_dump(outdir: Path) -> int:
    T = tasks()
    e4b, tids, _cl = sample(T)
    units = list(e4b) + [(REF, t) for t in tids]
    keys = [f"K{i:02d}" for i in range(len(units))]
    random.Random(80).shuffle(units)
    outdir.mkdir(parents=True, exist_ok=True)
    kmap, share = {}, {}
    for k, (r, t) in zip(keys, units):
        res = {d["instance_id"]: d for d in diag.jl(rdir(r) / "task_results.jsonl")}
        ms = steps_of(r, t)
        w, sh = window(ms)
        g = diag.gold_regions(T[t]["patch"], 5)
        gold_src = src_only(T[t]["patch"], list(g))
        body = (f"# {k}  task {t}\n## ISSUE\n{T[t]['problem_statement'][:2000]}\n## GOLD SOURCE DIFF (regions {sum(len(v) for v in g.values())})\n"
                f"{changed(gold_src, 120)}\n## RUN PATCH\n{changed(res[t].get('patch') or '', 60)}\n## WINDOW\n" + "\n".join(w))
        (outdir / f"{k}.txt").write_text(body, encoding="utf-8")
        kmap[k] = [r, t]
        share[k] = round(sh, 3)
    json.dump({"map": kmap, "share": share}, open(outdir / "keymap.json", "w", encoding="utf-8"), indent=0)
    print(f"wrote {len(units)} windows to {outdir}")
    return 0


def cmd_join(codes: Path, kmap_path: Path) -> int:
    T = tasks()
    e4b, tids, cl = sample(T)
    km = json.load(open(kmap_path, encoding="utf-8"))
    G = regraded()
    rows = []
    for line in open(codes, encoding="utf-8"):
        p = line.split()
        if not p or p[0].startswith("#"):
            continue
        r, t = km["map"][p[0]]
        summ = {d["task_id"]: d for d in diag.jl(rdir(r) / "summary.jsonl")}
        x = scripted(r, t, T[t], summ[t])
        row = {"run": r, "task_id": t, "class": cl[r][t], "armR_regraded_resolved": G[t]["R_resolved_regraded"],
               "window_share": km["share"][p[0]], "a": p[1], "b": p[2], "c": p[3], "f": p[4],
               "added": p[5:], **{k: x[k] for k in ("cprime", "k", "d", "e1", "e2", "e3", "e4", "g", "time_left", "calls_left")}}
        rows.append(row)
    rows.sort(key=lambda z: (z["run"] != REF, z["run"], z["task_id"]))
    cols = ["run", "task_id", "class", "armR_regraded_resolved", "window_share", "a", "b", "c", "f", "x1",
            "cprime", "k", "d", "e1", "e2", "e3", "e4", "g", "time_left", "calls_left"]
    with open(ROOT / "experiments/EXP-080/codes.csv", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(",".join(cols) + "\n")
        for z in rows:
            v = {**z, "x1": " ".join(z["added"])}
            fh.write(",".join(str(v[c]) for c in cols) + "\n")
    print(f"joined {len(rows)} coded runs; E4B {sum(1 for z in rows if z['run'] != REF)}, arm R {sum(1 for z in rows if z['run'] == REF)}")
    for z in rows:
        print(f"   {z['run']:18s} {z['task_id']:15s} {z['class']} R{'v' if z['armR_regraded_resolved'] else '-'} share {z['window_share']:.3f} "
              f"a {z['a']} b {z['b']} c {z['c']} f {z['f']} {' '.join(z['added'])} | c' {z['cprime']}/{z['k']} d {z['d']} "
              f"e1 {z['e1']} e2 {z['e2']} e3 {z['e3']} e4 {z['e4']} g {z['g']} {z['time_left']} {z['calls_left']}")
    sh_e = sorted(z["window_share"] for z in rows if z["run"] != REF)
    sh_r = sorted(z["window_share"] for z in rows if z["run"] == REF)
    print(f"window share median: E4B {sh_e[len(sh_e) // 2]:.3f}, arm R {sh_r[len(sh_r) // 2]:.3f}")
    th = thresholds()
    n_added = max((len(z["added"]) for z in rows), default=0)
    items = ["a", "b", "c", "f", "d", "e1", "e2", "e3", "e4", "g"] + [f"x{i + 1}" for i in range(n_added)]
    for i in range(n_added):
        YES[f"x{i + 1}"] = "y"
        for z in rows:
            z[f"x{i + 1}"] = z["added"][i] if i < len(z["added"]) else "na"
    def analyse(rows, label):
        print(f"[{label}] item | E4B runs yes/n | arm R runs yes/n | tasks both | mean r - mean e | untied | with sign | call | like-for-like (arm R unresolved R/C/S)")
        calls = {}
        for it in items:
            E = collections.defaultdict(list)
            Rv = {}
            for z in rows:
                v = z[it]
                if v in ("na", "w"):
                    continue
                (E[z["task_id"]].append(v == YES[it]) if z["run"] != REF else Rv.__setitem__(z["task_id"], v == YES[it]))
            ey, en = rate([z[it] for z in rows if z["run"] != REF], it)
            ry, rn = rate([z[it] for z in rows if z["run"] == REF], it)
            both = [t for t in tids if t in E and t in Rv]

            def stat(ts):
                if not ts:
                    return 0.0, 0, 0
                e = {t: sum(E[t]) / len(E[t]) for t in ts}
                diff = sum(Rv[t] for t in ts) / len(ts) - sum(e.values()) / len(ts)
                unt = [t for t in ts if abs(Rv[t] - e[t]) > 1e-9]
                sgn = sum(1 for t in unt if (Rv[t] - e[t]) * diff > 0)
                return diff, len(unt), sgn
            diff, unt, sgn = stat(both)
            c1 = abs(diff) >= 0.30
            c2 = unt >= 4 and sgn >= 0.75 * unt
            call = "separates" if c1 and c2 else "leans" if c1 or c2 else "does not separate"
            calls[it] = (call, diff)
            lfl = [t for t in both if cl[REF][t] in ("R", "C", "S") and not G[t]["R_resolved_regraded"]]
            d2, u2, s2 = stat(lfl)
            print(f"   {it:3s} | {ey}/{en} | {ry}/{rn} | {len(both)} | {diff:+.3f} | {unt} | {sgn} | {call} | tasks {len(lfl)} diff {d2:+.3f} untied {u2} sign {s2}")
            split = collections.Counter((cl[REF][z['task_id']].upper() + ('v' if z['armR_regraded_resolved'] else '-'), z[it])
                                        for z in rows if z["run"] == REF)
            print(f"         arm R split by its stage and re-graded flag: " + " ".join(f"{k[0]}:{k[1]}={v}" for k, v in sorted(split.items())))
        print(f"D-011 two against two threshold: more than {th['two_v_two']:.2f} per draw (one against one {th['one_v_one']:.2f})")
        for it, (call, diff) in calls.items():
            if call != "separates":
                continue
            fail_yes = diff < 0  # arm R lower: the E4B failing state is the yes label
            out = []
            for d in DRAWS:
                zs = [z for z in rows if z["run"] == d and z[it] not in ("na", "w")]
                bad = [z for z in zs if (z[it] == YES[it]) == fail_yes]
                out.append((len(bad), sum(1 for z in bad if z["armR_regraded_resolved"])))
            base = [out[0], out[1]]
            print(f"   opportunity {it}: per draw loose/conditioned " + " ".join(f"{a}/{b}" for a, b in out)
                  + f"; base-pair mean conditioned {sum(b for _, b in base) / 2:.1f} -> "
                  + ("exceeds" if sum(b for _, b in base) / 2 > th["two_v_two"] else "cannot clear the rule at full conversion"))
    analyse(rows, "all coded runs")
    ungr = [z for z in rows if z["run"] in DRAWS[1:] and G[z["task_id"]]["gated"]]
    print(f"sample E4B runs that are un-regraded gated cells (EXP-077, EXP-075, EXP-078 on EXP-036 gated ids): {len(ungr)}: "
          + " ".join(f"{z['run']}:{z['task_id']}" for z in ungr))
    analyse([z for z in rows if z not in ungr], "un-regraded gated E4B runs dropped")
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "scripted"
    if mode == "dump":
        raise SystemExit(cmd_dump(Path(sys.argv[2])))
    if mode == "join":
        raise SystemExit(cmd_join(Path(sys.argv[2]), Path(sys.argv[3])))
    raise SystemExit(cmd_scripted())
