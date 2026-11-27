"""L-009 (2026-11-27): SFT rows from the public SWE-smith trajectories (HF `SWE-bench/SWE-smith-trajectories`, split
`tool`, MIT), mapped onto the harness's tools and prompts (D3 in rounds/L-001).

  apptainer exec --bind /data/mmyatmau env/harness.sif python3 -I tools/lora/smith_to_sft.py \
      --layout 31b --src /data/mmyatmau/gemma4-lora/data/d3/swe-smith-trajectories \
      --out /data/mmyatmau/gemma4-lora/data/d3/smith-31b.jsonl [--exclude-repos FILE] [--max-calls 24]
  ... --layout e4b-solver --system trees/e4b-r020-retry/prompts/solver.md --out .../smith-e4b-solver.jsonl

Kept: resolved trajectories with --min-calls..--max-calls mapped tool calls and at least one edit, whose every action
maps. Mapping (paths under /testbed become workspace-relative, `/testbed` in commands becomes `/workspace`):
- `bash` -> `run_command`; `str_replace_editor view` of a file -> `read_file` (line numbers stripped, the harness's
  150-line / 10000-char cut applied), of a directory -> `run_command` with a `find`; `str_replace` -> `edit_file`;
  `create` -> `write_file`; the last `submit` -> `submit_patch` (31b) or the closing text turn (e4b-solver);
  earlier `submit` calls (the source agent's review step) are dropped with their observation.
- `insert`, `undo_edit`, abbreviated views of long files and unparsable actions drop the trajectory.
Tool responses are rebuilt in the harness's JSON shapes (swegemma/tools). The teacher's text before each call is kept
as the thought, cut to --thought-chars; train with `--default-train call` so only the calls are trained.
Layouts: `31b` = harness task prompt (build_agent_prompt, no workspace tree) and a placeholder system message
(train with --system-prompt); `e4b-solver` = the solver system prompt with the problem filled in plus ADK's identity
line (train with --system-from-row), the request "Resolve the issue." as the user turn, five tools.
Rows are public data plus our prompts; they stay under /data/mmyatmau/gemma4-lora. Stdout carries counts only.
"""
import argparse
import collections
import difflib
import glob
import json
import os
import random
import re
from types import SimpleNamespace as NS

import pyarrow.parquet as pq

SIX = ["run_command", "read_file", "edit_file", "write_file", "get_status", "submit_patch"]
FN = re.compile(r"<function=(\w+)>(.*?)</function>", re.S)
PARAM = re.compile(r"<parameter=(\w+)>(.*?)</parameter>", re.S)
NUMLINE = re.compile(r"^\s*(\d+)\t(.*)$")


def text_of(c):
    if isinstance(c, list):
        return "".join(x.get("text", "") for x in c if isinstance(x, dict))
    return c or ""


def steps_of(msgs):
    """[(thought, name, args, observation)] from either the structured or the in-text call format."""
    out, i = [], 0
    while i < len(msgs):
        m = msgs[i]
        if m["role"] != "assistant":
            i += 1
            continue
        content = text_of(m.get("content"))
        calls = []
        if m.get("tool_calls"):
            for tc in m["tool_calls"]:
                a = tc["function"].get("arguments")
                if isinstance(a, str):
                    try:
                        a = json.loads(a)
                    except ValueError:
                        return None
                calls.append((tc["function"]["name"], a or {}))
            thought = content
        else:
            found = list(FN.finditer(content))
            if not found:
                i += 1
                continue
            thought = content[: found[0].start()]
            for f in found:
                calls.append((f.group(1), {k: v.strip("\n") for k, v in PARAM.findall(f.group(2))}))
        if len(calls) != 1:
            return None
        obs = ""
        if i + 1 < len(msgs) and msgs[i + 1]["role"] in ("user", "tool"):
            obs = text_of(msgs[i + 1].get("content"))
            i += 1
        if obs.startswith("OBSERVATION:\n"):
            obs = obs[len("OBSERVATION:\n"):]
        out.append((thought.strip(), calls[0][0], calls[0][1], obs.replace("\r\n", "\n")))
        i += 1
    return out


def rel(path):
    path = (path or "").strip()
    if path == "/testbed":
        return "."
    if path.startswith("/testbed/"):
        return path[len("/testbed/"):]
    return None


def ws(s):
    return (s or "").replace("/testbed", "/workspace")


def ok(**kw):
    d = {"status": "ok"}
    d.update(kw)
    return json.dumps(d, ensure_ascii=False)


def err(t, msg, details=None):
    d = {"status": "error", "error_type": t, "error_message": msg}
    if details is not None:
        d["details"] = details
    return json.dumps(d, ensure_ascii=False)


