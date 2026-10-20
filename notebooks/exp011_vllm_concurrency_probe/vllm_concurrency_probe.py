# %% [markdown]
# # EXP-006: vLLM concurrency/capacity probe (all 4 allowed Gemma-4 models, zero tasks, zero scoring)
#
# Boots each of the 4 `ALLOWED_MODEL_NAMES` once, with the harness-faithful vLLM server config (TP=4,
# `gpu_memory_utilization=0.90`, `max_model_len=32768`, no LoRA flags since our submission ships no
# adapters), reads vLLM's own startup log for its "Maximum concurrency for N tokens per request" line
# and KV-cache block counts, tears the server down cleanly, and moves to the next model. No
# `evaluate_task`, no `eval_config.yaml`, no `submission/` artifact, no scoring, no budget-gate
# interaction. Designed to fit well under the self-imposed 55-minute hard cap (`GLOBAL_HARD_CAP_S`).
#
# **Attach as inputs** (Add Input): competition `gemma-4-developer-agent`, dataset
# `metric/gemma-4-developer-agent-wheelhouse`, all 4 models:
# `google/gemma-4/Other/{gemma-4-31b-it-qat-w4a16-ct,gemma-4-12b-it-qat-w4a16-ct,gemma-4-e4b-it-qat-w4a16-ct,gemma-4-e2b-it-qat-w4a16-ct}/2`.
# **Accelerator**: NVIDIA L4 x4. **Internet**: off.
#
# Build: `python tools/build_notebook.py --src notebooks/exp011_vllm_concurrency_probe/vllm_concurrency_probe.py --out notebooks/exp011_vllm_concurrency_probe/vllm_concurrency_probe.ipynb`
# Retrieve: `kaggle kernels output rainm4/gemma4-exp011-vllm-concurrency-probe -p runs/EXP-006-vllm-concurrency-probe`

# %%
# ---------------------------------------------------------------- parameters (edit me)
EXP_ID = "EXP-006-vllm-concurrency-probe"

MODELS = [
    "gemma-4-31b-it-qat-w4a16-ct",
    "gemma-4-12b-it-qat-w4a16-ct",
    "gemma-4-e4b-it-qat-w4a16-ct",
    "gemma-4-e2b-it-qat-w4a16-ct",
]
MODEL_ROOT = "/kaggle/input/models/google/gemma-4/other"
MODEL_VERSION = 2
# Copied verbatim from the organizers' getting-started recipe: without this, 12B does not boot the way
# the real harness boots it (our own kaggle_eval_l4x4.py mirror omits it because it never serves 12B).
MODEL_VLLM_EXTRA_ARGS = {
    "gemma-4-12b-it-qat-w4a16-ct": [
        "--hf-overrides",
        '{"architectures": ["Gemma4ForCausalLM"], "model_type": "gemma4"}',
    ],
}
PER_MODEL_STARTUP_TIMEOUT_S = {
    "gemma-4-31b-it-qat-w4a16-ct": 900,
    "gemma-4-12b-it-qat-w4a16-ct": 600,
    "gemma-4-e4b-it-qat-w4a16-ct": 600,
    "gemma-4-e2b-it-qat-w4a16-ct": 600,
}

GLOBAL_SOFT_BUDGET_S = 45 * 60   # after this, no new first attempt starts
GLOBAL_HARD_CAP_S = 55 * 60      # no attempt starts unless its worst case still fits under this
GPU_FREE_TIMEOUT_S = 120         # teardown wait before declaring a GPU "not freed"
GPU_FREE_TOLERANCE_MIB = 1024    # per-GPU slack above the measured baseline
RETRY_ON_FAILURE = True          # one same-config retry, plus one labeled diagnostic attempt on OOM
DIAGNOSTIC_UTIL = 0.85           # fallback gpu_memory_utilization for OOM/insufficient-memory retries
BASE_PORT = 8000                 # model i uses BASE_PORT + i so a lingering socket never blocks the next boot

