import json
from pathlib import Path

import estimate_budget as E


def test_cap_only_pass_and_block(repo_root: Path, capsys):
    rc = E.main(["--eval-config", str(repo_root / "submission" / "eval_config.yaml")])
    assert rc == 0
    assert "VERDICT: PASS" in capsys.readouterr().out
    rc = E.main(["--cap-minutes", "6"])
    assert rc == 1
    assert "VERDICT: BLOCK" in capsys.readouterr().out


def test_no_cap_blocks(capsys):
    assert E.main([]) == 1
    assert "unbounded" in capsys.readouterr().out


def test_projection_with_rows(tmp_path: Path, capsys):
    rows = [
        {"task_id": "a", "wall_s": 100, "setup_s": 20, "n_calls": 10, "output_tokens": 500, "resolved": True},
        {"task_id": "b", "wall_s": 200, "setup_s": 20, "n_calls": 20, "output_tokens": 1000, "resolved": False},
        {"task_id": "c", "duration_s": 600, "setup_s": 20, "tool_calls": 45, "output_tokens": 9000, "resolved": False},
    ]
    p = tmp_path / "r.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    rc = E.main(["--cap-minutes", "4.5", "--results", str(p), "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["verdict"] == "PASS"
    assert out["setup_source"] == "measured" and abs(out["setup_s_used"] - 20) < 1e-9
    per = {e["task_id"]: e for e in out["per_task"]}
    assert per["c"]["capped"] and per["c"]["est_s"] == 270.0
    # decode model: 0.6*20 + 1000/25.5 = 51.2 s < measured 200 s -> measured wins
    assert per["b"]["est_s"] == 200.0
    assert out["worst_case_h"] == 120 * (270 + 20) / 3600
    assert out["proj_p50_h"] == 120 * (200 + 20) / 3600
