"""R-027 check (zero GPU): run skills_lib/locate/scripts/rank.py on every snapshot, unpacked to a scratch dir, with
the issue's first 400 characters as the query. Counts only: gold source file in the printed list, list length,
seconds per task. Usage: python3.13 -I tools/locate_check.py data/raw <scratch dir> <top>"""
import json, os, re, runpy, shutil, sys, tarfile, time, io, contextlib
DATA, SCR, TOP = sys.argv[1], sys.argv[2], int(sys.argv[3])
F = re.compile(r"^(?:diff --git a/(\S+) b/|\+\+\+ b/(\S+))", re.M)
TST = re.compile(r"(^|/)(tests?|testing|docs_src|docs)/|test_[^/]*\.py$|_test\.py$|conftest\.py$")
script = os.path.abspath("skills_lib/locate/scripts/rank.py")
hit = n = empty = 0; secs = []
for line in open(f"{DATA}/tasks.jsonl"):
    t = json.loads(line)
    g = {f for a, b in F.findall(t["patch"]) for f in [a or b] if f != "/dev/null" and f.endswith(".py") and not TST.search(f)}
    d = os.path.join(SCR, "ws"); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    with tarfile.open(f"{DATA}/snapshots/{t['instance_id']}.tgz") as tf:
        tf.extractall(d, members=[m for m in tf if m.name.endswith(".py") or m.name.startswith("./.git/HEAD") or m.name == "./.git"], filter="data")
    os.makedirs(os.path.join(d, ".git"), exist_ok=True)
    sys.argv = [script, t["problem_statement"][:400]]; old = sys.path[:]; sys.path.insert(0, d)
    buf = io.StringIO(); t0 = time.time()
    with contextlib.redirect_stdout(buf):
        g_ = runpy.run_path(script, init_globals=None, run_name="__x__"); g_["TOP"] = TOP
        g_["rank"].__globals__["TOP"] = TOP; g_["main"]()
    secs.append(time.time() - t0); sys.path[:] = old
    out = buf.getvalue()
    n += 1; empty += "best first" not in out; hit += any(f in out for f in g)
print(f"top{TOP}: tasks {n}, gold listed {hit}, plain request {empty}, median s {sorted(secs)[len(secs)//2]:.2f}, max s {max(secs):.2f}")
