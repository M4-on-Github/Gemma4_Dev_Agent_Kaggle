"""PART A: 31B pre-first-edit call mix and the locate-script ceiling. Counts, shares and seconds only.

Usage: python3 -I locate_31b.py OUT_JSON [PER_DRAW_JSONL]

tools/r015_gates.py imports parse() from here, so R-015's mechanism numbers use these same conventions.

Conventions reused from the session-scratch pool script behind skill-script-sizing.md, so the numbers agree:
- calls are counted over agent steps in trace order (ci = 1, 2, ...);
- a step's model seconds = its elapsed_s minus the previous step's observation elapsed_s (or the task prompt's
  elapsed_s for the first step); tool seconds = observation elapsed_s minus step elapsed_s;
- edit attempt = edit_file/write_file on a relative, non-/tmp, non-test path; landed = tvr.call_ok(obs).
Additions here:
- seconds of a call = model seconds of the step that issued it + tool seconds + model seconds of any tool-less
  agent steps since the previous call (so per-call seconds sum to the observation clock at that call);
- a write_file at repo root whose basename starts repro/reproduce/test_/debug_/scratch counts as SCRATCH, not as
  the first edit (pool31b counts it as an edit; the number of draws where this differs is reported).
"""
import collections
import json
import os
import re
import statistics
import sys

HE = "/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng"
sys.path.insert(0, os.path.join(HE, "tools"))
import trace_vs_reference as tvr  # noqa: E402

RUNS = ["R-008-31b-base-te-d1", "R-008-31b-base-te-d2", "R-011-31b-base-te-d3", "R-011-31b-base-te-d4",
        "R-014-31b-base-te-d5"]
CAP_S = 480.0
CAP_CALLS = 28

SEARCH_PROGS = {"grep", "egrep", "fgrep", "rg", "ag", "find", "ls", "tree", "fd", "locate"}
SEARCH_GIT = {"grep", "log", "ls-files", "show", "blame"}
RUN_PROGS = {"python", "python3", "pytest", "bash", "sh", "uv", "tox", "make", "pip"}
READ_PROGS = {"cat", "head", "tail", "nl", "awk", "less", "more", "wc", "sed"}
SCRATCH_BASE = re.compile(r"^(repro|reproduce|test_|debug|scratch|tmp|check_|verify)")


def strip_cd(cmd):
    return re.sub(r"^\s*(cd\s+\S+\s*(&&|;)\s*)+", "", cmd).strip()


def classify_cmd(cmd):
    c = strip_cd(cmd)
    toks = c.split()
    if not toks:
        return "OTHER", False
    p = os.path.basename(toks[0])
    writes_file = bool(re.search(r"(^|[^2&])>\s*[\w./-]+|<<\s*['\"]?\w+|\btee\s", c))
    pyloc = bool(re.search(r"__file__|getsourcefile|getfile\(|inspect\.getsource|\.__module__", c))
    if p in RUN_PROGS or p.startswith("python"):
        return "RUN", pyloc
    if p in ("cat", "printf", "echo") and writes_file:
        return "SCRATCH", False
    if p == "sed" and re.search(r"\s-i\b", c):
        return "SHEDIT", False
    if p in SEARCH_PROGS:
        return "SEARCH", False
    if p == "git" and len(toks) > 1 and toks[1] in SEARCH_GIT:
        return "SEARCH", False
    if p in READ_PROGS:
        if re.search(r"\|\s*(grep|rg)\b", c):
            return "SEARCH", False
        return "SHREAD", False
    if p == "git":
        return "OTHER", False
    return "OTHER", False


def path_of(args):
    return tvr.norm_path(args.get("filepath") or args.get("path") or args.get("file_path") or "")


def shread_paths(cmd):
    c = strip_cd(cmd)
    return [tvr.norm_path(x) for x in re.findall(r"[\w./-]+\.py\b", c)]


