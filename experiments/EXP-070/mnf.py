#!/usr/bin/env python3
"""EXP-070 check 4a: ModuleNotFoundError for the two test-only packages (inline_snapshot, dirty_equals).

Counts, per run and task, (a) run_command steps whose observation reports ModuleNotFoundError or ImportError
naming either package, with the step's author, the command's programs, the exit code and whether the step comes after
the applier's last applied edit_file of the task (A) or before it (B); and (b) whether the grading test_tail in
task_results names either package next to ModuleNotFoundError or ImportError. The tail is the last part of the
grading output only, so (b) is a lower bound. Prints ids, counts, program names and exit codes only.
Usage: python -I -X utf8 experiments/EXP-070/mnf.py runs/EXP-061-r ...
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "experiments" / "EXP-063"))
import desk as D  # noqa: E402
import refs  # noqa: E402

PKG = ("inline_snapshot", "dirty_equals")
MNF = re.compile(r"(ModuleNotFoundError|ImportError)[^\n]{0,120}?(inline_snapshot|dirty_equals)")


def run_paths(run: Path) -> tuple[Path, Path]:
    for base in (run, run / "runs" / run.name):
        if (base / "traces").is_dir() and any((base / "traces").glob("trace_*.json")):
            return base / "traces", base / "task_results.jsonl"
    raise SystemExit(f"no traces under {run}")


def main(runs: list[str]) -> int:
    for r in runs:
        tdir, res = run_paths(Path(r))
        rows = {json.loads(l)["instance_id"]: json.loads(l) for l in res.read_text(encoding="utf-8").splitlines() if l.strip()}
        tot_obs = tot_tasks = tot_grade = 0
        print(f"=== {Path(r).name}")
        for tp in sorted(tdir.glob("trace_*.json")):
            tid = tp.stem[len("trace_"):]
            steps = json.loads(tp.read_text(encoding="utf-8")).get("steps") or []
            n = 0
            pk: set[str] = set()
            where: list[str] = []
            last_ok = -1
            for i, s in enumerate(steps):
                if s.get("source") == "agent" and D.author(s) == "applier":
                    obs0 = str((s.get("observation") or {}).get("content") or "")
                    for tc in s.get("tool_calls") or []:
                        if str(tc.get("function_name") or tc.get("name") or "") == "edit_file" and refs.args_of(tc) and not refs.failed(obs0):
                            last_ok = i
            for i, s in enumerate(steps):
                names = [str(tc.get("function_name") or tc.get("name") or "") for tc in s.get("tool_calls") or []]
                if "run_command" not in names:
                    continue
                obs = str((s.get("observation") or {}).get("content") or "").replace("\\n", "\n")
                hits = MNF.findall(obs)
                if hits:
                    n += 1
                    pk |= {h[1] for h in hits}
                    progs = "+".join(D.programs({"fn": "run_command", "args": refs.args_of(tc), "obs": ""})[12:-1]
                                     for tc in s.get("tool_calls") or []
                                     if str(tc.get("function_name") or tc.get("name") or "") == "run_command")
                    where.append(f"{D.author(s)}:{progs}:exit {refs.exit_code(obs)}:{'A' if last_ok >= 0 and i > last_ok else 'B'}")
            tail = str(rows.get(tid, {}).get("test_tail") or "").replace("\\n", "\n")
            g = sorted({h[1] for h in MNF.findall(tail)})
            tot_obs += n
            tot_tasks += n > 0
            tot_grade += bool(g)
            print(f"  {tid:15s} run_command obs with MNF {n} pkgs {sorted(pk) or '-'} [{' '.join(where) or '-'}]; grading tail {g or '-'}; "
                  f"resolved {rows.get(tid, {}).get('resolved')}")
        print(f"  RUN obs {tot_obs} tasks {tot_tasks}; grading tails naming a package {tot_grade}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
