"""Print how many source files differ from the task's baseline commit, as one integer.

harness-eng R-020 (fix 1 of the retry smoke). The root agent calls this between attempts instead of a shell command,
so it has no tool with which to work on the issue itself. Pure file reads: it reads the git index and the baseline
commit object directly, starts no other program, makes no connection, writes nothing and always ends normally.

- Tracked files: a file counts when it is gone, or when its content hash differs from the blob hash the index holds
  (stat fields are compared first so unchanged files are not hashed).
- New files: a file absent from the index counts when it was modified after the baseline commit time. Dot
  directories, __pycache__, virtual environments and compiled or log files are skipped.
- Dot files and directories, caches and compiled or log files are skipped everywhere.
- Test paths are left out as the grader leaves them out: a tests/test/testing directory, test_*.py, *_test.py,
  conftest.py.
- On any read error it prints 1, so an unreadable state never triggers another attempt.
The workspace is found as in EXP-057: PYTHONPATH entries, then sys.path, then /workspace, then the current directory.
"""
import hashlib
import os
import re
import struct
import sys
import zlib

TEST_DIRS = ("tests", "test", "testing")
JUNK_EXT = (".pyc", ".pyo", ".log", ".db", ".sqlite", ".sqlite3", ".coverage", ".orig", ".rej")
SKIP_DIRS = ("__pycache__", "node_modules", "site-packages", "dist-packages")


def is_test(path):
    parts = path.split("/")
    name = parts[-1]
    if name == "conftest.py":
        return True
    if name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py")):
        return True
    return any(p in TEST_DIRS for p in parts[:-1])


def is_junk(path):
    parts = path.split("/")
    if any(p.startswith(".") or p in SKIP_DIRS or p.endswith(".egg-info") for p in parts):
        return True
    return parts[-1].endswith(JUNK_EXT)


def find_root():
    seen = []
    for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep) + list(sys.path) + ["/workspace", os.getcwd()]:
        if not entry:
            continue
        path = os.path.abspath(entry)
        if path in seen:
            continue
        seen.append(path)
        if os.path.isfile(os.path.join(path, ".git", "index")):
            return path
    return None


def read_index(git):
    with open(os.path.join(git, "index"), "rb") as f:
        data = f.read()
    if data[:4] != b"DIRC":
        raise ValueError("index")
    version, count = struct.unpack(">II", data[4:12])
    if version not in (2, 3):
        raise ValueError("index version")
    out = {}
    pos = 12
    for _ in range(count):
        mtime_s, mtime_ns = struct.unpack(">II", data[pos + 8:pos + 16])
        mode = struct.unpack(">I", data[pos + 24:pos + 28])[0]
        size = struct.unpack(">I", data[pos + 36:pos + 40])[0]
        sha = data[pos + 40:pos + 60]
        flags = struct.unpack(">H", data[pos + 60:pos + 62])[0]
        head = 62
        if version == 3 and flags & 0x4000:
            head += 2
        end = data.index(b"\0", pos + head)
        path = data[pos + head:end].decode("utf-8", "surrogateescape")
        if not (version == 3 and flags & 0x4000 and struct.unpack(">H", data[pos + 62:pos + 64])[0] & 0x2000):
            out[path] = (mtime_s, size, sha, mode)   # intent-to-add entries are left to the new-file walk
        pos += ((head + len(path.encode("utf-8", "surrogateescape")) + 8) // 8) * 8
    return out


def baseline_time(git):
    ref = os.path.join(git, "refs", "tags", "_swegemma_baseline")
    try:
        with open(ref) as f:
            sha = f.read().strip()
        with open(os.path.join(git, "objects", sha[:2], sha[2:]), "rb") as f:
            obj = zlib.decompress(f.read())
        m = re.search(rb"\ncommitter [^\n]*> (\d+) [+-]\d{4}", obj)
        if m:
            return int(m.group(1))
    except (OSError, ValueError, zlib.error):
        pass
    try:
        return int(os.path.getmtime(ref))
    except OSError:
        return None


def blob_sha(path):
    with open(path, "rb") as f:
        body = f.read()
    return hashlib.sha1(b"blob %d\0" % len(body) + body).digest()


def count(root):
    git = os.path.join(root, ".git")
    index = read_index(git)
    n = 0
    for rel, (mtime_s, size, sha, mode) in index.items():
        if is_test(rel) or is_junk(rel) or (mode >> 12) == 0o16:   # gitlinks
            continue
        full = os.path.join(root, rel)
        try:
            st = os.lstat(full)
        except OSError:
            n += 1
            continue
        if (mode >> 12) == 0o12:   # symlink: compare by target
            continue
        if st.st_size == size and int(st.st_mtime) == mtime_s:
            continue
        try:
            if blob_sha(full) != sha:
                n += 1
        except OSError:
            n += 1
    base = baseline_time(git)
    if base is None:
        return n
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS and not d.endswith(".egg-info")
                       and not os.path.isfile(os.path.join(dirpath, d, "pyvenv.cfg"))]
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            if rel in index or is_test(rel) or is_junk(rel):
                continue
            try:
                if os.lstat(full).st_mtime > base + 1:
                    n += 1
            except OSError:
                pass
    return n


def main():
    try:
        root = find_root()
        print(count(root) if root else 1)
    except Exception:   # never fail the caller; an unreadable state means no further attempt
        print(1)


if __name__ == "__main__":
    main()