MEASURE_BATCH_SCALING = True     # optional ~1 min/model decode-batching arm; False = pure capacity probe
BURST_NS = [1, 4, 16]
BURST_MAX_TOKENS = 256

# %%
# ---------------------------------------------------------------- environment + wheelhouse (hosts' recipe)
import glob, importlib, importlib.metadata as im_md, json, os, re, shutil, subprocess, sys, threading, time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

T0 = time.monotonic()

os.environ.update({
    'LITELLM_LOCAL_MODEL_COST_MAP': 'True', 'TRANSFORMERS_NO_TF': '1', 'VLLM_WORKER_MULTIPROC_METHOD': 'spawn',
    'VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS': '1', 'VLLM_ENGINE_READY_TIMEOUT_S': '1200',
    'VLLM_NO_USAGE_STATS': '1', 'OTEL_SDK_DISABLED': 'true', 'PYTORCH_CUDA_ALLOC_CONF': 'expandable_segments:True',
    'NCCL_DEBUG': 'WARN', 'TRANSFORMERS_OFFLINE': '1', 'VLLM_LOGGING_LEVEL': 'INFO',
})

RUN_DIR = Path('/kaggle/working/runs') / EXP_ID
for sub in ('logs', 'nvidia_smi', 'metrics', 'burst', 'cmd'):
    (RUN_DIR / sub).mkdir(parents=True, exist_ok=True)

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

REQUIRED_PKGS = ('adk_submission',)  # this probe never imports swegemma/evaluate -- no task/eval code path at all


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
print(f'wheelhouse: installed {len(all_wheels) - len(skipped)}/{len(all_wheels)} wheels in {time.time() - T_INSTALL:.0f}s')
missing = []
for _pkg in REQUIRED_PKGS:
    try:
        importlib.import_module(_pkg)
    except Exception as _exc:  # noqa: BLE001
        missing.append(f'{_pkg} ({_exc.__class__.__name__}: {_exc})')
if missing:
    # Nothing downstream is worth paying GPU time for without adk_submission.
    (RUN_DIR / 'summary.json').write_text(json.dumps({'status': 'env_error', 'missing': missing}, indent=1))
    raise SystemExit('required packages unavailable: ' + '; '.join(missing))
print('required packages present:', ', '.join(REQUIRED_PKGS))

try:
    import torch
    import vllm  # noqa: F401  -- import error here is also an env_error, same fail-fast reasoning as above
except Exception as _exc:  # noqa: BLE001
    (RUN_DIR / 'summary.json').write_text(json.dumps({'status': 'env_error', 'error': str(_exc)}, indent=1))
    raise SystemExit(f'vllm/torch import failed (env_error): {_exc}')

from adk_submission.server import VllmConfig, VllmServer
from adk_submission.errors import ServerStartupError

# %%
# ---------------------------------------------------------------- environment snapshot (env.json)


def _nvidia_smi_query(fields: str) -> list[list[str]]:
    try:
        out = subprocess.run(['nvidia-smi', f'--query-gpu={fields}', '--format=csv,noheader,nounits'],
                              capture_output=True, text=True, timeout=15)
        return [line.split(', ') for line in out.stdout.strip().splitlines() if line.strip()]
    except Exception as exc:  # noqa: BLE001
        print('nvidia-smi query failed:', exc)
        return []


def _per_gpu_used_mib() -> dict[int, int]:
    rows = _nvidia_smi_query('index,memory.used')
    return {int(r[0]): int(float(r[1])) for r in rows if len(r) >= 2}


def _compute_app_pids() -> list[int]:
    try:
        out = subprocess.run(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'],
                              capture_output=True, text=True, timeout=15)
        return [int(x) for x in out.stdout.split() if x.strip().isdigit()]
    except Exception as exc:  # noqa: BLE001
        print('nvidia-smi compute-apps query failed:', exc)
        return []


# Triggers the same small parent CUDA context on GPU0 the real harness's dtype expression creates, so the
# teardown baseline below is taken AFTER that context exists -- otherwise every model's "after boot" delta
# would be inflated by it on the first attempt only.
_ = torch.cuda.is_bf16_supported() if torch.cuda.is_available() else None
GPU_COUNT = torch.cuda.device_count() if torch.cuda.is_available() else 0
BASELINE_USED_MIB = _per_gpu_used_mib()

