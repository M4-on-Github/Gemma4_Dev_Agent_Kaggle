"""Plain-torch LoRA SFT on a served compressed-tensors Gemma 4 checkpoint (rounds/L-001), saved in the PEFT layout
the harness's vLLM loads (R-013). No peft, trl or datasets.

  # tokenizer only, no GPU: render every sample, check the loss spans, print counts
  apptainer exec env/harness.sif python3 -I tools/lora/train_lora.py --dry-run \
      --model models/gemma-4-e4b-it-qat-w4a16-ct --system-from-trace <an E4B trace of the frozen config> \
      --tools /data/mmyatmau/gemma4-lora/schema/tools.json \
      --data /data/mmyatmau/gemma4-lora/data/d1/synth-s1.jsonl:1500 \
      --data /data/mmyatmau/gemma4-lora/data/d2/31b-all-lfold-a.jsonl --cap-per-task 8 \
      --out /data/mmyatmau/gemma4-lora/adapters/<name>

Samples are chat rows ({"messages", "tool_names", "meta"}) from synth_edits.py (D1) or trace_to_sft.py (D2).
- The system message is replaced by the frozen config's served system instruction (--system-from-trace or
  --system-prompt), and the tool declarations by --tools / --tool-names, so the adapter trains under the prompt
  it is served with.
- Loss: per assistant message, `train` = "all" (the thought channel and the tool call), "call" (the tool call
  only) or "none" (context only). A row's messages without `train` take --default-train. A call's span runs from
  `<|tool_call>` through the `<|tool_response>` token that follows `<tool_call|>`: the model emits it and vLLM
  stops on it (eos ids 1, 106, 50).
- Rows from a run whose name contains "nothoughts" are dropped (made without thinking). --cap-per-task keeps at
  most K rows per instance_id (seeded choice). --val-tasks holds out that many D2 tasks for a validation loss.
- The checkpoint is loaded dequantized to bf16 (compressed-tensors, run_compressed=False), so the adapter trains
  on the served weights. LoRA goes on the q/k/v/o/gate/up/down projections of the text layers that the served
  checkpoint has, as R-013's full_zero canary did.
Stdout and <out>/train_log.jsonl carry counts and losses only.
"""
import argparse
import collections
import json
import math
import os
import random
import re
import struct
import sys
import time
from pathlib import Path

TARGETS = ("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj")
TC_OPEN, TC_CLOSE, TR_OPEN, TR_CLOSE = "<|tool_call>", "<tool_call|>", "<|tool_response>", "<tool_response|>"
MODEL_OPEN = "<|turn>model\n"
OUT_ROOTS = ("/data/mmyatmau/gemma4-lora/",)


def served_modules(model_dir):
    """Text-layer LoRA targets the served checkpoint has (same rule as make_lora_canary.py)."""
    out = set()
    for f in sorted(Path(model_dir).glob("*.safetensors")):
        with open(f, "rb") as fh:
            n = struct.unpack("<Q", fh.read(8))[0]
            h = json.loads(fh.read(n))
        for k in h:
            if k.endswith(".weight_packed") and ".language_model.layers." in k:
                m = k[: -len(".weight_packed")]
                if m.rsplit(".", 1)[1] in TARGETS:
                    out.add(m)
    return out


def load_rows(specs, cap_per_task, seed):
    rng = random.Random(seed)
    rows, why = [], collections.Counter()
    for spec in specs:
        path, _, n = spec.partition(":")
        rs = [json.loads(l) for l in open(path)]
        keep = []
        for r in rs:
            if "nothoughts" in (r.get("meta") or {}).get("run", ""):
                why["drop_nothoughts"] += 1
                continue
            keep.append(r)
        if cap_per_task:
            by = collections.defaultdict(list)
            for r in keep:
                by[(r.get("meta") or {}).get("instance_id")].append(r)
            keep = []
            for iid, g in sorted(by.items(), key=lambda x: str(x[0])):
                if iid is not None and len(g) > cap_per_task:
                    why["drop_over_cap"] += len(g) - cap_per_task
                    g = rng.sample(g, cap_per_task)
                keep.extend(g)
        if n:
            rng.shuffle(keep)
            keep = keep[: int(n)]
        for r in keep:
            r["_src"] = os.path.basename(path)
        why["rows_" + os.path.basename(path)] += len(keep)
        rows.extend(keep)
    return rows, why


