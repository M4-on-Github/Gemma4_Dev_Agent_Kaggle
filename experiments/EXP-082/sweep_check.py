#!/usr/bin/env python3
"""EXP-082: would a grep of the identifiers an agent changed have found the gold regions its partial fix missed?
Zero GPU. Rules: experiments/EXP-082-sweep-findability-partial-fixes.md sections 2 to 4 and 6.

Prints ids, counts and booleans only (plan.md:52: no gold, patch, trace or repository text, no repository paths).
Usage: python -I -X utf8 experiments/EXP-082/sweep_check.py --out experiments/EXP-082/counts.json
"""
from __future__ import annotations

import argparse
import builtins
import collections
import json
import keyword
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "EXP-074"))
import diag  # noqa: E402

M = 5            # diag.classify margin (EXP-074 section 2.3)
CTX = 3          # unified-diff context depth
NONSRC = diag.NONSRC
IMPOSSIBLE = {"httpx_3672", "requests_7205", "requests_7309", "requests_7315", "requests_7427"}
STOP = set(keyword.kwlist) | set(getattr(keyword, "softkwlist", [])) | set(dir(builtins))
TOK = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

MODELS = {
    "31B": {
        "runs": [("EXP-028-armR", "R"), ("EXP-028-armRH", "RH")],
        "expected_c": {"EXP-028-armR": 13, "EXP-028-armRH": 11},
        "go": 10, "drop": 6, "band": (2, 3), "next": 4,
    },
    "E4B": {
        "runs": [("EXP-038-e4b-dev48", None), ("EXP-077-base", None), ("EXP-075-t02", None), ("EXP-078-t02r", None)],
        "expected_c": {"EXP-038-e4b-dev48": 8, "EXP-077-base": 12, "EXP-075-t02": 9, "EXP-078-t02r": 9},
        "go": 16, "drop": 10, "band": (2, 2), "next": 3,
    },
}
ARM_R_EXPECTED = {"E": 6, "F": 3, "R": 6, "C": 14, "S": 10, "resolved": 9}


# ---------- line walker (mirrors diag.parse_diff's state machine) ----------
def walk(text: str):
    """Yield (file, tag, old_no, line_text) with tag in '-', '+', ' '. '+' lines carry the next old line number."""
    cur = None
    old_no = 0
    left_old = left_new = 0
    for ln in (text or "").split("\n"):
        if left_old > 0 or left_new > 0:
            if cur is None:
                left_old = left_new = 0
            elif ln.startswith("-"):
                yield cur, "-", old_no, ln[1:]
                old_no += 1
                left_old -= 1
                continue
            elif ln.startswith("+"):
                yield cur, "+", old_no, ln[1:]
                left_new -= 1
                continue
            elif ln.startswith(" ") or ln == "":
                yield cur, " ", old_no, ln[1:]
                old_no += 1
                left_old -= 1
                left_new -= 1
                continue
            elif ln.startswith("\\"):
                continue
        if ln.startswith("diff --git "):
            cur = None
            continue
        if ln.startswith("--- "):
            a = ln[4:].split("\t")[0]
            cur = diag.norm_path(a[2:]) if a.startswith("a/") else None
            continue
        if ln.startswith("+++ "):
            b = ln[4:].split("\t")[0]
            if b.startswith("b/"):
                cur = diag.norm_path(b[2:])
            continue
        m = re.match(r"^@@ -(\d+)(?:,(\d+))? \+\d+(?:,(\d+))? @@", ln)
        if m:
            old_no = int(m.group(1))
            left_old = int(m.group(2)) if m.group(2) is not None else 1
            left_new = int(m.group(3)) if m.group(3) is not None else 1
            if left_old == 0:
                old_no += 1
            continue


def idents(text: str, variant: str) -> set[str]:
    out = {t for t in TOK.findall(text) if len(t) >= 4 and t not in STOP}
    if variant in ("V1", "V2"):
        out = {t for t in out if t not in ("self", "cls") and not (t.startswith("__") and t.endswith("__"))}
    return out


def agent_tokens(patch: str, variant: str) -> set[str]:
    out: set[str] = set()
    for f, tag, _, txt in walk(patch):
        if tag in "+-" and not f.startswith(NONSRC):
            out |= idents(txt, variant)
    return out


