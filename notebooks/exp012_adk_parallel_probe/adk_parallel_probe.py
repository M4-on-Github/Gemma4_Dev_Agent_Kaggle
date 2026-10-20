# %% [markdown]
# # EXP-007: ADK `ParallelAgent` concurrency probe (31B only)
#
# Follow-up to EXP-006 (idle vLLM KV-cache capacity is real and large -- 88.6% idle for 31B under a
# single-request pattern). This experiment asks the next question: does ADK's `ParallelAgent` actually
# exploit that capacity for real agent work, or does it serialize anyway (event-loop handoff, sync tool
# calls run inline on the loop, a shared `max_llm_calls` budget)? Two stages:
#
# - **Stage 0** (no GPU, instant): a scripted fake `/v1/chat/completions` relay stands in for vLLM, so
#   every arm can be run and re-run cheaply to validate the harness (timing plugin, loop-lag monitor,
#   relay concurrency counter) before spending any GPU time.
# - **Stage 1** (real GPU, ~18-20 min): the same arms run against a real, harness-faithful 31B vLLM
#   server (`enable_lora=False`, TP=4, `max_model_len=32768`, `gpu_memory_utilization=0.90` -- same
#   recipe EXP-006 used).
#
# Hypotheses: H1 (`ParallelAgent` issues genuinely concurrent LLM requests -- relay sees >=2 in flight,
# wall time <= 0.75x sequential control), H2 (`AgentTool` sub-calls run concurrently; secondary -- E0
# traces show every tool-call step carries exactly one function call, so low real-world relevance), H3 (a
# long sync tool call in one branch stalls the sibling branch's progress -- loop-lag monitor + relay
# arrival timestamps), H4 (`RunConfig.max_llm_calls` is a shared budget across `ParallelAgent` branches,
# not per-branch).
#
# No `evaluate_task`, no `Evaluator`, no real submission, no task cohort, no LB interaction. All agents
# and tools here are synthetic, built only to exercise ADK's concurrency machinery.
#
# **Attach as inputs** (Add Input): competition `gemma-4-developer-agent`, dataset
# `metric/gemma-4-developer-agent-wheelhouse`, model `google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2`
# only. **Accelerator**: NVIDIA L4 x4. **Internet**: off.
#
# Build: `python tools/build_notebook.py --src notebooks/exp012_adk_parallel_probe/adk_parallel_probe.py --out notebooks/exp012_adk_parallel_probe/adk_parallel_probe.ipynb`
# Retrieve: `kaggle kernels output rainm4/gemma4-exp012-adk-parallel-probe -p runs/EXP-007-adk-parallel-probe`

# %%
# ---------------------------------------------------------------- parameters (edit me)
EXP_ID = "EXP-007-adk-parallel-probe"
MODEL_NAME = "gemma-4-31b-it-qat-w4a16-ct"
MODEL_ROOT = "/kaggle/input/models/google/gemma-4/other"
MODEL_VERSION = 2

RELAY_PORT = 8100
VLLM_PORT = 8000
STARTUP_TIMEOUT_S = 900

GLOBAL_SOFT_BUDGET_S = 25 * 60
GLOBAL_HARD_CAP_S = 40 * 60
GPU_FREE_TIMEOUT_S = 120
GPU_FREE_TOLERANCE_MIB = 1024

# Stage-0 fake relay: scripted per-request latency, long enough that a ThreadPoolExecutor-backed relay
# can show real overlap (and that a stalled event loop shows up as a visible gap) without burning wall
# time. Stage-1 real relay: vLLM is actually asked to think; no scripted delay is applied.
FAKE_LATENCY_S = 2.0
SLOW_TOOL_SECONDS = 3.0
MAX_LLM_CALLS_SHARED_TEST = 1  # H4: 1 shared call should let only 1 of 2 branches finish a turn

# %%
# ---------------------------------------------------------------- environment + wheelhouse (hosts' recipe, copied from EXP-006)
import asyncio, glob, importlib, importlib.metadata as im_md, json, os, re, shutil, subprocess, sys
import threading, time, urllib.request
from pathlib import Path

T0 = time.monotonic()

