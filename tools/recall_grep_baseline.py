"""Free, local, CPU-only baseline: how well does plain lexical search (no graph, no
embeddings, no Kaggle) recall the gold files identified by tools/recall_extract_gold.py?

Per the 2026-10-18 independent review, this baseline is required before any
search_similar_code / get_code_neighbors recall number can be interpreted as "good" or
"bad" -- if grep already gets most of the way there, the graph tools add little; if grep
does poorly, that raises the bar the graph tools need to clear.

Two baselines, both derived only from problem_statement + hints_text (the same inputs the
real agent would have at LOCATE time):
  1. identifier extraction (dotted paths, CamelCase>=4, snake_case>=4) -> rank files by
     hit count of any extracted identifier appearing in the file's text (via `git grep -l`
     against the base-commit tree inside the snapshot's embedded .git repo).
  2. same identifier set, but score by total occurrence count (via `git grep -c`) rather
     than file-level presence, as an alternate ranking.

Recall@k is computed against gold files (from gold.jsonl's gold_symbols[].file), restricted
to non-formatting-only, non-new-file gold (new files can't be found by searching the base
tree, since they don't exist yet in it -- same limitation search_similar_code would have).

Usage: python tools/recall_grep_baseline.py
Output: experiments/recall_check/grep_baseline.jsonl + summary to stdout
"""

from __future__ import annotations

import json
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TASKS_JSONL = REPO_ROOT / "data" / "local" / "tasks.jsonl"
SNAPSHOTS_DIR = REPO_ROOT / "data" / "local" / "snapshots"
GOLD_JSONL = REPO_ROOT / "experiments" / "recall_check" / "gold.jsonl"
OUT_PATH = REPO_ROOT / "experiments" / "recall_check" / "grep_baseline.jsonl"

STOPWORDS = {
    "the", "this", "that", "with", "from", "when", "what", "which", "where", "there",
    "should", "would", "could", "function", "method", "class", "error", "issue", "problem",
    "python", "code", "value", "values", "return", "returns", "result", "example", "using",
    "used", "will", "does", "test", "tests", "case", "cases", "import", "none", "true",
    "false", "self", "args", "kwargs",
}

DOTTED_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){1,5}\b")
CAMEL_RE = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+\b")
SNAKE_RE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")


def extract_identifiers(text: str) -> list[str]:
    if not text:
        return []
    found: list[str] = []
    found.extend(DOTTED_RE.findall(text))
    found.extend(CAMEL_RE.findall(text))
    for m in SNAKE_RE.findall(text):
        if m not in STOPWORDS and len(m) >= 4:
            found.append(m)
    # Dedup preserving first-seen order.
    seen = set()
    out = []
    for ident in found:
        if ident not in seen:
            seen.add(ident)
            out.append(ident)
    return out


def extract_snapshot(tgz_path: Path, dest: Path) -> bool:
    try:
        with tarfile.open(tgz_path) as tf:
            tf.extractall(dest, filter="data")
        return True
    except (FileNotFoundError, tarfile.TarError):
        return False


