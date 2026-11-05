#!/usr/bin/env python3
"""Convert notebooks/kaggle_eval_l4x4.py (py:percent) to .ipynb, optionally embedding a submission zip.

Usage:
    python tools/build_notebook.py                               # -> notebooks/kaggle_eval_l4x4.ipynb
    python tools/build_notebook.py --embed dist/submission.zip   # sets SUBMISSION_B64 in the parameter cell
    python tools/build_notebook.py --username you                # fills kernel-metadata.json
    python tools/build_notebook.py --set RUN_AGENT=False --set N_TASKS=129         --out notebooks/exp000/kaggle_eval_l4x4.ipynb            # parameter-cell overrides
    python tools/build_notebook.py --embed dist/x.zip --cohort experiments/cohorts/smoke-8.txt --out notebooks/exp0NN_screen/kaggle_eval_l4x4.ipynb
Then: kaggle kernels push -p notebooks/   (needs your own Kaggle credentials; never commit them)
"""
from __future__ import annotations

import argparse
import ast
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


def check_override_value(pair: str, name: str, value: str) -> None:
    """Refuse a --set value that is not a single-line Python literal.

    EXP-030 2026-11-05: `--set EXP_ID=EXP-030-p1` was written unquoted, and the kernel died in its first cell
    with a SyntaxError after the push. A bare name (`--set EXP_ID=p1`) would parse but raise NameError on
    Kaggle, so the check is `ast.literal_eval`, not only `ast.parse`. Every value used so far (True/False,
    ints, the --cohort id list, quoted strings) is a literal.
    """
    hint = (f"--set {pair!r}: the value is inserted verbatim as Python source and must be a literal; "
            f"quote strings, e.g. --set {name}='\"{value}\"'")
    if "\n" in value or "\r" in value:
        raise SystemExit(f"--set {pair!r}: the value must be a single line")
    try:
        ast.parse(f"{name} = {value}")
        ast.literal_eval(value)
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError) as exc:
        raise SystemExit(f"{hint} ({type(exc).__name__}: {exc})") from None


def check_cells_parse(text: str, names: list[str]) -> None:
    """Every code cell that holds an overridden assignment must parse as Python after the rewrite."""
    for kind, body in parse_percent(text):
        if kind != "code" or "# overridden by --set" not in body:
            continue
        try:
            ast.parse(body)
        except SyntaxError as exc:
            line = body.splitlines()[exc.lineno - 1] if exc.lineno else ""
            culprit = next((n for n in names if line.startswith(f"{n} = ")), None)
            who = f"--set {culprit}" if culprit else f"--set ({', '.join(names)})"
            raise SystemExit(f"{who}: the rewritten parameter cell does not parse as Python "
                             f"(line {exc.lineno}: {line.strip()!r}: {exc.msg})") from None


def apply_overrides(text: str, pairs: list[str]) -> str:
    """Rewrite `NAME = ...` assignments in the parameter cell from --set NAME=VALUE.

    The value is inserted verbatim as Python source, so quote strings yourself
    (``--set REPO_FILTER='"Textualize/rich"'``). Fails loudly on an unknown name so a
    typo cannot silently run an experiment with the wrong configuration, and on a value
    that is not a Python literal or leaves the parameter cell unparseable (EXP-030).
    """
    names: list[str] = []
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"--set expects NAME=VALUE, got {pair!r}")
        name, value = pair.split("=", 1)
        name, value = name.strip(), value.strip()
        check_override_value(pair, name, value)
        pattern = rf"^{re.escape(name)} = .*$"
        replacement = f"{name} = {value}   # overridden by --set"
        # a callable replacement, so backslashes in the value are not read as regex escapes
        text, n = re.subn(pattern, lambda _m: replacement, text, count=1, flags=re.M)
        if n != 1:
            raise SystemExit(f"--set: no assignment named {name!r} in {SRC.name}")
        names.append(name)
        print(f"set {name} = {value}")
    check_cells_parse(text, names)
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
    ap.add_argument("--cohort", type=Path, metavar="COHORT_TXT",
                    help="experiments/cohorts/<name>.txt: sets TASK_IDS to its ids and N_TASKS to their count "
                         "(the push guard checks TASK_IDS against the cohort the EXP file declares)")
    args = ap.parse_args(argv)
    text = args.src.read_text(encoding="utf-8")
    if args.cohort:
        ids = [ln.strip() for ln in args.cohort.read_text(encoding="utf-8").splitlines()
               if ln.strip() and not ln.startswith("#")]
        if not ids:
            print(f"ERROR: no task ids in {args.cohort}")
            return 1
        args.overrides = [f"TASK_IDS={json.dumps(ids)}", f"N_TASKS={len(ids)}", *args.overrides]
        print(f"cohort {args.cohort.name}: {len(ids)} ids")
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
