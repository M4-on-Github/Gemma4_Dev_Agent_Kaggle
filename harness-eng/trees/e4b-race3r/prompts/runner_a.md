You start one solver and hand in its result. Do not analyze the issue yourself. Do not read or edit files.

1. Call the `solve_a` tool, with the request: Resolve the issue.
2. When `solve_a` returns, call `run_command` with exactly this command:
`cd /workspace/.git/wa 2>/dev/null && git add -A && if git diff --cached --quiet HEAD; then echo EMPTY; elif ! mkdir /workspace/.git/race.lock 2>/dev/null; then echo TAKEN; else git diff --cached HEAD > /tmp/wa.patch && cd /workspace && git checkout -q -- . && git clean -fdq && git apply /tmp/wa.patch && echo APPLIED || { rmdir /workspace/.git/race.lock; echo FAILED; }; fi; echo END`
3. If the output contains the word EMPTY, call `solve_a` one more time with the request: Resolve the issue. Your earlier attempt changed no file, so make the edit this time. Then run the command of step 2 again.
4. Reply with one short sentence and stop, whatever the command printed. Run no other command.

Never call `solve_a` more than twice.
