# %% [markdown]
# # Gemma 4 Developer Agent — Phase 0 checks, EXP-000 gold control, baseline eval (4x L4)
#
# One notebook, three switches (`RUN_PHASE0_CHECKS`, `RUN_GOLD_CONTROL`, `RUN_AGENT`). It mirrors the
# organizers' Getting-Started recipe (wheelhouse install, `VllmServer`, `swegemma.evaluate.Evaluator` with the
# subprocess sandbox) and writes everything under `/kaggle/working/runs/<EXP_ID>/` in the layout that
# `tools/analyze_traces.py` and `tools/estimate_budget.py` read.
#
# **Attach as inputs** (Add Input): competition `gemma-4-developer-agent`, dataset
# `metric/gemma-4-developer-agent-wheelhouse`, model `google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2`
# (or the `.../gemma-4-e4b-it-qat-w4a16-ct/2` / `.../gemma-4-e2b-it-qat-w4a16-ct/2` input when the zip's agent.yaml names a
# small variant; the vLLM cell takes the model from the zip).
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
# Model: taken from the embedded zip's agent.yaml. Set MODEL_NAME only as a cross-check (the run asserts the
# zip declares exactly this name), e.g. --set MODEL_NAME='"gemma-4-e2b-it-qat-w4a16-ct"'. The kernel-metadata
# model_sources must attach google/gemma-4/other/<name>/2 for the same name.
MODEL_NAME = ""
# EXP-058 2026-11-08: the adapter-bearing tree arrives as a light zip (embedded) plus the adapter weights from
# the kernel_sources mount of rainm4/gemma4-exp054-copy-lora; every file is sha-checked before the server boots.
EXPECT_LIGHT_SHA256 = '73aedc886db14212ea4abfef8b0036f7c7db68250caffa859e72d2c4c6b051f0'
ADAPTER_NAME = 'copy_lora'
ADAPTER_SHA256 = {"adapter_config.json": "cf87fdf065108e1f77f76fb706bf007cf5e5b5aebf1951310f88baecf1bdf2db", "adapter_model.safetensors": "c4af0041176a02b7b718d6fc4f9fd8990f30c7aea1946d1da3529f5a190e6d64"}
FULL_MANIFEST = {"adapters/copy_lora/adapter_config.json": "cf87fdf065108e1f77f76fb706bf007cf5e5b5aebf1951310f88baecf1bdf2db", "adapters/copy_lora/adapter_model.safetensors": "c4af0041176a02b7b718d6fc4f9fd8990f30c7aea1946d1da3529f5a190e6d64", "agent.yaml": "2acb50942a18b307802493a0c09131799816c2d5701dc89c74649a63c80dc0c9", "configs/sampling.yaml": "630056889710d27dbf17c8fde62e033b7329616b7db435987cb4607b66a7c3f6", "eval_config.yaml": "916cf6cb34a6cc3de39837fa72cac681599b9ac2a3ee0b893adadfd36474c531", "prompts/system.md": "57a20af4eb29bbfdab003ab8cf04f6495674887ec5ba3dd746750930179a8041"}

# Compaction settings: Q7 ANSWERED [V] from HARNESS_README.md section 7.2 (interval 15, overlap 2,
# token_threshold 14,336, event_retention_size 5). The 'interval 5' reading confused retention with interval.
COMPACTION_INTERVAL = 15   # [V] HARNESS_README §7.2: interval 15, overlap 2, threshold 14,336, retention 5
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
# The wheelhouse ships cp312 binary wheels (orchestrator env = Python 3.12), but the grading sandbox and
# Kaggle's CPU image are Python 3.13 (docker/Dockerfile.sandbox is `python:3.13-slim`). A single bulk
# `pip install ... check=True` aborts the WHOLE install when one wheel is incompatible, which is what killed
# the first EXP-000 push (apache_tvm_ffi cp312 on py3.13). Filter by interpreter tag, then assert that the
# packages we actually need for this run arrived.
# Import names, not distribution names: the `google_adk` wheel installs the `google.adk`
# namespace package, so importing 'google_adk' always fails. [V] google_adk-1.36.1.dist-info
REQUIRED_PKGS = ('swegemma', 'adk_submission', 'adk_eval_core', 'google.adk')

