# %% [markdown]
# # Gemma 4 Developer Agent — Phase 0 checks, EXP-000 gold control, baseline eval (4x L4)
#
# One notebook, three switches (`RUN_PHASE0_CHECKS`, `RUN_GOLD_CONTROL`, `RUN_AGENT`). It mirrors the
# organizers' Getting-Started recipe (wheelhouse install, `VllmServer`, `swegemma.evaluate.Evaluator` with the
# subprocess sandbox) and writes everything under `/kaggle/working/runs/<EXP_ID>/` in the layout that
# `tools/analyze_traces.py` and `tools/estimate_budget.py` read.
#
# **Attach as inputs** (Add Input): competition `gemma-4-developer-agent`, dataset
# `metric/gemma-4-developer-agent-wheelhouse`, model `google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2`.
# **Accelerator**: NVIDIA L4 x4 (competition-attached notebooks only). **Internet**: off.
# The submission zip comes either from a private Kaggle dataset you upload (`SUBMISSION_ZIP`) or embedded as
# base64 by `python tools/build_notebook.py --embed dist/submission.zip`.
#
# **Status: UNTESTED on Kaggle.** This file was written without access to kaggle.com, the wheelhouse or the
# harness source. Cells marked `# VERIFY` use API names taken from a community mirror of the starter notebook
# and may need adjusting against the real `getting-started-gemma-4-developer-agent` notebook. Read the
# starter notebook first and diff the server/evaluator cells.
#
# Edit the parameters in the next cell, save a notebook *version* per experiment, then download
# `/kaggle/working/runs/<EXP_ID>.zip` and run `python tools/analyze_traces.py runs/<EXP_ID>`.

# %%
# ---------------------------------------------------------------- parameters (edit me)
EXP_ID = "EXP-001-baseline"
RUN_PHASE0_CHECKS = True          # Q1/Q2/Q3/Q7/Q9 answers + HARNESS_README copy + sample_submission dump
RUN_GOLD_CONTROL = True           # EXP-000: grade each candidate task with its reference patch (no model)
RUN_AGENT = True                  # run our submission on the sound tasks
MEASURE_DECODE_SPEED = True       # Q10: one timed completion against the server

# Task selection: explicit ids win; otherwise the first N_TASKS of the (optionally repo-filtered) dataset.
TASK_IDS = []                     # e.g. ids pasted from experiments/cohorts/smoke-8.txt
N_TASKS = 8
REPO_FILTER = ""                  # e.g. "Textualize/rich"; "" = all repos
EXCLUDE_IDS = []                  # known-unsound tasks from a previous gold control (experiments/README.md Q5)

# Where the submission comes from (first that exists wins). Upload dist/submission.zip as a private dataset,
# or embed it: python tools/build_notebook.py --embed dist/submission.zip
SUBMISSION_ZIP = "/kaggle/input/datasets/YOUR_KAGGLE_USERNAME/gemma4-sub-v1/submission.zip"   # VERIFY path
SUBMISSION_B64 = ""               # filled in by tools/build_notebook.py --embed

# Compaction settings: HARNESS_README says interval 5; the hosts' notebook mirror used 15 (plan Q7).
COMPACTION_INTERVAL = 5
COMPACTION_TOKEN_THRESHOLD = 14336

# %%
# ---------------------------------------------------------------- environment + wheelhouse (hosts' recipe)
# Adapted from the organizers' Getting-Started notebook as mirrored by community repos.  # VERIFY
import glob, importlib, json, os, shutil, subprocess, sys, time, zipfile, io, base64
from pathlib import Path

os.environ.update({
    'LITELLM_LOCAL_MODEL_COST_MAP': 'True', 'TRANSFORMERS_NO_TF': '1', 'VLLM_WORKER_MULTIPROC_METHOD': 'spawn',
    'VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS': '1', 'VLLM_ENGINE_READY_TIMEOUT_S': '1200',
    'VLLM_NO_USAGE_STATS': '1', 'OTEL_SDK_DISABLED': 'true', 'PYTORCH_CUDA_ALLOC_CONF': 'expandable_segments:True',
})
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
T_INSTALL = time.time()
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--no-deps', '--force-reinstall',
                *sorted(str(w) for w in tmp_whl.glob('*.whl'))], check=True)
