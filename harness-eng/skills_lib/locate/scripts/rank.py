"""Rank the repository's source files against the issue text and print one solver request line.

harness-eng R-027. The E4B root copies the opening sentences of the issue into `args`; this script scores every
source file with BM25 (identifier words and their snake/camel parts, the path counted three times) and prints

  Resolve the issue in /workspace. The source files that best match the issue, best first: a.py, b.py, ...

Pure file reads: it starts no other program, makes no connection and writes nothing. Test files, documentation,
example, benchmark and script directories, dot directories and virtual environments are left out. On any error, or
when nothing matches, it prints the plain request "Resolve the issue in /workspace." and ends normally.
The workspace is found as in count.py: PYTHONPATH entries, then sys.path, then /workspace, then the current directory.
"""
import collections
import math
import os
import re
import sys

TOP = 5
PLAIN = "Resolve the issue in /workspace."
MAX_FILES = 6000
MAX_BYTES = 400_000
TEST_DIRS = ("tests", "test", "testing")
SKIP_DIRS = ("__pycache__", "node_modules", "site-packages", "dist-packages", "scripts", "examples", "example",
             "benchmarks", "benchmark")
WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
SPLIT = re.compile(r"_|(?<=[a-z0-9])(?=[A-Z])")
STOP = set("the a an and or of to in is it be this that for on with as are was not by if from at but we can when use "
           "used using have has which".split())


def toks(text):
    out = []
    for w in WORD.findall(text):
        lw = w.lower()
        if len(lw) > 2 and lw not in STOP:
            out.append(lw)
        parts = [p.lower() for p in SPLIT.split(w) if len(p) > 2]
        if len(parts) > 1:
            out.extend(p for p in parts if p not in STOP)
    return out


def skip_dir(dirpath, d):
    return (d.startswith(".") or d in SKIP_DIRS or d.startswith("doc") or d.endswith(".egg-info") or d in TEST_DIRS
            or os.path.isfile(os.path.join(dirpath, d, "pyvenv.cfg")))


def is_test(name):
    return name == "conftest.py" or name.startswith("test_") or name.endswith("_test.py")


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


def rank(root, query):
    docs = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not skip_dir(dirpath, d))
        for name in sorted(filenames):
            if not name.endswith(".py") or is_test(name):
                continue
            full = os.path.join(dirpath, name)
            try:
                if os.path.getsize(full) > MAX_BYTES:
                    continue
                with open(full, encoding="utf-8", errors="replace") as f:
                    txt = f.read()
            except OSError:
                continue
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            docs[rel] = collections.Counter(toks(txt) + toks(rel.replace("/", " ").replace(".py", "")) * 3)
            if len(docs) >= MAX_FILES:
                break
        if len(docs) >= MAX_FILES:
            break
    if not docs:
        return []
    n = len(docs)
    df = collections.Counter(w for c in docs.values() for w in c)
    avg = sum(sum(c.values()) for c in docs.values()) / n
    q = collections.Counter(toks(query))
    scores = {}
    for rel, c in docs.items():
        length = sum(c.values())
        s = 0.0
        for w in q:
            if w in c:
                idf = math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5))
                s += idf * c[w] * 2.2 / (c[w] + 1.2 * (0.25 + 0.75 * length / avg))
        if s > 0:
            scores[rel] = s
    return sorted(scores, key=lambda r: (-scores[r], r))[:TOP]


def main():
    try:
        query = " ".join(a for a in sys.argv[1:] if a != "--")
        root = find_root()
        files = rank(root, query) if root and query.strip() else []
        if files:
            print(f"{PLAIN} The source files that best match the issue, best first: {', '.join(files)}.")
        else:
            print(PLAIN)
    except Exception:   # never fail the caller
        print(PLAIN)


if __name__ == "__main__":
    main()
