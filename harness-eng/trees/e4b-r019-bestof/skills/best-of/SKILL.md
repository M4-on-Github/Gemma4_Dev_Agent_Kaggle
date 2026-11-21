---
name: best-of
description: Decides whether one more attempt is needed and picks the attempt to keep. Call scripts/pick.py with an empty argument list after each saved attempt.
---

# best-of

Call `scripts/pick.py` through `run_skill_script` with three fields only: `skill_name` set to `best-of`, `file_path` set to `scripts/pick.py`, and `args` set to an empty list. Do not send `positional_args` or `short_options`. The script reads the attempts saved in the workspace and prints one word. NEXT means run one more attempt. APPLY means the attempt to keep is ready to apply.
