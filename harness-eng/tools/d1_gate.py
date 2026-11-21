"""Apply a round's pre-registered draw-1 kill gates to one finished run (counts only).

  python3 -I tools/d1_gate.py runs/<RUN> <expected rows> GATE [GATE ...]

GATE is `<field><op><value>` with op one of >=, <=, >, <, on a field of tools/round_counts.py's JSON, plus
`callcap` (rows with 28 or more reported tool calls). Prints the counts, then `PASS` or `KILL <gates that fired>`,
and exits 0 on PASS, 1 on KILL, 2 when the run is incomplete (fewer rows than expected): an incomplete draw is
reported, never read as a pass. Examples (2026-11-21):
  R-016 d1: resolved<=24 mean_wall>368.5 empty>=23 timecap>=27 compacted>2
  R-017 d1: resolved<=3 empty>=23 timecap>=7 compacted>2
  L-006 a2 d1: callcap>=20
"""
import json
import operator
import re
import subprocess
import sys
from pathlib import Path

OPS = {">=": operator.ge, "<=": operator.le, ">": operator.gt, "<": operator.lt}


def main():
    run, expected, gates = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
    here = Path(__file__).resolve().parent
    out = subprocess.check_output([sys.executable, "-I", str(here / "round_counts.py"), run],
                                  universal_newlines=True)  # system python3 is 3.6 here
    c = json.loads(out)
    rows = [json.loads(x) for x in open(Path(run) / "task_results.jsonl")]
    c["callcap"] = sum((r.get("tool_calls") or 0) >= 28 for r in rows)
    print(json.dumps(c))
    if c["rows"] < expected:
        print(f"INCOMPLETE {c['rows']} of {expected} rows")
        return 2
    fired = []
    for g in gates:
        m = re.fullmatch(r"(\w+)(>=|<=|>|<)([-\d.]+)", g)
        if not m:
            raise SystemExit(f"bad gate {g}")
        field, op, val = m.group(1), m.group(2), float(m.group(3))
        if OPS[op](float(c.get(field, 0)), val):
            fired.append(f"{g} (value {c.get(field, 0)})")
    print("KILL " + "; ".join(fired) if fired else "PASS")
    return 1 if fired else 0


if __name__ == "__main__":
    sys.exit(main())