importlib.invalidate_caches()
print(f'wheelhouse installed in {time.time() - T_INSTALL:.0f}s')

DATA_DIR = next(Path(p) for p in ['/kaggle/input/competitions/gemma-4-developer-agent',
                                  '/kaggle/input/gemma-4-developer-agent'] if Path(p).exists())
RUN_DIR = Path('/kaggle/working/runs') / EXP_ID
for sub in ('traces', 'patches', 'logs', 'phase0'):
    (RUN_DIR / sub).mkdir(parents=True, exist_ok=True)
print('data:', DATA_DIR, ' run dir:', RUN_DIR)

# %%
# ---------------------------------------------------------------- Phase 0 checks (plan §3.4)
# Answers Q1/Q2/Q3/Q7/Q9 by reading the installed harness source; saves HARNESS_README.md and
# sample_submission/ to the run dir so they can be downloaded and read offline.
if RUN_PHASE0_CHECKS:
    import importlib.metadata as md, re
    report = {'python': sys.version, 'packages': {}}
    for pkg in ('swegemma', 'adk-submission', 'adk-eval-core', 'google-adk', 'vllm', 'litellm'):
        try:
            report['packages'][pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            report['packages'][pkg] = None
    for name in ('HARNESS_README.md',):
        src = DATA_DIR / name
        if src.exists():
            shutil.copy(src, RUN_DIR / 'phase0' / name)
    ss = DATA_DIR / 'sample_submission'
    if ss.exists():
        shutil.copytree(ss, RUN_DIR / 'phase0' / 'sample_submission', dirs_exist_ok=True)
        print('--- sample_submission files (Q2) ---')
        for p in sorted(ss.rglob('*')):
            if p.is_file() and p.suffix in ('.yaml', '.yml', '.md', '.txt', '.json'):
                print(f'===== {p.relative_to(ss)}'); print(p.read_text()[:4000])

    def grep_pkg(pkg: str, patterns: list[str]) -> dict:
        hits = {}
        try:
            root = Path(importlib.import_module(pkg).__file__).parent
        except Exception as exc:  # noqa: BLE001
            return {'error': str(exc)}
        for pat in patterns:
            rx = re.compile(pat)
            for f in root.rglob('*.py'):
                for i, line in enumerate(f.read_text(errors='ignore').splitlines(), 1):
                    if rx.search(line):
                        hits.setdefault(pat, []).append(f'{f.relative_to(root)}:{i}: {line.strip()[:160]}')
        return hits

    report['Q1_tool_registry'] = grep_pkg('swegemma', [r'register\(', r'def (run_command|read_file|edit_file|write_file|get_status|submit_patch|get_code_neighbors|search_similar_code|get_code_subgraph)\b'])
    report['Q1_skill_tools'] = grep_pkg('adk_submission', [r'run_skill_script|load_skill_resource|SkillToolset'])
    report['Q2_eval_config_keys'] = grep_pkg('swegemma', [r'max_time_minutes|max_tool_calls|max_turns|timeout_seconds', r'load_submission_eval_config'])
    report['Q2_agent_tool_schema'] = grep_pkg('adk_submission', [r'agent_tool|config_path|skip_summarization'])
    report['Q3_thinking_forwarding'] = grep_pkg('adk_submission', [r'thinking_budget|thinking_token_budget|enable_thinking|include_thoughts'])
    report['Q7_compaction'] = grep_pkg('swegemma', [r'compaction_interval|token_threshold|EventsCompactionConfig'])
    report['Q9_extensions_limits'] = grep_pkg('swegemma', [r'ALLOWED_SUBMISSION_EXTENSIONS|MAX_SUBMISSION_SIZE_BYTES|allowed_file_extensions|max_total_size_bytes'])
    report['Q2_grading_timeout'] = grep_pkg('swegemma', [r'timeout', ]) if False else grep_pkg('swegemma', [r'verification.*timeout|timeout.*verif|command_timeout_seconds'])
    (RUN_DIR / 'phase0' / 'phase0_report.json').write_text(json.dumps(report, indent=1))
    print(json.dumps({k: (v if k == 'packages' else {kk: len(vv) for kk, vv in v.items()} if isinstance(v, dict) else v)
                      for k, v in report.items()}, indent=1))
    print('full grep hits saved to', RUN_DIR / 'phase0' / 'phase0_report.json')

# %%
# ---------------------------------------------------------------- tasks + candidates
from swegemma.models import load_tasks  # VERIFY import path
TASKS_PATH = DATA_DIR / 'tasks.jsonl'
all_tasks = load_tasks(TASKS_PATH)
from collections import Counter
print('repo counts:', Counter(t.repo for t in all_tasks))
if TASK_IDS:
    want = set(TASK_IDS)
    candidates = [t for t in all_tasks if t.instance_id in want]
else:
    pool = [t for t in all_tasks if (not REPO_FILTER or t.repo == REPO_FILTER) and t.instance_id not in set(EXCLUDE_IDS)]
    candidates = sorted(pool, key=lambda t: t.instance_id)[:N_TASKS]
print(f'{len(all_tasks)} tasks; candidates ({len(candidates)}):', [t.instance_id for t in candidates])

# %%
# ---------------------------------------------------------------- unpack our submission
AGENT_DIR = Path('/kaggle/working/agent')
shutil.rmtree(AGENT_DIR, ignore_errors=True); AGENT_DIR.mkdir(parents=True)
if SUBMISSION_B64:
    zipfile.ZipFile(io.BytesIO(base64.b64decode(SUBMISSION_B64))).extractall(AGENT_DIR)
elif Path(SUBMISSION_ZIP).exists():
    zipfile.ZipFile(SUBMISSION_ZIP).extractall(AGENT_DIR)
else:
    raise SystemExit('no submission: set SUBMISSION_ZIP to your uploaded dataset file or embed with tools/build_notebook.py')
print('agent files:', sorted(str(p.relative_to(AGENT_DIR)) for p in AGENT_DIR.rglob('*') if p.is_file()))
import yaml
EVAL = (yaml.safe_load((AGENT_DIR / 'eval_config.yaml').read_text()) or {}).get('evaluation', {}) \
    if (AGENT_DIR / 'eval_config.yaml').exists() else {}
print('eval_config:', EVAL)

# %%
# ---------------------------------------------------------------- vLLM server (hosts' recipe)  # VERIFY
import litellm, torch
from adk_submission import ModelRegistry, VllmConfig, VllmServer, discover_adapters
from google.adk.models.lite_llm import LiteLlm
from swegemma.config import ALLOWED_ADAPTER_EXTENSIONS, EvalConfig, build_submission_limits
from swegemma.models.discovery import validate_single_declared_model
try:
    from adk_submission.resolvers.generation import install_litellm_reasoning_patch
    install_litellm_reasoning_patch()
except Exception as exc:  # noqa: BLE001
    print('reasoning patch not installed:', exc)
litellm.drop_params = True

TARGET = 'gemma-4-31b-it-qat-w4a16-ct'
MODEL_DIR = '/kaggle/input/models/google/gemma-4/other/gemma-4-31b-it-qat-w4a16-ct/2'
declared = validate_single_declared_model(AGENT_DIR)
assert str(declared).endswith(TARGET), declared
adapters = discover_adapters(str(AGENT_DIR), adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
assert gpu_count >= 1, 'no GPU: select the L4 x4 accelerator'
tp = 4 if gpu_count >= 4 else (2 if gpu_count >= 2 else 1)
t0 = time.time()
server = VllmServer(VllmConfig(
    model=MODEL_DIR, port=8000, host='127.0.0.1', tool_call_parser='gemma4', reasoning_parser='gemma4',
    default_chat_template_kwargs={'enable_thinking': True}, max_model_len=32768,
    dtype='bfloat16' if torch.cuda.is_bf16_supported() else 'auto', gpu_memory_utilization=0.90,
    enable_auto_tool_choice=True, enable_lora=True, max_loras=8, max_lora_rank=128,
    tensor_parallel_size=tp, startup_timeout=60 * 20), adapter_manifest=adapters)
server.start()
SERVER_START_S = round(time.time() - t0, 1)
print(f'vLLM up in {SERVER_START_S}s (tp={tp}, gpus={gpu_count}) at {server.base_url}')
target_id = getattr(server, 'effective_model_path', MODEL_DIR)
models = ModelRegistry()
for alias in {declared, TARGET}:
    models.register(alias, LiteLlm(model=f'openai/{target_id}', api_base=server.base_url, api_key='EMPTY'))

# %%
# ---------------------------------------------------------------- Q10: decode speed probe
DECODE = None
if MEASURE_DECODE_SPEED:
    import urllib.request
    body = json.dumps({'model': target_id, 'messages': [{'role': 'user', 'content': 'Count from 1 to 400 separated by spaces.'}],
                       'max_tokens': 400, 'temperature': 0.0, 'chat_template_kwargs': {'enable_thinking': False}}).encode()
    req = urllib.request.Request(server.base_url.rstrip('/') + '/chat/completions', data=body,
                                 headers={'Content-Type': 'application/json'}, method='POST')
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=600) as resp:
        out = json.loads(resp.read())
    dt = time.time() - t0
    ct = out.get('usage', {}).get('completion_tokens', 0)
    DECODE = {'completion_tokens': ct, 'seconds': round(dt, 2), 'tok_s': round(ct / dt, 1) if dt else None}
    print('decode probe:', DECODE)

# %%
# ---------------------------------------------------------------- evaluator helpers
import asyncio, concurrent.futures
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.apps._configs import EventsCompactionConfig  # VERIFY import path (hosts' notebook mirror)
from swegemma.evaluate import Evaluator

def run_sync(fn):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(lambda: asyncio.run(fn())).result()
    return asyncio.run(fn())

def make_config(results_dir: Path) -> EvalConfig:
    limits, gen = build_submission_limits()
    return EvalConfig(
        tasks_path=TASKS_PATH, snapshots_dir=DATA_DIR / 'snapshots', results_dir=results_dir,
        submission_dir=AGENT_DIR, models=models, sandbox='subprocess',
        timeout_seconds=int(EVAL.get('timeout_seconds', 300)),
        max_time_minutes=float(EVAL.get('max_time_minutes', 60.0)),
        max_tool_calls=int(EVAL.get('max_tool_calls', 100)),
        max_turns=int(EVAL['max_turns']) if EVAL.get('max_turns') is not None else None,
        limits=limits, generation_constraints=gen, adapter_manifest=adapters,
        context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=1800, cache_intervals=10),
        events_compaction_config=EventsCompactionConfig(compaction_interval=COMPACTION_INTERVAL, overlap_size=2,
                                                        token_threshold=COMPACTION_TOKEN_THRESHOLD, event_retention_size=5),
        graph_dir=str(DATA_DIR / 'graphs'), embeddings_dir=str(DATA_DIR / 'embeddings'),
        wheels_dir=DATA_DIR / 'wheels', verbose=False)

