"""PART B: E4B failed edit_file calls and the tolerant-applier ceiling. Counts and shares only.

Usage: python3 -I applier_e4b.py OUT_JSON

For every edit_file call whose observation is not status ok, the error is bucketed from the harness's own strings:
  NOT_FOUND  "Failed to replace: old_string not found ..."
  NOT_UNIQUE "Target string occurs N times ..." / "Target string flexibly matches N locations ..."
  NOOP       "No changes to apply. old_string and new_string are identical."
  MALFORMED  "Invoking `edit_file()` failed as the following mandatory input parameters are not present" (ADK arg
             check), "old_string cannot be empty", and the new_string=None crashes ("replace() argument 2 ...",
             "'NoneType' object has no attribute 'splitlines'")
  BUDGET     BudgetExceeded (refused by the call cap; not an edit failure, excluded)
Each NOT_FOUND call is compared with the latest ok read_file observation of the same normalized path earlier in the
trace (read_file returns raw lines, no line numbers; reads are windows given by start_line/end_line):
  EXACT_IN_READ  old_string occurs verbatim in that read (so the file changed after the read, or the read differs)
  PREFIX         old_string carries line-number prefixes (cat -n / grep -n / "NN:" / "NN|") on >= half its lines and
                 matches (verbatim or whitespace-normalized, uniquely) after stripping them
  WS             whitespace-normalized old_string (CRLF->LF, tabs->space, each line stripped and inner runs collapsed,
                 blank lines dropped) occurs exactly once in the normalized read
  AMBIG          ... occurs more than once
  NEAR           best window of the same number of normalized lines has difflib ratio >= 0.9 and no other
                 non-overlapping window reaches 0.9 (NEAR_AMBIG if one does)
  ABSENT         none of these
  UNKNOWN        no ok read_file of that path before the call
STALE marks a call whose path had a landed edit_file/write_file between that read and the call.
The harness's edit_file already retries exact -> rstrip-lines -> strip-lines -> token-regex -> JSON-unescape
(adk_eval_core/editing/edit.py), so every NOT_FOUND below has already failed those tiers on the real file.
"""
import collections
import difflib
import json
import os
import re
import sys

HE = "/home/mmyatmau/Gemma4_Dev_Agent_Kaggle/harness-eng"
sys.path.insert(0, os.path.join(HE, "tools"))
import trace_vs_reference as tvr  # noqa: E402

ARMS = {
    "base_r011": [f"R-011-e4b-base-tu5-d{i}" for i in range(1, 9)],
    "applier_r014": ["R-014-e4b-applier-tu5-d1"],
    "full0_l003_partial": [f"L-003-e4b-full0-tu127-d{i}" for i in range(1, 9)],
}

PFX = [re.compile(r"^\s*\d+\t"), re.compile(r"^\s*\d+\s*[:|]\s?"), re.compile(r"^[\w./-]+:\d+[:-]"),
       re.compile(r"^\s*\d+ {1,2}(?=\S)")]


def err_bucket(d):
    if d.get("error_type") == "BudgetExceeded":
        return "BUDGET"
    em = str(d.get("error") or d.get("error_message") or d.get("raw") or "")
    if "old_string not found" in em:
        return "NOT_FOUND"
    if "Target string occurs" in em or "flexibly matches" in em or "Expected 1 occurrence" in em:
        return "NOT_UNIQUE"
    if "No changes to apply" in em:
        return "NOOP"
    if "mandatory input parameters" in em or "cannot be empty" in em or "NoneType" in em or "argument 2 must be" in em:
        return "MALFORMED"
    return "OTHER"


def ws_lines(text):
    out = []
    for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        ln = re.sub(r"\s+", " ", ln.replace("\t", " ")).strip()
        if ln:
            out.append(ln)
    return out


