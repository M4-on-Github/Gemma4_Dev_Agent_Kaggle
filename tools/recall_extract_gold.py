"""Extract gold-symbol ground truth for the free CPU-only search_similar_code recall check.

Runs entirely locally (no Kaggle/mounted graph data needed): diffs each sound task's
gold patch against its own base-commit snapshot (data/local/snapshots/<instance_id>.tgz),
AST-parses the base file to find the enclosing function/class for each changed line range,
and tags each changed symbol as 'primary' or 'formatting_only' (whitespace/comment-only diff).

This sidesteps the circularity problem flagged by the 2026-10-18 independent review (reusing
the harness's own graph-node boundaries as "ground truth" can't see gold the graph itself
missed, e.g. the open async-def coverage question) by deriving gold independently from the
actual base-commit source via Python's ast module.

Usage: python tools/recall_extract_gold.py
Output: experiments/recall_check/gold.jsonl (one record per task)
"""

from __future__ import annotations

import ast
import json
import re
import tarfile
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TASKS_JSONL = REPO_ROOT / "data" / "local" / "tasks.jsonl"
SNAPSHOTS_DIR = REPO_ROOT / "data" / "local" / "snapshots"
OUT_DIR = REPO_ROOT / "experiments" / "recall_check"
OUT_PATH = OUT_DIR / "gold.jsonl"

HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


@dataclass
class Hunk:
    file_path: str  # path as it appears in the diff, relative, forward slashes
    old_start: int
    old_len: int
    new_start: int
    new_len: int
    old_lines: list[str] = field(default_factory=list)  # context+removed, no prefix
    new_lines: list[str] = field(default_factory=list)  # context+added, no prefix


