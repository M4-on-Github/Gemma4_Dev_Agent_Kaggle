"""Keep the fastest complete resolved trajectories per task from a trace_to_sft.py file (L-005, 2026-11-21).

  python3 -I tools/lora/select_fast.py --in /data/mmyatmau/gemma4-lora/data/d2/31b-all-lfold-a.jsonl \
      --out /data/mmyatmau/gemma4-lora/data/d2/31b-fast-lfold-a.jsonl --per-task 8 --max-calls 20

A row is kept when its trajectory ends at the first submit_patch response (meta.end == "complete"), it was not made
without thinking (run name without "nothoughts"), and it has at most --max-calls LLM calls. Per task, rows are sorted
by LLM calls, then run name, and the first --per-task are kept, so the choice is deterministic and favours the
shortest solves. Rows hold trace text, so the output stays under /data/mmyatmau/gemma4-lora (plan.md:52). Stdout
carries counts only.
"""
import argparse
import collections
import json
import statistics


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--per-task", type=int, default=8)
    p.add_argument("--max-calls", type=int, default=20)
    a = p.parse_args()
    rows = [json.loads(l) for l in open(a.inp)]
    why = collections.Counter()
    by = collections.defaultdict(list)
    for r in rows:
        m = r.get("meta") or {}
        if m.get("end") != "complete":
            why["drop_not_complete"] += 1
        elif "nothoughts" in m.get("run", ""):
            why["drop_nothoughts"] += 1
        elif m.get("llm_calls", 10 ** 9) > a.max_calls:
            why["drop_over_max_calls"] += 1
        else:
            by[m["instance_id"]].append(r)
    keep = []
    for iid in sorted(by):
        g = sorted(by[iid], key=lambda r: (r["meta"]["llm_calls"], r["meta"]["run"]))
        why["drop_over_per_task"] += max(0, len(g) - a.per_task)
        keep.extend(g[: a.per_task])
    with open(a.out, "w") as f:
        for r in keep:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    calls = [r["meta"]["llm_calls"] for r in keep]
    per = collections.Counter(r["meta"]["instance_id"] for r in keep)
    print(json.dumps({
        "rows_in": len(rows), "rows_out": len(keep), "tasks_out": len(per),
        "rows_per_task": sorted(per.values()), "drops": dict(why),
        "llm_calls": {"min": min(calls), "median": statistics.median(calls), "max": max(calls)} if calls else None,
    }))


if __name__ == "__main__":
    main()
