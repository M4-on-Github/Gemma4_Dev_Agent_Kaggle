"""Locator v2: rank the files, the symbols and the related sites that an issue is about.

  python3 locate.py --issue-file <path> [--top-files 5] [--top-symbols 8] [--mode v2|bm25]

The repository is the current directory. Standard library only; reads files, starts nothing, writes nothing.

How it ranks (mode v2):
  1. One pass over the non-test .py files: word counts (BM25 against the whole issue, the v1 ranker), the names
     each file defines (regex) and the identifiers it mentions.
  2. Exact evidence from the issue: identifiers in backticks / code-shaped words that the repo DEFINES, file paths
     and dotted module names, traceback frames.
  3. A file graph (A -> B when A mentions a name B defines; rarer names and names from the issue weigh more) and
     personalized PageRank seeded with the lexical scores, as in Aider's repo map.
  4. Files = weighted sum of the normalized parts. Symbols = functions/classes/methods (stdlib ast, an indent
     scanner on syntax errors) of the best files plus exact-name matches anywhere, scored by BM25 over the symbol
     text, exact names, traceback frames and the file score.
  5. Related sites of the best symbols: overloads, sync/async twins, the same method in base, sub and sibling
     classes, same-named definitions elsewhere, near-duplicate bodies, callers and callees.

Mode bm25 is the v1 baseline: the BM25 file list only (--query-chars N limits the issue text as v1's caller did).
On any error the script prints one plain line and exits 0.
"""
import argparse
import ast
import collections
import math
import os
import re
import sys

PLAIN = "No ranking available; search the repository for the names used in the issue."
MAX_FILES = 6000
MAX_BYTES = 400_000
MAX_ISSUE = 20_000
TEST_DIRS = ("tests", "test", "testing")
SKIP_DIRS = ("__pycache__", "node_modules", "site-packages", "dist-packages", "scripts", "examples", "example",
             "benchmarks", "benchmark", "build", "dist", "vendor", "vendored", "_vendor", "third_party", "venv",
             "env", "migrations")
WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
SPLIT = re.compile(r"_|(?<=[a-z0-9])(?=[A-Z])")
STOP = set("the a an and or of to in is it be this that for on with as are was not by if from at but we can when use "
           "used using have has which".split())
DEF_RE = re.compile(r"^[ \t]*(?:async[ \t]+)?(def|class)[ \t]+([A-Za-z_][A-Za-z0-9_]*)[ \t]*(\([^)\n]*\))?", re.M)
FRAME_RE = re.compile(r'File "([^"\n]+)", line (\d+)(?:, in ([A-Za-z_][A-Za-z0-9_]*))?')
PATH_RE = re.compile(r"[A-Za-z0-9_./\\-]*[A-Za-z0-9_]\.py\b")
DOTTED_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+")
TICK_RE = re.compile(r"`([^`\n]{1,200})`")
FENCE_RE = re.compile(r"```.*?```", re.S)
COMMENT_RE = re.compile(r"<!--.*?(?:-->|\Z)", re.S)
CHECK_RE = re.compile(r"^[ \t]*[-*][ \t]*\[[ xX]\].*$", re.M)
URL_RE = re.compile(r"\b(?:https?|ftp)://\S+")
PY_WORDS = set("self cls None True False def class return import from for while with try except raise assert pass "
               "lambda yield async await print str int float bool list dict set tuple object type len".split())

# Weights of the v2 file score (each part is normalized to [0, 1] first) and of the symbol score.
W_BM25, W_IDENT, W_PATH, W_PPR = 1.0, 0.5, 1.0, 0.5
CLEAN = True             # drop HTML comments, checklist lines and links (template boilerplate) from the issue
TITLE_BOOST = 2.0        # extra BM25 weight of words in the issue's first line
NODEF_FACTOR = 1.0       # v2 file score multiplier for files that define no function or class
PPR_DAMP, PPR_ITERS, PPR_MAX_DEF_FILES = 0.3, 15, 4
SYM_FILES = 8            # symbols are taken from this many best files (plus exact-name matches anywhere)
S_BM25, S_EXACT, S_FILE, S_FRAME = 1.0, 1.0, 0.8, 0.8
S_B = 0.3                # BM25 length normalization for symbols (lower favours long bodies)
S_MULT = False           # multiply the symbol evidence by the file score instead of adding it
S_REF = 0.0              # issue identifiers used verbatim inside the symbol body
S_PPR = 0.0              # PageRank over the symbol call graph (caller -> callee), seeded with the other parts
REL_FOR, REL_MAX, REL_PER_SYM = 5, 12, 4   # related sites: for the best N symbols, total cap, cap per symbol
REL_FILES, REL_SIM, REL_CALLERS, REL_CALLEES = 20, 3, 2, 1   # pool of best files; caps per relation
SIM_MIN = 0.55           # token-set Jaccard above which two bodies count as near-duplicates

