"""D1 (rounds/L-001): synthetic copy-exact edit samples from public code, with tool responses produced by the
harness's own read_file / edit_file functions on a local workspace.

  apptainer exec --bind /data/mmyatmau env/harness.sif python3 -I tools/lora/synth_edits.py \
      --n 4000 --seed 1 --out /data/mmyatmau/gemma4-lora/data/d1/synth-s1.jsonl

Source code: the CPython standard library inside env/harness.sif (PSF License 2.0). Every file used is listed with
its sha256 in <out>.sources.tsv. Stdout carries counts only.

The case mix targets the E4B base edit failures counted in L-001 (R-011 d1-d8, 2055 edit_file calls): old_string
lines that were never shown (588 of 808 not-found), shown lines that are not contiguous (184), indentation (34),
non-unique old_string (about 150), and a missing argument (142). Each sample is:
  user: an instruction naming the file, the function and the change;
  assistant: read_file on a window around the target, then edit_file with old_string copied from that output;
  variants:
  - `unique`: the one-line old_string occurs more than once, so the edit carries context lines;
  - `recover_notfound`: a first edit_file whose old_string has one realistic copy error (an identifier altered in
    one line, an invented line, part of the new code typed into old_string, a skipped line, a dropped blank
    line). Only an error the harness's own matcher rejects as not-found is used; re-indentation is tried too, but
    the flexible match almost always applies it. The real tool answers not-found, and the assistant reads the
    window again and copies it exactly.
  - `recover_multi`: a first edit_file with a non-unique line gets the real "occurs N times" error, then the
    assistant retries with context.
Every assistant message carries `train`: "call" (learn the tool call; thoughts stay masked) or "none" (context
only, used for the failed attempt). A sample is kept only if the final edit_file returned ok and the file now
equals the independently computed target.
"""
import argparse
import ast
import collections
import hashlib
import json
import os
import random
import re
import shutil
import sys
import sysconfig
import tempfile
from pathlib import Path
from types import SimpleNamespace

from swegemma.edit import apply_replacement
from swegemma.tools.workspace import make_edit_file, make_read_file

LIMITS = SimpleNamespace(max_stdout_chars=5000, max_file_lines=150, max_file_chars=10000)  # swegemma/budget.py


class LocalDocker:
    """The two copy calls read_file / edit_file make, mapped from /workspace to a local directory."""

    def __init__(self, root):
        self.root = Path(root)

    def _local(self, p):
        p = str(p)
        rel = p[len("/workspace/"):] if p.startswith("/workspace/") else p.lstrip("/")
        return self.root / rel

    def copy_from(self, cid, src, dest):
        s = self._local(src)
        if s.is_file():
            shutil.copyfile(s, dest)

    def copy_to(self, cid, local, dest_dir):
        d = self._local(dest_dir)
        d.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(local, d / Path(local).name)


def stdlib_files():
    root = Path(sysconfig.get_paths()["stdlib"])
    skip = re.compile(r"(^|/)(test|tests|idlelib|lib2to3|tkinter|turtledemo|ensurepip|site-packages|"
                      r"dist-packages|__pycache__|encodings|pydoc_data)(/|$)")
    out = []
    for p in sorted(root.rglob("*.py")):
        rel = p.relative_to(root).as_posix()
        if skip.search(rel):
            continue
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if 120 <= txt.count("\n") <= 4000 and "\t" not in txt and "\r" not in txt:
            out.append((rel, txt))
    return root, out


THOUGHT_READ = ["I need to look at `{f}` in `{p}` before changing it.",
                "Let me read the code around `{f}` first.",
                "First I will read the part of `{p}` that holds `{f}`."]
THOUGHT_EDIT = ["The lines to change are in the output above. I will copy them exactly as old_string.",
                "I have the exact text now. old_string is copied from the read output, character for character.",
                "Copying the target lines exactly from the output, then replacing them."]
THOUGHT_RETRY_NF = ["The edit failed because old_string did not match. I will read the same range again and "
                    "copy it exactly.",
                    "old_string was not found, so I typed it wrong. Reading the lines again to copy them."]
THOUGHT_RETRY_MULTI = ["That line occurs more than once. I will add the surrounding lines so old_string is unique."]


def functions(tree):
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and 4 <= n.end_lineno - n.lineno <= 80:
            yield n


def body_start(fn):
    b = fn.body
    if b and isinstance(b[0], ast.Expr) and isinstance(getattr(b[0], "value", None), ast.Constant) \
            and isinstance(b[0].value.value, str):
        b = b[1:]
    return b[0] if b else None


