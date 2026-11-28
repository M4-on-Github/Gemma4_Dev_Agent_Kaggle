"""Knowledge probe (2026-11-28): how well does a served Gemma know the public libraries installed in the task
environments? No task data is read; only the installed packages' source (public libraries) is parsed with `ast`.

  sbatch -J heng_probe slurm/lora_py.sbatch P-001-e4b lib_probe.py --model models/gemma-4-e4b-it-qat-w4a16-ct \
      --envs env/taskenvs/<one env per repository> --out /data/mmyatmau/gemma4-lora/probe/e4b.json

Items, per library (top-level package), built from public `def`s in its modules:
- EXIST: "Which of these is a function or class defined in module M?" one real name, three real names from other
  libraries' modules (plausible, wrong place).
- PARAM: "Which of these is a parameter of M.f?" one real parameter, three parameters of other functions that f
  does not have.
The answer is read from the next-token logits over the four letters (no sampling, no thinking), so a library costs
a few seconds. Chance is 0.25. Stdout: one row per library and the totals.
"""
import argparse
import ast
import collections
import json
import os
import random

SKIP = {"pip", "setuptools", "wheel", "pkg_resources", "_distutils_hack", "tests", "test", "__pycache__"}


def scan(env, per_lib_modules=60):
    """{lib: [(module, name, [params])]} from the public top-level defs of each package."""
    out = collections.defaultdict(list)
    for lib in sorted(os.listdir(env)):
        root = os.path.join(env, lib)
        if lib in SKIP or lib.startswith(("_", ".")) or lib.endswith((".dist-info", ".py", ".pth", ".so")) \
                or not os.path.isfile(os.path.join(root, "__init__.py")):
            continue
        n = 0
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if not d.startswith(("_", ".")) and d not in SKIP]
            for f in sorted(fn):
                if not f.endswith(".py") or (f.startswith("_") and f != "__init__.py"):
                    continue
                n += 1
                if n > per_lib_modules:
                    break
                rel = os.path.relpath(os.path.join(dp, f), env)[:-3].replace(os.sep, ".")
                mod = rel[:-9] if rel.endswith(".__init__") else rel
                try:
                    tree = ast.parse(open(os.path.join(dp, f), encoding="utf-8", errors="replace").read())
                except (SyntaxError, ValueError):
                    continue
                for node in tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                        ps = [x.arg for x in node.args.args + node.args.kwonlyargs if x.arg not in ("self", "cls")]
                        out[lib].append((mod, node.name, ps))
                    elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                        ps = []
                        for b in node.body:
                            if isinstance(b, ast.FunctionDef) and b.name == "__init__":
                                ps = [x.arg for x in b.args.args + b.args.kwonlyargs if x.arg not in ("self", "cls")]
                        out[lib].append((mod, node.name, ps))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--envs", nargs="+", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--per-lib", type=int, default=30)
    p.add_argument("--min-defs", type=int, default=12)
    p.add_argument("--device-map", default="single", choices=("single", "auto"))
    p.add_argument("--seed", type=int, default=1)
    a = p.parse_args()
    rng = random.Random(a.seed)

    defs = collections.defaultdict(list)
    for env in a.envs:
        for lib, items in scan(env).items():
            if lib not in defs:
                defs[lib] = items
    defs = {k: v for k, v in defs.items() if len(v) >= a.min_defs}
    all_names = [(lib, n) for lib, v in defs.items() for _, n, _ in v]
    all_params = sorted({q for v in defs.values() for _, _, ps in v for q in ps if len(q) > 2})
    items = []
    for lib, v in sorted(defs.items()):
        own = {n for _, n, _ in v}
        pick = rng.sample(v, min(a.per_lib, len(v)))
        for mod, name, ps in pick:
            wrong = []
            while len(wrong) < 3:
                l2, n2 = rng.choice(all_names)
                if l2 != lib and n2 not in own and n2 not in wrong and n2 != name:
                    wrong.append(n2)
            items.append({"lib": lib, "kind": "EXIST", "q": f"Which of these is a function or class defined in the "
                          f"Python module `{mod}`?", "right": name, "wrong": wrong})
            real = [q for q in ps if len(q) > 2]
            if real:
                right = rng.choice(real)
                wrong = []
                while len(wrong) < 3:
                    c = rng.choice(all_params)
                    if c not in ps and c not in wrong:
                        wrong.append(c)
                items.append({"lib": lib, "kind": "PARAM", "q": f"Which of these is a parameter of `{mod}.{name}`?",
                              "right": right, "wrong": wrong})

    import torch
    from transformers import AutoModelForImageTextToText, AutoTokenizer, CompressedTensorsConfig
    tok = AutoTokenizer.from_pretrained(a.model)
    model = AutoModelForImageTextToText.from_pretrained(
        a.model, dtype=torch.bfloat16, attn_implementation="sdpa",
        device_map=({"": 0} if a.device_map == "single" else "auto"),
        max_memory=(None if a.device_map == "single" else {i: "30GiB" for i in range(torch.cuda.device_count())}),
        quantization_config=CompressedTensorsConfig(run_compressed=False))
    model.eval()
    letters = "ABCD"
    lid = [tok(x, add_special_tokens=False)["input_ids"][-1] for x in letters]
    res = collections.defaultdict(lambda: [0, 0])
    for it in items:
        opts = [it["right"]] + it["wrong"]
        rng.shuffle(opts)
        body = it["q"] + "\n" + "\n".join(f"{c}. {o}" for c, o in zip(letters, opts)) + \
            "\nAnswer with the letter only."
        text = tok.apply_chat_template([{"role": "user", "content": body}], tokenize=False,
                                       add_generation_prompt=True, enable_thinking=False)
        ids = tok(text, add_special_tokens=False, return_tensors="pt")["input_ids"].to("cuda")
        with torch.no_grad():
            lg = model(input_ids=ids).logits[0, -1]
        guess = letters[int(torch.tensor([lg[i] for i in lid]).argmax())]
        ok = opts[letters.index(guess)] == it["right"]
        for key in ((it["lib"], it["kind"]), ("ALL", it["kind"])):
            res[key][0] += ok
            res[key][1] += 1
    rows = []
    for lib in sorted({k[0] for k in res}):
        e, pm = res.get((lib, "EXIST"), [0, 0]), res.get((lib, "PARAM"), [0, 0])
        rows.append({"lib": lib, "exist": round(e[0] / max(1, e[1]), 2), "exist_n": e[1],
                     "param": round(pm[0] / max(1, pm[1]), 2), "param_n": pm[1]})
    rows.sort(key=lambda r: (r["lib"] != "ALL", r["exist"] + r["param"]))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(rows, open(a.out, "w"), indent=1)
    for r in rows:
        print("%-28s exist %.2f (n=%d)  param %.2f (n=%d)" % (r["lib"], r["exist"], r["exist_n"], r["param"], r["param_n"]))


if __name__ == "__main__":
    main()