def region_tokens(gold_entries: list, reg: tuple[int, int], variant: str) -> set[str]:
    lo, hi = reg[0] - CTX, reg[1] + CTX
    out: set[str] = set()
    for tag, old_no, txt in gold_entries:
        if tag == "+" or not (lo <= old_no <= hi):
            continue
        if variant == "V2" and tag != "-":
            continue
        out |= idents(txt, variant)
    return out


def analyse(patch: str, greg: dict, gold_entries: dict) -> dict:
    p = diag.parse_diff(patch)
    atoks = {v: agent_tokens(patch, v) for v in ("V0", "V1", "V2")}
    total = hit = 0
    flags = {v: [] for v in atoks}
    for f, rs in greg.items():
        lines = set().union(*[l for x, l in p.items() if diag.same_file(f, x)] or [set()])
        for r in rs:
            total += 1
            if diag.touches(lines, r, M):
                hit += 1
                continue
            for v in atoks:
                flags[v].append(bool(atoks[v] & region_tokens(gold_entries.get(f, []), r, v)))
    out = {"regions": total, "hit": hit, "missed": total - hit}
    for v in atoks:
        out[v + "_all"] = bool(flags[v]) and all(flags[v])
        out[v + "_any"] = any(flags[v])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "experiments" / "EXP-082" / "counts.json"))
    a = ap.parse_args()

    tasks = {}
    for l in open(ROOT / "data/raw/tasks.jsonl", encoding="utf-8"):
        t = json.loads(l)
        tasks[t["instance_id"]] = t
    dev = [l.strip() for l in open(ROOT / "experiments/cohorts/dev-48.txt", encoding="utf-8")
           if l.strip() and not l.startswith("#")]
    gate = {d["task_id"]: d for d in diag.jl(ROOT / "experiments/EXP-036/summary.jsonl")}

    greg_of, gold_entries_of = {}, {}
    for tid in dev:
        g = tasks[tid]["patch"]
        greg_of[tid] = diag.gold_regions(g, M)
        ents: dict[str, list] = collections.defaultdict(list)
        for f, tag, old_no, txt in walk(g):
            ents[f].append((tag, old_no, txt))
        gold_entries_of[tid] = dict(ents)

    report: dict = {"instrument": {}, "models": {}}
    instrument_ok = True
    per_run_rows: dict[str, dict[str, list]] = {}

    for model, cfg in MODELS.items():
        rows_unit, rows_r = [], []
        print(f"\n== {model}")
        for run, gate_key in cfg["runs"]:
            rd, summ, res = diag.load_run(run)
            raw = collections.Counter()
            excl = collections.Counter()
            for tid in sorted(summ):
                if tid not in greg_of:
                    continue
                s = summ[tid]
                patch = res[tid].get("patch") or ""
                c = diag.classify(patch, bool(s["patch_empty"]), greg_of[tid], M)
                if s["resolved"]:
                    raw["resolved"] += 1
                    excl["resolved"] += 1
                    continue
                raw[c] += 1
                if tid in IMPOSSIBLE:
                    excl["impossible"] += 1
                    continue
                if gate_key and gate.get(tid, {}).get(f"{gate_key}_resolved_regraded"):
                    excl["gap"] += 1
                    continue
                excl[c] += 1
                if c in "CR":
                    an = analyse(patch, greg_of[tid], gold_entries_of[tid])
                    an.update({"task": tid, "run": run, "cls": c})
                    ok = an["missed"] >= 1 and (an["hit"] > 0 if c == "C" else an["hit"] == 0)
                    an["consistent"] = ok
                    (rows_unit if c == "C" else rows_r).append(an)
            exp_c = cfg["expected_c"][run]
            got_c = excl["C"]
            good = got_c == exp_c
            instrument_ok &= good
            print(f"  {run:20s} tasks {len(summ)} raw {dict(raw)} exclusive {dict(excl)} C {got_c} expected {exp_c} {'ok' if good else 'MISMATCH'}")
            report["instrument"][run] = {"raw": dict(raw), "exclusive": dict(excl), "C": got_c, "expected_C": exp_c}
            if run == "EXP-028-armR":
                armr = {k: raw.get(k, 0) for k in ("E", "F", "R", "C", "S", "resolved")}
                good2 = armr == ARM_R_EXPECTED
                instrument_ok &= good2
                print(f"  arm R raw classes {armr} expected {ARM_R_EXPECTED} {'ok' if good2 else 'MISMATCH'}")
                report["instrument"]["armR_raw"] = armr

        n_incons = sum(1 for r in rows_unit + rows_r if not r["consistent"])
        instrument_ok &= n_incons == 0
        print(f"  region rows inconsistent with class letter: {n_incons}")

        def cnt(rows, key):
            ts = {r["task"] for r in rows if r[key]}
            return sum(1 for r in rows if r[key]), len(ts)

        res_m = {"pool": len(rows_unit), "distinct_tasks": len({r["task"] for r in rows_unit}), "inconsistent": n_incons}
        print(f"  unit task-runs (C) {res_m['pool']} on {res_m['distinct_tasks']} distinct tasks")
        for v in ("V0", "V1", "V2"):
            allc, allt = cnt(rows_unit, v + "_all")
            anyc, anyt = cnt(rows_unit, v + "_any")
            res_m[v] = {"all_runs": allc, "all_tasks": allt, "any_runs": anyc, "any_tasks": anyt}
            print(f"  {v}: all missed findable {allc} runs on {allt} tasks; any missed findable {anyc} runs on {anyt} tasks")
        r_m = {"runs": len(rows_r), "distinct_tasks": len({r["task"] for r in rows_r})}
        for v in ("V0", "V1"):
            allc, allt = cnt(rows_r, v + "_all")
            r_m[v + "_all_runs"] = allc
            r_m[v + "_all_tasks"] = allt
        print(f"  third count (class R runs) {r_m}")
        res_m["third_count_R"] = r_m

        v0, v1 = res_m["V0"]["all_runs"], res_m["V1"]["all_runs"]
        if not instrument_ok:
            verdict = "row 1 (instrument), verdict not read"
        elif v0 < cfg["drop"]:
            verdict = "row 2 DROP"
        elif v0 >= cfg["go"] and v1 >= cfg["drop"]:
            verdict = "row 3 GO"
        else:
            verdict = "row 4 BETWEEN"
        print(f"  thresholds go {cfg['go']} drop {cfg['drop']}: V0 {v0} V1 {v1} -> {verdict}")
        res_m["verdict"] = verdict
        res_m["rows"] = [{k: (int(v) if isinstance(v, bool) else v) for k, v in r.items()} for r in rows_unit]

        print("  per unit task-run: task run regions hit missed V0all V0any V1all V1any V2all V2any")
        for r in sorted(rows_unit, key=lambda r: (r["task"], r["run"])):
            print(f"    {r['task']:16s} {r['run']:20s} {r['regions']} {r['hit']} {r['missed']} "
                  f"{int(r['V0_all'])} {int(r['V0_any'])} {int(r['V1_all'])} {int(r['V1_any'])} {int(r['V2_all'])} {int(r['V2_any'])}")

        # ---- step 2 selection (rule fixed in section 6) ----
        lo, hi = cfg["band"]
        unit_by = collections.defaultdict(list)
        for r in rows_unit:
            unit_by[r["task"]].append(r)
        r_tasks = {r["task"] for r in rows_r}

        def key(tid):
            u = unit_by.get(tid, [])
            return (-sum(r["V1_all"] for r in u), -sum(r["V1_any"] for r in u), -len(u), tid)

        elig = [t for t in dev if t not in IMPOSSIBLE]
        nreg = {t: sum(len(x) for x in greg_of[t].values()) for t in elig}
        tier1 = sorted([t for t in elig if lo <= nreg[t] <= hi and t in unit_by], key=key)
        tier2 = sorted([t for t in elig if lo <= nreg[t] <= hi and t not in unit_by and t in r_tasks], key=key)
        tier3 = sorted([t for t in elig if nreg[t] == cfg["next"] and t in unit_by], key=key)
        pick = (tier1 + tier2 + tier3)[:8]
        print(f"  step 2 selection ({len(tier1)} tier1, {len(tier2)} tier2, {len(tier3)} tier3), first 8: {','.join(pick)}")
        print("  regions of picked: " + " ".join(f"{t}={nreg[t]}" for t in pick))
        res_m["step2_selection"] = pick
        report["models"][model] = res_m

    report["instrument_ok"] = instrument_ok
    print(f"\ninstrument {'OK' if instrument_ok else 'FAIL (row 1: verdicts not read)'}")
    Path(a.out).write_text(json.dumps(report, indent=1, sort_keys=True), encoding="utf-8")
    print(f"wrote {Path(a.out).name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
