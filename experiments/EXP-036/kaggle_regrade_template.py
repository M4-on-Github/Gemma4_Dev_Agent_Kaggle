# %% [markdown]
# # EXP-036: zero-GPU re-grade of EXP-028 Arms R and RH with the two test-only packages present
#
# Grading only. No agent and no model. `tools/regrade_patches.py` hands each stored patch straight to the
# harness grader (`sandbox='subprocess'`). For a task whose extracted workspace imports `inline_snapshot` or
# `dirty_equals`, the matching `tools/compat_shims/<pkg>` is first copied into `/workspace`.
#
# The kernel runs four passes over the same 48 dev-48 ids, in this order:
# - **R** and **RH**: the stored patches;
# - **GOLD**: the reference patches, written here from the competition's `tasks.jsonl`;
# - **BASE**: empty patches. This is the snapshot with the test patch applied, because grading always applies it.
#
# Timeouts are those of the scored grade: 240 s per command and 300 s for the pytest phase.
#
# **Inputs:** competition `gemma-4-developer-agent` and dataset `metric/gemma-4-developer-agent-wheelhouse`.
# **No model. Accelerator: none (CPU). Internet: off.**
# Pre-registration: `experiments/EXP-036-regrade-R-RH-with-shims.md`.
#
# This file is a template. `experiments/EXP-036/build_regrade_notebook.py` fills in the payloads. The built
# `.ipynb` embeds agent patches, so it is never committed (plan.md:52).

# %%
# ---------------------------------------------------------------- parameters (filled in by the builder)
EXP_ID = "EXP-036-regrade"
TASK_IDS = []
COMMAND_TIMEOUT = 240
VERIFICATION_TIMEOUT = 300
TAIL_CHARS = 20000
PASSES = ["R", "RH", "GOLD", "BASE"]
REGRADE_SCRIPT_B64 = ""
SHIM_INLINE_B64 = ""
SHIM_DIRTY_B64 = ""
PATCHES_ZIP_B64 = {}

# %%
# ---------------------------------------------------------------- CPU-only check + wheelhouse (EXP-004 recipe)
import base64, glob, importlib, io, json, os, shutil, subprocess, sys, time, zipfile
from pathlib import Path

ENV = {
    'python': sys.version.split()[0],
    'nvidia_device_nodes': sorted(glob.glob('/dev/nvidia[0-9]*')),
    'nvidia_smi_on_path': shutil.which('nvidia-smi') is not None,
    'cuda_visible_devices': os.environ.get('CUDA_VISIBLE_DEVICES'),
    'cpu_count': os.cpu_count(),
}
print('environment:', json.dumps(ENV))
print('accelerator:', 'GPU device nodes present' if ENV['nvidia_device_nodes'] else 'none (CPU only)')

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
REQUIRED_PKGS = ('swegemma', 'adk_submission', 'adk_eval_core')


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
assert not missing, 'required packages unavailable: ' + '; '.join(missing)
print('required packages present:', ', '.join(REQUIRED_PKGS), '| never imported here: vllm, torch, litellm, google.adk')

DATA_DIR = next(Path(p) for p in ['/kaggle/input/competitions/gemma-4-developer-agent',
                                  '/kaggle/input/gemma-4-developer-agent'] if Path(p).exists())
RUN_DIR = Path('/kaggle/working/runs') / EXP_ID
RUN_DIR.mkdir(parents=True, exist_ok=True)
(RUN_DIR / 'environment.json').write_text(json.dumps(ENV, indent=1))
print('data:', DATA_DIR, ' run dir:', RUN_DIR)

# %%
# ---------------------------------------------------------------- unpack tool + shims; write the four patch dirs
TOOLS_DIR = Path('/kaggle/working/tools')
for pkg in ('inline_snapshot', 'dirty_equals'):
    (TOOLS_DIR / 'compat_shims' / pkg).mkdir(parents=True, exist_ok=True)
