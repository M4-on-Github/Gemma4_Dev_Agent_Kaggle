#!/usr/bin/env python3
"""EXP-063 reference counts from base pipeline runs (EXP-061, EXP-062): the applier's check after each applied
draft, whether that check touched the edited file, and which draft was kept.

Prints ids, counts, draft numbers, program names, path arguments, exit codes and class letters only (hygiene rule:
no file text, no command arguments other than a path, no model messages).

Per task:
  drafts      usable drafts (a FILE line, an OLD block and a NEW block) among drafter_1..5
  events      the applier's tool calls in order, as letters:
                E<n>+  edit_file applied, matched to draft n (n = '?' when its old_string or new_string equals
                       no draft's block exactly; a match is exact equality after stripping outer blank lines)
                E<n>-  edit_file failed (error envelope or the harness arg-loss string)
                C      a check: run_command whose program is pytest or python (not git); printed separately
                U      undo: run_command whose program is git and whose second word is checkout
                G      any other run_command; R read_file; W write_file; S get_status; P submit_patch
  checks      for each C: the index of the applied edit it follows (or none), the program, its path argument
              if any (the first argument ending in .py or containing a slash, or none), the exit code, and
              rel = 'y' if the path argument names the edited file or a test file whose name contains the edited
              file's stem, else 'n'
  kept        the draft of the last applied edit that no later undo reverted (or '-' when no edit stands)
Usage: python -I -X utf8 experiments/EXP-063/refs.py runs/EXP-061-r runs/EXP-062-r
"""
from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path

ARG_LOSS = "mandatory input parameters are not present"

FILE_RE = re.compile(r"^FILE:\s*(\S+)", re.M)


def norm(s: str) -> str:
    return (s or "").strip("\n")


def _block(text: str, start: str, stops: tuple[str, ...]) -> str:
    """Lenient block cut: drafts often drop the <<< and >>> fences, so a block runs from its label to the next
    fence or label, and fence lines are removed."""
    i = text.find(start)
    body = text[i + len(start):]
    cut = min([j for j in (body.find(s) for s in stops) if j >= 0] or [len(body)])
    lines = [ln for ln in body[:cut].split("\n") if ln.strip() not in ("<<<", ">>>")]
    return norm("\n".join(lines))


def parse_draft(text: str) -> dict | None:
    text = text or ""
    m = FILE_RE.search(text)
    if not m or "OLD:" not in text or "NEW:" not in text:
        return None
    old = _block(text, "OLD:", ("\n>>>", "\nNEW:"))
    new = _block(text, "NEW:", ("\n>>>", "\nWHY:", "\nEND"))
    return {"file": m.group(1).strip("`"), "old": old, "new": new}


def args_of(tc: dict) -> dict:
    a = tc.get("arguments")
    if isinstance(a, str):
        try:
            a = json.loads(a)
        except ValueError:
            a = {}
    return a if isinstance(a, dict) else {}


def exit_code(obs: str) -> str:
    m = re.search(r'exit_code\\?"?\s*:\s*(-?\d+)', obs)
    return m.group(1) if m else "?"


def failed(obs: str) -> bool:
    return '"status": "error"' in obs or '\\"status\\": \\"error\\"' in obs or ARG_LOSS in obs


def task(trace: Path) -> dict:
    steps = json.load(open(trace, encoding="utf-8")).get("steps") or []
    drafts: dict[int, dict | None] = {}
    for s in steps:
        a = (s.get("extra") or {}).get("author") or ""
        if s.get("source") == "agent" and a.startswith("drafter_") and (s.get("extra") or {}).get("event_type") == "final":
            drafts[int(a.split("_")[1])] = parse_draft(s.get("message") or "")
    events, checks, applied = [], [], []  # applied: [draft, file, undone]
    for s in steps:
        if s.get("source") != "agent" or (s.get("extra") or {}).get("author") != "applier":
            continue
        obs = str((s.get("observation") or {}).get("content") or "")
        for tc in s.get("tool_calls") or []:
            fn = tc.get("function_name") or tc.get("name")
            ar = args_of(tc)
            if fn == "edit_file":
                fp, old, new = ar.get("filepath", ""), norm(ar.get("old_string", "")), norm(ar.get("new_string", ""))
                n = "?"
                for k, d in sorted(drafts.items()):
                    if d and fp.endswith(d["file"].lstrip("/")) and (old == d["old"] or new == d["new"]):
                        n = str(k)
                        break
                ok = not failed(obs) and bool(ar)
                events.append(f"E{n}{'+' if ok else '-'}")
                if ok:
                    applied.append([n, fp, False])
            elif fn == "run_command":
                try:
                    words = shlex.split(ar.get("command", ""))
                except ValueError:
                    words = (ar.get("command", "") or "").split()
                prog = Path(words[0]).name if words else ""
                if prog == "git" and len(words) > 1 and words[1] == "checkout":
                    events.append("U")
                    for ap in applied:
                        if any(w and ap[1].endswith(w) for w in words[2:] if w not in ("--", ".")) or "." in words[2:]:
                            ap[2] = True
                elif prog in ("pytest", "python", "python3"):
                    events.append("C")
                    path = next((w for w in words[1:] if (w.endswith(".py") or "/" in w) and not w.startswith("-")), None)
                    if path and "::" in path:
                        path = path.split("::")[0]
                    cur = applied[-1] if applied else None
                    rel = "n"
                    if cur and path:
                        stem = Path(cur[1]).stem
                        rel = "y" if (path.rstrip("/") and cur[1].endswith(path)) or stem in Path(path).name else "n"
                    label = prog if not (prog.startswith("python") and len(words) > 2 and words[1] == "-m") else f"{prog} -m {words[2]}"
                    if prog.startswith("python") and len(words) > 1 and words[1] == "-c":
                        label = f"{prog} -c"
                        path = None
                    checks.append({"after_edit": len(applied) or None, "prog": label, "path": path,
                                   "exit": exit_code(obs), "rel": rel})
                else:
                    events.append("G")
            else:
                events.append({"read_file": "R", "write_file": "W", "get_status": "S", "submit_patch": "P"}.get(fn, fn))
    standing = [ap for ap in applied if not ap[2]]
    return {"usable": sum(1 for d in drafts.values() if d), "events": events, "checks": checks,
            "kept": standing[-1][0] if standing else "-", "n_applied": len(applied)}


def main(runs: list[str]) -> int:
    for run in runs:
        rp = Path(run)
        res = {json.loads(l)["instance_id"]: json.loads(l) for l in open(rp / "task_results.jsonl", encoding="utf-8")}
        print(run)
        kept_tally: dict[str, int] = {}
        n_chk = n_rel = n_after = 0
        for p in sorted((rp / "traces").glob("trace_*.json")):
            tid = p.stem[len("trace_"):]
            t = task(p)
            kept_tally[t["kept"]] = kept_tally.get(t["kept"], 0) + 1
            print(f"  {tid:15s} usable {t['usable']}  applied {t['n_applied']}  kept {t['kept']:2s}  "
                  f"patch {res[tid]['patch_chars']:5d}  resolved {res[tid]['resolved']}  events {' '.join(t['events'])}")
            for c in t["checks"]:
                n_chk += 1
                n_after += c["after_edit"] is not None
                n_rel += c["rel"] == "y"
                print(f"      check after applied edit {c['after_edit']}: {c['prog']}  path {c['path']}  "
                      f"exit {c['exit']}  rel {c['rel']}")
        print(f"  checks {n_chk}, after an applied edit {n_after}, touching the edited file {n_rel}; kept {kept_tally}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
