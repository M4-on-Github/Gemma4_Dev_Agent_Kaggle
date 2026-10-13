import json
from pathlib import Path

import analyze_traces as A


def test_wilson_bounds():
    lo, hi = A.wilson(12, 48)
    assert 0.14 < lo < 0.16 and 0.38 < hi < 0.40
    assert A.wilson(0, 0) == (0.0, 0.0)


def test_synthetic_run_metrics(synthetic_run: Path):
    per_task, agg = A.analyze_run(synthetic_run, cap_minutes=4.5, max_calls=45)
    by = {r["task_id"]: r for r in per_task}
    good, bad = by["synth_good"], by["synth_bad"]

    assert good["resolved"] and good["submit_patch_called"] and good["phase_reached"] == "SUBMIT"
    assert good["n_calls"] == 4            # get_status / submit_patch are free
    assert good["n_identical_repeats"] == 0 and good["n_malformed"] == 0
    assert good["output_tokens"] == 1200 and not good["patch_empty"] and not good["scratch_in_patch"]

    assert not bad["resolved"]
    assert bad["n_identical_repeats"] == 2  # three identical greps -> two repeats
    assert bad["n_malformed"] == 1          # unparsed <|tool_call> left in content
    assert bad["n_undeclared_tool"] == 1    # run_skill_script not declared
    assert bad["nudges"] == 1
    assert bad["n_whole_file_reads"] == 1
    assert bad["n_edit_fail"] == 1
    assert bad["overflow_400"] and bad["time_cap_hit"]
    assert bad["scratch_in_patch"]
    assert bad["phase_reached"] == "EDIT"   # inferred: edit_file with no later run_command

    assert agg["tasks"] == 2 and agg["resolved"] == 1
    assert agg["setup_source"] == "measured" and agg["setup_s_used"] == 35.0
    assert abs(agg["projected_12h_total_h"] - (120 + 30 + 268 + 40) * 120 / 2 / 3600) < 1e-9
    assert abs(agg["worst_case_h"] - 120 * (270 + 35) / 3600) < 1e-9
    assert agg["overflow_rate"] == 0.5 and agg["scratch_in_patch_rate"] == 0.5


def test_cli_writes_outputs(synthetic_run: Path, tmp_path: Path, capsys):
    out = tmp_path / "out"
    assert A.main([str(synthetic_run), "--out", str(out), "--cap-minutes", "4.5"]) == 0
    rows = [json.loads(l) for l in (out / "summary.jsonl").read_text().splitlines() if l.strip()]
    assert {r["task_id"] for r in rows} == {"synth_good", "synth_bad"}
    agg = json.loads((out / "aggregates.json").read_text())
    assert agg["resolve_rate"] == 0.5
    assert "resolved 1/2" in capsys.readouterr().out


def test_traces_only_directory(synthetic_run: Path):
    (synthetic_run / "task_results.jsonl").unlink()
    per_task, agg = A.analyze_run(synthetic_run, cap_minutes=None, max_calls=None)
    assert {r["task_id"] for r in per_task} == {"synth_good", "synth_bad"}
    assert agg["worst_case_h"] is None
