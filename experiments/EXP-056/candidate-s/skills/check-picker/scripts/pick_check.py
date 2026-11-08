"""Choose one check command for the files that were just edited.

Reads files under /workspace and prints exactly one line: a test command, or an import
command when no test file fits. It starts no other program, makes no connection, writes
nothing and always ends normally.

The wrapper that runs skill scripts changes into a temporary directory first, so every
path here is built from the fixed workspace root and never from the current directory.
"""
import importlib.util
import os
import re
import sys

ROOT = "/workspace"
SKIP_DIRS = {"__pycache__", "node_modules", "venv", "build", "dist", "site-packages"}
MAX_PY_FILES = 8000
MAX_READ = 300000
ALWAYS_LOCAL = {"tests", "test", "conftest"}


def edited_paths(argv):
    """Collect the .py paths from the arguments, whatever shape the caller used."""
    out = []
    for token in argv[1:]:
        for piece in re.split(r"[\s,;]+", token):
            piece = piece.strip().strip("'\"[]")
            if piece.endswith(".py") and piece not in out:
                out.append(piece)
    return out


def to_rel(path):
    """Workspace-relative form of an edited path, or None when it is not a file there."""
    path = path.replace("\\", "/")
    if path.startswith(ROOT + "/"):
        path = path[len(ROOT) + 1:]
    while path.startswith("./"):
        path = path[2:]
    path = os.path.normpath(path).replace(os.sep, "/")
    if path.startswith("/") or path.startswith(".."):
        return None
    if not os.path.isfile(os.path.join(ROOT, path)):
        return None
    return path


def is_test_path(rel):
    base = os.path.basename(rel)
    parts = rel.split("/")[:-1]
    return (
        base.startswith("test_")
        or base.endswith("_test.py")
        or base == "conftest.py"
        or any(p in ("tests", "test", "testing") for p in parts)
    )


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
                found.append(rel.replace(os.sep, "/"))
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


def main():
    paths = []
    for raw in edited_paths(sys.argv):
        rel = to_rel(raw)
        if rel is not None and not is_test_path(rel) and rel not in paths:
            paths.append(rel)
    if not paths:
        print("python -c \"print('check-picker: pass the workspace paths of the .py files you edited')\"")
        return
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
        print("python -m pytest -q -x " + best[1])
    elif first_dotted is not None:
        print('python -c "import ' + first_dotted + '"')
    else:
        print("python -c \"print('check-picker: no importable module among the edited paths')\"")


if __name__ == "__main__":
    main()
