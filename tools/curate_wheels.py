"""Builds a per-task wheel pool whose highest version of each package honours the repo's own pins.

Why this exists
---------------
In Docker mode the harness never populates /wheels. container_setup.setup_container_wheels returns
early when the manager exposes extract_archive_to_container (container_setup.py:407), because
install_test_dependencies instead streams *unpacked* wheels straight into site-packages to avoid a
1.7 GB tar copy per task. The set it streams is _inspect_wheels_dir -> _deduplicate_wheels, which
documents itself as "Selects the highest version wheel per normalized distribution name".

So the grading container's environment is exactly "the highest version of every wheel in
wheels_dir", assembled with no dependency resolution, and the container runs with
network_mode='none' (sandbox/docker.py:86), so nothing can be fetched or corrected afterwards.
sandbox/setup.py would strip constraints anyway (clean_requirement_line -> re.split(r"[=<>!~]")).

The public wheels/ dataset ships 57 starlette versions up to 1.6.0. A fastapi tree pinned to
starlette<0.49 therefore receives 1.6.0 and every router construction dies with
`TypeError: Router.__init__() got an unexpected keyword argument 'on_startup'` -- a failure no
agent's patch could repair, which would make a sound task look broken and corrupt the Q5 answer.

Since selection is "highest wins", the pool itself is the only lever: drop the versions a task
forbids and the harness's own logic then lands on a compatible one. That is what this module does.
It only ever *removes* candidates, so it cannot invent an environment the organizers' pool could
not produce.

Two further consequences of a single global pool, both observed as hard failures:

* **The package under test gets shadowed.** The pool contains a released wheel for every repo in the
  benchmark (fastapi, rich, requests, httpx). Unpacked into site-packages it can win over the
  editable `/workspace` checkout, so the tests grade the *released* library instead of the patched
  one: `httpx_3672` died with `AttributeError: module 'httpx' has no attribute 'Stream'`. We drop the
  distribution under test from the pool entirely.
* **Unrelated pytest plugins auto-load.** A wheel added for one repo is visible to all of them, and
  pytest auto-registers plugins by entry point. `inline_snapshot` (needed by one fastapi task) made
  all four rich tasks fail at `INTERNALERROR` -- its plugin does `import attrs`, which inside the rich
  checkout resolves to rich's own `examples/attrs.py`, which raises `SystemExit`. We therefore keep
  only what the task declares, plus the transitive closure of those declarations and a small
  test-infrastructure allowlist.

Dependency declarations are read from PEP 621 `[project]`, PEP 735 `[dependency-groups]`, Poetry's
`[tool.poetry.dependencies]` / `[tool.poetry.group.*.dependencies]` (including `^`/`~` ranges), and
`requirements*.txt`. rich is Poetry-only, so a `[project]`-only parser silently finds no constraints
at all and curation becomes a no-op.
"""

from __future__ import annotations

import os
import re
import tarfile
from pathlib import Path

import zipfile

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

try:
    import tomllib
except ImportError:  # pragma: no cover - orchestrator is 3.12
    tomllib = None

# Docs toolchains pull a large, irrelevant dependency tree (and their pins fight the test deps).
# The harness globs requirements*.txt indiscriminately; we only care about what tests import.
_SKIP_REQ_FILES = re.compile(r"requirements-(docs|translations|github-actions)", re.I)

# Test plumbing that must exist even when a repo never names it. Deliberately minimal: anything
# else present but undeclared is dropped, because an undeclared pytest plugin auto-loads and can
# break an unrelated repo (see module docstring).
_INFRA = {
    "pytest", "pluggy", "iniconfig", "packaging", "tomli", "exceptiongroup", "py",
    "setuptools", "wheel", "pip", "typing_extensions", "pytest_timeout", "colorama",
}

# Empirically confirmed pins: the pool's highest version wins by construction, but for these
# names the highest version renders/behaves differently from what the gold patch's own tests
# were authored against, and no repo-declared constraint rules it out on its own. Found by
# gold-control sweeps (experiments/README.md class B); applied by default so every sweep gets
# them without remembering a --pin flag. A caller's own --pin for the same name still wins.
DEFAULT_OVERRIDES = {
    "pygments": "==2.20.0",  # 2.21.0 shifts ANSI truecolor output in rich's syntax/markdown tests
}


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "_", name).lower()


