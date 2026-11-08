# %% [markdown]
# # EXP-054: exact-copy LoRA on the E4B, stages 1 to 3 in one kernel (zero tasks, no agent run, no grading)
#
# Pre-registration: `experiments/EXP-054-exact-copy-lora-train-eval-e4b.md`. Stage 1 builds edit pairs from
# public files only (the kernel's own Python standard library), with each file window rendered by the harness's
# own `read_file` tool and each request rendered by the harness's own ADK and LiteLLM path. Stage 2 trains a
# rank-8 LoRA on `q_proj` and `o_proj` with the loss on the call tokens only, with anchor pairs for non-edit calls.
# Stage 3 serves the w4a16 checkpoint under the harness's own `VllmServer`, base against adapter, on held-out
# windows (exact-copy rate), on first-turn prompts (drift probe), on two prose texts (logprobs) and for decode
# speed. The readings are applied offline by `experiments/EXP-054/analyze_copy_lora.py`.
#
# **Inputs:** dataset `metric/gemma-4-developer-agent-wheelhouse`; models
# `google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2` (served) and
# `google/gemma-4/transformers/gemma-4-e4b-it-qat-q4_0-unquantized/2` (BF16, trained on); the competition source
# is attached only so that the kernel gets 4 GPUs (EXP-047 v1); nothing under it is read.
# **Accelerator:** NVIDIA L4 x4. **Internet:** off.
#
# Build: `python tools/build_notebook.py --src notebooks/exp054_copylora/copy_lora.py --embed dist/EXP-038-e4b.zip --out notebooks/exp054_copylora/copy_lora.ipynb`
# Retrieve: `kaggle kernels output rainm4/gemma4-exp054-copy-lora -p runs/EXP-054-copy-lora`

# %%
# ---------------------------------------------------------------- parameters
EXP_ID = "EXP-054-copy-lora"
MODEL = "gemma-4-e4b-it-qat-w4a16-ct"
MODEL_DIR = f"/kaggle/input/models/google/gemma-4/other/{MODEL}/2"
BF16_NAME = "gemma-4-e4b-it-qat-q4_0-unquantized"
SUBMISSION_B64 = ""
ZIP_SHA256 = "9de869bd2cd8853b72d653d06b9acef3e03794c8b588c26494435774dda11ac0"
SEED = 54
HARD_CAP_S = 3400              # every wait is bounded so that the kernel ends near this
BOOT0_STARTUP_TIMEOUT_S = 600
BOOT1_STARTUP_TIMEOUT_S = 720
BOOT0_PHASE_S = 560            # boot 0 request phase (base eval, drift, training generations)
BOOT1_PHASE_S = 600            # boot 1 request phase (base1 and adapter, interleaved)
BOOT1_LATEST_START_S = 2500    # boot 1 is not started after this
TRAIN_END_S = 2050             # the training loop stops by this kernel second
TRAIN_CAP_S = 660              # and after at most this many seconds of optimisation
REQ_TIMEOUT_S = 420
CONCURRENCY = 48
N_EVAL = 120                   # held-out edit windows, greedy
N_DRIFT = 48                   # held-out first-turn prompts, greedy
N_T1 = 60                      # held-out edit windows at the shipped sampling, boot 1 only
N_TRAIN = 400                  # training edit windows, one generation each at the shipped sampling
N_TRAIN_FIRST = 64             # training first-turn prompts (anchors)
LORA_R = 8
LORA_ALPHA = 16
LR = 5e-4
WARMUP_STEPS = 5
GRAD_ACCUM = 2
MAX_EPOCHS = 2
SEQ_LADDER = [12288, 10240, 8192, 6144, 4096]
DECODE_MAX_TOKENS = 256
# Fixed inputs, written for EXP-047 in our own words (reused unchanged).
LOGPROB_PROMPTS = [
    "The old lighthouse stood at the edge of the cliff for more than a century. Every evening the keeper climbed "
    "the narrow stairs, cleaned the great lens and lit the lamp before the sun went down. Ships that passed in the "
    "night could see the slow turning beam from many miles away, and the sailors knew that the rocks below were "
    "close. In winter the wind was so strong that the windows rattled in their frames, and the keeper wrote short "
    "notes in a logbook about the weather, the ships he saw and the birds that sheltered on the gallery. When the "
    "light was finally automated, the logbooks were carried down to the village and kept in the small library, "
    "where children still read them on rainy afternoons.",
    "A good recipe for bread needs only flour, water, salt and yeast, but the order and the timing matter. First "
    "the flour and water are mixed and left to rest, so that the dough becomes smooth without much kneading. Then "
    "the salt and the yeast are added, and the dough is folded every half hour while it rises in a warm place. "
    "After a few hours it is shaped into a round loaf, placed in a floured basket and left in a cool room "
    "overnight. In the morning the oven is heated with a heavy pot inside it, the loaf is turned out into the pot, "
    "and the lid is kept on for the first part of the bake so that the crust stays thin and the inside stays soft.",
]
DECODE_PROMPT = "Write a numbered list of short, simple sentences about the seasons of the year."
PRIOR_THOUGHT = "I will open the function named in the task so that I can see its exact code before I change it."

# %%
# ---------------------------------------------------------------- environment + wheelhouse (hosts' recipe, as EXP-047)
import asyncio, base64, concurrent.futures as cf, copy, glob, hashlib, importlib, importlib.metadata as im_md
import io, json, os, re, shutil, subprocess, sys, threading, time, zipfile
import urllib.error, urllib.request
from pathlib import Path
from types import SimpleNamespace

T0 = time.monotonic()


def elapsed() -> float:
    return time.monotonic() - T0


os.environ.update({
    'LITELLM_LOCAL_MODEL_COST_MAP': 'True', 'TRANSFORMERS_NO_TF': '1', 'VLLM_WORKER_MULTIPROC_METHOD': 'spawn',
    'VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS': '1', 'VLLM_ENGINE_READY_TIMEOUT_S': '1200',
    'VLLM_NO_USAGE_STATS': '1', 'OTEL_SDK_DISABLED': 'true', 'PYTORCH_CUDA_ALLOC_CONF': 'expandable_segments:True',
    'NCCL_DEBUG': 'WARN', 'TRANSFORMERS_OFFLINE': '1', 'HF_HUB_OFFLINE': '1', 'VLLM_LOGGING_LEVEL': 'INFO',
    'TOKENIZERS_PARALLELISM': 'false',
})

RUN_DIR = Path('/kaggle/working/runs') / EXP_ID
RUN_DIR.mkdir(parents=True, exist_ok=True)
WORK = Path('/tmp/exp054')
shutil.rmtree(WORK, ignore_errors=True); WORK.mkdir(parents=True)
RUN: dict = {'exp_id': EXP_ID, 'model': MODEL, 'status': 'started', 'stages': {}, 'paths': {}}


def save_run():
    RUN['elapsed_s'] = round(elapsed(), 1)
    (RUN_DIR / 'run.json').write_text(json.dumps(RUN, indent=1, default=str))


def stage(name: str, **kw):
    RUN['stages'][name] = {'t_s': round(elapsed(), 1), **kw}
    save_run()
    print(f'[{elapsed():7.1f}s] {name}', json.dumps(kw, default=str)[:600] if kw else '')


def stop(status: str, why: str):
    RUN['status'] = status; stage('stopped', why=why)
    raise SystemExit(why)


WHEELHOUSE_DIR = next((Path(p) for p in ['/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse',
                                         '/kaggle/input/gemma-4-developer-agent-wheelhouse'] if Path(p).exists()), None)
if WHEELHOUSE_DIR is None:
    stop('infrastructure', 'wheelhouse input missing')
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


def _wheel_is_compatible(path: Path) -> bool:
    try:
        from packaging.tags import sys_tags
        from packaging.utils import parse_wheel_filename
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
    print('bulk install failed; retrying wheel-by-wheel')
    for w in usable:
        r = subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--no-deps', '--force-reinstall', str(w)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            skipped.append(w.name)
importlib.invalidate_caches()
print(f'wheelhouse: installed {len(all_wheels) - len(skipped)}/{len(all_wheels)} wheels in {time.time() - T_INSTALL:.0f}s')

try:
    import torch
    import vllm  # noqa: F401
    from adk_submission import compile_submission, discover_adapters, discover_declared_models
    from adk_submission.server import VllmConfig, VllmServer
    from swegemma.config import ALLOWED_ADAPTER_EXTENSIONS
except Exception as _exc:  # noqa: BLE001
    RUN['import_error'] = f'{type(_exc).__name__}: {_exc}'
    stop('infrastructure', 'imports failed')

env = {'python': sys.version, 'install_s': round(time.time() - T_INSTALL, 1), 'skipped_wheels': skipped,
       'wheelhouse_dir': str(WHEELHOUSE_DIR), 'n_wheels': len(all_wheels)}
for pkg in ('vllm', 'torch', 'transformers', 'compressed-tensors', 'adk_submission', 'swegemma', 'google-adk',
            'litellm', 'safetensors', 'peft'):
    try:
        env[pkg] = im_md.version(pkg)
    except im_md.PackageNotFoundError:
        env[pkg] = None
GPU_COUNT = torch.cuda.device_count() if torch.cuda.is_available() else 0
env['gpu_count'] = GPU_COUNT
try:
    env['gpu_total_mib'] = [round(torch.cuda.get_device_properties(i).total_memory / 2**20) for i in range(GPU_COUNT)]
except Exception:  # noqa: BLE001
    pass
try:
    mem = dict(ln.split(':', 1) for ln in Path('/proc/meminfo').read_text().splitlines() if ':' in ln)
    env['mem_total_gib'] = round(int(mem['MemTotal'].split()[0]) / 2**20, 1)
    env['mem_available_gib'] = round(int(mem['MemAvailable'].split()[0]) / 2**20, 1)
except Exception:  # noqa: BLE001
    pass
env['cpu_count'] = os.cpu_count()
# the BF16 parent: the model mount only, never a recursive walk of /kaggle/input (the competition mount is there)
cands = [p for p in (f'/kaggle/input/models/google/gemma-4/transformers/{BF16_NAME}/2/config.json',
                     f'/kaggle/input/gemma-4/transformers/{BF16_NAME}/2/config.json') if Path(p).exists()]