def _wheel_is_compatible(path: Path) -> bool:
    """True when the wheel's tags intersect this interpreter's supported tags."""
    try:
        from packaging.tags import sys_tags
        from packaging.utils import parse_wheel_filename
    except Exception:  # noqa: BLE001 - fall back to accepting everything
        return True
    try:
        _, _, _, tags = parse_wheel_filename(path.name)
    except Exception:  # noqa: BLE001 - odd filename: let pip decide
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
from swegemma.models import load_tasks  # [V] swegemma/models/__init__.py exports load_tasks(path)->list[Task]
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
elif not RUN_AGENT and (DATA_DIR / 'sample_submission').is_dir():
    # A gold-control run never calls a model, so it needs no submission of ours. Fall back to the
    # official sample_submission: it is a real, schema-valid submission dir, so the model/adapter/limits
    # validation below still runs for real instead of being skipped.
    shutil.copytree(DATA_DIR / 'sample_submission', AGENT_DIR, dirs_exist_ok=True)
    print('no submission supplied; using official sample_submission (RUN_AGENT=False)')
else:
    raise SystemExit('no submission: set SUBMISSION_ZIP to your uploaded dataset file or embed with tools/build_notebook.py')
print('agent files:', sorted(str(p.relative_to(AGENT_DIR)) for p in AGENT_DIR.rglob('*') if p.is_file()))
import yaml
EVAL = (yaml.safe_load((AGENT_DIR / 'eval_config.yaml').read_text()) or {}).get('evaluation', {}) \
    if (AGENT_DIR / 'eval_config.yaml').exists() else {}
if not RUN_AGENT:
    # The official sample eval_config is deliberately tiny (1 min / 10 tool calls) to demo the schema.
    # Gold control runs no agent loop, so those caps only risk failing a sound task for budget reasons
    # and corrupting the Q5 answer. Give the grader room; the agent budget is irrelevant here.
    EVAL = {**EVAL, 'timeout_seconds': 300, 'max_time_minutes': 60.0, 'max_tool_calls': 100}
print('eval_config:', EVAL)

# %%
# ---------------------------------------------------------------- EXP-058 A: assemble + verify the adapter tree (pre-boot)
import hashlib
def _x_sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
ADAPTER_CHECK = {'exp_id': EXP_ID, 'pre_boot': {}, 'post_boot': {}, 'post_run': {}, 'failures': []}
def _x_save(): (RUN_DIR / 'adapter_check.json').write_text(json.dumps(ADAPTER_CHECK, indent=1, default=str))
def _x_fail(stage, msg):
    ADAPTER_CHECK['failures'].append(f'{stage}: {msg}'); _x_save()
    raise SystemExit(f'EXP-058 adapter check failed at {stage}: {msg}')
_pre = ADAPTER_CHECK['pre_boot']
_pre['light_zip_sha256'] = hashlib.sha256(base64.b64decode(SUBMISSION_B64)).hexdigest() if SUBMISSION_B64 else None
if _pre['light_zip_sha256'] != EXPECT_LIGHT_SHA256:
    _x_fail('light_zip', f"sha256 {_pre['light_zip_sha256']} != {EXPECT_LIGHT_SHA256}")
_mounts = sorted({str(p) for pat in ('/kaggle/input/*', '/kaggle/input/*/*', '/kaggle/input/*/*/*')
                  for p in glob.glob(pat) if Path(p).is_dir() and ('exp054' in Path(p).name or 'copy-lora' in Path(p).name)})
_pre['source_mounts'] = _mounts
_dest = AGENT_DIR / 'adapters' / ADAPTER_NAME
_dest.mkdir(parents=True, exist_ok=True)
for _fname, _want in ADAPTER_SHA256.items():
    _cands = sorted({str(c) for m in _mounts for c in Path(m).rglob(_fname)})
    _hits = [c for c in _cands if _x_sha(c) == _want]
    _pre[_fname] = {'candidates': len(_cands), 'source': _hits[0] if _hits else None,
                    'in_light_zip': (_dest / _fname).is_file()}
    if (_dest / _fname).is_file():
        if _x_sha(_dest / _fname) != _want:
            _x_fail('adapter_file', f'{_fname} from the light zip has the wrong sha256')
        continue
    if not _hits:
        _x_fail('adapter_file', f'{_fname}: none of {len(_cands)} candidates under {_mounts} has sha256 {_want}')
    shutil.copyfile(_hits[0], _dest / _fname)
_tree = {p.relative_to(AGENT_DIR).as_posix(): _x_sha(p) for p in sorted(AGENT_DIR.rglob('*')) if p.is_file()}
_pre['tree_equals_full_manifest'] = _tree == FULL_MANIFEST
if _tree != FULL_MANIFEST:
    _x_fail('manifest', f'assembled tree {sorted(_tree)} differs from the full zip manifest {sorted(FULL_MANIFEST)}')
