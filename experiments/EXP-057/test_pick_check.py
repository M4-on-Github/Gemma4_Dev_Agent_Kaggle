"""Synthetic-tree checks for the EXP-057 check-picker (no repo content, no competition data).

The workspace is always a temp directory that is NOT at /workspace. Two ways of running the script:
in process (cwd somewhere else, PYTHONPATH naming the workspace) and as a child process that
copies the skill harness's wrapper: a file inside the workspace, started with the workspace as
the working directory and PYTHONPATH set to it, which then changes into a temporary directory and
runs the script with runpy (adk skill_toolset.py:617-662, swegemma sandbox/subprocess.py:485-498,
adk_eval_core sandbox/base.py:201-205).
"""
import importlib.util
import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent / "candidate-f" / "skills" / "check-picker" / "scripts" / "pick_check.py"

WRAPPER = textwrap.dedent(
    """\
    import os, tempfile, sys, runpy
    _src = {src!r}
    def _go():
        _orig_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as td:
            os.makedirs(os.path.join(td, "scripts"))
            with open(os.path.join(td, "scripts", "pick_check.py"), "w") as f:
                f.write(_src)
            os.chdir(td)
            sys.argv = {argv!r}
            try:
                try:
                    runpy.run_path("scripts/pick_check.py", run_name="__main__")
                except SystemExit as e:
                    if e.code is not None and e.code != 0:
                        raise e
            finally:
                os.chdir(_orig_cwd)
    _go()
    """
)


def load():
    spec = importlib.util.spec_from_file_location("pick_check_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write(root, rel, text=""):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_tree(root):
    write(root, "src/pkg/__init__.py")
    write(root, "src/pkg/_client.py", "def f():\n    return 1\n")
    write(root, "src/pkg/util.py", "def g():\n    return 2\n")
    write(root, "src/pkg/other.py", "def h():\n    return 3\n")
    write(root, "tests/conftest.py", "import pytest\n")
    write(root, "tests/test_client.py", "from pkg import _client\n\ndef test_a():\n    assert _client.f() == 1\n")
    write(root, "tests/test_misc.py", "from pkg import util\n\ndef test_b():\n    assert util.g() == 2\n")
    old = time.time() - 5000
    for p in Path(root).rglob("*.py"):
        os.utime(p, (old, old))


@pytest.fixture
def ws(tmp_path):
    root = tmp_path / "work" / "workspace"
    root.mkdir(parents=True)
    make_tree(root)
    assert str(root) != "/workspace"
    return root


def run_in_process(ws, tmp_path, capsys, monkeypatch, *args):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir(exist_ok=True)
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("PYTHONPATH", str(ws))
    monkeypatch.setattr("sys.argv", ["scripts/pick_check.py", *args])
    load().main()
    out = capsys.readouterr().out
    assert out.endswith("\n") and out.count("\n") == 1, out
    return out.strip()


def run_like_harness(ws, argv_tail, pythonpath=True):
    code = WRAPPER.format(src=SCRIPT.read_text(encoding="utf-8"), argv=["scripts/pick_check.py", *argv_tail])
    wrapper = Path(ws) / ".adk_exec_test.py"
    wrapper.write_text(code, encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    if pythonpath:
        env["PYTHONPATH"] = str(ws)
    try:
        res = subprocess.run(
            [sys.executable, str(wrapper)], cwd=str(ws), env=env, capture_output=True, text=True, timeout=60
        )
    finally:
        wrapper.unlink()
    assert res.returncode == 0, res.stderr
    assert res.stderr == "", res.stderr
    assert res.stdout.endswith("\n") and res.stdout.count("\n") == 1, res.stdout
    return res.stdout.strip()


PICK_CLIENT = "python -m pytest -q -x tests/test_client.py"


def test_harness_wrapper_with_pythonpath(ws):
    assert run_like_harness(ws, ["src/pkg/_client.py"]) == PICK_CLIENT


def test_harness_wrapper_without_pythonpath_uses_first_sys_path_entry(ws):
    assert run_like_harness(ws, ["src/pkg/_client.py"], pythonpath=False) == PICK_CLIENT


def test_harness_wrapper_empty_args_uses_newest_file(ws):
    os.utime(ws / "src/pkg/util.py", None)
    assert run_like_harness(ws, []) == "python -m pytest -q -x tests/test_misc.py"


def test_run_directly_with_workspace_as_cwd_only(ws):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "src/pkg/_client.py"], cwd=str(ws), env=env, capture_output=True, text=True
    )
    assert res.returncode == 0 and res.stdout.strip() == PICK_CLIENT, (res.stdout, res.stderr)


