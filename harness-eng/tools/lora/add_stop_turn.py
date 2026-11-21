"""Append the model's own closing turn after the submit_patch response to trace_to_sft.py rows (L-006, 2026-11-21).

  python3 -I tools/lora/add_stop_turn.py --in /data/mmyatmau/gemma4-lora/data/d2/31b-fast-lfold-a.jsonl \
      --out /data/mmyatmau/gemma4-lora/data/d2/31b-fast-stop-lfold-a.jsonl

Why: trace_to_sft.py rows end at the first submit_patch response, so no trained row shows the model stopping. The
L-005 and L-003 adapters then kept calling submit_patch (rounds/L-006). This adds one assistant message with no
tool call, whose content is the text of the trace's first `final`/`text` agent step after that response, when no
tool call comes between them. The chat template renders it in the same model turn, right after
`<tool_response|>`, ending at `<turn|>` (eos id 106); train_lora.py trains that text and `<turn|>`.

Rows whose trace has no such step (the model called more tools, or stopped on a thought only) are kept unchanged
and counted. Every other message of every row is unchanged. Rows hold trace text, so the output stays under
/data/mmyatmau/gemma4-lora (plan.md:52); stdout carries counts only.
"""
import argparse
import collections
import json
import os


def closing_text(trace):
    st = [s for s in trace["steps"] if s["source"] == "agent"]
    first = next((i for i, s in enumerate(st)
                  if any(c["function_name"] == "submit_patch" for c in s.get("tool_calls") or [])), None)
    if first is None:
        return None, "no_submit"
    for s in st[first + 1:]:
        if s.get("tool_calls"):
            return None, "tools_after_submit"
        if s["extra"].get("event_type") in ("final", "text") and (s.get("message") or "").strip():
            return s["message"], None
    return None, "no_final_text"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--runs", default="runs")
    a = p.parse_args()
    why = collections.Counter()
    lens = []
    with open(a.out, "w") as fo:
        for line in open(a.inp):
            r = json.loads(line)
            m = r["meta"]
            if m.get("end") != "complete" or r["messages"][-1].get("name") != "submit_patch":
                why["unchanged_not_complete"] += 1
            else:
                tp = os.path.join(a.runs, m["run"], "traces", f"trace_{m['instance_id']}.json")
                text, err = closing_text(json.load(open(tp))) if os.path.exists(tp) else (None, "no_trace")
                if err:
                    why["unchanged_" + err] += 1
                else:
                    r["messages"].append({"role": "assistant", "content": text})
                    m["end"] = "complete_stop"
                    why["stop_added"] += 1
                    lens.append(len(text))
            fo.write(json.dumps(r, ensure_ascii=False) + "\n")
    lens.sort()
    print(json.dumps({"counts": dict(why), "stop_chars_median": lens[len(lens) // 2] if lens else None,
                      "stop_chars_max": lens[-1] if lens else None}))


if __name__ == "__main__":
    main()
