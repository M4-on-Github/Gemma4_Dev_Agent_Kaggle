"""EXP-034: best-of-N ceiling over the six dev-48 arms on disk (Q1) and the agent's visible test signal (Q2).

Definitions are the ones pre-registered in experiments/EXP-034-bestofn-ceiling-and-test-signal.md section 2.
Reads runs/ (gitignored) and data/raw/tasks.jsonl; writes counts only to --out and ids-and-booleans to --summary.
Run as:  python -I -X utf8 experiments/EXP-034/mine.py --tasks data/raw/tasks.jsonl \
             --out experiments/EXP-034/aggregates.json --summary experiments/EXP-034/summary.jsonl \
             [--handcheck runs/EXP-034/handcheck]
"""
from __future__ import annotations

import argparse
import itertools
import json
import random
import re
import statistics
from collections import Counter
from pathlib import Path

ARMS = {
    "E0": "runs/E0-dev48-baseline/runs/E0-dev48-baseline",
    "X003": "runs/exp003_public_budget_dev48/runs/EXP-003-public-budget-dev48",
    "A25": "runs/exp025_armA/runs/EXP-025-editfix-dev48-armA-baseline",
    "B25": "runs/exp025_armB/runs/EXP-025-editfix-dev48-armB-editfix",
    "R": "runs/EXP-028-armR",
    "RH": "runs/EXP-028-armRH",
}
SUMMARIES = "runs/EXP-034/{arm}/summary.jsonl"
X003_REGRADE = "runs_download/exp004_regrade_v2/runs/EXP-004-regrade-shim/EXP-003/regrade.jsonl"
FAMILIES = {"all": list(ARMS), "V": ["R", "RH"], "O": ["E0", "X003", "A25", "B25"]}
Q2_ARMS = ["R", "RH"]

PLUS_RE = re.compile(r"^\+\+\+ b/(\S+)", re.M)
MINUS_RE = re.compile(r"^--- a/(\S+)", re.M)
DIFF_GIT_RE = re.compile(r"^diff --git a/(\S+) b/(\S+)", re.M)

SUITE_RE = re.compile(r"pytest|py\.test|unittest")
SCRIPT_RE = re.compile(r"(?:^|[\s;&|(])python3?(?:\.\d+)?\s+(?:-[uBOWEsI]+\s+)*['\"]?([^\s'\"<>|;&]+\.py)\b")
PYC_RE = re.compile(r"(?:^|[\s;&|(])python3?(?:\.\d+)?\s+-c\b")
PYSTDIN_RE = re.compile(r"(?:^|[\s;&|(])python3?(?:\.\d+)?\s+-?\s*<<")
CREATE_RE = re.compile(r">\s*['\"]?([^\s'\"<>|;&]+\.py)\b")
TEE_RE = re.compile(r"\btee\s+(?:-a\s+)?['\"]?([^\s'\"<>|;&]+\.py)\b")

ERR_RE = re.compile(
    r"can't open file|ERROR collecting|no tests ran|collected 0 items|file or directory not found|^usage:|"
    r"^(?:E\s+)?(?:SyntaxError|ModuleNotFoundError|ImportError)\b|ImportError while importing",
    re.M,
)
PYTEST_FAIL_RE = re.compile(r"^=+ .*\b\d+ (?:failed|errors?)\b.*=+\s*$|^FAILED |^ERROR ", re.M)
PYTEST_PASS_RE = re.compile(r"\b\d+ passed\b")
TEXT_FAIL_RE = re.compile(r"\bFAIL\b|\bFAILED\b|\bAssertionError\b|\bTraceback\b|\bError:|\bBUG\b|not fixed|mismatch")


