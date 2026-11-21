"""Offline selector simulation over repeated draws of one tree (counts only; never prints patch text).

  python3.13 -I tools/select_sim.py runs/<D1> runs/<D2> ... [--k 2 3]

For each K and each combination of K draws, every task gets K candidate patches (one per draw). A selector picks
one; the task counts as resolved if the picked draw resolved it. Reports expected resolves per draw (averaged over
combinations) for: oracle (pass@K), random (pass@1), and the shippable rules below. Similarity between two patches
is Jaccard over their sets of changed lines (whitespace-stripped '+'/'-' lines, file headers dropped).
"""
import argparse, itertools, json, os, statistics

p = argparse.ArgumentParser(); p.add_argument("runs", nargs="+"); p.add_argument("--k", type=int, nargs="+", default=[2, 3])
a = p.parse_args()
D = [{json.loads(l)["instance_id"]: json.loads(l) for l in open(os.path.join(r, "task_results.jsonl"))} for r in a.runs]
T = sorted(set.intersection(*[set(d) for d in D]))

def lines(pt):
    out = set()
    for ln in (pt or "").splitlines():
        if ln.startswith(("+++", "---")): continue
        if ln[:1] in "+-" and ln[1:].strip(): out.add(ln[0] + ln[1:].strip())
    return frozenset(out)

def files(pt):
    return frozenset(ln[6:] for ln in (pt or "").splitlines() if ln.startswith("+++ b/"))

def src_only(pt):  # drop hunks in test files (graded tests are reset)
    keep, cur = [], True
    for ln in (pt or "").splitlines():
        if ln.startswith("diff --git"):
            path = ln.split(" b/")[-1]
            cur = not ("/tests/" in "/" + path or os.path.basename(path).startswith("test_") or path.endswith("_test.py") or "conftest" in path)
        if cur: keep.append(ln)
    return "\n".join(keep)

C = {t: [(lines(src_only(d[t]["patch"])), files(src_only(d[t]["patch"])), bool(d[t]["resolved"])) for d in D] for t in T}

def jac(x, y):
    return len(x & y) / len(x | y) if (x or y) else 1.0

def sel_medoid(c):  # nonempty candidate with the highest summed similarity to the others; ties -> first
    ne = [i for i, x in enumerate(c) if x[0]]
    if not ne: return 0
    return max(ne, key=lambda i: (sum(jac(c[i][0], c[j][0]) for j in ne if j != i), -i))

def sel_file_vote(c):  # nonempty candidate whose file set is most common; ties -> smallest patch, then first
    ne = [i for i, x in enumerate(c) if x[0]]
    if not ne: return 0
    return max(ne, key=lambda i: (sum(c[j][1] == c[i][1] for j in ne), -len(c[i][0]), -i))

def sel_first_nonempty(c):
    return next((i for i, x in enumerate(c) if x[0]), 0)

def sel_smallest(c):
    ne = [i for i, x in enumerate(c) if x[0]]
    return min(ne, key=lambda i: (len(c[i][0]), i)) if ne else 0

RULES = {"first_nonempty": sel_first_nonempty, "medoid": sel_medoid, "file_vote": sel_file_vote, "smallest": sel_smallest}
print(json.dumps({"tasks": len(T), "draws": len(D)}))
for k in a.k:
    combos = list(itertools.combinations(range(len(D)), k)); res = {}
    for name, f in [("oracle", None), ("random", None)] + list(RULES.items()):
        tot = []
        for cb in combos:
            s = 0
            for t in T:
                c = [C[t][i] for i in cb]
                if name == "oracle": s += any(x[2] for x in c)
                elif name == "random": s += sum(x[2] for x in c) / k
                else: s += c[f(c)][2]
            tot.append(s)
        res[name] = round(statistics.mean(tot), 2)
    print(json.dumps({"k": k, "combos": len(combos), **res}))