DEBUG = False          # the evaluator sets this to see errors instead of the plain line

_TOK_CACHE = {}


def expand(w):
    """v1 tokenization of one identifier: itself lowercased plus its snake/camel parts."""
    r = _TOK_CACHE.get(w)
    if r is None:
        r = []
        lw = w.lower()
        if len(lw) > 2 and lw not in STOP:
            r.append(lw)
        parts = [p.lower() for p in SPLIT.split(w) if len(p) > 2]
        if len(parts) > 1:
            r.extend(p for p in parts if p not in STOP)
        _TOK_CACHE[w] = r
    return r


def toks(text):
    out = []
    for w in WORD.findall(text):
        out.extend(expand(w))
    return out


def skip_dir(dirpath, d):
    return (d.startswith(".") or d in SKIP_DIRS or d.startswith("doc") or d.endswith(".egg-info") or d in TEST_DIRS
            or os.path.isfile(os.path.join(dirpath, d, "pyvenv.cfg")))


def is_test(name):
    return name == "conftest.py" or name.startswith("test_") or name.endswith("_test.py")


def read(root, rel):
    try:
        with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


class Repo:
    """Pass 1 over the repository. Per file: BM25 counts of the query words, defined names, mentioned names."""

    def __init__(self, root, qwords):
        self.root = root
        self.files = []
        self.tf = {}                                   # file -> {query word: count}
        self.length = {}                               # file -> v1 document length
        self.idents = {}                               # file -> frozenset of identifiers mentioned
        self.defs_in = {}                              # file -> set of names defined (regex)
        self.def_files = collections.defaultdict(set)  # name -> files defining it
        self.subclasses = collections.defaultdict(set)  # base name -> {(file, class name)}
        self.bases = collections.defaultdict(set)      # class name -> base names
        self.df = collections.Counter()
        self._parsed = {}
        intern = sys.intern
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if not skip_dir(dirpath, d))
            for name in sorted(filenames):
                if not name.endswith(".py") or is_test(name) or len(self.files) >= MAX_FILES:
                    continue
                full = os.path.join(dirpath, name)
                try:
                    if os.path.getsize(full) > MAX_BYTES:
                        continue
                except OSError:
                    continue
                rel = os.path.relpath(full, root).replace(os.sep, "/")
                txt = read(root, rel)
                cnt = collections.Counter(WORD.findall(txt))
                for w in WORD.findall(rel[:-3].replace("/", " ")):   # the path counts three times, as in v1
                    cnt[w] += 3
                tf, length = {}, 0
                for w, c in cnt.items():
                    for t in expand(w):
                        length += c
                        if t in qwords:
                            tf[t] = tf.get(t, 0) + c
                self.files.append(rel)
                self.tf[rel], self.length[rel] = tf, length
                self.df.update(tf.keys())
                self.idents[rel] = frozenset(intern(w) for w in cnt if len(w) > 3)
                names = set()
                for m in DEF_RE.finditer(txt):
                    names.add(m.group(2))
                    if m.group(1) == "class" and m.group(3):
                        for b in WORD.findall(re.sub(r"\[[^\]]*\]|\w+\s*=\s*[\w.]+", "", m.group(3))):
                            if b not in ("object", "Generic", "Protocol"):
                                self.bases[m.group(2)].add(b)
                                self.subclasses[b].add((rel, m.group(2)))
                self.defs_in[rel] = names
                for n in names:
                    self.def_files[n].add(rel)

    def bm25(self, qwords):
        n = len(self.files)
        avg = sum(self.length.values()) / n
        scores = {}
        for rel in self.files:
            tf, s = self.tf[rel], 0.0
            for w in qwords:
                c = tf.get(w)
                if c:
                    idf = math.log(1 + (n - self.df[w] + 0.5) / (self.df[w] + 0.5))
                    s += qwords[w] * idf * c * 2.2 / (c + 1.2 * (0.25 + 0.75 * self.length[rel] / avg))
            if s > 0:
                scores[rel] = s
        return scores

    def parsed(self, rel):
        """Definitions of one file, parsed on demand: dicts with name, qual, kind, start, end, cls, bases, nested."""
        if rel not in self._parsed:
            src = read(self.root, rel)
            try:
                defs = ast_defs(src)
            except (SyntaxError, ValueError, RecursionError, MemoryError):
                defs = scan_defs(src)
            lines = src.splitlines()
            for d in defs:
                d["file"] = rel
                d["_lines"] = lines
            self._parsed[rel] = defs
        return self._parsed[rel]


