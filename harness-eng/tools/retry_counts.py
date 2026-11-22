"""Retry mechanism counts for a tree whose root calls the `solve` agent_tool (R-018 onward). Counts only; never prints
trace text, code or paths.

  python3 -I tools/retry_counts.py runs/<RUN> [runs/<RUN> ...]

Per task the steps are cut into attempts at each root `solve` call. An attempt is empty when every submit_patch
result inside it reports files_changed 0, non-empty when one reports more than 0, and unknown when it holds no
submit_patch result. From R-020 on, the root's count command (a bare integer on stdout) is read the same way. Prints, per run: the histogram of solve calls per task; first-attempt empty / non-empty /
unknown; retried (first attempt empty and a second solve call followed); over-retry (a second solve call after a
non-empty first attempt); retry_miss (first attempt empty, not retried); rescued (resolved, first attempt empty); tasks with more than 3 solve calls; and solve_after_submit
(R-021, tasks with a root solve call after any submit_patch, which cannot change the outcome).
R-029 (change-check skill): a check that prints a line starting "syntax error" counts as a non-empty attempt, and
per task: syntax_flagged (any such line), syntax_retried (a solve call followed one), syntax_retry_miss (flagged, fewer
than 3 solve calls, no solve call after it), syntax_last (the last check before submit printed it), syntax_rescued
(flagged and resolved).
"""
import collections, json, os, re, sys

FC = re.compile(r'files_changed\W{0,4}(\d+)')


def attempts(steps):
    segs, cur, started = [], [], False
    for s in steps:
        if s.get("source") != "agent":
            continue
        names = [c["function_name"] for c in (s.get("tool_calls") or [])]
        if s["extra"].get("author") == "swe_agent" and "solve" in names:
            if started:
                segs.append(cur)
            cur, started = [], True
        if s["extra"].get("author") == "swe_agent" and ("run_command" in names or "run_skill_script" in names) and s.get("observation"):
            try:   # R-020: the root's count command or change-count skill prints the number of changed source files
                out = str(json.loads(s["observation"].get("content") or "{}").get("stdout", "")).strip()
            except (ValueError, AttributeError):
                out = ""
            if out.isdigit():
                cur.append(int(out))
            elif out.startswith("syntax error"):   # R-029: a changed source file does not parse; non-empty
                cur.append(1)
        if "submit_patch" in names and s.get("observation"):
            m = FC.findall(str(s["observation"].get("content")))
            if m:
                cur.append(int(m[-1]))
    if started:
        segs.append(cur)
    return segs


def state(seg):
    if not seg:
        return "unknown"
    return "nonempty" if max(seg) > 0 else "empty"


for run in sys.argv[1:]:
    agg = collections.Counter(); hist = collections.Counter()
    for line in open(os.path.join(run, "task_results.jsonl")):
        r = json.loads(line)
        tp = os.path.join(run, "traces", f"trace_{r['instance_id']}.json")
        if not os.path.exists(tp):
            agg["no_trace"] += 1
            continue
        steps = json.load(open(tp))["steps"]
        segs = attempts(steps)
        # R-021 (reported, not a gate): a root solve call after any submit_patch cannot change the outcome, since the
        # solver's final text then ends the task with the earlier patch already submitted.
        sub_seen = False
        for s in steps:
            if s.get("source") != "agent":
                continue
            names = [c["function_name"] for c in (s.get("tool_calls") or [])]
            if s["extra"].get("author") == "swe_agent" and "solve" in names and sub_seen:
                agg["solve_after_submit"] += 1
                break
            if "submit_patch" in names:
                sub_seen = True
        seq = []   # R-029: root check outputs and solve calls, in order
        for s in steps:
            if s.get("source") != "agent" or s["extra"].get("author") != "swe_agent":
                continue
            names = [c["function_name"] for c in (s.get("tool_calls") or [])]
            if "solve" in names:
                seq.append("solve")
            if "run_skill_script" in names and s.get("observation"):
                try:
                    out = str(json.loads(s["observation"].get("content") or "{}").get("stdout", "")).strip()
                except (ValueError, AttributeError):
                    out = ""
                seq.append("syn" if out.startswith("syntax error") else "chk")
        if "syn" in seq:
            agg["syntax_flagged"] += 1
            agg["syntax_rescued"] += bool(r["resolved"])
            i = seq.index("syn")
            later = "solve" in seq[i + 1:]
            agg["syntax_retried"] += later
            agg["syntax_retry_miss"] += (not later) and seq.count("solve") < 3
            checks = [x for x in seq if x in ("syn", "chk")]
            agg["syntax_last"] += checks[-1] == "syn"
        hist[len(segs)] += 1
        agg["solve_calls_gt3"] += len(segs) > 3
        if not segs:
            continue
        first = state(segs[0])
        agg["first_" + first] += 1
        if first == "empty":
            agg["retried"] += len(segs) > 1
            agg["rescued"] += bool(r["resolved"])
        if first == "nonempty" and len(segs) > 1:
            agg["over_retry"] += 1
    out = {"run": os.path.basename(run.rstrip("/")), "solve_calls_hist": dict(sorted(hist.items()))}
    out.update(agg)
    out["retry_miss"] = agg["first_empty"] - agg["retried"]   # first attempt empty, no second solve call
    print(json.dumps(out))
