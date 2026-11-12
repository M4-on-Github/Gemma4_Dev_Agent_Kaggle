#!/usr/bin/env python3
"""EXP-075 section 1 desk check (zero GPU): why the E4B's EXP-038 dev-48 empties are empty.

Prints ids, counts, class names, ratios and line counts only (hygiene rule: no file text, no command arguments other
than a path, no model messages).

Per edit_file call, the harness outcome class from the tool observation:
  ok         the edit applied
  notfound   "old_string not found" (all four match strategies failed)
  multi      "occurs N times" / "matches N locations" / "Expected 1 occurrence"
  same       old_string equals new_string
  argloss    "mandatory input parameters are not present"
  nofile     the file does not exist (FileNotFoundError, or a path error)
  other      any other error
For a notfound call, the old_string is compared with the base-commit copy of the target file (the snapshot):
  lines_in   share of its non-blank lines that occur in the file (whitespace-stripped)
  contig     its stripped non-blank lines occur as one contiguous run of the file's stripped non-blank lines
  escaped    it holds a literal backslash-n or backslash-quote sequence
  where      'file' (most lines in the target), 'other' (the target lacks them, another snapshot file holds most),
             'none' (no snapshot file holds most of them)
  read_before / reread  the target file was read (read_file on it) before this call / since the previous failed
             edit on it
  repeat     the arguments equal those of the previous edit_file call
Mechanism endpoint line (section 3 of EXP-075): over the tasks printed, edit_file calls by outcome, notfound share,
identical repeats, tasks with an edit_file call, tasks whose first edit_file call applied, empty patches.
Usage: python -I -X utf8 experiments/EXP-075/desk.py [--all] [--run RUN-NAME]   (default run EXP-038-e4b-dev48)
"""
from __future__ import annotations

import collections
import difflib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "EXP-074"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-063"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-075"))
import diag  # noqa: E402
import noise  # noqa: E402
import refs  # noqa: E402

RUN = ROOT / "runs" / "EXP-038-e4b-dev48"
E_IDS = ["fastapi_13537", "fastapi_13786", "fastapi_14360", "fastapi_14459", "fastapi_14873", "fastapi_15661",
         "rich_3063", "rich_3676", "rich_3935", "rich_4075"]


def cls(obs: str) -> str:
    if refs.ARG_LOSS in obs:
        return "argloss"
    if not refs.failed(obs):
        return "ok"
    if "old_string not found" in obs:
        return "notfound"
    if "occurs " in obs and " times" in obs or "matches " in obs and "locations" in obs or "Expected 1 occurrence" in obs:
        return "multi"
    if "are identical" in obs:
        return "same"
    if "not found in workspace" in obs or "FileNotFoundError" in obs or "No such file" in obs \
            or "outside" in obs or "does not exist" in obs:
        return "nofile"
    return "other"


def strip_lines(t: str) -> list[str]:
    return [x.strip() for x in t.split("\n") if x.strip()]


def find_file(snap: dict[str, str], fp: str) -> str | None:
    fp = diag.norm_path(fp)
    for k in snap:
        if diag.same_file(k, fp):
            return k
    return None


def compare(old: str, fp: str, snap: dict[str, str]) -> dict:
    ol = strip_lines(old)
    out = {"n_lines": len(ol), "escaped": ("\\n" in old) or ('\\"' in old)}
    key = find_file(snap, fp)
    if not ol:
        return out | {"lines_in": None, "contig": False, "where": "none", "file_lines": None}
    if key is None:
        best = max(snap, key=lambda k: sum(1 for x in ol if x in set(strip_lines(snap[k])))) if snap else None
        share = sum(1 for x in ol if best and x in set(strip_lines(snap[best]))) / len(ol)
        return out | {"lines_in": None, "contig": False, "where": "other" if share >= 0.5 else "none",
                      "file_lines": None}
    fl = strip_lines(snap[key])
    fs = set(fl)
    share = sum(1 for x in ol if x in fs) / len(ol)
    joined = "\n".join(fl)
    contig = "\n".join(ol) in joined
    where = "file"
    # missing lines: closest file line by difflib ratio (>= 0.85 is a near-copy: a typo, a dropped token)
    miss = [x for x in ol if x not in fs]
    near = 0
    for x in miss:
        cand = difflib.get_close_matches(x, fl, n=1, cutoff=0.85)
        near += bool(cand)
    # present lines in file order: count gaps where the old_string skips file lines between two of its lines
    pos, gaps, start = [], 0, 0
    for x in ol:
        if x in fs:
            try:
                i = fl.index(x, start)
            except ValueError:
                i = fl.index(x)
            pos.append(i)
            start = i + 1
    gaps = sum(1 for a, b in zip(pos, pos[1:]) if b != a + 1)
    out |= {"miss": len(miss), "near": near, "gaps": gaps}
    if share < 0.5:
        other = max((sum(1 for x in ol if x in set(strip_lines(v))) / len(ol)) for k, v in snap.items() if k != key)
        where = "other" if other >= 0.5 else "none"
    return out | {"lines_in": round(share, 2), "contig": contig, "where": where,
                  "file_lines": snap[key].count("\n") + 1}


