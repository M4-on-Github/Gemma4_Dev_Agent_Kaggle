"""Make the subprocess sandbox test against a copy of the public scorer's Python instead of the image's.

Why: swegemma's subprocess sandbox builds each task's venv from the interpreter that runs the
harness (here the vLLM image's Python 3.12) with that interpreter's site-packages visible, so the
tests import vLLM's pinned pygments, starlette, httpx, dirty_equals, ... The scorer instead runs
tests in `python:3.13-slim` with the pip packages of data/raw/docker/Dockerfile.public and the
competition wheels unpacked into site-packages (container_setup._ensure_container_site_packages).

`env/py313-scorer` is that copy (built by slurm/build_scorer_env.sh). `install(py313, extras)`
patches swegemma before the Evaluator is built so that every sandbox venv is
`<py313> -m venv --system-site-packages`, without the image's site-packages, and, when `extras`
is given, with one .pth line adding that directory (packages the public scorer does not ship;
results that need them are not scorer-faithful and are labelled so by the caller).
"""
import os
import subprocess
import types
from pathlib import Path

WRAPPED = {"pip": "pip", "pip3": "pip", "pytest": "pytest", "py.test": "pytest"}


def install(py313, extras=None):
    import swegemma.evaluate as ev
    import swegemma.sandbox.subprocess as sp

    py313 = str(Path(py313).resolve())
    extras = str(Path(extras).resolve()) if extras else None
    assert os.access(py313, os.X_OK), f"{py313} is not an executable interpreter"
    if extras:
        assert Path(extras).is_dir(), f"extras dir {extras} missing"

    def create(env_dir, system_site_packages=False, with_pip=False, symlinks=False, clear=False, **_):
        env_dir = Path(env_dir)
        cmd = [py313, "-m", "venv", "--system-site-packages", "--without-pip",
               "--symlinks" if symlinks else "--copies"] + (["--clear"] if clear else []) + [str(env_dir)]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        # The sandbox puts the harness's own bin dir on PATH after the venv's: without these, `pip`
        # and `pytest` would resolve to the image's Python 3.12.
        for name, mod in WRAPPED.items():
            w = env_dir / "bin" / name
            w.write_text(f'#!/bin/sh\nexec "{env_dir}/bin/python3" -m {mod} "$@"\n')
            w.chmod(0o755)
        if extras:
            for d in env_dir.glob("lib/python*/site-packages"):
                (d / "_heng_extras.pth").write_text(extras + "\n")

    sp.venv = types.SimpleNamespace(create=create)

    class ScorerSubprocessManager(sp.SubprocessManager):
        def __init__(self, *args, **kwargs):
            kwargs["system_site_packages"] = False   # no _host_env.pth pointing at the image's packages
            super().__init__(*args, **kwargs)

    ev.SubprocessManager = ScorerSubprocessManager
    out = subprocess.run([py313, "-c", "import sys; print(sys.version.split()[0])"], capture_output=True, text=True)
    return {"py313": py313, "python_version": out.stdout.strip(), "extras": extras}
