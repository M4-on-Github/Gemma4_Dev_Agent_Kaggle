"""Replace a range of lines in one source file with new text, then print the new region with line numbers.

harness-eng R-026 (sweep lever "line-edit"). It needs no copy of the old text, so an edit cannot fail on a
misquoted anchor. Pure file reads and one file write; it starts no other program and makes no connection.

  args = [path, start_line, end_line, new_text]      (1-based, inclusive; new_text may be empty to delete)
  args = [path, start_line, start_line - 1, text]    inserts text before start_line

The root is found as in change-count. Test files (a tests/test/testing directory, test_*.py, *_test.py,
conftest.py) and paths outside the repository are refused. The file's line ending is kept. At most 300 lines are
replaced in one call. Always ends normally; an error prints one line starting with ERROR and changes nothing.
"""
import os
import re
import sys

MAX_SPAN = 300
CONTEXT = 3


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


def is_test(rel):
    parts = rel.split("/")
    name = parts[-1]
    return (any(p in ("tests", "test", "testing") for p in parts[:-1]) or name.startswith("test_")
            or name.endswith("_test.py") or name == "conftest.py")


def parse(argv):
    keys = {"path": None, "start": None, "end": None, "text": None}
    alias = {"--path": "path", "--file": "path", "--file_path": "path", "--filepath": "path",
             "--start": "start", "--start_line": "start", "--end": "end", "--end_line": "end",
             "--text": "text", "--new_text": "text", "--new_string": "text", "--content": "text"}
    rest, i = [], 0
    while i < len(argv):
        a = argv[i]
        if a == "--":
            i += 1
            continue
        if a in alias and i + 1 < len(argv):
            keys[alias[a]] = argv[i + 1]
            i += 2
            continue
        rest.append(a)
        i += 1
    for k in ("path", "start", "end", "text"):
        if keys[k] is None and rest:
            keys[k] = rest.pop(0)
    return keys


def main():
    k = parse(sys.argv[1:])
    if k["path"] is None or k["start"] is None or k["end"] is None:
        print("ERROR usage: args = [path, start_line, end_line, new_text]")
        return
    if k["text"] is None:
        k["text"] = ""
    try:
        start, end = int(str(k["start"]).strip()), int(str(k["end"]).strip())
    except ValueError:
        print("ERROR start_line and end_line must be integers")
        return
    root = find_root()
    rel = k["path"].strip()
    if rel.startswith("/workspace/"):
        rel = rel[len("/workspace/"):]
    if root is None:
        print("ERROR repository not found")
        return
    path = os.path.abspath(os.path.join(root, rel))
    rel = os.path.relpath(path, root).replace(os.sep, "/")
    if not path.startswith(root + os.sep) or not os.path.isfile(path):
        print("ERROR not a file in the repository: " + k["path"])
        return
    if is_test(rel):
        print("ERROR test files are not edited")
        return
    with open(path, "rb") as f:
        raw = f.read()
    text = raw.decode("utf-8", errors="surrogateescape")
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(eol)
    trailing = lines and lines[-1] == ""
    if trailing:
        lines = lines[:-1]
    n = len(lines)
    if start < 1 or start > n + 1 or end < start - 1 or end > n:
        print("ERROR range %d-%d is outside the file (1-%d)" % (start, end, n))
        return
    if end - start + 1 > MAX_SPAN:
        print("ERROR at most %d lines per call" % MAX_SPAN)
        return
    new = k["text"].replace("\r\n", "\n")
    if new.endswith("\n"):
        new = new[:-1]
    new_lines = new.split("\n") if new != "" else []
    out = lines[:start - 1] + new_lines + lines[end:]
    data = eol.join(out) + (eol if trailing or not out else "")
    with open(path, "wb") as f:
        f.write(data.encode("utf-8", errors="surrogateescape"))
    lo = max(1, start - CONTEXT)
    hi = min(len(out), start - 1 + len(new_lines) + CONTEXT)
    print("OK %s: replaced lines %d-%d (%d lines) with %d lines; the file now has %d lines" % (
        rel, start, end, max(0, end - start + 1), len(new_lines), len(out)))
    for i in range(lo, hi + 1):
        print("%6d  %s" % (i, out[i - 1]))


try:
    main()
except Exception as e:
    print("ERROR replace failed: " + type(e).__name__)
