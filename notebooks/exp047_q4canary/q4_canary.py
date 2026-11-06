# %% [markdown]
# # EXP-047: Q4 adapter canary on the E4B (zero tasks, no agent run, no grading)
#
# Pre-registration: `experiments/EXP-047-q4-adapter-canary-e4b.md`. Builds three PEFT LoRA adapters inside the
# kernel from the E4B checkpoint's own module shapes (no competition data, no third-party weights), boots vLLM
# twice through the harness's own `VllmServer` (boot 0 without adapters, boot 1 with all three discovered by
# `discover_adapters`), and records prompt logprobs, greedy text, decode speed, `/v1/models`, the `build_cmd`
# LoRA flags and the KV cache tokens of each boot. The readings are applied offline by
# `experiments/EXP-047/analyze_canary.py`.
#
# **Inputs:** dataset `metric/gemma-4-developer-agent-wheelhouse`, model
# `google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2`. No competition input is attached.
# **Accelerator:** NVIDIA L4 x4. **Internet:** off.
#
# Build: `python tools/build_notebook.py --src notebooks/exp047_q4canary/q4_canary.py --out notebooks/exp047_q4canary/q4_canary.ipynb`
# Retrieve: `kaggle kernels output rainm4/gemma4-exp047-q4-canary -p runs/EXP-047-q4-canary`

# %%
# ---------------------------------------------------------------- parameters
EXP_ID = "EXP-047-q4-canary"
MODEL = "gemma-4-e4b-it-qat-w4a16-ct"
MODEL_DIR = f"/kaggle/input/models/google/gemma-4/other/{MODEL}/2"
SEED = 46
SOFT_STOP_S = 27 * 60          # no new boot or probe group starts after this
HARD_CAP_S = 30 * 60           # every wait is bounded so that the kernel ends near this
BOOT0_STARTUP_TIMEOUT_S = 600
BOOT1_STARTUP_TIMEOUT_S = 720
REQ_TIMEOUT_S = 120
GREEDY_MAX_TOKENS = 48
DECODE_MAX_TOKENS = 256
# Fixed inputs, written for this experiment in our own words.
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
CHAT_QUESTIONS = [
    "In two sentences, explain why the sky looks blue during the day.",
    "List the first five prime numbers and say in one sentence what makes a number prime.",
]
DECODE_PROMPT = "Write a numbered list of short, simple sentences about the seasons of the year."

# %%
# ---------------------------------------------------------------- environment + wheelhouse (hosts' recipe, as EXP-006)
import glob, hashlib, importlib, importlib.metadata as im_md, json, os, re, shutil, subprocess, sys, threading, time
import urllib.error, urllib.request
from pathlib import Path

T0 = time.monotonic()


def elapsed() -> float:
    return time.monotonic() - T0


os.environ.update({
    'LITELLM_LOCAL_MODEL_COST_MAP': 'True', 'TRANSFORMERS_NO_TF': '1', 'VLLM_WORKER_MULTIPROC_METHOD': 'spawn',
    'VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS': '1', 'VLLM_ENGINE_READY_TIMEOUT_S': '1200',
    'VLLM_NO_USAGE_STATS': '1', 'OTEL_SDK_DISABLED': 'true', 'PYTORCH_CUDA_ALLOC_CONF': 'expandable_segments:True',
    'NCCL_DEBUG': 'WARN', 'TRANSFORMERS_OFFLINE': '1', 'VLLM_LOGGING_LEVEL': 'INFO',
})

RUN_DIR = Path('/kaggle/working/runs') / EXP_ID
RUN_DIR.mkdir(parents=True, exist_ok=True)
CANARY: dict = {'exp_id': EXP_ID, 'model': MODEL, 'status': 'started', 'stages': {}}


def save_canary():
    CANARY['elapsed_s'] = round(elapsed(), 1)
    (RUN_DIR / 'canary.json').write_text(json.dumps(CANARY, indent=1, default=str))


def stage(name: str, **kw):
    CANARY['stages'][name] = {'t_s': round(elapsed(), 1), **kw}
    save_canary()
    print(f'[{elapsed():7.1f}s] {name}', kw if kw else '')


WHEELHOUSE_DIR = next((Path(p) for p in ['/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse',
                                         '/kaggle/input/gemma-4-developer-agent-wheelhouse'] if Path(p).exists()), None)
