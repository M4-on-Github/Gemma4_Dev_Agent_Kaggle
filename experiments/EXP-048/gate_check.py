"""EXP-048 section 6 decode gate: the EXP-047 adapter decode rate against the E4B's per-task spare.

Run as: python -I -X utf8 experiments/EXP-048/gate_check.py <EXP-047 v2 run dir> <EXP-038 summary.jsonl> <out dir>

Reads the boot-1 decode probes (`kind == "decode"`) of the EXP-047 canary v2 and the EXP-038 per-task rows.
Writes two scaled copies of the EXP-038 rows into <out dir> for tools/estimate_budget.py --results:
  decode_component.jsonl  wall_s + output_tokens x (1/tok_s_adapter - 1/tok_s_base)   (decode time only)
  whole_wall.jsonl        wall_s x tok_s_base / tok_s_adapter                         (every second slowed)
and prints the per-task figures against D-006's spare (311 s mean budget per task) and the 480 s cap.
Prints counts and seconds only; nothing from a trace.
"""
import json
import statistics
import sys
from pathlib import Path

BUDGET_MEAN_S = 311.0   # D-006 line 42: (10.5 h - 0.12 h kernel overhead) / 120
OVERHEAD_S = 445.6      # EXP-038 E7: measured kernel overhead outside the tasks (E7 = mean x 120 / 3600 + 445.6 s)
CAP_S = 480.0           # max_time_minutes 8 in experiments/EXP-033/candidate-e4b/eval_config.yaml

run_dir, summary, out_dir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
out_dir.mkdir(parents=True, exist_ok=True)

probes = [json.loads(l) for l in (run_dir / "probes.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
dec = [p for p in probes if p.get("kind") == "decode" and p.get("status") == 200 and p.get("tok_s")]
base = [p["tok_s"] for p in dec if p["label"] in ("base", "base_repeat")]
adap = [p["tok_s"] for p in dec if p["label"].startswith("canary_")]
tb, ta = statistics.mean(base), statistics.mean(adap)
ratio = tb / ta
print(f"decode probes: base n={len(base)} mean {tb:.2f} tok/s; adapter n={len(adap)} mean {ta:.2f} tok/s")
print(f"adapter decode drop {100 * (1 - ta / tb):.1f}%; seconds per token x {ratio:.4f}")

rows = [json.loads(l) for l in summary.read_text(encoding="utf-8").splitlines() if l.strip()]
walls = [r["wall_s"] for r in rows]
toks = [r.get("output_tokens") or 0 for r in rows]
extra = [t * (1 / ta - 1 / tb) for t in toks]
dc = [w + e for w, e in zip(walls, extra)]
ww = [w * ratio for w in walls]
n_calls = [r.get("n_calls") or 0 for r in rows]
print(f"EXP-038 rows {len(rows)}: mean wall {statistics.mean(walls):.1f} s, max {max(walls):.1f} s, "
      f"mean output tokens {statistics.mean(toks):.0f}, max {max(toks)}, mean calls {statistics.mean(n_calls):.1f}")
print(f"spare at the unchanged tree: {BUDGET_MEAN_S - statistics.mean(walls):.1f} s per task")
for name, xs in (("decode component", dc), ("whole-wall bound", ww)):
    add = statistics.mean(xs) - statistics.mean(walls)
    print(f"{name}: mean {statistics.mean(xs):.1f} s (+{add:.1f} s, {100 * add / (BUDGET_MEAN_S - statistics.mean(walls)):.1f}% "
          f"of the spare), spare left {BUDGET_MEAN_S - statistics.mean(xs):.1f} s; max task {max(xs):.1f} s "
          f"against the {CAP_S:.0f} s cap; tasks over the cap {sum(x > CAP_S for x in xs)}")
for name, xs in (("unchanged tree", walls), ("decode component", dc), ("whole-wall bound", ww)):
    print(f"E7-style projection, {name}: {statistics.mean(xs) * 120 / 3600 + OVERHEAD_S / 3600:.2f} h against 10.5 h")
print(f"decode component per task: mean +{statistics.mean(extra):.1f} s, max +{max(extra):.1f} s")

for fname, xs in (("decode_component.jsonl", dc), ("whole_wall.jsonl", ww)):
    with open(out_dir / fname, "w", encoding="utf-8", newline="\n") as f:
        for r, x in zip(rows, xs):
            f.write(json.dumps({"task_id": r["task_id"], "wall_s": round(x, 2), "setup_s": r.get("setup_s"),
                                "n_calls": r.get("n_calls"), "output_tokens": r.get("output_tokens"),
                                "resolved": r.get("resolved"), "time_cap_hit": r.get("time_cap_hit")}) + "\n")
print(f"wrote {out_dir / 'decode_component.jsonl'} and {out_dir / 'whole_wall.jsonl'}")