env_report = {
    'python': sys.version,
    'gpu_count': GPU_COUNT,
    'baseline_used_mib': BASELINE_USED_MIB,
    'nvidia_smi_gpus': _nvidia_smi_query('index,name,memory.total,memory.used,driver_version'),
    'install_s': round(time.time() - T_INSTALL, 1),
}
for pkg in ('vllm', 'torch', 'adk_submission', 'adk_eval_core', 'google-adk', 'litellm'):
    try:
        env_report[pkg] = im_md.version(pkg)
    except im_md.PackageNotFoundError:
        env_report[pkg] = None
(RUN_DIR / 'env.json').write_text(json.dumps(env_report, indent=1))
print('env:', json.dumps(env_report, indent=1))
if GPU_COUNT != 4:
    print(f'WARNING: expected 4 GPUs (TP=4 harness config), found {GPU_COUNT}. Results will not be L4x4-faithful.')

# %%
# ---------------------------------------------------------------- model config read (CPU-only, seconds)
model_configs: dict[str, dict] = {}
for m in MODELS:
    exact = Path(MODEL_ROOT) / m / str(MODEL_VERSION)
    resolved_by = 'exact'
    path = exact
    if not (path / 'config.json').exists():
        hits = list(Path('/kaggle/input').glob(f'**/{m}/**/config.json'))
        if hits:
            path = hits[0].parent
            resolved_by = 'glob'
        else:
            model_configs[m] = {'resolved_by': 'missing', 'path': str(exact)}
            continue
    try:
        cfg = json.loads((path / 'config.json').read_text())
    except Exception as exc:  # noqa: BLE001
        model_configs[m] = {'resolved_by': resolved_by, 'path': str(path), 'config_read_error': str(exc)}
        continue
    text_cfg = cfg.get('text_config', cfg)
    model_configs[m] = {
        'resolved_by': resolved_by,
        'path': str(path),
        'architectures': cfg.get('architectures'),
        'model_type': cfg.get('model_type'),
        'num_hidden_layers': text_cfg.get('num_hidden_layers'),
        'num_attention_heads': text_cfg.get('num_attention_heads'),
        'num_key_value_heads': text_cfg.get('num_key_value_heads'),
        'head_dim': text_cfg.get('head_dim'),
        'sliding_window': text_cfg.get('sliding_window'),
        'max_position_embeddings': text_cfg.get('max_position_embeddings'),
        'has_vision_config': 'vision_config' in cfg,
        'has_audio_config': 'audio_config' in cfg,
        'quant_method': (cfg.get('quantization_config') or {}).get('quant_method'),
    }
(RUN_DIR / 'model_configs.json').write_text(json.dumps(model_configs, indent=1))
print('model_configs:', json.dumps(model_configs, indent=1))

# %%
# ---------------------------------------------------------------- log capture helpers
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')
CAPACITY_LINE_RE = re.compile(r'(?i)kv.?cache|concurrency|blocks|GiB|memory|cuda graph|out of memory|divisible')