def parse_unified_diff(patch_text: str) -> list[Hunk]:
    """Minimal unified-diff parser: good enough for git-style patches with a/ b/ prefixes."""
    hunks: list[Hunk] = []
    cur_file: str | None = None
    cur_hunk: Hunk | None = None
    for raw_line in patch_text.splitlines():
        if raw_line.startswith("diff --git "):
            cur_file = None
            cur_hunk = None
            continue
        if raw_line.startswith("+++ "):
            path = raw_line[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            if path == "/dev/null":
                cur_file = None
            else:
                cur_file = path
            continue
        if raw_line.startswith("--- "):
            continue
        m = HUNK_HEADER_RE.match(raw_line)
        if m:
            if cur_hunk is not None:
                hunks.append(cur_hunk)
            old_start = int(m.group(1))
            old_len = int(m.group(2)) if m.group(2) is not None else 1
            new_start = int(m.group(3))
            new_len = int(m.group(4)) if m.group(4) is not None else 1
            cur_hunk = Hunk(
                file_path=cur_file or "",
                old_start=old_start,
                old_len=old_len,
                new_start=new_start,
                new_len=new_len,
            )
            continue
        if cur_hunk is None:
            continue
        if raw_line.startswith("-"):
            cur_hunk.old_lines.append(raw_line[1:])
        elif raw_line.startswith("+"):
            cur_hunk.new_lines.append(raw_line[1:])
        elif raw_line.startswith(" "):
            cur_hunk.old_lines.append(raw_line[1:])
            cur_hunk.new_lines.append(raw_line[1:])
        elif raw_line.startswith("\\"):
            continue  # "\ No newline at end of file"
        else:
            # Blank context line with no leading space (rare but seen in some patches)
            cur_hunk.old_lines.append(raw_line)
            cur_hunk.new_lines.append(raw_line)
    if cur_hunk is not None:
        hunks.append(cur_hunk)
    return [h for h in hunks if h.file_path.endswith(".py")]


def is_formatting_only(hunk: Hunk, patch_lines: list[str]) -> bool:
    """Heuristic: a hunk is formatting-only if every removed/added line, once whitespace
    is stripped, has a matching counterpart on the other side (same multiset of stripped
    lines) -- i.e. the diff is a pure reflow/whitespace/comment change with no lines that
    introduce a genuinely new stripped-text token sequence."""
    removed = [ln.strip() for ln in patch_lines if ln.startswith("-") and not ln.startswith("---")]
    added = [ln.strip() for ln in patch_lines if ln.startswith("+") and not ln.startswith("+++")]
    if not removed and not added:
        return True
    return sorted(removed) == sorted(added)


class ScopeFinder(ast.NodeVisitor):
    """Builds a line-range -> dotted-qualname index from a module's AST."""

    def __init__(self) -> None:
        self.ranges: list[tuple[int, int, str, str]] = []  # (start, end, qualname, kind)

    def _visit_def(self, node, prefix: str, kind: str) -> None:
        qualname = f"{prefix}.{node.name}" if prefix else node.name
        end = getattr(node, "end_lineno", node.lineno)
        self.ranges.append((node.lineno, end, qualname, kind))
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._visit_def(child, qualname, "function")
            elif isinstance(child, ast.ClassDef):
                self._visit_def(child, qualname, "class")

    def visit_Module(self, node: ast.Module) -> None:  # noqa: N802
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._visit_def(child, "", "function")
            elif isinstance(child, ast.ClassDef):
                self._visit_def(child, "", "class")


def build_scope_index(source: str) -> tuple[list[tuple[int, int, str, str]], bool]:
    """Returns (ranges, had_syntax_error). An empty ranges list with had_syntax_error=False
    just means the file has no function/class defs (e.g. a pure data/constants module)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [], True
    finder = ScopeFinder()
    finder.visit(tree)
    return finder.ranges, False


def enclosing_symbol(
    ranges: list[tuple[int, int, str, str]], line: int
) -> tuple[str, str] | None:
    """Returns the innermost (smallest-span) def/class enclosing `line`, or None for
    module-level (no enclosing def/class)."""
    best: tuple[int, int, str, str] | None = None
    for start, end, qualname, kind in ranges:
        if start <= line <= end:
            if best is None or (end - start) < (best[1] - best[0]):
                best = (start, end, qualname, kind)
    if best is None:
        return None
    return best[2], best[3]


def module_qualname(file_path: str) -> str:
    p = file_path[:-3] if file_path.endswith(".py") else file_path
    p = p.replace("/", ".")
    if p.endswith(".__init__"):
        p = p[: -len(".__init__")]
    return p


def read_snapshot_file(tgz_path: Path, rel_path: str) -> str | None:
    try:
        with tarfile.open(tgz_path) as tf:
            for candidate in (f"./{rel_path}", rel_path):
                try:
                    member = tf.getmember(candidate)
                except KeyError:
                    continue
                f = tf.extractfile(member)
                if f is None:
                    return None
                return f.read().decode("utf-8", errors="replace")
    except (FileNotFoundError, tarfile.TarError):
        return None
    return None


def extract_gold_for_task(task: dict) -> dict:
    instance_id = task["instance_id"]
    patch_text = task.get("patch") or ""
    snapshot_path = SNAPSHOTS_DIR / f"{instance_id}.tgz"

    result: dict = {
        "instance_id": instance_id,
        "repo": task.get("repo"),
        "base_commit": task.get("base_commit"),
        "snapshot_found": snapshot_path.exists(),
        "gold_symbols": [],
        "files_touched": [],
        "new_files": [],
        "parse_errors": [],
    }
    if not snapshot_path.exists():
        return result

    hunks = parse_unified_diff(patch_text)
    files_touched = sorted({h.file_path for h in hunks})
    result["files_touched"] = files_touched

    # Group hunks by file so we only read + parse each base file once.
    by_file: dict[str, list[Hunk]] = {}
    for h in hunks:
        by_file.setdefault(h.file_path, []).append(h)

    gold: dict[tuple[str, str], dict] = {}  # (file, qualname) -> record

    for file_path, file_hunks in by_file.items():
        base_source = read_snapshot_file(snapshot_path, file_path)
        if base_source is None:
            # New file entirely (no base content) -- gold is the whole new module.
            result["new_files"].append(file_path)
            key = (file_path, module_qualname(file_path))
            gold.setdefault(
                key,
                {
                    "file": file_path,
                    "qualname": module_qualname(file_path),
                    "kind": "new_module",
                    "formatting_only": False,
                },
            )
            continue

        ranges, had_syntax_error = build_scope_index(base_source)
        if had_syntax_error:
            result["parse_errors"].append(file_path)

        for h in file_hunks:
            patch_lines = []
            # Reconstruct the raw +/-/space lines for this specific hunk for the
            # formatting-only heuristic (re-derive from old/new_lines is lossy for
            # pure-context lines, so re-scan the original patch text per-hunk instead).
            patch_lines = _raw_hunk_lines(patch_text, file_path, h)
            fmt_only = is_formatting_only(h, patch_lines)

            if h.old_len == 0:
                # Pure insertion: anchor on the base-file line just before the insertion
                # point (old_start is the context line right before where new lines go).
                anchor_line = max(1, h.old_start)
            else:
                anchor_line = h.old_start + max(0, h.old_len // 2)

            found = enclosing_symbol(ranges, anchor_line)
            if found is None:
                qualname = module_qualname(file_path)
                kind = "module_level"
            else:
                qualname, kind = found
                qualname = f"{module_qualname(file_path)}.{qualname}"

            key = (file_path, qualname)
            if key in gold:
                if not fmt_only:
                    gold[key]["formatting_only"] = False
            else:
                gold[key] = {
                    "file": file_path,
                    "qualname": qualname,
                    "kind": kind,
                    "formatting_only": fmt_only,
                }

    result["gold_symbols"] = sorted(
        gold.values(), key=lambda r: (r["file"], r["qualname"])
    )
    return result


def _raw_hunk_lines(patch_text: str, file_path: str, target: Hunk) -> list[str]:
    """Re-extract a specific hunk's raw diff lines (with +/-/space prefixes intact)."""
    lines = patch_text.splitlines()
    out: list[str] = []
    in_target_file = False
    in_target_hunk = False
    seen_count = 0
    for line in lines:
        if line.startswith("+++ "):
            path = line[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            in_target_file = path == file_path
            in_target_hunk = False
            continue
        if not in_target_file:
            continue
        m = HUNK_HEADER_RE.match(line)
        if m:
            old_start = int(m.group(1))
            new_start = int(m.group(3))
            if (
                old_start == target.old_start
                and new_start == target.new_start
                and seen_count == 0
            ):
                in_target_hunk = True
                seen_count += 1
                continue
            elif in_target_hunk:
                break
            else:
                in_target_hunk = False
                continue
        if in_target_hunk:
            out.append(line)
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tasks = []
    with TASKS_JSONL.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))

    n_total = len(tasks)
    n_with_snapshot = 0
    n_with_gold = 0
    n_new_file_only = 0
    n_parse_errors = 0
    n_formatting_only_tasks = 0

    with OUT_PATH.open("w", encoding="utf-8") as out_f:
        for task in tasks:
            rec = extract_gold_for_task(task)
            if rec["snapshot_found"]:
                n_with_snapshot += 1
            if rec["gold_symbols"]:
                n_with_gold += 1
            if rec["gold_symbols"] and all(
                g["kind"] == "new_module" for g in rec["gold_symbols"]
            ):
                n_new_file_only += 1
            if rec["parse_errors"]:
                n_parse_errors += 1
            if rec["gold_symbols"] and all(
                g["formatting_only"] for g in rec["gold_symbols"]
            ):
                n_formatting_only_tasks += 1
            out_f.write(json.dumps(rec) + "\n")

    print(f"tasks total:              {n_total}")
    print(f"snapshot found:           {n_with_snapshot}")
    print(f"gold symbols extracted:   {n_with_gold}")
    print(f"new-file-only tasks:      {n_new_file_only}")
    print(f"AST parse errors (any):   {n_parse_errors}")
    print(f"all-formatting-only:      {n_formatting_only_tasks}")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