def load_jsonl(path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def norm_path(p: str) -> str:
    p = str(p).strip().strip("'\"").replace("\\", "/")
    if "/workspace/" in p:
        p = p.split("/workspace/", 1)[1]
    while p.startswith("./"):
        p = p[2:]
    return p.lstrip("/")


def patch_files(patch: str) -> set[str]:
    out = set()
    for _a, b in DIFF_GIT_RE.findall(patch or ""):
        out.add(norm_path(b))
    for p in PLUS_RE.findall(patch or "") + MINUS_RE.findall(patch or ""):
        out.add(norm_path(p))
    return out


def parse_hunks(patch: str):
    """[(file, [body lines with sign])] per hunk; headers excluded."""
    lines = (patch or "").splitlines()
    hunks, cur_file, cur = [], None, None
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("diff --git "):
            cur = None
        elif ln.startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ "):
            new = lines[i + 1][4:].strip()
            old = ln[4:].strip()
            cur_file = norm_path(new[2:] if new.startswith("b/") else (old[2:] if old.startswith("a/") else new))
            cur = None
            i += 2
            continue
        elif ln.startswith("@@"):
            cur = [cur_file, []]
            hunks.append(cur)
        elif cur is not None and ln[:1] in "+-":
            cur[1].append(ln)
        i += 1
    return hunks


def lines_changed(patch: str) -> int:
    return sum(len(h[1]) for h in parse_hunks(patch))


def normalised(patch: str):
    out = []
    for f, body in parse_hunks(patch):
        kept = []
        for ln in body:
            sign, txt = ln[0], ln[1:].strip()
            if not txt or txt.startswith("#"):
                continue
            kept.append(sign + re.sub(r"\s+", "", txt))
        if kept:
            out.append((f, tuple(kept)))
    return tuple(sorted(out))


def args_of(call) -> dict:
    a = call.get("arguments")
    if isinstance(a, str):
        try:
            a = json.loads(a)
        except Exception:
            a = {"command": a}
    return a if isinstance(a, dict) else {}


def calls_of(trace_path: Path):
    t = json.load(open(trace_path, encoding="utf-8"))
    out = []
    for s in t.get("steps", []):
        obs = (s.get("observation") or {}).get("content")
        tcs = s.get("tool_calls") or []
        for c in tcs:
            out.append((c.get("function_name"), args_of(c), obs if len(tcs) == 1 else _obs_for(s, c)))
    return out


def _obs_for(step, call):
    obs = (step.get("observation") or {})
    res = obs.get("results")
    if isinstance(res, list):
        for r in res:
            if r.get("source_call_id") == call.get("tool_call_id"):
                return r.get("content")
    return obs.get("content")


def obs_fields(obs):
    if isinstance(obs, list):
        obs = " ".join(str(x.get("text", x)) if isinstance(x, dict) else str(x) for x in obs)
    d = None
    if isinstance(obs, str):
        try:
            d = json.loads(obs)
        except Exception:
            d = None
    elif isinstance(obs, dict):
        d = obs
    if not isinstance(d, dict):
        return None, "", str(obs or "")
    det = d.get("details") if isinstance(d.get("details"), dict) else {}
    ec = d.get("exit_code", det.get("exit_code"))
    status = " ".join(str(d.get(k, "")) for k in ("status", "error_type"))
    text = "\n".join(str(x) for x in (d.get("stdout"), d.get("stderr"), d.get("error_message"),
                                      det.get("stdout"), det.get("stderr")) if x)
    return ec, status, text


def classify_result(kind: str, obs) -> str:
    ec, status, text = obs_fields(obs)
    if "imeout" in status or "timed out" in text.lower():
        return "error"
    if ERR_RE.search(text):
        return "error"
    if kind == "suite":
        if PYTEST_FAIL_RE.search(text):
            return "fail"
        if PYTEST_PASS_RE.search(text):
            return "pass"
        if ec not in (None, 0, "0"):
            return "fail"
        if ec is None and "error" in status:
            return "fail"
        return "pass"
    if ec not in (None, 0, "0") or (ec is None and "error" in status):
        return "fail"
    if TEXT_FAIL_RE.search(text):
        return "fail_text"
    return "pass"


def path_hit(p: str, files: set[str]) -> bool:
    p = norm_path(p)
    return any(p == f or p.endswith("/" + f) for f in files)


def is_edit(name, a, files) -> bool:
    if not files:
        return False
    if name in ("edit_file", "write_file"):
        return path_hit(a.get("filepath") or a.get("path") or "", files)
    if name == "run_command":
        cmd = str(a.get("command") or "")
        for f in files:
            if f in cmd:
                if re.search(r"sed\s+(-\w*\s+)*-i|perl\s+-\w*i|\.write\(", cmd):
                    return True
                if re.search(r">>?\s*['\"]?(?:\./|/workspace/)?" + re.escape(f), cmd):
                    return True
    return False


def test_kind(name, a):
    if name != "run_command":
        return None, None
    cmd = str(a.get("command") or "")
    if SUITE_RE.search(cmd):
        return "suite", None
    m = SCRIPT_RE.search(cmd)
    if m:
        return "script", norm_path(m.group(1))
    return None, None


def created_scripts(name, a, files):
    out = []
    if name == "write_file":
        p = norm_path(a.get("filepath") or a.get("path") or "")
        if p.endswith(".py") and not path_hit(p, files):
            out.append(p)
    elif name == "run_command":
        cmd = str(a.get("command") or "")
        if "<<" in cmd or re.search(r"\b(cat|echo|printf|tee)\b", cmd):
            for p in CREATE_RE.findall(cmd) + TEE_RE.findall(cmd):
                p = norm_path(p)
                if not path_hit(p, files):
                    out.append(p)
    return out


def base(p):
    return p.rsplit("/", 1)[-1]


def q2_task(trace_path: Path, files: set[str]):
    calls = calls_of(trace_path)
    edits = [i for i, (n, a, _o) in enumerate(calls) if is_edit(n, a, files)]
    tests, n_pyc, n_pystdin = [], 0, 0
    created = {}
    for i, (n, a, o) in enumerate(calls):
        for p in created_scripts(n, a, files):
            created.setdefault(base(p), i)
        k, sp = test_kind(n, a)
        if k:
            tests.append((i, k, sp, classify_result(k, o), o, str(a.get("command") or "")))
        elif n == "run_command":
            cmd = str(a.get("command") or "")
            n_pyc += bool(PYC_RE.search(cmd))
            n_pystdin += bool(PYSTDIN_RE.search(cmd))
    last_call = calls[-1][0] if calls else None
    first_edit = edits[0] if edits else None
    last_edit = edits[-1] if edits else None
    after = [t for t in tests if last_edit is not None and t[0] > last_edit]
    if last_edit is None:
        last_vis = "no_edit"
    elif after:
        last_vis = after[-1][3]
    else:
        last_vis = "none"
    # reproduction scripts: created, not in the patch, later run as a script
    repro_runs = [t for t in tests if t[1] == "script" and base(t[2]) in created and t[0] >= created[base(t[2])]]
    repro = None
    if repro_runs:
        before = [t for t in repro_runs if first_edit is None or t[0] < first_edit]
        if before:
            repro = "before_fail" if any(t[3] in ("fail", "fail_text") for t in before) else "before_nonfail"
        else:
            repro = "after_only"
    return {
        "last_vis": last_vis, "any_test": bool(tests), "tested_after": bool(after),
        "repro": repro, "n_pyc": n_pyc, "n_pystdin": n_pystdin, "last_call": last_call,
        "last_test": after[-1] if after else None,
    }


def ending(srow: dict, last_call) -> str:
    if srow.get("calls_cap_hit"):
        return "calls_cap"
    if srow.get("time_cap_hit") or srow.get("timeout_hit"):
        return "time_cap_or_timeout"
    if last_call == "submit_patch":
        return "submit"
    return "other"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", type=Path, default=Path("data/raw/tasks.jsonl"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    ap.add_argument("--handcheck", type=Path, default=None)
    a = ap.parse_args()

    gold = {t["instance_id"]: patch_files(t.get("patch") or "") for t in load_jsonl(a.tasks)}
    res, pat, summ, trc = {}, {}, {}, {}
    for arm, d in ARMS.items():
        rows = {(r.get("instance_id") or r.get("task_id")): r for r in load_jsonl(Path(d) / "task_results.jsonl")}
        res[arm] = {k: bool(v.get("resolved")) for k, v in rows.items()}
        pat[arm] = {k: (v.get("patch") or "") for k, v in rows.items()}
        summ[arm] = {r["task_id"]: r for r in load_jsonl(SUMMARIES.format(arm=arm))}
        trc[arm] = Path(d) / "traces"
    x003_scored = dict(res["X003"])
    res["X003"] = {r["instance_id"]: bool(r.get("resolved")) for r in load_jsonl(X003_REGRADE)}
    ids = sorted(set.intersection(*(set(res[k]) for k in ARMS), *(set(summ[k]) for k in ARMS)))
    cohort = set(Path("experiments/cohorts/dev-48.txt").read_text().split())
    agg = {"arms": list(ARMS), "n_intersection": len(ids), "n_intersection_in_dev48": len(set(ids) & cohort)}

    def fam_stats(arms, resd):
        per = {k: sum(resd[k][t] for t in ids) for k in arms}
        union = sum(any(resd[k][t] for k in arms) for t in ids)
        curve = {}
        for kk in range(1, len(arms) + 1):
            sizes = [sum(any(resd[k][t] for k in sub) for t in ids) for sub in itertools.combinations(arms, kk)]
            curve[kk] = round(statistics.mean(sizes), 3)
        best = max(per.values())
        return {"per_arm": per, "union": union, "best_single": best, "union_minus_best": union - best, "curve": curve}

    agg["q1a"] = {f: fam_stats(arms, res) for f, arms in FAMILIES.items()}
    res_sc = dict(res)
    res_sc["X003"] = x003_scored
    agg["q1a_sensitivity_x003_as_scored"] = {f: fam_stats(arms, res_sc) for f, arms in FAMILIES.items() if "X003" in arms}
    cnt = [sum(res[k][t] for k in ARMS) for t in ids]
    agg["q1b"] = {"all_arms": sum(c == len(ARMS) for c in cnt), "some_not_all": sum(0 < c < len(ARMS) for c in cnt),
                  "none": sum(c == 0 for c in cnt), "histogram_n_arms_resolving": dict(sorted(Counter(cnt).items()))}

    # Q1c proxies over (task, arm) with non-empty patch
    prox = {p: {} for p in ("diff_match", "majority_files", "smaller", "submit_before_cap")}
    nonempty = {}
    turn_flag = 0
    for t in ids:
        ne = [k for k in ARMS if pat[k][t].strip()]
        nonempty[t] = ne
        norms = {k: normalised(pat[k][t]) for k in ne}
        fsets = {k: frozenset(patch_files(pat[k][t])) for k in ne}
        fcount = Counter(fsets.values())
        lc = {k: lines_changed(pat[k][t]) for k in ne}
        med = statistics.median(lc.values()) if lc else None
        for k in ARMS:
            if k not in ne:
                continue
            prox["diff_match"][(t, k)] = any(norms[k] == norms[j] and norms[k] for j in ne if j != k)
            prox["majority_files"][(t, k)] = fcount[fsets[k]] >= 4
            prox["smaller"][(t, k)] = lc[k] < med
            calls = calls_of(trc[k] / f"trace_{t}.json")
            last = calls[-1][0] if calls else None
            s = summ[k][t]
            ok = last == "submit_patch" and not (s.get("calls_cap_hit") or s.get("time_cap_hit") or s.get("timeout_hit"))
            prox["submit_before_cap"][(t, k)] = ok
            if ok and (s.get("n_turns") or 0) >= 79:
                turn_flag += 1
    random_arm = sum(statistics.mean(res[k][t] for k in ARMS) for t in ids)
    random_ne = sum(statistics.mean(res[k][t] for k in nonempty[t]) if nonempty[t] else 0 for t in ids)
    q1c = {"n_pairs_nonempty": sum(len(v) for v in nonempty.values()), "random_arm": round(random_arm, 3),
           "random_nonempty": round(random_ne, 3), "union": agg["q1a"]["all"]["union"],
           "submit_before_cap_with_n_turns_ge_79": turn_flag, "proxies": {}}
    for p, m in prox.items():
        tab = Counter((bool(v), res[k][t]) for (t, k), v in m.items())
        score = 0.0
        for t in ids:
            cand = [k for k in nonempty[t] if m.get((t, k))] or nonempty[t]
            score += statistics.mean(res[k][t] for k in cand) if cand else 0
        q1c["proxies"][p] = {
            "proxy_true_resolved": tab[(True, True)], "proxy_true_unresolved": tab[(True, False)],
            "proxy_false_resolved": tab[(False, True)], "proxy_false_unresolved": tab[(False, False)],
            "selector_score": round(score, 3), "gain_over_random_arm": round(score - random_arm, 3),
            "gain_over_random_nonempty": round(score - random_ne, 3),
        }
    agg["q1c"] = q1c

    # Q2
    q2, per_task_q2, hand_pool = {}, {}, []
    for arm in Q2_ARMS:
        rows = {}
        for t in ids:
            files = patch_files(pat[arm][t])
            r = q2_task(trc[arm] / f"trace_{t}.json", files)
            r["resolved"] = res[arm][t]
            r["rfwf"] = (not res[arm][t]) and bool(files & gold.get(t, set()))
            r["ending"] = ending(summ[arm][t], r["last_call"])
            rows[t] = r
            if arm == "R" and r["last_test"] is not None:
                hand_pool.append((t, r["last_test"]))
        per_task_q2[arm] = rows

        def table(sel):
            sub = [r for r in rows.values() if sel(r)]
            lv = Counter(r["last_vis"] for r in sub)
            return {
                "n": len(sub),
                "last_visible": dict(sorted(lv.items())),
                "last_pass": lv["pass"], "last_fail_incl_text": lv["fail"] + lv["fail_text"],
                "last_fail_by_ending": dict(sorted(Counter(r["ending"] for r in sub if r["last_vis"] in ("fail", "fail_text")).items())),
                "last_pass_by_ending": dict(sorted(Counter(r["ending"] for r in sub if r["last_vis"] == "pass").items())),
                "no_test_anywhere": sum(not r["any_test"] for r in sub),
                "repro": dict(sorted(Counter(r["repro"] or "no_repro_script" for r in sub).items())),
                "endings": dict(sorted(Counter(r["ending"] for r in sub).items())),
            }

        q2[arm] = {
            "all": table(lambda r: True), "resolved": table(lambda r: r["resolved"]),
            "unresolved": table(lambda r: not r["resolved"]), "rfwf": table(lambda r: r["rfwf"]),
            "python_c_calls": sum(r["n_pyc"] for r in rows.values()),
            "python_stdin_heredoc_calls": sum(r["n_pystdin"] for r in rows.values()),
        }
    agg["q2"] = q2

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(agg, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    with open(a.summary, "w", encoding="utf-8", newline="\n") as fh:
        for t in ids:
            row = {"task_id": t}
            for k in ARMS:
                ne = k in nonempty[t]
                row[f"resolved_{k}"] = res[k][t]
                row[f"patch_nonempty_{k}"] = ne
                for p in prox:
                    row[f"{p}_{k}"] = bool(prox[p].get((t, k))) if ne else False
            for k in Q2_ARMS:
                r = per_task_q2[k][t]
                row[f"tested_after_last_edit_{k}"] = r["tested_after"]
                row[f"last_visible_pass_{k}"] = r["last_vis"] == "pass"
                row[f"last_visible_fail_{k}"] = r["last_vis"] in ("fail", "fail_text")
            fh.write(json.dumps(row) + "\n")

    if a.handcheck:
        # stratified draw: up to 4 pass, 4 fail (incl text), 2 error, random.Random(34)
        rng = random.Random(34)
        strata = {"pass": [], "fail": [], "error": []}
        for t, lt in sorted(hand_pool):
            strata["fail" if lt[3] in ("fail", "fail_text") else lt[3]].append((t, lt))
        pick = []
        for s, n in (("pass", 4), ("fail", 4), ("error", 2)):
            pool = strata[s]
            pick += rng.sample(pool, min(n, len(pool)))
        rng.shuffle(pick)
        a.handcheck.mkdir(parents=True, exist_ok=True)
        with open(a.handcheck / "obs.txt", "w", encoding="utf-8") as fh, open(a.handcheck / "key.txt", "w", encoding="utf-8") as kh:
            for i, (t, lt) in enumerate(pick):
                ec, status, text = obs_fields(lt[4])
                fh.write(f"===== #{i} kind={lt[1]} exit_code={ec} status={status}\nCMD: {lt[5][:400]}\n{text[-2500:]}\n\n")
                kh.write(f"#{i} {t} {lt[3]}\n")
    print(json.dumps({"n": len(ids), "q1a_all": agg["q1a"]["all"], "q1b": agg["q1b"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
