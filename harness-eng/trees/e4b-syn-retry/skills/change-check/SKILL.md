---
name: change-check
description: Prints how many source files the working tree has changed since the start of the task, or the first syntax error among the changed source files. Call scripts/check.py with an empty argument list.
---

# change-check

Call `scripts/check.py` through `run_skill_script` with three fields only: `skill_name` set to `change-check`, `file_path` set to `scripts/check.py`, and `args` set to an empty list. Do not send `positional_args` or `short_options`. It prints one line: `0` when no source file changed, a line that starts with `syntax error` when a changed source file does not parse, and otherwise the number of changed source files. Test files are not counted.