def ast_defs(src):
    out = []

    def walk(node, prefix, cls, in_func):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                is_cls = isinstance(ch, ast.ClassDef)
                start = min([ch.lineno] + [d.lineno for d in ch.decorator_list])
                bases = []
                if is_cls:
                    for b in ch.bases:
                        while isinstance(b, ast.Subscript):
                            b = b.value
                        if isinstance(b, ast.Attribute):
                            bases.append(b.attr)
                        elif isinstance(b, ast.Name):
                            bases.append(b.id)
                out.append({"name": ch.name, "qual": prefix + ch.name, "start": start, "end": ch.end_lineno,
                            "kind": "class" if is_cls else ("async def" if isinstance(ch, ast.AsyncFunctionDef)
                                                            else "def"),
                            "cls": cls, "bases": bases, "nested": in_func})
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
                 "end": len(lines), "kind": kind, "cls": cls, "bases": [],
                 "nested": any(x["kind"] != "class" for _, x in stack)}
            out.append(d)
            stack.append((ind, d))
    return out


class Issue:
    """Evidence read from the issue text: BM25 words, weighted identifiers, paths, traceback frames."""

    def __init__(self, text):
        if CLEAN:
            text = URL_RE.sub(" ", CHECK_RE.sub(" ", COMMENT_RE.sub(" ", text)))
        text = text.strip()[:MAX_ISSUE]
        self.words = {w: 1.0 for w in toks(text)}          # BM25 query word -> weight
        for w in toks(text.split("\n", 1)[0]):
            self.words[w] = 1.0 + TITLE_BOOST
        self.ident = collections.defaultdict(float)
        self.frames = [(p.replace("\\", "/"), int(ln), fn) for p, ln, fn in FRAME_RE.findall(text)]
        self.paths = [p.replace("\\", "/").lstrip("./") for p in PATH_RE.findall(text)]
        self.dotted = DOTTED_RE.findall(text)
        fenced = " ".join(FENCE_RE.findall(text))
        prose = FENCE_RE.sub(" ", text)

        def add(w, weight):
            if len(w) > 2 and w not in PY_WORDS and w.lower() not in STOP:
                self.ident[w] = max(self.ident[w], weight)
        for span in TICK_RE.findall(prose):
            for w in WORD.findall(span):
                add(w, 3.0)
        for w in WORD.findall(fenced):
            add(w, 1.5)
        for m in WORD.finditer(prose):
            w = m.group()
            codey = ("_" in w.strip("_") or re.search(r"[a-z0-9][A-Z]", w) or prose[m.end():m.end() + 1] == "("
                     or (m.start() and prose[m.start() - 1] == "."))
            add(w, 2.0 if codey else (1.0 if w[0].isupper() and not w.isupper() else 0.5))
        for d in self.dotted:
            for w in d.split("."):
                add(w, 2.0)
        for _, _, fn in self.frames:
            if fn:
                add(fn, 2.0)


def norm(d):
    m = max(d.values(), default=0.0)
    return {k: v / m for k, v in d.items()} if m > 0 else {}


