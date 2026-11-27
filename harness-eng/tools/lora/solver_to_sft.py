"""L-008 (2026-11-22): SFT rows from the `solve` sub-agent's own steps in retry-layout traces (trees/e4b-r020-retry and
its one-solve control), checked against the solver's recorded prompt tokens.

  apptainer exec --bind /data/mmyatmau env/harness.sif python3 -I tools/lora/solver_to_sft.py \
      --tokenizer models/gemma-4-e4b-it-qat-w4a16-ct --tools /data/mmyatmau/gemma4-lora/schema/tools.json \
      --system trees/e4b-r020-retry/prompts/solver.md --tasks cohorts/lfold-a.txt \
      --out /data/mmyatmau/gemma4-lora/data/d5/<name>.jsonl runs/<run> [...]

Rows hold task and trace text, so they are written only under /data/mmyatmau/gemma4-lora and never into git or a
release (plan.md:52). Stdout carries counts only.

Per resolved task in the fold:
- the trace is cut into attempts at each root `solve` call; the solver steps after call k form attempt k. The row
  is the LAST attempt (it left the submitted working tree; an earlier attempt was empty or was redone);
- messages: the solver system prompt as ADK builds it (--system with `{problem_description}` and `{hints?}` filled from
  the task's session state, as swegemma/harness/agent_runner.py sets it, then ADK's identity line), the root's request string as
  the user turn, one assistant message per solver LLM call with its tool responses (as trace_to_sft.py), and the
  closing text turn (the solver's final text, with that call's thought), which teaches the solver to stop;
- prefix check: every solver call with recorded prompt_tokens is re-rendered; the row is cut before the first call
  whose gap exceeds --max-gap (then it has no closing turn and is labelled `cut`). The system text is chosen per
  row from a few joinings of instruction and identity by the smallest first-call gap, and reported;
- kept when the attempt has at least --min-calls LLM calls.
"""
import argparse
import collections
import json
import os
import re
import sys

from transformers import AutoTokenizer


def load_ids(path):
    return {l.split()[0] for l in open(path) if l.strip() and not l.startswith("#")}


def inject(template, state):
    """google/adk/utils/instructions_utils.py: {name} from state, {name?} empty when missing."""
    def sub(m):
        name = m.group().strip("{}").strip()
        opt = name.endswith("?")
        name = name.removesuffix("?")
        if name in state:
            return str(state[name])
        if opt:
            return ""
        raise KeyError(name)
    return re.sub(r"{+[^{}]*}+", sub, template)


def served_json(o):
    try:
        return json.dumps(json.loads(o), ensure_ascii=False)
    except Exception:
        return o or ""


def args_of(tc):
    a = tc.get("arguments")
    if isinstance(a, str):
        try:
            a = json.loads(a)
        except ValueError:
            return {}
    return a if isinstance(a, dict) else {}


def attempts(steps, root, solver):
    """[(request string, [solver steps])] in order."""
    out = []
    for s in steps:
        if s["source"] != "agent":
            continue
        a = s["extra"].get("author")
        if a == root:
            for tc in s.get("tool_calls") or []:
                if tc["function_name"] == solver:
                    v = list(args_of(tc).values())
                    out.append((str(v[0]) if len(v) == 1 else None, []))
        elif a == solver and out:
            out[-1][1].append(s)
    return out