def parse(run, row):
    p = os.path.join(HE, "runs", run, "traces", f"trace_{row['instance_id']}.json")
    t = json.load(open(p))
    calls = []
    prev_obs = None
    pending = 0.0
    ci = 0
    for s in t.get("steps", []):
        ex = s.get("extra") or {}
        el = ex.get("elapsed_s")
        if s.get("source") != "agent":
            if el is not None and prev_obs is None:
                prev_obs = el
            continue
        if el is None:
            continue
        obs_el = ((s.get("observation") or {}).get("extra") or {}).get("elapsed_s")
        ms = max(0.0, el - (prev_obs if prev_obs is not None else el))
        ts = max(0.0, obs_el - el) if obs_el is not None else 0.0
        prev_obs = obs_el if obs_el is not None else el
        tcs = s.get("tool_calls") or []
        if not tcs:
            pending += ms
            continue
        d = tvr.obs_dict(s)
        share = (ms + pending) / len(tcs)
        pending = 0.0
        for tc in tcs:
            ci += 1
            fn, args = tc.get("function_name"), tc.get("arguments") or {}
            rec = dict(i=ci, fn=fn, sec=share + ts / len(tcs), model_s=share, tool_s=ts / len(tcs),
                       clock=obs_el if obs_el is not None else el, ok=tvr.call_ok(d), path="", cls="OTHER",
                       pyloc=False, edit=False, budget=d.get("error_type") == "BudgetExceeded")
            out = tvr.obs_text(d)
            rec["out"] = out  # kept in memory only, never written
            if fn == "read_file":
                rec["cls"], rec["path"] = "READ", path_of(args)
            elif fn == "get_status":
                rec["cls"] = "STATUS"
            elif fn == "run_command":
                cmd = str(args.get("command", ""))
                rec["cls"], rec["pyloc"] = classify_cmd(cmd)
                if rec["cls"] == "SHREAD":
                    ps = shread_paths(cmd)
                    rec["path"] = ps[0] if ps else ""
                rec["shedit"] = bool(tvr.CMD_EDIT.search(cmd)) and rec["cls"] in ("SHEDIT", "OTHER")
            elif fn in ("edit_file", "write_file"):
                pth = path_of(args)
                rec["path"] = pth
                repo = bool(pth) and not pth.startswith("/") and not pth.startswith("tmp/")
                src = repo and not tvr.is_test_path(pth)
                scratch_root = fn == "write_file" and "/" not in pth and bool(SCRATCH_BASE.match(os.path.basename(pth)))
                if src and not scratch_root:
                    rec["cls"], rec["edit"] = "EDIT", True
                elif fn == "write_file":
                    rec["cls"] = "SCRATCH"
                    rec["pool_edit"] = src  # pool31b would have counted it
                else:
                    rec["cls"] = "EDIT_NONSRC"
            elif fn == "submit_patch":
                rec["cls"] = "SUBMIT"
            calls.append(rec)
    return calls


