"""EXP-036: build the CPU-only re-grade notebook from the committed template.

Fills the template's parameter cell:
- TASK_IDS from the cohort file, on one line;
- base64 copies of tools/regrade_patches.py and the two shims;
- one zip per --arm LABEL=DIR of that arm's stored *.patch files.

It then converts the result to .ipynb with tools/build_notebook.py's own parse_percent / to_ipynb. It checks
that every arm holds exactly the cohort's ids, and that the kernel metadata next to --out requests no
accelerator.

The output embeds agent patches, which are diffs of competition repository code. It goes to an untracked path
and is never committed (plan.md:52).

Run as:
  python -I -X utf8 experiments/EXP-036/build_regrade_notebook.py \
      --template experiments/EXP-036/kaggle_regrade_template.py --cohort experiments/cohorts/dev-48.txt \
      --arm R=runs/EXP-028-armR/patches --arm RH=runs/EXP-028-armRH/patches \
      --out notebooks/exp036_regrade/kaggle_regrade.ipynb
"""
from __future__ import annotations

import argparse
import base64
import importlib.util
import io
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("build_notebook", ROOT / "tools" / "build_notebook.py")
BN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BN)


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def zip_patches(d: Path, ids: list[str]) -> str:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i in ids:
            info = zipfile.ZipInfo(f"{i}.patch", date_time=(2020, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            zf.writestr(info, (d / f"{i}.patch").read_bytes())
    return base64.b64encode(buf.getvalue()).decode("ascii")


def set_param(text: str, name: str, value) -> str:
    line = f"{name} = {value!r}"
    text, n = re.subn(rf"^{re.escape(name)} = .*$", lambda _m: line, text, count=1, flags=re.M)
    if n != 1:
        raise SystemExit(f"no `{name} = ...` line in the template")
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--template", type=Path, required=True)
    ap.add_argument("--cohort", type=Path, required=True)
    ap.add_argument("--arm", action="append", default=[], metavar="LABEL=DIR", required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()

    ids = [ln.strip() for ln in a.cohort.read_text(encoding="utf-8").splitlines()
           if ln.strip() and not ln.startswith("#")]
    zips = {}
    for spec_ in a.arm:
        label, d = spec_.split("=", 1)
        d = Path(d)
        have = {p.stem for p in d.glob("*.patch")}
        if have != set(ids):
            raise SystemExit(f"arm {label}: {len(have - set(ids))} ids not in the cohort, {len(set(ids) - have)} missing")
        zips[label] = zip_patches(d, ids)

    meta_path = a.out.parent / "kernel-metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("enable_gpu") or meta.get("enable_tpu") or meta.get("machine_shape") or meta.get("model_sources"):
        raise SystemExit(f"{meta_path}: must request no accelerator, no machine_shape and no model")
    if meta.get("code_file") != a.out.name:
        raise SystemExit(f"{meta_path}: code_file {meta.get('code_file')!r} != {a.out.name!r}")

    text = a.template.read_text(encoding="utf-8")
    text = set_param(text, "TASK_IDS", ids)
    text = set_param(text, "REGRADE_SCRIPT_B64", b64(ROOT / "tools" / "regrade_patches.py"))
    text = set_param(text, "SHIM_INLINE_B64", b64(ROOT / "tools" / "compat_shims" / "inline_snapshot" / "__init__.py"))
    text = set_param(text, "SHIM_DIRTY_B64", b64(ROOT / "tools" / "compat_shims" / "dirty_equals" / "__init__.py"))
    text = set_param(text, "PATCHES_ZIP_B64", zips)
    for kind, body in BN.parse_percent(text):
        if kind == "code":
            compile(body, "<cell>", "exec")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(BN.to_ipynb(BN.parse_percent(text)), indent=1) + "\n", encoding="utf-8")
    print(f"wrote {a.out}: {len(ids)} ids, arms {sorted(zips)}, {a.out.stat().st_size} bytes (do not commit)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