def _wheel_name_version(filename: str) -> tuple[str, str] | None:
    if not filename.endswith(".whl"):
        return None
    parts = filename[:-4].split("-")
    if len(parts) < 2:
        return None
    return normalize(parts[0]), parts[1]



def wheel_is_importable(filename: str, py_minor: int = 13) -> bool:
    """Whether unpacking this wheel into a cp3{py_minor} linux site-packages yields a usable module.

    The harness never checks a wheel's tags: _deduplicate_wheels picks the highest version per
    name, full stop. The public pool ships cp312 *and* cp313 builds of the same packages, and for
    three of them the cp312 build has the higher version -- charset_normalizer 3.5.1 (cp312) beats
    3.4.9 (cp313), sqlalchemy 2.0.52 beats 2.0.51. Unpacked into the 3.13 sandbox, the cp312
    extension module simply is not importable, which surfaces far from the cause: requests' own
    conftest dies with `ModuleNotFoundError: No module named 'charset_normalizer'` even though the
    wheel is right there in the pool. So compatibility has to be checked before version order.
    """
    if not filename.endswith(".whl"):
        return False
    parts = filename[:-4].split("-")
    if len(parts) < 5:
        # Fewer than name-version-py-abi-platform: not a tag we can read, so do not exclude it.
        return True
    py_tags, abi_tag, platform_tag = parts[-3], parts[-2], parts[-1]

    if not any(plat == "any" or "manylinux" in plat or plat == "linux_x86_64"
               for plat in platform_tag.split(".")):
        return False

    for tag in py_tags.split("."):
        if tag in ("py2", "py3") or tag == f"py3{py_minor}" or tag == f"cp3{py_minor}":
            return True
        # An abi3 wheel built for an older CPython stays importable on newer ones.
        if abi_tag == "abi3" and tag.startswith("cp3"):
            try:
                if int(tag[3:] or 0) <= py_minor:
                    return True
            except ValueError:
                pass
    return False


def _poetry_spec(raw: str) -> str:
    """Translates Poetry's caret/tilde shorthand into PEP 440, which SpecifierSet can parse.

    Poetry is not PEP 508: `^1.2.3` means >=1.2.3,<2.0.0 and `~1.2.3` means >=1.2.3,<1.3.0. Caret
    also special-cases leading zeros (`^0.2.3` -> <0.3.0, `^0.0.3` -> <0.0.4). Left untranslated,
    these parse as nothing and every Poetry repo silently gets an unconstrained pool.
    """
    raw = raw.strip()
    m = re.match(r"^([\^~])\s*([0-9][0-9.]*)$", raw)
    if not m:
        return raw
    op, ver = m.group(1), m.group(2)
    parts = [int(x) for x in ver.split(".") if x != ""]
    while len(parts) < 3:
        parts.append(0)
    major, minor, patch = parts[0], parts[1], parts[2]
    if op == "~":
        upper = f"{major}.{minor + 1}.0"
    elif major > 0:
        upper = f"{major + 1}.0.0"
    elif minor > 0:
        upper = f"0.{minor + 1}.0"
    else:
        upper = f"0.0.{patch + 1}"
    return f">={ver},<{upper}"


def _walk_poetry_deps(table: dict, add) -> None:
    """Feeds a [tool.poetry...dependencies] table to `add`, handling both string and table values."""
    for name, value in (table or {}).items():
        if name.lower() == "python":
            continue
        if isinstance(value, str):
            spec = _poetry_spec(value)
        elif isinstance(value, dict):
            spec = _poetry_spec(str(value.get("version", "")))
        elif isinstance(value, list):
            # Multiple constraints (per-platform); intersecting them is unsafe, so take none.
            spec = ""
        else:
            spec = ""
        add(f"{name}{spec}" if spec else name)


def dist_under_test(repo: str, instance_id: str) -> str:
    """Normalized distribution name of the repo being graded, which must never come from the pool."""
    short = (repo or "").rsplit("/", 1)[-1]
    if not short:
        short = (instance_id or "").rsplit("_", 1)[0]
    return normalize(short)


def _wheel_requires(wheel: Path) -> set[str]:
    """Base (non-extra) Requires-Dist names declared by a wheel's METADATA."""
    out: set[str] = set()
    try:
        with zipfile.ZipFile(wheel) as zf:
            meta = next((n for n in zf.namelist()
                         if n.endswith(".dist-info/METADATA")), None)
            if meta is None:
                return out
            for line in zf.read(meta).decode("utf-8", "replace").splitlines():
                if not line.startswith("Requires-Dist:"):
                    continue
                raw = line.split(":", 1)[1].strip()
                # Skip deps gated behind an extra: they are optional by definition.
                if ";" in raw and "extra ==" in raw:
                    continue
                m = re.match(r"^([A-Za-z0-9._-]+)", raw)
                if m:
                    out.add(normalize(m.group(1)))
    except Exception:
        pass
    return out


