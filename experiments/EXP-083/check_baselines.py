"""Check a re-downloaded baseline run against its committed summary.jsonl (EXP-083/084, 2026-11-20).
Match = same task ids, same resolved flag per task, |wall_s difference| <= 0.5 s per task. Also compares
patch emptiness and n_calls (reported, not part of the match). Prints ids and counts only."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAIRS = {
    "EXP-028-armR": "experiments/EXP-028/armR/summary.jsonl",
    "EXP-028-armRH": "experiments/EXP-028/armRH/summary.jsonl",
    "EXP-038-e4b-dev48": "experiments/EXP-038/e4b/summary.jsonl",
    "EXP-075-t02": "experiments/EXP-075/summary.jsonl",
    "EXP-077-base": "experiments/EXP-077/summary.jsonl",
    "EXP-078-t02r": "experiments/EXP-078/summary.jsonl",
}


def load(p):
    out = {}
    for l in open(p, encoding="utf-8"):
        if l.strip():
            r = json.loads(l)
            out[r.get("task_id") or r.get("task") or r.get("instance_id")] = r
    return out


ok_all = True
for run in (sys.argv[1:] or PAIRS):
    new, old = load(ROOT / "runs" / run / "summary.jsonl"), load(ROOT / PAIRS[run])
    ids_same = set(new) == set(old)
    common = sorted(set(new) & set(old))
    res_diff = [t for t in common if bool(new[t]["resolved"]) != bool(old[t]["resolved"])]
    wall_diff = [t for t in common if abs(float(new[t]["wall_s"]) - float(old[t]["wall_s"])) > 0.5]
    empty_diff = [t for t in common if bool(new[t]["patch_empty"]) != bool(old[t]["patch_empty"])]
    calls_diff = [t for t in common if new[t]["n_calls"] != old[t]["n_calls"]]
    ok = ids_same and not res_diff and not wall_diff
    ok_all &= ok
    print(f"{run}: tasks new {len(new)} committed {len(old)} ids_same {ids_same}; resolved new {sum(bool(new[t]['resolved']) for t in new)} "
          f"committed {sum(bool(old[t]['resolved']) for t in old)}; resolved mismatches {len(res_diff)} {','.join(res_diff)}; "
          f"wall mismatches {len(wall_diff)} {','.join(wall_diff)}; empty mismatches {len(empty_diff)}; n_calls mismatches {len(calls_diff)} -> {'MATCH' if ok else 'NO MATCH'}")
print("all match" if ok_all else "NOT all match")