def record(r, task, t_start: float, t_end: float) -> dict:
    patch = r.agent_patch or ''
    dur = float(r.duration_seconds or 0)
    wall = t_end - t_start
    return {'instance_id': task.instance_id, 'repo': task.repo, 'resolved': bool(r.resolved),
            'status': getattr(r, 'status', None), 'test_exit_code': r.test_exit_code,
            'duration_s': round(dur, 1), 'task_wall_s': round(wall, 1),
            'setup_s': round(max(0.0, wall - dur), 1),   # everything outside the agent loop (setup + grading)  VERIFY
            'tool_calls': getattr(r, 'tool_calls', None), 'llm_calls': getattr(r, 'total_llm_calls', None),
            'total_tokens': getattr(r, 'total_tokens', None), 'error': getattr(r, 'error', None) or getattr(r, 'error_message', None),
            'patch_chars': len(patch), 'patch': patch, 'trace': str(getattr(r, 'trace_path', '') or getattr(r, 'trace_json_path', '') or ''),
            'test_tail': (r.test_output or '')[-1500:], 'max_time_minutes': EVAL.get('max_time_minutes'),
            'max_tool_calls': EVAL.get('max_tool_calls')}

def append_row(path: Path, row: dict) -> None:
    with path.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(row) + '\n')