def strip_prefix(old):
    lines = old.replace("\r\n", "\n").split("\n")
    ne = [l for l in lines if l.strip()]
    if not ne:
        return None
    for rx in PFX:
        hit = sum(1 for l in ne if rx.match(l))
        if hit >= max(1, (len(ne) + 1) // 2):
            return "\n".join(rx.sub("", l, count=1) for l in lines)
    return None


def ws_count(old, text):
    o = "\n".join(ws_lines(old))
    if not o:
        return 0
    return "\n".join(ws_lines(text)).count(o)


def near(old, text):
    ol = ws_lines(old)
    tl = ws_lines(text)
    n = len(ol)
    if n == 0 or len(tl) < n:
        return None
    os_ = "\n".join(ol)
    scores = []
    sm = difflib.SequenceMatcher(autojunk=False)
    sm.set_seq2(os_)
    for i in range(len(tl) - n + 1):
        w = "\n".join(tl[i:i + n])
        sm.set_seq1(w)
        if sm.real_quick_ratio() < 0.9 or sm.quick_ratio() < 0.9:
            continue
        r = sm.ratio()
        if r >= 0.9:
            scores.append((r, i))
    if not scores:
        return None
    best_r, best_i = max(scores)
    others = [i for r, i in scores if abs(i - best_i) >= n]
    return "NEAR_AMBIG" if others else "NEAR"


def near_detail(old, new, text):
    """For a NEAR call: line-token ratio of the best window, lines of old_string not in that window, and whether
    those lines also appear in new_string (an applier would then write the model's misquoted lines into the file)."""
    ol, tl = ws_lines(old), ws_lines(text)
    nl = set(ws_lines(new or ""))
    n = len(ol)
    best = (-1.0, 0)
    sm = difflib.SequenceMatcher(autojunk=False)
    sm.set_seq2("\n".join(ol))
    for i in range(len(tl) - n + 1):
        sm.set_seq1("\n".join(tl[i:i + n]))
        if sm.real_quick_ratio() < 0.9 or sm.quick_ratio() < 0.9:
            continue
        best = max(best, (sm.ratio(), i))
    w = tl[best[1]:best[1] + n]
    line_ratio = difflib.SequenceMatcher(None, ol, w, autojunk=False).ratio()
    wset = set(w)
    miss = [l for l in ol if l not in wset]
    return dict(line_ratio=line_ratio, n_lines=n, miss_lines=len(miss), miss_in_new=sum(1 for l in miss if l in nl))


def classify_nf(old, read_text):
    if read_text is None:
        return "UNKNOWN"
    if old and old in read_text:
        return "EXACT_IN_READ"
    sp = strip_prefix(old)
    if sp is not None:
        if sp in read_text or ws_count(sp, read_text) == 1:
            return "PREFIX"
    c = ws_count(old, read_text)
    if c == 1:
        return "WS"
    if c > 1:
        return "AMBIG"
    nr = near(old, read_text)
    return nr or "ABSENT"


def path_of(args):
    return tvr.norm_path(args.get("filepath") or args.get("path") or args.get("file_path") or "")


def scan(run, iid):
    t = json.load(open(os.path.join(HE, "runs", run, "traces", f"trace_{iid}.json")))
    reads = collections.defaultdict(list)  # path -> [(ci, content)]
    landed = collections.defaultdict(list)  # path -> [ci]
    shell_out = []  # stdout of run_command, for UNKNOWN cases
    fails = []
    n_reads = n_paged = 0
    ci = 0
    edit_ok_src = False
    edits_by = collections.Counter()
    for s in t.get("steps", []):
        if s.get("source") != "agent":
            continue
        author = (s.get("extra") or {}).get("author")
        d = tvr.obs_dict(s)
        for tc in s.get("tool_calls") or []:
            ci += 1
            fn, args = tc.get("function_name"), tc.get("arguments") or {}
            if fn == "read_file" and d.get("status") == "ok" and isinstance(d.get("content"), str):
                p = path_of(args)
                reads[p].append((ci, d["content"]))
                n_reads += 1
                tot = d.get("total_lines") or 0
                if d.get("is_truncated") or (d.get("start_line") or 1) > 1 or (tot and (d.get("end_line") or tot) < tot):
                    n_paged += 1
            elif fn == "run_command":
                shell_out.append((ci, tvr.obs_text(d)))
            elif fn in ("edit_file", "write_file"):
                p = path_of(args)
                ok = tvr.call_ok(d)
                repo = bool(p) and not p.startswith("/") and not p.startswith("tmp/")
                if ok:
                    landed[p].append(ci)
                    if repo and not tvr.is_test_path(p):
                        edit_ok_src = True
                if fn == "edit_file":
                    edits_by[author] += 1
                if fn == "edit_file" and not ok:
                    b = err_bucket(d)
                    rec = dict(ci=ci, bucket=b, author=author)
                    if b == "NOT_FOUND":
                        old = args.get("old_string")
                        old = old if isinstance(old, str) else ""
                        prior = reads.get(p) or []
                        if prior:
                            rci, text = prior[-1]
                            rec["stale"] = any(rci < x < ci for x in landed.get(p, []))
                            rec["cls"] = classify_nf(old, text)
                            if rec["cls"] == "NEAR":
                                nw = args.get("new_string")
                                rec.update(near_detail(old, nw if isinstance(nw, str) else "", text))
                            if rec["cls"] in ("ABSENT", "NEAR", "NEAR_AMBIG"):
                                # does it match an earlier read window of the same path?
                                rec["earlier_ws"] = any(old in tx or ws_count(old, tx) == 1 for _, tx in prior[:-1])
                        else:
                            rec["cls"] = "UNKNOWN"
                            rec["stale"] = False
                            sh = "\n".join(o for _, o in shell_out)
                            sp = strip_prefix(old)
                            rec["shell_ws"] = bool(old) and (ws_count(old, sh) >= 1 or
                                                             (sp is not None and ws_count(sp, sh) >= 1))
                        rec["prefixed"] = strip_prefix(old) is not None
                    if b == "NOT_UNIQUE":
                        # would anchoring to the latest read window pick one occurrence?
                        old = args.get("old_string")
                        old = old if isinstance(old, str) else ""
                        prior = reads.get(p) or []
                        if prior and old:
                            rci, text = prior[-1]
                            rec["stale"] = any(rci < x < ci for x in landed.get(p, []))
                            rec["win_unique"] = text.count(old) == 1 or ws_count(old, text) == 1
                        else:
                            rec["stale"], rec["win_unique"] = False, None
                    fails.append(rec)
    return dict(fails=fails, landed_src=edit_ok_src, n_reads=n_reads, n_paged=n_paged, edits_by=dict(edits_by))


def main():
    out = {}
    for arm, runs in ARMS.items():
        draws = []
        for run in runs:
            p = os.path.join(HE, "runs", run, "task_results.jsonl")
            if not os.path.exists(p):
                continue
            for line in open(p):
                row = json.loads(line)
                if not os.path.exists(os.path.join(HE, "runs", run, "traces", f"trace_{row['instance_id']}.json")):
                    continue
                r = scan(run, row["instance_id"])
                r.update(run=run, iid=row["instance_id"], resolved=bool(row["resolved"]))
                draws.append(r)
        fails = [f for d in draws for f in d["fails"]]
        b = collections.Counter(f["bucket"] for f in fails)
        nf = [f for f in fails if f["bucket"] == "NOT_FOUND"]
        cls = collections.Counter(f["cls"] for f in nf)
        cls_fresh = collections.Counter(f["cls"] for f in nf if not f["stale"])
        stale = sum(f["stale"] for f in nf)
        real_fail = [f for f in fails if f["bucket"] != "BUDGET"]
        d_fail = [d for d in draws if any(f["bucket"] != "BUDGET" for f in d["fails"])]
        d_nf = [d for d in draws if any(f["bucket"] == "NOT_FOUND" for f in d["fails"])]
        d_fail_nolanded = [d for d in d_fail if not d["landed_src"]]
        tol = lambda d, ks: any(f["bucket"] == "NOT_FOUND" and f["cls"] in ks and not f["stale"] for f in d["fails"])
        tol_any = lambda d, ks: any(f["bucket"] == "NOT_FOUND" and f["cls"] in ks for f in d["fails"])
        n_edit_calls = sum(sum(d["edits_by"].values()) for d in draws)
        nr = [f for f in nf if f["cls"] == "NEAR" and not f["stale"]]
        near_stats = dict(
            n=len(nr),
            line_ratio_ge_09=sum(1 for f in nr if f["line_ratio"] >= 0.9),
            miss_lines_1=sum(1 for f in nr if f["miss_lines"] == 1),
            miss_lines_2=sum(1 for f in nr if f["miss_lines"] == 2),
            miss_lines_3plus=sum(1 for f in nr if f["miss_lines"] >= 3),
            miss_lines_0=sum(1 for f in nr if f["miss_lines"] == 0),
            misquoted_line_carried_into_new=sum(1 for f in nr if f["miss_in_new"] > 0),
            single_line_old=sum(1 for f in nr if f["n_lines"] == 1),
        )
        near_line = lambda d: any(f["bucket"] == "NOT_FOUND" and f["cls"] == "NEAR" and not f["stale"]
                                  and f["line_ratio"] >= 0.9 for f in d["fails"])
        out[arm] = dict(
            runs=runs, task_draws=len(draws), resolved=sum(d["resolved"] for d in draws),
            edit_calls=n_edit_calls, failed_edit_calls=len(real_fail),
            buckets=dict(b),
            not_found=len(nf),
            not_found_classes=dict(cls), not_found_classes_not_stale=dict(cls_fresh), not_found_stale=stale,
            not_found_prefixed=sum(f["prefixed"] for f in nf),
            unknown_matching_shell_output=sum(1 for f in nf if f["cls"] == "UNKNOWN" and f.get("shell_ws")),
            absent_near_matching_earlier_read=sum(1 for f in nf if f.get("earlier_ws")),
            read_obs=sum(d["n_reads"] for d in draws), read_obs_paged=sum(d["n_paged"] for d in draws),
            draws_with_failed_edit=len(d_fail), draws_with_not_found=len(d_nf),
            draws_failed_and_never_landed=len(d_fail_nolanded),
            never_landed_rescued_ws_prefix=sum(1 for d in d_fail_nolanded if tol(d, ("WS", "PREFIX"))),
            never_landed_rescued_ws_prefix_incl_stale=sum(1 for d in d_fail_nolanded if tol_any(d, ("WS", "PREFIX"))),
            never_landed_rescued_plus_near=sum(1 for d in d_fail_nolanded if tol(d, ("WS", "PREFIX", "NEAR"))),
            never_landed_rescued_plus_near_line=sum(1 for d in d_fail_nolanded if near_line(d)),
            near_stats=near_stats,
            not_unique_window_unique=sum(1 for f in fails if f["bucket"] == "NOT_UNIQUE" and f.get("win_unique")
                                         and not f.get("stale")),
            not_unique_no_read=sum(1 for f in fails if f["bucket"] == "NOT_UNIQUE" and f.get("win_unique") is None),
            never_landed_rescued_window_anchor=sum(1 for d in d_fail_nolanded if any(
                f["bucket"] == "NOT_UNIQUE" and f.get("win_unique") and not f.get("stale") for f in d["fails"])),
            never_landed_rescued_plus_exact_in_read=sum(1 for d in d_fail_nolanded
                                                         if tol(d, ("WS", "PREFIX", "NEAR", "EXACT_IN_READ"))),
            resolved_draws_with_failed_edit=sum(1 for d in d_fail if d["resolved"]),
            edits_by_author=dict(sum((collections.Counter(d["edits_by"]) for d in draws), collections.Counter())),
            fails_by_author=dict(collections.Counter(f["author"] for f in real_fail)),
        )
        print(arm, json.dumps(out[arm]))
    json.dump(out, open(sys.argv[1], "w"), indent=1)


if __name__ == "__main__":
    main()
