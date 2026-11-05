import ast
import json
from pathlib import Path

import pytest

import build_notebook as B


def _code_cells(nb_path: Path) -> list[str]:
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    return ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]


def test_unquoted_string_override_is_refused(tmp_path: Path):
    """EXP-030 2026-11-05: --set EXP_ID=EXP-030-p1 (unquoted) killed the kernel in cell 1 with a SyntaxError."""
    out = tmp_path / "nb.ipynb"
    with pytest.raises(SystemExit) as exc:
        B.main(["--set", "EXP_ID=EXP-030-p1", "--out", str(out)])
    assert "EXP_ID=EXP-030-p1" in str(exc.value)
    assert not out.exists()


def test_bare_name_override_is_refused(tmp_path: Path):
    """A bare identifier parses but would raise NameError on Kaggle; it is not a literal."""
    out = tmp_path / "nb.ipynb"
    with pytest.raises(SystemExit) as exc:
        B.main(["--set", "EXP_ID=p1", "--out", str(out)])
    assert "EXP_ID=p1" in str(exc.value)
    assert not out.exists()


def test_unbalanced_override_is_refused(tmp_path: Path):
    with pytest.raises(SystemExit) as exc:
        B.main(["--set", "TASK_IDS=['a', 'b'", "--out", str(tmp_path / "nb.ipynb")])
    assert "TASK_IDS" in str(exc.value)


def test_cell_parse_check_names_the_offending_set():
    text = "# %%\nA = 1\nB = 2\n"
    broken = text.replace("B = 2", "B = (2   # overridden by --set")
    with pytest.raises(SystemExit) as exc:
        B.check_cells_parse(broken, ["A", "B"])
    assert "--set B" in str(exc.value)


def test_existing_invocations_still_build(tmp_path: Path, repo_root: Path):
    """Quoted strings, booleans, ints and the --cohort id list all pass, and every code cell that carries an
    override parses."""
    out = tmp_path / "nb.ipynb"
    rc = B.main(["--cohort", str(repo_root / "experiments" / "cohorts" / "smoke-8.txt"),
                 "--set", 'EXP_ID="EXP-030-p1"', "--set", "RUN_GOLD_CONTROL=False",
                 "--set", "MEASURE_DECODE_SPEED=True", "--set", "MODEL_NAME='gemma-4-e2b-it-qat-w4a16-ct'",
                 "--out", str(out)])
    assert rc == 0
    cells = _code_cells(out)
    param = next(c for c in cells if "# overridden by --set" in c)
    ast.parse(param)
    assert 'EXP_ID = "EXP-030-p1"   # overridden by --set' in param
    assert "RUN_GOLD_CONTROL = False   # overridden by --set" in param
    assert "N_TASKS = 8   # overridden by --set" in param