def convert(request, steps, system):
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": request}]
    recorded, closing = [], None
    for i, s in enumerate(steps):
        tcs = s.get("tool_calls") or []
        if not tcs:
            if s["extra"].get("event_type") == "final":
                closing = s
            continue
        calls, responses = [], []
        for tc in tcs:
            calls.append({"id": tc["tool_call_id"], "type": "function",
                          "function": {"name": tc["function_name"], "arguments": tc.get("arguments") or {}}})
            responses.append({"role": "tool", "tool_call_id": tc["tool_call_id"], "name": tc["function_name"],
                              "content": served_json((s.get("observation") or {}).get("content", ""))})
        if "metrics" in s or msgs[-1]["role"] != "tool":
            recorded.append((len(msgs), (s.get("metrics") or {}).get("prompt_tokens")))
            msgs.append({"role": "assistant", "content": "", "reasoning_content": s.get("message") or None,
                         "tool_calls": calls})
            msgs.extend(responses)
        else:
            j = max(k for k, m in enumerate(msgs) if m["role"] == "assistant")
            msgs[j]["tool_calls"].extend(calls)
            msgs.extend(responses)
    if closing is None or not (closing.get("message") or "").strip():
        return msgs, recorded, None
    # the closing call: the thinking step(s) without tool calls just before the final step carry its thought
    k = steps.index(closing)
    thought = None
    if k > 0 and not steps[k - 1].get("tool_calls") and steps[k - 1]["extra"].get("event_type") == "thinking":
        thought = steps[k - 1].get("message") or None
        rec = (steps[k - 1].get("metrics") or {}).get("prompt_tokens")
    else:
        rec = (closing.get("metrics") or {}).get("prompt_tokens")
    recorded.append((len(msgs), rec or None))
    msgs.append({"role": "assistant", "content": closing["message"], "reasoning_content": thought})
    return msgs, recorded, "complete"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tokenizer", required=True)
    p.add_argument("--tools", required=True)
    p.add_argument("--system", required=True, help="the solver's instruction file as shipped")
    p.add_argument("--tasks", required=True)
    p.add_argument("--task-data", required=True, help="tasks.jsonl (problem_statement, hints_text)")
    p.add_argument("--out", required=True)
    p.add_argument("--root", default="swe_agent")
    p.add_argument("--solver", default="solve")
    p.add_argument("--max-gap", type=int, default=64)
    p.add_argument("--min-calls", type=int, default=3)
    p.add_argument("--unresolved", action="store_true",
                   help="L-010: keep the last attempt of UNRESOLVED tasks instead (for contrast sets, not training)")
    p.add_argument("--tool-names", default="run_command,read_file,edit_file,write_file,get_status")
    p.add_argument("runs", nargs="+")
    a = p.parse_args()
    if not os.path.abspath(a.out).startswith("/data/mmyatmau/gemma4-lora/"):
        sys.exit("--out must be under /data/mmyatmau/gemma4-lora/ (trace text never goes into the repo)")
    tok = AutoTokenizer.from_pretrained(a.tokenizer)
    alltools = json.load(open(a.tools))
    names = a.tool_names.split(",")
    tools = [alltools[n] for n in names]
    keep = load_ids(a.tasks)
    base = open(a.system).read()
    desc = "Resolves the issue in /workspace end to end and leaves the change in the working tree. Takes one request string."
    ident = f'You are an agent. Your internal name is "{a.solver}". The description about you is "{desc}".'
    state = {}
    for line in open(a.task_data):
        t = json.loads(line)
        if t["instance_id"] in keep:
            st = {"problem_description": t["problem_statement"]}
            if (t.get("hints_text") or "").strip():
                st["hints"] = t["hints_text"].strip()
            state[t["instance_id"]] = st

    def cands(iid):
        b = inject(base, state[iid])
        return {"ident_after": b + "\n\n" + ident, "ident_after_strip": b.strip() + "\n\n" + ident, "plain": b}

    def ntok(m):
        s = tok.apply_chat_template(m, tools=tools, tokenize=False, enable_thinking=True, add_generation_prompt=True)
        return len(tok(s, add_special_tokens=False)["input_ids"])

    why, per_task, chosen = collections.Counter(), collections.Counter(), collections.Counter()
    gaps, calls_kept, first_gaps = [], [], collections.defaultdict(list)
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
                att = attempts(json.load(open(tp))["steps"], a.root, a.solver)
                if not att:
                    why["no_attempt"] += 1
                    continue
                request, steps = att[-1]
                if request is None or not steps:
                    why["bad_attempt"] += 1
                    continue
                # pick the system text whose first solver call matches its recorded prompt tokens best
                best = None
                for name, sysm in cands(iid).items():
                    msgs, recorded, end = convert(request, steps, sysm)
                    if not recorded or recorded[0][1] is None:
                        continue
                    g = abs(ntok(msgs[:recorded[0][0]]) - recorded[0][1])
                    first_gaps[name].append(g)
                    if best is None or g < best[0]:
                        best = (g, name, msgs, recorded, end)
                if best is None:
                    why["no_metrics"] += 1
                    continue
                g0, name, msgs, recorded, end = best
                chosen[name] += 1
                worst, cut = 0, None
                for k, (i, rec) in enumerate(recorded):
                    if rec is None:
                        continue
                    gap = ntok(msgs[:i]) - rec
                    if abs(gap) > a.max_gap:
                        cut = (k, i)
                        break
                    worst = max(worst, abs(gap))
                if cut:
                    k, i = cut
                    msgs, recorded, end = msgs[:i], recorded[:k], "cut"
                if end is None:
                    end = "no_final"
                if len(recorded) < a.min_calls:
                    why["too_short_" + end] += 1
                    continue
                gaps.append(worst)
                why["kept_" + end] += 1
                calls_kept.append(len(recorded))
                per_task[iid] += 1
                fo.write(json.dumps({"messages": msgs, "tool_names": names,
                                     "meta": {"run": os.path.basename(run.rstrip("/")), "instance_id": iid,
                                              "llm_calls": len(recorded), "end": end, "attempts": len(att),
                                              "system": name, "max_prefix_gap": worst}},
                                    ensure_ascii=False) + "\n")
    med = lambda v: sorted(v)[len(v) // 2] if v else None
    print(json.dumps({"counts": dict(why), "system_chosen": dict(chosen),
                      "first_gap_median": {k: med(v) for k, v in first_gaps.items()},
                      "tasks_kept": len(per_task), "samples_per_task": sorted(per_task.values(), reverse=True),
                      "llm_calls_kept": sum(calls_kept), "max_prefix_gap_median": med(gaps)}))


if __name__ == "__main__":
    main()
