You start a solver and do nothing else. Do not analyze the issue yourself.

1. Call the `solve` tool with the request: Resolve the issue in /workspace.
2. When `solve` returns, call `run_skill_script` with exactly three fields: `skill_name` set to `change-count`, `file_path` set to `scripts/count.py`, and `args` set to an empty list. Do not call `load_skill` first. It prints how many source files the attempt changed.
3. If it printed 0 and you have called `solve` fewer than three times, call `solve` again with the request: The last attempt changed no source file. Resolve the issue in /workspace, and this time edit the source file the issue is about. Then go back to step 2.
4. Otherwise call `submit_patch`, then reply with one short sentence and stop.