def ident_scores(repo, issue):
    """Issue identifiers that a file defines, weighted by how few files define them."""
    n, out = len(repo.files), collections.defaultdict(float)
    for w, weight in issue.ident.items():
        fs = repo.def_files.get(w)
        if fs and len(fs) <= 8:
            rarity = math.log(1 + n / len(fs)) / math.log(1 + n)
            for f in fs:
                out[f] += weight * rarity
    return out


def path_scores(repo, issue):
    out = collections.defaultdict(float)
    by_base = collections.defaultdict(list)
    for f in repo.files:
        by_base[f.rsplit("/", 1)[-1]].append(f)
    mentions = [(p, 1.0) for p in issue.paths] + [(p, 1.0 + 0.5 * i / max(len(issue.frames), 1))
                                                  for i, (p, _, _) in enumerate(issue.frames)]
    for p, weight in mentions:
        parts = p.split("/")
        cands = by_base.get(parts[-1], [])
        best, best_n = [], 0
        for f in cands:
            fp, k = f.split("/"), 0
            while k < min(len(fp), len(parts)) and fp[-1 - k] == parts[-1 - k]:
                k += 1
            if k > best_n:
                best, best_n = [f], k
            elif k == best_n:
                best.append(f)
        if best and (best_n >= 2 or len(cands) == 1):
            for f in best:
                out[f] += weight / len(best)
    mods = {}
    for f in repo.files:
        m = f[:-3].replace("/", ".")
        mods[m[:-9] if m.endswith(".__init__") else m] = f
    for d in issue.dotted:
        parts = d.split(".")
        for k in range(len(parts), 1, -1):          # longest dotted prefix that is a module of the repo
            hit = [f for m, f in mods.items() if m == ".".join(parts[:k]) or m.endswith("." + ".".join(parts[:k]))]
            if hit:
                for f in hit:
                    out[f] += 0.7 / len(hit)
                break
    return out


def pagerank(repo, issue, seed):
    """Personalized PageRank over files; rank flows from a file to the files that define the names it mentions."""
    if not seed:
        return {}
    out_edges = {}
    for f in repo.files:
        e = collections.defaultdict(float)
        for w in repo.idents[f]:
            fs = repo.def_files.get(w)
            if not fs or len(fs) > PPR_MAX_DEF_FILES or w.startswith("__"):
                continue
            weight = (10.0 if w in issue.ident else 1.0) * (0.1 if w.startswith("_") else 1.0) / len(fs)
            for g in fs:
                if g != f:
                    e[g] += weight
        tot = sum(e.values())
        if tot:
            out_edges[f] = [(g, v / tot) for g, v in e.items()]
    tot = sum(seed.values())
    p = {f: v / tot for f, v in seed.items()}
    r = dict(p)
    for _ in range(PPR_ITERS):
        nxt = collections.defaultdict(float)
        dangling = 0.0
        for f, v in r.items():
            edges = out_edges.get(f)
            if edges:
                for g, w in edges:
                    nxt[g] += PPR_DAMP * v * w
            else:
                dangling += PPR_DAMP * v
        for f, v in p.items():
            nxt[f] += (1 - PPR_DAMP + dangling) * v
        r = nxt
    return r


def rank_files(repo, issue):
    bm = norm(repo.bm25(issue.words))
    idn = norm(ident_scores(repo, issue))
    pth = norm(path_scores(repo, issue))
    lex = {f: W_BM25 * bm.get(f, 0) + W_IDENT * idn.get(f, 0) + W_PATH * pth.get(f, 0) for f in repo.files}
    lex = {f: v for f, v in lex.items() if v > 0}
    ppr = norm(pagerank(repo, issue, lex)) if W_PPR else {}
    score = {f: lex.get(f, 0) + W_PPR * ppr.get(f, 0) for f in set(lex) | set(ppr)}
    return {f: v * (1.0 if repo.defs_in[f] else NODEF_FACTOR) for f, v in score.items() if v > 0}


def body_tokens(d, repo=None):
    if "_tok" not in d:
        lines = d["_lines"][d["start"] - 1:d["end"]]
        if d["kind"] == "class" and repo is not None:      # a class is its header and class-level statements
            inner = [x for x in repo.parsed(d["file"]) if x is not d and d["start"] <= x["start"] and x["end"] <= d["end"]]
            drop = set()
            for x in inner:
                drop.update(range(x["start"] + 1, x["end"] + 1))
            lines = [ln for i, ln in enumerate(lines, d["start"]) if i not in drop]
        d["_raw"] = collections.Counter(WORD.findall("\n".join(lines)))
        c = collections.Counter()
        for w, n in d["_raw"].items():
            for t in expand(w):
                c[t] += n
        for t in toks(d["qual"].replace(".", " ")):
            c[t] += 3
        d["_tok"] = c
    return d["_tok"]