cands = cands or sorted(glob.glob(f'/kaggle/input/models/**/{BF16_NAME}/*/config.json', recursive=True))
BF16_DIR = str(Path(cands[0]).parent) if cands else None
env['bf16_dir'] = BF16_DIR
RUN['env'] = env
(RUN_DIR / 'env.json').write_text(json.dumps(env, indent=1))
print(json.dumps(env, indent=1))
if GPU_COUNT != 4 or not Path(MODEL_DIR, 'config.json').exists():
    stop('infrastructure', f'need 4 GPUs and the E4B input; gpu_count={GPU_COUNT}')

# the shipped E4B tree (S-014), embedded and checked by sha256
zbytes = base64.b64decode(SUBMISSION_B64)
RUN['zip_sha256'] = hashlib.sha256(zbytes).hexdigest()
if RUN['zip_sha256'] != ZIP_SHA256:
    stop('infrastructure', 'embedded zip sha256 mismatch')
SUB0 = Path('/kaggle/working/sub0')   # the shipped tree, no adapters/ (boot 0)
SUB1 = Path('/kaggle/working/sub1')   # the shipped tree plus adapters/copy_lora and an adapter line (boot 1)
for d in (SUB0, SUB1):
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
with zipfile.ZipFile(io.BytesIO(zbytes)) as zf:
    zf.extractall(SUB0)
    zf.extractall(SUB1)
RUN['sub0_files'] = sorted(str(p.relative_to(SUB0)) for p in SUB0.rglob('*') if p.is_file())
stage('installed', gpu_count=GPU_COUNT, bf16_dir=BF16_DIR, mem_available_gib=env.get('mem_available_gib'))

# %%
# ---------------------------------------------------------------- stage 1a: edit items from public files
# The kernel's own Python standard library. Each package is one "repository"; packages are split into training
# and held-out by a hash of the package name. Edits are made by the ast, in functions of 6 to 90 lines:
#   K1  the integer constant that occurs once in the function, n -> n + 1
#   K2  the one `==` or `!=` in the function, flipped
#   K3  a one-line call statement whose callee occurs once in the function, deleted
# The target `old_string` is the smallest block of 2 or more whole lines around the edited line that occurs
# once in the whole file; `new_string` is that block with the edit made.
import ast
import random
import sysconfig
from collections import Counter

STDLIB = Path(sysconfig.get_paths()['stdlib'])
EXCLUDE_PARTS = {'test', 'tests', 'idle_test', 'encodings', 'pydoc_data', 'site-packages', 'dist-packages',
                 'lib2to3', 'turtledemo', '__pycache__', 'ensurepip', 'venv', 'idlelib', '__phello__'}
WS_BASE = WORK / 'ws'


def file_text_ok(p: Path):
    try:
        b = p.read_bytes()
    except OSError:
        return None
    if b'\r' in b or not b.isascii():
        return None
    t = b.decode('ascii')
    if any(s in t for s in ('<|', '|>', 'tool_call', '<tool')) or not t.endswith('\n'):
        return None
    n = t.count('\n')
    return t if 80 <= n <= 4000 else None


def top_functions(tree):
    """Module-level functions and class methods (not nested functions), with a qualified name."""
    out = []

    def walk(node, prefix):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.append((prefix + ch.name, ch))
            elif isinstance(ch, ast.ClassDef):
                walk(ch, prefix + ch.name + '.')
    walk(tree, '')
    return out


def _src_order(nodes):
    return sorted(nodes, key=lambda n: (n.lineno, n.col_offset))


def find_edits(fn, lines):
    """Return up to one edit per kind for this function: dicts with kind, line index, new line text or None."""
    res = []
    # K1
    consts = _src_order([n for n in ast.walk(fn) if isinstance(n, ast.Constant) and type(n.value) is int])
    cnt = Counter(n.value for n in consts)
    for n in consts:
        if cnt[n.value] != 1 or not (0 <= n.value <= 9999) or n.lineno != n.end_lineno or n.lineno == fn.lineno:
            continue
        ln = lines[n.lineno - 1]
        if ln[n.col_offset:n.end_col_offset] != str(n.value):
            continue
        res.append({'kind': 'K1', 'e': n.lineno - 1, 'value': n.value,
                    'new_line': ln[:n.col_offset] + str(n.value + 1) + ln[n.end_col_offset:]})
        break
    # K2
    eqs = [(n, op) for n in ast.walk(fn) if isinstance(n, ast.Compare) for op in n.ops
           if isinstance(op, (ast.Eq, ast.NotEq))]
    if len(eqs) == 1:
        n, op = eqs[0]
        if len(n.ops) == 1 and n.lineno == n.end_lineno and n.lineno != fn.lineno:
            ln = lines[n.lineno - 1]
            a, b = n.left.end_col_offset, n.comparators[0].col_offset
            sym = '==' if isinstance(op, ast.Eq) else '!='
            if n.left.end_lineno == n.lineno and n.comparators[0].lineno == n.lineno and ln[a:b].strip() == sym:
                new = '!=' if sym == '==' else '=='
                res.append({'kind': 'K2', 'e': n.lineno - 1, 'op': sym, 'new_op': new,
                            'new_line': ln[:a] + ln[a:b].replace(sym, new, 1) + ln[b:]})
    # K3
    callee = Counter()
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            f = n.func
            callee[f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None] += 1
    stmts = []
    for node in ast.walk(fn):
        for field in ('body', 'orelse', 'finalbody'):
            lst = getattr(node, field, None)
            if isinstance(lst, list) and len(lst) > 1:
                stmts.extend(st for st in lst if isinstance(st, ast.Expr) and isinstance(st.value, ast.Call))
    for st in _src_order(stmts):
        f = st.value.func
        nm = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
        if nm is None or callee[nm] != 1 or st.lineno != st.end_lineno:
            continue
        ln = lines[st.lineno - 1]
        if ln[:st.col_offset].strip() or ln[st.col_offset:].rstrip() != ln[st.col_offset:st.end_col_offset]:
            continue
        res.append({'kind': 'K3', 'e': st.lineno - 1, 'callee': nm, 'new_line': None})
        break
    return res


def unique_in(content: str, s: str) -> bool:
    i = content.find(s)
    return i >= 0 and content.find(s, i + 1) == -1


def make_block(content: str, lines: list, e: int, new_line):
    n = len(lines)
    for w in range(2, 9):
        starts = sorted(range(max(0, e - w + 1), min(e, n - w) + 1), key=lambda s: (abs(s + (w - 1) / 2 - e), s))
        for s in starts:
            blk = lines[s:s + w]
            if not blk[0].strip() or not blk[-1].strip():
                continue
            old = '\n'.join(blk)
            if not unique_in(content, old):
                continue
            nb = list(blk)
            if new_line is None:
                del nb[e - s]
            else:
                nb[e - s] = new_line
            return s, w, old, '\n'.join(nb)
    return None


def statement(kind: str, rel: str, qual: str, ed: dict) -> str:
    """Our own words; names the file, the function and the change, and gives no line numbers."""
    if kind == 'K1':
        return (f"In `{rel}`, the function `{qual}` uses the integer constant {ed['value']} where it should use "
                f"{ed['value'] + 1}. That constant appears only once in the function. Change it to "
                f"{ed['value'] + 1} and change nothing else.")
    if kind == 'K2':
        return (f"In `{rel}`, the one equality comparison in the function `{qual}` is the wrong way round: the "
                f"`{ed['op']}` test should be `{ed['new_op']}`. Flip that operator and change nothing else.")
    return (f"In `{rel}`, the function `{qual}` makes a call to `{ed['callee']}` as a statement on its own, and "
            f"that call must no longer be made. Delete that one statement and change nothing else.")


def build_items():
    pkgs = sorted(d.name for d in STDLIB.iterdir()
                  if d.is_dir() and (d / '__init__.py').exists() and d.name not in EXCLUDE_PARTS)
    items, n_files = [], 0
    for pkg in pkgs:
        src = STDLIB / pkg
        for p in sorted(src.rglob('*.py')):
            relp = p.relative_to(src)
            if any(part in EXCLUDE_PARTS for part in relp.parts) or relp.name.startswith('test'):
                continue
            content = file_text_ok(p)
            if content is None:
                continue
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            n_files += 1
            lines = content.split('\n')
            total = len(content.splitlines())
            for qual, fn in top_functions(tree):
                fstart = min([d.lineno for d in fn.decorator_list] + [fn.lineno])
                fend = fn.end_lineno
                if not 6 <= fend - fstart + 1 <= 90:
                    continue
                ws_, we_ = max(1, fstart - 3), min(total, fend + 3)
                if we_ - ws_ + 1 > 150 or len('\n'.join(lines[ws_ - 1:we_])) > 10000:
                    continue
                for ed in find_edits(fn, lines):
                    blk = make_block(content, lines, ed['e'], ed['new_line'])
                    if blk is None:
                        continue
                    s, w, old, new = blk
                    if s + 1 < ws_ or s + w > we_:
                        continue
                    gold = content.replace(old, new, 1)
                    try:
                        if ast.dump(ast.parse(gold)) == ast.dump(tree):
                            continue
                    except SyntaxError:
                        continue
                    rel = f'{pkg}/{relp.as_posix()}'
                    items.append({'pkg': pkg, 'rel': rel, 'src': str(p), 'kind': ed['kind'], 'qual': qual,
                                  'fstart': fstart, 'fend': fend, 'win': [ws_, we_], 'block': [s + 1, s + w],
                                  'old': old, 'new': new, 'statement': statement(ed['kind'], rel, qual, ed)})
    return pkgs, n_files, items


PKGS, N_FILES, ALL_ITEMS = build_items()
by_pkg = Counter(it['pkg'] for it in ALL_ITEMS)
order = sorted(by_pkg, key=lambda k: hashlib.sha256(k.encode()).hexdigest())
HELD, n_held = [], 0
for k in order:   # held-out packages: first in hash order until 20% of packages and 400 items
    if len(HELD) >= max(3, round(0.2 * len(by_pkg))) and n_held >= 400:
        break
    HELD.append(k); n_held += by_pkg[k]
HELD = set(HELD)
rng = random.Random(SEED)