def test_list_shape_and_absolute_and_literal_prefixes(ws, tmp_path, capsys, monkeypatch):
    assert run_in_process(ws, tmp_path, capsys, monkeypatch, "src/pkg/_client.py") == PICK_CLIENT
    assert run_in_process(ws, tmp_path, capsys, monkeypatch, ws.as_posix() + "/src/pkg/_client.py") == PICK_CLIENT
    assert run_in_process(ws, tmp_path, capsys, monkeypatch, "/workspace/src/pkg/_client.py") == PICK_CLIENT
    assert run_in_process(ws, tmp_path, capsys, monkeypatch, "./src/pkg/_client.py") == PICK_CLIENT
    assert run_in_process(ws, tmp_path, capsys, monkeypatch, "src/pkg/_client.py", "src/pkg/other.py") == PICK_CLIENT


def test_dict_shapes_long_short_and_positional(ws, tmp_path, capsys, monkeypatch):
    # args as a dict: --key value; short_options: -k value; positional_args: after a bare --
    assert run_in_process(ws, tmp_path, capsys, monkeypatch, "--paths", "src/pkg/_client.py") == PICK_CLIENT
    assert run_in_process(ws, tmp_path, capsys, monkeypatch, "--files", "['src/pkg/_client.py', 'src/pkg/other.py']") == PICK_CLIENT
    assert run_in_process(ws, tmp_path, capsys, monkeypatch, "-p", "src/pkg/_client.py") == PICK_CLIENT
    assert run_in_process(ws, tmp_path, capsys, monkeypatch, "--", "src/pkg/_client.py") == PICK_CLIENT
    assert run_in_process(ws, tmp_path, capsys, monkeypatch, "--paths", "x", "--", "src/pkg/_client.py") == PICK_CLIENT
    assert run_like_harness(ws, ["--files", "['src/pkg/_client.py']", "--", "src/pkg/_client.py"]) == PICK_CLIENT


def test_empty_args_fall_back_to_the_newest_source_file(ws, tmp_path, capsys, monkeypatch):
    os.utime(ws / "src/pkg/util.py", None)
    assert run_in_process(ws, tmp_path, capsys, monkeypatch) == "python -m pytest -q -x tests/test_misc.py"


def test_unusable_args_fall_back_too(ws, tmp_path, capsys, monkeypatch):
    os.utime(ws / "src/pkg/_client.py", None)
    for args in (("nope/missing.py",), ("tests/test_client.py",), ("/etc/other.py",), ("../x.py",)):
        assert run_in_process(ws, tmp_path, capsys, monkeypatch, *args) == PICK_CLIENT


def test_recent_window_keeps_only_files_near_the_newest(ws, tmp_path, capsys, monkeypatch):
    os.utime(ws / "src/pkg/util.py", None)
    mod = load()
    monkeypatch.setenv("PYTHONPATH", str(ws))
    mod.ROOT = str(ws)
    assert mod.newest_sources() == ["src/pkg/util.py"]
    now = time.time()
    os.utime(ws / "src/pkg/_client.py", (now - 30, now - 30))
    assert mod.newest_sources() == ["src/pkg/util.py", "src/pkg/_client.py"]


