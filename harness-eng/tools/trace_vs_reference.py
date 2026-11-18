"""Compare every failing Gemma draw against the task's reference patch. Standard library, Python 3.6+.

  python3 tools/trace_vs_reference.py                       # writes runs/_analysis/trace_vs_reference.jsonl
  python3 tools/trace_vs_reference.py --summary             # also prints the class tables
  python3 tools/trace_vs_reference.py --show fastapi_14099  # one line per draw of one task

Inputs: data/raw/tasks.jsonl (reference patch), the four control runs (gradeable set), and every
runs/{R,S,F}-* dir with a task_results.jsonl (draws). Output rows hold no repo code, only paths,
line numbers, counts and short error strings; they stay under runs/ (not in git).

Per draw it computes: reference files and hunks; the agent's final patch files and hunks; whether a
reference file was named in a tool output and read (with hunk coverage) before the first edit; hunk
overlap (within WINDOW lines); edits to other files; edit-tool failures; the end reason; whether a
test or check ran after the last edit and passed; one primary miss class.
"""
import argparse
import collections
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WINDOW = 5
SHIMS_FROM_UTC = "2026-11-18T17:10:00Z"  # HENG_SHIMS=1 on every run started after this (README, Setup 7)
REPO_TOPS = {"fastapi", "rich", "requests", "httpx", "scripts", "tests", "docs_src", "docs", "src"}
EDIT_TOOLS = ("edit_file", "write_file")
CLASSES = ["no-edit/empty patch", "edit-tool failure", "wrong file", "right file wrong region",
           "partial fix", "all hunks touched, wrong change"]


# ---------------------------------------------------------------- diff parsing