LOG_PATTERNS = {
    'max_concurrency': re.compile(r'Maximum concurrency for ([\d,]+) tokens per request:\s*([\d.]+)x'),
    'gpu_kv_cache_tokens': re.compile(r'GPU KV cache size:\s*([\d,]+) tokens'),
    'kv_avail_gib': re.compile(r'Available KV cache memory:\s*([\d.]+)\s*GiB'),
    'weights': re.compile(r'Model loading took\s*([\d.]+)\s*GiB(?: memory)? and\s*([\d.]+)\s*s'),
    'cudagraph': re.compile(r'Graph capturing finished in\s*([\d.]+)\s*secs?, took\s*([\d.]+)\s*GiB'),
    'init_engine_s': re.compile(r'init engine \(profile, create kv cache, warmup model\) took\s*([\d.]+)\s*seconds'),
    'vllm_version': re.compile(r'vLLM API server version\s*(\S+)'),
    'num_gpu_blocks': re.compile(r'#\s*GPU blocks:\s*(\d+)|num_gpu_blocks(?:\s*is)?[:=]\s*(\d+)'),
    'estimated_max_len': re.compile(r'estimated maximum model length is\s*(\d+)'),
}
FAILURE_PATTERNS = [
    ('env_error', re.compile(r'undefined symbol|ImportError|ModuleNotFoundError')),
    ('tp_incompatible', re.compile(r'is not divisible by|must be divisible by')),
    ('kv_too_small', re.compile(r'estimated maximum model length is\s*\d+')),
    ('oom', re.compile(r'CUDA out of memory|OutOfMemoryError')),
    ('insufficient_memory', re.compile(r'No available memory for the cache blocks|less than desired GPU memory utilization')),
]


def parse_log(text: str) -> dict:
    text = ANSI_RE.sub('', text)
    out: dict = {}
    m = LOG_PATTERNS['max_concurrency'].findall(text)
    if m:
        tokens = {int(t.replace(',', '')) for t, _ in m}
        out['concurrency_line_tokens'] = sorted(tokens)
        out['max_concurrency'] = min(float(x) for _, x in m)
    m = LOG_PATTERNS['gpu_kv_cache_tokens'].findall(text)
    if m:
        out['gpu_kv_cache_tokens'] = min(int(x.replace(',', '')) for x in m)
    m = LOG_PATTERNS['kv_avail_gib'].findall(text)
    if m:
        vals = [float(x) for x in m]
        out['kv_avail_gib_min'], out['kv_avail_gib_max'] = min(vals), max(vals)
        out['kv_avail_gib_total'] = sum(vals)
    m = LOG_PATTERNS['weights'].findall(text)
    if m:
        out['weights_gib_per_gpu'] = max(float(g) for g, _ in m)
        out['weights_gib_total'] = sum(float(g) for g, _ in m)
        out['load_s'] = max(float(s) for _, s in m)
    m = LOG_PATTERNS['cudagraph'].findall(text)
    if m:
        out['cudagraph_s'] = max(float(s) for s, _ in m)
        out['cudagraph_gib'] = max(float(g) for _, g in m)
    m = LOG_PATTERNS['init_engine_s'].findall(text)
    if m:
        out['init_engine_s'] = max(float(x) for x in m)
    m = LOG_PATTERNS['vllm_version'].search(text)
    if m:
        out['vllm_version_log'] = m.group(1)
    m = LOG_PATTERNS['num_gpu_blocks'].findall(text)
    if m:
        for a, b in m:
            if a or b:
                out['num_gpu_blocks'] = int(a or b)
                break
    m = LOG_PATTERNS['estimated_max_len'].search(text)
    if m:
        out['estimated_max_model_len'] = int(m.group(1))
    capacity_lines = [ln for ln in text.splitlines() if CAPACITY_LINE_RE.search(ln)]
    out['_capacity_lines'] = capacity_lines
    return out


def classify_failure(text: str) -> str:
    for status, pat in FAILURE_PATTERNS:
        if pat.search(text):
            return status
    return 'other_error'


class LogTee:
    """Copies a VllmServer's log file out continuously -- VllmServer.stop() unlinks it, even on success."""

    def __init__(self, server: VllmServer, dest: Path):
        self.server = server
        self.dest = dest
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._last_size = 0

    def _copy_once(self):
        path = getattr(self.server, 'log_path', None)
        if not path or not os.path.exists(path):
            return
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
        except Exception:  # noqa: BLE001
            return
        if len(text) >= self._last_size:
            self.dest.write_text(text)
            self._last_size = len(text)

    def _run(self):
        while not self._stop.is_set():
            self._copy_once()
            self._stop.wait(1.0)

    def start(self):
        self._thread.start()

    def stop_and_final_copy(self):
        self._stop.set()
        self._thread.join(timeout=5)
        self._copy_once()
        return self.dest.read_text() if self.dest.exists() else ''