os.environ.update({
    'LITELLM_LOCAL_MODEL_COST_MAP': 'True', 'TRANSFORMERS_NO_TF': '1', 'VLLM_WORKER_MULTIPROC_METHOD': 'spawn',
    'VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS': '1', 'VLLM_ENGINE_READY_TIMEOUT_S': '1200',
    'VLLM_NO_USAGE_STATS': '1', 'OTEL_SDK_DISABLED': 'true', 'PYTORCH_CUDA_ALLOC_CONF': 'expandable_segments:True',
    'NCCL_DEBUG': 'WARN', 'TRANSFORMERS_OFFLINE': '1', 'VLLM_LOGGING_LEVEL': 'INFO',
})

RUN_DIR = Path('/kaggle/working/runs') / EXP_ID
for sub in ('logs', 'nvidia_smi', 'arms', 'cmd', 'relay'):
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

REQUIRED_PKGS = ('adk_submission', 'google.adk')


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
    (RUN_DIR / 'summary.json').write_text(json.dumps({'status': 'env_error', 'missing': missing}, indent=1))
    raise SystemExit('required packages unavailable: ' + '; '.join(missing))
print('required packages present:', ', '.join(REQUIRED_PKGS))

try:
    import torch
    import vllm  # noqa: F401
except Exception as _exc:  # noqa: BLE001
    (RUN_DIR / 'summary.json').write_text(json.dumps({'status': 'env_error', 'error': str(_exc)}, indent=1))
    raise SystemExit(f'vllm/torch import failed (env_error): {_exc}')

from adk_submission.server import VllmConfig, VllmServer
from adk_submission.errors import ServerStartupError
from adk_submission import ModelRegistry, ToolRegistry
from adk_submission.compiler import compile_submission
from adk_submission.limits import SubmissionLimits

from google.adk.apps import App
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents import RunConfig
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.models.lite_llm import LiteLlm
from google.genai import types as genai_types
import litellm
try:
    from adk_submission.resolvers.generation import install_litellm_reasoning_patch
    install_litellm_reasoning_patch()
except Exception as exc:  # noqa: BLE001
    print('reasoning patch not installed:', exc)
litellm.drop_params = True

GPU_COUNT = torch.cuda.device_count() if torch.cuda.is_available() else 0
print(f'GPU_COUNT={GPU_COUNT}')

# %%
# ---------------------------------------------------------------- shared helpers (log tee, teardown, nvidia-smi)


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


_ = torch.cuda.is_bf16_supported() if torch.cuda.is_available() else None
BASELINE_USED_MIB = _per_gpu_used_mib()


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

