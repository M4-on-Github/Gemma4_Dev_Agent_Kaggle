"""Finds tasks that no agent can ever resolve, without running a container.

Two classes of task are unresolvable by construction on the public evaluation path. Both are
properties of the task and the fixed sandbox, not of the patch an agent writes, so they can be
screened statically -- which matters because a snapshot is ~150MB and there are 129 tasks.

Everything here rests on one fact about grading, verification.py:619-646: the harness runs

    pytest <every file the test_patch touches> --junitxml=... -q

and sets `resolved = test_res.exit_code == 0`. The unit of selection is the *file*, never a
`::node`, and the gate is the exit code of the whole invocation. So a task is graded on every
test in the files its test_patch happens to touch, not only on the tests it adds, and one error
anywhere in one of those files sinks it.

1. ALWAYS-SKIPPED REQUIRED TEST.
   On top of the exit code, verification.py:328-340 fails a task if any *required* node is
   skipped:
       if not has_pass or has_non_pass: return False, 'Required test node did not pass: ...'
   Required nodes come from FAIL_TO_PASS/PASS_TO_PASS, but tasks.jsonl ships neither, so the
   harness falls back to _extract_test_functions_from_patch(test_patch) -- every test the patch
   adds. A test_patch that adds a pair of version-gated alternatives therefore guarantees one
   skip, and the task can never pass. The sandbox is Python 3.13 (Dockerfile.sandbox).

2. MISSING PYTEST PLUGIN, USED ANYWHERE IN A TOUCHED FILE.
   container_setup.py:156-165 skips a fixed set of plugin names when injecting the wheel pool
   into site-packages (`if pkg_norm in skip_base_pkgs: continue`), on the assumption that the
   image already provides them. Dockerfile.sandbox installs only pytest, pytest-timeout, typer
   and the build backends -- so pytest-httpbin, pytest-asyncio and pytest-xdist are in neither
   place, and cannot be added via the pool. A test that requests one of their fixtures errors at
   *setup*, which is a non-zero exit, which fails the task.

   Granularity is what makes this screen correct, and two earlier versions got it wrong:
     - screening on the repo *declaring* the plugin flagged all 13 requests tasks; 5 pass.
     - screening on whether an *added* test requests the fixture flagged 6; the measured count
       was 8.
   The right question is whether ANY test in a touched file requests it, because pytest runs the
   whole file. `requests/tests/test_requests.py` has 135 httpbin-dependent tests, and all 8 tasks
   touching that file fail while all 5 touching `test_utils.py`/`test_adapters.py` (0 such tests)
   pass -- a clean split with no exceptions. That needs the snapshot, to read the other tests in
   the file.

Class 1 needs only tasks.jsonl; class 2 additionally needs a local snapshot.

Usage:
    python tools/screen_tasks.py data/local/tasks.jsonl [--snapshots DIR] [--pyminor 13]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tarfile
from pathlib import Path

SKIP_MARK = re.compile(r"@pytest\.mark\.(skipif|skip)\b")
DEF = re.compile(r"def\s+(test_\w+)")
# A test function with its parameter list. DOTALL so a signature may wrap across lines.
DEF_SIG = re.compile(r"def\s+(test_\w+)\s*\(([^)]*)\)", re.S)
# `+++ b/path` lines name the files pytest will be pointed at.
PATCH_FILE = re.compile(r"^\+\+\+ b/(\S+)", re.M)

# container_setup.py:156 -- never injected from the pool.
SKIP_BASE_PKGS = {
    "pytest",
    "pytest_timeout",
    "pytest_asyncio",
    "pytest_httpbin",
    "pytest_xdist",
    "pluggy",
    "pip",
    "setuptools",
    "wheel",
}
# Dockerfile.sandbox's pip install line, normalized. Anything in SKIP_BASE_PKGS but not here is
# unobtainable: the pool cannot supply it and the image does not have it.
IMAGE_PKGS = {
    "pytest",
    "pytest_timeout",
    "typer",
    "pdm_backend",
    "setuptools",
    "wheel",
    "poetry_core",
    "hatchling",
    "flit_core",
    "editables",
    "pluggy",
    "pip",
}
UNOBTAINABLE = SKIP_BASE_PKGS - IMAGE_PKGS

# The fixtures each unobtainable plugin provides. pytest-xdist contributes nothing here: it adds
# CLI options, not fixtures, and the harness's pytest command passes none of them.
PLUGIN_FIXTURES = {
    "pytest_httpbin": ("httpbin", "httpbin_secure", "httpbin_both"),
    "pytest_asyncio": ("event_loop", "event_loop_policy", "unused_tcp_port", "unused_udp_port"),
}
FIXTURE_OWNER = {
    fixture: plugin
    for plugin, fixtures in PLUGIN_FIXTURES.items()
    if plugin in UNOBTAINABLE
    for fixture in fixtures
}


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "_", name).lower()


def added_lines(patch: str) -> list[str]:
    return [l[1:] for l in patch.splitlines() if l.startswith("+") and not l.startswith("+++")]


def marks_for_tests(patch: str) -> dict[str, str]:
    """Maps each test function the patch adds to the skip marker decorating it, if any."""
    out: dict[str, str] = {}
    pending: list[str] = []
    for line in added_lines(patch):
        s = line.strip()
        # Keep accumulating while a marker's parenthesis is still open (multi-line decorators).
        if SKIP_MARK.search(s) or (
            pending
            and not s.startswith(("def ", "@"))
            and pending[-1].count("(") > pending[-1].count(")")
        ):
            pending.append(s)
            continue
        if s.startswith("@"):
            continue
        m = DEF.search(s)
        if m:
            if pending:
                out[m.group(1)] = " ".join(pending)
            pending = []
    return out


def always_skipped(mark: str, pyminor: int) -> tuple[bool | None, str]:
    """Whether a skip marker is statically certain to fire on this interpreter."""
    if re.search(r"@pytest\.mark\.skip\b(?!if)", mark):
        return True, "unconditional @pytest.mark.skip"

    m = re.search(r"sys\.version_info(?:\.minor|\[1\])\s*(<=|>=|<|>|==|!=)\s*(\d+)", mark)
    if m is not None:
        op, val = m.group(1), int(m.group(2))
        if _holds(pyminor, op, val):
            return True, f"sys.version_info.minor {op} {val} holds on 3.{pyminor}"
        return False, ""

    m = re.search(r"sys\.version_info\s*(<|>=|<=|>)\s*\(\s*3\s*,\s*(\d+)", mark)
    if m is not None:
        op, val = m.group(1), int(m.group(2))
        if _holds(pyminor, op, val):
            return True, f"sys.version_info {op} (3,{val}) holds on 3.{pyminor}"
        return False, ""

    if "platform" in mark:
        return None, "platform-gated; cannot decide statically"
    return None, "skipif condition is not statically decidable"


def _holds(left: int, op: str, right: int) -> bool:
    return {
        "<": left < right,
        "<=": left <= right,
        ">": left > right,
        ">=": left >= right,
        "==": left == right,
        "!=": left != right,
    }[op]


def _fixture_requests(source: str) -> dict[str, str]:
    """Maps each test in `source` that names an unobtainable fixture to the owning plugin."""
    out: dict[str, str] = {}
    for match in DEF_SIG.finditer(source):
        for raw_param in match.group(2).split(","):
            param = raw_param.strip().split(":")[0].split("=")[0].strip().lstrip("*")
            owner = FIXTURE_OWNER.get(param)
            if owner is not None:
                out[match.group(1)] = f"{param} (from {owner})"
    return out


def missing_fixture_uses(patch: str, snapshot: Path) -> dict[str, tuple[int, str]]:
    """Per touched test file, how many of its tests request an unobtainable fixture.

    Reads the file from the snapshot rather than from the patch, because pytest is pointed at the
    whole file: a test the task never mentions still errors at setup and still sets a non-zero
    exit code. The patch's own added lines are scanned too, for tests that do not exist yet.
    """
    targets = {
        path
        for path in PATCH_FILE.findall(patch)
        if path.endswith(".py") and Path(path).name != "conftest.py"
    }
    if not targets:
        return {}

    found: dict[str, tuple[int, str]] = {}
    added = "\n".join(added_lines(patch))
    try:
        with tarfile.open(snapshot, "r:gz") as tf:
            members = {
                member.name.lstrip("./"): member for member in tf.getmembers() if member.isfile()
            }
            for path in sorted(targets):
                source = added
                member = members.get(path)
                if member is not None:
                    fh = tf.extractfile(member)
                    if fh is not None:
                        source = fh.read().decode("utf-8", "replace") + "\n" + added
                hits = _fixture_requests(source)
                if hits:
                    found[path] = (len(hits), sorted(hits.values())[0])
    except (tarfile.TarError, OSError) as exc:
        print(f"  ! could not read {snapshot.name}: {exc}", file=sys.stderr)
    return found


def _required_nodes(test_patch: str) -> list[str]:
    """The harness's own extractor, so the screen agrees with grading by construction."""
    try:
        from swegemma.harness.verification import _extract_test_functions_from_patch
    except ImportError:
        # Same rule, applied locally: every test_* function the patch adds.
        return sorted(set(DEF.findall("\n".join(added_lines(test_patch)))))
    return list(_extract_test_functions_from_patch(test_patch))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("tasks", type=Path)
    ap.add_argument(
        "--snapshots",
        type=Path,
        default=None,
        help="snapshot dir; enables the missing-plugin screen for tasks present there",
    )
    ap.add_argument("--pyminor", type=int, default=13, help="sandbox Python minor version")
    ap.add_argument("--json-out", type=Path, default=None)
    a = ap.parse_args()

    doomed: list[dict] = []
    suspect: list[dict] = []
    clean = 0
    screened_for_plugins = 0

    for line in a.tasks.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        task = json.loads(line)
        instance_id, repo = task["instance_id"], task.get("repo", "")
        patch = task.get("test_patch") or ""
        required = _required_nodes(patch)
        reasons: list[tuple[str, str]] = []
        warnings: list[tuple[str, str]] = []

        marks = marks_for_tests(patch)
        for node in required:
            short = node.split("::")[-1].split("[")[0]
            if short not in marks:
                continue
            verdict, why = always_skipped(marks[short], a.pyminor)
            if verdict:
                reasons.append(("always-skipped-required-test", f"{short}: {why}"))
            elif verdict is None:
                warnings.append(("undecidable-skip", f"{short}: {why}"))

        if a.snapshots is not None:
            snap = a.snapshots / f"{instance_id}.tgz"
            if snap.is_file():
                screened_for_plugins += 1
                for path, (count, example) in missing_fixture_uses(patch, snap).items():
                    reasons.append(
                        (
                            "missing-pytest-plugin",
                            f"pytest is pointed at {path}, in which {count} test(s) request "
                            f"{example}; container_setup's skip_base_pkgs refuses to inject it "
                            f"and the image does not provide it, so setup errors and the exit "
                            f"code is non-zero",
                        )
                    )

        record = {
            "instance_id": instance_id,
            "repo": repo,
            "required_nodes": required,
            "reasons": reasons,
            "warnings": warnings,
        }
        if reasons:
            doomed.append(record)
        elif warnings:
            suspect.append(record)
        else:
            clean += 1

    total = clean + len(doomed) + len(suspect)
    print(
        f"screened {total} tasks  |  clean {clean}  |  "
        f"DOOMED {len(doomed)}  |  SUSPECT {len(suspect)}"
    )
    if a.snapshots is not None:
        print(
            f"missing-plugin screen applied to {screened_for_plugins}/{total} "
            f"(needs a local snapshot)"
        )
    print()

    for label, group in (
        ("DOOMED - unresolvable by construction", doomed),
        ("SUSPECT - needs a run to decide", suspect),
    ):
        if not group:
            continue
        print(f"--- {label} ---")
        for record in group:
            print(f"{record['instance_id']:20} {record['repo']}")
            for kind, why in record["reasons"] + record["warnings"]:
                print(f"    [{kind}] {why}")
        print()

    if a.json_out:
        a.json_out.parent.mkdir(parents=True, exist_ok=True)
        a.json_out.write_text(
            json.dumps({"clean": clean, "doomed": doomed, "suspect": suspect}, indent=2),
            encoding="utf-8",
        )
        print(f"wrote {a.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
