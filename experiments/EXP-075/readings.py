"""EXP-075 / EXP-077 reading inputs that no other script prints (added 2026-11-12, before any result).

For one run it prints:
  infra   row 1 inputs: task_results rows, rows with llm_calls 0, rows with n_turns 0, cap-string rows,
          no-submit endings with turns, other non-empty errors, and the infrastructure-error total
          (llm_calls 0 or n_turns 0, or an error that is neither a cap string nor a no-submit ending with turns)
  h7      n_identical_repeats summed over the tasks, and the number of tasks at 8 or more
  m       notfound and edit_file calls (desk.task), the share
  h1      of the 5 EXP-038 resolves, the ids lost (gross)
With --rerun NAME (the EXP-077 run) it also prints the rerun's lost ids, the net ids (lost in the run, held
in the rerun), and s = |M(rerun) - M(EXP-038)| from unrounded call counts.
Prints ids, counts and fixed harness labels only.
Usage: python -I -X utf8 experiments/EXP-075/readings.py RUN-NAME [--rerun RUN-NAME]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "EXP-075"))
import desk  # noqa: E402
import noise  # noqa: E402

BASE = "EXP-038-e4b-dev48"
RESOLVED_5 = ["fastapi_14301", "fastapi_14463", "requests_6644", "rich_3006", "rich_3905"]
CAP_PREFIXES = ("Agent exceeded session timeout", "Agent exceeded turns budget")
NO_SUBMIT = "Agent completed execution without calling submit_patch."


def jl(p: Path) -> list[dict]:
    return [json.loads(line) for line in open(p, encoding="utf-8") if line.strip()]


def mech(name: str) -> tuple[int, int]:
    desk.RUN = noise.run_dir(name)
    summ = {d["task_id"]: d for d in jl(desk.RUN / "summary.jsonl")}
    nf = calls = 0
    for tid in sorted(summ):
        ed = desk.task(tid)["edits"]
        calls += len(ed)
        nf += sum(e["cls"] == "notfound" for e in ed)
    return nf, calls


def lost(name: str) -> list[str]:
    summ = {d["task_id"]: d for d in jl(noise.run_dir(name) / "summary.jsonl")}
    return [t for t in RESOLVED_5 if not (summ.get(t) or {}).get("resolved")]


def report(name: str) -> None:
    rd = noise.run_dir(name)
    tr = jl(rd / "task_results.jsonl")
    summ = {d["task_id"]: d for d in jl(rd / "summary.jsonl")}
    c = {"rows": len(tr), "llm_calls_0": 0, "n_turns_0": 0, "cap": 0, "no_submit_with_turns": 0, "other_error": 0,
         "infra_errors": 0}
    infra_ids = []
    for r in tr:
        tid = r.get("instance_id")
        err = str(r.get("error") or "")
        turns = (summ.get(tid) or {}).get("n_turns")
        zero_calls = r.get("llm_calls") == 0
        zero_turns = turns == 0
        c["llm_calls_0"] += zero_calls
        c["n_turns_0"] += zero_turns
        is_cap = err.startswith(CAP_PREFIXES)
        is_ns = err == NO_SUBMIT and (turns or 0) > 0
        c["cap"] += bool(err) and is_cap
        c["no_submit_with_turns"] += bool(err) and is_ns
        other = bool(err) and not is_cap and not is_ns
        c["other_error"] += other
        if zero_calls or zero_turns or other:
            c["infra_errors"] += 1
            infra_ids.append(tid)
    print(f"infra {rd.name}: {c} ids {infra_ids}")
    rep = [int((d.get("n_identical_repeats") or 0)) for d in summ.values()]
    print(f"h7 {rd.name}: n_identical_repeats_total {sum(rep)} tasks_at_8_or_more {sum(x >= 8 for x in rep)} "
          f"max_one_task {max(rep) if rep else None}")
    nf, calls = mech(name)
    print(f"m {rd.name}: notfound {nf} edit_calls {calls} share {nf / calls if calls else None}")
    print(f"h1 {rd.name}: gross_lost {len(lost(name))} ids {lost(name)}")


def main() -> int:
    name = sys.argv[1]
    report(name)
    if "--rerun" in sys.argv:
        rr = sys.argv[sys.argv.index("--rerun") + 1]
        a, r = lost(name), lost(rr)
        net = [t for t in a if t not in r]
        print(f"h1 rerun {rr}: lost {len(r)} ids {r}; net_lost {len(net)} ids {net}")
        nf_b, c_b = mech(BASE)
        nf_r, c_r = mech(rr)
        mb, mr = nf_b / c_b, nf_r / c_r
        print(f"s: M({rr}) {nf_r}/{c_r} = {mr} M({BASE}) {nf_b}/{c_b} = {mb} s {abs(mr - mb)} "
              f"falls_threshold {0.340 - 2 * abs(mr - mb)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