def pick(pool, n):
    """Balanced over K1/K2/K3 and spread over files: one item per function, at most 3 per (file, kind)."""
    seen, per_file, buckets = set(), Counter(), {'K1': [], 'K2': [], 'K3': []}
    for it in sorted(pool, key=lambda it: hashlib.sha256((it['rel'] + it['qual'] + it['kind']).encode()).hexdigest()):
        if (it['rel'], it['qual']) in seen or per_file[(it['rel'], it['kind'])] >= 3:
            continue
        seen.add((it['rel'], it['qual'])); per_file[(it['rel'], it['kind'])] += 1
        buckets[it['kind']].append(it)
    out, i = [], 0
    while len(out) < n and any(buckets.values()):
        k = ('K1', 'K2', 'K3')[i % 3]; i += 1
        if buckets[k]:
            out.append(buckets[k].pop(0))
    return out


held_pool = [it for it in ALL_ITEMS if it['pkg'] in HELD]
train_pool = [it for it in ALL_ITEMS if it['pkg'] not in HELD]
EVAL = pick(held_pool, N_EVAL)
TRAIN = pick(train_pool, N_TRAIN)
used = {id(it) for it in TRAIN}
TRAIN_FIRST = [it for it in pick([it for it in train_pool if id(it) not in used], N_TRAIN_FIRST)]
DRIFT = EVAL[::max(1, len(EVAL) // N_DRIFT)][:N_DRIFT]
for name, lst in (('eval', EVAL), ('train', TRAIN), ('train_first', TRAIN_FIRST)):
    for j, it in enumerate(lst):
        it.setdefault('ids', []).append(f'{name}-{j:03d}')
for j, it in enumerate(EVAL):
    it['pid'] = f'e{j:03d}'
for j, it in enumerate(TRAIN):
    it['pid'] = f't{j:03d}'
for j, it in enumerate(TRAIN_FIRST):
    it['pid'] = f'f{j:03d}'
RUN['data'] = {'stdlib': str(STDLIB), 'n_packages': len(PKGS), 'n_files': N_FILES, 'n_items': len(ALL_ITEMS),
               'held_packages': sorted(HELD), 'n_held_items': len(held_pool), 'n_train_items': len(train_pool),
               'n_eval': len(EVAL), 'n_drift': len(DRIFT), 'n_train': len(TRAIN), 'n_train_first': len(TRAIN_FIRST),
               'eval_kinds': dict(Counter(it['kind'] for it in EVAL)),
               'train_kinds': dict(Counter(it['kind'] for it in TRAIN))}
stage('items', **{k: v for k, v in RUN['data'].items() if k != 'held_packages'})
if len(EVAL) < 60 or len(TRAIN) < 64:
    stop('infrastructure', 'too few items')

# %%
# ---------------------------------------------------------------- stage 1b: workspaces, the harness's tree, prompt and read_file
PATHS = RUN['paths']


def make_workspace(pkg: str) -> Path:
    root = WS_BASE / pkg
    if not root.exists():
        shutil.copytree(STDLIB / pkg, root / pkg,
                        ignore=shutil.ignore_patterns('__pycache__', 'test', 'tests', 'idle_test', '*.pyc'))
    return root


try:
    from swegemma.harness.agent_runner import build_agent_prompt, build_workspace_tree_command
    PATHS['prompt'] = 'swegemma.build_agent_prompt'
except Exception as exc:  # noqa: BLE001
    build_agent_prompt = build_workspace_tree_command = None
    PATHS['prompt'] = f'unavailable: {type(exc).__name__}'
try:
    from swegemma.config import EvalConfig
    EVAL_CFG = EvalConfig(tasks_path=Path('/tmp/exp054_none/tasks.jsonl'), snapshots_dir=Path('/tmp/exp054_none'),
                          results_dir=Path('/tmp/exp054_none'), submission_dir=SUB0, models=None,
                          graph_dir='/tmp/exp054_none', embeddings_dir='/tmp/exp054_none',
                          timeout_seconds=240, max_tool_calls=28, max_time_minutes=8, max_turns=80)
    PATHS['eval_config'] = 'swegemma.EvalConfig'
except Exception as exc:  # noqa: BLE001
    EVAL_CFG = SimpleNamespace(
        budget=SimpleNamespace(time_minutes=8, tool_calls=28, turns=80, cost_usd=None),
        harness=SimpleNamespace(command_timeout_seconds=240, max_stdout_chars=5000, max_file_lines=150,
                                max_file_chars=10000),
        graph_dir=None, embeddings_dir=None, enable_sandbox_testing=True)
    PATHS['eval_config'] = f'namespace ({type(exc).__name__})'
DECLARED = ['run_command', 'read_file', 'edit_file', 'write_file', 'get_status', 'submit_patch']
TREES: dict = {}


def tree_for(pkg: str) -> str:
    if pkg not in TREES:
        root = make_workspace(pkg)
        if build_workspace_tree_command is not None:
            r = subprocess.run(['bash', '-c', build_workspace_tree_command(max_lines=200, workspace_dir=str(root))],
                               capture_output=True, text=True, timeout=60)
            TREES[pkg] = r.stdout.strip() if r.returncode == 0 else ''
        else:
            TREES[pkg] = ''
    return TREES[pkg]


class _StubDocker:
    """Serves `copy_from` out of the local workspace, as the sandbox would out of /workspace."""

    def __init__(self):
        self.root = None

    def copy_from(self, container_id, src, dest):
        s = str(src)
        s = s[len('/workspace/'):] if s.startswith('/workspace/') else s.lstrip('/')
        p = self.root / s
        if p.is_file():
            shutil.copyfile(p, dest)


class _StubCtx:
    def __init__(self):
        self.docker = _StubDocker(); self.container_id = 'exp054'; self.budget = None; self.tool_lock = None
        self.tool_calls_used = None
        self.harness = SimpleNamespace(max_file_lines=150, max_file_chars=10000, max_stdout_chars=5000,
                                       command_timeout_seconds=240)

    def check_budget(self, count_tool_call=True):
        return None


STUB = _StubCtx()
try:
    from swegemma.tools.workspace import make_read_file
    READ_TOOL = make_read_file(STUB)
    PATHS['read_file'] = 'swegemma.make_read_file'
except Exception as exc:  # noqa: BLE001
    READ_TOOL = None
    PATHS['read_file'] = f'unavailable: {type(exc).__name__}'
try:
    from swegemma.edit import apply_replacement
    PATHS['apply_replacement'] = 'swegemma.edit'
except Exception as exc:  # noqa: BLE001
    apply_replacement = None
    PATHS['apply_replacement'] = f'unavailable: {type(exc).__name__}'


def render_read(it: dict) -> dict:
    STUB.docker.root = make_workspace(it['pkg'])
    if READ_TOOL is not None:
        return READ_TOOL(it['rel'], it['win'][0], it['win'][1])
    content = (STUB.docker.root / it['rel']).read_text()
    lines = content.splitlines()
    s, e = it['win']
    return {'status': 'ok', 'filepath': it['rel'], 'content': '\n'.join(lines[s - 1:e]), 'start_line': s,
            'end_line': e, 'total_lines': len(lines), 'is_truncated': False}


def user_prompt(it: dict) -> str:
    tree = tree_for(it['pkg'])
    task = SimpleNamespace(repo=f"python-stdlib/{it['pkg']}", problem_statement=it['statement'], hints_text='',
                           base_commit=None)
    if build_agent_prompt is not None:
        return build_agent_prompt(task, EVAL_CFG, tree, enable_sandbox_testing=True, declared_tools=DECLARED)
    return f'You are evaluating a software engineering task for repository {task.repo}.\n\nProblem Statement:\n{task.problem_statement}\n'


n_bad_window = 0
for it in EVAL + TRAIN + TRAIN_FIRST:
    it['user'] = user_prompt(it)
    if it['pid'].startswith('f'):
        continue
    resp = render_read(it)
    it['read_resp'] = resp
    lines = (STUB.docker.root / it['rel']).read_text().split('\n')
    want = '\n'.join(lines[it['win'][0] - 1:it['win'][1]])
    if resp.get('status') != 'ok' or resp.get('content') != want or resp.get('is_truncated'):
        it['bad_window'] = True; n_bad_window += 1
EVAL = [it for it in EVAL if not it.get('bad_window')]
TRAIN = [it for it in TRAIN if not it.get('bad_window')]
DRIFT = [it for it in DRIFT if not it.get('bad_window')]
FILES = {it['rel']: (WS_BASE / it['pkg'] / it['rel']).read_text() for it in EVAL}
stage('rendered', n_bad_window=n_bad_window, n_eval=len(EVAL), n_train=len(TRAIN), n_drift=len(DRIFT),
      paths=dict(PATHS), mean_user_chars=round(sum(len(it['user']) for it in EVAL) / max(1, len(EVAL))))

# %%
# ---------------------------------------------------------------- log capture, teardown, HTTP, probes (as EXP-047)
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')
LOG_PATTERNS = {
    'gpu_kv_cache_tokens': re.compile(r'GPU KV cache size:\s*([\d,]+) tokens'),
    'max_concurrency': re.compile(r'Maximum concurrency for ([\d,]+) tokens per request:\s*([\d.]+)x'),
}


def parse_log(text: str) -> dict:
    text = ANSI_RE.sub('', text)
    out: dict = {}
    m = LOG_PATTERNS['gpu_kv_cache_tokens'].findall(text)
    if m:
        out['gpu_kv_cache_tokens'] = min(int(x.replace(',', '')) for x in m)
    m = LOG_PATTERNS['max_concurrency'].findall(text)
    if m:
        out['max_concurrency'] = min(float(x) for _, x in m)
    return out


def classify_failure(text: str) -> str:
    for status, pat in [('kv_or_max_len', re.compile(r'(?i)max seq len|maximum model length|KV cache is needed')),
                        ('lora_unexpected_modules', re.compile(r'(?i)target modules in|unexpected modules')),
                        ('oom', re.compile(r'CUDA out of memory|OutOfMemoryError')),
                        ('env_error', re.compile(r'undefined symbol|ImportError|ModuleNotFoundError'))]:
        if pat.search(text):
            return status
    return 'other_error'


class LogTee:
    """Copies a VllmServer's log continuously: VllmServer.stop() deletes it."""

    def __init__(self, server, dest: Path):
        self.server, self.dest = server, dest
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._last = 0

    def _copy_once(self):
        path = getattr(self.server, 'log_path', None)
        if not path or not os.path.exists(path):
            return
        try:
            text = open(path, 'r', encoding='utf-8', errors='replace').read()
        except Exception:  # noqa: BLE001
            return
        if len(text) >= self._last:
            self.dest.write_text(text); self._last = len(text)

    def _run(self):
        while not self._stop.is_set():
            self._copy_once(); self._stop.wait(2.0)

    def start(self):
        self._thread.start()

    def stop_and_final_copy(self) -> str:
        self._stop.set(); self._thread.join(timeout=5); self._copy_once()
        return self.dest.read_text() if self.dest.exists() else ''


def _compute_app_pids() -> list:
    try:
        out = subprocess.run(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'],
                             capture_output=True, text=True, timeout=15)
        return [int(x) for x in out.stdout.split() if x.strip().isdigit()]
    except Exception:  # noqa: BLE001
        return []


def teardown(server) -> float:
    t = time.monotonic()
    if server is not None:
        try:
            server.stop(timeout=30)
        except Exception as exc:  # noqa: BLE001
            print('server.stop() raised:', exc)
    for pid in _compute_app_pids():
        if pid != os.getpid():
            try:
                os.kill(pid, 9)
            except Exception:  # noqa: BLE001
                pass
    time.sleep(5)
    return round(time.monotonic() - t, 1)


def http(method: str, url: str, body=None, timeout: float = REQ_TIMEOUT_S) -> dict:
    t = time.monotonic()
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {'status': resp.status, 'json': json.loads(resp.read()), 's': round(time.monotonic() - t, 3)}
    except urllib.error.HTTPError as exc:
        return {'status': exc.code, 'error': exc.read().decode('utf-8', 'replace')[:1500], 's': round(time.monotonic() - t, 3)}
    except Exception as exc:  # noqa: BLE001
        return {'status': None, 'error': f'{type(exc).__name__}: {exc}'[:500], 's': round(time.monotonic() - t, 3),
                'timeout': 'timed out' in str(exc).lower() or isinstance(exc, TimeoutError)}


PROBES = RUN_DIR / 'probes.jsonl'


def record_probe(row: dict):
    with open(PROBES, 'a') as f:
        f.write(json.dumps(row) + '\n')


def prompt_logprobs(base_url: str, model_name: str, prompt: str) -> dict:
    r = http('POST', base_url + '/completions', {'model': model_name, 'prompt': prompt, 'max_tokens': 1,
                                                 'temperature': 0, 'echo': True, 'logprobs': 0}, timeout=120)
    out = {'status': r['status'], 's': r['s'], 'method': 'echo'}
    if r['status'] == 200:
        out['resp_model'] = (r['json'] or {}).get('model')
        try:
            ch = r['json']['choices'][0]
            n_prompt = r['json']['usage']['prompt_tokens']
            lp = ch['logprobs']
            out.update(logprobs=lp['token_logprobs'][1:n_prompt], n_prompt=n_prompt)
            return out
        except Exception as exc:  # noqa: BLE001
            out['parse_error'] = f'{type(exc).__name__}: {exc}'
    else:
        out['error'] = r.get('error')
    r = http('POST', base_url + '/completions', {'model': model_name, 'prompt': prompt, 'max_tokens': 1,
                                                 'temperature': 0, 'prompt_logprobs': 0}, timeout=120)
    out2 = {'status': r['status'], 's': r['s'], 'method': 'prompt_logprobs'}
    if r['status'] == 200:
        out2['resp_model'] = (r['json'] or {}).get('model')
        try:
            pl = r['json']['choices'][0].get('prompt_logprobs') or r['json'].get('prompt_logprobs')
            lps = []
            for pos in pl[1:]:
                (_, ent), = list(pos.items())[:1]
                lps.append(ent['logprob'])
            out2.update(logprobs=lps, n_prompt=len(pl))
        except Exception as exc:  # noqa: BLE001
            out2['parse_error'] = f'{type(exc).__name__}: {exc}'
    else:
        out2['error'] = r.get('error')
    return out2


def decode_probe(base_url: str, model_name: str) -> dict:
    body = {'model': model_name, 'messages': [{'role': 'user', 'content': DECODE_PROMPT}],
            'max_tokens': DECODE_MAX_TOKENS, 'temperature': 0, 'ignore_eos': True,
            'chat_template_kwargs': {'enable_thinking': False}}
    r = http('POST', base_url + '/chat/completions', body, timeout=120)
    out = {'status': r['status'], 's': r['s']}
    if r['status'] == 200:
        out['resp_model'] = r['json'].get('model')
        out['completion_tokens'] = (r['json'].get('usage') or {}).get('completion_tokens')
        if out['completion_tokens'] and r['s']:
            out['tok_s'] = round(out['completion_tokens'] / r['s'], 2)
    else:
        out['error'] = r.get('error')
    return out


def boot(label: str, sub: Path, manifest, startup_timeout: int):
    cfg = VllmConfig(
        model=MODEL_DIR, port=8000, host='127.0.0.1', tool_call_parser='gemma4', reasoning_parser='gemma4',
        default_chat_template_kwargs={'enable_thinking': True}, max_model_len=32768,
        dtype='bfloat16' if torch.cuda.is_bf16_supported() else 'auto', gpu_memory_utilization=0.90,
        enable_auto_tool_choice=True, enable_lora=True, max_loras=8, max_lora_rank=128,
        tensor_parallel_size=4, startup_timeout=startup_timeout)
    server = VllmServer(cfg, adapter_manifest=manifest)
    cmd = server.build_cmd()
    info = {'lora_flags': [t for t in cmd if t in ('--enable-lora', '--max-loras', '--max-lora-rank', '--lora-modules')],
            'startup_timeout': startup_timeout}
    tee = LogTee(server, RUN_DIR / f'{label}.log')
    t = time.monotonic()
    try:
        tee.start(); server.start(); info['started'] = True
    except Exception as exc:  # noqa: BLE001
        info['started'] = False; info['error'] = f'{type(exc).__name__}: {str(exc)[:1500]}'
    info['boot_s'] = round(time.monotonic() - t, 1)
    if info['started']:
        tee._copy_once()
        log_path = RUN_DIR / f'{label}.log'
        log_text = log_path.read_text() if log_path.exists() else ''
    else:
        log_text = tee.stop_and_final_copy()
    info.update(parse_log(log_text or ''))
    if not info['started']:
        info['failure_class'] = classify_failure((log_text or '') + info.get('error', ''))
        info['teardown_s'] = teardown(server)
        return None, tee, info
    info['served_base'] = getattr(server, 'effective_model_path', MODEL_DIR)
    models = http('GET', server.base_url + '/models', timeout=30)
    info['v1_models'] = [m.get('id') for m in (models.get('json') or {}).get('data', [])] if models['status'] == 200 else models
    return server, tee, info


# %%
# ---------------------------------------------------------------- the harness's own request rendering (ADK -> LiteLLM -> HTTP body)
# The agent is compiled from the shipped tree by the official compile path; each synthetic history is sent through
# the agent's own LiteLlm (with the adk_submission reasoning patch) to a local capture endpoint, and the captured
# HTTP body is what is then sent to vLLM, with only the model name, temperature and return_token_ids changed.
import http.server
import socketserver

CAP_PORT = 8011
CAPTURED: list = []


class _CapHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        n = int(self.headers.get('Content-Length', 0) or 0)
        raw = self.rfile.read(n)
        try:
            CAPTURED.append(json.loads(raw))
        except Exception:  # noqa: BLE001
            CAPTURED.append({'_unparsed': True})
        body = json.dumps({'id': 'cap', 'object': 'chat.completion', 'created': 0, 'model': 'cap',
                           'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': 'ok'},
                                        'finish_reason': 'stop'}],
                           'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2}}).encode()
        self.send_response(200); self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)

    def log_message(self, *a):  # noqa: D401
        pass


