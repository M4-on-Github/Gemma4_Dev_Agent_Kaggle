#!/usr/bin/env python3
"""Convert notebooks/kaggle_eval_l4x4.py (py:percent) to .ipynb, optionally embedding a submission zip.

Usage:
    python tools/build_notebook.py                               # -> notebooks/kaggle_eval_l4x4.ipynb
    python tools/build_notebook.py --embed dist/submission.zip   # sets SUBMISSION_B64 in the parameter cell
    python tools/build_notebook.py --username you                # fills kernel-metadata.json
    python tools/build_notebook.py --set RUN_AGENT=False --set N_TASKS=129         --out notebooks/exp000/kaggle_eval_l4x4.ipynb            # parameter-cell overrides
Then: kaggle kernels push -p notebooks/   (needs your own Kaggle credentials; never commit them)
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "notebooks" / "kaggle_eval_l4x4.py"
OUT = ROOT / "notebooks" / "kaggle_eval_l4x4.ipynb"
META = ROOT / "notebooks" / "kernel-metadata.json"
CELL_RE = re.compile(r"^# %%(?: \[(markdown)\])?\s*$")


def parse_percent(text: str) -> list[tuple[str, str]]:
    cells: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        m = CELL_RE.match(line)
        if m:
            cells.append(("markdown" if m.group(1) else "code", []))
            continue
        if not cells:
            cells.append(("code", []))
        cells[-1][1].append(line)
    out = []
    for kind, lines in cells:
        if kind == "markdown":
            lines = [re.sub(r"^# ?", "", ln) for ln in lines]
        body = "\n".join(lines).strip("\n")
        if body.strip():
            out.append((kind, body))
    return out


def apply_overrides(text: str, pairs: list[str]) -> str:
    """Rewrite `NAME = ...` assignments in the parameter cell from --set NAME=VALUE.

    The value is inserted verbatim as Python source, so quote strings yourself
    (``--set REPO_FILTER='"Textualize/rich"'``). Fails loudly on an unknown name so a
    typo cannot silently run an experiment with the wrong configuration.
    """
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"--set expects NAME=VALUE, got {pair!r}")
        name, value = pair.split("=", 1)
        name = name.strip()
        pattern = rf"^{re.escape(name)} = .*$"
        replacement = f"{name} = {value.strip()}   # overridden by --set"
        text, n = re.subn(pattern, replacement, text, count=1, flags=re.M)
        if n != 1:
            raise SystemExit(f"--set: no assignment named {name!r} in {SRC.name}")
        print(f"set {name} = {value.strip()}")
    return text


def to_ipynb(cells: list[tuple[str, str]]) -> dict:
    nb_cells = []
    for kind, body in cells:
        cell = {"cell_type": kind, "metadata": {}, "source": body.splitlines(True)}
        if kind == "code":
            cell.update({"outputs": [], "execution_count": None})
        nb_cells.append(cell)
    return {"cells": nb_cells, "nbformat": 4, "nbformat_minor": 5,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                         "language_info": {"name": "python"}}}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", type=Path, default=SRC)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--embed", type=Path, help="submission.zip to embed as SUBMISSION_B64")
    ap.add_argument("--username", help="Kaggle username for kernel-metadata.json")
    ap.add_argument("--set", dest="overrides", action="append", default=[], metavar="NAME=VALUE",
                    help="override a parameter-cell assignment; repeatable")
    args = ap.parse_args(argv)
    text = args.src.read_text(encoding="utf-8")
    if args.overrides:
        text = apply_overrides(text, args.overrides)
    if args.embed:
        b64 = base64.b64encode(args.embed.read_bytes()).decode()
        text, n = re.subn(r'^SUBMISSION_B64 = ""', f'SUBMISSION_B64 = "{b64}"', text, count=1, flags=re.M)
        if n != 1:
            print("ERROR: SUBMISSION_B64 line not found in the parameter cell")
            return 1
        print(f"embedded {args.embed} ({len(b64)} base64 chars)")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(to_ipynb(parse_percent(text)), indent=1), encoding="utf-8")
    print(f"wrote {args.out}")
    if args.username and META.is_file():
        meta = json.loads(META.read_text(encoding="utf-8"))
        meta["id"] = f"{args.username}/{meta['id'].split('/', 1)[-1]}"
        META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        print(f"kernel-metadata.json id -> {meta['id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
