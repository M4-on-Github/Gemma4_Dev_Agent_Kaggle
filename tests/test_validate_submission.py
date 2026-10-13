from pathlib import Path

import validate_submission as V


def errors_of(sub: Path, strict: bool = False) -> list[str]:
    return V.validate_dir(sub, strict_tree=strict).errors


def test_repo_submission_is_valid(repo_root: Path):
    rep = V.validate_dir(repo_root / "submission", strict_tree=False)
    assert rep.ok, rep.render()
    assert not rep.warnings, rep.render()


def test_minimal_submission_valid(minimal_submission: Path):
    rep = V.validate_dir(minimal_submission, strict_tree=True)
    assert rep.ok, rep.render()


def test_disallowed_extension(minimal_submission: Path):
    (minimal_submission / "run.sh").write_text("echo hi\n")
    errs = errors_of(minimal_submission, strict=True)
    assert any("disallowed file extension" in e and "run.sh" in e for e in errs)


def test_missing_eval_config_is_error(minimal_submission: Path):
    (minimal_submission / "eval_config.yaml").unlink()
    assert any("no eval_config.yaml" in e for e in errors_of(minimal_submission))


def test_eval_config_worst_case_gate(minimal_submission: Path):
    (minimal_submission / "eval_config.yaml").write_text(
        "evaluation:\n  max_time_minutes: 10\n  max_tool_calls: 45\n  max_turns: 70\n  timeout_seconds: 300\n")
    assert any("EXCEEDS the packing gate" in e for e in errors_of(minimal_submission))


def test_eval_config_requires_evaluation_key(minimal_submission: Path):
    (minimal_submission / "eval_config.yaml").write_text("max_time_minutes: 4.5\n")
    assert any("'evaluation:' mapping" in e for e in errors_of(minimal_submission))


def test_unknown_eval_key(minimal_submission: Path):
    (minimal_submission / "eval_config.yaml").write_text(
        "evaluation:\n  max_time_minutes: 4.5\n  per_task_timeout_seconds: 10\n")
    assert any("unknown key evaluation.per_task_timeout_seconds" in e for e in errors_of(minimal_submission))


def test_placeholder_keyerror(minimal_submission: Path):
    (minimal_submission / "prompts" / "system.md").write_text("Fix {issue_title} now.\n")
    errs = errors_of(minimal_submission)
    assert any("placeholder '{issue_title}'" in e for e in errs)


def test_hints_placeholder_must_be_optional(minimal_submission: Path):
    (minimal_submission / "prompts" / "system.md").write_text("Hints: {hints}\n")
    assert any("{hints?}" in e for e in errors_of(minimal_submission))
    (minimal_submission / "prompts" / "system.md").write_text("Hints: {hints?} and {problem_description}\n")
    assert not errors_of(minimal_submission)


def test_literal_braces_only_warn(minimal_submission: Path):
    (minimal_submission / "prompts" / "system.md").write_text('Call run_command with {"command": "ls"}\n')
    rep = V.validate_dir(minimal_submission)
    assert rep.ok
    assert any("literal braces" in w for w in rep.warnings)


def test_undeclared_tool_is_error(minimal_submission: Path):
    (minimal_submission / "agent.yaml").write_text(
        "name: a\nmodel: gemma-4-31b-it-qat-w4a16-ct\ninstruction: !include prompts/system.md\n"
        "tools:\n  - run_command\n  - submit_patch\n  - bash\n")
    assert any("'bash' is not provided" in e for e in errors_of(minimal_submission))


def test_name_dict_tool_form_is_error(minimal_submission: Path):
    (minimal_submission / "agent.yaml").write_text(
        "name: a\nmodel: gemma-4-31b-it-qat-w4a16-ct\ninstruction: !include prompts/system.md\n"
        "tools:\n  - name: run_command\n  - name: submit_patch\n")
    assert any("{name: ...} form" in e for e in errors_of(minimal_submission))


def test_wrong_model_and_prefix_stripping(minimal_submission: Path):
    (minimal_submission / "agent.yaml").write_text(
        "name: a\nmodel: openai/gemma-4-31b-it-qat-w4a16-ct\ninstruction: !include prompts/system.md\n"
        "tools:\n  - run_command\n  - submit_patch\n")
    assert not errors_of(minimal_submission)
    (minimal_submission / "agent.yaml").write_text(
        "name: a\nmodel: gemma-4-12b-it\ninstruction: !include prompts/system.md\ntools:\n  - run_command\n")
    assert any("not allowed" in e for e in errors_of(minimal_submission))


