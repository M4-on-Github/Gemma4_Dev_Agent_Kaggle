"""L-010 (2026-11-27): gradient-free, computed rank-1 adapters ("weight-space" edits) for the E4B solver.

  python3 -I tools/lora/wsp_edit.py --model models/gemma-4-e4b-it-qat-w4a16-ct --tools .../schema/tools.json \
      --pos .../d5/e4b-solver-lfold-a.jsonl --neg .../d6/e4b-solver-unres-lfold-a.jsonl --out .../adapters/L-010-wsp

What it does, with no gradient step:
1. Decision points. Each row is rendered exactly as train_lora.py renders it; a decision point is the last token before
   an assistant turn starts. POS = turns whose call is edit_file/write_file in resolved rows. NEG = turns at call
   index >= --stall-from whose call is not an edit, in unresolved rows that never edit ("stalled").
2. Per layer L: delta_L = mean residual at POS - mean residual at NEG, on the "fit" half of the tasks. The held-out
   half gives each layer's separation (AUC of the projection on delta_L): the architecture map.
3. Candidates: add k * delta_L to the residual stream at layer L through a rank-1 change of that layer's
   mlp.down_proj: dW = k * delta_L a^T with a = mu / (mu.mu), mu = the mean input of down_proj over all tokens of
   the fit rows, so that a^T x is 1 on average.
4. Proxy score, on held-out tasks, by greedy generation from the decision point with dW added to the weight: the
   share of stalled points whose next call is an edit (wanted up), the same share on early points (call index < 2
   of resolved rows; wanted flat), and the share with no parsable call (wanted flat).
5. Every candidate is written as a served-format adapter (rank 1, alpha 1, only the edited modules).
Stdout carries counts and scores only. Rows hold trace text and stay under /data/mmyatmau/gemma4-lora.
"""
import argparse
import collections
import json
import os
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import train_lora as TL  # noqa: E402  (spans(), template markers)

