"""Pull the output bundles of our own past Kaggle kernels into harness-eng/runs/kaggle/.

Each eval kernel under ../notebooks/ wrote runs/<EXP>.zip (task_results.jsonl, traces, patches).
Kaggle keeps the output of a kernel's latest version, so this fetches that bundle and the kernel log
for every kernel id named in ../notebooks/*/kernel-metadata.json. Kernels without a runs/*.zip
(probes, trainers, regrades) are listed and skipped.

Standard library only; runs on the cluster's system python3 (3.6). The token is read from ../.env.
The fetched bundles hold competition repo snippets and are git-ignored.

Usage: python3 harness-eng/tools/fetch_runs.py [slug-substring ...]
       no arguments = every kernel; a run already on disk is skipped.
Writes runs/kaggle/INDEX.tsv: kernel id, bundle name, sha256, bytes, or the reason it was skipped.
"""
import hashlib
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
OUT = ROOT / "runs" / "kaggle"
API = "https://www.kaggle.com/api/v1/kernels/output"


def token():
    for line in (REPO / ".env").read_text().splitlines():
        if line.startswith("KAGGLE_API_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("KAGGLE_API_TOKEN missing from .env")


def listing(kernel_id, tok):
    user, slug = kernel_id.split("/", 1)
    files, log, page = [], "", ""
    while True:
        q = {"userName": user, "kernelSlug": slug}
        if page:
            q["pageToken"] = page
        req = urllib.request.Request(API + "?" + urllib.parse.urlencode(q), headers={"Authorization": "Bearer " + tok})
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.loads(r.read().decode("utf-8"))
        files += d.get("files", [])
        log = log or d.get("log", "")
        page = d.get("nextPageToken", "")
        if not page:
            return files, log


def main():
    want = sys.argv[1:]
    tok = token()
    OUT.mkdir(parents=True, exist_ok=True)
    ids = sorted({json.loads(p.read_text())["id"] for p in REPO.glob("notebooks/*/kernel-metadata.json")})
    if want:
        ids = [i for i in ids if any(w in i for w in want)]
    rows = []
    for kid in ids:
        try:
            files, log = listing(kid, tok)
        except urllib.error.HTTPError as exc:
            rows.append((kid, "", "", "", "listing failed: HTTP %d" % exc.code))
            print(kid, "-> listing failed", exc.code, flush=True)
            continue
        bundles = [f for f in files if f.get("fileName", "").startswith("runs/") and f["fileName"].endswith(".zip")
                   and f["fileName"].count("/") == 1]
        if not bundles:
            rows.append((kid, "", "", "", "no runs/*.zip in output (%d files)" % len(files)))
            print(kid, "-> no run bundle", flush=True)
            continue
        for f in bundles:
            name = Path(f["fileName"]).stem
            dest = OUT / name
            if (dest / "task_results.jsonl").exists() or (dest / "summary.json").exists():
                rows.append((kid, name, "", "", "already on disk"))
                print(kid, "->", name, "already on disk", flush=True)
                continue
            zpath = OUT / (name + ".zip")
            with urllib.request.urlopen(f["url"], timeout=600) as r, open(str(zpath), "wb") as fh:
                h, n = hashlib.sha256(), 0
                for chunk in iter(lambda: r.read(1 << 20), b""):
                    fh.write(chunk)
                    h.update(chunk)
                    n += len(chunk)
            dest.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(str(zpath)) as z:
                z.extractall(str(dest))
            zpath.unlink()
            (dest / "kernel.log.json").write_text(log)
            (dest / "KERNEL").write_text(kid + "\n")
            rows.append((kid, name, h.hexdigest(), str(n), "fetched"))
            print(kid, "->", name, n, "bytes", flush=True)
    with open(str(OUT / "INDEX.tsv"), "a") as fh:
        for r in rows:
            fh.write("\t".join(r) + "\n")
    print("%d kernels, %d bundles fetched" % (len(ids), sum(1 for r in rows if r[4] == "fetched")))


if __name__ == "__main__":
    main()
