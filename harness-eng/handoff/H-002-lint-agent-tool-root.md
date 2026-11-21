# H-002: validator false error on agent_tool roots (handoff, not a pre-registration)

Written 2026-11-21 on pleiades. It is a code fix on this branch's `tools/`, which the cluster does not write here.
It is needed only if R-016 (31B) or R-017 (E4B), both on `recursive-harness`, is kept. Each of them moves the agent
into an `agent_tool`. Counts only.

## The false error

- `tools/validate_submission.py:532-533` reports `root agent has no way to modify files` on
  `trees/31b-r016-nocompact` and `trees/e4b-r017-nocompact` (on `recursive-harness`).
- Those roots declare `submit_patch` and an `agent_tool` whose agent holds `run_command`, `read_file`, `edit_file`,
  `write_file`, `get_status` and `submit_patch`.
- The EXP-061 rule (lines 522-529) uses the union over reachable agents only when the root declares `sub_agents`.
  It does not do so for an `agent_tool`, although `_reachable_llm_tool_names` (line 410) already walks every agent in
  the tree, `agent_tool` children included (lines 222-224).
- `adk_submission.validate_directory` (official) returns OK on both trees. R-016's smoke ran 2 of 2 SUCCESS on the
  cluster with this layout (job 59992).

## Suggested fix

```python
            checked = set(tool_names)
            if cfg.get("sub_agents") or any(isinstance(t, dict) and "agent_tool" in t for t in tools):
                checked = _reachable_llm_tool_names(tree)
```

Add a test: a root with `submit_patch` plus an `agent_tool` whose agent has `edit_file` validates with no error. A
root whose `agent_tool` agent has only `read_file` still errors.

## Also needed before packing such a tree

- `tests/test_pack_submission.py::test_pack_ships_only_closure` asserts that the shipped set is the current four
  files. A solver tree ships seven: `agent.yaml`, `eval_config.yaml`, `prompts/root.md`, `prompts/solver.md`,
  `configs/sampling.yaml`, `configs/sampling_root.yaml` and `sub_agents/solver.yaml`.
- The warning `sub-agent with submit_patch can end the session from inside a sub-call` is intended for this layout.
  `pack_submission.py` refuses on warnings unless `--allow-warnings` is given.
- `prompts/solver.md` carries `{problem_description}` (required: the harness puts it in state, and ADK raises
  KeyError if it is missing) and `{hints?}`. Keep the brace lint's allowance for these two placeholders.