# %%
# ---------------------------------------------------------------- relay process (fake stage-0 / proxy stage-1)
#
# A tiny stdlib http.server running in a subprocess (so it has its own GIL/event loop -- it must stay
# responsive even while the main process's asyncio loop is doing other things). It serves
# /v1/chat/completions and /v1/models, and logs one JSON line per request to RELAY_LOG with
# {t_arrive, t_depart, in_flight_at_arrive} so we can measure real concurrency from the server side,
# independent of anything the client (ADK) claims about itself.
RELAY_SRC = r'''
import json, sys, threading, time, http.server, socketserver, urllib.request

MODE = sys.argv[1]            # "fake" or "proxy"
PORT = int(sys.argv[2])
LOG_PATH = sys.argv[3]
FAKE_LATENCY_S = float(sys.argv[4])
UPSTREAM_BASE = sys.argv[5] if len(sys.argv) > 5 else ""

_lock = threading.Lock()
_in_flight = 0
_log_fh = open(LOG_PATH, "a")


def log_event(rec):
    with _lock:
        _log_fh.write(json.dumps(rec) + "\n")
        _log_fh.flush()


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _reply(self, code, body: dict):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/v1/models"):
            self._reply(200, {"data": [{"id": "probe-model"}]})
        else:
            self._reply(404, {"error": "not found"})

    def do_POST(self):
        global _in_flight
        if not self.path.startswith("/v1/chat/completions"):
            self._reply(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        t_arrive = time.monotonic()
        with _lock:
            _in_flight += 1
            in_flight_at_arrive = _in_flight
        try:
            if MODE == "fake":
                time.sleep(FAKE_LATENCY_S)
                msgs = body.get("messages", [])

                def _as_text(content):
                    # OpenAI-compatible clients may send a plain string or a list of
                    # {"type": "text", "text": ...} parts -- handle both.
                    if isinstance(content, str):
                        return content
                    if isinstance(content, list):
                        return " ".join(
                            p.get("text", "") for p in content
                            if isinstance(p, dict) and p.get("type") == "text"
                        )
                    return ""

                last_user = next((_as_text(m.get("content")) for m in reversed(msgs) if m.get("role") == "user"), "")
                tool_calls = None
                content = None
                last_user_lower = last_user.lower()
                if "lookup_fact" in last_user_lower or "slow_sync_tool" in last_user_lower or "fact" in last_user_lower:
                    fn_name = "slow_sync_tool" if "slow" in last_user_lower else "lookup_fact"
                    already_called = any(
                        m.get("role") == "tool" for m in msgs
                    )
                    if already_called:
                        content = "done"
                    else:
                        tool_calls = [{
                            "id": "call_0", "type": "function",
                            "function": {"name": fn_name, "arguments": json.dumps({"key": "probe", "seconds": FAKE_LATENCY_S})},
                        }]
                else:
                    content = "ok"
                msg = {"role": "assistant", "content": content}
                if tool_calls:
                    msg["tool_calls"] = tool_calls
                resp = {
                    "id": "fake-0", "object": "chat.completion", "model": body.get("model", "probe-model"),
                    "choices": [{"index": 0, "message": msg, "finish_reason": "tool_calls" if tool_calls else "stop"}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                }
                self._reply(200, resp)
            else:
                req = urllib.request.Request(
                    UPSTREAM_BASE + "/chat/completions", data=json.dumps(body).encode(),
                    headers={"Content-Type": "application/json"}, method="POST",
                )
                with urllib.request.urlopen(req, timeout=180) as upstream_resp:
                    data = upstream_resp.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except Exception as exc:  # noqa: BLE001 -- never let a relay bug drop the connection silently
            try:
                self._reply(500, {"error": f"{exc.__class__.__name__}: {exc}"})
            except Exception:  # noqa: BLE001
                pass
        finally:
            t_depart = time.monotonic()
            with _lock:
                _in_flight -= 1
            log_event({"t_arrive": t_arrive, "t_depart": t_depart, "in_flight_at_arrive": in_flight_at_arrive})


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


if __name__ == "__main__":
    srv = ThreadingServer(("127.0.0.1", PORT), Handler)
    srv.serve_forever()
'''

RELAY_SCRIPT_PATH = RUN_DIR / 'relay' / 'relay_server.py'
RELAY_SCRIPT_PATH.write_text(RELAY_SRC)
RELAY_LOG_PATH = RUN_DIR / 'relay' / 'relay_log.jsonl'


class Relay:
    def __init__(self, mode: str, port: int, upstream_base: str = ''):
        self.mode = mode
        self.port = port
        self.upstream_base = upstream_base
        self.base_url = f'http://127.0.0.1:{port}/v1'
        self.proc = None
        RELAY_LOG_PATH.write_text('')

    def start(self):
        self.proc = subprocess.Popen(
            [sys.executable, str(RELAY_SCRIPT_PATH), self.mode, str(self.port), str(RELAY_LOG_PATH),
             str(FAKE_LATENCY_S), self.upstream_base if self.mode == 'proxy' else ''],
        )
        for _ in range(100):
            if http_get(f'{self.base_url}/models') is not None:
                return
            time.sleep(0.1)
        raise RuntimeError('relay did not become ready')

    def stop(self):
        if self.proc is not None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except Exception:  # noqa: BLE001
                self.proc.kill()

    def read_log(self) -> list[dict]:
        if not RELAY_LOG_PATH.exists():
            return []
        out = []
        for line in RELAY_LOG_PATH.read_text().splitlines():
            if line.strip():
                out.append(json.loads(line))
        return out


def make_relay(mode: str, port: int, upstream_base: str = '') -> Relay:
    return Relay(mode, port, upstream_base)

# %%
# ---------------------------------------------------------------- synthetic tools


def lookup_fact(key: str) -> str:
    return f'fact for {key}: 42'