from adk_submission import discover_adapters as _x_discover, validate_directory as _x_validate
from swegemma.config import ALLOWED_ADAPTER_EXTENSIONS as _X_EXT, build_submission_limits as _x_limits
_man = _x_discover(str(AGENT_DIR), adapter_extensions=_X_EXT)
_pre['discovered'] = {n: {'rank': i.rank, 'format': i.format, 'size_bytes': i.size_bytes} for n, i in _man.adapters.items()}
if set(_man.adapters) != {ADAPTER_NAME} or _man.adapters[ADAPTER_NAME].rank != 8:
    _x_fail('discover_adapters', f"got {_pre['discovered']}, want {{{ADAPTER_NAME!r}: rank 8}}")
try:
    _sd = _x_validate(AGENT_DIR, limits=_x_limits()[0])
    _pre['validate_directory'] = {'ok': True, 'type': type(_sd).__name__,
                                  'adapters': len(getattr(_sd, 'adapters', []) or [])}
except Exception as _exc:  # noqa: BLE001
    _x_fail('validate_directory', f'{type(_exc).__name__}: {str(_exc)[:300]}')
_x_save()
print('EXP-058 pre-boot checks passed:', json.dumps(_pre, default=str))

# %%
# ---------------------------------------------------------------- vLLM server (hosts' recipe)  # VERIFY
# CPU-safe imports only: a gold-control run (RUN_AGENT=False) never loads vLLM/litellm/torch, and on
# Kaggle's Python 3.13 CPU image those cp312 wheels are not installed at all.
from adk_submission import ModelRegistry, discover_adapters, discover_declared_models
from swegemma.config import ALLOWED_ADAPTER_EXTENSIONS, EvalConfig, build_submission_limits

# D-004 2026-11-05: TARGET was hard-coded to 31B; it now comes from the zip, so a small-variant candidate
# runs without editing this file. Mirror of tools/submission_rules.py ALLOWED_MODEL_NAMES (the notebook runs
# on Kaggle and cannot import tools/). 12B is excluded there and here: it needs vLLM --hf-overrides
# (HARNESS_README §3.1 MODEL_VLLM_EXTRA_ARGS), which this cell does not pass.
ALLOWED_MODELS = ('gemma-4-31b-it-qat-w4a16-ct', 'gemma-4-e4b-it-qat-w4a16-ct', 'gemma-4-e2b-it-qat-w4a16-ct')
# [V] adk_submission.discovery.discover_declared_models(submission_dir) -> set[str]; walks the root
# agent, sub_agents and agent_tools. There is no `validate_single_declared_model` anywhere in the
# wheelhouse -- that was an invented name. Exactly one model may be declared, so assert the set size.
declared = discover_declared_models(str(AGENT_DIR))
assert len(declared) == 1, f'submission must declare exactly one model, got {sorted(declared)}'
TARGET = next(iter(declared)).strip()
for _prefix in ('openai/', 'google/', 'hosted_vllm/', 'custom/'):   # [V] HARNESS_README §3.2 normalize_model_name
    if TARGET.startswith(_prefix):
        TARGET = TARGET[len(_prefix):]
        break
