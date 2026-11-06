"""EXP-047 readings, applied exactly as pre-registered (experiments/EXP-047-q4-adapter-canary-e4b.md sections 2.4, 3, 4,
with the 4.3 and 4.4 amendments of 2026-11-05: row A1f, non-finite logprobs, a loud-only failure).

Usage: python -I -X utf8 experiments/EXP-047/analyze_canary.py runs/EXP-047-q4-canary [--json out.json]

Reads the kernel output (canary.json and probes.jsonl, found anywhere under the given directory) and prints the
endpoints E1-E7 and the rows of readings A and B that fire. Prints numbers, labels and model names only.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

COMPACTION_LINE = 14_336
MAX_MODEL_LEN = 32_768
NAMES = ("canary_zero", "canary_big", "canary_loud")


def find(root: Path, name: str) -> Path | None:
    hits = sorted(root.rglob(name))
    return hits[0] if hits else None


def load(root: Path) -> tuple[dict, list[dict]]:
    c, p = find(root, "canary.json"), find(root, "probes.jsonl")
    canary = json.loads(c.read_text(encoding="utf-8")) if c else {}
    probes = [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()] if p else []
    return canary, probes


def logprob_runs(probes: list[dict], boot: str, label: str) -> dict[int, dict]:
    return {r["i"]: r for r in probes if r.get("boot") == boot and r.get("label") == label
            and r.get("kind") == "logprob" and not r.get("skipped")}


def d(probes: list[dict], boot_x: str, x: str, boot_y: str, y: str) -> tuple[float | None, list[str]]:
    """Max |logprob_x - logprob_y| over prompts and positions; prompts whose token sequences differ are dropped."""
    rx, ry = logprob_runs(probes, boot_x, x), logprob_runs(probes, boot_y, y)
    notes, vals = [], []
    for i in sorted(set(rx) | set(ry)):
        a, b = rx.get(i), ry.get(i)
        if not a or not b or a.get("status") != 200 or b.get("status") != 200 or a.get("logprobs") is None \
                or b.get("logprobs") is None:
            notes.append(f"prompt {i}: missing or non-200")
            continue
        if a.get("tokens") != b.get("tokens") or len(a["logprobs"]) != len(b["logprobs"]):
            notes.append(f"prompt {i}: token sequences differ, dropped")
            continue
        for u, v in zip(a["logprobs"], b["logprobs"]):
            if u is None or v is None:
                continue
            # amendment 2026-11-05: a non-finite logprob on one side only counts as an infinite difference
            fu, fv = math.isfinite(u), math.isfinite(v)
            vals.append(abs(u - v) if fu and fv else (0.0 if (u == v) else math.inf))
    return (max(vals) if vals else None), notes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args(argv)
    canary, probes = load(a.run_dir)
    if not canary:
        print("no canary.json under", a.run_dir)
        return 1
    b0, b1 = canary.get("boot0") or {}, canary.get("boot1") or {}
    out: dict = {"status": canary.get("status"), "elapsed_s": canary.get("elapsed_s"),
                 "boot0_started": b0.get("started"), "boot1_started": b1.get("started"),
                 "boot1_failure_class": b1.get("failure_class"), "boot1_lora_flags": b1.get("lora_flags"),
                 "boot1_v1_models": b1.get("v1_models"), "boot_s": [b0.get("boot_s"), b1.get("boot_s")]}

    # E4: floor
    f1, n1 = d(probes, "boot1", "base_repeat", "boot1", "base")
    f0, n0 = d(probes, "boot0", "base_repeat", "boot0", "base")
    floors = [x for x in (f1, f0) if x is not None]
    F = max(floors) if floors else None
    tau = max(10 * F, 1e-3) if F is not None else None
    H = max(100 * F, 0.05) if F is not None else None
    out.update(F=F, F_boot1=f1, F_boot0=f0, tau=tau, H=H)

    # E1-E3
    E = {}
    for name in NAMES:
        E[name], notes = d(probes, "boot1", name, "boot1", "base")
        if notes:
            out[f"notes_{name}"] = notes
    out.update(E1_big=E["canary_big"], E2_loud=E["canary_loud"], E3_zero=E["canary_zero"])
    out["base_boot0_vs_boot1"] = d(probes, "boot0", "base", "boot1", "base")[0]

    # E5: loadable
    listed = b1.get("v1_models") if isinstance(b1.get("v1_models"), list) else []
    adapter_reqs = [r for r in probes if r.get("boot") == "boot1" and r.get("label") in NAMES and not r.get("skipped")]
    non200 = [(r["label"], r["kind"], r.get("status")) for r in adapter_reqs if r.get("status") != 200]
    # amendment 4.4, 2026-11-05: E5's non-200 test reads the logprob requests (the measure) only; greedy and decode
    # failures are recorded. A logprob failure confined to canary_loud is classed by its error text.
    lp_non200 = [x for x in non200 if x[1] == "logprob"]
    loud_class = None
    if lp_non200 and all(x[0] == "canary_loud" for x in lp_non200):
        err = " ".join(str(r.get("error") or "") + " " + str((r.get("echo_attempt") or {}).get("error") or "")
                       for r in adapter_reqs if r["label"] == "canary_loud" and r["kind"] == "logprob").lower()
        if any(k in err for k in ("lora", "adapter", "target module", "unexpected", "not found", "does not exist")):
            loud_class = "load_failure"
        elif any(k in err for k in ("nan", "inf", "overflow", "numer")):
            loud_class = "overflow"
        else:
            loud_class = "unclassified"
        if loud_class == "overflow":
            E["canary_loud"] = math.inf
        if loud_class != "load_failure":
            lp_non200 = []
    adapter_lp = [r for r in adapter_reqs if r["kind"] == "logprob"]
    E5 = bool(b1.get("started")) and all(n in listed for n in NAMES) and not lp_non200 and bool(adapter_lp)
    all_lp_skipped = bool(b1.get("started")) and not adapter_lp
    out.update(E5_loadable=E5, adapter_non200=non200, names_listed={n: n in listed for n in NAMES},
               loud_failure_class=loud_class, adapter_logprob_all_skipped=all_lp_skipped,
               E2_loud_after_4_4=E["canary_loud"])

    # amendment (i), 2026-11-05: the server answers under the adapter's name, and the compile path does not fall
    # through to the base model (adk_submission server.py:432-439 binds an adapter name to the base path silently
    # unless the server is vLLM with LoRA enabled)
    wrong_name = [(r["label"], r["kind"], r.get("resp_model")) for r in adapter_reqs
                  if r.get("status") == 200 and r.get("resp_model") is not None and r.get("resp_model") != r.get("served")]
    no_name = sum(1 for r in adapter_reqs if r.get("status") == 200 and r.get("resp_model") is None)
    routing = canary.get("routing") or {}
    reg = routing.get("registry_models") or {}
    base_path = b1.get("served_base")
    fall = []
    for key in ("canary_big", "adapter:canary_big"):
        m = reg.get(key)
        if m is not None and not str(m).endswith("canary_big"):
            fall.append(f"registry {key} -> base or other")
    am = routing.get("agent_model")
    if am is not None and not str(am).endswith("canary_big"):
        fall.append("compiled root agent model is not canary_big")
    greedy_text = {(r["label"], r.get("i")): r.get("text") for r in probes
                   if r.get("boot") == "boot1" and r.get("kind") == "greedy" and not r.get("skipped")}
    big0, base0txt = greedy_text.get(("canary_big", 0)), greedy_text.get(("base", 0))
    if ("text" in routing and big0 is not None and base0txt is not None and big0 != base0txt
            and routing["text"] == base0txt):
        fall.append("compile-path text equals base text while direct canary_big differs")
    out.update(resp_model_mismatch=wrong_name, resp_model_missing=no_name, fall_through=fall, registry_checked=bool(reg),
               routing_read=(am is not None and "error" not in routing), base_path_recorded=base_path is not None)

    # E6
    K0, K1 = b0.get("gpu_kv_cache_tokens"), b1.get("gpu_kv_cache_tokens")
    out.update(K0=K0, K1=K1, K1_over_K0=(round(K1 / K0, 4) if K0 and K1 else None))

    # E7, recorded
    greedy = {}
    for r in probes:
        if r.get("kind") == "greedy" and not r.get("skipped"):
            greedy.setdefault(f"{r['boot']}:{r['label']}", []).append(r.get("text"))
    ref = greedy.get("boot1:base")
    out["greedy_equal_to_boot1_base"] = {k: (v == ref) for k, v in greedy.items()}
    out["decode_tok_s"] = {r["label"]: r.get("tok_s") for r in probes if r.get("kind") == "decode" and not r.get("skipped")}
    big_q0 = next((r.get("text") for r in probes if r.get("boot") == "boot1" and r.get("label") == "canary_big"
                   and r.get("kind") == "greedy" and r.get("i") == 0), None)
    out["routing"] = {"agent_model": routing.get("agent_model"), "error": routing.get("error"),
                      "text_equals_direct_canary_big": (routing.get("text") == big_q0) if "text" in routing else None}

    # Reading A, first match
    infra = (not b0.get("started")) or canary.get("status") == "infrastructure" or all_lp_skipped or \
        (b1.get("started") and E["canary_big"] is None and E["canary_loud"] is None and E5)
    if infra:
        A = "A0"
    elif (b0.get("started") and not b1.get("started")) or (b1.get("started") and not E5):
        A = "A1k" if b1.get("failure_class") == "kv_or_max_len" else "A1"
    elif wrong_name or fall:
        A = "A1f"
    elif tau is None or (F is not None and not math.isfinite(F)) or E["canary_zero"] is None:
        A = "A6"
    elif E["canary_zero"] > tau:
        A = "A2"
    elif E["canary_big"] is not None and E["canary_loud"] is not None and E["canary_big"] > H and E["canary_loud"] > H:
        A = "A3"
    elif E["canary_loud"] is not None and E["canary_loud"] > H and E["canary_big"] is not None and E["canary_big"] <= tau:
        A = "A4"
    elif E["canary_big"] is not None and E["canary_loud"] is not None and E["canary_big"] <= tau \
            and E["canary_loud"] <= tau and E5:
        A = "A5"
    else:
        A = "A6"
    # Reading B, first match
    if not b1.get("started") or K1 is None:
        B = "B0"
    elif K1 < COMPACTION_LINE:
        B = "B1"
    elif K1 < MAX_MODEL_LEN:
        B = "B2"
    else:
        B = "B3"
    out.update(reading_A=A, reading_B=B)
    print(json.dumps(out, indent=1, default=str))
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
