#!/usr/bin/env python3
"""EXP-080 section 6.1 follow-up (zero GPU, added after results, defect 12): split the E4B task-draws that leave arm R's
path at class E (empty patch) by what the run attempted. For each such run: did it issue any edit_file or write_file
call on a gold source file (any outcome), on other files only, or none; and did any change call on a gold file succeed
(refs.failed). Prints ids and counts only.
Usage: python -I -X utf8 experiments/EXP-080/e_split.py
"""
from __future__ import annotations

import collections
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.argv = sys.argv[:1]
import items as I  # noqa: E402
import part1 as P  # noqa: E402

diag = I.diag
refs = I.refs
noise = I.noise


def main() -> int:
    T = I.tasks()
    ref = noise.classes(P.REF, T)
    cl = {d: noise.classes(d, T) for d in P.DRAWS}
    tot = collections.Counter()
    for d in P.DRAWS:
        c = collections.Counter()
        for t in sorted(ref):
            if P.stage(cl[d][t]) != "E" or P.rank(cl[d][t]) >= P.rank(ref[t]):
                continue
            gold = list(diag.gold_regions(T[t]["patch"], 5).keys())
            att_gold = att_other = ok_gold = 0
            for s in I.steps_of(d, t):
                for tc in s.get("tool_calls") or []:
                    if I.fn_of(tc) not in I.CHANGE:
                        continue
                    a = refs.args_of(tc) or {}
                    path = str(a.get("filepath") or a.get("path") or a.get("file_path") or "")
                    on_gold = any(diag.same_file(path, g) for g in gold) if path else False
                    if on_gold:
                        att_gold += 1
                        ok_gold += 0 if refs.failed(I.obs_of(s)) else 1
                    else:
                        att_other += 1
            key = ("gold file attempted, one succeeded" if ok_gold else
                   "gold file attempted, all failed" if att_gold else
                   "other files only" if att_other else "no change call")
            c[key] += 1
            print(f"   {d:18s} {t:15s} armR {ref[t]} -> E: {key} (gold {att_gold}, ok {ok_gold}, other {att_other})")
        tot.update(c)
        print(f"{d}: leaves at E {sum(c.values())}: " + "; ".join(f"{k} {v}" for k, v in sorted(c.items())))
    print(f"four draws, leaves at E {sum(tot.values())}: " + "; ".join(f"{k} {v}" for k, v in sorted(tot.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