def map_step(name, a, obs, totals):
    """-> (tool name, arguments, response json) or a drop reason string."""
    if name == "bash":
        cmd = a.get("command")
        if not cmd:
            return "bash_no_command"
        o = ws(obs)
        if o.startswith("Your command ran successfully and did not produce any output"):
            o = ""
        return "run_command", {"command": ws(cmd)}, ok(stdout=o[:5000], stderr="", exit_code=0)
    if name == "str_replace_editor":
        c, p = a.get("command"), rel(a.get("path"))
        if p is None:
            return "path_outside"
        if c == "view":
            if "files and directories up to 2 levels deep" in obs[:200]:
                body = ws(obs.split("\n", 1)[1] if "\n" in obs else "")
                d = "/workspace" if p == "." else "/workspace/" + p
                return "run_command", {"command": f"find {d} -maxdepth 2 -not -path '*/.*'"}, \
                    ok(stdout=body[:5000], stderr="", exit_code=0)
            if "too large to display entirely" in obs[:400]:
                return "view_abbreviated"
            if "cat -n" not in obs[:200]:
                return "read_file", {"filepath": p}, err("FileReadError", ws(obs)[:500])
            lines = []
            for ln in obs.split("\n")[1:]:
                mm = NUMLINE.match(ln)
                if mm:
                    lines.append((int(mm.group(1)), mm.group(2)))
            if not lines:
                return "view_unparsed"
            start, last = lines[0][0], lines[-1][0]
            vr = a.get("view_range")
            if isinstance(vr, str):
                try:
                    vr = json.loads(vr)
                except ValueError:
                    vr = None
            args = {"filepath": p}
            if vr:
                args["start_line"] = int(vr[0])
                if len(vr) > 1 and int(vr[1]) != -1:
                    args["end_line"] = int(vr[1])
            if not vr or (len(vr) > 1 and int(vr[1]) == -1):
                totals[p] = last
            total = max(totals.get(p, 0), last)
            trunc = False
            if len(lines) > 150:
                lines, trunc = lines[:150], True
            snippet = "\n".join(t for _, t in lines)
            if len(snippet) > 10000:
                snippet, trunc = snippet[:10000], True
            return "read_file", args, ok(filepath=p, content=snippet, start_line=start, end_line=lines[-1][0],
                                         total_lines=total, is_truncated=trunc)
        if c == "str_replace":
            old, new = a.get("old_str"), a.get("new_str", "")
            if old is None:
                return "edit_no_old"
            args = {"filepath": p, "old_string": old, "new_string": new}
            if "has been edited" in obs[:300]:
                diff = "\n".join(difflib.unified_diff(old.split("\n"), new.split("\n"), fromfile="a/" + p,
                                                      tofile="b/" + p, lineterm=""))
                return "edit_file", args, ok(filepath=p, occurrences=1, strategy="exact", diff=diff[:5000],
                                             is_truncated=len(diff) > 5000)
            return "edit_file", args, err("FileEditError", ws(obs)[:500])
        if c == "create":
            body = a.get("file_text")
            if body is None:
                return "create_no_text"
            if "created successfully" in obs[:300]:
                return "write_file", {"filepath": p, "content": body}, ok(filepath=p, size=len(body))
            return "write_file", {"filepath": p, "content": body}, err("FileWriteError", ws(obs)[:500])
        return "editor_" + str(c)
    if name == "submit":
        return "submit"
    return "tool_" + name


