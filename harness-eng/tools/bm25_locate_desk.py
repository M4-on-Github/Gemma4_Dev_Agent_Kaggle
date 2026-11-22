"""R-027 desk check (zero GPU): can BM25 over a snapshot's source files, queried with the issue text, rank the gold
patch's source files near the top? Writes per-task ranks to a gitignored JSONL (task ids stay out of git) and prints
counts only.

  python3.13 -I tools/bm25_locate_desk.py data/raw runs/_desk/bm25_ranks.jsonl
"""
import json, math, re, sys, tarfile, collections

DATA, OUT = sys.argv[1], sys.argv[2]
F = re.compile(r"^(?:diff --git a/(\S+) b/|\+\+\+ b/(\S+))", re.M)
TST = re.compile(r"(^|/)(tests?|testing|docs_src|docs|scripts|\.github|examples?|benchmarks?)/|test_[^/]*\.py$|_test\.py$|conftest\.py$")
WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
IDENT = re.compile(r"`([^`\n]{2,60})`|\b([A-Za-z_]\w*(?:\.\w+)+|[a-z]+_\w+|[A-Z][a-z]+[A-Z]\w*)\b")
STOP = set("the a an and or of to in is it be this that for on with as are was not by if from at but we can when use used using have has which".split())


def toks(text):
    out = []
    for w in WORD.findall(text):
        lw = w.lower()
        if len(lw) > 2 and lw not in STOP:
            out.append(lw)
        parts = [p.lower() for p in re.split(r"_|(?<=[a-z0-9])(?=[A-Z])", w) if len(p) > 2]
        if len(parts) > 1:
            out.extend(p for p in parts if p not in STOP)
    return out


def gold_src(p):
    return {f for a, b in F.findall(p or "") for f in [a or b] if f != "/dev/null" and f.endswith(".py") and not TST.search(f)}


def rank(task):
    t = tarfile.open(f"{DATA}/snapshots/{task['instance_id']}.tgz")
    docs = {}
    for m in t:
        if not m.isfile() or not m.name.endswith(".py"):
            continue
        rel = m.name[2:] if m.name.startswith("./") else m.name
        if rel.startswith(".git/") or TST.search(rel) or m.size > 400_000:
            continue
        txt = t.extractfile(m).read().decode("utf-8", "replace")
        docs[rel] = collections.Counter(toks(txt) + toks(rel.replace("/", " ").replace(".py", "")) * 3)
    N = len(docs) or 1
    df = collections.Counter(w for c in docs.values() for w in c)
    avg = sum(sum(c.values()) for c in docs.values()) / N
    ps = task["problem_statement"]
    queries = {"full": ps, "ident": " ".join(a or b for a, b in IDENT.findall(ps)), "head400": ps[:400]}
    out = {}
    for mode, qtext in queries.items():
        out[mode] = score(docs, N, df, avg, collections.Counter(toks(qtext)), gold_src(task["patch"]))
    return {"instance_id": task["instance_id"], "n_files": len(docs), "gold": len(gold_src(task["patch"])),
            "best_rank": out["full"], "by_mode": out}


def score(docs, N, df, avg, q, g):
    scores = {}
    for rel, c in docs.items():
        L = sum(c.values()); s = 0.0
        for w, qn in q.items():
            if w in c:
                idf = math.log(1 + (N - df[w] + 0.5) / (df[w] + 0.5))
                s += idf * c[w] * 2.2 / (c[w] + 1.2 * (0.25 + 0.75 * L / avg))
        scores[rel] = s
    order = sorted(scores, key=lambda r: -scores[r])
    ranks = sorted(order.index(f) + 1 for f in g if f in scores and scores[f] > 0)
    return ranks[0] if ranks else None


rows = []
with open(OUT, "w") as fh:
    for line in open(f"{DATA}/tasks.jsonl"):
        r = rank(json.loads(line)); rows.append(r); fh.write(json.dumps(r) + "\n")
print("tasks", len(rows), "median files", sorted(r["n_files"] for r in rows)[len(rows) // 2])
for mode in ("full", "ident", "head400"):
    b = [r["by_mode"][mode] for r in rows]
    print(mode, "gold found", sum(x is not None for x in b), {f"top{k}": sum(bool(x and x <= k) for x in b) for k in (1, 3, 5, 10)})
