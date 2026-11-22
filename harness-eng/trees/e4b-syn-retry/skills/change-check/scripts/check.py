"""Print how many source files differ from the task's baseline commit, or the first syntax error among them.

harness-eng R-029 2026-11-22 (syntax trigger). Built on change-count (R-020): the same changed-file rules, pure file
reads, no other program, no connection, nothing written, always ends normally. It also runs the builtin compile() on
every changed or new .py source file. Output, one line:
- `0` when no source file changed;
- `syntax error in PATH line N` for the first changed source file that does not parse (PATH relative to the
  workspace), unless the baseline version of that file, when it is a loose object, does not parse either;
- otherwise the number of changed source files.
Desk check (rounds/R-029): a final patch that leaves a changed source file unparseable resolved 0 of 103 E4B
task-draws (R-021 retry x12) and 0 of 67 (R-021 control x12).
On any read error it prints 1, so an unreadable state never triggers another attempt.
"""
import warnings
warnings.simplefilter("ignore")
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


def parses(body):
    try:
        compile(body, "x", "exec", dont_inherit=True)
        return None
    except (SyntaxError, ValueError) as e:
        return getattr(e, "lineno", None) or 0


def loose_blob(git, sha):
    try:
        h = sha.hex()
        with open(os.path.join(git, "objects", h[:2], h[2:]), "rb") as f:
            obj = zlib.decompress(f.read())
        return obj[obj.index(b"\0") + 1:]
    except (OSError, ValueError, zlib.error):
        return None


def broken(root, git, rel, sha):
    if not rel.endswith(".py"):
        return None
    try:
        with open(os.path.join(root, rel), "rb") as f:
            line = parses(f.read())
    except OSError:
        return None
    if line is None:
        return None
    if sha is not None:
        base = loose_blob(git, sha)
        if base is not None and parses(base) is not None:
            return None   # the baseline does not parse under this interpreter either
    return "syntax error in %s line %d" % (rel, line)


def count(root):
    git = os.path.join(root, ".git")
    index = read_index(git)
    n = 0
    changed = []
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
                changed.append((rel, sha))
        except OSError:
            n += 1
    base = baseline_time(git)
    if base is None:
        return report(root, git, n, changed)
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
                    changed.append((rel, None))
            except OSError:
                pass
    return report(root, git, n, changed)


def report(root, git, n, changed):
    for rel, sha in sorted(changed):
        msg = broken(root, git, rel, sha)
        if msg:
            return msg
    return n


def main():
    try:
        root = find_root()
        print(count(root) if root else 1)
    except Exception:   # never fail the caller; an unreadable state means no further attempt
        print(1)


if __name__ == "__main__":
    main()