def cut_thought(t, n):
    t = ws(t)
    if len(t) <= n:
        return t
    cut = t[:n]
    k = max(cut.rfind(". "), cut.rfind("\n"))
    return cut[: k + 1].strip() if k > n // 2 else cut.strip()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--src", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--layout", required=True, choices=("31b", "e4b-solver"))
    p.add_argument("--system", help="solver prompt template (e4b-solver)")
    p.add_argument("--exclude-repos", help="file of owner/repo names to leave out")
    p.add_argument("--min-calls", type=int, default=4)
    p.add_argument("--max-calls", type=int, default=24)
    p.add_argument("--max-chars", type=int, default=45000)
    p.add_argument("--thought-chars", type=int, default=400)
    p.add_argument("--per-repo", type=int, default=40)
    p.add_argument("--time-minutes", type=float, default=8.0)
    p.add_argument("--tool-calls", type=int, default=28)
    p.add_argument("--turns", type=int, default=80)
    p.add_argument("--seed", type=int, default=1)
    a = p.parse_args()

    excl = set()
    if a.exclude_repos:
        excl = {l.strip().lower() for l in open(a.exclude_repos) if l.strip()}
    if a.layout == "31b":
        from swegemma.harness.agent_runner import build_agent_prompt
        cfg = NS(budget=NS(time_minutes=a.time_minutes, tool_calls=a.tool_calls, turns=a.turns, cost_usd=None),
                 harness=NS(command_timeout_seconds=240, max_stdout_chars=5000, max_file_lines=150,
                            max_file_chars=10000),
                 graph_dir=None, embeddings_dir=None, enable_sandbox_testing=True)
    else:
        template = open(a.system).read()
        desc = "Resolves the issue in /workspace end to end and leaves the change in the working tree. Takes one request string."
        ident = f'You are an agent. Your internal name is "solve". The description about you is "{desc}".'

    why, rows = collections.Counter(), []
    for f in sorted(glob.glob(os.path.join(a.src, "tool-*.parquet"))):
        pf = pq.ParquetFile(f)
        for batch in pf.iter_batches(batch_size=16):
            for r in batch.to_pylist():
                why["seen"] += 1
                if not r["resolved"]:
                    why["drop_unresolved"] += 1
                    continue
                iid = r["instance_id"]
                owner_repo = iid.split(".")[0].replace("__", "/", 1)
                if owner_repo.lower() in excl:
                    why["drop_excluded_repo"] += 1
                    continue
                msgs = json.loads(r["messages"])
                user0 = text_of(next((m["content"] for m in msgs if m["role"] == "user"), ""))
                pm = re.search(r"<pr_description>\s*(.*?)\s*</pr_description>", user0, re.S)
                if not pm:
                    why["drop_no_problem"] += 1
                    continue
                problem = ws(pm.group(1))
                st = steps_of(msgs)
                if not st:
                    why["drop_unparsed"] += 1
                    continue
                last_submit = max((i for i, s in enumerate(st) if s[1] == "submit"), default=None)
                if last_submit is None:
                    why["drop_no_submit"] += 1
                    continue
                out, totals, bad, edits = [], {}, None, 0
                for i, (thought, name, args, obs) in enumerate(st[: last_submit + 1]):
                    mapped = map_step(name, args, obs, totals)
                    if mapped == "submit":
                        if i == last_submit and a.layout == "31b":
                            patch = r.get("patch") or ""
                            out.append((thought, "submit_patch", {},
                                        ok(patch_size=len(patch), files_changed=patch.count("diff --git"))))
                        continue
                    if isinstance(mapped, str):
                        bad = mapped
                        break
                    edits += mapped[0] in ("edit_file", "write_file") and '"status": "ok"' in mapped[2]
                    out.append((thought,) + mapped)
                if bad:
                    why["drop_" + bad] += 1
                    continue
                if not edits:
                    why["drop_no_edit"] += 1
                    continue
                if not a.min_calls <= len(out) <= a.max_calls:
                    why["drop_calls_out_of_range"] += 1
                    continue
                if a.layout == "31b":
                    task = NS(repo=owner_repo, problem_statement=problem, hints_text="")
                    m = [{"role": "system", "content": "SYSTEM"},
                         {"role": "user", "content": build_agent_prompt(task, cfg, "", declared_tools=SIX)}]
                    names = SIX
                else:
                    sysm = template.replace("{problem_description}", problem)
                    sysm = re.sub(r"{hints\?}", "", sysm)
                    m = [{"role": "system", "content": sysm + "\n\n" + ident},
                         {"role": "user", "content": "Resolve the issue."}]
                    names = SIX[:5]
                for k, (thought, tool, args, resp) in enumerate(out):
                    cid = f"c{k:03d}"
                    m.append({"role": "assistant", "content": "", "reasoning_content": cut_thought(thought, a.thought_chars),
                              "tool_calls": [{"id": cid, "type": "function",
                                              "function": {"name": tool, "arguments": args}}]})
                    m.append({"role": "tool", "tool_call_id": cid, "name": tool, "content": resp})
                m.append({"role": "assistant", "content": "The fix is in place.", "reasoning_content": ""})
                if sum(len(json.dumps(x, ensure_ascii=False)) for x in m) > a.max_chars:
                    why["drop_too_many_chars"] += 1
                    continue
                rows.append({"tool_names": names, "messages": m,
                             "meta": {"instance_id": iid, "repo": owner_repo, "run": "swe-smith", "end": "complete",
                                      "llm_calls": len(out), "model": r["model"]}})
    rng = random.Random(a.seed)
    by = collections.defaultdict(list)
    for r in rows:
        by[r["meta"]["repo"]].append(r)
    kept = []
    for repo in sorted(by):
        g = by[repo]
        if len(g) > a.per_repo:
            why["drop_over_repo_cap"] += len(g) - a.per_repo
            g = rng.sample(g, a.per_repo)
        kept.extend(g)
    rng.shuffle(kept)
    with open(a.out, "w") as fo:
        for r in kept:
            fo.write(json.dumps(r, ensure_ascii=False) + "\n")
    calls = sorted(r["meta"]["llm_calls"] for r in kept)
    print(json.dumps({"rows": len(kept), "repos": len(by), "calls_median": calls[len(calls) // 2] if calls else 0,
                      "counts": dict(sorted(why.items()))}, indent=1))


if __name__ == "__main__":
    main()
