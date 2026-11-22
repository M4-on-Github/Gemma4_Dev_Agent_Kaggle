"""Print lines of one file with their line numbers, at most 120 lines per call.

harness-eng R-026 (sweep lever "line-edit"): the numbers to pass to replace.py. Pure file reads.
  args = [path, start_line, end_line]
"""
import os
import sys

MAX = 120


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


def main():
    argv = [a for a in sys.argv[1:] if a != "--"]
    flags = {}
    plain = []
    i = 0
    while i < len(argv):
        if argv[i].startswith("--") and i + 1 < len(argv):
            flags[argv[i].lstrip("-")] = argv[i + 1]
            i += 2
        else:
            plain.append(argv[i])
            i += 1
    rel = flags.get("path") or flags.get("file_path") or flags.get("file") or (plain.pop(0) if plain else None)
    s = flags.get("start") or flags.get("start_line") or (plain.pop(0) if plain else "1")
    e = flags.get("end") or flags.get("end_line") or (plain.pop(0) if plain else None)
    root = find_root()
    if not rel or root is None:
        print("ERROR usage: args = [path, start_line, end_line]")
        return
    if rel.startswith("/workspace/"):
        rel = rel[len("/workspace/"):]
    path = os.path.abspath(os.path.join(root, rel))
    if not path.startswith(root + os.sep) or not os.path.isfile(path):
        print("ERROR not a file in the repository: " + rel)
        return
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    try:
        start = max(1, int(s))
        end = min(len(lines), int(e) if e is not None else start + MAX - 1, start + MAX - 1)
    except ValueError:
        print("ERROR start_line and end_line must be integers")
        return
    print("%s: lines %d-%d of %d" % (rel, start, end, len(lines)))
    for i in range(start, end + 1):
        print("%6d  %s" % (i, lines[i - 1]))


try:
    main()
except Exception as ex:
    print("ERROR show failed: " + type(ex).__name__)
