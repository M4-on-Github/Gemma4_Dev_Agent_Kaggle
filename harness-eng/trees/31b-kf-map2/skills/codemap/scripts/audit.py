"""List the functions the draft changed and the related sites it did not change.

harness-eng R-039. Called with no arguments between the draft step and the finish step. It prints

  CHANGED by the draft:
  path:first-last kind name
  RELATED SITES NOT CHANGED ...
  path:first-last kind name -- why it is related

or, when no source file differs from the baseline, the line NO DRAFT EDIT and a hint.

Pure file reads: the changed files come from the git index (as in the change-count skill), their baseline text
from the git object store (loose objects and pack files, read here in Python), the definitions from the standard
ast module. It starts no other program, makes no connection, writes nothing and always ends normally.

Related sites are ordered by how often each relation held between the sites of one fix when measured offline:
near-duplicate bodies, the same method across the class family, overloads and sync/async twins, the same name
elsewhere, users of a distinctive name, then the distinctive names it uses. A time guard stops the scan early instead of running long.
"""
import ast
import bisect
import collections
import hashlib
import os
import re
import struct
import sys
import time
import zlib

T0 = time.time()
SCAN_SECONDS = 8.0       # pass over the repository stops after this
PARSE_SECONDS = 14.0     # no more files are parsed for related sites after this
MAX_LINES = 10
MAX_CHARS = 2500
MAX_BYTES = 400_000
SIM_MIN = 0.55
NO_EDIT = ("NO DRAFT EDIT\nNo source file differs from the baseline. Edit the best-matching function from the code "
           "map now.")
TEST_DIRS = ("tests", "test", "testing")
SKIP_DIRS = ("__pycache__", "node_modules", "site-packages", "dist-packages", "build", "dist", "vendor", "vendored",
             "_vendor", "third_party", "venv")
WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
DEF_RE = re.compile(r"^[ \t]*(?:async[ \t]+)?(def|class)[ \t]+([A-Za-z_][A-Za-z0-9_]*)[ \t]*(\([^)\n]*\))?", re.M)


