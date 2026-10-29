"""PreToolUse hook (session-wide, Bash|PowerShell): a kernel push needs a committed pre-registration.

CLAUDE.md: "A new experiments/EXP-NNN-<slug>.md is committed *before* the kernel is pushed." A dev-48 run
costs ~4 of the 30 weekly L4x4 GPU-hours, and readings written after the numbers land are worthless, so the
rule is enforced here instead of on the honor system. `kaggle kernels push -p notebooks/<dir>` passes only if:
  - <dir> names the experiment (`exp028_armR`, `EXP-028-...`, `exp-028`): the first 3-digit group is NNN,
  - exactly one tracked `experiments/EXP-NNN-*.md` exists,
  - that file has no unstaged or staged changes (its committed text is what the kernel is run against),
  - it contains a readings section (a heading mentioning "reading" or "pre-registered").
Pass `--prereg-dir` nothing; override only by editing this file, which the pre-registration commit would show.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def block(reason: str) -> None:
    print(f"Blocked kernel push: {reason}", file=sys.stderr)
    sys.exit(2)


try:
    event = json.load(sys.stdin)
except ValueError:
    block("could not parse hook input.")

command = event.get("tool_input", {}).get("command", "") or ""
if not re.search(r"\bkaggle\s+kernels\s+push\b", command):
    sys.exit(0)

m = re.search(r"(?:-p|--path)\s+[\"']?([^\s\"']+)", command)
if not m:
    block("name the notebook directory with -p notebooks/<expNNN_dir>.")
nb_dir = m.group(1)
num = re.search(r"(?i)exp[-_]?(\d{3})", Path(nb_dir).name)
if not num:
    block(f"the notebook directory name must carry the experiment number (expNNN_...); got {nb_dir}.")
exp = f"EXP-{num.group(1)}"

root = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True).stdout


tracked = [ln for ln in git("ls-files", f"experiments/{exp}-*.md").splitlines() if ln.strip()]
if len(tracked) != 1:
    block(f"expected exactly one tracked experiments/{exp}-<slug>.md, found {len(tracked)}. Commit the pre-registration first.")
prereg = tracked[0]

if git("status", "--porcelain", "--", prereg).strip():
    block(f"{prereg} has uncommitted changes. Commit the pre-registration before pushing.")

text = (root / prereg).read_text(encoding="utf-8", errors="replace")
if not re.search(r"(?im)^#+\s.*(reading|pre-registered)", text):
    block(f"{prereg} has no readings section (a heading mentioning 'reading' or 'pre-registered').")

sys.exit(0)
