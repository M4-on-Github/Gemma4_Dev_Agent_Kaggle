---
name: attempt-check
description: Tells the root what to do after a solve attempt. Prints one line that starts with retry, repair, or submit. Call scripts/check.py with an empty argument list.
---

# attempt-check

Call `scripts/check.py` through `run_skill_script` with three fields only: `skill_name` set to `attempt-check`, `file_path` set to `scripts/check.py`, and `args` set to an empty list. Do not send `positional_args` or `short_options`. It prints one line. A line that starts with `retry` means the attempt changed no source file. A line that starts with `repair` names a changed source file that does not parse. `submit` means submit the change now.
