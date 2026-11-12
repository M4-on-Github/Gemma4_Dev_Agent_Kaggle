#!/usr/bin/env python3
"""EXP-079 desk check, part 2 (zero GPU): can the file-list search recipe clear the D-011 endpoint rule?

For each base draw (EXP-038, EXP-077; EXP-077 is the out-of-sample draw, the recipe was chosen on EXP-038):
  miss      tasks whose gold path is not shown before the first edit (desk.py shown_path n)
  reach     misses with at least one qualifying search (EXP-076 trunc.py: a search before the first edit whose
            pattern is quoted from the issue and is a literal substring of a gold source file at the base commit)
  list_ok   reach tasks where the file-list form of one such search would name a gold file within 5000 characters
            (trunc.list_ok); split by whether every qualifying search was scoped to non-gold paths (needs a change
            of scope the recipe does not ask for) or not (the recipe alone suffices)
  bound     misses where any search before the first edit (any pattern of 3 or more characters that a gold file
            holds, quoted from the issue or not, any scope) would name a gold file in list form: the upper bound at
            full uptake
Then the paired shown_path table EXP-038 against EXP-077 and the threshold arithmetic of the D-011 rule
(keep beyond the larger of the base-draw gap and two reference SDs), over all 48 and over the fixed id set.
Prints ids, counts and labels only.
Usage: python -I -X utf8 experiments/EXP-079/ceiling.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for d in ("EXP-074", "EXP-063", "EXP-075", "EXP-076"):
    sys.path.insert(0, str(ROOT / "experiments" / d))
import diag  # noqa: E402
import noise  # noqa: E402
import refs  # noqa: E402
import trunc  # noqa: E402
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("desk79", ROOT / "experiments" / "EXP-079" / "desk.py")
D79 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(D79)  # the EXP-079 counter; a plain import finds EXP-076 desk.py

D76 = trunc.D
BS = chr(92)
BASES = D79.BASES


def qualifying(rd: Path, tid: str, task: dict, any_pattern: bool = False) -> list[tuple[str, bool]]:
    """(cause, list_ok) per qualifying search before the first edit. any_pattern: drop the quoted-from-the-issue
    condition and keep every search pattern of 3 or more characters that a gold file holds (the upper bound)."""
    gf = list(diag.gold_regions(task["patch"], 5))
    ps = task.get("problem_statement") or ""
    snap = diag.snapshot(tid)
    gt = [v for k, v in snap.items() if any(diag.same_file(k, x) for x in gf)]
    steps = json.load(open(rd / "traces" / f"trace_{tid}.json", encoding="utf-8"))["steps"]
    out, edited = [], False
    for s in steps:
        if s.get("source") != "agent":
            continue
        obs = str((s.get("observation") or {}).get("content") or "")
        for tc in s.get("tool_calls") or []:
            fn = tc.get("function_name") or tc.get("name")
            if fn in ("edit_file", "write_file"):
                edited = True
            if fn != "run_command" or edited:
                continue
            cmd = str(refs.args_of(tc).get("command") or "")
            _, pat = D76.search_pattern(cmd)
            if pat is None or not (any_pattern or D76.in_issue(pat, ps)):
                continue
            lit = pat.replace(BS, "")
            if len(lit) < 3 or not any(lit in v for v in gt):
                continue
            shows = any(x in obs for x in gf) or any(Path(x).name in obs for x in gf)
            why = "shows" if shows else trunc.cause(cmd, pat, obs, gf)
            out.append((why, trunc.list_ok(lit, snap, gf)[1]))
    return out


def main() -> int:
    tasks = {json.loads(x)["instance_id"]: json.loads(x) for x in open(ROOT / "data/raw/tasks.jsonl", encoding="utf-8")}
    fixed = D79.fixed_default(tasks)
    shown = {}
    for run in BASES:
        rd = noise.run_dir(run)
        cls = noise.classes(run, tasks)
        sp = {}
        miss, reach, alone, scope, bound = [], [], [], [], []
        for tid in sorted(cls):
            gf = list(diag.gold_regions(tasks[tid]["patch"], 5))
            sp[tid] = D79.task(rd, tid, gf)["shown_path"]
            if sp[tid]:
                continue
            miss.append(tid)
            if any(ok for _, ok in qualifying(rd, tid, tasks[tid], any_pattern=True)):
                bound.append(tid)
            q = qualifying(rd, tid, tasks[tid])
            if not q:
                continue
            reach.append(tid)
            if any(ok and c != "scoped_other" for c, ok in q):
                alone.append(tid)
            elif any(ok for c, ok in q):
                scope.append(tid)
        shown[run] = sp
        print(f"{run}: miss {len(miss)}/48; with a qualifying search {len(reach)}; list_ok by the recipe alone "
              f"{len(alone)} {alone}; list_ok only with a wider scope {len(scope)} {scope}")
        print(f"   misses in the fixed set {sum(t in fixed for t in miss)}/{len(fixed)}; recipe-alone misses in it "
              f"{sum(t in fixed for t in alone)}")
        print(f"   upper bound (any search pattern a gold file holds, list form, any scope): {len(bound)} {bound}; "
              f"in the fixed set {sum(t in fixed for t in bound)}")
    a, b = shown[BASES[0]], shown[BASES[1]]
    ids = sorted(a)
    for name, sel in (("all 48", ids), (f"fixed {len(fixed)}", fixed)):
        n = len(sel)
        ka, kb = sum(a[t] for t in sel), sum(b[t] for t in sel)
        yn = sum(a[t] and not b[t] for t in sel)
        ny = sum(b[t] and not a[t] for t in sel)
        p = (ka + kb) / (2 * n)
        gap = abs(ka - kb)
        sd_one = math.sqrt(2 * n * p * (1 - p))            # one arm draw against one base draw, binomial
        sd_pool = math.sqrt(2 * (2 * n) * p * (1 - p)) / 2  # two pooled against two pooled, per-draw units
        sd_pair = math.sqrt(yn + ny)                        # paired: discordant base pairs as the flip reference
        thr_pool = max(gap, 2 * sd_pool)
        thr_one = max(gap, 2 * sd_one)
        print(f"{name}: EXP-038 {ka}/{n}, EXP-077 {kb}/{n}, pooled mean {(ka + kb) / 2:.1f} per draw (p {p:.3f}); "
              f"gap {gap}; paired flips 038-only {yn}, 077-only {ny} (sqrt {sd_pair:.2f})")
        print(f"   two reference SDs, per-draw units: one draw against one {2 * sd_one:.2f}; two pooled against two "
              f"{2 * sd_pool:.2f}")
        print(f"   keep threshold (per-draw mean of the arm above the base mean by more than): pooled design "
              f"{thr_pool:.2f} -> arm mean above {(ka + kb) / 2 + thr_pool:.2f} of {n}; one draw {thr_one:.2f} -> "
              f"above {(ka + kb) / 2 + thr_one:.2f}; room to the ceiling {n - (ka + kb) / 2:.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
