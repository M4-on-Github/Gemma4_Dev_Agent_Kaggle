"""Build LoRA canary adapters for a served w4a16 checkpoint from its safetensors header alone (no weights read).

R-013 (2026-11-20). Run inside env/harness.sif on CPU:
  python3 -I tools/make_lora_canary.py <served model dir> <out dir> [--rank 16]

Writes under <out>/adapters/ (gitignored: harness-eng/adapters/ and *.safetensors):
  loud_l0/    rank 4 on q_proj and o_proj of text layer 0, the organisers' sample layout, with lora_B ~ N(0, 0.02).
              It must change prompt logprobs, so it shows an adapter is applied.
  full_zero/  rank R on every q/k/v/o/gate/up/down projection the checkpoint has in its text layers, lora_B = 0.
              It is the training shape, so it gives the decode cost, and it must leave logprobs unchanged.
Module names and shapes come from the served header. A module the checkpoint lacks is never written: the 31B's
full-attention layers have no v_proj, and the E4B's KV-shared layers have no k_proj or v_proj. The E4B's
per_layer_* projections are not standard LoRA targets and are left out.
"""
import json
import struct
import sys
from pathlib import Path

import torch
from safetensors.torch import save_file

TARGETS = ("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj")


def header(model_dir):
    keys = {}
    for f in sorted(Path(model_dir).glob("*.safetensors")):
        with open(f, "rb") as fh:
            n = struct.unpack("<Q", fh.read(8))[0]
            h = json.loads(fh.read(n))
        h.pop("__metadata__", None)
        keys.update(h)
    return keys


def modules(h):
    """{module path: (in_features, out_features)} for the text-layer LoRA targets (int4 packs 8 values per int32)."""
    out = {}
    for k, v in h.items():
        if not k.endswith(".weight_packed") or ".language_model.layers." not in k:
            continue
        m = k[: -len(".weight_packed")]
        if m.rsplit(".", 1)[1] in TARGETS:
            out[m] = (v["shape"][1] * 8, v["shape"][0])
    return out


def config(model_name, rank, targets, layers):
    return {"base_model_name_or_path": model_name, "bias": "none", "fan_in_fan_out": False, "inference_mode": True,
            "init_lora_weights": True, "layers_to_transform": layers, "lora_alpha": 2 * rank, "lora_dropout": 0.0,
            "modules_to_save": None, "peft_type": "LORA", "r": rank, "target_modules": sorted(targets),
            "task_type": "CAUSAL_LM", "use_dora": False, "use_rslora": False}


def write(d, cfg, tensors):
    d.mkdir(parents=True, exist_ok=True)
    (d / "adapter_config.json").write_text(json.dumps(cfg, indent=2) + "\n")
    save_file(tensors, str(d / "adapter_model.safetensors"))


def main():
    served, out = Path(sys.argv[1]), Path(sys.argv[2])
    rank = int(sys.argv[sys.argv.index("--rank") + 1]) if "--rank" in sys.argv else 16
    name = served.name
    mods = modules(header(served))
    g = torch.Generator().manual_seed(0)

    loud = {}
    for m, (fin, fout) in mods.items():
        if ".layers.0.self_attn." in m and m.rsplit(".", 1)[1] in ("q_proj", "o_proj"):
            loud[f"base_model.model.{m}.lora_A.weight"] = (torch.randn(4, fin, generator=g) * 0.01).to(torch.bfloat16)
            loud[f"base_model.model.{m}.lora_B.weight"] = (torch.randn(fout, 4, generator=g) * 0.02).to(torch.bfloat16)
    write(out / "adapters" / "loud_l0", config(name, 4, ["q_proj", "o_proj"], [0]), loud)

    full, kinds, n_params = {}, {}, 0
    for m, (fin, fout) in sorted(mods.items()):
        full[f"base_model.model.{m}.lora_A.weight"] = (torch.randn(rank, fin, generator=g) * 0.01).to(torch.bfloat16)
        full[f"base_model.model.{m}.lora_B.weight"] = torch.zeros(fout, rank, dtype=torch.bfloat16)
        kind = m.rsplit(".", 1)[1]
        kinds[kind] = kinds.get(kind, 0) + 1
        n_params += rank * (fin + fout)
    write(out / "adapters" / "full_zero", config(name, rank, kinds, None), full)
    print(json.dumps({"model": name, "loud_l0_tensors": len(loud), "full_zero_rank": rank, "full_zero_modules": kinds,
                      "full_zero_params": n_params, "full_zero_mib_bf16": round(n_params * 2 / 2**20, 1)}))


if __name__ == "__main__":
    main()
