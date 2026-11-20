"""LoRA serving canary (R-013, 2026-11-20): boot the harness's own VllmServer with the adapters under
<adapters-root>/adapters/ and measure, with no task run:
  - the vLLM command line (the LoRA flags the harness derives) and /v1/models;
  - prompt logprobs of two own-words texts under the base name (twice, the floor) and each adapter name;
  - decode tok/s for the base and each adapter, alternating, after a warm-up, at 1 and 4 streams;
  - prefill seconds for a ~12k-token prompt per name (a nonce defeats the prefix cache).
The harness right-sizes --max-loras and --max-lora-rank from the mounted adapters (adk_submission/server.py), so
the decode number that matters comes from a boot that mounts only the adapter that would ship.
Run through slurm/lora_canary.sbatch, which uses eval.sbatch's container setup.
"""
import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cluster_eval import decode_probe, free_port  # noqa: E402  (the same probe the base runs record)

TEXTS = [  # own words, no competition text
    "The parser reads a configuration file line by line, strips comments, and stores each key with its value.",
    "When the cache is full, the oldest entry is removed before the new one is written to disk.",
]


def post(url, body, timeout=600):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read()), time.time() - t0


def prompt_logprobs(base, name, text):
    out, _ = post(base + "/completions", {"model": name, "prompt": text, "max_tokens": 1, "temperature": 0.0,
                                          "prompt_logprobs": 0})
    lps = []
    for d in out["choices"][0].get("prompt_logprobs") or []:
        if d:  # one entry per position: the prompt token itself (prompt_logprobs=0)
            lps.append(next(iter(d.values()))["logprob"])
    return out.get("model"), lps


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model-dir", required=True)
    p.add_argument("--adapters-root", required=True, help="dir holding adapters/<name>/")
    p.add_argument("--out", required=True)
    a = p.parse_args()
    import torch
    from adk_submission import VllmConfig, VllmServer, discover_adapters
    from swegemma.config import ALLOWED_ADAPTER_EXTENSIONS
    adapters = discover_adapters(a.adapters_root, adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
    names = sorted(adapters.adapters)
    assert names, f"no adapters under {a.adapters_root}/adapters"
    cfg = VllmConfig(model=a.model_dir, port=free_port(), host="127.0.0.1", tool_call_parser="gemma4",
                     reasoning_parser="gemma4", default_chat_template_kwargs={"enable_thinking": True},
                     max_model_len=32768,
                     dtype="bfloat16" if torch.cuda.get_device_capability()[0] >= 8 else "float16",
                     gpu_memory_utilization=0.90, enable_auto_tool_choice=True, enable_lora=True, max_loras=8,
                     max_lora_rank=128, tensor_parallel_size=1, startup_timeout=1200)
    server = VllmServer(cfg, adapter_manifest=adapters)
    rec = {"adapters": names, "cmd": server.build_cmd(), "gpu": torch.cuda.get_device_name(0)}
    print("cmd:", " ".join(map(str, rec["cmd"])), flush=True)
    t0 = time.time()
    server.start()
    rec["boot_s"] = round(time.time() - t0, 1)
    base = server.base_url.rstrip("/")
    base_id = getattr(server, "effective_model_path", a.model_dir)
    try:
        with urllib.request.urlopen(base + "/models", timeout=60) as r:
            rec["models"] = [m["id"] for m in json.loads(r.read())["data"]]
        all_names = [base_id] + names
        for n in all_names:  # warm-up, not recorded
            decode_probe(base, n)
        lp = {n: [prompt_logprobs(base, n.split("#")[0], t) for t in TEXTS]
              for n in [base_id, base_id + "#repeat"] + names}
        ref = [x[1] for x in lp[base_id]]
        rec["logprob"] = {}
        for n, v in lp.items():
            d = [abs(x - y) for (_, lps), r in zip(v, ref) for x, y in zip(lps, r)]
            rec["logprob"][n] = {"model_field": [m for m, _ in v], "n": len(d),
                                 "mean_abs_delta": sum(d) / max(1, len(d)), "max_abs_delta": max(d or [0])}
        print("logprob:", json.dumps(rec["logprob"]), flush=True)
        rec["decode"] = {n: [] for n in all_names}
        for _ in range(2):
            for n in all_names:
                rec["decode"][n].append({"s1": decode_probe(base, n), "s4": decode_probe(base, n, 4)})
        print("decode:", json.dumps(rec["decode"]), flush=True)
        long_text = " ".join(TEXTS * 300)  # about 12k tokens
        rec["prefill_s"] = {}
        for n in all_names:
            _, dt = post(base + "/completions", {"model": n, "prompt": f"[{n}-{time.time()}] " + long_text,
                                                 "max_tokens": 1, "temperature": 0.0})
            rec["prefill_s"][n] = round(dt, 2)
        print("prefill_s:", json.dumps(rec["prefill_s"]), flush=True)
    finally:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(rec, indent=1))
        server.stop()


if __name__ == "__main__":
    main()
