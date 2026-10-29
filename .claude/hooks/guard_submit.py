"""PreToolUse hook (session-wide, Bash|PowerShell): gate main-track competition submissions.

The main track accepts one upload per UTC day and a timeout scores zero for that slot, so an upload is the
scarcest action in this repo. A `kaggle competitions submit` command passes only if all hold:
  - it comes from the `submitter` agent,
  - its message (-m) names an S-NNN proposal (S-NNN = the submissions.md row it will become),
  - approvals/S-NNN.txt exists (written by the user; no agent's write guard allows that folder),
  - the SHA-256 in that file matches the file being submitted (-f).
The paper track is submitted through the Kaggle Writeup UI by the user, never from here.
"""
import hashlib
import json
import os
import re
import shlex
import sys
from pathlib import Path


def block(reason: str) -> None:
    print(f"Blocked submission: {reason}", file=sys.stderr)
    sys.exit(2)


try:
    event = json.load(sys.stdin)
except ValueError:
    block("could not parse hook input.")

command = event.get("tool_input", {}).get("command", "") or ""
if not re.search(r"competitions\s+submit\b|competition_submit|submissions?/submit", command):
    sys.exit(0)

if event.get("agent_type") != "submitter":
    block("only the submitter agent may submit.")

try:
    argv = shlex.split(command, posix=True)
except ValueError:
    block("could not parse the command.")


def arg(*names):
    for i, a in enumerate(argv):
        if a in names and i + 1 < len(argv):
            return argv[i + 1]
        for n in names:
            if a.startswith(n + "="):
                return a.split("=", 1)[1]
    return None


message, file_arg = arg("-m", "--message"), arg("-f", "--file")
match = re.search(r"\bS-\d{3,}\b", message or "")
if not match or not file_arg:
    block("command needs -f <file> and a -m message naming S-NNN.")

root = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
approval = root / "approvals" / f"{match.group(0)}.txt"
if not approval.is_file():
    block(f"{approval.relative_to(root).as_posix()} does not exist; the user has not approved {match.group(0)}.")

path = Path(file_arg)
if not path.is_absolute():
    path = Path(event.get("cwd", root)) / path
if not path.is_file():
    block(f"file not found: {file_arg}")
if path.name != "submission.zip":
    block("the upload must be named submission.zip (CLAUDE.md, Windows notes).")

digest = hashlib.sha256(path.read_bytes()).hexdigest()
# Tolerate UTF-16 or BOM-prefixed files written by PowerShell.
if digest not in approval.read_bytes().decode("utf-8", "ignore").replace("\x00", "").lower():
    block(f"SHA-256 of {file_arg} ({digest}) is not in {approval.name}.")

sys.exit(0)