def test_forbidden_strings(minimal_submission: Path):
    (minimal_submission / "prompts" / "system.md").write_text("If needed run pip install foo via subprocess.\n")
    errs = errors_of(minimal_submission)
    assert any("pip install" in e for e in errs) and any("subprocess" in e for e in errs)


def test_repo_specific_prompt_is_error(minimal_submission: Path):
    (minimal_submission / "prompts" / "system.md").write_text("For FastAPI tasks edit docs_src.\n")
    assert any("public dev-set repo" in e for e in errors_of(minimal_submission))


def test_forbidden_generation_field(minimal_submission: Path):
    (minimal_submission / "configs" / "sampling.yaml").write_text("temperature: 0.2\ntools: []\nfoo: 1\n")
    errs = errors_of(minimal_submission)
    assert any("tools is forbidden" in e for e in errs) and any("unknown generate_content_config field 'foo'" in e for e in errs)


def test_include_escape_rejected(minimal_submission: Path, tmp_path: Path):
    (tmp_path / "outside.md").write_text("x")
    (minimal_submission / "agent.yaml").write_text(
        "name: a\nmodel: gemma-4-31b-it-qat-w4a16-ct\ninstruction: !include ../outside.md\ntools:\n  - run_command\n")
    errs = errors_of(minimal_submission)
    assert errs and ("escapes" in errs[0] or "'..'" in errs[0])


def test_include_missing_target(minimal_submission: Path):
    (minimal_submission / "agent.yaml").write_text(
        "name: a\nmodel: gemma-4-31b-it-qat-w4a16-ct\ninstruction: !include prompts/nope.md\ntools:\n  - run_command\n")
    assert any("not found" in e for e in errors_of(minimal_submission))


def test_agent_tool_subagent_single_model_rule(minimal_submission: Path):
    (minimal_submission / "sub_agents").mkdir()
    (minimal_submission / "sub_agents" / "x.yaml").write_text(
        "name: x\nmodel: gemma-4-12b-it\ndescription: d\ninstruction: !include ../prompts/system.md\ntools:\n  - read_file\n")
    (minimal_submission / "agent.yaml").write_text(
        "name: a\nmodel: gemma-4-31b-it-qat-w4a16-ct\ninstruction: !include prompts/system.md\n"
        "tools:\n  - run_command\n  - submit_patch\n  - agent_tool:\n      config_path: sub_agents/x.yaml\n      skip_summarization: true\n")
    errs = errors_of(minimal_submission)
    assert any("multiple base models" in e for e in errs)


def test_skill_name_must_match_dir(minimal_submission: Path):
    d = minimal_submission / "skills" / "my-skill"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("---\nname: other-name\ndescription: x\n---\n# hi\n")
    (minimal_submission / "agent.yaml").write_text(
        "name: a\nmodel: gemma-4-31b-it-qat-w4a16-ct\ninstruction: !include prompts/system.md\n"
        "tools:\n  - run_command\n  - submit_patch\nskills:\n  - skills/my-skill\n")
    assert any("must equal the directory name" in e for e in errors_of(minimal_submission))


def test_zip_requires_root_agent_yaml(tmp_path: Path, minimal_submission: Path):
    import zipfile
    z = tmp_path / "nested.zip"
    with zipfile.ZipFile(z, "w") as zf:
        for p in minimal_submission.rglob("*"):
            if p.is_file():
                zf.write(p, "submission/" + p.relative_to(minimal_submission).as_posix())
    rep = V.validate_zip(z)
    assert any("not at the archive root" in e for e in rep.errors)


def test_zero_byte_member_is_error(tmp_path: Path, minimal_submission: Path):
    import zipfile
    z = tmp_path / "zero.zip"
    with zipfile.ZipFile(z, "w") as zf:
        for p in minimal_submission.rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(minimal_submission).as_posix())
        zf.writestr("prompts/empty.md", "")
    rep = V.validate_zip(z)
    assert any("0-byte member" in e for e in rep.errors)
