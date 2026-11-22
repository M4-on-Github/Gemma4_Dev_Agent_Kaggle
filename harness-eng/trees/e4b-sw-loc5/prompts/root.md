You start a solver and do nothing else. Do not analyze the issue yourself.

1. Call `run_skill_script` with exactly three fields: `skill_name` set to `locate`, `file_path` set to `scripts/rank.py`, and `args` set to a list holding one string: the first three sentences of the issue, copied word for word. Do not call `load_skill` first. It prints one line: the request for the solver.
2. Call the `solve` tool with the request set to exactly the line that `locate` printed.
3. When `solve` returns, call `run_skill_script` with exactly three fields: `skill_name` set to `change-count`, `file_path` set to `scripts/count.py`, and `args` set to an empty list. Do not call `load_skill` first. It prints how many source files the attempt changed.
4. If it printed 0 and you have called `solve` fewer than three times, go back to step 2 and call `solve` again with the same request.
5. Otherwise call `submit_patch`, then reply with one short sentence and stop.