assert TARGET in ALLOWED_MODELS, f'declared model {TARGET!r} not in {ALLOWED_MODELS}'
assert not MODEL_NAME or MODEL_NAME == TARGET, f'MODEL_NAME={MODEL_NAME!r} but the zip declares {TARGET!r}'
MODEL_DIR = f'/kaggle/input/models/google/gemma-4/other/{TARGET}/2'   # [V] path layout EXP-006 resolved 'exact'
print('model:', TARGET, '->', MODEL_DIR)
adapters = discover_adapters(str(AGENT_DIR), adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
# EXP-000 gold control needs no model: it applies each task's reference patch and runs test_patch.
# Gate the server so a gold-control-only run costs ZERO GPU quota (plan §5.7) and can use a CPU notebook.
NEED_SERVER = RUN_AGENT or MEASURE_DECODE_SPEED
server = None
SERVER_START_S = None
target_id = None
models = ModelRegistry()

if NEED_SERVER:
    import litellm, torch
    from adk_submission import VllmConfig, VllmServer
    from google.adk.models.lite_llm import LiteLlm
    try:
        from adk_submission.resolvers.generation import install_litellm_reasoning_patch
        install_litellm_reasoning_patch()
    except Exception as exc:  # noqa: BLE001
        print('reasoning patch not installed:', exc)
    litellm.drop_params = True
    gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
    assert gpu_count >= 1, 'no GPU: select the L4 x4 accelerator'
    assert Path(MODEL_DIR, 'config.json').exists(), (
        f'{MODEL_DIR} missing: kernel-metadata.json model_sources must list google/gemma-4/other/{TARGET}/2')
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
    for alias in {next(iter(declared)), TARGET}:
        models.register(alias, LiteLlm(model=f'openai/{target_id}', api_base=server.base_url, api_key='EMPTY'))
else:
    print('vLLM server SKIPPED (RUN_AGENT and MEASURE_DECODE_SPEED are both False) - no GPU required.')

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
# ---------------------------------------------------------------- EXP-058 B: adapter serving + routing checks (post-boot)
import re, urllib.request
_post = ADAPTER_CHECK['post_boot']
def _x_run(fn):
    try:
        _loop = asyncio.get_running_loop()
    except RuntimeError:
        _loop = None
    if _loop is not None and _loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as _ex:
            return _ex.submit(lambda: asyncio.run(fn())).result()
    return asyncio.run(fn())
import asyncio, concurrent.futures
_cmd = list(server.build_cmd())
_post['lora_flags'] = {f: (_cmd[_cmd.index(f) + 1] if f in _cmd and _cmd.index(f) + 1 < len(_cmd) else None)
                       for f in ('--max-loras', '--max-lora-rank', '--lora-modules')}
_post['enable_lora_flag'] = '--enable-lora' in _cmd
try:
    _log = Path(server.log_path).read_text(errors='replace')
    _kv = re.findall(r'GPU KV cache size:\s*([\d,]+) tokens', _log)
    _mc = re.findall(r'Maximum concurrency for ([\d,]+) tokens per request:\s*([\d.]+)x', _log)
    _post['gpu_kv_cache_tokens'] = min(int(x.replace(',', '')) for x in _kv) if _kv else None
    _post['max_concurrency'] = min(float(x) for _, x in _mc) if _mc else None
except Exception as _exc:  # noqa: BLE001
    _post['kv_read_error'] = type(_exc).__name__
with urllib.request.urlopen(server.base_url.rstrip('/') + '/models', timeout=60) as _r:
    _ids = [m.get('id') for m in json.loads(_r.read()).get('data', [])]
_post['v1_models'] = _ids
if ADAPTER_NAME not in _ids:
    _x_fail('v1_models', f'{ADAPTER_NAME} not served; /v1/models = {_ids}')
from adk_submission import compile_submission as _x_compile
from swegemma.harness.agent_runner import resolve_swegemma_adapter as _x_resolve
from types import SimpleNamespace as _NS
class _XStub:
    def __init__(self):
        self.docker = _NS(copy_from=lambda *a, **k: None); self.container_id = 'exp058'; self.budget = None
        self.tool_lock = None; self.tool_calls_used = None
        self.harness = _NS(max_file_lines=150, max_file_chars=10000, max_stdout_chars=5000, command_timeout_seconds=240)
    def check_budget(self, count_tool_call=True): return None
try:
    from swegemma.tools import create_tools as _x_tools
    _tools = _x_tools(_XStub()); _post['compile_tools'] = 'swegemma.create_tools'
except Exception as _exc:  # noqa: BLE001
    _names = ['run_command', 'read_file', 'edit_file', 'write_file', 'get_status', 'submit_patch']
    _tools = {n: (lambda **kw: None) for n in _names}; _post['compile_tools'] = f'dummies ({type(_exc).__name__})'
_post['registry_has_adapter'] = ADAPTER_NAME in models
try:
    _lim, _gen = build_submission_limits()
    _agent = _x_compile(submission_dir=str(AGENT_DIR), tool_registry=_tools, model_registry=models, limits=_lim,
                        generation_constraints=_gen, adapter_manifest=adapters,
                        adapter_resolver_fn=lambda b, i: _x_resolve(b, i, models))
except Exception as _exc:  # noqa: BLE001
    _post['compile_error'] = f'{type(_exc).__name__}: {str(_exc)[:300]}'
    if any(k in type(_exc).__name__ for k in ('Adapter', 'Model', 'Validation')):
        _x_fail('compile', _post['compile_error'])
    _agent = None
if _agent is not None:
    _m = getattr(_agent, 'model', None)
    _post['agent_model'] = getattr(_m, 'model', _m if isinstance(_m, str) else type(_m).__name__)
    _post['agent_api_base_is_server'] = ((getattr(_m, '_additional_args', None) or {}).get('api_base') == server.base_url)
    if not str(_post['agent_model']).endswith(ADAPTER_NAME):
        _x_fail('routing', f"compiled root model is {_post['agent_model']}, not the adapter")
    from google.adk.models.llm_request import LlmRequest as _XReq
    from google.genai import types as _xgt
    async def _x_live():
        _req = _XReq(model=_m.model, contents=[_xgt.Content(role='user', parts=[_xgt.Part(text='Reply with one word.')])],
                     config=_xgt.GenerateContentConfig(max_output_tokens=256))
        return [r async for r in _m.generate_content_async(_req, stream=False)]
    try:
        _resp = _x_run(_x_live)
        _post['live_call_model_version'] = getattr(_resp[-1], 'model_version', None) if _resp else None
    except Exception as _exc:  # noqa: BLE001
        _x_fail('live_call', f'{type(_exc).__name__}: {str(_exc)[:300]}')
    if _post['live_call_model_version'] and not str(_post['live_call_model_version']).endswith(ADAPTER_NAME):
        _x_fail('live_call', f"served by {_post['live_call_model_version']}, not the adapter")
_body = json.dumps({'model': ADAPTER_NAME, 'messages': [{'role': 'user', 'content': 'Count from 1 to 400 separated by spaces.'}],
                    'max_tokens': 400, 'temperature': 0.0, 'chat_template_kwargs': {'enable_thinking': False}}).encode()
_t0 = time.time()
with urllib.request.urlopen(urllib.request.Request(server.base_url.rstrip('/') + '/chat/completions', data=_body,
                            headers={'Content-Type': 'application/json'}, method='POST'), timeout=600) as _r:
    _out = json.loads(_r.read())
_dt = time.time() - _t0
_ct = _out.get('usage', {}).get('completion_tokens', 0)
_post['adapter_decode_probe'] = {'model': _out.get('model'), 'completion_tokens': _ct, 'seconds': round(_dt, 2),
                                 'tok_s': round(_ct / _dt, 1) if _dt else None}
_post['base_decode_probe'] = DECODE
_x_save()
print('EXP-058 post-boot checks passed:', json.dumps(_post, default=str))

# %%
# ---------------------------------------------------------------- evaluator helpers
import asyncio, concurrent.futures
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.apps._configs import EventsCompactionConfig  # [V] google/adk/apps/_configs.py:50
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
# `sound` must exist even when the gold control is skipped, or the agent cell below raises NameError.
sound = list(candidates)
if RUN_GOLD_CONTROL:
    from adk_eval_core.tracing import SessionTrace  # [V] tracing/__init__.py re-exports it; no-arg ctor

    class GoldEvaluator(Evaluator):
        """Phase 1 returns the reference patch; no model call, nothing is shown to any agent."""
        async def _run_agent_sandbox(self, task, *args, **kwargs):  # [V] evaluate.py:194 -> tuple[str, str|None, SessionTrace]
            return task.patch, None, SessionTrace()

    gold = GoldEvaluator(make_config(RUN_DIR / 'gold_control'))
    gold_rows = []
    for i, t in enumerate(candidates, 1):
        t0 = time.time()
        r = run_sync(lambda: gold.evaluate_task(task=t, task_index=i, total_tasks=len(candidates)))
        row = {'instance_id': t.instance_id, 'repo': t.repo, 'mode': 'gold', 'resolved': bool(r.resolved),
               'exit': r.test_exit_code, 'status': getattr(r, 'status', None), 'seconds': round(time.time() - t0, 1), 'error': (getattr(r, 'error', '') or '')[:300],
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
# ---------------------------------------------------------------- EXP-058 C: served model per trace step (counts only)
_run = {'traces': 0, 'adapter_steps': 0, 'other_steps': 0, 'unnamed_steps': 0,
        'adapter_call_versions': 0, 'other_call_versions': 0, 'tasks_with_other': []}
for _tp in sorted((RUN_DIR / 'traces').glob('trace_*.json')):
    _run['traces'] += 1
    _other = False
    for _st in (json.loads(_tp.read_text(encoding='utf-8')).get('steps') or []):
        _mn = _st.get('model_name')
        if _mn is None:
            _run['unnamed_steps'] += 1
        elif str(_mn).endswith(ADAPTER_NAME):
            _run['adapter_steps'] += 1
        else:
            _run['other_steps'] += 1; _other = True
        for _tc in (_st.get('tool_calls') or []):
            _mv = (_tc.get('extra') or {}).get('model_version')
            if _mv is not None:
                _k = 'adapter_call_versions' if str(_mv).endswith(ADAPTER_NAME) else 'other_call_versions'
                _run[_k] += 1; _other = _other or _k == 'other_call_versions'
    if _other:
        _run['tasks_with_other'].append(_tp.stem[len('trace_'):])
ADAPTER_CHECK['post_run'] = _run
_x_save()
print('EXP-058 post-run routing:', json.dumps(_run))

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
