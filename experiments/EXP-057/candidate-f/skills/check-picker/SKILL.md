---
name: check-picker
description: Picks the one command to run as the final check after your last edit. Call scripts/pick_check.py with the paths of the source files you edited.
---

# check-picker

Call `scripts/pick_check.py` through `run_skill_script` with three fields only: `skill_name` set to `check-picker`, `file_path` set to `scripts/pick_check.py`, and `args` set to one list of strings holding the paths of the files you edited. Do not send `positional_args` or `short_options`. An empty list is allowed: the script then uses the source files changed most recently. The script only reads the workspace. It prints exactly one command line: an existing test file that fits the edited module, or an import of that module when no test file fits. It does not run anything. Run the printed line yourself with `run_command`.
