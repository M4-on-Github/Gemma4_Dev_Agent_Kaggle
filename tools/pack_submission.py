#!/usr/bin/env python3
"""Build a deterministic submission.zip with agent.yaml at the archive root.

Steps:
  1. compute the closure of files reachable from the root config (!include, agent_tool/sub_agents config_path,
     skills directories, the referenced adapter directory) plus eval_config.yaml;
  2. copy them (real copies, never hard links: zipping hard-linked files has produced 0-byte members [M]);
  3. validate the build tree strictly (tools/validate_submission.py) — refuse to pack if invalid, and refuse
     if the eval_config worst case exceeds the 11.0 h packing gate;
  4. write the zip with fixed timestamps and 0644 modes so identical sources give an identical SHA256;
  5. re-validate the archive and print members, size and SHA256 (record the hash in experiments/README.md).

Usage:
    python tools/pack_submission.py [--src submission] [--out dist/submission.zip] [--allow-warnings] [--official]
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import submission_rules as R  # noqa: E402
import validate_submission as V  # noqa: E402

_ZIP_DATE = (2026, 1, 1, 0, 0, 0)

# Prompt variants rejected by an experiment but left reachable in git history: packing one into a
# submission zip without noticing would silently re-score a config we already decided against.
# Each entry is (unique substring, experiment id, reason) — see experiments/<id>.md for the decision.
_REJECTED_PROMPT_MARKERS: list[tuple[str, str, str]] = [
    (
        "search_similar_code with that identifier query",
        "EXP-002-estop-a",
        "graph-tools-first LOCATE (E-STOP(a')): decision was 'do not proceed', "
        "superseded by the recall-check finding that these tools lose to a grep baseline at every k",
    ),
]


def check_rejected_prompts(build: Path) -> list[str]:
    hits = []
    for path in sorted(build.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker, exp_id, reason in _REJECTED_PROMPT_MARKERS:
            if marker in text:
                rel = path.relative_to(build)
                hits.append(f"{rel}: matches rejected variant from {exp_id} ({reason})")
    return hits


def build_tree(src: Path, build: Path) -> list[Path]:
    tree = V.load_agent_tree(src)
    files = sorted(tree.reachable_files())
    src = src.resolve()
    for f in files:
        rel = f.relative_to(src)
        dest = build / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(f.read_bytes())   # byte copy: never a hard link or symlink
    return files


def write_zip(build: Path, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(build.rglob("*")):
            if p.is_file():
                info = zipfile.ZipInfo(p.relative_to(build).as_posix(), date_time=_ZIP_DATE)
                info.external_attr = 0o644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, p.read_bytes())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pack(src: Path, out: Path, *, allow_warnings: bool = False, official: bool = False) -> int:
    with tempfile.TemporaryDirectory() as td:
        build = Path(td) / "build"
        build.mkdir()
        print(f"[1/5] computing closure from {src}")
        try:
            files = build_tree(src, build)
        except V.SubmissionError as exc:
            print(f"ERROR: {exc}")
            return 1
        print(f"      {len(files)} reachable files")
        rejected = check_rejected_prompts(build)
        if rejected:
            print("PACKING REFUSED: build tree contains an experimentally-rejected prompt variant:")
            for hit in rejected:
                print(f"  - {hit}")
            return 1
        print("[2/5] validating build tree (strict)")
        report = V.validate_dir(build, strict_tree=True, official=official)
        print(report.render())
        if not report.ok:
            print("PACKING REFUSED: validation errors")
            return 1
        if report.warnings and not allow_warnings:
            print("PACKING REFUSED: warnings present (re-run with --allow-warnings to override)")
            return 1
        print(f"[3/5] writing {out}")
        write_zip(build, out)
    print("[4/5] re-validating the archive")
    zreport = V.validate_zip(out, official=False)
    if not zreport.ok:
        print(zreport.render())
        print("PACKING REFUSED: archive invalid")
        out.unlink(missing_ok=True)
        return 1
    with zipfile.ZipFile(out) as zf:
        names = sorted(zf.namelist())
    print("[5/5] archive contents:")
    for n in names:
        print(f"  {n}")
    size = out.stat().st_size
    print(f"\nagent.yaml at root: {'agent.yaml' in names}")
    print(f"archive: {out}  size: {size / 1024:.1f} KiB  ({size / R.MAX_TOTAL_SIZE_BYTES * 100:.3f}% of 3 GiB)")
    print(f"sha256: {sha256(out)}")
    print("PACK: OK — record the sha256 next to the LB submission in experiments/README.md")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    root = Path(__file__).resolve().parents[1]
    ap.add_argument("--src", type=Path, default=root / "submission")
    ap.add_argument("--out", type=Path, default=root / "dist" / "submission.zip")
    ap.add_argument("--allow-warnings", action="store_true")
    ap.add_argument("--official", action="store_true", help="also run the harness validator if importable")
    args = ap.parse_args(argv)
    return pack(args.src.resolve(), args.out.resolve(), allow_warnings=args.allow_warnings, official=args.official)


if __name__ == "__main__":
    sys.exit(main())