EDITS = ("edit_file", "write_file")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--tools", required=True)
    p.add_argument("--pos", required=True)
    p.add_argument("--neg", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--tool-names", default="run_command,read_file,edit_file,write_file,get_status")
    p.add_argument("--stall-from", type=int, default=8)
    p.add_argument("--max-len", type=int, default=12000)
    p.add_argument("--rows-per-set", type=int, default=70)
    p.add_argument("--eval-stalled", type=int, default=40)
    p.add_argument("--eval-early", type=int, default=30)
    p.add_argument("--new-tokens", type=int, default=320)
    p.add_argument("--ks", default="1,2,4")
    p.add_argument("--layers", default="", help="comma list; default: the 2 best layers by held-out AUC in 6..34")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--serve-hours", type=float, default=0.0, help="then serve candidate specs from <out>/queue")
    p.add_argument("--device-map", default="single", choices=("single", "auto"))
    a = p.parse_args()

    import torch
    from safetensors.torch import save_file
    from transformers import AutoModelForImageTextToText, AutoTokenizer, CompressedTensorsConfig

    rng = random.Random(a.seed)
    tok = AutoTokenizer.from_pretrained(a.model)
    alltools = json.load(open(a.tools))
    names = a.tool_names.split(",")
    tools = [alltools[n] for n in names]

    def points(path, want):
        """[(task, text, char offset b, call index, is_edit)] per row -> list of rows with their decision points."""
        out = []
        for line in open(path):
            r = json.loads(line)
            msgs = r["messages"]
            asst = [m for m in msgs if m["role"] == "assistant"]
            calls = [(m.get("tool_calls") or [{}])[0].get("function", {}).get("name") for m in asst]
            row_edits = any(c in EDITS for c in calls)
            if want == "neg" and row_edits:
                continue
            text = tok.apply_chat_template(msgs, tools=tools, tokenize=False, enable_thinking=True)
            sp = TL.spans(text, msgs, "all")
            if sp is None or len(sp) != len(asst):
                continue
            pts = []
            for k, ((b, _), c) in enumerate(zip(sp, calls)):
                if c is None:
                    continue
                pts.append((b, k, c in EDITS))
            out.append({"task": r["meta"]["instance_id"], "text": text, "pts": pts})
        return out

    pos_rows, neg_rows = points(a.pos, "pos"), points(a.neg, "neg")
    tasks = sorted({r["task"] for r in pos_rows} | {r["task"] for r in neg_rows})
    rng.shuffle(tasks)
    fit_tasks = set(tasks[: len(tasks) // 2])

    def encode(row):
        enc = tok(row["text"], add_special_tokens=False, return_offsets_mapping=True)
        ids, offs = enc["input_ids"], enc["offset_mapping"]
        ends = {e: i for i, (s, e) in enumerate(offs)}
        return ids, offs, ends

    model = AutoModelForImageTextToText.from_pretrained(
        a.model, dtype=torch.bfloat16, attn_implementation="sdpa", device_map=({"": 0} if a.device_map == "single" else "auto"),
        max_memory=(None if a.device_map == "single" else {i: "30GiB" for i in range(torch.cuda.device_count())}),
        quantization_config=CompressedTensorsConfig(run_compressed=False))
    model.eval()
    layers = model.model.language_model.layers
    nl = len(layers)
    dev = torch.device("cuda")

    mlp_in_sum = [None] * nl
    mlp_in_n = [0]
    grab = {"on": False}

    def mk(i):
        def hook(mod, inp):
            if grab["on"]:
                x = inp[0][0].float()
                s = x.sum(0).cpu()
                mlp_in_sum[i] = s if mlp_in_sum[i] is None else mlp_in_sum[i] + s
                if i == 0:
                    mlp_in_n[0] += x.shape[0]
        return hook

    hooks = [layers[i].mlp.down_proj.register_forward_pre_hook(mk(i)) for i in range(nl)]
    # residual after each layer, only at the decision positions (all positions of all layers do not fit for the 31B)
    res_idx, res_out = [None], [None] * nl

    def mkres(i):
        def hook(mod, inp, out):
            if res_idx[0] is not None:
                h = out[0] if isinstance(out, (tuple, list)) else out
                res_out[i] = h[0, res_idx[0]].float().cpu()
        return hook

    hooks += [layers[i].register_forward_hook(mkres(i)) for i in range(nl)]

    def collect(rows, sel, cap, mu=False):
        """residuals [n, nl, d] at the decision points sel(pt) of up to `cap` rows; -> (tensor, [task])."""
        feats, owner, used = [], [], 0
        rows = rows[:]
        rng.shuffle(rows)
        for r in rows:
            if used >= cap:
                break
            pts = [pt for pt in r["pts"] if sel(pt)]
            if not pts:
                continue
            e = encode(r)
            if e is None:
                continue
            ids, offs, ends = e
            idx = [ends.get(b) for b, _, _ in pts]
            idx = [i for i in idx if i is not None and i < a.max_len]  # long rows: use the prefix that fits
            if not idx:
                continue
            ids = ids[: max(idx) + 1]
            grab["on"] = mu
            res_idx[0], res_out[:] = idx, [None] * nl
            with torch.no_grad():
                model(input_ids=torch.tensor([ids], device=dev))
            grab["on"] = False
            res_idx[0] = None
            feats.append(torch.stack(res_out, 1))  # [pts, nl, d]
            owner += [r["task"]] * len(idx)
            used += 1
        return (torch.cat(feats) if feats else torch.zeros(0, nl, 1)), owner

    P, Pt = collect(pos_rows, lambda pt: pt[2], a.rows_per_set, mu=True)
    N, Nt = collect(neg_rows, lambda pt: (not pt[2]) and pt[1] >= a.stall_from, a.rows_per_set, mu=True)
    for h in hooks:
        h.remove()
    pf = torch.tensor([t in fit_tasks for t in Pt])
    nf = torch.tensor([t in fit_tasks for t in Nt])
    delta = P[pf].mean(0) - N[nf].mean(0)  # [nl, d]
    resid_norm = torch.cat([P[pf], N[nf]]).norm(dim=-1).mean(0)

    def auc(x, y):
        if len(x) == 0 or len(y) == 0:
            return float("nan")
        return float((x[:, None] > y[None, :]).float().mean() + 0.5 * (x[:, None] == y[None, :]).float().mean())

    amap = []
    for L in range(nl):
        d = delta[L] / delta[L].norm()
        amap.append({"layer": L, "delta_norm": round(float(delta[L].norm()), 3),
                     "resid_norm": round(float(resid_norm[L]), 3),
                     "auc_heldout": round(auc(P[~pf][:, L] @ d, N[~nf][:, L] @ d), 3)})
    print(json.dumps({"points": {"pos": len(Pt), "neg": len(Nt), "pos_fit": int(pf.sum()), "neg_fit": int(nf.sum()),
                                 "tasks": len(tasks)}, "mlp_tokens": mlp_in_n[0]}))
    print(json.dumps({"architecture_map": amap}))
    if a.layers:
        pick = [int(x) for x in a.layers.split(",")]
    else:
        cand = [m for m in amap if 6 <= m["layer"] <= min(34, nl - 2) and m["auc_heldout"] == m["auc_heldout"]]
        pick = [m["layer"] for m in sorted(cand, key=lambda m: -m["auc_heldout"])[:2]]
        if not pick:
            sys.exit("no layer has a held-out AUC (a set has no held-out points)")
    print(json.dumps({"layers_picked": pick}))

    def dw(L, k):
        mu = mlp_in_sum[L] / mlp_in_n[0]
        avec = mu / (mu @ mu)
        return (k * delta[L]), avec  # B column [d], A row [mlp]

    cands = [("base", [])]
    for k in [float(x) for x in a.ks.split(",")]:
        cands.append((f"L{pick[0]}-k{k:g}", [(pick[0], k)]))
    if len(pick) > 1:
        cands.append((f"L{pick[1]}-k2", [(pick[1], 2.0)]))
        cands.append((f"L{pick[0]}+L{pick[1]}-k1", [(pick[0], 1.0), (pick[1], 1.0)]))
        cands.append((f"L{pick[0]}+L{pick[1]}-k2", [(pick[0], 2.0), (pick[1], 2.0)]))

    def eval_points(rows, sel, n):
        out = []
        rows = [r for r in rows if r["task"] not in fit_tasks]
        rng.shuffle(rows)
        for r in rows:
            pts = [pt for pt in r["pts"] if sel(pt)]
            if not pts:
                continue
            b = rng.choice(pts)[0]
            ids = tok(r["text"][:b], add_special_tokens=False)["input_ids"]
            if len(ids) <= a.max_len:
                out.append(ids)
            if len(out) >= n:
                break
        return out

    stalled = eval_points(neg_rows, lambda pt: (not pt[2]) and pt[1] >= a.stall_from, a.eval_stalled)
    early = eval_points(pos_rows, lambda pt: pt[1] < 2, a.eval_early)
    call_re = re.compile(re.escape(TL.TC_OPEN) + r"\s*(?:call:)?\s*([a-z_]+)")

    def next_call(ids):
        with torch.no_grad():
            g = model.generate(input_ids=torch.tensor([ids], device=dev), max_new_tokens=a.new_tokens,
                               do_sample=False, use_cache=True)
        txt = tok.decode(g[0, len(ids):], skip_special_tokens=False)
        m = call_re.search(txt)
        return m.group(1) if m else None

    os.makedirs(a.out, exist_ok=True)
    results = []

    def factors(e):
        """One rank-1 factor pair (B [d], A [mlp]) for an edit spec.
        mode add:    dW = k * v a^T, a = mu/(mu.mu)          (adds k*v on the average token)
        mode ablate: dW = -k * u u^T W, u = unit(v)          (removes the layer's writes along v)
        v = delta at `src` layer (default: the edited layer), sign flipped by `sign`; `topdims` keeps only the
        largest |v| coordinates."""
        L, k = int(e["layer"]), float(e.get("k", 1.0))
        v = delta[int(e.get("src", L))].clone() * float(e.get("sign", 1.0))
        if e.get("topdims"):
            keep = v.abs().topk(int(e["topdims"])).indices
            m = torch.zeros_like(v)
            m[keep] = 1.0
            v = v * m
        if e.get("mode", "add") == "add":
            mu = mlp_in_sum[L] / mlp_in_n[0]
            return L, k * v, mu / (mu @ mu)
        u = v / v.norm()
        W = layers[L].mlp.down_proj.weight
        return L, -k * u, (u.to(W.device).to(W.dtype) @ W).float().cpu()

    def run_cand(name, edits):
        saved, tensors, by_layer = [], {}, collections.defaultdict(list)
        for e in edits:
            L, Bv, Av = factors(e)
            by_layer[L].append((Bv, Av))
        for L, fs in by_layer.items():
            Bm = torch.stack([b for b, _ in fs], 1)  # [d, r]
            Am = torch.stack([x for _, x in fs], 0)  # [r, mlp]

            def hook(mod, inp, out, Bm=Bm, Am=Am):
                return out + ((inp[0].float() @ Am.to(out.device).T) @ Bm.to(out.device).T).to(out.dtype)
            saved.append(layers[L].mlp.down_proj.register_forward_hook(hook))
            key = f"base_model.model.model.language_model.layers.{L}.mlp.down_proj"
            tensors[key + ".lora_A.weight"] = Am.to(torch.bfloat16).contiguous()
            tensors[key + ".lora_B.weight"] = Bm.to(torch.bfloat16).contiguous()
        rank = max([len(v) for v in by_layer.values()] or [1])
        for key in list(tensors):  # one rank for the whole adapter: pad the smaller layers with zeros
            t = tensors[key]
            if key.endswith("lora_A.weight") and t.shape[0] < rank:
                tensors[key] = torch.cat([t, torch.zeros(rank - t.shape[0], t.shape[1], dtype=t.dtype)], 0)
            if key.endswith("lora_B.weight") and t.shape[1] < rank:
                tensors[key] = torch.cat([t, torch.zeros(t.shape[0], rank - t.shape[1], dtype=t.dtype)], 1)
        cs = [next_call(ids) for ids in stalled]
        ce = [next_call(ids) for ids in early]
        for h in saved:
            h.remove()
        res = {"cand": name, "edits": edits, "stalled_n": len(cs), "stalled_edit": sum(c in EDITS for c in cs),
               "stalled_nocall": sum(c is None for c in cs), "early_n": len(ce),
               "early_edit": sum(c in EDITS for c in ce), "early_nocall": sum(c is None for c in ce),
               "stalled_calls": [str(c) for c in cs], "early_calls": [str(c) for c in ce]}
        print(json.dumps(res), flush=True)
        if tensors:
            d = Path(a.out) / name
            d.mkdir(parents=True, exist_ok=True)
            save_file(tensors, str(d / "adapter_model.safetensors"))
            cfg = {"base_model_name_or_path": Path(a.model).name, "bias": "none", "fan_in_fan_out": False,
                   "inference_mode": True, "init_lora_weights": True, "layers_to_transform": None,
                   "lora_alpha": float(rank), "lora_dropout": 0.0, "modules_to_save": None, "peft_type": "LORA",
                   "r": rank, "target_modules": ["down_proj"], "task_type": "CAUSAL_LM", "use_dora": False,
                   "use_rslora": False}
            (d / "adapter_config.json").write_text(json.dumps(cfg, indent=2) + "\n")
        return res

    for name, edits in cands:
        results.append(run_cand(name, [{"layer": L, "k": k} for L, k in edits]))
    json.dump({"map": amap, "picked": pick, "results": results}, open(os.path.join(a.out, "wsp.json"), "w"), indent=1)

    if a.serve_hours > 0:
        # look-edit-test loop: an outside editor drops <out>/queue/<name>.json = {"edits": [{layer, k, mode, src,
        # sign, topdims}, ...]} and reads <out>/done/<name>.json; <out>/queue/STOP ends the job.
        import time
        q, done = Path(a.out) / "queue", Path(a.out) / "done"
        q.mkdir(exist_ok=True)
        done.mkdir(exist_ok=True)
        t_end = time.time() + a.serve_hours * 3600
        print(json.dumps({"serving": str(q)}), flush=True)
        while time.time() < t_end and not (q / "STOP").exists():
            specs = sorted(f for f in q.glob("*.json") if not (done / f.name).exists())
            if not specs:
                time.sleep(10)
                continue
            f = specs[0]
            try:
                res = run_cand(f.stem, json.load(open(f))["edits"])
            except Exception as ex:  # a bad spec must not end the loop
                res = {"cand": f.stem, "error": type(ex).__name__ + ": " + str(ex)[:200]}
                print(json.dumps(res), flush=True)
            json.dump(res, open(done / f.name, "w"), indent=1)


if __name__ == "__main__":
    main()