def teardown(server: VllmServer | None, gpu_free_timeout_s: float = GPU_FREE_TIMEOUT_S) -> tuple[float, bool]:
    t0 = time.monotonic()
    if server is not None:
        try:
            server.stop(timeout=30)
        except Exception as exc:  # noqa: BLE001
            print('server.stop() raised (continuing with nvidia-smi sweep):', exc)
    # Orphaned TP-worker/EngineCore children spawned with multiprocessing method 'spawn' can outlive the
    # parent api_server process stop() terminates; sweep anything still holding a CUDA context.
    own_pid = os.getpid()
    for pid in _compute_app_pids():
        if pid == own_pid:
            continue
        try:
            os.kill(pid, 9)
        except ProcessLookupError:
            pass
        except Exception as exc:  # noqa: BLE001
            print(f'could not kill leftover compute pid {pid}:', exc)
    clean = False
    while time.monotonic() - t0 < gpu_free_timeout_s:
        used = _per_gpu_used_mib()
        if all(used.get(g, 0) <= BASELINE_USED_MIB.get(g, 0) + GPU_FREE_TOLERANCE_MIB for g in range(GPU_COUNT)):
            clean = True
            break
        time.sleep(2)
    return time.monotonic() - t0, clean


def http_get(url: str, timeout: float = 10.0) -> str | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception as exc:  # noqa: BLE001
        print(f'GET {url} failed:', exc)
        return None


def http_post_json(url: str, body: dict, timeout: float = 180.0) -> dict | None:
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as exc:  # noqa: BLE001
        print(f'POST {url} failed:', exc)
        return None

# %%
# ---------------------------------------------------------------- per-model probe loop
rows: list[dict] = []
jsonl_path = RUN_DIR / 'capacity.jsonl'


def append_row(row: dict):
    rows.append(row)
    with open(jsonl_path, 'a') as f:
        f.write(json.dumps(row) + '\n')


def make_server(model: str, port: int, util: float, max_model_len: int) -> VllmServer:
    cfg = VllmConfig(
        model=model_configs[model]['path'], port=port, host='127.0.0.1',
        tool_call_parser='gemma4', reasoning_parser='gemma4',
        max_model_len=max_model_len,
        dtype='bfloat16' if torch.cuda.is_bf16_supported() else 'auto',
        gpu_memory_utilization=util,
        enable_auto_tool_choice=True,
        enable_lora=False, max_loras=1, max_lora_rank=128,   # faithful: no adapters ship in our submission
        scheduler_reserve_full_isl=False,
        extra_args=list(MODEL_VLLM_EXTRA_ARGS.get(model, [])),
        startup_timeout=PER_MODEL_STARTUP_TIMEOUT_S.get(model, 600),
        tensor_parallel_size=4 if GPU_COUNT >= 4 else max(GPU_COUNT, 1),
    )
    return VllmServer(cfg)


