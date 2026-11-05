#!/usr/bin/env python3
"""EXP-038 section 3.3: fault row F, then G, on the CPU re-grade of the E4B's 48 stored patches (passes E4B, GOLD,
BASE; kernel rainm4/gemma4-exp038-regrade v1).

Definitions are EXP-036's (experiments/EXP-036/analyze_regrade.py), applied to one arm:
- the gated set is EXP-036's `gated_ids` (the EXP-034 six-arm union), read from experiments/EXP-036/aggregates.json;
- G = gated tasks the E4B resolves under the re-grade (all gated tasks are unresolved as run, row 0b);
- "the patch's own collection error" uses the file-set rule of the EXP-036 critic re-review: on a task whose
  re-grade exits 2, the error is the patch's own iff BASE does not exit 2, or a graded file that collects under
  BASE fails to collect under the patch. It is applied, as in EXP-036, to the unresolved tasks whose patch touches
  a gold-patch file (EXP-034 `patch_files`), and is also reported over every exit-2 row;
- the paired re-graded 2x2 against Arm R's re-grade (EXP-036, 12 of 48) uses EXP-036's committed summary.jsonl.

Reads runs/ and data/ (gitignored); run from the repo root as `python -I -X utf8 experiments/EXP-038/analyze_regrade.py`.
Writes experiments/EXP-038/regrade/aggregates.json (counts, ids, exit codes, error class names) and
experiments/EXP-038/regrade/summary.jsonl (per task: id and booleans only). No tail text, no patch text (plan.md:52).
"""
from __future__ import annotations

import importlib.util
import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M = _load("exp034_mine", "experiments/EXP-034/mine.py")
G = _load("exp035_grader_tests", "experiments/EXP-035/grader_tests.py")

RG = ROOT / "runs/EXP-038-regrade"
ASRUN = ROOT / "runs/EXP-038-e4b-dev48/task_results.jsonl"
TASKS = ROOT / "data/raw/tasks.jsonl"
DEV48 = ROOT / "experiments/cohorts/dev-48.txt"
A36 = ROOT / "experiments/EXP-036/aggregates.json"
S36 = ROOT / "experiments/EXP-036/summary.jsonl"
OUT_DIR = ROOT / "experiments/EXP-038/regrade"
PASSES = ("E4B", "GOLD", "BASE")
TAIL_CAP = 20000
GATE_RE = re.compile(r"No module named '?(inline_snapshot|dirty_equals)")
GOLD_UNRESOLVED = ["httpx_3672", "requests_7205", "requests_7309", "requests_7315", "requests_7427"]
BASE_RESOLVED = ["requests_6644"]
EXP041_IDS = ["fastapi_15589", "fastapi_9753"]


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def mcnemar(b: int, c: int):
    n = b + c
    return None if n == 0 else round(min(1.0, 2 * sum(math.comb(n, k) for k in range(min(b, c) + 1)) / 2 ** n), 4)


def err_classes(tail):
    return sorted(set(re.findall(r"^E\s+(\w+(?:Error|Exception))\b", tail or "", re.M)))


def err_files(tail):
    return {m for m in re.findall(r"^ERROR (\S+?)(?:\s+-\s.*)?$", tail or "", re.M) if "::" not in m}