def rank_symbols(repo, issue, fscore, top_files):
    fnorm = norm(fscore)
    cands = []
    for f in top_files[:SYM_FILES]:
        cands.extend(d for d in repo.parsed(f) if not d["nested"])
    seen = {id(d) for d in cands}
    for w in issue.ident:                                   # exact-name definitions outside the best files
        fs = repo.def_files.get(w, ())
        if 0 < len(fs) <= 4:
            for f in sorted(fs, key=lambda x: -fscore.get(x, 0)):
                for d in repo.parsed(f):
                    if d["name"] == w and not d["nested"] and id(d) not in seen:
                        seen.add(id(d))
                        cands.append(d)
    if not cands:
        return []
    n = len(cands)
    df = collections.Counter()
    for d in cands:
        df.update(w for w in body_tokens(d, repo) if w in issue.words)
    avg = sum(sum(d["_tok"].values()) for d in cands) / n
    bm = {}
    for i, d in enumerate(cands):
        c, s = d["_tok"], 0.0
        length = sum(c.values())
        for w in issue.words:
            if w in c:
                idf = math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5))
                s += issue.words[w] * idf * c[w] * 2.2 / (c[w] + 1.2 * (1 - S_B + S_B * length / avg))
        bm[i] = s
    bm = norm(bm)
    frame_fn = {fn for _, _, fn in issue.frames if fn}
    max_w = max(issue.ident.values(), default=1.0)
    ref = {}
    if S_REF:
        rdf = collections.Counter(w for d in cands for w in d["_raw"] if w in issue.ident)
        for i, d in enumerate(cands):
            ref[i] = sum(issue.ident[w] * math.log(1 + n / rdf[w]) for w in d["_raw"] if w in issue.ident
                         and w != d["name"]) / math.sqrt(8 + d["end"] - d["start"])
        ref = norm(ref)
    scored = []
    for i, d in enumerate(cands):
        exact = issue.ident.get(d["name"], 0.0) / max_w
        if d["cls"] and d["name"].startswith("__"):
            exact = 0.0
        if d["cls"] and d["cls"] in issue.ident:
            exact = exact * 1.5 + 0.3 * issue.ident[d["cls"]] / max_w
        frame = 1.0 if d["name"] in frame_fn else 0.0
        s = S_BM25 * bm.get(i, 0) + S_EXACT * exact + S_FRAME * frame + S_REF * ref.get(i, 0)
        if S_MULT:
            s *= 0.1 + fnorm.get(d["file"], 0)
        else:
            s += S_FILE * fnorm.get(d["file"], 0)
        scored.append((s, d))
    if S_PPR:
        scored = symbol_pagerank(repo, scored)
    scored.sort(key=lambda x: (-x[0], x[1]["file"], x[1]["start"]))
    return [d for _, d in scored]


def symbol_pagerank(repo, scored):
    """Add PageRank mass: a symbol passes rank to the candidates whose (distinctive) names its body mentions."""
    by_name = collections.defaultdict(list)
    for i, (_, d) in enumerate(scored):
        if len(d["name"]) > 3 and not d["name"].startswith("__"):
            by_name[d["name"]].append(i)
    edges = {}
    for i, (_, d) in enumerate(scored):
        e = [j for w in d["_raw"] if w in by_name and len(by_name[w]) <= 3 for j in by_name[w] if j != i]
        if e:
            edges[i] = e
    tot = sum(s for s, _ in scored) or 1.0
    p = [s / tot for s, _ in scored]
    r = list(p)
    for _ in range(PPR_ITERS):
        nxt = [0.0] * len(r)
        dangling = 0.0
        for i, v in enumerate(r):
            e = edges.get(i)
            if e:
                for j in e:
                    nxt[j] += 0.5 * v / len(e)
            else:
                dangling += 0.5 * v
        r = [nxt[i] + (0.5 + dangling) * p[i] for i in range(len(r))]
    top, smax = max(r) or 1.0, max(s for s, _ in scored) or 1.0
    return [(s / smax + S_PPR * r[i] / top, d) for i, (s, d) in enumerate(scored)]