def run_burst(base_url: str, model_id: str, label: str) -> dict:
    result: dict = {}
    try:
        http_post_json(f'{base_url}/chat/completions', {
            'model': model_id,
            'messages': [{'role': 'user', 'content': 'Count from 1 to 50 separated by spaces.'}],
            'max_tokens': 32, 'temperature': 0.0,
        }, timeout=60)  # warm-up, excluded from results
        records_by_n = {}
        for n in BURST_NS:
            def one_request(_i):
                body = {
                    'model': model_id,
                    'messages': [{'role': 'user', 'content': 'Count from 1 to 400 separated by spaces.'}],
                    'max_tokens': BURST_MAX_TOKENS, 'temperature': 0.0, 'min_tokens': BURST_MAX_TOKENS,
                }
                t0 = time.monotonic()
                out = http_post_json(f'{base_url}/chat/completions', body, timeout=180)
                t1 = time.monotonic()
                ct = (out or {}).get('usage', {}).get('completion_tokens', 0)
                return {'t_start': t0, 't_end': t1, 'completion_tokens': ct, 'ok': out is not None}
            with ThreadPoolExecutor(max_workers=n) as ex:
                recs = list(ex.map(one_request, range(n)))
            records_by_n[n] = recs
            (RUN_DIR / 'burst' / f'{label}.jsonl').open('a').write(
                json.dumps({'n': n, 'records': recs}) + '\n')
        n1 = records_by_n.get(1, [{}])[0]
        dt1 = max(n1.get('t_end', 0) - n1.get('t_start', 0), 1e-6)
        tok_s_n1 = n1.get('completion_tokens', 0) / dt1
        result['tok_s_n1'] = tok_s_n1
        for n in BURST_NS:
            if n == 1:
                continue
            recs = records_by_n.get(n, [])
            if not recs:
                continue
            total_tokens = sum(r.get('completion_tokens', 0) for r in recs)
            span = max(r['t_end'] for r in recs) - min(r['t_start'] for r in recs)
            agg = total_tokens / max(span, 1e-6)
            result[f'agg_tok_s_n{n}'] = agg
            result[f'speedup_n{n}'] = agg / tok_s_n1 if tok_s_n1 else None
    except Exception as exc:  # noqa: BLE001
        result['burst_error'] = str(exc)
    return result


def attempt(model: str, arm: str, attempt_no: int, util: float, max_model_len: int, port: int) -> dict:
    row = {
        'exp_id': EXP_ID, 'model': model, 'arm': arm, 'harness_faithful': (arm == 'faithful'),
        'attempt': attempt_no, 'tp': 4 if GPU_COUNT >= 4 else GPU_COUNT, 'gpu_mem_util': util,
        'max_model_len': max_model_len, 'model_path_resolved_by': model_configs[model].get('resolved_by'),
    }
    if model_configs[model].get('resolved_by') == 'missing':
        row['status'] = 'missing_input'
        return row

    server = make_server(model, port, util, max_model_len)
    cmd_evidence = {
        'recipe_argv': server.build_cmd(),
        'lora_flags_in_cmd': any('--enable-lora' in a or '--max-lora' in a for a in server.build_cmd()),
    }
    (RUN_DIR / 'cmd' / f'{model}_{arm}_a{attempt_no}.json').write_text(json.dumps(cmd_evidence, indent=1))
    row['lora_flags_in_cmd'] = cmd_evidence['lora_flags_in_cmd']
    row['extra_args'] = str(server.config.extra_args)

    log_dest = RUN_DIR / 'logs' / f'{model}_{arm}_a{attempt_no}.log'
    tee = LogTee(server, log_dest)
    tee.start()
    t_boot0 = time.monotonic()
    try:
        server.start()
        boot_s = time.monotonic() - t_boot0
        log_text = tee.stop_and_final_copy()
        parsed = parse_log(log_text)
        (RUN_DIR / 'logs' / f'{model}_{arm}_a{attempt_no}.capacity_lines.txt').write_text(
            '\n'.join(parsed.pop('_capacity_lines', [])))
        row.update({'status': 'ok', 'boot_s': round(boot_s, 1), **parsed})
        row['max_concurrency_32k'] = parsed.get('max_concurrency') if max_model_len == 32768 else None
        if max_model_len != 32768:
            row['implied_max_concurrency_at_len'] = parsed.get('max_concurrency')

        used = _per_gpu_used_mib()
        for g, v in used.items():
            row[f'nvsmi_used_mib_gpu{g}'] = v
        row['nvsmi_used_mib_total'] = sum(used.values())
        totals = _nvidia_smi_query('index,memory.total')
        row['nvsmi_total_mib_total'] = sum(int(float(r[1])) for r in totals)
        (RUN_DIR / 'nvidia_smi' / f'{model}_{arm}_after_boot.csv').write_text(
            '\n'.join(','.join(r) for r in _nvidia_smi_query('index,memory.used,memory.total')))

        models_resp = http_get(f'{server.base_url}/models')
        model_id = server.config.model
        if models_resp:
            try:
                data = json.loads(models_resp).get('data', [])
                if data:
                    model_id = data[0].get('id', model_id)
            except Exception:  # noqa: BLE001
                pass

        metrics_text = http_get(f'http://{server.config.host}:{server.config.port}/metrics')
        if metrics_text:
            (RUN_DIR / 'metrics' / f'{model}_{arm}.txt').write_text(metrics_text)

        if MEASURE_BATCH_SCALING and arm == 'faithful':
            row.update(run_burst(server.base_url, model_id, f'{model}_{arm}'))
    except ServerStartupError as exc:
        log_text = tee.stop_and_final_copy()
        combined = (log_text or '') + '\n' + (getattr(exc, 'output', '') or '')
        (RUN_DIR / 'logs' / f'{model}_{arm}_a{attempt_no}.exc_output.txt').write_text(combined)
        status = classify_failure(combined)
        parsed = parse_log(combined)
        row.update({'status': status, 'boot_s': round(time.monotonic() - t_boot0, 1), **parsed,
                    'error_tail': '\n'.join(combined.splitlines()[-40:])})
        if status == 'kv_too_small' and parsed.get('estimated_max_model_len'):
            row['implied_max_concurrency_32k'] = parsed['estimated_max_model_len'] / 32768
    except Exception as exc:  # noqa: BLE001
        log_text = tee.stop_and_final_copy()
        (RUN_DIR / 'logs' / f'{model}_{arm}_a{attempt_no}.exc_output.txt').write_text(log_text or str(exc))
        row.update({'status': classify_failure((log_text or '') + str(exc)),
                    'boot_s': round(time.monotonic() - t_boot0, 1), 'error_tail': str(exc)[-2000:]})
    finally:
        teardown_s, teardown_clean = teardown(server)
        row['teardown_s'] = round(teardown_s, 1)
        row['teardown_clean'] = teardown_clean
    return row