def main() -> int:
    ids = sorted(s.strip() for s in DEV48.read_text(encoding="utf-8").splitlines() if s.strip() and not s.startswith("#"))
    rg = {p: {r["instance_id"]: r for r in jl(RG / p / "regrade.jsonl")} for p in PASSES}
    asrun = {r["instance_id"]: r for r in jl(ASRUN)}
    a36 = json.loads(A36.read_text(encoding="utf-8"))
    s36 = {r["task_id"]: r for r in jl(S36)}
    gated = set(a36["gated_ids"])
    const = set(a36["posthoc_gold_equals_base_ids"])
    nongated = [t for t in ids if t not in gated]
    informative = [t for t in ids if t not in gated and t not in const]

    # ---------------------------------------------------------------- fault row F
    rows = {p: len(rg[p]) for p in PASSES}
    ids_ok = {p: sorted(rg[p]) == ids for p in PASSES}
    gold = {t: bool(rg["GOLD"][t]["resolved"]) for t in rg["GOLD"]}
    base = {t: bool(rg["BASE"][t]["resolved"]) for t in rg["BASE"]}
    gold_unres = sorted(t for t, v in gold.items() if not v)
    base_res = sorted(t for t, v in base.items() if v)
    F = {"rows_per_pass": rows, "ids_equal_cohort": ids_ok,
         "GOLD_all48": sum(gold.values()), "GOLD_gated": sum(gold.get(t, False) for t in gated),
         "GOLD_unresolved_ids": gold_unres, "GOLD_unresolved_expected": GOLD_UNRESOLVED,
         "BASE_all48": sum(base.values()), "BASE_resolved_ids": base_res, "BASE_resolved_expected": BASE_RESOLVED}
    F["fires"] = bool(any(n < 48 for n in rows.values()) or not all(ids_ok.values())
                      or F["GOLD_all48"] != 43 or F["GOLD_gated"] != 15 or gold_unres != GOLD_UNRESOLVED
                      or F["BASE_all48"] != 1 or base_res != BASE_RESOLVED)
    out = {"F": F}
    if F["fires"]:
        print(json.dumps(out, indent=1))
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "aggregates.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
        return 0

    for p in PASSES:  # same tail assertion as EXP-036
        bad = [t for t, r in rg[p].items() if len(r["tail"]) < TAIL_CAP and r["tail"] and not r["tail"].startswith("STDOUT:")]
        assert not bad, (p, bad)

    out["audit"] = {
        "exit_codes": {p: dict(sorted(Counter(str(r["exit"]) for r in rg[p].values()).items())) for p in PASSES},
        "exit_minus9_ids": {p: sorted(t for t, r in rg[p].items() if r["exit"] == -9) for p in PASSES},
        "tails_at_cap": {p: sum(len(r["tail"]) >= TAIL_CAP for r in rg[p].values()) for p in PASSES},
        "shims_dropped": {p: {"gated": sum(bool(rg[p][t]["shims_dropped"]) for t in gated),
                              "nongated": sum(bool(rg[p][t]["shims_dropped"]) for t in nongated)} for p in PASSES},
        "gated_still_missing_package": {p: sorted(t for t in gated if GATE_RE.search(rg[p][t]["tail"])) for p in PASSES},
        "errors": {p: sorted({r.get("error") or "" for r in rg[p].values()} - {""}) for p in PASSES},
    }

    # ---------------------------------------------------------------- G and the re-graded resolves
    ar = {t: bool(asrun[t]["resolved"]) for t in ids}
    rr = {t: bool(rg["E4B"][t]["resolved"]) for t in ids}
    ft = sorted(t for t in ids if rr[t] and not ar[t])
    tf = sorted(t for t in ids if ar[t] and not rr[t])
    sub = lambda d, s: sum(d[t] for t in s)
    out["E4B"] = {
        "as_run": {"all48": sub(ar, ids), "gated": sub(ar, gated), "nongated": sub(ar, nongated), "informative27": sub(ar, informative)},
        "regraded": {"all48": sub(rr, ids), "gated": sub(rr, gated), "nongated": sub(rr, nongated), "informative27": sub(rr, informative)},
        "G_gated_F_to_T": sum(t in gated for t in ft),
        "F_to_T_gated_ids": [t for t in ft if t in gated], "F_to_T_nongated_ids": [t for t in ft if t not in gated],
        "T_to_F_ids": [[t, rg["E4B"][t]["exit"], t in gated] for t in tf],
        "gated_exit_codes": dict(sorted(Counter(str(rg["E4B"][t]["exit"]) for t in gated).items())),
    }
    out["G_reading"] = "G >= 2 of 15" if out["E4B"]["G_gated_F_to_T"] >= 2 else "G <= 1"
    out["reference_EXP036"] = {arm: {"regraded_all48": a36[arm]["regraded"]["all48"], "regraded_gated": a36[arm]["regraded"]["gated"],
                                     "G": a36[arm]["G_gated_F_to_T"], "F_to_T_gated_ids": a36[arm]["F_to_T_gated_ids"]}
                               for arm in ("R", "RH")}

    # paired re-graded 2x2 against R's re-grade (EXP-036)
    rR = {t: bool(s36[t]["R_resolved_regraded"]) for t in ids}

    def pair(sel):
        both = [t for t in sel if rr[t] and rR[t]]
        r_only = [t for t in sel if rR[t] and not rr[t]]
        e_only = [t for t in sel if rr[t] and not rR[t]]
        return {"n": len(sel), "both": len(both), "R_only": len(r_only), "E4B_only": len(e_only),
                "neither": len(sel) - len(both) - len(r_only) - len(e_only), "R_only_ids": r_only, "E4B_only_ids": e_only,
                "mcnemar_exact_two_sided_p": mcnemar(len(r_only), len(e_only))}
    out["paired_regraded_vs_R_regraded"] = {"all48": pair(ids), "gated15": pair(sorted(gated)), "informative27": pair(informative)}

    # ---------------------------------------------------------------- the patch's own collection errors (file-set rule)
    tasks = {t["instance_id"]: t for t in jl(TASKS) if t["instance_id"] in set(ids)}

    def own(t):
        tail, btail = rg["E4B"][t]["tail"], rg["BASE"][t]["tail"]
        graded = set(G.tp_files(tasks[t].get("test_patch") or ""))
        pf, bf = err_files(tail), err_files(btail)
        new_fail = sorted((pf - bf) & graded) if graded else sorted(pf - bf)
        return {"task_id": t, "gated": t in gated, "base_exit": rg["BASE"][t]["exit"],
                "patch_error_classes": err_classes(tail), "base_error_classes": err_classes(btail),
                "n_files_failing_collection_patch": len(pf), "n_files_failing_collection_base": len(bf),
                "n_newly_failing_graded_files": len(new_fail),
                "patch_tail_under_cap": len(tail or "") < TAIL_CAP, "base_tail_under_cap": len(btail or "") < TAIL_CAP,
                "own_error": rg["BASE"][t]["exit"] != 2 or bool(new_fail)}
    grp = [t for t in ids if not rr[t] and (M.patch_files(asrun[t].get("patch") or "") & M.patch_files(tasks[t].get("patch") or ""))]
    c_grp = [own(t) for t in grp if rg["E4B"][t]["exit"] == 2]
    c_all = [own(t) for t in ids if rg["E4B"][t]["exit"] == 2]
    out["own_collection_error"] = {
        "rule": "file-set (EXP-036 critic re-review 2026-11-05)",
        "group_unresolved_patch_touches_gold_file": {"n_prime": len(grp), "gated_in_group": sum(t in gated for t in grp),
                                                      "exit2": len(c_grp), "own_error": sum(x["own_error"] for x in c_grp),
                                                      "own_error_ids": sorted(x["task_id"] for x in c_grp if x["own_error"]),
                                                      "c_tasks": c_grp},
        "all_exit2_rows": {"n": len(c_all), "own_error": sum(x["own_error"] for x in c_all),
                           "own_error_ids": sorted(x["task_id"] for x in c_all if x["own_error"])},
        "reference_EXP036": {arm: {"n_prime": a36[arm]["table"]["n_prime"], "C": a36[arm]["table"]["C"],
                                   "own_error": a36[arm]["table"]["posthoc_c_own_collection_error"],
                                   "own_error_ids": a36[arm]["table"]["posthoc_c_own_collection_error_ids"]} for arm in ("R", "RH")},
    }

    # ---------------------------------------------------------------- EXP-041's two ids (observation, not a reading)
    out["exp041_ids"] = {t: {"gated": t in gated, "as_run_resolved": ar[t], "regraded_resolved": rr[t],
                             "regrade_exit": rg["E4B"][t]["exit"], "shims_dropped": bool(rg["E4B"][t]["shims_dropped"]),
                             "regrade_missing_package": bool(GATE_RE.search(rg["E4B"][t]["tail"])),
                             "as_run_exit": asrun[t].get("test_exit_code"),
                             "as_run_missing_package": bool(GATE_RE.search(asrun[t].get("test_tail") or "")),
                             "R_as_run": bool(s36[t]["R_resolved_as_run"]), "R_regraded": rR[t],
                             "GOLD_regraded": gold[t], "BASE_regraded": base[t]} for t in EXP041_IDS}

    out["seconds"] = json.loads((RG / "summary.json").read_text(encoding="utf-8"))["seconds"]
    log = json.loads((RG / "gemma4-exp038-regrade.log").read_text(encoding="utf-8"))
    out["kernel_log_end_s"] = round(float(log[-1]["time"]), 1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "aggregates.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    with open(OUT_DIR / "summary.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for t in ids:
            fh.write(json.dumps({"task_id": t, "gated": t in gated, "E4B_resolved_as_run": ar[t],
                                 "E4B_resolved_regraded": rr[t], "R_resolved_regraded": rR[t]}) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
