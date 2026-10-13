#!/usr/bin/env python3
"""Pre-commit style guard: refuse to commit competition data, large files, credentials or bad submission files.

Checks every staged file (or every tracked file with --all):
  * path under data/, runs/, wheelhouse/, snapshots/, graphs/, embeddings/, traces/ -> FAIL (redistribution rule)
  * size > 5 MiB -> FAIL
  * extension in .tgz .npz .safetensors .zip .parquet .bin .pt .pth -> FAIL
  * name in kaggle.json, access_token, .env, *.env, id_rsa -> FAIL
  * content that looks like a credential (KAGGLE_KEY=..., "key": "<32 hex>", api tokens) -> FAIL
  * a file under submission/ with a disallowed extension -> FAIL
  * a .jsonl outside tests/fixtures or experiments/**/summary.jsonl -> FAIL (traces contain repo snippets)

Install as a hook:  ln -sf ../../tools/check_repo_hygiene.py .git/hooks/pre-commit  (needs chmod +x)
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

MAX_BYTES = 5 * 1024 * 1024
DATA_DIRS = ("data", "runs", "wheelhouse", "snapshots", "graphs", "embeddings", "traces")
BAD_EXT = {".tgz", ".npz", ".safetensors", ".zip", ".parquet", ".bin", ".pt", ".pth", ".gguf"}
BAD_NAMES = {"kaggle.json", "access_token", ".env", "id_rsa", "id_ed25519"}
SUBMISSION_EXT = {".yaml", ".yml", ".md", ".txt", ".py", ".json", ".safetensors"}
SECRET_PATTERNS = (
    re.compile(r"KAGGLE_KEY\s*[=:]\s*['\"]?[A-Za-z0-9]{16,}"),
    re.compile(r'"key"\s*:\s*"[0-9a-f]{32}"'),
    re.compile(r"\b(sk|hf|ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----"),
)


def staged_files(repo: Path, all_tracked: bool) -> list[str]:
    cmd = ["git", "ls-files"] if all_tracked else ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"]
    out = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, check=True).stdout
    return [ln for ln in out.splitlines() if ln.strip()]


def check_path(repo: Path, rel: str) -> list[str]:
    problems: list[str] = []
    pp = PurePosixPath(rel)
    parts = pp.parts
    if parts and parts[0] in DATA_DIRS and pp.name != ".gitkeep":
        problems.append(f"{rel}: competition data / run output must not be committed")
    if pp.suffix.lower() in BAD_EXT:
        problems.append(f"{rel}: binary/archive extension {pp.suffix} is not allowed in git")
    if pp.name in BAD_NAMES or pp.name.endswith(".env"):
        problems.append(f"{rel}: credential file")
    if pp.suffix == ".jsonl" and not (parts[:2] == ("tests", "fixtures") or
                                      (parts[0] == "experiments" and pp.name == "summary.jsonl")):
        problems.append(f"{rel}: .jsonl outside tests/fixtures or experiments/**/summary.jsonl (traces hold repo code)")
    if parts and parts[0] == "submission" and pp.suffix.lower() not in SUBMISSION_EXT:
        problems.append(f"{rel}: disallowed extension inside submission/ (allowed {sorted(SUBMISSION_EXT)})")
    path = repo / rel
    if path.is_file():
        size = path.stat().st_size
        if size > MAX_BYTES:
            problems.append(f"{rel}: {size / 1048576:.1f} MiB > 5 MiB")
        if size < 2 * MAX_BYTES and pp.suffix.lower() not in BAD_EXT:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                text = ""
            for pat in SECRET_PATTERNS:
                if pat.search(text):
                    problems.append(f"{rel}: looks like it contains a credential ({pat.pattern[:30]}...)")
                    break
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true", help="check all tracked files, not only staged ones")
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("paths", nargs="*", help="explicit paths to check instead of git")
    args = ap.parse_args(argv)
    files = args.paths or staged_files(args.repo, args.all)
    problems: list[str] = []
    for rel in files:
        problems += check_path(args.repo, rel)
    if problems:
        print("REPO HYGIENE: FAIL")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"REPO HYGIENE: OK ({len(files)} files checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
