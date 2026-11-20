"""Split a cohort into two LoRA folds (A: train, B: evaluate), stratified by repo and by base solve rates.

  python3 tools/lora/make_folds.py --cohort cohorts/cdev2-79.txt --name lfold \
      --e4b runs/R-011-e4b-base-tu5-d{1..8} --b31 runs/R-008-31b-base-te-d{1,2} runs/R-011-31b-base-te-d{3,4}

Within each repo, tasks are ordered by (E4B base resolves, 31B base resolves, sha1 of the id) and assigned in
snake order A B B A A B B A ..., so both folds get the same mix of easy and hard tasks and the result does not
depend on file order. Writes cohorts/<name>-a.txt and cohorts/<name>-b.txt (ids only) and prints balance counts.
"""
import argparse
import collections
import hashlib
import json
import os


def ids(path):
    return [l.split()[0] for l in open(path) if l.strip() and not l.startswith("#")]


def resolves(runs, keep):
    c = collections.Counter()
    for run in runs:
        for line in open(os.path.join(run, "task_results.jsonl")):
            r = json.loads(line)
            if r["instance_id"] in keep and r.get("resolved"):
                c[r["instance_id"]] += 1
    return c


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cohort", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--e4b", nargs="+", required=True)
    p.add_argument("--b31", nargs="+", required=True)
    a = p.parse_args()
    tasks = ids(a.cohort)
    keep = set(tasks)
    e4, b31 = resolves(a.e4b, keep), resolves(a.b31, keep)
    by_repo = collections.defaultdict(list)
    for t in tasks:
        by_repo[t.rsplit("_", 1)[0]].append(t)
    folds = {"a": [], "b": []}
    snake = "abba"
    for repo in sorted(by_repo):
        order = sorted(by_repo[repo], key=lambda t: (e4[t], b31[t], hashlib.sha1(t.encode()).hexdigest()))
        for i, t in enumerate(order):
            folds[snake[i % 4]].append(t)
    stats = {}
    for f, ts in folds.items():
        stats[f] = {"tasks": len(ts),
                    "per_repo": dict(collections.Counter(t.rsplit("_", 1)[0] for t in ts)),
                    "e4b_base_resolves": sum(e4[t] for t in ts), "e4b_tasks_ever_solved": sum(e4[t] > 0 for t in ts),
                    "b31_base_resolves": sum(b31[t] for t in ts), "b31_tasks_ever_solved": sum(b31[t] > 0 for t in ts)}
    src = os.path.basename(a.cohort)
    for f, ts in folds.items():
        with open(os.path.join("cohorts", f"{a.name}-{f}.txt"), "w") as fo:
            role = "train (LoRA fold A)" if f == "a" else "evaluate (LoRA fold B)"
            fo.write(f"# {a.name}-{f}: {len(ts)} ids, {role}. Split of {src} by tools/lora/make_folds.py "
                     f"(repo x E4B {len(a.e4b)} draws x 31B {len(a.b31)} draws, snake order). "
                     f"E4B base resolves {stats[f]['e4b_base_resolves']}, 31B base resolves "
                     f"{stats[f]['b31_base_resolves']}.\n")
            fo.write("\n".join(ts) + "\n")
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
