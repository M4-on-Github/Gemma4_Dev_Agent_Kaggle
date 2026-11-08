#!/usr/bin/env python3
"""EXP-058: derive the adapter-test notebook source from notebooks/kaggle_eval_l4x4.py.

Asserts the template's LF sha256, adds four parameters after `MODEL_NAME = ""` and inserts three cells, each
before a cell header that must match exactly once. Nothing in the template is changed or removed.

  A (before the vLLM cell)        assemble adapters/copy_lora from the kernel_sources mount, sha-checked; the tree
                                   must equal the packed full zip's manifest; discover_adapters and the official
                                   validate_directory must accept it. Any failure stops the kernel before boot.
  B (before evaluator helpers)    /v1/models lists the adapter; the vLLM LoRA flags and KV pool; compile the tree
                                   the way the harness runner does (registry without the adapter, so
                                   resolve_swegemma_adapter takes its model_copy branch) and stop unless the root
                                   model routes to the adapter; one live call through that model object; an
                                   adapter decode probe beside the base one.
  C (before the bundle cell)      count trace steps by served model (adapter / other / none), counts only.
Everything lands in RUN_DIR/adapter_check.json.

    python -I -X utf8 experiments/EXP-058/make_nb_src.py notebooks/kaggle_eval_l4x4.py \
        experiments/EXP-058/full_manifest.json notebooks/exp058_lora/kaggle_eval_adapter.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

TEMPLATE_SHA256 = "f307ac369898076bfdcc1cffc1d22591d74cca66e14ea76228e9a60a284f2d19"   # LF, at commit 2111524
PARAM_ANCHOR = 'MODEL_NAME = ""\n'
HDR = "# %%\n# ---------------------------------------------------------------- "
ANCHOR_A = HDR + "vLLM server (hosts' recipe)"
ANCHOR_B = HDR + "evaluator helpers"
ANCHOR_C = HDR + "bundle for download + stop server"

CELL_A = r'''# %%
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

'''

CELL_B = r'''# %%
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

'''

CELL_C = r'''# %%
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

'''


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, man_path, out = (Path(a) for a in argv)
    text = src.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
    got = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if got != TEMPLATE_SHA256:
        print(f"REFUSED: template sha256 {got} != {TEMPLATE_SHA256}")
        return 1
    man = json.loads(man_path.read_text(encoding="utf-8"))
    params = (
        "# EXP-058 2026-11-08: the adapter-bearing tree arrives as a light zip (embedded) plus the adapter weights from\n"
        "# the kernel_sources mount of rainm4/gemma4-exp054-copy-lora; every file is sha-checked before the server boots.\n"
        f"EXPECT_LIGHT_SHA256 = {man['light_zip_sha256']!r}\n"
        "ADAPTER_NAME = 'copy_lora'\n"
        f"ADAPTER_SHA256 = {json.dumps({k.rsplit('/', 1)[1]: v for k, v in man['members'].items() if k.startswith('adapters/')})}\n"
        f"FULL_MANIFEST = {json.dumps(man['members'], sort_keys=True)}\n"
    )
    for anchor, label in ((PARAM_ANCHOR, "param"), (ANCHOR_A, "A"), (ANCHOR_B, "B"), (ANCHOR_C, "C")):
        n = text.count(anchor)
        if n != 1:
            print(f"REFUSED: anchor {label} matched {n} times, need exactly 1")
            return 1
    text = text.replace(PARAM_ANCHOR, PARAM_ANCHOR + params, 1)
    text = text.replace(ANCHOR_A, CELL_A + ANCHOR_A, 1)
    text = text.replace(ANCHOR_B, CELL_B + ANCHOR_B, 1)
    text = text.replace(ANCHOR_C, CELL_C + ANCHOR_C, 1)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(text.encode("utf-8"))
    print(f"wrote {out}  lines {text.count(chr(10))}  sha256 {hashlib.sha256(text.encode('utf-8')).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
