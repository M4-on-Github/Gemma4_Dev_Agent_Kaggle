"""R-028 desk (zero GPU): edit_file argument loss (a result holding only `error`) and outcomes, per draw, for the
31B base draws and the E4B retry draws. Counts only.  python3.13 -I tools/edit_argloss_desk.py"""
import json,glob,collections,statistics,sys
def scan(run):
    out=[]
    for l in open(f"runs/{run}/task_results.jsonl"):
        r=json.loads(l); p=f"runs/{run}/traces/trace_{r['instance_id']}.json"
        try: st=json.load(open(p))["steps"]
        except Exception: continue
        loss=ok=other=0; first_loss_t=None; t0=None; lost_after_first=0; ok_after_loss=False
        for s in st:
            for c in s.get("tool_calls") or []:
                if c["function_name"]!="edit_file": continue
                try: d=json.loads((s.get("observation") or {}).get("content") or "")
                except Exception: d=None
                if isinstance(d,dict) and set(d)=={"error"}:
                    loss+=1
                elif isinstance(d,dict) and d.get("status")=="ok":
                    ok+=1; ok_after_loss|=loss>0
                else: other+=1
        out.append(dict(res=r["resolved"],loss=loss,ok=ok,other=other,okal=ok_after_loss,empty=not r.get("patch_chars"),calls=r["tool_calls"]))
    return out
for name,runs in [("31B base x6",["R-008-31b-base-te-d1","R-008-31b-base-te-d2","R-011-31b-base-te-d3","R-011-31b-base-te-d4","R-014-31b-base-te-d5","R-015-31b-base-te-d6"]),
                  ("E4B retry x12",[f"R-021-e4b-retry-ada-d{i}" for i in range(1,13)])]:
    rows=[x for r in runs for x in scan(r)]; D=len(runs)
    L=[x for x in rows if x["loss"]]; N=[x for x in rows if not x["loss"]]
    print(name,"tasks/draw",len(rows)/D,"| edit ok/draw",round(sum(x["ok"] for x in rows)/D,1),"lost/draw",round(sum(x["loss"] for x in rows)/D,1),"other err/draw",round(sum(x["other"] for x in rows)/D,1))
    print("  tasks with loss/draw",round(len(L)/D,2),"resolved among them",round(sum(x["res"] for x in L)/D,2),"| without loss",round(len(N)/D,2),"resolved",round(sum(x["res"] for x in N)/D,2))
    print("  loss tasks: never an ok edit",round(sum(not x["ok"] for x in L)/D,2),"ok after a loss",round(sum(x["okal"] for x in L)/D,2),"empty patch",round(sum(x["empty"] for x in L)/D,2),"median lost per loss task",statistics.median(x["loss"] for x in L) if L else 0)
