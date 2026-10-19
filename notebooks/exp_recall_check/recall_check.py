# %% [markdown]
# Free, CPU-only recall check — real search_similar_code / get_code_neighbors / get_code_subgraph
#
# Follow-up to EXP-002-estop-a (see experiments/EXP-002-estop-a.md, experiments/recall_check/README.md).
# The local-only half of this check (AST-diff gold extraction + a `git grep` lexical baseline,
# 24.8/35.4/37.2/41.6% recall@1/3/5/10 on 113 tasks) is already built and logged. This notebook is the
# **Kaggle-side half**: it calls the *real* `swegemma.graph` functions (the exact code the harness tools
# wrap) against the actual mounted graph/embedding data, so the grep numbers above have something real to
# be compared against. No GPU, no model, no vLLM server — **CPU notebook, zero GPU quota**.
#
# **Attach as inputs** (Add Input): competition `gemma-4-developer-agent`, dataset
# `metric/gemma-4-developer-agent-wheelhouse`. **Accelerator**: None / CPU. **Internet**: off.
#
# **Status: UNTESTED on Kaggle** (written without access to kaggle.com or the real mounted graph/embedding
# data — this repo checkout has no local `data/graphs`/`data/embeddings`). Node-name-to-file-path mapping
# in particular is a best-effort heuristic (prefix search against the snapshot's known .py files) because
# the real graph node attribute schema (does a node carry an explicit file/path attribute, or only a dotted
# name?) is unverified until this runs for real — see the "schema check" diagnostic below, which is
# designed to surface that question rather than assume an answer.

# %%
# ---------------------------------------------------------------- parameters (edit me)
EXP_ID = "recall-check-v1"
K = 10                      # top-k for search_similar_code, matches the grep baseline's recall@k levels
MAX_NEIGHBORS = 50          # matches get_code_neighbors' own default
MAX_TASKS = None            # None = all tasks with findable gold; set an int to smoke-test a subset first
TOP_N_IDENTIFIERS = 3       # how many extracted identifiers to space-join for the "joined" query arm,
                            # matching the real agent's observed query style (EXP-002 traces used 2-3
                            # space-joined identifiers per search_similar_code call, not single terms)
ANISOTROPY_SAMPLE_SIZE = 200  # how many node-pairs to sample per repo for the embedding-anisotropy check

# %%
# ---------------------------------------------------------------- environment + wheelhouse (CPU-only subset)
# Adapted from notebooks/exp009_estop_a_smoke8's proven install-cell pattern, trimmed to what this
# diagnostic actually needs: only `swegemma` (for swegemma.graph.*), no adk_submission/google.adk/vLLM/
# litellm/torch -- this is a pure graph/embedding read, never an agent loop.
import glob, importlib, json, os, subprocess, sys, time, tarfile, re
from pathlib import Path

WHEELHOUSE_DIR = next(Path(p) for p in ['/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse',
                                        '/kaggle/input/gemma-4-developer-agent-wheelhouse'] if Path(p).exists())
for pat in ('/usr/local/lib/python*/dist-packages/*cutlass*.pth', '/usr/local/lib/python*/site-packages/*cutlass*.pth'):
    for pth in glob.glob(pat):
        try:
            os.unlink(pth)
        except OSError:
            pass
tmp_whl = Path('/tmp/wheelhouse'); tmp_whl.mkdir(parents=True, exist_ok=True)
for w in WHEELHOUSE_DIR.glob('*.whl'):
    if 'cutlass' in w.name.lower():
        continue
    name = w.name.replace('cu128', '+cu128') if ('cu128' in w.name and '+' not in w.name) else w.name
    if not (tmp_whl / name).exists():
        os.symlink(w, tmp_whl / name)

REQUIRED_PKGS = ('swegemma',)  # the only package this notebook's diagnostic code actually imports

def _wheel_is_compatible(path: Path) -> bool:
    try:
        from packaging.tags import sys_tags
        from packaging.utils import parse_wheel_filename
    except Exception:  # noqa: BLE001
        return True
    try:
        _, _, _, tags = parse_wheel_filename(path.name)
    except Exception:  # noqa: BLE001
        return True
    supported = set(sys_tags())
    return any(t in supported for t in tags)

all_wheels = sorted(tmp_whl.glob('*.whl'))
usable = [w for w in all_wheels if _wheel_is_compatible(w)]
skipped = [w.name for w in all_wheels if w not in usable]
T_INSTALL = time.time()
proc = subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--no-deps', '--force-reinstall',
                       *(str(w) for w in usable)], capture_output=True, text=True)
