---
name: locate
description: Ranks the repository's source files by how well they match the issue text and prints one line, the request to pass to the solver. Call scripts/rank.py with args set to a list holding one string, the opening sentences of the issue.
---

# locate

Call `scripts/rank.py` through `run_skill_script` with three fields only: `skill_name` set to `locate`, `file_path`
set to `scripts/rank.py`, and `args` set to a list holding one string, the opening sentences of the issue copied word
for word. It prints one line: the request for the solver, naming the source files that best match the issue, best
first.