gpu_not_freed = False
for i, model in enumerate(MODELS):
    port = BASE_PORT + i
    elapsed = time.monotonic() - T0
    burst_cost_s = 90 if MEASURE_BATCH_SCALING else 0
    worst_case = elapsed + PER_MODEL_STARTUP_TIMEOUT_S.get(model, 600) + GPU_FREE_TIMEOUT_S + burst_cost_s
    if gpu_not_freed:
        append_row({'exp_id': EXP_ID, 'model': model, 'arm': 'faithful', 'attempt': 1,
                     'status': 'skipped_gpu_not_freed'})
        continue
    if elapsed > GLOBAL_SOFT_BUDGET_S:
        append_row({'exp_id': EXP_ID, 'model': model, 'arm': 'faithful', 'attempt': 1,
                     'status': 'skipped_time_budget'})
        continue
    if worst_case > GLOBAL_HARD_CAP_S:
        append_row({'exp_id': EXP_ID, 'model': model, 'arm': 'faithful', 'attempt': 1,
                     'status': 'skipped_time_budget'})
        continue

    row = attempt(model, 'faithful', 1, 0.90, 32768, port)
    append_row(row)
    print(f'[{model}] faithful attempt 1: status={row.get("status")} '
          f'boot_s={row.get("boot_s")} max_concurrency_32k={row.get("max_concurrency_32k")}')

    if row.get('status') == 'skipped_gpu_not_freed' or not row.get('teardown_clean', True):
        gpu_not_freed = True
        continue

    if row.get('status') != 'ok' and RETRY_ON_FAILURE:
        elapsed = time.monotonic() - T0
        worst_case = elapsed + PER_MODEL_STARTUP_TIMEOUT_S.get(model, 600) + GPU_FREE_TIMEOUT_S
        if worst_case <= GLOBAL_HARD_CAP_S:
            if row['status'] in ('oom', 'insufficient_memory'):
                retry_row = attempt(model, 'diagnostic_util_0.85', 1, DIAGNOSTIC_UTIL, 32768, port)
            elif row['status'] == 'kv_too_small':
                retry_row = attempt(model, 'diagnostic_len_16k', 1, 0.90, 16384, port)
            elif row['status'] in ('startup_timeout', 'other_error'):
                retry_row = attempt(model, 'faithful', 2, 0.90, 32768, port)
            else:
                retry_row = None
            if retry_row is not None:
                append_row(retry_row)
                print(f'[{model}] retry ({retry_row["arm"]}): status={retry_row.get("status")}')
                if not retry_row.get('teardown_clean', True):
                    gpu_not_freed = True
        if row['status'] == 'env_error':
            print('env_error on a real boot attempt -- aborting remaining models')
            break