def main():
    out_json = sys.argv[1]
    per_draw_out = sys.argv[2] if len(sys.argv) > 2 else None
    draws = []
    for run in RUNS:
        for line in open(os.path.join(HE, "runs", run, "task_results.jsonl")):
            row = json.loads(line)
            calls = parse(run, row)
            err = row.get("error") or ""
            draws.append(dict(iid=row["instance_id"], run=run, resolved=bool(row["resolved"]), calls=calls,
                              timecap="timeout" in err, callcap=(row.get("tool_calls") or 0) >= CAP_CALLS,
                              turnscap="turns" in err))
    tasks = tvr.load_rows(os.path.join(HE, "data", "raw", "tasks.jsonl"))
    refs = {}
    for iid in {d["iid"] for d in draws}:
        pd = tvr.parse_diff(tasks[iid]["patch"])
        refs[iid] = {p for p, f in pd.items() if not f["new"] and not tvr.is_test_path(p)}
    del tasks
    by_task = collections.defaultdict(list)
    for d in draws:
        by_task[d["iid"]].append(d["resolved"])
    noisy = {k for k, v in by_task.items() if 0 < sum(v) < len(v)}

    # per-draw features
    all_search_s, all_edit_s = [], []
    pool_first_diff = 0
    for d in draws:
        cs = d["calls"]
        fe = next((c for c in cs if c["edit"]), None)
        fl = next((c for c in cs if c["edit"] and c["ok"]), None)
        pool_fe = next((c for c in cs if c["edit"] or c.get("pool_edit")), None)
        if (pool_fe and pool_fe["i"]) != (fe and fe["i"]):
            pool_first_diff += 1
        d["first_try"] = fe["i"] if fe else None
        d["first_ok"] = fl["i"] if fl else None
        d["pre"] = [c for c in cs if fe is None or c["i"] < fe["i"]]
        edited = {c["path"] for c in cs if c["edit"]}
        d["edited_any"] = sorted(edited)
        d["noisy"] = d["iid"] in noisy
        for c in d["pre"]:
            if c["cls"] == "SEARCH":
                all_search_s.append(c["sec"])
        if fe:
            all_edit_s.append(fe["sec"])
        # file eventually edited (first attempt's file): when was it first read / first named
        if fe:
            tgt = fe["path"]
            d["tgt_read_first3"] = any(c["cls"] == "READ" and c["path"] == tgt for c in cs[:3])
            d["tgt_named_first3"] = any(tgt and tgt in (c.get("out") or "") for c in cs[:3]) or d["tgt_read_first3"]
            named = [c["i"] for c in d["pre"] if (tgt and tgt in (c.get("out") or "")) or
                     (c["cls"] in ("READ", "SHREAD") and c["path"] == tgt)]
            d["tgt_first_named"] = named[0] if named else None
            rd = [c["i"] for c in d["pre"] if c["cls"] == "READ" and c["path"] == tgt]
            d["tgt_first_read"] = rd[0] if rd else None
        # reference (gold-patch) source files: when were they first named in any output, or first read
        rf = refs[d["iid"]]
        d["n_ref"] = len(rf)
        nm = [c["i"] for c in d["pre"] if any(r in (c.get("out") or "") for r in rf) or
              (c["cls"] in ("READ", "SHREAD") and c["path"] in rf)]
        rr = [c["i"] for c in d["pre"] if c["cls"] == "READ" and c["path"] in rf]
        d["ref_named_at"] = nm[0] if nm else None
        d["ref_read_at"] = rr[0] if rr else None
        d["fe_on_ref"] = (fe["path"] in rf) if fe else None
        k = d["ref_named_at"]
        d["sec_to_ref"] = sum(c["sec"] for c in d["pre"] if c["i"] <= k) if k else 0.0
        d["distinct_read"] = len({c["path"] for c in d["pre"] if c["cls"] == "READ" and c["path"]})
        d["shedit_pre"] = any(c.get("shedit") for c in d["pre"])
        d["fe_clock"] = fe["clock"] if fe else None
        d["last_clock"] = max([c["clock"] for c in cs], default=0.0)
        d["ncalls"] = len(cs)
    script_cost = statistics.median(all_search_s)
    edit_cost = statistics.median(all_edit_s)

    def replaced(d, variant):
        """Calls a locate script would replace in the pre-edit window."""
        edited = set(d["edited_any"])
        rep = []
        for c in d["pre"]:
            if c["cls"] == "SEARCH":
                rep.append(c)
            elif c["cls"] == "READ" and c["path"] not in edited:
                rep.append(c)
            elif variant == "wide" and c["cls"] == "SHREAD" and c["path"] not in edited:
                rep.append(c)
            elif variant == "wide" and c["cls"] == "RUN" and c["pyloc"]:
                rep.append(c)
        return rep

    def reach(d, s_sec, s_calls):
        """A draw that never attempted an edit gets one more turn (assumed to be the edit) inside the caps.

        The draw is replayed with its own calls and seconds, minus the saved ones; the extra turn costs the draw's own
        median per-call seconds. A time-capped draw is taken to end at the cap (CAP_S), so it needs saved seconds >= one
        own-median turn; a call-capped draw needs >= 1 saved call; a draw that hit neither cap already had room."""
        own = statistics.median([c["sec"] for c in d["calls"]]) if d["calls"] else edit_cost
        ok_t = (s_sec >= own) if d["timecap"] else (d["last_clock"] - s_sec + own <= CAP_S)
        ok_c = (s_calls >= 1) if (d["callcap"] or d["turnscap"]) else (d["ncalls"] - s_calls + 1 <= CAP_CALLS)
        return ok_t and ok_c

    for d in draws:
        # locate-only ceiling: calls 1..k (k = first call whose output names a reference file) become one call
        k = d["ref_named_at"]
        d["loc_save_calls"] = (k - 1) if k else 0
        d["loc_save_s"] = max(0.0, d["sec_to_ref"] - script_cost) if k and k > 1 else 0.0
        d["loc_fit"] = reach(d, d["loc_save_s"], d["loc_save_calls"])
        for v in ("strict", "wide"):
            rep = replaced(d, v)
            n = len(rep)
            sec = sum(c["sec"] for c in rep)
            d[f"save_calls_{v}"] = max(0, n - 1)
            d[f"save_s_{v}"] = max(0.0, sec - script_cost) if n else 0.0
            d[f"fit_{v}"] = reach(d, d[f"save_s_{v}"], d[f"save_calls_{v}"])

    groups = {
        "all": draws,
        "resolved": [d for d in draws if d["resolved"]],
        "unresolved": [d for d in draws if not d["resolved"]],
        "noisy_fail": [d for d in draws if d["noisy"] and not d["resolved"]],
        "noisy_solve": [d for d in draws if d["noisy"] and d["resolved"]],
        "never_landed": [d for d in draws if d["first_ok"] is None],
        "never_landed_unres": [d for d in draws if d["first_ok"] is None and not d["resolved"]],
        "no_attempt": [d for d in draws if d["first_try"] is None],
    }
    classes = ["SEARCH", "READ", "SHREAD", "RUN", "SCRATCH", "STATUS", "SHEDIT", "OTHER", "EDIT_NONSRC", "SUBMIT"]
    res = dict(script_cost_s=script_cost, edit_cost_s=edit_cost, n_noisy_tasks=len(noisy),
               pool_first_try_differs=pool_first_diff, groups={})
    for g, ds in groups.items():
        n = len(ds)
        tab = {}
        tot_calls = sum(len(d["pre"]) for d in ds)
        tot_s = sum(c["sec"] for d in ds for c in d["pre"])
        for k in classes:
            cs = [c for d in ds for c in d["pre"] if c["cls"] == k]
            tab[k] = dict(calls=len(cs), calls_per_draw=round(len(cs) / n, 2) if n else 0,
                          sec=round(sum(c["sec"] for c in cs), 1),
                          sec_per_draw=round(sum(c["sec"] for c in cs) / n, 1) if n else 0,
                          model_s=round(sum(c["model_s"] for c in cs), 1), tool_s=round(sum(c["tool_s"] for c in cs), 1))
        pyl = [c for d in ds for c in d["pre"] if c["cls"] == "RUN" and c["pyloc"]]
        edited = [d for d in ds if d["first_try"] is not None]
        fn_ = [d["tgt_first_named"] for d in edited if d.get("tgt_first_named")]
        fr_ = [d["tgt_first_read"] for d in edited if d.get("tgt_first_read")]
        gi = dict(n=n, pre_calls=tot_calls, pre_calls_per_draw=round(tot_calls / n, 2) if n else 0,
                  pre_s=round(tot_s, 1), pre_s_per_draw=round(tot_s / n, 1) if n else 0, classes=tab,
                  run_pyloc_calls=len(pyl), run_pyloc_s=round(sum(c["sec"] for c in pyl), 1),
                  first_try_median=statistics.median([d["first_try"] for d in edited]) if edited else None,
                  fe_clock_median=round(statistics.median([d["fe_clock"] for d in edited]), 1) if edited else None,
                  n_with_attempt=len(edited),
                  distinct_read_mean=round(statistics.mean([d["distinct_read"] for d in ds]), 2) if n else 0,
                  distinct_read_median=statistics.median([d["distinct_read"] for d in ds]) if n else 0,
                  tgt_read_first3=sum(d.get("tgt_read_first3", False) for d in edited),
                  tgt_named_first3=sum(d.get("tgt_named_first3", False) for d in edited),
                  tgt_first_named_median=statistics.median(fn_) if fn_ else None,
                  tgt_first_read_median=statistics.median(fr_) if fr_ else None,
                  tgt_never_read_before_edit=sum(1 for d in edited if not d.get("tgt_first_read")),
                  gap_named_to_edit_median=statistics.median([d["first_try"] - d["tgt_first_named"] for d in edited
                                                              if d.get("tgt_first_named")]) if fn_ else None,
                  timecap=sum(d["timecap"] for d in ds), callcap=sum(d["callcap"] for d in ds),
                  shedit_pre=sum(d["shedit_pre"] for d in ds))
        rn = [d["ref_named_at"] for d in ds if d["ref_named_at"]]
        rr = [d["ref_read_at"] for d in ds if d["ref_read_at"]]
        na = [d for d in ds if d["first_try"] is None]
        gi["ref"] = dict(
            named_by_call3=sum(1 for d in ds if d["ref_named_at"] and d["ref_named_at"] <= 3),
            named_ever_pre=len(rn), named_at_median=statistics.median(rn) if rn else None,
            sec_to_named_median=round(statistics.median([d["sec_to_ref"] for d in ds if d["ref_named_at"]]), 1)
            if rn else None,
            read_by_call3=sum(1 for d in ds if d["ref_read_at"] and d["ref_read_at"] <= 3),
            read_ever_pre=len(rr), read_at_median=statistics.median(rr) if rr else None,
            first_edit_on_ref=sum(1 for d in edited if d["fe_on_ref"]),
            no_attempt_ref_named=sum(1 for d in na if d["ref_named_at"]),
            no_attempt_ref_read=sum(1 for d in na if d["ref_read_at"]),
            no_attempt_ref_read_by3=sum(1 for d in na if d["ref_read_at"] and d["ref_read_at"] <= 3))
        gi["ceil_locate_only"] = dict(
            save_calls=sum(d["loc_save_calls"] for d in ds),
            save_calls_per_draw=round(sum(d["loc_save_calls"] for d in ds) / n, 2) if n else 0,
            save_s=round(sum(d["loc_save_s"] for d in ds), 1),
            save_s_per_draw=round(sum(d["loc_save_s"] for d in ds) / n, 1) if n else 0,
            no_attempt_fit=sum(1 for d in na if d["loc_fit"]),
            no_attempt_capped_fit=sum(1 for d in na if (d["timecap"] or d["callcap"]) and d["loc_fit"]))
        for v in ("strict", "wide"):
            gi[f"ceil_{v}"] = dict(
                save_calls=sum(d[f"save_calls_{v}"] for d in ds),
                save_calls_per_draw=round(sum(d[f"save_calls_{v}"] for d in ds) / n, 2) if n else 0,
                save_s=round(sum(d[f"save_s_{v}"] for d in ds), 1),
                save_s_per_draw=round(sum(d[f"save_s_{v}"] for d in ds) / n, 1) if n else 0,
                no_attempt=sum(1 for d in ds if d["first_try"] is None),
                no_attempt_fit=sum(1 for d in ds if d["first_try"] is None and d[f"fit_{v}"]),
                no_attempt_capped=sum(1 for d in ds if d["first_try"] is None and (d["timecap"] or d["callcap"])),
                no_attempt_capped_fit=sum(1 for d in ds if d["first_try"] is None and (d["timecap"] or d["callcap"])
                                          and d[f"fit_{v}"]),
                attempted_capped=sum(1 for d in ds if d["first_try"] is not None and (d["timecap"] or d["callcap"])),
                fe_earlier_s_median=round(statistics.median([d[f"save_s_{v}"] for d in ds
                                                             if d["first_try"] is not None]), 1)
                if any(d["first_try"] is not None for d in ds) else None,
            )
        res["groups"][g] = gi
    # capped draws: on which clock does the time cap fire?
    tc = [d["last_clock"] for d in draws if d["timecap"]]
    res["timecap_last_clock_min_med_max"] = [round(min(tc), 1), round(statistics.median(tc), 1), round(max(tc), 1)]
    json.dump(res, open(out_json, "w"), indent=1)
    if per_draw_out:
        with open(per_draw_out, "w") as fh:
            for d in draws:
                fh.write(json.dumps({k: v for k, v in d.items() if k not in ("calls", "pre", "edited_any")}) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "groups"}))


if __name__ == "__main__":
    main()
