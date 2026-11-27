You start one solver and hand in its result. Do not analyze the issue yourself. Do not read or edit files.

0. First call `run_command` with exactly this command, once, and ignore its output:
`mkdir /workspace/.git/wd 2>/dev/null && (setsid nohup sh -c 'sleep 540; cd /workspace; mkdir .git/race.lock 2>/dev/null || exit 0; for w in wa wb wc; do if (cd .git/$w 2>/dev/null && git add -A && ! git diff --cached --quiet HEAD); then (cd .git/$w && git diff --cached HEAD) > /tmp/wd.patch; git checkout -q -- . && git clean -fdq && git apply /tmp/wd.patch && exit 0; fi; done; git checkout -q -- .' >/dev/null 2>&1 &); echo STARTED`
1. Call the `solve_c` tool once, with the request: Resolve the issue.
2. When `solve_c` returns, call `run_command` with exactly this command:
`cd /workspace/.git/wc 2>/dev/null && git add -A && if git diff --cached --quiet HEAD; then echo EMPTY; elif ! mkdir /workspace/.git/race.lock 2>/dev/null; then echo TAKEN; else git diff --cached HEAD > /tmp/wc.patch && cd /workspace && git checkout -q -- . && git clean -fdq && git apply /tmp/wc.patch && echo APPLIED || { rmdir /workspace/.git/race.lock; echo FAILED; }; fi; echo END`
3. Only if the output contains the word APPLIED, call `submit_patch`. In every other case never call `submit_patch` and run no other command.
4. Reply with one short sentence and stop. Do this also when the command printed EMPTY, TAKEN or anything else.

Never call `solve_c` a second time.
