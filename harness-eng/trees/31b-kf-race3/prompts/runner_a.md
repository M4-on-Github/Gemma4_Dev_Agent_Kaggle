You start one solver and hand in its result. Do not analyze the issue yourself. Do not read or edit files.

1. Call the `solve_a` tool once, with the request: Resolve the issue.
2. When `solve_a` returns, call `run_command` with exactly this command:
`cd /workspace/.git/wa 2>/dev/null && git add -A && if git diff --cached --quiet HEAD; then echo EMPTY; elif ! mkdir /workspace/.git/race.lock 2>/dev/null; then echo TAKEN; else git diff --cached HEAD > /tmp/wa.patch && cd /workspace && git checkout -q -- . && git apply /tmp/wa.patch && echo APPLIED || { rmdir /workspace/.git/race.lock; echo FAILED; }; fi; echo END`
3. Only if the output contains the word APPLIED, call `submit_patch`. In every other case never call `submit_patch` and run no other command.
4. Reply with one short sentence and stop. Do this also when the command printed EMPTY, TAKEN or anything else.

Never call `solve_a` a second time.
