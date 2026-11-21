"""Decide whether another attempt is needed, and pick the attempt to keep.

Reads the saved attempts .git/cand_1.diff, .git/cand_2.diff, ... in the task workspace and prints exactly one word:
NEXT when one more attempt should run, APPLY when .git/chosen.diff now holds the attempt to keep. It reads and
writes only inside the workspace's .git directory, starts no other program, makes no connection and always ends
normally.

Policy (harness-eng R-019): an attempt counts only by the source files it changes (test files and test configs are
left out, as the grader leaves them out). After two attempts that both change the same set of files, the smaller
of the two is kept. Otherwise a third attempt runs, and the file set that most attempts share wins; a tie goes to
the smallest attempt, then the earliest. When no attempt changes a source file, chosen.diff is empty.

The workspace root is found at run time, as in EXP-057: the PYTHONPATH entries, then sys.path, then the literal
/workspace, then the current directory; the first that holds .git/cand_1.diff.
"""
import os
import re
import sys

MAX_ATTEMPTS = 3
PROTECTED_NAMES = ("conftest.py", "pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg", ".pytest.ini",
                   "sitecustomize.py", "usercustomize.py")
TEST_DIRS = ("tests", "test", "testing")


def is_protected(path):
    parts = path.split("/")
    name = parts[-1]
    if name in PROTECTED_NAMES or name.endswith(".pth"):
        return True
    if name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py")):
        return True
    if name.endswith(".py") and any(p in TEST_DIRS for p in parts[:-1]):
        return True
    return False


def find_root():
    seen = []
    for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep) + list(sys.path) + ["/workspace", os.getcwd()]:
        if not entry:
            continue
        path = os.path.abspath(entry)
        if path in seen:
            continue
        seen.append(path)
        if os.path.isfile(os.path.join(path, ".git", "cand_1.diff")):
            return path
    return None


def sections(text):
    """Split a git diff into (path, section text) pairs."""
    out = []
    cur_path, cur = None, []
    for line in text.splitlines(True):
        if line.startswith("diff --git "):
            if cur_path is not None:
                out.append((cur_path, "".join(cur)))
            m = re.match(r"diff --git a/(\S+) b/(\S+)", line)
            cur_path = m.group(2) if m else ""
            cur = [line]
        elif cur_path is not None:
            cur.append(line)
    if cur_path is not None:
        out.append((cur_path, "".join(cur)))
    return out


def load(path):
    try:
        with open(path, encoding="latin-1", newline="") as f:   # byte-exact both ways
            text = f.read()
    except OSError:
        text = ""
    src = [(p, s) for p, s in sections(text) if p and not is_protected(p)]
    files = tuple(sorted(p for p, _ in src))
    size = sum(len(s) for _, s in src)
    return files, size, text


def choose(cands):
    """cands: list of (files, size, text) in attempt order. Returns (decision, text to keep or None)."""
    real = [(i, c) for i, c in enumerate(cands) if c[0]]
    n = len(cands)
    if n == 2 and len(real) == 2 and real[0][1][0] == real[1][1][0]:
        i, c = min(real, key=lambda ic: (ic[1][1], ic[0]))
        return "APPLY", c[2]
    if n < MAX_ATTEMPTS:
        return "NEXT", None
    if not real:
        return "APPLY", ""
    votes = {}
    for _, c in real:
        votes[c[0]] = votes.get(c[0], 0) + 1
    i, c = min(real, key=lambda ic: (-votes[ic[1][0]], ic[1][1], ic[0]))
    return "APPLY", c[2]


def main():
    root = find_root()
    if root is None:
        print("APPLY")
        return
    git = os.path.join(root, ".git")
    cands = []
    k = 1
    while os.path.isfile(os.path.join(git, "cand_%d.diff" % k)):
        cands.append(load(os.path.join(git, "cand_%d.diff" % k)))
        k += 1
    decision, text = choose(cands)
    if decision == "APPLY":
        try:
            with open(os.path.join(git, "chosen.diff"), "w", encoding="latin-1", newline="") as f:
                f.write(text or "")
        except OSError:
            pass
    print(decision)


if __name__ == "__main__":
    main()