def slow_sync_tool(seconds: float = SLOW_TOOL_SECONDS) -> str:
    """A plain sync function -- FunctionTool._invoke_callable calls this directly on the event loop
    (no thread pool), per google_adk/tools/function_tool.py:223-238. If this blocks the sibling
    ParallelAgent branch, that is H3 confirmed."""
    time.sleep(seconds)
    return f'slept {seconds}s'


TOOL_REGISTRY_DICT = {
    'lookup_fact': lookup_fact,
    'slow_sync_tool': slow_sync_tool,
}

# %%
# ---------------------------------------------------------------- timing/instrumentation plugin + loop-lag monitor


class ExpTimingPlugin(BasePlugin):
    def __init__(self, name: str = 'exp_timing_plugin'):
        super().__init__(name)
        self.events: list[dict] = []

    def _branch(self, ctx) -> str | None:
        return getattr(getattr(ctx, '_invocation_context', None), 'branch', None)

    async def before_model_callback(self, *, callback_context, llm_request):
        self.events.append({'t': time.monotonic(), 'kind': 'llm_call_start',
                             'branch': self._branch(callback_context), 'agent': callback_context.agent_name})
        return None

    async def after_model_callback(self, *, callback_context, llm_response):
        self.events.append({'t': time.monotonic(), 'kind': 'llm_call_end',
                             'branch': self._branch(callback_context), 'agent': callback_context.agent_name})
        return None

    async def before_tool_callback(self, *, tool, tool_args, tool_context):
        self.events.append({'t': time.monotonic(), 'kind': 'tool_call_start', 'tool': tool.name,
                             'branch': self._branch(tool_context), 'agent': tool_context.agent_name})
        return None

    async def after_tool_callback(self, *, tool, tool_args, tool_context, result):
        self.events.append({'t': time.monotonic(), 'kind': 'tool_call_end', 'tool': tool.name,
                             'branch': self._branch(tool_context), 'agent': tool_context.agent_name})
        return None


async def loop_lag_monitor(samples: list[dict], stop_event: threading.Event, interval_s: float = 0.05):
    """Measures event-loop responsiveness: schedules a wakeup `interval_s` out and records how late it
    actually fired. A sync tool call running inline on the loop (H3) shows up here as a lag spike."""
    while not stop_event.is_set():
        t_expected = time.monotonic() + interval_s
        await asyncio.sleep(interval_s)
        lag = time.monotonic() - t_expected
        samples.append({'t': time.monotonic(), 'lag_s': lag})

# %%
# ---------------------------------------------------------------- submission-YAML builders (schema-verified)
import yaml


def write_llm_agent(root: Path, rel_path: str, name: str, instruction: str, tools: list[str], model_alias: str):
    cfg = {
        'agent_class': 'LlmAgent',
        'name': name,
        'model': model_alias,
        'instruction': instruction,
        'tools': tools,
    }
    p = root / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(cfg, sort_keys=False))


def write_sequential_agent(root: Path, rel_path: str, name: str, sub_agent_paths: list[str]):
    cfg = {
        'agent_class': 'SequentialAgent',
        'name': name,
        'sub_agents': [{'config_path': p} for p in sub_agent_paths],
    }
    p = root / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(cfg, sort_keys=False))


def write_parallel_agent(root: Path, rel_path: str, name: str, sub_agent_paths: list[str]):
    cfg = {
        'agent_class': 'ParallelAgent',
        'name': name,
        'sub_agents': [{'config_path': p} for p in sub_agent_paths],
    }
    p = root / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(cfg, sort_keys=False))


def build_submission_dir(arm_name: str, model_alias: str, kind: str) -> Path:
    """kind: 'control_seq' | 'parallel' | 'parallel_sync_block'. Builds a tiny synthetic submission tree
    under RUN_DIR/arms/<arm_name>/ with a root.yaml plus analyzer_a.yaml/analyzer_b.yaml sub-agents."""
    root = RUN_DIR / 'arms' / arm_name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    a_tools = ['lookup_fact']
    b_tools = ['slow_sync_tool'] if kind == 'parallel_sync_block' else ['lookup_fact']

    write_llm_agent(root, 'analyzer_a.yaml', 'analyzer_a',
                     "Call the lookup_fact tool with key='A', then reply with exactly the tool's return value.",
                     a_tools, model_alias)
    write_llm_agent(root, 'analyzer_b.yaml', 'analyzer_b',
                     ("Call the slow_sync_tool tool, then reply with exactly the tool's return value."
                      if kind == 'parallel_sync_block' else
                      "Call the lookup_fact tool with key='B', then reply with exactly the tool's return value."),
                     b_tools, model_alias)

    if kind == 'control_seq':
        write_sequential_agent(root, 'agent.yaml', 'root_sequential', ['analyzer_a.yaml', 'analyzer_b.yaml'])
    else:
        write_parallel_agent(root, 'agent.yaml', 'root_parallel', ['analyzer_a.yaml', 'analyzer_b.yaml'])
    return root

