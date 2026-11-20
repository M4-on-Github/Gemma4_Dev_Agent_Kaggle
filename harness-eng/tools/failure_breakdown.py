"""Where a draw's wall time went, per task and per failure group. Standard library, Python 3.6+.

  python3 -I tools/failure_breakdown.py runs/R-008-31b-base-te-d1 runs/R-008-31b-base-te-d2 \
      --tvr runs/_analysis/trace_vs_reference.jsonl

Writes runs/_analysis/failure_breakdown.jsonl (one row per task-draw; paths, counts and seconds only, no repo
or trace text) and prints markdown tables: the time decomposition per group, the overlap of the time-cap and
empty-patch groups, their stability across the draws given, and, for unresolved draws, when the reference file
was first opened and first named in the agent's own thoughts.

Time method (the one R-004 used, so the numbers compare):
  - A step's `elapsed_s` is stamped when the model's reply arrives, its observation's when the tool returns.
    Model seconds of a turn = its `elapsed_s` minus the previous observation's; tool seconds = observation
    minus call.
  - Decode seconds = completion_tokens / the draw's median rate on turns of 300 tokens or more.
  - The rest of a turn's model seconds is compaction when prompt_tokens fell by more than 3000 from the previous
    turn, a stall when more than 30 s are left unexplained without one, and overhead otherwise.
  - The unfinished final turn = duration_s minus the last recorded elapsed_s (a turn still generating when the
    session ended leaves no step).
Group ends (`end`) and miss classes (`class`) come from trace_vs_reference.py's rows when --tvr is given.
"""
import argparse
import collections
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import trace_vs_reference as tvr  # noqa: E402

LONG = 800          # a "long" turn, as in R-004
RATE_MIN = 300      # turns used for the draw's decode rate
COMPACT_DROP = 3000
STALL_S = 30.0
PARTS = ["decode_short", "decode_long", "overhead", "compaction", "stall", "tool", "unfinished"]


def ref_names(diff_text):
    """Reference files, their basenames, and function/class names from the hunk headers and +/- def lines."""
    files = list(tvr.parse_diff(diff_text).keys())
    names = set()
    for line in (diff_text or "").splitlines():
        m = re.match(r"^@@ .*? @@\s*(?:async\s+)?(?:def|class)\s+(\w+)", line)
        if m:
            names.add(m.group(1))
        m = re.match(r"^[+-]\s*(?:async\s+)?(?:def|class)\s+(\w+)", line)
        if m and not line.startswith(("+++", "---")):
            names.add(m.group(1))
    names = {n for n in names if len(n) >= 5 and not n.startswith("test")}
    return files, names


def mentions(text, files, names):
    if not text:
        return False
    for f in files:
        if f in text or os.path.basename(f) in text:
            return True
    return any(re.search(r"\b%s\b" % re.escape(n), text) for n in names)


def is_source_edit(fn, args, d, ref_files):
    if fn not in tvr.EDIT_TOOLS or not tvr.call_ok(d):
        return False
    p = tvr.norm_path(args.get("filepath") or args.get("path") or args.get("file_path") or "")
    return bool(p) and not tvr.is_test_path(p) and not p.startswith("/")


def analyze(trace, row, ref_files, ref_fn_names):
    steps = trace.get("steps", [])
    turns = []        # (model_s, tool_s, completion, prompt)
    prev_obs = None
    t_first_ref_read = t_first_ref_named = t_first_edit = None
    last_elapsed = 0.0
    long_end_tools = collections.Counter()
    for s in steps:
        ex = s.get("extra") or {}
        el = ex.get("elapsed_s")
        if s.get("source") != "agent":
            if el is not None and prev_obs is None:
                prev_obs = el
            continue
        mt = s.get("metrics") or {}
        comp = mt.get("completion_tokens") or 0
        prm = mt.get("prompt_tokens") or 0
        if el is None:
            continue
        obs_el = ((s.get("observation") or {}).get("extra") or {}).get("elapsed_s")
        model_s = max(0.0, el - (prev_obs if prev_obs is not None else el))
        tool_s = max(0.0, obs_el - el) if obs_el is not None else 0.0
        turns.append((model_s, tool_s, comp, prm))
        last_elapsed = max(el, obs_el or 0.0)
        prev_obs = obs_el if obs_el is not None else el
        if t_first_ref_named is None and ex.get("event_type") in ("thinking", "text", None) and \
                mentions(s.get("message") or "", ref_files, ref_fn_names):
            t_first_ref_named = el
        d = tvr.obs_dict(s)
        for tc in s.get("tool_calls") or []:
            fn, args = tc.get("function_name"), tc.get("arguments") or {}
            blob = json.dumps(args)
            if comp >= LONG:
                long_end_tools[fn] += 1
            if t_first_ref_read is None and any(f in blob for f in ref_files) and \
                    fn in ("read_file", "run_command", "view_file", "search_files", "grep"):
                t_first_ref_read = el
            if t_first_edit is None and is_source_edit(fn, args, d, ref_files):
                t_first_edit = el
    dur = float(row.get("duration_s") or 0.0)
    return turns, {"t_first_ref_read": t_first_ref_read, "t_first_ref_named": t_first_ref_named,
                   "t_first_edit": t_first_edit, "unfinished": max(0.0, dur - last_elapsed),
                   "long_end_tools": dict(long_end_tools)}


