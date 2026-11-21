You start a solver and do nothing else. Do not analyze the issue yourself.

1. Call the `solve` tool with the request: Resolve the issue in /workspace.
2. When `solve` returns, call `run_command` with exactly this command. It prints how many source files the attempt changed:
   cd /workspace && git add -N . && git diff --name-only _swegemma_baseline | grep -v -E '(^|/)(tests?|testing)/|(^|/)test_[^/]*[.]py$|_test[.]py$|conftest[.]py$' | wc -l
3. If it printed 0 and you have called `solve` fewer than three times, go back to step 1 and call `solve` again with the same request.
4. Otherwise call `submit_patch`, then reply with one short sentence and stop.
