You start one script and do nothing else. Do not analyze the issue or the code yourself.

1. Call `run_skill_script` with exactly three fields: `skill_name` set to `codemap`, `file_path` set to `scripts/audit.py`, and `args` set to an empty list. Do not call `load_skill` first.
2. When it returns, reply with the single word `audited` and stop. The next step reads what the script printed.
