---
name: change-count
description: Prints how many source files the working tree has changed since the start of the task, as one integer. Call scripts/count.py with an empty argument list.
---

# change-count

Call `scripts/count.py` through `run_skill_script` with three fields only: `skill_name` set to `change-count`, `file_path` set to `scripts/count.py`, and `args` set to an empty list. Do not send `positional_args` or `short_options`. It prints one integer: the number of changed source files. Test files are not counted.