if proc.returncode != 0:
    print('bulk install failed; retrying wheel-by-wheel to isolate the bad ones')
    failed = []
    for w in usable:
        r = subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--no-deps', '--force-reinstall', str(w)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            failed.append(w.name)
    skipped += failed
importlib.invalidate_caches()
print(f'wheelhouse: installed {len(all_wheels) - len(skipped)}/{len(all_wheels)} wheels in {time.time() - T_INSTALL:.0f}s '
      f'(python {sys.version_info.major}.{sys.version_info.minor})')
if skipped:
    print(f'  incompatible/failed ({len(skipped)}):', ', '.join(sorted(skipped)[:12]))
missing = []
for _pkg in REQUIRED_PKGS:
    try:
        importlib.import_module(_pkg)
    except Exception as _exc:  # noqa: BLE001
        missing.append(f'{_pkg} ({_exc.__class__.__name__}: {_exc})')
assert not missing, 'required packages unavailable: ' + '; '.join(missing)
print('  required packages present:', ', '.join(REQUIRED_PKGS))

DATA_DIR = next(Path(p) for p in ['/kaggle/input/competitions/gemma-4-developer-agent',
                                  '/kaggle/input/gemma-4-developer-agent'] if Path(p).exists())
GRAPH_DIR = str(DATA_DIR / 'graphs')
EMB_DIR = str(DATA_DIR / 'embeddings')
SNAPSHOTS_DIR = DATA_DIR / 'snapshots'
TASKS_PATH = DATA_DIR / 'tasks.jsonl'
RUN_DIR = Path('/kaggle/working/runs') / EXP_ID
RUN_DIR.mkdir(parents=True, exist_ok=True)
print('data:', DATA_DIR, ' graphs:', GRAPH_DIR, ' embeddings:', EMB_DIR, ' run dir:', RUN_DIR)

# %%
# ---------------------------------------------------------------- real tool internals (not the ADK wrapper)
# tools/graph.py's search_similar_code/get_code_neighbors always call straight into these two functions
# with no transformation of `query`/`node` beyond what's shown here (confirmed by reading
# data/src/swegemma/swegemma/tools/graph.py directly) -- calling them ourselves is behaviourally identical
# to going through the tool, without needing to fake an ADK ToolContext.
from swegemma.graph import graph_utils, retrieval_utils, embedding_utils  # noqa: E402

def load_graph(repo_name: str, base_commit: str):
    return graph_utils.get_graph(
        repo_name=repo_name, use_local_storage=True,
        graph_dir=GRAPH_DIR, embeddings_dir=EMB_DIR, base_commit=base_commit,
    )

def call_search_similar_code(query: str, graph, repo_name: str, base_commit: str, k: int = K):
    """Mirrors tools/graph.py:search_similar_code's call to get_similar_nodes exactly."""
    return retrieval_utils.get_similar_nodes(
        node=query, repo_name=repo_name, k=k, graph=graph,
        use_local_storage=True, graph_dir=GRAPH_DIR, embeddings_dir=EMB_DIR, base_commit=base_commit,
    )

def call_get_code_neighbors(node: str, graph, repo_name: str, base_commit: str, max_neighbors: int = MAX_NEIGHBORS):
    """Mirrors tools/graph.py:get_code_neighbors -- note the `repo_name;node` prefix it adds, which
    search_similar_code's call does NOT do (confirmed asymmetry in the real wrapper)."""
    node_arg = node if ';' in str(node) else f'{repo_name};{node}'
    result = graph_utils.get_neighbor(
        node=node_arg, graph=graph, max_neighbors=max_neighbors, edge_type=None,
        use_local_storage=True, repo_name=repo_name, graph_dir=GRAPH_DIR, embeddings_dir=EMB_DIR,
        base_commit=base_commit,
    )
    return result if isinstance(result, list) else result.get(node_arg, [])

# %%
# ---------------------------------------------------------------- gold extraction (same logic as
# tools/recall_extract_gold.py, reproduced inline so this notebook is self-contained and regenerates gold
# straight from the real Kaggle-mounted tasks.jsonl + snapshots, rather than depending on a separately
# uploaded copy of the local gold.jsonl).
import ast
from dataclasses import dataclass, field

HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

@dataclass
class Hunk:
    file_path: str
    old_start: int
    old_len: int
    new_start: int
    new_len: int