# %%
# ---------------------------------------------------------------- arm runner


def run_sync(fn):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(lambda: asyncio.run(fn())).result()
    return asyncio.run(fn())


def run_arm(arm_id: str, kind: str, relay_base_url: str, model_id_on_relay: str, max_llm_calls: int) -> dict:
    root = build_submission_dir(arm_id, 'probe_model', kind)
    models = ModelRegistry()
    models.register('probe_model', LiteLlm(model=f'openai/{model_id_on_relay}', api_base=relay_base_url, api_key='EMPTY'))
    tools = ToolRegistry()
    for name, fn in TOOL_REGISTRY_DICT.items():
        tools.register(name, fn)

    root_agent = compile_submission(root, tool_registry=tools, model_registry=models,
                                     limits=SubmissionLimits(), generation_constraints=None)
    plugin = ExpTimingPlugin()
    app = App(name=arm_id.replace('-', '_'), root_agent=root_agent, plugins=[plugin])
    session_service = InMemorySessionService()

    lag_samples: list[dict] = []
    stop_event = threading.Event()

    async def drive():
        session = await session_service.create_session(app_name=app.name, user_id='probe_user')
        runner = Runner(app=app, session_service=session_service)
        lag_task = asyncio.create_task(loop_lag_monitor(lag_samples, stop_event))
        t_start = time.monotonic()
        try:
            async for _event in runner.run_async(
                user_id='probe_user', session_id=session.id,
                new_message=genai_types.Content(role='user', parts=[genai_types.Part.from_text(text='go')]),
                run_config=RunConfig(max_llm_calls=max_llm_calls),
            ):
                pass
        finally:
            stop_event.set()
            lag_task.cancel()
        return time.monotonic() - t_start

    wall_s = run_sync(drive)
    return {
        'arm_id': arm_id, 'kind': kind, 'wall_s': round(wall_s, 3),
        'events': plugin.events,
        'max_lag_s': max((s['lag_s'] for s in lag_samples), default=None),
        'lag_samples_n': len(lag_samples),
    }

# %%
# ---------------------------------------------------------------- Stage 0: fake relay (no GPU)
stage0_rows: list[dict] = []
relay0 = make_relay('fake', RELAY_PORT)
relay0.start()
try:
    for arm_id, kind, max_calls in [
        ('s0-control-seq', 'control_seq', 10),
        ('s0-parallel', 'parallel', 10),
        ('s0-parallel-sync-block', 'parallel_sync_block', 10),
        ('s0-shared-budget', 'parallel', MAX_LLM_CALLS_SHARED_TEST),
    ]:
        before_n = len(relay0.read_log())
        try:
            row = run_arm(arm_id, kind, relay0.base_url, 'probe-model', max_calls)
            after_log = relay0.read_log()
            relay_rows = after_log[before_n:]
            row['relay_max_in_flight'] = max((r['in_flight_at_arrive'] for r in relay_rows), default=None)
            row['relay_n_requests'] = len(relay_rows)
            row['status'] = 'ok'
            print(f'[stage0] {arm_id}: wall_s={row["wall_s"]} relay_max_in_flight={row["relay_max_in_flight"]} '
                  f'relay_n_requests={row["relay_n_requests"]} max_lag_s={row["max_lag_s"]}')
        except Exception as exc:  # noqa: BLE001 -- one bad arm must not abort the rest of the probe
            row = {'arm_id': arm_id, 'kind': kind, 'status': 'error', 'error': f'{exc.__class__.__name__}: {exc}'}
            print(f'[stage0] {arm_id}: ERROR {row["error"]}')
        stage0_rows.append(row)
        (RUN_DIR / 'arms' / f'{arm_id}.json').write_text(json.dumps(row, indent=1, default=str))
