"""EXP-036 analysis: resolves, flips and the recomputed EXP-035 table on the re-graded R / RH / GOLD / BASE passes.

Definitions are the ones pre-registered in experiments/EXP-036-regrade-R-RH-with-shims.md, section 2.3.
- The gated set and regex come from experiments/EXP-034/posthoc_gated.py.
- The RFWF definition comes from EXP-034's mine.py.
- The per-test classifier comes from experiments/EXP-035/grader_tests.py, imported, not copied.

The script reads runs/ and data/, both gitignored. It writes:
- --out: counts and task ids only;
- --summary: per task, the id and booleans only;
- --rows: per-task V / H labels. Keep this file under runs/: the labels derive from the gold test patch (plan.md:52).

Run from the repo root as:
    python -I -X utf8 experiments/EXP-036/analyze_regrade.py --regrade runs/EXP-036-regrade \
        --tasks data/raw/tasks.jsonl --snapshots data/local/snapshots --out experiments/EXP-036/aggregates.json \
        --summary experiments/EXP-036/summary.jsonl --rows runs/EXP-036-regrade/rows.jsonl
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M = _load("exp034_mine", "experiments/EXP-034/mine.py")
G = _load("exp035_grader_tests", "experiments/EXP-035/grader_tests.py")

GATE_RE = re.compile(r"No module named '?(inline_snapshot|dirty_equals)")
ARMS = {"R": "runs/EXP-028-armR", "RH": "runs/EXP-028-armRH"}
PASSES = ("R", "RH", "GOLD", "BASE")
TAIL_CAP = 20000
EXP034_ALL48_V = {"union": 11, "best": 10, "union_minus_best": 1}


def load_jsonl(p):
    with open(p, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def tid_key(t):
    return (t[0], tuple(t[1]))


def parse(tail: str):
    # G.parse_tail drops the first line of a tail of 1500+ characters, its cut-off as run. Re-graded tails are cut
    # at TAIL_CAP. An uncut tail starts with the line "STDOUT:", so dropping that line is harmless; this is
    # asserted in main().
    return G.parse_tail(tail or "")


def failing_set(pt):
    return {tid_key(t) for t in pt["ids"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regrade", type=Path, default=Path("runs/EXP-036-regrade"))
    ap.add_argument("--tasks", type=Path, default=Path("data/raw/tasks.jsonl"))
    ap.add_argument("--snapshots", type=Path, default=Path("data/local/snapshots"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    ap.add_argument("--rows", type=Path, required=True)
    a = ap.parse_args()

    tasks = {t["instance_id"]: t for t in load_jsonl(a.tasks)}
    asrun = {arm: {(r.get("instance_id") or r.get("task_id")): r for r in load_jsonl(Path(d) / "task_results.jsonl")}
             for arm, d in ARMS.items()}
    rg = {p: {r["instance_id"]: r for r in load_jsonl(a.regrade / p / "regrade.jsonl")} for p in PASSES}
    env = json.loads((a.regrade / "environment.json").read_text(encoding="utf-8"))

    # gated set: the six-arm union, exactly as experiments/EXP-034/posthoc_gated.py
    six = {k: {(r.get("instance_id") or r.get("task_id")): r for r in load_jsonl(Path(d) / "task_results.jsonl")}
           for k, d in M.ARMS.items()}
    ids48 = sorted(set.intersection(*(set(v) for v in six.values())))
    gated = {t for k in six for t in ids48 if GATE_RE.search(six[k][t].get("test_tail") or "")}
    own_blocked = {arm: {t for t in ids48 if GATE_RE.search(asrun[arm][t].get("test_tail") or "")} for arm in ARMS}
    nongated = [t for t in ids48 if t not in gated]

    for p in PASSES:
        bad = [t for t, r in rg[p].items() if len(r["tail"]) < TAIL_CAP and r["tail"] and not r["tail"].startswith("STDOUT:")]
        assert not bad, (p, bad)

    out = {"environment": env, "n_ids": len(ids48), "n_gated": len(gated), "n_nongated": len(nongated),
           "gated_ids": sorted(gated), "own_blocked": {k: len(v) for k, v in own_blocked.items()}}

    # ---------------------------------------------------------------- row 0 audit
    audit = {"rows_per_pass": {p: len(rg[p]) for p in PASSES},
             "ids_equal_cohort": {p: sorted(rg[p]) == ids48 for p in PASSES},
             "exit_codes": {p: dict(sorted(Counter(str(r["exit"]) for r in rg[p].values()).items())) for p in PASSES},
             "exit_minus9_ids": {p: sorted(t for t, r in rg[p].items() if r["exit"] == -9) for p in PASSES},
             "tails_at_cap": {p: sum(len(r["tail"]) >= TAIL_CAP for r in rg[p].values()) for p in PASSES},
             "shims_dropped": {p: {"gated": sum(bool(rg[p][t]["shims_dropped"]) for t in gated),
                                   "nongated": sum(bool(rg[p][t]["shims_dropped"]) for t in nongated)} for p in PASSES},
             "gated_still_missing_package": {p: sorted(t for t in gated if GATE_RE.search(rg[p][t]["tail"])) for p in PASSES}}
    out["audit"] = audit

    # ---------------------------------------------------------------- resolves and flips
    res = {}
    for arm in ARMS:
        ar = {t: bool(asrun[arm][t]["resolved"]) for t in ids48}
        rr = {t: bool(rg[arm][t]["resolved"]) for t in ids48}
        res[arm] = rr
        sub = lambda d, s: sum(d[t] for t in s)
        ft = sorted(t for t in ids48 if rr[t] and not ar[t])
        tf = sorted(t for t in ids48 if ar[t] and not rr[t])
        out[arm] = {
            "as_run": {"all48": sub(ar, ids48), "gated": sub(ar, gated), "nongated": sub(ar, nongated), "own_blocked": sub(ar, own_blocked[arm])},
            "regraded": {"all48": sub(rr, ids48), "gated": sub(rr, gated), "nongated": sub(rr, nongated), "own_blocked": sub(rr, own_blocked[arm])},
            "G_gated_F_to_T": sum(t in gated for t in ft),
            "F_to_T_gated_ids": [t for t in ft if t in gated], "F_to_T_nongated_ids": [t for t in ft if t not in gated],
            "T_to_F_ids": [[t, rg[arm][t]["exit"], t in gated] for t in tf],
            "F_to_T_own_blocked": sum(t in own_blocked[arm] for t in ft),
            "gated_regraded_resolves_also_gold_resolved": sum(1 for t in gated if rr[t] and rg["GOLD"][t]["resolved"]),
        }
    gold = {t: bool(rg["GOLD"][t]["resolved"]) for t in ids48}
    base = {t: bool(rg["BASE"][t]["resolved"]) for t in ids48}
    out["GOLD"] = {"all48": sum(gold.values()), "gated": sum(gold[t] for t in gated), "nongated": sum(gold[t] for t in nongated),
                   "unresolved_ids": [[t, rg["GOLD"][t]["exit"], t in gated] for t in ids48 if not gold[t]]}
    out["BASE"] = {"all48": sum(base.values()), "gated": sum(base[t] for t in gated),
                   "resolved_ids": [t for t in ids48 if base[t]]}
    union = sum(res["R"][t] or res["RH"][t] for t in ids48)
    best = max(out["R"]["regraded"]["all48"], out["RH"]["regraded"]["all48"])
    ug = sum(res["R"][t] or res["RH"][t] for t in gated)
    bg = max(out["R"]["regraded"]["gated"], out["RH"]["regraded"]["gated"])
    out["best_of_n_R_RH_regraded"] = {"all48": {"union": union, "best": best, "union_minus_best": union - best},
                                     "gated": {"union": ug, "best": bg, "union_minus_best": ug - bg},
                                     "exp034_all48_as_scored": EXP034_ALL48_V}

    # Post hoc: tasks on which GOLD and BASE end the same way, with the same exit code and the same count line once
    # the duration is removed. On those tasks the patch under test does not change the grade on this grader.
    def count_line(tail):
        pt = parse(tail)
        if not pt["count_line"]:
            return []
        line = [l for l in pt["text"].splitlines() if G.COUNT_RE.search(l)][-1]
        return [re.sub(r"\bin [\d.]+s\b", "in Xs", line)]
    insens = sorted(t for t in ids48 if rg["GOLD"][t]["exit"] == rg["BASE"][t]["exit"]
                    and count_line(rg["GOLD"][t]["tail"]) == count_line(rg["BASE"][t]["tail"]))
    out["posthoc_gold_equals_base_failing_ids_equal"] = sorted(
        t for t in insens if failing_set(parse(rg["GOLD"][t]["tail"])) == failing_set(parse(rg["BASE"][t]["tail"])))
    out["posthoc_gold_equals_base_ids"] = insens
    for arm in ARMS:
        out[arm]["posthoc_regraded_excluding_gold_equals_base"] = sum(res[arm][t] for t in ids48 if t not in insens)
        out[arm]["posthoc_as_run_excluding_gold_equals_base"] = sum(bool(asrun[arm][t]["resolved"]) for t in ids48 if t not in insens)

    # ---------------------------------------------------------------- recomputed EXP-035 table
    snaps = {}
    base_pt = {t: parse(rg["BASE"][t]["tail"]) for t in ids48}
    gold_pt = {t: parse(rg["GOLD"][t]["tail"]) for t in ids48}
    rows_out = []
    for arm in ARMS:
        grp = []
        for t in ids48:
            patch = asrun[arm][t].get("patch") or ""
            if res[arm][t] or not (M.patch_files(patch) & M.patch_files(tasks[t].get("patch") or "")):
                continue
            row = rg[arm][t]
            files = G.tp_files(tasks[t].get("test_patch") or "")
            if t not in snaps:
                snaps[t] = G.Snap(a.snapshots / f"{t}.tgz")
            pt = parse(row["tail"])
            bpt = base_pt[t]
            base_known = bool(bpt["complete"]) and not bpt["interrupted"] and rg["BASE"][t]["exit"] in (0, 1)
            base_fail = failing_set(bpt) if base_known else set()
            gpass = (lambda k: gold[t] or (gold_pt[t]["complete"] and k not in failing_set(gold_pt[t])))
            counters, cache, tests = Counter(), {}, []
            for tid in pt["ids"]:
                cat, _cd, _st = G.classify_test(tid, files, snaps[t], cache, counters)
                k = tid_key(tid)
                status = None
                if cat in ("a", "b"):
                    status = "unknown" if not base_known else ("base_fail" if k in base_fail else "base_pass")
                tests.append({"k": k, "cat": cat, "base": status, "gold_pass": gpass(k) if status == "base_fail" else None})
            vis = [x for x in tests if x["cat"] in ("a", "b") and x["base"] == "base_pass"]
            hid_ok = all(x["cat"].startswith("c_") or (x["cat"] in ("a", "b") and x["base"] == "base_fail") for x in tests)
            if row["exit"] == 2:
                cat_task = "C"
            elif vis:
                cat_task = "V"
            elif pt["ids"] and pt["complete"] and hid_ok:
                cat_task = "H"
            else:
                cat_task = "U"
            # S1: unknown-base (b) tests count as visible
            s1 = "V" if cat_task in ("U", "H") and any(x["cat"] in ("a", "b") and x["base"] == "unknown" for x in tests) else cat_task
            # S2: base-failing (b) tests that GOLD passes count as visible
            s2 = "V" if cat_task in ("U", "H") and any(x["base"] == "base_fail" and x["gold_pass"] for x in tests) else cat_task
            # S3: EXP-035's corrected rule on re-graded tails, C folded into U, no base exclusion
            if not pt["ids"]:
                s3 = "U"
            elif any(x["cat"] in ("a", "b") for x in tests):
                s3 = "V"
            elif pt["complete"] and all(x["cat"].startswith("c_") for x in tests):
                s3 = "H"
            else:
                s3 = "U"
            cause = None
            if cat_task == "U":
                if any(x["base"] == "unknown" for x in tests):
                    cause = "b_base_unknown"
                elif pt["ids"]:
                    cause = "partial_or_unlocated"
                else:
                    cause = G.unreadable_cause({"test_exit_code": row["exit"]}, pt, snaps[t], M.patch_files(patch),
                                               [l for fd in files.values() for l in fd["plus"]]) + (f"_exit{row['exit']}" if row["exit"] not in (0, 1) else "")
            r = {"arm": arm, "task_id": t, "gated": t in gated, "exit": row["exit"], "cat": cat_task, "s1": s1, "s2": s2,
                 "s3": s3, "cause": cause, "n_tests": len(tests),
                 "n_b_base_fail": sum(x["base"] == "base_fail" for x in tests),
                 "n_b_base_unknown": sum(x["base"] == "unknown" for x in tests),
                 "n_b_base_pass": sum(x["base"] == "base_pass" for x in tests)}
            grp.append(r)
        rows_out += grp
        n = len(grp)
        c = Counter(r["cat"] for r in grp)
        C, V, H, U = c["C"], c["V"], c["H"], c["U"]
        if n < 12 or len(rg["BASE"]) < 48:
            row_t = "T0"
        elif C + U >= n / 2:
            row_t = "T1"
        elif V >= n / 3:
            row_t = "T2"
        elif V + H and H >= (2 / 3) * (V + H):
            row_t = "T3"
        else:
            row_t = "T4"

        def which(cnt):
            v, h, cu = cnt.get("V", 0), cnt.get("H", 0), cnt.get("C", 0) + cnt.get("U", 0)
            if n < 12:
                return "T0"
            if cu >= n / 2:
                return "T1"
            if v >= n / 3:
                return "T2"
            if v + h and h >= (2 / 3) * (v + h):
                return "T3"
            return "T4"
        sens = {}
        for s in ("s1", "s2", "s3"):
            cnt = Counter(r[s] for r in grp)
            if s == "s3":
                cnt = Counter({"V": cnt["V"], "H": cnt["H"], "U": cnt["U"]})
            sens[s] = {"counts": dict(sorted(cnt.items())), "row": which(cnt)}
        out[arm]["table"] = {
            "n_prime": n, "C": C, "V": V, "H": H, "U": U, "C_plus_U": C + U,
            "wilson95": {k: G.wilson(v, n) for k, v in (("C", C), ("V", V), ("H", H), ("U", U), ("C_plus_U", C + U))},
            "row": row_t, "sensitivity": sens,
            "gated_in_group": sum(r["gated"] for r in grp),
            "by_gated": {g: dict(sorted(Counter(r["cat"] for r in grp if r["gated"] == g).items())) for g in (True, False)},
            "u_causes": dict(sorted(Counter(r["cause"] for r in grp if r["cause"]).items())),
            "exit_codes": dict(sorted(Counter(str(r["exit"]) for r in grp).items())),
            "b_tests_base_fail": sum(r["n_b_base_fail"] for r in grp),
            "b_tests_base_unknown": sum(r["n_b_base_unknown"] for r in grp),
            "b_tests_base_pass": sum(r["n_b_base_pass"] for r in grp),
            "tasks_with_base_unknown_b": sum(r["n_b_base_unknown"] > 0 for r in grp),
        }
        # Post hoc, added 2026-11-05 after the critic's light review (experiments/EXP-036/critic.md Q4): the same
        # table without the tasks on which GOLD and BASE grade alike (`insens`), since none of them is a judged
        # wrong fix; V's bounds (lower = V; upper = V + C + U, every unreadable task counted as visible); and,
        # per C task, BASE's exit and the error class names in both tails, to tell the patch's own collection
        # error from one BASE already has.
        gx = [r for r in grp if r["task_id"] not in insens]
        cx = Counter(r["cat"] for r in gx)
        nx = len(gx)

        def err_classes(tail):
            return sorted(set(re.findall(r"^E\s+(\w+(?:Error|Exception))\b", tail or "", re.M)))

        def err_files(tail):
            # files whose collection failed: the short-summary lines "ERROR <path>[ - <message>]" (no "::",
            # which would be a per-test setup error, not a collection error)
            return {m for m in re.findall(r"^ERROR (\S+?)(?:\s+-\s.*)?$", tail or "", re.M) if "::" not in m}
        c_tasks = []
        for r in grp:
            if r["cat"] != "C":
                continue
            t = r["task_id"]
            pe, be = err_classes(rg[arm][t]["tail"]), err_classes(rg["BASE"][t]["tail"])
            graded = set(G.tp_files(tasks[t].get("test_patch") or ""))
            pf, bf = err_files(rg[arm][t]["tail"]), err_files(rg["BASE"][t]["tail"])
            new_fail = sorted((pf - bf) & graded) if graded else sorted(pf - bf)
            # EXP-036 erratum 2026-11-05 (critic re-review, experiments/EXP-036/critic.md): the family rule that
            # stood here (ModuleNotFoundError folded into ImportError, compared by class name) cleared
            # fastapi_14609 in both arms and is withdrawn, as is reading the raw class-name rule as a count. The
            # file-set rule replaces it: the patch's own collection error iff BASE does not exit 2, or a graded
            # file that collects under BASE fails to collect under the patch. It would miss a patch that changes
            # the error on an identical file set; that case does not occur in R or RH. The raw class-name rule
            # is kept as a field only because the first review cited it.
            c_tasks.append({"task_id": t, "gated": r["gated"], "base_exit": rg["BASE"][t]["exit"],
                            "patch_error_classes": pe, "base_error_classes": be,
                            "n_files_failing_collection_patch": len(pf), "n_files_failing_collection_base": len(bf),
                            "n_newly_failing_graded_files": len(new_fail),
                            "patch_tail_under_cap": len(rg[arm][t]["tail"] or "") < TAIL_CAP,
                            "base_tail_under_cap": len(rg["BASE"][t]["tail"] or "") < TAIL_CAP,
                            "own_error_raw": rg["BASE"][t]["exit"] != 2 or pe != be,
                            "own_error": rg["BASE"][t]["exit"] != 2 or bool(new_fail)})
        out[arm]["table"]["posthoc_excluding_gold_equals_base"] = {
            "excluded_in_group": sorted(r["task_id"] for r in grp if r["task_id"] in insens),
            "n_prime": nx, "C": cx["C"], "V": cx["V"], "H": cx["H"], "U": cx["U"],
            "row": ("T0" if nx < 12 else "T1" if cx["C"] + cx["U"] >= nx / 2 else "T2" if cx["V"] >= nx / 3
                    else "T3" if cx["V"] + cx["H"] and cx["H"] >= (2 / 3) * (cx["V"] + cx["H"]) else "T4"),
            "V_lower": cx["V"], "V_upper": cx["V"] + cx["C"] + cx["U"],
        }
        out[arm]["table"]["posthoc_c_tasks"] = c_tasks
        out[arm]["table"]["posthoc_c_own_collection_error"] = sum(x["own_error"] for x in c_tasks)
        out[arm]["table"]["posthoc_c_own_collection_error_rule"] = "file-set (critic re-review 2026-11-05)"
        out[arm]["table"]["posthoc_c_own_collection_error_ids"] = sorted(x["task_id"] for x in c_tasks if x["own_error"])
        out[arm]["table"]["posthoc_c_own_collection_error_raw_class_rule"] = sum(x["own_error_raw"] for x in c_tasks)
    out["base_status_known_tasks"] = sum(1 for t in ids48 if base_pt[t]["complete"] and not base_pt[t]["interrupted"] and rg["BASE"][t]["exit"] in (0, 1))

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    with open(a.summary, "w", encoding="utf-8", newline="\n") as fh:
        for t in ids48:
            fh.write(json.dumps({"task_id": t, "gated": t in gated,
                                 "R_resolved_as_run": bool(asrun["R"][t]["resolved"]), "R_resolved_regraded": res["R"][t],
                                 "RH_resolved_as_run": bool(asrun["RH"][t]["resolved"]), "RH_resolved_regraded": res["RH"][t]}) + "\n")
    a.rows.parent.mkdir(parents=True, exist_ok=True)
    with open(a.rows, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows_out:
            fh.write(json.dumps(r) + "\n")
    brief = {k: out[k] for k in ("n_gated", "GOLD", "BASE", "best_of_n_R_RH_regraded", "posthoc_gold_equals_base_ids")}
    for arm in ARMS:
        brief[arm] = {k: v for k, v in out[arm].items()}
    print(json.dumps(brief, indent=1))
    print(json.dumps(audit, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