def is_test(path):
    parts = path.split("/")
    name = parts[-1]
    if name == "conftest.py" or (name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py"))):
        return True
    return any(p in TEST_DIRS for p in parts[:-1])


def is_junk(path):
    parts = path.split("/")
    return any(p.startswith(".") or p in SKIP_DIRS or p.endswith(".egg-info") for p in parts)


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


# ---- git, read directly ------------------------------------------------------------------------------------------

def read_index(git):
    with open(os.path.join(git, "index"), "rb") as f:
        data = f.read()
    if data[:4] != b"DIRC":
        raise ValueError("index")
    version, count = struct.unpack(">II", data[4:12])
    if version not in (2, 3):
        raise ValueError("index version")
    out, pos = {}, 12
    for _ in range(count):
        mtime_s = struct.unpack(">I", data[pos + 8:pos + 12])[0]
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
            out[path] = (mtime_s, size, sha, mode)
        pos += ((head + len(path.encode("utf-8", "surrogateescape")) + 8) // 8) * 8
    return out


class Objects:
    """Blob contents by hash: loose objects first, then version-2 pack indexes with offset and reference deltas."""

    def __init__(self, git):
        self.dir = os.path.join(git, "objects")
        self.packs = None

    def _load_packs(self):
        self.packs = []
        pdir = os.path.join(self.dir, "pack")
        try:
            names = sorted(n for n in os.listdir(pdir) if n.endswith(".idx"))
        except OSError:
            names = []
        for n in names:
            try:
                with open(os.path.join(pdir, n), "rb") as f:
                    idx = f.read()
                if idx[:8] != b"\377tOc\0\0\0\2":
                    continue
                total = struct.unpack(">I", idx[8 + 255 * 4:8 + 256 * 4])[0]
                self.packs.append((os.path.join(pdir, n[:-4] + ".pack"), idx, total))
            except OSError:
                continue

    def _find(self, sha):
        if self.packs is None:
            self._load_packs()
        for pack, idx, total in self.packs:
            first = sha[0]
            lo = struct.unpack(">I", idx[8 + (first - 1) * 4:12 + (first - 1) * 4])[0] if first else 0
            hi = struct.unpack(">I", idx[8 + first * 4:12 + first * 4])[0]
            base = 8 + 1024
            while lo < hi:
                mid = (lo + hi) // 2
                cur = idx[base + mid * 20:base + mid * 20 + 20]
                if cur == sha:
                    off_pos = base + total * 24 + mid * 4
                    off = struct.unpack(">I", idx[off_pos:off_pos + 4])[0]
                    if off & 0x80000000:
                        big = base + total * 28 + (off & 0x7FFFFFFF) * 8
                        off = struct.unpack(">Q", idx[big:big + 8])[0]
                    return pack, off
                if cur < sha:
                    lo = mid + 1
                else:
                    hi = mid
        return None

    @staticmethod
    def _inflate(f):
        d, out = zlib.decompressobj(), []
        while not d.eof:
            chunk = f.read(65536)
            if not chunk:
                break
            out.append(d.decompress(chunk))
        return b"".join(out)

    def _pack_object(self, pack, off, depth=0):
        if depth > 60:
            raise ValueError("delta chain")
        with open(pack, "rb") as f:
            f.seek(off)
            c = f.read(1)[0]
            kind, shift = (c >> 4) & 7, 4
            while c & 0x80:
                c = f.read(1)[0]
                shift += 7
            if kind in (1, 2, 3, 4):
                return self._inflate(f)
            if kind == 6:
                c = f.read(1)[0]
                rel = c & 0x7F
                while c & 0x80:
                    c = f.read(1)[0]
                    rel = ((rel + 1) << 7) | (c & 0x7F)
                delta = self._inflate(f)
                base = self._pack_object(pack, off - rel, depth + 1)
            elif kind == 7:
                ref = f.read(20)
                delta = self._inflate(f)
                base = self.raw(ref, depth + 1)
            else:
                raise ValueError("object type")
        return apply_delta(base, delta)

    def raw(self, sha, depth=0):
        hexsha = sha.hex()
        try:
            with open(os.path.join(self.dir, hexsha[:2], hexsha[2:]), "rb") as f:
                obj = zlib.decompress(f.read())
            return obj[obj.index(b"\0") + 1:]
        except OSError:
            pass
        hit = self._find(sha)
        if hit is None:
            raise KeyError(hexsha)
        return self._pack_object(hit[0], hit[1], depth)


def apply_delta(base, delta):
    pos = 0

    def varint():
        nonlocal pos
        v = shift = 0
        while True:
            c = delta[pos]
            pos += 1
            v |= (c & 0x7F) << shift
            shift += 7
            if not c & 0x80:
                return v
    varint()
    varint()
    out = []
    while pos < len(delta):
        c = delta[pos]
        pos += 1
        if c & 0x80:
            off = size = 0
            for i in range(4):
                if c & (1 << i):
                    off |= delta[pos] << (8 * i)
                    pos += 1
            for i in range(3):
                if c & (0x10 << i):
                    size |= delta[pos] << (8 * i)
                    pos += 1
            out.append(base[off:off + (size or 0x10000)])
        else:
            out.append(delta[pos:pos + c])
            pos += c
    return b"".join(out)


def baseline_time(git):
    ref = os.path.join(git, "refs", "tags", "_swegemma_baseline")
    try:
        return int(os.path.getmtime(ref))
    except OSError:
        try:
            return int(os.path.getmtime(os.path.join(git, "index")))
        except OSError:
            return None


def changed_files(root):
    """[(path, baseline text or None, state)] for non-test .py files that differ from the index."""
    git = os.path.join(root, ".git")
    index = read_index(git)
    objects = Objects(git)
    out = []
    for rel, (mtime_s, size, sha, mode) in index.items():
        if not rel.endswith(".py") or is_test(rel) or is_junk(rel) or (mode >> 12) != 0o10:
            continue
        full = os.path.join(root, rel)
        try:
            st = os.lstat(full)
        except OSError:
            out.append((rel, None, "deleted"))
            continue
        if st.st_size == size and int(st.st_mtime) == mtime_s:
            continue
        try:
            with open(full, "rb") as f:
                body = f.read()
        except OSError:
            continue
        if hashlib.sha1(b"blob %d\0" % len(body) + body).digest() == sha:
            continue
        try:
            old = objects.raw(sha).decode("utf-8", "replace")
        except Exception:
            old = None
        out.append((rel, old, "changed"))
    base = baseline_time(git)
    if base is not None:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS
                           and not d.endswith(".egg-info") and d not in TEST_DIRS
                           and not os.path.isfile(os.path.join(dirpath, d, "pyvenv.cfg"))]
            for name in filenames:
                if not name.endswith(".py") or name.startswith("."):
                    continue
                rel = os.path.relpath(os.path.join(dirpath, name), root).replace(os.sep, "/")
                if rel in index or is_test(rel):
                    continue
                try:
                    if os.lstat(os.path.join(dirpath, name)).st_mtime > base + 1:
                        out.append((rel, None, "new file"))
                except OSError:
                    pass
            if time.time() - T0 > SCAN_SECONDS:
                break
    return sorted(out)


def changed_ranges(old, new):
    """Line ranges of the new text that differ from the old text; a deletion is the two lines around it."""
    a, b = old.splitlines(), new.splitlines()
    pre = 0
    while pre < len(a) and pre < len(b) and a[pre] == b[pre]:
        pre += 1
    suf = 0
    while suf < len(a) - pre and suf < len(b) - pre and a[-1 - suf] == b[-1 - suf]:
        suf += 1
    am, bm = a[pre:len(a) - suf], b[pre:len(b) - suf]
    if not am and not bm:
        return []
    if len(am) * len(bm) > 4_000_000 or not am or not bm:
        blocks = [(0, len(bm))]
    else:
        import difflib
        blocks = [(j1, j2) for tag, _, _, j1, j2 in
                  difflib.SequenceMatcher(None, am, bm, autojunk=False).get_opcodes() if tag != "equal"]
    out = []
    for j1, j2 in blocks:
        lo, hi = pre + j1 + 1, pre + j2
        if hi < lo:                       # pure deletion between new lines lo-1 and lo
            lo, hi = max(lo - 1, 1), min(lo, len(b))
        out.append((lo, max(hi, lo)))
    return out


# ---- definitions and the repository scan -------------------------------------------------------------------------

def ast_defs(src):
    out = []

    def walk(node, prefix, cls, in_func):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                is_cls = isinstance(ch, ast.ClassDef)
                start = min([ch.lineno] + [d.lineno for d in ch.decorator_list])
                out.append({"name": ch.name, "qual": prefix + ch.name, "start": start, "end": ch.end_lineno,
                            "kind": "class" if is_cls else ("async def" if isinstance(ch, ast.AsyncFunctionDef)
                                                            else "def"),
                            "cls": cls, "nested": in_func})
                walk(ch, prefix + ch.name + ".", ch.name if is_cls else cls, in_func or not is_cls)
            else:
                walk(ch, prefix, cls, in_func)
    walk(ast.parse(src), "", "", False)
    return out


def scan_defs(src):
    """Indent-based fallback for files that do not parse."""
    lines, out, stack = src.splitlines(), [], []
    pat = re.compile(r"^([ \t]*)(async[ \t]+def|def|class)[ \t]+([A-Za-z_][A-Za-z0-9_]*)")
    for i, line in enumerate(lines, 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        ind = len(line) - len(line.lstrip())
        while stack and ind <= stack[-1][0]:
            stack.pop()[1]["end"] = i - 1
        m = pat.match(line)
        if m:
            kind = "class" if m.group(2) == "class" else ("def" if m.group(2) == "def" else "async def")
            cls = next((d["name"] for _, d in reversed(stack) if d["kind"] == "class"), "")
            d = {"name": m.group(3), "qual": ".".join([x["name"] for _, x in stack] + [m.group(3)]), "start": i,
                 "end": len(lines), "kind": kind, "cls": cls,
                 "nested": any(x["kind"] != "class" for _, x in stack)}
            out.append(d)
            stack.append((ind, d))
    return out


class Repo:
    """One regex pass: names each file defines and mentions, class bases. Files are parsed on demand."""

    def __init__(self, root):
        self.root = root
        self.files = []
        self.idents = {}
        self.def_files = collections.defaultdict(set)
        self.subclasses = collections.defaultdict(set)
        self.bases = collections.defaultdict(set)
        self.syntax_errors = {}
        self._parsed = {}
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if not (
                d.startswith(".") or d in SKIP_DIRS or d in TEST_DIRS or d.endswith(".egg-info")
                or os.path.isfile(os.path.join(dirpath, d, "pyvenv.cfg"))))
            for name in sorted(filenames):
                if not name.endswith(".py") or name.startswith(".") or is_test(name):
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
                self.files.append(rel)
                self.idents[rel] = frozenset(sys.intern(w) for w in set(WORD.findall(txt)) if len(w) > 3)
                for m in DEF_RE.finditer(txt):
                    self.def_files[m.group(2)].add(rel)
                    if m.group(1) == "class" and m.group(3):
                        for b in WORD.findall(re.sub(r"\[[^\]]*\]|\w+\s*=\s*[\w.]+", "", m.group(3))):
                            if b not in ("object", "Generic", "Protocol"):
                                self.bases[m.group(2)].add(b)
                                self.subclasses[b].add(m.group(2))
            if time.time() - T0 > SCAN_SECONDS:
                break

    def parsed(self, rel):
        if rel not in self._parsed:
            try:
                with open(os.path.join(self.root, rel), encoding="utf-8", errors="replace") as f:
                    src = f.read()
            except OSError:
                src = ""
            try:
                defs = ast_defs(src)
            except SyntaxError as e:
                self.syntax_errors[rel] = e.lineno or 0
                defs = scan_defs(src)
            except (ValueError, RecursionError, MemoryError):
                defs = scan_defs(src)
            lines = src.splitlines()
            for d in defs:
                d["file"] = rel
                d["_lines"] = lines
            self._parsed[rel] = defs
        return self._parsed[rel]


def tokens(d):
    if "_tok" not in d:
        d["_tok"] = frozenset(WORD.findall("\n".join(d["_lines"][d["start"] - 1:d["end"]])))
    return d["_tok"]


def twins(name):
    """Sync/async spellings of a name."""
    out = set()
    for pre in ("a", "async_", "sync_"):
        out.add(pre + name)
        if name.startswith(pre) and len(name) > len(pre) + 2:
            out.add(name[len(pre):])
    for suf in ("_async", "_sync", "_aio"):
        out.add(name + suf)
        if name.endswith(suf):
            out.add(name[:-len(suf)])
    if name.startswith("_"):
        out.update("_" + t for t in twins(name[1:]))
    out.discard(name)
    return out


def family(repo, cls):
    """Classes related to cls by inheritance (bases, subclasses, siblings; two levels) as (relation, name)."""
    out, seen = [], {cls}

    def add(rel, name):
        if name not in seen:
            seen.add(name)
            out.append((rel, name))
    for b in sorted(repo.bases.get(cls, ())):
        add("base class", b)
    for s in sorted(repo.subclasses.get(cls, ())):
        add("subclass", s)
    for b in sorted(repo.bases.get(cls, ())):
        for s in sorted(repo.subclasses.get(b, ())):
            add("sibling class", s)
    for rel, name in list(out):
        if rel == "subclass":
            for s in sorted(repo.subclasses.get(name, ())):
                add("subclass", s)
        elif rel == "base class":
            for b in sorted(repo.bases.get(name, ())):
                add("base class", b)
    return out


def related(repo, anchors, limit=MAX_LINES):
    """Sites related to the anchor definitions, best first: [(def, anchor, reason)]."""
    anchor_files = []
    for a in anchors:
        if a["file"] not in anchor_files:
            anchor_files.append(a["file"])
    names = {a["name"] for a in anchors}
    dirs = {f.rsplit("/", 1)[0] if "/" in f else "" for f in anchor_files}
    # Files to parse, most promising first: the anchors' files, files that mention an anchor name, the same
    # directories, then the rest. The time guard cuts the tail.
    order = list(anchor_files)
    rest = [f for f in repo.files if f not in anchor_files]
    rest.sort(key=lambda f: (not (names & repo.idents[f]), (f.rsplit("/", 1)[0] if "/" in f else "") not in dirs, f))
    pool = []
    for f in order + rest:
        if f not in anchor_files and time.time() - T0 > PARSE_SECONDS:
            break
        pool.extend(d for d in repo.parsed(f) if not d["nested"])

    def overlaps(x):
        return any(x["file"] == a["file"] and x["start"] <= a["end"] and a["start"] <= x["end"] for a in anchors)
    tiers = [[] for _ in range(6)]
    for a in anchors:
        is_fn, name, tw = a["kind"] != "class", a["name"], twins(a["name"])
        fam = dict((n, r) for r, n in reversed(family(repo, a["cls"]))) if a["cls"] and is_fn else {}
        distinct = len(name) >= 5 and not name.startswith("__") and len(repo.def_files.get(name, ())) <= 2
        mine = tokens(a)
        t = [[] for _ in range(6)]
        for x in pool:
            if x is a or overlaps(x):
                continue
            if x["kind"] == "class":
                continue
            other = tokens(x)
            j = len(mine & other) / len(mine | other) if mine and other else 0.0
            key = (-j, x["file"] != a["file"], x["file"], x["start"])
            if is_fn and len(mine) >= 12 and j >= SIM_MIN:
                t[0].append((key, x, "similar code to " + a["qual"]))
            elif fam and x["cls"] in fam and (x["name"] == name or x["name"] in tw):
                t[1].append((key, x, "same method in %s of %s" % (fam[x["cls"]], a["cls"])))
            elif x["file"] == a["file"] and x["qual"] == a["qual"]:
                t[2].append((key, x, "overload of " + a["qual"]))
            elif is_fn and x["name"] in tw and not name.startswith("__"):
                t[2].append((key, x, "sync/async twin of " + a["qual"]))
            elif is_fn and x["name"] == name and not name.startswith("__") and len(repo.def_files.get(name, ())) <= 6:
                t[3].append((key, x, "same name as " + a["qual"]))
            elif distinct and name in other and x["name"] != name:
                t[4].append((key, x, "uses " + a["qual"]))
            elif (is_fn and x["name"] in mine and len(x["name"]) >= 5 and not x["name"].startswith("__")
                  and len(repo.def_files.get(x["name"], ())) <= 2):
                t[5].append(((x["file"] != a["file"], -j, x["file"], x["start"]), x, "used by " + a["qual"]))
        for i in range(6):
            tiers[i].append(sorted(t[i], key=lambda r: r[0]))
    out, seen = [], set()
    for tier in tiers:                       # tier by tier; inside a tier, round-robin over the anchors
        i = 0
        while len(out) < limit and any(i < len(lst) for lst in tier):
            for lst in tier:
                if i < len(lst) and len(out) < limit:
                    _, x, why = lst[i]
                    if (x["file"], x["start"]) not in seen:
                        seen.add((x["file"], x["start"]))
                        out.append((x, why))
            i += 1
    return out


def fmt(d):
    return "%s:%d-%d %s %s" % (d["file"], d["start"], d["end"], d["kind"], d["qual"])


def audit(root):
    changes = changed_files(root)
    if not changes:
        return NO_EDIT
    repo = Repo(root)
    out, anchors, notes = ["CHANGED by the draft:"], [], []
    for rel, old, state in changes:
        if state == "deleted":
            out.append("%s (file removed)" % rel)
            continue
        defs = repo.parsed(rel)
        if rel in repo.syntax_errors:
            notes.append("SYNTAX ERROR: %s does not parse (near line %d). Repair it first." % (
                rel, repo.syntax_errors[rel]))
        if state == "new file" or old is None:
            out.append("%s (%s)" % (rel, "new file" if state == "new file" else "changed; baseline unreadable"))
            continue
        try:
            with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as f:
                new = f.read()
        except OSError:
            continue
        module_level, hit = False, []
        for lo, hi in changed_ranges(old, new):
            inner = None
            for d in defs:
                if d["start"] <= lo and hi <= d["end"] and (inner is None or d["end"] - d["start"] < inner["end"] - inner["start"]):
                    inner = d
            if inner is None:
                module_level = True
            elif all(inner is not h for h in hit):
                hit.append(inner)
        for d in hit:
            out.append(fmt(d))
            anchors.append(d)
        if module_level:
            out.append("%s (module-level lines)" % rel)
    out = out[:1 + 12] + notes
    sites = related(repo, anchors[:6]) if anchors else []
    if sites:
        out.append("RELATED SITES NOT CHANGED (most likely first; open each range and decide whether the issue's "
                   "behavior also passes through it):")
        out += ["%s -- %s" % (fmt(x), why) for x, why in sites]
    elif anchors:
        out.append("RELATED SITES NOT CHANGED: none found.")
    text = "\n".join(out)
    while len(text) > MAX_CHARS and "\n" in text:
        text = text[:text.rindex("\n")]
    return text


def main():
    try:
        root = find_root()
        print(audit(root) if root else NO_EDIT)
    except Exception:   # never fail the caller
        print("AUDIT UNAVAILABLE\nRun `git diff` and check the related sites listed in the code map by hand.")


if __name__ == "__main__":
    main()