finally:
    relay0.stop()

(RUN_DIR / 'stage0.json').write_text(json.dumps(stage0_rows, indent=1, default=str))

# %%
# ---------------------------------------------------------------- Stage 1: real 31B vLLM
stage1_rows: list[dict] = []
stage1_skipped_reason = None

exact = Path(MODEL_ROOT) / MODEL_NAME / str(MODEL_VERSION)
model_path = exact
if not (model_path / 'config.json').exists():
    hits = list(Path('/kaggle/input').glob(f'**/{MODEL_NAME}/**/config.json'))
    model_path = hits[0].parent if hits else exact

elapsed = time.monotonic() - T0
if elapsed > GLOBAL_SOFT_BUDGET_S:
    stage1_skipped_reason = 'soft_budget_exceeded_before_boot'
elif not (model_path / 'config.json').exists():
    stage1_skipped_reason = 'model_input_missing'

server = None
vllm_log_tee = None
if stage1_skipped_reason is None:
    cfg = VllmConfig(
        model=str(model_path), port=VLLM_PORT, host='127.0.0.1',
        tool_call_parser='gemma4', reasoning_parser='gemma4', max_model_len=32768,
        dtype='bfloat16' if torch.cuda.is_bf16_supported() else 'auto',
        gpu_memory_utilization=0.90, enable_auto_tool_choice=True,
        enable_lora=False, max_loras=1, max_lora_rank=128,
        scheduler_reserve_full_isl=False, extra_args=[], startup_timeout=STARTUP_TIMEOUT_S,
        tensor_parallel_size=4 if GPU_COUNT >= 4 else max(GPU_COUNT, 1),
    )
    server = VllmServer(cfg)
    (RUN_DIR / 'cmd' / 'vllm_31b.json').write_text(json.dumps({'recipe_argv': server.build_cmd()}, indent=1))
    log_dest = RUN_DIR / 'logs' / 'vllm_31b.log'
    vllm_log_tee = LogTee(server, log_dest)
    vllm_log_tee.start()
    t_boot0 = time.monotonic()
    try:
        server.start()
        boot_s = time.monotonic() - t_boot0
        print(f'vLLM 31B booted in {boot_s:.1f}s')
        model_id = server.config.model
        models_resp = http_get(f'{server.base_url}/models')
        if models_resp:
            try:
                data = json.loads(models_resp).get('data', [])
                if data:
                    model_id = data[0].get('id', model_id)
            except Exception:  # noqa: BLE001
                pass

        relay1 = make_relay('proxy', RELAY_PORT, upstream_base=server.base_url)
        relay1.start()
        try:
            for arm_id, kind in [
                ('s1-control-seq', 'control_seq'),
                ('s1-parallel', 'parallel'),
                ('s1-parallel-sync-block', 'parallel_sync_block'),
            ]:
                worst_case = (time.monotonic() - T0) + 180
                if worst_case > GLOBAL_HARD_CAP_S:
                    print(f'[stage1] skipping {arm_id}: hard cap would be exceeded')
                    stage1_rows.append({'arm_id': arm_id, 'kind': kind, 'status': 'skipped_time_budget'})
                    continue
                before_n = len(relay1.read_log())
                try:
                    row = run_arm(arm_id, kind, relay1.base_url, model_id, 10)
                    after_log = relay1.read_log()
                    relay_rows = after_log[before_n:]
                    row['relay_max_in_flight'] = max((r['in_flight_at_arrive'] for r in relay_rows), default=None)
                    row['relay_n_requests'] = len(relay_rows)
                    row['status'] = 'ok'
                    print(f'[stage1] {arm_id}: wall_s={row["wall_s"]} relay_max_in_flight={row["relay_max_in_flight"]} '
                          f'relay_n_requests={row["relay_n_requests"]} max_lag_s={row["max_lag_s"]}')
                except Exception as exc:  # noqa: BLE001 -- one bad arm must not waste the already-booted GPU
                    row = {'arm_id': arm_id, 'kind': kind, 'status': 'error', 'error': f'{exc.__class__.__name__}: {exc}'}
                    print(f'[stage1] {arm_id}: ERROR {row["error"]}')
                stage1_rows.append(row)
                (RUN_DIR / 'arms' / f'{arm_id}.json').write_text(json.dumps(row, indent=1, default=str))
        finally:
            relay1.stop()
    except ServerStartupError as exc:
        stage1_skipped_reason = f'vllm_boot_failed: {exc}'
        print('vLLM boot failed:', exc)
    except Exception as exc:  # noqa: BLE001
        stage1_skipped_reason = f'vllm_or_arm_error: {exc}'
        print('stage1 error:', exc)
    finally:
        if vllm_log_tee is not None:
            vllm_log_tee.stop_and_final_copy()
        teardown_s, teardown_clean = teardown(server)
        print(f'teardown_s={teardown_s:.1f} teardown_clean={teardown_clean}')