def twins(name):
    """Sync/async spellings of a name."""
    out = set()
    for pre in ("a", "async_", "_async_", "sync_"):
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
    """Classes related to cls by inheritance: bases, subclasses, siblings (two levels), as (relation, name)."""
    out, seen = [], {cls}

    def add(rel, name):
        if name not in seen:
            seen.add(name)
            out.append((rel, name))
    for b in sorted(repo.bases.get(cls, ())):
        add("base class", b)
    for _, s in sorted(repo.subclasses.get(cls, ())):
        add("subclass", s)
    for b in sorted(repo.bases.get(cls, ())):
        for _, s in sorted(repo.subclasses.get(b, ())):
            add("sibling class", s)
    for rel, name in list(out):
        if rel == "subclass":
            for _, s in sorted(repo.subclasses.get(name, ())):
                add("subclass", s)
        elif rel == "base class":
            for b in sorted(repo.bases.get(name, ())):
                add("base class", b)
    return out


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def related_sites(repo, issue, symbols, fscore, top_files):
    """Sites likely to need the same change as the best symbols. Returns [(def, anchor def, reason)].
    Order per symbol = how often each relation held between the sites of one fix when measured offline:
    near-duplicate bodies, the same method across the class family, the same name elsewhere, callers, callees."""
    shown = {(d["file"], d["start"]) for d in symbols}
    per_sym = []
    pool = [d for f in top_files[:REL_FILES] for d in repo.parsed(f) if not d["nested"]]
    for d in symbols[:REL_FOR]:
        found, name = [], d["name"]
        is_fn = d["kind"] != "class"
        tw = twins(name)

        def add(x, why):
            key = (x["file"], x["start"])
            if key not in shown and x is not d and not x["nested"] and all(y is not x for y, _ in found):
                found.append((x, why))

        def defs_named(n, limit):
            for f in sorted(repo.def_files.get(n, ()), key=lambda x: (x != d["file"], -fscore.get(x, 0)))[:limit]:
                for x in repo.parsed(f):
                    if x["name"] == n:
                        yield x
        for x in repo.parsed(d["file"]):                      # overloads, redefinitions, sync/async twins
            if x["qual"] == d["qual"]:
                add(x, "overload")
            elif x["name"] in tw and x["cls"] == d["cls"] and is_fn and x["kind"] != "class":
                add(x, "sync/async twin")
        if is_fn:                                             # near-duplicate bodies
            mine = set(body_tokens(d, repo))
            if len(mine) >= 12:
                sims = []
                for x in pool:
                    if x is not d and x["kind"] != "class":
                        j = jaccard(mine, set(body_tokens(x, repo)))
                        if j >= SIM_MIN:
                            sims.append((-j, x["file"], x["start"], x))
                for _, _, _, x in sorted(sims, key=lambda t: t[:3])[:REL_SIM]:
                    add(x, "similar code")
        if is_fn and d["cls"]:                                # the same method across the class family
            for rel, cname in family(repo, d["cls"])[:12]:
                for c in defs_named(cname, 2):
                    for x in repo.parsed(c["file"]):
                        if x["cls"] == cname and x["kind"] != "class" and (x["name"] == name or x["name"] in tw):
                            add(x, "same method in " + rel)
        if not is_fn:
            for rel, cname in family(repo, name)[:4]:
                if rel == "subclass":
                    for x in defs_named(cname, 2):
                        if x["kind"] == "class":
                            add(x, "subclass")
        if is_fn and not name.startswith("__"):               # same name or twin elsewhere
            if len(repo.def_files.get(name, ())) <= 6:
                for x in defs_named(name, 6):
                    if x["kind"] != "class":
                        add(x, "same name")
            for t in sorted(tw):
                for x in defs_named(t, 2):
                    if x["kind"] != "class":
                        add(x, "sync/async twin")
        distinct = len(name) >= 5 and not name.startswith("__") and len(repo.def_files.get(name, ())) <= 2
        if distinct:                                          # callers of a distinctive name
            callers = [x for x in pool if x is not d and x["kind"] != "class" and x["name"] != name
                       and name in body_tokens(x, repo) and name in x["_raw"]]
            callers.sort(key=lambda x: (x["file"] != d["file"], -fscore.get(x["file"], 0), x["file"], x["start"]))
            for x in callers[:REL_CALLERS]:
                add(x, "uses it")
        if is_fn and REL_CALLEES:                             # distinctive names it calls, same file first
            body_tokens(d, repo)
            callees = [x for x in pool if x is not d and x["name"] in d["_raw"] and len(x["name"]) >= 5
                       and not x["name"].startswith("__") and len(repo.def_files.get(x["name"], ())) <= 2]
            callees.sort(key=lambda x: (x["file"] != d["file"], -fscore.get(x["file"], 0), x["file"], x["start"]))
            for x in callees[:REL_CALLEES]:
                add(x, "used by it")
        per_sym.append((d, found[:REL_PER_SYM]))
    out, i = [], 0
    while len(out) < REL_MAX and any(i < len(f) for _, f in per_sym):   # round-robin over the best symbols
        for d, found in per_sym:
            if i < len(found) and len(out) < REL_MAX:
                x, why = found[i]
                if (x["file"], x["start"]) not in shown:
                    shown.add((x["file"], x["start"]))
                    out.append((x, d, why))
        i += 1
    return out


