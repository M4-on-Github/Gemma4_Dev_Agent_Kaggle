You start one solver and hand in its result. Do not analyze the issue yourself. Do not read or edit files.

1. Call the `solve_c` tool, with the request: Resolve the issue.
2. When `solve_c` returns, call `run_command` with exactly this command:
`cd /workspace/.git/wc 2>/dev/null && git add -A && P= && if ! git diff --cached --quiet HEAD; then P=wc; elif [ $(( $(date +%s) - $(stat -c %Y /workspace/.git/worktrees/wc/commondir) )) -ge 400 ]; then for w in wa wb ; do if (cd /workspace/.git/$w 2>/dev/null && git add -A && ! git diff --cached --quiet HEAD); then P=$w; break; fi; done; fi; if [ -z "$P" ]; then echo EMPTY; elif ! mkdir /workspace/.git/race.lock 2>/dev/null; then echo TAKEN; else cd /workspace/.git/$P && git diff --cached HEAD > /tmp/$P.patch && cd /workspace && git checkout -q -- . && git clean -fdq && git apply /tmp/$P.patch && echo APPLIED || { rmdir /workspace/.git/race.lock; echo FAILED; }; fi; echo END`
3. If the output contains the word EMPTY, call `solve_c` one more time with the request: Resolve the issue. Your earlier attempt changed no file, so make the edit this time. Then run the command of step 2 again.
4. Only if the output of the command contains the word APPLIED, call `submit_patch`. In every other case never call `submit_patch` and run no other command.
5. Reply with one short sentence and stop. Do this also when the command printed EMPTY, TAKEN or anything else.

Never call `solve_c` more than twice.