# %%
# ---------------------------------------------------------------- table build + summary + bundle
import csv

all_cols: list[str] = []
seen = set()
for r in rows:
    for k in r.keys():
        if k not in seen:
            seen.add(k)
            all_cols.append(k)

with open(RUN_DIR / 'capacity.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=all_cols, extrasaction='ignore')
    w.writeheader()
    for r in rows:
        w.writerow(r)

# idle_kv_fraction_1agent_32k = 1 - 1/C : share of KV capacity unused with exactly one 32k-token request
# in flight (one agent, one task) -- real agent contexts are 5k-15k tokens, so the true idle share with
# one agent running is even higher than this conservative full-context figure.
for r in rows:
    c = r.get('max_concurrency_32k')
    if c is None:
        r['idle_kv_fraction_1agent_32k'] = None
    elif c < 1:
        r['idle_kv_fraction_1agent_32k'] = 'n/a (<1 full-length request fits)'
    else:
        r['idle_kv_fraction_1agent_32k'] = round(1 - 1 / c, 3)

faithful_by_model = {r['model']: r for r in rows if r.get('arm') == 'faithful' and r.get('attempt') == 1}
summary = {
    'install_s': env_report['install_s'],
    'total_wall_s': round(time.monotonic() - T0, 1),
    'per_model': {
        m: {
            'status': faithful_by_model.get(m, {}).get('status'),
            'max_concurrency_32k': faithful_by_model.get(m, {}).get('max_concurrency_32k'),
            'idle_kv_fraction_1agent_32k': faithful_by_model.get(m, {}).get('idle_kv_fraction_1agent_32k'),
            'boot_s': faithful_by_model.get(m, {}).get('boot_s'),
            'speedup_n4': faithful_by_model.get(m, {}).get('speedup_n4'),
        }
        for m in MODELS
    },
}
c31 = (faithful_by_model.get('gemma-4-31b-it-qat-w4a16-ct') or {}).get('max_concurrency_32k')
s31 = (faithful_by_model.get('gemma-4-31b-it-qat-w4a16-ct') or {}).get('speedup_n4')
if c31 is None:
    decision_hint = 'C_31B unmeasured (boot failed or skipped) -- investigate failure status before deciding'
elif c31 >= 4 and (not MEASURE_BATCH_SCALING or (s31 or 0) >= 2.0):
    decision_hint = 'proceed to EXP-007 ParallelAgent concurrency probe (N=2..4 branches)'
elif c31 < 2:
    decision_hint = 'close the intra-task parallelism line for 31B: no KV room for even 2 full-length concurrent requests'
else:
    decision_hint = 'EXP-007 should target N=2 branches only'
summary['decision_hint'] = decision_hint
(RUN_DIR / 'summary.json').write_text(json.dumps(summary, indent=1))
print('summary:', json.dumps(summary, indent=1))
print()
print(f'{"model":<32} {"status":<12} {"C@32k":>8} {"idle@1agent":>12} {"boot_s":>8} {"speedup_n4":>10}')
for m in MODELS:
    p = summary['per_model'][m]
    print(f'{m:<32} {str(p["status"]):<12} {str(p["max_concurrency_32k"]):>8} '
          f'{str(p["idle_kv_fraction_1agent_32k"]):>12} {str(p["boot_s"]):>8} {str(p["speedup_n4"]):>10}')

shutil.make_archive(str(Path('/kaggle/working/runs') / EXP_ID), 'zip', RUN_DIR)
print('bundled:', str(Path('/kaggle/working/runs') / EXP_ID) + '.zip')