def collect_constraints(snapshot_tgz: Path) -> tuple[dict[str, SpecifierSet], set[str]]:
    """Intersects every version constraint the repo declares, and records every name it declares.

    Returns (constraints, declared_names). The name set matters as much as the constraints: the pool
    is restricted to it, so an undeclared package cannot leak in and auto-load as a pytest plugin.
    """
    out: dict[str, SpecifierSet] = {}
    declared: set[str] = set()

    def add(req_line: str) -> None:
        line = re.sub(r";.*$", "", req_line).strip()
        if not line or line.startswith(("#", "-", "git+")):
            return
        m = re.match(r"^([A-Za-z0-9._-]+)\s*(?:\[[^\]]*\])?\s*(.*)$", line)
        if not m:
            return
        name, spec_txt = normalize(m.group(1)), m.group(2).strip()
        declared.add(name)
        if not spec_txt:
            return
        try:
            spec = SpecifierSet(spec_txt)
        except InvalidSpecifier:
            return
        out[name] = out[name] & spec if name in out else spec

    with tarfile.open(snapshot_tgz) as tf:
        for member in tf.getnames():
            if member.count("/") > 2:
                continue
            base = os.path.basename(member)
            if base == "pyproject.toml" and tomllib is not None:
                fh = tf.extractfile(member)
                if fh is None:
                    continue
                try:
                    data = tomllib.loads(fh.read().decode("utf-8", "replace"))
                except Exception:
                    continue
                project = data.get("project", {}) or {}
                for dep in project.get("dependencies", []) or []:
                    add(dep)
                for group in (project.get("optional-dependencies", {}) or {}).values():
                    for dep in group or []:
                        add(dep)
                for group in (data.get("dependency-groups", {}) or {}).values():
                    for dep in group or []:
                        if isinstance(dep, str):
                            add(dep)
                # Poetry: rich and many others declare nothing under [project] at all.
                poetry = (data.get("tool", {}) or {}).get("poetry", {}) or {}
                _walk_poetry_deps(poetry.get("dependencies", {}), add)
                _walk_poetry_deps(poetry.get("dev-dependencies", {}), add)
                for grp in (poetry.get("group", {}) or {}).values():
                    _walk_poetry_deps((grp or {}).get("dependencies", {}), add)
            elif re.fullmatch(r"(test-)?requirements.*\.txt", base) and not _SKIP_REQ_FILES.search(base):
                fh = tf.extractfile(member)
                if fh is None:
                    continue
                for line in fh.read().decode("utf-8", "replace").splitlines():
                    add(line)
    return out, declared


