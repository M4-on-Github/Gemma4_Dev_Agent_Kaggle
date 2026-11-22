"""R-027 mechanism (reported, not a gate): per draw, the miss classes (resolved / no source edit / touched a gold
source file / wrong files only) and, for the arms, how many tasks' submitted source files include a file the
locate line named and how many touched a gold file that the line named. Counts only.
  python3.13 -I tools/locate_mech.py <label> <run dir glob> [<label> <glob> ...]"""
import collections, glob, json, re, sys
T = {json.loads(l)["instance_id"]: json.loads(l) for l in open("data/raw/tasks.jsonl")}
F = re.compile(r"^(?:diff --git a/(\S+) b/|\+\+\+ b/(\S+))", re.M)
TST = re.compile(r"(^|/)(tests?|testing|docs_src|docs)/|test_[^/]*\.py$|_test\.py$|conftest\.py$")
LST = re.compile(r"best first: (.*?)\.?\s*$", re.S)


def src(p):
    return {f for a, b in F.findall(p or "") for f in [a or b] if f != "/dev/null" and not TST.search(f)}


def listed(run, iid):
    try:
        st = json.load(open(f"{run}/traces/trace_{iid}.json"))["steps"]
    except (OSError, ValueError):
        return None
    for s in st:
        for c in s.get("tool_calls") or []:
            if c["function_name"] == "run_skill_script" and (c.get("arguments") or {}).get("skill_name") == "locate":
                try:
                    out = str(json.loads((s.get("observation") or {}).get("content") or "{}").get("stdout", ""))
                except (ValueError, AttributeError):
                    continue
                m = LST.search(out.strip())
                if m:
                    return {x.strip() for x in m.group(1).split(",") if x.strip()}
    return None


for label, pat in zip(sys.argv[1::2], sys.argv[2::2]):
    runs = sorted(glob.glob(pat)); c = collections.Counter()
    for run in runs:
        for l in open(run + "/task_results.jsonl"):
            x = json.loads(l); iid = x["instance_id"]; g = src(T[iid]["patch"]); a = src(x.get("patch"))
            k = "resolved" if x["resolved"] else "no_src_edit" if not a else "touched_gold" if g & a else "wrong_files"
            c[k] += 1
            L = listed(run, iid)
            if L is not None:
                c["list_printed"] += 1
                c["gold_in_list"] += bool(g & L)
                c["edited_a_listed_file"] += bool(a & L)
                c["edited_gold_from_list"] += bool(a & g & L)
    n = len(runs) or 1
    print(label, "draws", len(runs), {k: round(v / n, 2) for k, v in sorted(c.items())})
