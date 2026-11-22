"""Desk check (zero GPU): how often a final patch leaves a changed Python file that does not parse, and how such
task-draws resolve. Applies each recorded patch to the changed files of the task's snapshot in a scratch dir
(`git apply`, desk side only), then runs the builtin compile() on each changed .py file before and after.
Counts only; never prints code, paths or ids.
  python3.13 -I tools/patch_syntax_desk.py data/raw <scratch dir> <label> <run dir> [<run dir> ...] [-- <label> ...]"""
import collections, json, os, re, shutil, subprocess, sys, tarfile, warnings
warnings.simplefilter("ignore")   # compile() warnings name repository files; never print them
DATA, SCR = sys.argv[1], sys.argv[2]
F = re.compile(r"^diff --git a/(\S+) b/(\S+)", re.M)
groups, cur = [], None
for a in sys.argv[3:]:
    if a == "--":
        cur = None
    elif cur is None:
        cur = [a, []]; groups.append(cur)
    else:
        cur[1].append(a)


def check(iid, patch):
    files = sorted({b for a, b in F.findall(patch)})
    d = os.path.join(SCR, "ws"); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    for f, b in CACHE[iid].items():
        if f in files and ".." not in f.split("/") and not f.startswith("/"):
            os.makedirs(os.path.dirname(os.path.join(d, f)) or d, exist_ok=True); open(os.path.join(d, f), "wb").write(b)
    before = {}
    for f in files:
        p = os.path.join(d, f)
        if f.endswith(".py") and os.path.exists(p):
            try:
                compile(open(p, "rb").read(), f, "exec"); before[f] = True
            except (SyntaxError, ValueError):
                before[f] = False
    r = subprocess.run(["git", "apply", "--unsafe-paths", "--whitespace=nowarn", "-"], cwd=d, input=patch.encode(),
                       capture_output=True)
    if r.returncode:
        return "no_apply"
    bad = False; bad_src = False
    for f in files:
        p = os.path.join(d, f)
        if f.endswith(".py") and os.path.exists(p) and before.get(f, True):
            try:
                compile(open(p, "rb").read(), f, "exec")
            except (SyntaxError, ValueError):
                bad = True; bad_src |= not is_test(f)
    return "syntax_error_src" if bad_src else ("syntax_error_test_only" if bad else "parses")


def is_test(path):   # as trees/e4b-r020-retry/skills/change-count/scripts/count.py (the grader's test paths)
    parts = path.split("/"); name = parts[-1]
    return (name == "conftest.py" or (name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py")))
            or any(p in ("tests", "test", "testing") for p in parts[:-1]))


rows = [(label, run, json.loads(line)) for label, runs in groups for run in runs
        for line in open(os.path.join(run, "task_results.jsonl"))]
need = collections.defaultdict(set)
for _, _, r in rows:
    if r.get("patch"):
        need[r["instance_id"]] |= {b for a, b in F.findall(r["patch"])}
CACHE = {}   # instance -> {path: bytes}, read once per snapshot
for iid, files in need.items():
    want = {"./" + f for f in files} | files; CACHE[iid] = {}
    with tarfile.open(f"{DATA}/snapshots/{iid}.tgz") as tf:
        for m in tf:
            if m.isfile() and m.name in want:
                CACHE[iid][m.name[2:] if m.name.startswith("./") else m.name] = tf.extractfile(m).read()
res = {}
for label, run, r in rows:
    res[(run, r["instance_id"])] = check(r["instance_id"], r["patch"]) if r.get("patch") else "empty"
os.makedirs("runs/_desk", exist_ok=True)
with open("runs/_desk/patch_syntax_rows.jsonl", "w") as fh:   # gitignored: ids allowed here only
    for (run, iid), k in res.items():
        fh.write(json.dumps({"run": run, "instance_id": iid, "cls": k}) + "\n")
for label, runs in groups:
    C = collections.Counter(); Rv = collections.Counter()
    for run in runs:
        for line in open(os.path.join(run, "task_results.jsonl")):
            r = json.loads(line)
            k = res[(run, r["instance_id"])]
            C[k] += 1; Rv[k] += bool(r["resolved"])
    n = len(runs)
    print(label, "draws", n, {k: (round(C[k] / n, 2), round(Rv[k] / n, 2)) for k in sorted(C)}, "(per draw: task-draws, resolved)")
