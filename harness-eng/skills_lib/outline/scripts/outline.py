"""Print the outline of one source file: every class and function with its line range, one per line.

harness-eng R-026 (sweep lever "outline"). Pure file reads: it starts no other program, makes no connection and
writes nothing. The path is relative to the repository root, found as in change-count: PYTHONPATH entries, then
sys.path, then /workspace, then the current directory. Python files are parsed with ast; other files fall back to
lines that start a def, class or function. Output is capped at 150 lines. Always ends normally.
"""
import ast
import os
import re
import sys

CAP = 150


def find_root():
    seen = []
    for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep) + list(sys.path) + ["/workspace", os.getcwd()]:
        if not entry:
            continue
        path = os.path.abspath(entry)
        if path in seen:
            continue
        seen.append(path)
        if os.path.isdir(os.path.join(path, ".git")):
            return path
    return None


def arg_path(argv):
    rest = [a for a in argv if a != "--"]
    for i, a in enumerate(rest):
        if a in ("--path", "--file", "--file_path", "--filepath") and i + 1 < len(rest):
            return rest[i + 1]
    plain = [a for a in rest if not a.startswith("--")]
    return plain[0] if plain else None


def sig(node):
    a = node.args
    names = [x.arg for x in list(getattr(a, "posonlyargs", [])) + a.args]
    if a.vararg:
        names.append("*" + a.vararg.arg)
    names += [x.arg for x in a.kwonlyargs]
    if a.kwarg:
        names.append("**" + a.kwarg.arg)
    return "(" + ", ".join(names) + ")"


def walk(body, depth, out):
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            end = getattr(node, "end_lineno", node.lineno)
            if isinstance(node, ast.ClassDef):
                out.append("%sL%d-%d class %s" % ("  " * depth, start, end, node.name))
            else:
                kind = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
                out.append("%sL%d-%d %s %s%s" % ("  " * depth, start, end, kind, node.name, sig(node)))
            walk(node.body, depth + 1, out)


def main():
    rel = arg_path(sys.argv[1:])
    root = find_root()
    if not rel or root is None:
        print("usage: args = [\"relative/path/to/file.py\"]")
        return
    path = os.path.abspath(os.path.join(root, rel.replace("/workspace/", "", 1) if rel.startswith("/workspace/") else rel))
    if not path.startswith(root + os.sep) or not os.path.isfile(path):
        print("not a file in the repository: " + rel)
        return
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    n = text.count("\n") + (0 if text.endswith("\n") else 1)
    out = []
    try:
        if not path.endswith(".py"):
            raise SyntaxError
        walk(ast.parse(text).body, 0, out)
    except (SyntaxError, ValueError, RecursionError):
        out = []
        pat = re.compile(r"^\s*(async\s+def|def|class|function|func|fn|pub\s+fn)\s+\w+")
        for i, line in enumerate(text.splitlines(), 1):
            if pat.match(line):
                out.append("L%d %s" % (i, line.strip()[:100]))
    print("%s: %d lines, %d entries" % (rel, n, len(out)))
    for line in out[:CAP]:
        print(line)
    if len(out) > CAP:
        print("... %d more entries" % (len(out) - CAP))


try:
    main()
except Exception as e:  # never fail the call
    print("outline failed: " + type(e).__name__)
