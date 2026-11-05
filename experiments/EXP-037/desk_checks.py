"""EXP-037 desk checks B1-B3 (zero GPU), written after the critic's prereg review (experiments/EXP-037/critic.md).

B1  Which names from inline_snapshot / dirty_equals the graded files of the 15 gated tasks reach, and how they are
    used. "Graded files" = the files the test patch touches (Task.test_files = extract_test_files_from_patch,
    harness-stack), in their post-patch text, plus every conftest.py on their directory chain, plus the local modules
    those files import (transitively, resolved inside the base-commit snapshot). Then the size of the smallest
    stand-in command that covers those uses, and its projected turn cost.
B2  Inputs for costing a 3-call-cap mechanism run (Arm R's per-task non-turn time, mean s/turn, call slack past the cap).
B3  The 11 non-gated dev-48 ids the search reaches, with Arm R / RH as-run and re-graded resolves (EXP-036 summary).

Reads data/ and runs/ (gitignored); writes names, counts and ids only to --out.
Run from the repo root as:
    python -I -X utf8 experiments/EXP-037/desk_checks.py --tasks data/raw/tasks.jsonl \
        --snapshots data/local/snapshots --out experiments/EXP-037/desk_checks.json
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import statistics
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

PKGS = ("inline_snapshot", "dirty_equals")
EXP036_AGG = "experiments/EXP-036/aggregates.json"
EXP036_SUM = "experiments/EXP-036/summary.jsonl"
TRIGGER = "experiments/EXP-037/trigger_mining.json"
R_SUM = "experiments/EXP-028/armR/summary.jsonl"
RH_SUM = "experiments/EXP-028/armRH/summary.jsonl"
R_RESULTS = "runs/EXP-028-armR/task_results.jsonl"
INSERT = "experiments/EXP-037/insert_vendoring.md"

# measured inputs, all cited in the EXP file (section 2 and the critic's P3)
DECODE_TOK_S = 29.8          # EXP-032 P1 decode probe
RATE_PROSE = 0.2866          # tokens per byte, R -> RH prose section (prompt_cost.json)
RATE_CODE_HI = 0.39          # upper end assumed for code (unmeasured)
GREP_MEAN_S = 11.7           # Arm R forensics, grep/rg run_command turn, mean (286 calls)
WRITE_MEAN_S = 22.6          # Arm R forensics, heredoc-write turn, mean (48 calls)
GREP_CMD_BYTES = 85          # the first call's command
HIT, MISS, N48 = 26, 22, 48  # dev-48 reach of the search (trigger_mining.json)
HEADROOM_S = 13.8            # EXP-032 row d, (10.5 - 10.04 h) / 120

# ---------------------------------------------------------------- the smallest stand-in (B1)
# Two top-level files, written by one run_command in the same guarded form as the built insert.
# Covers exactly the names and forms B1 finds in the graded closure: Snapshot (as an annotation only),
# snapshot(v) inside ==, IsDict(d) | IsDict(d) chains inside ==, IsPartialDict(d) inside ==.
SMALL_IS = (
    "class Snapshot: pass\n"
    "def snapshot(v=None): return v\n"
)
SMALL_DE = (
    "class _Or:\n"
    "    def __init__(self, a, b): self.a, self.b = a, b\n"
    "    def __eq__(self, o): return self.a == o or self.b == o\n"
    "    def __or__(self, o): return _Or(self, o)\n"
    "class IsDict(dict):\n"
    "    def __eq__(self, o): return isinstance(o, dict) and dict(o) == dict(self)\n"
    "    def __or__(self, o): return _Or(self, o)\n"
    "class IsPartialDict(dict):\n"
    "    def __eq__(self, o): return isinstance(o, dict) and all(k in o and o[k] == v for k, v in self.items())\n"
)


def probe_small():
    """Equality on the observed forms only, small stand-in against tools/compat_shims. Returns (n probes, n differ)."""
    import importlib.util
    ref = {}
    for pkg in PKGS:
        spec = importlib.util.spec_from_file_location("ref_" + pkg, f"tools/compat_shims/{pkg}/__init__.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        ref[pkg] = mod
    small = {"inline_snapshot": {}, "dirty_equals": {}}
    exec(SMALL_IS, small["inline_snapshot"])
    exec(SMALL_DE, small["dirty_equals"])
    vals = [None, 0, 1, "a", [1, 2], dict(a=1), dict(a=1, b=2), dict(a=2), dict(b=2), dict(a=dict(x=1)), dict()]
    n = bad = 0
    for v in vals:
        for x in vals:
            r = (x == ref["inline_snapshot"].snapshot(v), ref["inline_snapshot"].snapshot(v) == x)
            s = (x == small["inline_snapshot"]["snapshot"](v), small["inline_snapshot"]["snapshot"](v) == x)
            n += 1; bad += r != s
    dicts = [d for d in vals if isinstance(d, dict)]
    for x in vals:
        for d1 in dicts:
            for d2 in dicts:
                for d3 in (None, dict(b=2)):
                    def build(m):
                        e = m["IsDict"](d1) | m["IsDict"](d2)
                        return e | m["IsDict"](d3) if d3 is not None else e
                    rm = vars(ref["dirty_equals"])
                    r = (x == build(rm), build(rm) == x)
                    s = (x == build(small["dirty_equals"]), build(small["dirty_equals"]) == x)
                    n += 1; bad += r != s
            r = (x == ref["dirty_equals"].IsPartialDict(d1), ref["dirty_equals"].IsPartialDict(d1) == x)
            s = (x == small["dirty_equals"]["IsPartialDict"](d1), small["dirty_equals"]["IsPartialDict"](d1) == x)
            n += 1; bad += r != s
    return n, bad
SMALL_CMD = (
    "cd /workspace\n"
    "if ! python -c 'import inline_snapshot' 2>/dev/null; then mkdir -p inline_snapshot; "
    "cat > inline_snapshot/__init__.py <<'EOF'\n" + SMALL_IS + "EOF\nfi\n"
    "if ! python -c 'import dirty_equals' 2>/dev/null; then mkdir -p dirty_equals; "
    "cat > dirty_equals/__init__.py <<'EOF'\n" + SMALL_DE + "EOF\nfi\n"
    "git status --short | head -5\n"
)


def load_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


# ---------------------------------------------------------------- test patch -> post-patch text
def parse_patch(tp: str):
    """{path: (created, [(old_start, old_len, [body lines])])}"""
    lines = (tp or "").splitlines()
    out, i = {}, 0
    while i < len(lines):
        if lines[i].startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ "):
            old = lines[i][4:].split("\t")[0].strip()
            new = lines[i + 1][4:].split("\t")[0].strip()
            path = new[2:] if new.startswith("b/") else new
            hunks = []
            i += 2
            while i < len(lines) and not (lines[i].startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ ")):
                m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", lines[i])
                if m:
                    hunks.append((int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1), []))
                elif hunks and lines[i][:1] in " +-":
                    hunks[-1][2].append(lines[i])
                elif hunks and lines[i] == "":
                    hunks[-1][2].append(" ")
                elif hunks and lines[i].startswith("\\"):
                    pass
                i += 1
            created = old == "/dev/null" or (len(hunks) == 1 and hunks[0][0] == 0 and hunks[0][1] == 0)
            if new != "/dev/null":
                out[path] = (created, hunks)
        else:
            i += 1
    return out


def apply_hunks(src_lines, hunks):
    """Apply by recorded old-line numbers; returns (new lines, ok)."""
    res, pos, ok = [], 0, True
    for start, olen, body in hunks:
        s = start - 1 if olen > 0 else start
        res.extend(src_lines[pos:s])
        pos = s
        for ln in body:
            tag, txt = ln[:1], ln[1:]
            if tag == "+":
                res.append(txt)
            else:
                if pos >= len(src_lines) or src_lines[pos].rstrip() != txt.rstrip():
                    ok = False
                if pos < len(src_lines):
                    res.append(src_lines[pos]) if tag == " " else None
                pos += 1
    res.extend(src_lines[pos:])
    return res, ok


class Snap:
    """All .py files of a base-commit snapshot, read in one sequential pass (random access into a .tgz is slow)."""

    def __init__(self, tgz: Path):
        self.files = {}
        with tarfile.open(tgz, "r|*") as tf:
            for m in tf:
                name = m.name[2:] if m.name.startswith("./") else m.name
                if m.isfile() and name.endswith(".py"):
                    self.files[name] = tf.extractfile(m).read().decode("utf-8", "replace")
        self.members = self.files

    def read(self, path):
        return self.files.get(path)

    def isfile(self, path):
        return path in self.files


# ---------------------------------------------------------------- closure and usage
def resolve_local(mod: str, level: int, cur: str, snap: Snap, post: dict):
    def exists(p):
        return p in post or snap.isfile(p)
    if level:
        base = cur.split("/")[:-1]
        if level > 1:
            base = base[: len(base) - (level - 1)]
        parts = base + (mod.split(".") if mod else [])
    else:
        parts = mod.split(".")
    stem = "/".join(parts)
    for cand in (stem + ".py", stem + "/__init__.py"):
        if exists(cand):
            return cand
    return None


def closure(graded, snap, post):
    seen, todo = set(), list(graded)
    for g in graded:  # conftest.py on the directory chain
        parts = g.split("/")[:-1]
        for k in range(len(parts) + 1):
            c = "/".join(parts[:k] + ["conftest.py"])
            if c in post or snap.isfile(c):
                todo.append(c)
    texts = {}
    while todo:
        f = todo.pop()
        if f in seen:
            continue
        seen.add(f)
        src = post.get(f)
        if src is None:
            src = snap.read(f)
        if src is None:
            continue
        texts[f] = src
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                r = resolve_local(node.module or "", node.level, f, snap, post)
                if r:
                    todo.append(r)
                if node.module is not None or node.level:
                    for a in node.names:  # from pkg import submodule
                        sub = ((node.module + ".") if node.module else "") + a.name
                        r2 = resolve_local(sub, node.level, f, snap, post)
                        if r2:
                            todo.append(r2)
            elif isinstance(node, ast.Import):
                for a in node.names:
                    r = resolve_local(a.name, 0, f, snap, post)
                    if r:
                        todo.append(r)
    return texts


def usage(texts):
    """names imported from the two packages and how each is used, over the closure."""
    imported = defaultdict(set)      # name -> files
    forms = defaultdict(Counter)     # name -> Counter of use forms
    kw = defaultdict(Counter)
    for f, src in texts.items():
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        local = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in PKGS:
                for a in node.names:
                    key = node.module.split(".")[0] + "." + a.name
                    imported[key].add(f)
                    local[a.asname or a.name] = key
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.split(".")[0] in PKGS:
                        imported[a.name + ".<module>"].add(f)
                        local[a.asname or a.name] = a.name + ".<module>"
        if not local:
            continue
        parents = {}
        for node in ast.walk(tree):
            for ch in ast.iter_child_nodes(node):
                parents[ch] = node
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in local:
                key = local[node.id]
                par = parents.get(node)
                if isinstance(par, (ast.ImportFrom, ast.alias)):
                    continue
                if isinstance(par, ast.Call) and par.func is node:
                    forms[key]["call_no_args" if not par.args and not par.keywords else
                               ("call_args" if not par.keywords else "call_kwargs")] += 1
                    for k in par.keywords:
                        kw[key][k.arg or "**"] += 1
                    gp = parents.get(par)
                    if isinstance(gp, ast.Attribute):
                        forms[key]["result_attr:" + gp.attr] += 1
                    if isinstance(gp, ast.BinOp) and isinstance(gp.op, ast.BitOr):
                        forms[key]["in_bitor"] += 1
                        top = gp
                        while isinstance(parents.get(top), ast.BinOp) and isinstance(parents[top].op, ast.BitOr):
                            top = parents[top]
                        n_ops = sum(isinstance(x, ast.BinOp) and isinstance(x.op, ast.BitOr) for x in ast.walk(top))
                        forms[key]["in_bitor_chain_of_%d_operands" % (n_ops + 1)] += 1
                        leaves, stack = [], [top]
                        while stack:
                            x = stack.pop()
                            if isinstance(x, ast.BinOp) and isinstance(x.op, ast.BitOr):
                                stack += [x.left, x.right]
                            else:
                                leaves.append(x)
                        other = sum(not (isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id in local)
                                    for x in leaves)
                        if other:
                            forms[key]["bitor_with_untracked_operand"] += 1
                        if isinstance(parents.get(top), ast.Compare):
                            forms[key]["bitor_in_compare:" + type(parents[top].ops[0]).__name__] += 1
                    if isinstance(gp, ast.Compare):
                        forms[key]["compare_op:" + type(gp.ops[0]).__name__] += 1
                    if isinstance(gp, ast.Compare):
                        forms[key]["in_compare"] += 1
                elif isinstance(par, ast.Subscript) and par.value is node:
                    forms[key]["subscript"] += 1
                elif isinstance(par, ast.Attribute) and par.value is node:
                    forms[key]["attr:" + par.attr] += 1
                elif isinstance(par, ast.BinOp) and isinstance(par.op, ast.BitOr):
                    forms[key]["bare_in_bitor"] += 1
                else:
                    forms[key]["bare:" + type(par).__name__] += 1
    return imported, forms, kw


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--snapshots", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    tasks = {t["instance_id"]: t for t in load_jsonl(a.tasks)}
    agg = json.load(open(EXP036_AGG, encoding="utf-8"))
    gated = agg["gated_ids"]
    out = {"gated_ids": gated}

    # ------------------------------------------------ B1
    per_task, all_imp, all_forms, all_kw = {}, Counter(), defaultdict(Counter), defaultdict(Counter)
    tree_imp = Counter()
    for tid in gated:
        snap = Snap(Path(a.snapshots) / f"{tid}.tgz")
        pp = parse_patch(tasks[tid]["test_patch"])
        post, applied = {}, {}
        for path, (created, hunks) in pp.items():
            base = [] if created else (snap.read(path) or "").splitlines()
            new, ok = apply_hunks(base, hunks)
            post[path] = "\n".join(new) + "\n"
            applied[path] = ok
        graded = [p for p in pp if p.endswith(".py")]
        texts = closure(graded, snap, post)
        imp, forms, kw = usage(texts)
        imp_direct, _, _ = usage({p: post[p] for p in graded})
        # the whole tests tree at base commit, for comparison with the critic's "tests tree" count
        tree_names = set()
        for name in snap.members:
            if name.endswith(".py") and re.search(r"(^|/)tests?/", name):
                try:
                    t_ast = ast.parse(snap.read(name) or "")
                except SyntaxError:
                    continue
                for node in ast.walk(t_ast):
                    if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in PKGS:
                        for al in node.names:
                            tree_names.add(node.module.split(".")[0] + "." + al.name)
        for k in tree_names:
            tree_imp[k] += 1
        per_task[tid] = {
            "graded_py_files": len(graded),
            "patch_applied_cleanly": all(applied.get(p, True) for p in graded),
            "closure_files": len(texts),
            "closure_files_importing_pkgs": len({f for fs in imp.values() for f in fs}),
            "names": sorted(imp),
            "names_in_test_patch_files": sorted(imp_direct),
            "tests_tree_names_not_in_closure": sorted(tree_names - set(imp)),
        }
        for k in imp:
            all_imp[k] += 1
        for k, c in forms.items():
            all_forms[k].update(c)
        for k, c in kw.items():
            all_kw[k].update(c)
    out["B1"] = {
        "per_task": per_task,
        "tasks_reaching_name": dict(sorted(all_imp.items())),
        "use_forms": {k: dict(v) for k, v in sorted(all_forms.items())},
        "keywords": {k: dict(v) for k, v in sorted(all_kw.items())},
        "tests_tree_tasks_per_name": dict(sorted(tree_imp.items())),
    }
    built = open(INSERT, encoding="utf-8").read()
    mm = re.search(r"copied exactly:\n```\n(.*?)```\n", built, re.S)
    built_cmd = mm.group(1)
    def cost(nbytes):
        lo, hi = nbytes * RATE_PROSE, nbytes * RATE_CODE_HI
        return {"bytes": nbytes, "tokens": [round(lo), round(hi)], "gen_s": [round(lo / DECODE_TOK_S, 1), round(hi / DECODE_TOK_S, 1)]}
    def delta(write_turn_s):
        hit = GREP_MEAN_S + write_turn_s
        return round(HIT / N48 * hit + MISS / N48 * GREP_MEAN_S, 1)
    small_b = len(SMALL_CMD.encode())
    built_b = len(built_cmd.encode())
    # write turn modelled as a grep-like turn (11.7 s mean) plus generating the bytes beyond the 85-byte grep [I]
    rows = {}
    for name, nb in (("built", built_b), ("small", small_b)):
        c = cost(nb)
        extra = [round((nb - GREP_CMD_BYTES) * r / DECODE_TOK_S, 1) for r in (RATE_PROSE, RATE_CODE_HI)]
        c["write_turn_model_s"] = [round(GREP_MEAN_S + e, 1) for e in extra]
        c["delta_8min_model_s"] = [delta(GREP_MEAN_S + e) for e in extra]
        rows[name] = c
    rows["built"]["delta_8min_forensics_means_s"] = delta(WRITE_MEAN_S)
    rows["floor_any_second_turn"] = {"note": "second turn at the grep-turn mean, zero extra bytes",
                                     "delta_8min_s": delta(GREP_MEAN_S)}
    rows["floor_miss_only"] = {"note": "grep turn on every task, no second turn", "delta_8min_s": round(GREP_MEAN_S, 1)}
    rows["headroom_s"] = HEADROOM_S
    rows["small_cmd_sha256"] = hashlib.sha256(SMALL_CMD.encode()).hexdigest()
    rows["small_cmd_has_braces"] = ("{" in SMALL_CMD) or ("}" in SMALL_CMD)
    rows["small_cmd_lines"] = SMALL_CMD.count("\n")
    rows["small_file_bytes"] = {"inline_snapshot": len(SMALL_IS.encode()), "dirty_equals": len(SMALL_DE.encode())}
    one = [round(GREP_MEAN_S + len(SMALL_CMD.encode()) * r / DECODE_TOK_S, 1) for r in (RATE_PROSE, RATE_CODE_HI)]
    rows["one_call_small_every_task_s"] = {"note": "grep and small write in one command on all 48 tasks [I]", "delta_8min_s": one}
    pn, pb = probe_small()
    rows["small_probes_vs_compat_shims"] = {"n": pn, "differ": pb}
    out["B1"]["cost"] = rows

    # ------------------------------------------------ B2 inputs
    rs = load_jsonl(R_SUM)
    rr = load_jsonl(R_RESULTS)
    turns = sum(r["n_turns"] for r in rs)
    out["B2_inputs"] = {
        "R_wall_s_sum_48": round(sum(r["wall_s"] for r in rs), 1),
        "R_turns_48": turns,
        "R_mean_s_per_turn_48": round(13824 / turns, 2),  # 230.4 min agent wall (run_forensics) / turns
        "R_calls_past_cap_on_capped": sorted(Counter(r["tool_calls"] - r["max_tool_calls"] for r in rr
                                                     if r["tool_calls"] >= r["max_tool_calls"]).items()),
        "R_n_calls_minus_cap_on_capped": sorted(Counter(r["n_calls"] - 28 for r in rs if r["calls_cap_hit"]).items()),
        "R_turns_minus_calls_median": statistics.median(r["n_turns"] - r["n_calls"] for r in rs),
    }
    b2 = out["B2_inputs"]
    non_turn = (b2["R_wall_s_sum_48"] - 13824) / 48       # task wall not spent in turns, per task
    spt = b2["R_mean_s_per_turn_48"]
    extra_turns = b2["R_turns_minus_calls_median"]       # non-call turns per task
    hit_agent = [GREP_MEAN_S + w + spt + extra_turns * spt for w in (WRITE_MEAN_S, rows["built"]["write_turn_model_s"][1])]
    miss_agent = GREP_MEAN_S + 2 * spt + extra_turns * spt
    est = {}
    for label, n_hit, n_miss in (("gated-8", 8, 0), ("gated-8 plus 3 miss ids", 8, 3)):
        for ov in (444.8, 516.7):
            lo = ov + n_hit * (non_turn + hit_agent[0] + 15) + n_miss * (non_turn + miss_agent + 15)
            hi = ov + n_hit * (non_turn + hit_agent[1] + 20) + n_miss * (non_turn + miss_agent + 20)
            est[f"{label}, overhead {ov} s"] = [round(lo), round(hi), round(lo / 3600, 2), round(hi / 3600, 2)]
        n = n_hit + n_miss
        est[f"{label}, ceiling at max_time_minutes 2"] = [round(516.7 + n * (120 + 20)), round((516.7 + n * 140) / 3600, 2)]
    out["B2_estimate"] = {"non_turn_s_per_task": round(non_turn, 1), "hit_agent_s": [round(x, 1) for x in hit_agent],
                          "miss_agent_s": round(miss_agent, 1), "setup_and_grade_allowance_s": [15, 20],
                          "seconds_lo_hi_hours_lo_hi": est}

    # ------------------------------------------------ B3
    trig = json.load(open(TRIGGER, encoding="utf-8"))
    reach = trig["snapshot_reach"]
    reach_ids = reach["gated_hit"] + reach["nongated_hit"]
    s36 = {r["task_id"]: r for r in load_jsonl(EXP036_SUM)}
    non = sorted(t for t in reach_ids if t not in gated)
    out["B3"] = {
        "nongated_reach_ids": non,
        "n": len(non),
        "R_as_run_resolved": sorted(t for t in non if s36[t]["R_resolved_as_run"]),
        "RH_as_run_resolved": sorted(t for t in non if s36[t]["RH_resolved_as_run"]),
        "both_as_run_resolved": sorted(t for t in non if s36[t]["R_resolved_as_run"] and s36[t]["RH_resolved_as_run"]),
        "R_regraded_resolved": sorted(t for t in non if s36[t]["R_resolved_regraded"]),
        "RH_regraded_resolved": sorted(t for t in non if s36[t]["RH_resolved_regraded"]),
    }
    rmap = {r["task_id"]: r for r in rs}
    out["B3"]["R_cost_on_R_resolved"] = {
        t: {k: rmap[t][k] for k in ("n_calls", "wall_s", "calls_cap_hit", "time_cap_hit")}
        for t in out["B3"]["R_as_run_resolved"]}
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