def curate(
    pool: Path,
    snapshot_tgz: Path,
    out_dir: Path,
    *,
    repo: str = "",
    instance_id: str = "",
    supplemental: set[str] | None = None,
    extra_pool: Path | None = None,
    overrides: dict[str, str] | None = None,
    py_minor: int = 13,
) -> dict[str, object]:
    """Links pool wheels into out_dir, honouring the task's pins and keeping only what it declares.

    Returns a report describing what was narrowed, dropped and left unsatisfiable, so a run log can
    show exactly why a task's environment differs from the raw pool.
    """
    constraints, declared = collect_constraints(snapshot_tgz)
    # An override replaces the declared range outright. Needed because a repo's own pins can be
    # too loose to reproduce its snapshots: rich allows pygments ^2.13.0 and the pool ships both
    # 2.20.0 and 2.21.0, but only 2.20.0 renders the colours test_syntax asserts on. The right
    # version is not derivable from the metadata -- it is found by running -- so it is recorded
    # here rather than inferred.
    overridden: list[str] = []
    merged_overrides = {**DEFAULT_OVERRIDES, **(overrides or {})}
    for raw_name, raw_spec in merged_overrides.items():
        name = normalize(raw_name)
        constraints[name] = SpecifierSet(raw_spec)
        overridden.append(f'{name}{raw_spec}')
    under_test = dist_under_test(repo, instance_id)
    supplemental = {normalize(n) for n in (supplemental or set())}

    # Both directories are wheel sources. `supplemental` only says which names are *gated*;
    # without scanning extra_pool for files too, a wheel added there is silently invisible
    # and the task fails with a missing module that the report shows as neither kept nor
    # dropped. A later source wins a filename collision.
    sources: dict[str, Path] = {}
    for src in (pool, extra_pool):
        if src is None or not src.is_dir():
            continue
        for filename in os.listdir(src):
            if filename.endswith(".whl"):
                sources[filename] = src / filename

    grouped: dict[str, list[tuple[Version, str]]] = {}
    unparsed: list[str] = []
    for filename in sources:
        nv = _wheel_name_version(filename)
        if nv is None:
            continue
        name, raw_version = nv
        try:
            grouped.setdefault(name, []).append((Version(raw_version), filename))
        except InvalidVersion:
            unparsed.append(filename)

    # Drop wheels that cannot be imported on the sandbox interpreter *before* version order is
    # applied, since the harness's own pick is a pure max() over versions. Only drop when a
    # compatible build of the same name survives: if every candidate is incompatible the wheel
    # is all the task has, and removing it turns a version problem into a missing module.
    abi_filtered: list[str] = []
    for name, candidates in grouped.items():
        usable = [c for c in candidates if wheel_is_importable(c[1], py_minor)]
        if usable and len(usable) != len(candidates):
            for _, filename in candidates:
                if not wheel_is_importable(filename, py_minor):
                    abi_filtered.append(filename)
            grouped[name] = usable

    # Transitive closure of the declarations, so a declared package still gets its own
    # dependencies even though the repo never names them directly. Only `supplemental` wheels are
    # gated on this: the organizers' own pool is injected wholesale by the harness, and dropping
    # from it diverges from grading -- rich's tests `import attr` without declaring attrs anywhere,
    # so a declaration-only pool breaks a task that the real pool handles fine.
    keep: set[str] = set()
    if supplemental:
        queue = [n for n in declared if n in grouped] + [n for n in _INFRA if n in grouped]
        while queue:
            current = queue.pop()
            if current in keep:
                continue
            keep.add(current)
            _, newest = max(grouped[current])
            for dep in _wheel_requires(sources[newest]):
                if dep in grouped and dep not in keep:
                    queue.append(dep)

    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.iterdir():
        stale.unlink()

    def link(filename: str) -> None:
        src, dst = sources[filename], out_dir / filename
        try:
            os.link(src, dst)
        except OSError:
            dst.write_bytes(src.read_bytes())

    narrowed: list[str] = []
    unsatisfiable: list[str] = []
    dropped_undeclared: list[str] = []
    kept = 0
    for name, candidates in grouped.items():
        # Never ship the library being graded: unpacked into site-packages it can shadow the
        # editable /workspace checkout and the tests then grade the released version instead.
        if name == under_test:
            continue
        # A wheel we added from PyPI is only safe where the task actually wants it: pytest
        # auto-registers plugins by entry point, so an undeclared one runs in every repo.
        # inline_snapshot (added for one fastapi task) broke all four rich tasks that way.
        if name in supplemental and name not in keep:
            dropped_undeclared.append(name)
            continue

        spec = constraints.get(name)
        allowed = candidates
        if spec is not None:
            # prereleases=True: a pool pinned to e.g. a release candidate must stay reachable.
            allowed = [c for c in candidates if spec.contains(str(c[0]), prereleases=True)]
            if not allowed:
                # Keep the raw pool's choice rather than removing the package outright: a missing
                # module is a harsher, less informative failure than a version mismatch.
                unsatisfiable.append(f"{name}{spec}")
                allowed = candidates
            elif len(allowed) != len(candidates):
                best, worst_dropped = max(allowed)[0], max(candidates)[0]
                if best != worst_dropped:
                    narrowed.append(f"{name}: {worst_dropped} -> {best} ({spec})")

        # The harness takes the highest version per name, so only that one can ever be used.
        # Linking the single winner keeps the pool small and makes the chosen env auditable.
        link(max(allowed)[1])
        kept += 1

    for filename in unparsed:
        link(filename)

    return {
        "kept": kept,
        "overridden": sorted(overridden),
        "constraints": len(constraints),
        "declared": len(declared),
        "under_test": under_test,
        "narrowed": sorted(narrowed),
        "unsatisfiable": sorted(unsatisfiable),
        "dropped_undeclared": sorted(dropped_undeclared),
        "abi_filtered": sorted(abi_filtered),
    }