def start_capture_server():
    srv = socketserver.ThreadingTCPServer(('127.0.0.1', CAP_PORT), _CapHandler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def run_async(coro):
    with cf.ThreadPoolExecutor(1) as ex:
        return ex.submit(asyncio.run, coro).result()


def call_id(it: dict) -> str:
    return 'chatcmpl-tool-' + hashlib.sha256(it['pid'].encode()).hexdigest()[:16]


def hand_messages(it: dict, with_read: bool, system_text: str) -> list:
    msgs = [{'role': 'system', 'content': system_text}, {'role': 'user', 'content': it['user']}]
    if with_read:
        args = {'filepath': it['rel'], 'start_line': it['win'][0], 'end_line': it['win'][1]}
        msgs.append({'role': 'assistant', 'content': None, 'reasoning_content': PRIOR_THOUGHT, 'reasoning': PRIOR_THOUGHT,
                     'tool_calls': [{'id': call_id(it), 'type': 'function',
                                     'function': {'name': 'read_file', 'arguments': json.dumps(args)}}]})
        msgs.append({'role': 'tool', 'tool_call_id': call_id(it), 'content': json.dumps(it['read_resp'], ensure_ascii=False)})
    return msgs


def compile_agent(sub: Path, server, manifest):
    import litellm
    from swegemma.harness.agent_runner import resolve_swegemma_adapter
    litellm.drop_params = True
    declared = discover_declared_models(str(sub))
    registry = server.create_model_registry(aliases=sorted({*declared, MODEL}), model_prefix='openai/')
    try:
        from swegemma.tools import create_tools
        tools = create_tools(STUB)
        tools_path = 'swegemma.create_tools'
    except Exception as exc:  # noqa: BLE001
        from swegemma.tools.workspace import make_edit_file, make_write_file
        tools = {'read_file': make_read_file(STUB), 'edit_file': make_edit_file(STUB), 'write_file': make_write_file(STUB)}
        tools_path = f'partial ({type(exc).__name__})'
    agent = compile_submission(submission_dir=str(sub), tool_registry=tools, model_registry=registry,
                               adapter_manifest=manifest,
                               adapter_resolver_fn=lambda b, i: resolve_swegemma_adapter(b, i, registry))
    return agent, registry, tools_path


async def _capture_all(agent, jobs):
    from google.adk.models.llm_request import LlmRequest
    from google.genai import types as gt
    model = copy.copy(agent.model)
    model._additional_args = dict(agent.model._additional_args or {}, api_base=f'http://127.0.0.1:{CAP_PORT}/v1')
    tools = await agent.canonical_tools()
    instr = agent.instruction if isinstance(agent.instruction, str) else str(agent.instruction)
    identity = f'You are an agent. Your internal name is "{agent.name}".'
    if getattr(agent, 'description', None):
        identity += f' The description about you is "{agent.description}".'
    out = []
    for it, with_read in jobs:
        contents = [gt.Content(role='user', parts=[gt.Part(text=it['user'])])]
        if with_read:
            cid = call_id(it)
            contents.append(gt.Content(role='model', parts=[
                gt.Part(text=PRIOR_THOUGHT, thought=True),
                gt.Part(function_call=gt.FunctionCall(id=cid, name='read_file', args={
                    'filepath': it['rel'], 'start_line': it['win'][0], 'end_line': it['win'][1]}))]))
            contents.append(gt.Content(role='user', parts=[
                gt.Part(function_response=gt.FunctionResponse(id=cid, name='read_file', response=it['read_resp']))]))
        cfg = agent.generate_content_config.model_copy(deep=True) if agent.generate_content_config else gt.GenerateContentConfig()
        req = LlmRequest(model=model.model, contents=contents, config=cfg)
        req.append_instructions([instr])
        req.append_instructions([identity])
        req.append_tools(tools)
        n0 = len(CAPTURED)
        async for _ in model.generate_content_async(req, stream=False):
            pass
        out.append(CAPTURED[n0] if len(CAPTURED) > n0 else None)
    return out, instr + '\n\n' + identity


def capture_bodies(agent, jobs):
    """Returns (bodies, path). Falls back to hand-built messages if the ADK path fails."""
    try:
        bodies, sys_text = run_async(_capture_all(agent, jobs))
        if all(b and 'messages' in b for b in bodies):
            return bodies, 'adk_capture', sys_text
        raise RuntimeError('capture incomplete')
    except Exception as exc:  # noqa: BLE001
        RUN.setdefault('capture_errors', []).append(f'{type(exc).__name__}: {str(exc)[:800]}')
    sys_text = (SUB0 / 'prompts' / 'system.md').read_text() + '\n\nYou are an agent. Your internal name is "swe_agent".'
    tmpl = {'temperature': 1.0, 'top_p': 0.95, 'top_k': 64, 'max_tokens': 8192,
            'chat_template_kwargs': {'enable_thinking': True}, 'thinking_token_budget': 4096}
    return [dict(tmpl, messages=hand_messages(it, wr, sys_text)) for it, wr in jobs], 'hand', sys_text


# %%
# ---------------------------------------------------------------- requests, call extraction, and the edit judge
TOK = None
TC_START = TC_END = None
EOS_IDS: set = set()


def make_body(base_body: dict, model_name: str, greedy: bool) -> dict:
    b = copy.deepcopy(base_body)
    b.pop('stream', None); b.pop('stream_options', None)
    b['model'] = model_name
    b['return_token_ids'] = True
    if greedy:
        b['temperature'] = 0.0
    return b


def first_call_span(toks: list):
    try:
        i = toks.index(TC_START)
    except ValueError:
        return None
    try:
        j = toks.index(TC_END, i + 1)
    except ValueError:
        return (i, None)
    return (i, j)


def chat_job(tag: dict, body: dict, base_url: str) -> dict:
    r = http('POST', base_url + '/chat/completions', body)
    row = dict(tag, status=r['status'], s=r['s'])
    if r['status'] != 200:
        row['error'] = (r.get('error') or '')[:300]
        return row
    js = r['json']
    ch = js['choices'][0]
    msg = ch.get('message') or {}
    toks = ch.get('token_ids') or []
    row.update(resp_model=js.get('model'), finish_reason=ch.get('finish_reason'),
               completion_tokens=(js.get('usage') or {}).get('completion_tokens'),
               prompt_tokens=(js.get('usage') or {}).get('prompt_tokens'))
    calls = msg.get('tool_calls') or []
    row['n_calls'] = len(calls)
    if calls:
        fn = calls[0].get('function') or {}
        row['tool'] = fn.get('name')
        try:
            row['args'] = json.loads(fn.get('arguments') or '{}')
        except Exception:  # noqa: BLE001
            row['args'] = None; row['args_unparsed'] = True
    else:
        row['tool'] = None
    span = first_call_span(toks) if toks else None
    row['has_call_token'] = span is not None
    row['call_tokens'] = (span[1] - span[0] - 1) if span and span[1] is not None else None
    row['_toks'] = toks
    row['_prompt_ids'] = js.get('prompt_token_ids')
    return row


def norm_path(fp) -> str:
    if not isinstance(fp, str):
        return ''
    s = fp.strip()
    for pre in ('/workspace/', './'):
        if s.startswith(pre):
            s = s[len(pre):]
    return s.lstrip('/')


def judge(it: dict, row: dict) -> dict:
    """Class of the first call against the full raw file: E exact unique, b fuzzy, g multiple, c no match,
    f missing arguments, w wrong file, x no call or another tool."""
    out = {'cls': 'x', 'exact': False, 'correct_strict': False, 'correct_ast': False}
    if row.get('status') != 200 or row.get('tool') != 'edit_file':
        out['other_tool'] = row.get('tool')
        return out
    a = row.get('args') or {}
    if not all(isinstance(a.get(k), str) for k in ('filepath', 'old_string', 'new_string')) or not a.get('old_string'):
        out['cls'] = 'f'; return out
    if norm_path(a['filepath']) != it['rel']:
        out['cls'] = 'w'; return out
    content = FILES[it['rel']]
    gold = content.replace(it['old'], it['new'], 1)
    try:
        if apply_replacement is not None:
            res = apply_replacement(content, a['old_string'], a['new_string'], filepath=it['rel'], allow_multiple=False)
            new_content, strategy = res.new_content, res.strategy
        else:
            if not unique_in(content, a['old_string']):
                raise ValueError('occurs 2 times' if content.count(a['old_string']) > 1 else 'not found')
            new_content, strategy = content.replace(a['old_string'], a['new_string'], 1), 'exact'
    except ValueError as exc:
        out['cls'] = 'g' if re.search(r'occurs \d+ times|matches \d+ locations', str(exc)) else 'c'
        return out
    out['strategy'] = strategy
    out['cls'] = 'E' if strategy == 'exact' and unique_in(content, a['old_string']) else 'b'
    out['exact'] = out['cls'] == 'E'
    out['correct_strict'] = new_content == gold
    try:
        out['correct_ast'] = ast.dump(ast.parse(new_content)) == ast.dump(ast.parse(gold))
    except SyntaxError:
        out['correct_ast'] = False
    return out


EVAL_ROWS = RUN_DIR / 'eval.jsonl'
CALLS = RUN_DIR / 'calls.jsonl'   # the edit-call arguments (public file text), kept in the run dir only
PHASE_OPEN: dict = {}
GEN: dict = {}                    # training generations kept in memory: pid -> row with token ids


def run_phase(name: str, jobs: list, deadline_s: float) -> dict:
    """jobs: (tag, body, base_url, item or None). Results that arrive after the deadline are dropped."""
    PHASE_OPEN[name] = True
    n_done = Counter()
    t = time.monotonic()
    ex = cf.ThreadPoolExecutor(CONCURRENCY)
    futs = {ex.submit(chat_job, tag, body, url): (tag, it) for tag, body, url, it in jobs}
    try:
        for fut in cf.as_completed(futs, timeout=max(1.0, deadline_s - elapsed())):
            tag, it = futs[fut]
            try:
                row = fut.result()
            except Exception as exc:  # noqa: BLE001
                row = dict(tag, status=None, error=f'{type(exc).__name__}: {exc}'[:300])
            if not PHASE_OPEN.get(name):
                break
            if tag['role'] == 'gen':
                GEN[(tag['pid'], tag['kind'])] = row
            if it is not None and tag['kind'] in ('edit', 't1'):
                row.update(judge(it, row))
                with open(CALLS, 'a') as f:
                    f.write(json.dumps({k: row.get(k) for k in ('boot', 'arm', 'kind', 'pid', 'tool', 'args')}) + '\n')
            keep = {k: v for k, v in row.items() if not k.startswith('_') and k != 'args'}
            if it is not None:
                keep['edit_kind'] = it['kind']
            with open(EVAL_ROWS, 'a') as f:
                f.write(json.dumps(keep) + '\n')
            n_done[tag['arm'] + ':' + tag['kind']] += 1
    except cf.TimeoutError:
        pass
    PHASE_OPEN[name] = False
    ex.shutdown(wait=False, cancel_futures=True)
    return {'n_jobs': len(jobs), 'done': dict(n_done), 'phase_s': round(time.monotonic() - t, 1)}


# %%
# ---------------------------------------------------------------- boot 0: the shipped tree, no adapters
from transformers import AutoTokenizer

TOK = AutoTokenizer.from_pretrained(MODEL_DIR)
TC_START = TOK.convert_tokens_to_ids('<|tool_call>')
TC_END = TOK.convert_tokens_to_ids('<tool_call|>')
try:
    gcfg = json.loads(Path(MODEL_DIR, 'generation_config.json').read_text())
    e = gcfg.get('eos_token_id')
    EOS_IDS = set(e if isinstance(e, list) else [e]) - {None}
except Exception:  # noqa: BLE001
    EOS_IDS = set()
if TOK.eos_token_id is not None:
    EOS_IDS.add(TOK.eos_token_id)
RUN['tokens'] = {'tool_call_start': TC_START, 'tool_call_end': TC_END, 'eos_ids': sorted(EOS_IDS)}

if elapsed() > 700:   # install and data generation are not bounded by a timeout; this bounds them
    stop('infrastructure', f'boot 0 would start at {elapsed():.0f} s, after 700 s')
manifest0 = discover_adapters(str(SUB0), adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
server, tee, info0 = boot('boot0', SUB0, manifest0, BOOT0_STARTUP_TIMEOUT_S)
RUN['boot0'] = info0; save_run()
print('boot0:', json.dumps(info0, indent=1, default=str)[:2000])
if server is None:
    stop('infrastructure', 'boot 0 failed')
base0 = info0['served_base']

cap_srv = start_capture_server()
try:
    agent0, registry0, tools_path = compile_agent(SUB0, server, manifest0)
    PATHS['tools'] = tools_path
    PATHS['agent_model'] = getattr(agent0.model, 'model', None)
except Exception as exc:  # noqa: BLE001
    agent0 = None
    RUN.setdefault('capture_errors', []).append(f'compile: {type(exc).__name__}: {str(exc)[:800]}')
JOBS_E = [(it, True) for it in EVAL]
JOBS_D = [(it, False) for it in DRIFT]
JOBS_T = [(it, True) for it in TRAIN]
JOBS_F = [(it, False) for it in TRAIN_FIRST]
all_jobs = JOBS_E + JOBS_D + JOBS_T + JOBS_F
bodies, PATHS['request'], SYS_TEXT = capture_bodies(agent0, all_jobs) if agent0 is not None else capture_bodies(None, all_jobs)
cap_srv.shutdown()
for (it, wr), b in zip(all_jobs, bodies):
    it['body_read' if wr else 'body_first'] = b
b0 = EVAL[0]['body_read']
RUN['request_shape'] = {'keys': sorted(b0.keys()), 'n_messages': len(b0.get('messages', [])),
                        'roles': [m.get('role') for m in b0.get('messages', [])],
                        'assistant_keys': sorted(next((m for m in b0['messages'] if m.get('role') == 'assistant'), {}).keys()),
                        'n_tools': len(b0.get('tools') or []),
                        'tool_names': [((t.get('function') or {}).get('name')) for t in (b0.get('tools') or [])],
                        'non_message_params': {k: v for k, v in b0.items() if k not in ('messages', 'tools')}}
stage('captured', path=PATHS['request'], shape=RUN['request_shape'])

# render check: the server's /tokenize of the same body against the prompt ids a chat request returns
rc = {}
try:
    tb = {k: b0[k] for k in ('messages', 'tools') if k in b0}
    tb.update(model=base0, add_generation_prompt=True,
              chat_template_kwargs=b0.get('chat_template_kwargs') or {'enable_thinking': True})
    r = http('POST', server.base_url.rsplit('/v1', 1)[0] + '/tokenize', tb, timeout=60)
    rc['tokenize_status'] = r['status']
    tok_ids = (r.get('json') or {}).get('tokens') if r['status'] == 200 else None
    row = chat_job({'boot': 'boot0', 'arm': 'base0', 'kind': 'render', 'pid': EVAL[0]['pid'], 'role': 'check'},
                   dict(make_body(b0, base0, True), max_tokens=16), server.base_url)
    rc['chat_status'] = row.get('status')
    rc['n_prompt_ids'] = len(row.get('_prompt_ids') or [])
    rc['tokenize_equals_prompt_ids'] = (tok_ids == row.get('_prompt_ids')) if tok_ids and row.get('_prompt_ids') else None
    rc['n_tokenize'] = len(tok_ids or [])
except Exception as exc:  # noqa: BLE001
    rc['error'] = f'{type(exc).__name__}: {exc}'[:500]
RUN['render_check'] = rc
stage('render_check', **rc)

# logprob texts on boot 0, twice
for label in ('base0', 'base0_repeat'):
    for i, text in enumerate(LOGPROB_PROMPTS):
        record_probe({'boot': 'boot0', 'label': label, 'kind': 'logprob', 'i': i,
                      **prompt_logprobs(server.base_url, base0, text)})

# the request phase: base0 greedy on held-out edits and first turns, and the training generations at the shipped sampling
jobs = []
url = server.base_url
ev = [({'boot': 'boot0', 'arm': 'base0', 'kind': 'edit', 'pid': it['pid'], 'role': 'eval'},
       make_body(it['body_read'], base0, True), url, it) for it in EVAL]
dr = [({'boot': 'boot0', 'arm': 'base0', 'kind': 'drift', 'pid': it['pid'], 'role': 'eval'},
       make_body(it['body_first'], base0, True), url, None) for it in DRIFT]
tr = [({'boot': 'boot0', 'arm': 'base0', 'kind': 'train_edit', 'pid': it['pid'], 'role': 'gen'},
       make_body(it['body_read'], base0, False), url, None) for it in TRAIN]
tf = [({'boot': 'boot0', 'arm': 'base0', 'kind': 'train_first', 'pid': it['pid'], 'role': 'gen'},
       make_body(it['body_first'], base0, False), url, None) for it in TRAIN_FIRST]
gen_jobs = tr + tf
for k in range(max(len(ev) + len(dr), len(gen_jobs))):   # interleave: one eval job, then two generation jobs
    if k < len(ev) + len(dr):
        jobs.append((ev + dr)[k])
    jobs.extend(gen_jobs[2 * k:2 * k + 2])
p0 = run_phase('boot0', jobs, min(elapsed() + BOOT0_PHASE_S, HARD_CAP_S - 1900))
RUN['phase0'] = p0
tee.stop_and_final_copy()
info0.update(parse_log((RUN_DIR / 'boot0.log').read_text()))
info0['teardown_s'] = teardown(server)
RUN['boot0'] = info0
stage('boot0_done', **p0)

# %%
# ---------------------------------------------------------------- stage 2a: training sequences (loss on the call tokens only)
from vllm.tool_parsers.gemma4_tool_parser import _parse_gemma4_args

DELIM = '<|"|>'
DELIM_ID = TOK.convert_tokens_to_ids(DELIM)
RUN['tokens']['string_delim'] = DELIM_ID


def fmt_value(v) -> str:
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, (int, float)):
        return str(v)
    return DELIM + str(v) + DELIM


def raw_call(toks: list, span) -> str:
    return TOK.decode(toks[span[0] + 1:span[1]], skip_special_tokens=False)


def split_call(text: str):
    m = re.match(r'^call:([A-Za-z_][\w]*)\{(.*)\}$', text, re.S)
    return (m.group(1), m.group(2)) if m else (None, None)


def key_order(args_str: str) -> list:
    keys, i, n = [], 0, len(args_str)
    while i < n:
        m = re.match(r'[\s,]*([A-Za-z_]\w*):', args_str[i:])
        if not m:
            break
        keys.append(m.group(1)); i += m.end()
        if args_str[i:].startswith(DELIM):
            j = args_str.find(DELIM, i + len(DELIM))
            i = n if j < 0 else j + len(DELIM)
        else:
            m2 = re.match(r'[^,]*', args_str[i:]); i += m2.end()
    return keys


SEQS, stats = [], Counter()
key_orders = Counter()
for it in TRAIN + TRAIN_FIRST:
    kind = 'train_edit' if it['pid'].startswith('t') else 'train_first'
    row = GEN.get((it['pid'], kind))
    if not row or row.get('status') != 200 or not row.get('_prompt_ids') or not row.get('_toks'):
        stats['no_generation'] += 1; continue
    toks = row['_toks']
    span = first_call_span(toks)
    if span is None or span[1] is None:
        stats['no_call'] += 1; continue
    name, args_str = split_call(raw_call(toks, span))
    if name is None:
        stats['call_unsplittable'] += 1; continue
    tail = [toks[span[1] + 1]] if span[1] + 1 < len(toks) and toks[span[1] + 1] in EOS_IDS else []
    prefix = list(row['_prompt_ids']) + toks[:span[0] + 1]
    if kind == 'train_edit' and name == 'edit_file':
        try:
            parsed = _parse_gemma4_args(args_str)
        except Exception:  # noqa: BLE001
            parsed = {}
        order_ = key_order(args_str)
        key_orders[','.join(order_)] += 1
        fp = parsed.get('filepath') if norm_path(parsed.get('filepath')) == it['rel'] else it['rel']
        want = {'filepath': fp, 'old_string': it['old'], 'new_string': it['new']}
        keys = [k for k in order_ if k in want or k in parsed] + [k for k in ('filepath', 'old_string', 'new_string') if k not in order_]
        text = 'call:edit_file{' + ','.join(f'{k}:{fmt_value(want[k] if k in want else parsed[k])}' for k in keys) + '}'
        ids = TOK.encode(text, add_special_tokens=False)
        ok_text = TOK.decode(ids, skip_special_tokens=False) == text and ids.count(DELIM_ID) == 6
        try:
            back = _parse_gemma4_args(split_call(text)[1])
        except Exception:  # noqa: BLE001
            back = {}
        ok_parse = all(back.get(k) == v for k, v in want.items())
        if not (ok_text and ok_parse):
            stats['target_roundtrip_fail'] += 1; continue
        SEQS.append({'kind': 'pair', 'pid': it['pid'], 'ids': prefix + ids + [TC_END] + tail, 'start': len(prefix),
                     'base_exact': None})
        stats['pair'] += 1
    else:
        SEQS.append({'kind': 'anchor_read' if kind == 'train_edit' else 'anchor_first', 'pid': it['pid'],
                     'ids': prefix + toks[span[0] + 1:span[1] + 1] + tail, 'start': len(prefix), 'tool': name})
        stats['anchor_read' if kind == 'train_edit' else 'anchor_first'] += 1
n_pairs = stats['pair']
anchors = [s for s in SEQS if s['kind'] != 'pair']
rng.shuffle(anchors)
firsts = [s for s in anchors if s['kind'] == 'anchor_first'][:max(1, n_pairs // 2)]
reads = [s for s in anchors if s['kind'] == 'anchor_read'][:max(0, n_pairs - len(firsts))]
TRAIN_SEQS = [s for s in SEQS if s['kind'] == 'pair'] + firsts + reads
rng.shuffle(TRAIN_SEQS)
lens = sorted(len(s['ids']) for s in TRAIN_SEQS)
RUN['train_data'] = {'stats': dict(stats), 'n_pairs': n_pairs, 'n_anchor_first': len(firsts), 'n_anchor_read': len(reads),
                     'n_seqs': len(TRAIN_SEQS), 'key_orders': dict(key_orders.most_common(6)),
                     'len_median': lens[len(lens) // 2] if lens else None, 'len_max': lens[-1] if lens else None,
                     'target_tokens_mean': round(sum(len(s['ids']) - s['start'] for s in TRAIN_SEQS) / max(1, len(TRAIN_SEQS)), 1)}
stage('train_data', **RUN['train_data'])
if n_pairs < 32:
    stop('infrastructure', f'only {n_pairs} pairs')
with open(WORK / 'train_seqs.jsonl', 'w') as f:   # training data stays in /tmp: not in the kernel output
    for s in TRAIN_SEQS:
        f.write(json.dumps({'kind': s['kind'], 'ids': s['ids'], 'start': s['start']}) + '\n')

# %%
# ---------------------------------------------------------------- stage 2b: the PEFT key names, from the served checkpoint's index
from safetensors import safe_open

idx_path = Path(MODEL_DIR, 'model.safetensors.index.json')
if idx_path.exists():
    weight_map = json.loads(idx_path.read_text())['weight_map']
else:
    weight_map = {}
    for fpath in sorted(Path(MODEL_DIR).glob('*.safetensors')):
        with safe_open(str(fpath), 'pt') as sf:
            for k in sf.keys():
                weight_map[k] = fpath.name
MOD_RE = re.compile(r'^(.*\.layers\.(\d+)\.self_attn\.(q_proj|o_proj))\.(weight|weight_packed|weight_shape)$')
KEYS = {}
for name in weight_map:
    m = MOD_RE.match(name)
    if m and 'vision' not in name and 'audio' not in name:
        KEYS[f'{m.group(2)}.{m.group(3)}'] = m.group(1)
RUN['peft_keys'] = {'n': len(KEYS), 'example': KEYS.get('0.q_proj')}

# %%
# ---------------------------------------------------------------- stage 2c: the training script (run as a child process under torchrun)
TRAIN_PY = r'''
import json, math, os, random, sys, time
import torch
import torch.nn.functional as F
import torch.distributed as dist

cfg = json.load(open(sys.argv[1]))
rank = int(os.environ.get('RANK', 0)); world = int(os.environ.get('WORLD_SIZE', 1)); local = int(os.environ.get('LOCAL_RANK', 0))
torch.cuda.set_device(local)
dev = torch.device('cuda', local)
if world > 1:
    dist.init_process_group('nccl')
T0 = time.time()
LOG = {'rank_world': world, 'weights': None, 'events': []}


def say(msg):
    if rank == 0:
        print(f'[train {time.time() - T0:7.1f}s] {msg}', flush=True)
        LOG['events'].append([round(time.time() - T0, 1), msg])


def allmin(x):
    t = torch.tensor([float(x)], device=dev)
    if world > 1:
        dist.all_reduce(t, op=dist.ReduceOp.MIN)
    return t.item()


def allmax(x):
    t = torch.tensor([float(x)], device=dev)
    if world > 1:
        dist.all_reduce(t, op=dist.ReduceOp.MAX)
    return t.item()


import transformers
cls = getattr(transformers, 'Gemma4ForConditionalGeneration', None) or transformers.AutoModelForImageTextToText


def load(src, kind):
    kw = dict(device_map={'': local}, attn_implementation='sdpa')
    if kind == 'w4a16':
        from transformers import CompressedTensorsConfig
        kw['quantization_config'] = CompressedTensorsConfig(run_compressed=False)
    try:
        return cls.from_pretrained(src, dtype=torch.bfloat16, **kw)
    except TypeError:
        return cls.from_pretrained(src, torch_dtype=torch.bfloat16, **kw)


model = None
for src, kind in cfg['sources']:
    try:
        for r in range(world):
            if r == rank:
                model = load(src, kind)
            if world > 1 and cfg['stagger']:
                dist.barrier()
        LOG['weights'] = kind; LOG['weights_dir'] = src
        break
    except Exception as exc:
        say(f'load {kind} failed: {type(exc).__name__}: {str(exc)[:300]}')
        model = None
        torch.cuda.empty_cache()
if model is None:
    say('no weights loaded'); json.dump(LOG, open(cfg['log'], 'w')); sys.exit(3)
say(f'loaded {LOG["weights"]}; cuda alloc {torch.cuda.memory_allocated(dev) / 2**30:.2f} GiB')

inner = model.model
lm = inner.language_model
ple = getattr(lm, 'embed_tokens_per_layer', None)
if ple is not None:
    ple.to('cpu')
    _orig = ple.forward

    def _ple_forward(ids, _o=_orig):
        return _o(ids.to('cpu')).to(dev, non_blocking=True)
    ple.forward = _ple_forward
for nm in ('vision_tower', 'audio_tower', 'embed_vision', 'embed_audio', 'multi_modal_projector'):
    mod = getattr(inner, nm, None)
    if isinstance(mod, torch.nn.Module):
        mod.to('cpu')
torch.cuda.empty_cache()
for p in model.parameters():
    p.requires_grad_(False)
LOG['cuda_alloc_after_offload_gib'] = round(torch.cuda.memory_allocated(dev) / 2**30, 2)
say(f'after offload cuda alloc {LOG["cuda_alloc_after_offload_gib"]} GiB')


class LoRA(torch.nn.Module):
    def __init__(self, base, r, alpha, gen):
        super().__init__()
        self.base = base
        out_f, in_f = base.weight.shape
        a = torch.empty(r, in_f, dtype=torch.float32)
        torch.nn.init.kaiming_uniform_(a, a=math.sqrt(5), generator=gen)
        self.lora_A = torch.nn.Parameter(a.to(dev))
        self.lora_B = torch.nn.Parameter(torch.zeros(out_f, r, dtype=torch.float32, device=dev))
        self.scale = alpha / r

    def forward(self, x):
        y = self.base(x)
        z = (x @ self.lora_A.to(x.dtype).t()) @ self.lora_B.to(x.dtype).t()
        return y + z * self.scale


gen = torch.Generator().manual_seed(cfg['seed'])
loras = {}
for i, layer in enumerate(lm.layers):
    for proj in ('q_proj', 'o_proj'):
        base = getattr(layer.self_attn, proj, None)
        if base is None or f'{i}.{proj}' not in cfg['keys']:
            continue
        mod = LoRA(base, cfg['r'], cfg['alpha'], gen)
        setattr(layer.self_attn, proj, mod)
        loras[f'{i}.{proj}'] = mod
params = [p for m in loras.values() for p in (m.lora_A, m.lora_B)]
LOG['n_lora_modules'] = len(loras); LOG['n_lora_params'] = sum(p.numel() for p in params)
say(f'lora modules {len(loras)}, params {LOG["n_lora_params"]}')
model.config.use_cache = False
try:
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    LOG['grad_ckpt'] = True
except Exception as exc:
    LOG['grad_ckpt'] = f'{type(exc).__name__}: {exc}'[:200]
model.train()

seqs = [json.loads(l) for l in open(cfg['data'])]


def step_loss(s, L=None):
    ids = s['ids'] if L is None else s['ids'][-L:]
    start = s['start'] - (len(s['ids']) - len(ids))
    x = torch.tensor(ids, device=dev)[None]
    keep = torch.arange(start - 1, len(ids) - 1, device=dev)
    out = model(input_ids=x, logits_to_keep=keep, use_cache=False)
    return F.cross_entropy(out.logits[0].float(), x[0, start:])


# memory ladder: the longest sequence, cut from the left to each length in turn
longest = max(seqs, key=lambda s: len(s['ids']))
L_ok = 0
probe = {}
for L in sorted({min(x, len(longest['ids'])) for x in cfg['ladder']}, reverse=True):
    L_try = L
    torch.cuda.reset_peak_memory_stats(dev)
    ok = 1.0
    try:
        loss = step_loss(longest, L_try)
        loss.backward()
    except torch.OutOfMemoryError:
        ok = 0.0
    except RuntimeError as exc:
        ok = 0.0 if 'out of memory' in str(exc).lower() else -1.0
        if ok < 0:
            probe[str(L)] = f'error: {str(exc)[:200]}'
    for p in params:
        p.grad = None
    torch.cuda.empty_cache()
    probe[str(L)] = probe.get(str(L)) or {'ok': ok, 'len': L_try,
                                          'peak_gib': round(torch.cuda.max_memory_allocated(dev) / 2**30, 2)}
    if allmin(ok) > 0:
        L_ok = L_try
        break
LOG['probe'] = probe; LOG['L_ok'] = L_ok
say(f'probe {probe} -> L {L_ok}')
if L_ok <= 0:
    json.dump(LOG, open(cfg['log'], 'w')) if rank == 0 else None
    sys.exit(4)

data = [s for s in seqs if len(s['ids']) <= L_ok]
LOG['n_seqs_fit'] = len(data); LOG['n_seqs_dropped_long'] = len(seqs) - len(data)
LOG['n_pairs_fit'] = sum(1 for s in data if s['kind'] == 'pair')
per_rank = len(data) // world
steps_per_epoch = per_rank // cfg['accum']
total_steps = max(1, steps_per_epoch * cfg['epochs'])
opt = torch.optim.AdamW(params, lr=cfg['lr'], betas=(0.9, 0.999), weight_decay=0.0)


def lr_at(s):
    # cosine to 10% over whichever runs out first: the planned steps or the time to the deadline
    warm = min(1.0, (s + 1) / cfg['warmup'])
    frac = max(s / total_steps, (time.time() - t_train) / max(1.0, deadline - t_train))
    return cfg['lr'] * warm * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(1.0, frac))))


t_train = time.time()
deadline = min(cfg['deadline_epoch'], t_train + cfg['cap_s'])
step, seen, hist = 0, 0, []
stopped = 'completed'
for ep in range(cfg['epochs']):
    order = list(range(len(data)))
    random.Random(cfg['seed'] + ep).shuffle(order)
    mine = [data[j] for j in order[rank::world][:per_rank]]
    for st in range(steps_per_epoch):
        if allmax(1.0 if time.time() > deadline else 0.0) > 0:
            stopped = 'deadline'; break
        sums = {'pair': [0.0, 0], 'anchor': [0.0, 0]}
        for g in range(cfg['accum']):
            s = mine[st * cfg['accum'] + g]
            loss = step_loss(s)
            (loss / cfg['accum']).backward()
            k = 'pair' if s['kind'] == 'pair' else 'anchor'
            sums[k][0] += loss.item(); sums[k][1] += 1
        flat = torch.cat([(p.grad if p.grad is not None else torch.zeros_like(p)).reshape(-1) for p in params])
        if world > 1:
            dist.all_reduce(flat); flat /= world
        off = 0
        for p in params:
            n = p.numel(); p.grad = flat[off:off + n].view_as(p).clone(); off += n
        gn = torch.nn.utils.clip_grad_norm_(params, 1.0).item()
        for gr in opt.param_groups:
            gr['lr'] = lr_at(step)
        opt.step(); opt.zero_grad(set_to_none=True)
        st_t = torch.tensor([sums['pair'][0], sums['pair'][1], sums['anchor'][0], sums['anchor'][1]], device=dev)
        if world > 1:
            dist.all_reduce(st_t)
        v = st_t.tolist()
        hist.append({'step': step, 'pair_loss': (v[0] / v[1]) if v[1] else None,
                     'anchor_loss': (v[2] / v[3]) if v[3] else None, 'grad_norm': round(gn, 4),
                     'lr': lr_at(step), 't': round(time.time() - t_train, 1)})
        step += 1; seen += cfg['accum'] * world
        if rank == 0 and step % 5 == 0:
            say(f'step {step}/{total_steps} pair {hist[-1]["pair_loss"]} anchor {hist[-1]["anchor_loss"]}')
    if stopped == 'deadline':
        break
LOG.update(steps=step, total_steps_planned=total_steps, seqs_seen=seen, stopped=stopped, history=hist,
           train_s=round(time.time() - t_train, 1), peak_train_gib=round(torch.cuda.max_memory_allocated(dev) / 2**30, 2))
if rank == 0:
    from safetensors.torch import save_file
    out = cfg['out_dir']
    os.makedirs(out, exist_ok=True)
    tensors, bnorm = {}, {}
    for k, mod in loras.items():
        key = 'base_model.model.' + cfg['keys'][k]
        tensors[key + '.lora_A.weight'] = mod.lora_A.detach().to(torch.bfloat16).cpu().contiguous()
        tensors[key + '.lora_B.weight'] = mod.lora_B.detach().to(torch.bfloat16).cpu().contiguous()
        bnorm[k] = round(mod.lora_B.detach().float().norm().item(), 6)
    save_file(tensors, os.path.join(out, 'adapter_model.safetensors'), metadata={'format': 'pt'})
    acfg = {'alpha_pattern': {}, 'auto_mapping': None, 'base_model_name_or_path': 'google/gemma-4-e4b-it', 'bias': 'none',
            'fan_in_fan_out': False, 'inference_mode': True, 'init_lora_weights': True, 'layer_replication': None,
            'layers_pattern': None, 'layers_to_transform': None, 'loftq_config': {}, 'lora_alpha': cfg['alpha'],
            'lora_dropout': 0.0, 'megatron_config': None, 'megatron_core': 'megatron.core', 'modules_to_save': None,
            'peft_type': 'LORA', 'r': cfg['r'], 'rank_pattern': {}, 'revision': None,
            'target_modules': ['q_proj', 'o_proj'], 'task_type': 'CAUSAL_LM', 'use_dora': False, 'use_rslora': False}
    json.dump(acfg, open(os.path.join(out, 'adapter_config.json'), 'w'), indent=2)
    LOG['b_norm'] = bnorm; LOG['b_norm_total'] = round(sum(x * x for x in bnorm.values()) ** 0.5, 6)
    LOG['n_tensors'] = len(tensors)
    json.dump(LOG, open(cfg['log'], 'w'), indent=1)
    say(f'saved {len(tensors)} tensors; B norm {LOG["b_norm_total"]}')
if world > 1:
    dist.barrier(); dist.destroy_process_group()
'''

TRAIN_SCRIPT = WORK / 'train_lora.py'
TRAIN_SCRIPT.write_text(TRAIN_PY)
ADAPTER_DIR = SUB1 / 'adapters' / 'copy_lora'
TRAIN_LOG = RUN_DIR / 'train.json'
sources = ([[BF16_DIR, 'bf16']] if BF16_DIR else []) + [[MODEL_DIR, 'w4a16']]
mem_gib = env.get('mem_available_gib') or 0


def train_cfg(world: int) -> dict:
    return {'sources': sources, 'stagger': bool(world > 1 and mem_gib < 100), 'keys': KEYS, 'r': LORA_R,
            'alpha': LORA_ALPHA, 'lr': LR, 'warmup': WARMUP_STEPS, 'accum': GRAD_ACCUM, 'epochs': MAX_EPOCHS,
            'seed': SEED, 'ladder': SEQ_LADDER, 'data': str(WORK / 'train_seqs.jsonl'), 'out_dir': str(ADAPTER_DIR),
            'log': str(TRAIN_LOG), 'cap_s': TRAIN_CAP_S,
            'deadline_epoch': time.time() + (TRAIN_END_S - elapsed())}


def run_train(world: int) -> dict:
    cfgp = WORK / f'train_cfg_{world}.json'
    cfgp.write_text(json.dumps(train_cfg(world)))
    t = time.monotonic()
    cmd = [sys.executable, '-m', 'torch.distributed.run', '--standalone', f'--nproc_per_node={world}', str(TRAIN_SCRIPT), str(cfgp)]
    budget = max(60.0, (TRAIN_END_S + 240) - elapsed())
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=budget)
        rc_, out_, err_ = r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired as exc:
        rc_, out_, err_ = 'timeout', (exc.stdout or b'').decode('utf-8', 'replace') if isinstance(exc.stdout, bytes) else (exc.stdout or ''), ''
        for pid in _compute_app_pids():
            if pid != os.getpid():
                try:
                    os.kill(pid, 9)
                except Exception:  # noqa: BLE001
                    pass
    (RUN_DIR / f'train_stdout_{world}.txt').write_text((out_ or '')[-20000:])
    (RUN_DIR / f'train_stderr_{world}.txt').write_text((err_ or '')[-20000:])
    return {'world': world, 'returncode': rc_, 's': round(time.monotonic() - t, 1),
            'adapter_saved': (ADAPTER_DIR / 'adapter_model.safetensors').exists()}


TRAIN_RUNS = [run_train(4)]
if not TRAIN_RUNS[-1]['adapter_saved'] and elapsed() < TRAIN_END_S - 600:
    TRAIN_RUNS.append(run_train(1))   # the one in-kernel fallback: one process, one GPU
RUN['train_runs'] = TRAIN_RUNS
TRAIN_INFO = json.loads(TRAIN_LOG.read_text()) if TRAIN_LOG.exists() else {}
RUN['train'] = {k: v for k, v in TRAIN_INFO.items() if k not in ('history', 'b_norm', 'events')}
stage('trained', runs=TRAIN_RUNS, steps=TRAIN_INFO.get('steps'), L_ok=TRAIN_INFO.get('L_ok'),
      b_norm_total=TRAIN_INFO.get('b_norm_total'), weights=TRAIN_INFO.get('weights'))
if not TRAIN_RUNS[-1]['adapter_saved']:
    stop('infrastructure', 'training produced no adapter')

# %%
# ---------------------------------------------------------------- boot 1: the shipped tree plus the adapter
blob = (ADAPTER_DIR / 'adapter_model.safetensors').read_bytes()
RUN['adapter'] = {'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()}
agent_yaml = (SUB1 / 'agent.yaml').read_text()
if not re.search(r'(?m)^adapter:', agent_yaml):
    agent_yaml = re.sub(r'(?m)^(model:.*)$', r'\1\nadapter: copy_lora', agent_yaml, count=1)
    (SUB1 / 'agent.yaml').write_text(agent_yaml)
manifest1 = discover_adapters(str(SUB1), adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
RUN['adapter']['discovered'] = {n: getattr(i, 'rank', None) for n, i in manifest1.adapters.items()}
if elapsed() > BOOT1_LATEST_START_S:
    stop('infrastructure', 'no time left for boot 1')
server, tee, info1 = boot('boot1', SUB1, manifest1, BOOT1_STARTUP_TIMEOUT_S)
RUN['boot1'] = info1; save_run()
print('boot1:', json.dumps(info1, indent=1, default=str)[:2000])
if server is None:
    RUN['status'] = 'boot1_failed'; stage('boot1_failed')
    raise SystemExit('boot 1 failed')
base1 = info1['served_base']
url = server.base_url

# idle-server probes first: decode speed, then the logprob texts
for label, served in (('base1', base1), ('adapter', 'copy_lora'), ('base1', base1), ('adapter', 'copy_lora')):
    record_probe({'boot': 'boot1', 'label': label, 'kind': 'decode', **decode_probe(url, served)})
for label, served in (('base1', base1), ('base1_repeat', base1), ('adapter', 'copy_lora')):
    for i, text in enumerate(LOGPROB_PROMPTS):
        record_probe({'boot': 'boot1', 'label': label, 'kind': 'logprob', 'i': i, **prompt_logprobs(url, served, text)})

# routing through the official compile path (recorded)
routing = {}
try:
    agent1, registry1, _ = compile_agent(SUB1, server, manifest1)
    routing['agent_model'] = getattr(agent1.model, 'model', None)
    routing['registry_models'] = {n: (getattr(registry1.get(n), 'model', None) or str(registry1.get(n)))
                                  for n in registry1.list_available()}
except Exception as exc:  # noqa: BLE001
    routing['error'] = f'{type(exc).__name__}: {str(exc)[:800]}'
RUN['routing'] = routing

jobs = []
for it in EVAL:   # interleaved per prompt: base1 then adapter
    for arm, served in (('base1', base1), ('adapter', 'copy_lora')):
        jobs.append(({'boot': 'boot1', 'arm': arm, 'kind': 'edit', 'pid': it['pid'], 'role': 'eval'},
                     make_body(it['body_read'], served, True), url, it))
for it in DRIFT:
    for arm, served in (('base1', base1), ('adapter', 'copy_lora')):
        jobs.append(({'boot': 'boot1', 'arm': arm, 'kind': 'drift', 'pid': it['pid'], 'role': 'eval'},
                     make_body(it['body_first'], served, True), url, None))
for it in EVAL[:N_T1]:
    for arm, served in (('base1', base1), ('adapter', 'copy_lora')):
        jobs.append(({'boot': 'boot1', 'arm': arm, 'kind': 't1', 'pid': it['pid'], 'role': 'eval'},
                     make_body(it['body_read'], served, False), url, it))
p1 = run_phase('boot1', jobs, min(elapsed() + BOOT1_PHASE_S, HARD_CAP_S - 90))
RUN['phase1'] = p1
tee.stop_and_final_copy()
info1.update(parse_log((RUN_DIR / 'boot1.log').read_text()))
info1['teardown_s'] = teardown(server)
RUN['boot1'] = info1
RUN['status'] = 'complete'
stage('done', **p1)

# %%
# ---------------------------------------------------------------- quick look (the readings are applied offline)
rows = [json.loads(ln) for ln in open(EVAL_ROWS)] if EVAL_ROWS.exists() else []
for arm in ('base0', 'base1', 'adapter'):
    ed = [r for r in rows if r.get('arm') == arm and r.get('kind') == 'edit' and r.get('status') == 200]
    print(arm, 'edit n', len(ed), 'exact', sum(r.get('exact', False) for r in ed),
          'classes', dict(Counter(r.get('cls') for r in ed)))
print('train', {k: RUN['train'].get(k) for k in ('weights', 'L_ok', 'steps', 'seqs_seen', 'stopped', 'b_norm_total')})
print('elapsed', round(elapsed(), 1), 's')
save_run()