(TOOLS_DIR / 'regrade_patches.py').write_bytes(base64.b64decode(REGRADE_SCRIPT_B64))
(TOOLS_DIR / 'compat_shims' / 'inline_snapshot' / '__init__.py').write_bytes(base64.b64decode(SHIM_INLINE_B64))
(TOOLS_DIR / 'compat_shims' / 'dirty_equals' / '__init__.py').write_bytes(base64.b64decode(SHIM_DIRTY_B64))

PATCH_DIRS = {}
for label, b64 in PATCHES_ZIP_B64.items():
    d = Path('/kaggle/working/patches') / label
    d.mkdir(parents=True, exist_ok=True)
    zipfile.ZipFile(io.BytesIO(base64.b64decode(b64))).extractall(d)
    PATCH_DIRS[label] = d

want = set(TASK_IDS)
gold_dir = Path('/kaggle/working/patches') / 'GOLD'
base_dir = Path('/kaggle/working/patches') / 'BASE'
gold_dir.mkdir(parents=True, exist_ok=True)
base_dir.mkdir(parents=True, exist_ok=True)
for line in (DATA_DIR / 'tasks.jsonl').read_text(encoding='utf-8').splitlines():
    if not line.strip():
        continue
    t = json.loads(line)
    if t['instance_id'] in want:
        (gold_dir / f"{t['instance_id']}.patch").write_text(t.get('patch') or '', encoding='utf-8')
        (base_dir / f"{t['instance_id']}.patch").write_text('', encoding='utf-8')
PATCH_DIRS['GOLD'] = gold_dir
PATCH_DIRS['BASE'] = base_dir
counts = {k: len(list(v.glob('*.patch'))) for k, v in PATCH_DIRS.items()}
print('patch files per pass:', counts)
assert all(counts[p] == len(want) for p in PASSES), counts

# %%
# ---------------------------------------------------------------- four grading passes (subprocess sandbox, CPU)
TASK_IDS_ARG = ','.join(TASK_IDS)
TIMES = {}


def run_regrade(label: str) -> int:
    out_dir = RUN_DIR / label
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(TOOLS_DIR / 'regrade_patches.py'),
           '--tasks', str(DATA_DIR / 'tasks.jsonl'),
           '--snapshots', str(DATA_DIR / 'snapshots'),
           '--wheels', str(DATA_DIR / 'wheels'),
           '--patches-dir', str(PATCH_DIRS[label]),
           '--out', str(out_dir),
           '--label', label,
           '--task-ids', TASK_IDS_ARG,
           '--timeout', str(COMMAND_TIMEOUT),
           '--verification-timeout', str(VERIFICATION_TIMEOUT),
           '--tail-chars', str(TAIL_CHARS)]
    print('+', ' '.join(cmd[:2]), '... --label', label)
    t0 = time.time()
    rc = subprocess.run(cmd, cwd='/kaggle/working').returncode
    TIMES[label] = round(time.time() - t0, 1)
    return rc


RCS = {p: run_regrade(p) for p in PASSES}
print('exit codes:', RCS, ' seconds:', TIMES)

# %%
# ---------------------------------------------------------------- counts only (the analysis runs locally)
def load_jsonl(p: Path) -> list:
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]


summary = {'exp_id': EXP_ID, 'environment': ENV, 'exit_codes': RCS, 'seconds': TIMES, 'passes': {}}
for p in PASSES:
    rows = load_jsonl(RUN_DIR / p / 'regrade.jsonl')
    summary['passes'][p] = {'n': len(rows), 'resolved': sum(bool(r['resolved']) for r in rows),
                            'shims_dropped_tasks': sum(bool(r.get('shims_dropped')) for r in rows)}
(RUN_DIR / 'summary.json').write_text(json.dumps(summary, indent=1))
print(json.dumps(summary, indent=1))

# %%
# ---------------------------------------------------------------- bundle for download
shutil.make_archive(str(Path('/kaggle/working/runs') / EXP_ID), 'zip', RUN_DIR)
print('bundle:', Path('/kaggle/working/runs') / f'{EXP_ID}.zip')
