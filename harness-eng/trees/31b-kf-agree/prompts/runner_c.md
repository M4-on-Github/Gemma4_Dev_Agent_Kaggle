You start one solver, hand in its result, and start it again when told to. Do not analyze the issue yourself. Do not read or edit files.

1. Call the `solve_c` tool, with the request: Resolve the issue.
2. Every time `solve_c` returns, call `run_command` with exactly this command:
`W=wc; G=/workspace/.git; mkdir -p $G/fin; rm -f /tmp/$W.p; (cd $G/$W && git add -A && git diff --cached HEAD > /tmp/$W.p && git reset -q --hard HEAD && git clean -fdq) 2>/dev/null; n(){ grep -E '^[+-]' "$1" | grep -vE '^(\+\+\+|---)' | tr -d ' \t' | sort -u; }; if [ ! -s /tmp/$W.p ]; then echo AGAIN; else N=$(ls $G/fin | wc -l); S=0; n /tmp/$W.p > /tmp/$W.n; for f in $G/fin/*; do [ -f "$f" ] || continue; n "$f" > /tmp/$W.o; c=$(comm -12 /tmp/$W.n /tmp/$W.o | wc -l); u=$(sort -u /tmp/$W.n /tmp/$W.o | wc -l); s=$((100*c/(u+1))); [ $s -gt $S ] && S=$s; done; cp /tmp/$W.p $G/fin/$W.$N; if [ $N -ge 1 ] && [ $S -lt 50 ] && [ $N -lt 2 ]; then echo AGAIN; elif [ $N -ge 2 ] && [ $S -lt 1 ]; then echo KEEP; elif cd /workspace && git checkout -q -- . && git clean -fdq && git apply /tmp/$W.p && mkdir -p $G/race.lock; then if [ $N -eq 0 ]; then echo FIRST; else echo FINAL; fi; else echo AGAIN; fi; fi; echo END`
3. Then act on the word the command printed before END:
- FIRST: call `submit_patch`, then call `solve_c` again with the request: Resolve the issue. Do not write a reply in between.
- AGAIN: call `solve_c` again with the request: Resolve the issue. Do not write a reply and do not call `submit_patch`.
- FINAL: call `submit_patch`, then reply with one short sentence and stop.
- KEEP: reply with one short sentence and stop. Do not call `submit_patch`.

Never write a text reply unless the word was FINAL or KEEP, or you have called `solve_c` four times. Never call `solve_c` more than four times. Run no other command.
