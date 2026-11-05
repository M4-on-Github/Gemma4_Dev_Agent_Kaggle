"""EXP-037 placement check: where the older-lineage arms' stand-ins sat in the final patch.

For each final patch in the four older-lineage dev-48 arms, list the diff paths that create an
`inline_snapshot` or `dirty_equals` module, with the task id and the as-run resolve flag. Prints our own
stand-in paths, task ids and flags only (no repository content).
Run as:  python -I -X utf8 experiments/EXP-037/vendor_paths.py
"""
import json
import re
from pathlib import Path

ARMS = {"E0": "runs/E0-dev48-baseline/runs/E0-dev48-baseline",
        "X003": "runs/exp003_public_budget_dev48/runs/EXP-003-public-budget-dev48",
        "A25": "runs/exp025_armA/runs/EXP-025-editfix-dev48-armA-baseline",
        "B25": "runs/exp025_armB/runs/EXP-025-editfix-dev48-armB-editfix"}
DIFF = re.compile(r"^diff --git a/(\S+) b/", re.M)
STANDIN = re.compile(r"(?:^|/)(inline_snapshot|dirty_equals)(?:/|\.py$)")

for arm, d in ARMS.items():
    for line in open(Path(d) / "task_results.jsonl", encoding="utf-8"):
        r = json.loads(line)
        patch = r.get("patch") or r.get("model_patch") or ""
        paths = [x for x in DIFF.findall(patch) if STANDIN.search(x)]
        if paths:
            print(arm, r.get("instance_id"), "resolved" if r.get("resolved") else "unresolved", paths)
