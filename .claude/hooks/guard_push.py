"""PreToolUse hook (session-wide, Bash|PowerShell): a kernel push needs a committed pre-registration whose
cohort matches the notebook it is about to run.

CLAUDE.md: "A new experiments/EXP-NNN-<slug>.md is committed *before* the kernel is pushed." A dev-48 run
costs 4-7 of the 30 weekly L4x4 GPU-hours, a smoke-8 screen ~0.8, and readings written after the numbers land
are worthless, so the rule is enforced here instead of on the honor system. `kaggle kernels push -p
notebooks/<dir>` passes only if:
  - <dir> names the experiment (`exp028_armR`, `EXP-028-...`, `exp-028`): the first 3-digit group is NNN,
  - exactly one tracked `experiments/EXP-NNN-*.md` exists,
  - that file has no unstaged or staged changes (its committed text is what the kernel is run against),
  - it contains a readings section (a heading mentioning "reading" or "pre-registered"),
  - the directory holds exactly one .ipynb whose parameter cell runs the agent (`RUN_AGENT = True`; a gold
    control with `RUN_AGENT = False` is allowed only from an exp000 directory, because cell 5 then sets a
    60-minute cap, the EXP-020 hazard; a notebook with no `RUN_AGENT` parameter passes here, without the
    cohort check, only when `kernel-metadata.json` is CPU-only: GPU and TPU off, no machine shape, no model
    source),
  - the EXP file names one cohort (a `**Cohort:** <name>` line, or exactly one `experiments/cohorts/<name>.txt`
    reference) and the notebook's `TASK_IDS` equal that cohort's ids. This keeps a screen at 8 tasks and a
    dev-48 arm at 48: the GPU budget class is checked from the ids, not from the agent's label.
Override only by editing this file, which the pre-registration commit would show.
"""
import ast
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

# ---- the notebook's parameter cell
nb_path = Path(nb_dir) if Path(nb_dir).is_absolute() else root / nb_dir
ipynbs = sorted(nb_path.glob("*.ipynb")) if nb_path.is_dir() else []
if len(ipynbs) != 1:
    block(f"expected exactly one .ipynb in {nb_dir}, found {len(ipynbs)}.")
try:
    nb = json.loads(ipynbs[0].read_text(encoding="utf-8"))
except ValueError:
    block(f"{ipynbs[0].name} is not valid JSON.")
src = "\n".join("".join(c.get("source", [])) for c in nb.get("cells", []) if c.get("cell_type") == "code")


def param(name: str):
    """Value of `NAME = <literal>` in the parameter cell, or None if absent."""
    hit = re.search(rf"(?m)^{name} = (.+?)(?:\s+#[^\"'\]]*)?$", src)
    if not hit:
        return None
    try:
        return ast.literal_eval(hit.group(1).strip())
    except (ValueError, SyntaxError):
        block(f"could not parse `{name} = ...` in {ipynbs[0].name}.")


run_agent = param("RUN_AGENT")
if run_agent is not True:
    if re.search(r"(?i)exp[-_]?000", Path(nb_dir).name):
        sys.exit(0)  # gold control: no agent run, no cohort check
    # A CPU-only kernel that never runs the agent (a re-grade of patches already on disk, EXP-036): no GPU
    # budget is at stake, so neither the 60-minute-cap hazard nor the cohort check applies. Added 2026-11-05
    # on the user's decision. The notebook must have no RUN_AGENT parameter at all (False is still blocked).
    try:
        meta = json.loads((nb_path / "kernel-metadata.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        meta = {}
    cpu_only = (meta.get("enable_gpu") is False and meta.get("enable_tpu") is False
                and not meta.get("machine_shape") and not meta.get("model_sources"))
    if run_agent is None and cpu_only:
        sys.exit(0)
    block("RUN_AGENT is not True. Gold controls (RUN_AGENT = False; cell 5 then sets a 60-minute cap) run only from an exp000 directory.")

# ---- the cohort the pre-registration declares
explicit = re.findall(r"(?im)^(?:\*\*cohort:\*\*|cohort:)\s*`?([a-z][a-z0-9-]*)", text)
referenced = sorted(set(re.findall(r"cohorts/([a-z0-9-]+)\.txt", text)))
if explicit:
    cohort = explicit[0]
elif len(referenced) == 1:
    cohort = referenced[0]
else:
    block(f"{prereg} must name one cohort: add a `**Cohort:** <name>` line (found references to {referenced or 'none'}).")

cohort_file = root / "experiments" / "cohorts" / f"{cohort}.txt"
if not cohort_file.is_file():
    block(f"{prereg} names cohort {cohort!r} but experiments/cohorts/{cohort}.txt does not exist.")
want = {ln.strip() for ln in cohort_file.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")}

task_ids = param("TASK_IDS")
if not isinstance(task_ids, list) or not task_ids:
    block(f"TASK_IDS is empty: build with `--cohort experiments/cohorts/{cohort}.txt` (N_TASKS picks the first N sorted tasks, not the cohort).")
have = set(task_ids)
if have != want:
    block(f"the notebook runs {len(have)} ids but {prereg} declares cohort {cohort} ({len(want)} ids): "
          f"{len(have - want)} not in the cohort, {len(want - have)} missing. The GPU budget class is checked from the ids.")

sys.exit(0)
