"""EXP-037 build check: the inserted commands do what section 2 says, and the stand-ins they write behave like
tools/compat_shims (the code the EXP-036 re-grade used).

1. Extracts the first-call search command (the inline code after "Your first tool call is") and the fenced
   second-call command from experiments/EXP-037/insert_vendoring.md.
2. Runs them with Git Bash in two throwaway git repositories (synthetic files only, no competition data):
   (a) a test file names inline_snapshot: the search prints that path; the second call writes both stand-ins
       at the top level and nothing under tests/; a repeat of the second call changes nothing;
   (b) no file names either package: the search prints nothing (so the second call is not made).
3. Imports the written stand-ins and tools/compat_shims side by side and compares a fixed list of probes
   (equality both ways, inequality, repr, hashability, `|` alternation, class subscription).
Exit 0 only if every check passes.  Run as:  python experiments/EXP-037/check_standins.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SHIMS = REPO / "tools" / "compat_shims"
TEXT = (HERE / "insert_vendoring.md").read_text(encoding="utf-8")


def second_command() -> str:
    blocks = re.findall(r"^```\n(.*?)^```\n", TEXT, re.S | re.M)
    if len(blocks) != 1:
        sys.exit(f"expected one fenced block, found {len(blocks)}")
    return blocks[0]


def search_command() -> str:
    m = re.findall(r"Your first tool call is `([^`]+)`", TEXT)
    if len(m) != 1:
        sys.exit(f"expected one first-call command, found {len(m)}")
    return m[0]


def bash() -> str:
    # On Windows a bare "bash" resolves to System32 (WSL) before PATH; use the Git Bash on PATH instead.
    exe = os.environ.get("EXP037_BASH") or shutil.which("bash")
    if not exe or "system32" in exe.lower():
        sys.exit(f"no usable bash found ({exe}); set EXP037_BASH")
    return exe


def run_in(repo: Path, cmd: str) -> str:
    if "cd /workspace" not in cmd:
        sys.exit("command does not start in /workspace")
    r = subprocess.run([bash(), "-c", cmd.replace("cd /workspace", f"cd '{repo.as_posix()}'", 1)],
                       capture_output=True, text=True)
    if r.returncode != 0 or r.stderr.strip():
        sys.exit(f"command exit {r.returncode}: {r.stderr}")
    return r.stdout


def git_repo(root: Path, test_text: str) -> Path:
    root.mkdir(parents=True)
    (root / "pkg").mkdir()
    (root / "pkg" / "__init__.py").write_text("x = 1\n")
    (root / "tests").mkdir()
    (root / "tests" / "test_a.py").write_text(test_text)
    for c in (["git", "init", "-q"], ["git", "add", "-A"],
              ["git", "-c", "user.email=a@b", "-c", "user.name=a", "commit", "-qm", "init"]):
        subprocess.run(c, cwd=root, check=True)
    return root


def files_of(root: Path) -> dict:
    # __pycache__ written by the import probe is ignored
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*")
            if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def probes(ins, de):
    S, s = ins.Snapshot, ins.snapshot
    out = []
    for v in (None, 0, 1, "a", [1, 2], {"k": 1}):
        out += [s(v) == v, v == s(v), s(v) != v, s(v) == "other", repr(s(v))]
    out += [s() == None, S[int] is S, hash(s(1)) == hash(1), hash(s("a")) == hash("a")]  # noqa: E711
    D, P, O, H = de.IsDict, de.IsPartialDict, de.IsOneOf, de.HasRepr
    cases = [{"a": 1}, {"a": 1, "b": 2}, {"b": 2}, [("a", 1)], 1, "1", None]
    for c in cases:
        out += [D({"a": 1}) == c, c == D(a=1), D({"a": 1}) != c, P({"a": 1}) == c, c == P(a=1),
                O(1, 2) == c, c == O(None, "1"), H("1") == c, c == H("None"),
                (D(a=1) | D(b=2)) == c, (H("1") | 1) == c, ({"b": 2} | P(a=1)) == c]
    out += [repr(D(a=1)), repr(P(a=1)), repr(O(1, "x")), repr(H("1")), repr(D(a=1) | O(2))]
    for obj in (D(a=1), P(a=1), O(1), H("1"), D(a=1) | O(2)):
        try:
            hash(obj)
            out.append("hashable")
        except TypeError:
            out.append("unhashable")
    return out


def main() -> int:
    search, cmd = search_command(), second_command()
    print(f"first call: {search} ({len(search.encode())} bytes)")
    print(f"second call: {len(cmd.encode())} bytes, {cmd.count(chr(10))} lines, sha256 {hashlib.sha256(cmd.encode()).hexdigest()}")
    tmp = Path(tempfile.mkdtemp(prefix="exp037_"))
    try:
        a = git_repo(tmp / "a", "from inline_snapshot import snapshot\n")
        found = run_in(a, search).strip()
        print("(a) search output:", found)
        assert found == "tests/test_a.py", found
        out = run_in(a, cmd).strip()
        print("(a) second-call output:", out.replace("\n", " | "))
        assert out.splitlines() == ["?? dirty_equals/", "?? inline_snapshot/"], out
        fa = files_of(a)
        assert sorted(fa) == ["dirty_equals/__init__.py", "inline_snapshot/__init__.py", "pkg/__init__.py",
                              "tests/test_a.py"], sorted(fa)
        run_in(a, cmd)
        assert files_of(a) == fa, "repeat of the second call changed files"
        print("(a) repeat of the second call: no change")

        b = git_repo(tmp / "b", "import pkg\n")
        found_b = run_in(b, search).strip()
        print("(b) search output:", found_b or "(empty)")
        assert found_b == "", found_b

        new_i = load("new_inline_snapshot", a / "inline_snapshot" / "__init__.py")
        new_d = load("new_dirty_equals", a / "dirty_equals" / "__init__.py")
        ref_i = load("ref_inline_snapshot", SHIMS / "inline_snapshot" / "__init__.py")
        ref_d = load("ref_dirty_equals", SHIMS / "dirty_equals" / "__init__.py")
        pn, pr = probes(new_i, new_d), probes(ref_i, ref_d)
        diffs = [i for i, (x, y) in enumerate(zip(pn, pr)) if x != y]
        print(f"probes: {len(pn)} compared, {len(diffs)} differ")
        assert len(pn) == len(pr) and not diffs, diffs
        print("ALL CHECKS PASS")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
