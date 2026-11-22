---
name: outline
description: Prints every class and function in one source file with its line range, so you can read only the range you need. Call scripts/outline.py with args set to a list holding one relative file path.
---

# outline

Call `scripts/outline.py` through `run_skill_script` with three fields only: `skill_name` set to `outline`, `file_path` set to `scripts/outline.py`, and `args` set to a list holding one path relative to the repository root, for example `["pkg/module.py"]`. Do not send `positional_args` or `short_options`, and do not call `load_skill` first. Each printed line is `L<start>-<end>` followed by `class` or `def` and the name. Then read only that range with `read_file`.
