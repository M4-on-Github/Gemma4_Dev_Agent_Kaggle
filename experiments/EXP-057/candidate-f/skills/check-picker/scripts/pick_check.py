"""Choose one check command for the files that were just edited.

Reads files in the task workspace and prints exactly one line: a test command, or an import
command when no test file fits. It starts no other program, makes no connection, writes
nothing and always ends normally.

EXP-057: the workspace root is found at run time, never from a constant. The wrapper that runs
skill scripts writes its own file into the workspace, starts python there with PYTHONPATH set
to the workspace, and only then changes into a temporary directory, so the current directory is
useless but PYTHONPATH and the first sys.path entry both name the workspace. Candidates are
tried in that order, then the literal /workspace, then the current directory.

Arguments may arrive as a list of plain tokens, as --key value pairs, as -k value pairs, or after
a bare --. Every .py piece found in any of them is read as an edited path. With no usable path
the script falls back to the most recently modified source files in the workspace.
"""
import importlib.util
import os
import re
import sys

ROOT = "/workspace"
LITERAL_ROOT = "/workspace"
SKIP_DIRS = {"__pycache__", "node_modules", "venv", "build", "dist", "site-packages"}
MAX_PY_FILES = 8000
MAX_READ = 300000
ALWAYS_LOCAL = {"tests", "test", "conftest"}
RECENT_WINDOW_S = 300
RECENT_MAX = 3
NOTICE_PREFIX = 'python -c "print('


def norm(path):
    return path.replace("\\", "/")


def edited_paths(argv):
    """Collect the .py paths from the arguments, whatever shape the caller used."""
    out = []
    for token in argv[1:]:
        for piece in re.split(r"[\s,;]+", token):
            piece = piece.strip().strip("'\"[]{}()")
            if piece.endswith(".py") and piece not in out:
                out.append(piece)
    return out


def is_library_dir(path):
    parts = norm(path).split("/")
    if "site-packages" in parts or "dist-packages" in parts:
        return True
    if os.path.isfile(os.path.join(path, "os.py")):
        return True
    for prefix in {sys.prefix, sys.base_prefix, sys.exec_prefix}:
        lib = norm(os.path.join(prefix, "lib"))
        if norm(path).startswith(lib + "/") or norm(path) == lib:
            return True
    return False


def candidate_roots():
    """Directories that may be the workspace, most likely first."""
    out = []

    def add(path):
        if not path:
            return
        path = os.path.abspath(path)
        if path in out or not os.path.isdir(path):
            return
        if is_library_dir(path):
            return
        for own in (("scripts", "pick_check.py"), ("pick_check.py",)):
            if os.path.isfile(os.path.join(path, *own)):
                return
        out.append(path)

    for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep):
        add(entry)
    for entry in sys.path:
        add(entry)
    add(LITERAL_ROOT)
    add(os.getcwd())
    return out


def strip_root(path, root):
    """Workspace-relative form of a path string, or None when it points outside."""
    path = norm(path)
    for prefix in (norm(root).rstrip("/"), LITERAL_ROOT):
        if path.startswith(prefix + "/"):
            path = path[len(prefix) + 1:]
            break
    while path.startswith("./"):
        path = path[2:]
    if path.startswith("/") or re.match(r"^[A-Za-z]:", path):
        return None
    path = norm(os.path.normpath(path))
    if path.startswith("..") or path in ("", "."):
        return None
    return path


def to_rel(path, root=None):
    """Workspace-relative form of an edited path, or None when it is not a file there."""
    root = ROOT if root is None else root
    rel = strip_root(path, root)
    if rel is None or not os.path.isfile(os.path.join(root, rel)):
        return None
    return rel


def has_py(root):
    seen = 0
    for _dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        if any(n.endswith(".py") for n in filenames):
            return True
        seen += 1
        if seen > 400:
            break
    return False


def pick_root(raw_paths):
    """The workspace: the first candidate that holds a named edited file, else the first with sources."""
    roots = candidate_roots()
    for root in roots:
        for raw in raw_paths:
            if to_rel(raw, root) is not None:
                return root
    for root in roots:
        if has_py(root):
            return root
    return roots[0] if roots else LITERAL_ROOT


def is_test_path(rel):
    base = os.path.basename(rel)
    parts = rel.split("/")[:-1]
    return (
        base.startswith("test_")
        or base.endswith("_test.py")
        or base == "conftest.py"
        or any(p in ("tests", "test", "testing") for p in parts)
    )


def newest_sources():
    """The most recently modified non-test .py files, newest first (the edited file is the newest)."""
    entries = []
    seen = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            if not name.endswith(".py") or name.startswith("."):
                continue
            seen += 1
            full = os.path.join(dirpath, name)
            rel = norm(os.path.relpath(full, ROOT))
            if is_test_path(rel):
                continue
            try:
                entries.append((os.stat(full).st_mtime, rel))
            except OSError:
                pass
        if seen > MAX_PY_FILES:
            break
    if not entries:
        return []
    entries.sort(key=lambda e: (-e[0], e[1]))
    top = entries[0][0]
    return [rel for mtime, rel in entries[:RECENT_MAX] if top - mtime <= RECENT_WINDOW_S]