def parse_diff(text):
    """{path: {"new": bool, "hunks": [(lo, hi)]}} with (lo, hi) the old-file lines changed.

    Removed lines count as themselves; an insertion counts as the two old lines around it."""
    files = collections.OrderedDict()
    cur = None
    old_ln = None
    hunk = None
    old_path = None
    for line in (text or "").splitlines():
        if line.startswith("diff --git "):
            cur = None
            continue
        if line.startswith("--- "):
            old_path = line[4:].strip()
            continue
        if line.startswith("+++ ") and old_path is not None:
            new_path = line[4:].strip()
            p = new_path if new_path != "/dev/null" else old_path
            p = re.sub(r"^[ab]/", "", p.split("\t")[0])
            cur = files.setdefault(p, {"new": old_path == "/dev/null", "deleted": new_path == "/dev/null",
                                       "hunks": []})
            old_path = None
            continue
        m = re.match(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
        if m and cur is not None:
            old_ln = int(m.group(1))
            if m.group(2) == "0":
                old_ln += 1  # "-N,0" means insertion after line N
            hunk = [None, None, [], []]
            cur["hunks"].append(hunk)
            continue
        if cur is None or hunk is None:
            continue
        if line.startswith("-"):
            lo, hi = old_ln, old_ln
            old_ln += 1
            hunk[2].append(line[1:])
        elif line.startswith("+"):
            lo, hi = max(1, old_ln - 1), old_ln
            hunk[3].append(line[1:])
        elif line.startswith(" ") or line == "":
            old_ln += 1
            continue
        else:
            continue
        hunk[0] = lo if hunk[0] is None else min(hunk[0], lo)
        hunk[1] = hi if hunk[1] is None else max(hunk[1], hi)
    for f in files.values():
        kept = [h for h in f["hunks"] if h[0] is not None]
        f["hunks"] = [(h[0], h[1]) for h in kept]
        f["cosmetic"] = [is_cosmetic(h[2], h[3]) for h in kept]
        # a line moved from one hunk to another (an import moved up, say) is cosmetic in both hunks
        all_minus = set(_squash([l]) for h in kept for l in h[2]) - {""}
        all_plus = set(_squash([l]) for h in kept for l in h[3]) - {""}
        for i, h in enumerate(kept):
            m = [_squash([l]) for l in h[2] if _squash([l])]
            p = [_squash([l]) for l in h[3] if _squash([l])]
            if (m or p) and all(x in all_plus for x in m) and all(x in all_minus for x in p):
                f["cosmetic"][i] = True
    return files


def _squash(lines):
    return re.sub(r"[\s(),]", "", "".join(lines))


def is_cosmetic(minus, plus):
    """True for a hunk that only re-wraps code (black-style parentheses, line breaks, trailing commas),
    only reorders an import line, or only changes comments."""
    if _squash(minus) == _squash(plus):
        return True
    if sorted(_squash([m]) for m in minus) == sorted(_squash([q]) for q in plus):
        return True
    changed = [l.strip() for l in minus + plus if l.strip()]
    if changed and all(l.startswith("#") for l in changed):
        return True
    if minus and plus and all(l.strip().startswith(("from ", "import ")) for l in minus + plus if l.strip()):
        names = lambda ls: sorted(re.findall(r"\w+", " ".join(l.split(" import ", 1)[-1] for l in ls)))
        if names(minus) == names(plus):
            return True
    return False


def near(a, b, w=WINDOW):
    return a[0] <= b[1] + w and a[1] >= b[0] - w


PROTECTED_BASENAMES = {"conftest.py", "pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg", ".pytest.ini",
                       "sitecustomize.py", "usercustomize.py", "_swegemma_stubs.py"}


def is_protected(p):
    """Files the harness strips from the agent's patch (HARNESS_README section on protected files)."""
    b = os.path.basename(p)
    return (b in PROTECTED_BASENAMES or b.endswith(".pth") or is_test_path(p)
            or p.startswith("test/") or p.startswith("testing/") or b.endswith("_test.py"))


def is_test_path(p):
    return p.startswith("tests/") or "/tests/" in p or os.path.basename(p).startswith("test_")


# ---------------------------------------------------------------- trace parsing

def norm_path(p):
    if not isinstance(p, str):
        return ""
    p = p.strip().strip('"').strip("'")
    m = re.search(r"/workspace/(.*)$", p)
    if m:
        p = m.group(1)
    while p.startswith("./"):
        p = p[2:]
    return p


def obs_dict(step):
    o = (step.get("observation") or {}).get("content")
    if o is None:
        return {}
    try:
        d = json.loads(o)
        return d if isinstance(d, dict) else {"raw": str(d)}
    except Exception:
        return {"raw": o}


def call_ok(d):
    if "error" in d and "status" not in d:
        return False
    return d.get("status") == "ok"


def obs_text(d):
    parts = []
    for k in ("stdout", "stderr", "content", "error_message", "details", "raw", "error"):
        v = d.get(k)
        if isinstance(v, str):
            parts.append(v)
    return "\n".join(parts)


CMD_EDIT = re.compile(r"(sed\s+-i|>\s*[\w./-]+\.py\b|tee\s+[\w./-]+\.py|git\s+apply|\bpatch\s+-p|open\([^)]*['\"]w)")
CMD_TEST = re.compile(r"(pytest|python3?\s|unittest|py_compile|-m\s+compileall|scripts/test)")


def cmd_read_ranges(cmd, ref_files):
    """(path, lo, hi) for shell reads of a reference file: cat/sed -n/head/tail/nl/awk."""
    out = []
    for rf in ref_files:
        if rf not in cmd:
            continue
        m = re.search(r"sed\s+-n\s+['\"]?(\d+),(\d+)p", cmd)
        if m:
            out.append((rf, int(m.group(1)), int(m.group(2))))
            continue
        m = re.search(r"head\s+-n?\s*(\d+)", cmd)
        if m and re.search(r"\bhead\b", cmd):
            out.append((rf, 1, int(m.group(1))))
            continue
        if re.search(r"\b(cat|nl|awk)\b", cmd) and not re.search(r"cat\s*<<|cat\s*>", cmd):
            out.append((rf, 1, 10 ** 7))
    return out


def analyze_trace(trace, ref, ref_files):
    """Walk the tool calls in order. Returns a dict of per-draw facts."""
    calls = []
    for s in trace.get("steps", []):
        tcs = s.get("tool_calls") or []
        if not tcs:
            continue
        d = obs_dict(s)
        for tc in tcs:
            calls.append((tc.get("function_name"), tc.get("arguments") or {}, d))
    ref_set = set(ref_files)
    named_before = False
    read_ranges = collections.defaultdict(list)  # before first edit
    read_any_ref_before = False
    first_edit = None
    last_edit = None
    edit_attempts = 0
    edit_fail = 0
    edit_fail_types = collections.Counter()
    edit_fail_ref = 0
    malformed = 0
    edited_paths_attempted = set()
    source_ok = 0
    protected_ok = 0
    first_fail = None
    for idx, (name, args, d) in enumerate(calls):
        ok = call_ok(d)
        is_edit = False
        if name in EDIT_TOOLS:
            edit_attempts += 1
            p = norm_path(args.get("filepath") or args.get("path") or "")
            edited_paths_attempted.add(p)
            repo_target = bool(p) and not p.startswith("/") and not p.startswith("tmp/")
            budget = d.get("error_type") == "BudgetExceeded"
            if ok:
                is_edit = True
                if repo_target:
                    source_ok += 1
                    if is_protected(p):
                        protected_ok += 1
            elif budget or not repo_target:
                # the call cap, or a scratch file outside the repo: not a failure to edit the source
                edit_fail_types["BudgetExceeded" if budget else "scratch path refused"] += 1
            else:
                edit_fail += 1
                if first_fail is None:
                    first_fail = idx
                if "error" in d and "status" not in d:
                    malformed += 1
                    edit_fail_types["malformed args"] += 1
                else:
                    msg = d.get("error_message") or ""
                    et = d.get("error_type") or "?"
                    if "not found" in msg:
                        et = "old_string not found"
                    elif "occurs" in msg:
                        et = "old_string not unique"
                    elif "identical" in msg:
                        et = "no-op edit"
                    elif "traversal" in msg:
                        et = "path outside workspace"
                    edit_fail_types[et] += 1
                if p in ref_set:
                    edit_fail_ref += 1
        elif name == "run_command":
            cmd = args.get("command") or ""
            if ok and CMD_EDIT.search(cmd) and "/tmp/" not in cmd.split(">")[-1][:40]:
                if any(rf in cmd for rf in ref_files) or re.search(r"sed\s+-i", cmd):
                    is_edit = True
        if is_edit:
            if first_edit is None:
                first_edit = idx
            last_edit = idx
        if first_edit is None:
            txt = obs_text(d) if ok or name == "run_command" else ""
            for rf in ref_files:
                if rf in txt:
                    named_before = True
                elif name == "run_command":
                    cmd = args.get("command") or ""
                    base = os.path.basename(rf)
                    if re.search(r"(^|\s|/)%s(\s|$)" % re.escape(base), txt) and os.path.dirname(rf) in cmd:
                        named_before = True
            if name == "read_file" and ok:
                p = norm_path(d.get("filepath") or args.get("filepath") or "")
                if p in ref_set:
                    read_any_ref_before = True
                    try:
                        lo = int(d.get("start_line") or 1)
                        hi = int(d.get("end_line") or 10 ** 7)
                    except Exception:
                        lo, hi = 1, 10 ** 7
                    read_ranges[p].append((lo, hi))
            elif name == "run_command" and ok:
                for (p, lo, hi) in cmd_read_ranges(args.get("command") or "", ref_files):
                    read_any_ref_before = True
                    read_ranges[p].append((lo, hi))
    # hunk coverage by reads before the first edit
    # (substantive hunks only, the same set the overlap uses; a new file counts as not readable)
    covered = 0
    for rf, info in ref.items():
        if info["new"]:
            continue
        subst = [h for h, c in zip(info["hunks"], info["cosmetic"]) if not c] or info["hunks"]
        for h in subst:
            if any(near(h, r, 0) for r in read_ranges.get(rf, [])):
                covered += 1
    # test after last edit
    test_after = False
    test_after_pass = False
    if last_edit is not None:
        for name, args, d in calls[last_edit + 1:]:
            if name == "run_command" and CMD_TEST.search(args.get("command") or ""):
                test_after = True
                if call_ok(d) and d.get("exit_code", 0) == 0:
                    test_after_pass = True
                else:
                    test_after_pass = False
    budget_hit = any((d.get("error_type") == "BudgetExceeded") for _, _, d in calls)
    return {
        "n_calls_trace": len(calls),
        "named_ref_before_edit": named_before,
        "read_ref_before_edit": read_any_ref_before,
        "ref_hunks_read_before_edit": covered,
        "first_edit_call": None if first_edit is None else first_edit + 1,
        "edit_attempts": edit_attempts,
        "source_edits_ok": source_ok,
        "protected_edits_ok": protected_ok,
        "edit_failures": edit_fail,
        "first_edit_failure_call": None if first_fail is None else first_fail + 1,
        "edit_failures_on_ref": edit_fail_ref,
        "edit_malformed": malformed,
        "edit_fail_types": dict(edit_fail_types),
        "edit_attempted_ref": bool(edited_paths_attempted & ref_set),
        "test_after_last_edit": test_after,
        "test_after_last_edit_pass": test_after_pass,
        "budget_exceeded_seen": budget_hit,
        "submit_called": any(n == "submit_patch" for n, _, _ in calls),
    }


# ---------------------------------------------------------------- env flags

MISSING_MOD = re.compile(r"No module named '([\w.]+)'")


def env_flag(tail, patch=""):
    """Short string when the test tail points at the environment, else ''.

    An import the agent's own patch added (the name is on a '+' line) is the agent's error, not the
    environment's."""
    t = tail or ""
    added = "\n".join(l for l in (patch or "").splitlines() if l.startswith("+"))
    for m in MISSING_MOD.finditer(t):
        top = m.group(1).split(".")[0]
        if top not in REPO_TOPS and m.group(1).split(".")[-1] not in added:
            return "missing module %s" % m.group(1)
    m = re.search(r"ImportError: cannot import name '(\w+)' from '([\w.]+)'", t)
    if m and m.group(2).split(".")[0] not in REPO_TOPS and m.group(1) not in added:
        return "cannot import %s from %s" % (m.group(1), m.group(2))
    for pat in (r"VersionConflict", r"requires a different Python", r"fixture '(\w+)' not found",
                r"PytestUnknownMarkWarning", r"pluggy|PluginValidationError", r"No such file or directory: '(/[^']+)'"):
        m = re.search(pat, t)
        if m:
            return m.group(0)[:80]
    return ""


def first_failure_line(tail):
    t = tail or ""
    for line in t.splitlines():
        s = line.strip()
        if s.startswith("E ") and len(s) > 3:
            return s[:160]
    m = re.search(r"(\w+Error[^\n]{0,140})", t)
    return m.group(1) if m else ""


def tail_kind(tail):
    t = tail or ""
    if "SyntaxError" in t or "IndentationError" in t:
        return "syntax error"
    if "ERROR collecting" in t or "error during collection" in t:
        return "collection error"
    if re.search(r"\d+ failed", t):
        return "assertion/test failure"
    if re.search(r"\d+ error", t):
        return "test error"
    if not t.strip():
        return "no tail"
    return "other"


# ---------------------------------------------------------------- main

def load_rows(path):
    rows = collections.OrderedDict()
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            rows[d["instance_id"]] = d
    return rows


def classify(r):
    if r["patch_ref_files"] == 0:
        if r["agent_src_files"] == 0:
            # A failed edit is the primary miss only when a working edit would have landed in time:
            # two or more failed source edits, or one with at least three calls left after it.
            # One last-gasp attempt at the cap is a no-edit draw.
            n = r["n_calls_trace"]
            early = r["first_edit_failure_call"] is not None and r["first_edit_failure_call"] <= n - 3
            if r["edit_failures"] >= 2 or (r["edit_failures"] == 1 and early):
                return "edit-tool failure"
            return "no-edit/empty patch"
        if r["edit_failures_on_ref"] > 0:
            return "edit-tool failure"
        return "wrong file"
    if r["hunks_overlapped"] == 0:
        return "right file wrong region"
    if r["hunks_overlapped"] < r["ref_hunks"]:
        return "partial fix"
    return "all hunks touched, wrong change"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "runs", "_analysis", "trace_vs_reference.jsonl"))
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--show", default=None)
    a = ap.parse_args()

    tasks = load_rows(os.path.join(ROOT, "data", "raw", "tasks.jsonl"))
    ctl = {k: load_rows(os.path.join(ROOT, "runs", k, "task_results.jsonl"))
           for k in ("C-000-gold-all", "C-001-gold-all-shims", "C-000-empty-all", "C-001-empty-all-shims")}
    gold_any = {i for i in tasks if ctl["C-000-gold-all"].get(i, {}).get("resolved")
                or ctl["C-001-gold-all-shims"].get(i, {}).get("resolved")}
    empty_any = {i for i in tasks if ctl["C-000-empty-all"].get(i, {}).get("resolved")
                 or ctl["C-001-empty-all-shims"].get(i, {}).get("resolved")}
    gradeable = gold_any - empty_any
    shim_only = {i for i in gradeable if not ctl["C-000-gold-all"][i]["resolved"]}

    refs = {i: parse_diff(tasks[i]["patch"]) for i in tasks}
    test_files = {i: set(parse_diff(tasks[i]["test_patch"])) for i in tasks}

    out_rows = []
    for rd in sorted(glob.glob(os.path.join(ROOT, "runs", "*"))):
        run = os.path.basename(rd)
        if not re.match(r"^[RSF]-", run):
            continue
        trp = os.path.join(rd, "task_results.jsonl")
        if not os.path.exists(trp):
            continue
        model = "31b" if "-31b-" in run else "e4b" if "-e4b-" in run else "?"
        started = ""
        sp = os.path.join(rd, "summary.json")
        if os.path.exists(sp):
            try:
                started = json.load(open(sp)).get("started_utc") or ""
            except Exception:
                pass
        shims = bool(started) and started >= SHIMS_FROM_UTC
        for iid, row in load_rows(trp).items():
            if iid not in gradeable:
                continue
            ref = refs[iid]
            ref_files = list(ref)
            agent = parse_diff(row.get("patch") or "")
            tp = os.path.join(rd, "traces", "trace_%s.json" % iid)
            if os.path.exists(tp):
                try:
                    tf = analyze_trace(json.load(open(tp)), ref, ref_files)
                    has_trace = True
                except Exception as e:
                    tf = analyze_trace({}, ref, ref_files)
                    has_trace = False
            else:
                tf = analyze_trace({}, ref, ref_files)
                has_trace = False
            # Substantive reference hunks: drop re-wrap / comment-only / import-reorder hunks, unless
            # that would leave nothing.
            subst = []
            for rf, info in ref.items():
                if info["new"]:
                    subst.append((rf, None))
                    continue
                for h, cos in zip(info["hunks"], info["cosmetic"]):
                    if not cos:
                        subst.append((rf, h))
            n_cosmetic = sum(sum(v["cosmetic"]) for v in ref.values() if not v["new"])
            if not subst:
                subst = [(rf, h) for rf, info in ref.items() for h in (info["hunks"] or [None])]
                n_cosmetic = 0
            n_ref_hunks = len(subst)
            overl = 0
            for rf, h in subst:
                ah = agent.get(rf)
                if h is None:
                    overl += 1 if ah else 0
                elif ah and any(near(h, x) for x in ah["hunks"]):
                    overl += 1
            # A new file at the repo root that the reference does not have (repro.py, debug_wrap.py) is a
            # scratch script left in the patch, not an attempt at the fix.
            scratch = [p for p in agent if "/" not in p and agent[p]["new"] and p not in ref]
            agent_src = [p for p in agent if not is_test_path(p) and p not in scratch]
            other_src = [p for p in agent_src if p not in ref]
            agent_tests = [p for p in agent if is_test_path(p)]
            err = row.get("error") or ""
            calls = row.get("tool_calls") or 0
            cap = row.get("max_tool_calls") or 10 ** 9
            if "timeout" in err:
                end = "time cap"
            elif calls >= cap or "tool call budget" in err or tf["budget_exceeded_seen"]:
                end = "call cap"
            elif "turns budget" in err:
                end = "turn cap"
            elif "without calling submit_patch" in err:
                end = "no submit"
            elif err:
                end = "error"
            else:
                end = "submitted"
            r = {
                "run": run, "model": model, "instance_id": iid, "resolved": bool(row.get("resolved")),
                "shims": shims, "has_trace": has_trace,
                "env_confounded_no_shims": (iid in shim_only and not shims),
                "ref_files": len(ref_files), "ref_hunks": n_ref_hunks, "ref_hunks_cosmetic": n_cosmetic,
                "ref_layout": ";".join("%s:%s" % (p, ",".join("%d-%d" % h for h in v["hunks"]) or "new")
                                       for p, v in ref.items()),
                "agent_files": list(agent), "agent_src_files": len(agent_src),
                "patch_ref_files": sum(1 for p in ref if p in agent),
                "hunks_overlapped": overl, "other_src_files": other_src, "agent_test_files": agent_tests,
                "agent_touches_test_patch_file": sorted(set(agent) & test_files[iid]),
                "patch_chars": row.get("patch_chars") or len(row.get("patch") or ""),
                "tool_calls": calls, "max_tool_calls": row.get("max_tool_calls"),
                "duration_s": row.get("duration_s"), "end": end, "error": err[:80],
                "successful_edits": 0,
            }
            r.update(tf)
            r["successful_edits"] = tf["edit_attempts"] - tf["edit_failures"]
            r["successful_source_edits"] = tf["source_edits_ok"]
            tail = row.get("test_tail") or ""
            r["tail_kind"] = tail_kind(tail)
            r["tail_first_E"] = first_failure_line(tail)
            r["env_flag"] = env_flag(tail, row.get("patch") or "")
            r["class"] = None if r["resolved"] else classify(r)
            out_rows.append(r)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as fh:
        for r in out_rows:
            fh.write(json.dumps(r) + "\n")
    print("wrote %d draw rows to %s" % (len(out_rows), a.out))

    if a.show:
        for r in out_rows:
            if r["instance_id"] == a.show:
                print("%-30s res=%d cls=%-28s end=%-9s calls=%s firstedit=%s named=%d read=%d hread=%d/%d "
                      "ov=%d/%d efail=%d %s other=%s test=%d/%d E=%s env=%s" % (
                          r["run"], r["resolved"], r["class"], r["end"], r["tool_calls"], r["first_edit_call"],
                          r["named_ref_before_edit"], r["read_ref_before_edit"], r["ref_hunks_read_before_edit"],
                          r["ref_hunks"], r["hunks_overlapped"], r["ref_hunks"], r["edit_failures"],
                          r["edit_fail_types"], r["other_src_files"], r["test_after_last_edit"],
                          r["test_after_last_edit_pass"], r["tail_first_E"][:90], r["env_flag"]))
    if a.summary:
        summarize(out_rows, gradeable)


def summarize(rows, gradeable):
    for model in ("31b", "e4b"):
        rs = [r for r in rows if r["model"] == model and not r["env_confounded_no_shims"]]
        att = collections.defaultdict(list)
        for r in rs:
            att[r["instance_id"]].append(r)
        never = sorted(i for i, v in att.items() if not any(x["resolved"] for x in v))
        fail = [r for r in rs if not r["resolved"]]
        nfail = [r for r in fail if r["instance_id"] in never]
        print("\n== %s: draws %d, tasks attempted %d, never resolved %d, failing draws %d (on never-resolved %d)"
              % (model, len(rs), len(att), len(never), len(fail), len(nfail)))
        for label, sub in (("never-resolved", nfail), ("all failing", fail)):
            c = collections.Counter(r["class"] for r in sub)
            print("  %s:" % label, ", ".join("%s %d" % (k, c[k]) for k in CLASSES))


if __name__ == "__main__":
    main()