if WHEELHOUSE_DIR is None:
    CANARY['status'] = 'infrastructure'; stage('wheelhouse_missing')
    raise SystemExit('wheelhouse input missing')
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
    CANARY['status'] = 'infrastructure'; stage('import_failed', error=f'{type(_exc).__name__}: {_exc}')
    raise SystemExit(f'imports failed: {_exc}')

env = {'python': sys.version, 'install_s': round(time.time() - T_INSTALL, 1), 'skipped_wheels': skipped,
       'wheelhouse_dir': str(WHEELHOUSE_DIR), 'n_wheels': len(all_wheels)}
for pkg in ('vllm', 'torch', 'adk_submission', 'swegemma', 'google-adk', 'litellm', 'safetensors'):
    try:
        env[pkg] = im_md.version(pkg)
    except im_md.PackageNotFoundError:
        env[pkg] = None
for w in sorted(WHEELHOUSE_DIR.glob('vllm-*.whl')) + sorted(WHEELHOUSE_DIR.glob('adk_submission-*.whl')) + \
        sorted(WHEELHOUSE_DIR.glob('swegemma-*.whl')):
    h = hashlib.sha256()
    with open(w, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    env.setdefault('wheel_sha256', {})[w.name] = h.hexdigest()
GPU_COUNT = torch.cuda.device_count() if torch.cuda.is_available() else 0
env['gpu_count'] = GPU_COUNT
CANARY['env'] = env
(RUN_DIR / 'env.json').write_text(json.dumps(env, indent=1))
print(json.dumps(env, indent=1))
if GPU_COUNT != 4 or not Path(MODEL_DIR, 'config.json').exists():
    CANARY['status'] = 'infrastructure'; stage('no_gpu_or_model', gpu_count=GPU_COUNT, model_dir=MODEL_DIR)
    raise SystemExit('need 4 GPUs and the E4B input')
stage('installed')

# %%
# ---------------------------------------------------------------- model config and the q_proj / o_proj shapes
from safetensors import safe_open

cfg = json.loads(Path(MODEL_DIR, 'config.json').read_text())
tcfg = cfg.get('text_config') or cfg
shapes_report = {
    'architectures': cfg.get('architectures'), 'model_type': cfg.get('model_type'),
    'quant_method': (cfg.get('quantization_config') or {}).get('quant_method'),
    'text': {k: tcfg.get(k) for k in ('hidden_size', 'num_hidden_layers', 'num_attention_heads', 'num_key_value_heads',
                                      'head_dim', 'global_head_dim', 'intermediate_size', 'vocab_size',
                                      'num_kv_shared_layers', 'sliding_window', 'layer_types')},
}
HIDDEN = int(tcfg['hidden_size'])

idx_path = Path(MODEL_DIR, 'model.safetensors.index.json')
if idx_path.exists():
    weight_map = json.loads(idx_path.read_text())['weight_map']
else:
    files = sorted(Path(MODEL_DIR).glob('*.safetensors'))
    weight_map = {}
    for f in files:
        with safe_open(str(f), 'pt') as sf:
            for k in sf.keys():
                weight_map[k] = f.name

MOD_RE = re.compile(r'^(.*\.layers\.(\d+)\.self_attn\.(q_proj|o_proj))\.(weight|weight_packed|weight_shape)$')
mods: dict[str, dict] = {}
for name in weight_map:
    m = MOD_RE.match(name)
    if not m:
        continue
    if 'vision' in name or 'audio' in name:
        continue
    mods.setdefault(m.group(1), {'layer': int(m.group(2)), 'proj': m.group(3), 'tensors': set()})['tensors'].add(m.group(4))


def module_shape(mod: str, tensors: set) -> tuple[list[int], str]:
    if 'weight_shape' in tensors:
        with safe_open(str(Path(MODEL_DIR, weight_map[f'{mod}.weight_shape'])), 'pt') as sf:
            return [int(x) for x in sf.get_tensor(f'{mod}.weight_shape').tolist()], 'weight_shape'
    if 'weight' in tensors:
        with safe_open(str(Path(MODEL_DIR, weight_map[f'{mod}.weight'])), 'pt') as sf:
            return list(sf.get_slice(f'{mod}.weight').get_shape()), 'weight'
    with safe_open(str(Path(MODEL_DIR, weight_map[f'{mod}.weight_packed'])), 'pt') as sf:
        out, packed_in = sf.get_slice(f'{mod}.weight_packed').get_shape()
    return [int(out), int(packed_in) * 8], 'weight_packed_x8'


for mod, info in mods.items():
    info['shape'], info['shape_from'] = module_shape(mod, info['tensors'])
    info['tensors'] = sorted(info['tensors'])
prefixes = sorted({mod.split('.layers.')[0] for mod in mods})
layers = sorted({info['layer'] for info in mods.values()})
bad = [mod for mod, info in mods.items()
       if (info['proj'] == 'q_proj' and info['shape'][1] != HIDDEN) or (info['proj'] == 'o_proj' and info['shape'][0] != HIDDEN)]
shapes_report.update({'module_prefixes': prefixes, 'n_layers_found': len(layers), 'n_modules': len(mods),
                      'shape_mismatch': bad,
                      'modules': {mod: {k: v for k, v in info.items()} for mod, info in sorted(mods.items())}})
(RUN_DIR / 'model_shapes.json').write_text(json.dumps(shapes_report, indent=1))
print(json.dumps({k: v for k, v in shapes_report.items() if k != 'modules'}, indent=1))
if not mods or bad or len(prefixes) != 1 or 0 not in layers:
    CANARY['status'] = 'infrastructure'; stage('shape_check_failed', prefixes=prefixes, bad=bad[:5])
    raise SystemExit('could not derive q_proj/o_proj shapes cleanly')
stage('shapes', architectures=cfg.get('architectures'), n_layers=len(layers), prefix=prefixes[0])

# %%
# ---------------------------------------------------------------- the three adapters and the two submission dirs
from safetensors.torch import save_file

SUB0 = Path('/kaggle/working/canary_sub0')   # boot 0: no adapters/, no adapter line
SUB1 = Path('/kaggle/working/canary_sub')    # boot 1: adapters/ with three PEFT dirs, adapter line on the root
for d in (SUB0, SUB1):
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
(SUB0 / 'agent.yaml').write_text(f'name: canary_agent\nmodel: {MODEL}\ninstruction: "Answer briefly."\n')
(SUB1 / 'agent.yaml').write_text(f'name: canary_agent\nmodel: {MODEL}\nadapter: canary_big\ninstruction: "Answer briefly."\n')

ADAPTERS = {
    #  name           rank alpha layers      A std  B std
    'canary_zero': dict(r=4, alpha=8, layers=[0], a_std=0.01, b_std=0.0),
    'canary_big': dict(r=4, alpha=8, layers=[0], a_std=0.01, b_std=1.0),
    'canary_loud': dict(r=8, alpha=16, layers=None, a_std=1.0, b_std=1.0),
}
gen = torch.Generator().manual_seed(SEED)
adapters_report = {}
for i, (aname, spec) in enumerate(ADAPTERS.items()):
    adir = SUB1 / 'adapters' / aname
    adir.mkdir(parents=True)
    tensors = {}
    for mod, info in sorted(mods.items()):
        if spec['layers'] is not None and info['layer'] not in spec['layers']:
            continue
        out_f, in_f = info['shape']
        a = torch.randn(spec['r'], in_f, generator=gen) * spec['a_std']
        b = torch.randn(out_f, spec['r'], generator=gen) * spec['b_std'] if spec['b_std'] else torch.zeros(out_f, spec['r'])
        tensors[f'base_model.model.{mod}.lora_A.weight'] = a.to(torch.bfloat16).contiguous()
        tensors[f'base_model.model.{mod}.lora_B.weight'] = b.to(torch.bfloat16).contiguous()
    save_file(tensors, str(adir / 'adapter_model.safetensors'), metadata={'format': 'pt'})
    acfg = {
        'alpha_pattern': {}, 'auto_mapping': None, 'base_model_name_or_path': f'google/{MODEL}', 'bias': 'none',
        'fan_in_fan_out': False, 'inference_mode': True, 'init_lora_weights': True, 'layer_replication': None,
        'layers_pattern': None, 'layers_to_transform': spec['layers'], 'loftq_config': {}, 'lora_alpha': spec['alpha'],
        'lora_dropout': 0.0, 'megatron_config': None, 'megatron_core': 'megatron.core', 'modules_to_save': None,
        'peft_type': 'LORA', 'r': spec['r'], 'rank_pattern': {}, 'revision': None,
        'target_modules': ['q_proj', 'o_proj'], 'task_type': 'CAUSAL_LM', 'use_dora': False, 'use_rslora': False,
    }
    (adir / 'adapter_config.json').write_text(json.dumps(acfg, indent=2))
    # re-read from disk: what vLLM will load
    nz_a = nz_b = n_a = n_b = 0
    with safe_open(str(adir / 'adapter_model.safetensors'), 'pt') as sf:
        keys = list(sf.keys())
        for k in keys:
            t = sf.get_tensor(k)
            if k.endswith('lora_A.weight'):
                nz_a += int((t != 0).sum()); n_a += t.numel()
            else:
                nz_b += int((t != 0).sum()); n_b += t.numel()
    blob = (adir / 'adapter_model.safetensors').read_bytes()
    adapters_report[aname] = {**spec, 'n_tensors': len(keys), 'lora_A_nonzero': nz_a, 'lora_A_total': n_a,
                              'lora_B_nonzero': nz_b, 'lora_B_total': n_b, 'bytes': len(blob),
                              'sha256': hashlib.sha256(blob).hexdigest(), 'first_key': keys[0] if keys else None}
manifest0 = discover_adapters(str(SUB0), adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
manifest1 = discover_adapters(str(SUB1), adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
adapters_report['_discovered_boot0'] = sorted(manifest0.adapters.keys())
adapters_report['_discovered_boot1'] = {n: getattr(info, 'rank', None) for n, info in manifest1.adapters.items()}
(RUN_DIR / 'adapters.json').write_text(json.dumps(adapters_report, indent=1))
print(json.dumps(adapters_report, indent=1))
stage('adapters_built', discovered=adapters_report['_discovered_boot1'])

# %%
# ---------------------------------------------------------------- log capture, teardown, HTTP (as EXP-006)
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')
LOG_PATTERNS = {
    'gpu_kv_cache_tokens': re.compile(r'GPU KV cache size:\s*([\d,]+) tokens'),
    'max_concurrency': re.compile(r'Maximum concurrency for ([\d,]+) tokens per request:\s*([\d.]+)x'),
    'kv_avail_gib': re.compile(r'Available KV cache memory:\s*([\d.]+)\s*GiB'),
    'cudagraph': re.compile(r'Graph capturing finished in\s*([\d.]+)\s*secs?, took\s*([\d.]+)\s*GiB'),
}
LORA_LINE_RE = re.compile(r'(?i)lora')


def parse_log(text: str) -> dict:
    text = ANSI_RE.sub('', text)
    out: dict = {}
    m = LOG_PATTERNS['gpu_kv_cache_tokens'].findall(text)
    if m:
        out['gpu_kv_cache_tokens_all'] = [int(x.replace(',', '')) for x in m]
        out['gpu_kv_cache_tokens'] = min(out['gpu_kv_cache_tokens_all'])
    m = LOG_PATTERNS['max_concurrency'].findall(text)
    if m:
        out['max_concurrency'] = min(float(x) for _, x in m)
    m = LOG_PATTERNS['kv_avail_gib'].findall(text)
    if m:
        out['kv_avail_gib_min'] = min(float(x) for x in m)
    m = LOG_PATTERNS['cudagraph'].findall(text)
    if m:
        out['cudagraph_s_max'] = max(float(s) for s, _ in m)
        out['n_cudagraph_lines'] = len(m)
    out['n_lora_lines'] = sum(1 for ln in text.splitlines() if LORA_LINE_RE.search(ln))
    return out


def classify_failure(text: str) -> str:
    for status, pat in [('kv_or_max_len', re.compile(r'(?i)max seq len|maximum model length|KV cache is needed|larger than the maximum number of tokens')),
                        ('lora_unsupported', re.compile(r'does not support LoRA')),
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
            self._copy_once(); self._stop.wait(1.0)

    def start(self):
        self._thread.start()

    def stop_and_final_copy(self) -> str:
        self._stop.set(); self._thread.join(timeout=5); self._copy_once()
        return self.dest.read_text() if self.dest.exists() else ''


def _compute_app_pids() -> list[int]:
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


def http(method: str, url: str, body: dict | None = None, timeout: float = REQ_TIMEOUT_S) -> dict:
    t = time.monotonic()
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {'status': resp.status, 'json': json.loads(resp.read()), 's': round(time.monotonic() - t, 3)}
    except urllib.error.HTTPError as exc:
        return {'status': exc.code, 'error': exc.read().decode('utf-8', 'replace')[:2000], 's': round(time.monotonic() - t, 3)}
    except Exception as exc:  # noqa: BLE001
        return {'status': None, 'error': f'{type(exc).__name__}: {exc}', 's': round(time.monotonic() - t, 3),
                'timeout': 'timed out' in str(exc).lower() or isinstance(exc, TimeoutError)}


# %%
# ---------------------------------------------------------------- probes
PROBES = RUN_DIR / 'probes.jsonl'


def record(row: dict):
    with open(PROBES, 'a') as f:
        f.write(json.dumps(row) + '\n')


def prompt_logprobs(base_url: str, model_name: str, prompt: str) -> dict:
    r = http('POST', base_url + '/completions', {'model': model_name, 'prompt': prompt, 'max_tokens': 1,
                                                 'temperature': 0, 'echo': True, 'logprobs': 0})
    out = {'status': r['status'], 's': r['s'], 'method': 'echo'}
    if r['status'] == 200:
        out['resp_model'] = (r['json'] or {}).get('model')  # EXP-047 amendment (i): the name the server answered under
        try:
            ch = r['json']['choices'][0]
            n_prompt = r['json']['usage']['prompt_tokens']
            lp = ch['logprobs']
            out.update(tokens=lp['tokens'][:n_prompt], logprobs=lp['token_logprobs'][1:n_prompt], n_prompt=n_prompt)
            return out
        except Exception as exc:  # noqa: BLE001
            out['parse_error'] = f'{type(exc).__name__}: {exc}'
    else:
        out['error'] = r.get('error')
        if r.get('timeout'):
            out['timeout'] = True
            return out
    r = http('POST', base_url + '/completions', {'model': model_name, 'prompt': prompt, 'max_tokens': 1,
                                                 'temperature': 0, 'prompt_logprobs': 0})
    out2 = {'status': r['status'], 's': r['s'], 'method': 'prompt_logprobs', 'echo_attempt': out}
    if r['status'] == 200:
        out2['resp_model'] = (r['json'] or {}).get('model')
        try:
            pl = r['json']['choices'][0].get('prompt_logprobs') or r['json'].get('prompt_logprobs')
            toks, lps = [], []
            for pos in pl[1:]:
                (tid, ent), = list(pos.items())[:1]
                toks.append(str(tid)); lps.append(ent['logprob'])
            out2.update(tokens=toks, logprobs=lps, n_prompt=len(pl))
        except Exception as exc:  # noqa: BLE001
            out2['parse_error'] = f'{type(exc).__name__}: {exc}'
    else:
        out2['error'] = r.get('error'); out2['timeout'] = bool(r.get('timeout'))
    return out2


def chat(base_url: str, model_name: str, text: str, max_tokens: int, ignore_eos: bool = False) -> dict:
    body = {'model': model_name, 'messages': [{'role': 'user', 'content': text}], 'max_tokens': max_tokens,
            'temperature': 0, 'chat_template_kwargs': {'enable_thinking': False}}
    if ignore_eos:
        body['ignore_eos'] = True
    r = http('POST', base_url + '/chat/completions', body)
    out = {'status': r['status'], 's': r['s']}
    if r['status'] == 200:
        out['resp_model'] = r['json'].get('model')
        msg = r['json']['choices'][0]['message']
        out.update(text=msg.get('content'), completion_tokens=(r['json'].get('usage') or {}).get('completion_tokens'))
        if out['completion_tokens'] and r['s']:
            out['tok_s'] = round(out['completion_tokens'] / r['s'], 2)
    else:
        out['error'] = r.get('error'); out['timeout'] = bool(r.get('timeout'))
    return out


def probe_names(boot: str, base_url: str, names: list[tuple[str, str]], decode: bool):
    """names: (label, served model name). One timeout on a label skips the rest of that label's requests."""
    dead: set[str] = set()
    for kind in ('logprob', 'greedy', 'decode'):
        if kind == 'decode' and not decode:
            continue
        for label, served in names:
            if label in dead or elapsed() > HARD_CAP_S - 60:
                record({'boot': boot, 'label': label, 'kind': kind, 'skipped': True}); continue
            items = {'logprob': list(enumerate(LOGPROB_PROMPTS)), 'greedy': list(enumerate(CHAT_QUESTIONS)),
                     'decode': [(0, DECODE_PROMPT)]}[kind]
            for i, text in items:
                if kind == 'logprob':
                    res = prompt_logprobs(base_url, served, text)
                elif kind == 'greedy':
                    res = chat(base_url, served, text, GREEDY_MAX_TOKENS)
                else:
                    res = chat(base_url, served, text, DECODE_MAX_TOKENS, ignore_eos=True)
                record({'boot': boot, 'label': label, 'served': served, 'kind': kind, 'i': i, **res})
                if res.get('timeout'):
                    dead.add(label); break


def boot(label: str, sub: Path, manifest, startup_timeout: int):
    cfg = VllmConfig(
        model=MODEL_DIR, port=8000, host='127.0.0.1', tool_call_parser='gemma4', reasoning_parser='gemma4',
        default_chat_template_kwargs={'enable_thinking': True}, max_model_len=32768,
        dtype='bfloat16' if torch.cuda.is_bf16_supported() else 'auto', gpu_memory_utilization=0.90,
        enable_auto_tool_choice=True, enable_lora=True, max_loras=8, max_lora_rank=128,
        tensor_parallel_size=4, startup_timeout=startup_timeout)
    server = VllmServer(cfg, adapter_manifest=manifest)
    cmd = server.build_cmd()
    lora_flags = []
    for j, tok in enumerate(cmd):
        if tok in ('--enable-lora', '--max-loras', '--max-lora-rank', '--lora-modules'):
            lora_flags.append(tok)
            if tok in ('--max-loras', '--max-lora-rank'):
                lora_flags.append(cmd[j + 1])
            if tok == '--lora-modules':
                lora_flags.extend(t.split('=')[0] for t in cmd[j + 1:] if '=' in t and not t.startswith('--'))
    info = {'lora_flags': lora_flags, 'startup_timeout': startup_timeout}
    tee = LogTee(server, RUN_DIR / f'{label}.log')
    t = time.monotonic()
    try:
        tee.start()
        server.start()
        info['started'] = True
    except Exception as exc:  # noqa: BLE001
        info['started'] = False
        info['error'] = f'{type(exc).__name__}: {str(exc)[:1500]}'
    info['boot_s'] = round(time.monotonic() - t, 1)
    if info['started']:
        tee._copy_once()
        log_path = RUN_DIR / f'{label}.log'
        log_text = log_path.read_text() if log_path.exists() else ''
    else:
        log_text = tee.stop_and_final_copy()
    info.update(parse_log(log_text))
    if not info['started']:
        info['failure_class'] = classify_failure(log_text + info.get('error', ''))
        info['teardown_s'] = teardown(server)
        return None, tee, info
    info['served_base'] = getattr(server, 'effective_model_path', MODEL_DIR)
    models = http('GET', server.base_url + '/models', timeout=30)
    info['v1_models'] = [m.get('id') for m in (models.get('json') or {}).get('data', [])] if models['status'] == 200 else models
    return server, tee, info


# %%
# ---------------------------------------------------------------- boot 0: no adapters
server, tee, info0 = boot('boot0', SUB0, manifest0, BOOT0_STARTUP_TIMEOUT_S)
CANARY['boot0'] = info0; save_canary()
print('boot0:', json.dumps({k: v for k, v in info0.items()}, indent=1, default=str))
if server is None:
    CANARY['status'] = 'infrastructure'; stage('boot0_failed')
    raise SystemExit('boot 0 failed: infrastructure (reading A0)')
base0 = info0['served_base']
probe_names('boot0', server.base_url, [('base', base0), ('base_repeat', base0)], decode=False)
tee.stop_and_final_copy()
info0.update(parse_log((RUN_DIR / 'boot0.log').read_text()))
info0['teardown_s'] = teardown(server)
CANARY['boot0'] = info0
stage('boot0_done', kv=info0.get('gpu_kv_cache_tokens'))

# %%
# ---------------------------------------------------------------- boot 1: three adapters
if elapsed() > SOFT_STOP_S - BOOT1_STARTUP_TIMEOUT_S:
    CANARY['status'] = 'infrastructure'; stage('no_time_for_boot1')
    raise SystemExit('no time left for boot 1')
server, tee, info1 = boot('boot1', SUB1, manifest1, BOOT1_STARTUP_TIMEOUT_S)
CANARY['boot1'] = info1; save_canary()
print('boot1:', json.dumps(info1, indent=1, default=str))
if server is not None:
    base1 = info1['served_base']
    probe_names('boot1', server.base_url,
                [('base', base1), ('base_repeat', base1), ('canary_zero', 'canary_zero'),
                 ('canary_big', 'canary_big'), ('canary_loud', 'canary_loud')], decode=True)
    # routing through the official compile path (recorded, not read)
    routing: dict = {}
    try:
        import litellm
        from swegemma.harness.agent_runner import resolve_swegemma_adapter
        litellm.drop_params = True
        declared = discover_declared_models(str(SUB1))
        routing['declared'] = sorted(declared)
        registry = server.create_model_registry(aliases=sorted({*declared, MODEL}), model_prefix='openai/')
        # amendment (i): what each name resolves to; an adapter name bound to the base path is a silent fall-through
        routing['registry_models'] = {n: (getattr(registry.get(n), 'model', None) or str(registry.get(n)))
                                      for n in registry.list_available()}
        agent = compile_submission(submission_dir=str(SUB1), tool_registry={}, model_registry=registry,
                                   adapter_manifest=manifest1,
                                   adapter_resolver_fn=lambda b, i: resolve_swegemma_adapter(b, i, registry))
        mdl = getattr(agent, 'model', None)
        routing['agent_model'] = getattr(mdl, 'model', None) if not isinstance(mdl, str) else mdl
        resp = litellm.completion(model=routing['agent_model'], api_base=server.base_url, api_key='EMPTY',
                                  messages=[{'role': 'user', 'content': CHAT_QUESTIONS[0]}], temperature=0,
                                  max_tokens=GREEDY_MAX_TOKENS, timeout=REQ_TIMEOUT_S,
                                  extra_body={'chat_template_kwargs': {'enable_thinking': False}})
        routing['text'] = resp.choices[0].message.content
        routing['resp_model'] = getattr(resp, 'model', None)
    except Exception as exc:  # noqa: BLE001
        routing['error'] = f'{type(exc).__name__}: {str(exc)[:1500]}'
    CANARY['routing'] = routing
    tee.stop_and_final_copy()
    info1.update(parse_log((RUN_DIR / 'boot1.log').read_text()))
    info1['teardown_s'] = teardown(server)
CANARY['boot1'] = info1
CANARY['status'] = 'complete' if server is not None else 'boot1_failed'
stage('done', kv0=info0.get('gpu_kv_cache_tokens'), kv1=info1.get('gpu_kv_cache_tokens'))

# %%
# ---------------------------------------------------------------- quick look (the readings are applied offline)
rows = [json.loads(ln) for ln in open(PROBES)] if PROBES.exists() else []


def lp(boot_, label):
    return [r.get('logprobs') for r in sorted((r for r in rows if r['boot'] == boot_ and r['label'] == label
                                               and r['kind'] == 'logprob'), key=lambda r: r.get('i', 0))]


def dmax(a, b):
    vals = [abs(x - y) for pa, pb in zip(a, b) if pa and pb and len(pa) == len(pb) for x, y in zip(pa, pb)
            if x is not None and y is not None]
    return max(vals) if vals else None


for name in ('base_repeat', 'canary_zero', 'canary_big', 'canary_loud'):
    print(f'boot1 d({name}, base) =', dmax(lp('boot1', name), lp('boot1', 'base')))
print('boot0 d(base_repeat, base) =', dmax(lp('boot0', 'base_repeat'), lp('boot0', 'base')))
for r in rows:
    if r['kind'] == 'greedy' and r.get('i') == 0:
        print(r['boot'], r['label'], repr((r.get('text') or '')[:120]))
print('KV tokens boot0', info0.get('gpu_kv_cache_tokens'), 'boot1', info1.get('gpu_kv_cache_tokens'))
print('elapsed', round(elapsed(), 1), 's')
