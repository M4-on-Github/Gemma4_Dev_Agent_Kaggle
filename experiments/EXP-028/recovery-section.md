## If an edit call is lost
If `edit_file` (or `write_file`) returns an error containing "mandatory input parameters are not present", the call never reached the file: an argument was dropped while the call was being written, and sending the same tool again fails the same way about 9 times in 10. Do not call `edit_file` again in this task. Make every later change with one `run_command` built from this template, with the path and the text copied exactly from your last `read_file`:
```
python3 - <<'PY'
p = 'PATH'
s = open(p, newline='').read()
old = r'''OLD TEXT, one or more whole lines'''
new = r'''NEW TEXT'''
assert s.count(old) == 1, s.count(old)
open(p, 'w', newline='').write(s.replace(old, new))
PY
git diff --stat
```
If the assert prints 0, copy the text again from `read_file`; if it prints 2 or more, add one more line to the old text. Several replacements can share one heredoc. This counts as the edit for sections 3 and 4.

