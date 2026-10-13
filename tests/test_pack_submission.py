import zipfile
from pathlib import Path

import pack_submission as P


def test_pack_minimal_is_deterministic(minimal_submission: Path, tmp_path: Path):
    out1, out2 = tmp_path / "a.zip", tmp_path / "b.zip"
    assert P.pack(minimal_submission, out1) == 0
    assert P.pack(minimal_submission, out2) == 0
    assert P.sha256(out1) == P.sha256(out2)
    with zipfile.ZipFile(out1) as zf:
        names = zf.namelist()
        assert "agent.yaml" in names
        assert all(not n.startswith("/") and ".." not in n for n in names)
        assert all(info.file_size > 0 for info in zf.infolist())


def test_pack_ships_only_closure(real_submission_copy: Path, tmp_path: Path):
    out = tmp_path / "s.zip"
    assert P.pack(real_submission_copy, out) == 0
    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())
    assert names == {"agent.yaml", "eval_config.yaml", "prompts/swe_coder.md", "configs/sampling.yaml"}


def test_pack_refuses_invalid(minimal_submission: Path, tmp_path: Path):
    (minimal_submission / "eval_config.yaml").write_text("evaluation:\n  max_time_minutes: 30\n")
    out = tmp_path / "bad.zip"
    assert P.pack(minimal_submission, out) == 1
    assert not out.exists()


def test_pack_copies_hard_links(minimal_submission: Path, tmp_path: Path):
    import os
    src = minimal_submission / "prompts" / "system.md"
    link = minimal_submission / "prompts" / "linked.md"
    os.link(src, link)
    (minimal_submission / "agent.yaml").write_text(
        "name: a\nmodel: gemma-4-31b-it-qat-w4a16-ct\ninstruction: !include prompts/linked.md\n"
        "tools:\n  - run_command\n  - submit_patch\n")
    out = tmp_path / "h.zip"
    assert P.pack(minimal_submission, out, allow_warnings=True) == 0
    with zipfile.ZipFile(out) as zf:
        assert zf.getinfo("prompts/linked.md").file_size == src.stat().st_size
