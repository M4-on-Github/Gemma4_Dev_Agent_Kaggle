"""Synthetic-tree checks for the EXP-056 check-picker script (no repo content, no competition data)."""
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).parent / "candidate-s" / "skills" / "check-picker" / "scripts" / "pick_check.py"


def load(root):
    spec = importlib.util.spec_from_file_location("pick_check_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.ROOT = Path(root).as_posix()
    return mod


def write(root, rel, text=""):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(mod, capsys, monkeypatch, *args):
    monkeypatch.setattr("sys.argv", ["scripts/pick_check.py", *args])
    mod.main()
    out = capsys.readouterr().out
    assert out.endswith("\n") and out.count("\n") == 1, out
    return out.strip()


def make_tree(root):
    write(root, "src/pkg/__init__.py")
    write(root, "src/pkg/_client.py", "def f():\n    return 1\n")
    write(root, "src/pkg/util.py", "def g():\n    return 2\n")
    write(root, "src/pkg/other.py", "def h():\n    return 3\n")
    write(root, "tests/conftest.py", "import pytest\n")
    write(root, "tests/test_client.py", "from pkg import _client\n\ndef test_a():\n    assert _client.f() == 1\n")
    write(root, "tests/test_misc.py", "from pkg import util\n\ndef test_b():\n    assert util.g() == 2\n")


def test_name_match_picks_the_test_of_the_module(tmp_path, capsys, monkeypatch):
    make_tree(tmp_path)
    mod = load(tmp_path)
    assert run(mod, capsys, monkeypatch, "src/pkg/_client.py") == "python -m pytest -q -x tests/test_client.py"


def test_absolute_path_and_comma_list(tmp_path, capsys, monkeypatch):
    make_tree(tmp_path)
    mod = load(tmp_path)
    got = run(mod, capsys, monkeypatch, tmp_path.as_posix() + "/src/pkg/_client.py,src/pkg/other.py")
    assert got == "python -m pytest -q -x tests/test_client.py"


def test_dict_style_and_double_dash_tokens(tmp_path, capsys, monkeypatch):
    make_tree(tmp_path)
    mod = load(tmp_path)
    assert run(mod, capsys, monkeypatch, "--paths", "src/pkg/_client.py") == "python -m pytest -q -x tests/test_client.py"
    assert run(mod, capsys, monkeypatch, "--", "src/pkg/_client.py") == "python -m pytest -q -x tests/test_client.py"


def test_import_match_when_no_name_matches(tmp_path, capsys, monkeypatch):
    make_tree(tmp_path)
    mod = load(tmp_path)
    assert run(mod, capsys, monkeypatch, "src/pkg/util.py") == "python -m pytest -q -x tests/test_misc.py"


def test_import_line_when_no_test_fits(tmp_path, capsys, monkeypatch):
    make_tree(tmp_path)
    mod = load(tmp_path)
    assert run(mod, capsys, monkeypatch, "src/pkg/other.py") == 'python -c "import pkg.other"'


def test_test_with_missing_third_party_import_is_skipped(tmp_path, capsys, monkeypatch):
    make_tree(tmp_path)
    write(tmp_path, "tests/test_client.py", "import zzz_not_installed_anywhere\nfrom pkg import _client\n\ndef test_a():\n    pass\n")
    mod = load(tmp_path)
    assert run(mod, capsys, monkeypatch, "src/pkg/_client.py") == 'python -c "import pkg._client"'


def test_missing_import_in_conftest_is_skipped(tmp_path, capsys, monkeypatch):
    make_tree(tmp_path)
    write(tmp_path, "tests/conftest.py", "import zzz_not_installed_anywhere\n")
    mod = load(tmp_path)
    assert run(mod, capsys, monkeypatch, "src/pkg/_client.py") == 'python -c "import pkg._client"'


def test_indented_import_is_not_a_collection_import(tmp_path, capsys, monkeypatch):
    make_tree(tmp_path)
    write(tmp_path, "tests/test_client.py", "try:\n    import zzz_not_installed_anywhere\nexcept ImportError:\n    pass\nfrom pkg import _client\n")
    mod = load(tmp_path)
    assert run(mod, capsys, monkeypatch, "src/pkg/_client.py") == "python -m pytest -q -x tests/test_client.py"


def test_unusable_paths_give_the_notice_line(tmp_path, capsys, monkeypatch):
    make_tree(tmp_path)
    mod = load(tmp_path)
    for args in (("nope/missing.py",), ("tests/test_client.py",), ("/etc/other.py",), ("../x.py",), ()):
        got = run(mod, capsys, monkeypatch, *args)
        assert got.startswith('python -c "print(') and "check-picker" in got


def test_flat_layout_without_src(tmp_path, capsys, monkeypatch):
    write(tmp_path, "lib1/__init__.py")
    write(tmp_path, "lib1/core.py")
    write(tmp_path, "tests/test_core.py", "from lib1 import core\n")
    mod = load(tmp_path)
    assert run(mod, capsys, monkeypatch, "lib1/core.py") == "python -m pytest -q -x tests/test_core.py"


def test_namespace_src_dir_drops_the_src_prefix(tmp_path, capsys, monkeypatch):
    write(tmp_path, "src/onlymod.py")
    mod = load(tmp_path)
    assert run(mod, capsys, monkeypatch, "src/onlymod.py") == 'python -c "import onlymod"'