def parse_unified_diff(patch_text: str) -> list[Hunk]:
    hunks: list[Hunk] = []
    cur_file = None
    cur_hunk = None
    for raw_line in patch_text.splitlines():
        if raw_line.startswith("diff --git "):
            cur_file = None; cur_hunk = None; continue
        if raw_line.startswith("+++ "):
            path = raw_line[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            cur_file = None if path == "/dev/null" else path
            continue
        if raw_line.startswith("--- "):
            continue
        m = HUNK_HEADER_RE.match(raw_line)
        if m:
            if cur_hunk is not None:
                hunks.append(cur_hunk)
            cur_hunk = Hunk(
                file_path=cur_file or "", old_start=int(m.group(1)),
                old_len=int(m.group(2)) if m.group(2) is not None else 1,
                new_start=int(m.group(3)), new_len=int(m.group(4)) if m.group(4) is not None else 1,
            )
    if cur_hunk is not None:
        hunks.append(cur_hunk)
    return [h for h in hunks if h.file_path.endswith(".py")]

class ScopeFinder(ast.NodeVisitor):
    def __init__(self):
        self.ranges: list[tuple[int, int, str, str]] = []
    def _visit_def(self, node, prefix, kind):
        qualname = f"{prefix}.{node.name}" if prefix else node.name
        end = getattr(node, "end_lineno", node.lineno)
        self.ranges.append((node.lineno, end, qualname, kind))
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._visit_def(child, qualname, "function")
            elif isinstance(child, ast.ClassDef):
                self._visit_def(child, qualname, "class")
    def visit_Module(self, node):
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._visit_def(child, "", "function")
            elif isinstance(child, ast.ClassDef):
                self._visit_def(child, "", "class")

def build_scope_index(source: str):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [], True
    finder = ScopeFinder(); finder.visit(tree)
    return finder.ranges, False

def enclosing_symbol(ranges, line: int):
    best = None
    for start, end, qualname, kind in ranges:
        if start <= line <= end and (best is None or (end - start) < (best[1] - best[0])):
            best = (start, end, qualname, kind)
    return (best[2], best[3]) if best else None

def module_qualname(file_path: str) -> str:
    p = file_path[:-3] if file_path.endswith(".py") else file_path
    p = p.replace("/", ".")
    return p[: -len(".__init__")] if p.endswith(".__init__") else p

def read_snapshot_file(tgz_path: Path, rel_path: str):
    try:
        with tarfile.open(tgz_path) as tf:
            for candidate in (f"./{rel_path}", rel_path):
                try:
                    member = tf.getmember(candidate)
                except KeyError:
                    continue
                f = tf.extractfile(member)
                return f.read().decode("utf-8", errors="replace") if f else None
    except (FileNotFoundError, tarfile.TarError):
        return None
    return None

def snapshot_py_files(tgz_path: Path) -> set[str]:
    try:
        with tarfile.open(tgz_path) as tf:
            out = set()
            for name in tf.getnames():
                n = name[2:] if name.startswith("./") else name
                if n.endswith(".py"):
                    out.add(n)
            return out
    except (FileNotFoundError, tarfile.TarError):
        return set()

def extract_gold_for_task(task: dict) -> dict:
    instance_id = task["instance_id"]
    snapshot_path = SNAPSHOTS_DIR / f"{instance_id}.tgz"
    result = {"instance_id": instance_id, "snapshot_found": snapshot_path.exists(), "gold_symbols": []}
    if not snapshot_path.exists():
        return result
    hunks = parse_unified_diff(task.get("patch") or "")
    by_file: dict[str, list[Hunk]] = {}
    for h in hunks:
        by_file.setdefault(h.file_path, []).append(h)
    gold: dict[tuple[str, str], dict] = {}
    for file_path, file_hunks in by_file.items():
        base_source = read_snapshot_file(snapshot_path, file_path)
        if base_source is None:
            key = (file_path, module_qualname(file_path))
            gold.setdefault(key, {"file": file_path, "qualname": module_qualname(file_path),
                                  "kind": "new_module", "formatting_only": False})
            continue
        ranges, _had_err = build_scope_index(base_source)
        for h in file_hunks:
            anchor_line = max(1, h.old_start) if h.old_len == 0 else h.old_start + max(0, h.old_len // 2)
            found = enclosing_symbol(ranges, anchor_line)
            if found is None:
                qualname, kind = module_qualname(file_path), "module_level"
            else:
                qn, kind = found
                qualname = f"{module_qualname(file_path)}.{qn}"
            key = (file_path, qualname)
            gold.setdefault(key, {"file": file_path, "qualname": qualname, "kind": kind, "formatting_only": False})
    result["gold_symbols"] = sorted(gold.values(), key=lambda r: (r["file"], r["qualname"]))
    return result

# %%
# ---------------------------------------------------------------- identifier extraction (same regex set as
# tools/recall_grep_baseline.py, reproduced inline for the same self-containment reason as gold extraction)
STOPWORDS = {
    "the", "this", "that", "with", "from", "when", "what", "which", "where", "there",
    "should", "would", "could", "function", "method", "class", "error", "issue", "problem",
    "python", "code", "value", "values", "return", "returns", "result", "example", "using",
    "used", "will", "does", "test", "tests", "case", "cases", "import", "none", "true",
    "false", "self", "args", "kwargs",
}
DOTTED_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){1,5}\b")
CAMEL_RE = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+\b")
SNAKE_RE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")

def extract_identifiers(text: str) -> list[str]:
    if not text:
        return []
    found = list(DOTTED_RE.findall(text)) + list(CAMEL_RE.findall(text))
    for m in SNAKE_RE.findall(text):
        if m not in STOPWORDS and len(m) >= 4:
            found.append(m)
    seen, out = set(), []
    for ident in found:
        if ident not in seen:
            seen.add(ident); out.append(ident)
    return out

# %%
# ---------------------------------------------------------------- node-name <-> file-path mapping
# The real graph node attribute schema is unverified from this checkout (no local data/graphs to inspect),
# so rather than assume a 'file'/'path' node attribute exists, this maps dotted node names back to files by
# longest-prefix match against the snapshot's actual .py file list -- the same direction-reversal of
# module_qualname() used for gold extraction. A node_name that maps to nothing is logged, not silently
# mis-scored, which is itself a finding (either the mapping heuristic is wrong, or the node naming
# convention differs from what gold extraction assumes).
def node_name_to_file(node_name: str, valid_files: set[str]) -> str | None:
    name = str(node_name)
    if ';' in name:
        name = name.split(';', 1)[1]
    parts = name.split('.')
    for i in range(len(parts), 0, -1):
        cand = '/'.join(parts[:i]) + '.py'
        if cand in valid_files:
            return cand
        cand_init = '/'.join(parts[:i]) + '/__init__.py'
        if cand_init in valid_files:
            return cand_init
    return None

def is_test_file(file_path: str | None) -> bool:
    if not file_path:
        return False
    parts = file_path.split('/')
    return any(p in ('test', 'tests') for p in parts[:-1]) or parts[-1].startswith('test_')

# %%
# ---------------------------------------------------------------- main replay loop
import random

with TASKS_PATH.open(encoding="utf-8") as f:
    all_tasks = [json.loads(line) for line in f if line.strip()]
tasks_by_id = {t["instance_id"]: t for t in all_tasks}

per_task_records = []
graph_cache: dict[tuple[str, str], object] = {}
anisotropy_samples: dict[str, list[float]] = {}
zero_vector_checks = []
unmapped_node_names = []

task_ids = list(tasks_by_id.keys())
if MAX_TASKS is not None:
    random.Random(20261018).shuffle(task_ids)
    task_ids = task_ids[:MAX_TASKS]

n_skipped_no_snapshot = 0
n_skipped_no_gold = 0
n_skipped_no_identifiers = 0
n_scored = 0
n_graph_load_errors = 0

for instance_id in task_ids:
    task = tasks_by_id[instance_id]
    repo_name = task["repo"]
    base_commit = task["base_commit"]

    gold_rec = extract_gold_for_task(task)
    if not gold_rec["snapshot_found"]:
        n_skipped_no_snapshot += 1
        continue
    gold_files = {g["file"] for g in gold_rec["gold_symbols"]
                  if not g["formatting_only"] and g["kind"] != "new_module"}
    if not gold_files:
        n_skipped_no_gold += 1
        continue

    text = (task.get("problem_statement") or "") + "\n" + (task.get("hints_text") or "")
    identifiers = extract_identifiers(text)
    if not identifiers:
        n_skipped_no_identifiers += 1
        continue

    cache_key = (repo_name, base_commit)
    if cache_key not in graph_cache:
        try:
            graph_cache[cache_key] = load_graph(repo_name, base_commit)
        except Exception as exc:  # noqa: BLE001
            graph_cache[cache_key] = None
            n_graph_load_errors += 1
            print(f"[{instance_id}] graph load failed for {repo_name}@{base_commit}: {exc!r}")
    g = graph_cache[cache_key]
    if g is None:
        continue

    valid_files = snapshot_py_files(SNAPSHOTS_DIR / f"{instance_id}.tgz")
    query_single = identifiers[0]
    query_joined = " ".join(identifiers[:TOP_N_IDENTIFIERS])

    rec = {"instance_id": instance_id, "repo": repo_name, "gold_files": sorted(gold_files),
           "identifiers": identifiers[:TOP_N_IDENTIFIERS], "arms": {}}

    for arm_name, query in (("single", query_single), ("joined", query_joined)):
        try:
            resolved = None if any(c.isspace() for c in query) else graph_utils.resolve_node_name(query, g)
            path_taken = "lexical" if any(c.isspace() for c in query) else ("resolved" if resolved else "lexical_fallback")
            results = call_search_similar_code(query, g, repo_name, base_commit, k=K)
        except Exception as exc:  # noqa: BLE001
            rec["arms"][arm_name] = {"error": repr(exc)}
            continue
        mapped_files = []
        n_unmapped = 0
        for item in results:
            nn = item.get("node_name")
            mf = node_name_to_file(nn, valid_files)
            if mf is None:
                n_unmapped += 1
                unmapped_node_names.append({"instance_id": instance_id, "arm": arm_name, "node_name": nn})
            mapped_files.append(mf)
        hit_ranks = [i for i, mf in enumerate(mapped_files) if mf in gold_files]
        n_test = sum(1 for mf in mapped_files if is_test_file(mf))
        rec["arms"][arm_name] = {
            "query": query, "path_taken": path_taken, "resolved_node": resolved,
            "n_results": len(results), "n_unmapped": n_unmapped, "n_test_nodes": n_test,
            "hit_at_1": any(r < 1 for r in hit_ranks), "hit_at_3": any(r < 3 for r in hit_ranks),
            "hit_at_5": any(r < 5 for r in hit_ranks), "hit_at_10": any(r < 10 for r in hit_ranks),
            "top_similarity": round(float(results[0]["similarity"]), 4) if results else None,
            "min_similarity_in_topk": round(float(min(r["similarity"] for r in results)), 4) if results else None,
        }

    # get_code_neighbors chain step: seed on the joined arm's resolved node, else its top-1 result.
    joined_arm = rec["arms"].get("joined", {})
    seed_node = joined_arm.get("resolved_node")
    if seed_node is None and joined_arm.get("n_results", 0) > 0:
        try:
            seed_node = call_search_similar_code(query_joined, g, repo_name, base_commit, k=1)[0]["node_name"]
        except Exception:  # noqa: BLE001
            seed_node = None
    if seed_node is not None:
        try:
            neighbors = call_get_code_neighbors(seed_node, g, repo_name, base_commit)
            neighbor_files = {node_name_to_file(n, valid_files) for n in neighbors}
            rec["neighbors"] = {"seed_node": seed_node, "n_neighbors": len(neighbors),
                                "hit_in_neighbors": bool(gold_files & neighbor_files)}
        except Exception as exc:  # noqa: BLE001
            rec["neighbors"] = {"seed_node": seed_node, "error": repr(exc)}

    # Schema/coverage diagnostic: is each gold symbol's own qualname present as a graph node at all, and
    # does it have a non-zero embedding? Addresses the open "does gold even reach the graph" question.
    gold_node_checks = []
    for gsym in gold_rec["gold_symbols"]:
        if gsym["formatting_only"] or gsym["kind"] == "new_module":
            continue
        qn = gsym["qualname"]
        in_graph = g.has_node(qn) if hasattr(g, "has_node") else (qn in g.nodes)
        vec = None
        try:
            vec = embedding_utils.embed(node_content=qn, repo_name=repo_name, base_commit=base_commit,
                                        embeddings_dir=EMB_DIR)
        except Exception:  # noqa: BLE001
            vec = None
        is_zero_vec = vec is not None and not any(vec) if hasattr(vec, "__iter__") else None
        gold_node_checks.append({"qualname": qn, "in_graph": bool(in_graph), "has_embedding": vec is not None,
                                 "zero_vector": is_zero_vec})
        zero_vector_checks.append(is_zero_vec)
    rec["gold_node_checks"] = gold_node_checks

    per_task_records.append(rec)
    n_scored += 1

# %%
# ---------------------------------------------------------------- embedding-space anisotropy diagnostic
# Follows up on EXP-002's rich_3468 finding (top-10 cosine similarities clustered at 0.9991-0.9997,
# possibly uninformative) -- samples random node pairs per repo actually touched above and reports the
# mean/std of their cosine similarity. If this is high/tight across repos generally (not just rich_3468),
# that's evidence of genuine embedding-space anisotropy, not a one-task fluke.
import numpy as np

def cosine(a, b):
    a = np.asarray(a, dtype=np.float64); b = np.asarray(b, dtype=np.float64)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(np.dot(a, b) / (na * nb)) if na > 0 and nb > 0 else 0.0

anisotropy_summary = {}
for (repo_name, base_commit), g in graph_cache.items():
    if g is None:
        continue
    node_list = list(g.nodes)
    if len(node_list) < 2:
        continue
    vecs = {}
    for n in random.Random(20261018).sample(node_list, min(len(node_list), ANISOTROPY_SAMPLE_SIZE)):
        try:
            v = embedding_utils.embed(node_content=n, repo_name=repo_name, base_commit=base_commit,
                                      embeddings_dir=EMB_DIR)
        except Exception:  # noqa: BLE001
            v = None
        if v is not None:
            vecs[n] = v
    names = list(vecs.keys())
    sims = []
    for i in range(min(len(names), 60)):
        for j in range(i + 1, min(len(names), 60)):
            sims.append(cosine(vecs[names[i]], vecs[names[j]]))
    if sims:
        anisotropy_summary[f"{repo_name}@{base_commit}"] = {
            "n_vectors_sampled": len(names), "n_pairs": len(sims),
            "mean_cosine": round(float(np.mean(sims)), 4), "std_cosine": round(float(np.std(sims)), 4),
        }

# %%
# ---------------------------------------------------------------- aggregate + save
def agg(records, arm, k_field):
    scored = [r["arms"][arm] for r in records if arm in r["arms"] and "error" not in r["arms"][arm]]
    if not scored:
        return None
    return sum(1 for s in scored if s[k_field]) / len(scored)

summary = {
    "exp_id": EXP_ID, "n_total_tasks": len(all_tasks), "n_scored": n_scored,
    "n_skipped_no_snapshot": n_skipped_no_snapshot, "n_skipped_no_gold": n_skipped_no_gold,
    "n_skipped_no_identifiers": n_skipped_no_identifiers, "n_graph_load_errors": n_graph_load_errors,
    "n_unmapped_node_names": len(unmapped_node_names),
    "recall": {
        arm: {f"recall_at_{k}": agg(per_task_records, arm, f"hit_at_{k}") for k in (1, 3, 5, 10)}
        for arm in ("single", "joined")
    },
    "neighbor_chain_hit_rate": (
        sum(1 for r in per_task_records if r.get("neighbors", {}).get("hit_in_neighbors")) /
        sum(1 for r in per_task_records if "neighbors" in r)
        if any("neighbors" in r for r in per_task_records) else None
    ),
    "gold_in_graph_rate": (
        sum(1 for r in per_task_records for c in r["gold_node_checks"] if c["in_graph"]) /
        sum(1 for r in per_task_records for c in r["gold_node_checks"])
        if any(r["gold_node_checks"] for r in per_task_records) else None
    ),
    "gold_has_embedding_rate": (
        sum(1 for r in per_task_records for c in r["gold_node_checks"] if c["has_embedding"]) /
        sum(1 for r in per_task_records for c in r["gold_node_checks"])
        if any(r["gold_node_checks"] for r in per_task_records) else None
    ),
    "anisotropy_by_repo": anisotropy_summary,
}

with (RUN_DIR / "per_task_records.jsonl").open("w", encoding="utf-8") as f:
    for r in per_task_records:
        f.write(json.dumps(r) + "\n")
with (RUN_DIR / "unmapped_node_names.jsonl").open("w", encoding="utf-8") as f:
    for u in unmapped_node_names:
        f.write(json.dumps(u) + "\n")
with (RUN_DIR / "summary.json").open("w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print(json.dumps(summary, indent=2))
print(f"\nwrote: {RUN_DIR / 'summary.json'}, per_task_records.jsonl, unmapped_node_names.jsonl")
print("\nCompare against the local, zero-Kaggle git-grep baseline (experiments/recall_check/README.md):")
print("  recall@1/3/5/10 = 24.8% / 35.4% / 37.2% / 41.6%  (n=113, problem_statement+hints_text identifiers)")
