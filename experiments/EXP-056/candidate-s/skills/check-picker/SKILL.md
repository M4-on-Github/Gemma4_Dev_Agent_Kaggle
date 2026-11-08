---
name: check-picker
description: Picks the one command to run as the final check after your last edit. Call scripts/pick_check.py with the paths of the source files you edited.
---

# check-picker

Call `scripts/pick_check.py` through `run_skill_script`, passing the paths of the files you edited as a list in `args`. The script only reads the workspace. It prints exactly one command line: an existing test file that fits the edited module, or an import of that module when no test file fits. It does not run anything. Run the printed line yourself with `run_command`.