def task(tid: str) -> dict:
    steps = json.load(open(RUN / "traces" / f"trace_{tid}.json", encoding="utf-8")).get("steps") or []
    snap = diag.snapshot(tid)
    reads: list[tuple[int, str]] = []
    edits = []
    seq = 0
    last_edit_args = None
    kinds = []
    for s in steps:
        if s.get("source") != "agent":
            continue
        obs = str((s.get("observation") or {}).get("content") or "")
        tcs = s.get("tool_calls") or []
        for tc in tcs:
            seq += 1
            fn = str(tc.get("function_name") or tc.get("name") or "")
            ar = refs.args_of(tc)
            kinds.append(fn)
            if fn == "read_file":
                reads.append((seq, diag.norm_path(str(ar.get("filepath") or ""))))
            if fn != "edit_file":
                continue
            fp = str(ar.get("filepath") or "")
            c = cls(obs) if len(tcs) == 1 else cls(obs)  # one observation per step; E4B steps hold one call
            prev_fail = next((e for e in reversed(edits) if e["cls"] != "ok" and diag.same_file(e["file"], fp)), None)
            rb = any(diag.same_file(p, fp) for q, p in reads if q < seq)
            rr = prev_fail is not None and any(diag.same_file(p, fp) and q > prev_fail["seq"] for q, p in reads)
            e = {"seq": seq, "file": diag.norm_path(fp), "cls": c, "read_before": rb, "reread": rr,
                 "repeat": ar == last_edit_args, "multi_calls_in_step": len(tcs)}
            if c == "notfound":
                e |= compare(str(ar.get("old_string") or ""), fp, snap)
            else:
                key = find_file(snap, fp)
                e["file_lines"] = snap[key].count("\n") + 1 if key else None
            edits.append(e)
            last_edit_args = ar
    return {"edits": edits, "kinds": kinds}


def main() -> int:
    global RUN
    all_tasks = "--all" in sys.argv
    if "--run" in sys.argv:
        RUN = noise.run_dir(sys.argv[sys.argv.index("--run") + 1])
    summ = {d["task_id"]: d for d in diag.jl(RUN / "summary.jsonl")}
    ids = sorted(summ) if all_tasks else E_IDS
    tot = collections.Counter()
    nf = collections.Counter()
    per_task_dom = collections.Counter()
    for tid in ids:
        t = task(tid)
        s = summ[tid]
        ed = t["edits"]
        c = collections.Counter(e["cls"] for e in ed)
        tot.update(c)
        fails = [e for e in ed if e["cls"] != "ok"]
        dom = c.most_common(1)[0][0] if fails else ("no-edit-call" if not ed else "ok-only")
        if fails:
            dom = collections.Counter(e["cls"] for e in fails).most_common(1)[0][0]
        per_task_dom[dom] += 1
        files = sorted({e["file"] for e in ed})
        flines = sorted({e.get("file_lines") for e in ed if e.get("file_lines")})
        print(f"{tid}: empty {s['patch_empty']} resolved {s['resolved']} wall {s['wall_s']} calls {s['n_calls']} "
              f"submit {s['submit_patch_called']} capT {s['time_cap_hit']} capC {s['calls_cap_hit']} "
              f"tool_free {s.get('tool_free')} edits {len(ed)} {dict(c)} dominant {dom} "
              f"files {files} file_lines {flines} write_file {t['kinds'].count('write_file')} "
              f"read_file {t['kinds'].count('read_file')}")
        for e in ed:
            extra = ""
            if e["cls"] == "notfound":
                nf["n"] += 1
                nf["contig"] += e["contig"]
                nf["escaped"] += e["escaped"]
                nf[f"where_{e['where']}"] += 1
                nf["read_before"] += e["read_before"]
                nf["reread"] += e["reread"]
                nf["repeat"] += e["repeat"]
                if e["lines_in"] is not None:
                    nf["all_lines_in"] += e["lines_in"] == 1.0
                    nf["most_lines_in"] += 0.5 <= e["lines_in"] < 1.0
                extra = (f" lines {e['n_lines']} lines_in {e['lines_in']} contig {e['contig']} escaped {e['escaped']}"
                         f" where {e['where']} miss {e.get('miss')} near {e.get('near')} gaps {e.get('gaps')}")
                nf["miss_lines"] += e.get("miss") or 0
                nf["near_lines"] += e.get("near") or 0
                nf["with_gap"] += bool(e.get("gaps"))
            print(f"   #{e['seq']} {e['cls']} {e['file']} read_before {e['read_before']} reread {e['reread']} "
                  f"repeat {e['repeat']}{extra}")
    print("totals edit_file outcome:", dict(tot))
    print("tasks by dominant failed-edit class:", dict(per_task_dom))
    print("notfound detail:", dict(nf))
    mech = collections.Counter()
    for tid in ids:
        ed = task(tid)["edits"]
        mech["tasks"] += 1
        mech["empty"] += bool(summ[tid]["patch_empty"])
        mech["resolved"] += bool(summ[tid]["resolved"])
        mech["with_edit_call"] += bool(ed)
        mech["first_edit_applied"] += bool(ed) and ed[0]["cls"] == "ok"
        mech["edit_calls"] += len(ed)
        mech["notfound"] += sum(e["cls"] == "notfound" for e in ed)
        mech["failed"] += sum(e["cls"] != "ok" for e in ed)
        mech["repeat"] += sum(e["repeat"] for e in ed)
        mech["nonrepeat_calls"] += sum(not e["repeat"] for e in ed)
        mech["nonrepeat_notfound"] += sum((not e["repeat"]) and e["cls"] == "notfound" for e in ed)
    share = round(mech["notfound"] / mech["edit_calls"], 3) if mech["edit_calls"] else None
    nr = mech["nonrepeat_calls"]
    share_nr = round(mech["nonrepeat_notfound"] / nr, 3) if nr else None
    print(f"mechanism {RUN.name}: {dict(mech)} notfound_share {share} notfound_share_nonrepeat {share_nr}")
    walls = [summ[t]["wall_s"] for t in ids]
    print(f"wall median {statistics.median(walls)} max {max(walls)} over {len(ids)} tasks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
