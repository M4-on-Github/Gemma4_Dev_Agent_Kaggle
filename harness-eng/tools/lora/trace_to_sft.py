"""Convert resolved agent traces into chat-format SFT samples (D2 in rounds/L-001), checked against the served
prompt length.

  apptainer exec --bind /data/mmyatmau env/harness.sif python3 -I tools/lora/trace_to_sft.py \
      --tokenizer models/gemma-4-31b-it-qat-w4a16-ct --tools /data/mmyatmau/gemma4-lora/schema/tools.json \
      --tasks <fold file of instance ids> --out /data/mmyatmau/gemma4-lora/data/<name>.jsonl runs/<run> [...]

Output rows hold task, repo and trace text, so they are written only under /data/mmyatmau/gemma4-lora and never
into git or a release (plan.md:52). Stdout carries counts only.

Per sample:
- the system prompt, the task prompt, then one assistant message per LLM call (`reasoning_content` = the step's
  thought text, `tool_calls` = the call, or several when later steps of the same response carry no metrics),
  each followed by its tool responses;
- tool responses are re-serialized with `ensure_ascii=False`, as ADK's `_safe_json_serialize` sends them (the
  trace stores the default ASCII-escaped dump);
- it ends at the first `submit_patch` response (`complete`), or earlier at the first point the trace no longer
  shows what the model saw (`cut`):
  - a continuation nudge (the template drops earlier thoughts at a user turn);
  - an LLM call whose re-rendered prefix is more than --max-gap tokens from the recorded `prompt_tokens`. Most
    of these are ADK events compaction (cluster_eval.py: interval 15, threshold 14336 tokens), whose summary is
    not in the trace; a recorded drop of more than 3000 tokens is labelled `compaction`, the rest `mismatch`.
Kept only when the trace has a single agent author, the task resolved, and the faithful prefix has at least --min-calls LLM calls.
"""
import argparse
import collections
import json
import os
import sys

from transformers import AutoTokenizer


def load_ids(path):
    return {l.split()[0] for l in open(path) if l.strip() and not l.startswith("#")}


def served_json(o):
    try:
        return json.dumps(json.loads(o), ensure_ascii=False)
    except Exception:
        return o or ""