def decompose(turns, rate):
    out = dict.fromkeys(PARTS, 0.0)
    prev_prompt = None
    n_long = 0
    for model_s, tool_s, comp, prm in turns:
        dec = min(model_s, comp / rate) if rate else 0.0
        rest = model_s - dec
        out["decode_long" if comp >= LONG else "decode_short"] += dec
        n_long += comp >= LONG
        if prev_prompt is not None and prm < prev_prompt - COMPACT_DROP:
            out["compaction"] += rest
        elif rest > STALL_S:
            out["stall"] += rest
        else:
            out["overhead"] += rest
        out["tool"] += tool_s
        prev_prompt = prm
    return out, n_long


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--tvr", default=os.path.join(ROOT, "runs", "_analysis", "trace_vs_reference.jsonl"))
    ap.add_argument("--out", default=os.path.join(ROOT, "runs", "_analysis", "failure_breakdown.jsonl"))
    a = ap.parse_args()

    tasks = tvr.load_rows(os.path.join(ROOT, "data", "raw", "tasks.jsonl"))
    tv = {}
    if a.tvr and os.path.exists(a.tvr):
        with open(a.tvr) as fh:
            for line in fh:
                if line.strip():
                    r = json.loads(line)
                    tv[(r["run"], r["instance_id"])] = r

    rows = []
    for rd in a.runs:
        run = os.path.basename(os.path.normpath(rd))
        res = tvr.load_rows(os.path.join(rd, "task_results.jsonl"))
        loaded = []
        for iid, row in res.items():
            p = os.path.join(rd, "traces", "trace_%s.json" % iid)
            if not os.path.exists(p):
                continue
            with open(p) as fh:
                trace = json.load(fh)
            files, names = ref_names(tasks.get(iid, {}).get("patch", ""))
            turns, facts = analyze(trace, row, files, names)
            loaded.append((iid, row, turns, facts))
        rates = [c / m for _, _, ts, _ in loaded for m, _, c, _ in ts if c >= RATE_MIN and m > 0]
        rate = statistics.median(rates) if rates else 0.0
        for iid, row, turns, facts in loaded:
            parts, n_long = decompose(turns, rate)
            parts["unfinished"] = facts.pop("unfinished")
            t = tv.get((run, iid), {})
            r = {"run": run, "instance_id": iid, "resolved": bool(row.get("resolved")),
                 "end": t.get("end"), "class": t.get("class"),
                 "empty_patch": not (row.get("patch_chars") or 0),
                 "duration_s": row.get("duration_s"), "tool_calls": row.get("tool_calls"),
                 "turns": len(turns), "long_turns": n_long, "rate_tok_s": round(rate, 1)}
            r.update({k: round(v, 1) for k, v in parts.items()})
            r.update({k: (round(v, 1) if isinstance(v, float) else v) for k, v in facts.items()})
            rows.append(r)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print("wrote %d rows to %s\n" % (len(rows), a.out))
    report(rows)
    report_buckets(rows, tv)


def pct(x, tot):
    return "%d (%d%%)" % (round(x), round(100 * x / tot)) if tot else "0"


