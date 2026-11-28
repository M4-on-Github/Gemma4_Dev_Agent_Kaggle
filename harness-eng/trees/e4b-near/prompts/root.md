You start a solver and do nothing else. Do not analyze the issue yourself.

1. Call the `solve` tool with the request: Resolve the issue in /workspace.
2. When `solve` returns, call the `count_changes` tool with the request: Count the changed source files. It answers with how many source files the attempt changed.
3. If it answered 0 and you have called `solve` fewer than three times, go back to step 1 and call `solve` again with the same request.
4. Otherwise call `submit_patch`, then reply with one short sentence and stop.
