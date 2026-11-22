"""L-008 (2026-11-22): apply the pre-registered adapter choice to a finished train_lora.py run and copy the chosen
adapter into a tree. Exit 1 (nothing copied) when no adapter qualifies, so an `afterok` chain stops.

  python3 -I tools/lora/pick_adapter.py <adapter run dir> <tree>/adapters/<name>

Rule (rounds/L-008, training reading 2):
- `final` when its validation loss is below step 0's and no more than 10% above the lowest logged value;
- otherwise the latest `epochK` whose step has a logged validation loss at or before it that is below step 0's
  (the last logged value at or before that step is used);
- otherwise none.
Prints counts and losses only.
"""
import json
import os
import shutil
import sys


def main():
    run, dest = sys.argv[1], sys.argv[2]
    ev = [json.loads(l) for l in open(os.path.join(run, "train_log.jsonl"))]
    vals = [(e["step"], e["val_loss"]) for e in ev if e.get("val_loss") is not None]
    finite = [v for _, v in vals if v == v and v not in (float("inf"), float("-inf"))]
    if not vals or len(finite) != len(vals) or not any(e.get("event") == "saved" and e["dir"] == "final" for e in ev):
        print(json.dumps({"pick": None, "why": "unhealthy or unfinished"}))
        return 1
    v0, vmin = vals[0][1], min(finite)
    vfin = vals[-1][1]
    pick = None
    if vfin < v0 and vfin <= 1.10 * vmin:
        pick = "final"
    else:
        for e in reversed([e for e in ev if e.get("event") == "saved" and e["dir"].startswith("epoch")]):
            before = [v for s, v in vals if s <= e["step"]]
            if before and before[-1] < v0:
                pick = e["dir"]
                break
    print(json.dumps({"pick": pick, "val_step0": round(v0, 4), "val_min": round(vmin, 4), "val_final": round(vfin, 4),
                      "n_val": len(vals)}))
    if pick is None:
        return 1
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(os.path.join(run, pick), dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
