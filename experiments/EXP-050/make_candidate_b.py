#!/usr/bin/env python3
"""EXP-050: build variant B from the committed EXP-033 E4B tree, with one anchored edit.

Reads each file of experiments/EXP-033/candidate-e4b from the committed HEAD blob (git show), so the
source is the LF blob, not the worktree. Applies exactly one edit, which must match exactly once:

  B1 eval_config.yaml  max_time_minutes 8 -> 4.5, with a dated EXP-050 comment

Every other file is copied byte for byte. Writes LF to experiments/EXP-050/candidate-e4b-4p5/ and prints
per-file sha256 and whether the file equals its source.

Usage: python -I -X utf8 experiments/EXP-050/make_candidate_b.py
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = "experiments/EXP-033/candidate-e4b"
OUT = ROOT / "experiments" / "EXP-050" / "candidate-e4b-4p5"
FILES = ["agent.yaml", "configs/sampling.yaml", "eval_config.yaml", "prompts/system.md"]

EDITS = {
    "eval_config.yaml": [(
        b"  max_time_minutes: 8\n",
        b"  max_time_minutes: 4.5   # EXP-050 2026-11-07: 8 -> 4.5, so the packer's 11.0 h gate passes"
        b" without an override (120 x 5.5 min = 11.0 h). Not run at 4.5: the harness task message states"
        b" this value to the model, and prompts/system.md still states 8 minutes (left unchanged, one variable)\n",
    )],
}


def blob(path: str) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{path}"],
                          check=True, capture_output=True).stdout


def main() -> int:
    for rel in FILES:
        data = blob(f"{SRC}/{rel}")
        if b"\r\n" in data:
            print(f"ERROR: {rel} blob has CRLF")
            return 1
        new = data
        for old, rep in EDITS.get(rel, []):
            n = new.count(old)
            if n != 1:
                print(f"ERROR: anchor in {rel} matched {n} times")
                return 1
            new = new.replace(old, rep)
        dst = OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(new)
        print(f"{rel}: {len(new)} B sha256 {hashlib.sha256(new).hexdigest()} "
              f"{'identical to source' if new == data else 'edited'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
