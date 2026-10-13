from pathlib import Path

import check_repo_hygiene as H


def test_rules(tmp_path: Path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "tasks.jsonl").write_text("{}")
    (tmp_path / "submission").mkdir()
    (tmp_path / "submission" / "run.sh").write_text("x")
    (tmp_path / "big.txt").write_bytes(b"0" * (5 * 1024 * 1024 + 1))
    fake_key = "0123456789abcdef" * 2   # built at runtime so this test file itself passes the hygiene scan
    (tmp_path / "secret.py").write_text('cfg = {"username": "u", "key": "%s"}\n' % fake_key)
    (tmp_path / "ok.md").write_text("fine\n")
    assert H.check_path(tmp_path, "data/tasks.jsonl")
    assert H.check_path(tmp_path, "submission/run.sh")
    assert H.check_path(tmp_path, "big.txt")
    assert H.check_path(tmp_path, "secret.py")
    assert H.check_path(tmp_path, "kaggle.json")
    assert H.check_path(tmp_path, "runs/EXP-001/traces/trace_x.json")
    assert H.check_path(tmp_path, "model.safetensors")
    assert not H.check_path(tmp_path, "ok.md")
    assert not H.check_path(tmp_path, "experiments/EXP-001/summary.jsonl")
    assert not H.check_path(tmp_path, "tests/fixtures/x.jsonl")
    assert H.check_path(tmp_path, "notebooks/out.jsonl")


def test_repo_tracked_files_are_clean(repo_root: Path):
    assert H.main(["--all", "--repo", str(repo_root)]) == 0