def report(rows):
    groups = [
        ("all", lambda r: True),
        ("resolved", lambda r: r["resolved"]),
        ("failed", lambda r: not r["resolved"]),
        ("at the time cap", lambda r: r["end"] == "time cap"),
        ("empty patch", lambda r: r["empty_patch"]),
        ("time cap and empty", lambda r: r["end"] == "time cap" and r["empty_patch"]),
        ("call cap", lambda r: r["end"] == "call cap"),
    ]
    print("| Draw | Group | Tasks | Resolved | Wall s | Long turns | " + " | ".join(PARTS) + " |")
    print("|---|---|---|---|---|---|" + "---|" * len(PARTS))
    for run in sorted({r["run"] for r in rows}):
        rr = [r for r in rows if r["run"] == run]
        for name, f in groups:
            g = [r for r in rr if f(r)]
            tot = {p: sum(x[p] for x in g) for p in PARTS}
            wall = sum(tot.values())
            print("| %s | %s | %d | %d | %d | %d | %s |" % (
                run, name, len(g), sum(x["resolved"] for x in g), wall,
                sum(x["long_turns"] for x in g), " | ".join(pct(tot[p], wall) for p in PARTS)))
    # stability across draws
    by = collections.defaultdict(dict)
    for r in rows:
        by[r["instance_id"]][r["run"]] = r
    runs = sorted({r["run"] for r in rows})
    print("\nPer task over %d draws: how many draws ended in each state" % len(runs))
    for name, f in [("time cap", lambda r: r["end"] == "time cap"), ("empty patch", lambda r: r["empty_patch"]),
                    ("resolved", lambda r: r["resolved"])]:
        c = collections.Counter(sum(1 for x in by[i].values() if f(x)) for i in by if len(by[i]) == len(runs))
        print("  %-12s" % name, " ".join("%d/%d:%d" % (k, len(runs), c[k]) for k in range(len(runs) + 1)))
    # timing of the reference file for failures
    print("\nUnresolved draws: reference opened / named in thoughts / first source edit (seconds)")
    for name, f in [("time cap, empty", lambda r: r["end"] == "time cap" and r["empty_patch"]),
                    ("time cap, has patch", lambda r: r["end"] == "time cap" and not r["empty_patch"]),
                    ("empty, not time cap", lambda r: r["end"] != "time cap" and r["empty_patch"]),
                    ("other failed", lambda r: r["end"] != "time cap" and not r["empty_patch"])]:
        g = [r for r in rows if not r["resolved"] and f(r)]
        if not g:
            continue

        def med(k):
            v = [r[k] for r in g if r[k] is not None]
            return "%d/%d, median %s" % (len(v), len(g), round(statistics.median(v)) if v else "-")
        print("  %-20s n=%-3d opened %s | named %s | edited %s" % (
            name, len(g), med("t_first_ref_read"), med("t_first_ref_named"), med("t_first_edit")))


def bucket(r):
    empty = r["empty_patch"]
    if r["end"] == "time cap":
        return "time cap, no edit landed" if empty else "time cap, has patch"
    if r["end"] == "call cap":
        return "call cap, empty" if empty else "call cap, has patch"
    return "submitted, %s" % r["class"]


def report_buckets(rows, tv):
    """Unresolved draws by how they ended, and how many sit on tasks that some draw of the same model in the
    --tvr ledger resolved (the part a process fix can plausibly reach)."""
    if not tv:
        return
    ever = collections.Counter()
    for t in tv.values():
        ever[(t.get("model"), t["instance_id"])] += bool(t.get("resolved"))
    out = collections.defaultdict(lambda: [0, 0, set(), collections.Counter()])
    for r in rows:
        t = tv.get((r["run"], r["instance_id"]))
        if r["resolved"] or not t:
            continue
        b = out[bucket(r)]
        b[0] += 1
        b[1] += ever[(t.get("model"), r["instance_id"])] > 0
        b[2].add(r["instance_id"])
        b[3].update(t.get("edit_fail_types") or {})
    print("\n| Unresolved bucket | Draws | Tasks | On tasks some draw resolved | Edit failure types |")
    print("|---|---|---|---|---|")
    for k in sorted(out, key=lambda k: -out[k][0]):
        n, reach, ids, ft = out[k]
        print("| %s | %d | %d | %d | %s |" % (k, n, len(ids), reach,
                                             ", ".join("%s %d" % kv for kv in ft.most_common()) or "-"))


if __name__ == "__main__":
    main()
