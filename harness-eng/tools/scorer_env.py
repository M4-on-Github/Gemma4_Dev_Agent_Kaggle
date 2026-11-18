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
import contextvars
import os
import subprocess
import types
from pathlib import Path

WRAPPED = {"pip": "pip", "pip3": "pip", "pytest": "pytest", "py.test": "pytest"}


CURRENT_TASK = contextvars.ContextVar("heng_current_task", default=None)
TASK_ENV_USE = {}   # instance_id -> task env dir actually added (None when it had none)

# Runs at venv startup from a .pth line: put the task's own dependency dir ahead of every
# site-packages, so a version the repo declared (an older starlette, pygments, ...) wins over the
# scorer's newest-version set; the workspace (PYTHONPATH) still comes first.
PTH_LINE = ("import sys; p={p!r}; i=next((j for j, x in enumerate(sys.path) if x.endswith('site-packages')),"
            " len(sys.path)); p in sys.path or sys.path.insert(i, p)\n")


def install(py313, extras=None, task_envs=None):
    import swegemma.evaluate as ev
    import swegemma.sandbox.subprocess as sp

    py313 = str(Path(py313).resolve())
    extras = str(Path(extras).resolve()) if extras else None
    task_envs = Path(task_envs).resolve() if task_envs else None
    assert os.access(py313, os.X_OK), f"{py313} is not an executable interpreter"
    if extras:
        assert Path(extras).is_dir(), f"extras dir {extras} missing"
    if task_envs:
        assert task_envs.is_dir(), f"task-envs dir {task_envs} missing"
        orig = ev.Evaluator.evaluate_task

        async def evaluate_task(self, task, *args, **kwargs):
            # asyncio.to_thread copies the context, so SubprocessManager.start -> venv.create sees it
            token = CURRENT_TASK.set(task.instance_id)
            try:
                return await orig(self, task, *args, **kwargs)
            finally:
                CURRENT_TASK.reset(token)

        ev.Evaluator.evaluate_task = evaluate_task

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
        if task_envs:
            iid = CURRENT_TASK.get()
            assert iid, "venv created outside evaluate_task; cannot tell which task env to add"
            te = task_envs / iid
            TASK_ENV_USE[iid] = str(te) if te.is_dir() else None
            if te.is_dir():
                for d in env_dir.glob("lib/python*/site-packages"):
                    # "_" sorts before the alphabetical .pth files, so this runs first
                    (d / "__heng_taskenv.pth").write_text(PTH_LINE.format(p=str(te)))

    sp.venv = types.SimpleNamespace(create=create)

    class ScorerSubprocessManager(sp.SubprocessManager):
        def __init__(self, *args, **kwargs):
            kwargs["system_site_packages"] = False   # no _host_env.pth pointing at the image's packages
            super().__init__(*args, **kwargs)

    ev.SubprocessManager = ScorerSubprocessManager
    out = subprocess.run([py313, "-c", "import sys; print(sys.version.split()[0])"], capture_output=True, text=True)
    return {"py313": py313, "python_version": out.stdout.strip(), "extras": extras,
            "task_envs": str(task_envs) if task_envs else None}