def fmt(d):
    return "%s:%d-%d %s %s" % (d["file"], d["start"], d["end"], d["kind"], d["qual"])


def main(argv=None, want_struct=False):
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue-file", required=True)
    ap.add_argument("--top-files", type=int, default=5)
    ap.add_argument("--top-symbols", type=int, default=8)
    ap.add_argument("--mode", choices=["v2", "bm25"], default="v2")
    ap.add_argument("--query-chars", type=int, default=0)
    args = ap.parse_args(argv)
    res = {"files": [], "symbols": [], "related": []}
    try:
        with open(args.issue_file, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        if args.query_chars:
            text = text[:args.query_chars]
        if args.mode == "bm25":                      # v1: raw text, every word weight 1
            words = dict.fromkeys(toks(text), 1.0)
            repo = Repo(os.getcwd(), set(words))
            sc = repo.bm25(words) if repo.files else {}
            files = sorted(sc, key=lambda r: (-sc[r], r))
            res["files"] = files[:max(args.top_files, 10)]
            if files:
                print("The source files that best match the issue, best first: %s." % ", ".join(files[:args.top_files]))
            else:
                print(PLAIN)
            return res if want_struct else 0
        issue = Issue(text)
        repo = Repo(os.getcwd(), set(issue.words))
        if not repo.files or not issue.words:
            print(PLAIN)
            return res if want_struct else 0
        fscore = rank_files(repo, issue)
        files = sorted(fscore, key=lambda r: (-fscore[r], r))
        if not files:
            print(PLAIN)
            return res if want_struct else 0
        ranked = rank_symbols(repo, issue, fscore, files)
        symbols = ranked[:args.top_symbols]
        related = related_sites(repo, issue, symbols, fscore, files)
        out = ["FILES that best match the issue, best first:"]
        out += ["%d. %s" % (i + 1, f) for i, f in enumerate(files[:args.top_files])]
        if symbols:
            out.append("SYMBOLS to read first (file:first-last line), best first:")
            out += ["%d. %s" % (i + 1, fmt(d)) for i, d in enumerate(symbols)]
        if related:
            out.append("RELATED SITES that may need the same change (check each before you finish):")
            out += ["- %s  [%s of %s]" % (fmt(x), why, a["qual"]) for x, a, why in related]
        print("\n".join(out))
        res["files"] = files[:max(args.top_files, 10)]
        res["symbols"] = [{"file": d["file"], "start": d["start"], "end": d["end"], "qual": d["qual"]} for d in ranked[:20]]
        res["related"] = [{"file": x["file"], "start": x["start"], "end": x["end"], "why": why} for x, _, why in related]
    except Exception:   # never fail the caller
        if DEBUG:
            raise
        print(PLAIN)
    return res if want_struct else 0


if __name__ == "__main__":
    sys.exit(main() or 0)
