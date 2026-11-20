"""Install the competition wheelhouse and its missing dependencies into the image.
Runs inside `apptainer build` (%post).

Offline part, the recipe of the wheelhouse cell of notebooks/kaggle_eval_l4x4.py (the organizers'
Getting-Started recipe): every wheel compatible with this interpreter is installed with --no-deps.

Online part (the user's word, 2026-11-18). On Kaggle the wheelhouse lands on Kaggle's own image,
which supplies torch, litellm and the rest. The base here is a vLLM 0.24 image, so:
  1. torch 2.10.0 / torchaudio 2.10.0 / torchvision 0.25.0 for CUDA 12.8, the versions the
     wheelhouse's vLLM 0.19.1 pins, from the PyTorch wheel index;
  2. litellm 1.82.4, the version our Kaggle kernels recorded (phase0_report.json);
  3. whatever `pip check` reports as not installed, and the version conflicts in FIX_CONFLICTS,
     from PyPI, under a constraints file that pins every wheelhouse package and the torch stack.
Packages pinned by neither the wheelhouse nor our records come at PyPI's current version; the
resolved set is written to the lock file so the image can be rebuilt the same way.

Usage: python3 install_wheelhouse.py <wheelhouse dir> <report.json> <lock.txt> [--offline]
Exit 0 when the harness and server packages import, 1 otherwise.
"""
import importlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REQUIRED = ("swegemma", "adk_submission", "adk_eval_core", "google.adk", "vllm", "torch", "litellm", "transformers")
TORCH = ["torch==2.10.0", "torchaudio==2.10.0", "torchvision==0.25.0"]
TORCH_INDEX = "https://download.pytorch.org/whl/cu128"
EXTRA = ["litellm==1.82.4"]
# Conflicts worth fixing: the consumer is a harness or server package and the fix is a plain pin.
FIX_CONFLICTS = {"starlette", "websockets", "numba", "opentelemetry-exporter-otlp-proto-grpc",
                 "opentelemetry-exporter-otlp-proto-http"}
# Reported by pip check but left alone: unrelated to the harness, or the wheelhouse itself breaks
# the pin on Kaggle too (xgrammar wants transformers<5 while the wheelhouse ships transformers 5).
# Left over from the vLLM 0.24 base and wrong for the wheelhouse's vLLM 0.19.1: flashinfer refuses to
# import when flashinfer-jit-cache (0.6.12+cu130 in the base) differs from flashinfer (0.6.6 in the
# wheelhouse, which ships its kernels as flashinfer-cubin instead). Found by job 58817.
REMOVE_FROM_BASE = ["flashinfer-jit-cache"]
LEAVE = {"pycairo", "transformers", "nvidia-cutlass-dsl", "nixl-cu13"}


def pip(*args):
    return subprocess.run([sys.executable, "-m", "pip", *args], capture_output=True, text=True)


def compatible(path):
    from packaging.tags import sys_tags
    from packaging.utils import parse_wheel_filename
    try:
        tags = parse_wheel_filename(path.name)[3]
    except Exception:  # an odd filename: let pip decide
        return True
    return bool(set(sys_tags()) & set(tags))


def stage_wheels(src):
    stage = Path("/tmp/wheelhouse_stage")
    stage.mkdir(parents=True, exist_ok=True)
    for w in sorted(src.rglob("*.whl")):
        if "cutlass" in w.name.lower():
            continue
        # The dataset stores local-version wheels without the "+", which pip rejects.
        name = w.name.replace("cu128", "+cu128") if ("cu128" in w.name and "+" not in w.name) else w.name
        if not (stage / name).exists():
            os.symlink(w.resolve(), stage / name)
    return sorted(stage.glob("*.whl"))


def install_wheels(wheels):
    failed = []
    bulk = pip("install", "--no-index", "--no-deps", "--force-reinstall", *map(str, wheels))
    if bulk.returncode != 0:
        print("bulk install failed; installing wheel by wheel\n" + bulk.stderr[-2000:])
        for w in wheels:
            r = pip("install", "--no-index", "--no-deps", "--force-reinstall", str(w))
            if r.returncode != 0:
                failed.append({"wheel": w.name, "error": r.stderr.strip()[-400:]})
    return failed


def pip_check():
    lines = pip("check").stdout.strip().splitlines()
    missing, conflicts = set(), set()
    for ln in lines:
        m = re.match(r"\S+ \S+ requires ([A-Za-z0-9_.\-]+), which is not installed", ln)
        if m and m.group(1).lower() not in LEAVE:
            missing.add(m.group(1))
        m = re.match(r"\S+ \S+ has requirement (([A-Za-z0-9_.\-]+)[^,]*(?:,[^,]+?)*), but you have", ln)
        if m and m.group(2).lower() in FIX_CONFLICTS:
            conflicts.add(m.group(1).replace(" ", ""))
    return lines, sorted(missing), sorted(conflicts)


def main():
    src, report_path, lock_path = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    online = "--offline" not in sys.argv
    report = {"python": sys.version, "online": online, "steps": []}

    def step(name, r):
        ok = r.returncode == 0
        report["steps"].append({"step": name, "ok": ok, "tail": "" if ok else (r.stderr or r.stdout).strip()[-800:]})
        print(f"[{'ok' if ok else 'FAILED'}] {name}", flush=True)
        return ok

    if online:
        step("torch stack " + " ".join(TORCH), pip("install", "--index-url", TORCH_INDEX, *TORCH))

    step("remove from base " + " ".join(REMOVE_FROM_BASE), pip("uninstall", "-y", *REMOVE_FROM_BASE))
    wheels = stage_wheels(src)
    usable = [w for w in wheels if compatible(w)]
    report["wheels_found"] = len(wheels)
    report["skipped_incompatible"] = [w.name for w in wheels if w not in usable]
    report["failed_wheels"] = install_wheels(usable)
    print(f"wheelhouse: {len(usable) - len(report['failed_wheels'])}/{len(wheels)} wheels installed", flush=True)

    if online:
        from packaging.utils import parse_wheel_filename
        cons = Path("/tmp/constraints.txt")
        pins = [f"{parse_wheel_filename(w.name)[0]}=={parse_wheel_filename(w.name)[1]}" for w in usable]
        cons.write_text("\n".join(pins + TORCH) + "\n")
        step("extras " + " ".join(EXTRA), pip("install", "-c", str(cons), *EXTRA))
        for rnd in range(1, 6):   # installing a dependency can reveal its own missing dependencies
            _, missing, conflicts = pip_check()
            todo = missing + conflicts
            if not todo:
                break
            if not step(f"round {rnd}: " + " ".join(todo), pip("install", "-c", str(cons), *todo)):
                for spec in todo:   # one bad name must not block the rest
                    step(f"round {rnd} single: {spec}", pip("install", "-c", str(cons), spec))
                LEAVE.update(s.lower() for s in missing if pip("show", s).returncode != 0)

    importlib.invalidate_caches()
    imports = {}
    for mod in REQUIRED:
        try:
            m = importlib.import_module(mod)
            imports[mod] = "ok " + str(getattr(m, "__version__", ""))
        except Exception as exc:  # noqa: BLE001
            imports[mod] = f"FAILED {exc.__class__.__name__}: {exc}"
    report["imports"] = imports
    report["pip_check_left"] = pip_check()[0]
    lock_path.write_text(pip("freeze", "--all").stdout)
    report_path.write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
    bad = [m for m in REQUIRED if not imports[m].startswith("ok")]
    if bad:
        print("REQUIRED PACKAGES DO NOT IMPORT:", ", ".join(bad))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
