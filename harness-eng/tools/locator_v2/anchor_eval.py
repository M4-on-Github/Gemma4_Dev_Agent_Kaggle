"""Ceiling of the audit step (zero GPU): given a TRUE changed symbol, how many of the fix's other symbols does
trees/31b-map/skills/codemap/scripts/audit.py list among its related sites?

Usage (from harness-eng/, after `eval_locator.py prepare`):
  env/py313-scorer/bin/python3.13 -I -W ignore tools/locator_v2/anchor_eval.py --scratch <dir> \
      --cohort cohorts/A.txt [--frozen runs/_analysis/trace_vs_reference.frozen.jsonl --runs runs]

Tasks whose reference fix touches >= 2 gold symbols (gold as in eval_locator.py). Three anchorings:
  each   every gold symbol in turn is the one anchor; the others are the targets.
  first  the symbol of the reference patch's first changed line is the anchor.
  draft  (with --frozen) the anchors are the symbols a failing 31B "partial fix" patch really changed; the targets
         are the gold symbols that patch did not touch.
recall = targets listed in the top 10 related sites / targets; precision = listed sites that are targets / listed.
"task mean" averages inside a task first, so a few very large fixes do not dominate; "pooled" sums everything.
Prints counts and rates only; no task id, path or code.
"""
import argparse
import collections
import json
import os
import runpy
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import eval_locator as EV  # noqa: E402

AUDIT = os.path.join(HERE, "..", "..", "trees", "31b-map", "skills", "codemap", "scripts", "audit.py")


def find_def(repo, key):
    for d in repo.parsed(key[0]):
        if d["start"] == key[1] and d["end"] == key[2]:
            return d
    return None


def score(mod, repo, anchors, targets, gsyms):
    """(targets hit, targets, sites that are targets, sites listed)."""
    mod["related"].__globals__["T0"] = time.time()
    sites = [(x["file"], x["start"], x["end"]) for x, _ in mod["related"](repo, anchors)]
    hit = sum(EV.covers(sites, k, gsyms[k]) for k in targets)
    good = sum(any(EV.covers([s], k, gsyms[k]) for k in targets) for s in sites)
    return hit, len(targets), good, len(sites)


class Agg:
    def __init__(self):
        self.tasks, self.pool, self.any_hit, self.all_hit, self.listed = [], [0, 0, 0, 0], 0, 0, 0

    def add(self, rows):
        if not rows:
            return
        rec = sum(h / t for h, t, _, _ in rows if t) / max(sum(1 for r in rows if r[1]), 1)
        with_sites = [r for r in rows if r[3]]
        prec = sum(g / n for _, _, g, n in with_sites) / len(with_sites) if with_sites else None
        self.tasks.append((rec, prec))
        for r in rows:
            for i in range(4):
                self.pool[i] += r[i]
        self.any_hit += any(r[0] for r in rows)
        self.all_hit += all(r[0] == r[1] for r in rows)
        self.listed += bool(with_sites)

    def line(self, name):
        n = len(self.tasks)
        if not n:
            return "%s: n=0" % name
        precs = [p for _, p in self.tasks if p is not None]
        h, t, g, s = self.pool
        return ("%s: n=%d | recall task mean %.3f, pooled %d/%d (%.3f) | precision task mean %.3f, pooled %d/%d "
                "(%.3f) | units with any site listed %d, with >=1 target listed %d, with all targets listed %d" % (
                    name, n, sum(r for r, _ in self.tasks) / n, h, t, h / max(t, 1),
                    sum(precs) / max(len(precs), 1), g, s, g / max(s, 1), self.listed, self.any_hit, self.all_hit))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--data", default="data/raw")
    ap.add_argument("--cohort", action="append", default=[])
    ap.add_argument("--frozen")
    ap.add_argument("--runs", default="runs")
    args = ap.parse_args()
    ids = EV.read_cohort(args.cohort)
    tasks = EV.load_tasks(args.data, ids)
    drafts = collections.defaultdict(list)          # task -> failing 31B partial-fix patches
    if args.frozen and os.path.isfile(args.frozen):
        want = collections.defaultdict(set)
        with open(args.frozen) as fh:
            for line in fh:
                d = json.loads(line)
                if d.get("model") == "31b" and d.get("class") == "partial fix" and d["instance_id"] in tasks:
                    want[d["run"]].add(d["instance_id"])
        for run, tids in want.items():
            path = os.path.join(args.runs, run, "task_results.jsonl")
            if os.path.isfile(path):
                with open(path) as fh:
                    for line in fh:
                        r = json.loads(line)
                        if r.get("instance_id") in tids and r.get("patch"):
                            drafts[r["instance_id"]].append(r["patch"])
    each, first, draft, draft_each = Agg(), Agg(), Agg(), Agg()
    secs, skipped = [], 0
    for tid in ids:
        ws = os.path.join(args.scratch, "ws", tid)
        gfiles, gsyms, _ = EV.gold_of(tasks[tid], ws)
        if len(gsyms) < 2:
            continue
        mod = runpy.run_path(AUDIT, run_name="__audit__")
        mod["related"].__globals__["T0"] = time.time()
        repo = mod["Repo"](ws)
        gdefs = {k: find_def(repo, k) for k in gsyms}
        keys = [k for k in gsyms if gdefs[k] is not None]
        if len(keys) < 2:
            skipped += 1
            continue
        rows = []
        for k in keys:
            t0 = time.time()
            rows.append(score(mod, repo, [gdefs[k]], [o for o in gsyms if o != k], gsyms))
            secs.append(time.time() - t0)
        each.add(rows)
        first.add(rows[:1])
        if tid in drafts:
            drows = []
            for patch in drafts[tid]:
                anchors = []
                for f, sites in EV.changed_lines(patch).items():
                    if not f.endswith(".py") or EV.TST.search(f) or f not in repo.idents:
                        continue
                    defs = [d for d in repo.parsed(f)]
                    for lo, hi in sites:
                        inner = None
                        for d in defs:
                            if d["start"] <= lo and hi <= d["end"] and (
                                    inner is None or d["end"] - d["start"] < inner["end"] - inner["start"]):
                                inner = d
                        if inner is not None and all(inner is not a for a in anchors):
                            anchors.append(inner)
                done = [(a["file"], a["start"], a["end"]) for a in anchors]
                targets = [k for k in gsyms if not EV.covers(done, k, gsyms[k])
                           and not any(k[0] == f and k[1] <= e and s <= k[2] for f, s, e in done)]
                if anchors and targets:
                    drows.append(score(mod, repo, anchors[:6], targets, gsyms))
            for r in drows:
                draft.add([r])
            draft_each.add(drows)
    print("== cohort %s | audit related sites, top 10" % ",".join(os.path.basename(c) for c in args.cohort))
    print("tasks with >=2 gold symbols used: %d (skipped, gold not resolvable: %d)" % (len(each.tasks), skipped))
    print(each.line("each gold symbol as anchor (unit = task)"))
    print(first.line("first hunk's symbol as anchor (unit = task)"))
    if args.frozen:
        print(draft.line("31B partial-fix drafts, real changed symbols as anchors (unit = draw)"))
        print(draft_each.line("same (unit = task)"))
    secs.sort()
    if secs:
        print("seconds per anchor: median %.2f, max %.2f" % (secs[len(secs) // 2], secs[-1]))


if __name__ == "__main__":
    main()