# %%
# ---------------------------------------------------------------- EXP-000 gold control (Q5)
sound = list(candidates)
if RUN_GOLD_CONTROL:
    from adk_eval_core.tracing import SessionTrace  # VERIFY import path

    class GoldEvaluator(Evaluator):
        """Phase 1 returns the reference patch; no model call, nothing is shown to any agent."""
        async def _run_agent_sandbox(self, task, *args, **kwargs):  # VERIFY method name/signature
            return task.patch, None, SessionTrace()

    gold = GoldEvaluator(make_config(RUN_DIR / 'gold_control'))
    gold_rows = []
    for i, t in enumerate(candidates, 1):
        t0 = time.time()
        r = run_sync(lambda: gold.evaluate_task(task=t, task_index=i, total_tasks=len(candidates)))
        row = {'instance_id': t.instance_id, 'repo': t.repo, 'mode': 'gold', 'resolved': bool(r.resolved),
               'exit': r.test_exit_code, 'seconds': round(time.time() - t0, 1), 'error': (getattr(r, 'error', '') or '')[:300],
               'tail': (r.test_output or '')[-600:]}
        gold_rows.append(row)
        append_row(RUN_DIR / 'gold_control.jsonl', row)
        print('gold', t.instance_id, 'resolved=', row['resolved'], f"{row['seconds']}s")
    failures = [x['instance_id'] for x in gold_rows if not x['resolved']]
    (RUN_DIR / 'gold_failures.txt').write_text('# gold-control failures (exclude from cohorts)\n' + '\n'.join(failures) + '\n')
    sound = [t for t, x in zip(candidates, gold_rows) if x['resolved']]
    print(f'gold control: {len(sound)}/{len(candidates)} sound; failures: {failures}')

