---
name: codemap
description: Two scripts that read the repository's code graph. scripts/locate.py takes one string (the issue title and its first 120 words) and prints the best files, the best functions with line ranges, the code of the best two, and related sites. scripts/audit.py takes an empty argument list and prints the functions the working tree has changed and the related sites it has not changed.
---

# codemap

## locate

Call `scripts/locate.py` through `run_skill_script` with three fields only: `skill_name` set to `codemap`,
`file_path` set to `scripts/locate.py`, and `args` set to a list holding one string, the issue title and the first
120 words of the issue copied word for word. Do not send `positional_args` or `short_options`. It prints the code
map: `FILES`, `SYMBOLS` as `path:first-last kind name`, `CODE` of the best two symbols with line numbers, and
`RELATED SITES` that may need the same change.

## audit

Call `scripts/audit.py` through `run_skill_script` with three fields only: `skill_name` set to `codemap`,
`file_path` set to `scripts/audit.py`, and `args` set to an empty list. It prints `CHANGED by the draft:` with one
`path:first-last kind name` line per changed function or class, then `RELATED SITES NOT CHANGED` with one
`path:first-last kind name -- why it is related` line per site, most likely first. When no source file has changed
it prints `NO DRAFT EDIT`.
