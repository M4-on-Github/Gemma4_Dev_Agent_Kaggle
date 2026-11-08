#!/usr/bin/env python3
"""EXP-058: build the adapter-bearing candidate tree and its light zip, verifying every input by sha256.

Two subcommands, both deterministic and both refusing on any hash mismatch:

  tree   <src_tree> <adapter_dir> <outdir>
         Copies the four files of the EXP-033 E4B tree (sha256 checked after CRLF -> LF normalisation, so a
         CRLF worktree passes), applies ONE anchored edit to agent.yaml (the anchor must match exactly once),
         copies adapter_config.json and adapter_model.safetensors from <adapter_dir> (binary sha256 checked)
         into <outdir>/adapters/copy_lora/, and writes every text file with LF endings.

  light  <full_zip> <light_zip> <manifest_json>
         Writes a path -> sha256 manifest of every member of the full zip (as packed by
         tools/pack_submission.py), then a copy of the full zip without the one .safetensors member, same
         member order, same date_time, same compression, 0644. The kernel receives the light zip embedded and
         the weights from the EXP-054 v2 kernel output (kernel_sources), and checks the assembled tree
         against the manifest.

Usage (inputs under runs/ are data: run with -I -X utf8):
    python -I -X utf8 experiments/EXP-058/make_candidate.py tree experiments/EXP-033/candidate-e4b \
        runs/EXP-054-copy-lora-v2/sub1/adapters/copy_lora dist/EXP-058/candidate-a
    python -I -X utf8 experiments/EXP-058/make_candidate.py light dist/EXP-058-a.zip dist/EXP-058-a-light.zip \
        experiments/EXP-058/full_manifest.json
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

# sha256 of the committed EXP-033 tree (LF), recorded 2026-11-08 from `git ls-files --eol` i/lf w/lf files.
SRC_SHA256 = {
    "agent.yaml": "a14d765aabca70dbfea94a1d5bb338bce5a3e5cb452fbf07668dfd3cefada0f4",
    "configs/sampling.yaml": "630056889710d27dbf17c8fde62e033b7329616b7db435987cb4607b66a7c3f6",
    "eval_config.yaml": "916cf6cb34a6cc3de39837fa72cac681599b9ac2a3ee0b893adadfd36474c531",
    "prompts/system.md": "57a20af4eb29bbfdab003ab8cf04f6495674887ec5ba3dd746750930179a8041",
}
# sha256 of the EXP-054 v2 adapter (kernel rainm4/gemma4-exp054-copy-lora version 2, sub1/adapters/copy_lora/).
ADAPTER_SHA256 = {
    "adapter_config.json": "cf87fdf065108e1f77f76fb706bf007cf5e5b5aebf1951310f88baecf1bdf2db",
    "adapter_model.safetensors": "c4af0041176a02b7b718d6fc4f9fd8990f30c7aea1946d1da3529f5a190e6d64",
}
ADAPTER_NAME = "copy_lora"
ANCHOR = "model: gemma-4-e4b-it-qat-w4a16-ct\n"
INSERT = (
    "# EXP-058 2026-11-08: adapter none -> copy_lora (the EXP-054 v2 rank-8 q/o LoRA), nothing else changed from\n"
    "# experiments/EXP-033/candidate-e4b; an end-to-end bug test of an adapter-bearing tree, not an effect test\n"
    "adapter: copy_lora\n"
)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def die(msg: str) -> None:
    print(f"REFUSED: {msg}")
    raise SystemExit(1)


def cmd_tree(src: Path, adir: Path, out: Path) -> int:
    if out.exists():
        die(f"{out} exists; remove it first (the tool never merges into an old tree)")
    texts: dict[str, str] = {}
    for rel, want in SRC_SHA256.items():
        data = (src / rel).read_bytes().replace(b"\r\n", b"\n")
        if sha(data) != want:
            die(f"{rel}: sha256 {sha(data)} != recorded {want}")
        texts[rel] = data.decode("utf-8")
        print(f"ok   {rel}  {want[:12]}")
    n = texts["agent.yaml"].count(ANCHOR)
    if n != 1:
        die(f"agent.yaml: anchor matched {n} times, need exactly 1")
    if "adapter:" in texts["agent.yaml"]:
        die("agent.yaml already has an adapter key")
    texts["agent.yaml"] = texts["agent.yaml"].replace(ANCHOR, ANCHOR + INSERT, 1)
    blobs: dict[str, bytes] = {}
    for name, want in ADAPTER_SHA256.items():
        data = (adir / name).read_bytes()
        if sha(data) != want:
            die(f"{name}: sha256 {sha(data)} != recorded {want}")
        blobs[name] = data
        print(f"ok   adapters/{ADAPTER_NAME}/{name}  {want[:12]}  {len(data)} bytes")
    for rel, text in texts.items():
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))
    for name, data in blobs.items():
        p = out / "adapters" / ADAPTER_NAME / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    print(f"edit agent.yaml: +{INSERT.count(chr(10))} lines after the model line")
    for p in sorted(out.rglob("*")):
        if p.is_file():
            print(f"out  {p.relative_to(out).as_posix()}  {sha(p.read_bytes())}")
    return 0


def cmd_light(full: Path, light: Path, manifest: Path) -> int:
    with zipfile.ZipFile(full) as zin:
        infos = zin.infolist()
        man = {i.filename: sha(zin.read(i.filename)) for i in infos if not i.is_dir()}
        heavy = [i.filename for i in infos if i.filename.endswith(".safetensors")]
        if len(heavy) != 1:
            die(f"expected exactly one .safetensors member, found {heavy}")
        want = ADAPTER_SHA256["adapter_model.safetensors"]
        if man[heavy[0]] != want:
            die(f"{heavy[0]} in the zip has sha256 {man[heavy[0]]} != recorded {want}")
        light.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(light, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for i in infos:
                if i.filename == heavy[0]:
                    continue
                ni = zipfile.ZipInfo(i.filename, date_time=i.date_time)
                ni.external_attr = 0o644 << 16
                ni.compress_type = i.compress_type
                zout.writestr(ni, zin.read(i.filename))
    manifest.parent.mkdir(parents=True, exist_ok=True)
    doc = {"full_zip": full.name, "full_zip_sha256": sha(full.read_bytes()),
           "light_zip": light.name, "light_zip_sha256": sha(light.read_bytes()),
           "dropped_member": heavy[0], "members": man}
    manifest.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in doc.items() if k != "members"}, indent=1))
    for k, v in sorted(man.items()):
        print(f"member {k}  {v}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 4 and argv[0] == "tree":
        return cmd_tree(Path(argv[1]), Path(argv[2]), Path(argv[3]))
    if len(argv) == 4 and argv[0] == "light":
        return cmd_light(Path(argv[1]), Path(argv[2]), Path(argv[3]))
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