def test_dot_files_and_test_files_are_not_newest_sources(ws, tmp_path, capsys, monkeypatch):
    os.utime(ws / "src/pkg/util.py", (time.time() - 60, time.time() - 60))
    write(ws, ".adk_exec_abc.py", "x = 1\n")
    write(ws, "tests/test_new.py", "x = 1\n")
    mod = load()
    mod.ROOT = str(ws)
    assert mod.newest_sources() == ["src/pkg/util.py"]
    assert run_in_process(ws, tmp_path, capsys, monkeypatch) == "python -m pytest -q -x tests/test_misc.py"


def test_no_python_files_gives_the_notice_line(tmp_path):
    empty = tmp_path / "empty_ws"
    empty.mkdir()
    write(empty, "README.md", "text\n")
    for args in ([], ["src/nothing.py"]):
        got = run_like_harness(empty, args)
        assert got.startswith('python -c "print(') and "check-picker" in got


def test_import_line_when_no_test_fits(ws, tmp_path, capsys, monkeypatch):
    assert run_in_process(ws, tmp_path, capsys, monkeypatch, "src/pkg/other.py") == 'python -c "import pkg.other"'


def test_import_match_when_no_name_matches(ws, tmp_path, capsys, monkeypatch):
    assert run_in_process(ws, tmp_path, capsys, monkeypatch, "src/pkg/util.py") == "python -m pytest -q -x tests/test_misc.py"


def test_test_with_missing_third_party_import_is_skipped(ws, tmp_path, capsys, monkeypatch):
    write(ws, "tests/test_client.py", "import zzz_not_installed_anywhere\nfrom pkg import _client\n")
    assert run_in_process(ws, tmp_path, capsys, monkeypatch, "src/pkg/_client.py") == 'python -c "import pkg._client"'


def test_missing_import_in_conftest_is_skipped(ws, tmp_path, capsys, monkeypatch):
    write(ws, "tests/conftest.py", "import zzz_not_installed_anywhere\n")
    assert run_in_process(ws, tmp_path, capsys, monkeypatch, "src/pkg/_client.py") == 'python -c "import pkg._client"'


def test_indented_import_is_not_a_collection_import(ws, tmp_path, capsys, monkeypatch):
    write(ws, "tests/test_client.py", "try:\n    import zzz_not_installed_anywhere\nexcept ImportError:\n    pass\nfrom pkg import _client\n")
    assert run_in_process(ws, tmp_path, capsys, monkeypatch, "src/pkg/_client.py") == PICK_CLIENT


def test_flat_layout_without_src(tmp_path, capsys, monkeypatch):
    root = tmp_path / "flat"
    write(root, "lib1/__init__.py")
    write(root, "lib1/core.py")
    write(root, "tests/test_core.py", "from lib1 import core\n")
    assert run_in_process(root, tmp_path, capsys, monkeypatch, "lib1/core.py") == "python -m pytest -q -x tests/test_core.py"


def test_namespace_src_dir_drops_the_src_prefix(tmp_path, capsys, monkeypatch):
    root = tmp_path / "ns"
    write(root, "src/onlymod.py")
    assert run_in_process(root, tmp_path, capsys, monkeypatch, "src/onlymod.py") == 'python -c "import onlymod"'


def test_fixed_root_constant_is_never_the_only_root(ws, tmp_path, capsys, monkeypatch):
    # the EXP-056 defect: a script that looked only at the literal root saw an empty tree here
    assert not os.path.isdir("/workspace") or os.path.realpath("/workspace") != os.path.realpath(str(ws))
    assert run_in_process(ws, tmp_path, capsys, monkeypatch, "src/pkg/_client.py") == PICK_CLIENT


def test_script_has_no_forbidden_calls():
    text = SCRIPT.read_text(encoding="utf-8")
    for word in ("subprocess", "os.system", "socket", "urllib", "requests", "shutil", "popen", "git "):
        assert word not in text, word
    assert "open(" in text and "'w'" not in text and '"w"' not in text and '"a"' not in text
