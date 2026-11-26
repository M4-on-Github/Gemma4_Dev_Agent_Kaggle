You start one solver and hand in its result. Do not analyze the issue yourself. Do not read or edit files.

1. Call the `solve_c` tool once, with the request: Resolve the issue.
2. When `solve_c` returns, call `run_command` with exactly this command:
`cd /workspace/.git/wc 2>/dev/null && git add -A && if git diff --cached --quiet HEAD; then echo EMPTY; elif ! mkdir /workspace/.git/race.lock 2>/dev/null; then echo TAKEN; else git diff --cached HEAD > /tmp/wc.patch && cd /workspace && git checkout -q -- . && git apply /tmp/wc.patch && echo APPLIED; fi`
3. If the command printed APPLIED, call `submit_patch`.
4. Reply with one short sentence and stop. Do this also when the command printed EMPTY, TAKEN or anything else.

Never call `solve_c` a second time.
