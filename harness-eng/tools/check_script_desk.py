"""R-029 desk check (zero GPU): run skills_lib/change-check/scripts/check.py on real snapshots after applying recorded
final patches, and compare its verdict with tools/patch_syntax_desk.py's class. Counts only.
  python3.13 -I tools/check_script_desk.py data/raw <scratch dir> <rows jsonl> <n per class>"""
import collections, json, os, shutil, subprocess, sys, tarfile, time
DATA, SCR, ROWS, N = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
script = os.path.abspath("skills_lib/change-check/scripts/check.py")
rows = [json.loads(l) for l in open(ROWS)]
pick = collections.defaultdict(list)
for r in rows:
    if r["cls"] in ("syntax_error_src", "parses", "empty") and len(pick[r["cls"]]) < N and r["instance_id"] not in {x["instance_id"] for x in pick[r["cls"]]}:
        pick[r["cls"]].append(r)
C = collections.Counter(); secs = []
for cls, rs in pick.items():
    for r in rs:
        tr = {json.loads(l)["instance_id"]: json.loads(l) for l in open(os.path.join(r["run"], "task_results.jsonl"))}
        patch = tr[r["instance_id"]]["patch"]
        d = os.path.join(SCR, "ws"); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        with tarfile.open(f"{DATA}/snapshots/{r['instance_id']}.tgz") as tf:
            tf.extractall(d, filter="data")
        root = d
        if not os.path.isdir(os.path.join(d, ".git")):
            subs = [os.path.join(d, x) for x in os.listdir(d)]
            root = next((s for s in subs if os.path.isdir(os.path.join(s, ".git"))), d)
        time.sleep(1.1)
        if patch:
            subprocess.run(["git", "apply", "--whitespace=nowarn", "-"], cwd=root, input=patch.encode(), capture_output=True)
        t0 = time.time()
        out = subprocess.run([sys.executable, "-I", script], cwd="/", env={"PYTHONPATH": root}, capture_output=True, text=True).stdout.strip()
        secs.append(time.time() - t0)
        v = "syntax" if out.startswith("syntax error") else ("zero" if out == "0" else ("digit" if out.isdigit() else "other"))
        C[(cls, v)] += 1
for k, v in sorted(C.items()):
    print(k, v)
print("median s", round(sorted(secs)[len(secs) // 2], 2), "max s", round(max(secs), 2))
