#!/usr/bin/env python3
"""Build the EXP-024 "lost-edit recovery" candidate bundle (experiments/EXP-024-direction-review-2.md).

The candidate is submission/ with TWO prompt edits and nothing else. Every other byte of every
other file is taken verbatim from the committed LF blob (`git show HEAD:<path>`), because R9 in
EXP-022 showed that packing the autocrlf worktree changes the zip sha256.

Each anchor must match EXACTLY ONCE or the build aborts, so the diff cannot drift silently.

Usage:
    python -I -X utf8 tools/exp024_make_editfix.py <outdir>
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

FILES = (
    "agent.yaml",
    "configs/sampling.yaml",
    "eval_config.yaml",
    "prompts/swe_coder.md",
)

# --- E1: reverse the anchor-shortening advice that the traces show causes the doom loop -------------
E1_OLD = (
    "Use edit_file with old_string copied exactly from the file, 2 to 4 unique lines, short and "
    "distinct. Prefer several small edit_file calls over one large one. If edit_file reports that "
    "old_string was not found or is not unique, read_file that range again and retry with a shorter, "
    "more distinctive anchor; never retry the same anchor."
)
E1_NEW = (
    "Use edit_file with old_string copied verbatim from your most recent read_file of that exact "
    "file, and make it LONG: 3 or more consecutive whole lines, roughly 150 to 300 characters, "
    "including the enclosing def or class line when there is one. Long verbatim anchors are what "
    "succeed here; a one-line anchor is the most common cause of a lost edit, so never answer a "
    "failed edit by shortening the anchor. If edit_file reports that old_string was not found or is "
    "not unique, read_file that range again and re-anchor on MORE surrounding lines, never fewer."
)

# --- E2: an error-keyed recovery rule, inserted as its own section before the budget ledger --------
E2_OLD = "\n# Budget ledger\n"
E2_NEW = """
# Lost-edit recovery (the most common way a run scores zero)
If edit_file comes back with `failed as the following mandatory input parameters are not present: old_string`, the call never reached the file at all: the old_string argument was lost on the way to the tool, so your anchor was never tried and the file is untouched. Re-sending the same arguments reproduces this error forever; runs have spent a quarter of their whole budget doing exactly that and finished with an empty patch. Never send the same edit_file arguments twice. Recover on your very next call, in this order:
1. Re-send edit_file ONCE with a much LONGER old_string: 3 or more consecutive whole lines, 150 characters or more, copied verbatim from your last read_file. This is what actually recovers; shortening the anchor makes it worse.
2. If that also fails and the file is under about 150 lines, read_file the whole file, then rewrite it with ONE write_file call carrying the complete corrected content. write_file takes filepath then content, and content is its last argument, which is why it does not get lost this way.
3. If the file is larger than that, make the change with a single run_command that reads the file, applies one replace of a short unique single-line fragment, and writes it back.
An edit that never lands is worth exactly as much as no patch at all, and an empty patch always scores zero.

# Budget ledger
"""


def git_show(path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"HEAD:submission/{path}"],
        check=True, stdout=subprocess.PIPE,
    ).stdout


def apply_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"ABORT {label}: anchor matched {n} times, expected exactly 1")
    print(f"  {label}: anchor matched exactly once "
          f"({len(old)} B -> {len(new)} B, {len(new) - len(old):+d})")
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)

    for rel in FILES:
        blob = git_show(rel)
        if b"\r\n" in blob:
            raise SystemExit(f"ABORT: HEAD blob for {rel} contains CRLF")
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)

        if rel == "prompts/swe_coder.md":
            text = blob.decode("utf-8")
            before = len(blob)  # BYTES, so the delta below is comparable to len(blob) after encode
            text = apply_once(text, E1_OLD, E1_NEW, "E1 anchor-length rule")
            text = apply_once(text, E2_OLD, E2_NEW, "E2 lost-edit recovery")
            blob = text.encode("utf-8")
            print(f"  prompt: {before} -> {len(blob)} B ({len(blob) - before:+d})")

        dst.write_bytes(blob)
        print(f"  wrote {rel:26s} {len(blob):6d} B  sha256 {hashlib.sha256(blob).hexdigest()[:12]}")

    # No .gitattributes here: --official --strict rejects hidden files. The LF hazard of EXP-022 R9
    # is handled instead by writing the HEAD blobs byte-for-byte above (they are verified CRLF-free),
    # so the tree is already LF and must be packed without a round-trip through a checkout.
    print(f"\nCandidate tree: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
