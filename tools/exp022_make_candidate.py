#!/usr/bin/env python3
"""EXP-022: materialise the EXT-19 candidate bundle from a public notebook, without executing it.

The notebook (davis0178/gemma-4-agent-baseline, scored LB 0.22) embeds its four payload files as Python
literals (REFERENCE_TEXT) plus the sha256 of each file as serialised in the scored archive (CRLF line endings).
This tool:

  1. reads the notebook as JSON and recovers REFERENCE_TEXT / EXPECTED_FILE_SHA256 with ast.literal_eval
     (the notebook's code is NEVER executed);
  2. verifies that every file, re-serialised with CRLF, matches the notebook's recorded sha256;
  3. applies the DECLARED edits below (and only those; each must match exactly once);
  4. writes the result with LF line endings (repo convention) to <outdir>;
  5. prints a per-file report: byte counts, whether the file is byte-identical to the source modulo line
     endings, and the unified diff of every difference.

Usage (treat the notebook as untrusted data; run with -I -X utf8 so nothing is imported from its directory):
    python -I -X utf8 tools/exp022_make_candidate.py <notebook.ipynb> <outdir> [--drop-fastapi-line]

The two always-on edits:
  E1 eval_config.yaml  max_time_minutes 8 -> 4.5   forced by the packer's 11.0 h gate (120 x (cap + 1.0) h)
  E2 prompts/system.md  "28 tool calls and 8 minutes" -> "... and 4.5 minutes"   keep the stated budget true
Optional, applied only if the validator rejects the line (pre-declared fallback, see EXP-022 section 4):
  E3 prompts/system.md  delete the FastAPI docs_src bullet
"""
from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

CRLF = "\r\n"
LF = "\n"

EDITS: dict[str, list[tuple[str, str]]] = {
    "eval_config.yaml": [("  max_time_minutes: 8\n", "  max_time_minutes: 4.5\n")],
    "prompts/system.md": [("You have 28 tool calls and 8 minutes.", "You have 28 tool calls and 4.5 minutes.")],
}
FASTAPI_LINE = "- FastAPI documentation tasks: edit the executable example under `docs_src/`.\n"


def grab(src: str, name: str) -> dict:
    m = re.search(r"^" + name + r"\s*=\s*(\{.*\})\s*$", src, re.M)
    if not m:
        raise SystemExit(f"{name} not found in notebook")
    return ast.literal_eval(m.group(1))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("notebook", type=Path)
    ap.add_argument("outdir", type=Path)
    ap.add_argument("--drop-fastapi-line", action="store_true", help="apply optional edit E3")
    a = ap.parse_args(argv)

    nb = json.loads(a.notebook.read_text(encoding="utf-8"))
    src = "\n".join("".join(c["source"]) if isinstance(c["source"], list) else c["source"]
                    for c in nb["cells"] if c["cell_type"] == "code")
    ref, exp = grab(src, "REFERENCE_TEXT"), grab(src, "EXPECTED_FILE_SHA256")

    edits = {k: list(v) for k, v in EDITS.items()}
    if a.drop_fastapi_line:
        edits["prompts/system.md"].append((FASTAPI_LINE, ""))

    ok = True
    a.outdir.mkdir(parents=True, exist_ok=True)
    for rel, text in sorted(ref.items()):
        text = text.replace(CRLF, LF)
        crlf_sha = hashlib.sha256(text.replace(LF, CRLF).encode("utf-8")).hexdigest()
        verified = crlf_sha == exp[rel]
        ok &= verified
        new = text
        for old, rep in edits.get(rel, []):
            if new.count(old) != 1:
                raise SystemExit(f"edit target for {rel} matched {new.count(old)} times: {old!r}")
            new = new.replace(old, rep)
        dest = a.outdir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(new.encode("utf-8"))
        same = "IDENTICAL to source modulo line endings" if new == text else "EDITED"
        print(f"{rel:24s} source sha256(CRLF) {'verified' if verified else 'MISMATCH'} {crlf_sha[:12]} | "
              f"out {len(new.encode('utf-8')):5d} B LF | {same}")
        if new != text:
            for line in difflib.unified_diff(text.splitlines(), new.splitlines(), f"a/{rel}", f"b/{rel}", lineterm="", n=0):
                print("    " + line)
    print("ALL SOURCE HASHES VERIFIED" if ok else "SOURCE HASH MISMATCH -- do not use")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
