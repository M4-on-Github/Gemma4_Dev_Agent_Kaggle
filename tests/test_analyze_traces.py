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


def _turn(i: int, prompt_tokens: int, author: str = "swe_agent") -> dict:
    return {"step_id": i, "source": "agent", "message": "t", "metrics": {"prompt_tokens": prompt_tokens},
            "extra": {"author": author, "event_type": "thinking"}}


def test_token_compaction_detected_from_prompt_drops():
    """D-004 2026-11-05: compaction leaves no trace step, so it is read from a prompt-token drop right after a
    turn at or above R.COMPACTION_TOKEN_THRESHOLD (14,336), per author."""
    thr = A.R.COMPACTION_TOKEN_THRESHOLD
    steps = [
        {"step_id": 0, "source": "user", "message": "task", "extra": {"event_type": "task_prompt"}},
        _turn(1, 3000), _turn(2, 9000), _turn(3, thr + 3), _turn(4, 4700),          # 1: drop after >= thr
        _turn(5, 9000), _turn(6, 8000),                                             # no: drop below thr
        _turn(7, thr), _turn(8, thr - 1),                                           # 2: exactly at thr
        _turn(9, 20000, author="localizer_a"), _turn(10, 4000, author="localizer_b"),   # no: other author
        _turn(11, 3500, author="localizer_a"),                                      # 3: same author drop
        _turn(12, 30000), _turn(13, 30000),                                         # no: equal is not a drop
    ]
    assert A.count_token_compactions(steps) == 3
    m = A.analyze_trace({"steps": steps}, declared=set())
    assert m["compactions"] == 3
    # the old marker rule still counts, and the two are not summed
    marked = steps + [{"step_id": 99, "source": "system", "message": "", "extra": {"event_type": "compaction"}}]
    assert A.analyze_trace({"steps": marked}, declared=set())["compactions"] == 3