def convert(trace):
    """Messages up to the first submit_patch response or the first nudge; recorded = [(prefix end, tokens)]."""
    st = trace["steps"]
    authors = {s["extra"].get("author") for s in st if s["source"] == "agent"}
    if len(authors) > 1:
        return None, "multi_agent"
    sysm = next((s["message"] for s in st if s["extra"].get("event_type") == "system_instruction"), None)
    task = next((s["message"] for s in st if s["extra"].get("event_type") == "task_prompt"), None)
    if sysm is None or task is None:
        return None, "no_prompt"
    msgs = [{"role": "system", "content": sysm}, {"role": "user", "content": task}]
    recorded = []  # (index in msgs where this call's prefix ends, recorded prompt_tokens)
    submitted = False
    for s in st:
        if s["extra"].get("event_type") == "continuation_nudge":
            return (msgs, recorded, "nudge"), None
        if s["source"] != "agent" or not s.get("tool_calls"):
            continue
        calls, responses = [], []
        for tc in s["tool_calls"]:
            calls.append({"id": tc["tool_call_id"], "type": "function",
                          "function": {"name": tc["function_name"], "arguments": tc.get("arguments") or {}}})
            responses.append({"role": "tool", "tool_call_id": tc["tool_call_id"], "name": tc["function_name"],
                              "content": served_json((s.get("observation") or {}).get("content", ""))})
        if "metrics" in s or msgs[-1]["role"] != "tool":
            recorded.append((len(msgs), (s.get("metrics") or {}).get("prompt_tokens")))
            msgs.append({"role": "assistant", "content": "", "reasoning_content": s.get("message") or None,
                         "tool_calls": calls})
            msgs.extend(responses)
        else:  # a later call of the same LLM response: same assistant message, responses in call order
            j = max(i for i, m in enumerate(msgs) if m["role"] == "assistant")
            msgs[j]["tool_calls"].extend(calls)
            if s.get("message"):
                msgs[j]["reasoning_content"] = "\n".join(x for x in (msgs[j]["reasoning_content"], s["message"]) if x)
            msgs.extend(responses)
        if any(c["function"]["name"] == "submit_patch" for c in calls):
            submitted = True
            break
    return (msgs, recorded, "complete" if submitted else "no_submit"), None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tokenizer", required=True)
    p.add_argument("--tools", required=True)
    p.add_argument("--tasks", required=True, help="file of instance ids to keep (a fold)")
    p.add_argument("--out", required=True)
    p.add_argument("--max-gap", type=int, default=64)
    p.add_argument("--min-calls", type=int, default=3)
    p.add_argument("--unresolved", action="store_true", help="L-010: keep UNRESOLVED tasks instead (contrast sets)")
    p.add_argument("--tool-names", default="run_command,read_file,edit_file,write_file,get_status,submit_patch")
    p.add_argument("runs", nargs="+")
    a = p.parse_args()
    if not os.path.abspath(a.out).startswith("/data/mmyatmau/gemma4-lora/"):
        sys.exit("--out must be under /data/mmyatmau/gemma4-lora/ (trace text never goes into the repo)")
    tok = AutoTokenizer.from_pretrained(a.tokenizer)
    alltools = json.load(open(a.tools))
    tools = [alltools[n] for n in a.tool_names.split(",")]
    keep = load_ids(a.tasks)

    def ntok(m):
        s = tok.apply_chat_template(m, tools=tools, tokenize=False, enable_thinking=True, add_generation_prompt=True)
        return len(tok(s, add_special_tokens=False)["input_ids"])

    why = collections.Counter()
    per_task = collections.Counter()
    gaps, calls_kept = [], []
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as fo:
        for run in a.runs:
            for line in open(os.path.join(run, "task_results.jsonl")):
                r = json.loads(line)
                iid = r["instance_id"]
                if iid not in keep:
                    why["not_in_fold"] += 1
                    continue
                if bool(r.get("resolved")) == a.unresolved:
                    why["resolved" if a.unresolved else "unresolved"] += 1
                    continue
                tp = os.path.join(run, "traces", f"trace_{iid}.json")
                if not os.path.exists(tp):
                    why["no_trace"] += 1
                    continue
                res, err = convert(json.load(open(tp)))
                if err:
                    why[err] += 1
                    continue
                msgs, recorded, end = res
                # first LLM call whose prefix no longer matches what was served; the sample ends before it
                worst, cut, prev = 0, None, None
                for k, (i, rec) in enumerate(recorded):
                    if rec is None:
                        continue
                    gap = ntok(msgs[:i]) - rec
                    if abs(gap) > a.max_gap:
                        cut = (k, i, "compaction" if prev is not None and rec < prev - 3000 else "mismatch")
                        break
                    worst, prev = max(worst, abs(gap)), rec
                if cut:
                    k, i, end = cut
                    msgs, recorded = msgs[:i], recorded[:k]
                if len(recorded) < a.min_calls:
                    why["too_short_" + end] += 1
                    continue
                gaps.append(worst)
                why["kept_" + end] += 1
                calls_kept.append(len(recorded))
                per_task[iid] += 1
                fo.write(json.dumps({"messages": msgs, "tool_names": a.tool_names.split(","),
                                     "meta": {"run": os.path.basename(run.rstrip("/")), "instance_id": iid,
                                              "llm_calls": len(recorded), "end": end,
                                              "max_prefix_gap": worst}}, ensure_ascii=False) + "\n")
    print(json.dumps({"counts": dict(why), "tasks_kept": len(per_task),
                      "samples_per_task_max": max(per_task.values(), default=0),
                      "llm_calls_kept": sum(calls_kept),
                      "max_prefix_gap_median": sorted(gaps)[len(gaps) // 2] if gaps else None}))


if __name__ == "__main__":
    main()
