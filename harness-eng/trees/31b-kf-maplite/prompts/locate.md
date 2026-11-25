You start one script and do nothing else. Do not analyze the issue yourself.

1. Call `run_skill_script` with exactly three fields: `skill_name` set to `codemap`, `file_path` set to `scripts/locate.py`, and `args` set to a list holding one string: the issue title and the first 120 words of the issue, copied word for word, with every backticked name, file path and error message in them. Do not call `load_skill` first.
2. When it returns, reply with the single word `mapped` and stop. The next step reads what the script printed.
