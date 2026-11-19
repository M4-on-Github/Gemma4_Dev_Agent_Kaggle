"""Per-stage counts for SequentialAgent runs (R-011 reviewer endpoints). Standard library, Python 3.6+.

  python3 -I tools/stage_counts.py runs/<RUN> [runs/<RUN> ...]

Per run: task-draws with a step by each author, accepted edit/write calls per author, calls to a tool the
author does not have (e.g. the editor calling submit_patch), and resolved counts split by whether the
reviewer edited. A call is "accepted" when its observation carries no error. Counts only; no trace text
is printed.
"""
import collections
import glob
import json
import os
import sys

EDITS = {"edit_file", "write_file"}


def obs_error(obs):
    # Same failure test as ../tools/analyze_traces.py:236-238 (status-error envelope, or the bare missing-argument
    # error), plus ADK's fixed message for a tool the agent does not have.
    c = str((obs or {}).get("content") if isinstance(obs, dict) else "")
    return ('"status": "error"' in c or '\\"status\\": \\"error\\"' in c
            or "mandatory input parameters are not present" in c or "not found. Available tools" in c)


def run(rd):
    res = {}
    tr = os.path.join(rd, "task_results.jsonl")
    if os.path.exists(tr):
        for line in open(tr):
            if line.strip():
                r = json.loads(line)
                res[r.get("instance_id") or r.get("task_id")] = bool(r.get("resolved"))
    c = collections.Counter()
    for f in sorted(glob.glob(os.path.join(rd, "traces", "*.json"))):
        tid = os.path.basename(f)[len("trace_"):-len(".json")]
        steps = json.load(open(f)).get("steps") or []
        authors = set()
        edited = collections.Counter()
        for s in steps:
            a = (s.get("extra") or {}).get("author") or s.get("source")
            authors.add(a)
            for tc in s.get("tool_calls") or []:
                name = tc.get("function_name") or tc.get("name") or ""
                bad = obs_error(s.get("observation"))
                if name in EDITS and not bad:
                    edited[a] += 1
                if name == "submit_patch" and a == "editor":
                    c["editor_submit_calls"] += 1
        c["task_draws"] += 1
        for a in authors:
            c["has_" + str(a)] += 1
        rev = edited.get("reviewer", 0) > 0
        c["reviewer_edited"] += rev
        c["resolved"] += res.get(tid, False)
        c["resolved_when_reviewer_edited"] += rev and res.get(tid, False)
    return c


if __name__ == "__main__":
    for rd in sys.argv[1:]:
        print(os.path.basename(rd.rstrip("/")), dict(sorted(run(rd).items())))