def edit_candidates(fn, lines, rng):
    """(kind, description, line index a, line index b, replacement lines) for one function; indices 0-based."""
    out = []
    # rename a local variable assigned in the function (not a parameter), every use inside the function
    params = {x.arg for x in fn.args.args + fn.args.kwonlyargs + fn.args.posonlyargs}
    stores = collections.Counter(n.id for n in ast.walk(fn) if isinstance(n, ast.Name)
                                 and isinstance(n.ctx, ast.Store) and n.id not in params and len(n.id) > 1)
    for name, _ in stores.most_common(2):
        uses = sorted({n.lineno - 1 for n in ast.walk(fn) if isinstance(n, ast.Name) and n.id == name})
        if uses and uses[-1] - uses[0] < 12:
            new = name + rng.choice(["_val", "_item", "_res", "_tmp"])
            seg = [re.sub(rf"\b{re.escape(name)}\b", new, lines[i]) if i in uses else lines[i]
                   for i in range(uses[0], uses[-1] + 1)]
            out.append(("rename", f"rename the local variable `{name}` to `{new}` everywhere inside it",
                        uses[0], uses[-1], seg))
    # change one integer or string literal
    for n in ast.walk(fn):
        if isinstance(n, ast.Constant) and n.lineno == n.end_lineno and type(n.value) in (int, str):
            i = n.lineno - 1
            src = lines[i][n.col_offset:n.end_col_offset]
            if type(n.value) is int and not isinstance(n.value, bool) and re.fullmatch(r"\d{1,4}", src):
                rep = str(n.value + 1)
            elif type(n.value) is str and 2 <= len(src) <= 30 and re.fullmatch(r"(['\"])[\w .,:-]*\1", src):
                rep = src[0] + src[1:-1] + "_x" + src[-1]
            else:
                continue
            if lines[i].count(src) != 1:
                continue
            out.append(("literal", f"change the literal {src} to {rep}", i, i, [lines[i].replace(src, rep)]))
            break
    # flip one comparison operator
    flips = {" == ": " != ", " != ": " == ", " < ": " <= ", " > ": " >= ", " is None": " is not None"}
    for i in range(fn.lineno, fn.end_lineno):
        for a, b in flips.items():
            if lines[i].count(a) == 1 and lines[i].lstrip().startswith(("if ", "elif ", "while ", "return ")):
                out.append(("flip", f"in the line `{lines[i].strip()}`, change `{a.strip()}` to `{b.strip()}`",
                            i, i, [lines[i].replace(a, b)]))
                break
        else:
            continue
        break
    # insert a guard before the first statement of the body
    first = body_start(fn)
    if first is not None and fn.args.args:
        p = next((x.arg for x in fn.args.args if x.arg not in ("self", "cls")), None)
        i = first.lineno - 1
        if p and first.lineno == first.end_lineno:
            ind = re.match(r"\s*", lines[i]).group(0)
            guard = [f"{ind}if {p} is None:", f"{ind}    raise ValueError(\"{p} is required\")"]
            out.append(("guard", f"raise ValueError(\"{p} is required\") at the start of the body when `{p}` "
                        f"is None", i, i, guard + [lines[i]]))
    return out