(RUN_DIR / 'stage1.json').write_text(json.dumps(
    {'skipped_reason': stage1_skipped_reason, 'rows': stage1_rows}, indent=1, default=str))

# %%
# ---------------------------------------------------------------- decision rule


def wall_ratio(rows: list[dict]) -> float | None:
    by_kind = {r.get('kind'): r for r in rows if r.get('status', 'ok') == 'ok'}
    seq = by_kind.get('control_seq')
    par = by_kind.get('parallel')
    if not seq or not par or not seq.get('wall_s') or not par.get('wall_s'):
        return None
    return par['wall_s'] / seq['wall_s']


def max_in_flight(rows: list[dict], kind: str) -> int | None:
    for r in rows:
        if r.get('kind') == kind:
            return r.get('relay_max_in_flight')
    return None


summary = {
    'total_wall_s': round(time.monotonic() - T0, 1),
    'stage0': {
        'wall_ratio_parallel_over_control': wall_ratio(stage0_rows),
        'max_in_flight_parallel': max_in_flight(stage0_rows, 'parallel'),
    },
    'stage1': {
        'skipped_reason': stage1_skipped_reason,
        'wall_ratio_parallel_over_control': wall_ratio(stage1_rows) if not stage1_skipped_reason else None,
        'max_in_flight_parallel': max_in_flight(stage1_rows, 'parallel') if not stage1_skipped_reason else None,
    },
}

h1_pass_stage1 = (summary['stage1']['max_in_flight_parallel'] or 0) >= 2 and \
    (summary['stage1']['wall_ratio_parallel_over_control'] or 1.0) <= 0.75
sync_block_row1 = next((r for r in stage1_rows if r.get('kind') == 'parallel_sync_block'), None)
parallel_row1 = next((r for r in stage1_rows if r.get('kind') == 'parallel'), None)
h3_stall_frac = None
if sync_block_row1 and parallel_row1 and parallel_row1.get('wall_s'):
    h3_stall_frac = max(0.0, (sync_block_row1.get('wall_s', 0) - parallel_row1['wall_s']) / parallel_row1['wall_s'])
summary['h3_projected_stall_frac'] = h3_stall_frac

if stage1_skipped_reason:
    decision_hint = f'stage1 skipped ({stage1_skipped_reason}) -- use stage0 fake-relay results only, re-run stage1 before deciding'
elif not h1_pass_stage1:
    decision_hint = 'H1 REFUTED on real 31B -- close the ParallelAgent concurrency line, do not pursue EXP-008'
elif h3_stall_frac is not None and h3_stall_frac <= 0.10:
    decision_hint = 'H1 PASS, H3 cost small -- proceed to EXP-008 (SequentialAgent[ParallelAgent[analyzer_A, analyzer_B], swe_coder] vs E0 on dev-48)'
else:
    decision_hint = 'H1 PASS but H3 (sync-tool stall) cost is significant -- proceed to EXP-008 only if swegemma tools are made async first'
summary['decision_hint'] = decision_hint
(RUN_DIR / 'summary.json').write_text(json.dumps(summary, indent=1, default=str))
print('summary:', json.dumps(summary, indent=1, default=str))

shutil.make_archive(str(Path('/kaggle/working/runs') / EXP_ID), 'zip', RUN_DIR)
print('bundled:', str(Path('/kaggle/working/runs') / EXP_ID) + '.zip')
