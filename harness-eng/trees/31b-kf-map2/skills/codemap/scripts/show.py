"""Print the exact text of one function, class or line range, for a bounded number of lookups.

Usage (one string): "path/to/file.py:START-END"  or  "path/to/file.py NAME"  or  "NAME".
The text is printed unchanged, so it can be copied into an edit. After LIMIT lookups in one task the
script prints one line instead. Standard library only; reads files, starts nothing.
"""
import os
import re
import sys
import time

LIMIT, MAX_LINES, WINDOW = 4, 120, 900
SKIP = {".git", "node_modules", "__pycache__", ".tox", ".venv", "venv", "build", "dist", "site-packages"}
DONE = ("NO MORE LOOKUPS IN THIS STEP. Call edit_file now on the code already shown. "
        "An edit in a plausible place beats no edit.")
USAGE = 'Give one string: "path/file.py:START-END" or "path/file.py NAME" or "NAME".'


def find_root():
    seen = []
    for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep) + list(sys.path) + ["/workspace", os.getcwd()]:
        if not entry:
            continue
        path = os.path.abspath(entry)
        if path in seen:
            continue
        seen.append(path)
        if os.path.isdir(os.path.join(path, ".git")):
            return path
    return None


def spend(root):
    """Count this lookup; return how many were used before it (0 when the counter cannot be kept)."""
    path = os.path.join(root, ".git", "codemap.show")
    used = 0
    try:
        if time.time() - os.path.getmtime(path) < WINDOW:
            with open(path) as fh:
                used = int(fh.read().strip() or 0)
    except Exception:
        used = 0
    try:
        with open(path, "w") as fh:
            fh.write(str(used + 1))
    except Exception:
        pass
    return used


def is_test(rel):
    low = rel.lower()
    base = os.path.basename(low)
    return "/tests/" in "/" + low or "/test/" in "/" + low or base.startswith("test_") or base.endswith("_test.py")


def py_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP and not d.startswith("."))
        for name in sorted(filenames):
            if name.endswith(".py"):
                yield os.path.relpath(os.path.join(dirpath, name), root)


def read_lines(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as fh:
        return fh.read().split("\n")


def block_end(lines, start):
    """Last line (1-based) of the def/class that starts at 1-based line `start`."""
    head = lines[start - 1]
    indent = len(head) - len(head.lstrip())
    end = start
    for i in range(start, len(lines)):
        ln = lines[i]
        if ln.strip() and len(ln) - len(ln.lstrip()) <= indent and not ln.lstrip().startswith((")", "]", "}")):
            if i > start and not lines[start - 1].rstrip().endswith(":") and ":" not in "".join(lines[start - 1:i]):
                continue
            break
        if ln.strip():
            end = i + 1
    return end


def find_symbol(root, name, only=None):
    leaf = name.split(".")[-1]
    owner = name.split(".")[-2] if "." in name else None
    pat = re.compile(r"^\s*(?:async\s+def|def|class)\s+%s\b" % re.escape(leaf))
    hits = []
    for rel in ([only] if only else py_files(root)):
        try:
            lines = read_lines(root, rel)
        except Exception:
            continue
        for i, ln in enumerate(lines, 1):
            if pat.match(ln):
                score = 0 if is_test(rel) else 2
                if owner:
                    ind = len(ln) - len(ln.lstrip())
                    for j in range(i - 2, -1, -1):
                        up = lines[j]
                        if up.strip() and len(up) - len(up.lstrip()) < ind:
                            score += 1 if re.match(r"^\s*class\s+%s\b" % re.escape(owner), up) else 0
                            break
                hits.append((-score, rel, i, lines))
    hits.sort(key=lambda h: (h[0], h[1], h[2]))
    return hits


def render(rel, lines, start, end, left, note=""):
    start = max(1, start)
    end = min(len(lines), max(start, end))
    cut = ""
    if end - start + 1 > MAX_LINES:
        end = start + MAX_LINES - 1
        cut = " (cut at %d lines; ask for a later range if needed)" % MAX_LINES
    head = "%s lines %d-%d%s. Exact text, copy it unchanged into old_string. Lookups left: %d.%s" % (
        rel, start, end, cut, left, note)
    return head + "\n" + "\n".join(lines[start - 1:end])


def main():
    try:
        root = find_root()
        text = " ".join(a for a in sys.argv[1:] if a != "--").strip().strip("\"'`")
        if not root or not text:
            print(USAGE)
            return
        used = spend(root)
        if used >= LIMIT:
            print(DONE)
            return
        left = LIMIT - used - 1
        m = re.match(r"^(\S+?\.py)\s*[:#\s]\s*L?(\d+)\s*[-:, ]\s*L?(\d+)$", text)
        if m and os.path.isfile(os.path.join(root, m.group(1).lstrip("/"))):
            rel = m.group(1).lstrip("/")
            print(render(rel, read_lines(root, rel), int(m.group(2)), int(m.group(3)), left))
            return
        parts = text.replace(":", " ").split()
        only = None
        if parts and parts[0].endswith(".py"):
            rel = parts[0].lstrip("/")
            if rel.startswith("workspace/"):
                rel = rel[len("workspace/"):]
            if os.path.isfile(os.path.join(root, rel)):
                only = rel
            parts = parts[1:]
        names = [p for p in parts if re.match(r"^[A-Za-z_][\w.]*$", p) and p not in ("def", "class", "async")]
        if not names:
            if only:
                lines = read_lines(root, only)
                print(render(only, lines, 1, MAX_LINES, left))
            else:
                print(USAGE)
            return
        hits = find_symbol(root, names[-1], only) or (find_symbol(root, names[-1]) if only else [])
        if not hits:
            print("No function or class named %s. Lookups left: %d. %s" % (names[-1], left, USAGE))
            return
        _, rel, line, lines = hits[0]
        note = ""
        if len(hits) > 1:
            note = " Also defined at: " + ", ".join("%s:%d" % (h[1], h[2]) for h in hits[1:4]) + "."
        start = line
        while start > 1 and lines[start - 2].lstrip().startswith("@"):
            start -= 1
        print(render(rel, lines, start, block_end(lines, line), left, note))
    except Exception:
        print(USAGE)


if __name__ == "__main__":
    main()
