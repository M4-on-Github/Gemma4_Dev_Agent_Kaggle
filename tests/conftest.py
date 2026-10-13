import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

MINIMAL_PROMPT = (
    "You are swe_coder. Use run_command, read_file, edit_file, write_file, get_status and submit_patch. "
    "Scratch files go to /tmp. Submit before the budget ends.\n"
)


@pytest.fixture
def repo_root() -> Path:
    return ROOT


@pytest.fixture
def minimal_submission(tmp_path: Path) -> Path:
    """A tiny valid submission directory built from scratch (independent of submission/)."""
    sub = tmp_path / "sub"
    (sub / "prompts").mkdir(parents=True)
    (sub / "configs").mkdir()
    (sub / "agent.yaml").write_text(
        "name: swe_coder\nmodel: gemma-4-31b-it-qat-w4a16-ct\n"
        "instruction: !include prompts/system.md\n"
        "generate_content_config: !include configs/sampling.yaml\n"
        "tools:\n  - run_command\n  - read_file\n  - edit_file\n  - write_file\n  - get_status\n  - submit_patch\n",
        encoding="utf-8")
    (sub / "prompts" / "system.md").write_text(MINIMAL_PROMPT, encoding="utf-8")
    (sub / "configs" / "sampling.yaml").write_text(
        "temperature: 0.2\ntop_p: 0.95\ntop_k: 64\nmax_output_tokens: 4096\n"
        "thinking_config:\n  include_thoughts: false\n", encoding="utf-8")
    (sub / "eval_config.yaml").write_text(
        "evaluation:\n  max_time_minutes: 4.5\n  max_tool_calls: 45\n  max_turns: 70\n  timeout_seconds: 300\n",
        encoding="utf-8")
    return sub


@pytest.fixture
def real_submission_copy(tmp_path: Path, repo_root: Path) -> Path:
    dest = tmp_path / "submission"
    shutil.copytree(repo_root / "submission", dest)
    return dest


def make_step(step_id: int, source: str, message: str, tool: str | None = None, args: dict | None = None,
              observation: str | None = None, extra: dict | None = None) -> dict:
    step = {"step_id": step_id, "source": source, "message": message, "extra": extra or {}}
    if tool is not None:
        step["tool_calls"] = [{"tool_call_id": f"call_{step_id}", "function_name": tool, "arguments": args or {},
                               "extra": {"elapsed_s": 1.0}}]
        step["observation"] = {"content": observation or '{"status": "ok"}'}
    return step


@pytest.fixture
def synthetic_run(tmp_path: Path) -> Path:
    """A fake run directory in the official layout with two tasks: one resolved, one that spun and overflowed."""
    run = tmp_path / "run"
    (run / "traces").mkdir(parents=True)
    good = {
        "schema_version": "ATIF-v1.5", "agent": {"name": "swegemma", "version": "0.2.7"},
        "steps": [
            make_step(1, "system", "prompt"),
            make_step(2, "user", "You are evaluating a software engineering task for repository synthetic/repo."),
            make_step(3, "agent", "[phase=LOCATE calls=0/45 edits=0 submitted=no] searching", "run_command",
                      {"command": "git grep -n foo -- '*.py' | head -n 40"}),
            make_step(4, "agent", "[phase=LOCATE calls=1/45] read", "read_file",
                      {"filepath": "pkg/mod.py", "start_line": 10, "end_line": 60}),
            make_step(5, "agent", "[phase=EDIT calls=2/45] edit", "edit_file",
                      {"filepath": "pkg/mod.py", "old_string": "a", "new_string": "b"}),
            make_step(6, "agent", "[phase=VERIFY calls=3/45] test", "run_command",
                      {"command": "timeout 90 python -m pytest -x -q tests/test_mod.py | tail -n 60"}),
            make_step(7, "agent", "[phase=SUBMIT calls=4/45] status", "get_status", {}),
            make_step(8, "agent", "[phase=SUBMIT calls=4/45] submit", "submit_patch", {}),
            make_step(9, "agent", "Done. Fixed foo."),
        ],
        "final_metrics": {"total_prompt_tokens": 50000, "total_completion_tokens": 1200, "total_steps": 9},
    }
    bad = {
        "schema_version": "ATIF-v1.5", "agent": {"name": "swegemma", "version": "0.2.7"},
        "steps": [
            make_step(1, "system", "prompt"),
            make_step(2, "user", "task"),
            make_step(3, "agent", "look", "run_command", {"command": "grep -rn foo ."}),
            make_step(4, "agent", "again", "run_command", {"command": "grep -rn foo ."}),
            make_step(5, "agent", "again", "run_command", {"command": "grep -rn foo ."}),
            make_step(6, "agent", "whole file", "read_file", {"filepath": "pkg/big.py"}),
            make_step(7, "agent", "<|tool_call>call:grep -rn foo{<tool_call|>"),
            make_step(8, "user", "Please continue your work using the available tools, or call submit_patch when you have completed and verified your changes."),
            make_step(9, "agent", "edit", "edit_file", {"filepath": "pkg/big.py", "old_string": "x", "new_string": "y"},
                      observation='{"status": "error", "error_type": "FileEditError", "error_message": "old_string not found"}'),
            make_step(10, "agent", "undeclared", "run_skill_script", {"skill_name": "x", "file_path": "scripts/a.py"}),
        ],
        "final_metrics": {"total_prompt_tokens": 90000, "total_completion_tokens": 3000, "total_steps": 10},
    }
    (run / "traces" / "trace_synth_good.json").write_text(json.dumps(good), encoding="utf-8")
    (run / "traces" / "trace_synth_bad.json").write_text(json.dumps(bad), encoding="utf-8")
    rows = [
        {"instance_id": "synth_good", "repo": "synthetic/repo", "resolved": True, "duration_s": 120.0,
         "setup_s": 30.0, "tool_calls": 4, "llm_calls": 7, "error": None,
         "patch": "diff --git a/pkg/mod.py b/pkg/mod.py\n--- a/pkg/mod.py\n+++ b/pkg/mod.py\n@@ -1 +1 @@\n-a\n+b\n"},
        {"instance_id": "synth_bad", "repo": "synthetic/repo", "resolved": False, "duration_s": 268.0,
         "setup_s": 40.0, "tool_calls": 6, "llm_calls": 8,
         "error": "litellm.BadRequestError: Error code: 400 - maximum context length is 32768 tokens",
         "patch": "diff --git a/repro.py b/repro.py\nnew file mode 100644\n--- /dev/null\n+++ b/repro.py\n@@ -0,0 +1 @@\n+print(1)\n"},
    ]
    with open(run / "task_results.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    return run


@pytest.fixture
def synthetic_tasks(tmp_path: Path) -> Path:
    """tasks.jsonl with the public repo mix (67/48/13/1) but synthetic ids and no content."""
    path = tmp_path / "tasks.jsonl"
    counts = {"fastapi/fastapi": 67, "Textualize/rich": 48, "psf/requests": 13, "encode/httpx": 1}
    with open(path, "w", encoding="utf-8") as fh:
        for repo, n in counts.items():
            short = repo.split("/")[1].lower()
            for i in range(n):
                fh.write(json.dumps({"instance_id": f"{short}_{1000 + i}", "repo": repo}) + "\n")
    return path