def git_grep_files(repo_dir: Path, pattern: str) -> list[str]:
    """Runs `git grep -l -I -F <pattern>` against the working tree inside repo_dir.

    NOTE: the snapshot's embedded .git history does not reliably contain base_commit as a
    reachable commit object (confirmed empirically -- `git grep <base_commit>` fails with
    "fatal: unable to parse object" even though the file content on disk matches base_commit
    exactly, per tools/recall_extract_gold.py's independently-correct symbol extraction from
    the same tarball). So we grep the checked-out working tree directly rather than a ref.
    """
    try:
        proc = subprocess.run(
            ["git", "grep", "-l", "-I", "-F", pattern],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return []
    if proc.returncode not in (0, 1):  # 1 == no matches, still fine
        return []
    return [line for line in proc.stdout.splitlines() if line]


def rank_files_by_hits(repo_dir: Path, identifiers: list[str]) -> list[tuple[str, int]]:
    hit_counts: dict[str, int] = {}
    for ident in identifiers:
        for f in git_grep_files(repo_dir, ident):
            if not f.endswith(".py"):
                continue
            hit_counts[f] = hit_counts.get(f, 0) + 1
    return sorted(hit_counts.items(), key=lambda kv: -kv[1])


def recall_at_k(ranked_files: list[str], gold_files: set[str], k: int) -> bool:
    return bool(gold_files & set(ranked_files[:k]))


def main() -> None:
    tasks = {}
    with TASKS_JSONL.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                t = json.loads(line)
                tasks[t["instance_id"]] = t

    gold_recs = []
    with GOLD_JSONL.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                gold_recs.append(json.loads(line))

    results = []
    n_no_identifiers = 0
    n_no_gold_findable = 0
    hit_at_1 = 0
    hit_at_3 = 0
    hit_at_5 = 0
    hit_at_10 = 0
    n_scored = 0

    with tempfile.TemporaryDirectory(prefix="recall_grep_") as tmp_base:
        tmp_base_path = Path(tmp_base)
        for gold_rec in gold_recs:
            instance_id = gold_rec["instance_id"]
            task = tasks.get(instance_id)
            if task is None or not gold_rec["snapshot_found"]:
                continue

            gold_files = {
                g["file"]
                for g in gold_rec["gold_symbols"]
                if not g["formatting_only"] and g["kind"] != "new_module"
            }
            if not gold_files:
                n_no_gold_findable += 1
                continue

            text = (task.get("problem_statement") or "") + "\n" + (task.get("hints_text") or "")
            identifiers = extract_identifiers(text)
            rec = {
                "instance_id": instance_id,
                "n_identifiers": len(identifiers),
                "gold_files": sorted(gold_files),
            }
            if not identifiers:
                n_no_identifiers += 1
                rec["ranked_files"] = []
                results.append(rec)
                continue

            extract_dir = tmp_base_path / instance_id
            extract_dir.mkdir(parents=True, exist_ok=True)
            if not extract_snapshot(SNAPSHOTS_DIR / f"{instance_id}.tgz", extract_dir):
                rec["ranked_files"] = []
                results.append(rec)
                continue

            # Snapshot may extract directly, or into a single top-level dir.
            repo_dir = extract_dir
            git_dirs = list(extract_dir.glob("**/.git"))
            if git_dirs:
                repo_dir = git_dirs[0].parent

            ranked = rank_files_by_hits(repo_dir, identifiers)
            ranked_files = [f for f, _count in ranked]
            rec["ranked_files"] = ranked_files[:20]
            rec["hit_counts_top5"] = ranked[:5]
            results.append(rec)

            n_scored += 1
            if recall_at_k(ranked_files, gold_files, 1):
                hit_at_1 += 1
            if recall_at_k(ranked_files, gold_files, 3):
                hit_at_3 += 1
            if recall_at_k(ranked_files, gold_files, 5):
                hit_at_5 += 1
            if recall_at_k(ranked_files, gold_files, 10):
                hit_at_10 += 1

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as out_f:
        for rec in results:
            out_f.write(json.dumps(rec) + "\n")

    print(f"tasks with findable gold (non-new-file):  {n_scored + n_no_identifiers}")
    print(f"  -> skipped, no identifiers extracted:    {n_no_identifiers}")
    print(f"  -> scored:                                {n_scored}")
    print(f"tasks with no findable gold (all new/fmt): {n_no_gold_findable}")
    if n_scored:
        print(f"git-grep file-level recall@1:  {hit_at_1}/{n_scored} = {hit_at_1/n_scored:.1%}")
        print(f"git-grep file-level recall@3:  {hit_at_3}/{n_scored} = {hit_at_3/n_scored:.1%}")
        print(f"git-grep file-level recall@5:  {hit_at_5}/{n_scored} = {hit_at_5/n_scored:.1%}")
        print(f"git-grep file-level recall@10: {hit_at_10}/{n_scored} = {hit_at_10/n_scored:.1%}")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
