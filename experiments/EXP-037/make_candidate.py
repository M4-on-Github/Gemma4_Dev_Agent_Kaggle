"""EXP-037: build candidate-vendor from the EXP-027 v24-at-8 tree (= EXP-028 Arm R) with one anchored insertion.

The only change: experiments/EXP-037/insert_vendoring.md is inserted into prompts/system.md immediately before
the anchor line "## 1. Contract, before any tool call", which must occur exactly once. Every other file is
byte-copied. The base files are checked against the sha256 values recorded below (the committed LF blobs that
Arm R ran, zip c22069db...7600) before anything is written.

Run as:  python experiments/EXP-037/make_candidate.py [--out experiments/EXP-037/candidate-vendor]
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "experiments" / "EXP-027" / "candidate-v24-at-8"
INSERT = Path(__file__).resolve().parent / "insert_vendoring.md"
ANCHOR = "## 1. Contract, before any tool call\n"
BASE_SHA256 = {
    "agent.yaml": "6ad913b0c0cb67d669116a4074d7b520b3a69c8d5aa960b6abe51f9850b45227",
    "eval_config.yaml": "916cf6cb34a6cc3de39837fa72cac681599b9ac2a3ee0b893adadfd36474c531",
    "configs/sampling.yaml": "630056889710d27dbf17c8fde62e033b7329616b7db435987cb4607b66a7c3f6",
    "prompts/system.md": "57a20af4eb29bbfdab003ab8cf04f6495674887ec5ba3dd746750930179a8041",
}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "candidate-vendor")
    a = ap.parse_args(argv)

    files = sorted(p.relative_to(BASE).as_posix() for p in BASE.rglob("*") if p.is_file())
    if files != sorted(BASE_SHA256):
        sys.exit(f"base tree file set differs: {files}")
    for rel, want in BASE_SHA256.items():
        got = sha((BASE / rel).read_bytes())
        if got != want:
            sys.exit(f"base file {rel}: sha256 {got} != recorded {want} (CRLF worktree? check out the LF blob)")

    ins = INSERT.read_bytes()
    if b"\r" in ins:
        sys.exit("insert file has CR bytes; LF only")
    src = (BASE / "prompts/system.md").read_bytes().decode("utf-8")
    if src.count(ANCHOR) != 1:
        sys.exit(f"anchor found {src.count(ANCHOR)} times, need exactly 1")
    new = src.replace(ANCHOR, ins.decode("utf-8") + ANCHOR, 1)

    if a.out.exists():
        shutil.rmtree(a.out)
    for rel in files:
        dst = a.out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if rel == "prompts/system.md":
            dst.write_bytes(new.encode("utf-8"))
        else:
            dst.write_bytes((BASE / rel).read_bytes())

    for rel in files:
        b = (a.out / rel).read_bytes()
        print(f"{rel}: {len(b)} bytes, sha256 {sha(b)}, {'changed' if rel == 'prompts/system.md' else 'byte-identical to base'}")
    print(f"prompts/system.md: base {len(src.encode())} bytes -> {len(new.encode())} bytes "
          f"(+{len(new.encode()) - len(src.encode())}), base {len(src)} chars -> {len(new)} chars, "
          f"insert {len(ins)} bytes, {ins.decode().count(chr(10))} lines")
    diff = list(difflib.unified_diff(src.splitlines(), new.splitlines(), lineterm="", n=0))
    added = [l for l in diff if l.startswith("+") and not l.startswith("+++")]
    removed = [l for l in diff if l.startswith("-") and not l.startswith("---")]
    print(f"diff: {len(added)} lines added, {len(removed)} removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
