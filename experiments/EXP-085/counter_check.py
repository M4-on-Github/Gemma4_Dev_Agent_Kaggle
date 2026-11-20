#!/usr/bin/env python3
"""EXP-085 and EXP-086, written 2026-11-20 after the runs (an observation, not a reading): does the harness tool counter
count the agent_tool call and the reader's inner calls? Replaces the 'unaccounted' line of screen_read.py, which is 0 by
construction because the trace carries the reader's inner steps (extra.author == 'file_reader') and trace_counts counts them
as root calls (section 7 of both EXP files).

Per task it prints the harness counter (task_results.jsonl 'tool_calls', the number the budget plugin keeps) against
trace counts split by author: root counted calls (not get_status/submit_patch, not file_reader), file_reader calls (the
agent_tool call, made by the root), reader inner counted calls, and the counts the harness would show under each
hypothesis. It also flags file_reader responses that look like a tool error, and observations carrying a budget refusal.
Prints ids, counts and booleans only (plan.md:52).
Usage: python -I -X utf8 experiments/EXP-085/counter_check.py runs/EXP-085-reader [runs/EXP-086-reader ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

FREE = {"get_status", "submit_patch"}
REFUSAL = ("budget", "exceeded", "limit reached", "no tool calls left")
ERROR = ("error", "exception", "traceback")


def author(x) -> str:
    return ((x or {}).get("extra") or {}).get("author") or ""


def one(rd: Path, tid: str, row: dict) -> dict:
    steps = json.load(open(rd / "traces" / f"trace_{tid}.json", encoding="utf-8")).get("steps") or []
    root = reader = inner = inner_free = refusals = reader_err = 0
    reader_steps = root_steps = 0
    for s in steps:
        if s.get("source") == "agent" and s.get("llm_call_count"):
            if author(s) == "file_reader":
                reader_steps += 1
            else:
                root_steps += 1
        for tc in s.get("tool_calls") or []:
            fn = tc.get("function_name") or tc.get("name")
            by = author(tc)
            if by == "file_reader":
                if fn in FREE:
                    inner_free += 1
                else:
                    inner += 1
            elif fn == "file_reader":
                reader += 1
            elif fn not in FREE:
                root += 1
        obs = s.get("observation") or {}
        content = str(obs.get("content") or "") if isinstance(obs, dict) else ""
        tool = ((obs.get("extra") or {}).get("tool_name") if isinstance(obs, dict) else None) or ""
        head = content[:120].lower()
        if len(content) < 400 and any(m in head for m in REFUSAL):
            refusals += 1
        if tool == "file_reader" and any(m in head[:40] for m in ERROR):
            reader_err += 1
    h = row.get("tool_calls")
    hyp = {"root": root, "root+agent_tool": root + reader, "root+inner": root + inner,
           "root+agent_tool+inner": root + reader + inner}
    return {"harness": h, "max": row.get("max_tool_calls"), "root": root, "file_reader": reader, "inner": inner,
            "inner_free": inner_free, "reader_steps": reader_steps, "refusals": refusals, "reader_err": reader_err,
            "llm_calls": row.get("llm_calls"), "root_steps": root_steps,
            "turns_match": [k for k, v in {"root": root_steps, "root+reader": root_steps + reader_steps}.items()
                            if v == row.get("llm_calls")], "match": [k for k, v in hyp.items() if v == h], "hyp": hyp}


def main() -> int:
    for arg in sys.argv[1:]:
        rd = Path(arg)
        rows = [json.loads(l) for l in open(rd / "task_results.jsonl", encoding="utf-8") if l.strip()]
        print(f"== {rd.name}")
        print("  id | harness tool_calls (max) | root, file_reader, reader inner (inner free) | reader model steps | "
              "refusal obs | file_reader error-like | llm_calls | hypotheses equal to harness")
        tally: dict[str, int] = {}
        rtally: dict[str, int] = {}
        nr = 0
        for row in rows:
            tid = row.get("instance_id") or row.get("task_id")
            r = one(rd, tid, row)
            for k in r["match"]:
                tally[k] = tally.get(k, 0) + 1
            if r["file_reader"] >= 1:
                nr += 1
                for k in r["match"]:
                    rtally[k] = rtally.get(k, 0) + 1
            print(f"  {tid:16s} | {r['harness']} ({r['max']}) | {r['root']}, {r['file_reader']}, {r['inner']} ({r['inner_free']}) | "
                  f"{r['reader_steps']} | {r['refusals']} | {r['reader_err']} | {r['llm_calls']} (root steps {r['root_steps']}, turns = {','.join(r['turns_match']) or 'neither'}) | {','.join(r['match']) or 'none'} "
                  f"{r['hyp']}")
        n = len(rows)
        keys = ("root", "root+agent_tool", "root+inner", "root+agent_tool+inner")
        print(f"  tasks where each hypothesis equals the harness counter (of {n}): " + "; ".join(f"{k} {tally.get(k, 0)}" for k in keys))
        print(f"  the same over tasks with at least one file_reader call (of {nr}): " + "; ".join(f"{k} {rtally.get(k, 0)}" for k in keys))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