def spans(text, msgs, default_train):
    """Char spans to train on, one per trained assistant message, located in the rendered text in order."""
    starts = [m.start() for m in re.finditer(re.escape(TC_OPEN), text)]
    ends = [m.end() for m in re.finditer(re.escape(TC_CLOSE), text)]
    asst = [m for m in msgs if m["role"] == "assistant"]
    ncalls = sum(len(m.get("tool_calls") or []) for m in asst)
    if len(starts) != ncalls or len(ends) != ncalls:
        return None
    out, ci, prev_end = [], 0, None
    for m in asst:
        k = len(m.get("tool_calls") or [])
        if k == 0:
            return None
        s0, e1 = starts[ci], ends[ci + k - 1]
        ci += k
        if text.startswith(TR_OPEN, e1):
            e1 += len(TR_OPEN)
        mode = m.get("train", default_train)
        if prev_end is None or text.rfind(MODEL_OPEN, 0, s0) > prev_end:
            b = text.rfind(MODEL_OPEN, 0, s0)
            b = b + len(MODEL_OPEN) if b >= 0 else None
        else:
            b = text.find(TR_CLOSE, prev_end)
            b = b + len(TR_CLOSE) if b >= 0 else None
        if b is None or b > s0:
            return None
        if mode == "all":
            out.append((b, e1))
        elif mode == "call":
            out.append((s0, e1))
        prev_end = e1
    return out


def encode(tok, row, system, tools_by_name, tool_names, default_train, max_len):
    msgs = [{k: v for k, v in m.items() if k != "train"} for m in row["messages"]]
    trains = [m.get("train") for m in row["messages"]]
    msgs[0] = {"role": "system", "content": system}
    names = tool_names or row["tool_names"]
    text = tok.apply_chat_template(msgs, tools=[tools_by_name[n] for n in names], tokenize=False,
                                   enable_thinking=True)
    for m, t in zip(msgs, trains):
        if t is not None:
            m["train"] = t
    sp = spans(text, msgs, default_train)
    if sp is None:
        return None, "span_mismatch"
    enc = tok(text, add_special_tokens=False, return_offsets_mapping=True)
    ids, offs = enc["input_ids"], enc["offset_mapping"]
    if len(ids) > max_len:
        return None, "too_long"
    labels, j = [], 0
    for tid, (a, b) in zip(ids, offs):
        while j < len(sp) and sp[j][1] <= a:
            j += 1
        labels.append(tid if j < len(sp) and sp[j][0] <= a < sp[j][1] else -100)
    if not any(l != -100 for l in labels):
        return None, "no_trained_tokens"
    return {"input_ids": ids, "labels": labels}, None


