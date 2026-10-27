#!/usr/bin/env python3
"""Export a per-task metrics CSV that is safe to publish alongside the paper.

Why this exists
---------------
`plan.md:52` fixes the redistribution rule: competition data (tasks.jsonl, repos, graphs,
wheelhouse) must never be redistributed, and **our traces contain repo snippets**, so the
traces themselves stay out of git and out of any release. What may be published is
"aggregated CSVs / sanitized excerpts". This script is the only sanctioned path from a run
directory to a publishable file, so the rule is enforced by code rather than by memory.

What it emits, and why each field is safe
-----------------------------------------
Every column is a metric, a count, or a public identifier:

* counts and timings            -- numbers, no content
* ``repo``                      -- a public OSS project name (fastapi/fastapi, Textualize/rich, ...)
* ``task_id``                   -- an id only. ``experiments/cohorts/dev-48.txt`` already records
                                   the project's position that ids alone are not competition data,
                                   and these map to public GitHub issue numbers.
* ``error``                     -- harness-generated text (e.g. "Agent exceeded session timeout"),
                                   not task or repo content.
* ``tool_histogram``            -- per-tool call counts, flattened to one column per tool.

DROPPED, deliberately:

* ``trace``                     -- a local filesystem path. Useless to a reader and the one field
                                   that could carry a directory name.
* anything not on the allowlist -- the allowlist is positive, so a new field added upstream is
                                   excluded until someone reviews it here. Fails loudly instead of
                                   leaking by default.

Usage
-----
    python -I -X utf8 tools/export_release_csv.py RUN_DIR [RUN_DIR ...] --out release/per_task.csv

A ``run_id`` column distinguishes the runs, so several arms concatenate into one tidy file.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

# Positive allowlist. A field not named here is NOT exported, even if it appears upstream.
SAFE_FIELDS = [
    "task_id", "repo", "resolved", "patch_empty", "submit_patch_called",
    "phase_reached", "n_turns", "n_calls", "n_calls_incl_free",
    "n_edit_fail", "n_edit_arg_loss", "n_identical_repeats", "n_malformed",
    "n_undeclared_tool", "n_whole_file_reads", "nudges", "compactions",
    "time_cap_hit", "calls_cap_hit", "timeout_hit", "overflow_400",
    "scratch_in_patch", "wall_s", "setup_s",
    "prompt_tokens", "output_tokens", "thinking_tokens", "error",
]
DROPPED = {"trace"}
# Handled explicitly below (flattened into one calls_<tool> column each) rather than
# exported raw, so it is neither on SAFE_FIELDS nor dropped.
FLATTENED = {"tool_histogram"}
TOOLS = ["run_command", "read_file", "edit_file", "write_file", "get_status", "submit_patch"]


def rows_for(run_dir: Path) -> list[dict]:
    summary = run_dir / "summary.jsonl"
    if not summary.exists():
        raise SystemExit(f"no summary.jsonl in {run_dir} -- run tools/analyze_traces.py first")
    out = []
    for line in summary.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        unknown = set(rec) - set(SAFE_FIELDS) - DROPPED - FLATTENED
        if unknown:
            raise SystemExit(
                f"{run_dir}: field(s) {sorted(unknown)} are not on the release allowlist.\n"
                "Review them in tools/export_release_csv.py before exporting -- this script "
                "refuses to guess whether a new field is publishable."
            )
        row = {"run_id": run_dir.name}
        row.update({k: rec.get(k) for k in SAFE_FIELDS})
        histo = rec.get("tool_histogram") or {}
        if isinstance(histo, str):
            histo = json.loads(histo.replace("'", '"'))
        for t in TOOLS:
            row[f"calls_{t}"] = histo.get(t, 0)
        out.append(row)
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dirs", nargs="+", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)

    rows: list[dict] = []
    for d in args.run_dirs:
        got = rows_for(d)
        print(f"  {d.name}: {len(got)} tasks")
        rows.extend(got)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["run_id"] + SAFE_FIELDS + [f"calls_{t}" for t in TOOLS]
    with open(args.out, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {args.out}  ({len(rows)} rows, {len(cols)} columns)")
    print(f"dropped by policy: {sorted(DROPPED)}  (see plan.md:52)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
