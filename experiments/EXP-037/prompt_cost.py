"""EXP-037 zero-GPU cost of the inserted text, measured from arms on disk.

1. Tokens per byte of system-prompt text: for every dev-48 task present in both arms of a pair whose system
   prompts differ only in length, (first agent step prompt_tokens, arm 2) - (same, arm 1), divided by the
   byte difference of the two system_instruction messages. Pairs: R -> RH (RH = R + a 942-char section, same
   tree otherwise) and R -> A25 (a different 12.8 KB prompt). Median over tasks.
2. Headroom to the 14,336-token compaction threshold in Arm R: per task the peak prompt_tokens over agent
   steps; how many tasks peak below the threshold but within D tokens of it, for the D values given, on the
   given id lists. A task in that band would cross the threshold at least once more if every prompt grew by D.
Counts only.  Run as:
  python -I -X utf8 experiments/EXP-037/prompt_cost.py --ids experiments/cohorts/gated-8.txt --delta 700 1300 \
      --out experiments/EXP-037/prompt_cost.json
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

ARMS = {
    "R": "runs/EXP-028-armR",
    "RH": "runs/EXP-028-armRH",
    "A25": "runs/exp025_armA/runs/EXP-025-editfix-dev48-armA-baseline",
}
THRESHOLD = 14336


def trace(arm, t):
    p = Path(ARMS[arm]) / "traces" / f"trace_{t}.json"
    return json.load(open(p, encoding="utf-8")) if p.exists() else None


def sys_bytes(tr):
    for s in tr.get("steps", []):
        if (s.get("extra") or {}).get("event_type") == "system_instruction":
            return len(str(s.get("message") or "").encode("utf-8"))
    return None


def agent_prompts(tr):
    return [s["metrics"]["prompt_tokens"] for s in tr.get("steps", [])
            if s.get("source") == "agent" and isinstance(s.get("metrics"), dict) and s["metrics"].get("prompt_tokens")]


def ids_of(path):
    return [l.strip() for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev48", default="experiments/cohorts/dev-48.txt")
    ap.add_argument("--ids", required=True)
    ap.add_argument("--delta", type=int, nargs="+", required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    dev = ids_of(a.dev48)
    sub = ids_of(a.ids)

    out = {"threshold": THRESHOLD, "tokens_per_byte": {}, "headroom_R": {}}
    for a1, a2 in (("R", "RH"), ("R", "A25")):
        ratios, dbytes = [], set()
        for t in dev:
            x, y = trace(a1, t), trace(a2, t)
            if not x or not y:
                continue
            bx, by = sys_bytes(x), sys_bytes(y)
            px, py = agent_prompts(x), agent_prompts(y)
            if not (bx and by and px and py) or bx == by:
                continue
            dbytes.add(by - bx)
            ratios.append((py[0] - px[0]) / (by - bx))
        out["tokens_per_byte"][f"{a1}->{a2}"] = {
            "n_tasks": len(ratios), "system_bytes_diff": sorted(dbytes),
            "median": round(statistics.median(ratios), 4) if ratios else None,
            "min": round(min(ratios), 4) if ratios else None, "max": round(max(ratios), 4) if ratios else None,
        }

    for name, ids in (("dev48", dev), ("subset", sub)):
        peaks = {}
        for t in ids:
            tr = trace("R", t)
            p = agent_prompts(tr) if tr else []
            if p:
                peaks[t] = max(p)
        res = {"n_tasks": len(peaks), "peak_at_or_above_threshold": sum(v >= THRESHOLD for v in peaks.values()),
               "first_prompt_tokens_median": None}
        firsts = [agent_prompts(trace("R", t))[0] for t in peaks]
        res["first_prompt_tokens_median"] = statistics.median(firsts) if firsts else None
        for d in a.delta:
            band = sorted(t for t, v in peaks.items() if THRESHOLD - d <= v < THRESHOLD)
            res[f"newly_reach_with_+{d}"] = len(band)
            if name == "subset":
                res[f"newly_reach_with_+{d}_ids"] = band
        if name == "subset":
            res["peaks"] = {t: peaks[t] for t in sorted(peaks)}
        out["headroom_R"][name] = res
    a.out.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