def system_text(a):
    if a.system_prompt:
        return open(a.system_prompt).read()
    t = json.load(open(a.system_from_trace))
    return next(s["message"] for s in t["steps"] if s["extra"].get("event_type") == "system_instruction")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--tools", required=True)
    p.add_argument("--tool-names", default=None, help="comma list; default: each row's own")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--system-prompt")
    g.add_argument("--system-from-trace")
    p.add_argument("--data", action="append", required=True, help="path[:N rows]")
    p.add_argument("--cap-per-task", type=int, default=8)
    p.add_argument("--default-train", default="all", choices=("all", "call", "none"))
    p.add_argument("--val-tasks", type=int, default=3)
    p.add_argument("--max-len", type=int, default=16384)
    p.add_argument("--rank", type=int, default=16)
    p.add_argument("--alpha", type=float, default=32.0)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--epochs", type=float, default=2.0)
    p.add_argument("--accum", type=int, default=8)
    p.add_argument("--warmup", type=int, default=10)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--out", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--load-check", action="store_true", help="load, wrap, one forward/backward, then exit")
    p.add_argument("--device-map", default="single", choices=("single", "auto"),
                   help="single: all on cuda:0; auto: layers split over the visible GPUs")
    a = p.parse_args()
    if not os.path.abspath(a.out).startswith(OUT_ROOTS):
        sys.exit(f"--out must be under {OUT_ROOTS}")

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model)
    tools_by_name = json.load(open(a.tools))
    tool_names = a.tool_names.split(",") if a.tool_names else None
    system = system_text(a)
    rows, why = load_rows(a.data, a.cap_per_task, a.seed)
    rng = random.Random(a.seed)
    d2_tasks = sorted({r["meta"]["instance_id"] for r in rows if "instance_id" in r.get("meta", {})})
    val_tasks = set(rng.sample(d2_tasks, min(a.val_tasks, len(d2_tasks)))) if d2_tasks else set()
    train, val, lens, trained, per_src = [], [], [], [], collections.Counter()
    for r in rows:
        ex, err = encode(tok, r, system, tools_by_name, tool_names, a.default_train, a.max_len)
        if err:
            why[err + "_" + r["_src"]] += 1
            continue
        lens.append(len(ex["input_ids"]))
        trained.append(sum(l != -100 for l in ex["labels"]))
        per_src[r["_src"]] += 1
        (val if r.get("meta", {}).get("instance_id") in val_tasks else train).append(ex)
    q = sorted(lens)
    stats = {"counts": dict(why), "encoded": dict(per_src), "train_rows": len(train), "val_rows": len(val),
             "val_tasks": len(val_tasks), "tokens_total": sum(lens), "trained_tokens_total": sum(trained),
             "len_median": q[len(q) // 2] if q else None, "len_p90": q[int(0.9 * len(q))] if q else None,
             "len_max": q[-1] if q else None}
    print(json.dumps(stats))
    if a.dry_run:
        return

    import torch
    import torch.nn as nn
    from safetensors.torch import save_file
    from transformers import AutoModelForImageTextToText, CompressedTensorsConfig

    torch.manual_seed(a.seed)
    dev = torch.device("cuda")

    # Query-chunked attention in place of "sdpa". On Turing in bf16 (and for the 512-wide global heads anywhere)
    # SDPA falls back to the math kernel, which builds the whole heads x L x L score matrix: 7.98 GiB for the
    # 16359-token row (L-002 P1, both runs). Each chunk of QCHUNK queries is checkpointed, so the backward
    # recomputes one chunk's scores at a time. Same masks as SDPA (the sdpa mask functions are kept).
    from torch.utils.checkpoint import checkpoint
    from transformers import AttentionInterface
    from transformers.integrations.sdpa_attention import repeat_kv, sdpa_attention_forward
    QCHUNK = 1024
    chunked_on = [True]

    def _attn(q, k, v, m, scale):
        return torch.nn.functional.scaled_dot_product_attention(q, k, v, attn_mask=m, scale=scale)

    def chunked_sdpa(module, query, key, value, attention_mask, dropout=0.0, scaling=None, is_causal=None, **kw):
        L = query.shape[2]
        if not chunked_on[0] or L <= QCHUNK:
            return sdpa_attention_forward(module, query, key, value, attention_mask, dropout=dropout,
                                          scaling=scaling, is_causal=is_causal, **kw)
        n = getattr(module, "num_key_value_groups", 1)
        k, v = repeat_kv(key, n), repeat_kv(value, n)
        S = k.shape[2]
        outs = []
        for i in range(0, L, QCHUNK):
            q = query[:, :, i:i + QCHUNK]
            if attention_mask is None:  # SDPA skipped a plain causal mask; rebuild this chunk's rows
                qi = torch.arange(i, i + q.shape[2], device=q.device)[:, None] + (S - L)
                m = (torch.arange(S, device=q.device)[None, :] <= qi)[None, None]
            elif attention_mask.shape[2] == 1:
                m = attention_mask
            else:
                m = attention_mask[:, :, i:i + QCHUNK]
            outs.append(checkpoint(_attn, q, k, v, m, scaling, use_reentrant=False))
        return torch.cat(outs, 2).transpose(1, 2).contiguous(), None

    AttentionInterface.register("sdpa", chunked_sdpa)
    model = AutoModelForImageTextToText.from_pretrained(
        a.model, dtype=torch.bfloat16, attn_implementation="sdpa", device_map={"": 0} if a.device_map == "single" else "auto",
        quantization_config=CompressedTensorsConfig(run_compressed=False))
    model.config.use_cache = False
    for prm in model.parameters():
        prm.requires_grad_(False)

    class LoRA(nn.Module):
        def __init__(self, base, r, alpha):
            super().__init__()
            self.base = base
            self.scale = alpha / r
            self.A = nn.Parameter(torch.empty(r, base.in_features, device=base.weight.device, dtype=torch.float32))
            self.B = nn.Parameter(torch.zeros(base.out_features, r, device=base.weight.device, dtype=torch.float32))
            nn.init.kaiming_uniform_(self.A, a=math.sqrt(5))  # PEFT's default init

        def forward(self, x):
            return self.base(x) + (x @ self.A.t().to(x.dtype)) @ self.B.t().to(x.dtype) * self.scale

    want = served_modules(a.model)
    wrapped = {}
    for name, mod in list(model.named_modules()):
        if name in want:
            if not isinstance(mod, nn.Linear):
                sys.exit(f"target is {type(mod).__name__}, not a dequantized nn.Linear; run_compressed=False failed")
            parent = model.get_submodule(name.rsplit(".", 1)[0])
            lo = LoRA(mod, a.rank, a.alpha)
            setattr(parent, name.rsplit(".", 1)[1], lo)
            wrapped[name] = lo
    missing = sorted(want - set(wrapped))
    kinds = collections.Counter(n.rsplit(".", 1)[1] for n in wrapped)
    params = [x for lo in wrapped.values() for x in (lo.A, lo.B)]
    ngpu = torch.cuda.device_count()
    print(json.dumps({"wrapped": len(wrapped), "served_targets": len(want), "missing_in_model": len(missing),
                      "kinds": dict(kinds), "lora_params": sum(x.numel() for x in params),
                      "gpus": [torch.cuda.get_device_name(i) for i in range(ngpu)],
                      "bf16_supported": torch.cuda.is_bf16_supported(),
                      "gpu_mem_gib_after_load": round(sum(torch.cuda.memory_allocated(i) for i in range(ngpu)) / 2**30, 2)}))
    if missing:
        sys.exit("served targets missing from the loaded model: " + ", ".join(missing[:5]))
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.train()
    lm = model.model.language_model
    ple_cpu = [False]

    cap = model.config.get_text_config().final_logit_softcapping
    head = model.lm_head

    def head_ce(h, tgt):
        z = head(h).float()
        if cap is not None:
            z = torch.tanh(z / cap) * cap
        return torch.nn.functional.cross_entropy(z, tgt, reduction="sum")

    def loss_of(ex):
        # Decoder only, then the head at the trained positions in checkpointed chunks: full-vocab logits for a 16k
        # row are 8 GiB in bf16 (L-002 P1 ran out of memory there). Same softcap as Gemma4ForConditionalGeneration.
        ids = torch.tensor([ex["input_ids"]], device=dev)
        lab = ex["labels"]
        pos = [t for t in range(len(lab) - 1) if lab[t + 1] != -100]
        if ple_cpu[0]:  # text-only input: the embeddings Gemma4Model computes itself when given input_ids
            with torch.no_grad():
                kw = {"inputs_embeds": model.model.get_input_embeddings()(ids),
                      "per_layer_inputs": lm.get_per_layer_inputs(ids.cpu(), None).to(dev)}
        else:
            kw = {"input_ids": ids}
        hs = model.model(use_cache=False, return_dict=True, **kw).last_hidden_state[0]
        p = torch.tensor(pos, device=hs.device)
        tgt = torch.tensor([lab[t + 1] for t in pos], device=hs.device)
        total = 0.0
        for i in range(0, len(pos), 1024):
            total = total + checkpoint(head_ce, hs[p[i:i + 1024]], tgt[i:i + 1024], use_reentrant=False)
        return total / len(pos)

    os.makedirs(a.out, exist_ok=True)
    log = open(os.path.join(a.out, "train_log.jsonl"), "a")

    def save(tag):
        d = Path(a.out) / tag
        d.mkdir(parents=True, exist_ok=True)
        tensors = {}
        for n, lo in wrapped.items():
            tensors[f"base_model.model.{n}.lora_A.weight"] = lo.A.detach().to(torch.bfloat16).cpu().contiguous()
            tensors[f"base_model.model.{n}.lora_B.weight"] = lo.B.detach().to(torch.bfloat16).cpu().contiguous()
        save_file(tensors, str(d / "adapter_model.safetensors"))
        cfg = {"base_model_name_or_path": Path(a.model).name, "bias": "none", "fan_in_fan_out": False,
               "inference_mode": True, "init_lora_weights": True, "layers_to_transform": None,
               "lora_alpha": a.alpha, "lora_dropout": 0.0, "modules_to_save": None, "peft_type": "LORA",
               "r": a.rank, "target_modules": sorted(kinds), "task_type": "CAUSAL_LM", "use_dora": False,
               "use_rslora": False}
        (d / "adapter_config.json").write_text(json.dumps(cfg, indent=2) + "\n")

    # Reference loss on a row stock SDPA can hold, with everything on the GPU (no grad).
    mid = [e for e in train if 2 * QCHUNK < len(e["input_ids"]) <= 4096]
    if a.load_check and mid:
        chunked_on[0] = False
        with torch.no_grad():
            l_ref = loss_of(mid[0]).item()
        chunked_on[0] = True

    # Frozen lookups and unused towers go to the CPU: the per-layer embedding table is 5.25 GiB of the 15.15
    # after loading, and the audio and vision towers are never called on text (L-002 P1, third run).
    lm.embed_tokens_per_layer.to("cpu")
    for t in ("vision_tower", "audio_tower", "embed_vision", "embed_audio"):
        if getattr(model.model, t, None) is not None:
            getattr(model.model, t).to("cpu")
    ple_cpu[0] = True
    torch.cuda.empty_cache()
    print(json.dumps({"gpu_mem_gib_after_offload": [round(torch.cuda.memory_allocated(i) / 2**30, 2)
                                                    for i in range(ngpu)]}))

    if a.load_check:
        if mid:  # chunked attention + CPU per-layer inputs against the stock all-GPU reference
            with torch.no_grad():
                l_new = loss_of(mid[0]).item()
            print(json.dumps({"chunk_check_len": len(mid[0]["input_ids"]), "loss_new": round(l_new, 5),
                              "loss_ref": round(l_ref, 5), "abs_diff": round(abs(l_new - l_ref), 6)}))
        torch.cuda.reset_peak_memory_stats()
        t0 = time.time()
        ex = max(train, key=lambda e: len(e["input_ids"]))
        loss = loss_of(ex)
        loss.backward()
        print(json.dumps({"load_check_len": len(ex["input_ids"]), "loss": round(loss.item(), 4),
                          "grad_norm": round(torch.nn.utils.clip_grad_norm_(params, 1e9).item(), 4),
                          "step_s": round(time.time() - t0, 1),
                          "gpu_peak_gib": [round(torch.cuda.max_memory_allocated(i) / 2**30, 2) for i in range(ngpu)]}))
        return

    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.0, betas=(0.9, 0.999))
    steps = max(1, int(math.ceil(len(train) * a.epochs / a.accum)))
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1.0, (s + 1) / a.warmup) * 0.5 * (1 + math.cos(math.pi * min(1.0, s / steps))))

    def val_loss():
        if not val:
            return None
        model.eval()
        with torch.no_grad():
            v = [loss_of(ex).item() for ex in val]
        model.train()
        return round(sum(v) / len(v), 4)

    order, step, t0 = [], 0, time.time()
    log.write(json.dumps({"event": "start", "stats": stats, "steps": steps, "args": vars(a)}) + "\n")
    log.write(json.dumps({"event": "val", "step": 0, "val_loss": val_loss()}) + "\n")
    log.flush()
    while step < steps:
        if not order:
            order = list(range(len(train)))
            rng.shuffle(order)
        acc, ntok = 0.0, 0
        for _ in range(a.accum):
            if not order:
                order = list(range(len(train)))
                rng.shuffle(order)
            ex = train[order.pop()]
            loss = loss_of(ex) / a.accum
            loss.backward()
            acc += loss.item()
            ntok += len(ex["input_ids"])
        gn = torch.nn.utils.clip_grad_norm_(params, 1.0).item()
        opt.step()
        sched.step()
        opt.zero_grad(set_to_none=True)
        step += 1
        rec = {"event": "step", "step": step, "loss": round(acc, 4), "grad_norm": round(gn, 3),
               "lr": sched.get_last_lr()[0], "tokens": ntok, "elapsed_s": round(time.time() - t0, 1)}
        if step % max(1, steps // 8) == 0 or step == steps:
            rec["val_loss"] = val_loss()
        log.write(json.dumps(rec) + "\n")
        log.flush()
        print(json.dumps(rec), flush=True)
    save("final")
    log.write(json.dumps({"event": "saved", "dir": "final", "elapsed_s": round(time.time() - t0, 1)}) + "\n")


if __name__ == "__main__":
    main()
