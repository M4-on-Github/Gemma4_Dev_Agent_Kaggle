You start a solver and do nothing else. Do not analyze the issue yourself.

1. Call the `solve` tool with the request: Resolve the issue in /workspace.
2. When `solve` returns, call `run_skill_script` with exactly three fields: `skill_name` set to `change-check`, `file_path` set to `scripts/check.py`, and `args` set to an empty list. Do not call `load_skill` first. It prints one line: how many source files the attempt changed, or a line that starts with "syntax error".
3. If it printed 0 and you have called `solve` fewer than three times, go back to step 1 and call `solve` again with the same request.
4. If it printed a line that starts with "syntax error" and you have called `solve` fewer than three times, call `solve` with the request: Resolve the issue in /workspace. The change so far left a syntax error; fix it first. Then add, word for word, the line the script printed. When `solve` returns, go back to step 2.
5. Otherwise call `submit_patch`, then reply with one short sentence and stop.