def unique_block(text_lines, content, a, b):
    """Smallest window [a', b'] around [a, b] (up to 6 extra lines) whose text occurs once in the file."""
    for extra in range(0, 7):
        for lo, hi in ((a - extra // 2, b + extra - extra // 2), (a, b + extra), (a - extra, b)):
            lo, hi = max(0, lo), min(len(text_lines) - 1, hi)
            block = "\n".join(text_lines[lo:hi + 1])
            if block.strip() and content.count(block) == 1:
                return lo, hi
    return None


def corruptions(rng, lines, lo, hi, ea, eb, repl, kind):
    """Candidate copy errors of the kinds counted in the E4B base traces (L-001): a line never shown (an invented
    or altered line, or the new code typed into old_string), shown lines that are not contiguous (a skipped or
    dropped blank line), and re-indentation. Returns [(kind, bad old_string lines)] in random order."""
    o = lines[lo:hi + 1]
    pre, post = lines[lo:ea], lines[eb + 1:hi + 1]
    out = []
    inner = list(range(1, len(o) - 1))
    blank = [i for i in inner if not o[i].strip()]
    if blank:
        j = rng.choice(blank)
        out.append(("drop_blank", o[:j] + o[j + 1:]))
    full = [i for i in inner if o[i].strip()]
    if full:
        j = rng.choice(full)
        out.append(("skip_line", o[:j] + o[j + 1:]))
    ind = [i for i, l in enumerate(o) if l.startswith("    ")]
    if ind:
        j = rng.choice(ind)
        out.append(("reindent", o[:j] + [o[j][4:] if rng.random() < 0.5 else "    " + o[j]] + o[j + 1:]))
    words = [i for i, l in enumerate(o) if re.search(r"[A-Za-z_]\w{3,}", l)]
    if words:  # an altered line: one identifier changed, as when a line is retyped from memory
        j = rng.choice(words)
        w = rng.choice(re.findall(r"[A-Za-z_]\w{3,}", o[j]))
        alt = rng.choice([w + "s", w[:-1], w.replace("_", "") if "_" in w else w.lower() + "_"])
        if alt != w:
            out.append(("altered_line", o[:j] + [re.sub(rf"\b{re.escape(w)}\b", alt, o[j], count=1)] + o[j + 1:]))
    if len(o) >= 2:  # an invented line next to real ones
        j = rng.randint(1, len(o) - 1)
        ws = re.match(r"\s*", o[j - 1]).group(0)
        out.append(("invented_line", o[:j] + [ws + rng.choice(["pass", "return None", "result = None",
                                                                 "# check the value"])] + o[j:]))
    if kind == "guard":  # part of the new code typed into old_string
        out.append(("new_in_old", pre + [repl[0], repl[-1]] + post))
    elif kind == "rename":
        diff = [i for i in range(len(repl)) if repl[i] != lines[ea + i]]
        if len(diff) >= 2:
            seg = [repl[i] if i == diff[0] else lines[ea + i] for i in range(len(repl))]
            out.append(("new_in_old", pre + seg + post))
    rng.shuffle(out)
    return out


def tool_rejects(content, old, new):
    """The error the harness's own matcher gives for this edit, or None if it would apply."""
    try:
        apply_replacement(content, old, new)
        return None
    except ValueError as e:
        return str(e)


def call(i, name, args):
    return {"id": f"call_{i}", "type": "function", "function": {"name": name, "arguments": args}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mix", default="plain:0.45,unique:0.2,recover_notfound:0.25,recover_multi:0.1")
    a = ap.parse_args()
    if not os.path.abspath(a.out).startswith("/data/mmyatmau/gemma4-lora/"):
        sys.exit("--out must be under /data/mmyatmau/gemma4-lora/")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    rng = random.Random(a.seed)
    mix = [(k, float(v)) for k, v in (x.split(":") for x in a.mix.split(","))]
    root, files = stdlib_files()
    counts, used = collections.Counter(), {}
    with tempfile.TemporaryDirectory() as ws, open(a.out, "w") as fo:
        ctx = SimpleNamespace(docker=LocalDocker(ws), container_id="local", harness=LIMITS,
                              check_budget=lambda count_tool_call=True: None)  # no budget object: no warning
        read_file, edit_file = make_read_file(ctx), make_edit_file(ctx)
        tries = 0
        while counts["kept"] < a.n and tries < a.n * 30:
            tries += 1
            rel, txt = rng.choice(files)
            try:
                fns = list(functions(ast.parse(txt)))
            except SyntaxError:
                continue
            if not fns:
                continue
            fn = rng.choice(fns)
            lines = txt.split("\n")
            cands = edit_candidates(fn, lines, rng)
            if not cands:
                counts["no_candidate"] += 1
                continue
            kind, desc, ea, eb, repl = rng.choice(cands)
            variant = rng.choices([m for m, _ in mix], [w for _, w in mix])[0]
            one_line_unique = txt.count("\n".join(lines[ea:eb + 1])) == 1
            if variant in ("unique", "recover_multi") and (ea != eb or one_line_unique):
                variant = "plain"
            win = unique_block(lines, txt, ea, eb)
            if win is None:
                counts["no_unique_window"] += 1
                continue
            lo, hi = win
            old = "\n".join(lines[lo:hi + 1])
            new = "\n".join(lines[lo:ea] + repl + lines[eb + 1:hi + 1])
            target = txt.replace(old, new, 1)
            path = "lib/" + rel
            dest = Path(ws) / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(txt, encoding="utf-8")
            r0 = max(1, lo + 1 - rng.randint(3, 25))
            r1 = min(len(lines), hi + 1 + rng.randint(3, 25))
            if r1 - r0 + 1 > LIMITS.max_file_lines:
                r1 = r0 + LIMITS.max_file_lines - 1
            fname = fn.name
            sysmsg = {"role": "system", "content": "{SYSTEM}"}
            user = {"role": "user", "content": f"In `{path}`, function `{fname}`: {desc}. Change nothing else."}
            msgs, k = [sysmsg, user], 0

            def turn(thought, name, args, train):
                nonlocal k
                k += 1
                c = call(k, name, args)
                msgs.append({"role": "assistant", "content": "", "reasoning_content": thought,
                             "tool_calls": [c], "train": train})
                res = (read_file if name == "read_file" else edit_file)(**args)
                msgs.append({"role": "tool", "tool_call_id": c["id"], "name": name,
                             "content": json.dumps(res, ensure_ascii=False)})
                return res

            rargs = {"filepath": path, "start_line": r0, "end_line": r1}
            res = turn(rng.choice(THOUGHT_READ).format(f=fname, p=path), "read_file", rargs, "call")
            if res.get("status") != "ok" or old not in res.get("content", ""):
                counts["window_not_in_read"] += 1
                continue
            if variant == "recover_notfound":
                pick = None
                for ck, bad in corruptions(rng, lines, lo, hi, ea, eb, repl, kind):
                    err = tool_rejects(txt, "\n".join(bad), new)
                    if err is None:
                        counts["corrupt_applied_" + ck] += 1  # the tool's flexible match would apply it
                    elif "not found" in err.lower():
                        pick = (ck, bad)
                        break
                    else:
                        counts["corrupt_other_error_" + ck] += 1
                if pick is None:
                    counts["corrupt_none_rejected"] += 1
                    variant = "plain"
                else:
                    ck, bad = pick
                    r = turn(rng.choice(THOUGHT_EDIT), "edit_file",
                             {"filepath": path, "old_string": "\n".join(bad), "new_string": new}, "none")
                    if r.get("status") == "ok" or "not found" not in (r.get("error_message") or "").lower():
                        counts["corrupt_tool_disagrees"] += 1
                        continue
                    counts["corrupt_" + ck] += 1
                    turn(rng.choice(THOUGHT_RETRY_NF), "read_file", rargs, "call")
            elif variant == "recover_multi":
                bad_old, bad_new = "\n".join(lines[ea:eb + 1]), "\n".join(repl)
                r = turn(rng.choice(THOUGHT_EDIT), "edit_file",
                         {"filepath": path, "old_string": bad_old, "new_string": bad_new}, "none")
                if r.get("status") == "ok" or "occurs" not in (r.get("error_message") or ""):
                    counts["multi_not_rejected"] += 1
                    continue
                res = turn(rng.choice(THOUGHT_RETRY_MULTI), "edit_file",
                           {"filepath": path, "old_string": old, "new_string": new}, "call")
                if not (res.get("status") == "ok" and dest.read_text(encoding="utf-8") == target):
                    counts["final_mismatch"] += 1
                    continue
            if variant != "recover_multi":
                res = turn(rng.choice(THOUGHT_EDIT), "edit_file",
                           {"filepath": path, "old_string": old, "new_string": new}, "call")
                if not (res.get("status") == "ok" and dest.read_text(encoding="utf-8") == target):
                    counts["final_mismatch"] += 1
                    continue
            counts["kept"] += 1
            counts["kept_" + variant] += 1
            counts["kept_" + kind] += 1
            used[rel] = hashlib.sha256(txt.encode()).hexdigest()
            fo.write(json.dumps({"messages": msgs, "tool_names": ["run_command", "read_file", "edit_file",
                                                                  "write_file", "get_status", "submit_patch"],
                                 "meta": {"source": "cpython-stdlib", "license": "PSF-2.0", "file": rel,
                                          "variant": variant, "kind": kind,
                                          "corrupt": ck if variant == "recover_notfound" else None, "old_lines": hi - lo + 1,
                                          "seed": a.seed}}, ensure_ascii=False) + "\n")
            dest.unlink()
    with open(a.out + ".sources.tsv", "w") as fs:
        fs.write(f"# CPython stdlib from env/harness.sif ({root}), PSF License 2.0\nfile\tsha256\n")
        for rel in sorted(used):
            fs.write(f"{rel}\t{used[rel]}\n")
    counts["tries"] = tries
    counts["source_files"] = len(used)
    print(json.dumps(dict(sorted(counts.items()))))


if __name__ == "__main__":
    main()
