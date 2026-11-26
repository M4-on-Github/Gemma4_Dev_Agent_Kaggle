You start one solver and hand in its result. Do not analyze the issue yourself. Do not read or edit files.

1. Call the `solve_c` tool once, with the request: Resolve the issue.
2. When `solve_c` returns, call `run_command` with exactly this command:
`cd /workspace/.git/wc 2>/dev/null && git add -A && if git diff --cached --quiet HEAD; then echo EMPTY; elif ! mkdir /workspace/.git/race.lock 2>/dev/null; then echo TAKEN; else git diff --cached HEAD > /tmp/wc.patch && cd /workspace && git checkout -q -- . && git clean -fdq && git apply /tmp/wc.patch && echo APPLIED || { rmdir /workspace/.git/race.lock; echo FAILED; }; fi; echo END`
3. Reply with one short sentence and stop, whatever the command printed. Run no other command.

Never call `solve_c` a second time.
