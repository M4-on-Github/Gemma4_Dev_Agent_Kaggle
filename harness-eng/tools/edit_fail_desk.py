"""R-028 desk (zero GPU): classify edit_file "Failed to replace" errors against the base snapshot (exact, whitespace
only, all lines present but not contiguous, mostly present, mostly invented). Counts only.
  python3.13 -I tools/edit_fail_desk.py <run> [<run> ...]   (run names under runs/)"""
import json,glob,collections,tarfile,sys,re
runs=sys.argv[1:]
C=collections.Counter(); cache={}
def norm(x): return re.sub(r"\s+"," ",x).strip()
def basefile(iid,rel):
    key=(iid,rel)
    if key in cache: return cache[key]
    try:
        with tarfile.open(f"data/raw/snapshots/{iid}.tgz") as tf:
            m=tf.getmember("./"+rel); cache[key]=tf.extractfile(m).read().decode("utf-8","replace")
    except Exception: cache[key]=None
    return cache[key]
for run in runs:
  for l in open(f"runs/{run}/task_results.jsonl"):
    r=json.loads(l); iid=r["instance_id"]
    try: st=json.load(open(f"runs/{run}/traces/trace_{iid}.json"))["steps"]
    except Exception: continue
    read=set(); edited=set()
    for s in st:
      for c in s.get("tool_calls") or []:
        a=c.get("arguments") or {}; fp=str(a.get("filepath","")); rel=fp.split("/workspace/",1)[-1].lstrip("./") if fp else ""
        if c["function_name"]=="read_file": read.add(rel)
        if c["function_name"]!="edit_file": continue
        try: d=json.loads((s.get("observation") or {}).get("content") or "")
        except Exception: d=None
        if not isinstance(d,dict): continue
        if d.get("status")=="ok": edited.add(rel); continue
        if "Failed to replace" not in str(d.get("error_message","")): continue
        old=a.get("old_string")
        if not isinstance(old,str): C["no_old_arg"]+=1; continue
        C["failed"]+=1; C["read_before" if rel in read else "not_read_before"]+=1
        if rel in edited: C["file_already_edited"]+=1
        b=basefile(iid,rel)
        if b is None: C["cls_no_base_file"]+=1; continue
        if old in b: C["cls_exact_in_base"]+=1; continue
        if norm(old) in norm(b): C["cls_ws_only"]+=1; continue
        ol=[x.strip() for x in old.splitlines() if x.strip()]; bl=set(x.strip() for x in b.splitlines())
        frac=sum(x in bl for x in ol)/len(ol) if ol else 0
        C["cls_all_lines_present_noncontig" if frac==1 else ("cls_mostly_present" if frac>=.5 else "cls_mostly_invented")]+=1
        C["old_lines_le3" if len(ol)<=3 else "old_lines_gt3"]+=1
print(json.dumps(dict(sorted(C.items()))))