def module_info(rel):
    """Return (stem, dotted import name) for a source file."""
    parts = rel[:-3].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts:
        return None
    stem = parts[-1]
    start = len(parts) - 1
    i = len(parts) - 2
    while i >= 0 and os.path.isfile(os.path.join(ROOT, *parts[: i + 1], "__init__.py")):
        start = i
        i -= 1
    if start == len(parts) - 1 and len(parts) > 1 and parts[0] in ("src", "lib"):
        start = 1
    return stem, ".".join(parts[start:])


def find_tests():
    found = []
    seen = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            seen += 1
            if name.startswith("test_") or name.endswith("_test.py"):
                rel = os.path.relpath(os.path.join(dirpath, name), ROOT)
                found.append(norm(rel))
        if seen > MAX_PY_FILES:
            break
    return found


def read_text(rel):
    try:
        with open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace") as handle:
            return handle.read(MAX_READ)
    except OSError:
        return ""


def name_score(test_rel, stem):
    base = os.path.basename(test_rel)[:-3]
    if base.startswith("test_"):
        base = base[5:]
    elif base.endswith("_test"):
        base = base[:-5]
    t = base.lstrip("_").lower()
    s = stem.lstrip("_").lower()
    if len(s) < 3:
        return 0
    if t == s:
        return 100
    if s in t:
        return 60
    if len(t) >= 4 and t in s:
        return 40
    if s in test_rel.lower().split("/")[:-1]:
        return 30
    return 0


def import_score(text, dotted, stem):
    best = 0
    if "." in dotted:
        if re.search(r"^[ \t]*(?:from|import)[ \t]+" + re.escape(dotted) + r"\b", text, re.M):
            best = 50
        parent = dotted.rsplit(".", 1)[0]
        pattern = (
            r"^[ \t]*from[ \t]+" + re.escape(parent) + r"[ \t]+import[ \t]+[^\n]*\b"
            + re.escape(stem) + r"\b"
        )
        if re.search(pattern, text, re.M):
            best = max(best, 45)
        if dotted in text:
            best = max(best, 30)
    elif re.search(r"^[ \t]*(?:from|import)[ \t]+" + re.escape(dotted) + r"\b", text, re.M):
        best = 40
    return best


def local_names(test_rel):
    names = set(ALWAYS_LOCAL)
    places = [ROOT, os.path.join(ROOT, "src"), os.path.join(ROOT, os.path.dirname(test_rel))]
    for place in places:
        try:
            for entry in os.listdir(place):
                names.add(entry[:-3] if entry.endswith(".py") else entry)
        except OSError:
            pass
    return names


def missing_imports(test_rel):
    """Top-level imports of the test file and its conftest files that this interpreter cannot find."""
    texts = [read_text(test_rel)]
    folder = os.path.dirname(test_rel)
    while True:
        conf = os.path.join(folder, "conftest.py") if folder else "conftest.py"
        if os.path.isfile(os.path.join(ROOT, conf)):
            texts.append(read_text(conf))
        if not folder:
            break
        folder = os.path.dirname(folder)
    local = local_names(test_rel)
    missing = []
    for text in texts:
        for name in re.findall(r"^(?:from|import)[ \t]+([A-Za-z_]\w*)", text, re.M):
            if name in local or name in getattr(sys, "stdlib_module_names", ()) or name in missing:
                continue
            try:
                found = importlib.util.find_spec(name)
            except Exception:
                found = True
            if found is None:
                missing.append(name)
    return missing


def choose(paths):
    """One command line for the given workspace-relative source paths."""
    tests = find_tests()
    texts = {}
    best = None
    first_dotted = None
    for rel in paths:
        info = module_info(rel)
        if info is None:
            continue
        stem, dotted = info
        if first_dotted is None:
            first_dotted = dotted
        for test in tests:
            n = name_score(test, stem)
            if test not in texts:
                texts[test] = read_text(test)
            i = import_score(texts[test], dotted, stem)
            if n == 0 and i == 0:
                continue
            key = (n, i, -len(test))
            if best is None or key > best[0]:
                if not missing_imports(test):
                    best = (key, test)
    if best is not None:
        return "python -m pytest -q -x " + best[1]
    if first_dotted is not None:
        return 'python -c "import ' + first_dotted + '"'
    return NOTICE_PREFIX + "'check-picker: no importable module among the edited paths')\""


def main():
    global ROOT
    raw = edited_paths(sys.argv)
    ROOT = pick_root(raw)
    paths = []
    for item in raw:
        rel = to_rel(item)
        if rel is not None and not is_test_path(rel) and rel not in paths:
            paths.append(rel)
    if not paths:
        paths = newest_sources()
    if not paths:
        print(NOTICE_PREFIX + "'check-picker: no .py source file found in the workspace')\"")
        return
    print(choose(paths))


if __name__ == "__main__":
    main()