# %%
# ---------------------------------------------------------------- baseline agent eval
summary = {'exp_id': EXP_ID, 'server_start_s': SERVER_START_S, 'decode_probe': DECODE, 'eval_config': EVAL,
           'compaction': {'interval': COMPACTION_INTERVAL, 'token_threshold': COMPACTION_TOKEN_THRESHOLD},
           'tasks': [], 'resolved': 0}
if RUN_AGENT:
    ev = Evaluator(make_config(RUN_DIR / 'official'))
    for i, t in enumerate(sound, 1):
        t0 = time.time()
        r = run_sync(lambda: ev.evaluate_task(task=t, task_index=i, total_tasks=len(sound)))
        row = record(r, t, t0, time.time())
        append_row(RUN_DIR / 'task_results.jsonl', row)
        (RUN_DIR / 'patches' / f'{t.instance_id}.patch').write_text(row['patch'])
        for cand in (Path(row['trace']) if row['trace'] else None, RUN_DIR / 'official' / 'traces' / f'trace_{t.instance_id}.json'):
            if cand and cand.exists():
                shutil.copy(cand, RUN_DIR / 'traces' / f'trace_{t.instance_id}.json'); break
        summary['tasks'].append(t.instance_id); summary['resolved'] += int(row['resolved'])
        print(f"[{i}/{len(sound)}] {t.instance_id} resolved={row['resolved']} calls={row['tool_calls']} "
              f"agent={row['duration_s']}s setup={row['setup_s']}s err={(row['error'] or '')[:100]}")
    n = len(summary['tasks'])
    print(f"RESOLVED {summary['resolved']}/{n}" if n else 'no tasks run')
(RUN_DIR / 'summary.json').write_text(json.dumps(summary, indent=1))

# %%
# ---------------------------------------------------------------- bundle for download + stop server
# Official logs may contain repository snippets: keep the bundle private, never commit it (plan §1.3).
for extra in (RUN_DIR / 'official' / 'logs',):
    if extra.exists():
        shutil.copytree(extra, RUN_DIR / 'logs', dirs_exist_ok=True)
shutil.make_archive(str(Path('/kaggle/working/runs') / EXP_ID), 'zip', RUN_DIR)
print('bundle:', Path('/kaggle/working/runs') / f'{EXP_ID}.zip')
try:
    server.stop()
except Exception:  # noqa: BLE001
    pass
