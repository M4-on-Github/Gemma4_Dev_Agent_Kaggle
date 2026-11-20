"""Build one test-dependency directory per task, from what the repo declares at its base commit.

  env/uvpython/cpython-3.13.14-linux-x86_64-gnu/bin/python3.13 -I tools/build_task_envs.py [ids...]

The public scorer's wheel set (data/raw/wheels) carries only the newest version of each package and
lacks test-only packages (h11, pytest-httpbin, dirty-equals, orjson, ...), so many tasks cannot be
graded with it. For each task this script reads the snapshot's own dependency declarations, in this
order of preference:
  1. uv.lock          -> `uv export --frozen` of the tests group and all extras (exact pins);
  2. requirements-tests.txt / requirements-dev.txt / requirements.txt (`-e .[x]` becomes the
     project's own dependencies with extras x);
  3. poetry pyproject -> main and dev dependency names, pinned to poetry.lock where it has them;
  4. pyproject [project] dependencies, all extras and all dependency groups.
It then runs `uv pip install --target env/taskenvs/<id>` for Python 3.13, with unpinned versions
capped at the task's created_at (`--exclude-newer`), and removes the project's own package from
the target (the sandbox's workspace provides it). If the whole set fails, each requirement is tried
alone and the failures are recorded. One JSON line per task goes to env/taskenvs/report.jsonl.

tools/scorer_env.py adds env/taskenvs/<id> to the task's sandbox venv when --task-envs is given.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY313 = ROOT / "env/py313-scorer/bin/python3.13"
OUT = ROOT / "env/taskenvs"
UV = shutil.which("uv") or str(Path.home() / ".local/bin/uv")
REQ_FILES = ("requirements-tests.txt", "requirements-test.txt", "requirements-dev.txt", "requirements.txt")
SKIP = re.compile(r"^(mypy|ty|ruff|black|pre-commit|prek|coverage|pytest-cov|pytest-sugar|pytest-codspeed|"
                  r"types-.*|mkdocs.*|zensical|playwright|zizmor|codespell|isort|flake8|pylint|build|twine|"
                  r"wheel|asv|ipywidgets|smokeshow|pygithub|cairosvg|pillow|jieba|griffe.*|mdx-include|"
                  r"markdown-include-variants|python-slugify|mkdocstrings.*)$", re.I)


def norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def req_name(line):
    m = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", line)
    return norm(m.group(1)) if m else None


def run(cmd, cwd=None, timeout=900):
    env = dict(os.environ, UV_CACHE_DIR=str(ROOT / "env/cache/uv"), UV_PYTHON_DOWNLOADS="never")
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def project_root(src):
    for cand in [src] + sorted(p for p in src.iterdir() if p.is_dir()):
        if (cand / "pyproject.toml").exists() or (cand / "setup.py").exists():
            return cand
    raise FileNotFoundError("no pyproject.toml or setup.py")


def from_uv_lock(root):
    code, out = run([UV, "export", "--frozen", "--no-hashes", "--no-emit-project", "--no-header",
                     "--no-annotate", "--all-extras", "--group", "tests", "--format", "requirements-txt"], cwd=root)
    if code != 0:   # an older lock with no tests group
        code, out = run([UV, "export", "--frozen", "--no-hashes", "--no-emit-project", "--no-header",
                         "--no-annotate", "--all-extras", "--format", "requirements-txt"], cwd=root)
    if code != 0:
        raise RuntimeError("uv export failed: " + out[-800:])
    return [ln for ln in out.splitlines() if ln.strip() and not ln.startswith(("#", "-e", "."))], True


def expand_req_file(path, root, seen):
    reqs = []
    if path in seen:
        return reqs
    seen.add(path)
    for raw in path.read_text(errors="ignore").splitlines():
        ln = raw.split(" #")[0].strip()
        if not ln or ln.startswith("#"):
            continue
        m = re.match(r"-r\s+(\S+)|--requirement\s+(\S+)", ln)
        if m:
            inc = (path.parent / (m.group(1) or m.group(2))).resolve()
            if inc.exists():
                reqs += expand_req_file(inc, root, seen)
            continue
        m = re.match(r"-e\s+\.(\[[^\]]*\])?$", ln) or re.match(r"\.(\[[^\]]*\])?$", ln)
        if m:
            reqs.append(f"{root}{m.group(1) or ''}")
            continue
        if ln.startswith("-"):
            continue
        reqs.append(ln)
    return reqs


def poetry_reqs(root, py):
    tp = py.get("tool", {}).get("poetry", {})
    names = [n for n, v in tp.get("dependencies", {}).items()
             if n.lower() != "python" and not (isinstance(v, dict) and v.get("optional"))]
    names += list(tp.get("dev-dependencies", {}))
    for g in tp.get("group", {}).values():
        names += list(g.get("dependencies", {}))
    pins = {}
    if (root / "poetry.lock").exists():
        for p in tomllib.loads((root / "poetry.lock").read_text()).get("package", []):
            pins[norm(p["name"])] = p["version"]
    return [f"{n}=={pins[norm(n)]}" if norm(n) in pins else n for n in dict.fromkeys(names)]


def pep621_reqs(root, py):
    proj = py.get("project", {})
    reqs = list(proj.get("dependencies", []))
    for v in proj.get("optional-dependencies", {}).values():
        reqs += v
    for v in py.get("dependency-groups", {}).values():
        reqs += [x for x in v if isinstance(x, str)]
    return reqs


def declared(root):
    """(requirements, source, pinned_by_lock)."""
    py = tomllib.loads((root / "pyproject.toml").read_text()) if (root / "pyproject.toml").exists() else {}
    if (root / "uv.lock").exists():
        reqs, pinned = from_uv_lock(root)
        return reqs, "uv.lock", pinned
    for f in REQ_FILES:
        if (root / f).exists():
            return expand_req_file((root / f).resolve(), root, set()), f, False
    if py.get("tool", {}).get("poetry"):
        return poetry_reqs(root, py), "poetry", False
    return [str(root)] + pep621_reqs(root, py), "pyproject", False


BUILD_HINT = re.compile(r"hint: `([A-Za-z0-9._-]+)` \(v[^)]*\) was included")
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


DROP = ("pytest", "pluggy", "iniconfig", "py", "pytest-timeout")
# Per-task constraints the declarations miss, each with the failure it fixes. Rebuild with --force.
EXTRA_REQS = {
    # httpbin 0.10.0 imports werkzeug.http.parse_authorization_header, removed in werkzeug 3.0
    # (2023-09-30), which the date cap (2023-12-16) would otherwise pick. 2026-11-19, C-004.
    "requests_6592": ["werkzeug<3"],
}
# tests/test_syntax.py in these rich snapshots does `import pkg_resources`; the scorer copy's setuptools
# (84.x) no longer ships it, so the agent's `pytest tests/` failed at collection (R-008 E4B screens,
# 4 of 34 task-draws). Setuptools at the task date still has it. Grading was not affected. 2026-11-19, R-008.
for _iid in ("rich_3006", "rich_3043", "rich_3052", "rich_3061", "rich_3063", "rich_3064", "rich_3067",
             "rich_3105", "rich_3130", "rich_3180"):
    EXTRA_REQS.setdefault(_iid, []).append("setuptools")


def remove_dist(target, name):
    """Delete an installed distribution from a --target dir by its RECORD. True if one was there."""
    hit = False
    for di in list(target.glob("*.dist-info")) if target.exists() else []:
        if norm(di.name[:-len(".dist-info")].rsplit("-", 1)[0]) != name:
            continue
        hit = True
        rec = di / "RECORD"
        for ln in rec.read_text().splitlines() if rec.exists() else []:
            f = (target / ln.split(",")[0]).resolve()
            if f.is_relative_to(target.resolve()) and f.is_file():
                f.unlink()
        shutil.rmtree(di, ignore_errors=True)
    for d in sorted(target.rglob("*"), reverse=True) if hit else []:   # directories left empty
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    return hit


def install(reqs, target, created_at, pinned, workdir):
    """Install under the task-date cap. A compiled package whose dated version has no cp313 wheel
    fails to build from source (old cffi, greenlet, ...); uv names it in a hint, and it alone is then
    exempted from the cap (newest version) and the install retried, up to six times."""
    rf = workdir / "reqs.txt"
    rf.write_text("\n".join(reqs) + "\n")
    exempt = []
    for _ in range(7):
        cmd = [UV, "pip", "install", "--python", str(PY313), "--target", str(target), "--link-mode", "hardlink",
               "--no-progress", "-r", str(rf)]
        if not pinned:
            cmd += ["--exclude-newer", created_at]
            cmd += [a for p in exempt for a in ("--exclude-newer-package", f"{p}={NOW}")]
        code, out = run(cmd)
        m = BUILD_HINT.search(out) if code != 0 and not pinned else None
        if not m or norm(m.group(1)) in exempt:
            return code, out + (f"\n[exempt from date cap: {', '.join(exempt)}]" if exempt else "")
        exempt.append(norm(m.group(1)))
    return code, out


def build(task, force=False):
    iid = task["instance_id"]
    target = OUT / iid
    rec = {"instance_id": iid, "created_at": task["created_at"], "ok": False, "failed": [], "error": None}
    if target.exists() and not force:
        return None
    shutil.rmtree(target, ignore_errors=True)
    t0 = time.time()
    with tempfile.TemporaryDirectory(prefix=f"taskenv_{iid}_", dir=str(ROOT / "env/cache")) as tmp:
        tmp = Path(tmp)
        src = tmp / "src"
        src.mkdir()
        with tarfile.open(ROOT / "data/raw/snapshots" / f"{iid}.tgz") as tf:
            tf.extractall(src, filter="data")
        try:
            root = project_root(src)
            reqs, source, pinned = declared(root)
        except Exception as exc:  # noqa: BLE001
            rec["error"] = f"{type(exc).__name__}: {exc}"[:800]
            return rec
        project = norm(task["repo"].split("/")[-1])
        reqs = [r for r in reqs if req_name(r) != project or r.startswith(str(root))]
        reqs = [r for r in reqs if r.startswith(str(root)) or not SKIP.match(req_name(r) or "")]
        reqs += EXTRA_REQS.get(iid, [])
        rec.update(source=source, pinned=pinned, n_reqs=len(reqs),
                   reqs=[r.replace(str(root), ".") for r in reqs])
        code, out = install(reqs, target, task["created_at"], pinned, tmp)
        m = re.search(r"\[exempt from date cap: ([^\]]*)\]", out)
        rec["exempt_from_date_cap"] = m.group(1).split(", ") if m else []
        if code != 0:
            rec["error"] = out.strip()[-1500:]
            shutil.rmtree(target, ignore_errors=True)
            for r in reqs:   # one at a time, so one bad requirement does not block the rest
                c, o = install([r], target, task["created_at"], pinned, tmp)
                if c != 0:
                    rec["failed"].append({"req": r.replace(str(root), "."), "error": o.strip()[-600:]})
        # the workspace provides the project itself, and the scorer's own pytest must run the tests
        rec["dropped"] = [d for d in (project,) + DROP if remove_dist(target, d)]
        rec["ok"] = target.exists() and not rec["failed"]
        rec["seconds"] = round(time.time() - t0, 1)
        if target.exists():
            rec["packages"] = sorted(p.name[:-len(".dist-info")] for p in target.glob("*.dist-info"))
    return rec


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = [json.loads(ln) for ln in open(ROOT / "data/raw/tasks.jsonl")]
    want = set(a for a in sys.argv[1:] if not a.startswith("-"))
    force = "--force" in sys.argv
    if want:
        tasks = [t for t in tasks if t["instance_id"] in want]
    with open(OUT / "report.jsonl", "a") as rep:
        for t in tasks:
            rec = build(t, force)
            if rec is None:
                continue
            rep.write(json.dumps(rec) + "\n")
            rep.flush()
            fails = ", ".join(f["req"] for f in rec["failed"])
            print(f"{rec['instance_id']:16s} ok={rec['ok']} src={rec.get('source')} n={rec.get('n_reqs')} "
                  f"{rec.get('seconds')}s{' FAILED: ' + fails if fails else ''}"
                  f"{' ERROR: ' + rec['error'][-200:] if rec['error'] and not rec['failed'] and not rec['ok'] else ''}",
                  flush=True)


if __name__ == "__main__":
    main()
