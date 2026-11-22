---
name: line-edit
description: Shows file lines with line numbers and replaces a numbered range of lines with new text, so an edit needs no copy of the old text. Scripts show.py and replace.py.
---

# line-edit

Both scripts are called through `run_skill_script` with three fields only: `skill_name` set to `line-edit`, `file_path`, and `args` as a list of strings. Do not send `positional_args` or `short_options`, and do not call `load_skill` first. Paths are relative to the repository root.

- `scripts/show.py` with `args` `[path, start_line, end_line]` prints those lines, each with its line number, at most 120 lines.
- `scripts/replace.py` with `args` `[path, start_line, end_line, new_text]` replaces lines start_line to end_line, both included, with new_text. Write new_text with its full indentation and a newline between lines. It prints the new region with line numbers. Line numbers after the edited range shift, so run `show.py` again before a second edit in the same file.
